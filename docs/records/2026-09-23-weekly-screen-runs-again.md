---
id:
status: shipped
date: 2026-09-23
prs: [645]
supersedes:
superseded-by:
---

# The weekly screen ran to completion for the first time since 2026-08-24, and the served queue advanced four weeks

**WHAT.** `run_weekly` completed locally at `--end 2026-09-22`, writing run `2026-09-22-01`. The
served queue moves from the **2026-08-24** screen to **2026-09-22**: 268 → **289** names, **95
entered, 74 left**. The universe rebuilt to **2,126** names (as_of 2026-09-22) from 7,661
considered; 380 G1/G2 survivors, 289 candidates ranked, 289 structurally scanned with 48 flagged.
Artifacts: `ranked_queue.{jsonl,md}`, `candidate_records.jsonl`, `universe_snapshot.jsonl`,
`universe_stats.json`, `issuers.jsonl`, `securities.jsonl`, and the new
`screen_runs/2026-09-22-01.{jsonl,manifest.json}`.

**WHY.** The queue had been frozen for four weeks because the run could not finish: the refresh
re-pulled its whole 1,825-day window every time, and the client paced 20x above what the Polygon
plan serves. Both are fixed — `docs/records/2026-09-23-ingest-skips-sessions-the-store-already-holds.md`
(#643) and `docs/records/2026-09-23-polygon-pace-matches-the-plan.md` (#644) — and this run is the
first evidence they work together on the real path rather than in a dry run.

**AND THE QUEUE ADVANCING BROKE FOUR THINGS, each fixed here.** A screen re-rank is not a
self-contained artifact write; it moves the fleet as-of and the maintenance/candidate split, and
ten tests reddened saying so. The suite caught every one before the push (ARTIFACT-PASS rule):

1. **Price fixtures stopped at 2026-09-21 while the fleet as-of moved to 2026-09-22.** Rebuilt all
   18 series to `2024-12-02 .. 2026-09-22`, 452 bars each.
2. **CNXC, FUBO and VRRM left the queue**, so they moved onto the MAINTENANCE route — which reads
   committed fixtures, not the store — and had none. They now have them; that is the 3 new series
   above.
3. **The cohort pool had no rows for `2026-09-22-01`.** Built: **2,910 pool rows**, 0 resolver
   failures (142 skipped for no/denylisted SIC, 776 not operating-company equity, 1,052 with no
   price at a window endpoint). The queue was then RE-RANKED so its cohort reads come from its own
   run's pool rather than the previous run's: **0 ranks changed** — the cohort channel is
   inform-only, exactly as designed — while `cohort` calls went 16 → 54 and `no-cohort` 90 → 35.
   **The weekly job ranks BEFORE a pool for its own run can exist**, so pool-then-re-rank is a
   required tail step, not an optional one.
4. **`test_a_mixed_vintage_candidate_file_gets_no_cohort_and_still_gets_a_queue` had a literal
   vintage in its SETUP** — `.replace("2026-08-24T00:00:00", …)`. Once the candidates advanced to
   2026-09-22 the replace matched nothing, the file stayed single-vintage, and the test reddened
   claiming the guard had failed. The guard was fine; the mutation had silently stopped happening.
   Both stamps are now derived from the artifact, and the test asserts its own mutation took.

**AND ONE OPERATOR RULING.** The new screen admitted **TECX** at rank 174 while it is also a
QUALITY-book follow, and the engine refuses to assemble a name whose two routes disagree rather
than pick one. The follow reason on file argued the name *fails* the screen's gates "on their own
terms"; that premise is now false — TECX fell **32.2 points further than its industry cohort**
(Biological Products, 55 peers) over the screen's window. **Operator ruling 2026-09-23: the follow
keeps it**, recorded in `data/followed.json`'s `overrides_screen`, which also marks the follow
reason's gate sentence stale.

**HOW VERIFIED.**

* **The skip, measured exactly, not read off a progress line.** Recomputed against a copy of the
  PRE-run store (taken 13:57, before the run; the store had not been written since 08:03) using the
  universe the run actually screened: **1,225 sessions HELD, 79 FETCHED** of 1,304 weekday
  sessions — 51 holding no bars (market holidays), 28 below the 1,063-bar floor
  (`2026-08-12 .. 2026-09-21`, the per-name `refresh --aggs` residue), 0 inside the restatement
  window. The run's own progress line agrees: `1201 held` at session 1,250.
* **The network cost.** Exactly **ONE** grouped-daily network call during the ingest (2026-09-16);
  the other 78 were netcache hits. The run's Polygon spend was dominated by the UNIVERSE build's
  per-name share-count fallback, not the price refresh.
* **Pacing held under load.** ~40 minutes of continuous per-ticker fetching at a measured ~3.4–3.9
  calls/min with **no 429 and no retry**. Total wall clock ~53 minutes.
* **The four remediations, each re-run to green** before the full suite: `test_maintenance_path`
  (fixtures + the TECX ruling), `test_weekly_run_dating` (fixture vintage), `test_cohort_pool` (the
  pool), `test_cohort_anchoring::test_the_falsifier_can_actually_fire` (the re-rank restored arms
  big enough for the pre-registered falsifier to be testable at all), `test_snapshot_vintage` (the
  derived-stamp fix).
* **Suite.** Full offline suite run against the freshly-written artifacts (ARTIFACT-PASS rule).

**BOUNDARY.** Window `2021-09-23 .. 2026-09-22`, weekdays, unit = sessions; population = the
universe this run wrote, 2,126 names in-universe, floor 1,063 bars. Queue counts are rows in
`ranked_queue.jsonl` at HEAD `083ba8e` vs this run. Run wall clock and fetch rates are from the
2026-09-23 15:25–16:18 local run. **The "one network call" is not a steady-state number:** the
day's earlier failed attempts had left 548 fresh grouped-daily entries in the 24h netcache. A week
with a cold cache fetches ~79 sessions ≈ 20 minutes at 4 calls/min.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **This ran LOCALLY, and only can.** CI holds no store, so it would re-acquire all 1,304 sessions
   (~5.4 hours at this pace). STATE.md §5.0 row 31, owner: operator.
2. **Every committed dossier page still carries the 2026-08-24 fleet as-of.** The queue advancing
   does not re-render them; that is the next pass, and it requires full re-assembly (a `--no-llm`
   build is refused over a committed synthesis by `_refuse_synthesis_overwrite`).
3. **The universe build's per-name fallback is the expensive phase** — one Polygon call per
   admissible name with no XBRL share count anywhere (944 `no_shares` drops this run). At 4/min it
   dominates the run. Not changed here; stated so the next operator knows where the time goes.
