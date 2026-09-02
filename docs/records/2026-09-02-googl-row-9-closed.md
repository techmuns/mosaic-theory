---
id:
status: recorded
date: 2026-09-02
prs: []
supersedes:
superseded-by:
---

# §5.0 row 9 closed — GOOGL is confirmed; its two axis methods are not, and carry forward

**IDENTITY AND OUTCOME**, as the delete-on-close rule requires. §5.0 **row 9** — *"GOOGL's R3 record
is written and its gate is FAIL — the verdict is the operator's"* — is **CLOSED**. The verdict was
recorded **confirmed on 2026-09-01** and merged as **#567**. The row is deleted.

## What was actually decided

| | ratio / bar | IRR / floor | gate | status | spot |
|---|---|---|---|---|---|
| `scenarios/GOOGL.json` (**live**) | **2.4299x** / 2.0 | **17.11%** / 15% | **PASS** | **confirmed** | $339.35 (31 Aug) |
| `scenarios/archive/GOOGL-2026-08-17.json` | 1.6920x / 2.0 | 14.89% / 15% | FAIL | pending_analyst | $345.90 (14 Aug) |

Both readings stay on the record, linked in both directions — that is what the operator ruled.

**The nuance the table flattens, in the operator's own words:** *"The improvement comes from the price
falling, not from anything changing in the business, and the ratio is sensitive to that: risk is thin,
so it leaves the preferred band above $342.77 and stops being eligible above $345.26. I am confirming
the position on that basis, with the entry unchanged at $345.90."*

So the ledger entry is **$345.90** and `verdict.ratio_at_entry` is **1.6919956** — the *failing*
number. The position is confirmed on the 31 Aug reading while entered at the 14 Aug price. ### The gate is read at a different date than the entry, and the two disagree

Stated plainly, because it is the boundary error in its most expensive form — a claim about a **live
position**, not a commit message:

| read at | ratio | IRR | gate |
|---|---|---|---|
| **entry**, $345.90 (14 Aug) | **1.6920x** — below both the 2.0 bar and the 1.75 eligibility line | **14.89%** — below the 15% floor | **FAIL** |
| **confirmation**, $339.35 (31 Aug) | **2.4299x** | **17.11%** | **PASS** |

**The gate status is a function of the current quote, not a property of the position.** The operator's
own rationale bounds it: the record leaves the preferred band above **$342.77** and stops being
eligible above **$345.26** — and the entry sits at **$345.90**, above both. So at the price actually
paid, this position does not clear its own eligibility line; it clears at a lower quote recorded two
weeks later.

That compounds with how thin the IRR margin is: 14.89% against a 15% floor is 0.11pp, so the same
legs cross the return gate on a small move in the quote. Nothing here is wrong — both readings are on
the record, linked, and the operator confirmed on a stated basis. What is wrong is saying **"GOOGL
passes"** without a date attached: it is true of the live record and false at the entry, and this
session conflated exactly that once already.

## Why STATE.md carried the wrong figures until now

**#567 confirmed and reissued GOOGL without touching STATE.md.** Row 9 therefore cited
`scenarios/GOOGL.json` **by name** while quoting the archive's numbers, and §2's "R3 reached the
sanctioned create path" bullet repeated them. A merged build changed reality and left the snapshot
stating the opposite — the failure CLAUDE.md's session ritual exists to prevent, and the direct cause
of a false claim in `docs/records/2026-09-02-irr-total-return-already-ruled.md`, corrected there.

Both sites are fixed in this change: row 9 is gone, and the §2 bullet now labels 1.692x/14.89% as the
**archive** and states the live 2.4299x/17.11%/PASS beside it.

## What row 9 also held, and does NOT close with it

Row 9 bundled **three** operator to-dos. The verdict was one of them.

1. **confirm/override** — **CLOSED**, confirmed 2026-09-01.
2. **"ratify or restate the two axis methods"** — **STILL OPEN.** `assumptions.earnings.ratified` and
   `assumptions.multiple.ratified` are both `None`, with `ratified_by = None`. **Confirming a verdict
   is not ratifying a method**; they are separate acts. Carried forward as **§5.0 row 20** rather than
   deleted with the row that happened to contain it.
3. **"confirm the re-tag stands"** (`anchor.recipe_hint` moved R1 → R3 by hand on 2026-09-01) —
   **settled in fact**: the live dossier carries `recipe_hint: R3_forward_pe`, and the confirmation was
   recorded against the reissued R3 record. Not carried forward.

**Why item 2 is not a formality.** The record calls the 20.5x bear multiple *"the SINGLE BINDING
ASSUMPTION of this underwrite"* — the entire downside is a de-rating rather than an earnings fall,
since bear EPS exceeds today's NTM. The record also states the company's own P/NTM quartiles are a
**LIMITED** basis match and therefore context, not load-bearing. An unratified method under a
confirmed position is the gap worth keeping visible.

## Citation coverage

Two citations point at row 9. **`docs/records/2026-09-01-r3-reaches-the-create-path.md:87`** — this
record is its closure statement, and row 20 carries the surviving half. **STATE.md row 4 itself** read
*"GOOGL is the first record — row 9"*, an IN-SNAPSHOT pointer into a row this change deletes;
repointed here to this record.

*The first draft of this section audited `docs/records/` only and missed the STATE.md one — the same
narrowed population that produced the "21 citations repo-wide" error earlier today. Nothing guards
it: `test_state_identifiers.py` matches `S<n>`/`D<n>` tokens, not §5.0 "row N", so a green suite is
not evidence here.*
`docs/records/2026-09-02-irr-total-return-already-ruled.md:60` flagged the staleness that this change
resolves.

## Also closed here — §5.0 row 19 (every count states its boundary)

Row 19's own schedule read *"with the next CLAUDE.md / template touch"*. **This is one**, so the
trigger is honoured rather than left to fire unwatched — the failure mode argued about one row above.

Shipped, ~10 minutes as sized:

- **`docs/records/TEMPLATE.md` gains a `BOUNDARY` field** — window, filter, population, unit, and the
  commit or date measured at, for every count in the record. *A rule you must remember is weaker than
  a field you must fill*, which is why the field is the fix and the CLAUDE.md line is only its
  statement of principle.
- **CLAUDE.md** carries that principle, scoped deliberately to counts entering a record, a commit
  message or STATE.md — **not** conversational arithmetic that lands nowhere.

**Row 19 deleted.** Its evidence is the session that produced it: seven instances of one error, the
last of which — *"GOOGL is the only scenario with an unratified multiple"* — was caught by the
pre-merge read **inside this very PR**, in the row closing a defect about an unchecked claim. Five of
the nine live records carry an unratified multiple; GOOGL is the only **confirmed** one.
