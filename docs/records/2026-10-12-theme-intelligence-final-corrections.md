---
id: 2026-10-12-theme-intelligence-final-corrections
status: recorded
date: 2026-10-12
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — final evidence and UX acceptance corrections: every evidence link lands, source-named business groups apart from listed exposures, current findings told apart from history, a shorter overview and review queue

**WHAT.** Four corrections the operator demonstrated on the accepted redesign. Each was made at
render time from stored records, so no record was edited and no model was called ($0).

**1. Evidence navigation.**
- **The defect:** a line's citation linked to `#C-…`, but only the key-evidence rows carried ids.
  The four pilot cards held **27 broken link occurrences across 14 distinct targets** on screen,
  and the print views repeated them. The operator's count, reproduced exactly.
- **The fix:**
  - Every claim a card cites now has a row. Section 04 gains a collapsed **"Other evidence this
    card cites"** table: counter-evidence, context, and citations outside the key rows, each with
    its role on the thesis.
  - A cited id with no record is printed as text, never linked.
  - A link into a collapsed section opens it and scrolls to the target: on load (a link from the
    weekly page), on a hash change, and on a repeated click.
  - The new table scrolls inside its own container, so opening it never widens the page.

**2. Source-named business groups.** TrendForce names "GPU and ASIC manufacturers" (paragraph 8),
"GPU and ASIC vendors" (paragraphs 9 and 11) and memory "suppliers" (paragraph 6). It names no
company.
- **How groups are read:** verbatim, from paragraphs that hold the thesis's span-verified
  evidence. A group noun may be led only by acronym qualifiers ("GPU and ASIC", "HBM"), so an
  ordinary word or verb is never read as part of a name. A bare noun carries the words around it.
- **Where they appear:** section 05 lists them under their own heading, apart from listed-company
  exposures ("not companies; no ticker is implied and the research action does not count them").
  The "why Watch" line now says *"no listed company or verified sector exposure; the source names
  business groups only (…), not companies"* instead of "names no company or sector".
- **Nothing upgrades:** no ticker is looked up, and the stored priority (`F6 0 listed · 0 sector`)
  and the action are untouched.

**3. Current versus historical review status.** The old records stand as written; the readers now
tell history from what is still open.
- **J.P. Morgan's sector-count figures ('11', '10%'):** the claim quoting them failed the number
  check when the article was read. Today's check passes the stored claim ("five of the 11"), but
  the record keeps the failure, so the figures stay unused as evidence until the article is applied
  again.
  - They move from the open list to **"Resolved or historical"**, with that said in words.
  - The failing claim is found by STRUCTURE — same article version and paragraph, quoting the
    figure, number check failed — never parsed out of the ledger's sentence.
- **Nomura's two provenance-label findings:** these are review findings that questioned a
  conditional risk line's MEASURED OBSERVATION label. The re-grade relabelled both lines SOURCE
  OPINION.
  - On each line they now read "✓ Resolved — an earlier review (v1) questioned its MEASURED
    OBSERVATION label; this version labels it SOURCE OPINION", with the review's words one click
    away.
  - They are no longer counted: Review Required on the Nomura card goes from 5 lines to 3.
  - **The rule, deliberately narrow.** A finding is resolved only when all of these hold:
    - it is REVIEW_PARTIAL;
    - its words name the FACT label the line carried when it was made;
    - the same words now carry SOURCE OPINION.

    A finding about content, or one naming a label the line always carried, stays open.

**4. Readability.**
- **The weekly overview** says HOW each thesis works in the source's own words. That is the card's
  first source-stated transmission step that was not withheld or questioned, for example "AI
  infrastructure spending and technology investment drive continued sales strength across the
  index" instead of "Unit demand / volume growth or decline". The taxonomy category is shown,
  marked "Category:", only when no step is stated by the source.
- **"Effect on profits"** is the earnings chain in step names plus one sentence. The date
  explanation prints once.
- **The review queue** leads with the **current cards' findings**: one line per finding, shortened
  with "…", the whole finding on its card line. Three collapsed groups follow: incomplete sources;
  background alerts; resolved or historical.
- **The summary counts only current-card findings** (7, not 21). The verification stat counts the
  current open figures (2), with the 2 historical figures explained in the queue.
- **Also:**
  - a reviewer's shortened claim id ("C-1d67...") joins the audit layer;
  - the "earlier review" toggle no longer renders in heading capitals;
  - a landed table row is highlighted;
  - on a phone, evidence tables scroll sideways instead of squeezing to one word per line.

**WHY.** The operator accepted the redesign in principle and named four demonstrated issues, to be
resolved without redesigning again, without new research, sources, ingestion, scheduler, ledger
or portfolio features, and without deleting any evidence, risk, date or qualification.

**HOW VERIFIED** — on the real pilot output, before and after.
- **"Before"** is the reviewed preview regenerated exactly: the code at `4e70eeb0`, exported with
  `git archive`, rendering a copy of the same registry. It reproduces the operator's 27/14
  broken-link count.
- **Links:** 54 broken → **0** (cards and print views); 0 on the weekly page before and after.
- **Link landings in a real browser** (headless Brave):
  - 23 targets — the 14 previously broken plus every review link — at 1440 and 390 px: **46 of 46**
    found, their collapsed sections opened, on screen.
  - The audit switch takes the visible evidence links from 0 to at least 13.
- **Every section open, audit view off and on**, at 1440 and 390 px, on 9 pages (the weekly page,
  4 cards, 4 print views): **36 of 36** views fit, nothing past the screen edge outside a scroll
  container.
- **Integrity on the four WATCH theses:**
  - all nine sections, in order;
  - key-evidence rows 4 / 20 / 6 / 18, matching;
  - other-evidence rows 0 / 2 / 3 / 9, matching the JSON one for one;
  - every cited claim present in HTML and print;
  - print opens every section;
  - the action agrees across JSON, card and weekly page.
- **QA:** 22/22 on the preview run.
- **Measured views** (the weekly page and the 4 cards at 1440 and 390):
  - weekly page 5,328 → 4,304 px tall at 1440, and 11,912 → 8,392 at 390;
  - first thesis at 357 px on desktop, unchanged; 609 → 629 px at 390;
  - 0 ids, 0 engine codes, 0 "page None", 0 double escapes, no overflow.
- **Tests:** 17 new end-to-end tests in `test_theme_intelligence_final_corrections.py`, with
  positive and negative pins for each correction.
- **Mutants:** 26 of 26 of this round's mutants killed (one more was dropped as equivalent: it
  capped a resolved line's label, which is already SOURCE OPINION); the previous round's 31 of 31
  still killed.
- **Offline suite:** 5,075 passed, 512 skipped, 0 failed. ruff and `mypy --strict` are clean.

**BOUNDARY.**
- **Population:**
  - Before: the weekly report `R-20261012T133511Z-scan`, rendered at `4e70eeb0` from a copy of
    `data/theme_intelligence/v2/pilot-preview2-2026-10-12/`.
  - After: the same registry, rendered by this change.
  - Pages: the weekly page, the four WATCH cards and their print views. Measured 2026-10-12.
- **"27 / 14":** `a[href]` with an in-page `#` target missing from the page, counted on the four
  on-screen cards; the print views repeat the same 27.
- **"Business groups":** a group noun (suppliers, manufacturers, makers, vendors, producers,
  chipmakers, foundries, hyperscalers), optionally led by acronym qualifiers. Read only in
  paragraphs holding a span-verified claim linked to the thesis.
- **"Historical figure":** an open figure whose cause is `verification_failed` and whose failing
  claim(s) pass today's `_number_check` (`verify.number_passes`).
- **"Resolved finding":** the three conditions under 3.
- **"Current-card findings":** withheld or questioned lines of each thesis's current version, after
  resolved findings are removed.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** No model call; no stored record edited; the pilot registry unchanged by this round.
- **The resolved-finding rule reads the reviewer's words for the label's name.** If a future
  review words a label objection without naming the label, that finding stays open — the safe
  direction. A finding that objects to the label AND to content is resolved as a whole. Its full
  words stay on the line. Falsifier: a resolved finding whose words, read whole, raise a content
  point the relabel does not answer.
- **Business groups are read from evidence paragraphs only.** A group named in a paragraph holding
  no evidence of this thesis is not listed (TrendForce's page footer names "Makers" and
  "Suppliers" of other products; correctly excluded).
- **The weekly Markdown** still lists every review finding in full. It is not redesigned.
