---
id: 
status: recorded
date: 2026-07-28
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-28 MATERIALITY GUARD (queue item 17, audit P1) — FIRST AUDIT-DERIVED
REMEDIATION. Shipped independently of item 1, as directed.** ROOT CAUSE IS DEEPER THAN THE AUDIT
STATED: it called this "no materiality guard between extraction and synthesis", but the line never
reaches the extraction OUTPUT either — `financial_summary_annual` builds from a HAND-NAMED row
list, so `Asset Writedown` is invisible to every downstream consumer and a guard scanning the
assembled table could never fire. Fixed in BOTH halves: (a) SURFACING — material unusual items now
enter the annual summary as DATA, from the sheet's own unusual-items block, appended only when
valued (a name with no one-offs stays byte-identical); (b) the GUARD — fail-loud when a material
one-off appears in NEITHER the summary NOR the synthesis (two satisfying routes: data or argument).
SCOPE NARROWED ON EVIDENCE, the load-bearing finding: **the audit's stated fix is not implementable
as written.** "Any income-statement line >10% mcap / 5% revenue" fires on TWELVE lines for SMPL —
`Cost Of Goods Sold` at 102% of market cap (recurring, structural on every name forever),
`Weighted Avg. Diluted Shares Out.` (a SHARE COUNT against dollars), and `Filing Date` +46,212 (an
Excel DATE SERIAL read as $M, 5082% of market cap). A guard that fires on the filing date is
switched off within a week, and then the real one never fires either. Scope is therefore the CIQ
UNUSUAL-ITEMS BLOCK, delimited by the sheet's OWN subtotals (`EBT Excl. Unusual Items` → `EBT Incl.
Unusual Items`) — right on the merits, being exactly the family "clean"/"normalized" figures
EXCLUDE, i.e. what a reader on normalized earnings never meets; SMPL's bear case was already
arguing inside this family with the wrong member. NOT P9's defect (that inferred a FILING fact from
sheet shape; this reads a sheet's labelled subtotals to locate rows within it), and a missing
delimiter RAISES rather than reporting a clean pass. Present on all 12 committed bundles (3–8
rows). **REAL-RUN RESULT ACROSS THE COHORT: fires on exactly 2 of 11, zero false positives** —
SMPL `Asset Writedown` −$391.9M (43% of mcap, the audited defect) and **CNXC `Impairment of
Goodwill` −$1,523.3M (103% of market cap) — A PREVIOUSLY UNKNOWN SECOND INSTANCE nobody had looked
at**, in neither its summary nor its synthesis. ACCEPTANCE (operator policy 2026-07-28): the
fixture ERRORS on `2facc5e` (`ModuleNotFoundError: vinci.dossier.materiality`) and passes here —
red→green demonstrated, not asserted. 8 pins: the audited shape raises · the audit's own
11%-of-mcap test · either satisfying route silences it · the twelve-false-fire negative pin naming
COGS/share-count/date-serial · a sheet without the block refuses a clean pass · no-denominator is a
documented silent pass · every committed bundle has a locatable block · e2e conditional invariant.
Gate: ruff + `mypy --strict` clean · **1123 passed** (+8). NOT DONE HERE: SMPL/CNXC still carry the
pre-guard render — they re-assemble under item 16b's acceptance conditions once 18 and 1 land, and
this guard is what holds that re-assembly honest.
