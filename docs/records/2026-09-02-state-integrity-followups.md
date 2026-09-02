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

**RULED 2026-09-02 (operator).** A close is legitimate when **a record exists naming the row's
identity and its outcome** — closed / falsified / superseded — and **the guard checks for that
record**, not for a marker in the diff. *Evidence of closure must live outside the file being
edited*: an in-diff marker is exactly what the #443 shape defeats, since the same edit that drops a
row can supply its own excuse.

It falls out cleanly on the two live cases: **#569's row, deleted with no such record → fails**;
**row 13 and the prefilter row, deleted by PRs that wrote their closing records → pass**.
Delete-on-close keeps working and the silent path closes.

**Coupling, caught at ruling time:** the rule names rows by **identity**, so it presumes item 2.
**Until stable ids exist the guard must match on row CONTENT, never on number** — otherwise it
inherits the mutable-numbering problem it exists to prevent, and a renumber reads as a delete.

**Size: ~half a day, no longer gated.** It needs the merge base, so it is a CI workflow step or a
test that shells to git.

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

**Schedule: after item 1.** Item 1 stops data loss; this one stops confusion.

**Interim risk, weighted above "accepted".** A numeric gap is what a future build tidies without
thinking, and this one is load-bearing on two live claims. Mitigation shipped now rather than
deferred: a note directly under the §5.0 table says why row 15 is empty and warns against closing it.
That does not fix the dependency — it turns a **silent** falsification into a **visible** one, which
is the most a convention can buy until stable ids land. (Placed *under* the table, not inside it: a
non-table line inside a markdown table terminates its rendering, and the line-count guards are blind
to that — a defect this session already shipped once.)

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

**Fix: put it where counts get WRITTEN, not only in CLAUDE.md.** A **boundary field** in
`docs/records/TEMPLATE.md` (and the PR/commit shape) stating window, filter, population and unit.
**A rule you must remember is weaker than a field you must fill.** The CLAUDE.md line stays as the
statement of principle; the field is what enforces it at the moment the number is written.

**Size: ~10 minutes.** **Schedule: with the next CLAUDE.md / template touch.** It is discipline plus
one template field, so it gains nothing from being rushed and loses nothing by waiting for a natural
edit.

**Scope it deliberately:** counts entering a **record, a commit message or STATE.md**. Not
conversational arithmetic that never lands anywhere — re-deriving that slows the channel for no
gain.

## Note on where these came from

None of the five errors was caught by the author or by the operator's sign-off. All were caught by
the **independent pre-merge read** re-deriving the numbers. Recorded because it says what that read is
for: it is not a second opinion on the argument, it is the only step that recomputes. Weight
accordingly — an approval clears the reasoning, never the arithmetic.
