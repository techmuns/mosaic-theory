"""(STATE row 26) The load-bearing axis is per name, and no panel claims one for a name that has
not declared it.

THE DEFECT: `MULTIPLE_AND_PRICE.changes_the_call` carried GOOGL's condition verbatim — "for a
quality megacap the multiple IS the trade … the call breaking on THE ONLY AXIS THAT CAN BREAK IT"
— in a panel that applies to every name. It is false for a name whose case is earnings arrival,
where the multiple has been paid nothing for. The panel was not wrong to EXIST for such a name;
it was wrong about what CHANGES THE CALL, which is the field the design made mandatory precisely
so a panel could not be decorative.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest

from vinci.panels import PanelSpec, RenderOption
from vinci.panels_declare import PanelDeclarationError, all_registries, read_declarations
from vinci.panels_universal import MULTIPLE_AND_PRICE, UNIVERSAL_SEVEN

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: The scan #608 used, kept as the guard. Measured then: exactly one of seven hit.
ARCHETYPE = re.compile(r"only axis|the multiple IS|megacap|bear EPS", re.I)


def test_no_universal_panel_states_one_positions_archetype_as_universal() -> None:
    """The whole tier, not just the panel that failed — the scan is the guard, not the fix."""
    hits = [s.key for s in UNIVERSAL_SEVEN if ARCHETYPE.search(s.changes_the_call)]
    assert hits == [], f"archetype-bound language in a universal panel: {hits}"


def test_the_multiple_panel_carries_the_axis_as_per_name_config() -> None:
    """`config_schema` was added so the tier's 'varies by config only' claim could be expressed and
    then went unused across all seven. This is the first panel to make it true."""
    opt = MULTIPLE_AND_PRICE.render_config.get("load_bearing_axis")
    assert opt is not None
    assert opt.allowed == ("multiple", "earnings")
    assert opt.means.strip()


def test_a_render_key_is_not_refused_as_a_no_op_the_way_a_probe_key_is() -> None:
    """The two kinds of config are separate BECAUSE the no-op guard is only right about one.

    `config_schema` keys are read by a requirement, so one nothing reads is a silent no-op and is
    refused. A render key is consumed by the RENDERER, so that same check would reject it while
    being correct about probe keys.
    """
    ok = PanelSpec(key="k", tier="universal", title="T", changes_the_call="c",
                   render_config={"axis": RenderOption(means="m")})
    assert "axis" in ok.render_config
    with pytest.raises(Exception, match="no requirement reads"):
        PanelSpec(key="k2", tier="universal", title="T", changes_the_call="c",
                  config_schema={"orphan": "nothing reads this"})


def test_an_axis_outside_the_declared_set_raises_and_names_the_ruling() -> None:
    """THE FALSIFIER, AS A MACHINE CHECK. The record attaches one to this field: "a third R3 record
    matching neither archetype, at which point the field must be a statement rather than an enum."
    A name that fits neither raises at DECLARE time naming that ruling, rather than being quietly
    mis-filed under whichever value was closest."""
    bad = {"X": {"followed_since": "2026-01-01", "sleeve": "quality",
                 "panels": {"multiple_and_price": {"load_bearing_axis": "sentiment"}}}}
    tmp = ROOT / "tests" / "fixtures" / "_axis_tmp"
    (tmp / "data").mkdir(parents=True, exist_ok=True)
    (tmp / "data" / "followed.json").write_text(json.dumps(bad))
    try:
        with pytest.raises(PanelDeclarationError) as got:
            read_declarations(root=tmp)
        assert "not one of ['earnings', 'multiple']" in str(got.value)
        assert "free statement" in str(got.value), "the error names the ruling, not just the error"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_the_declaration_reader_spans_every_tier() -> None:
    """`followed.json` describes a name's WHOLE grid. Validating it against one tier's registry
    rejected the others — the moment GOOGL declared `multiple_and_price` (universal) the emitter,
    which passed the COHORT registry, refused the whole file and took the grid down with it."""
    keys = set(all_registries().keys())
    assert {"multiple_and_price", "commissioning", "theme_thesis"} <= keys
    decl = read_declarations(root=ROOT)
    assert decl, "no declarations read"
    for ticker, panels in decl.items():
        for k in panels:
            assert k in keys, f"{ticker} declares {k}, unknown to the merged registry"


def test_googl_declares_the_multiple_and_no_name_declares_an_axis_it_cannot_support() -> None:
    """CORPUS: GOOGL's own record says the entire bear outcome is a de-rating. WST is deliberately
    NOT set — its underwrite has not landed, and a value invented ahead of the record would be the
    coverage-that-isn't this field exists to prevent."""
    decl = read_declarations(root=ROOT)
    # The panel now carries a second per-name key (`valuation_metric`), so this asserts the AXIS
    # rather than the whole config object — a pin on the exact dict reddens whenever the panel
    # gains an unrelated knob, which is noise rather than a finding.
    assert decl["GOOGL"]["multiple_and_price"]["load_bearing_axis"] == "multiple"
    axes = {t: p.get("multiple_and_price", {}).get("load_bearing_axis")
            for t, p in decl.items()}
    assert {t for t, a in axes.items() if a} == {"GOOGL"}, (
        "exactly one name declares an axis today; when WST's underwrite lands, set it and update "
        "this assertion deliberately")


def test_the_renderer_is_silent_about_the_axis_when_none_is_declared_node() -> None:
    """The panel text was rewritten to claim NO axis, so a name that has not named one must get a
    distance and no story about what it costs. A default here would put one position's archetype
    back on every name — the defect, reintroduced one layer down."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = r"""
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { panelGridHtml } = await import(pathToFileURL(
  path.resolve("frontend/views/shared/panels.js")).href);
const base = { tier: "universal", key: "multiple_and_price", title: "M", state: "ready",
  caveat: "", cadence: "daily", missing: [], reason: "", sources: [],
  changes_the_call: "The distance between today's multiple and the one underwritten...",
  value: { metric: "EV/EBITDA", current: 25.8, low: 10.9, high: 24.8, median: 17.4,
           percentile: 1, n_closes: 37, as_of: "2026-06-30",
           series: [["a", 1], ["b", 2]], range_excludes_current: true } };
const g = panelGridHtml([{ ...base, ticker: "GOOGL",
  render_config: { load_bearing_axis: "multiple" } }], { ticker: "GOOGL" });
const w = panelGridHtml([{ ...base, ticker: "WST",
  render_config: { load_bearing_axis: "earnings" } }], { ticker: "WST" });
const n = panelGridHtml([{ ...base, ticker: "SMPL", render_config: {} }], { ticker: "SMPL" });
const odd = panelGridHtml([{ ...base, ticker: "ZZ",
  render_config: { load_bearing_axis: "sentiment" } }], { ticker: "ZZ" });
console.log(JSON.stringify({
  multipleSaid: /rests on the MULTIPLE/.test(g),
  earningsSaid: /EARNINGS ARRIVAL/.test(w),
  undeclaredSilent: !/rests on/.test(n),
  oppositeStoriesDiffer: /breaking/.test(g) && /without the thesis moving/.test(w),
  unrecognisedShown: /unrecognised/.test(odd),
}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr
    got = json.loads(out.stdout)
    assert got == dict.fromkeys(got, True), got


def test_the_committed_artifact_carries_the_axis_for_googl_and_for_nobody_else() -> None:
    """E2E over the real artifact: the field reaches the page, and reaches only the name that
    declared it."""
    snap = json.loads((ROOT / "data" / "monitor" / "2026-08-11.json").read_text())
    rows = [p for p in snap["panels"] if p["key"] == "multiple_and_price"]
    assert rows, "no multiple panel in the artifact — this check would prove nothing"
    declared = {p["ticker"]: (p.get("render_config") or {}).get("load_bearing_axis")
                for p in rows}
    assert declared.get("GOOGL") == "multiple"
    assert {t for t, a in declared.items() if a} == {"GOOGL"}
    for p in rows:
        assert not ARCHETYPE.search(p["changes_the_call"])
