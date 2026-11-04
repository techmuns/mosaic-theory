---
status: shipped
date: 2026-11-04
prs: []
supersedes:
superseded-by:
---

# The SEC filing decides a material LTM that CIQ's two exports disagree on: CELH's row is stated as filed, while NFLX and WAT stay refused because no filed figure for the same item exists

**WHAT.** The operator approved the filing as tiebreaker on 2026-11-04 ("the way an expert team
builds a line from the 10-K and 10-Qs when its data vendor disagrees with itself").
`vinci/dossier/filed_tiebreak.py` now runs at the pre-spend LTM check (`ltm_quarters`), for each
MATERIAL row whose annual-export LTM DIFFERs from its four quarters in the quarterly export:
- **The filed figure.** It reads the filer's XBRL for the same four quarters, through an explicit
  reviewed mapping (`MAPPING`), as filed by the page's price date (`concepts.facts_as_of`). Each
  quarter is the 3-month fact, or a longer period less the one a quarter shorter (Q4 = FY − 9M).
- **When it reproduces one of CIQ's two readings** within 2% or $0.5M (`ltm_quarters.agrees`, the
  check's own tolerance):
  - the row's LTM cell holds the filed figure (value and display cell);
  - the annual table's `source_ref` names every accession;
  - `financial_summary.filed_ltm` carries the `{value, source_ref}` with both CIQ readings and each
    quarter's filing;
  - one main-body caveat ("FILED FIGURE STATED — …") names CIQ's disagreement and the accessions.
- **Otherwise it refuses exactly as before.** That covers an unmapped row, a mapped concept missing
  a quarter, and a filed figure far from both readings. The check's own refusal message now adds
  why the filing could not decide.
- **All or nothing.** One undecided material row refuses the build.

The mapping has three entries:

| CIQ row | concept | sign |
|---|---|---|
| Restructuring Charges | `RestructuringCharges` | −1 |
| Other Unusual Items | `RestructuringCharges` | −1 |
| Merger & Related Restruct. Charges | `BusinessCombinationAcquisitionRelatedCosts`, then `BusinessCombinationIntegrationRelatedCosts` | −1 |

The first concept carrying all four quarters is THE figure. It is never spliced, never summed, and
never skipped for a later concept that agrees better.

| case | CIQ annual LTM | CIQ quarterly sum | filed (as filed by the export stamp) | outcome |
|---|---|---|---|---|
| CELH Other Unusual Items, LTM to 2026-06-30 (material) | −418.8 | −405.0 | **−412.748** = −246.707 (Q3-25) − 80.754 (Q4-25 = FY25 327.461 − 9M 246.707) − 4.427 (Q1-26) − 80.860 (Q2-26) | **stated as filed**; reproduces both readings (1.4%, 1.9%) |
| EPAM Restructuring Charges (not material) | −53.5 | −28.5 | −53.474 | sides with the ANNUAL export |
| NFLX Merger & Related Restruct. Charges (material) | −2,800.0 | +2,800.0 | no business-combination concept filed | **refused**, as today |
| WAT Merger & Related Restruct. Charges (material) | −459.0 | −346.0 | no business-combination concept filed | **refused**, as today |
| BDX Other Unusual Items (not material) | −184.0 | −143.0 | `RestructuringCharges` −693.0 | refused: reproduces neither |
| NKE Restructuring Charges (not material) | −385.0 | −311.0 | no `RestructuringCharges` fact for any of its four quarters to 2026-08-31 | refused: no filed figure |

CELH's filings: 10-Q 0001341766-25-000144 (2025-11-07), 10-K 0001341766-26-000024 (2026-03-02),
10-Q 0001341766-26-000039 (2026-05-07), 10-Q 0001341766-26-000050 (2026-08-06).

**THREE OF THE BRIEF'S VALUES DID NOT HOLD AT BUILD, AND THE BUILD FOLLOWED THE DATA.**
- **NFLX does not pass.** Its $2.8B termination fee from WBD is filed only inside
  `NonoperatingIncomeExpense`, the whole "interest and other income" line. Q1 2026 is 2,852.166
  (10-Q 0001065280-26-000138), which CIQ's own Q1 rows reproduce: interest and investment income
  70.0, FX −8.3, other −9.5 and the merger row 2,800.0. The brief's own rule maps that concept
  "only where the row is the whole non-operating line", and an unusual-items row never is: CIQ
  always splits the line above the block. Over the LTM to 2026-09-30 the line reads 2,992.3
  (Q4-25 derived 45.473 + 9M-26 2,946.833), 6.4% from +2,800.0, so even mapped, the band would
  refuse it. The filing supports the quarterly SIGN, as row 41 already says, and the merger row
  is the operator's call. The coordinating session was asked (option A, this build; B, a
  "containing line" kind that may only pick which CIQ reading the filing supports; C, stating
  2,992.3, advised against). It had not answered when this was written, so A stands.
- **NKE cannot be the case where the filed figure sides with the annual export.** In companyfacts
  it tags no restructuring P&L figure for FY26 or its LTM, only `SeveranceCosts1` 300M FY26 and
  `PaymentsForRestructuring`. The docstring and refusal message's "NKE's restructuring was the
  quarterly side's error" is therefore not confirmed by any filed figure (not changed here).
  EPAM is the real annual-side case.
- **WAT is a third material refusal.** Main's own check refuses it on the merger row (LTM −459.0
  against −346.0, no page). It files no mapped concept, so it stays refused.

**DOES THIS SELECT ON FORM?** (CLAUDE.md, before any new gate.) It adjudicates between two vendor
readings by the primary source, and ranks, grades or weights nothing. One narrow selection is
real: which refused names it can clear depends on whether the filer TAGS the item. CELH does; NFLX
(a containing line), WAT and NKE do not. That selection decides only whether a page can be built
on a verified figure. A name it cannot clear is refused exactly as before, so the selection can
only leave a name where it was.

**THE BAND, AND WHY.** The filed figure must reproduce one of CIQ's readings within the same 2%,
or half a printed million, at which CIQ is deemed to agree with itself (operator ruling
2026-10-30). The band is set by face validity, never by an outcome:
- CIQ copies its figures off the filings, so a line that reproduces neither is not shown to be the
  line CIQ read.
- A wider band would let a neighbouring item stand in for the row (NFLX's containing line, 6.4%).
- A narrower band would refuse ordinary restated comparatives.
The band also catches the mapping misreading a name. EPAM's Other Unusual Items (−17.8 / −16.8) is
not its restructuring (that sits in CIQ's own Restructuring row), and the −53.5 it would read is
refused.

**HOW VERIFIED.**
- **Real run at $0** (no assembly, no LLM): main's check and the tiebreak over all 37 folders of the
  operator's Drive `manual/ciq`, beside SEC companyfacts fetched 2026-11-04. Main's check refuses
  CELH, NFLX and WAT. On this branch CELH is decided (table above, and the caveat as printed); NFLX
  and WAT refuse with the reason added.
- **Pins** (`tests/test_filed_tiebreak.py`, 17 tests) run on `tests/fixtures/filed_tiebreak.json`:
  - the fixture is derived cells cut from the real exports (Drive shas CELH 0e47f54b97/9f492d7a75,
    NFLX 8ae9f12b10/512a1e9a0a, EPAM 04c788d495/7baf86ffeb, BDX b525583374/5489c75ea7, NKE
    f4bc343292/5a10072a9a) through the real decode path into the real `CiqBundle`, plus SEC's
    companyfacts cut by concept with each concept's rows unmodified
    (`scripts/build_filed_tiebreak_fixture.py`);
  - positive: CELH through `assemble._settle_ltm_refusals`, from the LTM cell and the demanded
    19c figure to the caveat rendered by `render._flags_section`, and EPAM's annual side;
  - negative: NFLX (the containing line, and why), BDX and EPAM's Other Unusual Items (far from
    both), CELH's EBITDA (unmapped), NKE (no fact), EPAM's merger row (NOT RUN, never asked),
    the price-date cut (CELH as filed by 2026-08-05 refuses, by 2026-08-06 decides), and
    all-or-nothing;
  - the call site, by AST: after `ltm_read.refused` and before every spend.
  - `tests/test_ciq_press_release_ltm.py`'s call-site pin follows the raise into
    `_settle_ltm_refusals`.
- **Mutation:** 12 mutants, one change each, in a scratch copy of the tree; 10 killed. Killed:
  - M1 sign flipped; M2 band accepts anything; M3 the as-of cut dropped; M4 Q4 not differenced;
  - M5 `NonoperatingIncomeExpense` mapped for the merger row;
  - M6 an undecided row no longer refuses;
  - M7 the filed figure not put in the cell; M8 the caveat routed to QA;
  - M9 a NOT RUN row reaching the filing; M12 the call deleted at assembly.

  Two SURVIVED, each equivalent on the whole corpus:
  - M10: the earliest filing of a 3-month fact read instead of the latest;
  - M11: falling through to the next concept on a band failure.
  Across the 37 names' mapped concepts, no quarter in the window carries two filings of different
  value, and no name files both business-combination concepts. The only restatement found is WST's
  9M-2024 restructuring (−2.5M → 0), which reaches neither line.

**BOUNDARY.**
- Population: the 37 folders of the operator's Drive `manual/ciq` as on disk 2026-11-04 (exports
  dated 2026-07-20 … 2026-11-02).
- Facts: SEC companyfacts fetched 2026-11-04, each name cut at its comps export stamp, standing in
  for the price date a build reads off its stored close. No store is in this worktree.
- Rows: the annual summary's additive rows, against the quarterly export's four quarters ending
  on the LTM date, tolerance 2% or 0.5 $M.
- Code: main `cfedcb39` plus this branch.
- Counts:
  - 40 rows DIFFER, on 18 of the 37 names (NOT RUN rows are excluded; they are never asked); 3 are
    material (CELH, NFLX, WAT).
  - Decided: 2, CELH (material) and EPAM's restructuring (not material).
  - Refused, 38 in all:
    - 27 have no mapping: 22 core Revenue/EBITDA/EBIT rows, and 5 Asset Writedown, Legal
      Settlements or Gain on Sale rows (none material);
    - 8 have a mapped concept with no fact for some quarter (NFLX and WAT among them);
    - 3 have a mapped concept far from both readings (BDX, MCK, EPAM Other Unusual Items).
- At assembly only material rows reach the tiebreak. So the change moves ONE name, CELH, from
  refused to buildable. NFLX and WAT refuse as before with a longer message, and 34 names are
  untouched.
- No committed page changes: the check runs at assembly.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Two survivors (M10, M11)** guard behaviour no real case reaches yet.
  - Falsifier: a filer restating a mapped quarter in the window, or tagging both
    business-combination concepts. The first such name is the pin.
- **"Other Unusual Items" → `RestructuringCharges` is the brief's mapping, and the band is its
  only guard.**
  - A row that is restructuring PLUS a small other item within 2% is stated as the restructuring
    alone, at most a 2% understatement, the same tolerance at which CIQ is deemed to agree with
    itself.
  - Falsifier: a decided row whose filed figure differs from CIQ's readings by the size of an item
    the filing names separately.
- **CELH is not re-assembled here.** Its page, with the follow entry recorded on 2026-11-02 (STATE
  row 32 (27)), is a separate artifact pass after merge. The page would read the 2026-10-30
  exports. Its Q3 10-Q (est. ~2026-11-06) makes a page built before it a quarter behind, and when
  to build is the operator's call.
