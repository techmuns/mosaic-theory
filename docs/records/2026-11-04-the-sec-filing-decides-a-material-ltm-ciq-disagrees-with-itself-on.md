---
status: shipped
date: 2026-11-04
prs: [891]
supersedes:
superseded-by:
---

# The SEC filing decides a material LTM that CIQ's two exports disagree on: CELH's row is stated as filed, NFLX's as CIQ's quarterly reading that its containing line confirms, and WAT stays refused

**WHAT.** The operator approved the filing as tiebreaker on 2026-11-04 ("the way an expert team
builds a line from the 10-K and 10-Qs when its data vendor disagrees with itself").
`vinci/dossier/filed_tiebreak.py` now runs at the pre-spend LTM check (`ltm_quarters`), for each
MATERIAL row whose annual-export LTM DIFFERs from its four quarters in the quarterly export. It
decides in one of two ways, and refuses otherwise.

- **Same item** (`MAPPING`). A filed concept states the row's own item. The filer's XBRL is read
  for the same four quarters, as filed by the page's price date (`concepts.facts_as_of`): each
  quarter's 3-month fact, or a longer period less the one a quarter shorter (Q4 = FY − 9M). The
  shorter period is the one filed ON OR BEFORE the longer, so a derived quarter pairs filings of
  one vintage (Codex, round 2). When
  the filed LTM reproduces one of CIQ's two readings within 2% or $0.5M (`ltm_quarters.agrees`, the
  check's own tolerance), the page states the FILED figure.
- **Containing line** (`CONTAINING`; operator ruling 2026-11-04, verbatim: "NFLX: B"). The item is
  filed only inside a wider line. That line's total is never stated as the row. It may only pick
  WHICH CIQ reading the filing supports:
  - CIQ's quarterly component rows of the line, plus the row itself, must reproduce the filed line
    in EVERY quarter of the window, within half a printed million (`BREAKDOWN_SLACK_MUSD` = 0.5 $M,
    the repo's rounding floor);
  - if they do, the page states CIQ's quarterly reading;
  - one quarter that misses refuses.
  It is read only when no same-item concept carries every quarter.
- **What the page gets in either case:**
  - the row's LTM cell holds the stated value (value and display cell);
  - the annual table's `source_ref` names every accession;
  - `financial_summary.filed_ltm` carries `{value, source_ref}`, with `kind`, both CIQ readings and
    each quarter's filing (and, for a containing line, CIQ's breakdown);
  - one main-body caveat, "FILED FIGURE STATED — …" or "CIQ READING CONFIRMED BY THE FILING — …",
    names CIQ's disagreement and the accessions.
- **Otherwise it refuses exactly as before**, and the refusal message adds why the filing could not
  decide. That covers:
  - an unmapped row;
  - a concept missing a quarter;
  - a filed figure far from both readings;
  - a breakdown that misses its line;
  - an EDGAR that will not serve companyfacts (`HttpError`; a throttle, `SecRateLimitedError`,
    still stops the run).
- **All or nothing.** One undecided material row refuses the build.

| CIQ row | same-item concept(s), sign −1 | containing line, sign +1 (CIQ components) |
|---|---|---|
| Restructuring Charges | `RestructuringCharges` | — |
| Other Unusual Items | `RestructuringCharges` | — |
| Merger & Related Restruct. Charges | `BusinessCombinationAcquisitionRelatedCosts`, then `BusinessCombinationIntegrationRelatedCosts` | `NonoperatingIncomeExpense` (Interest and Invest. Income, Currency Exchange Gains (Loss), Other Non-Operating Inc. (Exp.)) |

The first same-item concept carrying all four quarters is THE figure. It is never spliced, never
summed, and never skipped for a later concept that agrees better.

| case | CIQ annual LTM | CIQ quarterly sum | the filings (as filed by the export stamp) | outcome |
|---|---|---|---|---|
| CELH Other Unusual Items, LTM to 2026-06-30 (material) | −418.8 | −405.0 | `RestructuringCharges` **−412.748** = −246.707 (Q3-25) − 80.754 (Q4-25 = FY25 327.461 − 9M 246.707) − 4.427 (Q1-26) − 80.860 (Q2-26) | **stated as filed**; reproduces both readings (1.4%, 1.9%) |
| NFLX Merger & Related Restruct. Charges, LTM to 2026-09-30 (material) | −2,800.0 | +2,800.0 | `NonoperatingIncomeExpense` 45.473 / 2,852.166 / 51.661 / 43.006, against CIQ's quarterly breakdowns 45.5 / 2,852.2 / 51.7 / 43.0 | **CIQ's quarterly +2,800.0 stated**, confirmed in all four quarters (≤0.039 $M) |
| WAT Merger & Related Restruct. Charges (material) | −459.0 | −346.0 | no business-combination concept; `NonoperatingIncomeExpense` for no 2026 quarter | **refused**, as today |
| EPAM Restructuring Charges (not material) | −53.5 | −28.5 | −53.474 | sides with the ANNUAL export |
| CELH Merger & Related Restruct. Charges (not material) | −36.2 | −11.1 | the containing line misses CIQ's breakdown by 2.9 to 22.9 $M in all four quarters | refused |
| BDX Other Unusual Items (not material) | −184.0 | −143.0 | `RestructuringCharges` −693.0 | refused: reproduces neither |
| NKE Restructuring Charges (not material) | −385.0 | −311.0 | no `RestructuringCharges` fact for any of its four quarters to 2026-08-31 | refused: no filed figure |

CELH's filings: 10-Q 0001341766-25-000144 (2025-11-07), 10-K 0001341766-26-000024 (2026-03-02),
10-Q 0001341766-26-000039 (2026-05-07), 10-Q 0001341766-26-000050 (2026-08-06). NFLX's: 10-K
0001065280-26-000034 and 10-Qs 0001065280-26-000138, -000212, -000291.

**NFLX: WHAT THE FILING CAN AND CANNOT SAY.**
- **First build, option A.** The first build left NFLX refused: its $2.8B WBD termination fee is
  filed only inside `NonoperatingIncomeExpense`, its whole "interest and other income" line. The
  brief's rule maps that concept "only where the row is the whole non-operating line", which no
  unusual-items row is. Stated as the row, the line's LTM, 2,992.3, would also carry about 190M of
  interest and currency.
- **The question and the ruling.** The coordinating session was asked: A (refuse), B (a containing
  line that may only pick a CIQ reading) or C (state 2,992.3, advised against). The operator ruled,
  verbatim: "NFLX: B".
- **What the evidence is.** The filed TOTAL is consistent with BOTH exports. The annual export
  reaches the same LTM total (2,992.3 against 2,992.3 filed) by carrying +5,554.7 under Other
  Non-Operating, where the quarterly export's four quarters carry −27.0; its FX row, −58.4 against
  −76.6, differs too. Its −2,800.0 row is offset there. The rule decides on the breakdown QUARTER BY
  QUARTER, which only the quarterly export offers. In Q1 2026, 70.0 − 8.3 − 9.5 + 2,800.0 = 2,852.2
  against 2,852.166 filed. The caveat states all of this on the page, so the reader sees what the
  confirmation rests on.

**NKE AND WAT, AS VERIFIED AT BUILD.**
- **NKE cannot be the case where the filed figure sides with the annual export.** It tags no
  restructuring P&L figure for FY26 or its LTM, only `SeveranceCosts1` 300M FY26 and
  `PaymentsForRestructuring`.
  - The claim in `ltm_quarters`' docstring and refusal message, "NKE's restructuring was the
    quarterly side's error", is therefore confirmed by no filed figure (not changed here).
  - EPAM is the real annual-side case.
- **WAT is a third material refusal on main**, and it stays refused.

**FIXTURE LICENSING — RULED.** Codex's P1 on #891 called the fixture's CIQ cells a reproduction of
licensed tables. The operator ruled, verbatim: "no need to remove fixture or ciq data from main,
under our license we can keep it". `tests/fixtures/filed_tiebreak.json` stays, as does the merged
`tests/fixtures/ciq_ltm_quarters.json`. CLAUDE.md's committable list now names cut-down CIQ test
fixtures, with the date and the words.

**DOES THIS SELECT ON FORM?** (CLAUDE.md, before any new gate.) It adjudicates between two vendor
readings by the primary source, and ranks, grades or weights nothing. One narrow selection is
real: which refused names it can clear depends on HOW the filer tags the item.
- CELH tags it as the item.
- NFLX's sits in a line that CIQ's quarterly rows reproduce.
- WAT and NKE tag no mapped concept for every quarter.
That selection decides only whether a page can be built on a verified figure. A name it cannot
clear is refused exactly as before, so the selection can only leave a name where it was.

**THE BANDS, AND WHY.** Both are set by face validity, never by an outcome.
- **Same item: 2%, or half a printed million.** That is the tolerance at which CIQ is deemed to
  agree with itself (operator ruling 2026-10-30).
  - CIQ copies its figures off the filings, so a line that reproduces neither reading is not shown
    to be the line CIQ read.
  - A wider band would let a neighbouring item stand in for the row: NFLX's containing line sits
    6.4% from +2,800.0.
  - A narrower one would refuse ordinary restated comparatives.
  - It also catches the mapping misreading a name. EPAM's Other Unusual Items (−17.8 / −16.8) is not
    its restructuring, which sits in CIQ's own Restructuring row, so the −53.5 it would read is
    refused.
- **Containing line: 0.5 $M in every quarter.** That is the repo's rounding floor, half the unit
  the page prints. CIQ copies each component off the same filing, so a breakdown that is the filed
  line lands well inside it (NFLX: at most 0.039 $M), and one that misses is not that line (CELH:
  2.9 to 22.9 $M).

**HOW VERIFIED.**
- **Real run at $0** (no assembly, no LLM): main's check and the tiebreak over all 37 folders of the
  operator's Drive `manual/ciq`, beside SEC companyfacts fetched 2026-11-04. Main's check refuses
  CELH, NFLX and WAT. On this branch CELH and NFLX are decided (table above, each caveat as
  printed in the PR) and WAT refuses with the reason added.
- **Pins** (`tests/test_filed_tiebreak.py`, 29 tests) run on `tests/fixtures/filed_tiebreak.json`.
  - **The fixture.** Derived cells cut from the real exports through the real decode path into the
    real `CiqBundle`, plus SEC's companyfacts cut by concept with each concept's rows unmodified
    (`scripts/build_filed_tiebreak_fixture.py`). Drive shas (annual/quarterly):
    - CELH 0e47f54b97/9f492d7a75; NFLX 8ae9f12b10/512a1e9a0a; WAT 0e6c6973b5/6a23022579;
    - EPAM 04c788d495/7baf86ffeb; BDX b525583374/5489c75ea7; NKE f4bc343292/5a10072a9a.
  - **Positive:**
    - CELH and NFLX through `assemble._settle_ltm_refusals`, each from the LTM cell and the demanded
      19c figure to the caveat rendered by `render._flags_section`;
    - NFLX's figure is the quarterly reading, never the line's total;
    - EPAM's annual side.
  - **Negative:**
    - a breakdown missing by more than rounding (NFLX's real Q1 cell moved +0.4 still decides, +0.6
      refuses; a synthetic move on the real type) and CELH's merger row (corpus, 4 of 4 quarters);
    - WAT;
    - a containing line with no CIQ export beside it;
    - BDX and EPAM's Other Unusual Items, far from both;
    - CELH's EBITDA, unmapped; NKE, no fact; EPAM's merger row, NOT RUN and never asked;
    - the price-date cut (CELH as filed by 2026-08-05 refuses, by 2026-08-06 decides);
    - all-or-nothing;
    - an EDGAR that will not serve companyfacts;
    - from round 0, a restated quarter naming only the filing it was read from, and a partial
      quarterly reading never called "four quarters";
    - from the review of option B, three pins on NFLX's real fixture: a component row missing, an
      annual cell blanked, and a component no quarter carries;
    - from Codex round 2, a derived quarter pairs filings of one vintage, on MVST's REAL facts. Its
      9M-2024 line was restated from +7.864 to −0.293 in a 10-Q filed after its 10-K. As filed by
      2025-12-01, Q4-2024 reads −7.708 (the 10-K's own), never 0.449. The pin failed on the PR
      head.
  - **The call site**, by AST: after `ltm_read.refused` and before every spend.
    `tests/test_ciq_press_release_ltm.py`'s call-site pin follows the raise into
    `_settle_ltm_refusals`.
- **Mutation:** 21 mutants, one change each, in a scratch copy of the final code; 20 killed.
  - **Same item:**
    - M1 sign flipped; M2 band accepts anything; M3 the as-of cut dropped; M4 Q4 not differenced;
    - M5 the whole non-operating line read as a same-item concept;
    - M6 an undecided row no longer refuses;
    - M7 the figure not put in the cell; M8 the caveat routed to QA;
    - M9 a NOT RUN row reaching the filing;
    - M10 the earliest filing of a 3-month fact read;
    - M12 the call deleted at assembly; M13 an unreadable EDGAR crashing the build;
    - M14 accessions read off the rendered `source_ref`;
    - M15 a derived quarter pairing a later comparative (the vintage rule dropped).
  - **Containing line:**
    - B1 a missing quarter no longer refusing; B2 the line's TOTAL stated as the row;
    - B3 the slack widened to 1 $M; B4 the row's own cell left out of the breakdown;
    - B5 the line's sign flipped; B6 the same-item concepts skipped.
  - **One SURVIVED: M11**, falling through to the next same-item concept on a band failure. It is
    equivalent on the whole corpus, because no one of the 37 names files both business-combination
    concepts in the window.

**BOUNDARY.**
- **Population:** the 37 folders of the operator's Drive `manual/ciq` as on disk 2026-11-04
  (exports dated 2026-07-20 … 2026-11-02).
- **Facts:** SEC companyfacts fetched 2026-11-04, each name cut at its comps export stamp, standing
  in for the price date a build reads off its stored close. No store is in this worktree.
- **Rows:** the annual summary's additive rows, against the quarterly export's four quarters ending
  on the LTM date, tolerance 2% or 0.5 $M.
- **Code:** main `a439eabe` plus this branch.
- **Counts:**
  - 40 rows DIFFER, on 18 of the 37 names (NOT RUN rows are excluded; they are never asked). Three
    are material: CELH, NFLX, WAT.
  - Decided, 3: CELH Other Unusual Items (material, same item), NFLX's merger row (material,
    containing line) and EPAM's restructuring (not material, same item).
  - Refused, 37 in all:
    - 27 have no mapping: 22 core Revenue/EBITDA/EBIT rows, and 5 Asset Writedown, Legal
      Settlements or Gain on Sale rows, none material;
    - 6 have a mapped concept with no filed fact for some quarter, WAT among them;
    - 3 have a mapped concept far from both readings (BDX, MCK, EPAM Other Unusual Items);
    - 1 has a breakdown that misses its containing line (CELH's merger row).
- **At assembly:** only material rows reach the tiebreak. So the change moves TWO names, CELH and
  NFLX, from refused to buildable. WAT refuses as before with a longer message, and 34 names are
  untouched.
- **Committed pages:** none change, because the check runs at assembly.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **One survivor (M11)** guards behaviour no real case reaches yet.
  - Falsifier: a filer tagging both business-combination concepts in its window. The first such
    name is the pin.
- **"Other Unusual Items" → `RestructuringCharges` is the brief's mapping, and the band is its
  only guard.**
  - A row that is restructuring PLUS a small other item within 2% is stated as the restructuring
    alone. That is at most a 2% understatement, the same tolerance at which CIQ is deemed to agree
    with itself.
  - Falsifier: a decided row whose filed figure differs from CIQ's readings by the size of an item
    the filing names separately.
- **A containing line confirms the quarterly reading; it does not prove the annual one wrong.**
  - The filed total is consistent with both of NFLX's exports. The quarterly breakdown is the only
    one that can be checked per quarter, and that is what the operator's rule decides on.
  - Falsifier: a filing, or a later restatement, that books the fee other than as income in Q1
    2026.
- **CELH and NFLX are not re-assembled here.** Each is a separate artifact pass after merge.
  - CELH: its first page, with the follow entry recorded on 2026-11-02 (STATE row 32 (27)), on its
    2026-10-30 exports. Its Q3 10-Q, estimated ~2026-11-06, makes a page built before it a quarter
    behind, and when to build is the operator's call.
  - NFLX: its committed page (#867) states −2,800.0 until then.
