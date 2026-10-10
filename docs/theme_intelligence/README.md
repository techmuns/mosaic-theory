# Theme intelligence — worked output (2026-10-10, after the PR #703 review)

Derived readouts of the real runs that verify the corrected build: dashboards, nine-section cards
(web, print, Markdown, JSON), run manifests, validation logs and QA reports. No database, no
article full text — card evidence quotes are the short verbatim spans that anchor each claim.
Every folder was rendered by the final code (`5c9f3b9a`) from a FRESH registry; model answers are
content-cached, so a replayed answer costs nothing. Operator guide:
[`../theme_intelligence.md`](../theme_intelligence.md) · record:
[`../records/2026-10-10-theme-intelligence-review-corrections.md`](../records/2026-10-10-theme-intelligence-review-corrections.md).

| folder | what it shows |
|---|---|
| [`acceptance-software-shock-2026-02-09/`](acceptance-software-shock-2026-02-09/) | J.P. Morgan "Software Shock: AI's Broken Logic" as of 2026-02-09 — **exactly three theses, all WATCH**; the top-10 correlation "in the 99th percentile" kept as a market risk; Alphabet = **GOOGL / GOOG** from the 10-K cover filed 2026-02-05, GOOGM / GOOGN not registered as of the date; ledger 34 figures, 0 open; QA 19/19 |
| [`acceptance-calm-index-2026-10-10/`](acceptance-calm-index-2026-10-10/) | J.P. Morgan "A calm index, a restless market" (2026-10-02) — the **utilities thesis AND the dispersion argument as a market-regime record**, both RESEARCH NOW; ~43%, 75%, 11.2 and 41 captured; ledger 19 figures, 0 open; **Kriti Gupta and Nick Roberts**; QA 19/19 |
| [`overlap-semianalysis-trendforce/`](overlap-semianalysis-trendforce/) | **two publishers, one thesis, real articles:** SemiAnalysis's "Inside GLM-5.3: How Sparse Attention Affects DRAM Memory TAM" (2026-09-28) creates "Sparse attention does not reduce overall AI memory capacity demand"; TrendForce's "AI Server Demand Sustains Memory Contract Price Increases in 4Q26, While Consumer-Side Pressure Persists" (2026-09-30) independently confirms it → the SAME thesis, version 2, evidence STRONGER, each publisher on its own source line (SemiAnalysis: initial record, origins InferenceX + its own analysis; TrendForce: new evidence from an origin the thesis did not hold). TrendForce's pricing argument is a separate SIBLING (same node, different mechanism) — linked, not merged |
| [`contradiction-semianalysis-jpm/`](contradiction-semianalysis-jpm/) | **contradictory evidence, real articles:** SemiAnalysis (2026-09-15) argues grid friction pushes datacenters behind the meter (positive, `ai_infrastructure.power_grid`); J.P. Morgan (2026-10-02) argues moratoriums and rates pressure utilities (negative, same node). The engine links them as COMPETING (never merged), files J.P. Morgan's evidence against the SemiAnalysis thesis (version 2, WEAKER, "challenged") and says on the card that the two share the node but not the mechanism — see the record for why this challenge is a flag for the analyst, not a refutation |
| [`weekly-reprocessed-2026-10-10/`](weekly-reprocessed-2026-10-10/) | the first build's weekly sample **reprocessed from scratch** on the final code — `scan --from 2026-10-01 --to 2026-10-10`: 6 of 8 channels reachable (Morgan Stanley, Goldman Sachs BLOCKED — never bypassed), 6 dated articles in the window (2 TrendForce, 2 SemiAnalysis, 1 Nomura, 1 J.P. Morgan) plus 13 undated pages counted and never placed; 192 claims span-verified; 10 theses (Research Now / Watch / Skip 2 / 7 / 1); one SemiAnalysis thesis challenged twice by one article (v3); QA 18/20 — 3 figures and 2 paragraphs left open by the completeness pass, listed, never hidden |

Screenshots (`screenshots/`): `calm-dashboard.png` and `weekly-dashboard.png` (the KPI strip, the article date beside the first-detected date); `calm-card-regime-web.png` (the compact decision view: 01 / 02 / 06 / 08 open, the rest on demand) and `calm-card-regime-print.png` (print: every section and audit field open); `software-shock-dashboard.png`, `software-shock-card-ai-infrastructure-web.png`; `overlap-card-merged-sources.png` (section 09 of the merged card: each publisher's own line, v1 → v2) and `contradiction-card-challenged.png` (sections 02 / 07 / 09 of the challenged card). The last two are the real print cards with one added style rule that hides the other sections — the content is unchanged

The four folders of the first build (`acceptance-jpm-2026-02-09/`, `a-to-b-hypothetical-2026-02-20/`,
`weekly-run-2026-10-10/`, `first-scan-2026-10-10/`) and its screenshots were produced by the
pre-review code and are retired — they carried the defects the review named (GOOGM / GOOGN as
Alphabet stock, a RESEARCH NOW resting on a rhetorical question). They remain in git history. The
hypothetical A → B update on exported / re-imported state stays pinned by the test suite.

## Boundaries of every number above

- **Runs:** commit `5c9f3b9a`, 2026-10-10, model `claude-opus-4-8`, prompts `ti-extract-6` /
  `ti-complete-1` / `ti-review-4`, one fresh registry per folder; each article replayed AS OF the
  date shown (later-dated facts refused).
- **Ledger counts:** figures are the numbers the article's BODY states — numerals with their sign
  and unit (glued units such as "75GW" included), counted periods and ranges in words, a
  percentile — but not years, tenors ("200-day"), days of a month, numbers inside names ("S&P
  500", "GLM-5.3") or list markers ("(1)"); argument blocks are paragraphs / list items of at
  least 12 words. "Open" = neither captured by a verified claim nor judged immaterial with a
  reason.
- **SemiAnalysis** posts are paid: only the public preview is retrieved and analysed, recorded
  PARTIAL — never presented as full-text analysis.
- **Weekly:** window 2026-10-01 → 2026-10-10 (10 days ending the run date), as-of 2026-10-10, the eight configured channels as reachable on 2026-10-10 with the honest User-Agent; "discovered" = unique canonical URLs a channel's listing / feed / page data exposed; "in window" = those whose SOURCE-STATED date falls inside it; undated pages are counted, never placed. The KPI counts are over the theses this run created or changed and its events

## Reproduce

```bash
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-ss article --url "https://privatebank.jpmorgan.com/apac/en/insights/markets-and-investing/tmt/software-shock-ais-broken-logic" --as-of 2026-02-09
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-calm article --url "https://privatebank.jpmorgan.com/apac/en/insights/markets-and-investing/tmt/a-calm-index-a-restless-market" --as-of 2026-10-10
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-overlap article --url "https://newsletter.semianalysis.com/p/sparse-savings-persistent-demand-inside-glm53" --as-of 2026-09-28
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-overlap article --url "https://www.trendforce.com/presscenter/news/20260930-13258.html" --as-of 2026-09-30
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-contra article --url "https://newsletter.semianalysis.com/p/everyone-says-datacenter-moratoriums" --as-of 2026-09-15
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-contra article --url "https://privatebank.jpmorgan.com/apac/en/insights/markets-and-investing/tmt/a-calm-index-a-restless-market" --as-of 2026-10-02
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-weekly scan --from 2026-10-01 --to 2026-10-10 --as-of 2026-10-10
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-weekly qa --run latest
```

A fresh run re-fetches the pages and re-runs the model passes: wording will differ, the
deterministic rules will not. CI replays the FROZEN outputs instead
(`tests/fixtures/theme_intelligence/`).
