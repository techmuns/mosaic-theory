---
id: 
status: recorded
date: 2026-08-12
prs: [420]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

### THE SCHEDULED SURFACE — audited 2026-08-12 (operator-asked, post-#420)

**THE STRUCTURAL DEMOTE CHANNEL WAS DORMANT IN PRODUCTION, AND NOTHING SAID SO.** `scan_structural`
(`vinci/rank/structural.py:190`) is built, tested (16 references), source-bound to an 8-K accession
+ item + date, DEMOTE-ONLY, and it is the **only** channel permitted to move a name down. It ran
only when a human typed `vinci rank --structural`, no workflow passed the flag, and nobody had: the
2026-08-12 queue carried **0 flags across 284 names**. A company whose auditor resigned last month
could therefore sit at rank 5 looking like a bargain, and the analyst would find out only after
opening the dossier — which is the week of work the queue exists to protect.
- **FIXED, and with no flag.** `run_weekly()` now hard-wires `structural=True`; the workflow call
  stays the plain `python -m vinci run-weekly`. The first cut added a `--structural` flag and passed
  it from the YAML — **operator correction: a cron with opt-in pieces is exactly how this went
  dormant**, so the scheduled path takes no options at all. `refresh_queue(structural=…)` keeps its
  parameter only so both paths stay testable. Cost: EDGAR 8-K text + shares per candidate.
- **A LIVE SCAN REPLACES THE CARRY-FORWARD, it does not merge with it.** The carry-forward added in
  #420 exists for runs that do NOT scan. When a scan runs it is authoritative — it re-checks all
  five signals against current filings, so a name whose signal no longer fires must come back
  CLEAN. Merging would make a flag permanent: a disqualifier could never be cleared by the very
  scan designed to re-evaluate it, and the demote would outlive its own evidence. Pinned, and
  mutation-tested by merging instead of replacing.
- **This is a DECISION-PATH change, unlike everything else in #420** — it moves names in the queue
  rather than describing them. Taken on explicit operator instruction, recorded here as such.
- **REVIEW FIX (#431): "replace" had to learn what the scan actually LOOKED AT.** `scan_structural`
  fails SOFT per name, and worse, `_filings_for`/`_shares_for` CAUGHT their own HTTP errors and
  returned `[]` — so an EDGAR outage classified the name clean without even reaching the outer
  guard, and was indistinguishable from an issuer that genuinely filed nothing. Replacing flags
  wholesale on that result meant **one bad response could erase a real 8-K disqualifier and lift
  the name back above its 0.05 cap — the #420 failure, reintroduced by the fix for it.** Both
  helpers now return `None` for "never found out" vs `[]` for "looked, found nothing", and
  `scan_structural` returns a `StructuralScan(flags, covered)`. Prior flags survive for exactly the
  names the scan did not cover. The `[]`-vs-`None` distinction was the one guard the first
  mutation sweep did NOT catch — it needed its own outage test, with a quiet-issuer control so the
  fix cannot degrade into never trusting a clean result.
- **REVIEW FIX (#431): an empty universe rebuild now RAISES.** `build_universe()` has already
  cleared and exported `universe_snapshot.jsonl` by the time the check runs, so a soft return
  exited 0, and the workflow's next step commits `data/snapshots` — publishing a blank universe
  beside the previous candidates and queue **while reporting a clean run**. The commit step has no
  `if: always()`, so raising is sufficient to stop it. Pinned.

**`build-universe` WAS ON NO SCHEDULE — FIXED (operator instruction, same pass).** The universe is
the screen's INPUT: it decides which names are eligible to be screened at all (cap band, ADV floor,
operating-co gates). No workflow ran it, and the committed `universe_snapshot.jsonl` was stamped
**2026-07-29** while the screen consuming it ran **2026-08-12** — so for 14 days a name that fell
into the $300M–$10B band was never screened, a name that left it still was, and the caps doing the
banding were two weeks stale. `run_weekly()` now rebuilds it FIRST, before the screen.
- Ordering is safe by construction: `build_universe` opens its own `Store`, does a FULL replace
  (`clear_universe`), exports its own snapshot tables and closes — so the `rebuild_from_snapshots`
  immediately after reads the universe this just produced.
- The old early-exit ("no universe in snapshots — run build-universe first") is now a FAILURE
  branch, not an instruction: the build has already run, so an empty universe means it produced
  nothing and the screen is skipped loudly rather than run against an empty set.
- **This lengthens the weekly job materially** — the universe build resolves the full exchange list
  and needs EDGAR shares + SIC per surviving name, on top of the screen's own EOD + EDGAR work.
  Accepted deliberately: a fast job screening a stale universe is worse than a slow correct one.

**NOT A GAP, checked:** `vinci monitor` is marked *manual* in its own CLI help ("mark the book to
market vs benchmarks (manual)") — operator-driven by design, not an omission. `run-monthly` is
scheduled (1st, 07:00 UTC). The weekly snapshot commit cannot desync the committed frontend mirror,
because `frontend/snapshots/` is git-ignored (0 tracked files) — the gate's mirror check covers
`frontend/dossiers`, which a screen run does not touch.
