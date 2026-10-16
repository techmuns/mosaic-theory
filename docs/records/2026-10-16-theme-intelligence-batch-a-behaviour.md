---
id: 2026-10-16-theme-intelligence-batch-a-behaviour
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — batch A of the verified review leads, the behaviour fixes: U11, U60a, U51, U31a, U31c, U31d, U37, U57, U33 (U31f stopped)

**WHAT.** Operator, 2026-10-16: "yes start with U35 and then build both batches". Batch A holds
the remaining leads that change what the product does. They are groups 8 and 9 of the grouping in
`docs/records/2026-10-15-theme-intelligence-group-5-facts.md`, plus U33. Group 9's U28 is in
batch B.

| Lead | Defect | Fix |
|---|---|---|
| U11 | A proposed company was refused as "the source already names it" when its name merely began like a named company's ("Meta" / "Meta Materials"). | **The names alone cannot decide.** "Rockwell" / "Rockwell Automation" (one company, the pilot's) and "Meta" / "Meta Materials" (two) have the same shape. A proposal named like a named or already-proposed company, and carrying a ticker, is now resolved first. It stands only when the SEC verifies a listing that differs from EVERY same-named company's verified listings. An unverified ticker proves nothing, so the names decide. Its note says what it was named like. A duplicate is never sent for its 10-K. |
| U60a | The desk had its own name rule: "AT&T" split into "at", "t" and hid "AT", and a name with no ASCII letters hid every later name. | **One rule for the enrichment and the desk:** `verify.same_company`, with `distinct_listings` for two companies the SEC verified apart. A legal form ("AG", "Inc") may only make two names EQUAL. Dropped before the prefix test, as the enrichment's rule had dropped it, "Siemens AG" became a bare "siemens" that matched "Siemens Energy". |
| U51 | Only Citi's house names were excused, hard-coded, so "(J.P. Morgan, Oct 2)" was an unrecorded organisation. | **Any configured or retired publisher CITED as a dated source is a source.** The article's own publisher is excused in any form. A publisher named in a LIST ("lenders such as Goldman Sachs") may be an exposure, and is still said. |
| U31a | A channel going ERROR → DEGRADED alerted "RECOVERED". | **RECOVERED only when no longer failing.** ERROR → DEGRADED is a changed failure (NEW_FAILURE). |
| U31c | `bin/theme-intelligence-weekly` exited 2 for a PARTIAL scan whose QA failed; its header says 1. | **QA not passing is 1, whatever the scan said.** |
| U31d | A J.P. Morgan listing with no card fell back to the sitemap and blamed "no dates", which masked the "dropped to zero" alert. | **No card on an accessible listing is a layout change:** the adapter raises, as Citi's does. Undated cards still fall back to the sitemap. |
| U37 | An unpriced paid call printed "$0, every model answer from the cache" on a `state pull` replay, and counted as $0 in the carried-runs summary. | **An unknown cost is said as UNKNOWN**, and unpriced calls are counted apart. |
| U57 | The run's spend limit was set on the guard after the run started (six sites), and a CLI failure kept no traceback. | **`Pipeline.start_run(budget=)`** sets it as the run starts. The CLI's unexpected failures record the traceback, as the pipeline's do. |
| U33 | A replay read the operator's same-as / duplicate / new decision back out of a display sentence (`match_basis`), so a reword would re-identify a document silently. Card findings attach by their message text, written by six producers in three shapes. | **The decision is stored as a value:** `DocumentRecord.decision` and `decision_article`. A record from before it is read by `ingest.operator_decision` from the one sentence its writer shares (`SAID_SAME_AS`, `SAID_DUPLICATE`, `SAID_NEW`). The findings are pinned as a round trip through every real producer to `line_findings`, so a reworded producer turns a test red. QA's regex was already loud and is unchanged. |
| U31f | `actions/cache` saves only when the job succeeds, so a failed run's paid answers are not kept. | **STOPPED.** The fix (`actions/cache/restore` + `actions/cache/save` with `if: always()`) can only be proven by an Actions run, and the weekly run has never run on Actions (§5.0 row 32 (8)(c)). It is not written. It stays open with the first manual run. |

**WHY.** Each of these:
- refused a real company;
- hid one on the desk;
- flagged a source as an organisation;
- alerted a recovery that was not one;
- exited with the wrong status;
- masked a broken listing;
- printed a guessed $0;
- or, in U33's case, rested a replay's identity decision on the wording of a sentence.

**HOW VERIFIED.**
- **The live corpus** (CORPUS BEFORE SYNTHETIC; copies of every local registry, main 4283a3e0 against this branch):
  - **U60a:** every stored thesis version's exposure block was rendered on both codes. **0 of 1,050 change.** The first form of the shared rule changed 19: it hid "Siemens AG" behind "Siemens Energy". That flaw is the U11 one, so the rule was corrected before pinning.
  - **U11:**
    - The pilot's stored enrichment refused 2 distinct proposals by the name rule. Both were real duplicates: a second "Amazon.com" (AMZN), and "Rockwell" with a wrong ticker (DDAIF) after Rockwell Automation (ROK).
    - Under the new rule AMZN still matches the kept AMZN listing, and DDAIF cannot verify apart. So both stay refused.
    - The cached answers were made under the enrichment prompt before #718, so they cannot be replayed for free.
  - **U51:** 113 stored NAMED_NOT_RECORDED issues; 0 name a publisher.
  - **U31a:** 230 stored health records; 0 ERROR → DEGRADED transitions.
  - **U37:** 390 stored runs; the 7 with an unknown cost are all unfinished (RUNNING) runs in local test registries, never an unpriced call.
  - **U33:** 80 stored documents. The new reader gives each the same decision as the old sentence parse: 77 none, 2 same-as, 1 duplicate.
  - So U51, U31a, U37 and U33 change no stored result; they are pinned on constructed cases.
- **Pins:** `tests/test_theme_intelligence_batch_a.py`, 38 tests, each fix with its negative:
  - the enrichment end to end through `enrich_thesis`, with a resolver double that verifies some tickers;
  - the desk's exposure block;
  - a cited and a listed publisher through `process_document`;
  - the health checker over a scripted web (HEALTHY → ERROR → DEGRADED → HEALTHY);
  - the JPM adapter with no card and with undated cards;
  - the weekly runner itself, in a scratch repository with a stand-in for python;
  - a `state pull` replay that pays an unpriced call;
  - the CLI's failure record;
  - a replay decision under a reworded sentence, and the round trip of every finding producer.
- **Mutants: 18 of 18 killed.** An unmutated baseline passes. One test was order-dependent at
  first: two blocking findings on one line. It was split before the mutants ran.
- **Suite:** ruff clean, `mypy --strict vinci` clean (189 files), and the offline suite is green. The final count is in the PR.

**BOUNDARY.**
- Code: main 4283a3e0 (#725 merged, plus #726's U35 restatement) against this branch, 2026-10-16.
- Registries: copies, made with the SQLite backup API, of the 147 `registry.db` files under the `theme-intelligence` worktree's `data/theme_intelligence/` (backups excluded). The live pilot's checksum is unchanged (5fcc240d4b087d2feb1f81e6d6fabc3c).
- Exposure blocks: one per stored thesis version (1,050 across 134 registries), rendered with no enrichment and no business groups.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no model or SEC request (the resolver is a test double; the corpus copies are read offline).
- **A proposal named like a known company, with a ticker, costs one SEC lookup before it is decided.** It is cached like any resolution.
- **Names alone still cannot tell two companies apart** when neither has a verified listing. "Meta" and "Meta Materials" with no verified listings stay one company. *Falsifier: a distinct company refused while the SEC verifies it.*
- **`DocumentRecord` gains two optional fields**, and every record this code writes carries their keys. Code older than this PR refuses such a record (`extra="forbid"`), so the `theme-intelligence` worktree, where the pilot lives, moves to main with the merge.
- **U31f is open** until the first Actions run.
