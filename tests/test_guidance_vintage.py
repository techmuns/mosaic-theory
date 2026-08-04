"""Superseded guidance is MARKED in the brief, never dropped, and never left unordered.

WHY. The digest emitted every release's guidance as `guidance (metric period): low–high →
source_ref` — **no date, no order**. On SMPL that set July's `net sales 2026: 1,345–1,355` beside
April's `1,310–1,350` as equals, and the synthesis argued the FY26 guide from the APRIL filing.
That is audit defect P2 returning through the BRIEF after the extractor was fixed: the mechanical
layer was right the whole time — `current_guide` even names the July 8-K — and nothing carried it
into the digest.

MARK, NEVER DROP: the guidance history IS a bear point (SMPL's three-step cut sequence), so
superseded releases stay and merely stop looking current. Dates only — no heuristic, no ranking.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.dossier.schemas import Dossier
from vinci.dossier.synthesis import _primary_source_digest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"


def _digest(t: str) -> str:
    d = Dossier.model_validate(json.loads((DOSS / t / "dossier.json").read_text()))
    ps = d.mechanical.primary_source
    assert ps is not None, f"{t} has no primary_source"
    return _primary_source_digest(ps)


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_the_smpl_case_that_produced_p2_is_now_marked() -> None:
    """THE ORIGINAL DEFECT, pinned on the name it happened to. April's guide must still appear —
    dropping it would lose the cut sequence — and must be marked superseded by July's."""
    lines = _digest("SMPL").splitlines()
    cur = [i for i, x in enumerate(lines) if x.startswith("--- CURRENT GUIDE (filed 2026-07-09)")]
    sup = [i for i, x in enumerate(lines) if x.startswith("--- SUPERSEDED (filed 2026-04-09")]
    assert cur and sup, lines[:12]
    blob = "\n".join(lines)
    assert "1345.0–1355.0" in blob and "1310.0–1350.0" in blob, "a guide was DROPPED, not marked"
    assert "replaced by the guide filed 2026-07-09" in blob
    assert "NOT the company's current outlook" in blob


def test_exactly_one_current_marker_per_name_and_the_rest_superseded() -> None:
    """DATES ONLY. Across every committed name: at most one CURRENT marker, and it carries the
    LATEST filed date of any guidance-bearing release — computed over ALL releases, not just the
    four the digest shows, so a fifth release cannot leave the wrong one marked current."""
    if not DOSS.is_dir():
        pytest.skip("no committed dossiers")
    for folder in sorted(DOSS.glob("*/dossier.json")):
        t = folder.parent.name
        d = Dossier.model_validate(json.loads(folder.read_text()))
        ps = d.mechanical.primary_source
        if ps is None or not any(r.guidance for r in ps.releases):
            continue
        lines = _digest(t).splitlines()
        cur = [x for x in lines if x.startswith("--- CURRENT GUIDE")]
        dated = [r.filed for r in ps.releases if r.guidance and r.filed]
        # every guidance release undated -> none may claim current
        if not dated:
            assert not cur, f"{t}: a CURRENT marker on undated releases — {cur}"
            assert any("VINTAGE UNDATED" in x for x in lines), t
            continue
        assert len(cur) <= 1, f"{t}: {len(cur)} CURRENT markers — {cur}"
        assert cur, f"{t}: guidance is dated but nothing is marked current"
        assert str(max(dated)) in cur[0], (
            f"{t}: current marker is not the newest filing — {cur[0]}")


@pytest.mark.skipif(not (DOSS / "MVST").is_dir(), reason="no committed MVST")
def test_an_undated_release_is_labelled_not_guessed() -> None:
    """FAIL LOUD ON THE UNORDERABLE. MVST's guidance-bearing releases carry no `filed` date, so
    neither can be ranked. Labelled UNDATED rather than assumed current or assumed stale — a guess
    either way would be the defect this file exists to close, wearing a different hat."""
    lines = _digest("MVST").splitlines()
    assert not any(x.startswith("--- CURRENT GUIDE") for x in lines), lines[:10]
    assert not any(x.startswith("--- SUPERSEDED") for x in lines), lines[:10]
    und = [x for x in lines if "VINTAGE UNDATED" in x]
    assert und and "do not read it as current" in und[0], und


def test_supersession_is_computed_over_all_releases_not_the_shown_window() -> None:
    """SYNTHETIC ON PURPOSE, and the reason is worth stating: the digest shows only
    `releases[:4]`, and on today's corpus every name's newest guidance-bearing release already
    falls inside that window — so mutating the computation to key off `recent` instead of
    `ps.releases` changes NOTHING measurable, and a corpus-driven pin cannot catch it.

    The property is still real. Nothing asserts that `releases` arrives newest-first;
    `mechanical.py` appends them as it walks filings, and the digest's window is a display bound,
    not an ordering guarantee. If a fifth release ever carries the newest guide, keying off the
    window would mark a STALE release CURRENT — the exact defect this file closes, inverted.

    (CORPUS BEFORE SYNTHETIC is the rule; this is the case where the corpus provably cannot drive
    it, so the synthetic is the honest option rather than the lazy one.)
    """
    import datetime as _dt

    from vinci.dossier.schemas import GuidanceItem, PrimarySource, ReleaseExtract

    def _rel(day: int, low: float) -> ReleaseExtract:
        return ReleaseExtract(
            filed=_dt.date(2026, 1, day), source_ref=f"8-K day{day} EX-99.1",
            guidance=[GuidanceItem(metric="revenue", period="2026", low=low, high=low + 10,
                                   unit="$M", qualitative=False, verbatim="v", source_ref="s")])

    # five releases, OLDEST-first: the newest guide is the FIFTH, outside `releases[:4]`
    from vinci.dossier.schemas import Sourced
    _u = Sourced.unknown(note="not under test")
    ps = PrimarySource(releases=[_rel(d, float(d)) for d in (1, 2, 3, 4, 5)],
                       self_funding=_u, wall_coherence=_u, basis_triangulation=_u,
                       guide_verification=_u)
    lines = _primary_source_digest(ps).splitlines()
    cur = [x for x in lines if x.startswith("--- CURRENT GUIDE")]
    assert cur == [], (
        "a release inside the shown window was marked CURRENT while a NEWER guide sits outside it "
        f"— supersession is being computed over the window, not all releases: {cur}")
    assert all("2026-01-05" in x for x in lines if x.startswith("--- SUPERSEDED")), lines
