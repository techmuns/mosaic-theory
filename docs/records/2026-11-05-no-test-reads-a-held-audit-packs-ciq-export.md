---
status: shipped
date: 2026-11-05
prs: []
supersedes:
superseded-by:
---

# No test reads a held audit pack's CIQ export: one shared list every page and CIQ-folder loop goes through, an audit hook that refuses the open, and a guard that refuses a loop that bypasses them

**WHAT.** TeamNostra's six blind CIQ export packs (BURL, MTB, RIVN, PCVX, NVO, PLD, exported
2026-10-28) must never be read by mosaic-theory code until TeamNostra freezes its answer key. The
suite is mosaic-theory code, and until now nothing in it knew the rule. On 2026-11-05 #911 found
that a run with `data/manual` linked read BURL's real export. Three pieces now make the suite
enforce the rule itself:

1. **One list** — `tests/held_names.py`, `HELD_NAMES`. Every per-page parametrization and every loop
   over pages or CIQ folders that can reach a CIQ export goes through it, and the decision is made
   on the NAME, before any file in the folder is opened:
   - a parametrization takes `page_params(...)`: a held case keeps its id and is SKIPPED with a
     reason that names the rule (*"BURL is a held audit pack — TeamNostra's blind CIQ test set,
     which no mosaic-theory code reads until its answer key is frozen (tests/held_names.py)"*);
   - a loop takes `without_held(...)`: held names are dropped before the body runs, and the
     terminal summary lists every loop that dropped one (CI runs `-p no:warnings`, so a warning
     would never be seen);
   - a helper that takes one ticker calls `skip_if_held(ticker)`.

   Routed on this branch: 40 `without_held` sites in 20 modules, 15 `page_params` decorators in 6,
   and 4 `skip_if_held` calls in 3. Six enumerations in 3 modules carry
   `# held-names: reads no CIQ export` instead. Each of those six read no CIQ file at all in the
   linked run (the probe, below). #911's own `HELD = ("BURL",)` in `tests/test_input_manifest.py`
   now uses the shared list.
2. **A backstop** — an audit hook installed by `tests/conftest.py` (`refuse_held_open`). Any `open`
   of a file under a held name's folder in this checkout's `data/manual` FAILS the running test
   before a byte is read. The roots it watches are `data/manual` as spelled and as resolved, the
   resolved `ciq` and `ciq-archive`, and the resolved target of any held folder that is a link.
   The refusal is recorded too, so a test that swallows it (an `except BaseException`) still fails
   at teardown. This covers what no static check sees: a production function the test calls, a
   helper imported from another module, a copy. It refuses OPENS. Listing a folder reads no
   export, so listing is not refused (see 4 for how the archive search stopped listing anyway).
3. **A guard** — `tests/test_held_names.py`, a static scan of all 392 test modules. It refuses a
   loop or parametrization over the committed pages (`data/dossiers`, `frontend/dossiers`) or the
   CIQ folder (`data/manual`) whose values reach code that can open a CIQ export without passing
   through the list. The scan follows the values: through names bound in the function or the
   module, a helper's return, and a name imported from another test module. It stops at
   pass-throughs (`sorted`, `list`, `next` and the like). A consumer is any other call, so
   `CiqBundle.from_files(t, sorted(d.iterdir()))` counts as reading in that statement. It
   ignores truthiness and `len` uses. An enumeration of the CIQ folder must always go through the
   list. A page enumeration may instead carry the declaration, on its statement or alone on the
   line above.

   Its pins: positive and negative cases for each shape it reads, the refused ones copied from main
   `c4c9f432`, including the `test_ev_bridge` loop and the `test_forward_consensus` per-page
   parametrization that read BURL. The helpers and the backstop each have positive and negative
   pins, the backstop exercised through a real `open()` on a fake CIQ folder.

4. **The archive search lists no held folder.** `ciq_export_support.archived_bundle` searched with
   `root.rglob(ticker)`, which lists every folder it passes, so looking for SMPL's archived export
   read the file names in an archived BURL folder. `archived_folders` walks the same folders,
   symlinked ones matched but not descended into, as 3.12's `rglob` does, and never enters a held
   name's folder. Pinned against `rglob` on a fake tree, with a `scandir` spy for the held folder.

5. **The BURL-real-export test** (`test_the_real_burl_export_is_read_as_empty_not_broken`) is
   SKIPPED while BURL is held. It is not deleted. Its read is also routed, so the day BURL leaves
   the list it runs again unchanged.

**WHY.** A blind test proves an extractor only if nothing was fitted to those exact files. The
exclusion depended on the operator remembering to link a scratch copy without the held folders,
and the suite parametrizes over every committed page, BURL's included. A rule held in memory
failed once; this makes it a property of the suite.

**HOW VERIFIED.** All runs below are on this machine, linked to a scratch CIQ folder: an `rsync` of
Drive's `manual/ciq` and `manual/ciq-archive` with the six held names EXCLUDED AT COPY TIME (so no
held byte was ever read). Planted into it were seven FAKE held folders: one per held name under
`ciq/`, plus `ciq-archive/replaced-2026-10-28/BURL`. Each holds ten sentinel files named like
real exports, chmod 000, containing only the word `SENTINEL`. A pytest audit-hook probe (an
observer, loaded with `-p`) logged every `open`, `os.listdir` and `os.scandir` under those roots,
per test.

- **Before (main `c4c9f432`, the full offline suite):** 9,273 passed, 16 failed, 108 skipped,
  39 deselected, 8 xfailed in 18m45s. **46 tests in 21 modules touched a held folder: 1,751 opens
  and 191 listings.** 14 of the 16 failures are those tests failing on the unreadable sentinels.
  The other 2 involve no held name: `test_forward_consensus::test_every_spread_sits_on_its_own_trends_figure[GOOGL]`
  and `[LLY]`, against the exports Drive holds today. Across the run, 493 tests in 35 modules
  touched `data/manual` at all.
- **After (this branch):** AFTER_RUN_LINE
- **CI-like (this branch, no `data/manual`):** CI_RUN_LINE
- **The guard on the corpus:** the final scanner flags **50 enumerations in 27 modules on main
  `c4c9f432`**: 49 in-module, plus `COMPUTED` imported by `test_ciq_export_support` and passed raw
  into `own_export_census`. It flags 0 on this branch. Every module the probe caught is among the
  27, except `test_liquidity_line`, which takes its loop from `test_capital_panel_selection._bundles`
  and is fixed where that loop is defined. Six mutants, each reverting one routing in a scratch copy,
  were each caught at the exact line: the `test_ev_bridge` page loop, a `test_forward_consensus`
  decorator, the `test_capital_panel_selection` existence probe, the imported `COMPUTED`, the
  maintenance orphan, and a removed declaration.
- **The scan's misses, found and fixed while building it, each now pinned:** a CIQ path returned
  by a helper (`root = _root()`, two loops in `test_capital_panel_selection`), and a page list
  imported from another module (`COMPUTED`). Also fixed was a false positive: a temp-dir parameter
  read through another function's binding of the same name.
- **Cost of the hook:** +2.5 µs per `open()` (18.6 → 21.2 µs, 100,000 opens, 4 roots and 6 held
  folders linked).

**BOUNDARY.** Commit: main `c4c9f432` (#911 merged) for every "before" count and for the
population; this branch for every "after" count. Modules: `tests/**/*.py` minus `tests/fixtures/`,
`held_names.py` and `test_held_names.py` — 392 modules. Enumeration sites: calls to `glob`,
`rglob`, `iterdir`, `os.listdir`, `os.scandir` or `os.walk` whose receiver resolves to a
spelled path into `data/dossiers`, `frontend/dossiers` or `data/manual`. That is **224 sites (190
page, 34 CIQ-folder) in 117 modules**; 67 modules name a CIQ reader. Dynamic counts: one full
offline run (`-m "not network"`), linked as above, unit = audited filesystem calls under the CIQ
roots, attributed to the running test (none at collection). Held-ticker literals: string constants
containing a held ticker as a word, counted by AST over the same 392 modules: **61 constants in 18
modules**, of which 26 are values rather than docstrings or prose.

**THE HELD-TICKER REFERENCES (the brief's direct-reference sweep), classified.** Of the 26 value
literals:
- one reads a CIQ export: the BURL-real-export test's path, now skipped while held;
- one was a held list: #911's `HELD`, now the shared list;
- every other reads committed SEC fixtures (`_facts("BURL")`, `_rec("BURL")`, a lease-basis
  fixture), a committed page, or is a dict key or an expected value.

The probe agrees: no test outside the 46 touched a held folder. **NOT CHANGED, a question for the
operator:** about a dozen tests run extractors on BURL's committed SEC fixtures — `test_anchor_ltm_window`,
`test_cross_check`, `test_debt_maturities`, `test_ebitda_recon_wave2`, `test_lease_basis`,
`test_net_debt_one_builder`, `test_forward_multiples_and_basis`, `test_covenant_refused_newer`.
The rule as stated covers the CIQ packs; whether it extends to SEC data for the same six names is
the operator's call.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The static guard sees one module at a time, plus module-level names imported from another
  test module.** It does not follow:
  - an attribute import (`mod.NAME`);
  - a page list passed in as another module's function argument;
  - a production function that enumerates pages itself;
  - a CIQ path built without a spelled `manual` (`LocalFolderStore(...).location()`,
    `archive_roots()`).

  The audit hook covers all four in any linked run, because it watches every open in the process.
  *Falsifier: a linked run in which the hook refuses an open, or a held case runs.*
- **A subprocess runs outside the hook.** On main `c4c9f432`, nine test modules start a Python
  child (`sys.executable`). The ones that run `vinci` code on a ticker run it on SMPL
  (`test_measured_triggers`) or on fake paths (`test_input_manifest`), and no child is passed a
  held ticker. A new one would be caught only in review.
- **The guard over-approximates.** It counts `CiqBundle` as a reader, so a test that builds an
  empty synthetic bundle needs the declaration (`test_pe_basis_cause_claim`). A test whose page
  path is a temp copy needs it too (`test_prespend`). Six declarations, each measured at zero CIQ
  accesses in the linked run; the hook still checks them in every linked run.
- **A held page leaves the CIQ loops it was in.** In CI that costs nothing: those cases skipped
  there anyway (no exports), and now say why. The maintenance orphan
  (`test_maintenance_path._a_maintained_orphan`, a name assembled with `data/manual` linked) can no
  longer be a held name. On main it was not BURL only because the candidate set happened to put
  another name first.
- **Not done (scope):** the fact layer keeps its own exclusion, passed as `--exclude` on every run
  (`vinci/facts/__main__.py`). Production code (`assemble`, `precheck`) has no held list. Both are
  outside the suite.

**LIFTING IT.** Remove the name from `HELD_NAMES` and from its pin
(`test_the_list_is_the_six_audit_packs`). Every skip and every dropped loop then runs the name
again.
