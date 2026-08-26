---
id: S10
status: recorded
date: 2026-07-31
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S10. BATCH A — THE TWO RECOVERABLE VINTAGE STAMPS (2026-07-31).** From the enumeration of every
stamp that can differ from its value's vintage, these two had a vintage the code still held:
1. **P/E and its percentile** stamped `reference_date` while the EPS behind them is an annual period
   typically ~210d old (bounded at 470 by #298). A P/E is price ÷ earnings and its two COLUMNS have
   different vintages; the run-date stamp named the fresher one and hid the older. Now stamped with
   the EPS `period_end`, with a note giving the age and filing date. `annual_eps_point_as_of`
   returns the point; `annual_eps_as_of` delegates to it — ONE selection, two views.
2. **`high_52w`/`low_52w`** stamped with the last bar while each is a MAX OVER 365 DAYS. The window
   is now labelled beside the value. `window_facts` gained `anchor_before` rather than a second
   implementation: a RETURN needs a start price so it anchors at/before the window start, an
   EXTREMUM is a max over the bars INSIDE it — the two differ by exactly one bar, which is a flag on
   one function, not a fork (#294's rule, and this class recurs on the fix after it).

**NO VALUE MOVED — and no PAGE changed either.** Re-rendering all eleven dossiers from committed
JSON moved one file, FUBO, and its diff is entirely schema-default backfill (`material`,
`filed: null`, `extraction_version: null`) — the same class as MVST's 79 keys, not this batch. It
was reverted. **The labels reach the JSON but not the rendered page:** the dossier's P/E is
CIQ-sourced (confirmed a fourth time), and `render.py:2207` prints the 52-week range as values only,
never the note. `_sourced` does carry the note into `Sourced.note`, so a RE-ASSEMBLY would land it in
the machine-complete tier. Under the three-tier rule that is the right tier; it is reported plainly
rather than claimed as a page improvement.

**REVIEW FINDINGS ON BATCH A.** (a) The stamp change is SAFE downstream — both consumers of
`fundamentals.pe` (`mechanical.py:778, 869`) read `.value`/`.is_known` and never `.as_of`, so moving
the stamp from the run date to the EPS period trips no staleness gate. (b) The first cut branched on
the VALUE and needed `assert cur_pt is not None` to satisfy the type — a bare assert in a production
path, which `python -O` STRIPS, turning a loud explained refusal into an AttributeError. Branching
on the POINT narrows naturally; pinned by an AST scan so a reintroduced assert is caught anywhere in
the function. **`features.py:333` carries the same bare assert from #294 — flagged, not fixed here,
to hold Batch A's scope.**

**STILL OPEN — Batches B and C.** B: `shares_outstanding_by_cik` merges five quarterly frames into a
flat dict and DISCARDS which frame supplied each CIK, so the universe cap's 120–485d age is not
recoverable without changing that reader (three other callers). C: `RefPoint.vintage` SHIPPED (S15) but binds
forward only — the 70 unstamped committed references need analyst source material, so **P3 pt1 remains
OPEN and does not close on code**. `ScenarioRecord.spot` is still a bare float — **P4 pt2 remains OPEN**.
