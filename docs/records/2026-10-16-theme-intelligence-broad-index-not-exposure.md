---
id: 2026-10-16-theme-intelligence-broad-index-not-exposure
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — a whole-market index or a market indicator the source attaches is named on every surface and never counted as the thesis's exposure

**WHAT.** Two operator rulings, 2026-10-16.
- "Exclude broad indexes": the code review of #730 found that an attached S&P 500 counted as a
  thesis's exposure. A whole market is not an exposure.
- "Add the indicator exclusion": the Cboe 3-month implied correlation index counted too. It is a
  measure computed from option prices, not something anyone holds.

- **Whole-market index.** `cards.is_broad_market` recognises a whole-market index (membership set
  by geography and size alone) or a fund that tracks one.
  - The index is matched on its WHOLE normalised name in `BROAD_MARKET_INDICES`. "The S&P 500
    Index" and "S&P 500" match; "S&P 500 Software Index" and "S&P 500 Utilities" do not.
  - The fund is matched by a listed ticker in `BROAD_MARKET_FUNDS` (SPY, VOO, QQQ, IWM, EWZ …).
- **Market indicator.** `cards.is_market_indicator` recognises a measure of volatility,
  correlation, dispersion or skew.
  - It is matched on whole words of the name by `MARKET_INDICATOR`: implied correlation, implied
    volatility, a volatility index, VIX, MOVE, the COR1M–COR1Y tenors …
  - An index or fund that SELECTS stocks by volatility ("S&P 500 Low Volatility Index", "MSCI USA
    Minimum Volatility Index") holds stocks and is not one.
- **One definition, every path.** `exposure_instruments` leaves out both classes. The count (F6,
  the exposure condition), the desk, the card, the dashboard and the market panel all read it.
  `broad_market_instruments` / `market_indicators` return them; `CountedExposures.broad` /
  `.indicators` carry them.
- **Named, never dropped.**
  - Card section 05, HTML and Markdown, gets two headings, each shown only when it has a row:
    - "Broad market indices the source attaches — the whole market, not counted as this thesis's
      exposure";
    - "Market indicators the source attaches — a measure (volatility, correlation), not a holding;
      not counted as this thesis's exposure".
  - The desk and the dashboard row say "broad market index — not counted" or "market indicator —
    not counted".
  - When these are a thesis's only instruments, the desk's exposure gate and the card's why-line
    give the reason in one line (`uncounted_words`).

**DOES THIS SELECT ON FORM?** No.
- Both tests key on what the instrument IS: the whole market, or a measure rather than a holding.
- An index and the fund that wraps it are treated alike (S&P 500 and SPY; the VIX and a VIX
  futures fund).
- Both are lists of names and words. A broad index or an indicator written another way still
  counts. That is a recall limit, not a selection on form. A new spelling is added, never inferred.

**Checked against how experts define them (2026-10-16).**
- **Nasdaq-100.** Nasdaq's methodology selects the largest Nasdaq-listed companies outside
  Financials, with no sector rule beyond that. Morningstar puts QQQ in Large Growth, a style
  category, not a sector fund. So it is broad.
- **A single-country index.** MSCI designs its Brazil index to cover about 85% of that market,
  which makes it the whole market of one country, so it is broad. Excluding it means a country
  view cannot pass the exposure gate on its index alone. That is the operator's mandate call.
- **The Cboe correlation index.** Cboe describes it as an option-implied estimate of how closely
  the 50 largest S&P 500 stocks will move together. It is a measure, not a basket.

**WHY — and a correction to the review's example.** The finding said TH-A56902FFB6 (J.P. Morgan,
committed fixture) had the S&P 500 as its only counted exposure. It does not: it also counts a
sector (F6 "0 listed · 1 sector · 1 instrument" on main). The real case where the S&P 500 was the
only exposure is TH-5C3B51DF57 in a local registry copy.

**HOW VERIFIED.**
- **Corpus first.** Every attached instrument on the current version of every thesis in every
  local registry copy: 152 registries, 1,083 current versions, 196 attachments, 11 distinct names.
  - Broad, 48: S&P 500 ×32; Ibovespa, IPC, Colcap and BVL ×4 each.
  - Indicator, 33: the Cboe 3-month implied correlation index, in 33 registries.
  - Still counted, 115: S&P 500 Utilities ×47, IGV ×27, S&P 500 Software Index ×25, Magnificent 7
    ×9, S&P 500 AI Usage ×7.
  - Across EVERY name in those versions, attached or not, the indicator pattern matches only the
    Cboe index. No other name hits.
- **Re-grade, main 11e77e49 vs this branch.** Copies were re-graded by `run_reassess` ($0: no
  fetch, no model call; listing re-checks off on both sides). The population was the 90
  registries whose versions name any of the six, plus both J.P. Morgan fixtures built fresh: 642
  current theses.
  - **37 exposure factors drop instruments. 0 research actions change.**
  - TH-4BC577D53A, the calm-index dispersion regime (35 registries plus the fixture), loses the
    S&P 500 and the Cboe index. It stays RESEARCH NOW on its sectors.
  - TH-5C3B51DF57 goes from "0 listed · 0 sector · 1 instrument" (the S&P 500) to none. It is
    WATCH · on hold before and after.
  - TH-A56902FFB6 drops the S&P 500 and stays WATCH.
  - The Latin America theses TH-3A53B04C0B (Ibovespa) and TH-F4A90F739D (IPC) keep version 1
    under both codes; their stored F6 predates instrument counting. They count 1 and 2 sectors.
- **The live pilot.** No current version attaches either class; the S&P 500 appears only as a
  comparator on TH-FBDC863613. Nothing changes there.
- **Pins.**
  - `test_a_whole_market_index_is_told_from_a_sector_one`: 10 observed names plus 2 constructed.
  - `test_a_market_indicator_is_told_from_a_holding`: the observed Cboe index; constructed VIX
    forms; negatives that select stocks by volatility; observed sector instruments.
  - `test_the_whole_market_is_named_and_never_counted` and
    `test_a_market_indicator_is_named_and_never_counted`.
  - End to end on the committed fixtures:
    - `test_a_thesis_whose_only_instrument_is_the_whole_market_counts_no_exposure` (J.P. Morgan);
    - `test_the_calm_index_regime_names_its_index_and_its_indicator_and_counts_neither` (calm
      index: F6, the action, the card in HTML and Markdown, the desk, the dashboard, and the
      gate and why-line giving both reasons);
    - `test_every_surface_lists_the_instruments_the_count_takes`, extended.
- **Mutation.** 21 mutants, all killed: 12 on the broad half, 9 on the indicator half (including
  the low-volatility guard and the both-reasons line).
- **Suite.** ruff and `mypy --strict` clean; `pytest -m "not network"`: 5799 passed.
- **Preview.** `docs/theme_intelligence/broad-index-2026-10-16/screenshots/` holds:
  - each page collapsed and with every `<details>` opened;
  - section 05 of both cards, expanded.

**ALSO DONE (operator, 2026-10-16: "move the pilot to main").** The pilot checkout moved from
8afbe671 to main 11e77e49.
- The live registry is untouched: schema v5, md5 5fcc240d4b087d2feb1f81e6d6fabc3c.
- It migrates to v7 on its next run or render.
- Proven on a backup copy with main's code: v5 → v7, all 22 tables with every row unchanged, plus
  the new `market_contexts` table.

**ALSO OPEN (found here, not changed).** With both instruments set aside, the calm-index regime
TH-4BC577D53A's only counted exposure in the committed fixture is a "sector" named "at both a
sector and thematic level". That is a phrase from the article, not a sector. It was counted before
this change too, so no action moves here. But the exposure gate passes on extraction debris.

**BOUNDARY.**
- Measured 2026-10-16 on this branch over main 11e77e49.
- Population: the 152 `registry.db` files under the theme-intelligence data folder of the pilot
  worktree, read from backup copies; current versions only.
- "Attachments" = funds, indices and cited baskets in an attaching role (`INSTRUMENT_ROLES`, or a
  cited basket), counted per current version.
- The 90 re-graded registries are those whose stored versions name any of the six as
  `name_as_written`, in any version and any role. That is a superset of those with a current
  attachment; the rest are the check that nothing else moves.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A whole-market index or an indicator spelled another way still counts. Falsifier: a corpus
  survey finding one among the counted instruments.
- A market-regime record whose only attachment is the index or the measure it studies now reads
  "no exposure". That is the rulings' consequence, and it is said on the gate.
- A country view can no longer pass the exposure gate on its country index alone.
