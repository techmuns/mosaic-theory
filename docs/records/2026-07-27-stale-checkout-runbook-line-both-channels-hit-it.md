---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

9. **STALE-CHECKOUT RUNBOOK LINE (both channels hit it, 2026-07-27).** *Never run, preview, or
   test from the primary checkout `/Users/work/Documents/GitHub/mosaic-theory` — it is another
   session's working tree and is routinely tens of commits stale. Work only in an isolated
   worktree, and root any preview server in the worktree UNDER TEST.* This channel edited
   mechanical.py + tests there by momentum and read a stale committed dossier, which made a
   freshness pin fire spuriously (caught, reverted, re-applied in the worktree). The other
   channel's #216 preview was rooted in the same checkout, then **45 commits stale**, and briefly
   looked like a total render outage. Two independent channels, one footgun, one day apart.
