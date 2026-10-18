---
id: 2026-10-16-theme-intelligence-market-context
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — "Is it priced?": a labelled market-context panel beside the verdict, never read by the research action

**WHAT.** The operator asked on 2026-10-16 for item 2: "a clearly labelled 'is it priced?'
market-context panel beside the verdict". For a thesis's exposures it shows price against the
200-day average, drawdown, valuation against its own history and consensus revisions. It is
evidence for the human, never a model verdict, and the evidence gates stay as they are. Built:

- **`market.py`** is the only module of the package that reads prices.
  - It reuses the fund's own helpers rather than new ones:
    - Polygon `daily_bars` (cached);
    - `relative_return` — both legs end on their common last bar;
    - `pe_current_and_percentile` — only EPS filed by each day is read.
  - It adds two small point-in-time figures the fund did not have:
    - the close against its 200-day average;
    - the close against its highest CLOSE of the 52 weeks to the date.
  - For each exposure the count takes (verified listed companies, attached ETFs, indices and
    baskets), as of a date, it shows:
    - price position;
    - 3- and 12-month return against SPY;
    - P/E and its percentile among its own daily P/Es.
  - Consensus revisions read **"not held"**, with the reason.
  - An index or basket with no traded ticker is a row that says so.
  - A failed request is said on its row and as a `MARKET_DATA_FAILED` WARN issue, never filled.
- **Stored apart from the thesis.** An append-only `market_contexts` table (registry schema
  **v7**), written by a new $0 step: `python -m vinci.theme_intelligence market --as-of D`. It
  makes no model call and no new thesis version.
- **Shown, labelled first.** The label reads "MARKET CONTEXT — evidence for your judgement; never
  read by the research action". It appears:
  - on the desk's thesis page, directly under the thesis and its Why box, before Who is exposed;
  - in the card's section 06, beside "Consensus / valuation: not assessed";
  - in the Markdown record.
  "How each figure is measured" is on demand, and open in print.
- **The wall, opened for one module.** `tests/test_theme_intelligence_isolation.py`:
  - `market.py` alone may import the six fund modules it names, and must;
  - only `pipeline.py` imports `market.py`;
  - the rule's input (`ThesisState`, `compute_priority`) has no market, price, return or
    valuation field.

**WHY these choices.**
- **The Polygon plan serves exactly two years.** Probed 2026-10-16: SPY and IGV, 501 bars each,
  2024-10-16 → 2026-10-15. The comments in `vinci/eod/client.py` (2 years) and
  `screens/assemble.py` (5 years) disagree; the probe says two.
  - So the P/E percentile states the window actually held, never the helper's nominal five years.
  - It answers only once 450 daily P/Es are held: about as-of 2026-08 onward, on this plan.
- **The fund's split guard was applied to the window held.** `pe_current_and_percentile` refuses
  a range when a share-basis change falls inside "the range plus the EPS reach-back". Its range is
  nominally five years, so a 2022 split refused AMZN's and GOOGL's range even though every price
  held is post-split. `market.py` passes only the EPS periods the prices held can consume (first
  close less `MAX_EPS_AGE_DAYS`). That is the helper's own documented rule. A split inside the
  window still refuses; both cases are pinned.
- **Consensus revisions are not held.**
  - The only estimates are the fund's CIQ exports. They are snapshots as of their export date,
    not readable as of a past date, and exist only for the dossier names. 35 ticker folders
    hold an Estimates file in the main checkout, 2026-10-16, while `ciq.py` says 26.
  - No programmatic source was found under: finnhub, fmp, zacks, yfinance, alphavantage, ibes,
    factset, refinitiv, benzinga, Polygon financials.
  - Licensed CIQ figures on the theme desk would also be a new surface, which is the operator's
    call.

**HOW VERIFIED.**
- **Real run 1: the J.P. Morgan acceptance copy, as of 2026-02-09**, live Polygon and SEC, $0.
  - All 4 hyperscalers and IGV are priced. The software index and the "S&P 500 AI Usage" basket
    are rows that say "not priced".
  - **Face validity against the source itself:** the article says IGV traded "over 20% below
    its 200-day moving average". The panel computes **−20.4%** for the same date.
  - P/E: META 28.8×, AMZN 29.1×, GOOGL 30.0×, MSFT 30.3× (MSFT on FY2025 EPS, 224 days old).
    Every percentile is "not held — only 329 P/E points (< 450)".
- **Real run 2: the same exposures as of 2026-10-14**, about 500 bars held. The P/E percentiles
  answer:
  - META 77th, AMZN 29th, GOOGL 65th, MSFT 26th;
  - AMZN and GOOGL answer only after the split-window fix.
- **Real run 3: the pilot copy as of 2026-10-14.** 13 active theses, and **12 have nothing to
  price**: their exposures are sectors only. The 13th names "Magnificent 7", a basket with no
  ticker.
- **Tests:** 14 in `tests/test_theme_intelligence_market_context.py`.
  - The pure figures, positive and negative.
  - Point in time: a later crash or high, and a later 10-K, change nothing.
  - The split window, both ways.
  - The fixture thesis's rows, and failure handling.
  - End to end: stored, shown labelled beside the verdict on the desk, card and Markdown.
  - The run cutoff: a later context is not shown as of an earlier run.
  - Append-only, and v6 → v7 migration.
  - The research action is identical with no context, a crashing market and a soaring one.
  - Plus 3 new isolation pins.
- **Mutation:** 22 production mutants and 4 boundary mutants, all killed. One first-pass
  survivor (a widened 52-week window) closed with an older-high case.
- **Full gate:** ruff clean, `mypy --strict vinci` clean, `pytest -m "not network"` 5716 passed, 515 skipped.
- **Two group-4 tests pinned the schema at exactly 6.** They now assert what they test: the
  indexes exist at the current schema, and a v5 registry migrates to the latest. The next
  migration will not redden them.

**BOUNDARY.**
- Code: this branch on top of #730 (`claude/theme-intelligence-exposure-gate`, fc294c11).
- Price window: 2024-10-16 to the as-of, probed 2026-10-16.
- J.P. Morgan copy: `acceptance/final-jpm/registry.db` (built 2026-10-12), reassessed on #730's
  code, then priced as of 2026-02-09 and 2026-10-14.
- Pilot copy: md5 5fcc240d4b087d2feb1f81e6d6fabc3c, 13 ACTIVE theses, priced as of 2026-10-14.
- CIQ count: Estimates files in the main checkout's `data/manual/ciq/`, 2026-10-16.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0 per run.** No model call. Polygon is paced at about 4 requests a minute, one request per
  ticker plus SPY, with a 24-hour cache.
- **Most pilot theses show an empty panel today.** Sector-only theses have no ticker to price.
  - Pricing the enrichment step's company hypotheses (already labelled EXTERNAL HYPOTHESIS) would
    fill it.
  - That is the operator's call. It is not built, because it would put prices beside names the
    source never named.
- **The weekly run does not price.** The market step is separate, like enrich. The Actions
  workflow would need `POLYGON_API_KEY` as a secret to include it.
- **Anchoring.** A price panel beside a verdict can anchor the reader, just as the machine
  proposal can (CLAUDE.md's accepted risk). It is labelled first, carries no colour or score,
  and no rule reads it. *Falsifier: actions or overrides that track the panel's numbers.*
- **Registry v7.** Code before this change refuses a v7 registry. The pilot's checkout must
  move to this code when it lands (`theme-intelligence-pilot-worktree` memory).
