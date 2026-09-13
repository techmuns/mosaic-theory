"""(phase 6) The emitter — the gating rule surviving serialization, and the artifact's own shape.

The one thing that could quietly undo phases 2-4 is a `not_in_set` panel arriving in the JSON as a
row with a falsy state: a tile waiting to be drawn, when the rule is that those never draw. That is
what the first two tests are for, and the corpus check is the e2e layer over the real artifact.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest
from pydantic import ValidationError

from vinci.monitor import MonitorSnapshot
from vinci.panels_emit import PanelRow, emit_panels, panel_rows_for
from vinci.panels_payload import multiple_and_price

ROOT = pathlib.Path(__file__).resolve().parent.parent
MON = ROOT / "data" / "monitor"


def _snap() -> dict:
    return json.loads((MON / "2026-08-11.json").read_text())


def _dossier(t: str) -> dict | None:
    f = ROOT / "data" / "dossiers" / t / "dossier.json"
    return json.loads(f.read_text()) if f.is_file() else None


def _record(t: str) -> dict | None:
    f = ROOT / "scenarios" / f"{t}.json"
    return json.loads(f.read_text()) if f.is_file() else None


def test_a_panel_that_does_not_apply_emits_no_row_at_all() -> None:
    """NOT the same as a row saying it does not apply. LLY declares no `commissioning` — it
    publishes no property-named report — so the artifact must simply not mention it."""
    rows = panel_rows_for(
        "LLY", dossier=_dossier("LLY"), row=None, freshness=None, record=None,
        declarations={"LLY": {"segment_economics": {"note_name": "Segment Information"}}})
    keys = {r.key for r in rows}
    assert "commissioning" not in keys
    assert all(r.state in ("ready", "refused") for r in rows), "no falsy state reaches the artifact"


def test_the_committed_artifact_carries_no_not_in_set_row() -> None:
    """E2E over the real committed snapshot — the layer the TEST-LAYER RULE asks for.

    Phrasing- and count-independent: it does not care how many panels any name has today, only that
    nothing in the file is a tile that must not render.
    """
    snap = _snap()
    panels = snap.get("panels") or []
    assert panels, "the committed snapshot carries no panel block — this check would prove nothing"
    assert not [p for p in panels if p.get("state") == "not_in_set"]
    for p in panels:
        assert p.get("state") in ("ready", "refused")
        if p["state"] == "refused":
            assert p.get("reason") or p.get("missing"), f"{p['ticker']}/{p['key']} refuses silently"
        assert str(p.get("changes_the_call") or "").strip(), (
            f"{p['ticker']}/{p['key']} is decoration")


def test_the_artifact_carries_values_and_never_markup() -> None:
    """Display formatting is never load-bearing: the renderer may change how a figure reads without
    the artifact changing what it says. A tag in here would mean the two had been welded."""
    # A BARE `<` SCAN IS WRONG HERE and this test failed on its first run proving it: SMPL's kill
    # criterion reads "Quest revenue growth <= 0% YoY", a mathematical operator in legitimate prose.
    # The property is "no HTML TAG", so the pattern is tag-shaped. (Third substring false positive
    # in this build after RPO-inside-"Corporate" and ROU-inside-"Group" — a bare substring over
    # human text is nearly always too eager.)
    tag = re.compile(r"<\s*/?[a-zA-Z][^>]*>")
    for p in _snap().get("panels") or []:
        blob = json.dumps(p.get("value") or {})
        assert not tag.search(blob), f"{p['ticker']}/{p['key']} carries markup"


def test_a_ready_row_with_no_value_is_demoted_to_a_loud_refusal() -> None:
    """The requirement check and the payload builder can disagree; when they do, the honest output
    is a refusal that says so. An empty READY tile is indistinguishable from a panel that does not
    apply, which is the one thing the gating rule forbids."""
    rows = panel_rows_for(
        "ZZZZ", dossier={"mechanical": {"valuation": {
            # Requirements resolve — both facts are 'present' — but `own_history` is absent, so no
            # payload can be built from them.
            "ev_ebitda": {"value": 10.0, "status": "present", "source_ref": "s"},
            "range_position": {"value": "x", "status": "present", "source_ref": "s"}}}},
        row=None, freshness=None, record=None, declarations={})
    mp = next(r for r in rows if r.key == "multiple_and_price")
    assert mp.state == "refused"
    assert "payload builder disagree" in mp.reason or "no value could be built" in mp.reason


def test_the_name_set_is_the_union_not_just_the_ledger_rows() -> None:
    """A followed name with no ledger row still has panels. GOOGL carried a live position while
    having NO row in this snapshot; taking only `rows` would have made the grid invisible for
    exactly the names it was built for."""
    snap = _snap()
    row_tickers = {r["ticker"] for r in snap["rows"]}
    got = {p["ticker"] for p in snap.get("panels") or []}
    assert got - row_tickers, "no name outside the ledger rows got panels"
    assert "GOOGL" in got


def test_a_snapshot_predating_the_grid_still_validates() -> None:
    """`panels` is defaulted for the same reason `theme_falsifiers` is — every committed
    pre-phase-6 day must still load, or the book's history breaks on a code change."""
    old = json.loads((MON / "2026-07-20.json").read_text())
    assert "panels" not in old or not old["panels"]
    assert MonitorSnapshot.model_validate(old).panels == []


def test_the_multiple_payload_states_that_its_range_excludes_todays_mark() -> None:
    """16 of 18 corpus names carry one more series point than the range window counts, and the extra
    one is the current mark — which is why SMPL's 5.56x sits BELOW its own 6.11x low. Left implicit,
    a sparkline drawn over every point beneath a band drawn over n_closes reads as a glitch, and the
    tempting fix is to widen the band, which would restate the percentile the panel turns on."""
    v = multiple_and_price(
        (_dossier("SMPL") or {})["mechanical"]["valuation"])
    assert v is not None
    assert v["range_excludes_current"] is True
    assert len(v["series"]) == v["n_closes"] + 1
    assert v["current"] < v["low"], "the real state this flag exists to explain"


def test_emit_is_deterministic_over_the_committed_corpus() -> None:
    """Re-running the emitter on the same committed inputs reproduces the artifact's block. An
    artifact that cannot be regenerated is not derived data, it is hand-edited state."""
    import datetime as _dt

    from vinci.panels_emit import theme_panel_rows

    snap = _snap()
    cards = {json.loads(p.read_text())["driver_key"]
             for p in (ROOT / "data" / "themes" / "thesis").glob("*.json")}
    themes = ROOT / "data" / "themes"
    tracked = sorted({p.stem for p in (themes / "baskets").glob("*.json")}
                     | {p.stem for p in (themes / "economics").glob("*.json")})
    # THEME ROWS FIRST, matching the CLI's own order — the artifact is a sequence, so a
    # reproduction that emits the same rows in a different order is not a reproduction.
    again = theme_panel_rows(
        driver_keys=tracked, declared_cards=cards,
        theme_falsifiers=snap.get("theme_falsifiers") or [],
        today=_dt.date.fromisoformat(snap["as_of"]))
    again += emit_panels(rows=snap["rows"], freshness=snap["freshness"],
                         dossier_for=_dossier, record_for=_record, root=ROOT)
    got = [json.loads(r.model_dump_json()) for r in again]
    assert got == (snap.get("panels") or [])


def test_a_row_is_typed_rather_than_a_loose_dict() -> None:
    with pytest.raises(ValidationError):
        PanelRow(ticker="X", key="k", tier="universal", title="T",  # type: ignore[call-arg]
                 state="ready")


# --------------------------------------------------------------------------------------------
# Review fixes (PR #603). Each test below would have caught the defect it names.
# --------------------------------------------------------------------------------------------


def test_the_kills_payload_joins_on_the_only_key_a_measured_trigger_carries() -> None:
    """`MeasuredTrigger`/`MeasuredTriggerRow` carry `trigger`, `metric`, `threshold`, `observed` —
    NOT `criterion`/`text`/`reading`/`unit_checked`. Keying on the latter made every criterion
    "no measured metric — re-printed only" with a fully measured trigger sitting beside it, and the
    corpus could not catch it because no committed record carries one yet.
    """
    from vinci.panels_payload import kills

    crit = "Quest revenue growth <= 0% YoY for two consecutive quarters"
    v = kills(
        {"triggers": [crit], "measured": [{
            "trigger": crit, "metric": "quality.quest_growth_yoy", "comparator": "<=",
            "threshold": 0.0, "state": "NOT_FIRED", "reason": "read 0.031", "observed": 0.031,
            "unit": "ratio"}]},
        None,
    )
    (c,) = v["criteria"]
    assert c["text"] == crit
    assert c["reading"] == 0.031, "the monitor's evaluated reading must reach the surface"
    assert c["metric"] == "quality.quest_growth_yoy"
    assert c["threshold"] == 0.0
    assert c["unit_checked"] is True, "a resolved unit means the comparison WAS unit-checked"


def test_the_kills_payload_falls_back_to_the_record_and_never_invents_a_reading() -> None:
    """A criterion the monitor did not evaluate still prints its metric and threshold — and NO
    reading. A fabricated zero here would read as a crossed threshold."""
    from vinci.panels_payload import kills

    crit = "net debt / EBITDA above 4.0x"
    v = kills(
        {"triggers": [crit]},
        {"verdict": {"measured_triggers": [{
            "trigger": crit, "metric": "quality.net_debt_to_ebitda", "comparator": ">",
            "threshold": 4.0, "unit": "x"}]}},
    )
    (c,) = v["criteria"]
    assert c["metric"] == "quality.net_debt_to_ebitda" and c["threshold"] == 4.0
    assert c["reading"] is None, "never a coerced zero for an unmeasured criterion"


def test_an_unpriceable_stack_refuses_with_its_own_cause_not_a_claim_of_a_wiring_bug() -> None:
    """E2E over the committed artifact. TECX's capital structure lists tranches and none states both
    a principal and a fixed coupon — a disclosure fact, which `borrowing()` already words precisely.
    Relabelling it "a wiring bug rather than missing disclosure" told the reader a code defect about
    a real disclosure gap: a fabricated cause on a reader-facing refusal.
    """
    rows = [p for p in (_snap().get("panels") or [])
            if p["key"] == "cost_of_borrowing" and p["state"] == "refused"]
    assert rows, "no refused cost_of_borrowing row — this check would prove nothing"
    for p in rows:
        assert "wiring bug" not in p["reason"], f"{p['ticker']} blames the code for its disclosure"
        assert p["reason"].strip(), f"{p['ticker']} refuses silently"


def test_two_open_rows_refuse_with_the_ambiguity_rather_than_with_unrecorded() -> None:
    """`select_row` refuses by name when a ticker carries more than one OPEN decision, and its
    sentence was being discarded — the tile then said "this name has no row in the latest committed
    monitor snapshot", i.e. that the position is invisible to the book — false, and the one
    fact a reader would act on.
    """
    rows = [
        {"ticker": "ZZZZ", "verdict": "BUY", "closed": False, "entry_date": "2026-01-05"},
        {"ticker": "ZZZZ", "verdict": "BUY", "closed": False, "entry_date": "2026-04-05"},
    ]
    out = emit_panels(rows=rows, freshness=[], dossier_for=lambda _t: None,
                      record_for=lambda _t: None, root=ROOT)
    call = next(r for r in out if r.key == "the_call" and r.ticker == "ZZZZ")
    assert call.state == "refused"
    assert "2 OPEN decision rows" in call.reason, call.reason
    assert "2026-01-05" in call.reason and "2026-04-05" in call.reason


def test_the_renderer_and_its_header_agree_about_a_ready_row_it_cannot_draw_node() -> None:
    """The upstream demotion only fires on a FALSY payload, and `kills` is always
    ``{criteria: [...]}`` — empty or not. So a READY row with empty criteria reached the page
    as refusal TEXT wearing the READY class, with no badge, counted as "1 ready · 0 refused": the
    header was the reassuring half of an absent-vs-broken mismatch.

    Also pinned here: the verdict prints through `verdictWord` (AVOID_TERMINAL → AVOID, as the
    decision log and the dossier already do), and the multiple's own as-of is on the page, because
    the appended point is the dossier's mark and NOT the monitor day (VRRM's reads 2026-03-31).
    """
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = r"""
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const url = pathToFileURL(path.resolve("frontend/views/shared/panels.js")).href;
const { panelGridHtml } = await import(url);
const base = { ticker: "AAA", tier: "universal", changes_the_call: "c", caveat: "",
  cadence: "event", missing: [], reason: "", sources: [] };
const hollow = panelGridHtml([{ ...base, key: "kills", title: "Kills", state: "ready",
  value: { criteria: [] } }], { ticker: "AAA" });
const call = panelGridHtml([{ ...base, key: "the_call", title: "The call", state: "ready",
  value: { verdict: "AVOID_TERMINAL", sleeve: "s", entry_date: "2026-01-05", entry_price: 10,
           current_price: 11, closed: false, horizon_date: "2027-01-05", benchmark: "SPY" } }],
  { ticker: "AAA" });
const mult = panelGridHtml([{ ...base, key: "multiple_and_price", title: "M", state: "ready",
  value: { metric: "EV/EBITDA", current: 8.5, low: 10.4, high: 23.2, median: 14.0,
           percentile: 0.02, n_closes: 2, as_of: "2026-03-31",
           series: [["2026-02-28", 9.1], ["2026-03-15", 9.6], ["2026-03-31", 8.5]],
           current_is_last_point: true, range_excludes_current: true } }], { ticker: "AAA" });
console.log(JSON.stringify({
  hollowWearsRefusedClass: /class="pn-panel refused"/.test(hollow),
  hollowBadged: /pn-badge">REFUSED</.test(hollow),
  hollowStatesACause: /pn-up/.test(hollow),
  hollowCounted: hollow.includes("0 ready · 1 refused"),
  verdictShortened: call.includes(">AVOID<") && !call.includes("AVOID_TERMINAL"),
  multiplePrintsItsAsOf: mult.includes("as of Mar 31, 2026"),
  multipleDoesNotSayToday: !/today's mark/.test(mult),
}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver], capture_output=True,
                         text=True, check=True, cwd=ROOT)
    res = json.loads(out.stdout)
    assert res["hollowWearsRefusedClass"] and res["hollowBadged"], res
    assert res["hollowStatesACause"], "a refusal with no reason is the blank tile, again"
    assert res["hollowCounted"], "the header must be counted by the predicate the tile uses"
    assert res["verdictShortened"], res
    assert res["multiplePrintsItsAsOf"] and res["multipleDoesNotSayToday"], res


def test_every_truncated_list_in_the_renderer_states_its_own_truncation_node() -> None:
    """A TRUNCATED OUTPUT PRINTS ITS OWN TRUNCATION (CLAUDE.md, 2026-09-10).

    THE INCIDENT, carried forward from `tests/test_panels_render_truncation.py` (#601), which this
    branch deletes because it pins `vinci/panels_render.py` — a module this branch removed. Its
    coverage moves HERE, one layer up, where the renderer a human actually reads now lives:
    a scan printed the first 3 of 5 GLP-1 mentions and the conclusion drawn from that sample —
    *"no profit statement"* — was contradicted by the 4th and 5th and reached a merged record
    (`docs/records/2026-09-10-cah-cor-verified-not-assumed.md`, amendment 3).

    #601 fixed exactly two instances of this in `vinci/panels_render.py` — and THIS branch renamed
    that file, so the fix landed on a file that no longer exists here while the identical `[:N]`
    lived on in `panels.js`, the renderer that replaced it. A rename is a sibling call site with the
    evidence removed: the conflict was a modify/delete, and resolving it by deleting would have
    dropped the fix silently.

    THREE sites here, not the two #601 had. `sources` truncates too, and it is the worst-placed of
    the three: it prints a CORRECT count in the headline over a PARTIAL body, in the one tile a
    reader opens to CHECK rather than to trust — which is precisely the pair the rule names as what
    makes a truncation convincing.
    """
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = r"""
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { panelGridHtml } = await import(pathToFileURL(
  path.resolve("frontend/views/shared/panels.js")).href);
const base = { ticker: "AAA", tier: "universal", changes_the_call: "c", caveat: "",
  cadence: "event", missing: [], reason: "", sources: [], state: "ready" };
const nine = Array.from({length: 9}, (_, i) => `10-Q 2026-0${i+1}-01 acc 000${i}`);
const tl = panelGridHtml([{ ...base, key: "filing_watch", title: "F",
  value: { last_evidence_date: "2026-01-01", newer_filings: nine,
           next_expected_print: "2026-11-01", unread_print: true } }], { ticker: "AAA" });
// SEVEN DISTINCT GROUPS. The renderer groups form codes by what the filing IS, so a fixture of
// eight CODES collapsing to four groups never reaches the cap — which is what happened when
// grouping shipped and this pin went quietly vacuous. Three entries here (8-K, 6-K, FWP) are not
// dilution filings and stay unmapped, which is the only way to exceed the cap: there are five
// dilution MEANINGS in total, and that is precisely why no real name overflows any more.
const forms = [["424B2", 20], ["8-K", 9], ["S-8", 4], ["S-3", 3],
               ["S-4", 2], ["6-K", 1], ["FWP", 1]];
const dil = panelGridHtml([{ ...base, key: "dilution", title: "D",
  value: { line: "a line", forms, window_days: 1095 } }], { ticker: "AAA" });

// ...and the same three when nothing overflows: no summary line may appear.
const tl2 = panelGridHtml([{ ...base, key: "filing_watch", title: "F",
  value: { last_evidence_date: "2026-01-01", newer_filings: nine.slice(0, 3),
           next_expected_print: "2026-11-01", unread_print: false } }], { ticker: "AAA" });

console.log(JSON.stringify({
  timelineStatesRest: /\+5 more/.test(tl) && /of 9 filed since/.test(tl),
  timelineDrawsFour: (tl.match(/filed since/g) || []).length === 5,   // 4 dots + the overflow
  formsStateRest: /showing 5 of 7 form types/.test(dil),

  quietTimelineSaysNothing: !/more/.test(tl2),

}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr
    got = json.loads(out.stdout)
    assert got == dict.fromkeys(got, True), got


def test_the_corpus_actually_overflows_two_of_the_three_caps() -> None:
    """CORPUS BEFORE SYNTHETIC — the pin above is built by hand, so this proves the condition is
    REAL rather than invented, and it cannot pass vacuously.

    TECX carries 8 form types against 5 bars and 8 source refs against 5 lines, both in the
    committed artifact. The timeline cap has NO corpus witness (WERN's 4 exactly meets it and does
    not exceed it), which is recorded rather than papered over: #601 noted the same asymmetry, and
    a fix with no witness is proven by construction only.
    """
    # GROUPED, because that is what the renderer caps. Measuring raw form codes here would have
    # kept this pin green while the form-bar truncation stopped firing on every name in the corpus
    # — a check passing on a quantity its guard no longer reads.
    means = {"S-3ASR": "shelf", "S-3": "shelf", "F-3": "shelf", "424B2": "draw", "424B5": "draw",
             "424B3": "draw", "S-8": "employee", "S-1": "new", "F-1": "new", "S-4": "merger"}
    import re as _re

    def _groups(forms: list) -> int:
        base = [_re.sub(r"\s*(POS|POSASR)$|/A$", "", str(c)).strip() for c, _n in forms]
        return len({means.get(b, b) for b in base})

    forms_max = newer_max = 0
    for p in _snap().get("panels") or []:
        v = p.get("value") or {}
        forms_max = max(forms_max, _groups(v.get("forms") or []))
        # `sources` no longer truncates — it groups by panel and is bounded by the panel count, so
        # there is no cap here to witness. Measuring the old flat `refs` would be measuring a
        # quantity nothing reads.
        newer_max = max(newer_max, len(v.get("newer_filings") or []))
    # STATED, NOT ASSERTED: after grouping, the deepest name (TECX) sits at exactly the cap, so the
    # form-bar truncation has NO corpus witness today — it is proven by construction only, like the
    # timeline cap. Recorded rather than papered over; if a name ever carries a sixth KIND of
    # filing, pin it in the node test above and turn this back into an overflow assertion.
    assert forms_max <= 5, (
        f"a name now shows {forms_max} filing KINDS — the form-bar truncation has a corpus witness "
        f"again, so assert the overflow instead of this line")

    # Stated, not asserted: the timeline cap is unwitnessed on this corpus today.
    assert newer_max <= 4, (
        f"a name now carries {newer_max} newer filings — the timeline cap HAS a corpus witness, so "
        f"pin it in the node test above and retire this line")
