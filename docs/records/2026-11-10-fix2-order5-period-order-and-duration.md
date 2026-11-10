---
status: open
date: 2026-11-10
prs: []
supersedes:
superseded-by:
---

# Fix request 2, order 5, the CIQ reader's RA-D5 and V1-O2: period columns are read in time order, and a column's stated duration is read. No page moves

**WHAT.**
- **RA-D5** (`ciq_sheets.period_columns`, `_est_cols`, `_listing_rating`). Sheet order was read as
  time order:
  - growth was taken between neighbouring columns;
  - the estimate base was the last fiscal-year column;
  - a trajectory ran left to right;
  - the Estimates "current" year, the forward years and the next quarters were the first FY or FQ
    columns by position;
  - the listing's recommendation was read from column 1, assumed to be 'Current'.

  With the period columns reversed (document 7's "reordered period columns"), SMPL's FY23 revenue
  growth read -7% where it is +6%, its EPS revisions named FY 2033, its trajectory ran from 2026
  back to 2015, and its recommendation read "no Trends block headed with SMPL".
  - A Financials header's period columns now come in time order (`period_columns`): within each
    fiscal calendar by the end each header states, with a fiscal year before an LTM ending the
    same day; the calendars by their latest end. A calendar holding an undated column keeps the
    sheet's order, and a calendar with no dated column keeps its place among the others.
    `_fin_periods` and `_trajectory_series` read it, so every summary, ratio panel, trajectory and
    LTM pick follows it.
  - `margin_trend`'s margin series reads the same order as the absolute series beside it (review
    round 0: reversed, the two halves of one field ran in opposite directions).
  - The Estimates FY and FQ picks go by the year and quarter each label states ('FY 2027',
    'FQ3 2027'). Where one label states none, the sheet's order stands.
  - The listing's 'Current' column is found by its header.
- **V1-O2** (`header_period`, `stated_months`). The parser read the quarter token and not the
  duration, so '6 months FQ2/CQ4 Nov-30-2025' was the quarter 'Q2-26' to every label, same-quarter
  match and LTM sum.
  - A column stating 6 or 9 months through a quarter is now a year-to-date period: kind "YTD", no
    quarter, labelled '6M-26'. So is any other duration but 3 or 12 months (a 4-month stub reads
    '4M-25', review round 0, where it would have been a fiscal year).
  - QoQ is taken only between two quarters. In the annual summary a year-to-date column takes no
    growth, even beside another (review round 0: '9M-25' against '6M-25' read +8%), and it is no
    estimate base.
  - The LTM sum and the same-quarter YoY already read only kind "Q".

**WHY.** Document 15, order 5: latent silent defects shown on mutated or constructed inputs
("reordered period columns"; "6- and 9-month columns labelled as quarters"); "each is a passing
test".

**HOW VERIFIED.**
- **RA-D5, before.** SMPL's, LLY's, V's and AMZN's exports were mutated in memory: on the
  Financials statement sheets from the period header down, and on the Estimates Trends, Guidance,
  Revisions and Surprise sheets from the first period row down, every row's cells after column 0
  were reversed. At `origin/main` (`bfedbac9`), 11 of 34 CIQ readers moved, each on 1 to 4 of the
  4 folders: the annual and quarterly summaries, the trajectory, the return ratios, both revision
  lines, `forward_consensus`, the consensus view and stats, and the guidance pair.
- **RA-D5, after.** On the same four folders, 2 of the 34 move under reversal: `guidance_bridge`
  and `revenue_guide_lohi`. That is RA-D4, the same-day guide picked by column position, which
  #967 fixes. It is not touched here, since #967 edits the same walk.
- **V1-O2.** SMPL's latest quarter, and a synthetic quarter, restated in memory as '6 months': the
  column reads '6M-…', and its QoQ and YoY read "— (basis)" and "—". At `origin/main` it read
  'Q…' with a QoQ of a half year against a quarter.
- **Fail first.** `tests/test_ciq_period_order_and_duration.py` has 18 tests. 14 fail on
  `origin/main`'s `vinci/`, run in a tree of their own with shims for the two new helpers
  (sheet order; no duration). The 4 that pass there are the negative pins: a calendar with an
  undated column keeps the sheet's order, so does a calendar with no dated column, so does an
  Estimates label stating no year, and a 3-month column is still its quarter.
- **No page moves.** 34 CIQ readers give the same output at `origin/main` and here on all 36
  folders. Under reversal on all 36, the branch moves only the guidance pair (`guidance_bridge` on
  21, `revenue_guide_lohi` on 13), RA-D4's read as above. No synthesis request changes.

**BOUNDARY.**
- The exports under the primary checkout's `data/manual/ciq/` on 2026-11-10: 36 folders, 72
  Financials exports.
- The header census: every Financials sheet states "Order: Latest on Right" (864 sheets), none has
  a dated column out of order within a fiscal calendar, and of the 11,132 period-header cells, every
  one with a quarter token states "3 months".
- The mutations are in memory.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- Two columns with the same end in one calendar keep the sheet's order. No rule can place them,
  and none is on disk.
- A year-to-date column is no quarter, so a semi-annual filer's quarterly table shows its halves
  with no QoQ or YoY. Reading a half-on-half change would be a new rule.
- The anchor bridge's period kind (`ciq_balance`) reads anything that is not LTM or FY as a
  quarter-like None, as before.
- **Extraction version** `2026-11-10.period-order-and-duration`; the drift pins are re-pinned.
