---
id:
status: shipped
date: 2026-11-18
prs: [1113]
supersedes:
superseded-by:
---

# The forward-return fence now covers every decision module. The ranker, the sleeve registry, the proposal mapping, the universe gate and the edge-basis gate join the transitive fence, and the whole dossier is barred from the scoring harness and the ledger. The ledger half of P2-13 needed no build: its triggers have been on main since #800, and the primary's working DB already carries them ($0)

**WHAT.**
- `tests/test_outcome_import_fences.py` fences five more modules, the same way it fences the screen,
  the cohort, the triggers and the scenarios (#800): `vinci.rank`, `vinci.sleeves`,
  `vinci.dossier.verdict`, `vinci.universe` and `vinci.edge_basis`. Each is checked three ways:
  - direct imports;
  - every module it reaches;
  - the Store's ledger readers, and `decision_ledger` named in code.
- A new test walks all 49 files of `vinci/dossier/` and refuses any path to `vinci.scoring`
  (screen baseline included) or `vinci.ledger`. The dossier may still reach the monitor, the one
  outcome module it is allowed: `vinci.dossier.mechanical` takes the cap-band policy from it, and
  the walker test already names that edge. The Store-reader check (`iter_ledger`,
  `get_ledger_entry`, `decision_ledger` named in code) now runs over the whole dossier too: a
  ledger row read through the Store is the ledger (review round 0; a reader planted in verdict.py
  turned it red for the dossier and for verdict.py).
- One named allowance: `vinci/dossier/verdict.py` may import `Verdict` from `vinci.schemas.ledger`.
  `Verdict` is the label set its proposals are written in, an enum with no price on it. Any other
  name from that module is refused in verdict.py. The same import from any other fenced module is
  refused. A pin fails if verdict.py stops importing `Verdict`, so the allowance cannot outlive its
  use.
- A planted import is refused on a copy of the real tree (`vinci/*.py` and the test file, copied
  to a temp dir and loaded there). For each of the five modules, the copy passes as copied. Then
  `from vinci import scoring` is appended to the module's own file, and both of its checks refuse
  it. For the transitive half, the same import is planted in `vinci/schemas/cohort.py`, which no
  fence names. The ranker's direct check stays green, and the walk names the path, both through the
  ranker and through the dossier.

**WHY.**
- The 2026-11-13 engineering report listed P2-13 as open. It was not. #800, merged 2026-10-26,
  closed both halves the 2026-10-22 report had named:
  - the fence on screens, cohort, triggers and scenarios;
  - the monitor's reverse fence. The monitor computes returns, so it cannot be fenced from them;
    instead it is barred from reaching a ledger write path;
  - three ledger triggers.
- #800 left one gap open, recorded in its STATE.md claim. The older fences in `tests/test_rank.py`,
  `tests/test_dossier.py` and `tests/test_sleeves.py` read `node.module` and stop at the file. So
  `from vinci import scoring` passes them (`node.module` is `vinci`), and so does an outcome import
  one module away. The universe gate and the edge-basis gate had no fence at all.
- Each of these five modules sets a weight, a band, a vocabulary, a requirement or the proposal
  itself. §7 says no such parameter reads forward returns.

**HOW VERIFIED.**
- **Corpus first** (main `322c6caa`): the transitive walk was run over every top-level `vinci`
  module and package before any of the five joined the fence.
  - The four already fenced reach no outcome module.
  - rank (4 files), sleeves (1), dossier/verdict (1), universe (1) and edge_basis (1) reach none.
  - The one direct hit is verdict.py's `Verdict` import, which became the allowance.
  - In the dossier, 8 of 49 files reach `vinci.monitor` (through `assemble` or `mechanical`). None
    reaches the scoring harness or the ledger.
- **Mutation** (6 mutants, each run on the whole test file, all killed):
  1. the five modules dropped from `FENCED`: 6 red (the five copy pins, the scan pin);
  2. the walk made direct-only: 2 red (the one-module-away pin, the walker pin);
  3. the allowance widened to all of `vinci.schemas.ledger`: 1 red (the allowance pin);
  4. `from vinci import X` made unseen, the older fences' blind spot: 8 red;
  5. the dossier barrier emptied: 1 red (the one-module-away pin);
  6. the allowance removed: 3 red, on the live tree. This is the live-corpus control: the extended
     ban finds the one real direct import main has.
- `tests/test_outcome_import_fences.py`: 69 passed, up from 45 at `322c6caa`.
- **The ledger half: nothing to build**, re-checked on main `322c6caa`.
  - `vinci/store/schema.py` holds `decision_ledger_no_update`, `_no_delete` and `_no_rewrite`.
    `tests/test_store.py` pins each case this brief named: an INSERT lands, an UPDATE and a DELETE
    are refused, and an existing DB gains the triggers when opened.
  - Mutation of the DDL. Dropping no_update, no_delete, or all three turns the refusal pin and the
    migration pin red, while the INSERT pin stays green.
  - Every writer was read again. `Store.append_ledger` INSERTs. `rebuild_from_snapshots` runs
    `INSERT OR REPLACE`, and an identical re-seed is a no-op under `_no_rewrite`. The weekly run
    and run-monthly's scoring both re-seed this way (`vinci/orchestrator.py`). The ledger package
    writes only through `append_ledger`, and its corrections, voids and closes are new rows. The
    scoring harness only reads (`iter_ledger`). No UPDATE or DELETE names the table.
  - The primary checkout's `data/vinci.db`, read-only (`mode=ro`, file dated 2026-10-28) carries
    all three triggers and holds 0 ledger rows. Re-seeding the 10 rows committed on main is
    therefore a pure append, so VRRM's 2026-12-16 score cannot meet a trigger refusal.

**BOUNDARY.**
- Fence counts: main `322c6caa`, 2026-11-18. Population: the 220 `.py` files under `vinci/`, by
  import, static and literal-dynamic, as #800's docstring defines.
- File counts per module are `rglob("*.py")` under the package, or the one module file.
- Mutation counts: one run per mutant over `tests/test_outcome_import_fences.py` alone.
- Ledger counts: rows of `decision_ledger` in the DB, and lines of
  `data/snapshots/decision_ledger.jsonl` at `322c6caa`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The allowance is a judgment, flagged for review.** The strict reading of "a real import exists
  today → STOP" would leave verdict.py out of the direct ban altogether. The allowance is narrower
  than that: one name in one module, pinned both ways.
- **Still not caught**, as #800 stated: a path built from parts, `getattr` with a computed name, a
  read of `data/monitor/*.json` or of the scoring report.
- **Reported, not fenced.** These modules also reach the monitor: one `vinci.eod` module
  (`dividends`), `vinci.evals`, `vinci.impact`, `vinci.quality`, `vinci.orchestrator` and
  `vinci.cli`. None sets a decision parameter.
- The older direct-only fences stay where they are. The ranker's also bans `vinci.store`, which
  this fence does not.
