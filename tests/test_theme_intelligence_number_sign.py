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
