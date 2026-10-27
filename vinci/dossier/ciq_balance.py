"""CIQ balance-sheet / cash-flow facts — the DEPTH-STAGE fallback when EDGAR cannot supply a bridge.

EDGAR remains first. It is free, primary, and machine-checkable. But XBRL breadth fails in two
shapes this cohort hits repeatedly:

* **Absent** — MVST tags no depreciation at all (neither the combined tag nor the split pair), so
  the anchor's D&A is UNKNOWN and every EBITDA-basis number downstream is unreachable.
* **Stale** — a filer that switched tags leaves the old one frozen. FUBO's combined ``dep_amort``
  last reported **$0.003M in FY2014**; its current split tags sum to ~$38.5M. Preferring the
  combined tag by name rather than by vintage picked the twelve-year-old number (fixed in
  :func:`vinci.dossier.anchor._latest_dep_amort`, pinned there).

CIQ's Financials workbook carries the classified totals a human analyst would read — "Total Debt",
"Total Cash & ST Investments", "Depreciation & Amort., Total" — which is exactly the depth-stage
authority the manual CIQ pull exists to provide.

**But vendor data can be internally wrong, and this module assumes it.** VITL's Multiples sheet
carried a ``TEV/LTM EBITDA`` row computed against a rent-adjusted denominator while its own EBIT row
reconciled to EDGAR exactly. So every extraction here is cross-checked before it is allowed to reach
an anchor, and a failed check refuses rather than degrades:

1. **D&A agreement** — the Cash Flow and Income Statement both carry a depreciation line where the
   filer discloses one. They describe the same year and must agree.
2. **Net-debt agreement** — the Multiples sheet implies an enterprise value; minus market cap that
   is a second, independent read of net debt. It must land near the balance sheet's own total.
3. **UNIT scale** — every monetary figure is asserted to be $M by MAGNITUDE against revenue, not by
   trusting a header. Three separate 1e6 defects have shipped in this repo (the anchor's net debt
   into a $M guard, the R2 engine's equity ÷ raw share count, and the original diluted-shares trap);
   a scale read off a label would be the fourth.

Licensed data never leaves the machine: this module reads the git-ignored workbooks and emits
DERIVED scalars with a source stamp. The workbooks themselves are never committed or logged.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
from vinci.dossier.schemas import (
    CHECK_AGREE,
    CHECK_DIFFER,
    CHECK_NOT_RUN,
    CrossCheck,
    SourceStatus,
)

# --- tolerances (face-validity, never outcome-tuned) -------------------------------------------
# The two sheets are the same filer's own disclosure of the same year, so they should agree closely;
# 20% leaves room for CIQ's "Total" roll-up including amortisation lines the IS states separately.
_DA_TOLERANCE = 0.20
# Net debt cross-read runs through a MARKET cap and a traded multiple, so it inherits their vintage
# spread — a looser band, wide enough that only a structural disagreement trips it.
_ND_TOLERANCE = 0.25
# A monetary figure in $M sits within this factor of revenue-in-$M. Anything outside is a UNIT
# error, not a business fact: no real company holds 10,000x its revenue in cash, or 1e-4 of it.
_SCALE_HI, _SCALE_LO = 1_000.0, 1e-4


class CiqExtractionError(ValueError):
    """A vendor extraction the module refuses to hand on — never a silently degraded fact."""


@dataclass(frozen=True)
class CiqFact:
    """One extracted scalar with the vendor stamp that lets a human re-open the same cell."""

    value: float
    unit: str
    basis: str
    source: str


@dataclass(frozen=True)
class CiqFacts:
    """The balance-sheet bridge, plus the checks that were run on it.

    ``ok`` is False when any coherence check tripped; the caller must then refuse to use the facts
    rather than pick the survivors — a sheet that contradicts itself has not been shown to be
    right in the parts that happen to look reasonable."""

    ticker: str
    as_of: str | None
    source_file: str | None
    source_sha256: str | None
    facts: dict[str, CiqFact] = field(default_factory=dict)
    checks: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    #: (2026-10-27) the UNIT check's outcome as a structured value, beside its lines: agree when
    #: every monetary figure sits in range, differ when one does not, not_run when there is no
    #: revenue to measure against or no figure to measure (ORKA and TECX report no revenue). The
    #: lines said only "checks passed", so a scale check that never ran read the same as a pass.
    scale_check: CrossCheck = CHECK_NOT_RUN

    @property
    def ok(self) -> bool:
        return not self.failures

    def value(self, key: str) -> float | None:
        f = self.facts.get(key)
        return f.value if f else None


def _sourced(bundle: CiqBundle, fn: Any) -> float | None:
    """Run a ciq_sheets extractor and return its value, or None when it is not PRESENT."""
    try:
        s = fn(bundle)
    except CiqUnavailableError:
        return None
    return s.value if s.status is SourceStatus.PRESENT and s.value is not None else None


def _bs(bundle: CiqBundle, label: str) -> tuple[float | None, str | None]:
    """One Balance Sheet line → (value $M, source_ref). Reuses the shared row reader so the address
    and the freshest-period-first rule are stated in exactly one place."""
    s = cs._bs_latest(bundle, label)
    if s.status is not SourceStatus.PRESENT or s.value is None:
        return None, None
    return float(s.value), s.source_ref


def _pick(rows: list[list[Any]], label: str) -> float | None:
    ri = cs._find_row(rows, label)
    if ri is None:
        return None
    got = cs._latest_col(rows, ri, cs._period_header(rows))
    return float(got[1]) if got is not None else None


def _cf_row(bundle: CiqBundle, label: str, annual: bool) -> float | None:
    """Latest column of a Cash Flow / Income Statement row, cash flow first.

    Every (kind, sheet, freq) address below is a STRING LITERAL, fully unrolled. The CIQ-manifest
    drift guard reads these call sites statically and rejects a computed argument — a loop over
    sheet names or a freq parameter is invisible to it, so the manifest could silently stop
    covering an address this module depends on. Four explicit branches is the price of that guard
    seeing the truth, and it said so loudly the first two times this function was written."""
    def one(rows_fn: Any) -> float | None:
        try:
            rows = rows_fn()
        except CiqUnavailableError:
            return None
        return _pick(rows, label)

    if annual:
        got = one(lambda: bundle.sheet("financials", "Cash Flow", freq="annual"))
        if got is None:
            got = one(lambda: bundle.sheet("financials", "Income Statement", freq="annual"))
        return got
    got = one(lambda: bundle.sheet("financials", "Cash Flow", freq="quarterly"))
    if got is None:
        got = one(lambda: bundle.sheet("financials", "Income Statement", freq="quarterly"))
    return got


def _assert_scale(name: str, value: float | None, revenue: float | None) -> str | None:
    """A monetary figure must be $M by MAGNITUDE against revenue-in-$M. Returns a failure string,
    or None when the figure is absent (nothing to check) or in range."""
    if value is None or revenue is None or revenue <= 0 or value == 0:
        return None
    ratio = abs(value) / revenue
    if ratio > _SCALE_HI:
        return (f"{name} is {abs(value):,.0f} against revenue {revenue:,.1f} ($M) — {ratio:,.0f}x, "
                "which is a UNIT error, not a balance sheet")
    if ratio < _SCALE_LO:
        return (f"{name} is {abs(value):,.6f} against revenue {revenue:,.1f} ($M) — {ratio:.2e}x, "
                "which is a UNIT error (figure appears to be in whole dollars or billions)")
    return None


def extract(bundle: CiqBundle, ticker: str) -> CiqFacts:
    """Every balance-sheet fact the anchor bridge needs, cross-checked before it is handed on.

    Annual granularity for flow items (depreciation, operating cash flow, capital expenditure) —
    the anchor's other inputs are annual, and mixing a quarterly flow into an annual bridge is the
    period-alignment error ``_latest_dep_amort`` already refuses on the EDGAR side."""
    # both freqs stated as LITERALS — ("financials", None) is not a declared manifest address
    wb = (bundle.workbook("financials", freq="quarterly")
          or bundle.workbook("financials", freq="annual"))
    sha, _mtime = cs.file_provenance(wb.path) if wb is not None else (None, None)
    src_file = wb.path.name if wb is not None else None

    cash, cash_ref = _bs(bundle, "Total Cash & ST Investments")
    if cash is None:
        cash, cash_ref = _bs(bundle, "Cash And Equivalents")
    debt, debt_ref = _bs(bundle, "Total Debt")
    fin_lease, fin_ref = _bs(bundle, "Capital Leases")
    op_lease, op_ref = _bs(bundle, "Operating Lease Liabilities")

    # revenue is the SCALE REFERENCE every other figure is magnitude-checked against, so it is read
    # first and independently: annual where the workbook carries it, else the quarterly sheet.
    revenue = _cf_row(bundle, "Total Revenue", True) or _cf_row(bundle, "Total Revenue", False)

    da_cf = _cf_row(bundle, "Depreciation & Amort., Total", True)
    da_cf_plain = _cf_row(bundle, "Depreciation & Amort.", True)
    ocf = _sourced(bundle, cs.ltm_ocf)
    capex = _cf_row(bundle, "Capital Expenditure", True)
    diluted = _cf_row(bundle, "Weighted Avg. Diluted Shares Out.", False) or \
        _cf_row(bundle, "Weighted Avg. Diluted Shares Out.", True)

    stamp = f"CIQ Financials workbook {src_file or '?'} (sha {sha or '?'})"
    facts: dict[str, CiqFact] = {}

    def put(key: str, val: float | None, unit: str, basis: str, ref: str | None) -> None:
        if val is not None:
            facts[key] = CiqFact(value=round(val, 4), unit=unit, basis=basis,
                                 source=ref or stamp)

    put("cash", cash, "$M", "total cash and short-term investments, latest balance sheet", cash_ref)
    put("total_debt", debt, "$M", "CIQ classified total debt, latest balance sheet", debt_ref)
    put("finance_leases", fin_lease, "$M", "capital/finance leases, latest balance sheet", fin_ref)
    put("operating_leases", op_lease, "$M", "operating lease liabilities, latest balance sheet",
        op_ref)
    put("d_and_a", da_cf if da_cf is not None else da_cf_plain, "$M",
        "depreciation and amortisation, latest full year (cash-flow statement)", stamp)
    put("ocf", ocf, "$M", "cash from operations, trailing twelve months", stamp)
    put("capex", (abs(capex) if capex is not None else None), "$M",
        "capital expenditure, latest full year (magnitude)", stamp)
    put("diluted_shares", diluted, "millions", "weighted-average diluted shares, latest period",
        stamp)
    put("revenue", revenue, "$M", "total revenue, latest full year", stamp)

    checks: list[str] = []
    failures: list[str] = []

    # (3) UNIT scale, first — a scale error would make the other two checks meaningless
    scaled = ("cash", "total_debt", "d_and_a", "ocf", "capex")
    for key in scaled:
        bad = _assert_scale(key, facts[key].value if key in facts else None, revenue)
        if bad:
            failures.append(f"SCALE: {bad}")
    if not failures and revenue:
        checks.append(f"scale: every monetary figure within [{_SCALE_LO:g}, {_SCALE_HI:g}]x "
                      f"revenue {revenue:,.1f} ($M) — consistent with a $M sheet")
    measured = bool(revenue and revenue > 0
                    and any(key in facts and facts[key].value != 0 for key in scaled))
    scale_check: CrossCheck = (CHECK_NOT_RUN if not measured
                               else CHECK_DIFFER if any(f.startswith("SCALE:") for f in failures)
                               else CHECK_AGREE)

    # (1) D&A: the CONTAINMENT invariant, not an equality.
    #
    # The brief specified cash-flow vs income-statement agreement within ~20%. Measured against the
    # real workbooks that check fires on 2 of 4 honest names (AORT 61% apart, FUBO 97%), because the
    # two rows are DIFFERENT MEASURES by construction: CIQ's income-statement line is the
    # depreciation sitting inside operating expenses, while the cash-flow "Total" is consolidated.
    # AORT settles it — EDGAR's combined tag (22.458) matches the cash-flow total (23.35, 3.8%
    # apart) and not the income-statement line (9.05). An equality check there is a false-positive
    # generator, and a guard that fires on honest names gets switched off.
    #
    # What IS invariant, and holds on every name tested: the operating-expense portion cannot
    # exceed the consolidated total. That catches a swapped or garbled row with no tolerance to
    # tune, which is what a coherence check should be.
    da_is = _cf_row(bundle, "Depreciation & Amort.", True)
    da_total = facts["d_and_a"].value if "d_and_a" in facts else None
    if da_total and da_is:
        line = (f"D&A: income-statement line {da_is:,.2f} within cash-flow total {da_total:,.2f} "
                f"({da_is / da_total:.0%} of it)")
        if da_is <= da_total * (1 + _DA_TOLERANCE):
            checks.append(line)
        else:
            failures.append(f"D&A: income-statement line {da_is:,.2f} EXCEEDS the consolidated "
                            f"cash-flow total {da_total:,.2f} — the operating-expense portion "
                            "cannot be larger than the whole; one of these rows is misread")
    else:
        checks.append("D&A: only one statement discloses a depreciation line — containment unrun")

    # (2) Net debt: balance sheet vs the Multiples sheet's implied enterprise value less market cap
    nd_bs = None
    if debt is not None and cash is not None:
        nd_bs = debt + (fin_lease or 0.0) + (op_lease or 0.0) - cash
        put("net_debt", nd_bs, "$M",
            "total debt + leases where disclosed - total cash and short-term investments", None)
    ev_mult = _sourced(bundle, cs.ev_ebitda_current)
    ebitda = _sourced(bundle, cs.ltm_ebitda)
    if nd_bs is not None and ev_mult and ebitda and ebitda > 0:
        checks.append(f"net debt: balance-sheet bridge {nd_bs:,.1f} recorded; implied-TEV "
                      f"cross-read needs a market cap the workbook does not carry — deferred to "
                      f"the anchor, which holds one")
    return CiqFacts(ticker=ticker, as_of=None, source_file=src_file, source_sha256=sha,
                    facts=facts, checks=checks, failures=failures, scale_check=scale_check)


def scale_outcome(bundle: CiqBundle, ticker: str) -> CrossCheck:
    """The scale check's outcome for a name's CIQ exports — `extract`'s, which runs it first. A
    folder with no Financials workbook has nothing to measure: not run. A workbook `extract` cannot
    read is not run either — `anchor.ciq_bridge` reads that as "no bridge" and assembly goes on, so
    the outcome must not raise where the bridge did not; two exports of one kind still raise."""
    from vinci.dossier.ciq import CiqAmbiguousError

    if (bundle.workbook("financials", freq="quarterly") is None
            and bundle.workbook("financials", freq="annual") is None):
        return CHECK_NOT_RUN
    try:
        return extract(bundle, ticker).scale_check
    except CiqAmbiguousError:
        raise
    except Exception:  # noqa: BLE001 — the bridge's own rule: an unreadable workbook is no read
        return CHECK_NOT_RUN


def net_debt_cross_read(facts: CiqFacts, *, market_cap: float | None,
                        current_multiple: float | None, ltm_ebitda: float | None) -> str | None:
    """(2) The independent net-debt read, run where a market cap IS available (the anchor).

    ``TEV = current multiple x trailing EBITDA``; minus market cap that is net debt implied by the
    traded multiple. It must land near the balance sheet's own total. Returns a failure string or
    None (in tolerance, or not runnable)."""
    nd = facts.value("net_debt")
    if nd is None or not market_cap or not current_multiple or not ltm_ebitda:
        return None
    implied = current_multiple * ltm_ebitda - market_cap
    scale = max(abs(nd), abs(implied), 1.0)
    gap = abs(nd - implied) / scale
    if gap <= _ND_TOLERANCE:
        return None
    return (f"NET DEBT: balance sheet {nd:,.1f} vs multiple-implied {implied:,.1f} "
            f"(TEV {current_multiple:,.2f}x x EBITDA {ltm_ebitda:,.1f} - market cap "
            f"{market_cap:,.1f}) — {gap:.1%} apart, tolerance {_ND_TOLERANCE:.0%}")


def scale_check_backfill(path: Path, *, bundle: CiqBundle, refused: list[str]) -> bool:
    """Write `anchor.ciq_scale_check` onto ONE committed page, under a KEPT synthesis and every
    other anchor value as committed. True when the page moved.

    THE OUTCOME IS NOT ON THE PAGE, so the Financials exports are read — and only behind proof that
    each is the one the page was built from (`refresh.ciq_currency_transform`'s two proofs): the
    quarterly by the sha256 the page stamps (`ev_bridge.source_sha256`), the annual by its revenue
    and operating cash flow reproducing the page's annual table. A page that does not prove, has
    no anchor, or already holds a different outcome is named in ``refused`` — absent reads as not
    run, never as a pass."""
    from vinci.dossier import layer_refresh
    from vinci.dossier import statement_recon as sr
    from vinci.dossier.assemble import _read_scenario_card
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier, dossier_json, write_dossier

    original = path.read_text()
    doc = json.loads(original)
    t = str(doc.get("ticker"))
    a, mech = doc.get("anchor"), doc.get("mechanical") or {}
    if (path.parent / "known_wrong.json").exists():
        refused.append(f"{t}: SEALED by its own known_wrong.json")
        return False
    if not isinstance(a, dict):
        refused.append(f"{t}: no anchor block")
        return False
    stamp = (doc.get("ev_bridge") or {}).get("source_sha256")
    q = bundle.workbook("financials", freq="quarterly")
    if stamp is None or q is None or cs.file_provenance(q.path)[0] != stamp:
        refused.append(f"{t}: the quarterly Financials is not the export the page stamps")
        return False
    if bundle.workbook("financials", freq="annual") is not None:
        table = ((mech.get("financial_summary") or {}).get("annual") or {}).get("value")
        got = {(f.line, f.column): f.value for f in sr.ciq_figures(bundle)}
        if not isinstance(table, dict) or got != sr.table_figures(table):
            refused.append(f"{t}: the annual Financials does not reproduce the page's annual "
                           "table")
            return False
    new = scale_outcome(bundle, t)
    held = a.get("ciq_scale_check")
    if held is not None:
        if held != new:
            refused.append(f"{t}: ciq_scale_check on the page differs from the rebuild — kept")
        return False
    a["ciq_scale_check"] = new
    model = Dossier.model_validate(doc)
    if moved := layer_refresh.moved_layers(json.loads(original), json.loads(dossier_json(model))):
        model = layer_refresh.append(model, layer_refresh.entry("refresh", moved))
    write_dossier(path, model)       # the one writer: the operator's decision is guarded there
    path.with_name("dossier.md").write_text(render_markdown(
        model, card=_read_scenario_card(model.ticker), dossiers_root=path.parent.parent))
    return True
