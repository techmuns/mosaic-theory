---
status: shipped
date: 2026-11-09
prs: [938]
supersedes:
superseded-by:
---

# AORT (Artivion) is retired from coverage: its page and mirrors leave the corpus (28 → 27 pages), its 2026-07-22 WATCH record is archived intact and stays sealed, and the pins on its page read a frozen copy

**THE RULING.** The operator, 2026-11-09, verbatim: *"retire AORT fully"*. It answered the offer
"retire it fully: archive its page and scenario so its history stays in git, take it off the
research desk, move any tests on its page to frozen copies, and mark its fix-log rows 'not fixing:
name retired'". AORT's CIQ folder is no longer kept.

## What moved

1. **The page leaves the tree.** `data/dossiers/AORT/dossier.json` and `dossier.md` are deleted.
   The page's `llm_call.log` was never committed: `.gitignore` drops `data/dossiers/*/llm_call.log`.
   The primary checkout still holds AORT's (35 bytes, 2026-07-01), and a pull does not remove an
   ignored file, so `data/dossiers/AORT/` stays there as a folder with no page in it. Every reader
   keys on `dossier.json`, and so does the retired-archive pin below. **Operator: delete that
   folder by hand if wanted; nothing in git holds it.** `python frontend/build.py` then dropped
   `frontend/dossiers/AORT.json` and `.md`, and AORT's four entries in
   `frontend/dossiers/index.json` (`tickers`, `labels`, `reads`, `sleeves`). The build moved
   nothing else.
   - **The last commit holding the live page is `6fbbb4a2`** (#936, main on 2026-11-09). Read it
     with `git show 6fbbb4a2:data/dossiers/AORT/dossier.json`. The page was first committed at
     `5f52adea` (2026-06-26), assembled last on 2026-10-26, and 110 commits touched it. Its JSON
     last changed at `eac82b7f` (2026-11-05) and its markdown at `6fbbb4a2`.
   - **Deleted, not archived in the tree, and why.** No dossier archive exists to follow. Searched:
     `git log --all -i --grep=retire` (the retirements R1–R3, #905/#908/#910, removed code and data,
     never a page), `--grep` on "archive" and "dossier", `git log -S` on an archive path, and
     `find -iname '*archive*'`. The one archive directory is `scenarios/archive/`, which is for
     underwrite records. The one in-tree copy of a page is a test fixture under
     `tests/fixtures/frozen_pages/`, which tracks no page. A copy kept under `data/dossiers/` would
     be read by every reader that walks that folder: `frontend/build.py`, the fact layer's `pages`
     rule, and the corpus tests. Git history keeps the page, and the frozen copy keeps what the pins
     read.
2. **The underwrite record is archived.** `scenarios/AORT.json` moved to
   `scenarios/archive/AORT-2026-07-22.json`, byte-identical (a 100% rename).
   - The key is `scenarios.archive_key`'s `<TICKER>-<underwrite_date>`. AORT was underwritten on
     2026-07-22, a WATCH at $25.37.
   - **No ledger row names AORT**: 0 of the rows in `data/snapshots/decision_ledger.jsonl`. No
     ledger, scoring or monitor file was touched.
   - **The seal moved with it.** The manifest entry moved from key `AORT` to `AORT-2026-07-22`,
     with chars 687 and the sha256 unchanged. It was made through the edit tool, so the
     decision-path hook asked the operator. `seal.check_all` over all 13 sealable records reports no
     violation. The record's move was a `git mv`, which the hook does not see; it is a 100% rename.
   - **Its mirror.** `frontend/scenarios/AORT.json` became `AORT-2026-07-22.json`, and the index
     lists the archive key. The card is byte-identical but for one line, "next evidence": the live
     card read AORT's page's catalyst calendar ("Next results print", 2026-11-05), and with no page
     it reads `UNKNOWN`, "no scheduled evidence", "none on file".
3. **Tests.** Measured, not predicted. The full offline suite was run with the page and the record moved
   (CIQ unlinked, on `6fbbb4a2`). It gave **21 failures and one new skip**, every one from AORT's
   absence. The skip was `test_dossier`'s operating-drivers render, which skips without AORT's page.
   A second new skip was missed by that count and found in review (below). Each is now one of six
   things:
   - **13 pins read the frozen page** at `tests/fixtures/frozen_pages/2026-10-26/AORT/`. Its
     `dossier.json` and `dossier.md` are byte-identical to `6fbbb4a2`'s page, and their row is in
     that folder's README. The pins, by file:
     - `test_ev_gap_render`, 4: the TEV stamp; the suppressed name's total with no shape label; the
       TERMINAL/NEAR-TERM reason; the two margins as figures.
     - `test_refresh_fleet_and_bridge_guards`, 2: never "BLENDED"; the EV gap's TEV vintage.
     - One each in `test_maturity_wall_unstated` (the left-out instruments by type),
       `test_r4_machine_proposal` (condition 3 on "0 of the trailing"), `test_efts_caps_and_instants`
       (AORT's agreement families among the seven), `test_freshness` (the panel-age note),
       `test_evals_panel_and_stats` (AORT's frozen panel row; the frozen blob is the panel's
       `1ec36425`, so the row is still checked), `test_rebuild_keeps_committed_recipe` (AORT's
       erased `R2_NEEDED` re-tag, replayed on its page) and `test_dossier` (the operating-drivers
       host; it skipped and now runs).
   - **One pin reads the archived record**: `test_horizon_and_irr_gate`'s IRR on the nominal value,
     a real R2 record, via `sc.read_archived("AORT-2026-07-22")`.
   - **Six counts move, logic unchanged**:
     - `test_scenarios` ×2: exactly 9 → 8 live records;
     - `test_basis_equivalence`, `test_horizon_and_irr_gate` and `test_tiered_gates`: at least 9 →
       at least 8 live records;
     - `test_dilution_denominator`: `ANCHORS_AWAITING_BACKFILL` loses AORT, 9 → 8 names. This is
       a retirement, not a backfill, and the comment says so.
   - **One logic change**, `test_record_legibility` (the next section), plus its five negative pins.
   - **A second new skip**, found in review: `test_no_false_unknown`'s
     `test_every_underwritten_name_is_legacy_today[AORT]` skipped with no live record. It now reads
     the archived record, which is still committed.
   - **One pointer**: `test_records_ledger` needed this record to exist.

   **Each moved pin was shown red under one mutation of the frozen value it reads, then restored
   byte-identical** (sha256). The scripts are in the session's scratchpad; their output is in
   HOW VERIFIED.
   - Eleven are value mutations: the TEV stamp made "BLENDED"; `ev_gap.form` set to three-ratio;
     the reason without TERMINAL; the margins phrase and `margins.ours` (two mutations); the EV
     gap's `tev_as_of`; `pe_eps_basis.fiscal_years` set to null; `mechanical` emptied for the panel
     age; a sleeve flip on the panel's frozen AORT row. Two more were made on **scratch copies** of
     the archived record: `years_to_terminal` set to null, and a typed `covenant_leverage` fact
     added. The sealed file itself was never written.
   - Four pins host behaviour on AORT's page and pin no AORT value: the maturity-wall note, the
     operating-drivers render, the re-tag replay, and the efts families. They went red when the
     page stopped validating (`ticker` null, or one instrument's `description` null).
   - For the efts pin, **emptying AORT's instruments leaves it green**. MVST and WERN alone supply
     its seven families, so AORT's instruments are not load-bearing there. Stated rather than
     hidden.

   **Left as they are**, each already passing one host fewer:
   - `test_known_wrong_marker` loops SMPL/AORT/FUBO with `continue`;
   - `test_staleness_split` asserts a subset, {MVST, AORT, TECX, BRBR};
   - `test_cap_drift_render`, `test_share_basis`, `test_segment_facts`, `test_trigger_state_surface`,
     `test_quality_checks_that_can_fail`, `test_store_freshness`, `test_drawdown_filing_index_unavailable`,
     `test_parity_pins` and `test_ciq_reader_contract` name AORT only in docstrings, comments,
     constructed inputs or committed XBRL fixtures, and none failed.
   - The tests that read AORT's **CIQ workbook** (`test_no_backfill`, `test_consensus_rows[AORT]`,
     `test_guidance_point_refusal`'s V/AORT/CNXC candidates and others) skip wherever the folder is
     absent. With the CIQ folder linked they now skip for AORT too, because its folder is no longer
     kept. That happened before this PR, by the operator's hand. Order 10 of the fix request asks
     for retiring or re-basing tests whose committed data is gone. These are such tests, and they
     are reported here, not changed.
4. **STATE.md.** AORT leaves every §5.0 to-do that named it, and each row keeps its other items:
   - row 28: the re-export list, the "AORT too… its full set after its Q3 10-Q" sentence (struck),
     and the old-style-comps copy-in list;
   - row 32 (28): the operator's "re-pull AORT's Financials" (struck);
   - row 59: "SEVEN PAGES" → "SIX PAGES" with no customer count; AORT's precheck clause; RD-D1's
     page list;
   - row 60: order 2's paid rebuilds, twelve → eleven;
   - rows 10, 34 and 41, each waiting on AORT's re-assembly: AORT leaves row 10's list of
     uncaveated stored claims; row 34's interest lead (a 2026-10-28 measurement) and row 41's
     G-V1 item are marked retired, the G-V1 item moot. Row 41's list of the operator's narrowing
     keeps AORT, marked.

   Dated measurements that name AORT stay as they were measured, in rows 11, 28, 30, 32, 34, 41
   and 55. §2 gains a 3-line claim beside the other retirements. §5 below §5.0 is untouched.
5. **The fix log.** Two IDs name AORT's page: RD-D1 (its goodwill and intangibles are paired at
   different dates) and RBC-D1 (its page prints no customer count until re-assembled). Each now
   reads `AORT not fixing: name retired (operator 2026-11-09)` in its page column, and each status
   is unchanged for the ID's other pages. RBC-D1 stays `in progress (#936)` and RD-D1 stays `open`.
   - The fix-request record gains a dated `## Amendments` entry saying the same. The body of that
     record is unchanged.
   - #936 merged at `6fbbb4a2`. Under the log's rule 3, its three rows (RBC-D1, RA-D1 and RBC-D8)
     may now be flipped to `fixed`. This PR leaves that to the coordinator's sweep, because the
     brief said to change no status and the rows are #936's.

## A retired record has no successor, and the archive was built for supersession

The archive convention of 2026-07-27 assumes every archived record was replaced.
`tests/test_record_legibility.py` pins that every archived record "points forward"
(`superseded_by`). The web's ARCHIVED banner and `frontend/build.py`'s `archiveKey` also key on
`superseded_by`. AORT's record has nothing to point at, and writing a pointer would invent one.
- **What this PR does.** The record moves byte-identical with
  `superseded_by: null`, so no pointer is written. `tests/test_record_legibility.py` names it in
  `RETIRED_ARCHIVES`, beside this record. The "points forward" pin accepts an archive with no
  successor only when four things hold: it is named there, it names no successor, its ticker has
  no live record, and its ticker has no committed page. An archive that points nowhere for any
  other reason still fails. Five negative pins, built on the committed records, show it: one per
  condition, and one for a name listed retired whose record is not archived. **This is
  the one change to a test's logic in this PR.** Proposed, not built: move the list into a
  committed data file that the web and the assembler can read too (below).
- **What the web shows.** An archived record renders and is indexed by design: "ARCHIVED RECORDS
  STAY PUBLIC" (`vinci/scenarios.py`). So `AORT-2026-07-22` appears on the dossier shelf's "First
  analysis" tab, as `SMPL-2026-07-21` does, and opens at `#/dossier/AORT-2026-07-22`. **It carries
  no ARCHIVED banner**, because that banner keys on a successor. PROPOSED, NOT BUILT: a banner
  reading "ARCHIVED — name retired <date>" for an archived record with no successor, read from the
  same marker. That is a render change, so it goes through a Phase-1 preview (PREVIEW RULE). The
  alternative is for `build.py` to leave a retired record out of the index, which would be a
  departure from "archived records stay public" for the operator to rule on.

## What was left, and why

Each surface below names AORT and is unchanged.
- **The graph.** `data/graph_coverage.json` carries no AORT edge or node: 0 matches for "AORT" or
  "Artivion" at `6fbbb4a2`. #937 is regenerating it.
- **The fact layer** (`vinci/facts`, shadow; nothing reads it). Both committed manifests hold
  AORT's companyfacts: entity 0000784199, 16 year files plus its order file, 17 committed parquet
  objects. They are `pages` (`edgar-4f3207f4da9fb71a`, rule "committed pages plus followed names",
  28 selected and 26 ingested) and `screen` (`edgar-6e0e4626855b9fce`). The `pages` rule selects on
  the committed pages, so its next ingest selects 27 names, AORT not among them. The committed
  snapshot is history and is not regenerated here.
- **The screen and universe snapshots.** AORT is in the universe (`universe_snapshot.jsonl`,
  2026-10-16, market cap $1.06bn), the security master, screen run `2026-10-16-01` (NOT_EVALUATED:
  168 P/E points against the 450 the G3 floor needs), `candidate_records.jsonl`, and the ranked
  queue at **rank 78 of 343** (`AORT-screen2-20261016`). Each is a dated measurement of the market.
- **Theme intelligence.** AORT is not on the published desk: no file under
  `frontend/theme-intelligence/` mentions AORT or Artivion. The registry is outside the repo and was
  not read.
- **The data-quality snapshots.** `data/snapshots/data_quality/{ciq,prices,release}/*` count AORT
  on every date it had a page; the latest CIQ card, 2026-11-05, names it 23 times. Each is dated to
  the day it was measured. The next `--write` measures 27 pages.
- **Monitor days.** `data/monitor/*.json` and their mirrors carry AORT on 8 of the 9 committed
  days, every day from 2026-08-11 to 2026-11-02. The 2026-07-20 day predates its record. The
  monitor reads live records only, so the next monitor day has no AORT row.
- **History**: the 2026-10-26 assembly-run snapshot, the screen runs, `tests/fixtures/*` (the
  synthesis gold set, verbatim cases, label and release fixtures, SEC reference files), the eval
  panel's frozen selection (`vinci/evals/synthesis_panel.json`, which lists AORT as one of 16
  eligible pages; AORT is not on the six-page panel), `README.md`, `docs/`, `planning/` and 141
  records.
- **Code.** Every AORT mention in `vinci/` is a comment, a docstring, a `--help` example
  (`cli.py` ×3) or an error message citing history: `assemble.py` ×2 (the 2026-07-30 synthesis
  loss) and `propose.py` ×1 ("AORT already carries this shape"). **No AORT-specific logic exists.**
  This was checked by tokenizing every `vinci/` module and listing each AORT occurrence outside a
  comment or docstring. `frontend/` JS and CSS mention AORT in comments only.

## Nothing keeps a retired name out of the screen

Nothing name-level stands between AORT and the next weekly screen. Searched: `retire`, `denylist`,
`blocklist`, `exclude`, `suppress` and `not pursu` in `vinci/screens`, `vinci/rank`,
`vinci/universe.py` and `vinci/orchestrator.py`, plus `git log --grep`. The universe's filters are a
SIC denylist and a security-type allowlist. `data/followed.json` is opt-in. The operator ruled on
2026-11-05 that mosaic-theory holds back no name (#919, #922, about TeamNostra's hold). So AORT will
rank again, and only the operator's choice not to assemble it keeps it off the shelf.

**PROPOSED, NOT BUILT:** a committed `data/retired.json` (ticker, date, ruling, record), read in
three places:
- `vinci dossier assemble` and `precheck` refuse a retired name unless `--unretire` names the
  ruling;
- the ranked queue view tags the name "retired <date>" and does not drop it, so the screen still
  measures it;
- the archive invariant above reads the same file.

Dropping the name from the screen is not proposed. It would select on coverage history, and the
screen's job is to measure the market.

## Counts that move

- **Pages**: 28 → 27 (`data/dossiers/*/dossier.json`), and the same in `frontend/dossiers/`.
- **Underwrite records**: 9 → 8 live and 4 → 5 archived. The seal's 13 entries stay 13, one key
  renamed. `frontend/scenarios/index.json` keeps 13 entries, with `AORT` → `AORT-2026-07-22`.
- **STATE.md**:
  - row 59: seven → six pages print no customer count;
  - row 60: order 2's paid rebuilds, twelve → eleven;
  - row 28: the re-export list, eleven → ten names.
- **The fix log**: 2 rows annotated (RBC-D1, RD-D1), with 0 statuses changed.
- **RG-D19**, the ruling STATE row 60 asks for, measured on `622786a2`'s 28 pages: AORT carried
  16 of the 384 following-context passages, 11 of the 853 Key Developments quotes and 0 of the 42
  transcript quotes. Without it: **368 / 842 / 42**. Row 60 is left as measured.
- **Tests**: 21 failures and 2 skips, resolved as above. 15 pins moved and 6 counts moved. 1 guard
  is widened, with 5 negative pins added. `vinci/` had 0 lines changed.

**HOW VERIFIED.** Every result below is a real run on this change.
- **The full offline suite, three times** (`pytest -m "not network"`):
  1. **Before the test fixes**, CIQ unlinked, on `6fbbb4a2` with the page and the record moved:
     9,564 passed, 21 failed, 560 skipped, 8 xfailed. Those are the 21 failures and 2 new skips
     resolved in §3.
  2. **CIQ-linked**, with the primary's `data/manual/ciq` linked (36 tickers, none of them AORT),
     on this change before the review's fixes: 10,041 passed, 6 failed, 103 skipped, 8 xfailed. The
     files the review changed were then re-run linked: 125 passed, 0 failed.
     **The 6 fail identically on clean `6fbbb4a2` with the same folder.** They are:
     - V's estimate years (`test_estimate_year_derivation[V-want3]`);
     - UBER's EV bridge (`test_ev_bridge`; it named AORT on 2026-11-04, STATE row 32);
     - GOOGL's and LLY's Consensus-vs-Trends spreads (`test_forward_consensus`, row 32);
     - `test_forward_multiple_history`;
     - `test_share_basis`'s bridged name.

     Each export was re-pulled after its page was built. **None of the 6 is introduced here.**
  3. **The commit gate**, `bin/commit` (ruff, `mypy --strict vinci`, the suite CIQ-unlinked), which
     commits only when green.
     - **Its first run refused** on `test_emit_scenarios_is_deterministic`. Between that test's two
       emits, the `~/Documents` sync (iCloud's File Provider, which manages that folder) left 14
       "`<name> 3.json`" conflict copies in `frontend/scenarios/`.
     - That sync also left 66 "` 2`" copies in `frontend/dossiers/` and `frontend/monitor/` after
       the mirror rebuilds.
     - Every copy was untracked and byte-identical to its file, or to HEAD's copy where the file had
       been deleted. All were removed and the gate re-run. The same sync did this to the #891
       session.
- **The seal.** `seal.check_all` over the 13 sealable records returns `[]`. No manifest key lacks a
  record.
- **The build.** `python frontend/build.py` printed "27 dossier(s)" and "13 underwrite(s)
  [AORT-2026-07-22, BRBR, …]". Only AORT's mirrors and the two indexes changed.
- **The mutations.** Each moved pin was run against one mutated file, then the file was restored
  and its sha256 checked. All 15 went RED:

  | pin | mutation | result |
  |---|---|---|
  | `test_ev_gap_render` TEV stamp; `test_refresh_fleet_and_bridge_guards` blended[AORT] | md: the stamp reads "TEV BLENDED as-of" | RED, RED |
  | `test_ev_gap_render` suppressed name[AORT] | `ev_gap.form` = three-ratio | RED |
  | `test_ev_gap_render` TERMINAL reason | the reason lowercases TERMINAL | RED |
  | `test_ev_gap_render` margins[AORT] | the md phrase; `margins.ours` = null | RED, RED |
  | `test_refresh_fleet_and_bridge_guards` TEV vintage[AORT] | `vintages.tev_as_of` = 1999-01-01 | RED |
  | `test_r4_machine_proposal`[AORT-2] | `pe_eps_basis.fiscal_years` = null | RED |
  | `test_freshness` panel-age note | `mechanical` = {} | RED |
  | `test_evals_panel_and_stats` AORT row | the panel's frozen AORT row, sleeve flipped | RED |
  | `test_horizon_and_irr_gate` IRR (scratch copy) | `base.years_to_terminal` = null | RED (`ValueError: … an R2 leg needs years_to_terminal`) |
  | `test_no_false_unknown`[AORT] (scratch copy) | a typed `covenant_leverage` fact added | RED |
  | `test_maturity_wall_unstated`; `test_dossier` drivers host; `test_rebuild_keeps_committed_recipe`[AORT] | `ticker` = null (the page no longer validates) | RED, RED, RED |
  | `test_efts_caps_and_instants` seven families | one instrument's `description` = null | RED (emptying AORT's instruments: green; not load-bearing) |

  Each restore was byte-identical, and the frozen JSON still equals `git show 6fbbb4a2:data/dossiers/AORT/dossier.json`. The sealed archive
  was never written: its two pins ran in a scratch root holding a copy.
- **The guard on a real ignored file.** `data/dossiers/AORT/llm_call.log` was created and
  `git check-ignore` confirmed it is ignored. The widened pin passed. The folder check it replaced
  would have failed. The file was then removed.

**BOUNDARY.** Every count is on the committed tree at `6fbbb4a2` (main, 2026-11-09) unless it names
another commit. "Pages" means `data/dossiers/*/dossier.json`, 28 at `6fbbb4a2` and 27 here. The
RG-D19 shares were re-run on the 28 pages at `622786a2`, the record's boundary. That reproduction
gave 384 following-context passages, 853 Key Developments quotes and 42 transcript quotes over 40
words, exactly as recorded. Its 10-Q bucket read 50 against the record's 49, so its total read 945
against 944. AORT's share is 16 following-context passages and 11 Key Developments quotes, with no
transcript or 10-Q quote, so the off-by-one does not reach it. Without AORT: 368 / 842 / 42.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** No model call, no page rebuilt, no product code changed.
- **The archived card has no banner.** Falsifier: a reader takes `AORT-2026-07-22` for a live
  WATCH.
- **AORT will re-enter the ranked queue** on the next weekly run. Falsifier: an assembly of AORT
  started without the operator asking.
