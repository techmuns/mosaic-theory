"""THE FAST VALUES AT THE PAGE'S OWN CLOSE (2026-11-19, `vinci.dossier.price_values`).

The page's market cap is its close × its point-in-time share count, its TEV that cap plus CIQ's
claims, and CIQ's own cap and TEV stay beside them as DATED cross-checks that flag, never supply.
Every pin reads a REAL page: the frozen cut (`tests/frozen_support.py`) or the 2026-11-18 VRRM
copy, the rebuilt page whose Snapshot read "cap $333M (2026-11-06) ⚠ implies $2.19/sh vs CMP
(+31.9%)" beside a $1.66 close. Each guard has a negative pin beside its positive one.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from tests.frozen_support import FROZEN_PAGES, frozen_doc
from vinci.dossier import ciq_sheets, freshness, price_values
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.ev_gap import build_ev_gap
from vinci.dossier.mechanical import with_price_values
from vinci.dossier.schemas import MechanicalLayer

ROOT = Path(__file__).resolve().parents[1]
#: VRRM rebuilt 2026-11-18 at its 2026-11-17 close (the cut's VRRM predates the rebuild)
VRRM = FROZEN_PAGES / "2026-11-18" / "VRRM" / "dossier.json"


def _with_claims(doc: dict[str, Any]) -> dict[str, Any]:
    """The page's layer with CIQ's TEV less its cap as the page's OWN export states it
    (`ev_bridge.ciq_tev_claims`, read off the export the page was built from) — what the refresh
    supplies to a page built before `stock_info.ciq_tev_claims` existed."""
    mech: dict[str, Any] = copy.deepcopy(doc["mechanical"])
    eb = doc.get("ev_bridge") or {}
    if eb.get("ciq_tev_claims") is not None:
        mech["stock_info"]["ciq_tev_claims"] = {
            "value": eb["ciq_tev_claims"], "status": "present", "note": None,
            "source_ref": eb.get("ciq_tev_claims_source") or "ev_bridge.ciq_tev_claims"}
    return mech


def _vrrm() -> dict[str, Any]:
    return _with_claims(json.loads(VRRM.read_text()))


def test_the_pages_cap_is_its_close_times_its_count_and_ciqs_is_the_flagged_cross_check() -> None:
    """VRRM, the audit's case: $1.66 × 152,009,343 = $252.3M at 2026-11-17, against CIQ's $332.9M
    at 2026-11-06 — CIQ's cap implies $2.19/sh, +31.9%: drift, FLAGGED, not a corporate action."""
    mech = _vrrm()
    si = mech["stock_info"]
    assert (si["price"]["value"], si["as_of"], si["shares_out"]["value"]) == (
        1.66, "2026-11-17", 152009343.0), "fixture precondition"
    cap = price_values.cap_at_close(si)
    assert cap.value == pytest.approx(252.336, abs=1e-3)
    assert "2026-11-17" in (cap.source_ref or "") and "EDGAR XBRL shares" in (cap.source_ref or "")
    cc = price_values.cross_check(si)
    assert cc is not None
    assert (cc.ciq_market_cap, round(cc.implied_price, 2), round(cc.gap, 3)) == (332.9, 2.19, 0.319)
    assert cc.beyond_tolerance and not cc.corporate_action
    flag = price_values.cross_check_flag("VRRM", si)
    assert flag is not None and "2026-11-06" in flag and "2026-11-17" in flag and "+31.9%" in flag
    # the TEV at the close: that cap + CIQ's claims (its TEV less its cap, the name row's net debt)
    tev = price_values.tev_at_close(mech)
    assert tev.value == pytest.approx(252.336 + 938.3, abs=1e-3)
    assert price_values.ciq_tev(mech) == pytest.approx(1271.2)


def test_a_same_date_page_sits_on_the_noise_floor_and_is_not_flagged() -> None:
    """MCK, both figures on 2026-11-04: CIQ $124,686.4M against the page's $123,474.0M — +1.0%,
    the two share counts, inside the 2% tolerance. The negative of the flag above."""
    si = frozen_doc("MCK")["mechanical"]["stock_info"]
    assert si["as_of"] == si["market_cap_as_of"] == "2026-11-04", "fixture precondition"
    cc = price_values.cross_check(si)
    assert cc is not None and cc.gap == pytest.approx(0.0098, abs=1e-4)
    assert not cc.beyond_tolerance and not cc.corporate_action
    assert price_values.cross_check_flag("MCK", si) is None


def test_a_share_basis_change_is_still_told_apart_and_refused() -> None:
    """FUBO. Its cut page counts CIQ's post-split 30.2M shares: drift (1.06×), flagged, built.
    Handed EDGAR's PRE-split 342.4M — the count the 11.13× of 2026-07-29 was struck on — the page's
    own cap would be $3,516M, and the cross-check reads a whole-number ratio: a corporate action,
    which the build refuses. The page's cap is never compared with itself."""
    si = frozen_doc("FUBO")["mechanical"]["stock_info"]
    as_built = price_values.cross_check(si)
    assert as_built is not None and not as_built.corporate_action and as_built.beyond_tolerance
    pre_split = copy.deepcopy(si)
    pre_split["shares_out"]["value"] = 342.4e6
    assert price_values.cap_at_close(pre_split).value == pytest.approx(10.27 * 342.4, rel=1e-6)
    cc = price_values.cross_check(pre_split)
    assert cc is not None and cc.corporate_action and round(cc.ratio) == 12
    recon = freshness.reconcile_cap(cap_musd=si["market_cap"]["value"], shares=342.4e6,
                                    spot=si["price"]["value"])
    with pytest.raises(freshness.FreshnessError, match="share basis"):
        freshness.check_freshness(freshness.EventVerdict(()), recon, ticker="FUBO")
    # the recorded 2026-07-29 inputs: CIQ's post-split $256.4M against an $8.33 close
    old = freshness.reconcile_cap(cap_musd=256.4, shares=342.4e6, spot=8.33)
    assert old is not None and old.corporate_action and round(old.ratio, 2) == 11.12


def test_absent_claims_or_count_leave_the_value_unknown_and_never_impute() -> None:
    """NEGATIVE PINS: no claims (the name row's net debt gone) is no TEV at the close — not CIQ's
    TEV, not zero claims — and no count is no cap. The EV gap then states why it is not computed."""
    mech = _vrrm()
    no_claims = copy.deepcopy(mech)
    no_claims["stock_info"].pop("ciq_tev_claims")
    tev = price_values.tev_at_close(no_claims)
    assert tev.value is None and "TEV less market cap" in (tev.note or "")
    assert "imputed" in (tev.note or "")
    no_count = copy.deepcopy(mech)
    no_count["stock_info"]["shares_out"] = {"value": None, "status": "unknown", "note": "none",
                                            "source_ref": None}
    cap = price_values.cap_at_close(no_count["stock_info"])
    assert cap.value is None and "share count" in (cap.note or "")
    assert price_values.tev_at_close(no_count).value is None
    gap = build_ev_gap(None, {"revenue": 1.0, "margin": 0.1, "margin_basis": "ebitda",
                              "multiple": 8.0, "multiple_basis": "EV/EBITDA", "shares": 1.0},
                       tev=None, net_debt=938.3, shares=1.0, tev_as_of="2026-11-06",
                       consensus_as_of=None, tev_close_date="2026-11-17",
                       tev_absent=tev.note)
    assert gap["status"] == "not-computed" and "TEV less market cap" in str(gap["reason"])


def test_the_peer_rows_divide_the_tev_at_the_close_and_the_identity_rows_ciqs() -> None:
    """The price-implied PEER rows are the TEV at the page's close over the peer multiple; the
    name's own forward-multiple rows keep CIQ's TEV, whose multiple was struck at it, and so does
    `implied_expectations.tev` — CIQ's own, the dated cross-check."""
    built = with_price_values(MechanicalLayer.model_validate(_vrrm()), None)
    ie = built.valuation.implied_expectations
    assert ie is not None and ie.tev.value == pytest.approx(1271.2)
    assert ie.tev_at_close is not None and ie.tev_at_close.value == pytest.approx(1190.636)
    assert ie.tev_close_date == "2026-11-17"
    peers = [r for r in ie.rows if not r.is_identity and r.multiple and r.multiple > 0]
    names = [r for r in ie.rows if r.is_identity and r.multiple and r.multiple > 0]
    assert peers and names, "fixture precondition: both kinds of row"
    for r in peers:
        assert r.multiple is not None
        assert r.implied_level == pytest.approx(round(1190.636 / r.multiple, 1))
        assert "TEV at the page's close" in (r.source_ref or "")
    for r in names:
        assert r.multiple is not None
        assert r.implied_level == pytest.approx(round(1271.2 / r.multiple, 1))
    assert built.stock_info is not None and built.stock_info.market_cap.value == 332.9
    assert built.stock_info.market_cap_at_close is not None


def _rost_comps() -> CiqBundle:
    """ROST's own comps export (sha256 7171baef…), cut through the real decode path for the fix-3a
    pins (`tests/fixtures/ciq_comps_eval_panel.json`); it carries no Financial Data sheet."""
    raw = json.loads((ROOT / "tests/fixtures/ciq_comps_eval_panel.json").read_text())["names"]
    path = Path("/frozen/ROST-comps.xls")
    sheets = {k.split("|")[1]: copy.deepcopy(v) for k, v in raw["ROST"]["sheets"].items()}
    return CiqBundle(ticker="ROST", workbooks=(CiqWorkbook(kind="comps", path=path,
                                                          fmt=CiqFormat.BIFF_XLS, freq=None),),
                     _cache={path: sheets})


def test_the_names_cross_sectional_side_is_restated_at_its_close_the_peers_dated() -> None:
    """ROST's cut page (close $227.98, 2026-10-28; CIQ's panel 2026-09-25). The control first: the
    export rebuilds the committed read. Then EV/EBITDA 15.7x × (TEV at the close ÷ CIQ's TEV) =
    15.2x, CIQ's 15.7x and the peers' date beside it. Its P/E is UNKNOWN at the close here — this
    cut of the export carries no printed close — and never CIQ's 28.6x as today's."""
    page = _with_claims(frozen_doc("ROST"))
    bundle = _rost_comps()
    assert (ciq_sheets.cross_sectional_valuation(bundle).value
            == page["valuation"]["cross_sectional"]["value"]), "control: not ROST's export"
    built = with_price_values(MechanicalLayer.model_validate(page), bundle)
    text = built.valuation.cross_sectional.value or ""
    ratio = 73279.92 / 75880.3
    assert f"EV/EBITDA {15.7 * ratio:.1f}x at the 2026-10-28 close (CIQ 15.7x, 2026-09-25)" in text
    assert "vs peer median 7.0x (CIQ, 2026-09-25)" in text
    assert ("P/E UNKNOWN at the 2026-10-28 close — CIQ's comps panel prints no close to restate "
            "its P/E from (CIQ 28.6x, 2026-09-25)") in text
    assert built.valuation.cross_sectional.source_ref == page["valuation"]["cross_sectional"][
        "source_ref"], "the synthesis copies this ref verbatim — it must not move"


def test_the_pe_is_restated_by_the_close_over_ciqs_printed_close() -> None:
    """ROST's export prints a $236.12 close (read 2026-11-19 off the export the fixture is cut
    from): 28.6x × 227.98 / 236.12 = 27.6x at the page's close."""
    at = ciq_sheets.NameAtClose(tev_ratio=None, price_ratio=227.98 / 236.12,
                                price_as_of="2026-10-28", ciq_as_of="2026-09-25",
                                why=(("EV/EBITDA", "no TEV at the page's close"),))
    pe = ciq_sheets._name_at_close("P/E", 28.6, 13.8, at)
    assert pe == ("P/E 27.6x at the 2026-10-28 close (CIQ 28.6x, 2026-09-25) vs peer median "
                  "13.8x (CIQ, 2026-09-25) (+100%)")
    ev = ciq_sheets._name_at_close("EV/EBITDA", 15.7, 7.0, at)
    assert ev.startswith("EV/EBITDA UNKNOWN at the 2026-10-28 close — no TEV at the page's close")
    assert ciq_sheets._name_at_close("P/E", "NM", 13.8, at) == (
        "P/E NM vs peer median 13.8x (CIQ, 2026-09-25)")


def test_a_refresh_rederives_the_fast_values_and_leaves_a_page_without_them_alone() -> None:
    """`recompute_derived` re-strikes the fast values from the stored primitives where a page
    carries them, and adds nothing to a page built before them — the no-op round trip holds."""
    from vinci.dossier.refresh import recompute_derived

    old = _vrrm()
    assert "market_cap_at_close" not in old["stock_info"], "fixture precondition: built before"
    assert recompute_derived(old)["stock_info"] == old["stock_info"]
    new = json.loads(with_price_values(MechanicalLayer.model_validate(old), None)
                     .model_dump_json())
    moved = copy.deepcopy(new)
    moved["stock_info"]["price"]["value"] = 2.00
    again = recompute_derived(moved)
    assert again["stock_info"]["market_cap_at_close"]["value"] == pytest.approx(
        2.00 * 152009343.0 / 1e6, abs=1e-3)
    ie = again["valuation"]["implied_expectations"]
    assert ie["tev_at_close"]["value"] == pytest.approx(2.00 * 152.009343 + 938.3, abs=1e-3)
    assert ie["tev"]["value"] == pytest.approx(1271.2), "CIQ's own TEV does not follow the price"


# --- round 1 of #1132 -----------------------------------------------------------------------------


def _mck_comps() -> CiqBundle:
    """MCK's own comps export (sha256 158bc7e1…), its Financial Data header and name row cut through
    the real decode path (`tests/fixtures/ciq_comps_price_values.json`)."""
    raw = json.loads((ROOT / "tests/fixtures/ciq_comps_price_values.json").read_text())["names"]
    path = Path("/frozen/MCK-comps.xls")
    sheets = {k.split("|")[1]: copy.deepcopy(v) for k, v in raw["MCK"]["sheets"].items()}
    return CiqBundle(ticker="MCK", workbooks=(CiqWorkbook(kind="comps", path=path,
                                                          fmt=CiqFormat.BIFF_XLS, freq=None),),
                     _cache={path: sheets})


def test_the_claims_are_ciqs_tev_less_its_cap_never_the_net_debt_line() -> None:
    """(B, round 1) MCK: the comps 'Net Debt' line reads 4,633, CIQ's Total Enterprise Value less
    its Market Capitalization 7,571 — the claims the approved construction adds (the page's own
    `ev_bridge` agrees). The TEV at the close is $123,474.0M + 7,571 and CIQ's TEV its comps
    $132,257.4M. NEGATIVE: with no figure and no workbook the claims are UNKNOWN, never 4,633."""
    doc = frozen_doc("MCK")
    grid = doc["mechanical"]["peer_comps"]["peer_grid"]["value"]
    assert next(r for r in grid if r.get("is_name"))["net_debt"] == 4633.0, "precondition"
    assert doc["ev_bridge"]["ciq_tev_claims"] == 7571.0, "precondition: the page's own export"
    built = with_price_values(MechanicalLayer.model_validate(doc["mechanical"]), _mck_comps())
    assert built.stock_info is not None and built.stock_info.ciq_tev_claims is not None
    assert built.stock_info.ciq_tev_claims.value == 7571.0
    dumped = built.model_dump(mode="json")
    assert price_values.tev_at_close(dumped).value == pytest.approx(123473.975 + 7571.0)
    assert price_values.ciq_tev(dumped) == pytest.approx(132257.4)
    assert price_values.claims(doc["mechanical"]).value is None


def test_an_absent_input_note_reads_as_a_sentence() -> None:
    """(nit, round 1) The UNKNOWN cap names what is absent in plain words."""
    si = copy.deepcopy(_vrrm()["stock_info"])
    si["shares_out"] = {"value": None, "status": "unknown", "note": "none", "source_ref": None}
    assert "the page carries no share count;" in (price_values.cap_at_close(si).note or "")


def test_an_absent_ciq_tev_is_named_absent_not_non_positive() -> None:
    """(nit, round 1) ROST with CIQ's cap gone: its EV/EBITDA is UNKNOWN at the close because CIQ's
    TEV is ABSENT — the reason says so, not that it is non-positive."""
    page = _with_claims(frozen_doc("ROST"))
    page["implied_valuation"]["market_cap"] = {"value": None, "status": "unknown", "note": "x",
                                               "source_ref": None}
    built = with_price_values(MechanicalLayer.model_validate(page), _rost_comps())
    text = built.valuation.cross_sectional.value or ""
    assert "EV/EBITDA UNKNOWN at the 2026-10-28 close — CIQ's own TEV is absent" in text


def test_a_bundle_with_no_comps_workbook_leaves_the_cross_sectional_read_as_stored() -> None:
    """(round 1 of #1132, found writing this round's pins) A refresh where the export is not on
    disk opens an EMPTY bundle; reading it wrote the stored cross-sectional read over with MISSING
    ("export not found"). An empty bundle is no workbook: the read is left as stored."""
    page = _with_claims(frozen_doc("ROST"))
    empty = CiqBundle(ticker="ROST", workbooks=(), _cache={})
    built = with_price_values(MechanicalLayer.model_validate(page), empty)
    assert (built.valuation.cross_sectional.model_dump(mode="json")
            == page["valuation"]["cross_sectional"])
    assert built.stock_info is not None and built.stock_info.ciq_tev_claims is not None
