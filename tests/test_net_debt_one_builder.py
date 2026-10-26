"""§5.0 row 27 (1) — ONE net-debt builder, every balance-sheet line read at ONE date.

The screen's snapshot (`client.compute_fundamental_snapshot`) and the anchor
(`anchor._lease_inclusive_net_debt`) each built net debt by hand, reading every leg at THAT LEG's
latest date. A tag the filer stopped using was served for years beside a current balance sheet,
and the two formulas disagreed by ≥0.25x EBITDA on 121 of 1,694 universe names beyond the
operating leases that separate them on purpose (`docs/records/2026-10-19-net-debt-one-builder.md`).
Both now read `vinci.edgar.net_debt`.

Every pin runs on frozen REAL data:
- `tests/fixtures/companyfacts/` — the committed dossier names (their builder tags merged in at each
  fixture's own filing vintage);
- `tests/fixtures/net_debt_shapes/` — thirteen names outside the dossier set, one per tagging shape
  the rules were measured on, frozen from the companyfacts cache fetched 2026-08-06..2026-10-18
  (`python scripts/build_companyfacts_fixture.py --net-debt-shapes <TICKERS>`);
- `tests/fixtures/ciq_net_debt_one_builder.json` — CIQ's own Total Debt and Total Cash & ST
  Investments, read 2026-10-19 (derived scalars; the workbooks are never committed). The
  independent source is the point: a reading checked only against the tags it read tests the tag
  list, not the reading.
"""
from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime
from typing import Any, cast

import pytest

from vinci.dossier import anchor as anc
from vinci.edgar import concepts
from vinci.edgar import net_debt as nd
from vinci.edgar.client import EdgarClient, FundamentalSnapshot, compute_fundamental_snapshot
from vinci.screens.assemble import enrich_with_fundamentals

ROOT = pathlib.Path(__file__).resolve().parents[1]
FACTS = ROOT / "tests" / "fixtures" / "companyfacts"
FROZEN = ROOT / "tests" / "fixtures" / "companyfacts_frozen"
SHAPES = ROOT / "tests" / "fixtures" / "net_debt_shapes"
CIQ: dict[str, dict[str, Any]] = json.loads(
    (ROOT / "tests" / "fixtures" / "ciq_net_debt_one_builder.json").read_text())["names"]
M = 1e6


def _facts(ticker: str) -> dict[str, Any]:
    # a FROZEN vintage first: these pins compare EDGAR with CIQ figures frozen at a shared date, and
    # the tracking fixture moves with every re-assembly (`tests/fixtures/companyfacts_frozen/`)
    p = FROZEN / f"{ticker}.json"
    if not p.is_file():
        p = FACTS / f"{ticker}.json"
    if not p.is_file():
        p = SHAPES / f"{ticker}.json"
    facts: dict[str, Any] = json.loads(p.read_text())
    return facts


def _read(ticker: str) -> nd.NetDebt:
    got = nd.net_debt(_facts(ticker))
    assert got is not None, f"{ticker}: the fixture must carry a cash line"
    return got


def _ciq_net_debt(ticker: str) -> float:
    c = CIQ[ticker]
    return float(c["total_debt"] - c["total_cash_and_st_investments"])


def _anchor_value(ticker: str) -> float | None:
    got = anc._lease_inclusive_net_debt(_facts(ticker))
    return None if got is None or got[0] is None else got[0] / M


# --- POSITIVE: the anchor's reading is CIQ's, on every name the two share a date ----------------

#: UBER is held out by name: its debt line is now its own `LongTermDebt` total, and the remaining
#: +$222M to CIQ is its finance leases, which CIQ's total debt does not carry beside it
#: (below, `test_the_moved_names_move_toward_ciq`).
_AGREES = sorted(set(CIQ) - {"UBER"})


@pytest.mark.parametrize("ticker", _AGREES)
def test_the_anchor_reads_ciqs_net_debt_on_every_shared_date(ticker: str) -> None:
    """The EV basis against CIQ's Total Debt − Total Cash & ST Investments, both at the same
    balance-sheet date: within $15M or 1% of CIQ's total debt (rounding, issuance costs)."""
    reading = _read(ticker)
    assert reading.at.isoformat() == CIQ[ticker]["balance_sheet_date"], "not a shared date"
    got = _anchor_value(ticker)
    assert got is not None, f"{ticker}: refused ({reading.refusal})"
    tol = max(15.0, 0.01 * CIQ[ticker]["total_debt"])
    assert got == pytest.approx(_ciq_net_debt(ticker), abs=tol), (ticker, got, reading.refusal)


#: The anchor's net debt on main c4ebdc37 (2026-10-19), before the builder: each leg at its own
#: latest date. BURL and TGT read a stale `LongTermDebt`, WERN a current tag a quarter old, UBER
#: missed its $1,997M of current maturities.
_BEFORE = {"BURL": 5338.32, "TGT": 14804.0, "WERN": 896.501, "UBER": 7565.0}


@pytest.mark.parametrize("ticker", sorted(_BEFORE))
def test_the_moved_names_move_toward_ciq(ticker: str) -> None:
    """Every committed anchor this moves lands closer to CIQ's own figure than it was."""
    got = _anchor_value(ticker)
    assert got is not None
    ciq = _ciq_net_debt(ticker)
    assert abs(got - ciq) < abs(_BEFORE[ticker] - ciq), (ticker, got, _BEFORE[ticker], ciq)


def _burl_anchor(lease_basis: dict[str, Any] | None) -> Any:
    """BURL's anchor with the page's lease basis SET or REMOVED explicitly (#750's convention), so
    the pin reads one state before and after the artifact pass lands the block on the page."""
    mech = json.loads((ROOT / "data" / "dossiers" / "BURL" / "dossier.json").read_text())[
        "mechanical"]
    mech["valuation"].pop("lease_basis", None)
    if lease_basis is not None:
        mech["valuation"]["lease_basis"] = lease_basis
    return anc.compute_anchor(mech, facts=_facts("BURL"),
                              computed_at=datetime(2026, 10, 19, tzinfo=UTC), ciq=None)


def test_the_page_field_carries_the_reading_on_both_bridges() -> None:
    """Pinned on `compute_anchor`, the field the page prints.

    WITHOUT a lease basis R1 bridges CIQ's own history, and BURL's `anchor.net_debt` is CIQ's
    $5,202M on the EV basis; the bridge names the debt-and-finance-lease line, adding no lease
    twice. WITH its material lease basis (#750) R1 prices the ex-lease history, and the net debt
    is the builder's LEVERAGE basis — the same reading less exactly its $3,993M of operating
    leases, printed as EXCLUDED."""
    ev = _burl_anchor(None)
    assert ev.net_debt is not None and ev.net_debt.value == pytest.approx(5202.4, abs=0.5)
    assert "total debt incl. finance leases 1,914 + operating leases 3,993" in ev.net_debt.source
    assert "+ finance leases" not in ev.net_debt.source
    lb = json.loads((ROOT / "tests" / "fixtures" / "lease_basis" / "BURL.json").read_text())
    assert lb["material"], "BURL's frozen lease basis must be the material case"
    ex = _burl_anchor(lb)
    assert ex.net_debt is not None and ex.net_debt.basis == anc.NET_DEBT_EX_LEASE
    reading = _read("BURL")
    assert ex.net_debt.value == pytest.approx(reading.value(nd.Basis.LEVERAGE) / M, abs=1e-3)
    assert ev.net_debt.value - ex.net_debt.value == pytest.approx(3993.0, abs=0.5)
    assert "operating leases 3,993 EXCLUDED" in ex.net_debt.source


# --- ONE BUILDER: the screen and the anchor differ by operating leases and nothing else ---------

def test_the_screen_and_the_anchor_differ_by_exactly_operating_leases() -> None:
    """The invariant two formulas could not hold. On every committed fixture with a reading, the
    screen's snapshot (LEVERAGE basis) is the anchor's figure (EV basis) less operating leases —
    to the dollar — and a refusal in one is a refusal in the other."""
    compared = 0
    for p in sorted(FACTS.glob("*.json")):
        facts = json.loads(p.read_text())
        reading = nd.net_debt(facts)
        snap = compute_fundamental_snapshot("x", facts).net_debt
        a = anc._lease_inclusive_net_debt(facts)
        if reading is None or reading.refusal is not None:
            assert not snap.is_known and (a is None or a[0] is None), p.stem
            continue
        assert snap.value is not None and a is not None and a[0] is not None
        assert a[0] - snap.value == pytest.approx(reading.operating_leases, abs=1.0), p.stem
        compared += 1
    assert compared >= 20, f"only {compared} names compared — near-vacuous"


# --- ONE DATE: a line absent from the balance sheet is never served from an older one -----------

def test_a_current_tag_a_quarter_old_is_not_read() -> None:
    """WERN's `LongTermDebtCurrent` stopped at 2026-03-31; its 2026-06-30 sheet carries none (its
    total equals its noncurrent line, $793M). Reading the stale $9M put its net debt at $897M
    against CIQ's $889M."""
    facts = _facts("WERN")
    cur = [q for q in concepts.points_for_tag(facts, "LongTermDebtCurrent") if q.is_instant]
    assert max(q.period_end for q in cur).isoformat() == "2026-03-31"
    reading = _read("WERN")
    assert reading.borrowings is not None and reading.borrowings.value / M == pytest.approx(793.0)
    assert all(q.period_end == reading.at for q in reading.borrowings.read)


@pytest.mark.parametrize(("ticker", "stopped"), [
    ("TECX", "LongTermDebt last reported $15M at 2023-03-31"),
    ("KLIC", "LongTermDebt last reported $109M at 2012-03-31"),
])
def test_a_debt_line_absent_from_the_balance_sheet_is_refused(ticker: str, stopped: str) -> None:
    """A filer that used the standard tags and reports none at the date has repaid or MOVED its
    debt, and the two cannot be told apart: of 195 such names about 110 still show debt
    elsewhere, so zero would invent net cash. Refused — never the old balance (TECX: a $15M
    2023 figure; CIQ carries no debt), never zero."""
    reading = _read(ticker)
    assert reading.value(nd.Basis.LEVERAGE) is None and reading.value(nd.Basis.EV) is None
    assert reading.refusal is not None and "no debt line on the" in reading.refusal
    assert stopped in reading.refusal
    snap = compute_fundamental_snapshot("x", _facts(ticker))
    assert not snap.net_debt.is_known and not snap.net_leverage.is_known
    assert "no debt line on the" in (snap.net_leverage.note or ""), "the ratio names the reason"


# --- HOW THE DEBT LINE IS READ, one shape per rule ----------------------------------------------

def test_the_bare_total_completes_a_missing_current_tag() -> None:
    """OC: $899M of maturing senior notes sit under `SeniorNotesCurrent`, so noncurrent + current
    ($4,226M) misses them and the bare `LongTermDebt` ($5,125M) does not. Its $65M of short-term
    borrowings are genuine and are added — the NEGATIVE of the double-tag rule below."""
    b = _read("OC").borrowings
    assert b is not None and b.value / M == pytest.approx(5125.0 + 65.0)
    assert "ShortTermBorrowings" in {q.tag for q in b.read}


def test_current_maturities_tagged_twice_are_not_added_twice() -> None:
    """ATEC tags its $65.0M of current maturities as `LongTermDebtCurrent` AND as a short-term
    borrowing; its own total ($575.8M) is noncurrent + that one figure."""
    b = _read("ATEC").borrowings
    assert b is not None and b.value / M == pytest.approx(575.8, abs=0.05)
    assert "ShortTermBorrowings" not in {q.tag for q in b.read}


def test_borrowings_inside_the_bare_total_are_not_added() -> None:
    """UBER tags its current maturities as "short-term borrowings": $10,726M noncurrent + $1,997M =
    its $12,723M `LongTermDebt`. The old reading missed the $1,997M; adding it on top of the total
    would count it twice."""
    b = _read("UBER").borrowings
    assert b is not None and b.value / M == pytest.approx(12723.0)


def test_the_filers_own_total_settles_borrowings_inside_long_term_debt() -> None:
    """CSIQ's bare `LongTermDebt` ($6,010.3M) already carries its $2,389.0M of short-term
    borrowings — its own total debt says so. NEGATIVE: without that total, nothing settles it and
    the borrowings are added, so it is the arbiter doing the work, not the tag list."""
    facts = _facts("CSIQ")
    b = _read("CSIQ").borrowings
    assert b is not None and b.value / M == pytest.approx(6010.3, abs=0.05)
    stripped = {**facts, "facts": {ns: {t: v for t, v in node.items()
                                        if t != "DebtLongtermAndShorttermCombinedAmount"}
                                   for ns, node in facts["facts"].items()}}
    b2 = nd._borrowings(stripped, _read("CSIQ").at)
    assert b2 is not None and b2.value / M == pytest.approx(6010.3 + 2389.0, abs=0.05)


def test_the_bare_tag_beside_a_current_tag_is_the_noncurrent_line() -> None:
    """AAL tags `LongTermDebt` ($25,254M) and `LongTermDebtCurrent` ($2,979M) at the same date and
    no noncurrent tag: the bare tag is the noncurrent face line, and the sum is within 2% of its
    own total debt ($28,565M) — the old anchor's guard would have dropped the $2,979M."""
    b = _read("AAL").borrowings
    assert b is not None and b.value / M == pytest.approx(25254.0 + 2979.0)
    total = nd._at(_facts("AAL"), "DebtLongtermAndShorttermCombinedAmount", _read("AAL").at)
    assert total is not None and nd._close(b.value, total.value)


def test_the_debt_and_lease_line_is_read_before_a_bare_current_tag() -> None:
    """PPC carries $0.9M under `LongTermDebtCurrent` beside $2,861.4M under
    `LongTermDebtAndCapitalLeaseObligations`; the current tag alone would read as all the debt.
    Finance leases are inside that line and are not added again."""
    r = _read("PPC")
    assert r.borrowings is not None and r.borrowings.finance_leases_inside
    assert r.borrowings.value / M == pytest.approx(2862.3, abs=0.05)
    assert r.finance_leases == 0.0


def test_a_moved_debt_line_is_read_where_it_moved() -> None:
    """LUMN moved its debt to the debt-and-finance-lease family: $13,150M + $56M current, its own
    $13,206M `DebtAndCapitalLeaseObligations`. The old reading served its 2021 `LongTermDebt`
    of $31,500M beside a 2026-06-30 balance sheet."""
    r = _read("LUMN")
    assert r.borrowings is not None and r.borrowings.value / M == pytest.approx(13206.0)
    assert "LongTermDebt" not in {q.tag for q in r.borrowings.read}


def test_notes_in_the_borrowing_tag_are_read_and_their_total_is_held() -> None:
    """NFLX's $2,483.8M of current notes are tagged as short-term borrowings; its `NotesPayable`
    $14,309M is the whole reading's total, so the witness holds it. Without them its net debt
    was refused; with them it is within 0.2% of CIQ's $7,527M."""
    r = _read("NFLX")
    assert r.refusal is None and r.borrowings is not None
    assert r.borrowings.value / M == pytest.approx(11825.5 + 2483.8, abs=0.1)


# --- THE WITNESS: debt the reading cannot hold is refused, never a confident false net cash -----

def test_the_filers_own_total_above_the_reading_refuses_it() -> None:
    """RYZ: only a $2.6M current tag is readable, and its own total debt is $955M — debt in a tag
    no rule reads. Refused, naming the total (it would otherwise read net CASH)."""
    r = _read("RYZ")
    assert r.value(nd.Basis.LEVERAGE) is None
    assert r.refusal is not None and "DebtLongtermAndShorttermCombinedAmount $955M" in r.refusal


def test_mvsts_bank_borrowings_total_is_not_its_debt() -> None:
    """MVST's own "total debt" ($118.6M) is its bank borrowings only; CIQ counts $56.9M of
    subordinated and current notes beside it. It is a witness and an arbiter, never the debt line
    — read as the line it would put MVST at +$8M against CIQ's +$65M."""
    r = _read("MVST")
    assert r.borrowings is None and r.refusal is not None and "under-captured" in r.refusal


# --- LEASES: the filer's total first; an annual note is read, a stale line is not --------------

def test_the_lease_total_is_read_over_one_part() -> None:
    """PENG reports $65.5M of operating leases at 2026-05-29 but only the $59.3M noncurrent part
    (the current part is a note line). The total is what reproduces CIQ ($68.4M net debt)."""
    r = _read("PENG")
    assert r.operating_leases / M == pytest.approx(65.5, abs=0.05)
    assert [q.tag for q in r.operating_lease_points] == ["OperatingLeaseLiability"]


def test_an_annual_note_lease_is_read_and_a_stale_one_is_not() -> None:
    """BRBR discloses its leases only in the 10-K note (2025-09-30), within the bound of its
    2026-06-30 sheet: read. NEGATIVE: FLR's operating-lease tags stopped at 2019-09-30 ($278M) —
    older than the bound, so not read, where the old anchor still added them."""
    brbr = _read("BRBR")
    assert brbr.operating_leases > 0
    assert all(q.period_end < brbr.at and (brbr.at - q.period_end).days <= nd.LEASE_MAX_AGE_DAYS
               for q in brbr.operating_lease_points)
    flr = _read("FLR")
    stale = [q for t in nd._OPERATING_LEASE_TAGS[1]
             for q in concepts.points_for_tag(_facts("FLR"), t)]
    assert stale and max(q.period_end for q in stale).isoformat() == "2019-09-30"
    assert flr.operating_leases == 0.0 and flr.refusal is None


# --- BANKS, LENDERS, INSURERS: no net-debt leverage, on every surface that reads it -------------

def _snap() -> FundamentalSnapshot:
    return compute_fundamental_snapshot("x", _facts("WERN"))


class _Edgar:
    def fundamental_snapshot(self, cik: int | str) -> FundamentalSnapshot:
        return _snap()

    def companyfacts(self, cik: int | str) -> dict[str, Any]:
        return {}


def _enriched(sic: str | None) -> Any:
    from tests.test_screen2 import REF, _rec
    rec = _rec(drawdown=-0.4, rel=-0.3, pe_pctile=0.1)
    rec = rec.model_copy(update={"identity": rec.identity.model_copy(update={"sic": sic})})
    return enrich_with_fundamentals(rec, edgar=cast(EdgarClient, _Edgar()), price_bars=[],
                                    reference_date=REF).fundamentals


@pytest.mark.parametrize("sic", ["6021", "6141", "6311"])
def test_a_bank_lender_or_insurer_carries_no_net_debt_leverage(sic: str) -> None:
    """The record every page reads: both ratios UNKNOWN, naming why — on the same filing a
    non-financial reads its ratios from."""
    f = _enriched(sic)
    for field in (f.net_leverage, f.net_debt_to_ocf):
        assert not field.is_known and "not a leverage measure" in (field.note or ""), sic


@pytest.mark.parametrize("sic", ["6411", "6282", "7372", None])
def test_brokers_asset_managers_and_operating_companies_keep_it(sic: str | None) -> None:
    """NEGATIVE: an insurance broker (64), an asset manager (62), software and a missing SIC all
    keep the snapshot's ratios exactly."""
    f = _enriched(sic)
    s = _snap()
    assert f.net_leverage == s.net_leverage and f.net_debt_to_ocf == s.net_debt_to_ocf
    assert f.net_debt_to_ocf.is_known


def test_route_a_refuses_a_lenders_forward_leverage() -> None:
    """`_adjusted_facts` reads the snapshot's net debt beside a company's adjusted-EBITDA guide —
    a fintech lender can give one. A lender (SIC 6141) gets the reason, not a ratio over the
    debt that funds its loan book. NEGATIVE: no SIC, the same inputs compute."""
    import typing

    from tests.test_dossier import _facts as eps_facts
    from tests.test_dossier import _min_record, _StubEdgar
    from vinci.dossier import mechanical as dm
    from vinci.dossier import schemas as ds

    rg = ds.Sourced.present(
        "Adjusted EBITDA of $380 million to $385 million; Adjusted EPS of $1.19 to $1.25",
        source_ref="EDGAR 8-K X Ex-99.1")
    edgar = _StubEdgar(eps_facts([(2024, 0.85)], shares=151_906_653), net_debt=1_008_723_000.0)
    rec = _min_record(pe=5.5, price=4.71)
    lender = rec.model_copy(update={"identity": rec.identity.model_copy(update={"sic": "6141"})})
    from datetime import date
    _, ev, lev = dm._adjusted_facts(lender, typing.cast(EdgarClient, edgar), rg, date(2026, 8, 10))
    assert lev.value is None and "not a leverage measure" in (lev.note or "")
    assert ev.value is None and "not a leverage measure" in (ev.note or "")
    _, ev2, lev2 = dm._adjusted_facts(rec, typing.cast(EdgarClient, edgar), rg, date(2026, 8, 10))
    assert "~2.6x fwd-adj" in (lev2.value or "") and "~4.5x" in (ev2.value or "")


# --- THE FIXTURES CANNOT DRIFT FROM THE CODE ---------------------------------------------------

def test_every_tag_the_builder_requests_is_frozen_in_the_fixtures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Instrumented, not transcribed: every tag `net_debt` asks for over the whole fixture corpus
    is in `READ_TAGS`, and `READ_TAGS` is inside the dossier fixtures' `FIXTURE_TAGS`. A tag the
    code reads and the fixture drops reads as absent offline — a refusal or a reading the suite
    never sees (LUMN's current debt-and-lease line was missing exactly so)."""
    import importlib.util

    asked: set[str] = set()
    real = nd.points_for_tag

    def spy(facts: dict[str, Any], tag: str, *, concept: str = "") -> Any:
        asked.add(tag)
        return real(facts, tag, concept=concept)

    monkeypatch.setattr(nd, "points_for_tag", spy)
    real_extract = nd.extract_points

    def spy_extract(facts: dict[str, Any], concept: str) -> Any:
        asked.update(concepts.CONCEPT_ALIASES[concept])
        return real_extract(facts, concept)

    monkeypatch.setattr(nd, "extract_points", spy_extract)
    for p in [*FACTS.glob("*.json"), *FROZEN.glob("*.json"), *SHAPES.glob("*.json")]:
        nd.net_debt(json.loads(p.read_text()))
    asked |= set(nd._DEBT_WITNESS_TAGS) | {nd._FILER_TOTAL_DEBT}  # read raw by `_unread_debt`
    assert asked <= nd.READ_TAGS, sorted(asked - nd.READ_TAGS)
    spec = importlib.util.spec_from_file_location(
        "bcf", ROOT / "scripts" / "build_companyfacts_fixture.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert nd.READ_TAGS <= mod.FIXTURE_TAGS, sorted(nd.READ_TAGS - mod.FIXTURE_TAGS)


def test_a_refused_snapshot_says_so_on_the_ratio() -> None:
    """The ratios name the SAME reason as the net debt: a refused reading never reads as an absent
    one ("debt/cash not in XBRL")."""
    snap = compute_fundamental_snapshot("x", _facts("RYZ"))
    assert "under-captured" in (snap.net_leverage.note or "")
    absent = compute_fundamental_snapshot("x", {"facts": {"us-gaap": {}}})
    assert absent.net_leverage.note == "no net-debt — debt/cash not in XBRL"


# --- code review of #749 -------------------------------------------------------------------------

def test_a_current_debt_total_that_carries_finance_leases_does_not_count_them_twice() -> None:
    """GPK's `DebtCurrent` ($552M) is its current maturities ($533M) + borrowings ($12M) + its
    current finance leases ($7M) — and finance leases are added once, as finance leases. The
    borrowings read are $12M, not $19M. NEGATIVE: the same filing without the current finance-lease
    tag has nothing to strip, so the excess is all borrowings — the rule is what removes the $7M."""
    facts = _facts("GPK")
    r = _read("GPK")
    assert r.borrowings is not None and r.borrowings.value / M == pytest.approx(5115 + 533 + 12,
                                                                                abs=0.5)
    stripped = {**facts, "facts": {ns: {t: v for t, v in node.items()
                                        if t != "FinanceLeaseLiabilityCurrent"}
                                   for ns, node in facts["facts"].items()}}
    b2 = nd._borrowings(stripped, r.at)
    assert b2 is not None and (b2.value - r.borrowings.value) / M == pytest.approx(7.0, abs=0.5)


def test_every_leg_is_read_in_dollars() -> None:
    """LPL files in won and HSAI in yuan, with dollar convenience figures beside them. Cash was
    read in ANY unit while debt is read in dollars, so LPL netted dollar debt against won cash
    (3.26 trillion "dollars"). Every point the builder reads, on every fixture, is now USD."""
    for p in [*FACTS.glob("*.json"), *FROZEN.glob("*.json"), *SHAPES.glob("*.json")]:
        r = nd.net_debt(json.loads(p.read_text()))
        if r is None:
            continue
        pts = [r.cash, *(r.borrowings.read if r.borrowings else ()), *r.finance_lease_points,
               *r.operating_lease_points, *([r.securities] if r.securities else [])]
        assert all(q.unit == "USD" for q in pts), (p.stem, {q.unit for q in pts})
    lpl = _read("LPL")
    assert lpl.cash.unit == "USD" and lpl.value(nd.Basis.LEVERAGE) is not None
    assert abs(lpl.value(nd.Basis.LEVERAGE) or 0) / M < 10_000, "a won figure read as dollars"


def test_every_snapshot_consumer_applies_the_sector_rule() -> None:
    """The bank/lender/insurer rule lives at the consumers of `fundamental_snapshot`, so a NEW
    consumer must apply it too: every function in `vinci/` that calls it also calls
    `not_applicable` — a third reader cannot print a bank's "net debt" by forgetting."""
    import ast

    callers: list[str] = []
    for path in (ROOT / "vinci").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            calls = {c.func.attr if isinstance(c.func, ast.Attribute) else getattr(c.func, "id", "")
                     for c in ast.walk(fn) if isinstance(c, ast.Call)}
            if "fundamental_snapshot" in calls and fn.name != "fundamental_snapshot":
                callers.append(f"{path.relative_to(ROOT)}:{fn.name}")
                assert "not_applicable" in calls, f"{path.name}:{fn.name} skips the sector rule"
    assert len(callers) >= 2, f"the scan found {callers} — near-vacuous"

