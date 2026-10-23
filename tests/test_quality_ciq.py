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
from pathlib import Path
from typing import Any

import pytest

from vinci.cli import main
from vinci.dossier.anchor import BASIS_AGREE_PTS, AnchorMidcycleGap
from vinci.dossier.ciq import _WORKBOOK_KEYWORDS
from vinci.dossier.ciq_sheets import EV_BRIDGE_CIQ_TOL
from vinci.dossier.lease_basis import _RENT_DISAGREE, rent_disagrees
from vinci.dossier.schemas import (
    ClaimLine,
    EbitdaReconciliation,
    EbitdaReconQuarter,
    EvBridge,
    ImpliedValuation,
    LeaseBasis,
    LeaseObservation,
    OwnHistoryBand,
    Sourced,
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


def _page(ticker: str, *, quarters: list[dict[str, Any]] | None = None,
          lease: dict[str, Any] | None = None, bridge: dict[str, Any] | None = None,
          nd_reconciled: bool = True, iv: dict[str, Any] | None = None,
          cap: float | None = 1000.0, shares: float | None = 100e6, spot: float | None = 10.0,
          midcycle: dict[str, Any] | None = None,
          multiple: dict[str, Any] | None = None,
          band: dict[str, Any] | None = None) -> dict[str, Any]:
    mech: dict[str, Any] = {
        "stock_info": {"market_cap": {"value": cap}, "shares_out": {"value": shares},
                       "price": {"value": spot}},
        "valuation": {"implied_expectations": {"net_debt_reconciled": nd_reconciled}},
    }
    if quarters is not None:
        mech["financial_summary"] = {"ebitda_reconciliation": EbitdaReconciliation(
            quarters=[EbitdaReconQuarter.model_validate(q) for q in quarters],
            ciq_ltm=SENTINEL, any_different=any(q["different"] for q in quarters),
            line="synthetic", source_ref="synthetic").model_dump(mode="json")}
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
            iv=_implied_valuation(10.0, 20.0), nd_reconciled=True,
            midcycle=_gap(basis_gap=BASIS_AGREE_PTS - 0.01),
            multiple={"metric": "TEV/EBIT", "snapshot_reconciles": True},
            band=_band(margins=True, flag=None)),
        "BBB": _page(
            "BBB",
            lease=_lease(material=False, rent=100.0, cost=100.0 * _RENT_DISAGREE + 1.0, obs=[]),
            bridge=_ev_bridge(500.0, 500.0 + EV_BRIDGE_CIQ_TOL + 0.1),
            iv=_implied_valuation(10.0, 20.0), nd_reconciled=False,
            spot=20.0,                       # cap ÷ shares = $10/sh against a $20 close: a 2:1
            midcycle=_gap(basis_gap=BASIS_AGREE_PTS),
            multiple={"metric": "TEV/EBIT", "snapshot_reconciles": False},
            band=_band(margins=True, flag="periodicity_mismatch+band_incoherent")),
        "CCC": _page(
            "CCC",
            lease=_lease(material=True, rent=0.0, cost=50.0, obs=[]),
            bridge=_ev_bridge(500.0, None),
            iv=None, nd_reconciled=True,     # the flag reads True with NO bridge to test it on
            spot=None,
            midcycle=_gap(basis_gap=None, same_source=True),
            multiple={"metric": "Price/Earnings", "snapshot_reconciles": None},
            band=_band(margins=False, flag="periodicity_mismatch")),
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
                                                              "the page"}
    # a block with no quarters is not a page the check ran on
    empty = _page("EEE", quarters=[])
    assert "not_run" in _row(_card({"EEE": empty}), "ebitda_vs_xbrl", "EEE")


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
    never made."""
    card = _card()
    assert _row(card, "net_debt_vs_implied_bridge", "AAA") == _counts(confirmed=1)
    assert _row(card, "net_debt_vs_implied_bridge", "BBB") == _counts(unexplained=1)
    assert _row(card, "net_debt_vs_implied_bridge", "CCC") == _counts(unchecked=1)


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
    assert core.classify(ciq.SOURCE, fam["estimates.consensus"]) == core.SINGLE_SOURCE
    assert core.classify(ciq.SOURCE, fam["estimates.guidance"]) == core.UNVERIFIED
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
    assert set(core.failure_guard(ciq.SOURCE, fam["estimates.consensus"]).values()) == {"none"}
    card = _card()
    single = sum(1 for f in ciq.FAMILIES if core.classify(ciq.SOURCE, f) == core.SINGLE_SOURCE)
    for fc, row in card["failure_class_summary"].items():
        assert sum(row.values()) == len(ciq.FAMILIES), fc
        assert row["none_single_source"] == single, fc

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
    assert main(["audit", "quality", "--source", "ciq", "--as-of", "2026-10-23", "--write"]) == 0
    out = capsys.readouterr().out
    for t in ("AAA", "BBB", "CCC"):
        assert t in out
    assert "snapshot written: data/snapshots/data_quality/ciq/2026-10-23.json" in out
    saved = json.loads((tmp_path / "data/snapshots/data_quality/ciq/2026-10-23.json").read_text())
    assert saved["boundary"]["items"] == 3 and saved["boundary"]["measured_on"] == "2026-10-23"
    assert main(["audit", "quality", "--source", "ciq", "--as-of", "2026-10-23", "--write"]) == 0
    assert "snapshot unchanged" in capsys.readouterr().out


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
    assert main(["audit", "quality", "--source", "ciq", "--as-of", "2026-10-23", "--write"]) == 0
    _seed(tmp_path, {"BBB": _fixture()["BBB"]})
    capsys.readouterr()
    assert main(["audit", "quality", "--source", "ciq", "--as-of", "2026-10-23", "--write"]) == 0
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
