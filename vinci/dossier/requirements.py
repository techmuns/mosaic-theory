"""The canonical manifest of MANUAL CIQ inputs the dossier assembler expects — the ONE place that
defines what a human must pull by hand into ``data/manual/ciq/<TICKER>/``.

CIQ is licensed and pulled by hand (:mod:`vinci.dossier.manual_store`); everything else in the
funnel is automated. This module is the **single source of truth** for *which* CIQ exports the
mechanical layer (:mod:`vinci.dossier.mechanical` + :mod:`vinci.dossier.ciq_sheets`) actually
consumes, at what granularity and lookback, and which are required vs optional. BOTH consumers read
from :data:`CIQ_MODULES` and therefore cannot drift:

- the **MISSING-manifest** path in ``assemble_one`` (an empty / partial folder → per-module "pull
  CIQ" flags) — via :func:`missing_required` / :func:`manifest_flags`;
- the ``vinci dossier requirements`` **command** (a per-name export checklist + ``--json`` for the
  upload UI) — via :func:`as_payload` / :func:`render_checklist`.

If the assembler's required modules change, change them HERE; both outputs follow automatically.

It also documents the **don't-double-pull** rule: inputs sourced FREE from EDGAR (10-K/10-Q, 8-K,
Form 4) must NOT be manually uploaded — :data:`EDGAR_FREE_INPUTS`. Each ``used_for`` names the
extractor so the manifest stays code-traceable and a future session can find what consumes a module.
"""

from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel

from vinci.dossier.ciq import CiqBundle

# The documented manual-CIQ root (mirrors :meth:`LocalFolderStore.from_config` — git-ignored
# ``data/manual/ciq``). Kept as a literal so the manifest is a pure, config-free reference.
MANUAL_CIQ_ROOT = "data/manual/ciq"


class Granularity(enum.StrEnum):
    """The time resolution at which a module must be exported (notes' Period-Type discipline)."""

    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    BOTH = "both"  # the export carries both annual-cadence and quarterly/window views
    SNAPSHOT = "snapshot"  # current-only, no historical series


class CiqModuleRequirement(BaseModel, frozen=True):
    """One manual CIQ export the assembler expects — what it is, what consumes it, and how to pull
    it. ``workbook_kind`` is the :class:`CiqBundle` address key (NOT a filename); ``freq`` pins the
    two Financials exports (Annual vs Quarterly are distinct required files, notes line ~116)."""

    module: str  # human label, e.g. "Financials — Annual"
    workbook_kind: str  # CiqBundle kind: financials / estimates / customers / transcript
    freq: str | None  # "annual"/"quarterly" for the two Financials exports; None otherwise
    sheets: tuple[str, ...]  # the subsheets the mechanical layer reads from this export
    used_for: str  # what the mechanical layer derives from it (names the extractor)
    granularity: Granularity
    lookback: str  # the duration / lookback the extractors need
    required: bool  # required (mechanical FACTS depend on it) vs optional (synthesis colour only)

    def expected_path(self, ticker: str | None = None) -> str:
        """The folder this export must be placed in — concrete for a ticker, else the template."""
        return _expected_path(ticker)


class EdgarFreeInput(BaseModel, frozen=True):
    """A filing that must NOT be manually uploaded because the funnel pulls it FREE from EDGAR."""

    input: str  # the filing a human might be tempted to export from CIQ
    why: str  # why it's redundant to upload (where the funnel already gets it)
    edgar_source: str  # the free EDGAR path the automated layer uses instead


# --- THE single source of truth: the modules the mechanical layer actually consumes ------------
#
# Each entry is grounded in a real (workbook-kind, sheet) address read in ciq_sheets.py:
#   financials/Multiples (quarterly) → ev_ebitda_current/percentile, range_position, pe_ltm_current
#   financials/Income Statement, Cash Flow, Capital Structure Details, Segments, Ratios (annual) →
#       margin_trend, free_cash_flow, interest_coverage, liquidity_covenant_flags, segments,
#       segment_ebitda, geographic, multi_year_trajectory
#   financials/Income Statement (quarterly) → clean same-quarter YoY (margin_trend/trajectory)
#   estimates/{Consensus,Revisions,Surprise} → consensus_view, eps/revenue_revisions, surprise
#   customers (Business Relationships) → customers()
#   transcript (earnings call) → transcript_for_synthesis() + management_commentary()
#
# REQUIRED = the mechanical layer derives a source-bound FACT from it (valuation / quality /
# concentration / consensus numbers). OPTIONAL = it only colours the LLM synthesis or is a pointer
# (no mechanical fact), so the dossier degrades gracefully without it.
CIQ_MODULES: tuple[CiqModuleRequirement, ...] = (
    CiqModuleRequirement(
        module="Financials — Annual",
        workbook_kind="financials",
        freq="annual",
        sheets=(
            "Income Statement", "Cash Flow", "Balance Sheet", "Capital Structure Details",
            "Segments", "Ratios",
        ),
        used_for=(
            "5y margin trend (margin_trend), FCF (free_cash_flow), interest coverage "
            "(interest_coverage), net-debt/EBITDA from CIQ Net/Total Debt + LTM EBITDA "
            "(net_debt / total_debt / ltm_ebitda), capital-structure / covenant flags "
            "(liquidity_covenant_flags), segment + geographic concentration (segments / "
            "segment_ebitda / geographic), and the multi-year revenue/segment arc "
            "(multi_year_trajectory)"
        ),
        granularity=Granularity.ANNUAL,
        lookback="5 fiscal years (export with Period Type: Annual)",
        required=True,
    ),
    CiqModuleRequirement(
        module="Financials — Quarterly",
        workbook_kind="financials",
        freq="quarterly",
        sheets=("Multiples", "Income Statement", "Balance Sheet"),
        used_for=(
            "valuation-range position / multiple percentiles (ev_ebitda_current, "
            "ev_ebitda_percentile, range_position, pe_ltm_current), the freshest CIQ Net/Total "
            "Debt for net-debt/EBITDA (net_debt / total_debt), and the clean same-quarter YoY "
            "revenue trajectory (margin_trend / multi_year_trajectory)"
        ),
        granularity=Granularity.QUARTERLY,
        lookback=(
            "~20 quarterly Closes for the Multiples percentile (n≥8 settled quarters; fewer is "
            "resolution-limited per the notes); ≥8 quarters for the Q/Q view"
        ),
        required=True,
    ),
    CiqModuleRequirement(
        module="Estimates Report",
        workbook_kind="estimates",
        freq=None,
        sheets=(
            "Consensus", "Revisions", "Surprise", "Trends", "Guidance", "Multiples",
            "Recent Changes",
        ),
        used_for=(
            "forward consensus context (consensus_view), EPS & Revenue revision breadth "
            "(eps_revisions / revenue_revisions), annual EPS surprise / beat-miss history "
            "(surprise_history), AND the horizon-matched catalyst-path view (catalyst_path): FQ "
            "revision breadth (horizon_read), monthly consensus paths (acceleration_read), the "
            "NTM forward-multiple ladder (cross_name_anchor), the guidance bridge + delivery "
            "track-record (guidance_bridge), the broker revision-event log (revision_events), and "
            "target/rating stats (consensus_stats)"
        ),
        granularity=Granularity.BOTH,
        lookback=(
            "estimate revisions over the trailing 1–3 months; monthly consensus snapshots to 12m; "
            "EPS surprise + guidance track-record by fiscal year; forward multiples NTM→FY33"
        ),
        required=True,
    ),
    CiqModuleRequirement(
        module="Business Relationships (Customers & Suppliers)",
        workbook_kind="customers",
        freq=None,
        sheets=("Customers view", "Suppliers view"),
        used_for="customer / supplier concentration — largest-counterparty dependency (customers)",
        granularity=Granularity.SNAPSHOT,
        lookback="current — 'recently disclosed' (CIQ surfaces the last ~2 years), current-only",
        required=True,
    ),
    CiqModuleRequirement(
        module="Earnings-call transcript",
        workbook_kind="transcript",
        freq=None,
        sheets=(),  # a text document, not a workbook with subsheets
        used_for=(
            "qualitative synthesis context — a boilerplate-stripped, char-bounded slice "
            "(transcript_for_synthesis) — and a source-bound management-commentary POINTER "
            "(management_commentary); never embedded full, never machine-curated"
        ),
        granularity=Granularity.QUARTERLY,
        lookback="the last ~2 quarters (most recent 1–2 earnings calls)",
        required=False,
    ),
    CiqModuleRequirement(
        module="Company Comparable Analysis (peer comps)",
        workbook_kind="comps",
        freq=None,
        sheets=(
            "Financial Data", "Trading Multiples", "Operating Statistics", "Business Description",
            "Credit Health Panel", "Implied Valuation",
        ),
        used_for=(
            "peer-set COMPOSITION + market-cap / business-model dispersion (peer_set / "
            "comparability), the trailing-vs-forward peer-multiple spread (trading_multiples), the "
            "fundamental DELTAS (fundamental_deltas) + the per-peer GRID (peer_grid); the unified "
            "leverage block — comps total-debt/EBITDA (comps_total_debt_ebitda) + credit-health "
            "scores (credit_health); and the CIQ IMPLIED VALUATION table posed for the human "
            "(implied_valuation) — CIQ-computed, NO machine upside. Valuation Chart is empty"
        ),
        granularity=Granularity.SNAPSHOT,
        lookback="current — the latest comp set (LTM + NTM forward), current-only",
        required=False,
    ),
)

# Inputs that must NOT be manually uploaded — the funnel already pulls them FREE from EDGAR. Pulling
# them from CIQ wastes the human's time and (for insider data) walks into CIQ's direction-flip trap.
EDGAR_FREE_INPUTS: tuple[EdgarFreeInput, ...] = (
    EdgarFreeInput(
        input="8-K (current reports) + furnished Ex-99.1 press releases",
        why=(
            "the drawdown-cause 8-Ks and the revised full-year guidance (Ex-99.1) are fetched and "
            "source-bound automatically (mechanical._drawdown_filings / _revised_guidance)"
        ),
        edgar_source="EDGAR 8-K full text + filing-index Ex-99.1 (free, no entitlement)",
    ),
    EdgarFreeInput(
        input="10-K / 10-Q (annual & interim financial statements)",
        why=(
            "the screen + dossier read fundamentals (P/E, FCF sign, net leverage, shares, diluted "
            "EPS) from EDGAR XBRL companyfacts, and the formal filing text is free on EDGAR; the "
            "CIQ-rendered filing adds nothing the funnel doesn't already have"
        ),
        edgar_source="EDGAR XBRL companyfacts + the 10-K/10-Q full text (free)",
    ),
    EdgarFreeInput(
        input="Form 4 (insider transactions)",
        why=(
            "insider trades are free on EDGAR as Form 4; the dossier does not consume the CIQ "
            "Insider Trading export — and CIQ's Transaction-Type column carries a direction-flip "
            "trap (mechanical option-exercise sales look like discretionary selling), so prefer "
            "Form 4 (ciq_extraction_notes.md)"
        ),
        edgar_source="EDGAR Form 4 (free)",
    ),
)


# --- presence / MISSING manifest (consumed by assemble_one) -----------------------------------


def _expected_path(ticker: str | None) -> str:
    return f"{MANUAL_CIQ_ROOT}/{ticker.upper()}/" if ticker else f"{MANUAL_CIQ_ROOT}/<TICKER>/"


def module_present(bundle: CiqBundle, req: CiqModuleRequirement) -> bool:
    """Strict presence: a workbook of the module's kind AND — for the two Financials exports — its
    confirmed Period-Type ``freq``. The lenient :meth:`CiqBundle.workbook` fallback is wrong for a
    manifest (the Quarterly export is a *distinct* required file from the Annual one); here an
    unconfirmed-freq Financials workbook satisfies NEITHER slot, surfacing 'pull a clean export'."""
    return any(
        w.kind == req.workbook_kind and (req.freq is None or w.freq == req.freq)
        for w in bundle.workbooks
    )


def missing_required(bundle: CiqBundle) -> list[CiqModuleRequirement]:
    """The REQUIRED modules absent from ``bundle`` — the per-module MISSING manifest. Reads
    :data:`CIQ_MODULES`, so it can never drift from the requirements command. Optional modules are
    never reported missing (the dossier degrades gracefully without them)."""
    return [m for m in CIQ_MODULES if m.required and not module_present(bundle, m)]


def manifest_flags(bundle: CiqBundle, *, ticker: str, location: str) -> list[str]:
    """Assemble-time 'pull CIQ' flags for the MISSING required modules — derived from
    :data:`CIQ_MODULES` (the same definition the requirements command renders). Empty when every
    required module is present. An empty folder yields one summary flag; a partial folder names each
    still-missing module so the human pulls exactly what's left."""
    missing = missing_required(bundle)
    if not missing:
        return []
    names = ", ".join(m.module for m in missing)
    if bundle.is_empty:
        return [f"pull CIQ for {ticker} and re-run — no export found at {location} (need: {names})"]
    return [
        f"pull CIQ '{m.module}' for {ticker} — {m.used_for}; expected at {location}"
        for m in missing
    ]


# --- the `dossier requirements` command renderers (checklist + JSON) --------------------------


def as_payload(ticker: str | None = None) -> dict[str, Any]:
    """Machine-readable manifest (for ``--json`` and the future frontend upload UI). Every module is
    a structured record; the EDGAR-free 'do not upload' list is included so the UI documents the
    don't-double-pull rule. Reads :data:`CIQ_MODULES` — the single source."""
    return {
        "ticker": ticker.upper() if ticker else None,
        "manual_ciq_root": _expected_path(ticker),
        "modules": [
            {
                "module": m.module,
                "workbook_kind": m.workbook_kind,
                "freq": m.freq,
                "sheets": list(m.sheets),
                "used_for": m.used_for,
                "granularity": m.granularity.value,
                "lookback": m.lookback,
                "required": m.required,
                "expected_path": m.expected_path(ticker),
            }
            for m in CIQ_MODULES
        ],
        "edgar_free_do_not_upload": [
            {"input": e.input, "why": e.why, "edgar_source": e.edgar_source}
            for e in EDGAR_FREE_INPUTS
        ],
    }


def render_checklist(ticker: str | None = None) -> str:
    """A human export checklist for a name (``--ticker``) or the generic template. Required first,
    then optional, then the EDGAR-free DO-NOT-UPLOAD section. Reads :data:`CIQ_MODULES`."""
    who = ticker.upper() if ticker else "<TICKER>"
    root = _expected_path(ticker)
    lines = [
        f"=== CIQ manual-export checklist · {who} ===",
        f"Pull each REQUIRED export by hand into {root} (licensed CIQ data — git-ignored, never "
        "auto-fetched).",
        "",
        "REQUIRED (the mechanical layer derives source-bound facts from these):",
    ]
    for m in CIQ_MODULES:
        if not m.required:
            continue
        lines.append(f"  ☐ {m.module}  [{m.granularity.value}; {m.lookback}]")
        lines.append(f"      sheets: {', '.join(m.sheets) or '(text document)'}")
        lines.append(f"      used for: {m.used_for}")
    lines += ["", "OPTIONAL (colours the synthesis only — the dossier still assembles without it):"]
    for m in CIQ_MODULES:
        if m.required:
            continue
        lines.append(f"  ☐ {m.module}  [{m.granularity.value}; {m.lookback}]")
        lines.append(f"      used for: {m.used_for}")
    lines += ["", "DO NOT upload — pulled FREE from EDGAR (don't double-pull):"]
    for e in EDGAR_FREE_INPUTS:
        lines.append(f"  ✗ {e.input}")
        lines.append(f"      {e.why}  →  {e.edgar_source}")
    return "\n".join(lines)
