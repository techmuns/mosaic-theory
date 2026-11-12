---
id: 2026-11-12-fix2-s3-row42a-theme-older-pages
status: shipped
date: 2026-11-12
prs: [1024]
supersedes:
superseded-by:
---

# The theme desk's filings walk names an older submissions page it could not read, and reads a page of another vintage again instead of joining it (STATE row 42 (a))

**WHAT.** TeamNostra fix request 2, stream S3, STATE §5.0 row 42 (a).
- `SecResolver._walk_filings` (`vinci/theme_intelligence/securities.py`) walks a registrant's
  filings back from the recent submissions page. It stops at the first periodic filing on or
  before the as-of date, or at the first annual report for the enrichment step. It read the
  older pages itself:
  - **A page it could not read ended the walk with no word.** That was a 404 or an unreachable
    page (`HttpError`), or a listing with no name (`KeyError`). Each one was a `break`. The
    consumers then read the short list as the SEC's answer. The cover page said "no periodic
    filing on or before … in the SEC submissions index", and the annual report said "no annual
    report (10-K / 20-F / 40-F) on or before …".
  - **Some pages raised instead.** A body that is not JSON (an interstitial: `ValueError`), one
    that is not an object (`AttributeError`), or a span date that is not ISO (`ValueError`)
    raised out of the resolver. It also raised out of the enrichment step, which turns only an
    `HttpError` into "not verified".
  - **A page was held 30 days beside a document held 1, and never checked against the
    document's listing of it.** So a page of another vintage was joined as current.
- **Now the walk returns its rows with why it ended short.** The reason is `""` when it did not,
  and it is memoized with the rows.
  - When the walk found nothing, `pit_cover` and `annual_report` state that reason in place of
    "no … filing".
  - The resolution's note and every UNVERIFIED listing carry it, the path an unreadable cover
    page already takes. So does the enrichment candidate's basis note.
  - **The third consumer, the foreign-filer check (PR round 2, the coordinator):**
    `is_foreign_private_issuer` reads None both for "no periodic report by then" and for a walk
    that stopped short, and the enrichment step reads it as `bool(...)`.
    - So a 20-F filer was recorded as not foreign, its annual report was never asked for, and
      the candidate read "no verified US listing — no annual report to read", with the page
      named nowhere.
    - Now the resolver exposes the walk's reason (`filings_unread`), and the enrichment step
      states it in the candidate's basis note in place of that line.
    - `foreign_filer` stays a bool, False when the check could not finish. It is a schema field
      the market step and the cards read, and the note now says why.
- **A page is held one day, as its document is (`_ONE_DAY`).** It is checked against the
  document's listing of it by `_page_mismatch`, the EDGAR client's #878 check.
  - The check is restated here because the theme desk may import only shared plumbing
    (`tests/test_theme_intelligence_isolation.py`).
  - `test_the_listing_check_is_the_edgar_clients` holds the two to the same answers.
  - On a disagreement, the document and the pages are read fresh once. A second disagreement
    becomes the stated reason.
- An SEC refusal (`SecRateLimitedError`, not an `HttpError`) still stops the run.

**WHY.** #878's record listed this as the one open item no other row tracked. A walk that ends
short with no word breaks "fail loud, never fabricate". "No periodic filing" is a claim about the
registrant, made from a page that was never read.

**HOW VERIFIED.**
- **The live corpus first.** 0 of 261 measured (CIK, as-of) pairs in the theme desk's committed
  registry walk past their recent page (BOUNDARY). None of the 15 theme-desk SEC caches on this
  machine holds an older page at all. The live corpus has nothing for the check to find, so it
  was shown to find something on real data in two ways.
- **(1) Tests on Gartner's committed document and page -001** (#878's fixtures), through a real
  `CachedHttp` served by a mock transport. The document's recent page begins 2021-12-02, so as of
  2021-09-01 the walk must read -001.
  - `tests/test_theme_intelligence_older_pages.py` has 17 tests: 2 added in review round 0 and
    2 in PR round 2. 12 fail on main `53e5f26e`, one of them the parity test, whose function main
    does not have. The other 5 pass on both: four negative pins, and the round-0 pin on the order
    of the name check, which main had right.
  - On main a 404 on -001 read: "listing NOT point-in-time verified as of 2021-09-01: no periodic
    filing on or before 2021-09-01 in the SEC submissions index". Gartner had filed a 10-Q on
    2021-08-03, on that page.
  - On main an interstitial raised `JSONDecodeError` out of `resolve()` and `annual_report()`.
  - On main an earlier vintage of -001, held an hour, was joined: the listing was verified on
    the cover of the 10-Q filed 2021-05-04, where the newest was 2021-08-03.
  - On main a copy held two days was read from the cache.
  - The fix names -001 in each case, or reads it again.
- **(2) An offline replay on the 52 real document/page-001 pairs** this machine's 10
  EDGAR-client caches hold, base against head. Each pair is copied into a scratch cache, both
  stamped as fetched now. `pit_cover` is asked for the day before the recent page's oldest row,
  and every request is refused, so a cover is "not retrievable" but the filing is still named.
  - **27 pairs fetched in the same run** (within an hour). 26 give the same filing on both
    sides, so the listing check refused no real same-run pair. The 27th is Bank of Montreal, as
    of 2025-08-05. On main it read "no periodic filing on or before 2025-08-05 in the SEC
    submissions index", which is false: the walk had stopped at page -002, which the replay does
    not hold. Head names -002.
  - **25 pairs fetched in different runs.** In 22 the page is ~72 days older than its document;
    the others are 83, 51 and 97 days apart.
    - 24 disagree with their listing, and main joined every one.
    - 21 have a same-run pair of the same filer cached beside them. In 9 of those 21, main
      verified the listing on a STALE cover: the newest periodic filing by the as-of date sat in
      the hole between the page and its document. Two examples: UMB took the 10-Q filed
      2021-04-29 where the 10-Q filed 2021-10-28 was the newest; Twist took the 10-K filed
      2021-11-23 where the 10-Q filed 2022-08-08 was the newest.
    - Head names each disagreement. Offline the fresh re-read is refused; live it is read.
    - The 25th (Columbia Financial) agrees with its listing and gives the same filing on both.
- **Mutants.** 9 were run on the fix and 8 were killed: the page TTL back to 30 days, no listing
  check, a silent end, each consumer ignoring the reason, no fresh re-read, no `ValueError`
  catch, and no oldest-row test. The survivor removed a type check on the page body. It showed
  the check was redundant, since a JSON list already fails inside the listing check with a
  `TypeError` that names the page, so the check was removed.
- **Review round 0** (`/code-review high --fix`, 4 findings, 2 fixed behind a test that failed
  first):
  - FIXED: a listing with no name was checked before its span, so an unnamed listing wholly
    after the as-of date, a page the walk never reads, ended the walk as unreadable.
  - FIXED: the document read again after a stale page was kept unchecked, so a JSON list raised
    `AttributeError` out of the resolver. It is now the stated reason.
  - NO CHANGE: the listing check is restated, not imported. The isolation boundary forbids the
    import, and the parity test holds the two together.
  - NO CHANGE: the fresh walk reads every page fresh, including those that agreed. A re-cut
    moves rows from the newest end, so the newer pages are exactly the ones a fresh document
    re-cuts.
- **PR round 2** (the coordinator's review of `04216aa0`, MEDIUM, FIXED behind a test that failed
  first): the foreign-filer consumer above. The test uses ASML's authentic rows and ticker-map
  lines from the frozen J.P. Morgan subset, re-cut so its recent page keeps only the 20-F of
  2026-02-25 and page -001 holds the other 30, listed as EDGAR lists a page.
  - With -001 a 404, the candidate's basis note names it. On `04216aa0` it read "no verified US
    listing — no annual report to read".
  - Its negative: with -001 read, ASML's 20-F of 2025-03-05 makes it a foreign filer, and that
    20-F is the annual report its basis is checked against.
  - No live instance: 0 of 261 measured pairs walk past their recent page (BOUNDARY).
- **Two existing tests changed their fixtures.** Each served a page whose listed `filingFrom`
  was not its oldest row: 2024-01-01 for a page from 2025-02-26, and 2010-01-01 for one from
  2019-02-27. EDGAR does not serve that shape: #878 measured 35 of 35 same-run pairs listing the
  oldest row. Both are restated to their pages' oldest rows, and each test's claim is unchanged.

**BOUNDARY.**
- **The 261 pairs.** The theme desk's registry is at `origin/theme-intelligence-state`
  `ea8fb4a6` (`registry/*.jsonl`).
  - 63 security resolutions with a CIK. Each is dated by the run whose span holds its
    `resolved_at`, taking that run's `as_of`.
  - 322 enrichment candidates whose annual report was read (`basis_check` not UNCHECKED, or a
    basis source), over 92 sets. Each is dated by its set's `as_of` and mapped to a CIK through
    the SEC ticker map, by its listing's ticker, registrant or hint.
  - Together: 303 distinct (CIK, as-of) pairs over 168 CIKs. 42 have no cached submissions
    document on this machine, which leaves 261 measured: 54 with a resolution, 224 with an annual
    read. The as-of dates run 2026-10-13 → 2026-11-11.
  - Documents came from 16 caches: the 15 theme-desk caches plus the primary checkout's EDGAR
    cache. Each pair used the first copy fetched on or after its as-of, else the latest before;
    258 of the 261 copies were fetched before their as-of.
  - A pair "walks past its recent page" when its recent page holds no periodic filing (or, for
    an annual read, no annual report) on or before the as-of. Every recent page reached back at
    least 371 days before its as-of.
- **The 52 replay pairs.** Every submissions document in
  `/Users/work/Documents/GitHub/mosaic-theory/data/cache/sec` and
  `.claude/worktrees/*/data/cache/sec` (10 directories) whose listed page -001 is cached beside
  it. Measured 2026-11-12, head against base `53e5f26e`. "Same run" means fetched within an hour
  of each other. A stale cover is one where the same-run pair's newest periodic filing by the
  as-of is not the accession main verified on.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **No verified listing is lost.** A walk that reaches an unreadable page still yields
  UNVERIFIED listings, now with the page named. Before, it gave the same with a false reason (a
  404) or raised (an interstitial). A verified listing still needs a periodic filing in hand.
- **A cross-run pair costs more live:** one more document read, with the pages re-read fresh,
  once per registrant, as-of date and walk.
- **Found here, not fixed (hold scope):**
  - The DOCUMENT read, `submissions()`, catches only `HttpError`. A non-JSON document body still
    raises `ValueError` out of the resolver and the enrichment step.
  - `_rows` skips a row whose date is not a date, and its `zip(strict=False)` silently cuts
    arrays of unequal length to the shortest.
  - A failing page is asked for again by each walk: the periodic walk and then the annual walk
    for one date, and again for every other as-of date. Each ask pays the retry ladder. There is
    no failure memo like `sub_errors` for the document. Main did the same.
  - **The impact check's theme-desk consumer fails its second side on a WAL registry.**
    `vinci/impact/run.py`'s `snapshot_store` opens the source with `with sqlite3.connect(...)`,
    which commits but never closes, so the source registry's `-wal`/`-shm` stay on disk. The
    `{theme}` layout then symlinks them beside the other side's snapshot. Here, head's publish
    exited 1 while base's passed. Head passes when run directly. With the registry in DELETE
    journal mode both sides write the same 243 files, differing only in `published_at`.

**ROW 42 STAYS OPEN, WITH ONE ITEM.** All of the older-page reads are fixed: (1) by #1020, (2) by
#1016, (a) here. #878's record flips to `shipped`. Left is (b): a name the monitor drops is stated
only in the day's notes, and no web view renders them. That is a render change, and a Phase-1
preview comes first.
