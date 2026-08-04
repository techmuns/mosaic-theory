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
    cur = [x for x in lines if "[CURRENT GUIDE, filed 2026-07-09]" in x]
    sup = [x for x in lines if "[SUPERSEDED — filed 2026-04-09" in x]
    assert cur and sup, lines[:12]
    assert all(x.startswith("guidance ") for x in cur + sup), "a mark landed off a guidance line"
    blob = "\n".join(lines)
    assert "1345.0–1355.0" in blob and "1310.0–1350.0" in blob, "a guide was DROPPED, not marked"
    assert "replaced by the guide filed 2026-07-09" in blob
    assert "history, not the current outlook" in blob


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
        cur = [x for x in lines if "[CURRENT GUIDE," in x]
        dated = [r.filed for r in ps.releases if r.guidance and r.filed]
        # every guidance release undated -> none may claim current
        if not dated:
            assert not cur, f"{t}: a CURRENT marker on undated releases — {cur}"
            assert any("VINTAGE UNDATED" in x for x in lines), t
            continue
        # ONE CURRENT VINTAGE, not one current LINE: the mark is per guidance ITEM, so a release
        # stating four metrics yields four CURRENT marks and that is correct. What must be unique
        # is the DATE they carry. (The first cut asserted a line count, which was only true while
        # the mark was a per-release header — an assertion outliving the shape it described.)
        assert cur, f"{t}: guidance is dated but nothing is marked current"
        stamps = {x.split("[CURRENT GUIDE, filed ")[1].split("]")[0] for x in cur}
        assert stamps == {str(max(dated))}, (
            f"{t}: current marks carry {sorted(stamps)}, newest filing is {max(dated)}")


@pytest.mark.skipif(not (DOSS / "MVST").is_dir(), reason="no committed MVST")
def test_an_undated_release_is_labelled_not_guessed() -> None:
    """FAIL LOUD ON THE UNORDERABLE. MVST's guidance-bearing releases carry no `filed` date, so
    neither can be ranked. Labelled UNDATED rather than assumed current or assumed stale — a guess
    either way would be the defect this file exists to close, wearing a different hat."""
    lines = _digest("MVST").splitlines()
    assert not any("[CURRENT GUIDE," in x for x in lines), lines[:10]
    assert not any("[SUPERSEDED" in x for x in lines), lines[:10]
    und = [x for x in lines if "VINTAGE UNDATED" in x]
    assert und and "do not read as current" in und[0], und
    assert all(x.startswith("guidance ") for x in und), (
        "the undated mark landed off a guidance line")


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
    cur = [x for x in lines if "[CURRENT GUIDE," in x]
    assert cur == [], (
        "a release inside the shown window was marked CURRENT while a NEWER guide sits outside it "
        f"— supersession is being computed over the window, not all releases: {cur}")
    assert all("2026-01-05" in x for x in lines if "[SUPERSEDED" in x), lines


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_only_guidance_carries_a_vintage_mark_never_a_reported_actual() -> None:
    """THE DEFECT THE FIRST CUT SHIPPED, now pinned. The mark began life as a section header —
    `--- SUPERSEDED … history, NOT the company's current outlook ---` — which visually scoped over
    EVERYTHING beneath it. On SMPL that was April's guidance (correct) plus the Q2, Q1 and FY2025
    REPORTED ACTUALS and the $60.9M Atkins impairment: facts, none of them superseded, and the
    impairment is the very figure 19c FORCES the synthesis to cite. It also bled into the next
    guidance-less release, which emits no header of its own.

    A per-line mark has no scope to creep and nothing to bleed into. Reconciliations, one-offs and
    event impacts must carry NO vintage mark at all."""
    marks = ("[CURRENT GUIDE,", "[SUPERSEDED", "VINTAGE UNDATED")
    for line in _digest("SMPL").splitlines():
        if any(m in line for m in marks):
            assert line.startswith("guidance "), (
                f"a vintage mark landed on a non-guidance line — a reported actual is not "
                f"superseded: {line[:130]}")
    blob = _digest("SMPL")
    imp = [x for x in blob.splitlines() if "60.9M" in x]
    assert imp, "SMPL's $60.9M impairment left the digest"
    assert not any(m in x for x in imp for m in marks), (
        f"the impairment 19c forces the synthesis to cite is marked as stale: {imp}")


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_the_analyst_template_shows_the_same_vintages_as_the_brief() -> None:
    """P2 IN THE DECISION AID, closed. The template read `drawdown_cause.revised_guidance` and
    printed whatever it held under the label "current guidance". On SMPL that field holds the APRIL
    release, so the page the analyst sets six numbers from asserted the current outlook was
    "$1.31 to $1.35 billion, or −10% to −7%" and "300 to 350 basis points" — when July's guide is
    $1.345–1.355B, −7% to −6%, roughly −375bps.

    It survived the 2026-08-04 brief fix because that fix went to `primary_source` while this read a
    different field. BOTH now derive the vintage from one shared helper, so they cannot drift again:
    this test asserts the template's marks MATCH the brief's, rather than asserting a literal.
    """
    from vinci.dossier.propose import build_template
    doc = json.loads((DOSS / "SMPL" / "dossier.json").read_text())
    tmpl = [x for x in build_template(doc)["_evidence"]["revenue"]
            if x.startswith("guidance (")]
    brief = [x for x in _digest("SMPL").splitlines() if x.startswith("guidance (")]
    assert tmpl and brief

    def marks(lines: list[str]) -> set[str]:
        out = set()
        for x in lines:
            for m in ("[CURRENT GUIDE, filed ", "[SUPERSEDED — filed ", "[VINTAGE UNDATED"):
                if m in x:
                    out.add(x.split(m)[1].split("]")[0].split(",")[0].split(" ")[0])
        return out

    assert marks(tmpl) == marks(brief), (
        f"template and brief disagree on guidance vintages — template {sorted(marks(tmpl))}, "
        f"brief {sorted(marks(brief))}; they must share one derivation")
    blob = " ".join(tmpl)
    assert "1345.0–1355.0" in blob and "[CURRENT GUIDE, filed 2026-07-09]" in blob, blob[:200]
    assert "1310.0–1350.0" in blob, "April's guide was DROPPED from the template, not marked"
    assert "current guidance:" not in " ".join(build_template(doc)["_evidence"]["revenue"]), (
        "the old unmarked 'current guidance:' line is back")
