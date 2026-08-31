"""Backfill the IWM benchmark price history into the local store (internal_id ``IDX-IWM``).

The dossier idio comparison (``market_180d_return``) and the Brief stock-performance exhibit read
``store.get_price_history("IDX-IWM")``. Grouped-daily ingestion only stores the finalist universe,
so the benchmark index is fetched here per-symbol — one cached Polygon aggregates call — and stored
under its canonical benchmark id. Idempotent (INSERT OR REPLACE); re-run safe.

    .venv/bin/python -m scripts.fetch_benchmark_iwm            # ~2.2y to today
    .venv/bin/python -m scripts.fetch_benchmark_iwm 2024-01-01 2026-07-13

Adjusted closes (splits/dividends) so the rebased path carries no fabricated step. Fail-loud: a
non-OK Polygon status raises; an empty range prints and exits non-zero rather than writing nothing.
"""

from __future__ import annotations

import os
import pathlib
import sys
from datetime import date, timedelta

from vinci.config import load_local_env
from vinci.eod.client import PolygonEodClient
from vinci.schemas.market import PriceBar
from vinci.store import Store
from vinci.universe import benchmark_identity

_DB_PATH = "data/vinci.db"
_LOOKBACK_DAYS = 800  # ~2.2y — covers every finalist's 52w exhibit window + the 180d idio lookback


def main(argv: list[str]) -> int:
    load_local_env()
    ident = benchmark_identity("IWM")
    end = date.fromisoformat(argv[1]) if len(argv) > 1 else date.today()
    start = date.fromisoformat(argv[0]) if len(argv) > 0 else end - timedelta(days=_LOOKBACK_DAYS)

    client = PolygonEodClient.from_config()
    rows = client.daily_bars(ident.eod_symbol, start, end)
    if not rows:
        print(f"FAIL: no {ident.eod_symbol} bars for {start}..{end}", file=sys.stderr)
        return 1

    bars = [
        PriceBar(
            internal_id=ident.internal_id,
            bar_date=d,
            open=b.open,
            high=b.high,
            low=b.low,
            close=b.close,
            volume=b.volume,
            source="polygon-aggs",
        )
        for d, b in rows
    ]
    store = Store(_DB_PATH)
    n = store.write_prices(bars)
    print(
        f"stored {n} {ident.eod_symbol} bars as {ident.internal_id}: "
        f"{rows[0][0]} .. {rows[-1][0]} (last close {rows[-1][1].close:.2f})"
    )
    return 0


if __name__ == "__main__":
    # Run from the repo root — the data roots are CWD-relative (see build_cohort_pool.py).
    os.chdir(pathlib.Path(__file__).resolve().parents[1])
    raise SystemExit(main(sys.argv[1:]))
