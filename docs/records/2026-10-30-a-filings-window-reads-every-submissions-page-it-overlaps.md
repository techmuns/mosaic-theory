---
id: 2026-10-30-submissions-pages
status: open
date: 2026-10-30
prs: []
supersedes:
superseded-by:
---

# A filings window that reaches past the submissions index's recent page reads every older page it overlaps, or raises naming the one it could not read

**WHAT.** Phase 2, Session C, batch C3 (audit E1-D10).
- `EdgarClient.recent_filings(cik, forms=…, since=…)` read only the submissions document's
  `filings.recent` block — a filer's newest ~1,000 filings — and ignored the older pages the
  document lists under `filings.files`. A window that began before the recent page's first row
  ended there, silently: a short list read as "no filings before".
- Now, when `since` falls before the recent page's oldest filing, every older page whose
  `filingTo` reaches `since` is read too (`_older_rows`), through the same SEC client — the
  shared limiter, held 30 days in the cache as `theme_intelligence.securities` holds a closed
  page — and parsed by the one row reader both kinds of page share (`_page_filings`). Pages
  wholly before the window are not fetched. A page the window needs and cannot read RAISES
  `HttpError`, naming the page — unreachable, answered with something that is not JSON (an
  interstitial), missing its arrays, listed with no name, or listed with a span date that is not
  ISO, all alike (`_older_filings`; in-session review rounds 0 and 1: a `ValueError` or `KeyError`
  would have escaped the callers that catch only `HttpError` and aborted the assembly); every windowed caller already turns an `HttpError` into its
  UNKNOWN (the ownership register, insider and Section 16 scans, the dilution scan, the rank's
  8-K scan, the theme prefilter, the gap and maturity 8-Ks).
- A page that FAILED is remembered by the client, as the document's failure is (`_submissions`'
  memo, under the page's name; `_older_page`): an assembly makes several windowed reads of one
  filer, and without it a degraded feed would re-run the retry storm (≈15.6 s) at each. A page
  read is not remembered — the disk holds it.
- Without `since`, only the recent page is read, as before — those callers ask for the newest
  filing of a form, which the recent page holds by construction.
- `mechanical._ownership_events`' docstring stated the old limit as a known risk; it now states
  the window is read whole.
- This closes the UNLOCK named in `docs/records/2026-08-12-open-observations-surfaced-by-pr-2-s-corpus-swee.md`
  ("read the `filings.files` overflow pages, then pin truncation on a frozen fixture"), where
  NFLX's index had ~2 months of headroom on the 3-year ownership window.

**WHY.** A heavy filer's recent page covers months, not years. On today's live document Wells
Fargo's recent page starts 2025-12-09: main read **98** Form 4s in a 3-year window where the filer
made **308** — two thirds of the window missing and nothing said. The insider, ownership and
dilution scans read exactly such windows, and an empty or thin result there is PRESENT ("none in
window"), never UNKNOWN.

**HOW VERIFIED.**
- **Failing first.** `tests/test_submissions_older_pages.py` (9) on main `08948b5a`: the
  older-page read and the unreadable-page raise FAILED on main's behaviour (page -001's 8-Ks
  missing; no raise); the two negative pins (a window inside the recent page, and no window, fetch
  nothing more) passed on main and pass now. The fifth — a failed page fetched once by one client
  across two windowed reads — failed on this branch's first cut (fetched twice) before the memo;
  the three malformed-page cases (interstitial, no `form` array, unnamed page) failed on the
  reviewed head (a `ValueError`, a `KeyError`, a fetch of `/None`) before `_older_filings`; the
  non-ISO `filingTo` case failed on the PR head (`af70903c`, a `ValueError`) before review round 1. Fixtures are Gartner's real submissions document and
  its real older page -001, each cut to a slice of its rows (`tests/fixtures/submissions_pages`);
  HTTP is mocked.
- **One live read through the shared limiter** (`EdgarClient.from_config()`, this worktree's
  cache; 2 requests): Wells Fargo (CIK 72971), Form 4, window from 2023-10-31 — the document and
  its page -001 read; **308** filings, 2023-11-09 to 2026-10-05 (2023: 1, 2024: 118, 2025: 99,
  2026: 90). Main on the same two cached documents: **98**, oldest 2025-12-09.
- **The 16 cut filers, main against the branch, cache-only** (the primary's cache; an uncached
  URL raises, nothing fetched), the same 3-year window, Form 4 and all forms:
  - main returns a short list for every one, saying nothing: e.g. JPM 132 Form 4s from
    2025-07-02, BAC 142 from 2025-07-07, BMO 8,255 filings from 2025-08-06;
  - the branch reads BMO whole (6 older pages; 20,129 filings, oldest 2023-10-31) and Deutsche
    Bank whole (1 page; 1,295, oldest 2023-10-31) — the two whose pages are cached — and for the
    other 14, whose page -001 is not cached, RAISES naming it (live, it would be fetched through
    the limiter, as WFC's was).
  The 16: BAC, BLK, BMO, BNS, C, CM, DB, GS, JEF, JPM, MS, NMR, RY, STT, TD, WFC.
- **Every committed page** (26 that this session may open), main against the branch, cache-only,
  every form in a 3-year window: identical. 24 recent pages reach back to 2023-10-31 or before
  and ask for no older page; GOOGL's and V's documents are not in the cache, and both sides fail
  alike.

**BOUNDARY.**
- The primary checkout's `data/cache/sec`: 2,961 submissions documents (one per URL, fetched
  2026-06-30 to 2026-10-28), read 2026-10-30. 1,566 list older pages. "Cut" = the recent page's
  oldest filing date is after 2023-10-31, i.e. a window of 1,095 days (`_INSIDER_SCAN_DAYS`,
  `_DILUTION_SCAN_DAYS`, `_OWNERSHIP_SCAN_DAYS` — the longest any dossier caller asks) to
  2026-10-30: 16 documents.
- WFC: the live documents fetched 2026-10-30, read through the branch and, cache-only, main.
- Main: `08948b5a`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **More SEC requests for heavy filers** — one per older page a window overlaps (BMO's 3-year
  window: 6), each held 30 days. None for any committed page today.
- **A window a page cannot serve is UNKNOWN where it read short and PRESENT before.** That is the
  point; the falsifier is a heavy filer's scan reading UNKNOWN while SEC serves the page.
- **No committed page moves**: not one asks for an older page today, so nothing changes at its
  next assembly from this.

**OPEN — NOT THIS PR.**
- **The as-of callers without a window** read only the recent page: `mechanical`'s latest annual
  report at or before `reference_date` (the segment read, the Section 16 reach, the exhibit
  index), the 10-Q/8-K selections that filter on `reference_date`, `graph.filings`. For today's
  date the recent page holds the newest annual; for a historical re-assembly of a heavy filer it
  may not, and the answer is None. That is the as-of cut (C4), which waits on its ruling.
- **`theme_intelligence.securities._walk_filings`** reads the older pages itself and stops
  silently at one it cannot read — not Session C's file.
- **A 200 interstitial is cached as the page for its TTL** (review round 1, DEFERRED).
  `CachedHttp.get_text` writes any 200 body before `get_json` parses it, so an interstitial served
  for an older page reads "could not be read" (UNKNOWN, never a short count) for the page's
  30 days rather than the document's 1. The fix is to validate a JSON body before caching it in
  `vinci/netcache.py`, which is not Session C's file; `theme_intelligence.securities` holds its
  pages 30 days the same way.
