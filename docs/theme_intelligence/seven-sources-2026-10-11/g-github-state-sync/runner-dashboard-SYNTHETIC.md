# What to research this week — run R-20261011T150523Z-scan

_Research attention only — no row is a purchase or sale._

- Scan execution: SUCCEEDED
- Research verification: INCOMPLETE — NOT fully verified — over the 2 article(s), 3 version(s) this report's 5 runs analysed: 0 of 21 stated figure(s) and 1 of 17 argument paragraph(s) open; 1 completeness pass(es) did not run; causes: pass_not_run 1. Open material is never used as evidence, so it can hold a thesis back but never raise its research action
- Window: 2026-10-02 → 2026-10-11 (as of 2026-10-11, mode scan)
- Accessible sources: 5 of 5 (automatic channels)
- Blocked sources: none
- Manual-first sources (health check only; research arrives as uploads): Morgan Stanley, Goldman Sachs
- Articles analyzed: 2 full · 1 partial; queued by the budget cap, not yet read: 6
- Research Now / Watch / Skip: 1 / 1 / 0 — of the 2 theses this run created or changed (archived in the registry: 0)
- New / upgraded / downgraded / challenged theses: 2 / 0 / 0 / 0 — this run's events; a thesis new this run can also be challenged in it
- Reported figures not yet captured: 0 of 0

## Research source health

**Sources healthy: 2/7 | Degraded: 3 | Blocked: 2 | Errors: 0** — checked 2026-10-11 15:08 UTC; the channels' health, apart from execution and research verification

- **Change — Citi** [NEW_FAILURE]: first check of this channel
- **Change — Nomura** [NEW_FAILURE]: first check of this channel
- **Change — SemiAnalysis** [NEW_FAILURE]: first check of this channel
- **Citi** — DEGRADED: partial: 1 of 3 sampled article(s) partial (short body (96 words) — treated as a teaser / excerpt); 2 sampled page(s) summarise a report they link to — the scan READS it (linked_reports = "fetch") → UPLOAD_REQUIRED: upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source citi_must_c [--url <article URL>] if you are entitled to the full text
- **Morgan Stanley** — BLOCKED: robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com — cannot safely proceed: nothing is fetched (handled conservatively, re-tested every check) → UPLOAD_REQUIRED: automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source ms_research [--url <article URL>]
- **Nomura** — DEGRADED: partial: 1 of 3 sampled article(s) partial (the page summarises a fuller report it links to; that report was not read (http://go.nomuranow.com/research/japi/publication/1314426?appname=CONNECTS)) → UPLOAD_REQUIRED: upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source nomura_connects [--url <article URL>] if you are entitled to the full text
- **SemiAnalysis** — DEGRADED: partial: 1 of 3 sampled article(s) are paywalled previews — only the preview is readable → UPLOAD_REQUIRED: upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source semianalysis [--url <article URL>] if you are entitled to the full text
- **Goldman Sachs** — BLOCKED: https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403) → UPLOAD_REQUIRED: automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source gs_research [--url <article URL>]

| Publisher | Health | Freshness | Last checked | Last discovery OK | Last full-text OK | Last verified publication date | Discovered / listing-dated in window | Consecutive failed | Manual upload |
|---|---|---|---|---|---|---|---|---|---|
| Citi | DEGRADED | QUIET | 2026-10-11T15:05 | 2026-10-11 | — | 2026-09-14 | 20 / 0 | 1 | yes |
| J.P. Morgan Private Bank | HEALTHY | FRESH | 2026-10-11T15:05 | 2026-10-11 | 2026-10-11 | 2026-10-02 | 51 / 1 | 0 | — |
| Morgan Stanley | BLOCKED | UNKNOWN | 2026-10-11T15:06 | — | — | — | 0 / 0 | 1 | yes |
| Nomura | DEGRADED | FRESH | 2026-10-11T15:06 | 2026-10-11 | 2026-10-11 | 2026-10-07 | 14 / 0 | 1 | yes |
| TrendForce | HEALTHY | FRESH | 2026-10-11T15:07 | 2026-10-11 | 2026-10-11 | 2026-10-08 | 5 / 2 | 0 | — |
| SemiAnalysis | DEGRADED | FRESH | 2026-10-11T15:07 | 2026-10-11 | 2026-10-11 | 2026-10-08 | 20 / 2 | 1 | yes |
| Goldman Sachs | BLOCKED | UNKNOWN | 2026-10-11T15:08 | — | — | — | 0 / 0 | 1 | yes |

## Research intake / manual action

**1 analysed automatically · 3 imported manually · 0 partial awaiting a complete document · 5 publisher(s) blocked or degraded · 5 needing an upload · 2 needing a metadata or licence check · 4 coverage gap(s)** — ingestion coverage over 5 run(s), apart from source health and research verification

**Coverage by publisher (the configured channels)** (7)
- Citi [automatic; access DEGRADED] — 0 article(s) analysed automatically, 0 supplied — PARTIAL automated coverage — see source health
- J.P. Morgan Private Bank [automatic; access HEALTHY] — 0 article(s) analysed automatically, 0 supplied — automated coverage
- Morgan Stanley [manual-first; access BLOCKED] — 0 article(s) analysed automatically, 1 supplied — MANUAL-FIRST — 1 supplied document(s) analysed this week
- Nomura [automatic; access DEGRADED] — 0 article(s) analysed automatically, 0 supplied — PARTIAL automated coverage — see source health
- TrendForce [automatic; access HEALTHY] — 0 article(s) analysed automatically, 0 supplied — automated coverage
- SemiAnalysis [automatic; access DEGRADED] — 1 article(s) analysed automatically, 1 supplied — PARTIAL automated coverage — see source health
- Goldman Sachs [manual-first; access BLOCKED] — 0 article(s) analysed automatically, 0 supplied — MANUAL-FIRST — nothing supplied this week: its research this week is MISSING, not absent

**Articles automatically analysed** (1)
- SemiAnalysis — “Synthetic Memory Note: Inference Keeps Memory Tight” — published 2026-09-28; FULL; analysed as of 2026-10-11 (article run) [A-830a528c98ba]

**Articles manually imported** (3)
- Morgan Stanley — “Synthetic Utilities Note: AI Power Demand” (737cf809ea03c04c0a851836c1ef92fa481d06f1a7d973ff1ea5185008dd3226.pdf; pdf, 2 page(s)) — INGESTED, manual upload; published 2026-10-01 (the document text (page 1-2)); uploaded 2026-10-11 14:56 UTC; analysed as of 2026-10-11; original NOT on this machine — its text is not re-verifiable here; article A-22c4843c119d [D-737cf809ea03c04c]
- SemiAnalysis — “Synthetic Memory Note: Inference Keeps Memory Tight” (semianalysis_full_synthetic.pdf; pdf, 1 page(s)) — UPGRADED, manual upload; published 2026-09-28 (the document text (page 1-2)); uploaded 2026-10-11 14:53 UTC; analysed as of 2026-10-11; original NOT on this machine — its text is not re-verifiable here; article A-830a528c98ba [D-d84d23f59e316425]
- Morgan Stanley — “Synthetic Utilities Note: AI Power Demand Moves On-Site” (ms_report_synthetic.html; html) — REVIEW, manual upload; published 2026-10-01 (the document text (opening lines)); uploaded 2026-10-11 15:03 UTC; analysed as of 2026-10-11; original NOT on this machine — its text is not re-verifiable here; article A-22c4843c119d [D-ff11efe9f6404cc4]

**Partial articles awaiting a complete document** (0)
- none

**Publishers blocked or degraded** (5)
- Citi: DEGRADED — partial: 1 of 3 sampled article(s) partial (short body (96 words) — treated as a teaser / excerpt); 2 sampled page(s) summarise a report they link to — the scan READS it (linked_reports = "fetch")
- Morgan Stanley: BLOCKED — robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com — cannot safely proceed: nothing is fetched (handled conservatively, re-tested every check)
- Nomura: DEGRADED — partial: 1 of 3 sampled article(s) partial (the page summarises a fuller report it links to; that report was not read (http://go.nomuranow.com/research/japi/publication/1314426?appname=CONNECTS))
- SemiAnalysis: DEGRADED — partial: 1 of 3 sampled article(s) are paywalled previews — only the preview is readable
- Goldman Sachs: BLOCKED — https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403)

**Known articles requiring an upload** (5)
- Citi (channel DEGRADED) — upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source citi_must_c [--url <article URL>] if you are entitled to the full text — known: https://www.citigroup.com/global/insights/money-the-evolution-to-digital — Money: The Evolution to Digital
- Morgan Stanley (channel BLOCKED) — automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source ms_research [--url <article URL>] — known: unknown — the channel cannot be read
- Nomura (channel DEGRADED) — upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source nomura_connects [--url <article URL>] if you are entitled to the full text — known: https://www.nomuraconnects.com/focused-thinking-posts/beyond-the-headlines-ai-has-added-jobs-in-asia-so-far — Beyond the Headlines: AI Has Added Jobs in Asia – So Far
- SemiAnalysis (channel DEGRADED) — upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source semianalysis [--url <article URL>] if you are entitled to the full text — known: https://newsletter.semianalysis.com/p/are-open-models-catching-up — Are Open Models Catching Up?
- Goldman Sachs (channel BLOCKED) — automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source gs_research [--url <article URL>] — known: unknown — the channel cannot be read

**Requiring a metadata or licence check** (2)
- nomura_connects — “Finding Opportunities in an Uncertain World” — the page states no publication date — not placed in any window: VERIFY its date, then analyse it with `article --url <url> --published <verified date>` (https://www.nomuraconnects.com/focused-thinking-posts/opportunity-in-an-uncertain-world)
- REVIEW (which article it is, is uncertain) — Morgan Stanley — “Synthetic Utilities Note: AI Power Demand Moves On-Site” (ms_report_synthetic.html; html) — REVIEW, manual upload; published 2026-10-01 (the document text (opening lines)); uploaded 2026-10-11 15:03 UTC; analysed as of 2026-10-11; original NOT on this machine — its text is not re-verifiable here; article A-22c4843c119d [D-ff11efe9f6404cc4]

**Unknown publisher-level coverage gaps** (4)
- Morgan Stanley: coverage UNKNOWN (BLOCKED) — what it published cannot be seen by this system; no new article from it is NOT evidence it published nothing
- Goldman Sachs: coverage UNKNOWN (BLOCKED) — what it published cannot be seen by this system; no new article from it is NOT evidence it published nothing
- citi_must_c: partial discovery — the Must C page embeds its 20 linked series items; older items are not listed there
- 6 in-window article(s) queued by the budget cap — discovered, not yet read

## Source coverage

| Source | Status | Discovered | In window | Undated | New | Processed | Queued | Inaccessible | Errors / warnings |
|---|---|---|---|---|---|---|---|---|---|
| citi_must_c | OK | 20 | 0 | 0 | 0 | 0 | 0 | 0 | — (the Must C page embeds its 20 linked series items; older items are not listed there) |
| jpm_tmt | OK | 51 | 1 | 0 | 1 | 0 | 1 | 0 | — |
| ms_research | MANUAL_FIRST | 0 | 0 | 0 | 0 | 0 | 0 | 0 | automated access: BLOCKED — robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com — cannot safely proceed: nothing is fetched (handled cons |
| nomura_connects | OK | 14 | 1 | 1 | 1 | 0 | 1 | 0 | 1 candidate(s) carry no publication date the source states — counted UNDATED, never placed in a window; listed on the dashboard for date verification (`article --url <url> --published <verified date>`) |
| trendforce | OK | 5 | 2 | 0 | 2 | 0 | 2 | 0 | — |
| semianalysis | OK | 20 | 2 | 0 | 2 | 0 | 2 | 0 | — |
| gs_research | MANUAL_FIRST | 0 | 0 | 0 | 0 | 0 | 0 | 0 | automated access: BLOCKED — https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403) |

## Research verification — open items (1)

- AV-695ffbd28f09b41d b002 paragraph — pass_not_run: the completeness pass did not run

## Unresolved caveats

- PARTIAL_RETRIEVAL A-830a528c98ba: only part of the article was retrieved — no claim of full-text verification is made
- ARGUMENT_UNACCOUNTED A-830a528c98ba: b002: the completeness pass did not run
- COMPLETENESS_PASS_NOT_RUN A-830a528c98ba: fixture replay without a frozen completeness pass — only the deterministic figure / argument ledger ran

## NEW (2) — first recorded this run — new to the registry, not necessarily new to the market

### [RESEARCH NOW] Inference demand keeps memory supply tight
- Published 2026-09-28 · first ingested by the registry 2026-10-11 14:52 UTC (new to the registry, not necessarily new to the market) · analysed as of 2026-10-11
- Evidence direction: MIXED
- Why this action: Research Now — every condition met (an investigation, not a trade)
- What changed:
  - Memory demand keeps rising with inference
  - Direct confirmation — new evidence: Server DRAM inventory at hyperscalers fell to four weeks in 3Q26, the lowest in the synthetic series.
  - Direct confirmation — new evidence: Conventional DRAM contract prices are projected to rise 14% QoQ in 4Q26, the third consecutive quarterly increase.
  - Direct confirmation — new evidence: Memory demand keeps rising as inference workloads scale, and operators expect tightness to persist into next year.
  - Direct confirmation — new evidence: HBM supply stays allocated well ahead of shipments and contract terms are lengthening at every major supplier.
  - Direct confirmation — new evidence: HBM shipments are projected to grow 35% YoY in 2026 as accelerator volumes ramp.
  - Direct confirmation — new evidence: HBM's share of total DRAM revenue climbs above one third.
  - Direct confirmation — new evidence: Memory makers' capex is projected to rise 20% in 2026, mostly to advanced DRAM nodes and HBM packaging.
  - Direct confirmation — new evidence: DDR5 module spot prices rose 8% in September in the synthetic tracker.
  - Direct confirmation — new evidence: Module makers reported hyperscale customers placing orders two quarters ahead of need.
  - Direct confirmation — new evidence: Suppliers are expected to keep capacity additions disciplined due to past downturn and investor preference for restraint.
  - showing 10 of 11 pieces of evidence from A-830a528c98ba — the rest are in 04 KEY EVIDENCE and the evidence ledger
- Sources:
  - SemiAnalysis — Synthetic Analyst One; Synthetic Analyst Two — “Synthetic Memory Note: Inference Keeps Memory Tight” (article date 2026-09-28) — first record of this thesis
  - SemiAnalysis — Synthetic Analyst One; Synthetic Analyst Two — “Synthetic Memory Note: Inference Keeps Memory Tight” (article date 2026-09-28) — contradiction — evidence against this thesis
- How this evidence arrived: automatic (A-830a528c98ba); manual upload (D-d84d23f59e316425 “semianalysis_full_synthetic.pdf”, uploaded 2026-10-11, A-830a528c98ba)
- Exposure the source names: sector: HBM (positive); sector: Conventional DRAM (positive)
- Next research step: Identify listed memory makers most levered to HBM/advanced DRAM and check whether consensus estimates and valuations already price in the projected 2026 pricing and shipment gains.
- Audit: `TH-0B867D3317` v2 · flags UPGRADED · WATCH → RESEARCH NOW: F2_material_evidence 1→8; F3_independent_origins 1→2; F4_profit_transmission inferred→source-shown; F5_near_term_relevance not shown→yes; F6_recognizable_exposures 0 listed · 0 sector→0 listed · 2 sector; F7_dislocation_or_catalyst absent→present; F12_fundamental_inflection absent→qualifies; F11_retrieval PARTIAL→FULL · card: cards/TH-0B867D3317.html

### [WATCH] AI data centre capex growth drives on-site power demand, benefiting turbine and fuel-cell suppliers
- Published 2026-10-01 · first ingested by the registry 2026-10-11 14:56 UTC (new to the registry, not necessarily new to the market) · analysed as of 2026-10-11
- Evidence direction: NEW
- Why this action: Watch — not yet Research Now: no verified dislocation or catalyst, and the near-term inflection does not qualify (2 near-term change(s) but NOT credible — a forecast alone: no corroborating measured observation, and not the publisher's own data in an industry data report)
- What changed:
  - The median wait for a large-load grid connection lengthened to 48 months, pushing operators towards on-site generation.
  - On-site gas turbine orders are projected to grow 30% in 2027 as operators bypass constrained grids.
  - Hyperscaler AI data centre capex is expected to rise 24% in 2027, led by power and cooling.
  - Grid interconnection queues reached 2,600 GW in the synthetic dataset.
  - Synthetic AI capex in 2Q26 was $44.9bn
  - AI share of capex in 2Q26 was 39%
  - showing 6 of 10 pieces of evidence from A-22c4843c119d — the rest are in 04 KEY EVIDENCE and the evidence ledger
- Sources:
  - Morgan Stanley — Synthetic Strategist — “Synthetic Utilities Note: AI Power Demand” (article date 2026-10-01) — first record of this thesis
- How this evidence arrived: manual upload (D-737cf809ea03c04c “737cf809ea03c04c0a851836c1ef92fa481d06f1a7d973ff1ea5185008dd3226.pdf”, uploaded 2026-10-11, A-22c4843c119d)
- Exposure the source names: sector: turbine and fuel-cell suppliers (positive)
- Next research step: Identify listed turbine and fuel-cell suppliers with exposure to on-site data centre power and check whether consensus reflects the projected 2027 order growth.
- Audit: `TH-A90A29D80F` v1 · initial assessment — WATCH (RESEARCH NOW unmet: no verified dislocation or catalyst, and the near-term inflection does not qualify (2 near-term change(s) but NOT credible — a forecast alone: no corroborating measured observation, and not the publisher's own data in an industry data report)) · card: cards/TH-A90A29D80F.html

## UPGRADED (0) — research action raised on material evidence

_None this run._

## DOWNGRADED (0) — research action lowered — shown in full, never under the upgrades

_None this run._

## CHALLENGED (0) — contradictory evidence, a correction or a timing change arrived

_None this run._

## UNCHANGED BUT MATERIAL (0) — material evidence added; research action unchanged

_None this run._

## ARCHIVED (0) — moved off the active list (SKIP, or no material evidence for a quarter) — still searchable below

_None this run._

## Archive (every thesis)

| Thesis | Action | Evidence | Status | Sector | Ver | Last material update |
|---|---|---|---|---|---|---|
| Inference demand keeps memory supply tight (`TH-0B867D3317`) | RESEARCH NOW | MIXED | ACTIVE | Memory (DRAM, HBM, NAND): supply, pricing, capacity | 2 | 2026-09-28 |
| AI data centre capex growth drives on-site power demand, benefiting turbine and fuel-cell suppliers (`TH-A90A29D80F`) | WATCH | NEW | ACTIVE | Power generation, grid and interconnection for AI datacenters | 1 | 2026-10-01 |

_Verification log: 0 blocked · 0 held · 9 warnings · 4 info. Generated 2026-10-11 15:09 UTC from the registry (ti-engine-2; run R-20261011T150523Z-scan, extract ti-extract-6, review ti-review-4, model claude-opus-4-8)._
