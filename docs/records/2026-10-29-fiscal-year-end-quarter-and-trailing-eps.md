---
status: shipped
date: 2026-10-29
prs: []
supersedes:
superseded-by:
---

# At a fiscal year end the anchor reads the last 10-Q's quarter, never the 10-K's year, and the P/E caveat reads the year just closed; SMPL's living-page value pins move to its frozen 2026-08-18 page

**WHAT.** Two code fixes and a test move.
- **The share-count selector.** `anchor._latest_point` reads the diluted weighted average behind
  `anchor.diluted_shares`, the cover count's corroboration and `dilutive_increment`. A span longer
  than `QUARTER_MAX_DAYS` (100 days) is no longer a candidate. So between a 10-K and the next 10-Q
  it reads the last 10-Q's quarter, and a filer with no quarter on file gets None.
- **The P/E caveat.** `mechanical._ltm_gaap_eps` feeds the (d) P/E-basis caveat. With no LTM
  column it now reads the last actual column, the year just closed. Actual and estimate columns
  are told apart by the structured `is_estimate` flags, and a table without those flags reads
  nothing.
- **The pins.** Eight value pins read off SMPL's living page, and the bps-guide pin's only witness,
  now read a frozen copy of SMPL's 2026-08-18 page (`tests/fixtures/frozen_pages/`). The living
  pages keep structural invariants, including a new one: on every page, the revenue cross-check
  takes a range that a revenue-line guide states. SMPL's companyfacts vintage is frozen for
  `test_net_debt_one_builder`, as #810 froze NFLX's.

**WHY.** All three were found on SMPL's 2026-10-28 re-assembly (run `6a57e81b`, not committed),
against the FY2026 10-K 0001702744-26-000031, filed 2026-10-27.
- **The year read as a quarter.** The 10-K tags the weighted average over 2025-08-31..2026-08-29
  and nothing shorter, so "the shortest span at the latest end" was the year. The result:
  - `anchor.diluted_shares` read 92,372,473 under the basis "diluted weighted-average (latest
    10-Q)";
  - the cover count was corroborated against the year's basic average;
  - `scenario-propose` refused the page on a 6.34% gap that the year's average made.
- **The silent caveat.** CIQ exports no LTM column while the fiscal year is its latest period, so
  `_ltm_gaap_eps` read None. The (d) caveat went silent beside FY2026's −1.69 GAAP diluted EPS,
  while the page's P/E note still told the reader to "see the P/E-basis flag".
- **The pins.** Value pins on a living page break the TEST-LAYER RULE. The re-assembly turned
  eight red by moving real values: the guide, the calendar date, the TEV, net debt / EBITDA, the
  writedown, the impairment line, and the drawdown guide (twice). It also left the bps pin with no
  witness.

**HOW VERIFIED.**
- **Real run.** SMPL's 2026-10-28 page was re-anchored through `assemble._assembly_anchor` on the
  2026-10-28 SEC cache and CIQ export. The script was the same both times; PYTHONPATH selected the
  code.

  | | main `f2c6e7aa` | this PR |
  |---|---|---|
  | `diluted_shares` | 92,372,473 (2025-08-31..2026-08-29) | 89,940,680 (2026-03-01..2026-05-30) |
  | cover count 86,861,967 against | the year's basic, 6.0% below | the quarter's basic, 3.4% below |
  | `dilutive_increment` | 0, over the year | 0, over the quarter |
  | `anchor_base_value_per_share` | $45.6691 | $45.6691 (both divide by the cover count) |
  | `scenario-propose` template | REFUSED, 6.34% | REFUSED, 3.54% |

  Main's recompute matches the committed anchor block field for field: 0 fields differ. With this
  PR, three fields differ (`diluted_shares`, `shares_outstanding`, `dilutive_increment`), and the
  base does not move.
- **Witnesses on real frozen inputs**, each red before its fix:
  - the selector on SMPL's FY2026 10-K and on WOR's FY2026 10-K (`tests/fixtures/companyfacts/WOR.json`, the same shape, 364 days);
  - the anchor's three share inputs through `compute_anchor`;
  - the caveat on SMPL's FY2026 annual table.
  Negative pins: a year-only filer reads None; an LTM column still wins (−2.08 over FY2025's +1.02); an estimate column is never read.
- **Mutations**, seven, each restored and run in a scratch tree carrying the 2026-10-28 page:

  | mutation | result |
  |---|---|
  | the selector takes the year | 6 red |
  | no LTM column reads nothing | the witness red |
  | the fallback ignores `is_estimate` | the witness and the estimate pin red |
  | the web card prints "bp" for "bps" | the bps pin red, through the frozen witness |
  | the revenue cross-check takes any metric | the new living invariant red |
  | next evidence leads with the trigger | the frozen calendar pin red |
  | a year-only filer is told "no diluted WA tag" again | the year-only pin red |

  The fourth matters most: no living page carries a bps guide on that tree, so only the frozen
  witness could catch it.
- **Corpus.** The selector moves 2 of 31 inputs: the 30 tracking companyfacts fixtures at main
  `f2c6e7aa`, plus SMPL's FY2026 cut.
  - The two that move are SMPL's FY2026 cut and WOR. WOR is a frozen fixture with no page, and
    `test_anchor` reads only its margins.
  - No committed anchor moves.
  - `_ltm_gaap_eps` changes on one committed page: NKE, None → +2.10 (its FY26). The (b), (c) and
    (d) caveats all key on a negative or absent figure, so no caveat moves.

**THE REFERENCE DATE.** Measured; no code change.
- **The two dates on the page.** The maintenance path dates a page at `_fleet_reference_date`, the
  newest screen-run manifest's reference date: 2026-10-16
  (`data/snapshots/screen_runs/2026-10-16-01.manifest.json`). Its bars stop there (SMPL $11.19).
  `_at_latest_close` re-prices the price box and the EDGAR P/E pair at the store's latest close,
  2026-10-27 ($9.75), with EPS as of that day.
- **Why the P/E reads FY2025.** It reads FY2025's +1.02 at either date. At 2026-10-27 the latest
  annual EPS is FY2026's −1.69, filed that day, but `annual_eps_point_as_of` takes the latest
  POSITIVE annual EPS within 470 days (G3's shared reader). A later reference date would not move
  the P/E. The page's own note states this, and the caveat fixed here is what that note points at.
- **Why no re-assembly can be dated on the 10-K.** `vinci dossier` takes no `--ref`, so a page
  dated on or after the 10-K needs a screen run at 2026-10-27 or later. This worktree's store holds
  23 names a day through 2026-10-23 and 4 on each of 2026-10-26 and 10-27 (SMPL, SPY, IWM, MDY).
  There is no whole-market day after 2026-10-16 to screen. That is §5.0 row 31's operator call,
  not a build.

**BOUNDARY.**
- *Real run:* one name (SMPL). Inputs: its 2026-10-28 page, the SEC companyfacts cached 2026-10-28,
  the CIQ export synced 2026-10-28. Code: main `f2c6e7aa` vs this branch.
- *Corpus counts:* `tests/fixtures/companyfacts/*.json` at main `f2c6e7aa` (30 files), plus
  `tests/fixtures/fiscal_year_end/SMPL.companyfacts.json`; the diluted weighted-average tag only.
- *`_ltm_gaap_eps`:* the 27 committed pages at main `f2c6e7aa`.
- *Store counts:* `prices` rows per `bar_date` in this worktree's `data/vinci.db`, 2026-10-12..10-27,
  read 2026-10-29.
- *Gaps:* shares, in percent of the cover count (propose) or of the basic average (anchor).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **SMPL's template is still refused (§5.0 row 36, operator).** At a year end the quarter read is
  a quarter older: SMPL's ends 2026-05-30, and its cover count is dated 2026-10-22.
  `scenario-propose`'s 2% share tolerance (`SHARE_DISAGREEMENT_TOL`) reads a larger gap as
  structural. SMPL's 3.54% is the gap between that quarter's average and the cover count; its basic
  average fell 2.60% from Q2 to Q3 alone (92,343,383 → 89,940,680). The tolerance is a
  face-validity parameter on the R1 path, so it is not changed here.
- **An annual-only filer reads nothing.** A filer with no quarter on file now gets no weighted
  average, and so no corroborated count; its anchor block names the longest span it did find. No
  committed page or real fixture is in that state. A 20-F filer that tags us-gaap weighted averages
  annually only would be: row 4's FPI work should read its count another way, not through the year.
- **One synthetic fixture moved.** `test_band_guards`' facts tagged the diluted average over the
  year only — a shape no 10-K filer's companyfacts has — so its net-debt unit pin lost its
  denominator. The fixture gains the 10-Q quarter beside the year; what it pins is unchanged.
- **Still red on SMPL's 2026-10-28 page with this code** (the page's own PR, after the R1 ruling):
  - the R1 path: 8 `scenario-propose` refusals, the band reference, 3 ev_gap anchor-year pins,
    and 3 `test_propose` value pins;
  - the backfill list, which SMPL leaves (`ANCHORS_AWAITING_BACKFILL`);
  - the P/E corpus pin, until the page is re-assembled on this code. It now SEES SMPL, and demands
    the caveat that the old-code page lacks.
- **Found, not fixed.** `vinci/dossier/dilution.py::_paired_period` keeps the same
  shortest-span-at-the-latest-end rule. Only its own test imports it.
