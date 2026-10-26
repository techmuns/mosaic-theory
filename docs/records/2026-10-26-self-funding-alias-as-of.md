---
status: shipped
date: 2026-10-26
prs: [807]
supersedes:
superseded-by:
---

# The self-funding OCF leg, read as of a date, chooses its tag from that day's filings too — 0 of 27 committed pages move; 119 of 1,604 historical reads do

**WHAT.** `mechanical._latest_quarter_ocf(facts, filed_by=D)` (#806) now cuts the WHOLE companyfacts
blob to the rows filed by D (`concepts.facts_as_of`, #801) before anything reads it. #806 cut the
POINTS by date — the period and both legs of a year-to-date difference (through a `filed_by` it
added to `ebitda_recon._quarter`) — but chose the alias from TODAY's blob, so the tag it read could
be one the filer only adopted, or re-adopted, after D. The `filed_by` on `_quarter` is removed: one
cut, before every reader, as #801 argued for the snapshot. With no `filed_by` (assembly, which
reads live EDGAR as it stands) nothing changes.

**WHY.** `filed_by` exists for the refresh that reproduces what an assembly on D saw
(`refresh.cross_check_transform`), and EDGAR on D held exactly the rows filed by D. A hybrid —
today's alias choice, D's points — is a read no assembly ever made. `extract_points` picks the
alias by how far each sibling's ANNUAL series reaches, measured against filings that did not yet
exist on D.

The real case, AORT (then CryoLife): it moved its operating cash flow to
`NetCashProvidedByUsedInOperatingActivitiesContinuingOperations` in the 10-K filed 2014-02-21,
kept it until 2017, then went back. Chosen from today's blob the plain tag wins (it reaches 2026),
and as of 2014-04-30 it served its last quarter there — the quarter to 2013-09-30, +$7.3M (9M
$11.307M − H1 $4.035M). That day's filings carried Q1 2014 on the other tag: −$2.0M. The sign
flips.

**HOW VERIFIED.**
- **Measured before switching**, over all 30 companyfacts fixtures at every filed date of an OCF
  row (1,604 reads), comparing #806's read with the cut read:
  - **the 27 committed pages, as filed by each page's assembly date: 0 move** — so no stored line
    or outcome changes, and the refresh's real run is unchanged (22 reproduce; AORT, BRBR, CNXC,
    PARR and WLK refused as in #806; `fcf_sign_vs_edgar_ocf` 20/7 committed, 25/2 projected);
  - 119 historical reads move: 103 read a LATER quarter (AORT 15, BURL 14, HLF 14, ORKA 14, TGT
    12, TJX 14, WOR 16, FUBO 4); 10 read a quarter where #806 read UNKNOWN; 4 read an EARLIER one
    (cost 2 below); 1 goes to UNKNOWN (AORT 2014-02-21, where #806 served a five-month-old
    quarter); 1 reads the same quarter on the other tag (FUBO 2017-08-21: −$0.096M → +$0.102M —
    total against continuing operations, each that day's honest tag).
- **The pin fails first.** `test_the_tag_is_chosen_from_the_filings_of_that_day_too` (AORT as
  filed by 2014-04-30 → the quarter to 2014-03-31, −2.038, sign negative) failed on #806's read
  with `(7.272, 2013-09-30)`. #806's pins all pass on the cut, including HWM's two restatement
  pins — the cut now carries both legs.
- **Mutation**, 8 mutants in a scratch copy of the tree, 7 killed: no cut; the alias chosen from
  today's blob with the points cut (#806's shape); the difference read from the uncut blob; the
  earliest period; a fall-back to the ≤100-day read; the sign inverted; the cite without its
  quarter. The survivor is #806's known one: reverting the assembly call site's cite, pinned only
  by the live test.

**BOUNDARY.** 30 fixtures in `tests/fixtures/companyfacts/` (frozen 2026-10-23); dates = every
distinct `filed` of a row under either OCF alias (1,604 (fixture, date) reads); unit = one read of
`_latest_quarter_ocf`; the committed pages = the 27 under `data/dossiers/` at origin/main 5f4bf269,
each as filed by its own `assembled_at`; measured 2026-10-26.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The blob is copied per read** when `filed_by` is set (the refresh only; assembly does not
   cut). `facts_as_of` rebuilds every tag's rows — milliseconds against a pass of 27 pages.
2. **FOUND, NOT FIXED: an alias switch reads the OLD tag for a quarter** — the 4 earlier reads. In
   2018 BURL, HLF, ORKA and TJX moved back from the continuing-operations tag to the plain one. Cut
   to the day of their third-quarter 10-Q, the plain tag's newest ANNUAL fact is from 2013–14
   against the sibling's FY2017 — more than `SIBLING_LAG_DAYS` (200) behind — so `extract_points`'
   annual-grain sibling test calls it stale and serves the continuing-operations tag, whose latest
   quarter is the first (BURL as of 2018-11-28: the quarter to 2018-05-05, +$60.2M, where the
   quarter to 2018-11-03 was filed on the plain tag). An assembly on that day read the same, so the
   cut is still the right reproduction; the defect is the alias resolver's, shared by every concept
   reader, and no committed page's filer is in a transition. Falsifier: a committed page whose
   filer changed its OCF tag within the year.
## Amendments

**2026-10-26 — item 2 is FIXED for the latest-quarter reader, and only there.** `_latest_quarter_ocf` now takes the newest period ANY alias carries (`mechanical._latest_quarter`). The four EARLIER reads above (BURL, HLF, ORKA, TJX at their 2018 third quarters) now read the later quarter. `extract_points` and the annual readers are unchanged; their own form of the defect, a years-old annual served as the latest, is STATE.md §5.0 row 11. `docs/records/2026-10-26-latest-quarter-alias-at-quarterly-grain.md`
