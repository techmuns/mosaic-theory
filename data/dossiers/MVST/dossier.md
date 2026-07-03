# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 272 · ref 2026-06-22 · assembled 2026-07-03 12:17 UTC · LLM claude-opus-4-8_

## ⚠ Analyst caveats — verify before the verdict

- Net debt/EBITDA (3.9x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.9x as the covenant-basis leverage.
- Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp; its data is on/after 2026-05-15 (the latest embedded revision event), but the true export date is unknown, so freshness vs the 2026-06-22 reference cannot be confirmed. Re-pull, or corroborate against a dated sibling CIQ export.
- (E5) exhibit not extracted (cost bound): Loan Facilities Agreement·exhibit101-syndicatedloana.htm
- (E5) exhibit not extracted (cost bound): material contracts (10-K exhibit index)·mvst20251231-ex1013.htm

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
- **Covenant / contract pointers (CIK-verified execution filings)** — ↳ `EDGAR 10-K exhibit index + CIK-scoped efts (agreement-class, exhibit-bearing)`  <!-- ds-table -->

|  | Filing | Date | Accession / exhibit (or note) |
|---|---|---|---|
| material contracts (10-K exhibit index) | latest 10-K | 2026-03-16 | 0001628280-26-018264 — mvst20251231-ex1013.htm, mvst20251231-ex1021.htm |
| Convertible Loan | 8-K | 2025-03-17 | 0000947871-25-000313 — ss4588423_ex1001.htm |
| Convertible Loan | 8-K | 2024-06-04 | 0001760689-24-000021 — wu_microvast-guarantyagree.htm, wu_microvast-loanandsecuri.htm, wu_microvast-pledgeagreeme.htm |
| Loan Facilities Agreement | 8-K | 2022-09-29 | 0001760689-22-000094 — exhibit101-syndicatedloana.htm |
| Notes Payable | — | — | no contract-level filing expected (aggregate line item) |
| Operating Lease Liabilities | — | — | no contract-level filing expected (aggregate line item) |

- **Covenant terms (Tier-2, fenced — verbatim, source-bound)** — ↳ `fenced Tier-2 extraction (verbatim, source-bound)`  <!-- ds-table -->

|  | Value (verbatim, or UNKNOWN) | Source (exhibit · verbatim quote) |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0000947871-25-000313 · ss4588423_ex1001.htm |
| Principal / commitment amount | UNKNOWN | not stated in 8-K 0000947871-25-000313 · ss4588423_ex1001.htm |
| Interest / coupon rate | UNKNOWN | not stated in 8-K 0000947871-25-000313 · ss4588423_ex1001.htm |
| Maturity date | “November 28, 2025” in clause (a) of the definition of “Maturity Date” is deleted and replaced with “May 28, 2026” | 8-K 0000947871-25-000313 · ss4588423_ex1001.htm — verbatim: ““November 28, 2025” in clause (a) of the definition of “ Maturity Date ” is deleted and replaced with “May 28, 2026”.” |
| Financial-maintenance covenants | UNKNOWN | not stated in 8-K 0000947871-25-000313 · ss4588423_ex1001.htm |
| Security / collateral / guarantors | Guarantors: Microvast Holdings, Inc. (as Holdings and a Guarantor), Microvast Advanced Materials Inc., Microvast Advanced Membrane Inc., Microvast Energy, Inc., Microvast Power Solutions, Inc., Microvast GmbH; Liens securing the Obligations ratified and confirmed (amount/description of collateral not stated in this Amendment) | 8-K 0000947871-25-000313 · ss4588423_ex1001.htm — verbatim: “each of the Subsidiaries of Holdings listed as a “Guarantor” on the signature pages hereto (each such Guarantor, together with Holdings and Borrower,… |
| Mandatory prepayment / events of default | As a condition to effectiveness: “no Default or Event of Default shall have occurred and be continuing or shall be caused by this Amendment”; representation that “there exists no Default or Event of Default… after giving effect to this Amendment” (definitions/mandatory prepayment provisions not set out in this Amendment) | 8-K 0000947871-25-000313 · ss4588423_ex1001.htm — verbatim: “no Default or Event of Default shall have occurred and be continuing or shall be caused by this Amendment; ... there exists no Default or Event of De… |
| Agent | Acquiom Agency Services LLC, as administrative agent and collateral agent | 8-K 0000947871-25-000313 · ss4588423_ex1001.htm — verbatim: “ACQUIOM AGENCY SERVICES LLC, as administrative agent and collateral agent for the Lenders (in such capacity, “Agent”)” |
| Lender / Initial Lender | Yang Wu (Initial Lender) | 8-K 0000947871-25-000313 · ss4588423_ex1001.htm — verbatim: “YANG WU (the “Initial Lender” and, together with the Initial Lender’s permitted successors and assigns from time to time, collectively, the “Lenders”… |
| Underlying agreement / date | Loan and Security Agreement dated May 28, 2024 | 8-K 0000947871-25-000313 · ss4588423_ex1001.htm — verbatim: “that certain Loan and Security Agreement ... dated May 28, 2024, by and among Holdings, Borrower, the other Loan Parties party thereto, YANG WU ... a… |
| Amendment date | March 17, 2025 | 8-K 0000947871-25-000313 · ss4588423_ex1001.htm — verbatim: “THIS FIRST AMENDMENT TO LOAN AND SECURITY AGREEMENT (this “Amendment”) is entered into as of March 17, 2025” |
| Governing law | State of New York | 8-K 0000947871-25-000313 · ss4588423_ex1001.htm — verbatim: “THIS AMENDMENT SHALL BE A CONTRACT MADE UNDER AND GOVERNED BY THE INTERNAL LAWS OF THE STATE OF NEW YORK” |
| Fees and expenses | Borrower pays Agent and Lenders' reasonable and documented out-of-pocket expenses per Section 10.4 of the Loan Agreement | 8-K 0000947871-25-000313 · ss4588423_ex1001.htm — verbatim: “The Borrower agrees to pay all reasonable and documented out-of-pocket expenses of Agent and the Lenders in connection with the preparation, negotiat… |
| Conversion price / mechanics | Conversion Price = "$1.00 divided by the applicable Conversion Rate at such time." Conversion Rate (Section 2.12): "a rate (the “ Conversion Rate ”) of two (2) shares of Common Stock (subject to adjustment by the Borrower as provided in Section 2.12.4 ) per $1.00 principal amount of the Loans (the “ Conversion Obligation ”)." Partial-conversion minimum (Section 2.12): "convert all or any portion (if the portion to be converted is $100,000 principal amount, or an integral multiple of $100,000 in excess thereof) of its Loans at any time prior to the Close of Business on the Scheduled Trading Day immediately preceding the Maturity Date". Section 16 Conversion Blocker (Section 2.12.10(a)): Restricted Ownership Percentage "exceed 9.99% (the “ Restricted Ownership Percentage ”) of the total issued and outstanding shares of Common Stock". | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm — verbatim: ““ Conversion Price ” means at any time an amount equal to $1.00 divided by the applicable Conversion Rate at such time.” |
| Principal / commitment amount | Initial Term Loan Commitment: $12,000,000 (Closing Date). Delayed Draw Term Loan Commitment: $13,000,000 (Closing Date). Annex I: YANG WU — Initial Term Loan Commitment $12,000,000.00 (100.00%); Delayed Draw Term Loan Commitment $13,000,000.00 (100.00%); TOTALS: $12,000,000 and $13,000,000. | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm — verbatim: “The aggregate principal amount of the Initial Term Loan Commitments on the Closing Date is $12,000,000. ... The aggregate principal amount of the Del… |
| Interest / coupon rate | Rate = Term SOFR + Applicable Margin. "Applicable Margin" means 9.75% per annum. Floor: "Floor" means a rate of interest equal to 3.00% per annum. PIK: "the Borrower shall pay 3.75% of the interest due on each Loan on each interest payment date in-kind rather than in cash ... (such amount, the “ PIK Interest ”)." Default Rate: "the Applicable Margin ... shall be increased by three percentage points (3.00%) per annum (the resulting rate, the “ Default Rate ”)". | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm — verbatim: “The Borrower promises to pay interest on the unpaid principal amount of each Loan for the period commencing on the date of such Loan until such Loan … |
| Maturity date | Earliest to occur of (a) November 28, 2025 and (b) the date the Obligations are accelerated or terminated. | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm — verbatim: ““ Maturity Date ” means the earliest to occur of (a) November 28, 2025, and (b) the date on which the Obligations are accelerated or terminated pursu… |
| Financial-maintenance covenants | Minimum Liquidity: not less than $5,000,000, tested as of Friday of each calendar week (each a "Liquidity Testing Date"), from Closing Date until Maturity Date. "Financial Covenant" means the financial covenant set forth in Section 7.13. | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm — verbatim: “7.13.1 Minimum Liquidity . From the Closing Date until the Maturity Date, not permit Liquidity of the Borrower and its Subsidiaries, as of Friday of … |
| Security / collateral / guarantors | First priority (subject to Permitted Liens) security interest in substantially all property of Borrower and each Subsidiary Guarantor (and Holdings as to Pledged Equity of Borrower), excluding Excluded Property. Guarantors (signature pages): MICROVAST HOLDINGS, INC. (Holdings and a Guarantor); MICROVAST ADVANCED MATERIALS INC.; MICROVAST ADVANCED MEMBRANE INC.; MICROVAST ENERGY, INC.; MICROVAST POWER SOLUTIONS, INC. Guarantee Agreement dated as of Closing Date by and among the Loan Parties and the Agent. | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm — verbatim: “As security for the payment of the Obligations, each of the Borrower and each Subsidiary Guarantor (and, solely in the case of the Pledged Equity con… |
| Mandatory prepayment / events of default | Mandatory prepayment (Section 2.9.2): 100% of Net Cash Proceeds of debt issuances/other Debt incurrence (iii); 100% of Net Cash Proceeds of a Disposition (iv); immediately upon Change of Control, 100% of principal of Loans and all other Obligations then outstanding (v); 100% of Net Cash Proceeds of a Casualty/Condemnation Event (vii); 100% of Net Cash Proceeds of an Extraordinary Receipt (viii). Events of Default (Section 8.1) include: 8.1.1 Non-payment of Obligations; 8.1.2 Default under other Debt; 8.1.3 Bankruptcy/Insolvency; 8.1.4 Breach of certain covenants (with 30-day cure for certain); 8.1.5 Representations and warranties false/misleading in material respect; 8.1.6 Pension Plans (ERISA Event with MAE); 8.1.7 Judgments exceeding $50,000; 8.1.8 Invalidity of Loan Documents; 8.1.9 Invalidity of Liens; 8.1.10 Change of Control; 8.1.11 Certain Material Events. Remedies (Section 8.2): upon Section 8.1.3 EoD, Commitments terminate and Loans/Obligations immediately due and payable together with the Applicable Prepayment Premium (if any). | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm — verbatim: “2.9.2 Mandatory Prepayment . (a) Borrower shall prepay the Term Loans ... (iii) concurrently with the receipt by Holdings or any of its Subsidiaries … |


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
- **Consensus path anchors (Revenue — juxtapose, do NOT difference):** FY26E $438.7M · FY27E $587.7M · NTM $494.4M (consensus Revenue = TEV ÷ forward ladder; NTM = the name-NTM identity)
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

**Evidence balance:** mixed — a genuine multi-year profitability inflection collides with a fresh, sharp revenue collapse and deep consensus cuts that are still unresolved.

### Bull case (overshoot / mean-revert)
- The name is FCF-positive ($39.6M levered FCF LTM) with FCF turning from -$136M (2022) to +$40M LTM, making it self-funding rather than dependent on external capital.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Interest coverage of 10.6x (EBITDA/interest) sits comfortably above distress despite the leverage, indicating debt service is not the near-term binding constraint.
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- On operating fundamentals the name screens BETTER than the peer median (EBITDA margin 14% vs 6%; EBITDA growth 21% vs 1%), posing whether its discount to the peer-median TEV/EBITDA is RESIDUAL (overshoot) rather than EARNED — though this must be read against a HETEROGENEOUS peer set spanning $34M–$275B caps, not a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Forward consensus shows revenue and EBITDA re-accelerating (FY26E $438.7M/$62.1M EBITDA → FY27E $587.7M/$147.7M), and the forward multiple ladder compresses sharply (NTM TEV/EBITDA 7.54x → FY27 4.26x), posing whether the trailing 10.0x reads cheap-terminal or cheap-overshoot.
  - ↳ `CIQ Estimates→Trends (FY26/FY27 consensus EBITDA, latest snapshot)`
- Absolute EBITDA has swung from -$180M (2021) to +$74M (2025) and +$52M LTM, with EBITDA margin moving -118% → +17% → +14% LTM — a genuine multi-year profitability inflection, not just an optical margin swing.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`

### Bear case (terminal / value-trap)
- Leverage is elevated and worse than peers — net-debt/EBITDA 3.9x and total-debt/EBITDA 5.8x vs peer-median 2.0x — a genuine EARNED component of the discount that the strong operating margins do not fully offset.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-06-24`
- The reported GAAP net profit is misleading: Q1-26's $48.2M GAAP 'profit' rests on a $63.8M non-cash fair-value gain, with management disclosing an ADJUSTED net LOSS of $14.6M and YTD adjusted EBITDA of NEGATIVE $5.5M vs +$28.5M prior year — underlying earnings deteriorated sharply.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- Revenue is contracting hard: Q1-26 fell to $61M, down 48% YoY per management and -37% QoQ, and LTM revenue ($372M) has already rolled over from the FY25 peak ($428M) — the top-line ramp thesis is reversing, not compounding.
  - ↳ `CIQ Financials→Income Statement (quarterly, trailing 8Q)`
- Consensus was slashed across the board after two earnings gap-downs — FY26 revenue cut 609 → 444 (-27%) and FY26 EBITDA 129.7 → 62.1 (-52%) over the revision window — confirming the ramp story is being repriced downward, not just optically.
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
- The name is a single-segment battery pure-play (100% Batteries/Battery Systems) with elevated beta 3.5 vs peer-median 1.1, offering no diversification against the sector-wide margin and subsidy pressure management flagged.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- Rising short interest (21.4M → 26.3M shares, +22.9%; 7.9% of float) and net insider selling (0 buys vs 7 open-market sells) signal no smart-money conviction on the recovery.
  - ↳ `FINRA consolidated short interest (settle 2026-06-15); DTC = 26,323,600 short ÷ 4,607,454 screen 90d ADV`
- The trailing TEV/EBITDA of 10.0x is a trailing-only read with no forward basis to distinguish cheap-overshoot from cheap-terminal, and the 5y percentile floor read is LOW-CONFIDENCE (only 4 closes < 2y history) — the 'cheap' optic is not a reliable signal.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`

### Decisive question
**Is the sharp Q1-26 revenue collapse (-48% YoY, -37% QoQ) a temporary Phase-3.2 ramp/subsidy-transition dip that reverses into the FY27 re-acceleration consensus models, or the start of a structural volume decline that makes the trailing 10.0x a value trap?**

### …evidence for
- Management frames the Q1 dip as temporary, tied to Phase 3.2 capacity timing aligning with customer demand and expecting a continued revenue ramp through 2026, with SOP targeted in 2026.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- Consensus still models FY27 revenue re-accelerating to $587.7M and EBITDA to $147.7M, well above the LTM base, with forward multiples compressing accordingly.
  - ↳ `CIQ Estimates→Trends (FY26/FY27 consensus EBITDA, latest snapshot)`
- Gross margin held at 31.6% in Q1-26 despite the volume drop, which management cites as evidence of resilient premium positioning through the trough.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`

### …evidence against
- The most recently resolved FY25 revenue guide MISSED, and management attributed the shortfall to Korea regulatory shifts and EMEA platform delays — the same causes now recurring, suggesting a persistent rather than one-off headwind.
  - ↳ `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)`
- Consensus FY26 revenue and EBITDA were cut -27% and -52% respectively over the revision window and FY26 revenue guide is stale (98d old), showing analysts repricing the ramp downward through two earnings gap-downs.
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
- YTD adjusted EBITDA swung to NEGATIVE $5.5M from +$28.5M a year prior, indicating the underlying trough is deeper than the trailing $52M EBITDA figure implies.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`

### Key unknowns
- No revised-outlook 99.1 exhibit was parsed from either earnings 8-K — revised forward guidance is UNKNOWN, an opacity risk given two consecutive guide-down gap-downs.
- No adjusted (forward) EV/EBITDA, adjusted EPS, or adjusted net-debt/EBITDA in the revised guidance — the forward-clean-earnings basis needed to judge overshoot-vs-terminal is missing.
- No segment-level EBITDA disclosure (Segments sheet has no EBITDA section) — cannot see whether profitability is concentrated or broad within the single battery segment.
- Covenant terms are UNKNOWN (extract pending from located exhibits) — with two SOFR+9.75% convertible shareholder term loans maturing 2026-05-28 and multiple 2026–2027 maturities, refinancing/covenant risk is unquantified; a maturity-date 8-K (2026-05-28) exists and must be read for resolution.
- Two-analyst coverage only (N=2, both Buy, target $5.50) — thin, low-breadth consensus; conviction is fragile.
- Export date of the CIQ estimates pull is unverified (a floor ≥ 2026-05-15) — the revision/consensus snapshot may be staler than the true latest.
- Peer set is HETEROGENEOUS (caps span 8063x) — every peer-median multiple must be treated as a confidence-gated input, not a clean benchmark, before any discount is read as overshoot.

### Twin reference cases
- **Plug Power** — went terminal (LLM-claimed — verify)
  - distinguished by: US-listed clean-energy hardware pure-play that reported headline growth and margin milestones while burning through capital and repeatedly cutting guidance, with the market discounting the ramp narrative as perpetually deferred.
  - source: [LLM-suggested, unverified]
- **Romeo Power** — went terminal (LLM-claimed — verify)
  - distinguished by: SPAC-listed EV battery pack maker whose thin single-segment customer base and volume shortfalls left absolute profitability unable to keep pace with capacity commitments.
  - source: [LLM-suggested, unverified]
- **QuantumScape** — recovered (LLM-claimed — verify)
  - distinguished by: Battery technology name whose narrative rested on next-generation solid-state milestones and patent breadth ahead of commercialization — the same forward-optionality framing management leans on here.
  - source: [LLM-suggested, unverified]
- **Forsee Power S.A.** — went terminal
  - distinguished by: In-roster peer battery-systems maker at micro-cap scale with negative EBITDA margin and contracting revenue — the archetype of a de-rated small battery name where the discount proved EARNED.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Amprius Technologies** — recovered
  - distinguished by: In-roster US battery peer priced on rapid forward revenue growth despite negative trailing EBITDA — the case where the market pays through a trailing loss for an accelerating ramp.
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