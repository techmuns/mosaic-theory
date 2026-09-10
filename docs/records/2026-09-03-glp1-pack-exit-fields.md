---
id:
status: recorded
date: 2026-09-03
prs: []
supersedes:
superseded-by:
---

# Three exit fields added to the step-10 pack — and WAT's consensus is on a post-acquisition share base

**BOUNDARY.** Source: operator's CIQ exports read 2026-09-03 through `CiqBundle`. Exit **31 Dec 2027**
(operator's date). Consensus = `Estimates→Consensus`; share actuals = `Financials→Income Statement`
diluted weighted. USD, $m except per-share. Recipe stays **`R3_forward_pe`**. No raw CIQ committed.

## The completed pack

| | spot | NTM EPS @exit | NTM EBIT @exit | net debt @exit | implied shares @exit | FY end |
|---|---|---|---|---|---|---|
| WST | 342.63 | **11.34** | 952 | **−1,039** (net cash) | 71m | Dec-31 |
| WAT | 412.20 | **18.53** | 2,274 | 2,557 | **98m** | Dec-31 |
| MCK | 924.78 | **55.69** | 8,188 | 3,407 | 115m | Mar-31 |

## Flows are day-weighted; stocks are interpolated to the date

Not the same operation, and conflating them is wrong in both directions:

* **EPS and EBIT are FLOWS** over the NTM window (31 Dec 2027 → 31 Dec 2028) → day-weighted across
  the fiscal years the window straddles.
* **Net debt and share count are STOCKS at an instant** → interpolated to the exit date itself.

**This is what makes MCK's March close comparable to WAT's December, and it cannot be read off an FY
column.** For a December filer the NTM window *is* FY2028, so WST/WAT take FY2028E directly. For MCK
the window straddles two fiscal years:

> NTM EPS = **0.25 × FY2028E (50.46) + 0.75 × FY2029E (57.43) = 55.69**

Neither FY figure is right on its own — reading FY2028 understates by 9%, FY2029 overstates by 3%.
Net debt, being a stock, interpolates differently again: 75.1% of the way from MCK's FY2027 balance
(4,070) to FY2028 (3,188) = **3,407**.

> **A first cut of this got MCK wrong**, returning FY2029 outright with weights of 1.00/0.00 — on the
> single name the field exists for. Caught by hand-checking the blend against 0.25/0.75, which is the
> only reason it is right above.

## The share count is DERIVED, not taken from the latest actual

CIQ consensus carries no share-count forecast, but it carries `Net Income (Excl. Excep)` and
`EPS Normalized`, so the count consensus is *using* is recoverable:

> implied diluted shares = Net Income (Excl. Excep) ÷ EPS Normalized

| | implied @exit | latest actual | gap |
|---|---|---|---|
| WST | 71m | 72m | −2% |
| MCK | 115m | 123m | −7% |
| **WAT** | **98m** | **75m** | **+31%** |

WST and MCK reconcile, and MCK's −7% is simply its buyback continuing — which is the correct forward
figure to use rather than today's 123m.

## WAT's 31% gap is the BD Biosciences acquisition, and it has two consequences

Its own Key Developments file states it plainly: *"The BD Biosciences and BD Diagnostic Solutions
businesses have been acquired by Waters Corporation."* Consensus is therefore on the **enlarged,
post-deal share base**, while the latest reported diluted weighted average still reflects the
pre/partial-deal period.

**1 — The EV bridge must use 98m, not 75m.** An enterprise value built from today's share count
against consensus EBIT mismatches numerator and denominator by ~30%. Since `R3_forward_pe` values
per-share, this does not touch the primary construction — but it does touch the **EV/NTM EBIT
cross-check**, which is the corroborating basis under the LIMITED ruling.

**2 — It changes what WAT's materiality means.** WAT entered the shortlist on *"GLP-1 testing part of
the business grew over 40% this quarter"*. That growth rate is on the **pre-acquisition** base, while
the company being underwritten is materially larger and more diversified. The 40% is unaffected as a
statement about the testing line; what changes is its **weight in the whole**. Not disqualifying —
WST's 18% of net sales and MCK's ~$15bn are shares of their own bases too — but the prong was
measured before the denominator moved, and the underwrite should say so.

## Recipe unchanged

**`R3_forward_pe` stays.** GOOGL runs the trade on EPS methods with EV/NTM direct EBIT as the
corroborating cross-check, not the primary construction — the multiple remains an analyst judgement
corroborated by a denominator that is a reported line. The pack did not need rebuilding; it needed
these three fields.

## What is still the operator's

Ratify the two axis methods (§5.0 row 20 — both `ratified: None` under the only confirmed position);
confirm **31 Dec 2027** with the ~5-quarter deviation recorded against a mandate preferring one to
three; set the multiple triplet per name. Three names: **WST, WAT, MCK**.
