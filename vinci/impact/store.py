"""A price store that prices every committed page, filled at $0 from the HTTP cache (`fill`).

WHY (2026-11-11). The primary checkout's ``data/vinci.db`` is a stale copy BY DESIGN: every build
refreshes a COPY of it (RUNBOOKS §i step 2, "never the primary file"), so the bars a committed page
was built from live in that build's copy, and the primary never sees them. On 2026-11-11 it priced
18 of the 27 committed pages, to 2026-08-11, with no MCK bar at all. A $0 page build refuses a name
with no bars ("no price history in the store"), and a "0 of 17 move" says nothing of the other ten.

HOW, WITHOUT SPENDING. Every per-symbol pull any checkout made is in the shared HTTP cache under
the URL production asked for (`eod.client._AGGS` with its params). For each page's ticker and the
cap-band benchmarks, `fill` finds the newest cached window from ``start``, then runs production's
own ``vinci refresh <names> --aggs`` on a COPY of the source store, in a sandbox, with the cache
served frozen AND every socket refused (`child.block_sockets`): a response the cache does not hold
fails loud instead of being fetched. A name with no cached window is named, for the operator to
refresh — never pulled here.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

from vinci.impact import run as rn

#: The cap-band benchmarks every page's market legs read (RUNBOOKS §i step 2).
BENCHMARKS = ("IWM", "MDY", "SPY")
#: How far back from today a cached window's end is looked for.
LOOKBACK_DAYS = 45


def aggs_cache_file(cache_root: Path, symbol: str, start: dt.date, end: dt.date) -> Path:
    """Where production's per-symbol pull for this window is cached (`PolygonEodClient` →
    `CachedHttp`: the full URL with its params, sha256-named, under the ``polygon`` namespace)."""
    from vinci.eod.client import _AGGS
    from vinci.netcache import CachedHttp

    url = CachedHttp._with_params(_AGGS.format(symbol=symbol, start=start.isoformat(),
                                               end=end.isoformat()),
                                  {"adjusted": "true", "sort": "asc", "limit": 50000})
    return cache_root / "polygon" / f"{hashlib.sha256(url.encode('utf-8')).hexdigest()}.json"


def newest_cached_end(cache_root: Path, symbol: str, start: dt.date, today: dt.date,
                      lookback: int = LOOKBACK_DAYS) -> dt.date | None:
    for back in range(lookback + 1):
        end = today - dt.timedelta(days=back)
        if aggs_cache_file(cache_root, symbol, start, end).is_file():
            return end
    return None


def frontiers(db: Path, symbols: list[str]) -> dict[str, str | None]:
    """Each symbol's newest stored bar (through `securities`), or None."""
    out: dict[str, str | None] = dict.fromkeys(symbols)
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as c:
        for sym in symbols:
            row = c.execute("select max(p.bar_date) from prices p join securities s "
                            "on s.internal_id = p.internal_id where s.ticker = ?",
                            (sym,)).fetchone()
            out[sym] = row[0] if row else None
    return out


def fill(*, repo: Path, source: Path, out: Path, cache_root: Path, start: dt.date,
         today: dt.date, env_file: Path | None, python: str = sys.executable) -> dict[str, Any]:
    """A copy of ``source`` at ``out/impact-store/data/vinci.db`` with every committed page's
    ticker and the benchmarks refreshed from the cache only; returns what it did."""
    if rn._inside(out, repo):
        raise rn.ImpactError(f"--out {out} is inside the repository; keep the store outside it")
    pages = sorted(p.parent.name for p in (repo / "data" / "dossiers").glob("*/dossier.json"))
    symbols = [*pages, *BENCHMARKS]
    db = out / "impact-store" / "data" / "vinci.db"
    if db.exists():
        raise rn.ImpactError(f"{db} exists: one store, one folder")
    rn.snapshot_store(source, db)
    before = frontiers(db, symbols)
    ends = {sym: newest_cached_end(cache_root, sym, start, today) for sym in symbols}
    groups: dict[dt.date, list[str]] = {}
    for sym, end in ends.items():
        if end is not None:
            groups.setdefault(end, []).append(sym)
    box = out / "sandbox"
    (box / "data").mkdir(parents=True, exist_ok=True)
    (box / "data" / "vinci.db").symlink_to(db.resolve())
    (box / "data" / "cache").symlink_to(cache_root.resolve())
    runs = []
    for end, syms in sorted(groups.items()):
        done = subprocess.run(
            [python, "-P", str(rn.CHILD), "--expect-root", str(repo / "vinci"), "--frozen-cache",
             "--no-network", "--run-module", "vinci.cli", "refresh", *syms, "--aggs",
             "--start", start.isoformat(), "--end", end.isoformat()],
            cwd=box, env=rn.child_env(repo, env_file), capture_output=True, text=True)
        runs.append({"end": end.isoformat(), "symbols": syms, "exit": done.returncode,
                     "tail": (done.stdout + done.stderr)[-1500:]})
    shutil.rmtree(box)
    after = frontiers(db, symbols)
    return {"store": str(db), "source": str(source), "start": start.isoformat(),
            "symbols": symbols, "before": before, "after": after,
            "uncached": sorted(s for s, e in ends.items() if e is None), "runs": runs,
            "unpriced": sorted(s for s in symbols if after[s] is None)}


def lines(res: dict[str, Any]) -> list[str]:
    out = [f"store: {res['store']} (a .backup of {res['source']}), filled from the cache only, "
           f"windows from {res['start']}"]
    for r in res["runs"]:
        out.append(f"  refresh --aggs to {r['end']}: {len(r['symbols'])} name(s), exit "
                   f"{r['exit']}" + ("" if r["exit"] == 0 else f" — {r['tail'][-400:]}"))
    priced = [s for s in res["symbols"] if res["after"][s] is not None]
    out.append(f"priced {len(priced)} of {len(res['symbols'])} (the committed pages and "
               f"{', '.join(BENCHMARKS)}):")
    out += [f"  {s}: {res['before'][s] or 'no bar'} → {res['after'][s] or 'no bar'}"
            for s in res["symbols"]]
    if res["uncached"]:
        out.append(f"NOT IN THE CACHE, so not priced here ({len(res['uncached'])}): "
                   f"{', '.join(res['uncached'])} — `vinci refresh <names> --aggs` on a store "
                   "copy is a Polygon pull: the operator's call")
    return out


def to_json(res: dict[str, Any]) -> str:
    return json.dumps(res, indent=1, sort_keys=True)
