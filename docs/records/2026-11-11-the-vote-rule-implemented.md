---
status: shipped
date: 2026-11-11
prs: [982]
supersedes:
superseded-by:
---

# The vote rule is built (decision path): R1's binomial gate — today's 5-of-5 rule at five draws with every draw completed — counts failed, unparsed and unrecognized draws as dissent and keys two spellings of one lean as one; the split is printed beside every proposal and sealed in the ledger; a failing committed lean reads BORDERLINE; and `log-verdict` seals the proposal from a recorded ten-draw confirmation (R1 at ten). No committed page's proposal moves until it is re-assembled

**THE ASK.** Step 4 of the vote-rule decision (`docs/records/2026-11-10-the-proposal-vote-rule-design.md` §8–§9), from the coordinator after #978 merged, under the operator's 2026-11-11 "go ahead with the correct steps as per experts". The independence the design's tables assume was not falsified (`docs/records/2026-11-11-vote-rule-independence-measured.md`).

**DECISION PATH.** This edits:
- the gate beside the face-validity-frozen mapping (`verdict.py`);
- the synthesis tally (`synthesis.py`);
- the page schema, the ledger schema and its write;
- `log-verdict`.

What does not change:
- The three-row mapping is unchanged, and mixed proposes nothing.
- The LLM still writes no verdict. `Synthesis` gains no field. `DrawAgreement` gains four count and boolean fields, pinned by `test_synthesis_is_the_only_llm_output_and_carries_no_conclusion`.
- No code path approaches execution.

**DOES THIS SELECT ON FORM?** No. The gate reads only the COUNT of draws carrying a lean, never what kind of evidence a filing offers.

## What changed

- **R1** (`verdict.r1_required`, `verdict.draw_gate`, `verdict.DrawGate`): a proposal only if a one-sided exact binomial test says the build's modal committed lean is the majority read, at 5%, over the draws ATTEMPTED. That bar is 5 of 5 at five draws (today's rule) and 9 of 10 at ten.
- **R3**: a failed, unparsed or unrecognized draw counts toward no lean. **§2's first hole is closed.** A five-draw build with one completed draw recorded `unanimous` and proposed. It now reads 1 of 5 and withholds, and a page flag says why.
- **The spelling key** (`verdict.lean_key`, used by the mapping AND the tally): **§2's second hole is closed.** "Strongly bullish" and "strongly-bullish" are one lean.
- **R5**: `DrawAgreement` gains `modal_count`, `required`, `passes` and `rule`. These are counts and a boolean about the draws; the modal lean and the state are DERIVED from them, never stored. The fields are omitted while unset, so two things hold for a page built before the rule:
  - it re-serializes byte for byte;
  - it decides by `unanimous`, as it always did (**C7**; pinned on all 27 committed pages).
- **C(iii)**: proposed / borderline / none, from the gate. Borderline means a committed lean that holds a majority of the attempted draws but sits under R1's bar. The split is printed and no proposal is made.
- **R4**: the split is printed beside every proposal:
  - the markdown proposal line and reproducibility line;
  - the web's reproducibility line (`dossier.js`, `drawGateSplit`, parity-pinned against the markdown through node);
  - the `log-verdict` output.

  It is also **sealed** in a new optional `LedgerEntry.machine_tally`, which holds the page's tally and the confirmation's. The field is omitted while None, so every committed row re-serializes byte for byte.
- **C(iv)** (`vinci/dossier/confirmation.py`; `log-verdict`): before the ledger row is written, two things are read and drawn TEN times through production's `synthesize`:
  - the committed page's mechanical layer as the synthesis received it (`layer_as_synthesized`);
  - the page's transcripts (`page_transcripts`), refused where they differ from the page's input record. A BUILD record is complete, so it is held to its listing even where it lists no transcript.

  R1 at ten decides the sealed proposal.
  - **The decision path never imports the replay harness.** `test_nothing_on_the_decision_path_imports_the_harness` holds. Both readers are the harness's own readings written on the decision path. Tests pin them equal to `evals.capture_child.pre_synthesis_mech` on every committed page, and to `evals.replay.transcript_for` on the pages whose licensed transcripts are on the machine (skipped in CI).
  - **One confirmation per page version** (ticker + `assembled_at`). It is recorded in ONE file, `data/snapshots/proposal_confirmations.jsonl`, whether or not the verdict is then logged. A later log REUSES it, so it is never re-drawn until it agrees. No flag names another record.
  - **A confirmation that learned nothing is refused and NOT recorded.** That covers every draw failing, or more than `MAX_FAILED_DRAWS` = 2 failing (an outage, not a read), so an outage cannot use up a page's one confirmation. Up to two failed draws are R3's dissent.
  - **Every call on file must read.** Production's reader drops a call whose read fails, and the build flags it. LibreOffice fails a conversion while another runs, and GOOGL's Q3 call is an OLE Word document it converts. A call short would seal a read of other inputs for that page version for good, so the confirmation refuses and records nothing. No committed page carries the build's unparsed-call flag (0 of 27), so this blocks none today.
  - **`--dry-run` draws (or reuses) the confirmation**, prints what would be sealed, and writes nothing to the ledger. Every command prints the confirmation it draws or reuses, so a log that REUSES one seals `revealed_pre_verdict`, whichever command drew it.
  - **The record states whether the transcripts were verified** against the page's input record. A BACKFILLED record never lists a transcript, so it (18 of the 27 committed pages), or a page with no record, says UNVERIFIED rather than hide it.
  - **It is this code's request on the page's committed layer.** The record keeps the request's sha256, since `llm_call.log` is not committed and the page's own request cannot be proved from the repository.
- **The extraction version** `2026-11-11.vote-rule` is added, with its web twin. The drift pins are re-pinned (56 modules). `confirmation.py` is classed NOT_EXTRACTION: it seals a ledger row and never writes a page.

## How verified

**THE REAL RUN (paid), as the coordinator required:** one `log-verdict` dry run on a committed page, showing the ten-draw confirmation and the sealed split, with nothing written to the real ledger.

- **The page:** GOOGL, `assembled_at` 2026-11-03T12:46:12.909331Z, extraction version `2026-11-03.ex-lease-share-cut`, sleeve quality. It is a followed name whose verdict is already in the ledger (BUY, 2026-08-28), so a real log would be refused as a duplicate; the dry run returns before that.
- **The command,** from this worktree, with the primary's `.env` loaded for the key:

  ```
  vinci log-verdict GOOGL --verdict BUY --twin "dry run" --thesis "dry run" --kill "dry run" --horizon-days 180 --confidence medium --edge-basis watchlist --edge-note "a dry run of the vote rule confirmation; nothing is logged" --dry-run --ciq-root /Users/mac/Documents/GitHub/mosaic-theory/data/manual/ciq
  ```

  A first attempt with `--edge-basis variant-expectation` was refused by the edge-basis gate, before any draw: GOOGL's page states no total EV gap. `watchlist` is the honest basis for a run that logs nothing.
- **The output** (the paid run, 2026-11-11 08:44–08:58 IST; the xls reader's sector-size warnings are omitted):

  ```
  machine proposal for GOOGL: none — evidence two-sided (mixed) — the human's call
  machine proposal (C(iv), R1 at 10): none — 8x mixed, 2x strongly-bullish of 10 draws (the 9-of-10 rule)
    the page's own build: {'attempted': 5, 'completed': 5, 'labels': {'mixed': 4, 'strongly-bullish': 1}, 'unanimous': False} (recorded before the vote rule)
    the confirmation: drawn 2026-11-11T08:58:34+0530, model claude-opus-4-8, request sha256 2c8e28fb647da485; recorded in data/snapshots/proposal_confirmations.jsonl
    its transcripts: UNVERIFIED — the page records none (built before input records), so today's files were read
  dry run: nothing written to the ledger for GOOGL; this reveals the confirmation's proposal, so a later log of this page seals it as revealed
  ```

- **What it shows:**
  - ten draws were made through production's `synthesize`, every one completed;
  - R1 at ten needed 9 and the modal lean held 8;
  - the lean is `mixed`, which proposes nothing, so the state is **none**, not borderline;
  - the sealed proposal is none, as is the page's own (4 mixed, 1 strongly-bullish of 5).

  The recorded row carries draws 10, labels {mixed 8, strongly-bullish 2}, modal_count 8, required 9, passes false, state none, proposal null, dry_run true, transcripts_verified false, and the full request sha256 `2c8e28fb647da4855b0216cf7c8313a5f590cab59488ce70748be5af3f64ed79`.
- **Nothing was written to a ledger.** Counts after the run:
  - this worktree's `data/vinci.db` (created by the command): 0 `decision_ledger` rows;
  - the primary's `data/vinci.db`: 9 rows before and after, mtime unchanged (Nov 10 18:15);
  - the committed `data/snapshots/decision_ledger.jsonl`: sha256 `43d77c50a3d4c48f…` before and after, 7 rows.
- **Two defects the run found, fixed before the PR, each behind a test shown failing first:**
  1. **The page's own build printed as a raw Python dict.** Every committed page is built before the rule, so this is the line the human reads at every log. It now reads its labels and the rule that page decides by (`_pre_rule_split`; `test_a_page_built_before_the_rule_prints_its_split_not_a_dict`).
  2. **"UNVERIFIED — the page records none (built before input records)" was false for GOOGL.** Its page has an input record, a BACKFILL, which never lists a transcript. Checking the corpus behind it found a real gap. A BUILD record is complete (every export the bundle held is listed), yet the check compared only where a transcript was listed, so a transcript added to TECX's folder since its build would have been drawn on, unverified. The check now holds a build record to its listing even where it lists none, and the line states the backfill case (`test_a_transcript_added_since_a_complete_build_refuses`, `test_a_complete_build_that_read_no_transcript_is_verified_on_an_empty_folder`, `test_a_backfilled_record_reads_unverified_and_says_why`).
- **The transcript check, on the corpus** (all 27 committed pages, against the licensed folder on this machine, at this PR's head): 9 verified (the 9 build records), 18 unverified (the 18 backfills), 0 refused. **It can fire on real files:** a copy of MCK's folder with its Q1 FY27 call removed was refused — "transcripts on disk ['… Q2 2027 Earnings Call, Nov 04, 2026.rtf'] differ from the page's input record […] (names or sha256)". The copy was deleted afterwards.
- **The same dry run, re-run after those fixes ($0, nothing drawn):** the record was unchanged, so the confirmation was REUSED, and the last two lines now read:

  ```
    the page's own build: 4x mixed, 1x strongly-bullish of 5 draws (recorded before the vote rule; that page decides by unanimity: not unanimous)
    the confirmation: reused, recorded 2026-11-11T08:58:34+0530, model claude-opus-4-8, request sha256 2c8e28fb647da485; recorded in data/snapshots/proposal_confirmations.jsonl
    its transcripts: UNVERIFIED — the page's input record cannot say which it read (a backfill lists no transcript, or there is no record), so today's files were read
  ```

  The ledger counts and sha256 were unchanged again.
- **The demonstration's record row is not committed.** An artifact never rides a code commit, and this row was drawn in a worktree. It is kept with the three outputs in the session family's notes folder (`vote-rule-step4/`), outside the repository. Removing it here means GOOGL's 2026-11-03 page version has no recorded confirmation on main. GOOGL is already logged, so no real log of it can follow.

**THE FIRST FULL GATE FAILED TWICE (2026-11-11, on the tree squashed onto main `2b9b766c`); both are resolved before the commit:**
- **`test_quality_prices::test_the_all_clear_checks_fire_on_a_perturbed_live_series`** crashed on an EMPTY `data/vinci.db`. The dry run had created it in this worktree, where the test otherwise skips ("no data/vinci.db — the store is git-ignored"). The file held only its schema (`meta`, 1 row; 0 ledger rows) and was removed; the test skips again. That the test crashes on an empty store rather than skipping is reported as a one-line follow-up, not fixed here.
- **`test_the_transcripts_are_read_as_the_replay_harness_reads_them` failed on GOOGL**, though it passed alone after the merge. One of its two reads lacked the Q3 call. That call is an OLE-disguised Word document converted by LibreOffice, which fails a conversion while another runs (the reader's own note, RA-D11), and other sessions' gates were converting at the time. Two consequences:
  - **The confirmation now refuses when a call on file does not read** (above; `test_a_call_that_does_not_read_refuses_rather_than_draw_on_fewer_calls`, shown failing first, beside `test_every_call_that_reads_is_drawn_on`).
  - **The parity test shares one read per file**, so it compares the readers' code, not two conversions.
- **The paid run drew on both calls.** Rebuilt at $0 with a scripted client, GOOGL's request sha256 is `2c8e28fb647da485…` with both calls (114,742 characters) and `aec784c750ddcb92…` with the Q2 call alone (57,443). The paid run's recorded sha256 is `2c8e28fb647da485…`. The sha the record keeps did the audit job it was kept for.

**FAIL-FIRST.** Run against main `e73e7a54` (a `git archive` of it with the two new test files copied in), every test fails or errors except the backward-compatibility guards:
- `test_vote_rule.py`: 19 failed, 2 passed. The 2 are `test_an_old_tally_serializes_as_it_was_written` and `test_an_old_page_renders_as_it_did`, which pin that what was built before the rule is unchanged.
- `test_vote_rule_confirmation.py`: 17 errored at setup, since `cli._confirmation_record` does not exist on main.

The tests added after that run (the sleeve default, the pre-rule print, the transcript completeness check) were each shown failing on the line they fix.

**THE SUITE.** ruff and `mypy --strict` (206 files) are clean. The targeted suites pass, 495 passed and 18 skipped: the vote-rule tests, the drift pins, the harness-import guard, the four `getsource` tests a mid-edit run had reddened, `test_synthesis_draws`, `test_dossier` and `test_state_identifiers`. The full offline gate (`bin/commit`) is run before the commit.

## Review round 0 (`/code-review high --fix`, before the PR)

Nine findings. **Seven are FIXED**:
- six behind a test (1, 2, 3, 4, 7, 9). Finding 9's test was shown failing on the pre-fix line (`UnknownSleeveError`); it is latent, since all 27 committed pages record a sleeve;
- one a wording fix (6), made identically in both version tables and held by the drift pins.

**Two are DEFERRED** (5, 8, below). They are listed one by one in the PR's Review dispositions table. Two of the seven are worth naming here:
- **Finding 4 is the outage rule.** Before the fix, a run with most draws failed was recorded as dissent and used up the page's one confirmation.
- **Finding 3 removed `--confirmations`.** With it, a caller could name a fresh record and re-draw the confirmation until it agreed.

The pre-check full suite also caught the decision path importing the harness, through the first draft of `confirmation.py`. It was fixed by the two production readers above.

## Found, not fixed / follow-ups

- **#978's two deferred Codex findings,** in the frozen independence scorer (`vinci/evals/independence.py`), for its next version:
  - an unknown first-draw cache state (`first_draw_cache_read` None) reads as "not uncached" and silently leaves the exact test; it should read UNKNOWN;
  - a runs test with no variance prints z 0, p 1; it should read UNKNOWN or be suppressed.
- **Review finding 5:** the paid confirmation runs before `log_verdict`'s own refusals (the entry price, its staleness, a stated limit, a duplicate row). A refused log can therefore still spend ~$4. There is no integrity loss: the confirmation is recorded, and the next log reuses it and seals it as revealed. Moving it after those gates means splitting `log_verdict`, which belongs in its own PR.
- **Review finding 8:** the page is read twice in one command (`_sealed_proposal` and `_confirm_seal`). On a page without a synthesis, "machine proposal: none" may read like a withheld proposal. Cosmetic.
- **The harness mirror `compare._proposal` is unchanged.** It is in the scorer's fingerprint (`SCORER_FILES`), and editing it would orphan every registration already scored. At five draws with every draw completed it decides as R1 does.
- **The lean key and the known-lean set are still copied** in `independence.py` and `run_metrics.py` (the review's deferred item 7 on #978). `verdict.lean_key` is now the one to read.
- **A page's own proposal keeps today's five-draw instability** (the decision's accepted risk, §9). Only the sealed proposal is a ten-draw one.

**BOUNDARY.** The draw counts (10 attempted, 10 completed, 8 / 2) are ONE confirmation of ONE page version: GOOGL, `assembled_at` 2026-11-03T12:46:12.909331Z, drawn 2026-11-11 08:44–08:58 IST on `claude-opus-4-8` at this PR's code, on 114,742 characters of transcript (its two calls in the licensed folder, unverified). The ledger counts are rows of `decision_ledger` in each DB, and lines of the committed snapshot, read before and after each run. The corpus counts (9 / 18 / 0) are all 27 committed pages under `data/dossiers/`, read at this PR's head against the licensed folder on the primary checkout. The fail-first counts are the two new test files on main `e73e7a54`.

**WHAT IT COSTS / WHAT IS ACCEPTED.** - **This PR's paid spend: one ten-draw confirmation, NOT metered by this code.** `confirm` does not record its calls' cost; that is a follow-up below. The estimate is ≈ $4.03: step 3's 24 ten-draw builds on the same model cost $96.70, a mean of $4.03 a build (`docs/records/2026-11-11-vote-rule-independence-measured.md`; GOOGL was not on that panel). The reuse runs and the refused attempt drew nothing.
- **Accepted, as decided (§9):**
  - a page's own proposal keeps the five-draw instability;
  - each logged verdict costs one ten-draw confirmation (~$3–4), once per page version.
- **Accepted, new here: the confirmation record is a file in the checkout that runs `log-verdict`.**
  - **The cost:** reuse holds only where that file is. A log run from another checkout before it is committed would draw again.
  - **The operator's step:** commit `data/snapshots/proposal_confirmations.jsonl` beside `decision_ledger.jsonl` after a real log. No runbook step commits either today.
  - **The falsifier:** two rows for one ticker and `assembled_at` in the committed record.

**FOLLOW-UPS ADDED BY THE RUN:**
- `confirm` should seal each confirmation's list-price cost in its row (`graph.llm.cost_usd` over each call's usage, null when a call left none), so the per-verdict cost is a measured series rather than the design's estimate.
- A runbook step should commit the confirmation record with the ledger snapshot.
