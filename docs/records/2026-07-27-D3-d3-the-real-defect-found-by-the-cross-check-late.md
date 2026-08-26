---
id: D3
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**D3. THE REAL DEFECT, FOUND BY THE CROSS-CHECK: `_latest_point` RETURNS A CUMULATIVE PERIOD, NOT
THE QUARTER ITS DOCSTRING PROMISES.** A 10-Q tags the discrete quarter AND the year-to-date span
with the SAME `period_end` and the SAME `filed`, so `max(pts, key=(period_end, filed))` breaks the
tie arbitrarily. **MEASURED — 4 of 11 names get a cumulative span:** SMPL a 272-day (nine-month)
figure **+4.16%** above its quarter (93,677,801 vs 89,940,680), FUBO 181-day −2.17%, BRBR 181-day
+1.02%, CNXC 181-day +0.35%. The other seven land on a true ~89-day quarter and are unaffected.
**SMPL'S COMMITTED RECORD CARRIES THE FALSE BASIS STRING** — `"diluted weighted-average (latest
10-Q)"` on a nine-month average — which is item 24's own defect class (a denominator whose stated
basis is not what it is) sitting inside the field item 24 was about to swap. DIRECTION: SMPL is
buying back, so the cumulative average is HIGHER than the current quarter and per-share value is
understated. **This is a prerequisite, not a side-finding: swapping the denominator on top of a
mis-periodised input just moves the error.**
