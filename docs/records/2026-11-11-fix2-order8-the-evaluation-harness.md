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
  - Each paid draw is a `drawn` row, written before the draw. A comparison is drawn once across approvals. A `register-run` registration's builds are each drawn once, all under the approval that drew the first.
  - The judge's read of the gold's TEST half is a `judge_test_read` row, and a second read is refused whichever approval asks. That closes RG-D9, where both rules had held per approval ledger only.
  - The rows hold shas, refs, pages, counts, an approval's sha256 and dates: no path, no text.
- **RG-D11: the gold is the gold its manifest hashed** (`gold.verify_gold`). `load_gold` checks the five files against `MANIFEST.source_sha256`. Each coder file is checked as its two recorded halves, split at the DEV half's 330 claims; all five match today. An edited label is refused before any metric reads it.
- **RG-D12: a fixed scorer, never the candidate's** (`compare.refuse_unless_scored_by_base`, `fixed_scorer`, `refuse_unless_registered_scorer`). The final rule, merging B's scope (operator 2026-11-11: "Yes, take B's tests and close all six") with the retrospective refinement the coordinator accepted:
  - **The production files the metrics borrow** (`synthesis.py`, `mechanical.py`, `verdict.py`, `schemas.py`) must be BASE's bytes, always, for a prospective change and a retrospective alike. A candidate edits these, so a candidate never scores itself through them.
  - **The harness's own files** must be origin/main's at registration, a reviewed harness, recorded as `scorer_ref`. They are never compared with BASE's: a BASE older than the harness, which is any retrospective, would otherwise be refused from every checkout with these rules (B's check, gap 1).
  - **Enforced in the library, not only the CLI** (gap 1). `cm.register` refuses a checkout whose production files are not BASE's, and `run_compare` and `score_run` refuse a scorer that is not the registered one. The CLI's `refuse_unless_registered_scorer` also re-checks the production files against BASE and the harness against `scorer_ref`, which must be a commit on origin/main.
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
- `fixed_scorer` takes the retrospective branch, since `7ec84833` is on origin/main. From this branch it refuses, naming the scorer files this PR changes. Registered from main after this PR merges, it passes.

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
- **"Drawn once across approvals" across checkouts** is now closed by the approval binding (gap 6). A second draw under the SAME approval in another checkout, not yet committed, is still possible, as it was within one ledger before. That checkout holds the same approval's ledger.
- **The held-out rule departs from the example rule** given with the ruling, for the reason above, and passes over the two pages a replay cannot draw. Both are stated in the file and in this record. **The `gold` command's TEST figures now cover 178 of the 314 TEST claims.** The historical TEST figures (for example M-LABEL's 22/32 and 22/27) stand as recorded and were measured on all 314.
