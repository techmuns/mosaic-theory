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

from dotenv import load_dotenv
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
    # Operating-companies-only gate — TWO independent structural axes, both fail-CLOSED on a missing
    # value (exclude what we cannot confirm; never silently admit).
    #
    # Axis 1 — issuer BUSINESS type (EDGAR SIC). An ETF/ETP/closed-end fund/blank-check is a basket
    # or shell, not a de-rated business. entityType and 10-K-on-file do NOT separate them (a
    # commodity ETP files a 10-K and is "operating"); the SIC code does. A BLANK SIC is excluded
    # (how a BDC slips a denylist). Excluded codes: 6189 asset-backed, 6221 commodity ETPs, 6722
    # open-end funds, 6726 investment offices, 6770 blank-check/SPAC.
    excluded_sic_codes: tuple[str, ...] = ("6189", "6221", "6722", "6726", "6770")
    # Axis 2 — security INSTRUMENT type (Polygon). An ALLOWLIST of operating-company common equity:
    # CS = domestic common, ADRC = ADR common, OS = foreign ordinary, GDR = global depositary
    # receipt. Everything else (ETN/ETF/ETV/ETS/FUND/SP/PFD/RIGHT/WARRANT/UNIT) and a blank/unknown
    # type is excluded — this catches an ETN spliced onto its bank issuer's fundamentals (SHNY=ETS
    # → Bank of Montreal: ticker→CIK is correct, just not equity). An allowlist, not a denylist: a
    # new structured-product type defaults to excluded, not admitted.
    allowed_security_types: tuple[str, ...] = ("CS", "ADRC", "OS", "GDR")
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
    # FINRA's public query API (api.finra.org, delayed data) publishes no hard limit; pace it
    # politely — the twice-monthly short-interest file is fetched once per name and cached.
    finra_requests_per_sec: float = 4.0
    http_timeout_sec: float = 30.0
    max_retries: int = 4


class Config(BaseModel, frozen=True):
    """Top-level config. Paths derive from ``data_dir``; everything is overridable."""

    data_dir: Path = Field(default=Path("data"))
    universe: UniverseConfig = UniverseConfig()
    pacing: PacingConfig = PacingConfig()
    # A datum older than this many calendar days flips coverage_status -> STALE.
    price_staleness_days: int = 5
    # LLM for graph extraction + dossier synthesis + the theme exposure classifier. Bumped to
    # Opus 5 by OPERATOR RULING 2026-08-29 (the strongest-available-model policy that picked
    # Opus 4.8 in the first place, applied to the new generation). The 4.8-era groundedness
    # benchmark (vs Sonnet 4.6: ~1/3 the untraceable figures, 0 mis-cites, ~3.5x more stable —
    # see STATE.md) has NOT been re-run on Opus 5 — accepted with its falsifier in the record:
    # untraceable figures or mis-cites appearing in fresh extractions are the signal to re-run
    # graph Test 0 on a sample and, if it degrades, flip this knob back. Swappable, not a router.
    graph_llm_model: str = "claude-opus-5"
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
        return self.data_dir / "vinci.db"

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.cache_dir, self.snapshots_dir):
            d.mkdir(parents=True, exist_ok=True)


def get_config() -> Config:
    """Return the active config. (Override hook for tests / future env-driven config.)"""
    return Config()


def load_local_env(env_path: Path | None = None) -> None:
    """Populate ``os.environ`` from the repo-root ``.env`` — the ONE shared secret-loading path,
    so every contributor on every laptop runs identically (12-factor config).

    - **Local:** reads the git-ignored ``.env`` at the repo root (seed it once with
      ``cp .env.example .env``). New required key → add it to the committed ``.env.example`` so
      every laptop sees it on the next ``git pull``.
    - **CI / GitHub Actions:** ``.env`` is git-ignored so none exists on the runner — this is a
      no-op and the workflow's injected secrets are used. ``load_dotenv`` defaults to
      ``override=False``, so an already-set var ALWAYS wins: a real CI secret is never clobbered.

    Called once from the CLI entrypoint; importing the package as a library does NOT auto-load,
    keeping tests hermetic.
    """
    path = env_path or (Path(__file__).resolve().parent.parent / ".env")
    load_dotenv(path)  # override=False (default) → injected CI secrets win over any file


def sec_user_agent() -> str:
    """SEC fair-access requires a declared User-Agent with a contact. Overridable via env."""
    return os.environ.get("SEC_USER_AGENT", "vinci-research tech@muns.io")


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
