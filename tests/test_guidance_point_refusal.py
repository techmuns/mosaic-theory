"""A point guide inside its own rounding noise is REFUSED, not adjudicated.

THE CASE (NFLX, from the analyst reading the committed page against the primary source). CIQ states
NFLX's quarterly revenue guide as a POINT — FQ2 2026: 12,574.0 — and the actual landed at 12,559.9,
**0.11% below**. The delivery rule was `actual ≥ floor` with zero tolerance, so the page printed
`FQ2 2026 MISSED` while Netflix's own filing called the quarter in line with guidance. Same shape
one year earlier: FQ3 2025 guided 11,526, delivered 11,510.3 (−0.14%) → "MISSED".

THE CALL IN THE BAND IS THE UNDECIDABLE THING, NOT THE POINT CLASS — measured across all 19
workbooks before the rule was written:

    2,067 resolved calls · 941 (46%) on point guides
    142 inside ±0.5% of the point → 25 read MISSED, 117 read MET
    119 point-misses worse than −5% — real failures on any reading

A BLANKET refusal of point adjudication (the first proposal) would erase 46% of the fleet's
delivery evidence, hide all 119 real misses, and zero ONON's record outright (its guides are ALL
points). The band refusal removes only the 142 undecidable calls — and since 117 of them were METs,
it LOWERS fleet hit-rates on net, which is the direction that rules out outcome-flattering.

RANGE guides are untouched: the company stated its own band, and the band IS the tolerance.
"""
from __future__ import annotations

from datetime import date

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq_sheets import _POINT_DECISION_BAND, _guidance_reads


#: One metric block in the REAL sheet shape `_guidance_rows`/`_nearest_period_header` consume:
#: a period-header row, then the block label, `Guidance Date` / `Guidance`, the `Actual/Latest`
#: sub-header and `Actual`. Dates are ISO strings (excel_date accepts them).
def _block(metric: str, periods: list[str], guides: list[str], actuals: list[float | None],
           dates: list[str]) -> list[list[object]]:
    return [
        ["", *periods],
        [metric],
        ["Guidance Date", *dates],
        ["Guidance", *guides],
        ["Actual/Latest"],
        ["Actual", *[a if a is not None else "" for a in actuals]],
    ]


def _read(rows: list[list[object]], metric: str) -> object:
    starts = cs._metric_starts(rows, (metric,))
    reads = _guidance_reads(rows, starts, date(2026, 8, 12), 45)
    assert reads, "the constructed block yielded no read at all"
    return reads[0]


def test_a_point_call_inside_the_band_is_refused_and_named() -> None:
    """THE NFLX SHAPE, on constructed rows with its real numbers: −0.11% against a point is not a
    verdict. It leaves the denominator, is counted as at-guide, and may hold the recent slot as a
    THIRD state — never silently dropped (absence attributed, per house rules)."""
    r = _read(_block("Revenue", ["FQ1 2026", "FQ2 2026"], ["12157.0", "12574.0"],
                     [12249.757, 12559.938], ["2026-04-17", "2026-07-16"]), "Revenue")
    assert (r.resolved, r.met_n, r.at_guide_n) == (1, 1, 1), (
        "the in-band call must leave the record and be counted as at-guide")
    assert r.recent_period == "FQ2 2026" and r.recent_verdict == "at_guide", (
        f"the most recent period is in the band and must say so: {r.recent_period} "
        f"{r.recent_verdict}")


def test_a_point_call_outside_the_band_keeps_its_verdict_in_both_directions() -> None:
    """THE ANTI-BLANKET HALF, and the reason this is a band and not a class: a −10% shortfall
    against a point forecast is a miss on any reading, and a +10% overshoot a beat. Refusing those
    would hide the fleet's 119 real point-misses."""
    miss = _read(_block("Revenue", ["FQ1 2026"], ["10000.0"], [9000.0], ["2026-04-17"]), "Revenue")
    assert (miss.resolved, miss.met_n, miss.at_guide_n) == (1, 0, 0)
    assert miss.recent_verdict == "missed"

    beat = _read(_block("Revenue", ["FQ1 2026"], ["10000.0"], [11000.0], ["2026-04-17"]), "Revenue")
    assert (beat.resolved, beat.met_n, beat.at_guide_n) == (1, 1, 0)
    assert beat.recent_verdict == "met"


def test_a_range_guide_is_adjudicated_even_at_its_own_edge() -> None:
    """RANGES ARE UNTOUCHED. The company stated its own band, and the band IS the tolerance — an
    actual just below a range floor is a miss the company's own wording defines."""
    lo, hi = 10_000.0, 10_200.0
    just_below = _read(_block("Revenue", ["FY 2025"], [f"{lo:,.2f} - {hi:,.2f}"],
                              [lo * (1 - 0.001)], ["2025-01-21"]), "Revenue")
    assert (just_below.resolved, just_below.at_guide_n) == (1, 0), (
        "a RANGE call entered the point band — the refusal leaked past the point class")
    assert just_below.recent_verdict == "missed"


def test_a_cost_like_point_is_banded_in_its_own_direction() -> None:
    """#437's direction map still decides WHICH bound binds; the band rides on top of it. A tax
    rate guided at a 19.0 point and delivered at 19.05 (+0.26%) is inside the band — neither the
    MET the old sign-heuristic would have printed nor a MISSED."""
    r = _read(_block("Effective Tax Rate %", ["FQ4 2026"], ["19.0"], [19.05], ["2026-07-28"]),
              "Effective Tax Rate %")
    assert (r.resolved, r.at_guide_n) == (0, 1)
    assert r.recent_verdict == "at_guide"

    far = _read(_block("Effective Tax Rate %", ["FQ4 2026"], ["19.0"], [24.0], ["2026-07-28"]),
                "Effective Tax Rate %")
    assert far.recent_verdict == "missed", "a rate 26% over its point guide is a real miss"


def test_a_zero_point_guide_cannot_carry_a_relative_band() -> None:
    """A zero point has no scale to band against; it stays adjudicated by sign rather than being
    refused on an undefined margin."""
    r = _read(_block("Revenue", ["FQ1 2026"], ["0.0"], [5.0], ["2026-04-17"]), "Revenue")
    assert (r.resolved, r.at_guide_n) == (1, 0)


def test_the_band_is_the_measured_constant_not_a_drifting_literal() -> None:
    """0.5% is face-validity — the scale of a company's own "in line" language, with both live
    false-MISSes (−0.11%, −0.14%) well inside it. It is NEVER outcome-tuned; anyone moving it owes
    a re-measurement of the 142-call census in the module docstring."""
    assert _POINT_DECISION_BAND == 0.005


# ─── the committed corpus, where the rule has to survive the real sheets ─────────────────────────
def _bundle(ticker: str):
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.manual_store import LocalFolderStore

    files = LocalFolderStore(get_config().data_dir / "manual" / "ciq").files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


def test_nflx_fq2_2026_reads_at_guide_not_missed() -> None:
    """THE ANALYST'S FINDING, end to end on the licensed workbook. The primary source calls the
    quarter in line; the page must stop contradicting it."""
    rows = cs.guidance_bridge_rows(_bundle("NFLX"), reference_date=date(2026, 8, 12)).value or []
    rev = next(r for r in rows if r.metric == "Revenue")
    assert "FQ2 2026" in rev.most_recent, rev.most_recent
    assert "MISSED" not in rev.most_recent, (
        f"a −0.11% shortfall against a point forecast still reads as a miss: {rev.most_recent}")
    assert "AT GUIDE" in rev.most_recent
    assert "at-guide" in rev.record, "the record must disclose how many calls were refused"


def test_onon_keeps_a_record_because_the_refusal_is_a_band_not_a_class() -> None:
    """THE NAME A BLANKET REFUSAL WOULD HAVE ERASED: every ONON guide is a point, so refusing the
    class leaves 0/0 — a delivery history destroyed to fix a rounding artefact. The band keeps its
    decidable calls."""
    rows = cs.guidance_bridge_rows(_bundle("ONON"), reference_date=date(2026, 8, 12)).value or []
    rev = next(r for r in rows if r.metric == "Revenue")
    assert rev.record != "—", "ONON lost its delivery record entirely — the refusal over-reached"
    assert "actual ≥ floor" in rev.record


def test_real_misses_survive_across_the_fleet() -> None:
    """THE 119 POINT-MISSES WORSE THAN −5% ARE REAL, and the refusal must not eat them. Asserted as
    presence-of-the-state across the fleet rather than any one name's figure."""
    from vinci.config import get_config
    from vinci.dossier.manual_store import LocalFolderStore

    root = get_config().data_dir / "manual" / "ciq"
    ms = LocalFolderStore(root)
    if not root.is_dir() or not any(root.iterdir()):
        pytest.skip("licensed CIQ bundles unavailable (never committed)")
    missed = at_guide = 0
    for tk in sorted(p.name for p in root.iterdir() if p.is_dir()):
        try:
            from vinci.dossier.ciq import CiqBundle
            rows = cs.guidance_bridge_rows(
                CiqBundle.from_files(tk, ms.files(tk)), reference_date=date(2026, 8, 12)
            ).value or []
        except Exception:
            continue
        missed += sum("MISSED" in (r.most_recent or "") for r in rows)
        at_guide += sum("at-guide" in (r.record or "") for r in rows)
    assert missed, "no MISSED anywhere in the fleet — the band refusal erased real verdicts"
    assert at_guide, "no at-guide disclosure anywhere — the refusal never fires on the live corpus"


def test_the_summary_never_calls_an_at_guide_period_resolved() -> None:
    """REVIEW FINDING (#443). The at-guide state is deliberately EXCLUDED from `resolved`, but the
    summary string still introduced it with "most recent resolved:" — printing

        most recent resolved: FQ2 2026 AT GUIDE (±0.5% of a point — not adjudicated)

    which contradicts itself and implies the refused call entered the delivery record after all.
    A third state that is announced under the second state's name is two states again.

    ONE NEUTRAL LABEL CARRIES ALL THREE, and this pins the OUTPUT rather than the wording of any
    single verdict — asserted on the rendered string, which is what a reader receives.
    """
    from datetime import date as _d

    from vinci.dossier.ciq_sheets import guidance_bridge

    text = guidance_bridge(_bundle("NFLX"), reference_date=_d(2026, 8, 12)).value or ""
    assert "AT GUIDE" in text, "the at-guide state never reaches the summary string"
    assert "most recent resolved" not in text, (
        "an at-guide period is announced as 'resolved' — the very distinction the third state "
        "exists to preserve")
    assert "most recent guidance outcome:" in text

    # …and the neutral label serves the adjudicated states too, so the three are phrased alike and
    # differ only in the VERDICT — never in whether they are introduced at all.
    other = next((t for t in ("V", "AORT", "CNXC")
                  if "MET" in (guidance_bridge(_bundle(t), reference_date=_d(2026, 8, 12)).value
                               or "")), None)
    if other is None:
        pytest.skip("no committed name carries an adjudicated MET in its summary")
    met_text = guidance_bridge(_bundle(other), reference_date=_d(2026, 8, 12)).value or ""
    assert "most recent guidance outcome:" in met_text
    assert "most recent resolved" not in met_text
