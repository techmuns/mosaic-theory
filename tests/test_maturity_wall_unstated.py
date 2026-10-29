"""A MATURITY-WALL TOTAL SUMS THE STATED PRINCIPALS ONLY (audit D-D4, 2026-10-29).

THE DEFECT. `render._maturity_wall_lines` and its JS twin summed `principal_musd or 0`, so an
instrument CIQ's capital-structure panel prints '-' for counted as $0 and a group of nothing but
those printed a literal "$0.0M". On the committed pages at c51c286a: 47 instruments with no
principal across 17 pages, and nine pages printing "$0.0M" as a wall total — SMPL's 2029 revolver
read "due 2029: $0.0M". 32 of the 47 are revolving credit or commercial paper by CIQ's type, where
'-' can be an undrawn line; the panel does not say so, so the wall must not either.

THE RULE. A total sums the principals the panel STATES and says how many it leaves out; a group
with none stated prints no dollar figure; one note names every instrument left out, with CIQ's
type beside it. A wall whose principals are all stated renders exactly as before.

THE PINS. Value pins read SMPL's FROZEN 2026-08-18 page (tests/fixtures/frozen_pages/), never the
living one; the end-to-end pins re-derive every committed page's wall from its own JSON, on both
renderers.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import render as dr
from vinci.dossier.render import render_markdown
from vinci.dossier.schemas import Dossier

ROOT = Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
FROZEN = ROOT / "tests" / "fixtures" / "frozen_pages" / "2026-08-18" / "SMPL" / "dossier.json"
_NOTE = "_no principal stated — the CIQ panel"         # the md note line's opening


def _wall(md: str) -> list[str]:
    lines = md.splitlines()
    k = next(i for i, ln in enumerate(lines) if ln.startswith("- **Maturity wall**"))
    out = []
    for ln in lines[k + 1:]:
        if not ln.startswith("  "):
            break
        out.append(ln)
    return out


def _frozen_wall() -> list[str]:
    doc = Dossier.model_validate_json(FROZEN.read_text())
    return _wall(render_markdown(doc))


def test_d4_neg_a_group_with_no_principal_stated_prints_no_zero() -> None:
    """(-) SMPL, frozen real page: the 2029 group is one revolving credit facility CIQ prints '-'
    for. Main printed "due 2029: $0.0M" and an itemized total silent about it."""
    wall = "\n".join(_frozen_wall())
    assert "due 2029: $0.0M" not in wall
    assert "  - due 2029: 1 with no principal stated" in wall
    assert "itemized $304.5M + 1 with no principal stated (panel A 2025 filed Oct-28-2025)" in wall
    note = next(ln for ln in _frozen_wall() if _NOTE in ln)
    assert "Credit Agreement With Barclays… (Revolving Credit)" in note
    assert "can mean an undrawn facility; the panel does not say which" in note


def test_d4_pos_stated_principals_render_as_before() -> None:
    """(+) The fence: a group whose principals are all stated is untouched (SMPL's 2030 term loan,
    its undated lease), and an all-stated wall carries no note at all (MVST's verified set)."""
    wall = _frozen_wall()
    assert "  - due 2030: $249.1M" in wall
    assert "  - undated (floor — no panel maturity): $55.4M — Operating Lease $55.4M" in wall
    from datetime import date

    from tests.test_dossier import _mvst_capital_structure
    mvst = "\n".join(dr._maturity_wall_lines(_mvst_capital_structure(), date(2026, 7, 3)))
    assert "no principal stated" not in mvst and "itemized $268.6M (panel" in mvst


def test_a_facility_note_is_only_for_a_facility() -> None:
    """(-) The undrawn-facility sentence follows CIQ's TYPE, never the name: AORT's left-out
    instruments are a term loan, a convertible note and a delayed-draw term loan — named, with no
    claim that '-' could mean undrawn."""
    gap = [i for i in _instruments(json.loads((DOSS / "AORT" / "dossier.json").read_text()))
           if i["principal_musd"] is None]
    if not gap or any(i["type"] in dr._FACILITY_TYPES for i in gap):
        pytest.skip("AORT's committed page no longer carries only non-facility gaps")
    doc = Dossier.model_validate_json((DOSS / "AORT" / "dossier.json").read_text())
    note = next(ln for ln in _wall(render_markdown(doc)) if _NOTE in ln)
    assert "undrawn" not in note and all(f"({i['type']})" in note for i in gap)


# --- end to end: every committed page's wall, re-derived from its own JSON ---------------------

def _instruments(d: dict[str, Any]) -> list[dict[str, Any]]:
    inst = ((d.get("mechanical") or {}).get("capital_structure") or {}).get("instruments") or {}
    return list(inst.get("value") or []) if inst.get("status") == "present" else []


def _expect(xs: list[dict[str, Any]]) -> str:
    stated = [i["principal_musd"] for i in xs if i["principal_musd"] is not None]
    gap = len(xs) - len(stated)
    total = f"${sum(stated):,.1f}M"
    if not gap:
        return total
    return f"{total} + {gap} with no principal stated" if stated else (
        f"{gap} with no principal stated")


def _by_year(d: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    ref = str(d["reference_date"])
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for i in _instruments(d):
        md = i.get("maturity_date")
        if md and md >= ref and md[:4] != ref[:4]:
            out[md[:4]].append(i)
    return out


def _pages() -> list[Path]:
    return sorted(p for p in DOSS.glob("*/dossier.json") if _instruments(json.loads(p.read_text())))


def test_every_committed_wall_totals_its_stated_principals_e2e() -> None:
    """(+/-) END TO END, committed JSON → render_markdown: every year group prints the stated
    principals' sum and the count it leaves out, the reconciliation does the same over the whole
    panel, and no year line reads "$0.0M" unless the panel STATES zero. Shown to bite: on main the
    nine pages above print "$0.0M" over unstated principals."""
    seen_gap = 0
    for p in _pages():
        d = json.loads(p.read_text())
        wall = _wall(render_markdown(Dossier.model_validate(d)))
        for yr, xs in _by_year(d).items():
            line = next(ln for ln in wall if ln.startswith(f"  - due {yr}: "))
            assert line == f"  - due {yr}: {_expect(xs)}", (p.parent.name, line)
            seen_gap += any(i["principal_musd"] is None for i in xs)
        rec = next(ln for ln in wall if "_reconciliation: itemized" in ln)
        assert f"itemized {_expect(_instruments(d))} (panel" in rec, (p.parent.name, rec)
        has_gap = any(i["principal_musd"] is None for i in _instruments(d))
        assert any(_NOTE in ln for ln in wall) is has_gap, p.parent.name
    assert seen_gap >= 5, f"only {seen_gap} committed year groups carry an unstated principal"


@pytest.mark.skipif(not shutil.which("node"), reason="node unavailable")
def test_the_web_wall_totals_its_stated_principals_e2e() -> None:
    """(+/-) The JS twin, END TO END on the committed web mirror: each year chip shows the stated
    sum (a dash when none is stated) and the count it leaves out, and the footnote names the gap."""
    dj = (ROOT / "frontend" / "views" / "shared" / "dossier.js").resolve().as_uri()
    pages = [ROOT / "frontend" / "dossiers" / f"{p.parent.name}.json" for p in _pages()]
    pages = [p for p in pages if p.exists()]
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const out = {{}};
for (const p of process.argv.slice(1)) {{
  const h = renderDossier(JSON.parse(readFileSync(p)), null, null);
  const w = h.slice(h.indexOf("Maturity wall · vs"));
  out[p] = w.slice(0, w.indexOf('class="wall-foot"') + 4000);
}}
process.stdout.write(JSON.stringify(out));
"""
    res = json.loads(subprocess.run(["node", "--input-type=module", "-e", driver,
                                     *map(str, pages)], capture_output=True, text=True,
                                    check=True, cwd=ROOT).stdout)
    seen_gap = 0
    for p in pages:
        h, d = res[str(p)], json.loads(p.read_text())
        for yr, xs in _by_year(d).items():
            stated = [i["principal_musd"] for i in xs if i["principal_musd"] is not None]
            gap = len(xs) - len(stated)
            amt = f"${sum(stated):,.1f}M" if stated else "—"
            more = (f"<span>{'+ ' if stated else ''}{gap} with no principal stated</span>"
                    if gap else "")
            chip = f'<div class="wall-yr"><span>{yr}</span><b>{amt}</b>{more}</div>'
            assert chip in h, (p.stem, yr, chip)
            seen_gap += bool(gap)
        foot = h[h.index('class="wall-foot"'):]
        has_gap = any(i["principal_musd"] is None for i in _instruments(d))
        assert ("no principal stated — the CIQ panel" in foot) is has_gap, p.stem
        assert re.search(r"itemized \$[\d,]+\.\dM", foot), p.stem
    assert seen_gap >= 5, f"only {seen_gap} committed year chips carry an unstated principal"
