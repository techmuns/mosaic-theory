---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **Universe builder** (`vinci/universe`) — market cap = close × XBRL shares, cap-band + $3M ADV +

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **Two independent operating-co axes, each fail-CLOSED on a missing value (exclude what we cannot
    confirm; never silently admit) — built + verified 2026-06-19 by a full rebuild:**
    - **Axis 1 — issuer BUSINESS type (EDGAR SIC).** Denylist `excluded_sic_codes =
      6189/6221/6722/6726/6770` (`non_operating=38`) PLUS a **blank/unknown SIC is now excluded**
      (`unknown_sic=29`) — closing the hole where a BDC with no EDGAR SIC slipped the denylist (`None`
      is never `in` the set). *The 29 are 28 BDCs (CION, OTF, Prospect, Main Street, FS KKR, Sixth
      Street, …) + 1 foreign miner; the BDC candidates CION/OTF/GLAD/MSIF/PFLT left the queue.*
    - **Axis 2 — security INSTRUMENT type (Polygon reference; `PolygonEodClient.security_types()`,
      one cached bulk pull).** An **ALLOWLIST** `allowed_security_types = CS/ADRC/OS/GDR` (domestic
      common / ADR common / foreign ordinary / GDR); everything else excluded, split for honesty into
      `non_common_equity=7` (a confirmed basket/derivative — SHNY=ETS, DHC/ILPT=FUND, MNR/NOVTU/VSECU=
      UNIT, CORZW=WARRANT) and `unknown_type=4` (absent from Polygon's reference = recently delisted,
      stale bars — MASI/KW/KALV/SCVL, last trade before the 06-17 ref). *SHNY left both the universe
      AND the queue; the 14 ADRC candidates (ABVX, ATHM, CHA, DQ, …) survive — ADRC is admitted, so
      operating-co ADRs are not dropped.*
  - **SHNY was NOT a resolver collision.** Its ticker→CIK (→ cik 927971, Bank of Montreal) is
    **correct** — BMO *issues* the SHNY ETN (one of 27 BMO tickers). It was an **untyped-instrument
    leak**: a leveraged ETN (Polygon type ETS) whose bank fundamentals describe none of it, now caught
    by Axis 2 — not by any ticker-validation (a collision guard was built, then reverted as the wrong
    diagnosis). Axis 2's fail-closed-on-missing also sweeps recently-delisted names the 90-day price
    gate still admitted (an as-of-now vs as-of-date asymmetry, acceptable for a forward-tradeable
    universe).
  - **SIC now PERSISTED per-name (2026-07-06) — was a dead write.** The EDGAR SIC fetched for the
    Axis-1 gate (`resolver.sic_for(cik)`) was used then discarded (`[0]`), so `sic` was NULL in every
    committed security/issuer (0/2296). `universe.py` now enriches the identity with the already-fetched
    `(sic, sic_description)` before `store.upsert_security` — `securities.sic`/`issuers.sic` already
    round-trip, so no schema/store change. Enables a DERIVED coarse **sector** downstream via the
    existing `sectors.sector_for_sic` (assemble/inform ONLY — never a screen/rank/verdict input; the
    deferred SIC-peer-cohort §G2 caveat is untouched). *Verified: (1) a `build_universe` regression pin
    (monkeypatched clients) asserts the fetched SIC persists onto the stored security + derives its
    bucket; (2) `sectors` pins (7372→Technology, 2834→Health Care, blank/None→Unknown, never guessed);
    (3) a REAL run — NCNO+BILL both real SIC 7372→Technology (they cluster), AAPL 3571 / NVDA 3674→
    Technology, blank→Unknown — resolve→enrich→persist→round-trip→sector on live EDGAR. ruff + mypy
    --strict (vinci) + pins green. Committed `securities.jsonl` repopulates on the operator's next
    `build-universe`.*
  - **`universe_snapshot` accretion — FIXED 2026-07-06 (regression-pinned; same class as the re-screen
    accretion below).** Surfaced during the first post-persist rebuild on the operator's persistent DB:
    `build_universe` called `store.clear_universe(reference_date)` (clear only the rebuild's OWN
    `as_of`), so an EARLIER generation survived and the export layered on top — `run_weekly` reloads
    last build's snapshot (as_of 06-17), then `build_universe` writes today's (07-06) → the committed
    `universe_snapshot.jsonl` doubled to 3,487 rows with 1,677 duplicate `internal_id`s across two
    `as_of`. Reads still resolved (`latest_universe` = MAX `as_of`), but the committed artifact bloats
    every rebuild. **Fix:** `clear_universe()` is now a FULL replace (`DELETE FROM universe_snapshot`,
    all generations) — a rebuild is a clean single-generation snapshot, exactly as `clear_candidates`
    does for the screen. **Regression-pinned:** `test_clear_universe_is_a_full_replace` records a day-1
    generation, rebuilds at day-2 (clear + record), asserts ONLY day-2 remains (day-1 gone) — fails on
    the old per-`as_of` clear, passes on the fix. *The live 3,487-row accretion was cleaned via
    `clear_universe` before the 07-06 snapshot commit; this code fix generalises that so it can't recur.
    ruff + mypy --strict (87) + pytest green.*
  - **Sector cluster-count roll-up on the Overshoot screen + ranker (2026-07-06) — assemble/inform,
    gates NOTHING.** Building on the SIC persist above: the `rank` CLI writer attaches a DERIVED coarse
    `sector` per name (`sectors.sector_for_sic(identity.sic)`) into `ranked_queue.jsonl` — computed in
    the WRITER, never in `ranker.py`/`screen2.py` (an AST fence test asserts neither imports
    `vinci.sectors`; the `sector` field on `RankedCandidate` defaults None so the scorer stays pure).
    `screen-overshoot.js` gains a **cross-sectional cluster card** (coarse-sector cluster sizes over the
    admitted set + largest-cluster callout + explicit `Unknown` bucket) and a per-name Sector column;
    the ranker gains a sortable Sector column; `snapshots.js` threads `sector`. Purpose = DE-CONFOUNDING
    (G2 strips MARKET beta, not sector — a large cluster asks "did the GROUP fall, not the name?") +
    concentration visibility at SELECTION time (spread_by_sector is post-hoc / ledger-only / empty).
    Captioned "business classification (SEC SIC), NOT a peer cohort / NOT a sector-adjusted control";
    never a gate/weight/sort — the deferred SIC-peer-cohort §G2 caveat is untouched. *Verified: emit
    plumbing (292/292 ranked rows carry `sector`); AST fence + offline suite (475) green; REAL preview
    over the 317 admitted names (sectors live-resolved into the git-ignored mirror) → Technology 98
    (31%) / Health Care 83 (26%) / Materials 40 / … 0 Unknown; cluster card + both columns render,
    sortable, 0 console errors. Committed `ranked_queue.jsonl` carries real sectors on the operator's
    next full pipeline run (needs PR1's populated candidates upstream). Render PR — Phase-1 preview
    shown, STOP for approval per PREVIEW RULE.*
    **Sub-industry refinement (2026-07-06) — coarse sector was too generic ("Technology 98" reveals
    nothing).** Added `sectors.industry_for_sic` — a curated deterministic 4-digit-SIC → ~52 readable
    sub-industries (Software / Semiconductors / Biotech / Pharma / Hospitals / Gold Mining / …), same
    fail-honest discipline, FALLING BACK to the coarse sector so it is never *less* informative; it is
    the same assemble/inform lens (the AST fence already forbids `vinci.sectors` in the scorer/gate,
    covers it). The `rank` writer now emits `industry` beside `sector`; the per-name column shows the
    **sub-industry** (replaces the sector column) and the cluster roll-up is **TWO-LEVEL** (coarse
    sector → its sub-industries); the filter matches sector+industry. Honest ceiling recorded: SIC tops
    out at sub-industry, NOT the co-movement DRIVER (that is the theme edge) — do not push SIC further.
    *Verified: `industry_for_sic` pins (7372→Software, 2836→Biotech, 8062→Hospitals, unmapped→coarse
    fallback, blank→Unknown); ruff + mypy --strict + offline suite (479) green; REAL preview over the
    317 admitted → Technology 98 splits Software 36 / IT Services 28 / Semis… and Health Care 83 splits
    Pharma 38 / Devices 18 / Biotech 13 / Hospitals 3 / Diagnostics 7 (+ a Gold Mining 18 cluster);
    both columns fit (ranker no h-scroll), search "biotech"→13, 0 console errors.*
    **Screen focus (2026-07-06):** the redundant per-name TABLE was removed from the Screen (it lives
    on the Ranker in priority order) — the Screen is now purely the cross-sectional cluster roll-up +
    count + gate logic; the two prose "metric" cards ("This view" / "Disposition") were dropped
    (repetitive; folded into a count headline + the gate note). **DEFERRED — cluster TREEMAP / heatmap
    view (NOT built):** a Clusters↔Treemap toggle (hand-rolled dependency-free SVG, sized by cluster
    count, coloured by sector) was scoped + approved-in-principle (treemap over stacked-bars), then
    deferred by the operator. Rationale: the chip roll-up already conveys the exact counts; the treemap
    adds gestalt (area/colour concentration) but is a moderate build for marginal value today. **Unlock
    trigger:** revisit when the admitted set / sector count grows enough that the chip roll-up gets
    unwieldy (i.e. eyeballing concentration across the chips stops being easy).
