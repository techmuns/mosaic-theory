"""(phase 2) `PanelSpec` + the registry — what a monitor panel IS, and when it may render.

DOES THIS SELECT ON FORM? — answered in writing, as the standing rule on `DriverSpec` requires of
every spec and every gate built on one. FOUR gates have already failed that question.

  * **SET MEMBERSHIP IS SUBSTANCE.** Whether a panel belongs to a name is a claim about that
    name's ECONOMICS: a payments processor has no data-centre commissioning question, whatever it
    files. Membership is therefore DECLARED per name, never derived.
  * **REQUIREMENTS ARE FORM.** Whether the panel can be COMPUTED turns on disclosure — a tag, a
    note under a particular heading, a feed, an operator upload. That is form, and it is recorded
    separately, exactly as the rule demands.
  * **THE TRAP THIS BUILD WOULD HAVE WALKED INTO** is defining membership BY the requirement —
    "this filer has the note, so the panel applies". That inverts the rule and lets form decide
    substance. The commissioning panel is the live case: GOOGL's PP&E note is Alphabet's own
    presentation, and a trucking name commissioning tractors asks the SAME economic question under
    a different note name. Gate on "has Alphabet's note" and the trucking name is excluded for how
    it writes its accounts, which is the `machine_grade` failure one altitude down.

THE GATING RULE IS THE SAFETY PROPERTY, and it is that separation made visible:

  * `NOT_IN_SET` — substance says no. Renders NOTHING. No tile, no placeholder, no "n/a".
  * `REFUSED` — substance says yes, form cannot deliver. Renders LOUDLY, naming the requirement
    that failed.
  * `READY` — both hold.

These two must never look alike. An empty tile where a panel does not belong, and an empty tile
where a panel belongs but broke, is this repo's absent-vs-broken class — and a grid of tiles is
where it recurs most cheaply, because a reader scanning twelve panels reads silence as "fine".

WHAT THIS MODULE DOES NOT DO. It does not fetch, compute or render. It decides WHETHER a panel may
render and says why not — the smallest thing that can carry the safety property, so that the
property is testable before any panel exists to test it with.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

#: The four tiers from the approved design. `cohort` carries the leverage: it is a BUSINESS SHAPE,
#: not a sector label — tractor commissioning and server commissioning are one panel with a
#: different note name, and calling that tier "tech" would be the form error again.
PanelTier = Literal["universal", "cohort", "theme", "name"]

#: What a requirement is ABOUT. Kept as data rather than a callable so a spec can be read, diffed
#: and reviewed without executing it — and so a refusal can name the thing that failed.
RequirementKind = Literal["tag", "rfile_note", "metric_path", "feed", "upload",
                          "ledger_row", "snapshot_field", "criterion"]


class Requirement(BaseModel, frozen=True):
    """One thing the panel needs in order to compute — a claim about DISCLOSURE, never economics.

    `detail` is the specific thing: an XBRL tag, an R-file ShortName pattern, a dotted metric path.
    It is per NAME because the same economic question is disclosed differently by different
    filers, which is precisely why it cannot decide membership.
    """

    kind: RequirementKind
    detail: str
    #: Why this panel needs it, in one line — printed in the refusal, so a reader who has never
    #: seen the panel learns what is missing rather than a key they must go look up.
    why: str
    #: WHEN SET, `detail` IS A DEFAULT AND THE NAME SUPPLIES THE REAL ONE. This is the design's
    #: per-name config, and without it the tier promises were unfulfilled: cohort means *"the metric
    #: pair, the note name, the segment"* vary per name, yet `commissioning` hardcoded
    #: "property and equipment" — ALPHABET's note name — on the shared spec. A WERN commissioning
    #: panel would then probe for Alphabet's note and refuse naming the wrong filer's accounts,
    #: which is the exact failure this module's own docstring argues against. The key must appear in
    #: the owning `PanelSpec.config_schema`.
    config_key: str = ""

    @property
    def probe_key(self) -> str:
        """The key a caller reports this requirement's disclosure under.

        KIND-QUALIFIED, because `detail` alone collapsed two requirements that share a detail under
        different kinds into ONE probe — a panel could report READY with a disclosure never probed,
        and the mis-key guard could not see it because the key it was given was legitimate.
        """
        return f"{self.kind}:{self.detail}"

    def resolve(self, config: Mapping[str, str] | None) -> Requirement:
        """This requirement with its per-name detail applied, or itself when it takes no config."""
        if not self.config_key:
            return self
        supplied = (config or {}).get(self.config_key)
        if not supplied or not supplied.strip():
            return self
        return self.model_copy(update={"detail": supplied.strip()})

    @field_validator("detail", "why")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        # STRIPPED, NOT MERELY CHECKED. `detail` is the LOOKUP KEY a caller reports disclosure
        # under (`decide(have={detail: True})`), so a spec authored with a stray trailing space
        # would never match the key the caller sends and the panel would refuse forever with a
        # requirement the filing actually satisfies. `require_sleeve` normalises for the same
        # reason. Validating on `.strip()` while STORING the unstripped value is the bug.
        if not v.strip():
            raise ValueError("a requirement states WHAT it needs and WHY; neither may be blank")
        return v.strip()


class PanelSpec(BaseModel, frozen=True):
    """A monitor panel as a module: what it is, what it needs, how often, and what it must caveat.

    Same shape as `DriverSpec` and the sleeve registry deliberately — this is a new instance of an
    existing pattern, not a new architecture.
    """

    key: str
    tier: PanelTier
    #: Plain-words title. The panel grid is read by a human under time pressure.
    title: str
    requires: tuple[Requirement, ...] = ()
    #: WHAT VARIES PER NAME: config key → what it means, in words. The approved design lists
    #: `config_schema` as part of a panel and an earlier phase dropped it silently while declaring
    #: `render` deferred out loud. It is the mechanism behind the tier claims — universal panels
    #: vary by "config only", cohort panels by the note name and the metric pair — so without it
    #: "a trucking name reuses this panel with a different R-file note name" was an aspiration the
    #: type could not express.
    config_schema: dict[str, str] = {}
    #: How often the underlying source actually changes — the plan's Part 5 rule is to poll at the
    #: rate the SOURCE moves, never the rate one would like to know.
    cadence: Literal["event", "daily", "weekly", "monthly", "quarterly"] = "event"
    #: WHAT WOULD CHANGE THE CALL — the design's face-validity guard, made structural rather than
    #: left to review. The record states it plainly: *"every panel must state what would change the
    #: call; a panel that cannot answer that is decoration and should be cut, not shrunk"*, against
    #: the accepted risk that *"fifteen panels that each look important make none of them
    #: important"*. A guard enforced by reviewer attention is a guard that passes on a tired day, so
    #: it is a REQUIRED non-blank field: a decorative panel cannot be constructed at all.
    changes_the_call: str
    #: A standing qualification the panel must always carry beside its number. NOT an error — a
    #: fact about what the number is. The commissioning ratio needs one: it divides all
    #: not-yet-in-service assets by the technical-infrastructure member alone, so "49.7%" without
    #: that sentence reads as a commissioning rate and is not one. A panel whose number cannot be
    #: read correctly without a caveat and has nowhere to put it will mislead exactly as its
    #: docstring did.
    caveat: str = ""

    @model_validator(mode="after")
    def _schema_matches_requirements(self) -> PanelSpec:
        used = {r.config_key for r in self.requires if r.config_key}
        declared = set(self.config_schema)
        if used - declared:
            raise ValueError(
                f"panel {self.key!r} has requirement(s) keyed on {sorted(used - declared)} which "
                f"config_schema does not declare — a name could not know what to supply")
        if declared - used:
            raise ValueError(
                f"panel {self.key!r} declares config {sorted(declared - used)} that no requirement "
                f"reads — a config key nothing consumes is a silent no-op at every call site")
        return self

    @field_validator("key", "title", "changes_the_call")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        # `key` is the registry key AND the key a name declares a panel by, so it is normalised
        # rather than merely checked — " commissioning" registering beside "commissioning" is two
        # panels for one question, and `register`'s duplicate guard would not see it.
        if not v.strip():
            raise ValueError(
                "a panel carries a key, a human title, and a statement of what would change the "
                "call — the last is the face-validity guard: a panel that cannot answer it is "
                "decoration and must be cut, not shrunk")
        return v.strip()


# --------------------------------------------------------------------------------------------
# The gating rule. Three states, and the two that must never look alike.
# --------------------------------------------------------------------------------------------

#: `NOT_IN_SET` renders nothing at all. `REFUSED` renders loudly and names what failed. `READY`
#: renders the panel. The whole point of this module is that the first two are different values
#: rather than one falsy one — a caller cannot accidentally collapse them, because there is no
#: single "no" to collapse onto.
PanelState = Literal["not_in_set", "refused", "ready"]


@dataclass(frozen=True)
class PanelDecision:
    """Whether a panel may render for one name, and — when it may not — WHY, in words.

    `missing` is empty unless `state == "refused"`. `reason` is empty unless `state == "refused"`;
    a not-in-set panel has no reason to give BECAUSE IT HAS NO STORY: it was never asked for.
    """

    key: str
    state: PanelState
    missing: tuple[Requirement, ...] = ()
    reason: str = ""

    @property
    def renders(self) -> bool:
        """True when the panel occupies space on the grid — READY *or* REFUSED.

        A refusal RENDERS. This property exists so that a caller writing `if d.renders:` gets the
        loud-refusal behaviour by default and has to go out of its way to hide one.
        """
        return self.state != "not_in_set"


class PanelRegistry:
    """The panels this repo knows how to draw, by key.

    Deliberately a plain object over a module-level dict: a test builds its own registry rather
    than mutating a global, and a name's declared key can be checked against the registry at
    decision time instead of failing at render time.
    """

    def __init__(self, specs: Sequence[PanelSpec] = ()) -> None:
        self._by_key: dict[str, PanelSpec] = {}
        for spec in specs:
            self.register(spec)

    def register(self, spec: PanelSpec) -> None:
        if spec.key in self._by_key:
            raise ValueError(f"panel {spec.key!r} is already registered")
        self._by_key[spec.key] = spec

    def get(self, key: str) -> PanelSpec | None:
        return self._by_key.get(key)

    def __contains__(self, key: object) -> bool:
        return key in self._by_key

    def __len__(self) -> int:
        return len(self._by_key)

    def keys(self) -> tuple[str, ...]:
        return tuple(self._by_key)

    def decide(
        self,
        key: str,
        *,
        declared: bool,
        have: Mapping[str, bool] | None = None,
        because: Mapping[str, str] | None = None,
        config: Mapping[str, str] | None = None,
    ) -> PanelDecision:
        """Decide one panel for one name.

        `declared` is SUBSTANCE — did this name declare the panel beside its sleeve. `have` is
        FORM — for each requirement `detail`, whether the disclosure is actually there. The two
        arrive as separate arguments and are never derived from one another; that separation is
        the whole safety property, so it is enforced by the signature rather than by care.

        An UNDECLARED panel is `not_in_set` EVEN WHEN every requirement is satisfied. A name that
        happens to file the note does not thereby acquire the economic question — that inversion
        is the failure the standing rule was written for.

        A `have`/`because` KEY THAT MATCHES NO REQUIREMENT IS REFUSED, for the same reason an
        unregistered panel is: it is a wiring bug that would otherwise pass as an answer. A
        mis-keyed `have` reads as "not there" and refuses a panel whose disclosure is present —
        a LOUD refusal naming a requirement the filing actually satisfies, which is worse than a
        blank tile because it is believed. A mis-keyed `because` silently drops the extractor's
        own words, leaving the generic head — and the extractor's refusal reaching the reader
        verbatim is this module's whole job.
        """
        spec = self._by_key.get(key)
        if spec is None:
            # Not silence: a name declaring a panel that does not exist is a CONFIGURATION bug,
            # and configuration bugs that render as blank tiles are how a grid lies. Loud. The
            # admissible set is NAMED, per the registry convention (`require_sleeve`): a refusal
            # that says only "unknown" leaves the reader hunting for which entry to edit.
            raise KeyError(
                f"panel {key!r} is not registered; declared panels must exist — registered: "
                f"{sorted(self._by_key)}")
        have = have or {}
        because = because or {}
        # PER-NAME DETAILS FIRST: the requirements this name is actually probed against are the
        # spec's requirements with its own config applied, so a trucking name's commissioning panel
        # asks about ITS note and refuses naming ITS accounts — never Alphabet's.
        reqs = tuple(r.resolve(config) for r in spec.requires)
        details = {r.probe_key for r in reqs}
        unknown = sorted((have.keys() | because.keys()) - details)
        if unknown:
            raise KeyError(
                f"panel {key!r} was told about requirement(s) it does not have: {unknown}; it "
                f"requires {sorted(details)} (keys are '<kind>:<detail>'). A key matching no "
                f"requirement is a wiring bug, and silently reads as 'not there'.")
        # SUBSTANCE IS DECIDED BEFORE ANY FORM CHECK, and the order is load-bearing. An earlier
        # draft of this patch put the missing-config refusal above this line, so a panel that does
        # not apply to a name reported REFUSED for want of a note name it never needed — a loud
        # tile for a question nobody asked, which is the gating rule inverted. `not_in_set` wins
        # over every form complaint because a panel outside the set has no form to satisfy.
        if not declared:
            return PanelDecision(key=key, state="not_in_set")
        unfilled = tuple(r for r in reqs if r.config_key and not (config or {}).get(r.config_key))
        if unfilled:
            # A REFUSAL, not a raise: the panel genuinely applies and genuinely cannot be computed,
            # which is exactly the in-set-refused state. Raising would make an un-onboarded note
            # name look like a programming error rather than a step nobody has taken yet.
            return PanelDecision(
                key=key, state="refused", missing=unfilled,
                reason="; ".join(
                    f"{r.kind} config {r.config_key!r} is not set for this name, so the panel "
                    f"would probe the DEFAULT {r.detail!r} — "
                    f"{spec.config_schema.get(r.config_key, '')}"
                    for r in unfilled))
        missing = tuple(r for r in reqs if not have.get(r.probe_key, False))
        if missing:
            return PanelDecision(
                key=key,
                state="refused",
                missing=missing,
                reason="; ".join(_explain(r, because.get(r.probe_key, "")) for r in missing),
            )
        return PanelDecision(key=key, state="ready")


# --------------------------------------------------------------------------------------------
# The registry as it actually stands. Two panels, because two extractors exist (#578, #587).
# A panel is registered when something can DRAW it — not when it would be nice to have one.
# --------------------------------------------------------------------------------------------

COMMISSIONING = PanelSpec(
    key="commissioning",
    tier="cohort",
    title="Built but not running",
    requires=(
        Requirement(
            kind="rfile_note",
            detail="property and equipment",
            why="the not-yet-in-service and in-service balances are only in the PP&E note; "
            "no XBRL tag carries the split",
            config_key="note_name",
        ),
    ),
    config_schema={
        "note_name": "the heading this filer presents its fixed-asset note under — Alphabet says "
        "'property and equipment', and a trucking name commissioning tractors asks the SAME "
        "economic question under a name of its own, which is why this is config and not code",
    },
    cadence="quarterly",
    changes_the_call="A ratio that climbs while the in-service base stops growing says capital is "
    "going in and not yet earning — the duration question the memo calls the whole trade. Falling "
    "back toward the in-service growth rate says the buildout is converting.",
    caveat="Assets not yet in service spans EVERY asset type, while the denominator is the "
    "technical-infrastructure member alone — so this is not a commissioning RATE. The "
    "like-for-like figure is reported beside it.",
)

SEGMENT_ECONOMICS = PanelSpec(
    key="segment_economics",
    tier="cohort",
    title="Segment revenue and operating income",
    requires=(
        Requirement(
            kind="rfile_note",
            detail="segment",
            why="per-segment operating income is disclosed in the segment note, not as a "
            "top-level tag",
            config_key="note_name",
        ),
    ),
    config_schema={
        "note_name": "the heading this filer presents segment economics under; 'segment' is the "
        "common case but the report that carries the FIGURES is named per filer",
    },
    cadence="quarterly",
    changes_the_call="Operating income falling in a segment whose revenue still grows re-prices "
    "the mix: it means the growth is being bought. Which segment carries the margin is the thing "
    "a single consolidated line hides.",
)


def default_registry() -> PanelRegistry:
    """The panels this repo can draw today. Phases 3–5 add the universal, cohort and theme sets."""
    return PanelRegistry((COMMISSIONING, SEGMENT_ECONOMICS))


def _explain(req: Requirement, upstream: str) -> str:
    """One missing requirement, in words a human can act on.

    `upstream` is the EXTRACTOR'S OWN refusal, passed through verbatim when there is one. The
    panel never re-derives why a requirement failed: the extractors already distinguish "no such
    report", "the report has no numbers", "several match and choosing would file the wrong
    table's figures" and "the columns do not line up", and a second opinion computed here would
    be a divergent parser of the same question — the class that has already cost this repo a
    false reconcile caveat. So the panel's job is to SHOW the refusal, not to have one.
    """
    head = f"{req.kind} {req.detail!r} — {req.why}"
    return f"{head}. {upstream}" if upstream else head
