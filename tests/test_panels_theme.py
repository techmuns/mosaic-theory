"""(phase 5) Theme panels — attached to the driver, and the two absences kept apart.

The phase's precondition is recorded in `docs/records/2026-09-10-theme-panel-terms-verified.md`:
every trigger on every committed card is `{trigger, deadline, basis}` — prose, a date and a source,
with no metric anywhere — so this panel measures nothing and says so.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

from vinci.panels_theme import THEME_THESIS, basis_kind, resolve_theme, theme_payload

ROOT = pathlib.Path(__file__).resolve().parent.parent
TODAY = dt.date(2026, 9, 10)

# FROZEN, copied verbatim from the committed cards (2026-09-10). A timing basis and an external one
# — the two shapes the panel must never render alike.
TIMING = ("one full scheduled print cycle, late Oct - early Dec 2026 — every named "
          "representative's next quarterly print lands inside it")
EXTERNAL = "public price lists + customer disclosures; operator-selected 2026-08-30"


def _cards() -> set[str]:
    return {json.loads(p.read_text())["driver_key"]
            for p in (ROOT / "data" / "themes" / "thesis").glob("*.json")}


def _drivers() -> list[str]:
    d = ROOT / "data" / "themes"
    return sorted({p.stem for p in (d / "baskets").glob("*.json")}
                  | {p.stem for p in (d / "economics").glob("*.json")})


def test_a_tracked_driver_with_no_card_and_one_with_an_unswept_card_refuse_differently() -> None:
    """THE DEFECT THIS PHASE SHIPPED AND THE CORPUS CAUGHT, in one assertion.

    The committed 2026-08-11 snapshot predates the theme sweep and carries ZERO falsifier rows, so
    the first cut refused every driver with "no thesis card is declared" — FALSE for the two that
    have one. "The card is absent" and "the sweep has not run" recommend OPPOSITE actions (declare a
    thesis, or re-run the monitor), so they may not share a sentence.
    """
    got = {k: d for k, d, _ in resolve_theme(
        ["ai-datacenter", "ai-value-migration"], declared_cards=_cards(),
        theme_falsifiers=[], today=TODAY)}
    no_card, unswept = got["ai-datacenter"].reason, got["ai-value-migration"].reason
    assert got["ai-datacenter"].state == got["ai-value-migration"].state == "refused"
    assert no_card != unswept
    assert "no thesis card is declared" in no_card
    assert "HAS a declared thesis card" in unswept
    assert "re-run" in unswept, "the unswept case names the action that fixes it"
    assert "no thesis card is declared" not in unswept


def test_membership_is_tracking_not_having_a_card() -> None:
    """Deriving the set from the cards would make a tracked driver with no thesis INVISIBLE — the
    inversion the standing rule on `DriverSpec` exists to prevent, and the case this phase most
    wants seen. `ai-datacenter` is the live example: a 56-member basket, an economics roll-up, and
    no declared thesis at all."""
    keys = [k for k, _d, _p in resolve_theme(
        _drivers(), declared_cards=_cards(), theme_falsifiers=[], today=TODAY)]
    assert "ai-datacenter" in keys
    assert "ai-datacenter" not in _cards()


def test_a_timing_basis_and_an_external_one_are_not_rendered_alike() -> None:
    """A basis naming public price lists is a real source OUTSIDE this repo. Marking it the same as
    one that is checkable against filing cadence lets an unchecked claim borrow the credibility of
    a checked one."""
    assert basis_kind(TIMING) == "timing"
    assert basis_kind(EXTERNAL) == "external"
    assert basis_kind("") == "none"
    assert basis_kind("   ") == "none"


def test_the_payload_counts_the_bases_it_cannot_verify() -> None:
    rows = [
        {"driver_key": "d", "kind": "first-confirming", "trigger": "t1",
         "deadline": "2026-12-15", "basis": TIMING, "deadline_passed": False},
        {"driver_key": "d", "kind": "falsifier", "trigger": "t2",
         "deadline": "2027-03-31", "basis": EXTERNAL, "deadline_passed": False},
        {"driver_key": "other", "kind": "falsifier", "trigger": "t3",
         "deadline": "2027-01-01", "basis": TIMING, "deadline_passed": True},
    ]
    p = theme_payload(rows, driver_key="d", today=TODAY)
    assert p is not None
    assert len(p["triggers"]) == 2, "another driver's rows must not leak in"
    assert p["n_unverifiable"] == 1
    assert p["triggers"][0]["kind"] == "first-confirming", "what would make it RIGHT leads"
    assert p["triggers"][0]["days_remaining"] == (dt.date(2026, 12, 15) - TODAY).days


def test_a_corrupted_deadline_still_renders_its_row() -> None:
    """Deadlines are ISO by declare-time validation, so an unparseable one is a corrupted card. The
    row must still appear — a card that cannot be read must not vanish from the panel that exists
    to watch it."""
    p = theme_payload([{"driver_key": "d", "kind": "falsifier", "trigger": "t",
                        "deadline": "not-a-date", "basis": TIMING, "deadline_passed": False}],
                      driver_key="d", today=TODAY)
    assert p is not None and len(p["triggers"]) == 1
    assert p["triggers"][0]["days_remaining"] is None


def test_the_panel_says_it_measures_nothing() -> None:
    """Verified before the panel was written: no trigger on any committed card carries a metric or
    a threshold. The caveat is the channel that keeps the page honest about it."""
    assert "nothing here is measured" in THEME_THESIS.caveat
    assert THEME_THESIS.tier == "theme"
    assert THEME_THESIS.changes_the_call.strip()
    for p in (ROOT / "data" / "themes" / "thesis").glob("*.json"):
        card = json.loads(p.read_text())
        for t in [card["first_confirming"], *card["falsifiers"]]:
            assert set(t) == {"trigger", "deadline", "basis"}, (
                f"{p.stem} gained a field — if it is a metric, this panel can now measure and "
                f"this assertion should be retired deliberately")


def test_a_swept_card_resolves_ready_over_the_real_cards() -> None:
    """CORPUS BEFORE SYNTHETIC: the READY path must be reachable from the real committed cards, or
    every refusal above proves nothing."""
    from vinci.monitor import theme_falsifier_rows
    from vinci.themes.thesis import load_all_theses

    cards, _problems = load_all_theses(data_dir=ROOT / "data")
    rows = [json.loads(r.model_dump_json())
            for r in theme_falsifier_rows(cards, today=TODAY)]
    assert rows, "no card produced a sweep row — this check would prove nothing"
    got = {k: (d.state, p) for k, d, p in resolve_theme(
        _drivers(), declared_cards=_cards(), theme_falsifiers=rows, today=TODAY)}
    ready = [k for k, (s, _) in got.items() if s == "ready"]
    assert set(ready) == _cards(), "exactly the declared cards resolve ready"
    for k in ready:
        assert got[k][1]["triggers"], f"{k} resolved ready with no triggers"
