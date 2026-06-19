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
BUY−AVOID spread: it imports nothing from ``mosaic.scoring`` / ``mosaic.ledger``, and the ranker is
handed a *screen-time* candidate only. Tuning weights against P&L is the backtest trap the whole
project rejects. Keep this layer legible, not clever — reliability comes from being readable
top-to-bottom, every position defensible.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from pydantic import BaseModel, model_validator

from mosaic.rank.profile import (
    AxisCoverage,
    AxisScore,
    CauseClass,
    LiquidityTier,
    RankedCandidate,
)
from mosaic.schemas.candidate import CandidateRecord
from mosaic.schemas.data_record import DataRecord, EventType, Fundamentals, PriceFeatures

# --- Tier-1 axis calibration (face-validity constants; see the module docstring on tuning) ----
# Map the admitted drawdown band [−30% gate, −85% terminal floor] onto [0, 1]: deeper ranks higher
# (a deeper, sharper fall is a likelier overreaction). The screen already excludes < −85% (terminal
# by magnitude) and > −30% (too shallow), so this maps the *admitted* range.
_DD_GATE = 0.30
_DD_FLOOR = 0.85
# Idiosyncrasy anchor: a name underperforming its sector by this much over the decline window earns
# full credit. Idiosyncratic dislocation is where mispricing lives — THE most on-thesis axis.
_IDIO_FULL = 0.60
# Multiple-at-floor: G3 admits only a current multiple in the bottom ``_MULT_FLOOR_PCTILE`` of a
# name's OWN ~5y range; we map [0, floor] → [1, 0] so the cheapest-vs-its-own-history names earn the
# most credit. (UNKNOWN — negative earnings / absent XBRL — is handled by the fail-loud path below.)
_MULT_FLOOR_PCTILE = 0.25
# FAIL-LOUD: an UNKNOWN Tier-1 quality axis earns NO credit and is flagged as a depth task — never
# imputed. A name must rank on what we can CONFIRM; missing data ranks lower, explicitly.
_UNKNOWN_AXIS_SCORE = 0.0

# Shape (sharp discrete fall vs slow grind), read from the EOD gap-down detector. A single clean
# discrete drop is the archetype overshoot (one bad print, possibly overreacted); repeated gaps are
# messier — more often the market re-rating on accumulating bad news — so the score eases off, never
# rewarding "more violent" as "more promising". 0 gaps == a known grind, not missing data.
_SHAPE_BY_GAPS: dict[int, float] = {0: 0.0, 1: 1.0, 2: 0.90, 3: 0.80}
_SHAPE_MANY_GAPS = 0.70  # 4+ gap-downs

# Cause (discrete identifiable catalyst vs unexplained slow bleed). NB: today this SHARES the
# gap-down detector with shape (the only event source wired is EOD gap-downs); their combined weight
# is held modest below so one EOD signal can't dominate. They diverge once 8-K/guidance *text*
# events and the Tier-3 LLM annotation populate cause independently of price geometry.
_CAUSE_BLEED = 0.30  # no discrete catalyst — "more often real deterioration" → ranks lower
_CAUSE_DISCRETE_BASE = 0.80  # an identifiable discrete de-rating event → ranks higher
_CAUSE_STRUCTURAL_BREAK = 0.05  # Tier-3 LLM: terminal-looking (lost customer / reg kill / fraud)
_CAUSE_MEAN_REVERT = 0.97  # Tier-3 LLM: confirmed mean-revert candidate
_DECLINE_WINDOW_DAYS = 180  # the screen's gap-down detection window (for catalyst recency)

# Tier-2 volume overlay (MINOR). The only bar readable from a screen-time record is current volume
# vs its 90d average: low == panic exhausted (a clean-setup plus); high == still under active
# distribution (a falling-knife caution). This is NOT a smart-money-accumulation signal — that flow
# is private/microsecond and we are structurally late; public volume is coincident-to-lagging and
# strip-mined. Bounded small on purpose: it sharpens the ranking, it is not a pillar.
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


class RankWeights(BaseModel, frozen=True):
    """Face-validity weights over the Tier-1 structural axes. Sum to 1.0 (a clean 0..1 composite).

    Set by eyeballing the queue-top, NEVER by forward returns (see the module docstring). Their
    *ordering of magnitude* encodes the thesis, not an optimisation:
      - **idiosyncrasy** is THE most on-thesis axis (idiosyncratic dislocation = where mispricing
        lives; sector beta is not) → the largest weight.
      - **depth** is the screen's defining, fully-covered signal → second.
      - **multiple-at-floor** (cheap vs its OWN history) → third.
      - **cause** and **shape** share the gap-down detector today, so their COMBINED weight is held
        modest — one EOD signal must not dominate.
    """

    idiosyncrasy: float = 0.30
    depth: float = 0.25
    multiple: float = 0.20
    cause: float = 0.15
    shape: float = 0.10

    @model_validator(mode="after")
    def _sum_to_one(self) -> RankWeights:
        total = self.idiosyncrasy + self.depth + self.multiple + self.cause + self.shape
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"Tier-1 weights must sum to 1.0 (got {total})")
        return self

    def as_map(self) -> dict[str, float]:
        return {
            "idiosyncrasy": self.idiosyncrasy,
            "depth": self.depth,
            "multiple": self.multiple,
            "cause": self.cause,
            "shape": self.shape,
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


def shape_axis(rec: DataRecord) -> AxisScore:
    """Drawdown shape: sharp discrete fall (gap-down) vs slow grind (none). Always evaluable."""
    gaps = _gap_down_dates(rec)
    n = len(gaps)
    if n == 0:
        return AxisScore(
            axis="shape", score=0.0, coverage=AxisCoverage.PRESENT,
            label="grind — no discrete gap-down", raw=0.0,
        )
    score = _SHAPE_BY_GAPS.get(n, _SHAPE_MANY_GAPS)
    s = "" if n == 1 else "s"
    return AxisScore(
        axis="shape", score=score, coverage=AxisCoverage.PRESENT,
        label=f"sharp — {n} gap-down{s}", raw=float(n),
    )


def idiosyncrasy_axis(prices: PriceFeatures) -> AxisScore:
    """Idiosyncrasy: how much of the fall is the name vs its sector (G2). Name-specific → higher."""
    f = prices.rel_ret_vs_sector
    if not f.is_evaluable or f.value is None:
        return AxisScore(
            axis="idiosyncrasy", score=None, coverage=AxisCoverage.UNKNOWN,
            label="UNKNOWN — no clean sector benchmark",
        )
    rel = f.value  # negative == underperformed its sector
    score = _clip01(-rel / _IDIO_FULL)
    return AxisScore(
        axis="idiosyncrasy", score=score, coverage=AxisCoverage.PRESENT,
        label=f"{rel:+.0%} vs sector", raw=rel,
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


def cause_axis(rec: DataRecord, cause_class: CauseClass) -> AxisScore:
    """De-rating cause: discrete identifiable catalyst vs unexplained bleed, COLOURED by the Tier-3
    LLM flag. Discrete + recent → higher; a structural-break flag demotes; absent flag → as-is."""
    gaps = _gap_down_dates(rec)
    ref = rec.as_of
    if not gaps:
        base = _CAUSE_BLEED
        label = "slow bleed — no discrete catalyst"
    else:
        recent = gaps[-1]
        recency = 1.0
        age_txt = ""
        if ref is not None:
            age = (ref - recent).days
            recency = _clip01(1.0 - age / _DECLINE_WINDOW_DAYS)
            age_txt = f" ({age}d ago)"
        base = _CAUSE_DISCRETE_BASE + (1.0 - _CAUSE_DISCRETE_BASE) * recency
        label = f"discrete — gap-down {recent.isoformat()}{age_txt}"

    # Tier-3 LLM annotation COLOURS the cause; it never sets the primary sort key.
    if cause_class is CauseClass.STRUCTURAL_BREAK:
        return AxisScore(
            axis="cause", score=_CAUSE_STRUCTURAL_BREAK, coverage=AxisCoverage.PRESENT,
            label=f"{label} · LLM: structural-break (demoted)", raw=base,
        )
    if cause_class is CauseClass.MEAN_REVERT:
        return AxisScore(
            axis="cause", score=max(base, _CAUSE_MEAN_REVERT), coverage=AxisCoverage.PRESENT,
            label=f"{label} · LLM: mean-revert", raw=base,
        )
    return AxisScore(
        axis="cause", score=base, coverage=AxisCoverage.PRESENT,
        label=f"{label} · LLM: —", raw=base,
    )


# --- Tier-2 volume overlay + tradeability -----------------------------------------------------
def volume_overlay(prices: PriceFeatures) -> tuple[float, str]:
    """A MINOR ± adjustment from current volume vs its 90d average (panic exhausted vs heavy)."""
    f = prices.volume_spike
    if not f.is_evaluable or f.value is None:
        return 0.0, "UNKNOWN"
    vs = f.value
    if vs <= _VOL_EXHAUSTED:
        return _VOL_BONUS, f"exhausted ({vs:.2f}×)"
    if vs <= _VOL_ELEVATED:
        return 0.0, f"normal ({vs:.2f}×)"
    if vs <= _VOL_HEAVY:
        return _VOL_CAUTION_SMALL, f"elevated ({vs:.2f}×)"
    return _VOL_CAUTION, f"heavy distribution ({vs:.1f}×)"


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
        "multiple": multiple_axis(rec.fundamentals),
        "cause": cause_axis(rec, cause_class),
        "shape": shape_axis(rec),
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

    adv_f = prices.adv_90d_usd
    adv_usd = adv_f.value if (adv_f.is_evaluable and adv_f.value is not None) else 0.0
    gated = adv_usd < deep_work_adv_floor

    score = _clip01(quality + vol_adj)
    if gated:
        score *= _GATED_SCORE_MULT

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
        cause_class=cause_class,
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
    deep_work_adv_floor: float = _DEEP_WORK_ADV_FLOOR,
) -> list[RankedCandidate]:
    """Rank the whole candidate set into the priority queue (deterministic order, 1-based ``rank``).

    Sort: tradeable names first (the gate), then priority-score desc, then — for a stable, legible
    tie-break — deeper drawdown, then more-idiosyncratic, then ticker.
    """
    ann = annotations or {}
    caps = market_caps or {}
    ranked: list[RankedCandidate] = []
    for c in cands:
        iid = c.data_record.identity.internal_id
        tk = c.data_record.identity.ticker
        cc = ann.get(iid) or ann.get(tk) or CauseClass.UNCLASSIFIED
        ranked.append(
            rank_candidate(
                c, weights=weights, cause_class=cc,
                market_cap=caps.get(iid), deep_work_adv_floor=deep_work_adv_floor,
            )
        )

    def sort_key(r: RankedCandidate) -> tuple[bool, float, float, float, str]:
        dd = r.axes["depth"].raw if r.axes["depth"].raw is not None else 0.0
        idio = r.axes["idiosyncrasy"].raw if r.axes["idiosyncrasy"].raw is not None else 0.0
        # gated last; score desc; deeper (more negative dd) first; more idiosyncratic first; ticker.
        return (r.tradeability_gated, -r.priority_score, dd, idio, r.ticker)

    ranked.sort(key=sort_key)
    return [r.model_copy(update={"rank": i + 1}) for i, r in enumerate(ranked)]


def _profile_line(ticker: str, score: float, band: str, axes: dict[str, AxisScore]) -> str:
    def lab(name: str) -> str:
        return axes[name].label
    return (
        f"{ticker:<6} {score:.3f} [{band}]  "
        f"idio: {lab('idiosyncrasy')} | depth: {lab('depth')} | "
        f"mult: {lab('multiple')} | cause: {lab('cause')} | shape: {lab('shape')}"
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
    order = ["idiosyncrasy", "depth", "multiple", "cause", "shape"]
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


def render_queue_markdown(ranked: list[RankedCandidate], *, top: int | None = None) -> str:
    """A deterministic, committed Markdown view of the queue (a compact per-name table)."""
    rows = ranked if top is None else ranked[:top]
    intro = (
        "> Orders the screen's Edge-2 candidates by face-valid structural promise so scarce human "
        "deep-analysis time goes to the most-promising overshoots first. **Orders, never "
        "decides**; tuned by face-validity, never forward returns."
    )
    header = (
        "| # | ticker | score | band | idiosyncrasy | depth | multiple | cause | shape | "
        "liquidity |"
    )
    out = [
        "# Ranked candidate queue — structural priority profiles",
        "",
        intro,
        "",
        header,
        "|--:|:--|--:|:-:|:--|:--|:--|:--|:--|:--|",
    ]
    for r in rows:
        flag = " ⟂" if r.tradeability_gated else ""
        out.append(
            f"| {r.rank} | {r.ticker} | {r.priority_score:.3f} | {r.depth_band} | "
            f"{_md_cell(r, 'idiosyncrasy')} | {_md_cell(r, 'depth')} | {_md_cell(r, 'multiple')} | "
            f"{_md_cell(r, 'cause')} | {_md_cell(r, 'shape')} | {r.liquidity_tier.value}{flag} |"
        )
    return "\n".join(out) + "\n"
