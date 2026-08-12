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
    """THE ORIGINAL DEFECT, pinned on the name it happened to. The older guide must still appear —
    dropping it would lose the cut sequence — and must be marked superseded by the newest.

    DATES AND VALUES ARE DERIVED FROM THE RECORD, NEVER TYPED IN. The first cut hardcoded
    `2026-07-09`, `2026-04-09`, `1345.0–1355.0` and `1310.0–1350.0` against `data/dossiers/SMPL`
    — a LIVING artifact. Those literals are not wrong today; they are SCHEDULED to rot, because
    SMPL's next print lands a new 8-K, `filed 2026-07-09` stops being current, and the test reddens
    on a routine data event rather than on a defect (TEST-LAYER RULE: a value-level pin belongs on
    a frozen fixture, never on the re-drawn artifact). Reading the two dates and their guide values
    off `primary_source` keeps the defect coverage identical — a guide was marked, not dropped —
    while surviving every future guide."""
    d = Dossier.model_validate(json.loads((DOSS / "SMPL" / "dossier.json").read_text()))
    ps = d.mechanical.primary_source
    assert ps is not None
    # WITHIN THE DIGEST'S OWN WINDOW (corrected 2026-08-12). This took the OLDEST dated
    # guidance-bearing release and asserted the digest marks it — but the digest shows the four
    # most recent guidance-bearing releases and DISCLOSES the rest, so on a name with five the
    # oldest is legitimately absent and the pin reddened on a data event. The defect it exists to
    # catch is "a superseded guide was dropped or left unmarked", which is observable on any
    # supersession inside the window; taking the oldest SHOWN one keeps that coverage exactly.
    dated = sorted({r.filed for r in ps.releases if r.guidance and r.filed})
    shown = sorted({r.filed for r in [x for x in ps.releases if x.guidance][:4] if r.filed})
    assert len(shown) >= 2, (
        "SMPL no longer carries two dated guidance-bearing releases inside the digest window — "
        "this test needs a supersession to observe; re-point it at a name that has one")
    newest, older = dated[-1], shown[0]

    def _vals(on: object) -> set[str]:
        return {f"{g.low}–{g.high}" for r in ps.releases if r.filed == on
                for g in (r.guidance or []) if not g.qualitative}

    lines = _digest("SMPL").splitlines()
    cur = [x for x in lines if f"[CURRENT GUIDE, filed {newest}]" in x]
    sup = [x for x in lines if f"[SUPERSEDED — filed {older}" in x]
    assert cur and sup, lines[:12]
    assert all(x.startswith("guidance ") for x in cur + sup), "a mark landed off a guidance line"
    blob = "\n".join(lines)
    for label, want in (("newest", _vals(newest)), ("older", _vals(older))):
        missing = {v for v in want if v not in blob}
        assert not missing, f"a {label} guide was DROPPED, not marked: {sorted(missing)}"
    assert f"replaced by the guide filed {newest}" in blob
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

    # SUBSET, NOT EQUALITY (corrected 2026-08-12). The equality held only while no name had more
    # than four GUIDANCE-BEARING releases, and it broke the moment richer extraction gave SMPL a
    # fifth — on a data event, not a defect. The brief caps at four BY DESIGN and says so in its own
    # note; the template is the analyst surface and carries the full history. Asserting they match
    # would force one of those two deliberate choices to give way.
    #
    # WHAT ACTUALLY MUST HOLD is the thing the old message was reaching for — ONE DERIVATION: every
    # vintage the brief shows must exist in the template, and the CURRENT/SUPERSEDED mark on a
    # shared vintage must agree. A brief that promoted a superseded guide to current, or invented a
    # vintage the template does not have, is the P2 defect returning; a brief that shows fewer is
    # the documented window.
    assert marks(brief) <= marks(tmpl), (
        f"the brief shows guidance vintages the template does not — brief {sorted(marks(brief))}, "
        f"template {sorted(marks(tmpl))}; they must share one derivation")

    def mark_of(lines: list[str], vintage: str) -> set[str]:
        """Which mark KIND each surface put on a given vintage — the derivation, not the count."""
        kinds = set()
        for x in lines:
            for m in ("[CURRENT GUIDE, filed ", "[SUPERSEDED — filed "):
                if m in x and x.split(m)[1].startswith(vintage):
                    kinds.add(m)
        return kinds

    for v in marks(brief):
        assert mark_of(tmpl, v) == mark_of(brief, v), (
            f"template and brief mark vintage {v} differently — template {mark_of(tmpl, v)}, "
            f"brief {mark_of(brief, v)}; a guide current on one surface and superseded on the "
            f"other is the P2 defect in a new place")

    # …and anything the brief leaves out must be DISCLOSED, or its window reads as the whole record.
    if marks(brief) < marks(tmpl):
        assert any("omitted from the" in x for x in _digest("SMPL").splitlines()), (
            "the brief dropped a guidance vintage without saying so")
    # Derived, not typed in — same reason as the acceptance case above: hardcoding the July/April
    # figures schedules this to redden on SMPL's next print rather than on a defect.
    ps = Dossier.model_validate(doc).mechanical.primary_source
    assert ps is not None
    dated = sorted({r.filed for r in ps.releases if r.guidance and r.filed})
    assert len(dated) >= 2, "SMPL no longer shows a supersession — re-point this test"
    blob = " ".join(tmpl)
    assert f"[CURRENT GUIDE, filed {dated[-1]}]" in blob, blob[:200]
    for on, why in ((dated[-1], "the current guide"), (dated[0], "the older guide")):
        for rel in (x for x in ps.releases if x.filed == on):
            for g in rel.guidance or []:
                if g.qualitative:
                    continue
                assert f"{g.low}–{g.high}" in blob, (
                    f"{why} ({on}) value {g.low}–{g.high} is missing from the template — "
                    "dropped rather than marked")
    assert "current guidance:" not in " ".join(build_template(doc)["_evidence"]["revenue"]), (
        "the old unmarked 'current guidance:' line is back")


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_the_drawdown_moment_guide_is_marked_too_o1() -> None:
    """THE SECOND PATH, closed. #342 marked the `primary_source` digest and the 2026-08-04 SMPL
    roll argued the FY26 guide from APRIL anyway — because the model was reading a DIFFERENT field.

    `synthesize` excludes `primary_source` from the facts dump and swaps in the marked digest,
    while `drawdown_cause` goes into that dump RAW. On SMPL it carries April's verbatim outlook,
    and `bear[1]`'s `-22% to -19%` appears ONLY there — never in the structured guidance. So the
    brief was marked on one of two paths, which is why marking changed nothing.

    Asserted on the DUMP the model actually receives, not on the helper: the defect was that a
    correct helper was never applied to this field, and a test that called the helper directly
    would have passed throughout."""
    from vinci.dossier.synthesis import _mark_drawdown_guidance
    d = Dossier.model_validate(json.loads((DOSS / "SMPL" / "dossier.json").read_text()))
    ps = d.mechanical.primary_source
    assert ps is not None
    dumped = d.mechanical.model_dump(exclude={"primary_source"})
    raw = ((dumped.get("drawdown_cause") or {}).get("revised_guidance") or {}).get("value")
    assert raw, "SMPL's drawdown_cause carries no revised_guidance — re-point this test"
    assert not any(m in str(raw) for m in ("CURRENT GUIDE", "SUPERSEDED", "VINTAGE UNDATED")), (
        "the raw dump is already marked — this test can no longer show the mark being applied")

    _mark_drawdown_guidance(dumped, ps)
    marked = str(((dumped["drawdown_cause"]) or {})["revised_guidance"]["value"])
    newest = max(r.filed for r in ps.releases if r.guidance and r.filed)
    assert f"replaced by the guide filed {newest}" in marked, marked[-200:]
    assert "history, not the current outlook" in marked
    # MARK, NEVER DROP — the cut sequence is evidence, and the verbatim outlook must survive intact
    assert str(raw) in marked, "the guide's own text was altered rather than annotated"


def test_the_drawdown_mark_is_undated_rather_than_guessed_when_no_release_matches() -> None:
    """FAIL HONEST. The filing DATE is not on `revised_guidance` — only its accession is — so it is
    matched back to the release carrying one. No match ⇒ UNDATED, never a guessed vintage."""
    from vinci.dossier.synthesis import _mark_drawdown_guidance
    dumped = {"drawdown_cause": {"revised_guidance": {
        "value": "Outlook: net sales of $1 to $2 billion",
        "source_ref": "EDGAR 8-K 9999999999-99-999999 Ex-99.1"}}}
    _mark_drawdown_guidance(dumped, None)
    v = dumped["drawdown_cause"]["revised_guidance"]["value"]
    assert "VINTAGE UNDATED" in v and "do not read as current" in v, v


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_the_mark_reaches_the_prompt_synthesize_actually_builds() -> None:
    """THE CALL SITE, not the helper — and this file needed it because the first cut of the pin
    above called `_mark_drawdown_guidance` ITSELF.

    Deleting the one line in `synthesize` that applies it left every other test in this file GREEN,
    measured. That is the #345 defect exactly — the extractor exposes a value, a consumer reads it,
    and nothing checks the step between — repeated one PR after it was found and named. It is worth
    the fake client to close, because the failure is silent: an unmarked brief looks identical to a
    marked one from anywhere except the prompt.

    So this asserts on the STRING THE MODEL RECEIVES, obtained by running `synthesize` with a
    client that captures its `user` payload."""
    from typing import Any

    from vinci.dossier.synthesis import synthesize
    from vinci.graph.llm import LlmClient

    class _Capture(LlmClient):
        def __init__(self) -> None:
            self.user: str | None = None

        def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
            self.user = user
            return {}                     # incomplete -> synthesize returns None, which is fine

        @property
        def model(self) -> str:
            return "capture"

    d = Dossier.model_validate(json.loads((DOSS / "SMPL" / "dossier.json").read_text()))
    ps = d.mechanical.primary_source
    assert ps is not None
    cap = _Capture()
    synthesize(d.mechanical, llm=cap, ticker="SMPL", name="Simply Good Foods")
    assert cap.user, "synthesize built no user prompt"

    newest = max(r.filed for r in ps.releases if r.guidance and r.filed)
    assert f"replaced by the guide filed {newest}" in cap.user, (
        "the drawdown-moment guide reaches the model UNMARKED — `_mark_drawdown_guidance` is "
        "defined but never applied, which is invisible from every other test in this file")
    # and it must LEAD the block, so the vintage is read before the numbers it qualifies
    body = cap.user[cap.user.index("revised_guidance"):][:1400]
    mark_at = body.find("SUPERSEDED")
    pct_at = body.find("-10% to -7%")
    if pct_at != -1:
        assert mark_at != -1 and mark_at < pct_at, (
            "the mark trails the numbers it qualifies — a reader meets April's guide first, which "
            "is how it became a bear point")


def test_the_cap_never_spends_a_slot_on_a_guidanceless_release() -> None:
    """THE DEFECT THIS PR FIXES, pinned on the fleet rather than one name.

    The digest capped the RAW release list (`ps.releases[:4]`), so a release carrying no guidance
    could occupy a slot while a guidance-bearing one fell outside it. Measured on the committed
    artifacts when this was found: **AORT and CNXC each lost one guidance-bearing release and NCNO
    lost two**, and the note said only "older release(s) omitted" — never that any of them carried
    a guide. That defeats the mark's own stated purpose ("the guidance history IS a bear point …
    superseded releases stay in the digest"): the digest was dropping the evidence it exists to
    preserve, and the cut sequence a bear case rests on can disappear without a word.

    THE INVARIANT: the guide window holds the most recent guidance-bearing releases, up to its own
    cap — never fewer because a guidance-less neighbour was newer.
    """
    from vinci.dossier.synthesis import _primary_source_digest

    thin: list[tuple[str, int, int]] = []
    for p in sorted(DOSS.iterdir()):
        doc = p / "dossier.json"
        if not doc.is_file():
            continue
        ps = Dossier.model_validate(json.loads(doc.read_text())).mechanical.primary_source
        if ps is None:
            continue
        bearing = [r for r in ps.releases if r.guidance and r.filed]
        if not bearing:
            continue
        shown = {ln.split("filed ")[1].split("]")[0].split(",")[0]
                 for ln in _primary_source_digest(ps).splitlines()
                 if ln.startswith("guidance (") and "filed " in ln}
        expect = {str(r.filed) for r in bearing[:4] if r.filed}  # `filed` is a date; marks are text
        if not expect <= shown:
            thin.append((p.name, len(shown), len(expect)))
    assert not thin, (
        f"the digest dropped guidance-bearing releases that sit inside the guide window: {thin} — "
        f"a slot went to a release with no guidance while a guide fell out of the digest")
