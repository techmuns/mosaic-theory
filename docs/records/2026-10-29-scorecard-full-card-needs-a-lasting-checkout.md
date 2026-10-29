---
id: 2026-10-29-scorecard-full-card-needs-a-lasting-checkout
status: shipped
date: 2026-10-29
prs: [852]
supersedes:
superseded-by:
---

# An `exceptions` source's full card lives only in the checkout that ran it, so its `--write` runs in a checkout that lasts — RUNBOOKS §k

**WHAT.** RUNBOOKS §k now says to run an `exceptions` source's `vinci audit quality --write`
(`prices`, since #847) in a checkout that lasts: the primary checkout or another permanent checkout
of the repo, never a session worktree.

**WHY.** Since #847, the prices snapshot commits only its exceptions. The full card, every name for
every check, goes to the git-ignored `data/data_quality_full/<source>/<date>.json` of the checkout
that ran it, and the snapshot names it by path and sha256 (`rows.full`). A session's worktree is
deleted when the session is archived, and the card goes with it.

This came up on 2026-10-29. The first card was written in the compact-snapshot session's worktree,
`quirky-khayyam-b2ec8b`, as `data/data_quality_full/prices/2026-10-29.json`. The coordinator held
back that session's archive. The operator kept the session open, so the card survives with it.

**HOW VERIFIED.** No code changes.
- **The card is where the record says.** It sits under `data/data_quality_full/` in that worktree,
  reported ignored (`!!`) by `git status --ignored` on 2026-10-29.
- **Losing it costs only the per-name rows that passed.** The committed snapshot
  `data/snapshots/data_quality/prices/2026-10-29.json` keeps every exception and the counts, and
  `core.reconcile` refuses any card whose listed rows plus counts don't add back to its fleet.

**BOUNDARY.**
- **The card:** 2,663,520 bytes, 2,440 names, read from a read-only copy of the primary store
  (bars 2021-09-01 → 2026-08-05), per #847's PR body and record.
- **The worktree check:** 2026-10-29.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **This is a rule to remember, not a guard.** Nothing in code stops a `--write` from a worktree.
  A guard would have to tell a session worktree from a permanent checkout, which the code can't do
  today.
- **If the session is archived,** the 2026-10-29 card goes with it. Its exceptions stay committed,
  and re-running on the same store reproduces every row while the inputs sha256 still matches
  (RUNBOOKS §k).
