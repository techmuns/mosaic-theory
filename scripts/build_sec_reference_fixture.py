"""Freeze the slice of SEC's ticker files the MAINTENANCE pins resolve through, so they run offline.

WHY THIS EXISTS. `tests/test_maintenance_path.py` and `tests/test_maintenance_identity.py` built a
Config that symlinked the real `data/cache` — the resolver's index and the EDGAR cache. `data/cache`
is git-ignored, so on a fresh checkout (every CI run, every Codex cloud task) the resolver fetched
`https://www.sec.gov/files/company_tickers.json` live inside `pytest -m "not network"`, and the
cache entry's one-day TTL made a laptop re-fetch it daily too. MEASURED 2026-10-23 on a fresh
checkout of `ca17bc05` with outbound traffic refused: 8 of the 21 pins failed, every one on
`Exhausted retries for https://www.sec.gov/files/company_tickers.json`, after 7 minutes of retries.
CI passed only because GitHub's runners can reach sec.gov.

THE SAME REMEDY AS `build_price_fixture.py` AND `build_companyfacts_fixture.py` (STATE D17): commit
the small slice the pins read, and the cache dependency disappears. An instrumented real run of the
two files showed exactly two reference files read (`company_tickers.json` and
`company_tickers_exchange.json`) plus companyfacts for 21 names, all of which the committed
companyfacts fixture already holds.

SLICE BY THE FLEET, KEEPING THE RESOLVER'S SEMANTICS. Kept: every row whose ticker is a fleet name,
AND every row sharing a CIK with one — so a dual-class issuer keeps all its share classes and a
ticker claimed by two CIKs still resolves as ambiguous. The fleet is DERIVED (committed dossiers ∪
scenario records ∪ followed names), never hand-listed, so it cannot drift from what the pins walk.

RE-RUN IT IN THE SAME PR THAT ADDS A NAME TO THE FLEET. `tests/test_sec_reference_fixture.py`
fails loudly and names this script when a fleet name is missing from the slice.

    python scripts/build_sec_reference_fixture.py

Needs a warm cache or network; it is an operator tool, never imported by the suite.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tests" / "fixtures" / "sec_reference"


def fleet_names(data_dir: pathlib.Path) -> set[str]:
    """Committed dossiers ∪ scenario records ∪ followed names — every name a maintenance pin
    walks."""
    dossiers = {p.name for p in (data_dir / "dossiers").iterdir()
                if p.is_dir() and (p / "dossier.json").is_file()}
    records = {p.stem for p in (ROOT / "scenarios").glob("*.json") if not p.stem.startswith("_")}
    followed_path = data_dir / "followed.json"
    followed = set(json.loads(followed_path.read_text())) if followed_path.is_file() else set()
    return {t.upper() for t in dossiers | records | followed}


def slice_tickers(ct: dict[str, Any], names: set[str]) -> dict[str, Any]:
    """`company_tickers.json` rows for the fleet and every row sharing a CIK with a fleet name."""
    ciks = {rec["cik_str"] for rec in ct.values() if str(rec["ticker"]).upper() in names}
    kept = [rec for rec in ct.values()
            if str(rec["ticker"]).upper() in names or rec["cik_str"] in ciks]
    return {str(i): rec for i, rec in enumerate(kept)}


def slice_exchange(cte: dict[str, Any], names: set[str]) -> dict[str, Any]:
    """`company_tickers_exchange.json` rows chosen by the same rule, in SEC's fields/data shape."""
    fields = cte["fields"]
    i_cik, i_ticker = fields.index("cik"), fields.index("ticker")
    ciks = {row[i_cik] for row in cte["data"] if str(row[i_ticker]).upper() in names}
    rows = [row for row in cte["data"] if str(row[i_ticker]).upper() in names or row[i_cik] in ciks]
    return {"fields": fields, "data": rows}


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from vinci.config import get_config
    from vinci.resolver.resolver import _CT_URL, _CTE_URL
    from vinci.sec import build_sec_http

    cfg = get_config()
    http = build_sec_http(cfg)
    names = fleet_names(cfg.data_dir)
    # The resolver's own one-day TTL: a slice is cut from SEC's CURRENT file, never a stale cache.
    ct = slice_tickers(http.get_json(_CT_URL, ttl_seconds=86_400.0), names)
    cte = slice_exchange(http.get_json(_CTE_URL, ttl_seconds=86_400.0), names)
    i_ticker = cte["fields"].index("ticker")
    missing = {
        "company_tickers.json": sorted(names - {str(r["ticker"]).upper() for r in ct.values()}),
        "company_tickers_exchange.json": sorted(
            names - {str(r[i_ticker]).upper() for r in cte["data"]}),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, body in (("company_tickers.json", ct), ("company_tickers_exchange.json", cte)):
        # sort_keys: a regeneration with nothing moved is byte-identical — a diff is real change
        (OUT_DIR / name).write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
    print(f"fleet: {len(names)} names · company_tickers rows: {len(ct)} · "
          f"company_tickers_exchange rows: {len(cte['data'])} → {OUT_DIR}")
    for label, gone in missing.items():
        if gone:
            # A fleet name SEC does not list (a synthetic benchmark, a delisting) is reported, and
            # tests/test_sec_reference_fixture.py fails on it per file.
            print(f"not in SEC's {label} ({len(gone)}): {', '.join(gone)}")
    return 0


if __name__ == "__main__":
    # Run from the repo root: ~28 data roots resolve against the CWD (see the note in
    # build_cohort_pool.py). In __main__ only, so importing this module cannot chdir the suite.
    os.chdir(ROOT)
    raise SystemExit(main())
