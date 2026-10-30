---
id: 2026-10-30-cover-dated-shares
status: open
date: 2026-10-30
prs: []
supersedes:
superseded-by:
---

# A share count tagged after its own filing is dated from its cover and cross-checked, and EDGAR reads that stopped short now say so

**WHAT.** Phase 2, Session C, batch C1 (audit X1(a), E1-D11, E1-D16 and the covenant-pointer caps).
- **A share count tagged after its own filing is dated from its cover (X1(a); operator ruling
  2026-10-30, verbatim: "Yes, cross-check").** `vinci/edgar/cover_count.py`, read by the three
  share readers in `mechanical.py` (`_share_count_trend`, `_edgar_shares_outstanding`,
  `_adjusted_facts`):
  - THE DATE comes from the filing's cover sentence, by an anchored parse: the count's FIRST
    occurrence as the cover prints it (`151,982,804`), and exactly one date in its sentence
    introduced by "as of", "as at", "at" or "on". The hidden inline-XBRL header is dropped before
    the 400,000-character head is read. A date further before the filing than its form's cover
    counts at (`MAX_LEAD_DAYS` 90; 180 for a 20-F or 40-F) is not the count's.
  - UNREAD — no fetcher, the filing not in the submissions index, a failed fetch, no such
    sentence — the count is dated at its filing day, an upper bound, and printed `filed <date>`.
  - THE VALUE is held against the same filing's balance-sheet `CommonStockSharesOutstanding`
    (latest instant), else its quarter diluted weighted average, else the previous
    correctly-dated count. Past `CROSS_CHECK_TOL` (5%) the count is UNKNOWN: the share count
    reads None, a trend across it reads UNKNOWN, and a caveat (`share count UNKNOWN:`) names both
    figures.
  - Each correction is a QA flag (`share count:`, added to `flags._QA_MARKERS`) naming the
    accession, the tagged date and the date read or the bound, for every count in the trailing
    ~2y window.
  - A cover is fetched only for a count filed inside that window, through the assembly's SEC
    `CachedHttp`, for the name being assembled. `SecRateLimitedError` is not caught.
- **Full-text search reads every page, or says it did not (E1-D11).** `EdgarClient.fulltext_search`
  read one 100-hit efts page and returned it as the answer. It now reads page after page (`from=`)
  until every match is read or `FTS_MAX_PAGES` (5) is spent, and returns an `FtsResult`: the hits,
  efts's own `total`, and `capped`. The first page keeps the URL it always had, so the cache key
  does not move.
- **The theme prefilter names a query its page cap cut (E1-D11).** `mention_prefilter` takes
  `capped`, the twin of `skipped`: each batch×phrase that spent `max_pages` with matches unread is
  named with what it read of its total. `scan_driver_exposure` prints them under
  `!! PREFILTER PAGE CAP`, the matched set being a lower bound.
- **The covenant-pointer table states its caps.** `_covenant_pointers` searches 6 agreement
  families (`_COVENANT_QUERY_CAP`) and names 4 aggregate lines (`_COVENANT_GENERIC_CAP`). Each cap,
  when it binds, now adds one row saying what it left out, and a family whose capped search located
  fewer than two pointers says it read N of M hits. When nothing at all is located and the search
  stopped short anywhere, the note says so instead of `COVENANT_SEARCH_FOUND_NOTHING` ("across the
  filing history"), a claim only a whole search can make.
- **`latest_instant` returns None when no point is an instant (E1-D16).** It fell back to the whole
  list, so a list of flows answered with a flow.

**WHY.** The one-sided age check (`ref - end <= bound`) passes any future date, so a count tagged
after its own filing always read as fresh, and won "newest" over the real count: THM's 2023 count,
tagged 2033, was served as current; REPX's 2024 count, tagged 2029, shadowed its 2026-08-03 count.
The tag is a slip — the filing's own cover states the date (VRRM: "As of August 3, 2026, there
were 151,982,804 shares", in a 10-Q filed 2026-08-05 and tagged 2026-08-31). Dropping such a count
would have turned VRRM's, AAL's and JJSF's current counts UNKNOWN; dating it at the filing alone
would have printed a bound as a count date. The operator chose to read the cover and cross-check
the value.

CLAUDE.md: a truncated output prints its own truncation. The aggregate-line cap dropped
lines on 13 committed pages with nothing on the page saying so (LLY named 4 of its 52); the
prefilter's cap and the search's single page each turned "we stopped reading" into "there is no
more". A `latest_instant` that may return a flow is a reader whose population is wider than its
name; nothing feeds it flows today, which is the time to close it.

**HOW VERIFIED.**
- Failing first on main (`origin/main` 9503c4fa, in a throwaway worktree): the new test file does
  not import (`FtsResult` is absent), and the same behaviours through main's own API show each
  defect — `latest_instant(WOR revenue)` returns `Revenues` 2025-06-01..2026-05-31, not an
  instant; a 250-match search returns 100 hits from 1 request, as a bare list; `mention_prefilter`
  has no `capped`; LLY's table holds 4 aggregate rows of 52 and no row naming the cut.
- `tests/test_efts_caps_and_instants.py` (12): each behaviour with a positive and a negative pin —
  a one-page search is one request on the old URL; a prefilter read whole names nothing; BRBR's
  2-line panel gains no row; an uncapped search that found nothing keeps the found-nothing note.
  Fixtures are real: WOR's committed companyfacts subset, the committed instruments of LLY, BRBR,
  AORT, MVST and WERN, and efts pages in the shape efts serves.
- Real-data runs (no network):
  - The `"defense"` prefilter replayed over the cached efts responses (18 batches, 1,727 CIKs):
    0 skipped, 6 capped, each named — `'defense' × batch of 100 CIKs: read 500 of 530 hits
    (5-page cap)`, and 536, 564, 599, 608, 774.
  - The pointer caps over every committed page's own instruments: 13 of 26 pages gain one row —
    AMZN 4 of 8, CNXC 4 of 5, GOOGL 4 of 17, IT 4 of 6, LLY 4 of 52, NFLX 4 of 13, NKE 4 of 10,
    ROST 4 of 7, TGT 4 of 8, TJX 4 of 6, UBER 4 of 12, V 4 of 20, WLK 4 of 13. The query cap binds
    on none (the most agreement families on a page is 5: AORT, MVST).
  - `latest_instant` over every cached companyfacts blob through its real callers (net debt and the
    share count): it served a flow 0 times, and net debt and the share count move on 0 filers.
- X1(a), failing first on main through main's own readers (the fixtures below): THM serves
  195,885,531 (its 2023 count, tagged 2033), REPX 20,400,032 (tagged 2029, over its real
  2026-08-03 count of 22,153,785), and VRRM's trend reads "164,658,507 (2024-08-31) → 151,982,804
  (2026-08-31)". `tests/test_cover_dated_share_counts.py` (20) does not import on main
  (`vinci.edgar.cover_count` is absent). On the branch THM reads UNKNOWN (its real newest count,
  2026-05-01, is 182 days old on 2026-10-30, past the 180-day bound), REPX 22,153,785, and AAL keeps
  661,969,951, dated no later than its filing (2026-07-23).
- X1(a) pins, each from real text: VRRM's and JJSF's cover sentences read 2026-08-03 and
  2026-05-01; one share off, or a second date in the sentence, reads nothing; Hawaiian Electric's
  cover table reads its market-value date (2025-06-30), which the lead window refuses; Whitestone's
  "As o f May 4, 2026" reads nothing, and its count's later occurrence (the balance sheet) is never
  consulted; a hidden XBRL header longer than the head cannot push the cover out. VRRM's newest
  count mutated 10% high is refused against its filing's diluted weighted average (151,945,000),
  and the share count and trend then read UNKNOWN. An AST pin holds every call of a share reader
  in `mechanical.py` to passing `http=`.
- **The tolerance, by face validity.** Every dei cover count in the cache against the SAME
  filing's balance-sheet `CommonStockSharesOutstanding` (66,950 pairs): the gap's median is
  0.05%, p75 0.36%, p90 2.07%, p95 8.72%; 85.4% sit within 1%, 89.8% within 2%, 93.5% within 5%,
  95.4% within 10%. Against the quarter diluted weighted average where the filing has no
  balance-sheet count (14,289): median 1.09%, p90 5.68%, 89.0% within 5%. 5% admits a month or two
  of ordinary buybacks or issuance and refuses what a second share class or a unit slip produces.
  Nothing here reads a forward return.
- **The lead window, by face validity.** filed − tagged date over every correctly-dated dei cover
  count in the cache: 10-K (22,251) median 7 days, 98.36% within 90; 10-Q (65,325) median 6, 99.41%
  within 90; 20-F (1,741) median 91, 96.32% within 180; 40-F (484) median 79, 99.17% within 180.
- **The parser over the corpus**, read exactly as production reads (header dropped, head, first
  occurrence, lead window), over every dei cover count whose accession has a cached document
  holding the count (3,391 of the 3,450 with any cached document of the accession). For the 3,385
  CORRECTLY-dated counts the read must equal the filer's own tag: read 2,902, equal 2,877 (99.1%),
  differ 25, refused by the lead window 9, unread 474. Four of the 25 inspected are the filing
  disagreeing with itself, not the parser: PagerDuty's cover states March 9 against a tag of
  March 10; Chimera's and CytomX's covers state January 31 and February 28 against period-end
  tags; Natural Resource Partners' count first appears on its balance sheet, "outstanding at
  March 31, 2026", which is true of that count. The 9 refused are market-value dates and a cover
  stating the wrong year (Hawaiian Electric, CVB, Cathay's "As of February 13, 2025" in a 10-K
  filed 2026-03-02). All 6 future-dated counts with a cached cover are read, each within its
  lead: Lindsay 2026-03-31 (tag 2026-05-31), Farmers National Banc 2026-02-20 (tag 2026-03-20,
  read only once its 756,469-character hidden header is dropped), JJSF 2026-05-01, and VRRM
  2026-02-19, 2026-05-01, 2026-08-03. Before the first-occurrence rule and the lead window, the
  same run read 41 differing dates, among them Whitestone's balance-sheet 2026-03-31 for a cover
  stating "As o f May 4, 2026".
- **The rule over all 107 future-dated points** (covers read from the cache only, so a filing
  not cached is dated at its filing day here where assembly would fetch it): 6 dated from their
  cover, 101 at their filing day; the value agrees with its own filing on 91, is refused on 15,
  and has no other count to check against on 1. The ruling's five filers, each as its share count
  is served now:
  - **VRRM** 151,982,804, tag 2026-08-31 → cover 2026-08-03; agrees +0.02% with the same 10-Q's
    diluted weighted average (151,945,000; the filing tags no undimensioned balance-sheet count).
  - **JJSF** 18,753,416, tag 2026-05-14 → cover 2026-05-01; agrees +0.00% with the same 10-Q's
    balance-sheet count (18,753,000 at 2026-03-28).
  - **AAL** 661,969,951, tag 2027-07-17 → filed 2026-07-23 (its 10-Q is not cached); agrees
    +0.01% with the same filing's balance-sheet count (661,936,666 at 2026-06-30).
  - **REPX** 22,153,785 at 2026-08-03, its real newest count, correctly tagged; the count tagged
    2029 dates at its 10-K/A's filing day, 2024-04-03.
  - **THM** 261,637,473 at 2026-05-01, its real newest count, correctly tagged; the count tagged
    2033 dates at its filing day, 2023-11-08. On 2026-10-30 THM's share count reads UNKNOWN: its
    newest count is 182 days old, past the 180-day bound.
- **Every committed page at its own reference date** (26; main's readers against the branch's,
  both through a read-only double over the cache, nothing fetched): the share count and the trend
  are identical on 25. VRRM's share count stays 151,982,804; its trend reads −7.8% over ~1.8y,
  "164,804,157 (2024-10-25) → 151,982,804 (2026-08-03)", where main reads −7.7% over ~2.0y from
  2024-08-31. Its four in-window corrections flag: 0001193125-26-335490 (tag 2026-08-31, cover
  2026-08-03), -26-209227 (2026-05-31 → 2026-05-01), -26-067293 (2026-02-28 → 2026-02-19), and
  0000950170-25-029180 (2025-02-28, cover not cached, so filed 2025-02-27; assembly fetches it).

**BOUNDARY.**
- Cached companyfacts: the primary checkout's `data/cache/sec`, the latest blob per CIK, 2,253
  blobs fetched 2026-08-06 to 2026-10-27, read 2026-10-30 at 9503c4fa. Share points: the served
  `extract_points(facts, "shares")` series, non-zero values — 91,485 points, 107 of them ending
  after their own filing, at 81 filers. Cached filing documents: the `.htm` files under each
  accession's `Archives` path in the same cache; a cover counted as read only from those.
- Cached efts: the primary checkout's `data/cache/efts`, 1,223 responses carrying a hits body
  (1,200 batched, 19 single-CIK, 4 unscoped). Batched queries grouped by phrase, CIK batch, forms
  and dates: 984 groups, 6 of them ran all 5 pages with a total above 500, all `"defense"` over
  2025-09-01..2026-06-30. Of the 19 single-CIK responses, 15 are covenant queries
  (`"Credit Agreement"` 9, `"Loan Agreement"` 5, `"Indenture"` 1; 8-K) with totals 2 to 58; the one
  whose total exceeds its page is a `"data center"` search (154).
- Committed pages: the 26 `data/dossiers/*/dossier.json` at 9503c4fa that this session may open
  (one held page not opened); an instrument is an agreement family when `_COVENANT_CLASS_RE`
  matches its description, else an aggregate line, each family counted once.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A capped search costs up to 5 efts requests where it cost 1. The covenant search runs at most 6
  queries an assembly, and the 15 cached covenant queries match at most 58 filings each, so the
  usual cost is unchanged: one request a family.
- **Pages move only at re-assembly.** The 13 pages above gain their truncation row when next
  assembled; added to STATE row 41. So is VRRM's trend line; its count and anchor do not move.
- **A refused count is UNKNOWN, not a fallback.** Fifteen of the 107 future-dated points refuse at
  5% (all in filings from 2012 to 2025; none is read by a committed page). Some are unit slips
  (a balance-sheet count tagged 1,000 times too large at Ormat, in thousands at Fennec); others are real
  issuance between the balance-sheet and cover dates, which the rule cannot tell from a slip and so
  refuses. Falsifier: a page whose share count reads UNKNOWN where the filing's cover and balance
  sheet both state the count the page needs.
- **An unreadable cover is a bound, not a date.** A count whose cover cannot be had is printed
  "filed <date>". The bound is correct and never late, but it is up to the form's lead earlier
  than the count's true date would read.
- The prefilter's cut is printed, not persisted: a scan's saved output does not carry it, as it
  does not carry `skipped`. Falsifier: a saved scan read later as complete when its log printed a
  page cap.
