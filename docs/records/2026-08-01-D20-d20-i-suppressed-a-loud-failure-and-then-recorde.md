---
id: D20
status: recorded
date: 2026-08-01
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
date-source: git (first commit containing this text)
---

**D20. I SUPPRESSED A LOUD FAILURE AND THEN RECORDED GIT'S BEHAVIOUR AS THE BUG**
(2026-08-01; the first cut of this entry was wrong and the correction IS the entry).

During #303 a mutation edited a newly-created, not-yet-added caveat artifact, and the revert did not
revert: the mutated value (a caveat claiming 412 rows for a 423-row run) survived into the full-suite
run, where the test caught it. **The first cut of this entry blamed `git checkout --`, claiming it
"returned success having done nothing" on an untracked path.** That is FALSE, and review caught it by
running the case in a scratch repo rather than trusting the write-up:

    $ git checkout -- untracked.txt
    error: pathspec 'untracked.txt' did not match any file(s) known to git
    $ echo $?
    1

**Git failed loudly and correctly. The command that silenced it was mine:**
`git checkout -- <path> 2>/dev/null || true` — `2>/dev/null` hid the message and `|| true` ate the
exit code. So the hazard is NOT the revert idiom, which is reliable; it is the reflexive
`2>/dev/null || true` tail added to make a cleanup step "not fail". **D16 is the same class** (a gate
whose exit status is swallowed by a pipe), and this is its second instance: *a command that cannot
fail is not a safeguard.*

**SECOND FACE, SAME RULE — AND IT BIT TWICE DURING THE REVIEW THAT RECORDED IT** (2026-08-01, #307). On a TRACKED file `git checkout -- <file>` reverts to **HEAD**, not to *before my mutation*. Mid-review I widened a lint's regex, mutation-tested it, and restored with `git checkout --` — discarding the UNCOMMITTED widening and silently reinstating the narrow version; `git status` then read clean, so the loss looked like success. Re-applied, then **lost the same way a second time**: the command block that appended this very paragraph also ran two `git checkout -- STATE.md` mutation-restores after it, which reverted the paragraph along with the mutations.

**THE RULE BOTH FACES SHARE: `git checkout --` restores HEAD, so it is a mutation-restore ONLY when the pre-mutation state IS HEAD.** Untracked file -> it errors and reverts nothing (face one). Uncommitted edit -> it succeeds and reverts too much (face two). **The safe idiom is `cp file /tmp/bak` before mutating and `cp` back after, or commit first** — which is what this session did for every `vinci/` mutation and failed to do for the one file it was editing at the time.

**THE CORRECTION MATTERS MORE THAN THE INCIDENT.** As first written, this entry would have taught a
future reader to distrust `git checkout --` (loud, dependable) instead of distrusting `|| true` (the
actual defect) — a wrong diagnosis in the authoritative record, which is worse than no record. Same
shape as #302's guard comment asserting a generality its pattern did not have. **The operational
rule stands unchanged and is still `git checkout -- <file>`, never `git stash`**; what is banned is
appending `2>/dev/null || true` to it. For a file not yet in the index there is nothing to revert TO
— regenerate it from its source of truth, or `git clean` it.
