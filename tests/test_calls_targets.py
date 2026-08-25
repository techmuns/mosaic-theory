"""A stated target resolves to a price, or says why it did not — the silent-None class, closed.

THE DEFECT. ``tracker.py``'s ``parse_target`` took ``s.split("-")[0]`` as the first number, so any
target written with a leading minus began with the empty string, ``float("")`` raised, and a bare
``except Exception: return None`` swallowed it. Every negative percentage therefore scored as "the
author named no target" — indistinguishable, downstream, from a post that genuinely named none.

MEASURED ON THE COMMITTED CORPUS, not on invented strings: 40 of the account's 628 pct targets
begin with a minus sign, and 13 of those carry a bias that agrees with the sign (so they are
resolvable and were being dropped). The corpus-parity pin at the bottom is the real guard — it
holds the FIX and the UNCHANGED CONVENTIONS against every one of the 3,433 named targets at once.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.calls.targets import TargetStatus, parse_target

ROOT = pathlib.Path(__file__).resolve().parents[1]
LABELS = ROOT / "data" / "calls" / "pdicarlotrader" / "labels.json"


def _tracker_parse(tgt: object, ty: str | None, entry: float, bias: str | None) -> float | None:
    """``tracker.py``'s parser, transcribed verbatim — the behaviour these pins measure against."""
    if tgt is None:
        return None
    s = str(tgt).replace("$", "").replace(",", "").strip()
    try:
        if ty == "pct":
            v = abs(float(s.split("-")[0].strip("%+ ")))
            return entry * (1 + v / 100) if bias == "bullish" else entry * (1 - v / 100)
        if ty == "range":
            lo, hi = (float(x.strip("%+ ")) for x in s.split("-")[:2])
            return hi if bias == "bullish" else lo
        if ty == "point":
            return float(s)
    except Exception:
        return None
    return None


# --------------------------------------------------------------------------- the regression
@pytest.mark.parametrize(
    ("target", "bias", "want"),
    [("-10%", "bearish", 90.0),      # $QQQ and $SPY, 2024-08-29 — both in the hand-labelled set
     ("-30%", "bearish", 70.0),      # $HIMS, 2025-12-22 — and this target was actually TOUCHED
     ("-17%", "bearish", 83.0),      # $SMCI
     ("-40%", "bearish", 60.0)],     # $RDDT / $SENS, one post naming two tickers
)
def test_a_negative_percentage_resolves_instead_of_vanishing(
    target: str, bias: str, want: float
) -> None:
    """Each of these is a REAL row in the committed corpus that scored as 'no target named'."""
    assert _tracker_parse(target, "pct", 100.0, bias) is None, (
        f"{target} already parsed under the old code — this pin's premise is gone")
    got = parse_target(target, "pct", 100.0, bias)
    assert got.status is TargetStatus.RESOLVED
    assert got.price == pytest.approx(want)


def test_a_stated_direction_against_the_stated_bias_is_refused_not_coerced() -> None:
    """$QQQ, 2026-02-13: bias=bullish, target='-10-15%'. The post calls the drawdown the downside
    branch *if* his signals flip — it is not his target. Forcing it through the bullish formula
    invents a target 10% ABOVE entry, a number the author never wrote. Refuse, and say why."""
    got = parse_target("-10-15%", "pct", 100.0, "bullish")
    assert got.price is None
    assert got.status is TargetStatus.SIGN_CONFLICT


def test_every_non_resolution_carries_a_distinct_reason() -> None:
    """The whole defect class was five situations collapsing into one bare None."""
    assert parse_target(None, "none", 100.0, "bullish").status is TargetStatus.ABSENT
    assert parse_target("ATH", "qualitative", 100.0, "bullish").status is TargetStatus.QUALITATIVE
    assert parse_target("-10-15%", "pct", 100.0, "bullish").status is TargetStatus.SIGN_CONFLICT
    assert parse_target("10%", "pct", 100.0, "none").status is TargetStatus.NO_BIAS
    assert parse_target("10%", "pct", None, "bullish").status is TargetStatus.NO_ENTRY
    assert parse_target("about twice", "point", 100.0, "bullish").status is TargetStatus.UNPARSEABLE
    assert len({TargetStatus.ABSENT, TargetStatus.QUALITATIVE, TargetStatus.SIGN_CONFLICT,
                TargetStatus.NO_BIAS, TargetStatus.NO_ENTRY, TargetStatus.UNPARSEABLE}) == 6


# --------------------------------------------------------------------------- conventions held
@pytest.mark.parametrize(
    ("target", "ty", "bias", "want"),
    [("212", "point", "bullish", 212.0),        # a point target is read as written
     ("92.50", "point", "bullish", 92.5),
     ("172-180", "range", "bullish", 180.0),    # ascending range, bullish -> the second value
     ("60-80", "range", "bearish", 60.0),       # ascending range, bearish -> the first
     ("210-200", "range", "bullish", 200.0),    # DESCENDING: positional, NOT min/max. See below.
     ("50-100%", "pct", "bullish", 150.0),      # a pct range takes its FIRST number
     ("5%", "pct", "bullish", 105.0),
     ("83%", "pct", "bullish", 183.0)],
)
def test_the_preregistered_conventions_are_unchanged(
    target: str, ty: str, bias: str, want: float
) -> None:
    """These were chosen before any result was seen; changing one changes every number downstream.
    ``210-200`` is the load-bearing case: tracker.py reads a range POSITIONALLY, so a bullish call
    on a descending range takes the LOWER bound. That is arguably a second bug of the same family
    (88 ranges in the corpus are descending) — but it is not the fix that was authorised, and
    flipping it silently would move the hit-rate under results already produced."""
    assert parse_target(target, ty, 100.0, bias).price == pytest.approx(want)
    assert _tracker_parse(target, ty, 100.0, bias) == pytest.approx(want), "drifted from tracker.py"


# --------------------------------------------------------------------------- the corpus pin
@pytest.mark.skipif(not LABELS.is_file(), reason="no committed calls corpus")
def test_across_the_whole_corpus_only_the_authorised_class_changed() -> None:
    """THE REAL GUARD. Over every named target in the committed corpus, the new parser must agree
    with tracker.py on every price it produced, and may differ ONLY by resolving what tracker.py
    dropped. A future 'tidy-up' of the conventions reddens here rather than in production."""
    labels = json.loads(LABELS.read_text())
    named = {k: v for k, v in labels.items()
             if v.get("target_type") not in (None, "none") and v.get("target")}
    assert len(named) > 3000, f"corpus shrank to {len(named)} named targets — re-check the fixture"

    gained, changed = [], []
    for key, lab in named.items():
        old = _tracker_parse(lab["target"], lab["target_type"], 100.0, lab["bias"])
        new = parse_target(lab["target"], lab["target_type"], 100.0, lab["bias"])
        if old is None and new.price is not None:
            gained.append((key, lab["target"], lab["bias"]))
        elif old is not None and new.price is not None and abs(old - new.price) > 1e-9:
            changed.append((key, lab["target"], lab["bias"], old, new.price))

    assert not changed, (
        f"{len(changed)} target prices MOVED against tracker.py — the conventions are "
        f"pre-registered and must not drift: {changed[:5]}")
    assert gained, "nothing was recovered — the fix is not doing anything on the real corpus"
    # every recovery is the same shape: a minus-signed percentage whose direction agrees with bias
    for key, tgt, bias in gained:
        assert str(tgt).strip().startswith("-") and bias == "bearish", (
            f"{key} was recovered for an unexpected reason ({tgt!r}, {bias}) — the fix widened "
            f"beyond negative percentages")
    assert len(gained) == 13, f"expected the 13 known dropped calls, got {len(gained)}"
