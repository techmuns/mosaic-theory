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
"""
from __future__ import annotations

from datetime import date

import pytest

from vinci.dossier import ciq_sheets
from vinci.dossier.ciq_sheets import _GUIDANCE_METRICS

#: What the tuple held before, kept literal so the recovery is demonstrated rather than described.
_ORIGINAL_FIVE = ("Revenue", "Capital Expenditure", "Gross Margin %", "EBITDA", "EPS Normalized")


def _bundle(ticker: str):
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.manual_store import LocalFolderStore

    files = LocalFolderStore(get_config().data_dir / "manual" / "ciq").files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


def test_the_original_five_are_all_still_covered() -> None:
    """WIDENED, NEVER NARROWED. Dropping one while adding ten would be a silent regression wearing a
    feature's clothes, and the five were the only metrics any committed page has ever shown."""
    missing = [m for m in _ORIGINAL_FIVE if m not in _GUIDANCE_METRICS]
    assert not missing, f"the widening lost {missing} — that is a regression, not a widening"


def test_the_metrics_are_unique_and_ordered_decision_first() -> None:
    """Duplicates would double a block; the ORDER is the display order, so Revenue leads and the
    below-the-line items a reader consults second do not push it down the table."""
    assert len(set(_GUIDANCE_METRICS)) == len(_GUIDANCE_METRICS), "a metric is listed twice"
    assert _GUIDANCE_METRICS[0] == "Revenue"
    for below_the_line in ("Interest Expense", "Effective Tax Rate %", "DPS"):
        assert _GUIDANCE_METRICS.index(below_the_line) > _GUIDANCE_METRICS.index("EBITDA")


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
    workbook with the old tuple restored, so the comparison is measured rather than asserted."""
    bundle, ref = _bundle(ticker), date(2026, 8, 12)

    def metrics() -> set[str]:
        got = ciq_sheets.guidance_bridge_rows(bundle, reference_date=ref).value or []
        return {r.metric for r in got}

    wide = metrics()
    original = ciq_sheets._GUIDANCE_METRICS
    try:
        ciq_sheets._GUIDANCE_METRICS = _ORIGINAL_FIVE
        narrow = metrics()
    finally:
        ciq_sheets._GUIDANCE_METRICS = original
    assert narrow <= wide, f"{ticker}: the widening LOST {sorted(narrow - wide)}"
    assert len(wide) > len(narrow), f"{ticker}: the widening recovered nothing"


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
