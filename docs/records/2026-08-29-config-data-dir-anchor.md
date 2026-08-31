---
id:
status: shipped
date: 2026-08-29
prs: [526]
supersedes:
superseded-by:
---

# Scripts run from the repo root — the CWD convention is honoured, not fought

**THE BUG.** Running a script from `scripts/` built a second, empty tree at `scripts/data/` and
quietly refilled it: 4.6MB of SEC responses re-fetched into a cache nothing else would ever read.

**THE FIRST FIX WAS WRONG, AND THE REVIEW WAS RIGHT TO KILL IT.** It anchored `Config.data_dir` to
`Path(__file__).resolve().parents[1]`. But `data_dir` is one of ~28 roots that resolve against the
CWD — `vinci/scenarios.py`, `vinci/monitor.py`, `vinci/dossier/refresh.py`, and the
`Path("data/…")` literals in `cli.py` — and that uniformity is deliberate: four test modules use
`monkeypatch.chdir` for isolation because of it.

Moving one root and leaving 27 is **worse than either endpoint**. `vinci dossier IT` from
`scripts/` would read the underwrite record from `scripts/scenarios` — absent, and absent means
"not underwritten" BY DESIGN, per `_read_scenario_card`'s own docstring — while writing to the
now-absolute **committed** `data/dossiers/IT/`. A tracked artifact silently loses its thesis and the
run reports success. The old behaviour wrote a throwaway `scripts/data/dossiers` and left the
committed file alone. Half-right converted "fails uniformly from the wrong CWD" into "succeeds
except one silent read, into the tree that is under version control".

`parents[1]` was also wrong for the packaged install: the project declares a hatchling wheel and a
`vinci` console script, so under `pip install .` the anchor lands in site-packages.

**THE FIX THAT HOLDS.** `os.chdir(ROOT)` in each script's `__main__`. It corrects **all ~28 roots at
once**, not one — the config anchor never fixed `vinci themes` writing `scripts/data/scan_history/`,
because that path is a bare literal. In `__main__` only: `tests/test_cohort_pool.py` imports
`build_cohort_pool` to exercise `select_run`, and an import-time chdir would move the whole suite's
CWD out from under the four modules that isolate with it.

**TWELVE SCRIPTS, NOT THREE.** The three from #515 plus nine pre-existing instances of the same bug.
Three of those were found by the new invariant test rather than by grep — `fetch_benchmark_iwm.py`
and `price_state_falsifier.py` reach the data tree through `PolygonEodClient.from_config()` without
ever naming `get_config`, and `backfill_entity_master_sic.py` landed on main (#525) DURING this
branch and was caught on the rebase. Fixing three and leaving nine would have repeated, in
miniature, exactly what the review faulted.

**AND ONE NEAR-MISS WORTH RECORDING.** The revert was first done with `git checkout main -- \
 vinci/config.py`, but the local `main` ref was from session start. That restored an OLD config.py
and silently reverted the 2026-08-29 operator ruling bumping `graph_llm_model` to `claude-opus-5`.
The check that should have caught it — `git diff main -- vinci/config.py` — was circular, comparing
against the same stale ref. Diff against `origin/main`, never a local branch ref that has not been
fetched.

**VERIFIED.** The gate re-run from `scripts/` creates no `scripts/data`, no `scripts/scenarios`, and
completes at 0.0s/name — a cache HIT where it previously missed and re-fetched. `vinci/config.py`
and `tests/test_config.py` are byte-identical to main. 2 mutations caught: a data-reading script
dropping its chdir, and a chdir moved inside an importable function.

**WHAT IS NOT FIXED.** The ~28 CWD-relative roots stay CWD-relative. That is the repo's convention
and the tests depend on it; this record exists so the next attempt to "just anchor `data_dir`" finds
the reason it was tried and reverted.
