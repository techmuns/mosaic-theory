---
id: 2026-11-10-upload-ledger-reads-the-recorded-cost
status: recorded
date: 2026-11-10
prs: []
supersedes:
superseded-by:
---

# The one-step upload's ledger check reads the run's cost at the 4 places it is recorded to — the first real paid upload was refused after paying

**WHAT.** `vinci/theme_intelligence/upload.py`'s step 5, the paid-call ledger, now allows the
run's recorded cost to differ from the unrounded sum of its calls by half its last place
(`_RUN_COST_ROUNDING = 0.5e-4`, plus the existing `_CENT = 1e-6` slack). Every other condition is
unchanged:
- every earlier call is unchanged;
- every new call is the import's and priced;
- the spend is within the budget;
- a gap wider than the rounding is still refused, now pinned at $0.9389 against $0.9388.

**WHY.** The pipeline records a run's cost rounded to 4 places (`pipeline.py`,
`run.cost_usd = round(cost, 4)`, since #703). The ledger step, built later by #769, compared that
figure with the unrounded sum of the run's calls, allowing only $0.000001. Any run whose calls
sum to a fifth or sixth decimal is therefore refused, which is almost every real run.
- **The incident, 2026-11-10.** The operator's 10 manual uploads (Goldman Sachs and Morgan
  Stanley web articles, licence and budgets stated by the operator) began with the S&P 500
  piece, run R-20261110T140515Z-ingest.
  - It imported and passed QA 21/21, then was refused at the ledger: "the new calls sum to
    $0.9388, the run records $0.9388 — nothing pushed".
  - Its 7 calls summed $0.93881 against the recorded $0.9388, a gap of $0.00001.
  - $0.9388 was paid and nothing pushed. The other 9 were not attempted.
- **Why no test caught it.** The test's `FakeModel` bills every call at 1,000 in / 400 out
  tokens, $0.015 at its price, so its sums always land on 4 places. The happy path never carried
  a gap. The constant's own comment, "rounding tolerance when the new paid calls are summed
  against the run's cost", names this purpose; its value did not fit it.

**HOW VERIFIED.**
- **Tests first, both failing on the unfixed code:**
  - `test_a_run_cost_recorded_to_four_places_still_reconciles_and_pushes` is end to end: a fake
    model billing $0.01504 a call, upload → ledger → push. Before the fix it was refused with
    "the new calls sum to $0.0451, the run records $0.0451". The test also asserts its own
    premise, that the gap is real (between 1e-6 and 0.5e-4).
  - `test_the_ledger_reconciles_a_run_cost_recorded_to_four_places` is the incident's real
    shape: its 7 call prices against $0.9388.
- **Negative pins:** $0.9389 of calls against a recorded $0.9388 is still refused, with the same
  message as before; so is $0.93886, a gap of $0.00006, just past the allowance. Only that
  boundary pin fails when the allowance is loosened to $0.00009.
- **On the real ledgers.**
  - "Before" is the paid-call ledger of `theme-intelligence-state` 736a3fb8, imported fresh:
    342 calls. "After" is the local registry holding the refused import: 349 calls.
  - With the allowance at 0, which is the old behaviour, the check is refused with the incident's
    message.
  - With the fix it passes: "342 earlier paid call(s) unchanged; 7 new, all the import's, $0.9388
    (within $7.22)".
- `tests/test_theme_intelligence_upload.py`: 28 passed, the 4 new pins among them. The suite:
  see the PR.

**BOUNDARY.**
- The allowance is half of the last place the pipeline records, $0.00005 a run. A real mismatch
  smaller than that passes. The other ledger conditions (unchanged earlier calls, every new call
  the import's and priced, the budget) do not depend on it.
- The incident's figures are from run R-20261110T140515Z-ingest on 2026-11-10, against
  registry 736a3fb8.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0 for the fix.
- The refused import's $0.9388 is not lost: its answers are in the local LLM cache. A re-run of
  `upload` replays it at $0 from that cache, then pushes it.
- **Not in this change,** found in the same run and left for its own fix: the reader takes a
  PDF's metadata author "Un-named" as a byline. "Why Investors Are Reducing AI Exposure" (Goldman
  Sachs) would credit "Un-named" beside the analyst its text names.
