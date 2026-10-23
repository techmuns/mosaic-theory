---
id: 2026-10-23-bounded-pr-review
status: shipped
date: 2026-10-23
prs: [784]
supersedes:
superseded-by:
---

# PR feedback is bounded: Codex and Gemini review once and only comment, the PR's own session triages, at most 2 rounds

**WHAT.** A second and third reviewer, added without letting review run on forever.

- **Codex** reads the new `## Code Review Rules` in `AGENTS.md`.
- **Gemini Code Assist** reads `.gemini/config.yaml` and `.gemini/styleguide.md`. Its config:
  - comments only at severity HIGH and above;
  - has no comment cap (`-1`): a cap drops findings silently, and the severity floor bounds the
    volume instead;
  - reviews when a PR opens, drafts included, with no summary or help post;
  - skips derived data, records and prose (`data/`, `docs/`, `planning/`, `scenarios/`,
    `STATE.md`, the frontend's dossier, theme-intelligence and calls mirrors, and frontend JSON).
- **Both** get the same short checklist: the decision line, data integrity, and the public repo.
  Both are told never to push.
- **The PR's own session** triages their findings with `.claude/skills/pr-feedback/SKILL.md`:
  - every finding is FIX, DISMISS or DEFER;
  - FIX only behind a test that fails on the PR head;
  - one commit per round, at most 2 rounds;
  - at most one `@codex review`, never `@codex fix`, Gemini never re-run;
  - a `## Review dispositions` table in the PR body holds every finding;
  - then the session stops.

CLAUDE.md states the flow in one bullet. The operator installs the two GitHub apps for this repo
and merges.

**WHY.** The operator asked to add cross-model reviewers to the in-session `/code-review high
--fix` gate (#783), and asked whether chaining them risks an endless loop of fixes and verbose
code. Three findings shaped the design:

- **Reviewers from a different model family catch different errors.** The 2026-10-22 research
  found judges favour their own model family. Codex flags only P0/P1 by design.
- **Unbounded review loops are measurable here.** On nostra-demus/equity-research, which runs
  both bots, the last 40 merged PRs (measured 2026-10-23) show:
  - a median of 7 commits per PR (max 18);
  - Gemini reviewed 36 of 40, up to 5 rounds and 11 inline comments on one PR;
  - Codex reviewed 17 of 40, up to 7 rounds and 15 comments on one PR.
- **Reviews arrive fast; the merge is the slow part.** On those same PRs:
  - Gemini's first review came at a median of 2.4 min (p90 4.1);
  - Codex's at a median of 5.9 min (p90 7.7; one at 540 min);
  - opened-to-merged took a median of 17.9 h.

  So the session never waits on a reviewer: it stops after opening the PR, and the app wakes it
  when comments arrive.

The guard against bloat is the repo's own rule, "regression-test every bug fix", turned into a
filter. A finding the session cannot make fail is DISMISSED, which drops speculative hardening.
One writer per branch keeps bots and the session from fighting over the same code.

**HOW VERIFIED.**

- **Pins.** `tests/test_review_process.py` adds 7 pins (62 passed with `test_claude_hooks.py`,
  `test_records_ledger.py` and `test_state_identifiers.py`):
  - Gemini's severity floor, no cap, and review on open;
  - artifacts and prose skipped while code (`vinci/`, `tests/`, the hooks, workflows, CLAUDE.md,
    `frontend/views`) is reviewed;
  - on the committed tree, no code file hidden and every `data/dossiers/` file skipped;
  - Codex and Gemini given identical checks;
  - neither allowed to write;
  - the round cap one number in CLAUDE.md and the skill;
  - the skill discoverable, naming every outcome.
- **Mutants.** Six were run on the final files, and each turned red the pin that names it:
  - the `frontend/**/*.json` line removed;
  - threshold set to MEDIUM;
  - `vinci/**` added to the ignore list;
  - drafts excluded;
  - one check removed from the style guide;
  - a cap of 3 in CLAUDE.md.

  A 5-comment cap was also killed in an earlier run. Every file was restored.
- **This PR's own pre-PR review.** `/code-review high --fix` reported 6 findings, all fixed:
  - a failed check would have been deferred after the round cap;
  - round 0 could be miscounted as a round;
  - the review gate's refusal text and CLAUDE.md named a second, differently worded table;
  - CLAUDE.md said "once" while the skill allows one re-review;
  - the pins matched with `fnmatch`, whose `*` crosses `/`;
  - draft PRs were excluded from Gemini's review.
- **The real tree.** On `fc8ded92`, Gemini skips 2,012 of 2,749 tracked files and reviews 737:
  - skipped: data 367, docs 1,180, frontend 444, scenarios 16, planning 4, STATE.md 1;
  - reviewed: vinci 199, tests 474, frontend 26, scripts 15, plus the root config.

  `tests/fixtures/` stays reviewed, because it holds 2 `.py` files that a blanket skip would hide.
- **The existing `AGENTS.md` pin passes.** It is still a pointer: 52 lines (the cap is 60), with no
  sentence copied from CLAUDE.md.

NOT VERIFIED in use. Neither app is installed on this repo yet, so no bot comment has been triaged
under the skill. The first PR after the install is the live check: Gemini's review should carry
only HIGH or CRITICAL comments, and the session should be woken by the app, not poll.

**BOUNDARY.**

- **equity-research counts.** The 40 most recently merged PRs of nostra-demus/equity-research as
  listed on 2026-10-23, read-only. Reviews are counted per PR from the reviews API; inline comments
  from the pull-request comments API. Latencies run from the PR's `createdAt` to each bot's first
  review.
- **File counts.** `git ls-files` at `fc8ded92`, matched with a gitignore-style matcher on the
  configured patterns (`*` within one path segment, `**` across segments). Gemini's own glob
  semantics are not documented; this matcher is the stand-in.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The cost.** Codex review comes with the ChatGPT plan the operator already uses for
  equity-research, and Gemini's install already reviews equity-research. Neither adds a
  subscription here. The cost is the session's triage time, capped at 2 rounds per PR.
- **ACCEPTED: the skill is followed, not enforced.** Nothing stops a session posting
  `@codex fix`. The disposition table in the PR body, and the operator's merge, are the check.
- **Falsifier.** Over the first 20 PRs, track each reviewer's FIX/total. If a reviewer stays far
  below Uber's reported ~75% useful-comment rate, or PRs still exceed 2 rounds, raise its
  threshold or remove it.
## Amendments

**2026-10-23 — Codex is live; Gemini is NOT installed (operator decision, $19/month).**

- **Codex Code Review** was set up the same day. Asked with `@codex review` (once on #784 and
  #785, twice on #786, see the next bullet), it reported "Didn't find any major issues" on each of
  #784, #785 and #786, at their head commits
  (`e20a22e`, `93a16a2`, `5f62cdf`).
- **Its first attempt on #786 failed** at environment setup ("Setup repeatedly failed"). The retry,
  made after the other two reviews finished, succeeded. The likely cause is three environment
  setups starting at once.
- **Gemini Code Assist never responded:** nothing within 15 minutes of `/gemini review` on any of
  the three PRs. The operator then declined it at $19/month, because Codex already supplies the
  second model family.
- **`.gemini/config.yaml` and `.gemini/styleguide.md` stay committed and inert.** With no app
  installed they have no effect. Their pins in `tests/test_review_process.py` still hold, so
  installing Gemini later needs no repo change.
- **What now names Codex as the second reviewer:** CLAUDE.md's flow line, the `pr-feedback` skill
  and STATE.md. Each tells a session never to wait for, or request, a Gemini review.
