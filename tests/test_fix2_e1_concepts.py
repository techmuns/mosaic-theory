"""TeamNostra fix request 2, SEC client, three EDGAR-concept defects (orders 4 and 5).

* RE1-D7 — a same-day 10-K and 10-K/A resolved by ROW ORDER, and no restatement was named.
* RE1-D10 — ONE ALIAS FOR EVERY DATE: the P/E range read every past bar through the EPS alias
  served on its reference date, so bars before a re-tagging filing had no EPS.
* RE1-D15 — segment profit matched namespace PREFIXES as written, so an instance binding the
  us-gaap namespace to another prefix read as a single-segment filer.

The constructed inputs are TeamNostra's own (fix pack 2, `notes/E1_work`: `q13_probe.py`,
`alias_pit_probe.py`, `segment_prefix_probe.py`), cut to what each defect needs; they carry no real
company's figures. The real pins read the committed companyfacts and instance fixtures.
"""
from __future__ import annotations

import copy
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci.edgar import segment_facts as sf
from vinci.edgar.concepts import (
    CONCEPT_ALIASES,
    EVERY,
    REPORTING,
    annual_by_period,
    extract_points,
    facts_as_of,
    filed_at,
    latest_annual,
    latest_instant,
    points_for_tag,
    served_series,
    superseded,
)
from vinci.edgar.net_debt import _at
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import G3_SPLIT_BASIS, pe_current_and_percentile

_FIX = Path(__file__).resolve().parent / "fixtures"


def _row(start: str | None, end: str, val: float, accn: str, filed: str, form: str = "10-K",
         fy: int | None = None) -> dict[str, Any]:
    r: dict[str, Any] = {"end": end, "val": val, "accn": accn, "fy": fy or int(end[:4]),
                         "fp": "FY", "form": form, "filed": filed}
    if start is not None:
        r["start"] = start
    return r


def _blob(tag: str, unit: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"cik": 999999, "facts": {"us-gaap": {tag: {"units": {unit: rows}}}}}


# --- RE1-D7: a same-day 10-K and 10-K/A ----------------------------------------------------------

#: q13_probe's same-day section: the FY2024 10-K states 150,000,000 and the 10-K/A correcting it,
#: re-dated to the 10-K's own day, 90,000,000.
_SAME_DAY = [
    _row("2024-01-01", "2024-12-31", 150_000_000, "0000999999-25-000004", "2025-02-20"),
    _row("2024-01-01", "2024-12-31", 90_000_000, "0000999999-25-000020", "2025-02-20", "10-K/A"),
]


@pytest.mark.parametrize("order", ["as written", "reversed"])
def test_re1_d7_a_same_day_amendment_is_served_whatever_the_row_order(order: str) -> None:
    rows = _SAME_DAY if order == "as written" else list(reversed(_SAME_DAY))
    blob = _blob("OperatingIncomeLoss", "USD", copy.deepcopy(rows))
    pts = extract_points(blob, "operating_income")
    by_period = annual_by_period(pts)[date(2024, 12, 31)]
    assert (by_period.value, by_period.accession, by_period.form) == (
        90_000_000, "0000999999-25-000020", "10-K/A")
    assert latest_annual(pts) == by_period
    old = superseded(blob, by_period)
    assert old is not None and (old.value, old.accession) == (150_000_000, "0000999999-25-000004")
    assert "restating 150,000,000 first filed 2025-02-20 (0000999999-25-000004)" in filed_at(
        by_period, blob)


@pytest.mark.parametrize("order", ["as written", "reversed"])
def test_re1_d7_rost_10q_a_corrects_its_10q_cover_count_the_same_day(order: str) -> None:
    """REAL: ROST's cover count for 2010-11-18 was filed twice on 2010-12-08 — the 10-Q stating
    19,084,540 and the 10-Q/A correcting it to 119,084,540. The committed fixture lists the 10-Q
    first, so row order served the typo; the amendment is served either way now."""
    blob = json.loads((_FIX / "companyfacts" / "ROST.json").read_text())
    node = blob["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]
    if order == "reversed":
        node.reverse()
    pts = [p for p in points_for_tag(blob, "EntityCommonStockSharesOutstanding")
           if p.period_end == date(2010, 11, 18)]
    assert {(p.form, p.value) for p in pts} == {("10-Q", 19_084_540), ("10-Q/A", 119_084_540)}
    served = latest_instant(pts)
    assert served is not None and (served.form, served.value) == ("10-Q/A", 119_084_540)
    old = superseded(blob, served)
    assert old is not None and (old.form, old.value) == ("10-Q", 19_084_540)


@pytest.mark.parametrize("order", ["as written", "reversed"])
def test_re1_d7_net_debt_reads_a_same_day_instant_by_the_filing_served(order: str) -> None:
    rows = [_row(None, "2024-12-31", 500.0, "0000999999-25-000004", "2025-02-20"),
            _row(None, "2024-12-31", 450.0, "0000999999-25-000020", "2025-02-20", "10-K/A")]
    blob = _blob("LongTermDebtNoncurrent", "USD", rows if order == "as written" else rows[::-1])
    got = _at(blob, "LongTermDebtNoncurrent", date(2024, 12, 31))
    assert got is not None and (got.value, got.form) == (450.0, "10-K/A")


@pytest.mark.parametrize("order", ["as written", "reversed"])
def test_re1_d7_two_same_day_originals_resolve_by_accession_and_name_the_other(order: str) -> None:
    """The Tilray shape (two of its 10-Qs filed 2024-10-10 state one period at two values, in the
    SEC cache): no amendment to prefer, so the greater accession is served — never the first row —
    and the other is named. Here on an annual period, which the annual readers serve."""
    rows = [_row("2023-01-01", "2023-12-31", 816_000, "0001437749-24-031040", "2024-10-10"),
            _row("2023-01-01", "2023-12-31", 6_357_000, "0001437749-24-031042", "2024-10-10")]
    blob = _blob("NetIncomeLoss", "USD", rows if order == "as written" else rows[::-1])
    served = annual_by_period(extract_points(blob, "net_income"))[date(2023, 12, 31)]
    assert (served.value, served.accession) == (6_357_000, "0001437749-24-031042")
    old = superseded(blob, served)
    assert old is not None and old.value == 816_000


def test_re1_d7_negative_a_later_day_still_beats_a_same_period_amendment() -> None:
    """The precedence only breaks a same-DAY tie: an amendment filed earlier loses to the later
    day's filing of the period, as before."""
    rows = [_row("2024-01-01", "2024-12-31", 90_000_000, "0000999999-25-000020", "2025-06-10",
                 "10-K/A"),
            _row("2024-01-01", "2024-12-31", 95_000_000, "0000999999-26-000003", "2026-02-19",
                 fy=2025)]
    for order in (rows, rows[::-1]):
        pts = extract_points(_blob("OperatingIncomeLoss", "USD", copy.deepcopy(order)),
                             "operating_income")
        got = annual_by_period(pts)[date(2024, 12, 31)]
        assert (got.value, got.filed) == (95_000_000, date(2026, 2, 19))


def test_re1_d7_negative_a_same_day_same_figure_names_no_restatement() -> None:
    rows = [_row("2024-01-01", "2024-12-31", 150_000_000, "0000999999-25-000004", "2025-02-20"),
            _row("2024-01-01", "2024-12-31", 150_000_000, "0000999999-25-000020", "2025-02-20",
                 "10-K/A")]
    blob = _blob("OperatingIncomeLoss", "USD", rows)
    served = latest_annual(extract_points(blob, "operating_income"))
    assert served is not None and served.form == "10-K/A"
    assert superseded(blob, served) is None
    assert "restating" not in filed_at(served, blob)


def test_re1_d7_a_periodic_report_is_served_over_a_same_day_proxy() -> None:
    rows = [_row("2024-01-01", "2024-12-31", 10.0, "0000999999-25-000099", "2025-02-20",
                 "DEF 14A"),
            _row("2024-01-01", "2024-12-31", 12.0, "0000999999-25-000004", "2025-02-20")]
    for order in (rows, rows[::-1]):
        got = latest_annual(extract_points(_blob("NetIncomeLoss", "USD", list(order)),
                                           "net_income"))
        assert got is not None and (got.form, got.value) == ("10-K", 12.0)


@pytest.mark.parametrize("order", ["as written", "reversed"])
def test_re1_d7_an_amendment_outranks_only_the_form_it_amends(order: str) -> None:
    """REAL (Codex, round 1): GPK's 2011-12-31 long-term debt was filed twice on 2012-07-26, by a
    10-K/A (…-000042, 2,349,700,000) and a 10-Q (…-000044, 2,358,500,000). The 10-K/A amends
    the 10-K, not the 10-Q, so the two are different reports and the greater accession is served."""
    blob = json.loads((_FIX / "net_debt_shapes" / "GPK.json").read_text())
    rows = blob["facts"]["us-gaap"]["LongTermDebt"]["units"]["USD"]
    if order == "reversed":
        rows.reverse()
    cut = facts_as_of(blob, date(2012, 8, 1))
    got = _at(cut, "LongTermDebt", date(2011, 12, 31))
    assert got is not None and (got.form, got.value) == ("10-Q", 2_358_500_000)
    served = latest_instant([p for p in points_for_tag(cut, "LongTermDebt")
                             if p.period_end == date(2011, 12, 31)])
    assert served is not None and served.accession == "0001408075-12-000044"


def test_re1_d7_three_same_day_filings_of_two_forms_resolve_whatever_the_order() -> None:
    """A 10-K, its 10-K/A and a 10-Q on one day: the 10-K/A wins its own form, then the greater
    accession across forms (here the 10-Q's). No pairwise key can say this without a cycle."""
    rows = [_row(None, "2024-12-31", 1.0, "0000999999-25-000005", "2025-02-20"),
            _row(None, "2024-12-31", 2.0, "0000999999-25-000003", "2025-02-20", "10-K/A"),
            _row(None, "2024-12-31", 3.0, "0000999999-25-000004", "2025-02-20", "10-Q")]
    import itertools
    for perm in itertools.permutations(rows):
        blob = _blob("LongTermDebtNoncurrent", "USD", [dict(r) for r in perm])
        got = _at(blob, "LongTermDebtNoncurrent", date(2024, 12, 31))
        assert got is not None and (got.form, got.value) == ("10-Q", 3.0), perm


# --- RE1-D10: one alias for every date -----------------------------------------------------------

def _eps_row(end: str, val: float, accn: str, filed: str, fy: int | None = None) -> dict[str, Any]:
    return _row(f"{end[:4]}-01-01", end, val, accn, filed, fy=fy)


#: alias_pit_probe's filer: diluted EPS under `EarningsPerShareDiluted` in its FY2023 and FY2024
#: 10-Ks; its FY2025 10-K (filed 2026-02-19) moves to the continuing-operations alias and re-tags
#: FY2023-FY2024 under it.
_RETAG: dict[str, Any] = {"cik": 999999, "facts": {"us-gaap": {
    "EarningsPerShareDiluted": {"units": {"USD/shares": [
        _eps_row("2023-12-31", 1.00, "0000999999-24-000005", "2024-02-20"),
        _eps_row("2023-12-31", 1.00, "0000999999-25-000004", "2025-02-20", fy=2024),
        _eps_row("2024-12-31", 1.50, "0000999999-25-000004", "2025-02-20")]}},
    "IncomeLossFromContinuingOperationsPerDilutedShare": {"units": {"USD/shares": [
        _eps_row("2023-12-31", 0.95, "0000999999-26-000003", "2026-02-19", fy=2025),
        _eps_row("2024-12-31", 1.40, "0000999999-26-000003", "2026-02-19", fy=2025),
        _eps_row("2025-12-31", 1.70, "0000999999-26-000003", "2026-02-19", fy=2025)]}}}}}


def _weekly(start: date, end: date, close: float = 30.0) -> list[PriceBar]:
    return [PriceBar(internal_id="X", bar_date=d, open=close, high=close, low=close, close=close,
                     volume=1, source="constructed")
            for d in (start + timedelta(days=7 * i) for i in range((end - start).days // 7 + 1))]


def test_re1_d10_each_day_is_served_the_alias_of_its_day() -> None:
    ref = date(2026, 3, 1)
    series = served_series(facts_as_of(_RETAG, ref), "eps_diluted", as_of=ref)
    before = [p for p in series.on(date(2025, 6, 30)) if p.is_annual]
    assert {p.tag for p in before} == {"EarningsPerShareDiluted"}
    assert max(before, key=lambda p: p.period_end).value == 1.50
    after = series.on(ref)
    assert {p.tag for p in after} == {"IncomeLossFromContinuingOperationsPerDilutedShare"}
    # on the reference date the series IS extract_points' own
    assert after == extract_points(facts_as_of(_RETAG, ref), "eps_diluted", as_of=ref)
    assert series.on(date(2024, 2, 19)) == []


def test_re1_d10_the_pe_range_reads_bars_before_a_retag() -> None:
    ref = date(2026, 3, 1)
    cut = facts_as_of(_RETAG, ref)
    series = served_series(cut, "eps_diluted", as_of=ref)
    annual = [p for p in series.on(ref) if p.is_annual]
    bars = _weekly(date(2024, 3, 1), ref)
    pe, pct = pe_current_and_percentile(bars, annual, reference_date=ref, min_points=5,
                                        history=series)
    assert pe.value == pytest.approx(30.0 / 1.70)
    assert pct.value is not None and pct.note is not None
    assert pct.note.startswith(f"{len(bars)} P/E observations")
    assert ("EPS read under EarningsPerShareDiluted (2024-03-01..2026-02-13), then "
            "IncomeLossFromContinuingOperationsPerDilutedShare (2026-02-20..2026-02-27)"
            ) in pct.note
    # the same call without the series is the defect: only the two bars after the re-tag
    _, short = pe_current_and_percentile(bars, annual, reference_date=ref, min_points=5)
    assert short.value is None and "only 2 P/E points" in (short.note or "")


def test_re1_d10_negative_a_filer_that_never_retags_reads_identically() -> None:
    """REAL: NFLX's diluted EPS alias never moves (0 of the 31 committed fixtures move theirs), so
    the range read with the series is the range read without it, value and note alike."""
    blob = json.loads((_FIX / "companyfacts" / "NFLX.json").read_text())
    ref = date(2025, 6, 30)
    cut = facts_as_of(blob, ref)
    series = served_series(cut, "eps_diluted", currency=REPORTING, as_of=ref)
    annual = [p for p in series.on(ref) if p.is_annual]
    old = [p for p in extract_points(cut, "eps_diluted", currency=REPORTING, as_of=ref)
           if p.is_annual]
    assert annual == old
    bars = _weekly(ref - timedelta(days=1800), ref, close=100.0)
    with_series = pe_current_and_percentile(bars, annual, reference_date=ref, history=series)
    without = pe_current_and_percentile(bars, annual, reference_date=ref)
    assert with_series == without
    assert "EPS read under" not in (with_series[1].note or "")


@pytest.mark.parametrize("ticker", ["MCK", "WOR", "TGT"])
def test_re1_d10_the_series_is_the_walk_on_the_blob_cut_each_day(ticker: str) -> None:
    """REAL: on every day a row of each multi-alias concept was filed, the series equals the walk
    on the blob cut at that day (each of these three fixtures moves its revenue alias 2-3 times).
    Measured on all 31 committed fixtures, 14,167 of 14,167 days agree."""
    blob = json.loads((_FIX / "companyfacts" / f"{ticker}.json").read_text())
    for concept, tags in CONCEPT_ALIASES.items():
        if len(tags) < 2:
            continue
        series = served_series(blob, concept, currency=EVERY)
        if concept == "revenue":
            assert len(series.by_tag()) >= 3, "the fixture's revenue alias moves"
        for d in series.days:
            assert series.on(d) == extract_points(facts_as_of(blob, d), concept, currency=EVERY,
                                                  as_of=d), (concept, d)


def test_re1_d10_an_older_aliases_split_is_checked_and_adjusted() -> None:
    """A guard the series adds: a range that reads an OLDER alias is checked for a share-basis
    change inside that alias too (positive), and one with none is read (negative). The split that
    alias's own filer states (×10, two restated periods agreeing) is ADJUSTED, no longer refused
    (operator, 2026-11-11: "Split-adjust EPS, fund rule") — each bar reading that alias's pre-split
    EPS puts it on the current basis."""
    ref = date(2026, 3, 1)

    def blob(restated: float) -> dict[str, Any]:
        old = [_eps_row("2022-12-31", 10.0, "0000999999-23-000005", "2023-02-20"),
               _eps_row("2023-12-31", 12.0, "0000999999-24-000005", "2024-02-20"),
               _eps_row("2022-12-31", 10.0 / restated, "0000999999-25-000004", "2025-02-20",
                        fy=2024),
               _eps_row("2023-12-31", 12.0 / restated, "0000999999-25-000004", "2025-02-20",
                        fy=2024),
               _eps_row("2024-12-31", 1.50, "0000999999-25-000004", "2025-02-20")]
        new = [_eps_row("2024-12-31", 1.40, "0000999999-26-000003", "2026-02-19", fy=2025),
               _eps_row("2025-12-31", 1.70, "0000999999-26-000003", "2026-02-19", fy=2025)]
        return {"cik": 999999, "facts": {"us-gaap": {
            "EarningsPerShareDiluted": {"units": {"USD/shares": old}},
            "IncomeLossFromContinuingOperationsPerDilutedShare": {"units": {"USD/shares": new}}}}}

    bars = _weekly(date(2022, 3, 1), ref)
    for restated, split_named in ((10.0, True), (1.0, False)):
        cut = facts_as_of(blob(restated), ref)
        series = served_series(cut, "eps_diluted", as_of=ref)
        annual = [p for p in series.on(ref) if p.is_annual]
        _, pct = pe_current_and_percentile(bars, annual, reference_date=ref, min_points=5,
                                           history=series)
        assert pct.value is not None and G3_SPLIT_BASIS not in (pct.note or ""), restated
        assert ("EPS filed before 2025-02-20 put on the current share basis by the filer's own "
                "~10x restatement" in (pct.note or "")) is split_named, (restated, pct.note)


_OLD, _NEW = "EarningsPerShareDiluted", "IncomeLossFromContinuingOperationsPerDilutedShare"


def _pct_of(blob: dict[str, Any], ref: date) -> tuple[float | None, str]:
    series = served_series(facts_as_of(blob, ref), "eps_diluted", as_of=ref)
    annual = [p for p in series.on(ref) if p.is_annual]
    _, pct = pe_current_and_percentile(_weekly(date(2021, 3, 1), ref), annual, reference_date=ref,
                                       min_points=5, history=series)
    return pct.value, pct.note or ""


def test_a_split_one_alias_states_puts_a_retired_aliases_eps_on_the_current_basis() -> None:
    """Codex on #997 (P1): the filer re-tags diluted EPS in its FY2024 10-K, splits 10-for-1 in
    2025, and its FY2025 10-K restates FY2023-FY2024 under the NEW tag only. Bars before the re-tag
    read the RETIRED tag, which never restated: a split kept per alias left its old-basis EPS
    divided into split-adjusted prices, and the range stood PRESENT on the mix. The split is the
    issuer's, so it reaches every alias's EPS filed before the restating filing — the range reads
    exactly what the same filer with every figure already on the current basis reads."""
    ref = date(2026, 3, 1)

    def blob(k: float) -> dict[str, Any]:  # k: the pre-split basis (10, as filed; 1, already new)
        old = [_eps_row("2021-12-31", 0.20 * k, "0000999999-22-000005", "2022-02-20"),
               _eps_row("2022-12-31", 0.22 * k, "0000999999-23-000005", "2023-02-20"),
               _eps_row("2023-12-31", 0.24 * k, "0000999999-24-000005", "2024-02-20")]
        new = [_eps_row("2023-12-31", 0.24 * k, "0000999999-25-000004", "2025-02-20", fy=2024),
               _eps_row("2024-12-31", 0.26 * k, "0000999999-25-000004", "2025-02-20"),
               _eps_row("2023-12-31", 0.24, "0000999999-26-000003", "2026-02-19", fy=2025),
               _eps_row("2024-12-31", 0.26, "0000999999-26-000003", "2026-02-19", fy=2025),
               _eps_row("2025-12-31", 0.30, "0000999999-26-000003", "2026-02-19")]
        return {"cik": 999999, "facts": {"us-gaap": {_OLD: {"units": {"USD/shares": old}},
                                                     _NEW: {"units": {"USD/shares": new}}}}}

    consistent, _ = _pct_of(blob(1.0), ref)
    value, note = _pct_of(blob(10.0), ref)
    assert consistent is not None and value == pytest.approx(consistent), (value, consistent, note)
    assert "EPS filed before 2026-02-19 put on the current share basis" in note, note
    assert _OLD in note and _NEW in note, note  # the range did read both tags


def test_two_splits_stated_in_two_aliases_are_refused_never_chained() -> None:
    """The retired tag states its own 2-for-1 (restated 2023-02-20) and the new tag a 10-for-1
    (restated 2026-02-19). The retired tag's EPS filed before 2023 sits under BOTH, so one factor
    per alias is wrong: two basis changes in one window are refused, across aliases as within
    one."""
    ref = date(2026, 3, 1)
    old = [_eps_row("2019-12-31", 1.0, "0000999999-20-000005", "2020-02-20"),
           _eps_row("2020-12-31", 1.2, "0000999999-21-000005", "2021-02-20"),
           _eps_row("2021-12-31", 1.4, "0000999999-22-000005", "2022-02-20"),
           _eps_row("2020-12-31", 0.6, "0000999999-23-000005", "2023-02-20", fy=2022),
           _eps_row("2021-12-31", 0.7, "0000999999-23-000005", "2023-02-20", fy=2022),
           _eps_row("2022-12-31", 0.8, "0000999999-23-000005", "2023-02-20"),
           _eps_row("2023-12-31", 0.9, "0000999999-24-000005", "2024-02-20")]
    new = [_eps_row("2023-12-31", 0.9, "0000999999-25-000004", "2025-02-20", fy=2024),
           _eps_row("2024-12-31", 1.0, "0000999999-25-000004", "2025-02-20"),
           _eps_row("2023-12-31", 0.09, "0000999999-26-000003", "2026-02-19", fy=2025),
           _eps_row("2024-12-31", 0.10, "0000999999-26-000003", "2026-02-19", fy=2025),
           _eps_row("2025-12-31", 0.12, "0000999999-26-000003", "2026-02-19")]
    value, note = _pct_of({"cik": 999999, "facts": {"us-gaap": {
        _OLD: {"units": {"USD/shares": old}}, _NEW: {"units": {"USD/shares": new}}}}}, ref)
    assert value is None and G3_SPLIT_BASIS in note, (value, note)


def test_one_split_restated_under_both_tags_is_one_split() -> None:
    """Negative pin for the refusal above: a filer tagging both measures restates both in its
    restating 10-K — the retired tag at ×9.98 by rounding, the new at ×10.0. The retired tag's
    restated rows arrive after the walk has left it, so the range reads ONE split — adjusted, not
    refused as two."""
    ref = date(2026, 3, 1)
    old = [_eps_row("2022-12-31", 2.2, "0000999999-23-000005", "2023-02-20"),
           _eps_row("2023-12-31", 2.4, "0000999999-24-000005", "2024-02-20"),
           _eps_row("2024-12-31", 2.6, "0000999999-25-000004", "2025-02-20"),
           _eps_row("2023-12-31", 0.241, "0000999999-26-000003", "2026-02-19", fy=2025),
           _eps_row("2024-12-31", 0.26, "0000999999-26-000003", "2026-02-19", fy=2025)]
    new = [_eps_row("2023-12-31", 2.4, "0000999999-25-000004", "2025-02-20", fy=2024),
           _eps_row("2024-12-31", 2.6, "0000999999-25-000004", "2025-02-20"),
           _eps_row("2023-12-31", 0.24, "0000999999-26-000003", "2026-02-19", fy=2025),
           _eps_row("2024-12-31", 0.26, "0000999999-26-000003", "2026-02-19", fy=2025),
           _eps_row("2025-12-31", 0.30, "0000999999-26-000003", "2026-02-19")]
    value, note = _pct_of({"cik": 999999, "facts": {"us-gaap": {
        _OLD: {"units": {"USD/shares": old}}, _NEW: {"units": {"USD/shares": new}}}}}, ref)
    assert value is not None and G3_SPLIT_BASIS not in note, (value, note)
    assert note.count("put on the current share basis") == 1, note


def test_re1_d10_an_alias_the_walk_leaves_and_returns_to_is_read_as_three_runs() -> None:
    """Review round 0: the note gave each tag its first and last bar, so an alias served, left and
    served again read as one span overlapping the other's. Diluted EPS stops after FY2023, the
    continuing-operations alias carries FY2024 (the walk leaves the first, >200 days behind), and
    FY2025 returns to diluted EPS."""
    ref = date(2026, 3, 31)
    blob = {"cik": 999999, "facts": {"us-gaap": {
        "EarningsPerShareDiluted": {"units": {"USD/shares": [
            _eps_row("2023-12-31", 1.00, "0000999999-24-000005", "2024-02-20"),
            _eps_row("2025-12-31", 1.70, "0000999999-26-000003", "2026-02-19")]}},
        "IncomeLossFromContinuingOperationsPerDilutedShare": {"units": {"USD/shares": [
            _eps_row("2024-12-31", 1.40, "0000999999-25-000004", "2025-02-20")]}}}}}
    series = served_series(facts_as_of(blob, ref), "eps_diluted", as_of=ref)
    annual = [p for p in series.on(ref) if p.is_annual]
    _, pct = pe_current_and_percentile(_weekly(date(2024, 3, 1), ref), annual, reference_date=ref,
                                       min_points=5, history=series)
    assert ("EPS read under EarningsPerShareDiluted (2024-03-01..2025-02-14), then "
            "IncomeLossFromContinuingOperationsPerDilutedShare (2025-02-21..2026-02-13), then "
            "EarningsPerShareDiluted (2026-02-20..2026-03-27)") in (pct.note or "")


# --- RE1-D15: namespace prefixes -----------------------------------------------------------------

#: segment_prefix_probe's constructed two-segment instance, its us-gaap namespace bound to {P}.
_INSTANCE = """<?xml version="1.0" encoding="utf-8"?>
<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
  xmlns:xbrldi="http://xbrl.org/2006/xbrldi" xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
  xmlns:dei="http://xbrl.sec.gov/dei/2024" xmlns:{P}="{URI}"
  xmlns:abc="http://constructed.example/20251231">
 <xbrli:context id="FY"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000999999</xbrli:identifier></xbrli:entity>
  <xbrli:period><xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>2025-12-31</xbrli:endDate></xbrli:period></xbrli:context>
 <xbrli:context id="W"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000999999</xbrli:identifier>
  <xbrli:segment><xbrldi:explicitMember dimension="{P}:StatementBusinessSegmentsAxis">abc:WidgetsMember</xbrldi:explicitMember></xbrli:segment></xbrli:entity>
  <xbrli:period><xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>2025-12-31</xbrli:endDate></xbrli:period></xbrli:context>
 <xbrli:context id="G"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000999999</xbrli:identifier>
  <xbrli:segment><xbrldi:explicitMember dimension="{P}:StatementBusinessSegmentsAxis">abc:GadgetsMember</xbrldi:explicitMember></xbrli:segment></xbrli:entity>
  <xbrli:period><xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>2025-12-31</xbrli:endDate></xbrli:period></xbrli:context>
 <xbrli:unit id="usd"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>
 <dei:DocumentPeriodEndDate contextRef="FY">2025-12-31</dei:DocumentPeriodEndDate>
 <{P}:OperatingIncomeLoss contextRef="FY" unitRef="usd" decimals="-6">300000000</{P}:OperatingIncomeLoss>
 <{P}:OperatingIncomeLoss contextRef="W" unitRef="usd" decimals="-6">200000000</{P}:OperatingIncomeLoss>
 <{P}:OperatingIncomeLoss contextRef="G" unitRef="usd" decimals="-6">100000000</{P}:OperatingIncomeLoss>
 <{P}:Revenues contextRef="W" unitRef="usd" decimals="-6">900000000</{P}:Revenues>
 <{P}:Revenues contextRef="G" unitRef="usd" decimals="-6">600000000</{P}:Revenues>
</xbrli:xbrl>
"""  # noqa: E501 — the instance's own lines, verbatim
_GAAP = "http://fasb.org/us-gaap/2024"


def _instance(prefix: str, uri: str = _GAAP) -> str:
    return _INSTANCE.replace("{P}", prefix).replace("{URI}", uri)


@pytest.mark.parametrize("prefix", ["us-gaap", "gaap", "fasb"])
def test_re1_d15_segments_are_read_whatever_prefix_binds_us_gaap(prefix: str) -> None:
    read = sf.parse_instance(_instance(prefix), accession="0000999999-26-000003")
    assert read is not None
    assert read.measure == "us-gaap:OperatingIncomeLoss"
    assert [(f.segment, f.profit, f.revenue) for f in read.figures] == [
        ("Widgets", 200_000_000, 900_000_000), ("Gadgets", 100_000_000, 600_000_000)]
    assert read.consolidated == 300_000_000


def test_re1_d15_negative_the_us_gaap_prefix_bound_elsewhere_is_not_us_gaap() -> None:
    """The prefix is a label: `us-gaap` bound to a filer's own namespace names no us-gaap axis or
    element, so the instance holds no segment context this reader knows (None, as for any filer
    whose segments sit on an axis it does not read)."""
    assert sf.parse_instance(_instance("us-gaap", "http://constructed.example/not-gaap"),
                             accession="0000999999-26-000003") is None


def test_re1_d15_a_prefix_bound_to_two_namespaces_is_refused_not_guessed() -> None:
    text = _instance("gaap").replace(
        '<xbrli:context id="W">',
        '<xbrli:context id="W" xmlns:gaap="http://constructed.example/other">', 1)
    with pytest.raises(sf.SegmentFactsUnavailableError, match="bound to 2 namespaces"):
        sf.parse_instance(text, accession="0000999999-26-000003")


def test_re1_d15_every_committed_instance_binds_the_standard_prefixes() -> None:
    """REAL: the 10 committed segment instances read the same under the URI rule — each binds
    us-gaap, srt and dei to their own names, the shape 9 of 9 cached instances share."""
    for path in sorted((_FIX / "segment_facts").glob("*.xml")):
        text = path.read_text()
        assert 'xmlns:us-gaap="http://fasb.org/us-gaap/' in text, path.name


@pytest.mark.parametrize("order", ["as written", "reversed"])
def test_re1_d7_the_pe_level_reads_a_same_day_eps_amendment_whatever_the_row_order(
        order: str) -> None:
    """The P/E's own EPS pick (`annual_eps_point_as_of`) breaks a same-day tie by the filing
    served too: the 10-K/A's 1.80, never whichever row the response listed first."""
    ref = date(2025, 6, 30)
    rows = [_eps_row("2024-12-31", 2.00, "0000999999-25-000004", "2025-02-20"),
            _eps_row("2024-12-31", 1.80, "0000999999-25-000020", "2025-02-20")]
    rows[1]["form"] = "10-K/A"
    blob = _blob("EarningsPerShareDiluted", "USD/shares", rows if order == "as written"
                 else rows[::-1])
    annual = [p for p in extract_points(blob, "eps_diluted") if p.is_annual]
    pe, _ = pe_current_and_percentile(_weekly(date(2024, 7, 1), ref), annual,
                                      reference_date=ref, min_points=5)
    assert pe.value == pytest.approx(30.0 / 1.80)


def test_re1_d15_a_2009_taxonomy_us_gaap_and_dei_are_still_the_standard_names() -> None:
    """The 2009-2010 taxonomies sit at xbrl.us, not fasb.org / xbrl.sec.gov: bound to their own
    prefixes they are still us-gaap and dei, as they were read before the URI rule."""
    text = _instance("us-gaap", "http://xbrl.us/us-gaap/2009-01-31").replace(
        "http://xbrl.sec.gov/dei/2024", "http://xbrl.us/dei/2009-01-31")
    read = sf.parse_instance(text, accession="0000999999-10-000003")
    assert read is not None and read.measure == "us-gaap:OperatingIncomeLoss"
    assert [f.segment for f in read.figures] == ["Widgets", "Gadgets"]
