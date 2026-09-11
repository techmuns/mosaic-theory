---
id:
status: recorded
date: 2026-09-11
prs: []
supersedes:
superseded-by:
---

# WST is WATCHLIST at $326.55 — the verdict moved four times on arithmetic and never on a fact

**WHAT.** **WATCHLIST, limit $326.55, no scenario record.** WST clears asymmetry (**R:R 2.87x**
against a 2.0 bar) and **fails return** (**IRR 13.13%**, minimum band, against a 15% preferred
floor). **NO NEW FACT ABOUT WEST PHARMACEUTICAL APPEARS IN THIS RECORD** — every move came from
correcting how the same three consensus lines were combined.

## The verdict history, recorded because it IS the finding

| round | verdict | what moved it |
|---|---|---|
| 1 | FAIL | — |
| 2 | WATCHLIST @ $327.03 | limit off an interpolated NTM of ~9.65 |
| 3 | **PASS** @ IRR 16.7% | anchor "corrected" to CIQ's NTM 9.276 — **mixed basis** |
| 4 | **WATCHLIST @ $326.55** | same construction at both ends |

**Round 3 was a basis mix, and round 4 lands within $0.48 of round 2** — because the round-2
interpolation was already a correct day-weighted NTM. **Four rounds, one company, zero new
information.**

## CIQ's NTM convention, settled empirically rather than assumed

Neither an FY blend nor a day-weight. **It is the sum of the next four QUARTERLY estimates measured
from the LAST REPORTED quarter-end:**

| rolling 4-quarter window | sum |
|---|---:|
| Q2'26 … Q1'27 | 9.12251 |
| **Q3'26 … Q2'27** | **9.27593** |
| Q4'26 … Q3'27 | 9.61714 |

Against spot ÷ CIQ's own NTM P/E = **9.27590**. **A match to 3 parts in 100,000.** The anchor is
**2026-06-30**, two months before the 2026-09-03 snapshot.

*An earlier reading inferred a "FY2027 weight of 0.315, as if anchored in late April" by solving the
figure as a LINEAR blend of the two annuals. That is an artifact of testing a seasonal quarterly
series with a straight-line instrument: the quarters reconcile to the annuals (FY26 8.96005 vs
8.95851; FY27 9.97143 vs 9.96476) but are not evenly spread. The quarter-sum test is the right
instrument and it is exact.*

## The same-basis violation was the whole verdict

| construction | NTM now | NTM exit | growth | anchor | IRR | band |
|---|---:|---:|---:|---:|---:|---|
| **A — day-weighted, both ends** | **9.6560** | **11.34051** | **+17.45%** | **34.55x** | **13.13%** | minimum |
| B — CIQ convention, both ends | 9.2759 | 10.9802 | +18.37% | 35.96x | 13.82% | minimum |
| ~~MIXED — CIQ near, FY2028 exit~~ | 9.2759 | 11.34051 | ~~+22.26%~~ | 35.96x | ~~16.67%~~ | ~~preferred~~ |

**Both same-basis readings land in the minimum band and agree within 0.7pp.** The result was
basis-robust all along; the mix manufactured the pass.

**CONSTRUCTION A IS RULED**, on data quality and on precedent: A derives the near end from two deep
annual lines and **observes** the far end (FY2028 annual). B does the reverse, deriving its exit by
splitting FY2028 with a FY2027 quarterly shape carrying only **5–6 contributors** — the thinness the
GOOGL memo cites when it refuses FY28 quarterlies as *"standalone Street truth."*

## The legs — construction A, multiples fixed in turns at a stamped price

**Struck at spot $333.59, 2026-09-11. Exit 2027-12-31 (1.3032y). Exit NTM EPS 11.34051.**

| leg | multiple | exit $ | return | IRR | reason |
|---|---:|---:|---:|---:|---|
| **bear** | **28.78x** | **313.31** | −6.1% | −4.70% | the 24-month multiple trough, with the vial haircut on EPS |
| **base** | **34.55x** | **391.79** | +17.4% | **+13.13%** | holds the multiple struck at $333.59 — **fixed, not floating** |
| **bull** | **41.67x** | **472.60** | +41.7% | +30.64% | own quarterly-settled median, n=38 |

**R:R = (391.79 − 333.59) / (333.59 − 313.31) = 2.87x**, against the 2.0 bar. **IRR-15% limit,
base fixed in turns: $326.55.**

**The bear multiple is verified as a trough**: the cleaned daily series' 24-month minimum is
**28.83x** (all-time 26.15x), so 28.78x is that trough to within artifact-cleaning. **The bull is
the own-history median at 41.67x** (this run; the 2026-09-03 record reads 41.7x on the same n=38
population) — and per the `BASIS MATCH: LIMITED` ruling own-history is **corroboration, not a
target-generator**, so the bull leg is the operator's judgment placed AT a reference, not derived
FROM it.

## A LIMIT ONLY EXISTS BECAUSE THE MULTIPLE IS FIXED IN TURNS

Under a floating *"holds current"*, the exit multiple is `P / NTM_now`, so
**`base / P = NTM_exit / NTM_now` — independent of P.** The base return collapses to the EPS growth
rate, and **the IRR gate then passes at every price or at none**; at 13.13% it is none, and no entry
price could ever fix it. That is a property of the RULE, not of West Pharmaceutical.
**`docs/RUNBOOKS.md` step 10 now requires a leg's multiple to be struck once, at a stated price, and
fixed in turns thereafter** — reading GOOGL's bull 26.0x correctly as a fixed figure rather than a
rule that floats with the tape.

## What the base return actually is

**The base return IS the EPS growth rate** — the multiple contributes nothing by construction. So the
whole verdict rests on consensus arriving, and the record states how much of that is operations:

| FY2026 → FY2028 | |
|---|---:|
| EPS Normalized | **+26.59%** |
| Net income (Excl. Excep) | **+23.56%** |
| implied shares | **−2.40%** (71.52m → 69.81m) |

**3.03pp of the EPS growth is share count, not operations.**

*Resolved along the way: CIQ's `EPS Normalized` is DILUTED, not basic. Net income ÷ EPS gives
**71.52m** at FY2026 against the company's own Q2 guidance of "roughly **71.5 million diluted**
shares" — exact. The `Dilution: Basic` label governs that sheet's other ratios. Both 9.276 and
11.34051 come off one row, one basis; there is no share-basis mix.*

## The dated trigger, and why the bear stayed unevidenced

**Four rounds failed to evidence a bear.** The CGM exit and Annex 1 were both disclosed and both sit
inside consensus — management raised FY guidance to **$8.85–$9.05** with 200bps+ margin expansion in
the same breath as the CGM disclosure, so neither is a deviation from the base. The asymmetry passes
because the risk leg is small, and **the risk leg is small because no bear could be evidenced —
absence of found downside, not downside protection.**

**One dated event now exists on the axis the verdict depends on:**

| date | event |
|---|---|
| 2026-03-06 | Green tells the Board he intends to retire (8-K 2026-03-09, item 5.02) |
| 2026-06-01 | 8-K item 5.02: *"appointed Michel Lagarde… **starting August 31, 2026**. He succeeds Eric M. Green"* |
| 2026-07-23 | Q2 call — **outgoing** CEO gives FY guidance $8.85–$9.05 |
| **2026-08-31** | **handover effective** (Form 3 event date, filed 2026-09-10) |
| 2026-09-03 | CIQ consensus snapshot — three days after the handover |
| **~late Oct 2026** | **first print under new management** (prior cadence: Q1 Apr-23, Q2 Jul-23) |

**Nothing company-specific happened in the eight-day window** — the three filings of 2026-09-10 are
Section-16 paperwork for a transition public since June, so the workbook's estimates stand and no
re-pull was needed. **But the consensus the entire return rests on was struck by an outgoing CEO,
three days after his successor took office, with no print since.** A new CEO's first print is the
textbook rebasing opportunity. **It is not a bear leg — no direction, no magnitude, and a new CEO
can raise as readily as rebase — but it is the first dated, scheduled, falsifiable event this name
has produced.**

## TRIGGERS

1. **Price reaches $326.55** (IRR 15% at the struck legs), or
2. **The Q3 2026 print lands, ~late October 2026** — the first under Lagarde. A guidance reset in
   either direction re-underwrites: downward finally evidences the bear four rounds could not, and
   would LOWER the limit; upward moves the base.

**SIZING: WAIT. No starter.** Distinct from the verdict and more conservative than GOOGL's. The
return is entirely EPS delivery, 3.03pp of which is buyback; the bear is unevidenced after four
rounds; the first print under new management is ~six weeks out. **Passing one gate on a number that
moved four times without a fact is not a pass yet.**

## THE THEME READ-OUT

**Four of four shortlisted names were disqualified on their own disclosures, each by a different
mechanism** — BDX counts without a figure, WAT a rate with no base, MCK neutral, CAH not meaningful,
COR dilutive — **with CAH and COR reaching the same conclusion by opposite mechanisms.** The
survivor is an earnings-delivery bet where the multiple contributes nothing, priced within 2% of its
own limit, whose downside cannot be evidenced.

**So the driver is probably real and the fund cannot currently express it.** Per the testability
invariant — two independently-fated names SIZED on the leg being claimed — **the picks-and-shovels
leg fails with one.** The **card is unaffected**: its first-confirming rides the LLY/NVO print cycle
and lands 2026-11-30 regardless. **Two separate outcomes; the memo must not blur them.**

**BOUNDARY.** Estimates: operator's `WestPharmaceuticalServices,IncNYSEWSTEstimatesReport.xls`,
**2026-09-03 pull**, `Consensus` sheet — annual grid row 40 (`EPS Normalized`) and row 156
(`Net Income (Excl. Excep)`), quarterly grid row 269 under the row-268 period header; quarterly
coverage ends **FQ4 2027**, contributor depth 11–14 in FY2026 falling to 5–6 in FY2027. Multiples
from that workbook's `Multiples` sheet (`Dilution: Basic`, Dec fiscal year end). Multiple history:
`WST_Peers_Charting` Pane 1, 2,512 dates × 11 series, **2,506 clean daily observations** after
removing the six revision-lag days, quarterly-settled n=38. Spot **$333.59 @ 2026-09-11** (operator);
the workbook's own last close is $342.63 @ 2026-09-03. Horizon 2026-09-11 → 2027-12-31 = **476 days
= 1.3032y**. Filing timeline from EDGAR live, CIK 105770, read 2026-09-11. USD. No raw CIQ committed;
no scenario record written.

**WHAT IT COSTS / WHAT IS ACCEPTED — checked before claimed.** **The vial haircut is
OPERATOR-SUPPLIED AND NOT RE-DERIVED IN THIS BUILD.** The bear value $313.31 at 28.78x implies exit
EPS **10.8864**, a **−4.00%** haircut against 11.34051; the underlying *"$50m annualized net, 0.88pp
consolidated drag"* derivation was verified in conversation and **is not recoverable from disk** —
searched the session transcripts for both `0.88pp` and `vial`, no hits. It is restated here, not
re-measured. **If the bear leg becomes load-bearing, that derivation must be re-run and recorded**,
because at −4.00% it is the entire distance between the bear and a no-haircut 326.38.
**Second accepted item: construction A's near end is DERIVED** (day-weighting two annuals) while its
exit is observed — the reverse of CIQ's own convention. B was computed as the control and agrees
within 0.7pp of IRR, which is why A's derivation is acceptable rather than merely convenient.
**Falsifier for the whole record: the Q3 print resetting guidance in either direction.**
