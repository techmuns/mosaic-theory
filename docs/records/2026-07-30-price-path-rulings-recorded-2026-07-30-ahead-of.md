---
id: 
status: recorded
date: 2026-07-30
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**PRICE-PATH RULINGS — RECORDED 2026-07-30, ahead of the build (operator).** These were settled in
review and exist nowhere else; recording them is the first commit of the work, not its last.
1. **NO OFFSET ON THE SHARES COLUMN.** A price's vintage is a CLOSE, a share count's is a FILING.
   The vintage field takes the filing date or says UNKNOWN — it never inherits the CIQ export stamp.
   **FUBO is the proof:** CIQ's 29.4M against our 342.4M differ by a *filing*, not a day, so no
   export-date correction could reconcile them. (Rule in docs/engineering.md: *a stamp belongs to a
   COLUMN, not a block*.)
2. **THE STORE REFUSAL KEYS ON AGE, NOT ON TODAY.** Refuse on no price at all, or a price past the
   ceiling — never on "no bar for today", or every run before the US close refuses. Assembly here
   runs in Indian daytime against a prior-session close; that is the normal case, not a failure.
3. **CIQ STAYS OUT OF PRICE SELECTION.** Its comps price is on-disk and often fresher, but using it
   would give our derived cap and CIQ's cap a shared input and the comparison would stop testing
   price vintage at all — the independence rule, one turn after recording it. **CIQ becomes a
   staleness MONITOR instead (operator, better than the original ruling): if CIQ's dated close is
   NEWER than the store's latest bar, flag that the store needs refreshing — never take the value.**
   Comparing dates is not coupling.
4. **ITEM 24'S BLOCKING EVIDENCE IS IN HAND.** CIQ's `Shares Outstanding Latest` independently
   confirms our `shares_out` on **10 of 11 names within 0.1%** (ratios 0.9993–1.0011), FUBO the sole
   exception at 11.65×. That is the multi-name study item 24 was waiting on. CAVEAT TO CARRY: CIQ's
   count is printed to 0.1M granularity, so it is a CROSS-CHECK, never an authoritative source.
   **AMENDED 2026-07-31 (operator) — THIS EVIDENCE COVERS THE WRONG FIELD.** It validates
   `shares_out`, the BASIC cover-page count. The denominator item 24 moves TO is the DILUTED count,
   which this study never touched; the diluted field's own cross-check is D2 above (7 of 7 against
   the machine extraction), and it is that check which surfaced D3. FUBO's 11.65× is not an
   outlier to be carried as unexplained either — D6 gives its cause.
5. **TWO SOURCES HAVE NO FRESHNESS MEASUREMENT AT ALL** — the **price store** and the **Financials
   workbook**. Everything else carries an as-of. IT's 6% divergence was not a code defect: it was
   the refresh command not having been run, and nothing measures that. Until a guard exists,
   "fix the cadence" is a habit rather than a contract.
