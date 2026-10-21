---
id: 2026-10-21-theme-intelligence-review-resolution
status: recorded
date: 2026-10-21
prs: []
supersedes:
superseded-by:
---

# Theme intelligence: a reviewer can dismiss a review warning — with a name and a reason, kept append-only, and verifying nothing

**WHAT.** Follow-up B of `docs/records/2026-10-13-theme-intelligence-research-desk.md`, built at
the operator's direction ("yes, start B and A", 2026-10-21).

- **The command (`resolve.py`, CLI `review`), $0, no model call:**
  - `review list [--thesis TH-…] [--history]` shows every card-review finding on the current
    versions: its key, its state (OPEN / DISMISSED / WITHHELD / NOT RE-REVIEWED), the line, the
    review's words, and either the dismiss command or why it cannot be dismissed. `--history`
    prints every row ever recorded.
  - `review dismiss --finding F-… --reviewer NAME --reason "…"`, and `review reopen` with the
    same arguments.
  - Each dismissal or reopening is a run of mode `review`. It writes one row and renders its run's
    outputs.
- **The record:**
  - `ReviewResolution` rows sit in a new append-only table, `review_resolutions` (registry
    schema **v8**, migration 8, UPDATE/DELETE triggers).
  - Each row records the version, line, finding key, code, the finding's words, the line's words
    and cited evidence, the action, reviewer, reason and time.
  - The latest row for a key is its state. Every earlier row stays.
- **The key (`report.finding_key`)** is built from the thesis, the version whose review made the
  finding, its stored words, and the line's words and cited evidence now:
  - carried onto a later UNREVIEWED version with the same words, the finding keeps its dismissal;
  - a NEW review's finding has a new key, so it is open again (version-specific);
  - so is a changed line.
- **What a dismissal does:**
  - The finding stops counting as OPEN on the card's header, the desk's Review screen and the
    weekly report.
  - It is shown as history: "Dismissed by X on D — reason". The card keeps the review's words
    under the line (folded on screen, open in print).
- **What it never does** ("accepting a warning never makes unsupported evidence valid"):
  - The line stays in `flagged`, so its label stays capped: it is never shown as a verified fact.
  - A WITHHELD line is never dismissible. It closes by an analyst correction that passes the card
    checks (`reassess --corrections`) or by a re-review.
  - A line changed since its review (NOT RE-REVIEWED) is never dismissible.
  - No research-action rule reads the record: priority, engine and pipeline never mention it
    (pinned).
- **Also:**
  - **Weeks.** `review` joins `report.REFRESH_MODES`, so it never opens a desk week.
  - **As of.** A page rendered as of an earlier run never shows a later dismissal.
  - **`state pull`** carries a local review run WHOLE: the run and its rows unchanged, never
    stranded, never `ledger_only`.
  - **`qa`** re-checks each row against the finding it names.
  - **The desk** names each open finding's key and dismiss command in the audit view.
  - **Docs.** `docs/theme_intelligence.md` is updated.

**WHY.**
- Until now a review warning closed only through an analyst correction or a re-read.
  - A reviewer who read a finding and judged it immaterial could not say so.
  - So it stayed open for good: 58 open findings on the live desk, 39 of them marked as
    affecting an action.
- The design keeps the record honest in both directions:
  - nothing is edited (append-only);
  - nothing is upgraded (the label cap);
  - nothing is dismissed that nobody read (no withheld or changed line).

**HOW VERIFIED.**
- **Real data — the registry of record** (`theme-intelligence-state` 9939047e) was imported fresh
  into a SCRATCH directory with this branch. The probe dismissal ran there only: reviewer
  `verification-probe`, reason "PROBE … not a research judgement; never pushed". Nothing was
  pushed or published.
  - **`review list`:** 56 findings on 18 theses — 47 dismissible, 9 withheld.
    - Of the 9 withheld lines, 8 were withheld by the review itself. One (TH-16225B12C4 s06.1)
      was withheld by a card check (NUMBER_NOT_IN_CITED_CLAIMS) next to a review warning.
  - **A bug the real run found:** the first build listed that line as NOT RE-REVIEWED, while the
    refusal correctly said withheld. One structured field (`LineFinding.withheld`) now decides
    both, and the real shape is pinned.
  - **The probe** (the non-trivial case): F-b506e7ce82c7 on TH-38CA111885 s06.0, a line stored as
    **MEASURED OBSERVATION**.
    - Before the dismissal it printed SOURCE OPINION, capped by the open finding. After the
      dismissal it **still printed SOURCE OPINION**.
    - The card header changed from "Review required · 4 line(s)" to "3 line(s) · 1 review
      finding(s) dismissed by a reviewer".
    - The desk's Review screen went from **58 → 57** open findings and **39 → 38** affecting an
      action. Its history went from 23 → 24.
    - The weekly report went from "lines withheld or questioned (61) → (60)". Its "Resolved or
      historical" went from 0 → 1.
    - The week label was unchanged ("Week of 12–21 Oct 2026 …"): no empty week.
  - **Refusals on real findings:** the withheld line was refused, and a second dismissal was
    refused.
  - **`qa` on the review run:** 22/22 passed, including "every resolution names a finding it may
    resolve: 1 resolution(s)".
  - **Screenshots** are in `docs/theme_intelligence/review-resolution-2026-10-21/`:
    - the card line before and after on screen (`card-line-screen-*.png`, the finding folded);
    - after in print (`card-line-print-after.png`, every `<details>` open, as the PDF);
    - the Review screen before and after (`review-*.png`, with the dismissed entry in the history
      fold).
- **Pins:** 13 tests in `tests/test_theme_intelligence_review_resolution.py`, end to end through
  the rendered card, desk, weekly report, CLI, `state pull`, export/import and `qa`.
  - **Negative pins:**
    - a withheld line (by the review, or by a card check next to a warning) is refused;
    - a changed line is refused;
    - a blank reviewer or reason is refused;
    - an unknown key, a second dismissal, and a reopening of nothing are refused;
    - UPDATE and DELETE on the table abort;
    - a forged row for a withheld finding never applies, and `qa` fails it.
  - **Positive pins:**
    - the dismissal holds on an unreviewed version;
    - a new review reopens it;
    - an earlier run's pages never show it;
    - a fact-labelled line stays capped.
- **Mutation:** 23 mutants, 23 killed. Two first survived and got pins:
  - the report rendering as of now;
  - a dismissal lifting the label cap — the synthetic lines were all forecasts, so the first
    assertion was vacuous.
- **Suite:** see the PR.

**BOUNDARY.**
- **Registry and date:** registry `theme-intelligence-state` 9939047e, imported on 2026-10-21 with
  this branch (base main c5b3f3c2).
- **Three counts, three populations:**
  - **`review list`** counts card-review findings on the CURRENT versions of non-archived theses:
    56. It counts only lines a review finding names.
  - **The desk's Review screen** counts open items: 58. That is 47 review warnings plus 11 withheld
    lines, including 2 withheld by card checks with no review finding.
  - **The weekly report** counts "lines withheld or questioned" across its cards: 61.
- **Before and after:** every "before → after" pair is two scratch publications of that registry,
  without and with the one probe dismissal.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0; registry schema v8.** Code older than this refuses a migrated registry, as at every
  migration.
- **A dismissal is a judgement the operator owns.** No finding on the registry of record has been
  dismissed. Which of the 47 to dismiss is the operator's research call, and each one names its
  reviewer.
- **Accepted:** a dismissed finding a later review raises again is OPEN again (a new key). A
  re-reviewed thesis can bring back a finding the reviewer already dismissed. Its earlier
  dismissal stays in `review list --history`, but not on the new item.
  - *Falsifier:* if re-raised findings come back often enough to bury new ones, carry the earlier
    dismissal onto the item as context — never as the state.
