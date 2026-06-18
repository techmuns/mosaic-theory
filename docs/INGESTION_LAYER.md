# Ingestion Layer — Build Spec (Phase 1 foundation)

**Version:** v0.2 · **Status:** build spec, not yet built · **Owner:** Munshot Research · **For:** Claude Code
**Implements** the ingestion contract in `FUNNEL_SCREENS.md` v0.2 (freshness · declared completeness · stable entity key · point-in-time stamping).

**Changelog (v0.2):** **breadth data and execution data are now separated.** The wide universe scan runs on a free/cheap **EOD source** (not IBKR), because IBKR market data is per-exchange and a fund is billed at *professional* rates — paying global-professional fees just to *scan* is wasteful. IBKR is rescoped to **execution + the handful of names you actually trade or watch live.** This decouples breadth-data cost from universe size (near-zero) and confines IBKR fees to traded names.

> **First principles — one line.** This layer exists to make a gate's **PASS / FAIL / UNKNOWN reliable**. Funnel reliability is bounded *here*: a stale price, a missed filing, a duplicated headline, or a mis-resolved ticker yields confident garbage no matter how good the gate logic is.

## Scope

**In:** entity resolver · EOD market-data client (breadth) · IBKR client (execution + scoped real-time) · EDGAR client (US fundamentals) · news/event client (fenced) · store · orchestrator.
**Out (do not build here):** gate logic (the screens); CIQ automation (no feed — depth-only, manual); a Koyfin scraper (UI/ToS — manual at depth); non-US fundamental parsers (later); depth/harness/portfolio/execution logic.
**Reusability vs US-first:** entity master, EOD client, IBKR client, store, and news client are **geography-agnostic, built once**; only the EDGAR client is US-specific. Build the layer in full regardless of how US-first lands.

## The two data tiers (the v0.2 split)

- **Breadth tier — EOD, whole universe, free/cheap.** Daily prices + volume for every gated name, from a free global EOD source (**Stooq**) or a cheap reliable one (**Tiingo, ~$10/mo**) if you want better-than-free quality. Feeds every price-derived gate (drawdown, returns, relative strength, 52-week high, ADV/turnover). Reliability: decent, but gaps and no SLA → **re-verified at depth against IBKR for shortlist names only.**
- **Execution / scoped tier — IBKR, real-time, traded names only.** Live prices for names you hold or watch; implied vol/options for the shortlist (the stress attached-signal, at depth); the scanner for big-mover event triggers. **Not** the breadth price feed.

## Components

### 1. Entity master & resolver — build first (the join key, and the #1 risk)
- Canonical entity with a stable internal key, mapping `internal_id ↔ {IBKR conid, ticker+MIC, EOD-source symbol, EDGAR CIK (US), CIQ id (manual), Koyfin id (manual)}`.
- **Universe seeded from IBKR's tradeable ex-China list** within the cap/liquidity band (tradeability is still IBKR-defined — use IBKR *reference/contract* data, which is cheap, not its market data). Enriched with EDGAR CIK for US names; mapped to the EOD-source symbol for breadth price/volume.
- Coverage asymmetry baked in: US → CIK→fundamentals link; non-US → identity + EOD price only, **no free fundamentals → UNKNOWN on fundamental gates.**
- **#1 RISK — mis-resolution.** Ticker reuse across exchanges, dual listings, ADR vs ordinary, ticker changes, many-to-one CIK↔ticker, **and now EOD-source symbology quirks (e.g. Stooq's `.US`/`.UK` suffixes)** all risk joining the *wrong company's* data — the worst failure in the system. Resolution must be deterministic, hand-verified against known names, and **fail LOUD (UNKNOWN) when ambiguous** — never guess.

### 2. EOD market-data client (breadth) — global, free/cheap
- Daily OHLCV for the gated universe from Stooq (free) or Tiingo (~$10/mo).
- Derives: drawdown from 52-week high, trailing returns, relative-to-sector return, 90D ADV (shares + USD), turnover, volume spike.
- *Gotchas:* symbology mapping to the entity key (above); occasional gaps/errors (no SLA) → flag staleness, and re-verify shortlist names against IBKR at depth; currency in listing terms → normalise to USD for the size gate (**FX policy is an open decision — flag it**).

### 3. IBKR client (execution + scoped real-time)
Pulls (*verify exact endpoints, tick types, scan codes, pacing at build*):
- contract/reference resolution → `conid` (feeds the resolver + the tradeability gate — this part runs early, for the universe seed)
- live prices for traded/watched names (market data, scoped — not the universe)
- implied/historical vol + options chain for the **shortlist only** → the stress attached-signal at depth (ATM-straddle implied-move stays at depth per your framework)
- market scanner → big-mover **event triggers** for Screen 2 (coarse)
- *Gotchas:* market-data is **professional-rate and per-exchange** (the reason it's scoped, not breadth); pacing limits (queue/throttle); $500 min equity beyond subscription costs.

### 4. EDGAR client — US only; fundamentals + filings + insider
- **XBRL:** `companyfacts` (per issuer) + `frames` (one concept across all filers per period — the breadth tool) → valuation inputs (with EOD price) + the non-distress gate (FCF/op-income sign, leverage).
- **Full-text search (efts):** de-rating event detection (guidance-cut 8-Ks); the **Screen-3 relational trick** (who names the hot beneficiary as customer/supplier).
- **Submissions:** recent filings (8-K detection, report dates for the earnings-gap signal).
- **Form 4:** raw US insider transactions as an attached-signal source; **classification deferred to depth** (your CIQ notes own the direction-flip — do not re-implement loosely).
- *Gotchas:* fair-access (declared `User-Agent`, ~10 req/s — *verify*; throttle + cache); XBRL tag inconsistency; **restated vs as-reported → store as-reported with report date** (point-in-time); unit/scale.

### 5. News/event client — fenced to events and context only
- Web search + public press → **typed events**: downgrade, guidance-cut, contract/partnership (Screen 3), threat narrative (depth context). Dedup (same story across outlets = one event) + timestamp.
- **THE FENCE (enforce in schema):** typed events and context flags **only** — never a count, intensity, score, or gate input. The unreliable tier → events are pointers for depth, not gate inputs.

### 6. Store — the contract made physical
- Holds: entity master · time-series (EOD price/volume; scoped IBKR vol) · point-in-time fundamental snapshots · filing/event log.
- **Every datum carries an envelope:** `(value, as_of/knowable_date, source, coverage_status ∈ {present, unknown, stale})`. This is what makes UNKNOWN→defer *mechanical*.
- Append-only event log; per-field freshness metadata; declared-coverage map; **source-reliability tier on every field: EDGAR (authoritative) > IBKR-scoped > EOD-free > news (fenced).**
- Scale: local relational store (SQLite/Postgres) + parquet for time-series — do **not** stand up a big-data stack.
- **Survivorship flag:** seeding from *currently* tradeable names bakes survivorship into future backtests. Fine for live screening — but **snapshot the universe over time starting now** (cheap), so later validation isn't impossible.

### 7. Orchestrator / refresh
- Daily: EOD price/volume (breadth) + EDGAR submissions poll. Scoped: IBKR market data for traded/shortlist names. Event-driven: big movers → Screen 2.
- Idempotent refreshes; dedup; pacing-aware queueing on the IBKR/EDGAR clients.

## Output contracts (the most reusable deliverable)

### A — Name data-record (what the gates consume)
Every field with its `(value, as_of, source, coverage_status)` envelope.
- **identity:** internal_id · conid · ticker+MIC · eod_symbol · CIK? · name · country · currency · market_cap
- **price-derived (source: EOD; IBKR cross-check at depth):** last · 52w_high · drawdown_from_high · ret_3m/6m/12m · rel_ret_vs_sector · adv_90d_shares · adv_90d_usd · turnover · volume_spike
- **fundamental (US: present / non-US: unknown):** ev_ebitda + pctile_vs_history · pe + pctile · fcf_sign · op_income_sign · net_leverage
- **stress (attached, never a gate; shortlist only):** iv_pctile *(or unavailable)* · short_interest *(or unavailable)*
- **events (pointers only):** typed events {downgrade | guidance_cut | contract | threat} with dates
- **meta:** per-field coverage_status + as_of + source-tier · `overall_coverage_tier ∈ {US-full, non-US-thin}`

### B — Candidate-record (the screen→depth contract; emitted when gates pass)
`data_record (A)` **+** `screens_fired[]` **+** `gate_results{gate → PASS|FAIL|UNKNOWN}` **+** `trigger_reason` **+** `unknown_gates_for_depth[]` **+** `twin_to_rule_out` **+** `triage_band`.

## Build order (within the layer)
1. entity master / resolver (+ IBKR contract data for the universe seed) → 2. EOD breadth client (the wide net) → 3. store (PIT + coverage + source-tier) → 4. EDGAR client (US fundamentals/filings) → 5. IBKR client (scoped execution + shortlist vol) → 6. news/event client (fenced) → 7. orchestrator. Reusable across all three screens.

## Validation discipline (face-validity, never P&L)
- Resolve known names correctly — a US large-cap, a non-US name, an ADR — verify CIK↔conid↔eod_symbol↔ticker by hand.
- EDGAR `frames`/`companyfacts` return expected values for known filings; EOD prices match a known chart.
- Coverage logic: a non-US name returns **UNKNOWN** on fundamentals, never a silent 0.
- PIT stamps + staleness flags fire correctly; shortlist re-verification against IBKR agrees with EOD within tolerance.
- **Validate the data-record against names you already know before any gate consumes it.** Validate, never tune on forward returns.

## What this unblocks
Once the data-record is reliable, the screen gates become a thin layer on top and the candidate-record flows into your existing depth framework. Foundation of the breadth half — everything rides on it. Any later dashboard deploys via GitHub → Cloudflare Pages, configured once.

---
*End v0.2. Spec only — no component built yet.*
