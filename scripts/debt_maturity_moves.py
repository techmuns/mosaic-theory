"""Does a change to the debt-maturity reader move a committed page? A git ref's reader against this
checkout's, through `mechanical.maturity_check` on every committed page — cache only, measure only.

`vinci.edgar.debt_maturities` decides which maturity a page prints: a filing's date that differs
from CIQ's GOVERNS the instrument table, the calendar and the liquidity line. For each page under
``data/dossiers/`` with a ``capital_structure``, this rebuilds the check from the page's own panel,
pointers and reference date — the assembler's own composition, `mechanical.maturity_check` — once
with ``--ref``'s reader and once with this checkout's, reading EDGAR only from the ``--cache-dir``
caches (at any age; a miss is recorded, never fetched). It prints each page whose rows moved, and
whether the ``--ref`` rebuild reproduces the committed rows. Nothing is written back.

    PYTHONPATH=. python scripts/debt_maturity_moves.py --cache-dir <checkout>/data/cache \\
        [--cache-dir <another>/data/cache] --ref origin/main --out <path.json> --skip-file <path>

THE SKIP IS REQUIRED: ``--skip-file`` lists the tickers never to read, one per line, and each is
left out by FOLDER before its page is opened and by CIK (SEC's ticker map, from the caches) for
any other folder of the same issuer. The list lives outside the repo; nothing here names it.

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
from datetime import date
from pathlib import Path
from typing import Any

from vinci.dossier import mechanical as dm
from vinci.dossier.schemas import CapitalStructure
from vinci.edgar import debt_maturities
from vinci.edgar.client import EdgarClient
from vinci.netcache import CachedHttp, HttpError


class _CacheOnly(CachedHttp):
    """Every ``--cache-dir``'s SEC entries, read at any age, first hit wins; nothing is fetched or
    written — a miss raises `HttpError` and is recorded, so a page it touched reads as uncovered."""

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


def held_ciks(dirs: list[Path], tickers: set[str]) -> set[int]:
    """The CIKs of the ``--skip-file`` tickers, from SEC's ticker map in the caches — so a held
    issuer is left out under any of its tickers, never only under the one written down."""
    url = "https://www.sec.gov/files/company_tickers.json"
    for d in dirs:
        hit = CachedHttp(cache_dir=d, user_agent="cache-only", min_interval_sec=0,
                         namespace="sec")._read_cache(url, None)
        if hit is not None:
            rows = json.loads(hit).values()
            return {int(r["cik_str"]) for r in rows if r["ticker"] in tickers}
    raise SystemExit(f"SEC's ticker map ({url}) is in no --cache-dir: the --skip-file tickers "
                     "cannot be matched to their CIKs, so nothing is run")


def _reader_at(ref: str) -> types.ModuleType:
    """`vinci.edgar.debt_maturities` as ``ref`` has it, loaded from git — never this checkout's."""
    path = "vinci/edgar/debt_maturities.py"
    src = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True,
                         check=True).stdout
    mod = types.ModuleType("debt_maturities_at_ref")
    sys.modules[mod.__name__] = mod     # a dataclass resolves its module by name
    exec(compile(src, f"{ref}:{path}", "exec"), mod.__dict__)
    return mod


def _rows(check: Any) -> list[dict[str, Any]]:
    keep = ("description", "check", "filing_maturity", "governs", "source", "note")
    return [{k: getattr(r, k) for k in keep} for r in check.rows]


def run(dirs: list[Path], old: types.ModuleType, skip: set[str], skip_ciks: set[int]
        ) -> dict[str, Any]:
    pages: list[dict[str, Any]] = []
    for path in sorted(Path("data/dossiers").glob("*/dossier.json")):
        ticker = path.parent.name
        if ticker in skip:
            continue    # by folder, before the page is opened
        doc = json.loads(path.read_text())
        if int(doc["cik"]) in skip_ciks:
            continue    # the same issuer under another folder
        raw = (doc.get("mechanical") or {}).get("capital_structure")
        if not isinstance(raw, dict) or not raw.get("maturity_check"):
            continue
        cs = CapitalStructure.model_validate(raw)
        got: dict[str, list[dict[str, Any]]] = {}
        http = _CacheOnly(dirs)
        edgar = EdgarClient(http=http, efts_http=http)     # one submissions read for both runs
        for name, reader in (("old", old), ("new", debt_maturities)):
            dm.dmx = reader     # type: ignore[attr-defined]  # the one module the check reads
            try:
                check = dm.maturity_check(
                    edgar, http, str(doc["cik"]),
                    cs.instruments.value or [], cs.covenant_pointer_rows, cs.detail_as_of,
                    date.fromisoformat(str(doc["reference_date"])))
            finally:
                dm.dmx = debt_maturities     # type: ignore[attr-defined]
            got[name] = _rows(check)
        committed = [{k: r.get(k) for k in ("description", "check", "filing_maturity", "governs",
                                            "source", "note")}
                     for r in raw["maturity_check"]["rows"]]
        pages.append({"ticker": ticker, "covered": not http.misses,
                      "misses": sorted(set(http.misses)),
                      "old_reproduces_page": got["old"] == committed,
                      "moved": [{"old": a, "new": b} for a, b in zip(got["old"], got["new"],
                                                                     strict=True) if a != b]})
    covered = [p for p in pages if p["covered"]]
    return {
        "pages": len(pages), "covered": len(covered),
        "uncovered": [p["ticker"] for p in pages if not p["covered"]],
        "old_reproduces_page": sum(1 for p in covered if p["old_reproduces_page"]),
        "rows_moved": sum(len(p["moved"]) for p in covered),
        "governing_moved": sum(1 for p in covered for m in p["moved"]
                               if m["old"]["governs"] or m["new"]["governs"]),
        "detail": pages,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--cache-dir", action="append", required=True,
                    help="a data/cache holding SEC documents; repeat to read several")
    ap.add_argument("--ref", default="origin/main", help="the git ref whose reader is 'old'")
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-file", required=True,
                    help="tickers never to read, one per line (folder and CIK)")
    a = ap.parse_args()
    dirs = [Path(d) for d in a.cache_dir]
    skip = set(Path(a.skip_file).read_text().split())
    rep = run(dirs, _reader_at(a.ref), skip, held_ciks(dirs, skip))
    Path(a.out).write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(f"pages {rep['pages']} | covered {rep['covered']} | the ref's rebuild reproduces the "
          f"committed rows on {rep['old_reproduces_page']} | rows moved {rep['rows_moved']} "
          f"(governing {rep['governing_moved']})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    # From the repo root, as every data-tree script here runs (tests/test_script_cwd_convention.py).
    # In __main__ only: importing this module never moves a caller's working directory.
    os.chdir(Path(__file__).resolve().parents[1])
    raise SystemExit(main())
