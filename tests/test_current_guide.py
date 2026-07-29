"""ITEM 1 CLAUSE (c) — the guidance split, pinned.

THE DEFECT. `_revised_guidance` walks the DRAWDOWN 8-Ks and returns the first with a guidance
block. Its docstring claimed BOTH "on the drawdown 8-Ks" and "the verdict-relevant number", and
those diverge exactly when guidance is revised after the drawdown. SMPL: the bear argued April's
guide from that field while the base used July's from `primary_source.releases`, both unlabelled,
in one document.

WHAT THESE PIN. `_current_guide` answers the second question only, and it must do so by the
release's OWN filing date — the two ways of getting it wrong are SELECTION BY POSITION (the trap
the `[-1]` rule is about) and SELECTION BY DRAWDOWN SCOPE (the trap the field was split out of).
Each has its own red below, and each fixture is built so the WRONG answer is a different value
from the right one — a fixture where position and date agree would pass either way and pin nothing.
"""
from __future__ import annotations

import datetime as dt

from vinci.dossier.mechanical import _current_guide
from vinci.dossier.schemas import GuidanceItem, ReleaseExtract, SourceStatus


def _rel(acc: str, filed: str | None, *, guide: bool = True) -> ReleaseExtract:
    g = ([GuidanceItem(metric="net sales", period="2026", low=1000.0, high=1100.0, unit="$M",
                       qualitative=False, verbatim=f"from {acc}", source_ref=f"8-K {acc}")]
         if guide else [])
    return ReleaseExtract(
        source_ref=f"8-K {acc} EX-99.1",
        filed=dt.date.fromisoformat(filed) if filed else None,
        guidance=g, reconciliation=[], one_offs=[], event_impacts=[], qa_flags=[])


def test_current_guide_picks_by_date_never_by_position() -> None:
    """THE RED for the `[-1]` class. The fixture is deliberately ordered so that NEITHER the first
    nor the last element is the newest — position-based selection returns a different accession
    from date-based selection, so `releases[0]`, `releases[-1]` and `max(filed)` are three distinct
    answers and only one is right.

    EDGAR happens to return newest-first today, which is exactly why this matters: a positional
    implementation would look correct on every real bundle until the day the order changed."""
    releases = [
        _rel("acc-APR", "2026-04-09"),      # first, but NOT newest
        _rel("acc-JUL", "2026-07-09"),      # newest, in the MIDDLE
        _rel("acc-JAN", "2026-01-08"),      # last, and OLDEST
    ]
    out = _current_guide(releases)
    assert out.status is SourceStatus.PRESENT
    assert "acc-JUL" in (out.source_ref or ""), (
        f"selected {out.source_ref!r} — position-based selection would give acc-APR ([0]) or "
        "acc-JAN ([-1]); only max(filed) gives acc-JUL")
    assert "filed 2026-07-09" in (out.source_ref or ""), (
        "the chosen release must state the date it was chosen ON, or a reader cannot check the "
        "selection — the source_ref is the whole audit trail for this field")


def test_current_guide_is_not_drawdown_scoped() -> None:
    """THE RED for the trap the field was SPLIT OUT OF. `drawdown_cause.revised_guidance` sees only
    8-Ks at a gap-down; SMPL's July guide was never a candidate there. `_current_guide` reads
    `primary_source.releases` — every results filing — so a newer non-gap filing MUST win.

    Modelled on the real shapes: April is the drawdown filing, July is not."""
    drawdown_only = _current_guide([_rel("0001702744-26-000010", "2026-04-09")])
    assert "0001702744-26-000010" in (drawdown_only.source_ref or "")

    with_july = _current_guide([
        _rel("0001702744-26-000021", "2026-07-09"),      # NOT a gap-down filing
        _rel("0001702744-26-000010", "2026-04-09"),      # the drawdown filing
    ])
    assert "0001702744-26-000021" in (with_july.source_ref or ""), (
        "the drawdown filing won — this field is drawdown-scoped again, which is the exact defect "
        "the split exists to remove")
    # and the two fields genuinely disagree here — which is the whole reason for the split. If a
    # future refactor made them return the same source, this test would be pinning nothing.
    assert (with_july.source_ref or "") != (drawdown_only.source_ref or ""), (
        "the split field and the drawdown-scoped one selected the SAME filing, so this fixture no "
        "longer exercises the divergence it was built for")


def test_absence_is_attributed_and_never_silent() -> None:
    """Three distinct absences, three distinct reasons. A bare UNKNOWN would tell a reader nothing
    about whether we looked, found nothing, or could not order what we found."""
    none_parsed = _current_guide([])
    assert none_parsed.status is SourceStatus.UNKNOWN
    assert "no EX-99.1 release parsed" in (none_parsed.note or "")

    no_guide = _current_guide([_rel("a", "2026-07-09", guide=False),
                               _rel("b", "2026-04-09", guide=False)])
    assert no_guide.status is SourceStatus.UNKNOWN
    assert "no guide in any of the 2 parsed release(s)" in (no_guide.note or "")

    # a guide with NO date is the interesting one: we have the number but cannot say it governs
    undated = _current_guide([_rel("a", None), _rel("b", None)])
    assert undated.status is SourceStatus.UNKNOWN
    assert "none carries a filing date" in (undated.note or ""), (
        "a dateless guide must NOT be returned as current — that is a claim we cannot support, "
        "and returning it would reintroduce position-trust by the back door")


def test_a_dated_release_beats_an_undated_one_rather_than_being_skipped() -> None:
    """Mixed dating: the dated release wins outright. Falling back to 'first with a guide' when
    ANY release lacks a date would silently restore positional selection on exactly the corpus
    where dating is unreliable."""
    out = _current_guide([_rel("undated", None), _rel("dated", "2026-07-09")])
    assert out.status is SourceStatus.PRESENT and "dated" in (out.source_ref or "")
