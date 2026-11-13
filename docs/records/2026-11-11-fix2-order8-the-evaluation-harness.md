---
status: shipped
date: 2026-11-11
prs: [1030]
supersedes:
superseded-by:
---

# Fix request 2, order 8 — the evaluation harness: a registration is a committed row on main before it is drawn, and is drawn once across approvals (RG-D14, RG-D9); the gold is checked against its hashes (RG-D11); the scorer is BASE's (RG-D12); M-GAP is reported, never a target (RG-D13); the model is production's (RG-D15); six pages are held out by a fixed rule; each arm is scored against its own layer (STATE row 53 item 6); a test's git refs must be on main (row 56). RG-D10 was already closed by #958. $0; no paid draw; no page moves

**THE ASK.** Order 8 of fix request 2: RG-D9 to RG-D15, with RG-D18 merged separately in #996. Issue #1004 hands over two harness follow-ups: STATE row 53 item 6, and row 56. The order's "done when" from the fix request:
- registration and the gold hashes are checked before any paid draw;
- scoring runs from a fixed scorer;
- held-out pages are named and never used to build metrics;
- M-GAP takes its truth from an independent coding.

The operator's rulings, 2026-11-11, verbatim, relayed by the coordinator:
- (1) **"Committed index on main (Recommended)"**;
- (2) **"Bar it now, tell B on #1004 (Recommended)"**;
- (3) **"6 chosen by a fixed rule (Recommended)"**.

## What changed

- **RG-D14 and RG-D9: the registrations index** (`vinci/evals/registry.py`, `docs/evals/registrations.jsonl`).
  - `register` and `register-run` append the registration's row.
  - `run-compare`, `run`, `score` and `score-run` refuse a registration whose row `origin/main` does not hold. The row is merged in a docs-only PR first, so main's own history shows the registration before any draw. That closes RG-D14: the pre-registration commits had lived on branches that squash merges removed.
  - Each paid draw is a `drawn` row, written before the draw. A comparison is drawn once across approvals. *(Corrected in review round 1, 2026-11-12: keyed on the registration's sha, "once" held per sha, and a new `--note` gives one design a new sha, so a second approval could draw the same design again. The index now keys it on the DESIGN, `compare.draw_key` and `builds.draw_key`; see "Review round 1".)* *(Corrected again in review round 2, 2026-11-12: the CLI passed that key in and the claim trusted it, so a wrong key went unseen. The index now derives the key and the request pins from the registration itself, at the row and again at the claim, and refuses a row that disagrees. One spelling is one design, and one set of request bytes is drawn once too; see "Review round 2".)* A `register-run` registration's builds are each drawn once, all under the approval that drew the first.
  - The judge's read of the gold's TEST half is a `judge_test_read` row, and a second read is refused whichever approval asks. That closes RG-D9, where both rules had held per approval ledger only.
  - The rows hold shas, refs, pages, counts, an approval's sha256 and dates: no path, no text.
- **RG-D11: the gold is the gold its manifest hashed** (`gold.verify_gold`). `load_gold` checks the five files against `MANIFEST.source_sha256`. Each coder file is checked as its two recorded halves, split at the DEV half's 330 claims; all five match today. An edited label is refused before any metric reads it.
- **RG-D12: a fixed scorer, never the candidate's** (`compare.refuse_unless_scored_by_base`, `fixed_scorer`, `refuse_unless_registered_scorer`). The final rule, merging B's scope (operator 2026-11-11: "Yes, take B's tests and close all six") with the retrospective refinement the coordinator accepted:
  - **The production files the metrics borrow** (`synthesis.py`, `mechanical.py`, `verdict.py`, `schemas.py`) must be BASE's bytes, always, for a prospective change and a retrospective alike. A candidate edits these, so a candidate never scores itself through them.
  - **The harness's own files** must be origin/main's at registration, a reviewed harness, recorded as `scorer_ref`. They are never compared with BASE's: a BASE older than the harness, which is any retrospective, would otherwise be refused from every checkout with these rules (B's check, gap 1).
  - **Enforced in the library, not only the CLI** (gap 1). `cm.register` refuses a checkout whose production files are not BASE's, and `run_compare` refuses a scorer that is not the registered one. *(Corrected by B, 2026-11-12, and corrected again in review round 1: the library's `score_run` compared the fingerprint (`_check_run`) but not BASE's production files or the harness at `scorer_ref`, and `run_compare` likewise; since round 1 both run `refuse_unless_registered_scorer` whole.)* The CLI's `refuse_unless_registered_scorer` also re-checks the production files against BASE and the harness against `scorer_ref`, which must be a commit on origin/main.
  - **Twelve existing tests** registered old commits (`dc5b8787` → `b109e26c`) from today's checkout, which is the defect itself. They now stub only the production check, with a docstring pointing at its own pins: `test_evals_pr2.py`, `test_evals_pr2_round2.py`, `test_evals_pr926_round2.py` and `test_evals_replication_rule.py`.
  - **#953 is registered from a composite checkout:** `586fdcfd`'s production files under main's harness. #953 changed `synthesis.py` and `schemas.py` itself, and main's production files have moved since. The composite was proved at $0: this branch's harness imports cleanly against `586fdcfd`'s `vinci/`, and all 12 arms of the impact export load and score there. The PR gives the exact steps.
- **RG-D13: M-GAP is barred as a target** (`compare.BARRED_TARGETS`).
  - `register` refuses it, naming RG-D13.
  - `score` still scores and prints it (`Score.barred`, in `score_text`), and no ship or does-not-ship decision reads it.
  - A registration written before the bar decides on its other targets alone. With no other target, it does not ship.
  - This lasts until an independent coding of the gap types exists.
- **RG-D15: the model is production's** (`capture_child.production_model`). The capture reads `graph_llm_model` from the configuration of the code under test. In `capture_at`'s child, that is the code ref's own configuration. The constant `DEFAULT_MODEL`, a fifth copy of the model ID that no test pinned, is gone. The one model ID left in `vinci/evals` is the judge's own, `judge.JUDGE_MODEL`, pinned: the judge is an instrument calibrated against the gold, and it must not follow production (review round 0).
- **Held-out pages** (`vinci/evals/held_out_pages.json`): NKE, VITL, PARR, WLK, TJX and TGT. TECX and ORKA have no CIQ transcript a replay can read (the panel file's own exclusion), so each is passed over and the rule's next pick takes its place (B's check, gap 5). `python -m vinci.evals gold`, the command a metric change re-runs, scores without them: 136 TEST claims are left out, and it says so.
  - **The rule:** the committed pages outside the panel and outside the gold's DEV half, ordered by the sha256 of the ticker; the first six. The pool of 12 is frozen in the file, so a page added later moves nothing.
  - **A deviation from the coordinator's example rule, on purpose.** The example took the first six of all 21 non-panel pages. That gives NCNO and BRBR, which are gold DEV pages, the half the metrics were built on, and would break "never used to build or tune a metric".
  - A test pins the rule, the set, and their separation from the panel, the gold DEV half and M-GAP's frozen pages.
- **STATE row 53 item 6: each arm is scored against its own layer** (`compare.arm_layer`, `replay.layer_at`, `capture_child --layer-only`).
  - **Before:** both arms were captured with the registered transforms run by their own code, but scored against the committed layer, untransformed, for both. That tilted M-ABSENT's "quote: nowhere" and M-ECHO against CAND.
  - **Now, with transforms:** each arm's layer is rebuilt by its own ref in the same child capture uses, from the inputs the registration recorded, checked by sha256.
  - **Now, without transforms:** both arms keep the committed layer, as before.
- **`register --from-impact <export>`: the #953 retrospective's path** (coordinator, 2026-11-11; the format from impact-check, `impact-captures-format.md`). An impact export holds, per page and arm, a FRESH $0 build at that arm's own code: `built.json`, the `layer.json` its synthesis received, and the `request.json` it sent, each hashed in `manifest.json`.
  - `compare.captured_from_impact` reads it as the comparison: the two commits, and each page's two requests in the panel's order. Every file is checked against its manifest sha256, or refused.
  - `register` records the export's identity (its folder, its manifest's sha256 and every page's hashes) as `inputs["impact"]`.
  - `run-compare` rebuilds the comparison from the same export and checks its manifest's sha256, so the bytes drawn are the bytes captured.
  - `score_run` scores each arm against its own `layer.json`, its own `built.json` page and the transcripts its own request carried (`compare.impact_arm`). This is STATE row 53 item 6 for fresh builds: the frozen page is never read.
- **`vinci/impact/child.py`:** its model fallback read `capture.DEFAULT_MODEL`, which RG-D15 removes. It now reads `capture.production_model()`. A test pins that the child names only attributes the capture module has.
- **Row 56: the git-ref lint** (`tests/test_git_refs_reachable_from_main.py`). Every hex literal a test or the harness hands to git must be a commit `origin/main` reaches. "Handed to git" means three things:
  - a `<sha>:<path>` string;
  - a hex literal in a `["git", …]` argument list;
  - a ref keyword or a ref-taking function's argument.

  Docstrings and comments are provenance and are not checked.
- **RG-D10:** the `run` command was already closed by #958 (`54fa825b`), pinned by `tests/test_evals_run_builds.py::test_a_paid_run_needs_a_registration`. **The library is closed here** (B's check, gap 2). `replay.run_request`, which every paid draw goes through and which G-D10's own reproduction called, refuses with no registration before any client exists, a real `anthropic` client injected included. Callers pass the registration's sha; the judge passes its claimed half.
- **RG-D11 before ANY paid draw** (gap 4): `run_compare` and `run_build` check the gold's hashes (`gold.verify_committed_gold`) before anything else, not only where the gold is loaded.
- **The index's approvals** (gaps 3 and 6):
  - PR 2's 2026-11-06 read of the gold's TEST half is a committed `judge_test_read` row, marked `recorded_after_the_fact`. Its approval sha256 (`3e7cc4be…`) is B's measurement of PR 2's ledger, which lies outside this session's reach and was not re-hashed here.
  - Every `registered` row names its approval's sha256 (`register` and `register-run` need `--budget-ledger`). A draw under any other approval is refused wherever it runs, because the row is on main before any draw.
- **B's tests** (`tests/test_evals_order8_gaps.py`, 11; branch `claude/s1-order8-gap-tests` at `daeba680`) are taken in unchanged. On `7d1761b4`, 10 fail for their gap's own reason and 1 passes by design (the production-edit guard). On this PR, all 11 pass.
- **RUNBOOKS §n** states the new rules.

## How verified

**FAIL-FIRST** (the PR's section D lists every test). The two new test files were run on main's harness code at the merge-base `3d55bc31`, with this branch's files backed up, swapped out and restored byte-identical (15 files). 21 of 25 tests fail. The 4 that pass do so by design:
- the committed-gold guard (the gold is intact on main);
- the three tests of the new lint, which is test-only code with no production half. Its negative pin is the real incident's source.

The failing lines include:
- `DID NOT RAISE ValueError`, for an edited label;
- `assert 'claude-opus-4-8' == 'claude-test-x'`;
- `cannot import name 'refuse_unless_scored_by_base'`;
- the M-GAP case: `target M-GAP does not improve beyond noise (p_lower 1; Holm across 2 target(s))` on a run where M-LABEL fell 15 → 5, so `does not ship`.

**ON THE CORPUS, BEFORE ANY SYNTHETIC CASE.**
- **The gold's five files** equal their manifest hashes; the two coder files split 330/314.
- **The lint, over `tests/` and `vinci/evals/`,** finds 29 refs to 4 commits in 8 files (`a9c59287`, `b109e26c`, `c112f25`, `dc5b8787`), all reachable from origin/main. On `tests/test_evals_round2.py` as merged at `a9c59287`, it finds `4449189d` handed to `in_flight_names` and refuses it: no clone holds that commit.
- **The held-out rule's pool** is 12 of 27 committed pages, measured 2026-11-11 at main `3d55bc31`. None of the six held-out pages is named as a harness target page in any record.

**THE #953 EXPORT, READ BY THIS CODE ($0, read-only, nothing registered).** `captured_from_impact` on impact-check's export (`~/.cache/vinci/impact-captures/pr953-586fdcfd-7ec84833/`, outside every repo):
- The refs are `586fdcfd` → `7ec84833`, the pages are the panel's six, and it reaches.
- The 12 request pins equal the manifest's wire sha256s. LLY's two requests are identical; the other five differ.
- All 36 file hashes match the manifest.
- All 12 arms' layers parse under today's `MechanicalLayer` with NOTHING lost or changed. Today's schema adds only two fields, both `None`: `consensus_context.consensus_levels_note` on all 12, and `capital_allocation.impairment_headroom` on the 6 BASE arms. So scoring an arm under today's schema reads what its request carried.
- Each arm's request carried a transcripts section of the same length at both arms: 60,095 to 123,471 characters with its header. M-ABSENT's transcript split is scored on that section with its header stripped, 59,419 to 122,795 characters (review round 0b).
- `fixed_scorer` takes the retrospective branch, since `7ec84833` is on origin/main. From this branch it refuses, naming the scorer files this PR changes. *(Corrected in review round 1, 2026-11-12: registered from a checkout of main it is refused TOO, because all of `586fdcfd`'s production files differ from main's. It registers from the COMPOSITE checkout, `586fdcfd` with main's `vinci/evals`, `docs/evals` and the gold, which is the path proved at $0 above and the steps in the PR.)*

**THE SYNTHESIS REQUESTS DO NOT MOVE ($0).** Each of the six panel pages' requests was built in-process by main's harness and by this branch's, from the same pages and transcripts, read once and shared. All six are byte-identical by sha256: BURL, CNXC, LLY, MCK, ROST and SMPL, model `claude-opus-4-8`, two calls each.

**THE SUITE.** Every harness suite plus the vote-rule and model-key tests: 326 passed, 14 skipped. ruff and `mypy --strict` (208 files) are clean. The full offline gate (`bin/commit`) runs before the commit.

## Review round 0 (`/code-review high --fix`, before the PR)

Ten findings: seven FIXED, two DEFERRED, one DISMISSED. Each is a row of the PR's Review dispositions table.
- **Fixed by the reviewer, each behind a test:**
  - `run-compare` wrote its `drawn` row before `run_compare`'s own $0 refusals. A refused draw then used up the registration. `run_compare` now takes the claim as a callback, called after its last refusal.
  - `run` claimed a build outside the ledger lock and captured twice. `run_build` now calls the claim under its lock, after its own `prepare_build`.
  - The judge's TEST claim refused its own approval's resume of a stopped run. The approval that holds the read may resume it.
  - The comps and CIQ input hashing was written twice, so the two copies could drift. Both now call `compare._transform_inputs`.
- **Fixed here, behind tests shown failing first:**
  - `register` recorded `--base`/`--cand` as given. RG-D14's own merge moves main between registering and drawing, so a recorded `origin/main` would have been read at a moved main. Both are now resolved to commits.
  - Dropping a barred target from Holm's family loosened the registered correction. A barred target keeps its place at p = 1, its worst case, so its value is never read (`compare.target_family`).
  - The judge's model followed production's. It is pinned as `JUDGE_MODEL`.
- **DEFERRED:**
  - No registration made before this PR can be drawn or scored, because the index starts empty. This is accepted below.
  - `register` does not refuse a held-out page as a target page. That is a follow-up below.
- **DISMISSED:** `register`'s page-limited check cannot fire while M-GAP is barred. It stays as a guard for a future page-limited metric.

## Adopted by B (2026-11-12)

A's usage ran out, and order 8 passed to B (#1004, 2026-11-12 10:52Z; this PR's `## Handover to B`). What B did on top of A's head `2a970f06`:
- **The six gaps are closed, shown by reversal.** B's 11 tests pass on `2a970f06`. Each gap's fix was then reverted on its own, in place, and restored byte for byte. All 13 reversals redden the test that pins them:
  - gap 1: three reversals. `register` skips the BASE check; the BASE check compares the whole scorer; the BASE check compares only the harness.
  - gap 2: two. The registration check is removed; an injected real client is not recognised.
  - gap 3: PR 2's `judge_test_read` row is deleted (both tests).
  - gap 4: two. `run_compare` skips the gold check; `run_build` skips it.
  - gap 5: two. The gold report scores the held-out pages; TECX is held out.
  - gap 6: a draw under another approval is not refused (A's `test_a_registration_is_drawn_only_under_the_approval_it_is_bound_to`).
- **Main `4b2f0cb9` merged in** (`02b41584`), with no textual conflict. One semantic conflict was fixed (`9cd616ba`). RG-D20 case (h), from #1013, asked whether `register` takes M-GAP by constructing a `Registration`, but this PR refuses a barred target in `register` and keeps the constructor accepting it, so that #927's registration loads as history. (h) now reads `BARRED_TARGETS`, and also pins RUNBOOKS §n step 1's "barred as a target" sentence. It fails on `02b41584`, and both reversals are refused: M-GAP unbarred, and main's "joined it" wording with M-GAP barred.
- **Review round 0 by B** (`/code-review high --fix`, five findings):
  - **FIXED, behind tests failing on `306c5ff0`.**
    - A library `run_compare` or `run_build` with no `claim` drew anyway, so only the CLI wrote the `drawn` row after checking main. That is the class of gaps 1 and 2. A paid draw (`replay.paid_draw`: no SDK, or the real client) is now refused unclaimed, after every other $0 refusal and before any folder or client exists.
    - `registry.approval_id` died with an IndexError on an empty `--budget-ledger`, and with FileNotFoundError on a missing one. It now refuses, naming `budget-open`.
    - Reverted, each fix reddens its pin.
  - **DEFERRED**, both listed under the follow-ups below.
    - The library `score_run` has no RG-D12 scorer check.
    - `run_request`'s RG-D10 guard admits any registration string.
  - **NO CHANGE:** a `drawn` row reaches main only with a later PR. That is the accepted risk stated below.

## Review round 1 (the coordinator's review at `7073ea09`, 2026-11-12)

The coordinator's independent reviewer confirmed:
- B's 15 gap tests;
- the six held-out pages, and the 136 TEST claims the gold report leaves out;
- that RG-D12 at score time was CLI-only, and that no non-CLI caller reaches the paid or score paths today;
- 1,463 passing tests across the evals, RG-D20, git-ref, STATE and impact suites;
- gap 1's composite for #953.

It found eight items. One commit answers them. The tests are `tests/test_evals_order8_round1.py`: every FIX test fails on `7073ea09`, and every PIN names the mutant it kills.

- **1. FIXED: a DESIGN is drawn once across approvals.**
  - **Reproduced:** `shop.py`; `test_a_design_is_drawn_once_across_approvals_whatever_its_note`.
  - **The defect.** The index keyed "drawn once" on the registration's sha, and a new `--note` gives one design a new sha. So a second approval could re-register a drawn design and draw it again: result shopping past the replication rule.
  - **The fix.** Every `registered` row carries its design key, and `registry.claim_draw` refuses a registration whose design any other registration has drawn, reading the index in this checkout and on main.
    - `compare.draw_key` is the `DESIGN_FIELDS` plus the replication link.
    - `builds.draw_key` is everything but the note and the recorded inputs. A `RunRegistration` has a `note` too, so `register-run` had the same hole.
  - **The replication rule's one other draw** names the run it replicates, so it is a design of its own, drawn once too (`test_a_replication_is_its_own_design_and_is_drawn_once_too`).
  - **A row with no design** is refused at the claim, never read as a design of its own. None exists: nothing has been registered under order 8.
  - **Corrected in this record,** in RUNBOOKS §n and in `docs/evals/README.md`.
- **2. PINNED: mutant M1** (`require_on_main` reads the working copy). The real misuse is a draw straight after `register`, whose row is in this checkout's index and not yet on main (`test_a_draw_right_after_register_before_its_row_merges_is_refused`).
- **3. PINNED: mutant M11** (`arm_layer` rebuilds both arms at BASE's ref). `arm_layer` itself runs, with the child stood in, and each arm is built at its own ref (`test_each_arm_s_layer_is_rebuilt_at_its_own_ref`).
- **4. FIXED: RG-D12 whole, in the library (D1).**
  - The library's `run_compare` and `score_run` compared only the fingerprint. They now run `refuse_unless_registered_scorer` themselves: the fingerprint, BASE's production files, and the harness at a `scorer_ref` on main. A registration whose fingerprint matches but whose BASE holds other production files is refused at the draw and at the score.
  - `score_log.jsonl` records the scorer that ran (`scorer_fingerprint()`). That is equal to the registered one, because the check has just passed.
  - **Mutant M10's line is gone.** `run_compare`'s fingerprint check is now the first step of the whole check, and is pinned by `test_library_run_compare_refuses_a_scorer_that_is_not_the_registered_one`.
  - **The three other survivors:**
    - M5's guard (the export's manifest sha256) moved from the CLI into the library's `run_compare` and is pinned. Its only other guards are the request pins and the per-arm hashes, so a rewritten manifest would otherwise be drawn.
    - M7's guard (the request's wire sha256) is the only guard on `request.json`, which no file hash covers, and is pinned.
    - M8's guard (`arm_layer`'s recorded CIQ inputs) is pinned.
  - **Tests of other rules are stood in.** 44 existing tests register under placeholder refs ("A", "B") or old commits that no RG-D12 check can pass. They now stand in the fingerprint comparison they were written against (`tests/evals_scorer_stub.py`):
    - autouse in the six modules holding 37 of them;
    - a named fixture on the other seven, in the two order-8 modules. It is never autouse there, because those modules hold RG-D12's own pins.
  - **Five more tests in `test_evals_order8.py` follow the code:**
    - three index rows carry a design key;
    - the `--ticker` refusal opens an approval first, since `register` now reads it before anything else;
    - the structural approval pin reads `approval=approval` and the approval read before `write_registration`.
- **5. CORRECTED: the retrospective's instructions.** RUNBOOKS §n step 4, `Registration.scorer_ref`'s docstring and this record's #953 line said a retrospective registers from `origin/main`. The code requires BASE's production files, which all differ between `586fdcfd` and main, so that is refused. All three now give the composite checkout.
- **6. FIXED: what the scorer reads through.**
  - `vinci/sleeves.py` (read by `derive_proposal`), `vinci/dossier/midcycle.py` and `vinci/schemas/ledger.py` join the fingerprint as PRODUCTION files. All three exist at every commit the suite and #953 read the scorer at.
  - The scorer's whole static `vinci/` import closure is 99 files, 88 of them outside the fingerprint, measured at `7073ea09` by an `ast` walk from `SCORER_FILES`. `mechanical.py` imports the page builder: EDGAR, the price store, CIQ readers. A score's definitions do not read those, so they are not fingerprinted. The falsifier: a metric whose result changes with one of them.
- **7. FIXED: `register` reads its approval before it writes anything.** `register` wrote the registration file and then refused for want of `--budget-ledger`, and the file left behind blocked the retry. `register-run` read the approval after writing too. Both now read it first (`test_register_with_no_budget_ledger_writes_no_registration`).
- **8. DEFERRED: a CAND field that BASE's schema drops.** CAND's layer is parsed by BASE's `MechanicalLayer` (`impact_arm`, `arm_layer`), and pydantic drops a field CAND added (`extra_drop.py`). It is benign for #953, whose one such field is `impairment_headroom`, which is never sent. A future CAND would be tilted on M-ABSENT and M-ECHO. Making it loud means carrying a dropped-field list through `impact_arm`, `arm_layer`, `Score`, the score log and `score_text`: more than a few lines, so deferred, as the review allowed. The falsifier: an arm whose `layer.json` holds a key its parsed layer does not.

**DEFERRED, as the review marked them:**
- RG-D11 checks the gold only against the working copy's MANIFEST, so editing both passes. That is inherent without a pin held outside the repository.
- `run_request` accepts any registration string (D2). Every paid path above it now needs its index claim and its RG-D12 check. *(Corrected in review round 2, 2026-11-12: that was false for the judge. Its TEST read was claimed only by the CLI, and `judge.run_half("test")` under a fresh approval reached the paid client (`judge_test.py`). Since round 2, `run_half` claims the TEST read itself, before any client exists (F5). Its DEV half has no index claim, and the TEST-once rule is TEST's alone. So `run_compare` and `run_build` need their index claim, `run_compare` its RG-D12 check too, and the judge its TEST claim. The judge's DEV half is bounded only by its approval's ledger and cap.)*
- The git-ref lint cannot see a ref passed by name.

**#953's order.** #1036 (open) edits `schemas.py` and `synthesis.py`, both production files. So #953 registers after #1036 merges, as well as after this PR, #1031 and #1023.

**THE MUTANTS** (20; each applied alone, the evals, RG-D20 and git-ref suites run with `-x`, and the file restored byte for byte): **21 of 21 killed**. M6 survived the 20-mutant run and is now pinned by `test_an_approval_keeps_its_identity_as_its_ledger_grows`, which kills it: an approval's identity is its ledger's FIRST line, so under M6 every draw recorded would change it and a registration bound to it could not be drawn past its first row. Killed: M1 require_on_main reads the working copy, not main; M2 a barred target sits in Holm's family at p=0; M3 a barred-only registration's band is not forced to fail; M4 the BASE production re-check removed; M7 impact request.json wire sha256 not checked; M8 arm_layer skips the recorded CIQ-input check; M9 a build unit may be claimed twice; M11 arm_layer rebuilds BOTH arms at BASE's ref; M12 impact_arm reads BASE's arm for both; M13 fixed_scorer skips the harness-is-main check; M14 claim_judge_test lets any approval resume; M5' run_compare skips the export's manifest check (moved to the library); M10' run_compare's library RG-D12 check removed; D1 score_run's library RG-D12 check removed (no score-time check); R1a claim_draw keys on the sha again (design twins ignored); R1b the index stops recording the design; R1c a run's design includes its words; R1d a replication shares its first run's key; R6 the fingerprint drops vinci/sleeves.py; R7 register writes before it reads its approval; M6.

## Review round 2 (the coordinator's independent review at `3640be07`, 2026-11-12)

Six findings and one note. The operator ruled on two of them on 2026-11-12. One commit answers them, and its tests are in `tests/test_evals_order8_round2.py`.
- **Every FIX test fails on `3640be07`** for its finding's reason. This was shown by swapping in `3640be07`'s five `vinci/evals` files, running the tests, and restoring the files byte for byte (sha256 checked).
- **The two PINs pass on `3640be07`,** and fail there under the reviewer's own mutant.

- **F1. FIXED: the CLI's design wiring is pinned end to end, and the claim derives the key.**
  - **Reproduced:** `mutate_cli.py`. Its mutant makes `register` write `design=reg.sha` instead of `design=cm.draw_key(reg)`, and `register-run` likewise. It survived all 363 evals, git-ref and RG-D20 tests, and `shop_e2e.py` then drew one design under two approvals.
  - **Why nothing caught it.** The item-1 tests wrote their keys by hand. The CLI's one pin grepped its source. And `claim_draw` never derived the key from the registration it drew.
  - **The fix.** `registry.identity` derives a registration's sha, design key and request pins from the registration itself. `record_registered` and `claim_draw` now take the registration, not a sha and a key, so no caller hands the index a key. The claim refuses a row whose design or pins are not what the registration derives.
  - **Pinned end to end** (TEST-LAYER RULE). The CLI registers one design twice, under two approvals and two notes, then draws: through `run-compare`, and through `register-run` and `run`. The first draw reaches the spied client; the second is refused before any client. With the reviewer's mutant applied to `3640be07`, both pins fail.
  - **The index tests now use the production path.** The ones that wrote rows by hand write them with `record_registered` and claim with the registration. Their `match` strings are tightened to the design rule's own words, so F3's refusal cannot mask a design mutant.
- **F2. FIXED: one spelling is one design.**
  - **Reproduced:** `spellings.py`. Each of these respellings was a design of its own: the pages reordered (`NFLX,EPAM` against `EPAM,NFLX`), the targets reordered, a target repeated, and a gated metric's families reordered. `design_differs` named a field, and `draw_key` moved. Reordered pages were drawn twice even under ONE approval, because `run_compare`'s own check read the order as a design field.
  - **The fix.**
    - `compare._design` compares the pages and the targets as sets, for `design_differs` and `draw_key` both.
    - `builds.draw_key` sorts its pages.
    - `register` sorts a gated metric's families before it writes the rule that names them.
    - A target given twice is refused (`Registration`). Holm had run on one target, while the decision said "Holm across 2 target(s)".
  - **The transforms keep their order,** because they are applied in it.
- **F3. FIXED: one set of request bytes is drawn once across approvals.**
  - **The ruling** (operator, 2026-11-12, verbatim): **"Refuse by request pins (Recommended)"**. The question was "Should a paid draw also be refused when its whole set of request pins was already drawn under another registration?" The option read: "Closes the gap at the byte level. A replication under the replication rule stays allowed. Built in #1030's round 2 at $0."
  - **The defect.** The design key carries the scorer's fingerprint and a build's `code_ref` (HEAD by default). So any harness commit, or any change to a design field, gave byte-identical requests a new design, and a second approval could draw them. `prepare_build` refused by request pin, but per ledger only.
  - **The fix.** Every `registered` row records its request pins. `claim_draw` refuses a registration when EVERY one of its pins was already drawn under other registrations.
    - A comparison's pins count as drawn as a whole.
    - A build registration's pins count page by page, as its builds are drawn.
    - The run a replication replicates is exempt, so a replication is still drawn, once (`test_a_replication_is_its_own_design_and_is_drawn_once_too`).
  - **The boundary is the ruling's "whole set".**
    - A registration with even one request not yet drawn is drawn.
    - A build registration's undrawn page does not count as drawn.
    - A drawn registration whose row records no pins stops every draw, because its bytes cannot be read.
  - **It reads bytes, not kinds.** A `register-run` whose every request a comparison has drawn is refused too, and the reverse.
- **F4. CORRECTED: draw-once across checkouts is an accepted risk.**
  - **The ruling** (operator, verbatim): **"One drawing machine (Recommended)"**. The option read: "Correct the record to state this as an accepted risk, with a falsifier. Keep the rule that one agent runs every paid panel, one at a time, announced on #1004 first."
  - **The false claim.** The accepted-risk line said the approval binding closed it. The binding covers one sha, not its twins (`two_checkouts.py`).
  - **Restated** under "What it costs", with its falsifier.
  - **No code.** F3 changes which registrations count as twins, not what a checkout can see.
- **F5. FIXED: the judge's TEST-once rule is in the library.**
  - **The defect.** `claim_judge_test` was called only by the CLI's `judge` command, so `judge.run_half("test")` under a fresh approval reached the paid client (`judge_test.py`).
  - **The fix.** For a paid draw (`replay.paid_draw`), `run_half` now claims the read after its own per-approval refusals and before any client exists. The CLI no longer claims it separately.
  - **D2's deferral reason was false for the judge.** It said "every paid path above it now needs its index claim". It is corrected above and in the follow-ups.
- **F6. CORRECTED:** "Found, not fixed" still listed the library `score_run`'s scorer check, which round 1 fixed (item 4, D1).
- **The note: NOT FIXED.** `tests/test_evals_round2.py::test_score_refuses_a_scorer_other_than_the_registered_one` runs under its module's autouse stub (`fingerprint_only`), not production's `refuse_unless_registered_scorer`.
  - **Why it stays.** Making that one test run production needs the fixture to exempt it, with a `request` parameter and a condition. That is more than one line.
  - **What still covers it.** Production's fingerprint step is pinned by `test_library_run_compare_refuses_a_scorer_that_is_not_the_registered_one`, and the score-time call by D1's pin.

**THE MUTANTS.** 19 were run on round 2's code, each alone. For each, the evals, RG-D20 and git-ref suites ran with `-x`, and the file was restored byte for byte (sha256 checked); the committed index was unchanged after the run. **19 of 19 are killed.** Each is listed with the first test that failed:
- **The reviewer's own mutant.** Applied to `3640be07`, it fails both CLI PINs.
- **R2-1:** `identity` gives a comparison its sha as its design (round 1's design test; the pins rule refuses instead, and the tightened `match` sees it).
- **R2-2:** the same for a build registration.
- **R2-3:** `record_registered` writes the sha as the design (`test_a_registration_is_drawn_once_across_approvals`: the claim finds the row disagreeing).
- **R2-4:** the claim skips the row check (F1's `[design]` case).
- **R2-5:** the row check compares the design only (F1's `[pins]` case).
- **R2-6:** no request-pins rule (the builds `--min-gap-s 301` case).
- **R2-7:** no replication exemption (round 1's replication test).
- **R2-8:** a build registration's undrawn pages count as drawn (the boundary test).
- **R2-9:** a drawn row with no pins is skipped (the no-pins test).
- **R2-10:** "every pin drawn" is read as "the drawn set equals mine" (the boundary test).
- **R2-11 and R2-12:** `_design` keeps the order of the pages, then of the targets (F2).
- **R2-13:** `register` keeps the families' order (F2).
- **R2-14:** `builds.draw_key` keeps the pages' order (F2).
- **R2-15:** a target given twice is accepted.
- **R2-16:** `run_half` makes no TEST claim (the structural pin first; F5's own test also fails).
- **R2-17:** `run_half` claims only an UNPAID draw (`test_evals_judge.py`'s fake-client run, refused by the committed read).
- **R2-18:** `run_half` claims in this repository's index whatever root it is given (F5's positive pin).
- **R1a, re-run from round 1:** the claim ignores design twins. The round-1 design test still kills it, because its `match` no longer accepts the pins rule's refusal.

## What this means for #927's merged result

**#927 (fix 4a) shipped on its only target, M-GAP**, at 37 → 4 units, p_lower 2.6 × 10⁻¹¹ (`docs/records/2026-11-09-fix4a-measured-on-the-panel.md`). M-GAP's truth is the gap types #927's own code wrote. So that result measured compliance with the new rule-8 wording, on pages where no gap may be raised. It does not measure fidelity to the page.

Its registration and record stay as written, as history. The merged code stays merged; this PR does not revert or re-score anything. Re-scored under this code, the registration is refused three ways:
- by RG-D12: it was registered by its own files, `755044b4`, not its parent's, `03e384a3`;
- by RG-D14: its row is not in the index;
- if it were scored anyway, by RG-D13: with M-GAP barred it has no deciding target, so it does not ship.

**What stands and what does not.** The ship decision did not rest on M-GAP alone in evidence (impact-check and B's note, verified against `docs/records/2026-11-09-fix4a-measured-on-the-panel.md`, PR #931).
- **M-LABEL's gated families** (bleed, trailing-only, pe-percentile-blocked) fell **10 → 1, p_lower 0.005**. M-LABEL is a metric whose truth is the gold, not the candidate's output. The fall was measured as a no-worsening check, reported beside the decision rather than registered as a target.
- **Fix 4a's item (c)** reads through the gated trailing-only family, so its improvement has gold-validated evidence.
- **The gap framing (items a–b) was read by M-GAP alone.** That part is unproven until an independent coding of the gap types exists and M-GAP is re-measured against it.

## Found, not fixed / follow-ups

- **The independent coding of M-GAP's gap types** (RG-D13's lasting fix) is new gold: coders, not code. It is the operator's to commission. Until then M-GAP is barred.
- **`register` does not refuse a held-out page as a target page.** The ruling was "never used to build or tune a metric"; measuring a prompt change on a held-out page is neither, so it is left open. Whether held-out pages must also never be drawn is the operator's call.
- **CLOSED, no longer a follow-up: the library's `score_run` checks the registered scorer.** B's review deferred it. Review round 1 fixed it (item 4, D1): the library's `score_run` and `run_compare` run `refuse_unless_registered_scorer` whole. The 44 tests that score under placeholder refs stand in the fingerprint comparison (`tests/evals_scorer_stub.py`). *(Corrected in review round 2, 2026-11-12: this bullet still said the library's `score_run` did not check the registered scorer and that the fix needed its own PR.)*
- **`run_request`'s RG-D10 guard checks only that a registration string is present** (B's review, deferred). The judge passes `judge:{half}` by design. ~~Every paid path above it now also needs its index claim, so the guard is the last of three, not the only one.~~ *(Corrected in review round 2, 2026-11-12: the judge's paid path needed no index claim in the library until round 2 (F5). Now `run_compare` and `run_build` need their index claim, and the judge's TEST half needs its own. The judge's DEV half needs none, so for DEV this guard and the approval's cap are the only guards.)*
- **A CAND layer field BASE's schema drops is dropped silently** (round 1, item 8, deferred): see "Review round 1". The falsifier: an arm whose `layer.json` holds a key its parsed layer does not.
- **RG-D11 checks the gold only against the working copy's MANIFEST** (round 1, deferred): an edit to both passes, which is inherent without a pin held outside the repository.
- **The lint's rules are syntactic.** A ref handed to git through a wrapper it does not list is not seen. The falsifier is a `gate` red on an unreachable ref this lint passed.

**BOUNDARY.**
- The gold's hashes: the five files in `tests/fixtures/synthesis_gold/` at main `3d55bc31`.
- The lint's 29 refs to 4 commits: the hex literals its rules count as handed to git, in `tests/**/*.py` and `vinci/evals/**/*.py` on this branch, 2026-11-11.
- The held-out pool: the 27 `data/dossiers/*` pages at `3d55bc31`, minus the 6 panel pages, minus the 9 gold DEV pages outside the panel, leaving 12.
- The request comparison: the 6 panel pages, as in-process captures by each tree's harness, from one shared read of their inputs.
- The fail-first run: the 25 tests in the two new files, on main's harness code.

**WHAT IT COSTS / WHAT IS ACCEPTED.** $0, with no paid draw and no registration made.
- **Every registration made before this PR can no longer be drawn or scored by this code.** None is in the index, and some were registered by a candidate's scorer. Their results stand as their records state them.
- **A paid run now needs a docs-only PR merged before its first draw.** That costs a gate run's wait.
- **A `drawn` row is written after every $0 refusal and before the first paid call** (review round 0). A run that then stops mid-draw (a budget stop, an outage) has drawn, so its registration cannot be drawn again: a new registration is needed. The falsifier: a `drawn` row with no draws in its run folder.
- ~~**"Drawn once across approvals" across checkouts** is now closed by the approval binding (gap 6). A second draw under the SAME approval in another checkout, not yet committed, is still possible, as it was within one ledger before. That checkout holds the same approval's ledger.~~ *(Corrected in review round 2, 2026-11-12; operator: "One drawing machine (Recommended)".)* **"Drawn once across approvals" across checkouts is an ACCEPTED RISK, not closed.**
  - **What the binding covers.** The approval binding (gap 6) binds ONE registration: it is drawn only under the approval its row names.
  - **What it does not cover.** A twin is the same design, or the same request bytes (round 2's rule, F3), registered again under ANOTHER approval. It is a different sha with a binding of its own. A checkout reads only its own index and main's, and a `drawn` row reaches main only with a later PR. So two checkouts can each draw one twin before either `drawn` row is on main (`two_checkouts.py`, at `3640be07`: the second checkout's twin, under the second approval, was allowed). This is what the review found false in the line above. The same holds for a second draw under the SAME approval from another checkout.
  - **Why it stays open.** Closing it in code needs a lock that every checkout shares outside git, and none exists.
  - **What holds it.** The rule: one agent runs every paid panel, one at a time, announced on #1004 first.
  - **The falsifier:** two `drawn` rows on main whose registrations share a design key, or the later of which pins only bytes the earlier had drawn, with neither a replication of the other.
- **The held-out rule departs from the example rule** given with the ruling, for the reason above, and passes over the two pages a replay cannot draw. Both are stated in the file and in this record. **The `gold` command's TEST figures now cover 178 of the 314 TEST claims.** The historical TEST figures (for example M-LABEL's 22/32 and 22/27) stand as recorded and were measured on all 314.
