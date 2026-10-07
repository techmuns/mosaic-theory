---
id: 2026-10-07-amzn-re-tagged-r3
status: shipped
date: 2026-10-07
prs: [672]
supersedes:
superseded-by:
---

# AMZN is re-tagged R3 — the next R3 name after GOOGL, and a rebuild now keeps it

**WHAT.** AMZN's anchor `recipe_hint` is set by hand to `R3_forward_pe` (EPS × forward P/E, an
equity basis), with an operator reason. The reason is drafted from the two flags the page already
carries on R1's inputs:
- the LTM operating margin (12.1%) sits 6.8 points above the 10-FY median that R1 reverts to (5.3%);
- the consensus EBITDA row adds back 3.14× the D&A in the actuals (`financial_summary.ebitda_basis`).

`anchor.py` already records AMZN as the case where R1 lands near the price "because two stale
inputs offset". The diff is two lines (`recipe_hint`, `reason`). Every computed value is the
machine's R1 arithmetic, left untouched. Pages are re-rendered and mirrored; no LLM ran.

**WHY.** Operator instruction, 2026-10-07: re-tag AMZN to R3. It follows the review of the analyst
team's scenario feedback, which found the R1 anchor unfit as a scenario input. #670 is what lets the
tag stand: before it, the next re-assembly would have erased it, as it did all four hand re-tags on
record.

**WHAT IT MOVES, measured.**
- **The scenario gate accepts an R3 record on AMZN** (`check_tier_agreement`). It refused one before.
- **A rebuild keeps the tag.** With the machine's own R1 proposal handed to the write path, the
  written recipe stays `R3_forward_pe`, and the page carries a caveat naming both.

**FOR WHOEVER WRITES THE R3 RECORD.** Measured 2026-10-07, not acted on here:
- **CIQ's displayed NTM P/E is struck on GAAP EPS.** It is 27.26x at $256.29 (`Estimates→Multiples`),
  which implies an EPS of 9.4026 — the GAAP FQ3'26–FQ2'27 sum (9.39), not the normalized one (9.10,
  which would give 28.2x). GOOGL's R3 anchored on *normalized* P/NTM, so the basis must be stated,
  not copied.
- **The `Financials→Multiples` P/NTM EPS history implies 9.20 at the 09-16 close ($245.96).** That
  matches neither basis — the `BASIS MATCH: LIMITED` concern of 2026-09-03, measured on this name.
  It corroborates at most.
- **FY26 normalized EPS rests on 4 analysts still in consensus** (Revisions, last month), against 49
  for GAAP. FY27 normalized has 28.
- **`scenario-propose` still hardcodes `multiple_basis: "EV/EBITDA"`** (§5.0 row 10). The template
  needs that one hand-correction; its `recipe_id` now reads R3 from this tag.

**HOW VERIFIED.**
- The bytes before the anchor block were asserted unchanged.
- The page shows the method as `R3_forward_pe` with the reason, and the mirror is byte-identical.
- The gate and rebuild checks are above.
- Full offline suite on this branch: counts in the PR.

**BOUNDARY.**
- AMZN's committed dossier on main @`6b42cd32`.
- The CIQ Estimates export, dated 2026-10-06 or later, and the Financials export, 2026-09-17.
- The 09-16 close is from the local price store.
- "0 flips": AMZN's R1 `applicable` across its 9 committed anchor versions.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The `applicable` coupling (§5.0 row 10) applies to AMZN now.** The gate refuses an R3 record
  whenever a build finds R1's inputs incomplete. AMZN's R1 `applicable` has been True on all 9
  committed versions (0 flips), so the risk is lower than GOOGL's (3 of 8).
- **The reason is drafted from the page's own flags, not from an IC memo.** It records why R1 does
  not fit; the R3 underwrite's own method is still to be written.
