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
PPE_CFG = {"note_name": "property and equipment"}
PPE_KEY = "rfile_note:property and equipment"

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
        "commissioning", declared=False, have={"rfile_note:property and equipment": True}
    )
    assert d.state == "not_in_set"
    assert d.renders is False
    assert d.missing == ()
    assert d.reason == ""


def test_refused_renders_and_names_the_requirement() -> None:
    """The other half: substance says yes, form cannot deliver — so it is LOUD."""
    d = default_registry().decide("commissioning", declared=True, have={}, config=PPE_CFG)
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
    absent = reg.decide("commissioning", declared=False, have={}, config=PPE_CFG)
    broken = reg.decide("commissioning", declared=True, have={}, config=PPE_CFG)
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
        have={"rfile_note:segment": False},
        because={"rfile_note:segment": GOOGL_SEGMENT_AMBIGUOUS},
        config={"note_name": "segment"},
    )
    assert d.state == "refused"
    assert GOOGL_SEGMENT_AMBIGUOUS in d.reason

    c = reg.decide(
        "commissioning",
        declared=True,
        have={"rfile_note:property and equipment": False},
        because={"rfile_note:property and equipment": WERN_NO_PPE},
        config={"note_name": "property and equipment"},
    )
    assert WERN_NO_PPE in c.reason


def test_a_declared_panel_that_does_not_exist_is_loud_not_blank() -> None:
    """A configuration bug rendering as an empty tile is how a grid lies."""
    with pytest.raises(KeyError, match="not registered"):
        default_registry().decide("no_such_panel", declared=True)


def test_ready_only_when_substance_and_form_both_hold() -> None:
    reg = default_registry()
    assert reg.decide(
        "commissioning", declared=True, have={PPE_KEY: True}, config=PPE_CFG
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
        PanelSpec(key="k", tier="name", title=" ", changes_the_call="c")


def test_registry_refuses_a_duplicate_key() -> None:
    reg = PanelRegistry((SEGMENT_ECONOMICS,))
    with pytest.raises(ValueError, match="already registered"):
        reg.register(SEGMENT_ECONOMICS)


def test_a_key_and_a_requirement_detail_are_normalised_not_merely_checked() -> None:
    """`detail` is the LOOKUP KEY a caller reports disclosure under, and `key` is the registry's.

    Validating on `.strip()` while STORING the unstripped string accepts " commissioning" beside
    "commissioning" — two registry entries for one question, invisible to the duplicate guard —
    and a `detail` with a trailing space that NO caller key can ever match, so the panel refuses
    forever while naming a requirement the filing satisfies. The guard is the normalisation, not
    the blank check.
    """
    assert Requirement(kind="tag", detail="  x  ", why=" y ").detail == "x"
    assert PanelSpec(key=" k ", tier="name", title=" T ", changes_the_call="c").key == "k"

    reg = PanelRegistry((PanelSpec(key="dup", tier="name", title="T", changes_the_call="c"),))
    with pytest.raises(ValueError, match="already registered"):
        reg.register(PanelSpec(key=" dup ", tier="name", title="T", changes_the_call="c"))


def test_a_requirement_key_that_matches_nothing_is_refused_not_read_as_absent() -> None:
    """A mis-keyed `have`/`because` is a WIRING bug, and the two ways it fails are both silent.

    A `have` key that matches no requirement leaves the real one defaulting to False, so the
    panel refuses LOUDLY and names a requirement the filing actually satisfies — worse than a
    blank tile, because a named refusal is believed. A mis-keyed `because` drops the extractor's
    verbatim words, leaving the generic head, which is the one thing `_explain` exists to carry.
    """
    reg = default_registry()
    with pytest.raises(KeyError, match="does not have"):
        reg.decide("commissioning", declared=True, have={"property & equipment": True})
    with pytest.raises(KeyError, match="does not have"):
        reg.decide(
            "commissioning", declared=True, have={"property and equipment": False},
            because={"ppe": WERN_NO_PPE},
        )
    # ...and the correctly-keyed call still answers, so the guard is not simply refusing everything.
    assert reg.decide(
        "commissioning", declared=True, have={PPE_KEY: True}, config=PPE_CFG
    ).state == "ready"


def test_the_unregistered_panel_refusal_names_the_registered_set() -> None:
    """House convention (`require_sleeve`): refuse an unlisted value NAMING the admissible set.

    "unknown panel" alone leaves the operator hunting for which declaration to edit; the likely
    cause is a typo one character from a real key.
    """
    with pytest.raises(KeyError, match="commissioning"):
        default_registry().decide("comissioning", declared=True)


# --- review fixes, each pinned with the failure it closes -------------------------------------

def test_a_new_topic_must_state_its_own_absence_meaning_or_fail_loudly() -> None:
    """The guard reads the TOPIC PATTERN, not the `what` LABEL.

    Keyed on `what`, the guard made a DISPLAY STRING load-bearing — the rule this repo holds
    because display text drifts — and failed open in the way that matters: a caller passing a new
    `topic` and forgetting BOTH keywords inherited the segment clause AND had its note mislabelled
    "segment", so
    the refusal was wrong twice and silent about both. Observed: a `goodwill` topic returned
    *"no report naming a segment — a single-segment filer discloses none"*.
    """
    import re as _re

    from vinci.edgar.segments import _pick_report

    with pytest.raises(ValueError, match="must state what ABSENCE means"):
        _pick_report("<FilingSummary></FilingSummary>", topic=_re.compile("goodwill"))
    # The segment route still needs no keyword — it is the one topic the default clause is true of.
    from vinci.edgar.segments import SegmentReportUnavailableError
    with pytest.raises(SegmentReportUnavailableError):
        _pick_report("<FilingSummary></FilingSummary>")


def test_a_blank_absence_clause_is_the_same_hole_as_a_missing_one() -> None:
    """`absent_means=""` passed a None-only check and shipped a refusal explaining nothing."""
    import re as _re

    from vinci.edgar.segments import _pick_report

    for blank in ("", "   "):
        with pytest.raises(ValueError, match="may not be blank"):
            _pick_report("<FilingSummary></FilingSummary>", topic=_re.compile("goodwill"),
                         what="goodwill note", absent_means=blank)


def test_two_requirements_sharing_a_detail_are_probed_separately() -> None:
    """`detail` alone as the lookup key collapsed them into ONE probe.

    A panel could then report READY with a disclosure never probed, and the mis-key guard could not
    see it because the key it was handed was legitimate. The key is kind-qualified for this reason.
    """
    spec = PanelSpec(
        key="two", tier="name", title="T", changes_the_call="c",
        requires=(Requirement(kind="tag", detail="revenue", why="a"),
                  Requirement(kind="rfile_note", detail="revenue", why="b")))
    reg = PanelRegistry((spec,))
    # Satisfying only the TAG leaves the note unprobed — which must refuse, not pass.
    d = reg.decide("two", declared=True, have={"tag:revenue": True})
    assert d.state == "refused"
    assert [r.kind for r in d.missing] == ["rfile_note"]
    assert reg.decide(
        "two", declared=True,
        have={"tag:revenue": True, "rfile_note:revenue": True}).state == "ready"


def test_a_cohort_panel_probes_this_filers_note_not_the_one_it_was_written_against() -> None:
    """THE DESIGN-SYNC GAP: the approved plan's `config_schema` was dropped silently.

    The design says a cohort panel varies per name by *"the metric pair, the note name, the
    segment"*, and argues its own case with WERN — a trucking filer commissioning tractors asks the
    same economic question under a different note name. Yet `commissioning` hardcoded
    "property and equipment", ALPHABET's heading, on the SHARED spec. A WERN panel would have probed
    for Alphabet's note and refused naming the wrong filer's accounts, contradicting the argument in
    the module's own docstring.
    """
    reg = default_registry()
    wern = {"note_name": "revenue equipment"}
    ok = reg.decide("commissioning", declared=True,
                    have={"rfile_note:revenue equipment": True}, config=wern)
    assert ok.state == "ready"
    bad = reg.decide("commissioning", declared=True,
                     have={"rfile_note:revenue equipment": False}, config=wern)
    assert [r.detail for r in bad.missing] == ["revenue equipment"]
    assert "property and equipment" not in bad.reason, "refused naming Alphabet's note, not WERN's"


def test_an_unset_note_name_refuses_rather_than_probing_the_default() -> None:
    """Silently probing the default is how the wrong filer's note gets read as this one's."""
    d = default_registry().decide("commissioning", declared=True, have={}, config=None)
    assert d.state == "refused"
    assert "'note_name' is not set" in d.reason


def test_substance_is_decided_before_any_form_complaint() -> None:
    """The order inside `decide` is load-bearing, and this patch got it wrong once.

    With the missing-config refusal above the `declared` check, a panel that does not apply to a
    name reported REFUSED for want of a note name it never needed — a loud tile for a question
    nobody asked, which is the gating rule inverted.
    """
    d = default_registry().decide("commissioning", declared=False, have={}, config=None)
    assert d.state == "not_in_set"
    assert d.reason == ""


def test_a_config_schema_and_its_requirements_must_agree() -> None:
    """A key nothing reads is a silent no-op at every call site; one nothing declares cannot be
    supplied."""
    with pytest.raises(ValidationError, match="config_schema does not declare"):
        PanelSpec(key="a", tier="name", title="T", changes_the_call="c",
                  requires=(Requirement(kind="tag", detail="d", why="w", config_key="k"),))
    with pytest.raises(ValidationError, match="no requirement reads"):
        PanelSpec(key="b", tier="name", title="T", changes_the_call="c",
                  config_schema={"orphan": "nothing reads this"})
