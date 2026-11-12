---
status: shipped
date: 2026-11-11
prs: [1020]
supersedes:
superseded-by:
---

# STATE row 42 (1): a name whose filings window cannot be read drops its own freshness row, never the monitor day; row 42 now holds the theme desk's own older-page reader and the web's silence on a dropped name

**WHAT.** `cli._cmd_monitor` reads a 760-day EDGAR filings window for each name in the freshness
set. When that read now fails, the name's freshness row is not written, and the day carries a note
naming the ticker, the window and the error. The note reads `FILINGS <T>: its EDGAR filings window
since <date> could not be read (<error>) · its freshness row is NOT written`. Every other name's
row, the book, the spread and the realized view are written as before.

A read fails in one of three ways:
- `HttpError`: an older submissions page could not be read, which #878 made raise, naming the
  page.
- `HttpError` again: the submissions document itself could not be read.
- `ValueError`: the document came back as a 200 whose body is not JSON (an interstitial). The
  CLI's other submissions read (`_cmd_reattribute_prices`'s `filings`) catches the same pair.

An SEC refusal still stops the run. `SecRateLimitedError` is deliberately not an `HttpError`
(`vinci/netcache.py`): it means SEC is blocking this process, and a run that moved on to the next
name would send into the block.

This closes row 42's edge (1). Edge (2) closed in #1016. Stream S3 of fix request 2 took it on
2026-11-11 (issue #1004). It waited for coordinator A's `vinci/cli.py` work: #1006, then #1015
(merged as `1df0dc18`).

**WHY.** #878's record, "OPEN — NOT THIS PR": "One heavy filer on the watch list whose page cannot
be read stops the whole monitor day. Fix: record that name's window as unread and carry on,
loudly." Every other windowed caller already degraded that `HttpError` to its UNKNOWN. The
monitor was the one with no handler. The abort came after every price, dividend and split read,
so a day was lost to one name.

**The row is dropped rather than written with no filings.** An empty filings list would set
`unread_print` false: a fabricated "no new filing". The freshness row has no typed state for
"filings not read", so the precedent in the same loop applies. A record with an unreadable
evidence date (`UnreadableEvidenceDateError`) already has its row left out and named. A day with
no row for a name adds nothing to that name's measured-criterion history: `_history_for` reads
only the rows a day has, and returns None when no prior day carries the row at all.

**HOW VERIFIED.**
- **Fail first, through the real command:** `tests/test_monitor_unreadable_window.py`, 6 tests.
  - The setup:
    - the real `vinci monitor` re-cut over the committed ledger, securities and benchmark
      assignments (`tests/test_monitor_ref_date_bound.py`'s harness);
    - for IT, a real `EdgarClient` behind a real `CachedHttp`, served Gartner's committed
      submissions document and its older page -001 (`tests/fixtures/submissions_pages/`, #878's
      fixtures) by a mock transport;
    - every other name on the harness's frozen filings.
  - On main `1df0dc18`, 4 fail and 2 pass (the two negative pins). All 6 pass on this branch.
  - **An older page that cannot be read.** Page -001 was answered with an interstitial, then with
    a 404.
    - The setup: the committed document's recent page begins 2021-12-02, so a 760-day window
      reaches page -001 only from a day before 2024-01-01. A re-cut of 2023-09-01 (window from
      2021-08-02) is the real command's one path to the page on committed data.
    - On main, the command raised the page's `HttpError`: "older submissions page
      CIK0000749251-submissions-001.json for CIK0000749251 could not be read, so the filings
      window from 2021-08-02 is incomplete". No day was written.
    - Now the day is written, IT has no row, WERN still has its row (it is read after IT), and
      the note names IT, the window and the page.
  - **(−) The same page, served.** IT's row is written, and its newer filings include the 10-Q of
    2021-08-03 and the 8-K of 2021-11-02, which only page -001 holds. The day has no unread note.
  - **A submissions document that cannot be read,** on the committed 2026-09-22 day's re-cut. IT's
    document was answered with an interstitial (`ValueError`) and then a 404 (`HttpNotFoundError`).
    - On main, both abort the day.
    - Now IT has no row. WERN's newer filings and evidence date equal the committed 2026-09-22
      day's exactly.
  - **(−) An SEC refusal still stops the day,** and nothing is written.
- **Mutants**, each on this branch's code:
  - catching `HttpError` alone fails 1 test (the document's interstitial);
  - catching `Exception` fails 1 (the SEC refusal);
  - writing the row with no filings in place of `continue` fails 4.
- The harness's existing monitor tests (`tests/test_monitor_ref_date_bound.py`, 15) still pass.
- **A real run of the monitor, on the machine's cached responses, $0, nothing sent.**
  - The setup: `vinci monitor --ref 2026-08-05 --out <scratch>`, run on main's code (`1df0dc18`)
    and on this branch's, over main's committed inputs. Every response came from the
    newest-fetched cached copy of its URL across the primary's and every worktree's `data/cache`
    (10 roots), whatever its age. A miss raised, and nothing was written to any cache. 2026-08-05
    is the impact check's price-store frontier, the one recent day whose every read is cached:
    36 reads, 26 distinct URLs.
  - **The control, no failure.** Main and this branch write the same day, field for field: the
    book (IT, SMPL ×2, VRRM), five freshness rows (IT, MVST, NCNO, SMPL, WERN) and 9 notes.
  - **IT's submissions document failing,** with the `HttpError` a 5xx retry storm ends in
    (`Exhausted retries for https://data.sec.gov/submissions/CIK0000749251.json`).
    - Main raised it and wrote no day. MVST, NCNO, SMPL and WERN, sorted after IT, were never
      read.
    - This branch wrote the day. IT's freshness row is absent, and the other four rows, the book,
      the spread and the realized view equal the control's exactly. One note is added and none is
      removed: `FILINGS IT: its EDGAR filings window since 2024-07-06 could not be read
      (HttpError: Exhausted retries for https://data.sec.gov/submissions/CIK0000749251.json) ·
      its freshness row is NOT written`.
- **Review round 0 (`/code-review high --fix`):** this record named the CLI's other
  `(HttpError, ValueError)` handler after the wrong function (now `_cmd_reattribute_prices`), and
  the first commit message stated a count without its boundary (amended). Three findings were
  kept as built:
  - the note carries the error's own text, up to 200 characters of a non-retryable answer's body,
    as the unreadable-record note does;
  - a wholly degraded EDGAR costs one retry storm per name (below);
  - `ValueError` is caught across the whole read, as the CLI's other handler catches it. Each
    parse error inside the reader is a failure to read the window.
- **PR round 1 (the in-session `/code-review high`, run because Codex's review failed on its usage
  limit), **with the coordinator's independent review of `35ed5238` folded in:** 5 findings, none
  fixed (3 DEFER, 2 DISMISS).
  - The three deferrals are under WHAT IT COSTS.
  - Dismissed: this test file imports the ref-date harness's private helpers. Other test files in
    the suite already import helpers from one another, and nothing fails on it.
  - **Dismissed, with a pin (the coordinator, LOW):** the coordinator suggested catching
    `json.JSONDecodeError` instead of `ValueError`, so that a code defect stops the run. But
    `ValueError` is also how unreadable SEC data reaches the monitor:
    - `_page_filings` reads the recent page's SEC-supplied `filingDate` and `reportDate` with
      `date.fromisoformat`, unwrapped;
    - the older pages' same read is wrapped into an `HttpError` ("could not be read") in
      `_older_filings`;
    - so a blank date on a recent row (#878's review round 2 named the shape) raises a bare
      `ValueError`.
    - Pinned by `test_a_blank_date_on_the_recent_page_drops_its_row_not_the_day`. It blanks the
      newest 10-Q's `filingDate` in IT's committed document. On head, the day is written, IT is
      named and WERN keeps its row. With the narrowing, it fails: `client.py:472: ValueError:
      Invalid isoformat string: ''`, an aborted day. The other 6 tests pass either way.
    - The narrower catch becomes right once the reader wraps that read into `HttpError` as it
      wraps the older pages'. That change is in `vinci/edgar/client.py` and outside this PR.
    - The test file now holds 7 tests.

**BOUNDARY.**
- "760-day window": `known_through - timedelta(days=760)`, where `known_through` is the run's
  `--ref` (today on a routine run).
- "6 tests", "4 fail and 2 pass": the new file at this branch's first commit, run against main
  `1df0dc18`'s `vinci/cli.py`.
- **No name the monitor reads today has a window that reaches an older page.**
  - The population: the 7 names in the freshness set on 2026-11-11 (BRBR, EPAM, IT, MVST, NCNO,
    SMPL, WERN). These are the ledger's live verdicts on that day, after its corrections and
    voids, plus the `watch` and `pending_analyst` records, each with a `scenarios/<T>.json`. All
    read at `1df0dc18`.
  - The window: from 2024-10-12.
  - Each name was checked against the newest-fetched cached copy of its submissions document
    across the primary's and every worktree's `data/cache`, fetched 2026-11-02 to 2026-11-11 and
    read 2026-11-11, with nothing sent.
  - IT has the least headroom. Its recent page now begins 2022-02-08, about 2 years 8 months
    before the window's start.
  - So the older-page case is latent today. The document case is not: SEC can serve any name's
    document as an interstitial on any day.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A name whose window cannot be read loses its whole freshness row that day,** including its
  triggers, passed deadlines and measured criteria, not only its filings. The note names it. A
  typed "filings not read" state on `FreshnessRow` would keep the rest. That is a schema change to
  the committed days, their render and the web twin, and is not built here.
  - Falsifier: a day on which a name's passed deadline or kill criterion was hidden behind an
    unreadable window.
- **If EDGAR fails for every name, the day is written with no freshness rows,** and every name is
  named in a note. Before, the day aborted at the first. Each name now pays its own 5xx retry
  storm (5 attempts, about 15.6 s), so 7 names cost about 110 s and 35 requests. A re-run of the same day replaces it, because re-running
  the front of the book is routine (`write_snapshot`). An SEC refusal still stops the run.

- **DEFERRED (PR round 1): on the web the name vanishes with no word.**
  - The web's freshness panel (`frontend/views/shared/decision-log.js`, `freshnessPanel`) renders
    only `mon.freshness`, and no web view renders a monitor day's `notes`. So the `FILINGS` note
    reaches the CLI printout and the committed day's JSON only. The unreadable-record note this
    follows, and every other day note, is in the same position.
  - The fix is a render change to the panel, which the PREVIEW RULE gates on a preview and
    approval.
  - Falsifier: a deployed panel showing the day's names with no mention of one that was dropped.
  - **THIS PR WIDENS IT (PR round 2, the coordinator):** before, one unreadable window wrote no
    day at all, which was loud. Now the day is written and the panel shows N−1 names without
    saying one is missing. That is "A TRUNCATED OUTPUT PRINTS ITS OWN TRUNCATION", and it was
    recorded only here. It is now STATE row 42's OPEN (b), owned by the agent, with the fix
    named as a render change that the PREVIEW RULE gates. §5.0 is at its 60-line cap, so it
    joins row 42 rather than taking a row of its own.
- **DEFERRED (PR round 1): which names went unread is carried only in prose.** No typed field on
  the day records it, so any later consumer must parse `FILINGS <T>:` from free text, or use the
  typed state above, which is not built.
- **DEFERRED (PR round 1): a cut response body is printed with no mark that it was cut.** The
  note prints the error as raised. A non-retryable `HttpError` carries the response body cut at
  200 characters (`vinci/netcache.py`, `resp.text[:200]`), against "A TRUNCATED OUTPUT PRINTS ITS
  OWN TRUNCATION". The fix is in netcache's messages, which every caller prints.

**ROW 42 STAYS OPEN, WITH TWO ITEMS.** Both of row 42's edges are fixed.
- (a) #878's record lists one more open item that no other row tracks:
  - `theme_intelligence.securities` reads older pages itself. It holds them for 30 days beside
    a document held for 1, never checks them against their listing, and stops at a page it
    cannot read with no note.
  - This is still true at `1df0dc18`: `_walk_filings` holds pages for 30 days and `break`s on
    `HttpError`/`KeyError`.
  - So #878's record stays `open`, and row 42 cites it for this item.
- (b) The web's silence on a dropped name, which this PR widens (above, PR round 2).
