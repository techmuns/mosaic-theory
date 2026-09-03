---
id:
status: recorded
date: 2026-09-03
prs: []
supersedes:
superseded-by:
---

# GLP-1 step 10 — the input pack for WST, WAT, BDX, MCK. Legs are the analyst's act

**BOUNDARY.** Source: operator's CIQ exports read 2026-09-03 through `CiqBundle`. Spot = comp-sheet
`Day Close Price Latest`, as-of ~2026-09-02. EPS = `EPS Normalized` consensus. P/E = NTM forward,
Capital IQ basis. USD. No raw CIQ committed. **Internal check:** spot ÷ FY27E reproduces each name's
published FY27 P/E to two decimals for all four.

## The pack

| | spot | FY26E | FY27E | FY28E | NTM P/E | **FY end** |
|---|---|---|---|---|---|---|
| WST | 342.63 | 8.96 | 9.96 | 11.34 | 36.94 | Dec-31 |
| WAT | 412.20 | 14.58 | 16.55 | 18.54 | 26.39 | Dec-31 |
| BDX | 187.52 | 12.62 | 13.29 | 14.18 | 14.17 | **Sep-30** |
| MCK | 924.78 | 39.11 | 44.62 | 50.46 | 19.87 | **Mar-31** |

**The FY columns are NOT comparable across names.** BDX closes September and MCK closes March, so
MCK's FY2027 ends under seven months out while WST's and WAT's run to end-2027. **Only NTM is
comparable as published**, and any cross-name table on FY-labelled columns mixes horizons. Each
underwrite must state which fiscal year its legs are struck on and when that year ends.

## What the underwrite needs, and who supplies it

R3 is `value/share = EPS × forward P/E`. The machine supplies **consensus and the multiple context
above**. The analyst supplies **bear/base/bull EPS, bear/base/bull multiple, and the horizon** — and
consensus is an input to that judgement, never a substitute for it. Nothing here proposes legs.

The multiple leg is the one that binds. GOOGL's record is the precedent worth reading first: its
20.5x bear is labelled *"the SINGLE BINDING ASSUMPTION of this underwrite"*, its quartile basis is
recorded as **LIMITED** and treated as context rather than load-bearing, and its ratio moves from
2.43x to below the 2.0 bar on a 0.33x change in that one number.

## Carried into each underwrite

**WST — the premium question is settled HERE, not by comps.** Five bases gave four answers
(snapshot +48% to peers, own history 37th percentile, full-set spread re-rated, containment cheap on
an Avantor artifact, STVN expensive) because **WST has no clean comparator** — instruments and CROs
are different businesses, and Stevanato carries the same GLP-1 driver (its own forward P/E went
33.1 → 36.7 post-2023). The comp-spread line is closed. Materiality is 18% of net sales; the reward
at spot against a ratified 2:1 is the test that decides it.

**WAT — the 40% is a NON-FILING disclosure.** GLP-1 testing revenue growth "over 40%" came from the
**Q2-26 earnings call**, and the 10-Q reports the line blended. The `source_ref` must cite the
transcript (`Waters Corporation, Q2 2026 Earnings Call, Aug 04, 2026`), not the 10-Q. A
filings-anchored reader will not find it, which is the exact structural lateness the GLP-1 analyst
note warns about.

**BDX — materiality is UNQUANTIFIED, and the cheapness is not clean.** Its exposure was named in
prose (BioPharma Systems growth attributed to GLP-1, 80+ molecules contracted) with **no dollar
figure**, unlike WST's 18% and WAT's 40%. Against that: 13th percentile of its own forward history,
−18% to peers, **and shares +27% (224m → 283m) with net debt +245% (4,670 → 16,099)**. Cheap
alongside heavy dilution and a 3.4× leverage build is as consistent with company-specific trouble as
with opportunity. **Size the exposure before the cheapness means anything.**

**MCK — re-rated, and the mechanical explanation is ruled out.** 95th percentile of its own forward
history on both `P/NTM EPS` (+62/+71/+73% across 2022/2023/2024 splits) and `TEV/NTM EBITDA`
(+52/+59/+67%). Diluted shares fell **228m → 123m (−46%)**, which pushes a P/E multiple *down*, so
price outran even buyback-inflated earnings; net debt rose ~1,360 against an ~$86bn EV, roughly
**1.6%**, nowhere near a +52–67% EV/EBITDA move. Largest materiality on the sheet (~$15bn quarterly
GLP-1 distribution revenue, +24% YoY) and the most re-rated. Its FY2027 also ends soonest of the four.

## Known blocker on the write path

`scenario-propose` still emits an **R1-shaped template** — it hardcodes `multiple_basis: "EV/EBITDA"`
and revenue/margin stubs, so an R3 record needs both hand-corrected before `scenario-create` accepts
it (STATE.md §5.0 row 10; GOOGL's R3 needed exactly that). Expect the same for these four.
