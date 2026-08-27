---
id:
status: shipped
date: 2026-08-27
prs: []
supersedes:
superseded-by:
---

# `$BRKB` is notation, not a delisting

**Operator decision.** The `renamed` map now also carries symbol NOTATION, not only renames:
`{"BRKB": "BRK.B"}`. The map is read as **cashtag → the symbol Polygon serves it under**, which is
what it was always doing; the key's name understates it, and the module docstring now says so
rather than leaving the next reader to infer it from one entry.

**Why it mattered.** `$BRKB` is how he types it; `BRK.B` is what Polygon answers to. The cashtag
returned an EMPTY series, which is indistinguishable from a delisting — the same failure shape as
the `$SQ` truncation, arriving from the other direction. `BRK.B` serves the whole window.

**No splice, and it must not claim one.** The cashtag half is empty, so `_splice_rename` returns
the successor's series outright: no seam, no guards fired, and `spliced_at` is CORRECTLY ABSENT
while `renamed_to` records where the series came from. Pinned by
`test_a_notation_alias_is_the_successors_series_outright`, mutation-checked — forcing the file to
stamp `spliced_at` unconditionally reddens exactly that test.

**Result.** `BRKB` 0 → **383 bars** (2024-05-20 → 2025-11-26). Price anchors **8,149 → 8,155 of
8,185 (99.56% → 99.63%)**.

**No number moved, and here is the honest reason.** All 6 `$BRKB` rows are `bias=none` flow-spam —
"Top Bullish/Bearish Flow" lists where the cashtag appears as a line item, never as a call. They
were never scoreable and still are not; `vinci calls score` returns byte-identical output. What
this buys is a COMPLETE AUDIT SURFACE: a human reading those 6 rows now sees the price beside them
instead of a blank that looks like missing data.

**30 rows remain blank, and all of them should be** — crypto (DOGE, SOL, BTCU, BTCSD), indices
(SPX, NDXP, KOSPI), and 11 cashtag typos in the source posts. The typos stay uncorrected: inferring
`TSLA` from `TSAL` is a guess about what he meant.
