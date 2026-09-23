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


def _env_float(name: str, default: float) -> float:
    """A positive float from the environment, or ``default`` when unset — never a silent fallback.

    A pacing override that is unreadable must FAIL rather than quietly restore the default: the
    symptom of the wrong pace is a run that dies twenty minutes in on somebody else's rate limit,
    which is exactly the failure an operator would be trying to fix by setting this.
    """
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name}={raw!r} is not a number — set it to a positive rate or "
                           f"unset it to use the default ({default})") from exc
    if value <= 0:
        raise RuntimeError(f"{name}={raw!r} must be positive — a rate of zero or less would "
                           f"either stall every request or disable pacing entirely")
    return value


class PacingConfig(BaseModel, frozen=True):
    """External-API politeness/pacing. Verified live: SEC fair-access ~10 req/s; Polygon free
    tier ~5 req/min (re-measured 2026-09-23). Conservative defaults to stay well within limits."""

    sec_requests_per_sec: float = 8.0
    # efts (full-text search) is a separate, more rate-sensitive service than data.sec.gov;
    # pace it conservatively (it throttles to an error response, not a 429, under load).
    efts_requests_per_sec: float = 1.0
    # MEASURED, NOT ASSUMED (2026-09-23). This read 100.0 with a comment saying "Polygon Starter
    # lifts the free-tier 5/min cap" — the account does not serve that. A live probe of ten
    # `/v3/reference/tickers/<T>` calls at ~2s spacing returned 200 six times and then 429 on every
    # call after: a ~5/min ceiling. Pacing 20x above what the plan serves is what made the weekly
    # screen unrunnable — the client burst, the 429s exhausted `max_retries` (backoff tops out
    # around 31s, short of the 60s window), and the run died, locally and in CI.
    # 4.0 leaves headroom under a 5/min rolling window rather than sitting exactly on it.
    # Override with `POLYGON_REQUESTS_PER_MIN` when the plan changes; it is read per config build,
    # so no code edit is needed to go back up.
    polygon_requests_per_min: float = Field(default_factory=lambda: _env_float(
        "POLYGON_REQUESTS_PER_MIN", 4.0))
    # FINRA's public query API (api.finra.org, delayed data) publishes no hard limit; pace it
    # politely — the twice-monthly short-interest file is fetched once per name and cached.
    finra_requests_per_sec: float = 4.0
    http_timeout_sec: float = 30.0
    max_retries: int = 4


class Config(BaseModel, frozen=True):
    """Top-level config. Paths derive from ``data_dir``; everything is overridable."""

    data_dir: Path = Field(default=Path("data"))
    universe: UniverseConfig = UniverseConfig()
    # --- THE PARALLEL THEME BAND (operator ruling 2026-08-31) ---------------------------------
    # A SECOND, larger band read ONLY at the THEME altitude (exposure scans / theme research).
    # WHY PARALLEL RATHER THAN WIDENING `universe`: the primary band IS the forward-validation
    # population — screens, ranker and the BUY-AVOID spread have been accumulating against that
    # membership since the clock started, so widening it mid-flight changes the experiment's
    # population mid-experiment. A parallel band adds reach without touching the record: it lands
    # in its own snapshot (`theme_universe_snapshot`), and NOTHING downstream of the theme scan
    # reads it (pinned — a theme-band-only name reaching the screen fails the suite).
    # SCANNABLE IS NOT TRADEABLE: a megacap surfaced by a theme scan still enters the book only
    # through the existing dossier/underwrite path, where the MC1-MC4 / FPI1-FPI5 readiness gates
    # bind per name (docs/records/2026-08-21-tiered-gates-*).
    # The ceiling is a stated number rather than "infinity" so an out-of-band drop is still LOGGED
    # with its reason: it sits above the largest listed company, and a name exceeding it should
    # re-open this knob, not vanish. Face-validity, never tuned on forward returns.
    theme_universe: UniverseConfig = UniverseConfig(
        market_cap_min_usd=10_000_000_000.0, market_cap_max_usd=1.0e13)
    # BUILT PER CONFIG, NOT ONCE AT IMPORT. A bare `PacingConfig()` default is evaluated
    # when this class is defined, so an env-driven pace would be frozen to whatever the
    # environment held at import time — and a pace set after that (a CLI that loads `.env`
    # on entry, a test) would be silently ignored.
    pacing: PacingConfig = Field(default_factory=PacingConfig)
    # A datum older than this many calendar days flips coverage_status -> STALE.
    price_staleness_days: int = 5
    # LLM for graph extraction + dossier synthesis + the theme exposure classifier.
    #
    # REVERTED TO OPUS 4.8 BY OPERATOR RULING 2026-09-01, reversing the 2026-08-29 bump to Opus 5.
    # The 2026-08-29 ruling accepted a stated risk — the 4.8-era groundedness benchmark was not
    # re-run — with the falsifier "untraceable figures or mis-cites in fresh extractions". THAT
    # FALSIFIER WATCHED THE WRONG FAILURE MODE. What broke was not bad content but ABSENT content:
    # Opus 5 returns a tool_use block MISSING REQUIRED FIELDS, so `synthesize()` refuses and the
    # assembly hard-stops. No groundedness check could have seen it — there is nothing to ground.
    #
    # MEASURED before reverting (real API calls, prompts built exactly as `synthesize()` builds
    # them, max_tokens=16384 throughout): TECX 5 FAIL / 4 PASS on Opus 5 and 2 PASS / 0 FAIL on
    # 4.8; SMPL (overshoot, full financials — nothing like TECX) 2 FAIL / 1 PASS on Opus 5; V
    # 4 PASS / 0 FAIL. Fleet-wide and stochastic, not a property of one name or sleeve.
    # NOT truncation: stop_reason is `tool_use`, never `max_tokens`, and the FAILING calls burn
    # MORE output tokens (8.7-10.1k) than the passing ones (3.9-6.6k) while returning fewer fields.
    # All 18 committed syntheses were produced by 4.8; none by Opus 5 — the bump was never
    # exercised on the synthesis path, which is why this sat undetected for three days.
    #
    # Record: docs/records/2026-09-01-opus5-synthesis-regression.md. Re-raising this knob requires
    # measuring a PASS RATE over >=5 runs on >=3 names (include SMPL and TECX), not one green run.
    graph_llm_model: str = "claude-opus-4-8"
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
