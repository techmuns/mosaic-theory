---
id:
status: shipped
date: 2026-11-19
prs: [1137]
supersedes:
superseded-by:
---

# Three pins of the committed pages now hold on both page shapes, a page struck at its close (#1132) and a page built before it. #1132's suite never met the new shape, so the fast-values refresh turned 17 nodes red. Each pin was re-proved: it passes on both shapes and fails on a deliberately broken copy (tests only, $0).

**WHAT.**
- **`tests/test_cap_drift_render.py`.** The pins now hold the drift form owed by each page's own shape.
  - **New shape** (the page carries `stock_info.market_cap_at_close`). A drifting page must print CIQ's cap beside its own, in the approved form "(CIQ $8.1B at 2026-11-06, -2.2%)". Every figure in it is read off the page and checked against the JSON:
    - the percent is `cap_cross_check.gap`;
    - the date is `market_cap_as_of`;
    - CIQ's cap is the stored `cap_cross_check.ciq_market_cap`, which must equal `market_cap`;
    - the cap printed is the cap at the close.
  - **New shape, also checked:** the stored cross-check's gap must be the one its own inputs give, so a stale cross-check fails, and the old "implies" mark must not also appear.
  - **New shape, reconciling page:** it must print no CIQ cap.
  - **Old shape:** the "implies $X/sh" assertions are unchanged.
  - **The fleet pin** counts a drifting page as silent by the same shape rule. On the new shape a share-basis break must print its mismatch label.
- **`tests/test_ev_gap_persistence.py::test_every_written_form_states_a_status_and_both_vintages`.**
  - A gap carrying `tev_close_date` must carry exactly three vintages, each a real date; the consensus vintage may be a "≥" floor. `tev_close_date` must be the page's own close (`stock_info.as_of`).
  - A gap without it must carry exactly the old two, and its page must not carry a cap at the close. The shape is the page's (`stock_info.market_cap_at_close`), so a page whose cap moved to the close but whose gap was never re-struck fails (a review finding, round 0).
- **`tests/test_ev_gap_transform_idempotent.py::test_a_second_refresh_preserves_the_computed_gap`.**
  - `tev_close_date` is now stripped on both sides of the comparison with the committed vintages. It was stripped from the refreshed side only, a test bug that failed on every page already carrying it.
  - Where the committed page carries it, it must survive the refresh unchanged.

**WHY.**
- **#1132's suite missed these.** These tests read committed pages, and none carried the new fields until the refresh. A check the corpus never exercised on the new shape could not show that it held there: the CORPUS-BEFORE-SYNTHETIC lesson, met on #1132's own pins. The fast-values refresh of the 10 active pages turned 17 nodes red in the full gate (2 cap-drift, 10 vintages, 5 idempotence), so nothing was committed.
- **A separate tests-only PR,** merged before the refresh (coordinator B, 2026-11-19). The squash merge would otherwise fold a code change into an artifact commit (CLAUDE.md).

**HOW VERIFIED.** The three pins were run against main's pages, the refresh's pages and 13 broken copies. The refresh's pages came from the refresh's local commit; each broken copy is a page or the renderer deliberately broken, restored after each run.
- **Passes:**
  - C0, main `8bc138cd`'s 26 pages, all of the old shape: PASS.
  - C1, the 10 refreshed active pages beside the 16 committed others: PASS.
- **Fails:**
  - C2: the renderer drops CIQ's cap from the Snapshot.
  - C3: the renderer prints half the gap.
  - C4: EPAM's stored cross-check gap made stale (−5%).
  - C5: the renderer drops CIQ's date.
  - C6, old shape: the renderer drops the "implies" mark.
  - C7: EPAM's gap carries `tev_close_date` but no `tev_as_of`.
  - C8: EPAM's `tev_close_date` is not the page's close.
  - C9: EPAM's `tev_close_date` is not a date.
  - C10, old shape: EPAM's gap carries an extra vintage.
  - C11: the transform dates the TEV to a wrong close.
  - C12: EPAM's committed `tev_as_of` is wrong.
  - C13: EPAM's cap is at the close, but its gap has no close date.
  - C14: EPAM's consensus vintage is null. It fails as an assertion that names the field, not as an AttributeError.
- The outputs are in the PR body.

**BOUNDARY.**
- **Pages:** the 26 committed at main `8bc138cd`, 2026-11-19, and the same 26 with the 10 active pages but BRBR replaced by the fast-values refresh's output.
- **Nodes:** `test_cap_drift_render.py` (whole file); `test_every_written_form_states_a_status_and_both_vintages` (one node per page with a gap); `test_a_second_refresh_preserves_the_computed_gap` (one node per page with a computed gap: EPAM, IT, NCNO, SMPL, WERN).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **DEFERRED (review, round 0): the fleet pin's new-shape share-basis branch is exercised by no page.** It checks that a cap at the close with a whole-number ratio prints the mismatch label, but no committed page has such a ratio. The constructed mismatch test builds on AMZN, an old-shape page, so a renderer change dropping the label on the new shape would pass. It is closed by a constructed new-shape mismatch, its own test.
- **The cap-drift pins parse the Snapshot's own text,** with a regex on the approved form. A reworded tail fails them, as the old "implies" pin failed on the new form. That is the pin doing its job, and the wording is the renderer's, not an LLM's.
