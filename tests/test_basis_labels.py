"""Two labels an IC memo on TJX read as the figure's basis, when they were not (2026-10-21).

1. THE BRIEF'S FCF ROW. The Financial snapshot printed "FCF ($M)" — CIQ's LEVERED free cash flow —
   while the appendix two scrolls down said so; a brief-only reader takes it as CFO − capex. Both
   twins now print the appendix's label and its basis note under the snapshot.
2. THE FORECAST-ERROR SERIES. R4's evidence printed "FY2026 (US GAAP): actual 6957". "US GAAP" is
   CIQ's 'Acctg. Standard' — the filer's accounting STANDARD — and 6,957 is the actual CIQ set
   against its consensus; TJX's reported FY2026 EBIT is 7,178. Not a TJX quirk: 308 of 601
   year-observations differ from the page's own financial summary by >0.5% (23 of 25 pages,
   main 07665419).

Both pinned END TO END on every committed page (TEST-LAYER RULE): real JSON → render or evidence →
assertion. Invariants only — the label and the note, never a figure on a living page.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from vinci.dossier import ciq_sheets
from vinci.dossier import render as dr
from vinci.dossier import schemas as ds
from vinci.dossier.assemble import _read_scenario_card
from vinci.dossier.propose import r4_evidence

_PAGES = sorted(p for p in Path("data/dossiers").glob("*/dossier.json"))


def _has_fcf_row(doc: dict[str, object]) -> bool:
    fs = ((doc.get("mechanical") or {}).get("financial_summary") or {})  # type: ignore[union-attr]
    rows = (((fs or {}).get("annual") or {}).get("value") or {}).get("rows") or []
    return any(r.get("label") == "FCF ($M)" for r in rows)


def test_the_brief_names_its_fcf_levered_on_every_page_md_e2e() -> None:
    """Every committed page whose snapshot carries the FCF row: the BRIEF prints the levered label
    and the basis note, and never the bare "FCF ($M)". The appendix keeps the same label."""
    checked = 0
    for p in _PAGES:
        raw = json.loads(p.read_text())
        if not _has_fcf_row(raw):
            continue
        doc = ds.Dossier.model_validate(raw)
        md = dr.render_markdown(doc, card=_read_scenario_card(doc.ticker))
        brief = md.split("# Analysis — full dossier", 1)[0]
        snap = brief.split("**Financial snapshot**", 1)
        assert len(snap) == 2, f"{doc.ticker}: no Financial snapshot in the brief"
        assert "| FCF ($M) |" not in brief, f"{doc.ticker}: the brief still prints the bare row"
        assert f"| {dr._FCF_LEVERED_LABEL} |" in snap[1], f"{doc.ticker}: levered label missing"
        assert dr._FCF_LEVERED_NOTE in snap[1], f"{doc.ticker}: the basis note is missing"
        checked += 1
    assert checked >= 20, f"only {checked} pages carry an FCF row — the population shrank"


def test_the_web_snapshot_names_its_fcf_levered_e2e() -> None:
    """THE TWIN the memo actually read: dossier.js's financialSnapshot, every page with the row."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    names = [p.parent.name for p in _PAGES if _has_fcf_row(json.loads(p.read_text()))
             and Path(f"frontend/dossiers/{p.parent.name}.json").exists()]
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync, existsSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const out = {{}};
for (const t of {json.dumps(names)}) {{
  const d = JSON.parse(readFileSync(`frontend/dossiers/${{t}}.json`));
  const cp = `frontend/scenarios/${{t}}.json`;
  const h = renderDossier(d, null, existsSync(cp) ? JSON.parse(readFileSync(cp)) : null);
  const snap = (h.split(">Financial snapshot<")[1] || "").split('<div class="card')[0];
  out[t] = {{ snap: snap.length > 0, bare: snap.includes("FCF ($M)"),
             levered: snap.includes("<td>FCF (levered)</td>"),
             note: snap.includes("NOT CFO − capex") }};
}}
console.log(JSON.stringify(out));
"""
    res = json.loads(subprocess.run(["node", "--input-type=module", "-e", driver],
                                    capture_output=True, text=True, check=True).stdout)
    assert len(res) >= 20, f"only {len(res)} web pages checked"
    for t, r in res.items():
        assert r["snap"], f"{t}: no Financial snapshot card on the web"
        assert not r["bare"] and r["levered"] and r["note"], f"{t}: {r}"


def test_the_forecast_error_evidence_never_labels_an_actual_gaap_e2e() -> None:
    """Every committed page with an EBIT forecast-error series: no evidence line reads
    "(US GAAP): actual", and every year's line names the actual as CIQ's and the standard as the
    filer's."""
    checked = 0
    for p in _PAGES:
        doc = json.loads(p.read_text())
        series = (doc.get("historical_forecast_error") or {}).get("series") or []
        if not any(s.get("metric") == "EBIT" and s.get("observations") for s in series):
            continue
        lines = r4_evidence(doc)["ebit"]
        years = [ln for ln in lines if re.match(r"\s+FY\d{4}:", ln)]
        assert years, f"{p.parent.name}: the EBIT series reached no evidence line"
        assert not any(re.search(r"\((?:US GAAP|IFRS)\): actual", ln) for ln in lines), lines
        for ln in years:
            assert "CIQ's consensus-basis actual" in ln and "filer's accounting standard:" in ln, ln
        checked += 1
    assert checked >= 20, f"only {checked} pages carry an EBIT series — the population shrank"


def test_the_layer_says_its_actual_is_not_the_reported_line() -> None:
    """The stored note every page carries (and R4's evidence header prints): the actual is CIQ's,
    the basis field is a STANDARD. A deterministic constant, so the words are pinned."""
    note = ciq_sheets._FORECAST_ERROR_ELIGIBILITY
    assert "NOT the line the financial statements report" in note
    assert "accounting STANDARD" in note and "never the basis of that actual" in note
