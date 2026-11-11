---
status: recorded
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# VRRM's `run-monthly` is rehearsed on copies (STATE row 38): it completes clean on current `main`, reads VRRM at its correction (4.44 on 2026-06-18) and holds it PENDING until the 2026-12-15 close lands; nothing was appended and nothing from the run is committed

**WHAT.**
- **The run.** `python -m vinci run-monthly` (RUNBOOKS §l step 3; `--as-of` left at its default,
  2026-11-11) ran once, from 13:00:44Z to 13:26:18Z, in a detached worktree of `main` at
  `2637e91b` (#1008, the GOOGL void). It exited 0 and printed `spread=None pending=4`. Step 4
  (`frontend/build.py`) then exited 0 and changed nothing under `frontend/`.
- **It ran 46 seconds after a hold it had not seen. It is a first rehearsal, not the one row 38
  asks for.**
  - Coordinator A asked on #1004 at 12:59:58Z to hold the rehearsal until a monitor PR merges.
    That PR makes `vinci monitor` apply a void by the session a day is filed under.
  - This session had last read #1004 at about 12:50Z, and the run started at 13:00:44Z.
  - Scoring keys a void on the run's `as_of` (`schemas.ledger.voids_by_decision`), and
    `run_monthly` reads no monitor day (only `data/monitor/benchmark_assignments.json`). So this
    run's book was the ledger as of 2026-11-11, with GOOGL out from its ruling date.
  - The rehearsal is run again after A posts on #1004 that the void-keying PR and the 2026-11-11
    monitor day have merged. Its record follows this one.
- **What it ran on: copies only.**
  - The store is an APFS clone (`cp -c`) of `/Users/work/Documents/GitHub/mosaic-theory/data/vinci.db`,
    taken at 12:59:20Z. It was sha256 `78e2239147045795a10ca27f48cd0057f54e2d624eddb20b599420622f77c4a1`,
    389,201,920 bytes, last written 2026-10-28 22:04 IST. Its bars ended 2026-08-05 and its
    `decision_ledger` table held 0 rows. The primary's file was hashed again after the clone and
    had not changed.
  - The Polygon cache (1,553 files) and the Tiingo cache (192 files) are clones of the primary's
    `data/cache/polygon` and `data/cache/tiingo`. Only `.env` is a link: it is read, never written.
  - The ledger is the worktree's own copy of `data/snapshots/decision_ledger.jsonl`, the 10
    committed rows, sha256 `a3c8af3e…`. The run re-seeded the store's ledger table from it and
    exported it back byte-identical.
- **The live calls the run made.** Each was its own, through the repo's clients:
  - **Polygon, 101 calls:**
    - 96 grouped-daily: 68 sessions from 2026-08-06 to 2026-11-10 that the store did not hold;
      6 restatement checks at the held sessions 2026-06-30, 07-22, 07-30, 07-31, 08-03 and 08-04
      (07-22 is SPY's last held bar); and 21 market holidays in the 730-day window, which return
      no bars and are asked again on every run;
    - 5 splits references: VRRM, IT, SMPL, IWM, MDY.
  - **Tiingo, 5 symbols** (VRRM, IT, SMPL, IWM, MDY), each over 2026-06-10 → 2026-11-11. None was
    for GOOGL, which is voided.
- **What it would score for VRRM.** VRRM is `V-VRRM-screen2-20260617`, AVOID_TERMINAL, benchmark
  IWM, read at its correction `R-VRRM-screen2-20260617`. Its 180 days run to **2026-12-15**.
  - **At maturity** the row resolves on the first run whose store holds IWM's 2026-12-15 bar.
    It is read from these closes:
    - VRRM: entry 4.44 on 2026-06-18 (the store's close that session is the same 4.44, so the
      split basis passes); exit at VRRM's 2026-12-15 close.
    - IWM: entry 295.59 on 2026-06-18; exit at IWM's 2026-12-15 close.
    - Dividends from Tiingo's `divCash` on each leg's own sessions after the entry, through the
      exit. VRRM pays none. IWM's in the window so far is 0.750436 on 2026-09-15 (its 2026-06-15
      ex-date is before the entry). Its previous ex-dates fall mid-month, so its December one
      may land on or near the horizon session.
  - **The interim mark today** (as of 2026-11-11, last bar 2026-11-10), read through
    `score_ledger` with the run's own sources:

    | Leg | Entry close | 2026-11-10 close | Total return | Price return |
    |---|---|---|---|---|
    | VRRM | 4.44 (2026-06-18) | 2.06 | −53.60% | −53.60% |
    | IWM | 295.59 (2026-06-18) | 280.58 | −4.83% | −5.08% |

    The excess is **−48.78 pts**: the AVOID leg is lagging its benchmark.
  - **The spread stays n/a after VRRM resolves.** No BUY leg resolves before 2027-01-16 (IT and
    SMPL's 2026-07-06 rows), and GOOGL is voided. The first report after 12-15 reads 1 AVOID
    resolved and spread n/a.
- **The run never mis-scores early.** The same `score_ledger` call at `as_of` 2026-12-15, on the
  same store, holds VRRM PENDING: "its horizon 2026-12-15 has passed, but the benchmark's last bar
  on or before 2026-12-15 is 2026-11-10 — awaiting the horizon session's close."

**FAILURES AND WARNINGS.** There were no failures: no `SplitBasisError`, `SplitsUnreadError`,
`TotalReturnUnknownError`, `StaleExitError` or benchmark refusal. Four warnings:
1. **`data/snapshots/issuers.jsonl` changes on every run that ingests SPY.**
   - Cause: `universe.benchmark_identity` gives every benchmark the one issuer id `IDX`, named
     `"<SYM> (benchmark)"`. `run_monthly` upserts IWM, then MDY, then SPY, so the row is renamed
     after the last one.
   - The committed row reads `IWM (benchmark)`; the run exports `SPY (benchmark)`.
   - RUNBOOKS §l step 6 commits `data/snapshots`, so the real run's PR would carry this one-line
     flip. That is derived-artifact churn, not a scoring defect.
2. **A voided decision still picks a benchmark to ingest.**
   - Cause: `run_monthly` builds its benchmark set from every row with `event is None`. V-GOOGL
     is such a row, so SPY is refreshed for a decision that is out of the record.
   - It costs one grouped-daily call (SPY's 2026-07-22 restatement check) and produces warning 1.
     It never reaches a score: `score_ledger` drops the void.
3. **The store's sha256 moves when it is opened, with its content unchanged.**
   - The run left the store at `ce418fbf…` (430,219,264 bytes).
   - The read-only `score_ledger` script above moved it to `5cb27b51…`.
   - `sqlite3 .dump | shasum -a 256` reads `befeffd1…` for both.
   - This corroborates row 38's 2026-11-09 observation. A file hash is not a content identity
     for this store.
4. **The scoring report carries no interim marks.** It lists resolved rows only, plus each held
   row's note, so the interim read above needed `score_ledger` directly. The committed
   `scoring_report.md` also predates both appended rows. The real run's report adds VRRM's
   correction note and GOOGL's void note, as this one did.

**WHAT MUST CHANGE BEFORE THE REAL RUN.** These are proposals, not code in this task:
1. **Name the store.** Row 38 says "the primary's `data/vinci.db`", and there are two primaries.
   - The store A refreshed on 2026-11-11 (`c9986363…` → `a6a18e7d…`) and voided GOOGL on
     (`→ 2b75fe39…`) is `/Users/mac/…/data/vinci.db`.
   - This machine's (`/Users/work/…`) is the one rehearsed here: bars to 2026-08-05, ledger
     table empty.
   - The run does not depend on which: it re-seeds the ledger from the committed snapshot, and
     its export matched it byte for byte. Only the number of Polygon calls differs (96 grouped
     calls from 08-05; about 25 sessions plus the 21 holidays from 11-10).
   - The operator names the machine, and the real run uses a clean `main` worktree there.
2. **Do not commit the `issuers.jsonl` flip** (warning 1) unless the IDX issuer's name is made
   independent of the last benchmark upserted. The fix is a neutral name in
   `universe.benchmark_identity`, or an issuer per benchmark; it is S3-adjacent and is not built
   here.
3. **Timing.**
   - Re-rehearse on a copy around 2026-12-07 (about 12 minutes from a store that is current to
     11-10).
   - Score on 2026-12-16 after 10:30 IST (00:00 ET): the plan refuses a session's grouped-daily
     until midnight ET, and a refused session reads as a holiday, so an earlier run reads 12-15
     as missing and holds VRRM PENDING.
   - If Tiingo has not served 12-15 yet, the run stops with `TotalReturnUnknownError` by design;
     re-run once it has.
4. **Optional, efficiency only:** the 21 holiday re-asks cost about 5 minutes a run at 4
   requests a minute.

**WHY.** STATE row 38: VRRM is the first outcome the spread will ever carry, and it is scored
from a store that `run-monthly` itself refreshes. Its refusals surface only when it runs. The
rehearsal was unblocked once #1008 (the GOOGL void artifact, ledger 9 → 10 rows) merged, as
coordinator A asked on #1004.

**HOW VERIFIED.**
- The run's own output (`spread=None pending=4`, exit 0).
- `git status` in the rehearsal worktree after steps 3 and 4: only `data/snapshots/issuers.jsonl`
  and `data/snapshots/scoring_report.md` changed. `decision_ledger.jsonl` kept sha256 `a3c8af3e…`.
- Every live call counted from the cache files the run wrote (each entry's URL and `fetched_at`).
- The interim marks and the 12-15 hold come from `score_ledger` on the same store, with sources
  built over the run's span and as-of. That made no request: every response was the run's cached
  copy, fetched 13:24–13:26Z.

**BOUNDARY.**
- Code: `main` at `2637e91b`. Nothing on the scoring path changed by `c0d6d830`: `git diff`
  over `vinci/scoring`, `vinci/eod`, `vinci/store`, `vinci/ledger`, `vinci/orchestrator.py`,
  `vinci/universe.py`, `vinci/monitor.py`, `vinci/cli.py`, the ledger snapshot and the benchmark
  assignments is empty.
- Store: the clone above, before the run (`78e22391…`) and after it (`ce418fbf…`; content
  `befeffd1…`).
- Returns: total return, as of 2026-11-11, on the store's bars through 2026-11-10, for the four
  live screen-origin decision rows.
- Pending count: screen-origin rows only (VRRM, IT, SMPL ×2). GOOGL is voided and so is not
  pending.
- Call counts: cache files written between 13:00:44Z and 13:26:18Z in the rehearsal's Polygon and
  Tiingo caches.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0 of LLM. 101 Polygon calls and 5 Tiingo symbols: November's Tiingo symbol count, a floor
  (`TiingoBudget`), rises by at most 5.
- Nothing was written to the primary checkout, the committed ledger or `main`.
- The worktrees and store clones stay in the session's scratchpad.
