---
id:
status: shipped
date: 2026-11-04
prs: [908]
supersedes:
superseded-by:
---

# Retired: `vinci.themes` and the CIQ charting reader — the theme scan, cards, exposure, assay, the Themes edge of the app and the monitor's theme falsifiers, removed; STATE rows 7, 14, 21, 22, 23 withdrawn (R2 of three retirements)

**WHAT.** The operator decided on 2026-11-04 to retire `vinci.themes` (last output 2026-09-14) with
the CIQ charting reader built for its GLP-1 / AI research. This is R2 of three retirement PRs. R1
(#905, merged as `3ad14793`) retired the calls tape, graph Test 0/1, the scale back-fill and triage;
R3 retires the between-print panels. Theme intelligence (`vinci/theme_intelligence`,
`frontend/theme-intelligence/`) is a different package and is untouched. Removed:

| what | detail |
|---|---|
| `vinci/themes/` | 26 modules, 7,161 lines (scan, stage 2, exposure, drafts, review, priced check, thesis cards, economics roll-ups, forward freeze, assay, rent series, …) |
| `vinci/dossier/ciq_charting.py` | the CIQ charting-export reader (2026-09-03); nothing on the assembly path imported it |
| the theme CLI | 13 commands in `vinci/cli.py` (`themes`, `themes-stage2`, `themes-exposure`, `themes-draft`, `themes-review`, `themes-priced-check`, `themes-forward`, `theme-thesis declare`, `theme-economics`, `themes-assay`, `themes-assay-retrocast`, …) with their helpers and the top-level `vinci.themes.*` imports (1,231 handler lines, 244 parser lines) |
| the monitor's theme falsifiers | `_cmd_monitor`'s sweep of the thesis cards, `monitor.ThemeFalsifierRow` / `theme_falsifier_rows`, the `theme_falsifiers` field of `MonitorSnapshot` and its printout; `vinci/panels_theme.py` and the theme panel tier in `panels_emit` / `panels_declare` |
| the Themes edge of the app | `frontend/views/themes/` (5 views), `frontend/themes/` (12 committed display files), `frontend/radar/` (6), and their wiring in the kept files below |
| data | `data/themes/{baskets,economics,thesis}/`, `data/scan_history/` (9 files), `data/snapshots/candidate_themes.jsonl`; their `.gitignore` exceptions |
| docs | RUNBOOKS §a–d (monthly sweep, group-review recording, survivor checks, theme-advance) and §h (the radar's calendar) become one-paragraph stubs; the other letters are kept so "RUNBOOKS §j" still resolves |
| tests | 18 theme-only test files (323 cases), and 21 theme tests (23 cases) out of 9 shared files; two shared pins are cut to their non-theme half (below). Cases collected at `481e82f7`, parametrised cases counted |

**Restore** by reverting #908's squash commit on `main`. That undoes every edit at once: the 91
deletions and the edits to the kept files listed below. Copying the deleted files back by hand is NOT
a restore. The views need their nav entry, routes and getters in `app.js` and `lib/snapshots.js`,
and their mirrors in `build.py`. The commands need their handlers and imports in `vinci/cli.py`, and
the monitor needs its field and sweep back. `git checkout 481e82f7 -- <path>` is right only for a
DELETED path. Every one of the 91 is unchanged on `main` from `481e82f7` through `3ad14793` (R1 and
#904 touched none of them).

**KEPT, on purpose.**

- **`data/themes/ledgers/`**, the two frozen 2026-09-01 ratification ledgers (glp1-drug-value-chain
  15 BUY / 29 AVOID; ai-value-migration 168 / 189). CLAUDE.md's no-ledger-delete rule governs, and
  they are the record of that forward test (coordinator's ruling, 2026-11-04). **Nothing reads them
  any more.**
- **The theme band** — `data/snapshots/theme_universe_snapshot.jsonl` and
  `theme_universe_stats.json`. The brief removes them "after confirming nothing kept reads them",
  and kept code does: the universe builder writes them (`vinci universe --band theme`) and the
  store re-exports the table on every weekly run. Their only READER was `vinci.themes.detection`.
  Removing the band means editing `vinci/universe.py`, `vinci/store/` and `vinci/config.py` on the
  weekly path, so it is a FOLLOW-UP, not part of R2.
- History that names `vinci/themes/`: `vinci/sleeves.py`'s dormant `thematic` sleeve
  (`ledger_active=False`); comments in `vinci/edgar/client.py`, `vinci/theme_intelligence/extract.py`
  and `tests/test_submissions_memo.py`; `docs/theme_admissibility.md`, which describes the method as
  it stood; `docs/drafts/ai-compute-platform.card.draft.json`, the falsified draft card; and the
  `theme_falsifiers` block of every committed monitor day through 2026-11-02 (`data/monitor/`,
  `frontend/monitor/`).
- `frontend/views/shared/panels.js` still renders a theme tile if a committed day carries one (every
  day through 2026-11-02 does). R3 retires that view with the rest of the panels.

**Every kept file this PR edits** (each edit only where a removal forced it):

- `vinci/cli.py`: the 13 theme commands, their handlers and helpers, and the four top-level
  `vinci.themes` imports are removed; `_cmd_monitor` no longer sweeps thesis cards and builds its
  day without `theme_falsifiers`.
- `vinci/monitor.py`: `ThemeFalsifierRow`, `theme_falsifier_rows`, the `theme_falsifiers` field and
  its printout are removed. A day file that carries the key still loads: `MonitorSnapshot` ignores
  an unknown key.
- `vinci/panels_emit.py` loses the theme tier (`theme_panel_rows` and its import), and
  `vinci/panels_declare.py`'s `all_registries` merges the universal and default registries only.
- `frontend/app.js`: the Themes nav entry, its route and the legacy radar redirect are removed, and
  two comments that used `#/themes/scan` as their example now use `#/intel/themes`.
- `frontend/lib/snapshots.js`: the eight theme-edge getters and the `./themes` and `./radar` roots
  are removed.
- `frontend/views/shared/overview.js`: the theme-edge card and its getter are removed.
- `frontend/build.py`: the theme freeze, thesis, economics and radar mirrors, the mirror re-seed
  guard that served them, `--themes-src`, and their part of the printout are removed.
- `frontend/assets/styles.css`: the rules whose every selector needs a class only the removed views
  used are removed. A prune over the removed views and every kept frontend source found them: 163
  rules and section comments on R2's first base, plus the themes-index block by hand. That first
  prune kept the radar's `.rd-head`, because the calls tape used the class too (R1 then merged the
  tape's override into it). On `main` after R1 nothing uses it, so it goes, with `.filter-select`.
  The calls tape was `.filter-select`'s last user at `481e82f7`, so R1 should have removed it.
- `.gitignore`: the `!data/scan_history/` and `data/themes/{baskets,thesis,economics}/` exceptions
  are removed, and a RETIRED note sits above the block that keeps `data/themes/ledgers/`.
- `scripts/verbatim_key_flips.py` drops its theme-exposure corpus, the fourth consumer's. The other
  three consumers' five corpora stay.
- `docs/RUNBOOKS.md`: §a–d and §h are stubs. The preamble's git-ignored bullet, §f's DriverSpec /
  `reviews.json` bullets and §g's Radar scope cap are removed, and the KNOWN GAP bullets are
  condensed. A measurement that names `test_ciq_charting` notes that the test left.
- `docs/engineering.md`: the glossary's *themes lane* and *theme card* entries are marked retired.
- Tests cut to their non-theme halves:
  - The theme definitions are dropped from `test_amended_filings`, `test_efts_caps_and_instants`,
    `test_model_input_checks`, `test_parity_pins`, `test_retention`, `test_sec_refusals` and
    `test_theme_universe_band`.
  - `test_panel_emit`'s corpus pin reproduces every committed row except the theme tier.
  - `test_scenarios` keeps its emit pin's determinism half.
  - `test_snapshot_absence` probes the shared fetch layer through the scenario-card getter.
  - `test_tiered_gates` drops its watchlist test, and its views tuple drops the theme views.
  - `test_zero_coercion_lint` loses two entries, and `test_fpi1a_annual_report_currency` loses one.
  - `test_load_bearing_axis` checks a subset of keys.
  - `test_extraction_version_drift` is re-pinned, because the charting reader left the watched set.
    No version row is needed, because no page's output moves.

**STATE.** §5.0 rows 7, 14, 21, 22 and 23 are deleted as WITHDRAWN (operator, 2026-11-04) and named
in the empty-rows note. The block's header paragraph "FROZEN 2026-09-01 — the forward clock is
RUNNING on BOTH declared drivers" is struck as withdrawn. §2 carries one three-line claim that every
§2 line naming `vinci/themes/` describes removed code, restorable by reverting this PR. Rows 26–28,
30, 32, 41, 42 and 45 were read for theme references. Only row 26 has one: it names the theme tier
as history, and R3 closes that row. Rows 41 and 32's MCK, WAT and materiality text is about
dossiers, not `vinci.themes`. None of these rows is edited here.

**CLAUDE.md — for the operator's ruling, NOT edited here** (a CLAUDE.md edit asks the operator first):

- line 6: the RUNBOOKS loop list names "monthly sweep, group-review recording, survivor checks,
  theme-advance … calendar", now stubs;
- **THE DURABILITY SCREEN SELECTS PERSISTENTLY EXPENSIVE NAMES** (lines 262–271): a property of the
  themes method, citing "RUNBOOKS step 8" of the retired theme-advance loop;
- **DOES THIS SELECT ON FORM** (line 225) and **NEVER ASSERT ABSENT** (line 129) cite the
  `ai-compute-platform` prefilter as an example; **CUMULATIVE NUMBER** (WST), **REMOVING A CORRUPTED
  NAME** and **A COUNT TEST** (FVRR) came from theme work too. Their rules are general; only the
  examples are theme history.

**WHY.** Operator, 2026-11-04, from the coordinator's audit of what the core paths reach: dossier
assembly, the weekly refresh and theme intelligence reach 185 of the 229 `vinci` modules (static
import reachability from those three entry points, at `main` `1b8a5a2f`, 2026-11-04), and none of
them imports `vinci.themes`. The monthly score's baskets come from `data/followed.json` through
`vinci.scoring.baseline`. `vinci.themes` carried 455 tests and had not produced output since
2026-09-14.

**HOW VERIFIED.** Every run below is on this PR's code as built on `main` after R1 (`7f4be8c2`)
against `main` itself (`3ad14793`). `main` ran first; the branch ran on a clone of what `main`'s run
left. R2's first runs, on its original base `481e82f7`, gave the same results. (Outputs in the PR
body.)

- **The weekly path — a `vinci run-weekly` replay of the 2026-10-16 run.** Inputs: that weekly's own
  store (`research-alpha-audit-bcba59/data/vinci.db`, APFS-cloned; md5 `9e727a63…` before and after)
  and a clone of the HTTP cache R1's `main` replay had filled; every cached response is served
  whatever its age. `main` ran with misses allowed and needed none (0 misses, 95 s). The branch then
  ran with the network REFUSED (0 misses, 95 s). The result dicts are identical (436 G1/G2
  survivors, 344 candidates, 344 ranked, 69 structural flags). `data/snapshots` holds 86 files after
  `main`'s run and 85 after the branch's. **All are byte-identical except `candidate_themes.jsonl`,
  which this PR deletes.** That covers the universe, the queue, the screen run and its manifest, and
  the theme band's two files. `data/facts` (#904's shadow store) is identical too.
- **The monitor day** — `vinci monitor --ref 2026-11-02 --out <scratch>`, on a clone of the cache
  R1's `main` run filled. Take `main`'s day and remove its 7 `theme_falsifiers` rows and its 6
  theme-tier panels: what remains **equals this branch's day exactly**. That covers the spread, the
  rows, the realized returns, freshness (UNREAD PRINT, next print), the notes and the other 118
  panels. `main`'s printout has a THEME FALSIFIERS block; the branch's has none.
- **The $0 pre-spend check** — `vinci dossier precheck` on GOOGL, VRRM and TJX, with the Anthropic
  key removed from the process, the assembler's CIQ copy (`mosaic-theory-ta/data/manual`) and a
  clone of its store. `main` and the branch print the same 78 lines once timestamps and paths are
  removed; they are equal in content, not byte for byte. GOOGL compares 110 Sourced fields and 6
  blocks: 0 regressions, 0 post-spend refusals, exit 0. TJX: 0 / 0, exit 0. VRRM: 0 regressions and
  its standing stale-export refusal (oldest panel 99 days old against the 45-day ceiling), exit 1.
- **The app** — `frontend/build.py` rebuilds every mirror and changes no committed file. It
  recreates none of `frontend/themes/`, `frontend/radar/` or `frontend/calls/`. Served locally on a
  fresh port: the nav lists Overview, Dossier, Decision log, Monitor panels, Overshoot, Theme
  intelligence and the locked edges, with no Themes. The old `#/themes/radar` URL falls back to the
  overview. `#/dossier/GOOGL` and theme intelligence's `#/intel/themes` render, and the console logs
  no error. `node --check` passes on `app.js`, `lib/snapshots.js` and `views/shared/overview.js`.
- **Theme intelligence** — its 1,381 tests pass (5 skipped). Smoke run: the registry from the
  `theme-intelligence-state` branch (head `63e09f4d`) is imported into a fresh data dir and
  `publish`ed ($0, no model call), once with `main`'s code and once with this branch's. Each run
  writes 127 files, identical apart from the publish time (`published_at` and the pages' "Generated
  … UTC" footer).
- **`scripts/verbatim_key_flips.py`** — cache-only over the committed corpus (the primary
  checkout's `data/cache`, read only), with the six held test packs excluded: exit 0, "0 answers
  moved" across its five remaining corpora.
- **Gate.** At `7f4be8c2`: ruff, all checks passed; `mypy --strict vinci`, no issues in 191
  source files (219 less the 28 removed modules); `pytest -m "not network"`, **8,768 passed, 0
  failed**, 555 skipped (chiefly the tests that need the git-ignored CIQ exports), 8 xfailed, 39
  deselected, 383.5 s. That is R1's final 9,114 less the 346 removed cases (323 + 23). The head
  after it changes only comments, this record and STATE, and `bin/commit` ran the full gate green
  on it before committing.

**BOUNDARY.** Line and file counts: `git ls-files` / `wc -l` at `481e82f7`. Test counts: `pytest
--collect-only` at `481e82f7`. The 91 deletions: `git diff --name-status origin/main...HEAD`, status
`D`, at this PR's head. Each run states its own inputs above.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The theme lane is gone from `main`: no scan, no cards, no
falsifier sweep. A theme thesis is now theme intelligence's alone, which is not on the decision path.
Restoring means reverting #908's squash commit (see **Restore** above). Falsifier: a forward-test
reading wanted from the two kept ledgers. Nothing computes it now, so it would need that restore.
