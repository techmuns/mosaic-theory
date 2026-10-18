---
id: 2026-10-14-theme-intelligence-ms-batch-citi-links
status: recorded
date: 2026-10-14
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — five Morgan Stanley articles analysed, dates read from the page, Citi's "Read the full article here." followed, a supplied request leaves Uploads

**WHAT.**
- **Five Morgan Stanley September articles**, supplied by the operator as PDFs of the public pages,
  analysed into the pilot registry after a backup (`backups/registry-20261014T064905Z.db`). Each
  page's address came from morganstanley.com/what-we-do/research.

  | Article (page date) | Run | Cost | Result |
  |---|---|---|---|
  | Caffeine (2 Sep) | `R-20261014T064906Z-ingest` | $0.6755 | WATCH `TH-16225B12C4` (energy-drink demand) |
  | Biotech (14 Sep) | `R-20261014T065156Z-ingest` | $0.7662 | WATCH `TH-1D5A6AD90E` (AI "picks and shovels" in biotech); **RESEARCH NOW** `TH-BF20FBC464` (Alzheimer's, a $70bn drug market) |
  | Canada (15 Sep) | `R-20261014T065455Z-ingest` | $0.719 | WATCH `TH-41B1AB7F8C`; SKIP `TH-188B31F187` |
  | Healthcare industry trends (18 Sep) | `R-20261014T065757Z-ingest` | $1.0249 | WATCH `TH-2E2C6735DB`; SKIP `TH-7C43904AA3`; new evidence on `TH-1D5A6AD90E` and `TH-BF20FBC464` |
  | Healthcare consumerism (29 Sep) | `R-20261014T070200Z-ingest` | $0.5462 | new evidence on `TH-BF20FBC464` only — a link worth checking in Review |

- **A date the page prints is read wherever it sits** (`documents.py`). morganstanley.com's article
  pages, saved as PDF, lay the headline and date out in boxes the PDF reader detects as a table,
  and table text was never searched for the date. All six Morgan Stanley PDFs (13–14 Oct) went
  undated; the first one's date had to be stated by hand. Page 1–2 table text now joins the
  date search, in reading order. All five runs above read their date from the document.
- **Citi's "Read the full article here." is followed** (`parse._report_links`). The rule accepted a
  "here" link after "read the full article", but Citi's anchor text is "here." with the sentence's
  full stop. So the reader found no linked report on "Money: The Evolution to Digital", the page
  read as a 96-word teaser, and the operator was asked for a PDF the scan would otherwise
  download itself (`linked_reports = "fetch"`).
- **A teaser that links its full report is read through the link** (`health.py`), where the channel
  fetches linked reports. It is no longer counted as a teaser to supply; under `"request"` it
  still is.
- **A source's request leaves Uploads once every article it lists is supplied, held or read**
  (`desk.upload_items`). This answers "why is New research from Citi still pending if the PDF is
  already supplied?": the request came from Citi's 12 Oct health check and stayed until the next
  check, though its one listed article had been supplied and analysed. A held copy stays under
  Held documents. The manual-first channels' standing requests are unchanged.
- **Citi sourcing, checked.** The configured entry is `https://www.citigroup.com/global/insights/must-c`
  with `linked_reports = "fetch"`: the scan follows each article's download link and analyses the
  full PDF. Six earlier local runs (11 Oct) fetched "Must C - Sizing the ETF Opportunity" that way.
  The LatAm PDF the operator attached is byte-identical to one already stored in three earlier
  local registries, imported there as a manual upload. It is kept for reference and not analysed
  again: a 57-page report, the guide measures one such at $46.67.

**WHY.** The operator supplied the five articles for analysis and asked why Citi stayed pending.
The dry run showed the date miss, and the Citi page showed the link miss. Both cost the operator
manual work the system should do: typing a date, and supplying a PDF the scan can download.

**HOW VERIFIED.**
- **Real runs.** The five above, each SUCCEEDED, each dated from "the document text (page 1-2)".
- **Corpus before synthetic.**
  - Dates: the reader over every real document at hand. That is 296 files: the stored registry
    documents and other files in the local data directories, the operator's PDFs, and the
    fixtures. 7 changed, exactly the six Morgan Stanley PDFs (one twice, as its stored copy),
    from undated to their printed date. 289 unchanged.
  - Links: the page reader over the 62 distinct pages cached by the local registries'
    fetchers. 1 changed: Citi's "Money" page, which now finds its PDF. 61 unchanged; no new link
    found on any J.P. Morgan, TrendForce, SemiAnalysis, Nomura or Bank of America page.
- **Pins.**
  - A boxed date is read (new synthetic fixture `web_page_dated_in_a_box_synthetic.pdf`); an
    undated document stays undated (negative).
  - "Read the full article here." is a report link (new case in the link-rule table).
  - A linking teaser asks for nothing under `"fetch"` and still asks under `"request"`
    (negative).
  - A source's request leaves Uploads once every listed article is supplied; while one is still
    missing, it stays (negative).
  - Mutants: 4 of 4 killed.
- **The rendered desk from a copy of the updated registry:**
  - Uploads asks only for Morgan Stanley's and Goldman Sachs's standing requests;
  - 9 completed imports; 13 articles; 15 theses, 1 at Research Now;
  - 0 broken links and 0 default-view problems;
  - no horizontal overflow at 1440 and 390 px.
- Ruff and `mypy --strict` are clean; the offline suite result is in the PR.

**BOUNDARY.**
- **Pilot registry:** `data/theme_intelligence/v2/pilot-2026-10-12/registry.db` (the
  `theme-intelligence` worktree). Before these runs: 41 model calls, $7.8878. After: 69 calls,
  $11.6196, against the $18 pilot budget. Measured from its `llm_calls` on 2026-10-14. Each run
  was capped at $6 or what remained.
- **"296 files", "62 pages":** read 2026-10-14 from the `theme-intelligence` worktree's
  `data/theme_intelligence/v2/` (distinct files by name; distinct pages by content hash),
  `/Users/work/Downloads` copies and `tests/fixtures/theme_intelligence/synthetic_documents/`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $3.7318 of model spend.
- **Reported, not fixed:** the Morgan Stanley titles carry the browser tab's " | Morgan Stanley"
  suffix (the PDF's metadata title).
- **Open questions answered to the operator, not built:**
  - whether to add Goldman Sachs's Markets page as a second "where to look" for its manual-first
    channel;
  - whether to reinstate Bank of America, which is on the operator's original shortlist but was
    retired by decision on 2026-10-11.
