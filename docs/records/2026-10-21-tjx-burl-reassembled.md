---
id:
status: shipped
date: 2026-10-21
prs: [757]
supersedes:
superseded-by:
---

# TJX and Burlington re-assembled on #756 — each page now reads its own adjusted-EPS guide; TJX's draws agree 5/5, Burlington's stay split

**WHAT.** One re-assembly each of TJX and BURL. These are the operator's planned step after #756 merged
(the operator approved it on 2026-10-21, "re-assemble TJX and BURL based on latest main code"). The pass
ran on main `1d9708d8`, artifacts only: the two pages, their `frontend/dossiers/` mirrors and the
dossier index.

What landed from #756:

| | TJX | BURL |
|---|---|---|
| `valuation.adjusted_eps` | was "adjusted figure not in the 99.1 revised guidance" → **"Fiscal 2027 adjusted EPS guide $5.15–$5.20; adj P/E ~28.4x at $146.99 (2026-10-20 close)"** | same old note → **"next-fy adjusted EPS guide $11.77–$11.97; adj P/E ~21.8x at $258.86 (2026-10-20 close)"** |
| `primary_source.current_guide` | was "no guide in any of the 6 parsed release(s)" → **"adjusted eps Q3 2027: 1.30–1.32 $/sh; adjusted eps Fiscal 2027: 5.15–5.20 $/sh"** | was "adjusted eps next-fy: 11.8–12.0 $/sh" → **"… 11.77–11.97 $/sh; adjusted eps Q3 2026: 1.60–1.70 $/sh"** |
| forecast-error note | carries the "accounting STANDARD" sentence | carries the "accounting STANDARD" sentence |
| R1 anchor | unchanged: $129.10, ex-lease 15.8x, net debt −$3,133M | unchanged: $322.06, ex-lease 16.4x, net debt $1,210M |

The page also states, for BURL, the guidance read across its other releases: each quarter beside its
year, e.g. Fiscal 2026 $11.45–$11.80 and Q2 2026 $2.05–$2.20 from the May release.

**WHAT ELSE MOVED.**

- **Prices: the 2026-10-20 close** (TJX $146.99, BURL $258.86). The store was topped up before
  assembly: TJX was at 10-16, BURL at 10-06, SPY at 10-16, MDY at 10-09; all four now run to 10-20
  (`vinci refresh … --aggs`, 104 bars).
  - The 52-week benchmark leg is TJX vs SPY and BURL vs MDY, both over 2025-10-17..2026-10-16 (the
    page's reference date) on fresh closes.
  - Without the MDY top-up, the #743 guard would have refused BURL's leg.
  - BURL's "PRICE STALE AT ASSEMBLY" caveat is gone.
- **BURL's market-cap date: 2026-09-28 → 2026-09-25.** It is the same CIQ export and the same value
  ($15,998.4M); the date is a correction, not a regression.
  - The assembler dates the comps cap by matching the panel's printed close against the store
    (#466). The panel prints $254.69, which is BURL's 2026-09-25 bar exactly.
  - At the last build (2026-09-30) the store's BURL bars stopped at 09-22, so nothing matched. The
    page fell back to CIQ's export stamp (09-28), three days ahead of its data.
  - The page now states a 25-day gap between the price and the CIQ valuation snapshot. A current
    cap or TEV needs a fresh CIQ export.
- **The synthesis draws (re-run, not re-rolled):**
  - **TJX: 5 of 5 strongly-bullish, unanimous.** The last build (2026-10-18) had 4 strongly-bullish
    and 1 mixed. So the machine proposal is no longer withheld: under the overshoot book, a
    strongly-bullish lean derives BUY.
    - The proposal stays SEALED until the analyst's verdict is recorded. The page says so and
      never prints it, so it cannot anchor the decision.
    - The ledger will seal it beside the human verdict when one is logged. The IC memo's call was
      WATCHLIST.
    - Two builds on near-identical inputs gave 4/1 and 5/0. Neither is the "right" one; the page
      states this build's tally.
  - **BURL: 3 mixed and 2 strongly-bullish, the same tally as its last build.** The proposal stays
    withheld.
  - Both kept reads are new prose, e.g. TJX "…broad comp strength and a self-funding balance sheet
    behind a gradual-bleed de-rate".
- **QA flags.** TJX loses its "DIRECTIONAL language 'buy'" flag (the wording moved). BURL gains one;
  it is the Street's "Buy consensus (1.00)", a factual phrase, and stays flagged for the human.
  BURL's "TWIN ampersand-name 'Bed Bath & Beyond'" flag is gone with the re-drawn twins.
- **`layer_refreshes` is empty on both.** A fresh assembly builds every layer natively; the earlier
  refresh entries described the pages this replaces.

**HOW VERIFIED.**
- **Every input checked before the paid runs:**
  - **CIQ:** sha256 match with the operator's Drive folders (TJX 10 exports, newest 2026-10-18;
    BURL 11, newest 2026-09-28).
  - **The store:** read for each symbol's last bar, then topped up.
  - **Operator-authored state:** no tag reason on either anchor; neither name has a scenario record.
- **The ticker claim:** `artifacts/tjx-burl-reassemble` was pushed before work (RUNBOOKS preamble),
  after checking remote heads and every open PR's file list.
- **Both pages compared field by field against main.** The table and list above are that
  comparison. BURL's cap date was traced to the store match shown, and the benchmark legs were read
  off `stock_performance`.
- **Suite:** full offline suite (`-m "not network"`) with the shared price store UNLINKED, as in CI: **6,518 passed, 53 skipped, 2 failed**. The two failures are V (`test_share_basis`) and MCK (`test_capital_panel_selection`), the CIQ data issues that fail identically on main (STATE row 32 (12)). With the store linked, a third failure appears (`test_store_freshness`): the top-up left TJX, BURL, SPY and MDY newer than the other 23 pages' names, an environment state that CI never has (the #747 precedent).

**BOUNDARY.**
- **Population:** two pages, `data/dossiers/{TJX,BURL}/dossier.json` at main `1d9708d8` vs the
  re-assembled files.
- **Prices:** the shared store `mosaic-theory-ta/data/vinci.db`, bars to 2026-10-20 for TJX, BURL,
  SPY and MDY only. The universe frontier stays 2026-10-16, which is why each page's reference date
  and benchmark window end there.
- **Draw tallies:** one build each, 5 draws each. A tally, never a rate.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Two paid assemblies.** Every LLM phase re-ran: the synthesis (5 draws), the transcript operating
  drivers and the covenant extraction.
- **The follow reasons' figures stay at their follow dates.** TJX's are from 2026-10-16, BURL's from
  2026-09-22. They are dated by design.
- **The CIQ valuation snapshot is older than the price on both pages.** TJX's is 2026-10-16 (4 days);
  BURL's is 2026-09-25 (25 days). The pages state it; a fresh export is the operator's call.
