"""GUIDANCE EXTRACTION — the four failure modes found by the 51-item audit (2026-07-29).

THE AUDIT. Reading every guidance item in the committed fleet — 51 items, 11 names — found that
the extraction is NOT manufacturing guidance wholesale: 49 of 51 are genuine filing statements.
But 11 of those 49 carried a WRONG FIELD, which the coverage number hid. #254's "11 of 11 gain a
current guide" counted one fabricated (IT) and one unusable (AORT).

Two were live on the deployed page and both were wrong MAGNITUDES, not omissions:
  * CNXC — a single QUARTER's guide rendered `Fiscal 2026 revenue outlook: $2,465.0–$2,490.0M`
    on a business annualising ~$9.9bn;
  * VRRM — adjusted EPS of $1.19–$1.25 PER SHARE rendered `$1.2–$1.2M`.

FIXTURES ARE FROZEN SENTENCES, deliberately. Each is the real verbatim from a committed item, so a
value-level pin is legitimate here (the TEST-LAYER rule reserves those for frozen fixtures) and the
output is deterministic regex work, never LLM-composed.

THE MUST-SURVIVE CONTROLS AT THE BOTTOM ARE NOT DECORATION. A first cut of this fix used a
`[^.$•]{0,60}?` wildcard between a metric and its range; the per-item table over all 51 caught it
binding VITL's revenue guide to the adjusted-EBITDA range (900–920 became 105–115) and EPAM's to a
prior year's (4.5–7.5 became 14.8–15.2) — the same wrong-magnitude class this file exists to
remove, introduced by its own fix.
"""
from __future__ import annotations

import pytest

from vinci.dossier.flags import is_qa, partition
from vinci.dossier.mechanical import _fmt_guide_range, guidance_refusal_flags
from vinci.dossier.schemas import GUIDANCE_UNITS, GuidanceItem
from vinci.edgar.release_parse import GUIDANCE_REFUSAL_PREFIX, _guidance


def parse(sentence: str) -> list[GuidanceItem]:
    """Parse one sentence. The leading '. ' restores the boundary `_verbatim` snaps back to — in a
    real filing the sentence is never the first thing in the document, and without it the helper
    clips the sentence head (which is where the period usually lives)."""
    return _guidance(". " + sentence, "8-K test EX-99.1")


# --- MODE 1: boilerplate accepted as guidance ---------------------------------------------------

IT_BOILERPLATE = (
    "(NYSE: IT) today reported results for the first quarter of 2026 and updated its financial "
    "outlook for the full year 2026. Additional information regarding revenue follows."
)


def test_a_results_announcement_is_not_an_outlook() -> None:
    """Gartner's opener matched the outlook pattern on the phrase "financial outlook" while
    stating NO outlook. It produced TWO qualitative revenue guides — the whole of IT's guidance,
    fabricated, and `current_guide` rendered one as the company's current revenue guide.

    IT has ZERO numeric guidance items, so there was nothing truer to fall back to: the honest
    output is nothing at all."""
    assert parse(IT_BOILERPLATE) == []


def test_a_real_qualitative_outlook_still_survives() -> None:
    """THE CONTROL for mode 1, and it is the one that keeps the guard from becoming a mute button.
    Microvast states a genuine forward view with no figure; that is a real fact and must survive."""
    got = parse("2026 Outlook & Forward-Looking Information While we navigate tariffs, we expect "
                "continued revenue growth in 2026 and anticipate a recovery in delivery schedules.")
    assert len(got) == 1
    assert got[0].qualitative is True and got[0].metric == "revenue"


# --- MODE 2: real guidance mis-typed qualitative ------------------------------------------------

AORT_RANGE = (
    "Page 2 of 13 2026 Financial Outlooks Artivion expects revenues for the full year 2026 to be "
    "in the range of $486 to $504 million, representing growth of 10% to 14%."
)


def test_a_range_stated_across_a_period_year_is_read_as_a_number() -> None:
    """The qualitative fallback tested for a figure with `revenue\\D{0,40}\\$`, which REQUIRES
    non-digits between the metric and its number — so the period year defeated it: "revenues for
    the full year **2026** to be in the range of $486 to $504 million" read as having no number.

    The range was in the sentence the whole time. It was discarded, marked qualitative, and then
    truncated away by the renderer's 110-char cap at "$4…"."""
    got = parse(AORT_RANGE)
    assert len(got) == 1
    g = got[0]
    assert g.qualitative is False, "a stated range was still recorded as qualitative"
    assert (g.low, g.high) == (486.0, 504.0)
    assert g.unit == "$M"


# --- MODE 3: field mis-assignment on correctly-detected guidance --------------------------------


def test_two_metrics_sharing_one_range_are_refused_not_guessed() -> None:
    """BellRing writes "Fiscal year 2026 net sales and Adjusted EBITDA* expected to range between
    $2.41-$2.49 billion" — TWO metrics, ONE range. The pattern bound it to whichever sat nearer
    the introducer and recorded an ADJUSTED EBITDA guide of $2,410–2,490M against a business
    earning ~$490M: a ~5x error, stated confidently.

    A reader cannot resolve that sentence either. Refusing is the only honest answer."""
    assert parse("Fiscal year 2026 net sales and Adjusted EBITDA* expected to range between "
                 "$2.41-$2.49 billion") == []


def test_the_refusal_is_visible_and_attributed_never_silent() -> None:
    """REVIEW FINDING (operator, before merge). Refusing the sentence was right; DROPPING it
    silently was item 22's exact prohibition — "we found guidance we could not parse safely" is a
    different fact from "this release states no guidance", and a reader whose guidance picture is
    incomplete needs to know which one they have.

    The note must carry the SENTENCE and the ACCESSION, so the reader can resolve from the filing
    what the parser would not guess at."""
    notes: list[str] = []
    src = "8-K 0001772016-26-000045 EX-99.1"
    got = _guidance(". Fiscal year 2026 net sales and Adjusted EBITDA* expected to range between "
                    "$2.41-$2.49 billion", src, notes)
    assert got == []
    assert len(notes) == 1, "the refusal left no trace"
    n = notes[0]
    assert "not attributable" in n
    assert "net sales" in n and "adjusted ebitda" in n, "the note must name the competing metrics"
    assert "$2.41-$2.49 billion" in n, "the note must carry the sentence the reader must resolve"
    assert src in n, "the note must be source-bound"


def test_the_refusal_reaches_the_reader_not_only_the_json() -> None:
    """`qa_flags` is the machine tier by design ("dev/JSON only"), and a release's own flags roll
    up nowhere — so a note filed there would still be invisible on every surface. The partition
    sends anything off the QA hide-list to the human caveat channel; this pins that routing."""
    notes: list[str] = []
    _guidance(". Fiscal year 2026 net sales and Adjusted EBITDA* expected to range between "
              "$2.41-$2.49 billion", "8-K x", notes)
    assert not is_qa(notes[0]), "the refusal was routed to the machine-only tier"
    caveats, qa = partition(notes)
    assert len(caveats) == 1 and qa == []


def test_a_refused_release_is_not_also_reported_as_stating_no_guidance() -> None:
    """The two facts are mutually exclusive. A release whose guidance was found and refused DOES
    state guidance — emitting `no anchored pattern matched` beside the refusal would be the
    false-UNKNOWN shape, asserting absence where the parser saw a number."""
    from vinci.edgar.release_parse import _guidance as g

    notes: list[str] = []
    g(". Fiscal year 2026 net sales and Adjusted EBITDA* expected to range between "
      "$2.41-$2.49 billion", "8-K x", notes)
    assert notes and not any("no anchored pattern matched" in n for n in notes)


def test_the_rollup_lifts_refusals_and_only_refusals() -> None:
    """The routing's own red. Refusals must be lifted off the releases into the dossier flags; the
    sibling "no anchored pattern matched" flags must NOT be — those say a release stated no
    guidance, which is ordinary across the fleet, and promoting them would drown the channel and
    make the real refusals harder to see."""
    from vinci.dossier.schemas import ReleaseExtract

    def rel(*flags: str) -> ReleaseExtract:
        return ReleaseExtract(source_ref="8-K x", guidance=[], reconciliation=[], one_offs=[],
                              event_impacts=[], qa_flags=list(flags))

    got = guidance_refusal_flags([
        rel(f"{GUIDANCE_REFUSAL_PREFIX} — one range is shared by 2 metrics …"),
        rel("no anchored pattern matched — guidance/outlook: 8-K y"),
    ])
    assert len(got) == 1 and got[0].startswith(GUIDANCE_REFUSAL_PREFIX)


def test_a_ratio_is_not_a_level() -> None:
    """"Adjusted EBITDA as a percentage of net sales of 18% to 20" bound the range to its
    DENOMINATOR and printed "net sales $18–20M" — off by ~130x, and the wrong metric besides."""
    assert parse("Adjusted EBITDA as a percentage of net sales of 18% to 20") == []


def test_a_quarterly_guide_is_not_labelled_a_full_year() -> None:
    """LIVE ON THE DEPLOYED PAGE. Concentrix guides a QUARTER; the period came from a forward scan
    that found the fiscal year, so `Fiscal 2026 revenue outlook: $2,465.0–$2,490.0M` rendered as a
    full-year guide on a business annualising ~$9.9bn — a ~4x error a reader would take as a
    collapse."""
    got = parse("Third quarter reported revenue of $2.465 billion to $2.490 billion")
    assert len(got) == 1
    assert got[0].period.startswith("Q3"), f"period is {got[0].period!r}"
    assert (got[0].low, got[0].high) == (2465.0, 2490.0), "the billions scaling must be preserved"


def test_the_period_comes_from_the_guide_s_own_sentence() -> None:
    """fuboTV's bullet says "Fiscal 2026 Pro Forma Adjusted EBITDA of $80-100 million" and was
    labelled **Fiscal 2028** — the forward scan crossed into a later bullet. Two years off."""
    got = parse("We currently expect: Fiscal 2026 Pro Forma Adjusted EBITDA of $80-100 million")
    assert len(got) == 1
    assert "2026" in got[0].period and "2028" not in got[0].period


# --- MODE 4: the unit vocabulary could not express $/sh -----------------------------------------


def test_the_unit_vocabulary_can_express_dollars_per_share() -> None:
    """THE ROOT. `unit` held "$M" | "%" over a THREE-value reality, and the field's own docstring
    recorded the third in prose ("$M; $/sh for EPS") — encoding a unit in the METRIC NAME where no
    formatter reads it. Every new metric inherited the wrong default."""
    assert "$/sh" in GUIDANCE_UNITS


def test_an_unlisted_unit_is_refused() -> None:
    """The negative pin, on the BEAR_BASES precedent: a value claiming an unformattable unit is
    worse than an absent one."""
    with pytest.raises(ValueError, match="not one of"):
        GuidanceItem(metric="revenue", period="2026", low=1.0, high=2.0, unit="EUR",
                     qualitative=False, verbatim="v", source_ref="s")


def test_a_per_share_guide_is_typed_per_share() -> None:
    got = parse("Adjusted EPS of $1.19 to $1.25")
    assert len(got) == 1 and got[0].unit == "$/sh"


@pytest.mark.parametrize(
    ("low", "high", "unit", "expect"),
    [
        (1.19, 1.25, "$/sh", "$1.19–$1.25/sh"),   # was "$1.2–$1.2M": wrong unit AND zero width
        (1.30, 1.35, "$/sh", "$1.30–$1.35/sh"),   # was "$1.3–$1.4M"
        (985.0, 995.0, "$M", "$985.0–$995.0M"),   # unchanged — the common case must not move
        (4.5, 7.5, "%", "4.5–7.5% growth"),       # unchanged
    ],
)
def test_the_formatter_is_unit_aware_and_precision_aware(
    low: float, high: float, unit: str, expect: str,
) -> None:
    """TWO defects from one root, and fixing either alone still prints a wrong number: the unit
    (off by 1e6) and the precision (`.1f` collapsed 1.19–1.25 to a ZERO-WIDTH "$1.2–$1.2", which
    reads as a point estimate the company never gave)."""
    assert _fmt_guide_range(low, high, unit) == expect


def test_precision_widens_when_the_base_would_collapse_the_range() -> None:
    """THE WIDENING'S OWN RED — added because the first cut of this file did not exercise it at all.
    `$/sh` at 2dp already separates 1.19 from 1.25, so the VRRM case passes on the base precision
    alone. A $M range whose bounds differ in the SECOND decimal is where the loop earns its place:
    without it this prints "$140.2–$140.2M", the zero-width range that started mode 4, in the unit
    that carries most of the corpus."""
    assert _fmt_guide_range(140.21, 140.24, "$M") == "$140.21–$140.24M"


def test_precision_widens_only_as_far_as_it_must() -> None:
    """A range whose bounds already differ must NOT gain spurious digits — the widening is driven
    by the values, not applied uniformly, and equal bounds must not run away."""
    assert _fmt_guide_range(140.0, 150.0, "$M") == "$140.0–$150.0M"
    assert _fmt_guide_range(2.0, 2.0, "$/sh") == "$2.00–$2.00/sh"


# --- CONTROLS: the 40 clean items must not move -------------------------------------------------


@pytest.mark.parametrize(
    ("sentence", "metric", "low", "high", "unit"),
    [
        ("Updated fiscal year 2026 net sales outlook of $2.325-$2.365 billion",
         "net sales", 2325.0, 2365.0, "$M"),
        ("Total revenues between $157.75 million and $159.75 million",
         "revenue", 157.75, 159.75, "$M"),
        ("Net sales expected to range between $1.345 and $1.355 billion",
         "net sales", 1345.0, 1355.0, "$M"),
        ("Net revenue of $775 million to $800 million", "revenue", 775.0, 800.0, "$M"),
        ("Free Cash Flow of $140 million to $150 million",
         "free cash flow", 140.0, 150.0, "$M"),
        ("Total Revenue of $1,020 million to $1,030 million", "revenue", 1020.0, 1030.0, "$M"),
    ],
)
def test_clean_items_are_unchanged(
    sentence: str, metric: str, low: float, high: float, unit: str,
) -> None:
    """40 of 51 items were already correct. A fix that repairs 11 and breaks any of these is not a
    fix — and the wildcard-gap first cut broke two of them, which is why these are pinned."""
    got = parse(sentence)
    assert len(got) == 1, f"{sentence!r} -> {got}"
    g = got[0]
    assert (g.metric, g.low, g.high, g.unit) == (metric, low, high, unit)
