# Data Sources — Verified Tool Inventory

PM-maintained. Sole source of truth for what data PM can actually pull. Framework LLM is bound to this file: source proposals must reference tools/modules listed here, not external or unverified sources.

**Last verified:** YYYY-MM-DD (PM updates on each material change)

---

## SOURCE-BINDING DISCIPLINE — APPLIES THROUGHOUT

The source-binding discipline previously focused on Sessions A2 through C ("consensus / multiple / positioning pulls"). **Source-binding extends upstream to A1 (Parts 1, 4, 5) and remains in effect at A2.** Rules SBC-1 (numerical claims), SBC-2 (event claims), and SBC-3 (narrative exception) are defined in `checklist.md` STEP A1. Summary for sourcing decisions:

- Specific numerical claims about a candidate name's current state (price, return, multiple, business metric, rating, PT) → require in-session `web_search` tool call with visible URL, PM-upload extraction per the tools listed below, OR `[LLM-narrative, not verified]` tag.
- Specific event citations (M&A, listing notices, regulatory actions, named broker actions, named precedents) → same requirement.
- Qualitative mechanism-fit judgments (how a name maps to the thesis) → no source required (SBC-3 narrative exception).
- Training-memory claims without an in-session tool call are NOT acceptable as sourced claims, regardless of LLM confidence.

Verification at Session C: a new "Source-binding carry-forward check" runs at the start of Session C BEFORE C1-PRE. It surfaces any A1/A2 claim that is currently driving the live decision basis without source-binding or B3 verification. See `checklist.md` STEP C1-SB SOURCE-BINDING CARRY-FORWARD CHECK (named STEP C1-SB to avoid a naming collision with the pre-existing STEP C1 — SCENARIO REFINEMENT step).

---

## CIQ (Capital IQ Pro)

### Financials modules
- Income Statement, Balance Sheet, Cash Flow — Annual / Quarterly
- Segments — geographic and business segment breakdowns
- Capital Structure Summary
- Capital Structure Details
- Ratios — standard financial ratios
- Industry Specific (where applicable)
- Pension OPEB (where applicable)
- Supplemental
- Key Stats

### Estimates modules
- Consensus EPS / Revenue / Margins — current + 4 prior quarters minimum
- Revision history with broker attribution (subject to entitlement)
- Guidance — company-issued forward guidance
- Surprise — historical beat/miss vs consensus
- Trends — consensus trend over time
- Revisions — aggregate revision counts

### Multiples
- Current + 5y multiple history
- TEV/LTM Revenue, TEV/NTM Revenue, P/E (LTM and NTM), EV/EBITDA, etc.
- Quarterly granularity

### Holders / Ownership
- Public, Private, Institutional holders
- Quarterly snapshots with delta computation
- Full latest holder list with sizing

### Insider Trading
- Trailing transactions (configurable window)
- Form 4 detail (US issuers)
- Holder, transaction type, shares, price, filing date

### Charting
- Short interest history (1-3 year configurable)
- Price history
- Custom charts with data export

### Key Developments
- News and research notes
- Filterable by **date range, document type, and category** (confirmed PM has full filter capability)
- Categories include: Client Announcements, Results Announcements, Guidance, M&A, Investor Activism, Index Constituent changes, etc.

### Transcripts
- Earnings calls
- Available for major reporting issuers
- Format note: CIQ exports as ".rtf" extension are actually MS Word documents — require LibreOffice or Word for conversion before LLM parsing

### Other CIQ modules
- Events Calendar
- Quick Comps
- Credit Health Panel / Credit Ratings
- Fixed Income
- M&A / Private Placements
- Customers & Suppliers (structured customer evidence — useful for B3 item b)
- Shares Outstanding history

### Jurisdiction coverage (annual filings)
- 10-K (US), 20-F (FPIs)
- Annual Report aggregation for UK/EU
- Yuho (Japan), Business Report (Korea)
- Coverage varies by issuer — for thinly-covered names, supplement with company IR pages

---

## IBKR (Interactive Brokers)

### Options chains
- US-listed equities
- Canada, Europe, Asia-Pacific (200+ countries supported)
- ATM straddle prices for implied move computation
- Bid/ask, volume, open interest

### Volatility
- Implied 12-month vol (where liquid options exist, during the name's primary listing market trading hours)
- Historical vol 12-month + 36-month

### Volume / Liquidity
- 90-day Average Daily Volume (90D ADV) in shares
- Listing currency

---

## Koyfin (free tier)

### Price / Performance
- Stock and ETF price history
- Performance returns (cross-asset, configurable windows)

### Estimates
- FY1 EPS change (%)
- FY1 EPS, current NTM P/E
- P/E range (past)
- Short interest history

### Volatility / Ratios
- 1Y volatility
- EV/EBITDA, P/E (NTM or LTM), P/Sales, Net Debt/EBITDA
- 5y beta (monthly)

### ETF flows
- ETF flow data (verified available in free tier)

### Scope limitation
Koyfin in PM's free tier does NOT include: commodity prices, macro time series, cross-asset correlation analytics, alternative data feeds, freight/shipping data, flight/tourism data, or specialty industry feeds. **Framework must not assume access to upstream macro indicators beyond what's listed above.**

---

## TradingView

### Not yet operationally verified
- Charting + technical analysis tools (PM has account, not yet used for thesis work)
- Real-time charts

**Status:** held out of source-to-question map until PM verifies use through actual thesis work.

---

## Freely available

### SEC EDGAR (US issuers only)
- 10-K, 10-Q, 8-K filings
- Form 4 insider transactions
- Proxy statements
- Free, comprehensive, US issuers

### Company Investor Relations pages
- Event dates calendar
- Annual reports (especially for non-US issuers with thin CIQ coverage)
- Earnings releases / decks
- Press releases

### Financial press
- FT, Bloomberg public articles, Reuters
- Free reads of news / company coverage
- NOT a substitute for Bloomberg Terminal (which PM does NOT have access to)

---

## What's explicitly NOT in PM's tool inventory

The framework must not propose, reference, or instruct PM to pull from any of these:

- **Bloomberg Terminal** (no subscription) — therefore: no BBG-specific data feeds, no BQNT, no BLP
- **FactSet** (no subscription)
- **Refinitiv Eikon** (no subscription)
- **Specialty/alternative data providers** — Quandl, YipitData, Earnest Analytics, Second Measure, M Science, etc.
- **Commodity feeds** — beyond what Koyfin shows in free tier (which is limited)
- **Cross-asset macro databases** — beyond Koyfin's basic ETF and price history
- **Flight/tourism data** (IATA, OAG, etc.) — not accessible
- **Trade/shipping data** (port traffic, freight rates) — not accessible
- **Customer-side intelligence platforms** — G2, Capterra, Glassdoor are PM-checkable via web browsing but not structured data pulls; framework treats as web search not structured

When framework logic suggests an analysis that depends on data outside this inventory (e.g., "to track Chinese tourist flows for European luxury thesis"), LLM must surface the gap honestly: 'this data would require a source not in PM's verified inventory; proceed without it, or PM acquires the data source first, or thesis-type does not fit fund's data infrastructure.'

---

## Source-to-question map (the operational core)

When PM is uncertain about how to ground a declaration in Session A/B/C, consult this map. LLM may reference these mappings when proposing source-direction.

### "What is consensus currently pricing?"
- **Primary:** CIQ Estimates → Consensus sheet (current EPS/Rev/Margins + revision history)
- **Supplementary:** CIQ Key Developments filtered to `Type = Research Notes` over last 30-60 days (qualitative analyst views)
- **Verification:** Koyfin FY1 EPS for cross-check

### "What is positioning showing?"
- **Primary:** CIQ Holders (institutional flow snapshots, top-5 holder deltas) + CIQ Charting → Short Interest history
- **Liquid-options names:** IBKR options chain (skew, implied move on next earnings, ATM straddle)
- **Supplementary:** Koyfin short interest for cross-check
- **Insider angle:** CIQ Insider Trading (forward-filled by holder name)

### "What is the trade-press narrative on this thesis?"
- **Primary:** CIQ Key Developments → filter by `Type = Research Notes` or `Type = Client Announcements` over relevant window
- **Supplementary:** Web search of FT, Reuters, Bloomberg public for the past 30-60 days
- **For sector-level narrative:** Industry trade press (PM searches by sector keywords)

### "What does the customer evidence show?"
- **Primary:** CIQ Customers & Suppliers module (structured) — if available for the issuer
- **Secondary:** CIQ Transcripts (earnings call mentions of named customers) + IR releases (customer announcements)
- **Tertiary:** Web search of G2/Capterra/Glassdoor (qualitative customer sentiment, not structured)
- **For B3 item b in evidence card**

### "What does the historical drawdown look like (for Gate 5)?"
- **Primary:** CIQ Charting → Price history, 5-year window
- **Compute:** rolling 30-day, 60-day, 90-day max drawdowns
- **Supplementary:** Koyfin price history for cross-check

### "What does sector ETF performance show (for Gate 4)?"
- **Primary:** CIQ Charting on sector ETF or Koyfin sector ETF price history
- **For non-US names:** identify the relevant local sector index (STOXX subindex, TOPIX subindex, KOSPI 200 sector, etc.) and pull from Koyfin or CIQ
- **Compute:** worst rolling 3-month return over 5 years

### "What does options market imply (for C2 Check 2)?"
- **Primary:** IBKR options chain for the next earnings or catalyst event
- **Compute:** implied_move = (ATM_straddle / underlying) × sqrt(365/days_to_expiry), where days_to_expiry is CALENDAR days to expiry (the IBKR expiry-tab number). Option time-to-expiry is calendar time — annualize with a 365-day year; do not pair a 252 trading-day numerator with IBKR calendar days.
- **Applicability:** only for names with liquid options at the relevant expiry (rule of thumb: daily volume >100 contracts on near-term ATM strikes)
- **If illiquid options:** substitute with Check 6 (post-event reaction pattern) — pull last 3 earnings prices from CIQ Charting

### "What is the credit profile / leverage situation?"
- **Primary:** CIQ Capital Structure Details + Credit Health Panel
- **Supplementary:** CIQ Fixed Income (debt instrument detail)
- **Ratings:** CIQ Credit Ratings (includes S&P, Fitch, Moody's where available; for local issuers includes JCR, R&I, NICE, Korea Ratings)

### "What does management track record look like?"
- **Primary:** CIQ Estimates → Surprise sheet (historical beat/miss vs consensus over multiple quarters)
- **Supplementary:** CIQ Transcripts (read previous guidance vs realized to identify pattern)

### "What is the insider activity?"
- **Primary:** CIQ Insider Trading (forward-fill Holder Name, filter on Transaction Type)
- **US-only supplementary:** SEC EDGAR Form 4 for raw transaction detail
- **For non-US:** rely on CIQ aggregation (PDMR/MAR filings for UK/EU, EDINET for Japan, KIND for Korea — coverage varies)

---

## Maintenance commitment

This file is reviewed and updated by PM:
- At fund anniversary review (annual hard check)
- When PM adds or removes a tool subscription
- When PM discovers a CIQ feature/filter not previously used
- When framework LLM surfaces a source gap during a session (PM decides: ignore, acquire, or expand the inventory)

**Stale-file risk:** if PM doesn't maintain, LLM proposes sources that no longer reflect reality. Mitigation: anchor maintenance to fund-anniversary cadence at minimum.
