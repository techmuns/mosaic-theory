---
id:
status: shipped
date: 2026-11-13
prs: [1044]
supersedes:
superseded-by:
---

# MVST (Microvast) is retired from coverage: its page and mirrors leave the corpus (27 → 26 pages), its 2026-07-22 WATCH record is archived intact and stays sealed, so it leaves the monitor's freshness set and the rebuild, and the pins on its page read a frozen copy

**THE RULING.** The operator, 2026-11-12, verbatim: *"we want to drop/remove MVST altogether from
our list for future as well"*. TeamNostra's B relayed it on #1004 (issuecomment-6832102572), and
the operator confirmed it to the coordinator in chat the same day. B's note, verbatim: *"It comes
out of the followed names, the rebuild, the monitor's freshness set and the deployed desk. Its git
history stays. This is a small PR of its own, before the rebuild."* MVST's CIQ folder was already
gone from `data/manual/ciq` before this PR. The precedent is AORT's retirement
(`docs/records/2026-11-09-aort-retired.md`, #942), followed step for step.

## What moved

1. **The page leaves the tree.** `data/dossiers/MVST/dossier.json` and `dossier.md` are deleted.
   `python frontend/build.py` then dropped `frontend/dossiers/MVST.json` and `.md`, and MVST's
   four entries in `frontend/dossiers/index.json` (`tickers`, `labels`, `reads`, `sleeves`). The
   build moved nothing else.
   - **The last commit holding the live page is `047f4c6b`** (#1041, main on 2026-11-12). Read it
     with `git show 047f4c6b:data/dossiers/MVST/dossier.json`. The page was assembled last on
     2026-09-17 (reference date 2026-08-24); its JSON and markdown last changed at `91817458`
     (2026-11-11).
   - **A git-ignored file outlives it.** The iCloud primary checkout holds
     `data/dossiers/MVST/llm_call.log` (126,567 bytes, 2026-07-07). A pull does not remove an
     ignored file, so that folder stays with no page in it. Every reader keys on `dossier.json`.
     **Operator: delete that folder by hand if wanted; nothing in git holds it.**
2. **The underwrite record is archived.** `scenarios/MVST.json` moved to
   `scenarios/archive/MVST-2026-07-22.json`, byte-identical (a 100% rename; sha256 `7ea5662a…` on
   both sides). MVST was underwritten on 2026-07-22, a WATCH at $0.92, and the record names no
   successor (`superseded_by: null`).
   - **No ledger row names MVST**: 0 of the 10 rows in `data/snapshots/decision_ledger.jsonl`. No
     ledger, scoring or monitor file was touched.
   - **The seal moved with it.** The manifest entry moved from key `MVST` to `MVST-2026-07-22`,
     with chars 650 and the sha256 unchanged. It was made through the edit tool, past the
     decision-path hook. `seal.check_all` over all 13 sealable records reports no violation, and
     no manifest key lacks a record.
   - **Its mirror.** `frontend/scenarios/MVST.json` became `MVST-2026-07-22.json`, and the index
     lists the archive key. The card is byte-identical but for "next evidence": the live card read
     MVST's page's catalyst calendar ("Next results print", 2026-11-11), and with no page it reads
     `UNKNOWN`, "no scheduled evidence", "none on file". That is AORT's card, line for line.
   - **The retired-archive guard names it.** `tests/test_record_legibility.py`'s
     `RETIRED_ARCHIVES` gains `MVST-2026-07-22` beside this record, so the "points forward" pin
     accepts it only while it names no successor, MVST has no live record and MVST has no page.
3. **The monitor's freshness set.** A monitor day writes a freshness row for each live ledger
   decision and each `watch` / `pending_analyst` record, and both doors need `scenarios/<T>.json`
   (`vinci/cli.py`: `_watch_tickers` globs the live records, and the day skips a name with none).
   Archiving the record is what takes MVST out: the watch set on the committed book goes from 7
   names to 6 (BRBR, EPAM, IT, NCNO, SMPL, WERN). **Pinned** by a new test,
   `test_a_retired_name_leaves_the_monitors_freshness_set`: on the committed book no retired
   name is in the set and the set is not empty; on a scratch copy of the book with MVST's
   archived record put back live, the same check sees MVST.
4. **The rebuild.** #1041's record put MVST in group 3 (re-export a full set now), priced at the
   $4.44 median because no build is recorded for it. That record gains a dated amendment: group 3
   is IT, ORKA, PARR and WERN, the rebuild covers 26 pages, and by its own rule group 3's cap is
   $19 (was $26) and all 26 are expected at $135.34. No approval is changed; the cap is the
   operator's. STATE row 28's re-export list drops MVST.
5. **Tests.** Measured, not predicted. The full offline suite was run with the page and the
   record moved (CIQ unlinked), and again on clean `047f4c6b`: main 0 failures, the branch 23,
   every one from MVST's absence — 13 page reads, 9 record and page counts or paths, and the guard
   waiting for this record — and 7 new skips against main: six `test_dossier` pins that skip without MVST's page,
   and `test_no_false_unknown[MVST]` (no live record). One more skip changed its reason:
   `test_guidance_vintage`'s undated-release pin, whose decorator now skipped it on MVST's folder
   alone. Each is now one of these:
   - **18 pins read the frozen page** at `tests/fixtures/frozen_pages/2026-09-17/MVST/`. Its
     `dossier.json` and `dossier.md` are byte-identical to `047f4c6b`'s page, and their row is in
     that folder's README. By file:
     - `test_dossier`, 8: the Brief snapshot's alignment, the 99.1 reason folded once, the
       return-ratio table, the ESM render smoke ("LPR + 115 bps"), the T2 covenant table
       ("SOFR + 9.750%"), the T3 revision log, the T1 provenance tier, and P6's cited EX-99.1
       bear point (MVST frozen beside VRRM's living page). These are clear of the transcript-cut
       PR's lines (~9,900–10,020).
     - `test_ev_gap_render`, 3: the suppressed name's total with no shape label, the COVERAGE
       reason, the two margins as figures.
     - `test_ev_gap_routing`, 3: MVST routed on coverage, the check order that misroutes it when
       reversed, and the fleet split. **No living page routes price-implied-only** (24 route
       three-ratio and ORKA and TECX are unrouted, measured here), so the split reads MVST's
       frozen page beside the 26 living ones; without it the split would lose its second route.
     - one each in `test_filing_wall_and_concentration_roles` (MVST's panel against the 10-Q's
       $104.2M wall still differs), `test_efts_caps_and_instants` (MVST's agreement families
       among the seven), `test_labels` (its CIQ-GICS industry) and `test_r4_machine_proposal`
       (condition 2 failing on a normalized-EPS P/E).
   - **One pin reads the archived record**: `test_no_false_unknown`'s legacy pin for MVST, via
     `scenarios/archive/MVST-2026-07-22.json`, as AORT's does.
   - **Eight counts move, logic unchanged**:
     - `test_scenarios` ×2: exactly 8 → 7 live records;
     - `test_basis_equivalence`, `test_horizon_and_irr_gate`, `test_tiered_gates` and
       `test_measured_triggers`: at least 8 → at least 7 live records;
     - `test_anchored_drawdown`: at least 27 → at least 26 pages;
     - `test_spot_as_of_gate`: at least 6 → at least 5 live records carrying a spot date. MVST's
       was the sixth; the five are GOOGL, IT, NCNO, SMPL and WERN. The test was renamed from
       `test_the_six_stamped_records_…` to `test_the_live_stamped_records_…`, since it walks only
       the live records.
   - **One path re-pointed, no check moved**: `test_evals_panel_and_stats` hashes each panel
     row's page. MVST's row was already skipped on main: its page's blob (`b6f83eea`) moved at
     `91817458`, after the panel froze on `d9f1ca85`. It reads the frozen page and is still
     skipped.
   - **One decorator removed**: `test_guidance_vintage`'s
     `skipif(not (DOSS / "MVST").is_dir())`. The pin's own docstring says the rule is about
     undated releases, not about MVST, and it already skips when no page carries one. Tied to
     MVST's folder, it would skip forever in a clean checkout, and run in the iCloud primary,
     where the ignored log keeps the folder. It now skips by its own condition, as it did on main.
   - **One pin retired, not re-pointed**: `test_pages_await_parser_rebuild`'s
     `test_mvst_revenues_of_releases_carry_their_headline_revenue`, a strict xfail waiting for
     MVST's rebuild to land E2-D11's headline revenue. MVST will never be rebuilt, so on a frozen
     page it could never pass — the shape the module's own docstring refuses ("instead of leaving
     one that can never pass"). E2-D11's EPAM half stays an ordinary end-to-end pin and WERN's
     stays strict-xfail. **This departs from the build brief**, which asked for every pin to be
     re-pointed; it is stated, not hidden. **The function is deleted outright.** Fix-log row
     E2-D11 named its node id, and `tests/test_fix_log.py` resolves each named node by `ast`, so
     deleting it first turned `test_fix_log` red (7 failures, every one that row's unresolved
     node). A fix PR edits neither the log nor STATE row 60 (the log's rule 1), so this PR kept a
     skipped stub until the coordinator's bookkeeping batch 7 (#1047, `dad8f441`) dropped the
     node and marked E2-D11's MVST half "not fixing: name retired"; the merge of main then let
     the stub go.
   - **One guard extended and one pin added** in `test_record_legibility` (items 2 and 3).

   **Each moved pin was shown red under one mutation of the frozen value it reads, then restored
   byte-identical** (sha256). The scripts are in the session's scratchpad; their output is in
   HOW VERIFIED. Two pins host behaviour on MVST's page and pin no MVST value (the Brief
   snapshot's alignment and the 99.1 fold); they went red when the page stopped validating. For
   the efts pin, **emptying MVST's instruments leaves it green**: AORT's frozen and WERN's living
   instruments supply its seven families, so MVST's are not load-bearing there. It went red when
   one MVST instrument stopped validating. Stated rather than hidden, as AORT's was.

   **Left as they are**, each passing with one host fewer: the corpus-wide pins that walk
   `data/dossiers/` (the EV-gap sigma and dispersion pins among them: MVST's page printed no sigma
   line, so they lose no coverage), and every test that names MVST only in a docstring, a comment,
   a constructed input, or a committed fixture of its filings, companyfacts or CIQ cells. Those
   fixtures are test corpora, and #1039 and #1027 add more MVST filing text the same way.
   One network pin is left as well: `test_primary_source`'s `test_primary_source_assembly_mvst_live`
   reads `data/dossiers/MVST/dossier.json` and the git-ignored `data/manual/ciq/MVST` folder, and
   skips when either is absent. The CIQ folder was gone before this PR, so it already skipped; with
   the page gone too it now always skips. It is outside the offline suite, so it is not re-pointed
   here; it is reported for retirement.
6. **STATE.md.** §2 gains a 3-line claim beside AORT's. In §5.0, row 28's re-export list drops
   MVST and its 2026-11-12 update gains the rebuild's new group 3, and its still-open item
   "`test_primary_source_assembly_mvst_live` broken on main" is struck (it now always skips).
   Rows 27, 30, 41 (three notes), 51 and 54, each left pointing at MVST's page, gain a short note
   that MVST is retired; each dated measurement that names MVST stays as measured. Row 60's
   clause ("MVST retired 2026-11-12: it has no next build") was carried by batch 7 (#1047), since
   fix-log rule 1 keeps row 60 out of fix PRs. §5 below §5.0 is untouched.

## Where the followed names live, and MVST was never one

The brief asked for MVST to leave "the followed / covered list". Searched: `followed`, `covered`,
`coverage`, `universe`, `watchlist`, `watch`, `retire`, `denylist`, `exclude`, in `vinci/`,
`data/`, `frontend/` and `scripts/`, plus `git log -S MVST` and `git log --all -i --grep=retire`.
What a "covered name" is, in code, is written down once: the fact layer's `pages` rule,
`vinci/facts/scope.py`, "committed pages (data/dossiers/*/dossier.json) plus followed names
(data/followed.json)".
- **`data/followed.json`** holds 17 names (LLY, NFLX, UBER, V, GOOGL, TECX, ORKA, AMZN, PARR, WLK,
  NKE, ROST, BURL, TGT, TJX, MNST, MCK). **MVST is not among them, and never was**: it entered
  through the screen, not the follow list. Nothing was removed there.
- **The committed pages** are the other half, and that is where MVST was covered. With its page
  gone, each reader that walks `data/dossiers/*/dossier.json` stops seeing it: `refresh_fleet`,
  the frontend build, and the fact layer's next `pages` ingest (26 names, not 27).
- **The watch list** is the set of live `watch` records, which feeds the monitor (item 3).

## What was left, and why

Each surface below names MVST and is unchanged.
- **The screen and universe snapshots.** MVST is in the security master (`securities.jsonl`), the
  cohort pool, and six screen runs, 2026-07-29 to 2026-10-16. The latest, `2026-10-16-01`, has it
  `out_of_band`: market cap $199.3M against the $300M floor. It is not in the universe snapshot,
  the candidate records or the ranked queue. Each is a dated measurement of the market.
- **Nothing keeps MVST out of a future screen**, exactly as for AORT: no name-level exclusion
  exists, and the operator ruled on 2026-11-05 that the screen holds back no name. If MVST's
  market cap rises past $300M it can rank again, and only the operator's ruling keeps it off the
  shelf. AORT's proposal stands, still not built: a committed `data/retired.json` that `assemble`
  and `precheck` refuse and the queue view tags, never drops.
- **The graph.** `data/graph_coverage.json` carries MVST as one of its 109 focal names (3 edges,
  0 US-listed). It is a dated, model-judged exposure map whose totals count every name, so a hand
  edit would make them false. Its own regeneration decides its population.
- **The fact layer** (shadow; nothing reads it). Both committed manifests
  (`edgar-4f3207f4da9fb71a`, `edgar-e94e051d94ce1985`) hold MVST's companyfacts. They are
  history; the `pages` rule's next ingest selects 26 names, MVST not among them.
- **Monitor days.** `data/monitor/*.json` and their mirrors carry MVST on 9 of the 10 committed
  days, 2026-08-11 to 2026-11-11 (the 2026-07-20 day predates its record). The next day has none,
  and the new pin holds that.
- **The data-quality snapshots** count MVST on each date it had a page. The next `--write` counts
  26.
- **The deployed desk.** No file under `frontend/theme-intelligence/` names MVST or Microvast, and
  neither does the desk's committed source (`vinci/theme_intelligence/config/sources.toml`,
  `taxonomy.toml`), `data/themes/` or the theme universe snapshot. The registry
  (`data/theme_intelligence/registry.db`) is not on this machine and was not read. So no theme
  evidence that mentions MVST was found to keep or drop.
- **The eval panel's frozen selection** (`vinci/evals/synthesis_panel.json`) lists MVST among its
  28 rows and pages at its freeze ref. MVST is not on the six-page panel (BURL, CNXC, LLY, MCK,
  ROST, SMPL). It is a frozen record, and #1030 is editing `vinci/evals/`.
- **Code.** Every MVST mention in `vinci/` is a comment or a docstring but one, found by
  tokenizing every module: `vinci/dossier/render.py:693`, the canonical graph-cohort reason
  "MVST is in the graph but has no US-listed exposed names to price — UNKNOWN". It would print
  "MVST" on ANY page whose graph-cohort reasons fold. No committed page prints it today (0 of 26, and not the frozen MVST page). **Reported, not fixed** — a
  render-text change, out of this PR's scope. `frontend/` JS mentions MVST in comments only.
- **History**: `tests/fixtures/*` (MVST's filing text, companyfacts, CIQ cut cells, impact
  captures), `docs/`, `planning/` and the records.
- **The fix log** (the coordinator's alone). Two rows name MVST's page: E2-D11 ("WERN's and MVST's
  halves wait for their re-exports (strict xfail)") and RBC-D1 (MVST among the pages whose count
  was written at $0). Not edited here. The coordinator's batch 7 (#1047) dropped E2-D11's MVST
  node and marked its MVST half "not fixing: name retired"; RBC-D1 still lists MVST among the
  "$0 count" pages, the coordinator's to annotate as AORT's was.

## Counts that move

- **Pages**: 27 → 26 (`data/dossiers/*/dossier.json`), and the same in `frontend/dossiers/`.
- **Underwrite records**: 8 → 7 live and 5 → 6 archived. The seal's 13 entries stay 13, one key
  renamed. `frontend/scenarios/index.json` keeps 13 entries, with `MVST` → `MVST-2026-07-22`.
- **The freshness watch set**: 7 → 6 names.
- **The rebuild**: 27 → 26 pages; group 3, 5 → 4 pages, $17.28 → $12.84 at last cost.
- **Tests**: 23 failures and 7 new skips resolved; 18 pins re-pointed at the frozen page, 1 at
  the archive, 8 counts moved, 1 path re-pointed, 1 decorator removed, 1 strict xfail deleted,
  1 guard entry and 1 pin added.
  `vinci/` had 0 lines changed.

**HOW VERIFIED.** Every result below is a real run on this change.
- **The full offline suite**, branch against main (`pytest -m "not network"`, CIQ unlinked): main
  0 failed, 292 skip lines; the branch before the test fixes 23 failed, with the 7 new skips above
  and none other from MVST (the corpus-parametrized skips each lost MVST's case). The same run
  over the 77 files that name MVST gave 14 of the 23. The final tree's counts are in the PR body.
  Two pins that skip on main without a built `frontend/snapshots` ran on the branch, because
  `frontend/build.py` built it there; that is the checkout, not MVST.
- **The seal.** `seal.check_all` over the 13 sealable records returns `[]`.
- **The build.** `python frontend/build.py` printed "26 dossier(s)" and "13 underwrite(s)
  [AORT-2026-07-22, …, MVST-2026-07-22, …]". Only MVST's mirrors and the two indexes changed.
- **The mutations.** Each re-pointed pin was run unmutated (all 18 PASSED), then against one
  mutated file, then the file was restored and its sha256 checked:

  | pin | mutation | result |
  |---|---|---|
  | `test_dossier` Brief-snapshot alignment; K6 99.1 fold | `ticker` = null (the page no longer validates) | RED, RED |
  | `test_dossier` return-ratio table | the "RoE %" row relabelled | RED |
  | `test_dossier` ESM render smoke | covenant row 16, "plus 115 bps" → 999 bps | RED |
  | `test_dossier` T2 covenant table | `floating_rate` "SOFR + 9.750%" → "SOFR + 1.000%" | RED |
  | `test_dossier` T3 revision log | `catalyst_path.revision_events` emptied | RED |
  | `test_dossier` T1 provenance tier | accession `0001760689-24-000021` renamed | RED |
  | `test_dossier` P6 cited EX-99.1 bear point | the bear points' EX-99.1 refs renamed | RED |
  | `test_ev_gap_render` suppressed[MVST] | `ev_gap.form` = three-ratio | RED |
  | `test_ev_gap_render` coverage reason | the reason gains TERMINAL | RED |
  | `test_ev_gap_render` margins[MVST] | `margins.ours` = null; the md phrase reworded | RED, RED |
  | `test_ev_gap_routing` routes on coverage; fleet split | EBITDA FY2026 estimates "1/1" → "10/10" | RED, RED |
  | `test_ev_gap_routing` check order | EBITDA FY2026 high 62.078 → 90.0 | RED |
  | `test_filing_wall_and_concentration_roles` plain wall | the panel's instruments emptied | RED |
  | `test_efts_caps_and_instants` seven families | instruments emptied: GREEN (not load-bearing); one `description` = null: RED | RED |
  | `test_labels` | `industry.value` → "Application Software" | RED |
  | `test_r4_machine_proposal`[MVST-2] | `pe_eps_basis.fiscal_years` = null | RED |
  | `test_no_false_unknown`[MVST] (scratch copy) | a typed `covenant_leverage` fact added | RED |
  | `test_record_legibility` freshness pin | MVST's archived record put back live (removed after) | RED |
  | `test_record_legibility` retired-archive guard | MVST's page put back under `data/dossiers/` (removed after) | RED |

  Each restore was byte-identical; the frozen JSON still equals
  `git show 047f4c6b:data/dossiers/MVST/dossier.json`. The sealed archive was only read: its pin
  ran on a scratch copy.

**BOUNDARY.** Every count is on the committed tree at `047f4c6b` (main, 2026-11-12) unless it
names another commit or date. "Pages" means `data/dossiers/*/dossier.json`, 27 at `047f4c6b` and
26 here. "The tests that name MVST" means the 77 `tests/*.py` files that `git grep -l -i
"MVST\|microvast"` lists at `047f4c6b`. The watch set is `_watch_tickers` over `scenarios/*.json`.
The routing split is `route_for` on each page's first EBITDA consensus cell. The screen figures
are run `2026-10-16-01`'s. Costs are #1041's, at last recorded cost, list price.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** No model call, no vendor call, no page rebuilt, no product code changed.
- **The archived card has no banner**, as AORT's has none. Falsifier: a reader takes
  `MVST-2026-07-22` for a live WATCH.
- **MVST can re-enter the ranked queue** if its market cap passes $300M. Falsifier: an assembly of
  MVST started without the operator asking.
- **One strict xfail retired rather than re-pointed.** Falsifier: E2-D11's 'Revenues of' read
  regresses on a release only MVST's page exercised; EPAM's end-to-end pin and the parser's own
  unit pin on MVST's Q2 2026 release text (`test_release_stated_figures`) still cover the read.
