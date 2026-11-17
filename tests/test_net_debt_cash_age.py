"""§5.0 row 11 (b) — net debt's cash instant is bounded by the filer's newest balance sheet.

Net debt reads every line AT the cash instant (`vinci.edgar.net_debt`), and the cash instant was
the latest one the cash aliases carry, however old. PennyMac Mortgage's cash aliases stop at
2018-12-31, so the screen's snapshot served a net debt of $5,958M read off its 2018 balance sheet
beside 10-Qs to 2026-09-30 (`docs/records/2026-11-17-the-monitors-stale-tag-row-is-retired.md`,
found; `docs/records/2026-11-17-net-debts-cash-instant-is-bounded-by-the-newest-balance-sheet.md`,
fixed). A cash instant more than `CASH_MAX_AGE_DAYS` (180, two quarters) behind the filer's newest
balance sheet (`balance_sheet_date`: the newest `Assets` instant, us-gaap or ifrs-full) is refused,
naming both dates.

Every pin runs on a FROZEN real filer (`tests/fixtures/cash_age/`, README there).
"""
from __future__ import annotations

import json
import pathlib
from datetime import date
from typing import Any

from vinci.edgar.client import compute_fundamental_snapshot
from vinci.edgar.concepts import facts_as_of
from vinci.edgar.net_debt import (
    CASH_MAX_AGE_DAYS,
    Basis,
    balance_sheet_date,
    net_debt,
)
from vinci.facts.screen_replay import screen_inputs
from vinci.schemas.data_record import Identity
from vinci.schemas.envelope import CoverageStatus
from vinci.screens.retention import CandidateRow, read_rows

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "cash_age"
SHAPES = ROOT / "tests" / "fixtures" / "net_debt_shapes"


def _facts(ticker: str, where: pathlib.Path = FIXTURES) -> dict[str, Any]:
    facts: dict[str, Any] = json.loads((where / f"{ticker}.json").read_text())
    return facts


# --- POSITIVE: a cash instant two quarters or more behind the newest balance sheet -------------


def test_pennymac_net_debt_is_no_longer_read_off_its_2018_balance_sheet() -> None:
    """PennyMac's cash aliases stop at 2018-12-31; its balance sheets run to 2026-09-30. Net debt
    was $5,958M, every line read at 2018-12-31. It is refused now, naming the cash line, both
    dates and the 2,830d between them."""
    facts = _facts("PMT")
    assert balance_sheet_date(facts) == date(2026, 9, 30)
    nd = net_debt(facts)
    assert nd is not None and nd.at == date(2018, 12, 31)
    assert nd.value(Basis.LEVERAGE) is None and not nd.nothing_to_read
    assert nd.refusal == (
        "the cash line read, CashAndCashEquivalentsAtCarryingValue, was last reported $60M at "
        "2018-12-31, 2830d before the filer's 2026-09-30 balance sheet — a past balance sheet, "
        "not read as current")


def test_pennymacs_committed_screen_row_names_the_stale_cash() -> None:
    """PennyMac passed every gate of screen run 2026-10-16-01. Its row carried net leverage
    UNKNOWN as "no EBITDA in XBRL" and net debt / OCF as "OCF<=0", each computed over the 2018
    net debt. Replayed through the screen's own code (`screen_inputs`) at the run's cut and
    close, net debt is UNKNOWN and both ratios name the stale cash line, never a missing tag."""
    (row,) = [r for r in read_rows("2026-10-16-01", ROOT / "data" / "snapshots")
              if isinstance(r, CandidateRow) and r.ticker == "PMT"]
    last = row.gate_inputs["last"]
    assert last.value is not None and last.as_of == date(2026, 10, 16)
    # the run's candidate record's identity, as committed with the run (2026-10-16); SIC group 67
    # is not one net debt exempts
    identity = Identity(internal_id="SEC-0001464423-PMT", issuer_id="ISS-0001464423",
                        cik="0001464423", ticker="PMT", mic="XNYS", exchange="NYSE",
                        eod_symbol="PMT", name="PennyMac Mortgage Investment Trust", sic="6798")
    got = screen_inputs(identity, _facts("PMT"), cut=last.as_of, close=float(last.value),
                        reference_date=row.reference_date)
    snap = got["snapshot.net_debt"]
    assert snap["coverage_status"] == "unknown" and snap["value"] is None
    assert snap["note"].startswith("the cash line read, CashAndCashEquivalentsAtCarryingValue, "
                                   "was last reported $60M at 2018-12-31, 2738d before the "
                                   "filer's 2026-06-30 balance sheet")
    for key in ("fundamentals.net_leverage", "fundamentals.net_debt_to_ocf"):
        assert got[key]["coverage_status"] == "unknown", key
        assert got[key]["note"].startswith("no net-debt — the cash line read"), key


def test_three_quarters_behind_is_refused() -> None:
    """Jack in the Box's cash alias stops at 2025-07-06; its balance sheet runs to 2026-04-12,
    280d later."""
    nd = net_debt(_facts("JACK"))
    assert nd is not None and nd.at == date(2025, 7, 6) and nd.stale_cash == date(2026, 4, 12)
    assert nd.value(Basis.LEVERAGE) is None


def test_two_quarters_behind_is_refused_and_one_is_not() -> None:
    """Diebold's served cash alias stops at 2026-03-31. On today's blob its newest balance sheet
    is 2026-09-30, two quarters (183d) later: refused. As filed by 2026-10-16, before its Q3 10-Q,
    the newest is 2026-06-30, one quarter (91d): served, $607.6M. The bound sits between."""
    facts = _facts("DBD")
    nd = net_debt(facts)
    assert nd is not None and nd.at == date(2026, 3, 31) and nd.stale_cash == date(2026, 9, 30)
    assert (nd.stale_cash - nd.at).days == 183 > CASH_MAX_AGE_DAYS
    then = net_debt(facts, as_of=date(2026, 10, 16))
    assert then is not None and then.refusal is None
    assert balance_sheet_date(facts_as_of(facts, date(2026, 10, 16))) == date(2026, 6, 30)
    assert then.value(Basis.LEVERAGE) == 607_600_000.0


def test_an_ifrs_balance_sheet_dates_the_filers_newest() -> None:
    """Himax's us-gaap cash and balance sheet both stop at 2017-12-31; its IFRS balance sheets run
    to 2025-12-31. Measured against us-gaap alone the cash was current (0d), and only an
    under-capture witness on the 2017 balance sheet refused it. It is refused now as what it is: a
    2017 balance sheet, 2,922d behind the filer's newest."""
    nd = net_debt(_facts("HIMX"))
    assert nd is not None and nd.at == date(2017, 12, 31)
    assert nd.stale_cash == date(2025, 12, 31)
    assert (nd.refusal or "").startswith("the cash line read")


def test_an_ifrs_balance_sheet_in_another_currency_still_dates_it() -> None:
    """National Steel's IFRS balance sheets are in BRL. A date carries no currency: its 2024
    balance sheet dates the newest, and its 2009 dollar cash is refused, no BRL figure read."""
    facts = _facts("SID")
    units = set(facts["facts"]["ifrs-full"]["Assets"]["units"])
    assert units == {"BRL"}, "the shape must be in the data"
    assert balance_sheet_date(facts) == date(2024, 12, 31)
    nd = net_debt(facts)
    assert nd is not None and nd.at == date(2009, 12, 31) and nd.stale_cash == date(2024, 12, 31)


# --- NEGATIVE: what must still be served ----------------------------------------------------


def test_one_quarter_behind_is_served() -> None:
    """Morningstar's served cash alias stops at 2025-12-31, one quarter (90d) behind its
    2026-03-31 balance sheet: inside the bound, served at $543.9M."""
    nd = net_debt(_facts("MORN"))
    assert nd is not None and nd.at == date(2025, 12, 31) and nd.refusal is None
    assert nd.stale_cash is None
    assert nd.value(Basis.LEVERAGE) == 543_900_000.0


def test_an_annual_filers_year_end_is_its_newest_balance_sheet() -> None:
    """TAT Technologies files 20-Fs and no 10-Q. Its cash is at its 2025-12-31 year end, months
    before any page date, and that IS its newest balance sheet (0d): served, net cash $39.5M. The
    bound is measured against the filer's own clock, so an annual filer needs no wider one."""
    facts = _facts("TATT")
    assert balance_sheet_date(facts) == date(2025, 12, 31)
    nd = net_debt(facts)
    assert nd is not None and nd.at == date(2025, 12, 31) and nd.refusal is None
    assert nd.value(Basis.LEVERAGE) == -39_547_000.0
    snap = compute_fundamental_snapshot("0000808439", facts)
    assert snap.net_debt.coverage_status is CoverageStatus.PRESENT


def test_a_forward_dated_balance_sheet_does_not_date_the_newest() -> None:
    """Roper's 10-Q filed 2009-11-02 tags `Assets` at 2009-12-31, a period not yet ended. As filed
    by 2009-11-30 the newest balance sheet is 2009-09-30, not that forward date."""
    facts = facts_as_of(_facts("ROP"), date(2009, 11, 30))
    rows = [r for u in facts["facts"]["us-gaap"]["Assets"]["units"].values() for r in u]
    assert any(r["end"] == "2009-12-31" and r["filed"] == "2009-11-02" for r in rows)
    assert balance_sheet_date(facts) == date(2009, 9, 30)


def test_a_fixture_without_a_balance_sheet_total_is_not_measured() -> None:
    """A frozen net-debt shape cut before `Assets` was read carries no balance-sheet total, so the
    cash instant's age is not measured and its reading is unchanged (every real filer with a dollar
    cash line on the 2026-11-17 cache tags one)."""
    facts = _facts("ATEC", SHAPES)
    assert balance_sheet_date(facts) is None
    nd = net_debt(facts)
    assert nd is not None and nd.stale_cash is None
