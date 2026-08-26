---
id: 
status: recorded
date: 2026-08-03
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**PIN THE BASIS, NOT JUST THE OUTPUT — GENERAL FORM, 2026-08-03 (operator).** Three instances now
where two values AGREED and no behavioural test could have caught the error: (1) #320's proposed
market-cap swap — both caps agree, so the substitution moved no number and the false stamp would
surface only on the first name where they diverged; (2) #321's fabricated blend — `stock_info.as_of`
vs the cap's real vintage, agreeing often enough to look right; (3) the R2 wedge above — an
operating margin compared to an EBITDA margin, where both are "margins" and neither the type system
nor any assertion notices. **THE RULE: when a value's BASIS is a choice, pin the choice — a
structural pin on the source, or an assertion that names the basis — because an output-level test
can only catch a basis error on the day the two bases happen to disagree.**
