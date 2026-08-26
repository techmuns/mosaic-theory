---
id: 
status: recorded
date: 2026-07-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-24 benchmark cap-band pin (ranker screen-time cap as the fallback).**
Closes the KNOWN-ISSUE above. Root cause: the dossier's `_resolve_benchmark` bands on the **CIQ
valuation cap** (`implied_val.market_cap`, $M) and **silently defaults to IWM when that is UNKNOWN**;
IT's committed candidate `market_cap` is null, so the screen's own cap never reached the dossier —
and in an incomplete store (a worktree re-assembly) the CIQ cap is absent → silent MDY→IWM. Fix (the
operator's own suggestion): the **ranker already freezes the screen-time EOD×XBRL cap on every
`ranked_queue` row** (`market_cap`, present on 275/275 rows), and that value flows to the assembler
via the `Finalist`. So the benchmark is banded on that frozen cap **as a fallback when the CIQ cap is
absent** — no new schema field, no screen change, dossier-side only. Threaded
`Finalist.market_cap_screen` (from `_cap_of(row)`) → `assemble_mechanical(screen_cap_usd=…)` →
`_resolve_benchmark(…, screen_cap_usd=…)`. Fallback order: CIQ cap → ranker screen-time cap → IWM
default; the CIQ cap still WINS when present (committed dossiers unchanged — IT stays MDY via the CIQ
path, verified). Real-run: the exact IT incident — CIQ unknown + ranker $9.13B → **MDY** (was IWM);
basis "cap-band: $9.1B (screen-time, ranker) → mid → MDY". SECOND beneficiary found: **NCNO**'s
committed dossier was on the "cap UNKNOWN → IWM default" basis (its CIQ cap was absent in production
too) — its ranker cap $2.03B keeps the SAME symbol (IWM) but the next re-assembly states a JUSTIFIED
basis instead of a blind default. INVARIANT: `test_resolve_benchmark_cap_bands_and_unknown_fallback`
extended (positive IT→MDY fallback, negative small-cap→IWM, CIQ-wins-over-ranker priority) +
`test_finalist_carries_ranker_screen_cap_for_benchmark_fallback` (`_cap_of` + threading). Gate: ruff
+ `mypy --strict` clean · 1049 passed · no committed-artifact drift (only NCNO's basis text improves
on re-assembly; every benchmark SYMBOL is unchanged).
