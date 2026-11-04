---
id: 2026-11-04-a-skip-is-not-a-pass-the-ciq-export-floor
status: shipped
date: 2026-11-04
prs: [896]
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
- **The review's six files**, plus the helper's pins and the drift pin, branch against main:

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
- **`-rs` under `bin/commit`'s doubled `-q`** prints every SKIPPED line. It still prints no
  totals line.
- **Full suite, both ways:** FILLED BELOW.

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
