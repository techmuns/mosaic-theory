"""Forward cash-flow consensus reaches the page — but only where the basis survives the crossing.

WHAT WAS MISSING. `CFO`/`Capex`/`FCF` carried actuals and nothing forward; the estimate columns
beside them read `—` while Estimates→Trends carried a consensus for all of them (Capex/CFO/FCF on
18 of 19 workbooks, D&A on 19 of 19). D&A had no row at all.

WHAT IS FUSED, AND WHAT IS NOT — the whole substance of this change.

  FUSED: CFO and Capex. CIQ names the same measure on both sheets ("Cash from Ops." / "Cash From
  Operations"; "Capital Expenditure" both sides), and the sign convention matches (capex negative in
  both).

  NOT FUSED: FCF. The actuals row is **Levered Free Cash Flow**; the consensus row is plain **Free
  Cash Flow**. Measured across the fleet, consensus FCF is not even CFO − capex: within 2% on only
  4 of 15 measurable names, SIGN-FLIPPED on AORT (−2.16x) and WERN (−7.79x), and 19.35x on PENG. And
  Trends carries no fiscal year overlapping the actuals, so there is **no period on which the two
  bases can be tested against each other**.

  NOT FUSED: D&A. NFLX's Cash Flow sheet carries BOTH `Depreciation & Amort.` (~372) and
  `Other Amortization` (~9,216 — the content assets), so what "D&A" denotes depends on the business;
  and UBER's own committed bear point already records the divergence: *"estimate columns imply 2,952
  of D&A against 737 in the actuals (4.01x), so the forward EBITDA add-back is a DIFFERENT basis"*.

WHY IT MATTERS, MEASURED. Had FCF been fused, the step from the last actual to the first consensus
column would have rendered as a real change on every name — median |step| **51%** across 17 names:
WERN −982% (sign flip), FUBO +281%, VRRM +184%, PENG −168%, AORT +166%, NFLX −49% (25,388 → 12,868).
A reader scanning that row sees free cash flow halving. Nothing halved; the basis changed.
"""
from __future__ import annotations

import pytest

from vinci.dossier.ciq_sheets import _C1_CF, _C1_CF_CONSENSUS_ONLY, financial_summary_annual


def _bundle(ticker: str):
    """The name's bundle, or SKIP — the licensed workbooks are never committed."""
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.manual_store import LocalFolderStore

    files = LocalFolderStore(get_config().data_dir / "manual" / "ciq").files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


def _table(ticker: str):
    t = financial_summary_annual(_bundle(ticker)).value
    assert t is not None
    return t, {r.label: r for r in t.rows}, sum(1 for e in t.is_estimate if e)


@pytest.mark.parametrize("ticker", ["NFLX", "NCNO", "V"])
def test_cfo_and_capex_now_carry_their_forward_consensus(ticker: str) -> None:
    """THE FEATURE. Both were blank in the estimate columns and both are safely fusable, because the
    two sheets name the same measure on each side."""
    _t, rows, n_est = _table(ticker)
    for label in ("CFO ($M)", "Capex ($M)"):
        row = rows.get(label)
        assert row is not None, f"{ticker}: {label} is missing entirely"
        est = row.values[-n_est:]
        assert any(v is not None for v in est), (
            f"{ticker}: {label} still has no forward consensus — the fuse did not reach it")


@pytest.mark.parametrize("ticker", ["NFLX", "NCNO", "V"])
def test_fcf_and_da_actuals_rows_stay_blank_across_the_estimate_boundary(ticker: str) -> None:
    """THE REFUSAL, and the point of the whole change. A consensus figure in these rows would assert
    that it continues the actuals' basis — an identity no available period can test."""
    _t, rows, n_est = _table(ticker)
    for label in ("FCF ($M)", "D&A ($M)"):
        row = rows.get(label)
        if row is None:
            continue
        assert all(v is None for v in row.values[-n_est:]), (
            f"{ticker}: {label} fused a consensus figure into a row whose actuals are a different "
            f"CIQ measure — this is the 'same window, different basis' defect")


@pytest.mark.parametrize("ticker", ["NFLX", "NCNO", "V"])
def test_the_consensus_lives_in_its_own_labelled_row(ticker: str) -> None:
    """…and it is not simply dropped. The forward view IS decision-relevant; it just may not be
    graphed against the history. Its actual columns are blank and its label says the basis."""
    t, rows, n_est = _table(ticker)
    for label, _metric in _C1_CF_CONSENSUS_ONLY:
        row = rows.get(label + " ($M)")
        assert row is not None, (
            f"{ticker}: {label} row missing — the consensus was dropped rather than moved")
        assert "consensus basis" in row.label, "the row must say the basis in its own label"
        assert all(v is None for v in row.values[:-n_est]), (
            f"{ticker}: {label} carries a figure in an ACTUALS column")
        assert any(v is not None for v in row.values[-n_est:]), (
            f"{ticker}: {label} exists but carries no consensus figure — an empty row is the "
            f"defect PR-C removed from the estimate columns")


@pytest.mark.parametrize("ticker", ["NFLX", "NCNO", "V", "VITL", "WERN"])
def test_no_column_carries_both_an_actual_and_a_consensus_for_the_same_metric(ticker: str) -> None:
    """THE INVARIANT BEHIND THE SPLIT, stated so it cannot be undone by accident: for FCF and D&A
    the actuals and consensus rows must never both hold a value in one column. If they did,
    one period would carry two different measures of the same thing under one heading."""
    t, rows, _n = _table(ticker)
    for actual_label, cons_label in (("FCF ($M)", "FCF (consensus basis) ($M)"),
                                     ("D&A ($M)", "D&A (consensus basis) ($M)")):
        a, c = rows.get(actual_label), rows.get(cons_label)
        if a is None or c is None:
            continue
        overlap = [t.columns[i] for i, (x, y) in enumerate(zip(a.values, c.values, strict=True))
                   if x is not None and y is not None]
        assert not overlap, (
            f"{ticker}: {overlap} carry both an actual and a consensus {actual_label}")


def test_the_fuse_table_records_which_metrics_are_fusable() -> None:
    """The decision is DATA, not scattered branches — so which metrics fuse is auditable in one
    place and a future edit has to face the basis question rather than stumble past it."""
    fusable = {display: est for display, _cf, est in _C1_CF}
    assert fusable["CFO"] and fusable["Capex"], "CFO/Capex are same-measure on both sheets"
    assert fusable["FCF"] is None, "FCF must not fuse — levered actuals vs plain consensus"
    assert fusable["D&A"] is None, "D&A must not fuse — the add-back basis diverges (UBER 4.01x)"
    assert {label for label, _m in _C1_CF_CONSENSUS_ONLY} == {
        "FCF (consensus basis)", "D&A (consensus basis)"}, (
        "every non-fusable metric needs its own row, or the consensus is silently dropped")
