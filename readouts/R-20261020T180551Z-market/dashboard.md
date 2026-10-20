# What to research this week — run R-20261020T180551Z-market

_Research attention only — no row is a purchase or sale._

- Scan execution: SUCCEEDED
- Research verification: NOTHING_ANALYSED — no article was analysed in this run
- Window: 2026-10-20 → 2026-10-20 (as of 2026-10-20, mode market)
- Sources: none read — market context for stored theses (prices and filings as of the date; display only, no model call)
- Articles analyzed: 0 full · 0 partial
- Research Now / Watch / Skip: 0 / 0 / 0 — of the 0 theses the week's runs created or changed (archived in the registry: 0)
- New / upgraded / downgraded / challenged theses: 0 / 0 / 0 / 0 — the week's events; a thesis new this week can also be challenged in it
- Reported figures not yet captured: 0 of 0

## Research source health

**Sources healthy: 3/6 | Degraded: 1 | Blocked: 2 | Errors: 0** — checked 2026-10-20 18:05 UTC; the channels' health, apart from execution and research verification

- **Change — SemiAnalysis** [NEW_FAILURE]: first check of this channel
- **Morgan Stanley** — BLOCKED: robots.txt unreachable (ReadTimeout) — FAIL CLOSED, nothing fetched from www.morganstanley.com — cannot safely proceed: nothing is fetched (handled conservatively, re-tested every check) → UPLOAD_REQUIRED: automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source ms_research [--url <article URL>]
- **SemiAnalysis** — DEGRADED: partial: 3 of 3 sampled article(s) are paywalled previews — only the preview is readable → none to supply — paid posts are read as their free preview by the operator's decision (paywalled_posts = "preview_only")
- **Goldman Sachs** — BLOCKED: https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403) → UPLOAD_REQUIRED: automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source gs_research [--url <article URL>]

| Publisher | Health | Freshness | Last checked | Last discovery OK | Last full-text OK | Last verified publication date | Discovered / listing-dated in window | Consecutive failed | Manual upload |
|---|---|---|---|---|---|---|---|---|---|
| Citi | HEALTHY | QUIET | 2026-10-20T18:02 | 2026-10-20 | — | 2026-09-14 | 20 / 0 | 0 | — |
| J.P. Morgan Private Bank | HEALTHY | FRESH | 2026-10-20T18:03 | 2026-10-20 | 2026-10-20 | 2026-10-16 | 52 / 1 | 0 | — |
| Morgan Stanley | BLOCKED | UNKNOWN | 2026-10-20T18:03 | — | — | — | 0 / 0 | 1 | yes |
| TrendForce | HEALTHY | FRESH | 2026-10-20T18:04 | 2026-10-20 | 2026-10-20 | 2026-10-19 | 5 / 4 | 0 | — |
| SemiAnalysis | DEGRADED | FRESH | 2026-10-20T18:04 | 2026-10-20 | — | 2026-10-19 | 20 / 2 | 1 | — |
| Goldman Sachs | BLOCKED | UNKNOWN | 2026-10-20T18:05 | — | — | — | 0 / 0 | 1 | yes |

## Research intake / manual action

**0 analysed automatically · 0 imported manually · 0 partial awaiting a complete document · 3 publisher(s) blocked or degraded · 2 needing an upload · 0 needing a metadata, licence or visual check · 2 coverage gap(s)** — ingestion coverage over 1 run(s), apart from source health and research verification

**Coverage by publisher (the configured channels)** (6)
- Citi [automatic; access HEALTHY] — 0 article(s) analysed automatically, 0 supplied — automated coverage
- J.P. Morgan Private Bank [automatic; access HEALTHY] — 0 article(s) analysed automatically, 0 supplied — automated coverage
- Morgan Stanley [manual-first; access BLOCKED] — 0 article(s) analysed automatically, 0 supplied — MANUAL-FIRST — nothing supplied this week: its research this week is MISSING, not absent
- TrendForce [automatic; access HEALTHY] — 0 article(s) analysed automatically, 0 supplied — automated coverage
- SemiAnalysis [automatic; access DEGRADED] — 0 article(s) analysed automatically, 0 supplied — PARTIAL automated coverage — see source health
- Goldman Sachs [manual-first; access BLOCKED] — 0 article(s) analysed automatically, 0 supplied — MANUAL-FIRST — nothing supplied this week: its research this week is MISSING, not absent

**Articles automatically analysed** (0)
- none

**Articles manually imported** (0)
- none

**Partial articles awaiting a complete document** (0)
- none

**Publishers blocked or degraded** (3)
- Morgan Stanley: BLOCKED — robots.txt unreachable (ReadTimeout) — FAIL CLOSED, nothing fetched from www.morganstanley.com — cannot safely proceed: nothing is fetched (handled conservatively, re-tested every check)
- SemiAnalysis: DEGRADED — partial: 3 of 3 sampled article(s) are paywalled previews — only the preview is readable
- Goldman Sachs: BLOCKED — https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403)

**Known articles requiring an upload** (2)
- Morgan Stanley (channel BLOCKED) — automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source ms_research [--url <article URL>] — known: unknown — the channel cannot be read
- Goldman Sachs (channel BLOCKED) — automatic access is refused or unsafe — never bypassed; re-tested every check. Meanwhile upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence ingest-file --path <report.pdf or saved page> --source gs_research [--url <article URL>] — known: unknown — the channel cannot be read

**Requiring a metadata, licence or visual check** (0)
- none

**Unknown publisher-level coverage gaps** (2)
- Morgan Stanley: coverage UNKNOWN (BLOCKED) — what it published cannot be seen by this system; no new article from it is NOT evidence it published nothing
- Goldman Sachs: coverage UNKNOWN (BLOCKED) — what it published cannot be seen by this system; no new article from it is NOT evidence it published nothing

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

_Verification log: 0 blocked · 0 held · 0 warnings · 0 info. Generated 2026-10-20 18:05 UTC from the registry (ti-engine-5; run R-20261020T180551Z-market, extract ti-extract-6, review ti-review-4, model claude-opus-4-8)._
