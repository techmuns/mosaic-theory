---
id:
status: shipped
date: 2026-11-13
prs: [1061]
supersedes:
superseded-by:
---

# The monthly spend report: each paid bucket's list-price spend in a UTC month, read from the records that already exist, refusing nothing (operator 2026-11-13: "Report only"). November reads $336.39 over four buckets; confirmations and validate-keys record no cost, and the report says so

**WHAT.** Issue 1004, lane 4, part B.
- B's design (issuecomment-6847522000) proposed a monthly ledger per bucket that would refuse a
  run crossing its month's cap.
- A's operator-approved reply put the cap values with the operator.
- The operator then ruled, relayed by B (issuecomment-6847993179): *"Report only"*. The ledger
  reports and refuses nothing. Per-run control is unchanged: every paid run still spends only
  under the operator's approved cap.

`python -m vinci.spend --month YYYY-MM [--evals-ledger FILE …] [--evals-root DIR …]
[--theme-ref REF] [--json]` (`vinci/spend.py`) reads each bucket from the record it already has.
It adds no write path.

| bucket | read from | what it cannot see |
|---|---|---|
| pages | `data/snapshots/assembly_runs/*.jsonl` (committed): one line per name a build attempted, with refused and failed lines included. `usd` is the list price of its metered calls. Each line is dated by its own `started_at`. | a build whose run file was not committed |
| confirmations | `data/snapshots/proposal_confirmations.jsonl`: rows counted by `drawn_at` | **every cost.** A row carries no `usd` or usage, and a confirmation refused after its draws writes no row. The bucket is NOT RECORDED, and no file is committed yet. |
| evals | the budget ledgers (`vinci.evals.replay.Budget`), which are outside the repo by design. Only the ledgers passed in are read; with none passed the bucket is NOT READ, never $0. A draw row has no time of its own, so it is dated by the latest stamp above it: the approval's `opened_at`, or a `build_start`'s `started_at`. A copy that is another ledger's bytes, or an earlier prefix of them, counts once. | a ledger not passed in, or one kept on another machine; and the month of a `run-compare` or `judge` draw, which writes no stamp and so can fall in an earlier month |
| theme desk | `registry/llm_calls.jsonl` on the `theme-intelligence-state` branch, read with `git show`. The weekly CI run and a local `state push` write it, so **CI's spend is visible here.** Rows have `cost_usd` and `at`; a cache hit costs $0, and a live call with no cost is unpriced. | a local run not yet pushed to the branch |
| graph judge | `judged_by` in the committed `data/graph_coverage.json`. A month before the recorded re-judge is NOT READ. | any earlier re-judge, because each run overwrites the last; a re-judge that STOPPED and wrote nothing; and any `graph-coverage` run, which records no cost |
| validate-keys | nothing | **every run.** A one-token billable ping per CI run is recorded nowhere: NOT RECORDED |

**How the report reads its records.**
- Months are UTC calendar months.
- Every figure is the list price the writer recorded.
- A missing figure is `None`, never zero:
  - an unpriced row is counted apart;
  - a bucket with no record is named in the total as "NOT included".
- A malformed record raises. Skipping it would print a total smaller than the spend.

**No new write path, and why.** Two buckets record no cost: confirmations and validate-keys.
- **Confirmations:** recording the cost means touching `log-verdict`'s seal path
  (`vinci/dossier/confirmation.py`). Its row would gain `usd` and usage, and a confirmation
  refused after its draws would need a cost-only row. That deserves its own review, so it is
  proposed, not built. No confirmation has run yet: no `proposal_confirmations.jsonl` is
  committed.
- **validate-keys:** recording it would need CI to commit from a `contents: read` job, for a
  one-token call. It is left unrecorded and said so.

**WHY.** Operator, 2026-11-13: *"Report only"*. Spend was recorded in five places in four shapes:
- committed JSONL;
- ledgers outside the repo;
- a state branch;
- a field that each run overwrites.

Nothing summed a month across them. The survey behind the table read every paid path:
- dossier builds;
- the seal-time confirmation;
- `run-compare`, `run` and `judge` in the evals harness;
- `graph-coverage` and `graph-rejudge`;
- the theme desk's commands and its weekly workflow;
- `validate-keys`.

The weekly screen and monthly scoring make no paid call. The Polygon, Tiingo, SEC and R2 calls are
metered as quotas, not in USD, and are out of scope.

**HOW VERIFIED.** The real run, at `3d195fcd`, 2026-11-13 10:45Z, with `origin/theme-intelligence-state` at `ea8fb4a6`:

```
spend report, 2026-11 (UTC calendar month, list price) — reports, refuses nothing
bucket                usd   rows  source
pages              $66.98     16  data/snapshots/assembly_runs/*.jsonl
confirmations           —      0  data/snapshots/proposal_confirmations.jsonl   (NOT RECORDED)
evals             $243.07    592  budget ledgers passed to this run (6 of 6 carry a row)
theme desk         $23.73    185  origin/theme-intelligence-state@ea8fb4a6:registry/llm_calls.jsonl
graph judge         $2.61      1  data/graph_coverage.json (the re-judge of 2026-11-09)
validate-keys           —      0  none   (NOT RECORDED)
total of the 4 bucket(s) read: $336.39 — NOT included: confirmations, validate-keys
```

Each figure was checked a second way, apart from the module:
- **pages:** the 16 lines of the 16 run files named `2026-11-*` sum to $66.9843, with 0 unpriced.
- **evals:** the six ledgers sum to $243.0683:
  - fix 3b, $30.724;
  - driver facts, $27.5048;
  - RA-D2 and RA-D4, $30.5374;
  - RA-D2, $30.2778;
  - RA-D4, $27.3239;
  - the vote rule's independence check, $96.7004.
- **theme desk:** 163 live calls, $23.72712; 22 cached, $0.
- **graph judge:** the committed `judged_by` reads `cost_usd` 2.6083 on 2026-11-09.

October at the same commit reads $136.49 over three buckets: pages, evals ($0.00, 0 of the six ledgers carry an October row) and the theme desk. Its graph judge is NOT READ, since the 2026-11-09 re-judge overwrote any earlier one.

**The tests** (`tests/test_spend_report.py`, 18 cases) are built from real records:
- committed assembly lines;
- ledgers written by the real `Budget`;
- the theme branch's row shape;
- the confirmation row's keys.

What they pin:
- The committed corpus, read two ways: each month's total dated from `started_at` equals the sum
  over the run files named for that month.
- UTC month edges, for a `+05:30` stamp and a `+0530` ledger opening.
- A `build_start` moves the draws after it into the next month.
- Unpriced rows are counted apart.
- A malformed row raises.
- A byte-identical ledger, or an earlier prefix copy, counts once; no ledger passed is NOT READ.
- A non-ledger is refused.
- An unreadable theme ref, and a graph-judge month before the recorded re-judge, are "NOT READ", not zero.
- A month outside 01–12 is refused.
- The total names every bucket it left out.
- The module imports no model client and no HTTP layer.

All of them fail at base, where the module is absent.

**BOUNDARY.**
- **Window:** the UTC calendar month 2026-11-01T00:00Z to 2026-11-30T23:59:59Z. The run was made on
  2026-11-13, so November is 13 days in.
- **Sources:**
  - pages: the 44 committed run files at `3d195fcd`, 16 of them with a line in November;
  - evals: the six budget ledgers in the coordinator's shared notes folder outside the repo. They
    are every ledger on this machine whose first line is an approval, and the only ledgers this run
    saw;
  - theme desk: `registry/llm_calls.jsonl` at `ea8fb4a6`, 476 rows of which 185 are November's;
  - graph judge: `judged_by` at `3d195fcd`.
- **Excluded:**
  - confirmations and validate-keys, which record no cost;
  - any budget ledger on another machine (B's included) and any not in that folder;
  - theme runs not pushed to the state branch;
  - re-judges before the latest, and every `graph-coverage` run;
  - vendor quotas.
- **Unit:** USD at list price (`vinci.config.LLM_PRICE_PER_MTOK`), as each writer recorded it.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The total is a floor, not the spend. The report names what it cannot see, but cannot size it.
- Each figure is the writer's own list price. A price change, or a writer that priced wrongly,
  flows through unchanged.
- Falsifier: an invoice for a month that exceeds the report's total by more than the named blind
  spots could explain.
