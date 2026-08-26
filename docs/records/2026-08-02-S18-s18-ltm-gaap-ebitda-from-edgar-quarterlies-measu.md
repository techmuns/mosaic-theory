---
id: S18
status: shipped
date: 2026-08-02
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
date-source: git (first commit containing this text)
---

**S18. LTM GAAP EBITDA FROM EDGAR QUARTERLIES — MEASURED, NOT BUILT. COVERAGE 2 of 1,780 (0.1%),
AND THE CAUSE IS STRUCTURAL (2026-08-01).**

**THE GATE FAILED, so nothing was built.** Across the 1,780 names in the 2026-07-29 universe, the
number that can assemble FOUR CONSECUTIVE trailing quarters of operating income AND D&A is **2**.
Window-end spread is meaningless at n=2 (all 2026-03-31). A basis covering 0.1% is not a
cross-sectional basis, and item 3's rule — report and stop below what a cohort table needs — binds.

**THE CAUSE, from a known-answer read rather than the aggregate: US FILERS DO NOT TAG A DISCRETE
Q4, AND MOST TAG D&A ONLY YTD.** Both verified directly:
- **D&A is tagged once per year, always the same quarter.** SMPL's discrete-quarter `dep_amort`
  periods are 2025-11-29, 2024-11-30, 2023-11-25, 2022-11-26, 2017-11-25 — its fiscal Q1, every
  year, and nothing else. BRBR's are 2025-12-31, 2024-12-31, 2023-12-31, 2022-12-31, 2021-12-31,
  2020-12-31 — its Dec quarter, every year. Four CONSECUTIVE quarters of D&A do not exist for
  either name at any point in their filing history.
- **Operating income has an annual hole where Q4 should be.** SMPL runs 2026-05-30, 2026-02-28,
  2025-11-29 and then jumps to 2025-05-31 — the quarter ending ~2025-08-30 is its fiscal Q4, which
  the 10-K reports only as part of the full year. Every filer has this hole, every year.

Cause counts (population 1,780): `both:gap-in-quarters` **1,281** · `both:no-quarterly` **441** ·
`D&A:gap-in-quarters` 44 · `D&A:no-quarterly` 7 · `both:fewer-than-4` 4 · `opinc:no-quarterly` 1.

**THE MEASUREMENT WAS WRONG TWICE BEFORE IT WAS RIGHT, and the first way was D3.** Cut 1 pooled
YTD periods with discrete quarters — EDGAR tags 6-month and 9-month periods alongside 3-month ones,
a 6-month period never chains onto a 3-month one, and the result was 0.2% with 73%
`gap-in-quarters`. **That is the cumulative-vs-quarter defect (D3) committed inside the instrument
built to evaluate a new basis.** Cut 2 filtered to 80-100 day durations and returned 0.1% — still
unvalidated, still a number I could not defend. **Only cut 3 — printing the actual periods for two
names whose data I had already read — established that the failure is real and structural.**
D22 again: neither of the first two runs was checked against a case with a known answer, and the
implausibility of 0.2% is the only reason the first was not reported as a finding.

**THE CHAIN LOGIC WAS VALIDATED IN REVIEW — the positive control that cuts 1-3 never ran.**
Every earlier check tested whether the instrument REJECTED things; none tested whether it
could ACCEPT. On synthetic known-answer inputs: four clean consecutive quarters -> ACCEPTED;
three quarters -> rejected `fewer-than-4`; a hole in the middle (the real Q4 shape) ->
rejected `gap-in-quarters`; a duplicate `period_end` variant -> ACCEPTED, so the de-dup does
not manufacture a false negative. **Only with that control does 2-of-1,780 become a finding
rather than a fourth unvalidated number.** The two operator mutations are satisfied by the
same controls: a window shorter than four quarters is refused, and quarters that do not chain
are refused rather than silently mixed.

**THE PATH THAT WOULD WORK, NOT BUILT AND NOT PROPOSED AS QUEUED: YTD DIFFERENCING.**
Q4 = FY - 9M, Q3 = 9M - H1, Q2 = H1 - Q1. That reconstructs discrete quarters arithmetically from
what filers DO tag, and it is a materially different build from the one scoped here — it carries
restatement risk on every subtraction and a fiscal-boundary rule of its own. **The cohort table
therefore stays on EDGAR ANNUAL GAAP (S17), whose weakness is period and not convention.**

**ITEM 6 NEEDS ITS OWN PR** (stated, not built): bounding `latest_annual` by age changes behaviour
for every consumer of `ebitda_annual` fleet-wide — names currently resolving on a stale annual would
begin returning UNKNOWN — so the blast radius needs its own measurement, exactly as #298's EPS bound
was built solo.
