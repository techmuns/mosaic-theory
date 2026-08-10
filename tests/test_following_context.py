"""A verbatim quote can be exact, cited and digit-traceable — and still argue against its source.

THE CLASS (STATE §B1a). BRBR's driver row quoted *"In the third quarter, 70% of RTD shake category
volumes were sold on price promotion."* Every guard we have passes it, because every guard takes the
QUOTED TEXT as the check: quote-in-transcript, digit-trace, 19c's citation requirement. The sentence
the extraction did not take says the figure is *"relatively in line with historical norms … while
down sequentially from the heavier promoted second quarter."* The synthesis then built a bear point
arguing an escalating promotion sequence its own source contradicts.

WHY THERE IS NO CLASSIFIER, AND IT WAS MEASURED. Splitting the 13 severed rows by opener: 5 follow
with a reversing connective, 10 with a continuing one — and **BRBR's reversal is in the continuing
bucket**, opening with *"This is"*, exactly like VRRM's *"This is a great indication that safety
measures are working."* Identical syntax, opposite function. A connective regex calls the one case
that bit us benign, so the context is carried UNCONDITIONALLY: the moment a rule decides which rows
deserve it, the text-criterion judgment is back.

WHY A PARAGRAPH AND NOT N SENTENCES. A 26-row hand sample found the reading-changing context beyond
the next sentence in 4 of 7 cases. Over all 191 rows: +1 sentence costs 90% of the verbatim payload,
+2 186%, +3 279%, PARAGRAPH 161% — and the paragraph is the only bound that crosses ZERO call
boundaries, because a blank line precedes every `--- <call> ---` header. Sentence bounds splice a
different transcript onto 1-3 rows (EPAM's Nelnet quote picks up the Q4 2025 call's opening).
"""
from __future__ import annotations

from vinci.dossier.driver_extract import _CONTEXT_MAX, _following_paragraph

# The real BRBR passage — the quote that is already committed in `dossier.json`, plus the sentence
# that reverses it. Corpus before synthetic: this is the text the defect was found in.
BRBR_QUOTE = ("In the third quarter, 70% of RTD shake category volumes were sold on price "
              "promotion.")
BRBR_PARA = (
    "Household penetration continues to grow for both the protein shake category and Premier "
    "shakes.\n\n"
    f"{BRBR_QUOTE} This is relatively in line with historical norms for this period after "
    "adjusting for the shift of a major e-commerce promotion, while down sequentially from the "
    "heavier promoted second quarter.\n\n"
    "Turning to innovation.")


def test_the_qualifier_that_reverses_the_reading_is_captured() -> None:
    """THE CASE THAT STARTED THIS. Without the continuation, 70% reads as escalation; with it, the
    source says the figure is seasonally normal and DOWN sequentially."""
    ctx = _following_paragraph(BRBR_QUOTE, BRBR_PARA)
    assert ctx is not None
    assert "in line with historical norms" in ctx
    assert "down sequentially" in ctx
    assert "Turning to innovation" not in ctx, "ran past the paragraph into the next section"


def test_a_benign_continuation_is_carried_too_because_nothing_classifies() -> None:
    """THE DESIGN PIN. VRRM's shape: the next sentence opens with the SAME connective as BRBR's
    reversal and merely amplifies. It must still be carried — a rule that kept only the reversing
    ones is the criterion we refuse to invent, and it would drop BRBR's."""
    q = "Traffic fatalities decreased significantly in 2025 by more than 6%."
    tail = "This is a great indication that safety measures are working."
    assert _following_paragraph(q, f"{q} {tail}") == tail


def test_the_context_never_runs_into_the_next_call() -> None:
    """MEASURED HAZARD, not hypothetical: EPAM's Nelnet quote sits at the end of one call, and a
    sentence-bounded rule spliced the NEXT call's opening remarks onto it. The paragraph bound is
    safe because a blank line precedes every header — this pins the explicit clamp as well."""
    q = "We continue working with Nelnet to expand the PDLC program."
    text = (f"{q} And that program is scaling.\n\n"
            "--- EPAM Systems, Inc., Q4 2025 Earnings Call, Feb 19, 2026.rtf ---\n\n"
            "Good morning, everyone and thank you for joining us today.")
    ctx = _following_paragraph(q, text)
    assert ctx == "And that program is scaling."
    assert "Earnings Call" not in (ctx or ""), "spliced a different transcript onto the quote"
    assert "Good morning" not in (ctx or "")


def test_a_header_with_no_blank_line_before_it_is_still_clamped() -> None:
    """THE BELT-AND-BRACES HALF. The paragraph bound happens to be safe on today's corpus; the
    explicit `_CALL_HEADER` split is what keeps it safe if a slice is ever emitted without the
    blank line, which is a formatting detail no guard controls."""
    q = "Revenue grew 6%."
    text = f"{q} Margins held. --- Acme Inc., Q1 2026 Earnings Call, Jan 02, 2026.rtf --- Welcome."
    ctx = _following_paragraph(q, text)
    assert ctx == "Margins held."


def test_a_quote_that_ends_its_paragraph_yields_nothing_rather_than_the_next_one() -> None:
    """`None` and a wrong paragraph are very different. Reaching forward past a blank line would
    attach an unrelated speaker's words as though they qualified this fact."""
    q = "Net sales declined 6.3% to $357 million."
    assert _following_paragraph(q, f"{q}\n\nGross margin declined 390 basis points.") is None


def test_an_unlocatable_quote_fails_soft_and_costs_no_row() -> None:
    """FAIL-SOFT HERE, DELIBERATELY. The row is already validated — the caller DROPS it when the
    quote is not in the slice — so a locate-miss at this later step is a whitespace artefact, and
    raising would cost a real driver row for a purely additive field."""
    assert _following_paragraph("A sentence not present.", "Some other transcript.") is None
    assert _following_paragraph("", "text") is None
    assert _following_paragraph("q", "") is None


def test_whitespace_differences_between_the_llm_quote_and_the_source_still_locate() -> None:
    """The quote comes back from an LLM and its whitespace need not match the source byte-for-byte;
    the containment check upstream normalises, so this must too or context silently vanishes on
    every line-wrapped quote."""
    ctx = _following_paragraph("Revenue grew   6%\n  this quarter.",
                               "Revenue grew 6% this quarter. But margins fell.")
    assert ctx == "But margins fell."


def test_a_re_wrapped_quote_still_stops_at_its_own_paragraph() -> None:
    """REVIEW FINDING, and the version of this test above is why it was needed.

    Locating a re-wrapped quote once took a separate code path that matched on FLATTENED text — and
    flattening is exactly what destroys the paragraph breaks the bound depends on. That path
    returned up to `_CONTEXT_MAX` of running text, splicing later paragraphs and other speakers
    onto the fact as though they qualified it. It never fired on the corpus (191/191 matched raw)
    and the test above passed on it, because its fixture is ONE SHORT PARAGRAPH — too small to show
    the difference. The fixture was shaped to the assertion.

    Same input shape, a fixture large enough to tell the two behaviours apart."""
    q = "Revenue grew   6%\n  this quarter."
    src = ("Revenue grew 6% this quarter. Margins held.\n\n"
           "A DIFFERENT SPEAKER answering a different question entirely.\n\n"
           "And a third paragraph nobody quoted.")
    assert _following_paragraph(q, src) == "Margins held."


def test_a_slice_with_no_paragraph_breaks_is_bounded_rather_than_returning_everything() -> None:
    """A malformed slice would otherwise hand one row the entire transcript as its 'paragraph'."""
    q = "Revenue grew 6%."
    ctx = _following_paragraph(q, q + " " + ("filler sentence. " * 400))
    assert ctx is not None and len(ctx) <= _CONTEXT_MAX


def test_the_synthesis_digest_puts_the_context_beside_the_fact() -> None:
    """CARRYING IT IS NOT ENOUGH — the LLM already had the whole transcript and still built the
    wrong sequence from the quote alone, because the DIGEST is what it is told to ground in. If
    this only reached `dossier.json` it would serve the audit and change no synthesis."""
    from vinci.dossier.schemas import DriverKind, OperatingDriver, OperatingDriversExtract
    from vinci.dossier.synthesis import _operating_drivers_digest

    od = OperatingDriversExtract(rows=[OperatingDriver(
        kind=DriverKind.LEADING_INDICATOR, metric="RTD shake volumes on promotion",
        period="Q3 2026", value="70%", verbatim=BRBR_QUOTE,
        following_context="This is relatively in line with historical norms for this period.",
        source_ref="CIQ transcript: BellRing Q3 2026", tier="llm-fenced")])
    digest = _operating_drivers_digest(od)
    assert "…continues: This is relatively in line with historical norms" in digest
    assert "read it before characterising the fact above it" in digest, (
        "the header must tell the model what a continues-line is for, or it reads as noise")


def test_a_row_without_context_emits_no_continues_line() -> None:
    """THE NEGATIVE HALF. Anchored (filing) rows have no transcript paragraph, and an empty
    '…continues:' line would read as 'the source said nothing further', which is not a fact."""
    from vinci.dossier.schemas import DriverKind, OperatingDriver, OperatingDriversExtract
    from vinci.dossier.synthesis import _operating_drivers_digest

    od = OperatingDriversExtract(rows=[OperatingDriver(
        kind=DriverKind.LEADING_INDICATOR, metric="revenue", period="Q1", value="$1M",
        verbatim="Revenue was $1M.", source_ref="0001-ex99", tier="anchored")])
    # Scoped to the ROW lines: the digest HEADER explains what a continues-line is, so a
    # whole-string check matches the documentation rather than the data.
    rows = [ln for ln in _operating_drivers_digest(od).splitlines() if not ln.startswith("===")]
    assert not any("…continues:" in ln for ln in rows)


def test_a_quote_at_the_very_end_of_the_slice_returns_none_rather_than_raising() -> None:
    """REVIEW FINDING — the bounds guard was unpinned and survived mutation. The last driver on a
    call can quote its final sentence, and without the guard the index map is read one past its end
    and raises IndexError straight into the extraction, costing every row on that name."""
    q = "And that concludes our prepared remarks."
    assert _following_paragraph(q, f"Some earlier text. {q}") is None
    assert _following_paragraph(q, q) is None
