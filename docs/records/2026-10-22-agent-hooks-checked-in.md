---
id: 2026-10-22-agent-hooks-checked-in
status: open
date: 2026-10-22
prs: []
supersedes:
superseded-by:
---

# Three CLAUDE.md rules become hooks: the §5.0 index at session start, a Stop-time fast gate, and a prompt before a decision-line edit

**WHAT.** `.claude/settings.json` is now committed. It wires three stdlib Python hooks under
`.claude/hooks/`, run by the system `python3` (3.9 on the operator's Mac):

1. **`open_now.py` (SessionStart: startup, clear, compact).** Prints one line per STATE.md §5.0
   row — number, owner, bold title cut at 150 characters — plus the line range of the full rows,
   and says that it is titles only. On `5969a48`: 20 rows, 2,652 characters, against a §5.0 block
   whose row 32 alone is ~10k characters.
2. **`fast_gate.py` (Stop).** On UNCOMMITTED `.py` changes under `vinci/`, `tests/`, `frontend/`
   it runs ruff on the changed files, `mypy --strict vinci` when a `vinci/` file changed, and
   pytest `-x` on the changed test files and the tests that import a changed module (most direct
   first, at most 20). A failure exits 2, so the turn continues with the failure in hand; it blocks
   at most 3 times in a row, then lets the turn end with a warning. A timeout or a missing venv
   warns and never blocks. A clean tree exits 0 after one `git` call.
3. **`decision_path_guard.py` (PreToolUse + PostToolUse on Edit, Write, MultiEdit,
   NotebookEdit).** An edit to the decision line or its gates — `vinci/dossier/verdict.py`,
   `vinci/dossier/schemas.py`, `vinci/seal.py`, `scenarios/`, `vinci/ledger/`,
   `data/snapshots/decision_ledger.jsonl`, `vinci/scoring/`, `.claude/settings.json`,
   `.claude/hooks/`, `.github/workflows/`, `bin/commit` — returns `permissionDecision: "ask"`, which
   Claude Code turns into an operator prompt (in auto mode too). PostToolUse runs only when the edit
   went through, records that approval, and the same file is not asked about again that session.

Also: `.claude/settings.local.json` (personal permissions) is git-ignored by the repo, not only by
one user's global exclude; CLAUDE.md names the hooks in one bullet.

**WHY.** Every CLAUDE.md rule was advisory. Anthropic's Claude Code documentation calls hooks
"deterministic" where CLAUDE.md is advisory, and the team's research of 2026-10-22 found no
checked-in hook, skill or settings file in this repo despite 350 lines of rules. Each hook here
replaces a sentence an agent had to remember: "read §5.0 first", "no red commit", and "if a change
crosses the decision line, STOP and flag it". Screens and the ranker are deliberately NOT guarded:
the real-run-before-merge rule governs them, and a prompt on every ranker edit would train the
operator to click through. A pytest output filter (failures only), proposed alongside these, was
NOT built: it would hide the totals line the repo's verification rule relies on.

**HOW VERIFIED.** Real runs on a scratch worktree of `5969a48`, each hook fed the documented stdin
JSON:
- `vinci/seal.py` given an unused `import os` → exit 2: `I001` and `F401` at `vinci/seal.py:21`
  and `:24`, 6.7 s with a cold mypy cache.
- A `-> int` function returning `"x"` plus an always-failing test in `tests/test_seal.py` →
  exit 2: the mypy `return-value` error at `vinci/seal.py:229`, then pytest on the 4 test files
  that import `vinci.seal`, "1 failed, 94 passed", 1.5 s.
- Repeated with `stop_hook_active: true` → attempts 2 and 3 block, the 4th returns the
  `systemMessage` and exits 0.
- A comment added to `vinci/dossier/schemas.py` (72 importing test files, 20 run) → exit 0 in
  8.9 s. A tree with no changes in scope → exit 0 in 0.8 s.
- Guard: `vinci/dossier/verdict.py` → the `ask` JSON; `vinci/dossier/assemble.py` → no output.

`tests/test_claude_hooks.py` pins 12 behaviours positive and negative, including the committed
§5.0 parsed independently and every row number required in the index, and a parse at
`feature_version=(3, 9)`. Two mutants were run against it: removing `verdict.py` from the protected
list reds `test_guard_asks_before_the_proposal_mapping_is_edited`; a gate that returns 0 instead of
2 reds `test_fast_gate_blocks_the_turn_on_a_lint_failure` and
`test_fast_gate_gives_up_blocking_after_its_cap`. Both were restored, back to 12 passed.

NOT VERIFIED in a live Claude Code session: the bundled CLI on this machine is not logged in, so a
headless session could not be started. The JSON shapes follow code.claude.com/docs/en/hooks as
read on 2026-10-22. That page's excerpt confirmed `file_path` for Write and Edit but did not show
the MultiEdit and NotebookEdit input schemas; the guard reads `file_path` or `notebook_path`. The
first session started on a checkout carrying this change is the live check: the index should
appear in its context.

**BOUNDARY.** Timings are wall-clock on the operator's Mac on 2026-10-22, one run each, measured
with the primary checkout's `.venv` (Python 3.12.13). The test-selection counts (`schemas.py` 72,
`config.py` 46, `assemble.py` 31, `seal.py` 4, `verdict.py` 4) are files under `tests/` matching
the import patterns at `5969a48`.

**WHAT IT COSTS / WHAT IS ACCEPTED.** A turn that ends with uncommitted Python changes pays seconds
for the fast gate, and up to the 240 s per-check timeout on a very wide change. That is accepted:
the timeout warns instead of blocking. A protected file costs one operator prompt per session.
Falsifier: if sessions routinely hit the 3-block cap, or operators approve every prompt unread,
the hooks are noise and the list or the cap should change. The fast gate is a subset; `bin/commit`
and CI remain the gate.
