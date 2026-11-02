---
id: 2026-11-02-four-readers-read-by-header-and-whole-number
status: shipped
date: 2026-11-02
prs: [883]
supersedes:
superseded-by:
---

# Four readers stop pairing by position: a "respectively" maturity, a segment column, an ADS count and the dilution quarter (audit E2-D14, E2-D18, F-D2, X3)

**WHAT.** Four small readers each took a value from the wrong place.

- **E2-D14, `edgar.debt_maturities._loans`.** "The Revolving Credit Facility and the Term Loan B
  mature on June 1, 2029 and June 1, 2030, respectively" pairs its loans with its dates by
  position. The grammar does not read position. It gave the first date to the loan nearest the
  verb, so the Term Loan B differed from CIQ's 2030-06-01, the newer filing governed, and the page
  printed 2029-06-01. A sentence whose MATURITY dates are a list paired "respectively" now states
  no loan maturity: a maturity verb, two or more dates or years, then "respectively" (or the verb,
  "respectively", then the dates).
  - **Narrower than the brief's "refuse respectively sentences", on measurement.** Most such
    sentences in the cached filings pair amounts, rates or balance dates beside one maturity
    that main reads right. "The Series B Term Loan matures on April 22, 2029 and bears interest
    … floors of 0.50% and 1.50%, respectively" is one. "A term loan that matures in March 2032,
    at March 31, 2026 and December 31, 2025, respectively" is another. The first cut refused the
    word alone and lost them. Both are now pinned as still read.
  - The corpus has the defect live. Target's 10-Q 0000027419-26-000022 (filed 2026-05-29) says
    "Our committed $1.0 billion 364-day and $3.0 billion unsecured revolving credit facilities
    that will expire in October 2026 and October 2028, respectively". Main gave the $3.0 billion
    revolver October 2026, the 364-day facility's date. Three more filings misread worse: a Term
    Loan given the Revolver's 2029 (CIK 2011286), a revolver given the term facility's 2033 (CIK
    102752), and Term B Loans given the revolving loans' 2028 (CIK 1974138).
- **E2-D18, `edgar.segments.segment_rows`.** A 10-Q heads its columns with two rows: a duration
  ("3 Months Ended" over two columns, "9 Months Ended" over two more) above a date. Every date
  can be the same quarter end, so main, which read the date row alone, filed the quarter's figure
  and the year-to-date figure under one period. Alphabet's Q3 2026 10-Q report R84 gave
  "Total revenues" 127,577 and 357,269 both under "Sep. 30, 2026".
  - Each column is now named by both rows: "3 Months Ended Sep. 30, 2026". A duration header
    whose column count differs from the date header's is refused. So is a figure row wider or
    narrower than the header (main cut it to fit). So is a duration row that carries a column
    label which is not a duration, as an unmarked caption cell would (review round 0): dropping
    that row would label every column by its date alone again.
  - The 10-K's labels change too: "12 Months Ended Dec. 31, 2025". `segment_rows` has no
    production caller, so no page or record moves.
- **F-D2, `resolver.ads_ratio`.** A count was read by its first word: "twenty-four" as 20,
  "thirty-five" as 30, "three hundred" as 3 and "1,000" as 1, each `known`.
  - A count is now read whole, in words or digits. The tens take their unit ("twenty-four",
    "twenty four"), a count takes "hundred" ("three hundred", "two hundred and fifty"), and digits
    take their thousands separators. "seventy" and "ninety", which main's word list lacked, are
    read.
  - A number that runs on past what was read is refused, never read as its first part: "one
    thousand", "2,50", "ten-fold", the mixed "2 1/2". The number is matched atomically, so a
    refused "twenty five thousand" is not retried as "twenty" (review round 0). A count that
    starts inside another number is refused too.
  - The fences hold: "two" is 2, KT's "one-half of one share" 0.5, SMFG's "3/5 of one share"
    0.6, RERE's "every three ADSs represent two" 2/3 and TSM's "five (5)" 5.
- **X3, `dossier.dilution._paired_period`.** At a 10-K's end date both weighted averages are
  tagged over the year alone, so "the shortest span at the latest end" was the year. SMPL's
  FY2026 10-K gave 363 days, 92,372,473 on both legs. `anchor._latest_point` closed the same
  defect on 2026-10-29. The pairing now reuses `anchor.QUARTER_MAX_DAYS` (100), so the pair is
  the last 10-Q's quarter (SMPL 2026-03-01..2026-05-30, 89,940,680; WOR 2025-12-01..2026-02-28).
  A filer with no quarter on file is refused, and the refusal says a quarter is missing. Only a
  test imports the module.
- **Extraction version** `2026-11-02.D14-D18-FD2-X3`, in both tables, with `--repin`.

**WHY.** Each reader paired a value with its subject by position or by prefix, and each gave a
confident wrong value where it should have refused. Refusing is the house rule: an unread
"respectively" sentence leaves the instrument not run and the page on CIQ's date. The row's note
then reads as if no filing stated a maturity, which is DEFERRED below.

**HOW VERIFIED.**
- **Pins, each red on `origin/main` f8e1bbb9 and green here.** Each was run against an archive of
  main's `vinci/` and `tests/` with only the new tests and fixtures copied in.
  - `tests/test_debt_maturities.py`: end to end, filing text → `read` → `check` →
    `govern_instruments`, the Term Loan B keeps 2030-06-01 (main 2029-06-01, governing). The
    audit's sentence, Target's and the three real ones above state no loan maturity. The two real
    sentences whose "respectively" pairs rates or balance dates, and a plain "The Term Loan B
    matures on June 1, 2030.", still read as main reads them; these are the fence that keeps the
    refusal narrow.
  - `tests/test_segment_economics.py`, on Alphabet's Q3 2026 10-Q (`FilingSummary.xml` and
    `R84.htm`, frozen byte for byte from EDGAR, acc 0001652044-26-000084):
    - the four "Total revenues" figures land in four periods (main: two keys);
    - each period's segment revenue plus hedging is its own total (96,302 + 30,709 + 372 + 194 =
      127,577 for the quarter);
    - a header whose two rows disagree is refused, as is a row wider than its header, and so is
      a duration row whose caption cell is unmarked.
    - The 10-K pins now carry the duration in their labels.
  - `tests/test_ads_ratio.py`: the audit's four and "seventy" and "two hundred and fifty" read
    whole; "one thousand", "2,50", "ten-fold", "twenty five thousand" and "2 1/2" state nothing.
    The fences pass on both main and here.
  - `tests/test_dilution_denominator.py`: SMPL's and WOR's real FY2026 10-K companyfacts pair the
    last 10-Q quarter (main: the year). A year-only filer is refused, naming the quarter.
- **Decision path, F-D2.** `scripts/ads_ratio_moves.py` reads each primary depositary line's ratio
  as the weekly run does, `EntityResolver.ads_ratio(cik, 2026-10-16)`, once with main's
  `read_ratio` and once with this one, cache only.
  - **85 lines, all covered. Known 76 → 76; moved 0.** So no screen P/E level, anchor count or
    cap moves, and STATE row 41 gains nothing.
  - 58 are read from a 12(b) title and 18 from the text.
  - The 9 refused: BMA and GGB (none stated), GRFS, HIMX and EDU (several stated), and KOF, TV,
    BSBR and VLRS (units).
  - **EDU differs from #840's 77, on both readers.** Its FY2025 20-F (0001193125-25-216394, filed
    2025-09-25) describes two ratio changes, one ADS for one share becoming one for ten in 2022
    and four for one becoming one for one in 2011. So the text states 1, 4 and 10, and the
    reader refuses by design. #840 records EDU at 10. The reader is unchanged since #840, so the
    input differs; not investigated (below).
  - Coverage needed this worktree's cache warmed through the house's paced SEC client: 34
    submissions indexes and 101 documents, over four passes. Two documents failed once with
    exhausted retries, UGP's and IPX's, and were read on the next pass.
- **D14 on the committed pages.** `scripts/debt_maturity_moves.py` rebuilds every committed page's
  maturity check through `mechanical.maturity_check` twice, once with main's reader and once with
  this one, from the page's own panel, pointers and reference date, cache only.
  - All 26 non-held pages are covered. Main's rebuild reproduces the committed rows on all 26.
  - **Rows moved: 0.** So no page moves, and STATE row 41 gains nothing.
  - Coverage needed this worktree's cache warmed through the house's paced SEC client: 76
    documents, then 26 submissions indexes re-fetched, then 21 documents. The primary checkout's
    cached indexes predate several pages' latest 10-Q. With them, main's rebuild matched only 13
    of 24 covered pages, and the one row that moved was Target's revolver read off the older
    May 10-Q.
- **D14 across the cached filings.** The probe read every cached SEC document that says
  "respectively" and "matur…" or "expire": 3,718 filings, plus 1 that `html_to_text` could not
  read. In 58 of them, main reads a loan maturity from 81 sentences that say "respectively". Main
  and this reader were then compared on those 58 filings, on full sentences:
  - **14 refused (13 distinct, in 10 filings).** Each is a maturity list paired by position, and
    main gave the class its first date, or another loan's date.
  - **The other 67 read exactly as on main.**
  - The probe is a session script. The page replay above is the committed one.
- **X3 on the committed pages' companyfacts.** All 26 non-held pages' companyfacts are cached. The
  pair moves on 0, and this branch's pair equals `anchor._latest_point`'s quarter on all 26. The
  defect is latent: no cached blob is at a 10-K end, as SMPL's and WOR's frozen fixtures are.
- **ruff** and **`mypy --strict vinci`** are clean (the two scripts too). `node --check` passes on
  the JS twin.

**BOUNDARY.**
- **Code:** branch `claude/p2d-d4-small-batch` from `origin/main` f8e1bbb9.
- **Held test packs:** never read. Their folders and CIKs are skipped by name before any file is
  opened.
- **D14 pages:** the 26 committed `data/dossiers/*/dossier.json` outside the held test packs that
  carry a `maturity_check`, rebuilt 2026-11-02 at their own reference dates.
- **D14 sentences:** the primary checkout's `sec` cache, read 2026-11-02: every EDGAR Archives
  `.htm` that is not an R-file and not a held test pack's CIK, and whose text says "respectively"
  and "matur" or "expire". Sentences are split by `debt_maturities._SENTENCE`; a sentence counts
  when it names a loan noun (`_NOUN`) and says "respectively".
- **D18:** two real filings. Alphabet's FY2025 10-K R90 is the existing fixture. Its Q3 2026 10-Q
  R84 and FilingSummary were fetched 2026-11-02 in 3 paced requests (submissions, summary,
  report). Amazon's Q2 2026 10-Q summary is in the primary cache.
- **F-D2:** the 85 lines of the committed `data/snapshots/universe_snapshot.jsonl` (as of
  2026-10-16) that the Polygon reference pull of 2026-10-17 (UTC; 13,271 typed tickers, read from
  another worktree's git-ignored cache) types `ADRC`/`GDR`. Each ratio is read as of 2026-10-16,
  from submissions indexes re-fetched 2026-11-02 where the primary cache lacked them. Also the
  19-name fixture, through the existing pins.
- **X3:** the 26 pages' companyfacts as cached (the primary checkout's, any age), read 2026-11-02,
  plus the two frozen fixtures.

**FOUND, NOT FIXED** (outside these four items):
- **`segments._pick_report` refuses both 10-Qs tried.** Alphabet's Q3 2026 10-Q indexes "Revenues
  - Revenue by Segment (Details)" beside R84, and Amazon's Q2 2026 10-Q indexes "Disaggregation of
  Revenue (Details)" beside its reportable-segments report. Each is refused as ambiguous, so on a
  10-Q `segment_rows` never reaches the table this fixes.
- **R84's segment headings are not read.** The separator is "Segment Reporting [Line Items]", which
  the reader does not know (it knows "Segment Reporting Information"). The axis label is suffix-form
  ("Google Services | Operating Segments"), and `_AXIS_PREFIX` strips the wrong side. Every R84 row
  files under the wrong segment. The pins here assert columns only.
- **A refused "respectively" sentence is not named on its row** (review round 0, DEFERRED). The
  instrument's row reads not run, "no filing read states a maturity for it", although the filing
  stated two dates by position. Naming the refusal means carrying a reason through `decide` and
  `check`, which is beyond E2-D14.
- **EDU's cover reads its 12(b) title as "Name of Exchange on Which Registered"**
  (`instrument.cover_lines`, on the 20-F above). So its title states no ratio, and the text's
  three are refused. Not investigated.
- **`_notes` reads the whole text, not by sentence,** so a "respectively" sentence about notes is
  not refused by this change. Notes never differ (`decide`), so it cannot move a page date. Not
  measured here.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **A maturity list paired "respectively" is refused whole.** That includes a loan maturity the
   same sentence states plainly elsewhere. The instrument it would have dated is not run, and the
   page keeps CIQ's date. A positional pairing the rule does not see stays as main reads it: dates
   that are not adjacent to "respectively", or a list split by other words. FALSIFIER: a committed
   page whose maturity check loses a correct filing date to this refusal (0 of the 26 now), or
   one that still governs on a positional date.
2. **A segment period label is longer, and the 10-K's labels change.** No caller reads them yet.
3. **An ADS count beyond "N hundred", or in "thousand" words, is refused, not read.** Not observed
   on the 85 lines.
