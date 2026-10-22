---
id: 2026-10-22-pr-review-gate
status: open
date: 2026-10-22
prs: []
supersedes:
superseded-by:
---

# An agent's PR on a code change is code-reviewed before it opens: `gh pr create` waits for `/code-review high --fix`

**WHAT.** `.claude/hooks/review_gate.py` runs as a PreToolUse hook on every Bash call and acts only
on `gh pr create`. If the branch changes CODE against `origin/main`, the hook refuses the call
(exit 2) until the session transcript shows the `code-review` skill run at effort `high`, `xhigh`,
`max` or `ultra` since the last other `gh pr create` in the session. CODE means `.py`, `.js`,
`.mjs`, `.ts`, `.sh`, `.toml`, `.yml`/`.yaml`, `bin/`, `functions/` or `.claude/settings.json`.
The refusal tells the agent to:

1. run `Skill(skill="code-review", args="high --fix")`, the operator's `/code-review high --fix`;
2. keep only fixes for confirmed correctness bugs or requirement gaps;
3. commit through `bin/commit`;
4. list every finding as FIXED or DISMISSED, with a reason, in a "Code review (high)" section of the
   PR body.

A branch that changes no code (records, STATE.md, committed data, artifact passes) is not gated. An
unreadable transcript lets the PR open with a visible warning. The operator still reviews and
merges every PR. CLAUDE.md's hooks bullet now names four hooks.

**WHY.** On 2026-10-22 the operator asked for `/code-review high` with fix application to run on
every PR without being typed. The 2026-10-22 research report on agent engineering (delivered to
the operator, not committed) supports a
fresh-context reviewer as part of the framework, with two limits:

- **The builder grades itself too kindly.** Anthropic's harness work found a separate evaluator
  more tractable than a self-critical generator. Claude Code's best practices put an adversarial
  review step before work counts as done. Anthropic's own pipeline runs review agents on every PR,
  and those agents must prove their findings.
- **A reviewer asked for gaps reports some even when the work is sound.** Chasing every finding
  produces over-engineering, which is why step 2 keeps only confirmed fixes and step 4 makes each
  dismissal visible. Anthropic's source-control post calls adversarial review "myopic".

Three alternatives were weighed:

- **The `anthropics/claude-code-action` GitHub Action, reviewing in CI.** Deferred. It bills the
  API per review. On a public repo it needs care with secrets: fork PRs get none, and
  `pull_request_target` would hand them out. A bot's push made with `GITHUB_TOKEN` does not
  re-trigger `gate`.
- **Managed Code Review.** Declined. It averages $15–25 per review and needs a Team or Enterprise
  plan.
- **A CLAUDE.md sentence.** Rejected. It is advisory, which is the problem this framework exists
  to fix.

The gate runs inside the session that builds the PR, on the operator's existing Claude Code plan.

**HOW VERIFIED.** On real data, 2026-10-22:

- **This session's transcript.** It holds two `gh pr create` calls (#781, #782) and one `Skill`
  call (deep-research, not code-review). The gate's parser returns "not reviewed" for a new
  `gh pr create`.
- **Branch diffs.** The #782 hooks branch changes 5 code files and is gated. The #781 branch
  changes only `.gitignore`, `CLAUDE.md`, `STATE.md`, `docs/DEPLOY.md` and a record, so it is not
  gated.

`tests/test_claude_hooks.py` adds 7 pins (19 in the file), built on the transcript shape checked
against that live transcript:

- an unreviewed code PR is refused;
- a reviewed one passes;
- a second PR needs a second review;
- the call being decided is not counted as the "last PR";
- `low` effort, or no effort named, does not count;
- docs, data and STATE.md branches pass;
- `gh pr view`, `gh pr list` and `git push` are ignored;
- an unreadable transcript passes with a warning.

Three mutants were run, and each turned red the pin that names it:

- accepting any effort → `test_review_gate_does_not_accept_a_low_effort_review`;
- counting the current call as the last PR → `test_review_gate_lets_a_reviewed_code_pr_through`
  and `test_review_gate_needs_a_fresh_review_for_each_pr`;
- gating every branch → `test_review_gate_does_not_gate_a_docs_or_data_branch`.

Restored: 19 passed.

**The gate's own PR went through the gate's process**, and that turned up two kinds of bug.

**The review itself.** `/code-review high --fix` on the branch reported 7 findings. 5 were fixed,
each with a test that fails on the pre-fix hooks (5 failed, 19 passed) and passes after:

- a `gh pr create` quoted in a commit message was gated;
- an operator-typed `/code-review` was not counted;
- a deleted `vinci` module escaped the fast gate;
- pytest progress lines crowded out the FAILED lines;
- `git()` raised instead of degrading.

2 were skipped:

- a review of another branch in the same session counts;
- the hook starts `python3` on every Bash call.

**The live transcript.** Run against this session's real transcript, the gate STILL refused, even
though the review had run. A heredoc that wrote the new tests contained `cd x && gh pr create`, and
it was read as a PR opened after the review. Heredoc bodies and quoted strings are now stripped
before matching, and `test_review_gate_reads_a_heredoc_as_data_not_a_pr` pins it. On the same
transcript, the previous gate exits 2 and the fixed gate exits 0. The synthetic pins had all
passed; only the real transcript showed this.

**BOUNDARY.**

- **Transcript counts.** These are tool calls in one session transcript
  (`a08ef917-84bf-4d59-9bc3-5b40b1f95038.jsonl`) at the time of the check, after removing calls the
  file repeats by id.
- **Code-file counts.** These are files from `git diff --name-only` against the merge base with
  `origin/main` on 2026-10-22, matched by the CODE pattern above.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The cost.** Every Bash call pays a python3 start-up (tens of milliseconds) before the hook
  returns. Every code PR pays a `/code-review high` run on the operator's plan, measured in minutes,
  not dollars of API.
- **ACCEPTED: the gate trusts the transcript.** A review the agent ran but then ignored still
  satisfies it. The PR body's FIXED/DISMISSED list, and the operator's merge, are the check on
  that.
- **ACCEPTED: PRs opened outside Claude Code are not gated.** That includes the operator's own
  terminal and Codex.
- **Falsifier.** If, over the first 20 gated PRs, most findings are DISMISSED, or the fixes
  introduce regressions CI catches, the review is noise at this effort. Revisit the level or the
  instruction.
