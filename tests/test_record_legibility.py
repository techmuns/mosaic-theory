"""RECORD LEGIBILITY (2026-07-27) — amendment classes, the refresh path, the current-state block.

THE DEFECT these pin. SMPL's rationale reached 450 words of which 330 (73%) was amendment, and a
reader met the sealed 2026-07-21 thesis FIRST — before any indication that the position had since
been closed, the record moved to watch, and the base margin re-set. The rationale was correct and
sealed; it simply could not say what was true now. Three fixes, pinned here:

* amendment CLASSES, so a leg change is distinguishable from a system correction, with caps that
  keep the trail proportionate and `machine` refused from the rationale entirely;
* a real REFRESH PATH, so a machine refresh has somewhere to go that is not the sealed field;
* the CURRENT-STATE block, machine-derived and rendered first.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

from vinci import scenarios as sc
from vinci import seal

ROOT = Path(__file__).resolve().parents[1]


def _load_build() -> Any:
    spec = importlib.util.spec_from_file_location("_legib_build", ROOT / "frontend" / "build.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_BUILD: Any = _load_build()


# --- amendment classes: the caps, the rejection, legacy acceptance -----------------------------
def test_judgment_cap_is_100_words() -> None:
    """100, not 60: SMPL's 161-word re-verification carried a leg change, its evidence AND its
    fragility disclosure — three things that legitimately co-occur. A 60-word cap would have
    forced one of them out of the record, which is the opposite of legibility."""
    ok = f"[amended 2026-07-28 (judgment): {' '.join(['word'] * 100)}.]"
    over = f"[amended 2026-07-28 (judgment): {' '.join(['word'] * 101)}.]"
    assert seal.amendment_violations(f"Thesis. {ok}") == []
    v = seal.amendment_violations(f"Thesis. {over}")
    assert len(v) == 1 and "101 words against a 100-word cap" in v[0]


def test_process_cap_is_25_words_because_it_is_a_pointer() -> None:
    ok = f"[amended 2026-07-28 (process): {' '.join(['word'] * 25)}.]"
    over = f"[amended 2026-07-28 (process): {' '.join(['word'] * 26)}.]"
    assert seal.amendment_violations(f"Thesis. {ok}") == []
    v = seal.amendment_violations(f"Thesis. {over}")
    assert "26 words against a 25-word cap" in v[0] and "POINTER" in v[0]


def test_machine_class_is_refused_from_the_rationale_at_any_length() -> None:
    """The specimen: SMPL's 88-word "machine refresh on current data" tag changed two numbers and
    cost a fifth of the record's prose. Refused outright now — length is irrelevant."""
    for n in (5, 88):
        v = seal.amendment_violations(
            f"Thesis. [amended 2026-07-28 (machine): {' '.join(['word'] * n)}.]")
        assert len(v) == 1 and "REJECTED from the rationale" in v[0] and "refresh_log" in v[0]


def test_class_required_only_from_the_gate_date_legacy_stays_legal() -> None:
    """NOT retroactive. Every one of the five tags on the committed records predates the gate and
    must stay legal unclassed — a rule that invalidates the records it was written for is a rule
    that will be ignored."""
    assert seal.amendment_violations("Thesis. [amended 2026-07-26: no class, legacy.]") == []
    assert seal.amendment_violations("Thesis. [amended 2026-07-22: no class, legacy.]") == []
    v = seal.amendment_violations("Thesis. [amended 2026-07-27: no class, post-gate.]")
    assert len(v) == 1 and "declares no class" in v[0]
    # a legacy tag is also NOT cap-checked — the caps bind forward with the classes
    assert seal.amendment_violations(
        f"Thesis. [amended 2026-07-26: {' '.join(['word'] * 400)}.]") == []


def test_every_committed_record_is_class_compliant_and_seal_clean() -> None:
    """THE ARTIFACT PIN: the new contract must not redden the records that motivated it."""
    man = seal.load_manifest(ROOT)
    recs = {p.stem: json.loads(p.read_text())
            for p in (ROOT / "scenarios").glob("*.json") if not p.stem.startswith("_")}
    # (31b) RELATIONAL floor — unfiltered, so the seal check must cover the whole corpus.
    assert recs, ("no committed records — check_all([]) is vacuously clean and this test would "
                  "certify an empty book as seal-compliant")
    assert seal.check_all(recs, man) == []
    checked = 0
    for t, r in recs.items():
        checked += 1
        assert seal.amendment_violations((r.get("verdict") or {}).get("rationale")) == [], t
    assert checked == len(recs)


def test_tag_parts_reads_date_class_and_body_length() -> None:
    assert seal.tag_parts("[amended 2026-07-28 (judgment): three little words.]") \
        == ("2026-07-28", "judgment", 3)
    assert seal.tag_parts("[amended 2026-07-22: three little words.]") == ("2026-07-22", None, 3)


# --- the refresh path: it moves machine inputs and REFUSES analyst surfaces --------------------
def _rec() -> sc.ScenarioRecord:
    return sc.read_record("SMPL", root=ROOT)


def test_refresh_moves_machine_inputs_and_logs_provenance() -> None:
    before = _rec()
    out = sc.refresh_record(before, spot=11.11, facts={"ltm_revenue": 1400.0},
                            source="Polygon close; CIQ grid", on_date="2026-07-28")
    added = out.refresh_log[len(before.refresh_log):]
    assert {e.field for e in added} == {"spot", "facts.ltm_revenue"}
    for e in added:
        assert e.date == "2026-07-28" and e.source == "Polygon close; CIQ grid"
        assert e.old and e.new and e.old != e.new
    assert out.spot == 11.11 and out.facts["ltm_revenue"].value == 1400.0
    assert out.result.ratio != before.result.ratio      # the engine recomputed


def test_refresh_refuses_every_analyst_surface() -> None:
    """The constitutional line: a refresh may never move judgment. An analyst-owned input is not
    even expressible here, and the legs/verdict/assumptions are asserted unchanged on the way out.
    """
    rec = _rec()
    with pytest.raises(sc.RefreshRefusedError, match="not a refreshable machine fact"):
        sc.refresh_record(rec, facts={"margin": 0.16}, source="s", on_date="2026-07-28")
    # a REFRESHABLE fact the record does NOT carry: a refresh updates what the analyst already
    # recorded, it never introduces a new input (SMPL carries all six, so strip one to build it)
    stripped = rec.model_copy(update={
        "facts": {k: v for k, v in rec.facts.items() if k != "cash_interest"}})
    with pytest.raises(sc.RefreshRefusedError, match="never introduces one"):
        sc.refresh_record(stripped, facts={"cash_interest": 1.0},
                          source="s", on_date="2026-07-28")
    with pytest.raises(sc.RefreshRefusedError, match="must state its SOURCE"):
        sc.refresh_record(rec, spot=9.9, source="   ", on_date="2026-07-28")
    out = sc.refresh_record(rec, spot=9.9, source="s", on_date="2026-07-28")
    assert out.scenarios == rec.scenarios and out.verdict == rec.verdict
    assert out.assumptions == rec.assumptions
    assert out.verdict.rationale == rec.verdict.rationale     # the sealed field is untouched


def test_refresh_is_a_noop_when_nothing_moved() -> None:
    rec = _rec()
    assert sc.refresh_record(rec, spot=rec.spot, source="s", on_date="2026-07-28") is rec


def test_a_retired_field_is_refused_loudly_not_dropped_quietly() -> None:
    """`status_note` was retired 2026-07-27 — the header is the rating alone, so nothing rendered
    it. Pydantic's default is extra="ignore", which would have made every stale record load CLEAN
    and lose the analyst's sentence on the next write. Silent loss is the one failure this repo
    never takes: the load RAISES and names the key, so the words are migrated or discarded by
    a decision, never by omission."""
    assert "status_note" in sc.RETIRED_VERDICT_FIELDS
    assert not hasattr(sc.Verdict(status="watch"), "status_note")
    with pytest.raises(ValueError, match="retired field"):
        sc.Verdict.model_validate({"status": "watch", "status_note": "a caption"})
    # the schema no longer advertises it, so nothing downstream can start writing it again
    assert "status_note" not in (ROOT / "scenarios" / "_schema.json").read_text()
    # and no committed record still carries it — live or archived
    live = (ROOT / "scenarios").glob("*.json")
    archived = (ROOT / "scenarios" / "archive").glob("*.json")
    for p in [*live, *archived]:
        if p.name.startswith("_"):
            continue
        assert "status_note" not in p.read_text(), f"{p.name} still carries the retired key"


# --- the current-state block -------------------------------------------------------------------
def test_next_evidence_prefers_the_calendar_then_a_trigger_then_says_unknown() -> None:
    """RESOLUTION ORDER (ratified). SMPL carries BOTH a calendar print (2026-10-08) and a dated
    trigger (2027-01-07); the calendar must win — leading with the trigger would misstate "next
    evidence" by a full quarter. A record with NEITHER must say UNKNOWN, never invent.

    The no-source fixture is WERN, not AORT: AORT gained a real calendar row on 2026-07-27, which
    is the right outcome and exactly why a LIVING record makes a poor "absent" fixture. WERN has
    no dossier at all (so no calendar can exist for it) and no dated triggers — a structural
    UNKNOWN rather than a temporary one."""
    smpl = _BUILD._next_evidence("SMPL", {"dated_triggers": [
        {"deadline": "2027-01-07", "trigger": "the analyst's falsifier"}]})
    assert smpl["date"] == "2026-10-08" and "catalyst calendar" in smpl["source"]
    assert not (ROOT / "data" / "dossiers" / "WERN").exists(), "WERN gained a dossier — re-pick"
    wern = _BUILD._next_evidence("WERN", {})
    assert wern["date"] == "UNKNOWN" and wern["source"] == "none on file"
    # with no calendar on file, the dated trigger is the fallback — not UNKNOWN
    fb = _BUILD._next_evidence("NO_SUCH_TICKER", {"dated_triggers": [
        {"deadline": "2027-01-07", "trigger": "t"}]})
    assert fb["date"] == "2027-01-07" and fb["source"] == "analyst dated trigger"


def test_the_holding_question_is_answered_by_the_band_not_a_dead_key() -> None:
    """A status word alone misleads: SMPL reads `watch` while its position is CLOSED, and the
    reader needs "not held" in words. That answer MOVED rather than disappeared — the at-a-glance
    fold put it in the ENTRY cell, so `held` / `holdingLabel` became emitted-and-unread and were
    retired with `statusNote`. Pin the answer where it now lives, so this cannot regress into a
    card that states the holding nowhere."""
    s = _BUILD._current_state(json.loads((ROOT / "scenarios" / "SMPL.json").read_text()))
    assert "held" not in s and "holdingLabel" not in s, "the retired trio must not come back"
    card = (ROOT / "frontend" / "views" / "shared" / "uw-card.js").read_text()
    ratio = card[card.index("function ratioCell"):]
    entry = card[card.index("ENTRY"):]
    assert "no position" in entry, "the ENTRY cell must state a record that holds nothing"
    assert ratio, "ratioCell still carries the ceiling sub-line the band reads"
    # and a closed position states its close in the verdict chip itself
    assert "— closed " in card, "the verdict chip carries the close"


def test_current_state_carries_the_decision_numbers_and_both_dates() -> None:
    """The card must TRANSPORT the record's decision numbers — asserted against the record itself,
    never against frozen literals.

    TEST-LAYER RULE (2026-07-31). This pinned `ratio == 3.83` and `ceiling2to1 == 12.72` on a LIVING
    committed artifact, so it reddened the moment the record legitimately moved — item 24 swapped
    SMPL's denominator to diluted shares outstanding and the ratio became 4.78. Nothing was broken;
    the pin was reading a VALUE where it should have been reading a DERIVATION. Its own sibling
    assertion already knew — the `underwriteDate` line says a frozen literal "would pin the
    pre-supersession vintage forever" — the reasoning was simply not carried across the test."""
    rec = json.loads((ROOT / "scenarios" / "SMPL.json").read_text())
    s = _BUILD._current_state(rec)
    r = rec["result"]
    assert s["ratio"] == pytest.approx(r["ratio"], abs=0.005), "the card recomputed the ratio"
    assert s["bar"] == r["bar"] == 2.0, "the ratified 2:1 bar is not the one on the card"
    assert s["passFail"] == r["pass_fail"] and s["passFail"] in {"PASS", "FAIL", "UNDEFINED"}
    # TRANSPORT, PROVEN BY MOVING THE INPUT. Equality against the live record cannot distinguish
    # "the card carries the record's verdict" from "the card hardcodes the value this record
    # happens to have" — a mutation that pinned `passFail: "PASS"` sailed through the assertion
    # above. Feed a record that says something else and the card must say it too.
    flipped = json.loads(json.dumps(rec))
    flipped["result"]["pass_fail"] = "FAIL"
    flipped["result"]["ratio"] = 1.11
    moved = _BUILD._current_state(flipped)
    assert moved["passFail"] == "FAIL" and moved["ratio"] == pytest.approx(1.11, abs=0.005), (
        "the card does not follow the record — these numbers are being produced, not transported")
    # the ceiling is DERIVED — the spot at which (base−spot)/(spot−bear) equals the bar — so it is
    # checked by its arithmetic, which a value literal never did
    per = r["per_scenario"]
    expected = ((per["base"]["value_per_share"] + r["bar"] * per["bear"]["value_per_share"])
                / (1.0 + r["bar"]))
    assert s["ceiling2to1"] == pytest.approx(expected, abs=0.02), (
        "ceiling2to1 is not the spot at which reward:risk falls to the bar")
    # the underwrite date is the RECORD's own — SMPL was reissued 2026-07-27, so a frozen
    # literal here would pin the pre-supersession vintage forever
    assert s["spot"] == pytest.approx(rec["spot"], abs=0.005) and s["spotSource"]
    assert s["underwriteDate"] == rec["underwrite_date"]


# --- SUPERSESSION: archive-and-reissue (2026-07-27) --------------------------------------------
def test_archived_records_leave_the_live_set_but_stay_in_the_seal_sweep() -> None:
    """THE TWO-SIDED SCOPE RULE, both halves pinned.

    OUT of the live set: the audit, the monitor and the spread read `scenarios/*.json`, which does
    NOT recurse into `archive/` — so a superseded record can never be scored, counted or audited a
    second time. IN the seal sweep: superseding must not become a way to move a sealed rationale
    out from under the seal. An archived record is still the record of what was believed."""
    live = sc.all_records(root=ROOT)
    archived = sc.all_archived(root=ROOT)
    assert archived, "the committed book carries at least one archived record"
    assert set(live) & set(archived) == set(), "an archive key must never collide with a ticker"
    for key, rec in archived.items():
        assert rec.superseded_by, f"{key} is archived but points nowhere"
        assert key not in live, f"{key} is in the LIVE set — audit/spread would double-count"
    # the seal sweep DOES cover them, keyed as the manifest keys them
    sealable = seal.load_all_sealable(ROOT)
    for key in archived:
        assert key in sealable, f"{key} escaped the seal sweep"
    assert seal.check_all(sealable, seal.load_manifest(ROOT)) == []


def test_supersession_links_both_ways_and_never_edits_the_archived_rationale() -> None:
    """The pair is bidirectional and the archived copy differs from its original by ONE field."""
    live = sc.read_record("SMPL", root=ROOT)
    key = live.supersedes
    assert key, "the reissued SMPL record must point back at what it replaced"
    arch = sc.read_archived(key, root=ROOT)
    assert arch.superseded_by == sc.archive_key(live), "the archived record must point forward"
    assert sc.archive_key(arch) == key
    # the reissue is CLEAN: no amendment tags carried over into the new sealed text
    assert seal.amendments(live.verdict.rationale or "") == []
    # ...AND NO ARCHIVED RECORD EVER LOSES ITS AMENDMENTS. Asserted on the record that HAS them
    # rather than on whatever `live.supersedes` happens to point at: the 2026-08-05 supersession
    # archived SMPL-2026-07-27, itself a clean reissue carrying zero, so a bare `== 3` against the
    # newest archive reddened on a legitimate event while saying nothing about preservation. The
    # 1.2 record is the one that accumulated three, and it is the one worth watching.
    assert len(seal.amendments(
        sc.read_archived("SMPL-2026-07-21", root=ROOT).verdict.rationale or "")) == 3, (
        "SMPL-2026-07-21 lost amendment tags from its sealed rationale — an archived record is "
        "history and is never edited")


def test_supersede_refuses_a_live_position_and_a_one_way_link() -> None:
    """A LIVE position is AMENDED, never superseded — reissuing would move the thesis out from
    under an open position. Proven by the refusal, not by the docstring."""
    live = sc.read_record("SMPL", root=ROOT)
    arch = sc.read_archived(str(live.supersedes), root=ROOT)
    confirmed = arch.model_copy(update={
        "verdict": arch.verdict.model_copy(update={"status": "confirmed"})})
    with pytest.raises(sc.SupersedeRefusedError, match="LIVE position"):
        sc.supersede_record(confirmed, live, live_confirmed_open=True)
    with pytest.raises(sc.SupersedeRefusedError, match="ticker mismatch"):
        sc.supersede_record(arch, live.model_copy(update={"ticker": "AORT"}))
    with pytest.raises(sc.SupersedeRefusedError, match="already points at"):
        sc.supersede_record(arch, live.model_copy(update={"supersedes": "XXXX-2020-01-01"}))
    with pytest.raises(sc.SupersedeRefusedError, match="no close row"):
        sc.supersede_record(confirmed, live, closed_entry_ids=set())


def test_supersession_did_not_touch_the_ledger() -> None:
    """A reissue is a RECORD event, not a transaction: no new ledger row, nothing mutated. The
    forward spread must be identical before and after — supersession cannot launder a track."""
    led = (ROOT / "data" / "snapshots" / "decision_ledger.jsonl").read_text().splitlines()
    rows = [json.loads(x) for x in led if x.strip()]
    smpl = {r["entry_id"] for r in rows if r["ticker"] == "SMPL"}
    # THE ORIGINAL PAIR IS INTACT — that is the claim, and it is not a row COUNT. The first cut
    # asserted `len(smpl) == 2`, true only while SMPL held no later position; the 2026-08-05
    # verdict added a third row and reddened this on a deliberate act no supersession performed.
    # A supersession cannot launder a track by REMOVING or MUTATING what is already there; a
    # separate, later log-verdict is free to append. Both survive here.
    assert {"V-SMPL-screen2-20260706", "C-SMPL-screen2-20260706"} <= smpl, (
        "the 2026-07 decision/close pair left the ledger — a supersession must never remove a "
        "row; the forward spread has to be identical before and after")
    orig = [r for r in rows if r["entry_id"] == "V-SMPL-screen2-20260706"][0]
    assert orig["entry_price"] == 10.92 and orig["verdict"] == "BUY", (
        "the sealed decision row was mutated — supersession is a RECORD event, not a transaction")


# --- what the RENDERED PAGE showed (2026-07-27, found by looking) ------------------------------
def test_supersession_links_use_the_apps_hash_route_not_a_query_string() -> None:
    """FOUND BY LOOKING AT THE PAGE, not by reading code. The banners shipped with
    `href="?scenario=…"` — a query string, in an app that routes entirely on the hash
    (`#/dossier/<key>`). Both links rendered, looked right, and would have dumped the reader at
    the app root with the route lost. Same lesson as #216: the card renderer passing in isolation
    proves nothing about the page."""
    src = (ROOT / "frontend" / "views" / "shared" / "uw-card.js").read_text()
    assert "?scenario=" not in src, "supersession links must not use a query string"
    banner = src[src.index("function supersessionBanner"):]
    banner = banner[:banner.index("\n}")]
    assert banner.count('href="#/dossier/') == 2, (
        "both directions (archived→live, live→archived) must link on the app's hash route")


def test_one_amendment_marker_shared_by_the_card_and_the_dossier() -> None:
    """The dossier's thesis block carried a SECOND copy of the amendment-tag regex, and that copy
    never learned about CLASSED tags — so `[amended 2026-07-28 (judgment): …]` rendered marked on
    the card and UNMARKED in the Brief. Two divergent parsers of one string is the named bug
    class; this pins the single shared helper."""
    card = (ROOT / "frontend" / "views" / "shared" / "uw-card.js").read_text()
    doss = (ROOT / "frontend" / "views" / "shared" / "dossier.js").read_text()
    assert "export function amendMarks" in card, "amendMarks must be the exported shared helper"
    assert "amendMarks" in doss.split("\n")[9], "the dossier must IMPORT it"
    # the dossier must no longer carry its own copy of the tag regex
    assert r"\[amended (\d{4}-\d{2}-\d{2})" not in doss, (
        "the dossier is parsing amendment tags itself again — use the shared amendMarks")


# --- at-a-glance v2 + the ledger binding (2026-07-27) ------------------------------------------
def test_a_reissued_record_does_not_inherit_the_ledger_row_it_never_made() -> None:
    """THE SUPERSESSION BUG. The ledger joined by TICKER alone, which was right while one ticker
    meant one record. SMPL's BUY was decided 2026-07-21 against the record now ARCHIVED; the live
    record was reissued 2026-07-27 and opened no position (`entry_price` is None) — yet its card
    headlined that BUY, and the SAME row displayed on two records.

    RULE: a record owns the row only if the row was decided during its tenure."""
    ledger = _BUILD._ledger_rows_by_ticker()
    live = json.loads((ROOT / "scenarios" / "SMPL.json").read_text())
    arch = json.loads((ROOT / "scenarios" / "archive" / "SMPL-2026-07-21.json").read_text())
    owned = _BUILD._ledger_for_record(arch, ledger)
    assert owned and owned["entry_id"] == "V-SMPL-screen2-20260706", (
        "the 2026-07-21 record lost the row decided during ITS tenure")
    # THE RULE NOW HAS A POSITIVE CASE, which is strictly stronger. The first cut asserted the live
    # record owns NOTHING — true only while every SMPL decision pre-dated it. The 2026-08-05
    # reissue had a verdict logged against it the same day, so it legitimately owns THAT row, and
    # a bare `is None` reddened on the rule working. Ownership is tenure in both directions.
    live_owned = _BUILD._ledger_for_record(live, ledger)
    assert (live_owned or {}).get("entry_id") != "V-SMPL-screen2-20260706", (
        "the reissued record claimed a row decided before it existed — the supersession bug")
    if live_owned is not None:
        assert live_owned["decided_at"][:10] >= live["underwrite_date"], (
            f"the live record owns {live_owned['entry_id']} decided "
            f"{live_owned['decided_at'][:10]} against an underwrite dated "
            f"{live['underwrite_date']} — a record cannot own a row that pre-dates it")
    # a never-superseded name is unaffected: one record, it owns its row
    it = json.loads((ROOT / "scenarios" / "IT.json").read_text())
    assert (_BUILD._ledger_for_record(it, ledger) or {}).get("entry_id") == "V-IT-screen2-20260706"


def test_close_rows_are_not_positions_in_the_js_ledger_loader() -> None:
    """The loader mapped EVERY row into `entries`, so a closed name counted twice — a close row
    repeats the ORIGINAL verdict for provenance. The dashboard read 5 logged / 4 BUY against a
    true 3 / 2. JS twin of vinci.monitor.decision_rows: partition, then attach."""
    src = (ROOT / "frontend" / "lib" / "snapshots.js").read_text()
    body = src[src.index("async function _loadLedger"):]
    body = body[:body.index("\n}")]
    assert '.filter((p) => !p.event)' in body, "close rows must be filtered out of entries"
    assert "closes_entry_id" in body and "closeBy" in body, "closes must be paired to their row"
    assert "realizedReturn" in body, "realized return is derived here, never stored"


def test_at_a_glance_v2_cell_count_matches_its_grid_and_ranks_by_fact_class() -> None:
    """v1 proposed a 6th stat cell for `next evidence`. Wrong twice: `.uw-statband` was
    repeat(5,1fr), so a 6th cell dropped Method to a ragged second row; and a DATE at the 16.5px
    mono of `.uw-stat-val` reads with a valuation number's authority. Dates belong in the
    pre-existing `.uw-mast-foot` (11.2px ink-3), and the status caption is a CAPTION — prose never
    sits between the title and the numbers.

    **THE BAND IS SIX CELLS SINCE 2026-08-05** — the base-case IRR joined it as a PEER of the
    reward:risk cell when the convention became nominal 2:1 AND an IRR floor AND a stated horizon.
    v1's objection was never "five is sacred", it was "cells and columns must not disagree", so
    that is what this pins now: the count and the grid are asserted AGAINST EACH OTHER rather than
    against a constant. Add a seventh cell without widening the grid and this reddens exactly as it
    did for v1; move both together and it stays green — which is the contract that was always
    meant. The date rule is untouched and still pinned below: an IRR is a RATE, and rates are what
    this band is for."""
    import re as _re
    css = (ROOT / "frontend" / "assets" / "styles.css").read_text()
    m = _re.search(r"\.uw-statband \{[^}]*?grid-template-columns:([^;]+);", css, _re.S)
    assert m, ".uw-statband lost its explicit column template"
    # COUNT TRACKS, not a `repeat(N)` literal: the lead column is wider than the rest
    # (`1.25fr repeat(5, 1fr)`), so a regex keyed on `repeat(` alone would read 5 and silently
    # stop matching the six cells it exists to compare against.
    columns = 0
    for tok in _re.findall(r"repeat\([^)]*\)|\S+", m.group(1).strip()):
        rep = _re.match(r"repeat\((\d+),", tok)
        columns += int(rep.group(1)) if rep else 1
    card = (ROOT / "frontend" / "views" / "shared" / "uw-card.js").read_text()
    band = card[card.index('<div class="uw-statband">'):]
    band = band[:band.index("</div>")]
    assert band.count("Cell(c)") == columns, (
        f"the band renders {band.count('Cell(c)')} cells into a {columns}-column grid — they must "
        f"move together or Method drops to a ragged second row (the v1 defect): {band}")
    # the promoted fields landed in their correct slots
    foot = card[card.index("function mastheadFoot"):]
    foot = foot[:foot.index("\n}")]
    assert "Next evidence" in foot and "underwritten" in foot, "dates belong in the mast-foot"
    assert "currentStateBlock" not in card, "the separate block is superseded by the masthead"


def test_header_and_foot_say_each_thing_once() -> None:
    """COPY DISCIPLINE (operator: "not comprehendible … non-necessary words"). The header said the
    status THREE times — the `watch` pill, then "not held", then a caption OPENING "Watch
    reflects…" — and the foot said "Next" twice ("Next evidence … Next results print") before a
    shouty "scenario verdict — NOT a ledger verdict of record". Both are now stated once.

    The caption was then retired outright (see the retired-field pin): shortening it twice and
    still finding it redundant was the evidence that the slot itself was the problem."""
    card = (ROOT / "frontend" / "views" / "shared" / "uw-card.js").read_text()
    foot = card[card.index("function mastheadFoot"):]
    foot = foot[:foot.index("\n}")]
    assert "Next evidence ${" not in foot, "the event label already names the event"
    assert 'replace(/^next\\s+/i' in foot, "the label's own leading 'Next ' must be stripped"
    assert "no ledger verdict logged" in foot
    assert "NOT a ledger verdict of record" not in card, "the shouty clause is retired"
    # the header states the rating and nothing else — no holding word, no caption
    pills = card[card.index("function verdictPills"):]
    pills = pills[:pills.index("\n}")]
    assert "statusNote" not in pills and "holdingLabel" not in pills


def test_lineage_sits_in_record_and_reproduce_not_above_the_numbers() -> None:
    """(#3) Which record this one replaced is FILING-CABINET information — it helps a reader find
    the paperwork, not judge the name — so on the dossier it belongs in the Appendix's
    "Record & reproduce" beside the analyst, date and ledger id. The STANDALONE card keeps the
    banner: an archived record's page has no appendix to carry it."""
    card = (ROOT / "frontend" / "views" / "shared" / "uw-card.js").read_text()
    doss = (ROOT / "frontend" / "views" / "shared" / "dossier.js").read_text()
    detail = card[card.index("const detail = () =>"):]
    detail = detail[:detail.index("`;")]
    assert "supersessionBanner" not in detail, "the dossier tier must not carry the banner"
    body = card[card.index("const body = () =>"):]
    body = body[:body.index("`;")]
    assert "supersessionBanner" in body, "the standalone card must keep it"
    assert "supersedes <a href=" in doss, "the Appendix must carry the lineage, linked"


def test_the_logged_verdict_panel_states_a_close() -> None:
    """THE FIFTH SURFACE. Four surfaces were made close-aware when the ledger row was bound to the
    record that justified it; this one was missed, and SMPL's exited position still read as a live
    "BUY · unresolved" in the Appendix. `resolved` stays untouched on purpose — a call is scored at
    its horizon whatever happened to the position — so the close is stated as an ADDITIVE fact,
    exactly as decision-log.js already states it."""
    doss = (ROOT / "frontend" / "views" / "shared" / "dossier.js").read_text()
    fn = doss[doss.index("function loggedVerdict("):]
    fn = fn[:fn.index("\n}\n")]
    assert "v.closed" in fn, "the panel must read the close attached by the loader"
    assert "closedChip" in fn and "realizedReturn" in fn, "close date, price and realized return"
    assert "Close reason" in fn, "why it was exited is the point of the row"
    # a close must NOT flip `resolved` — the call is still scored at its horizon
    assert 'v.resolved ? "resolved"' in fn, "horizon scoring stands after an exit"


def test_the_record_only_page_binds_its_ledger_row_by_id_not_by_route_key() -> None:
    """On the record-only path the route key IS the record key (`SMPL-2026-07-21`), so a
    `e.ticker === ticker` lookup matched nothing: the archived page printed "no verdict logged yet
    for SMPL-2026-07-21" three inches under a masthead correctly reading "BUY — closed 2026-07-22",
    and offered a CLI recipe built on a fabricated candidate id. build.py already decided which
    record owns the row; this side takes that answer rather than re-deriving it."""
    doss = (ROOT / "frontend" / "views" / "shared" / "dossier.js").read_text()
    seg = doss[doss.index("if (card) {"):]
    seg = seg[:seg.index("${assembleHelp()}")]
    assert "e.ticker === ticker" not in seg, "the route key is not a ticker on this path"
    assert "card.ledger.entryId" in seg, "bind by the id build.py resolved"
    assert "card.ticker || ticker" in seg and "loggedVerdict(verdict, tk," in seg, (
        "the CLI recipe must use the real ticker, never the record key")
