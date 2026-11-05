---
status: shipped
date: 2026-11-05
prs: [917]
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
- **After (this branch):** 9,315 passed, 3 failed, 119 skipped, 39 deselected, 8 xfailed in 33m16s (collected at `20f69b71`). **0 held-folder accesses — no open, no listing.** 13 held cases skipped with the rule as their reason; 41 loops listed in the summary as having dropped a held name. The 3 failures: main's own GOOGL and LLY spreads, and `test_records_ledger` refusing this record while its `prs:` was empty (filled in once the PR existed). It ran longer than before because the tests that failed at BURL now read every other folder (the slow reader below). A linked re-run of `test_maintenance_path`, `test_maintenance_identity`, the guard and `test_ciq_export_support` at `9d09894d` (the link fix), with the probe resolving held-named paths too: 83 passed, 1 skipped, 0 held-folder accesses.
- **CI-like (this branch, no `data/manual`):** a `git clone` of the branch at `e5ff9984` with `origin/main` at `c4c9f432` and nothing untracked, run as the gate runs it (`-m "not network" -p no:warnings`): 8,883 passed, 1 failed, 557 skipped, 39 deselected, 8 xfailed in 10m42s. The 1 failure is the same empty-`prs:` refusal. 557 skipped is the count #911 recorded for its own final tree in CI-like form (not re-measured on main here); 12 of them now give the held reason (BURL's per-page cases, which skip in CI either way, for want of an export).
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
- **The review round** (`/code-review high --fix`, 10 findings). 8 fixed, each behind a pin that
  fails on the old logic (mutation-checked):
  - the hook now watches the `ciq-archive` beside a linked `ciq` folder;
  - it matches roots without regard to case (APFS does not tell case apart);
  - the scan follows a page list read inside a nested function;
  - it no longer settles a recursive helper as "reads no CIQ" before the call that does returns;
  - it no longer counts a docstring as a path into the CIQ folder;
  - a cut site says it was cut;
  - the helpers' unused `key` parameters are gone;
  - each module is parsed once.

  2 skipped. A central collection hook would also skip held pages' committed-JSON cases. Held
  packs kept under a non-ticker folder name are question (2) below. After the round the guard
  still flags 50 on main and 0 here, and the 6 routing mutants are still each caught.
- **A hole found after the review, by the CI-like run's left-out summary.** `test_maintenance_path`
  and `test_maintenance_identity` build a scratch data folder that symlinks `manual` to this
  checkout's `data/manual`. An open spelled through it matched none of the hook's roots, and it
  matched none of the probe's either, so the "before" count cannot see such a path. The hook now
  resolves a path that has a held ticker as one of its folders and judges where it leads. It is
  pinned both ways, and the pin fails with the fallback removed. Neither module reads CIQ: the
  finalist functions they call (`load_finalists`, `_standalone_record`, `_maintenance_reason`)
  never touch the store. The linked re-run of both modules with the fixed probe is below.
- **The helpers and the backstop, mutation-checked:** 6 mutants, each killed by its own pin —
  the hook never refusing, ignoring a linked held folder, or matching case-sensitively;
  `page_params` not skipping; `without_held` keeping a held name; a file's own name counted as
  held.
- **Cost of the hook:** +5.8 µs per `open()` on the PR head `99c8b681` (22.9 → 28.7 µs, best of
  3 × 200,000 opens, 4 roots and 6 held folders linked). The first figure, +2.5 µs, was measured
  before the case-folded roots and the link fallback, and no longer described the shipped hook
  (review round 1).
- **Review round 1** (Codex failed on its usage limit, so the in-session `/code-review high` stood
  in; 6 findings): 2 FIXED — this cost figure, and a checkout under a held-named folder (`/srv/PLD/…`)
  marking every page held, which is pinned and failed on the head. 4 DISMISSED:
  - a cheaper prefilter in the hook (~6 s at most over a 17-minute suite, no failure);
  - the left-out summary listing a loop that dropped a held name it would not have used (the list
    did drop it, and a lazy helper would be a single-use-iterator trap);
  - a refused open reported as a failure plus a teardown error (loud either way);
  - the bare word `"manual"` counting as a CIQ path. Narrowing it un-flagged `test_maintenance_path`,
    whose `_LINKED` tuple links the CIQ folder by that bare name, and let a routing mutant survive.
    Measured, then reverted.
- **Found on the way, not changed (a slow reader the old failure hid):**
  `test_segment_absence_and_relationship_route::test_the_customers_export_is_chosen_by_name_not_by_file_order`
  ran about 15 minutes in the targeted run. `customers()` spends 164.5 s in `read_text`'s regex on
  AMZN's 2.9 MB Customers RTF and 147.7 s on GOOGL's 2.6 MB one (measured once each, this
  machine, Drive's exports of today), and the test calls it twice per folder. On main the stub
  BURL folder failed the test at its third folder, so the cost never showed. It is a property of
  `vinci/dossier/ciq.py:read_text` and is out of this change's scope.

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

The probe agrees: no test outside the 46 touched a held folder.

**NOT CHANGED — two questions for the operator.**
1. About a dozen tests run extractors on BURL's committed SEC fixtures: `test_anchor_ltm_window`,
   `test_cross_check`, `test_debt_maturities`, `test_ebitda_recon_wave2`, `test_lease_basis`,
   `test_net_debt_one_builder`, `test_forward_multiples_and_basis`,
   `test_covenant_refused_newer`. The rule as stated covers the CIQ packs. Whether it extends to
   SEC data for the same six names is the operator's call.
2. The hook recognises a held export by a TICKER-NAMED folder. Drive's `manual/` also holds a
   `CIQ exports` folder, which this work deliberately did not list. If the packs sit there under
   company names, the hook would not refuse an open of them. No test reads that folder: the store
   reads only `ciq/`, and the scratch copy left `CIQ exports` out. Should the suite refuse every
   open under `data/manual` outside `ciq/` and `ciq-archive/`?

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
