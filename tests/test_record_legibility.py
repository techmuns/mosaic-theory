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
    assert seal.check_all(recs, man) == []
    for t, r in recs.items():
        assert seal.amendment_violations((r.get("verdict") or {}).get("rationale")) == [], t


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


def test_status_note_is_capped_at_one_line() -> None:
    with pytest.raises(ValueError, match="25-word cap"):
        sc.Verdict(status="watch", status_note=" ".join(["word"] * 26))
    assert sc.Verdict(status="watch", status_note=" ".join(["word"] * 25)).status_note


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


def test_current_state_says_not_held_explicitly_for_a_closed_position() -> None:
    """A status word alone misleads: SMPL reads `watch` while its position is CLOSED. The block
    must say "not held" in words, and must not claim `held` for a closed or pending record."""
    rec = json.loads((ROOT / "scenarios" / "SMPL.json").read_text())
    closed = _BUILD._current_state(rec, {"_closed": {"exitPrice": 10.53}})
    assert closed["held"] is False and closed["holdingLabel"] == "not held — position closed"
    no_ledger = _BUILD._current_state(rec, None)
    assert no_ledger["held"] is False and "not held" in no_ledger["holdingLabel"]
    # a genuinely held position: confirmed + a ledger row + NO close
    conf = dict(rec)
    conf["verdict"] = {**rec["verdict"], "status": "confirmed"}
    held = _BUILD._current_state(conf, {"entry_id": "V-X"})
    assert held["held"] is True and held["holdingLabel"] == "held"


def test_current_state_carries_the_decision_numbers_and_both_dates() -> None:
    rec = json.loads((ROOT / "scenarios" / "SMPL.json").read_text())
    s = _BUILD._current_state(rec, None)
    assert s["ratio"] == 3.83 and s["bar"] == 2.0 and s["passFail"] == "PASS"
    assert s["baseNormalMargin"] == 0.14 and s["ceiling2to1"] == 12.72
    assert s["spot"] == 10.53 and s["spotSource"] and s["underwriteDate"] == "2026-07-21"
