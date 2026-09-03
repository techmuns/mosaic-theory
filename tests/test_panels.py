"""(phase 2) `PanelSpec` + registry — the gating rule, pinned.

The rule under test, from the approved panel design: NOT IN THE SET never renders; IN THE SET BUT
REFUSED renders loudly and names the requirement that failed; **these two must never look alike**.

Every refusal exercised here was OBSERVED on a real filing (2026-09-03, live EDGAR), never
invented: GOOGL's Q2 10-Q indexes two segment (Details) reports matching the economics refinement;
WERN and LLY index no property-and-equipment report at all. The point of using real ones is that
an invented refusal proves the assertion, not the rule.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from vinci.panels import (
    COMMISSIONING,
    SEGMENT_ECONOMICS,
    PanelRegistry,
    PanelSpec,
    Requirement,
    default_registry,
)

# Observed live, 2026-09-03. Verbatim heads of the real refusals.
GOOGL_SEGMENT_AMBIGUOUS = (
    "more than one segment report matches the refinement, so which one holds the figures is "
    "ambiguous and is not guessed: ['Revenues - Revenue by Segment (Details)', 'Information "
    "about Segments and Geographic Areas - Revenue and Operating Income/Loss by Segment (Details)']"
)
WERN_NO_PPE = (
    "no property-and-equipment (Details) report in 0000793074-26-000140: this filing indexes no "
    "report naming a property-and-equipment — unlike a single-segment filer, an operating company "
    "always holds fixed assets"
)


def test_not_in_set_renders_nothing_even_when_every_requirement_is_met() -> None:
    """SUBSTANCE decides membership; FORM never promotes a name into the set.

    This is the standing rule's inversion, as a test. A payments name that happens to file a
    property-and-equipment note does not thereby acquire a data-centre commissioning question —
    and if `decide` ever derived membership from `have`, this is the assertion that reddens.
    """
    d = default_registry().decide(
        "commissioning", declared=False, have={"property and equipment": True}
    )
    assert d.state == "not_in_set"
    assert d.renders is False
    assert d.missing == ()
    assert d.reason == ""


def test_refused_renders_and_names_the_requirement() -> None:
    """The other half: substance says yes, form cannot deliver — so it is LOUD."""
    d = default_registry().decide("commissioning", declared=True, have={})
    assert d.state == "refused"
    assert d.renders is True
    assert [r.detail for r in d.missing] == ["property and equipment"]
    # It names WHAT is missing and WHY the panel needs it — not a bare key the reader must chase.
    assert "property and equipment" in d.reason
    assert "no XBRL tag carries the split" in d.reason


def test_the_two_negative_states_never_look_alike() -> None:
    """The safety property itself, asserted as a DIFFERENCE rather than as two separate facts.

    A grid reader scanning twelve tiles reads silence as "fine". If a future refactor collapses
    these onto one falsy value — `None`, `False`, an empty decision — this reddens, which is the
    only reason it is written as a comparison.
    """
    reg = default_registry()
    absent = reg.decide("commissioning", declared=False, have={})
    broken = reg.decide("commissioning", declared=True, have={})
    assert absent.state != broken.state
    assert absent.renders != broken.renders
    assert bool(absent.reason) != bool(broken.reason)


def test_the_extractors_real_refusal_reaches_the_reader_verbatim() -> None:
    """A refusal SHOWS the extractor's words; the panel never forms a second opinion.

    Both strings below were produced by the real extractors against live filings. The panel is
    not allowed to paraphrase them: the extractors distinguish "no such report" from "the report
    has no numbers" from "several match", and a re-derivation here would be a divergent parser of
    the same question.
    """
    reg = default_registry()
    d = reg.decide(
        "segment_economics",
        declared=True,
        have={"segment": False},
        because={"segment": GOOGL_SEGMENT_AMBIGUOUS},
    )
    assert d.state == "refused"
    assert GOOGL_SEGMENT_AMBIGUOUS in d.reason

    c = reg.decide(
        "commissioning",
        declared=True,
        have={"property and equipment": False},
        because={"property and equipment": WERN_NO_PPE},
    )
    assert WERN_NO_PPE in c.reason


def test_a_declared_panel_that_does_not_exist_is_loud_not_blank() -> None:
    """A configuration bug rendering as an empty tile is how a grid lies."""
    with pytest.raises(KeyError, match="not registered"):
        default_registry().decide("no_such_panel", declared=True)


def test_ready_only_when_substance_and_form_both_hold() -> None:
    reg = default_registry()
    assert reg.decide(
        "commissioning", declared=True, have={"property and equipment": True}
    ).state == "ready"


def test_a_panel_whose_number_needs_a_caveat_has_somewhere_to_put_it() -> None:
    """The commissioning ratio divides a whole by a part; "49.7%" alone is not a commissioning rate.

    This pins the CHANNEL, not the wording — the caveat text is prose and will be re-edited. What
    must not happen is the channel disappearing, leaving the number to be read as a rate.
    """
    assert COMMISSIONING.caveat.strip()
    assert "not a commissioning RATE" in COMMISSIONING.caveat


def test_specs_are_frozen_and_refuse_blank_declarations() -> None:
    with pytest.raises(ValidationError):
        COMMISSIONING.key = "other"  # type: ignore[misc]
    with pytest.raises(ValueError):
        Requirement(kind="tag", detail="  ", why="x")
    with pytest.raises(ValueError):
        Requirement(kind="tag", detail="x", why="")
    with pytest.raises(ValueError):
        PanelSpec(key="k", tier="name", title=" ")


def test_registry_refuses_a_duplicate_key() -> None:
    reg = PanelRegistry((SEGMENT_ECONOMICS,))
    with pytest.raises(ValueError, match="already registered"):
        reg.register(SEGMENT_ECONOMICS)
