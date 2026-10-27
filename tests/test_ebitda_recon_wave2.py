"""CIQ's EBITDA against the filings — wave 2 (2026-10-27): every differing or unchecked quarter
given its cause, each cause pinned on the REAL case that showed it.

Measured before any pin on the 27 committed pages (main 56500bb1, BEFORE snapshot
`data/snapshots/data_quality/ciq/2026-10-27.json`): 100 quarters on 25 pages — 37 confirmed, 4
stated, 30 unexplained, 29 unchecked. The causes, each a pin below:

* LLY's quarterly export IS its annual one (same sha) — four fiscal years read as four quarters;
* CNXC and GOOGL tag D&A only on the split pair; BURL only a GROSS interest-expense line;
* V, NKE: the gap is an amount the quarter's own XBRL tags (V's litigation provisions);
* CNXC (and SMPL, IT, NCNO…): the gap is CIQ's own itemised unusual items, a SUM;
* AMZN: two quarters swap $2,500M — one item booked in another quarter at CIQ;
* V's quarter to 2026-06-30: EDGAR has not reported it — a vintage gap, said so.

The fixture freezes, per name, the CIQ figures the committed page stores and the companyfacts
points as filed (`tests/fixtures/ebitda_recon_wave2.json`, its `_about` says what each part is).
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import ebitda_recon as er

_FX = json.loads((Path(__file__).parent / "fixtures" / "ebitda_recon_wave2.json").read_text())


def _hdr(iso: str) -> str:
    return date.fromisoformat(iso).strftime("%b-%d-%Y")


class _Bundle:
    """The quarterly Income Statement rows `reconcile` reads, shaped as CIQ exports them. CIQ's
    unusual items ride as 'EBT Excl.' = the net and 'EBT Incl.' = 0, so their difference is the
    derived figure the page stores — no raw CIQ cell beyond it."""

    def __init__(self, ciq: dict[str, float], unusual: dict[str, float] | None = None) -> None:
        ends = sorted(ciq)
        rows: list[list[Any]] = [["For the Fiscal Period Ending", *map(_hdr, ends)],
                                 ["EBITDA", *(ciq[d] for d in ends)]]
        if unusual is not None:
            rows += [["EBT Excl. Unusual Items", *(unusual.get(d) for d in ends)],
                     ["EBT Incl. Unusual Items", *(0.0 if d in unusual else None for d in ends)]]
        self._rows = rows

    def workbook(self, kind: str, freq: str | None = None) -> object:
        return object()

    def sheet(self, kind: str, name: str, freq: str | None = None) -> list[list[Any]]:
        return self._rows


def _facts(t: str, drop: tuple[str, ...] = ()) -> dict[str, Any]:
    pts = {k: v for k, v in _FX[t]["points"].items() if k not in drop}
    return {"facts": {"us-gaap": {tag: {"units": {"USD": [
        {"start": s, "end": e, "val": v, "filed": f, "form": fm, "accn": a}
        for s, e, v, f, fm, a in rows]}} for tag, rows in pts.items()}}}


def _rec(t: str, *, drop: tuple[str, ...] = (), unusual: bool = True) -> Any:
    fx = _FX[t]
    return er.reconcile(_Bundle(fx["ciq"], fx["unusual"] if unusual else None),  # type: ignore[arg-type]
                        _facts(t, drop), [], lambda r: None)


def _q(rec: Any, end: str) -> Any:
    return next(q for q in rec.quarters if q.period_end == end)


# --- the four columns must be four quarters -------------------------------------------------------


def test_lly_annual_columns_under_a_quarterly_name_write_no_block() -> None:
    """LLY's 'Financials_Quarterly' states 'Period Type: Annual' and is byte-for-byte its annual
    export: the four latest columns are 2022-12-31 … 2025-12-31. Before: four 'quarters' of
    unchecked fiscal years. Now: no LTM, no block."""
    assert sorted(_FX["LLY"]["ciq"]) == ["2022-12-31", "2023-12-31", "2024-12-31", "2025-12-31"]
    assert _rec("LLY") is None


def test_four_consecutive_quarters_still_reconcile() -> None:
    """Negative pin: a real LTM (CNXC's four quarters, 274 days end to end) is not refused."""
    rec = _rec("CNXC")
    assert rec is not None and len(rec.quarters) == 4


# --- our rebuild: the split pair and the gross interest line --------------------------------------


def test_cnxc_rebuilds_on_the_split_pair() -> None:
    """CNXC tags `Depreciation` and `AmortizationOfIntangibleAssets`, never a combined line: all
    four quarters were 'no quarterly D&A tag'. The quarter to 2026-02-28: operating income
    $118.559M + depreciation $55.913M + amortisation $103.456M = $277.928M."""
    q = _q(_rec("CNXC"), "2026-02-28")
    assert q.tags == ["OperatingIncomeLoss", "Depreciation", "AmortizationOfIntangibleAssets"]
    assert q.filing_ebitda == pytest.approx(277.928, abs=1e-3)


def test_one_leg_of_the_split_pair_is_not_dna() -> None:
    """Negative pin: depreciation alone is not the filer's D&A — GOOGL's 2025 quarters tag no
    amortisation, so they stay unbuilt, and say what is missing."""
    rec = _rec("GOOGL")
    q = _q(rec, "2025-12-31")
    assert q.filing_ebitda is None
    assert "Depreciation and AmortizationOfIntangibleAssets" in (q.note or "")
    # ...while the two 2026 quarters, which tag both, rebuild to CIQ's figure exactly
    assert [_q(rec, d).gap for d in ("2026-03-31", "2026-06-30")] == [0.0, 0.0]


def test_burl_rebuilds_on_gross_interest_expense() -> None:
    """BURL stopped tagging a net interest line after its 2025 second quarter and tags
    `InterestExpenseNonoperating`: the quarter to 2025-11-01 is pre-tax $138.059M + interest
    $19.154M + D&A — within 2% of CIQ's $254.96M."""
    q = _q(_rec("BURL"), "2025-11-01")
    assert q.construction == er._PRETAX_GROSS
    assert "InterestExpenseNonoperating" in q.tags
    assert q.different is False


def test_a_net_interest_line_still_wins() -> None:
    """Negative pin: the gross line is read only where no NET line is tagged for the quarter.
    With BURL's pre-tax and gross interest both removed, the quarter cannot be rebuilt at all."""
    q = _q(_rec("BURL", drop=("InterestExpenseNonoperating", "InterestExpense")), "2025-11-01")
    assert q.filing_ebitda is None and "interest-expense line" in (q.note or "")


# --- the filing's own tagged amount ---------------------------------------------------------------


def test_v_quotes_its_tagged_litigation_provisions() -> None:
    """V's three differing quarters had no release on the page (it keeps the last two). Each gap
    is the quarter's `LossContingencyLossInPeriod` to the million — the Q4 one derived as the
    10-K year less the nine-month year to date."""
    rec = _rec("V")
    for end, amount in (("2025-09-30", "903,000,000"), ("2025-12-31", "708,000,000"),
                        ("2026-03-31", "329,000,000")):
        q = _q(rec, end)
        assert q.matching_amount is not None and q.matching_amount.startswith(
            f"LossContingencyLossInPeriod {amount} USD"), end
        assert (q.matching_source or "").endswith(" XBRL")
    assert "its filing tags a matching amount" in rec.line


def test_a_tag_outside_the_family_is_never_read() -> None:
    """Negative pin: TGT's quarter to 2026-01-31 differs by $115.000M and its
    `ContractWithCustomerLiabilityRevenueRecognized` (gift-card revenue) is $115.000M to the dollar
    — a coincidence an any-tag search would quote."""
    assert "ContractWithCustomerLiabilityRevenueRecognized" in _FX["TGT"]["points"]
    q = _q(_rec("TGT", unusual=False), "2026-01-31")
    assert q.gap == pytest.approx(115.0) and q.matching_amount is None


def test_a_tagged_amount_two_thousand_dollars_off_is_not_a_match() -> None:
    """Negative pin on the precision: V's $708M provision against a gap $2K away is no match."""
    f = _facts("V")
    assert er._matching_fact(f, 708.0, date(2025, 12, 31), er._OPERATING) is not None
    assert er._matching_fact(f, 708.002, date(2025, 12, 31), er._OPERATING) is None


def test_the_nonoperating_line_is_read_only_for_a_pretax_construction() -> None:
    """NKE's quarter to 2025-08-31 is +$23M, its tagged `OtherNonoperatingIncomeExpense` −$23M —
    a line its pre-tax construction keeps inside and CIQ's EBIT does not. For an operating-income
    construction that line is outside both, so it is never quoted there."""
    q = _q(_rec("NKE", unusual=False), "2025-08-31")
    assert (q.matching_amount or "").startswith("OtherNonoperatingIncomeExpense -23,000,000")
    f = _facts("NKE")
    assert er._matching_fact(f, 23.0, date(2025, 8, 31), er._OPERATING) is None


# --- CIQ's own itemisation ------------------------------------------------------------------------


def test_cnxc_goodwill_quarters_are_ciqs_itemised_unusual_items() -> None:
    """CNXC's quarter to 2025-11-30 is +$1,468.713M against CIQ's own unusual items of $1,468.088M
    (goodwill impairment $1,523.3M net of merger costs and other items) — a SUM no single stated
    amount matches; its quarter to 2026-02-28 (+$36.733M against $40.721M) is not explained."""
    rec = _rec("CNXC")
    q = _q(rec, "2025-11-30")
    assert er.unusual_explains(q.gap, q.ciq_unusual)
    assert "itemises unusual items" in rec.line
    q2 = _q(rec, "2026-02-28")
    assert q2.different and not er.unusual_explains(q2.gap, q2.ciq_unusual)


def test_unusual_explains_is_two_percent_of_the_gap() -> None:
    """The tolerance pinned both ways, and no reason without a figure."""
    assert er.unusual_explains(100.0, 98.0) and not er.unusual_explains(100.0, 97.9)
    assert not er.unusual_explains(100.0, None) and not er.unusual_explains(None, 100.0)


# --- a period mismatch ----------------------------------------------------------------------------


def test_amzn_offsetting_quarters_state_each_other() -> None:
    """AMZN's quarter to 2025-09-30 is +$2,500M and the next −$2,500M; its LTM agrees to the
    dollar and neither quarter has a release on the page. Each states the other."""
    rec = _rec("AMZN")
    assert _q(rec, "2025-09-30").offset_by == "2025-12-31"
    assert _q(rec, "2025-12-31").offset_by == "2025-09-30"
    assert rec.ltm_gap == 0.0 and "in another quarter at CIQ" in rec.line


def _row(end: str, gap: float, *, quote: str | None = None) -> Any:
    from vinci.dossier.schemas import EbitdaReconQuarter
    return EbitdaReconQuarter(period_end=end, ciq_ebitda=100.0 + gap, filing_ebitda=100.0,
                              gap=gap, different=True, matching_amount=quote)


def test_gaps_of_one_sign_never_offset() -> None:
    """Negative pins: two quarters both +$2,500M are not a swap; nor are +2,500 and −2,498 (the
    sum is past $1M)."""
    assert er._offsets([_row("2025-09-30", 2500.0), _row("2025-12-31", 2500.0)]) == {}
    assert er._offsets([_row("2025-09-30", 2500.0), _row("2025-12-31", -2498.0)]) == {}
    assert er._offsets([_row("2025-09-30", 2500.0), _row("2025-12-31", -2500.0)]) == {
        "2025-09-30": "2025-12-31", "2025-12-31": "2025-09-30"}


# --- a vintage gap, said so -----------------------------------------------------------------------


def test_a_quarter_edgar_has_not_reported_says_so() -> None:
    """V's quarter to 2026-06-30: companyfacts, fetched 2026-10-27, ends at the 10-Q filed
    2026-04-29. The note said 'no quarterly D&A tag' — it now says EDGAR has not reported it."""
    q = _q(_rec("V"), "2026-06-30")
    assert q.filing_ebitda is None
    assert (q.note or "").startswith("EDGAR reports nothing for this quarter yet")
