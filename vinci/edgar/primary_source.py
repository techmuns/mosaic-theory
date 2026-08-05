"""(RC-1 C) Cross-source DERIVATIONS over the primary-source extracts + the CIQ/EDGAR mechanical
layer: the survival self-funding read, the same-window filing-vs-panel wall coherence, the
EBITDA-basis triangulation, and guide verification.

PURE functions (no I/O): the assembly feeds them already-extracted structured values, so they
unit-test offline against the committed pins. Every derived line names the SOURCE LAYER of each
component (filing vs CIQ panel vs release) — a mixed-layer figure is SURFACED, never forced to match
(CLAUDE.md derived-pin rule). A missing input yields an honest UNKNOWN line, never a guess.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

_TOL = 0.05  # 5% band for the same-window wall coherence + guide cross-source match


# --- (surface 1) self-funding — two inputs, both must be positive -------------------------------
def self_funding(ocf_latest_q_positive: bool | None, ltm_fcf_positive: bool | None) -> str:
    """'self-funding' ONLY when latest-Q OCF > 0 AND LTM FCF > 0; else the honest MIXED state. A
    single positive leg is not self-funding — supersedes the committed one-input 'self-funding'."""
    if ocf_latest_q_positive is None or ltm_fcf_positive is None:
        return "self-funding: UNKNOWN — latest-Q OCF and/or LTM FCF sign unavailable"
    if ocf_latest_q_positive and ltm_fcf_positive:
        return "self-funding: YES — latest-Q OCF > 0 AND LTM FCF > 0"
    legs = (f"latest-Q OCF {'>' if ocf_latest_q_positive else '<'} 0, "
            f"LTM FCF {'>' if ltm_fcf_positive else '<'} 0")
    return f"self-funding: MIXED — {legs} (both must be positive to self-fund)"


# --- (surface 2) same-window wall coherence — tranche-matched, exclusive boundary ----------------
@dataclass(frozen=True)
class PanelInstrument:
    name: str
    principal_musd: float | None
    maturity: date | None


def _plus_12m(d: date) -> date:
    try:
        return d.replace(year=d.year + 1)
    except ValueError:  # Feb-29 balance date → Feb-28 next year
        return d.replace(year=d.year + 1, day=28)


def panel_convertible_principal(panel: list[PanelInstrument], balance: date) -> float | None:
    """The panel's convertible-LOAN principal maturing in the SAME [balance, +12m) window — matched
    to the filing's convertible-loan repayment tranche (the +PIK delta). Excludes the convertible
    BOND ('convertible' AND 'loan' in the name). None if there is no in-window convertible loan."""
    end = _plus_12m(balance)
    conv = [i.principal_musd for i in panel
            if i.principal_musd is not None and i.maturity is not None
            and balance <= i.maturity < end
            and "convertible" in i.name.lower() and "loan" in i.name.lower()]
    return round(sum(conv), 1) if conv else None


def wall_coherence(
    filing_within_12m: float | None,
    panel: list[PanelInstrument],
    *,
    balance: date,
    filing_convertible: float | None = None,
    panel_convertible_principal: float | None = None,
    tol: float = _TOL,
) -> tuple[str, list[str]]:
    """Same-window filing-vs-panel wall coherence. Panel side = sum of instrument PRINCIPAL maturing
    in [balance, balance+12m) — EXCLUSIVE upper boundary (a maturity AT +12m is not 'within 12
    months'; the filing convention). Compare like-for-like to the filing's ≤12m figure; AGREE within
    tolerance ⇒ 'filing cross-validates panel'. Both figures carry BOTH basis labels; convertible
    delta (panel principal vs filing repayment = accrued PIK) is rendered as INFORMATION.

    Returns (render_line, qa_flags). A divergence with an instrument maturing within ±7d of the
    boundary is flagged a possible window-convention artifact — never a false-fire on convention."""
    if filing_within_12m is None:
        return ("wall coherence: UNKNOWN — filing states no ≤12m figure", [])
    end = _plus_12m(balance)
    in_window = [i for i in panel if i.principal_musd is not None and i.maturity is not None
                 and balance <= i.maturity < end]
    panel_sum = round(sum(i.principal_musd for i in in_window), 1)  # type: ignore[misc]
    diff = round(abs(panel_sum - filing_within_12m), 1)
    pct = diff / filing_within_12m if filing_within_12m else 1.0
    agrees = pct <= tol
    qa: list[str] = []
    boundary = [i for i in panel if i.maturity is not None
                and abs((i.maturity - end).days) <= 7]
    if not agrees and boundary:
        qa.append("wall coherence: divergence with an instrument maturing within ±7d of the +12m "
                  f"boundary ({', '.join(i.name for i in boundary)}) — possible window-convention "
                  "artifact, not a true divergence")
    verb = "AGREES" if agrees else "DIVERGES"
    lead = ("filing cross-validates panel" if agrees
            else "filing DIVERGES from panel — verify; neither silently preferred")
    line = (f"wall coherence — {lead}: panel same-window ${panel_sum}M (CIQ panel, principal "
            f"basis) vs filing ${filing_within_12m}M (10-Q, repayment basis) — {pct * 100:.1f}% "
            f"{'<' if agrees else '≥'} {tol * 100:.0f}% tol → {verb}. "
            f"Window [balance, +12m) EXCLUSIVE (filing convention).")
    if filing_convertible is not None and panel_convertible_principal is not None:
        delta = round(filing_convertible - panel_convertible_principal, 1)
        line += (f" Convertible: ${panel_convertible_principal}M panel-principal vs "
                 f"${filing_convertible}M filing-repayment (+${delta}M accrued PIK).")
    return (line, qa)


# --- (surface 3) EBITDA-basis triangulation — every leverage row basis-labeled -------------------
# ITEM 18 — the two non-numeric covenant-basis readings, defined beside the line that prints them.
#
# COVENANT_BASIS_UNKNOWN is the historical text and stays the default. It is only honest where
# nothing in the fund's own records contradicts it — which is precisely what item 18's caller now
# checks before letting it through.
COVENANT_BASIS_UNKNOWN = "UNKNOWN (not disclosed)"
# The LEGACY reading: an underwrite record exists but predates 18a's typed fact fields, so its
# leverage basis lives only in the V-row's prose. Saying UNKNOWN there is FALSE — the fund holds the
# number and is asserting ignorance of it (SMPL: the dossier printed UNKNOWN while V-SMPL recorded
# "the 8-K's loan-basis reads 1.2x"). Saying the PROSE value would need a prose reader, which is
# out of scope by decision. This says the true thing instead, and it self-clears: the moment a V-row
# carries the typed fact, the typed branch takes over. Legacy rows are NOT backfilled.
COVENANT_BASIS_NO_STRUCTURED_SOURCE = "no structured source for this decision vintage"


def basis_triangulation(
    net_debt_ebitda_ciq: str | None,
    total_debt_ebitda_comps: str | None,
    net_debt: float | None,
    ltm_adjusted_ebitda: float | None,
    *,
    gaap_gross_margin: float | None,
    impairment: float | None,
    revenue: float | None,
    ciq_adjusted_margin: float | None = None,
    covenant_basis: str | None = None,
) -> str:
    """The EBITDA/margin bases table — LABELS are load-bearing (a leverage number is meaningless
    without its basis). net debt / company-adjusted LTM EBITDA is the third basis; covenant basis
    is UNKNOWN when the agreement's EBITDA definition is not disclosed. Margin: GAAP vs
    impairment-excluded (source CIQ's figure; render GAAP + impairment/revenue as the labeled
    cross-check).

    ``covenant_basis`` (item 18) is RESOLVED BY THE CALLER and rendered verbatim. This function
    stays record-ignorant on purpose: it sits in ``vinci.edgar`` and must not learn what an
    underwrite record is. None keeps the historical line, which is the honest reading when there is
    no record to contradict it."""
    adj = (f"~{round(net_debt / ltm_adjusted_ebitda, 1)}x"
           if net_debt is not None and ltm_adjusted_ebitda else "UNKNOWN")
    ltm_lbl = f"${ltm_adjusted_ebitda}M" if ltm_adjusted_ebitda is not None else "LTM unavailable"
    rows = [
        "EBITDA-basis triangulation (each leverage basis-labeled):",
        f"  net debt / EBITDA (CIQ, GAAP basis): {net_debt_ebitda_ciq or 'UNKNOWN'}",
        f"  total debt / EBITDA (CIQ comps, GAAP basis): {total_debt_ebitda_comps or 'UNKNOWN'}",
        f"  net debt / company-adjusted LTM EBITDA ({ltm_lbl}): {adj}",
        f"  covenant basis: {covenant_basis or COVENANT_BASIS_UNKNOWN}",
    ]
    if gaap_gross_margin is not None and impairment is not None and revenue:
        recon = round(gaap_gross_margin + impairment / revenue * 100, 1)
        shown = ciq_adjusted_margin if ciq_adjusted_margin is not None else recon
        rows.append(
            f"  margin: GAAP {gaap_gross_margin}% · impairment-excluded {shown}% "
            f"(CIQ; cross-check {gaap_gross_margin} + {impairment}/{revenue} = {recon}%)")
    return "\n".join(rows)


# --- (surface / digest) guide verification -------------------------------------------------------
def guide_verification(
    metric: str,
    ciq_low: float | None,
    ciq_high: float | None,
    *,
    prior_fy_actual: float | None = None,
    release_qualitative: bool = False,
    release_low: float | None = None,
    release_high: float | None = None,
    release_basis: str = "level",
) -> str:
    """Cross-check the CIQ guide against the release-parsed guide. VENDOR-ECHO requires BOTH: CIQ
    guide ≈ prior-FY actual (0.1% relative, source-rounding) AND the release gives NO corroborating
    number for this metric (absent or QUALITATIVE) — a stale carry-forward the primary source does
    not confirm. Cross-source VERIFIED when the CIQ and release ranges match; else a mismatch."""
    if ciq_low is None:
        return f"guide verification ({metric}): CIQ guide UNKNOWN — not cross-checked"
    # CROSS-BASIS: REFUSE, NEVER DERIVE (2026-08-05). CIQ guides a LEVEL; a release can guide a
    # CHANGE ("net sales expected to range between -2% and +2% year-over-year"). Comparing -2..+2
    # against 1,345..1,355 is meaningless, and the tempting fix — derive a level from the prior
    # period — CROSSES SOURCES MID-CHECK: the prior-year figure lives in a CIQ series whose gross
    # margin need not share the filer's definition, so a filing-derived guide would be verified
    # against a vendor-derived base. That is the operating-vs-EBITDA lesson applied to a base we
    # would be manufacturing. Refusing loses no verification: before this the change guide was
    # dropped entirely, so "not cross-checked" is strictly more than the nothing it replaces.
    if release_basis == "change" and release_low is not None:
        return (f"guide verification ({metric}): CIQ guides a LEVEL ({ciq_low}–{ciq_high}) and the "
                f"release guides a CHANGE ({release_low}–{release_high}) — NOT CROSS-CHECKED. "
                "Deriving a level from the prior period would compare a filing-derived guide "
                "against a vendor-derived base; the two need not share a definition.")
    # VENDOR-ECHO — TWO CONJUNCTS: (1) CIQ guide ≈ prior-FY actual within source-rounding (0.1% rel;
    # the release rounds $427.516→$427.5, so relative not absolute-3dp); AND (2) the release states
    # NO number for this metric (release_low is None) or only a QUALITATIVE outlook. A numeric
    # release guide equal to the prior actual is RELEASE-VERIFIED, not a stale echo — corroboration
    # SUPPRESSES the flag (it falls through to cross-source VERIFIED below).
    _echo = False
    if (prior_fy_actual is not None and prior_fy_actual != 0
            and (release_low is None or release_qualitative)):
        _rel, pa = 0.001, abs(prior_fy_actual)  # 0.1% relative — source-rounding, not coincidence
        _echo = (abs(ciq_low - prior_fy_actual) / pa < _rel
                 and (ciq_high is None or abs(ciq_high - prior_fy_actual) / pa < _rel))
    if _echo:
        tail = ("release outlook QUALITATIVE-only — render the qualitative growth line"
                if release_qualitative else "release states no outlook here — uncorroborated")
        return (f"guide verification ({metric}): CIQ FY guide {ciq_low} ≈ prior-FY actual "
                f"{prior_fy_actual} (within source-rounding) → VENDOR-ECHO flag (stale "
                f"carry-forward); {tail}")
    if release_qualitative and release_low is None:
        return (f"guide verification ({metric}): CIQ {ciq_low}–{ciq_high} vs release QUALITATIVE "
                "→ plausibility flag; render the qualitative growth line")
    if release_low is None:  # release stated no numeric guide — nothing to cross-check
        return (f"guide verification ({metric}): CIQ {ciq_low}–{ciq_high} vs release "
                "NO NUMERIC OUTLOOK → not cross-checked")
    # release_low is now narrowed to a float by the early return above (no redundant None re-check).
    if abs(ciq_low - release_low) < 0.01 and abs(
            (ciq_high or 0.0) - (release_high or 0.0)) < 0.01:
        return (f"guide verification ({metric}): CIQ {ciq_low}–{ciq_high} vs release "
                f"{release_low}–{release_high} → cross-source VERIFIED")
    return (f"guide verification ({metric}): CIQ {ciq_low}–{ciq_high} vs release "
            f"{release_low}–{release_high} → MISMATCH flag")
