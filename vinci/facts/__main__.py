"""``python -m vinci.facts {ingest,parity,verify,screen-replay}``: the EDGAR writer, the checks.

    python -m vinci.facts ingest --cache-dir <dir>                            # the pages' snapshot
    python -m vinci.facts ingest --scope screen --run <run_id> --cache-dir <dir>
    python -m vinci.facts parity --cache-dir <dir> [--exclude <T> ...]        # every page, shadow
    python -m vinci.facts screen-replay --run <run_id> --cache-dir <dir>      # the screen, shadow
    python -m vinci.facts verify [--name screen] [--store r2://]       # manifest against objects
    python -m vinci.facts upload [--name screen]                       # a snapshot's objects to R2

``--cache-dir`` is the directory that holds ``sec/`` (``Config.cache_dir``, ``data/cache`` by
default). Nothing here fetches: a name the cache does not hold is reported, never requested.

NO NAME IS HELD BACK (operator ruling 2026-11-05): an ingest writes its rule's whole population and
an upload sends a snapshot whole, so neither takes ``--exclude``; a command line that passes it
(the records carry some, from the lifted hold) is refused by argparse before anything is read.
``parity``'s ``--exclude`` is an ordinary skip: a page left out of the comparison, counted in its
output (a committed page the current snapshot does not hold, say).

``pages`` is written to ``data/facts/objects`` (committed); ``screen``, past the 50 MB committed
cap, to ``$VINCI_FACTS_STORE`` or the git-ignored ``data/facts/local``, with only its manifest
committed (:mod:`vinci.facts.store`). ``upload`` copies a snapshot's objects to the R2 bucket the
four ``R2_*`` variables name, from the machine that wrote them, then reads every one back.
``--store r2://`` makes ``verify``, ``parity`` and
``screen-replay`` read the objects from R2 (:mod:`vinci.facts.remote`). Run as a module, this loads
the repository's ``.env`` first (``vinci.config.load_local_env``), as the ``vinci`` CLI does.
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
    IngestShapeError,
    NotInCacheError,
    acceptance_rows,
    read_cached_companyfacts,
    rows_from_companyfacts,
    unread_reason,
)
from vinci.facts.reader import FactStore, manifest_summary
from vinci.facts.scope import (
    RULE,
    ScopeName,
    scope_names,
    screen_scope_names,
)
from vinci.facts.store import (
    DEFAULT_NAME,
    FactsStoreError,
    FileEntry,
    OrderEntry,
    build_manifest,
    is_r2,
    load_manifest,
    manifests_dir,
    requested_location,
    store_root,
    verify_manifest,
    write_entity,
    write_filings,
    write_manifest,
)

DOSSIERS = Path("data") / "dossiers"
FOLLOWED = Path("data") / "followed.json"
SNAPSHOTS = Path("data") / "snapshots"
#: Where each scope's objects live: the pages' fit the committed cap, the screen's do not.
STORAGE = {"pages": "git", "screen": "local"}


def _scope(a: argparse.Namespace, *, exclude: frozenset[str] = frozenset()
           ) -> tuple[list[ScopeName], int, str]:
    """The names the scope's rule selects less ``exclude``, how many it left out, and the rule.
    Only the parity passes ``exclude``; it reads the pages' scope alone."""
    if getattr(a, "scope", "pages") == "screen":
        if not a.run:
            raise SystemExit("--scope screen needs --run <run_id>")
        names, rule = screen_scope_names(a.run, SNAPSHOTS)
        return names, 0, rule
    names, excluded = scope_names(DOSSIERS, FOLLOWED, a.cache_dir, exclude=exclude)
    return names, excluded, RULE


def cmd_ingest(a: argparse.Namespace) -> int:
    name = a.scope
    names, _, rule = _scope(a)              # the rule's whole population: no name is held back
    by_cik: dict[str, list[str]] = {}
    unread: list[dict[str, str | None]] = []
    for n in names:
        if n.cik is None:
            unread.append({"ticker": n.ticker, "cik": None, "reason": n.unresolved})
        else:
            by_cik.setdefault(n.cik, []).append(n.ticker)
    storage = STORAGE[name]
    root = store_root(a.store, storage=storage)
    # EVERY RESPONSE IS CHECKED BEFORE ANY OBJECT IS WRITTEN (TeamNostra fix request 2, RFL-D9).
    # One row of an unknown shape stopped the ingest after it had written earlier companies'
    # objects, which no manifest then named (6 left on disk, no manifest, in the audit's run).
    # Objects are named by content and may be another snapshot's too, so none is ever deleted:
    # the run refuses before it writes. Each response is read twice, never held: the screen's
    # universe is ~28M rows.
    problems = _shape_problems(by_cik, a.cache_dir)
    if problems:
        for p in problems:
            print(f"SHAPE {p}")
        print(f"nothing written: {len(problems)} cached response(s) of a shape this ingest cannot "
              "store faithfully (each named above); no object and no manifest")
        return 1
    files: list[FileEntry] = []
    orders: dict[str, OrderEntry] = {}
    filings: dict[str, OrderEntry] = {}
    entities: list[dict[str, Any]] = []
    for cik, tickers in sorted(by_cik.items()):
        try:
            resp = read_cached_companyfacts(cik, a.cache_dir)
        except NotInCacheError as exc:
            unread.extend({"ticker": t, "cik": cik, "reason": str(exc)} for t in tickers)
            print(f"UNREAD {'/'.join(tickers)} {cik}: {exc}")
            continue
        facts = json.loads(resp.text)
        got = rows_from_companyfacts(facts)
        if got.entity != cik:
            raise SystemExit(f"{cik}: the cached response is for CIK {got.entity}")
        if not got.rows:
            why = unread_reason(facts, got)
            unread.extend({"ticker": t, "cik": cik, "reason": why} for t in tickers)
            print(f"UNREAD {'/'.join(tickers)} {cik}: {why}")
            continue
        accepted = acceptance_rows(cik, got.rows, a.cache_dir)
        # ONE ENTITY AT A TIME: the screen's universe is ~28M rows, never all held at once
        got_files, orders[cik] = write_entity(got.rows, root)
        filings[cik] = write_filings(SOURCE, cik, accepted.rows, root)
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
            "acceptance": accepted.summary(),
        })
        print(f"read {'/'.join(tickers):6} {cik} fetched {resp.fetched_at:%Y-%m-%d} "
              f"{got.rows_in_response:>7,} rows, {got.exact_duplicates_dropped} exact duplicates, "
              f"{got.rows_without_filed} without a filed date; acceptance time for "
              f"{len(accepted.rows):,} of {accepted.accessions:,} accessions", flush=True)
    scope = {"rule": rule, "names_selected": len(names),
             # Both counts are kept, as 0, so every manifest states one scope shape: the two
             # written under the lifted hold state 1 and 6, and the screen replay reads the first
             # (names_selected less it is the population it replays).
             "excluded_by_operator_instruction": 0, "exclusions_listed": 0,
             "names_ingested": sum(len(e["tickers"]) for e in entities),
             "unread": sorted(unread, key=lambda u: str(u["ticker"]))}
    manifest = build_manifest(source=SOURCE, extractor=EXTRACTOR,
                              extractor_version=EXTRACTOR_VERSION, scope=scope,
                              entities=entities, files=files, orders=orders, name=name,
                              storage=storage, filings=filings)
    path = write_manifest(manifest)
    print(f"wrote {path} ({storage}: objects under {root})\n  {manifest_summary(manifest)}")
    return 0


def _shape_problems(by_cik: dict[str, list[str]], cache_dir: Path) -> list[str]:
    """Every cached response, and its submissions documents, read as the ingest reads them,
    nothing written: one line per entity this ingest cannot store faithfully."""
    problems: list[str] = []
    for cik, tickers in sorted(by_cik.items()):
        try:
            resp = read_cached_companyfacts(cik, cache_dir)
        except NotInCacheError:
            continue                          # reported as unread by the writing pass
        try:
            got = rows_from_companyfacts(json.loads(resp.text))
            if got.entity != cik:
                # the writing pass's own refusal, made here so it too precedes every write
                problems.append(f"{'/'.join(tickers)} {cik}: the cached response is for CIK "
                                f"{got.entity}")
                continue
            if got.rows:
                acceptance_rows(cik, got.rows, cache_dir)
        except (IngestShapeError, json.JSONDecodeError) as exc:
            problems.append(f"{'/'.join(tickers)} {cik}: {type(exc).__name__}: {exc}")
    return problems


def cmd_parity(a: argparse.Namespace) -> int:
    from vinci.facts.parity import as_json, compare_page
    # a ticker as typed: `--exclude burl` skips BURL, as inputs-backfill reads its own
    names, skipped, _ = _scope(a, exclude=frozenset(t.strip().upper() for t in a.exclude))
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
    head = ("page", "cut", "fetched", "past fetch", "rows in resp", "filed after cut",
            "dups held once", "rows compared", "store rows", "row diffs", "order diffs",
            "keys compared", "key diffs", "keys restated", "ambiguous keys", "get() sample",
            "get() diffs")
    print("| " + " | ".join(head) + " |\n|" + "---|" * len(head))
    for r in results:
        if r.unread:
            print(f"| {r.ticker} | {r.cut} | UNREAD: {r.unread} |")
            continue
        if r.changed:
            print(f"| {r.ticker} | {r.cut} | CHANGED: {r.changed} |")
            continue
        cells = (r.ticker, r.cut, r.fetched_at[:10], "yes" if r.past_fetch else "no",
                 f"{r.rows_in_response:,}", f"{r.rows_after_cut:,}",
                 f"{r.duplicates_held_once} (of {r.duplicates_dropped_by_ingest})",
                 f"{r.rows_compared:,}", f"{r.store_rows:,}",
                 r.row_diffs, r.order_diffs, f"{r.keys_compared:,}", r.key_diffs,
                 f"{r.keys_restated:,}", r.ambiguous_keys, r.get_sampled, r.get_diffs)
        print("| " + " | ".join(str(c) for c in cells) + " |")
        if r.examples:
            print(f"    {r.ticker}: showing {len(r.examples)} of {r.discrepancies:,} "
                  "discrepancies")
        for e in r.examples:
            print(f"    {r.ticker}: {e}")
    bad = [r.ticker for r in results if not r.zero_diff]
    changed = [r.ticker for r in results if r.changed]
    unread = [r.ticker for r in results if r.unread]
    print(f"\n{len(results)} page-cuts compared; {len(results) - len(bad)} zero-diff; "
          f"{len(bad)} not zero-diff{(': ' + ', '.join(bad)) if bad else ''} — of them "
          f"{len(changed)} CHANGED (the cache holds another response than the snapshot "
          f"ingested) and {len(unread)} UNREAD; {skipped} name(s) of the pages' scope left out "
          "by --exclude")
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


def _shown(problems: list[str], k: int = 20) -> None:
    for p in problems[:k]:
        print(f"  PROBLEM {p}")
    if len(problems) > k:
        print(f"  (showing {k} of {len(problems)} problems)")


def cmd_verify(a: argparse.Namespace) -> int:
    manifest = load_manifest(a.snapshot, name=a.name)
    print(manifest_summary(manifest))
    fetch_problems: list[str] = []
    if is_r2(requested_location(a.store, storage=manifest["storage"])):
        from vinci.facts.remote import R2Objects, manifest_objects
        remote = R2Objects.from_env()
        with remote.client:
            rep = remote.fetch_all(manifest_objects(manifest), workers=a.workers)
        print(f"  from R2: {rep.objects:,} objects named ({rep.bytes:,} bytes): {rep.fetched:,} "
              f"fetched ({rep.fetched_bytes:,} bytes) and {rep.cached:,} already in the cache "
              f"{remote.cache}, each hashed against its entry; {len(rep.problems)} problems")
        fetch_problems = rep.problems
        _shown(fetch_problems)
        root = remote.cache
    else:
        root = store_root(a.store, storage=manifest["storage"])
    problems = verify_manifest(manifest, root, check_content=not a.no_content)
    _shown(problems)
    print(("verified: every object present, its bytes as sealed, rows as stated"
           + ("" if a.no_content else ", its rows hashing to its name, every order complete"))
          if not problems else f"{len(problems)} problems")
    return 1 if problems or fetch_problems else 0


def cmd_upload(a: argparse.Namespace) -> int:
    from vinci.facts.remote import (
        R2Client,
        bucket_against_manifests,
        upload_refusal,
        upload_snapshot,
    )
    manifest = load_manifest(a.snapshot, name=a.name)
    if (why := upload_refusal(manifest)) is not None:      # before any request (RFL-D6)
        print(f"snapshot {manifest['snapshot_id']}: nothing uploaded — {why}")
        return 1
    root = store_root(a.store, storage=manifest["storage"])
    t = manifest["totals"]
    print(f"snapshot {manifest_summary(manifest)}\n  + {t['order_files']:,} order objects "
          f"({t['order_bytes']:,} bytes); the local copy: {root} ({manifest['storage']})")
    with R2Client.from_env() as client:
        status = client.head_bucket()
        if status != 200:
            print(f"HeadBucket HTTP {status}: the bucket cannot be read with these keys; "
                  "nothing uploaded")
            return 1
        rep = upload_snapshot(manifest, root, client, workers=a.workers)
        print(f"  objects the manifest names: {rep.objects:,} ({rep.bytes:,} bytes)\n"
              f"  written: {rep.written:,} ({rep.written_bytes:,} bytes); already in the bucket "
              f"with the same bytes: {rep.present:,} ({rep.present_bytes:,} bytes); not "
              f"attempted: {rep.not_attempted:,}\n"
              f"  read back and hashed against the manifest: {rep.read_back:,} of {rep.objects:,} "
              f"({rep.read_back_bytes:,} bytes); {len(rep.problems)} problems")
        _shown(rep.problems)
        if not a.no_audit:
            read, unread = [], 0
            for i in sorted(p.stem for p in manifests_dir().glob("*.json")):
                try:
                    read.append(load_manifest(i))
                except FactsStoreError:          # an older version kept in the tree
                    unread += 1
            audit = bucket_against_manifests(client, read)
            print(f"  the bucket after this upload, against the {len(read)} committed manifests "
                  f"it reads ({unread} manifest{'' if unread == 1 else 's'} not read: a "
                  "version this code does not read) "
                  f"({audit['manifest_objects']:,} distinct objects, "
                  f"{audit['manifest_bytes']:,} bytes): {audit['bucket_keys']:,} keys "
                  f"({audit['bucket_bytes']:,} bytes); {audit['named_by_a_manifest']:,} named by "
                  f"a manifest, {audit['named_by_none']:,} named by none; "
                  f"{audit['named_and_absent']:,} named and absent; {audit['size_differs']:,} "
                  "with a size other than the manifest's")
            # the audit is the evidence that only the manifests' objects are in the bucket: a key
            # none names, or a named key of another size, fails the run.
            # Named-and-absent does not: a committed manifest may not have been uploaded yet.
            if audit["named_by_none"] or audit["size_differs"]:
                print(f"  FAIL: the bucket holds {audit['named_by_none']:,} key(s) no committed "
                      f"manifest names and {audit['size_differs']:,} named key(s) of another size")
                return 1
    return 1 if rep.problems or rep.not_attempted else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m vinci.facts")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("ingest", cmd_ingest), ("parity", cmd_parity), ("verify", cmd_verify),
                     ("screen-replay", cmd_screen_replay), ("upload", cmd_upload)):
        p = sub.add_parser(name)
        p.set_defaults(fn=fn)
        p.add_argument("--store", default=None,
                       help="object root (default: data/facts/objects for a committed snapshot; "
                            "$VINCI_FACTS_STORE or data/facts/local for a local one)"
                            + ("" if name in ("ingest", "upload") else "; r2:// reads from R2"))
        if name != "ingest":
            p.add_argument("--snapshot", default=None, help="snapshot id (default: current.json)")
        if name in ("verify", "upload"):
            p.add_argument("--name", default=DEFAULT_NAME, choices=sorted(STORAGE),
                           help="which current snapshot (default: pages)")
            p.add_argument("--workers", type=int, default=16,
                           help="R2 requests in flight at once (default 16)")
        if name == "upload":
            p.add_argument("--no-audit", action="store_true",
                           help="skip listing the bucket against every committed manifest")
        if name == "ingest":
            p.add_argument("--scope", default="pages", choices=sorted(STORAGE),
                           help="which companies (default: the committed pages)")
        if name in ("ingest", "screen-replay"):
            p.add_argument("--run", default=None, help="the screen run (--scope screen)")
        if name == "parity":
            p.add_argument("--exclude", action="append", default=[], metavar="TICKER",
                           help="leave this name's page out of the comparison (repeatable): an "
                                "ordinary skip, counted in the output")
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
    from vinci.config import load_local_env
    load_local_env()                     # the CLI entry only: a library import stays hermetic
    sys.exit(main())
