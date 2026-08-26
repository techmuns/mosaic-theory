---
id: 
status: shipped
date: 2026-08-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**THE WEEKLY SCREEN WAS DOWN FOR FOUR WEEKS AND NOTHING SAID SO — FIXED 2026-08-24
(`fix/universe-seed-row-drop`).** Runs on 2026-08-03, 08-10, 08-17 and 08-24 all failed; the served
queue sat frozen at `screen_run_at 2026-08-14` while a red job re-ran itself every Monday.

    ROW-DROP on issuers.jsonl: writing 1810 row(s) over 2304 on disk
    would drop 503 existing row(s) by PK.

**THE CAUSE IS THE EMPTY STORE, NOT THE GUARD.** `data/vinci.db` is git-ignored, so on every CI run
`build_universe` starts with NOTHING. It upserts only what that fetch admits and then exports
`issuers`/`securities` — accumulate-only tables, because the entity master has to resolve a
ledgered name after it leaves the universe. Writing one fetch's subset over the committed master is
a shrink, and the no-row-drop guard was RIGHT to refuse it. `run_weekly` does seed the store, but at
its own line AFTER `build_universe` has already exported; the seed has to happen inside the context
that writes.

**IT PASSED ON EVERY LAPTOP THE WHOLE TIME** — a developer's store already holds the accumulation.
Green everywhere except where it matters, the same shape as the eleven-merge maintenance-pin streak.

**THE FIX SEEDS ONLY THE TABLES THAT MAY NOT SHRINK**, and that restriction is the load-bearing
half. `rebuild_from_snapshots` gained a `tables` subset mirroring `export_snapshots`;
`BUILD_UNIVERSE_SEED_TABLES` is DERIVED as `BUILD_UNIVERSE_TABLES ∩ NO_ROW_DROP_TABLES`, never
hand-listed. Seeding EVERYTHING — the obvious fix, and the one first proposed in chat — would also
reload `universe_snapshot`, which is POINT-IN-TIME (the committed file holds exactly one `as_of`):
it would have started accumulating dates it was never meant to keep, trading one table's bug for
another table's silent semantic change.

**INVARIANT (INVARIANT RULE) — `tests/test_universe_seed.py`, 9 pins, every one against an EMPTY
store because a populated one proves nothing here.** The outage reproduced (unseeded export raises),
the fix verified on the real committed corpus (2304 → 2304), the seed shown to survive
`clear_universe()`, and a genuinely new identity shown to still reach the master — a fix that merely
reproduced the committed file would stop recording new names, the same outage wearing the opposite
sign. **THE PIN THAT MATTERED WAS THE ONE ADDED LAST:** mutation-testing showed that DELETING THE
SEED CALL FROM `build_universe` left all eight original pins GREEN — they exercised the store
primitives, never the call site, so the guard survived its only caller being removed. That is the
pin-the-helper trap for the second time this session. A pin now runs the REAL `build_universe`
against an empty universe feed, and the mutation dies. 5/5 mutations killed.
