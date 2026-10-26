---
status: shipped
date: 2026-10-26
prs: [808]
supersedes:
superseded-by:
---

# The latest-quarter OCF read takes the newest period ANY alias carries — the alias the annual walk serves left it a stale quarter after a tag switch; 0 of 27 pages move, 19 of 2,161 cached filers do

**WHAT.** `mechanical._latest_quarter_ocf` (the self-funding line's OCF leg) now reads through a
new `mechanical._latest_quarter(facts, concept)`. The period is the NEWEST flow period any of the
concept's aliases carries. The quarter ending there comes from `ebitda_recon._quarter` over the
aliases in priority order: the first alias that yields that quarter, both legs of a year-to-date
difference on that one tag. So precedence is kept WITHIN a period (the pattern of `_quarterly_map`)
and the next alias carrying the period is read only where the first cannot be differenced. Before,
the period was the newest of the ONE alias `extract_points` serves. The `filed_by` cut (#807) runs
first, unchanged. `extract_points`, `_resolve` and every annual reader are unchanged.

**WHY.** `concepts._resolve` judges each alias by how far its ANNUAL series reaches whenever any
alias carries an annual (`_reach(..., annual_grain=True)`, `SIBLING_LAG_DAYS` = 200). That is right
for an annual reader and wrong for a latest-quarter one: a filer that moves to another tag mid-year
has its newest quarters on that tag and no annual on it yet, so the tag is skipped as "left behind"
and the served tag's newest period is a quarter or a year old. Found in #807
(`docs/records/2026-10-26-self-funding-alias-as-of.md`, item 2) as the 4 reads that went EARLIER.

- **BURL as filed by 2018-11-28** (its third-quarter 10-Q). The plain tag carried the nine months to
  2018-11-03 ($375.4M) and the half ($166.3M), but its newest annual was FY2013. So the walk served
  the continuing-operations tag, whose newest period is the first quarter: +$60.2M, to 2018-05-05.
  It now reads +$209.0M, to 2018-11-03.
- **ScanSource (CIK 918965), live today.** It tags its 10-Ks on the continuing-operations tag
  (FY2024, FY2025) and its 10-Qs on the plain one (newest annual FY2019). The walk serves the
  former. Its newest period is the year to 2025-06-30, with no nine months on that tag to take
  from it, so the read was UNKNOWN. It now reads $125.4M − $54.1M = **+$71.4M**, the quarter to
  2026-03-31.
- **An abandoned alias still cannot win: it carries no later period.** UBER's
  `RevenueFromContractWithCustomerExcludingAssessedTax` stops at 2019-06-30. The walk SERVED it as
  filed by 2019-11-05, because before UBER's first 10-K no alias had an annual and its lag
  (92 days) sat inside the 200-day sibling allowance. Meanwhile the quarter to 2019-09-30 was under
  `Revenues`. The same defect on the all-points grain.

**HOW VERIFIED.**
- **Census first, on the shared cache** (2,161 companyfacts, read-only). A case is a (filer,
  concept) where `extract_points` serves a tag whose newest flow period is older than a period
  carried by a skipped HIGHER-priority alias. Found: **62 cases in 60 filers**, which reproduces the
  brief's count: OCF 16, pre-tax 15, revenue 12, capex 8, D&A 5, diluted EPS 4, net income 2.
  Counting a newer LOWER-priority alias too gives 226 in 210 filers. Only the OCF reader changes
  here.
- **The pins fail first, on #807's reader.**
  - `test_a_tag_the_filer_moved_back_to_mid_year_carries_the_latest_quarter`: BURL as filed by
    2018-11-28 got `(60.21, 2018-05-05)`.
  - `test_a_period_two_aliases_carry_is_read_from_the_first_that_can_be_differenced`: FUBO as filed
    by 2017-08-21 got +0.102, the continuing-operations tag, against the plain tag's −0.096 that
    precedence gives.
  - The negative pin `test_an_abandoned_alias_is_never_served_for_a_later_period` reads UBER revenue
    at all 32 dates UBER filed a revenue row. Each time the period is the newest any alias carries,
    and the abandoned tag never supplies one after 2019-06-30. As filed by 2019-11-05,
    `extract_points` serves the abandoned tag and `_latest_quarter` reads `Revenues` to 2019-09-30.
  - All of #806's and #807's pins pass unchanged, including AORT 2014: the reverse switch, a
    higher-priority tag genuinely left for three years.
- **Mutation**, 8 mutants in a scratch copy of the tree, **8 killed**, each by the pin built for it:
  - the period from the alias `extract_points` serves (#807's rule);
  - only the first alias carrying the period differenced (FUBO 2015 → UNKNOWN);
  - precedence reversed within the period;
  - the earliest period;
  - only the first alias read at all;
  - no `filed_by` cut;
  - the period from today's blob with the quarter from the cut;
  - the first alias's name reported for another's value.
- **Found in review (`/code-review high`), fixed behind a pin that failed first.** `_quarter`
  matches a period ending within a week. So, tried over every alias, a higher-priority alias whose
  newest quarter closed a few days earlier would have been read under the later date. Only the
  aliases carrying that exact period end are now differenced.
  `test_only_an_alias_carrying_the_latest_period_end_itself_is_read` uses AORT as filed by
  2014-04-30, with a plain-tag quarter to 2014-03-28 added. Before the fix it read 99.0 under
  2014-03-31; it now reads −2.038. It is a constructed row on a real fixture: no such case exists
  in the corpus. The three real runs below are byte-identical before and after this fix.
- **Real run, nothing written.**
  - **(1) The 27 committed pages, each as filed by its own `assembled_at`: 0 move.** Every page reads
    the same quarter and value as under #807, so no stored line, cite or `fcf_sign_vs_edgar_ocf`
    outcome changes.
  - **(2) Every OCF filed date over the 30 companyfacts fixtures: 31 of 1,604 reads move.**
    - 18 read a LATER quarter. #807's 4 earlier reads are among them: BURL 2018-11-28 and TJX
      2018-12-04, to 2018-11-03; HLF 2018-10-30 and ORKA 2018-11-14, to 2018-09-30. The other 14
      are the 2014 switches of BURL, FUBO, HLF, HWM, ORKA, TJX and WOR.
    - 5 read a quarter where #807 read UNKNOWN: HWM 2015 ×4, TGT 2015-03-13. #807 served the plain
      tag, whose newest period was a fiscal year with no nine months on that tag. On the 10-K
      dates (HWM 2015-02-19, TGT 2015-03-13) the year falls through to the continuing-operations
      tag, which carries both. On HWM's three later dates a newer quarter on that tag is read.
    - 7 go to UNKNOWN (cost 1 below).
    - FUBO 2017-08-21 reads −$0.096M (total) where #807 read +$0.102M (continuing operations).
      Both tags carry the half; precedence gives the plain tag, as #806 read.
  - **(3) Every cached companyfacts, today's blob: 19 of 2,161 move.** These are the 16 OCF filers
    of the census and 3 where a lower-priority alias carries the newer quarters: Jack in the Box,
    Stoneridge, Broadwind.
    - 13 read a later quarter, and 3 of those flip sign: ThredUp −$1.5M → +$4.5M, Element
      Solutions +$91.1M → −$66.6M, Crane −$29.5M → +$122.3M.
    - 5 read a quarter where the read was UNKNOWN: XPO, Brink's, Angi, ScanSource, EnPro.
    - 1 goes to UNKNOWN: Broadwind. Its half to 2026-06-30 is on the continuing-operations tag, and
      its first quarter (+$2.9M, the old read) is on the plain one.
    - No committed page's filer is among the 19.

**BOUNDARY.**
- **Census and cache run:** the shared SEC cache
  `/Users/work/Documents/GitHub/mosaic-theory-ta/data/cache/sec`, read-only. 2,161 companyfacts
  entries, fetched 2026-08-12..2026-10-26 (ScanSource and Broadwind fetched 2026-08-13 and
  2026-09-17). Concepts: the 7 flow concepts with more than one alias. Unit: one (filer, concept),
  or one read. No cut (today's blob). Code at main 7213d486 plus this change.
- **Fixture run:** the 30 files in `tests/fixtures/companyfacts/` (frozen 2026-10-23). Dates are
  every distinct `filed` of a row under either OCF alias: 1,604 (fixture, date) reads, as #807
  measured.
- **Pages:** the 27 under `data/dossiers/` at main 7213d486, each as filed by its own
  `assembled_at` (2026-08-18 … 2026-10-21).
- **Shape-B census:** the 62 cases above. Filter: the served tag's newest annual is more than 365
  days behind the newest period any alias carries. Measured 2026-10-26.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **UNKNOWN on the first year-to-date after a switch.** The newest period sits on the new tag,
   its prior year-to-date on the old one, and the two are never mixed (total and
   continuing-operations cash flow differ wherever there are discontinued operations). That is
   7 historical fixture reads and Broadwind today, where the old read served the previous quarter
   itself: a stale value, by #806's rule never served. Falsifier: a committed page assembled
   inside such a window (0 of 27 today).
2. **NOT FIXED — annual readers are served a years-old annual when the newer alias carries no
   annual.** It is the same resolver seen from the other side, recorded in STATE.md §5.0 row 11.
   Of the 62 cases, 6 serve an annual more than 365 days behind the concept's newest period:
   - Climb Global (CIK 945983) capex, FY2019. The screen's `fcf_sign` takes FY2025 OCF less it.
   - Comstock Inc. (CIK 1120970) capex, FY2023. Same.
   - AbCellera (CIK 1703057) D&A, FY2023. The screen's EBITDA adds it to FY2025 operating income.
   - DiamondRock (CIK 1298946) D&A, FY2017. Its operating income is also FY2017.
   - SL Green (CIK 1040971) pre-tax income, FY2017. No reader takes pre-tax at annual grain: it is
     read only per quarter, through `_quarterly_map` and `ebitda_recon._quarter`, which walk every
     alias.
   - KalVista (CIK 1348911) revenue, the year to 2024-04-30. Read only by `EdgarFundamentals`, the
     CIQ-empty fallback, which keys by period and so loses FY2025 rather than mixing it.

   **`stale_served` would name only 4 of them.** AbCellera and KalVista still tag recent quarters on
   the served alias, so its lag behind the filer's frontier (307 and 219 days) sits under
   `STALE_TAG_LAG_DAYS` (550). The annual lag is invisible to it. The brief's four (Climb,
   DiamondRock, Comstock, SL Green) are exactly the four it names.
3. **Where the first alias cannot be differenced, the quarter read is the next alias's**, a
   different measure wherever there are discontinued operations. #806 and #807 read the same
   whenever the walk served that tag. TGT as filed by 2015-03-13: the total year is $4,439M and
   the continuing year $5,131M, the nine months are on the continuing tag only, and the quarter
   read is continuing operations', +$3,081M.
4. **Seen, not fixed:** SL Green's screen `fcf_sign` reads FY2019 capex against FY2025 OCF (82.9
   less 253.0). That is a stale tag outside this census: no capex alias carries a period after
   2019-12-31, so it is the all-stale fallback, the family `stale_served` exists for.
