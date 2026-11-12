"""RG-D21 — THE THEME NUMBER CHECK READS A STATED DECLINE'S SIGN (fix request 2, group G).

The check (`verify._number_check`) passed a POSITIVE value for a figure the quote states as a
decline — "Shipments were down 27%" read as +27 — a silent wrong value; and it REFUSED the right
value, −27, when the value text itself carried the word ("down 27%") — a loud false refusal,
because the decline was looked for only beside the figure in the quote, and with the word inside
the value text there is nothing beside it.

On the registry the desk is published from (`theme-intelligence-state` 4527c2b1, 1,190 claims,
596 with a value), ONE stored claim carried the wrong sign: C-f5fcf829b5a474, "Spot prices for
low- to mid-capacitance consumer-grade MLCCs slipped approximately 5%", value +5, metric "spot
price change". Its shape is pinned below. A positive value stays legitimate where the METRIC names
the decline ("mean reward reduction": a 3x lower mean reward is 3, not −3) or the figure is a
multiple.
"""

from __future__ import annotations

import pytest

from vinci.theme_intelligence.verify import _number_check

FINDING = "Shipments were down 27% YoY in the quarter."
MLCC = ("Spot prices for low- to mid-capacitance consumer-grade MLCCs slipped approximately 5% in "
        "early October")


@pytest.mark.parametrize(("value", "text"), [(-27.0, "down 27%"), (-27.0, "27%")])
def test_a_stated_decline_read_as_negative_passes(value: float, text: str) -> None:
    ok, notes = _number_check(value, text, "%", FINDING)
    assert ok is True, notes


@pytest.mark.parametrize("text", ["27%", "down 27%"])
def test_a_stated_decline_read_as_positive_is_refused(text: str) -> None:
    ok, notes = _number_check(27.0, text, "%", FINDING)
    assert ok is False
    assert any("states a decline" in n for n in notes), notes


def test_the_real_mlcc_claim_is_refused_positive_and_passes_negative() -> None:
    ok, notes = _number_check(5.0, "approximately 5%", "%", MLCC, metric="spot price change")
    assert ok is False and any("states a decline" in n for n in notes), notes
    assert _number_check(-5.0, "approximately 5%", "%", MLCC, metric="spot price change")[0]


# --- negative pins: a positive value that is NOT a wrong sign -------------------------------------

def test_a_metric_that_names_the_decline_keeps_its_positive_magnitude() -> None:
    q = "Orders saw a 27% decline in the quarter."
    assert _number_check(27.0, "27%", "%", q, metric="order decline")[0] is True
    assert _number_check(27.0, "27%", "%", q, metric="orders")[0] is False


def test_a_multiple_lower_is_a_factor_not_a_sign() -> None:
    """The real C-743ff569c48ece: 'a 3x lower mean reward', value 3, metric 'mean reward
    reduction' — it passed before and passes now."""
    q = ("training on these degenerate rollouts result in a 3x lower mean reward compared to "
         "training on clean rollouts")
    assert _number_check(3.0, "3x", "x", q, metric="mean reward reduction")[0] is True
    assert _number_check(3.0, "3x", "x", q, metric="mean reward")[0] is True  # a multiple


def test_a_rise_is_unchanged() -> None:
    q = "Revenue rose 27% YoY."
    assert _number_check(27.0, "27%", "%", q)[0] is True
    assert _number_check(-27.0, "27%", "%", q)[0] is False
    assert _number_check(-27.0, "down 27%", "%", q)[0] is False  # not in the quote


# --- review round 0: the sign is read from the number that reads as the value ---------------------

def test_a_leading_number_in_the_value_text_does_not_hide_the_decline() -> None:
    q = "2025 shipments down 27% YoY."
    assert _number_check(-27.0, "2025 shipments down 27%", "%", q)[0] is True
    assert _number_check(27.0, "2025 shipments down 27%", "%", q)[0] is False


def test_a_decline_beside_another_number_is_not_this_ones() -> None:
    q = "Units were down 27%, up 5% sequentially."
    assert _number_check(5.0, "down 27%, up 5%", "%", q)[0] is True
    assert _number_check(-5.0, "down 27%, up 5%", "%", q)[0] is False


def test_a_figure_stated_as_a_rise_and_a_fall_refuses_neither_sign() -> None:
    q = "Revenue rose 27% while costs fell 27%."
    assert _number_check(27.0, "27%", "%", q)[0] is True
    assert _number_check(-27.0, "27%", "%", q)[0] is True


@pytest.mark.parametrize(("metric", "quote"), [
    ("net loss change", "Net loss fell 27% in the quarter."),
    ("credit loss provisions", "Credit loss provisions dropped 27%."),
    ("drop-off rate", "The drop-off rate fell 27%."),
])
def test_a_metric_naming_what_fell_is_not_a_decline_metric(metric: str, quote: str) -> None:
    assert _number_check(27.0, "27%", "%", quote, metric=metric)[0] is False


def test_times_as_a_noun_is_not_a_multiple() -> None:
    q = "Lead wait times down 27% this year."
    assert _number_check(27.0, "wait times down 27%", "%", q)[0] is False
    assert _number_check(-27.0, "wait times down 27%", "%", q)[0] is True
    assert _number_check(2.0, "two times lower", "x", "Costs were two times lower.")[0] is True


def test_a_decline_after_a_spelled_percent_is_read() -> None:
    q = "Orders posted a 27 percent decline."
    assert _number_check(-27.0, "27 percent decline", "%", q)[0] is True


# --- review round 1 (Codex, #987) ---------------------------------------------------------------

def test_a_spelled_out_figure_carries_its_sign_too() -> None:
    """Codex P2 (4534697293): the sign was read beside DIGIT numbers only, so a figure written in
    words lost it — "down twenty-seven percent" read as −27 was refused, and "twenty-seven
    percent decline" read as +27 passed."""
    q = "Orders were down twenty-seven percent YoY."
    assert _number_check(-27.0, "down twenty-seven percent", "%", q)[0] is True
    q2 = "Orders posted a twenty-seven percent decline."
    ok, notes = _number_check(27.0, "twenty-seven percent decline", "%", q2)
    assert ok is False and any("states a decline" in n for n in notes), notes


def test_a_multiple_elsewhere_in_the_value_text_does_not_exempt_the_value() -> None:
    """Codex P2 (4534697300): the multiple exemption read the whole value text, so an unrelated
    "3x" let a decline stored positive pass. It binds to the number that reads as the value."""
    q = "Net debt sits at 3x leverage, with EBITDA down 27 million in the quarter."
    vt = "3x leverage, with EBITDA down 27 million"
    ok, notes = _number_check(27_000_000.0, vt, "USD", q)
    assert ok is False and any("states a decline" in n for n in notes), notes
    assert _number_check(-27_000_000.0, vt, "USD", q)[0] is True
    assert _number_check(3.0, "3x lower", "x", "Costs were 3x lower.")[0] is True  # still kept


# --- the residual (Codex on #987, 4535189339): a decline after a POINTS unit ---------------------
# The value text carries the number alone ("27") and the unit is stored apart ("percentage
# points"): the trailing decline word stood past a unit the check could not step over, so
# +27 passed (the silent wrong value) and −27 was refused. Only a percent unit was skipped.

POINTS = [
    ("27", 27.0, "percentage points", "Margins posted a 27 percentage point decline"),
    ("27", 27.0, "percentage points", "a 27 percentage-point drop in share"),
    ("27", 27.0, "percentage points", "share fell to 40%, a 27 percentage points decline"),
    ("2.5", 2.5, "pp", "Gross margin saw a 2.5pp decline year over year"),
    ("2.5", 2.5, "pp", "Gross margin saw a 2.5 pp decline year over year"),
    ("40", 40.0, "bps", "Spreads saw a 40 bps decline this week"),
    ("40", 40.0, "bps", "Spreads saw a 40bp decline this week"),
    ("40", 40.0, "basis points", "a 40 basis point decline in yields"),
    ("40", 40.0, "basis points", "yields were 40 basis points lower"),
    # the unit hyphenated onto the figure, the compound-adjective form (review of this residual)
    ("40", 40.0, "basis points", "a 40-basis-point decline in yields"),
    ("27", 27.0, "percentage points", "a 27-percentage-point drop in share"),
    ("27", 27.0, "%", "a 27-percent drop in shipments"),
    # bare points
    ("2.5", 2.5, "pts", "Gross margin saw a 2.5 pts decline"),
    ("300", 300.0, "points", "the index posted a 300 point decline"),
]


@pytest.mark.parametrize(("text", "size", "unit", "quote"), POINTS)
def test_a_points_decline_read_as_positive_is_refused(text: str, size: float, unit: str,
                                                      quote: str) -> None:
    ok, notes = _number_check(size, text, unit, quote)
    assert ok is False and any("states a decline" in n for n in notes), (quote, notes)


@pytest.mark.parametrize(("text", "size", "unit", "quote"), POINTS)
def test_a_points_decline_read_as_negative_passes(text: str, size: float, unit: str,
                                                  quote: str) -> None:
    ok, notes = _number_check(-size, text, unit, quote)
    assert ok is True, (quote, notes)


def test_a_scale_word_in_the_value_text_reads_as_it_did() -> None:
    """The coordinator's negative pin: '27 million decline' stays as it reads today. With the
    scale word in the value text the decline already stood beside the whole figure, so +27M was
    refused and −27M passed — before and after."""
    q = "EBITDA posted a 27 million decline"
    ok, notes = _number_check(27e6, "27 million", "USD", q)
    assert ok is False and any("states a decline" in n for n in notes), notes
    assert _number_check(-27e6, "27 million", "USD", q)[0] is True


def test_a_points_rise_or_level_is_unchanged() -> None:
    """Real shapes on the registry, each a points figure with no decline: they keep passing."""
    assert _number_check(100.0, "more than 100 basis points", "basis points",
                         "CCC spreads are up more than 100 basis points this year")[0] is True
    assert _number_check(40.0, "40", "bps", "Spreads saw a 40 bps rise this week")[0] is True
    assert _number_check(6.0, "roughly 6 percentage points", "percentage points",
                         "would move S&P 500 earnings growth by roughly 6 percentage points in "
                         "the same direction")[0] is True


def test_the_real_points_drop_on_the_registry_keeps_passing() -> None:
    """C-7f13888d27d72f, the one points figure on the registry worded as a decline, already
    negative: '–6 to –8 percentage points' read as −8."""
    q = "occasional drops as low as –6 to –8 percentage points"
    assert _number_check(-8.0, "–6 to –8 percentage points", "percentage points", q)[0] is True
