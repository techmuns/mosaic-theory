---
id: 2026-10-23-codex-review-requested-by-hook
status: shipped
date: 2026-10-23
prs: [789]
supersedes:
superseded-by:
---

# A code PR an agent opens gets one `@codex review` request from a hook — the review gate's own code rule decides which PRs

**WHAT.** `.claude/hooks/codex_request.py` runs after every successful Bash call (PostToolUse,
matcher `Bash`). It posts ONE comment, `@codex review`, on the PR when all of these hold:

- the command RUNS `gh pr create` (the review gate's `opens_a_pr`: a commit message, heredoc or
  `gh pr view` that mentions it is not a PR);
- the call succeeded. PostToolUse fires only on exit 0; a failed create fires
  PostToolUseFailure, which this is not wired to;
- Claude Code reports the PR it created: `tool_response.gitOperation.pr` with action `created`,
  else the last PR URL gh printed on stdout;
- the PR is in the GitHub repository this checkout's `origin` names (ssh or https, any case), so a
  PR opened elsewhere from a mosaic-theory session is never commented on;
- the PR changes CODE by the review gate's own rule. `review_gate.judged_code` was extracted from
  the gate's `main()` and is imported, not copied, so the two hooks cannot drift: a PR the gate
  holds for review is exactly a PR Codex is asked to review, including the gate's fail-closed
  reading of a checkout it cannot resolve;
- the PR has no `@codex review` comment yet.

It never blocks: the PR is already open. If `gh` fails, the agent is told (and the operator sees a
warning) to post the request by hand, with the command to run. On success the agent is told the
request is posted and not to post another.

CLAUDE.md's hooks line now reads **Five** and names the request; the pr-feedback skill says the hook
makes the opening request and that its own one re-review is separate from it.

**WHY.** Codex is every PR's second reviewer (`2026-10-23-bounded-pr-review`), and its automatic
review is enabled for the repo, but it never fired on a PR this repo's agents opened as
`nogods404`. #784, #785 and #786 were each reviewed only after a hand-typed `@codex review`.
#787 (docs only) and #788 (code) opened and merged with no Codex review at all, because nobody
typed one. That is the step a busy session forgets. The operator asked for the request to be
mandatory on a code PR, using the same code rule as the review gate.

The connector's other reply on open, *"To use Codex here, create an environment for this repo"*,
is not a review. It appeared exactly on the PRs whose BODY mentions `@codex` (#784 and #789, of
#784–#789), within 15 seconds of opening. A mention in the body starts no review; a comment does.

**HOW VERIFIED.**

- **Live, on this PR (#789).** This session's own `gh pr create` returned `gitOperation.pr` =
  `{number: 789, action: "created"}`. That real command and real `tool_response`, read back from
  the transcript, were fed to the hook under the system `/usr/bin/python3` (3.9.6), with the real
  `gh` logged in as `nogods404`. The hook exited 0, told the agent the request was posted, and
  `nogods404` commented `@codex review` at 12:15:10Z. Codex's review-summary comment followed at
  12:15:29Z with its code review `"status":"running"` on the PR head `803c5d31`. The new hook
  could not fire by itself in this session: hooks run from the primary checkout, which does not
  have it yet.
- **Live, a second time on the same payload:** exit 0, no output, and #789 still carries exactly
  one `@codex review` comment.

- **A dry replay of every real `gh pr create` in this session's transcript**, with `gh` replaced by
  a recorder on PATH so nothing was posted:

  | PR | Files (from GitHub) | Hook's calls |
  |---|---|---|
  | #781 | `.gitignore`, `CLAUDE.md`, `STATE.md`, `docs/DEPLOY.md`, a record | none — no code |
  | #782, #783, #784, #785, #786, #788 | code (hooks, settings, tests, `.gemini/*.yaml`) | `pr view`, then `pr comment … @codex review` |
  | #787 | `CLAUDE.md`, the skill, `STATE.md`, a record | none — no code |

  The other 19 Bash calls whose text contains `gh pr create` (heredocs, test scripts, greps) made
  no `gh` call. Every one of the 8 real responses carried `gitOperation.pr` with action `created`,
  so the fixture in the tests is that shape, copied from #788's.
- **`tests/test_claude_hooks.py` adds 10 pins** (41 in the file):
  - wired once, as a PostToolUse `Bash` group;
  - a code PR gets exactly one request, and the agent is told not to post another;
  - `--head docs` and a clean checkout get nothing;
  - the same decision as the gate over six commands (`--head code|docs`, `time … --head
    techmuns:code|docs`, `cd "$W"`, `--fill` on a clean checkout);
  - nothing for what opened no PR, run from a checkout that DOES change code (a commit message
    naming it, `gh pr view` printing a PR URL, `gh pr list`, a non-Bash tool, `--web`, a
    `gitOperation` whose action is not `created`);
  - gh's stdout is read when Claude Code records no PR;
  - no second request when one exists, including `@codex review <focus>`; a comment that merely
    mentions it later in the text does not count;
  - never another repository: an `equity-research` URL, a `cd` into another repo's checkout, no
    `origin` at all;
  - `origin` matched over ssh, `ssh://`, mixed case and no `.git`;
  - a `gh` failure exits 0 with the error and the hand command.
- **Mutants: 10 of 10 killed**, each restored, `__pycache__` cleared between runs: posting on a
  no-code PR, skipping the repo match, skipping the duplicate check, ignoring the action, no stdout
  fallback, no `opens_a_pr` check, no tool-name check, a silent `gh` failure, `search` for `match`
  in the duplicate check, a case-sensitive repo match. **Two survived the first draft of the
  tests and were killed by tightening them:** the not-a-PR pin ran on a clean checkout, so the
  code rule hid a missing `opens_a_pr` check; and no pin wrote `origin` differently from the URL.
- **The gate's refactor is behaviour-neutral:** its 16 existing `test_review_gate_*` pins pass
  unchanged.

**BOUNDARY.**

- **The live run.** PR #789's comments via `gh pr view --json comments`, 2026-10-23 12:15Z.
- **The connector's reply.** PRs #784–#789, comments and bodies via `gh pr view`, 2026-10-23.
- **The replay.** This session's transcript (`a08ef917…jsonl`) on 2026-10-23: 27 Bash calls whose
  command text contains `gh pr create` and that carry a recorded `tool_response`; 8 of them created
  a PR (#781–#788). Code judged by `--head` branch against `main` as of `0750e917`. PR file lists
  from `gh pr view --json files`.
- **Pins and mutants.** `tests/test_claude_hooks.py` on this branch, `-k codex`, 2026-10-23.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **ACCEPTED: a double review if Codex starts auto-reviewing these PRs.** The duplicate check only
  sees comments, not a review Codex starts by itself. Falsifier: a code PR that gets two Codex
  reviews for one request. Then remove the hook or switch Codex's auto-review off.
- **ACCEPTED: an unreadable comment list does not stop the request.** A duplicate costs one extra
  review; a missed request costs the review.
- **A hook change applies when the primary checkout pulls `main`** (`$CLAUDE_PROJECT_DIR`; see
  `2026-10-23-review-gate-judges-the-pr-checkout`). Until then sessions still post by hand.
