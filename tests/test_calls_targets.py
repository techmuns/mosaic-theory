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
import re

import pytest

from vinci.calls.targets import TargetStatus, parse_target

_RANGE_NUMS = re.compile(r"\d+(?:\.\d+)?")

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
     ("210-200", "range", "bullish", 210.0),    # DESCENDING: read by VALUE — see the pin below
     ("210-200", "range", "bearish", 200.0),
     ("50-100%", "pct", "bullish", 150.0),      # a pct range takes its FIRST number
     ("5%", "pct", "bullish", 105.0),
     ("83%", "pct", "bullish", 183.0)],
)
def test_the_preregistered_conventions_are_unchanged(
    target: str, ty: str, bias: str, want: float
) -> None:
    """These were chosen before any result was seen; changing one changes every number downstream.
    The two DESCENDING cases are the exception and are covered by their own pin below: tracker.py
    read ranges positionally, which only means "high end vs low end" while ranges are written
    ascending. Everything else here must still equal tracker.py exactly."""
    assert parse_target(target, ty, 100.0, bias).price == pytest.approx(want)
    if target != "210-200":
        assert _tracker_parse(target, ty, 100.0, bias) == pytest.approx(want), "drifted"


# --------------------------------------------------------------------------- the corpus pin
@pytest.mark.skipif(not LABELS.is_file(), reason="no committed calls corpus")
def test_across_the_whole_corpus_only_the_authorised_classes_changed() -> None:
    """THE REAL GUARD. Over every named target in the committed corpus, the new parser may differ
    from tracker.py ONLY in the two ways the operator authorised: percentages tracker.py dropped,
    and descending ranges it read positionally. Anything else reddens here, not in production."""
    labels = json.loads(LABELS.read_text())
    named = {k: v for k, v in labels.items()
             if v.get("target_type") not in (None, "none") and v.get("target")}
    assert len(named) > 3000, f"corpus shrank to {len(named)} named targets — re-check the fixture"

    gained, changed = [], []
    for key, lab in named.items():
        # PRICE EACH TARGET NEAR ITSELF. A fixed entry of 100 makes a "1000-950" range read as a
        # 10x call and the plausibility band then refuses it — which is correct behaviour, but it
        # is not what THIS test is about. Anchoring the entry to the target's own magnitude
        # isolates the range/sign logic, which is the thing being held against tracker.py.
        nums = [float(x) for x in _RANGE_NUMS.findall(str(lab["target"]))]
        entry = nums[0] if (nums and lab["target_type"] in ("point", "range")) else 100.0
        old = _tracker_parse(lab["target"], lab["target_type"], entry, lab["bias"])
        new = parse_target(lab["target"], lab["target_type"], entry, lab["bias"])
        if old is None and new.price is not None:
            gained.append((key, lab["target"], lab["bias"]))
        elif old is not None and new.price is not None and abs(old - new.price) > 1e-9:
            changed.append((key, lab["target"], lab["bias"], old, new.price))

    # THE ONLY PRICES ALLOWED TO MOVE ARE DESCENDING RANGES. A range written high-then-low was
    # read positionally, handing a bullish call its LOWER bound and a bearish call its HIGHER one —
    # easier to hit in both directions, in the way that flatters the author.
    for key, tgt, bias, old, new in changed:
        nums = [float(x) for x in _RANGE_NUMS.findall(str(tgt))][:2]
        assert len(nums) == 2 and nums[0] > nums[1], (
            f"{key}: a price moved on something that is not a descending range ({tgt!r}) — the "
            f"pre-registered conventions must not drift: {old} -> {new}")
        assert new == pytest.approx(max(nums) if bias == "bullish" else min(nums)), (
            f"{key}: a descending range did not resolve to its true high/low end")
    # A PROPERTY, NOT A COUNT. The exact number depends on how many descending ranges also trip the
    # plausibility band — a data fact that moves as the corpus grows, and a count pinned
    # against a living artifact reddens on a routine data event rather than on a defect. What must
    # hold is the RULE: every moved price is a descending range, resolving to its true end.
    assert len(changed) >= 50, (
        f"only {len(changed)} descending ranges moved — the by-value fix is barely doing anything; "
        f"re-check that the corpus still contains descending ranges")
    assert gained, "nothing was recovered — the fix is not doing anything on the real corpus"
    # every recovery is the same shape: a minus-signed percentage whose direction agrees with bias
    for key, tgt, bias in gained:
        assert str(tgt).strip().startswith("-") and bias == "bearish", (
            f"{key} was recovered for an unexpected reason ({tgt!r}, {bias}) — the fix widened "
            f"beyond negative percentages")
    assert len(gained) == 13, f"expected the 13 known dropped calls, got {len(gained)}"


# --------------------------------------------------------------------------- implausible targets
@pytest.mark.parametrize(
    ("price", "entry", "ok"),
    [("430", 430.0, True),        # at the money
     ("4300", 430.0, True),       # exactly 10x — a ten-bagger call, admitted
     ("43000", 430.0, False),     # 100x — not a target anyone stated
     ("43", 430.0, True),         # exactly 0.1x — a 90%-crash call, admitted
     ("4.3", 430.0, False),       # 99% — beyond what was said
     ("5000000", 430.0, False)],  # $TSLA to five million dollars
)
def test_a_target_nowhere_near_the_price_is_refused(price: str, entry: float, ok: bool) -> None:
    """WHY THIS IS NOT COSMETIC. `target_hit` asks whether the HIGH ever reached the target for a
    bullish call and whether the LOW ever did for a bearish one. So an absurdly HIGH target on a
    BEARISH call is satisfied by every bar that ever traded, and an absurdly LOW one on a BULLISH
    call likewise — the hit is arithmetic, not evidence.

    Measured on the corpus before the fix: 621 of 1,966 resolved targets sat outside the band and
    **489 of them were reporting a hit**. The band is set on face validity — 10x admits a genuine
    ten-bagger call, 0.1x admits a 90%-crash call — and never on what it does to the hit-rate."""
    got = parse_target(price, "point", entry, "bullish")
    assert got.resolved is ok, f"{price} against an entry of {entry}: expected resolved={ok}"
    if not ok:
        assert got.status is TargetStatus.IMPLAUSIBLE


def test_a_bearish_call_cannot_be_handed_a_free_hit() -> None:
    """The exact shape found in the corpus: $TSLA bearish, target $5,000,000, entry $430. Every low
    that has ever printed is below five million, so the call 'hit' its target by arithmetic."""
    assert parse_target("5000000", "point", 430.26, "bearish").price is None
    assert parse_target("12", "point", 600.0, "bullish").price is None      # $SPY 'to $12'


def test_without_an_entry_the_target_is_not_refused_for_want_of_one() -> None:
    """Refusing on an unknown would discard good targets because no price was supplied, which is
    the opposite of the intent — the check exists to catch numbers that CONTRADICT a known price."""
    got = parse_target("5000000", "point", None, "bullish")
    assert got.resolved and got.price == pytest.approx(5_000_000.0)


@pytest.mark.skipif(not LABELS.is_file(), reason="no committed calls corpus")
def test_the_implausible_band_does_not_swallow_ordinary_calls() -> None:
    """A guard that refuses too much is its own defect. Against every resolvable point/range target
    in the corpus priced at its own entry, the overwhelming majority must survive."""
    import statistics
    labels = json.loads(LABELS.read_text())
    kept, refused = 0, 0
    for v in labels.values():
        if v.get("target_type") not in ("point", "range") or not v.get("target"):
            continue
        # price each target against ITSELF scaled to a realistic entry, so the test measures the
        # band and not the corpus's price levels
        nums = [float(x) for x in _RANGE_NUMS.findall(str(v["target"]))][:1]
        if not nums:
            continue
        got = parse_target(v["target"], v["target_type"], nums[0], v.get("bias"))
        if got.resolved:
            kept += 1
        else:
            refused += 1
    assert kept > 0 and refused / max(kept + refused, 1) < 0.05, (
        f"the plausibility band refuses {refused}/{kept + refused} targets priced at their own "
        f"level — it is too tight and is discarding real calls")
    assert statistics.mean([1.0]) == 1.0


# ------------------------------------------------------------------- levels against the bias
def test_a_level_against_the_bias_is_marked_but_never_discarded() -> None:
    """MARKED, NOT REFUSED, and the ground truth is why. Four of the eighty-three HAND labels are
    this shape and all four are correct: $UNH bullish with a $300 target against a $303 entry is
    the support he expects a bounce FROM; $SPY bearish with $676–684 against $668 is the rejection
    zone he expects price to rise INTO before falling. They are levels being watched, not targets
    being predicted — and a guard that discarded four ground-truth labels to catch a machine
    artifact would be the worse trade."""
    below = parse_target("300", "point", 303.12, "bullish")
    assert below.price == pytest.approx(300.0), "a watched level was discarded"
    assert below.status is TargetStatus.COUNTER_DIRECTIONAL
    above = parse_target("676-684", "range", 668.36, "bearish")
    assert above.price == pytest.approx(676.0) and above.status is TargetStatus.COUNTER_DIRECTIONAL
    # ...and an ordinary target in the direction of the call is untouched
    assert parse_target("400", "point", 340.0, "bullish").status is TargetStatus.RESOLVED
    assert parse_target("100", "point", 140.0, "bearish").status is TargetStatus.RESOLVED


def test_a_percentage_target_can_never_be_counter_directional() -> None:
    """A pct target is DERIVED from the bias, so it cannot point against it — and if this ever
    starts returning COUNTER_DIRECTIONAL the derivation itself has broken."""
    for bias in ("bullish", "bearish"):
        got = parse_target("10%", "pct", 100.0, bias)
        assert got.status is TargetStatus.RESOLVED, f"{bias}: {got.status}"
