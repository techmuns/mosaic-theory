"""``python -m vinci.facts {ingest,parity,verify}``: the EDGAR writer, the parity, the check.

    python -m vinci.facts ingest --cache-dir <dir holding sec/>   # writes objects + a manifest
    python -m vinci.facts parity --cache-dir <dir holding sec/>   # every committed page, shadow
    python -m vinci.facts verify                                  # manifest against its objects

``--cache-dir`` is the directory that holds ``sec/`` (``Config.cache_dir``, ``data/cache`` by
default). Nothing here fetches: a name the cache does not hold is reported, never requested.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from vinci.config import get_config
from vinci.facts.edgar_ingest import (
    EXTRACTOR,
    EXTRACTOR_VERSION,
    SOURCE,
    NotInCacheError,
    read_cached_companyfacts,
    rows_from_companyfacts,
)
from vinci.facts.reader import FactStore, manifest_summary
from vinci.facts.scope import RULE, ScopeName, scope_names
from vinci.facts.store import (
    build_manifest,
    load_manifest,
    store_root,
    verify_manifest,
    write_manifest,
    write_partitions,
)

DOSSIERS = Path("data") / "dossiers"
FOLLOWED = Path("data") / "followed.json"


def _scope(a: argparse.Namespace) -> tuple[list[ScopeName], int]:
    return scope_names(DOSSIERS, FOLLOWED, a.cache_dir, exclude=frozenset(a.exclude))


def cmd_ingest(a: argparse.Namespace) -> int:
    names, excluded = _scope(a)
    by_cik: dict[str, list[str]] = {}
    unread: list[dict[str, str | None]] = []
    for n in names:
        if n.cik is None:
            unread.append({"ticker": n.ticker, "cik": None, "reason": n.unresolved})
        else:
            by_cik.setdefault(n.cik, []).append(n.ticker)
    rows: list[dict[str, Any]] = []
    entities: list[dict[str, Any]] = []
    for cik, tickers in sorted(by_cik.items()):
        try:
            resp = read_cached_companyfacts(cik, a.cache_dir)
        except NotInCacheError as exc:
            unread.extend({"ticker": t, "cik": cik, "reason": str(exc)} for t in tickers)
            print(f"UNREAD {'/'.join(tickers)} {cik}: {exc}")
            continue
        got = rows_from_companyfacts(json.loads(resp.text))
        if got.entity != cik:
            raise SystemExit(f"{cik}: the cached response is for CIK {got.entity}")
        rows.extend(got.rows)
        entities.append({
            "entity": cik, "tickers": sorted(tickers), "entity_name": got.entity_name,
            "source_url": resp.url, "fetched_at": resp.fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "response_sha256": resp.sha256, "rows_in_response": got.rows_in_response,
            "rows_kept": len(got.rows), "exact_duplicates_dropped": got.exact_duplicates_dropped,
            "rows_without_filed": got.rows_without_filed,
        })
        print(f"read {'/'.join(tickers):6} {cik} fetched {resp.fetched_at:%Y-%m-%d} "
              f"{got.rows_in_response:>7,} rows, {got.exact_duplicates_dropped} exact duplicates, "
              f"{got.rows_without_filed} without a filed date")
    root = store_root(a.store)
    files = write_partitions(rows, root)
    scope = {"rule": RULE, "names_selected": len(names) + excluded,
             "excluded_by_operator_instruction": excluded,
             "names_ingested": sum(len(e["tickers"]) for e in entities),
             "unread": sorted(unread, key=lambda u: str(u["ticker"]))}
    manifest = build_manifest(source=SOURCE, extractor=EXTRACTOR,
                              extractor_version=EXTRACTOR_VERSION, scope=scope,
                              entities=entities, files=files)
    path = write_manifest(manifest)
    print(f"wrote {path} under {root}\n  {manifest_summary(manifest)}")
    return 0


def cmd_parity(a: argparse.Namespace) -> int:
    from vinci.facts.parity import as_json, compare_page
    names, _ = _scope(a)
    results = []
    cuts: list[date | None] = [None, *(date.fromisoformat(d) for d in a.also_at)]
    with FactStore(a.snapshot, root=a.store) as store:
        print(f"snapshot {manifest_summary(store.manifest)}")
        for at in cuts:
            for n in names:
                if n.page is None:
                    continue
                doc = json.loads(n.page.read_text())
                results.append(compare_page(n.ticker, doc, store, a.cache_dir, at=at))
    head = ("page", "cut", "fetched", "rows in resp", "filed after cut", "rows compared",
            "store rows", "row diffs", "order diffs", "keys compared", "key diffs",
            "keys restated", "ambiguous keys", "get() sample", "get() diffs")
    print("| " + " | ".join(head) + " |\n|" + "---|" * len(head))
    for r in results:
        cells = (r.ticker, r.cut, r.fetched_at[:10], f"{r.rows_in_response:,}",
                 f"{r.rows_after_cut:,}", f"{r.rows_compared:,}", f"{r.store_rows:,}",
                 r.row_diffs, r.order_diffs, f"{r.keys_compared:,}", r.key_diffs,
                 f"{r.keys_restated:,}", r.ambiguous_keys, r.get_sampled, r.get_diffs)
        print("| " + " | ".join(str(c) for c in cells) + " |")
        for e in r.examples:
            print(f"    {r.ticker}: {e}")
    bad = [r.ticker for r in results if not r.zero_diff]
    print(f"\n{len(results)} page-cuts compared; {len(results) - len(bad)} zero-diff; "
          f"{len(bad)} with a diff{(': ' + ', '.join(bad)) if bad else ''}")
    if a.json:
        Path(a.json).write_text(as_json(results))
    return 1 if bad else 0


def cmd_verify(a: argparse.Namespace) -> int:
    manifest = load_manifest(a.snapshot)
    problems = verify_manifest(manifest, store_root(a.store))
    print(manifest_summary(manifest))
    for p in problems:
        print(f"  PROBLEM {p}")
    print("verified: every object present, hashing to its name, rows as stated"
          if not problems else f"{len(problems)} problems")
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m vinci.facts")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("ingest", cmd_ingest), ("parity", cmd_parity), ("verify", cmd_verify)):
        p = sub.add_parser(name)
        p.set_defaults(fn=fn)
        p.add_argument("--store", default=None, help="object root (default $VINCI_FACTS_STORE "
                                                     "or data/facts/objects)")
        if name != "ingest":
            p.add_argument("--snapshot", default=None, help="snapshot id (default: current.json)")
        if name != "verify":
            p.add_argument("--cache-dir", type=Path, default=get_config().cache_dir,
                           help="the directory holding the SEC cache's sec/ (read only)")
            p.add_argument("--exclude", action="append", default=[], metavar="TICKER",
                           help="leave this name out (repeatable)")
        if name == "parity":
            p.add_argument("--json", default=None, help="also write the results here")
            p.add_argument("--also-at", action="append", default=[], metavar="YYYY-MM-DD",
                           help="also replay every page at this as-of (repeatable)")
    a = ap.parse_args(argv)
    return int(a.fn(a))


if __name__ == "__main__":
    sys.exit(main())
