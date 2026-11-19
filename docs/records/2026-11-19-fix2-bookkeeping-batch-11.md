---
id:
status: shipped
date: 2026-11-19
prs: [1086]
supersedes:
superseded-by:
---

# Fix request 2 bookkeeping, batch 11 (A, the coordinator): RH-D2 and H-D1 to `fixed` (#1086, `258ecb39`), so the fix log reads 144 fixed, 30 open, 3 in progress and 1 disagreed. That is the most it reaches without a new ruling.

**WHAT.**
- **RH-D2 → `fixed`** (`docs/fix-log-teamnostra-2.md`).
  - #1086 (`258ecb39`, merged 2026-11-16) applied #1002's approved patch to `.claude/hooks/fast_gate.py`: the fast gate now warns, never blocks, when its venv lacks a tool. The operator's words, carried from the row: "I'll allow the hook edit".
  - The regression test #1002 added (`e3f715b0`) lost its strict-xfail marker in the same commit.
  - The row names `tests/test_claude_hooks.py::test_fast_gate_warns_and_lets_a_clean_change_finish_when_a_tool_is_missing`.
- **H-D1 → `fixed`.** It is the same defect as RH-D2 (`= RH-D2`) and names the same test node, as `tests/test_fix_log.py` requires of a `fixed` row.
- **STATE §5.0 row 60**: its counts restated as 144 fixed, 30 open, 3 in progress and 1 disagreed, plus one batch-11 clause.

**WHY.** B asked on issue #1004, comment 7004085362, 2026-11-19, posted with the operator's approval ("yes post it"). Both rows still read `in progress (#1002)` three days after #1086 landed, because batch 9 (`6b9c734d`, 2026-11-16 01:21 IST) was booked before #1086 merged. B's count is that #1086 is the only one of the 49 commits on main since batch 9 that fixes a fix-request-2 ID.

**HOW VERIFIED.**
- **On main `abadb913`:**
  - `.claude/hooks/fast_gate.py` carries #1086's three added lines;
  - `test_fast_gate_warns_and_lets_a_clean_change_finish_when_a_tool_is_missing` passes;
  - `tests/test_claude_hooks.py` has 0 `xfail` markers left.
- **The new counts** come from `tests/test_fix_log.py`'s own `parse_log`, not from a hand pattern: 178 rows; 144 `fixed`, 30 `open`, 3 `in progress`, 1 `disagree`.
- **A first draft failed** `tests/test_fix_log.py` because H-D1 named no test node; it was fixed before the commit.
- **Tests:** `tests/test_fix_log.py`, `tests/test_state_identifiers.py` and `tests/test_record_status_matches_open_now.py` pass on this branch.

**BOUNDARY.**
- Counts are rows of `docs/fix-log-teamnostra-2.md` by their Status cell, as `test_fix_log.parse_log` reads them, on this branch cut from main `abadb913`, 2026-11-19.
- "148 asked" is 178 rows less the 30 §4 IDs that TeamNostra builds.
- The 49-commit figure is B's, on main `abadb913`, not re-counted here.

**WHAT IT COSTS / WHAT IS ACCEPTED.** $0, docs only. The 3 rows left `in progress` and the 1 `disagree` stand by ruling:
- RG-D3's part (d) and RG-D8's clause-binding half are parked with no live case;
- RG-D13 is barred, because M-GAP cannot be a target;
- RE2-D18 is disagreed.

So 144 is the ceiling until a new ruling.
