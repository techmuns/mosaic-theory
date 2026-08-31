"""Backfill the ENTITY MASTER's missing EDGAR SIC codes — fill holes, never rewrite known values.

WHY IT EXISTS. 516 of 2,485 committed `securities.jsonl` rows carried no SIC. None was in the
current universe (the `unknown_sic` gate excludes a name it cannot confirm, so an admitted name
always has one) and — after #523 repaired IT/Gartner — none was ledgered, so nothing on a decision
surface read one. But that is a statement about TODAY's book, not a property of the data: the row
that DID get read was IT, and it was exposed for exactly the reason the rest are — **ledgered (or
followed) but out of the cap band**, so no `build_universe` ever comes back to enrich it. Every
name in this population is one ledger entry away from being the next IT. This closes the hole.

HOW THE HOLES GOT THERE, two eras, both now shut:
  * PRE-#83 (before 2026-07-06) `build_universe` fetched a SIC for its Axis-1 gate and then
    DISCARDED it — a dead write. Rows written in that era carry NULL and were only ever fixed for
    names the universe re-admitted afterwards.
  * The PARTIAL-UPSERT CLOBBER (#523): an un-enriched `upsert_security` nulled a known SIC. Fixed
    at the store — `sic` now COALESCEs — which is WHY this backfill is durable rather than a value
    the next `vinci refresh` would erase again. Run this only on top of that fix.

WHAT IT REFUSES TO DO.
  * **It fills holes; it does not re-classify.** If a CIK already has a SIC anywhere (its issuer
    row or a sibling share class) and EDGAR now reports a DIFFERENT one, that is a re-classification
    event, not a hole — it is REPORTED and SKIPPED. A backfill silently rewriting known values
    would be an unreviewed data migration wearing a repair's name.
  * **A SIC that EDGAR does not publish stays NULL.** No inference from the name, the exchange, or
    a sibling issuer. Missing stays missing and is counted out loud (CLAUDE.md: UNKNOWN or raise,
    never a guessed value).
  * **Synthetic `IDX-` benchmark rows are never touched** — SPY/IWM/MDY et al. are not SEC issuers
    and have no submissions record; a SIC on one would be a fabrication.

HOW IT WRITES. Through `Store.upsert_security` + `export_snapshots`, i.e. the REAL production
path, not a hand-edit of the JSONL — so the no-row-drop guard, the schema, and the COALESCE
semantics all apply exactly as they do in a pipeline run. One EDGAR SIC belongs to the ISSUER, so
it is applied to every share class under that CIK, which is what `resolver._enrich_issuer` already
does when it enriches an issuer's securities.

    python scripts/backfill_entity_master_sic.py --dry-run   # report only, writes nothing
    python scripts/backfill_entity_master_sic.py             # fetch, apply, export

~420 cached EDGAR submissions calls at 8 req/s (~1 min cold, free on re-run).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vinci.config import get_config  # noqa: E402
from vinci.resolver.resolver import EntityResolver  # noqa: E402
from vinci.store import Store  # noqa: E402

#: Synthetic benchmark identities (SPY/IWM/MDY/sector ETFs) — not SEC issuers, no submissions
#: record, and a SIC on one would be invented. Never fetched, never written.
SYNTHETIC_PREFIX = "IDX-"

#: The entity-master tables this touches, in schema order (parents before children — the store's
#: rebuild is FK-ordered and a child-first subset fails).
ENTITY_TABLES: tuple[str, ...] = ("issuers", "securities")


def _rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="fetch and report, but write nothing")
    ap.add_argument("--limit", type=int, default=None,
                    help="stop after N CIKs (a cost gate for timing the full pass)")
    args = ap.parse_args()

    cfg = get_config()
    snaps = cfg.snapshots_dir
    securities = _rows(snaps / "securities.jsonl")
    issuers = _rows(snaps / "issuers.jsonl")

    # --- WHICH CIKs HAVE A HOLE -----------------------------------------------------------------
    # A hole is a NULL sic on a security row or on an issuer row. Both are collected because they
    # diverge: a preferred class (HWCPZ) can be null while its issuer and common share (HWC) carry
    # the code, and the reverse is possible too.
    sics_by_cik: defaultdict[str, set[str]] = defaultdict(set)   # the KNOWN values per CIK
    holes: set[str] = set()
    for r in securities:
        if str(r["internal_id"]).startswith(SYNTHETIC_PREFIX):
            continue
        cik = str(r["cik"])
        if r.get("sic"):
            sics_by_cik[cik].add(str(r["sic"]))
        else:
            holes.add(cik)
    for r in issuers:
        cik = str(r["cik"])
        if not cik:
            # THE SYNTHETIC BENCHMARK ISSUER (`issuer_id="IDX"`, `cik=""` — `benchmark_identity`).
            # The securities side is excluded by its `IDX-` internal_id, but the issuer row carries
            # no such prefix, and an empty CIK reached `sic_for` as `pad_cik("")` → a bare
            # `ValueError: invalid literal for int()`. Caught in the 10-CIK cost-gate dry run.
            # An empty CIK is the structural mark of a synthetic identity in BOTH tables.
            continue
        if r.get("sic"):
            sics_by_cik[cik].add(str(r["sic"]))
        else:
            holes.add(cik)

    targets = sorted(holes)
    if args.limit is not None:
        targets = targets[: args.limit]
    n_synthetic = sum(1 for r in securities
                      if str(r["internal_id"]).startswith(SYNTHETIC_PREFIX))
    n_sec_holes = sum(1 for r in securities if not r.get("sic")) - n_synthetic
    n_iss_holes = sum(1 for r in issuers if not r.get("sic"))
    print(f"{len(targets)} CIK(s) with a missing SIC ({n_sec_holes} security row(s), "
          f"{n_iss_holes} issuer row(s)); {n_synthetic} synthetic {SYNTHETIC_PREFIX} row(s) "
          f"excluded by design")

    # --- FETCH ----------------------------------------------------------------------------------
    resolver = EntityResolver.from_config(cfg)
    resolved: dict[str, tuple[str, str | None]] = {}
    absent_at_edgar: list[str] = []
    fetch_failed: list[tuple[str, str]] = []
    # (cik, known, fetched) — reported, never applied
    conflicts: list[tuple[str, str, str]] = []

    for i, cik in enumerate(targets, 1):
        if i % 50 == 0 or i == len(targets):
            print(f"  … {i}/{len(targets)}", flush=True)
        try:
            sic, desc = resolver.sic_for(cik)
        except Exception as exc:                        # noqa: BLE001 — reported, never guessed
            fetch_failed.append((cik, f"{type(exc).__name__}: {exc}"))
            continue
        if not sic:
            absent_at_edgar.append(cik)                 # EDGAR publishes none → stays NULL
            continue
        known = sics_by_cik.get(cik, set())
        if known and sic not in known:
            # a RE-CLASSIFICATION, not a hole — out of a backfill's remit
            conflicts.append((cik, "/".join(sorted(known)), sic))
            continue
        resolved[cik] = (sic, desc)

    # --- REPORT ---------------------------------------------------------------------------------
    print(f"\nRESOLVED           : {len(resolved)}")
    print(f"ABSENT AT EDGAR    : {len(absent_at_edgar)}  (stays NULL — never inferred)")
    print(f"FETCH FAILED       : {len(fetch_failed)}")
    print(f"RE-CLASSIFICATIONS : {len(conflicts)}  "
          f"(reported, NOT applied — a backfill fills holes)")
    for cik, known, got in conflicts:
        print(f"    {cik}: entity master has {known}, EDGAR says {got}")
    for cik, why in fetch_failed:
        print(f"    FAILED {cik}: {why}")
    if absent_at_edgar:
        print(f"    no SIC published for: {', '.join(absent_at_edgar[:20])}"
              f"{' …' if len(absent_at_edgar) > 20 else ''}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0
    if not resolved:
        print("\nnothing to write")
        return 0

    # --- APPLY, through the real store path ------------------------------------------------------
    # One EDGAR SIC belongs to the ISSUER, so it lands on every share class under that CIK — the
    # same rule `resolver._enrich_issuer` applies. Only rows whose sic is currently NULL are
    # rewritten; the store's COALESCE would preserve a known value anyway, but not touching it
    # keeps the diff exactly as wide as the repair.
    by_cik: defaultdict[str, list[str]] = defaultdict(list)
    for r in securities:
        if not r.get("sic") and not str(r["internal_id"]).startswith(SYNTHETIC_PREFIX):
            by_cik[str(r["cik"])].append(str(r["internal_id"]))

    # THE ISSUER'S NAME MUST SURVIVE THIS (found in verification, not review). `upsert_security`
    # writes ONE Identity's `name` to BOTH tables, and four CIKs hold two securities under two
    # DIFFERENT names — a renamed company still carrying its old ticker's row (DCOM/DCBG,
    # SHOE/SCVL, DMC/FDP, HAPN/LC). Writing the null-SIC row of such a pair silently RENAMED the
    # issuer, because the row that had lagged behind happened to be written last. A SIC backfill
    # renaming issuers is an unreviewed data migration wearing a repair's name, so each touched
    # issuer's name is restored by RE-UPSERTING the sibling security whose name the issuer row
    # already carried — public API only, and it reasserts exactly the prior state rather than
    # patching a column behind the store's back.
    issuer_name = {str(r["cik"]): str(r["name"]) for r in issuers}
    sibling_named: dict[str, str] = {}
    for r in securities:
        cik = str(r["cik"])
        if str(r["name"]) == issuer_name.get(cik):
            sibling_named.setdefault(cik, str(r["internal_id"]))

    written, restored, unrestorable = 0, [], []
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(snaps, tables=ENTITY_TABLES)

        def _upsert(internal_id: str, sic: str, desc: str | None) -> None:
            ident = store.get_security(internal_id)
            if ident is None:
                raise RuntimeError(f"{internal_id} vanished between read and write — refusing to "
                                   f"continue on a store that disagrees with the snapshot")
            store.upsert_security(ident.model_copy(update={"sic": sic, "sic_description": desc}))

        for cik, (sic, desc) in resolved.items():
            ids = by_cik.get(cik) or []
            if not ids:
                # the hole was on the ISSUER row only — carry the fetch through any one of its
                # securities, which is what updates the issuer row
                ids = [str(r["internal_id"]) for r in securities if str(r["cik"]) == cik][:1]
            for internal_id in ids:
                _upsert(internal_id, sic, desc)
                written += 1
            # restore the issuer name if this CIK's rows disagree about it
            if any(str(r["name"]) != issuer_name.get(cik)
                   for r in securities if str(r["internal_id"]) in ids):
                keeper = sibling_named.get(cik)
                if keeper is None:
                    unrestorable.append(cik)
                elif keeper not in ids:
                    _upsert(keeper, sic, desc)
                    restored.append(cik)

        counts = store.export_snapshots(snaps, tables=ENTITY_TABLES)

    print(f"\nwrote {written} security row(s) across {len(resolved)} issuer(s); exported {counts}")
    if restored:
        print(f"issuer name preserved on {len(restored)} CIK(s) whose securities disagree on it: "
              f"{', '.join(restored)}")
    if unrestorable:
        print(f"WARNING — no security carries the issuer name for {unrestorable}; the issuer row's "
              f"`name` may have moved. Inspect before committing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
