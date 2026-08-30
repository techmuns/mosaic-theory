"""The theme thesis card — the HUMAN-DECLARED record of WHY a driver is a bet, and its gate.

Brief Items 1/4 (rulings R1–R5 adopted 2026-08-28; recorded in
``docs/records/2026-08-29-anchoring-falsifier-measured-in-scoring-report.md``). The themes lane
could carry a driver from detection to Stage-4 ratification with its thesis living nowhere but the
operator's head — the theme-level analog of the pre-A4 state ``vinci/edge_basis.py`` closed for
names ("no verdict without saying what the edge IS"). The card is that record at driver level:
the binding-mechanism type, the market's mistake stated as a MECHANISM, the null thesis, and
falsifiers with calendar deadlines.

OPERATOR-TYPED ONLY, like ``DatedTrigger``: the machine never drafts a card field, and no LLM tool
schema may carry these field names (pinned — the schema-walk guard beside ``CandidateTheme``'s
no-conclude pin). ``mechanism`` is a CLOSED enum (ruling R1, the predecessor framework's seven,
adapted), face-validity-frozen and never outcome-tuned: it routes surface grouping now and
theme-tier panel attachment later (the ``PanelSpec`` plan, §5.0); it is never a score.

THE GATE: ``require_thesis_card`` refuses a Stage-4 freeze for a card-less driver — wired into the
``themes-forward`` preflight cluster (the #424 refuse-with-NOTHING-written pattern). A card-less
driver's page renders a loud ``THESIS UNSTATED`` stamp (ruling R2 — absence must never look like
passage; the absent-vs-broken rule), and the three drivers frozen before this gate existed stay
frozen: the gate binds NEW freezes, the stamp covers the surface.

Storage (ruling R3): ``data/themes/thesis/<driver_key>.json`` beside the frozen baskets; a
re-declare requires ``supersede`` and archives the prior card under ``thesis/archive/`` — the
``write_baskets`` archive-and-reissue pattern in this same package, not new machinery. The card
carries a machine-stamped ``mirror_slug`` (from the registry at write time, never operator-typed)
so the stdlib-only frontend build can mirror it without importing vinci — drift is pinned by a
test comparing every committed card's stamp to the registry.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ValidationError, field_validator

from vinci.scenarios import DatedTrigger

THESIS_SUBDIR = "themes/thesis"

#: The surface stamp for a card-less driver — one string, shared by every renderer that needs it,
#: so the loud state cannot drift into three wordings.
THESIS_UNSTATED = "THESIS UNSTATED"


class ThesisMechanism(StrEnum):
    """WHICH mispricing channel binds the theme's members to the driver — ruling R1's closed seven
    (the predecessor framework's ``mechanism_type`` controlled list, adapted). The enum describes
    the CHANNEL of the claimed mistake, never the valuation instrument: names under one theme may
    underwrite on different recipes. Face-validity-frozen; a driver that seems to need two values
    means the ENUM is wrong — fix the enum, never force the mapping."""

    CUSTOMER_SIDE = "customer-side"
    COMPANY_SIDE = "company-side"
    POLICY_SIDE = "policy-side"
    SUPPLY_SIDE = "supply-side"
    POSITIONING_SIDE = "positioning-side"
    CATALYST_SIDE = "catalyst-side"
    VALUATION_DISLOCATION = "valuation-dislocation"


def _iso_or_refuse(value: str, *, what: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{what} deadline {value!r} is not an ISO date — a falsifier the monitor cannot "
            f"place in time is the deadline-less class the card exists to end"
        ) from exc


class ThemeThesis(BaseModel, frozen=True):
    """One driver's thesis card. Every field has a named CONSUMER (v2 rule — a consumer-less field
    is the guard-that-cannot-fire class): ``declared_date`` leads the render (stamp-position rule);
    ``mechanism`` groups the surface and will route panel attachment; ``market_mistake`` +
    ``null_thesis`` render in one block beside the page's priced read; ``first_confirming`` +
    ``falsifiers`` feed the monitor's deadline sweep (brief Item 2); ``note`` is rationale only.

    LIMIT, STATED: mechanism-not-conclusion in ``market_mistake`` is human discipline — the
    machine checks presence and shape only, and pretending otherwise would be a fake guard."""

    driver_key: str            # must resolve in DRIVER_SPECS — enforced at write, where the
    #                            registry is importable without a schema→registry cycle
    declared_date: date
    mechanism: ThesisMechanism
    market_mistake: str        # the MECHANISM the market gets wrong — never the conclusion
    null_thesis: str           # what the world looks like if the driver is noise
    first_confirming: DatedTrigger        # earliest datapoint that should confirm, with deadline
    falsifiers: tuple[DatedTrigger, ...]  # >=1 — the scenarios.py type, imported never duplicated
    note: str = ""
    #: MACHINE-STAMPED at write time from ``DriverSpec.mirror_slug`` — never operator-typed. The
    #: stdlib-only frontend build reads it to place the mirror; committed cards are pinned against
    #: the registry so the binding cannot drift (the #412 mirror-binding lesson). "" == the driver
    #: has no mirror yet (a real state — glp1-demand-shift), and no frontend mirror is written.
    mirror_slug: str = ""

    @field_validator("market_mistake", "null_thesis")
    @classmethod
    def _substantive(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "blank — the card exists to make the operator state it; an empty declaration "
                "recorded as present would be worse than the stamp")
        return v

    @field_validator("falsifiers")
    @classmethod
    def _at_least_one_dated(cls, v: tuple[DatedTrigger, ...]) -> tuple[DatedTrigger, ...]:
        if not v:
            raise ValueError(
                "no falsifiers — a thesis with nothing that can kill it is not a thesis; "
                "declare at least one DatedTrigger (trigger, deadline, basis)")
        for t in v:
            _iso_or_refuse(t.deadline, what=f"falsifier {t.trigger[:40]!r}")
        return v

    @field_validator("first_confirming")
    @classmethod
    def _confirming_dated(cls, v: DatedTrigger) -> DatedTrigger:
        _iso_or_refuse(v.deadline, what="first_confirming")
        return v


# --------------------------------------------------------------------------------------------------
# storage — beside the frozen baskets, same data_dir-keyed path discipline as `forward.py`
# --------------------------------------------------------------------------------------------------
def thesis_path(driver: str, *, data_dir: Path) -> Path:
    return data_dir / THESIS_SUBDIR / f"{driver}.json"


def _archive_path(card: ThemeThesis, *, data_dir: Path) -> Path:
    return (data_dir / THESIS_SUBDIR / "archive"
            / f"{card.driver_key}-{card.declared_date.isoformat()}.json")


def load_thesis(driver: str, *, data_dir: Path) -> ThemeThesis | None:
    """The card, or ``None`` — and None IS the ``THESIS UNSTATED`` state, never an error: the
    stamp renders it loudly; only the freeze gate turns it into a refusal."""
    path = thesis_path(driver, data_dir=data_dir)
    if not path.exists():
        return None
    return ThemeThesis.model_validate_json(path.read_text())


def write_thesis(card: ThemeThesis, *, data_dir: Path, supersede: bool = False) -> Path:
    """Validate against the registry, refuse a silent overwrite, write the card.

    The registry check lives HERE (not on the schema) because ``drivers.py`` imports the schema
    module family — validating at write keeps the direction acyclic while still making an unknown
    key unwritable. Overwrite discipline is ``assert_basket_writable``'s: an existing card without
    ``supersede`` refuses with NOTHING written; with it, the prior card is archived first
    (archive-and-reissue, never in-place edit)."""
    from vinci.themes.drivers import DRIVER_SPECS

    spec = DRIVER_SPECS.get(card.driver_key)
    if spec is None:
        raise ValueError(
            f"unknown driver {card.driver_key!r} — a card must bind to a registry DriverSpec "
            f"(live: {sorted(DRIVER_SPECS)})")
    if card.mirror_slug != spec.mirror_slug:
        # the stamp is the machine's to write — a hand-typed slug is exactly the unverifiable
        # binding the mirror_slug field exists to end (#412)
        raise ValueError(
            f"mirror_slug {card.mirror_slug!r} does not match the registry's "
            f"{spec.mirror_slug!r} for {card.driver_key} — the declare path stamps this; "
            f"do not type it")
    path = thesis_path(card.driver_key, data_dir=data_dir)
    if path.exists():
        prior = ThemeThesis.model_validate_json(path.read_text())
        if not supersede:
            raise FileExistsError(
                f"a thesis card for {card.driver_key!r} exists (declared "
                f"{prior.declared_date.isoformat()}). Re-declare with supersede to archive it "
                f"and write the new card — NOTHING was written.")
        # THE ARCHIVE NAME IS DATE-KEYED, so two supersessions of cards sharing a `declared_date`
        # would collide and the second would overwrite the first archive — losing exactly what
        # archiving exists to keep. This is the SAME HOLE `write_baskets` already found and closed
        # (`forward.py`, pinned by `test_two_supersessions_on_one_day_do_not_collide_in_the
        # _archive`), reproduced here by copying the shape without the fix. Declaring a card,
        # correcting a typo, and correcting again in one session is a normal thing to do, so it is
        # disambiguated rather than assumed rare.
        base = _archive_path(prior, data_dir=data_dir).with_suffix("")
        base.parent.mkdir(parents=True, exist_ok=True)
        arch = base.with_suffix(".json")
        n = 2
        while arch.exists():
            arch = base.with_name(f"{base.name}-{n}").with_suffix(".json")
            n += 1
        arch.write_text(path.read_text())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(card.model_dump_json(indent=1) + "\n")
    return path


def stamped(card: ThemeThesis) -> ThemeThesis:
    """Return the card with ``mirror_slug`` stamped from the registry — the declare path calls
    this so the operator's file never carries (or needs) the binding."""
    from vinci.themes.drivers import DRIVER_SPECS

    spec = DRIVER_SPECS.get(card.driver_key)
    if spec is None:
        raise ValueError(
            f"unknown driver {card.driver_key!r} — a card must bind to a registry DriverSpec "
            f"(live: {sorted(DRIVER_SPECS)})")
    return card.model_copy(update={"mirror_slug": spec.mirror_slug})


def require_thesis_card(driver: str, *, data_dir: Path) -> ThemeThesis:
    """THE GATE — no Stage-4 freeze without a card ("no verdict without the edge", theme level).

    Raises with the remedy in the message; the CLI prints it and writes NOTHING (it runs in the
    #424 preflight cluster, before the ledger append)."""
    try:
        card = load_thesis(driver, data_dir=data_dir)
    except (ValidationError, ValueError) as exc:
        # A CORRUPT CARD IS NOT AN ABSENT ONE, and the gate must not conflate them: "declare it"
        # would be wrong advice for a file that exists and is broken. Raised as a stated refusal
        # rather than a traceback — the freeze still writes nothing either way.
        raise ValueError(
            f"the thesis card for {driver!r} exists but does not load "
            f"({str(exc).splitlines()[0]}) — repair or re-declare it; the freeze wrote nothing"
        ) from exc
    if card is None:
        raise FileNotFoundError(
            f"no theme thesis card for driver {driver!r} — Stage-4 ratification requires one "
            f"(theme thesis gate). Declare it: vinci theme-thesis declare {driver} "
            f"--file <card.json>")
    return card
