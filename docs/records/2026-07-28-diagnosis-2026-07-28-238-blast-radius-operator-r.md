---
id: 
status: recorded
date: 2026-07-28
prs: [238]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**DIAGNOSIS — 2026-07-28 #238 BLAST RADIUS (operator-required before any re-assembly).** Four
questions, all answered by real runs across the twelve bundles.
(1) **GREEN PATH IS DETERMINISTIC — the LLM is NOT in the loop.** The guard is satisfied by EITHER
route, and the SURFACING half is mechanical (reads the sheet's own block, appends), so by the time
the guard runs the summary already carries the row. PROVEN by running the guard with an **EMPTY
synthesis string** against the real post-surfacing table for both firing names: SMPL and CNXC both
pass. No intermittent failure on model variance, and no name that can never build. Pinned
(`test_the_green_path_is_deterministic_and_does_not_involve_the_llm`) so a change making the
summary route conditional reddens BEFORE anyone meets it as a stuck build. **CNXC's item-16c
re-assembly is therefore UNBLOCKED on this ground.**
(2) **ROW-SET DIFF, pre vs post, real code both sides: 11 of 12 names gain rows; 56 rows fleet-wide.**
Gains: EPAM/IT +4, CNXC/WERN +3, BRBR/SMPL +2, AORT/MVST/NCNO/VITL/VRRM +1, **FUBO +0** (no
unusual items — byte-identical, as designed). So the blast radius is far wider than the two names
above the 10% floor: MVST's −36.6, VRRM's −1.3, BRBR's −0.9 and the rest all now surface.
(3) **POSITIONAL-INDEXING REGRESSION: none — but the risk was real.** The insert sits BEFORE the
cash-flow block, so **CFO/Capex/FCF shift position on 11 of 12 names**. Safe only because every
consumer selects BY LABEL: `audit_r1._fy_margins` uses `startswith("Revenue ($M)")`, render's FCF
relabel matches `r.label == "FCF ($M)"`, and both twins' brief snapshots filter on an explicit
label WHITELIST. The only `rows[0]` reads in the tree are the catalyst calendar, a different
structure. PINNED (`test_no_consumer_reads_the_annual_table_by_row_position`) — the row-wise form
of ciq.py's never-hard-code-column-positions rule; mutation-tested. CONSEQUENCE WORTH THE
OPERATOR'S ATTENTION: because both brief snapshots whitelist, **the surfaced writedown lands in the
APPENDIX, not the brief** — the record is complete and the guard is satisfied, but a brief-only
reader still does not meet a 43%-of-market-cap charge. Whether P1-scale items belong in the brief
is a DESIGN decision, not a defect, and is not taken here.
(4) **FLEET DIVERGENCE IS REAL AND UNMARKED.** Every committed dossier predates the guard; after
any single re-assembly we hold two extraction vintages with nothing distinguishing them, which
breaks cross-name comparison exactly where it matters most (the verdict-pending cohort). NOT FIXED
HERE — the operator's two options stand: stamp each dossier with an extraction version, or plan a
single fleet re-assembly once the guard is proven green. **Recommendation: the version stamp, and
FIRST** — it is cheap, it makes the divergence legible while it exists, and a fleet re-assembly
without it cannot even be verified complete. Queued as item 26.
