---
id: 2026-10-23-maintenance-pins-offline
status: open
date: 2026-10-23
prs: []
supersedes:
superseded-by:
---

# The maintenance pins run offline: SEC's ticker files and companyfacts come from committed fixtures, and the network is refused while they run

**WHAT.** The 21 pins in `tests/test_maintenance_path.py` and `tests/test_maintenance_identity.py`
no longer read the git-ignored `data/cache`. Each test's temporary Config gets a cache seeded by
`tests/sec_offline_support.py` from committed fixtures:

- `tests/fixtures/sec_reference/`: the fleet's slice of `company_tickers.json` and
  `company_tickers_exchange.json`, 30 rows each. The builder is
  `scripts/build_sec_reference_fixture.py`.
- `tests/fixtures/companyfacts/`: the existing subsets, unchanged.

Entries are written through `vinci.sec.build_sec_http`, which owns the cache layout, and stamped as
fetched now, so the resolver's one-day TTL never expires them mid-run. An autouse `no_network`
fixture refuses outbound connections in both files. A fixture gap therefore fails with the fix in
its message, instead of fetching.

**WHY.** On a fresh checkout, `data/cache` is absent, so the resolver fetched
`https://www.sec.gov/files/company_tickers.json` live inside `pytest -m "not network"`. The one-day
TTL made a laptop re-fetch it daily as well. Codex's cloud onboarding reported the failures, and
they were reproduced before any code changed. On a fresh checkout of `ca17bc05`, with outbound
traffic refused by a dead proxy:

- **8 failed, 13 passed, 1 skipped, in 427 s.**
- Every failure read `Exhausted retries for https://www.sec.gov/files/company_tickers.json`.

CI passed only because GitHub's runners reach sec.gov. An SEC outage or rate limit would turn
`gate` red for no code reason.

This is the class behind the eleven red merges of August, where the git-ignored store was empty on
a fresh checkout. It is the third dependency of that kind, after prices (`build_price_fixture.py`)
and companyfacts (D17), and it gets the same remedy: commit the slice the pins read.

**HOW VERIFIED.**

- **What the pins read, measured not guessed.** An instrumented run of the two files on a fresh
  checkout recorded every URL the SEC client served and every ticker the resolver looked up. That
  came to 23 URLs: the two ticker files plus companyfacts for 21 CIKs. The committed companyfacts
  fixture holds all 21. It came to 21 tickers, all fleet names.
- **The fix, under the condition that failed.** Same fresh checkout, same dead proxy, with the fix:
  **21 passed, 1 skipped, in 14.5 s**, and no `data/cache` written.
- **The WHOLE offline suite, under the same condition.** Fresh checkout of `ca17bc05` with this
  change and outbound traffic refused: **6,385 passed, 529 skipped, 37 deselected, 1 failed, in
  193 s.** The one failure is outside this fix (see DEFERRED below).
- **The pins' assertions don't read fundamentals.** They check routes, caveats, price truncation,
  locatability and that snapshots are unchanged. So the companyfacts subset changes no assertion's
  input.
- **`tests/test_sec_reference_fixture.py`** adds 6 pins:
  - both files list every fleet name;
  - every fleet name resolves;
  - a non-fleet name (`MSFT`) raises `UnknownSymbolError`;
  - `GOOG` and `GOOGL` share an issuer (sliced by CIK too);
  - a seeded cache resolves with the network refused;
  - an unseeded cache fails loudly instead of fetching.
- **Mutants.** Each turned the named pins red, and each was restored:
  - the maintenance-path pins left unseeded → 6 failures naming the network;
  - `no_network` made a no-op → `test_an_unseeded_cache_fails_loud_instead_of_fetching`;
  - VRRM dropped from `company_tickers.json` → the first version SURVIVED, because the resolver
    merges both files and the exchange file still had VRRM. The per-file pin
    `test_both_ticker_files_list_every_fleet_name` was added, and it now reds with the builder's
    name in the message.

**DEFERRED: a ninth test of the same class, found by the full-suite run.**
`tests/test_synthesis_write_block.py::test_the_failure_is_counted_as_an_error_not_a_flag` calls
`assemble_cohort` on the DEFAULT Config (the real `data/`, not a temp one), so on a fresh checkout
it also fetches `company_tickers.json` live. Its fix differs: there is no temporary Config to seed,
and seeding the real `data/cache` would write into the checkout. It is left for its own change, not
widened into this one (CLAUDE.md: hold scope).

**This PR's own pre-PR review** (`/code-review high --fix`) reported 5 findings:

- **3 fixed:**
  - the builder read a cached ticker file with no TTL, so a stale local cache could be sliced; it
    now uses the resolver's one-day TTL;
  - the builder reported missing names from one file only; it now reports both;
  - every seed re-parsed about 30 companyfacts files; it now parses them once per process.
- **2 skipped:**
  - `no_network` duplicates the guard inline in `test_dilution_denominator.py`, and unifying them
    would edit that file;
  - seeding calls the private `CachedHttp._write_cache`, and a public method would change
    production code for a test need.

The full-suite run also caught the builder breaking the repo's script rule
(`tests/test_script_cwd_convention.py`): it now `chdir`s to the repo root in `__main__`, as the
other builders do.

**BOUNDARY.**

- **"Fresh checkout."** A `git worktree` of the commit with no `data/` cache.
- **"Network refused."** `HTTPS_PROXY`/`HTTP_PROXY` pointed at a closed local port, which fails
  every httpx request the same way a blocked sandbox does.
- **The fleet.** Committed dossiers ∪ scenario records ∪ `data/followed.json`, 27 names at
  `ca17bc05`. GOOGL's issuer adds GOOG, GOOGN and GOOGM, for 30 rows.
- **Timings.** One run each, on the operator's Mac, on 2026-10-23.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The cost.** 4.6 KB of fixture, and a builder to re-run in any PR that adds a fleet name. The
  coverage pin names the builder when it is needed.
- **ACCEPTED: the slice can go stale against SEC's live file,** for example a renamed ticker. The
  pins test routing over committed artifacts, not SEC's current listing, and the builder refreshes
  it.
- **ACCEPTED: these pins no longer exercise the real `data/cache` on a laptop.** That is the point:
  a pin must mean the same thing everywhere it runs.
