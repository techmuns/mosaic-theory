"""Committed SEC data for pins that run the REAL assembly path — so they never reach the network.

The maintenance pins build a resolver and an EDGAR client from a Config, exactly as production does,
so the only clean place to supply SEC data is the cache those clients read. `seed_sec_cache` writes
the committed fixtures there through the SEC client itself (`vinci.sec.build_sec_http` — one owner
of the cache layout and namespace), stamped as fetched now so the one-day TTL never expires them
mid-run:

- `tests/fixtures/sec_reference/` — the fleet's slice of `company_tickers.json` and
  `company_tickers_exchange.json` (`scripts/build_sec_reference_fixture.py`);
- `tests/fixtures/companyfacts/` — the committed companyfacts subsets
  (`scripts/build_companyfacts_fixture.py`).

`no_network` refuses outbound connections for the duration, so a fixture gap FAILS with the fix in
its message instead of quietly fetching — the same guard `tests/test_dilution_denominator.py` uses.
"""
from __future__ import annotations

import contextlib
import functools
import json
import pathlib
import socket
from collections.abc import Iterator

from vinci.config import Config
from vinci.edgar.client import _COMPANYFACTS
from vinci.resolver.resolver import _CT_URL, _CTE_URL
from vinci.sec import build_sec_http

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
SEC_REFERENCE = FIXTURES / "sec_reference"
COMPANYFACTS = FIXTURES / "companyfacts"


@functools.lru_cache(maxsize=1)
def _entries() -> tuple[tuple[str, str], ...]:
    """(URL, body) for every committed SEC fixture — read and parsed once per test process."""
    entries = [(_CT_URL, (SEC_REFERENCE / "company_tickers.json").read_text()),
               (_CTE_URL, (SEC_REFERENCE / "company_tickers_exchange.json").read_text())]
    for path in sorted(COMPANYFACTS.glob("*.json")):
        text = path.read_text()
        entries.append((_COMPANYFACTS.format(cik=str(json.loads(text)["cik"]).zfill(10)), text))
    return tuple(entries)


def seed_sec_cache(cfg: Config) -> int:
    """Write every committed SEC fixture into ``cfg``'s cache; return the number of entries."""
    http = build_sec_http(cfg)
    try:
        for url, text in _entries():
            http._write_cache(url, text)
    finally:
        http.close()
    return len(_entries())


@contextlib.contextmanager
def no_network() -> Iterator[None]:
    """Refuse outbound connections: a pin that needs SEC data the fixtures lack fails loudly."""
    real = socket.create_connection

    def refuse(*_a: object, **_k: object) -> object:
        raise AssertionError(
            "a maintenance pin reached for the network — it reads committed SEC fixtures only. "
            "A missing name: run `python scripts/build_sec_reference_fixture.py` (ticker files) or "
            "`python scripts/build_companyfacts_fixture.py` (facts) in the SAME PR that adds it.")

    socket.create_connection = refuse  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.create_connection = real  # type: ignore[assignment]
