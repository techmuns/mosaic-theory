---
id: 2026-10-29-sec-one-budget-per-machine
status: shipped
date: 2026-10-29
prs: [854]
supersedes:
superseded-by:
---

# Every SEC request on the machine takes its turn from one budget of 8 a second; a refusal silences them all for SEC's window, then fails loud; only a 404 reads as absent; the User-Agent is checked (audit items E1-D1, E1-D8, E1-D9, E1-D15)

**WHAT.**
- **One budget (E1-D1).** `vinci/netcache.py` `SharedPace`, reached through `sec_pace()`. Every
  `CachedHttp` request to `www.sec.gov`, `data.sec.gov` or `efts.sec.gov` takes a slot from it,
  whoever built the client and whatever interval it was given. That covers theme intelligence's
  own 0.15 s client and the quality pass's unpaced one, without touching their files. The total is
  `SEC_MAX_REQUESTS_PER_SEC = 8.0`, across every client, thread and `vinci` process on the
  machine. Each client's own interval still applies on top, and is now taken under a lock.
- **A refusal is a clock for the whole machine.** A 429 or a 403 from an SEC host holds off every
  SEC request: for `Retry-After` when SEC sends one, else 660 s. The request then retries once. A
  second refusal raises `SecRateLimitedError`, deliberately not an `HttpError`. So does a
  `Retry-After` above 900 s, at once. Other hosts keep their 429 path; they now also read a
  `Retry-After` when one is sent.
- **A refusal stops the run, not one name (PR review, round 1).**
  - Once `SecRateLimitedError` is raised, no further SEC request leaves the process
    (`netcache.sec_refusal()`). A later read, from any client, raises at once without sending; a
    cached copy is still served.
  - `assemble_cohort` skips names not yet started and raises once the running ones finish. The
    theme exposure scan cancels and raises. The dossier anchor's broad handler re-raises.
  - The one write path (`assemble._write`) refuses to write any page once SEC has refused the
    process, because a page built across the refusal can carry blanks where a swallowed SEC read
    belonged.
  - For a 403, the error names both possible causes: a fair-access block, or a User-Agent SEC does
    not accept.
- **Only a 404 is absence (E1-D8, E1-D9).** A 404 raises `HttpNotFoundError`, a subclass of
  `HttpError`. `EdgarClient.fundamental_snapshot_and_facts` maps only that to "no XBRL"; any other
  failure raises with its status. The screen (`screens/assemble.enrich_with_fundamentals`) reads
  companyfacts once, through that method. The share-count frame merge skips a period on a 404
  only; anything else raises.
- **The User-Agent is checked (E1-D15).** `config.sec_user_agent()` refuses the `.env.example`
  placeholder and any value with no email address. The error names the variable, never the value.

**WHY.**
- **The ceiling is a total.** SEC's published policy allows 10 requests a second per user, across
  all machines. Above it, the IP may be limited until the rate has stayed below the threshold for
  ten minutes. No HTTP status is documented for this.
- **The old pace was per client, and unlocked.** Each `CachedHttp` kept its own "last request at",
  and the class said thread-safety was not required. But the dossier assembly runs 8 workers, each
  building its own clients; the theme exposure scan drives one client from a thread pool; and
  theme intelligence builds its own SEC client. So the code's 8-a-second setting held only for one
  client on one thread (measured below).
- **The old refusal path made a block worse.**
  - A 403 raised on the first attempt, and every other thread kept sending.
  - A 429 waited 61 s at most four times, about four minutes inside a ten-minute block, and each
    retry restarted SEC's clock.
  - A caller's `except HttpError` then went on to the next name and sent again.
- **Absence was read from failure.**
  - The snapshot's broad `except` made a 503 that outlived its retries into "no XBRL".
  - The screen's second companyfacts read could disagree with the snapshot's. On a transient
    failure it read the data the snapshot had called absent. On a true 404 it raised, so a filer
    with no XBRL stopped `enrich_with_fundamentals` instead of reading UNKNOWN.
  - The frame merge's broad `except` skipped a failing newest period and served the period before
    it, under the same tag, with nothing to say it was a quarter older.

**DESIGN — why this shape, kept simple.**
- **A bucket one token deep.** With depth b, b + 8 requests fit in one second. Depth 1 is the only
  depth that holds the cap in every sliding second.
- **Take-at-wake, not reserve-ahead.** A caller sleeps until the slot looks free, then takes it
  under the locks, or sleeps again if another caller got there first. A reserve-ahead design lets
  64 threads hold slots seconds into the future, and they would fire into a block that started
  after they reserved. Here a hold-off binds at once.
- **The state is two numbers in one file under `flock`:** when the next request may go, and the
  end of any hold-off. A thread lock wraps the `flock`, because `flock` excludes open files, not
  threads sharing one. The file is reopened after a fork for the same reason.
- **Wall-clock seconds, because two processes agree on them.** A value further ahead than the
  longest hold (900 s plus one interval) can only be a clock that stepped back, so it is
  discarded, not obeyed as a stall.
- **The file is per user, not per checkout.** The default is `~/.cache/vinci/sec-pace`
  (`$XDG_CACHE_HOME`, overridable with `VINCI_SEC_PACE_FILE`). The brief suggested the cache
  directory, but sessions run from separate worktrees, each with its own `data/cache`, and they
  all share one IP. A file under the cache directory would not have coordinated them. If the file
  cannot be opened, the request raises and names the variable.
- **Any SEC 403 counts as a refusal.** SEC documents no status. This repo's own assembly code
  already names a "SEC fair-access 403". And no read path here expects a 403 from SEC for any
  other reason; a missing User-Agent is now refused before sending.
- **660 s:** SEC's ten minutes plus one, the same one-unit margin as the existing 61 s for a
  60-second window.
- **`SecRateLimitedError` is outside `HttpError`.** Several callers degrade an `HttpError` to
  UNKNOWN and move to the next name. During a block that sends again into it, and it records a
  refusal as missing data.
- **Why stop the whole process, and not only the three named handlers.** `vinci/` holds 75 broad
  `except Exception` handlers. Re-raising in each is an audit, not a fix, and the next handler
  added would reopen it. A per-process stop makes any swallowed refusal harmless to SEC: nothing
  more is sent. The one write path then refuses whatever page was built across it. The cohort,
  the exposure scan and the anchor re-raise so the run says so at once, rather than going through
  every remaining name.
- **The suite gets a budget of its own** (`tests/conftest.py`, autouse, per test). Offline tests
  drive real clients over mock transports; a slot one took from the user's file is a slot a live
  run waits for. A test marked `network` keeps the machine's budget, because it sends real
  requests. The fixture is per test, not per session, because it reads each test's marker. It also
  clears the per-process stop between tests.

**HOW VERIFIED.**
- **New pins:** `tests/test_sec_pacing.py` (6) and `tests/test_sec_refusals.py` (26). All run on
  a virtual clock over a mock transport, except the two-process test, which uses a real clock,
  real processes and a mock transport. Nothing reaches SEC.
- **Failing first, on main's `netcache.py` (0fa8ce4a):** 5 of the 6 pacing pins fail. The
  exception is the non-SEC pin, which is meant to pass on both.
  - 8 clients × 8 threads: peak 191 in one second.
  - 1 shared client × 8 threads: 48.
  - 4 unpaced clients: 32.
  - A non-SEC client at 0.25 s shared by 8 threads: two sends 0.0 s apart.
  - Two processes: closest sends 0.00006 s apart.
  - The refusal file fails at import on main, because its names did not exist.
- **Mutations, each put back one at a time** (`tests/test_sec_refusals.py` +
  `tests/test_sec_pacing.py`, 32 tests). All 8 were caught:
  - D8's broad `except` back in the snapshot: 3 pins fail.
  - The screen's second companyfacts read back: 1 (the 404 pin).
  - D9's broad `except` back in the frame merge: 2.
  - The User-Agent check removed: 7.
  - The refusal path reverted to the old 403/429 handling: 7.
  - The hold-off made a no-op: 5.
  - The per-instance interval unlocked (read, sleep, then write): 1.
  - The shared budget skipped: 8.
- **A real paced EDGAR read**, through `EdgarClient.from_config`, the default pace file and the
  operator's declared User-Agent (validated, not printed):
  - companyfacts for CIK 0000320193 (one request; 505 tags; FCF and operating-income signs +1);
  - the same read again, served from cache with no request;
  - its submissions (one request; 11 recent 10-Ks), 1.054 s after the first.
  - Two requests to SEC in all.
- **Absence is a 404 at SEC, checked rather than assumed.** This change reads only a 404 as
  absent, and treats a 403 as a refusal that holds every SEC request off for 11 minutes. So it
  matters that SEC does not answer a routine absence with 403. Two more normal requests, paced
  through the shared budget, both answered `404` with an S3 `NoSuchKey` body:
  - a not-yet-published frame (`dei/EntityCommonStockSharesOutstanding/shares/CY2030Q1I`);
  - companyfacts for a CIK that does not exist (`CIK0000000001`).
  The period-average test's frame stub, which modelled absence with a plain `RuntimeError`, now
  raises the real type.
- **Test doubles.** Five screen doubles in four test files modelled the old two-read interface.
  Each now serves the same snapshot and facts through `fundamental_snapshot_and_facts`. The
  sector-rule consumer scan counts both snapshot entry points, so the screen did not drop out of
  it.
- **Round 1 (the coordinator's `/code-review high`, standing in for Codex at its usage limit).**
  Seven new pins: six fail on the PR head before round 1 (dbbcf025), and the seventh, marked
  `network`, passes and runs only with `-m network`:
  - after a refusal, a second client's SEC request raises and sends nothing;
  - a 403's error names `SEC_USER_AGENT`, and a 429's does not;
  - a refused cohort raises after trying 1 of 4 names, where the head tried all 4 and returned
    errors;
  - a refused exposure scan raises, where the head graded every name UNASSESSED;
  - `_write` refuses a page while SEC has refused the process, and writes it once it has not;
  - an offline test's budget is the suite's own, where the head used `~/.cache/vinci/sec-pace`;
  - a `network` test keeps the machine's budget.
- **The suite never touches the real budget, and its pacing costs nothing measurable.** A scratch
  pytest plugin logged every SEC slot taken in a full offline run.
  - On the PR head (dbbcf025): 19 tests took 315 slots. One slot came from the user's real file:
    `test_sec_reference_fixture.py::test_an_unseeded_cache_fails_loud_instead_of_fetching`. Its
    13:12:15 write was found in the file during the PR's own suite run.
  - After round 1: 23 tests took 323 slots, none from the user's file. The same test's one slot
    came from the suite's own file, with 0.0 s spent waiting. The other 322 came from files the
    SEC tests make for themselves, mostly on virtual clocks.
  - Wall time, full offline suite on this machine: 301 s on the PR head; 290 s and 353 s on
    two runs after round 1. The same code ranged from 295 to 457 s here while other sessions
    ran, so the spread is load. Pacing did not slow the suite: waiting on the suite's own
    budget totalled 0.0 s.
- **The gate:** ruff (`vinci tests frontend`) and `mypy --strict vinci` clean. The full
  `pytest -m "not network"` result is in the PR body.

**MEASURED PEAK, BEFORE AND AFTER (real clock).** Script: a mock transport recording each send's
`time.time()`, clients from the real `build_sec_http`. Peak = the most sends in any half-open
one-second window.

| shape | requests | main 0fa8ce4a | this branch |
|---|--:|---|---|
| 1 client × 1 thread | 24 | peak 8 (3.06 s) | peak 8 (3.04 s) |
| 8 clients × 8 threads | 192 | all 192 within 0.41 s | peak 8 (25.06 s) |
| 1 shared client × 8 threads | 48 | all 48 within 0.81 s | peak 8 (6.27 s) |

**BOUNDARY.**
- **Peaks:** measured 2026-10-29 on this machine, on the counts in the table (3 or 6 requests per
  thread), over a mock transport. They show what the code permits, not a production rate. "Before"
  is capped by the request count: all 192 landed inside one second.
- **Virtual-clock figures:** the test assertions (191, 48, 32) count sends in virtual seconds.
- **Mutation counts:** over the 32 tests of the two new files.
- **Real requests:** four to `data.sec.gov` in all, on 2026-10-29: the two-request read (from a
  fresh `data/cache` in this worktree) and the two 404 checks.
- **Broad handlers:** 75 `except Exception` handlers in `vinci/` at this branch. 12 of the modules
  holding them also read SEC. They were not audited (see below).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Parallel SEC reads are slower.** Eight assembly workers now share 8 a second where they had 8
  each. That is the point: the old speed came from exceeding SEC's ceiling.
- **A genuinely permanent SEC 403 costs 11 minutes** before it fails loud, where it used to fail
  at once. *Falsifier:* a `SecRateLimitedError` on one URL while other SEC reads in the same run
  succeed. That would be a per-resource 403, which needs its own status path.
- **The budget is per machine, not per IP.** Two machines behind one address (or a browser
  reading EDGAR on this one) are outside it. The 2-a-second margin under SEC's 10 is the only
  allowance for them. *Falsifier:* a refusal while no `vinci` process exceeds 8 a second.
- **Broad handlers can still swallow `SecRateLimitedError`, harmlessly to SEC.** Within the name
  being built, a handler that catches `Exception` turns the refusal into an UNKNOWN. Nothing more
  is sent, and that page is not written. A batch other than the cohort and the exposure scan that
  catches it per item runs on with each item failing at once. Those 75 handlers were not audited.
- **The CI secret: settled.** The operator confirmed, through the coordinating session on
  2026-10-29, that the `SEC_USER_AGENT` repository secret carries an email. The STATE row opened
  for it in this PR was closed before merge. `.github/scripts/validate_keys.py` still sends the
  secret without this check.

**NOT DONE HERE (outside this batch's files), for follow-up:**
- `vinci/dossier/mechanical.py` still reads the snapshot and then companyfacts a second time; it
  could use `fundamental_snapshot_and_facts`.
- Theme intelligence derives its contact from the User-Agent's last word
  (`theme_intelligence/config.py`).
- efts' own 1-a-second pace is per client: eight efts clients may send up to 8 a second between
  them, which is still inside the shared total.
- The audit of the broad handlers above.
- **A frame that fails past its retries now stops every caller (review round 1, DEFERRED).**
  `shares_outstanding_with_provenance` raises on any non-404 failure. Its callers
  (`universe.py:209`, the universe builder; `themes/leaders.py:96`; `themes/assay.py:790`) used
  to receive an older period's value silently and now stop. That is the intended direction (fail
  loud). Returning the failed periods to each caller would change a return type across three files
  outside this batch.
- **Redirect hops are not paced.** The SEC check reads the URL a client is asked for; a hop
  `httpx` follows on a redirect takes no slot of its own. The read paths here request final URLs.
  Pacing every hop needs an `httpx` request hook. (Code review, round 0.)
- **One transient failure now stops the whole screen.** The weekly screen
  (`vinci/screens/run.py`) has no per-name handler, so a companyfacts read that fails past its
  retries now stops the run instead of recording "no XBRL". That is loud, as intended. A per-name
  UNKNOWN that carries the real reason belongs in that file. (Code review, round 0.)
- **The User-Agent check runs at import.** `theme_intelligence/config.py` calls `sec_user_agent()`
  at import, so an invalid value stops every theme-intelligence command, including the
  Tiingo-only steps. (Code review, round 0.)
