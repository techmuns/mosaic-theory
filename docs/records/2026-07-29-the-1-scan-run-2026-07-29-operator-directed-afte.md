---
id: 
status: recorded
date: 2026-07-29
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**THE `[-1]` SCAN — RUN 2026-07-29 (operator-directed, after the trap appeared a THIRD time, that
time in the diagnostic written by whoever had just fixed the other two). RESULT: CLEAN, no fourth
production instance — and the operator records the prediction as WRONG, alongside the mechanism
errors.** 76 `[-1]` sites in production; **21 index a series**; all 21 correct, by THREE distinct
mechanisms: (i) NAMED-OR-GUARDED — the caller refuses when the latest cell is absent, so `[-1]` is
provably the latest (`pe_ltm_current`, `ev_ebitda_percentile`, `fy_cols`); (ii) THE DATE TRAVELS —
the own-history band takes the last SURVIVING pair but stamps that value's own as-of, which is
exactly why the band may and the P/LTM tail may not (the distinction was already written into item
20's own comment); (iii) CORRECT BY THE EXPORT'S SHAPE — true only because CIQ happens to order
columns a particular way, with nothing asserting it.
**(iii) IS THE FINDING, and it was worth more than a fourth instance would have been.** Two sites:
**capital structure** `vcols[-1]`, which stamps `"(latest quarter)"` — a provenance CLAIM on an
unasserted convention → **ASSERTION SHIPPED** (`_cs_col_date` + refuse-on-descending, pinned
positive AND negative); and the **materiality period fallback** `periods[-1]`, doubly protected
(never fires — all 12 bundles carry LTM — and that sheet carries no estimate columns even if it
did) → **comment, not assertion**, per the operator.
**THE DURABLE OUTPUT IS THE RULE**, now in docs/engineering.md: *`[-1]` on a series is safe iff the
element is guaranteed to be the one you mean, OR the value's own date travels with it.* It would
have prevented all three instances.
**SCOPE DISCIPLINE ADOPTED (operator, from this result): FINISH THE KNOWN QUEUE; DO NOT GO LOOKING
FOR CLASSES ON SPEC.** Twenty-one sites correct by three distinct mechanisms is a codebase being
careful, which is evidence the original nine were SPECIFIC GAPS rather than symptoms of general
looseness. Run a scan when it is cheap AND motivated by a live recurrence; not on a hunch.

**ITEM 21's REVIEW BASIS — STATED, because the previous message was ambiguous about it
(operator 2026-07-29).** 21 changes EXTRACTED VALUES, so it needs a **REAL SHOWN RUN as its own
evidence** — the decision-path rule — **NOT operator approval**. It ships on that run unless the
run surprises. The two that need the operator are **28 and 22**, both RENDER changes, which the
PREVIEW RULE gates: preview from committed JSON, then STOP. The operator's mechanical list was
wrong on those two and is corrected here.
