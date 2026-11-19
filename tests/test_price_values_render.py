"""THE FAST VALUES ON THE PAGE (2026-11-19, operator: "Approve, $0 refresh") — both renderers.

The Snapshot prints the page's cap at its close, CIQ's beside it only where it disagrees beyond the
tolerance; the price-implied levels name the TEV at the close they divide and CIQ's own TEV the †
rows divide; the EV gap states both its TEV's dates. Each line is MAIN BODY on the web — present
with every `<details>` collapsed and with every one force-opened — and says what the markdown
says. A page built before the fields renders exactly as before, on both twins.

END TO END ON REAL PAGES (TEST-LAYER RULE): VRRM's page as #1121 committed it
(`tests/fixtures/frozen_pages/2026-11-18/VRRM/`, the rebuilt page whose CIQ cap is 31.9% off its
close) and the cut's MCK and FUBO, each taken through production's own builder
(`mechanical.with_price_values`) and production's renderers. EPAM's EV gap is the transform's on
the cut's page, its gap struck by the production transform.
"""
from __future__ import annotations

import copy
import json
import pathlib
import re
import shutil
import subprocess
import typing

import pytest

from tests.frozen_support import FROZEN_PAGES, frozen_doc
from vinci.dossier.mechanical import with_price_values
from vinci.dossier.render import render_markdown
from vinci.dossier.schemas import Dossier, MechanicalLayer

ROOT = pathlib.Path(__file__).resolve().parents[1]
JS = ROOT / "frontend" / "views" / "shared" / "dossier.js"
VRRM = FROZEN_PAGES / "2026-11-18" / "VRRM" / "dossier.json"


def _with_values(page: dict[str, typing.Any]) -> dict[str, typing.Any]:
    """The page with its fast values built by production's own builder (no comps workbook: the
    cross-sectional read is left as stored)."""
    out = copy.deepcopy(page)
    eb = out.get("ev_bridge") or {}
    if eb.get("ciq_tev_claims") is not None:
        # CIQ's TEV less its cap as the page's own export states it, as the refresh supplies it
        out["mechanical"]["stock_info"]["ciq_tev_claims"] = {
            "value": eb["ciq_tev_claims"], "status": "present", "note": None,
            "source_ref": eb.get("ciq_tev_claims_source") or "ev_bridge.ciq_tev_claims"}
    mech = with_price_values(MechanicalLayer.model_validate(out["mechanical"]), None)
    out["mechanical"] = json.loads(mech.model_dump_json())
    return out


def _vrrm() -> dict[str, typing.Any]:
    page: dict[str, typing.Any] = json.loads(VRRM.read_text())
    return page


def _md(page: dict[str, typing.Any]) -> str:
    return render_markdown(Dossier.model_validate(page))


def _node(tmp_path: pathlib.Path, pages: dict[str, dict[str, typing.Any]]) -> dict[str, str]:
    """Each page through the production `renderDossier`, one node process (`test_covenant_summary_
    label`'s driver)."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    jobs = []
    for name, page in pages.items():
        src, dst = tmp_path / f"{name}.json", tmp_path / f"{name}.html"
        src.write_text(json.dumps(page))
        jobs.append([str(src), str(dst)])
    (tmp_path / "jobs.json").write_text(json.dumps(jobs))
    driver = r"""
import { readFileSync, writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { renderDossier } = await import(pathToFileURL(process.argv[1]).href);
for (const [src, dst] of JSON.parse(readFileSync(process.argv[2]))) {
  writeFileSync(dst, renderDossier(JSON.parse(readFileSync(src)), null));
}
"""
    subprocess.run(["node", "--input-type=module", "-e", driver, str(JS),
                    str(tmp_path / "jobs.json")], capture_output=True, text=True, check=True)
    return {name: (tmp_path / f"{name}.html").read_text() for name in pages}


def _collapsed(html_text: str) -> str:
    """The page with every `<details>` removed, innermost first: what shows with all collapsed."""
    prev = None
    while prev != html_text:
        prev = html_text
        html_text = re.sub(r"<details\b[^>]*>(?:(?!<details\b).)*?</details>", "", html_text,
                           flags=re.S)
    return html_text


def _text(html_text: str) -> str:
    """The rendered text, a tag read as a space (a table cell's edge separates its words)."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_text))


VRRM_CAP_MD = "cap $252M (CIQ $333M at 2026-11-06, +31.9%)"
VRRM_TEV = ("TEV $1,190.6M at the 2026-11-17 close (CIQ claims as-of 2026-11-06; the † rows divide "
            "$1,271.2M, CIQ's cap plus its net debt, as-of 2026-11-06)")


def test_the_snapshot_prints_the_cap_at_the_close_and_ciqs_beyond_tolerance_e2e(
        tmp_path: pathlib.Path) -> None:
    """VRRM: $1.66 × 152.0M = $252M at the close; CIQ's $333M of 2026-11-06 is +31.9%, beyond the
    2% tolerance, so it prints beside it — and the old "⚠ implies $2.19/sh vs CMP" line does not."""
    page = _with_values(_vrrm())
    md = _md(page)
    (snap,) = [ln for ln in md.splitlines() if ln.startswith("- **Snapshot:**")]
    assert VRRM_CAP_MD in snap and "implies $2.19/sh" not in snap
    web = _node(tmp_path, {"VRRM": page})["VRRM"]
    for tier in (web, _collapsed(web)):
        assert "Market cap $252M (CIQ $333M at 2026-11-06, +31.9%)" in _text(tier)


def test_a_cap_inside_the_tolerance_prints_no_ciq_figure_e2e(tmp_path: pathlib.Path) -> None:
    """MCK, both on 2026-11-04, +1.0%: the page's $123.5B alone — the noise floor is not news."""
    page = _with_values(frozen_doc("MCK"))
    (snap,) = [ln for ln in _md(page).splitlines() if ln.startswith("- **Snapshot:**")]
    assert "cap $123.5B ·" in snap and "CIQ" not in snap
    web = _text(_collapsed(_node(tmp_path, {"MCK": page})["MCK"]))
    assert re.search(r"Market cap \$123\.5B 52-wk", web), web[web.find("Market cap"):][:80]


def test_a_share_basis_change_prints_the_mismatch_on_both_twins_e2e(
        tmp_path: pathlib.Path) -> None:
    """FUBO handed EDGAR's pre-split count (ratio 12.0): the Snapshot names the mismatch and CIQ's
    figure — a page the build refuses, printed honestly where an artifact predates the guard."""
    page = copy.deepcopy(frozen_doc("FUBO"))
    page["mechanical"]["stock_info"]["shares_out"]["value"] = 342.4e6
    page = _with_values(page)
    (snap,) = [ln for ln in _md(page).splitlines() if ln.startswith("- **Snapshot:**")]
    assert "⚠ SHARE-BASIS MISMATCH vs CIQ $293M (2026-08-11)" in snap
    web = _text(_collapsed(_node(tmp_path, {"FUBO": page})["FUBO"]))
    assert "SHARE-BASIS MISMATCH vs CIQ $293M (2026-08-11)" in web


def test_the_price_implied_levels_name_both_teves_on_both_twins_e2e(
        tmp_path: pathlib.Path) -> None:
    """The peer rows divide the TEV at the close, the † rows CIQ's own; the table cites the
    first."""
    page = _with_values(_vrrm())
    md = _md(page)
    assert f"  - _{VRRM_TEV} · multiples as-of " in md
    web = _node(tmp_path, {"VRRM": page})["VRRM"]
    for tier in (web, _collapsed(web)):
        assert VRRM_TEV in _text(tier)


def test_the_ev_gap_states_both_its_tev_dates_e2e(tmp_path: pathlib.Path) -> None:
    """EPAM's cut page through the production transform (its scenario record's base leg): the
    gap's TEV is struck at the 2026-11-11 close on CIQ's claims of 2026-11-06 — both dates on the
    markdown and in both web tiers."""
    from vinci.dossier.refresh import ev_gap_transform

    page = copy.deepcopy(frozen_doc("EPAM"))
    mech = ev_gap_transform("EPAM")(_with_values(page)["mechanical"])
    assert (mech.get("ev_gap") or {}).get("status") == "computed", "fixture precondition"
    page["mechanical"] = mech
    line = "TEV at the 2026-11-11 close, CIQ claims as-of 2026-11-06 · form"
    assert line in _md(page)
    web = _node(tmp_path, {"EPAM": page})["EPAM"]
    for tier in (web, _collapsed(web)):
        assert line in _text(tier)


@pytest.mark.parametrize("which", ["md", "web"])
def test_a_page_built_before_the_fields_renders_as_before(which: str,
                                                          tmp_path: pathlib.Path) -> None:
    """NEGATIVE: VRRM as committed (no fast values) keeps CIQ's cap, its date and the old drift
    line, the plain "TEV as-of" header — the render moves only with the data."""
    page = _vrrm()
    assert "market_cap_at_close" not in page["mechanical"]["stock_info"], "fixture precondition"
    if which == "md":
        md = _md(page)
        assert "cap $333M (2026-11-06) ⚠ implies $2.19/sh vs CMP (+31.9%)" in md
        assert "  - _TEV as-of 2026-11-06 · multiples as-of" in md
        assert "close, CIQ claims as-of" not in md
    else:
        web = _text(_node(tmp_path, {"VRRM": page})["VRRM"])
        assert "Market cap $333M (2026-11-06)" in web
        assert "TEV as-of 2026-11-06 · multiples as-of" in web and "CIQ claims as-of" not in web


def test_the_tev_the_identity_rows_divide_is_named_for_what_it_is_e2e(
        tmp_path: pathlib.Path) -> None:
    """(round 1 of #1132) On MCK the † rows divide $129,319.4M — CIQ's cap plus its 'Net Debt'
    line — while CIQ's Total Enterprise Value is $132,257.4M; so the line names that figure as cap
    plus net debt, never "CIQ's own TEV", on both twins."""
    page = _with_values(frozen_doc("MCK"))
    want = "the † rows divide $129,319.4M, CIQ's cap plus its net debt, as-of 2026-11-04"
    md = _md(page)
    assert want in md and "CIQ's own TEV" not in md
    web = _node(tmp_path, {"MCK": page})["MCK"]
    for tier in (web, _collapsed(web)):
        assert want in _text(tier) and "CIQ's own TEV" not in _text(tier)
