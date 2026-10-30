"""Is a quote an LLM returned actually IN the document it says it read? — the verbatim-span check.

An LLM phase asked for "the exact clause you read it from" can return a clause it RECALLED rather
than READ — most of all on a filing older than the model's training cutoff, whose wording is in the
weights. The prompt cannot tell the two apart; only the document can. This module asks the
document, deterministically and with no model: a quote is kept only when it is a span of the source
text, and refused otherwise. The operating-driver extractor has refused an uncontained quote since
#131 (`driver_extract`, with its own whitespace-and-case rule); this is that rule as one shared
helper, so the covenant and graph extractors stop trusting the prompt alone.

WHAT COUNTS AS THE SAME TEXT. Both sides reduce to one comparison key, and every step of the
reduction removes something that is NOT the document's wording:
- NFKC — compatibility forms: "…" is "...", a non-breaking space is a space, "ﬁ" is "fi".
- Quote marks fold to one mark and dashes to one dash. That is typography, and the model re-types
  it freely: it writes 'US-Joint' for a filing's “US-Joint”.
- Case folds, as the operating-driver check already does.
- ALL whitespace and the invisible format characters are removed. `html_to_text` joins text nodes
  with a space, so a bolded defined term reads “ Maturity Date ” and a tag before a comma reads
  "WHEREAS ," — spaces the document never had.
- EXCEPT between two digits, where whitespace reduces to ONE space, never to nothing (audit G-D7).
  Removing it there joined two figures into a third: "Level 1 1.25%" read as "Level 11.25%", and a
  quote stating 11.25% matched a document that prints 1.25%. An invisible character is no gap, and
  still folds away inside a figure.
Nothing else is forgiven. A reordered clause, an inserted section number, a dropped parenthetical, a
corrected typo, page furniture the quote reads across: none is a span, and each is refused.

ELISION. A quote stitched at an ellipsis ("…", "...", "[...]") is ELIDED, and kept, when every
piece is a span AND the pieces occur in the document's order — the quotation convention for an
omission. Pieces found out of order are refused: that is a rearrangement, not an omission.
Punctuation touching an ellipsis, and a stop the model put at the end of a cut, belong to the cut
and are trimmed; nowhere else is punctuation dropped.

LIMITS, stated. A span check proves PRESENCE, never SUPPORT. A short quote ("Term SOFR") is a span
of any SOFR facility, and an elided quote may omit a qualifier between its pieces. A pass says the
words were read from this document — not that they carry the value the model attached to them.
"""

from __future__ import annotations

import enum
import re
import unicodedata

#: Every quote mark the model or a filer types, folded to one. NFKC leaves the curly and low-9
#: forms alone, so they are listed. Primes are NOT: NFKC turns a double prime into two primes, so
#: folding them would match one mark against two — they are feet and minutes, not quotation.
_QUOTE_MARKS = "\"'`\u00b4\u2018\u2019\u201a\u201b\u201c\u201d\u201e\u201f\u00ab\u00bb"
#: Hyphen, non-breaking hyphen, figure dash, en dash, em dash, horizontal bar, minus.
_DASHES = "\u2010\u2011\u2012\u2013\u2014\u2015\u2212"
_FOLD = str.maketrans({**dict.fromkeys(_QUOTE_MARKS, "'"), **dict.fromkeys(_DASHES, "-")})
#: The characters that render as nothing: soft hyphen, zero-width space/joiners, word joiner, BOM.
#: `\s` matches none of them. Dropped first, so one never decides whether a gap sits between digits.
_INVISIBLE = re.compile("[\u00ad\u200b\u200c\u200d\u2060\ufeff]+")
#: Whitespace: a run between two digits (group 1) is kept as one space, any other run is dropped.
_DROP = re.compile(r"(?<=\d)(\s+)(?=\d)|\s+")
#: An omission marker AFTER reduction: "…" is "..." by NFKC and ". . ." loses its spaces, so one
#: pattern covers all three; a bracket around it ("[...]") is part of the marker.
_ELLIPSIS = re.compile(r"\[?\.{3,}\]?")
#: Punctuation that belongs to a cut rather than to the text cut from.
_CUT_PUNCT = ".,;:"


class SpanMatch(enum.StrEnum):
    """What the source says about one quote."""

    VERBATIM = "verbatim"  # one contiguous span of the source
    ELIDED = "elided"  # every ellipsis-separated piece is a span, in the source's order
    NOT_FOUND = "not_found"  # anything else — the caller refuses the value
    EMPTY = "empty"  # no quote to check — nothing binds the value either, so also refused

    @property
    def found(self) -> bool:
        return self in (SpanMatch.VERBATIM, SpanMatch.ELIDED)


def comparison_key(text: str) -> str:
    """The text reduced to what a span check compares: NFKC, one quote mark, one dash, case-folded,
    no whitespace but one space between two digits. Applied identically to the quote and to its
    source."""
    return squeeze(unicodedata.normalize("NFKC", text).translate(_FOLD).casefold())


def squeeze(text: str) -> str:
    """The whitespace step of :func:`comparison_key`: invisible characters dropped, a whitespace
    run between two digits kept as one space, every other run dropped."""
    return _DROP.sub(lambda m: " " if m.group(1) else "", _INVISIBLE.sub("", text))


class SourceText:
    """A source document reduced ONCE to its comparison key — a covenant exhibit runs to 1.2M
    characters and is asked about every term the model returned from it."""

    def __init__(self, text: str) -> None:
        self._key = comparison_key(text)

    def match(self, quote: str) -> SpanMatch:
        """VERBATIM / ELIDED when the quote is in this source, NOT_FOUND when it is not, EMPTY when
        there is no quote. An empty quote is never "found": "" is a substring of every text."""
        q = comparison_key(quote)
        if not q:
            return SpanMatch.EMPTY
        if q in self._key:
            return SpanMatch.VERBATIM
        pieces = _ELLIPSIS.split(q)
        if len(pieces) == 1:
            # No omission marker: the only forgiveness left is a stop the model closed its cut with.
            tail = q.rstrip(_CUT_PUNCT)
            return SpanMatch.VERBATIM if tail and tail in self._key else SpanMatch.NOT_FOUND
        pos = 0
        seen = 0
        for i, raw in enumerate(pieces):
            # Trim cut punctuation on the sides that touch a marker, and at the quote's own end.
            piece = raw.lstrip(_CUT_PUNCT) if i > 0 else raw
            piece = piece.rstrip(_CUT_PUNCT)
            if not piece:
                continue
            at = self._key.find(piece, pos)
            if at < 0:
                return SpanMatch.NOT_FOUND
            pos = at + len(piece)
            seen += 1
        return SpanMatch.ELIDED if seen else SpanMatch.NOT_FOUND
