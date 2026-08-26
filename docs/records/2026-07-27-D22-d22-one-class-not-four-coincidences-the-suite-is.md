---
id: D22
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**D22. ONE CLASS, NOT FOUR COINCIDENCES: THE SUITE IS UNVERIFIED EVIDENCE.**
(2026-08-01, after the fourth instance in one week.)

Production is mutation-tested — every guard this week was proved able to go RED. **The suite itself
is not.** Mutation testing proves a test CAN fail; **it never proves the test would fail on the
defect that actually occurs.** All four instances are that one gap, and their surface differences
are what made them look like four problems:

| # | what the test did | face |
|---|---|---|
| #280 | fixture raised on a cache entry aged past TTL — a hole in the fixture, not the code | false RED |
| #294 | the pin asserted on CALL TEXT, so a legitimate rename reddened it | false RED |
| #302 | the hygiene guard's regex was narrower than its own comment claimed; it ran green over **six live violations in STATE.md** | false GREEN |
| #305 | the fixture was a duck-typed stub, and its shape DICTATED the production signature (`getattr(f, "value", None)`) | the test **caused** the defect |

**WHY IT IS ONE CLASS.** In each, the test was trusted as evidence ABOUT production while nothing
checked the test against reality. #302 is the purest form: its mutation PASSED because the mutation
used a shape the guard already knew — a self-consistent instrument agreeing with itself while the
corpus it was pointed at held six violations. #305 is the sharpest: the fixture did not merely fail
to catch the defect, it SUPPLIED it.

**THE COUNTER-MEASURE ALREADY EXISTS AND IS APPLIED INCONSISTENTLY** (operator, 2026-08-01):
*"run any new check against the existing corpus, not only a synthetic mutation — a new check finding
nothing in a large corpus is suspicious, not reassuring."* Applied in #303 it immediately caught two
things a synthetic never would: the `ensure_ascii` mangling that a parsed-dict compare called
identical, and the 1.2 archive record that the version-scoping pin had never walked.

**THE RULE, THREE PARTS:**
1. **CORPUS BEFORE SYNTHETIC.** Every new check runs against the live committed corpus before it is
   believed. A check that finds nothing there is suspect until you have shown it CAN find something.
2. **MUTATE WITH A SHAPE THE INSTRUMENT DOES NOT ALREADY KNOW.** A mutation drawn from the guard's
   own pattern list tests the list, not the guard.
3. **FIXTURES ARE BUILT FROM THE REAL TYPE.** Never a hand-rolled stub with the attributes the test
   happens to need — that is how a fixture's shape becomes a production signature.

**NOT SHIPPED AS A MACHINE CHECK, and that is the accepted risk**: parts 1–3 are review discipline,
not lintable. The INVARIANT RULE is satisfied by recording it here as consciously accepted, with the
four instances as the evidence that the discipline is what fails, not the tooling.
