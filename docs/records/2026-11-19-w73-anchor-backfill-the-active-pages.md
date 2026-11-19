---
id:
status: open
date: 2026-11-19
prs: []
supersedes:
superseded-by:
---

# W73's $0 anchor backfill of the active pages: 8 of 9 move and every screen value stands. Each multiple is now labelled with its own close and passed by the event rule at the page's date. SMPL (+29.6%) and VRRM (−24.2%) carry the price-drift flag. LLY's `valuation_basis` multiple takes its own close's date (2026-11-02), and the test allowance for it is deleted. NCNO is unchanged; BRBR and GOOGL are excluded ($0, artifacts + tests)

**THE RULING.** W73's own ruling ("Approve with corrections", 2026-11-19, relayed by coordinator B) made the backfill a SEPARATE $0 artifact PR after the code PR. That PR is #1144, merged as `bc1c0e16` on "Merge once green". B's brief:
- the active pages, with BRBR and GOOGL out;
- LLY restated, and `tests/w73_lly_expected.py` and every call to it deleted;
- the build store refreshed to the latest close first;
- never run after an `own-history-refresh` that puts a newer export on a page (W68 refuses that close).

**WHAT.**
- **The run.** `vinci anchor-backfill --tickers EPAM,IT,LLY,NCNO,SMPL,TJX,VITL,VRRM,WERN` ran on main `bc1c0e16`, then `frontend/build.py`. Each mirror in `frontend/dossiers` is byte-identical to its page.
- **8 pages move:** EPAM, IT, LLY, SMPL, TJX, VITL, VRRM and WERN.
  - Leaf by leaf against main, each moves only `anchor.*` (14 to 19 leaves) and one appended `layer_refreshes` entry (4 leaves; LLY 5).
  - The one leaf outside the anchor is LLY's `valuation_basis.current_multiple.as_of`, 2026-10-30 → 2026-11-02. That is W65's finding B: the multiple is dated by its own close, no longer by the comps TEV's date.
  - The anchor leaves are W73's:
    - the event rule's verdict on the close (`multiple.close_stale`, `multiple.close_note`), on 8 pages;
    - the drift measure (`multiple.close_drift`), on 8 pages, and its note on 2;
    - the split's dated wording (`gap_split.read`, `basis` and `arithmetic` lines), on 7 pages;
    - the mid-cycle sentence (`midcycle_gap.read`), on 3 pages;
    - one leverage line;
    - `computed_at`.
- **Every screen value stands.** Every priced base moves +0% (EPAM $173.28, IT $136.91, LLY $820.15, SMPL $11.37, TJX $136.20, VRRM $1.34, WERN $39.93). VITL stays lease-refused and publishes none. No `applicable`, `recipe_hint`, multiple value, median, net debt or `ev_gap` moves.
- **Each close passes the event rule at its page's date.** Nothing the rule counts was filed after the close and on or before the page's price date (2026-11-11, VRRM's 2026-11-17):

  | page | close | the stock since that close | flagged |
  |---|---|---:|---|
  | EPAM | 2026-11-05 | −1.7% | no |
  | IT | 2026-11-11 | 0.0% | no |
  | LLY | 2026-11-02 | +1.9% | no |
  | SMPL | 2026-10-27 | +29.6% ($9.75 → $12.64) | **yes** |
  | TJX | 2026-08-28 | +1.0% | no |
  | VITL | 2026-11-06 | −0.5% | no (no value published) |
  | VRRM | 2026-11-06 | −24.2% ($2.19 → $1.66) | **yes** |
  | WERN | 2026-11-09 | −0.2% | no |

- **What each page reads.** The multiple row is "Multiple at the latest close, own history | … | close of <date> · nothing reported after it by the page's close of <date> · <the flag, past 10%> · median … beside it, not used". The method row and subtitle drop "today's", and the split reads "at 5.1x (the 2026-10-27 close)". Each md moves in those places, in the header's "layers refreshed" stamp and in the rendered refresh entry.
- **NCNO is unchanged** and left byte-identical. It is an R2 page whose anchor stops before the multiple leg.
- **The allowance is deleted.** `tests/w73_lly_expected.py` goes, and its 8 call sites return to their pre-W73 lines (`ac3c9479`), because LLY's page now carries the date the code derives. It is a separate commit from the pages: the pages' commit leaves the allowance in place, where it changes nothing once LLY carries 2026-11-02, so each commit is green on its own.

**WHY.**
- No committed page carried W73: it merged as code only, by ruling.
- The active pages therefore still said "today's multiple" for a close up to 75 days old. They carried W62's cadence verdict, now retired. Two pages printed no drift flag although their stock had moved more than 10% since the close.

**HOW VERIFIED.**
- **The inputs, checked before the run:**
  - **The CIQ exports.** For all 9 names, every file on Drive (`data/manual/ciq/<T>/`) carries exactly the sha256 its page stamps (`inputs.ciq`), file for file; none is a link. They were read in place and never copied. BRBR and GOOGL differ: their pages predate the exports now on Drive.
  - **The price store.** It is a copy of #1132's impact store (2,827,554 rows, frontier 2026-11-10), refreshed by `vinci refresh` (Polygon grouped-daily) for the 9 names. That added 6 sessions, 2026-11-11 to 2026-11-18, and 54 bars. The run was at about 2026-11-19 18:41 UTC (its grouped-daily cache files are stamped 18:40–18:41 UTC), before that day's 21:00 UTC close, so 2026-11-18 is the latest close.
  - **The store's control.** Each page's own-date bar equals its `stock_info.price` on 8 of 8 pages; 7 of those bars came from the refresh.
  - **EDGAR** companyfacts and submissions were fetched 2026-11-19.
- **Dry run first.** 9 processed: 8 CHANGED, 1 unchanged (NCNO), every priced base +0%. The written run matched it.
- **The leaf diff** of every page against main `bc1c0e16` is as listed in WHAT. 0 other leaves move.
- **The full offline suite** passed on each commit (`bin/commit`), the CIQ folder and the store set aside so it ran as CI does.

**FOUND ON THE WAY: TJX's close is its 10-Q's own filing date** (passed to W82 and to B).
- TJX's ex-lease close is 2026-08-28, and its 10-Q (`0000109198-26-000048`) was filed that day.
- The observation behind it (`lease_basis.observations[38]`) is priced 2026-08-28 on the balance sheet of 2026-08-01, with LTM EBITDA $8,903M for the four quarters to that date. It is struck on that 10-Q itself.
- The date-only rule passes it: a filing on the close's own day is not after it. A rule counting same-day filings as after (W82's question) would refuse a multiple built from the very filing.
- BRBR's 2026-11-18 case is the other kind: a CIQ 4pm close beside a release that may have come after the bell.

**BOUNDARY.**
- **Roster:** `data/coverage_roster.jsonl` at `bc1c0e16`, the latest row per ticker: 11 active and 15 watch, 26 committed pages.
- **Code:** main `bc1c0e16` (W73, #1144), 2026-11-19.
- **Count:**
  - Processed: 9 active pages (11 active less BRBR and GOOGL).
  - Moved: 8 pages. Unchanged: 1 (NCNO).
  - Excluded: 2 (BRBR, GOOGL). Left as committed: the 15 watch pages.
- **The flag:** 2 of 8 pages carry it (SMPL, VRRM), at the 10% line ruled "Proceed at 10%". The move is page price ÷ the store's bar on or before the close.
- **Leaves:** counted over each page's `dossier.json` against `origin/main` at `bc1c0e16`, list members by index.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **BRBR and GOOGL still read the pre-W73 words**, until BRBR's rebuild (A's) and GOOGL's paid rebuild (the operator's $6 cap, a separate PR). BRBR's close was a same-day case, which waits on W82.
- **The 15 watch pages carry W73** only when each is re-derived.
- **TJX passes on a 75-day-old close** because nothing it counts was filed between 2026-08-28 and 2026-11-11. Its Q3 release (8-K item 2.02, 2026-11-18) postdates its page, so at a build priced after 2026-11-18 the rule refuses it (`tests/test_w73_dated_multiple.py::test_tjx_is_refused_once_it_has_reported_where_the_cadence_passed_it`).
