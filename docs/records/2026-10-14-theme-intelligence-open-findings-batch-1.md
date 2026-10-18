---
id: 2026-10-14-theme-intelligence-open-findings-batch-1
status: recorded
date: 2026-10-14
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — open review findings O1-O7, O13, O14, O19-O21 fixed

**WHAT.** Operator, 2026-10-14: "go ahead with 1 and 2 first" — (1) record the open findings
(`docs/records/2026-10-14-theme-intelligence-open-review-findings.md`), (2) fix O1-O7, O13, O14
and O19-O21. Twelve findings, each with a regression test that fails without its fix.

| # | Fix |
|---|---|
| O1 | `parse_text_date` replaces "Sept" only as a WORD: "September 30, 2026" is read (it became "Sepember", UNKNOWN). |
| O2 | The "Published <date>" fallback reads the page WITHOUT its noise elements and without everything from the first related-content heading on (`parse._own_page_text`, reusing `_noise`). A related card's date no longer dates the page. |
| O3 | A related-content heading must be the WHOLE heading, not its first words. "More from" stops only before a capitalised name. "Recommended positioning for 2027" no longer cuts the article. |
| O4 | The quarter-label excuse takes a year only when one is attached ("3Q26", "Q3'26", "Q1 2027"), never a figure after it ("In Q3 45%"). A period LABEL is checked as a period: when the cited claims carry labels of the same kind, the line's must be one of them ("4Q27" against "3Q26" is a BLOCK). |
| O5 | `_CHANGE` matches whole word forms of the SAME vocabulary, never open stems. "accelerator", "surgical", "momentum" and "moment" (via `MoM`) are not changes; "contracted" counts only before a figure. |
| O6 | A hypothesis's affected company is found by the name as written, else by its normalised name. "Caterpillar (CAT)" finds the mention "Caterpillar"; "Alphabet Inc." finds "Alphabet". |
| O7 | `Store.linked_claim_ids` counts only LIVE theses' links: a retired thesis carries nothing now. |
| O13 | An already-stored claim or mention id keeps its first record on EVERY pass (it was re-analysis only), so a retry of a run that died mid-article no longer fails for good. |
| O14 | The post-scan enrichment turns ANY failure into a run warning (the SDK's errors are not RuntimeErrors). |
| O19 | The router awaits the view, so a view's failure is shown. The desk view, finding no desk page (Pages serves the app's index for a miss), says "not published", or "not in the published research desk" with a link home. |
| O20 | A card's source title links only to an http(s) address (the desk's `_link` rule). |
| O21 | Area links URL-encode the name ("Healthcare · Pharma & biotech"). |

**WHY.** Each is a defect a verifier reproduced: a wrong fact, a silent loss, or a failure.

**HOW VERIFIED.**
- **Corpus before synthetic**, old (837d2bb8) vs new, read-only:
  - **Pages and dates (O1-O3):** 281 distinct real HTML pages from the local HTTP caches plus
    the HTML fixtures; **0 change**.
    - The stop-heading rule matches the old one on all **564 distinct real headings** (7 stop
      headings, the same 7).
    - Two first drafts were caught here: one dropped "Explore more of our thought leadership",
      the other added "Related Stories". Both were corrected before shipping.
  - **Card checks (O4):** 551 thesis versions across 147 local registries, **0 differences**;
    the live pilot's current versions, 0.
  - **Change words (O5):** 2,203 distinct stored claims. The new rule only REMOVES matches:
    "moment" 6, "momentum" 5, "accelerator" 1, "contracted spending" 1. It adds none.
    - A first draft also dropped "increasingly" and added "expansion"; it was corrected to
      the old vocabulary exactly.
    - One claim stops counting as a fundamental change: "$150B of contracted spending", a
      level.
  - **Names (O6):** 105 stored UNSUPPORTED_ENTITY refusals; **22 name an entity the same
    registry records as a mention.** Read in one registry, they are the variant-spelling shape:
    the hypothesis names "Caterpillar (CAT)" and "GE Vernova" against the mentions "Caterpillar"
    and "GE Vernova (GEV)", across 11 re-read registries of one report.
    - This changed the fix: the first draft (register an alias only when two mentions share an
      id) would not have covered it.
- **A real run on the pilot, $0:** `run_reassess` of all 23 theses from stored evidence, on a
  copy. Old and new code give **identical** outcomes: no action changes, one card-line issue
  each (the same one). The pilot's checksum is unchanged.
- **Pins:** `tests/test_theme_intelligence_open_findings.py`, 13 tests, each with its negative.
  O19 runs the real `desk.js` under node with stubs for `fetch` and `DOMParser`.
- **Mutants: 14 of 14 killed.**
  - On the first pass, O3 survived because its test sliced the HTML mid-tag; the test was fixed.
  - O6's alias line survived because the normalised-name lookup already covers it; it was
    removed as redundant.
- Ruff and `mypy --strict` are clean, and `node --check` passes; the offline suite result is in
  the PR.

**BOUNDARY.**
- "281 pages / 564 headings": every cached HTML body under the `theme-intelligence` worktree's
  `data/theme_intelligence/**/http_cache*`, distinct by content, plus
  `tests/fixtures/theme_intelligence/**/*.html`, read 2026-10-14.
- "2,203 claims / 551 versions / 105 refusals": the 147 local registries (backups excluded),
  distinct by id.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **Still open:** O8-O12 (company matching), O15-O18 (state sync and money), O22 (robots
  wildcards), and the U-list, each in the open-findings record.
