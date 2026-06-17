"""Shared SEC HTTP factory — one polite, cached client config for all SEC consumers
(the resolver and the EDGAR client), so pacing and caching are identical and the on-disk
cache is shared (keyed by URL)."""

from __future__ import annotations

from mosaic.config import Config, get_config, sec_user_agent
from mosaic.netcache import CachedHttp


def build_sec_http(config: Config | None = None) -> CachedHttp:
    """Client for data.sec.gov / www.sec.gov (companyfacts, submissions, reference files)."""
    cfg = config or get_config()
    cfg.ensure_dirs()
    return CachedHttp(
        cache_dir=cfg.cache_dir,
        user_agent=sec_user_agent(),
        min_interval_sec=1.0 / cfg.pacing.sec_requests_per_sec,
        max_retries=cfg.pacing.max_retries,
        timeout_sec=cfg.pacing.http_timeout_sec,
        namespace="sec",
    )


def build_efts_http(config: Config | None = None) -> CachedHttp:
    """Client for efts.sec.gov full-text search — paced slower (it is rate-sensitive)."""
    cfg = config or get_config()
    cfg.ensure_dirs()
    return CachedHttp(
        cache_dir=cfg.cache_dir,
        user_agent=sec_user_agent(),
        min_interval_sec=1.0 / cfg.pacing.efts_requests_per_sec,
        max_retries=cfg.pacing.max_retries,
        timeout_sec=cfg.pacing.http_timeout_sec,
        namespace="efts",
    )
