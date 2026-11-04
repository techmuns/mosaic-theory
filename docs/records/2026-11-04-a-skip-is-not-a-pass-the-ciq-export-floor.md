---
id: 2026-11-04-a-skip-is-not-a-pass-the-ciq-export-floor
status: shipped
date: 2026-11-04
prs: [897]
supersedes:
superseded-by:
---

# A skip is not a pass: a floor fails when most computed pages' exports have drifted, the frozen pins run on the operator's ciq-archive, and bin/commit prints every skip reason

**WHAT.** This answers the cross-review of #889 (nogods404, 2026-11-04, posted after #889
merged).

#889 made the CIQ-workbook tests skip when the export on disk is not the one their expectation
came from. Between a re-export and the artifact pass, every page's export can drift at once. The
page-keyed tests then skip as a class, and a CIQ-reader mutation fails nothing behavioural: only
the code-hash drift pin (`tests/test_extraction_version_drift.py`) goes red, and any edit to a
watched module trips that anyway. This PR is the smallest fix the review proposed, in three parts.

1. **A floor.** `tests/test_ciq_export_support.py::test_most_computed_pages_hold_the_estimates_export_they_stamp`
   applies `ciq_export_support.floor_breach` and `OWN_EXPORT_FLOOR = 0.5`. Where the CIQ folder
   holds tickers, at least half the computed pages (committed pages whose ev_gap is computed,
   `test_ev_gap_transform_idempotent.COMPUTED`) must hold the Estimates export they stamp. Below
   that it fails, naming every drifted page. Without the folder it skips, saying there is nothing
   to measure. The house precedent is `test_ev_bridge`'s `compared >= 20`.
2. **The frozen pins look in the archive.** `skip_unless_export` searches the operator's
   `ciq-archive/` before it skips: the folder beside the one the store reads, and the folder
   beside the one that links to. It returns the bundle the pin must run on, which is the archived
   FOLDER whole (one pull, never one workbook spliced into the live folder). NFLX's FQ2 pin
   (`406592d103`) and SMPL's −391.9 (`049150fb62`) now run on this machine, from
   `ciq-archive/replaced-2026-10-28/`.
3. **`bin/commit` passes `-rs`,** so its gate prints every skip's reason.

**WHY.** A skip says the expectation is unverified against this export, which is correct for one
test. It is never evidence that the code is right, and a class of skips passed the gate unread:
`-q` on top of addopts' `-q` prints no reasons. The floor turns "most of the class skipped" into a
failure with the remedy in its message (run the artifact pass, or link the pages' own exports).
The archive turns a frozen pin from "skips on every current folder" into "runs where the operator
kept its export".

The threshold is the review's proposal, and before choosing it I checked it against the live
folder. On 2026-11-04 the folder held 6 of 8 computed pages' own Estimates exports; NCNO and SMPL
were re-exported ahead of their re-assembly. So half does not make main red, and it fires when 5
of 8 drift.

**HOW VERIFIED.** All runs were on this machine, 2026-11-04, `pytest -m "not network"`, with the
Drive folder linked as it stood that day ("live").

- **"All drifted"** is a scratch CIQ root identical to live, except that each of the 8 computed
  pages' Estimates export is a copy with one byte appended. The content is the same and the sha
  is new, so it simulates every page re-exported at once. The readers parse it unchanged:
  SMPL's Revenue median is 1152.39 and EPAM's 5657.0 on both. That root has no `ciq-archive/`
  beside it.
- **Each change behind a test that fails on main `a439eabe`.** With only those pins copied
  onto main's helper and `bin/commit`, 3 failed:
  - the archived-export pin and the linked-folder pin each fail with "skipped where it must run";
  - the `bin/commit` pin fails because the line reads `-q` with no `-rs`.

  On this branch all 3 pass. For the floor, the failing case is the state itself: on all-drifted,
  main fails nothing and the branch fails the floor pin.
- **The review's six files**, plus the helper's pins and the drift pin, branch `dfd7ea24` (before
  review round 0 added 2 pins) against main:

  | Folder, mutation | main `a439eabe` | branch |
  |---|---|---|
  | live, none | 98 passed, 15 skipped | 107 passed, 13 skipped |
  | live, M1 (consensus vintage's floor marker stripped) | 9 failed | 9 failed |
  | live, M3 (forward window off by one) | 7 failed | 7 failed |
  | all drifted, none | **0 failed**, 90 passed, 23 skipped | **1 failed: the floor** |
  | all drifted, M1 | **1 failed: the drift pin only** | **2 failed: the floor and the drift pin** |
  | all drifted, M3 | 7 failed | 8 failed (adds the floor) |

  - Live M1 fails parity EPAM and IT; idempotent AORT, BRBR, EPAM, IT, MVST and WERN; and the drift
    pin.
  - Live M3 fails `test_revenue_resolves_on_every_name` IT, MVST, VITL and VRRM;
    `test_the_levels_reach_the_written_dossier` EPAM and VITL; and the drift pin.
  - M3 is caught on every folder because the baseline's vintage gate reads the data date, which
    appending a byte does not move.
  - Live and unmutated, the branch adds 7 helper pins and runs NFLX and materiality where main
    skips them: 98 + 9 = 107 passed, and 15 − 2 = 13 skipped.
- **The archived exports under mutation,** live folder:

  | Mutation | main | branch |
  |---|---|---|
  | M4 (surfaced unusual items at 1/1000) | materiality skips | materiality fails |
  | M5 (`_POINT_DECISION_BAND = 0`) | NFLX fails on its ungated record check | NFLX fails |

  Unmutated, main skips both pins and the branch passes both.
- **The floor's own pins:**
  - 4 of 8 holds; 3 of 8 fails, naming all 5 drifted pages; an empty population fails.
  - The census reads the page stamp against the folder: a constructed export is drifted, a name
    with no folder is drifted, and the stamp itself is own.
  - The archive is found beside a LINKED folder's target (the real topology), and an archive
    holding only other exports skips, saying it was searched.
- **Review round 0** (`/code-review high --fix`, 8 findings):
  - FIXED 1: the floor checked the checkout's absolute folder while the census reads the
    configured, cwd-relative store, so a run from another directory failed "0 of 8". It now
    checks the configured folder; a new pin changes directory and expects a skip.
  - FIXED 2: an archived folder holding two exports of one kind raised `CiqAmbiguousError` and
    ended the search. It is now passed by; a new pin covers it.
  - FIXED 8: `archive_roots`' docstring said four dated folders. That afternoon the archive held
    five (`replaced-2026-11-04/SMPL` was added that day).
  - DISMISSED 3: a page with no export on disk counts as drifted by design, because none of its
    page-keyed tests run.
  - DISMISSED 4 and 5: they concern where the NFLX and materiality tests build their live bundle,
    a pattern older than this PR. Either way the pin skips; it never runs on the wrong export.
  - DISMISSED 6 and 7: an extra parse per archived folder, and the store lookup written three
    times.
- **`-rs` under `bin/commit`'s doubled `-q`** prints every SKIPPED line. It still prints no
  totals line.
- **Full suite, both ways:** `pytest -m "not network" -rs`, each run in its own checkout, with
  no local store.

  | Folder | main `4a820016` | merged `e3c34907` | main `a439eabe` | `6c4904b7` |
  |---|---|---|---|---|
  | Live | 4 failed, 9287 passed, 106 skipped | 4 failed, 9299 passed, 104 skipped | 4 failed, 9221 passed, 89 skipped | 4 failed, 9233 passed, 87 skipped |
  | None | 0 failed, 8847 passed, 550 skipped | 1 failed, 8855 passed, 551 skipped | 0 failed, 8764 passed, 550 skipped | 0 failed, 8773 passed, 551 skipped |

  - **Live:** the 4 failures are the same set on all four trees:
    - AORT's bridge;
    - GOOGL's and LLY's 2% Consensus-vs-Trends check;
    - `test_latest_col_provenance::test_the_ascending_convention_holds_on_every_committed_bundle`
      on `SMPL/Balance Sheet/annual`. That one is new on main today: SMPL's Drive export was
      replaced on 2026-11-04 (`ciq-archive/replaced-2026-11-04/SMPL`).
  - **Live, +12 passed and −2 skipped:** 10 new test ids (9 helper pins, 1 `test_record_hygiene` id),
    and the NFLX and SMPL frozen pins now run.
  - **None:** the same 10 ids, of which the floor skips; every other skip reason is identical to
    main's.
  - **The one no-folder failure on the merged tree** is `test_sec_pacing.py::test_two_processes_on_
    one_machine_share_one_budget`, a real-clock two-process timing test ("min gap 0.097s"). Run
    alone it failed 1 of 3 on the merged tree and 2 of 6 on main `4a820016` ("min gap 0.009s",
    "0.040s"). It is a pre-existing flake; this branch touches no SEC pacing.

**BOUNDARY.**
- **"Computed pages"** is the 8 committed pages whose `mechanical.ev_gap.status` is "computed" on
  main `a439eabe`: AORT, BRBR, EPAM, IT, MVST, NCNO, SMPL, WERN.
- **"6 of 8" and "25 of 27 pages"** were read against the live Drive folder (37 ticker folders)
  on 2026-11-04. SMPL's live Estimates data date moved from ≥2026-10-27 that morning to ≥2026-10-29
  by the afternoon, so Drive changed during the day.
- **Every sha256** is the 10-hex `file_provenance` prefix.
- **The subset runs** are the six files the review measured (`test_consensus_parity`,
  `test_consensus_rows`, `test_consensus_transform`, `test_materiality`,
  `test_ev_gap_transform_idempotent`, `test_guidance_point_refusal`), plus
  `test_ciq_export_support` and `test_extraction_version_drift`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **In CI there is no folder, so the floor skips, and a reader mutation there is still caught by
  nothing but the drift pin.** This fix covers machines that hold the folder, which are the only
  ones where these tests can run. Covering CI would need committed licensed bytes, and raw CIQ
  is never committed.
- **The floor counts drift, not correctness.** At 4 of 8 it passes, while the 4 drifted pages'
  page-keyed tests still skip.
- **The frozen pins now depend on the operator keeping `ciq-archive/`.** If the archive is
  deleted they skip again, saying so.
- **`bin/commit` still prints no totals line** under its doubled `-q`. Dropping the extra `-q`
  would print it, but that is beyond the proposed fix.
- **Not changed, reported:**
  - `.claude/hooks/fast_gate.py` runs pytest without `-rs` too. That was outside the proposed fix,
    and the hooks are sandbox-protected.
  - `tests/test_ev_gap_transform_idempotent.py:33` fails `mypy` (`-> dict` without type
    arguments). It is pre-existing; tests are not mypy-gated, and it surfaced only because the
    helper's pins now import `COMPUTED` from it.
