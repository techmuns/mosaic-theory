---
id: D11
status: recorded
date: 2026-07-27
prs: [283, 282]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
date-source: UNKNOWN — not recoverable from the header or git; do not read as fact
---

**D11. THE OFFLINE GATE HAD A LIVE SEC CLIENT IN IT** (review finding on #283, and #282 shipped it).
Three corpus pins built a real `EdgarClient` and wrapped each fetch in
`except Exception: pytest.skip("EDGAR facts unavailable offline")`. **`data/dossiers` is COMMITTED
but `data/cache` is git-ignored**, so on a fresh checkout the `is_dir()` guard passes, the cache
misses, and `companyfacts` goes to the wire — inside `pytest -m "not network"`. MEASURED in a
cleanroom with `socket.create_connection` blocked: a cold cache **attempts a live call**, it does
not degrade. Both outcomes were wrong — with egress, ~33 live SEC requests inside the gate that
exists to be offline; without it, the broad `except` swallows the failure and **every corpus pin
silently passes by skipping**, which is the guard-that-cannot-fire class inside the pins written to
prevent it. Every other EDGAR test in the suite (`test_anchor`, `test_band_guards`) uses a synthetic
fixture; these were the only ones reaching for a real client, and `@pytest.mark.network` already
exists for tests that mean it. **FIXED with an `offline_edgar` fixture that skips on a COLD cache
and BLOCKS outbound connections while the pins run**, so a cache miss fails loudly instead of
fetching. **THE FIRST GUARD WAS ITSELF WRONG and the cleanroom caught it:** `cache_dir.is_dir()`
tests existence, but the config/client CREATE the directory — an empty cache sailed past and hit the
network block, which would have RED-ed main on any fresh checkout. The guard counts entries.
Verified both ways: cold cache → 3 skipped, no network attempt; partially-warm cache → 3 loud
failures, not silent skips.
