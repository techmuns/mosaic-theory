---
id: 
status: recorded
date: 2026-07-23
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-23 What-broke follow-ups (IT driver, NCNO price series, per-symbol
backfill).** Three operator-flagged fixes on PR #197. (1) IT's driver read only "$150.0M goodwill
impairment" — Gartner states its non-GAAP metrics with a COLON ("adjusted EBITDA: $436 million,
+5%", period in the section header), which `_RECON`'s verb-only connector (of/was/totaled) dropped.
Added the colon to the connector; currency-evidence + no-% guards still reject the ratio. Verified
no-regression by re-parsing all 11 EX-99.1 (only IT changed; MVST's diffs were stale-artifact
drift). IT's driver patched SURGICALLY (byte-preserving recompute of the one field) — a full
re-assembly was observed to flip IT's cap-band benchmark MDY→IWM (a data-sensitive side effect;
see the drift note). (2) NCNO had NO price series (10 store bars, all post-dating its 2026-07-06
reference). Root cause was NOT a missing vendor — Polygon HAS NCNO's history; `ingest_prices` uses
grouped-daily (whole-market/day), so backfilling ONE new name = ~250 whole-market calls at the free
tier's ~5/min (the stall). Fix: `refresh --aggs` = `ingest_prices_per_symbol` using the existing
`daily_bars` (ONE call/name). Backfilled NCNO (1268 bars) + the IWM/MDY benchmarks; re-assembled →
NCNO now renders the full chart + idio strip (name −37% vs IWM +36%, −45pp idiosyncratic). Tiingo
(the wired-but-keyless per-symbol adapter) is NOT needed. Pinned: colon-connector on a frozen
Gartner fixture; per-symbol ingest on a fake client (one call/name, store round-trip). Gate: 1042.
