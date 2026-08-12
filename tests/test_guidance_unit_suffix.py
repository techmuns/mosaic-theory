"""A magnitude suffix is a magnitude: `$51.7B` is not `$51.7M`, and each side states its own.

WHY (NFLX, found validating an analyst's reading of the committed page). The dossier carried
`revenue 2026: 50.7–51.7 $M` against a company guiding **$50.7–51.7 BILLION** — its own filed words,
in the exhibit the dossier cites:

    "We continue to project 2026 revenue of $50.7-$51.7B"
    "we forecast 2026 revenue of $50.7B-$51.7B, which represents 12%-14% growth"

The parser read only the SPELLED-OUT units. `billion` scaled; `B` did not exist to it. That is the
Concentrix billions-as-millions defect a third time, and this module's own rule is that a magnitude
error in a decision figure is worse than an absent one.

THREE FAILURES, ONE REGEX, all silent:
  (1) TRAILING suffix ignored — "$50.7-$51.7B" parsed 50.7–51.7, a 1000x understatement, and the
      verbatim stopped at "51.7" so the page showed a sentence ending mid-number.
  (2) LEADING suffix broke the match — "$50.7B-$51.7B" and "$985M-$995M" matched NOTHING, because
      the `B` sat where the range separator had to be. The guide was dropped with no flag: the same
      dropped-clause class as the change-basis guides, which cost ten of seventeen clauses.
  (3) The trailing unit was applied to BOTH numbers — "$500 million to $1.2 billion" produced
      low=500,000 against high=1,200. A range whose floor is 400x its ceiling is not a wide guide,
      it is an impossible one, and nothing rejected it.

THE SENTENCES BELOW ARE FROZEN FIXTURES quoted from filed exhibits (NFLX 0001065280-26-000137,
Concentrix). Filing text is immutable, so these are value pins that cannot rot.
"""
from __future__ import annotations

import pytest

from vinci.edgar.release_parse import parse_release


def _guide(sentence: str):
    """The single revenue guide parsed out of a one-sentence outlook block."""
    r = parse_release(f"Outlook\n{sentence}\n", source_ref="8-K test EX-99.1")
    return r.guidance[0] if r.guidance else None


# --- (1) + (2) the two NFLX forms, from one exhibit ---------------------------------------------
@pytest.mark.parametrize(
    "sentence",
    [
        "We continue to project 2026 revenue of $50.7-$51.7B.",       # trailing suffix (was 50.7)
        "we forecast 2026 revenue of $50.7B-$51.7B, which is growth.",  # leading too (was DROPPED)
        "We project 2026 revenue of $50.7-$51.7bn.",                   # the bn spelling
    ],
)
def test_the_nflx_billions_suffix_is_read_as_billions(sentence: str) -> None:
    """THE REGRESSION. Each of these shipped as 50.7–51.7 (or as nothing at all); all three state
    fifty-odd BILLION and must land as $M like every other guide the composer prints."""
    g = _guide(sentence)
    assert g is not None, "a stated guide must never be silently dropped"
    assert (g.low, g.high) == (50_700.0, 51_700.0)
    assert g.unit == "$M"


def test_the_million_suffix_form_is_not_dropped() -> None:
    """`$985M-$995M` matched nothing for the same structural reason, and a million-suffix guide is
    the commoner shape. Correct here means UNSCALED — the composer already prints $M."""
    g = _guide("We project 2026 revenue of $985M-$995M.")
    assert g is not None and (g.low, g.high) == (985.0, 995.0)


# --- (3) mixed units — the impossible range -----------------------------------------------------
def test_each_side_scales_by_its_own_stated_unit() -> None:
    """THE SECOND REGRESSION. The trailing unit governed both numbers, so a low stated in MILLIONS
    beside a high in BILLIONS was multiplied into 500,000 — a floor 400x above its own ceiling."""
    g = _guide("We project 2026 revenue of $500 million to $1.2 billion.")
    assert g is not None and (g.low, g.high) == (500.0, 1200.0)
    assert g.low < g.high, "a range whose floor exceeds its ceiling is not a guide"


# --- what must NOT change -----------------------------------------------------------------------
@pytest.mark.parametrize(
    ("sentence", "expected"),
    [
        # the spelled-out forms this module already read correctly
        ("We project 2026 revenue of $50.7 to $51.7 billion.", (50_700.0, 51_700.0)),
        ("We project 2026 revenue of $985 to $995 million.", (985.0, 995.0)),
        # Concentrix, verbatim — one stated unit governs a bare partner, as before
        ("Third quarter reported revenue of $2.465 billion to $2.490 billion.", (2465.0, 2490.0)),
    ],
)
def test_the_spelled_out_forms_are_untouched(sentence: str, expected: tuple[float, float]) -> None:
    g = _guide(sentence)
    assert g is not None and (g.low, g.high) == expected


def test_a_following_word_is_not_eaten_as_a_unit() -> None:
    """THE INVERTED RISK, guarded. `[MB]` under re.I would otherwise read the `b` of "based" as
    billions and turn $2.5M into $2,500M — the same magnitude error this fix removes, pointing the
    other way. The suffix must be a suffix, not the first letter of the next word."""
    g = _guide("We project 2026 revenue of $2.4 to $2.5 based on current rates.")
    assert g is not None and (g.low, g.high) == (2.4, 2.5)

    million = _guide("We project 2026 revenue of $900 to $950 million, mostly subscriptions.")
    assert million is not None and (million.low, million.high) == (900.0, 950.0)


@pytest.mark.parametrize(
    ("word", "scale"),
    [("billion", 1000.0), ("Billion", 1000.0), ("B", 1000.0), ("b", 1000.0), ("bn", 1000.0),
     ("million", 1.0), ("M", 1.0), ("mm", 1.0), ("%", 1.0), ("", 1.0), (None, 1.0)],
)
def test_unit_scale_never_guesses(word: str | None, scale: float) -> None:
    """An unrecognised or absent unit is 1.0 — the number as filed. Inventing a multiplier for a
    unit nobody stated is the fabrication this codebase refuses.

    IMPORTED LOCALLY, on purpose: a module-level import of a symbol this fix ADDS would make the
    whole file fail to collect against the pre-fix parser, and an ImportError demonstrates nothing
    about the defect. The behavioural pins above must run — and fail — on the old code."""
    from vinci.edgar.release_parse import _unit_scale

    assert _unit_scale(word) == scale
