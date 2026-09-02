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
while the **`ai-compute-platform` card row (closed by #572)** and the **prefilter-recall row (closed
by #576)**, both deleted by PRs that wrote their closing records, **→ pass**. Delete-on-close keeps
working and the silent path closes.

> **Named by identity, not by number — and the first draft of this record got it wrong.** It said
> "row 13". The card row was row 13 *only on #572's branch*; on `main` row 13 is a different,
> still-open item (the UNIT-unchecked accepted risk). A number stated at the feature-branch boundary
> and read in the post-merge file — the exact defect item 3 exists to stop, committed into the record
> arguing for it.

**Coupling, caught at ruling time:** the rule names rows by **identity**, so it presumes item 2.
**Until stable ids exist the guard must match on row CONTENT, never on number** — otherwise it
inherits the mutable-numbering problem it exists to prevent, and a renumber reads as a delete.

**Size: ~half a day, no longer gated.** It needs the merge base, so it is a CI workflow step or a
test that shells to git.

**Schedule: before the next STATE-touching PR.** This is the only one of the three actively losing
data — both firings were caught by a human read, and a read is not guaranteed.

## 2 — §5.0 row numbers are load-bearing citations with nothing protecting them (§5.0 row 18)

**All figures below are AS OF THIS COMMIT, over a stated population: every git-tracked file,
including STATE.md.** Every figure moved while this section was being written — `main` advanced under
it three times — and three successive drafts were each wrong at their own boundary.

**What.** **22 citations across 17 files** point at `§5.0 row <n>`. `test_state_identifiers.py` lints
`S<n>`/`D<n>` tokens and **not** these.

**Four do not resolve — but three of the four are correct writing, not damage:**

| citation | what it actually is |
|---|---|
| `…drawdown-filing-index-unavailable.md:62` → row 16 | *"row 16 is STRUCK — the accepted risk it recorded is resolved"* — **#570's own closure evidence**, exactly what item 1's ruling demands |
| `…submissions-memo.md:131` → row 16 | *"row 16 is struck, the item being closed"* — an amendment **#570 wrote into #569's record**; also closure evidence |
| `…orcl-…-boundary.md:425` → row 15 | a deliberate gap, covered by an appended repair |
| `…submissions-memo.md:91` → row 16 | **the only genuinely stale pointer** — present tense — and #570 appended the repair below it |

**The real finding, which is stronger than the one the first draft made.** A `§5.0 row <n>` lint
**cannot distinguish a correct closing statement from a stale pointer**: both are a number with no
row behind it. Linting the pattern is not even a reliable *detector*, which is exactly why item 1's
guard keys on **records** rather than numbers.

> **Retraction.** An earlier draft of this section, and the commit message that shipped it, said
> #570 "left three pointers hanging, including its own" and made that the lead evidence. **That was
> wrong and it accused another PR of a defect that was compliance with the rule written one row
> above.** Two of the three are #570 recording a closure; the third is repaired by #570's own
> amendment. Items 1 and 2 were, briefly, contradicting each other — item 1 ruling that a record
> naming a row and its outcome *is* a legitimate close, item 2 counting two such records as damage.

A further **six** citations resolve to a row whose *meaning* has drifted (rows 6 and 7) — real rows,
wrong referents. Those are the silent kind and the reason the count of "broken" depends entirely on
what you mean by broken.

**Fix: position-independent citation** — a stable per-row id, cited instead of the position. Linting
`§5.0 row <n>` is a **detector**, not the fix; it would have caught the breakage after the fact
rather than made it impossible.

**Size: ~1 session** — scheme, migration of the **22** existing citations, lint, plus repair of the single genuinely stale pointer.

**Schedule: after item 1.** Item 1 stops data loss; this one stops confusion.

**Interim risk, weighted above "accepted".** A numeric gap is what a future build tidies without
thinking, and there are now **two** gaps (15 and 16) carrying four citations between them.
Mitigation shipped rather than deferred: a note under the §5.0 table names both gaps, says why each
exists, and warns against renumbering **any** row. The reason is sharper than "the note would go
stale": **closing the 15/16 gaps would renumber rows 17–19 and make four existing citations resolve
to the WRONG rows** — converting visibly-broken pointers into silently-wrong ones, which is strictly
worse than the present state.

(Placed *under* the table, not inside it: a non-table line inside a markdown table terminates its
rendering and the line-count guards are blind to that — a defect this session already shipped once.)


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
