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
    """Every committed anchor with a base and a USED count: it divides the page's own point-in-time
    count, and the dilution test divides the SAME equity by that count plus the increment. (A
    refused count is the next section's.)"""
    seen = 0
    for p in _PAGES:
        d = json.loads(p.read_text())
        a = d.get("anchor") or {}
        base = a.get("anchor_base_value_per_share")
        so = (a.get("shares_outstanding") or {}).get("value")
        if base is None or so is None:
            continue
        seen += 1
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
    test sits on its own row. And the web twin of the refusal row, on LLY's."""
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
const out = {{}};
for (const t of ["TJX", "LLY"]) {{
  const d = JSON.parse(readFileSync(`frontend/dossiers/${{t}}.json`));
  const cp = `frontend/scenarios/${{t}}.json`;
  const h = renderDossier(d, null, existsSync(cp) ? JSON.parse(readFileSync(cp)) : null);
  out[t] = {{ count: h.includes("shares outstanding"), test: h.includes("Dilution test / share"),
             refused: h.includes("Point-in-time count") && h.includes("employee benefit trust") }};
}}
console.log(JSON.stringify(out));
"""
    res = json.loads(subprocess.run(["node", "--input-type=module", "-e", driver],
                                    capture_output=True, text=True, check=True).stdout)
    assert res["TJX"] == {"count": True, "test": True, "refused": False}, res
    # LLY's count is refused: the web twin states it, and strikes no dilution test
    assert res["LLY"]["refused"] is True and res["LLY"]["test"] is False, res


# --- the count is USED only where the filer's own basic weighted average corroborates it ---------
# Real shapes, measured 2026-10-21 on main 4b514dca's committed pages and the EDGAR cache that day:
# LLY's cover count carries the 50,000,000 shares its employee benefit trust holds (EDGAR
# CommonStockSharesHeldInEmployeeTrustShares, FY2025 10-K), which its EPS does not count; IT's sits
# 5.0% BELOW its average after $1,082M repurchased in the half.

_Q2 = ("2026-04-01", "2026-06-30")


def _mech(count: float) -> dict[str, Any]:
    return {"stock_info": {"shares_out": {"value": count, "status": "present",
                                          "source_ref": "EDGAR XBRL shares outstanding"}}}


def _count(count: float, diluted: int, basic: int) -> tuple[float | None, str]:
    facts = _shares([(*_Q2, diluted)], [(*_Q2, basic)])
    return an._shares_outstanding(_mech(count), facts, an._latest_point(facts, an._DILUTED_TAG))


def test_a_count_the_filers_eps_does_not_recognise_is_refused() -> None:
    """THE RED (LLY, as filed): 941,357,065 on the cover against 892,400,000 basic — +5.5%. Divided
    by, it put Lilly's base at $664.23 against $699.65 on the diluted average: a 5% cut made of
    trust shares. Refused, and the refusal names the figure, the gap and the period."""
    out, why = _count(941_357_065, 893_700_000, 892_400_000)
    assert out is None
    assert why.startswith(an.SHARES_REFUSED)
    assert "941,357,065" in why and "5.5% above" in why and "2026-04-01..2026-06-30" in why


def test_a_buyback_below_the_average_is_the_count_used() -> None:
    """NEGATIVE (IT, as filed): 63,148,976 against 66,501,000 basic — −5.0%, the buyback the
    weighted average lags. Used, with the check stated beside it."""
    out, why = _count(63_148_976, 66_581_000, 66_501_000)
    assert out == 63_148_976
    assert "5.0% below the filer's basic weighted average 66,501,000" in why


def test_the_margins_are_the_boundaries() -> None:
    """Either side of each margin (+2%, −10%): just inside is used, just past is refused."""
    assert _count(101.9e6, 100.0e6, 100.0e6)[0] == 101.9e6
    assert _count(102.1e6, 100.0e6, 100.0e6)[0] is None
    assert _count(90.1e6, 100.0e6, 100.0e6)[0] == 90.1e6
    assert _count(89.9e6, 100.0e6, 100.0e6)[0] is None


def test_no_weighted_average_no_count_no_base() -> None:
    """NEGATIVE (V's shape): a count with no filer weighted average to check it against — V's is
    CIQ's comps figure, on the page whose share basis already fails (STATE row 32 (12)). Refused,
    so the anchor stays as main had it rather than gaining a base on an unchecked count."""
    out, why = an._shares_outstanding(_mech(1_835_600_000), {"facts": {}}, None)
    assert out is None and "cannot be checked" in why


def test_a_refused_count_leaves_the_base_on_the_diluted_average_e2e() -> None:
    """On every committed anchor whose count was refused: the base divides the diluted weighted
    average (`per_share_shares`), no dilution test is struck, and both renderers state the refusal.
    LLY and PARR are the two the 2026-10-21 pass refuses."""
    from vinci.dossier import render as dr
    from vinci.dossier import schemas as ds
    from vinci.dossier.assemble import _read_scenario_card

    refused = []
    for p in _PAGES:
        d = json.loads(p.read_text())
        a = d.get("anchor") or {}
        so = a.get("shares_outstanding") or {}
        if a.get("anchor_base_value_per_share") is None or so.get("value") is not None:
            continue
        if not str(so.get("source", "")).startswith(an.SHARES_REFUSED):
            continue
        refused.append(p.parent.name)
        assert an.per_share_shares(a) == a["diluted_shares"]["value"], p.parent.name
        assert a.get("anchor_base_value_per_share_diluted") is None, p.parent.name
        doc = ds.Dossier.model_validate_json(p.read_text())
        md = dr.render_markdown(doc, card=_read_scenario_card(doc.ticker))
        assert "| Point-in-time count | refused |" in md, p.parent.name
        assert "· on the diluted weighted average" in md, p.parent.name
    assert {"LLY", "PARR"} <= set(refused), refused


def test_lillys_real_page_refuses_its_count_and_keeps_its_equity() -> None:
    """THE COMPUTE, on LLY's committed mechanical layer and its frozen companyfacts (the artifact
    pins above cannot see a code change; this one can): the count is refused, no dilution test is
    struck, and the base divides the diluted weighted average — the SAME equity the page re-struck
    with a corroborated count (its basic average, 892,400,000) divides."""
    from datetime import UTC, datetime

    mech = json.loads(Path("data/dossiers/LLY/dossier.json").read_text())["mechanical"]
    facts = json.loads(Path("tests/fixtures/companyfacts/LLY.json").read_text())
    now = datetime.now(UTC)
    a = an.compute_anchor(mech, facts=facts, computed_at=now)
    assert a.shares_outstanding is not None and a.shares_outstanding.value is None
    assert a.shares_outstanding.source.startswith(an.SHARES_REFUSED)
    assert a.anchor_base_value_per_share is not None
    assert a.anchor_base_value_per_share_diluted is None
    assert a.diluted_shares is not None and a.diluted_shares.value == 893_700_000
    fixed = json.loads(json.dumps(mech))
    fixed["stock_info"]["shares_out"]["value"] = 892_400_000
    b = an.compute_anchor(fixed, facts=facts, computed_at=now)
    assert b.shares_outstanding is not None and b.shares_outstanding.value == 892_400_000
    assert b.anchor_base_value_per_share is not None
    assert a.anchor_base_value_per_share * 893_700_000 == pytest.approx(
        b.anchor_base_value_per_share * 892_400_000, rel=1e-6)
