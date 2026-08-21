"""THE QUANTITY GUARD — two different quantities wearing one unit, and the swap that flips a gate.

THE INCIDENT (measured read-only 2026-08-18, recorded as accepted risk with this exact unlock).
`scenario-refresh diluted_shares` on SMPL flips its gate PASS → FAIL. SMPL is the fund's ONLY open
position and the ledger carries a BUY at $11.33 struck on the passing number. The alarm inverts on
reading the second side: **SMPL's PASS is sound and the REFRESH is the error** — the record's
denominator is shares OUTSTANDING (item 24's deliberate work) while the dossier anchor supplies the
diluted WEIGHTED AVERAGE.

WHY NO EXISTING GUARD SEES IT. `refresh_record` refuses a UNIT change on the reasoning that "basis
is prose about the same quantity; unit is the quantity's scale". That assumption is what fails
here: outstanding and weighted-average are DIFFERENT QUANTITIES wearing the SAME unit (`M shares`).

AND WHY THE OBVIOUS FIX IS FORBIDDEN. `basis` is free prose, so a basis-comparison guard is a TEXT
comparison of analyst wording — the rendered-string parse this repo refuses outright. The build
proved that empirically: a substring classifier over the real corpus stamped all eight
`outstanding` records as `weighted_average`, because every basis MENTIONS the weighted average
while explaining the quantity it is not. EPAM's says outright that "the latest-quarter diluted
weighted average of 52,267,000 is NOT used". The structured field exists because prose cannot be
compared, and the classifier that tried is the proof.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import vinci.scenarios as sc

ROOT = Path(__file__).resolve().parents[1]
LIVE = sorted(p for p in (ROOT / "scenarios").glob("*.json") if not p.name.startswith("_"))
ARCHIVE = sorted((ROOT / "scenarios" / "archive").glob("*.json"))


def _rec(name: str) -> sc.ScenarioRecord:
    return sc.read_record(name, root=ROOT)


def _fact(rec: sc.ScenarioRecord, **over: object) -> sc.Fact:
    f = rec.facts["diluted_shares"]
    return f.model_copy(update=over)  # type: ignore[arg-type]


# --- the vocabulary ------------------------------------------------------------------------

def test_an_unlisted_quantity_kind_is_refused() -> None:
    """An unlisted quantity is not reviewable — the `BEAR_BASES` rule, applied one level down."""
    with pytest.raises(ValueError, match="quantity_kind"):
        sc.Fact(value=1.0, unit="M shares", basis="b", source="s", quantity_kind="per_diluted")
    # and the empty default stays legal, or every pre-field record fails to load
    assert sc.Fact(value=1.0, unit="M shares", basis="b", source="s").quantity_kind == ""


def test_the_two_kinds_that_caused_the_incident_are_both_admissible() -> None:
    assert {"outstanding", "weighted_average"} <= sc.QUANTITY_KINDS
    assert "diluted_shares" in sc.QUANTITY_SENSITIVE_FACTS


# --- the incident, reproduced -----------------------------------------------------------------

def test_a_bare_float_cannot_swap_the_denominator_on_smpl() -> None:
    """THE DOOR THE INCIDENT ACTUALLY WALKS THROUGH. `vinci scenario-refresh --fact
    diluted_shares=X` can only send a float, so the value moved while the basis kept saying
    "outstanding" over a number that was no longer outstanding — the manufactured mislabel
    `refresh_record`'s own docstring warns about, arriving through the writer meant to prevent it.
    """
    rec = _rec("SMPL")
    assert rec.result is not None and rec.result.pass_fail == "PASS", (
        "fixture drifted — this pin is about protecting a PASSING record under an open position")
    with pytest.raises(sc.RefreshRefusedError, match="must DECLARE which one it supplies"):
        sc.refresh_record(rec, facts={"diluted_shares": 93.678},
                          source="anchor WA", on_date="2026-08-21")


def test_a_declared_swap_is_refused_and_says_no_unit_check_can_see_it() -> None:
    """The honest version of the same move is still a re-underwrite, not a refresh."""
    rec = _rec("SMPL")
    wa = _fact(rec, value=93.678, quantity_kind="weighted_average")
    with pytest.raises(sc.RefreshRefusedError, match="QUANTITY SWAP"):
        sc.refresh_record(rec, facts={"diluted_shares": wa},
                          source="anchor", on_date="2026-08-21")


def test_the_gate_the_swap_would_have_flipped_is_still_passing() -> None:
    """THE STAKE, pinned as a number rather than a story: the refused refresh is refused while
    SMPL's gate reads PASS. If this ever reddens, the position's own record moved and the guard's
    justification needs re-reading rather than the pin needs relaxing."""
    r = _rec("SMPL").result
    assert r is not None and r.ratio is not None
    assert r.pass_fail == "PASS" and r.ratio >= r.bar


def test_the_same_quantity_re_read_still_works() -> None:
    """The guard must not become a wall. A re-read of the SAME quantity — a fresher 10-Q cover
    count — is the legitimate refresh this path exists for, and it stays open."""
    rec = _rec("SMPL")
    fresher = _fact(rec, value=88.9, source="10-Q re-read", quantity_kind="outstanding")
    out = sc.refresh_record(rec, facts={"diluted_shares": fresher},
                            source="10-Q re-read", on_date="2026-08-21")
    assert out.facts["diluted_shares"].value == 88.9
    assert out.facts["diluted_shares"].quantity_kind == "outstanding"


def test_an_unstamped_record_refuses_rather_than_guessing() -> None:
    """A record with no structured quantity has nothing to check against, so the refresh REFUSES
    and names the remedy. Guessing from the prose is the forbidden parse; passing it through is
    the hazard."""
    rec = _rec("SMPL")
    bare = rec.model_copy(update={
        "facts": {**rec.facts, "diluted_shares": _fact(rec, quantity_kind="")}})
    declared = _fact(rec, value=88.9, quantity_kind="outstanding")
    with pytest.raises(sc.RefreshRefusedError, match="carries no structured quantity_kind"):
        sc.refresh_record(bare, facts={"diluted_shares": declared},
                          source="s", on_date="2026-08-21")


def test_a_non_sensitive_fact_still_takes_a_bare_float() -> None:
    """Deliberately NOT every fact: `net_debt` in $M is one quantity, and demanding a declaration
    everywhere would train the operator to type past it."""
    rec = _rec("SMPL")
    assert "net_debt" in rec.facts and "net_debt" not in sc.QUANTITY_SENSITIVE_FACTS
    out = sc.refresh_record(rec, facts={"net_debt": rec.facts["net_debt"].value + 1.0},
                            source="10-Q", on_date="2026-08-21")
    assert out.facts["net_debt"].value == rec.facts["net_debt"].value + 1.0


# --- the corpus is stamped, and stamped CORRECTLY ---------------------------------------------

@pytest.mark.parametrize("path", LIVE + ARCHIVE, ids=lambda p: p.stem)
def test_every_committed_diluted_shares_declares_its_quantity(path: Path) -> None:
    """Without this the guard is decorative: an unstamped record refuses every refresh instead of
    catching the swap, and the hazard just moves from silent to blocked."""
    f = (json.loads(path.read_text()).get("facts") or {}).get("diluted_shares")
    if f is None:
        pytest.skip(f"{path.stem} carries no diluted_shares")
    assert f.get("quantity_kind") in sc.QUANTITY_KINDS, (
        f"{path.stem}: diluted_shares has no admissible quantity_kind — stamp it from the basis "
        f"prose BY READING IT; a substring rule gets this backwards")


def test_the_one_record_that_genuinely_carries_the_other_quantity() -> None:
    """THE ARCHIVE'S HONEST RECORD. `SMPL-2026-07-21` predates item 24 and carries the diluted
    weighted average — the very quantity the live record was moved OFF. It is stamped for what it
    is, not normalised to match its successor: an archive that agrees with the present has stopped
    being evidence. This is also the corpus proof that the swap is real rather than theoretical."""
    p = ROOT / "scenarios" / "archive" / "SMPL-2026-07-21.json"
    if not p.is_file():
        pytest.skip("the pre-item-24 SMPL archive is gone")
    f = json.loads(p.read_text())["facts"]["diluted_shares"]
    assert f["quantity_kind"] == "weighted_average"
    live = _rec("SMPL").facts["diluted_shares"]
    assert live.quantity_kind == "outstanding", (
        "the live record and its own archive must disagree here — that disagreement IS item 24")


def test_the_stamps_round_trip_and_an_unstamped_fact_emits_no_key() -> None:
    """Absent-vs-null, the `leg_fy` rule: a record that never stated a quantity carries NO key for
    one, so every pre-field record round-trips byte-identically."""
    rec = _rec("SMPL")
    committed = (ROOT / "scenarios" / "SMPL.json").read_text()
    assert sc.write_record(rec, root=ROOT).read_text() == committed
    scoped = sc._version_scoped(rec.model_copy(update={
        "facts": {**rec.facts, "diluted_shares": _fact(rec, quantity_kind="")}}))
    assert "quantity_kind" not in scoped["facts"]["diluted_shares"]
    assert "quantity_kind" in sc._version_scoped(rec)["facts"]["diluted_shares"]
