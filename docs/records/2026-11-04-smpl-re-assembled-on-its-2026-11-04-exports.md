---
id:
status: open
date: 2026-11-04
prs: []
supersedes:
superseded-by:
---

# SMPL's page is rebuilt once on the operator's 2026-11-04 CIQ exports, priced after its FY2026 10-K, while its underwrite still waits for the Q1 FY27 10-Q; the first build of the day was held for the 'Fiscal Year Change' reader

**WHAT.** The operator asked on 2026-11-04 for SMPL's page itself to be rebuilt now ("rebuild
SMPL now"), with the underwrite still waiting under STATE §5.0 row 36. Two paid builds ran on
the same 11 exports; only the second is committed.

| | committed 2026-08-18 page | held build `4f30d3a2` | committed build `29e8038c` |
|---|---|---|---|
| code | ext `2026-08-16.1` | main `cfedcb39` | main `05b2529b` (+ #898, #900, #902, #905, #906) |
| cost, calls | none in the series | $2.27, 6 calls | **$2.99, 8 calls**, 0 failed |
| price date | 2026-08-17 | 2026-11-03 | **2026-11-03** ($12.47) |
| lean (draws) | mixed | mixed (5/5) | **mixed (4 mixed / 1 strongly-bearish)** |
| machine proposal | none | none | **none** (mixed; the split draws would withhold too) |
| R1 anchor base $/sh | 44.8347 | 46.4765 | **46.4765** |
| UNTRACEABLE caveats | 0 (predates #859) | 7 | **13** |
| material row, stated? | Asset Writedown LTM −391.9, yes | FY26 −331.0, yes | **Asset Writedown FY26 −331.0, yes** |
| Sourced fields present / lost vs the committed page | 98 present | 12 lost + `ev_bridge` null | **0 lost**; 2 moved to the at-underwrite part, 6 newly present |

- **The R1 anchor base moves +3.7%** on the FY2026 10-K (`0001702744-26-000031`, filed
  2026-10-27):
  - D&A 21.431 (FY2025) → 24.255 (FY2026);
  - net debt ex-lease 273.153 → 208.794 (total debt 347, cash 138, operating leases 50 excluded);
  - LTM revenue 1,392.235 → 1,356.499;
  - EBIT margin median 0.154481 (8 FY) → 0.153855 (9 FY);
  - ex-lease band median 17.924621 (35 closes) → 18.2256495 (34 closes, 2018-04-10..2026-10-27).
  
  The diluted count is still the Q3 FY26 average 89,940,680, beside the cover count 86,861,967
  (2026-10-22). So the page carries `VALUATION_RECIPE_BASIS_CONFLICT` at 3.54%. That is row 36's
  gap, untouched by a CIQ export. `scenarios/SMPL.json` is untouched, and no `scenario-propose`
  or scenario step ran.
- **The drawdown at the underwrite is kept** (#906). The page prints "Drawdown at underwrite
  (2026-08-05)":
  - 2026-04-09 −18.1% and 2026-04-10 −11.5%, both earnings;
  - 8-K `0001702744-26-000010`, filed 2026-04-09, with the FY26 outlook as it stood.
  
  Since the underwrite (2026-08-06 → 2026-11-03) there is no single day of −10% or worse. The
  current-window fields `drawdown_cause.gap_down_dates` and `revised_guidance` read UNKNOWN
  ("no gap-down from 2026-05-07 to 2026-11-03"). The anchor carries both by value.
- **The covenant table is present** (#898): 16 rows, 10 with a value, across the 2018 Repricing
  Amendment (8-K `0001213900-18-003172`) and the 2019 Incremental Facility Amendment (8-K
  `0001104659-19-060856`). The committed page had 19 rows, 14 with a value. The table is an LLM
  draw (the precheck names it "decided by the paid draw, not compared"), and it was not re-rolled.
  Against the committed page:
  - the 2019 exhibit's "Financial-maintenance covenants" (Total Net Leverage ≤5.00x, as an
    investment condition) is now refused by the E5 quote guard, because this draw's value states
    $100,000,000 and its quote does not;
  - five of the model's extra rows are absent: Administrative Agent, quarterly amortization
    ($1,676,470.59), the 0.50% closing fee, the 0.50% MFN protection, and the 2019 exhibit's
    governing law;
  - two are new: the 2018 Amendment Effective Date and the 2018 exhibit's governing law;
  - every other core row has the same status on both pages.
- **The EV bridge is back and agrees with CIQ.** It reads the 2026-08-29 balance sheet, with
  claims of $259.1M against the comps' TEV less market cap of $259.1M. On the scorecard,
  `ev_bridge_vs_ciq_tev` and `net_debt_vs_implied_bridge` confirm, and SMPL has 0 unexplained
  differences on every check.
- **The 13 UNTRACEABLE figures** (#859's trace): 5 in bull points (8.8, 5, 28.9, 13, 29.1),
  6 in bear points (10, −10, 7, 10, 13, 17) and 2 in a decisive-for point (250, 300). Each is on
  the page for the human, and none was re-rolled away.
- **UNREAD PRINT does not clear, and cannot from a page.** `monitor.freshness_row` reads the
  RECORD's evidence date: `scenarios/SMPL.json`'s underwrite, 2026-08-05, or a later
  `[amended …]` tag. It never reads the page. The new day reads
  `SMPL UNREAD PRINT evidence 2026-08-05 (underwrite_date)`, with the 10-K and 8-K of
  2026-10-27, and the held build's run read the same with its page in the tree. Row 36 said these
  filings "postdate the committed page". The cause is the record, and the row is corrected. The
  flag clears at the re-underwrite.
- **The monitor day is new** (RUNBOOKS §j): `data/monitor/2026-11-03.json`, run with no `--ref`.
  The 2026-11-02 day is untouched.
  - The book is on total return.
  - BUY−AVOID is +67.26 pp (price return +67.25 pp), against +73.96 pp on 2026-11-02.
  - SMPL's two rows mark at $12.47: +14.19% and +10.06%, against IWM −4.03% and −7.02%.
  - The newest `newer_filings` date is 2026-11-03 and the newest `last_evidence_date` is
    2026-09-01, both before the run day.
  - There are no "no freshness row" or "evidence dated after" notes.
  - `test_emit_is_deterministic_over_the_committed_corpus` is green on it.

**WHY THE FIRST BUILD WAS HELD.** `4f30d3a2` ran on main `cfedcb39`, and the 2026-11-04
Financials export reaches back to 2015, past SMPL's 2016–17 fiscal-year change. So every
statement header carried an undated "Fiscal Year Change" column. The August and 2026-10-28
exports start at Nov-2016 and carry none. The shared latest-cell reader (#872) refuses to place
a latest column when any header cell is undated. That build therefore:
- lost 12 fields that had values (8 to the marker, `financial_summary.coherence` following them,
  `capital_structure.summary` to a column-order refusal, and the two drawdown fields to the data
  record);
- built no EV bridge, and said nothing about why;
- printed a "Fiscal Y" column.

A census of every CIQ folder on disk (2026-11-04: 37 folders, 222 statement sheets, 4,983
non-empty header cells) found 6 undated cells, all SMPL's. The operator chose option 1: hold the
page, fix the reader, rebuild once. Only `4f30d3a2`'s cost-and-outcome line is committed
(`dd47cc34`), because the series takes every paid run.

The fixes it waited on:
- #900, the marker is no column (`docs/records/2026-11-04-a-fiscal-year-change-is-no-column.md`);
- #898, the amendment exhibits reach the covenant extractor;
- #902 and the field precheck, `vinci dossier precheck`;
- #906, the drawdown anchor.

The columns before the change (the Conyers Park SPAC's `FY16` and the Atkins predecessor's
`FY15`) still print. #900's record measures which statistics reach across the change, and cutting
or labelling them is the operator's ruling there.

**HOW VERIFIED.**
- **Pre-spend, at $0, before each paid build.**
  - The exports passed main's readers: 11 files, 0 unrecognised; all six statements state their
    period type; the newest column is FY26 (2026-08-29) and `filed`; no press-release column; USD
    on all 18 panels; `estimates_as_of` ≥2026-10-29; comps stamped 2026-11-04 at $12.47.
  - The LTM check reads NOT RUN, which is correct right after a 10-K: the newest column is a
    fiscal year and there is no LTM.
  - Before `29e8038c`, `vinci dossier precheck --ticker SMPL` exited 0, with 0 regressions and 0
    post-spend refusals. The two drawdown fields were listed as moved into
    `drawdown_cause.anchor.at_anchor`, and 6 fields as newly present. The paid page matches that
    list exactly, re-derived field by field against main `05b2529b`'s
    `data/dossiers/SMPL/dossier.json` (the 2026-08-18 page).
- **CIQ sha256.** All 11 files are byte-identical from before the first build to after the second.
- **The material row.** `uncited_material_figures` returns [] on the committed page, and the bear
  point states "$331.0M intangible write-down". Its `ref` does not resolve (an UNCITED qa flag),
  and the same point quotes the old LTM $391.9M. The guard's presence check passes; the citation
  is the human's to read.
- **Scorecard.** CIQ source, `data/snapshots/data_quality/ciq/2026-11-05.json`, measured on
  committed inputs (head `026c1b87`, `inputs_match_head` true).
- **Tracking fixture.** `tests/fixtures/companyfacts/SMPL.json` was regenerated
  (`scripts/build_companyfacts_fixture.py SMPL`) and is byte-identical across both builds' days.
  The frozen vintage is unchanged.

**BOUNDARY.**
- **Runs:** `4f30d3a2`, 2026-11-04 07:21:32→07:32:12Z, and `29e8038c`, 2026-11-04
  18:58:07→19:06:54Z. Model `claude-opus-4-8`. Extraction `2026-11-03.ex-lease-share-cut` and
  `2026-11-04.drawdown-window-at-price-date`. 14 calls in all, 0 failed, $5.27 at list price.
- **Draws:** 5 per build. They are tallies, never rates.
- **UNTRACEABLE:** the page's caveats matching "untraceable figure".
- **Field comparison:** every dict carrying `value` and `status` outside lists, across the whole
  page; 108 on the committed page, 116 on the new one. The covenant rows are compared by
  (exhibit, row name).
- **Store:** a copy of the primary's `data/vinci.db` (sha `0263451a…`, bars to 2026-08-11) in
  this session's worktree; the primary was not written. `vinci refresh SMPL IWM --aggs --start
  2021-07-01 --end 2026-11-03`: Polygon served 501 bars each, and both run 2021-06-21..2026-11-03
  (1,350 bars). SMPL has no graph cohort, so no other name was refreshed.
- **Census:** `ciq_sheets._column_date` over the period-header row of each annual and quarterly
  Income Statement, Balance Sheet and Cash Flow in every `data/manual/ciq/*` folder, read
  2026-11-04 at main `cfedcb39`.
- **Monitor:** Polygon grouped-daily, with Tiingo dividends on every leg. The run of 2026-11-04
  ~19:10 UTC, before that day's close, is filed under 2026-11-03.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$5.27,** of which $2.27 buys no committed page. It is counted in the series.
- **The underwrite has not moved.** SMPL carries a fired trigger (initial FY27 guidance below
  ~$1.30B) and a record from 2026-08-05 until the Q1 FY27 10-Q, about early January 2027
  (row 36). The page is current and the record is not, and UNREAD PRINT says so every day.
- **The covenant draw is thinner than August's.** It has four fewer term values, one of them
  refused by the quote guard. The missing rows describe the 2019 incremental term loan, whose own
  row states a July 7, 2024 maturity; whether that loan is still outstanding was not checked. The
  revolver's 2029-12-16 maturity is read separately, off the 10-Q.
