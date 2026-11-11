---
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, hooks, CI and tests (RH-D3–D8, RG-D18, RE1-D17): one gate that runs anywhere, guards on the gate's configuration and the grader, a key check that fails what it cannot check and sends SEC nothing, and node tests that skip without node. RH-D2 and RH-D10 are stopped for the operator

**WHAT.**
- **RH-D3.** `bin/commit` defaulted `VENV` to one Mac's absolute path, which published a username
  and exited 127 on every other machine. It now resolves `$VENV`, else the checkout's `.venv`,
  else the primary checkout's: the fast gate's own order. With none, it refuses and says how to
  fix it.
- **RH-D4.** `bin/commit` now runs gate.yml's frontend-mirror check. The gates in
  `weekly-screen.yml`, `monthly-score.yml` and `theme-intelligence-weekly.yml` now pass `-rs`. A
  pin reads every workflow's pytest line and `bin/commit`'s, and requires gate.yml's flags on
  each.
- **RH-D5 (= RG-D22).** `tests/test_evals_round2.py::_full_history` also requires a non-shallow
  repository. `pn.motivated_from_git` raises on any shallow clone, so a shallow clone holding the
  freeze commit failed where it should have skipped.
- **RH-D6.** The five `tests/test_sleeves.py` tests that launch node check
  `shutil.which("node")` first. They had read the child's stderr, but a missing node raises
  `FileNotFoundError` before any stderr exists. The stderr sniff went with it: with node present
  it turned a JS error containing "not found", or any non-zero exit, into a skip. A guard
  (`tests/test_node_tests_skip_without_node.py`) requires a node check covering every node launch
  in the suite.
- **RH-D7 + RG-D18.** The edit guard now asks before `pyproject.toml`, `tests/conftest.py`,
  `.github/scripts/`, `vinci/evals/` and the two synthesis gold sets are edited. The review gate
  counts the grader's JSON (`vinci/evals/`, `tests/fixtures/synthesis_(gap_)gold/`) as code, so a
  PR that moves only the gold set or the gap types gets /code-review and Codex.
- **RH-D8.** `validate_keys.check_anthropic` warns only on `APIConnectionError` (its timeout
  included). Any other exception fails, naming its type. It used to pass as "connectivity, NOT a
  key problem".
- **RE1-D17.** `validate_keys.check_sec` sends no request. It applies `vinci.config`'s own
  `SEC_USER_AGENT` rule (placeholder refused, contact email required; pinned equal), and fails
  the run only when a set value would be refused.

**STOPPED.**
- **RH-D2.** The Stop hook blocks a clean change when ruff is missing.
  - The fix makes a tool's own "No module named <tool>" a warning, as the hook's docstring
    promises. It was REFUSED by the session's permission classifier, as loosening a gate.
  - The patch is in the PR body. It needs the operator's approval.
- **RH-D10.** The weekly job pushes to `main`.
  - Measured 2026-11-11 (`gh api …/branches/main/protection`): a PR is required (0 approvals),
    the `gate` check is required, and admins are not enforced. So the job's `GITHUB_TOKEN` pushes
    of snapshots and of `run_status.json` are refused. Its last green run, 2026-08-25, predates
    the protection.
  - Picking a remedy is the operator's call, and it touches §5.0 row 31. The options: run locally
    and land by PR (monthly-score's ruling), upload artifacts, or have the bot open a PR. A bot PR
    triggers no `gate` run. A workflow change here cannot be proven by a real run.

**HOW VERIFIED.** Every fix was run at main `173b4818` and at head, with these results.
- RH-D6: `test_sleeves.py` with node off PATH. Main: 5 failed (`FileNotFoundError: 'node'`).
  Head: 5 skipped.
- RH-D5: a real `--depth 400` clone of main, which holds `bcda7ce3`. Main's test file: `RuntimeError:
  shallow clone`. Head's: skipped.
- RH-D3, RH-D4: `bin/commit`, driven in a scratch checkout with a recording interpreter. Main:
  5 of 5 new tests fail (exit 127; the stale mirror committed; the flags missing in 3 workflows).
  Head: all pass.
- RH-D8, RE1-D17: 8 of 8 new tests fail on main's script and pass on head's.
- RH-D7, RG-D18: the guard asks on 8 named paths and stays silent on 3 controls. The review gate
  refuses a grader-JSON-only PR that was never reviewed.

**BOUNDARY.** "89 launches in 41 files, 5 unguarded": every `subprocess.*(["node", …])` call in
`tests/**/*.py` at main `173b4818`. "Depth 400": a `git clone --depth 400` of main, which reported
itself shallow and held `bcda7ce3`, 55 commits back. Measured 2026-11-11.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- `bin/commit` now runs `frontend/build.py`. On this iCloud-synced checkout, the build's rewrite
  of `frontend/dossiers/` can leave `* 2.*` copies, which the check reads as untracked files. It
  refuses then, rather than passing. Delete the copies and re-run.
- A refused `SEC_USER_AGENT` now fails `validate-keys`, where it was informational. The pipelines
  refuse the same value at their first SEC call.
