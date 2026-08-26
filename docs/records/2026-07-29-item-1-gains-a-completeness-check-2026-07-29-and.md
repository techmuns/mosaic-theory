---
id: 
status: recorded
date: 2026-07-29
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**ITEM 1 GAINS A COMPLETENESS CHECK — 2026-07-29, and it closed a defect the gate itself had.**
A SMPL re-assembly in a worktree whose EOD store held no SMPL bars produced a dossier with **no
spot, no 52-week range and no as-of** — and reported "1 done · 0 error(s)", raised no caveat, and
**PASSED the freshness gate**. The gate catches *cap ÷ shares disagrees with spot*; it did not
catch *there is no spot*, because `reconcile_cap` returns None on an absent input and
`check_freshness` read None as nothing-to-report. **Completeness and reconciliation are different
checks and the gate conflated them** — the guard-that-cannot-fire class, inside a guard built to
close that class. The comment that justified it ("an absent input is its own fail-loud elsewhere")
was wrong: for a missing price at assembly there IS no elsewhere. The FIELD layer was honest
throughout (`status=unknown, note="no price bars"`); nothing at BUILD level noticed, which is what
made it shippable. Now `absent_cap_inputs()` names every missing input and the build REFUSES —
following the unusual-items guard's precedent that a guard which cannot run must not report a pass.
Per-name table: 11/11 carry all three inputs, so it fires only on a genuinely incomplete build.
**THE DEGRADED ARTIFACT WAS REVERTED, NOT COMMITTED.**
