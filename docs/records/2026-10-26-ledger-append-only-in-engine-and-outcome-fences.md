---
id: 2026-10-26-ledger-append-only-in-engine-and-outcome-fences
status: shipped
date: 2026-10-26
prs: [800]
supersedes:
superseded-by:
---

# The decision ledger is append-only in the engine, and the screen, cohort, trigger and scenario modules cannot reach forward returns by import

**WHAT.** The 2026-10-22 agentic-engineering report named two guardrail gaps to close before any
agent loop is allowed. Both are closed here.

1. **`decision_ledger` refuses every rewrite in SQLite itself** (`vinci/store/schema.py`). Three
   triggers:
   - `BEFORE UPDATE` and `BEFORE DELETE` abort. This is the pair the theme-intelligence registry
     installs (`vinci/theme_intelligence/store.py`).
   - `decision_ledger_no_rewrite` (`BEFORE INSERT`) aborts when the entry_id already holds a
     different row. `INSERT OR REPLACE` deletes a conflicting row without firing delete
     triggers while `recursive_triggers` is off, so without this trigger the pair can be
     bypassed by the statement `rebuild_from_snapshots` runs on every weekly screen and monthly
     score. An identical re-seed is still a no-op.

   `IF NOT EXISTS` makes `Store.init_schema` the migration: an operator's existing DB gains the
   triggers the next time it is opened, rows intact.
2. **Outcome-import fences on the four modules that had none** (`tests/test_outcome_import_fences.py`):
   `vinci/screens/`, `vinci/cohort.py`, `vinci/triggers.py`, `vinci/scenarios.py`. Each may not
   import `vinci.scoring`, `vinci.ledger` or `vinci.monitor`.
   - Direct imports are checked, and so is the whole transitive closure.
   - `vinci.schemas.ledger` is banned on direct imports only. `vinci/schemas/__init__.py`
     re-exports it, so any `vinci.schemas.*` import loads it.
   - The Store's two ledger readers (`iter_ledger`, `get_ledger_entry`) are banned by attribute
     name, and so is `decision_ledger` named in code (raw SQL or the JSONL path; docstrings
     excepted). The screen imports `Store` legitimately, for prices and candidates.
   - Every name `vinci/schemas/ledger.py` defines is banned under the package too, because
     `from vinci.schemas import LedgerEntry` reads as `vinci.schemas.LedgerEntry`.
   - The import parser sees `from vinci import scoring`, relative imports, imports inside
     functions, and `import_module` / `__import__` called with a string literal.
3. **The monitor gets the reverse fence.** It cannot reach `vinci.ledger` or `vinci.store`, the
   ledger's write paths.

**WHY — AND TWO THINGS THE BRIEF HAD WRONG.**
- *Absence verified before it was asserted.* Searched:
  - `CREATE TRIGGER|BEFORE (UPDATE|DELETE)|RAISE(ABORT` over `vinci/`;
  - a second vocabulary: `set_authorizer|query_only|immutable|no_update|no_delete|tamper`;
  - pickaxe `git log --all -S"CREATE TRIGGER"` and `-S"RAISE(ABORT"`. Every hit is a
    theme-intelligence commit (e4b2c23d … 409fcc41);
  - `git log --all -i --grep=append-only`.

  The fund ledger was append-only by convention: no UPDATE or DELETE on it exists in `vinci/`,
  `scripts/` or `tests/`.
- *`tests/test_scenarios.py` has NO import fence.* The brief listed it among the five fenced
  files. Searched: `ast.parse`/`ast.Import` over every test naming `scenarios.py`, and
  `git log -i --grep` for `no-forward-returns|import guard|reads no forward`. The fences that do
  exist are in `test_rank.py`, `test_themes.py`, `test_dossier.py` and `test_sleeves.py`, plus the
  theme-intelligence isolation tests. So `vinci/scenarios.py` is fenced here.
- *The monitor cannot carry a "reads no returns" fence.* Its own docstring says it computes every
  leg's excess return, the interim BUY−AVOID spread and the realized P&L. It is part of the outcome
  layer, which no earlier fence names; they forbid only `vinci.scoring` and `vinci.ledger`. So the
  monitor joins the forbidden set, and its own fence is the write fence its docstring promises.

**HOW VERIFIED.**
- **Real DB copy.** A copy of a real working DB: `sweet-torvalds-b0afb6/data/vinci.db`, 401 MB,
  7 ledger rows, 7/7 identical to the committed `decision_ledger.jsonl`. It was copied with
  SQLite's backup API and the source was opened read-only.
  - [1] Opening it with the new `Store` installed the three triggers, rows unchanged.
  - [2] A full `rebuild_from_snapshots` from a copy of the committed snapshots succeeded, with
    `decision_ledger: 7` and the rows unchanged.
  - [3] The subset seed (`BUILD_UNIVERSE_SEED_TABLES`) succeeded.
  - [4] On the real `V-GOOGL` row, UPDATE, DELETE and an `INSERT OR REPLACE` with a doubled entry
    price were all refused. The rows were unchanged afterwards.
  - [5] `log_verdict` on a real candidate (AAOI-screen2-20261016, BUY @ 75.57 as of 2026-10-16)
    appended, with the machine proposal sealed (`proposal=BUY`, `disposition=confirmed`).
  - [6] `close_position` appended its close row.
  - [7] `export_snapshots(tables=["decision_ledger"])` went 7 → 9 and passed the no-row-drop
    guard.
  - [8] A re-seed onto the DB that wrote those rows succeeded.
  - [9] A fresh DB rebuilt twice holds 9 rows.
  - [10] Re-opening the migrated copy works.

  `vinci/seal.py` (the rationale seal) writes `scenarios/_seal.json` and never touches SQLite.
  Nothing in the repo was written.
- **Mutation, 15 of 15 killed.**
  - Six trigger mutants:
    - drop `no_update`;
    - drop `no_delete`;
    - drop `no_rewrite`, leaving the theme-intelligence pair alone;
    - `no_rewrite` compares the payload only;
    - `no_rewrite` refuses an identical re-seed;
    - the triggers lose `IF NOT EXISTS`.

    The last one SURVIVED the first pin set: no pin re-opened a DB that already had the
    triggers. A later-open assertion was added, and the mutant is now killed.
  - Nine injections into real production modules:
    - `screen2.py` imports `vinci.scoring`;
    - `cohort.py` imports the monitor lazily;
    - `triggers.py` has `from vinci import ledger`;
    - `prose_lint.py`, which is unfenced but sits under `scenarios`, imports the monitor (only the
      transitive fence catches this);
    - `screens/run.py` calls `store.iter_ledger()`;
    - `monitor.py` imports `Store` lazily;
    - `scenarios.py` calls `importlib.import_module('vinci.scoring.harness')`;
    - `screen2.py` has `from vinci.schemas import LedgerEntry` (the package re-export);
    - `screens/run.py` runs `SELECT payload FROM decision_ledger` on the Store's connection.

    The last two came from this build's `/code-review high`, which found both bypasses. Both
    were fenced, and both mutants were then killed.
  - **Round 1 (Codex P2 on #800).** A PACKAGE import followed by an attribute got past the fence:
    `from vinci import schemas` then `schemas.LedgerEntry`, or `import vinci.schemas.candidate`
    then `vinci.schemas.ledger.LedgerEntry`. The import names only the package. The parser now
    resolves attribute chains through any name an import bound. Five parser pins fail on the PR
    head. As mutants in `screens/screen2.py` and `cohort.py`, both shapes SURVIVE the PR-head fence
    and are KILLED by the fixed one.
- **Corpus before synthetic.**
  - `test_the_committed_ledger_cannot_be_rewritten_once_loaded` loads the LIVE committed ledger and
    attacks every real row three ways.
  - The walker is shown to find the outcome edges the live tree really has: the CLI → scoring /
    ledger / monitor, `dossier.mechanical` → monitor, and the screen → store.
- **Runtime agrees with the AST.** Each module was imported in a fresh interpreter, and
  `sys.modules` was then checked for scoring/ledger/monitor/store.
  - `vinci.cohort`, `vinci.triggers`, `vinci.scenarios`, `vinci.rank`: none.
  - `vinci.screens`: the store only.
  - `vinci.monitor`: itself only.
  - `vinci.dossier.mechanical`: the monitor and the store.
- **A near-miss in this build's own findings.** The walker counts `if TYPE_CHECKING:` imports,
  which never execute. A first draft of this record therefore reported that the ranker crosses its
  own `vinci.store` fence through `vinci.screens`. That import is TYPE_CHECKING-only, and
  `import vinci.rank` loads no store, so the claim was withdrawn before review. The fence still
  counts such imports, which errs toward red and never toward a false green.
- **Ledger history.** All 8 commits that touched `data/snapshots/decision_ledger.jsonl` took it
  0 → 7 rows. No row was ever dropped or rewritten. That was the convention holding, not an
  enforcement.

**BOUNDARY.**
- *Ledger counts:* `data/snapshots/decision_ledger.jsonl` at `main` 545403de (2026-10-26), all rows,
  unit = ledger rows (decisions and closes alike).
- *Working DBs compared read-only on 2026-10-26.* All are git-ignored `data/vinci.db` files:
  - the primary checkout: 0 ledger rows;
  - `sweet-torvalds-b0afb6`: 7, identical;
  - `research-alpha-audit-bcba59`: 7, identical;
  - `analyze-zip-files-quality-9022ad`: 0.

  None carried a trigger.
- *Mutants:* run with `PYTHONDONTWRITEBYTECODE=1`, `__pycache__` cleared before and after each.
  - The 6 trigger mutants ran against the 5 ledger pins in `tests/test_store.py`.
  - The 9 fence mutants ran against the 31 tests in `tests/test_outcome_import_fences.py`.
- *Import closures:* computed over `vinci/**/*.py` at this branch's head.

**OPEN — found here, not fixed here (hold scope; not a §5.0 row, §5.0 is at its cap).**
1. *The older fences cannot see `from vinci import scoring`.* They read `node.module`, which is
   `vinci`. Demonstrated by adding that line to `rank/ranker.py`, `themes/gates.py` and
   `dossier/verdict.py`: each package's fence stayed GREEN. The proposal mapping in `verdict.py` is
   the code that must never be outcome-tuned. `test_sleeves.py` reads the same field; it was not
   run.
2. *The older fences are direct-only.* A forbidden import added to any module they do not scan,
   but that their package imports, leaves them green. Mutant F4 shows the shape on `scenarios`.
3. *The dossier imports the monitor* (`dossier/mechanical.py`, `dossier/assemble.py`) for the
   cap-band policy (`benchmark_for_cap`, `BENCHMARK_SMALL`). The dossier therefore loads the module
   that computes the spread. Moving the policy out of `monitor.py` would let the dossier be fenced
   from it.
4. *Reading outcome data by FILE PATH is only partly fenced.* A literal `decision_ledger` is
   caught. A path built from parts, `data/monitor/*.json` and `scoring_report.*` are not. None of
   the four fenced modules does so today (grep, 2026-10-26).
5. *A committed ledger row's CONTENT can be edited by hand undetected.* `_assert_no_row_drop`
   compares primary keys only. A fresh DB loads the edited row, and the triggers only stop a
   working DB that already holds the old row (it now fails loud on the re-seed). A CI check that
   every row on the merge base is byte-identical on the PR would close it.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *Not a defence against a deliberate `DROP TRIGGER`.* The same is true of the theme-intelligence
  registry and of `vinci/seal.py`. The committed JSONL's git history is the backstop for a
  determined rewrite.
- *Behaviour change.* A working DB whose ledger row disagrees with the committed JSONL now FAILS on
  re-seed, where the JSONL used to win silently. That disagreement means one of the two was
  rewritten. The DB is a rebuildable cache, so the remedy is to find which one, move the DB aside
  and rebuild.
- *`recursive_triggers`.* Enabling it would make REPLACE fire the delete trigger and refuse even an
  identical re-seed. `Store` never enables it.
