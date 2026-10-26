"""The R4 card render — an EV/NTM EBIT record's card and its markdown twin (2026-10-09).

Before this, an R4 record's card showed every input EXCEPT the one that produced its value: no EBIT
row, no bridge, and a per-leg "EV/EBIT cross-check" that only repeated the input multiple. The card
now walks the leg — NTM EBIT at exit → the multiple → EV → less TEV claims → equity — every number
the record's own, and the markdown twin carries the same columns with the same numbers.

THE RECORD IS BUILT FOR REAL. No committed R4 record exists yet (the AMZN/UBER re-tags come after
this), so one is written through the real `scenario-propose` → `scenario-create` path from AMZN's
committed page, its tag set to R4 in memory, the six leg inputs taken from the page's own figures.
The card is then emitted by `frontend/build.py` and rendered by `uw-card.js` under node — the path
the site runs. Assertions are invariants against that record, never a pinned figure (the page is a
living artifact).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import pathlib
import re
import shutil
import subprocess
from typing import Any

import pytest

import vinci.scenarios as sc
from vinci.dossier.render import (
    _assumption_methodology_lines,
    _card_thousands,
    _scenario_table_lines,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
R4_ROWS = ("NTM EBIT at exit ($M)", "EV ($M)", "less TEV claims ($M)", "Equity ($M)")

pytestmark = pytest.mark.skipif(not shutil.which("node"), reason="node unavailable")


def _load_build() -> Any:
    spec = importlib.util.spec_from_file_location("_r4_card_build", ROOT / "frontend" / "build.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_BUILD: Any = _load_build()


def _render(card: dict[str, Any], tmp: pathlib.Path) -> str:
    """`uwCard(card)` under node — the renderer the site runs."""
    src = tmp / "card.json"
    src.write_text(json.dumps(card))
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { uwCard } = await import(pathToFileURL(process.argv[1]).href);
process.stdout.write(uwCard(JSON.parse(readFileSync(process.argv[2]))));
"""
    out = subprocess.run(
        ["node", "--input-type=module", "-e", driver,
         str(ROOT / "frontend" / "views" / "shared" / "uw-card.js"), str(src)],
        capture_output=True, text=True, check=True)
    return out.stdout


def _row_cells(html: str, label: str) -> list[str]:
    m = re.search(r"<tr[^>]*><td[^>]*>" + re.escape(label) + r"</td>((?:<td[^>]*>.*?</td>)+)</tr>",
                  html)
    assert m, f"no '{label}' row on the card"
    return [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>",
                                                                   m.group(1))]


def _js_thousands(v: float) -> str:
    """`uw-card.js` `thousands`: JS Math.round (.5 toward +inf), en-US grouping."""
    return f"{math.floor(v + 0.5):,}"


@pytest.fixture(scope="module")
def r4(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """A real R4 record on AMZN's committed figures, written by the create path."""
    from vinci.cli import _cmd_scenario_create, _cmd_scenario_propose

    root = tmp_path_factory.mktemp("r4card")
    doc = json.loads((ROOT / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())
    doc["anchor"]["recipe_hint"] = sc.RECIPE_R4
    (root / "data" / "dossiers" / "AMZN").mkdir(parents=True)
    (root / "data" / "dossiers" / "AMZN" / "dossier.json").write_text(json.dumps(doc))
    (root / "scenarios").mkdir()
    mp = pytest.MonkeyPatch()
    mp.chdir(root)
    try:
        tpl_path = root / "tpl.json"
        assert _cmd_scenario_propose(argparse.Namespace(ticker="AMZN", out=str(tpl_path))) == 0
        fc = doc["forward_consensus"]
        ebit = next(s["mean"] for s in fc["spreads"]
                    if s["metric"] == "EBIT" and s["period"] == "FY 2028")
        mult = next(m["value"] for m in fc["current_multiples"]
                    if m["metric"] == "TEV/EBIT" and m["period"] == "NTM")
        tpl = json.loads(tpl_path.read_text())
        for scale, leg in ((0.8, "bear"), (1.0, "base"), (1.1, "bull")):
            tpl["scenarios"][leg].update(
                ebit=round(ebit * scale, 2), multiple=round(mult * scale, 4),
                reason=f"{leg} test leg", ebit_derivation="FY2028 consensus EBIT, scaled",
                multiple_derivation="today's NTM EV/EBIT, scaled")
        tpl["scenarios"]["base"].update(years_to_terminal=1.25, leg_fy="2028")
        tpl["scenarios"]["bear"]["bear_basis"] = "analyst"
        # struck on the page's OWN close: a fixed date reds on every re-assembly onto a later
        # close (`scenario-create` refuses a spot after the underwrite date, correctly)
        assert tpl["spot_as_of"], "AMZN: the page carries no spot date to strike the legs on"
        tpl.update(entry_basis="NTM", entry_denominator=round(ebit / 1.5, 1),
                   underwrite_date=tpl["spot_as_of"], analyst="test")
        tpl_path.write_text(json.dumps(tpl))
        assert _cmd_scenario_create(argparse.Namespace(ticker="AMZN",
                                                       from_file=str(tpl_path))) == 0
        rec: dict[str, Any] = json.loads((root / "scenarios" / "AMZN.json").read_text())
    finally:
        mp.undo()
    return rec


# --- the emitter --------------------------------------------------------------------------------

def test_the_emitter_carries_the_r4_leg_driver(r4: dict[str, Any]) -> None:
    card = _BUILD._scenario_card(r4)
    by = {s["name"]: s for s in card["scenarios"]}
    for leg, s in r4["scenarios"].items():
        assert by[leg]["ebit"] == s["ebit"], f"{leg}: the card lost the leg's driver"


def test_a_record_without_ebit_emits_no_ebit_key() -> None:
    """GOOGL's committed R3 card is unchanged by construction: no `ebit` key."""
    rec = json.loads((ROOT / "scenarios" / "GOOGL.json").read_text())
    assert all("ebit" not in s for s in _BUILD._scenario_card(rec)["scenarios"])


# --- the card -----------------------------------------------------------------------------------

def test_the_r4_card_walks_the_leg_from_ebit_to_equity(
    r4: dict[str, Any], tmp_path: pathlib.Path,
) -> None:
    """Each R4 row carries the record's own number, as the card formats it: the leg's EBIT, its EV
    and equity (`result.per_scenario`), and the `net_debt` fact the record subtracted."""
    card = _BUILD._scenario_card(r4)
    html = _render(card, tmp_path)
    legs = {s["name"]: s for s in card["scenarios"]}
    order = [c for c in ("bear", "base", "bull") if c in legs]
    claims = next(f["value"] for f in card["facts"] if f["key"] == "net_debt")
    expect = {
        "NTM EBIT at exit ($M)": [_js_thousands(legs[n]["ebit"]) for n in order],
        "EV ($M)": [_js_thousands(legs[n]["ev"]) for n in order],
        "less TEV claims ($M)": [_js_thousands(claims)] * len(order),
        "Equity ($M)": [_js_thousands(legs[n]["equity"]) for n in order],
    }
    for label, want in expect.items():
        assert _row_cells(html, label) == want, label
    assert "How each axis was modeled — NTM EBIT and multiple methodology" in html
    assert "Cross-checks — per leg" not in html, (
        "on R4 the leg's EV/EBIT IS its input multiple — a cross-check would verify it against "
        "itself")


def test_the_r4_card_prints_no_undefined_collapsed_or_force_opened(
    r4: dict[str, Any], tmp_path: pathlib.Path,
) -> None:
    """THE PREVIEW RULE'S PRINT TIER (#176): every <details> force-opens in the PDF, so the
    collapsed tiers' content is checked too, not only the visible one."""
    html = _render(_BUILD._scenario_card(r4), tmp_path)
    opened = re.sub(r"<details(?![^>]*\bopen\b)", "<details open", html)
    assert html.count("<details") >= 3
    for state in (html, opened):
        assert not re.search(r"undefined|NaN", state)


def test_no_committed_card_grows_an_r4_row(tmp_path: pathlib.Path) -> None:
    """NEGATIVE PIN — the rows key on the record carrying `ebit`. Every committed card (R1, R2,
    R3) renders none of them (measured byte-identical to main on all 13 before this shipped)."""
    cards = sorted((ROOT / "frontend" / "scenarios").glob("*.json"))
    cards = [p for p in cards if p.name != "index.json"]
    if not cards:
        pytest.skip("frontend/scenarios is unbuilt in this checkout")
    for p in cards:
        html = _render(json.loads(p.read_text()), tmp_path)
        assert not any(f">{r}<" in html for r in R4_ROWS), p.name


# --- the markdown twin --------------------------------------------------------------------------

def test_the_markdown_twin_prints_the_cards_numbers(
    r4: dict[str, Any], tmp_path: pathlib.Path,
) -> None:
    """md/web PARITY: the same four figures per leg, digit for digit. The first cut formatted the
    raw value in Python (.5 to even) against the card's rounded-then-Math.round (.5 up) and split
    the twins by $1M on the bull leg."""
    rec = sc.ScenarioRecord.model_validate(r4)
    lines = _scenario_table_lines(rec)
    head = next(ln for ln in lines if ln.startswith("| scenario |"))
    assert "NTM EBIT at exit $M" in head and "less TEV claims $M" in head
    cols = [c.strip() for c in head.strip("|").split("|")]
    html = _render(_BUILD._scenario_card(r4), tmp_path)
    for label, col in (("NTM EBIT at exit ($M)", "NTM EBIT at exit $M"), ("EV ($M)", "EV $M"),
                       ("less TEV claims ($M)", "less TEV claims $M"),
                       ("Equity ($M)", "equity $M")):
        md = [[c.strip() for c in ln.strip("|").split("|")][cols.index(col)]
              for ln in lines if ln.startswith(("| bear |", "| base |", "| bull |"))]
        assert md == _row_cells(html, label), label


def test_the_methodology_heading_names_the_quantity(r4: dict[str, Any]) -> None:
    rec = sc.ScenarioRecord.model_validate(r4)
    heads = [ln for ln in _assumption_methodology_lines(rec) if ln.startswith("### ")]
    assert any(h.startswith("### NTM EBIT at exit") for h in heads), heads
    assert not any(h.startswith("### Ebit") for h in heads)


def test_an_r3_table_and_heading_keep_their_shape() -> None:
    """NEGATIVE PIN — GOOGL's committed R3 record: no EBIT or bridge column, `### Earnings`."""
    rec = sc.ScenarioRecord.model_validate_json((ROOT / "scenarios" / "GOOGL.json").read_text())
    head = next(ln for ln in _scenario_table_lines(rec) if ln.startswith("| scenario |"))
    assert "EBIT" not in head and "claims" not in head
    assert any(ln.startswith("### Earnings") for ln in _assumption_methodology_lines(rec))


def test_card_thousands_rounds_the_way_the_card_does() -> None:
    """CONSTRUCTED — the two cases where Python's own format and the card's disagree."""
    assert f"{2.5:,.0f}" == "2" and _card_thousands(2.5, None) == "3"
    assert _card_thousands(5_181_375.46, 1) == "5,181,376"     # round to 1dp first, then .5 up
    assert _card_thousands(-2.5, None) == "-2"                   # Math.round(-2.5) is -2
    assert _card_thousands(None, 1) == "—"
