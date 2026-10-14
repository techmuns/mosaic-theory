# Theme intelligence — worked output (2026-10-10 runs, after review round 3)

Derived readouts of the real runs that verify the build after the PR #703 review rounds:
dashboards, nine-section cards (web, print, Markdown, JSON), run manifests, validation logs and QA
reports. No database, no article full text — card evidence quotes are the short verbatim spans
that anchor each claim. Every folder was rendered by code commit `0b75b811` from a FRESH registry
(run 2026-10-10 19:15 UTC); model answers are content-cached, so a replayed answer costs nothing.
Operator guide: [`../theme_intelligence.md`](../theme_intelligence.md) · records:
[`round 3`](../records/2026-10-11-theme-intelligence-review-round-3.md),
[`round 2`](../records/2026-10-10-theme-intelligence-review-corrections.md).

Every QA report states two things apart: the SCAN EXECUTION status (did the run complete?) and the
RESEARCH VERIFICATION status (is everything it read accounted for?).

| folder | what it shows |
|---|---|
| [`acceptance-software-shock-2026-02-09/`](acceptance-software-shock-2026-02-09/) | J.P. Morgan "Software Shock: AI's Broken Logic" as of 2026-02-09 — **exactly three theses, all WATCH**; Alphabet = **GOOGL / GOOG** VERIFIED from the 10-K cover filed 2026-02-05; ledger 34 figures / 12 paragraphs, 0 open; QA 20/20, FULLY_VERIFIED |
| [`acceptance-calm-index-2026-10-10/`](acceptance-calm-index-2026-10-10/) | J.P. Morgan "A calm index, a restless market" (2026-10-02) — the **utilities thesis** (now segmented: grid-connected utilities, id `TH-30F6348B8B`) **AND the dispersion market-regime record**, both RESEARCH NOW; 19 figures, 0 open; **Kriti Gupta and Nick Roberts**; QA 20/20, FULLY_VERIFIED |
| [`contradiction-semianalysis-jpm/`](contradiction-semianalysis-jpm/) | **no false weakening, real articles:** SemiAnalysis (2026-09-15) "Grid friction pushes datacenters behind-the-meter" (on-site generation) stays v1, WATCH; J.P. Morgan's utilities thesis (2026-10-02) is linked **RELATED, not a contradiction** — different mechanism, segment and timeframe named on the link; 0 challenges. `qa-step1.txt`: the SemiAnalysis preview, scan PARTIAL / verification INCOMPLETE (one paragraph, `no_account`) |
| [`overlap-semianalysis-trendforce/`](overlap-semianalysis-trendforce/) | **direct vs adjacent, real articles:** SemiAnalysis's sparse-attention thesis (DRAM / HBM, 2026-09-28) and TrendForce's pricing (DRAM / HBM + NAND / SSD) and enterprise-SSD (NAND / SSD) theses (2026-09-30) stay **separate, linked ADJACENT SUPPORT** — never a merge, never a confirmation. `qa-step1.txt`: the SemiAnalysis preview, PARTIAL / INCOMPLETE ("GLM's 5.2 / 5.3", `capture_not_verified`) |
| [`trendforce-4q26-2026-09-30/`](trendforce-4q26-2026-09-30/) | **the near-term inflection route:** TrendForce's 4Q26 contract-price and enterprise-SSD forecasts — the tracker's own data, the pricing step stated, a research question composed in the first view — **RESEARCH NOW without a dislocation or dated catalyst**; QA 20/20, FULLY_VERIFIED |
| [`weekly-with-source-health-2026-10-11/`](weekly-with-source-health-2026-10-11/) | **source health (Priority 1A):** `health-check-1.txt` — the live `sources --check-health` of the eight channels (2026-10-11 08:28 UTC): `Sources healthy: 2/8 | Degraded: 4 | Blocked: 2 | Errors: 0`; `health-check-2.json` — the `--json` re-check two minutes later (Morgan Stanley / Goldman Sachs not re-requested, streaks continued, no repeated alert); and the weekly scan that checks health at its start — the dashboard's "Research source health" block beside scan execution SUCCEEDED and research verification INCOMPLETE; QA 21/22 |
| [`weekly-reprocessed-2026-10-10/`](weekly-reprocessed-2026-10-10/) | the weekly sample reprocessed from scratch — `scan --from 2026-10-01 --to 2026-10-10`: **scan execution SUCCEEDED, research verification INCOMPLETE**; 6 of 8 channels (Morgan Stanley, Goldman Sachs BLOCKED — never bypassed); 6 dated articles; 10 theses, Research Now / Watch / Skip 2 / 7 / 1, 0 challenges; 0 of 228 figures and 1 of 170 paragraphs open (b008, `account_names_no_record`); QA 20/21 |

Screenshots (`screenshots/`): `weekly-dashboard.png` (the two statuses in the header, the
open-items panel and the verification tile; each row's three dates), `calm-dashboard.png`,
`software-shock-dashboard.png`, `trendforce-dashboard.png` (the inflection's "why" in the first
view); `calm-card-regime-web.png` / `calm-card-regime-print.png`,
`software-shock-card-ai-infrastructure-web.png`; and focused captures of real print cards — the
file unchanged but for one added style rule that hides the other sections:
`contradiction-card-related.png` (J.P. Morgan's utilities card, sections 07 / 09: the RELATED link
and why), `contradiction-card-btm-unchanged.png` (the behind-the-meter card: v1, nothing filed
against it), `overlap-card-adjacent-support.png` (TrendForce's pricing card, 07 / 09: the
ADJACENT SUPPORT link) and `trendforce-card-inflection.png` (section 08 with the audit view on:
the decision trace naming the route and the question). Source health: `weekly-dashboard-source-health.png` (the block on the dashboard) and `source-health-block-expanded.png` (the block alone, all eight publishers expanded).

The round-2 folders' merged SemiAnalysis / TrendForce card and challenged behind-the-meter card,
and their screenshots, showed the behaviour this round reversed; they remain in the repository
history.

The four folders of the first build (`acceptance-jpm-2026-02-09/`, `a-to-b-hypothetical-2026-02-20/`,
`weekly-run-2026-10-10/`, `first-scan-2026-10-10/`) and its screenshots were produced by the
pre-review code and are retired — they carried the defects the review named (GOOGM / GOOGN as
Alphabet stock, a RESEARCH NOW resting on a rhetorical question). They remain in git history. The
hypothetical A → B update on exported / re-imported state stays pinned by the test suite.

## Boundaries of every number above

- **Runs:** commit `0b75b811`, 2026-10-10 19:15 UTC, model `claude-opus-4-8`, prompts
  `ti-extract-6` / `ti-complete-1` / `ti-review-4`, one fresh registry per folder; each article
  replayed AS OF the date shown (later-dated facts refused) — every card says "a historical
  replay" where the as-of precedes ingestion.
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
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-tf article --url "https://www.trendforce.com/presscenter/news/20260930-13258.html" --as-of 2026-09-30
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-contra article --url "https://newsletter.semianalysis.com/p/everyone-says-datacenter-moratoriums" --as-of 2026-09-15
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-contra article --url "https://privatebank.jpmorgan.com/apac/en/insights/markets-and-investing/tmt/a-calm-index-a-restless-market" --as-of 2026-10-02
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-weekly scan --from 2026-10-01 --to 2026-10-10 --as-of 2026-10-10
.venv/bin/python -m vinci.theme_intelligence --data-dir /tmp/ti-weekly qa --run latest
```

A fresh run re-fetches the pages and re-runs the model passes: wording will differ, the
deterministic rules will not. CI replays the FROZEN outputs instead
(`tests/fixtures/theme_intelligence/`).
