---
status: shipped
date: 2026-11-11
prs: [981, 983, 986, 987, 988, 991, 992, 993, 995, 996, 998, 999, 1000, 1002, 1003]
supersedes:
superseded-by:
---

# Fix request 2 bookkeeping, batch 3: 41 fix-log rows to `fixed` and 3 kept `in progress` from fifteen merged PRs, row 60 recounted (of 148 asked: 119 fixed, 20 open, 8 in progress, 1 disagreed), and the day's rulings recorded: the deterministic pre-merge check, the FACTS-only panel rule, the split with the prompt-fix coordinator, and what waits until after fix request 2

**WHAT.** This is the third batch under batched bookkeeping (operator 2026-11-10). Each merged PR's
"Bookkeeping for the coordinator" section was applied to `docs/fix-log-teamnostra-2.md`, each row
with its squash commit. A row that said `in progress` or `fixed on merge` before its merge is
written as its merged state; a row its PR calls partial stays `in progress (#N)` with the residual
named.

**Flipped to `fixed` (41).**
- #981 `62d682c6`: RA-D2. The NA ruling's third leg is not read, and the row says so: a filing's
  own "no dividend" statement has no reader wired into this row.
- #983 `85306351`: RA-D4.
- #986 `65758333`: RE1-D7, RE1-D10, RE1-D15.
- #988 `fdf85180`: RH-D1.
- #991 `87f763d3`: RF-D5, RF-D10, RF-D11, RF-D12.
- #992 `31ff7b87`: RFL-D1, RFL-D2, RFL-D4 to RFL-D10.
- #993 `0d08979a`: E2-D5, FUBO refreshed at $0.
- #995 `6d9907d7` and #1003 `3410860a`: RD-D2. #995 alone: RD-D3.
- #996 `7edbfa36`: RH-D3, RH-D4, RH-D5 (= RG-D22, no row of its own), RH-D6, RH-D7, RG-D18,
  RH-D8, RE1-D17.
- #998 `8c5e7345`: G-D8 to G-D15.
- #999 `3d55bc31`: RFL-D3.
- #1000 `fb568c7f`: RD-D4.
- #1002 `e3f715b0`: RH-D10.

**Kept `in progress` (3), each residual named in its row.**
- RG-D21 (#987): a decline stated in percentage points or basis points still reads positive. Its
  own small PR follows.
- RH-D2 = H-D1 (#1002): the regression test is in, as a strict xfail. The two-line hook patch was
  refused three times by the editing session's auto-mode check as self-modification. The operator
  said "I'll allow the hook edit".

**The day's rulings recorded here, each verbatim in STATE row 60.**
1. **The deterministic pre-merge check.** It answers the operator's 2026-11-11 requirement:
   `python -m vinci.impact run` (#1000, RUNBOOKS §o) writes every fix PR's cross-setup section, and
   `CLAUDE.md` requires it. The coordinator's merge script also refuses a PR in four cases:
   - an unfilled placeholder in an added record line;
   - a body still saying `PENDING:`, `RUNNING:` or `QUEUED:`;
   - a Codex inline finding with no reply;
   - a requested Codex review not yet completed.
   Each was added after a real miss: #981 merged a record holding two placeholders, and #995
   merged before its round-1 fix.
2. **FACTS-only request moves need no paid panel by default.** The operator: "Not needed; #953 is
   the test (Recommended)". #953's request moved in its FACTS section on 23 of 27 pages, five of
   them panel pages, and it merged without a panel check because the hand-built compare could not
   see it. Its retrospective panel run (operator: "Run it now, $35 cap (Recommended)") is the
   ruling's falsifier. The harness stream runs it once order 8 merges.
3. **The split with the prompt-fix coordinator** (issue #1004, operator: "Yes, post the split").
   - The fix-request-2 coordinator's streams take on B's fix 2 and fix 5 (with RG-D1 to D7) and
     B's harness follow-ups (with order 8: row 53 item 6, the row 56 lint).
   - The CIQ stream takes the `customers()` hang.
   - The prices stream takes fact-layer slices 2b to 6, re-scoped, and the refresh price-date
     edges.
   - Rebuilds go in one combined pass per batch.
   - B owns fix 4b, fix 6 and the VRRM rehearsal (operator: "B, as offered").
   - RG-D13: M-GAP is barred as a target or gate until coded independently (operator: "Bar it
     now, tell B on #1004 (Recommended)").
   - **A correction to the reply on #1004:** that reply said the hand-offs would become fix-log
     rows. `tests/test_fix_log.py` admits only TeamNostra's ID shapes, so they are tracked in row
     60 and here, by the stream that carries each.
4. **After fix request 2, recorded, not built:**
   - the earnings-surprise reader stopping at a plain 'Guidance' row (LLY: 47 of 94
     `accounting_basis` empty);
   - a stale-companyfacts guard (SEC served V an unchanged body from 2026-09-02 to 11-04; 8 of 27
     pages checkable against their own source, all current);
   - the model-jury design;
   - the void writer refusing a back-dated `--ruled-on`;
   - the weekly screen's run-status follow-ons (row 32, item 14).

**WHY.** Rule 3 says `fixed` means on `main`. Every flip here names a squash commit that the lint
checks as reachable, and a test node it checks as existing.

**HOW VERIFIED.** `tests/test_fix_log.py`, `tests/test_state_identifiers.py`,
`tests/test_state_open_now.py` and the record lints pass on this branch. A first run of the
fix-log lint refused RFL-D3's row, because a snapshot id inside it reads as a commit sha. The id
moved out of the commit column.

**BOUNDARY.**
- 178 rows by Status cell: 119 `fixed`, 50 `open`, 8 `in progress`, 1 `disagree`.
- Of the 148 asked (all but the 30 `§4`): 119 fixed, 20 open, 8 in progress, 1 disagreed.
- The 44 rows changed: 39 `open` → `fixed`, 2 `in progress` → `fixed` (RA-D2, RA-D4) and 3
  `open` → `in progress` (RG-D21, RH-D2, H-D1).
- Read on this branch, cut from main `2637e91b`, 2026-11-11.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- "Fixed" here means the code is on `main`. Many fixes reach a page only at its next paid
  re-assembly, and each row's pages column says so: #961's 24 covenant rows, #981's dividend
  rows, #983's 16 guidance bridges. That pass is one combined batch under the operator's spend
  approval, not part of this record.
## Amendments

- **2026-11-12 — where the split's hand-offs stand** (bookkeeping batch 5, `docs/records/2026-11-12-fix2-bookkeeping-batch-5.md`, read on main `53e5f26e`). Item 3 above is unchanged; the fix log admits only TeamNostra IDs, so the hand-offs move here:
  - **Fix 2** did not go to the driver-facts stream. Stream S2 kept it when that stream took RG-D1 to RG-D7 and fix 5 (A's 13:14Z comment on #1004, operator-approved). It shipped in #1019 (`7af9a5b1`), except a reconciliation's unit: `ReconciliationValue` has no unit field, and adding one edits `schemas.py` and `release_parse.py`, both on A's unmerged `claude/fixreq2-e2-remainder` branch (`docs/records/2026-11-11-prompt-fix-2-digest-figures.md`).
  - **The refresh price-date edges** went to stream S3 (issue #1004: "Refresh paths that skip the price-date cut") and shipped in #1014 (`9b12444e`): three back-fill paths read EDGAR as filed by the page's price date, and 0 of 27 pages move. Its record names two found, not fixed: `cross_check_transform` still cuts at the assembly date (a loud refusal, never a wrong value), and assembly's statement reconciliation states `as_filed_by` as its build date, deferred in round 2 because `mechanical.py` is on A's `claude/fixreq2-e2-remainder` branch (`docs/records/2026-11-11-fix2-s3-refresh-back-fill-reads-edgar-at-the-price-date.md`).
  - **Fact-layer slices 2b to 6** were re-scoped by stream S3 in #1017 (`bc8ef88f`) against RFL-D1 to RFL-D10, all fixed, so no RFL remainder is left; the slices themselves stay open (STATE row 44; `docs/records/2026-11-11-fix2-s3-fact-layer-confirmed-and-rescoped.md`).
  - **The VRRM rehearsal**, B's, ran on copies in #1018 (`91dbdd8a`); who runs it where is left open (STATE row 38; `docs/records/2026-11-11-vrrm-run-monthly-rehearsed-on-a-copy.md`).
  - **Not in batch 5's PRs:** fix 5 and RG-D1 to RG-D7 (A's driver-facts stream; the seven rows read `open`), the harness follow-ups (order 8), the `customers()` hang (the CIQ stream), and the combined rebuild pass.
  - **B's own two:** fix 6 was dropped by its own $0 test (#1005, `4c8349bc`, record only: `docs/records/2026-11-11-fix6-draw-agreement-test.md`). Fix 4b waits on order 8 (A's harness PR) and on A's `_validate` guard, the build-time 12-word refusal A asked S2 to keep clear of (#1004, 2026-11-11); neither is on main at `53e5f26e`.
