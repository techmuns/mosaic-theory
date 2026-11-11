---
status: shipped
date: 2026-11-11
prs: [1020]
supersedes:
superseded-by:
---

# STATE row 42 (1): a name whose filings window cannot be read drops its own freshness row, never the monitor day; row 42 now holds only the theme desk's own older-page reader

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
  CLI's other submissions read (`_cmd_reconcile_identity`'s `filings`) catches the same pair.

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
  named in a note. Before, the day aborted. A re-run of the same day replaces it, because re-running
  the front of the book is routine (`write_snapshot`). An SEC refusal still stops the run.

**ROW 42 STAYS OPEN, NARROWED.** Both of row 42's edges are fixed. #878's record lists one more
open item that no other row tracks.
- `theme_intelligence.securities` reads older pages itself. It holds them for 30 days beside a
  document held for 1, never checks them against their listing, and stops at a page it cannot read
  with no note. This is still true at `1df0dc18`: `_walk_filings` holds pages for 30 days and
  `break`s on `HttpError`/`KeyError`.
- So #878's record stays `open`, and row 42 now cites it for that item alone.
