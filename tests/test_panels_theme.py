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
    assert "othing here is measured" in THEME_THESIS.caveat  # case-agnostic on the lead word
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


def test_the_tab_strip_offers_no_tab_that_cannot_be_selected_node() -> None:
    """A THEME ROW'S `ticker` IS A DRIVER KEY, and the tab strip is a NAME strip.

    Deriving tabs from every row appended six driver tabs that could not be selected: clicking one
    set the asked-for value to something not in the ticker list, so the view fell back to the first
    ticker and NO tab highlighted. A control that looks live and does nothing is worse than an
    absent one — the reader concludes the data is empty rather than that the link is dead.
    """
    import shutil
    import subprocess

    import pytest

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = r"""
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { panelGridHtml } = await import(pathToFileURL(
  path.resolve("frontend/views/shared/panels.js")).href);
const base = { changes_the_call: "c", caveat: "", cadence: "event", sources: [], value: {},
  missing: [], reason: "" };
const rows = [
  // The sources payload groups by the panel that shows each number; the flat `refs` shape this
  // fixture used no longer builds a body, so the row would correctly demote to a refusal and the
  // assertion below would be reading the wrong tile.
  { ...base, ticker: "AORT", tier: "universal", key: "sources", title: "S", state: "ready",
    value: { by_panel: [{ key: "the_call", title: "The call", refs: ["r"] }],
             n_panels: 1, n_refs: 1 } },
  { ...base, ticker: "ai-datacenter", tier: "theme", key: "theme_thesis", title: "T",
    state: "refused", missing: [{ kind: "metric_path", detail: "thesis_card", why: "W" }],
    reason: "metric_path 'thesis_card' — W. no thesis card is declared" },
];
const html = panelGridHtml(rows, { ticker: "AORT" });
const tabs = (await import(pathToFileURL(
  path.resolve("frontend/views/shared/panels.js")).href)).tabTickers(rows);
// A theme tile still renders on a name's page (the tier attaches to the driver)...
const themeShown = /ai-datacenter/i.test(html);
// ...and its subject is named correctly.
const saysDriver = /applies to this driver/.test(html);
const saysName = /applies to this name/.test(html);
// The `why` appears ONCE, because `reason` already carries it.
const whyCount = (html.match(/>W</g) || []).length + (html.match(/— W\./g) || []).length;
console.log(JSON.stringify({ themeShown, saysDriver, saysName, whyCount, tabs,
  tabsExcludeDrivers: !tabs.includes("ai-datacenter"),
  tabsKeepNames: tabs.includes("AORT") }));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr
    got = json.loads(out.stdout)
    assert got["themeShown"] is True
    assert got["saysDriver"] is True
    assert got["saysName"] is False, "a theme tile's subject is a driver, not a name"
    assert got["whyCount"] == 1, "the requirement's why must not be printed twice"
    assert got["tabsExcludeDrivers"] is True, "a driver key must not become an unselectable tab"
    assert got["tabsKeepNames"] is True
    assert got["tabs"] == ["AORT"]


def test_a_refusal_whose_reason_omits_the_why_still_shows_it_node() -> None:
    """`decide()`'s MISSING-CONFIG branch composes its own sentence and never mentions `why`, so an
    unconditional de-dup would drop the explanation entirely — on exactly the refusal a
    half-onboarded name hits. Latent on today's corpus; pinned so it stays that way."""
    import shutil
    import subprocess

    import pytest

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = r"""
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { panelGridHtml } = await import(pathToFileURL(
  path.resolve("frontend/views/shared/panels.js")).href);
const html = panelGridHtml([{ ticker: "WERN", tier: "cohort", key: "commissioning",
  title: "C", state: "refused", changes_the_call: "c", caveat: "", cadence: "event",
  sources: [], value: {},
  missing: [{ kind: "rfile_note", detail: "revenue equipment", why: "THE ONLY EXPLANATION" }],
  reason: "rfile_note config 'note_name' is not set for this name, so the panel would probe the "
        + "DEFAULT 'property and equipment'" }], { ticker: "WERN" });
console.log(JSON.stringify({ explanationSurvives: /THE ONLY EXPLANATION/.test(html) }));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout)["explanationSurvives"] is True


def test_a_ready_theme_row_cites_the_real_card_not_a_placeholder() -> None:
    """A literal `<driver>.json` in a sources list reads as provenance and is not."""
    from vinci.monitor import theme_falsifier_rows
    from vinci.panels_emit import theme_panel_rows
    from vinci.themes.thesis import load_all_theses

    cards, _p = load_all_theses(data_dir=ROOT / "data")
    rows = [json.loads(r.model_dump_json())
            for r in theme_falsifier_rows(cards, today=TODAY)]
    out = theme_panel_rows(driver_keys=_drivers(), declared_cards=_cards(),
                           theme_falsifiers=rows, today=TODAY)
    ready = [r for r in out if r.state == "ready"]
    assert ready, "no theme row resolved ready — this check would prove nothing"
    for r in ready:
        assert r.sources, f"{r.ticker} resolved ready citing nothing"
        assert "<driver>" not in r.sources[0]
        assert f"thesis/{r.ticker}.json" in r.sources[0]
        assert (ROOT / "data" / "themes" / "thesis" / f"{r.ticker}.json").is_file(), (
            f"{r.ticker} cites a card that does not exist")
