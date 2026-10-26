"""A share count that jumps 10x is a split, and calling it dilution points the label backwards.

THE DEFECT. NFLX's committed page read *"diluting (trailing ~1.7y): 427,458,114 (2024-09-30) →
4,163,939,676 (2026-06-30), +874.1%"* with `qa_flags: []` and `caveats: []`. The filer executed a
10:1 forward split in Nov-2025 and restated its EPS comparatives but never the `dei` cover count, so
those two endpoints are different units. On ONE basis the count FELL ~1.4% across the post-split
window — while the company was buying stock back. The label was not merely overstated; it pointed
the opposite way, on the fund's second-largest quality name.

THE TRAP THIS FILE EXISTS TO PIN, and it was measured rather than reasoned. `share_basis_change`
was already imported into `mechanical.py` and already wired to the P/E path, so "just call the
detector" looks like a one-line fix. Run on the three candidate series for NFLX:

    shares          (`dei:EntityCommonStockSharesOutstanding`)  -> None
    WA diluted      (`WeightedAverageNumberOfDilutedSharesOutstanding`) -> 7.000x   (WRONG)
    annual EPS      (`eps_diluted`)                             -> 10.020x  (the filer's own)

Keyed to the SHARES series — the obvious choice, since that is the series being labelled — the
guard returns None and never fires. Keyed to the weighted-average series it fires with a confidently
wrong factor. Only annual EPS carries the restatement, because a basis change is only visible where
the filer RE-REPORTS a period, and nobody re-files a prior cover count. A guard written without
running all three would have shipped and never fired.

FLEET EXPOSURE, measured across all 15 committed companyfacts fixtures: NFLX is the only name with
a basis change today (every other name: no factor, no jump). So these fixtures carry the cases the
corpus cannot — a reverse split, a break at the window edge, a factor whose jump sits outside the
window — because "fires on the one name that has it" is not evidence a guard generalises.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier.mechanical import _basis_break, _share_count_trend
from vinci.edgar.concepts import extract_points
from vinci.screens.assemble import share_basis_change

REF = date(2026, 7, 29)
# FROZEN at the June-quarter vintage these pins were measured on (the "-1.4%" below): the tracking
# fixture moves with every re-assembly (`tests/fixtures/companyfacts_frozen/README.md`)
NFLX = Path(__file__).resolve().parent / "fixtures" / "companyfacts_frozen" / "NFLX.json"


class _Stub:
    """`_share_count_trend` touches exactly one client method, so a duck type drives it offline."""

    def __init__(self, facts: dict[str, Any]) -> None:
        self.facts = facts

    def companyfacts(self, cik: str) -> dict[str, Any]:
        return self.facts


def _pt(period: str, value: float, filed: str = "2026-01-01") -> Any:
    """A share-count point built from the REAL `ConceptPoint` — every field the model requires,
    none invented. An instant fact (`period_start=None`), which is what a cover-page count is."""
    from vinci.edgar.concepts import ConceptPoint
    return ConceptPoint(
        concept="shares", tag="EntityCommonStockSharesOutstanding", unit="shares", value=value,
        period_start=None, period_end=date.fromisoformat(period), filed=date.fromisoformat(filed),
        fy=None, fp=None, form="10-Q", accession="x")


# ─── the trap: which series actually carries the restatement ─────────────────────────────────

@pytest.mark.skipif(not NFLX.is_file(), reason="no NFLX fixture")
def test_only_the_eps_series_states_the_split_factor() -> None:
    """THE MEASUREMENT THE DESIGN RESTS ON. If this ever inverts, the guard above it is keyed to
    the wrong series and will silently stop firing — so the premise is pinned, not just the
    behaviour it produced."""
    fx = json.loads(NFLX.read_text())
    from vinci.edgar.concepts import points_for_tag
    assert share_basis_change(extract_points(fx, "shares")) is None, (
        "the shares series now carries a restatement — the guard could key on it directly")
    assert share_basis_change(extract_points(fx, "eps_diluted")) == pytest.approx(10.02, abs=0.05)
    # RE-MEASURED 2026-10-16: the 7.0x this series used to return was NFLX's 2015 7-for-1, the
    # first split found — not a wrong number. Read latest change first, it states the 2025
    # 10-for-1 as EPS does; the guard stays keyed on EPS (the per-share figure the filer restates)
    wa = share_basis_change(points_for_tag(fx, "WeightedAverageNumberOfDilutedSharesOutstanding"))
    assert wa == pytest.approx(10.0, abs=0.05), (
        f"the WA series returned {wa} — the latest split, read first, is the 2025 10-for-1")


@pytest.mark.skipif(not NFLX.is_file(), reason="no NFLX fixture")
def test_the_committed_defect_no_longer_renders() -> None:
    """THE CASE THAT STARTED THIS, end to end on the real fixture."""
    out = _share_count_trend(_Stub(json.loads(NFLX.read_text())), "0001065280", REF)
    assert out.value is not None
    assert "+874" not in out.value, f"the cross-basis percentage came back: {out.value}"
    assert "diluting" not in out.value, "still labelled dilution across a split"
    assert "share-basis change" in out.value and "2025-12-31" in out.value
    assert "-1.4%" in out.value, f"the post-split reading is wrong: {out.value}"
    assert "DIFFERENT BASIS" in out.value, "the reader is not told why the earlier half is missing"


# ─── the cases the corpus does not contain ───────────────────────────────────────────────────

def test_a_reverse_split_is_caught_in_the_same_breath_as_a_forward_one() -> None:
    """NOT IN TODAY'S CORPUS, and the likelier event in this fund's band — `share_basis_change`
    returns a DIRECTION-FREE magnitude for exactly that reason, so the share-side scan must be
    symmetric too. A 1-for-10 reverse: the count falls, and an endpoint delta would read −90% as
    a heroic buyback."""
    pts = [_pt("2025-03-31", 300_000_000.0), _pt("2025-06-30", 305_000_000.0),
           _pt("2025-09-30", 30_500_000.0), _pt("2025-12-31", 30_000_000.0)]
    assert _basis_break(pts, 10.0) == 2, "a reverse split was not located"


def test_the_break_is_located_by_the_filers_factor_not_by_bigness() -> None:
    """A guard that fired on any large jump would call a genuine 2x issuance a split. The factor
    comes from the filer's own restatement, and the jump has to MATCH it."""
    pts = [_pt("2025-03-31", 100_000_000.0), _pt("2025-06-30", 200_000_000.0)]  # a real 2x raise
    assert _basis_break(pts, 10.0) is None, "a 2x jump was accepted as a 10x split"
    assert _basis_break(pts, 2.0) == 1, "the matching factor was not located"


def test_an_issuance_before_the_split_does_not_win_on_position() -> None:
    """REVIEW FINDING (P1, #413), and the failure was worse than the bug this module fixes.

    With a ±factor-of-2 tolerance a stated 10x accepted anything from 5x to 20x, and the scan took
    the FIRST match. A 5x dilutive raise preceding a real 10x split therefore won on POSITION, and
    the "post-change" segment still crossed the true break — emitting `+900.0%` inside a sentence
    asserting the basis had been accounted for. A wrong number that reads as checked.

    Fixed twice over and this pins both: the 5x is now outside the 25% tolerance (error 50%), AND
    the scan takes the closest fit rather than the earliest, so it would lose on fit even if the
    window admitted it."""
    pts = [_pt("2024-12-31", 20_000_000.0),
           _pt("2025-03-31", 100_000_000.0),      # 5x dilutive issuance — must NOT be chosen
           _pt("2025-06-30", 101_000_000.0),
           _pt("2025-09-30", 1_010_000_000.0),    # the real 10x split
           _pt("2025-12-31", 1_000_000_000.0)]
    brk = _basis_break(pts, 10.0)
    assert brk == 3, f"selected index {brk} — the 5x issuance won on position again"

    # …and the segment handed to the trend must not itself cross a basis change
    seg = pts[brk:]
    assert all(max(a.value / b.value, b.value / a.value) < 1.5
               for a, b in zip(seg, seg[1:], strict=False)), (
        "the post-change segment still straddles a break — the trend across it is invalid")


def test_the_closest_fit_wins_even_when_both_jumps_are_inside_the_tolerance() -> None:
    """The tolerance and the best-match rule are INDEPENDENT halves, so each is pinned alone. Here
    both candidates sit inside 25% of a stated 10x (8.0x → 20% error, 9.9x → 1% error); only the
    best-match rule separates them, and a first-match scan would take the 8.0x."""
    pts = [_pt("2025-03-31", 10_000_000.0),
           _pt("2025-06-30", 80_000_000.0),       # 8.0x — in range, poorer fit
           _pt("2025-09-30", 80_000_000.0),
           _pt("2025-12-31", 792_000_000.0)]      # 9.9x — the better fit
    assert _basis_break(pts, 10.0) == 3, "the first in-range jump won over the closer one"


def test_a_split_outside_the_window_does_not_suppress_a_real_trend() -> None:
    """THE FACTOR ALONE MUST NEVER SILENCE A READING — its LOCATION does. A name that split three
    years ago has a factor forever; every point in the trailing window sits on one basis, so the
    ordinary percentage is correct and must still print. Suppressing on the factor would blank the
    field permanently for any company that has ever split."""
    pts = [_pt("2025-03-31", 100_000_000.0), _pt("2025-06-30", 99_000_000.0),
           _pt("2025-09-30", 97_000_000.0)]
    assert _basis_break(pts, 10.0) is None
    # …and end to end: a fixture whose EPS states a factor but whose shares window is post-split
    facts = {"facts": {
        "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
            {"end": "2025-09-30", "val": 4.2e9, "filed": "2025-10-22", "form": "10-Q", "accn": "a"},
            {"end": "2026-06-30", "val": 4.0e9, "filed": "2026-07-17", "form": "10-Q", "accn": "b"},
        ]}}},
        "us-gaap": {"EarningsPerShareDiluted": {"units": {"USD/shares": [
            {"start": "2023-01-01", "end": "2023-12-31", "val": 12.03, "filed": "2024-01-23",
             "fy": 2023, "fp": "FY", "form": "10-K", "accn": "c"},
            {"start": "2023-01-01", "end": "2023-12-31", "val": 1.20, "filed": "2026-01-23",
             "fy": 2023, "fp": "FY", "form": "10-K", "accn": "d"},
            {"start": "2024-01-01", "end": "2024-12-31", "val": 19.83, "filed": "2025-01-23",
             "fy": 2024, "fp": "FY", "form": "10-K", "accn": "e"},
            {"start": "2024-01-01", "end": "2024-12-31", "val": 1.98, "filed": "2026-01-23",
             "fy": 2024, "fp": "FY", "form": "10-K", "accn": "f"},
        ]}}},
    }}
    out = _share_count_trend(_Stub(facts), "x", REF)
    assert out.value is not None and "share-basis change" not in out.value, (
        f"a split outside the window blanked a valid trend: {out.value}")
    assert "buying back" in out.value, out.value


def test_one_point_after_the_break_reports_no_trend_rather_than_a_two_point_fiction() -> None:
    """A window that breaks at its last point has nothing to measure on the current basis. Saying
    so beats both a cross-basis percentage and silence."""
    pts = [_pt("2025-06-30", 400_000_000.0), _pt("2025-09-30", 405_000_000.0),
           _pt("2025-12-31", 4_050_000_000.0)]
    assert _basis_break(pts, 10.0) == 2
    from vinci.dossier.mechanical import _split_straddled_trend
    out = _split_straddled_trend(pts, 2, 10.0)
    assert out.value is not None
    assert "NOT COMPARABLE" in out.value and "Only one share count since" in out.value
    assert "%" not in out.value.split("Only one")[0], "a percentage was printed across the break"


def test_the_post_change_span_is_stated_because_the_label_band_did_not_move() -> None:
    """The ±2% band was calibrated on a ~2y window; a post-change window is whatever the filer's
    calendar leaves — NFLX's is 0.5y, where −1.4% reads 'flat'. The band is a face-validity constant
    and is deliberately NOT re-tuned here, so the SPAN has to be visible or 'flat' is unreadable."""
    out = _share_count_trend(_Stub(json.loads(NFLX.read_text())), "0001065280", REF)
    assert out.value is not None and "over ~0.5y" in out.value, out.value


# ─── the fleet ────────────────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not Path("tests/fixtures/companyfacts").is_dir(), reason="no fixtures")
def test_no_other_committed_name_changes_reading() -> None:
    """SCOPE, pinned. Exactly one fixture has a basis change; a guard that started firing elsewhere
    would be matching on magnitude rather than on the filer's restatement. Asserts the SHAPE
    (split-flagged or not) rather than any wording, so it survives a re-render."""
    flagged = []
    for p in sorted(Path("tests/fixtures/companyfacts").glob("*.json")):
        out = _share_count_trend(_Stub(json.loads(p.read_text())), "x", REF)
        if out.value and "share-basis change" in out.value:
            flagged.append(p.stem)
    assert flagged == ["NFLX"], f"basis-change flag fired on {flagged}, expected only NFLX"
