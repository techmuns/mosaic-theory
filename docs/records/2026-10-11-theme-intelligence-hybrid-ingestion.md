---
id:
status: shipped
date: 2026-10-11
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence hybrid ingestion — claim-level contradiction, supplied documents through the same pipeline, publisher fixes, one registry and one weekly report, a cost limit

**WHAT.** In `vinci/theme_intelligence/` (research attention only, off the decision path), the
"complete the hybrid research ingestion system" brief on PR #703:

- **Claim-level contradiction** (`contradiction.py`). Two theses contradict only when a pair of
  their claims measures the same product (`[[product]]` taxonomy: HBM, conventional DRAM, NAND,
  SSD …; a generic term like "DRAM" covers its parts and is AMBIGUOUS against one of them), the
  same variable, an overlapping period and place, and points opposite ways. Only the directly
  contradicting claims are filed against the incumbent; an unclear pairing is
  CONTRADICTION_REVIEW (never applied); counter-evidence is weighed by independent ORIGINS,
  never by claim count, and a restated observation is compared once.
- **Supplied documents** (`documents.py`, `ingest.py`, CLI `ingest-file` / `ingest-inbox` /
  `documents`, store migration v4). PDF (pdfplumber, now a dependency), HTML, Markdown, text;
  DOCX refused plainly. Page references, tables as one block with values as printed, footnotes,
  headings, bylines; scanned pages and chart values FLAGGED, a scanned page makes the document
  PARTIAL. The date comes from the document's own text, never the upload time, file name or PDF
  file metadata. Identity before any model call: same file → DUPLICATE; same text →
  DUPLICATE; a fuller document of a PARTIAL article (stated URL, the document's own canonical
  link, or the same publisher's title / date / text) → UPGRADED, a new version of the SAME
  article; anything uncertain → REVIEW, answered by `--same-as` / `--duplicate-of` / `--as-new`.
  No public URL → `urn:document:sha256:…`. Licence gate: the text reaches the model only when
  the operator states its licence allows it (`--llm-permitted`) or the channel's
  `manual_llm_processing = "permitted"`; otherwise HELD. Originals are copied owner-only into the
  git-ignored data directory. Same-article continuity: a later version naming more segments
  updates the thesis its earlier version created, never a twin.
- **Publisher fixes.** Citi: the article body sits in `div.template-apply-sidebar`; the parser's
  noise filter dropped all of the ETF page (0 words) — a noise-named element holding most of the
  page's paragraph text is now kept (parser `ti-parse-5`). Linked reports: a page that SAYS it
  summarises a report it links to ("Download Here", "to read the full report, click here")
  records the link and reads PARTIAL; per channel `linked_reports = fetch | request` — Citi fetches
  its public ir.citi.com PDFs (robots obeyed) as a fuller version of the same article, Nomura's
  client-portal reports are requested, never fetched. BofA: an undated page is bounded by its
  last-modified date (before the window → out of it, said so); the rest are listed for date
  verification and `article --published` takes an operator-verified date. J.P. Morgan and
  TrendForce adapters pinned on trimmed copies of their real listings.
- **One registry, one weekly report** (`state.py`, `report.py`). `state pull` rebuilds the local
  registry from the state branch and replays local documents the branch lacks; `state push` is
  fast-forward only and pushes derived JSONL only (no PDF, page, database or article text —
  checked before commit). A scan's dashboard takes in the manual runs since the previous scan;
  every row says how its evidence arrived; a Research Intake / Manual Action section lists
  automatic and manual intake, partial articles awaiting documents, blocked / degraded publishers,
  uploads and metadata / licence checks needed, and coverage gaps. QA on an imported registry
  counts a claim whose text is not held as "not re-checkable here", never re-verified.
- **Cost limit.** Each document is estimated before any model call from the completeness pass's
  work — parts = ceil((stated figures + argument paragraphs) / 50), $0.4–$2.1 per part + $2 —
  and HELD above `DOC_COST_LIMIT_USD` ($30) until `--max-cost` raises it; the same limit stops a
  scan from spending on a linked report unattended.

**WHY.** The brief: research must stay useful when publishers refuse automated agents; an
operator's report must enter the SAME registry, rules and weekly list as a fetched article, the
route never changing priority; broad taxonomy labels must never weaken a thesis.

**HOW VERIFIED.** Real runs on the final code, outputs in
`docs/theme_intelligence/hybrid-ingestion-2026-10-11/`, plus tests and mutants:

- *Citi "Overcoming Gridlock 2.0"* (public 60-page PDF, no URL): urn identity, eight byline
  authors, published 2026-06-28 from the text, uploaded 2026-10-11 → 17 nine-section cards, one
  RESEARCH NOW (a market-regime record on dated PJM windows); against a registry holding J.P.
  Morgan + SemiAnalysis power theses it CONTEXTUALISES (SIBLING / RELATED), never merges — no
  claim is the same; QA 18/20 (17 of 851 figures and 4 of 292 paragraphs open, causes listed).
  The same file renamed → DUPLICATE, nothing re-counted. Cost $46.67.
- *Citi ETF page*: 0 → 965 words; its 34-page report fetched from ir.citi.com as version 2 of
  the same article (one article, one thesis); $3.80; replayed in a fresh registry for $0.
- *Citi LatAm*: the page analysed as a PARTIAL preview with its report REQUESTED (Citi set to
  "request" for that registry, as Nomura is), then the 57-page PDF supplied with `--url` →
  UPGRADED, one article, two versions, the preview's thesis re-versioned, 13 more theses; $9.88.
- *TrendForce 2026-09-30*: web article, then a saved HTML copy → DUPLICATE (same text), then a
  printed PDF → REVIEW (99% of the article inside it, 72% of it the article — site furniture),
  answered `--duplicate-of` → one article.
- *State sync*: a local bare repository stands in for GitHub. The 2026-10-11 weekly registry
  pushed; a "laptop" pulled, imported the saved TrendForce release, pushed (fast-forward); the
  "Actions" side restored the branch with `import-state` as the workflow does and ran a REAL scan
  (8 channels health-checked: 2 healthy, 4 degraded, 2 blocked) whose ONE weekly report ranks the
  upload, labelled a manual upload with its original "NOT on this machine"; QA 22/22.
- *Claim-level contradiction on the real two-publisher cases* (SemiAnalysis + TrendForce memory;
  SemiAnalysis + J.P. Morgan power), re-run on the final code from cached model output ($0): no
  contradiction recorded; QA 20/20 each.
- *Cost limit*: the Gridlock PDF in a fresh registry → HELD, "estimated $9–$50 … up to 23
  completeness parts … above the per-document limit $30; nothing was sent to the model".
- *Parser corpus check*: all 58 cached HTML pages, parser before vs after — only the pages the
  changes target changed (`parser-corpus-check.txt`). The check caught a rule before it shipped:
  "a PDF link is a fuller report" marked every J.P. Morgan page partial (a Form CRS footer) and
  BofA pages (a print copy); the rule now needs the page's own words.
- *Found by the real runs and fixed in this build*: a printed web page would have UPGRADED a
  complete article with its site furniture; a 21% title overlap sent a new TrendForce release to
  REVIEW; a pulled registry compared text it does not hold as 0%, silently; an automatic fetch
  was recorded as "the operator states"; one article read in two versions was reported as "2
  articles … 1 read only as a preview"; Citi read DEGRADED for reports its scan reads; stale
  UNDATED rows stayed on the review list; a week's verification said "this run"; a failed
  analysis left its run RUNNING and the next import called it a DUPLICATE of an analysis that
  never finished; and the $46.67 report that motivated the cost limit.
- Tests: 326 theme-intelligence tests pass (2 skipped); new files `test_theme_intelligence_
  ingestion.py`, `_publishers.py`, `_state_sync.py`. Synthetic fixtures (invented, bannered) stand
  in for licensed documents. Mutation checks: 56 of 56 guard mutants killed (claim-level
  contradiction 10, ingestion / publishers / report / state 29, the real-run fixes 10, the cost
  limit 6, the retry 1).

**BOUNDARY.** Real runs 2026-10-11 between 10:06 and 11:03 UTC on branch `claude/theme-intelligence`
(final code `ea3c6a20` plus this record's commit); as-of 2026-10-11 except the cached replays
(their articles' own dates). Costs are list price for `claude-opus-4-8`, per run, from the run
manifests: $46.67 + $3.80 + $0.41 + $9.47 + $0.69 = $61.04 this round; every re-run $0 from the
content-addressed cache. "58 cached HTML pages" = every text/html entry in
`data/theme_intelligence/v2/shared_http_cache` on 2026-10-11. Health counts are over the eight
configured channels at the scan's start (11:02 UTC). Test counts: `pytest -k theme_intelligence`,
offline. The cost constants are calibrated on THREE reports — a small sample, stated as such.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *Cost.* A figure-dense research PDF is expensive through the full pipeline ($46.67 for one 60-page
  report); the limit holds such a document until the operator decides. Falsifier: a document whose
  measured cost exceeds its estimated high end — the calibration test is the place to widen it.
- *GitHub sync is not demonstrated*: the `theme-intelligence-state` branch does not exist on
  GitHub; the round trip ran against a local bare repository. The first workflow run (after
  merge) or the first `state push` creates it.
- *On a pulled registry, text-based identity is unavailable* (the export blanks article text):
  a supplied copy of an article the scheduled run fetched is matched by URL, title and date, or
  goes to REVIEW.
- *Licensed reports* (Morgan Stanley, Goldman Sachs, SemiAnalysis paid) were not available; their
  scenarios ran on synthetic fixtures only — never presented as research by those publishers.
- *Acceptance 6 on real data is "contextualise", not "update"*: under the claim-level identity
  rules no real report in hand states the same claim as an existing multi-publisher thesis; the
  update path is pinned on synthetic documents (Case D).
- No OCR (a scanned page is flagged, its text unread); chart values are not read.
