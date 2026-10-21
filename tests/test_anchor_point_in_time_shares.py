"""The anchor's value per share divides by the POINT-IN-TIME count; dilution is tested beside it.

THE DEFECT (a review of TJX's page, 2026-10-21). `anchor_base_value_per_share` was equity ÷ the
diluted WEIGHTED AVERAGE over the latest quarter (TJX 1.117B), while the page's own market cap,
the scenario template (`propose.resolve_shares`) and `valuation_basis.exit_share_count` all divide
by the point-in-time count (1,099,974,061) — item 24's denominator. A buyback name reads lower on
the average by the quarter's repurchase pace: TJX $129.10 against $131.10.

THE FIX keeps ONE equity and states both counts: the base on point-in-time shares, and a dilution
test on point-in-time shares PLUS the filer's own increment (diluted less basic weighted average
over the 10-Q's quarter — TJX 1,117,000,000 − 1,104,000,000 = 13,000,000 → $129.57).
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import anchor as an
from vinci.dossier import tagger
from vinci.edgar.concepts import points_for_tag

_PAGES = sorted(Path("data/dossiers").glob("*/dossier.json"))


def test_one_equity_two_counts_on_every_committed_anchor_e2e() -> None:
    """Every committed anchor with a base: it divides the page's own point-in-time count, and the
    dilution test divides the SAME equity by that count plus the increment."""
    seen = 0
    for p in _PAGES:
        d = json.loads(p.read_text())
        a = d.get("anchor") or {}
        base = a.get("anchor_base_value_per_share")
        if base is None:
            continue
        seen += 1
        so = (a.get("shares_outstanding") or {}).get("value")
        assert so == d["mechanical"]["stock_info"]["shares_out"]["value"], p.parent.name
        assert an.per_share_shares(a) == so
        dil, inc = a.get("anchor_base_value_per_share_diluted"), (
            a.get("dilutive_increment") or {}).get("value")
        if dil is not None:
            assert inc is not None and inc >= 0
            assert base * so == pytest.approx(dil * (so + inc), rel=1e-6), p.parent.name
    assert seen >= 10, f"only {seen} anchors carry a base"


def test_the_denominator_helper_reads_the_anchor_it_is_given() -> None:
    """POSITIVE: the point-in-time count when the anchor carries one. NEGATIVE: an anchor written
    before it carries only the weighted average — which is what ITS base was struck on."""
    assert an.per_share_shares({"shares_outstanding": {"value": 1.1e9},
                                "diluted_shares": {"value": 1.117e9}}) == 1.1e9
    assert an.per_share_shares({"diluted_shares": {"value": 1.117e9}}) == 1.117e9
    assert an.per_share_shares({}) is None


def test_the_leverage_read_rebuilds_the_anchors_own_equity() -> None:
    """`tagger._leverage` multiplies the base back by the count it was divided by — on the
    point-in-time count, the equity is the anchor's, not one 1.5% larger."""
    a = {"net_debt": {"value": -3133.0}, "anchor_base_value_per_share": 131.1019,
         "shares_outstanding": {"value": 1_099_974_061.0}, "diluted_shares": {"value": 1.117e9}}
    _r, why = tagger._leverage(a)
    assert f"{131.1019 * 1_099_974_061 / 1e6:,.0f}M" in why, why


def _row(s: str, e: str, v: int) -> dict[str, Any]:
    return {"start": s, "end": e, "val": v, "filed": "2026-08-28", "form": "10-Q", "accn": "x"}


def _shares(diluted: list[tuple[str, str, int]],
            basic: list[tuple[str, str, int]]) -> dict[str, Any]:
    row = _row
    return {"facts": {"us-gaap": {
        an._DILUTED_TAG: {"units": {"shares": [row(*x) for x in diluted]}},
        an._BASIC_TAG: {"units": {"shares": [row(*x) for x in basic]}}}}}


def test_the_increment_is_one_periods_difference_or_nothing() -> None:
    """TJX's Q2 FY27, as filed: diluted 1,117,000,000 less basic 1,104,000,000 over the SAME
    quarter.
    NEGATIVE: a basic figure only for the six months is a different span — it differs by the
    buyback pace, not by dilution — so no increment, never a mixed one."""
    q = ("2026-05-03", "2026-08-01")
    facts = _shares([(*q, 1_117_000_000)], [(*q, 1_104_000_000)])
    dil = an._latest_point(facts, an._DILUTED_TAG)
    got = an._dilutive_increment(facts, dil)
    assert got is not None and got[0] == 13_000_000.0
    other = _shares([(*q, 1_117_000_000)], [("2026-02-01", "2026-08-01", 1_106_000_000)])
    assert an._dilutive_increment(other, an._latest_point(other, an._DILUTED_TAG)) is None
    assert points_for_tag(other, an._BASIC_TAG)          # the fact exists; its span is wrong


def test_the_screen_rows_name_the_count_and_the_test_md_and_web_e2e() -> None:
    """Both twins, on TJX's committed page: the base names its point-in-time count and the dilution
    test sits on its own row."""
    from vinci.dossier import render as dr
    from vinci.dossier import schemas as ds
    from vinci.dossier.assemble import _read_scenario_card

    doc = ds.Dossier.model_validate_json(Path("data/dossiers/TJX/dossier.json").read_text())
    md = dr.render_markdown(doc, card=_read_scenario_card("TJX"))
    assert doc.anchor is not None and doc.anchor.shares_outstanding is not None
    assert f"on {doc.anchor.shares_outstanding.value:,.0f} shares outstanding" in md
    assert "| Dilution test / share |" in md
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync, existsSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const d = JSON.parse(readFileSync("frontend/dossiers/TJX.json"));
const cp = "frontend/scenarios/TJX.json";
const h = renderDossier(d, null, existsSync(cp) ? JSON.parse(readFileSync(cp)) : null);
console.log(JSON.stringify({{ count: h.includes("shares outstanding"),
                              test: h.includes("Dilution test / share") }}));
"""
    res = json.loads(subprocess.run(["node", "--input-type=module", "-e", driver],
                                    capture_output=True, text=True, check=True).stdout)
    assert res == {"count": True, "test": True}, res
