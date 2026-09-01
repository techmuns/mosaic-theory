---
id:
status: recorded
date: 2026-09-01
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §2 (capability entry, compacted)
date-source: the migration date — the capability is older and is dated in the body
---

# Earliness-assay v0 harness (`vinci/themes/assay.py` + `assay_schemas.py` + `assay_candidates.py`; CLI `themes-assay` / `themes-assay-retrocast`) — FALSIFY-OR-SURVIVE, ZERO LLM, backend-only (nothing deploys).

*The one-line summary stays in STATE.md §2 with a pointer here. This is the detail that stood beneath it, verbatim.*

- **Earliness-assay v0 harness (`vinci/themes/assay.py` + `assay_schemas.py` + `assay_candidates.py`;
  CLI `themes-assay` / `themes-assay-retrocast`) — FALSIFY-OR-SURVIVE, ZERO LLM, backend-only (nothing
  deploys).** A deterministic retrocast that places each quarter of a candidate theme in a velocity×price
  QUADRANT and measures EARLY residence — to test the fund's *earliness* premise (that a theme is
  observable in disclosure BEFORE the basket re-rates) before any capital or extraction is built on it.
  **Two axes, point-in-time:** (x) disclosed-activity velocity — new filers first-mentioning the driver's
  terms per quarter (EDGAR full-text search, `from`-paginated, cache-first; a page cap degrades LOUDLY to
  a lower bound, never silently); (y) an obvious basket's median excess re-rating vs IWM AND SPY (Polygon
  grouped-daily, as-of only; a missing close is `None`→UNKNOWN, never a silent 0.0). Each quarter →
  {EARLY / PRICED / QUIET / NARRATIVE / UNKNOWN} under a **boundary sensitivity grid** (2 price-flat
  thresholds × 2 activity-rising tests = 4 combos); EARLY residence (longest consecutive run) is measured
  per combo. Output is an **`AssayCard` — assemble-not-conclude: NO score / rank / verdict field** (pinned
  by a schema-walk guard + an AST no-ledger/no-scoring import guard; `rank` added to the forbidden set —
  a quadrant is a factual label, not a ranking). **THE_BASKET_RULE (verbatim, printed on every card):**
  "At as-of, rank filers by DISTINCT filings mentioning ANY of the candidate's terms over the trailing 8
  quarters (EDGAR full-text). Map CIK->ticker (SEC company_tickers). Keep common stocks whose as-of market
  cap (XBRL cover-page shares x Polygon close) is $100M-$10B (the Component-A cap band). Take the top 10 by
  mention count. Purely mechanical + ex-ante: no discretion, no forward information, no price used in
  selection." **KILL CRITERION (pre-committed, verbatim):** "If the retrocasts show that NEITHER
  ai-datacenter NOR defense-demand-shift had >=2 consecutive quarters of EARLY-quadrant residence before
  their re-rates - under ANY boundary combo in the sensitivity grid - the early-window premise is
  falsified and the assay build STOPS at this harness." **v0 limitations (recorded honestly):** (1) NO
  commitment/"money" read — velocity is *mention presence*, not disclosed $ commitment; 8-K commitment
  extraction is **v1**; (2) NO attention/search prior — **v1**; (3) the 8-K-family vs 10-K-family mention
  split is **PRINTED, not weighted** in v0; (4) **ZERO LLM** by construction; (5) point-in-time ticker map
  (SEC publishes only the CURRENT CIK↔ticker — noted in a card caveat). Quarters snapshot to
  `data/assay_history/` (reusing `scan_history.record_snapshot`, tagged `exposure_basis=<reference-combo
  quadrant>`); cards to `data/assay/`; efts velocity cache to `data/assay_cache/` — all git-ignored,
  LOCAL-only. Verified: ruff + `mypy --strict vinci` (90) clean; +15 network-free tests (quadrant/
  residence math incl. the ≥2q-EARLY positive control under EVERY combo, the already-priced negative
  control, the price-gap→UNKNOWN case; the no-conclude schema+AST guard; the driver-terms identity; the
  efts cache round-trip; +4 REGRESSIONS below). **Adversarial review (3 lenses × verify-refute, 5
  confirmed / 4 refuted) caught and FIXED pre-merge three real defects, each now pinned by an
  end-to-end regression:** (i) efts pages are 100 hits, not 10 — the by-10 step overlapped pages and
  inflated `cik_counts`/form-splits ~8× (now steps by 100 and stops by position-vs-total, mirroring
  `exposure.py`); (ii) a cik-less efts hit truncated pagination silently WITHOUT setting `capped`
  (same fix — the stop no longer reads the CIK-filtered row count); (iii) a share-frame LOOKAHEAD —
  basket cap-banding read XBRL shares disclosed AFTER as_of (now reuses `universe.recent_share_periods`'
  40-day filing-lag gate → no forward information, per THE_BASKET_RULE). **Live 4-case retrocast
  (2026-07-06, real EDGAR+Polygon, ZERO LLM): VERDICT = `INCONCLUSIVE — price axis gapped; the kill
  criterion cannot be evaluated` (correctly NOT a false FALSIFICATION).** flat20_medrise EARLY
  residence (longest run / total): ai-datacenter@2026-06-01 = 1/2, defense@2026-06-15 = 0/0 (both
  POST-re-rate → priced), ai-datacenter@2022-07-01 = 0/0, defense@2023-01-01 = 0/0 — **but both
  pre-re-rate (EARLY-expected) windows are ENTIRELY price-gapped** (Polygon's ~5y history can't reach
  the 2016-2020 8-quarter baselines), so a ≥2q EARLY run could be neither observed NOR ruled out. The
  VELOCITY axis validated cleanly (rich efts back to 2018; sensible point-in-time baskets — VRT/RIOT/
  KULR for 2022 AI-datacenter, ONDS/RDW/AVAV for 2026 defense; loud lower-bound flags on 34-44 capped
  term-quarters/case). **Assay v0 SURVIVES (not falsified); it neither confirms nor kills the
  earliness premise — the binding constraint is PRICE HISTORY (a v1 unlock: deeper EOD back to ~2016),
  not a design flaw.** Operationally: efts throws transient 500s under the request burst → the harness
  fails LOUD (never fabricates); a cache-first re-run resumes (idempotent, monotonic) — the retrocast
  completed via that recovery. On a feat/theme-assay branch; PR opened, NOT merged.**
  **— ADDENDUM (2026-07-06, deeper-history re-run; the INCONCLUSIVE record above stays — it was TRUE
  under the 5y constraint):** operator upgraded the Polygon plan; EOD now reaches 2018-01-02 (verified:
  SPY & IWM both 61/61 bars across Q1-2018). Re-running the SAME 4 cases (efts fully cache-first, ZERO
  LLM; **+104 pre-2021 grouped-daily bars fetched fresh; NO cache purge — the prior polygon cache held
  only valid `OK` bars (2021-09-30→2026-07-02), and the old plan's pre-2021 gaps were 403s that netcache
  never persisted, so zero poison existed**) makes the pre-re-rate windows evaluable and FLIPS the
  verdict to **`PASS (survives — early-window premise NOT falsified)`**. Evidence: **defense-demand-shift
  @ 2023-01-01 has a ≥2 consecutive EARLY run under ALL 4 combos** (flat20/flat30 × medrise/sloperise →
  runs 2/3/2/3) — rising new-filer velocity (521→425→419→366) while basket excess vs IWM AND SPY stayed
  flat-to-negative through 2021 (+0%/+0%, −10%/−14%, −16%/−25%, −17%/−37%: activity rose BEFORE price),
  then the basket re-rated NARRATIVE (+22–33%) in 2022. **ai-datacenter @ 2022-07-01** = one isolated
  EARLY quarter (2022Q1, +7%/+9%, medrise combos only, run 1). The 2026 (post-re-rate) cases are
  UNCHANGED (ai-dc 1/2, defense 0/0 — their windows were already inside the 5y history), and their EARLY
  quarters (2025Q1/2026Q1) sit MID-re-rate, not a clean pre-move signal. Residual honesty (median-of-
  available, n disclosed, NO substitution): defense-2023 early quarters rest on n=7/10 priced members
  (short-history: DRS IPO-2022 = 2/16 quarter-ends, DPRO 7/16, POWWP 8/16); ai-dc-2022 on n=4–5/10 (many
  AI-DC names IPO'd 2021+) — every quarter ≥ the 3-member median floor, no smoothing. **The earliness
  premise SURVIVES on evidence; deeper price history was indeed the unlock. Still NOT merged.**
