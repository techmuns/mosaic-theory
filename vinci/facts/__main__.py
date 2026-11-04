"""``python -m vinci.facts {ingest,parity,verify,screen-replay}``: the EDGAR writer, the checks.

    python -m vinci.facts ingest --cache-dir <dir> --exclude <T> ...          # the pages' snapshot
    python -m vinci.facts ingest --scope screen --run <run_id> --cache-dir <dir> --exclude <T> ...
    python -m vinci.facts parity --cache-dir <dir> --exclude <T> ...          # every page, shadow
    python -m vinci.facts screen-replay --run <run_id> --cache-dir <dir>      # the screen, shadow
    python -m vinci.facts verify [--name screen]                       # manifest against objects

``--cache-dir`` is the directory that holds ``sec/`` (``Config.cache_dir``, ``data/cache`` by
default). Nothing here fetches: a name the cache does not hold is reported, never requested. Every
``--exclude`` a current snapshot was written with must be passed again, or the ingest refuses.

``pages`` is written to ``data/facts/objects`` (committed); ``screen``, past the 50 MB committed
cap, to ``$VINCI_FACTS_STORE`` or the git-ignored ``data/facts/local``, with only its manifest
committed (:mod:`vinci.facts.store`).
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
from vinci.facts.scope import (
    RULE,
    ScopeName,
    require_exclusions,
    scope_names,
    screen_scope_names,
)
from vinci.facts.store import (
    DEFAULT_NAME,
    FileEntry,
    OrderEntry,
    build_manifest,
    load_manifest,
    store_root,
    verify_manifest,
    write_entity,
    write_manifest,
)

DOSSIERS = Path("data") / "dossiers"
FOLLOWED = Path("data") / "followed.json"
SNAPSHOTS = Path("data") / "snapshots"
#: Where each scope's objects live: the pages' fit the committed cap, the screen's do not.
STORAGE = {"pages": "git", "screen": "local"}


def _scope(a: argparse.Namespace) -> tuple[list[ScopeName], int, str]:
    if getattr(a, "scope", "pages") == "screen":
        if not a.run:
            raise SystemExit("--scope screen needs --run <run_id>")
        return screen_scope_names(a.run, SNAPSHOTS, exclude=frozenset(a.exclude))
    names, excluded = scope_names(DOSSIERS, FOLLOWED, a.cache_dir, exclude=frozenset(a.exclude))
    return names, excluded, RULE


def cmd_ingest(a: argparse.Namespace) -> int:
    name = a.scope
    listed = len(set(a.exclude))
    names, excluded, rule = _scope(a)
    # before any response is read or anything written
    require_exclusions(excluded, listed=listed, rule=rule, selected=len(names) + excluded,
                       source=SOURCE, name=name)
    by_cik: dict[str, list[str]] = {}
    unread: list[dict[str, str | None]] = []
    for n in names:
        if n.cik is None:
            unread.append({"ticker": n.ticker, "cik": None, "reason": n.unresolved})
        else:
            by_cik.setdefault(n.cik, []).append(n.ticker)
    storage = STORAGE[name]
    root = store_root(a.store, storage=storage)
    files: list[FileEntry] = []
    orders: dict[str, OrderEntry] = {}
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
        if not got.rows:
            unread.extend({"ticker": t, "cik": cik, "reason": "the cached response holds no row "
                           "with a filed date"} for t in tickers)
            print(f"UNREAD {'/'.join(tickers)} {cik}: no row with a filed date")
            continue
        # ONE ENTITY AT A TIME: the screen's universe is ~28M rows, never all held at once
        got_files, orders[cik] = write_entity(got.rows, root)
        files.extend(got_files)
        entities.append({
            "entity": cik, "tickers": sorted(tickers), "entity_name": got.entity_name,
            "source_url": resp.url, "fetched_at": resp.fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "response_sha256": resp.sha256, "rows_in_response": got.rows_in_response,
            "rows_kept": len(got.rows), "exact_duplicates_dropped": got.exact_duplicates_dropped,
            "rows_without_filed": got.rows_without_filed,
            # named beside the count, and only when there are any
            **({"rows_without_filed_named": got.rows_without_filed_named}
               if got.rows_without_filed_named else {}),
        })
        print(f"read {'/'.join(tickers):6} {cik} fetched {resp.fetched_at:%Y-%m-%d} "
              f"{got.rows_in_response:>7,} rows, {got.exact_duplicates_dropped} exact duplicates, "
              f"{got.rows_without_filed} without a filed date", flush=True)
    scope = {"rule": rule, "names_selected": len(names) + excluded,
             "excluded_by_operator_instruction": excluded, "exclusions_listed": listed,
             "names_ingested": sum(len(e["tickers"]) for e in entities),
             "unread": sorted(unread, key=lambda u: str(u["ticker"]))}
    manifest = build_manifest(source=SOURCE, extractor=EXTRACTOR,
                              extractor_version=EXTRACTOR_VERSION, scope=scope,
                              entities=entities, files=files, orders=orders, name=name,
                              storage=storage)
    path = write_manifest(manifest)
    print(f"wrote {path} ({storage}: objects under {root})\n  {manifest_summary(manifest)}")
    return 0


def cmd_parity(a: argparse.Namespace) -> int:
    from vinci.facts.parity import as_json, compare_page
    names, _, _ = _scope(a)
    results = []
    cuts: list[tuple[date | None, bool]] = [(None, False),
                                             *((date.fromisoformat(d), False) for d in a.also_at),
                                             *([(None, True)] if a.filing_eve else [])]
    with FactStore(a.snapshot, root=a.store) as store:      # the pages' check: pages only
        print(f"snapshot {manifest_summary(store.manifest)}")
        for at, eve in cuts:
            for n in names:
                if n.page is None:
                    continue
                doc = json.loads(n.page.read_text())
                results.append(compare_page(n.ticker, doc, store, a.cache_dir, at=at, eve=eve))
    head = ("page", "cut", "fetched", "rows in resp", "filed after cut", "rows compared",
            "store rows", "row diffs", "order diffs", "keys compared", "key diffs",
            "keys restated", "ambiguous keys", "get() sample", "get() diffs")
    print("| " + " | ".join(head) + " |\n|" + "---|" * len(head))
    for r in results:
        if r.unread:
            print(f"| {r.ticker} | {r.cut} | UNREAD: {r.unread} |")
            continue
        cells = (r.ticker, r.cut, r.fetched_at[:10], f"{r.rows_in_response:,}",
                 f"{r.rows_after_cut:,}", f"{r.rows_compared:,}", f"{r.store_rows:,}",
                 r.row_diffs, r.order_diffs, f"{r.keys_compared:,}", r.key_diffs,
                 f"{r.keys_restated:,}", r.ambiguous_keys, r.get_sampled, r.get_diffs)
        print("| " + " | ".join(str(c) for c in cells) + " |")
        if r.examples:
            print(f"    {r.ticker}: showing {len(r.examples)} of {r.discrepancies:,} "
                  "discrepancies")
        for e in r.examples:
            print(f"    {r.ticker}: {e}")
    bad = [r.ticker for r in results if not r.zero_diff]
    print(f"\n{len(results)} page-cuts compared; {len(results) - len(bad)} zero-diff; "
          f"{len(bad)} with a diff{(': ' + ', '.join(bad)) if bad else ''}")
    if a.json:
        Path(a.json).write_text(as_json(results))
    return 1 if bad else 0


def cmd_screen_replay(a: argparse.Namespace) -> int:
    from vinci.facts.screen_replay import print_replay, replay_run
    with FactStore(a.snapshot, name="screen", root=a.store) as store:
        print(f"snapshot {manifest_summary(store.manifest)}")
        result = replay_run(a.run, SNAPSHOTS, store, a.cache_dir, eve=a.filing_eve)
    bad = print_replay(result, shown=a.shown)
    if a.json:
        Path(a.json).write_text(json.dumps(result.as_dict(), indent=2))
    return 1 if bad else 0


def cmd_verify(a: argparse.Namespace) -> int:
    manifest = load_manifest(a.snapshot, name=a.name)
    problems = verify_manifest(manifest, store_root(a.store, storage=manifest["storage"]),
                               check_content=not a.no_content)
    print(manifest_summary(manifest))
    for p in problems:
        print(f"  PROBLEM {p}")
    print(("verified: every object present, its bytes as sealed, rows as stated"
           + ("" if a.no_content else ", its rows hashing to its name, every order complete"))
          if not problems else f"{len(problems)} problems")
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m vinci.facts")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("ingest", cmd_ingest), ("parity", cmd_parity), ("verify", cmd_verify),
                     ("screen-replay", cmd_screen_replay)):
        p = sub.add_parser(name)
        p.set_defaults(fn=fn)
        p.add_argument("--store", default=None,
                       help="object root (default: data/facts/objects for a committed snapshot; "
                            "$VINCI_FACTS_STORE or data/facts/local for a local one)")
        if name != "ingest":
            p.add_argument("--snapshot", default=None, help="snapshot id (default: current.json)")
        if name == "verify":
            p.add_argument("--name", default=DEFAULT_NAME, choices=sorted(STORAGE),
                           help="which current snapshot (default: pages)")
        if name == "ingest":
            p.add_argument("--scope", default="pages", choices=sorted(STORAGE),
                           help="which companies (default: the committed pages)")
        if name in ("ingest", "screen-replay"):
            p.add_argument("--run", default=None, help="the screen run (--scope screen)")
        if name in ("ingest", "parity"):
            p.add_argument("--exclude", action="append", default=[], metavar="TICKER",
                           help="leave this name out (repeatable)")
        if name in ("ingest", "parity", "screen-replay"):
            p.add_argument("--cache-dir", type=Path, default=get_config().cache_dir,
                           help="the directory holding the SEC cache's sec/ (read only)")
        if name in ("parity", "screen-replay"):
            p.add_argument("--json", default=None, help="also write the results here")
            p.add_argument("--filing-eve", action="store_true",
                           help="also replay at the eve of the last filing day by each cut")
        if name == "parity":
            p.add_argument("--also-at", action="append", default=[], metavar="YYYY-MM-DD",
                           help="also replay every page at this as-of (repeatable)")
        if name == "screen-replay":
            p.add_argument("--shown", type=int, default=20,
                           help="how many mismatches to print (every one is counted)")
        if name == "verify":
            p.add_argument("--no-content", action="store_true",
                           help="check bytes only, not that each object's rows hash to its name")
    a = ap.parse_args(argv)
    return int(a.fn(a))


if __name__ == "__main__":
    sys.exit(main())
