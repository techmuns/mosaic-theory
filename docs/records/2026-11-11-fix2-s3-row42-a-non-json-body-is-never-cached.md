---
status: shipped
date: 2026-11-11
prs: [1016]
supersedes:
superseded-by:
---

# STATE row 42 (2): a 200 body that is not JSON is never cached as JSON — an interstitial no longer blocks a filer's filings window for a day; row 42 (1), the monitor, waits for coordinator A's monitor and CLI PRs

**WHAT.** `CachedHttp.get_json` (`vinci/netcache.py`) now parses a body before it caches it.
- Before, `get_text` wrote any 200 body to the cache and `get_json` parsed it afterwards. So an
  interstitial served once for a submissions document or an older submissions page stayed the
  cached copy for its whole TTL: one day for both since #878 (`EdgarClient._ONE_DAY`). Every
  windowed read of that filer, in every process on the machine, read "could not be read" (an
  UNKNOWN) until it expired, though SEC was serving the page again.
- Now a non-JSON body raises the same `ValueError` it always did, with nothing written. A non-JSON
  copy already on disk, written by the old code, is a miss and is fetched again.
- `get_text`, used for documents read as text (filings' HTML), still caches any 200 body.

This is row 42's edge (2), owned by `vinci/netcache.py`'s owner. Stream S3 took it on 2026-11-11
(issue #1004).

**Row 42 (1), the monitor aborting its whole day on one unreadable older page, is not in this
PR.** Its fix is in `cli._cmd_monitor`. `vinci/cli.py` is in flight in coordinator A's #1006, and
A has a monitor void-keying PR open on the monitor's files. The S3 rule is to wait rather than
edit a file A has in flight. Row 42 now names that blocker.

**WHY.** #878's record deferred this edge (review round 1): "The fix is to validate a JSON body
before caching it in `vinci/netcache.py`."

**HOW VERIFIED.** `tests/test_netcache_json_body.py`, 8 tests. They run on Gartner's (IT)
committed submissions document and older page -001 (`tests/fixtures/submissions_pages/`, #878's
fixtures), served by a mock transport behind a real `CachedHttp` and a real `EdgarClient`. That is
the path the monitor and every windowed caller read through.
- **Fail first, on main's `vinci/netcache.py`:** the two positive pins fail, and the two negative
  pins pass. All 8 pass on this branch.
  - An interstitial, then the real page: on main the second client was served the cached
    interstitial from disk with no request, and raised again. Now the second read reaches SEC and
    returns the page's 8-Ks since 2021-06-01.
  - A non-JSON copy already on disk is refetched once, and the JSON is cached in its place.
  - (−) A JSON page is cached and read back with no second request.
  - (−) `get_text` still caches any 200 body.
  - Review round 0 (`/code-review high --fix`): `get_text` and `get_json` now share one read
    path (`_get`), and a refused cached copy's fetch time is forgotten, so `fetched_at` never
    states a read that failed. Pinned by `test_a_rejected_copy_whose_refetch_fails_states_no_fetch_time`,
    red on `fa40c5d0`.
  - PR round 1 (the in-session `/code-review high`, Codex's review having failed on its usage
    limit): the refused copy is now removed from disk as well, because `fetched_at` falls back
    to the disk entry and still stated the refused copy's time. Pinned by the same test, now
    asserting `fetched_at(url) is None`, red on `cc7a7fff`.
  - PR round 2 (the coordinator's independent review, at `2a39c9c4`) REVERSED round 1's disk
    removal and pinned the headline change:
    - **The headline change was unpinned.** A write moved above the parse survived all 5 tests,
      because the next read refused the written copy and refetched. It is now pinned on the disk
      itself by `test_a_refused_body_is_never_written_fresh_or_over_an_expired_copy`: a refused
      first fetch leaves no entry, and an expired valid copy survives a refused refetch byte for
      byte. That mutant now fails it.
    - **Round 1's unlink deleted the refused copy from caches that are only read.** These are
      the cache-only scripts and the impact check's frozen cache shared by both sides, so a
      second reader met a miss. A refused copy is now a miss in memory only, recorded in
      `_refused` so `fetched_at` states no time for it. Its file stays, and the next good write
      replaces it. Pinned by `test_a_cache_only_reader_never_deletes_the_copy_it_refuses`, red
      on `2a39c9c4`, and by `test_a_good_write_after_a_refusal_states_its_own_fetch_time` (the
      negative). Dropping the marker fails 2 tests.
- **The callers' suites pass**, `-m "not network"`: netcache, older pages, EDGAR, SEC pacing,
  budget and refusals, and amended filings.

**BOUNDARY.**
- "One day": the `ttl_seconds` `EdgarClient` passes for the submissions document and each older
  page (`_ONE_DAY`, 86,400 s).
- The interstitial body in the test is constructed: an HTML page where JSON was asked for. No real
  200 interstitial body is committed in this repo, and #878's own pin raises a `ValueError` in its
  place.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **An interstitial now costs one request per read until SEC serves the page.** Before, it cost
  none, and the read failed for a day. SEC's pacing and refusal rules (#854, #939) apply to every
  retry. A 403 or 429 refusal is unchanged: it never reaches the body check.
- **The monitor still aborts on an unreadable older page** until row 42 (1) lands.
- **DEFERRED (PR round 1): `post_json` still caches a 200 body before it parses it.** That is the
  same class on FINRA's short-interest query path (`finra.py`), outside row 42's submissions reads.
  The fix would route `post_json` through the same body check.
- **DEFERRED (PR round 2): the submissions failure memo does not remember a non-JSON body.**
  `EdgarClient._submissions` and `_older_page` remember only `HttpError`, and a non-JSON body
  raises `ValueError`. So one client serving five reads of a filer whose page is an
  interstitial sends 5 requests where main sent 1 (main's disk copy acted as the memo, for the
  day the page was wrong).
  - The memo exists to stop a retry STORM: about 15.6 s of retries per read on a degraded feed.
    A non-JSON 200 is one paced request with no retry.
  - Remembering it would also keep an assembly reading the failure after SEC recovered.
  - This is `vinci/edgar/client.py`, outside this PR. The cost stands at one request per read.
- **DEFERRED (PR round 2): `fetched_at`, before any read, still counts a non-JSON copy as held.**
  It reads the disk entry without parsing it, and it serves `get_text`'s copies too.
  `theme_intelligence/market.py` gates its Tiingo budget on it, so such a copy makes one request
  that is not counted against the budget, where main raised with none. Fixing it means parsing in
  `fetched_at`, which is the text path's API as well.
- **OPEN, not caused by this PR** (review, 2026-11-11):
  - `json.loads(get_text(...))` callers still cache an interstitial:
    `scripts/audit_verbatim_corpus.py:130` and `vinci/quality/sources/release.py:563`;
  - `_write_cache` is a plain, non-atomic `write_text`.
