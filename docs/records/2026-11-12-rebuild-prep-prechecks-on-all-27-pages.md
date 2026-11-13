---
id:
status: recorded
date: 2026-11-12
prs: []
supersedes:
superseded-by:
---

# Rebuild prep at $0, all 27 committed pages on main 68bd4b33: 10 build now with nothing lost, 7 lose only buyback figures fix 3b stops stating, 5 need a full CIQ re-export now, and 5 wait for their next filing; expected $141 on today's code, proposed cap $170

**WHAT.**
- **The check.** `vinci dossier precheck --ticker <T>` (RUNBOOKS §i step 4; STATE row 43) ran once on each of the 27 committed pages, on `main` at `68bd4b33`.
  - No LLM call was made: the scratch worktree's `.env` carries no Anthropic key, the variable was blanked, and there was no evidence spool.
  - Nothing was assembled, and nothing was written under `data/dossiers/`.
  - The method is #1018's (`docs/records/2026-11-11-rebuild-prep-prechecks-on-twenty-pages.md`), widened from its 20 pages to all 27.
- **The table** below has one row per page, grouped for the operator. Its columns:
  - the newest periodic filing on EDGAR, read on 2026-11-12;
  - the CIQ Financials, Estimates and comps file dates;
  - what to re-export;
  - the precheck's result;
  - the last recorded build cost.
- **The four groups:**
  1. **Build now, nothing lost (10):** CNXC, GOOGL, NCNO, NKE, SMPL, TECX, TJX, UBER, VRRM, WLK. Each exits 0, and each page's Financials postdate its newest 10-Q or 10-K.
     - UBER's comps are still owed for its valuation basis (row 28): the precheck compares presence, not values.
     - VRRM's Q3 call is not in CIQ, so its latest call read is Q2.
     - TJX's panel ages out on 2026-12-01, the first date its next 10-Q is likely (last year's: 2025-12-02).
  2. **Build now, losing only a buyback figure fix 3b (#930) stops stating (7):** AMZN, EPAM, LLY, MCK (2), NFLX, V, VITL.
     - Each exits 1, and each loss is a repurchase tag whose latest period ends 1 to 15 years before the price date.
     - Each needs the operator's acceptance, as VITL's and TECX's did. EPAM, V and VITL are new to this list, because #1018's table did not cover them. Each 11-09 page states a buyback figure that fix 3b now refuses.
  3. **Re-export a full set now; the newest filing is already out (5):** IT, MVST, ORKA, PARR, WERN. Their Financials predate their newest 10-Q.
     - IT, MVST, PARR and WERN are also refused on panel age.
     - ORKA loses two interest-coverage fields to #872. Its CIQ Income Statement reads '-' at the latest column, and #872 never reads an older period in its place.
  4. **Wait for the filing due next, then re-export a full set (5):** BRBR (FY26 10-K), BURL, ROST and TGT (Q3 10-Qs), and FUBO (no periodic filing since 2026-08-05).
     - Each is refused now on comps 48 to 93 days old.
     - A comps-only re-export would put the comps and the Financials on different balance sheets, UBER's failure (row 28).
     - BURL and ROST each also lose a buyback figure to fix 3b.

| Page · committed build (extraction) | Newest periodic filing (EDGAR, 2026-11-12) · next due (last year's) | CIQ Financials / Estimates / comps (file dates, IST) | Re-export | Precheck: exit · regressions · post-spend refusal · panel age, refused from | Last build: $ (run, date) |
|---|---|---|---|---|---|
| **1. Build now, nothing lost** | | | | | |
| CNXC · 10-29 (`2026-10-29.G-D3`) | 10-Q 10-07 (Q to 08-31) · 10-K (2026-01-28) | 10-26 / 10-26 / 10-26; Q3 call held | none | 0 · 0 · 0 · 20d, from 12-08 | $5.41 (`40520189`, 10-29) |
| GOOGL · 11-03 (`2026-11-03.ex-lease-share-cut`) | 10-Q 10-29 (Q to 09-30) | 11-02 / 11-02 / 11-02; Q3 call held | none | 0 · 0 · 0 · 13d, from 12-15 | $4.43 (`05a57bf8`, 11-03) |
| NCNO · 08-18 (`2026-08-16.1`) | 10-Q 08-25 (Q to 07-31) · 10-Q (2025-12-03) | 10-28–29 / 10-28 / 10-28; Q2 FY27 call held | none before the next 10-Q | 0 · 0 · 0 · 16d, from 12-12 | none recorded |
| NKE · 10-29 (`2026-10-29.G-D3`) | 10-Q 10-02 (Q to 08-31) · 10-Q (2025-12-30) | 10-29 / 10-29 / 10-29; Q1 FY27 call held | none | 0 · 0 · 0 · 15d, from 12-13 | $4.60 (`8a695c73`, 10-29) |
| SMPL · 11-04 (`2026-11-04.drawdown-window-at-price-date`) | 10-K 10-27 (FY to 08-29) · 10-Q (2026-01-08) | 11-04 / 11-04 / 11-04; Q4 call held | none now; after the Q1 10-Q for its underwrite (row 36) | 0 · 0 · 0 · 9d, from 12-19 | $2.99 (`29e8038c`, 11-04) |
| TECX · 11-10 (`2026-11-09.order2-pages`) | 10-Q 11-05 (Q to 09-30) | 11-09 / 11-09 / 11-09; no call in the folder | none | 0 · 0 · 0 · 6d, from 12-22 | $1.46 (`3fdddf73`, 11-10) |
| TJX · 10-29 (`2026-10-29.G-D3`) | 10-Q 08-28 (Q to 08-01) · 10-Q (2025-12-02) | 10-18 / 10-18 / 10-18; Q2 FY27 call held | none for a build before 12-01 | 0 · 0 · 0 · 27d, from 12-01 | $4.32 (`8ad38af1`, 10-29) |
| UBER · 11-09 (`2026-11-09.order2-pages`) | 10-Q 11-04 (Q to 09-30) | 11-06 / 11-05 / 11-05; Q3 call held | the comps, owed for its valuation basis (row 28) | 0 · 0 · 0 · 8d, from 12-20 | $6.54 (`46b8ba39`, 11-09) |
| VRRM · 11-09 (`2026-11-09.asof-cut`) | 10-Q 10-30 (Q to 09-30) | 11-09 / 11-09 / 11-09; latest call Q2 (Q3 not in CIQ) | the Q3 call, when CIQ has it | 0 · 0 · 0 · 6d, from 12-22 | $5.27 (`b9fd1442`, 11-09) |
| WLK · 11-09 (`2026-11-09.asof-cut`) | 10-Q 11-04 (Q to 09-30) | 11-09 / 11-09 / 11-09; Q3 call held | none | 0 · 0 · 0 · 6d, from 12-22 | $4.44 (`29d2fce2`, 11-09) |
| **2. Build now, a fix-3b loss to accept** | | | | | |
| AMZN · 11-03 (`2026-11-03.ex-lease-share-cut`) | 10-Q 10-30 (Q to 09-30) | 11-02 / 11-02 / 11-02; Q3 call held | none | 1 · `capital_allocation.buyback_cash` (FY2024, 679d old) · 0 · 13d, from 12-15 | $5.82 (`f4458b22`, 11-03) |
| EPAM · 11-09 (`2026-11-09.asof-cut`) | 10-Q 11-05 (Q to 09-30) | 11-09 / 11-09 / 11-09; Q3 call held | none | 1 · `buyback_avg_price` (2023-Q1, 1,320d) · 0 · 6d, from 12-22 | $4.49 (`53365700`, 11-09) |
| LLY · 11-03 (`2026-11-03.ex-lease-share-cut`) | 10-Q 10-29 (Q to 09-30) | 11-03 / 11-02 / 11-02; Q3 call held | none | 1 · `buyback_shares` (2021-H1, 1,959d) · 0 · 13d, from 12-15 | $3.03 (`ac8b8b71`, 11-03) |
| MCK · 11-05 (`2026-11-05.input-record`) | 10-Q 11-04 (Q to 09-30) | 11-05 / 11-05 / 11-05; Q2 FY27 call held | none | 1 · `buyback_avg_price` (2020-Q3, 2,232d), `buyback_shares` (FY to 2020-03, 2,415d) · 0 · 8d, from 12-20 | $7.40 (`d4304414`, 11-05) |
| NFLX · 11-05 (`2026-11-05.input-record`) | 10-Q 10-21 (Q to 09-30) · 10-K (2026-01-23) | 10-28 / 10-28 / 10-28; Q3 call held | none | 1 · `buyback_avg_price` (2011, 5,428d) · 0 · 16d, from 12-12 | $5.55 (`56f6a840`, 11-05) |
| V · 11-09 (`2026-11-09.order2-pages`) | 10-K 11-05 (FY to 09-30) · 10-Q (2026-01-30) | 11-09 / 11-09 / 11-09; Q4 call held | none | 1 · `buyback_avg_price` (to 2015-06, 4,151d) · 0 · 6d, from 12-22 | $4.15 (`bdf37011`, 11-09) |
| VITL · 11-09 (`2026-11-09.asof-cut`) | 10-Q 11-03 (Q to 09-27) | 11-09 / 11-09 / 11-09; Q3 call held | none | 1 · `buyback_shares` (2019-03/04, 2,751d) · 0 · 6d, from 12-22 | $2.59 (`d7e1ac46`, 11-09) |
| **3. Re-export a full set now** | | | | | |
| IT · 08-18 (`2026-08-16.1`) | 10-Q 11-03 (Q to 09-30) | **07-20–21** / 07-30 / 07-30; latest call Q1 | **full set**, with the Q2 and Q3 2026 calls | 1 · 0 · freshness, comps 106d (07-29) | none recorded |
| MVST · 09-17 (`2026-08-16.1`) | 10-Q 11-09 (Q to 09-30) | **08-13** / 08-13 / 08-13; latest call Q2 | **full set**, with the Q3 2026 call | 1 · 0 · freshness, comps 92d (08-12) | none recorded |
| ORKA · 10-26 (`2026-10-09.3`) | 10-Q 11-09 (Q to 09-30) | **09-01** / 10-26 / 10-26; no call in the folder | **full set** | 1 · `leverage_survival.interest_coverage`, `quality.interest_coverage` (#872) · 0 · 20d, from 12-08 | $1.25 (`fee45da9`, 10-26) |
| PARR · 10-26 (`2026-10-09.3`) | 10-Q 11-04 (Q to 09-30) | **09-17** / 09-17 / 09-17; latest call Q2 | **full set**, with the Q3 2026 call | 1 · 0 · freshness, comps 57d (09-16) | $2.71 (`921d6fa7`, 10-26) |
| WERN · 09-17 (`2026-08-16.1`) | 10-Q 11-09 (Q to 09-30) | **08-19** / 08-19 / 08-19; latest call Q2 | **full set**, with the Q3 2026 call | 1 · 0 · freshness, comps 86d (08-18) | none recorded |
| **4. Wait for the next filing, then a full set** | | | | | |
| BRBR · 10-26 (`2026-10-09.3`) | 10-Q 08-04 (Q to 06-30) · FY26 10-K (2025-11-18) | 09-22 / 09-22 / 09-22; Q3 call held | full set after the FY26 10-K, with its Q4 call | 1 · 0 · freshness, comps 52d (09-21) | $1.79 (`d9ef21bc`, 10-26) |
| BURL · 10-26 (`2026-10-09.3`) | 10-Q 08-27 (Q to 08-01) · Q3 10-Q (2025-11-25) | 09-28 / 09-28 / 09-28; Q2 FY27 call held | full set after the Q3 10-Q, with its Q3 call | 1 · `buyback_avg_price` (2015, 4,210d) · freshness, comps 48d (09-25) | $6.53 (`6de30ce0`, 10-26) |
| FUBO · 08-18 (`2026-08-16.1`) | 10-Q 08-05 (Q to 06-30); none since | 08-12 / 08-12 / 08-12; latest call 08-05 | full set after its next periodic filing | 1 · `capital_structure.covenant_term_rows` (#652), `quality.free_cash_flow` (#817) · freshness, comps 93d (08-11) | none recorded |
| ROST · 10-29 (`2026-10-29.G-D3`) | 10-Q 09-01 (Q to 08-01) · Q3 10-Q (2025-12-10) | 09-28 / 09-28 / 09-28; Q2 FY27 call held | full set after the Q3 10-Q, with its Q3 call | 1 · `buyback_shares` (to 2025-11-01, 374d) · freshness, comps 48d (09-25) | $2.24 (`2b562803`, 10-29) |
| TGT · 10-26 (`2026-10-09.3`) | 10-Q 08-28 (Q to 08-01) · Q3 10-Q (2025-11-26) | 09-28 / 09-28 / 09-28; Q2 FY27 call held | full set after the Q3 10-Q, with its Q3 call | 1 · 0 · freshness, comps 48d (09-25) | $3.07 (`59d556d2`, 10-26) |

- **Reading the table.**
  - A **full set** is every export kind the page reads, per its input record: Financials (Annual and Quarterly), Estimates, comps, Customers and Suppliers, Key Developments and Profile, plus Credit Health where the folder holds one and every call since the last one held.
  - **"From"** is the precheck's own date: a paid build on or after it is refused on panel age. The panel is the comps export's TEV date (`valuation.implied_expectations.tev_as_of`) on all 27.
  - **"Call held"** compares the newest call's date, from its file name, with the filer's newest 8-K item 2.02.
  - **Re-export now** means the Financials file date is older than the newest 10-Q or 10-K filing date. The freshness guard does not check this: ORKA passes it on comps dated 10-23 while its Financials are from 09-01.

**THE COST, AND A PROPOSED CAP.**
- **The series** holds a written build for 22 of the 27, summing to **$90.08** at each one's last recorded cost. FUBO, IT, MVST, NCNO and WERN have none, so each is priced at the median of the 7 builds since 2026-11-09 ($4.44; the range is $1.46–$6.54).
- **At last cost**, all 27 come to **$112.28**.
- **The code has grown since.** Across the 12 names with two or more written builds, the last cost over the first runs **+5% to +86%, median +25.5%**. The prompt and digest changes since (#1019, #1023) are not yet in any recorded build.
- **The expected cost is therefore last cost × 1.255:**

  | Batch | Pages | At last cost | Expected (× 1.255) | Proposed cap (+20%) |
  |---|---|---|---|---|
  | Groups 1 + 2: build on today's exports | 17 | $76.93 | $96.55 | **$116** |
  | Group 3, after its re-export | 5 | $17.28 | $21.69 | $26 |
  | Group 4, after its filing and re-export | 5 | $18.07 | $22.68 | $27 |
  | **All 27** | 27 | $112.28 | **$140.91** | **$170** |

- **What the cap does not cover:**
  - **A refused re-roll**, which costs one more build. It happened 3 times in the series (CNXC, LLY and NFLX in October, $13.14), and a failed MNST build cost $3.33.
  - **A growth larger than the median.** GOOGL grew 86% and SMPL 69%, so per-batch caps, set as each batch is ready, are safer than one cap for all 27.

**WHY.** A combined rebuild follows fix request 2, and it is paid. Re-exports are the operator's manual step and the usual bottleneck. Before any spend, the operator needs to know:
- which pages are ready;
- which exports to pull;
- which losses to accept;
- what it should cost.

**HOW VERIFIED.**
- **The precheck's own output, per page.**
  - 10 exits are 0 and 17 are 1.
  - 14 regressions on 11 pages: AMZN 1, BURL 1, EPAM 1, FUBO 2, LLY 1, MCK 2, NFLX 1, ORKA 2, ROST 1, V 1, VITL 1.
  - 9 freshness refusals.
  - 0 materiality or drawdown refusals.
  - Every log opens with the spreadsheet reader's warnings that an `.xls` export's size is "not 512 + multiple of sector size". These are the reader's warnings on CIQ's files, not a failure.
- **Attribution, by the note each regression prints.**
  - "no current figure — the latest … covers …" is fix 3b (#930), on 10 regressions on 9 pages.
  - "an older period is never read in its place" is #872 (ORKA's 2).
  - FUBO's two name #652's exhibit guard and #817's stale-annual guard; its page (`2026-08-16.1`) predates both.
- **The store holds two years of bars for every page.**
  - The base is S5's backfilled clone (`docs/records/2026-11-11-rebuild-prep-prechecks-on-twenty-pages.md`), whose GOOGL, BURL, LLY, MCK, NFLX, ROST, TGT and TJX bars start 2024-11-12.
  - UBER and V had 69 bars there, from 2026-08-05, so their 52-week and 180-day figures would have read as false regressions. They were backfilled on the scratch copy first: `vinci refresh UBER V --aggs --start 2024-11-12 --end 2026-11-10`, 2 Polygon calls, 500 bars each, nothing restated.
- **Nothing was written outside the scratch copies.**
  - The primary's `data/vinci.db` was never opened.
  - The CIQ folder was read through a symlink.
  - The scratch worktree is a detached `68bd4b33`.

**BOUNDARY.**
- **Code:** `main` at `68bd4b33`, in a detached scratch worktree.
- **Pages:** all 27 committed under `data/dossiers/` at that commit.
- **Store:** S5's backfilled clone plus the UBER and V backfill. The price frontier is 2026-11-10 for all 27, and no bar after it was fetched.
- **CIQ:** the primary checkout's `data/manual/ciq`, read only, as it stood on 2026-11-12 at about 16:00Z. Export dates are file modification dates in IST.
- **Filings:** EDGAR submissions read on 2026-11-12. "Last year's" filing is the 10-K or 10-Q a filer filed between 2025-11-12 and 2026-01-31.
- **Costs:** `usd` from the 44 files under `data/snapshots/assembly_runs/` at `68bd4b33` (2026-10-26 → 2026-11-10), at list price, `claude-opus-4-8`. Growth is each name's last written build over its first.
- **Live calls:** SEC 3,030, EFTS 37, FINRA 7, Polygon 16 (2 backfills and 14 ticker references), Tiingo 0. They are counted as cache files written in the scratch worktree after the cache clone, prechecks and filing reads together.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0 of LLM. The run took about 52 minutes of the machine's shared SEC budget (16:09–17:01Z) for the prechecks, plus the filing reads.
- **The precheck compares presence and some values, never the synthesis.** A paid build can still differ from it where the paid draw decides, such as the 19c guard or `capital_structure.maturity_event`.
- **The expected cost is a measured growth applied to measured costs**, not a fit. Five of the 27 are priced at a median, because no build is recorded for them.
- **The table is today's.** Exports and filings move: TJX's panel ages out on 12-01, and the Q3 10-Qs for BURL, TGT and ROST are due late November to mid-December.
## Amendments

### 2026-11-13: MVST leaves the rebuild, so group 3 is IT, ORKA, PARR and WERN

- **The ruling.** The operator, 2026-11-12, verbatim: *"we want to drop/remove MVST altogether
  from our list for future as well"*. MVST's page left the corpus with it
  (`docs/records/2026-11-13-mvst-retired.md`), so the rebuild covers 26 pages, not 27. The body
  above is as measured on 27.
- **Group 3 is IT, ORKA, PARR and WERN**, four pages, each owing a full set now. MVST's row
  ("full set, with the Q3 2026 call") is no longer owed.
- **The cost, by this record's own rule** (last cost × 1.255, then +20%):
  - MVST had no recorded build and was priced at the $4.44 median. That median is of the 7 builds
    since 2026-11-09, none of them MVST's, so it is unchanged for FUBO, IT, NCNO and WERN. So
    four of the 26 are priced at the median, where the body above says five of the 27.
  - Group 3 at last cost is $4.44 (IT) + $1.25 (ORKA) + $2.71 (PARR) + $4.44 (WERN) = $12.84.

  | Batch | Pages | At last cost | Expected (× 1.255) | Cap (+20%) |
  |---|---|---|---|---|
  | Groups 1 + 2 | 17 | $76.93 | $96.55 | $116, unchanged |
  | Group 3, after its re-export | 4 | $12.84 | $16.11 | **$19** (was $26) |
  | Group 4, after its filing and re-export | 5 | $18.07 | $22.68 | $27, unchanged |
  | **All 26** | 26 | $107.84 | **$135.34** | $162.41 (was $169.09 on 27, proposed as $170) |

- **No approval changes here.** The $170 cap was approved in batches of $116, $26 and $27 (as
  relayed in this amendment's build brief). By the rule, group 3's batch needs $19 of its $26, and
  the three batches sum to $162. Whether to lower a cap is the operator's call.

### 2026-11-13: the operator marks coverage, so the rebuild is 10 pages at about $46

- **The ruling.** B's note on issue #1004 (issuecomment-6847554747, 2026-11-13 08:05Z) gives the operator's coverage marking. The operator approved it, verbatim *"go ahead"*, accepting B's table from issuecomment-6847522000 unchanged. Recorded in `docs/records/2026-11-13-fix2-bookkeeping-batch-8.md`.
- **Active and rebuilt (10),** by this record's groups:

  | Group | Pages | At last cost |
  |---|---|---|
  | 1, build now | GOOGL, NCNO, SMPL, TJX | $16.18 |
  | 2, a fix-3b loss to accept | EPAM, LLY, VITL | $10.11 |
  | 3, on the operator's 2026-11-12 re-exports | IT, WERN | $8.88 |
  | 4, after its FY26 10-K and a full re-export | BRBR | $1.79 |
  | **All 10** | | **$36.96** |

  - NCNO, IT and WERN have no recorded build and are priced at the $4.44 median, as above.
  - With this record's ×1.255 allowance the 10 come to $46.38 (36.96 × 1.255 = 46.3848; B's note rounds it to about $46.39).
  - Group 2's three losses are accepted (operator, 2026-11-13, verbatim *"accept all three"*, issuecomment-6847662066): EPAM's `buyback_avg_price` for 2023-Q1, LLY's `buyback_shares` for 2021-H1 and VITL's `buyback_shares` for 2019.
- **Active, no rebuild now: VRRM.** Its AVOID is scored on 2026-12-15 from prices, and its 11-09 page is newer than its Q3 10-Q.
- **Watch, no paid rebuild (15):** AMZN, BURL, CNXC, FUBO, MCK, NFLX, NKE, ORKA, PARR, ROST, TECX, TGT, UBER, V and WLK.
  - Their pages stay as committed, and no re-export is owed for them.
  - Of group 1, CNXC, NKE, TECX, UBER and WLK leave the rebuild; of group 2, AMZN, MCK, NFLX and V, whose losses are not incurred; of group 3, ORKA and PARR; of group 4, BURL, FUBO, ROST and TGT.
  - Six keep known errors until they go active: UBER (STATE rows 28 and 34); WLK, PARR, AMZN and NFLX (row 34); ORKA (row 35).
  - A watch name goes active on an underwrite, a machine proposal, the screen admitting it to the queue's top 20, or the operator's say-so.
- **The cost line.** The body's $140.91 on 27 pages, and the amendment above's $135.34 on 26, price pages the rebuild no longer builds. It now spends about $46 against the approved $170 cap (batches of $116, $26 and $27), which stands. The body is as measured.
