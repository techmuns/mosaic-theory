"""Resolving a STATED target to a price — and saying out loud when it cannot be resolved.

WHY THIS MODULE EXISTS. ``tracker.py``'s ``parse_target`` collapsed five different situations into
one silent ``None``: a qualitative target ("ATH"), an absent one, an unparseable one, a target whose
sign contradicts the stated bias, and — the defect — every ordinary NEGATIVE percentage.

    >>> "-10%".split("-")[0]        # the original first step
    ''
    >>> float('')                   # ValueError, swallowed by a bare `except`
    Traceback (most recent call last):
    ValueError: could not convert string to float: ''

Measured on the committed corpus: **40 of 628 pct targets begin with a minus sign**, so 40 calls
were scored as though the author named no target at all — they dropped out of the target-hit
denominator with nothing said. That is the fail-loud rule inverted: a parse failure became a quiet
"not applicable".

WHAT CHANGED, PRECISELY:
  1. The sign is read only at the START of the string, so "-10-15%" parses as (-10, 15) and
     "50-100%" as (50, 100) — the separator is never mistaken for a sign.
  2. Every non-resolution carries a REASON. A caller can now tell "he named no target" from
     "he named one and we could not read it", which are opposite facts about the author.
  3. A stated direction that CONTRADICTS the stated bias is refused, never coerced. $QQQ on
     2026-02-13 is bias=bullish with target="-10-15%" — the post says the drawdown is what happens
     *if* his signals flip, i.e. the downside branch, not his target. Forcing it through the bullish
     formula would invent a target 10% ABOVE entry, a number the author never stated. This is the
     spec's "worst case flips polarity with his position" trap, met at the parser.

THE CONVENTIONS ARE PRESERVED EXACTLY, because they are pre-registered and changing them changes
results: a pct target takes the FIRST number of a range and applies it in the bias direction; a
`range` target takes the HIGH end when bullish and the LOW end when bearish; a `point` target is
read as-is. Only the failure modes changed.
"""
from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel

#: A signed number is recognised ONLY at the start; any later "-" is a range separator, never a
#: sign. This is the whole bug fix: "-10-15%" -> (-10, 15), "50-100%" -> (50, 100).
_PAIR = re.compile(
    r"^\s*(?P<lo>[-+]?\d+(?:\.\d+)?)\s*(?:[-–—]\s*(?P<hi>[-+]?\d+(?:\.\d+)?))?"
)


class TargetStatus(StrEnum):
    """Why a target did or did not resolve. Every value here was a bare ``None`` before."""

    RESOLVED = "resolved"
    ABSENT = "absent"                 # the author named no target
    QUALITATIVE = "qualitative"       # "ATH", "prior highs" — real, but not a number
    SIGN_CONFLICT = "sign_conflict"   # stated direction contradicts the stated bias
    UNPARSEABLE = "unparseable"       # a target was named and could not be read — a DEFECT signal
    NO_ENTRY = "no_entry"             # a pct/relative target with no entry price to apply it to
    NO_BIAS = "no_bias"               # a RELATIVE move with no stated direction to apply it in


class TargetParse(BaseModel, frozen=True):
    """A resolved target price, or the stated reason there isn't one."""

    price: float | None
    status: TargetStatus

    @property
    def resolved(self) -> bool:
        return self.price is not None


def _numbers(raw: str) -> tuple[float, float | None] | None:
    m = _PAIR.match(raw)
    if m is None:
        return None
    hi = m.group("hi")
    return float(m.group("lo")), (float(hi) if hi is not None else None)


def parse_target(
    target: object, target_type: str | None, entry: float | None, bias: str | None
) -> TargetParse:
    """Resolve a stated target to an absolute price, or say why it could not be resolved.

    ``entry`` is required only for ``pct`` (a relative move needs something to be relative to).
    ``bias`` picks the direction for ``pct`` and which end of a ``range`` is the target.
    """
    if target is None or target_type in (None, "none") or str(target).strip() == "":
        return TargetParse(price=None, status=TargetStatus.ABSENT)
    if target_type == "qualitative":
        return TargetParse(price=None, status=TargetStatus.QUALITATIVE)

    raw = str(target).replace("$", "").replace(",", "").strip()
    nums = _numbers(raw)
    if nums is None:
        return TargetParse(price=None, status=TargetStatus.UNPARSEABLE)
    lo, hi = nums

    if target_type == "point":
        return TargetParse(price=lo, status=TargetStatus.RESOLVED)

    if target_type == "range":
        if hi is None:
            return TargetParse(price=lo, status=TargetStatus.RESOLVED)
        # BY VALUE, not by position (fixed 2026-08-25, operator-authorised). tracker.py took the
        # SECOND number when bullish and the FIRST when bearish, which is only "the high end vs the
        # low end" while the author happens to write ranges ascending. 88 of the corpus's ranges are
        # DESCENDING — "$TSLA 210-200", "$NVDA 120-118" — and on those the positional rule handed a
        # bullish call its LOWER bound and a bearish call its HIGHER one: the target was easier to
        # hit in both directions, in exactly the way that flatters the author.
        #
        # The convention itself is unchanged and still reads as it always did — bullish targets the
        # top of the range, bearish the bottom. Only the ASSUMPTION that the author writes ranges
        # ascending is gone. On ascending ranges (the other 533) this is bit-identical to before.
        low, high = min(lo, hi), max(lo, hi)
        return TargetParse(price=(high if bias == "bullish" else low),
                           status=TargetStatus.RESOLVED)

    if target_type == "pct":
        if bias not in ("bullish", "bearish"):
            # tracker.py never reaches these: it filters to bullish/bearish before scoring. The
            # refusal matches that, but names the actual reason instead of implying a sign clash.
            return TargetParse(price=None, status=TargetStatus.NO_BIAS)
        # An EXPLICIT sign is a stated direction. When it disagrees with the stated bias the two
        # facts cannot both be the target, so neither is assumed. (No sign = magnitude only.)
        stated_down = raw.lstrip().startswith("-")
        stated_up = raw.lstrip().startswith("+")
        if (stated_down and bias == "bullish") or (stated_up and bias == "bearish"):
            return TargetParse(price=None, status=TargetStatus.SIGN_CONFLICT)
        if entry is None or entry <= 0:
            return TargetParse(price=None, status=TargetStatus.NO_ENTRY)
        # FIRST number of a range, magnitude only, applied in the bias direction — tracker.py's
        # convention, preserved exactly.
        mag = abs(lo) / 100.0
        return TargetParse(price=entry * (1 + mag) if bias == "bullish" else entry * (1 - mag),
                           status=TargetStatus.RESOLVED)

    return TargetParse(price=None, status=TargetStatus.UNPARSEABLE)
