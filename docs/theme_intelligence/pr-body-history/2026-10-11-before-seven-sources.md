## Summary

A new, isolated package **`vinci/theme_intelligence/`**: a research discovery and prioritisation tool. It reads research from eight publisher channels, and now from documents the operator supplies; extracts source-anchored evidence, named companies and risks; keeps a persistent, versioned registry of theses; and writes a decision-first weekly dashboard of nine-section **Living Thesis Cards**.

**"RESEARCH NOW" means allocate analyst attention — never buy.** The package stays off the fund's decision path (unchanged by this update): no fund module imports it; it imports only `vinci.config`, the existing LLM client and the HTTP cache (AST-pinned); it has its own SQLite registry; it has no buy / sell / target / weight field; its priority rules read no prices, returns or outcomes.

**This update completes the hybrid research ingestion brief** — see the next section. Earlier updates (source health, review rounds 2 and 3, the original build) are condensed at the end; their full write-ups are in the records and in `docs/theme_intelligence/pr-body-history/2026-10-11-before-hybrid-ingestion.md`.

- **Code:** all inside `vinci/theme_intelligence/`, plus one new dependency, `pdfplumber>=0.11,<0.12`, in `pyproject.toml`.
- **Changed outside the package:** `STATE.md` (§2 line, §5.0 row 32 item 8), `docs/engineering.md` (glossary), `docs/theme_intelligence.md` (guide), `docs/records/2026-10-11-theme-intelligence-hybrid-ingestion.md`, tests, fixtures, worked output.
- **Untouched:** fund screen / ranker / dossier / verdict / scoring / valuation / ledger / portfolio / trading / historical-alpha-audit code.

Guide: `docs/theme_intelligence.md` · Record: `docs/records/2026-10-11-theme-intelligence-hybrid-ingestion.md` · Worked output: `docs/theme_intelligence/hybrid-ingestion-2026-10-11/`

---

## Hybrid research ingestion (this update)

### What was built

**Stage 1 — claim-level contradiction** (`contradiction.py`). Two theses contradict only when a pair of their claims measures the same product, variable, overlapping period and place, and points opposite ways.
- A `[[product]]` taxonomy (HBM, conventional DRAM, NAND, SSD …) makes HBM up beside conventional DRAM down COMPATIBLE. Genuine opposing forecasts for the same DRAM series and quarter CONTRADICT.
- Only the directly contradicting claims are filed against the incumbent.
- A generic term against one of its parts ("DRAM" vs "HBM"), a negation or an unclear pairing → CONTRADICTION_REVIEW: listed, never applied.
- Counter-evidence is weighed by independent ORIGINS, never by claim count; a restated observation is compared once.

**Stage 2 — supplied documents** (`documents.py`, `ingest.py`).
```bash
python -m vinci.theme_intelligence ingest-file --path "/secure/research/report.pdf" --source ms_research --llm-permitted
python -m vinci.theme_intelligence ingest-inbox        # data/theme_intelligence/inbox/ → processed/ held/ review/ rejected/
python -m vinci.theme_intelligence documents --status HELD
```
- PDF (pdfplumber), HTML, Markdown and text. DOCX is refused with a plain message: no compatible library is installed.
- Kept: a page reference on every block; each table as one block with values as printed; footnotes; headings; title, authors (metadata / front matter / byline) and the document's own date, each with where it was read.
- Flagged, never dropped: scanned pages (a document with one is PARTIAL — no OCR), chart pages (plotted values not read), unreadable pages.
- The publication date is NEVER taken from the upload time, the file name or the PDF's CreationDate / ModDate. An operator-stated date fills only a gap; a disagreement is listed for review.
- No public URL → `urn:document:sha256:…`.

**Stage 3 — one registry, one pipeline.** Identity is decided before any model call:
- the same FILE, or the same TEXT in another format → DUPLICATE, nothing re-counted;
- a fuller document of a PARTIAL article → **UPGRADED**: a new version of the SAME article, re-extracted, the earlier version kept, restated claims REPEATED (never independent confirmations);
- anything uncertain → **REVIEW**, answered with `--same-as` (a fuller version), `--duplicate-of` (the same: add nothing) or `--as-new`.

The match can come from a stated `--url`, from the document's own canonical link, or from the same publisher's title, date and text.
- **Same-article continuity:** a later version that names more segments updates the thesis its earlier version created — never a twin.
- **Licence gate:** the text reaches the model only when the operator states its licence allows it, or the channel's `manual_llm_processing = "permitted"`; otherwise it is HELD.
- **Route-independence (pinned):** the route in never changes research priority — the same report as a fetched page and as an upload gives the same thesis, action and rules.

**Stage 4 — publisher fixes.**
- **Citi:** the article body sits in `div.template-apply-sidebar`, and the noise filter dropped the whole ETF page (0 words). A noise-named element holding most of the page's paragraph text is now kept (parser `ti-parse-5`). Each Must C page's public report ("Download Here", ir.citi.com) is read through the robots-obeying fetcher as a fuller version of the same article (`linked_reports = "fetch"`, at most 2 per run).
- **Nomura:** "To read the full report, click here" leads to the client portal — requested, never fetched.
- **BofA:** an undated page is bounded by its last-modified date. Modified before the window → out of it, said so. The rest are listed for date verification, and `article --url U --published <verified date>` records the date as operator-verified.
- **SemiAnalysis:** RSS discovery and PARTIAL previews unchanged; an authorised full PDF UPGRADES the preview.
- **J.P. Morgan and TrendForce:** adapters pinned on trimmed copies of their real listings.
- **Morgan Stanley / Goldman Sachs:** health checks continue; manual import is the route (see *Dependencies*).

**Stage 5 — local uploads and the scheduled run share ONE registry** (`state.py`).
```bash
python -m vinci.theme_intelligence state pull --remote <the repo's git URL>   # rebuild from the state branch; replay local documents it lacks
python -m vinci.theme_intelligence ingest-file --path report.pdf --source gs_research --llm-permitted
python -m vinci.theme_intelligence state push                                 # fast-forward only; derived JSONL only
```
- `push` refuses a tree holding any PDF, page, database or article text, and refuses if the branch moved since your pull.
- `pull` backs up first and never silently discards a local run it cannot replay.
- The next scheduled scan's report includes the uploads. On the runner the originals are absent and every surface says so; QA counts such claims "not re-checkable here", never re-verified.

**Stage 6 — the weekly dashboard.**
- A scan's report takes in the manual runs since the previous scan — ONE ranked list.
- Every row says how its evidence arrived (automatic / manual upload / linked report).
- A **Research intake / manual action** section: automatic and manual intake; partial articles awaiting documents; blocked or degraded publishers; articles needing an upload; metadata or licence checks needed; coverage gaps. Each list states its population.
- Three dates are kept apart: an article published last month and uploaded today reads *Published* last month.

**Stage 7 — privacy, licensing, cost.**
- Originals are stored owner-only in the git-ignored data directory, and the export blanks article text.
- A test fails if any PDF / DOCX other than the labelled synthetic fixtures is ever tracked.
- Unverified claims never reach a thesis (QA).
- Source health, ingestion coverage and research verification are separate statuses.
- **Cost limit** (forced by a real run, below): every document is estimated before any model call and HELD above $30 until `--max-cost`, including a linked report a scan would fetch.

### Real demonstrations — final code, real documents

Outputs: `docs/theme_intelligence/hybrid-ingestion-2026-10-11/`. The public Citi PDFs and TrendForce pages were processed at the operator's instruction (`--llm-permitted`). No original is committed, and the long-report folders keep one card each.

| acceptance | run | result | cost |
|---|---|---|---|
| 1, 2, 7 | Citi "Overcoming Gridlock 2.0", 60-page PDF, **no URL** | `urn:` identity, eight byline authors, published **2026-06-28** from its own text, uploaded 2026-10-11 → **17 nine-section cards**, one RESEARCH NOW (a market-regime record on dated PJM windows); QA 18/20 — 17 of 851 figures and 4 of 292 paragraphs open, causes listed, none used as evidence | $46.67 |
| 5 | the same PDF renamed | DUPLICATE, same document id, nothing re-counted | $0 |
| 6 | the same run, against a registry already holding J.P. Morgan + SemiAnalysis power theses | **contextualised** (SIBLING / RELATED), never merged or weakened — no claim is the same under the claim-level rules | — |
| 4 | Citi LatAm page analysed automatically as a PARTIAL preview with its report REQUESTED (Citi set to "request" for this registry, as Nomura is), then the 57-page PDF via `ingest-file --url` | **UPGRADED**: one article, two versions (570 → 24,960 words), the page's date kept and the PDF's 2026-09-10 recorded beside it, the preview's thesis re-versioned, 13 more theses | $0.41 + $9.47 |
| Stage 4 Citi | Citi ETF page (0 words before the fix) | 965 words, PARTIAL; its 34-page report fetched from ir.citi.com as version 2 of the same article; replayed in a fresh registry for $0 | $3.80 |
| 3 | TrendForce 2026-09-30: web, then a saved HTML file, then a printed PDF | HTML → **DUPLICATE** (same text); printed PDF → **REVIEW** (99% of the article inside it, 72% of it the article — site furniture), answered `--duplicate-of` → **one article** | $0 |
| 9, 13, 7, 8 | local bare git repository standing in for GitHub: the 2026-10-11 weekly registry pushed → a "laptop" pulls, imports the saved TrendForce release (published 2026-09-30), pushes (fast-forward) → the "Actions" side restores with `import-state` as the workflow does and runs a **real scan** (8 channels checked: 2 healthy, 4 degraded, 2 blocked) | the ONE weekly report ranks the upload — "Published 2026-09-30 · first ingested 2026-10-11 10:38 UTC", "manual upload", original "NOT on this machine"; QA 22/22 | $0.69 |
| 10 | the real two-publisher cases (SemiAnalysis + TrendForce memory; SemiAnalysis + J.P. Morgan power), final code | no contradiction recorded; QA 20/20 each | $0 (cache) |
| cost | the Gridlock PDF in a fresh registry | **HELD**: "estimated $9–$50 … up to 23 completeness parts for 851 stated figures and 292 argument paragraphs — above the per-document limit $30; nothing was sent to the model" | $0 |

**Model spend this update: $61.04** at list price (`claude-opus-4-8`, from the run manifests). Every replay was $0.

### Screenshots

The weekly dashboard's source-health and research-intake blocks (combined report, restored registry):

![intake](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/hybrid-ingestion-2026-10-11/screenshots/weekly-intake-block.png?raw=true)

Ranked rows saying how their evidence arrived:

![rows](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/hybrid-ingestion-2026-10-11/screenshots/weekly-ranked-rows-with-intake.png?raw=true)

The RESEARCH NOW card from the Citi PDF imported with no URL:

![card](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/hybrid-ingestion-2026-10-11/screenshots/citi-gridlock-pdf-card-research-now.png?raw=true)

### Found by the real runs — fixed, pinned, mutation-checked

1. **Cost.** The Gridlock report cost $46.67 — 22 completeness parts, each re-sending the whole text, $39.44 — against $9.47 (LatAm) and $3.80 (ETF). Cost follows figure density. The automatic Citi fetch could have spent this unattended → the estimate and the $30 limit above.
2. **Printed web pages.** A printed page would have UPGRADED a complete article with its site furniture → a longer copy of a COMPLETE article now goes to REVIEW.
3. **Title overlap.** Two different TrendForce releases sharing 21% of title words (0% text) went to REVIEW → a title alone needs 50%.
4. **Pulled registry.** A pulled registry compared text it does not hold as 0%, silently → the basis now says the text isn't on this machine.
5. **Canonical links.** A saved page's canonical link was ignored → it is now identity.
6. **False provenance.** An automatic linked fetch was recorded as "the operator states …" → recorded as the report the page links to.
7. **Wrong counts.** One article read in two versions was reported as "2 articles … 1 read only as a preview" → "1 article(s), 2 version(s)", and not preview-only.
8. **Citi health.** Citi read DEGRADED ("report not read", upload required) though its scan reads the reports → not degraded under a "fetch" policy.
9. **Stale review rows.** 12 BofA pages stayed UNDATED on the review list after the scan had ruled them out of the window → the row is updated.
10. **Verification scope.** The week's verification said "this run" while covering three runs → it names its scope.
11. **Failed analyses.** One crashed with a traceback and left its run RUNNING, and the next import of the same document was called a DUPLICATE of an analysis that never finished → FAILED, plainly; then RETRIED.
12. **Over-broad report links.** The parser corpus check (58 cached pages) caught "a PDF link means a fuller report" before it shipped. It marked every J.P. Morgan page partial (a Form CRS footer) and BofA pages (a print copy) → the page must say so.

### Where it runs

| where | what |
|---|---|
| this machine | `ingest-file`, `ingest-inbox`, `documents`, `state pull/push/status`, `article`, `scan`, `report`, `qa` |
| GitHub Actions | the weekly scan, unchanged (restore → gate → scan → QA → export → commit); manual documents arrive only through `state push` |
| needs configuration | the `theme-intelligence-state` branch does not exist on GitHub yet (the first workflow run after merge, or the first `state push`, creates it); the cron needs `THEME_INTELLIGENCE_SCHEDULE_ENABLED=true`; `state push` needs the operator's git credentials; secure cloud document storage is NOT configured — originals stay on the operator's machine |

**Not claimed:** automatic local-to-GitHub synchronisation. It ran against a local bare repository only.

### Dependencies and access restrictions — open

- **Morgan Stanley:** the connection is dropped on every request, robots.txt included → BLOCKED, fail closed.
- **Goldman Sachs:** HTTP 403 → BLOCKED.
- Their research reaches clients through entitled portals and licensed distribution. I did **not** probe or configure any such access; the dependable route is an entitled operator's `ingest-file`.
- **Nomura:** full reports are on the client portal — upload only.
- **SemiAnalysis:** paid posts are previews — upload only.
- **Licences:** confirm each publisher's third-party-LLM terms before `--llm-permitted`. The default is HELD.
- **Cost:** a figure-dense report costs $10–$50; above $30 it waits for `--max-cost`.
- **No OCR**, and chart values are not read.
- **On a pulled registry, text-based identity is unavailable:** a supplied copy of an article the scheduled run fetched is matched by URL, title and date, or goes to REVIEW.

### Tests, mutants, gate

- New test files: `test_theme_intelligence_ingestion.py` (34), `_publishers.py` (13), `_state_sync.py` (8); additions to `_evidence_roles`, `_overlap`, `_source_health`, `_scan`.
- Synthetic fixtures (`tests/fixtures/theme_intelligence/synthetic_documents/`): invented and bannered, standing in for licensed documents — never presented as research by any publisher.
- **Mutation checks: 56 of 56 guard mutants killed**:
  - claim-level contradiction: 10;
  - ingestion / publishers / report / state: 29;
  - the real-run fixes: 10;
  - the cost limit: 6;
  - the retry: 1.
- `ruff check vinci tests frontend` clean; `mypy --strict vinci` clean (181 files).
- `pytest -m "not network"`: **4,759 passed**, 508 skipped, 37 deselected, 0 failed.

### Completion — the brief, item by item

| item | disposition | note |
|---|---|---|
| Stage 1 — claim-level compatibility (product, scope, variable, geography, period, outcome); HBM vs DRAM; genuine DRAM contradiction; attach only direct claims; never by claim count; dedup by evidence and origin; ambiguous → review; regression + mutation tests | SHIPPED | real two-publisher cases: no contradiction |
| Stage 2 — PDF, HTML, Markdown, text | SHIPPED | |
| Stage 2 — DOCX | SKIPPED | no compatible library installed; refused with a plain message |
| Stage 2 — CLI, no-URL reports, inbox, preserve metadata / pages / tables / values / footnotes, flag scanned / charts, no dates from uploads or filenames | SHIPPED | no OCR — scanned pages flagged |
| Stage 3 — same pipeline; Cases A–C | SHIPPED | A on synthetic (SemiAnalysis) and real (Citi LatAm) |
| Stage 3 — Case D: a manual report strengthens / challenges / contextualises another publisher's thesis | SHIPPED | strengthen pinned (synthetic); real: contextualise |
| Stage 4 — Citi parser + full content | SHIPPED | |
| Stage 4 — BofA dates | SHIPPED | |
| Stage 4 — Nomura | SHIPPED | portal reports requested, never fetched |
| Stage 4 — SemiAnalysis | SHIPPED | |
| Stage 4 — JPM / TrendForce regression | SHIPPED | |
| Stage 4 — MS / GS legitimate access | PARTIAL | health checks continue; manual import works; licensed / official access NOT investigated beyond documenting it |
| Stage 5 — one logical registry; manual article in the next weekly report; no laptop access needed by Actions; nothing licensed committed; provenance kept; absent originals never "reverified" | SHIPPED | shown against a local bare repository |
| Stage 5 — GitHub sync | STOPPED | not demonstrated — the state branch does not exist yet; not claimed |
| Stage 6 — intake section; one ranked list; three dates | SHIPPED | |
| Stage 7 — private storage; licence gate; unverified never strengthens; separate statuses | SHIPPED | plus the cost limit |
| Acceptance 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12 | SHIPPED | table above |
| Acceptance 6 — a manual report UPDATING an existing multi-publisher thesis | PARTIAL | real: contextualised, not updated (no real report in hand states the same claim); update path pinned on synthetic documents |
| Acceptance 13 — persistence documented and verified as configured | PARTIAL | local verified; GitHub not exercised |
| Ruff, mypy, full offline suite, mutation checks | SHIPPED | above |
| CI | see the PR checks | |
| Do not merge; no automatic CI fixes | STOPPED here | awaiting review |

---

## Earlier updates (condensed; full text: `docs/theme_intelligence/pr-body-history/2026-10-11-before-hybrid-ingestion.md`)

- **Priority 1A — source health** (`docs/records/2026-10-11-theme-intelligence-source-health.md`). Every channel is checked cheaply and LLM-free — `sources --check-health` and at the start of every scan.
  - Seven tests; one status per channel (HEALTHY / DEGRADED / BLOCKED / ERROR / UNKNOWN), with freshness kept apart.
  - History in an append-only table; change alerts, with a hook for delivery.
  - Live, 2026-10-11: 2/8 healthy, 4 degraded, 2 blocked.
  - 24 of 24 mutants killed.
- **Review round 3** (`docs/records/2026-10-11-theme-intelligence-review-round-3.md`).
  - A challenge needs the same claim, and the segment is part of identity — round 2's merge and challenge are reversed.
  - A narrow near-term-inflection route to RESEARCH NOW.
  - Research verification is shown apart from execution; three dates on every card.
  - 27 of 27 mutants killed.
- **Review round 2** (`docs/records/2026-10-10-theme-intelligence-review-corrections.md`).
  - J.P. Morgan's Software Shock yields exactly three WATCH theses.
  - Alphabet is resolved point-in-time.
  - The calm-index article: all 19 figures accounted for.
- **The original build** (`docs/records/2026-10-10-theme-intelligence.md`): the package, its registry, the nine-section cards, the weekly workflow (opt-in cron, state branch).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

