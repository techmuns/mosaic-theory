---
id: D10
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
split-from: 2026-07-27-D9-d9-the-false-unknown-class-third-instance-review.md
date-source: UNKNOWN — not recoverable from the header or git; do not read as fact
---

*(scheduling superseded by D19.)* **D10. FUBO DOES NOT CLOSE FOR FREE — the selector is right and the SOURCE is missing** (the cheap
read, 2026-07-31). The tie-break fix does not touch `shares_out`: that path is
`_edgar_shares_outstanding` → `latest_instant(extract_points(facts, "shares"))`, a DIFFERENT
selector, and cover-page counts are **instants** — there is no quarter-vs-cumulative ambiguity to
break. The real cause is upstream of any selection: **EDGAR's companyfacts for CIK 0001484769 has
no `dei:EntityCommonStockSharesOutstanding` point after 2025-07-31**, while the same blob carries
us-gaap facts filed as recently as **2026-06-16**. The company kept filing; the dei fact stopped
appearing. So it still needs the queued 10-Q cover-page read — now evidenced on both sides, with
CIQ's 29.4M confirmed right and ours confirmed wrong. **The overlay cannot fix it either**: its
`basic_out` leg is that same stale fact.
