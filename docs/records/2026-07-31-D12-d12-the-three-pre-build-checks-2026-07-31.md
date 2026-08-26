---
id: D12
status: recorded
date: 2026-07-31
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**D12. THE THREE PRE-BUILD CHECKS (2026-07-31).**
1. **NO OTHER `except → skip` PINS.** AST scan of the whole suite (not grep — an except handler
   whose body can reach `pytest.skip`, however spelled): **one** site remains,
   `test_dossier.py:7805`, and it is `except LookupError` around "IT not in the committed candidate
   set" — a narrow, named absence, not an error being swallowed. The pattern is not systemic.
2. **THE SUITE DOES CATCH A JSON/PAGE DIVERGENCE — three pins, verified by mutation.** Reverting
   SMPL's rendered `Screen value / share` to `$41.60` against a record of `43.3326` reds
   `test_dossier::test_analysis_tier_reads_in_decision_order_e2e`,
   `test_parity_pins::test_screening_context_reaches_every_committed_dossier_e2e` and
   `test_refresh_path::test_a_noop_refresh_is_byte_identical`. The hole feared after the backfill
   does not exist; the ARTIFACT-PASS RULE (full suite on freshly-committed artifacts) is what makes
   it bind, and it is why the stale page could not have shipped.
3. **THE us-gaap FALLBACK DOES NOT RESOLVE FUBO.** `us-gaap:CommonStockSharesOutstanding` DOES
   carry a newer instant — **2025-09-30 = 342,664,855** vs dei's 2025-07-31 = 342,433,118 — but it
   is still **pre-reverse-split and still 11.2× too high**, so the fallback buys two months of
   staleness and no correctness. Swept ALL share-named tags across both namespaces: **no 2026 filing
   carries any point-in-time share count at all**, while us-gaap facts filed 2026-05-06/2026-06-16
   are present. The only current share information FUBO publishes is the weighted average (30.7M).
   **CHEAPER THAN A COVER-PAGE PARSE, and general:** a share count whose vintage lags the issuer's
   OWN latest filed fact by more than a quarter is stale — the same measure-the-source-against-itself
   trick as the store-freshness guard, and it flags FUBO with no parsing at all. Queued.
