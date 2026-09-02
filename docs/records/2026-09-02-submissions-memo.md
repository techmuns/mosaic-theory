---
id:
status: shipped
date: 2026-09-02
prs: [569]
supersedes:
superseded-by:
---

# The submissions document is read once per CIK per client — and a degraded feed's storm is paid once, for the names that survive to a second read

**WHAT.** `EdgarClient._submissions` now memoizes the PARSED submissions document on the instance,
keyed by padded CIK, bounded to `_SUBMISSIONS_MEMO_MAX = 2`, remembering FAILURE as well as success.
A remembered `HttpError` re-raises an equivalent error; it never returns `None` or `{}`. The document
is returned by reference, not copied. Nothing else changed: no URL constant was unified, no TTL was
touched, and no rendered value moves.

**WHY.** `CachedHttp` caches on disk only, so one dossier assembly's 13 reads of one CIK's
submissions document (12 via `recent_filings`, 1 via `registrant_history`, all threaded the same
`edgar` object by `assemble_mechanical`) each cost a disk read plus TWO json parses — the cache
envelope, then the payload. That parse cost is real but small and is NOT the reason for this change:
measured 0.72 ms per read on the corpus-median 152 KB document, so ~8.6 ms per dossier and ~4.3 s
over a 500-name batch. On its own it would not have been worth the risk.

The reason is the failure path. `netcache._write_cache` runs only on success, so a failed fetch is
never cached and every subsequent call site re-runs the full retry storm — 5 attempts with 1+2+4+8 s
backoff plus throttle, ≈15.6 s, or ≈165 s if SEC hangs to the 30 s timeout rather than erroring.

**The original brief claimed a flat ~10× on every name. That was wrong and the build brief was
amended before this was written.** Of the 13 call sites, 12 catch and continue; ONE does not —
`_drawdown_filings` (`vinci/dossier/mechanical.py:285`) — and `_drawdown_cause` runs it FIRST in
`assemble_mechanical`. Scoped precisely: of 20 EDGAR network calls in `mechanical.py`, exactly one is
unprotected. So the payoff splits by regime, and only one regime gets it.

**HOW VERIFIED.** Real runs against real cached submissions documents copied out of `data/cache/sec`
(only the envelope `fetched_at` was refreshed on the scratchpad copies so the 1-day TTL passes
offline; every payload byte is the live corpus).

*Gate 1 — same answers.* 12 form-sets plus `registrant_history` on three real documents, memoized
versus memo-cleared-every-call, IDENTICAL on all three: JPMORGAN CHASE & CO (4.42 MB, 4 former
names, 385 filings), Elanco Animal Health (1,852), Dynatrace (1,133).

*Gate 2 — one parse per CIK per run.* 13 reads of CIK 0000019617, counting real `json.loads` and
`CachedHttp._read_cache` calls:

    today (no memo) : 13 disk reads, 26 json parses
    with the memo   :  1 disk read,   2 json parses

*Gate 5 — degraded feed, both regimes*, with the real pacing config (`max_retries=4`,
`sec_requests_per_sec=8.0`), backoff counted rather than slept:

    Regime B (no gap-down events; the 12 protected sites run)
      12 reads, today : 187.4 s of backoff, 60 upstream attempts
      12 reads, memo  :  15.5 s of backoff,  5 upstream attempts     -> 12.1x
    Regime A (gap-down events; site 285 raises, nothing else runs)
       1 read,  today :  15.5 s of backoff,  5 upstream attempts
       1 read,  memo  :  15.5 s of backoff,  5 upstream attempts     -> no payoff

*Mutation-tested, per CORPUS BEFORE SYNTHETIC — the pins were shown able to fail before being
believed* (`tests/test_submissions_memo.py`, 15 pins; baseline 15 passed):

    M1 memo removed entirely        ->  7 failed
    M2 failure answers {} not raise ->  3 failed
    M3 bound removed                ->  1 failed
    M4 key collapsed to a constant  -> 11 failed
    M5 memo hit returns a copy      ->  1 failed
    M6 remembers every exception    ->  1 failed
    M7 failure answers None         ->  3 failed
    M8 (wrap mechanical.py:285)     ->  1 failed  (the accepted-risk pin)

**M5 caught a real defect in the pins themselves.** The first version of the reference pin asserted
that a sentinel write survived a second read — which a `copy.deepcopy` ALSO satisfies, because the
memo-MISS path returns the memoized object either way. It passed the mutation. The pin now asserts
IDENTITY (`first is second`). Without the mutation pass this file would have shipped a pin that
could not see the exact regression it existed to catch.

*Suite:* 3431 passed before, **3447 passed, 132 skipped, 37 deselected** after; `ruff check .` clean;
`mypy --strict vinci` clean (139 files). The +16 is 15 new pins plus one case from
`tests/test_record_hygiene.py`, which parametrizes over `docs/records/` and so grew by exactly this
file (343 → 344).

**WHAT IT COSTS / WHAT IS ACCEPTED.**

*Accepted — the unprotected first call site.* `mechanical.py:285` stays unwrapped, by decision
(operator, 2026-09-02). On a degraded feed a name carrying `earnings_gap_down` events — 9 of 17
committed dossiers: AORT, BRBR, CNXC, EPAM, FUBO, MVST, SMPL, VITL, VRRM — raises out of
`assemble_mechanical`, is caught by `assemble_cohort`'s per-name `task` handler, and is DROPPED into
the returned `errors` list rather than rendering with a blank drawdown block. The run does not crash;
the name silently does not appear. **This memo therefore cannot help the majority regime, and the PR
claims no payoff there.** Fixing it would change what a degraded-feed dossier SAYS for that class of
names, which is out of this change's scope. Recorded as STATE.md §5.0 row 16 and machine-pinned by
`test_the_first_submissions_call_site_is_still_unprotected_which_bounds_this_memo`, whose FALSIFIER
is someone wrapping that call site — the pin then reddens and instructs them to strike the row.

*Accepted — return by reference.* The memoized dict is shared with callers, so a future consumer that
mutates it would poison every later read within the run. Copying is not the alternative: `deepcopy`
measures 1.86 ms against 0.42 ms for a fresh parse, so it would cost 4.4× the work it saves and make
the change a net pessimization. Verified read-only today (`parse_registrant_history`,
`parse_former_names`, `recent_filings`) and pinned by
`test_the_memoized_document_is_not_mutated_by_its_consumers`.

*Accepted — the bound is 2, not unbounded.* One assembly touches one CIK, but `vinci/cli.py:1839`'s
monitor loop and the theme scans hold one client across MANY CIKs and read each exactly once, where
an unbounded memo is pure cost: a parsed submissions dict is 3.6–3.9× its text (0.53 MB at the corpus
median, 16.97 MB at the 4.42 MB max), so a 2,000-name sweep would retain ~1.0 GB for no reuse.

*Not covered, stated so it is not later mistaken for a claim:* `resolver.submissions()` and
`vinci/themes/assay.py` read the same endpoint through their own `CachedHttp` instances and are
untouched, as is the `EdgarClient` built at `assemble.py:366` (outside `assemble_one`).

**FOUND WHILE VERIFYING, NOT FIXED** (reported per CLAUDE.md's hold-scope rule):

- `CachedHttp.close()` and `__exit__` exist (`netcache.py:115–122`) but no production caller uses
  them, and `EdgarClient.from_config()` builds two `httpx.Client`s per call across ~20 construction
  sites — a pre-existing fd/socket leak.
- `netcache.py:41` asserts "Thread-safety is not required — the orchestrator is single-threaded by
  design". `assemble_cohort` runs `ThreadPoolExecutor(max_workers=8)`. The claim is stale for that
  path (benign today: the shared resolver's index is preloaded and `resolve_ticker` defaults to
  `enrich=False`, so no concurrent HTTP occurs on it).
- `recent_filings`' filler allocation (`vinci/edgar/client.py:440, 441, 449`) builds `[""] * n` /
  `[None] * n` inside the per-filing loop. It is O(kept × n), not O(n²) — both `continue` guards
  precede it — so size any claim off the kept count, not the ~1,000-filing cap.

## Amendments

**2026-09-02 — the accepted risk above is RESOLVED, same day, by #570.** `mechanical.py`'s drawdown
path now catches `HttpError` and degrades to UNKNOWN instead of raising out of `assemble_mechanical`,
so a degraded feed no longer drops the name. Consequences for the claims in this record:

- **The scope limit no longer holds.** The measured 187.4 s → 15.5 s applies to EVERY name, not only
  the no-gap subset. The "no payoff" row of the regime table above is now historical.
- **STATE.md §5.0 row 12 is struck**, the item being closed.
- **The pin named above did NOT fire when the fix landed, and has been replaced.**
  `test_the_first_submissions_call_site_is_still_unprotected_which_bounds_this_memo` asserted the
  absence of a `try` INSIDE `_drawdown_filings`, but the correct fix wraps the call one frame up in
  `_drawdown_cause` — so the pin stayed green and would have let row 12 rot silently. It pinned a
  SHAPE (where the `try` sits) rather than the PROPERTY (whether an `HttpError` can escape). Its
  replacement, `test_the_degraded_feed_payoff_is_no_longer_bounded_by_an_unprotected_call_site`,
  asserts the property and was mutation-tested against a revert of the fix.

The body above is left as written, per the amendment contract: the wrong version staying visible is
the point. Record for the fix: `docs/records/2026-09-02-drawdown-filing-index-unavailable.md`.
