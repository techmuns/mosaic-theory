---
id:
status: recorded
date: 2026-09-17
prs: []
supersedes:
superseded-by:
---

# The rubric-v2 test runs five weeks late — its fail rule is fixed before a single draft exists

**WHAT.** The drafting-rubric v2 validation was pre-registered on 2026-07-15 for the **Aug 13
sweep**: *"`keep-for-checks` is expected to be the EXCEPTION, not the default … If Aug 13 shows
keep-for-checks creeping back to the default, THAT is the trigger to revisit."* **That sweep was
not run.** The next Component-A sweep ran **2026-09-17** (population `as_of` 2026-08-24, window
2025-08-25 → 2026-08-24, 251 trading days), and **the operator ruled 2026-09-17 that it counts as
the pre-registered test.** The pre-registration never said what "creeping back to the default"
means as a count, so **this record fixes it before `themes-draft` is run.**

## The verdict rule, fixed in advance

Population: the drafts `themes-draft` writes for this sweep — the **17 unreviewed clusters** (no
review in `reviews.json` overlaps ≥50% of the smaller member set).

| verdict | rule |
|---|---|
| **FAIL** | `keep-for-checks` is the most common `suggested` value among the drafted clusters. **A tie for most common counts as FAIL** — a joint default is not "the exception". |
| **PASS** | `keep-for-checks` is strictly less common than at least one other suggestion. |
| **CANNOT TELL** | any draft errors out (`unassessed-error`) and some assignment of those drafts would flip FAIL ↔ PASS. |

**Recorded beside the verdict, never scored:**
1. **Exact agreement** — draft `suggested` vs the analyst's recorded decision, per cluster. Jul-15 baseline: **5/11**.
2. **Draft `keep-for-checks` where the analyst parks** — the gap the Jul-15 check named. Jul-15 baseline: **4/11**.
3. **Drafts with a blank `draft_name`, `hypothesis` or `reason`.** `drafts.py::draft_cluster` validates only `suggested`, so a blank field passes silently.

## What makes it a fair test, checked at `0341af2`

- **The rubric is the one pre-registered.** `git log -- vinci/themes/drafts.py` shows two commits,
  both 2026-07-15 (#130, #133); `PROMPT_VERSION = "2"`.
- **The clusters are new to the drafter.** All 17 match no review.
- **The date slipped; the data barely did.** The window ends 2026-08-24, 11 days after the
  scheduled sweep; the run date is 2026-09-17. **No deferral ruling was found** (searched
  STATE.md, `docs/`, and `git log --grep` for `sweep`, `rubric`, `2026-08-13`). The slip surfaced
  2026-09-14.

## Weaknesses, written down before the result

- **The examples lean to park.** Every draft is primed with the 10 most-recent reviews: **9 park,
  1 reject, 0 keep-for-checks** (all reviewed 2026-07-15). A FAIL survives that push; a PASS is
  partly given by it. **Read a PASS as weaker than a FAIL.**
- **The batch is eligible for keep-for-checks.** The rubric allows it only on flat-or-lagging
  price, and **13 of 17** clusters lag IWM over 12 months. More keep-for-checks than Jul-15 is not
  by itself a failure — the rule above is about the default, not the count.
- **The review is not blind.** The operator ruled 2026-09-17 against deciding before seeing the
  drafts. **The verdict is unaffected — it reads the drafts alone, before any review exists.**
  Items 1 and 2 are exposed to anchoring and **are not comparable to the Jul-15 baselines**, which
  re-drafted clusters the analyst had already decided.

**BOUNDARY.** Every count is from scan `component-a/20260917T082645Z__0341af2.jsonl`: basis r2,
window 2025-08-25 → 2026-08-24 (251 trading days), primary band only (2,113 names; 2,080 with
enough history), ref = universe `as_of` 2026-08-24. **17** = clusters matching no review at ≥50%
member overlap of the smaller set, among 55 admissible. **13 of 17** = 12-month relative strength
vs IWM below zero. **9 / 1 / 0** = the 10 most-recent entries of `frontend/radar/reviews.json` by
`reviewed`, at `0341af2`. Jul-15 baselines are from
`docs/records/2026-08-26-capability-drafting-rubric-v2-park-default-runtime-few-sh.md` (11
clusters, one scan).

**WHAT IT COSTS / WHAT IS ACCEPTED.** 17 LLM calls on `claude-opus-4-8`. Accepted: the non-blind
review (operator ruling), and the park-leaning examples — they are part of the rubric as
pre-registered, and changing them now would be the second iteration the 2026-07-15 ruling did not
sanction.
