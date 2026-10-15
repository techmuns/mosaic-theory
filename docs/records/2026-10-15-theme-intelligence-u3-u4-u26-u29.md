---
id: 2026-10-15-theme-intelligence-u3-u4-u26-u29
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — the spend guard and the paid-call ledger: U3, U4, U26, U29 fixed

**WHAT.** Operator, 2026-10-15: "fix U3, U4, U26, U29". These are the money leads confirmed in
`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`.

| Lead | Defect | Fix |
|---|---|---|
| U3 | `scan --resume` restarted the guard at $0. A run that had spent $38.50 of $40 could spend another $40, and its manifest then read 0 spent, 0 paid calls, no refusals. | A resumed run carries its earlier attempts' spend, calls and refusals (`SpendGuard.start_run(carried=)`). The carried figure is the larger of the last summary and the ledger's paid rows, because an attempt that died never wrote its summary but its ledger rows stand. `--budget` on a resume is the run's TOTAL limit, and the resume warning says what is already spent and against which limit. |
| U4 | A paid call that ended in an exception was counted by the guard but never written to `llm_calls`, so the run's `cost_usd` was understated. Examples: a completeness pass with no tool call, three truncated reviews, a truncated enrichment. | Every call the model billed is reported to the guard (`sent`), and every ledger row matches one off (`recorded`). At `finish_run`, a billed call no path recorded is written as `<tool>-unrecorded`, with why (the exception, or "answer not used"), and the run says so. A failure with NO usage reported is not shown as billed: the guard still counts it at its bound, and no ledger row is owed. A truncated full extraction is recorded once, in the run that paid it: a later run that resumes its compact retry from the truncation marker no longer records the attempt again (`ExtractionResult.truncated_now`). Without this, the fix above would have counted it twice. |
| U26 | One report over its OWN limit was reported as "the run budget is exhausted", and every later candidate was queued. "Its own limit" means its document limit or that limit's retry / completeness share. | A refusal names the limit that refused it (`BudgetExceeded.scope`: run, document, retry, price). A scan stops and queues the rest only on the RUN's budget, or on a refusal with no scope. A document held by its own limit is queued alone and the scan goes on; the run is PARTIAL, because an in-window article was not analysed. The enrichment pass does the same per thesis. |
| U29 | Two refusals of one thesis's review in one run (two articles, two document limits) shared one issue id with two payloads. That raised StoreIntegrityError, which failed the article, and a scan with it. | The id hashes the refusal it records. Two statements get two issues; the same statement twice is still one. **The same defect on the review's other failure path** was found while pinning: two DIFFERENT review failures of one thesis in one run (a truncation, then a missing tool call; `LlmError` is a `RuntimeError`). It took the same fix. |

**WHY.** U3 and U4 understate what a run spent, and the guard exists to state that. U26 stops a
weekly scan on one long report. U29 fails a whole scan when two articles on one thesis run out of
budget.

**HOW VERIFIED.**
- **The verifier's reproductions, main (c2872114) against this branch:**
  - **U3:** after the resume, main allowed another $40.00, and the manifest read 0.0 spent, 0
    paid calls, no refusal. On this branch, $38.50 is carried and $1.50 is left; the manifest
    reads 38.5, 1 paid call, and keeps the first attempt's refusal.
  - **U4, completeness:** main's guard billed $0.70 against a run `cost_usd` of $0.35. On this
    branch it is $0.70 against $0.70: `extract` plus `completeness-unrecorded`.
  - **U4, review:** three truncated reviews read $0.45 against $0 on main. On this branch they
    are three `review-unrecorded` rows, $0.45.
  - **U4, enrichment:** a truncated enrichment read $0.15 against $0 on main. On this branch it
    is `enrichment-unrecorded`, $0.15.
  - **U26:** a report over its retry share, with $25 of the $40 run budget spent. Main processed
    1 of 4 candidates and queued all 4 under "the run budget is exhausted". This branch processes
    all 4, queues the report alone, and the run is PARTIAL.
  - **U29:** with a per-document limit, main raised StoreIntegrityError on the second article.
    On this branch both articles are PROCESSED. The control (the run's limit, the same statement
    twice) passes on both.
- **Real registries:**
  - No real run changes: the fixes act on new runs only, and nothing stored is rewritten.
  - Measured over 147 registries, 208 distinct runs, 91 of them with a spend summary:
    - **0 resumed runs**, so U3 is latent.
    - **0 runs whose guard paid calls differ from their ledger paid rows**, so U4 is latent: no
      billed call has ended in an exception in a run that wrote a summary.
    - **0 budget review refusals**, so U29 is latent.
    - **4 stored `extract-truncated` rows** among 1,530 distinct ledger rows, **none recorded in
      more than one run**. The resumed-compact double count has no stored instance.
    - **2 refusals, both a document's retry share.** Both came from ingest runs
      (`reask-check`, `reask-check2`, 2026-10-12), not scans, so U26 never fired on stored data.
      These two refusals are exactly the shape U26 misreads.
  - Nothing that reads ledger purposes counts the new rows as articles: the desk, QA and report
    match `purpose == "extract"` exactly.
- **Pins:** `tests/test_theme_intelligence_money.py`, 21 tests, each fix with its negative. Against
  main, 15 fail. The 6 that pass are what main already gets right:
  - the run's budget still stops a scan;
  - a scan with no hold is SUCCEEDED;
  - a call a path records itself is one row, not two;
  - the run's budget still stops enrichment;
  - the same refusal twice is one issue;
  - a compact retry in the same run records the truncation once.
- **Mutants: 30 of 30 killed** (`budget.py`, `pipeline.py`, `extract.py`). An unmutated baseline
  passes.
  - **U3, 7 mutants:** a resume starting at $0; calls, refusals or nothing carried; cached rows
    counted; the smaller of summary and ledger; no warning.
  - **U4, 9 mutants:** a failed call unreported; an unbilled failure reported; a used answer
    unreported; no match in the guard or in the pipeline; `finish_run` writing none; rows not
    named by tool; a resumed compact retry re-recording the truncation; a same-run truncation
    not marked as this run's.
  - **U26, 11 mutants:** no scope, or each scope read as the run's; the hold forgetting its scope;
    every hold stopping the scan, or none; a held run reading SUCCEEDED; every scan PARTIAL;
    enrichment always stopping, or never.
  - **U29, 3 mutants:** either id ignoring the detail; an id fresh per call.
- Ruff and `mypy --strict vinci` clean; the offline suite result is in the PR.

**BOUNDARY.** Code: main c2872114 against this branch, 2026-10-15. Reproductions: the review's own
probe scripts, offline, on scratch registries, $0. The registry counts (147 / 208 / 91 / 2) are
every `registry.db` under the `theme-intelligence` worktree's `data/theme_intelligence/` (backups
excluded):
- runs are distinct by run id;
- "with a spend summary" means any stored copy of the run carries one;
- refusals come from the runs' `spend.refusals`, classified by the limit each one names;
- "paid rows" are the run's non-cached `llm_calls` rows;
- ledger rows (1,530) are distinct by call id, and "recorded in more than one run" means the
  same article and the same usage under two run ids.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no model or SEC requests.
- **A call is matched to its ledger row by its usage.** Two billed calls with identical usage in
  one run can swap labels (`kind`, document) between the two. The count and the cost stay right.
- **A crashed attempt's guard call list is not rebuilt from the ledger.** Only its spend is
  carried, and the ledger keeps its rows.
- **A ledger row with an unknown cost counts $0 toward a resume's carried spend.** The guard
  counted that call at its bound while it ran, and that bound is not stored.
- **A truncated attempt from a run that died hard is recorded nowhere.** A killed process never
  reached `finish_run`, and the run that resumes from its marker no longer records it. This was
  chosen over double-counting the designed flow, which is: held by the budget, then resumed with
  a higher limit.
