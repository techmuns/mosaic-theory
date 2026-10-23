"""CIQ DATA-QUALITY SCORECARD — one dated, fleet-wide answer to "is the CIQ data credible?".

WHY (2026-10-23). The checks existed and each page carried its own: CIQ's quarterly EBITDA against
the filings, the lease rows inside CIQ's TEV against EDGAR's operating leases, the EV bridge against
CIQ's own TEV, market cap against shares × price. But the results sat page by page — 27 pages each
holding their own — with no fleet view and no series over time. This module reads the COMMITTED
pages only (`data/dossiers/*/dossier.json`), never the licensed workbooks, so it runs in every
checkout and in CI.

FOUR STATUSES, per UNIT (a quarter, a balance-sheet date, a page — named per check):

* ``confirmed`` — a second figure agrees within the check's OWN tolerance (the constant the page
  is built with, imported here, never re-typed);
* ``differs_stated`` — they differ, and the page carries a reason for THAT unit (EBITDA: the
  quarter's release states a matching amount; leases: CIQ's balance sheet predates the standard);
* ``differs_unexplained`` — they differ, and nothing on the page says why;
* ``unchecked`` — the unit exists but has no second figure to compare.

A page where a check never ran is ``not_run`` (its block is absent, so its units are unknown), and
one it does not apply to is ``not_applicable``. Neither is folded into ``unchecked``: "no second
figure" and "never looked" are different facts, and summing them would make the second look like
the first.

INDEPENDENCE IS NAMED PER CHECK. ``independent``: the second figure is not CIQ's (EDGAR XBRL, the
EOD close). ``internal``: it is another CIQ export. An internal agreement shows the sheets were read
coherently and the pulls match — never that CIQ is right.

WHERE A PAGE STORES A VERDICT, IT IS READ; WHERE IT STORES ONLY THE INPUTS, THE PRODUCER'S OWN
CONSTANT IS APPLIED (`EV_BRIDGE_CIQ_TOL`, `reconcile_cap`, `rent_disagrees`). Nothing is re-decided.

STRUCTURED VALUES ONLY. A verdict that exists only as display text (guide verification, wall
coherence, the vintage probe) is listed in the coverage map as UNSCORED, with its path — never
parsed here.

COUNTS AND STATUSES ONLY. The repo is public (2026-10-22): no CIQ figure, gap or quote enters the
snapshot. The tolerances are this repo's constants, not CIQ data.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vinci.dossier.anchor import BASIS_AGREE_PTS, MIDCYCLE_GAP_PTS
from vinci.dossier.band_guards import _MAX_IMPLIED_DA_MARGIN, BAND_INCOHERENT
from vinci.dossier.ciq_sheets import EV_BRIDGE_CIQ_TOL
from vinci.dossier.ebitda_recon import DIFFERENT_SHARE
from vinci.dossier.freshness import _INTEGER_TOLERANCE, reconcile_cap
from vinci.dossier.lease_basis import (
    _RENT_DISAGREE,
    MATERIALITY,
    RECONCILE_TOL,
    rent_disagrees,
)
from vinci.dossier.mechanical import _ie_bridge_net_debt
from vinci.dossier.schemas import ImpliedValuation
from vinci.dossier.valuation_basis import SNAPSHOT_TOL

SCHEMA = "ciq_quality/1"
CONFIRMED = "confirmed"
DIFFERS_STATED = "differs_stated"
DIFFERS_UNEXPLAINED = "differs_unexplained"
UNCHECKED = "unchecked"
STATUSES: tuple[str, ...] = (CONFIRMED, DIFFERS_STATED, DIFFERS_UNEXPLAINED, UNCHECKED)
STATUS_MEANING: dict[str, str] = {
    CONFIRMED: "a second figure agrees within the check's own tolerance",
    DIFFERS_STATED: "they differ, and the page states a reason for that unit",
    DIFFERS_UNEXPLAINED: "they differ, and nothing on the page says why",
    UNCHECKED: "the unit exists but has no second figure to compare",
}
INDEPENDENT = "independent"
INTERNAL = "internal"
SINGLE_SOURCE = "single_source"
UNVERIFIED = "unchecked"
#: The coverage classes, in the order a reader trusts them.
COVERAGE_MEANING: dict[str, str] = {
    INDEPENDENT: "a non-CIQ figure (EDGAR XBRL, the EOD close) is compared and a verdict stored",
    INTERNAL: "compared only against another CIQ export — coherence, not correctness",
    SINGLE_SOURCE: "no second source exists among this repo's inputs",
    UNVERIFIED: "a second source exists in principle; no structured verdict is on the page",
}
#: The lease-observation statuses `lease_basis.observations` writes. Any other is a new state this
#: scorecard has not been taught — it raises rather than drop out of the count.
_LEASE_STATUSES = frozenset({"reconciled", "unreconciled", "unchecked", "pre-adoption"})


@dataclass(frozen=True)
class PageResult:
    """One check on one page: units by status, or why there are none."""

    counts: dict[str, int] = field(default_factory=dict)
    excluded: int = 0                      # units the check's own rule leaves out (named per check)
    not_run: str | None = None
    not_applicable: str | None = None


@dataclass(frozen=True)
class Check:
    id: str
    title: str
    ciq_side: str
    second_source: str
    independence: str
    unit: str
    tolerance: str
    population: str
    stated_reason: str | None
    excluded_rule: str | None
    run: Callable[[dict[str, Any]], PageResult]


def _get(d: Any, *path: str) -> Any:
    for k in path:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _num(x: Any) -> float | None:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _one(status: str) -> PageResult:
    return PageResult(counts={status: 1})


# --- the checks ---------------------------------------------------------------------------------


def _ebitda_vs_xbrl(page: dict[str, Any]) -> PageResult:
    er = _get(page, "mechanical", "financial_summary", "ebitda_reconciliation")
    if not isinstance(er, dict):
        return PageResult(not_run="no ebitda_reconciliation block on the page")
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
    return PageResult(counts=dict(c))


def _lease_rows_vs_edgar(page: dict[str, Any]) -> PageResult:
    lb = _get(page, "mechanical", "valuation", "lease_basis")
    if not isinstance(lb, dict):
        return PageResult(not_run="no lease_basis block on the page")
    if not lb.get("material"):
        return PageResult(not_applicable="rent below the materiality line — the page keeps CIQ's "
                                         "history and never splits the leases out")
    obs = lb.get("observations") or []
    if not obs:
        return PageResult(not_run="lease basis material but no observations (the page states "
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
    return PageResult(counts=dict(c), excluded=excluded)


def _rent_vs_edgar_lease_cost(page: dict[str, Any]) -> PageResult:
    lb = _get(page, "mechanical", "valuation", "lease_basis")
    if not isinstance(lb, dict):
        return PageResult(not_run="no lease_basis block on the page")
    rent, cost = _num(lb.get("rent_expense")), _num(lb.get("edgar_lease_cost"))
    verdict = rent_disagrees(rent, cost) if rent is not None and cost is not None else None
    if verdict is None:
        return _one(UNCHECKED)
    return _one(DIFFERS_UNEXPLAINED if verdict else CONFIRMED)


def _ebit_margin_vs_gaap(page: dict[str, Any]) -> PageResult:
    mg = _get(page, "anchor", "midcycle_gap")
    if not isinstance(mg, dict):
        return PageResult(not_run="no anchor.midcycle_gap — it is written only beside a mid-cycle "
                                  "gap the page states")
    gap = _num(mg.get("basis_gap_pts"))
    if mg.get("same_source") or gap is None:
        return _one(UNCHECKED)
    return _one(CONFIRMED if gap < BASIS_AGREE_PTS else DIFFERS_UNEXPLAINED)


def _market_cap_share_basis(page: dict[str, Any]) -> PageResult:
    si = _get(page, "mechanical", "stock_info")
    if not isinstance(si, dict):
        return PageResult(not_run="no stock_info block on the page")
    rc = reconcile_cap(cap_musd=_num(_get(si, "market_cap", "value")),
                       shares=_num(_get(si, "shares_out", "value")),
                       spot=_num(_get(si, "price", "value")))
    if rc is None:
        return _one(UNCHECKED)
    # a whole-number ratio IS the stated reason: `reconcile_cap` names it a corporate action
    # between the panels (and `check_freshness` refuses such a build)
    return _one(DIFFERS_STATED if rc.corporate_action else CONFIRMED)


def _ev_bridge_vs_ciq_tev(page: dict[str, Any]) -> PageResult:
    eb = page.get("ev_bridge")
    if not isinstance(eb, dict):
        return PageResult(not_run="no ev_bridge block on the page")
    claims, ciq = _num(eb.get("claims")), _num(eb.get("ciq_tev_claims"))
    if claims is None or ciq is None:
        return _one(UNCHECKED)
    return _one(CONFIRMED if abs(claims - ciq) <= EV_BRIDGE_CIQ_TOL else DIFFERS_UNEXPLAINED)


def _net_debt_vs_implied_bridge(page: dict[str, Any]) -> PageResult:
    ie = _get(page, "mechanical", "valuation", "implied_expectations")
    if not isinstance(ie, dict):
        return PageResult(not_run="no implied_expectations block on the page")
    iv = _get(page, "mechanical", "implied_valuation")
    # THE STORED FLAG READS TRUE WHEN THE BRIDGE IS ABSENT (`nd_ok = bridge_nd is None or …`), so
    # it is never taken alone: the bridge is re-read through the producer's own function first
    bridge = (_ie_bridge_net_debt(ImpliedValuation.model_validate(iv))
              if isinstance(iv, dict) else None)
    if bridge is None:
        return _one(UNCHECKED)
    return _one(CONFIRMED if ie.get("net_debt_reconciled") else DIFFERS_UNEXPLAINED)


def _multiples_sheet_coherence(page: dict[str, Any]) -> PageResult:
    bands = _get(page, "mechanical", "valuation", "own_history", "value")
    band = next((b for b in bands or [] if isinstance(b, dict)
                 and str(b.get("metric", "")).startswith("EV/EBITDA")), None)
    if band is None:
        return PageResult(not_run="no EV/EBITDA own-history band on the page")
    # its margins are persisted on the band only when it ran (`ciq_sheets.own_history_bands`)
    if _num(band.get("implied_d_and_a_margin")) is None:
        return _one(UNCHECKED)
    tripped = BAND_INCOHERENT in (band.get("data_quality") or "").split("+")
    return _one(DIFFERS_UNEXPLAINED if tripped else CONFIRMED)


def _snapshot_multiple(page: dict[str, Any]) -> PageResult:
    cm = _get(page, "valuation_basis", "current_multiple")
    if not isinstance(cm, dict):
        return PageResult(not_applicable="no current multiple on the page (the active recipe is "
                                         "not priceable)")
    if cm.get("metric") != "TEV/EBIT":
        return PageResult(not_applicable="the active recipe's multiple is not TEV/EBIT — the "
                                         "snapshot test runs on TEV/EBIT only")
    v = cm.get("snapshot_reconciles")
    if v is None:
        return _one(UNCHECKED)
    return _one(CONFIRMED if v else DIFFERS_UNEXPLAINED)


CHECKS: tuple[Check, ...] = (
    Check("ebitda_vs_xbrl", "CIQ quarterly EBITDA vs the same quarter rebuilt from the filings",
          "CIQ Financials (quarterly) Income Statement 'EBITDA', the four quarters of its LTM",
          "EDGAR XBRL: operating income + D&A (else pre-tax − net interest + D&A)", INDEPENDENT,
          "quarter",
          f"differs beyond {DIFFERENT_SHARE:.0%} of the rebuilt figure "
          "(ebitda_recon.DIFFERENT_SHARE) — the page's own `different` flag",
          "pages carrying mechanical.financial_summary.ebitda_reconciliation",
          "the quarter's own release states an amount matching the gap (quoted, not attributed)",
          None, _ebitda_vs_xbrl),
    Check("lease_rows_vs_edgar", "CIQ's lease rows inside TEV vs EDGAR's operating leases",
          "CIQ 'Curr. Port. of Leases' + 'Long-Term Leases', per balance-sheet date",
          "EDGAR operating-lease liability on the same date (finance leases either side)",
          INDEPENDENT, "balance-sheet date",
          f"within {RECONCILE_TOL:.0%} of EDGAR's figure (lease_basis.RECONCILE_TOL)",
          f"pages whose rent is material (≥{MATERIALITY:.0%} of EBITDA, lease_basis.MATERIALITY)",
          "CIQ's balance sheet as originally filed predates ASC 842; EDGAR's figure is a later "
          "comparative", "dates before ASC 842 on both sides — no operating lease to compare",
          _lease_rows_vs_edgar),
    Check("rent_vs_edgar_lease_cost", "CIQ's rent vs EDGAR's lease cost, one fiscal year",
          "CIQ annual Income Statement 'Net Rental Exp.'",
          "EDGAR LeaseCost (else OperatingLeaseCost), the same fiscal year", INDEPENDENT, "page",
          f"within {_RENT_DISAGREE:g}x either way (lease_basis.rent_disagrees) — a loose band",
          "pages carrying mechanical.valuation.lease_basis", None, None,
          _rent_vs_edgar_lease_cost),
    Check("ebit_margin_vs_gaap", "CIQ EBIT margin vs EDGAR GAAP operating margin, one fiscal year",
          "CIQ annual EBIT ÷ revenue (financial_summary actual columns)",
          "EDGAR GAAP operating income ÷ revenue (R1's own margin series)", INDEPENDENT, "page",
          f"under {BASIS_AGREE_PTS:g} points apart (anchor.BASIS_AGREE_PTS)",
          f"pages carrying anchor.midcycle_gap — written only where the twelve months sit "
          f"≥{MIDCYCLE_GAP_PTS:g} points from R1's median (anchor.MIDCYCLE_GAP_PTS), so a "
          "conditional sample, not the fleet", None, None, _ebit_margin_vs_gaap),
    Check("market_cap_share_basis", "CIQ market cap vs EDGAR shares × the EOD close",
          "CIQ Comparable Analysis 'Market Capitalization'",
          "EDGAR point-in-time shares outstanding × the page's EOD close", INDEPENDENT, "page",
          f"SHARE BASIS ONLY: a ratio within {_INTEGER_TOLERANCE:.0%} of a whole number ≥2 is a "
          "corporate action between panels (freshness.reconcile_cap). Price drift between CIQ's "
          "cap date and the close is NOT tested — no tolerance is defined for it",
          "every page", "a whole-number ratio: a share-basis mismatch between panels", None,
          _market_cap_share_basis),
    Check("ev_bridge_vs_ciq_tev", "CIQ balance-sheet claims vs CIQ's own TEV less market cap",
          "CIQ Financials Balance Sheet Net Debt + preferred + minority (ev_bridge.claims)",
          "CIQ Comparable Analysis TEV − market cap (ev_bridge.ciq_tev_claims)", INTERNAL, "page",
          f"within ${EV_BRIDGE_CIQ_TOL:g}M (ciq_sheets.EV_BRIDGE_CIQ_TOL) — read from the "
          "top-level ev_bridge on every page, not valuation_basis.ev_bridge."
          "reconciles_to_ciq_tev, which is None by design wherever the recipe's bridge is not "
          "CIQ's",
          "pages carrying ev_bridge", None, None, _ev_bridge_vs_ciq_tev),
    Check("net_debt_vs_implied_bridge", "CIQ comps net debt vs the comps cash/debt bridge",
          "CIQ Comparable Analysis Financial Data net debt (the TEV build)",
          "CIQ Comparable Analysis Implied Valuation: total debt − cash", INTERNAL, "page",
          "the page's net_debt_reconciled flag — counted only where the bridge exists, because "
          "the flag also reads True when it does not",
          "pages carrying mechanical.valuation.implied_expectations", None, None,
          _net_debt_vs_implied_bridge),
    Check("multiples_sheet_coherence",
          "CIQ's TEV/LTM EBITDA row vs its own EBIT and revenue rows, one column",
          "CIQ Financials Multiples 'TEV/LTM EBITDA' at the latest column all three rows report",
          "the same column's 'TEV/LTM EBIT' and 'TEV/LTM Total Revenue' (TEV cancels)", INTERNAL,
          "page",
          f"implied D&A neither negative nor above {_MAX_IMPLIED_DA_MARGIN:.0%} of revenue "
          "(band_guards.sheet_coherence) — the band's band_incoherent flag",
          "pages carrying an EV/EBITDA own-history band", None, None,
          _multiples_sheet_coherence),
    Check("snapshot_multiple", "CIQ forward TEV/EBIT struck at the page's CIQ snapshot",
          "CIQ Estimates FY TEV/EBIT × that year's EBIT consensus",
          "CIQ market cap + CIQ claims (comps)", INTERNAL, "page",
          f"within {SNAPSHOT_TOL:.1%} (valuation_basis.SNAPSHOT_TOL) — the page's "
          "snapshot_reconciles",
          "pages whose active recipe prices TEV/EBIT", None, None, _snapshot_multiple),
)
CHECK_IDS = tuple(c.id for c in CHECKS)


# --- the coverage map ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Family:
    """A CIQ field family: where it comes from, what the page carries, and how it is verified."""

    id: str
    kind: str                      # the workbook kind (`vinci.dossier.ciq._WORKBOOK_KEYWORDS`)
    sheets: tuple[str, ...]        # 'Workbook→Sheet' as the pages' source_refs cite them
    carries: str
    checks: tuple[str, ...] = ()   # scored checks (ids in `CHECKS`)
    fallback: str = UNVERIFIED     # the class when no scored check covers it
    unscored: tuple[str, ...] = ()  # checks that run but leave no structured verdict
    note: str = ""


FAMILIES: tuple[Family, ...] = (
    Family("financials.quarterly_ebitda", "financials",
           ("Financials→Income Statement",), "quarterly EBITDA — the LTM every EV/EBITDA divides",
           checks=("ebitda_vs_xbrl",),
           note="a difference is mostly CIQ's normalisation by design (it leaves out items it "
                "treats as unusual — ebitda_recon), so 'differs' is not by itself a CIQ error"),
    Family("financials.annual_income_statement", "financials",
           ("Financials→Income Statement",), "revenue, EBIT, EPS in the Financial Summary",
           checks=("ebit_margin_vs_gaap",),
           note="only the EBIT margin is compared, and only on the conditional sample its check "
                "names; revenue and EPS are not set against the filings"),
    Family("financials.rent", "financials", ("Financials→Income Statement",),
           "'Net Rental Exp.' — the lease-materiality reading",
           checks=("rent_vs_edgar_lease_cost",)),
    Family("financials.balance_sheet_claims", "financials", ("Financials→Balance Sheet",),
           "Net Debt, Total Debt, cash, preferred, minority — the EV bridge",
           checks=("ev_bridge_vs_ciq_tev",),
           unscored=("ciq_balance.extract — the UNIT (scale) check against revenue, D&A "
                     "containment and the net-debt cross-read; runs only in anchor-backfill / "
                     "anchor-retag on the raw workbooks, and its result is printed, never stored "
                     "on the page",),
           note="EDGAR's net debt sits beside the bridge (ev_bridge.edgar_net_debt) on another "
                "basis and is never compared — no tolerance is defined across the two"),
    Family("financials.lease_rows", "financials",
           ("Financials→Balance Sheet", "Financials→Historical Capitalization"),
           "the operating leases inside CIQ's TEV", checks=("lease_rows_vs_edgar",)),
    Family("financials.tev_history", "financials",
           ("Financials→Historical Capitalization", "Financials→Multiples"),
           "TEV by quarter and the trailing multiple bands",
           checks=("multiples_sheet_coherence",),
           unscored=("anchor.data_quality — the recorded-D&A check and the market reconciliation "
                     "(band_guards) leave a flag only when they trip, so a pass and a check that "
                     "could not run read the same",),
           note="the lease component is lease_rows_vs_edgar; TEV and the band's closes are not "
                "rebuilt from another source"),
    Family("financials.cash_flow", "financials", ("Financials→Cash Flow",),
           "operating cash flow, capex, free cash flow",
           unscored=("mechanical.primary_source.self_funding — compares SIGNS with EDGAR, in "
                     "display text only",)),
    Family("financials.capital_structure", "financials",
           ("Financials→Capital Structure Details", "Financials→Capital Structure Summary"),
           "debt instruments and maturities",
           unscored=("mechanical.primary_source.wall_coherence — the 10-Q maturity wall against "
                     "the CIQ panel, verdict in display text only",)),
    Family("financials.segments", "financials", ("Financials→Segments",), "segment revenue",
           note="segment profit on the filer's measure comes from XBRL separately "
                "(mechanical.concentration.segment_profit) and is not set against CIQ's segments"),
    Family("financials.ratios", "financials", ("Financials→Ratios",), "CIQ's computed ratios"),
    Family("estimates.consensus", "estimates",
           ("Estimates→Consensus", "Estimates→Trends", "Estimates→Revisions",
            "Estimates→Recent Changes"), "forward consensus paths, spreads and revisions",
           fallback=SINGLE_SOURCE,
           note="no second consensus source; forward_consensus.reconciliations sets identities "
                "(CFO − CapEx vs FCF, EBIT + D&A vs EBITDA) against the same means — information, "
                "not a pass/fail, by the schema's own rule, so they are counted, not scored"),
    Family("estimates.forward_multiples", "estimates", ("Estimates→Multiples",),
           "the NTM multiples a recipe prices", checks=("snapshot_multiple",),
           unscored=("mechanical.valuation.implied_expectations.vintage_coherent — reads True "
                     "also when the probe cannot run; which it was is in coherence_note text "
                     "only",)),
    Family("estimates.guidance", "estimates", ("Estimates→Guidance",), "CIQ's record of guidance",
           unscored=("mechanical.primary_source.guide_verification — CIQ's revenue guide against "
                     "the 8-K release, verdict in display text only",)),
    Family("estimates.surprise", "estimates", ("Estimates→Surprise",),
           "final consensus against CIQ's actual, per completed year",
           note="the actuals are CIQ's own; they are not set against the filings"),
    Family("comps.market_cap", "comps", ("Comparable Analysis→Financial Data",),
           "market capitalization", checks=("market_cap_share_basis",),
           note="share basis only — see the check's tolerance"),
    Family("comps.tev_net_debt", "comps",
           ("Comparable Analysis→Financial Data", "Comparable Analysis→Implied Valuation"),
           "TEV, net debt and the cash/debt bridge",
           checks=("ev_bridge_vs_ciq_tev", "net_debt_vs_implied_bridge")),
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


def classify(f: Family) -> str:
    """A family's coverage class, DERIVED from its scored checks — never declared beside them."""
    kinds = {c.independence for c in CHECKS if c.id in f.checks}
    if INDEPENDENT in kinds:
        return INDEPENDENT
    if INTERNAL in kinds:
        return INTERNAL
    return f.fallback


def _consensus_identities(pages: dict[str, dict[str, Any]]) -> dict[str, int]:
    rows = {t: len(_get(p, "forward_consensus", "reconciliations") or []) for t, p in pages.items()}
    return {"pages_with_identity_rows": sum(1 for n in rows.values() if n),
            "identity_rows": sum(rows.values())}


# --- the scorecard ------------------------------------------------------------------------------


def load_pages(root: Path) -> dict[str, dict[str, Any]]:
    """Every committed page under ``root/data/dossiers``, by ticker."""
    ddir = root / "data" / "dossiers"
    out: dict[str, dict[str, Any]] = {}
    for f in sorted(ddir.glob("*/dossier.json")) if ddir.is_dir() else []:
        out[f.parent.name.upper()] = json.loads(f.read_text())
    return out


def dossier_set_sha256(root: Path) -> str:
    """One hash over the page set — ticker and file bytes, in ticker order — so a snapshot names
    the exact pages it counted even where the working tree differs from the commit."""
    h = hashlib.sha256()
    for f in sorted((root / "data" / "dossiers").glob("*/dossier.json")):
        h.update(f.parent.name.upper().encode() + b"\n")
        h.update(hashlib.sha256(f.read_bytes()).hexdigest().encode() + b"\n")
    return h.hexdigest()


def _score_check(c: Check, pages: dict[str, dict[str, Any]]) -> dict[str, Any]:
    by_name: dict[str, Any] = {}
    fleet: Counter[str] = Counter()
    excluded = 0
    not_run: dict[str, list[str]] = {}
    not_applicable: dict[str, list[str]] = {}
    for t in sorted(pages):
        r = c.run(pages[t])
        if r.not_run is not None:
            not_run.setdefault(r.not_run, []).append(t)
            by_name[t] = {"not_run": r.not_run}
            continue
        if r.not_applicable is not None:
            not_applicable.setdefault(r.not_applicable, []).append(t)
            by_name[t] = {"not_applicable": r.not_applicable}
            continue
        row = {s: r.counts.get(s, 0) for s in STATUSES}
        if r.excluded:
            row["excluded"] = r.excluded
        by_name[t] = row
        fleet.update(r.counts)
        excluded += r.excluded
    run = [t for t, v in by_name.items() if "not_run" not in v and "not_applicable" not in v]
    totals = {s: fleet.get(s, 0) for s in STATUSES}
    return {
        "id": c.id, "title": c.title, "ciq_side": c.ciq_side, "second_source": c.second_source,
        "independence": c.independence, "unit": c.unit, "tolerance": c.tolerance,
        "population": c.population, "stated_reason": c.stated_reason,
        "excluded_rule": c.excluded_rule,
        "fleet": {"pages": len(pages), "pages_run": len(run), "units": sum(totals.values()),
                  **totals, "excluded": excluded,
                  "pages_not_run": sum(len(v) for v in not_run.values()),
                  "pages_not_applicable": sum(len(v) for v in not_applicable.values())},
        "not_run": [{"reason": k, "tickers": v} for k, v in not_run.items()],
        "not_applicable": [{"reason": k, "tickers": v} for k, v in not_applicable.items()],
        "by_name": by_name,
    }


def scorecard(pages: dict[str, dict[str, Any]], *, measured_on: str, git_head: str | None,
              dossiers_match_head: bool | None, dossier_sha256: str) -> dict[str, Any]:
    """The scorecard: a pure function of the pages plus the boundary stamp it is given."""
    checks = [_score_check(c, pages) for c in CHECKS]
    by_id = {c["id"]: c for c in checks}
    coverage = []
    for f in FAMILIES:
        entry: dict[str, Any] = {
            "family": f.id, "kind": f.kind, "sheets": list(f.sheets), "carries": f.carries,
            "classification": classify(f), "checks": [
                {"id": cid, "independence": by_id[cid]["independence"],
                 "pages_run": by_id[cid]["fleet"]["pages_run"],
                 "units": by_id[cid]["fleet"]["units"],
                 "confirmed": by_id[cid]["fleet"][CONFIRMED]} for cid in f.checks],
            "unscored": list(f.unscored), "note": f.note or None}
        if f.id == "estimates.consensus":
            entry["counted"] = _consensus_identities(pages)
        coverage.append(entry)
    return {
        "schema": SCHEMA,
        "boundary": {
            "measured_on": measured_on, "git_head": git_head,
            "dossiers_match_head": dossiers_match_head,
            "dossier_glob": "data/dossiers/*/dossier.json", "pages": len(pages),
            "tickers": sorted(pages), "dossier_set_sha256": dossier_sha256,
            "reads": "committed pages only — never the licensed workbooks"},
        "statuses": STATUS_MEANING,
        "coverage_classes": COVERAGE_MEANING,
        "checks": checks,
        "coverage": coverage,
    }


# --- rendering ----------------------------------------------------------------------------------

_SHORT = {CONFIRMED: "confirmed", DIFFERS_STATED: "differs (stated)",
          DIFFERS_UNEXPLAINED: "differs (unexplained)", UNCHECKED: "unchecked"}


def _rows(cells: list[str], width: int = 100) -> list[str]:
    """Cells packed into indented lines, never split inside one (a name keeps its counts)."""
    lines: list[str] = []
    for cell in cells:
        if lines and len(lines[-1]) + 2 + len(cell) <= width:
            lines[-1] += "  " + cell
        else:
            lines.append("      " + cell)
    return lines


def render(card: dict[str, Any]) -> str:
    """The scorecard as text. EVERY name is printed — no list here is cut."""
    b = card["boundary"]
    head = b["git_head"] or "UNKNOWN commit"
    match = {True: "", False: " (WORKING TREE DIFFERS FROM IT — the sha256 names the pages read)",
             None: " (whether the working tree matches it is UNKNOWN)"}[b["dossiers_match_head"]]
    out = [f"=== CIQ DATA-QUALITY SCORECARD — {b['measured_on']} · {b['pages']} committed pages "
           f"({b['dossier_glob']}) at {head}{match} ===",
           f"dossier set sha256 {b['dossier_set_sha256']}",
           "reads the committed pages only, never the licensed workbooks; counts and statuses only",
           ""]
    out.append("statuses, per unit:")
    out += [f"  {_SHORT[s]:<22} {m}" for s, m in card["statuses"].items()]
    out.append("")
    for i, c in enumerate(card["checks"], 1):
        f = c["fleet"]
        out.append(f"[{i}] {c['id']} — {c['title']}  ({c['independence'].upper()}; "
                   f"unit: {c['unit']})")
        out.append(f"    CIQ side:      {c['ciq_side']}")
        out.append(f"    second source: {c['second_source']}")
        out.append(f"    tolerance:     {c['tolerance']}")
        out.append(f"    population:    {c['population']}")
        if c["stated_reason"]:
            out.append(f"    stated reason: {c['stated_reason']}")
        out.append(f"    FLEET: {f['units']} {c['unit']}(s) on {f['pages_run']} of {f['pages']} "
                   "pages — " + " · ".join(f"{f[s]} {_SHORT[s]}" for s in STATUSES)
                   + (f" · {f['excluded']} excluded ({c['excluded_rule']})"
                      if f["excluded"] else ""))
        for label, groups in (("not run", c["not_run"]), ("not applicable", c["not_applicable"])):
            for g in groups:
                out.append(f"    {label} on {len(g['tickers'])}: {', '.join(g['tickers'])} — "
                           f"{g['reason']}")
        run = {t: v for t, v in c["by_name"].items()
               if "not_run" not in v and "not_applicable" not in v}
        cells = [f"{t} {'/'.join(str(v[s]) for s in STATUSES)}" for t, v in run.items()]
        out.append("    by name, confirmed/stated/unexplained/unchecked "
                   f"(all {len(run)} pages run):")
        out += _rows(cells)
        out.append("")
    out.append("COVERAGE MAP — how each CIQ field family is verified "
               "(by name: confirmed/stated/unexplained/unchecked above)")
    for k, m in card["coverage_classes"].items():
        out.append(f"  {k:<14} {m}")
    out.append("")
    for e in card["coverage"]:
        checks = "; ".join(f"{x['id']} on {x['pages_run']}/{b['pages']} pages, {x['confirmed']} of "
                           f"{x['units']} confirmed" for x in e["checks"]) or "no scored check"
        out.append(f"  {e['classification'].upper():<14} {e['family']} — {e['carries']}")
        out.append(f"  {'':<14} {checks}")
        for u in e["unscored"]:
            out.append(f"  {'':<14} UNSCORED: {u}")
        if "counted" in e:
            out.append(f"  {'':<14} counted: " + ", ".join(f"{k} {v}"
                                                          for k, v in e["counted"].items()))
        if e["note"]:
            out.append(f"  {'':<14} note: {e['note']}")
    totals = Counter(e["classification"] for e in card["coverage"])
    out.append("")
    out.append(f"{len(card['coverage'])} families: " + " · ".join(
        f"{totals.get(k, 0)} {k}" for k in COVERAGE_MEANING))
    return "\n".join(out)


def snapshot_path(root: Path, measured_on: str) -> Path:
    return root / "data" / "snapshots" / "ciq_quality" / f"{measured_on}.json"
