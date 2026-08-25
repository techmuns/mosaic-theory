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
import json
import re
import shutil
import subprocess
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SNAP = ROOT / "data" / "snapshots"
DOSS = ROOT / "data" / "dossiers"
GRAPH = ROOT / "data" / "graph_coverage.json"  # DERIVED EDGAR-10-K exposure map (private-repo only)
FORWARD = ROOT / "data" / "forward"  # git-ignored staging for the frozen theme-edge freeze
#                                      artifacts
OUT_SNAP = HERE / "snapshots"
OUT_DOSS = HERE / "dossiers"
OUT_THEMES = HERE / "themes"  # COMMITTED display JSON (like dossiers) — the deployable theme copy

# The lightweight snapshots the UI fetches at runtime. The MB-scale candidate /
# universe / securities files are intentionally NOT mirrored — their derived
# counts go into manifest.json instead, so the deploy stays small.
_MIRRORED = ("ranked_queue.jsonl", "decision_ledger.jsonl")


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# --- MIRROR RE-SEED GUARD -----------------------------------------------------------------------
# 4th worktree-provenance incident; 2nd sweep.json re-seed. A generated artifact whose SOURCE is
# absent in THIS worktree must be left BYTE-UNTOUCHED — never regenerated from seeds/defaults.
# The failure this kills: a build run from a worktree without data/scan_history/manifest.jsonl
# silently rewrote the COMMITTED frontend/radar/sweep.json back to the seeded June-17 date, so a
# real sweep looked stale. The same class covers theme freezes (git-ignored source) and the radar
# inbox/log. ONE implementation, so the discipline can't drift between emitters.
def _preserve_unless_source(label: str, artifact: Path, *, source_present: bool) -> bool:
    """True ⇒ the caller may regenerate. False ⇒ it MUST leave the artifact untouched.

    Source absent + artifact present → the deploy / other-worktree case: the committed file is the
    only good copy, so keep it and say so. Source absent + artifact ALSO missing → nothing to
    preserve and nothing to serve; that is a real breakage, so raise rather than emit a seeded
    placeholder (fail loud, never fabricate)."""
    if source_present:
        return True
    if artifact.exists():
        print(f"SKIPPED {label}: source absent")
        return False
    raise SystemExit(
        f"{label}: source absent AND artifact missing ({artifact}) — nothing to preserve")


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

    The card renders on surfaces that never load the ledger snapshot (the theme watchlist embeds
    its card into the frozen theme JSON), so the join happens HERE, at build, not in the client.
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
        for cand in reversed(found):
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
    return {
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
            {"name": n, "revenue": s["revenue"], "margin": s["margin"], "multiple": s["multiple"],
             "reason": s["reason"],
             **({"yearsToTerminal": s["years_to_terminal"]}
                if s.get("years_to_terminal") is not None else {}),
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
                       **({"closed": led["_closed"]} if led.get("_closed") else {})}}
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
    """Standalone `frontend/scenarios/` mirror — `index.json` {"tickers":[…]} + one
    `<TICKER>.json` per committed underwrite record, in the EXACT `_scenario_card()` shape the
    theme JSON embeds (one contract, one consumer-side renderer). Deterministic + idempotent, so
    the committed output never churns; COMMITTED like `frontend/dossiers/` so the static serve
    works without a build step. Sits beside the dossier mirror: dossiers = assembled facts,
    scenarios = first-cut underwrites — the SHARED per-name surface types the two, never blends."""
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
CALLS = ROOT / "data" / "calls"
OUT_CALLS = HERE / "calls"


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


def _mirror_calls() -> list[str]:
    """Mirror data/calls/<handle>/ -> frontend/calls/<handle>/ for every account present.

    WHOLE-TREE COPY, deliberately. Unlike the snapshot mirror there is no per-file allowlist: an
    account's shape is its own (a file per month of posts, a file per tracked ticker's bars), and
    an allowlist would silently drop a new month the moment the corpus grew. What IS enforced is
    that an account carries a meta.json — a stray directory is skipped rather than half-served.

    ``results.jsonl`` rides along when present; it is written by `vinci calls score`, and without
    it the chart readout degrades to "not scored" rather than to a fabricated number.
    """
    if not CALLS.is_dir():
        return []
    if OUT_CALLS.exists():
        shutil.rmtree(OUT_CALLS)
    OUT_CALLS.mkdir(parents=True)
    idx = CALLS / "accounts.json"
    if idx.exists():
        shutil.copyfile(idx, OUT_CALLS / "accounts.json")
    handles: list[str] = []
    for d in sorted(x for x in CALLS.iterdir() if x.is_dir()):
        if not (d / "meta.json").is_file():
            continue
        shutil.copytree(d, OUT_CALLS / d.name)
        handles.append(d.name)
    return handles


def _git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:  # noqa: BLE001 — provenance is best-effort; absence is shown as "—"
        return None


# --------------------------------------------------------------------------------------------------
# Theme-edge freeze → committed display JSON (mirrors the dossier flow, with ONE difference: the
# frozen SOURCE (forward_*_baskets.json + _ledger.jsonl) is GIT-IGNORED, so on the Cloudflare deploy
# it is ABSENT. This step is therefore NON-DESTRUCTIVE when the source is missing — it leaves the
# COMMITTED frontend/themes/*.json in place (never rmtree's them). It only regenerates when a local
# run points --themes-src at the freeze artifacts. Read-only transform; no backend import.
# --------------------------------------------------------------------------------------------------
# slug + display label per driver (falls back to a slugified driver string for a future theme)
_DRIVER_SLUG: dict[str, tuple[str, str]] = {
    "AI-datacenter value chain": ("ai-datacenter", "AI-datacenter"),
    "defense-demand-shift": ("defense", "Defense demand-shift"),
    "truckload-supply-purge": ("truckload-supply-purge", "Truckload supply purge"),
}
# the concreteness → rank ladder + the driver-tie gate, mirroring vinci.themes.exposure so the tier
# shape derives IDENTICALLY from the ledger's (grade, driver_tie) as the backend's exposure_basis.
_CONC_RANK = {"none": 0, "stated-intent": 1, "committed-capacity": 2,
              "quantified-revenue": 3, "binding-contract": 4}
_BASIS = {0: "none", 1: "aspirational", 2: "committed", 3: "quantified", 4: "binding"}
# scan exposure_basis → tier bucket (the FULL theme exposure shape lives in the scan, not the
# freeze; a freeze may scope a subset — ai-datacenter froze only its committed enablers, defense
# froze all 108)
_SCAN_BASIS = {
    "binding-contracts-with-terms": "binding", "quantified-revenue-share": "quantified",
    "committed-capacity-or-capex": "committed", "aspirational-intent-only": "aspirational",
    "no-theme-exposure-disclosed": "none",
}
_ACC_RE = re.compile(r"\d{10}-\d{2}-\d{6}")
# mirrors vinci.themes.forward — the zero-RATIFIED honesty label + the UNDEFINED-with-reason
# measures + the §4 power-floor note. Kept as literals here so build.py stays stdlib-only
# (deploy-safe); a regression test pins them equal to the backend's (tests/test_build_themes.py).
_HOLD_NONE_HONESTY = (
    "No BUY leg exists (zero RATIFIED) -> the core edge-measure (RATIFIED-PASSED) and all "
    "RATIFIED-dependent spreads are UNDEFINED and NOT computed. The outputs below are "
    "AVOID-discipline and exposure-carry DIAGNOSTICS, beta-confounded, and are NOT a validation "
    "of the semantic-primary edge."
)
_UNDEFINED_REASON = "no BUY leg — zero RATIFIED; requires a ratified cohort that does not exist"
_UNDEFINED_MEASURES = [
    ["RATIFIED-PASSED (§3a, the core edge-measure)", _UNDEFINED_REASON],
    ["RATIFIED-NAIVE(equal-weight) (§3b-i)", _UNDEFINED_REASON],
    ["RATIFIED vs keyword/co-movement screen (§3b-ii, deferred)", _UNDEFINED_REASON],
]
_POWER_NOTE = (
    "UNPOWERED — DIRECTIONAL / ANECDOTAL: below the a-priori floor (needs >=8 theme-quarters "
    "across >=4 drivers, sign-consistent). A forward-directional read, never a significance test."
)


# First-path segments the themes sub-router owns (plus legacy redirects) — a theme slug that
# collides would be unroutable, so the build fails LOUD rather than shipping a shadowed page.
_RESERVED_SLUGS = frozenset({"radar", "watchlist", "scan", "forward"})


def _slug(driver: str) -> tuple[str, str]:
    if driver in _DRIVER_SLUG:
        s, label = _DRIVER_SLUG[driver]
    else:
        s = re.sub(r"[^a-z0-9]+", "-", driver.lower()).strip("-") or "driver"
        label = driver
    if s in _RESERVED_SLUGS:
        raise SystemExit(f"theme slug {s!r} collides with a reserved themes route "
                         f"({', '.join(sorted(_RESERVED_SLUGS))}) — rename the driver")
    return s, label


def _eff_basis(grade: str, tie: str) -> str:
    """Effective basis after the driver-tie gate — mirrors vinci.themes.exposure._effective_rank:
    driver-specific keeps the concreteness rank; indirect caps at committed; not-driver at
    aspirational."""
    r = _CONC_RANK.get(grade, 0)
    if tie in ("driver-specific", "chain-layer-specific"):
        pass
    elif tie == "indirect":
        r = min(r, 2)
    else:  # not-driver (or anything unrecognized — conservative)
        r = min(r, 1)
    return _BASIS[r]


def _acc(source_ref: str) -> str | None:
    m = _ACC_RE.search(source_ref or "")
    return m.group(0) if m else None


def _edgar_url(cik: str | None, source_ref: str) -> str | None:
    acc = _acc(source_ref)
    if not acc or not cik:
        return None
    try:
        c = str(int(cik))
    except (TypeError, ValueError):
        return None
    return f"https://www.sec.gov/Archives/edgar/data/{c}/{acc.replace('-', '')}/{acc}-index.htm"


def _theme_display(baskets: dict[str, Any], ledger: list[dict[str, Any]],
                   scan: list[dict[str, Any]] | None) -> dict[str, Any]:
    """The display subset the 4 theme views read — cohorts, tier shape, per-name grade_fact +
    accession + rationale + trigger, the UNDEFINED-spread reasons, and the honesty label."""
    driver = baskets["driver"]
    slug, label = _slug(driver)
    wl_set, ac_set = set(baskets.get("watchlist", [])), set(baskets.get("avoid_controls", []))
    rt_set = set(baskets.get("real_tier", []))
    triggers = baskets.get("watchlist_triggers", {}) or {}

    tier = {"binding": 0, "quantified": 0, "committed": 0, "aspirational": 0}
    cats: Counter[str] = Counter()
    names: list[dict[str, Any]] = []
    for r in ledger:
        tag = r.get("chain_layer") or r.get("substructure_tag") or "unspecified"
        grade = r.get("machine_grade") or r.get("grade") or "none"
        tie = r.get("driver_tie", "")
        basis = _eff_basis(grade, tie)
        if basis in tier:
            tier[basis] += 1
        cats[tag] += 1
        cohorts = ([c for c, s in
                    (("watchlist", wl_set), ("avoid-control", ac_set), ("real", rt_set))
                    if r["ticker"] in s])
        names.append({
            "ticker": r["ticker"], "substructureTag": tag, "driverTie": tie, "grade": grade,
            "basis": basis, "gradeFact": r.get("grade_fact", ""),
            "accession": _acc(r.get("source_ref", "")),
            "edgarUrl": _edgar_url(r.get("cik"), r.get("source_ref", "")),
            "rationale": r.get("rationale", ""), "cohorts": cohorts,
        })
    _rank = {"binding": 0, "quantified": 1, "committed": 2, "aspirational": 3, "none": 4}
    names.sort(key=lambda n: (_rank.get(n["basis"], 9), n["ticker"]))
    by_ticker = {n["ticker"]: n for n in names}

    # FROZEN tier = the dispositioned ledger set (defense 108 = all surfaced; ai-datacenter 56 =
    # the committed enablers only). The TIER SHAPE is the theme's FULL exposure shape from the scan
    # (so none + surfaced + tiers reconcile to the universe); it degrades to the frozen breakdown
    # (no none/universe) when no scan is present.
    frozen = len(ledger)
    if scan is not None:
        sc: Counter[str] = Counter(
            _SCAN_BASIS.get(s.get("exposure_basis", ""), "none") for s in scan
        )
        surfaced = len(scan) - sc["none"]
        tier_shape = {"binding": sc["binding"], "quantified": sc["quantified"],
                      "committed": sc["committed"], "aspirational": sc["aspirational"],
                      "none": sc["none"], "surfaced": surfaced, "universe": len(scan)}
    else:
        surfaced = frozen
        tier_shape = {**tier, "none": None, "surfaced": frozen, "universe": None}

    cards = _scenario_cards()

    def _detail(t: str, extra: dict[str, Any]) -> dict[str, Any]:
        n = by_ticker.get(t, {})
        base = {k: n.get(k, "") for k in
                ("substructureTag", "grade", "basis", "gradeFact", "accession", "edgarUrl",
                 "rationale")}
        # attach ONLY when an underwrite record exists — names without one stay byte-identical
        card = {"scenarioCard": cards[t]} if t in cards else {}
        return {"ticker": t, **base, **extra, **card}

    watchlist = [_detail(t, {"trigger": triggers.get(t, "")}) for t in baskets.get("watchlist", [])
                 if t in by_ticker]
    avoid_controls = [_detail(t, {}) for t in baskets.get("avoid_controls", []) if t in by_ticker]
    categories = [{"tag": k, "n": v} for k, v in cats.most_common()]

    # NAIVE cohort = the equal-weight baseline over the WHOLE committed tier — mirrors the
    # backend's len(baskets.all_committed) (forward.py "NAIVE-N", cli.py:689). NOT `surfaced`
    # (scan breadth): a theme that froze a SUBSET of the surfaced universe (ai-datacenter: 56
    # committed of 450 surfaced) would otherwise render an ~8x-overstated NAIVE cohort next to
    # the tier-scale buy/passed pills. Fall back to the frozen ledger size for a freeze that
    # predates the all_committed field.
    naive_n = len(baskets.get("all_committed") or []) or frozen
    forward = {
        "cohorts": {"buy": len(baskets.get("ratified", [])), "naive": naive_n,
                    "passed": len(baskets.get("passed", [])),
                    "watchlist": len(baskets.get("watchlist", [])),
                    "avoidControls": len(ac_set), "realTier": len(rt_set)},
        "undefinedMeasures": _UNDEFINED_MEASURES,
        "diagnostics": [
            {"name": "avoid-discipline", "status": "PENDING",
             "confound": f"{driver}-BETA-CONFOUNDED + regime-dependent — was declining to buy the "
                         f"committed tier costly or vindicated in THIS window? Largely a "
                         f"{driver}-beta bet, NOT selection skill.",
             "note": "0 days forward from freeze — accrues over calendar time."},
            {"name": "exposure-carry", "status": "PENDING",
             "confound": f"PARTIALLY beta-controlled — both cohorts are {driver}-labelled so the "
                         f"common {driver}-beta largely cancels in the divergence; isolates "
                         "whether the exposure GRADE (real vs not) carries forward info. The more "
                         "informative of the two — still NOT an edge verdict.",
             "note": "genuine-exposure (watchlist) vs other-PASSED divergence; pending forward."},
        ],
        "honestyLabel": _HOLD_NONE_HONESTY,
        "powerNote": _POWER_NOTE,
    }
    # frozen tier counts — the DRILLABLE buckets (every count here has per-name detail in names[]):
    # firm = REAL (binding + quantified), partial = committed, early = aspirational. The magnitude
    # words are the portfolio-altitude labels; the underlying grade tiers are unchanged.
    frozen_tiers = {
        "firm": sum(1 for n in names if n["basis"] in ("binding", "quantified")),
        "partial": sum(1 for n in names if n["basis"] == "committed"),
        "early": sum(1 for n in names if n["basis"] == "aspirational"),
    }
    return {
        "driver": driver, "slug": slug, "label": label,
        "freezeDate": (baskets.get("freeze_timestamp") or "")[:10],
        "freezeTimestamp": baskets.get("freeze_timestamp", ""),
        "ratifiedCount": len(baskets.get("ratified", [])), "surfacedCount": surfaced,
        "frozenCount": frozen, "watchlistCount": len(baskets.get("watchlist", [])),
        "tierShape": tier_shape, "frozenTiers": frozen_tiers, "categories": categories,
        "names": names, "watchlist": watchlist, "avoidControls": avoid_controls,
        "realTier": list(baskets.get("real_tier", [])), "forward": forward,
    }


# a-priori power floor — mirrors vinci.themes.forward.MIN_DRIVERS (never tuned on returns)
_MIN_THEMES = 4


def _theme_index(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(summaries)
    total_buys = sum(s["ratifiedCount"] for s in summaries)
    total_wl = sum(s["watchlistCount"] for s in summaries)
    return {
        "drivers": summaries,
        "crossDriver": {
            "driversFrozen": n, "totalRatified": total_buys, "totalWatchlist": total_wl,
            "line": (f"{n} theme{'s' if n != 1 else ''} in snapshot; exposure-carry diagnostic "
                     f"poolable but UNPOWERED ({n} < {_MIN_THEMES} themes)."),
        },
        # the POOLED forward state — cross-theme facts that live at the portfolio altitude (not per
        # theme). On the snapshot day every horizon is 0 days forward → everything PENDING.
        "pooledForward": {
            "totalBuys": total_buys,
            "totalWatchlist": total_wl,
            "powerFloor": {
                "themes": n, "needed": _MIN_THEMES,
                "pct": min(100, round(100 * n / _MIN_THEMES)),
                "label": f"{n} of ~{_MIN_THEMES}-{_MIN_THEMES + 1} themes — unpowered",
            },
            "undefinedMeasures": _UNDEFINED_MEASURES,
            "honestyLabel": _HOLD_NONE_HONESTY,
            "diagnostics": [
                {"name": "exposure-carry", "status": "PENDING",
                 "note": "genuine-exposure vs other-PASSED divergence, pooled across themes — "
                         "PARTIALLY beta-controlled; the more informative of the two; pending "
                         "forward."},
                {"name": "avoid-discipline", "status": "PENDING",
                 "note": "was declining to buy the committed tier costly or vindicated, pooled — "
                         "beta-confounded; pending forward."},
            ],
        },
    }


def build_themes(themes_srcs: list[Path]) -> list[str]:
    """Transform each discovered freeze (one driver per src dir: forward_*_baskets.json + its
    _ledger.jsonl (+ any *scan*.jsonl for the none count)) into COMMITTED
    frontend/themes/<slug>.json + index.json. NON-DESTRUCTIVE: if NO source is found (the Cloudflare
    deploy — the source is git-ignored), it leaves the committed output untouched and WARNs, so the
    Edge-2 frontend and any prior theme commit still build/serve."""
    pairs: list[tuple[Path, Path, Path | None]] = []
    for d in themes_srcs:
        if not d.exists():
            continue
        for bp in sorted(d.glob("forward_*_baskets.json")):
            lp = bp.with_name(bp.name[: -len("_baskets.json")] + "_ledger.jsonl")
            if not lp.exists():
                print(f"WARN theme: {bp.name} has no sibling {lp.name} — skipped")
                continue
            scans = sorted(d.glob("*scan*.jsonl"))
            pairs.append((bp, lp, scans[0] if scans else None))
    # RE-SEED GUARD (same class as sweep.json): no freeze source in this worktree — e.g. the
    # Cloudflare deploy, where the source is git-ignored — ⇒ keep the committed theme JSON.
    # The embedded underwrite CARDS are the one part the guard's own principle still permits:
    # their source is the COMMITTED scenarios/ records + ledger snapshot (present even where the
    # freeze source is not), so they refresh in place while every other byte of the theme JSON
    # stays preserved. With no committed records, refresh_theme_cards() is a no-op — the same
    # source-absent discipline, one level down.
    if not _preserve_unless_source("frontend/themes/", OUT_THEMES, source_present=bool(pairs)):
        refresh_theme_cards()
        return []
    OUT_THEMES.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    for bp, lp, sp in pairs:
        baskets = json.loads(bp.read_text())
        display = _theme_display(baskets, _jsonl(lp), _jsonl(sp) if sp else None)
        (OUT_THEMES / f"{display['slug']}.json").write_text(json.dumps(display, indent=1))
        summaries.append({k: display[k] for k in ("slug", "label", "freezeDate", "ratifiedCount",
                          "surfacedCount", "frozenCount", "watchlistCount", "tierShape",
                          "frozenTiers")})
    summaries.sort(key=lambda s: s["slug"])
    (OUT_THEMES / "index.json").write_text(json.dumps(_theme_index(summaries), indent=1))
    return [s["slug"] for s in summaries]


def refresh_theme_cards() -> list[str]:
    """Re-embed the underwrite cards inside the COMMITTED theme JSONs from the COMMITTED records.

    The theme display JSON embeds each watch name's `scenarioCard` so the watchlist renders without
    a second fetch — but it is normally rewritten only by a full freeze, whose source
    (`forward_*_baskets.json`) is GIT-IGNORED. That made the embedded card un-regenerable in CI: any
    change to the card's shape left the committed theme copy stale, with a pin asserting the two are
    identical and no way to satisfy it. This refreshes JUST the embedded cards in place — every
    other byte of the theme JSON is untouched — so a card-shape change propagates to the watchlist
    from committed inputs alone. A name whose record has since been deleted keeps its embedded copy
    (removing it is a freeze decision, not a render one); a theme with no cards is left alone."""
    if not OUT_THEMES.is_dir():
        return []
    cards = _scenario_cards()
    touched: list[str] = []
    for p in sorted(OUT_THEMES.glob("*.json")):
        if p.name == "index.json":
            continue
        display = json.loads(p.read_text())
        changed = False
        # the display JSON's actual list keys (_theme_display emits camelCase avoidControls;
        # a snake_case sweep key here would silently never match)
        for key in ("watchlist", "avoidControls"):
            for row in display.get(key) or []:
                t = str(row.get("ticker", "")).upper()
                if "scenarioCard" in row and t in cards and row["scenarioCard"] != cards[t]:
                    row["scenarioCard"] = cards[t]
                    changed = True
        if changed:
            p.write_text(json.dumps(display, indent=1))
            touched.append(p.stem)
    if touched:
        print(f"themes: re-embedded underwrite cards in {', '.join(touched)}")
    return touched


# --------------------------------------------------------------------------------------------------
# Radar sweep bar — last-run / next-due (+30d) for the Component-A co-movement sweep. The CANONICAL
# invocation is recorded ONCE here (and in STATE §5 "CANONICAL invocation — recorded HERE, the ONE
# place; the future Radar screen MUST source it from here, no second hardcoding"); the frontend
# RENDERS this string, never hardcodes it. Display-only reminder — nothing fires automatically.
# --------------------------------------------------------------------------------------------------
_SWEEP_COMMAND = "python -m vinci.cli themes"
_SWEEP_SEED_DATE = "2026-06-17"  # the June-17 harvest — seeded last_run until a manifest exists
_SWEEP_CADENCE_DAYS = 30


def _radar_sweep_payload(manifest: Path) -> dict[str, str]:
    """Compute the sweep payload: last_run (latest ts of a COMPONENT-A row in the ROOT scan-history
    manifest, else the seeded June-17 harvest), source (manifest|seeded), next_due (+30d), and the
    canonical command. Pure — testable without the frontend dir. Refreshes on the next site build.

    `record_snapshot` writes ONE multi-driver manifest at data/scan_history/manifest.jsonl (each row
    carries a `driver_slug`), so the sweep bar must FILTER to `component-a` before taking the latest
    ts — a later row from another driver must not masquerade as the co-movement sweep's last run."""
    if manifest.exists():
        rows = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
        ca_ts = (str(r.get("ts", "")) for r in rows if r.get("driver_slug") == "component-a")
        ts = max(ca_ts, default="")
        last_run, source = (ts[:10] if ts else _SWEEP_SEED_DATE), ("manifest" if ts else "seeded")
    else:
        last_run, source = _SWEEP_SEED_DATE, "seeded"
    next_due = (date.fromisoformat(last_run) + timedelta(days=_SWEEP_CADENCE_DAYS)).isoformat()
    return {"last_run": last_run, "source": source, "next_due": next_due, "command": _SWEEP_COMMAND}


def emit_radar_sweep() -> None:
    """Write frontend/radar/sweep.json for the sweep bar (display-only — nothing fires). Reads
    the ROOT manifest where record_snapshot writes (data/scan_history/manifest.jsonl); the prior
    component-a/manifest.jsonl path never existed, so the bar re-seeded silently (the #125 bug)."""
    out = HERE / "radar"
    manifest = ROOT / "data" / "scan_history" / "manifest.jsonl"
    # RE-SEED GUARD: no manifest in this worktree ⇒ keep the committed sweep.json. Regenerating
    # would re-seed a real sweep date back to the June-17 default (the incident this guards).
    if not _preserve_unless_source(
            "sweep.json", out / "sweep.json", source_present=manifest.exists()):
        return
    out.mkdir(parents=True, exist_ok=True)
    (out / "sweep.json").write_text(json.dumps(_radar_sweep_payload(manifest), indent=1) + "\n")


# --------------------------------------------------------------------------------------------------
# Radar INBOX + REVIEW LOG — join the latest component-a snapshot × analyst-owned reviews.json.
# The machine ASSEMBLES: match clusters to reviewed groups by MEMBER OVERLAP (ids are per-run,
# never match on id), sorting into inbox (unjudged) vs log (reviewed). It NEVER decides —
# reviews.json is the single record; a drifted match re-entering the inbox is CORRECT, not an
# error. Non-destructive: absent snapshot/reviews → keep the committed files (deploy-safe).
# --------------------------------------------------------------------------------------------------
_MATCH_MIN = 0.5  # member overlap as a fraction of the SMALLER set


def _overlap(a: set[str], b: set[str]) -> float:
    """|a ∩ b| / min(|a|, |b|) — overlap as a fraction of the smaller set (0 if either is empty)."""
    return len(a & b) / min(len(a), len(b)) if a and b else 0.0


def _latest_component_a(root: Path) -> Path | None:
    """Newest local/committed component-a snapshot (timestamp-prefixed filename → lexical max)."""
    snaps = sorted((root / "data" / "scan_history" / "component-a").glob("*.jsonl"))
    return snaps[-1] if snaps else None


def _sig(cluster: dict[str, Any], *keys: str) -> float | None:
    """Dig a numeric strength/admissibility value; None if any hop is missing (never fabricate)."""
    node: Any = cluster
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            return None
        node = node[k]
    return node if isinstance(node, (int, float)) else None


def _industry_hint(cluster: dict[str, Any]) -> str | None:
    """Most common member INDUSTRY + coverage ("Services-Prepackaged Software · 7/7"); a single
    industry or a strict majority → that; else "mixed: <top> N · <second> M". The names are the
    OFFICIAL SEC SIC titles, attached to member rows by the backend resolver (vinci.labels) at
    sweep time — build.py (stdlib fence) aggregates, it never maintains a naming map. PRE-FIELD
    snapshots (members lack `industry`) degrade to the raw `SIC <code>` — 4-digit specificity is
    kept, a name is never fabricated. Assemble-only hint — never a verdict. Deterministic."""
    members = cluster.get("members", [])
    vals = Counter((str(m.get("industry") or "")).strip() for m in members)
    vals.pop("", None)
    if not vals:  # pre-field snapshot → raw SIC codes, loudly un-named
        vals = Counter(f"SIC {str(m.get('sic') or '').strip()}" for m in members
                       if str(m.get("sic") or "").strip())
        if not vals:
            return None
    total = len(members)
    ranked = vals.most_common()
    top, top_n = ranked[0]
    if len(ranked) == 1 or top_n * 2 > total:  # single industry, or a strict majority
        return f"{top} · {top_n}/{total}"
    second, sn = ranked[1]
    return f"mixed: {top} {top_n} · {second} {sn}"


def _draft_pairs(out: Path) -> list[tuple[set[str], dict[str, Any]]]:
    """DRAFTED records from radar/drafts.json as (member-set, record) pairs for a member-overlap
    join into the inbox. Only status=='drafted' with a name (unassessed-errors carry no draft).
    Empty when the file is absent (deploy-safe). The draft is ADVISORY — never marks a decision."""
    path = out / "drafts.json"
    if not path.exists():
        return []
    drafts = json.loads(path.read_text()).get("drafts", [])
    return [({t for t in d.get("members", []) if t}, d)
            for d in drafts if d.get("status") == "drafted" and d.get("draft_name")]


def _match_draft(cluster_set: set[str],
                 pairs: list[tuple[set[str], dict[str, Any]]]) -> dict[str, Any] | None:
    """Best-overlap drafted record for a cluster (≥ _MATCH_MIN of the smaller set), else None.
    Member-overlap join, not cluster_id (ids are per-run) — mirrors the reviews matcher above."""
    cand = [(s, d) for s, d in pairs if _overlap(cluster_set, s) >= _MATCH_MIN]
    if not cand:
        return None
    return max(cand, key=lambda sd: _overlap(cluster_set, sd[0]))[1]


def _inbox_entry(cluster: dict[str, Any], first_seen: str,
                 draft: dict[str, Any] | None = None) -> dict[str, Any]:
    """One inbox row for an unreviewed cluster (display-only stats; machine never decides). When an
    advisory draft matches, carry its name / read (terse reason) / suggestion — advisory, not a
    verdict; the fuller hypothesis stays in drafts.json (the machine-complete record)."""
    members = [m["ticker"] for m in cluster.get("members", [])]
    label = " ".join(members[:2]) + (f" +{len(members) - 2}" if len(members) > 2 else "")
    return {
        "cluster_id": cluster["cluster_id"], "first_seen": first_seen, "members": members,
        "label": label, "industry_hint": _industry_hint(cluster),
        "rel12": _sig(cluster, "strength_signals", "rel_strength_vs_market", "h12mo", "value"),
        "mom12": _sig(cluster, "strength_signals", "momentum", "h12mo", "value"),
        "coherence": _sig(cluster, "admissibility", "coherence_value"),
        "breadth_exp": _sig(cluster, "strength_signals", "breadth_expanding", "value"),
        "crowding": _sig(cluster, "strength_signals", "crowding_overextension", "value"),
        "draft_name": draft.get("draft_name") if draft else None,
        "draft_read": draft.get("reason") if draft else None,
        "draft_suggested": draft.get("suggested") if draft else None,
    }


# Review-decision vocabulary — the analyst record (reviews.json) is VERBATIM and human-written;
# this seam canonicalizes shorthand at EMIT time so the renderer's label/filter vocab holds
# (reviews.json stays untouched — the record is the record). An unmapped decision fails the
# build LOUD: extend the map consciously, never render an unknown pill.
_CANON_DECISION = {"advanced": "advanced", "watch": "watch", "parked": "parked",
                   "rejected": "rejected", "park": "parked", "reject": "rejected"}


def emit_radar_inbox_log() -> None:
    """Sort the latest component-a clusters into inbox (unreviewed) vs log (matched to a review), by
    member overlap ≥ _MATCH_MIN of the smaller set. Emits frontend/radar/{inbox,log}.json; assembles
    only — reviews.json is the single record. Non-destructive when a source is absent."""
    out = HERE / "radar"
    reviews_path = out / "reviews.json"
    snap_path = _latest_component_a(ROOT)
    # RE-SEED GUARD (same class as sweep.json): deploy / no local run → keep the committed
    # inbox.json + log.json rather than emitting an empty pair over the last real emission.
    if not _preserve_unless_source(
            "radar inbox.json + log.json", out / "inbox.json",
            source_present=snap_path is not None and reviews_path.exists()):
        return
    reviews = json.loads(reviews_path.read_text())["reviews"]
    clusters = [json.loads(line) for line in snap_path.read_text().splitlines() if line.strip()]
    if clusters and not any((str(m.get("industry") or "")).strip()
                            for c in clusters for m in c.get("members", [])):
        print("radar inbox: component-a snapshot predates member.industry — "
              "raw-SIC hints until the next sweep")
    m = re.match(r"(\d{4})(\d{2})(\d{2})", snap_path.name)
    scan_iso = "-".join(m.groups()) if m else ""

    review_sets = {r["key"]: set(r["members"]) for r in reviews}
    cluster_sets = {c["cluster_id"]: {mem["ticker"] for mem in c.get("members", [])}
                    for c in clusters}

    # LOG: every review + its current match status (best-overlap current cluster + membership delta)
    log_reviews = []
    for r in sorted(reviews, key=lambda r: r["key"]):
        rset = review_sets[r["key"]]
        cand = sorted((cid for cid, cs in cluster_sets.items() if _overlap(cs, rset) >= _MATCH_MIN))
        if cand:
            best = max(cand, key=lambda cid: _overlap(cluster_sets[cid], rset))  # ties → lowest cid
            cs = cluster_sets[best]
            match = {"status": "matched", "cluster_id": best,
                     "added": sorted(cs - rset), "dropped": sorted(rset - cs)}
        else:
            match = {"status": "gone", "cluster_id": None, "added": [], "dropped": []}
        canon = _CANON_DECISION.get(str(r.get("decision") or ""))
        if canon is None:
            raise SystemExit(f"unknown radar decision {r.get('decision')!r} in reviews.json "
                             f"({r.get('key')}) — extend _CANON_DECISION or fix the record")
        log_reviews.append({**r, "decision": canon, "match": match})

    # INBOX: current clusters matched by NO review (not yet judged). An advisory draft (if any) is
    # joined by member overlap — it informs the row, never marks it reviewed.
    draft_pairs = _draft_pairs(out)
    inbox = sorted(
        (_inbox_entry(c, scan_iso, _match_draft(cluster_sets[c["cluster_id"]], draft_pairs))
         for c in clusters
         if not any(_overlap(cluster_sets[c["cluster_id"]], rs) >= _MATCH_MIN
                    for rs in review_sets.values())),
        key=lambda e: e["cluster_id"])

    (out / "inbox.json").write_text(
        json.dumps({"scan_date": scan_iso, "inbox": inbox}, indent=1, ensure_ascii=False) + "\n")
    (out / "log.json").write_text(
        json.dumps({"scan_date": scan_iso, "reviews": log_reviews},
                   indent=1, ensure_ascii=False) + "\n")
    gone = sum(1 for r in log_reviews if r["match"]["status"] == "gone")
    print(f"radar inbox+log: {len(clusters)} clusters → {len(clusters) - len(inbox)} matched / "
          f"{len(inbox)} inbox; {len(log_reviews)} reviews ({gone} gone)")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description="Assemble the static snapshot mirror the dashboard serves."
    )
    ap.add_argument("--themes-src", nargs="*", dest="themes_src", default=None,
                    help="dir(s) each holding ONE driver's frozen freeze (forward_*_baskets.json + "
                         "_ledger.jsonl, + any *scan*.jsonl for the none count). "
                         "Default: data/forward/. Absent → the committed frontend/themes/ is left "
                         "untouched.")
    args = ap.parse_args(argv)

    for d in (OUT_SNAP, OUT_DOSS):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    for name in _MIRRORED:
        shutil.copyfile(SNAP / name, OUT_SNAP / name)
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
    (OUT_DOSS / "index.json").write_text(
        json.dumps({"tickers": tickers, "labels": labels, "reads": reads,
                    "sleeves": sleeves}, indent=2))

    scen_tickers = emit_scenarios()
    mon_days = emit_monitor()
    calls_handles = _mirror_calls()

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

    # THEME-EDGE display JSON — non-destructive when the (git-ignored) freeze source is absent.
    theme_srcs = [Path(p) for p in (args.themes_src or [FORWARD])]
    theme_slugs = build_themes(theme_srcs)

    # Radar sweep bar — regenerated every build (manifest git-ignored → seeded; a run refreshes).
    emit_radar_sweep()
    # Radar inbox + review log — sort latest clusters into unreviewed vs reviewed (non-destructive).
    emit_radar_inbox_log()

    print(
        f"mirror: {len(queue)} queue rows, {len(uni)} universe rows, "
        f"{len(tickers)} dossier(s) [{', '.join(tickers) or 'none'}], "
        f"{len(scen_tickers)} underwrite(s) [{', '.join(scen_tickers) or 'none'}], "
        f"{len(mon_days)} monitor day(s) [latest {mon_days[-1] if mon_days else 'none'}], "
        f"{len(calls_handles)} calls account(s) [{', '.join(calls_handles) or 'none'}], "
        f"{len(theme_slugs)} theme(s) [{', '.join(theme_slugs) or 'none'}] → frontend/"
    )


if __name__ == "__main__":
    main()
