---
id: 2026-10-13-theme-intelligence-review-carry
status: recorded
date: 2026-10-13
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — a version written without the card review keeps the earlier open findings and says it was not reviewed

**WHAT.**
- **The defect** (OPEN in `2026-10-13-theme-intelligence-research-desk.md`, whose body stands as
  written). Some runs record `REVIEW_NOT_RUN` for a thesis: `--no-review`, the review budget
  exhausted, or no model client and no cached review. The new version they wrote showed only its
  own run's findings, which were none. So the previous version's open finding vanished from the
  card, the weekly report and the desk's Review screen, even on an unchanged line.
- **The fix** (`report._findings`, behind `line_findings` and the new `review_carry`). The card,
  the weekly report and the desk all read it. For a version whose run recorded `REVIEW_NOT_RUN`,
  every open finding of the version before stays open:
  - **Same words, same cited evidence:** the finding stays on that line as UNRESOLVED REVIEW, with
    the version and date that made it.
  - **Changed words or evidence:** the line (the same words elsewhere, or the same line id) reads
    **NOT RE-REVIEWED**, quoting the line as the review read it.
  - **Line removed:** the finding is listed as removed. It stays open and is never resolved.
  - **A review that withheld a line** (REVIEW_UNSUPPORTED) keeps withholding the same line.
  - The carry chains across consecutive unreviewed versions back to the last review that ran.
- **Disclosure.** Every version the review never read says so, even with no earlier finding: a
  "Not reviewed" note in the card header and Markdown, and a "Not reviewed" item on the desk's
  Review screen and reading page. It never reads "No unresolved review findings".
- **What does not change.**
  - **Nothing is copied or edited.** Each finding is read from the run that made it, so there is
    no duplicate. The first-raised date and version are the original's.
  - **Research actions and priority** are not recomputed. A questioned line still never reads as a
    verified fact (the existing label cap).
  - **The deterministic card checks** are each version's own; they always run.
- **A review that RUNS stands on its own findings (the existing rule).** A finding it does not
  raise again is no longer open; one it raises again stays open. The relabel rule
  (`finding_scope`) still applies only to label-only findings.

**WHY.** A skipped review is not a clean review. Before the fix, `--no-review`, an exhausted
review budget or a missing client could make an open finding disappear without anyone resolving
it.

**HOW VERIFIED.**
- **Through the REAL pipeline review path** (`Pipeline._review`), with an offline fake reviewer
  for the reviews that run (no network, no paid call). The articles are SYNTHETIC on the reserved
  `.test` domain. All three review-unavailable paths are covered: `--no-review`, the budget
  refused (the guard sends nothing), and no client with no cache. Tests in
  `tests/test_theme_intelligence_review_carry.py`:
  - v1 reviewed with two findings. v2, unreviewed: the identical bottom line keeps its finding on
    the card ("raised by the review of version 1") and on the desk's Review screen (raised date
    and version 1 kept). The changed What-changed line reads NOT RE-REVIEWED. The header says Not
    reviewed and never "No unresolved review findings". Only v1's findings are stored, unedited.
    Rendering writes nothing.
  - A chain of two unreviewed versions still carries from version 1.
  - A later successful review that raises nothing clears it. One that raises it again keeps it.
  - A brand-new thesis the review never read says so (all three paths).
  - A removed line's finding stays open. The same words on other evidence read NOT RE-REVIEWED.
- **Mutants:** 8 of 8 killed — no carry, a changed line read as unchanged, evidence ignored, a
  removed line's finding dropped, the carry crossing a successful review, the first-raised version
  replaced, an unreviewed card shown as clean, a changed line labelled as an ordinary finding.
- **Real pilot unchanged:** its registry has no `REVIEW_NOT_RUN` (every pilot version was reviewed
  or carried by a re-grade). The desk renders the same counts as before: 0 broken links, 0
  default-view ids or codes. The 6- and 12-week stress desks are unchanged too.
- **The private preview** adds a labelled synthetic demo: v1 reviewed, v2 with `--no-review`. It
  shows the old warning on the card and on Review.
- **Gate:** ruff, `mypy --strict` and the offline suite — results in the PR.

**BOUNDARY.**
- "Unreviewed version": a thesis version whose run holds a `REVIEW_NOT_RUN` issue for that thesis
  (`report.review_not_run`).
- "Open finding": the card-review findings (REVIEW_PARTIAL, REVIEW_INFERENCE_UNSUPPORTED,
  REVIEW_UNSUPPORTED) on the last reviewed version, plus those carried onto it, after the relabel
  rule.
- "Real pilot": the copy of `data/theme_intelligence/v2/pilot-2026-10-12/registry.db` at
  `R-20261012T133456Z-reassess`, checked 2026-10-13.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0: no model call, no record written.
- **Accepted: the research action of an unreviewed version stays as the engine computed it.**
  When an earlier review WITHHELD a decision-bearing line, the engine put that version on a
  verification hold. An unreviewed later version is not re-held: the line shows withheld, but the
  action is not recomputed (the brief: keep the existing action). Falsifier: an unreviewed version
  promoted to Research Now while a carried withheld line bears on it — the desk lists the withheld
  line as decision-affecting, so it is visible.
- **Line matching is by words first, then by line id.** A rewritten line that moved to another
  position and kept no words is reported as removed (open), never as clean.
