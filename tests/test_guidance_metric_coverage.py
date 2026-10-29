"""The guidance table shows what management guided, not a five-metric sample of it.

WHAT WAS DROPPED. `_GUIDANCE_METRICS` listed five blocks — Revenue, Capital Expenditure, Gross
Margin %, EBITDA, EPS Normalized — and CIQ's Guidance sheet carries far more. Everything outside the
tuple was silently absent: not marked UNKNOWN, not flagged, simply never looked for.

THE ONE THAT MATTERS MOST. **NFLX guides its own FREE CASH FLOW at 12,500.0 for FY 2026** and the
page could not show it. #421 had just established that the same page's `Levered Free Cash Flow` read
**25,388** — roughly twice management's own number — and wrote a basis note pointing the reader
toward exactly the figure this whitelist was excluding.

MEASURED ACROSS 19 WORKBOOKS: **65 current guides → 138 (+73)**. Every name gains; AORT 5→9,
CNXC 3→8, IT 4→12, CPB 4→12, NFLX 4→10, V 3→10, WERN 2→7.

THIS WIDENS WHAT CAN BE READ, NEVER WHAT MUST BE. A block absent from a workbook is not rendered,
and every recovered guide still carries `GUIDANCE_BASIS_REF` (#427: CIQ states a LEVEL, and where
management guided a RATE the level is CIQ's arithmetic) and its own `age`, so a guide that stopped
being updated reads `3765d (stale)` rather than passing as current.

THE LIST ITSELF IS GONE (audit A-D8, 2026-10-29). The fifteen names still dropped 17 guided blocks
across 11 of the 34 non-test exports, so blocks are now found by the sheet's own structure
(`ciq_sheets._guidance_starts`). The pins below compare that discovery against the former lists on
the licensed workbooks; the CI-visible pins are in `tests/test_ciq_reader_contract.py`.
"""
from __future__ import annotations

from datetime import date

import pytest

from vinci.dossier import ciq_sheets

#: What the tuple held before, kept literal so the recovery is demonstrated rather than described.
_ORIGINAL_FIVE = ("Revenue", "Capital Expenditure", "Gross Margin %", "EBITDA", "EPS Normalized")
#: The fifteen-name list that replaced it, until A-D8 (2026-10-29) retired lists altogether.
_FORMER_FIFTEEN = (
    "Revenue", "EBITDA", "EBIT", "Gross Margin %",
    "EPS Normalized", "EPS (GAAP)", "Net Income (GAAP)", "Net Income (Excl. Excep)",
    "Cash From Operations", "Capital Expenditure", "Free Cash Flow",
    "Depreciation & Amortization", "Interest Expense", "Effective Tax Rate %", "DPS",
)


def _bundle(ticker: str):
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.manual_store import LocalFolderStore

    files = LocalFolderStore(get_config().data_dir / "manual" / "ciq").files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


def _reads(ticker: str, names: tuple[str, ...] | None) -> set[str]:
    """The metrics read off a licensed workbook — by the former list ``names``, or (None) by the
    sheet's own structure, as the readers now do."""
    rows = _bundle(ticker).sheet("estimates", "Guidance")
    starts = (ciq_sheets._guidance_starts(rows) if names is None
              else ciq_sheets._metric_starts(rows, names))
    return {r.metric for r in ciq_sheets._guidance_reads(rows, starts, date(2026, 8, 12), 45)}


@pytest.mark.parametrize("ticker", ["NFLX", "V", "AORT", "CNXC", "ROST", "TJX", "TGT", "PARR"])
def test_discovery_reads_every_guide_the_former_lists_read(ticker: str) -> None:
    """WIDENED, NEVER NARROWED (A-D8). Every metric the fifteen-name list read — and so the five
    before it — is still read, block for block. (The display order was always the sheet's:
    `_metric_starts` sorted the blocks it found, so the list's order never reached a page.)"""
    found = _reads(ticker, None)
    for former in (_ORIGINAL_FIVE, _FORMER_FIFTEEN):
        assert _reads(ticker, former) <= found, f"{ticker}: discovery LOST a listed guide"


def test_nflx_free_cash_flow_guide_is_recovered() -> None:
    """THE HEADLINE CASE, end to end on the licensed workbook. Management's own FCF guide is the
    figure #421's basis note points toward, and it was the one the whitelist excluded.

    Asserts PRESENCE and PERIOD, never the figure — a re-pulled export moves guides, and pinning
    12,500.0 here would rot the moment NFLX guides again."""
    rows = ciq_sheets.guidance_bridge_rows(
        _bundle("NFLX"), reference_date=date(2026, 8, 12)).value or []
    fcf = [r for r in rows if r.metric == "Free Cash Flow"]
    assert fcf, (
        f"NFLX's own free-cash-flow guide is still absent; metrics present: "
        f"{sorted({r.metric for r in rows})}")
    assert "2026" in str(fcf[0].period), f"the recovered guide is not a current period: {fcf[0]}"


@pytest.mark.parametrize("ticker", ["NFLX", "V", "AORT", "CNXC"])
def test_widening_strictly_adds(ticker: str) -> None:
    """EVERY GUIDE THE OLD TUPLE FOUND IS STILL FOUND, and more besides. Run against the same
    workbook with the old tuple's blocks, so the comparison is measured rather than asserted."""
    wide, narrow = _reads(ticker, None), _reads(ticker, _ORIGINAL_FIVE)
    assert narrow <= wide, f"{ticker}: the widening LOST {sorted(narrow - wide)}"
    assert len(wide) > len(narrow), f"{ticker}: the widening recovered nothing"


@pytest.mark.parametrize(("ticker", "metric"), [
    ("ROST", "Same Store Sales Growth %"), ("TJX", "Same Store Sales Growth %"),
    ("TJX", "EBT (GAAP)"), ("CNXC", "Net Debt"), ("PARR", "Maintenance Capital Expenditure"),
])
def test_a_block_the_former_list_never_named_is_read(ticker: str, metric: str) -> None:
    """A-D8 on the licensed workbooks it was measured on (2026-10-29): guided blocks outside the
    fifteen names, dated 2025-26, now read."""
    assert metric in _reads(ticker, None) - _reads(ticker, _FORMER_FIFTEEN)


@pytest.mark.parametrize("ticker", ["NFLX", "V"])
def test_every_recovered_guide_still_states_its_age_and_its_basis(ticker: str) -> None:
    """THE GUARD THAT MAKES WIDENING SAFE. More metrics means more names that STOPPED guiding
    something, so each row must still say how old it is — V recovers six guides between 2114 and
    4767 days old, and they read `(stale)` rather than passing as current under "Latest guide".
    The basis caution from #427 must reach them too."""
    sourced = ciq_sheets.guidance_bridge_rows(_bundle(ticker), reference_date=date(2026, 8, 12))
    rows = sourced.value or []
    assert rows, f"{ticker} produced no guidance rows at all"
    assert "CIQ's arithmetic" in (sourced.source_ref or ""), (
        "the recovered guides lost the #427 basis caution — a CIQ LEVEL would read as the "
        "company's own published figure")
    for row in rows:
        assert row.age, (
            f"{ticker}: {row.metric} states no age — a stale guide would pass as current")


# ─── delivery direction is a METRIC property, not a sign (review finding, #437) ───────────────────

def test_a_positive_cost_guide_is_not_read_as_a_revenue_guide() -> None:
    """THE REVIEW FINDING. The delivery read inferred "cost guide" from `range_high < 0`, which
    holds only because CIQ states capex and interest expense NEGATIVE. Widening admitted
    `Effective Tax Rate %` — cost-like but stated POSITIVE (19.0) — so it took the revenue path and
    a tax rate HIGHER than guided was recorded as MET.

    MEASURED, NOT ARGUED: **all 12 names carrying a tax-rate guide had an inverted record.** VRRM
    went from `3/3` to `0/3` — a perfect delivery record that was in fact a perfect miss — and V
    from `12/32` to `28/32`.
    """
    from vinci.dossier.ciq_sheets import _GUIDANCE_HIGHER_IS_DELIVERY

    assert _GUIDANCE_HIGHER_IS_DELIVERY["Effective Tax Rate %"] is False, (
        "a tax RATE is delivered by coming in LOWER; reading it the other way inverts the record")
    for higher_is_better in ("Revenue", "EBITDA", "EPS (GAAP)", "Free Cash Flow", "DPS"):
        assert _GUIDANCE_HIGHER_IS_DELIVERY[higher_is_better] is True, higher_is_better
    # Capex/interest are stated NEGATIVE, so "higher" is signed and means less spend — the outcome
    # is unchanged for them; what changed is that the direction is chosen by NAME, not by sign.
    for signed_cost in ("Capital Expenditure", "Interest Expense"):
        assert _GUIDANCE_HIGHER_IS_DELIVERY[signed_cost] is True, signed_cost


def test_a_metric_with_no_defined_direction_records_no_outcome() -> None:
    """REFUSE, DO NOT GUESS. `Depreciation & Amortization` is a consequence of past capital
    decisions, not a target management delivers against — more of it is neither a beat nor a miss.
    It is deliberately absent from the map, and its GUIDE still shows while the met/missed record
    is withheld. A coin-flip dressed as a track record is worse than no track record."""
    from vinci.dossier.ciq_sheets import _GUIDANCE_HIGHER_IS_DELIVERY

    assert "Depreciation & Amortization" not in _GUIDANCE_HIGHER_IS_DELIVERY

    rows = ciq_sheets.guidance_bridge_rows(
        _bundle("VRRM"), reference_date=date(2026, 8, 12)).value or []
    da = [r for r in rows if r.metric == "Depreciation & Amortization"]
    if not da:
        pytest.skip("VRRM's export carries no D&A guide block")
    assert da[0].latest_guide, "the guide itself must still be shown"
    assert not (da[0].record or "").strip("—").strip(), (
        f"D&A reported a delivery record with no defined direction: {da[0].record!r}")


def test_every_formerly_listed_metric_is_either_directed_or_knowingly_undirected() -> None:
    """THE COMPLETENESS GUARD, as it stood for the fifteen listed metrics: adding a metric without
    deciding its direction is exactly how the tax rate got in. Since A-D8 a discovered metric the
    map does not name records NO outcome (pinned on the synthetic export in
    `test_ciq_reader_contract.py`), so a missing direction withholds a record rather than guessing
    one; the fifteen keep their decided directions."""
    from vinci.dossier.ciq_sheets import _GUIDANCE_HIGHER_IS_DELIVERY

    undirected = {"Depreciation & Amortization"}   # decided, not overlooked
    unclassified = [m for m in _FORMER_FIFTEEN
                    if m not in _GUIDANCE_HIGHER_IS_DELIVERY and m not in undirected]
    assert not unclassified, (
        f"{unclassified} are guided but have no delivery direction — classify them in "
        f"_GUIDANCE_HIGHER_IS_DELIVERY, or add them to the undirected set deliberately")
