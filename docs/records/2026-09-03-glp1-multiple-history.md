---
id:
status: recorded
date: 2026-09-03
prs: []
supersedes:
superseded-by:
---

# The multiple history was already on disk — WST's premium predates the driver, and MCK is the name that re-rated

**BOUNDARY.** Source: `CIQ Financials→Multiples` (Close, quarterly), 39 settled quarters
2017-03-31…2026-06-30 plus a current snapshot at 2026-09-02 which is **excluded from every
distribution** per the documented last-column rule. Metrics are **forward** basis (`P/NTM EPS`,
`TEV/NTM EBITDA`). Read 2026-09-03 through `CiqBundle` + `ciq_sheets._multiples_close`. No raw CIQ
is reproduced. Split dates 2022/2023/2024 are **chosen**, and all three are reported for that reason.

## Two process corrections first, because they caused the rest

**The history was never a new pull.** It sits in `Financials→Multiples`, which
`docs/ciq_extraction_notes.md:282` describes precisely: *"~91 rows × 9 cols: historical quarterly time
series with Average / High / Low / Close per quarter … ~5y history."* The operator's endorsement and
my proposal both assumed a new CIQ session was needed. **Check whether the existing export carries the
series before pulling anything.**

**`ciq.py` handles workbooks and I said it did not.** I read `vinci/ciq/` (RTF relationship exports),
found no workbook path, and asserted absence — while `vinci/dossier/ciq.py` + `ciq_sheets.py` hold a
tested BIFF reader and `pyproject.toml:16` pins `xlrd>=2.0` commented *"legacy .xls (BIFF) CIQ
Financials/Estimates workbooks"*. The hand-rolled extraction that followed produced two defects in one
sitting: a name-prefix match that returned **Waters' multiple as West's** (Waters sits inside West's
comp set), and a `2>/dev/null` that swallowed an exception into empty tables. Everything below runs
through the sanctioned path, which finds `Close` by **label search within 6 rows** rather than a fixed
offset and takes the latest close **by date** because column order is not time order — incident #459.

## The cross-source assert — available today, no new pull

`Financials→Multiples` `P/NTM EPS` Close (latest by date) against `Estimates→Multiples`
`Price/Earnings` @ NTM. Different files, different sheets, independent parse paths:

| | financials | estimates | delta |
|---|---|---|---|
| WST | 36.94 | 36.94 | **0.00%** |
| WAT | 26.39 | 26.39 | **0.00%** |
| BDX | 14.17 | 14.17 | **0.00%** |
| MCK | 19.87 | 19.87 | **0.00%** |

All four reconcile exactly. This retroactively validates the NTM figures the premium ranking rests on.

## The test: did the premium open up, or predate the driver?

`P/NTM EPS`, own history, current percentile and pre-vs-post median at each split:

| | current | percentile | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| **WST** | 36.9 | **37%** | −5% | +2% | −9% |
| **WAT** | 26.4 | 63% | +10% | +5% | +10% |
| **BDX** | 14.2 | 13% | −11% | −18% | −28% |
| **MCK** | 19.9 | **95%** | **+62%** | **+71%** | **+73%** |

`TEV/NTM EBITDA` gives the same ordering (MCK 95th, +52/+59/+67%).

**WST's premium predates GLP-1, and the conclusion survives every split date** (−5%, +2%, −9% — no
consistent direction). At the 37th percentile of its own forward history it is mid-range, not
elevated. **The +48% to peers is a standing quality premium. The shortlist holds on WST.**

**MCK re-rated, hard and consistently** — +62/+71/+73%, 95th percentile on both metrics.

## The mechanical explanation for MCK is ruled out

| | diluted shares | net debt |
|---|---|---|
| MCK | 228m → **123m (−46%)** | 3,451 → 4,811 (+39%) |

**A 46% share-count reduction pushes the P/E multiple DOWN, not up** — buyback-boosted EPS is a larger
denominator. MCK's `P/NTM EPS` multiple sits at the 95th percentile *despite* that, so price outran
even the repurchase-inflated earnings. The re-rating is **stronger** than the raw figure, not
explained away. On the EV side, net debt rose 1,360 against an enterprise value near $86bn — roughly
**1.6% of EV**, nowhere near a +52–67% move in `TEV/NTM EBITDA`. Neither buybacks nor leverage
accounts for it.

## Two corrections to the previous record's reading

**WAT is 63rd percentile, not 97th.** The 97th came from `P/LTM EPS`, whose current value of 186.1x is
a one-off distortion. On the forward basis WAT is upper-middle, not extended. My "most extended of the
four" was an LTM artifact.

**BDX is cheap AND structurally changed.** 13th percentile, de-rating on every split — but **shares
+27% (224m → 283m) and net debt +245% (4,670 → 16,099)**. Cheapness alongside heavy dilution and a
3.4× leverage build is as consistent with company-specific trouble as with opportunity. WAT's balance
sheet also swung from **net cash −1,396 to +4,938 net debt**, a 6.3bn move that is material context
for any multiple comparison across its own history.

## BOUND ON THE CONCLUSION — not a caveat

The specified test was **spread-to-peer over time**. What ran is **own-history percentile**, and these
do not answer the same question: a sector-wide re-rating moves a name and its peers together, so
own-history alone cannot separate name from sector. Peer histories require **each peer's own
workbook**, and the pull holds only the four subject names — their comp sheets are point-in-time.

**This is therefore unresolvable from what is on disk.** WST's stability across three split dates and
its 37th-percentile standing are strong evidence the premium is not new, but they do not exclude a
sector-wide re-rating that lifted WST and its comp set together. Stated as a bound: **the WST
conclusion holds against its own history and is untested against its peers'.**

## Pull defects, counted rather than passed over

Per name, 11 files: **10 matched a registered kind, 1 dropped**. The drop is always the **Credit
Health Panel**, which has no entry in `_WORKBOOK_KEYWORDS`.

**MCK's `Financials_Annual.xls` reports `Period Type: Quarterly`** — the other three are correctly
Annual. Per the extraction notes the annual export drives 5y normalized analysis and trend flags, so
MCK is missing that half of the standard pull. The `Multiples` subsheet is byte-identical across both
exports for all four names, so it is frequency-invariant and the percentile work above is unaffected.

## Still owed

The `ciq.py` extension the operator specified — ticker-not-name-prefix matching for comp sheets, the
cross-source reconciliation as a **failing assert** rather than a one-off script, and synthetic BIFF
fixtures pinning each. The reconciliation ran clean here by hand; it is not yet a guard.
