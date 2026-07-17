"""Mid-cycle & scenarios — the cyclical-underwriting primitive. Deterministic, no LLM.

A trailing multiple on trough earnings reads "expensive" and a trailing multiple on peak earnings
reads "cheap"; neither is the bar. This block assembles the ANCHORS a human needs to underwrite a
cyclical on mid-cycle economics, then does the ARITHMETIC on the analyst's own scenarios. It
proposes nothing: every scenario assumption is supplied by the human (or is the anchor default,
labelled as such); the machine computes value, placement, the ratio, and sensitivity.

REWARD-TO-RISK CONVENTION (operator-ratified 2026-07-16 — the fund's definition of its ≥2:1 bar):

    reward = (base value per share − spot price)
    risk   = (spot price − bear value per share)
    Both measured at SPOT, not entry. BULL is computed and PRINTED (upside shape + base
    discipline) but is NEVER in the ratio. The ratio is a PRICE RATIO only — no probability
    weights, no stops. Bar: >= 2:1 (analyst-specified).
    Degenerate cases fail loud, never silently: bear >= spot → "risk undefined (bear at or above
    spot)"; base <= spot → reward is negative/zero, printed plainly.

PRECEDENT: RCAT (~1:1) / AVAV (~1.3:1) are PRE-CONVENTION — asserted in frozen prose, not
reproducible from recorded inputs. They are NOT back-filled and their frozen rationales are not
altered (ratified 2026-07-04, leave-as-is). This convention binds FORWARD.

SOURCE DISCIPLINE. The annual series come from EDGAR XBRL (free). ``extract_points`` resolves a
concept's aliases FIRST-HIT-WINS, which silently truncates a filer that switched tags (WERN:
``RevenueFromContractWithCustomerExcludingAssessedTax`` = 4y vs ``Revenues`` = 18y). This block
therefore selects the alias with the LONGEST annual coverage and reports the tag it used — ONE tag,
ONE basis, never a splice across tags (mixing ASC-606 and pre-606 revenue bases would be a
mixed-layer derivation). The shared extractor is left unchanged.
"""
from __future__ import annotations

import statistics as st
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from vinci.edgar.concepts import CONCEPT_ALIASES, ConceptPoint, extract_points

MIN_YEARS = 10   # the anchor window; below this we print ACTUAL coverage, never extrapolate
BAR = 2.0               # the fund's ≥2:1 reward-to-risk bar (analyst-specified)
CONVENTION_TEXT = (
    "reward = (base value per share − spot); risk = (spot − bear value per share); both at SPOT, "
    "not entry. Bull is printed but NEVER in the ratio. Price ratio only — no probability weights, "
    "no stops. Bar: >= 2:1 (operator-ratified 2026-07-16)."
)


@dataclass(frozen=True)
class AnnualSeries:
    """One concept's annual history from ONE us-gaap tag (single basis, never spliced)."""

    concept: str
    tag: str | None                      # the alias actually used (None → no data at all)
    by_year: dict[int, float]
    accession_by_year: dict[int, str | None]

    @property
    def years(self) -> list[int]:
        return sorted(self.by_year)

    @property
    def n_years(self) -> int:
        return len(self.by_year)


def annual_series(facts: dict[str, Any], concept: str) -> AnnualSeries:
    """The annual series for ``concept``, taking the alias with the LONGEST annual coverage (ties →
    CONCEPT_ALIASES priority). One tag = one basis; we never splice tags into a single series."""
    best: AnnualSeries | None = None
    for tag in CONCEPT_ALIASES[concept]:
        by_year: dict[int, float] = {}
        acc: dict[int, str | None] = {}
        filed: dict[int, date] = {}
        for p in _points_for_tag(facts, concept, tag):
            y = p.period_end.year
            # latest-FILED wins for a restated year; same tag throughout, so the basis is stable
            if y not in by_year or (p.filed and (y not in filed or p.filed > filed[y])):
                by_year[y] = p.value
                acc[y] = p.accession
                if p.filed:
                    filed[y] = p.filed
        cand = AnnualSeries(concept=concept, tag=tag, by_year=by_year, accession_by_year=acc)
        if best is None or cand.n_years > best.n_years:
            best = cand
    return best or AnnualSeries(concept=concept, tag=None, by_year={}, accession_by_year={})


def _points_for_tag(facts: dict[str, Any], concept: str, tag: str) -> list[ConceptPoint]:
    """Annual points reported under exactly ``tag`` (reuses the shared extractor's parse by
    restricting the alias list to one tag — no re-implementation of XBRL parsing)."""
    saved = CONCEPT_ALIASES[concept]
    try:
        CONCEPT_ALIASES[concept] = [tag]
        return [p for p in extract_points(facts, concept) if p.is_annual]
    finally:
        CONCEPT_ALIASES[concept] = saved


@dataclass(frozen=True)
class MarginAnchor:
    """ANCHOR A — the name's own operating-margin history (mid-cycle from its own cycle)."""

    by_year: dict[int, float]            # year → operating margin (fraction)
    revenue_tag: str | None
    opinc_tag: str | None
    note: str = ""

    @property
    def years(self) -> list[int]:
        return sorted(self.by_year)

    @property
    def n_years(self) -> int:
        return len(self.by_year)

    @property
    def values(self) -> list[float]:
        return [self.by_year[y] for y in self.years]

    @property
    def median(self) -> float | None:
        return st.median(self.values) if self.by_year else None

    @property
    def trough(self) -> float | None:
        return min(self.values) if self.by_year else None

    @property
    def peak(self) -> float | None:
        return max(self.values) if self.by_year else None

    def quartiles(self) -> tuple[float, float] | None:
        """(q1, q3) — None when too few points for a stable read."""
        v = sorted(self.values)
        if len(v) < 4:
            return None
        return _pctile(v, 0.25), _pctile(v, 0.75)

    @property
    def covers_window(self) -> bool:
        return self.n_years >= MIN_YEARS

    @property
    def coverage_note(self) -> str:
        if not self.by_year:
            return "UNDEFINED — no overlapping revenue/operating-income years"
        span = f"{self.years[0]}–{self.years[-1]}"
        if self.covers_window:
            return f"{self.n_years}y ({span})"
        return (f"{self.n_years}y ({span}) — SHORT of the {MIN_YEARS}y window; actual coverage "
                f"printed, NOT extrapolated")


def _pctile(sorted_vals: list[float], q: float) -> float:
    """Linear-interpolated quantile on a sorted list (deterministic; no numpy)."""
    if not sorted_vals:
        raise ValueError("empty")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def percentile_of(value: float, sample: list[float]) -> float | None:
    """The percentile ``value`` occupies within ``sample`` (fraction ≤ value / n). None if empty."""
    if not sample:
        return None
    return sum(1 for x in sample if x <= value) / len(sample)


def margin_anchor(revenue: AnnualSeries, opinc: AnnualSeries, *, note: str = "") -> MarginAnchor:
    """Operating margin per year, on the years BOTH series report. Zero/negative revenue years are
    dropped (a margin on non-positive revenue is not a number)."""
    by_year: dict[int, float] = {}
    for y in sorted(set(revenue.by_year) & set(opinc.by_year)):
        rev = revenue.by_year[y]
        if rev and rev > 0:
            by_year[y] = opinc.by_year[y] / rev
    return MarginAnchor(by_year=by_year, revenue_tag=revenue.tag, opinc_tag=opinc.tag, note=note)


# --- (b) FUEL-SURCHARGE SPLIT -------------------------------------------------------------------
_FUEL_HINTS = ("fuelsurcharge", "surcharge")


def fuel_surcharge_tags(facts: dict[str, Any]) -> list[str]:
    """us-gaap/custom tags that look like separately-disclosed fuel-SURCHARGE REVENUE. A fuel COST
    tag (e.g. ``FuelCosts``) is NOT a surcharge-revenue disclosure — never treat it as one."""
    out: list[str] = []
    for ns, node in (facts.get("facts") or {}).items():
        for tag in node:
            low = tag.lower()
            if any(h in low for h in _FUEL_HINTS) and "cost" not in low and "expense" not in low:
                out.append(f"{ns}:{tag}")
    return sorted(out)


@dataclass(frozen=True)
class FuelSplit:
    """Margins computed BOTH ways when surcharge revenue is separately disclosed. We never pick
    one — a surcharge-inclusive margin is diluted by a pass-through; excluding it changes the
    denominator only. Not disclosed → ``disclosed`` False, only the as-reported read exists."""

    disclosed: bool
    tags_found: list[str]
    incl: MarginAnchor | None = None     # as-reported (surcharge INSIDE revenue)
    excl: MarginAnchor | None = None     # surcharge revenue removed from the denominator
    note: str = ""


def fuel_split(facts: dict[str, Any], revenue: AnnualSeries, opinc: AnnualSeries) -> FuelSplit:
    tags = fuel_surcharge_tags(facts)
    incl = margin_anchor(revenue, opinc, note="as-reported (surcharge inside revenue)")
    if not tags:
        return FuelSplit(
            disclosed=False, tags_found=[], incl=incl,
            note=("fuel-surcharge revenue is NOT separately XBRL-tagged for this filer — only the "
                  "as-reported margin exists here; the split, if needed, must come from the 10-K "
                  "revenue table by hand"))
    ns_tag = tags[0].split(":", 1)[1]
    saved = CONCEPT_ALIASES.get("revenue")
    try:
        CONCEPT_ALIASES["_fuel_surcharge"] = [ns_tag]
        fuel = annual_series(facts, "_fuel_surcharge")
    finally:
        CONCEPT_ALIASES.pop("_fuel_surcharge", None)
        if saved is not None:
            CONCEPT_ALIASES["revenue"] = saved
    ex_rev = AnnualSeries(
        concept="revenue_ex_fuel", tag=revenue.tag,
        by_year={y: revenue.by_year[y] - fuel.by_year[y]
                 for y in sorted(set(revenue.by_year) & set(fuel.by_year))
                 if revenue.by_year[y] - fuel.by_year[y] > 0},
        accession_by_year=revenue.accession_by_year)
    return FuelSplit(
        disclosed=True, tags_found=tags, incl=incl,
        excl=margin_anchor(ex_rev, opinc, note=f"surcharge revenue removed ({tags[0]})"),
        note="BOTH margins printed — the machine does not pick one")


# --- (c) ANCHOR B — peers ------------------------------------------------------------------------
@dataclass(frozen=True)
class PeerAnchor:
    """Cross-peer band. A peer with < MIN_YEARS of margin history is EXCLUDED and NAMED — never
    silently dropped, never averaged in on a short history."""

    included: dict[str, MarginAnchor] = field(default_factory=dict)
    excluded: dict[str, str] = field(default_factory=dict)   # ticker → loud reason

    @property
    def peer_medians(self) -> dict[str, float]:
        return {t: m for t, a in self.included.items() if (m := a.median) is not None}

    @property
    def band_median(self) -> float | None:
        """The cross-peer median OF each peer's own long-history median."""
        v = list(self.peer_medians.values())
        return st.median(v) if v else None


def peer_anchor(per_peer: dict[str, MarginAnchor]) -> PeerAnchor:
    inc: dict[str, MarginAnchor] = {}
    exc: dict[str, str] = {}
    for t, a in per_peer.items():
        if a.n_years == 0:
            exc[t] = "EXCLUDED — no overlapping revenue/operating-income years on EDGAR"
        elif not a.covers_window:
            exc[t] = (f"EXCLUDED — only {a.n_years}y of margin history "
                      f"({a.years[0]}–{a.years[-1]}), short of the {MIN_YEARS}y window")
        else:
            inc[t] = a
    return PeerAnchor(included=inc, excluded=exc)


# --- (2) SCENARIO GRID ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Scenario:
    """One analyst-supplied (or anchor-default) scenario. The machine NEVER proposes assumptions."""

    name: str                      # bear | base | bull
    revenue: float                 # $ (same unit as the series)
    margin: float                  # operating margin, fraction
    multiple: float                # EV / operating income (turns)
    source: str                    # "analyst" | "anchor default"
    reason: str | None = None


class ScenarioError(ValueError):
    """A scenario the machine refuses to compute — e.g. a deviation with no reason."""


def build_scenario(name: str, *, revenue: float, multiple: float, anchor_margin: float | None,
                   margin: float | None = None, reason: str | None = None) -> Scenario:
    """The analyst supplies; the machine labels and refuses. Margin omitted → the A/B ANCHOR
    DEFAULT (labelled). A supplied margin that DEVIATES from the anchor requires a reason —
    ``ScenarioError`` otherwise. The machine never proposes an assumption."""
    if margin is None:
        if anchor_margin is None:
            raise ScenarioError(
                f"{name}: no margin supplied and no anchor default available (anchor UNDEFINED) — "
                f"supply margin=… with --reason-{name}")
        return Scenario(name=name, revenue=revenue, margin=anchor_margin, multiple=multiple,
                        source="anchor default", reason=reason)
    deviates = anchor_margin is None or abs(margin - anchor_margin) > 1e-12
    if deviates and not (reason and reason.strip()):
        anchor_txt = "n/a" if anchor_margin is None else f"{anchor_margin:.4f}"
        raise ScenarioError(
            f"{name}: margin {margin:.4f} deviates from the anchor default ({anchor_txt}) — "
            f"--reason-{name} is required; refusing to compute a deviated scenario with no reason")
    return Scenario(name=name, revenue=revenue, margin=margin, multiple=multiple,
                    source="analyst" if deviates else "anchor default", reason=reason)


@dataclass(frozen=True)
class ScenarioValue:
    op_income: float
    ev: float
    equity: float
    vps: float


def scenario_value(s: Scenario, *, net_debt: float, shares: float) -> ScenarioValue:
    """revenue × margin → operating income → × multiple → EV → − net debt → equity → ÷ shares."""
    if shares <= 0:
        raise ValueError("shares must be > 0")
    oi = s.revenue * s.margin
    ev = oi * s.multiple
    eq = ev - net_debt
    return ScenarioValue(op_income=oi, ev=ev, equity=eq, vps=eq / shares)


@dataclass(frozen=True)
class RewardRisk:
    """THE CONVENTION, computed. ``undefined`` is set (and ratio None) when risk is undefined."""

    reward: float | None
    risk: float | None
    ratio: float | None
    undefined: str | None = None
    convention: str = CONVENTION_TEXT

    @property
    def clears_bar(self) -> bool | None:
        return None if self.ratio is None else self.ratio >= BAR


def reward_risk(*, base_vps: float, bear_vps: float, spot: float) -> RewardRisk:
    """reward = base − spot; risk = spot − bear; both at SPOT. Bull is NOT in the ratio.
    Degenerate: bear >= spot → risk undefined; base <= spot → reward <= 0, printed plainly."""
    reward = base_vps - spot
    risk = spot - bear_vps
    if risk <= 0:
        return RewardRisk(reward=reward, risk=risk, ratio=None,
                          undefined="risk undefined (bear at or above spot)")
    return RewardRisk(reward=reward, risk=risk, ratio=reward / risk)


def sensitivity(base: Scenario, bear: Scenario, *, net_debt: float, shares: float, spot: float,
                margin_step: float = 0.01, multiple_step: float = 1.0) -> list[dict[str, Any]]:
    """The ratio at base margin ±1pt and base multiple ±1 turn (bear held fixed — the risk leg is
    the analyst's floor, not a sensitivity axis). Small, deterministic grid."""
    rows: list[dict[str, Any]] = []
    for dm in (-margin_step, 0.0, margin_step):
        for dx in (-multiple_step, 0.0, multiple_step):
            b = Scenario(name=base.name, revenue=base.revenue, margin=base.margin + dm,
                         multiple=base.multiple + dx, source=base.source, reason=base.reason)
            if b.multiple <= 0:
                rows.append({"d_margin": dm, "d_multiple": dx, "ratio": None,
                             "undefined": "multiple <= 0"})
                continue
            rr = reward_risk(base_vps=scenario_value(b, net_debt=net_debt, shares=shares).vps,
                             bear_vps=scenario_value(bear, net_debt=net_debt, shares=shares).vps,
                             spot=spot)
            rows.append({"d_margin": dm, "d_multiple": dx, "ratio": rr.ratio,
                         "undefined": rr.undefined})
    return rows
