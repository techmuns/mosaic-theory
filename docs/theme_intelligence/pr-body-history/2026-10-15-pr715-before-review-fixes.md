Operator, 2026-10-15: "fix U3, U4, U26, U29". These are the money leads confirmed in `docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`. The full account is in `docs/records/2026-10-15-theme-intelligence-u3-u4-u26-u29.md`.

## What changes

- **U3: a resumed scan spends its limit once.** `scan --resume` restarted the guard at $0, so a run that had spent $38.50 of $40 could spend another $40, and its manifest then read 0 spent and 0 paid calls.
  - A resume now carries its earlier attempts' spend, calls and refusals (`SpendGuard.start_run(carried=)`).
  - The carried figure is the larger of the last summary and the ledger's paid rows, so an attempt that died without a summary still counts.
  - `--budget` on a resume is the run's total, and the resume warning states what is spent and the limit.
- **U4: every billed call is in the ledger.** A paid call that ended in an exception (a failed completeness pass, truncated reviews, a truncated enrichment) was counted by the guard but missing from `llm_calls`, so `cost_usd` was understated.
  - The guard now hears of every billed call (`sent`), and each ledger row matches one off (`recorded`).
  - `finish_run` writes the rest as `<tool>-unrecorded`, with why.
  - A failure with no usage reported is not shown as billed.
  - A truncated full extraction is recorded once, in the run that paid it (`ExtractionResult.truncated_now`). Without this, a compact retry resumed in a later run would have counted it twice once this fix landed.
- **U26: a document's own limit holds that document alone.** One report over its retry share was reported as "the run budget is exhausted", and every later candidate was queued.
  - A refusal now names the limit that refused it (`BudgetExceeded.scope`: run / document / retry / price).
  - Only the run's budget, or a refusal with no scope, stops a scan.
  - A held document is queued alone, the scan goes on, and the run is PARTIAL.
  - The enrichment pass does the same per thesis.
- **U29: one refusal, one id.** Two refusals of one thesis's review in one run shared an issue id with two payloads, raising StoreIntegrityError, which failed the article and the scan. The id now hashes the refusal it records.
  - The same defect sat on the review's other failure path: two different review failures of one thesis in one run, such as a truncation followed by a missing tool call. It is fixed and pinned the same way.

## Real-run verification

The review's own probe scripts, offline on scratch registries, $0, run on main c2872114 and on this branch:

```
U3   main    resumed: guard run_spent 0.0 limit 40.0 -> may spend another $ 40.0
             resumed: cost_usd 38.5 | spend record now 0.0 of 40.0 | paid_calls 0 | refusals []
     branch  resumed: guard run_spent 38.5 limit 40.0 -> may spend another $ 1.5
             resumed: cost_usd 38.5 | spend record now 38.5 of 40.0 | paid_calls 1 | refusals [1 kept]
U4   main    completeness: guard $0.70 | ledger [extract 0.35] | run.cost_usd 0.35
     branch  completeness: guard $0.70 | ledger [extract 0.35, completeness-unrecorded 0.35] | run.cost_usd 0.7
     main    3 truncated reviews: guard $0.45 | run.cost_usd 0.0 ; truncated enrichment: guard $0.15 | run.cost_usd 0.0
     branch  3 x review-unrecorded | run.cost_usd 0.45 ; enrichment-unrecorded | run.cost_usd 0.15
U26  main    processed 1 of 4 | queued all 4 | "the run budget is exhausted" with $25.00 of $40.00 spent | PARTIAL
     branch  processed 4 of 4 | queued the report alone | "held by its own limit" | PARTIAL
U29  main    article 2 RAISED: StoreIntegrityError verification_issues: id [...] already stored with a DIFFERENT payload
     branch  article 2: PROCESSED | thesis version 2   (control, the run's limit: one issue on both)
```

Real registries, measured over 147 registries, 208 distinct runs, 91 with a spend summary. The fixes act on new runs only; no stored record changes.
- 0 resumed runs, 0 guard/ledger gaps and 0 budget review refusals: U3, U4 and U29 are latent.
- 2 refusals, both of a document's retry share, both in ingest runs. U26 never fired on stored data.
- 4 `extract-truncated` rows; none is recorded in more than one run.

Checks:
- Pins: `tests/test_theme_intelligence_money.py`, 21 tests. Against main, 15 fail; the 6 that pass are the negatives and controls.
- Mutants: 30 of 30 killed, and the unmutated baseline passes.
- `ruff check .` and `mypy --strict vinci` are clean. The offline suite result is below.

Offline suite (`pytest -m "not network"`): **5,386 passed, 513 skipped, 37 deselected** (exit 0); record and STATE lints 720 passed.

## Also on this branch (docs only)

- **Operator decision, 2026-10-15:** TH-DEE87FCF51 SKIP → WATCH (the #714 effect) is ACCEPTED. It is recorded in STATE row 32 item (8). The live pilot has not been reassessed yet.
- **The figure-ledger OPEN item keeps only its open half.** A figure reference still reads as a figure (checked on this branch); #714 fixed the "2,358.5GVA" misread.
- This body before the change is kept in `docs/theme_intelligence/pr-body-history/2026-10-15-pr715-before-operator-decision.md`.

## Disposition

| Item | Status | Note |
|---|---|---|
| U3: a resume carries the run's spend | SHIPPED | latent in stored data (0 resumed runs) |
| U4: billed calls that ended in an exception are in the ledger | SHIPPED | includes a truncated extraction recorded once across a resume, found while fixing |
| U26: a document's own limit holds that document alone | SHIPPED | scan and enrichment pass; a held run is PARTIAL |
| U29: two refusals of one thesis in one run | SHIPPED | the sibling no-review path fixed too |

Accepted, stated in the record:
- Calls are matched to ledger rows by usage, so identical usage can swap labels; the count and cost stay right.
- A crashed attempt's call list is not rebuilt; only its spend is.
- A truncated attempt from a run that was killed outright is recorded nowhere.

🤖 Generated with [Claude Code](https://claude.com/claude-code)


