---
id:
status: shipped
date: 2026-11-16
prs: [1086]
supersedes:
superseded-by:
---

# RH-D2 (= H-D1) lands: the fast gate warns, and no longer blocks, when its venv lacks a tool. The operator applied #1002's approved three-line patch to `.claude/hooks/fast_gate.py`, and the strict xfail that held its place comes off

**WHAT.**
- In `.claude/hooks/fast_gate.py::run()`, when a check exits non-zero and its last stderr line
  is the tool's OWN `No module named <tool>`, the check returns `-1` with "`<tool>` is not
  installed in `<py>`". The gate reports that as INCOMPLETE, a warning, and lets the turn end.
- Any other failure still blocks, an import failure inside the tool included
  (`test_fast_gate_still_blocks_when_a_tool_fails_importing_something_else`, unchanged).
- The patch is #1002's, word for word. It applies to main `ee9c4635` unchanged:
  `fast_gate.py` has not moved since `fc8ded92` (2026-10-23).
- The strict xfail on
  `tests/test_claude_hooks.py::test_fast_gate_warns_and_lets_a_clean_change_finish_when_a_tool_is_missing`
  is removed. Nothing else changes in the test.
- **Who edited what.** Agents may not edit their own guardrails. This session's permission
  check refused the hook edit when #1002 was built, and the patch was not routed around. The
  coordinator turned #1002's block into a patch file and checked it with `git apply --check`.
  The operator applied it on 2026-11-16 with `git apply` ("Yes, start it", after "I'll allow
  the hook edit", 2026-11-11). The coordinator removed the xfail marker. The coordinator's own
  worktree guard refused a write into a second worktree, so the patch was applied twice: first
  in a scratch worktree (removed), then in this one. Both diffs hash the same
  (`399605a74315f892`, sha256 of `git diff`, first 16 characters).

**WHY.** The hook's own rule is that missing tooling is a WARNING, never a block. A venv without
ruff answers `-m ruff` with exit 1 and `No module named ruff`, the same exit a lint failure
gives. So main's hook blocked a CLEAN change for up to three turns. The 2026-11-11 record
(`docs/records/2026-11-11-fix2-rh-d2-rh-d10.md`) carries the finding and the ruling. Its status
flips from open to shipped here, because RH-D10 shipped in #1002 and RH-D2 ships now.

**HOW VERIFIED.**
- **Red at base:** at main `ee9c4635` the test is a strict XFAIL, so its assertions fail
  without the patch. The other RH-D2 pin passes.
- **The flip:** with the patch applied and the marker still on, the test is
  `XPASS(strict)`, which fails, as #1002 designed.
- **Green:** with the marker removed, `tests/test_claude_hooks.py` is 65 passed.
- **A real run, not the test's stand-in interpreter.**
  - The setup: a real `python -m venv --without-pip` venv with no ruff. Its own answer to
    `-m ruff` is exit 1 and "No module named ruff". The scratch checkout has one clean
    uncommitted file, `frontend/probe.py` (`VALUE = 1`).
  - Main's hook, `origin/main:.claude/hooks/fast_gate.py`: exit 2 with "FAST GATE FAILED on 1
    uncommitted Python file(s) — attempt 1 of 3 … No module named ruff". That is the bug.
  - The patched hook: exit 0 with `{"systemMessage": "fast gate INCOMPLETE (not blocking):
    ruff: ruff is not installed in …/bare-venv/bin/python"}`.
- **The full local gate:** see the PR body, which gives `ruff check vinci tests frontend`,
  `mypy --strict vinci` and `pytest -m "not network" -p no:warnings -n auto`, run on this tree
  with the venv re-synced to the lock (anthropic 2.6.0, pytest-xdist 3.8.0).

**BOUNDARY.** The 65 tests are `tests/test_claude_hooks.py` alone, on this tree (main
`ee9c4635` plus this change), on 2026-11-16, with the shared venv re-synced to `requirements.lock`
at `b64be6f1`. The real run is one scratch checkout with one clean file and one ruff-less venv,
under macOS and Python 3.12.13.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A missing tool now lets a turn end without that check. That is the hook's stated rule, and
  `bin/commit` and CI still run the full gate.
- The match is the LAST stderr line ending in the UNQUOTED `No module named <tool>`, which is
  what `python -m <tool>` prints when the tool is absent. An import failing INSIDE the tool prints
  the name quoted (`No module named 'tomli'`, the second pin's real traceback), so it still
  blocks. The
  residual is any other failure whose last stderr line happens to end in that unquoted phrase.
  **Falsifier:** a turn that ends INCOMPLETE where `bin/commit` then fails on that tool.
