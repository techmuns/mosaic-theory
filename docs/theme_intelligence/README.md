# Theme intelligence — worked output (2026-10-10)

Derived readouts of the runs that verify the build: dashboards, nine-section cards (web, print,
Markdown, JSON), run manifests and validation logs. No database, no article full text — card
evidence quotes are the short verbatim spans that anchor each claim. Operator guide:
[`../theme_intelligence.md`](../theme_intelligence.md).

| folder | run | what it shows |
|---|---|---|
| [`acceptance-jpm-2026-02-09/`](acceptance-jpm-2026-02-09/) | `R-20261010T121233Z-article` | the J.P. Morgan acceptance article, replayed AS OF 2026-02-09 into a fresh registry: exactly three theses — AI infrastructure **RESEARCH NOW**, software recovery **WATCH**, AI-adoption margins **WATCH** |
| [`a-to-b-hypothetical-2026-02-20/`](a-to-b-hypothetical-2026-02-20/) | `R-20261010T122404Z-article` | a clearly labelled HYPOTHETICAL article B applied to the PRESERVED registry (exported to JSONL and re-imported, the scheduler's durable path): same thesis id, version 2, evidence STRONGER, RESEARCH NOW kept |
| [`weekly-run-2026-10-10/`](weekly-run-2026-10-10/) | `R-20261010T120521Z-scan` | `bin/theme-intelligence-weekly` run for real: all eight channels, 2026-10-01 → 10, drained the three articles the previous scan had QUEUED, QA 13/13 |
| [`first-scan-2026-10-10/`](first-scan-2026-10-10/) | `R-20261010T114919Z-scan` | the first live capped scan (`--max-articles 3`): three analysed, three QUEUED with the cap printed |

Screenshots (`screenshots/`): `jpm-dashboard.png`, `jpm-card-research-now-web.png` (01/02/06/08
open, the rest on demand), `jpm-card-research-now-print.png` (every section and audit toggle open),
`a-to-b-dashboard.png`, `weekly-scan-dashboard.png`.

## Boundaries of every number above

- **Acceptance:** one article (`A-332d3da6f3ac`, published 2026-02-09 10:30 +05:30, retrieved FULL
  2026-10-09, 42 parsed blocks / 1,146 body words); as-of 2026-02-09; extraction prompt
  `ti-extract-5`, review prompt `ti-review-3`, model `claude-opus-4-8`; 22 claims extracted, 22
  span-verified; 15 named entities, of which META, AMZN, GOOGL (with GOOG/GOOGM/GOOGN — the SEC map
  lists four tickers for Alphabet and does not state their type) and MSFT are the source-named
  listed exposures of the RESEARCH NOW thesis.
- **Weekly run / first scan:** window 2026-10-01 → 2026-10-10 (10 days ending the run date),
  as-of 2026-10-10, all eight configured channels; "discovered" counts unique canonical URLs a
  channel's listing / feed / page data exposed on that day; "in window" counts those whose
  SOURCE-STATED date falls in the window; undated candidates are counted and never placed.
- **Cost:** list price for `claude-opus-4-8` ($5 / $25 per million input / output tokens); a
  cache hit costs 0 and its tokens are reported separately as `replayed_from_cache_*`. The
  acceptance extraction itself (≈ $0.37) was paid in the first live run and replayed here.

## Reproduce

```bash
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-a article --url "https://privatebank.jpmorgan.com/apac/en/insights/markets-and-investing/tmt/software-shock-ais-broken-logic" --as-of 2026-02-09
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-a export-state --out /tmp/ti-state
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-b import-state --src /tmp/ti-state
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-b article --url "https://example.test/hypothetical/capex-reaffirmed-2026-02-20" --as-of 2026-02-20 --publisher "Hypo Wire (HYPOTHETICAL TEST FIXTURE)" --html tests/fixtures/theme_intelligence/hypothetical_b/article.html --fixture tests/fixtures/theme_intelligence/hypothetical_b/extraction.json
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-b qa --run latest
```

(A fresh run re-fetches the page and re-runs the LLM passes; outputs will differ in wording, not in
the deterministic rules. CI replays the FROZEN extraction instead — `tests/fixtures/theme_intelligence/`.)
