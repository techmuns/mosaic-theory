"""§5.0 row 11 (a) — a filer that moved its statements to IFRS no longer keeps a frozen us-gaap
fiscal year.

`filer_fiscal_year` read only the us-gaap flow concepts, so once a filer's flows moved to
`ifrs-full` its last us-gaap year read as its newest, and `behind_filer` passed that year's
annuals as current. The screen's snapshot served National Steel's operating-income sign for FY2009
and Himax's for FY2017 (`docs/records/2026-11-17-the-monitors-stale-tag-row-is-retired.md`, found;
`docs/records/2026-11-17-an-ifrs-filers-fiscal-year-is-read-from-its-ifrs-statements.md`, fixed).
Its IFRS flow years now date the year (`concepts.IFRS_FLOW_TAGS`); no IFRS figure is ever read as a
value.

Every pin runs on a FROZEN real filer (`tests/fixtures/ifrs_movers/`, README there).
"""
from __future__ import annotations

import json
import pathlib
from datetime import date
from typing import Any

from vinci.dossier.anchor import _dep_amort_point
from vinci.edgar.client import compute_fundamental_snapshot
from vinci.edgar.concepts import (
    ANNUAL_MAX_DAYS,
    ANNUAL_MIN_DAYS,
    FLOW_CONCEPTS,
    IFRS_FLOW_TAGS,
    StaleAnnual,
    behind_filer,
    currency_withheld,
    current_annual,
    extract_points,
    facts_as_of,
    filer_fiscal_year,
    latest_annual,
)
from vinci.facts.screen_replay import screen_inputs
from vinci.schemas.data_record import Identity
from vinci.schemas.envelope import CoverageStatus
from vinci.screens.retention import CandidateRow, read_rows

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "ifrs_movers"


def _facts(ticker: str) -> dict[str, Any]:
    facts: dict[str, Any] = json.loads((FIXTURES / f"{ticker}.json").read_text())
    return facts


def _ifrs_annual_ends(facts: dict[str, Any], tag: str) -> set[date]:
    rows = [r for unit in facts["facts"]["ifrs-full"][tag]["units"].values() for r in unit]
    spans = [(date.fromisoformat(r["start"]), date.fromisoformat(r["end"]))
             for r in rows if r.get("start")]
    return {end for start, end in spans
            if ANNUAL_MIN_DAYS <= (end - start).days <= ANNUAL_MAX_DAYS}


def test_every_flow_concept_has_its_ifrs_lines() -> None:
    """`filer_fiscal_year` reads `IFRS_FLOW_TAGS[concept]` for each of `FLOW_CONCEPTS`: a flow
    concept added without its IFRS lines would raise KeyError in every snapshot, and one dropped
    from `FLOW_CONCEPTS` would silently stop dating the year. The two lists move together."""
    assert tuple(IFRS_FLOW_TAGS) == FLOW_CONCEPTS
    assert all(IFRS_FLOW_TAGS.values())


def test_the_page_fixture_builder_keeps_the_ifrs_lines() -> None:
    """Every annual reader on a page reads `filer_fiscal_year`, so the IFRS lines are tags the
    dossier fixtures' pins read: `scripts/build_companyfacts_fixture.py` must freeze them, or a
    page filer that carries ifrs-full would date an older year offline than in production (none
    does on 2026-11-17)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "bcf", ROOT / "scripts" / "build_companyfacts_fixture.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    wanted = {t for tags in IFRS_FLOW_TAGS.values() for t in tags}
    assert wanted <= mod.FIXTURE_TAGS, sorted(wanted - mod.FIXTURE_TAGS)


# --- POSITIVE: a us-gaap annual years behind the filer's IFRS statements is withheld ------------


def test_himax_fiscal_year_is_its_newest_ifrs_year() -> None:
    """Himax's last us-gaap 20-F is for FY2017; its 20-Fs since are IFRS, to FY2025. Its newest
    fiscal year is FY2025, named by the IFRS tag that dates it."""
    facts = _facts("HIMX")
    gaap = latest_annual(extract_points(facts, "operating_income"))
    assert gaap is not None and gaap.period_end == date(2017, 12, 31), "the shape is in the data"
    assert date(2025, 12, 31) in _ifrs_annual_ends(facts, "ProfitLossFromOperatingActivities")
    fy = filer_fiscal_year(facts)
    assert fy is not None
    assert (fy.period_end, fy.tag) == (date(2025, 12, 31), "ifrs-full:Revenue")


def test_himax_every_us_gaap_annual_is_withheld_naming_the_ifrs_year() -> None:
    """All eight of Himax's flow concepts were served for FY2017 as current. Each is withheld now,
    2,922d behind the IFRS year, and the refusal names both ends."""
    facts = _facts("HIMX")
    point, stale = current_annual(facts, "operating_income")
    assert point is None
    assert stale == StaleAnnual(
        concept="operating_income", tag="OperatingIncomeLoss", period_end=date(2017, 12, 31),
        newer_tag="ifrs-full:Revenue", newer_end=date(2025, 12, 31), lag_days=2922,
        against_filer=True)
    for concept in FLOW_CONCEPTS:
        point, stale = current_annual(facts, concept)
        assert point is None and stale is not None and stale.against_filer, concept
        assert stale.period_end == date(2017, 12, 31), concept


def test_himax_snapshot_withholds_its_fy2017_signs() -> None:
    """End to end through the screen's snapshot: the operating-income and FCF signs, EBITDA and
    EPS were PRESENT for FY2017 and are UNKNOWN, each saying it is more than one fiscal year behind
    the filer's IFRS year — never "no operating_income", which would send a reader looking for a
    missing tag."""
    snap = compute_fundamental_snapshot("0001342338", _facts("HIMX"))
    for field in (snap.op_income_sign, snap.fcf_sign, snap.ebitda_annual,
                  snap.eps_diluted_annual):
        assert field.coverage_status is CoverageStatus.UNKNOWN
        note = field.note or ""
        assert "2017-12-31" in note and "ifrs-full:Revenue to 2025-12-31" in note, note
        assert "more than one fiscal year behind" in note, note


def test_national_steels_committed_screen_row_no_longer_serves_fy2009() -> None:
    """National Steel's row in screen run 2026-10-16-01 read `op_income_sign` +1 and `fcf_sign` −1
    as filed 2010-06-01: FY2009, beside IFRS 20-Fs to FY2024. Replayed through the screen's own
    code (`screen_inputs`) at the run's cut and close, both are UNKNOWN naming the IFRS year. Its
    IFRS statements are in BRL: the year is dated by their PERIOD, and no BRL figure is read."""
    (row,) = [r for r in read_rows("2026-10-16-01", ROOT / "data" / "snapshots")
              if isinstance(r, CandidateRow) and r.ticker == "SID"]
    last = row.gate_inputs["last"]
    assert last.value is not None and last.as_of == date(2026, 10, 16)
    facts = _facts("SID")
    fy = filer_fiscal_year(facts_as_of(facts, last.as_of))
    assert fy is not None and (fy.period_end, fy.tag, fy.unit) == (
        date(2024, 12, 31), "ifrs-full:Revenue", "BRL")
    # the run's candidate record's identity, as committed with the run (2026-10-16)
    identity = Identity(internal_id="SEC-0001049659-SID", issuer_id="ISS-0001049659",
                        cik="0001049659", ticker="SID", mic="XNYS", exchange="NYSE",
                        eod_symbol="SID", name="NATIONAL STEEL CO", sic="3310")
    got = screen_inputs(identity, facts, cut=last.as_of, close=float(last.value),
                        reference_date=row.reference_date)
    for key in ("fundamentals.op_income_sign", "fundamentals.fcf_sign"):
        field = got[key]
        assert field["coverage_status"] == "unknown" and field["value"] is None, key
        assert "2009-12-31" in field["note"] and "ifrs-full:Revenue to 2024-12-31" in field["note"]
    assert got["snapshot.op_income_sign"] == got["fundamentals.op_income_sign"]


def test_a_mover_with_no_current_ifrs_revenue_line_is_dated_by_its_other_lines() -> None:
    """Purple Biotech's last us-gaap year is FY2021; its IFRS 20-Fs run to FY2025, but its IFRS
    revenue line stops at FY2020. Its year is dated by the other lines (`ProfitLoss` to
    2025-12-31), so its FY2021 net income is withheld — never left current for want of a revenue
    line."""
    facts = _facts("PPBT")
    assert max(_ifrs_annual_ends(facts, "Revenue")) == date(2020, 12, 31)
    fy = filer_fiscal_year(facts)
    assert fy is not None
    assert (fy.period_end, fy.tag) == (date(2025, 12, 31), "ifrs-full:ProfitLoss")
    point, stale = current_annual(facts, "net_income")
    assert point is None
    assert stale == StaleAnnual(
        concept="net_income", tag="ProfitLoss", period_end=date(2021, 12, 31),
        newer_tag="ifrs-full:ProfitLoss", newer_end=date(2025, 12, 31), lag_days=1461,
        against_filer=True)


# --- NEGATIVE: what must still be served ----------------------------------------------------


def test_the_day_before_the_first_ifrs_year_the_last_us_gaap_annual_is_served() -> None:
    """As filed the day before Himax's first IFRS 20-F (2019-03-27), no IFRS fiscal year is past
    its FY2017 us-gaap annuals: its newest fiscal year IS FY2017, and every one of the eight is
    served, as for any filer. The ruling below starts only once an IFRS year past them is filed."""
    facts = facts_as_of(_facts("HIMX"), date(2019, 3, 27))
    fy = filer_fiscal_year(facts)
    assert fy is not None and fy.period_end == date(2017, 12, 31)
    assert not fy.tag.startswith("ifrs-full:")
    for concept in FLOW_CONCEPTS:
        point, stale = current_annual(facts, concept)
        assert stale is None and point is not None, concept
        assert point.period_end == date(2017, 12, 31), concept
    snap = compute_fundamental_snapshot("0001342338", facts)
    assert snap.op_income_sign.coverage_status is CoverageStatus.PRESENT


# --- THE FIRST IFRS YEAR (operator ruling 2026-11-18, "Withhold it (Recommended)") -------------


def test_the_first_ifrs_year_withholds_the_last_us_gaap_annual() -> None:
    """OPERATOR RULING 2026-11-18 ("Withhold it (Recommended)"): in the year a filer first reports
    under IFRS, its last us-gaap annual is withheld, reading UNKNOWN, once an IFRS fiscal year past
    it is filed. It is no longer served as current.

    Himax's first IFRS 20-F, filed 2019-03-28, is for FY2018 (`ifrs-full:Revenue`). As filed that
    day its FY2017 us-gaap annuals are one fiscal year behind it (365d), and round 0 of #1112 still
    served all eight, the operating-income sign among them. Each is withheld now, naming both years;
    one filer year behind a us-gaap year still stays (`test_annual_pairs.py`). Its FY2018
    `ProfitLossFromOperatingActivities` was first filed 2020-03-25, so it is the FILER's IFRS year
    that withholds the operating income, not that concept's own IFRS line."""
    facts = facts_as_of(_facts("HIMX"), date(2019, 3, 28))
    assert "ProfitLossFromOperatingActivities" not in facts["facts"]["ifrs-full"], \
        "the operating-income line is not in the first IFRS 20-F"
    fy = filer_fiscal_year(facts)
    assert fy is not None and (fy.period_end, fy.tag) == (date(2018, 12, 31), "ifrs-full:Revenue")
    point, stale = current_annual(facts, "operating_income")
    assert point is None
    assert stale == StaleAnnual(
        concept="operating_income", tag="OperatingIncomeLoss", period_end=date(2017, 12, 31),
        newer_tag="ifrs-full:Revenue", newer_end=date(2018, 12, 31), lag_days=365,
        against_filer=True)
    assert "reports under IFRS" in stale.note and "more than one" not in stale.note, stale.note
    for concept in FLOW_CONCEPTS:
        point, stale = current_annual(facts, concept)
        assert point is None and stale is not None and stale.against_filer, concept
        assert (stale.period_end, stale.lag_days) == (date(2017, 12, 31), 365), concept
    snap = compute_fundamental_snapshot("0001342338", facts)
    for field in (snap.op_income_sign, snap.fcf_sign, snap.ebitda_annual,
                  snap.eps_diluted_annual):
        assert field.coverage_status is CoverageStatus.UNKNOWN
        note = field.note or ""
        assert "2017-12-31" in note and "ifrs-full:Revenue to 2018-12-31" in note, note
        assert "reports under IFRS" in note and "more than one" not in note, note
    # the anchor's D&A, which must be the filer's newest year, is refused as it was at round 0
    refused = _dep_amort_point(facts)
    assert isinstance(refused, str) and "ifrs-full:Revenue to 2018-12-31" in refused, refused
    # as filed by the next 20-F (FY2019) it is two years behind, the rule since round 0
    point, stale = current_annual(facts_as_of(_facts("HIMX"), date(2020, 3, 25)),
                                  "operating_income")
    assert point is None and stale is not None and stale.lag_days == 730
    assert "more than one fiscal year behind" in stale.note


# --- A US-GAAP TAG TYING THE IFRS YEAR (review of f1adee46, should-fix 1) -----------------------


def _eu_profit_loss(end: date) -> Any:
    """enCore's us-gaap `ProfitLoss` annual to ``end``, as its 40-F of 2023-04-28 tagged it."""
    facts = facts_as_of(_facts("EU"), date(2023, 4, 28))
    (point,) = [p for p in extract_points(facts, "net_income")
                if p.is_annual and p.period_end == end and p.tag == "ProfitLoss"]
    return point


def test_a_us_gaap_tag_tying_the_ifrs_year_does_not_hide_it() -> None:
    """A REAL TIE. enCore's 40-F filed 2023-04-28 (IFRS, FY2022) also tags us-gaap `ProfitLoss`
    for FY2022 and FY2021 — the IFRS figures with their sign flipped. The us-gaap FY2022 ends the
    day the IFRS year does and wins the tie, so it names the filer's year; round 1 then judged
    the year as us-gaap and let a figure one IFRS year behind stand (700d, not 350d). The IFRS
    year is kept beside the winner, and the ruling is judged against it: the FY2021 figure is
    withheld, 365d behind it. 21 census days in 9 ifrs-full filers tie so (review of f1adee46)."""
    facts = facts_as_of(_facts("EU"), date(2023, 4, 28))
    fy = filer_fiscal_year(facts)
    assert fy is not None and (fy.period_end, fy.tag) == (date(2022, 12, 31), "ProfitLoss"), \
        "the tie is in the data: a us-gaap tag names the year"
    assert (fy.ifrs_end, fy.ifrs_tag) == (
        date(2022, 12, 31), "ifrs-full:ProfitLossFromOperatingActivities")
    stale = behind_filer(_eu_profit_loss(date(2021, 12, 31)), fy)
    assert stale == StaleAnnual(
        concept="net_income", tag="ProfitLoss", period_end=date(2021, 12, 31),
        newer_tag="ifrs-full:ProfitLossFromOperatingActivities", newer_end=date(2022, 12, 31),
        lag_days=365, against_filer=True)
    # end to end, on Himax's first IFRS 20-F with a us-gaap `ProfitLoss` row copied from its own
    # IFRS FY2018 row, so that a us-gaap tag ties the IFRS year as enCore's does: the FY2017
    # operating-income sign is still withheld, never PRESENT
    himax = facts_as_of(_facts("HIMX"), date(2019, 3, 28))
    (row,) = [r for r in himax["facts"]["ifrs-full"]["ProfitLoss"]["units"]["USD"]
              if (r.get("start"), r["end"]) == ("2018-01-01", "2018-12-31")]
    himax["facts"]["us-gaap"].setdefault("ProfitLoss", {"units": {"USD": []}})
    himax["facts"]["us-gaap"]["ProfitLoss"]["units"].setdefault("USD", []).append(dict(row))
    tied = filer_fiscal_year(himax)
    assert tied is not None and (tied.tag, tied.ifrs_end) == ("ProfitLoss", date(2018, 12, 31))
    sign = compute_fundamental_snapshot("0001342338", himax).op_income_sign
    assert sign.coverage_status is CoverageStatus.UNKNOWN, sign
    assert "ifrs-full:Revenue to 2018-12-31" in (sign.note or ""), sign.note


def test_the_tying_figure_itself_is_not_behind_the_ifrs_year() -> None:
    """The negative beside it: enCore's us-gaap FY2022 `ProfitLoss` ends the day the IFRS year
    does, 0d behind it, so the ruling does not withhold it. (That it is served, with its sign
    flipped against the IFRS figure, is FOUND NOT FIXED in the record; no production reader
    serves `net_income` through `current_annual`.)"""
    fy = filer_fiscal_year(facts_as_of(_facts("EU"), date(2023, 4, 28)))
    assert behind_filer(_eu_profit_loss(date(2022, 12, 31)), fy) is None


# --- THE FISCAL YEAR IS A DATE, NEVER A FIGURE (review of #1112, item 3) --------------------------


def test_the_fiscal_year_carries_no_figure() -> None:
    """The point that dates National Steel's year is a BRL revenue. `filer_fiscal_year` returns
    its period and where it was read, and NO value: a reader can never take it for revenue, in
    dollars or in reais."""
    fy = filer_fiscal_year(_facts("SID"))
    assert fy is not None and (fy.period_end, fy.tag, fy.unit) == (
        date(2024, 12, 31), "ifrs-full:Revenue", "BRL")
    assert not hasattr(fy, "value")


def test_a_us_gaap_year_in_another_currency_dates_the_year() -> None:
    """Canopy Growth filed IFRS 40-Fs in CAD to FY2019 and US GAAP 10-Ks in CAD since. Round 0 of
    #1112 dated its us-gaap half in dollars only and its IFRS half in every currency, so its
    newest fiscal year read as `ifrs-full:Revenue` to 2019-03-31, seven years old. Both halves
    read every unit for the DATE: its year is its FY2026 10-K. Nothing it serves moves: its
    figures are CAD, and the snapshot withholds every one by currency (FPI1a)."""
    facts = _facts("CGC")
    fy = filer_fiscal_year(facts)
    assert fy is not None and (fy.period_end, fy.unit, fy.form) == (
        date(2026, 3, 31), "CAD", "10-K")
    assert not fy.tag.startswith("ifrs-full:")
    snap = compute_fundamental_snapshot("0001737927", facts)
    assert snap.op_income_sign.coverage_status is CoverageStatus.UNKNOWN
    assert snap.op_income_sign.note == currency_withheld("CAD")


def test_an_ifrs_half_year_does_not_date_the_fiscal_year() -> None:
    """Amber International's newest annual is its us-gaap FY2024 (20-F filed 2025-06-12); its 6-K
    of 2025-09-10 tags the half-year to 2025-06-30 in ifrs-full. A half-year is no fiscal year:
    the filer's newest is still FY2024, and its annuals are served as current. (21 of the 1,078
    cached filers carry an IFRS interim period newer than their newest IFRS annual.)"""
    facts = _facts("AMBR")
    rows = [r for u in facts["facts"]["ifrs-full"]["ProfitLoss"]["units"].values() for r in u]
    assert {(r["start"], r["end"], r["form"]) for r in rows} >= {
        ("2025-01-01", "2025-06-30", "6-K")}, "the half-year must be in the data"
    fy = filer_fiscal_year(facts)
    assert fy is not None and (fy.period_end, fy.form) == (date(2024, 12, 31), "20-F")
    assert not fy.tag.startswith("ifrs-full:")
    for concept in ("revenue", "operating_income", "operating_cash_flow", "capex"):
        point, stale = current_annual(facts, concept)
        assert stale is None and point is not None, concept
        assert point.period_end == date(2024, 12, 31), concept


def test_ifrs_years_older_than_the_us_gaap_year_move_nothing() -> None:
    """enCore Energy filed 40-Fs under IFRS to FY2023 and 10-Ks under US GAAP since. Its newest
    fiscal year is its us-gaap FY2025, and its current annuals are served."""
    facts = _facts("EU")
    assert max(_ifrs_annual_ends(facts, "ProfitLoss")) == date(2023, 12, 31)
    fy = filer_fiscal_year(facts)
    assert fy is not None and (fy.period_end, fy.tag) == (date(2025, 12, 31), "Revenues")
    for concept in ("revenue", "operating_income", "operating_cash_flow"):
        point, stale = current_annual(facts, concept)
        assert stale is None and point is not None, concept
        assert point.period_end == date(2025, 12, 31), concept
    snap = compute_fundamental_snapshot("0001500881", facts)
    assert snap.op_income_sign.coverage_status is CoverageStatus.PRESENT


def test_a_filer_current_under_ifrs_has_no_figure_invented() -> None:
    """IAMGOLD reports under IFRS, to FY2025, and tags no us-gaap flow. Its fiscal year is now
    dated (FY2025, ifrs-full), and still nothing is read: every annual field says the concept is
    absent, the reading it gave before. An IFRS figure is never served in a us-gaap field."""
    facts = _facts("IAG")
    fy = filer_fiscal_year(facts)
    assert fy is not None and (fy.period_end, fy.tag) == (date(2025, 12, 31), "ifrs-full:Revenue")
    snap = compute_fundamental_snapshot("0001203464", facts)
    assert (snap.op_income_sign.coverage_status, snap.op_income_sign.note) == (
        CoverageStatus.UNKNOWN, "no operating_income")
    assert snap.fcf_sign.note == "no OCF/capex"
    assert snap.ebitda_annual.note == "no operating_income/D&A"
    assert snap.eps_diluted_annual.note == "no diluted EPS"
