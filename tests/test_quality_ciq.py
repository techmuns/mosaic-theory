"""THE CIQ SOURCE of the data-quality scorecard (`vinci.quality.sources.ciq`) — pinned at two
layers.

* A FROZEN FIXTURE built from the REAL schema types (`EbitdaReconQuarter`, `LeaseObservation`,
  `EvBridge`, `ImpliedValuation`, `AnchorMidcycleGap`, …) with SYNTHETIC values — every status of
  every check, its boundary, and the guard that a CIQ figure never reaches the snapshot. No CIQ
  value is copied into this file (the repo is public).
* END TO END over the committed pages: phrasing-independent invariants only (the pages are living
  artifacts), plus the committed snapshot reproducing whenever the page set is the one it names.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci.cli import main
from vinci.dossier.anchor import BASIS_AGREE_PTS, AnchorMidcycleGap
from vinci.dossier.ciq import _WORKBOOK_KEYWORDS
from vinci.dossier.ciq_sheets import _NETTED_LABEL, EV_BRIDGE_CIQ_TOL
from vinci.dossier.lease_basis import _RENT_DISAGREE, rent_disagrees
from vinci.dossier.schemas import (
    CHECK_AGREE,
    CHECK_DIFFER,
    CHECK_NOT_RUN,
    ClaimLine,
    CrossCheck,
    EbitdaReconciliation,
    EbitdaReconQuarter,
    EvBridge,
    ImpliedExpectations,
    ImpliedValuation,
    LeaseBasis,
    LeaseObservation,
    OwnHistoryBand,
    PeerRow,
    PrimarySource,
    Sourced,
    StatementReconciliation,
    StatementReconRow,
)
from vinci.quality import core
from vinci.quality.sources import ciq

ROOT = Path(__file__).resolve().parents[1]
#: A CIQ-looking figure planted in every CIQ field of the fixture. It must never reach the snapshot.
SENTINEL = 7777.123


# --- the frozen fixture, from the real types ---------------------------------------------------


def _q(period: str, *, filing: float | None, different: bool = False,
       quote: str | None = None) -> dict[str, Any]:
    return EbitdaReconQuarter(
        period_end=period, ciq_ebitda=SENTINEL, filing_ebitda=filing,
        gap=(SENTINEL - filing) if filing is not None else None, different=different,
        matching_amount=quote,
        matching_source="8-K 0000000000-26-000001 EX-99.1" if quote else None,
        note=None if filing is not None else "no quarterly D&A tag for this quarter",
    ).model_dump(mode="json")


def _obs(day: str, status: str, edgar: float | None) -> dict[str, Any]:
    return LeaseObservation(
        balance_sheet_date=day, tev=SENTINEL, leases_in_tev=SENTINEL, finance_leases=0.0,
        operating_leases=SENTINEL, edgar_operating_leases=edgar, ltm_ebitda=SENTINEL,
        multiple=None, status=status).model_dump(mode="json")


def _lease(*, material: bool, rent: float | None, cost: float | None,
           obs: list[dict[str, Any]]) -> dict[str, Any]:
    return LeaseBasis(
        rent_expense=rent, rent_ebitda=SENTINEL, edgar_lease_cost=cost, threshold=0.05,
        material=material, materiality="synthetic", observations=[
            LeaseObservation.model_validate(o) for o in obs],
        source_ref="synthetic").model_dump(mode="json")


def _ev_bridge(claims: float, ciq: float | None) -> dict[str, Any]:
    return EvBridge(
        lines=[ClaimLine(label="Total Debt", sign=1, value=SENTINEL, source="synthetic")],
        claims=claims, net_debt=SENTINEL, ciq_tev_claims=ciq, rule="synthetic",
    ).model_dump(mode="json")


def _implied_valuation(cash: float | None, debt: float | None) -> dict[str, Any]:
    return ImpliedValuation(
        implied_equity=Sourced.unknown(note="synthetic"),
        bridge=Sourced.unknown(note="synthetic"), bridge_cash=cash, bridge_debt=debt,
        market_cap=Sourced.present(SENTINEL, source_ref="synthetic"),
        comparability_gate=Sourced.unknown(note="synthetic")).model_dump(mode="json")


def _gap(*, basis_gap: float | None, same_source: bool = False) -> dict[str, Any]:
    return AnchorMidcycleGap(
        ltm_margin=0.2, median_margin=0.1, median_years=10, gap_pts=10.0, ltm_side="above",
        basis_year=2025 if basis_gap is not None else None, basis_gap_pts=basis_gap,
        same_source=same_source, basis="synthetic", read="synthetic").model_dump(mode="json")


def _band(*, margins: bool, flag: str | None) -> dict[str, Any]:
    return OwnHistoryBand(
        metric="EV/EBITDA (TEV/LTM)", current=SENTINEL, low=SENTINEL, high=SENTINEL,
        median=SENTINEL, percentile=0.5, n_closes=20, data_quality=flag,
        implied_ebitda_margin=0.3 if margins else None,
        implied_ebit_margin=0.2 if margins else None,
        implied_d_and_a_margin=0.1 if margins else None).model_dump(mode="json")


def _ie(*, nd_reconciled: bool = True, nd_check: CrossCheck | None = None,
        vintage_coherent: bool = True, vintage: CrossCheck | None = None) -> dict[str, Any]:
    """The implied-expectations block, with its two flags and their stored outcomes."""
    return ImpliedExpectations(
        rows=[], tev=Sourced.present(SENTINEL, source_ref="synthetic"),
        anchors=Sourced.unknown(note="synthetic"), heterogeneity_gate="synthetic",
        tev_as_of="2026-10-01", multiples_as_of="2026-10-01", vintage_coherent=vintage_coherent,
        vintage_check=vintage, coherence_note="synthetic", net_debt_reconciled=nd_reconciled,
        net_debt_check=nd_check).model_dump(mode="json")


def _ps(*, guide: CrossCheck | None = None, wall: CrossCheck | None = None,
        near: bool | None = None, sign: CrossCheck | None = None) -> dict[str, Any]:
    """The primary-source block: three display lines, and beside each its stored outcome."""
    line = Sourced.present("synthetic", source_ref="synthetic")
    return PrimarySource(
        self_funding=line, self_funding_check=sign, wall_coherence=line,
        wall_coherence_check=wall, wall_coherence_near_boundary=near,
        basis_triangulation=line, guide_verification=line,
        guide_verification_check=guide).model_dump(mode="json")


_LINE_LABEL = {"revenue": "Revenue ($M)", "operating_cash_flow": "CFO ($M)"}


def _stmt(rows: list[tuple[str, str, float | None, bool, str | None, str | None]],
          ) -> dict[str, Any]:
    """An annual table and its statement block that AGREE — every CIQ figure the sentinel. A row:
    (line, column, filing, different, other_tag, earlier_accession)."""
    cols = list(dict.fromkeys(c for _ln, c, *_r in rows))
    have = {(ln, c) for ln, c, *_r in rows}
    table = {"columns": cols, "is_estimate": [False] * len(cols), "note": "synthetic",
             "rows": [{"label": lbl, "cells": [], "material": False,
                       "values": [SENTINEL if (ln, c) in have else None for c in cols]}
                      for ln, lbl in _LINE_LABEL.items()]}
    block = StatementReconciliation(rows=[StatementReconRow(
        line=ln, column=c, period_end="2025-12-31", ciq=SENTINEL, filing=f,
        gap=(SENTINEL - f) if f is not None else None, different=d, other_tag=o,
        earlier_accession=e) for ln, c, f, d, o, e in rows],
        as_filed_by="2026-10-23", source_ref="synthetic").model_dump(mode="json")
    return {"annual": {"value": table, "status": "present"}, "statement_reconciliation": block}


def _page(ticker: str, *, quarters: list[dict[str, Any]] | None = None,
          lease: dict[str, Any] | None = None, bridge: dict[str, Any] | None = None,
          ie: dict[str, Any] | None = None, iv: dict[str, Any] | None = None,
          cap: float | None = 1000.0, shares: float | None = 100e6, spot: float | None = 10.0,
          midcycle: dict[str, Any] | None = None,
          multiple: dict[str, Any] | None = None,
          band: dict[str, Any] | None = None,
          ps: dict[str, Any] | None = None,
          stmt: dict[str, Any] | None = None) -> dict[str, Any]:
    mech: dict[str, Any] = {
        "stock_info": {"market_cap": {"value": cap}, "shares_out": {"value": shares},
                       "price": {"value": spot}},
        "valuation": {"implied_expectations": _ie() if ie is None else ie},
    }
    if ps is not None:
        mech["primary_source"] = ps
    if quarters is not None:
        mech["financial_summary"] = {"ebitda_reconciliation": EbitdaReconciliation(
            quarters=[EbitdaReconQuarter.model_validate(q) for q in quarters],
            ciq_ltm=SENTINEL, any_different=any(q["different"] for q in quarters),
            line="synthetic", source_ref="synthetic").model_dump(mode="json")}
    if stmt is not None:
        mech.setdefault("financial_summary", {}).update(stmt)
    if lease is not None:
        mech["valuation"]["lease_basis"] = lease
    if iv is not None:
        mech["implied_valuation"] = iv
    if band is not None:
        mech["valuation"]["own_history"] = {"value": [band], "status": "present"}
    page: dict[str, Any] = {"ticker": ticker, "mechanical": mech}
    if bridge is not None:
        page["ev_bridge"] = bridge
    if midcycle is not None:
        page["anchor"] = {"midcycle_gap": midcycle}
    if multiple is not None:
        page["valuation_basis"] = {"current_multiple": multiple}
    return page


def _fixture() -> dict[str, dict[str, Any]]:
    """Three pages that between them put every check in every status it has."""
    return {
        "AAA": _page(
            "AAA",
            quarters=[_q("2026-03-31", filing=100.0), _q("2026-06-30", filing=90.0, different=True,
                                                          quote="a $10 million charge"),
                      _q("2026-09-30", filing=80.0, different=True),
                      _q("2025-12-31", filing=None)],
            lease=_lease(material=True, rent=100.0, cost=100.0 * _RENT_DISAGREE, obs=[
                _obs("2018-12-31", "pre-adoption", None),      # excluded: before ASC 842
                _obs("2019-03-31", "pre-adoption", 50.0),      # stated: a later comparative
                _obs("2019-06-30", "reconciled", 50.0),
                _obs("2019-09-30", "reconciled", 50.0),
                _obs("2019-12-31", "unreconciled", 50.0),
                _obs("2020-03-31", "unchecked", None)]),
            bridge=_ev_bridge(500.0, 500.0 + EV_BRIDGE_CIQ_TOL),
            iv=_implied_valuation(10.0, 20.0),
            ie=_ie(nd_check=CHECK_AGREE, vintage=CHECK_AGREE),
            midcycle=_gap(basis_gap=BASIS_AGREE_PTS - 0.01),
            multiple={"metric": "TEV/EBIT", "snapshot_reconciles": True},
            band=_band(margins=True, flag=None),
            ps=_ps(guide=CHECK_AGREE, wall=CHECK_AGREE, sign=CHECK_AGREE),
            stmt=_stmt([("revenue", "FY22", 100.0, True, None, None),           # unexplained
                        ("revenue", "FY23", 100.0, True, None, "0000000000-24-000001"),
                        ("revenue", "FY24", 100.0, True, "Revenues", None),      # both stated
                        ("revenue", "FY25", 100.0, False, None, None),           # confirmed
                        ("revenue", "LTM", None, False, None, None),             # unchecked
                        ("operating_cash_flow", "FY25", 50.0, False, None, None),
                        ("operating_cash_flow", "LTM", 50.0, False, None, None)])),
        "BBB": _page(
            "BBB",
            lease=_lease(material=False, rent=100.0, cost=100.0 * _RENT_DISAGREE + 1.0, obs=[]),
            bridge=_ev_bridge(500.0, 500.0 + EV_BRIDGE_CIQ_TOL + 0.1),
            iv=_implied_valuation(10.0, 20.0),
            ie=_ie(nd_reconciled=False, nd_check=CHECK_DIFFER, vintage_coherent=False,
                   vintage=CHECK_DIFFER),
            spot=20.0,                       # cap ÷ shares = $10/sh against a $20 close: a 2:1
            midcycle=_gap(basis_gap=BASIS_AGREE_PTS),
            multiple={"metric": "TEV/EBIT", "snapshot_reconciles": False},
            band=_band(margins=True, flag="periodicity_mismatch+band_incoherent"),
            ps=_ps(guide=CHECK_DIFFER, wall=CHECK_DIFFER, near=False, sign=CHECK_DIFFER)),
        "CCC": _page(
            "CCC",
            lease=_lease(material=True, rent=0.0, cost=50.0, obs=[]),
            bridge=_ev_bridge(500.0, None),
            iv=None,                         # both flags read True with NOTHING tested
            ie=_ie(nd_check=CHECK_NOT_RUN, vintage=CHECK_NOT_RUN),
            spot=None,
            midcycle=_gap(basis_gap=None, same_source=True),
            multiple={"metric": "Price/Earnings", "snapshot_reconciles": None},
            band=_band(margins=False, flag="periodicity_mismatch"),
            ps=_ps(guide=CHECK_NOT_RUN, wall=CHECK_NOT_RUN, sign=CHECK_NOT_RUN),
            # no revenue figure at all (a pre-revenue name); one OCF year differs, unexplained
            stmt=_stmt([("operating_cash_flow", "FY25", 50.0, True, None, None)])),
    }


def _card(pages: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    pages = _fixture() if pages is None else pages
    return core.scorecard(ciq.SOURCE, ciq.corpus(pages, "0" * 64), measured_on="2026-10-23",
                          git_head="abc1234", inputs_match_head=True)


def _check(card: dict[str, Any], cid: str) -> dict[str, Any]:
    return next(c for c in card["checks"] if c["id"] == cid)


def _row(card: dict[str, Any], cid: str, ticker: str) -> dict[str, Any]:
    row: dict[str, Any] = _check(card, cid)["by_name"][ticker]
    return row


def _counts(confirmed: int = 0, stated: int = 0, unexplained: int = 0,
            unchecked: int = 0) -> dict[str, int]:
    return {core.CONFIRMED: confirmed, core.DIFFERS_STATED: stated,
            core.DIFFERS_UNEXPLAINED: unexplained, core.UNCHECKED: unchecked}


# --- every status of every check, on the fixture -----------------------------------------------


def test_ebitda_statuses_follow_the_pages_own_flags() -> None:
    card = _card()
    assert _row(card, "ebitda_vs_xbrl", "AAA") == _counts(1, 1, 1, 1)
    assert _row(card, "ebitda_vs_xbrl", "BBB") == {"not_run": "no ebitda_reconciliation block on "
                                                              "the page — no quarterly CIQ export, "
                                                              "no EDGAR facts, or the export's "
                                                              "four latest columns are not four "
                                                              "consecutive quarters"}
    # a block with no quarters is not a page the check ran on
    empty = _page("EEE", quarters=[])
    assert "not_run" in _row(_card({"EEE": empty}), "ebitda_vs_xbrl", "EEE")


def test_statement_statuses_follow_the_rows_own_flags() -> None:
    card = _card()
    assert _row(card, "revenue_vs_xbrl", "AAA") == _counts(confirmed=1, stated=2, unexplained=1,
                                                           unchecked=1)
    assert _row(card, "ocf_vs_xbrl", "AAA") == _counts(confirmed=2)
    assert _row(card, "ocf_vs_xbrl", "CCC") == _counts(unexplained=1)
    assert _row(card, "revenue_vs_xbrl", "CCC") == {
        "not_applicable": "CIQ's annual table carries no figure for this line"}
    for cid in ("revenue_vs_xbrl", "ocf_vs_xbrl"):     # no block: never looked, not 'unchecked'
        assert set(_row(card, cid, "BBB")) == {"not_run"}


def test_a_statement_block_that_is_not_the_tables_is_not_scored() -> None:
    """A refresh that moved the table and left the block would score figures the page no longer
    shows — so the block is scored only while each of its CIQ figures IS the table's."""
    page = _fixture()["AAA"]
    page["mechanical"]["financial_summary"]["annual"]["value"]["rows"][0]["values"][0] += 1.0
    card = _card({"AAA": page})
    assert "stale" in _row(card, "revenue_vs_xbrl", "AAA")["not_run"]
    assert _row(card, "ocf_vs_xbrl", "AAA") == _counts(confirmed=2)    # the other line still is
    page = _fixture()["AAA"]
    page["mechanical"]["financial_summary"]["statement_reconciliation"]["rows"].pop(0)
    assert "stale" in _row(_card({"AAA": page}), "revenue_vs_xbrl", "AAA")["not_run"]


def test_lease_rows_statuses_and_the_pre_adoption_split() -> None:
    card = _card()
    # the comparative (EDGAR reports a lease, CIQ's original balance sheet does not) is a stated
    # difference; before the standard on BOTH sides it is excluded, never a confirmation
    assert _row(card, "lease_rows_vs_edgar", "AAA") == {**_counts(2, 1, 1, 1), "excluded": 1}
    assert "not_applicable" in _row(card, "lease_rows_vs_edgar", "BBB")      # rent immaterial
    assert "not_run" in _row(card, "lease_rows_vs_edgar", "CCC")             # material, no obs
    assert _check(card, "lease_rows_vs_edgar")["fleet"]["excluded"] == 1


def test_lease_rows_refuses_a_status_it_was_not_taught() -> None:
    page = _page("ZZZ", lease=_lease(material=True, rent=1.0, cost=1.0,
                                     obs=[_obs("2020-03-31", "reconciled", 1.0)]))
    page["mechanical"]["valuation"]["lease_basis"]["observations"][0]["status"] = "half-checked"
    with pytest.raises(ValueError, match="half-checked"):
        _card({"ZZZ": page})


def test_rent_band_edge_and_the_unratioable_case() -> None:
    card = _card()
    assert _row(card, "rent_vs_edgar_lease_cost", "AAA") == _counts(confirmed=1)   # exactly 1.5x
    assert _row(card, "rent_vs_edgar_lease_cost", "BBB") == _counts(unexplained=1)  # beyond it
    assert _row(card, "rent_vs_edgar_lease_cost", "CCC") == _counts(unchecked=1)    # rent of 0


def test_rent_disagrees_is_the_pages_own_rule() -> None:
    assert rent_disagrees(100.0, 100.0 * _RENT_DISAGREE) is False
    assert rent_disagrees(100.0 * _RENT_DISAGREE + 1.0, 100.0) is True
    assert rent_disagrees(0.0, 50.0) is None


def test_ebit_margin_boundary_and_same_source() -> None:
    card = _card()
    assert _row(card, "ebit_margin_vs_gaap", "AAA") == _counts(confirmed=1)
    assert _row(card, "ebit_margin_vs_gaap", "BBB") == _counts(unexplained=1)    # exactly 2.0
    assert _row(card, "ebit_margin_vs_gaap", "CCC") == _counts(unchecked=1)      # both legs CIQ
    # both legs CIQ is never a confirmation, even where the type carries a gap beside the flag
    one = {"DDD": _page("DDD", midcycle=_gap(basis_gap=0.0, same_source=True))}
    assert _row(_card(one), "ebit_margin_vs_gaap", "DDD") == _counts(unchecked=1)


def test_market_cap_tests_share_basis_only() -> None:
    card = _card()
    assert _row(card, "market_cap_share_basis", "AAA") == _counts(confirmed=1)
    assert _row(card, "market_cap_share_basis", "BBB") == _counts(stated=1)      # a 2:1 split
    assert _row(card, "market_cap_share_basis", "CCC") == _counts(unchecked=1)   # no close


def test_ev_bridge_tolerance_edge() -> None:
    card = _card()
    assert _row(card, "ev_bridge_vs_ciq_tev", "AAA") == _counts(confirmed=1)     # exactly $0.5M
    assert _row(card, "ev_bridge_vs_ciq_tev", "BBB") == _counts(unexplained=1)
    assert _row(card, "ev_bridge_vs_ciq_tev", "CCC") == _counts(unchecked=1)


def test_net_debt_flag_is_not_counted_where_the_bridge_is_absent() -> None:
    """THE NEGATIVE PIN: CCC's page says net_debt_reconciled=True with no bridge to test it on
    (the producer's `bridge_nd is None or …`). Counted as confirmed, it would be a pass the check
    never made — so the stored outcome is read, never the flag."""
    card = _card()
    assert _row(card, "net_debt_vs_implied_bridge", "AAA") == _counts(confirmed=1)
    assert _row(card, "net_debt_vs_implied_bridge", "BBB") == _counts(unexplained=1)
    assert _row(card, "net_debt_vs_implied_bridge", "CCC") == _counts(unchecked=1)
    # the flag alone, with no outcome stored beside it, is a check the scorecard never saw run
    bare = _page("FLG", iv=_implied_valuation(10.0, 20.0), ie=_ie(nd_reconciled=True))
    assert "not_run" in _row(_card({"FLG": bare}), "net_debt_vs_implied_bridge", "FLG")


def _netting_page(ticker: str, *, comps_net_debt: float, netted: float | None) -> dict[str, Any]:
    """A page whose comps net debt sits BELOW its cash/debt bridge (debt 20 − cash 10 = 10),
    as CIQ's Net Debt does when it nets long-term marketable securities (UBER, 2026-10-23)."""
    page = _page(ticker, iv=_implied_valuation(10.0, 20.0),
                 ie=_ie(nd_reconciled=False, nd_check=CHECK_DIFFER))
    page["mechanical"]["peer_comps"] = {"peer_grid": {"status": "present", "value": [
        PeerRow(name="peer", ticker="X:P", net_debt=SENTINEL).model_dump(mode="json"),
        PeerRow(name=ticker, ticker=f"X:{ticker}", is_name=True,
                net_debt=comps_net_debt).model_dump(mode="json")]}}
    if netted is not None:
        page["ev_bridge"] = EvBridge(
            lines=[ClaimLine(label="Total Debt", sign=1, value=20.0, source="synthetic"),
                   ClaimLine(label=_NETTED_LABEL, sign=-1, value=netted, source="synthetic")],
            claims=comps_net_debt, net_debt=comps_net_debt, rule="synthetic",
        ).model_dump(mode="json")
    return page


def test_net_debt_gap_that_is_ciqs_netting_is_a_stated_reason() -> None:
    """Operator, 2026-10-24: CIQ's Net Debt nets long-term marketable securities and the comps
    bridge is debt − cash, so where the gap IS the page's netted line (UBER: 9,340 − 4,744 =
    4,596 netted) the difference has a stated reason. A gap the netting does not account for,
    or a page that carries no netted line (ORKA), stays unexplained."""
    exact = _netting_page("NET", comps_net_debt=6.0, netted=4.0)
    edge = _netting_page("EDG", comps_net_debt=6.0 - EV_BRIDGE_CIQ_TOL, netted=4.0)
    wrong = _netting_page("WRG", comps_net_debt=5.0, netted=4.0)
    none_ = _netting_page("NON", comps_net_debt=6.0, netted=None)
    card = _card({"NET": exact, "EDG": edge, "WRG": wrong, "NON": none_})
    assert _row(card, "net_debt_vs_implied_bridge", "NET") == _counts(stated=1)
    assert _row(card, "net_debt_vs_implied_bridge", "EDG") == _counts(stated=1)
    assert _row(card, "net_debt_vs_implied_bridge", "WRG") == _counts(unexplained=1)
    assert _row(card, "net_debt_vs_implied_bridge", "NON") == _counts(unexplained=1)
    # a page whose flag already agrees is confirmed whatever its netting
    agree = _netting_page("AGR", comps_net_debt=10.0, netted=0.0)
    agree["mechanical"]["valuation"]["implied_expectations"].update(
        net_debt_reconciled=True, net_debt_check=CHECK_AGREE)
    assert _row(_card({"AGR": agree}), "net_debt_vs_implied_bridge", "AGR") == _counts(confirmed=1)


def test_net_debt_never_scores_a_display_parsed_bridge() -> None:
    """Codex, #792 round 1: the producer's `_ie_bridge_net_debt` falls back to PARSING the bridge's
    display string when its structured floats are absent. A bridge known only from display text is
    no structured second figure, so the page's flag is not counted as confirmed on it."""
    iv = _implied_valuation(None, None)
    iv["bridge"] = Sourced.present("+ cash $10.0M − total debt $20.0M",
                                   source_ref="synthetic").model_dump(mode="json")
    # the producer DID compare (its parse found both), so its outcome agrees — and is still not
    # counted, because the second figure is display text
    page = _page("DSP", iv=iv, ie=_ie(nd_check=CHECK_AGREE))
    assert _row(_card({"DSP": page}), "net_debt_vs_implied_bridge", "DSP") == _counts(unchecked=1)
    half = _page("HLF", iv=_implied_valuation(10.0, None), ie=_ie(nd_check=CHECK_AGREE))
    assert _row(_card({"HLF": half}), "net_debt_vs_implied_bridge", "HLF") == _counts(unchecked=1)


def test_multiples_sheet_coherence_reads_the_bands_own_flag() -> None:
    card = _card()
    assert _row(card, "multiples_sheet_coherence", "AAA") == _counts(confirmed=1)
    assert _row(card, "multiples_sheet_coherence", "BBB") == _counts(unexplained=1)
    # another flag on the band is not a coherence trip, and no margins means the check never ran
    assert _row(card, "multiples_sheet_coherence", "CCC") == _counts(unchecked=1)
    assert "not_run" in _row(_card({"DDD": _page("DDD")}), "multiples_sheet_coherence", "DDD")


def test_snapshot_multiple_runs_on_tev_ebit_only() -> None:
    card = _card()
    assert _row(card, "snapshot_multiple", "AAA") == _counts(confirmed=1)
    assert _row(card, "snapshot_multiple", "BBB") == _counts(unexplained=1)
    assert "not_applicable" in _row(card, "snapshot_multiple", "CCC")


#: The checks that read an outcome stored beside a line or flag (`schemas.CrossCheck`).
_STORED = ("guide_vs_release", "wall_vs_10q", "fcf_sign_vs_edgar_ocf", "forward_multiple_vintage",
           "net_debt_vs_implied_bridge")


def test_a_stored_outcome_is_scored_as_stored() -> None:
    card = _card()
    for cid in _STORED:
        assert _row(card, cid, "AAA") == _counts(confirmed=1), cid
        assert _row(card, cid, "BBB") == _counts(unexplained=1), cid
        assert _row(card, cid, "CCC") == _counts(unchecked=1), cid


def test_the_vintage_flag_that_reads_coherent_without_running_is_unchecked() -> None:
    """THE NEGATIVE PIN: CCC's `vintage_coherent` is True and its probe never ran. The flag alone
    is never read; with no outcome beside it the page is one the check did not run on."""
    assert _fixture()["CCC"]["mechanical"]["valuation"]["implied_expectations"][
        "vintage_coherent"] is True
    assert _row(_card(), "forward_multiple_vintage", "CCC") == _counts(unchecked=1)
    bare = {"FLG": _page("FLG", ie=_ie(vintage_coherent=True))}
    assert "no vintage_check on the page" in _row(_card(bare), "forward_multiple_vintage", "FLG")[
        "not_run"]


def test_a_divergence_the_page_explains_is_stated() -> None:
    """An instrument maturing beside the window's +12m boundary is the reason the page states
    for a wall divergence (`wall_coherence_near_boundary`) — never read as unexplained."""
    page = {"EDG": _page("EDG", ps=_ps(wall=CHECK_DIFFER, near=True))}
    assert _row(_card(page), "wall_vs_10q", "EDG") == _counts(stated=1)
    assert _row(_card(), "wall_vs_10q", "BBB") == _counts(unexplained=1)    # near=False


def test_an_absent_outcome_is_not_run_and_never_a_pass() -> None:
    """A page that predates the outcomes, or has no block to carry them: not run, by name."""
    old = {"OLD": _page("OLD", ps=_ps(), iv=_implied_valuation(10.0, 20.0))}
    card = _card(old)
    for cid in _STORED:
        row = _row(card, cid, "OLD")
        assert "on the page" in row["not_run"] and core.CONFIRMED not in row, cid
    none = {"NON": _page("NON")}
    del none["NON"]["mechanical"]["valuation"]["implied_expectations"]
    for cid in _STORED:
        assert "not_run" in _row(_card(none), cid, "NON"), cid


def test_an_outcome_the_scorecard_was_not_taught_raises() -> None:
    page = _page("ZZZ", ps=_ps())
    page["mechanical"]["primary_source"]["guide_verification_check"] = "half-checked"
    with pytest.raises(ValueError, match="half-checked"):
        _card({"ZZZ": page})


# --- invariants of the card itself -------------------------------------------------------------


def _assert_coherent(card: dict[str, Any]) -> None:
    n = card["boundary"]["items"]
    assert card["boundary"]["names"] == sorted(card["boundary"]["names"])
    for c in card["checks"]:
        f, rows = c["fleet"], c["by_name"]
        assert sorted(rows) == card["boundary"]["names"]
        assert f["items"] == n == f["items_run"] + f["items_not_run"] + f["items_not_applicable"]
        for s in core.STATUSES:   # the fleet total IS the sum of the names — nothing dropped
            assert f[s] == sum(r.get(s, 0) for r in rows.values()), (c["id"], s)
        assert f["units"] == sum(f[s] for s in core.STATUSES)
        assert f["excluded"] == sum(r.get("excluded", 0) for r in rows.values())
        listed = [t for g in c["not_run"] + c["not_applicable"] for t in g["names"]]
        assert len(listed) == f["items_not_run"] + f["items_not_applicable"] == len(set(listed))


def _numbers(o: Any) -> list[Any]:
    if isinstance(o, dict):
        return [x for v in o.values() for x in _numbers(v)]
    if isinstance(o, list):
        return [x for v in o for x in _numbers(v)]
    return [o] if isinstance(o, (int, float)) and not isinstance(o, bool) else []


def test_fixture_card_is_coherent_and_deterministic() -> None:
    card = _card()
    _assert_coherent(card)
    assert json.dumps(card) == json.dumps(_card())


def test_no_ciq_figure_reaches_the_snapshot() -> None:
    """COUNTS AND STATUSES ONLY. The sentinel sits in every CIQ field of the fixture; it, and any
    non-integer number at all, must be absent from what would be committed."""
    body = json.dumps(_card())
    assert str(SENTINEL) not in body and "7777" not in body
    assert all(isinstance(x, int) for x in _numbers(_card()))
    # the guard can fire: a card that carried a figure would be caught by the same two tests
    leaked = {**_card(), "leak": SENTINEL}
    assert str(SENTINEL) in json.dumps(leaked)
    assert not all(isinstance(x, int) for x in _numbers(leaked))


# --- the coverage map --------------------------------------------------------------------------


def test_every_workbook_kind_has_a_place_in_the_map() -> None:
    assert set(_WORKBOOK_KEYWORDS) <= {f.origin for f in ciq.FAMILIES}


def test_every_check_is_mapped_and_every_mapped_check_exists() -> None:
    mapped = {cid for f in ciq.FAMILIES for cid in f.checks}
    assert mapped == set(ciq.CHECK_IDS)
    assert len({f.id for f in ciq.FAMILIES}) == len(ciq.FAMILIES)


def test_classification_is_derived_from_the_scored_checks() -> None:
    fam = {f.id: f for f in ciq.FAMILIES}
    assert core.classify(ciq.SOURCE, fam["financials.quarterly_ebitda"]) == core.INDEPENDENT
    assert core.classify(ciq.SOURCE, fam["financials.balance_sheet_claims"]) == core.INTERNAL
    # consensus and segments are INTERNAL on the currency their panels state, and nothing else
    # (`currency_stated_usd`, 2026-10-27); the peer grid, which it does not read, stays single
    assert core.classify(ciq.SOURCE, fam["estimates.consensus"]) == core.INTERNAL
    assert core.classify(ciq.SOURCE, fam["comps.peer_grid"]) == core.SINGLE_SOURCE
    assert core.classify(ciq.SOURCE, fam["estimates.guidance"]) == core.INDEPENDENT
    assert core.classify(ciq.SOURCE, fam["financials.segments"]) == core.INTERNAL
    assert core.classify(ciq.SOURCE, fam["financials.ratios"]) == core.UNVERIFIED
    # a family with an internal AND an independent check is independent; internal alone is not
    mixed = core.Family("x", "comps", (), "x", checks=("ev_bridge_vs_ciq_tev", "ebitda_vs_xbrl"))
    assert core.classify(ciq.SOURCE, mixed) == core.INDEPENDENT
    internal_only = core.Family("y", "comps", (), "y", checks=("ev_bridge_vs_ciq_tev",))
    assert core.classify(ciq.SOURCE, internal_only) == core.INTERNAL


def test_failure_guards_follow_the_checks_declared_classes() -> None:
    """The guard a family shows per failure class is the strongest of its scored checks' — an
    internal check never reads as an independent guard, and an unscored family guards nothing."""
    fam = {f.id: f for f in ciq.FAMILIES}
    ebitda = core.failure_guard(ciq.SOURCE, fam["financials.quarterly_ebitda"])
    assert set(ebitda.values()) == {core.INDEPENDENT}
    claims = core.failure_guard(ciq.SOURCE, fam["financials.balance_sheet_claims"])
    assert claims["wrong_cell"] == core.INTERNAL and claims["different_definition"] == "none"
    consensus = core.failure_guard(ciq.SOURCE, fam["estimates.consensus"])
    assert consensus.pop("wrong_unit") == core.INTERNAL and set(consensus.values()) == {"none"}
    card = _card()
    for fc, row in card["failure_class_summary"].items():
        assert sum(row.values()) == len(ciq.FAMILIES), fc
        # split by the DECLARED fallback (does a second source exist?), never the derived class
        single = sum(1 for f in ciq.FAMILIES if f.fallback == core.SINGLE_SOURCE
                     and core.failure_guard(ciq.SOURCE, f)[fc] == "none")
        assert row["none_single_source"] == single, fc
    # consensus has no second source: its unguarded classes count single-source, its currency not
    summary = card["failure_class_summary"]
    assert summary["wrong_file"]["none_single_source"] == (
        summary["wrong_unit"]["none_single_source"] + 1)

    # one read: the hash `load` stamps is the hash of exactly the pages it returns
    assert ciq.load(ROOT).sha256 == ciq.dossier_set_sha256(ROOT)


_CITED = re.compile(r"CIQ ([A-Z][A-Za-z &/-]*?)(?: \((?:Quarterly|Annual)\))?\s*→\s*"
                    r"([A-Z][A-Za-z0-9 &/-]*?)(?=\s*(?:→|\(|\[|·|—|,|;|'|\)|$| vs | against ))")


def _cited_sheets(pages: dict[str, dict[str, Any]]) -> set[str]:
    """Every 'Workbook→Sheet' a page's source_refs cite in the arrow form. A TEST-side read of
    provenance strings, guarding the map's completeness — the scorecard itself parses none."""
    out: set[str] = set()

    def walk(o: Any) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str) and "source" in k:
                    out.update(f"{m.group(1).strip()}→{m.group(2).strip()}"
                               for m in _CITED.finditer(v))
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(pages)
    return out


def test_cited_sheet_reader_finds_an_undeclared_sheet() -> None:
    page = {"x": {"source_ref": "CIQ Financials (Quarterly)→Income Statement 'EBITDA'"},
            "y": {"source_ref": "CIQ Financials→Pension Detail (2026-08-01)"}}
    cited = _cited_sheets({"P": page})
    assert cited == {"Financials→Income Statement", "Financials→Pension Detail"}
    declared = {s for f in ciq.FAMILIES for s in f.cited_as}
    assert cited - declared == {"Financials→Pension Detail"}


# --- end to end over the committed pages -------------------------------------------------------

_PAGES = ciq.load_pages(ROOT)
needs_pages = pytest.mark.skipif(not _PAGES, reason="no committed dossiers")


@needs_pages
def test_every_sheet_the_committed_pages_cite_is_in_the_map() -> None:
    declared = {s for f in ciq.FAMILIES for s in f.cited_as}
    cited = _cited_sheets(_PAGES)
    assert cited, "the reader found no citation at all — it is not reading the pages"
    assert cited <= declared, sorted(cited - declared)


@needs_pages
def test_committed_corpus_card_is_coherent() -> None:
    card = core.scorecard(ciq.SOURCE, ciq.load(ROOT), measured_on="2026-10-23", git_head=None,
                          inputs_match_head=None)
    _assert_coherent(card)
    assert card["boundary"]["items"] == len(list((ROOT / "data" / "dossiers").glob(
        "*/dossier.json")))
    assert all(isinstance(x, int) for x in _numbers(card))
    assert card["source"]["id"] == "ciq" and core.discover()["ciq"] is ciq.SOURCE
    # the EBITDA check counts every quarter the pages carry — none dropped, none invented
    quarters = sum(len(((p.get("mechanical") or {}).get("financial_summary") or {})
                       .get("ebitda_reconciliation", {}).get("quarters") or [])
                   for p in _PAGES.values())
    assert _check(card, "ebitda_vs_xbrl")["fleet"]["units"] == quarters
    # and every lease date, less the ones its rule excludes, on the material pages it runs on
    lease = _check(card, "lease_rows_vs_edgar")
    dates = sum(len(_PAGES[t]["mechanical"]["valuation"]["lease_basis"]["observations"])
                for t, r in lease["by_name"].items() if "not_run" not in r
                and "not_applicable" not in r)
    assert lease["fleet"]["units"] + lease["fleet"]["excluded"] == dates


@needs_pages
def test_every_stated_net_debt_difference_is_exactly_the_netting() -> None:
    card = core.scorecard(ciq.SOURCE, ciq.corpus(_PAGES, ""), measured_on="2026-10-24",
                          git_head=None, inputs_match_head=None)
    for t, row in _check(card, "net_debt_vs_implied_bridge")["by_name"].items():
        if not row.get(core.DIFFERS_STATED):
            continue
        p = _PAGES[t]
        iv = p["mechanical"]["implied_valuation"]
        nd = next(r["net_debt"] for r in p["mechanical"]["peer_comps"]["peer_grid"]["value"]
                  if r.get("is_name"))
        netted = next(ln["value"] for ln in p["ev_bridge"]["lines"] if ln["label"] == _NETTED_LABEL)
        assert abs(iv["bridge_debt"] - iv["bridge_cash"] - nd - netted) <= EV_BRIDGE_CIQ_TOL, t


@needs_pages
def test_committed_market_caps_are_ciqs() -> None:
    """The market-cap check is a CIQ check only while the page's cap IS CIQ's."""
    refs = {t: ((p["mechanical"]["stock_info"].get("market_cap") or {}).get("source_ref") or "")
            for t, p in _PAGES.items()}
    assert all("CIQ" in r for r in refs.values()), refs


@needs_pages
def test_no_committed_page_is_confirmed_on_an_absent_bridge() -> None:
    card = core.scorecard(ciq.SOURCE, ciq.corpus(_PAGES, ""), measured_on="2026-10-23",
                          git_head=None, inputs_match_head=None)
    for t, row in _check(card, "net_debt_vs_implied_bridge")["by_name"].items():
        iv = _PAGES[t]["mechanical"].get("implied_valuation") or {}
        if iv.get("bridge_cash") is None or iv.get("bridge_debt") is None:
            assert row.get(core.CONFIRMED, 0) == 0, t


@needs_pages
def test_the_all_clear_checks_fire_on_a_perturbed_committed_page() -> None:
    """CORPUS BEFORE SYNTHETIC. The EV bridge and the share basis confirm on every committed page,
    so each is shown to fire on a real one: a committed page, perturbed in memory only."""
    from vinci.dossier.freshness import reconcile_cap

    def drift(p: dict[str, Any]) -> float:
        si = p["mechanical"]["stock_info"]
        rc = reconcile_cap(cap_musd=si["market_cap"]["value"], shares=si["shares_out"]["value"],
                           spot=si["price"]["value"])
        return abs(rc.gap) if rc is not None else 1.0

    usable = [t for t, p in _PAGES.items() if isinstance(p.get("ev_bridge"), dict)
              and p["ev_bridge"].get("ciq_tev_claims") is not None
              and (p["mechanical"].get("implied_valuation") or {}).get("bridge_cash") is not None]
    t = min(usable, key=lambda x: drift(_PAGES[x]))
    page = json.loads(json.dumps(_PAGES[t]))
    page["ev_bridge"]["ciq_tev_claims"] += 2 * EV_BRIDGE_CIQ_TOL
    page["mechanical"]["stock_info"]["shares_out"]["value"] /= 2   # a 2:1 split between panels
    page["mechanical"]["implied_valuation"]["bridge_cash"] = None   # and no bridge to test against
    page["mechanical"]["implied_valuation"]["bridge"] = {"status": "unknown", "note": "perturbed"}
    card = _card({t: page})
    assert _row(card, "ev_bridge_vs_ciq_tev", t) == _counts(unexplained=1)
    assert _row(card, "market_cap_share_basis", t) == _counts(stated=1)
    assert _row(card, "net_debt_vs_implied_bridge", t) == _counts(unchecked=1)
    untouched = _card({t: _PAGES[t]})
    assert _row(untouched, "ev_bridge_vs_ciq_tev", t) == _counts(confirmed=1)
    assert _row(untouched, "market_cap_share_basis", t) == _counts(confirmed=1)


def _stmt_rows(page: dict[str, Any], line: str) -> list[dict[str, Any]]:
    sr = ((page["mechanical"].get("financial_summary") or {}).get("statement_reconciliation")
          or {})
    return [r for r in sr.get("rows") or [] if r["line"] == line]


@needs_pages
def test_the_statement_checks_count_every_committed_row_and_find_real_differences() -> None:
    card = core.scorecard(ciq.SOURCE, ciq.corpus(_PAGES, ""), measured_on="2026-10-26",
                          git_head=None, inputs_match_head=None)
    for cid, line in (("revenue_vs_xbrl", "revenue"), ("ocf_vs_xbrl", "operating_cash_flow")):
        c = _check(card, cid)
        # every row the pages carry is a unit — none dropped, none invented — and every committed
        # block is its own table's (none stale)
        assert c["fleet"]["units"] == sum(len(_stmt_rows(p, line)) for p in _PAGES.values()), cid
        assert c["fleet"]["items_not_run"] == 0, c["not_run"]
        for t, row in c["by_name"].items():
            rows = _stmt_rows(_PAGES[t], line)
            named = sum(1 for r in rows if r["different"]
                        and (r["other_tag"] or r["earlier_accession"]))
            assert row.get(core.DIFFERS_STATED, 0) == named, (cid, t)
    # CORPUS BEFORE SYNTHETIC: both 'differs' readings occur on a real page before being relied on
    assert _check(card, "revenue_vs_xbrl")["fleet"][core.DIFFERS_STATED] > 0
    assert _check(card, "ocf_vs_xbrl")["fleet"][core.DIFFERS_UNEXPLAINED] > 0


class _FixtureEdgar:
    """EDGAR answered from the committed companyfacts fixtures — the network is never touched."""

    def __init__(self, ticker: str) -> None:
        self._path = ROOT / "tests" / "fixtures" / "companyfacts" / f"{ticker}.json"

    def companyfacts(self, cik: str) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(self._path.read_text())
        return out


@needs_pages
def test_the_statement_checks_fire_on_a_perturbed_committed_page() -> None:
    """CORPUS BEFORE SYNTHETIC. A committed page whose every revenue and OCF period confirms is
    perturbed IN MEMORY the ways a CIQ figure goes wrong — another unit (×1,000), another period
    (the year before's figure), another cell (revenue in the cash-flow row) — and rebuilt through
    the back-fill against the committed filings: each lands as an unexplained difference, and the
    untouched page still confirms."""
    from vinci.dossier import statement_recon as sr
    from vinci.dossier.refresh import statement_recon_transform

    def years(p: dict[str, Any]) -> list[str]:
        """Fiscal-year columns both lines carry, oldest first."""
        ocf = {r["column"] for r in _stmt_rows(p, "operating_cash_flow") if not r["is_ltm"]}
        return [r["column"] for r in _stmt_rows(p, "revenue")
                if not r["is_ltm"] and r["column"] in ocf]

    def clean(p: dict[str, Any]) -> bool:
        """Every period confirms, and the year shift and the row swap are real errors on it."""
        rows = _stmt_rows(p, "revenue") + _stmt_rows(p, "operating_cash_flow")
        if len(years(p)) < 3 or any(r["filing"] is None or r["different"] for r in rows):
            return False
        v: dict[tuple[str, str], float] = {(r["line"], r["column"]): r["ciq"] for r in rows}
        _u, c, y = years(p)[-3:]
        return (abs(v[("revenue", c)] / v[("revenue", y)] - 1) > 0.05
                and abs(v[("revenue", c)] / v[("operating_cash_flow", c)] - 1) > 0.05)

    t = next(t for t, p in sorted(_PAGES.items()) if clean(p))
    page = json.loads(json.dumps(_PAGES[t]))
    fs = page["mechanical"]["financial_summary"]
    table = fs["annual"]["value"]
    vals = {r["label"]: r["values"] for r in table["rows"]}
    rev, ocf = vals["Revenue ($M)"], vals["CFO ($M)"]
    unit, cell, period = (table["columns"].index(c) for c in years(page)[-3:])
    rev[unit] *= 1000.0                 # another unit: thousands read as millions
    rev[period] = rev[cell]             # another period: the year before's revenue
    ocf[cell] = rev[cell]               # another cell: revenue in the cash-flow row
    figures = [sr.CiqFigure(r["line"], r["column"], date.fromisoformat(r["period_end"]),
                            r["is_ltm"], sr.table_figures(table)[(r["line"], r["column"])])
               for r in fs.pop("statement_reconciliation")["rows"]]
    refused: list[str] = []
    page["mechanical"] = statement_recon_transform(
        page, edgar=_FixtureEdgar(t), refused=refused, figures_for=lambda _t: figures)(
        page["mechanical"])
    assert refused == []
    card = _card({t: page})
    n_rev, n_ocf = len(_stmt_rows(page, "revenue")), len(_stmt_rows(page, "operating_cash_flow"))
    assert _row(card, "revenue_vs_xbrl", t) == _counts(confirmed=n_rev - 2, unexplained=2)
    assert _row(card, "ocf_vs_xbrl", t) == _counts(confirmed=n_ocf - 1, unexplained=1)
    untouched = _card({t: _PAGES[t]})
    assert _row(untouched, "revenue_vs_xbrl", t) == _counts(confirmed=n_rev)
    assert _row(untouched, "ocf_vs_xbrl", t) == _counts(confirmed=n_ocf)


#: Where each stored outcome sits on a page, by the check that scores it.
_STORED_AT = {"guide_vs_release": ("primary_source", "guide_verification_check"),
              "wall_vs_10q": ("primary_source", "wall_coherence_check"),
              "fcf_sign_vs_edgar_ocf": ("primary_source", "self_funding_check"),
              "forward_multiple_vintage": ("implied_expectations", "vintage_check"),
              "net_debt_vs_implied_bridge": ("implied_expectations", "net_debt_check")}
_STATUS_OF = {CHECK_AGREE: core.CONFIRMED, CHECK_DIFFER: core.DIFFERS_UNEXPLAINED,
              CHECK_NOT_RUN: core.UNCHECKED}


def _stored(page: dict[str, Any], cid: str) -> Any:
    block, key = _STORED_AT[cid]
    mech = page["mechanical"]
    node = (mech.get("primary_source") if block == "primary_source"
            else (mech.get("valuation") or {}).get("implied_expectations"))
    return (node or {}).get(key)


@needs_pages
def test_every_committed_outcome_is_scored_as_the_page_stores_it() -> None:
    """Each committed page's stored outcome lands as its status — the wall's divergence as STATED
    where the page carries its boundary reason, a bridge known only from display text as
    unchecked — and a page without one is not run, never confirmed."""
    card = core.scorecard(ciq.SOURCE, ciq.corpus(_PAGES, ""), measured_on="2026-10-23",
                          git_head=None, inputs_match_head=None)
    for cid in _STORED_AT:
        for t, row in _check(card, cid)["by_name"].items():
            v = _stored(_PAGES[t], cid)
            if v is None:
                assert "not_run" in row, (cid, t)
                continue
            want = _STATUS_OF[v]
            ps = _PAGES[t]["mechanical"].get("primary_source") or {}
            if cid == "wall_vs_10q" and v == CHECK_DIFFER and ps.get(
                    "wall_coherence_near_boundary") is True:
                want = core.DIFFERS_STATED
            iv = _PAGES[t]["mechanical"].get("implied_valuation") or {}
            if cid == "net_debt_vs_implied_bridge" and (iv.get("bridge_cash") is None
                                                        or iv.get("bridge_debt") is None):
                want = core.UNCHECKED
            if cid == "net_debt_vs_implied_bridge" and v == CHECK_DIFFER and row.get(
                    core.DIFFERS_STATED):
                want = core.DIFFERS_STATED   # CIQ's netting — which pages, the netting pin says
            assert row == {**_counts(), want: 1}, (cid, t, v, row)


@needs_pages
def test_no_committed_flag_that_passed_without_running_is_confirmed() -> None:
    """CORPUS BEFORE SYNTHETIC: committed pages carry `vintage_coherent: true` where the probe
    never ran. Each is unchecked on the card, never confirmed."""
    card = core.scorecard(ciq.SOURCE, ciq.corpus(_PAGES, ""), measured_on="2026-10-23",
                          git_head=None, inputs_match_head=None)
    rows = _check(card, "forward_multiple_vintage")["by_name"]
    silent = [t for t, p in _PAGES.items()
              if ((p["mechanical"].get("valuation") or {}).get("implied_expectations") or {})
              .get("vintage_coherent") is True and _stored(p, "forward_multiple_vintage")
              == CHECK_NOT_RUN]
    assert silent, "no committed page carries a coherent flag over a probe that did not run"
    for t in silent:
        assert rows[t] == _counts(unchecked=1), t


def _latest_snapshot() -> Path | None:
    snaps = sorted((ROOT / "data" / "snapshots" / "data_quality" / "ciq").glob("*.json"))
    return snaps[-1] if snaps else None


@needs_pages
def test_the_committed_snapshot_reproduces_from_the_pages_it_names() -> None:
    """A snapshot is a SERIES point: valid always, and byte-for-byte the scorecard of the pages
    it names whenever those are the pages committed now. After an artifact pass moves the pages,
    the hash differs and only coherence is asserted."""
    snap = _latest_snapshot()
    if snap is None:
        pytest.skip("no committed CIQ quality snapshot yet")
    saved = json.loads(snap.read_text())
    assert saved["schema"] == core.SCHEMA and saved["source"]["id"] == "ciq"
    assert snap.stem == saved["boundary"]["measured_on"]
    _assert_coherent(saved)
    assert all(isinstance(x, int) for x in _numbers(saved))
    b = saved["boundary"]
    if b["inputs_sha256"] != ciq.dossier_set_sha256(ROOT):
        return
    fresh = core.scorecard(ciq.SOURCE, ciq.corpus(_PAGES, b["inputs_sha256"]),
                           measured_on=b["measured_on"], git_head=b["git_head"],
                           inputs_match_head=b["inputs_match_head"])
    assert fresh == saved


# --- the command -------------------------------------------------------------------------------


def _seed(tmp: Path, pages: dict[str, dict[str, Any]]) -> None:
    for t, p in pages.items():
        d = tmp / "data" / "dossiers" / t
        d.mkdir(parents=True)
        (d / "dossier.json").write_text(json.dumps(p))


def test_command_prints_every_name_and_writes_a_dated_snapshot(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(tmp_path, _fixture())
    monkeypatch.chdir(tmp_path)
    today = date.today().isoformat()
    assert main(["audit", "quality", "--source", "ciq", "--write"]) == 0
    out = capsys.readouterr().out
    for t in ("AAA", "BBB", "CCC"):
        assert t in out
    assert f"snapshot written: data/snapshots/data_quality/ciq/{today}.json" in out
    saved = json.loads((tmp_path / f"data/snapshots/data_quality/ciq/{today}.json").read_text())
    assert saved["boundary"]["items"] == 3 and saved["boundary"]["measured_on"] == today
    assert main(["audit", "quality", "--source", "ciq", "--write"]) == 0
    assert "snapshot unchanged" in capsys.readouterr().out


def test_a_snapshot_is_dated_the_day_it_is_measured(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Codex, #792 round 1: `--as-of` stamped a WRITTEN series point with any date while the pages
    read were today's, so a backdated snapshot would carry later data. It may still label a
    printed report; it can never date a written one."""
    _seed(tmp_path, _fixture())
    monkeypatch.chdir(tmp_path)
    past = (date.today() - timedelta(days=30)).isoformat()
    assert main(["audit", "quality", "--source", "ciq", "--as-of", past, "--write"]) == 1
    assert "dated the day it is measured" in capsys.readouterr().err
    assert not (tmp_path / "data" / "snapshots").exists()
    assert main(["audit", "quality", "--source", "ciq", "--as-of", past]) == 0      # print only
    assert main(["audit", "quality", "--source", "ciq", "--as-of", date.today().isoformat(),
                 "--write"]) == 0


def test_command_with_no_pages_fails_loud(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["audit", "quality", "--source", "ciq"]) == 1
    assert not (tmp_path / "data" / "snapshots").exists()


def test_command_refuses_an_as_of_that_is_not_a_date(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The as-of names the snapshot file: a path-shaped one must never become a directory."""
    _seed(tmp_path, _fixture())
    monkeypatch.chdir(tmp_path)
    for bad in ("2026/10/23", "../x", "today"):
        assert main(["audit", "quality", "--source", "ciq", "--as-of", bad, "--write"]) == 1
    assert not (tmp_path / "data" / "snapshots").exists()
    assert not (tmp_path / "data" / "x.json").exists()


def test_a_changed_same_date_snapshot_says_it_replaced_one(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(tmp_path, {"AAA": _fixture()["AAA"]})
    monkeypatch.chdir(tmp_path)
    assert main(["audit", "quality", "--source", "ciq", "--write"]) == 0
    _seed(tmp_path, {"BBB": _fixture()["BBB"]})
    capsys.readouterr()
    assert main(["audit", "quality", "--source", "ciq", "--write"]) == 0
    assert "snapshot REPLACED" in capsys.readouterr().out


def test_two_folders_for_one_ticker_are_refused(tmp_path: Path) -> None:
    for name in ("tjx", "TJX"):
        (tmp_path / "data" / "dossiers" / name).mkdir(parents=True, exist_ok=True)
    if len(list((tmp_path / "data" / "dossiers").iterdir())) < 2:
        pytest.skip("case-insensitive filesystem: the two folders are one")
    for name in ("tjx", "TJX"):
        (tmp_path / "data" / "dossiers" / name / "dossier.json").write_text("{}")
    with pytest.raises(ValueError, match="two dossier folders for TJX"):
        ciq.load_pages(tmp_path)
