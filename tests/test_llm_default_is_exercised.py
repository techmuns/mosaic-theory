"""The configured LLM must be one that has actually PRODUCED a committed synthesis.

THE INCIDENT THIS CLOSES (2026-09-01). The default was bumped to `claude-opus-5` on 2026-08-29.
No dossier was assembled with synthesis for the next three days, so nobody learned that Opus 5
returns a `tool_use` block MISSING REQUIRED FIELDS roughly half the time — `synthesize()` refuses
it, and the assembly hard-stops. Measured: TECX 5 FAIL / 4 PASS, SMPL 2 FAIL / 1 PASS, both on
Opus 5; TECX 2 PASS / 0 FAIL on 4.8. The knob was reverted by operator ruling.

WHY THE RECORDED FALSIFIER MISSED IT. The bump was accepted with the falsifier "untraceable figures
or mis-cites appearing in fresh extractions" — a GROUNDEDNESS watch. The failure was not bad
content but ABSENT content. No groundedness check can see a synthesis that was never produced.

WHAT THIS TEST IS. The cheapest honest guard: a model the fleet has never successfully used is
UNVERIFIED on the path that matters, and saying so offline costs nothing. It would have gone red
on 2026-08-29, at the moment of the bump, forcing the choice to be made deliberately — assemble one
name with the new model, or record the exemption — instead of discovered three days later by a
hard-stop.

WHAT IT IS NOT. It cannot test model QUALITY; nothing offline can. It tests that the configured
model has been exercised end-to-end at least once, which is a floor, not a ceiling.
"""

from __future__ import annotations

import json
import pathlib

from vinci.config import get_config

DOSS = pathlib.Path(__file__).resolve().parents[1] / "data" / "dossiers"

#: Models allowed WITHOUT a committed synthesis, each with the reason it is exempt. Empty by
#: design: a bump with no exercised artifact is exactly the state this guard refuses. To raise the
#: knob to a new model, either assemble one name with it (which clears this test the honest way) or
#: name it here WITH ITS REASON and accept the risk out loud.
#:
#: NOT A SKIP-LIST. An entry says "we know this is unexercised and chose to ship anyway" — which is
#: a defensible operator decision, and a recorded one. A bare bypass would not be.
UNEXERCISED_BY_RULING: dict[str, str] = {}


def _models_that_produced_a_synthesis() -> set[str]:
    """Every model named by a committed dossier that actually carries a synthesis."""
    out: set[str] = set()
    for f in sorted(DOSS.glob("*/dossier.json")):
        d = json.loads(f.read_text())
        if d.get("synthesis") and d.get("llm_model"):
            out.add(str(d["llm_model"]))
    return out


def test_the_configured_model_has_produced_at_least_one_committed_synthesis() -> None:
    """THE GUARD. Red the moment the knob moves to a model the fleet has never used."""
    configured = get_config().graph_llm_model
    if configured in UNEXERCISED_BY_RULING:
        return
    exercised = _models_that_produced_a_synthesis()
    assert exercised, (
        "no committed dossier carries both a synthesis and an llm_model — this guard cannot "
        "measure anything; check the fleet rather than deleting the test")
    assert configured in exercised, (
        f"graph_llm_model is {configured!r}, which has produced NO committed synthesis "
        f"(models that have: {sorted(exercised)}). A model unexercised on the synthesis path is "
        f"unverified where it matters: on 2026-08-29 the knob moved to claude-opus-5 and the "
        f"regression — a tool call missing required fields ~50% of the time — was found three days "
        f"later by an assembly hard-stop, not by any check. Either assemble one name with it, or "
        f"add it to UNEXERCISED_BY_RULING with the reason.")


def test_the_exemption_map_cannot_hide_a_working_model() -> None:
    """An exemption is for an UNEXERCISED model. Listing one that has demonstrably worked would
    make the map a bypass rather than a record, and would silently stop the guard measuring."""
    exercised = _models_that_produced_a_synthesis()
    overlap = sorted(set(UNEXERCISED_BY_RULING) & exercised)
    assert not overlap, (
        f"{overlap} are listed as unexercised but have produced committed syntheses — remove them; "
        "the map records models we chose to ship WITHOUT that evidence")


def test_the_fleets_syntheses_name_their_model() -> None:
    """The guard's input must exist. A dossier carrying a synthesis with no `llm_model` is an
    unattributable artifact — nothing can say what produced it, and this check would silently
    measure a smaller corpus than it appears to."""
    unattributed = [
        f.parent.name for f in sorted(DOSS.glob("*/dossier.json"))
        if (d := json.loads(f.read_text())).get("synthesis") and not d.get("llm_model")
    ]
    assert not unattributed, (
        f"{unattributed} carry a synthesis with no llm_model — the artifact cannot say what wrote "
        "it, so no guard can check the model that did")
