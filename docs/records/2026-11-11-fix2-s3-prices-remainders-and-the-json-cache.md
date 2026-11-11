---
status: shipped
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, prices: RF-D5, D10, D11 and D12 confirmed fixed on main; RF-D5's two remainders closed (the grouped left edge names a name it could not check, and the unattended callers print what an ingest names); STATE row 42 (2), a non-JSON body is never cached

**WHAT.** This is stream S3 of TeamNostra fix request 2 (issue #1004: prices, ledger, refresh).

**1. The four price IDs are fixed on main, by #991 (`87f763d3`).** Each was confirmed by running
TeamNostra's own reproduction on main `2637e91b`. The scripts are from fix pack 2's `notes/F_work/`
and were run unchanged from a copy outside the repo, with `vinci` from this checkout.

| ID | Reproduction | Audit at `622786a2` | main `2637e91b` |
|---|---|---|---|
| RF-D5 | `aggs_splice.py` | a ×0.5 step on 2026-03-02, `ret_6m` −0.5, drawdown −0.505, summary names nothing | `restated {'SPLT': [0.5]}`, no step, `ret_6m` 0.0, drawdown −0.0099 |
| RF-D10 | `misc_repros.py` R1 | no frontier: `last` 150.0 as of 2026-08-31, `ret_3m` 0.5 | no frontier: `last` 100.0 as of 2026-06-30, `ret_3m` 0.0 |
| RF-D11 | `misc_repros.py` R2 | TR on Tiingo bars 0.111111 | the notes' rows carry `adj*` only and now RAISE ("an unreadable Tiingo row … no bar is guessed"); with the raw fields Tiingo serves beside them, TR 0.0 |
| RF-D12 | `misc_repros.py` R3 | no raise; 22 days fetched, 0 bars | RAISES `EodError`: "the source REFUSED a date inside the plan's 730-day window (403 NOT_AUTHORIZED)" |

**2. RF-D5's remainders, recorded by #991 as "FOUND, NOT FIXED", are now fixed.**
- **The grouped path's left edge skipped a held name the source did not serve, and named it
  nowhere** (`eod.client.restate_held`, which `continue`d). That name's older bars went
  unchecked and appeared in no summary list, beneath new-basis bars. The skip now collects the
  name, and `ingest_prices` names it `unanchored` when this run wrote it new bars. The right edge
  already named the same case that way. A name the window wrote nothing for is not named,
  because there is no splice to warn of.
- **The unattended callers discarded the ingest summary.** These are `screens.run.screen_universe`
  (the weekly screen; universe and benchmark), `orchestrator.run_monthly` (the refresh before
  scoring) and `scripts/build_price_fixture.py` (run by the weekly job). Each now prints
  `eod.client.basis_lines(summary)` to stderr: one `PRICE BASIS:` line per name restated, moved in
  price alone, or left unanchored. The output is empty when the summary names nothing.
  `vinci refresh` already printed the whole summary and is unchanged.

**3. STATE §5.0 row 42 (2): `CachedHttp.get_json` parses a body before caching it.**
- `get_text` wrote any 200 body to the cache before `get_json` parsed it. So an interstitial
  served once for a submissions document or an older page stayed the cached copy for its whole
  TTL (one day). Every windowed read of that filer, in every process, read "could not be read"
  until it expired.
- Now a non-JSON body raises the same `ValueError` it did, with nothing written. A non-JSON copy
  already on disk is a miss and is fetched again. `get_text`, used for documents read as text,
  caches any 200 body, as before.

**Row 42 (1), the monitor aborting on an unreadable older page, is NOT in this PR.** Its fix is
in `cli._cmd_monitor`. Coordinator A's #1006 has `vinci/cli.py` in flight, and the S3 rule is to
wait rather than edit a file A has open. It is S3's next change after #1006 merges.

**WHY.** These are the remainders #991's record left, plus row 42's netcache edge, which the
stream owns since 2026-11-11 (#1004).

**HOW VERIFIED.**
- **Fail first.** The new tests were run on main's `vinci/eod/client.py`, `vinci/screens/run.py`,
  `vinci/orchestrator.py`, `scripts/build_price_fixture.py` and `vinci/netcache.py`, with a
  placeholder `basis_lines` returning `[]` so that each fails at its own assertion.
  - `tests/test_prices_order5.py`, the 3 new left-edge tests: 1 fails on main (`unanchored == []`)
    and the 2 negative pins pass. The positive pin uses IESC's real 2026-08-05 restatement pair.
  - `tests/test_price_basis_said.py`, 5 tests: all 5 fail on main. They pin the call sites: the
    weekly screen's stderr, the real `run_monthly`'s stderr, the script's source, and no bare
    ingest call in either module.
  - `tests/test_netcache_json_body.py`, 4 tests: 2 fail on main and the 2 negative pins pass.
    They run on Gartner's committed submissions document and older page -001 (#878's fixtures),
    through a real `CachedHttp` and a real `EdgarClient`. On main, the second read was served the
    cached interstitial from disk and raised again. Now it fetches the page and returns its 8-Ks.
  - All 12 pass on this branch.
- **The neighbours pass:** price, ingest, screen, orchestrator, run-monthly, EDGAR, SEC pacing,
  older-pages and amended-filing tests, 333 and 191 tests in two runs, with `-m "not network"`.
  The full suite result is in the PR.
- **Drift guard.** `vinci/screens/run.py` is re-pinned `--refactor`: it only prints. No dossier
  reads `eod.client` or `netcache` output differently.

**BOUNDARY.**
- The reproductions ran on 2026-11-11 against main `2637e91b`, on TeamNostra's constructed worlds
  (`fakes.py`): `SPLT` plus IWM and SPY on a weekday calendar. There was no network: the scripts
  strip `POLYGON_API_KEY` and `TIINGO_API_KEY` and serve fakes.
- R2's raw-field variant is this record's own: a flat $10 dividend on 2026-03-09, raw close
  100 → 90, `adjClose` 90 on every day, `splitFactor` 1. The script is outside the repo.
- "1 day TTL": `EdgarClient`'s `_ONE_DAY` on the submissions document and each older page
  (`_submissions`, `_older_page`).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A stderr line is not a record.** The weekly and monthly runs print the names, but no run
  artifact carries them. A typed field on the screen's run manifest would be the next step. It
  is not built here because the manifest is the screen's committed schema. Falsifier: an
  unanchored name in a weekly's log that no reviewer saw.
- **An interstitial now costs one request per read until SEC serves the page.** Before, it cost
  none, but the read failed for a day. The SEC pacing and refusal rules (#854, #939) still apply
  to every retry.
- **The monitor still aborts on an unreadable older page** until row 42 (1) lands.
