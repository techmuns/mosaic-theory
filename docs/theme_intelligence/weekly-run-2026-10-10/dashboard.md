# What to research this week — run R-20261010T120521Z-scan (SUCCEEDED)

_Research attention only — no row is a purchase or sale._

- Window: 2026-10-01 → 2026-10-10 (as of 2026-10-10, mode scan)
- Sources checked: 8 of 8; failed: 0 new + 2 standing (gs_research, ms_research)
- Articles read: 3 (partial 1, blocked 0); queued by the budget cap, not yet read: 0
- Themes created / updated: 1 / 0; attribution-only contributions: 0
- Active RESEARCH NOW / WATCH / SKIP: 0 / 4 / 0; archived 0

## Source coverage

| Source | Status | Discovered | In window | Undated | New | Processed | Queued | Inaccessible | Errors / warnings |
|---|---|---|---|---|---|---|---|---|---|
| citi_must_c | OK | 20 | 0 | 0 | 0 | 0 | 0 | 0 | — (the Must C page embeds its 20 linked series items; older items are not listed there) |
| bofa_institutional | OK | 16 | 0 | 12 | 0 | 0 | 0 | 0 | 12 candidate(s) carry no publication date the source states — counted UNDATED, never placed in a window (analyse one on demand with `article --url`) |
| jpm_tmt | OK | 51 | 1 | 0 | 1 | 1 | 0 | 0 | — |
| ms_research | BLOCKED | 0 | 0 | 0 | 0 | 0 | 0 | 0 | https://www.morganstanley.com/what-we-do/research: robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com; standing access limitation recorded in sources.toml — this channel refuses the honest research User-Agent; it is reported every run, never bypass… [+2 chars — full text in the JSON export] |
| nomura_connects | OK | 14 | 1 | 1 | 1 | 1 | 0 | 0 | 1 candidate(s) carry no publication date the source states — counted UNDATED, never placed in a window (analyse one on demand with `article --url`) |
| trendforce | OK | 5 | 2 | 0 | 0 | 0 | 0 | 0 | — |
| semianalysis | OK | 20 | 2 | 0 | 1 | 1 | 0 | 0 | — |
| gs_research | BLOCKED | 0 | 0 | 0 | 0 | 0 | 0 | 0 | https://www.goldmansachs.com/insights/goldman-sachs-research/: HTTP 403; standing access limitation recorded in sources.toml — this channel refuses the honest research User-Agent; it is reported every run, never bypassed |

## Unresolved caveats

- NUMBER_NOT_IN_SPAN C-5c67905341e0f8: c6: number check failed: value=2.0 value_text='Two more hikes' vs quote — quote 'Two more hikes by the European Central Bank in December 2026 and March 2027, com'
- NUMBER_NOT_IN_SPAN C-d2d64abab25d58: c17: number check failed: value=2.0 value_text='two hikes' vs quote — quote 'In India , a faster rise in food and oil prices alongside firming core inflation'
- NUMBER_NOT_IN_SPAN C-5fe7199559831c: c9: number check failed: value=-10.0 value_text='around –10%' vs quote — quote 'S&P 500 Utilities start out strong, climbing to a peak above 10% in July before '
- NUMBER_NOT_IN_SPAN C-4a8a059631e44d: c9: number check failed: value=2.0 value_text='Two more hikes' vs quote — quote 'Two more hikes from the Bank of Japan against a market consensus of four or more'
- NUMBER_NOT_IN_SPAN C-fdbde227bd0846: c7: number check failed: value=-50.0 value_text='halving' vs quote — quote 'halving the API-equivalent value for the $200 plan and introducing a new $500 ti'
- PARTIAL_RETRIEVAL A-291cb465969d: only part of the article was retrieved — no claim of full-text verification is made
- NUMBER_NOT_IN_SPAN C-93592dd1df25fd: c11: number check failed: value=0.0 value_text='None' vs quote — quote 'None for the Bank of England and Bank of Canada against market pricing of around'
- NUMBER_NOT_IN_SPAN C-b3df96d94bcdeb: c3: number check failed: value=1.0 value_text='A hike' vs quote — quote 'A hike in December by the US Federal Reserve followed by an extended hold throug'
- NUMBER_NOT_IN_SPAN C-030bbe0d83c30c: c17: number check failed: value=None value_text='~20% ... ~50%' vs quote — quote 'the ~20% token increase for Max plans and ~50% increase for the Pro plan weren’t'
- UNSUPPORTED_ENTITY J.P. Morgan Private Bank: 'J.P. Morgan Private Bank' does not occur in the article text — dropped (no unnamed entity may be source-mentioned)
- NUMBER_NOT_IN_SPAN C-4af3d4cd2e5b48: c8: number check failed: value=7.0 value_text='seven' vs quote — quote 'equities have been more focused on seven straight quarters of corporate earnings'
- source ms_research BLOCKED: https://www.morganstanley.com/what-we-do/research: robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com
- source gs_research BLOCKED: https://www.goldmansachs.com/insights/goldman-sachs-research/: HTTP 403

## NEW (1) — first recorded this run (new to the registry — novelty_unverified)

### [WATCH] Rising rates and data-center moratoriums are driving utilities sector underperformance (`TH-98FD8D046C` v1)
- Evidence direction: NEW
- Priority: new → WATCH — initial assessment — WATCH (RESEARCH NOW unmet: no source-named listed company exposure; verification hold)
- What changed this run:
  - [novelty_unverified] Utilities price and P/E declined after the New York data center moratorium and dropped sharper after Texas data center restrictions in early August.
  - [novelty_unverified] State governments have put moratoriums on data-center build-out, weighing on utilities.
  - [novelty_unverified] Higher Treasury yields compete with utilities' dividends, weighing on the sector.
- Sources:
  - J.P. Morgan Private Bank — Kriti Gupta — “A calm index, a restless market” (2026-10-02) [novelty_unverified]
- Named by the source: S&P 500 Utilities [index]
- Sectors: Utilities
- Next action: Identify which listed utilities have greatest data-center load exposure and track state-level moratorium developments and their earnings guidance.
- Last material update: 2026-10-02 · card: cards/TH-98FD8D046C.html

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
| Rising memory and CPU costs squeeze notebook brands' margins and shipments in 2027 (`TH-4BC0244112`) | WATCH | NEW | ACTIVE | Consumer electronics and devices (PCs, notebooks, phones, displays) | 1 | 2026-10-10 |
| AI datacenter shift to VCSEL NPO optical interconnects lifts named VCSEL suppliers (`TH-921772E86C`) | WATCH | NEW | ACTIVE | Optical interconnects, transceivers and datacenter networking | 1 | 2026-10-10 |
| Rising rates and data-center moratoriums are driving utilities sector underperformance (`TH-98FD8D046C`) | WATCH | NEW | ACTIVE | Power generation, grid and interconnection for AI datacenters | 1 | 2026-10-02 |
| China's unconstrained AI release and price war pressures Western frontier lab economics (`TH-EBC230CDDD`) | WATCH | NEW | ACTIVE | AI model developers and AI platforms / applications | 1 | 2026-10-08 |

_Verification log: 12 blocked · 0 held · 8 warnings · 2 info. Generated 2026-10-10 12:27 UTC from the registry (ti-engine-1; run R-20261010T120521Z-scan, extract ti-extract-5, review ti-review-2, model claude-opus-4-8)._
