---
id: 2026-10-21-theme-intelligence-rulings
status: recorded
date: 2026-10-21
prs: []
supersedes:
superseded-by:
---

# Theme intelligence: the operator's open rulings decided, red means broken, and a replay says what it skipped

**WHAT.** Operator, 2026-10-21: "go with your picks". This followed a detailed list of STATE row
32 (8)'s open items, each diagnosed first.

| item | decision | basis (measured 2026-10-21 on `theme-intelligence-state` 9939047e unless said) |
|---|---|---|
| (a) may a qualitative "swept up in the sell-off" count as a dislocation? | **No, kept as is** | It changes no action. 5 active Watch theses are held only by "no dislocation or catalyst", and none offers such a sentence: 2 offer forecasts (2027 server revenue, a 2027–28 CPO timeline), 3 offer nothing. |
| (c) get the weekly run working | **Closed** | The keys are fixed and checked (`validate-keys` checks every secret a workflow reads). The second run scanned 7 articles for $4.445, and U31f is proven. It was red only for (l). |
| (d) turn on the article prompt cache | **Stays off** | It discounts only a split completeness pass. None of this week's 7 articles, and none of the merge's 8 completeness passes, was split: $0 to save. |
| (e) pay ~$12 for a second Gridlock draw | **Skipped** | A measurement, not a fix: run-to-run variation cannot be switched off (no temperature on this model since 2026-09-24). Gridlock is not in the registry. |
| (f) page 37's gas mechanism | **Closed: moot** | Gridlock is not in the registry. It matters only if Gridlock is uploaded. |
| (f) the label "Direct confirmation — new evidence" | **Reworded, in its own render PR** | It names evidence that is not independent. On 0 cards today; on 4 in the pilot, none independent (3 other Morgan Stanley articles, 1 the same article re-read). |
| (k) do demand-driver names count as exposures? | **Yes, kept as is** | It changes no action. One active thesis carries one ("demand for generics", TH-DEB6560D7F), beside 4 other exposures. |
| (l) one unverified figure turns the week red | **Fixed here: red means broken** | See below. |
| (m) a cache-only replay says "$0" while skipping paid steps | **Fixed here** | See below. |

(g) stays open on one question: the full paid SemiAnalysis Beijing post (a clean save, and a
ruling on reading paid SemiAnalysis posts in full).

**(l) RED MEANS BROKEN.**
- QA's two research-completeness checks are marked `research`: "every reported figure captured or
  judged immaterial" and "every argument block accounted for".
- When one fails it prints `[OPEN]`, never `[FAIL]`.
- `qa` exits **3** when nothing is broken but research is open, **1** when an integrity check
  fails, and **0** when all pass.
- The weekly job's QA step turns exit 3 into a `::warning::` ("research verification INCOMPLETE —
  … nothing is broken") and records `result=research-open` in the state-branch commit message. It
  fails the job only on an integrity failure.
- `bin/theme-intelligence-weekly` does the same.
- **Why:** run 39565710165 went red on QA 21/22 for one restated figure ('36%',
  `capture_not_verified`). A quarter of the locally tested articles (8 of 32) carried an open
  figure, so red would have stopped meaning broken.
- **Not built:** the optional second half, which would accept a restated figure when a verified
  claim has the same number, unit and year. It trades against the 2026-10-11 Citi false match that
  made `states_figure` conservative. Open figures stay visible, and they no longer turn a week
  red.

**(m) A REPLAY SAYS WHAT IT DID NOT RUN.**
- `state.not_run` counts the run's completeness reports with `pass_ran` False and its
  `REVIEW_NOT_RUN` theses.
- The replay line now ends "— NOT run: the completeness pass for N document(s) and M card
  review(s); a paid replay would run (and bill) them".
- The $0 wording says "every model answer from the cache, $0" only when nothing was skipped.
  Otherwise it says "the answers it used came from the cache, $0", followed by what was skipped.
- `test_a_replay_is_answered_by_the_analysis_the_document_was_last_given` had pinned "every
  model answer from the cache, $0" on a replay with reviews switched OFF: exactly the claim (m)
  is about. Its proof that neither reading pass was asked again (`replay.calls == []`) stays.
  Its wording assertion now reads the truth: from the cache, $0, and the card review NOT run.

**HOW VERIFIED.**
- **(l), on the real red run** (R-20261021T080508Z-scan, the Actions registry, its cards
  rendered as the scan renders them):
  - main's code: `[FAIL] every reported figure … '36%'`, **exit 1**;
  - this branch: `[OPEN] …`, **exit 3**.
- **(m), the 2026-10-21 one-registry rehearsal re-run with this code.** It used a copy of the
  pilot, the branch at bfdc5266 and an invalid model key, so it could spend nothing.
  - Its two replay lines now read "… NOT run: the completeness pass for 1 document(s) and 1 card
    review(s) …" and "… for 4 document(s) and 6 card review(s) …".
  - The first time, the same rehearsal printed "every model answer from the cache, $0".
- **Pins** (`tests/test_theme_intelligence_red_means_broken.py`, 7):
  - END TO END through `cmd_qa`: an open figure and an open argument are OPEN with exit 3;
  - NEGATIVE: a broken hash is FAIL, exit 1;
  - the workflow's QA step and fail step;
  - the local script;
  - END TO END through `state.pull`: the replay names its skipped pass and review;
  - NEGATIVES: nothing skipped adds nothing, and END TO END says "every model answer from the
    cache".
- **Mutation:** 11 mutants, all killed.

**BOUNDARY.**
- Registry counts: `theme-intelligence-state` 9939047e (30 theses, 21 active), 2026-10-21.
- "A quarter of locally tested articles": 8 of the 32 distinct article URLs with a completeness
  record across the 132 local registries, 2026-10-21.
- The real red run: Actions run 39565710165.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A week with open research is green with a warning.** Its open items stay in the QA output,
  the readout and the desk ("research verification INCOMPLETE").
- **Falsifier:** an integrity defect that only the two research checks would catch. Nothing
  known: those checks read the reading's coverage, not the records' soundness.
