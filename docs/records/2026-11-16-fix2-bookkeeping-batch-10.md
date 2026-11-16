---
id:
status: shipped
date: 2026-11-16
prs: [1080, 1081, 1082, 1083]
supersedes:
superseded-by:
---

# Fix request 2 bookkeeping, batch 10 (A, the coordinator): STATE row 62 closed now that B's machine runs the lock's anthropic 2.6.0, row 65 opened because a `vinci` command can run the checkout its venv's editable install names (on B's Mac, per row 62's premise, one at `481e82f7` with no lock; on the operator's Mac, one at `9708fbc0`), row 41 given #1081's review's two follow-ups, both reproduced at main `ee9c4635`, and the fix log unchanged (of 148 asked: 142 fixed, 0 open, 5 in progress, 1 disagreed)

**WHAT.**
- **STATE §5.0 row 62, closed.** The row is deleted. Below §5.0 the archive is in `docs/records/`, so the row has no other entry to strike.
  - **Its last open half was B's machine.** B reported on issue #1004 (comment 6911073109, 2026-11-16 08:15Z) that the operator re-synced B's venv that day.
  - **Before** (B, read only, about 08:00Z): anthropic 0.112.0 and `pip check` clean. Against main's `requirements.lock` (54 pins), 4 versions differed and 8 packages were missing, pytest-xdist among them.
  - **The re-sync:** the venv's own interpreter, `pip install --require-hashes -r <main's lock>`, and no `-e .`. The lock was read by path from main `b64be6f1`.
  - **After** (B, 08:08Z): anthropic 2.6.0, Python 3.12.13 and `pip check` clean. Of the 54 pins, 52 apply on macOS, because colorama and httpx2-jsfetch are Windows- and Emscripten-only. All 52 match, and none is missing.
  - **Main's SDK tests** at `b64be6f1` passed on that venv: `test_sdk_byte_check`, `test_dependency_lock`, `test_run_metrics`, `test_evals_judge` and `test_evals_replay_and_guard`. The result was 66 passed and 1 skipped (uv is not installed there). B ran them in a scratch checkout, and they wrote nothing.
  - **Nothing in flight straddles the two SDKs.** B's tracker records no evals registration or judge calibration in flight on that Mac. That is B's statement; this batch cannot see the tracker.
- **STATE §5.0 row 65, new** (owner: the operator). It holds what B surfaced, plus the same check on the operator's Mac.
  - **B's primary checkout** is at `481e82f7` (#903, 2026-11-04). It has no `requirements.lock`, so row 62's re-sync command does not work there as written. Row 62 said to run that command from the machine's primary checkout.
  - **What the comment does not state:** where B's venv's editable `vinci` points. Row 62 stated that a venv's editable `vinci` points at its primary checkout. If B's does, a build or draw that imports `vinci` through it runs `481e82f7`'s code. That code is 176 first-parent commits behind main `ee9c4635`. It predates:
    - the SDK pin and the run line's `sdk_version` (#1049);
    - the transcript evidence store (#951) and `tests/test_public_transcript_text.py` (#1006);
    - the 12-word guard at build (#1036).
  - **The sign a build left:** such a build's run line would state no `sdk_version`. All 11 committed run lines that state one state 2.6.0, every one dated 2026-11-14 (HOW VERIFIED).
  - **The operator's Mac,** measured by this batch, read only. Both its venvs' editable `vinci` name the operator's primary checkout. That checkout is at `9708fbc0` (#1024, 2026-11-12), 59 first-parent commits behind main `ee9c4635`, with no lock and no `sdk_version` in `vinci/`.
    - A script launched the way the `vinci` console entry point is (`pyproject.toml` `[project.scripts]`) imports `vinci` from that checkout, even when run from a worktree at main.
    - `python -c` run from the worktree imports the worktree's `vinci`.
    - The shared venv still has no pytest-xdist, so it does not match the whole lock, as batch 9's record found.
  - **The paid builds were not reached** (the coordinator's check, added in review round 1 and re-run here). Each of the 11 run lines dated 2026-11-14 records an `extraction_version`. Its components appear nowhere under `vinci/` at `9708fbc0` or at `481e82f7`, and all of them appear at `ee9c4635`. So those 11 builds ran newer code than either stale checkout. The hazard is the `vinci` console script on any future run.
  - **Carried from row 62.** Row 62 was the only STATE site stating that agents may not reinstall a shared venv, and the only one giving the re-sync's conditions. Row 65 now states both:
    - the venv's own interpreter, `pip install --require-hashes -r` the lock, and no `-e .` step;
    - while no build runs;
    - between evals registrations and judge calibrations, never during one.
  - **What unlocks it:**
    - B states `vinci.__file__`, printed by the venv's own interpreter launched as B's builds launch.
    - On each Mac, before the next build or draw, the primary checkout is brought to main, or builds launch as `python -m vinci` from a checkout at main.
    - Until a machine's primary checkout carries `requirements.lock`, its next re-sync reads the lock from main by path, as the operator did on 2026-11-16.
- **STATE §5.0 row 41** gains one clause, "FOUND, NOT FIXED", owner agent. It holds the two follow-ups lane 1 reported from #1081's review, outside #1081's scope. Both concern GOOGL's landing (#1078), which row 41 holds, so it is their nearest row. Neither is a TeamNostra ID, so neither fits the fix log.
  - **(a) A pin that passes on a missing block.** `tests/test_footnote_every_figure.py:552` asserts `"source_ref" not in (frozen["mechanical"]["valuation"].get("ev_ebitda_basis") or {})`.
    - It would pass if GOOGL's frozen 2026-11-03 fixture lost the block.
    - Today the fixture carries it, with 12 keys and no `source_ref`, so the pin is not yet vacuous.
    - The `or {}` is #903's (`481e82f7`). #1078 (`c58d5b2f`) moved the assertion onto the frozen page.
  - **(b) GOOGL's "10.9–25.8x" flagged as two untraceable figures: reproduced.**
    - **The flags:** GOOGL's committed page flags "Untraceable figure 10.9" and "Untraceable figure 25.8" in its first bear point. They are `caveats[12]` and `[13]` in `dossier.json`, and lines 524 and 525 of `dossier.md` and of its mirror.
    - **The cited block holds both figures.** The point cites "10.9–25.8x" to `CIQ Financials→Multiples (Close; last col = current, excluded from history)`. The block under that exact ref, `mechanical.valuation.own_history`, holds `low` 10.934315 and `high` 25.809247.
    - **The same figures pass elsewhere.** The same point's 17.5x is not flagged; it is the block's `median`, 17.451829. Nor are 10.9 and 25.8 flagged in the decisive question's evidence against, which cites the same figure to the same ref.
    - **The cause is not diagnosed.** The review guessed a range split in `synthesis._figure_entries` (`vinci/dossier/synthesis.py:1781`). This batch did not test that guess.
    - **What it is:** a false caveat on a committed page. It moves only at GOOGL's next build.
  - **What unlocks them:** a $0 code PR for each, neither scheduled. For (a), a pin that fails when the block is absent. For (b), the range trace diagnosed and fixed.
- **STATE §5.0 row 60.**
  - It names this record and adds a batch-10 clause.
  - Its count is re-stamped as unchanged at main `ee9c4635`.
  - It books the four PRs merged since batch 9 as no ID and no row:
    - **#1080** (`e465a009`): row 64 (b);
    - **#1081** (`2b2c450d`): row 41;
    - **#1082** (`b64be6f1`): row 64 (a); its section reads "None owed";
    - **#1083** (`ee9c4635`): row 10.
- **The fix log, `docs/fix-log-teamnostra-2.md`, is not edited.** No PR since batch 9 names an ID, so no status moves.

**WHY.**
- **The session ritual.** Closing an item deletes its §5.0 row. Row 62's last open half was answered by the source it named: what B's machine runs, from the venv B's builds and draws use.
- **Row 65, not just a line in this record.** A build on either Mac can run code that is days behind main while the run line gives no sign of it. Run lines record no commit and no machine, and a pre-#1049 build writes no `sdk_version` at all. The check is cheap, and only the owner of each machine can make it. The row replaces row 62's line, so §5.0 stays at 60 of its 60-line cap.
- **Row 65 claims no more than the comment states.** For B's Mac, what follows is conditional on row 62's own premise, because the comment does not say where the editable `vinci` points. The operator's-Mac half was measured here, so it is stated as measured.
- **Row 41 for the two follow-ups.** Both came out of the GOOGL landing that row 41 records. A row of their own would breach the cap.

**HOW VERIFIED.**
- **B's comment** was read through the GitHub API (`issues/comments/6911073109`, author `nogods404`, created 2026-11-16 08:15:50Z), read only. No other comment on #1004 since 2026-11-15 00:00Z is from B. This batch posted nothing.
- **The run lines.** Every file in `data/snapshots/assembly_runs/` at main `ee9c4635` was parsed as JSON lines: 55 files, one line each, none unparsed.
  - 11 lines carry `sdk_version`, all 2.6.0. Each is dated 2026-11-14: NCNO, SMPL, TJX, EPAM, LLY ×2, VITL, IT, WERN and GOOGL ×2.
  - The other 44 carry no such field. The field arrived with #1049 on 2026-11-13.
  - Outside `docs/`, `tests/`, `vinci/` and `scripts/`, `git grep sdk_version` at `ee9c4635` finds only these 11 files and STATE.md. So the evals draw rows that two panel records state at 0.112.0 (#1062's and #1066's, each 60 rows) are not committed, and are not in this count.
  - This agrees with the coordinator's 11 of 11 at the same commit.
- **`481e82f7`, from git.** It is #903, committed 2026-11-04, and an ancestor of main.
  - `git cat-file -e 481e82f7:requirements.lock` fails, because the lock was first added by `96d0cfea` (#1049, 2026-11-13).
  - `git grep sdk_version 481e82f7 -- vinci/` finds nothing.
  - `vinci/dossier/driver_evidence.py` (added by #951) and `tests/test_public_transcript_text.py` (added by #1006) are absent there.
  - `git rev-list --first-parent --count 481e82f7..origin/main` gives 176.
- **The operator's Mac,** read only, 2026-11-16. Nothing was installed or reinstalled.
  - Both venvs' `_editable_impl_vinci.pth` name the operator's primary checkout. Their anthropic reads 2.6.0. That checkout's `main` is at `9708fbc0` (#1024, 2026-11-12).
  - At `9708fbc0` there is no `requirements.lock` and no `sdk_version` in `vinci/`. `git rev-list --first-parent --count 9708fbc0..origin/main` gives 59.
  - A two-line script in this session's scratchpad, run by the shared venv's interpreter from this batch's worktree (at main `ee9c4635`), printed the primary checkout's `vinci` folder. `python -c` from the same worktree printed the worktree's.
- **The builds were not reached.** Each 2026-11-14 run line's `extraction_version` is a `+`-joined set of versions. Across the 11 lines there are 7 distinct ones:
  - `2026-11-11.guide-periods-read-where-stated-and-one-off-periods`;
  - `2026-11-13.bare-sales-and-profit-name-their-rows`;
  - `2026-11-13.wall-reads-indebtedness-and-the-notes-other-wordings`;
  - `2026-11-14.form4-price-its-filing-contradicts-is-refused`;
  - `2026-11-14.a-price-is-the-close-of-a-date-only-near-it`;
  - `2026-11-14.a-release-quote-keeps-the-figure-it-backs`;
  - `2026-11-14.a-passage-is-filed-as-the-call-prints-it`.

  `git grep -F <version> <commit> -- vinci/` finds each one at `ee9c4635`, and none at `9708fbc0` or `481e82f7`. Each of the 11 lines carries at least one version dated 2026-11-13 or 2026-11-14. The coordinator's check named only those two dates; the 2026-11-11 version is also absent at both stale commits, because #1027 merged it on 2026-11-13. Code at either commit could not have written any of these versions.
- **Follow-up (a):** `grep -n 'or {}'` at main `ee9c4635` finds line 552 as stated. The frozen fixture's `mechanical.valuation.ev_ebitda_basis` was read: a dict of 12 keys with no `source_ref`. `git log -L548,552` names #1078 and #903 as the commits that wrote those lines.
- **Follow-up (b):** GOOGL's committed `dossier.json` and `dossier.md` at main `ee9c4635` were read.
  - The `caveats` list holds 13 "Untraceable figure" entries: 13, 1, 2, 1 and 1 (bull points), 10.9, 25.8, 129109, 3 and 40 (bear points), 3 and 40 (decisive-against), and 129109 (a key unknown).
  - Neither 17.5 nor 22.9 is among them.
  - `synthesis.bear_points[0].figures` and `synthesis.decisive_question.evidence_against[1].figures` both cite "10.9–25.8x" to the same ref.
  - `mechanical.valuation.own_history.source_ref` is that ref, word for word.
- **The fix-log count.** A script over `tests/test_fix_log.py`'s `parse_log` read all 178 rows: 142 fixed, 30 open, 5 in progress and 1 disagreed. Of the 148 asked: 142 fixed, 0 open, 5 in progress and 1 disagreed. These equal batch 9's figures, as they should with no status moved. The 5 in progress are RG-D3, RG-D8, RH-D2, H-D1 and RG-D13.
- **The four PRs' bodies** were read (`gh pr view`). None names a TeamNostra ID, and #1082's "Bookkeeping for the coordinator" section reads "None owed". `git log c58d5b2f..origin/main -- docs/fix-log-teamnostra-2.md` lists batch 9 alone.
- **Tests and lints:** in the PR.

**BOUNDARY.**
- **The run lines:** every line of every file in `data/snapshots/assembly_runs/` at main `ee9c4635`, read 2026-11-16. The unit is one run line.
- **The not-reached check:** the 11 run lines dated 2026-11-14 at main `ee9c4635`, and the 7 distinct extraction versions they record. Each version was searched under `vinci/` at `9708fbc0`, `481e82f7` and `ee9c4635`, on 2026-11-16.
- **Commit distances:** first-parent commits on `origin/main`, from each named commit up to `ee9c4635`.
- **B's machine:** B's comment of 2026-11-16 08:15Z only. Nothing on B's Mac was read by this batch.
- **The operator's Mac:** two venvs (the shared venv and the primary checkout's `.venv`) and one checkout, read 2026-11-16.
- **The follow-ups:** one test line, one frozen fixture, and GOOGL's committed page and mirror, at main `ee9c4635`.
- **The fix-log count:** all 178 rows by their Status cell, and the 148 asked (every Order except `§4`), on this branch's log. The log is unchanged from main `ee9c4635`, counted 2026-11-16.
- **The PRs booked:** every first-parent commit on `origin/main` after batch 9 (`6b9c734d`, #1079) through `ee9c4635`. They are #1080, #1081, #1082 and #1083. #1084 (row 63) is open and is not booked.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Row 62 closes on B's report, not on a reading of B's Mac.** Nothing in the repo records the machine a run line ran on. The falsifier: a run line, an evals draw or a judge calibration from B's Mac dated after 2026-11-16 08:08Z that states an SDK other than 2.6.0.
- **Row 65's B half is conditional.** If B's editable `vinci` points somewhere other than the stale checkout, or B's builds never import through it, that half closes on B's first statement.
- **Row 41's two follow-ups stay unfixed.** This batch is docs only. GOOGL's page keeps its two false caveats until its next build.

**FOUND, NOT FIXED.**
- **A test comment now points at a closed row.** `tests/test_one_gate.py:33` says agents may not reinstall the shared venv "(STATE row 62)". Row 62 is deleted here, and its rule now stands in row 65. The comment's other claim still holds: the shared venv has no pytest-xdist (`import xdist` fails, read 2026-11-16). `git grep "row 62"` outside `docs/records/` and STATE.md finds only this line. This batch changes no test file, so the pointer is left for the next PR that touches the file.
- **The operator's primary checkout is behind main.** It sits at `9708fbc0`, 59 first-parent commits behind, and both of this Mac's venvs import `vinci` from it in script mode. That is row 65's operator half. It is recorded, not acted on: agents may not reinstall a shared venv, and the checkout is the operator's.
