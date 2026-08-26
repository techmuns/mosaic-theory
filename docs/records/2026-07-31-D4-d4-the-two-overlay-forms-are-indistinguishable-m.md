---
id: D4
status: recorded
date: 2026-07-31
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
date-source: git (first commit containing this text)
---

**D4. THE TWO OVERLAY FORMS ARE INDISTINGUISHABLE — MEASURED, so the choice is not an analytic
question.** additive `basic_out + (dil_wa − basic_wa)` vs multiplicative
`basic_out × (dil_wa ÷ basic_wa)`, both legs taken from the SAME reported period: **widest spread
across the fleet is MVST at +0.033%; no name exceeds 0.1%.** The operator's expectation that they
diverge where the count has moved (SMPL buying back, MVST issuing) did NOT materialise, and the
algebra says why — the spread is the dilution delta times the fractional gap between outstanding
and the period's basic average, and that second term is ≤0.24% everywhere. **PICK: ADDITIVE**, on
robustness rather than fit — its assumption is stated in the units the instruments actually exist
in (a COUNT of options/RSUs), and it degrades safely where the multiplicative form divides by a
small or zero basic average. **BOTH LEGS MUST COME FROM ONE PERIOD** — two independent
`_latest_point` calls can straddle a quarter and a YTD span and the delta would then be nonsense.
