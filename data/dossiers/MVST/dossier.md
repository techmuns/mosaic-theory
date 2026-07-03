# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 272 · ref 2026-06-22 · assembled 2026-07-03 15:03 UTC · LLM claude-opus-4-8_

## ⚠ Analyst caveats — verify before the verdict

- Net debt/EBITDA (3.9x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.9x as the covenant-basis leverage.
- Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp; its data is on/after 2026-05-15 (the latest embedded revision event), but the true export date is unknown, so freshness vs the 2026-06-22 reference cannot be confirmed. Re-pull, or corroborate against a dated sibling CIQ export.

## Mechanical layer (source-bound facts — assembles & cites, never concludes)

### Drawdown cause & idiosyncrasy — what happened, and did it happen alone?
- **Shape:** discrete gap-downs by 8-K item code — 2026-03-17 earnings (2.02); 2026-05-12 earnings (2.02); 2026-05-18 no 8-K matched
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- **Gap-down dates:** 2026-03-17, 2026-05-12, 2026-05-18
  - ↳ `EOD gap-down detector (screen events)`
- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**
  - gap 2026-03-17 → 2026-03-16 [`0001628280-26-018235`](https://www.sec.gov/Archives/edgar/data/1760689/000162828026018235/mvst-20260316.htm)
    - items: 2.02 Results of Operations and Financial Condition, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On March 16, 2026, Microvast Holdings, Inc. issued a press release announcing its consolidated financial results for the fourth quarter and year ended December 31, 2025. A copy of the press release and the slideshow is furnished herewith as Exhibit 99.1 and 99.2, respectively to this Current Report on Form 8-K and each is incorporated herein by refere
  - gap 2026-05-12 → 2026-05-11 [`0001628280-26-033601`](https://www.sec.gov/Archives/edgar/data/1760689/000162828026033601/mvst-20260511.htm)
    - items: 2.02 Results of Operations and Financial Condition
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On May 11, 2026, Microvast Holdings, Inc. (the “Company”) issued a press release announcing its unaudited condensed consolidated financial results for the period ended March 31, 2026. In addition, the Company posted an accompanying slideshow presentation to its website summarizing its results for the same period. The full text of the press release is 
- **Revised guidance (catalyst 8-K Ex-99.1):** _UNKNOWN_ — no revised-outlook 99.1 exhibit parsed for 8-Ks ['0001628280-26-018235', '0001628280-26-033601']

_Did it happen alone? (idiosyncratic vs shared — the G2-vs-market compensation):_
- **Name 180d return:** -58.1%
  - ↳ `EOD MVST 180d to 2026-06-22`
- **Market (IWM) 180d return:** 18.0%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -82.2%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — MVST in graph but no US-listed exposed names to price

### Leverage & survival (unified — both bases labeled, no net-vs-total mixing)
- **Net debt / EBITDA (CIQ NET basis):** 3.9x
  - ↳ `CIQ Net Debt $200M [Q1 Mar-31-2026] ÷ CIQ EBITDA $52M [LTM 12 months Mar-31-2026]`
- **Total debt / EBITDA (comps — name vs peer median):** name 5.8x vs peer median 2.0x (comps TOTAL-debt/EBITDA basis)
  - ↳ `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-06-24`
- **Net debt / OCF:** 4.4x
  - ↳ `CIQ Net Debt $200M [Q1 Mar-31-2026] ÷ CIQ OCF $46M [LTM 12 months Mar-31-2026]`
- **Net debt / EBITDA (fwd-adj covenant basis) · EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Interest coverage:** 10.6x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- **Survival (self-funding + nearest wall):** net-debt/EBITDA 3.9x (CIQ) | FCF-positive → self-funding
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign (survival capacity)`
- **Credit health (S&P-MI scores — scale labeled):** name Overall/Operational/Solvency/Liquidity 3/3/2/2 (S&P issuer rating unrated); peer-median O/Op/S/L 2.5/2.5/3/3; scale 1=strongest … 4=weakest (S&P-MI PD model)
  - ↳ `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-06-24`

- **FCF sign:** positive
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** 39.6
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- **Capital structure (instruments) — panel A 2025 filed Mar-16-2026** — ↳ `CIQ Financials→Capital Structure Details (A 2025 filed Mar-16-2026)`  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---|---|---|---|---|---|---|
| Convertible Bond - CNY | Bonds and Notes | $41.7M | 3.000% - 4.000% | NA | 2027-01-31 | Y | Y | CNY |
| Convertible Loan With Shareholder - Delayed Draw Term Loan | Term Loans | $13.0M | NA | SOFR + 9.750% | 2026-05-28 | Y | Y | USD |
| Convertible Loan With Shareholder - Initial Term Loan | Term Loans | $12.0M | NA | SOFR + 9.750% | 2026-05-28 | Y | Y | USD |
| Loan Facilities Agreement With a Group of Lenders Led by a Bank in China | Term Loans | $42.9M | NA | New Benchmark | 2026-12-10 | Y | N | CNY |
| Long-term Loan Agreement With a Chinese Bank | Term Loans | $13.9M | 2.700% | NA | 2027-06-19 | Y | N | CNY |
| Notes Payable | Bonds and Notes | $78.3M | NA | NA | undated | N | N | USD |
| Operating Lease Liabilities | Capital Lease | $17.3M | 5.000% | NA | undated | Y | N | USD |
| Short-term Loan Agreements and Bank Facilities With Chinese Banks | Term Loans | $49.5M | 2.400% - 4.850% | NA | 2027-03-31 | Y | N | USD |

- **Maturity wall** (deterministic, vs the 2026-06-22 reference):
  - **matured (pre-reference): $25.0M** — resolution not in this data; verify each against its 8-K (NEVER assume repaid or defaulted):
    - 2026-05-28 (25d before ref): $13.0M Convertible Loan With Shareholder 
    - 2026-05-28 (25d before ref): $12.0M Convertible Loan With Shareholder 
  - due ≤12m (through 2026): $42.9M — 2026-12-10 $42.9M
  - due 2027: $105.1M
  - undated (floor — no panel maturity): $95.6M — Notes Payable $78.3M, Operating Lease Liabilitie $17.3M
  - _reconciliation: itemized $268.6M (panel A 2025 filed Mar-16-2026) vs the latest-quarter aggregates below — the gap is unitemized / newer term loans; read the QoQ movement in the aggregates line._
- **Capital-structure aggregates (latest quarter):** term loans 215.2 (131.3→215.2 QoQ); senior bonds 94.0; leases 16.8; total principal 326.0; total debt 326.0 (latest quarter) ($M)
  - ↳ `CIQ Financials→Capital Structure Summary`
- **8-Ks at instrument maturities:** 8-K at maturity 2026-05-28: filed 2026-05-28 [0000947871-26-000585] 5.02 Departure/Election of Directors or Certain Officers, 8.01 Other Events, 9.01 Financial Statements and Exhibits — read for resolution
  - ↳ `EDGAR 8-K submissions (±10d of instrument maturities)`
- **Maturity resolution (8-K verbatim):** On May 28, 2026, Mr. Wu delivered a Notice of Conversion in respect of the full $25.0 million principal amount outstanding under the Loan Agreement. Such principal amount will be converted into shares of common stock of the Company in accordance with the terms of the Loan Agreement.
  - ↳ `8-K 0000947871-26-000585 (2026-05-28)`
- **Covenant / contract pointers (CIK-verified execution filings)** — ↳ `EDGAR 10-K exhibit index + CIK-scoped efts (agreement-class, exhibit-bearing)`  <!-- ds-table -->

|  | Filing | Date | Accession / exhibit (or note) |
|---|---|---|---|
| material contracts (10-K exhibit index) | latest 10-K | 2026-03-16 | 0001628280-26-018264 — mvst20251231-ex1013.htm, mvst20251231-ex1021.htm |
| Convertible Loan | 8-K | 2025-03-17 | 0000947871-25-000313 — ss4588423_ex1001.htm |
| Convertible Loan | 8-K | 2024-06-04 | 0001760689-24-000021 — wu_microvast-guarantyagree.htm, wu_microvast-loanandsecuri.htm, wu_microvast-pledgeagreeme.htm |
| Loan Facilities Agreement | 8-K | 2022-09-29 | 0001760689-22-000094 — exhibit101-syndicatedloana.htm |
| Notes Payable | — | — | no contract-level filing expected (aggregate line item) |
| Operating Lease Liabilities | — | — | no contract-level filing expected (aggregate line item) |

- **Covenant terms — Convertible Loan (governing; Tier-2 fenced)** — ↳ `fenced Tier-2 extraction (verbatim, source-bound)`  <!-- ds-table -->

|  | Governing value (verbatim, or UNKNOWN) | Source § (base · amended by) |
|---|---|---|
| Conversion price / mechanics | Conversion Price = $1.00 divided by the applicable Conversion Rate. Conversion Rate = two (2) shares of Common Stock (subject to adjustment) per $1.00 principal amount of the Loans. Partial-conversion minimum: portion to be converted must be $100,000 principal amount, or an integral multiple of $100,000 in excess thereof. Conversion right exercisable at any time prior to the Close of Business on the Scheduled Trading Day immediately preceding the Maturity Date. | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm |
| Principal / commitment amount | Initial Term Loan Commitment: $12,000,000. Delayed Draw Term Loan Commitment: $13,000,000. (Annex I: Yang Wu 100.00% of each.) | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm |
| Interest / coupon rate | Term SOFR (for the applicable Interest Period) + Applicable Margin; Applicable Margin = 9.75% per annum; 3.75% of interest paid in-kind (PIK Interest); Floor = 3.00% per annum; Default Rate = Applicable Margin + 3.00% per annum. | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm |
| Maturity date | “November 28, 2025” in clause (a) of the definition of “Maturity Date” is deleted and replaced with “May 28, 2026”. | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm · amended by 0000947871-25-000313 |
| Financial-maintenance covenants | Minimum Liquidity: from the Closing Date until the Maturity Date, Liquidity of Borrower and its Subsidiaries as of Friday of each calendar week (each a "Liquidity Testing Date") not less than $5,000,000. | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm |
| Security / collateral / guarantors | Guarantors (signature pages): MICROVAST HOLDINGS, INC. (Holdings and a Guarantor); MICROVAST ADVANCED MATERIALS INC.; MICROVAST ADVANCED MEMBRANE INC.; MICROVAST ENERGY, INC.; MICROVAST POWER SOLUTIONS, INC.; MICROVAST GMBH. Borrower: MICROVAST, INC. Agent/Collateral Agent: ACQUIOM AGENCY SERVICES LLC. Liens and rights securing payment of the Obligations are ratified and confirmed by each Loan Party. | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm · amended by 0000947871-25-000313 |
| Mandatory prepayment / events of default | This Amendment references (but does not define) "Default" and "Event of Default" as conditions/representations; no mandatory-prepayment provision or event-of-default definition is stated in this Amendment. (Condition: "no Default or Event of Default shall have occurred and be continuing or shall be caused by this Amendment.") | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm · amended by 0000947871-25-000313 |

- **Covenant terms — Loan Facilities Agreement (governing; Tier-2 fenced)** — ↳ `fenced Tier-2 extraction (verbatim, source-bound)`  <!-- ds-table -->

|  | Governing value (verbatim, or UNKNOWN) | Source § (base · amended by) |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Principal / commitment amount | aggregate amount up to RMB 800,000,000.00 yuan (Eight hundred million yuan). Annex I Initial Commitments: Bank of China, Huzhou Branch RMB 250 million; China Construction Bank, Huzhou Branch RMB 250 million; Bank of Huzhou, Co. RMB 150 million; China Zheshang Bank, Huzhou Branch RMB 150 million. | 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Interest / coupon rate | Floating rate; 12-month floating period. RMB lending floating rate = latest one year LPR published by the National Interbank Funding Center (one Business Day before the applicable date) Plus 115 bps. Reset on each anniversary of the first disbursement date. Late Default Interest Rate: 150% of applicable Interest Rate; Misappropriation Default Interest Rate: 200% of applicable Interest Rate. Interest calculated on daily basis: daily interest rate = annual rate/360. | 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Maturity date | December 10, 2026 (5 years in total). Availability Period ends 9 June 2023. Repayment schedule (Ten Thousand Yuan): 6/10/2023 3000; 12/10/2023 7000; 6/10/2024 10000; 12/10/2024 10000; 6/10/2025 10000; 12/10/2025 10000; 6/10/2026 15000; 12/10/2026 15000. | 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Financial-maintenance covenants | Article 14.1 clause 9 (Financial indicator): 'The Borrower shall meet the following financial indicators: [/]' — no specific indicators stated (left blank). Related stated covenants: Article 14(3) 'the Borrower shall ensure that the final total financing balance for the Project does not exceed RMB 800 million, and the final proportion of equity funds is not less than 45%'; Article 14.1 clause 10 'The Borrower shall ensure that the equity fund of the Project in an amount of RMB 500 million is in place before the disbursement of Loans'. | 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Security / collateral / guarantors | Mortgagor / Pledgor: Microvast Power Systems Co., Ltd. Mortgage Contract: three mortgage contracts (#HuKai 2022 C113, #HuKai 2022 C114, #HuKai 2022 C115) signed 1 September 2022. Guarantor: [/] (blank). Guarantee Contract: signed on [/] (blank). Pledge Contract: in respect of [/] signed on [/] (blank). Security Documents = Guarantee Contract/Maximum Guarantee Contract, Mortgage Contract/Maximum Mortgage Contract and/or Pledge Contract/Maximum Pledge Contract. Article 14(1): 'The property and equipment of the Project will be mortgaged to the syndicate when they are available for the mortgage.' Debt Service Reserve Account required (Article 6.3). | 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Mandatory prepayment / events of default | Events of Default (Art 15.1): 1. Misrepresentation; 2. Breach of contract/other obligations; 3. Payment default; 4. Material payment default (fails to pay for two consecutive times or three times in total); 5. Misappropriation of loans; 6. Cross default (fails to repay any due Indebtedness of RMB 1000 or more); 7. Insolvency (deferred repayment/restructuring RMB 1,000,000 or more; stops/suspends payments); 8. Liquidation and bankruptcy events; 9. Enforcement events (assets RMB 30,000,000 or more sealed/frozen not released within 90 Business Days); 10. Financial indicators (fails to meet Clause 9); 11. Material Adverse Effects; 12. Invalidity of Finance Documents. Remedies (Art 15.2 clause 3) include acceleration of Outstanding Loans, cancellation of Total Commitments, additional security, enforcing Security Documents. Compulsory cancellation on change of control (Art 7.4): 'The Agent (acting on instructions of all Lenders ) shall, after giving at least 10 Business Days' prior notice to the Borrower , require the Borrower to prepay the loans and cancel the Total Commitments.' Change in law (Art 11): Borrower shall within 10 Business Days prepay Lenders Affected by Change in Law. Voluntary prepayment (Art 7.1): minimum RMB 30,000,000.00 in integer multiples of RMB 30,000,000.00, 30 Business Days' notice. | 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |

- **Covenant terms — material contracts (10-K exhibit index) (governing; Tier-2 fenced)** — ↳ `fenced Tier-2 extraction (verbatim, source-bound)`  <!-- ds-table -->

|  | Governing value (verbatim, or UNKNOWN) | Source § (base · amended by) |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Principal / commitment amount | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Interest / coupon rate | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Maturity date | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Financial-maintenance covenants | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Security / collateral / guarantors | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Mandatory prepayment / events of default | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Instrument type | Restricted Stock Unit Award Agreement under the Microvast Holdings, Inc. 2021 Equity Incentive Plan | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Vesting schedule | One-third of the RSUs vest on each of the first, second, and third anniversaries of the Grant Date | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Settlement | One Share per vested RSU, or at the Company's option the cash value (Fair Market Value of a Share on the applicable Vesting Date); settled no later than March 15 of the year following vesting | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Forfeiture on termination | Unvested RSUs forfeited for no consideration on Termination of Employment; on Termination for Cause, all RSUs (vested but not settled or unvested) forfeited | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Change in Control | Unvested RSUs treated per the Plan; vested unsettled RSUs settled immediately prior to the Change in Control | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Dividend Equivalents | Dividend Equivalents credited and converted into additional RSUs; subject to same vesting/settlement terms as the corresponding Award | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Clawback | Subject to clawback/recoupment per applicable law and Company policy | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Governing law | State of Delaware | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Transfer restrictions | RSUs not assignable or transferable except by will or laws of descent and distribution | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |


### Trajectory (revenue · EBITDA · margins · ROIC)
- **Trajectory ($M · % — per period)** — ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`  <!-- ds-table -->

|  | Dec-2021 | Dec-2022 (R) | Dec-2023 (R) | Dec-2024 | Dec-2025 | Mar-2026 (LTM) |
|---|---|---|---|---|---|---|
| Revenue ($M) | 152 | 204 | 307 | 380 | 428 | 372 |
| EBITDA ($M) | -180 | -140 | -85 | 5 | 74 | 52 |
| EBITDA margin | -118% | -68% | -28% | 1% | 17% | 14% |
| Gross margin | -28% | 4% | 19% | 31% | 36% | 35% |
| ROIC | -24.5% | -12.3% | -8.7% | -2.2% | 3.3% | 1.5% |

_Revenue YoY (latest same-quarter): -25.5% (Q1 Mar-31-2026 vs Q1 Mar-31-2024). R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** diluting (trailing ~1.7y): 323,815,298 (2024-08-05) → 333,157,384 (2026-05-04), +2.9%
  - ↳ `EDGAR XBRL shares, trailing 2024-08-05..2026-05-04`

### Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 11.1x vs peer median 14.5x (-23%); P/E NM vs peer median 39
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
- **Implied expectations (price-inverted · multiples-space)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _price-implied fundamental levels at stated multiples — the human judges earned vs residual; identity (†): at the name's own multiple the implied level IS consensus._
  - _TEV as-of 2026-06-24 · multiples as-of 2026-05-15_
- **Implied metric levels · fixed multiple set** — ↳ `TEV = mcap 423.1 + net debt 199.9 (CIQ Comparable Analysis→Financial Data, Latest, as-of 2026-06-24) — simple-TEV basis`  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **7.54x** | **$82.6M EBITDA †** |
| peer-median NTM TEV/EBITDA | 12.9x | $48.3M EBITDA |
| peer-median LTM TEV/EBITDA | 14.5x | $43.0M EBITDA |
| **name NTM TEV/Rev** | **1.26x** | **$494.4M Revenue †** |
| peer-median NTM TEV/Rev | 2.55x | $244.3M Revenue |
| peer-median LTM TEV/Rev | 3.2x | $194.7M Revenue |

- **Consensus path anchors (EBITDA — juxtapose, do NOT difference):** FY26E $62.1M · FY27E $147.7M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue — juxtapose, do NOT difference):** FY26E $444.4M · FY27E $591.5M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)
  - _vintage-coherent: derived FY26 $61.4M vs direct consensus $62.1M (residual 0.010 ≤ 0.10 tolerance)_
  - _Fixed multiple set (declared in code, no per-name curation): name NTM + peer-median NTM/LTM, on TEV/EBITDA and TEV/Rev._

- **P/E:** _UNKNOWN_ — no positive EPS/price
- **EV/EBITDA (GAAP TEV/LTM):** 10.0x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **Own-history range position:** EV/EBITDA (TEV/LTM) 10.0x as-of 2026-03-31 — trailing range 15.8–66.9x (median 24.9x) over 4 closes → LOW-CONFIDENCE (4 closes < 8q ≈2y) — floor read unreliable
  - ↳ `CIQ Financials→Multiples (Close; last col = current, excluded from history)`

### Peer comps (CIQ Comparable Analysis — consensus comp, framed to RESIST)
- **Peer set (roster · caps · business)** — ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| Amprius Technologies | $2.0B | develops, manufactures, and markets lithium-ion (United States) |
| Forsee Power S.A. | $34M | designs, manufactures, and sells battery systems for (France) |
| Cummins Inc. | $96.5B | offers various power solutions worldwide. The company (United States) |
| BorgWarner Inc. | $14.5B | provides technology solutions for combustion, hybrid, (United States) |
| Contemporary Amperex Technology Co. | $275.0B | engages in the research, development, production, and (China) |
| Panasonic Holdings Corporation | $64.4B | develops, manufactures, sells, services, and supplies (Japan) |
| Leclanché SA | $167M | designs, develops, and manufactures customized turnkey (Switzerland) |
| Samsung SDI Co. | $24.8B | manufactures and sells batteries in South Korea, (Gyeonggi-do South) |

_the name: $423M_

- **Comparability (confidence gate):** market caps span $34M–$275.0B (8063x); the name is $423M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM)** — ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| TEV/Rev | 1.7 | 0.7 | 3.2 | 5.8 | 22 |
| TEV/EBITDA | 11.1 | 7.9 | 14.5 | 18.5 | 38.4 |
| P/E | NM | 22.6 | 39 | 38.9 | 54.9 |
| NTM TEV/Rev | 1.25 | 1.06 | 2.55 | 3.64 | 13.47 |
| NTM TEV/EBITDA | 7.46 | 7.63 | 12.9 | 43.3 | 198.12 |
| NTM P/E | 14.11 | 13.27 | 22.77 | 26.23 | 55.1 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · margin · growth · leverage — name vs peers)** — ↳ `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-06-24`  <!-- ds-table -->

|  | Cap | EBITDA margin | Rev growth (1y) | EBITDA growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|
| Contemporary Amperex Technology Co. | $275.0B | 24% | 28% | 29% | 1.1 | 42,108 (net cash) |
| Cummins Inc. | $96.5B | 15% | 0% | 0% | 1.6 | 5,058 |
| Panasonic Holdings Corporation | $64.4B | 9% | -5% | 1% | 2.0 | 5,157 |
| Samsung SDI Co. | $24.8B | 4% | -9% | -66% | 24.2 | 6,518 |
| BorgWarner Inc. | $14.5B | 14% | 2% | 2% | 2.0 | 1,963 |
| Amprius Technologies | $2.0B | -19% | 173% | – | NM | 56 (net cash) |
| **Microvast Holdings · the name** | **$423M** | **14%** | **-10%** | **21%** | **5.8** | **200** |
| Leclanché SA | $167M | -265% | 32% | – | NM | 100 |
| Forsee Power S.A. | $34M | -10% | -21% | – | NM | 63 |
| Peer median (peers) | $19.7B | 6% | 1% | 1% | 2.0 | 1,031 |


### Implied valuation (CIQ-computed at peer multiples — POSED, not concluded)
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Composition first — the human judges earned vs residual (not a machine upside)._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 423.1
  - ↳ `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-06-24`
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $126.10M, − total debt $326.00M
  - ↳ `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-06-24`
- **Implied EQUITY value ($M, CIQ)** — ↳ `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-06-24`  <!-- ds-table -->

|  | Low | Median | Mean | High |
|---|---|---|---|---|
| LTM Total Revenue | 64.3 | 1,004.4 | 1,963.7 | 7,962.6 |
| LTM EBITDA | 212.5 | 550.7 | 760.2 | 1,794.7 |
| LTM EBIT | 21.8 | 193.9 | 163.1 | 242.9 |
| NTM Revenue (Capital IQ) | 329.6 | 1,070.4 | 1,616.4 | 6,521.1 |
| NTM EBITDA (Capital IQ) | 437.0 | 877.0 | 3,415.6 | 16,341.2 |
| NTM EPS (Capital IQ) | 397.9 | 682.6 | 786.5 | 1,652.1 |
| LTM Tangible Book Value/Share | 385.1 | 2,139.1 | 2,972.4 | 8,131.3 |



### Catalyst path (estimates · guidance · revisions) — export date unverified (data ≥ 2026-05-15)
- **Horizon read (FQ — next-2Q revision breadth)** — ↳ `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`:
  - EPS Normalized FQ3 2026: 1m 0↑/0↓, 2m 1↑/0↓, 3m 1↑/0↓
  - Revenue FQ2 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - Revenue FQ3 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - EBIT FQ2 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - EBIT FQ3 2026: 1m 0↑/0↓, 2m 1↑/0↓, 3m 1↑/0↓
  - Interest Expense FQ2 2026: 1m 0↑/0↓, 2m 1↑/0↓, 3m 1↑/0↓
  - Interest Expense FQ3 2026: 1m 0↑/0↓, 2m 1↑/0↓, 3m 1↑/0↓
  - EBT (GAAP) FQ2 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - EBT (GAAP) FQ3 2026: 1m 0↑/0↓, 2m 1↑/0↓, 3m 1↑/0↓
  - Net Income (GAAP) FQ2 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - _no revisions in any window: EPS Normalized FQ2 2026, EPS (GAAP) FQ2 2026, EPS (GAAP) FQ3 2026, EBITDA FQ2 2026, EBITDA FQ3 2026_
- **Acceleration read (monthly consensus path):** FY 2026 EPS Normalized: 0.24 (12m) → 0.29 (9m) → 0.20 (6m) → 0.06 (3m) → 0.06 (2m) → 0.04 (1m) → 0.04 (latest); net -83% (12m→latest) | FY 2026 EPS (GAAP): 0.09 (12m) → 0.11 (9m) → 0.09 (6m) → 0.05 (3m) → 0.05 (2m) → 0.18 (1m) → 0.18 (latest); net +100% (12m→latest) | FY 2026 Revenue: 609.0 (12m) → 593.9 (9m) → 544.2 (6m) → 480.5 (3m) → 480.5 (2m) → 444.4 (1m) → 444.4 (latest); net -27% (12m→latest) | FY 2026 EBITDA: 129.7 (12m) → 146.5 (9m) → 146.5 (6m) → 62.1 (1m) → 62.1 (latest); net -52% (12m→latest) [3m, 2m n/a] | FY 2026 EBIT: 46.1 (12m) → 52.8 (9m) → 43.4 (6m) → 22.5 (3m) → 22.5 (2m) → 20.0 (1m) → 20.0 (latest); net -57% (12m→latest) | FY 2026 Interest Expense: -13.7 (12m) → -4.61 (9m) → -4.81 (6m) → -5.02 (3m) → -5.02 (2m) → -4.91 (1m) → -4.91 (latest); improving (magnitude toward zero) (12m→latest) | FY 2026 EBT (GAAP): 37.0 (12m) → 59.4 (9m) → 38.8 (6m) → 17.6 (3m) → 17.6 (2m) → 73.1 (1m) → 73.1 (latest); net +98% (12m→latest) | FY 2026 Net Income (Excl. Excep): 92.7 (12m) → 92.6 (9m) → 21.4 (3m) → 21.4 (2m); net -77% (12m→2m) [6m n/a] | FY 2026 Net Income (GAAP): 33.4 (12m) → 42.3 (9m) → 32.9 (6m) → 17.6 (3m) → 17.6 (2m) → 70.1 (1m) → 70.1 (latest); net +110% (12m→latest)  [data ≥ 2026-05-15 · export date unverified]
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
- **Cross-name anchor (NTM forward-multiple ladder)** — ↳ `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`:
  - NTM: TEV/REV 1.26 · TEV/EBITDA 7.54 · TEV/EBIT 17.55 · Price/Earnings 14.33 · PEG –
  - FY 2026: TEV/REV 1.42 · TEV/EBITDA 10.14 · TEV/EBIT 31.54 · Price/Earnings 32.25 · PEG –
  - FY 2027: TEV/REV 1.06 · TEV/EBITDA 4.26 · TEV/EBIT 9.17 · Price/Earnings 8.60 · PEG –
  - FY 2028: TEV/REV 0.83 · TEV/EBITDA 3.47 · TEV/EBIT 5.35 · Price/Earnings – · PEG –
  - _+5 later fiscal years in JSON_
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — ↳ `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)`  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| Revenue | 427.5 | FY 2026 | 2026-03-16 | 98d (stale) | actual ≥ floor 10/13 | FY 2025 MISSED |
| Capital Expenditure | '(180.00) - (210.00)' | FY 2023 | 2023-11-10 | 955d (stale) | spend ≤ ceiling 4/4 | FY 2023 MET |
| Gross Margin % | '32.00 - 35.00' | FY 2025 | 2025-11-10 | 224d (stale) | actual ≥ floor 4/4 | FY 2024 MET |

- **Consensus stats (target + ratings):** Target price: mean $5.50, median $5.50, high/low 6.00/5.00, N 2/2; Ratings: Buy 2, Outperform 0, Hold 0, Underperform 0, Sell 0, No Opinion 0  [data ≥ 2026-05-15 · export date unverified]
  - ↳ `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
- **Revision-event log** (47 events · 3 broker-days) — ↳ `CIQ Estimates→Recent Changes (47 broker revision events)  [data ≥ 2026-05-15 · export date unverified]`:
  - **2026-05-15 · H.C. Wainwright & Co.** — Upward Revision×3, Initiation of Coverage×9, Downward Revision×6:
    - Revenue FY 2026: 563.49→438.83 (cons 450.0→444.41)
    - EBITDA FY 2026: 146.5→62.08 (cons -→62.08)
    - EBIT FY 2026: 63.58→21.96 (cons 17.96→19.96)
    - Net Income (GAAP) FY 2026: 47.54→69.84 (cons 70.43→70.13)
    - EBT (GAAP) FY 2026: 59.42→75.69 (cons 70.43→73.06)
    - _+13 more line items in JSON_
  - **2026-05-11 · broker undisclosed** — Upward Revision×5, Downward Revision×8:
    - Net Income (GAAP) FY 2026: 17.63→70.43 (cons 17.63→70.43)
    - EBT (GAAP) FY 2026: 17.63→70.43 (cons 17.63→70.43)
    - Revenue FY 2026: 480.52→450.0 (cons 480.52→450.0)
    - Revenue FQ2 2026: 103.21→95.91 (cons 103.21→95.91)
    - EBIT FY 2026: 22.46→17.96 (cons 22.46→17.96)
    - _+8 more line items in JSON_
  - **2026-03-17 · broker undisclosed** — Downward Revision×16:
    - Net Income (Excl. Excep) FY 2026: 92.58→21.38 (cons -→21.38)
    - Revenue FY 2026: 525.0→480.52 (cons 525.0→480.52)
    - Net Income (Excl. Excep) FQ2 2026: 16.86→0.45 (cons -→0.45)
    - Gross Margin % FY 2026: 34.0→27.9 (cons -→27.9)
    - Gross Margin % FQ2 2026: 33.8→28.0 (cons -→28.0)
    - _+11 more line items in JSON_
- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2022 +0%, FY2023 +0%, FY2024 +0%, FY2025 +0%; Revenue surprise: FY2021 +3%, FY2022 +2%, FY2023 +3%, FY2024 +6%, FY2025 -8% (GAAP-EPS basis; +beat / −miss)
  - ↳ `CIQ Estimates→Surprise (annual)`
- **Insider activity (Form 4, 6m):** Open-market buys 0 · sells 7 (net -121.0K sh) · grants 20 · last 2026-06-12 · other C×1
  - ↳ `EDGAR Form 4 (latest 0000947871-26-000620; 18 in 6m)`
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-06-15): 21.4M → 26.3M sh (+22.9%, rising) · 7.9% of shares out (EDGAR XBRL) · DTC 5.7d · recent: 2026-06-15 26.3M · 2026-05-29 21.4M · 2026-05-15 21.6M · 2026-04-30 21.2M
  - ↳ `FINRA consolidated short interest (settle 2026-06-15); DTC = 26,323,600 short ÷ 4,607,454 screen 90d ADV`

### Concentration
- **Segments (revenue share):** [12 months Dec-31-2025] Batteries / Battery Systems 428 (100%) of Total 428
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** Ashok Leyland Limited (NSEI:ASHOKLEY) — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2025 Form 10-K; BAIC BluePark New Energy Technology Co., Ltd. (SHSE:600733) — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Cargotec Solutions LLC — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Jbm Electric Vehicles Private Limited — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Kinglong United Automotive Industry (Suzhou) Co., Ltd — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; TREPEL Airport Equipment GmbH — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2025 Form 10-K
  - ↳ `CIQ Customers&Suppliers Microvast Holdings Inc NasdaqCM MVST Customers.rtf`
- **Geographic:** [12 months Dec-31-2025] China 139 (33%); Other Asia & Pacific 3 (1%); Italy 93 (22%); France 78 (18%); Other Europe 41 (10%); U.S. 39 (9%); India 35 (8%) of Total 428
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** mixed — a genuine multi-year EBITDA/FCF turn and self-funding balance sheet set against a 48% revenue collapse, high leverage, and slashed forward estimates.

### Bull case (overshoot / mean-revert)
- The name is FCF-positive (LTM levered FCF +$39.6M) and self-funding, with interest coverage of 10.6x — the balance sheet is servicing itself rather than burning toward a raise.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- The $25.0M convertible shareholder loans maturing 2026-05-28 were resolved by a full conversion-to-equity notice from Mr. Wu, removing that near-term maturity wall (dilutive, but not a default/cash-drain event).
  - ↳ `8-K 0000947871-26-000585 (2026-05-28)`
- On the fundamental_deltas the name screens BETTER than the peer median on the metrics that carry the discount — EBITDA margin 14% vs 6% and EBITDA growth 21% vs 1% — so at least part of the TEV/EBITDA discount is unexplained by fundamentals and POSES a residual-overshoot question for the human (not a computed upside).
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Gross margin has held resilient through the volume collapse — Q1-26 gross margin 31.6% versus 36.9% a year prior despite revenue down 48% — indicating pricing/mix power rather than a margin structure breaking down.
  - ↳ `CIQ Financials→Income Statement (quarterly, trailing 8Q)`
- Absolute EBITDA turned sharply positive over four years — from -180 (Dec-2021) to +74 (Dec-2025), with margin now 17% at FY25 — a genuine operating inflection, not a one-quarter blip.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Consensus GAAP net income and EBT for FY26 were revised sharply UPWARD into the latest snapshot (Net Income GAAP net +110%, EBT GAAP net +98% 12m→latest), and both covering analysts rate the name Buy.
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`

### Bear case (terminal / value-trap)
- Leverage is the REAL signal, not optical: total-debt/EBITDA 5.8x is nearly 3x the peer median 2.0x and net-debt/EBITDA is 3.9x — the discount is at least partly EARNED by a genuinely weaker balance sheet.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-06-24`
- Revenue is contracting hard, not merely optically: Q1-26 revenue $60.6M was down 48% YoY driven by volume falling from ~536MWh to ~274MWh, and LTM revenue ($372M) has rolled over below the FY25 print ($428M) — the top line is genuinely shrinking.
  - ↳ `CIQ Financials→Income Statement (quarterly, trailing 8Q)`
- The consensus EBITDA and revenue paths were cut severely into the latest snapshot — FY26 EBITDA -52% and FY26 revenue -27% (12m→latest) — a genuine deterioration in the forward operating outlook, not a timing artifact.
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
- The Q1-26 headline GAAP net profit of $48.2M is an optical MISREAD — management states it rests on a $63.8M non-cash fair-value gain on warrant/convertible liabilities, with an underlying adjusted net LOSS of $14.6M and adjusted EBITDA of -$5.5M YTD versus +$28.5M prior year.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- The headline TEV/EBITDA discount (11.1x vs peer median 14.5x) is a MISREAD as a clean cheapness signal — the peer set spans $34M to $275B (8063x) and is HETEROGENEOUS, so the median is anchored by businesses of unlike scale and model and cannot be read as a benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- Beta of 3.5 versus peer-median 1.1 shows the discount is partly EARNED by far higher risk, and short interest is rising (21.4M→26.3M shares, +22.9%, 7.9% of float) — the market is leaning against the name, not merely ignoring it.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The stock has massively underperformed on an idiosyncratic basis — down 58% over 180d while the small-cap index rose 18%, a -82% relative move that is name-specific, not a shared-cohort drawdown.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`

### Decisive question
**Is the Q1-26 volume/revenue collapse a temporary Phase-3.2 ramp-and-timing trough that reverses as capacity comes online through 2026 — or the start of durable demand erosion that turns the leveraged balance sheet into a value trap?**

### …evidence for
- Management frames the Q1-26 YoY dip as temporary and tied to Phase-3.2 production timing aligning with customer demand, expecting a continued revenue ramp through 2026.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- Consensus revenue is modeled to reaccelerate to $591.5M in FY27 from $444.4M FY26E, and FY27 EBITDA to $147.7M — consistent with a ramp-recovery rather than terminal decline.
  - ↳ `CIQ Estimates→Trends (FY26/FY27 consensus Revenue, latest snapshot)`
- The prior FY22→FY25 arc shows the name has already converted a scaling story into positive absolute EBITDA and FCF, evidence the ramp mechanism can work.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`

### …evidence against
- Consensus FY26 revenue was cut -27% and FY26 EBITDA -52% (12m→latest), showing analysts materially marking down the ramp they were counting on.
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
- The most recent resolved revenue guidance (FY2025) was MISSED, and management attributed the shortfall to Korea regulatory shifts and EMEA platform ramp delays — external demand headwinds that may persist.
  - ↳ `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)`
- Underlying (ex non-cash) profitability already turned negative in Q1-26 — adjusted EBITDA -$5.5M YTD vs +$28.5M prior year — so the trough is hitting real economics, not just optics.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`

### Key unknowns
- No adjusted/forward EV/EBITDA, adjusted EPS, or adjusted net-debt/EBITDA in the revised 99.1 guidance — the forward valuation basis is MISSING, so trailing 10.0x cannot distinguish cheap-overshoot from cheap-terminal (an opaque forward picture, a bearish gap).
- No revised-outlook 99.1 exhibit was parsed for either gap-down 8-K — the actual guidance management gave at the two decline events is UNKNOWN.
- No segment-level EBITDA disclosure (Segments sheet lacks an EBITDA section) — with revenue 100% in one battery-systems segment, profitability by product/region is opaque.
- Cash-runway visibility against 2026-2027 maturities (Chinese bank term loans, CNY convertible bond due 2027, notes payable with no stated maturity date) is not quantified beyond FCF-positive — refinancing/rollover risk on the China-heavy debt stack is unresolved.
- Financial-maintenance covenants exist (Minimum Liquidity on the convertible loan; a financial-indicator article in the Loan Facilities Agreement) but the actual thresholds and current headroom are not in the supplied facts.
- Customer concentration magnitude is UNKNOWN — customers are named but no revenue share per customer is disclosed.
- The peer set is HETEROGENEOUS (caps span 8063x) so every peer multiple and delta must be treated as a confidence-gated input, not a clean benchmark; the true comparable sub-scale battery cohort is not isolated.
- Export date of the estimates/consensus pull is unverified (a floor of ≥2026-05-15), so the freshness of the revision path is uncertain.

### Twin reference cases
- **QuantumScape** — went terminal (LLM-claimed — verify)
  - distinguished by: SPAC-era battery story trading on a multi-year technology promise (here solid-state and the KAF school-bus powertrain) while near-term volumes and revenue disappoint — the pattern of a narrative deck outrunning the shipped P&L.
  - source: [LLM-suggested, unverified]
- **Romeo Power** — went terminal (LLM-claimed — verify)
  - distinguished by: commercial-vehicle battery-pack integrator dependent on customer platform ramps that slipped, with concentrated customers and a single product segment — the pattern of demand-timing risk in a 100%-battery-systems name.
  - source: [LLM-suggested, unverified]
- **Amprius Technologies** — recovered
  - distinguished by: in-roster peer battery name of small scale that sustained a high-growth narrative; the analogue is a small battery maker whose equity re-rated on ramp progress rather than trailing profitability.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Forsee Power S.A.** — went terminal
  - distinguished by: in-roster micro-cap battery-systems peer with negative EBITDA margin and shrinking revenue — the pattern of a sub-scale battery maker unable to reach durable profitability.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)


## APPENDIX — FINANCIAL SUMMARY (actuals + consensus estimates) — export date unverified (data ≥ 2026-05-15)
### Annual (last-4-FY + LTM + FY26E/FY27E consensus)
- **Annual financials ($M; E = consensus)** — ↳ `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`  <!-- ds-table -->

|  | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|
| Revenue ($M) | 204 | 307 | 380 | 428 | 372 | 444 | 592 |
| Revenue growth | — | +50% | — (basis) | +13% | — (basis) | +4% (vs FY25) | +33% |
| EBITDA ($M) | -140 | -85 | 5 | 74 | 52 | 62 | 148 |
| EBITDA margin | -68% | -28% | 1% | 17% | 14% | 14% | 25% |
| EBIT ($M) | -160 | -108 | -26 | 40 | 19 | 20 | 69 |
| Net income ($M) | -158 | -106 | -196 | -29 | -43 | 70 | 56 |
| EPS (GAAP, dil.) | -0.52 | -0.34 | -0.61 | -0.09 | -0.19 | 0.18 | 0.17 |
| EPS (Normalized) | -0.33 | -0.21 | -0.22 | 0.00 | -0.03 | 0.04 | 0.15 |
| CFO ($M) | -54 | -75 | 3 | 76 | 46 | — | — |
| Capex ($M) | -151 | -187 | -28 | -20 | -20 | — | — |
| FCF (levered, CIQ) | -136 | -117 | -65 | 18 | 40 | — | — |

_E = consensus (Estimates→Trends 'Current'), as-of ≥2026-05-15; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_

### Trailing 8 quarters (the recent-quarter trajectory)
- **Quarterly financials** — ↳ `CIQ Financials→Income Statement (quarterly, trailing 8Q)`  <!-- ds-table -->

|  | Q2-24 | Q3-24 (R) | Q4-24 (R) | Q1-25 (R) | Q2-25 | Q3-25 | Q4-25 | Q1-26 |
|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 84 | 101 | 113 | 116 | 91 | 123 | 96 | 61 |
| Gross margin | 33% | 33% | 37% | 37% | 35% | 38% | 35% | 32% |
| EBITDA ($M) | -4 | 12 | 12 | 22 | 18 | 23 | 11 | 0 |
| EBITDA margin | -5% | 12% | 11% | 19% | 19% | 19% | 11% | 0% |
| Revenue QoQ | — | — (basis) | +12% | +3% | — (basis) | +35% | -22% | -37% |
| Revenue YoY | — | — | — | — | +9% | — (basis) | — (basis) | — (basis) |

_QoQ/YoY same-basis only; (R) = Reclassified_

### Balance-sheet posture
- **Posture:** as of Q1-26 ($M): cash & ST inv 126; total debt 326; net debt 200; equity 466; net working capital -18; net-debt/EBITDA → see the Leverage & survival block (not recomputed)
  - ↳ `CIQ Financials→Balance Sheet (quarterly, Q1-26)`
- **Coherence — BS vs implied-valuation bridge:** cash BS $126M / bridge $126M; debt BS $326M / bridge $326M — reconcile with the implied-valuation bridge.
  - ↳ `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`

### Management commentary (transcript POINTER — read the file; not a machine excerpt)
- **Earnings call:** 2 earnings-call transcript(s) on file — read in full for management posture: Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`

---
> **No BUY/AVOID here — this dossier only assembles and cites.** The verdict is the human's, logged separately via the ledger with a frozen entry price.