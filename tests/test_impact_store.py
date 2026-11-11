"""The $0 store fill (`vinci.impact.store`): a page the primary's stale store cannot price is
priced from the HTTP cache, never fetched. Its corpus run (2026-11-11): from the primary's
`data/vinci.db`, which held no bar for BURL, GOOGL, LLY, MCK, NFLX, ROST, TGT, TJX, UBER, V, MDY
or SPY, the fill priced all 30 names (27 pages and the benchmarks) to the 2026-11-09 close in
3.9 s with every socket refused (record)."""
from __future__ import annotations

import datetime as dt
import pathlib
import socket

import pytest

from vinci.eod.client import _AGGS
from vinci.impact import child
from vinci.impact import store as sto
from vinci.netcache import CachedHttp


def test_the_cache_file_is_the_one_production_reads(tmp_path: pathlib.Path) -> None:
    http = CachedHttp(cache_dir=tmp_path, user_agent="t", min_interval_sec=0.0,
                      namespace="polygon")
    start, end = dt.date(2021, 7, 1), dt.date(2026, 11, 10)
    url = http._with_params(_AGGS.format(symbol="MCK", start="2021-07-01", end="2026-11-10"),
                            {"adjusted": "true", "sort": "asc", "limit": 50000})
    assert sto.aggs_cache_file(tmp_path, "MCK", start, end) == http._cache_path(url)
    http.close()


def test_the_newest_cached_window_is_found_and_an_uncached_name_is_none(
        tmp_path: pathlib.Path) -> None:
    start, today = dt.date(2021, 7, 1), dt.date(2026, 11, 11)
    for end in (dt.date(2026, 11, 3), dt.date(2026, 11, 10)):
        f = sto.aggs_cache_file(tmp_path, "MCK", start, end)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("{}")
    assert sto.newest_cached_end(tmp_path, "MCK", start, today) == dt.date(2026, 11, 10)
    assert sto.newest_cached_end(tmp_path, "BURL", start, today) is None


def test_the_fill_can_reach_no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket.socket, "connect", socket.socket.connect)
    monkeypatch.setattr(socket.socket, "connect_ex", socket.socket.connect_ex)
    monkeypatch.setattr(socket, "create_connection", socket.create_connection)
    child.block_sockets()
    with pytest.raises(RuntimeError, match="network is blocked"):
        socket.create_connection(("api.polygon.io", 443), timeout=1)
