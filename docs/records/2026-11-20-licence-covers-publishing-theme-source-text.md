---
id: 2026-11-20-licence-covers-publishing-theme-source-text
status: shipped
date: 2026-11-20
prs: [1151]
supersedes:
superseded-by:
---

# The licence covers publishing the theme sources' text in the public repo (operator, 2026-11-20). The research reports' and the weekly scan's articles' words may be on the desk and the state branch; a local path still may not, and the history is not rewritten.

**WHAT.**

The operator's rulings, 2026-11-20, verbatim:
- **The licence.** Coordinator A asked: "Does the licence also allow publishing the reports' text word for word in this public repo, where anyone online can read it?" The question named the Goldman Sachs, Morgan Stanley and Citi reports. The answer: *"Yes, full text may be public"*.
- **The weekly scan.** Asked where the weekly scan should run, the operator answered: *"we don't want to run things manually here on mac and eventually wants to keep weekly run triggers on github actions eventually, whats the correct process? given that we have license & permission to keep the articles in public repo"*. So the licence also covers the weekly scan's web articles, and the scan stays on GitHub Actions as it is.
- **The state branch's history.** It holds 92 local file paths, showing this Mac's username and folder names. Asked whether to still rewrite it: *"No rewrite, fix paths ahead (Recommended)"*.
- **The desk's quote cap.** Asked whether the desk keeps #1140's 400-character cap: *"Keep the 400 cap (Recommended)"*.

What changes:
- **CLAUDE.md's Security section.** The Theme intelligence bullet now says the sources' text may be published, on the research desk (`frontend/theme-intelligence/`) and in the registry export on the `theme-intelligence-state` branch. "Still never published" no longer bars theme sources' text. The transcript rule (12 consecutive words, and a driver row quotes none) is unchanged. A local path is still never published.
- **Withdrawn**, because each was given to remove licensed text that this ruling now allows:
  - 2026-11-20: *"Public, no source words"* (the registry export) and *"Yes, same rule"* (the committed desk);
  - 2026-11-19: *"Purge history, backup first"*.
  - From 2026-11-19's *"Fix source + scrub tip"*, the source fix stays: the PDF reader misfiling body paragraphs as headings is a correctness bug in its own right. No scrub follows.
- **#1143 is superseded**, because it caps quotes and drops sections in the export. A smaller code PR replaces it: the reader fix, paths stored relative from creation, and a path guard on `export-state` and `state push`.
- **The research desk republishes (#1139)** from the current state tip under main's code, which carries #1140's cap.

**WHY.**
- **How it came up.** On 2026-11-19 the review of #1140 found report paragraphs on the public `theme-intelligence-state` branch: 31,207 distinct characters, filed as `blocks[].section` headings, at tip `a74c4e30`.
- **What A measured.** A's review of #1143 (2026-11-20) found the 400-character cap still left 28.7% of the 8 uploaded reports' body text in the export, and #1139's desk carried 16.3%.
- **The rule this replaces.** CLAUDE.md's Theme intelligence bullet (operator decision 2026-10-13, PR #703) allowed "titles, figures and SHORT verbatim source quotes … Never an article's text". The 2026-11-04 licence record left an article's text beyond short quotes out, as a choice that "the operator can widen … with a later record". This record widens it, for the theme sources only.
- **Why one ruling replaces several.** The rulings it withdraws were all made under the old rule, so they fall with it. Keeping them would have stripped every quote from the desk and the export, and needed a private word store plus a re-fetch or a private bucket for CI's articles. That cost is no longer needed.

**HOW VERIFIED.** A policy change with no code path. The record and STATE checks run on this branch: `tests/test_record_legibility.py`, `tests/test_records_ledger.py`, `tests/test_state_identifiers.py` and `tests/test_record_status_matches_open_now.py`.

**BOUNDARY.**
- **31,207 characters:** distinct `payload.blocks[].section` strings in `registry/article_versions.jsonl`, measured at state tip `a74c4e30` on 2026-11-19.
- **28.7% and 16.3%:** source runs of 40 characters or more, matched against the 8 PDFs uploaded on 2026-11-19 and re-read with #1143's reader (head `2bbc6efd`), with headings, titles and names excluded. 28.7% is 73,869 of 257,112 characters, measured on #1143's export of the local registry (8,899 rows). 16.3% is 41,990 characters, measured on #1139's desk at `f5dbfb68`.
- **92 paths:** occurrences in `evidence_location`, `runs.output_dir` and `runs.warnings` at `a74c4e30`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- Everything published is world-readable for good: this repo's history, the state branch and the desk.
- The ruling is the operator's reading of the licences. No agent re-checks the vendors' terms.
- Its scope is the theme sources only: the research reports the operator uploads, and the weekly scan's articles. It does not widen the transcript rule, CIQ workbook files, credentials, `*.db` or PII.
- The 92 local paths stay in the state branch's history, which is not rewritten. New exports write paths relative to the data directory once the path PR merges.
- **Backups, private and never pushed:**
  - `~/archive/theme-intelligence-state-before-purge-2026-11-19.bundle`;
  - `~/archive/ti-desk-and-export-branches-2026-11-20.bundle`;
  - `~/archive/ti-registry-before-words-out-2026-11-20.db`.
