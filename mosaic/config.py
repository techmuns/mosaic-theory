"""Configuration for the Loop 1 slice — the US universe definition, filesystem paths,
and external-API pacing/identity.

First principles
----------------
- **US-only.** EDGAR is the only free programmatic *fundamental* feed, so every gate evaluates.
- **One cap band.** A face-validity config knob (small/mid), *never* tuned on forward returns.
- **Secrets live in the environment**, never in this file or in serialized config
  (``POLYGON_API_KEY``, ``ANTHROPIC_API_KEY``, optionally ``SEC_USER_AGENT``).

Universe and threshold values here are *starting points calibrated by face-validity*, per
``FUNNEL_SCREENS.md`` — they are deliberately coarse and must not be optimised against P&L.
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

# --- Exchanges --------------------------------------------------------------------------------
# SEC ``company_tickers_exchange.json`` uses these human-readable exchange names. We keep the
# major US listing venues and exclude OTC (illiquid, thin disclosure). MIC mapping is for the
# entity master's ``ticker+MIC`` identity field.
US_EXCHANGES: dict[str, str] = {
    "Nasdaq": "XNAS",
    "NYSE": "XNYS",
    "NYSE American": "XASE",
}


class UniverseConfig(BaseModel, frozen=True):
    """The US universe gate (capacity gate). Coarse by design."""

    exchanges: tuple[str, ...] = tuple(US_EXCHANGES)
    # Small/mid-cap band in USD. Defaults are face-validity starting points (revisit by
    # eyeballing the resulting universe, never by forward returns).
    market_cap_min_usd: float = 300_000_000.0
    market_cap_max_usd: float = 10_000_000_000.0
    # Tradeability gate: minimum 90-day average daily $-volume. An unbuyable/unexitable micro-cap
    # fails tradeability before the de-rating question is even asked — a property of the name, not a
    # screen judgment. Excludes the illiquid failed-SPAC/zombie junk the cap band alone passes.
    adv_floor_usd: float = 3_000_000.0
    # Operating-companies-only gate: an ETF/ETP/closed-end fund/blank-check is a basket or shell,
    # not a de-rated business — outside the universe by definition. entityType and 10-K-on-file do
    # NOT separate them (a commodity ETP files a 10-K and is "operating"); the SIC code does.
    # Excluded: 6189 asset-backed, 6221 commodity ETPs, 6722 open-end funds, 6726 investment
    # offices, 6770 blank-check/SPAC.
    excluded_sic_codes: tuple[str, ...] = ("6189", "6221", "6722", "6726", "6770")
    country: str = "US"
    currency: str = "USD"
    # Optional cap on universe size for the thin Loop 1 slice (None = no cap).
    max_names: int | None = None


class PacingConfig(BaseModel, frozen=True):
    """External-API politeness/pacing. Verified live: SEC fair-access ~10 req/s; Polygon free
    tier ~5 req/min. Conservative defaults to stay well within limits."""

    sec_requests_per_sec: float = 8.0
    # efts (full-text search) is a separate, more rate-sensitive service than data.sec.gov;
    # pace it conservatively (it throttles to an error response, not a 429, under load).
    efts_requests_per_sec: float = 1.0
    # Polygon Starter lifts the free-tier 5/min cap and gives 5y history; this is latency-bound
    # (~1s/call) anyway, so the throttle rarely engages. (Free tier was 5.0.)
    polygon_requests_per_min: float = 100.0
    http_timeout_sec: float = 30.0
    max_retries: int = 4


class Config(BaseModel, frozen=True):
    """Top-level config. Paths derive from ``data_dir``; everything is overridable."""

    data_dir: Path = Field(default=Path("data"))
    universe: UniverseConfig = UniverseConfig()
    pacing: PacingConfig = PacingConfig()
    # A datum older than this many calendar days flips coverage_status -> STALE.
    price_staleness_days: int = 5
    # Graph-track LLM (who-names-whom extraction). Accuracy gates the moat hypothesis, so this is a
    # strong model, not the cheapest — a swappable knob (Opus is the diagnostic fallback).
    graph_llm_model: str = "claude-sonnet-4-6"
    # A focal naming this many or more distinct hubs is a "super-connector" (e.g. an IT integrator
    # like Kyndryl that names every hyperscaler, or a packager that lists all its customers). Such a
    # name enumerates a LIST, not a few concentrated dependencies, and manufactures spurious shared-
    # node degree. Excluded from the shared-node count (a node needs 2+ NON-super-connector focals).
    # Default 6: band-A data showed a clean gap — normal names ≤5 hubs, list-enumerators ≥13. A
    # multi-sourced sector (semis naming many foundries) may warrant a higher value; overridable.
    graph_super_connector_degree: int = 6
    # Fail-loud floor: a real US trading day returns ~10-12k grouped-daily rows. A non-trading day
    # returns 0 (legitimate). A status=OK response with 0 < rows < this floor signals a partial/
    # degraded refresh and must RAISE rather than silently write a half day.
    grouped_daily_min_results: int = 3000

    # --- derived paths (kept out of the model so they don't serialize) ---
    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def snapshots_dir(self) -> Path:
        """Durable, append-only JSON/CSV provenance committed to the repo (NOT the binary DB)."""
        return self.data_dir / "snapshots"

    @property
    def db_path(self) -> Path:
        """Local working store — rebuildable from snapshots; never committed."""
        return self.data_dir / "mosaic.db"

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.cache_dir, self.snapshots_dir):
            d.mkdir(parents=True, exist_ok=True)


def get_config() -> Config:
    """Return the active config. (Override hook for tests / future env-driven config.)"""
    return Config()


def sec_user_agent() -> str:
    """SEC fair-access requires a declared User-Agent with a contact. Overridable via env."""
    return os.environ.get("SEC_USER_AGENT", "mosaic-research tech@muns.io")


def require_env(name: str) -> str:
    """Fetch a required secret from the environment, failing loud if absent.

    Used for ``POLYGON_API_KEY`` / ``ANTHROPIC_API_KEY``. We fail loud rather than degrade so a
    misconfigured run never silently produces partial data.
    """
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Required environment variable {name!r} is not set. "
            "Set it locally or as a GitHub Actions secret."
        )
    return value
