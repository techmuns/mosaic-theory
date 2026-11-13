---
id:
status: shipped
date: 2026-11-13
prs: [1052]
supersedes:
superseded-by:
---

# Retired: the ranker's unfed LLM cause channel (`vinci/rank/cause.py` and its read), the recipe tagger (`vinci/dossier/tagger.py`) and the R-file segment reader (`vinci/edgar/segments.py`) — no caller; the queue is byte-identical at base and head. The graph extractor and judge, the evals judge and the four one-off page passes stay, each with its live caller

**WHAT.** Issue 1004, lane 4, part A. B's design note (comment 6847522000, "### 4. Retire dead code
and cap spend", operator 2026-11-13: *"yes need to do this reliably"*), as amended by A's
operator-approved reply (comment 6847633111), named the candidates. Each was proved uncalled
before deletion (the proof is below, per candidate). A module with any live caller stays.

| candidate | outcome | why |
|---|---|---|
| `vinci/rank/cause.py` (126 lines), with the ranker's read of `cause_class` | **removed** | its one caller was `vinci rank --cause-file`, never fed: all 343 rows of the committed queue read `unclassified` |
| `vinci/dossier/tagger.py` (159 lines) | **removed** | no caller in code; tests only |
| `vinci/edgar/segments.py` (335 lines) | **removed** | no caller since #910 retired the monitor panels (2026-11-05); `segment_facts.py` reads segment profit from the XBRL instance |
| `vinci/graph/extract.py`, `vinci/graph/judge.py` | kept | `vinci graph-coverage` and `vinci graph-rejudge` write `data/graph_coverage.json` (kept by the operator, #905); the judge was fixed 2026-11-10 (#937, RBC-D9, RG-D16), which proposes a paid re-judge |
| `vinci/evals/judge.py` | kept | excluded by A: `python -m vinci.evals judge` calls `jg.run_half` (`vinci/evals/__main__.py:397`), RG-D9's draw-once claim |
| `vinci/dossier/driver_pass.py` | kept | `tests/stripped_pages.py:77` imports its `_calls_on_disk`, and `passage()` / `rows_with_words()` there read a row's words from the call on disk for 6 test modules |
| `vinci/dossier/transcript_run_pass.py` | kept | `page_transcript` serves `tests/test_transcript_run_guard.py::test_no_committed_synthesis_copies_more_than_12_words_of_its_calls`, the corpus check RG-D19's fixed row cites |
| `vinci/dossier/ciq_reread.py` | kept | fixed 2026-11-11 (RBC-D3, `c2a4d743`); the $0 route by which a CIQ-reader fix reaches a page without a paid re-assembly, live while 15 pages stay frozen on watch |
| `vinci/dossier/inputs_backfill.py` | kept | Workstream B, §5.0 row 48, open; re-runnable by design |

**Which "one-off pass modules" B meant.** B's note names them without a list, and B's diagnosis is
in B's own notes. The four above are every module under `vinci/` whose docstring calls itself a
one-off or a $0 pass over committed pages (`git grep -i "one-off"` over `vinci/`, `*_pass.py`, and
the writers `layer_refresh` records). None is retired.

**The ranker change (decision path).**
- Removed:
  - `vinci rank --cause-file`;
  - `rank_candidates(annotations=)`, `rank_candidate(cause_class=)`, and `character_axis`'s
    cause parameter, with its two branches and their constants `_CHAR_STRUCTURAL_BREAK` and
    `_CHAR_MEAN_REVERT`;
  - the orchestrator's cause carry-forward: `carry_forward_assessment` now returns the structural
    flags alone, `rank_from_snapshots` takes no annotations, and `refresh_queue`'s result loses
    `carried_cause`, which was always 0;
  - the summary line's "LLM cause annotations: 0".
- Kept, as constants: the queue's `cause_class` field (always `unclassified`), the `CauseClass`
  enum (so an old queue still parses), and the character label's "· LLM: —" suffix. They are the
  committed queue's format. The frontend's ranker view reads that label, and `ranked_queue.md`
  prints it. Dropping them would move all 343 rows, the md table and the frontend mirror, so it
  is a separate decision (a follow-up).
- **This reverses the 2026-11-04 decision** recorded in
  `2026-11-04-retire-calls-graph-tests-scale-backfill-triage.md`: "The ranker's cause slot
  (`vinci/rank/cause.py`, `cause_class`) stays and is unfed". The operator's 2026-11-13 approval
  of B's design, which names "`rank/cause.py` with the ranker's read of its inert field", is
  what this rests on.
- **The decision-path hook does not ask for `vinci/rank`.** `.claude/hooks/decision_path_guard.py`
  leaves out "screens and the ranker" on purpose: they are governed by the real-run-before-merge
  rule. So no operator prompt fired, and the real run is below.

**Other edits forced by the removals.**
- `tests/test_extraction_version_drift.py` drops the two removed modules from `NOT_EXTRACTION`.
  `--repin --refactor` deleted `segments.py`'s pin and re-pinned `vinci/rank/ranker.py`, whose
  code moved with no page value changing.
- Fix-log row RE2-D15 keeps `fixed` (`670a784c`, #969) and now names the removal pin, as #964's
  rows did for `vinci/ciq/`.
- `docs/engineering.md`: the two lines that named the cause classifier as a live LLM call.
- `tests/test_dilution_denominator.py` and `vinci/edgar/segment_facts.py`: one docstring line each
  that named a removed module.
- `tests/test_rank.py`: three mypy errors that predate this PR, in a file it touches (RUNBOOKS §e).
- New: `tests/test_retired_modules.py`.

**Left alone, on purpose.**
- `vinci/dossier/anchor.py` (lines 349, 1225, 1743) and `vinci/dossier/assemble.py:762` still say
  "the tagger" in docstrings. The recipes are B's lane (3a, 3b), so they are not edited here.
- `tests/fixtures/impact/pr953.json` names `vinci.dossier.tagger` twice. It is a frozen report of
  #953's impact run, and no test recomputes it.
- The records of the removed modules keep their bodies.
- **Not on B's list:** `vinci/dossier/dilution.py` has no importer outside its tests
  (`tests/test_dilution_denominator.py`). Reported, not touched.

**WHY.** Operator, 2026-11-13, on B's design: *"yes need to do this reliably"*. Dead code costs
review surface and suite time on every change near it. `cause.py` was also the one LLM path that
could reach a rank score: a `--cause-file` label demoted or boosted the character axis. After this,
nothing under `vinci/rank` imports an LLM client, and a pin holds that.

**THE PROOF, PER CANDIDATE** (at `b207c8a9`, 2026-11-13 08:40–08:47Z, before any deletion; `git grep -i -E` over every tracked text file; `git log --all`). "Importers" is an AST walk of every tracked `.py` file
(`import`, `from … import`, relative imports and the package `__init__` they load), plus a sweep
for `importlib` / `__import__` / `pkgutil` / `runpy`. CLI entry points: `pyproject`'s one script
(`vinci = vinci.cli:main`) and the five `__main__` modules (`vinci`, `vinci.evals`, `vinci.facts`,
`vinci.impact`, `vinci.theme_intelligence`). Workflows: all five under `.github/workflows/`.

`vinci/rank/cause.py`:
- **House term**, `rank[./]cause`: 10 hits in 9 files. Those are STATE.md, `docs/engineering.md`,
  four records, `tests/test_extraction_version_drift.py`, `tests/test_rank.py` and
  `vinci/rank/__init__.py`. `cause[- ]classif|cause tier|Tier-3 LLM`: 21 hits, all in records,
  docs and the rank package.
- **Plain words**, `de-?rating cause|cause of (a|the|each) … de-?rating`: 6 hits. One is in
  `vinci/dossier/schemas.py`, about a release's cause, an unrelated sense.
- **Symbols.** `classify_cause|parse_cause_reply|annotations_from_raw|load_cause_annotations|CAUSE_TOOL|_CAUSE_SYSTEM|classify_derating_cause`
  has 31 hits: `vinci/cli.py` 2, `vinci/rank/__init__.py` 6, `tests/test_rank.py` 11,
  `docs/engineering.md` 1 and the module itself. `cause[-_]file` has 8 hits: `vinci/cli.py` 4, an
  orchestrator docstring, a test message and two records. `cause_class|CauseClass` has 408 hits,
  343 of them the committed queue's rows.
- **`git log --all -i --grep`:** `cause tier`, 0 commits; `cause[- ]class`, 1 (`8c5e7345`,
  2026-11-11, which corrected `docs/engineering.md`'s note on it).
- **`git log --all -S`:** `load_cause_annotations`, 1 (`d9e2956c`, 2026-06-19, the ranker's first
  commit); `classify_cause`, 2 (the same, and `8c5e7345`); `cause_file`, 2 (`d9e2956c`, and
  `01050694`, #501).
- **Importers:** `vinci/rank/__init__.py:9`, a re-export; through it, `vinci/cli.py` for
  `vinci rank --cause-file`; and `tests/test_rank.py:36`. `vinci/orchestrator.py` read `cause_class`
  back from the prior queue. No script, workflow (the weekly job is one `run_weekly` call), frontend
  file or string import.
- **Committed data:** `data/snapshots/ranked_queue.jsonl`, 343 of 343 rows `"cause_class":"unclassified"`
  and the character label ending "· LLM: —". No cause annotation file is committed.

`vinci/dossier/tagger.py`:
- **House term**, `dossier[./]tagger`: 6 hits, all in tests and `tests/fixtures/impact/pr953.json`.
  `recipe tagger`: 2 (the module and its test). `tagger`: 60 hits in 24 files. The four frontend
  files are "stagger" (false positives). The rest are records, tests, docstrings in `anchor.py`
  and `assemble.py`, and the module.
- **Plain words**, `propose[sd]? a recipe|which recipe fits|recipe proposal`: 6 hits. `vinci/cli.py:1216`
  is the operator re-tag command's help text, not a call.
- **Symbols.** `tagger._leverage|tagger.propose|_margin_shape|_actual_margins|_LEVERAGE_DOMINANT|_RAMP_*`
  has 17 hits. `vinci/audit_r1.py`'s two are its own `check_margin_shape` / `check_leverage`, not
  imports.
- **`git log --all -i --grep=tagger`:** 10 commits. The latest two are `4bba300c` (2026-10-19, the
  lease-basis fix) and `6b42cd32` (2026-10-07, #671, which ran the tagger by hand for its record).
- **`git log --all -S'dossier.tagger'`:** 3 commits: `fb568c7f` (the impact fixture), `4bba300c`
  and `3f509928` (2026-07-21, its creation).
- **Importers:** `tests/test_tagger.py:16`, `tests/test_anchor_point_in_time_shares.py:24` and
  `tests/test_lease_basis.py:529, :745`. Nothing under `vinci/`, no CLI command, no script, workflow
  or string import.
- **Committed data:** only the frozen `pr953.json` report.
- **What goes with it:** it is the only code that proposes `R1_NOT_ROBUST` or `R2` from leverage
  and margin shape. The build's live proposals are the anchor's `recipe_hint` and
  `recipe_proposal.py`'s R4. Not found under the searches above: any other machine proposer of
  those two recipes.

`vinci/edgar/segments.py`:
- **House terms.** `edgar[./]segments`: 17 hits in 8 files. Those are STATE.md's §2 MC2 claim, four
  records, the two test files, and `segment_facts.py`'s docstring. `MC2`: 21 hits. The nine in
  `data/snapshots/assembly_runs/` are a base64 URL fragment (a false positive). `R-files?|rfile`:
  261 hits, chiefly the retired panels' `rfile_note` in committed monitor days. The two in
  `vinci/evals` and `vinci/impact` are `tarfile` (false positives).
- **Plain words**, `segment economics|per-segment operating income`: 232 hits in 44 files: pages'
  prose, monitor days and records. None is an import.
- **Symbols**, `segment_rows|SegmentReportUnavailableError|SegmentRow|_pick_report|_SEGMENT_REPORT`:
  81 hits, only in the module, its two test files, the fix log and five records.
- **`git log --all -i --grep`:** `segment economics`, 4; `MC2`, 5.
- **`git log --all -S`:** `segment_rows`, 5 (latest `670a784c`, #969, RE2-D15);
  `SegmentReportUnavailableError`, 7 (latest `097098f9`, #910, which removed the last production
  caller); `edgar.segments`, 8.
- **Importers:** `tests/test_segment_economics.py` (7 sites) and
  `tests/test_maturity_reader_and_structural_scan.py:141, :156`. Nothing under `vinci/` since
  #910. Fix-log row RE2-D15 itself said "`segment_rows` has no production consumer".
- **Committed data:** `tests/fixtures/segments/` (5 files, used by these tests only, removed) and
  its extraction pin (removed).

**HOW VERIFIED.**
- **The decision-path run: the queue is byte-identical at base and head.**
  - The real `vinci rank` CLI was run over a scratch copy of the committed `data/snapshots`, by
    `b207c8a9`'s code and then by head's.
  - `ranked_queue.jsonl` (343 rows, sha256 `8a1ccd59d04e1f6b…`) and `ranked_queue.md` (69 lines,
    `e601701826062c73…`) are identical, and so is every one of the 97 files in the folder.
  - Stdout differs in one line, which loses "· LLM cause annotations: 0".
  - The weekly path, `refresh_queue(structural=False)`, gives the same result: every file is
    identical at both refs, and equal to the `vinci rank` output. Its result is
    `{ranked: 343, structural_flagged: 69, carried_structural: 69}` on both, with base's extra
    `carried_cause: 0`.
  - Against the COMMITTED 2026-10-16 queue, base's own re-rank already differs, in the
    inform-only `cohort` block of 47 rows (for example peers 172 → 161). That comes from main's
    code and data since 10-16. Every rank, score and axis matches.
- **The first cut of head crashed that run, and a pin now holds it.** `_cmd_rank`'s summary line
  still read `len(annotations)`. The removed local's name then resolved to `from __future__ import
  annotations`, giving `TypeError: object of type '_Feature' has no len()` after ranking. No unit
  test reached the line. `test_vinci_rank_runs_on_the_committed_queue` runs the command end to end
  over the committed snapshots. It reds with that line put back and passes without it.
- **The removal pin finds real callers.** On the base tree, `tests/test_retired_modules.py`'s scan
  finds the importers listed above for all three modules: cause 2, tagger 4, segments 9. It finds
  `vinci/rank/cause.py:27`'s import of `vinci.graph.llm` as the one LLM import under `vinci/rank`.
  Negative pins plant every import form (plain, from, from-package, relative, package `__init__`,
  `importlib.import_module`, `__import__`) and a same-prefix sibling (`vinci.rank.causes`) that
  must not match.
- The gate, the code review and the cross-setup run are in the PR body.

**BOUNDARY.**
- Hit counts: `git grep -c` over every tracked text file at `b207c8a9`, 2026-11-13 08:40–08:47Z,
  case-insensitive; a count is matching lines.
- Commit counts: `git log --all` in this clone at the same time.
- Line counts: `wc -l` at `b207c8a9`.
- The 343 queue rows: `data/snapshots/ranked_queue.jsonl` as committed (the 2026-10-16 screen run).
- The 97 files: everything under a scratch copy of `data/snapshots` at `b207c8a9`, after each
  side's `vinci rank`.
- The 6 test modules: of the 17 files `git grep -l stripped_pages -- tests` lists at `b207c8a9`,
  those that call `passage(` or `rows_with_words(`: `test_driver_evidence`, `test_driver_facts`,
  `test_evals_order8`, `test_model_input_checks`, `test_transcript_run_guard`,
  `test_vote_rule_confirmation`.
- The 47 cohort rows: base's re-rank against the committed queue, compared field by field.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- Restore any module by reverting this PR's squash commit. `git checkout b207c8a9 -- <path>` is
  right only for a deleted path: the ranker, orchestrator and CLI edits must be reverted with it.
- The queue keeps a field and a label suffix that no code varies. That is the price of a
  byte-identical queue; dropping them is offered as a follow-up.
- Falsifier: a build that needs one of the three back within the quarter, or a recipe build
  (lane 3) that wants the tagger's `R1_NOT_ROBUST` / `R2` signals.
