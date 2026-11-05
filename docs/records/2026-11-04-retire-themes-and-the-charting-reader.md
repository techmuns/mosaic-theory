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
| the Themes edge of the app | `frontend/views/themes/` (5 views), `frontend/themes/` (12 committed display files), `frontend/radar/` (5 of its 6; `reviews.json` is kept, below), and their wiring in the kept files below |
| data | `data/themes/{baskets,economics,thesis}/`, `data/scan_history/` (9 files), `data/snapshots/candidate_themes.jsonl`; their `.gitignore` exceptions |
| docs | RUNBOOKS §a–d (monthly sweep, group-review recording, survivor checks, theme-advance) and §h (the radar's calendar) become one-paragraph stubs; the other letters are kept so "RUNBOOKS §j" still resolves |
| tests | 18 test files (323 cases), and 21 theme tests (23 cases) out of 9 shared files; two shared pins are cut to their non-theme half (below). The 18 files held 9 tests that pin behaviour this PR KEEPS; they moved to kept files (**THE LOST PINS**, below). Cases collected at `481e82f7` and again at `05b2529b` (the same 323), parametrised cases counted |

**Restore** by reverting #908's squash commit on `main`. That undoes every edit at once: the 90
deletions and the edits to the kept files listed below. Copying the deleted files back by hand is NOT
a restore. The views need their nav entry, routes and getters in `app.js` and `lib/snapshots.js`,
and their mirrors in `build.py`. The commands need their handlers and imports in `vinci/cli.py`, and
the monitor needs its field and sweep back. `git checkout 481e82f7 -- <path>` is right only for a
DELETED path. Every one of the 90 is unchanged on `main` from `481e82f7` through `2771d9a1`, the
latest `main` checked (R1, #904, #906 and #907 touched none of them), so every `main` commit before
this PR's merge, `05b2529b` included, still holds the removed code.

**KEPT, on purpose.**

- **`data/themes/ledgers/`**, the two frozen 2026-09-01 ratification ledgers (glp1-drug-value-chain
  15 BUY / 29 AVOID; ai-value-migration 168 / 189). CLAUDE.md's no-ledger-delete rule governs, and
  they are the record of that forward test (coordinator's ruling, 2026-11-04). **Nothing reads them
  any more.**
- **The theme band** — `data/snapshots/theme_universe_snapshot.jsonl` and
  `theme_universe_stats.json`. The brief removes them "after confirming nothing kept reads them",
  and kept code does: `vinci build-universe --band theme` writes both, and every weekly run
  re-exports the snapshot table from the store (it never writes the stats file). Their only READER
  was `vinci.themes.detection`.
  Removing the band means editing `vinci/universe.py`, `vinci/store/` and `vinci/config.py` on the
  weekly path, so it is a FOLLOW-UP, not part of R2.
- History that names `vinci/themes/`: `vinci/sleeves.py`'s dormant `thematic` sleeve
  (`ledger_active=False`); comments in `vinci/edgar/client.py`, `vinci/theme_intelligence/extract.py`
  and `tests/test_submissions_memo.py`; `docs/theme_admissibility.md`, which describes the method as
  it stood; `docs/drafts/ai-compute-platform.card.draft.json`, the falsified draft card; and the
  `theme_falsifiers` block of every committed monitor day through 2026-11-02 (`data/monitor/`,
  `frontend/monitor/`).
- **`frontend/radar/reviews.json`**, the 46 analyst dispositions of the 2026-07-13..15 group reviews,
  "THE single source of review reasons" (its own `_note`). It is a human record, so it is kept like
  the ledgers (coordinator, round 2; the operator can override), and RUNBOOKS §f keeps its sacred
  bullet as history. **Nothing reads it any more.** The `DriverSpec` texts go with `vinci.themes`,
  as approved.
- `frontend/views/shared/panels.js` still renders a theme tile if a committed day carries one (every
  day through 2026-11-02 does). R3 retires that view with the rest of the panels.
- The CIQ quality scorecard's `charting` family row (`vinci/quality/sources/ciq.py`): the latest
  committed scorecard lists it and must reproduce byte for byte, so it stays, mapping nothing.

**THREE STANDING WATCHES LEAVE WITH THE RADAR — awaiting the operator's keep-or-drop ruling.** They
lived in `frontend/radar/candidates.json` (deleted; at `481e82f7`) and RUNBOOKS §h, and they are
single-name re-underwrite triggers, not theme scans. Nothing checks them now. Each rule, verbatim
from `candidates.json`:

- **Truckload (MRTN, HTLD)**, each: "Re-underwrite when TL revenue per loaded mile turns positive YoY
  for two consecutive reported quarters, OR on a >=20% derate from the 2026-07-13 close while ACT
  capacity data stays tight." (WERN, the third name, was "DOSSIER-NOW" and has its own dossier.)
- **Senior housing (lead AHR)**: "BKD or SNDA same-store RevPOR growth >= same-store opex growth for
  two consecutive quarters, OR NIC occupancy >= 90.0%".
- **In-silico evidence (CERT)**, any one of: "FDA FINALIZES any NAMs guidance or Modernization Act 3.0
  ENACTED"; "first documented FDA acceptance of in-silico/NAMs data in lieu of animal TOXICOLOGY in an
  approval"; "CERT software growth >=15% YoY for two consecutive quarters OR bookings growth turns
  positive"; "CRL discloses client-behavior change or NAMs-attributed DSA backlog erosion". Its note:
  "if any fires: deep study on CERT alone — not a scan".

The AHR and CERT rules are also in STATE.md §2's theme entries; MRTN's and HTLD's are not.

**THE LOST PINS (round 2).** Some deleted test files held the ONLY pins on behaviour this PR keeps.
The coordinator's reviewers showed two of them: with the filing-lag gate removed, or the passed-
deadline flag line removed, the suite stayed green. So all 18 files were audited. Each of their 311
test functions was checked two ways. Statically: does it, through the helpers, fixtures and
constants it reaches, name anything this PR removes? Empirically: the file ran against the head with
its removed-module imports neutralised. Nine tests pin kept behaviour, and they moved verbatim:
two gain a docstring line naming where they came from, and one takes its new file's `mon.`
prefix. Every other test names removed code, or passes only
because the directory it compares is gone. Each moved pin passes on the head and FAILS under a
mutant of the code it guards:

| pin (from) | now in | guards | mutant → result |
|---|---|---|---|
| `test_share_periods_are_point_in_time_no_lookahead` (`test_theme_assay`) | `tests/test_universe.py` | the 40-day filing-lag gate in `universe.recent_share_periods`, on the decision path | gate removed → FAIL |
| `test_scenario_passed_deadlines_now_render_in_the_terminal_view` (`test_theme_falsifier_sweep`) | `tests/test_monitor.py` | the ⚑ "deadline PASSED → re-underwrite due" line in `monitor.render_table` | line removed → FAIL |
| `test_lean_tag_is_label_only_and_never_directional` (`test_build_themes`) | `tests/test_dossier_shelf_tags.py` (new) | `leanTag` stays neutral ink (RUNBOOKS §f, Verdicts) | `pill buy` class added → FAIL |
| `test_shelf_tag_prefers_the_logged_human_verdict` (same) | same | `cardTag` puts the logged verdict before the lean | dispatch inverted → FAIL |
| `test_dossier_index_labels_match_the_backend_resolver` (same) | same | `build.py`'s index `labels` equal `vinci.labels` | `source_ref` dropped, index rebuilt → FAIL |
| `test_dossier_index_reads_are_verbatim_and_complete` (same) | same | `build.py`'s index `reads` are verbatim | a read truncated, index rebuilt → FAIL |
| `test_build_never_grows_a_second_lean_parser` (same) | same | `build.py` ships the read raw | a lean regex added → FAIL |
| `test_a_refusal_whose_reason_omits_the_why_still_shows_it_node` (`test_panels_theme`) | `tests/test_panel_emit.py` | `panels.js` keeps a `why` the reason never carried | de-dup made unconditional → FAIL |
| `test_the_tab_strip_offers_no_tab_that_cannot_be_selected_node` (same) | same | `tabTickers` offers only selectable names | theme filter removed → FAIL |

The two panel pins leave with `panels.js` in R3. A tenth test, `test_charting_is_a_registered_kind`,
pinned the opposite of what this PR now wants. It is replaced by its negative,
`test_a_kind_nothing_reads_never_refuses_a_name` (below).

**Every kept file this PR edits** (each edit only where a removal forced it):

- `vinci/cli.py`: the 13 theme commands, their handlers and helpers, and the four top-level
  `vinci.themes` imports are removed; `_cmd_monitor` no longer sweeps thesis cards and builds its
  day without `theme_falsifiers`. `build-universe --band`'s help and docstring no longer say the
  theme band is read by theme scans (round 2).
- `vinci/dossier/ciq.py` (round 2): the `charting` workbook kind is unregistered. Registered with no
  reader, it made two charting pulls in one folder refuse the whole name (`CiqAmbiguousError`) over a
  file nothing reads. Now a charting export is an unrecognised file, which the assembler names in
  the page's caveats. The negative pin `test_a_kind_nothing_reads_never_refuses_a_name`
  (`tests/test_ciq_one_export_per_kind.py`) failed first with that refusal. Neither CIQ copy (the
  assembler's, the primary's; 36 folders each) holds a charting export, so no page moves, and the
  drift re-pin needs no version row.
- `vinci/scenarios.py`, `vinci/dossier/synthesis.py`, `vinci/dossier/ciq_sheets.py` (round 2): three
  comments cited "RUNBOOKS step 10" of the retired loop and now cite §m. Comments only, which the
  drift hash ignores.
- `vinci/monitor.py`: `ThemeFalsifierRow`, `theme_falsifier_rows`, the `theme_falsifiers` field and
  its printout are removed. A day file that carries the key still loads: `MonitorSnapshot` ignores
  an unknown key.
- `vinci/panels_emit.py` loses the theme tier (`theme_panel_rows` and its import), and
  `vinci/panels_declare.py`'s `all_registries` merges the universal and default registries only.
- `frontend/app.js`: the Themes nav entry, its route and the legacy radar redirect are removed, and
  two comments that used `#/themes/scan` as their example now use `#/intel/themes`.
- `frontend/lib/snapshots.js`: the eight theme-edge getters and the `./themes` and `./radar` roots
  are removed, and a comment's count of shell-404 catches is corrected (round 0).
- `frontend/lib/format.js` (round 2): the grade vocabulary only the theme views used (`GRADE_LABEL`,
  `GRADE_DEF`, `gradeLabel`, `cleanGrade`, `GRADE_BUCKET`, `gradeBucket`) is removed; nothing imports
  any of it. A comment on the tiered ladder no longer names `themes/portfolio.js` as a renderer.
- `frontend/views/shared/overview.js`: the theme-edge card and its getter are removed.
- `frontend/build.py`: the theme freeze, thesis, economics and radar mirrors, the mirror re-seed
  guard that served them, `--themes-src`, and their part of the printout are removed. Two docstrings
  that justified a shape by the theme JSON are reworded (round 0).
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
- `docs/RUNBOOKS.md`: §a–d and §h are stubs. The a–d stub says to read the old text with
  `git show 481e82f7:docs/RUNBOOKS.md` and to restore by the revert, never a whole-file checkout
  (round 1). The §h stub names its three watches (round 1). **The underwrite procedure the old §d
  held as steps 9–10 is restored as its own section, §m** (round 2). That covers `scenario-propose` →
  `scenario-create`, the ratio/IRR ladder, the ratified R3 anchor-and-displace method, "a leg's
  multiple is struck once", "the base leg gets its own mechanism", "the two halves must share a
  window", "the anchor needs its own sanity check", and "sizing first, valuation second" for the CIQ
  pull. It applies to every underwrite, GOOGL's included, and is verbatim apart from two clauses that
  pointed into the retired loop. The preamble's git-ignored bullet, §f's DriverSpec bullet and §g's
  Radar scope cap are removed. §f's `reviews.json` bullet stays as kept history (round 2). The KNOWN
  GAP bullets are condensed, and a measurement that names `test_ciq_charting` notes that the test
  left.
- `docs/drafts/README.md` (round 2) no longer tells the reader to declare a card with the removed
  command into the removed directory. `.claude/launch.json` (round 2) drops its `radar-preview`
  config, which served another checkout's Radar.
- `docs/engineering.md`: the glossary's *themes lane* and *theme card* entries are marked retired.
- Tests that RECEIVE the moved pins: `tests/test_universe.py`, `tests/test_monitor.py`,
  `tests/test_panel_emit.py` and the new `tests/test_dossier_shelf_tags.py` (round 2, table above);
  and `tests/test_ciq_one_export_per_kind.py` gains the charting negative pin.
- Dead test helpers whose only users were theme tests are removed (round 2):
  `test_theme_universe_band._write_snapshots`, `test_efts_caps_and_instants._ShortPageEfts` and
  `_CiklessEfts`, and `test_model_input_checks._EXPOSURE_STREAM` and `_Exposure`.
- Tests cut to their non-theme halves:
  - The theme definitions are dropped from `test_amended_filings`, `test_efts_caps_and_instants`,
    `test_model_input_checks`, `test_parity_pins`, `test_retention`, `test_sec_refusals` and
    `test_theme_universe_band`.
  - `test_panel_emit`'s corpus pin reproduces every committed row except the theme tier, and its
    failure message no longer lists theme cards as a cause (round 1).
  - `test_scenarios` keeps its emit pin's determinism half.
  - `test_snapshot_absence` probes the shared fetch layer through the scenario-card getter.
  - `test_tiered_gates` drops its watchlist test, and its views tuple drops the theme views.
  - `test_zero_coercion_lint` loses two entries, and `test_fpi1a_annual_report_currency` loses one.
  - `test_load_bearing_axis` checks a subset of keys.
  - `test_extraction_version_drift` is re-pinned, because the charting reader left the watched set
    and `vinci/dossier/ciq.py` changed. No version row is needed, because no page's output moves.

**STATE.** §5.0 rows 7, 14, 21, 22 and 23 are deleted as WITHDRAWN (operator, 2026-11-04) and named
in the empty-rows note. The block's header paragraph "FROZEN 2026-09-01 — the forward clock is
RUNNING on BOTH declared drivers" is struck as withdrawn. §2 carries one three-line claim that every
§2 line naming `vinci/themes/` describes removed code, restorable by reverting this PR. Rows 26–28,
30, 32, 41, 42 and 45 were read for theme references. Only row 26 has one: it names the theme tier
as history, and R3 closes that row. Rows 41 and 32's MCK, WAT and materiality text is about
dossiers, not `vinci.themes`. None of these rows is edited here. **Row 5 is** (round 2). Its "Phase 5
SHIPPED — theme panels attach to the DRIVER (`vinci/panels_theme.py`)" is struck and marked retired
in #908. Its item (a) justified itself partly by two theme triggers that could not be checked; those
are marked retired, and the 20-F/6-K blindness it names stands. R3 closes row 5.

**CLAUDE.md — for the operator's ruling, NOT edited here** (a CLAUDE.md edit asks the operator first):

- line 6: the RUNBOOKS loop list names "monthly sweep, group-review recording, survivor checks,
  theme-advance … calendar", now stubs;
- **THE DURABILITY SCREEN SELECTS PERSISTENTLY EXPENSIVE NAMES** (lines 262–271): a property of the
  themes method, citing "RUNBOOKS step 8" of the retired theme-advance loop;
- **A GRADE IS ECONOMIC SUBSTANCE; DISCLOSURE FORM IS A SEPARATE FIELD** (lines 220–230): its
  subject types `ExposureConcreteness` / `ExposureBasis` lived in the deleted
  `vinci/themes/schemas.py`, as did `machine_grade`'s grading, and its four failed surfaces (lines
  225–230) include the `ai-compute-platform` prefilter. The rule now names types that no longer
  exist;
- **NEVER ASSERT ABSENT** (lines 118–138): its examples are theme history. They are McKesson's
  `fee-for-service` searched across Cardinal and Cencora (125–128), the `ai-compute-platform`
  prefilter (129), and AES/ETN escalated off a 400-day probe of a 290-day theme scan (133–134);
- **EVERY COUNT STATES ITS BOUNDARY** (line 231): its 2026-09-02 instances begin with that 400-day
  theme-scan probe;
- **A TRUNCATED OUTPUT PRINTS ITS OWN TRUNCATION** (lines 232–239): its example is a theme scan's
  "GLP-1 mentions: 5" that printed 3;
- **CUMULATIVE NUMBER** (WST), **REMOVING A CORRUPTED NAME** and **A COUNT TEST** (FVRR) came from
  theme work too.

Their rules are general; only the examples are theme history. The exception is A GRADE IS ECONOMIC
SUBSTANCE, whose subject is gone.

**WHY.** Operator, 2026-11-04, from the coordinator's audit of what the core paths reach: dossier
assembly, the weekly refresh and theme intelligence reach 185 of the 229 `vinci` modules (static
import reachability from those three entry points, at `main` `1b8a5a2f`, 2026-11-04), and none of
them imports `vinci.themes`. The monthly score's baskets come from `data/followed.json` through
`vinci.scoring.baseline`. `vinci.themes` had not produced output since 2026-09-14. At `05b2529b`, the
25 test files that mention `vinci.themes` collect 475 cases, and the 18 files this PR deletes
collect 323 (`pytest --collect-only` over a `git archive` of that commit).

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
  `main`'s run and 85 after the branch's. **All are byte-identical except `candidate_themes.jsonl`.**
  The weekly never writes that file (only the removed `vinci themes` command did), so the
  difference is this PR's committed deletion, not anything the run did. The run rewrites the
  universe, the queue, the screen run and its manifest, and the theme band's snapshot (re-exported
  from the store). It does NOT write `theme_universe_stats.json` (only `build-universe --band theme`
  does), so the run does not cover that file. `data/facts` (#904's shadow store) is identical
  too.
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
- **After merging #906 (`05b2529b`) as `a5f3d806`.** #906 changed dossier code. It shared four
  files with this PR, and only the §5.0 empty-rows note conflicted: both sides inserted a sentence at
  the same spot. A word-level three-way merge keeps both, and a check shows every word either side
  added is present. The prechecks and the monitor day were re-run on `main` `05b2529b` against the
  merge. The prechecks print the same 87 lines once timestamps and paths are removed (#906 adds
  output), with the same exits. The monitor day is `main`'s minus its 7 theme rows and 6 theme
  panels, 118 panels each.
- **Gate on the merge `a5f3d806`:** 8,800 passed, 0 failed. At `7f4be8c2`, before #906, the suite
  gave 8,768 passed, which is R1's final 9,114 less the 346 removed cases (323 + 23); #906 adds 32.
- **Review rounds 1 and 2.**
  - Round 1, `891126f1`, an in-session `/code-review high` run because Codex hit its usage limit: 3
    text fixes (the two RUNBOOKS stubs and one test message).
  - Round 2, the coordinator's review of `891126f1`: `main` (#907, `2771d9a1`) merged in clean, the
    lost pins restored (table above), the charting kind unregistered behind a failing-first test,
    §m, `reviews.json` kept, dead leftovers and stale text removed, STATE row 5, and this record
    corrected.
  - Round 2 changes no code path that the weekly, monitor or precheck runs above exercise, apart from
    the unregistered kind. That kind matches no file in either CIQ copy, so those runs stand.
- **Gate, on the final head.** ruff: all checks passed. `mypy --strict vinci`: no issues in 191 source files (219
  less the 28 removed modules). `pytest -m "not network"`: **8,825 passed, 0 failed**, 555 skipped
  (chiefly the tests that need the git-ignored CIQ exports), 8 xfailed, 39 deselected, 363.1 s. From
  the merge's 8,800, #907 adds 15 (its new test file's 14 cases, and one `test_record_hygiene` case
  for its record), and round 2 adds its 10 pins (9 moved, 1 new). Per-file `--collect-only` against
  a `git archive` of `a5f3d806`.

**BOUNDARY.** Line and file counts: `git ls-files` / `wc -l` at `481e82f7`. Test counts: `pytest
--collect-only` at `481e82f7`, and at `05b2529b` where stated. The 90 deletions: `git diff
--name-status origin/main...HEAD`, status `D`, at this PR's head. The audit's 311: top-level `test_*`
functions and `Test*` methods in the 18 files at `05b2529b`, before parametrisation. Each run states
its own inputs above.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The theme lane is gone from `main`: no scan, no cards, no
falsifier sweep. A theme thesis is now theme intelligence's alone, which is not on the decision path.
Restoring means reverting #908's squash commit (see **Restore** above). The three single-name
watches above are unchecked until the operator rules on them. Falsifier: a forward-test reading
wanted from the two kept ledgers. Nothing computes it now, so it would need that restore.
