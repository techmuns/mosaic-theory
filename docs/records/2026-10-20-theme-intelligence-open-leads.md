---
id: 2026-10-20-theme-intelligence-open-leads
status: recorded
date: 2026-10-20
prs: []
supersedes:
superseded-by:
---

# Theme intelligence: the weekly run keeps the answers it paid for, the first Actions run starts, and four open leads close

**WHAT.** STATE §5.0 row 32 (8), the agent's items (h) and (i), and the operator's (c) and (d).
Operator, 2026-10-20: "complete all steps in correct order". The order:
1. **U31f, the paid cache.**
2. **The leads.** Each was measured on the 132 local registries before it was changed:
   - (i) the figure ledger reading a figure REFERENCE as a figure;
   - QA's content-hash check;
   - the desk's counter-evidence gate;
   - the desk's Articles follow-up.
3. **The first weekly run on Actions**, on the PR branch, so it also proves U31f.

The operator's rulings ((a), (f), (k), the prompt cache in (d)) and the paid options ((e), (g)) are
theirs and stay open. The stale test branch in (d) is deleted.

**THE FIXES.**
- **U31f — the weekly run keeps a failed run's paid answers.**
  - The combined `actions/cache` saves in its post-step only when the JOB succeeds. This job
    fails on purpose when the scan fails or QA does not pass, so a failed run's paid model output
    was thrown away and the retry paid again.
  - The workflow now restores with `actions/cache/restore` and saves with `actions/cache/save` in
    its own step: `always()`, right after the scan, skipped only when the scan never ran or wrote
    nothing.
  - The key carries the run AND the attempt. A cache key is written once, so a re-run of the
    same run must save under its own key.
- **(i) A figure reference is not a figure.**
  - `completeness._skip_number` reads a number that NAMES a figure, table, exhibit, chart,
    section, statute (§), appendix, slide or page as a reference. Only punctuation and a PDF's
    table debris may stand between the word and the number.
  - It runs after the unit test, so a number with a unit ("5 pp", "23%") is always a figure.
  - The decimal half of the 2026-10-11 lead ("2,358.5GVA" read as "2,358") was already fixed on
    2026-10-14, when `GVA` joined the ledger's units.
- **QA's "version content hashes recompute" hashes the content AS STORED.** `card_sha(v.content)`
  re-serialised the PARSED content through today's model, so a field the schema gained later,
  with its default, moved the hash of an intact version. The pilot's six were written before
  `s07_what_could_go_wrong.price_context` existed.
- **The desk's counter-evidence gate reads the stored verdict.** It used to be inferred by
  elimination: added only when a WATCH passed every other gate. It now reads `counter_verdict`,
  the F8 value the card and the weekly report already read (U53), whenever the verdict holds.
- **The Articles follow-up is the ONE partial-awaiting-full rule.**
  - `desk.week_articles` kept a third copy of `report.partial_ask` that never read unreadable
    pages.
  - It now asks what the rule asks:
    - "Check the unreadable pages", pointing to Uploads;
    - "Supply the full report";
    - or nothing.
  - Where nothing is asked, it says why: the channel was retired; only back-matter pages could not
    be read; or the channel is preview-only by decision.

**DOES THIS SELECT ON FORM?** No. Theme intelligence is research attention, off the decision path:
- the ledger change decides which numbers are figures;
- the QA change decides what counts as intact;
- the desk changes decide what a page names.

None ranks or gates a name.

**HOW VERIFIED** (the 132 local registries under the pilot worktree's
`data/theme_intelligence/v2/`, each read on a backup-API copy; the live pilot never opened for
writing).
- **(i)** 27,758 stored ledger figures. Main's current rule against this one, on the same stored
  sentences: the new rule drops exactly 4, all references.
  - "see Figure | | | ; | 23";
  - "section 165(c)";
  - "§39.169", a Texas statute;
  - "Penn World Table 10.0".
  Three were open (uncaptured) items, so the change closes three false open items and drops no
  real figure.
- **Hashes.** 1,011 stored versions:
  - the stored content reproduces the stored hash on 1,011;
  - main's re-serialisation reproduces it on 42.
  On the live pilot's 29 runs, the check failed 4 under main's method and 0 now.
- **The gate.** 16 latest versions carry a counter-evidence verdict. Main's desk showed the gate
  on 1 of them; it shows it on 16. No WATCH is left with every gate passing (which elimination
  could have explained): 0.
- **The follow-up.** 81 PARTIAL article rows.
  - On main, 62 agreed with the shared rule. 8 asked for "the full report" for a supplied document
    whose pages needed a visual check. 11 asked for one where only back matter was unreadable.
  - Now 81 of 81 agree.
  - The 11 rows say "Nothing to ask — only back-matter pages could not be read".
- **The live pilot alone** shows neither desk lead today: its 3 PARTIAL rows already agreed, and
  no thesis carries a verdict. The leads were real on the wider corpus, which is why it was
  measured.
- **Pins** (`tests/test_theme_intelligence_open_leads.py`, 11, on committed fixtures through the
  real functions):
  - the four corpus sentences, and figures beside a reference that must stay, including words
    between a reference word and its number;
  - a stored version in the pilot's exact shape (no `price_context`), and a tampered version that
    must still fail;
  - the batch-B contested case through `desk.gates`, with its negative;
  - the preview-only unreadable case through `desk.week_articles`, and its back-matter variant;
  - a text lint of the workflow's cache steps, and the combined form main carried as its negative.
- **Mutation:** 13 mutants, all killed.
- **Suite:** ruff and `mypy --strict` clean; `pytest -m "not network"` with the store moved
  aside, 6,018 passed / 526 skipped.

**THE FIRST WEEKLY RUN ON ACTIONS (U31f's proof).** Started 2026-10-20 17:55 UTC on
`fix/theme-intelligence-open-leads` (run 39470335127):
- defaults: a 10-day window, at most 25 articles analysed;
- expected at most about $30, at the pilot's $1.19 per analysed article.

Its result is below.

**(d) The stale test branch is deleted.** `theme-intelligence-state-test-20261011` held only
SYNTHETIC commits from 2026-10-11, with no PR. Tip `8d9d00a73fa025fc05974f91f870637f85503d7c`;
restore with `git push origin 8d9d00a73fa025fc05974f91f870637f85503d7c:refs/heads/theme-intelligence-state-test-20261011`.

**BOUNDARY.**
- **Code:** main 07665419.
- **Corpus:** the 132 registries present on this machine on 2026-10-20, of which the live pilot
  `pilot-2026-10-12` is one (13 articles, 38 versions); the rest are test and probe registries
  from 2026-10-10 to 2026-10-16.
- **Units:** counts of stored figures, versions, runs and rows.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The ledger change re-bills a completeness pass only for an article whose ledger it changes.**
  Four stored figures across the corpus; the first Actions run starts from an empty cache anyway.
- **The first state-branch commit comes from this PR's branch, not main.** The run is the only
  way to prove U31f before merge, and the branch differs from main only by these fixes. If the PR
  changes, the state branch keeps that run's records.
- **Still open, the operator's:**
  - (a) whether a qualitative sell-off is a dislocation;
  - (d) the article prompt cache;
  - (e) a second Gridlock draw (~$12);
  - (f) page 37's card;
  - (g) a paid re-enrichment;
  - (k) demand-driver names as exposures.
