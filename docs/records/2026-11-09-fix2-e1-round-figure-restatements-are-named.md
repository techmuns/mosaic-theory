---
id:
status: open
date: 2026-11-09
prs: []
supersedes:
superseded-by:
---

# A round figure is not a coarse one: a restatement is told from a re-rounding at no coarser than a figure's second significant figure, a per-share one at the cent (TeamNostra fix request 2, RE1-D6). 70 → 35 of 1,769 changes unnamed on the fixtures; 0 of 28 frozen pages move

**WHAT.**
- `vinci/edgar/concepts._same_figure` decides whether a later filing RESTATED a figure or only
  re-reported it at another precision. Its readers:
  - `superseded`;
  - `filed_at`'s "restating … first filed …";
  - the EDGAR fallback's "restates" notes;
  - the SBC line's restatement note;
  - the filed tie-break's restatement date.
- companyfacts carries no `decimals`, so precision is still read from each value's trailing zeros.
  Two limits are added:
  - **never coarser than the value's second significant figure**: 900,000,000 is read as stated
    to $10 million, not $100 million;
  - **a per-share value (`unit` containing "/") at the cent, or finer where its own digits
    are**: 3.3 is read as 3.30, and 0.05 as stated to the cent, not to a tenth of one (the
    significant-figure limit would read it to 0.001 and name 0.054 a restatement of it; review
    round 0 — no per-share pair on the fixtures reads differently either way).
- A zero carries no precision of its own, and the other figure's decides. Two equal figures are
  the same figure.
- `superseded` passes the point's unit. The tie-break (`dossier/filed_tiebreak.py`) is not edited,
  so it passes none: it gets the significant-figure limit, not the cent one. It reads LTM
  money lines, not per-share ones.

**WHY.**
- **The reproductions (TeamNostra's notes, RE1-D6), all "the same figure" before:**
  - 200,000,000 / 180,000,000;
  - 3,000,000,000 / 2,600,000,000;
  - 0.40 / 0.38;
  - −0.10 / −0.12.
- **Real ones on the committed fixtures**, each named now and unnamed before:
  - **HLF's re-audit** (its 10-K/A of 2013-12-16): FY2011 diluted EPS 3.30 → 3.32, and Q4 2012
    1.05 → 1.00.
  - **Verra Mobility's 10-K/A** of 2021-05-17: Q3 2019 diluted EPS 0.11 → 0.10.
  - **NFLX's FY2015 10-K**: long-term debt at 2014-12-31 restated from $900,000 thousand to
    $885,849 thousand, the shape of issuance costs netted under ASU 2015-03.
  - **MCK's Dec-2014 quarter**: operating income $780 million in its 10-Q, $800 million in the
    next year's.
- **Why not compare exact values**, TeamNostra's other suggestion. That would name precision-only
  re-reports, which the fixtures hold in number:
  - AMZN's FY2015 depreciation, first filed as "$4.9 billion", later as 4,949 million;
  - Visa's AFS securities, 6,267 million → "$6.3 billion";
  - HLF's quarterly net sales, 618,633 thousand → 618.6 million in a later table;
  - #875's review case, −69,075,000 → −69,100,000.

  The review of #875 ruled these the same figure on purpose.
- **Why a second significant figure.** A filing that re-rounds a figure still states it to at
  least two ("$4.9 billion", "$69.1 million"). A one-significant-figure value is the one
  trailing-zero guess with no evidence behind it: it is as consistent with "stated in millions,
  happened to be round" as with "stated to the hundred million". And a per-share figure is stated
  to the cent, which `_amount` already assumes when it prints one.

**HOW VERIFIED.**
- **Fail first.** `tests/test_restatement_precision.py` on `origin/main` `6fbbb4a2`:
  - The 5 real restatements failed on substance (`superseded` returned None).
  - The 3 precision-only guards passed.
  - The rest failed on the new `unit` keyword.

  After the fix, all 19 pass (one added in review round 0), and so do the existing `test_edgar_fallback_provenance_and_sign.py`
  (with #875's rounding pin) and `test_filed_tiebreak.py`.
- **The corpus, whole.** All 31 fixtures in `tests/fixtures/companyfacts`, every later filing
  against its period's first, the old rule copied beside the new:

  | population (30 non-test fixtures) | old rule | new rule |
  |---|--:|--:|
  | 1,769 changes > 0.5% from the first filing: read as the same figure | 70 | 35 |
  | 802 non-zero changes ≤ 0.5%: named as restatements | 257 | 261 |
  | 9 periods first filed as zero: judgement changed | — | 0 |

  - The 4 newly named small changes are each a per-share figure that moved by one cent, for
    example NKE's FY2013 diluted EPS 2.71 → 2.70.
  - With BURL (the 31st fixture): 1,792 changes > 0.5%, and 70 → 35 the same.
- **What the 35 left are.** Each is a two-significant-figure value that the other figure rounds
  to, for example AMZN's "4.9 billion" against 4,949 million, or Visa's 6.3 billion against 6,267
  million. Some may be restatements, for example MCK's June-2014 quarter D&A, 284 → 280 million.
  companyfacts cannot tell them apart; only the instance's `decimals` can (below).
- **The $0 page compare: the 28 pages frozen at `bcda7ce3`.**
  - **Method.** Each page is cut at its price date (`facts.parity.page_cut`). Its companyfacts as
    they stood then come from the fact layer's committed pages snapshot `edgar-4f3207f4da9fb71a`
    (`FactStore.companyfacts_as_of`) for 26 pages. The other two come from an SEC cache copy cut
    there:
    - BURL from a worktree cache fetched 2026-11-04;
    - MCK from one live read on 2026-11-09. Its body is 804 bytes longer than the copy MCK's page
      recorded on 2026-11-05 (sha256 `6b1b194f…`), and the rows filed by the 2026-11-04 cut were
      compared.
  - **Readers compared.** For every point of every tag, `superseded` and the tie-break's
    `_restated_on`, under the old rule and the new.
  - **Result.** 373 points read differently across the 28 companies' companyfacts. **None is cited
    on any page:**
    - 0 of 28 pages carry a `filed_at` citation of a point that moved. The matcher is sensitive:
      it finds the 15 points the pages do cite this way, on AMZN, GOOGL, MCK, NFLX and SMPL, and
      none of those moved.
    - The SBC line, which cites no accession, was read directly: on all 28 its served figure and
      its revenue denominator are named the same under both rules.
  - **So no page moves.** None needs a $0 refresh or a paid rebuild for this change.
- **The version.** Row `2026-11-09.restatement-precision`, because the rule can move a figure a
  future page cites. Re-pinned with `tests.test_extraction_version_drift --repin`.
- **The full offline suite** ran green before commit (`bin/commit`).

**BOUNDARY.**
- **Fixture counts:** `tests/fixtures/companyfacts/*.json` at `6fbbb4a2`, 30 files (BURL left
  out, as TeamNostra's scan did) or 31 with it.
  - **Population:** every (taxonomy, tag, unit, start, end) group with a value, an end and a filed
    date; each later filing (`filed` after the group's first) against the group's first filing.
  - **The bands:** relative to the first value. A first value of zero is counted apart.
  - TeamNostra counted 1,768 changes > 0.5% on the same 30 files; this scan counts 1,769. Its
    script was not run.
- **Page compare:** the 28 `data/dossiers/*/dossier.json` at `bcda7ce3`, run 2026-11-09.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Up to 35 restatements of a two-significant-figure figure can still go unnamed**, MCK's
  284 → 280 perhaps among them. That is TeamNostra's "70" halved, not closed. *To close it:* read `decimals` from
  each filing's XBRL instance, one instance per accession. That is the stronger fix, at a fetch
  per filing. Proposed, not built.
- **A precision change to one significant figure is now named as a restatement.** Beyond the
  per-share ones, 21 of the corpus's pairs are newly named:
  - some are restatements (NFLX's debt, MCK's quarter, NKE's 782 → 800 million pre-tax income);
  - some look like re-roundings, for example TJX's Q1 FY2023 depreciation, first filed
    218,000,000 and then 200,000,000.

  The note reads "restating 218,000,000 first filed …", which is what the filings say.
  *Falsifier:* a page reader who checks a named restatement and finds it a re-rounding to one
  significant figure.
