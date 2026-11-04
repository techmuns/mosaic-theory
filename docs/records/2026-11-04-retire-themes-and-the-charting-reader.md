---
id:
status: shipped
date: 2026-11-04
prs: [R2PR]
supersedes:
superseded-by:
---

# Retired: `vinci.themes` and the CIQ charting reader — the theme scan, cards, exposure, assay, the Themes edge of the app and the monitor's theme falsifiers, removed; STATE rows 7, 14, 21, 22, 23 withdrawn (R2 of three retirements)

**WHAT.** The operator decided on 2026-11-04 to retire `vinci.themes` (last output 2026-09-14) with
the CIQ charting reader built for its GLP-1 / AI research. This is R2 of three retirement PRs (R1,
#905: the calls tape, graph Test 0/1, the scale back-fill, triage; R3: the between-print panels).
Theme intelligence (`vinci/theme_intelligence`, `frontend/theme-intelligence/`) is a different
package and is untouched. Removed:

| what | detail |
|---|---|
| `vinci/themes/` | 26 modules, 7,161 lines (scan, stage 2, exposure, drafts, review, priced check, thesis cards, economics roll-ups, forward freeze, assay, rent series, …) |
| `vinci/dossier/ciq_charting.py` | the CIQ charting-export reader (2026-09-03); nothing on the assembly path imported it |
| the theme CLI | 13 commands in `vinci/cli.py` (`themes`, `themes-stage2`, `themes-exposure`, `themes-draft`, `themes-review`, `themes-priced-check`, `themes-forward`, `theme-thesis declare`, `theme-economics`, `themes-assay`, `themes-assay-retrocast`, …) with their helpers and the top-level `vinci.themes.*` imports (1,231 handler lines, 244 parser lines) |
| the monitor's theme falsifiers | `_cmd_monitor`'s sweep of the thesis cards, `monitor.ThemeFalsifierRow` / `theme_falsifier_rows`, the `theme_falsifiers` field of `MonitorSnapshot` and its printout; `vinci/panels_theme.py` and the theme panel tier in `panels_emit` / `panels_declare` |
| the Themes edge of the app | `frontend/views/themes/` (5 views), `frontend/themes/` (12 committed display files), `frontend/radar/` (6), the nav entry, route and legacy-route redirects in `app.js`, the eight getters in `lib/snapshots.js`, the overview's theme-edge card, `build.py`'s theme freeze / thesis / economics / radar mirrors, and the CSS only those views used |
| data | `data/themes/{baskets,economics,thesis}/`, `data/scan_history/` (9 files), `data/snapshots/candidate_themes.jsonl`; their `.gitignore` carve-outs |
| docs | RUNBOOKS §a–d (monthly sweep, group-review recording, survivor checks, theme-advance) and §h (the radar's calendar) become one-paragraph stubs; the other letters are kept so "RUNBOOKS §j" still resolves |
| tests | 18 theme-only test files (323 cases), and 21 theme tests (23 cases) out of 9 shared files; two shared pins are cut to their non-theme half (below). Cases collected at `481e82f7`, parametrised cases counted |

**Restore** any of it with `git checkout 481e82f7 -- <path>`: the last `main` commit that held
every removed file. Each was unchanged from there until this PR.

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
- `vinci/sleeves.py`'s dormant `thematic` sleeve (`ledger_active=False`), and comments in
  `vinci/edgar/client.py` and `vinci/theme_intelligence/extract.py` that name `vinci/themes/` files
  as history. `docs/theme_admissibility.md` still describes the method as it stood.
- `frontend/views/shared/panels.js` still renders a theme tile if a committed day carries one (every
  day through 2026-11-02 does). R3 retires that view with the rest of the panels.

**Rewired, and only where a removal forced it.** `scripts/verbatim_key_flips.py` drops its
theme-exposure corpus (the other three corpora stay). `tests/test_panel_emit.py`'s corpus pin
reproduces every committed row except the theme tier. `tests/test_scenarios.py`'s emit pin keeps its
determinism half. `tests/test_snapshot_absence.py` probes the shared fetch layer through the
scenario-card getter instead of the theme economics one. The extraction drift pins re-pin, because the charting reader left the watched set; no version row, because no page's output moves. A day file
that carries `theme_falsifiers` still loads: `MonitorSnapshot` ignores the unknown key.

**STATE.** §5.0 rows 7, 14, 21, 22 and 23 are deleted as WITHDRAWN (operator, 2026-11-04) and named
in the empty-rows note. The block's header paragraph "FROZEN 2026-09-01 — the forward clock is
RUNNING on BOTH declared drivers" is struck as withdrawn. §2 carries one three-line claim that every
§2 line naming `vinci/themes/` describes removed code. Rows 26–28, 30, 32, 41, 42 and 45 were read
for theme references. Only row 26 has one: it names the theme tier as history, and R3 closes that
row. Rows 41 and 32's MCK, WAT and materiality text is about dossiers, not `vinci.themes`. None of
these rows is edited here.

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
assembly, the weekly refresh and theme intelligence reach 185 of the 229 `vinci` modules, and none
of them imports `vinci.themes`. The monthly score's baskets come from `data/followed.json` through
`vinci.scoring.baseline`. `vinci.themes` carried 455 tests and had not produced output since
2026-09-14.

**HOW VERIFIED.** (Outputs in the PR body.)

- **The weekly path — a `vinci run-weekly` replay of the 2026-10-16 run** on the inputs R1 used
  (that weekly's own store, APFS-cloned, plus a clone of the HTTP cache `origin/main`'s replay had
  filled; every cached response served whatever its age). The network was REFUSED: 0 misses, 94 s.
  **Every file in `data/snapshots` came out byte-identical to `origin/main`'s replay, except
  `candidate_themes.jsonl`, which this PR deletes.** That covers the universe (2,065), candidates
  and queue (344), the screen run and its manifest, and the theme band's two files.
- **The monitor day** — `vinci monitor --ref 2026-11-02 --out <scratch>` on `origin/main`, then on
  this branch with a clone of the cache main filled. Main's day, minus its 7 `theme_falsifiers` rows
  and its 6 theme-tier panels, **equals this branch's day exactly**: spread, rows, freshness
  (UNREAD PRINT, next print), realized returns and the other 118 panels. The run no longer prints a
  THEME FALSIFIERS block.
- **The $0 pre-spend check** — `vinci dossier precheck` on GOOGL, VRRM and TJX (the Anthropic key
  removed from the process; the assembler's CIQ copy and a clone of its store): the same 44 lines as
  `origin/main` (GOOGL and TJX 0 regressions / 0 post-spend refusals, exit 0; VRRM 0 regressions and
  its standing stale-export refusal, exit 1).
- **The app** — `frontend/build.py` (this worktree's code) rebuilds every mirror, changes no
  committed file and recreates neither `frontend/themes/` nor `frontend/radar/`.
- **Theme intelligence** — its 1,381 tests pass (5 skipped). Smoke run: the registry from the
  `theme-intelligence-state` branch (head `63e09f4d`) imported into a fresh data dir and `publish`ed
  ($0, no model call) with this branch's code and with `origin/main`'s. 126 files each, identical
  apart from `published_at`.
- **`scripts/verbatim_key_flips.py`** — cache-only over the committed corpus, the six held test
  packs excluded: exit 0, "0 answers moved" across its five remaining corpora.
- **Gate.** SUITE

**BOUNDARY.** Line and file counts: `git ls-files` / `wc -l` at `481e82f7`. Test counts: `pytest
--collect-only` at `481e82f7`. Each run states its own inputs above.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The theme lane is gone from `main`: no scan, no cards, no
falsifier sweep. A theme thesis is now theme intelligence's alone, which is not on the decision path.
Restoring is a `git checkout` from `481e82f7` plus re-adding the commands, the monitor fields and
the app's edge. Falsifier: a forward-test reading wanted from the two kept ledgers. Nothing computes
it now, so it would need that restore.
