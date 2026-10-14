---
id: 2026-10-12-theme-intelligence-product-redesign
status: recorded
date: 2026-10-12
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — the three J.P. Morgan research defects corrected from stored evidence ($0), and the weekly page and Living Thesis Card redesigned for the analyst; awaiting the operator's review of the preview

**WHAT.**

**1. Three research defects, corrected from stored evidence — $0, no model call.**
- **The run:** `reassess --as-of 2026-10-12 --corrections <private file>` on the pilot registry,
  `R-20261012T133456Z-reassess`. It re-graded 4 theses and changed 2. QA passes 20/20. It was
  rehearsed first on two copies of the registry, with identical outcomes.
- **A1 — the bottom line** (`TH-FBDC863613` v2, line s01.0). The line said earnings had "beaten
  expectations for eight consecutive quarters". The source projects that the third quarter, if
  realised, would be the eighth consecutive quarter of double-digit growth.
  - The line is replaced by an **ANALYST CORRECTION**: operator-directed text citing three claims
    the thesis already links, all verified.
  - It keeps the conditional, so its label is derived as SOURCE OPINION, never a measured fact.
  - The unverified sector-count clause is dropped.
  - The reason is recorded on the line, in the version summary and as an `ANALYST_CORRECTION`
    issue.
- **A2 — the Magnificent 7 lagging the index.** This share-price line was filed as
  counter-evidence to EARNINGS broadening.
  - It is now **price context**: market context, never earnings evidence for or against the
    thesis.
  - The priority's counter-evidence count (F8) falls from 2 to 1. The action stays WATCH.
- **A3 — the number check.** A number inside a named index or a period label is part of a name:
  "S&P 500", "Russell 2000", "Magnificent 7", "Q3", "3Q26", "1H27".
  - The one line v1 withheld for "printing 500" is shown in v2.
  - Every other number on a line is still checked against its cited claims.
  - A figure written in words beside digits ("five of the 11") is now read as written.
  - Under that rule the sector-count claim (`C-8f2c9206bb9090`) would pass. Its stored record from
    the paid run keeps the failure, so figures '11' and '10%' stay **OPEN** in the research
    verification ("failed the number check"). They are not re-verified by editing a record.
- **Also in this run** (`TH-2FFD9B58A8` v2): two conditional risk lines ("could create a feedback
  loop…") were stored as MEASURED OBSERVATION. They are now stored as SOURCE OPINION, which is the
  previous round's rule persisted. The version summary now says so; before this change it read
  only "no change in action".

**2. The weekly page.**
- **First screen:** the title and the as-of date, then a summary: Research Now / Watch / Skip,
  review items, verification, articles read. The theses follow immediately as concise cards.
- **Each card shows:**
  - the mechanism in words;
  - what changed;
  - the effect on profits;
  - why Watch or Research Now, read from the stored factor values;
  - the next question;
  - the source and its dates;
  - a Review Required indicator linked to the affected lines.
- **Its own views:** this week's activity, the review queue, sources, the archive, and Operations
  & audit (run ids, engine codes, upload commands, the validation log).
- **One row per thesis, with every event of the week.** The pilot's TrendForce thesis reads
  "New · Downgraded: Research Now → Watch" on one row. The counts are counted from events.

**3. The Living Thesis Card.**
- **The header** carries the action, the horizon and the three dates. It also carries a Review
  Required indicator that links each finding to its exact line; repeated section names are
  numbered.
- **At a glance** answers seven questions, each linked to its full section:
  1. the thesis;
  2. what changed;
  3. the effect on profits, margins or demand;
  4. the strongest evidence, with units, periods and sources;
  5. why this action;
  6. what could invalidate it;
  7. the next check.
- The risks and the next check are open, not inside a collapsed section.
- **All nine sections follow, unchanged in content.** Claim ids, engine codes and the decision
  trace sit behind an "Audit view" switch. Print opens everything.

**4. Display defects fixed.**
- "page None" on web articles: new text says nothing, and stored text is cleaned on display.
- Double-escaped entities: HTML decodes once, and Markdown decodes well-formed references only.
- Page-wide overflow at 390 px.
- An id left in visible text: "automatic ()", the footer's run id and engine version, a version
  history's article id.
- `NOT_ASSESSED` now reads "Not assessed".

**WHY.** The operator's redesign brief: correct the three known J.P. Morgan findings from the saved
evidence without inventing facts or editing evidence, and make the product usable by an analyst.
The research comes first, technical detail stays reachable but out of the default view, and
nothing about the facts, history or research action changes.

**HOW VERIFIED.**
- **Before and after**, measured with headless Brave on the real pilot output.
  - Before: the original preview's pages, as the old renderer wrote them.
  - After: the same registry plus the corrections, rendered by the new code.
  - 390 px is measured inside a 390 px frame, because Brave's minimum window is 500 px.
  - Text inside a collapsed section counts as off-screen. The measure was corrected for this: its
    first version counted collapsed content as visible, so both sides were re-measured with the
    fix.

  | | before | after |
  |---|---|---|
  | first thesis from the top, desktop (1440) | 2,125 px | 357 px |
  | first thesis from the top, mobile (390) | 3,683 px | 609 px |
  | page width at 390 px | 422 (overflow) | 390 |
  | "page None", whole page (= print) | 18 | 0 |
  | double-escaped entities, whole page | 5 | 0 |
  | registry ids on screen, weekly page | 13 | 0 |
  | ids / engine codes on screen, per card | 1–3 / `NOT_ASSESSED` | 0 / none |

- **Integrity** on the four real WATCH theses:
  - all nine sections, in order;
  - every key-evidence row (4, 20, 6, 18) and every cited claim (4, 22, 9, 27) reachable in the
    HTML and in print;
  - print opens every section;
  - the action agrees across the card JSON, the card and the weekly page.
- **QA:** 22/22 on the preview run.
- **Tests:**
  - 16 new end-to-end tests (rendered artifacts) in `test_theme_intelligence_product_redesign.py`;
  - 4 tests of the old layout re-pinned on the same invariants — nothing truncated, counts state
    their population, no engine code in the analyst's view, no warning box when fully verified;
  - **31 of 31 mutants killed.**
- **Offline suite:** 5,056 passed, 512 skipped, 0 failed. ruff and `mypy --strict` are clean.

**BOUNDARY.**
- **"4 reassessed, 2 changed":** `R-20261012T133456Z-reassess`, every non-archived thesis in
  `data/theme_intelligence/v2/pilot-2026-10-12/` as of 2026-10-12.
- **The before/after figures:**
  - Before: `pilot-preview-2026-10-12`, run `R-20261012T122900Z-scan`.
  - After: `pilot-preview2-2026-10-12`, run `R-20261012T133511Z-scan`, a copy of the pilot
    registry taken after the corrections.
  - Pages: the weekly page and the four WATCH cards. Viewports: 1440×1000 and 390×844.
  - Measured 2026-10-12.
- **"First thesis":** the top of the first thesis card (`.thesis.row`; the old layout's `.row`)
  in document pixels.
- **"Whole page":** every rendered text node, including collapsed sections and the audit layer,
  which is what print shows.
- **Ids:** `TH-`/`C-`/`A-`/`AV-`/`R-2026…` patterns. **Codes:** `UPPER_SNAKE` tokens. Both are
  counted outside the audit layer and outside collapsed sections.
- **"31 mutants":** each guard of this round broken in turn against
  `test_theme_intelligence_product_redesign.py`, `…_scan.py` and `…_pilot_corrections.py`.
- **"4 of 188 figures open":** the preview week (11 runs, 5 articles), of which '11' and '10%' are
  the J.P. Morgan sector-count claim's.
- **The preview scan:** $0, no model call; 4 in-window articles queued, none analysed. It made 34
  HTTP requests, 15 of them served from the cache: 19 live requests to public listing pages for
  discovery and the health check, through the robots-respecting fetcher. `--cache-only` means
  "no model client", not "no network".

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** The pilot total stands at $4.3345 of $18. Nothing is merged, scheduled or published.
- **The J.P. Morgan bottom line is corrected by the operator, not by the pipeline.** The card
  review flagged that line for a different element and missed the paraphrase error, so a reviewer
  can pass a paraphrase that changes a claim's sense. Falsifier: the next paid run's review
  catches a planted paraphrase of this kind.
- **The sector-count figures stay open.** They close only when the article is applied again under
  today's rule.
- **One review finding now reads as history.** Its warning on Nomura's two relabelled lines still
  says "Labelled MEASURED OBSERVATION…", true of the version it was made on. It is carried
  verbatim, never reworded.
- **Two outputs were not redesigned:** the weekly Markdown (only entities fixed) and the JSON, which
  keeps stored values as stored.
- **On mobile the first thesis is at 609 px.** The ~500 px target is for desktop, where it is 357 px.
