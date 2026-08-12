"""Contract A — the **name data-record** the gates consume (per ``INGESTION_LAYER.md`` §A).

Identity fields are plain typed values: they are the *join key*, the resolver's responsibility,
and are guaranteed correct or the resolver fails loud — they are not uncertain "data". Every
*measured/pulled* value (prices, fundamentals, events, market cap) is wrapped in a
:class:`~vinci.schemas.envelope.DataField` so its coverage is explicit.

Loop 1 is US-only, so ``overall_coverage_tier`` is always ``US-full`` and the stress signals
(IBKR options/short-interest, shortlist-only) are left UNKNOWN — wired for extension, not
populated yet.
"""

from __future__ import annotations

import enum
from datetime import date

from pydantic import BaseModel, Field

from vinci.schemas.envelope import DataField, SourceTier


class Identity(BaseModel, frozen=True):
    """The stable join key across EOD / EDGAR / (later) IBKR. Resolver output."""

    internal_id: str  # stable security-level id, e.g. "SEC-0000320193-AAPL"
    issuer_id: str  # stable issuer-level id, e.g. "ISS-0000320193"
    cik: str  # 10-digit zero-padded SEC CIK
    ticker: str
    mic: str  # ISO 10383 market identifier code, e.g. XNAS
    exchange: str  # human-readable, e.g. "Nasdaq"
    eod_symbol: str  # symbol as the EOD source (Polygon) knows it
    name: str
    share_class: str | None = None  # e.g. "A"/"B" for dual-class issuers
    sic: str | None = None  # SEC SIC — operating-co universe gate (not G2)
    sic_description: str | None = None
    country: str = "US"
    currency: str = "USD"


class PriceFeatures(BaseModel, frozen=True):
    """EOD-derived price features (source: EOD; cross-checked at depth). Screen-2 G1/G2 inputs."""

    last: DataField[float]
    high_52w: DataField[float]
    low_52w: DataField[float]
    drawdown_from_high: DataField[float]  # negative fraction, e.g. -0.42 == -42% (G1)
    dist_from_low: DataField[float]  # fraction above the 52w low
    ret_3m: DataField[float]
    ret_6m: DataField[float]
    ret_12m: DataField[float]
    rel_ret_vs_market: DataField[float]  # name return minus IWM return over the decline window (G2)
    adv_90d_shares: DataField[float]
    adv_90d_usd: DataField[float]
    turnover: DataField[float]  # adv_90d_usd / market_cap
    volume_spike: DataField[float]  # latest volume / 90d average
    # ~13 WEEKLY means (5 sessions each), oldest→newest, each a ratio to the SAME 90d average
    # volume_spike uses — so the trend and the number share a unit and the last point is the most
    # recent week. DISPLAY-ONLY: volume_spike stays the scorer's input; this is what lets a human
    # see DIRECTION, which a one-session ratio structurally cannot show. Bucketed weekly because at
    # sparkline width a daily series of a small-cap is spike noise and direction is the point.
    # Defaulted: a snapshot written before 2026-08-12 carries no series and must still parse.
    volume_trend: DataField[list[float]] | None = None


class Fundamentals(BaseModel, frozen=True):
    """EDGAR XBRL fundamentals (US: present / non-US: unknown). Screen-2 G3 + non-distress."""

    ev_ebitda: DataField[float]
    ev_ebitda_pctile_vs_history: DataField[float]  # 0..1 within trailing range (G3)
    pe: DataField[float]
    pe_pctile_vs_history: DataField[float]
    fcf_sign: DataField[int]  # -1 / 0 / +1 (trailing FCF sign)
    op_income_sign: DataField[int]
    net_leverage: DataField[float]  # net debt / EBITDA
    # OCF-basis leverage, carried alongside net_leverage. Defaulted so snapshots written before this
    # field (committed candidate_records.jsonl) still load — they read UNKNOWN until a re-screen.
    net_debt_to_ocf: DataField[float] = DataField.unknown(
        source="EDGAR", tier=SourceTier.EDGAR, note="not in snapshot (pre-OCF-leverage screen)"
    )
    # Net share issuance over the trailing ~2y, as a fraction (+0.42 == shares up 42%; negative ==
    # buyback). INFORM-ONLY — an evidence-strip input the human reads, never a rank input, and an
    # AST fence asserts the scorer never touches it. Computed from the SAME companyfacts the
    # screen already fetches (no extra network) via the one shared `share_count_change`, so the
    # displayed number and the dilution-spiral demote can never be two different quantities.
    # Its `note` carries the endpoints, so "+42%" is checkable against EDGAR rather than trusted.
    # Defaulted so a snapshot written before 2026-08-12 still loads (reads UNKNOWN until re-screen).
    share_count_change_730d: DataField[float] = DataField.unknown(
        source="EDGAR", tier=SourceTier.EDGAR, note="not in snapshot (pre-evidence-strip screen)"
    )


class StressSignals(BaseModel, frozen=True):
    """Attached stress signals — never a gate, shortlist-only (IBKR). Deferred in Loop 1."""

    iv_pctile: DataField[float]
    short_interest: DataField[float]


class EventType(enum.StrEnum):
    """News/filing **events** are pointers for depth — typed only, never a count or score
    (the fence from ``FUNNEL_SCREENS.md`` principle 5)."""

    DOWNGRADE = "downgrade"
    GUIDANCE_CUT = "guidance_cut"
    CONTRACT = "contract"
    THREAT = "threat"
    EARNINGS_GAP_DOWN = "earnings_gap_down"


class TypedEvent(BaseModel, frozen=True):
    """A single typed event with its date and provenance. No intensity/score (fenced)."""

    event_type: EventType
    event_date: date
    source: str  # e.g. "EDGAR 8-K acc 0000320193-24-000123" or "EOD gap-down"
    detail: str | None = None
    accession: str | None = None  # SEC accession number where applicable


class CoverageTier(enum.StrEnum):
    US_FULL = "US-full"
    NON_US_THIN = "non-US-thin"


class DataRecord(BaseModel, frozen=True):
    """The full name data-record (contract A). The reusable foundation the screens sit on."""

    identity: Identity
    market_cap: DataField[float]
    prices: PriceFeatures
    fundamentals: Fundamentals
    stress: StressSignals
    events: list[TypedEvent] = Field(default_factory=list)
    overall_coverage_tier: CoverageTier = CoverageTier.US_FULL
    # When this record was assembled (point-in-time stamp for the whole record).
    as_of: date | None = None
