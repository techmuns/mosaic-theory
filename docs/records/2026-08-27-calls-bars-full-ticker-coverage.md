---
id:
status: shipped
date: 2026-08-27
prs: []
supersedes:
superseded-by:
---

# The bar window stops excluding the thin tail, and the tail turns out to hold nothing

**What was wrong.** `tickers.json` tracked 214 of the 411 tickers @pdicarlotrader ever mentioned.
The cutoff was undocumented and turned out to be **mentions >= 3** — every excluded ticker had one
or two mentions. Downstream that meant 263 audit rows carried NO price anchor and 63 directional
calls scored `NO_PRICE_DATA`: not judged and not counted, with nothing in the numbers saying so.

**What shipped.** The spec now covers every mentioned ticker. The 197 additions use the SAME
window rule the original 214 were built with, derived from the file rather than assumed —
`fetch_from` = first mention −95 days (exact across all 214), `fetch_to` = min(last mention +1
year, 2026-08-25). The existing 214 entries are BYTE-IDENTICAL; the change is append-only.

Fetched 198 tickers / 51,834 bars through the existing `vinci calls fetch-bars` path (key from env,
never logged). 16 came back empty.

**Coverage.** Price anchors: **7,922 -> 8,149 of 8,185 rows (96.8% -> 99.6%)**.

**Scoring: purely additive, and the headline did not move.**

| | before | after |
| --- | --- | --- |
| CLOSED | 2,811 | 2,857 |
| NO_PRICE_DATA | 71 | 13 |
| direction-correct | 51.12% | 51.03% |

**ZERO previously-CLOSED rows changed return or verdict** — the fetch could only add, never restate.
45 rows moved `NO_PRICE_DATA -> CLOSED` and scored **20/45 (44%) direction-correct**, BELOW the
51% base. The thin-coverage tail carries no hidden skill: this is the third independent check to
land on ~51%, after the noise-removal and adoption passes. Excluding it was never the reason the
number is what it is.

**The 36 rows still blank, all of them honestly unfetchable as US equities:**

| kind | tickers | rows |
| --- | --- | --- |
| crypto | DOGE, SOL, BTCU, BTCSD | 11 |
| indices | SPX, NDXP, KOSPI | 6 |
| share-class notation | BRKB (Polygon wants `BRK.B`) | 6 |
| cashtag typos in the source posts | SCMI, ID, CLK, DOOG, CWHY, OCL, ZET, RBXL, TSAL, RKLN, INTV | 13 |

Several typos are legible mangles of real symbols (TSAL/TSLA, RKLN/RKLB, DOOG/GOOG). They are NOT
auto-corrected — inferring the intended ticker from a misspelling is a guess about what he meant,
and this corpus does not guess.

**FOUND, NOT FIXED — the `renamed` map is dead data.** `tickers.json` carries
`{"SQ": "XYZ", "FB": "META", "TWTR": null}`, and NOTHING reads it: `fetch_account_bars` passes the
cashtag straight to Polygon. Verified by symbol search across `vinci/calls/` — the only occurrences
are comments. The cost is real and visible: `$SQ` holds 153 bars ending **2025-01-17**, the day
Block became XYZ, so its window silently truncates mid-corpus rather than following the rename.
`BRKB` is the same class of problem in punctuation form. Wiring the map into the fetch (with a
mid-window handoff for a rename that lands inside a ticker's own window) is a build, not a
one-liner, and is NOT in this change.
