---
id: 2026-10-16-split-detector-reporting-precision
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# A split restated on cents is still a split — `share_basis_change` reads factors at their reporting precision

**WHAT.** `vinci/screens/assemble.py::share_basis_change` reads a split from a filer's own
restatement: two periods restated by the same factor. "The same" meant within 2% (`_SPLIT_TOL`).
EPS is filed to the cent, so a small restated figure carries more error than that on rounding
alone, and two real splits were missed:

| Split | Period | As first filed → restated | Factor | Gap |
|---|---|---|---|---|
| NVIDIA 2024 10-for-1 | FY2023 | 1.74 → 0.17 | ×10.24 | 2.05% apart |
| | FY2024 | 11.93 → 1.19 | ×10.03 | |
| Pegasystems 2025 2-for-1 (shares 85.1M → 171.1M) | FY2023 | 0.73 → 0.37 | ×1.97 | 2.2% apart |
| | FY2024 | 1.11 → 0.55 | ×2.02 | |

The fix:

- **Two factors agree** when they are within 2% (unchanged) OR the ranges their stated figures allow
  overlap (`_factor_range`; a figure is known to half a cent, or half its own last decimal when
  finer).
- **Three guards keep it from reading splits that are not there:**
  - the 2% is NOT stacked on the ranges;
  - a restatement that crosses zero never counts, because a split rescales and never turns a
    profit into a loss;
  - a ratio too coarse to state a factor counts for nothing: 0.01 → 0.02 allows anything from
    ×1 to ×5 (`_SPLIT_PRECISION`, 10%).
- **With two splits in one series, the LATEST is reported**, since today's figures sit on it.

**WHY — what it changed on the decision path.**
- **PEGA reached the screen.** The 2026-09-22 run:
  - passed it at G3 ("P/E at 11%ile of trailing range");
  - scored its multiple axis 0.577, for priority 0.647 and rank 44 of 289.
- That percentile divided split-adjusted prices by pre-split EPS. Under the fix:
  - G3 is NOT_EVALUATED with the split as its stated reason, as PATK, IVR and WIX already are;
  - the name is still admitted;
  - the multiple axis is UNKNOWN and earns no credit (the ranker's own rule), giving priority
    0.531 and about rank 100.
- **The committed queue keeps the old rank until the next screen run** (STATE §5.0 row 32 (9)).

**HOW VERIFIED.**
- **On the screen's own population.** All 162 names with a G3 P/E percentile or a split refusal in
  the committed 2026-09-22 run, re-read on live SEC companyfacts ($0) under main's code and this
  change.
  - Main reproduces the committed run's three refusals exactly (IVR, PATK, WIX).
  - This change adds one: **PEGA**, verified from its own filings above.
  - Two names change only their full-history factor, the latest split now reported first: ACI
    2.11 → 2.09 and SFBS 3.0 → 2.0. Neither is in G3's window.
- **On the committed fleet** (29 companyfacts fixtures, full history and windowed): **no change.**
  On the way, a stacked tolerance briefly read SMPL's 2021 accounting restatement as a ×1.84
  split: FY2018 0.96 → 0.51, FY2019 0.56 → −0.31. The sign rule and the no-stacking rule were
  added for it; both are pinned.
- **Known splits on live data:**
  - NVDA: G3 window None → 10.13.
  - AVGO, LRCX, SMCI, CMG, WMT: already detected, unchanged.
  - AAPL and TSLA full history: 7.0 → 4.0 and 5.0 → 3.0, the latest of each pair of splits.
- **A measurement corrected.** `test_share_basis_trend` pinned NFLX's weighted-average share series
  as returning a "confidently wrong 7.0x". It was NFLX's 2015 7-for-1, found first, which was also
  hidden on cents (×7.12 and ×6.97). Read latest-first, the series states the 2025 10-for-1, as
  EPS does. The pin and the docstring in `vinci/dossier/mechanical.py` are updated; the guard
  stays keyed on EPS.
- **Tests:** 10 in `tests/test_split_basis_reporting_precision.py`.
  - NVDA and PEGA real filings, frozen: detected at their G3 windows, and the premise that their
    factors really are more than 2% apart.
  - PEGA's percentile refused at the field G3 and the ranker read.
  - The negatives: SMPL, cents restatements, a restatement across zero, ranges that only come
    near.
  - Latest-first on NFLX; the precision rule.
  - 8 mutants, all killed; one first-pass survivor (the stacking) closed with its own pin.
  - The 19 existing split pins still pass.
- **Full gate:** ruff clean, `mypy --strict vinci` clean, `pytest -m "not network"` 5681 passed, 514 skipped.

**BOUNDARY.**
- Code: main 8afbe671 against this change.
- Population: the committed screen run `data/snapshots/screen_runs/2026-09-22-01.jsonl`, its G3
  window (reference − 1825 − 470 days). Companyfacts were read 2026-10-16.
- Rank effect: computed from the committed `ranked_queue.jsonl` axes, as the ranker combines them
  (unknown axis = 0.0, weight 0.2). It is not a re-run of the screen.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Detection is now wider by the reporting precision.** Two unrelated restatements whose cents
  ranges overlap would read as a split and refuse a percentile, with a false note.
  - Bounded by the sign rule, the no-stacking rule and the 10% precision floor.
  - Measured: none on the fleet or the 162-name population.
  - *Falsifier: a G3 split refusal on a name whose filings show no corporate action.*
- **Found while building the theme desk's five-year P/E** (PR #734, which guards itself
  independently). That PR's record first said the fund rule missed AVGO and LRCX the same way.
  It did not: over the fund's window it catches them. The theme panel's narrower two-year window
  holds one restated year, below the two-period minimum. Corrected on #734.
