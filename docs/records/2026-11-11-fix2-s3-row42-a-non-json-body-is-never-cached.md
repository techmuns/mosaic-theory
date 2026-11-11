---
status: shipped
date: 2026-11-11
prs: []
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

**HOW VERIFIED.** `tests/test_netcache_json_body.py`, 5 tests. They run on Gartner's (IT)
committed submissions document and older page -001 (`tests/fixtures/submissions_pages/`, #878's
fixtures), served by a mock transport behind a real `CachedHttp` and a real `EdgarClient`. That is
the path the monitor and every windowed caller read through.
- **Fail first, on main's `vinci/netcache.py`:** the two positive pins fail, and the two negative
  pins pass. All 4 pass on this branch.
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
