"""The adjusted-EPS guide reaches the valuation from the NEWEST release — and the current-guide line
keeps its cents and says when newer releases carry no parsed guide (2026-10-21).

THE DEFECT. `valuation.adjusted_eps` was read from the drawdown 8-K's revised guidance ONLY, so 26
of 27 pages said "adjusted figure not in the 99.1 revised guidance" — TJX and Burlington among them,
neither of which has a drawdown 8-K, while each of their latest releases states one (TJX $5.15–$5.20
for Fiscal 2027, Burlington $11.77–$11.97). The note also claimed a read that never happened.

THE TRAP BESIDE THE FIX. Target's March guide ($7.50–$8.50) became readable in the same change,
and August's raise to $9.90–$10.90 is not. "The newest release that happens to carry a guide"
would print March's as Target's earnings power; the newest release, or nothing, does not.
"""
from __future__ import annotations

import json
import typing
from datetime import date
from pathlib import Path

from tests.test_dossier import _facts, _min_record, _StubEdgar
from tests.test_guidance_opener_period import _TJX
from vinci.dossier import mechanical as dm
from vinci.dossier.schemas import (
    GuidanceItem,
    PrimarySource,
    ReleaseExtract,
    Sourced,
    SourceStatus,
)
from vinci.edgar.client import EdgarClient
from vinci.edgar.release_parse import parse_release

_ABSENT: Sourced[str] = Sourced.unknown(
    note="no revised guidance at the drawdown to read an adjusted figure from")


def _g(period: str, lo: float, hi: float, *, metric: str = "adjusted eps",
       unit: str = "$/sh") -> GuidanceItem:
    return GuidanceItem(metric=metric, period=period, low=lo, high=hi, unit=unit,
                        qualitative=False, verbatim="v", source_ref="s")


def _rel(acc: str, filed: str, guides: list[GuidanceItem]) -> ReleaseExtract:
    return ReleaseExtract(source_ref=f"8-K {acc} EX-99.1", filed=date.fromisoformat(filed),
                          guidance=guides, reconciliation=[], one_offs=[], event_impacts=[],
                          qa_flags=[])


# --- the valuation field --------------------------------------------------------------------------

def test_tjx_s_year_reaches_the_valuation_from_its_own_release_text() -> None:
    """END TO END from the filing's sentences: parse → the newest release → the field. The YEAR's
    range, never the quarter's, and the P/E struck on its midpoint at the stored close."""
    rel = parse_release(_TJX, source_ref="8-K 0000109198-26-000045 EX-99.1").model_copy(
        update={"filed": date(2026, 8, 19)})
    out = dm._release_adjusted_eps([rel], _min_record(pe=30.0, price=155.25), _ABSENT)
    assert out.status is SourceStatus.PRESENT, out.note
    assert "$5.15–$5.20" in (out.value or "") and "1.30" not in (out.value or ""), out.value
    assert f"~{155.25 / 5.175:.1f}x at $155.25" in (out.value or ""), out.value
    assert "0000109198-26-000045" in (out.source_ref or "") and "2026-08-19" in (
        out.source_ref or "")


def test_burlington_s_committed_release_reaches_the_valuation_e2e() -> None:
    """THE COMMITTED PAGE, read as the assembler will read it: Burlington's stored releases already
    carry its guide, and nothing carried it to the field. Asserts the field equals the newest
    release's annual adjusted-EPS range, whatever it reads after a re-pull — a value pin on a living
    page would rot."""
    doc = json.loads(Path("data/dossiers/BURL/dossier.json").read_text())
    ps = PrimarySource.model_validate(doc["mechanical"]["primary_source"])
    newest = max((r for r in ps.releases if r.filed), key=lambda r: r.filed or date.min)
    annual = [g for g in newest.guidance if g.metric == "adjusted eps" and g.low and g.high
              and dm.primary_source.period_scope(g.period) == "annual"]
    out = dm._release_adjusted_eps(ps.releases, _min_record(pe=27.0, price=256.85), _ABSENT)
    if not annual:
        assert out.status is SourceStatus.UNKNOWN
        return
    lo, hi = dm._guide_bounds(annual[0].low or 0.0, annual[0].high or 0.0, "$/sh")
    assert out.status is SourceStatus.PRESENT and f"${lo}–${hi}" in (out.value or ""), out


def test_a_newer_release_without_a_guide_is_never_reached_past() -> None:
    """TARGET'S SHAPE. March parses, May and August do not: the field is UNKNOWN and names the
    release it read, rather than printing March's guide as today's earnings power."""
    out = dm._release_adjusted_eps([
        _rel("0000027419-26-000034", "2026-08-19", []),
        _rel("0000027419-26-000020", "2026-05-20", []),
        _rel("0000027419-26-000012", "2026-03-03", [_g("next-fy", 7.50, 8.50)]),
    ], _min_record(pe=20.0, price=110.0), _ABSENT)
    assert out.status is SourceStatus.UNKNOWN
    assert "0000027419-26-000034" in (out.note or "") and "2026-08-19" in (out.note or "")
    assert (_ABSENT.note or "") in (out.note or ""), "the drawdown absence must stay stated"
    assert "7.50" not in (out.note or "")


def test_a_quarter_s_eps_is_never_an_earnings_power() -> None:
    """A quarterly range over today's price is not a P/E. NEGATIVE beside it: a change-basis EPS
    guide is not a level either."""
    quarter_only = [_rel("a", "2026-08-19", [_g("Q3 2027", 1.30, 1.32)])]
    assert dm._release_adjusted_eps(
        quarter_only, _min_record(pe=30.0, price=150.0), _ABSENT).status is SourceStatus.UNKNOWN
    change = _g("next-fy", 4.0, 6.0, unit="%").model_copy(update={"basis": "change"})
    assert dm._release_adjusted_eps(
        [_rel("a", "2026-08-19", [change])], _min_record(pe=30.0, price=150.0),
        _ABSENT).status is SourceStatus.UNKNOWN


def test_no_dated_release_leaves_the_drawdown_absence_as_it_was() -> None:
    assert dm._release_adjusted_eps([], _min_record(pe=30.0, price=150.0), _ABSENT) == _ABSENT


def test_the_absence_says_which_read_happened() -> None:
    """26 of 27 pages said "not in the 99.1 revised guidance" whether or not one had been read.
    POSITIVE: a revised guidance WAS read and holds no adjusted figure — the old words, still true.
    NEGATIVE: none was read — the note says so instead of describing a read."""
    edgar = typing.cast(EdgarClient, _StubEdgar(_facts([(2024, 0.85)], shares=1e8), 1e9))
    rec = _min_record(pe=30.0, price=150.0)
    read = Sourced.present("Revised outlook: revenue of $1.0 billion to $1.1 billion",
                           source_ref="8-K x Ex-99.1")
    none = Sourced[str].unknown(note="no catalyst 8-K to follow for a revised-guidance exhibit")
    eps_read = dm._adjusted_facts(rec, edgar, read, date(2026, 10, 21))[0]
    eps_none = dm._adjusted_facts(rec, edgar, none, date(2026, 10, 21))[0]
    assert eps_read.note == "adjusted figure not in the 99.1 revised guidance"
    assert eps_none.note == "no revised guidance at the drawdown to read an adjusted figure from"


# --- the current-guide line -----------------------------------------------------------------------

def test_a_per_share_guide_keeps_its_cents() -> None:
    """`.1f` printed Burlington's $11.77–$11.97 as "11.8–12.0" and would print TJX's $5.15–$5.20 as
    "5.2–5.2" — a range the company never gave. A $M guide prints as it always did."""
    out = dm._current_guide([_rel("a", "2026-08-19", [
        _g("Fiscal 2027", 5.15, 5.20), _g("next-fy", 11.77, 11.97),
        _g("2026", 1410.0, 1425.0, metric="revenue", unit="$M")])])
    assert "5.15–5.20 $/sh" in (out.value or ""), out.value
    assert "11.77–11.97 $/sh" in (out.value or ""), out.value
    assert "1,410.0–1,425.0 $M" in (out.value or ""), out.value


def test_a_newer_release_with_no_parsed_guide_is_named_beside_the_old_one() -> None:
    """POSITIVE: March's guide, with May and August unparsed — printed, AND marked with both later
    filings (live on FUBO, LLY, MVST and NFLX before this change). NEGATIVE: when the newest
    release carries the guide, no mark."""
    stale = dm._current_guide([
        _rel("aug", "2026-08-19", []), _rel("may", "2026-05-20", []),
        _rel("mar", "2026-03-03", [_g("next-fy", 7.50, 8.50)])])
    assert "7.50–8.50" in (stale.value or "")
    assert "2 newer releases (filed 2026-05-20, 2026-08-19) carry no parsed guide" in (
        stale.value or ""), stale.value
    fresh = dm._current_guide([
        _rel("aug", "2026-08-19", [_g("next-fy", 9.90, 10.90)]),
        _rel("mar", "2026-03-03", [_g("next-fy", 7.50, 8.50)])])
    assert "newer release" not in (fresh.value or "") and "9.90–10.90" in (fresh.value or "")
