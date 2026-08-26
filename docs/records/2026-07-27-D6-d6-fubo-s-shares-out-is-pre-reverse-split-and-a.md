---
id: D6
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**D6. FUBO'S `shares_out` IS PRE-REVERSE-SPLIT AND A YEAR STALE — the 11.65× CIQ divergence now has
its cause.** Its `EntityCommonStockSharesOutstanding` is dated **2025-07-31** while every other
name's is 2026; the weighted-average count fell 349,096,793 → 30,715,279 between the Dec-2025 and
Mar-2026 quarters. So the committed `shares_out` of 342,433,118 is a pre-split count and CIQ's
29.4M was right. `reconcile_cap` catches the divergence (`market_cap` comes from CIQ and implies
~30.8M shares against a `shares_out` of 342.4M) — the guard works; the FIELD is wrong, and the
cover-page tag is the reason. **The overlay does not fix this**: its `basic_out` leg is that same
stale cover-page fact. A staleness rule on the cover-page point is a separate, required piece.
