"""Daily OHLCV for the tape's tickers — fetched SERVER-SIDE, committed, then served statically.

WHY NOT FROM THE BROWSER. The build spec asks the page to call Polygon when a chart opens. It must
not: that puts ``POLYGON_API_KEY`` into client JavaScript, where every viewer can read it, and the
dashboard is a READ-ONLY static mirror by design (``frontend/lib/snapshots.js``: "there is NO write
path"; ``frontend/lib/ui.js``: "nothing here triggers a write, compute, or fetch"). So bars are
pulled by this module, written under ``data/calls/<handle>/bars/``, committed, and mirrored to the
frontend — exactly the path every other number on the dashboard already takes. The cost is honest
and stated on the page: prices are as of the last fetch, not live.

ONE CLIENT, NOT TWO. ``PolygonEodClient.daily_bars`` is the fund's existing per-symbol adapter —
adjusted, disk-cached, fail-loud on a bad status. Nothing here re-implements it.

THE WINDOW comes from ``tickers.json`` (first mention −3mo, last mention +12mo), so a ticker
mentioned once costs one small call rather than a full-history pull.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from vinci.calls.accounts import account_dir
from vinci.eod.client import PolygonEodClient

#: Benchmark for the tape. SPY, because ``tracker.py`` pre-registered SPY and changing the
#: benchmark changes every excess return. The fund's own screens use IWM; both now exist, so every
#: rendered comparison names which one it is rather than saying "the benchmark".
BENCHMARK = "SPY"


def bars_dir(handle: str) -> Path:
    return account_dir(handle) / "bars"


def _iso(d: str | date) -> date:
    return d if isinstance(d, date) else date.fromisoformat(str(d)[:10])


def fetch_account_bars(
    handle: str, *, client: PolygonEodClient | None = None, only: set[str] | None = None,
    on_progress: object = None,
) -> dict[str, int]:
    """Fetch every tracked ticker's window into ``bars/<TICKER>.json``. Returns {ticker: n_bars}.

    Re-running is cheap: ``CachedHttp`` serves an unexpired response from disk, so this is safe to
    run repeatedly and only pays for windows that have actually moved on.
    """
    cli = client or PolygonEodClient.from_config()
    d = account_dir(handle)
    spec = json.loads((d / "tickers.json").read_text())
    rows = [t for t in spec["tickers"] if only is None or t["ticker"] in only]
    if only and BENCHMARK not in {t["ticker"] for t in rows}:
        full = {t["ticker"]: t for t in spec["tickers"]}
        if BENCHMARK in full:
            rows.append(full[BENCHMARK])
    out = bars_dir(handle)
    out.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for i, t in enumerate(rows, 1):
        sym = t["ticker"]
        got = cli.daily_bars(sym, _iso(t["fetch_from"]), _iso(t["fetch_to"]))
        payload = {
            "ticker": sym,
            "from": t["fetch_from"], "to": t["fetch_to"],
            # COMPACT ROWS, not objects: [iso, open, high, low, close, volume]. 214 tickers of
            # keyed objects is several megabytes of repeated field names in a file the browser
            # downloads.
            "bars": [[bd.isoformat(), b.open, b.high, b.low, b.close, b.volume] for bd, b in got],
        }
        (out / f"{sym}.json").write_text(json.dumps(payload, separators=(",", ":")))
        counts[sym] = len(got)
        if callable(on_progress):
            on_progress(i, len(rows), sym, len(got))
    return counts


def load_bars(handle: str, ticker: str) -> list[tuple[date, float, float, float, float, float]]:
    """Read one ticker's committed bars. Empty list when absent — the caller renders an empty state
    rather than crashing (8 of the account's symbols are delisted or renamed)."""
    p = bars_dir(handle) / f"{ticker}.json"
    if not p.is_file():
        return []
    raw = json.loads(p.read_text())
    return [(date.fromisoformat(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]),
             float(r[5])) for r in raw.get("bars", [])]
