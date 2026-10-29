"""(RC-1 C) Cross-source DERIVATIONS over the primary-source extracts + the CIQ/EDGAR mechanical
layer: the survival self-funding read, the same-window filing-vs-panel wall coherence, the
EBITDA-basis triangulation, and guide verification.

PURE functions (no I/O): the assembly feeds them already-extracted structured values, so they
unit-test offline against the committed pins. Every derived line names the SOURCE LAYER of each
component (filing vs CIQ panel vs release) — a mixed-layer figure is SURFACED, never forced to match
(CLAUDE.md derived-pin rule). A missing input yields an honest UNKNOWN line, never a guess.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import NamedTuple

from vinci.dossier.schemas import CHECK_AGREE, CHECK_DIFFER, CHECK_NOT_RUN, CrossCheck

_TOL = 0.05  # 5% band for the same-window wall coherence
#: The guide check's match: both bounds within this, ABSOLUTE, in the guide's own unit (named
#: 2026-10-23 so the data-quality scorecard cites it rather than re-typing it — `_TOL` above had
#: claimed to be this band too, and is not).
GUIDE_MATCH = 0.01
#: A wall divergence beside an instrument maturing within this many days of the window's +12m
#: boundary is flagged a possible window-convention artifact.
BOUNDARY_DAYS = 7
#: Every QA flag the wall check writes opens with this — the refresh that rebuilds the check
#: selects the page's stored wall flags by it (`refresh.cross_check_transform`).
WALL_FLAG = "wall coherence:"
#: The wall line when the 10-Q states no ≤12m figure — returned before the panel is read, so no
#: panel maturity can move it (`refresh.maturity_check_transform` relies on that).
WALL_NOT_STATED = "wall coherence: UNKNOWN — filing states no ≤12m figure"


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


def self_funding_check(ocf_latest_q_positive: bool | None,
                       ltm_fcf_positive: bool | None) -> CrossCheck:
    """The two legs of :func:`self_funding` set against each other: EDGAR's latest-quarter OCF
    sign and CIQ's LTM FCF sign. NOT ITS QUESTION: the line asks whether the name funds itself;
    this asks whether the two sources point the same way, so two NEGATIVE legs AGREE here and
    still read MIXED there. Not run when either sign is unavailable — the line's UNKNOWN."""
    if ocf_latest_q_positive is None or ltm_fcf_positive is None:
        return CHECK_NOT_RUN
    return CHECK_AGREE if ocf_latest_q_positive == ltm_fcf_positive else CHECK_DIFFER


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


class WallCoherence(NamedTuple):
    """The wall read whole: the line and its QA flags, and beside them the outcome a reader may
    not parse out of the line (`CrossCheck`) and whether a divergence states its boundary reason."""

    line: str
    qa: list[str]
    check: CrossCheck
    near_boundary: bool | None      # set on a divergence only: an instrument within ±7d of +12m


def wall_coherence(
    filing_within_12m: float | None,
    panel: list[PanelInstrument],
    *,
    balance: date,
    filing_convertible: float | None = None,
    panel_convertible_principal: float | None = None,
    tol: float = _TOL,
    filing_basis: str | None = None,
) -> tuple[str, list[str]]:
    """(render_line, qa_flags) — :func:`wall_coherence_read`'s line and flags, for a caller that
    stores no outcome."""
    r = wall_coherence_read(filing_within_12m, panel, balance=balance,
                            filing_convertible=filing_convertible,
                            panel_convertible_principal=panel_convertible_principal, tol=tol,
                            filing_basis=filing_basis)
    return (r.line, r.qa)


def wall_coherence_read(
    filing_within_12m: float | None,
    panel: list[PanelInstrument],
    *,
    balance: date,
    filing_convertible: float | None = None,
    panel_convertible_principal: float | None = None,
    tol: float = _TOL,
    filing_basis: str | None = None,
) -> WallCoherence:
    """Same-window filing-vs-panel wall coherence. Panel side = sum of instrument PRINCIPAL maturing
    in [balance, balance+12m) — EXCLUSIVE upper boundary (a maturity AT +12m is not 'within 12
    months'; the filing convention). Compare like-for-like to the filing's ≤12m figure; AGREE within
    tolerance ⇒ 'filing cross-validates panel'. Both figures carry BOTH basis labels; convertible
    delta (panel principal vs filing repayment = accrued PIK) is rendered as INFORMATION.

    A divergence with an instrument maturing within ±7d of the boundary is flagged a possible
    window-convention artifact — never a false-fire on convention.

    ``filing_basis`` is the filing figure's own basis (`MaturityWall.basis`; None is principal). A
    figure that is not principal is NOT COMPARED (audit E2-D15): Netflix states $3,194M of
    principal AND interest, and set against the panel's $2,526M of principal it would print a 26%
    divergence that is only the coupon. Like the unstated wall, the line is returned before the
    panel is read."""
    if filing_within_12m is None:
        return WallCoherence(WALL_NOT_STATED, [],
                             CHECK_NOT_RUN, None)
    if filing_basis not in (None, "principal"):
        return WallCoherence(
            f"wall coherence: NOT RUN — the 10-Q states ${filing_within_12m}M due ≤12m as "
            f"{filing_basis}, and the CIQ panel counts principal only", [], CHECK_NOT_RUN, None)
    # NO DATED PRINCIPAL, NO SECOND FIGURE (Codex, #793): with no instrument carrying both a
    # principal and a maturity the panel's same-window total cannot be established, and summing
    # nothing to $0.0 would read as a divergence the panel never showed
    if not any(i.principal_musd is not None and i.maturity is not None for i in panel):
        return WallCoherence("wall coherence: UNKNOWN — the CIQ panel carries no instrument with "
                             "both a principal and a maturity", [], CHECK_NOT_RUN, None)
    end = _plus_12m(balance)
    in_window = [i for i in panel if i.principal_musd is not None and i.maturity is not None
                 and balance <= i.maturity < end]
    panel_sum = round(sum(i.principal_musd for i in in_window), 1)  # type: ignore[misc]
    diff = round(abs(panel_sum - filing_within_12m), 1)
    # A STATED ZERO agrees with a zero (audit E2-D15): Werner's 10-Q says "no principal amount
    # expected to be paid within 12 months", and dividing by it read $0 against $0 as a 100% gap.
    pct = diff / filing_within_12m if filing_within_12m else (0.0 if diff == 0 else 1.0)
    agrees = pct <= tol
    qa: list[str] = []
    boundary = [i for i in panel if i.maturity is not None
                and abs((i.maturity - end).days) <= BOUNDARY_DAYS]
    if not agrees and boundary:
        qa.append(f"{WALL_FLAG} divergence with an instrument maturing within "
                  f"±{BOUNDARY_DAYS}d of the +12m boundary ({', '.join(i.name for i in boundary)}) "
                  "— possible window-convention artifact, not a true divergence")
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
    return WallCoherence(line, qa, CHECK_AGREE if agrees else CHECK_DIFFER,
                         None if agrees else bool(boundary))


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
    # A NON-POSITIVE EBITDA HAS NO LEVERAGE MULTIPLE (audit E1-D13) — the guard its twin in
    # `edgar.client` has always carried ("EBITDA<=0 (ratio meaningless)"). This one tested only
    # truthiness, so a negative LTM printed "($-100.0M): ~-3.0x", a leverage that reads as net cash.
    # Reading stated losses (audit E2-D10) is what lets a negative LTM reach this line.
    if net_debt is None or ltm_adjusted_ebitda is None:
        adj = "UNKNOWN"
    elif ltm_adjusted_ebitda <= 0:
        adj = "UNKNOWN — EBITDA<=0 (ratio meaningless)"
    else:
        adj = f"~{round(net_debt / ltm_adjusted_ebitda, 1)}x"
    ltm_lbl = f"${ltm_adjusted_ebitda}M" if ltm_adjusted_ebitda is not None else "LTM unavailable"
    rows = [
        "EBITDA-basis triangulation (each leverage basis-labeled):",
        # NOT "GAAP basis" (2026-10-21): CIQ's EBITDA leaves out items CIQ treats as unusual —
        # TJX's Q2 FY27 sits $331M below the 10-Q's — so it is labelled as the vendor's figure
        # (`financial_summary.ebitda_reconciliation` measures how far it sits from the filings)
        f"  {CIQ_NET_DEBT_LABEL}: {net_debt_ebitda_ciq or 'UNKNOWN'}",
        f"  {CIQ_COMPS_LABEL}: {total_debt_ebitda_comps or 'UNKNOWN'}",
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
#: A guide period label → the SCOPE it covers, or None when the label says nothing decidable.
#: CIQ writes "FQ3 2026" / "FY 2026"; a release writes "2026" / "Fiscal 2028" / "next-fy" / "Q3".
#: Only these two shapes are decided — an unrecognised label yields None and the check proceeds
#: exactly as before, because inventing a scope would manufacture the refusal this guards against.
_QUARTER_PERIOD = re.compile(r"\b(?:FQ\s*[1-4]|Q[1-4])\b", re.I)
#: A HALF-YEAR names a determinate six-month span, so it decides a scope exactly as "FQ3" does.
#: Leaving it undecidable let an H1 guide fall through to the numeric comparison against an FY
#: guide and emit the same false MISMATCH this refusal exists to stop (review finding, #429).
#: PROTECTIVE, NOT CORRECTIVE — measured over the live corpus, the labels that actually reach
#: `guide_verification` are only `FQ*`/`FY*` (CIQ side) and `2024`/`2026`/`Fiscal 2028`/`Q1`–`Q4`/
#: `next-fy` (release side); NO committed name currently produces a half-year guide period. The
#: worded half-year forms in the corpus (`first half of 2026`, `six months ended June 30, 2026`)
#: live in `operating_drivers.rows[]`, a different consumer that never calls this.
_HALF_PERIOD = re.compile(
    r"\b(?:H[12]|[12]H)\b|\b(?:first|second)\s+half\b|\bsix\s+months\s+ended\b", re.I)
_ANNUAL_PERIOD = re.compile(r"\bFY\b|\bfiscal\b|\bnext-fy\b|^\s*(?:19|20)\d{2}\s*$", re.I)


#: The triangulation's two CIQ rows, named for the EBITDA they divide. Shared with the refresh that
#: relabels pages written under the old "(CIQ, GAAP basis)" wording, so both say one thing.
CIQ_NET_DEBT_LABEL = "net debt / EBITDA (CIQ's EBITDA, vendor-normalised)"
CIQ_COMPS_LABEL = "total debt / EBITDA (CIQ comps EBITDA, vendor-normalised)"
OLD_TRIANGULATION_LABELS = (("net debt / EBITDA (CIQ, GAAP basis)", CIQ_NET_DEBT_LABEL),
                            ("total debt / EBITDA (CIQ comps, GAAP basis)", CIQ_COMPS_LABEL))


def period_scope(label: str | None) -> str | None:
    """``"quarter"`` / ``"half"`` / ``"annual"`` / ``None`` (undecidable) for a guide-period label.

    ORDER IS LOAD-BEARING, most-specific first. Quarter leads: "FQ3 2026" carries a bare year the
    annual pattern would also match, and a quarter label carrying its fiscal year is still a
    quarter — and "second half of quarter" is a QUARTER, not a half-year. Half comes next for the
    same reason in the other direction: "H1 fiscal 2026" contains "fiscal", so testing annual first
    would call a six-month guide a year — the misclassification is worse than the undecidable it
    replaces, because a wrong scope SILENCES a real mismatch instead of merely not refusing.
    """
    if not label:
        return None
    text = label.strip()
    if _QUARTER_PERIOD.search(text):
        return "quarter"
    if _HALF_PERIOD.search(text):
        return "half"
    if _ANNUAL_PERIOD.search(text):
        return "annual"
    return None


class GuideVerification(NamedTuple):
    """The guide check whole: its line, and the outcome a reader may not parse out of it."""

    line: str
    check: CrossCheck


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
    ciq_period: str | None = None,
    release_period: str | None = None,
) -> str:
    """:func:`guide_verification_read`'s line, for a caller that stores no outcome."""
    return guide_verification_read(
        metric, ciq_low, ciq_high, prior_fy_actual=prior_fy_actual,
        release_qualitative=release_qualitative, release_low=release_low,
        release_high=release_high, release_basis=release_basis, ciq_period=ciq_period,
        release_period=release_period).line


def guide_verification_read(
    metric: str,
    ciq_low: float | None,
    ciq_high: float | None,
    *,
    prior_fy_actual: float | None = None,
    release_qualitative: bool = False,
    release_low: float | None = None,
    release_high: float | None = None,
    release_basis: str = "level",
    ciq_period: str | None = None,
    release_period: str | None = None,
    later_release: tuple[date, float | None, float | None, str | None] | None = None,
) -> GuideVerification:
    """Cross-check the CIQ guide against the release-parsed guide. VENDOR-ECHO requires BOTH: CIQ
    guide ≈ prior-FY actual (0.1% relative, source-rounding) AND the release gives NO corroborating
    number for this metric (absent or QUALITATIVE) — a stale carry-forward the primary source does
    not confirm. Cross-source VERIFIED when the CIQ and release ranges match; else a mismatch.

    THE OUTCOME: VERIFIED agrees and MISMATCH differs; every other branch is a check that did NOT
    run — a refusal (cross-basis, cross-period), a missing side, and the vendor-echo and
    plausibility flags alike, because none of them sets CIQ's guide against a release number.

    ``later_release`` (filed, low, high, period) — a release filed after CIQ's guide that guides
    something else (`mechanical._guide_verification`, 2026-10-27). It moves no outcome: the release
    above is the one of CIQ's date. It is NAMED, so a guide the company has since moved never
    reads as the guide in force."""
    if later_release is not None and ciq_low is not None:
        base = guide_verification_read(
            metric, ciq_low, ciq_high, prior_fy_actual=prior_fy_actual,
            release_qualitative=release_qualitative, release_low=release_low,
            release_high=release_high, release_basis=release_basis, ciq_period=ciq_period,
            release_period=release_period)
        filed, lo, hi, period = later_release
        return GuideVerification(
            f"{base.line}; a later release (filed {filed.isoformat()}, {period}) guides "
            f"{lo}–{hi} — CIQ's guide predates it", base.check)
    if ciq_low is None:
        return GuideVerification(
            f"guide verification ({metric}): CIQ guide UNKNOWN — not cross-checked", CHECK_NOT_RUN)
    # CROSS-BASIS: REFUSE, NEVER DERIVE (2026-08-05). CIQ guides a LEVEL; a release can guide a
    # CHANGE ("net sales expected to range between -2% and +2% year-over-year"). Comparing -2..+2
    # against 1,345..1,355 is meaningless, and the tempting fix — derive a level from the prior
    # period — CROSSES SOURCES MID-CHECK: the prior-year figure lives in a CIQ series whose gross
    # margin need not share the filer's definition, so a filing-derived guide would be verified
    # against a vendor-derived base. That is the operating-vs-EBITDA lesson applied to a base we
    # would be manufacturing. Refusing loses no verification: before this the change guide was
    # dropped entirely, so "not cross-checked" is strictly more than the nothing it replaces.
    if release_basis == "change" and release_low is not None:
        return GuideVerification(
            f"guide verification ({metric}): CIQ guides a LEVEL ({ciq_low}–{ciq_high}) and the "
            f"release guides a CHANGE ({release_low}–{release_high}) — NOT CROSS-CHECKED. "
            "Deriving a level from the prior period would compare a filing-derived guide "
            "against a vendor-derived base; the two need not share a definition.", CHECK_NOT_RUN)
    # CROSS-PERIOD: REFUSE, the same way (2026-08-12). The two sources need not guide the SAME
    # period, and nothing here checked it: NFLX's CIQ revenue guide is FQ3 2026 (12,860.0) while the
    # release guides FY2026 ($50.7–51.7bn). Compared as bare numbers they cannot agree, so the check
    # printed MISMATCH — reading as a management-execution failure — when 12,860 × 4 = 51,440 sits
    # INSIDE the annual guide and the two corroborate. Scaling a quarter to a year to force the
    # comparison would be the manufactured base the cross-basis refusal above already rejects (a
    # guide is not four equal quarters). Only refuse when BOTH labels decide a scope and the scopes
    # differ; an unrecognised label leaves the prior behaviour untouched.
    if release_low is not None:
        ciq_scope, rel_scope = period_scope(ciq_period), period_scope(release_period)
        if ciq_scope is not None and rel_scope is not None and ciq_scope != rel_scope:
            # reads as English in the rendered line ("guides a QUARTER … guides a HALF-YEAR")
            noun = {"quarter": "QUARTER", "half": "HALF-YEAR", "annual": "YEAR"}
            return GuideVerification(
                f"guide verification ({metric}): CIQ guides a {noun[ciq_scope]} "
                f"({ciq_period}: {ciq_low}–{ciq_high}) and the release guides a "
                f"{noun[rel_scope]} ({release_period}: {release_low}–{release_high}) "
                "— NOT CROSS-CHECKED. Different periods; annualising one to match the other "
                "would manufacture the base the comparison is supposed to verify.", CHECK_NOT_RUN)
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
        return GuideVerification(
            f"guide verification ({metric}): CIQ FY guide {ciq_low} ≈ prior-FY actual "
            f"{prior_fy_actual} (within source-rounding) → VENDOR-ECHO flag (stale "
            f"carry-forward); {tail}", CHECK_NOT_RUN)
    if release_qualitative and release_low is None:
        return GuideVerification(
            f"guide verification ({metric}): CIQ {ciq_low}–{ciq_high} vs release QUALITATIVE "
            "→ plausibility flag; render the qualitative growth line", CHECK_NOT_RUN)
    if release_low is None:  # release stated no numeric guide — nothing to cross-check
        return GuideVerification(
            f"guide verification ({metric}): CIQ {ciq_low}–{ciq_high} vs release "
            "NO NUMERIC OUTLOOK → not cross-checked", CHECK_NOT_RUN)
    # release_low is now narrowed to a float by the early return above (no redundant None re-check).
    if abs(ciq_low - release_low) < GUIDE_MATCH and abs(
            (ciq_high or 0.0) - (release_high or 0.0)) < GUIDE_MATCH:
        return GuideVerification(
            f"guide verification ({metric}): CIQ {ciq_low}–{ciq_high} vs release "
            f"{release_low}–{release_high} → cross-source VERIFIED", CHECK_AGREE)
    return GuideVerification(
        f"guide verification ({metric}): CIQ {ciq_low}–{ciq_high} vs release "
        f"{release_low}–{release_high} → MISMATCH flag", CHECK_DIFFER)
