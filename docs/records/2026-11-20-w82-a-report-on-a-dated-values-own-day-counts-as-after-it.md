---
id:
status: open
date: 2026-11-20
prs: []
supersedes:
superseded-by:
---

# W82: a report filed ON a dated value's own day counts as after it, on the CIQ-export event rule (#1132) and on R1's CIQ-history close (W73); the ex-lease close keeps the strict reading by ruling; the filing list the rule reads includes its start day. At a 2026-11-19 build AMZN, MCK and UBER are newly refused, and no committed R1 value moves ($0, code only)

**THE RULINGS.** The operator's words, each relayed verbatim by coordinator B:
- 2026-11-19, **"Yes, that rule"**. This answered "Count a same-day filing as after the close, in
  both gates?", raised in B's independent review of #1144 (W73, finding C, deferred there to W82).
- 2026-11-19, **"Yes, option 1 + W84"**. This answered "Keep the ex-lease band strict and add the
  W84 follow-up?", after this session's measurement (below) found that the first ruling, applied
  to the ex-lease band, refuses every ex-lease close for good.

**WHAT.**
- **One rule function.** `freshness.first_event_after` now counts a filing ON `day` as after it:
  `day <= filed <= upto`.
  - It has ONE strict reading, `same_day_counts=False` (`day < filed`), and ONE caller takes it.
  - It is the rule both gates read, so they cannot drift apart.
- **Gate A: the CIQ-export event rule** (`freshness.event_verdict`).
  - An export panel dated the day of a 10-Q, 10-K, 8-K item 2.02, or a foreign or transition
    filer's report is stale. `check_freshness` refuses it, naming the filing.
  - The note says the panel "shares its date with, and so may not carry," the filing, never that it
    "predates" it.
  - `EventVerdict.events` lists the events on or after the oldest panel, so a same-day filing that
    outdates a panel is among the events read.
- **Gate B: R1's dated close** (`anchor.close_verdict`).
  - On CIQ's history, a report on the close's day refuses it. The value is withheld and the recipe
    kept (W62's rule, unchanged).
  - The note says the company reported "on the day of the" close rather than "after the" close.
  - **The ex-lease close keeps the strict reading** (`close_verdict(…, priced_at_its_report=True)`).
    `compute_anchor` passes it for the ex-lease band, and only there, and names the divergence
    beside the call.
- **The reader** (`mechanical.read_filing_events`) reads its start day.
  - It started a day after the oldest panel, or the close, and kept only filings strictly after it.
    So neither gate could have seen a same-day filing whatever the rule said.
  - The list now keeps every same-day filing, and the ex-lease strictness stays in its caller.
- **Wording.** The $0 precheck's freshness line now reads "filed on or after the panel's date".
  `event_verdict`'s docstring is reworded.
- **Kept as it was, by ruling:** `mechanical._panel_freshness_flag` is a caveat, not a gate, and it
  keeps `panel < print`.
- **A new extraction vintage:** `2026-11-20.a-report-on-a-dated-values-own-day-counts-as-after-it`,
  which follows W73's. `anchor.py`, `freshness.py` and `mechanical.py` are re-pinned under it.

**WHY.**
- **The rule reads DATES, never times, so the strict reading could not see a same-day report.**
  BellRing filed its 8-K item 2.02 (`0001628280-26-074645`) and its 10-K (`0001772016-26-000027`) on
  2026-11-18, the close its 2026-11-19 CIQ export carries. Priced at 2026-11-19, the strict reading
  passed that close, and the page would have said "nothing reported after it by the page's close of
  2026-11-19": false if the release came after the bell.
- **B's reasoning, adopted by the operator:**
  - it fails safe and needs no new data;
  - CIQ takes hours to days to load results, so an export closed on a results day likely lacks
    them;
  - EDGAR already dates a filing accepted after 5:30pm ET to the next business day;
  - the cost is that a value dated on a results day waits one more close.
- **Not built:** reading the acceptance time against a 4pm (or 1pm half-day) close. That is an
  optional later refinement.
- **Why the ex-lease close is the exception.**
  - The ex-lease history prices each quarter at CIQ's Historical Capitalization "Pricing as of"
    date. That is the filing date of the quarter's own 10-Q or 10-K (`lease_basis`: "TEV at the
    balance-sheet date, priced at the filing date").
  - On all 16 ex-lease pages, the band's latest close is the filing date of the report it is built
    from (table below). So under `>=`, every ex-lease close is refused by its own report.
  - The next quarter's close is again its own report's day, and the "clears it" remedy (a CIQ export
    carrying a later close) can never arrive inside that band. That is a permanent withholding, not
    "one more close".
  - The operator chose option 1: keep that band strict, and take the same-day releasers it lets
    through as W84 (below).
- **DOES THIS SELECT ON FORM?** No. It moves a date boundary by one day. It reads filing dates and
  the band's own kind, and no outcome or forward return.

**HOW VERIFIED.**
- **Measured at $0 before any code (step 1; boundary below):**
  - **Gate A newly refuses 3 of the 26 pages.** At a 2026-11-19 build and at each page's own build,
    the four export panels of each are dated the day of a report.

    | page | panels' date | first report on or after it, in (date, accession) order | release |
    |---|---|---|---|
    | AMZN | 2026-10-30 | 10-Q `0001018724-26-000040` filed 2026-10-30 | 8-K 2.02 `0001018724-26-000038`, 2026-10-29 |
    | MCK | 2026-11-04 | 8-K item 2.02 `0000927653-26-000279` filed 2026-11-04 (10-Q `0000927653-26-000281` the same day) | same day |
    | UBER | 2026-11-04 | 8-K item 2.02 `0001543151-26-000039` filed 2026-11-04 (10-Q `0001543151-26-000041` the same day) | same day |

    - The other 23 are unchanged.
    - BRBR, FUBO, ORKA, PARR, TGT and TJX are already refused at a 2026-11-19 build by a later filing
      (#1132's record).
    - A re-export closing after the filing clears each of the three.
  - **Gate B, as built (option 1), moves no committed page.**
    - CIQ-history closes: BRBR 09-21, IT 11-11, LLY 11-02, V 11-06, VITL 11-06 and VRRM 11-06 pass
      either way, with no report on their day. GOOGL 09-30 is refused either way, by its 8-K 2.02
      of 10-28.
    - FUBO, ORKA and TECX carry no R1 close.
    - BRBR's same-day case is a close its NEXT build carries (2026-11-18); BRBR stays out of every
      refresh.
  - **What the first ruling, applied to the ex-lease band, would have moved: all 16 ex-lease pages,
    for good.** Each close is the filing date of the report it is built from:

    | page | close | report(s) that day | results released |
    |---|---|---|---|
    | AMZN | 10-30 | 10-Q `0001018724-26-000040` | earlier, 10-29 |
    | BURL | 08-27 | 8-K 2.02 `0001193125-26-369502`; 10-Q `0001193125-26-371311` | same day |
    | CNXC | 10-07 | 10-Q `0001803599-26-000155` | earlier, 09-29 |
    | EPAM | 11-05 | 8-K 2.02 `0001352010-26-000048`; 10-Q `0001352010-26-000052` | same day |
    | MCK | 11-04 | 8-K 2.02 `0000927653-26-000279`; 10-Q `0000927653-26-000281` | same day |
    | NCNO | 08-25 | 8-K 2.02 `0001902733-26-000099`; 10-Q `0001902733-26-000101` | same day |
    | NFLX | 10-21 | 10-Q `0001065280-26-000291` | earlier, 10-20 |
    | NKE | 10-02 | 10-Q `0000320187-26-000193` | earlier, 10-01 |
    | PARR | 08-05 | 10-Q `0000821483-26-000014`; 8-K 2.02 `0001628280-26-052766` | same day |
    | ROST | 09-01 | 10-Q `0000745732-26-000041` | earlier, 08-20 |
    | SMPL | 10-27 | 8-K 2.02 `0001702744-26-000028`; 10-K `0001702744-26-000031` | same day |
    | TGT | 08-28 | 10-Q `0000027419-26-000042` | earlier, 08-19 |
    | TJX | 08-28 | 10-Q `0000109198-26-000048` | earlier, 08-19 |
    | UBER | 11-04 | 8-K 2.02 `0001543151-26-000039`; 10-Q `0001543151-26-000041` | same day |
    | WERN | 11-09 | 10-Q `0000793074-26-000172` | earlier, 10-27 |
    | WLK | 11-04 | 8-K 2.02 `0001262823-26-000076`; 10-Q `0001262823-26-000080` | same day |

- **Pins** (`tests/test_w82_same_day_filing.py`, 13 tests). Each guard is pinned positive AND
  negative, on the frozen cut (`cut-4889ddba`) and the filers' real filings
  (`tests/fixtures/event_rule_filings.json`):
  - (+) BRBR's real 2026-11-18 8-K 2.02 and 10-K refuse a CIQ-history close dated 2026-11-18, end
    to end through `compute_anchor`. This uses a copy of BRBR's frozen page with its close moved to
    that date; no BRBR page is refreshed. Each of the two reports alone refuses it.
  - (+) The same filings refuse a same-day export. The reader lists both reports from the export's
    day and from the close's day (`since=close`).
  - (+) AMZN, MCK and UBER are refused at gate A with their real accessions, at a 2026-11-19 build
    and at their own builds.
  - (−) MCK's and EPAM's ex-lease closes pass on their own same-day 10-Q and 8-K, end to end. The
    same close and filings under the CIQ-history reading are refused, so the divergence is the
    band's, not missing filings.
  - (−) A report the day before still counts as before: BRBR's copy closed 2026-11-19, and AMZN's
    8-K 2.02 of 10-29 against its 10-30 panel.
  - (−) No report on the date passes: IT's 2026-11-11 close (the partial column at its export date,
    BRBR's shape), and an empty filing list.
  - `first_event_after` directly: inclusive by default, strict on request, `upto` bounding both.
- **Rewritten pins of the behaviour reversed:**
  - `test_event_rule.py`:
    - the boundary pin now refuses MCK on its own day (it passed before);
    - the reader keeps BURL's 2026-09-25 10-Q, its panel's own day;
    - the roster walk holds every refusal at a page's own build to a same-day filing, and names
      none of them. A page whose `extraction_version` includes W82's vintage must pass outright.
  - `test_freshness.py`'s wiring pin (every committed page passes its own gate at `assembled_at`)
    takes the same split: on an older stamp only a same-day filing may refuse; on W82's, nothing may.
  - `test_prespend.py`'s own-build walk, through the $0 check's `freshness_refusal`: a page on
    an older stamp must pass the strict gate it ran (`first_event_after` read strictly), and one
    whose stamp includes W82's vintage must pass the head gate.
  - **Which gate a page ran is read from its stamp** (`extraction_version.includes`), never its
    `assembled_at`: a page built today on main's older code ran the strict gate (review round 0).
  - `test_w73_dated_multiple.py`'s one-rule pin now walks both bands:
    - a CIQ-history close equals `event_verdict`;
    - an ex-lease close equals the strict `first_event_after`;
    - TJX's ex-lease close passes on its own 10-Q, and the export gate's reading refuses it.
- **Fail-first, on main `bc1c0e16`'s `vinci/`:**
  - 12 of the 54 tests in the three files fail: 9 new, the 3 rewritten.
  - Each fails at the defect itself: the close or panel passes, the reader lists nothing, or the
    strict keyword does not exist.
  - The 4 negatives pass on both.
- **Mutation:** 12 of 12 mutants red. They include:
  - the rule back to strict;
  - the strict reading ignored;
  - the `upto` bound dropped;
  - the events strictly after;
  - the note always "predates";
  - the reader starting a day late (either feed) or keeping strictly after;
  - the call site dropping the ex-lease divergence, or making every band strict;
  - `close_verdict` ignoring its keyword;
  - the close note always "after the".
- <the impact run, the full gate and the review rounds: in the PR body>

**BOUNDARY.**
- **Pages:** the 26 committed `data/dossiers/*/dossier.json` (11 active + 15 watch), measured
  2026-11-19 at main `ac3c9479`. Re-checked at `bc1c0e16` (#1144 merged): W73 moved no export panel
  and no R1 close on any page.
- **Filings:** `tests/fixtures/event_rule_filings.json`. It holds every 10-Q, 10-K and 8-K item 2.02
  each of the 26 filers made 2026-08-01..2026-11-19, read 2026-11-19 from EDGAR's submissions feed
  through `mechanical.read_filing_events` (#1132).
  - The earliest reference date measured is 2026-08-05 (PARR's ex-lease close), inside that window.
  - The shared SEC cache, read through the repo's client with the cache frozen and sockets refused,
    was set aside. Its submissions copies for these filers were fetched 2026-06-30..2026-11-12 and
    cannot see the November reports.
- **Gate A:** `freshness.export_panels`, judged at a build on 2026-11-19 and at each page's own
  `assembled_at` day.
- **Gate B:** the R1 band's latest close (`anchor.r1_multiple_band(…).band.as_of`), judged up to the
  page's price date (`stock_info.as_of`).
- **Units:** "Newly refuses" means refused by `day <= filed` and passed by `day < filed`.
- **Order:** a gate names its first filing in (date, accession) order.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A value dated on a results day waits one more close**, even where the results came out the day
  before: AMZN's 10-30 panel, whose 8-K 2.02 was 10-29, is refused on its 10-Q.
  - That is the fail-safe side, accepted by the ruling.
  - Reading acceptance times would tell the two apart. It is not built.
- **W84, OPEN (operator 2026-11-19, "Yes, option 1 + W84").**
  - The ex-lease close's strictness lets through the 8 pages whose results came out the SAME day as
    the report their quarter is priced on: BURL, EPAM, MCK, NCNO, PARR, SMPL, UBER and WLK at
    2026-11-19.
  - Where that release came after the bell, CIQ's observation pairs a pre-release price with the
    reported quarter's EBITDA. That is a defect of the observation's pricing date, not of the event
    rule.
  - W84 prices such a quarter at the first close after its filing, in `lease_basis`.
  - Until then, W73's 10% drift flag beside the multiple bounds the risk.
  - The pass note on those closes still reads "nothing reported after it", true by date, and states
    no same-day report.
  - **FALSIFIER:** an ex-lease page among the 8 whose same-day release moved the stock past the
    drift flag's 10% by the page's close, priced and unflagged, means the bound does not hold.
- **The caveat and the gate disagree on a same-day print.** `_panel_freshness_flag` still reads
  `panel < print`, so a panel dated the print's day carries no caveat, while the gate refuses its
  build. Kept as ruled: a caveat, hold scope.
- **No committed page moves.** The gate runs at a build or a precheck, and the anchor at its next
  derivation (W73's $0 artifact PR, active pages, BRBR excluded).
