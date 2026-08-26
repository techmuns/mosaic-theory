---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **MAIN WAS RED FOR ELEVEN CONSECUTIVE MERGES, and the gate said nothing about it (2026-08-07,

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **The pins passed on a laptop and COULD NOT pass in CI.** #354 shipped them against a populated
    local DB. That is D17 exactly — a pin that has never gated where it actually runs — and the
    failure text pointed at the store rather than at the missing fixture, so eleven merges read it
    as environmental noise. **`UNSTABLE` was noted on #191 and #192 and waved through both times**;
    the streak is what that costs.
  - **FIXED by the remedy D17 already established**: commit the small slice the pins read.
    `scripts/build_price_fixture.py` (mirroring `build_companyfacts_fixture.py`) freezes the bars
    for the MAINTENANCE-route names + the small-cap benchmark — **IT, MVST, IWM · 418 bars each ·
    220 KB**. The maintained set is DERIVED (committed dossiers minus screen candidates), never
    hand-listed, so it cannot drift from the fleet.
  - **OPERATOR RULING 2026-08-07 — committing Polygon-derived OHLCV to this PRIVATE repo is
    authorised** for this test-fixture purpose. It is a bounded slice, not a feed. **If the repo or
    deploy ever becomes public this fixture reverts to git-ignored**, on the same footing as the
    dossiers and `graph_coverage.json`.
  - **The store is the fixture on EVERY machine, not a fallback.** Falling back to a populated local
    DB where one exists would make the pins mean something different on a laptop than in CI — which
    is the exact property that let this defect survive eleven merges without a local run noticing.
    Only prices are substituted; dossiers, snapshots and the resolver cache are symlinked, so the
    pins still read the real committed corpus.
  - **How verified.** The failing condition was REPRODUCED, not assumed: with `data/vinci.db` AND
    `data/cache` moved aside — a fresh CI checkout — the full offline suite runs **1938 passed, 8
    skipped, 0 failed**, against CI's current *6 failed, 1881 passed*. With the DB restored, **1941
    passed**. A new pin, `test_every_maintained_name_has_committed_price_bars`, fails loudly and
    NAMES the script when a name becomes maintained without bars — so the next followed name cannot
    re-open this hole silently.
