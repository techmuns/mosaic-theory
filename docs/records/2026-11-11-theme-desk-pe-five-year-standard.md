---
id: 2026-11-11-theme-desk-pe-five-year-standard
status: recorded
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# The research desk's P/E column is five years or nothing, and its five-year histories are kept between weekly runs

**WHAT.** The operator, 2026-11-11, on TH-BAA07551ED's "Companies the thesis implies": "why do we
have some names with 2y PE percentile vs some at 5y … it should be same (5y) for all names", and
then "why cant we have 5y for all as standard?" Three changes, all in `vinci/theme_intelligence/`
and its workflow, off the decision path:
- **`market.pe_five_year` replaces `pe_five_or_two`.** The percentile is five years or NOT HELD
  with its reason, never the two years Polygon serves in its place. Today's P/E needs no window
  and is unchanged.
- **The renderer refuses a two-year figure in the column,** now headed "P/E vs own 5y history".
  A context stored before the standard keeps its two-year figures (append-only), so in the cell
  and in "How each figure is measured" it reads "not held — a two-year figure, from before the
  desk's five-year standard".
- **The weekly workflow keeps `data/theme_intelligence/http_cache/tiingo` between runs.** These
  are Tiingo's price histories, and they are restored and saved around the market step: the LLM
  cache's pattern (U31f). The guard that keeps the fetcher's page cache on the runner now allows
  exactly that folder, with a negative pin.

**WHY.** On R-20261110T153023Z-market (175 listed rows, 89 tickers), 104 rows had a percentile:
**57 on five years and 47 on two**, in one column. Mixing windows breaks the comparison the column
exists for. The 47 two-year rows, by cause:

| Cause | Rows | Tickers |
|---|---|---|
| The run's Tiingo budget (`TIINGO_PER_RUN` = 45 new histories a run), with the cache never kept: the row text "a later run fetches it" never came true in CI, and the same 45 were fetched every week | 27 | 21 |
| A stock split inside five years: the fund's rule refuses a range through one | 11 | 2 (AMZN, GOOGL) |
| A restated EPS or a share-basis change inside five years | 8 | 2 |
| Listed under five years | 1 | 1 |

- **29 more rows** had no percentile at all with their five-year fetch also skipped for budget.
- On 2026-11-09 (Actions) and 2026-11-10 (local), the same 21 tickers were on five years.

**HOW VERIFIED.**
- **Pins first, each failing on the unfixed code:**
  - `test_five_years_or_not_held_never_two` (`pe_five_year` did not exist).
  - `test_no_two_year_percentile_reaches_the_five_year_column`, end to end on the real stored
    context of TH-BAA07551ED (fixture `tests/fixtures/ti_market_context_TH-BAA07551ED.json`, run
    R-20261110T153023Z-market). Before the fix it rendered AMZN as "45th pctile · 2y". Now MSFT,
    META and ORCL show five-year figures, and AMZN, GOOGL, EQIX, DLR and VRT are not held, with
    why.
  - `test_the_weekly_actions_run_keeps_its_tiingo_histories_between_runs`: restore before the
    market step, save after it with `always()`.
  - `test_only_the_price_histories_leave_the_runner_never_the_page_cache`: a workflow keeping the
    whole `http_cache` is refused.
- **On the real corpus,** publishing the whole desk from the registry (ea8fb4a6) to a scratch
  folder with this code:
  - 0 cells with a two-year percentile;
  - 147 "not held — a two-year figure…";
  - 173 five-year cells;
  - the old header on 0 pages.

  Main's live desk carries 147 two-year cells (the 47 rows repeat across cards, print cards and
  thesis pages).
- **Code review** (`/code-review high --fix`): 10 findings, 6 fixed by the review and 1 by hand;
  dispositions in the PR. Among the fixes: with no Tiingo key, prices that already cover five
  years are still measured.
- **The suite:** see the PR.

**BOUNDARY.**
- Counts are over the listed rows of R-20261110T153023Z-market (registry 4527c2b1), exposures
  and implied companies together.
- Cell counts are over the scratch publication's HTML (242 files) and the live desk on main
  3da9f3cb.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **The live desk keeps its two-year cells until it is republished.** That waits for the fund
  rule's split adjustment (AMZN, GOOGL; the operator's "Split-adjust EPS, fund rule"), then a
  market run that fetches every history.
- **Quarter rollover.** A span is quarter-aligned, so each new quarter every history is fetched
  again, 45 a run. Until a quarter's histories are all held, some rows say "not fetched this
  run". A name listed under about 5 months asks Tiingo again each run, because its span ends at
  the run's date. The kept cache grows by one span per ticker per quarter. Not fixed here; this
  is pre-existing `deep_history` behaviour, which the review raised.
- **Not fixed here (review):** the renderer's two-year refusal keys on the column's format kind
  ("rank"), so a future rank column would inherit it.
