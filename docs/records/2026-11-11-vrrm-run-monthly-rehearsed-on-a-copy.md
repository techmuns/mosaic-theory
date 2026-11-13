---
status: recorded
date: 2026-11-11
prs: [1018]
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

**BEFORE THE REAL RUN — RULED, WITH ONE QUESTION OPEN.**
- **The ruling.** The operator accepted this record's proposals (operator 2026-11-11, verbatim:
  "Yes, as proposed (Recommended)", recorded by A on issue #1004 at 14:09Z):
  1. score on `/Users/mac`'s store (refreshed, with the void in; sha256 `2b75fe39…`) on
     **2026-12-16 after 10:30 IST**;
  2. re-rehearse on a copy around **2026-12-07**;
  3. keep the `issuers.jsonl` `IDX` flip (warning 1) **out of the commit**;
  4. B owns it;
  5. A's monitor void-keying PR (#1015) lands first, and A posts on #1004 when it does.
- **Why those dates.**
  - The plan refuses a session's grouped-daily until midnight ET (10:30 IST), and a refused
    session reads as a holiday. A run before then reads 12-15 as missing and holds VRRM PENDING.
  - If Tiingo has not served 12-15 yet, the run stops with `TotalReturnUnknownError` by design;
    re-run once it has.
  - The 12-07 re-rehearsal takes about 12 minutes from a store current to 11-10.
- **OPEN, for the operator; not resolved here: who runs it, where.**
  - B owns the run, but the named store is on A's machine (`/Users/mac`), and B's sessions run on
    `/Users/work`. This machine's primary store is the one rehearsed above: bars to 2026-08-05,
    ledger table empty.
  - The run re-seeds the ledger from the committed snapshot, and its export matched it byte for
    byte, so the two stores differ only in the Polygon calls the refresh makes (96 grouped calls
    from 08-05 here; about 25 sessions plus the 21 holidays from 11-10 on `/Users/mac`).
  - Two ways: A runs it on `/Users/mac` for B, or the operator allows `/Users/work`'s store after
    a refresh.
- **Not ruled, efficiency and hygiene only:**
  - the `IDX` issuer's name could be made independent of the last benchmark upserted, with a
    neutral name in `universe.benchmark_identity` or an issuer per benchmark (S3-adjacent, not
    built here);
  - the 21 holiday re-asks cost about 5 minutes a run at 4 requests a minute.

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
## Amendments

- **2026-11-12 — THE SECOND REHEARSAL RAN CLEAN, ON `/Users/work`, ON COPIES, AFTER A'S SIGNAL** (S1, for B).
  This is the rehearsal row 38 asked for. It ran once #1015 (`1df0dc18`, the void keyed on the session filed) and the 2026-11-11 monitor day (#1022, `493995f0`) were on main. The operator has since ruled that the 2026-12-16 scoring runs on `/Users/work` after a fresh price refresh ("Approve all three", `docs/records/2026-11-12-operator-delegation-and-defaults.md`), so this run is its dress rehearsal.
  - **Code:** a detached worktree of `main` at `4b2f0cb9`. Nothing on the scoring path has changed between it and main `650057f3`: `git diff` over the paths in this record's boundary is empty.
  - **Copies only.**
    - Store: an APFS clone of `/Users/work`'s primary `data/vinci.db`, taken at 14:06:06Z. sha256 `78e2239147045795a10ca27f48cd0057f54e2d624eddb20b599420622f77c4a1` (the same file as the first rehearsal), 389,201,920 bytes, content `.dump` `62ac9d76…`, bars to 2026-08-05. The primary's file hashed the same before and after the clone, and again after the reads below.
    - Caches: clones of the primary's Polygon cache (1,563 files) and Tiingo cache (202 files).
    - `.env` is linked read only.
  - **The run.** `python -m vinci run-monthly` (default `--as-of` 2026-11-12) ran once, 14:06:32Z → 14:32:24Z. It exited 0 and printed `spread=None pending=4`, with no failure.
  - **The ledger exports byte-identical.** `data/snapshots/decision_ledger.jsonl` kept sha256 `a3c8af3e8dd979e04ad20f94691a0362bef2c77913930d53469514cad5c42675` (10 rows). Of the 97 tracked `data/snapshots` files, only two changed: `issuers.jsonl` (warning 1's `IDX` flip, IWM → SPY) and `scoring_report.md` (VRRM's correction note and GOOGL's void note, warning 4).
  - **The store.** The run moved it from `78e22391…` to `cd8620cf8b27a9d4ca22a52a21aa6b91bcb5e41e850a94410af0d34c844dfb8e` (430,755,840 bytes), content `.dump` `cf2359f1b7b66b404692d676b7cd1654a18c9b170f862486cc8018a5eca09ac4`. A second clone, opened by `score_ledger` for the reads below, moved to `f1faf30f…` with the same content. That is warning 3 again.
  - **Latest bars:** VRRM 2.06 and IWM 283.09, both on **2026-11-11**. IT, SMPL, MDY and SPY also end 2026-11-11. The 2026-11-12 session was not yet served, because the run was before midnight ET.
  - **The interim mark**, as of 2026-11-12, read through `score_ledger` with sources over the run's own span and as-of:

    | Leg | Entry close | 2026-11-11 close | Total return | Price return |
    |---|---|---|---|---|
    | VRRM | 4.44 (2026-06-18, the correction) | 2.06 | −53.60% | −53.60% |
    | IWM | 295.59 (2026-06-18) | 283.09 | −3.98% | −4.23% |

    The excess is **−49.63 pts**. At `as_of` 2026-12-15, on the same store, VRRM is held PENDING: "its horizon 2026-12-15 has passed, but the benchmark's last bar on or before 2026-12-15 is 2026-11-11 — awaiting the horizon session's close."
  - **The live calls.** Polygon made 102:
    - 97 grouped-daily: 69 sessions 2026-08-06 → 2026-11-11; 7 restatement checks at the held sessions 06-30, 07-22, 07-30, 07-31, 08-03, 08-04 and 08-05; and the same 21 holidays;
    - 5 splits references: IT, IWM, MDY, SMPL, VRRM.

    Tiingo made 5 (IT, IWM, MDY, SMPL, VRRM). The reads above made none: the caches held 1,575 and 207 files before and after them.
  - **Warnings 1–4 recur unchanged.** Warning 2 also still holds: the voided V-GOOGL still has SPY refreshed.
  - **BOUNDARY:**
    - calls are the cache files written between 14:06:32Z and 14:32:24Z in the cloned caches;
    - returns are total return, as of 2026-11-12, on bars through 2026-11-11, for the four live screen-origin rows (VRRM, IT, SMPL ×2; GOOGL is voided);
    - the snapshot count is `git ls-files data/snapshots` at `4b2f0cb9`.
  - **COST:** $0 of LLM. Nothing from the run is committed, and the primary checkout and its store are untouched. The re-rehearsal around 2026-12-07 and the scoring run on 2026-12-16 after 10:30 IST (RUNBOOKS §l) remain.
