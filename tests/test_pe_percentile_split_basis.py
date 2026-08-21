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

from vinci.edgar.concepts import extract_points
from vinci.schemas.envelope import CoverageStatus
from vinci.screens.assemble import (
    G3_REASONS,
    G3_SPLIT_BASIS,
    pe_current_and_percentile,
    share_basis_change,
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
SPLIT_NAMES = {"NFLX"}


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


def test_the_percentile_is_refused_and_the_pe_itself_survives() -> None:
    """THE BEHAVIOUR THAT MATTERS. Refusing the whole block would delete a sound P/E; publishing
    the range would keep a number that says the opposite of the truth. Exactly one of the two is
    withdrawn, and it says why."""
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
    assert pctile.coverage_status is not CoverageStatus.PRESENT, (
        f"the percentile survived a share-basis change: {pctile.value} — this is the 0.909 that "
        f"told a reader NFLX sat at the top of its 5-year range")
    assert G3_SPLIT_BASIS in (pctile.note or ""), f"refused without its cause: {pctile.note!r}"
    assert "10" in (pctile.note or ""), "the refusal does not state the factor it found"


def test_the_new_reason_is_in_the_taxonomy() -> None:
    """G3's reasons are counted and labelled elsewhere; a reason emitted but not enumerated is a
    cause with no count, which the existing exhaustiveness pin exists to prevent."""
    assert G3_SPLIT_BASIS in G3_REASONS


#: The trailing-range window the production call site uses, against the committed fleet's as-of.
_WINDOW_START = date(2026, 8, 14) - timedelta(days=1825)


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
