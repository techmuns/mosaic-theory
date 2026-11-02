---
id: 2026-10-30-submissions-pages
status: open
date: 2026-10-30
prs: [878]
supersedes:
superseded-by:
---

# A filings window that reaches past the submissions index's recent page reads every older page it overlaps, or raises naming the one it could not read

**WHAT.** Phase 2, Session C, batch C3 (audit E1-D10).
- `EdgarClient.recent_filings(cik, forms=…, since=…)` read only the submissions document's
  `filings.recent` block — a filer's newest ~1,000 filings — and ignored the older pages the
  document lists under `filings.files`. A window that began before the recent page's first row
  ended there, silently: a short list read as "no filings before".
- Now, when `since` falls before the recent page's oldest filing, every older page the window
  overlaps is read too (`_window` → `_older_filings` → `_older_page`), through the same SEC
  client and its shared limiter, and parsed by the one row reader both kinds of page share
  (`_page_filings`). A page is skipped as wholly before the window only when its listed
  `filingTo` + 1 day is before `since`: a page's rows run to `filingTo` + 1 (review round 2 —
  skipping on `filingTo` alone dropped BMO's 51 filings of 2025-08-05 for a window opening that
  day).
- **AN OLDER PAGE IS NOT IMMUTABLE** (review round 2). EDGAR re-cuts the older pages from the
  newest end whenever the recent page's boundary moves — WFC's page -001 spanned
  2020-02-11..2024-10-20 on 2026-06-30 and 2020-05-29..2025-10-28 on 2026-10-30 — so a page cached
  apart from the document listing it is another vintage: it leaves a hole between its newest row
  and the recent page, or repeats rows the recent page holds. Three things follow:
  - a page is cached no longer than its document (`_ONE_DAY`; the first cut held it 30 days, as
    `theme_intelligence.securities` holds its pages);
  - each page is checked against the listing that names it (`_page_mismatch`: its row count is
    `filingCount`, its oldest row is `filingFrom`, its newest at most `filingTo` + 1 day). On a
    disagreement the window is read once more with the document and its pages fetched fresh
    (`_submissions(fresh=True)`, `ttl_seconds=0`); a second disagreement raises, naming it;
  - each accession is returned once across the pages (a belt: the listing check already refuses
    the mixed vintages that repeat one).
- A page the window needs and cannot read RAISES `HttpError`, naming the page — unreachable,
  answered with something that is not JSON (an interstitial), not an object, missing its arrays,
  listed with no name, listed with a span date that is not ISO, or disagreeing with its listing
  when read fresh, all alike (in-session review rounds 0 and 1: a `ValueError` or `KeyError`
  would have escaped the callers that catch only `HttpError` and aborted the assembly). A blank
  `filingDate` on a recent row is skipped where the reader decides whether to read older pages
  (review round 2: it raised a `ValueError` where main returned the 8-Ks).
- **Every windowed caller but one turns that `HttpError` into its UNKNOWN**: the ownership
  register, insider and Section 16 scans, the dilution scan, the rank's 8-K scan, the theme
  prefilter, the gap and maturity 8-Ks. **The exception is the monitor** (`cli._cmd_monitor`'s
  760-day window has no handler): one unreadable older page aborts the whole monitor day. Not
  Session C's function; OPEN below and STATE §5.0 row 42. (The first cut of this record, and
  commit `af70903c`, said "every windowed caller" — that was false.)
- A page that FAILED is remembered by the client, as the document's failure is (`_submissions`'
  memo, under the page's name): an assembly makes several windowed reads of one filer, and
  without it a degraded feed would re-run the retry storm (≈15.6 s) at each. A page read is not
  remembered — the disk holds it.
- Without `since`, only the recent page is read, as before — those callers ask for the newest
  filing of a form, which the recent page holds by construction.
- `mechanical._ownership_events`' docstring stated the old limit as a known risk; it now states
  the window is read whole.
- This closes the UNLOCK named in `docs/records/2026-08-12-open-observations-surfaced-by-pr-2-s-corpus-swee.md`
  ("read the `filings.files` overflow pages, then pin truncation on a frozen fixture"), where
  NFLX's index had ~2 months of headroom on the 3-year ownership window.

**WHY.** A heavy filer's recent page covers months, not years. Wells Fargo's recent page holds
1,305 filings — from 2025-10-30 on its document of 2026-10-30 (the coordinator's reviewer's
reading of that copy), from 2025-10-31 on the live read of 2026-10-31 — and its oldest Form 4
there is 2025-12-09 (the first cut of this record called that the recent page's start): main read **98** Form 4s in a 3-year window where the filer made **308** — two thirds
of the window missing and nothing said. The insider, ownership and dilution scans read exactly
such windows, and an empty or thin result there is PRESENT ("none in window"), never UNKNOWN.

**HOW VERIFIED.**
- **Failing first.** `tests/test_submissions_older_pages.py` (16). Fixtures are Gartner's real
  submissions document and its real older page -001, each cut to a slice of its rows
  (`tests/fixtures/submissions_pages`; the document's listing of -001 restated to the cut page in
  round 2, so the listing check reads it as consistent); HTTP is mocked.
  - On main `08948b5a`: the older-page read and the unreadable-page raise FAILED (page -001's 8-Ks
    missing; no raise); the two negative pins (a window inside the recent page, no window) passed
    on main and pass now.
  - On this branch's first cut: the failed-page memo (the page was fetched twice).
  - On the round-0 head: the interstitial, missing-array and unnamed-page cases (a `ValueError`, a
    `KeyError`, a fetch of `/None`).
  - On `af70903c` (round 1): a non-ISO `filingTo` (a `ValueError`).
  - On `2b02c9b0` (round 2), all seven: the page TTL (30 days against the document's 1); a stale
    -001 missing an 8-K the window holds; a page that never matches its listing (no raise); a
    newer -001 beside an older document (5 accessions returned twice); a repeated accession across
    pages (twice); a page listed to the day before the window (its row on `filingTo` + 1
    missed); a blank `filingDate` on an unrequested recent row (a `ValueError`).
- **The listing check is measured, not assumed.** The 35 document/page pairs this machine's 24
  SEC caches hold from ONE run (the document fetched within an hour of the page): the row count
  equals `filingCount` on 35, the oldest row equals `filingFrom` on 35, and the newest row is at
  most `filingTo` + 1 day (+1 on 17, +0 on 2, earlier on 16); on all 26 of them that are a -001,
  the recent page's oldest row is `filingTo` + 2.
- **The reviewer's probes, on this head** (offline, their caches read only):
  - BMO, document and pages of 2026-08-06, `since=2025-08-05`: all **51** filings of that day
    returned (main and `2b02c9b0`: 0).
  - BMO, document of 2026-08-28 beside pages of 2026-08-06 (the 23-day hole of 319 filings on
    `2b02c9b0`, nothing raised), and BMO's document of 2026-07-13 beside its -001 of 2026-08-06
    (529 accessions returned twice): both now RAISE naming -001 ("2095 rows where it lists 2023";
    "… lists 2015") — offline the fresh read can only serve the same copies; live it fetches a
    consistent pair.
  - The blank-date case: 7 8-Ks returned, as main.
- **One live read through the shared limiter** (`EdgarClient.from_config()`, this worktree's
  cache; 2 requests, 2026-10-31 20:27 UTC): Wells Fargo (CIK 72971), Form 4, window from
  2023-11-02 — **308** filings, 2023-11-09 to 2026-10-05 (2023: 1, 2024: 118, 2025: 99, 2026: 90).
  The fresh pair is consistent with its listing: -001 holds 2,006 rows from 2020-05-29 (listed
  2,006 from 2020-05-29), its newest 2025-10-30 (listed to 2025-10-29), the recent page 1,305
  rows from 2025-10-31. On the documents of 2026-10-30, cache-only: the branch 308, main **98**.
- **The 16 cut filers, main against the branch, cache-only** (the primary's cache; an uncached
  URL raises, nothing fetched), the same 3-year window, Form 4 and all forms — re-run on this
  head, unchanged from `af70903c`:
  - main returns a short list for every one, saying nothing: e.g. JPM 132 Form 4s from
    2025-07-02, BAC 142 from 2025-07-07, BMO 8,255 filings from 2025-08-06;
  - the branch reads BMO whole (6 older pages; 20,129 filings, oldest 2023-10-31) and Deutsche
    Bank whole (1 page; 1,295, oldest 2023-10-31) — the two whose pages are cached, each pair
    consistent with its listing — and for the other 14, whose page -001 is not cached, RAISES
    naming it (live, it would be fetched through the limiter, as WFC's was).
  The 16: BAC, BLK, BMO, BNS, C, CM, DB, GS, JEF, JPM, MS, NMR, RY, STT, TD, WFC.
- **Every committed page** (26 that this session may open), main against the branch, cache-only,
  every form in a 3-year window — re-run on this head: identical. 24 recent pages reach back to
  2023-10-31 or before and ask for no older page; GOOGL's and V's documents are not in the cache,
  and both sides fail alike.

**BOUNDARY.**
- The primary checkout's `data/cache/sec`: 2,961 submissions documents (one per URL, fetched
  2026-06-30 to 2026-10-28), read 2026-10-30 and again 2026-11-01. 1,566 list older pages. "Cut" =
  the recent page's oldest filing date is after 2023-10-31, i.e. a window of 1,095 days
  (`_INSIDER_SCAN_DAYS`, `_DILUTION_SCAN_DAYS`, `_OWNERSHIP_SCAN_DAYS` — the longest any dossier
  caller asks) to 2026-10-30: 16 documents.
- The listing measurement: every cached older page in the 24 `data/cache/sec` directories under
  `/Users/work/Documents/GitHub` (checkouts and worktrees), paired with the same directory's copy
  of its document where the two were fetched within an hour: 35 pairs, read 2026-11-01.
- WFC: the live documents fetched 2026-10-30 (main against the branch) and 2026-10-31 20:27 UTC
  (the branch's live read).
- Main: `08948b5a`. Heads: `af70903c` (PR opened), `2b02c9b0` (round 1).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **More SEC requests for heavy filers** — one per older page a window overlaps (BMO's 3-year
  window: 6), each held a day like its document, and the document plus those pages once more when
  a cached page is of another vintage. None for any committed page today.
- **A window a page cannot serve is UNKNOWN where it read short and PRESENT before.** That is the
  point; the falsifier is a heavy filer's scan reading UNKNOWN while SEC serves a consistent page.
- **No committed page moves**: not one asks for an older page today, so nothing changes at its
  next assembly from this.
- **STATE §5.0 was at its 60-line cap**, so rows 5 and 6 were merged into row 5, verbatim, to make
  room for row 42 (the coordinator's direction, 2026-11-01): both are the between-print monitor
  (its panel registry; the four rulings of 2026-08-31), with the same owner, the operator.

**OPEN — NOT THIS PR.**
- **The monitor aborts on an unreadable older page** (`cli._cmd_monitor`, a 760-day window with no
  handler — not Session C's function). One heavy filer on the watch list whose page cannot be
  read stops the whole monitor day. Fix: record that name's window as unread and carry on, loudly.
  STATE §5.0 row 42 (1).
- **A 200 interstitial is cached as the page for its TTL** (review round 1, DEFERRED).
  `CachedHttp.get_text` writes any 200 body before `get_json` parses it, so an interstitial served
  for an older page reads "could not be read" (UNKNOWN, never a short count) until the cached copy
  expires — now ONE day, the document's TTL, since round 2 (it was 30). The fix is to validate a
  JSON body before caching it in `vinci/netcache.py`, which is not Session C's file. STATE §5.0
  row 42 (2).
- **`theme_intelligence.securities`** (Session A's file) reads the older pages itself, holds them
  30 days beside a document held 1 — the stale-vintage hole and double count above — never checks
  them against their listing, and stops silently at a page it cannot read. Not edited here.
- **The as-of callers without a window** read only the recent page: `mechanical`'s latest annual
  report at or before `reference_date` (the segment read, the Section 16 reach, the exhibit
  index), the 10-Q/8-K selections that filter on `reference_date`, `graph.filings`. For today's
  date the recent page holds the newest annual; for a historical re-assembly of a heavy filer it
  may not, and the answer is None. That is the as-of cut (C4), ruled 2026-11-01 and built next.
