---
id:
status: shipped
date: 2026-11-13
prs: [1061]
supersedes:
superseded-by:
---

# The monthly spend report: each paid bucket's list-price spend in a UTC month, read from the records that already exist, refusing nothing (operator 2026-11-13: "Report only"). November to 2026-11-13 12:08Z reads $363.23 over four buckets; confirmations and validate-keys record no cost, and the report says so

**WHAT.** Issue 1004, lane 4, part B.
- B's design (issuecomment-6847522000) proposed a monthly ledger per bucket that would refuse a
  run crossing its month's cap.
- A's operator-approved reply put the cap values with the operator.
- The operator then ruled, relayed by B (issuecomment-6847993179): *"Report only"*. The ledger
  reports and refuses nothing. Per-run control is unchanged: every paid run still spends only
  under the operator's approved cap.

`python -m vinci.spend --month YYYY-MM [--evals-ledger FILE …] [--evals-root DIR …]
[--theme-ref REF] [--json]` (`vinci/spend.py`) reads each bucket from the record it already has.
It adds no write path. The evals roots default to the folders in `VINCI_LEDGER_ROOTS`. The report
prints every root it searched and every ledger it read, so it never claims a wider search.

| bucket | read from | what it cannot see |
|---|---|---|
| pages | `data/snapshots/assembly_runs/*.jsonl` (committed; the repo's own `data/`, wherever the command runs): one line per name a build attempted, with refused and failed lines included. `usd` is the list price of its metered calls. Each line is dated by its own `started_at`. No run file at all is NOT READ. | a build whose run file was not committed |
| confirmations | `data/snapshots/proposal_confirmations.jsonl`: rows counted by `drawn_at` | **every cost.** A row carries no `usd` or usage, and a confirmation refused after its draws writes no row. The bucket is NOT RECORDED, and no file is committed yet. |
| evals | the budget ledgers (`vinci.evals.replay.Budget`), which are outside the repo by design. Only the ledgers passed in, or found under the roots searched, are read, and each root and ledger is printed; with none found the bucket is NOT READ, never $0. The rows column counts every ledger row; the note says how many are draws. A draw row has no time of its own, so it is dated by the latest stamp above it: the approval's `opened_at`, or a `build_start`'s `started_at`. A copy that is another ledger's bytes, or an earlier prefix of them, counts once. | a ledger not passed in, or one kept on another machine; and the month of a `run-compare` or `judge` draw, which writes no stamp and so can fall in an earlier month |
| theme desk | `registry/llm_calls.jsonl` on the `theme-intelligence-state` branch, read with `git show`. The weekly CI run and a local `state push` write it, so **CI's spend is visible here.** Rows have `cost_usd` and `at`; a cache hit costs $0, and a live call with no cost is unpriced. | a local run not yet pushed to the branch |
| graph judge | `judged_by` in the committed `data/graph_coverage.json`. A month before the recorded re-judge is NOT READ, and so is a map with no `judged_by` (`graph-coverage --json` writes one). | any earlier re-judge, because each run overwrites the last; a re-judge that STOPPED and wrote nothing; and any `graph-coverage` run, which records no cost |
| validate-keys | nothing | **every run.** A one-token billable ping per CI run is recorded nowhere: NOT RECORDED |

**How the report reads its records.**
- Months are UTC calendar months.
- Every figure is the list price the writer recorded.
- A missing figure is `None`, never zero:
  - an unpriced row is counted apart, and its bucket's figure and the total then print as a
    floor ("≥", "at least") naming the rows not in them;
  - a bucket with no record, or one not read, is named in the total as "NOT included".
- Each bucket prints what its `rows` column counts, since the units differ.
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

**HOW VERIFIED.** The real run, re-made after the independent review (round 1). The code is
this PR's head on `4b8f7426`, as of **2026-11-13 12:08:25Z**, with `origin/theme-intelligence-state`
at `ea8fb4a6`. Two ledger roots were searched: the coordinator's shared notes folder and the panel
exports folder. Both are outside the repo, so they are named here by role, while the run itself
printed their paths.

```
spend report, 2026-11 (UTC calendar month, list price) — reports, refuses nothing
bucket                usd   rows  source
pages              $66.98     16  data/snapshots/assembly_runs/*.jsonl
confirmations           —      0  data/snapshots/proposal_confirmations.jsonl   (NOT RECORDED)
evals             $269.91    648  7 of 7 ledgers read; 594 of the 648 rows are draws
                                  read: <notes>/synthesis-eval-driver-facts/ledger-driver-facts.jsonl — 59 draw(s), $27.50
                                  read: <notes>/synthesis-eval-fix3b/ledger-fix3b.jsonl — 60 draw(s), $30.72
                                  read: <notes>/synthesis-eval-ra-d2/ledger-ra-d2.jsonl — 60 draw(s), $30.28
                                  read: <notes>/synthesis-eval-ra-d2-d4/ledger-ra-d2-d4.jsonl — 60 draw(s), $30.54
                                  read: <notes>/synthesis-eval-ra-d4/ledger-ra-d4.jsonl — 60 draw(s), $27.32
                                  read: <notes>/vote-rule-independence/ledger.jsonl — 240 draw(s), $96.70
                                  read: <panel-exports>/pr1027-run/ledger-e2-remainder.jsonl — 55 draw(s), $26.84
theme desk         $23.73    185  origin/theme-intelligence-state@ea8fb4a6:registry/llm_calls.jsonl
graph judge         $2.61      1  data/graph_coverage.json (the re-judge of 2026-11-09)
validate-keys           —      0  none   (NOT RECORDED)
total of the 4 bucket(s) read: $363.23 — NOT included: confirmations, validate-keys
```

**E2's ledger was still being written.** It is the six-page panel check for #1027, opened
2026-11-13 15:23:53 +05:30 under a $35.28 cap. At the as-of time it held 56 rows: one zero-cost
registration row and 55 draws, $26.8372. Its last append was at 12:07:07Z, 78 seconds before the
run, so a later run will read more. #953's run folder did not exist yet.

**An earlier boundary in this record was false.** The first version said the six ledgers in the
notes folder were "every ledger on this machine whose first line is an approval". They were not:
E2's paid ledger sat in the panel exports folder, which that run never searched. The report now
prints the roots it searched and every ledger it read, and makes no claim beyond them.

**Each figure was checked a second way, apart from the module:**
- **pages:** the 16 lines of the 16 run files named `2026-11-*` sum to $66.9843, with 0 unpriced.
- **evals:** the six notes-folder ledgers sum to $243.0683:
  - fix 3b, $30.724;
  - driver facts, $27.5048;
  - RA-D2 and RA-D4, $30.5374;
  - RA-D2, $30.2778;
  - RA-D4, $27.3239;
  - the vote rule's independence check, $96.7004.

  E2's ledger adds $26.8372, for a total of $269.9055. The six notes-folder ledgers hold 539
  draws and 53 zero-cost rows; E2's holds 55 and 1.
- **theme desk:** 163 live calls, $23.72712; 22 cached, $0.
- **graph judge:** the committed `judged_by` reads `cost_usd` 2.6083 on 2026-11-09.

October reads $136.49 over three buckets: pages, evals ($0.00, since no ledger read carries an
October row) and the theme desk. Its graph judge is NOT READ, because the 2026-11-09 re-judge
overwrote any earlier one.

**The tests** (`tests/test_spend_report.py`, 26 cases) are built from real records:
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
- **Round 1, added after the independent review:**
  - pages with no run file is NOT READ;
  - the command reads the repo's own `data/` from any folder;
  - a map with no `judged_by` is NOT READ;
  - `report()` returns all six buckets, by name;
  - every root searched and every ledger read is printed, with `VINCI_LEDGER_ROOTS` as the
    default;
  - draws are counted apart from zero-cost rows;
  - each bucket says what its rows count, and the total says it is not a floor.
- **Round 2, Codex P1 on `40c33550`:** a bucket with unpriced rows never yields a definite total.
  Its figure prints "≥" and the total "at least", naming the unpriced rows. The pin fails on
  `bff7ef27`.

All of them fail at base, where the module is absent. Six of the seven round-1 pins also fail on
this PR's first head, `09913271`. The seventh, the all-six-buckets pin, reds when `theme_desk` is
dropped from `report()`.

**BOUNDARY.**
- **Window:** the UTC calendar month from 2026-11-01T00:00Z, read as of 2026-11-13 12:08:25Z,
  13 days in.
- **Sources:**
  - pages: the 44 committed run files at `4b8f7426`, 16 of them with a line in November;
  - evals: the seven budget ledgers found under the two roots searched, the coordinator's shared
    notes folder and the panel exports folder. They are the only ledgers this run saw. Every one
    of them is printed by the run;
  - theme desk: `registry/llm_calls.jsonl` at `ea8fb4a6`, 476 rows, 185 of them November's;
  - graph judge: `judged_by` at `4b8f7426`.
- **Excluded:**
  - confirmations and validate-keys, which record no cost;
  - any budget ledger outside the two roots searched, B's machine included;
  - E2's draws after 12:07:07Z;
  - theme runs not pushed to the state branch;
  - re-judges before the latest, and every `graph-coverage` run;
  - vendor quotas.
- **Unit:** USD at list price (`vinci.config.LLM_PRICE_PER_MTOK`), as each writer recorded it.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The total is neither a floor nor exact for one month. It leaves out what each bucket cannot
  see, which the report names but cannot size. A `run-compare` or `judge` draw made in a later
  month can also be dated to an earlier one. Summed over every month, it is a floor.
- Each figure is the writer's own list price. A price change, or a writer that priced wrongly,
  flows through unchanged.
- Falsifier: an invoice for a month that exceeds the report's total by more than the named blind
  spots could explain.
