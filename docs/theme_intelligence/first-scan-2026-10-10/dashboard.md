# What to research this week — run R-20261010T114919Z-scan (SUCCEEDED)

_Research attention only — no row is a purchase or sale._

- Window: 2026-10-01 → 2026-10-10 (as of 2026-10-10, mode scan)
- Sources checked: 8 of 8; failed: 0 new + 2 standing (gs_research, ms_research)
- Articles read: 3 (partial 0, blocked 0); queued by the budget cap, not yet read: 3
- Themes created / updated: 3 / 0; attribution-only contributions: 0
- Active RESEARCH NOW / WATCH / SKIP: 0 / 3 / 0; archived 0

## Source coverage

| Source | Status | Discovered | In window | Undated | New | Processed | Queued | Inaccessible | Errors / warnings |
|---|---|---|---|---|---|---|---|---|---|
| citi_must_c | OK | 20 | 0 | 0 | 0 | 0 | 0 | 0 | — (the Must C page embeds its 20 linked series items; older items are not listed there) |
| bofa_institutional | OK | 16 | 0 | 12 | 0 | 0 | 0 | 0 | 12 candidate(s) carry no publication date the source states — counted UNDATED, never placed in a window (analyse one on demand with `article --url`) |
| jpm_tmt | OK | 51 | 1 | 0 | 1 | 0 | 1 | 0 | — |
| ms_research | BLOCKED | 0 | 0 | 0 | 0 | 0 | 0 | 0 | https://www.morganstanley.com/what-we-do/research: robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com; standing access limitation recorded in sources.toml — this channel refuses the honest research User-Agent; it is reported every run, never bypass… [+2 chars — full text in the JSON export] |
| nomura_connects | OK | 14 | 1 | 1 | 1 | 0 | 1 | 0 | 1 candidate(s) carry no publication date the source states — counted UNDATED, never placed in a window (analyse one on demand with `article --url`) |
| trendforce | OK | 5 | 2 | 0 | 2 | 2 | 0 | 0 | — |
| semianalysis | OK | 20 | 2 | 0 | 2 | 1 | 1 | 0 | — |
| gs_research | BLOCKED | 0 | 0 | 0 | 0 | 0 | 0 | 0 | https://www.goldmansachs.com/insights/goldman-sachs-research/: HTTP 403; standing access limitation recorded in sources.toml — this channel refuses the honest research User-Agent; it is reported every run, never bypassed |

## Unresolved caveats

- NUMBER_NOT_IN_SPAN C-c3a65deab8471d: c1: number check failed: value=650000000.0 value_text='650 million units' vs quote — quote 'boost VCSEL sales to 650 million units by 2031'
- source ms_research BLOCKED: https://www.morganstanley.com/what-we-do/research: robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched from www.morganstanley.com
- source gs_research BLOCKED: https://www.goldmansachs.com/insights/goldman-sachs-research/: HTTP 403

## NEW (3) — first recorded this run (new to the registry — novelty_unverified)

### [WATCH] Rising memory and CPU costs squeeze notebook brands' margins and shipments in 2027 (`TH-4BC0244112` v1)
- Evidence direction: NEW
- Priority: new → WATCH — initial assessment — WATCH (RESEARCH NOW unmet: no source-named listed company exposure; premise is conditional in the source)
- What changed this run:
  - [novelty_unverified] If DRAM and CPU prices stay elevated and are passed to consumers, the full-year shipment decline could reach the high-single-digit range. ⟨cited figures: forecast⟩
  - [novelty_unverified] For a US$900 MSRP mainstream notebook, CPU, DRAM and SSD made up about 68% of BOM cost in 3Q26. ⟨cited figures: approximate⟩
  - [novelty_unverified] Global notebook shipments are projected to decline by a low-single-digit percentage in 2027. ⟨cited figures: forecast⟩
  - [novelty_unverified] DRAM supply is likely to stay tight in 2027 as AI servers absorb capacity, with PC DRAM facing limited supply growth.
  - [novelty_unverified] The primary 2027 notebook market risk is expected to shift from supply constraints to rising costs hurting demand.
  - [novelty_unverified] Brands face a trade-off: raising prices weakens demand, absorbing costs squeezes gross margins.
- Sources:
  - TrendForce — author UNKNOWN — “Rising Costs Threaten Notebook Demand in 2027, Raising Risks of Shipment Declines and Price Increases, Says TrendForce” (date UNKNOWN) [novelty_unverified]
- Named by the source: no company named
- Sectors: Consumer Electronics, Technology Hardware
- Next action: Check listed notebook OEM/ODM guidance and consensus margin/shipment estimates for 2027 against TrendForce's low- vs high-single-digit decline scenarios.
- Last material update: 2026-10-10 · card: cards/TH-4BC0244112.html

### [WATCH] AI datacenter shift to VCSEL NPO optical interconnects lifts named VCSEL suppliers (`TH-921772E86C` v1)
- Evidence direction: NEW
- Priority: new → WATCH — initial assessment — WATCH (RESEARCH NOW unmet: verification hold)
- What changed this run:
  - [novelty_unverified] VCSEL sales are projected to grow at a 38% CAGR from 2025 to 2031. ⟨cited figures: forecast⟩
  - [novelty_unverified] Copper signal attenuation is expected to accelerate the transition to optical interconnect technologies including VCSEL NPO and Micro LED CPO.
  - [novelty_unverified] Several VCSEL NPO solutions are expected to launch between 2027 and 2028.
  - [novelty_unverified] Six major suppliers are investing heavily in VCSEL NPO R&D.
  - [novelty_unverified] Coherent, Broadcom, ams OSRAM and HiSilicon use mature 850nm VCSELs with photodiodes to achieve aggregate bandwidth up to 3.2 Tbps.
  - [novelty_unverified] Lumentum and Furukawa Electric adopted higher-cost 1,060nm VCSEL solutions; Coherent plans to adopt this approach.
  - [novelty_unverified] showing 6 of 9 pieces of evidence from A-5576af910bf8 — the rest are in 04 KEY EVIDENCE and the evidence ledger
- Sources:
  - TrendForce — author UNKNOWN — “Six Leading Suppliers Bet on VCSEL NPO; VCSEL Demand Projected to Reach 650 Million Units by 2031, Says TrendForce” (date UNKNOWN) [novelty_unverified]
- Named by the source: Lumentum (LITE); Furukawa Electric (UNRESOLVED); Coherent (COHR); Broadcom (AVGO); ams OSRAM (UNRESOLVED); HiSilicon (UNRESOLVED)
- Sectors: Semiconductors, Technology Hardware
- Next action: Assess each named supplier's current VCSEL/optical revenue exposure and capacity plans to gauge how material a 38% VCSEL CAGR through 2031 could be to earnings.
- Last material update: 2026-10-10 · card: cards/TH-921772E86C.html

### [WATCH] China's unconstrained AI release and price war pressures Western frontier lab economics (`TH-EBC230CDDD` v1)
- Evidence direction: NEW
- Priority: new → WATCH — initial assessment — WATCH (RESEARCH NOW unmet: no source-named listed company exposure; verification hold)
- What changed this run:
  - [novelty_unverified] Quarterly releases rose from 3 in Q1 2023 to 101 in Q3 2025
  - [novelty_unverified] The dataset includes 857 counted model releases
  - [novelty_unverified] Open-weight releases make up more than half of every quarter since mid-2023
  - [novelty_unverified] Anthropic's economics are being squeezed by cheap open-weight rivals especially in China
  - [novelty_unverified] China's frontier labs are in a release and price war
- Sources:
  - SemiAnalysis — Mark Chen; Doug; Dylan Patel — “Beijing Will Not Pace the Frontier: China’s Speed-First AI Safety Regime” (2026-10-08) [novelty_unverified]
- Named by the source: Alibaba (UNRESOLVED); Anthropic [private company]; DeepSeek [private company]; Zhipu Z.ai [private company]
- Sectors: Technology, Artificial Intelligence
- Next action: Investigate whether cheap Chinese open-weight model availability is measurably compressing API pricing or share for publicly traded or investable AI model developers.
- Last material update: 2026-10-08 · card: cards/TH-EBC230CDDD.html

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
| China's unconstrained AI release and price war pressures Western frontier lab economics (`TH-EBC230CDDD`) | WATCH | NEW | ACTIVE | AI model developers and AI platforms / applications | 1 | 2026-10-08 |

_Verification log: 8 blocked · 0 held · 20 warnings · 1 info. Generated 2026-10-10 12:27 UTC from the registry (ti-engine-1; run R-20261010T114919Z-scan, extract ti-extract-5, review ti-review-2, model claude-opus-4-8)._
