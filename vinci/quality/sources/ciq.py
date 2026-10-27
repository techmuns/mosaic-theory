"""THE CIQ SOURCE for the data-quality scorecard (`vinci.quality.core`): "is the CIQ data
credible?".

WHY (2026-10-23). The checks existed and each page carried its own: CIQ's quarterly EBITDA against
the filings, the lease rows inside CIQ's TEV against EDGAR's operating leases, the EV bridge against
CIQ's own TEV, market cap against shares × price. Their results sat page by page — 27 pages each
holding their own. This source reads the COMMITTED pages only (`data/dossiers/*/dossier.json`),
never the licensed workbooks, so it runs in every checkout and in CI.

``independent`` here means the second figure is not CIQ's (EDGAR XBRL, the EOD close);
``internal`` means it is another CIQ export.

WHERE A PAGE STORES A VERDICT, IT IS READ; WHERE IT STORES ONLY THE INPUTS, THE PRODUCER'S OWN
CONSTANT IS APPLIED (`EV_BRIDGE_CIQ_TOL`, `reconcile_cap`, `rent_disagrees`). Nothing is re-decided.

STRUCTURED VALUES ONLY. A verdict that exists only as display text is listed in the coverage map
as UNSCORED, with its path — never parsed here. Three that were (guide verification, wall
coherence, self-funding), and two bools that read True when nothing ran (the vintage probe, the
net-debt flag), store their outcome beside the reading since 2026-10-23 (`schemas.CrossCheck`), and
are scored from that.

COUNTS AND STATUSES ONLY. The repo is public (2026-10-22): no CIQ figure, gap or quote reaches the
snapshot. The tolerances are this repo's constants, not CIQ data.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from vinci.dossier.anchor import BASIS_AGREE_PTS, MIDCYCLE_GAP_PTS
from vinci.dossier.band_guards import (
    _MAX_DA_RATIO,
    _MAX_IMPLIED_DA_MARGIN,
    _MAX_MARKET_RATIO,
    BAND_INCOHERENT,
)
from vinci.dossier.ciq_sheets import _NETTED_LABEL, EV_BRIDGE_CIQ_TOL, USD_STATED
from vinci.dossier.ebitda_recon import DIFFERENT_SHARE
from vinci.dossier.freshness import _INTEGER_TOLERANCE, reconcile_cap
from vinci.dossier.lease_basis import (
    _RENT_DISAGREE,
    MATERIALITY,
    RECONCILE_TOL,
    rent_disagrees,
)
from vinci.dossier.mechanical import _IE_TOL
from vinci.dossier.schemas import CHECK_AGREE, CHECK_DIFFER, CHECK_NOT_RUN
from vinci.dossier.statement_recon import DIFFERENT_FLOOR as _STMT_FLOOR
from vinci.dossier.statement_recon import DIFFERENT_SHARE as _STMT_SHARE
from vinci.dossier.statement_recon import table_figures
from vinci.dossier.valuation_basis import SNAPSHOT_TOL
from vinci.edgar.primary_source import _TOL as _WALL_TOL
from vinci.edgar.primary_source import BOUNDARY_DAYS, GUIDE_MATCH
from vinci.quality.core import (
    CONFIRMED,
    DIFFERS_STATED,
    DIFFERS_UNEXPLAINED,
    INDEPENDENT,
    INTERNAL,
    SINGLE_SOURCE,
    UNCHECKED,
    Check,
    Corpus,
    Family,
    ItemResult,
    Source,
    one,
)

#: The lease-observation statuses `lease_basis.observations` writes. Any other is a new state this
#: scorecard has not been taught — it raises rather than drop out of the count.
_LEASE_STATUSES = frozenset({"reconciled", "unreconciled", "unchecked", "pre-adoption"})
#: Why a check that reads a stored `CrossCheck` did not run on a page that lacks it. Both causes
#: are named because the page cannot say which: it predates the field, or the back-fill refused
#: it (its stored line did not reproduce from the page's own inputs) and only assembly can write it.
_ABSENT = ("no {key} on the page — it predates the field, or its stored line did not reproduce "
           "from the page's own inputs (refresh.cross_check_transform); assembly writes it")


def _get(d: Any, *path: str) -> Any:
    for k in path:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _num(x: Any) -> float | None:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _cross_check(page: dict[str, Any], node: Any, key: str, *, stated: bool = False) -> ItemResult:
    """A stored `CrossCheck` → one unit: agree confirms, differ differs (stated when the page
    states why for this page), not run is unchecked — the page exists and the check had no second
    figure. ABSENT is not run, never a pass; a value this scorecard was not taught raises."""
    v = node.get(key) if isinstance(node, dict) else None
    if v is None:
        return ItemResult(not_run=_ABSENT.format(key=key))
    if v == CHECK_AGREE:
        return one(CONFIRMED)
    if v == CHECK_DIFFER:
        return one(DIFFERS_STATED if stated else DIFFERS_UNEXPLAINED)
    if v == CHECK_NOT_RUN:
        return one(UNCHECKED)
    raise ValueError(f"{page.get('ticker')}: {key} is {v!r}, not an outcome this scorecard knows "
                     f"({[CHECK_AGREE, CHECK_DIFFER, CHECK_NOT_RUN]})")


# --- the checks ---------------------------------------------------------------------------------


def _ebitda_vs_xbrl(page: dict[str, Any]) -> ItemResult:
    er = _get(page, "mechanical", "financial_summary", "ebitda_reconciliation")
    if not isinstance(er, dict):
        return ItemResult(not_run="no ebitda_reconciliation block on the page")
    if not er.get("quarters"):
        return ItemResult(not_run="ebitda_reconciliation block carries no quarters")
    c: Counter[str] = Counter()
    for q in er.get("quarters") or []:
        if _num(q.get("filing_ebitda")) is None:
            c[UNCHECKED] += 1
        elif not q.get("different"):
            c[CONFIRMED] += 1
        elif q.get("matching_amount"):
            c[DIFFERS_STATED] += 1
        else:
            c[DIFFERS_UNEXPLAINED] += 1
    return ItemResult(counts=dict(c))


def _statement_vs_xbrl(page: dict[str, Any], line: str) -> ItemResult:
    fs = _get(page, "mechanical", "financial_summary")
    sr = _get(fs, "statement_reconciliation")
    if not isinstance(sr, dict):
        return ItemResult(not_run="no statement_reconciliation block on the page")
    rows = [r for r in sr.get("rows") or [] if isinstance(r, dict) and r.get("line") == line]
    # THE BLOCK IS SCORED ONLY WHILE IT IS THE TABLE'S: a refresh that moved the table and left the
    # block would otherwise score figures the page no longer shows
    want = {k: v for k, v in table_figures(_get(fs, "annual", "value")).items() if k[0] == line}
    if {(line, r.get("column")): r.get("ciq") for r in rows} != want:
        return ItemResult(not_run="the block's CIQ figures are not the annual table's — a stale "
                                  "block; assembly or refresh.statement_recon_transform rebuilds "
                                  "it")
    if not rows:
        return ItemResult(not_applicable="CIQ's annual table carries no figure for this line")
    c: Counter[str] = Counter()
    for r in rows:
        if _num(r.get("filing")) is None:
            c[UNCHECKED] += 1
        elif not r.get("different"):
            c[CONFIRMED] += 1
        elif r.get("other_tag") or r.get("earlier_accession"):
            c[DIFFERS_STATED] += 1
        else:
            c[DIFFERS_UNEXPLAINED] += 1
    return ItemResult(counts=dict(c))


def _revenue_vs_xbrl(page: dict[str, Any]) -> ItemResult:
    return _statement_vs_xbrl(page, "revenue")


def _ocf_vs_xbrl(page: dict[str, Any]) -> ItemResult:
    return _statement_vs_xbrl(page, "operating_cash_flow")


def _lease_rows_vs_edgar(page: dict[str, Any]) -> ItemResult:
    lb = _get(page, "mechanical", "valuation", "lease_basis")
    if not isinstance(lb, dict):
        return ItemResult(not_run="no lease_basis block on the page")
    if not lb.get("material"):
        return ItemResult(not_applicable="rent below the materiality line — the page keeps CIQ's "
                                         "history and never splits the leases out")
    obs = lb.get("observations") or []
    if not obs:
        return ItemResult(not_run="lease basis material but no observations (the page states "
                                  "its refusal)")
    c: Counter[str] = Counter()
    excluded = 0
    for o in obs:
        status = o.get("status")
        if status not in _LEASE_STATUSES:
            raise ValueError(f"{page.get('ticker')}: lease observation status {status!r} is not "
                             f"one this scorecard knows ({sorted(_LEASE_STATUSES)})")
        if status == "reconciled":
            c[CONFIRMED] += 1
        elif status == "unreconciled":
            c[DIFFERS_UNEXPLAINED] += 1
        elif status == "unchecked":
            c[UNCHECKED] += 1
        elif (_num(o.get("edgar_operating_leases")) or 0.0) > 0:
            # 'pre-adoption' WHILE EDGAR reports operating leases on that date: the comparative
            # rule in `lease_basis._split` — EDGAR's figure is a later filing's comparative and
            # CIQ's balance sheet is the one originally filed, before the standard applied
            c[DIFFERS_STATED] += 1
        else:
            excluded += 1        # before ASC 842 on both sides: no operating lease to compare
    return ItemResult(counts=dict(c), excluded=excluded)


def _rent_vs_edgar_lease_cost(page: dict[str, Any]) -> ItemResult:
    lb = _get(page, "mechanical", "valuation", "lease_basis")
    if not isinstance(lb, dict):
        return ItemResult(not_run="no lease_basis block on the page")
    rent, cost = _num(lb.get("rent_expense")), _num(lb.get("edgar_lease_cost"))
    verdict = rent_disagrees(rent, cost) if rent is not None and cost is not None else None
    if verdict is None:
        return one(UNCHECKED)
    return one(DIFFERS_UNEXPLAINED if verdict else CONFIRMED)


def _ebit_margin_vs_gaap(page: dict[str, Any]) -> ItemResult:
    mg = _get(page, "anchor", "midcycle_gap")
    if not isinstance(mg, dict):
        return ItemResult(not_run="no anchor.midcycle_gap — it is written only beside a mid-cycle "
                                  "gap the page states")
    gap = _num(mg.get("basis_gap_pts"))
    if mg.get("same_source") or gap is None:
        return one(UNCHECKED)
    return one(CONFIRMED if gap < BASIS_AGREE_PTS else DIFFERS_UNEXPLAINED)


def _market_cap_share_basis(page: dict[str, Any]) -> ItemResult:
    si = _get(page, "mechanical", "stock_info")
    if not isinstance(si, dict):
        return ItemResult(not_run="no stock_info block on the page")
    rc = reconcile_cap(cap_musd=_num(_get(si, "market_cap", "value")),
                       shares=_num(_get(si, "shares_out", "value")),
                       spot=_num(_get(si, "price", "value")))
    if rc is None:
        return one(UNCHECKED)
    # a whole-number ratio IS the stated reason: `reconcile_cap` names it a corporate action
    # between the panels (and `check_freshness` refuses such a build)
    return one(DIFFERS_STATED if rc.corporate_action else CONFIRMED)


def _primary_source_check(page: dict[str, Any], key: str) -> ItemResult:
    ps = _get(page, "mechanical", "primary_source")
    if not isinstance(ps, dict):
        return ItemResult(not_run="no primary_source block on the page")
    # the wall's boundary instrument is the one reason a page states for a divergence here
    return _cross_check(page, ps, key, stated=key == "wall_coherence_check"
                        and ps.get("wall_coherence_near_boundary") is True)


def _guide_vs_release(page: dict[str, Any]) -> ItemResult:
    return _primary_source_check(page, "guide_verification_check")


def _wall_vs_10q(page: dict[str, Any]) -> ItemResult:
    return _primary_source_check(page, "wall_coherence_check")


def _fcf_sign_vs_edgar_ocf(page: dict[str, Any]) -> ItemResult:
    return _primary_source_check(page, "self_funding_check")


def _ev_bridge_vs_ciq_tev(page: dict[str, Any]) -> ItemResult:
    eb = page.get("ev_bridge")
    if not isinstance(eb, dict):
        return ItemResult(not_run="no ev_bridge block on the page")
    claims, ciq = _num(eb.get("claims")), _num(eb.get("ciq_tev_claims"))
    if claims is None or ciq is None:
        return one(UNCHECKED)
    return one(CONFIRMED if abs(claims - ciq) <= EV_BRIDGE_CIQ_TOL else DIFFERS_UNEXPLAINED)


def _net_debt_vs_implied_bridge(page: dict[str, Any]) -> ItemResult:
    ie = _get(page, "mechanical", "valuation", "implied_expectations")
    if not isinstance(ie, dict):
        return ItemResult(not_run="no implied_expectations block on the page")
    # THE STORED FLAG READS TRUE WHEN THE BRIDGE IS ABSENT (`nd_ok = bridge_nd is None or …`), so
    # its outcome is read instead (`net_debt_check`). And the bridge counts only as its two
    # STRUCTURED floats: the producer's `_ie_bridge_net_debt` falls back to parsing the display
    # string, which is no structured second figure (Codex, #792 round 1)
    iv = _get(page, "mechanical", "implied_valuation")
    cash, debt = _num(_get(iv, "bridge_cash")), _num(_get(iv, "bridge_debt"))
    # CIQ'S NET DEBT NETS LONG-TERM MARKETABLE SECURITIES; the comps bridge is debt − cash. Where
    # the gap IS the page's netted line (UBER 2026-10-23: 9,340 − 4,744 = the 4,596 netted, to the
    # dollar), a difference has a stated reason (operator, 2026-10-24). Every figure is a
    # structured one: the comps net debt is the name's own row in the peer grid, the one
    # `mechanical._implied_expectations` builds TEV from.
    nd = next((_num(r.get("net_debt")) for r in _get(page, "mechanical", "peer_comps",
                                                     "peer_grid", "value") or []
               if isinstance(r, dict) and r.get("is_name")), None)
    netted = next((_num(ln.get("value")) for ln in _get(page, "ev_bridge", "lines") or []
                   if isinstance(ln, dict) and ln.get("label") == _NETTED_LABEL), None)
    netting = (cash is not None and debt is not None and nd is not None and bool(netted)
               and abs(debt - cash - nd - (netted or 0.0)) <= EV_BRIDGE_CIQ_TOL)
    r = _cross_check(page, ie, "net_debt_check", stated=netting)
    if r.not_run is None and (cash is None or debt is None):
        return one(UNCHECKED)
    return r


def _forward_multiple_vintage(page: dict[str, Any]) -> ItemResult:
    ie = _get(page, "mechanical", "valuation", "implied_expectations")
    if not isinstance(ie, dict):
        return ItemResult(not_run="no implied_expectations block on the page")
    return _cross_check(page, ie, "vintage_check")


def _multiples_sheet_coherence(page: dict[str, Any]) -> ItemResult:
    bands = _get(page, "mechanical", "valuation", "own_history", "value")
    band = next((b for b in bands or [] if isinstance(b, dict)
                 and str(b.get("metric", "")).startswith("EV/EBITDA")), None)
    if band is None:
        return ItemResult(not_run="no EV/EBITDA own-history band on the page")
    # its margins are persisted on the band only when it ran (`ciq_sheets.own_history_bands`)
    if _num(band.get("implied_d_and_a_margin")) is None:
        return one(UNCHECKED)
    tripped = BAND_INCOHERENT in (band.get("data_quality") or "").split("+")
    return one(DIFFERS_UNEXPLAINED if tripped else CONFIRMED)


def _snapshot_multiple(page: dict[str, Any]) -> ItemResult:
    cm = _get(page, "valuation_basis", "current_multiple")
    if not isinstance(cm, dict):
        return ItemResult(not_applicable="no current multiple on the page (the active recipe is "
                                         "not priceable)")
    if cm.get("metric") != "TEV/EBIT":
        return ItemResult(not_applicable="the active recipe's multiple is not TEV/EBIT — the "
                                         "snapshot test runs on TEV/EBIT only")
    v = cm.get("snapshot_reconciles")
    if v is None:
        return one(UNCHECKED)
    return one(CONFIRMED if v else DIFFERS_UNEXPLAINED)


def _band_check(page: dict[str, Any], key: str) -> ItemResult:
    a = page.get("anchor")
    if not isinstance(a, dict):
        return ItemResult(not_run="no anchor block on the page")
    bc = a.get("band_checks")
    if not isinstance(bc, dict):
        # an anchor writes the block only where it reaches the guards (`compute_anchor`'s R1 path)
        return ItemResult(not_run="no anchor.band_checks — the anchor never reached the band "
                                  "guards (no own-history multiple, an R2 or R4 recipe), or it "
                                  "predates the field and did not reproduce "
                                  "(refresh.band_checks_backfill)")
    return _cross_check(page, bc, key)


def _recorded_d_and_a_vs_edgar(page: dict[str, Any]) -> ItemResult:
    return _band_check(page, "recorded_d_and_a")


def _market_reconciliation(page: dict[str, Any]) -> ItemResult:
    return _band_check(page, "market_reconciliation")


def _currency_stated_usd(page: dict[str, Any]) -> ItemResult:
    cur = _get(page, "mechanical", "ciq_currency")
    if not isinstance(cur, dict):
        return ItemResult(not_run="no ciq_currency on the page — it predates the field, or the "
                                  "back-fill could not prove the folder's exports the page's own "
                                  "(refresh.ciq_currency_transform); assembly writes it")
    c: Counter[str] = Counter()
    for panel in cur.get("panels") or []:
        v = panel.get("check") if isinstance(panel, dict) else None
        if v == CHECK_AGREE:
            c[CONFIRMED] += 1
        elif v == CHECK_DIFFER:
            c[DIFFERS_UNEXPLAINED] += 1
        elif v == CHECK_NOT_RUN:
            c[UNCHECKED] += 1
        else:
            raise ValueError(f"{page.get('ticker')}: a ciq_currency panel's check is {v!r}, not "
                             "an outcome this scorecard knows "
                             f"({[CHECK_AGREE, CHECK_DIFFER, CHECK_NOT_RUN]})")
    if not c:
        return ItemResult(not_run="ciq_currency lists no panel")
    return ItemResult(counts=dict(c))


CHECKS: tuple[Check, ...] = (
    Check("ebitda_vs_xbrl", "CIQ quarterly EBITDA vs the same quarter rebuilt from the filings",
          "CIQ Financials (quarterly) Income Statement 'EBITDA', the four quarters of its LTM",
          "EDGAR XBRL: operating income + D&A (else pre-tax − net interest + D&A)", INDEPENDENT,
          "quarter",
          f"differs beyond {DIFFERENT_SHARE:.0%} of the rebuilt figure AND by at least $1M "
          "(ebitda_recon.DIFFERENT_SHARE) — the page's own `different` flag",
          "pages carrying mechanical.financial_summary.ebitda_reconciliation",
          "the quarter's own release states an amount matching the gap (quoted, not attributed)",
          None, ("wrong_file", "wrong_cell", "wrong_unit", "wrong_period", "different_definition"),
          _ebitda_vs_xbrl),
    Check("revenue_vs_xbrl", "CIQ annual revenue vs the same period from the filings",
          "CIQ Financials (annual) Income Statement 'Total Revenue' — the financial summary's "
          "Revenue row, each fiscal year and the LTM, at the period end CIQ's header states",
          "EDGAR XBRL revenue on the first alias reporting the period (ASC 606 net, gross, "
          "Revenues, SalesRevenueNet), as filed by the page's assembly date; the LTM a twelve-"
          "month fact, else fiscal year + year-to-date − prior year-to-date on one tag",
          INDEPENDENT, "period",
          f"differs beyond {_STMT_SHARE:.1%} of the filing figure AND by at least "
          f"${_STMT_FLOOR:g}M (statement_recon.DIFFERENT_SHARE) — the row's own `different` flag",
          "pages carrying mechanical.financial_summary.statement_reconciliation",
          "the filings carry CIQ's figure themselves: another revenue alias for the same period, "
          "or an earlier filing's figure for the fiscal year (restated since)", None,
          ("wrong_file", "wrong_cell", "wrong_unit", "wrong_period", "different_definition"),
          _revenue_vs_xbrl),
    Check("ocf_vs_xbrl", "CIQ annual operating cash flow vs the same period from the filings",
          "CIQ Financials (annual) Cash Flow 'Cash from Ops.' — the financial summary's CFO row, "
          "each fiscal year and the LTM, at the period end CIQ's header states",
          "EDGAR XBRL NetCashProvidedByUsedInOperatingActivities (else its continuing-operations "
          "tag), as filed by the page's assembly date; the LTM a twelve-month fact, else fiscal "
          "year + year-to-date − prior year-to-date on one tag (a 10-Q tags cash flow "
          "year-to-date)",
          INDEPENDENT, "period",
          f"differs beyond {_STMT_SHARE:.1%} of the filing figure AND by at least "
          f"${_STMT_FLOOR:g}M (statement_recon.DIFFERENT_SHARE) — the row's own `different` flag",
          "pages carrying mechanical.financial_summary.statement_reconciliation",
          "the filings carry CIQ's figure themselves: the other operating-cash-flow alias for the "
          "same period, or an earlier filing's figure for the fiscal year (restated since)", None,
          ("wrong_file", "wrong_cell", "wrong_unit", "wrong_period", "different_definition"),
          _ocf_vs_xbrl),
    Check("lease_rows_vs_edgar", "CIQ's lease rows inside TEV vs EDGAR's operating leases",
          "CIQ 'Curr. Port. of Leases' + 'Long-Term Leases', per balance-sheet date",
          "EDGAR operating-lease liability on the same date (finance leases either side)",
          INDEPENDENT, "balance-sheet date",
          f"within {RECONCILE_TOL:.0%} of EDGAR's figure (lease_basis.RECONCILE_TOL)",
          f"pages whose rent is material (≥{MATERIALITY:.0%} of EBITDA, lease_basis.MATERIALITY)",
          "CIQ's balance sheet as originally filed predates ASC 842; EDGAR's figure is a later "
          "comparative", "dates before ASC 842 on both sides — no operating lease to compare",
          ("wrong_file", "wrong_cell", "wrong_unit", "wrong_period", "different_definition"),
          _lease_rows_vs_edgar),
    Check("rent_vs_edgar_lease_cost", "CIQ's rent vs EDGAR's lease cost, one fiscal year",
          "CIQ annual Income Statement 'Net Rental Exp.'",
          "EDGAR LeaseCost (else OperatingLeaseCost), the same fiscal year", INDEPENDENT, "page",
          f"within {_RENT_DISAGREE:g}x either way (lease_basis.rent_disagrees) — a loose band",
          "pages carrying mechanical.valuation.lease_basis", None, None,
          ("wrong_file", "wrong_cell", "wrong_unit"),
          _rent_vs_edgar_lease_cost),
    Check("ebit_margin_vs_gaap", "CIQ EBIT margin vs EDGAR GAAP operating margin, one fiscal year",
          "CIQ annual EBIT ÷ revenue (financial_summary actual columns)",
          "EDGAR GAAP operating income ÷ revenue (R1's own margin series)", INDEPENDENT, "page",
          f"under {BASIS_AGREE_PTS:g} points apart (anchor.BASIS_AGREE_PTS)",
          f"pages carrying anchor.midcycle_gap — written only where the twelve months sit "
          f"≥{MIDCYCLE_GAP_PTS:g} points from R1's median (anchor.MIDCYCLE_GAP_PTS), so a "
          "conditional sample, not the fleet", None, None,
          ("wrong_file", "wrong_cell", "different_definition"),
          _ebit_margin_vs_gaap),
    Check("market_cap_share_basis", "CIQ market cap vs EDGAR shares × the EOD close",
          "CIQ Comparable Analysis 'Market Capitalization'",
          "EDGAR point-in-time shares outstanding × the page's EOD close", INDEPENDENT, "page",
          f"SHARE BASIS ONLY: a ratio within {_INTEGER_TOLERANCE:.0%} of a whole number ≥2 is a "
          "corporate action between panels (freshness.reconcile_cap). Price drift between CIQ's "
          "cap date and the close is NOT tested — no tolerance is defined for it",
          "every page", "a whole-number ratio: a share-basis mismatch between panels", None,
          ("wrong_unit", "wrong_period"),
          _market_cap_share_basis),
    Check("guide_vs_release", "CIQ's revenue guide vs the 8-K release's guide",
          "CIQ Estimates→Guidance revenue guide, the latest (a point or a range)",
          "the 8-K EX-99.1 releases' revenue guide (release_parse)", INDEPENDENT, "page",
          f"both bounds within {GUIDE_MATCH:g}, absolute (primary_source.GUIDE_MATCH) — the "
          "page's guide_verification_check. Compared only where both sides guide a LEVEL for the "
          "same period scope: a change guide, another period, a release with no number and the "
          "vendor-echo flag are checks that did not run",
          "pages carrying mechanical.primary_source.guide_verification_check", None, None,
          ("wrong_file", "wrong_cell", "wrong_unit", "wrong_period"),
          _guide_vs_release),
    Check("wall_vs_10q", "CIQ's capital panel vs the 10-Q's maturity wall, one 12-month window",
          "CIQ Financials→Capital Structure Details: principal maturing in [balance, +12m)",
          "the latest 10-Q's stated maturities within 12 months (filing_sections.maturity_wall)",
          INDEPENDENT, "page",
          f"within {_WALL_TOL:.0%} of the filing's figure (primary_source.wall_coherence) — "
          "principal against repayment basis, both labelled on the page's line. Run only where "
          "the 10-Q states a 12-month figure",
          "pages carrying mechanical.primary_source.wall_coherence_check",
          f"an instrument matures within ±{BOUNDARY_DAYS}d of the window's +12m boundary — a "
          "possible window-convention artifact (wall_coherence_near_boundary)", None,
          ("wrong_file", "wrong_cell", "wrong_unit", "wrong_period"),
          _wall_vs_10q),
    Check("fcf_sign_vs_edgar_ocf", "The SIGN of CIQ's LTM FCF vs the sign of EDGAR's latest OCF",
          "CIQ Financials→Cash Flow 'Levered Free Cash Flow', latest period — its sign",
          "EDGAR XBRL operating cash flow, the latest single quarter — its sign", INDEPENDENT,
          "page",
          "SIGN ONLY, of two different measures (primary_source.self_funding_check): agree when "
          "the signs match, both negative included. A differ is mostly capex or seasonality, not "
          "by itself a CIQ error",
          "pages carrying mechanical.primary_source.self_funding_check", None, None,
          ("wrong_file", "wrong_cell"),
          _fcf_sign_vs_edgar_ocf),
    Check("ev_bridge_vs_ciq_tev", "CIQ balance-sheet claims vs CIQ's own TEV less market cap",
          "CIQ Financials Balance Sheet Net Debt + preferred + minority (ev_bridge.claims)",
          "CIQ Comparable Analysis TEV − market cap (ev_bridge.ciq_tev_claims)", INTERNAL, "page",
          f"within ${EV_BRIDGE_CIQ_TOL:g}M (ciq_sheets.EV_BRIDGE_CIQ_TOL) — read from the "
          "top-level ev_bridge on every page, not valuation_basis.ev_bridge."
          "reconciles_to_ciq_tev, which is None by design wherever the recipe's bridge is not "
          "CIQ's",
          "pages carrying ev_bridge", None, None, ("wrong_cell", "wrong_unit", "wrong_period"),
          _ev_bridge_vs_ciq_tev),
    Check("net_debt_vs_implied_bridge", "CIQ comps net debt vs the comps cash/debt bridge",
          "CIQ Comparable Analysis Financial Data net debt (the TEV build)",
          "CIQ Comparable Analysis Implied Valuation: total debt − cash", INTERNAL, "page",
          f"within {_IE_TOL:.0%} of the net debt (mechanical._net_debt_probe) — the page's "
          "net_debt_check, never its net_debt_reconciled flag, which also reads True with no "
          "bridge; counted only where the bridge's structured bridge_cash and bridge_debt both "
          "exist",
          "pages carrying mechanical.valuation.implied_expectations",
          f"the gap is CIQ netting long-term marketable securities: debt − cash − comps net debt "
          f"equals the page's netted line (ev_bridge) within ${EV_BRIDGE_CIQ_TOL:g}M", None,
          ("wrong_cell", "wrong_unit"),
          _net_debt_vs_implied_bridge),
    Check("multiples_sheet_coherence",
          "CIQ's TEV/LTM EBITDA row vs its own EBIT and revenue rows, one column",
          "CIQ Financials Multiples 'TEV/LTM EBITDA' at the latest column all three rows report",
          "the same column's 'TEV/LTM EBIT' and 'TEV/LTM Total Revenue' (TEV cancels)", INTERNAL,
          "page",
          f"implied D&A neither negative nor above {_MAX_IMPLIED_DA_MARGIN:.0%} of revenue "
          "(band_guards.sheet_coherence) — the band's band_incoherent flag",
          "pages carrying an EV/EBITDA own-history band", None, None,
          ("wrong_cell", "different_definition"),
          _multiples_sheet_coherence),
    Check("snapshot_multiple", "CIQ forward TEV/EBIT struck at the page's CIQ snapshot",
          "CIQ Estimates FY TEV/EBIT × that year's EBIT consensus",
          "CIQ market cap + CIQ claims (comps)", INTERNAL, "page",
          f"within {SNAPSHOT_TOL:.1%} (valuation_basis.SNAPSHOT_TOL) — the page's "
          "snapshot_reconciles",
          "pages whose active recipe prices TEV/EBIT", None, None, ("wrong_file", "wrong_period"),
          _snapshot_multiple),
    Check("forward_multiple_vintage",
          "CIQ's FY 2026 forward multiple at CIQ's TEV vs CIQ's FY 2026 EBITDA consensus",
          "CIQ Estimates→Multiples FY 2026 TEV/EBITDA, as comps TEV ÷ multiple (the EBITDA the "
          "ladder implies)",
          "CIQ Estimates→Trends FY 2026 EBITDA consensus, latest snapshot", INTERNAL, "page",
          f"residual within {_IE_TOL:.0%} of the consensus (mechanical._vintage_probe) — the "
          "page's vintage_check, never its vintage_coherent flag, which also reads True when the "
          "probe cannot run",
          "pages carrying mechanical.valuation.implied_expectations.vintage_check — FY 2026 "
          "only, so a name that has reported FY 2026, or has no positive consensus for it, "
          "cannot run it", None, None,
          ("wrong_file", "wrong_unit", "wrong_period"),
          _forward_multiple_vintage),
    Check("recorded_d_and_a_vs_edgar",
          "The D&A CIQ's Multiples sheet implies vs the D&A the filer recorded",
          "CIQ Financials→Multiples: the implied D&A margin of one column (TEV/LTM EBITDA against "
          "TEV/LTM EBIT and TEV/LTM Total Revenue) × the anchor's LTM revenue",
          "EDGAR XBRL depreciation and amortisation, latest fiscal year (the anchor's d_and_a)",
          INDEPENDENT, "page",
          f"within {_MAX_DA_RATIO:g}x either way (band_guards.recorded_d_and_a_check) — an "
          "order-of-magnitude screen, the anchor's band_checks. Not run on the ex-lease history, "
          "which carries no implied D&A margin",
          "pages whose anchor reached the band guards (anchor.band_checks)", None, None,
          ("wrong_file", "wrong_cell", "wrong_unit", "different_definition"),
          _recorded_d_and_a_vs_edgar),
    Check("market_reconciliation",
          "The EBITDA the multiple R1 prices implies vs the EBITDA recorded",
          "the current EV/EBITDA multiple of the band R1 prices (CIQ's, or the ex-lease rebuild)",
          "(CIQ comps market cap + the anchor's EDGAR net debt) ÷ that multiple, against CIQ's "
          "LTM EBIT + EDGAR D&A", INTERNAL, "page",
          f"within {_MAX_MARKET_RATIO:g}x either way (band_guards.market_reconciliation) — an "
          "order-of-magnitude screen, the anchor's band_checks. INTERNAL: CIQ figures sit on "
          "both sides, with EDGAR's net debt and D&A in the legs",
          "pages whose anchor reached the band guards (anchor.band_checks)", None, None,
          ("wrong_cell", "wrong_unit", "different_definition"),
          _market_reconciliation),
    Check("currency_stated_usd",
          "The currency each CIQ money panel states vs the USD the page reads it in",
          "the currency each CIQ money panel states where the page reads it: the Financials' "
          "per-column 'Currency' row and 'Principal Due (…)' header, the Estimates' section "
          "headers (Company Level and the name's own listing), the comps book's 'Currency:' label",
          "the page's own unit — every CIQ money figure is read as USD ($M); a convention, not a "
          "figure from another source", INTERNAL, "panel",
          f"exact: every currency the panel states is one of {sorted(USD_STATED)} "
          "(ciq_sheets.USD_STATED); one stating another differs, one stating none is unchecked. "
          "CURRENCY ONLY — the scale ('In Millions of …') is not read. A panel stating another "
          "currency is refused before assembly (ciq_sheets.require_usd), so a built page differs "
          "only where a back-fill found one",
          "pages carrying mechanical.ciq_currency — one unit per money panel the folder holds",
          None, None, ("wrong_unit",), _currency_stated_usd),
)
CHECK_IDS = tuple(c.id for c in CHECKS)


# --- the coverage map: every CIQ workbook kind the loader knows has a family --------------------


def _consensus_identities(pages: dict[str, dict[str, Any]]) -> dict[str, int]:
    rows = {t: len(_get(p, "forward_consensus", "reconciliations") or []) for t, p in pages.items()}
    return {"pages_with_identity_rows": sum(1 for n in rows.values() if n),
            "identity_rows": sum(rows.values())}


FAMILIES: tuple[Family, ...] = (
    Family("financials.quarterly_ebitda", "financials",
           ("Financials→Income Statement",), "quarterly EBITDA — the LTM every EV/EBITDA divides",
           checks=("ebitda_vs_xbrl", "currency_stated_usd"),
           note="a difference is mostly CIQ's normalisation by design (it leaves out items it "
                "treats as unusual — ebitda_recon), so 'differs' is not by itself a CIQ error"),
    Family("financials.annual_income_statement", "financials",
           ("Financials→Income Statement",), "revenue, EBIT, EPS in the Financial Summary",
           checks=("revenue_vs_xbrl", "ebit_margin_vs_gaap", "currency_stated_usd"),
           note="revenue is set against the filings per fiscal year and the LTM; the EBIT margin "
                "only on the conditional sample its check names; EBIT and EPS themselves are not "
                "set against the filings"),
    Family("financials.rent", "financials", ("Financials→Income Statement",),
           "'Net Rental Exp.' — the lease-materiality reading",
           checks=("rent_vs_edgar_lease_cost", "currency_stated_usd")),
    Family("financials.balance_sheet_claims", "financials", ("Financials→Balance Sheet",),
           "Net Debt, Total Debt, cash, preferred, minority — the EV bridge",
           checks=("ev_bridge_vs_ciq_tev", "currency_stated_usd"),
           unscored=("ciq_balance.extract — the UNIT (scale) check against revenue, D&A "
                     "containment and the net-debt cross-read; runs only in anchor-backfill / "
                     "anchor-retag on the raw workbooks, and its result is printed, never stored "
                     "on the page",),
           note="EDGAR's net debt sits beside the bridge (ev_bridge.edgar_net_debt) on another "
                "basis and is never compared — no tolerance is defined across the two"),
    Family("financials.lease_rows", "financials",
           ("Financials→Balance Sheet", "Financials→Historical Capitalization"),
           "the operating leases inside CIQ's TEV",
           checks=("lease_rows_vs_edgar", "currency_stated_usd")),
    Family("financials.tev_history", "financials",
           ("Financials→Historical Capitalization", "Financials→Multiples"),
           "TEV by quarter and the trailing multiple bands",
           checks=("multiples_sheet_coherence", "recorded_d_and_a_vs_edgar",
                   "market_reconciliation", "currency_stated_usd"),
           note="the lease component is lease_rows_vs_edgar; TEV and the band's closes are not "
                "rebuilt from another source"),
    Family("financials.cash_flow", "financials", ("Financials→Cash Flow",),
           "operating cash flow, capex, free cash flow",
           checks=("ocf_vs_xbrl", "fcf_sign_vs_edgar_ocf", "currency_stated_usd"),
           note="operating cash flow is set against the filings per fiscal year and the LTM; "
                "capex and the levered FCF figure are not — the FCF reaches the filings only as a "
                "SIGN against a different measure, and a quarter's OCF and a year's levered FCF "
                "differ in sign for ordinary reasons (capex, seasonality)"),
    Family("financials.capital_structure", "financials",
           ("Financials→Capital Structure Details", "Financials→Capital Structure Summary"),
           "debt instruments and maturities", checks=("wall_vs_10q", "currency_stated_usd"),
           note="run only where the 10-Q states a 12-month maturity figure; the rest of the panel "
                "(coupons, the later maturities) is not set against the filings"),
    Family("financials.segments", "financials", ("Financials→Segments",), "segment revenue",
           checks=("currency_stated_usd",),
           note="internal on the currency the panel states, and nothing else; segment profit on "
                "the filer's measure comes from XBRL separately "
                "(mechanical.concentration.segment_profit) and is not set against CIQ's segments"),
    Family("financials.ratios", "financials", ("Financials→Ratios",), "CIQ's computed ratios"),
    Family("estimates.consensus", "estimates",
           ("Estimates→Consensus", "Estimates→Trends", "Estimates→Revisions",
            "Estimates→Recent Changes"), "forward consensus paths, spreads and revisions",
           checks=("currency_stated_usd",), fallback=SINGLE_SOURCE,
           note="internal on the currency the Consensus and Trends panels state, and nothing "
                "else: no second consensus source; forward_consensus.reconciliations sets "
                "identities (CFO − CapEx vs FCF, EBIT + D&A vs EBITDA) against the same means — "
                "information, "
                "not a pass/fail, by the schema's own rule, so they are counted, not scored",
           counted=_consensus_identities),
    Family("estimates.forward_multiples", "estimates", ("Estimates→Multiples",),
           "the NTM multiples a recipe prices",
           checks=("snapshot_multiple", "forward_multiple_vintage")),
    Family("estimates.guidance", "estimates", ("Estimates→Guidance",), "CIQ's record of guidance",
           checks=("guide_vs_release", "currency_stated_usd"),
           note="the revenue guide only; CIQ's other guided metrics are not set against the "
                "releases"),
    Family("estimates.surprise", "estimates", ("Estimates→Surprise",),
           "final consensus against CIQ's actual, per completed year",
           checks=("currency_stated_usd",),
           note="internal on the currency the panel states, and nothing else: the actuals are "
                "CIQ's own and are not set against the filings"),
    Family("comps.market_cap", "comps", ("Comparable Analysis→Financial Data",),
           "market capitalization", checks=("market_cap_share_basis", "currency_stated_usd"),
           note="share basis only — see the check's tolerance"),
    Family("comps.tev_net_debt", "comps",
           ("Comparable Analysis→Financial Data", "Comparable Analysis→Implied Valuation"),
           "TEV, net debt and the cash/debt bridge",
           checks=("ev_bridge_vs_ciq_tev", "net_debt_vs_implied_bridge", "currency_stated_usd")),
    Family("comps.peer_grid", "comps",
           ("Comparable Analysis→Trading Multiples", "Comparable Analysis→Operating Statistics"),
           "the peer multiples and operating statistics", fallback=SINGLE_SOURCE),
    Family("comps.credit_health", "comps", ("Comparable Analysis→Credit Health Panel",),
           "S&P-MI credit-health scores, name against peers", fallback=SINGLE_SOURCE,
           note="the scale DIRECTION is verified before rendering (credit_health_panels."
                "scale_basis); the scores themselves have no second source"),
    Family("credit_health.standalone", "credit_health", ("Credit Health Panel export→Summary",),
           "the same scores ranked within the GICS industry", fallback=SINGLE_SOURCE),
    Family("comps.description", "comps", ("Comparable Analysis→Business Description",),
           "the business description", fallback=SINGLE_SOURCE),
    Family("profile.classification", "profile",
           ("Public Company Profile→Primary Industry Classification",), "the industry class",
           fallback=SINGLE_SOURCE),
    Family("text.transcripts", "transcript", (), "earnings-call passages", fallback=SINGLE_SOURCE,
           note="quoted verbatim with the file named — the quote is the source"),
    Family("text.key_developments", "key_developments", (), "key-development items",
           fallback=SINGLE_SOURCE, note="quoted verbatim with the file named"),
    Family("text.customers", "customers", (), "CIQ's business-relationship lists",
           fallback=SINGLE_SOURCE),
    Family("charting", "charting", (), "peer time series (theme work, not the dossier pages)",
           fallback=SINGLE_SOURCE),
)



# --- what it reads ------------------------------------------------------------------------------

READS = "data/dossiers/*/dossier.json"


def load_pages(root: Path) -> dict[str, dict[str, Any]]:
    """Every committed page under ``root/data/dossiers``, by ticker."""
    ddir = root / "data" / "dossiers"
    out: dict[str, dict[str, Any]] = {}
    for f in sorted(ddir.glob("*/dossier.json")) if ddir.is_dir() else []:
        t = f.parent.name.upper()
        if t in out:      # two folders one ticker apart only in case — never keep one silently
            raise ValueError(f"two dossier folders for {t} under {ddir}")
        out[t] = json.loads(f.read_text())
    return out


def dossier_set_sha256(root: Path) -> str:
    """One hash over the page set — ticker and file bytes, in ticker order — so a snapshot names
    the exact pages it counted even where the working tree differs from the commit."""
    h = hashlib.sha256()
    for f in sorted((root / "data" / "dossiers").glob("*/dossier.json")):
        h.update(f.parent.name.upper().encode() + b"\n")
        h.update(hashlib.sha256(f.read_bytes()).hexdigest().encode() + b"\n")
    return h.hexdigest()


def corpus(pages: dict[str, dict[str, Any]], sha256: str) -> Corpus:
    return Corpus(items=pages, reads=READS, item_noun="page", sha256=sha256,
                  tracked=("data/dossiers",))


def load(root: Path) -> Corpus:
    """ONE read of each page: the bytes hashed are the bytes scored."""
    ddir = root / "data" / "dossiers"
    pages: dict[str, dict[str, Any]] = {}
    h = hashlib.sha256()
    for f in sorted(ddir.glob("*/dossier.json")) if ddir.is_dir() else []:
        t, raw = f.parent.name.upper(), f.read_bytes()
        if t in pages:    # two folders one ticker apart only in case — never keep one silently
            raise ValueError(f"two dossier folders for {t} under {ddir}")
        pages[t] = json.loads(raw)
        h.update(t.encode() + b"\n" + hashlib.sha256(raw).hexdigest().encode() + b"\n")
    return corpus(pages, h.hexdigest())


SOURCE = Source(
    id="ciq", title="CIQ",
    reads_note="reads the committed pages only, never the licensed workbooks",
    load=load, checks=CHECKS, families=FAMILIES)
