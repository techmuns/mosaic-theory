"""A verbatim that stops mid-word reads as the filer's own sentence ending there.

THE DEFECT, MEASURED ON THE LIVE CORPUS rather than argued. Across all 14 committed names' 10-Q
primary documents, `results_attribution` emits 40 rows — and the old 170/340 bounds cut **16 of
them mid-word, 40% of the corpus, on four names** (UBER 12, SMPL 2, MVST 1, VRRM 1). Four cuts
severed a dollar figure. The worst is UBER's: the sentence quantifying the UK model change ended at

    "…partially offset by business model changes in the UK that negatively impacted reven"

dropping `by $1.1 billion` — the number that explains why Mobility revenue grew 1% against Gross
Bookings up 22%. A reader of that page sees THAT the UK change hurt revenue and cannot see BY HOW
MUCH, while every quote-fidelity guard passes: the quoted text really is in the filing. It just is
not the whole claim.

WHY THE BOUNDS WERE WRONG AND NOT MERELY TIGHT. `_attr_verbatim` had three interacting limits and
the two that bit were invisible. The sentence-end SEARCH window (`cause_end + 170`) silently became
a raw offset cut whenever the real sentence ended later; then `frag[:340]` cut whatever survived.
Measured: cause→sentence-end runs to 477 (p50 138, p90 285) and the full fragment to 633 (p50 324,
p90 482). So 170 and 340 sat below the p90 of the thing they were bounding.

WIDENING IS SAFE FOR A STRUCTURAL REASON, not because the new numbers are bigger. `text.find(". ",
cause_end)` returns the FIRST sentence boundary after the cause, so the window only decides whether
that boundary is ACCEPTED or replaced by an offset cut — a wider window can never reach into a
second sentence. That is what these tests pin: the bound, and the fact that it stops at one
sentence.

THIS IS A DIFFERENT SEAT FROM THE BRBR FIX. BellRing's severed reversal was an `llm-fenced` row in
`driver_extract.py`, repaired by carrying the FOLLOWING paragraph (`_following_paragraph`). These
rows are `anchored` — deterministic regex extraction in `filing_sections.py` — and the paragraph
carry never widened this window, so a quote could still be cut mid-number before any context was
appended. Same defect class, two seats; neither fix covers the other.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from vinci.edgar.filing_sections import (
    _ATTR_SENTENCE_WINDOW,
    _ATTR_VERBATIM_CAP,
    _clip,
    results_attribution,
)

# The real UBER passage, verbatim from 10-Q 0001543151-26-000032 as `normalize_text(html_to_text())`
# renders it. CORPUS BEFORE SYNTHETIC: this is the text the defect was found in, not a shape built
# to the assertion. Long enough that the old 340 cap lands inside "revenue" — which is the point.
UBER_UK = (
    "Mobility revenue increased $75 million, or 1%, and Mobility Segment Operating Income "
    "increased $486 million, or 28%. Mobility revenue increased primarily attributable to an "
    "increase in Mobility Gross Bookings of 22%, driven by an increase in Trip volumes, partially "
    "offset by business model changes in the UK that negatively impacted revenue by $1.1 billion. "
    "Mobility Segment Operating Income increased primarily attributable to the revenue increase."
)


def _row(text: str) -> str:
    rows = results_attribution(text, source_ref="10-Q test")
    assert rows, "the extractor found no attribution row — the fixture stopped exercising it"
    return rows[0].verbatim


def test_the_uk_quantification_survives_the_bound() -> None:
    """THE CASE THAT STARTED THIS, end to end through the public extractor. The old bounds ended
    this row at "…impacted reven"; the figure is the whole reason the row is worth carrying."""
    vb = _row(UBER_UK)
    assert "$1.1 billion" in vb, f"the quantification was severed again: …{vb[-80:]}"
    assert vb.rstrip().endswith("."), f"the quote does not end at a sentence: …{vb[-60:]}"


def test_the_verbatim_stops_at_one_sentence_and_does_not_annex_the_next() -> None:
    """THE OTHER HALF, and the one a wider window could plausibly break. The passage continues with
    a SECOND sentence about Segment Operating Income; the row must not swallow it — a verbatim that
    runs on attributes a later claim to this magnitude."""
    vb = _row(UBER_UK)
    assert "Mobility Segment Operating Income increased primarily attributable to the revenue" \
        not in vb, "the verbatim ran past its own sentence into the next one"
    assert vb.count("$1.1 billion") == 1


def test_a_cut_that_still_has_to_happen_is_visible_rather_than_silent() -> None:
    """THE INVISIBILITY WAS THE DEFECT, not the length — so the remaining cases must announce
    themselves. No bound drawn from today's corpus can promise tomorrow's filings fit inside it."""
    assert _clip("alpha beta gamma delta", 12) == "alpha beta …"
    assert _clip("short", 100) == "short"
    assert _clip("alpha, beta, gamma", 8).endswith(" …"), "punctuation dangling before the mark"
    # and never mid-word
    out = _clip("supercalifragilistic expialidocious", 25)
    assert out == "supercalifragilistic …", out


def test_the_bounds_sit_above_the_measured_corpus_maxima() -> None:
    """THE NUMBERS ARE MEASURED, so the pin states what they were measured against. Observed maxima
    across 40 rows / 14 names: cause→sentence-end 477, full fragment 633. A later edit that
    tightens either below its maximum re-opens the exact defect, silently."""
    assert _ATTR_SENTENCE_WINDOW >= 477, "the window fell below the observed sentence-end distance"
    assert _ATTR_VERBATIM_CAP >= 633, "the cap fell below the observed fragment length"


def test_a_sentence_with_no_end_at_all_is_bounded_rather_than_taking_the_document() -> None:
    """A malformed slice — a table with no ". " anywhere after the cause — must not hand one row
    the rest of the filing. The window is the backstop, and the ellipsis says it fired."""
    runon = ("Revenue increased $5 million, or 3%, due to volume " + "and more volume " * 80)
    vb = _row(runon)
    assert len(vb) <= _ATTR_VERBATIM_CAP + 2, f"unbounded: {len(vb)} chars"
    assert vb.rstrip().endswith("…"), "an offset-bounded fragment did not mark itself as cut"


def test_the_leading_table_debris_strip_still_runs() -> None:
    """The pre-existing behaviour the cap change must not disturb: MD&A magnitudes are snapped out
    of table rows, so the fragment starts with cell noise that has to go."""
    noisy = ("4 % 94.9 % $ 1,490 Total revenue increased $50 million, or 4%, due to higher volume "
             "across the segment.")
    vb = _row(noisy)
    assert vb.startswith("Total revenue"), vb


# ─── the corpus itself, as an invariant ───────────────────────────────────────────────────────

@pytest.mark.skipif(not Path("data/dossiers").is_dir(), reason="no committed dossiers")
def test_no_committed_dossier_carries_a_mid_word_attribution_verbatim() -> None:
    """THE FLEET PIN, and it is the one that would have caught this. It reads the COMMITTED
    artifacts, so it fails until the artifact pass re-renders them — which is the intended
    coupling: the fix is not done while a severed quote is still on a page.

    Phrasing-independent by construction (TEST-LAYER RULE): it asserts that an anchored attribution
    quote ENDS somewhere a sentence can end, never that it contains any particular words."""
    import json

    bad: list[str] = []
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        blob = json.loads(p.read_text())
        for m in re.finditer(
            r'\{"kind": "attribution".*?"verbatim": "(.*?)", "following_context"',
            json.dumps(blob, ensure_ascii=False),
        ):
            vb = m.group(1).strip()
            if vb and not vb.endswith((".", "%", ")", "…", '"')):
                bad.append(f"{p.parent.name}: …{vb[-64:]}")
    assert not bad, (
        "committed attribution verbatims end mid-sentence — re-run the artifact pass:\n  "
        + "\n  ".join(bad[:12]))
