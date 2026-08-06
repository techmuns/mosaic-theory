"""A guide can state a LEVEL or a CHANGE, and the two are never confused.

WHY. `GuidanceItem` could only express a level, so every change guide was dropped: ten of seventeen
dropped clauses across four names, including all four of SMPL's basis-point gross-margin guides —
the metric its own kill criteria test. `375` appeared ZERO times in the dossier while sitting
verbatim in the filing the record cites.

THE FAILURE MODE THIS EXISTS TO PREVENT is not the drop, it is the careless fix. Capturing
"decline between 300 and 350 basis points" without a basis field stores `low=300 high=350 unit="%"`
— a gross margin of 300–350%, a 100x error in a decision figure. This parser has already been fixed
twice for exactly that class (Concentrix billions-as-millions; BellRing's shared range binding a
$2.4bn revenue figure to a ~$490M EBITDA line), and its own rule is that a magnitude error is worse
than an absent one.

THE SENTENCES BELOW ARE FROZEN FIXTURES, quoted verbatim from filed 8-Ks. Filing text is immutable,
so these are value pins that cannot rot — unlike a pin on a re-drawn artifact.
"""
from __future__ import annotations

import pytest

from vinci.dossier.schemas import GuidanceItem
from vinci.edgar.primary_source import guide_verification
from vinci.edgar.release_parse import _guidance


def _one(text: str) -> GuidanceItem:
    got = _guidance(text, "8-K test")
    assert len(got) == 1, f"expected exactly one guide, got {[(g.metric, g.low) for g in got]}"
    return got[0]


@pytest.mark.parametrize(
    ("sentence", "metric", "low", "high", "unit"),
    [
        # SMPL 2026-07-09 — the guide its kill criteria test, and the reason this exists
        ("Gross margins expected to decline approximately 375 basis points year-over-year",
         "gross margin", -375.0, -375.0, "bps"),
        # SMPL 2026-04-09 — two-sided, and the range must come back LOW-first after negation
        ("Gross margins expected to decline between 300 and 350 basis points year-over-year",
         "gross margin", -350.0, -300.0, "bps"),
        # SMPL 2026-01-08 — signed percentages, no direction word; the signs carry it
        ("Net sales expected to range between -2% and +2% year-over-year",
         "net sales", -2.0, 2.0, "%"),
        # SMPL 2025-07-10 — an INCREASE stays positive
        ("Adjusted EBITDA expected to increase 4% to 5%", "adjusted ebitda", 4.0, 5.0, "%"),
        # SMPL 2025-07-10 — "decline BY approximately", a different connective
        ("In addition, the Company is maintaining its outlook for full year gross margin to "
         "decline by approximately 200 basis points year-over-year",
         "gross margin", -200.0, -200.0, "bps"),
    ],
)
def test_the_change_shapes_capture_with_the_right_sign_and_unit(
        sentence: str, metric: str, low: float, high: float, unit: str) -> None:
    """EVERY ONE IS A REAL FILED SENTENCE. The sign is the load-bearing assertion: a decline stored
    positive reads as an expansion, which is the same class of wrong as storing it as a level."""
    g = _one(sentence)
    assert (g.metric, g.low, g.high, g.unit, g.basis) == (metric, low, high, unit, "change")
    assert g.low <= g.high, "a range must come back low-first — negation reverses the ends"
    assert not g.qualitative


def test_the_plural_is_matched_because_it_was_the_first_gate() -> None:
    """`gross\\s+margin` followed by `\\s*` cannot consume the `s` in "Gross marginS". SMPL's guide
    failed on the NOUN before any shape gap mattered, so singular and plural are both pinned."""
    for noun in ("Gross margin", "Gross margins"):
        g = _one(f"{noun} expected to decline approximately 375 basis points year-over-year")
        assert g.metric == "gross margin" and g.low == -375.0


def test_a_level_is_never_shadowed_by_a_change_in_the_same_release() -> None:
    """SMPL's July release states net sales as a LEVEL and gross margin as a CHANGE. Both must
    survive: a level is the stronger statement, and gating the change patterns on `seen` is what
    stops the weaker one overwriting it."""
    text = ("Updating Fiscal Year 2026 Outlook: "
            "Net sales expected to range between $1.345 and $1.355 billion, or a decline of "
            "roughly 7% to 6% year-over-year "
            "Gross margins expected to decline approximately 375 basis points year-over-year "
            "Adjusted EBITDA expected to range between $220 and $225 million")
    by = {g.metric: g for g in _guidance(text, "8-K")}
    assert by["net sales"].basis == "level" and by["net sales"].low == 1345.0
    assert by["adjusted ebitda"].basis == "level" and by["adjusted ebitda"].low == 220.0
    assert by["gross margin"].basis == "change" and by["gross margin"].unit == "bps"
    assert by["gross margin"].low == -375.0


def test_a_change_guide_is_never_cross_checked_against_a_level_guide() -> None:
    """THE REFUSAL. CIQ guides a level; the release can guide a change. Comparing -2..+2 against
    1,345..1,355 is meaningless, and DERIVING a level from the prior period would verify a
    filing-derived guide against a vendor-derived base whose definition need not match. Refusing
    loses nothing — before this the change guide was dropped entirely."""
    out = guide_verification("revenue", 1345.0, 1355.0,
                             release_low=-2.0, release_high=2.0, release_basis="change")
    assert "NOT CROSS-CHECKED" in out
    assert "LEVEL" in out and "CHANGE" in out
    assert "need not share a definition" in out, "the refusal must say WHY, not merely refuse"
    # ...and a LEVEL-basis release still cross-checks exactly as before
    same = guide_verification("revenue", 1345.0, 1355.0,
                              release_low=1345.0, release_high=1355.0, release_basis="level")
    assert "NOT CROSS-CHECKED" not in same


def test_both_consumers_label_a_change_rather_than_printing_it_like_a_level() -> None:
    """THE ARTIFACTS THE READER RECEIVES — the brief's digest line and the analyst's template — not
    the helpers that build them. "-350–-300" beside a "%" unit reads as a margin; the whole point of
    the basis field is that it stops being printable as one."""
    import datetime as dt

    from vinci.dossier.propose import evidence_for
    from vinci.dossier.schemas import PrimarySource, ReleaseExtract, Sourced
    from vinci.dossier.synthesis import _primary_source_digest

    change = GuidanceItem(metric="gross margin", period="2026", low=-350.0, high=-300.0,
                          unit="bps", basis="change", qualitative=False,
                          verbatim="Gross margins expected to decline between 300 and 350 bps",
                          source_ref="8-K X EX-99.1")
    unknown = Sourced.unknown(note="not under test")
    ps = PrimarySource(
        releases=[ReleaseExtract(filed=dt.date(2026, 7, 9), source_ref="8-K X EX-99.1",
                                 guidance=[change])],
        self_funding=unknown, wall_coherence=unknown, basis_triangulation=unknown,
        guide_verification=unknown)

    digest = _primary_source_digest(ps)
    assert "CHANGE of -350.0–-300.0 bps" in digest, digest
    assert "vs the prior period" in digest

    ev = evidence_for({"mechanical": {"primary_source": ps.model_dump(mode="json")}})
    line = next(x for x in ev["revenue"] if x.startswith("guidance ("))
    assert "CHANGE of -350.0–-300.0" in line, line


#: Committed guides whose verbatim is a GROWTH-RATE sentence but whose stored basis is still
#: "level" — extracted before the 2026-08-06 label fix and awaiting their name's re-assembly.
#:
#: **EMPTY.** It held EPAM's two guides for exactly one PR; re-assembling EPAM moved both to
#: `basis="change"` and the set shrank, which is the `ANCHORS_AWAITING_BACKFILL` contract working:
#: the artifacts are TRACKED rather than described. Kept as a declared set rather than deleted so
#: a name arriving in this state is a deliberate, explained addition rather than a quiet one.
GUIDES_AWAITING_REASSEMBLY: set[tuple[str, str]] = set()


def test_a_growth_rate_is_a_change_because_the_pattern_says_so_not_because_it_is_a_percent(
) -> None:
    """THE DISCRIMINATOR IS IN THE PATTERN, which is what makes the label safe rather than a guess.

    A bare `%` figure is genuinely ambiguous — "gross margin expected to be 29% to 30%" is a LEVEL
    in percent. `_GUIDE_PCT` cannot match that sentence: it requires the literal `growth rate`
    within 60 characters of the metric. So every match is a rate of change BY CONSTRUCTION, and
    labelling the whole path "change" cannot mislabel a level.

    Pinned on the PATTERN, not just the output: if the `growth rate` requirement were relaxed, the
    blanket label would silently start converting percent LEVELS into changes, and the output pins
    below would still pass."""
    import vinci.edgar.release_parse as rp

    assert "growth" in rp._GUIDE_PCT.pattern, (
        "`_GUIDE_PCT` no longer requires 'growth rate', so its blanket basis='change' is no longer "
        "sound — a percent LEVEL could now reach it and be relabelled a change")
    assert rp._GUIDE_PCT.search("Gross margin expected to be in the range of 29% to 30%") is None, (
        "a percent LEVEL reached the growth-rate path — it would be stored as a change")
    assert rp._GUIDE_PCT.search(
        "the year-over-year revenue growth rate to be in the range of 4.0% to 6.5%") is not None


@pytest.mark.parametrize(
    ("sentence", "low", "high"),
    [
        # EPAM 2026-05-07 8-K 0001352010-26-000026 EX-99.1 — the guide that manufactured the flag
        ("For the full year, EPAM now expects the year-over-year revenue growth rate to be in "
         "the range of 4.0% to 6.5%", 4.0, 6.5),
        # EPAM 2026-02-19 8-K 0001352010-26-000010 EX-99.1
        ("The Company expects the year-over-year revenue growth rate to be in the range of "
         "4.5% to 7.5%", 4.5, 7.5),
    ],
)
def test_the_filed_growth_rate_sentences_store_as_a_change(
        sentence: str, low: float, high: float) -> None:
    """FROZEN FIXTURES, quoted verbatim from filed 8-Ks — filing text is immutable, so these are
    value pins that cannot rot."""
    g = _one(sentence)
    assert (g.metric, g.low, g.high, g.unit, g.basis) == ("revenue", low, high, "%", "change")
    assert not g.qualitative


def test_the_refusal_now_fires_where_a_false_mismatch_was_manufactured() -> None:
    """THE WHOLE POINT, end to end on EPAM's REAL numbers.

    Before: `guide verification (revenue): CIQ 1400.0–1415.0 vs release 4.0–6.5 → MISMATCH flag` —
    a QUARTERLY LEVEL IN $M against a FULL-YEAR GROWTH RATE IN PERCENT, and the synthesis wrote a
    bear point on it. PR 2 built the refusal but gated it on `release_basis == "change"`, and the
    label said "level", so it never fired. The compare was fixed; the label is what let a change
    through it."""
    out = guide_verification("revenue", 1400.0, 1415.0,
                             release_low=4.0, release_high=6.5, release_basis="change")
    assert "NOT CROSS-CHECKED" in out and "MISMATCH" not in out, (
        f"the false MISMATCH survives: {out}")
    assert "LEVEL" in out and "CHANGE" in out


def test_a_growth_rate_stated_with_a_decline_word_is_refused_not_stored_positive() -> None:
    """THE SIGN HOLE THAT LABELLING THIS PATH A CHANGE OPENED.

    "the revenue growth rate to decline in the range of 2% to 3%" reads two ways — the rate
    declines TO +2..+3%, or it declines BY 2..3% — and the pattern captures bare digits, so it
    would store +2.0..+3.0 either way. While the path said "level" that was merely wrong; once it
    says "change" the sign is what the value MEANS, and "a decline stored positive reads as an
    expansion" is the error class this file exists to prevent.

    `_GUIDE_CHANGE_RANGE` reads the same word as unambiguously negative (`_DECLINE`). Accepting it
    positive here would put two parsers of one concept in contradiction — and this one runs FIRST,
    so it would shadow the other through `seen`. So: REFUSE, with the sentence attributed, the
    BellRing shared-range precedent.

    NOT LIVE — 0 committed guides match; this is the guard arriving before the instance."""
    import vinci.edgar.release_parse as rp

    notes: list[str] = []
    got = rp._guidance(
        "expects the revenue growth rate to decline in the range of 2% to 3%", "8-K X", notes)
    assert got == [], (
        f"a sign-ambiguous growth rate was stored anyway: {[(g.low, g.high) for g in got]}")
    assert len(notes) == 1 and notes[0].startswith(rp.GUIDANCE_REFUSAL_PREFIX)
    assert "opposite signs" in notes[0], "the refusal must say WHY, not merely refuse"
    assert "2% to 3%" in notes[0], "the refusal must carry the sentence so a reader can resolve it"
    # …and an unambiguous growth rate is still captured, so the guard is not a blanket refusal
    assert _one("net sales growth rate of 3% to 5%").basis == "change"


def test_a_dollar_level_is_untouched_by_the_growth_rate_label() -> None:
    """THE NEGATIVE. A guide stated as a LEVEL in dollars must stay a level — the growth-rate path
    must not widen into 'anything near the word growth'. EPAM's own November release states a $M
    level in a sentence that CONTAINS the word "growth" ("the strength of organic constant currency
    revenue growth … raises its outlook to $5,430 to $5,445 million"), which is exactly the sentence
    a phrase-sniffing implementation would have mislabelled."""
    g = _one("Net sales expected to range between $1.345 and $1.355 billion")
    assert (g.unit, g.basis) == ("$M", "level")
    assert g.low == 1345.0


def test_no_committed_guide_is_a_growth_rate_still_stored_as_a_level() -> None:
    """THE CORPUS, with the known-stale set recorded rather than assumed away.

    Every committed guide predates this fix, so the two EPAM growth-rate guides still read "level"
    until EPAM re-assembles. Recording them is the `ANCHORS_AWAITING_BACKFILL` precedent: the
    artifacts are TRACKED, so re-assembling EPAM shrinks this to empty and a NEW name arriving in
    this state reds the pin instead of passing unnoticed."""
    import json
    import pathlib

    import vinci.edgar.release_parse as rp

    root = pathlib.Path(__file__).resolve().parents[1]
    stale: set[tuple[str, str]] = set()
    checked = 0
    for p in sorted((root / "data" / "dossiers").glob("*/dossier.json")):
        ps = (json.loads(p.read_text())["mechanical"].get("primary_source")) or {}
        for r in ps.get("releases") or []:
            for g in r.get("guidance") or []:
                checked += 1
                if g.get("basis") == "level" and rp._GUIDE_PCT.search(g.get("verbatim") or ""):
                    stale.add((p.parent.name, str(r.get("filed"))))
    assert checked, "no committed guidance reached this sweep — it checked nothing"
    assert stale == GUIDES_AWAITING_REASSEMBLY, (
        f"growth-rate guides still stored as a level: {sorted(stale)}, recorded: "
        f"{sorted(GUIDES_AWAITING_REASSEMBLY)}. If a name re-assembled, shrink the set; if a NEW "
        "one appeared, a change is being cross-checked against a level somewhere.")


def test_the_basis_vocabulary_is_closed_and_bps_is_a_legal_unit() -> None:
    """A basis outside the set is refused at construction, the `GUIDANCE_UNITS` precedent: an
    unlisted value cannot be formatted, and a value claiming the wrong one is worse than absent."""
    ok = GuidanceItem(metric="gross margin", period="2026", low=-375.0, high=-375.0, unit="bps",
                      basis="change", qualitative=False, verbatim="v", source_ref="s")
    assert ok.unit == "bps"
    with pytest.raises(ValueError, match="not one of"):
        GuidanceItem(metric="revenue", period="2026", low=1.0, high=2.0, unit="$M",
                     basis="delta", qualitative=False, verbatim="v", source_ref="s")
    # DEFAULTS TO LEVEL, so every guide captured before 2026-08-05 keeps its meaning
    assert GuidanceItem(metric="revenue", period="2026", low=1.0, high=2.0, unit="$M",
                        qualitative=False, verbatim="v", source_ref="s").basis == "level"
