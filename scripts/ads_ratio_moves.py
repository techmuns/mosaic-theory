"""Does a change to the ADS-ratio reader move a depositary line's ratio? A git ref's reader against
this checkout's, through `EntityResolver.ads_ratio` on the primary universe's depositary lines —
cache only, measure only.

`vinci.resolver.ads_ratio` decides how many ordinary shares an ADS represents, which divides every
per-share figure set against an ADS price (the screen's per-ADS P/E, the anchor's traded units).
The population is #840's: the lines of the committed ``data/snapshots/universe_snapshot.jsonl``
that a Polygon reference pull types ``ADRC``/``GDR`` (`universe.DEPOSITARY_TYPES`) — the pull read
from ``--types-cache`` as fetched on ``--types-date``, the reference feed's results only (never a
request URL, which carries the key). Each issuer's ratio is read as the weekly run reads it,
``resolver.ads_ratio(cik, snapshot as_of)``, once with ``--ref``'s `read_ratio` and once with this
checkout's, EDGAR read only from the ``--cache-dir`` caches (at any age; a miss is recorded, never
fetched). Nothing is written back.

    PYTHONPATH=. python scripts/ads_ratio_moves.py --cache-dir <checkout>/data/cache \\
        --types-cache <checkout>/data/cache --types-date 2026-10-17 --ref origin/main \\
        --out <path.json>

(`PYTHONPATH=.` imports THIS checkout's `vinci`. The script runs from the repo root, so a relative
path argument is read from there.)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import types
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from vinci.netcache import CachedHttp, HttpError
from vinci.resolver import resolver as rv
from vinci.resolver.ads_ratio import read_ratio
from vinci.resolver.index import to_eod_symbol
from vinci.universe import DEPOSITARY_TYPES


class _CacheOnly(CachedHttp):
    """Every ``--cache-dir``'s SEC entries, read at any age, first hit wins; nothing is fetched or
    written — a miss raises `HttpError` and is recorded, so a line it touched reads as uncovered."""

    def __init__(self, dirs: list[Path]) -> None:
        super().__init__(cache_dir=dirs[0], user_agent="cache-only", min_interval_sec=0,
                         namespace="sec")
        self._dirs = [CachedHttp(cache_dir=d, user_agent="cache-only", min_interval_sec=0,
                                 namespace="sec") for d in dirs]
        self.misses: list[str] = []

    def _read_cache(self, url: str, ttl_seconds: float | None) -> str | None:
        for h in self._dirs:
            if (hit := CachedHttp._read_cache(h, url, None)) is not None:
                return hit
        return None

    def _fetch_with_retries(self, url: str, **kw: Any) -> str:
        self.misses.append(url)
        raise HttpError(f"not in any --cache-dir: {url}")

    def _write_cache(self, url: str, text: str) -> None:
        raise AssertionError("a cache-only replay never writes")


def _reader_at(ref: str) -> Callable[..., Any]:
    """`read_ratio` as ``ref`` has it, loaded from git — never this checkout's."""
    path = "vinci/resolver/ads_ratio.py"
    src = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True,
                         check=True).stdout
    mod = types.ModuleType("ads_ratio_at_ref")
    exec(compile(src, f"{ref}:{path}", "exec"), mod.__dict__)
    found: Callable[..., Any] = mod.read_ratio
    return found


def security_types(cache: Path, on: date) -> dict[str, str | None]:
    """``{ticker: type}`` from every cached page of Polygon's ticker reference fetched on ``on``."""
    out: dict[str, str | None] = {}
    for p in (cache / "polygon").glob("*.json"):
        try:
            entry = json.loads(p.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if urlsplit(entry.get("url", "")).path.rstrip("/") != "/v3/reference/tickers":
            continue
        if datetime.fromtimestamp(entry["fetched_at"], tz=UTC).date() != on:
            continue
        for r in json.loads(entry["text"]).get("results", []):
            if (t := r.get("ticker")) is not None:
                out[t] = r.get("type") or None
    return out


def _ratio(a: Any) -> dict[str, Any]:
    return {"status": a.status, "ordinary_per_ads": a.ordinary_per_ads, "source": a.source,
            "accession": a.accession, "reason": a.reason}


def run(dirs: list[Path], sec_types: dict[str, str | None], old: Callable[..., Any]
        ) -> dict[str, Any]:
    rows = [json.loads(x) for x in Path("data/snapshots/universe_snapshot.jsonl").read_text()
            .splitlines() if x.strip()]
    lines = []
    for r in rows:
        _sec, cik, ticker = r["internal_id"].split("-", 2)
        if sec_types.get(to_eod_symbol(ticker)) in DEPOSITARY_TYPES:
            lines.append((ticker, cik, date.fromisoformat(r["as_of"])))
    out: list[dict[str, Any]] = []
    for ticker, cik, as_of in lines:
        http = _CacheOnly(dirs)
        got: dict[str, dict[str, Any] | None] = {}
        for name, reader in (("old", old), ("new", read_ratio)):
            rv.read_ratio = reader     # type: ignore[attr-defined]  # the one name ads_ratio calls
            try:
                got[name] = _ratio(rv.EntityResolver(http=http).ads_ratio(cik, as_of))
            except HttpError:          # the submissions index is not cached: recorded as a miss
                got[name] = None
            finally:
                rv.read_ratio = read_ratio     # type: ignore[attr-defined]
        out.append({"ticker": ticker, "cik": cik, "covered": not http.misses,
                    "misses": sorted(set(http.misses)), **got})
    covered = [x for x in out if x["covered"]]
    return {
        "lines": len(out), "covered": len(covered),
        "uncovered": [x["ticker"] for x in out if not x["covered"]],
        "known_old": sum(1 for x in covered if x["old"]["status"] == "known"),
        "known_new": sum(1 for x in covered if x["new"]["status"] == "known"),
        "moved": [x for x in covered
                  if (x["old"]["status"], x["old"]["ordinary_per_ads"])
                  != (x["new"]["status"], x["new"]["ordinary_per_ads"])],
        "detail": out,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--cache-dir", action="append", required=True,
                    help="a data/cache holding SEC documents; repeat to read several")
    ap.add_argument("--types-cache", required=True, help="a data/cache holding the Polygon pull")
    ap.add_argument("--types-date", required=True, help="the day the reference pull was fetched")
    ap.add_argument("--ref", default="origin/main", help="the git ref whose reader is 'old'")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sec_types = security_types(Path(a.types_cache), date.fromisoformat(a.types_date))
    if not sec_types:
        raise SystemExit(f"no Polygon reference pull fetched {a.types_date} in {a.types_cache}")
    rep = run([Path(d) for d in a.cache_dir], sec_types, _reader_at(a.ref))
    Path(a.out).write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str))
    print(f"typed tickers {len(sec_types)} | depositary lines {rep['lines']} | covered "
          f"{rep['covered']} | known {rep['known_old']} -> {rep['known_new']} | moved "
          f"{len(rep['moved'])}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    # From the repo root, as every data-tree script here runs (tests/test_script_cwd_convention.py).
    # In __main__ only: importing this module never moves a caller's working directory.
    os.chdir(Path(__file__).resolve().parents[1])
    raise SystemExit(main())
