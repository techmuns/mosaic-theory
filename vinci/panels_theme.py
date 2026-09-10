"""(phase 5) THEME PANELS — attached to the DRIVER, not the ticker.

The design's third tier: *"theme | data-centre policy · model pricing | nothing — attaches to the
driver, not the ticker"*. A theme panel asks whether a declared thesis is still standing, so its
subject is a `driver_key` and its config is nothing — every driver that declares a thesis runs the
same panel over its own card.

WHAT IT DOES NOT DO, verified before it was written (`docs/records/2026-09-10-theme-panel-terms-
verified.md`): it puts NO number beside a theme falsifier. Every trigger on both committed cards is
`{trigger, deadline, basis}` — prose, a date and a source, with no metric or threshold anywhere. So
the panel surfaces the trigger, its deadline state and WHERE it would be checked. That is the same
answer `kills` reached one altitude down, and it is honest rather than empty: a criterion nobody can
check is not a criterion, and the `basis` is the half that says whether anyone can.

THE MEASUREMENT STAYS RESERVED. `ThemeFalsifierRow` records that indicator measurement "is the
PanelSpec plan's job, and this sweep must never grow into a rival panel" — so this panel CONSUMES
that sweep's rows rather than re-deriving deadlines from the cards. One answer, not two that could
disagree.

A LIVE DRIVER WITH NO DECLARED THESIS REFUSES, LOUDLY. `ai-datacenter` carries a frozen 56-member
basket and an economics roll-up and has no thesis card at all. That is IN THE SET BUT REFUSED — the
fund tracks it with capital-relevant machinery and has declared no thesis to watch — and it must
look nothing like a driver the panel does not apply to. Silence there would hide exactly the gap
worth seeing.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

from vinci.panels import PanelDecision, PanelRegistry, PanelSpec, Requirement

#: A basis that names one of these is checkable against filing cadence; anything else names a source
#: outside the repo and is reported UNVERIFIABLE rather than quietly treated as checked.
_TIMING_WORDS = ("print cycle", "quarterly print", "print cycles", "report by", "quarterly prints")

THEME_THESIS = PanelSpec(
    key="theme_thesis",
    tier="theme",
    title="Declared thesis — what would falsify it, and by when",
    requires=(
        Requirement(
            kind="metric_path",
            detail="thesis_card",
            why="the panel watches a DECLARED thesis; a driver with no card has no mechanism, no "
            "market mistake and no falsifiers, so there is nothing to hold to a deadline",
        ),
    ),
    cadence="event",
    changes_the_call="A falsifier whose window has closed is the thesis owing an answer — the "
    "fund said what would prove it wrong and by when, and the date arrived. It does not declare "
    "the thesis dead: the machine says the window closed, the human reads whether it fired.",
    caveat="No trigger on any committed card carries a metric or a threshold, so nothing here is "
    "measured — the panel shows the criterion, its deadline and WHERE it would be checked. A basis "
    "naming a source outside the repo is marked unverifiable, never silently treated as checked.",
)


def theme_registry() -> PanelRegistry:
    return PanelRegistry((THEME_THESIS,))


def basis_kind(basis: str) -> str:
    """`timing` | `external` | `none` — which sort of claim this basis makes.

    STATED RATHER THAN INFERRED AT RENDER TIME. A timing basis asserts that N print cycles land
    inside the window, which is falsifiable against real cadence and rots silently when a filer
    moves its reporting date. An external basis names public price lists or payer disclosures —
    real sources, outside this repo, and unverifiable from committed data. Rendering both the same
    way would let an unchecked claim borrow the credibility of a checked one.
    """
    if not basis.strip():
        return "none"
    low = basis.lower()
    return "timing" if any(w in low for w in _TIMING_WORDS) else "external"


def _days_to(deadline: str, today: _dt.date) -> int | None:
    try:
        return (_dt.date.fromisoformat(deadline) - today).days
    except ValueError:
        # Deadlines are ISO by declare-time validation, so an unparseable one is a CORRUPTED card.
        # Returning None renders "—" rather than raising, but the row still shows: a card that
        # cannot be read must not silently vanish from the panel that exists to watch it.
        return None


def theme_payload(rows: list[dict[str, Any]], *, driver_key: str,
                  today: _dt.date) -> dict[str, Any] | None:
    """The declared triggers for one driver, from the monitor's OWN sweep rows.

    `rows` are `ThemeFalsifierRow` dumps off the snapshot — never the cards themselves, so the
    deadline state the panel shows is the one the sweep computed.
    """
    mine = [r for r in rows if str(r.get("driver_key")) == driver_key]
    if not mine:
        return None
    triggers = []
    for r in mine:
        basis = str(r.get("basis") or "")
        triggers.append({
            "kind": r.get("kind"), "trigger": r.get("trigger"),
            "deadline": r.get("deadline"), "basis": basis,
            "basis_kind": basis_kind(basis),
            "deadline_passed": bool(r.get("deadline_passed")),
            "days_remaining": _days_to(str(r.get("deadline") or ""), today),
        })
    # First-confirming leads: it is the one trigger that says what would make the thesis RIGHT, and
    # a page that opens with three ways to be wrong reads as a thesis already in trouble.
    triggers.sort(key=lambda t: (t["kind"] != "first-confirming", str(t["deadline"])))
    return {
        "driver_key": driver_key, "triggers": triggers,
        "n_passed": sum(1 for t in triggers if t["deadline_passed"]),
        "n_unverifiable": sum(1 for t in triggers if t["basis_kind"] != "timing"),
    }


def resolve_theme(
    driver_keys: list[str],
    *,
    declared_cards: set[str],
    theme_falsifiers: list[dict[str, Any]],
    today: _dt.date,
    registry: PanelRegistry | None = None,
) -> list[tuple[str, PanelDecision, dict[str, Any] | None]]:
    """`(driver_key, decision, payload)` for every driver the fund tracks.

    SUBSTANCE IS "THE FUND TRACKS THIS DRIVER", not "the driver has a card". Deriving membership
    from the card would make a tracked driver with no declared thesis invisible — the inversion the
    standing rule on `DriverSpec` exists to prevent, and the one case this phase most wants seen.

    THREE OUTCOMES, NOT TWO, and the first cut of this function collapsed the middle one. A driver
    with a DECLARED CARD but no sweep rows is not a driver with no thesis: the committed 2026-08-11
    snapshot predates the theme sweep entirely and carries zero rows, so every driver refused with
    "no thesis card is declared" — FALSE for the two that have one. `declared_cards` is therefore an
    input rather than something inferred from the rows, because "the card is absent" and "the sweep
    has not run" are different states that recommend opposite actions: declare a thesis, or re-run
    the monitor.
    """
    reg = registry or theme_registry()
    out = []
    for key in sorted(driver_keys):
        payload = theme_payload(theme_falsifiers, driver_key=key, today=today)
        has_card = key in declared_cards
        if payload is not None:
            why = ""
        elif not has_card:
            why = (f"{key} is tracked by the fund — it carries a basket and/or an economics "
                   f"roll-up — but no thesis card is declared for it: no mechanism, no market "
                   f"mistake and no falsifiers on file. Nothing is broken; nothing was declared.")
        else:
            why = (f"{key} HAS a declared thesis card, but this monitor day carries no theme "
                   f"falsifier rows for it — the snapshot predates the sweep, or the sweep did not "
                   f"run. The thesis exists and is unwatched on this day; re-run `vinci monitor`. "
                   f"This is NOT the same as having declared no thesis.")
        out.append((key, reg.decide(
            "theme_thesis", declared=True,
            have={"metric_path:thesis_card": payload is not None},
            because={} if payload is not None else {"metric_path:thesis_card": why},
        ), payload))
    return out
