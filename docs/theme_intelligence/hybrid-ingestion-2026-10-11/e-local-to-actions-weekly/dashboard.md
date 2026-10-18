# What to research this week — run R-20261011T110031Z-scan

_Research attention only — no row is a purchase or sale._

- Scan execution: SUCCEEDED
- Research verification: FULLY_VERIFIED — every figure and argument paragraph accounted for, full text read (over the 1 article(s) this report's 3 runs analysed: 0 of 7 stated figure(s) and 0 of 17 argument paragraph(s) open)
- Window: 2026-10-02 → 2026-10-11 (as of 2026-10-11, mode scan)
- Accessible sources: 6 of 8
- Blocked sources: Morgan Stanley, Goldman Sachs
- Articles analyzed: 1 full · 0 partial
- Research Now / Watch / Skip: 1 / 1 / 0 — of the 2 theses this run created or changed (archived in the registry: 1)
- New / upgraded / downgraded / challenged theses: 1 / 0 / 0 / 0 — this run's events; a thesis new this run can also be challenged in it
- Reported figures not yet captured: 0 of 0

## Research source health

**Sources healthy: 2/8 | Degraded: 4 | Blocked: 2 | Errors: 0** — checked 2026-10-11 11:02 UTC; the channels' health, apart from execution and research verification

- **Citi** — DEGRADED: partial: 1 of 3 sampled article(s) partial (short body (96 words) — treated as a teaser / excerpt); latest scan R-20261011T083033Z-scan: 0 full, 0 preview / partial, 0 unreadable; 2 sampled page(s) summarise a report they link to — the scan READS it (linked_reports = "fetch") → UPLOAD_REQUIRED: upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source citi_must_c [--url <article URL>] if you are entitled to the full text
- **Bank of America** — DEGRADED: metadata problem: 2 of 3 sampled article(s) carry no publication date on the page or the listing — undated articles are never placed in a window (1 of 3 sampled page(s) state a publication date; the listing dates 0 of 16; 1 of 3 carry a byline; latest scan R-20261011T083033Z-scan: 12 of 16 undated) → MANUAL_REVIEW: review: publication dates are not on the pages, so articles are counted UNDATED and never placed in a window — analyse one on demand with `article --url`
- **Morgan Stanley** — BLOCKED: robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com — cannot safely proceed: nothing is fetched (handled conservatively, re-tested every check) → UPLOAD_REQUIRED: automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence article --url <article URL> --html <saved page> --as-of <date> --source ms_research
- **Nomura** — DEGRADED: partial: 1 of 3 sampled article(s) partial (the page summarises a fuller report it links to; that report was not read (http://go.nomuranow.com/research/japi/publication/1314426?appname=CONNECTS)); latest scan R-20261011T083033Z-scan: 1 full, 0 preview / partial, 0 unreadable → UPLOAD_REQUIRED: upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source nomura_connects [--url <article URL>] if you are entitled to the full text
- **SemiAnalysis** — DEGRADED: partial: 1 of 3 sampled article(s) are paywalled previews — only the preview is readable; latest scan R-20261011T083033Z-scan: 1 full, 1 preview / partial, 0 unreadable → UPLOAD_REQUIRED: upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source semianalysis [--url <article URL>] if you are entitled to the full text
- **Goldman Sachs** — BLOCKED: https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403) → UPLOAD_REQUIRED: automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence article --url <article URL> --html <saved page> --as-of <date> --source gs_research

| Publisher | Health | Freshness | Last checked | Last discovery OK | Last full-text OK | Last verified publication date | Discovered / listing-dated in window | Consecutive failed | Manual upload |
|---|---|---|---|---|---|---|---|---|---|
| Citi | DEGRADED | QUIET | 2026-10-11T11:00 | 2026-10-11 | 2026-10-11 | 2026-09-14 | 20 / 0 | 2 | yes |
| Bank of America | DEGRADED | QUIET | 2026-10-11T11:00 | 2026-10-11 | 2026-10-11 | 2026-06-25 | 16 / 0 | 2 | — |
| J.P. Morgan Private Bank | HEALTHY | FRESH | 2026-10-11T11:01 | 2026-10-11 | 2026-10-11 | 2026-10-02 | 51 / 1 | 0 | — |
| Morgan Stanley | BLOCKED | UNKNOWN | 2026-10-11T08:30 | — | — | — | 0 / 0 | 1 | yes |
| Nomura | DEGRADED | FRESH | 2026-10-11T11:01 | 2026-10-11 | 2026-10-11 | 2026-10-07 | 14 / 0 | 2 | yes |
| TrendForce | HEALTHY | FRESH | 2026-10-11T11:02 | 2026-10-11 | 2026-10-11 | 2026-10-08 | 5 / 2 | 0 | — |
| SemiAnalysis | DEGRADED | FRESH | 2026-10-11T11:02 | 2026-10-11 | 2026-10-11 | 2026-10-08 | 20 / 2 | 2 | yes |
| Goldman Sachs | BLOCKED | UNKNOWN | 2026-10-11T08:31 | — | — | — | 0 / 0 | 1 | yes |

## Research intake / manual action

**0 analysed automatically · 1 imported manually · 1 partial awaiting a complete document · 6 publisher(s) blocked or degraded · 5 needing an upload · 1 needing a metadata or licence check · 3 coverage gap(s)** — ingestion coverage over 3 run(s), apart from source health and research verification

**Articles automatically analysed** (0)
- none

**Articles manually imported** (1)
- TrendForce — “AI Server Demand Sustains Memory Contract Price Increases in 4Q26, While Consumer-Side Pressure Persists, Says TrendForce” (TrendForce 20260930-13258 AI server memory.html; html) — INGESTED, manual upload; published 2026-09-30 (json-ld Article.datePublished); uploaded 2026-10-11 10:35 UTC; analysed as of 2026-10-11; original NOT on this machine — its text is not re-verifiable here; article A-decec490fcdd [D-bac61ba06ddc5cc9]

**Partial articles awaiting a complete document** (1)
- SemiAnalysis — “Anthropic Subscriptions Offer 5x+ More Value Than OpenAI” (published 2026-10-05; 2799 words read) [A-291cb465969d]

**Publishers blocked or degraded** (6)
- Citi: DEGRADED — partial: 1 of 3 sampled article(s) partial (short body (96 words) — treated as a teaser / excerpt); latest scan R-20261011T083033Z-scan: 0 full, 0 preview / partial, 0 unreadable; 2 sampled page(s) su… [+76 chars — full text in the JSON export]
- Bank of America: DEGRADED — metadata problem: 2 of 3 sampled article(s) carry no publication date on the page or the listing — undated articles are never placed in a window (1 of 3 sampled page(s) state a publication date; the l… [+99 chars — full text in the JSON export]
- Morgan Stanley: BLOCKED — robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com — cannot safely proceed: nothing is fetched (handled conservatively, re-tested every check)
- Nomura: DEGRADED — partial: 1 of 3 sampled article(s) partial (the page summarises a fuller report it links to; that report was not read (http://go.nomuranow.com/research/japi/publication/1314426?appname=CONNECTS)); lat… [+75 chars — full text in the JSON export]
- SemiAnalysis: DEGRADED — partial: 1 of 3 sampled article(s) are paywalled previews — only the preview is readable; latest scan R-20261011T083033Z-scan: 1 full, 1 preview / partial, 0 unreadable
- Goldman Sachs: BLOCKED — https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403)

**Known articles requiring an upload** (5)
- Citi (channel DEGRADED) — upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source citi_must_c [--url <article URL>] if you are entitled to the full text — known: https://www.citigroup.com/global/insights/latam-poised-for-take-off — LatAm Poised for Take-Off
- Morgan Stanley (channel BLOCKED) — automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence article --url <article URL> --html <saved page> --as-of <date> --source ms_research — known: unknown — the channel cannot be read
- Nomura (channel DEGRADED) — upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source nomura_connects [--url <article URL>] if you are entitled to the full text — known: https://www.nomuraconnects.com/focused-thinking-posts/central-banks-recalibrating-monetary-policies — Central Banks Recalibrating Monetary Policies
- SemiAnalysis (channel DEGRADED) — upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source semianalysis [--url <article URL>] if you are entitled to the full text — known: https://newsletter.semianalysis.com/p/beijing-will-not-pace-the-frontier — Beijing Will Not Pace the Frontier: China’s Speed-First AI Safety Regime
- Goldman Sachs (channel BLOCKED) — automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence article --url <article URL> --html <saved page> --as-of <date> --source gs_research — known: unknown — the channel cannot be read

**Requiring a metadata or licence check** (1)
- nomura_connects — “Finding Opportunities in an Uncertain World” — the page states no publication date — not placed in any window: VERIFY its date, then analyse it with `article --url <url> --published <verified date>` (https://www.nomuraconnects.com/focused-thinking-posts/opportunity-in-an-uncertain-world)

**Unknown publisher-level coverage gaps** (3)
- Morgan Stanley: coverage UNKNOWN (BLOCKED) — what it published cannot be seen by this system; no new article from it is NOT evidence it published nothing
- Goldman Sachs: coverage UNKNOWN (BLOCKED) — what it published cannot be seen by this system; no new article from it is NOT evidence it published nothing
- citi_must_c: partial discovery — the Must C page embeds its 20 linked series items; older items are not listed there

## Source coverage

| Source | Status | Discovered | In window | Undated | New | Processed | Queued | Inaccessible | Errors / warnings |
|---|---|---|---|---|---|---|---|---|---|
| citi_must_c | OK | 20 | 0 | 0 | 0 | 0 | 0 | 0 | — (the Must C page embeds its 20 linked series items; older items are not listed there) |
| bofa_institutional | OK | 16 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| jpm_tmt | OK | 51 | 1 | 0 | 0 | 0 | 0 | 0 | — |
| ms_research | BLOCKED | 0 | 0 | 0 | 0 | 0 | 0 | 0 | robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com — cannot safely proceed: nothing is fetched (handled conservatively, re-tested every check) (source-health check SH-5cff3eceebf436); standing access limitation recorded in sources.toml — this chann… [+83 chars — full text in the JSON export] |
| nomura_connects | OK | 14 | 1 | 1 | 0 | 0 | 0 | 0 | 1 candidate(s) carry no publication date the source states — counted UNDATED, never placed in a window; listed on the dashboard for date verification (`article --url <url> --published <verified date>`) |
| trendforce | OK | 5 | 2 | 0 | 0 | 0 | 0 | 0 | — |
| semianalysis | OK | 20 | 2 | 0 | 0 | 0 | 0 | 0 | — |
| gs_research | BLOCKED | 0 | 0 | 0 | 0 | 0 | 0 | 0 | https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403) (source-health check SH-1092aa47717295); standing access limitation recorded in sources.toml — this channel refuses the honest research User-Agent; it is reported every run, never bypassed |

## Unresolved caveats

- source ms_research BLOCKED: robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com — cannot safely proceed: nothing is fetched (handled conservatively, re-tested every check) (source-health check SH-5cff3eceebf436)
- source gs_research BLOCKED: https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403) (source-health check SH-1092aa47717295)

## NEW (1) — first recorded this run — new to the registry, not necessarily new to the market

### [RESEARCH NOW] AI server demand keeps DRAM and NAND memory undersupplied, sustaining price increases in 4Q26
- Published 2026-09-30 · first ingested by the registry 2026-10-11 10:38 UTC (new to the registry, not necessarily new to the market) · analysed as of 2026-10-11
- Evidence direction: NEW
- Why this action: Research Now — no dislocation or dated catalyst, but a credible near-term change in a fundamental: do current earnings estimates and market expectations for Semiconductors already reflect contract price change of 10–15% in 4Q26? (an investigation, not a trade)
- What changed:
  - Conventional DRAM contract prices are projected to grow 10-15% QoQ in 4Q26.
  - NAND Flash contract prices are expected to increase 15-20% QoQ in 4Q26.
  - Enterprise SSD bit demand is projected to grow more than 80% YoY in 2026 as CSPs expand AI inference infrastructure.
  - Enterprise SSDs are the only memory category expected to see price growth accelerate, driven by strong CSP demand.
  - Server DRAM is expected to remain undersupplied in 4Q26.
  - Overall NAND Flash contract prices are projected to increase 15-20% QoQ in 4Q26.
  - showing 6 of 10 pieces of evidence from A-decec490fcdd — the rest are in 04 KEY EVIDENCE and the evidence ledger
- Sources:
  - TrendForce — TrendForce — “AI Server Demand Sustains Memory Contract Price Increases in 4Q26, While Consumer-Side Pressure Persists, Says TrendForce” (article date 2026-09-30) — first record of this thesis
- How this evidence arrived: manual upload (D-bac61ba06ddc5cc9 “TrendForce 20260930-13258 AI server memory.html”, uploaded 2026-10-11, A-decec490fcdd)
- Exposure the source names: sector: Semiconductors (positive); TrendForce (UNRESOLVED)
- Next research step: Identify listed DRAM and NAND Flash suppliers and check whether consensus estimates and valuations already capture 4Q26 price increases and the 2027 supply-tightness narrative.
- Audit: `TH-1C1CAEA8AF` v1 · initial assessment — NOW all conditions met — near-term window(s) C-ba0032959d0836: forecast window 2026-10-01..2026-12-31 (4q26); C-5e7bfaa2a93a45: forecast window 2026-10-01..2026-12-31 (4q26); C-af6e5de53922c6: forecast window 2026-10-01..2026-12-31 (4q26); C-c4ea777ac30f35: forecast window 2026-01-01..2026-12-31 (2026); source-named exposure(s): sector: Semiconductors; a near-term fundamental inflection — C-5e7bfaa2a93a45: forecast window 2026-10-01..2026-12-31 (4q26) — the publisher's own data in an industry data report; research question: do current earnings estimates and market expectations for Semiconductors already reflect contract price change of 10–15% in 4Q26?; premise asserted; retrieval FULL; reliability high; no hold — an INVESTIGATION of the thesis, not a trade (valuation NOT_ASSESSED) · card: cards/TH-1C1CAEA8AF.html

## UPGRADED (0) — research action raised on material evidence

_None this run._

## DOWNGRADED (0) — research action lowered — shown in full, never under the upgrades

_None this run._

## CHALLENGED (0) — contradictory evidence, a correction or a timing change arrived

_None this run._

## UNCHANGED BUT MATERIAL (1) — material evidence added; research action unchanged

### [WATCH] Rising component costs threaten 2027 notebook shipments and brand margins
- Published 2026-10-08 · first ingested by the registry 2026-10-11 08:31 UTC · analysed as of 2026-10-11
- Evidence direction: STRONGER
- Why this action: Watch — not yet Research Now: no verified dislocation or catalyst
- What changed:
  - Direct confirmation — new evidence: PC DRAM supply could decline in 2027 as capacity shifts to server applications.
  - Direct confirmation — new evidence: PC OEMs are procuring DRAM aggressively on expectations of tight supply in 2027.
  - Direct confirmation — new evidence: Rising costs and depleted low-cost inventories are weighing on smartphone production, suppressing mobile DRAM bit demand.
  - Direct confirmation — new evidence: NAND Flash suppliers have adopted a more flexible pricing stance on client SSDs, restraining price increases.
  - Direct confirmation — new evidence: Smartphone brands are relying on existing inventories for Q4 production, limiting incremental eMMC/UFS procurement.
  - Direct confirmation — new evidence: NAND Flash wafer prices have reached historical highs that retail channels increasingly cannot absorb.
  - Direct confirmation — new evidence: Despite suppliers seeking broader price increases on AI-driven momentum, OEMs respond with only minimum purchase volumes, narrowing negotiations to price confirmation for small orders.
- Sources:
  - TrendForce — TrendForce — “AI Server Demand Sustains Memory Contract Price Increases in 4Q26, While Consumer-Side Pressure Persists, Says TrendForce” (article date 2026-09-30) — direct confirmation — new evidence
- How this evidence arrived: manual upload (D-bac61ba06ddc5cc9 “TrendForce 20260930-13258 AI server memory.html”, uploaded 2026-10-11, A-decec490fcdd)
- Exposure the source names: sector: Consumer Electronics (negative); sector: Semiconductors (negative); TrendForce (UNRESOLVED)
- Next research step: Map listed PC OEMs and smartphone brands and assess their memory cost exposure and ability to pass through rising component costs into 2027.
- Audit: `TH-4BC0244112` v2 · no change in action (F2_material_evidence 6→7; F6_recognizable_exposures 0 listed · 1 sector→0 listed · 2 sector; F9_premise_in_source conditional→asserted) · card: cards/TH-4BC0244112.html

## ARCHIVED (0) — moved off the active list (SKIP, or no material evidence for a quarter) — still searchable below

_None this run._

## Archive (every thesis)

| Thesis | Action | Evidence | Status | Sector | Ver | Last material update |
|---|---|---|---|---|---|---|
| AI server demand keeps DRAM and NAND memory undersupplied, sustaining price increases in 4Q26 (`TH-1C1CAEA8AF`) | RESEARCH NOW | NEW | ACTIVE | Memory (DRAM, HBM, NAND): supply, pricing, capacity | 1 | 2026-09-30 |
| Low implied correlation makes equity sector and theme selection the key diversifier (`TH-4BC577D53A`) | RESEARCH NOW | NEW | ACTIVE | Market-wide / multi-sector (index level, concentration, correlation, rates) | 1 | 2026-10-02 |
| Rate, political and AI-power forces have pressured utilities as an AI enabler (`TH-588B6416E4`) | RESEARCH NOW | NEW | ACTIVE | Utilities outside AI power | 1 | 2026-10-02 |
| Cost pressures prompt notebook production to reshore from emerging locations back to China (`TH-07643AD5F6`) | WATCH | NEW | ACTIVE | Consumer electronics and devices (PCs, notebooks, phones, displays) | 1 | 2026-10-08 |
| Rising component costs threaten 2027 notebook shipments and brand margins (`TH-4BC0244112`) | WATCH | STRONGER | ACTIVE | Consumer electronics and devices (PCs, notebooks, phones, displays) | 2 | 2026-10-08 |
| Asian tech/AI boom and energy normalization support Singapore, Malaysia region equities (`TH-4FC37DBE69`) | WATCH | NEW | ACTIVE | AI adoption by end users (broad) | 1 | 2026-10-07 |
| Anthropic subscriptions outvalue OpenAI's, signaling differing lab unit economics (`TH-6BDD0881AD`) | WATCH | NEW | ACTIVE | AI model developers and AI platforms / applications | 1 | 2026-10-05 |
| Labs can silently cut subscription value by not raising limits after price cuts (`TH-70E56311B3`) | WATCH | NEW | ACTIVE | AI model developers and AI platforms / applications | 1 | 2026-10-05 |
| Global central banks resume hiking but Nomura sees far fewer hikes than markets price (`TH-C619388BB6`) | WATCH | NEW | REVIEW_NEEDED | Market-wide / multi-sector (index level, concentration, correlation, rates) | 1 | 2026-10-07 |
| China's frontier labs race ahead without safety gating, intensifying competition for US labs (`TH-EBC230CDDD`) | WATCH | NEW | ACTIVE | AI model developers and AI platforms / applications | 1 | 2026-10-08 |
| AI datacenter optical shift drives VCSEL NPO suppliers' unit demand to 2031 (`TH-921772E86C`) | SKIP | NEW | ARCHIVED | Optical interconnects, transceivers and datacenter networking | 1 | 2026-10-08 |

_Verification log: 0 blocked · 0 held · 11 warnings · 1 info. Generated 2026-10-11 11:03 UTC from the registry (ti-engine-2; run R-20261011T110031Z-scan, extract ti-extract-6, review ti-review-4, model claude-opus-4-8)._
