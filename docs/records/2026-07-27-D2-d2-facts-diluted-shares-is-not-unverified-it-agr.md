---
id: D2
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
date-source: UNKNOWN — not recoverable from the header or git; do not read as fact
---

**D2. `facts.diluted_shares` IS NOT UNVERIFIED — it agrees with the machine extraction on 7 of 7
records, to the digit.** AORT/EPAM/IT/MVST/NCNO/SMPL/WERN all match `_latest_point`'s value exactly
(+0.00%). It is analyst-entered but machine-derived, it is inside `REFRESHABLE_FACTS`, and
`ciq_balance.extract` independently reads `Weighted Avg. Diluted Shares Out.` off the CIQ Financials
workbook as a vendor bridge. The field has a path and a cross-check; what it lacked was a CORRECT
PERIOD — see D3.
