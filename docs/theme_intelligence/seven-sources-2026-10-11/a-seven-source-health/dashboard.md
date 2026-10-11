# What to research this week — run R-20261011T151148Z-scan

_Research attention only — no row is a purchase or sale._

- Scan execution: SUCCEEDED
- Research verification: NOTHING_ANALYSED — no article was analysed in this run
- Window: 2026-10-02 → 2026-10-11 (as of 2026-10-11, mode scan)
- Accessible sources: 5 of 5 (automatic channels)
- Blocked automatic channels: none
- Manual-first sources (health check only; research arrives as uploads): Morgan Stanley [automated access BLOCKED], Goldman Sachs [automated access BLOCKED]
- Articles analyzed: 0 full · 0 partial
- Research Now / Watch / Skip: 0 / 0 / 0 — of the 0 theses this run created or changed (archived in the registry: 1)
- New / upgraded / downgraded / challenged theses: 0 / 0 / 0 / 0 — this run's events; a thesis new this run can also be challenged in it
- Reported figures not yet captured: 0 of 0

## Research source health

**Sources healthy: 2/7 | Degraded: 3 | Blocked: 2 | Errors: 0** — checked 2026-10-11 15:13 UTC; the channels' health, apart from execution and research verification

- **Citi** — DEGRADED: partial: 1 of 3 sampled article(s) partial (short body (96 words) — treated as a teaser / excerpt); latest scan R-20261011T083033Z-scan: 0 full, 0 preview / partial, 0 unreadable; 2 sampled page(s) summarise a report they link to — the scan READS it (linked_reports = "fetch") → UPLOAD_REQUIRED: upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source citi_must_c [--url <article URL>] if you are entitled to the full text
- **Morgan Stanley** — BLOCKED: robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com — cannot safely proceed: nothing is fetched (handled conservatively, re-tested every check) → UPLOAD_REQUIRED: automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence article --url <article URL> --html <saved page> --as-of <date> --source ms_research
- **Nomura** — DEGRADED: partial: 1 of 3 sampled article(s) partial (the page summarises a fuller report it links to; that report was not read (http://go.nomuranow.com/research/japi/publication/1314426?appname=CONNECTS)); latest scan R-20261011T083033Z-scan: 1 full, 0 preview / partial, 0 unreadable → UPLOAD_REQUIRED: upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source nomura_connects [--url <article URL>] if you are entitled to the full text
- **SemiAnalysis** — DEGRADED: partial: 1 of 3 sampled article(s) are paywalled previews — only the preview is readable; latest scan R-20261011T083033Z-scan: 1 full, 1 preview / partial, 0 unreadable → UPLOAD_REQUIRED: upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source semianalysis [--url <article URL>] if you are entitled to the full text
- **Goldman Sachs** — BLOCKED: https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403) → UPLOAD_REQUIRED: automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence article --url <article URL> --html <saved page> --as-of <date> --source gs_research

| Publisher | Health | Freshness | Last checked | Last discovery OK | Last full-text OK | Last verified publication date | Discovered / listing-dated in window | Consecutive failed | Manual upload |
|---|---|---|---|---|---|---|---|---|---|
| Citi | DEGRADED | QUIET | 2026-10-11T15:11 | 2026-10-11 | 2026-10-11 | 2026-09-14 | 20 / 0 | 4 | yes |
| J.P. Morgan Private Bank | HEALTHY | FRESH | 2026-10-11T15:12 | 2026-10-11 | 2026-10-11 | 2026-10-02 | 51 / 1 | 0 | — |
| Morgan Stanley | BLOCKED | UNKNOWN | 2026-10-11T08:30 | — | — | — | 0 / 0 | 1 | yes |
| Nomura | DEGRADED | FRESH | 2026-10-11T15:12 | 2026-10-11 | 2026-10-11 | 2026-10-07 | 14 / 0 | 4 | yes |
| TrendForce | HEALTHY | FRESH | 2026-10-11T15:13 | 2026-10-11 | 2026-10-11 | 2026-10-08 | 5 / 2 | 0 | — |
| SemiAnalysis | DEGRADED | FRESH | 2026-10-11T15:13 | 2026-10-11 | 2026-10-11 | 2026-10-08 | 20 / 2 | 4 | yes |
| Goldman Sachs | BLOCKED | UNKNOWN | 2026-10-11T08:31 | — | — | — | 0 / 0 | 1 | yes |

## Research intake / manual action

**0 analysed automatically · 0 imported manually · 1 partial awaiting a complete document · 5 publisher(s) blocked or degraded · 5 needing an upload · 1 needing a metadata or licence check · 3 coverage gap(s)** — ingestion coverage over 1 run(s), apart from source health and research verification

**Coverage by publisher (the configured channels)** (7)
- Citi [automatic; access DEGRADED] — 0 article(s) analysed automatically, 0 supplied — PARTIAL automated coverage — see source health
- J.P. Morgan Private Bank [automatic; access HEALTHY] — 0 article(s) analysed automatically, 0 supplied — automated coverage
- Morgan Stanley [manual-first; access BLOCKED] — 0 article(s) analysed automatically, 0 supplied — MANUAL-FIRST — nothing supplied this week: its research this week is MISSING, not absent
- Nomura [automatic; access DEGRADED] — 0 article(s) analysed automatically, 0 supplied — PARTIAL automated coverage — see source health
- TrendForce [automatic; access HEALTHY] — 0 article(s) analysed automatically, 0 supplied — automated coverage
- SemiAnalysis [automatic; access DEGRADED] — 0 article(s) analysed automatically, 0 supplied — PARTIAL automated coverage — see source health
- Goldman Sachs [manual-first; access BLOCKED] — 0 article(s) analysed automatically, 0 supplied — MANUAL-FIRST — nothing supplied this week: its research this week is MISSING, not absent

**Articles automatically analysed** (0)
- none

**Articles manually imported** (0)
- none

**Partial articles awaiting a complete document** (1)
- SemiAnalysis — “Anthropic Subscriptions Offer 5x+ More Value Than OpenAI” (published 2026-10-05; 2799 words read) [A-291cb465969d]

**Publishers blocked or degraded** (5)
- Citi: DEGRADED — partial: 1 of 3 sampled article(s) partial (short body (96 words) — treated as a teaser / excerpt); latest scan R-20261011T083033Z-scan: 0 full, 0 preview / partial, 0 unreadable; 2 sampled page(s) su… [+76 chars — full text in the JSON export]
- Morgan Stanley: BLOCKED — robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com — cannot safely proceed: nothing is fetched (handled conservatively, re-tested every check)
- Nomura: DEGRADED — partial: 1 of 3 sampled article(s) partial (the page summarises a fuller report it links to; that report was not read (http://go.nomuranow.com/research/japi/publication/1314426?appname=CONNECTS)); lat… [+75 chars — full text in the JSON export]
- SemiAnalysis: DEGRADED — partial: 1 of 3 sampled article(s) are paywalled previews — only the preview is readable; latest scan R-20261011T083033Z-scan: 1 full, 1 preview / partial, 0 unreadable
- Goldman Sachs: BLOCKED — https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403)

**Known articles requiring an upload** (5)
- Citi (channel DEGRADED) — upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source citi_must_c [--url <article URL>] if you are entitled to the full text — known: https://www.citigroup.com/global/insights/money-the-evolution-to-digital — Money: The Evolution to Digital
- Morgan Stanley (channel BLOCKED) — automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence article --url <article URL> --html <saved page> --as-of <date> --source ms_research — known: unknown — the channel cannot be read
- Nomura (channel DEGRADED) — upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source nomura_connects [--url <article URL>] if you are entitled to the full text — known: https://www.nomuraconnects.com/focused-thinking-posts/beyond-the-headlines-ai-has-added-jobs-in-asia-so-far — Beyond the Headlines: AI Has Added Jobs in Asia – So Far
- SemiAnalysis (channel DEGRADED) — upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source semianalysis [--url <article URL>] if you are entitled to the full text — known: https://newsletter.semianalysis.com/p/are-open-models-catching-up — Are Open Models Catching Up?
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
| jpm_tmt | OK | 51 | 1 | 0 | 0 | 0 | 0 | 0 | — |
| ms_research | MANUAL_FIRST | 0 | 0 | 0 | 0 | 0 | 0 | 0 | automated access: BLOCKED — robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com — cannot safely proceed: nothing is fetched (handled cons |
| nomura_connects | OK | 14 | 1 | 1 | 0 | 0 | 0 | 0 | 1 candidate(s) carry no publication date the source states — counted UNDATED, never placed in a window; listed on the dashboard for date verification (`article --url <url> --published <verified date>`) |
| trendforce | OK | 5 | 2 | 0 | 0 | 0 | 0 | 0 | — |
| semianalysis | OK | 20 | 2 | 0 | 0 | 0 | 0 | 0 | — |
| gs_research | MANUAL_FIRST | 0 | 0 | 0 | 0 | 0 | 0 | 0 | automated access: BLOCKED — https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403) |

## NEW (0) — first recorded this run — new to the registry, not necessarily new to the market

_None this run._

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
| Low implied correlation makes equity sector and theme selection the key diversifier (`TH-4BC577D53A`) | RESEARCH NOW | NEW | ACTIVE | Market-wide / multi-sector (index level, concentration, correlation, rates) | 1 | 2026-10-02 |
| Rate, political and AI-power forces have pressured utilities as an AI enabler (`TH-588B6416E4`) | RESEARCH NOW | NEW | ACTIVE | Utilities outside AI power | 1 | 2026-10-02 |
| Cost pressures prompt notebook production to reshore from emerging locations back to China (`TH-07643AD5F6`) | WATCH | NEW | ACTIVE | Consumer electronics and devices (PCs, notebooks, phones, displays) | 1 | 2026-10-08 |
| Rising component costs threaten 2027 notebook shipments and brand margins (`TH-4BC0244112`) | WATCH | NEW | ACTIVE | Consumer electronics and devices (PCs, notebooks, phones, displays) | 1 | 2026-10-08 |
| Asian tech/AI boom and energy normalization support Singapore, Malaysia region equities (`TH-4FC37DBE69`) | WATCH | NEW | ACTIVE | AI adoption by end users (broad) | 1 | 2026-10-07 |
| Anthropic subscriptions outvalue OpenAI's, signaling differing lab unit economics (`TH-6BDD0881AD`) | WATCH | NEW | ACTIVE | AI model developers and AI platforms / applications | 1 | 2026-10-05 |
| Labs can silently cut subscription value by not raising limits after price cuts (`TH-70E56311B3`) | WATCH | NEW | ACTIVE | AI model developers and AI platforms / applications | 1 | 2026-10-05 |
| Global central banks resume hiking but Nomura sees far fewer hikes than markets price (`TH-C619388BB6`) | WATCH | NEW | REVIEW_NEEDED | Market-wide / multi-sector (index level, concentration, correlation, rates) | 1 | 2026-10-07 |
| China's frontier labs race ahead without safety gating, intensifying competition for US labs (`TH-EBC230CDDD`) | WATCH | NEW | ACTIVE | AI model developers and AI platforms / applications | 1 | 2026-10-08 |
| AI datacenter optical shift drives VCSEL NPO suppliers' unit demand to 2031 (`TH-921772E86C`) | SKIP | NEW | ARCHIVED | Optical interconnects, transceivers and datacenter networking | 1 | 2026-10-08 |

_Verification log: 0 blocked · 0 held · 0 warnings · 0 info. Generated 2026-10-11 15:15 UTC from the registry (ti-engine-2; run R-20261011T151148Z-scan, extract ti-extract-6, review ti-review-4, model claude-opus-4-8)._
