# Hybrid research ingestion — the real demonstrations (2026-10-11)

Every folder holds DERIVED readouts of one real run on the final code of PR #703 — the
dashboard (html / md / json / csv), the print report, the nine-section cards, the manifest
(model, prompt versions, cost, tokens), the validation log, the QA report (`qa.txt`), the command
log (`run-log.txt`, machine paths made repo-relative) and a registry summary (`registry.txt`:
articles and their versions, document records, theses, relations). **No original document, no
article full text and no database is here** — the reports read are public Citi Must C PDFs and
public publisher pages, kept in the git-ignored data directory and processed at the operator's
instruction (`--llm-permitted`).

| folder | what it shows | acceptance |
|---|---|---|
| `a-citi-gridlock-no-url/` | Citi's 60-page "Overcoming Gridlock 2.0" PDF imported with NO URL (`urn:document:sha256:…`), byline authors and its own date (published 2026-06-28, uploaded 2026-10-11), through the full pipeline into 17 nine-section cards (one RESEARCH NOW on dated PJM windows), against a registry already holding J.P. Morgan and SemiAnalysis power theses — which it CONTEXTUALISES (SIBLING / RELATED) and never merges into, because no claim is the same; then the same file under another name → DUPLICATE. Cost $46.67 (22 completeness parts) — the run that motivated the cost limit | 1, 2, 5, 6 (contextualise), 7 |
| `b-citi-etf-linked-report/` | Citi's ETF page — parsed to 0 words before the parser fix — read (965 words, PARTIAL: it summarises a report), and its linked 34-page report fetched from ir.citi.com (robots obeyed) as version 2 of the SAME article | Stage 4 (Citi) |
| `c-citi-latam-preview-then-upload/` | Citi's LatAm page analysed automatically as a PARTIAL preview with its linked report REQUESTED (Citi set to "request" for this registry, as Nomura is configured), then the 57-page PDF supplied with `ingest-file --url` → UPGRADED: one article, two versions, the preview's thesis re-versioned, 13 more from the full text | 4, 7 |
| `d-trendforce-html-pdf-one-article/` | TrendForce's 2026-09-30 release analysed from the web, then the same release as a saved HTML file (→ DUPLICATE: the same text) and printed to PDF (→ REVIEW: it holds 99% of the article plus 28% site furniture; the human answers `--duplicate-of`) — one article, nothing re-counted | 3, 5 |
| `e-local-to-actions-weekly/` | the ONE-registry workflow against a local bare git repository standing in for GitHub: the 2026-10-11 weekly registry pushed; the "laptop" pulls, imports an older article (TrendForce, published 2026-09-30, uploaded 2026-10-11 — first REVIEW on a 21% title overlap, which the fix since rules NEW), pushes (fast-forward); the "Actions" side restores the branch exactly as the workflow does (`import-state`) and runs a real scan — 8 channels health-checked, 2 healthy / 4 degraded / 2 blocked — whose ONE weekly report includes the upload (ranked, labelled a manual upload, its original "NOT on this machine"), QA 22/22 | 7, 8, 9, 13 |
| `f-cost-guard/` | the same Gridlock PDF in a fresh registry with the final code → HELD: "estimated $9–$50 … up to 23 completeness parts for 851 stated figures and 292 argument paragraphs — above the per-document limit $30; nothing was sent to the model" (the log also shows the `--cache-only` traceback that was then fixed: a failed analysis is now recorded FAILED, plainly) | cost control |
| `stage1-memory-semianalysis-trendforce/`, `stage1-power-semianalysis-jpm/` | the real two-publisher cases re-run on the final code (cached model output, $0): no contradiction is recorded where the claims differ in product, mechanism, segment or period | 10 |

What is NOT shown with real documents, and why: a Morgan Stanley / Goldman Sachs / SemiAnalysis
paid report (licensed — not held; the scenarios run on clearly labelled SYNTHETIC fixtures in
`tests/fixtures/theme_intelligence/synthetic_documents/`), and GitHub itself (the state branch does
not exist yet; the sync is shown against a local bare repository).

**Long-report folders (a, b, c) keep ONE representative card** (html + md) and no print report:
each card carries dozens of verbatim quotes, and all of them together would be a substantial
share of a report's text — the full set stays in the git-ignored run folder. Their dashboards
link to the cards that are not here.

`parser-corpus-check.txt`: every cached HTML page (58) parsed by the parser before this round
and by the final one — which pages changed and how (Citi's ETF page 0 → 965 words; the pages
that say they summarise a linked report become PARTIAL with the link recorded; BofA pages gain
their last-modified date). `screenshots/`: the weekly dashboard's health and intake blocks, the
ranked rows with how their evidence arrived, and the RESEARCH NOW card the Citi PDF produced.
