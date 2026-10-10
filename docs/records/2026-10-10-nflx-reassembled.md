---
id:
status: shipped
date: 2026-10-10
prs: [704]
supersedes:
superseded-by:
---

# NFLX re-assembled on the latest code — the stamp catches up, a renamed peer joins the capital-intensity panel, and the lean draws mixed

**WHAT.** NFLX was re-assembled on main @544af3ae (`2026-10-09.3`).
- **The previous page** was assembled 2026-10-07 on `2026-08-16.1` and refreshed six times since,
  the last landing `2026-10-09.3`'s blocks (#702). The new stamp covers the whole page, so the
  refresh record is dropped, as every full assembly does.
- **Prices were refreshed first:** NFLX, SPY, MDY and IWM, 2026-10-07 → 2026-10-09 by per-symbol
  aggregates (12 bars). NFLX's close is $70.30 on 2026-10-09; the page had $68.69 on 2026-10-06.
- **The CIQ exports are unchanged.** The Drive folder and `data/manual/ciq/NFLX` hold
  byte-identical files (11 of 11), with Financials `d162f709ec` and Estimates `406592d103` — the
  page's own hashes.

**Only artifacts changed:**
- NFLX's page and its mirror;
- `frontend/dossiers/index.json` (the lean label);
- the NFLX and IWM price fixtures;
- STATE row 32.

**WHY.** Operator instruction, 2026-10-10: "re-assemble NFLX". Netflix reports Q3 on 2026-10-20 (the
company's 2026-09-14 announcement), so this page is current until then.

**WHAT MOVED** (against main's page):

    extraction stamp      2026-08-16.1 (+6 refreshes, last 2026-10-09.3)  ->  2026-10-09.3 (assembled)
    price                 $68.69 (2026-10-06)  ->  $70.30 (2026-10-09)
    draws                 strongly-bullish 4 / mixed 1  ->  strongly-bullish 2 / mixed 3 — proposal withheld both times
    lean                  strongly-bullish  ->  mixed
    caveats / qa          6 / 7  ->  6 / 9
    non-operating count   absent  ->  1 of the trailing 4 (window end 2026-06-30)
    recipe                R1_midcycle_margin_evebitda, applicable=False  ->  unchanged

**Unchanged, equal to main:**
- `forward_consensus`, `forward_multiple_history` and `historical_forecast_error`;
- `midcycle` and `reference_date`.

**What moved, and why each is expected:**
- **`ev_bridge`:** only `edgar_source` moved. The EDGAR cross-check now names the short-term
  securities leg ($29M), the #684 code, which postdates the 10-07 assembly.
- **The anchor's `net_debt`:** its source text moved the same way. Its value is still withheld,
  because EDGAR's debt read is under-captured: notes payable of $14,309M exceed the extracted total.
  That is why R1 declines on NFLX, and nothing here changes it.
- **`mechanical.valuation`:** 14 figures, the forward multiples repriced at the new close (e.g. 19.13x
  → 19.58x).
- **The machine's R4 read, now on the page:** NTM EBIT > 0 (16.7x) and R1 cannot anchor (declines;
  EBITDA basis divergent 3.42×) both hold. R3 CAN price it cleanly: the P/E basis is
  indistinguishable and only 1 of 4 quarters is material. So R4 is not proposed, and the R1 tag
  stands.

**A PEER JOINED THE CAPITAL-INTENSITY PANEL — VERIFIED, NOT ASSUMED.** CIQ's comps grid lists
"Skydance Corporation $10.7B" as `SKYD`.
- **On main's page** it read "unresolved — no CIK for 'SKYD'".
- **Now** it resolves to **CIK 0002041610, "Skydance Corp" (NYSE)**. That is the same issuer the
  local securities table holds as PSKY / Paramount Skydance; PSKY no longer resolves. SEC's ticker
  map picked up the renamed ticker after 2026-10-07.
- **What enters with it:** $7,683M acquired, $44,411M of assets, and a $5,981M goodwill impairment
  (FY2024).
- **The panel moves:**
  - median acquired-to-market-cap 0.107 → 0.288;
  - median acquired-to-assets 0.152 → 0.162;
  - large-peer impairment median 8.1% → 12.8%;
  - n_large 5 → 6.

  A correct peer, newly reachable — not a mis-resolution. (The old PARA ticker now belongs to an
  unrelated company, Banzai.)

**Redrawn by the LLM-fenced phases:**
- **The synthesis:** 7 bull / 4 bear → 8 bull / 5 bear, and the lean drew mixed. Two new QA flags
  mark directional words for human review ('conviction', 'sell').
- **The covenant digest and the operating-driver rows:** reworded.

**THE LEAN FLIPPED, AND THAT IS NOT EVIDENCE.** Strongly-bullish 4/1 on 2026-10-07 is now mixed 3/2.
The inputs moved by three closes of price and one peer. The gate withholds the proposal both times,
and nothing was re-rolled.

**THE FIXTURES:**
- **NFLX:** 3 bars added (10-07 → 10-09).
- **IWM:** the 10-09 bar added. Its 10-07 row changed only in `source` (`polygon-grouped` →
  `polygon-aggs`) — the refresh re-fetched an existing bar, and the prices are identical.
- **The companyfacts fixture** rebuilt byte-identically.

**HOW VERIFIED.**
- **CIQ inputs:** sha256 checked on 11 of 11 files, Drive against the data copy; Financials and
  Estimates equal the page's hashes.
- **Prices:** `vinci refresh NFLX SPY MDY IWM --start 2026-10-07 --end 2026-10-09 --aggs` wrote 12
  bars; the store now ends 2026-10-09 for all four.
- **Assembly:** `dossier --ticker NFLX` exited 0 with `1 done · 0 error(s)`, 2026-10-10
  18:33–18:40 IST.
- **The page was diffed against main's key by key.** Every moved key is itemized above, and the
  peer's identity was resolved through the assembly's own resolver.
- **Mirror:** `frontend/dossiers/NFLX.{json,md}` are byte-identical to the page.
- **Suite:** `pytest -m "not network"` on the freshly-committed artifacts. Counts are in the PR.

**BOUNDARY.**
- **Scope:** one page, NFLX, 2026-10-10.
- **Prices:** through the 2026-10-09 close.
- **CIQ:** the exports on disk, unchanged since 2026-10-07.
- **Draw counts:** five draws, one build.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The synthesis is fully rewritten,** as every full assembly does.
- **NFLX's R1 anchor still declines** on EDGAR's under-captured debt. CIQ's bridge — claims $7,527M at the 2026-06-30 balance
  sheet, equal to CIQ's TEV less market cap — is on the page beside it.
- **The Q3 report (2026-10-20) will stale this page.**
