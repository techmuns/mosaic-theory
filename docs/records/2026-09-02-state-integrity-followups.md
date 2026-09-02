---
id:
status: open
date: 2026-09-02
prs: []
supersedes:
superseded-by:
---

# Three STATE.md integrity follow-ups, sized and scheduled — deliberately not built here

*Opened at the end of the session that produced them, and left unbuilt on purpose. The work that
generated these is finished: the driver is falsified and closed with a live monitor, the parent's
denominator is cleared, the 357 stands, the tooling is merged. **The risk now is not error, it is the
instrumentation becoming the work.** Each item is sized so it can be scheduled against real
priorities rather than run off the back of the session that noticed it.*

## 1 — The #443 shape has no guard, and it fired twice in one session (§5.0 row 17)

**What.** Twice on 2026-09-02, `main` advanced into the §5.0 lines a branch was rewriting. The second
time, the resolution that takes the branch side wholesale **deleted #569's row 16 and passed
`test_state_open_now`, `test_state_identifiers` and `test_records_ledger`.**

**Why it passes.** Those guards verify **internal consistency**. A smaller self-consistent file is
indistinguishable from a correct one — CLAUDE.md says exactly this ("a dropped entry leaves a smaller
file that is still internally consistent, so it passes") and treats it as unlintable, which is why
the re-check is a human step. It is lintable, just not from one file: it needs **two revisions**.

**Guard.** Diff §5.0 rows against the **merge base** and fail on any row present in either parent and
absent from the result **without a close marker**.

**Size: ~half a day, gated on one design ruling** — what marks a legitimate close. A commit-message
token, a struck-through row kept in place, or an explicit deleted-rows manifest. The guard is
straightforward once that is chosen; choosing it is the actual decision. It needs the merge base, so
it is a CI workflow step or a test that shells to git.

**Schedule: before the next STATE-touching PR.** This is the only one of the three actively losing
data — both firings were caught by a human read, and a read is not guaranteed.

## 2 — §5.0 row numbers are load-bearing citations with nothing protecting them (§5.0 row 18)

**What.** 17 citations repo-wide point at `§5.0 row <n>`. `test_state_identifiers.py` lints
`S<n>`/`D<n>` tokens and **not** these. This PR broke such a pointer twice and repaired it twice.

**Why it is now worse than cosmetic.** The **gap at row 15 is load-bearing on two independent
claims**: the ORCL record's appended repair asserts "no row 15 exists", and #569's own record cites
row 16. Anyone tidying the numbering falsifies both — and tidying a numeric gap is exactly the kind
of thing a future build does without thinking. It is held together by convention alone.

**Fix: position-independent citation** — a stable per-row id, cited instead of the position. Linting
`§5.0 row <n>` is a **detector**, not the fix; it would have caught the breakage after the fact
rather than made it impossible.

**Size: ~1 session** — scheme, migration of the 17 existing citations, lint.

**Schedule: after item 1.** Item 1 stops data loss; this one stops confusion. **Interim risk
accepted:** the gap holds by convention until this lands.

## 3 — Every count states its boundary (§5.0 row 19)

**What.** Four errors in one session were **one error**: a count taken at a boundary that was never
stated.

| the count | the boundary that was wrong |
|---|---|
| AES/ETN "silent recall loss" | a 400-day probe of a **290-day** scan |
| "1,910 cache entries written during the run" | the **whole calendar day** — off 3.4x; true figure 560 of 591 |
| day-total "623" | matched **neither** counting convention (626 raw, 560 excluding one term) |
| prefilter yield "against 357" | 357 is a **downstream stage**, not the graded population |

All four survived reasoning review, **including the operator's** — they are invisible without
re-running the count. The third landed inside the record documenting the first two.

**Fix: one line in CLAUDE.md** — any count entering a record, a commit message or STATE.md states its
boundary: window, filter, population, unit.

**Size: ~10 minutes.** **Schedule: with the next CLAUDE.md touch.** It is a discipline rather than
machinery, so it gains nothing from being rushed and loses nothing by waiting for a natural edit.

## Note on where these came from

None of the five errors was caught by the author or by the operator's sign-off. All were caught by
the **independent pre-merge read** re-deriving the numbers. Recorded because it says what that read is
for: it is not a second opinion on the argument, it is the only step that recomputes. Weight
accordingly — an approval clears the reasoning, never the arithmetic.
