---
id:
status: shipped
date: 2026-10-11
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — `state pull` keeps every paid-call record, run id and cost through a rebuild, counted once

**WHAT.** The pilot condition on PR #703: a `state pull` that rebuilds the registry from the
state branch no longer loses the paid model-call records, costs and run ids of local runs the
branch lacks (`state.py`, `store.py`, `schemas.py`, `pipeline.py`, `engine.py`, `report.py`,
`health.py`):

- Every run the branch lacks is CARRIED into the rebuilt registry — run id, times, cost and
  every call row unchanged — marked `ledger_only` (why its evidence is not here). A replay that
  paid nothing is not carried; it is replayed again and its originals are carried.
- The replay run names the runs it replays (`replay_of`, followed through a replay of a
  replay). Its model answers come from the cache: the spend is counted once, on the originals.
  The evidence is derived once, by the replay — nothing from the original run is merged in.
- After the rebuild the paid-call ledger is checked — every paid call of the replaced registry
  and of the branch present exactly once at the same cost, else the pull fails loud — and
  printed (`paid-call ledger: N call(s), $X`).
- A replay keeps the original ingestion dates: the upload time (already), the article's
  `first_seen_at`, the thesis's `created_at` and its "first ingested" line.
- The weekly report never counts a carried run, and a carried scan never bounds the week;
  health never reads a carried scan as a channel's latest.
- A local run whose id names a different run on the branch is refused; `--force` pulls without
  carrying it and says so with its cost (its record stays in the backup).
- Nothing new crosses to the branch but run and call rows; no article text.
- The guide's last eight-source example ("Accessible sources: 6 of 8") is corrected.

**WHY.** Found on 2026-10-11 by the GitHub state test (`2026-10-11-theme-intelligence-seven-sources.md`,
open item): a replay recorded the analysis under a NEW run from the cache at $0, and the
original runs — R-20261011T145550Z-ingest ($0.3082) and R-20261011T150313Z-ingest ($0.4661) —
survived only in the pre-pull backups, so the branch under-reported what was spent.

**HOW VERIFIED.**

*Real, on the private repository's temporary branch `theme-intelligence-state-test-20261011`
(synthetic documents; the production branch untouched)* — log:
`docs/theme_intelligence/state-pull-ledger-2026-10-11/run-log.txt`:

1. a fresh restore BEFORE: 4 paid calls, $0.5065 (the two runs above missing);
2. machine X (synced at `2cf1f7e`) makes two paid imports: $0.2550 and $0.2523;
3. machine Y — the operator's pre-pull backup — pulls with the fix: carries
   R-20261011T145550Z-ingest (3 paid calls, $0.3082); ledger 7 calls, $0.8147; push `4d53cd7`;
4. X's push is refused (stale); X pulls: carries its two runs, replays both documents from the
   cache ($0, `replay_of` both), ledger 14 calls, $1.3220; push `d21e466`;
5. machine W — the fresh environment's pre-pull backup — pulls: carries
   R-20261011T150313Z-ingest (5 paid calls, $0.4661); ledger 19 calls, $1.7882; push `8d9d00a`;
6. a FRESH restore AFTER: **19 paid calls, $1.7882, identical call by call (id, run, cost) to
   the union of every participant's records before; none missing, none extra**; the four
   carried runs under their original ids and costs; the replay $0;
7. the two replayed imports keep their upload time, article first-seen time and thesis
   created time, to the microsecond (X's pre-pull backup vs the fresh restore);
8. a $0 scheduled-style scan on the restore: one weekly report, each of the 5 uploads listed
   once, the carried runs not counted ("this report's 6 runs"); health 2 / 3 / 2 of 7; QA
   22/22;
9. the branch tree: 22 files, all JSONL; 0 article blocks with text; no whole document text,
   PDF bytes or credential pattern. (The first version of this check flagged the note's banner
   sentence in `claims.jsonl`: the model had quoted it as a claim — a short verbatim quote, by
   design — so the check now looks for the note's whole paragraph instead.)

*Tests:* `tests/test_theme_intelligence_state_ledger.py` (7): two paid imports → pull →
replay → push → fresh restore, the ledger, run ids, costs, ingestion dates and per-article
evidence unchanged; a second pull; two pulls before a push; a forced pull (and a later
ordinary pull not blocked by the carried run); an id clash (refused untouched; forced: said,
with its cost); a ledger that does not reconcile; a carried scan. **19 mutants, all killed**
(one survived at first — the report test's imports fell outside the week either way; the test
was rewritten so the guard decides).

**BOUNDARY.** Real run: 2026-10-11 17:31–17:35 UTC, code at `e8c1c58d`, the temporary
branch from `2cf1f7e` to `8d9d00a`. Ledger counts: every llm_calls row not served from the
cache, by call id, across the named registries and the two pre-pull backups. Cost of this
pass: **$0.5073 measured** (machine X's two imports; every other step made no model call).

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- The document record D-737cf809 on the test branch still shows its private copy's hash as its
  name and the replay time as its upload time — written before the 2026-10-11 replay fix; this
  pass restores the run's record, not that document record. Test branch only.
- A run whose id names a different run on the branch cannot be carried (one id, two records):
  refused, or under `--force` reported with its cost and kept in the backup.
- Replay runs made before this fix (two on the test branch) carry no `replay_of`.
