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
    polygon_requests_per_min: float = 5.0
    http_timeout_sec: float = 30.0
    max_retries: int = 4


class Config(BaseModel, frozen=True):
    """Top-level config. Paths derive from ``data_dir``; everything is overridable."""

    data_dir: Path = Field(default=Path("data"))
    universe: UniverseConfig = UniverseConfig()
    pacing: PacingConfig = PacingConfig()
    # A datum older than this many calendar days flips coverage_status -> STALE.
    price_staleness_days: int = 5

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
