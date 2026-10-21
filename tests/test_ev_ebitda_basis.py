"""What CIQ's headline EV/EBITDA divides, and R1's ex-lease multiple at the page's price.

THE DEFECT (a review of TJX's page, 2026-10-21). The page printed CIQ's TEV/LTM EBITDA, 13.3x, with
no basis; the reviewer divided CIQ's TEV ($170,372M) by reported LTM EBITDA ($8,903M), got 19.1x,
and called the headline wrong. It is not wrong — TEV WITH operating leases over EBITDA WITH rent
added back reproduces 13.3x to 0.7% — but the page never said so, and R1's own basis today (TEV
less operating leases over reported EBITDA, at the page's price: 17.8x) was nowhere on it; its only
"current" was 16.3x at a two-month-old quarterly close.

THE FLEET, measured before any pin (2026-10-21, main 4b514dca, 27 pages): 14 reproduce the
rent-inclusive pairing within 0.7%–4.9%, NFLX the reported one, BRBR/GOOGL/LLY/UBER/V cannot be told
apart (rent under 5% of EBITDA), AORT/IT/VITL/VRRM reproduce neither, four lack an input. A label
assumed fleet-wide would be wrong on a third of the pages, so each is measured.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from vinci.dossier import ev_ebitda_basis as eb
from vinci.dossier import render as dr
from vinci.dossier import schemas as ds
from vinci.dossier.assemble import _read_scenario_card

_PAGES = sorted(Path("data/dossiers").glob("*/dossier.json"))


def _doc(t: str) -> ds.Dossier:
    return ds.Dossier.model_validate_json(Path(f"data/dossiers/{t}/dossier.json").read_text())


def _with(m: ds.MechanicalLayer, *, rent: float | None = ..., multiple: float | None = None,
          ) -> ds.MechanicalLayer:
    """`m` with its rent or its headline multiple replaced — the REAL page, one field moved."""
    v = m.valuation
    if rent is not ...:
        assert v.lease_basis is not None
        v = v.model_copy(update={"lease_basis": v.lease_basis.model_copy(
            update={"rent_expense": rent})})
    if multiple is not None:
        v = v.model_copy(update={"ev_ebitda": v.ev_ebitda.model_copy(update={"value": multiple})})
    return m.model_copy(update={"valuation": v})


# --- the reading, on TJX's real page with one field moved at a time ----------------------------

def test_tjx_reproduces_the_rent_inclusive_pairing() -> None:
    """THE RED: 13.3x divides $12,810M, which is reported LTM EBITDA plus rent — and the line says
    it is NOT a multiple of reported EBITDA."""
    got = eb.headline_basis(_doc("TJX").mechanical)
    assert got is not None and got.reading == "ebitda_plus_rent", got
    assert got.ratio_to_reported_plus_rent is not None
    assert abs(got.ratio_to_reported_plus_rent - 1) <= eb.PAIRING_TOL
    assert abs(got.ratio_to_reported - 1) > eb.PAIRING_TOL
    assert "NOT a multiple of reported EBITDA" in got.line


@pytest.mark.parametrize(("rent", "multiple", "reading"), [
    # rent negligible: both pairings reproduce, and the line says the pairing changes nothing
    (10.0, 170372.2 / 8903.0, "indistinguishable"),
    # rent unmeasured and the multiple IS a multiple of reported EBITDA
    (None, 170372.2 / 8903.0, "reported"),
    # neither pairing: the multiple divides something else (AORT/IT/VITL/VRRM's shape)
    (3814.0, 9.0, "not_reproduced"),
])
def test_each_reading_is_measured_never_assumed(rent: float | None, multiple: float,
                                                reading: str) -> None:
    got = eb.headline_basis(_with(_doc("TJX").mechanical, rent=rent, multiple=multiple))
    assert got is not None and got.reading == reading, got


def test_no_snapshot_tev_no_reading() -> None:
    """NEGATIVE: without the comps TEV there is no denominator to test — absent, never a guess."""
    m = _doc("TJX").mechanical
    v = m.valuation
    assert v.implied_expectations is not None
    ie = v.implied_expectations.model_copy(update={"tev": ds.Sourced[float].unknown(note="x")})
    bare = m.model_copy(update={"valuation": v.model_copy(update={"implied_expectations": ie})})
    assert eb.headline_basis(bare) is None


# --- the ex-lease multiple at the page's price ---------------------------------------------------

def test_the_at_price_figure_is_its_own_arithmetic_e2e() -> None:
    """On every committed page that carries it: (price × shares + net debt) ÷ LTM EBITDA, from the
    block's own fields; the shares are the page's point-in-time count; the LTM EBITDA is the
    ex-lease history's latest; and the anchor's ex-lease net debt is the same figure."""
    seen = 0
    for p in _PAGES:
        d = json.loads(p.read_text())
        at = d["mechanical"]["valuation"].get("ev_ebitda_ex_lease_at_price")
        if not at:
            continue
        seen += 1
        assert at["value"] == pytest.approx(
            (at["price"] * at["shares"] / 1e6 + at["net_debt"]) / at["ltm_ebitda"], rel=1e-6)
        assert at["shares"] == d["mechanical"]["stock_info"]["shares_out"]["value"]
        obs = [o for o in d["mechanical"]["valuation"]["lease_basis"]["observations"]
               if o["multiple"] is not None]
        assert at["ltm_ebitda"] == pytest.approx(obs[-1]["ltm_ebitda"])
        a = d.get("anchor") or {}
        if (a.get("net_debt") or {}).get("basis", "").startswith("net debt excluding"):
            assert at["net_debt"] == pytest.approx(a["net_debt"]["value"], abs=0.01), p
    assert seen >= 10, f"only {seen} pages carry the ex-lease figure — the pass did not land"


def test_an_immaterial_rent_page_carries_no_ex_lease_figure() -> None:
    """NEGATIVE: where rent is immaterial R1 prices CIQ's own history, so there is no ex-lease
    figure to strike — absent on the page, not a figure on a basis R1 does not use."""
    for t in ("LLY", "V", "GOOGL"):
        lb = _doc(t).mechanical.valuation.lease_basis
        if lb is not None and not lb.material:
            assert _doc(t).mechanical.valuation.ev_ebitda_ex_lease_at_price is None, t


def test_r1s_current_multiple_is_on_r1s_basis_e2e() -> None:
    """`valuation_basis.current_multiple` for R1 was always empty. On an ex-lease page it is the
    history's latest quarterly close AND the same basis at the page's price — the block's value,
    not CIQ's lease-inclusive headline."""
    d = json.loads(Path("data/dossiers/TJX/dossier.json").read_text())
    cm = d["valuation_basis"]["current_multiple"]
    at = d["mechanical"]["valuation"]["ev_ebitda_ex_lease_at_price"]
    band = d["mechanical"]["valuation"]["lease_basis"]["ex_lease_band"]
    assert cm["value"] == pytest.approx(band["current"]) and cm["as_of"] == band["as_of"]
    assert cm["value_at_page_price"] == pytest.approx(at["value"])
    assert cm["value_at_page_price"] != pytest.approx(d["mechanical"]["valuation"]["ev_ebitda"][
        "value"]), "R1's current multiple must not be CIQ's lease-inclusive headline"


# --- the page ----------------------------------------------------------------------------------

def test_the_brief_states_the_basis_where_it_matters_md_e2e() -> None:
    """Both directions, on every committed page: the line prints for the rent-inclusive and the
    unreproduced readings, and not for a multiple of reported EBITDA or an indistinguishable one;
    the ex-lease figure prints wherever the page carries it."""
    stated = quiet = 0
    for p in _PAGES:
        doc = ds.Dossier.model_validate_json(p.read_text())
        v = doc.mechanical.valuation
        brief = dr.render_markdown(doc, card=_read_scenario_card(doc.ticker)).split(
            "# Analysis — full dossier", 1)[0]
        b = v.ev_ebitda_basis
        if b is not None and b.reading in ("ebitda_plus_rent", "not_reproduced"):
            assert f"- **What CIQ's EV/EBITDA divides:** {b.line}" in brief, doc.ticker
            stated += 1
        else:
            assert "What CIQ's EV/EBITDA divides" not in brief, doc.ticker
            quiet += 1
        at = v.ev_ebitda_ex_lease_at_price
        assert (at is not None) == ("R1's basis (ex-lease EV/EBITDA) at the page's price"
                                    in brief), doc.ticker
    assert stated >= 10 and quiet >= 5, (stated, quiet)


def test_the_web_states_the_same_lines_e2e() -> None:
    """THE TWIN: dossier.js's valuation card prints the same two sentences on TJX, and neither on
    NFLX (a multiple of reported EBITDA)."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync, existsSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const out = {{}};
for (const t of ["TJX", "NFLX"]) {{
  const d = JSON.parse(readFileSync(`frontend/dossiers/${{t}}.json`));
  const cp = `frontend/scenarios/${{t}}.json`;
  const h = renderDossier(d, null, existsSync(cp) ? JSON.parse(readFileSync(cp)) : null);
  out[t] = {{ divides: h.includes("What CIQ&#39;s EV/EBITDA divides")
                      || h.includes("What CIQ's EV/EBITDA divides"),
             atPrice: h.includes("at the page&#39;s price") || h.includes("at the page's price") }};
}}
console.log(JSON.stringify(out));
"""
    res = json.loads(subprocess.run(["node", "--input-type=module", "-e", driver],
                                    capture_output=True, text=True, check=True).stdout)
    assert res["TJX"] == {"divides": True, "atPrice": True}, res
    assert res["NFLX"]["divides"] is False, res
