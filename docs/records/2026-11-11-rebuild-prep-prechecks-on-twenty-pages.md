---
status: recorded
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Rebuild prep at $0: the pre-spend check on the 20 committed pages not yet built on fixes 1, 3a, 3b, 4a and rows 51 and 57 — 6 pass clean, 5 lose only fields a merged fix stops stating, 9 are refused on a CIQ panel past the 45-day ceiling, and 5 have CIQ exports older than their newest 10-Q

**WHAT.**
- **The check.** `vinci dossier precheck --ticker <T>` (RUNBOOKS §i step 4; STATE row 43) ran once on
  each of the 20 pages. It made no LLM call: the environment carried no Anthropic key and no
  evidence spool, and nothing was assembled. The 20 are every committed page except the seven built
  after those fixes merged: VITL, VRRM, EPAM and WLK (2026-11-09, extraction `2026-11-09.asof-cut`),
  and V, UBER and TECX (`2026-11-09.order2-pages`).
- **The table** below has one row per page. Its columns:
  - the newest filing the page should reflect, from EDGAR on 2026-11-11;
  - the CIQ exports' dates (file dates in the CIQ folder) and whether they postdate that filing;
  - what to re-download;
  - the precheck's result;
  - the expected cost, from the cost-and-outcome series.
- **The four groups, for the operator:**
  1. **Buildable now, nothing lost (6):** GOOGL, CNXC, NCNO, NKE, SMPL, TJX. Each exits 0.
     - SMPL's underwrite still waits for its Q1 FY27 10-Q (row 36); the page itself can carry the
       fixes now.
     - TJX's panel ages out on 2026-12-01 and NCNO's on 12-12. Last year their next 10-Qs were
       filed 12-02 and 12-03.
  2. **Buildable now, losing only what a merged fix stops stating (5):** AMZN (1 field), LLY (1),
     MCK (2), NFLX (1), ORKA (2). Each exits 1 and needs the operator's acceptance, as VITL and
     TECX did.
     - All 7 losses come from merged fixes. Each committed value is years stale:
       - fix 3b (#930) stops stating a buyback figure more than a year old (5 of the 7: AMZN,
         LLY, MCK ×2, NFLX);
       - #872 stops reading an older period for "the latest" figure (ORKA's two).
     - ORKA's CIQ exports also predate its 2026-11-09 10-Q (group 3).
  3. **Re-export now; the newest filing is already out (5):** IT, MVST, ORKA, PARR, WERN. Their
     Financials predate their newest 10-Q. IT, MVST, PARR and WERN are also refused on panel age.
  4. **Wait for the filing due next, then re-export (5):** BRBR (FY26 10-K), BURL, TGT, ROST (Q3
     10-Qs), FUBO (no periodic filing since 2026-08-05).
     - Each is refused now on a comps panel 47 to 92 days old.
     - A comps-only re-export would put the comps and the Financials on different balance
       sheets, UBER's failure (row 28), so a full set after the filing is the cleaner path.

| Page (sleeve) · committed build | Newest filing to reflect (EDGAR, 2026-11-11) | CIQ exports: Financials / Estimates / Comps | Postdate it? → re-download | Precheck (exit · regressions · post-spend refusals · panel age) | Expected cost: last build (run, date, calls) |
|---|---|---|---|---|---|
| AMZN (quality) · 2026-11-03 | 10-Q filed 2026-10-30 (Q to 09-30) | 11-02 / 11-02 / 11-02; Q3 call 10-29 held | yes → none | exit 1 · 1: `capital_allocation.buyback_cash` (latest repurchase tag covers FY2024, 679d old; fix 3b) · 0 · 12d, refused from 12-15 | $5.82 (`f4458b22`, 11-03, 10) |
| BRBR (overshoot) · 2026-10-26 | 10-Q filed 2026-08-04 (Q to 06-30); FY26 10-K next (last year's: 2025-11-18) | 09-22 / 09-22 / 09-22 | yes, but stale → full set after the FY26 10-K, with its Q4 call | exit 1 · 0 · 1: freshness, comps 51d (09-21), refused from 11-06 | $1.79 (`d9ef21bc`, 10-26, 7) |
| BURL (quality) · 2026-10-26 | 10-Q filed 2026-08-27 (Q to 08-01); Q3 10-Q next (last year's: 2025-11-25) | 09-28 / 09-28 / 09-28 | yes, but stale → full set after the Q3 10-Q, with its Q3 call | exit 1 · 1: `capital_allocation.buyback_avg_price` (tag's latest is 2015; fix 3b) · 1: freshness, comps 47d (09-25), refused from 11-10 | $6.53 (`6de30ce0`, 10-26, 10) |
| CNXC (overshoot) · 2026-10-29 | 10-Q filed 2026-10-07 (Q to 08-31) | 10-26 / 10-26 / 10-26; Q3 call held | yes → none | exit 0 · 0 · 0 · 19d, refused from 12-08 | $5.41 (`40520189`, 10-29, 9); a 19c refusal on 10-26 cost $5.16 |
| FUBO (overshoot) · 2026-08-18 | 10-Q filed 2026-08-05 (Q to 06-30); none since | 08-12 / 08-12 / 08-12 | yes, but stale → full set after its next periodic filing | exit 1 · 2: `capital_structure.covenant_term_rows` (#652 refuses the exhibit as not a debt agreement), `quality.free_cash_flow` (annual cash flow ends FY2024; #817) · 1: freshness, comps 92d (08-11) | no build recorded (the page predates the series) |
| GOOGL (quality) · 2026-11-03 | 10-Q filed 2026-10-29 (Q to 09-30) | 11-02 / 11-02 / 11-02; Q3 call 10-28 held | yes → none | exit 0 · 0 · 0 · 12d, refused from 12-15 | $4.43 (`05a57bf8`, 11-03, 7) |
| IT (overshoot) · 2026-08-18 | 10-Q filed 2026-11-03 (Q to 09-30) | 07-20–21 / 07-30 / 07-30; latest call Q1 (05-05) | **no** → full set: Financials A+Q, Estimates, comps, Customers + Suppliers, Key Developments, Profile, and the Q2 and Q3 2026 calls | exit 1 · 0 · 1: freshness, comps 105d (07-29) | no build recorded |
| LLY (quality) · 2026-11-03 | 10-Q filed 2026-10-29 (Q to 09-30) | 11-03 / 11-02 / 11-02; Q3 call held | yes → none | exit 1 · 1: `capital_allocation.buyback_shares` (tag's latest is 2021-H1; fix 3b) · 0 · 12d, refused from 12-15 | $3.03 (`ac8b8b71`, 11-03, 6); a 19c refusal on 10-29 cost $2.91 |
| MCK (quality) · 2026-11-05 | 10-Q filed 2026-11-04 (Q to 09-30) | 11-05 / 11-05 / 11-05; Q2 FY27 call held | yes → none | exit 1 · 2: `buyback_avg_price` (2020), `buyback_shares` (2019–20); fix 3b · 0 · 7d, refused from 12-20 | $7.40 (`d4304414`, 11-05, 11) |
| MVST (overshoot) · 2026-09-17 | 10-Q filed 2026-11-09 (Q to 09-30) | 08-13 / 08-13 / 08-13; latest call Q2 | **no** → full set, with the Q3 2026 call | exit 1 · 0 · 1: freshness, comps 91d (08-12) | no build recorded |
| NCNO (overshoot) · 2026-08-18 | 10-Q filed 2026-08-25 (Q to 07-31); Q3 FY27 10-Q next (last year's: 2025-12-03) | 10-28–29 / 10-28 / 10-28 | yes → none before the next 10-Q | exit 0 · 0 · 0 · 15d, refused from 12-12 | no build recorded |
| NFLX (overshoot) · 2026-11-05 | 10-Q filed 2026-10-21 (Q to 09-30) | 10-28 / 10-28 / 10-28; Q3 call held | yes → none | exit 1 · 1: `buyback_avg_price` (tag's latest is 2011; fix 3b) · 0 · 15d, refused from 12-12 | $5.55 (`56f6a840`, 11-05, 10); a 19c refusal on 10-29 cost $5.06 |
| NKE (overshoot) · 2026-10-29 | 10-Q filed 2026-10-02 (Q to 08-31); Q2 FY27 10-Q next (last year's: 2025-12-30) | 10-29 / 10-29 / 10-29; Q1 FY27 call held | yes → none | exit 0 · 0 · 0 · 14d, refused from 12-13 | $4.60 (`8a695c73`, 10-29, 10) |
| ORKA (quality) · 2026-10-26 | 10-Q filed 2026-11-09 (Q to 09-30) | **09-01** / 10-26 / 10-26 | **no** → full set (Financials A+Q, Estimates, comps, Customers + Suppliers, Key Developments, Profile) | exit 1 · 2: `leverage_survival.interest_coverage`, `quality.interest_coverage` (the committed value reads FY2024; the latest LTM column reads '-', and #872 reads no older period in its place) · 0 · 19d, refused from 12-08 | $1.25 (`fee45da9`, 10-26, 5) |
| PARR (ultra_short_term) · 2026-10-26 | 10-Q filed 2026-11-04 (Q to 09-30) | 09-17 / 09-17 / 09-17; latest call Q2 | **no** → full set, with the Q3 2026 call | exit 1 · 0 · 1: freshness, comps 56d (09-16) | $2.71 (`921d6fa7`, 10-26, 10) |
| ROST (quality) · 2026-10-29 | 10-Q filed 2026-09-01 (Q to 08-01); Q3 10-Q next (last year's: 2025-12-10) | 09-28 / 09-28 / 09-28 | yes, but stale → full set after the Q3 10-Q, with its Q3 call | exit 1 · 1: `buyback_shares` (covers to 2025-11-01, 374d; fix 3b) · 1: freshness, comps 47d (09-25), refused from 11-10 | $2.24 (`2b562803`, 10-29, 6) |
| SMPL (overshoot) · 2026-11-04 | 10-K filed 2026-10-27 (FY to 08-29); Q1 FY27 10-Q next (last year's: 2026-01-08) | 11-04 / 11-04 / 11-04; Q4 call held | yes → none now; after the Q1 10-Q for its underwrite (row 36) | exit 0 · 0 · 0 · 8d, refused from 12-19 | $2.99 (`29e8038c`, 11-04, 8) |
| TGT (quality) · 2026-10-26 | 10-Q filed 2026-08-28 (Q to 08-01); Q3 10-Q next (last year's: 2025-11-26) | 09-28 / 09-28 / 09-28 | yes, but stale → full set after the Q3 10-Q, with its Q3 call | exit 1 · 0 · 1: freshness, comps 47d (09-25), refused from 11-10 | $3.07 (`59d556d2`, 10-26, 8) |
| TJX (overshoot) · 2026-10-29 | 10-Q filed 2026-08-28 (Q to 08-01); Q3 10-Q next (last year's: 2025-12-02) | 10-18 / 10-18 / 10-18 | yes → none for a build before 12-01 | exit 0 · 0 · 0 · 26d, refused from 12-01 | $4.32 (`8ad38af1`, 10-29, 11) |
| WERN (overshoot) · 2026-09-17 | 10-Q filed 2026-11-09 (Q to 09-30) | 08-19 / 08-19 / 08-19; latest call Q1 | **no** → full set, with the Q2 and Q3 2026 calls | exit 1 · 0 · 1: freshness, comps 85d (08-18) | no build recorded |

- **Reading the table.**
  - "Refused from" is the precheck's own date: a paid build on or after it is refused on panel age.
    The panel is the comps export's TEV date (`valuation.implied_expectations.tev_as_of`) on all 20.
  - "Postdate it?" compares the Financials export's file date with the newest 10-Q or 10-K filing
    date. The freshness guard does not check this: ORKA passes it, on comps dated 10-23, while its
    Financials are from 09-01.
- **Expected cost.**
  - The series holds a build for 15 of the 20, summing to **$61.14** at their last recorded cost.
  - The current code costs more. Three names were built both on 10-26 and on 11-09: UBER
    $5.75 → $6.54 (+14%), WLK $3.30 → $4.44 (+35%), V $2.72 → $4.15 (+53%). That band gives
    **$69.70–$93.54** for the 15.
  - FUBO, IT, MVST, NCNO and WERN have no recorded build (their pages predate the series). The 7
    builds of 11-09 and 11-10 ran $1.46–$6.54, median $4.44, so about $22 for the five, between
    $7 and $33.
  - Group 1 (6) plus group 2 without ORKA (4) are the 10 pages buildable on today's exports:
    **$43.55** at last cost for the 9 with a record ($49.65–$66.63 on the band), plus NCNO.
  - A 19c refusal costs one more build. It happened once each to CNXC, LLY and NFLX in October.

**WHY.** The brief: a combined rebuild follows the remaining fixes. Coordinator A runs it, or S5
does on the operator's approval. The re-exports the operator downloads by hand are the usual
bottleneck, so the operator needs, before any spend: which pages are ready, which exports to pull,
which losses to rule on, and what it costs.

**HOW VERIFIED.**
- **The precheck's own output, per page,** on two code heads with identical results:
  - first on `main` at `2637e91b` (extraction `2026-11-11.unpriced-count-names-its-horizon`);
  - then on `main` at `c0d6d830`, after #971 and #972 (CIQ reader, order 5) merged (extraction
    `2026-11-10.header-offset-and-renamed-tabs+2026-11-10.period-order-and-duration+2026-11-11.unpriced-count-names-its-horizon`).
  - All 20 are the same on both: exit, regression paths, post-spend refusals and panel age. This
    agrees with both PRs' "no page moves".
  - Every log opens with the spreadsheet reader's warnings that an `.xls` export's size is "not
    512 + multiple of sector size". These are the reader's warnings on CIQ's files, not a failure.
  - Exits are 6 at 0 and 14 at 1.
  - 11 regressions on 8 pages: AMZN 1, BURL 1, FUBO 2, LLY 1, MCK 2, NFLX 1, ORKA 2, ROST 1.
  - 9 freshness refusals.
  - 0 materiality or drawdown refusals.
- **Attribution by the note each regression prints, then the code.**
  - `git log -S` on each note's text: `no current figure` → `f491d155` (#930, fix 3b);
    `an older period is never read in its place` → `ad84cb3f` (#872).
  - FUBO's two notes name #652's exhibit guard and #817's stale-annual guard. Its page (extraction
    `2026-08-16.1`) predates both.
- **A store-caused false result was found and removed before the table was drawn.**
  - The first GOOGL run listed 5 regressions: the 52-week high and low, and three 180-day legs.
  - Their notes read "only 97d history (< 330d)" and "name has no bars over the window".
  - The store had no GOOGL bar before 2026-08-05. Seven more pages were in the same state: BURL,
    LLY, MCK, NFLX, ROST, TGT, TJX, 69 bars each. Those pages were built on another machine's
    store (row 38).
  - The eight were backfilled on the scratch copy with `vinci refresh <8 names> --aggs --start
    2024-11-12 --end 2026-11-10`: 8 Polygon calls, 500 bars each, nothing restated.
  - All 20 were then re-run. GOOGL's re-run exits 0, and its first output is kept in the scratchpad.
- **Nothing written outside the scratch copies.**
  - The primary's `data/vinci.db` read `78e22391…` before and after.
  - No file in the primary's `data/manual/ciq` is newer than 13:00Z on 2026-11-11.
  - `git status` in the scratch worktree is clean.

**BOUNDARY.**
- **Code:** `main` at `2637e91b`, then at `c0d6d830`, in a detached scratch worktree.
- **Pages:** the 27 committed under `data/dossiers/` at that commit, less the 7 named above, so 20.
- **Store:** the S5 rehearsal's refreshed clone (bars to 2026-11-10;
  `docs/records/2026-11-11-vrrm-run-monthly-rehearsed-on-a-copy.md`) plus the 8-name backfill,
  sha256 `ca8bd5a6…` before the re-runs.
- **CIQ:** the primary checkout's `data/manual/ciq`, read through a symlink.
- **Caches:** SEC, EFTS and FINRA caches cloned from the primary's.
- **Dates:**
  - Panel ages are each precheck's own, measured on 2026-11-11.
  - Export dates are file modification dates (IST) in the CIQ folder.
  - Filing dates are EDGAR submissions read on 2026-11-11.
  - "Last year's" is the 10-K or 10-Q a filer filed between 2025-11-11 and 2026-01-20.
- **Costs:** `usd` from `data/snapshots/assembly_runs/*.jsonl` at `2637e91b` (44 files): the latest
  `written` line per name, list price, `claude-opus-4-8`.
- **Live calls:** SEC 8,884, EFTS 28, FINRA 20, Polygon 22 (14 ticker references and the 8
  backfills), Tiingo 0. Counted as cache files written in the scratch worktree from 13:30Z; the
  re-run on `c0d6d830` (15:20–15:28Z) wrote none.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0 of LLM.
- About 1.7 hours of the machine's shared SEC budget (13:31–14:08Z, then 14:11–15:15Z). GOOGL's first run took 36 minutes, because
  its SEC reads were cold here and another session's run was sharing the budget.
- The precheck compares presence and some values, never the synthesis. A paid build can still
  differ from it where the paid draw decides (`capital_structure.maturity_event` on GOOGL, the
  19c guard).
- The cost band is a measured range on three names, not a fit.
