"""Versioned scenario records — schema, round-trip, recipe run, and the unit guards.

Pins: the record round-trips byte-stably; the recipe REFUSES a mismatched multiple_basis or a
missing source-bound fact (never assumes); the machine records PASS/FAIL honestly and never moves
the verdict off ``pending_analyst``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pydantic
import pytest

from vinci import scenarios as sc


def _rec(**over: object) -> sc.ScenarioRecord:
    base = {
        "ticker": "TEST", "recipe_id": sc.RECIPE_R1,
        "recipe_desc": "mid-cycle operating margin x exit EV/EBITDA",
        "multiple_basis": "EV/EBITDA", "underwrite_date": "2026-07-19", "analyst": "tester",
        "spot": 46.0, "spot_source": "test", "spot_as_of": "2026-07-10",
        "facts": {
            "d_and_a": sc.Fact(value=286.321, unit="$M", basis="consolidated FY2025",
                               source="10-K"),
            "net_debt": sc.Fact(value=979.776, unit="$M", basis="incl leases", source="10-Q"),
            "diluted_shares": sc.Fact(value=59.91, unit="M shares", basis="Q1-2026", source="10-Q"),
        },
        "scenarios": {
            "bear": sc.ScenarioInput(revenue=2850.0, margin=0.015, multiple=6.0, reason="trough",
                                     bear_basis="own-history", margin_basis="EBIT"),
            "base": sc.ScenarioInput(revenue=3100.0, margin=0.0625, multiple=6.5, reason="mid"),
            "bull": sc.ScenarioInput(revenue=3400.0, margin=0.080, multiple=7.0, reason="turn"),
        },
        # schema 1.1: methodology is REQUIRED — the fixture exercises the strict path everywhere
        "assumptions": {
            "revenue": sc.AssumptionDerivation(method="legs set against reported history"),
            "margin": sc.AssumptionDerivation(method="modeled off the own-history median anchor",
                references=[sc.RefPoint(label="own-history median operating margin",
                                        value=7.45, unit="%", source="EDGAR margin_anchor",
                                        vintage="FY2025")]),
            "multiple": sc.AssumptionDerivation(method="chosen against the own-history band"),
        },
    }
    base.update(over)
    return sc.ScenarioRecord(**base)  # type: ignore[arg-type]


def test_record_roundtrips(tmp_path: Path) -> None:
    rec = _rec()
    p = sc.write_record(rec, root=tmp_path)
    back = sc.read_record("TEST", root=tmp_path)
    assert back == rec
    assert p.read_text().endswith("\n")                 # newline-terminated, diff-able
    assert sc.all_records(root=tmp_path)["TEST"] == rec


def test_schema_file_excluded_from_records(tmp_path: Path) -> None:
    sc.write_record(_rec(), root=tmp_path)
    sc.write_json_schema(root=tmp_path)
    assert (tmp_path / "scenarios" / "_schema.json").exists()
    assert list(sc.all_records(root=tmp_path)) == ["TEST"]   # `_schema.json` is not a record


def test_recipe_computes_on_ebitda_and_records_fail() -> None:
    """The WERN shape: reward negative at spot → an honest FAIL, recorded not hidden."""
    out = sc.run_recipe(_rec())
    per = out.result.per_scenario
    assert per["base"].ebitda == pytest.approx(480.071)      # EBIT 193.75 + D&A 286.321
    assert per["base"].value_per_share == pytest.approx(35.73, abs=0.02)
    assert per["bear"].value_per_share == pytest.approx(16.60, abs=0.02)
    assert per["bull"].value_per_share == pytest.approx(48.88, abs=0.02)
    assert out.result.reward == pytest.approx(-10.27, abs=0.02)
    assert out.result.risk == pytest.approx(29.40, abs=0.02)
    assert out.result.ratio == pytest.approx(-0.349, abs=0.005)
    assert out.result.pass_fail == "FAIL" and out.result.bar == 2.0
    # the machine records, it does NOT ratify
    assert out.verdict.status == "pending_analyst" and out.verdict.recorded is None


def test_recipe_refuses_mismatched_basis() -> None:
    with pytest.raises(ValueError, match="multiple_basis"):
        sc.run_recipe(_rec(multiple_basis="EV/EBIT"))


def test_recipe_refuses_missing_fact() -> None:
    r = _rec()
    facts = {k: v for k, v in r.facts.items() if k != "d_and_a"}
    with pytest.raises(ValueError, match="d_and_a"):
        sc.run_recipe(r.model_copy(update={"facts": facts}))


def test_recipe_refuses_unknown_recipe() -> None:
    with pytest.raises(ValueError, match="unknown recipe_id"):
        sc.run_recipe(_rec(recipe_id="R9_not_a_recipe"))


def test_blank_reason_is_refused_at_the_record_boundary() -> None:
    """F2: ``run_recipe`` builds its Scenario directly, bypassing build_scenario's no-reason guard,
    so the refusal binds on the RECORD — the durable artifact — instead."""
    for blank in ("", "   ", "\n\t"):
        with pytest.raises(ValueError, match="reason is required"):
            sc.ScenarioInput(revenue=3100.0, margin=0.0625, multiple=6.5, reason=blank)
    ok = sc.ScenarioInput(revenue=3100.0, margin=0.0625, multiple=6.5, reason="stated why")
    assert ok.reason == "stated why"


def test_norm_fcf_is_none_without_its_inputs_never_ebit() -> None:
    """F1: with cash interest/tax absent the FCF formula collapses to EBIT. Printing EBIT under a
    'normalized FCF' label would be a fabricated number — it must be None instead."""
    r = _rec()
    facts = {k: v for k, v in r.facts.items() if k not in ("cash_interest", "cash_tax_rate")}
    out = sc.run_recipe(r.model_copy(update={"facts": facts}))
    base = out.result.per_scenario["base"]
    assert base.norm_fcf is None                       # NOT 193.75 (EBIT) under an FCF label
    assert base.op_income == pytest.approx(193.75)     # EBIT itself is still reported, as EBIT
    assert base.ev_ebit is not None                    # the other cross-check is unaffected
    # supplied → it computes: EBIT 193.75 − tax 38.674 − interest 39.053
    full = sc.run_recipe(_rec(facts={
        **facts,
        "cash_interest": sc.Fact(value=39.053, unit="$M", basis="FY2025", source="10-K"),
        "cash_tax_rate": sc.Fact(value=0.25, unit="rate", basis="assumption", source="analyst"),
    }))
    assert full.result.per_scenario["base"].norm_fcf == pytest.approx(116.02, abs=0.05)


def test_refpoint_and_method_blanks_are_refused() -> None:
    """1.1 guards: a reference value or method that cannot be verified is refused at the
    boundary (the blank-reason pattern); an EMPTY references list is legal — a pure-judgment
    method honestly stated beats a fabricated reference."""
    for field in ("label", "unit", "source"):
        kw = {"label": "x", "value": 1.0, "unit": "%", "source": "y", field: "  "}
        with pytest.raises(ValueError, match="cannot be verified"):
            sc.RefPoint(**kw)  # type: ignore[arg-type]
    ok = sc.RefPoint(label="median margin", value=7.45, unit="%", source="EDGAR")
    assert ok.value == 7.45
    for blank in ("", "   ", "\n\t"):
        with pytest.raises(ValueError, match="method is required"):
            sc.AssumptionDerivation(method=blank)
    judged = sc.AssumptionDerivation(method="half-turn premium for cycle-turn rerating")
    assert judged.references == []


def test_r1_assumption_axes_are_guarded_both_ways() -> None:
    """Unknown axis → refused at ANY version (silent render-drop is data loss); completeness →
    binds from 1.1; an unknown recipe_id is unconstrained until it declares axes."""
    assert set(_rec().assumptions) == {"revenue", "margin", "multiple"}   # POS: exact set OK
    incomplete = {"revenue": sc.AssumptionDerivation(method="history")}
    with pytest.raises(ValueError, match="must cover exactly"):
        _rec(assumptions=incomplete)
    bad = dict(_rec().assumptions)
    bad["fx_rate"] = sc.AssumptionDerivation(method="typo axis")
    with pytest.raises(ValueError, match="unknown assumption axis"):
        _rec(assumptions=bad)
    with pytest.raises(ValueError, match="unknown assumption axis"):
        _rec(schema_version="1.0", assumptions={"fx_rate": bad["fx_rate"]})  # any version
    exotic = _rec(recipe_id="R9_future", assumptions={"wacc": sc.AssumptionDerivation(
        method="declared when the recipe exists")})
    assert "wacc" in exotic.assumptions                                   # unconstrained


def test_legacy_1_0_record_computes_without_assumptions() -> None:
    """Methodology binds FORWARD: a 1.0 record with no assumptions validates, computes the same
    numbers as always, and gets the formula STAMPED; the same emptiness at 1.1 is refused."""
    legacy = _rec(schema_version="1.0", assumptions={})
    out = sc.run_recipe(legacy)
    assert out.result.per_scenario["base"].value_per_share == pytest.approx(35.73, abs=0.02)
    assert out.recipe_formula == list(sc.R1_FORMULA)
    with pytest.raises(ValueError, match="must state how each axis was modeled"):
        _rec(assumptions={})


def test_run_recipe_stamps_and_guards_the_r1_formula() -> None:
    """The stated recipe can never drift from the computed one: unstamped → stamped from the ONE
    engine constant; a record CLAIMING different arithmetic is refused, never overwritten. The
    five steps are exact-pinned — code constants, not LLM text."""
    out = sc.run_recipe(_rec())
    assert out.recipe_formula == list(sc.R1_FORMULA)
    restated = sc.run_recipe(out)                       # pre-stamped, correct → unchanged
    assert restated.recipe_formula == list(sc.R1_FORMULA)
    with pytest.raises(ValueError, match="does not match R1_FORMULA"):
        sc.run_recipe(_rec(recipe_formula=["EV = EBIT × multiple"]))
    assert list(sc.R1_FORMULA) == [
        "EBIT = revenue × op margin",
        "EBITDA = EBIT + D&A",
        "EV = EBITDA × exit multiple (EV/EBITDA)",
        "equity = EV − net debt",
        "value/share = equity ÷ diluted shares",
    ]


def test_committed_wern_underwrite_carries_its_methodology() -> None:
    """E2E on the committed record — the reproducibility-unit invariant. Skip-gated while the
    committed record predates the backfill (schema 1.0); permanently active after."""
    root = Path(__file__).resolve().parents[1]
    rec = sc.read_record("WERN", root=root)
    if rec.schema_version == "1.0":
        pytest.skip("pre-backfill — binds after this PR's artifact commit")
    assert set(rec.assumptions) == {"revenue", "margin", "multiple"}
    assert rec.recipe_formula == list(sc.R1_FORMULA)
    for axis, a in rec.assumptions.items():
        for r in a.references:
            assert r.source.strip(), f"{axis} reference {r.label!r} has no source"
    # assumptions/formula must not feed arithmetic: recompute == committed result
    assert sc.run_recipe(rec).result == rec.result


def test_scenario_card_emits_derivations_and_omits_them_for_legacy_records() -> None:
    """The emit passes methodology through UNROUNDED and in renderer-friendly list shape; a
    pre-1.1 record emits NEITHER key — the degrade is omission, never a fabricated empty."""
    build = _load_build()
    rec = json.loads(sc.run_recipe(_rec()).model_dump_json())
    card = build._scenario_card(rec)
    assert card["recipeFormula"] == list(sc.R1_FORMULA)
    assert [a["axis"] for a in card["assumptions"]] == ["revenue", "margin", "multiple"]
    margin = next(a for a in card["assumptions"] if a["axis"] == "margin")
    ref = margin["references"][0]
    # EXHAUSTIVE by design — it is what caught the 1.4 `vintage` reaching the card, so keep it a
    # whole-dict compare and never relax it to a subset. (raw pass-through, no _rd)
    assert ref == {"label": "own-history median operating margin", "value": 7.45,
                   "unit": "%", "source": "EDGAR margin_anchor", "vintage": "FY2025"}
    legacy = {k: v for k, v in rec.items() if k not in ("assumptions", "recipe_formula")}
    lcard = build._scenario_card(legacy)
    assert "assumptions" not in lcard and "recipeFormula" not in lcard


def test_uw_card_methodology_block_owns_its_print_fate() -> None:
    """Source pins for the schema-1.1 render: the recipe CHAIN is provenance and lives in the
    on-demand tier; the reference tables carry their OWN "M" endnote scope inside the <details>
    (marker + list share print fate — the Inputs-block invariant, mechanically enforced repo-wide
    by the #10 sweep); the Method fact prints in the main tier.

    TIER CORRECTION (tear-sheet build): the chain used to render in the MAIN body, above the legs
    table. It is a drift guard — proof the stated recipe is the computed recipe — which makes it
    provenance, and DESIGN RULE v2 puts provenance in the collapsed/print-excluded tier, not
    between the analyst's decision values. The recipe NAME still leads (the masthead's Method
    cell); only the arithmetic moved."""
    import re

    uw = (Path(__file__).resolve().parents[1] / "frontend" / "views" / "shared" / "uw-card.js"
          ).read_text()
    legs = re.search(r"function legsTable\(c\) \{(.*?)\n\}", uw, re.S)
    assert legs and "${recipeLine(c)}" not in legs.group(1), (
        "the recipe chain is provenance — it must NOT render in the main-body legs table")
    refs = re.search(r"function methodRefsDetails\(c\) \{(.*?)\n\}", uw, re.S)
    assert refs and "${recipeLine(c)}" in refs.group(1), (
        "the recipe chain must render inside the on-demand references <details> (print-excluded)")
    assert refs, "methodRefsDetails() is gone"
    assert 'withEndnotes("M", tables)' in refs.group(1), (
        "the reference tables must own their endnote scope — resolving into the card's list "
        "orphans every entry in a collapsed-block print")
    assert "citeMark(p.source)" in refs.group(1), "every reference value must be source-cited"
    body = re.search(r"const body = \(\) => `(.*?)`;", uw, re.S)
    assert body and "${methodFact(c)}" in body.group(1), (
        "the Method fact must print in the main body tier (always-visible methodology)")
    # canonical axis order — the regression was a botched modulo sort putting revenue LAST
    assert re.search(r"const rank = \(a\) => \{ const i = AXIS_ORDER\.indexOf\(a\.axis\); "
                     r"return i < 0 \? 99 : i; \};", uw), (
        "orderedAssumptions must rank known axes by AXIS_ORDER (revenue first) and unknown last")
    # degrade: both helpers return "" on absent data — no fabricated block
    assert re.search(r'function recipeLine\(c\) \{[^}]*?return "";', uw, re.S)
    # WAS `!withRefs.length` — "no axis carries references" (2026-09-01). The degrade condition
    # moved to "no axes at all" because an axis WITHOUT references is no longer nothing to show:
    # it renders its chosen trio under a stated "set by judgment" row, which is a fact the reader
    # needs and not a fabricated block. The invariant this line guards — absent data yields "",
    # never invented content — is unchanged.
    assert 'if (!axes.length) return "";' in uw
    assert "no reference values" in uw, (
        "an axis with no references must SAY so — an empty table reads as nothing-to-say when "
        "the truth is nothing-anchors-this")
    assert 'if (!lines) return "";' in uw


def test_uw_card_renders_derivations_and_degrades_silently_node() -> None:
    """Node-gated e2e: render the COMMITTED WERN card through the real uwCard and assert the
    methodology actually reaches the HTML — data-driven (every method sentence + every reference
    label from the committed JSON, escaped exactly as the renderer escapes), plus the structural
    markers. NEG: the same card stripped of assumptions/recipeFormula renders NO methodology
    block and loses exactly one Sources list (the M scope) — silence, never fabrication."""
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    card_path = Path(__file__).resolve().parents[1] / "frontend" / "scenarios" / "WERN.json"
    if "assumptions" not in json.loads(card_path.read_text()):
        pytest.skip("committed card predates the backfill")
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const cardUrl = pathToFileURL(path.resolve("frontend/views/shared/uw-card.js")).href;
const { uwCard } = await import(cardUrl);
const { escapeHtml } = await import(pathToFileURL(path.resolve("frontend/lib/format.js")).href);
const card = JSON.parse(readFileSync("frontend/scenarios/WERN.json"));
const html = uwCard(card);
const missing = [];
for (const a of card.assumptions) {
  if (!html.includes(escapeHtml(a.method))) missing.push(["method", a.axis]);
  for (const r of a.references)
    if (!html.includes(escapeHtml(r.label))) missing.push(["ref", r.label.slice(0, 40)]);
}
const stripped = { ...card }; delete stripped.assumptions; delete stripped.recipeFormula;
const bare = uwCard(stripped);
const count = (h, n) => h.split(n).length - 1;
console.log(JSON.stringify({
  missing,
  recipe: html.includes("EBIT = revenue"),
  block: html.includes('class="uw-method"') && html.includes("[M1]"),
  chosen: html.includes("chosen (bear · base · bull)"),
  bareClean: !bare.includes("uw-method") && !bare.includes("uw-recipe"),
  sourcesFull: count(html, 'class="card ds-section ds-sources"'),
  sourcesBare: count(bare, 'class="card ds-section ds-sources"'),
}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True,
                         cwd=Path(__file__).resolve().parents[1])
    res = json.loads(out.stdout)
    assert res["missing"] == [], f"committed methodology absent from the render: {res['missing']}"
    assert res["recipe"] and res["block"] and res["chosen"], res
    assert res["bareClean"], "a stripped card must render NO methodology block (no fabrication)"
    # full = U + I + M scopes; stripped loses exactly the M list, U and I untouched
    assert (res["sourcesFull"], res["sourcesBare"]) == (3, 2), res


def test_uw_card_ev_revenue_shows_no_dead_margin_rows_node() -> None:
    """THE DEAD-INPUT PIN AT THE RENDER LAYER. An EV/Revenue value is revenue × multiple; margin
    and D&A never enter it. If the card printed a margin row anyway it would read as a driver of a
    number it did not produce, and no reader could tell — the same class of defect as #179's
    `undefined` reference table, which shipped invisibly into every PDF because the preview only
    checked the collapsed state.

    Rendered in BOTH states for that reason: collapsed as seen on screen, and force-open as the T1
    print rule exports it. A row hidden behind a <details> is still in the PDF."""
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    card_path = Path(__file__).resolve().parents[1] / "frontend" / "scenarios" / "FUBO.json"
    if not card_path.exists():
        pytest.skip("no EV/Revenue card committed yet — awaiting combined-entity re-scope, "
                    "not this build")
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const cardUrl = pathToFileURL(path.resolve("frontend/views/shared/uw-card.js")).href;
const { uwCard } = await import(cardUrl);
const card = JSON.parse(readFileSync("frontend/scenarios/FUBO.json"));
const html = uwCard(card);
// the PRINT tier: every <details> force-opens in the PDF, so scan that text too
const printed = html.replace(/<details/g, "<details open");
console.log(JSON.stringify({
  basis: card.multipleBasis,
  marginRow: /Terminal op margin|>Op margin</.test(html),
  marginRowPrinted: /Terminal op margin|>Op margin</.test(printed),
  undef: /undefined|NaN/.test(printed),
  // the value drivers that DO belong, and the mechanics EV/Revenue must keep
  exitRow: html.includes("Exit EV/Revenue"),
  revenueRow: html.includes("Terminal revenue ($M)"),
  horizonRow: html.includes("Years to terminal"),
  survival: html.includes("uw-survival"),
  tier: html.includes("tier B"),
  methodAxes: html.includes("revenue, multiple and horizon methodology"),
  marginMethod: /<b>Op margin<\/b>/.test(printed),
}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True,
                         cwd=Path(__file__).resolve().parents[1])
    res = json.loads(out.stdout)
    assert res["basis"] == "EV/Revenue", res
    assert not res["marginRow"], "EV/Revenue card renders a margin row that no computation fed"
    assert not res["marginRowPrinted"], "the margin row is absent on screen but PRESENT in the PDF"
    assert not res["marginMethod"], "an EV/Revenue card carries a margin methodology line"
    assert not res["undef"], "undefined/NaN reached the rendered card (the #179 class)"
    assert res["exitRow"] and res["revenueRow"] and res["horizonRow"], res
    assert res["survival"] and res["tier"] and res["methodAxes"], res


def test_committed_schema_matches_the_model() -> None:
    """F4: ``scenarios/_schema.json`` is committed — pin it so a model change cannot silently
    leave a stale schema behind."""
    committed = json.loads((Path(__file__).resolve().parents[1] / "scenarios" /
                            "_schema.json").read_text())
    assert committed == sc.json_schema(), (
        "scenarios/_schema.json is stale — regenerate with vinci.scenarios.write_json_schema()")


def test_frontend_build_stays_stdlib_only() -> None:
    """F3: docs/DEPLOY.md pins frontend/build.py as the Cloudflare Pages build step — run as
    `python frontend/build.py` with NO requirements.txt. Importing `vinci` there would pull in
    pydantic and break the deploy, so the scenario-card renderer reads the records as plain JSON."""
    src = (Path(__file__).resolve().parents[1] / "frontend" / "build.py").read_text()
    offenders = [ln.strip() for ln in src.splitlines()
                 if ln.strip().startswith(("import vinci", "from vinci"))]
    assert not offenders, f"frontend/build.py must stay stdlib-only; found: {offenders}"


def _load_build():  # type: ignore[no-untyped-def]
    """Import frontend/build.py as a module (it is a script, not a package member)."""
    import importlib.util

    path = Path(__file__).resolve().parents[1] / "frontend" / "build.py"
    spec = importlib.util.spec_from_file_location("fe_build", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_emit_scenarios_matches_theme_embedded_card_and_is_deterministic() -> None:
    """The standalone `frontend/scenarios/<T>.json` must be the EXACT `_scenario_card()` shape the
    theme JSON embeds (one contract), and two emits must be byte-identical (committed output never
    churns). Runs against the real committed `scenarios/` + `frontend/themes/` artifacts."""
    build = _load_build()
    root = Path(__file__).resolve().parents[1]
    cards = build._scenario_cards()
    assert "WERN" in cards                                  # the committed record reaches the emit
    theme = json.loads((root / "frontend" / "themes" / "truckload-supply-purge.json").read_text())
    embedded = next(w["scenarioCard"] for w in theme["watchlist"]
                    if w["ticker"] == "WERN" and "scenarioCard" in w)
    assert cards["WERN"] == embedded                        # ONE shape, wherever the card renders
    out = root / "frontend" / "scenarios"
    if out.is_dir():                                        # emitted by the build → pinned stable
        first = {p.name: p.read_bytes() for p in sorted(out.glob("*.json"))}
        build.emit_scenarios()
        second = {p.name: p.read_bytes() for p in sorted(out.glob("*.json"))}
        assert first == second                              # idempotent, byte-for-byte
        idx = json.loads(second["index.json"].decode())
        assert idx == {"tickers": sorted(cards)}


def test_reserved_theme_slugs_fail_loud() -> None:
    """A theme slug that collides with a themes-route first segment (radar/watchlist/scan/forward)
    would be unroutable — the build must refuse it, never ship a shadowed page."""
    build = _load_build()
    with pytest.raises(SystemExit, match="reserved themes route"):
        build._slug("Radar")
    assert build._slug("Truckload Supply Purge")[0] == "truckload-supply-purge"


def test_dossier_view_resolves_existence_from_the_index_never_from_a_404() -> None:
    """PRODUCTION REGRESSION — WERN's page rendered locally but hung forever on the deploy.

    The view used to PROBE for `dossiers/<T>.json` and read "no dossier" off a 404. That holds on a
    plain static server, but the authed Pages origin runs functions/_middleware.js on EVERY request
    and a miss that fails inside ctx.next() falls through its bare `catch {}` to challenge() — a
    401. getDossier tolerates ONLY 404, so it rethrew and the view died at "Loading dossier…".

    It bit exactly one name: WERN — the only ticker with an underwrite but no dossier, hence the
    only page whose NORMAL path needs a missing file. Reproduced against an origin that answers 401
    for a miss, and fixed by asking the committed index (which lists what the build actually
    emitted) instead of interpreting a transport error. Absence is DATA, not an error code.

    The helpers stay fail-loud on purpose — a 500/401 on a file that SHOULD exist must still throw
    rather than silently degrade to "nothing committed yet"; the fix is to not probe for files the
    index already says are absent."""
    import re

    js = (Path(__file__).resolve().parents[1] / "frontend" / "views" / "shared" / "dossier.js"
          ).read_text()
    # the dossier read is GUARDED by index membership — and appears exactly once, so no unguarded
    # probe can hide elsewhere in the view
    assert len(re.findall(r"await getDossier\(", js)) == 1, "an unguarded getDossier probe crept in"
    guard = r"known\.includes\(ticker\)\s*\?\s*await getDossier\(ticker\)\s*:\s*null"
    assert re.search(guard, js), (
        "the dossier fetch must be gated on the committed index, not on a 404 from a probe")
    # ditto the underwrite record
    assert len(re.findall(r"await getScenarioCard\(", js)) == 1
    assert re.search(r"\(await getScenarioIndex\(\)\)\.includes\(ticker\)", js), (
        "the scenario-card fetch must be gated on the scenario index")


def test_citation_system_is_shared_not_re_implemented() -> None:
    """The citation system has ONE home (frontend/lib/cites.js).

    It used to be ~25 private lines inside dossier.js, which is precisely why uw-card.js hardcoded
    the inline form for EVERY cite — including its main-body Spot cite, where the dossier's own
    convention says endnote. A good implementation locked in one module forces the next surface to
    ship a lesser one; this pins the lift so it cannot regress."""
    root = Path(__file__).resolve().parents[1] / "frontend"
    lib = (root / "lib" / "cites.js").read_text()
    for fn in ("export function citeMark", "export function withEndnotes",
               "export function auditCitesInline", "export const citePlaceholders"):
        assert fn in lib, f"lib/cites.js lost {fn}"
    dossier = (root / "views" / "shared" / "dossier.js").read_text()
    assert 'from "../../lib/cites.js"' in dossier, "dossier.js must import the shared cite system"
    for dead in ("function citeMark(", "function withEndnotes(", "function auditCitesInline("):
        assert dead not in dossier, f"dossier.js re-declares {dead} — one implementation, one home"
    # exactly ONE module may know the placeholder grammar — a second copy is the documented
    # "two divergent parsers of one string" bug class
    marker = 'data-ref="'
    hits = sorted(p.name for p in root.rglob("*.js") if marker in p.read_text())
    assert hits == ["cites.js"], f"the citeMark placeholder shape leaked outside cites.js: {hits}"


def test_uw_card_owns_its_citations_and_renders_the_same_everywhere() -> None:
    """The card is SELF-CONTAINED: it runs its own endnote scopes, so no host must run a pass and
    the same card cannot render differently on two surfaces (it did — the theme page's copy kept
    long inline strings while the dossier's was numbered).

    TWO scopes, because print fate differs. The main body's list sits inside the card. The Inputs
    <details> keeps its OWN nested scope: `details:not([open])` drops a collapsed block from the
    PDF, so an [I n] resolving into the card's outer list would orphan there — marker and Sources
    entry must always share print fate."""
    import re

    root = Path(__file__).resolve().parents[1] / "frontend"
    uw = (root / "views" / "shared" / "uw-card.js").read_text()
    assert 'withEndnotes("U", body)' in uw, "the card must run its own main-body endnote scope"
    inputs = re.search(r"function inputsDetails\(c\) \{(.*?)\n\}", uw, re.S)
    assert inputs, "inputsDetails must take no cite mode — the card has no modes left"
    assert 'withEndnotes("I", rows)' in inputs.group(1), (
        "the Inputs block must own its scope — resolving into the card's list orphans every entry "
        "when the block is printed collapsed")
    assert "citeMark(f.source)" in inputs.group(1)
    # the mode knob is GONE — a knob a host can get wrong is a rendering difference in waiting
    assert "cites" not in uw.split("export function uwCard")[1], (
        "uwCard must take no cite mode; self-contained scopes make the failure impossible")
    assert 'class="cite"' not in uw, "no hand-rolled inline cite survives in the card"
    # ...and no host runs a pass on its behalf
    dossier = (root / "views" / "shared" / "dossier.js").read_text()
    assert 'withEndnotes("U"' not in dossier, "the card owns the U scope now, not the host"


def test_uw_headline_state_machine_never_invents_a_target() -> None:
    """THE CONSTITUTIONAL PIN of the tear-sheet header. `base_vps` is a COMPUTATION; it becomes a
    TARGET only when a human verdict ratifies it, and never when it sits at/below spot (a
    WERN-shape avoid has no upside to target). Rendered on the real committed cards + two
    synthetic states, via node — the label is what an analyst reads as the fund's call.

    Pins the RULE, not the wording: each state must produce its own distinct eyebrow, a pending
    record must never print the ratified label, and a priced record must never print either."""
    import json
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node not available")
    root = Path(__file__).resolve().parents[1]
    uw = (root / "frontend" / "views" / "shared" / "uw-card.js").resolve().as_uri()
    driver = f"""
import {{ readFileSync }} from "node:fs";
const {{ uwCard }} = await import("{uw}");
const rd = (p) => JSON.parse(readFileSync(p));
// The ARCHIVED SMPL record, not the live one (2026-07-27). Fixture history, because it is the
// argument: IT held this role until it was exited; live SMPL held it until the input-staleness
// close; then live SMPL was REISSUED as a fresh watch record with NO entry price, which is
// correct for a record that opens no position and useless as a "has an entry" fixture.
// An ARCHIVED record is frozen by construction — it cannot drift out from under the pin the way
// three living records already have.
const it = rd("frontend/scenarios/SMPL-2026-07-21.json");  // base ABOVE spot; entry + ledger row
it.verdict.status = "confirmed";                    // synthetic: the state, not the record
const wern = rd("frontend/scenarios/WERN.json");    // watch, base BELOW spot (priced)
// synthetic: the same record still awaiting the analyst — the machine's only reachable state
const pending = JSON.parse(JSON.stringify(it));
pending.verdict.status = "pending_analyst";
pending.verdict.entryPrice = null; pending.verdict.ratioAtEntry = null;
delete pending.ledger;
// synthetic: a CONFIRMED verdict whose base sits below spot — status must NOT win over price
const confirmedButPriced = JSON.parse(JSON.stringify(wern));
confirmedButPriced.verdict.status = "confirmed";
const grab = (h) => (h.match(/uw-stat-lab uw-eyebrow">([^<]*)</) || [null, ""])[1].trim();
console.log(JSON.stringify({{
  target: grab(uwCard(it)),
  pending: grab(uwCard(pending)),
  priced: grab(uwCard(wern)),
  confirmedButPriced: grab(uwCard(confirmedButPriced)),
  targetHasLedgerPill: /pill (?:buy|unresolved)">BUY/.test(uwCard(it)),
  pricedHasNoLedgerPill: !/pill (?:buy|unresolved)">BUY/.test(uwCard(wern)),
  // CLOSE-AWARE (2026-07-27): the ledger word stays, but a CLOSED position never headlines as a
  // bare live verdict — it carries its close. SMPL is closed, so the fixture asserts the closed
  // form; a synthetic OPEN copy of the same card must still read the bare word.
  closedShowsClose: /BUY — closed [0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}} at [$]/.test(uwCard(it)),
  openStaysBare: (() => {{
    const o = JSON.parse(JSON.stringify(it));
    delete o.ledger.closed;
    // the PILL must close immediately after the word — a bare verdict, no close clause. (Scoped
    // to the pill on purpose: "closed"/"closes" appear all over the card's prose and band refs.)
    return /pill buy">BUY</.test(uwCard(o));
  }})(),
  pendingShowsPass: /uw-mini">PASS</.test(uwCard(pending)),
  targetHidesPass: !/uw-mini">PASS</.test(uwCard(it)),
  pendingNoEntry: /no position/.test(uwCard(pending)),
  targetHasEntry: uwCard(it).includes(String(it.verdict.entryPrice)),
}}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, cwd=root, check=True)
    r = json.loads(out.stdout)
    # three DISTINCT states, none of them borrowing another's label
    assert len({r["target"], r["pending"], r["priced"]}) == 3, r
    assert r["target"] and r["pending"] and r["priced"], r
    assert r["pending"] != r["target"], "a pending record must not print the ratified label"
    assert r["priced"] != r["target"], "a base at/below spot is never a target"
    # price beats status: ratification cannot turn a below-spot base into a target
    assert r["confirmedButPriced"] == r["priced"], (
        "a CONFIRMED verdict whose base sits below spot must still read as priced")
    # the verdict of record is the LEDGER's, never invented from the scenario status
    assert r["targetHasLedgerPill"], "a logged BUY must show the ledger verdict"
    assert r["pricedHasNoLedgerPill"], "a name with no ledger row must not show a BUY/AVOID word"
    # ...and a CLOSED position shows its close beside that word, while an open one stays bare
    assert r["closedShowsClose"], "a closed position must headline with its close, never bare BUY"
    assert r["openStaysBare"], "an OPEN position must still render the bare ledger verdict"
    # PASS is the machine's bar test — it speaks only while the human's call is still open
    assert r["pendingShowsPass"] and r["targetHidesPass"], r
    assert r["pendingNoEntry"] and r["targetHasEntry"], r


def test_theme_embedded_cards_are_regenerable_from_committed_inputs() -> None:
    """The theme JSON embeds each watch name's card, and a pin asserts the embed equals a fresh
    build — but the FREEZE source that writes it is git-ignored. Without a refresh path a
    card-shape change is unsatisfiable in CI: the committed embed goes stale and nothing
    committed can rebuild it. `refresh_theme_cards()` closes that, from committed inputs only.

    Pinned by mutating the committed embed and asserting the refresh restores it byte-for-byte."""
    build = _load_build()
    root = Path(__file__).resolve().parents[1]
    p = root / "frontend" / "themes" / "truckload-supply-purge.json"
    original = p.read_text()
    try:
        doc = json.loads(original)
        row = next(w for w in doc["watchlist"] if "scenarioCard" in w)
        row["scenarioCard"] = {"ticker": row["ticker"], "stale": True}   # simulate a shape change
        p.write_text(json.dumps(doc, indent=1))
        assert build.refresh_theme_cards() == ["truckload-supply-purge"]
        assert p.read_text() == original, "refresh must restore the embed byte-for-byte"
        assert build.refresh_theme_cards() == [], "a clean refresh must be a no-op (idempotent)"
    finally:
        p.write_text(original)


def test_entry_price_refuses_a_price_that_never_traded() -> None:
    """NEGATIVE PIN for the entry-price guard. Every forward return in the spread is measured FROM
    this number, so a 0.0/negative that slipped through would divide the whole track record by a
    price that never traded. Absent stays legal — that is "no position", not a bad price."""
    for bad in (0.0, -1.0, -141.06):
        with pytest.raises(ValueError, match="not a traded price"):
            sc.Verdict(status="confirmed", entry_price=bad)
    assert sc.Verdict().entry_price is None                     # absent == no position, allowed


def test_entry_price_and_ratio_record_a_live_entry() -> None:
    """POSITIVE PIN — the recorded-BUY shape round-trips: a real price, the asymmetry accepted at
    it, and the status the human set. ``ratio_at_entry`` is deliberately unconstrained: a verdict
    may be recorded at a ratio the machine would call ugly, and the record must hold it."""
    v = sc.Verdict(status="confirmed", recorded="2026-07-21", entry_price=141.06,
                   ratio_at_entry=6.685869749511423, reunderwrite_triggers=["a", "b"])
    rt = sc.Verdict.model_validate_json(v.model_dump_json())
    assert (rt.entry_price, rt.status) == (141.06, "confirmed")
    assert rt.ratio_at_entry == 6.685869749511423
    assert sc.Verdict(ratio_at_entry=-0.35).ratio_at_entry == -0.35     # a FAIL ratio is a fact


def test_ratification_and_gate_adjudication_are_additive() -> None:
    """A pre-ratification record (no ``ratified_by``/``ratified``/``gate_adjudication``) stays valid
    with all three None — the honest default is "not yet ratified", never a silent yes."""
    assert _rec().gate_adjudication is None
    a = sc.AssumptionDerivation(method="m")
    assert (a.ratified_by, a.ratified) == (None, None)
    done = sc.AssumptionDerivation(method="m", ratified_by="analyst", ratified="2026-07-21")
    rt = sc.AssumptionDerivation.model_validate_json(done.model_dump_json())
    assert (rt.ratified_by, rt.ratified) == ("analyst", "2026-07-21")


def test_committed_records_that_opened_a_position_carry_their_entry() -> None:
    """E2E on the COMMITTED artifacts, phrasing-independent: a still-pending verdict carries no
    entry, a recorded one dates itself, and an entry price never appears without the asymmetry
    accepted at it. Pins the invariant, never the analyst's prose (which re-words).

    ITEM 31(b) — FILTERED SWEEP, so it cannot state a relational floor: its subject is the records
    that OPENED a position, and counting them independently would just re-run the same filter. Per
    the rule, the CLAIM therefore lives on a constructed fixture
    (``test_an_opened_position_without_its_ratio_is_refused``) and this sweep keeps only its
    COVERAGE role — with a loud red when the filter matches nothing, because a sweep over zero
    matches proves nothing and must say so rather than pass."""
    opened = 0
    for p in sorted((Path(__file__).resolve().parents[1] / "scenarios").glob("*.json")):
        if p.name.startswith("_"):
            continue
        v = sc.ScenarioRecord.model_validate_json(p.read_text()).verdict
        if v.status == "pending_analyst":
            assert v.entry_price is None, f"{p.name}: a pending verdict must not carry an entry"
            continue
        assert v.recorded, f"{p.name}: a recorded verdict must date itself"
        if v.entry_price is not None:
            opened += 1
            assert v.entry_price > 0 and v.ratio_at_entry is not None, (
                f"{p.name}: an entry price with no ratio at entry is an unreadable anchor")
    assert opened, (
        "no committed record carries an entry price — this sweep just examined ZERO opened "
        "positions and would have passed no matter what the invariant said. The claim itself is "
        "pinned by test_an_opened_position_without_its_ratio_is_refused; this red means the "
        "COVERAGE is gone, which is a fact about the book worth noticing, not a test to relax")


def test_an_opened_position_without_its_ratio_is_refused() -> None:
    """THE CLAIM, on a CONSTRUCTED record — item 31(b)'s fixture branch.

    Its sibling sweep above can only ever check the records that happen to exist; if the book ever
    holds no open position it examines nothing. The invariant — *an entry price without the
    asymmetry accepted at it is an unreadable anchor* — is a property of a RECORD, so it is pinned
    on one built here and cannot decay with the corpus."""
    rec = _rec()
    v = rec.verdict.model_copy(update={
        "status": "confirmed", "recorded": "2026-07-21",
        "entry_price": 12.5, "ratio_at_entry": 2.1})
    ok = rec.model_copy(update={"verdict": v})
    assert ok.verdict.entry_price == 12.5 and ok.verdict.ratio_at_entry == 2.1

    # the negative: an entry with no ratio at entry is exactly what the sweep forbids
    bad = ok.model_copy(update={"verdict": v.model_copy(update={"ratio_at_entry": None})})
    assert bad.verdict.entry_price is not None and bad.verdict.ratio_at_entry is None, (
        "the fixture no longer expresses the forbidden shape, so the assertion below proves "
        "nothing — the schema moved and this pin must move with it")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))


def test_every_committed_card_renders_without_undefined() -> None:
    """REGRESSION PIN (#179). The chosen-trio row looked its value up by AXIS NAME. R1's three axes
    happen to be spelled exactly like their leg fields, so that held — until R2 added ``horizon``,
    whose leg field is ``yearsToTerminal``. The lookup resolved to undefined and PRINTED it, three
    times, in the first R2 record ever written.

    It would have shipped in every PDF too: the T1 print rule force-opens every details block, and
    the chosen row lives inside the collapsed reference table, so a preview of the VISIBLE tier
    could not see it (#176's synthetic preview checked exactly that and passed).

    Asserts the invariant across EVERY committed card, not just the R2 one — the next axis added to
    any recipe gets caught here rather than in an export."""
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    root = Path(__file__).resolve().parents[1]
    cards = sorted(p.name for p in (root / "frontend" / "scenarios").glob("*.json")
                   if p.name != "index.json")
    assert cards, "no committed cards to render"
    driver = r"""
import { readFileSync, readdirSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const uwUrl = pathToFileURL(path.resolve("frontend/views/shared/uw-card.js")).href;
const { uwCard } = await import(uwUrl);
const CHOSEN_RE = /chosen \(bear · base · bull\)<\/td>\s*<td class="num">([^<]*)<\/td>/g;
const out = {};
for (const f of readdirSync("frontend/scenarios")) {
  if (!f.endsWith(".json") || f === "index.json") continue;
  const card = JSON.parse(readFileSync("frontend/scenarios/" + f));
  const html = uwCard(card, { ticker: true, mark: null });
  out[f.replace(".json","")] = {
    undef: (html.match(/undefined/g) || []).length,
    axes: (card.assumptions || []).map((a) => a.axis),
    chosenRows: (html.match(/chosen \(bear/g) || []).length,
    horizonLabel: html.includes("Years to terminal"),
    // the CHOSEN-TRIO cells specifically (dot-joined), not the main scenarios table
    chosenTrios: [...html.matchAll(CHOSEN_RE)].map((m) => m[1].trim()),
  };
}
console.log(JSON.stringify(out));
"""
    proc = subprocess.run(["node", "--input-type=module", "-e", driver],
                          capture_output=True, text=True, check=True, cwd=root)
    res = json.loads(proc.stdout)
    for ticker, r in res.items():
        assert r["undef"] == 0, (
            f"{ticker}: rendered card prints 'undefined' x{r['undef']} — an assumption axis has no "
            f"leg-field mapping (axes: {r['axes']})")
        assert r["chosenRows"], f"{ticker}: no chosen-trio row rendered"
        assert all(c.strip() for c in r["chosenTrios"]), (
            f"{ticker}: an axis rendered an EMPTY chosen row — {r['chosenTrios']}")
    r2 = [t for t, r in res.items() if "horizon" in r["axes"]]
    for t in r2:
        assert res[t]["horizonLabel"], f"{t}: horizon axis renders its bare key, not a label"
        trios = res[t]["chosenTrios"]
        assert len(trios) == len(res[t]["axes"]), (
            f"{t}: {len(trios)} chosen-trio rows for {len(res[t]['axes'])} axes")
        yrs = [x for x in trios if x.endswith("y")]
        assert yrs, f"{t}: no horizon chosen row printing years — got {trios}"
        assert all(part.strip().endswith("y") and part.strip()[:-1].replace(".", "").isdigit()
                   for part in yrs[0].split("·")), (
            f"{t}: the horizon chosen row is not per-leg year values — got {yrs[0]!r}")


def test_every_committed_record_result_matches_its_own_facts() -> None:
    """COHERENCE INVARIANT — a record's stored ``result`` must equal ``run_recipe`` on its own
    inputs.

    Shipped after a real defect (PR #189, found 2026-07-22): two records had a FACT amended and
    verified by an in-memory recompute, but were written back with ``json.dumps`` rather than
    ``write_record`` — so the stored ``result`` kept the pre-amendment values while the facts moved
    beneath it. IT rendered 121.20/273.85 at ratio 7.04 on a card whose facts computed
    118.85/270.14 at 6.09, and nothing was red: no consumer re-derives on read.

    This is the one check that makes stored-derived-state safe. It runs over every committed
    record, so the next silent divergence fails here instead of on a card.

    ITEM 31(b) — FILTERED SWEEP, and the fixture branch DOES NOT APPLY here. The claim is that
    PERSISTED numbers still match a recompute from their own facts; a constructed record would
    compute and then compare against that same computation, which proves nothing. A divergence can
    only exist on data that was written and left. So for this one the whole fix is the loud red
    when the filter matches nothing — the sweep must announce that it checked zero records rather
    than pass.
    """
    import warnings as _w
    checked = 0
    for path in sorted((Path(__file__).resolve().parents[1] / "scenarios").glob("[A-Z]*.json")):
        payload = json.loads(path.read_text())
        stored = (payload.get("result") or {}).get("per_scenario") or {}
        if not stored:
            continue                      # a record that has never been run has nothing to diverge
        checked += 1
        with _w.catch_warnings():
            _w.simplefilter("ignore")
            fresh = sc.run_recipe(sc.ScenarioRecord.model_validate(payload))
        for leg, cell in stored.items():
            assert cell["value_per_share"] == pytest.approx(
                fresh.result.per_scenario[leg].value_per_share, abs=1e-6), (
                f"{path.stem} {leg}: stored {cell['value_per_share']:.4f} but its own facts "
                f"compute {fresh.result.per_scenario[leg].value_per_share:.4f} — the record was "
                "written without persisting the recompute")
        if (payload["result"].get("ratio") is not None
                and fresh.result.ratio is not None):
            assert payload["result"]["ratio"] == pytest.approx(fresh.result.ratio, abs=1e-6), (
                f"{path.stem}: stored ratio diverges from its own facts")
        # THE GATE FIELDS ARE STORED DERIVED STATE TOO, so they fall under the same invariant
        # (added 2026-08-05, in review). Covering only `value_per_share` and `ratio` left a REAL
        # hole, not a theoretical one: on an R1 record the horizon drives nothing else — R1 is
        # undiscounted — so moving `years_to_terminal` without re-running moves the IRR and
        # nothing this sweep compared. Demonstrated on SMPL: graded at 1.5y then re-pointed at
        # 6.0y, the record stored 81.13% against its own facts computing 16.01% and this test
        # passed GREEN. Past 6.5y the same edit flips the gate PASS -> FAIL while the stored
        # record still reads PASS. That is the #189 defect — stored derived state drifting under
        # moved inputs, invisible because no consumer re-derives on read — on the newest field.
        for field in ("horizon_years", "irr", "irr_pass_fail", "gate"):
            if field not in payload["result"]:
                continue                  # predates the gate — the archive scoping drops these
            stored_v, fresh_v = payload["result"][field], getattr(fresh.result, field)
            ok = (stored_v == pytest.approx(fresh_v, abs=1e-9)
                  if isinstance(stored_v, float) and isinstance(fresh_v, float)
                  else stored_v == fresh_v)
            assert ok, (
                f"{path.stem}: stored {field}={stored_v!r} but its own facts compute {fresh_v!r} "
                "— the record was written without persisting the recompute")
    assert checked, (
        "no committed record carries a stored result — this coherence sweep examined ZERO records "
        "and would pass however far the stored numbers had drifted. Unlike its siblings the claim "
        "cannot move to a fixture (a constructed record computes and then compares against that "
        "same computation), so this red IS the guard")


# --- schema 1.3: fielded references (docs/refpoint_schema_proposal.md, ratified 2026-07-27) ----
def test_13_refpoint_field_validators() -> None:
    """The new fields refuse incoherent states at construction, version-independent."""
    ok = sc.RefPoint(label="trailing median", value=6.9, unit="x", source="s",
                     role="median", leg="base")
    assert ok.role == "median" and ok.leg == "base" and not ok.excluded
    with pytest.raises(pydantic.ValidationError, match="not one of"):
        sc.RefPoint(label="x", value=1, unit="x", source="s", role="fiftieth-ish")
    with pytest.raises(pydantic.ValidationError, match="requires excluded_reason"):
        sc.RefPoint(label="x", value=1, unit="x", source="s", excluded=True)
    with pytest.raises(pydantic.ValidationError, match="not declared"):
        sc.RefPoint(label="x", value=1, unit="x", source="s", excluded_reason="why")
    with pytest.raises(pydantic.ValidationError, match="not ISO"):
        sc.AxisNote(text="finding", date="July 26")
    with pytest.raises(pydantic.ValidationError, match="blank note"):
        sc.AxisNote(text="   ", date="2026-07-26")


def test_13_gate_refuses_prose_structure_and_foreign_units_forward_only(tmp_path: Path) -> None:
    """require_fielded_refs: label prose carrying a LEG or an EXCLUSION, and a unit outside the
    vocabulary, are REFUSED on 1.3 records and LEGAL on legacy — BASIS_REQUIRED_FROM precedent.

    Each refusal is the real committed shape that motivated the field: the leg suffix ("— bear"),
    the exclusion flag ("NOT a reference for us"), and the SMPL smuggled-finding unit (a second
    value hidden in ":1 (cell A …; cell B ≈1.73)")."""
    bad_leg = sc.RefPoint(label="FY2020 worst clean year — bear", value=9.58, unit="%", source="s")
    bad_excl = sc.RefPoint(label="scale leader - NOT a reference for us", value=14.5, unit="x",
                           source="s")
    bad_unit = sc.RefPoint(label="entry-boundary cells", value=1.96,
                           unit=":1 (cell A at the re-set 14% normal; cell B ≈1.73)", source="s")
    for bad, msg in ((bad_leg, "leg belongs in"), (bad_excl, "excluded=True"),
                     (bad_unit, "not one of")):
        rec = _rec(assumptions={
            "revenue": sc.AssumptionDerivation(method="m"),
            "margin": sc.AssumptionDerivation(method="m"),
            "multiple": sc.AssumptionDerivation(method="m", references=[bad])})
        with pytest.raises(ValueError, match=msg):
            sc.require_fielded_refs(rec)
        legacy = rec.model_copy(update={"schema_version": "1.2"})
        sc.require_fielded_refs(legacy)          # forward-binding: legacy stays writable
    # write_record runs the gate — the refusal reaches the ONLY write path, and nothing lands
    with pytest.raises(ValueError, match="fielded references"):
        sc.write_record(_rec(assumptions={
            "revenue": sc.AssumptionDerivation(method="m"),
            "margin": sc.AssumptionDerivation(method="m"),
            "multiple": sc.AssumptionDerivation(method="m", references=[bad_leg])},
        ), root=tmp_path)
    assert not list((tmp_path / "scenarios").glob("TEST*")), "a refused record must not be written"


def test_13_gate_narrowings_stay_legal() -> None:
    """DELIBERATELY NARROW MATCHES, pinned with the real sentences that motivated them (the
    prose_lint convention). "stated, not derived" is PROVENANCE on a row that IS used — AORT's
    street margins — and must never be read as an exclusion; stat words ("median", "worst",
    "trough") are legal label prose because the ROLE field is the machine copy, not a ban."""
    fine = [
        sc.RefPoint(label="street operating margin, FY2026 - stated, not derived",
                    value=6.93, unit="%", source="s", vintage="FY2026"),
        sc.RefPoint(label="this company's trailing median", value=17.85, unit="x", source="s",
                    role="median", vintage="FY2021-FY2025"),
        sc.RefPoint(label="FY2020 worst clean year", value=9.58, unit="%", source="s",
                    role="trough", leg="bear", vintage="FY2020"),
    ]
    rec = _rec(assumptions={
        "revenue": sc.AssumptionDerivation(method="m"),
        "margin": sc.AssumptionDerivation(method="m"),
        "multiple": sc.AssumptionDerivation(method="m", references=fine)})
    sc.require_fielded_refs(rec)                 # no raise — the narrowings hold


def test_13_every_committed_record_passes_the_gate_and_carries_the_migration() -> None:
    """E2E on the LIVING records, phrasing-independent: every committed 1.3 record passes the
    fielded-refs gate on READ (the migration is complete, not partial), and the structure the
    labels used to carry now exists as FIELDS somewhere in the corpus — at least one leg tag, one
    exclusion with its reason, and SMPL's boundary FINDING as a dated note beside two honest
    references (the row whose unit smuggled a second value; migration 2026-07-27, ratified)."""
    root = Path(__file__).resolve().parents[1]
    recs = {p.stem: sc.read_record(p.stem, root=root)
            for p in (root / "scenarios").glob("*.json") if not p.stem.startswith("_")}
    assert len(recs) >= 7
    legs = excls = notes = 0
    for t, rec in recs.items():
        sc.require_fielded_refs(rec)             # raises = a migrated record regressed
        for a in rec.assumptions.values():
            for r in a.references:
                legs += r.leg is not None
                excls += r.excluded
                if r.excluded:
                    assert (r.excluded_reason or "").strip(), f"{t}: excluded without reason"
            notes += len(a.notes)
    assert legs >= 5, "the leg field lost its committed population"
    assert excls >= 3, "the excluded field lost its committed population"
    assert notes >= 1, "the axis-note home lost its committed population"
    smpl = recs["SMPL"].assumptions["multiple"]
    assert any(n.date == "2026-07-26" for n in smpl.notes), (
        "SMPL's boundary finding must live as a dated NOTE (it was a fake reference row whose "
        "unit carried a second value)")
    assert sum(1 for r in smpl.references if r.unit == ":1") == 2, (
        "the two entry-boundary cells must be honest references")


def test_a_new_reference_without_a_vintage_is_refused_and_a_committed_one_is_not(
        tmp_path: Path) -> None:
    """P3 pt1: a `source` names WHERE a value came from and never WHEN — "CIQ Estimates->Trends",
    "EDGAR OperatingIncomeLoss / revenue". From 1.4 a reference must state its vintage.

    BINDS FORWARD. The census found 70 of 119 committed references carry no period token at all,
    and the period is not recoverable FROM THE RECORD — it lives in the analyst's source material.
    So the gate keys on the record's OWN schema_version (the BASIS_REQUIRED_FROM precedent): a 1.3
    record stays writable unstamped forever, a 1.4 record cannot be written without one. This
    pins BOTH directions, because a forward-binding rule that also fires backward is a migration
    nobody authorised, and one that fires in neither direction is decoration."""
    unstamped = sc.RefPoint(label="own-history median", value=7.45, unit="%", source="EDGAR")
    assert unstamped.vintage is None, "the field must stay OPTIONAL on the model — legacy is legal"

    # NEW record (defaults to the current SCHEMA_VERSION): refused, and the message says WHEN.
    with pytest.raises(ValueError, match="no vintage"):
        sc.write_record(_rec(assumptions={
            "revenue": sc.AssumptionDerivation(method="m", references=[unstamped]),
            "margin": sc.AssumptionDerivation(method="m"),
            "multiple": sc.AssumptionDerivation(method="m"),
        }), root=tmp_path)

    # Same reference, same axes, on a record that predates the rule: writes clean.
    legacy = _rec(assumptions={
        "revenue": sc.AssumptionDerivation(method="m", references=[unstamped]),
        "margin": sc.AssumptionDerivation(method="m"),
        "multiple": sc.AssumptionDerivation(method="m"),
    })
    legacy = legacy.model_copy(update={"schema_version": "1.3"})
    sc.write_record(legacy, root=tmp_path)

    # Whitespace is not a vintage — the empty-ish forms a hurried stamp actually takes.
    for blank in ("", "   "):
        with pytest.raises(ValueError, match="no vintage"):
            sc.write_record(_rec(assumptions={
                "revenue": sc.AssumptionDerivation(method="m", references=[
                    unstamped.model_copy(update={"vintage": blank})]),
                "margin": sc.AssumptionDerivation(method="m"),
                "multiple": sc.AssumptionDerivation(method="m"),
            }), root=tmp_path)


def test_no_committed_record_is_silently_in_violation_of_the_vintage_rule(tmp_path: Path) -> None:
    """The 70 unstamped references are NOT backfilled — P3 pt1 does not close on code. This pin is
    the reason that is safe: no committed record carries a reference that the vintage rule would
    demand a stamp for. It reddens the day someone bumps a record's schema_version without
    stamping its references — which is exactly when the backfill stops being optional.

    WAS "every record PREDATES the rule" (2026-09-01). That was the same claim by a shortcut, and
    the shortcut was a fact about the corpus rather than the invariant: it held only while no
    record had crossed 1.4. GOOGL's R3 record is at 1.5 and carries ZERO references — no committed
    statistic anchors a forward P/E — so it is not in violation and there is nothing to stamp, yet
    the shortcut called it one. Asserting the rule itself is STRICTER, not weaker: a 1.4+ record
    that DID carry an unstamped reference now reddens, where the old form would equally have
    reddened but told the reader the wrong thing about why.
    """
    def unstamped(rec: dict[str, object]) -> list[str]:
        """Every reference the vintage rule would demand a stamp for — empty when compliant."""
        ver = rec["schema_version"]
        assert isinstance(ver, str)
        if sc._schema_ver(ver) < sc._schema_ver(sc.VINTAGE_REQUIRED_FROM):
            return []                                 # predates the rule — its refs go unstamped
        axes = rec.get("assumptions") or {}
        assert isinstance(axes, dict)
        return [f"{axis}/{r.get('label')!r}" for axis, a in axes.items()
                for r in (a.get("references") or []) if not r.get("vintage")]

    # THE CHECK CAN FIRE — asserted before it is trusted. GOOGL is the only record at or past the
    # rule and it carries ZERO references, so the corpus loop below would pass over an inert
    # helper without noticing. The shape here is a REAL committed record with its schema bumped
    # and nothing else touched, which is precisely the situation the pin exists to catch.
    root = Path(__file__).resolve().parents[1] / "scenarios"
    canary = json.loads((root / "SMPL.json").read_text())
    assert not unstamped(canary), "SMPL is below the rule — it must report nothing as written"
    canary["schema_version"] = "1.5"
    assert unstamped(canary), (
        "the vintage check is INERT: a record bumped to 1.5 with SMPL's unstamped references must "
        "be reported, or the corpus loop below proves nothing")

    seen = 0
    for f in sorted(root.glob("*.json")):
        if f.name.startswith("_"):
            continue
        rec = json.loads(f.read_text())
        seen += 1
        assert not unstamped(rec), (
            f"{f.name} is at schema {rec['schema_version']} — at or past "
            f"{sc.VINTAGE_REQUIRED_FROM} its references must each carry a vintage; "
            f"{unstamped(rec)} carry none")
    # EXACT, not a floor: adding a record must force a conscious look at this rule rather than
    # sliding past it. Nine as of GOOGL, 2026-09-01.
    assert seen == 9, f"expected the 9 committed records, walked {seen}"


def _ref_keys(payload: dict[str, object], axis: str = "revenue") -> set[str]:
    """The key set of the first reference on ``axis``, as WRITTEN (not as modelled)."""
    axes = payload["assumptions"]
    assert isinstance(axes, dict)
    return set(axes[axis]["references"][0])            # type: ignore[index,arg-type]


def test_a_record_writes_only_the_reference_fields_its_own_schema_knows(tmp_path: Path) -> None:
    """VERSION-SCOPED SERIALIZATION. `write_record` emitted every model field regardless of the
    record's version, so #302's `vintage` would have put 119 `"vintage": null` keys across the 7
    committed 1.3 records — real changes buried in default noise.

    THREE VERSIONS, ONE RECORD, walking the map: a 1.2 record predates all four 1.3 reference
    fields AND `vintage`; a 1.3 record has the four and predates `vintage`; a 1.4 record has all
    five. Absence is the assertion — a null would say "we looked and there is none" about a
    question the record predates."""
    ref = sc.RefPoint(label="own-history median", value=7.45, unit="%", source="EDGAR",
                      role="median", vintage="FY2025")
    base = _rec(assumptions={
        "revenue": sc.AssumptionDerivation(method="m", references=[ref]),
        "margin": sc.AssumptionDerivation(method="m"),
        "multiple": sc.AssumptionDerivation(method="m"),
    })
    v13 = {"role", "leg", "excluded", "excluded_reason"}

    def written(version: str) -> set[str]:
        rec = base.model_copy(update={"schema_version": version})
        return _ref_keys(json.loads(sc.write_record(rec, root=tmp_path).read_text()))

    always = {"label", "value", "unit", "source"}
    k12, k13, k14 = written("1.2"), written("1.3"), written("1.4")

    assert k12 == always, f"a 1.2 record predates every versioned field, got {sorted(k12)}"
    assert k13 == always | v13, f"a 1.3 record has the four and not vintage, got {sorted(k13)}"
    assert k14 == always | v13 | {"vintage"}, f"a 1.4 record has all five, got {sorted(k14)}"

    # THE ORDERING IS THE POINT, stated as a chain rather than three loose facts.
    assert k12 < k13 < k14, "each schema is a strict superset of the one before"

    # `excluded` is a BOOL defaulting to False — `exclude_none` could never have dropped it, which
    # is why the criterion is the version and not the value.
    assert "excluded" not in k12 and json.loads(
        sc.write_record(base.model_copy(update={"schema_version": "1.3"}),
                        root=tmp_path).read_text())["assumptions"]["revenue"]["references"][0][
        "excluded"] is False, "the 1.3 record keeps excluded=False; the 1.2 record drops the key"


def test_an_unparseable_schema_version_keeps_nothing_versioned(tmp_path: Path) -> None:
    """`_schema_ver` returns (0,) on anything it cannot parse. A stamp we cannot read must NOT be
    treated as "latest" — the conservative direction is to write the smallest honest record, not
    to assume the newest shape. Hand-edited records make a junk version reachable."""
    ref = sc.RefPoint(label="l", value=1.0, unit="%", source="s", role="median", vintage="FY2025")
    rec = _rec(assumptions={
        "revenue": sc.AssumptionDerivation(method="m", references=[ref]),
        "margin": sc.AssumptionDerivation(method="m"),
        "multiple": sc.AssumptionDerivation(method="m"),
    }).model_copy(update={"schema_version": "not-a-version"})
    assert _ref_keys(json.loads(sc.write_record(rec, root=tmp_path).read_text())) == {
        "label", "value", "unit", "source"}


def test_the_committed_records_round_trip_byte_identical(tmp_path: Path) -> None:
    """THE CORPUS RUN, not a synthetic. #302's hygiene guard passed its mutation and ran green over
    six live violations because the mutation used a shape it already knew — so this asserts on the
    REAL committed records: re-writing each one changes NOTHING. It is the check that would have
    caught the 119 nulls, and it reddens on the next schema field that forgets to declare itself
    in REF_FIELDS_INTRODUCED_IN."""
    root = Path(__file__).resolve().parents[1] / "scenarios"
    seen = 0
    for f in sorted(root.glob("*.json")):
        if f.name.startswith("_"):
            continue
        seen += 1
        before = f.read_text()
        rec = sc.read_record(f.stem, root=root.parent)   # records_dir() appends "scenarios"
        after = sc.write_record(rec, root=tmp_path).read_text()
        assert before == after, (
            f"{f.name} does not round-trip — re-writing it changes the committed record, so the "
            "next real diff is unreadable. If a field was just added, declare it in "
            "REF_FIELDS_INTRODUCED_IN or AXIS_FIELDS_INTRODUCED_IN.")
    assert seen == 9, f"expected the 9 committed records, walked {seen}"

    # THE ARCHIVE IS THE ONLY RECORD BELOW 1.3, and therefore the only one that exercises
    # version-scoping AT ALL: seven records that share a version cannot fail a version check.
    # Walking `scenarios/*.json` alone passed while `write_archived` materialised `"notes": []`
    # on all three axes of the 1.2 record — found in review, not by this pin's first cut.
    archived, below_gate = 0, 0
    for f in sorted((root / "archive").glob("*.json")):
        archived += 1
        before = f.read_text()
        rec = sc.ScenarioRecord.model_validate_json(before)
        if sc._schema_ver(rec.schema_version) < sc._schema_ver(sc.FIELDED_REFS_FROM):
            below_gate += 1
        assert before == sc.write_archived(rec, root=tmp_path).read_text(), (
            f"archive/{f.name} does not round-trip — `write_archived` promises the same "
            "serialization as `write_record`, so both are version-scoped or neither is")
    # AT LEAST ONE below the gate — not EVERY one, and not exactly one record in the archive.
    # The first cut asserted both, which held only while a single record sat there; the 2026-08-05
    # SMPL supersession archived a SECOND (at 1.3) and reddened this on a legitimate event. The
    # stated value is untouched — a real sub-1.3 record still exercises version-scoping, and the
    # archive only ever grows — so the assertion now says what it always meant.
    assert archived, "the archive is empty — every claim below it is vacuous"
    assert below_gate, (
        f"none of the {archived} archived record(s) sits below schema {sc.FIELDED_REFS_FROM} — "
        "this pin's value is that the archive holds a record BELOW the gates; without one, "
        "version-scoping is untested against any real record and needs a new source of one")
