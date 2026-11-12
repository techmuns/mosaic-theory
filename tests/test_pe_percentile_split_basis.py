"""The P/E percentile refuses a range built across a share-basis change.

THE DEFECT, FOUND BY REVIEWING A MERGED ARTIFACT. NFLX's committed dossier carried
`pe_percentile_5y = 0.909` — "near the top of its 5-year range", read by a human as expensive.
On one consistent share basis the same figure sits near the bottom.

The cause is that the percentile's two columns disagree after a split. Prices are RETROACTIVELY
split-adjusted by the vendor; annual EPS is point-in-time AS FILED, and a filer restates only the
two or three comparatives its latest 10-K carries. NFLX split 10:1, so FY2020-22 EPS is still
as-filed at ~10x the current basis while the prices beside it are adjusted — every observation in
that stretch divides one basis by the other and lands ~10x too low, dragging the distribution down
and pushing today's multiple to the top of it.

The P/E ITSELF was never wrong: price and current EPS are both current-basis. Only the RANGE is
unbuildable, so only the range is refused.
"""
from __future__ import annotations

import json
import pathlib
from datetime import date, timedelta

import pytest

from vinci.edgar.concepts import ConceptPoint, extract_points
from vinci.schemas.envelope import CoverageStatus
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import (
    G3_REASONS,
    G3_SPLIT_BASIS,
    MAX_EPS_AGE_DAYS,
    pe_current_and_percentile,
    share_basis_change,
    split_restatement,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "companyfacts"

#: Names whose share-basis change is a CONFIRMED corporate action INSIDE THE TRAILING
#: WINDOW — each verified from the FILING,
#: never from the ratio alone, because the detector cannot tell a split from a restatement and the
#: whole point of this set is that a human checked.
#:
#:   NFLX — 10:1 forward (FY2023 12.03 → 1.20, FY2024 19.83 → 1.98).
#: HLF IS NOT HERE, AND THAT IS THE CORRECTION (review of #488). It HAS a confirmed split — 2:1
#: forward, shareholder-approved 2018-04-26, 8-K 0001193125-18-136523, "(5) Effect a two-for-one
#: stock split of the Company's common shares" (73,825,918 for); the companion 8-K
#: 0001157523-18-000984 labels figures "Pre Stock Split"; the filer halved its own history in the
#: 2019-02-19 10-K (FY2016 3.02 → 1.51, FY2017 2.58 → 1.29). **But 2018 is EIGHT YEARS before a
#: window opening 2021-08-15**, so it cannot touch one observation in the trailing range: the full
#: series returns 2.0032 and the WINDOWED series returns None. Adding it here would have ratified
#: the very collateral damage the fleet test below exists to catch — the percentile was withdrawn
#: with a note claiming the split "falls inside the window", which was false. This set means
#: "rescaled INSIDE the window", not "has ever split".
#:
#: The share COUNT series shows nothing either way (99.5M → 103.6M over 2022-2025, smooth) — the
#: split predates it, so checking counts alone concludes "no split" and is wrong for a different
#: reason. Both traps are recorded because both were walked into.
#:
#:   (former entry, kept for its evidence) HLF — 2:1 FORWARD, 8-K 0001193125-18-136523:
#:          "(5) Effect a two-for-one stock split of the Company's common shares" (73,825,918 for).
#:          Its companion 8-K (0001157523-18-000984) labels figures "Pre Stock Split" outright.
#:          The filer restated its own history onto the post-split basis in the 2019-02-19 10-K:
#:          FY2016 3.02 (filed 2017-02 and 2018-02) → 1.51 (filed 2019-02); FY2017 2.58 (2018-02)
#:          → 1.29 (2019-02). Per-share figures HALVE in later filings, which is what a forward
#:          split does to comparatives. Ratio measured 2.0032. The share COUNT series (99.5M →
#:          103.6M over 2022-2025) is smooth and shows nothing — the split predates it, so
#:          checking counts alone would have concluded "no split" and been wrong.
#: Names whose per-share basis was RESCALED INSIDE the window — never "has ever split".
#: GOOGL added 2026-08-28 on the filer's own restatement, the standard this module's first test
#: describes: FY2020 reported 58.61 (2021-02-03, 2022-02-02) then 2.93 (2023-02-03); FY2021
#: reported 112.2 then 5.61. Both exactly 20.0x — the July-2022 20-for-1, restated in the FY2022
#: 10-K, and the detector reads 20.0017 over the windowed points. The percentile is correctly
#: WITHHELD for GOOGL: split-adjusted prices over as-filed EPS would divide one basis by the other.
#: AMZN added 2026-09-18, on the same standard, when its page was first committed: FY2020 reported
#: 41.83 (2021-02-03, again 2022-02-04) then 2.09 (2023-02-03); FY2021 reported 64.81 (2022-02-04)
#: then 3.24 (2023-02-03). Both exactly 20.0x — the June-2022 20-for-1, restated in the FY2022
#: 10-K; the detector reads 20.0087 over the windowed points. Its percentile is correctly WITHHELD.
SPLIT_NAMES = {"NFLX", "GOOGL", "AMZN"}


def _eps(ticker: str) -> list:
    p = FIXTURES / f"{ticker}.json"
    if not p.is_file():
        pytest.skip(f"no committed companyfacts fixture for {ticker}")
    return [q for q in extract_points(json.loads(p.read_text()), "eps_diluted") if q.is_annual]


def test_the_factor_is_read_from_the_filings_not_inferred_from_magnitude() -> None:
    """A magnitude test cannot tell a split from an earnings collapse. THE FILER'S OWN RESTATEMENT
    can: NFLX reports FY2023 as 12.03 (filed 2024-01-26) and 1.20 (filed 2026-01-23), FY2024 as
    19.83 then 1.98 — 10.03x and 10.02x. Two independent periods rescaled by the SAME factor is a
    split, because a split rescales every comparative identically and an accounting revision does
    not. That agreement, not the size, is the evidence."""
    factor = share_basis_change(_eps("NFLX"))
    assert factor is not None, "NFLX's 10:1 split is not detected in its own filing history"
    assert factor == pytest.approx(10.0, rel=0.01), f"factor read as {factor}, expected ~10x"


def test_a_reverse_split_is_caught_too() -> None:
    """REVIEW FINDING on this PR. The first cut divided old/new, catching only a FORWARD split —
    EPS restated DOWN, the NFLX shape — and silently missing a REVERSE split, where the filer
    restates EPS UP by the same factor and the contamination is identical.

    That blind spot pointed straight at the screen's own population: reverse splits are the
    commoner event among $300M-$10B names, and the forward case that motivated the fix is the rarer
    one. Ratio is now taken EITHER WAY, matching the cap reconciliation's "x either way".

    SYNTHETIC, deliberately and narrowly: no committed name has a reverse split, so there is no
    corpus to read it from, and the alternative is leaving the direction untested until a name
    arrives with a wrong percentile. The forward case above is pinned on real filings."""
    from vinci.edgar.concepts import ConceptPoint

    def pt(year: int, filed: date, val: float) -> ConceptPoint:
        return ConceptPoint(
            concept="eps_diluted", tag="EarningsPerShareDiluted", unit="USD/shares", value=val,
            period_start=date(year, 1, 1), period_end=date(year, 12, 31), filed=filed,
            fy=year, fp="FY", form="10-K", accession="x")

    # 1:10 reverse split — the later filing restates each comparative UPWARD by 10x
    reverse = [
        pt(2023, date(2024, 1, 26), 0.50), pt(2023, date(2026, 1, 23), 5.00),
        pt(2024, date(2025, 1, 27), 0.80), pt(2024, date(2026, 1, 23), 8.00),
    ]
    got = share_basis_change(reverse)
    assert got is not None, (
        "a reverse split was not detected — prices are split-adjusted and the older EPS is "
        "as-filed exactly as in the forward case, so the percentile is wrong by the same factor")
    assert got == pytest.approx(10.0, rel=0.01), f"factor read as {got}"


def test_a_name_without_a_restatement_is_left_alone() -> None:
    """The detector must be a NARROW instrument. Fired on ordinary restatement noise it would
    delete a valid percentile from every name that ever revised a figure."""
    assert share_basis_change(_eps("UBER")) is None


def test_a_period_merely_repeated_across_filings_is_not_a_restatement() -> None:
    """WHAT ACTUALLY KEEPS THE OLD PERIODS OUT, measured rather than assumed. Every one of NFLX's
    annual periods appears in two or three successive 10-Ks as a comparative, so "reported by more
    than one filing" describes nearly the whole series and discriminates nothing. FY2018-2022
    repeat ONE value each; only FY2023 and FY2024 carry two distinct ones. The factor floor is what
    separates them.

    Fed only the repeated-but-unchanged periods, the detector must find nothing. Asserted on that
    SUBSET, because the full series returns 10x whatever this branch does — an earlier cut of this
    pin asserted the full series and would have passed with the discrimination removed."""
    pts = _eps("NFLX")
    by_period: dict[date, list] = {}
    for p in pts:
        by_period.setdefault(p.period_end, []).append(p)

    repeated_same = {
        e for e, ps in by_period.items()
        if len({q.filed for q in ps}) > 1 and len({q.value for q in ps}) == 1
    }
    assert len(repeated_same) >= 3, (
        f"only {len(repeated_same)} periods are repeated-but-unchanged — this pin's subject is "
        f"gone; re-read the series before trusting the detector's narrowness")

    assert share_basis_change([p for p in pts if p.period_end in repeated_same]) is None, (
        "a period restated to the SAME value was read as a share-basis change — the detector "
        "would then fire on any filer that simply carries comparatives forward, which is all of "
        "them")


def test_the_percentile_is_split_adjusted_and_reads_where_a_consistent_basis_puts_it() -> None:
    """THE BEHAVIOUR THAT MATTERS, AS RULED 2026-11-11 (operator: "Split-adjust EPS, fund rule").
    Until then the range was refused, because publishing it unadjusted kept the 0.909 that told a
    reader NFLX sat at the top of its 5-year range. Now every EPS filed before the filer's own
    restating 10-K (2026-01-23) is put on the current basis by the filer's ~10.02x, and the range
    reads where a consistent basis puts it — near the bottom, as this pin's docstring once
    predicted. The P/E itself is unchanged."""
    from vinci.schemas.market import PriceBar

    ref = date(2026, 8, 7)
    bars = [
        PriceBar(internal_id="SEC-NFLX", bar_date=ref - timedelta(days=n), open=74.0, high=75.0,
                 low=73.0, close=74.14, volume=1e6, source="t")
        for n in range(0, 1800, 3)
    ]
    pe, pctile = pe_current_and_percentile(bars, _eps("NFLX"), reference_date=ref)

    assert pe.coverage_status is CoverageStatus.PRESENT, (
        "the P/E itself was withdrawn — it was never wrong")
    assert pe.value == pytest.approx(74.14 / 2.53, rel=0.01)
    assert pctile.coverage_status is CoverageStatus.PRESENT and pctile.value is not None
    assert pctile.value < 0.2, (
        f"{pctile.value}: a split-adjusted range must not read near the top — that was the "
        f"0.909 an unadjusted range published")
    note = pctile.note or ""
    assert "put on the current share basis by the filer's own ~10.02x restatement" in note
    assert "EPS filed before 2026-01-23" in note and "(a forward split)" in note


def test_the_new_reason_is_in_the_taxonomy() -> None:
    """G3's reasons are counted and labelled elsewhere; a reason emitted but not enumerated is a
    cause with no count, which the existing exhaustiveness pin exists to prevent."""
    assert G3_SPLIT_BASIS in G3_REASONS


#: The trailing-range window the production call site uses, against the committed fleet's as-of —
#: THE RANGE PLUS THE EPS REACH-BACK (review of #490), because the range's observations are built
#: from `annual_eps_as_of(bar_date)`, which reaches back up to `MAX_EPS_AGE_DAYS` past a period
#: end. Windowing on the range alone drops periods the range actually consumes.
_WINDOW_START = date(2026, 8, 14) - timedelta(days=1825 + MAX_EPS_AGE_DAYS)


def test_only_the_known_split_name_is_affected_on_the_committed_fleet() -> None:
    """COLLATERAL DAMAGE. Every other fleet name keeps its percentile; a detector that fired
    broadly would quietly delete a valuation signal across the book."""
    for f in sorted(FIXTURES.glob("*.json")):
        pts = [p for p in extract_points(json.loads(f.read_text()), "eps_diluted") if p.is_annual]
        if not pts:
            continue
        # WINDOWED, matching the CALL SITE this test guards. The production check restricts to the
        # trailing range (`assemble._pe_percentile`), so a raw full-history call here would assert
        # a different function than the one that withdraws percentiles — and did: it demanded HLF
        # be allowlisted for a split outside the window.
        got = share_basis_change([q for q in pts if q.period_end >= _WINDOW_START])
        if f.stem in SPLIT_NAMES:
            assert got is not None, f"{f.stem}: known split no longer detected"
        else:
            assert got is None, (
                f"{f.stem}: a share-basis change was detected ({got}) where none is known — its "
                f"percentile is about to be withdrawn, so confirm the split before accepting it")


def test_a_split_outside_the_window_does_not_withdraw_the_percentile() -> None:
    """THE CALL SITE, NOT THE DETECTOR (review of #488) — and the pin that was missing.

    `share_basis_change` scans every annual point it is given. The production call passed the FULL
    history while the sentence above it said "inside the window", so a rescaling that predates the
    trailing range refused a percentile it cannot touch.

    HLF is the case: its only basis change is the 2018 2:1 split, EIGHT YEARS before a window
    opening 2021-08-15. Full series → 2.0032; windowed → None. Its committed page carried "a
    share-basis change falls inside the window" as a FALSE claim and deleted a buildable signal.

    THE FLEET TEST ABOVE CANNOT CATCH THIS: it windows the points itself, so it asserts the
    FUNCTION and stays green while the CALL SITE scans everything. Verified — un-windowing the
    call site leaves that test passing and reddens only this one. Same shape as pinning a helper
    while the artifact it feeds goes wrong."""
    from vinci.schemas.market import PriceBar

    ref = date(2026, 8, 14)
    bars = [
        PriceBar(internal_id="SEC-HLF", bar_date=ref - timedelta(days=n), open=12.0, high=12.6,
                 low=11.9, close=12.33, volume=1e6, source="t")
        for n in range(0, 1800, 3)
    ]
    pe, pctile = pe_current_and_percentile(bars, _eps("HLF"), reference_date=ref)
    assert pe.coverage_status is CoverageStatus.PRESENT
    assert pctile.coverage_status is CoverageStatus.PRESENT, (
        f"HLF's percentile was withdrawn for a split outside the window: {pctile.note!r}")
    assert G3_SPLIT_BASIS not in (pctile.note or ""), (
        "the split-basis refusal fired on a rescaling that cannot touch a single observation in "
        "the trailing range")


def test_a_split_at_the_window_edge_is_adjusted_through_the_reach_back() -> None:
    """THE NEGATIVE HALF OF THE WINDOWING, and the boundary the first cut left open (review of
    #490) — adjusted since 2026-11-11 where it was refused.

    Windowing the split check on the RANGE alone is too narrow, because the range does not read
    EPS points dated inside it: each bar reads `annual_eps_as_of(bar_date)`, which reaches back up
    to `MAX_EPS_AGE_DAYS` past a period end. So a rescaling can sit outside the range and still
    contaminate every observation in it.

    THE CASE: a 2:1 forward split whose 10-K (filed 2023-02-15) restates FY2020 and FY2021, under
    a window opening 2021-08-15. Only FY2021 ends inside the range — ONE agreeing period, below
    `_SPLIT_MIN_PERIODS` — so a range-only window returns None and publishes a percentile whose
    first eighteen months divide split-adjusted prices by as-filed EPS (4.40, not 2.20). The
    reach-back window keeps FY2020 too, both factors agree at 2.0, and the refusal fires.

    MUTATION: drop `+ MAX_EPS_AGE_DAYS` from `_split_start` and the split goes unread, so the range
    divides by the as-filed 4.00 and 4.40 and this reddens on the value."""
    from vinci.edgar.concepts import ConceptPoint
    from vinci.schemas.market import PriceBar

    def pt(pe: date, filed: date, val: float) -> ConceptPoint:
        return ConceptPoint(
            concept="eps_diluted", tag="EarningsPerShareDiluted", unit="USD/shares", value=val,
            period_start=pe - timedelta(days=364), period_end=pe, filed=filed,
            fy=pe.year, fp="FY", form="10-K", accession="x")

    ref = date(2026, 8, 14)
    pts = [
        pt(date(2020, 12, 31), date(2021, 2, 15), 4.00),   # as filed — PRE-split basis
        pt(date(2021, 12, 31), date(2022, 2, 15), 4.40),   # as filed — PRE-split basis
        pt(date(2020, 12, 31), date(2023, 2, 15), 2.00),   # restated by the post-split 10-K
        pt(date(2021, 12, 31), date(2023, 2, 15), 2.20),   # restated by the post-split 10-K
        pt(date(2022, 12, 31), date(2023, 2, 15), 2.40),
        pt(date(2023, 12, 31), date(2024, 2, 15), 2.60),
        pt(date(2024, 12, 31), date(2025, 2, 15), 2.80),
        pt(date(2025, 12, 31), date(2026, 2, 15), 3.00),
    ]
    window_start = ref - timedelta(days=1825)
    assert share_basis_change([p for p in pts if p.period_end >= window_start]) is None, (
        "the fixture no longer exercises the boundary — the range-only window must MISS this "
        "split, or the pin proves nothing about the reach-back")

    bars = [PriceBar(internal_id="SEC-X", bar_date=window_start + timedelta(days=n), open=50.0,
                     high=51.0, low=49.0, close=50.0, volume=1e6, source="t")
            for n in range((ref - window_start).days + 1)]
    _pe, pctile = pe_current_and_percentile(bars, pts, reference_date=ref)
    # ON ONE BASIS the price is flat and EPS rises every year, so today's P/E (50 / 3.00) is the
    # lowest in the range: only the bars since FY2025's EPS was filed are at or below it. Divided by
    # the as-filed 4.00 and 4.40 instead, the first eighteen months would read 12.5 and 11.4 — below
    # today's — and the percentile would more than triple.
    in_range = [b for b in bars if ref - timedelta(days=1825) <= b.bar_date <= ref]
    expected = sum(1 for b in in_range if b.bar_date >= date(2026, 2, 15)) / len(in_range)
    assert pctile.coverage_status is CoverageStatus.PRESENT, pctile.note
    assert pctile.value == pytest.approx(expected), (pctile.value, expected)
    assert "EPS filed before 2023-02-15 put on the current share basis" in (pctile.note or "")


def _split_pt(pe: date, filed: date, val: float) -> ConceptPoint:
    return ConceptPoint(
        concept="eps_diluted", tag="EarningsPerShareDiluted", unit="USD/shares", value=val,
        period_start=pe - timedelta(days=364), period_end=pe, filed=filed,
        fy=pe.year, fp="FY", form="10-K", accession="x")


def _flat_bars(ref: date) -> list[PriceBar]:
    return [PriceBar(internal_id="SEC-X", bar_date=ref - timedelta(days=n), open=50.0, high=51.0,
                     low=49.0, close=50.0, volume=1e6, source="t") for n in range(0, 1826)]


#: a 2:1 split restated by the 10-K filed 2023-02-15 (FY2020 4.00 → 2.00, FY2021 4.40 → 2.20)
_ONE_SPLIT = [
    _split_pt(date(2020, 12, 31), date(2021, 2, 15), 4.00),
    _split_pt(date(2021, 12, 31), date(2022, 2, 15), 4.40),
    _split_pt(date(2020, 12, 31), date(2023, 2, 15), 2.00),
    _split_pt(date(2021, 12, 31), date(2023, 2, 15), 2.20),
    _split_pt(date(2022, 12, 31), date(2023, 2, 15), 2.40),
    _split_pt(date(2023, 12, 31), date(2024, 2, 15), 2.60),
]


def test_a_split_the_filings_known_by_the_date_do_not_state_is_still_refused() -> None:
    """NEGATIVE, POINT IN TIME: valued on 2023-01-31, before the restating 10-K was filed, the
    split cannot be read from what was known — and the old rule's check scans every filing it is
    handed — so the range is refused, never adjusted with a factor from the future."""
    ref = date(2023, 1, 31)
    pts = [*_ONE_SPLIT[:2], _split_pt(date(2022, 12, 31), date(2023, 2, 15), 2.40),
           _split_pt(date(2020, 12, 31), date(2023, 2, 15), 2.00),
           _split_pt(date(2021, 12, 31), date(2023, 2, 15), 2.20)]
    assert split_restatement([p for p in pts if p.filed <= ref]) is None
    _pe, pctile = pe_current_and_percentile(_flat_bars(ref), pts, reference_date=ref)
    assert pctile.coverage_status is CoverageStatus.UNKNOWN
    assert G3_SPLIT_BASIS in (pctile.note or ""), pctile.note


def test_two_splits_in_one_window_are_refused_never_chained() -> None:
    """NEGATIVE: a 2:1 restated in 2023 and a 3:1 restated in 2025 inside one window — two basis
    changes, refused rather than chained."""
    ref = date(2026, 8, 14)
    pts = [*_ONE_SPLIT,
           _split_pt(date(2022, 12, 31), date(2025, 2, 15), 0.80),   # 2.40 → 0.80, ×3
           _split_pt(date(2023, 12, 31), date(2025, 2, 15), 0.8667),  # 2.60 → 0.8667, ×3
           _split_pt(date(2024, 12, 31), date(2025, 2, 15), 0.93),
           _split_pt(date(2025, 12, 31), date(2026, 2, 15), 1.00)]
    assert split_restatement([p for p in pts if p.filed <= ref]) is None
    _pe, pctile = pe_current_and_percentile(_flat_bars(ref), pts, reference_date=ref)
    assert pctile.coverage_status is CoverageStatus.UNKNOWN
    assert G3_SPLIT_BASIS in (pctile.note or ""), pctile.note


def test_two_splits_of_the_same_size_are_two_not_one() -> None:
    """NEGATIVE, HLF's shape: two 2:1 splits agree on the factor, so agreement alone groups them
    and would rescale from the earlier restating filing. Restating filings more than a year apart
    are two splits — refused."""
    pts = [_split_pt(date(2009, 12, 31), date(2010, 2, 15), 4.0),
           _split_pt(date(2010, 12, 31), date(2011, 2, 15), 4.4),
           _split_pt(date(2009, 12, 31), date(2012, 2, 15), 2.0),
           _split_pt(date(2010, 12, 31), date(2012, 2, 15), 2.2),
           _split_pt(date(2016, 12, 31), date(2017, 2, 15), 6.0),
           _split_pt(date(2017, 12, 31), date(2018, 2, 15), 6.6),
           _split_pt(date(2016, 12, 31), date(2019, 2, 15), 3.0),
           _split_pt(date(2017, 12, 31), date(2019, 2, 15), 3.3)]
    assert share_basis_change(pts) == pytest.approx(2.0, rel=0.01)
    assert split_restatement(pts) is None
    one = [p for p in pts if p.period_end >= date(2016, 1, 1)]
    got = split_restatement(one)
    assert got is not None and got.restated_from == date(2019, 2, 15)
    assert got.scale == pytest.approx(0.5, rel=0.01)


def test_a_later_revision_of_a_comparative_does_not_date_the_split_late() -> None:
    """The restating filing is the FIRST on the new basis (review): the 2:1 is restated by the
    10-K filed 2023-02-15, and the next 10-K revises the comparatives a few percent (2.00 → 2.10,
    2.20 → 2.31). Dated by agreement with the LAST figure, the split would start 2024-02-15 and
    the 2023-02-15 10-K's own new-basis FY2022 2.40 would be halved again."""
    pts = [*_ONE_SPLIT,
           _split_pt(date(2020, 12, 31), date(2024, 2, 15), 2.10),
           _split_pt(date(2021, 12, 31), date(2024, 2, 15), 2.31)]
    got = split_restatement(pts)
    assert got is not None and got.restated_from == date(2023, 2, 15)


def test_two_splits_restated_by_consecutive_10ks_are_two_not_one() -> None:
    """NEGATIVE (review): FY2023 40 → 4 restated by the 10-K filed 2025-02-01, which itself first
    states FY2024 at 50; the next 10-K restates FY2024 50 → 5. Both ×10, restating filings 365 days
    apart — inside the year a single split allows — but the first restating 10-K states a period on
    the old basis, so these are two splits. One factor from 2025-02-01 would leave FY2024's 50
    unscaled for a year of bars against a current basis of 5. Refused."""
    pts = [_split_pt(date(2023, 12, 31), date(2024, 2, 1), 40.0),
           _split_pt(date(2023, 12, 31), date(2025, 2, 1), 4.0),
           _split_pt(date(2024, 12, 31), date(2025, 2, 1), 50.0),
           _split_pt(date(2024, 12, 31), date(2026, 2, 1), 5.0)]
    assert split_restatement(pts) is None


def test_a_reverse_split_scales_older_eps_up() -> None:
    """A REVERSE split restates EPS UP (1:5: 0.20 → 1.00); older EPS is multiplied, not divided."""
    pts = [_split_pt(date(2021, 12, 31), date(2022, 2, 15), 0.20),
           _split_pt(date(2022, 12, 31), date(2023, 2, 15), 0.30),
           _split_pt(date(2021, 12, 31), date(2024, 2, 15), 1.00),
           _split_pt(date(2022, 12, 31), date(2024, 2, 15), 1.50)]
    got = split_restatement(pts)
    assert got is not None and got.scale == pytest.approx(5.0, rel=0.01)
    assert got.restated_from == date(2024, 2, 15)
