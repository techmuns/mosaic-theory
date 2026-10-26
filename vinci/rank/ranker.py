"""The ranker / triage layer — orders the screen's ~307 undifferentiated Edge-2 candidates into a
priority queue so a 2-person team deep-pulls the most structurally-promising overshoots first and
the tail expires.

WHAT THIS IS — and IS NOT
-------------------------
- **NOT a second screen.** It adds NO filtering. It ORDERS what the screen already passed.
- **NOT an alpha model.** It does NOT predict returns and is NEVER trained/tuned on forward returns.
- **NOT a decision-maker.** It ORDERS; the human deep-pulls and judges each name downstream.
It describes the structural setup that ALREADY EXISTS so the human can prioritise — a
lagging/coincident act by design. The leading judgment ("will this overshoot revert?") is the
human's job downstream, never a signal computed here.

TUNING DISCIPLINE — load-bearing, read before touching the weights
------------------------------------------------------------------
The weights in :class:`RankWeights` are set/adjusted by EYEBALLING whether the queue-top looks like
genuine overshoots — by **face-validity** — **NEVER** by checking which weights would have paid.
There is NO code path in this module that reads forward returns, post-screen prices, or the
BUY−AVOID spread: it imports nothing from ``vinci.scoring`` / ``vinci.ledger``, and the ranker is
handed a *screen-time* candidate only. Tuning weights against P&L is the backtest trap the whole
project rejects. Keep this layer legible, not clever — reliability comes from being readable
top-to-bottom, every position defensible.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, model_validator

from vinci.rank.profile import (
    AxisCoverage,
    AxisScore,
    CauseClass,
    LiquidityTier,
    RankedCandidate,
    StructuralDisqualifier,
)
from vinci.schemas.candidate import CandidateRecord

if TYPE_CHECKING:
    from vinci.screens.annotations import ScreenAnnotation
from vinci.schemas.data_record import DataRecord, EventType, Fundamentals, PriceFeatures

# --- Tier-1 axis calibration (face-validity constants; see the module docstring on tuning) ----
# Map the admitted drawdown band [−30% gate, −85% terminal floor] onto [0, 1]: deeper ranks higher
# (a deeper, sharper fall is a likelier overreaction). The screen already excludes < −85% (terminal
# by magnitude) and > −30% (too shallow), so this maps the *admitted* range.
_DD_GATE = 0.30
_DD_FLOOR = 0.85
# Idiosyncrasy anchor: a name underperforming the market (IWM) by this much over the decline window
# earns full credit. Idiosyncratic dislocation is where mispricing lives — THE most on-thesis axis.
_IDIO_FULL = 0.60
# Multiple-at-floor: G3 admits only a current multiple in the bottom ``_MULT_FLOOR_PCTILE`` of a
# name's OWN ~5y range; we map [0, floor] → [1, 0] so the cheapest-vs-its-own-history names earn the
# most credit. (UNKNOWN — negative earnings / absent XBRL — is handled by the fail-loud path below.)
_MULT_FLOOR_PCTILE = 0.25
# FAIL-LOUD: an UNKNOWN Tier-1 quality axis earns NO credit and is flagged as a depth task — never
# imputed. A name must rank on what we can CONFIRM; missing data ranks lower, explicitly.
_UNKNOWN_AXIS_SCORE = 0.0

# Drawdown CHARACTER — sharp/discrete/recent fall vs slow grind/bleed. ONE axis today *on purpose*:
# "shape" (sharp vs grind) and "cause" (discrete event vs unexplained bleed) both rest on the SAME
# EOD gap-down detector (the only event source wired), so treating them as two independent axes
# would be false precision. A discrete, recent drop is the overshoot signature (ranks higher); a
# grind/bleed is "more often real deterioration" (ranks lower); many repeated gaps ease the score
# off (accumulating bad news, messier — never reward "more violent" as "more promising"). The
# Tier-3 LLM cause-flag COLOURS this axis (demote/boost), never sets it.
# SPLIT THIS BACK into a price-geometry "shape" axis + a filing-text "cause" axis once 8-K/guidance
# TEXT events and the LLM annotation populate cause INDEPENDENTLY of price geometry (see §4/§5).
_CHAR_BLEED = 0.30  # no discrete catalyst (slow grind/bleed) → ranks lower
_CHAR_DISCRETE_BASE = 0.80  # an identifiable discrete de-rating event (gap-down) → ranks higher
# Gentle sharpness easing by gap-down count: a single clean discrete drop is the archetype overshoot
# and repeated gaps are messier. A multiplier on the (recency-bumped) discrete base.
_SHARPNESS_BY_GAPS: dict[int, float] = {1: 1.0, 2: 0.97, 3: 0.94}
_SHARPNESS_MANY_GAPS = 0.90  # 4+ gap-downs
_CHAR_STRUCTURAL_BREAK = 0.05  # Tier-3 LLM: terminal-looking (lost customer / reg kill / fraud)
_CHAR_MEAN_REVERT = 0.97  # Tier-3 LLM: confirmed mean-revert candidate
_DECLINE_WINDOW_DAYS = 180  # the screen's gap-down detection window (for catalyst recency)

# Tier-2 volume overlay (MINOR). The only bar readable from a screen-time record is current volume
# vs its 90d average. THE SIGN'S RATIONALE (face-validity, never returns): low reads as panic
# exhausted (a clean-setup plus); high reads as a falling-knife caution. This is NOT a
# smart-money-accumulation signal — that flow is private/microsecond and we are structurally late;
# public volume is coincident-to-lagging and strip-mined. Bounded small on purpose: it sharpens the
# ranking, it is not a pillar.
#
# THE RATIONALE IS NOT THE LABEL (audit 2026-08-12, STATE.md §5). The input is ONE session's share
# volume over a 90d average — no price direction — so a displayed label may describe the MAGNITUDE
# and never the MECHANISM. The old strings said "exhausted" and "heavy distribution", naming who
# traded and why from a number containing neither: on the 2026-07-29 queue, 2 of the 10 names
# labelled "heavy distribution" closed UP that session (VRRM +22.0% on 3.6×, at rank 5). The bands
# below are now plainly descriptive and state their basis. Unchanged: every ± value, and the
# thresholds — re-banding on the audit's forward-return numbers would be tuning on outcomes.
_VOL_EXHAUSTED = 0.80
_VOL_ELEVATED = 1.50
_VOL_HEAVY = 3.00
_VOL_BONUS = 0.05
_VOL_CAUTION_SMALL = -0.02
_VOL_CAUTION = -0.05

# Tradeability. Liquidity DISPLAY tiers (face-validity bands, NOT a filter) on 90d ADV ($).
_ADV_AMPLE = 25_000_000.0
_ADV_WORKABLE = 5_000_000.0
# The GATE: below this 90d-ADV floor a name is de-prioritised + flagged (a concentrated position
# can't be built, so deep work isn't worth it). It defaults to the universe's OWN ADV floor → a
# no-op re-check that adds NO filtering (this layer is NOT a second screen). Raise it to push thin
# names down the queue without dropping them.
_DEEP_WORK_ADV_FLOOR = 3_000_000.0
_GATED_SCORE_MULT = 0.5
# Tier-3 deterministic structural-disqualifier: a fired 8-K signal SINKS the name. The cap is set
# with min() so it can ONLY lower a score (DEMOTE-ONLY — there is no promote path), and disqualified
# names sort below the live queue. Stops the team wasting CIQ deep-pull effort on structurally-dead
# names; never a return signal.
_STRUCTURAL_SINK_CAP = 0.05


class RankWeights(BaseModel, frozen=True):
    """Face-validity weights over the Tier-1 structural axes. Sum to 1.0 (a clean 0..1 composite).

    Set by eyeballing the queue-top, NEVER by forward returns (see the module docstring). Their
    *ordering of magnitude* encodes the thesis, not an optimisation:
      - **idiosyncrasy** is THE most on-thesis axis (idiosyncratic dislocation = where mispricing
        lives; market beta is not) → the largest weight.
      - **depth** is the screen's defining, fully-covered signal → second.
      - **character** (sharp/discrete/recent fall vs grind/bleed) ties depth — it rests on the
        gap-down detector, kept at ~0.25 so one EOD signal can't dominate. SPLITS into shape + cause
        once 8-K/guidance TEXT events land (then re-weight the two halves).
      - **multiple-at-floor** (cheap vs its OWN history) → fourth.
    """

    idiosyncrasy: float = 0.30
    depth: float = 0.25
    character: float = 0.25
    multiple: float = 0.20

    @model_validator(mode="after")
    def _sum_to_one(self) -> RankWeights:
        total = self.idiosyncrasy + self.depth + self.character + self.multiple
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"Tier-1 weights must sum to 1.0 (got {total})")
        return self

    def as_map(self) -> dict[str, float]:
        return {
            "idiosyncrasy": self.idiosyncrasy,
            "depth": self.depth,
            "character": self.character,
            "multiple": self.multiple,
        }


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _gap_down_dates(rec: DataRecord) -> list[date]:
    return sorted(
        e.event_date for e in rec.events if e.event_type is EventType.EARNINGS_GAP_DOWN
    )


# --- Tier-1 axes ------------------------------------------------------------------------------
def depth_axis(prices: PriceFeatures) -> AxisScore:
    """Drawdown depth: distance from the 52w high, over the admitted band. Deeper → higher."""
    f = prices.drawdown_from_high
    if not f.is_evaluable or f.value is None:
        return AxisScore(
            axis="depth", score=None, coverage=AxisCoverage.UNKNOWN,
            label="UNKNOWN — insufficient price history",
        )
    dd = f.value  # negative fraction
    score = _clip01((-dd - _DD_GATE) / (_DD_FLOOR - _DD_GATE))
    return AxisScore(
        axis="depth", score=score, coverage=AxisCoverage.PRESENT,
        label=f"{dd:.0%} from 52w high", raw=dd,
    )


def idiosyncrasy_axis(prices: PriceFeatures) -> AxisScore:
    """Idiosyncrasy: how much of the fall is name-specific vs the market (IWM) — the G2 input."""
    f = prices.rel_ret_vs_market
    if not f.is_evaluable or f.value is None:
        return AxisScore(
            axis="idiosyncrasy", score=None, coverage=AxisCoverage.UNKNOWN,
            label="UNKNOWN — no clean market benchmark",
        )
    rel = f.value  # negative == underperformed the market (IWM)
    score = _clip01(-rel / _IDIO_FULL)
    return AxisScore(
        axis="idiosyncrasy", score=score, coverage=AxisCoverage.PRESENT,
        label=f"{rel:+.0%} vs market", raw=rel,
    )


def multiple_axis(funds: Fundamentals) -> AxisScore:
    """Multiple vs its OWN ~5y history: bottom-decile (at-floor) → higher. EV/EBITDA, else P/E."""
    f = funds.ev_ebitda_pctile_vs_history
    metric = "EV/EBITDA"
    if not f.is_evaluable or f.value is None:
        f = funds.pe_pctile_vs_history
        metric = "P/E"
    if not f.is_evaluable or f.value is None:
        return AxisScore(
            axis="multiple", score=None, coverage=AxisCoverage.UNKNOWN,
            label="UNKNOWN — XBRL absent / negative earnings",
        )
    pctile = f.value
    score = _clip01((_MULT_FLOOR_PCTILE - pctile) / _MULT_FLOOR_PCTILE)
    return AxisScore(
        axis="multiple", score=score, coverage=AxisCoverage.PRESENT,
        label=f"{metric} {pctile:.0%}ile of own 5y range", raw=pctile,
    )


def character_axis(rec: DataRecord, cause_class: CauseClass) -> AxisScore:
    """Drawdown character: sharp/discrete/recent fall (overshoot signature → higher) vs slow
    grind/bleed (→ lower), eased off for many repeated gaps, COLOURED by the Tier-3 LLM cause-flag.

    ONE axis today on purpose — shape (price geometry) and cause (catalyst) both rest on the same
    EOD gap-down detector, so splitting them now is false precision. Split back out when 8-K/
    guidance TEXT events let cause read the filing independently of price. Always evaluable (a grind
    is a *known* zero-gap state, not missing data).
    """
    gaps = _gap_down_dates(rec)
    ref = rec.as_of
    n = len(gaps)
    if n == 0:
        base = _CHAR_BLEED
        label = "grind/bleed — no discrete gap-down"
    else:
        recent = gaps[-1]
        recency = 1.0
        age_txt = ""
        if ref is not None:
            age = (ref - recent).days
            recency = _clip01(1.0 - age / _DECLINE_WINDOW_DAYS)
            age_txt = f", {age}d ago"
        base = _CHAR_DISCRETE_BASE + (1.0 - _CHAR_DISCRETE_BASE) * recency
        base *= _SHARPNESS_BY_GAPS.get(n, _SHARPNESS_MANY_GAPS)  # ease off for many repeated gaps
        s = "" if n == 1 else "s"
        label = f"sharp discrete — {n} gap-down{s} (latest {recent.isoformat()}{age_txt})"

    # Tier-3 LLM annotation COLOURS the character; it never sets the primary sort key.
    if cause_class is CauseClass.STRUCTURAL_BREAK:
        return AxisScore(
            axis="character", score=_CHAR_STRUCTURAL_BREAK, coverage=AxisCoverage.PRESENT,
            label=f"{label} · LLM: structural-break (demoted)", raw=base,
        )
    if cause_class is CauseClass.MEAN_REVERT:
        return AxisScore(
            axis="character", score=max(base, _CHAR_MEAN_REVERT), coverage=AxisCoverage.PRESENT,
            label=f"{label} · LLM: mean-revert", raw=base,
        )
    return AxisScore(
        axis="character", score=base, coverage=AxisCoverage.PRESENT,
        label=f"{label} · LLM: —", raw=base,
    )


# --- Tier-2 volume overlay + tradeability -----------------------------------------------------
def volume_overlay(prices: PriceFeatures) -> tuple[float, str]:
    """A MINOR ± adjustment from the latest session's volume vs its 90d average.

    The returned label describes the MAGNITUDE and states its basis. It must never name a mechanism
    (who traded, and why) — the input carries no price direction, so any such word is a guess. See
    the band comment above and the 2026-08-12 audit in STATE.md §5.
    """
    f = prices.volume_spike
    if not f.is_evaluable or f.value is None:
        return 0.0, "UNKNOWN"
    vs = f.value
    if vs <= _VOL_EXHAUSTED:
        return _VOL_BONUS, f"quiet ({vs:.2f}× vs 90d avg)"
    if vs <= _VOL_ELEVATED:
        return 0.0, f"normal ({vs:.2f}× vs 90d avg)"
    if vs <= _VOL_HEAVY:
        return _VOL_CAUTION_SMALL, f"elevated ({vs:.2f}× vs 90d avg)"
    return _VOL_CAUTION, f"heavy ({vs:.1f}× vs 90d avg)"


def liquidity_tier(adv_usd: float) -> LiquidityTier:
    if adv_usd >= _ADV_AMPLE:
        return LiquidityTier.AMPLE
    if adv_usd >= _ADV_WORKABLE:
        return LiquidityTier.WORKABLE
    return LiquidityTier.THIN


# --- the composite ----------------------------------------------------------------------------
def rank_candidate(
    cand: CandidateRecord,
    *,
    weights: RankWeights | None = None,
    cause_class: CauseClass = CauseClass.UNCLASSIFIED,
    market_cap: float | None = None,
    structural_flag: StructuralDisqualifier | None = None,
    deep_work_adv_floor: float = _DEEP_WORK_ADV_FLOOR,
) -> RankedCandidate:
    """Score one candidate into a :class:`RankedCandidate` (``rank`` is assigned later, on sort).

    A TRANSPARENT weighted composite of the Tier-1 axes, + the Tier-2 volume overlay, × the
    tradeability gate. No learned model, no optimisation, no forward returns — a sort key you can
    read top-to-bottom.
    """
    w = weights or RankWeights()
    rec = cand.data_record
    prices = rec.prices

    axes: dict[str, AxisScore] = {
        "idiosyncrasy": idiosyncrasy_axis(prices),
        "depth": depth_axis(prices),
        "character": character_axis(rec, cause_class),
        "multiple": multiple_axis(rec.fundamentals),
    }
    weight = w.as_map()
    contributions: dict[str, float] = {}
    unknown_axes: list[str] = []
    quality = 0.0
    for name, ax in axes.items():
        s = ax.score if ax.score is not None else _UNKNOWN_AXIS_SCORE
        if ax.coverage is AxisCoverage.UNKNOWN:
            unknown_axes.append(name)
        contrib = weight[name] * s
        contributions[name] = contrib
        quality += contrib

    vol_adj, vol_state = volume_overlay(prices)

    # the RATIO itself, structurally — so no consumer ever has to parse it back out of vol_state
    vs_f = prices.volume_spike
    vol_spike = vs_f.value if (vs_f.is_evaluable and vs_f.value is not None) else None
    # and the weekly series beside it, for the queue's direction sparkline (display-only)
    vt_f = prices.volume_trend
    vol_trend = vt_f.value if (vt_f is not None and vt_f.is_evaluable and vt_f.value) else None

    adv_f = prices.adv_90d_usd
    adv_usd = adv_f.value if (adv_f.is_evaluable and adv_f.value is not None) else 0.0
    gated = adv_usd < deep_work_adv_floor

    score = _clip01(quality + vol_adj)
    if gated:
        score *= _GATED_SCORE_MULT
    # Tier-3 deterministic structural disqualifier — DEMOTE-ONLY: min() caps the score (it can only
    # LOWER, never raise), sinking a structurally-dead name. No promote path exists.
    structurally_disqualified = structural_flag is not None
    if structurally_disqualified:
        score = min(score, _STRUCTURAL_SINK_CAP)

    return RankedCandidate(
        candidate_id=cand.candidate_id,
        ticker=rec.identity.ticker,
        name=rec.identity.name,
        priority_score=score,
        rank=0,  # assigned by rank_candidates after the deterministic sort
        depth_band=cand.triage_band.value,
        axes=axes,
        contributions=contributions,
        quality=quality,
        volume_overlay=vol_adj,
        liquidity_tier=liquidity_tier(adv_usd),
        adv_usd=adv_usd,
        market_cap=market_cap,
        volume_state=vol_state,
        volume_spike=vol_spike,
        volume_trend=vol_trend,
        cause_class=cause_class,
        structurally_disqualified=structurally_disqualified,
        structural_flag=structural_flag,
        unknown_axes=unknown_axes,
        tradeability_gated=gated,
        profile_line=_profile_line(rec.identity.ticker, score, cand.triage_band.value, axes),
        screen_run_at=cand.screen_run_at,
    )


def rank_candidates(
    cands: list[CandidateRecord],
    *,
    weights: RankWeights | None = None,
    annotations: dict[str, CauseClass] | None = None,
    market_caps: dict[str, float] | None = None,
    structural_flags: dict[str, StructuralDisqualifier] | None = None,
    deep_work_adv_floor: float = _DEEP_WORK_ADV_FLOOR,
) -> list[RankedCandidate]:
    """Rank the whole candidate set into the priority queue (deterministic order, 1-based ``rank``).

    Sort: structurally-disqualified names sink to the very bottom (Tier-3, demote-only), then
    tradeable names first (the gate), then priority-score desc, then — for a stable, legible
    tie-break — deeper drawdown, then more-idiosyncratic, then ticker.
    """
    ann = annotations or {}
    caps = market_caps or {}
    struct = structural_flags or {}
    ranked: list[RankedCandidate] = []
    for c in cands:
        iid = c.data_record.identity.internal_id
        tk = c.data_record.identity.ticker
        cc = ann.get(iid) or ann.get(tk) or CauseClass.UNCLASSIFIED
        ranked.append(
            rank_candidate(
                c, weights=weights, cause_class=cc, market_cap=caps.get(iid),
                structural_flag=struct.get(iid) or struct.get(tk),
                deep_work_adv_floor=deep_work_adv_floor,
            )
        )

    def sort_key(r: RankedCandidate) -> tuple[bool, bool, float, float, float, str]:
        dd = r.axes["depth"].raw if r.axes["depth"].raw is not None else 0.0
        idio = r.axes["idiosyncrasy"].raw if r.axes["idiosyncrasy"].raw is not None else 0.0
        # structurally-disqualified sink to the absolute bottom; then gated; then score desc; deeper
        # (more negative dd) first; more idiosyncratic first; ticker.
        return (
            r.structurally_disqualified, r.tradeability_gated, -r.priority_score, dd, idio,
            r.ticker,
        )

    ranked.sort(key=sort_key)
    return [r.model_copy(update={"rank": i + 1}) for i, r in enumerate(ranked)]


def _profile_line(ticker: str, score: float, band: str, axes: dict[str, AxisScore]) -> str:
    def lab(name: str) -> str:
        return axes[name].label
    return (
        f"{ticker:<6} {score:.3f} [{band}]  "
        f"idio: {lab('idiosyncrasy')} | depth: {lab('depth')} | "
        f"character: {lab('character')} | mult: {lab('multiple')}"
    )


# --- loaders (operate on the committed snapshots — no DB, no network) -------------------------
def load_candidates_from_snapshot(path: Path) -> list[CandidateRecord]:
    """Load the screen's candidate-records from the committed ``candidate_records.jsonl``."""
    out: list[CandidateRecord] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out.append(CandidateRecord.model_validate_json(row["payload"]))
    return out


def load_market_caps_from_snapshot(path: Path) -> dict[str, float]:
    """Join size (market cap) from the committed ``universe_snapshot.jsonl`` by internal_id."""
    out: dict[str, float] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        mc = row.get("market_cap")
        if mc is not None:
            out[row["internal_id"]] = float(mc)
    return out


# --- legible rendering ------------------------------------------------------------------------
def _fmt_usd(x: float | None) -> str:
    if x is None:
        return "size —"
    if x >= 1e9:
        return f"${x / 1e9:.2f}B"
    return f"${x / 1e6:.1f}M"


def render_profile_block(r: RankedCandidate) -> str:
    """The full, auditable per-name profile: every axis, its sub-score, and its additive
    contribution (summing to ``quality``) — readable so you see *why* the name is where it is."""
    lines = [f"#{r.rank:<3} {r.ticker:<6} {r.priority_score:.3f}  [{r.depth_band}]  {r.name[:46]}"]
    if r.structural_flag is not None:
        lines.append(
            f"       ⛔ STRUCTURAL DISQUALIFIER (Tier-3, demote-only): {r.structural_flag.signal}"
        )
        lines.append(f"          ↳ {r.structural_flag.detail} · src: {r.structural_flag.source}")
    order = ["idiosyncrasy", "depth", "character", "multiple"]
    for name in order:
        ax = r.axes[name]
        contrib = r.contributions[name]
        s = "  UNK" if ax.score is None else f"{ax.score:.2f}"
        lines.append(f"       {name:<13} s={s}  +{contrib:.3f}   {ax.label}")
    gate = "  ⟂ GATED (below deep-work ADV floor)" if r.tradeability_gated else ""
    lines.append(
        f"       {'tradeability':<13} {r.liquidity_tier.value.upper():<8} "
        f"ADV {_fmt_usd(r.adv_usd)} · {_fmt_usd(r.market_cap)}{gate}"
    )
    lines.append(
        f"       {'volume (T2)':<13} {r.volume_overlay:+.2f}     {r.volume_state}"
    )
    lines.append(
        f"       {'= quality':<13} {r.quality:.3f}  + vol {r.volume_overlay:+.2f}  "
        f"→ score {r.priority_score:.3f}"
    )
    if r.unknown_axes:
        flagged = ", ".join(r.unknown_axes)
        lines.append(f"       depth-tasks (UNKNOWN, flagged not imputed): {flagged}")
    return "\n".join(lines)


def _md_cell(r: RankedCandidate, name: str) -> str:
    ax = r.axes[name]
    return "UNKNOWN" if ax.score is None else ax.label


def _pct(v: float) -> str:
    return f"{v * 100:+.1f}%"


def _annotation_section(ranked: list[RankedCandidate],
                        annotations: Mapping[str, ScreenAnnotation]) -> list[str]:
    """The annotations on this run's names, in queue order — every annotated name in the queue,
    including one below the table's cut, so a reader never meets a warning that is not shown."""
    named = [(r, annotations[r.ticker]) for r in ranked if r.ticker in annotations]
    if not named:
        return []
    out = ["", "## Annotations on this screen run", "",
           "_Added after the run, by operator ruling. The results above stand as the run "
           "produced them; ⚠ marks an annotated name._", ""]
    for r, a in named:
        out.append(f"- **{r.ticker}** (rank {r.rank}) — annotated {a.annotated_on}. {a.finding}")
        for g in a.gates:
            out.append(
                f"  - {g.gate} {g.label} (passes at ≤ {_pct(g.threshold)}): as committed "
                f"{_pct(g.as_committed.value)} {'PASS' if g.as_committed.passes else 'FAIL'} · "
                f"on the corrected data {_pct(g.repaired.value)} "
                f"{'PASS' if g.repaired.passes else 'FAIL'}")
        out.append(f"  - Measured: {a.measured} Record: `{a.record}`")
    return out


def render_queue_markdown(ranked: list[RankedCandidate], *, top: int | None = None,
                          annotations: Mapping[str, ScreenAnnotation] | None = None) -> str:
    """A deterministic, committed Markdown view of the queue (a compact per-name table).

    ``annotations`` (ticker → annotation on THIS run, `vinci.screens.annotations`) marks a name ⚠
    and lists the annotation after the table. Without one the output is unchanged, byte for byte."""
    notes = annotations or {}
    rows = ranked if top is None else ranked[:top]
    intro = (
        "> Orders the screen's Edge-2 candidates by face-valid structural promise so scarce human "
        "deep-analysis time goes to the most-promising overshoots first. **Orders, never "
        "decides**; tuned by face-validity, never forward returns."
    )
    header = (
        "| # | ticker | score | band | idiosyncrasy | depth | character | multiple | "
        "liquidity |"
    )
    out = [
        "# Ranked candidate queue — structural priority profiles",
        "",
        intro,
        "",
        header,
        "|--:|:--|--:|:-:|:--|:--|:--|:--|:--|",
    ]
    for r in rows:
        flag = " ⟂" if r.tradeability_gated else ""
        out.append(
            f"| {r.rank} | {r.ticker}{' ⚠' if r.ticker in notes else ''} | "
            f"{r.priority_score:.3f} | {r.depth_band} | "
            f"{_md_cell(r, 'idiosyncrasy')} | {_md_cell(r, 'depth')} | "
            f"{_md_cell(r, 'character')} | {_md_cell(r, 'multiple')} | "
            f"{r.liquidity_tier.value}{flag} |"
        )
    out += _annotation_section(ranked, notes)
    return "\n".join(out) + "\n"
