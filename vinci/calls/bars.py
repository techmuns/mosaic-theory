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

A CASHTAG IS NOT ALWAYS A SYMBOL. He posts the ticker he knew; the vendor may want a different
string. ``tickers.json``'s ``renamed`` map is read as **cashtag → the symbol Polygon serves it
under**, which covers two cases the fetcher used to fail silently on:

- a RENAME mid-window. Polygon serves each symbol only for the span it was live, so fetching the
  cashtag alone truncated the window with NOTHING SAID — ``$SQ`` stopped dead at 2025-01-17, the
  day Block became XYZ, and every later ``$SQ`` post lost its price.
- NOTATION. ``$BRKB`` is how he types it and ``BRK.B`` is what Polygon answers to; the cashtag
  returns an empty series and the file looks like a delisting.

The first needs a splice, the second is the successor's series outright — ``_splice_rename``
handles both, and ``null`` (TWTR) is a delisting with no successor at all.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from vinci.calls.accounts import account_dir
from vinci.eod.client import PolygonEodClient, RawBar

#: Benchmark for the tape. SPY, because ``tracker.py`` pre-registered SPY and changing the
#: benchmark changes every excess return. The fund's own screens use IWM; both now exist, so every
#: rendered comparison names which one it is rather than saying "the benchmark".
BENCHMARK = "SPY"


#: WHAT A RENAME HANDOFF LOOKS LIKE. Both bounds are face-validity, not tuned: a rename hands the
#: series over at the next session (SQ→XYZ is 4 calendar days, across a holiday weekend), and the
#: seam is an ordinary session's move ($86.96 → $88.06 open, +1.3%). A months-long hole or a
#: 2×-style step is not a rename — it is the WRONG PAIR, and splicing it would fabricate one
#: continuous price history out of two different companies.
_SEAM_MAX_GAP_DAYS = 10
_SEAM_MAX_MOVE = 0.5
#: Where both symbols serve the same date they are the same security, so their adjusted closes
#: must agree. Beyond this they do not, and the map entry is wrong.
_OVERLAP_TOL = 0.01

Series = list[tuple[date, RawBar]]


def _splice_rename(old: Series, new: Series, *, cashtag: str, successor: str) -> Series:
    """Join a renamed ticker's two symbol-halves into ONE continuous series.

    The halves do not overlap in practice (``$SQ`` ends 2025-01-17, ``XYZ`` starts 2025-01-21), so
    this is a concatenation rather than a merge. Where they DO overlap the cashtag's own symbol
    wins — but only after its closes are checked against the successor's, because agreement on the
    shared dates is the evidence that these are one security at all.

    RAISES rather than papering over: a bad map entry is a wrong answer, not a missing one, and a
    silently spliced pair would read as a clean price history forever after.
    """
    if not old:
        return new                      # the window opens after the rename
    if not new:
        return old                      # the window closes before it
    shared = {d for d, _ in old} & {d for d, _ in new}
    if shared:
        o, n = dict(old), dict(new)
        off = [d for d in sorted(shared)
               if abs(n[d].close / o[d].close - 1.0) > _OVERLAP_TOL]
        if off:
            d0 = off[0]
            raise ValueError(
                f"${cashtag} → {successor}: the two symbols serve {len(shared)} of the same dates "
                f"but disagree on {len(off)} of them (e.g. {d0}: {o[d0].close} vs {n[d0].close}) — "
                f"they are not the same security, so the `renamed` entry is wrong")
    tail = old[-1]
    after = [b for b in new if b[0] > tail[0]]
    if not after:
        return old
    head = after[0]
    gap = (head[0] - tail[0]).days
    if gap > _SEAM_MAX_GAP_DAYS:
        raise ValueError(
            f"${cashtag} → {successor}: {gap} days between {tail[0]} and {head[0]} — a rename "
            f"hands over at the next session, so this is a suspension or the wrong successor, "
            f"not a rename; splicing it would hide the hole")
    move = head[1].open / tail[1].close - 1.0
    if abs(move) > _SEAM_MAX_MOVE:
        raise ValueError(
            f"${cashtag} → {successor}: the seam moves {move:+.1%} ({tail[0]} close "
            f"{tail[1].close} → {head[0]} open {head[1].open}) — that is a split or the wrong "
            f"symbol, not a rename")
    return old + after


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
    renamed: dict[str, str | None] = spec.get("renamed") or {}
    counts: dict[str, int] = {}
    for i, t in enumerate(rows, 1):
        sym = t["ticker"]
        lo, hi = _iso(t["fetch_from"]), _iso(t["fetch_to"])
        got = cli.daily_bars(sym, lo, hi)
        # A cashtag with a live successor is fetched TWICE and joined — one call more, for the
        # half of the window the cashtag's own symbol no longer covers. `null` means delisted with
        # no successor (TWTR), which is the cashtag alone and an honest short series.
        successor = renamed.get(sym)
        spliced_at: str | None = None
        if successor:
            nxt = cli.daily_bars(successor, lo, hi)
            joined = _splice_rename(got, nxt, cashtag=sym, successor=successor)
            if nxt and joined is not got:
                seam = [d for d, _ in joined if d >= nxt[0][0]]
                spliced_at = seam[0].isoformat() if seam and got else None
            got = joined
        payload = {
            "ticker": sym,
            "from": t["fetch_from"], "to": t["fetch_to"],
            # COMPACT ROWS, not objects: [iso, open, high, low, close, volume]. 214 tickers of
            # keyed objects is several megabytes of repeated field names in a file the browser
            # downloads.
            "bars": [[bd.isoformat(), b.open, b.high, b.low, b.close, b.volume] for bd, b in got],
        }
        if successor:
            # PROVENANCE: which symbols this series is actually made of, so a reader never has to
            # infer from a date why the ticker changed hands mid-file.
            payload["renamed_to"] = successor
            if spliced_at:
                payload["spliced_at"] = spliced_at
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
