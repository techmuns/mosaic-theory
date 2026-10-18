---
id: 2026-10-18-stale-refresh-scripts-retired
status: recorded
date: 2026-10-18
prs: [746]
supersedes:
superseded-by:
---

# Two stale refresh scripts retired, and the suite now checks every script's library calls

**WHAT.** The #745 run found `scripts/refresh_stock_performance.py` calling
`mechanical._stock_performance` without its required `bench=` argument. Operator, 2026-10-18: "is
this a critical issue? diagnose properly and if yes then we should fix it".

**THE DIAGNOSIS.**
- **Broken since 2026-07-21.** `fefadc5a` made `bench` a required keyword-only argument. The script
  was edited twice afterwards (#526 on 2026-08-31, #702 on 2026-10-10) and never run.
- **Nothing runs it.** No workflow, test, CLI command or runbook step calls it; it is mentioned
  only in old records and its own usage lines.
- **It fails loud and early.** Reproduced on a temporary copy of GOOGL's page with a clone of the
  store, calling the script's `main` directly (its `__main__` changes to the repo root):
  `TypeError: _stock_performance() missing 1 required keyword-only argument: 'bench'`, raised
  before any write. The copy was untouched.
- **The obvious repair is the danger.** The 2026-10-07 record names this script as a way to fix
  STATE row 32 (7). Patched with the missing argument and run on a temporary copy of TGT, it
  exited 0 and:
  - wrote the 52-week chart's benchmark return 13.7% → 16.6% while the prose still read "vs SPY
    +13.7%". That is the contradiction `refresh_dossier`'s citation guards refuse, and TGT, ORKA
    and PARR (three of the seven pages still open) quote exactly this figure;
  - added no `layer_refreshes` entry, so the page did not record that it changed;
  - never mirrored to `frontend/dossiers/`, so the served page stayed old;
  - printed "vs IWM" for an SPY benchmark.
- **A second script, the same class.** `mypy scripts/` (the gate type-checks only `vinci/`) found
  one more stale call: `scripts/refresh_concentration.py` calls `mechanical._concentration` without
  `edgar`, `http` and `cik`. It is the same kind of path: it writes outside `refresh_dossier`, with
  no guard, no refresh entry and no mirror, and nothing runs it. The other `mypy scripts/` findings
  are annotation-level in one-off analysis scripts, not stale library calls.
- **Verdict: not critical, worth fixing.** No page was harmed, and none could be while the scripts
  crash. But they sat beside an open item as documented tools, and their natural repair silently
  makes the defect the write path exists to refuse.

**THE FIX.**
- **Both scripts deleted**, not repaired. Their jobs are covered by the guarded path:
  - the chart: `refresh_dossier(..., transform=benchmark_figures_transform(...))` (#745);
  - concentration: a re-assembly, which the script's own docstring named as reproducing it. No
    transform was written for concentration, since nothing needs one now.
- **`tests/test_scripts_call_current_signatures.py`** runs mypy over `scripts/` and fails on any
  `call-arg` finding: a call that no longer fits the library function it calls. It is narrow on
  purpose; the scripts are not otherwise typed, and a full type-check would bury this one signal.

**HOW VERIFIED.**
- Before the deletion, the check failed and named exactly the two scripts' stale calls (line 48
  and line 45), and nothing else in `scripts/`.
- After the deletion it passes.
- A positive pin rebuilds the retired script's own broken call in a temporary file and must see it
  named ("Missing named argument "bench""). It takes about 6 seconds.
- **One existing pin moved with it.** `test_every_dossier_writer_saves_through_the_one_write` counts
  page writers as proof its scan finds something, with a floor of 9. It counted 10, and the two lost
  are exactly the retired scripts' `main` functions (checked against main's files). The floor is now
  8, with the reason beside it; every remaining writer still saves through the one write.
- **Suite.** ruff and `mypy --strict` clean; `pytest -m "not network"` with the store moved aside:
  5877 passed, 512 skipped.

## CODE REVIEW FIX (code review of #745 and #746, 2026-10-18)

One finding on this PR, fixed: **the check missed the commonest way a script goes stale**, an
import of a renamed or removed library name. It now also fails on mypy's `attr-defined`,
`import-not-found` and `import-untyped` findings that name a `vinci` module. mypy reports a removed
`vinci` SUBMODULE as `import-untyped`, because the package itself resolves as installed; that was
measured, not assumed, and it is why `--ignore-missing-imports` is no longer passed (it would let a
removed module read as an untyped one).
- **On `scripts/` today the wider check finds nothing.** Every import resolves, and the one
  `attr-defined` finding is a typing note in an analysis script, not a `vinci` module.
- **Pins.** A removed function and a removed module are both named. NEGATIVE: a third-party
  package without stubs is not.
- **Mutation.** 4 mutants, all killed: `attr-defined` dropped, `import-untyped` dropped, the
  `vinci` filter dropped, `--ignore-missing-imports` restored.
- **Suite.** 5878 passed, 512 skipped.

**BOUNDARY.** 2026-10-18 on main 57517b76; population: the 16 files in `scripts/` before the
deletion, 14 after.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A future one-field refresh is written as a `refresh_dossier` transform, under its guards, not as
  a script.
- The other `mypy scripts/` findings (annotation-level) are not addressed here.
