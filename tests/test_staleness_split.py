"""THE STALENESS SPLIT — two ages wore one number, and only one is ours.

  * **EXPORT staleness** — we have not pulled. An operator action fixes it, so it GATES.
  * **CONSENSUS staleness** — no analyst has revised. Nothing we do moves it, so it prints,
    caveats past the same ceiling, feeds the neglect screen, and never gates.

THE LIVE CASE that forced it: AORT's Estimates workbook was re-exported on 2026-07-30 and still
reads 2026-06-30, because the street has gone quiet on the name. Under one merged number that is
30 days of "staleness" counting toward a ceiling breach that no operator action can prevent — the
gate would eventually refuse a build for a condition nobody can clear.

MEASURED CONSEQUENCE, whole fleet: exactly ONE name changes gate outcome. MVST was refused at 56d;
its export panels are 16d. Nothing else moves, and no name newly fails.
"""
from __future__ import annotations

import datetime as dt
import inspect
import json
import pathlib

import pytest

import vinci.dossier.freshness as fr

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD = dt.date(2026, 7, 30)

# One panel of each class, far apart, so a classification error cannot hide behind a small gap.
MECH = {
    "catalyst_path": {"as_of": {"value": "2026-05-15"}},                 # consensus, 76d
    "financial_summary": {"as_of": {"value": "2026-05-20"}},             # consensus, 71d
    "valuation": {"implied_expectations": {"multiples_as_of": "2026-06-01",   # consensus, 59d
                                           "tev_as_of": "2026-07-20"}},       # export,    10d
    "stock_info": {"as_of": {"value": "2026-07-28"}},                    # export,     2d
}


# --- the classification ---------------------------------------------------------------------


def test_each_class_reports_its_own_oldest() -> None:
    """THE RED. Merged, this build is 76d old and refused. Split, it is 10d of export age — which
    is the only part an operator could have prevented."""
    exp = fr.panel_age(MECH, BUILD, kind="export")
    con = fr.panel_age(MECH, BUILD, kind="consensus")
    assert exp is not None and exp.days == 10, exp
    assert exp.oldest_key == "valuation.implied_expectations.tev_as_of"
    assert con is not None and con.days == 76, con
    assert con.oldest_key == "catalyst_path.as_of"


def test_the_two_classes_partition_the_panels() -> None:
    """Neither class may drop or double-count a panel. A key silently in neither would vanish from
    the gate AND the page — the quietest possible failure, since nothing would look wrong."""
    all_keys = {k for k, _ in fr.panel_dates(MECH)}
    exp = {k for k, _ in fr.panel_dates(MECH) if k not in fr.CONSENSUS_PANELS}
    con = {k for k, _ in fr.panel_dates(MECH) if k in fr.CONSENSUS_PANELS}
    assert exp | con == all_keys and not (exp & con), (exp, con)
    assert len(all_keys) == 5, all_keys


def test_financial_summary_is_classified_consensus_despite_its_name() -> None:
    """The one members would get wrong by reading names. ``financial_summary.as_of`` sounds like the
    Financials workbook; its source_ref is *CIQ Estimates→Recent Changes*, so it moves only when an
    analyst revises. Classified by the stamp, not the label — the category-label rule."""
    assert "financial_summary.as_of" in fr.CONSENSUS_PANELS


def test_kind_is_mandatory_and_validated() -> None:
    """NO DEFAULT, deliberately: a default would let a caller keep the old merged meaning while the
    constant beside it says the classes differ. Both existing callers had to state which."""
    with pytest.raises(TypeError):
        fr.panel_age(MECH, BUILD)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="must be 'export' or 'consensus'"):
        fr.panel_age(MECH, BUILD, kind="panel")


# --- the gate keeps refusing what we CAN fix, and stops refusing what we cannot ----------------


def test_a_stale_export_still_fails_the_build() -> None:
    """The half that must NOT be weakened. A panel we could have re-pulled and did not still
    refuses — otherwise the split would be a way to switch the gate off."""
    old = {"valuation": {"implied_expectations": {"tev_as_of": "2026-01-01"}}}
    age = fr.panel_age(old, BUILD, kind="export")
    assert age is not None and age.days > fr.MAX_PANEL_AGE_DAYS
    with pytest.raises(fr.FreshnessError, match="ceiling"):
        fr.check_freshness(age, None, ticker="X")


def test_a_quiet_street_does_not_fail_the_build() -> None:
    """THE POINT OF THE ITEM. Consensus 76d over the ceiling, export 10d inside it: the build
    passes, and the caveat carries the fact instead."""
    fr.check_freshness(fr.panel_age(MECH, BUILD, kind="export"), None, ticker="X")
    note = fr.consensus_note(fr.panel_age(MECH, BUILD, kind="consensus"))
    assert note is not None and "76d" in note
    assert "re-export will NOT move it" in note and "neglect" in note


def test_consensus_note_is_silent_inside_the_ceiling_and_never_raises() -> None:
    """It is a caveat, not a guard. Inside the ceiling it says nothing; outside it, it returns a
    string — there is no input for which it raises, which is what keeps it off the gate path."""
    young = {"catalyst_path": {"as_of": {"value": "2026-07-28"}}}
    assert fr.consensus_note(fr.panel_age(young, BUILD, kind="consensus")) is None
    assert fr.consensus_note(None) is None


def test_the_same_ceiling_governs_both() -> None:
    """One number, deliberately. A second threshold would need its own justification, and the
    question — is this old enough to distrust? — is identical; only who can act differs.

    REVIEW FINDING: the first cut scanned the SOURCE for the substrings "60"/"90"/"30". That reads
    like a check and is not one — a hardcoded ``<= 45`` would have passed it while decoupling from
    the constant, which is the exact drift it exists to prevent. Driven at the boundary instead, so
    the tie to ``MAX_PANEL_AGE_DAYS`` holds by construction: silent AT the ceiling, speaking one day
    past it, wherever the constant is set."""
    at = dt.date(2026, 1, 1)
    on_ceiling = {"catalyst_path": {"as_of": {"value": str(at - dt.timedelta(
        days=fr.MAX_PANEL_AGE_DAYS))}}}
    one_past = {"catalyst_path": {"as_of": {"value": str(at - dt.timedelta(
        days=fr.MAX_PANEL_AGE_DAYS + 1))}}}
    assert fr.consensus_note(fr.panel_age(on_ceiling, at, kind="consensus")) is None, (
        "the caveat fires AT the ceiling; the gate's own comparison is `>`, not `>=`")
    past = fr.consensus_note(fr.panel_age(one_past, at, kind="consensus"))
    assert past is not None and str(fr.MAX_PANEL_AGE_DAYS) in past


# --- the wiring: the gate must read EXPORT, or the split is undone -----------------------------


def test_the_gate_reads_the_export_age() -> None:
    """A guard nobody rewired is not rewired. Passing the consensus age to ``check_freshness``
    restores the exact defect the split removed, and it would be invisible — the code would still
    read `check_freshness(panel_age(...))`."""
    src = inspect.getsource(__import__("vinci.dossier.assemble", fromlist=["x"])._freshness_check)
    assert 'panel_age(dumped, built_at, kind="export")' in src, (
        "the gate is not reading the export age — the split is undone")
    assert 'kind="consensus"' not in src, "the gate must never key on consensus staleness"


def test_both_ages_reach_the_page() -> None:
    """Removing consensus staleness from the gate must not remove it from view — that is the
    opposite of the intent, since a name nobody revises is a signal worth reading."""
    import vinci.dossier.render as rd

    src = inspect.getsource(rd._panel_age_line)
    assert "_panel_age_note" in src and "_consensus_age_note" in src
    assert "Panel age:" in src and "Consensus age:" in src


# --- the corpus -------------------------------------------------------------------------------


@pytest.mark.skipif(not (ROOT / "data" / "dossiers").is_dir(), reason="no committed dossiers")
def test_every_consensus_member_still_exists_in_the_corpus() -> None:
    """REVIEW FINDING, and it is the split's real failure mode. ``CONSENSUS_PANELS`` matches EXACT
    dotted paths. Rename one — ``catalyst_path`` moves, ``implied_expectations`` is restructured —
    and the entry goes dead, the panel falls to the EXPORT side, and **the gate silently starts
    refusing builds for consensus staleness again**. Nothing else in the suite would red: the
    synthetic-fixture tests build their own paths, and the corpus tests only read what is there.

    Fail-open in the dangerous direction, so it needs its own pin. Every member must be observed on
    the real corpus; a dead entry is a classification that has quietly stopped classifying."""
    seen: set[str] = set()
    for d in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        seen |= {k for k, _ in fr.panel_dates(json.loads(d.read_text())["mechanical"])}
    assert seen, "no panel paths found across the corpus — the harvester moved"
    dead = sorted(fr.CONSENSUS_PANELS - seen)
    assert not dead, (
        f"CONSENSUS_PANELS entries match nothing in the corpus: {dead}. Each is now classified "
        "EXPORT by default and will GATE — re-derive membership from the source_refs before "
        "deleting the entry.")


@pytest.mark.skipif(not (ROOT / "data" / "dossiers").is_dir(), reason="no committed dossiers")
def test_every_committed_page_carries_both_ages() -> None:
    """Non-vacuous by construction: fails if it finds no dossier, and asserts both lines on every
    one — a page showing only the gated half hides the neglect signal."""
    seen = 0
    for d in sorted((ROOT / "data" / "dossiers").iterdir()):
        md = d / "dossier.md"
        if not (d / "dossier.json").exists() or not md.exists():
            continue
        txt = md.read_text()
        seen += 1
        assert "- **Panel age:**" in txt, f"{d.name}: no panel age"
        assert "- **Consensus age:**" in txt, f"{d.name}: no consensus age"
    assert seen >= 10, f"expected the committed corpus, saw {seen}"


@pytest.mark.skipif(not (ROOT / "data" / "dossiers").is_dir(), reason="no committed dossiers")
def test_the_split_changes_exactly_one_name_and_loosens_nothing_else() -> None:
    """THE FLEET MEASUREMENT, pinned. The split may only ever move a name from refused to allowed
    by removing CONSENSUS age from the gate — never by shortening an EXPORT age. If a name's export
    age ever exceeds its merged age, the classification has put an export panel on the consensus
    side and the gate has been weakened."""
    moved = []
    for d in sorted((ROOT / "data" / "dossiers").iterdir()):
        j = d / "dossier.json"
        if not j.exists():
            continue
        doc = json.loads(j.read_text())
        mech, built = doc.get("mechanical") or {}, doc["assembled_at"]
        merged = max((dt.date.fromisoformat(str(built)[:10]) - dt.date.fromisoformat(v)).days
                     for _, v in fr.panel_dates(mech)) if fr.panel_dates(mech) else None
        exp = fr.panel_age(mech, built, kind="export")
        if merged is None or exp is None:
            continue
        assert exp.days <= merged, (
            f"{d.name}: export age {exp.days}d exceeds the merged {merged}d — an export panel is "
            "classified as consensus and the gate is measuring less than it should")
        if merged > fr.MAX_PANEL_AGE_DAYS >= exp.days:
            moved.append(d.name)
    # SUBSET, not equality. REVIEW FINDING: `moved == ["MVST"]` would red on a WIN — the moment
    # MVST re-enters a screen and rebuilds against fresh consensus, its merged age drops inside the
    # ceiling and the list goes EMPTY. That is the corpus-pinned-to-current-defects anti-pattern,
    # and a test that fails when things improve is worse than one that decays. The invariant is
    # directional: the split may not move a name we have not measured. Fewer is progress.
    assert set(moved) <= {"MVST"}, (
        f"the split moves {sorted(moved)}; measured 2026-07-30 it moves MVST alone. A name not on "
        "that list means the classification widened — re-measure before accepting it.")
