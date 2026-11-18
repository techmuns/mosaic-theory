"""§5.0 row 11 (b) — net debt reads its cash AT the filer's newest balance sheet.

Net debt reads every line AT the cash instant (`vinci.edgar.net_debt`), and the cash instant was
the latest one the alias walk's cash series carried, however old. PennyMac Mortgage's cash aliases
stop at 2018-12-31, so the screen's snapshot served a net debt of $5,958M read off its 2018
balance sheet beside 10-Qs to 2026-09-30 (`docs/records/2026-11-17-the-monitors-stale-tag-row-is-
retired.md`, found; `docs/records/2026-11-19-net-debt-reads-its-cash-at-the-newest-balance-
sheet.md`, fixed). OPTION 2 (coordinator's ruling): the cash is read at the filer's newest balance
sheet (`balance_sheet_date`: the newest `Assets` instant, us-gaap or ifrs-full), from the first
cash alias that carries it in dollars. Only when none does is the walk's latest cash read, and then
only within `CASH_MAX_AGE_DAYS` (180, two quarters) of it; older is refused, naming both dates.

Every pin runs on a FROZEN real filer (`tests/fixtures/cash_age/`, README there).
"""
from __future__ import annotations

import json
import pathlib
from datetime import date
from typing import Any

from vinci.edgar.client import compute_fundamental_snapshot
from vinci.edgar.concepts import CONCEPT_ALIASES, extract_points, facts_as_of, latest_instant
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
        "no cash line is tagged at the filer's 2026-09-30 balance sheet, and the one read, "
        "CashAndCashEquivalentsAtCarryingValue, was last reported $60M at 2018-12-31, 2830d "
        "before it — a past balance sheet, not read as current")


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
    assert snap["note"].startswith("no cash line is tagged at the filer's 2026-06-30 balance "
                                   "sheet, and the one read, CashAndCashEquivalentsAtCarryingValue"
                                   ", was last reported $60M at 2018-12-31, 2738d before it")
    for key in ("fundamentals.net_leverage", "fundamentals.net_debt_to_ocf"):
        assert got[key]["coverage_status"] == "unknown", key
        assert got[key]["note"].startswith("no net-debt — no cash line is tagged at"), key


def test_three_quarters_behind_is_refused() -> None:
    """Jack in the Box's cash alias stops at 2025-07-06; its balance sheet runs to 2026-04-12,
    280d later."""
    nd = net_debt(_facts("JACK"))
    assert nd is not None and nd.at == date(2025, 7, 6) and nd.stale_cash == date(2026, 4, 12)
    assert nd.value(Basis.LEVERAGE) is None


_ALIAS_1, _ALIAS_2 = CONCEPT_ALIASES["cash"]


def test_a_second_alias_at_the_newest_balance_sheet_is_read() -> None:
    """Diebold tags `CashAndCashEquivalentsAtCarryingValue` to 2026-03-31 and the restricted-cash
    total to every quarter since. The alias walk serves the first (its 200d sibling rule), so net
    debt read the 2026-03-31 balance sheet: refused under a 180d bound on today's blob (183d), and
    $607.6M as filed by 2026-10-16. Its cash is read at its newest balance sheet now, from the
    alias that carries it: 2026-09-30 today, 2026-06-30 at the run's cut."""
    facts = _facts("DBD")
    walked = latest_instant([p for p in extract_points(facts, "cash") if p.unit == "USD"])
    assert walked is not None and (walked.tag, walked.period_end) == (_ALIAS_1, date(2026, 3, 31))
    nd = net_debt(facts)
    assert nd is not None and nd.refusal is None and nd.stale_cash is None
    assert (nd.at, nd.cash.tag, nd.cash.value) == (date(2026, 9, 30), _ALIAS_2, 184_900_000.0)
    then = net_debt(facts, as_of=date(2026, 10, 16))
    assert then is not None and then.refusal is None
    assert (then.at, then.cash.tag, then.cash.value) == (date(2026, 6, 30), _ALIAS_2,
                                                         282_400_000.0)


def test_eastman_at_the_runs_cut_reads_its_june_balance_sheet() -> None:
    """THE OSCILLATION OPTION 1 FOUND. Eastman tags `CashAndCashEquivalentsAtCarryingValue` only in
    its 10-K and the restricted-cash total in its 10-Qs. The walk keeps the first while the second
    leads by 200d or less, so after Q1 (90d) and Q2 (181d) net debt read the 2025-12-31 year end,
    and after Q3 (273d) it switches. A 180d bound refused it at the run's cut (181d). As filed by
    2026-10-16 its cash is read at its 2026-06-30 balance sheet, $691M; today, at 2026-09-30."""
    facts = _facts("EMN")
    cut = facts_as_of(facts, date(2026, 10, 16))
    walked = latest_instant([p for p in extract_points(cut, "cash") if p.unit == "USD"])
    assert walked is not None and (walked.tag, walked.period_end) == (_ALIAS_1, date(2025, 12, 31))
    assert balance_sheet_date(cut) == date(2026, 6, 30)
    nd = net_debt(facts, as_of=date(2026, 10, 16))
    assert nd is not None and nd.refusal is None
    assert (nd.at, nd.cash.tag, nd.cash.value) == (date(2026, 6, 30), _ALIAS_2, 691_000_000.0)
    walked_now = latest_instant([p for p in extract_points(facts, "cash") if p.unit == "USD"])
    assert walked_now is not None and walked_now.tag == _ALIAS_2, "after Q3 the walk switches"
    now = net_debt(facts)
    assert now is not None and (now.at, now.cash.tag) == (date(2026, 9, 30), _ALIAS_2)


def test_with_no_alias_at_the_newest_two_quarters_behind_is_refused_and_one_is_not() -> None:
    """THE BACKSTOP. AdaptHealth tags neither cash alias at its 2026-06-30 or 2026-09-30 balance
    sheet; its cash stops at 2026-03-31. As filed by 2026-10-16 that is one quarter (91d) behind
    its newest and is read; on today's blob it is two quarters (183d) behind and refused."""
    facts = _facts("AHCO")
    then = net_debt(facts, as_of=date(2026, 10, 16))
    assert then is not None and then.refusal is None and then.at == date(2026, 3, 31)
    nd = net_debt(facts)
    assert nd is not None and nd.at == date(2026, 3, 31) and nd.stale_cash == date(2026, 9, 30)
    assert (nd.stale_cash - nd.at).days == 183 > CASH_MAX_AGE_DAYS
    assert nd.value(Basis.LEVERAGE) is None


def test_an_ifrs_balance_sheet_dates_the_filers_newest() -> None:
    """Himax's us-gaap cash and balance sheet both stop at 2017-12-31; its IFRS balance sheets run
    to 2025-12-31. Measured against us-gaap alone the cash was current (0d), and only an
    under-capture witness on the 2017 balance sheet refused it. It is refused now as what it is: a
    2017 balance sheet, 2,922d behind the filer's newest."""
    nd = net_debt(_facts("HIMX"))
    assert nd is not None and nd.at == date(2017, 12, 31)
    assert nd.stale_cash == date(2025, 12, 31)
    assert (nd.refusal or "").startswith("no cash line is tagged at the filer's 2025-12-31")


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


def test_one_quarter_behind_reads_the_newest_balance_sheet_where_an_alias_carries_it() -> None:
    """Morningstar's walked cash alias stops at 2025-12-31, one quarter behind its 2026-03-31
    balance sheet; inside a 180d bound it was served, at that year end, $543.9M. The restricted-cash
    total carries 2026-03-31, so net debt is read there now: the bound is a backstop, never the
    reason a quarter-old balance sheet is read when the newest is tagged."""
    nd = net_debt(_facts("MORN"))
    assert nd is not None and nd.refusal is None and nd.stale_cash is None
    assert (nd.at, nd.cash.tag, nd.cash.value) == (date(2026, 3, 31), _ALIAS_2, 492_800_000.0)


def test_where_both_aliases_carry_the_newest_the_first_is_read() -> None:
    """THE ORDER IS THE ALIAS LIST'S. Visa tags both cash aliases at its 2026-09-30 balance sheet:
    `CashAndCashEquivalentsAtCarryingValue` $12,938M and the restricted-cash total $19,118M. The
    first is read, as the walk served it; reading the second would net $6,180M of restricted cash.
    712 of the 1,078 cached filers carry both at their newest balance sheet, 405 with different
    values (2026-11-19)."""
    facts = _facts("V")
    newest = balance_sheet_date(facts)
    assert newest == date(2026, 9, 30)
    nd = net_debt(facts)
    assert nd is not None and nd.refusal is None
    assert (nd.at, nd.cash.tag, nd.cash.value) == (newest, _ALIAS_1, 12_938_000_000.0)
    assert nd.value(Basis.LEVERAGE) == 9_133_000_000.0


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
