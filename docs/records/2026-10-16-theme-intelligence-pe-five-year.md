---
id: 2026-10-16-theme-intelligence-pe-five-year
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — P/E against five years of its own history, and the per-share basis it is never measured across

**WHAT.** The operator, on 2026-10-16, asked to "build the five-year P/E history", after adding a
Tiingo key. On the "Is it priced?" panel (display only):

- **Five years where they hold** (`market.deep_history`, `pe_five_or_two`).
  - Polygon serves two years. Tiingo's RAW closes and split factors fill the three before them.
    - The closes are split-adjusted here: a split's own day already trades on the new basis.
    - They are rebased onto Polygon's prices by the median ratio over at least
      `OVERLAP_MIN_DAYS` (20) overlapping trading days.
    - The join is REFUSED unless every overlapping day agrees within 0.5%. That catches a split
      Tiingo did not record, or two sources that disagree.
  - A company listed for less than five years gets no five-year range.
  - Each percentile shows "· 5y" or "· 2y"; where five years were not used, it says why.
- **Tiingo spend is bounded.**
  - A span is quarter-aligned and in the past, so it is cached for good.
  - A run requests at most `TIINGO_PER_RUN` (45) spans it does not hold; the rest say "fetched on a
    later run". The free plan allows 50 requests an hour (tiingo.com/about/pricing, 2026-10-16).
  - The key travels in a header, never in a URL, the cache or a log.
- **The per-share basis guard** (`basis_breaks`), beside the fund's own rule. It reads only
  filings known by the date. It flags:
  - an annual EPS a later filing restated by ×1.5 or more;
  - a share count that moved ×1.5 or more between cover pages.
  A range across such a change is refused. Today's P/E is refused too when the share count moved
  after the EPS in use was filed: a split not yet restated in a 10-K.

**WHY — a fund bug found on the way.**
- Before building, I checked for existing work, so nothing was spent twice:
  - git history, every branch, searched for tiingo, five-year and own-history P/E, plus a
    code-history search for the Tiingo client;
  - uncommitted code and Tiingo caches in all 57 worktrees;
  - open PRs and live sessions.
  - Nothing found. The fund's own five-year Polygon bars (main checkout's `data/vinci.db`,
    2021-07 → 2026-08-05) are behind the isolation rule, and are frozen at the split basis of
    their fetch date.
- **The anomaly.** The first pilot run gave NVIDIA a five-year percentile (82nd) through its 2024
  10-for-1 split. The fund's `share_basis_change` needs two restated periods within 2%:
  - FY2023 1.74 → 0.17 is ×10.24 (cents rounding);
  - FY2024 11.93 → 1.19 is ×10.03;
  - they differ by 2.05%, so it returns None.
- AVGO and LRCX (2024 10-for-1s) were missed for a DIFFERENT reason (corrected before merge). Over
  the fund's own window the rule catches them (×10.00). The panel's two-year window holds only one
  of their restated years, below the rule's two-period minimum. So #731/#733's **two-year**
  percentiles for NVDA, AVGO and LRCX were wrong too: older P/Es ten times too low.
- The fund's cents miss (NVDA, and PEGA's 2025 2-for-1 on the screen) is fixed in #735.
- `basis_breaks` refuses all three. The fund's detector is decision-path code, so it is left for
  its own PR: a task was spawned with the reproduction.

**HOW VERIFIED.**
- **Real runs** (live Polygon, SEC and Tiingo; $0).
  - J.P. Morgan exposures as of 2026-10-14: META five-year 60th percentile (77th over two), MSFT
    24th over five. Tiingo and Polygon agree exactly over 53 overlapping days (ratio 1.0000).
    AMZN and GOOGL fall back to two years: 2022 splits, refused by the fund's rule.
  - Pilot copy, same date: 21 five-year and 6 two-year percentiles. NVDA, AVGO, LRCX, SMCI and CELH
    are refused, each with the restated figures or the share-count jump.
    - Cost: 39 Tiingo requests on the first run (under the cap), 0 on every re-run (cache).
- **Tests:** 16 in `tests/test_theme_intelligence_pe_five_year.py`:
  - split adjustment;
  - the join, the rebase, and a split Tiingo records inside the overlap (adjusted, not refused);
  - the refusals: two disagreeing sources (1% off, an unrecorded split), a short overlap, an
    unfetched span, a listing younger than five years;
  - nothing after the date read;
  - the request budget, the raw close, and caching for good;
  - NVIDIA's real filings (frozen): the fund rule misses, `basis_breaks` finds both signals, only
    filings known by the date are read, the range is refused today, today's P/E is refused in
    September 2024;
  - five-else-two with its label, end to end through the market step.
  - 17 mutants, all killed; 2 first-pass survivors closed.
- **Full gate:** ruff clean, `mypy --strict vinci` clean, `pytest -m "not network"` 5752 passed, 515 skipped.

**BOUNDARY.**
- Code: this branch on #733 (`claude/theme-intelligence-market-extended`).
- Prices: Tiingo spans fetched 2026-10-16 for as-of 2026-10-14 (2021-10-01 → 2024-12-31,
  quarter-aligned); Polygon 2024-10-16 → 2026-10-14.
- Pilot copy: md5 5fcc240d…, 13 ACTIVE theses.
- The 57 worktrees: as `git worktree list` showed them, 2026-10-16.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The first run of a quarter spends up to 45 Tiingo requests**; later runs in the quarter, none.
  On GitHub Actions the cache does not persist and the key is not set. That run reads two years
  and says so, unless `TIINGO_API_KEY` is added as a secret.
- **The basis guard refuses some valid ranges.** A share count that moved ×1.5 through an
  all-stock merger rather than a split refuses the range too (e.g. LNTH's five years). The cell
  says which change it saw.
- **Not fixed here:** the fund's `share_basis_change` cents miss — fixed separately in #735.
