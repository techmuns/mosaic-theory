#!/usr/bin/env python3
"""Assemble the static snapshot mirror the dashboard serves.

Copies the lightweight committed snapshots and the DERIVED dossiers (never the raw
CIQ workbooks) into ``frontend/``, and generates ``manifest.json`` (the cheap
index: counts + dates that the UI can't otherwise derive without fetching the
megabyte-scale candidate files). Run by Cloudflare Pages on every deploy, and
locally for preview.

It READS only committed snapshots under ``data/snapshots/`` and committed dossiers
under ``data/dossiers/``, and WRITES the ``frontend/snapshots/`` mirror (git-ignored
— regenerated here every deploy) and the ``frontend/dossiers/`` mirror (committed
for the authed deploy, but idempotently regenerated here too). It is not a backend
and runs no pipeline; it only mirrors existing artifacts.

LICENSING: only the DERIVED ``dossier.json``/``dossier.md`` are mirrored — never the
raw licensed CIQ in ``data/manual/ciq/``. ``data/dossiers/`` is committed to the
PRIVATE/authed repo (verified: {value, source_ref} facts + synthesis + public 10-K
phrases, no licensed CIQ); if the repo or deploy ever becomes public, the dossiers
and ``frontend/dossiers/`` revert to git-ignored.
"""
from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SNAP = ROOT / "data" / "snapshots"
DOSS = ROOT / "data" / "dossiers"
GRAPH = ROOT / "data" / "graph_coverage.json"  # DERIVED EDGAR-10-K exposure map (private-repo only)
#                                      artifacts
OUT_SNAP = HERE / "snapshots"
OUT_DOSS = HERE / "dossiers"

# The lightweight snapshots the UI fetches at runtime. The MB-scale candidate /
# universe / securities files are intentionally NOT mirrored — their derived
# counts go into manifest.json instead, so the deploy stays small.
_MIRRORED = ("ranked_queue.jsonl", "decision_ledger.jsonl")


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# --- SCENARIO CARDS (reusable) ------------------------------------------------------------------
# A committed `scenarios/<TICKER>.json` underwrite record renders as a card attachable under ANY
# watchlist name — no full-dossier dependency. Names WITHOUT a record are untouched (the key is
# omitted entirely, so their display JSON stays byte-identical).
#
# STDLIB ONLY (docs/DEPLOY.md): this file is the Cloudflare Pages build step, run as
# `python frontend/build.py` with NO requirements.txt — so it must never import `vinci` (which
# pulls in pydantic) or anything else off the stdlib. The records are plain JSON; we read them
# directly. The record's own field names are the contract (vinci/scenarios.py owns the schema).
def _rd(x: Any, places: int) -> Any:
    """Round for DISPLAY only — the stored record keeps full precision. None passes through, so an
    absent cross-check still renders as absent rather than as 0."""
    return round(x, places) if isinstance(x, (int, float)) and not isinstance(x, bool) else x


def _ledger_join() -> dict[str, list[dict[str, Any]]]:
    """The committed decision ledger, keyed by ticker — the DECISION row of record, with its
    close attached when the position has been closed.

    The card renders on surfaces that never load the ledger snapshot (the scenarios mirror; the
    theme watchlist did too until it retired, 2026-11-04), so the join happens HERE, at build, not
    in the client.
    Absent file → empty: a deploy without a ledger renders cards with no verdict-of-record line
    rather than failing.

    PAIRING, not last-row-wins (fixed 2026-07-27). Since close rows shipped (2026-07-22) a ticker
    carries TWO rows — the decision row and its close — and a close row repeats the ORIGINAL
    verdict for provenance. The former `out[ticker] = row` loop therefore let FILE ORDER decide
    which one reached the card: IT's card rendered its close row's id as though it were the
    decision, and a closed position still headlined a bare "BUY" as if it were open. The card now
    always anchors on the DECISION row and carries `_closed` when a close pairs to it.

    STDLIB TWIN of ``vinci.monitor.pair_closes`` (this file must never import vinci — see the
    module note above; same twinning convention as the committed-GICS index below). The twin is
    pinned against the original on the real committed ledger, so the two cannot drift.
    """
    p = SNAP / "decision_ledger.jsonl"
    if not p.is_file():
        return {}
    rows = _jsonl(p)
    # The close fields live on the ENTRY (inside `payload`), never at the row's top level — a
    # committed row simply has no `event` key there, so a top-level filter passes every close
    # through as a position. Stdlib twin of vinci.monitor.entry_of, which exists for this trap.
    def entry_of(row: dict[str, Any]) -> dict[str, Any]:
        pl = row.get("payload")
        return json.loads(pl) if isinstance(pl, str) else row

    entries = [entry_of(r) for r in rows]
    by_entry: dict[str, dict[str, Any]] = {
        str(e.get("entry_id")): dict(e) for e in entries if not e.get("event")}
    # A DECISION'S CORRECTION (RF-D7) rides WITH it, as `closed` does: a stdlib twin of
    # `vinci.monitor.apply_corrections`. The card keeps the decision's SEALED entry beside the
    # underwrite record's own (they are the same price, and the record's ratio was computed at
    # it); the entry the ledger READS the decision at is carried as `_correction`, so the card can
    # say so.
    for e in entries:
        if e.get("event") != "CORRECTION":
            continue
        target = by_entry.get(str(e.get("corrects_entry_id")))
        if target is None:
            continue          # an orphan correction is the ledger's problem (the readers raise)
        target["_correction"] = {
            "correctionId": e.get("entry_id"),
            "entryPrice": _rd(e.get("entry_price"), 2),
            "entryPriceAsOf": e.get("entry_price_as_of"),
            "reason": e.get("reason"),
        }
    # A VOIDED DECISION IS NO VERDICT OF RECORD (operator ruling 2026-11-11, GOOGL): a stdlib twin
    # of `vinci.monitor.decision_rows`' rule. The row is MARKED here, never dropped, so the tenure
    # walk below still finds the record it belonged to — and `_scenario_card` then shows that card
    # as voided rather than as holding a BUY, or as "no ledger verdict logged" (a verdict was
    # logged; it was ruled out).
    for e in entries:
        if e.get("event") != "VOID":
            continue
        target = by_entry.get(str(e.get("voids_entry_id")))
        if target is None:
            continue          # an orphan void is the ledger's problem (the python readers raise)
        target["_voided"] = {"entryId": target.get("entry_id"), "voidId": e.get("entry_id"),
                             "ruledOn": e.get("ruled_on")}
    for e in entries:
        if e.get("event") != "CLOSE":
            continue
        target = by_entry.get(str(e.get("closes_entry_id")))
        if target is None:
            continue          # an unpairable close is the ledger's problem, not the card's
        target["_closed"] = {
            "exitPrice": _rd(e.get("exit_price"), 2),
            "exitPriceAsOf": e.get("exit_price_as_of"),
            "reason": e.get("reason"),
            "closeEntryId": e.get("entry_id"),
        }
    # ONE TICKER CAN HOLD MORE THAN ONE POSITION, and this collapse used to be decided by FILE
    # ORDER — the identical defect the docstring above records as fixed for the decision/close
    # PAIR, still open one level up for two DECISION rows. It could not fire until 2026-08-05:
    # SMPL closed its 2026-07-06 position and opened another on 2026-07-29, so the comprehension
    # `{ticker: e for e in ...}` had two candidates and silently kept whichever came last. It also
    # took the ARCHIVED record's card down with it — `_ledger_for_record` could no longer see the
    # row the 2026-07-21 record owns, so the served archived card lost its position entirely.
    #
    # ALL of them are kept, newest last, and `_ledger_for_record` selects by TENURE from the
    # full list — a superseded record finds its own row, a live one finds the row decided
    # during its own tenure. Nothing collapses to one-row-per-ticker any more: that collapse
    # WAS the defect, and a "position of record" helper built on it survived only because two
    # tests called it. Keeping every row also restores the twin claim to a direct equality —
    # the join resolves exactly the closed pairs `pair_closes` does, with nothing restricted.
    out: dict[str, list[dict[str, Any]]] = {}
    for e in by_entry.values():
        out.setdefault(str(e.get("ticker", "")).upper(), []).append(e)
    for lst in out.values():
        lst.sort(key=lambda e: str(e.get("decided_at") or ""))
    return out


def _ledger_rows_by_ticker() -> dict[str, list[dict[str, Any]]]:
    """Every decision row per ticker, oldest first — the index ownership-by-tenure needs."""
    return _ledger_join()


def _amendment_index() -> dict[str, list[dict[str, Any]]]:
    """The amendment-index sidecar, keyed by ticker (record legibility, 2026-07-27).

    Carries the CLASS of each pre-gate tag (inferred, and labelled as inferred) and any
    ``superseded_note`` — a LATER finding that changed what an earlier tag means. SMPL tag 1 is
    the case: it records a staleness premise that the 2026-07-26 verification then refuted. The
    sealed text is never edited, so the correction has to travel BESIDE it; otherwise a reader
    meets the superseded claim and only learns it was wrong three tags later, if at all."""
    p = ROOT / "scenarios" / "_amendment_index.json"
    if not p.is_file():
        return {}
    try:
        rows = json.loads(p.read_text()).get("tags") or []
    except ValueError:
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        # keyed by the RECORD the tags live on: a ticker for a live record, an ARCHIVE KEY for a
        # superseded one. SMPL's three tags travelled with the record they were written on when it
        # was archived; the reissued live record carries none, so it gets no index at all.
        key = str(r.get("record") or r.get("ticker", "")).upper()
        out.setdefault(key, []).append(
            {"index": r.get("tag_index"), "date": r.get("date"),
             "inferredClass": r.get("inferred_class"),
             **({"supersededNote": r["superseded_note"]} if r.get("superseded_note") else {})})
    return out


def _ledger_for_record(
    rec: dict[str, Any], ledger: dict[str, dict[str, Any]] | None,
) -> dict[str, Any] | None:
    """The ledger row THIS record justified — or None (supersession fix, 2026-07-27).

    THE DEFECT. The join was by TICKER alone, which was right while one ticker meant one record.
    Supersession broke that: SMPL's BUY was decided 2026-07-21 against the record that is now
    ARCHIVED, while the live record was reissued 2026-07-27 and opened no position at all
    (`entry_price` is None). Joining by ticker put that BUY on the reissued card — a `watch`
    record headlining a verdict it never made — and displayed the SAME row on two records.

    THE RULE. A record owns the row only if the row was decided during ITS tenure: the record's
    `underwrite_date` is the latest one at or before `decided_at`. A record underwritten AFTER the
    decision cannot have justified it. Records with no supersession are unaffected — there is only
    one record, so it is trivially the latest at-or-before.
    """
    # A TICKER CAN HOLD MORE THAN ONE POSITION since 2026-08-05 — SMPL closed its 2026-07-06 one
    # and opened another on 2026-07-29 — so the index is a LIST per ticker and each candidate is
    # tested against this record's tenure, newest first. A single row is still accepted, because
    # the tenure rule below is written for one and this stays its own base case.
    t_up = str(rec.get("ticker", "")).upper()
    found = (ledger or {}).get(t_up)
    if isinstance(found, list):
        # a LIVE row this record owns outranks a VOIDED one (operator ruling 2026-11-11):
        # `vinci.monitor.decision_rows` drops the voided row before anything is read, so a newer
        # void must not hide an older live position of the same record. A voided row is returned
        # only when the record owns no live one, so the card can say its verdict was voided.
        for cand in [c for c in reversed(found) if not c.get("_voided")] + [
                c for c in reversed(found) if c.get("_voided")]:
            owned = _ledger_for_record(rec, {t_up: cand})
            if owned is not None:
                return owned
        return None
    led = found
    if not led:
        return None
    decided = str(led.get("decided_at") or "")[:10]
    mine = str(rec.get("underwrite_date") or "")
    if not decided or not mine:
        return led                      # undatable either side → keep the legacy behaviour
    if mine > decided:
        return None                     # this record post-dates the decision: not its row
    # a LATER sibling that still pre-dates the decision owns it instead
    sib = str(rec.get("superseded_by") or "")
    if sib:
        successor_date = sib.split("-", 1)[1] if "-" in sib else ""
        if successor_date and successor_date <= decided:
            return None
    return led


def _superseded_ledger(
    rec: dict[str, Any], ledger: dict[str, dict[str, Any]] | None,
) -> dict[str, Any] | None:
    """The ledger row this record's SUPERSEDED predecessor owns — or None.

    Only for a record that owns NO row of its own: a live reissue struck after the decision it
    inherits. What the reader needs is not the row (it belongs to the predecessor, and
    `_ledger_for_record` is right to say so) but the FACT that one exists and where — otherwise the
    card reads "no ledger verdict logged" on a name holding an open position.

    Walks ONE link back, deliberately. A longer chain would need the whole ancestry, and the
    honest answer for a reader is the nearest record that carries the row; the card links the
    chain either way, so a second hop is a click, not a hidden fact.
    """
    if _ledger_for_record(rec, ledger) is not None:
        return None                      # it owns its own row — nothing to borrow
    prior = str(rec.get("supersedes") or "")
    if not prior:
        return None
    # THE PREDECESSOR AS COMMITTED, never a record synthesised from this one. The first cut passed
    # `{**rec, underwrite_date: <prior>, superseded_by: None}` — and stripping `superseded_by`
    # disabled the very sibling clause that assigns rows correctly. On SMPL's middle record it
    # attributed the 2026-08-05 BUY (owned by the LIVE record) to SMPL-2026-07-21, which owns the
    # 2026-07 one: a real position, named against the wrong record, on a card that had been
    # correct before. Read the predecessor off disk and let the ownership rule judge IT.
    src = ROOT / "scenarios" / "archive" / f"{prior}.json"
    if not src.is_file():
        return None
    try:
        prior_rec = json.loads(src.read_text())
    except (OSError, ValueError):
        return None
    led = _ledger_for_record(prior_rec, ledger)
    if not led:
        return None
    return {"recordKey": prior,
            # ROUNDED LIKE THE OWNED ROW (`_rd(..., 2)` below) — same field, same shape, so the
            # two are comparable: the card pairs the borrowed as-of date with the borrowed price
            # only when it IS the price on screen, and an unrounded twin would fail that identity.
            **{k: (_rd(led[j], 2) if j == "entry_price" else led[j])
               for k, j in (("verdict", "verdict"), ("decidedAt", "decided_at"),
                            ("entryPrice", "entry_price"),
                            ("entryPriceAsOf", "entry_price_as_of"))
               if led.get(j) is not None},
            **({"correction": led["_correction"]} if led.get("_correction") else {}),
            # `closed` RIDES WITH THE VERDICT HERE TOO (external-honesty pass 2026-07-27, extended
            # 2026-09-01). The rule is that no surface may render the word "BUY" without the fact
            # that the position was closed — and this block is a new surface for exactly that word.
            # Dropping it made SMPL-2026-07-27's foot read "BUY logged 2026-07-21 against the
            # superseded SMPL-2026-07-21" for a position closed 2026-07-22, on a card that had
            # been correct before. Same shape as the owned row's `closed`, so one renderer reads
            # both; omitted on an open position, so those stay byte-identical.
            **({"closed": led["_closed"]} if led.get("_closed") else {}),
            # the predecessor's row VOIDED (operator ruling 2026-11-11): carried so `_scenario_card`
            # drops this block and marks the card voided — never emitted itself
            **({"_voided": led["_voided"]} if led.get("_voided") else {})}


def _record_key(rec: dict[str, Any]) -> str:
    """The key a record is indexed under: its ARCHIVE KEY once superseded, else its ticker."""
    t = str(rec.get("ticker", "")).upper()
    return f"{t}-{rec['underwrite_date']}" if rec.get("superseded_by") else t


def _next_evidence(ticker: str, verdict: dict[str, Any]) -> dict[str, str]:
    """(record legibility, 2026-07-27) WHEN this record next meets new evidence, and FROM WHERE.

    RESOLUTION ORDER, ratified 2026-07-27: the dossier catalyst calendar's earliest FUTURE row →
    the earliest dated trigger → honest UNKNOWN. The calendar leads because it carries the actual
    next print (SMPL: 2026-10-08); a dated trigger is a DEADLINE the analyst set, which for SMPL
    sits a full quarter later (2027-01-07) and would misstate "next evidence" by three months if
    it led. A record with neither says so rather than inventing a date."""
    cal_path = DOSS / ticker.upper() / "dossier.json"
    if cal_path.is_file():
        try:
            doss = json.loads(cal_path.read_text())
            cal = ((doss.get("mechanical") or {}).get("catalyst_calendar") or {})
            ref = str(doss.get("reference_date") or "")
            rows = sorted((r for r in (cal.get("rows") or [])
                           if str(r.get("expected_date") or "") > ref),
                          key=lambda r: str(r.get("expected_date")))
            if rows:
                return {"date": str(rows[0]["expected_date"]),
                        "what": str(rows[0].get("event") or "next scheduled event"),
                        "source": f"catalyst calendar ({rows[0].get('date_basis') or 'stated'})"}
        except (OSError, ValueError, KeyError):
            pass                                   # a malformed dossier degrades to the fallback
    trigs = sorted((t for t in (verdict.get("dated_triggers") or []) if t.get("deadline")),
                   key=lambda t: str(t["deadline"]))
    if trigs:
        return {"date": str(trigs[0]["deadline"]),
                "what": f"re-underwrite trigger: {trigs[0].get('trigger') or ''}".strip(),
                "source": "analyst dated trigger"}
    return {"date": "UNKNOWN", "what": "no scheduled evidence", "source": "none on file"}


def _current_state(rec: dict[str, Any]) -> dict[str, Any]:
    """(record legibility, 2026-07-27) The MACHINE-DERIVED current state — what is true NOW.

    Written because the rationale records what was believed at DECISION time, and a reader meeting
    it first infers the present from the past. SMPL is the specimen: `watch`, position closed, base
    margin re-set — none of which the (sealed, correct, 07-21) rationale can say, because it was
    written before any of it happened.

    The block no longer renders as a block: the at-a-glance fold moved these values into the
    masthead band, where the ENTRY cell states the holding directly ("— no position") and the
    verdict chip states any close. The HOLDING TRIO that answered that question here — `held`,
    `holdingLabel`, and the ledger argument they needed — is retired with `statusNote`; see the
    note below. What remains is what the band actually reads."""
    v = rec.get("verdict") or {}
    r = rec.get("result") or {}
    status = str(v.get("status") or "pending_analyst")
    # READ, NEVER RECOMPUTE. This file is stdlib-only and cannot import `vinci`, so it used to
    # carry its own copy of the formula — with the bar HARDCODED to 2, while `uw-card.js` states
    # the opposite rule for itself ("an absent bar renders honest, never an invented 2 … the card
    # carries no fund constants of its own"). The recipe now computes the ceiling from the RECORD's
    # own bar and persists it, so both sides read one number and cannot drift.
    ceiling = r.get("ceiling2to1")
    # RETIRED 2026-07-27 — `statusNote`, and with it `held` / `holdingLabel` / `baseNormalMargin`,
    # all four for the same reason: nothing read them. The at-a-glance fold deleted the block that
    # rendered the holding trio and left them emitted into every card, which is exactly how a dead
    # key gets rendered back by the next author instead of questioned. Those three were machine-
    # DERIVED, so retiring them discards nothing — a rebuild recomputes them the day a surface
    # wants them; `status_note` was analyst prose, which is why only that one needed an operator
    # call. The orphan half of the card-key parity pin now catches the next one.
    out: dict[str, Any] = {
        "status": status,
        "ratio": _rd(r.get("ratio"), 2),
        "bar": _rd(r.get("bar"), 1),
        "passFail": r.get("pass_fail"),
        # BOTH dates: the ratio is computed at a spot that has its own as-of, and the underwrite
        # that produced the legs has another. Showing one invites reading a stale number as live.
        "spot": _rd(rec.get("spot"), 2),
        "spotSource": rec.get("spot_source"),
        "underwriteDate": rec.get("underwrite_date"),
        "nextEvidence": _next_evidence(str(rec["ticker"]), v),
    }
    if ceiling is not None:
        out["ceiling2to1"] = _rd(ceiling, 2)
    # THE STATED LIMIT RIDES BESIDE THE CEILING, because the pair is the information: the ceiling
    # says where the bar falls on today's legs, the limit says what the analyst will pay, and the
    # GAP is the conservatism they added. EPAM: ceiling $93.71, limit $89.50. Shown only when
    # stated — an absent limit renders nothing rather than borrowing the ceiling, which is the
    # substitution the field exists to prevent.
    lim = rec.get("limit") or {}
    if lim.get("price") is not None:
        # ONLY the price reaches the card. `stated_at` and `note` are PROVENANCE and live in
        # `scenarios/<T>.json` (tier 3) — emitting them here would put keys on the card that no
        # view renders, which the parity pin correctly refuses.
        out["limit"] = _rd(lim.get("price"), 2)
    elif lim.get("state") == "deferred":
        # A DEFERRAL IS NOT SILENCE, and the card has to say so or it renders identically to the
        # six records that carry no limit at all — which is the oversight/deliberate-absence
        # collapse this state exists to prevent.
        out["limitDeferred"] = True
    return out


def _scenario_card(rec: dict[str, Any], ledger: dict[str, dict[str, Any]] | None = None
                   ) -> dict[str, Any]:
    """One underwrite record → the display card: the bear/base/bull grid, the reward/risk ratio
    against the bar, the capital-intensity cross-checks, and the verdict. The basis and recipe
    travel WITH the card so the multiple's unit can never be misread on screen.

    Numbers are rounded HERE, never in the record: prices/ratio to 2dp, multiples and $M to 1dp."""
    r = rec.get("result") or {}
    per = r.get("per_scenario") or {}
    v = rec.get("verdict") or {}
    led = _ledger_for_record(rec, ledger)
    # ONCE, not twice: the emit below is a conditional spread, and calling the helper in both the
    # value and the condition re-ran the ownership walk AND re-read the predecessor off disk for
    # every card.
    sled = _superseded_ledger(rec, ledger)
    # A VOIDED ROW IS NO LEDGER VERDICT ON THE CARD (operator ruling 2026-11-11): neither its own
    # nor a predecessor's. The card carries `voided` instead — the fact, never the BUY — and the
    # decision log's audit tier holds the voided call itself, once.
    gone = next((x["_voided"] for x in (led, sled) if x and x.get("_voided")), None)
    led = None if led and led.get("_voided") else led
    sled = None if sled and sled.get("_voided") else sled
    return {
        **({"voided": gone} if gone else {}),
        "ticker": rec["ticker"], "recipeId": rec["recipe_id"], "recipeDesc": rec["recipe_desc"],
        # schema-1.1 methodology: the stamped arithmetic chain + per-axis derivations. Keys are
        # OMITTED (not emptied) for pre-1.1 records — the degrade is silence, never a fabricated
        # block, and old committed cards stay byte-identical under the emit-determinism pin.
        # Reference values pass through RAW (display-natural units in the record; no _rd).
        **({"recipeFormula": list(rec["recipe_formula"])}
           if rec.get("recipe_formula") else {}),
        **({"assumptions": [
            {"axis": k, "method": a["method"],
             # Draft status is STRUCTURED, never a marker inside the prose (the register rule: a
             # prose duplicate of structured state is the thing being removed). Emitted only when
             # UNratified, so a ratified axis stays byte-identical — the card badges from this.
             **({"unratified": True} if not a.get("ratified_by") else {}),
             # (schema 1.3) role/leg/excluded ride each reference so the card SELECTS on fields,
             # never on label prose (the /median/i regex this replaces showed the PEER median on
             # MVST by array order). Emitted only when set — legacy refs stay byte-identical.
             "references": [{"label": p["label"], "value": p["value"], "unit": p["unit"],
                             "source": p["source"],
                             # (schema 1.4) the vintage rides too, or the field the backend now
                             # REQUIRES would exist only in the backend: `source` says where a
                             # value came from, `vintage` says when, and the human reads the card.
                             # Emitted only when set, so the 7 committed 1.3 records — none of
                             # which carry one — stay byte-identical.
                             **({"vintage": p["vintage"]} if p.get("vintage") else {}),
                             **({"role": p["role"]} if p.get("role") else {}),
                             **({"leg": p["leg"]} if p.get("leg") else {}),
                             **({"excluded": True,
                                 "excludedReason": p.get("excluded_reason")}
                                if p.get("excluded") else {})}
                            for p in (a.get("references") or [])],
             **({"notes": [{"text": n["text"], "date": n["date"],
                            **({"source": n["source"]} if n.get("source") else {})}
                           for n in a["notes"]]}
                if a.get("notes") else {})}
            for k, a in rec["assumptions"].items()]}
           if rec.get("assumptions") else {}),
        "multipleBasis": rec["multiple_basis"], "underwriteDate": rec["underwrite_date"],
        "analyst": rec["analyst"], "spot": _rd(rec["spot"], 2), "spotSource": rec["spot_source"],
        "facts": [{"key": k, "value": f["value"], "unit": f["unit"], "basis": f["basis"],
                   "source": f["source"]} for k, f in (rec.get("facts") or {}).items()],
        "scenarios": [
            # (R3) revenue/margin EMITTED CONDITIONALLY, in place, for the same reason `eps` is:
            # a forward-P/E record carries neither — its record drops the keys rather than assert
            # a null someone looked for and did not find. The unconditional bracket read here was
            # what actually broke, and it broke in the real build rather than in a test: the card
            # builder wants them for DISPLAY, where a None would have rendered harmlessly, so
            # "the arithmetic would have failed first" was not true of this consumer. Order is
            # unchanged and R1/R2 records always carry both, so their cards stay byte-identical
            # under the emit-determinism pin.
            {"name": n,
             **({"revenue": s["revenue"]} if s.get("revenue") is not None else {}),
             **({"margin": s["margin"]} if s.get("margin") is not None else {}),
             "multiple": s["multiple"],
             "reason": s["reason"],
             **({"yearsToTerminal": s["years_to_terminal"]}
                if s.get("years_to_terminal") is not None else {}),
             # (R3) the P/E leg's only driver. Emitted the same conditional way as the horizon, so
             # R1/R2 cards stay byte-identical under the emit-determinism pin — and so a P/E card
             # stops showing every input EXCEPT the one that produced its value (review of #542).
             **({"eps": s["eps"]} if s.get("eps") is not None else {}),
             # (R4) NTM EBIT at exit, the EV/NTM EBIT leg's only driver — emitted the same
             # conditional way, so every R1/R2/R3 card stays byte-identical, and so an R4 card does
             # not show every input except the one that produced its value (#688's record).
             **({"ebit": s["ebit"]} if s.get("ebit") is not None else {}),
             **({"valuePerShare": _rd(o["value_per_share"], 2), "opIncome": _rd(o["op_income"], 1),
                 "ebitda": _rd(o["ebitda"], 1), "ev": _rd(o["ev"], 1),
                 "equity": _rd(o["equity"], 1), "evEbit": _rd(o.get("ev_ebit"), 1),
                 "normFcf": _rd(o.get("norm_fcf"), 1),
                 # (R2) the terminal-year bridge. Omitted wholesale on R1 records so their
                 # committed cards stay byte-identical under the emit-determinism pin.
                 **({"valueTerminal": _rd(o.get("value_terminal"), 2),
                     "years": o.get("years"), "dAndAT": _rd(o.get("d_and_a_t"), 1),
                     "netDebtT": _rd(o.get("net_debt_t"), 1),
                     "sharesT": _rd(o.get("shares_t"), 2)}
                    if o.get("value_terminal") is not None else {})}
                if (o := per.get(n)) is not None else {})}
            for n, s in (rec.get("scenarios") or {}).items()],
        # (R2) tier + hurdle + the survival gate. All omitted on R1 records.
        **({"tier": rec["tier"]} if rec.get("tier") else {}),
        **({"hurdle": r["hurdle"]} if r.get("hurdle") is not None else {}),
        **({"survival": {
            "status": sv["status"], "burn": _rd(sv.get("burn"), 1),
            "burnBasis": sv.get("burn_basis") or "", "burnSource": sv.get("burn_source") or "",
            "cash": _rd(sv.get("cash"), 1), "facilities": _rd(sv.get("facilities"), 1),
            "facilitiesSource": sv.get("facilities_source"),
            "runwayYears": _rd(sv.get("runway_years"), 2),
            "yearsToBreakeven": sv.get("years_to_breakeven"),
            "announcedRaise": bool(sv.get("announced_raise")),
            "raiseAccession": sv.get("raise_accession"),
            "note": sv.get("note") or "", "detail": list(sv.get("detail") or [])}}
           if (sv := r.get("survival")) else {}),
        "reward": _rd(r.get("reward"), 2), "risk": _rd(r.get("risk"), 2),
        "ratio": _rd(r.get("ratio"), 2), "bar": r.get("bar"),
        "ratioUndefined": r.get("ratio_undefined"), "passFail": r.get("pass_fail"),
        # THE SECOND TEST (2026-08-05): nominal 2:1 AND a base-case IRR floor AND a stated horizon.
        # OMITTED when absent — the `gateAdjudication` precedent below — so records written before
        # the convention stay byte-identical instead of gaining a wall of nulls.
        **({"irr": _rd(r.get("irr"), 4)} if r.get("irr") is not None else {}),
        **({"irrUndefined": r.get("irr_undefined")} if r.get("irr_undefined") else {}),
        **({"irrFloor": r.get("irr_floor")} if r.get("irr_floor") is not None else {}),
        **({"irrPassFail": r.get("irr_pass_fail")} if r.get("irr_pass_fail") else {}),
        **({"horizonYears": r.get("horizon_years")} if r.get("horizon_years") is not None else {}),
        **({"gate": r.get("gate")} if r.get("gate") else {}),
        # THE TIERED LADDER (2026-08-21): omitted when absent — same byte-identical rule as the
        # IRR block above, so every record judged under the 2:1/15% booleans stays unchanged and
        # the card renders the legacy-regime line from the ABSENCE of `gateRegime`. `eligible` is
        # three-state (False is a real answer), so its emit key is presence-of-the-regime, never
        # truthiness of the value.
        **({"gateRegime": r.get("gate_regime")} if r.get("gate_regime") else {}),
        **({"asymmetryTier": r.get("asymmetry_tier")} if r.get("asymmetry_tier") else {}),
        **({"returnTier": r.get("return_tier")} if r.get("return_tier") else {}),
        **({"eligibleRatio": r.get("eligible_ratio")}
           if r.get("eligible_ratio") is not None else {}),
        **({"eligibleIrr": r.get("eligible_irr")} if r.get("eligible_irr") is not None else {}),
        **({"eligible": r.get("eligible")} if r.get("gate_regime") else {}),
        **({"eligibleUndefined": r.get("eligible_undefined")}
           if r.get("eligible_undefined") else {}),
        **({"ceilingEligible": _rd(r.get("ceiling_eligible"), 2)}
           if r.get("ceiling_eligible") is not None else {}),
        **({"irrConvention": r.get("irr_convention")} if r.get("irr_convention") else {}),
        # gate_adjudication: a machine gate the human consciously overrode. OMITTED when absent so
        # records that never hit a gate stay byte-identical.
        **({"gateAdjudication": rec["gate_adjudication"]} if rec.get("gate_adjudication") else {}),
        # (record legibility) the MACHINE-DERIVED current state — the values the masthead band
        # reads. No longer takes the ledger row: the only thing it needed one for was the retired
        # holding trio, and the card binds its own ledger via `_ledger_for_record`.
        "currentState": _current_state(rec),
        # (supersession 2026-07-27) the two pointers, BOTH rendered as links. An archived record is
        # never hidden — it says what replaced it, and the live record says what it replaced, so a
        # reader can walk the chain in either direction without leaving the surface.
        **({"supersedes": rec["supersedes"]} if rec.get("supersedes") else {}),
        # (2026-09-01) THE ROW THIS RECORD'S PREDECESSOR OWNS. `_ledger_for_record` is correct to
        # withhold the row from a record underwritten AFTER the decision — that rule exists so a
        # reissue cannot headline a verdict it never made (SMPL, 2026-07-27). But the card then
        # printed "no ledger verdict logged" on a name that HAS a logged position, contradicting
        # its own appendix, and sub-labelled the entry with this record's date instead of the
        # date the position was actually opened. Both are the READER being misled by a rule that
        # is right about ownership: the answer is to name where the row lives, not to move it.
        # Emitted only when this record owns none itself, so a record with its own row is
        # byte-identical.
        **({"supersededLedger": sled} if sled else {}),
        **({"supersededBy": rec["superseded_by"]} if rec.get("superseded_by") else {}),
        **({"archiveKey": f'{str(rec["ticker"]).upper()}-{rec["underwrite_date"]}'}
           if rec.get("superseded_by") else {}),
        # the sidecar's classification of this record's PRE-GATE tags (+ any supersession).
        # Keyed by RECORD (ticker for live, archive key for archived) — a reissued live record
        # carries no tags, so it gets no index; the archived one keeps them.
        **({"amendmentIndex": _amendment_index()[_record_key(rec)]}
           if _amendment_index().get(_record_key(rec)) else {}),
        "verdict": {"status": v.get("status"), "recorded": v.get("recorded"),
                    # THE rationale — one field since 2026-07-22. `rationale_plain` is deprecated
                    # and deliberately NOT emitted: a card key nothing reads is a key that will be
                    # read again by mistake.
                    "rationale": v.get("rationale"),
                    "reunderwriteTriggers": v.get("reunderwrite_triggers") or [],
                    # (catalyst calendar) the analyst's DATED falsifiers. The md tier merges these
                    # into the calendar as `trigger-deadline` rows; the card never carried them, so
                    # the WEB silently rendered a SHORTER calendar than the PDF — SMPL showed 2 of
                    # 3 entries, and the missing one was the analyst's own falsifier. OMITTED when
                    # empty so trigger-less records stay byte-identical across re-emits. The
                    # sub-fields (trigger/deadline/basis) are single words — no case conversion.
                    **({"datedTriggers": v["dated_triggers"]} if v.get("dated_triggers") else {}),
                    # the human's FROZEN entry beside the underwrite's own ratio — the card must
                    # show what was accepted AT ENTRY, not only what the grid computed at spot.
                    # Keys OMITTED (never null) on a verdict that opened no position (watch /
                    # pending), so un-entered records stay byte-identical across re-emits.
                    # (The merge stacked this pair from BOTH #165 and the tear-sheet branch as
                    # duplicate dict keys — silently last-one-wins in Python; ONE emit now.)
                    **({"entryPrice": _rd(v["entry_price"], 2)}
                       if v.get("entry_price") is not None else {}),
                    **({"ratioAtEntry": _rd(v["ratio_at_entry"], 2)}
                       if v.get("ratio_at_entry") is not None else {}),
                    "avoidPriced": v.get("avoid_priced"),
                    "avoidPricedNote": v.get("avoid_priced_note")},
        # The LEDGER verdict of record (BUY / AVOID_TERMINAL) — the scenario record has no such
        # field, and the card must never invent one. Key OMITTED when the name has no ledger row,
        # so an un-logged name renders no verdict-of-record line (and stays byte-identical).
        # `closed` rides WITH the verdict so no surface can render the word "BUY" without the
        # fact that the position is closed (external-honesty pass 2026-07-27). Key omitted for an
        # open position → open cards stay byte-identical.
        # The BOOK rides with the verdict for the same reason `closed` does: the card renders a
        # verdict word, and a `PASS` on a quality name means "not at this price" where an
        # `AVOID_TERMINAL` on a screen name means "this is dying". A card showing the word without
        # the book cannot distinguish them. Emitted ONLY for a non-default book, so every existing
        # card stays byte-identical (the same omit-don't-null rule the keys above follow).
        **({"ledger": {"verdict": led["verdict"], "entryId": led["entry_id"],
                       "entryPrice": _rd(led.get("entry_price"), 2),
                       "entryPriceAsOf": led.get("entry_price_as_of"),
                       "decidedAt": led.get("decided_at"),
                       **({"sleeve": led["sleeve"]}
                          if (led.get("sleeve") or "overshoot") != "overshoot" else {}),
                       **({"closed": led["_closed"]} if led.get("_closed") else {}),
                       **({"correction": led["_correction"]} if led.get("_correction") else {})}}
           if led else {}),
    }


def _scenario_cards() -> dict[str, dict[str, Any]]:
    """Every committed underwrite record — LIVE keyed by ticker, ARCHIVED by archive key.

    Archived records are rendered and indexed, never hidden (supersession, 2026-07-27): the point
    of archive-and-reissue is that nothing is deleted, so a superseded record keeps its own page
    and its own link forward. They are excluded from the LIVE set that the audit, the monitor and
    the spread read — that exclusion is structural (those read `scenarios/*.json`, which does not
    recurse into `archive/`), so an archived record can never be scored or counted twice."""
    d = ROOT / "scenarios"
    if not d.is_dir():
        return {}
    ledger = _ledger_rows_by_ticker()
    out: dict[str, dict[str, Any]] = {}
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("_"):          # _schema.json and friends are not records
            continue
        rec = json.loads(p.read_text())
        out[str(rec["ticker"]).upper()] = _scenario_card(rec, ledger)
    arch = d / "archive"
    if arch.is_dir():
        for p in sorted(arch.glob("*.json")):
            if p.name.startswith("_"):
                continue
            rec = json.loads(p.read_text())
            out[p.stem.upper()] = _scenario_card(rec, ledger)
    return out


OUT_SCEN = HERE / "scenarios"


def emit_scenarios() -> list[str]:
    """Standalone `frontend/scenarios/` mirror — `index.json` {"tickers":[…]} + one `<TICKER>.json`
    per committed underwrite record, in the EXACT `_scenario_card()` shape (one contract, one
    consumer-side renderer; the theme JSON embedded it too until 2026-11-04). Deterministic +
    idempotent, so the committed output never churns; COMMITTED like `frontend/dossiers/` so the
    static serve works without a build step. Sits beside the dossier mirror: dossiers =
    assembled facts, scenarios = first-cut underwrites — the SHARED per-name surface types the
    two, never blends."""
    cards = _scenario_cards()
    if OUT_SCEN.exists():
        shutil.rmtree(OUT_SCEN)
    OUT_SCEN.mkdir(parents=True)
    for t, card in sorted(cards.items()):
        (OUT_SCEN / f"{t}.json").write_text(json.dumps(card, indent=1) + "\n")
    (OUT_SCEN / "index.json").write_text(
        json.dumps({"tickers": sorted(cards)}, indent=2) + "\n")
    return sorted(cards)


MON = ROOT / "data" / "monitor"
OUT_MON = HERE / "monitor"


def emit_monitor() -> list[str]:
    """Mirror the committed monitor history → `frontend/monitor/` + `index.json`
    {"days":[…], "latest": "YYYY-MM-DD"}, plus the benchmark assignments. The frontend reads the
    LATEST snapshot only — a committed, dated price, never a live fetch: the browser must not be
    able to show a mark the repo cannot reproduce. No history → nothing written and the live
    columns degrade to "—" (never a fabricated mark)."""
    if not MON.is_dir():
        return []
    days = sorted(p.stem for p in MON.glob("*.json") if p.name != "benchmark_assignments.json")
    if OUT_MON.exists():
        shutil.rmtree(OUT_MON)
    OUT_MON.mkdir(parents=True)
    for d in days:
        shutil.copyfile(MON / f"{d}.json", OUT_MON / f"{d}.json")
    asg = MON / "benchmark_assignments.json"
    if asg.exists():
        shutil.copyfile(asg, OUT_MON / "benchmark_assignments.json")
    (OUT_MON / "index.json").write_text(
        json.dumps({"days": days, "latest": days[-1] if days else None}, indent=2) + "\n")
    return days


def _screen_annotations(snap: Path) -> list[Any]:
    """Every committed screen-run annotation file, as written, in path order — what the queue view
    reads to mark a name (`frontend/lib/snapshots.js`). Validated by `vinci.screens.annotations`."""
    return [json.loads(p.read_text())
            for p in sorted((snap / "screen_runs").glob("*.annotations.json"))]


EV_MODULE = ROOT / "vinci" / "dossier" / "extraction_version.py"
EV_ENTRIES = ROOT / "vinci" / "dossier" / "extraction_versions"


def _extraction_versions(module: Path = EV_MODULE, entries: Path = EV_ENTRIES) -> dict[str, Any]:
    """``{"versions": {id: what it names}, "follows": {id: [the ids it follows]}}`` for every
    declared extraction vintage: the table the dossier page's stamp detail reads (`dossier.js`
    stampDetail), written to the git-ignored snapshot mirror on every deploy. ``follows`` is what
    tells a joined stamp (``A+B``, two heads merged in parallel) from two ids that never were.

    WHY HERE AND NOT A HAND-KEPT COPY (2026-11-11). The web twin was a second copy of the table that
    every output-changing PR appended to by hand, on the same lines as every other such PR. The
    table is now the frozen `LEGACY_VERSIONS` literal plus one file per vintage, and this reads
    both. It may not import vinci (the stdlib fence above), so the literal is read with `ast` —
    implicit string concatenation is resolved by the parser, so each row is the exact string.
    A parity test binds this to `vinci.dossier.extraction_version.EXTRACTION_VERSIONS`. Missing or
    malformed input raises: a deploy whose pages cannot say what their vintage names fails here."""
    tree = ast.parse(module.read_text(encoding="utf-8"))
    legacy = [ast.literal_eval(n.value) for n in tree.body
              if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
              and n.target.id == "LEGACY_VERSIONS" and n.value is not None]
    if len(legacy) != 1:
        raise RuntimeError(f"{module}: expected one LEGACY_VERSIONS literal, found {len(legacy)}")
    versions: dict[str, str] = {}
    follows: dict[str, list[str]] = {}
    prev: str | None = None
    for v, names in legacy[0]:  # each frozen row follows the row above it
        versions[str(v)], follows[str(v)], prev = str(names), [prev] if prev else [], str(v)
    if not entries.is_dir():
        raise RuntimeError(f"{entries} is missing — the vintages after the frozen table live there")
    for p in sorted(entries.glob("*.json")):
        entry = json.loads(p.read_text(encoding="utf-8"))
        if (not isinstance(entry, dict) or not isinstance(entry.get("id"), str)
                or not isinstance(entry.get("names"), str)
                or not isinstance(entry.get("follows"), list)
                or not all(isinstance(f, str) for f in entry["follows"])):
            raise RuntimeError(f"{p}: an extraction vintage holds a string id and names and a "
                               "list of the ids it follows")
        versions[entry["id"]] = entry["names"]
        follows[entry["id"]] = list(entry["follows"])
    return {"versions": versions, "follows": follows}




def _git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:  # noqa: BLE001 — provenance is best-effort; absence is shown as "—"
        return None


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description="Assemble the static snapshot mirror the dashboard serves."
    )
    ap.parse_args(argv)

    for d in (OUT_SNAP, OUT_DOSS):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    for name in _MIRRORED:
        shutil.copyfile(SNAP / name, OUT_SNAP / name)
    # SCREEN-RUN ANNOTATIONS (operator ruling 2026-10-26) — a note on a committed run's result that
    # later data showed was wrong; the queue view prints it under the name, the result stands. ONE
    # file, written even when empty, so an absent one is a deploy fault, never "none". Validated by
    # `vinci.screens.annotations` (tests); copied here as written.
    (OUT_SNAP / "screen_annotations.json").write_text(
        json.dumps(_screen_annotations(SNAP), indent=2) + "\n")
    # EXTRACTION VINTAGES — what each page's stamp names, read by the dossier page's Record &
    # reproduce row. Derived from vinci/dossier/ on every deploy, never committed (the function).
    (OUT_SNAP / "extraction_versions.json").write_text(
        json.dumps(_extraction_versions(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    # universe gate-exclusion health stats — present once the universe has been built with the
    # stats emit (vinci/universe.py). Absent on older snapshots → the ingestion screen degrades.
    if (SNAP / "universe_stats.json").exists():
        shutil.copyfile(SNAP / "universe_stats.json", OUT_SNAP / "universe_stats.json")

    # DERIVED dossiers only (data/dossiers/<TICKER>/dossier.json → dossiers/<TICKER>.json).
    # The index also carries a LABELS overlay — each committed dossier's CIQ-GICS industry
    # (status "present" only), so the ranker upgrades a name the moment its dossier commits,
    # without a queue re-emit. Stdlib twin of vinci.labels.committed_gics_index (the build fence
    # forbids the import) — a parity test pins the two against the real committed tree.
    # The index also carries READS — each dossier's synthesis ``evidence_balance`` VERBATIM, so the
    # index cards can tag a name with the machine's evidence lean at a glance. Emitted RAW and
    # UNPARSED on purpose: the "<lean> — <why>" split has exactly ONE shared JS parser
    # (dossier.js splitLean, mirroring vinci/dossier/verdict.py) and this build step must never
    # grow a third copy of that regex. WHAT THIS IS: the evidence LEAN, which the Brief already
    # shows openly with its rationale — NOT the machine's BUY/AVOID proposal, which stays sealed
    # until the human logs their verdict (the 2026-07-13 anti-anchoring pivot). Absent/blank
    # synthesis -> no entry (fail-honest; the card simply carries no tag, never a "neutral" one).
    tickers: list[str] = []
    labels: dict[str, dict[str, str]] = {}
    reads: dict[str, str] = {}
    # WHICH BOOK each name is judged under, so the SHELF can say so without opening the page.
    # The per-name JSON already carries it (the mirror is a byte copy), but the index is what the
    # grid reads — without it a quality name is indistinguishable from an overshoot one until you
    # open it, and its BUY/PASS vocabulary and different question then arrive unexplained.
    sleeves: dict[str, str] = {}
    if DOSS.exists():
        for folder in sorted(p for p in DOSS.iterdir() if p.is_dir()):
            f = folder / "dossier.json"
            if f.is_file():
                ticker = folder.name.upper()
                shutil.copyfile(f, OUT_DOSS / f"{ticker}.json")
                # the rendered markdown rides the mirror too, so the dossier page can offer it as
                # a download. Same licensing status as the JSON beside it — DERIVED analysis, not
                # reproduced CIQ — so it is committed under exactly the same rule.
                md = folder / "dossier.md"
                if md.is_file():
                    shutil.copyfile(md, OUT_DOSS / f"{ticker}.md")
                tickers.append(ticker)
                doc = json.loads(f.read_text())
                ind = doc.get("industry") or {}
                if ind.get("status") == "present" and (ind.get("value") or "").strip():
                    labels[ticker] = {"industry": ind["value"].strip(), "source": "ciq-gics",
                                      "source_ref": ind.get("source_ref") or ""}
                eb = ((doc.get("synthesis") or {}).get("evidence_balance") or "").strip()
                if eb:
                    reads[ticker] = eb
                # ABSENT == the default book, exactly as the model reads it: every dossier
                # committed before the tag existed is overshoot, which is truthful (the screen was
                # their only route). Emitted for every name so the shelf never has to guess.
                sleeves[ticker] = str(doc.get("sleeve") or "overshoot")
    # EVERY FOLLOWED NAME AND ITS BOOK, read verbatim from the committed follow file — the file
    # `vinci log-verdict` itself reads to open its ticker door. The page needs it to print a
    # command the CLI accepts: a followed name logs by TICKER, not by a candidate id it never had.
    # Names without a dossier ride along (a follow can precede its first assembly). The route rule
    # lives in dossier.js `logVerdictId`; this only mirrors the file, and refuses a shape the CLI
    # would refuse rather than guessing a book.
    followed: dict[str, str] = {}
    fpath = ROOT / "data" / "followed.json"
    if fpath.exists():
        fdoc = json.loads(fpath.read_text())
        if not isinstance(fdoc, dict):
            raise SystemExit(f"{fpath} must map TICKER -> {{reason, sleeve, ...}}")
        for key, entry in fdoc.items():
            if not (isinstance(entry, dict) and isinstance(entry.get("sleeve"), str)):
                raise SystemExit(f"{fpath}: {key} carries no sleeve — every followed name states "
                                 f"its book")
            followed[str(key).upper()] = entry["sleeve"].strip()
    (OUT_DOSS / "index.json").write_text(
        json.dumps({"tickers": tickers, "labels": labels, "reads": reads,
                    "sleeves": sleeves, "followed": followed}, indent=2))

    scen_tickers = emit_scenarios()
    mon_days = emit_monitor()

    # DERIVED EDGAR-10-K exposure map → slim graph.json (edges + shared nodes + headline stats).
    # Authorized for the private/authed repo as a derived artifact (CLAUDE.md) and COMMITTED there
    # (verbatim PUBLIC 10-K phrases + relationship-TYPE taxonomy only, no CIQ workbook data); the
    # deploy regenerates graph.json from it. If absent (e.g. a public repo) the graph screen
    # degrades to UNKNOWN.
    if GRAPH.exists():
        g = json.loads(GRAPH.read_text())
        slim = {
            "model": g.get("model"),
            "stats": {
                "names": g.get("n_names"),
                "withEdges": g.get("names_with_edges"),
                "totalEdges": g.get("total_edges"),
                "realEdges": g.get("real_edges"),
                "realUsListed": g.get("real_us_listed"),
            },
            "edges": [
                {
                    "focal": e.get("focal_ticker"),
                    "counterpartyName": e.get("counterparty_name"),
                    "counterpartyTicker": e.get("counterparty_ticker"),
                    "relType": e.get("relationship_type"),
                    "direction": e.get("direction"),
                    "resolution": e.get("node_kind"),
                    "evidence": e.get("evidence"),
                }
                for e in g.get("edges", [])
            ],
            "sharedNodes": g.get("shared_nodes", []),
            "superConnectors": g.get("super_connectors", []),
        }
        (OUT_SNAP / "graph.json").write_text(json.dumps(slim))

    # manifest.json — the cheap index. Regenerated every build, so it cannot drift
    # from the snapshots. Only carries what the UI can't cheaply derive client-side.
    queue = _jsonl(SNAP / "ranked_queue.jsonl")
    uni_path = SNAP / "universe_snapshot.jsonl"
    uni = _jsonl(uni_path) if uni_path.exists() else []
    manifest = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "source_commit": _git_sha(),
        "universe": {"count": len(uni), "as_of": (uni[0].get("as_of") if uni else None)},
        "screen": {
            "candidates": len(queue),
            "as_of": (
                str(queue[0].get("screen_run_at"))[:10]
                if queue and queue[0].get("screen_run_at")
                else None
            ),
        },
        # THE LAST RUN'S OUTCOME, folded in rather than mirrored as its own file — the manifest is
        # already fetched on every screen, so run health costs no extra request. Written by the
        # weekly job's always-runs reporting step (weekly-screen.yml); ABSENT until the first run
        # under that step, and absent is rendered as "unknown", never as success. This is the ONLY
        # thing on the served surface that can distinguish "a run failed" from "nobody ran one":
        # every other freshness number here is the age of what was COMMITTED, and a failed run
        # commits nothing.
        **({"run": json.loads((SNAP / "run_status.json").read_text())}
           if (SNAP / "run_status.json").exists() else {}),
        # Queue summary counts so the overview reads two numbers from this ~200-byte file instead
        # of fetching + parsing the full ~440 KB ranked_queue.jsonl to show them. The full queue
        # still loads lazily on the Ranker screen, where it's actually needed.
        "queue": {
            "total": len(queue),
            "demoted": sum(1 for r in queue if r.get("structurally_disqualified")),
            "gated": sum(1 for r in queue if r.get("tradeability_gated")),
        },
    }
    (OUT_SNAP / "manifest.json").write_text(json.dumps(manifest, indent=2))

    # G3 (multiple) UNKNOWN disambiguation — split the ambiguous "XBRL absent / negative earnings"
    # into the actual per-name reason (label-integrity), derived from the committed candidate facts.
    cand_path = SNAP / "candidate_records.jsonl"
    g3: dict[str, str] = {}
    if cand_path.exists():
        for row in _jsonl(cand_path):
            payload = row.get("payload")
            p = json.loads(payload) if isinstance(payload, str) else (payload or row)
            dr = p.get("data_record", p)
            f = dr["fundamentals"]
            ev = f.get("ev_ebitda_pctile_vs_history") or {}
            pe_pct = f.get("pe_pctile_vs_history") or {}
            if ev.get("coverage_status") == "present" or pe_pct.get("coverage_status") == "present":
                continue  # multiple is known — no disambiguation needed
            pe = f.get("pe") or {}
            ois = f.get("op_income_sign") or {}
            fcf = f.get("fcf_sign") or {}
            neg = (ois.get("value") is not None and ois["value"] < 0) or (
                fcf.get("value") is not None and fcf["value"] < 0
            )
            if neg:
                reason = "negative earnings — no meaningful P/E"
            elif pe.get("coverage_status") != "present":
                reason = "multiple data absent — EDGAR XBRL gap"
            else:
                reason = "P/E present, no 5y percentile — insufficient history"
            g3[dr["identity"]["ticker"]] = reason
    (OUT_SNAP / "g3_reasons.json").write_text(json.dumps(g3))

    print(
        f"mirror: {len(queue)} queue rows, {len(uni)} universe rows, "
        f"{len(tickers)} dossier(s) [{', '.join(tickers) or 'none'}], "
        f"{len(scen_tickers)} underwrite(s) [{', '.join(scen_tickers) or 'none'}], "
        f"{len(mon_days)} monitor day(s) [latest {mon_days[-1] if mon_days else 'none'}] "
        "→ frontend/"
    )


if __name__ == "__main__":
    main()
