---
id:
status: open
date: 2026-10-28
prs: []
supersedes:
superseded-by:
---

# The screen reads each name's bars only up to its reference date, so a `vinci screen --ref <past>` replay draws G1 off that day's close, not the store's latest

**WHAT.** `vinci/screens/run.py` gains `_bars_to(store, internal_id, reference_date)`, which returns
the stored bars on or before the reference date. `screen_universe` reads every name's bars and the
benchmark's through it. That is the screen's only read of prices, so one cut reaches every reader
after it:
- the record (`build_price_record` → `compute_price_features`, `relative_return`,
  `detect_gap_downs`);
- the gate inputs retained with their windows (`_gate_inputs`);
- the fundamentals' P/E range (`enrich_with_fundamentals`).

Before, `compute_price_features` took `bars[-1]` as the latest close and used the reference date
only for staleness and window starts. So it read the store's LATEST bar whatever the date.
Decided by the operator's session on 2026-10-27, from #824's "seen, not fixed".

Two comments that described the old behaviour as safe now say what is true:
`dossier/assemble.py` (the maintenance route's truncation) and the docstring of
`tests/test_maintenance_path.py::test_the_standalone_record_is_truncated_to_its_own_reference_date`.

**WHY HERE, NOT IN `compute_price_features`.** Four callers reach it, and they do not want one
thing:

| caller | bars it passes | wants |
|---|---|---|
| the screen (`screens/run.py` → `build_price_record`) | every stored bar | the reference date's: **the defect** |
| the maintenance route (`dossier/assemble.py` → `build_data_record`) | already cut to the reference date (the IT case) | the reference date's |
| the dossier's price box (`mechanical._stock_info`) | every stored bar | the LATEST stored close, on purpose: `_at_latest_close` prices every "at the current price" reading at the close the box shows |
| `vinci eod TICKER [--ref]` (`cli._cmd_eod`) | every stored bar | the reference date's (same defect, print only) |

A cut inside the feature function would move every re-assembled page's price box back to its
screen date. That is a design change to the dossier, not this fix. So the cut is the screen's,
next to its store read. `vinci eod --ref` is left as it was and reported below.

**HOW VERIFIED.**

1. *Pinned first, red on main.* `tests/test_as_of_properties.py` gains two things. Both were red
   on main's code (all 24 cases) and are green with the cut:
   - `test_the_screen_never_reads_a_bar_after_its_reference_date`, 23 names × 6 examples. It runs
     the REAL `screen_universe` (ingest stubbed, EDGAR UNKNOWN) on a store holding the committed
     bars. The retention rows it writes at d must equal those from a store holding only the bars
     to d, however the bars after d are changed.
   - `test_amzn_replayed_at_2025_12_31_reads_g1_off_that_days_close`. On main, G1's input was
     stamped 2026-10-16.

   *Mutants.* Removing the cut turns both red. Over-cutting (`<` for `<=`, dropping the bar ON the
   reference date) passes the property, because both sides go through the same cut, and fails the
   AMZN pin. That gap is why the pin exists.
2. *Real store, real screen.* Each run below used `screen_universe` on a copy of a real store. It
   has prices 2021-07-01 → 2026-10-16 for 2,797 names, and its universe snapshot of 2026-10-16
   holds 2,065 names. Ingest was stubbed (no network) and EDGAR stubbed (all fundamentals UNKNOWN,
   so only the price gates differ). Settings: staleness 5 d, default thresholds, CARRY routing.
   "Main" is the screen path as on main: `vinci/screens`, `vinci/eod`, `vinci/store` and
   `vinci/schemas` are unchanged from `56500bb1` to `3ab4747f`.
   - **Live reference (2026-10-16, the store's frontier): byte-identical.** The 2,065 retention
     rows hash to the same SHA-256 (`f7e960b69ed21acd…`) under main and the fix. G1/G2
     survivors are 434 under both.
   - **Past replay (2026-08-24, 53 days before the frontier), the same 2,065 names.**
     - **G1's outcome changes for 319 names:**

       | G1 on main | G1 with the fix | names |
       |---|---|---|
       | PASS | FAIL | 262 |
       | FAIL | PASS | 45 |
       | FAIL | NOT_EVALUATED | 6 |
       | PASS | NOT_EVALUATED | 6 |

     - **G1/G2 survivors: 391 → 318.**
     - **G1 input dates.** On main, 1,642 G1 inputs were stamped after the reference date, 1,641
       of them on 2026-10-16. With the fix there are none: 1,630 are stamped 2026-08-24 and 435
       carry no value.
     - **The 12 NOT_EVALUATED** read "no drawdown (insufficient price history)": under 330 days
       of bars by 2026-08-24. Main drew a 52-week high for them from bars that came later.
   - **AMZN replayed at 2025-12-31** (outside the cap band, so run alone):

     | | last close | drawdown | 52-week window | G1 |
     |---|---|---|---|---|
     | main | $250.00, dated 2026-10-16 | −12.95%, stamped 2026-10-16 | "spans 654d over 450 bars" | FAIL |
     | with the fix | $230.82, dated 2025-12-31 | −10.74%, stamped 2025-12-31 | 365d over 251 bars | FAIL |

**BOUNDARY.**
- *Population:* the 2,065 names of the store's 2026-10-16 universe snapshot, re-recorded at
  2026-08-24 in the copy so the same names are screened. The store copy is a SQLite backup of a
  worktree's `data/vinci.db` (prices to 2026-10-16), taken 2026-10-27.
- *Window:* one past reference date, 2026-08-24, 53 days before the store frontier. A replay
  further back moves more names, and one nearer moves fewer.
- *Gates:* G1 and G2 only. G3 is UNKNOWN under the EDGAR stub, so the rollup is not a production
  rollup.
- *Units:* names; outcomes as `per_gate` records them.
- *Code:* main at `3ab4747f` (screen path unchanged since `56500bb1`) against this branch.
- *Measured:* 2026-10-27/28.

**SEEN, NOT FIXED.** `vinci eod TICKER --ref <past>` (`cli._cmd_eod`) prints "features as of
<ref>" off every stored bar, the same lookahead in a print-only face-validity command. It is a
one-line cut with its own pin, kept out of this decision-path PR.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A replay of the committed past screen runs would now read differently**, in the direction of
  what was knowable on their dates. Committed screen runs are not rewritten, and the defect did
  not reach them. Across all 8 committed runs in `data/snapshots/screen_runs/` (2026-07-29-01 …
  2026-10-16-01), 0 of 42,467 stamped price inputs (`drawdown_from_high`, `rel_ret_vs_market`,
  `last`) are dated after their run's reference date (checked 2026-10-28). Each run was produced
  with the store's frontier at its own date. The live run is byte-identical.
- **The dossier still reads its price box at the latest close.** That is by design
  (`_at_latest_close`), and its "52-week" stamp names the window it actually covers.
