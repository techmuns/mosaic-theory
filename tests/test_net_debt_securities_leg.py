"""§5.0 row 27 — the anchor's net debt nets the SAME cash a CIQ TEV nets.

GOOGL's page carried net DEBT +$64,880M (`anchor.net_debt`) beside net CASH −$121,683M (CIQ,
same quarter). The gap was its $186,563M of marketable securities to the dollar: EDGAR's `cash`
concept is cash and equivalents only, CIQ's is "Total Cash & ST Investments", and every multiple
the anchor's net debt bridges is a CIQ TEV multiple. The anchor now subtracts ONE
current-securities tag, read only at the cash instant
(`vinci.edgar.net_debt._short_term_securities`, the one builder the anchor and the screen's
snapshot share since §5.0 row 27 (1)).

Every pin here runs on frozen REAL data: the companyfacts fixtures, and CIQ's own figures frozen in
`tests/fixtures/ciq_cash_and_st_investments.json` (derived values, read 2026-10-08; the workbooks
are never committed). The independent source is the point — a leg checked only against the tag it
read would test the tag list, not the leg.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
from typing import Any

import pytest

from vinci.dossier import anchor as anc
from vinci.edgar import net_debt as nd
from vinci.edgar.concepts import extract_points, latest_instant, points_for_tag

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "companyfacts"
CIQ: dict[str, dict[str, Any]] = json.loads(
    (ROOT / "tests" / "fixtures" / "ciq_cash_and_st_investments.json").read_text())["names"]


def _facts(ticker: str) -> dict[str, Any]:
    p = FIXTURES / f"{ticker}.json"
    if not p.is_file():
        pytest.skip(f"no committed companyfacts fixture for {ticker}")
    facts: dict[str, Any] = json.loads(p.read_text())
    return facts


def _cash_end(facts: dict[str, Any]) -> dt.date:
    cash = latest_instant(extract_points(facts, "cash"))
    assert cash is not None, "the fixture must carry a cash instant"
    return cash.period_end


def _at(facts: dict[str, Any], tag: str, end: dt.date) -> list[float]:
    return [p.value for p in points_for_tag(facts, tag)
            if p.period_start is None and p.period_end == end]


# --- POSITIVE: EDGAR cash + the leg IS CIQ's cash, on every name the two share a date ---------

#: The tag that reproduces CIQ on each shared date — measured 2026-10-08, one per name.
_EXPECTED_TAG = {
    "AMZN": "MarketableSecuritiesCurrent",
    "GOOGL": "MarketableSecuritiesCurrent",
    "ORKA": "MarketableSecuritiesCurrent",
    "UBER": "MarketableSecuritiesCurrent",
    "NFLX": "ShortTermInvestments",
    "WLK": "AvailableForSaleSecuritiesDebtSecuritiesCurrent",
}


@pytest.mark.parametrize("ticker", sorted(_EXPECTED_TAG))
def test_edgar_cash_plus_the_leg_is_ciqs_cash_and_st_investments(ticker: str) -> None:
    facts = _facts(ticker)
    cash = latest_instant(extract_points(facts, "cash"))
    assert cash is not None
    ciq = CIQ[ticker]
    assert cash.period_end.isoformat() == ciq["balance_sheet_date"], (
        f"{ticker}: the EDGAR cash instant moved off CIQ's balance-sheet date — this comparison "
        "is only meaningful at a shared date; refreeze both sides together")
    leg = nd._short_term_securities(facts, cash.period_end)
    assert leg is not None and leg.tag == _EXPECTED_TAG[ticker], (
        f"{ticker}: read {leg.tag if leg else None}, expected {_EXPECTED_TAG[ticker]}")
    edgar_total = (cash.value + leg.value) / 1e6
    assert edgar_total == pytest.approx(ciq["total_cash_and_st_investments"], abs=0.05), (
        f"{ticker}: EDGAR cash {cash.value / 1e6:,.1f} + {leg.tag} {leg.value / 1e6:,.1f} = "
        f"{edgar_total:,.1f} against CIQ 'Total Cash & ST Investments' "
        f"{ciq['total_cash_and_st_investments']:,.1f}")


def test_googl_reads_net_cash_now_and_equals_ciqs_net_debt() -> None:
    """THE INCIDENT. +$64,880M (net debt) became −$121,683M (net cash) — CIQ's own figure, to the
    dollar, because GOOGL's debt and lease legs already agreed with CIQ's Total Debt."""
    got = anc._lease_inclusive_net_debt(_facts("GOOGL"))
    assert got is not None and got[0] is not None
    ciq = CIQ["GOOGL"]
    assert got[0] / 1e6 == pytest.approx(ciq["total_debt"] - ciq["total_cash_and_st_investments"],
                                         abs=0.5)
    assert got[0] < 0, "GOOGL holds more cash and securities than debt — the sign must say so"
    assert "short-term investments 186,563 (MarketableSecuritiesCurrent, 2026-06-30)" in got[1]


# --- NEGATIVE: the tags that hold MORE than the current balance are never read ----------------

def test_orka_parent_and_noncurrent_securities_are_present_and_not_netted() -> None:
    """ORKA tags the parent ($857.1M) AND its two children ($605.1M current + $252.0M
    noncurrent). Netting the parent takes the noncurrent part; summing all three takes $1,714M.
    CIQ nets $605.1M."""
    facts = _facts("ORKA")
    end = _cash_end(facts)
    assert _at(facts, "MarketableSecurities", end), "the trap must be in the data, or it is vacuous"
    assert _at(facts, "MarketableSecuritiesNoncurrent", end)
    leg = nd._short_term_securities(facts, end)
    assert leg is not None and leg.tag == "MarketableSecuritiesCurrent"
    assert leg.value / 1e6 == pytest.approx(605.094, abs=0.001)


def test_nflx_afs_total_is_present_and_not_netted() -> None:
    """NFLX's `AvailableForSaleSecuritiesDebtSecurities` is $9,131.5M at the cash instant —
    every AFS security, most of them already INSIDE cash equivalents. Its short-term investments
    are $28.7M."""
    facts = _facts("NFLX")
    end = _cash_end(facts)
    afs = _at(facts, "AvailableForSaleSecuritiesDebtSecurities", end)
    assert afs and max(afs) / 1e6 > 9_000, "the trap must be in the data, or this is vacuous"
    leg = nd._short_term_securities(facts, end)
    assert leg is not None and leg.tag == "ShortTermInvestments"
    assert leg.value / 1e6 == pytest.approx(28.678, abs=0.001)


# --- NEGATIVE: a tag that STOPPED before the cash instant is never netted ---------------------

#: Six names that carry a read tag whose series ended before their cash instant (fixtures as of
#: 2026-10-08). CIQ nets none of them either: each one's CIQ cash equals its EDGAR cash.
_STALE = ("EPAM", "LLY", "MVST", "NKE", "ROST", "TGT")


@pytest.mark.parametrize("ticker", _STALE)
def test_a_securities_tag_that_stopped_before_the_cash_instant_is_not_netted(ticker: str) -> None:
    facts = _facts(ticker)
    end = _cash_end(facts)
    present = {t: max(p.period_end for p in points_for_tag(facts, t) if p.period_start is None)
               for t in nd._SHORT_TERM_SECURITIES_TAGS
               if any(p.period_start is None for p in points_for_tag(facts, t))}
    assert present, f"{ticker}: no read tag in the fixture — the stale case is not in the data"
    assert all(last < end for last in present.values()), (
        f"{ticker}: a read tag reaches the cash instant {end} — not a stale case: {present}")
    assert nd._short_term_securities(facts, end) is None
    got = anc._lease_inclusive_net_debt(facts)
    if got is not None:
        assert "short-term investments" not in got[1], f"{ticker}: a stale balance was netted"


def test_wlk_falls_through_a_stale_first_tag_to_the_live_one() -> None:
    """WLK's `MarketableSecuritiesCurrent` stopped in 2016; its current $209M sits under the third
    tag. A stale tag must fall through, not end the search."""
    facts = _facts("WLK")
    end = _cash_end(facts)
    msc = [p.period_end for p in points_for_tag(facts, "MarketableSecuritiesCurrent")]
    assert msc and max(msc) < end, "the stale first tag must be in the data"
    leg = nd._short_term_securities(facts, end)
    assert leg is not None and leg.tag == "AvailableForSaleSecuritiesDebtSecuritiesCurrent"
    assert leg.value / 1e6 == pytest.approx(209.0, abs=0.001)


def test_a_name_without_the_line_keeps_its_bridge_text() -> None:
    """BRBR tags none of the three: its net debt and its bridge text are what they were — the leg
    prints only where it is netted, so a page that moves is a page whose number moved."""
    facts = _facts("BRBR")
    assert not any(points_for_tag(facts, t) for t in nd._SHORT_TERM_SECURITIES_TAGS)
    got = anc._lease_inclusive_net_debt(facts)
    assert got is not None and "short-term investments" not in got[1]
    assert got[1].endswith(" ($M)") and " − cash " in got[1]


# --- THE CONSUMER: the field the page receives, and the value it feeds ------------------------

def test_amzns_anchor_carries_the_leg_and_its_base_value_moves_by_exactly_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pinned on `compute_anchor`'s output, not the helper: `anchor.net_debt` is what the page
    prints and the scenario template copies, and the R1 base value is equity ÷ shares — so the
    leg must raise the base by exactly its own size per share of the count the base divides
    (`per_share_shares`: the point-in-time count since 2026-10-21)."""
    page = ROOT / "data" / "dossiers" / "AMZN" / "dossier.json"
    mech = json.loads(page.read_text())["mechanical"]
    now = dt.datetime(2026, 10, 8, tzinfo=dt.UTC)
    with_leg = anc.compute_anchor(mech, facts=_facts("AMZN"), computed_at=now, ciq=None)
    assert with_leg.net_debt is not None and with_leg.net_debt.value is not None
    assert "short-term investments 44,775 (MarketableSecuritiesCurrent, 2026-06-30)" in (
        with_leg.net_debt.source)

    monkeypatch.setattr(nd, "_SHORT_TERM_SECURITIES_TAGS", ())
    without = anc.compute_anchor(mech, facts=_facts("AMZN"), computed_at=now, ciq=None)
    assert without.net_debt is not None and without.net_debt.value is not None
    assert without.net_debt.value - with_leg.net_debt.value == pytest.approx(44_775.0, abs=0.001)
    shares = anc.per_share_shares(with_leg.model_dump(mode="json"))
    assert shares and with_leg.anchor_base_value_per_share and without.anchor_base_value_per_share
    assert (with_leg.anchor_base_value_per_share - without.anchor_base_value_per_share
            == pytest.approx(44_775e6 / shares, abs=1e-3))
