---
id:
status: shipped
date: 2026-11-19
prs: [1086]
supersedes:
superseded-by:
---

# Fix request 2 bookkeeping, batch 11 (A, the coordinator): RH-D2 and H-D1 to `fixed` (#1086, `258ecb39`), so the fix log reads 144 fixed, 30 open, 3 in progress and 1 disagreed. The 3 still in progress are parked or waiting on the operator, each named below with what moves it.

**WHAT.**
- **RH-D2 → `fixed`** (`docs/fix-log-teamnostra-2.md`).
  - #1086 (`258ecb39`, merged 2026-11-16) applied #1002's approved patch to `.claude/hooks/fast_gate.py`: the fast gate now warns, never blocks, when its venv lacks a tool. The operator's words, carried from the row: "I'll allow the hook edit".
  - The regression test #1002 added (`e3f715b0`) lost its strict-xfail marker in the same commit.
  - The row names `tests/test_claude_hooks.py::test_fast_gate_warns_and_lets_a_clean_change_finish_when_a_tool_is_missing`.
- **H-D1 → `fixed`.** It is the same defect as RH-D2 (`= RH-D2`) and names the same test node, as `tests/test_fix_log.py` requires of a `fixed` row.
- **STATE §5.0 row 60**: its counts restated as 144 fixed, 30 open, 3 in progress and 1 disagreed, plus one batch-11 clause.

**WHY.** B asked on issue #1004, comment 7004085362, 2026-11-19, posted with the operator's approval ("yes post it"). Both rows still read `in progress (#1002)` three days after #1086 landed. The last booking, batch 10 (`37910301`, 2026-11-16 14:44 IST), was made 9 minutes before #1086 merged (`258ecb39`, 14:53 IST), and no batch has run since. B's comment names batch 9 as the last booking, which is the same slip, corrected here.

**HOW VERIFIED.**
- **On main `abadb913`:**
  - `.claude/hooks/fast_gate.py` carries #1086's three added lines;
  - `test_fast_gate_warns_and_lets_a_clean_change_finish_when_a_tool_is_missing` passes;
  - `tests/test_claude_hooks.py` has 0 `xfail` markers left.
- **The new counts** come from `tests/test_fix_log.py`'s own `parse_log`, not from a hand pattern: 178 rows; 144 `fixed`, 30 `open`, 3 `in progress`, 1 `disagree`.
- **A first draft failed** `tests/test_fix_log.py` because H-D1 named no test node; it was fixed before the commit.
- **Tests:** `tests/test_fix_log.py`, `tests/test_state_identifiers.py` and `tests/test_record_status_matches_open_now.py` pass on this branch.
- **Independent review of `5bc77caf`:**
  - with #1086's hunk reverted, the named node FAILS and the negative pin `::test_fast_gate_still_blocks_when_a_tool_fails_importing_something_else` still passes;
  - on a real venv with no ruff, the pre-fix hook exits 2 and main's exits 0 with an INCOMPLETE warning;
  - the 49 commits since `6b9c734d`, and the bodies of PRs #1080–#1129, name no other fix-request-2 ID that is owed a booking.

**BOUNDARY.**
- Counts are rows of `docs/fix-log-teamnostra-2.md` by their Status cell, as `test_fix_log.parse_log` reads them, on this branch cut from main `abadb913`, 2026-11-19.
- "148 asked" is 178 rows less the 30 §4 IDs that TeamNostra builds.
- The 49-commit figure is `6b9c734d..abadb913`, B's count, re-counted in the independent review.

**WHAT IT COSTS / WHAT IS ACCEPTED.** $0, docs only. Each row left open, and what moves it. None is held by an operator ruling.
- **RG-D3 part (d)** (`in progress (#1040)`): parked by the coordinator (A) on #1004 (comment 6878897873, 2026-11-14). It comes off the shelf when a start-year filer (ROST, BURL, TGT) goes active, or when any page writes such a claim.
- **RG-D8's clause-binding half** (`in progress (#1006)`): parked on B's hand-over list (#1004 comment 6830159523, 2026-11-12, "Parked on purpose").
- **RG-D13** (`in progress (#1030)`): #1030 bars M-GAP as a target. The lasting fix, an independent coding of M-GAP's gap types, is new gold for the operator to commission.
- **RE2-D18:** `disagree`.
