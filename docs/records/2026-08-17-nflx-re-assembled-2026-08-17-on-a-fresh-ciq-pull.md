---
id: 
status: recorded
date: 2026-08-17
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**NFLX RE-ASSEMBLED 2026-08-17 ON A FRESH CIQ PULL (`artifacts/nflx-reassemble`) — AND THE
"3 DAYS OF LOOKAHEAD" I FIRST RECORDED HERE WAS FALSE. IT IS A STAMP BUG, NOT A DATA FACT.**
- **THE CORRECTION, PROVED BY ARITHMETIC.** NFLX's new cap is 325,453.5 stamped
  `market_cap_as_of 2026-08-17`. But 325,453.5 / 78.16 (the **2026-08-14** close) = 4,163.9M shares,
  and the PRIOR artifact's 308,714.5 / 74.14 (the 2026-08-07 close) = **the same 4,163.9M**. The cap
  is priced off the AS-OF's close. **No field carries future data.** `market_cap_as_of` publishes
  the CIQ **EXPORT** stamp as if it were the OBSERVATION date, and the previous artifact shows the
  identical offset (08-07 close stamped 08-10), so this **predates this assembly** entirely.
- **WHY THE FIRST ENTRY WAS WRONG, and it is the sharper lesson.** I measured "dates past the
  reference_date" and called them lookahead without asking WHAT EACH DATE LABELS. Nine fields
  carried a later date; ZERO carried later DATA. A date-comparison sweep cannot tell an export stamp
  from an observation — the same class as reading a display string for a value. The general claim in
  the first draft (pull-time stamps vs a data-bounded as-of) is **true about STAMPS and false about
  DATA**, and I applied it to the wrong one.
- **THE STATED UNLOCK COULD NEVER HAVE FIRED.** "Re-assemble after a close that reaches the panel
  date -> lookahead goes to 0" is unreachable: an export stamp is always ahead of the data it
  carries, so waiting cannot close it. A ledger entry with an impossible unlock is worse than none.
- **THIS RE-OPENS THE MVST FINDING.** MVST's recorded "1-day lookahead" is very likely the same
  stamp bug. The as-of item must be RE-MEASURED asking what each date LABELS before any of it is
  built — **do not size that build off the field counts recorded earlier in this file.**
- **THE REAL DEFECT, for its own CODE PR (never an artifact commit):** `mechanical.py` corrects the
  sibling `tev_as_of` through the export-vs-data helper and assigns `market_cap_as_of` RAW, so one
  panel renders two dates for one observation — `CMP $78.16 (2026-08-14) / cap $325.5B (2026-08-17)`
  — which is what `test_the_tev_cite_carries_both_dates_when_they_differ` exists to prevent. Same
  for the eight comps `source_ref` suffixes.
- **WHAT CHANGED, AND WHAT DID NOT:** `reference_date` 2026-08-12 -> 2026-08-14,
  `extraction_version` -> `2026-08-16.1` (NFLX is the FIRST artifact on it; the fleet is now
  legitimately split-vintage, 1 vs 13), synthesis re-rolled 6/6 -> 8/6. **`ev_ebitda` is 20.5 either
  side** — both Financials workbooks are still 2026-08-10, so multiples and own-history did not move
  and a Financials re-pull is still owed.
- **TWO DATA REGRESSIONS THIS PASS CARRIES, recorded rather than hand-patched:**
  (a) **GARTNER INC (CIK 0000749251 — the FOLLOWED name IT) lost `sic 8741` -> null.** `store.py`
  uses `INSERT OR REPLACE` and COALESCEs only `first_seen`, so a transient EDGAR submissions miss
  **permanently erases a known classification** (`unknown_sic` 28 -> 29 in the same run). A
  store-layer defect needing its own fix; hand-editing the derived snapshot would misreport what the
  pipeline produced.
  (b) **The fixture regeneration REWROTE HISTORY** — 1,174 insertions vs 1,156 deletions across 7
  files, so it is not additive: past-bar VOLUMES changed and `source` flipped `polygon-aggs` ->
  `polygon-grouped`. Volume drives the ADV gate (`below_adv_floor` 445 -> 447 in this same commit).
  The first draft said only "both fixtures regenerated", which hid it.
- **PROCESS NOTE (mine):** `vinci screen` COMPUTES a screen but does not persist a run snapshot, so
  it does not advance `_fleet_reference_date` — only the orchestrator (`run-weekly`) exports the
  `screen_runs/*.manifest.json` the as-of is read from. Running `screen` first was wasted work.
- **THE ARTIFACT-PASS RULE EARNED ITS KEEP AGAIN:** the first suite run went RED on
  `test_the_wall_clock_is_unreachable_from_the_reference_date` — the committed price fixture still
  held 2026-08-12 while the as-of had moved. Both fixtures regenerated per the runbook; green after.
