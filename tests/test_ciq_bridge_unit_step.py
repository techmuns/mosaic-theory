"""ONE FIGURE A UNIT STEP OFF IS REFUSED, NOT SCORED "AGREE" (audit BC-D10's remainder, fix request
2, order 3; 2026-11-10).

#863 made the anchor bridge read each statement's own unit line, so an export stated in thousands
is refused. Its magnitude band against revenue was left as it was: seven orders of magnitude wide
([1e-4, 1000]x revenue), so one cell divided by 1,000 sits inside it. The verifier's case: ORCL's
cash ÷ 1000 with every unit line stating Millions gave `ok True`, outcome `agree`.

A band cannot be narrowed to catch it: pre-revenue names hold cash at hundreds of times revenue,
and real figures step by about 1,000x between periods (SMPL's 2016 stub-period Total Debt, EPAM's,
MNST's and NKE's quarterly operating cash flow; 201 of 176,052 consecutive pairs on disk). So each
figure is re-read from its own parts instead, and one a unit step from that re-read is refused.

The real-export pins mutate one cell in memory on whichever export the folder holds and skip where
it is absent, as on CI; the constructed twin runs everywhere.
"""
from __future__ import annotations

from typing import Any

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.config import get_config
from vinci.dossier import ciq_balance as cb
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.schemas import CHECK_DIFFER

_PAGES = ("AMZN", "BRBR", "BURL", "CNXC", "EPAM", "FUBO", "GOOGL", "IT", "LLY", "MCK", "MVST",
          "NCNO", "NFLX", "NKE", "ORKA", "PARR", "ROST", "SMPL", "TECX", "TGT", "TJX", "UBER",
          "V", "VITL", "VRRM", "WERN", "WLK")


def _real(ticker: str) -> CiqBundle:
    files = LocalFolderStore.from_config(get_config()).files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


def _latest_col(rows: list[list[Any]], label: str, header: int | None) -> tuple[int, int]:
    ri = cs._find_row(rows, label)
    assert ri is not None, label
    got = cs.latest_cell(rows, ri, header)
    assert got.col is not None and got.value is not None, got.reason
    return ri, got.col


@pytest.mark.parametrize(("label", "factor"), [
    ("Total Cash & ST Investments", 1e-3), ("Total Cash & ST Investments", 1e3),
    ("Total Debt", 1e-3)])
def test_bc_d10_one_balance_cell_a_unit_step_off_is_refused(label: str, factor: float) -> None:
    """THE VERIFIER'S CASE, on SMPL's export as it stands: the quarterly balance sheet's latest
    cash (or debt) cell scaled by 1,000, every unit line still stating Millions. Before: `ok`,
    `agree`. Now refused, the cell and its re-read named."""
    b = _real("SMPL")
    before = cb.extract(b, "SMPL")
    assert before.ok and before.scale_check != CHECK_DIFFER, before.failures
    bs = b.sheet("financials", "Balance Sheet", freq="quarterly")
    ri, col = _latest_col(bs, label, cs._bs_period_header(bs))
    bs[ri][col] = float(bs[ri][col]) * factor
    after = cb.extract(b, "SMPL")
    assert not after.ok and after.scale_check == CHECK_DIFFER
    assert any(f.startswith(f"SCALE: '{label}' reads") and "re-add to there" in f
               for f in after.failures), after.failures


def test_bc_d10_one_flow_cell_a_unit_step_off_is_refused() -> None:
    """The annual Cash Flow sheet's latest operating cash flow ×1,000: its four quarters re-add to
    a thousandth of it."""
    b = _real("SMPL")
    cf = b.sheet("financials", "Cash Flow", freq="annual")
    ri, col = _latest_col(cf, "Cash from Ops.", cs._period_header(cf))
    cf[ri][col] = float(cf[ri][col]) * 1e3
    after = cb.extract(b, "SMPL")
    assert not after.ok and after.scale_check == CHECK_DIFFER
    assert any(f.startswith("SCALE: 'Cash from Ops.' reads") for f in after.failures)


def test_bc_d10_no_committed_pages_export_is_one_unit_step_from_its_own_rows() -> None:
    """(−) CORPUS BEFORE SYNTHETIC: on every page's export as it stands, no figure the bridge
    reads is a unit step from its re-read (measured 2026-11-10: 0.93-1.36x, cash and debt exact)."""
    store = LocalFolderStore.from_config(get_config())
    held = [t for t in _PAGES if store.files(t)]
    if not held:
        pytest.skip("no licensed CIQ bundle on this machine (never committed)")
    for t in held:
        facts = cb.extract(CiqBundle.from_files(t, store.files(t)), t)
        assert not any("re-add to there" in f for f in facts.failures), (t, facts.failures)


def test_bc_d10_the_step_is_a_unit_and_only_a_unit() -> None:
    """(+) 1,000x and 1,000,000x either way, within a factor of 2. (−) A real gap (1.36x, BDX's
    three-quarter re-read), a sign flip, and 100x — the cents-and-dollars ratio, which is no CIQ
    unit — are not a unit step."""
    assert [cb.unit_step(v, 1.0) for v in (1e3, 7e2, 1e-3, 1.6e-3, 1e6, -1e3 * -1)] == [
        1e3, 1e3, 1e-3, 1e-3, 1e6, 1e3]
    assert [cb.unit_step(v, 1.0) for v in (1.36, -1e3, 100.0, 0.0)] == [None, None, None, None]


def test_bc_d10_twin_the_synthetic_operating_cash_flow_a_unit_step_off_is_refused() -> None:
    b = CiqBundle.from_files(gen.TICKER, sorted((gen.HERE / gen.TICKER).iterdir()))
    assert cb.extract(b, gen.TICKER).ok
    cf = b.sheet("financials", "Cash Flow", freq="annual")
    ri, col = _latest_col(cf, "Cash from Ops.", cs._period_header(cf))
    cf[ri][col] = float(cf[ri][col]) / 1e3
    after = cb.extract(b, gen.TICKER)
    assert not after.ok and after.scale_check == CHECK_DIFFER, after.failures
    assert any(f.startswith("SCALE: 'Cash from Ops.' reads") for f in after.failures)


def test_bc_d10_twin_a_small_flow_a_unit_step_down_is_judged_on_its_cell_not_its_rounding() -> None:
    """(+) An operating cash flow of 40 over four quarters of 10, its annual cell ÷ 1,000: 0.04,
    which the fact rounds to 0.0 — and a 0.0 is no ratio, so the step passed as a zero and the
    magnitude band skips a zero too. The re-read compares the CELL. (−) The same 40 as stated."""
    from vinci.dossier.ltm_quarters import _four_quarters

    def bundle(annual_ocf: float) -> CiqBundle:
        b = CiqBundle.from_files(gen.TICKER, sorted((gen.HERE / gen.TICKER).iterdir()))
        cf = b.sheet("financials", "Cash Flow", freq="annual")
        q = b.sheet("financials", "Cash Flow", freq="quarterly")
        ri, col = _latest_col(cf, "Cash from Ops.", cs._period_header(cf))
        end = cs.latest_cell(cf, ri, cs._period_header(cf)).period
        qhdr, qi = cs._period_header(q), cs._find_row(q, "Cash from Ops.")
        assert end is not None and end.end is not None and qhdr is not None and qi is not None
        four, why = _four_quarters(q, qhdr, end.end)
        assert four is not None, why
        for j, _p in four:
            q[qi][j] = 10.0
        cf[ri][col] = annual_ocf
        return b

    stated = cb.extract(bundle(40.0), gen.TICKER)
    assert not any("re-add to there" in f for f in stated.failures), stated.failures
    off = cb.extract(bundle(0.04), gen.TICKER)
    assert off.value("ocf") == 0.0                      # the rounding that hid it
    assert not off.ok and off.scale_check == CHECK_DIFFER, off.failures
    assert any(f.startswith("SCALE: 'Cash from Ops.' reads 0.04 at") for f in off.failures)


def test_bc_d10_a_small_debt_a_unit_step_down_is_refused_on_a_page_with_no_revenue() -> None:
    """THE OBSERVED CASE, on TECX's export as it stands: Total Debt 3.9 ÷ 1,000 is 0.0039, which
    `_bs` rounds to 0.0 — before, `ok` True. And TECX reports no revenue, so the magnitude screen
    cannot run: a unit step found against the figure's own rows still reads `differ`, never
    `not_run` beside a SCALE refusal."""
    b = _real("TECX")
    assert cb.extract(b, "TECX").ok
    bs = b.sheet("financials", "Balance Sheet", freq="quarterly")
    ri, col = _latest_col(bs, "Total Debt", cs._bs_period_header(bs))
    bs[ri][col] = float(bs[ri][col]) * 1e-3
    after = cb.extract(b, "TECX")
    assert after.value("revenue") is None
    assert not after.ok and after.scale_check == CHECK_DIFFER, (after.scale_check, after.failures)
    assert any(f.startswith("SCALE: 'Total Debt' reads") for f in after.failures), after.failures
