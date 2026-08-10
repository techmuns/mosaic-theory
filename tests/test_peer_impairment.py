"""Does the sector WRITE DOWN what it carries — the half the balance comparison cannot answer.

WHY (STATE.md §M3). SMPL carrying 73.2% of assets as acquired against a 57.6% large-peer median
settles that the LOAD is ordinary for packaged food. It says nothing about whether the sector marks
that load down, and $369.0M written off means OPPOSITE things against a sector that impairs
routinely and one that never does. That is the half bearing on management quality.

OFFLINE BY CONSTRUCTION. `test_peer_capital_intensity.py` is `pytest.mark.network` and CI therefore
never runs it — the same shape that left main red for eleven merges (#367), where pins that passed
on a laptop could not pass in CI at all. Every guard below runs in `pytest -m "not network"`, on
companyfacts dicts built to the REAL EDGAR structure `points_for_tag` parses (units → rows with
start/end/val/filed), never to a shape invented for the assertion (#305).

THE VALUES ARE DRAWN FROM THE LIVE CORPUS, not imagined: JJSF really does tag
`GoodwillImpairmentLoss` for 16 consecutive years at zero, CPB really did impair four times between
FY2013 and FY2018 and not since, and SMPL's live charge really is a 272-day year-to-date point that
the annual rule excludes.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pytest

from vinci.dossier.capital_allocation import (
    IMPAIRMENT_WINDOW_YEARS,
    _annual_series,
    _build_peer_impairment,
    build_peer_capital_intensity,
)
from vinci.dossier.schemas import PeerRow

GW = "GoodwillImpairmentLoss"
INT = "ImpairmentOfIntangibleAssetsExcludingGoodwill"
COMBINED = "GoodwillAndIntangibleAssetImpairment"
END = date(2026, 5, 30)          # SMPL's real balance date


def _row(val: float, end: date, *, days: int = 365, filed: date | None = None) -> dict[str, Any]:
    return {"start": str(end - timedelta(days=days)), "end": str(end), "val": val,
            "filed": str(filed or (end + timedelta(days=30))), "fy": end.year, "fp": "FY",
            "form": "10-K", "accn": "x"}


def _facts(**tags: list[dict[str, Any]]) -> dict[str, Any]:
    """companyfacts in the REAL shape — us-gaap namespace, units → USD → rows."""
    return {"facts": {"us-gaap": {t: {"units": {"USD": rows}} for t, rows in tags.items()}}}


def _annual_years(n: int, *, val: float, end: date = END) -> list[dict[str, Any]]:
    return [_row(val, date(end.year - i, end.month, end.day)) for i in range(n)]


# ─── _annual_series: the three hazards that silently inflate a sum ────────────────────────────

def test_year_to_date_and_quarterly_points_are_excluded() -> None:
    """POSITIVE + NEGATIVE. A 272-day YTD point overlaps the year containing it, so summing both
    double-counts. Only the ~12-month span survives; the 272d and 90d ones do not."""
    facts = _facts(**{GW: [_row(60.9e6, END, days=365),
                           _row(38.0e6, END, days=272),
                           _row(12.0e6, END, days=90)]})
    tag, kept = _annual_series(facts, (GW,))
    assert tag == GW
    assert [round(p.value / 1e6, 1) for p in kept] == [60.9], (
        "a non-annual duration survived the annual filter — the window total is not summable")


def test_a_restatement_of_one_year_is_counted_once_at_the_amended_value() -> None:
    """Same `period_end`, two filings. Latest `filed` wins — the amended figure, not the original,
    and NOT both. Two rows here would inflate the total by the original's value."""
    facts = _facts(**{GW: [_row(100.0e6, END, filed=date(2026, 7, 1)),
                           _row(150.0e6, END, filed=date(2026, 9, 1))]})
    _, kept = _annual_series(facts, (GW,))
    assert len(kept) == 1, "a restated year was counted twice"
    assert kept[0].value == pytest.approx(150.0e6), "kept the superseded filing, not the amendment"


def test_two_annual_spans_that_overlap_do_not_both_survive() -> None:
    """A 52/53-week filer can report two ~annual periods whose ends differ by days but whose spans
    overlap. Newest kept; the overlapping older one dropped."""
    facts = _facts(**{GW: [_row(10.0e6, END),
                           _row(20.0e6, END - timedelta(days=7))]})
    _, kept = _annual_series(facts, (GW,))
    assert len(kept) == 1 and kept[0].period_end == END, (
        "two overlapping annual spans both survived — their sum covers ~12 months twice")


def test_a_family_with_no_annual_points_returns_nothing_rather_than_a_quarterly_one() -> None:
    """NEGATIVE PIN. Falling back to a quarterly point when no annual exists would put a 90-day
    figure in a column labelled as a year."""
    assert _annual_series(_facts(**{GW: [_row(5.0e6, END, days=90)]}), (GW,)) == (None, [])


# ─── the four states, each a different fact ──────────────────────────────────────────────────

def test_charged_is_the_sum_over_disjoint_years() -> None:
    imp = _build_peer_impairment(_facts(**{GW: _annual_years(3, val=100.0e6)}), 1000.0, END)
    assert imp.state == "charged"
    assert imp.charged_years == 3 and imp.observations == 3
    assert imp.total == pytest.approx(300.0)
    assert imp.pct_acquired == pytest.approx(0.3)


def test_explicit_zero_is_a_measurement_and_never_reads_as_an_absence() -> None:
    """JJSF's real shape: tags `GoodwillImpairmentLoss` every year and states 0. That is the
    strongest available evidence of 'did not write down' and must be DISTINGUISHABLE from a filer
    that never tags the concept."""
    imp = _build_peer_impairment(_facts(**{GW: _annual_years(5, val=0.0)}), 1000.0, END)
    assert imp.state == "explicit-zero"
    assert imp.observations == 5 and imp.charged_years == 0
    assert imp.total is None, "a nil year rendered as a $0 charge rather than as no charge"
    assert imp.note and "REPORTS this concept and states zero" in imp.note


def test_none_in_window_keeps_the_charge_the_window_drops() -> None:
    """CPB's real shape: four charges FY2013-FY2018, none since. Over a trailing five years it
    would look identical to a name that never impaired — and it is not one, so the last charge
    survives on the row."""
    old = date(2018, 7, 29)
    imp = _build_peer_impairment(_facts(**{GW: [_row(540.0e6, old)]}), 1000.0, END)
    assert imp.state == "none-in-window"
    assert imp.observations == 0
    assert imp.last_charge_end == old and imp.last_charge_amount == pytest.approx(540.0)
    assert imp.note and "tagged historically but NOT inside this window" in imp.note


def test_untagged_is_not_the_same_sentence_as_reports_nil() -> None:
    """FRPT/BRBR/UTZ tag neither family, ever. #362's rule at value scope: the uninformative state
    must not borrow the informative one's meaning."""
    imp = _build_peer_impairment(_facts(), None, END)
    assert imp.state == "untagged"
    assert imp.note and "NOT the same as reporting zero" in imp.note


def test_the_four_states_produce_four_distinct_notes() -> None:
    """The whole point of the block. If two states share a sentence, the page tells the reader the
    same thing about two different facts."""
    built = [
        _build_peer_impairment(_facts(**{GW: _annual_years(2, val=1.0e6)}), 100.0, END),
        _build_peer_impairment(_facts(**{GW: _annual_years(2, val=0.0)}), 100.0, END),
        _build_peer_impairment(_facts(**{GW: [_row(1.0e6, date(2015, 1, 1))]}), 100.0, END),
        _build_peer_impairment(_facts(), 100.0, END),
    ]
    assert [b.state for b in built] == ["charged", "explicit-zero", "none-in-window", "untagged"]
    assert len({b.note for b in built}) == 4, "two states share a sentence"


# ─── the pending charge: the bug this build shipped and caught ────────────────────────────────

def test_the_live_charge_sums_both_families_not_just_the_first() -> None:
    """REGRESSION — the first cut took the single latest point across all five tags and returned
    SMPL's **$38.0M goodwill** leg while silently dropping the **$331.0M intangible** leg beside
    it. The families are different concepts on one income statement, so they ADD; the published
    figure was 10% of the real one, and it was the headline the block exists to contextualise."""
    facts = _facts(**{GW: [_row(60.9e6, END - timedelta(days=273)),
                           _row(38.0e6, END, days=272)],
                      INT: [_row(331.0e6, END, days=272)]})
    imp = _build_peer_impairment(facts, 1508.9, END)
    assert imp.pending == pytest.approx(369.0), (
        "the live year-to-date charge dropped a family — SMPL's real figure is 38.0 + 331.0")
    assert imp.pending_span is not None and "272d" in imp.pending_span


def test_the_live_charge_is_never_added_to_the_window_total() -> None:
    """The rule that makes the window summable is what excludes the YTD point, so the two are
    different quantities. SMPL's window figure is $60.9M against a $369.0M live charge — a 6x gap
    (STATE.md §M3)."""
    facts = _facts(**{GW: [_row(60.9e6, END - timedelta(days=273)),
                           _row(38.0e6, END, days=272)],
                      INT: [_row(331.0e6, END, days=272)]})
    imp = _build_peer_impairment(facts, 1508.9, END)
    assert imp.total == pytest.approx(60.9), "a year-to-date charge entered the annual window total"
    assert imp.pending == pytest.approx(369.0)


def test_a_combined_tag_does_not_double_count_the_intangible_leg() -> None:
    """NO LIVE INSTANCE — every name on SMPL's set resolves to `GoodwillImpairmentLoss`, so this is
    SYNTHETIC and says so. The tag sits in `GOODWILL_IMPAIRMENT`, its scope already includes
    intangibles, and adding the intangible family on top would double the charge silently."""
    facts = _facts(**{COMBINED: _annual_years(1, val=200.0e6),
                      INT: _annual_years(1, val=150.0e6)})
    imp = _build_peer_impairment(facts, 1000.0, END)
    assert imp.total == pytest.approx(200.0), "the intangible family was added on top of a tag "\
                                              "whose scope already contains it"
    assert imp.note and "double-count" in imp.note


# ─── the base rate: the denominator is the finding ────────────────────────────────────────────

class _Res:
    def __init__(self, cik: str) -> None:
        self.cik = cik


def _built(specs: dict[str, tuple[float, dict[str, Any]]]) -> Any:
    """Drive the real builder end to end over a synthetic grid."""
    grid = [PeerRow(name=t, ticker=t, market_cap=mc, is_name=(t == "SUBJ"))
            for t, (mc, _) in specs.items()]
    facts = {t: f for t, (_, f) in specs.items()}
    return build_peer_capital_intensity(
        grid, resolve=lambda t: _Res(t), companyfacts=lambda c: facts[c])


def _balance(acquired: float) -> dict[str, Any]:
    def inst(v: float) -> dict[str, Any]:
        return {"units": {"USD": [{"end": str(END), "val": v, "filed": str(END),
                                   "form": "10-K", "accn": "x"}]}}
    return {"Goodwill": inst(acquired), "Assets": inst(acquired * 2)}


def _peer(acquired: float, **tags: list[dict[str, Any]]) -> dict[str, Any]:
    node = _balance(acquired)
    node.update({t: {"units": {"USD": rows}} for t, rows in tags.items()})
    return {"facts": {"us-gaap": node}}


def test_the_base_rate_denominator_excludes_peers_that_were_never_measured() -> None:
    """THE FINDING, not a detail. A peer with no annual observation in the window (CPB) was not
    measured; counting it among the clean names manufactures the reassuring answer out of an
    absence — the #362 failure applied to a denominator."""
    pc = _built({
        "SUBJ": (2000.0, _peer(1000e6, **{GW: _annual_years(1, val=50e6)})),
        "CHG1": (5000.0, _peer(1000e6, **{GW: _annual_years(3, val=300e6)})),
        "CHG2": (5000.0, _peer(1000e6, **{GW: _annual_years(2, val=100e6)})),
        "NIL":  (5000.0, _peer(1000e6, **{GW: _annual_years(4, val=0.0)})),
        "OLD":  (5000.0, _peer(1000e6, **{GW: [_row(900e6, date(2015, 6, 1))]})),
        "NONE": (5000.0, _peer(1000e6)),
    })
    assert pc.imp_n_large_assessed == 3, (
        "assessed must count CHG1, CHG2 and NIL only — OLD and NONE were never measured")
    assert pc.imp_n_large_charged == 2
    assert pc.imp_window_years == IMPAIRMENT_WINDOW_YEARS
    assert pc.imp_subject_state == "charged"


def test_a_peer_that_never_resolves_gets_no_impairment_record_rather_than_a_clean_one() -> None:
    """`unresolved` and `fetch-failed` rows must not acquire a write-down verdict — absence of a
    row is not evidence of no charge (#362 at the fetch layer, which this block inherits)."""
    def _boom(_: str) -> Any:
        raise RuntimeError("no CIK")
    grid = [PeerRow(name="X", ticker="X", market_cap=5000.0, is_name=False)]
    pc = build_peer_capital_intensity(grid, resolve=_boom, companyfacts=lambda c: {})
    assert pc.rows[0].impairment is None, "an unresolvable ticker was given a write-down state"
    assert pc.imp_n_large_assessed == 0
