---
name: pr-feedback
description: Triage review feedback on a PR this session opened — Codex, Gemini Code Assist, a failed CI check or the operator — under the bounded process. FIX a finding only behind a test that fails first, otherwise DISMISS or DEFER; one fix commit per round; at most 2 rounds; then stop. Use when the app wakes the session about PR comments or a failed check, or when asked to address review feedback on a PR.
---

# PR feedback — bounded triage

ROUND CAP: 2

The PR's own session is the ONLY writer. Codex and Gemini review when the PR opens (draft or
not) and only comment. This skill turns their comments into at most two rounds of fixes, then stops, so that
review → fix → re-review cannot run on forever or pile up defensive code.

## 1. Collect

```bash
gh pr view <n> --json number,headRefOid,body,reviews,comments
gh api repos/techmuns/mosaic-theory/pulls/<n>/comments --paginate   # inline review comments
gh pr checks <n>
```

List every finding not yet in the PR body's `## Review dispositions` table: reviewer, severity
(Codex P0/P1; Gemini HIGH/CRITICAL), file:line, the claim. A failed check is a finding.

**Which round is this?** The pre-PR `/code-review high --fix` findings are round 0: they go in
the table as rows, and round 0 never gets a `### Round` line. This round is the highest
`### Round <k>` already in the PR body, plus one (none → round 1).

## 2. Triage — every finding gets exactly one outcome

| Outcome | When | What you do |
|---|---|---|
| **FIX** | The defect is real AND you wrote a test that FAILS on the PR head (a failed CI check is its own test; a wrong fact in prose needs the source that corrects it) | Fix it minimally, keep the test |
| **DISMISS** | You cannot make it fail, it is style, or it asks for hardening with no nameable failure | Reply on the thread with a one-line reason |
| **DEFER** | Real, but outside this PR's scope (CLAUDE.md: hold scope) | Name it in the build's record; open a STATE.md §5.0 row only if it needs an owner |

After the round cap, a new review finding is DEFER unless it is Codex P0 or Gemini CRITICAL. Those
are still FIXed behind a failing test, and you tell the operator in your message. A FAILED CHECK is
never deferred: `gate` must be green to merge, so it is fixed in any round.

Never post `@codex fix` and never run `/gemini review`. Never commit a bot's suggestion block as
it stands: it was written without this repo's tests or scope.

## 3. Apply — one commit per round

All FIXes of the round go in ONE commit through `bin/commit` (the Stop-time fast gate runs
first), then ONE push. Each FIX's test goes in the same commit.

## 4. Re-review — at most once per PR

Only when a FIX changed behaviour beyond the lines the comment named, post `@codex review` once.
That reply, if it comes, is round 2. Gemini is not asked to re-review.

## 5. Record — the PR body is the ledger

Keep one table in the PR body, updated with `gh pr edit <n> --body-file <file>`, and add a
`### Round <k>` line under it with the commit that round produced:

```markdown
## Review dispositions

| # | Round | Source | Severity | File:line | Finding | Outcome | Test or reason |
|---|---|---|---|---|---|---|---|
| 1 | 0 | /code-review high | — | vinci/x.py:42 | … | FIX | tests/test_x.py::test_… |
| 2 | 1 | Codex | P1 | vinci/y.py:10 | … | DISMISS | could not make it fail: … |

### Round 1 — 3 findings: 1 FIX (abc1234), 1 DISMISS, 1 DEFER
```

Every finding stated in the table, with its count in the round line — never a summary that drops
rows. The operator merges when `gate` is green and the table has no finding without an outcome.

## 6. Stop

End the turn. Do not poll for new comments: the app wakes this session when they arrive. Never
merge.
