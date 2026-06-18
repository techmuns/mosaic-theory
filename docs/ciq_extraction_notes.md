# CIQ Extraction Reference

Critical rules for LLM extracting from CIQ files. Empirically validated against real CIQ exports. Generic to any name.

This file is consult-as-needed. The most important rules are duplicated in Session B PM PROVIDES in checklist.md — this file exists for the cases where LLM hits an edge case the inline rules don't cover.

---

## File format reality

CIQ extensions mislead about actual format. Always verify with `file` command before parsing; never trust the extension:

| Extension | Actual format | Parser to use |
|---|---|---|
| `.xls` | Legacy BIFF (Excel 97-2003 binary) | `xlrd` library only. openpyxl fails with explicit error. |
| `.rtf` (Key Developments) | Real RTF text | `striprtf` library |
| `.rtf` (Transcripts, some Annual Reports) | OLE Composite Document (MS Word .doc renamed) | LibreOffice CLI (`libreoffice --headless --convert-to txt`) or MS Word required. NO RTF library will parse this. striprtf silently returns ~12 words of garbage. |
| `.doc` (formal regulatory filings from CIQ: 10-Q, 10-K, 20-F, Yuho, Annual Report, Half-year, etc.) | MIME-wrapped quoted-printable HTML | Three-step pipeline: (1) decode quoted-printable via `quopri.decodestring`, (2) parse with `BeautifulSoup`, (3) `html.unescape` the extracted text. The file starts with MIME headers (X-Sender, boundary, Content-Type) — skip past these. python-docx fails (not a real .doc). |
| `.pdf` (Annual Report book vs 10-K) | Either glossy shareholder report OR the formal 10-K — must distinguish (see SEC filings section below) | `pdftotext -layout` for text PDFs; `pdfinfo` for page count (do not trust `file` command's PDF page count — it's frequently wrong) |

**Warning emitted by xlrd:** "file size not 512 + multiple of sector size (512)" — harmless, ignore.

**Production implication for transcripts:** if the sandbox lacks LibreOffice, the disguised-DOC transcript cannot be auto-extracted. PM must either pre-convert (MS Word → Save As .txt or .pdf) or paste relevant sections directly. LLM must detect garbage output (very low word count from a multi-MB file) and surface to PM rather than attempt fabricated content.

**Production implication for 10-Q/10-K:** the MIME-wrapped HTML decoding pipeline is non-obvious. If LLM gets text containing `=3D`, `=20`, or `&#8217;` entities, the quoted-printable + HTML-entity decoding step was skipped. The decoded output should be clean prose with no `=` continuation artifacts.

---

## Formal annual & interim regulatory filings — which document, when, and why

Three distinct documents that CIQ may export as PDF or RTF, sometimes mislabeled informally. Framework requires the correct one. **Jurisdiction-aware equivalents are listed for the formal regulatory filings — use whichever applies to the issuer's primary listing.**

| Document type | Frequency | US-listed (domestic) | FPIs on US exchanges | UK/EU/HK/SG/AU | Japan | Korea | Required for B3? |
|---|---|---|---|---|---|---|---|
| Formal annual filing | Annual | **10-K** | **20-F** | **Annual Report** (formal regulatory filing) | **Yuho** (有価証券報告書) | **Business Report** | YES — load-bearing for risk-factor enumeration, business/segment description, full-year MD&A, full revenue disaggregation, contractual obligations, segment footnotes |
| Formal interim filing | Quarterly / Half-yearly | **10-Q** | **6-K** (where filed) | **Half-year report** | **Quarterly Report** (四半期報告書) | **Quarterly Report** | YES — load-bearing for most-recent-period customer concentration, geographic exposure, material changes since annual filing |
| Glossy Annual Report book (shareholder mailing) | Annual | — same in all jurisdictions: marketing material — | NO — does not contain the formal items the framework's B3 quality flags require |

**Distinguishing the formal annual filing from the glossy shareholder mailing at upload time:**

For US 10-K / 20-F: starts with "UNITED STATES SECURITIES AND EXCHANGE COMMISSION" boilerplate, table of contents listing Items 1-15 (10-K) or 1-19 (20-F), contains Item 1A "Risk Factors" enumeration, typically 100-300 pages of text-dense legal/financial language.

For non-US formal annual filings (UK Annual Report, Yuho, Business Report): also dense regulatory document with statutory section headings, audited financial statements, risk factor disclosures per jurisdiction's standard. NOT a glossy publication.

Glossy Annual Report book (mailed with proxy in any jurisdiction): cover art, shareholder letter from CEO in first 5-10 pages, accolade pages (industry awards, ESG ratings), 50-150 pages with image-heavy content. May embed the formal 10-K (or jurisdiction equivalent), may not. Even when it does embed, the wrapper material consumes context window and obscures Item structure.

**Timing through the year (which combination of filings B3 needs):**
- If today is within ~60 days of fiscal year-end → only the prior formal annual filing is available; no recent interim filing yet. Use the annual alone with a note that the most-recent quarter's customer concentration / geographic exposure is unavailable until the next interim filing.
- If today is mid-fiscal-year → need BOTH the latest formal annual filing (filed up to ~14 months ago covering the prior fiscal year) AND the latest formal interim filing (filed within ~60 days, covering most recent quarter/half-year). The annual provides the structural disclosures; the interim provides freshness on customer concentration, geographic, and material changes.
- If today is just after a fiscal year-end but before annual filing → use the trailing interim filings (or four trailing 10-Qs / two trailing half-year reports to approximate the annual basis) and surface the annual-pending status to PM.

**If only the glossy shareholder Annual Report book is provided (no formal regulatory filing):**
- LLM must explicitly downgrade B3 quality flags to "interim-only basis" and surface to PM with a request to upload the formal annual filing (or the regulator's URL — SEC EDGAR for US/FPI, Companies House for UK, EDINET for Japan, DART for Korea, equivalent for others).
- Do NOT silently substitute glossy-book content for formal-filing content — they are not equivalent on the dimensions B3 evaluates.
- Specifically, the formal risk factor enumeration, segment footnote, and contractual-obligations table cannot be derived from the glossy book.

---

## Universal data-handling rules (apply to all CIQ files)

1. **Missing data:** Empty cells, `'-'` (hyphen), and `"Entitlement Needed"` all mean UNAVAILABLE. Never fabricate, estimate, or interpolate. Surface to PM with options: re-export with different settings, source externally per data_sources.md, or proceed with the gap noted.

2. **Date format varies across sheets in the SAME file family, and even WITHIN the same file:**
   - String dates (`'12 months\nJan-31-2024'`, `'Jun-30-2025'`): Income Statement, Balance Sheet, Cash Flow, Holders columns
   - Excel serial dates (`45657.0` = 2024-12-31): Financials → Multiples, Estimates → Recent Changes, Charting
   - **Already-decoded datetime (no serial conversion needed):** Insider Trading file's `Trade Date Range` and `Filed Date` columns. CIQ converts these at export time. LLM doing serial conversion on these gets NaN.
   - Always test column type with `pd.api.types.is_datetime64_any_dtype(df[col])` before assuming serial-conversion is needed.
   - Conversion of serials when needed: `datetime(1899, 12, 30) + timedelta(days=serial)`

3. **Forward-fill sparse-attribution columns.** Insider Trading file groups multi-transaction entries under a single holder name on the first row, then blanks the holder name on subsequent rows. Always `df['Holder Name'].ffill()` before any per-holder analysis.

4. **Header position is not fixed.** Charting exports vary header row by chart type. Scan column 0 for "Pricing Date" or "Date" string; header is that row, data starts at header+1. Do not hardcode positions.

5. **CIQ tier gating.** "Entitlement Needed" string in any field means PM's CIQ subscription does not include that specific data point. Count the underlying event (e.g., a revision exists in the database) but mark the detail as UNAVAILABLE.

---

## Transaction Type filtering (Insider Trading) — DIRECTION-FLIP RISK

**The most consequential extraction error in the framework if mis-specified.** Naive total-shares-sold sum produces directionally wrong outputs because mechanical option-exercise transactions appear identical to discretionary sales in unfiltered data. A real-data example: naive sum reads $232M of insider selling → bearish; correct discretionary signal is ~$28M of buys vs ~$1M of sells → bullish.

**Empirically verified Transaction Type categories in real CIQ exports** (not the hypothetical category names previously listed in this file — those were guesses; these are the actual values that appear):

| Transaction Type | Discretionary signal? | Treatment |
|---|---|---|
| `Open Market Acquisition` | YES (real BUY) | Include in discretionary-buy total. This is the load-bearing positive signal. |
| `Open Market Disposition` | YES (real SELL) | Include in discretionary-sell total. |
| `Sale` | NO (mechanical) | CIQ uses this category for option-exercise tax-cover sales and similar mechanical disposition events, NOT for discretionary open-market selling. Discretionary sells appear under `Open Market Disposition` (see above). Always exclude `Sale` rows from discretionary signal — they are the disposition leg of a `Derivative Exercise and Sale` and CIQ already classifies the transaction type as non-discretionary. |
| `Derivative Exercise and Sale` | NO (mechanical) | Combined-view row for paired exercise + disposition. CIQ may emit THREE rows for one cashless exercise: this combined-view row + a separate `Derivative Exercise` (exercise leg) + a separate `Sale` (disposition leg). All three rows represent the SAME underlying transaction. Excluding all three from discretionary signal correctly counts the transaction as zero discretionary signal (it is mechanical). |
| `Derivative Exercise` | NO (mechanical) | Option/RSU vest. No signal. Exclude. |
| `Derivative Exercise and Retained Stock` | NO (mechanical) | Vest with no sale. Exclude. |
| `Other Derivative Acquisition` | NO (mechanical) | RSU grants, ESPP. Exclude. |
| `Other Acquisition` | RARELY (depends on context) | Could be merger consideration, gift received — verify per case. Default exclude unless context indicates discretionary. |
| `Sale to Issuer` | NO (mechanical) | Company buying back restricted stock from departing officers. Not a market signal. |
| `Intent to Sell (Form 144)` | NO (duplicate) | Form 144 is the SEC filing announcing intent to sell. The actual transaction is recorded in a separate row on the same date for the same holder with the same shares — empirically the matching row is `Open Market Disposition` (when the actual sale is discretionary) OR `Derivative Exercise and Sale` (when the sale is mechanical exit from vested options). **Naive sum double-counts.** Exclude all Form 144 rows from totals; they are filings, not transactions. |
| `Initial Statement of Beneficial Ownership (Form 3)` | NO (administrative) | Officer/director initial filing. Not a transaction. Exclude. |
| `Other Disposition` | NO (gift/donation) | Transaction Value = 0 indicates non-market transfer (charitable donation, gift, intra-family transfer). No information content about insider's view of valuation. Exclude from discretionary signal. Identified by: Transaction Value = 0 AND Price Range = "-". |

**Required pre-processing pipeline:**
1. `df['Holder Name'].ffill()` — CIQ blanks Holder Name on subsequent rows of multi-leg transactions. Without ffill, ~75% of rows are misattributed (verified empirically: 722 of 982 rows blank in real export).
2. Drop footnote rows: filter out rows where Holder Name contains "denotes", "footnote", "Note:", or other legend markers.
3. Convert `Trade Date Range` to datetime if not already (see date-format rule above — Insider Trading is one of the columns that's already datetime, no serial conversion).
4. Filter to material discretionary categories per table above.
5. Apply materiality floor: ignore individual transactions below $50,000 unless they cluster (3+ insiders trading same direction within a 30-day window — consistent with checklist B3 item u cluster criterion).

**10b5-1 plan invisibility caveat:** CIQ has NO column flagging which sales are pre-arranged 10b5-1 plan sales (mechanical, scheduled in advance, lower information content) vs discretionary (insider-chose-to-sell-now). This information is in SEC EDGAR Form 4 footnotes, not CIQ structured exports. Framework treats all `Open Market Disposition` as discretionary by default; PM should flag uncertainty and cross-reference EDGAR for high-stakes signals.

**Activist position detection:** large `Open Market Acquisition` by a filer with NO insider role keyword in any parenthetical (i.e., not a board member adding to their personal stake; an external institutional or fund accumulator). Use the same insider-detection logic specified in the Holders section above — keyword-based, case-sensitive: `Director`, `Officer`, `Founder`, `CEO`, `CFO`, `CTO`, `COO`, `Chairman`, `President`, `EVP`, `SVP`, with listing-reference parens excluded. Flag as potential activist position when ANY of: single transaction >$10M, OR accumulated >1% of shares outstanding within 90 days, OR accumulated >$25M across multiple trades within 90 days. CIQ Holders file's largest-mover analysis will also surface this; cross-reference for verification. Note: insiders (board members, officers) adding to their personal stakes are signal but are NOT activist positions — they go through item v (insider activity) not item m/n (institutional). Activist flag triggers a Session B narrative item: the activist's public stance on the name (if any) should be searched and surfaced to PM.

---

## Common extraction edge cases

## Financials export — per-subsheet frequency requirements

The CIQ Financials combined export has a "Period Type" toggle (Annual / Quarterly / LTM) that controls frequency for ALL subsheets in the file. Different subsheets have different frequency needs for the framework's computations. **PM exports the Financials file TWICE per name** — once with Period Type: Annual (for 5y normalized analysis and trend flags), once with Period Type: Quarterly (for Q/Q trajectory, discrete-event discontinuity catch, and Multiples percentile-quartile classification).

Subsheet inventory (13 subsheets — verified on US large-cap export; CIQ uses uniform export structure across listings as a design convention, so the inventory is expected to hold for FPI, Japan, Korea, UK/EU listings, but this has not been directly verified on non-US exports):

| Subsheet | Annual file role | Quarterly file role | Notes |
|---|---|---|---|
| Key Stats | 5y annual + LTM snapshot | Same data, less useful | Low-priority sanity-check; values are recomputed in primary statements at higher resolution |
| Income Statement | 5y CAGR, normalized margin, 5y-avg EBITDA for cyclical leverage check | 8Q Q/Q margin trajectory, seasonality, lumpy-vs-smooth volatility, revenue beat/miss composition, discrete-event detection | LOAD-BEARING in both files |
| Balance Sheet | 5y net-debt/EBITDA trend (requires 4+ years for the deteriorating-leverage flag), long-run shares outstanding trajectory | 8Q discrete capital structure events, Q/Q buyback execution pace, working-capital trajectory, cash burn rate | LOAD-BEARING in both files |
| Cash Flow | 5y FCF/Net Income conversion ratio (earnings quality), capex intensity trend, M&A history, dividend history | 8Q FCF volatility, SBC run rate, recent capex trajectory, WC swings | LOAD-BEARING in both files |
| Multiples | 5y range bookend (annual close per year, n≈5) — fallback for sparse-data verdict | 20+ quarterly Close points for percentile-quartile classification, B1 re-anchoring drift check | LOAD-BEARING; quarterly required for meaningful percentile (see Sparse-data fallback rule below). **Last column in BOTH files is partial-period today's-date snapshot — exclude from historical distribution per `Multiples — TWO SUBSHEETS` rule above.** |
| Historical Capitalization | 5y annual capitalization trajectory | 8Q quarterly capitalization trajectory; tracks shares outstanding at quarterly resolution; catches recap events | LOAD-BEARING in both files for item s (debt+capital) and item w (capital allocation) |
| Capital Structure Summary | Current + 2-3 prior periods (typically includes the latest quarter even in annual export) | Same content as annual; the quarterly export does not materially change this subsheet | Annual file sufficient — quarterly export is redundant for this subsheet |
| Capital Structure Details | Per-instrument forward-looking detail (maturity ladder, coupon, seniority, covenants, undrawn revolver capacity) | Identical content (frequency toggle does not apply to forward-looking instrument list) | Snapshot subsheet; either file sufficient |
| Ratios | 5y CIQ-computed ratios | 8Q CIQ-computed ratios | LOW priority — framework should compute its own ratios from primary statements (CIQ ratio conventions may differ from market-standard denominator definitions) |
| Supplemental | 5y annual industry-specific KPIs (where available) | 8Q quarterly industry-specific KPIs (where available) | LOAD-BEARING when A2 confirming metric is industry-specific (SaaS NDR/ARR/cRPO, banks NIM/NCO/loan growth, REITs FFO/AFFO/occupancy, energy production volumes, retailers same-store sales). **Frequently empty for tech/software** because tech companies report these metrics inline in Income Statement commentary or earnings call disclosures rather than the structured Supplemental subsheet — when empty, the metrics are still load-bearing but must be extracted from transcripts/IR releases, NOT skipped. |
| Industry Specific | Same as Supplemental | Same as Supplemental | Conditional on sector. **Frequently empty across all sectors** — CIQ stores industry KPIs in Supplemental for some sectors and Industry Specific for others. Check both; use whichever has data. Empty in both = "No Data Available" message, not a missing file. |
| Pension OPEB | Current + 2-3 prior years of defined-benefit pension obligation, funded status, assumed discount rate and return rate | Annual file sufficient (Pension OPEB is reported annually in financial statements regardless of quarterly toggle) | **Conditional on industry — load-bearing for defined-benefit-heavy industries** (industrials, autos, airlines, banks, legacy manufacturers); **immaterial for most tech/software/SaaS** (DC plans only; subsheet shows "No Data Available"). Empty subsheet for tech/software is correct, not a gap. |
| Segments | 5y annual revenue mix by segment, segment-level growth differentiation, geographic concentration, segment margin (where reported) | 8Q quarterly segment data; catches segment inflection earlier than annual lag | LOAD-BEARING annual (for B3 item h); quarterly is preferred when CIQ has it but not strictly required. |

**File-level metadata in CIQ Financials exports (deterministic grounding requirement):** the export's Period Type setting appears in the Income Statement subsheet at **row 7, the value in the cell labelled "Period Type:"** (verbatim values: `Annual` or `Quarterly`). The period-column frequency markers appear in **row 14** (verbatim form: `12 months | Jan-31-2022 ...` for annual, `3 months | Q1 | Apr-30-2020 ...` for quarterly; the latest column may be prefixed `Press Release` or `LTM`).

Any judgment the LLM forms about a file's frequency, coverage, or adequacy MUST be grounded in a VERBATIM read of these specific cells — read and quote `Income Statement` row 7 Period Type cell, plus the first and last row-14 period headers — NOT inferred from the data's shape, column count, or any other proxy. Shape inference ("this file has many columns, so it must be quarterly") is the failure surface that produced wrong frequency/staleness flags in practice: the same LLM that misread frequency-by-shape read the Multiples date columns correctly when it read the actual cells. Forced verbatim cell reads are reliable; shape inference is not.

If the verbatim read shows a mismatch between the file's actual Period Type and what the framework's B1/B3 step expects for that slot — OR shows the latest period is older than the most recent reported print the thesis relies on — this is a **data-integrity trigger**, not a thing to silently work around. It is governed by the **Session B Part 0 Data-Integrity Gate** (`checklist.md`, opening of the B1 file-read prompt): the LLM STOPS, quotes the verbatim read, names the mitigation it would otherwise apply, and asks PM to choose (re-upload / correct-my-read / proceed-with-mitigation-knowingly). The LLM does NOT aggregate, derive, or substitute a non-CIQ source on its own authority. See the Part 0 gate spec for trigger set (T1-T4), non-triggers, and resolution handling.

**Industry Specific / Pension OPEB / Supplemental empty-subsheet rule:** when these subsheets contain "No Data Available", this is expected behavior for sectors where the industry-specific KPIs aren't aggregated to structured CIQ data. Do NOT treat empty as a missing file. The framework still needs the equivalent metrics from other sources (transcripts, IR releases, formal annual filing); the gap is just that CIQ hasn't aggregated them for this sector.

## Sparse-data fallback for Multiples percentile-quartile classification

The framework's B1 valuation-position classification (NEAR-FLOOR / BELOW-CENTER / ABOVE-CENTER / NEAR-CEILING) uses percentile-of-Close-history quartiles. This computation requires sufficient settled-quarter data points to produce meaningful quartiles.

**Threshold:** n ≥ 8 settled-quarter Close points required for percentile-quartile classification. This is a **practical threshold for this framework**, not a theoretical statistical result — below n=8, quartile estimates from any small sample have wide confidence intervals, and the framework's verdict resolution drops to endpoint-comparison rather than continuous-percentile.

**Fallback when n < 8 settled-quarter points are available** (typical when PM exported Multiples at Annual frequency only, producing n≈4-5 annual closes). Define the rank position of current Close in the sorted history (0-indexed from lowest):

- Rank 0 of n (current is below all n historical closes) → **NEAR-FLOOR**
- Rank 1 of n (current is above 1, below n−1) → **NEAR-FLOOR** if n ≤ 5, else **BELOW-CENTER**
- Rank in lower-middle (e.g., rank 2 of 4, or rank 2 of 5) → **BELOW-CENTER**
- Rank exactly at median (n/2 rounded down) → **BELOW-CENTER** if current Close < median value, **ABOVE-CENTER** if current Close ≥ median value
- Rank in upper-middle → **ABOVE-CENTER**
- Rank n−1 of n (above n−1, below 1) → **NEAR-CEILING** if n ≤ 5, else **ABOVE-CENTER**
- Rank n of n (current is above all n historical closes) → **NEAR-CEILING**

For n=4 specifically (annual fallback): rank 0 → NEAR-FLOOR; rank 1 → NEAR-FLOOR (small-sample treats below-3-of-4 as endpoint-region); rank 2 → BELOW-CENTER or ABOVE-CENTER per median tiebreak; rank 3 → NEAR-CEILING; rank 4 → NEAR-CEILING.

**Label the verdict "resolution-limited"** in the B1 evidence card output. Example: `Multiple position: NEAR-FLOOR (resolution-limited verdict; n=4 settled annual closes; current 12.7x sits below all four — 21x, 24x, 28x, 31x)`.

**Surface to PM** as a request for the quarterly Multiples export when CIQ has it. If CIQ doesn't have quarterly Multiples history for the name (some international small-caps, recent IPOs), the resolution-limited fallback is the final verdict — explicit limitation labeling is the discipline.

The fallback applies ONLY to percentile-quartile classification. The B1 re-anchoring drift check (>5% relative drift between A2-anchored and CIQ-derived threshold) does NOT require n≥8 — it's a single-value comparison, works at any resolution.

## Discrete-event discontinuity check (B1 + B3)

**Trigger:** When quarterly Financials are available, run this check before completing B1 / B3:
- Any Balance Sheet line item with >25% change between consecutive quarters (in either direction)
- Any Income Statement margin (gross / operating / EBITDA / net) that compressed or expanded by >300 bps between consecutive quarters
- Any Cash Flow statement line item with >50% change between consecutive quarters (Cash Flow is naturally lumpier than Balance Sheet/Income Statement, so the threshold is higher)

**Required action when triggered:**
1. Name the quarter and direction.
2. Cross-reference the matching quarter's 10-Q (or formal interim filing equivalent) Notes section AND the matching quarter's earnings call Q&A for explanation.
3. Classify the event: capital structure (debt issuance, buyback execution, dividend declaration), M&A (acquisition, divestiture), restructuring (one-time charge, segment reorganization), accounting (change in revenue recognition, reclassification — see Reclassified column warning above), or operating (one-time gain/loss).
4. Surface to PM in the B1 / B3 output: "Discrete event detected in [quarter]: [classification + brief description from primary source]. Material to thesis? [PM judgment required]."

**Threshold calibration note:** the 25%/300bp/50% thresholds are calibrated for large-cap names (>$5B market cap) where these percentage changes correspond to economically material absolute dollar amounts and meaningful margin shifts. For small-caps (<$1B market cap), the 25% Balance Sheet threshold may produce false alarms on small absolute dollar changes; consider adding an absolute floor (e.g., >$50M or >5% of equity). For low-margin sectors (retail, distribution, commodity at trough margin <5%), the 300bp absolute margin threshold may miss meaningful relative shifts (100bp shift = 20% relative change for a 5% margin name); consider relative-to-base thresholds. Current rule applies as-is for typical fund universe (large-cap global ex-China ex-India), but small-cap or low-margin theses warrant PM judgment on threshold appropriateness rather than mechanical application.

**Why required:** discrete events of this magnitude can directionally change the trade. Debt-funded buybacks can be bullish (capital return discipline) or bearish (financial engineering masking ops weakness); large acquisitions can dilute or accrete; restructurings can be reset-to-growth or write-down-of-strategic-failures. Framework treating "current state" as the new baseline without investigating the event-of-record is silent wrong attribution — same severity class as the Vanguard restructuring catch. The check requires *quarterly* Financials data (annual-only export cannot detect Q/Q discontinuity by definition); this is one of the load-bearing reasons the framework requires the quarterly file.

**Behavior when quarterly export has fewer than 8 quarters of data** (typical for recent IPOs, international small-caps with limited history, names that recently restated): the discrete-event check runs across whatever consecutive-quarter pairs are available, even if only 3-4 quarters. Label the analysis "trajectory-limited" in the B1 output. The trajectory analysis for B3 item l (Q/Q margin trajectory over last 8 quarters) similarly proceeds with available quarters and labels resolution-limited. Same pattern as Multiples sparse-data fallback: do the analysis that's possible, label the constraint, do not improvise filler or pretend the gap doesn't exist.

---

**Multiples — TWO SUBSHEETS, DIFFERENT USES + CALCULATION CONVENTIONS.** The Multiples subsheet appears in BOTH the Estimates Report and the Financials exports — they contain fundamentally different data:

- **Financials → Multiples** (~91 rows × 9 cols): historical *quarterly* time series with Average / High / Low / Close per quarter for each multiple type (TEV/LTM Revenue, TEV/NTM Revenues, TEV/LTM EBITDA, P/E, etc., stacked vertically). Metadata rows 0-12, header row ~13 with Excel serial dates in columns 2+. ~5y history. **Use this for: B1 valuation-position classification, B1 re-anchoring check on relative thresholds, B3 valuation context section.**
- **Estimates → Multiples** (~26 rows × 7 cols): current *forward* snapshot only — NTM and forward FY values for TEV/REV, TEV/EBITDA, P/E, PEG. No history. **Use this only for: current-forward-multiple snapshot at A2 if Financials has not been pulled yet.**

If both files are uploaded and a step needs historical range, use Financials → Multiples. Using Estimates → Multiples for range work produces wrong B1 verdicts (no historical range to classify against; falsely confident NEAR-FLOOR claims; meaningless drift comparisons).

**Calculation conventions when reading Financials → Multiples:**
- **Use the Close column** for both current and historical values. Close is the point-in-time observation at quarter-end (market-standard for valuation-position work). Average is smoothed and underweights endpoint moves; High/Low are intra-quarter extremes that do not represent any actual sustained traded level.
- **Match the LTM vs NTM convention to whatever A2 anchored on.** The sheet contains both TEV/LTM Rev and TEV/NTM Rev (separate row blocks) — if A2 anchored "current EV/NTM Rev = 5.0x", B1 must pull TEV/NTM Rev Close, not TEV/LTM Rev. These typically differ by 1-2x; mixing them makes the re-anchoring drift check meaningless.
- **Range-position classification uses percentile of current Close vs historical Close distribution.** NEAR-FLOOR = bottom quartile (0–25th percentile of Close history); BELOW-CENTER = 25–50th; ABOVE-CENTER = 50–75th; NEAR-CEILING = top quartile (75–100th). Do not use min(Low)-to-max(High) across the history as the range — that combines intra-quarter extremes from different quarters and produces a band that nobody ever traded at sustainably.
- **Exclude the partial-period today's-date snapshot from the historical distribution.** The Financials → Multiples sheet's last column is often an intra-quarter snapshot (e.g., today's date) rather than a settled quarter-end Close. Use it as the "current" value for percentile comparison, but EXCLUDE it from the historical distribution against which percentile is computed. Percentile-of-history is meaningful only against settled quarter-end Closes.

**Income Statement — "Reclassified" period column warning.** Early-year columns in CIQ Income Statement may have headers `Reclassified\n12 months\n[year]` rather than the standard `12 months\n[year]` — indicating CIQ has restated the historical period using a later-period accounting basis. **Do NOT compute YoY growth across the reclassified-vs-current-basis boundary** — the comparison mixes apples and oranges. Either restrict YoY computation to consistently-formatted periods, or note the reclassification in B1 output. Same warning applies to Cash Flow and Balance Sheet historicals when header includes "Reclassified".

**LTM vs FY for YoY growth convention.** Financials sheets typically include both fiscal-year columns (e.g., `12 months Jan-31-2026`) and a trailing-LTM column (e.g., `LTM 12 months Apr-30-2026`). For YoY growth rates: use FY-vs-FY-prior (consistent period comparison) OR LTM-vs-LTM-prior (consistent trailing comparison) — **never mix the two**. Mixing produces wrong YoY because LTM straddles fiscal-year boundaries. If B1 needs the freshest growth rate, prefer LTM-vs-LTM-prior; if B1 needs the cleanest annual basis, prefer FY-vs-FY-prior.

**Estimates Report → Recent Changes sheet:** header at row 14, columns: `Change Type | Date | Broker | Analyst | Data Point | Period | Broker Value Current | Broker Value Prior | Consensus After | Consensus Before`. Date in Excel serial. Change Type values: `Upward Revision`, `Downward Revision`, `-` (no change / informational). **This sheet is where per-broker PT changes appear** — including upgrades/downgrades. Filter on Data Point = "Target Price" for PT-revision-specific events.

**Estimates Report → Revisions sheet — METRIC AMBIGUITY (verdict-flipping risk):** the sheet has ~23 metric blocks stacked vertically (EPS Normalized, EPS GAAP, Cash EPS, DPS, BVPS, NAV/share, CFPS, Revenue, EBITDA, EBIT, Interest Expense, EBT×2, Net Income×2, Net Debt, D&A, CFO, Capex, FCF, Gross Margin %, Effective Tax Rate %, ROE %, ROA %, TEV, Non-Periodic Data Items). Each block has Last Month / Last 2 Months / Last 3 Months rows with `# of Analysts | # of Analysts still in Consensus | Upward | Downward` columns per FY/FQ period. Framework's "consensus revision breadth, last 30 days" instruction is ambiguous without specifying metric — different metrics can give contradictory signals (empirically: EPS Normalized FY27 Last Month 40 up / 0 down = very positive; EPS GAAP FQ3 27 Last Month 0 up / 16 down = very negative).

Required: B1 must explicitly read AT LEAST these three metric blocks and report directional agreement or disagreement:
- **EPS Normalized** (the primary forward earnings consensus — load-bearing for valuation math)
- **Revenue** (the topline trajectory — directional driver of multi-segment names)
- **EBITDA or EBIT** (the margin trajectory — confirms or contradicts the "growth is profitable" narrative)

When the three agree, report a single direction with high confidence. When they disagree, report all three explicitly and flag the seam to PM — the disagreement is itself a signal (e.g., positive EPS revisions with negative Revenue revisions = margin-driven beats from cost cuts, not demand-driven).

**Note PT (Target Price) revisions are NOT in this Revisions sheet** — they're in Recent Changes (per-broker events) and in Consensus (aggregated PT statistics). Framework's "PT/EPS revision direction" wording lumps two different sheets together.

**Estimates Report → Surprise sheet — limited to per-share metrics + consensus-not-guidance:** metric blocks are EPS Normalized, EPS GAAP, EPS Excl Excep+GW, DPS, BVPS, NAV/share, CFPS. **NO Revenue surprise**, **NO EBITDA surprise**. If B3 needs Revenue beat/miss history, compute from Consensus sheet (expected) + Income Statement quarterly actuals (actual). Also note: Surprise measures actual-vs-CONSENSUS-estimate, NOT actual-vs-MANAGEMENT-GUIDANCE — these can diverge (a name can beat consensus while missing its own prior guide). Framework's B3 item o "guidance hit rate" requires the Guidance sheet + quarterly actuals composition, not the Surprise sheet alone.

**Estimates Report → Consensus sheet — multi-listing column risk:** large-cap names often have multiple listing columns side-by-side: e.g., a primary listing (USD on US exchange) next to a GDR/ADR equivalent on a foreign exchange in local currency, or multi-class share variants. LLM picking "first non-blank consensus PT" could pick the foreign-currency-denominated equivalent and produce a number in wrong currency. **Always read column header to confirm primary listing and verify currency before extracting any price/PT/multiple value.**

**Holders file — comprehensive rules.** Header at row 17. Columns: `Holder | [Date1] Common Stock Equivalent Held | [Date2] ... | Latest Common Stock Equivalent Held`. The file lists ~4,000-5,000+ holders for large-cap names; only a fraction are material.

*Data is shares, not percentages.* To convert to % held, divide by shares outstanding from Financials → Balance Sheet (Total Common Shares Outstanding or equivalent). Do NOT use training-data shares-outstanding values — they may be stale, especially after buybacks or splits.

*The "Latest" column is NOT the same as the most-recent formal quarter column.* It reflects interim filings (off-quarter 13F amendments, share-class changes, etc.) and may differ from the prior column by small amounts even when no major flow occurred. **For Q/Q delta computation, use the last two formal quarter-end columns (e.g., Mar-31-2026 minus Dec-31-2025), NOT Latest minus prior-quarter.**

*Filer-family aggregation required before mover ranking — CATASTROPHIC if missed.* Large multi-entity filer families (Vanguard, BlackRock, State Street, Capital Group, Fidelity/FMR, T. Rowe Price) periodically restructure how holdings are reported across subsidiary entities. Empirically observed: Vanguard Group, Inc. went from 89M shares to 0 in one quarter while several Vanguard subsidiaries (Capital Management, Portfolio Management, Fiduciary Trust, Global Advisers) went from 0 to ~88M aggregate. Net Vanguard ownership unchanged. Naive entity-level ranking reports "Vanguard added 80M shares" as ADDING NET — confidently wrong.

Required pre-processing:
1. Before ranking movers, group holders by parent family using **start-of-name pattern match** (NOT substring-anywhere match — substring match falsely aggregates independent firms whose names happen to contain the same word). Strip leading "The " before matching. Family patterns (case-insensitive, anchored at start):
   - `^Vanguard\b` → Vanguard family (catches: Vanguard Capital Management, Vanguard Portfolio Management, Vanguard Fiduciary Trust, Vanguard Global Advisers, etc., and "The Vanguard Group, Inc." after stripping "The")
   - `^BlackRock\b` → BlackRock family
   - `^State Street\b` → State Street family
   - `^Capital (Research|Group|International|World)\b` → Capital Group family (catches Capital Research and Management, Capital International Inc., Capital Group Companies, Capital World Investors — the actual Capital Group affiliate naming pattern). Does NOT match "Quadrant Capital Group LLC", "Winton Capital Group Limited", "Saban Capital Group" etc. (independent firms with "Capital Group" elsewhere in name).
   - `^(Fidelity|FMR)\b` → Fidelity family (FMR LLC is the legal entity for Fidelity)
   - `^T\.\s*Rowe Price\b` → T. Rowe Price family
   - `^Geode\b` → Geode (treated as separate family from Fidelity despite affiliation — files independently)
   - For other multi-entity filers seen at scale, extend the pattern list — but always anchor at start of name, never substring-anywhere.
2. Compute family-level Q/Q delta = sum(latest formal quarter family) − sum(prior formal quarter family).
3. Rank family-level deltas. Cite subsidiary entities only for transparency on what drove family-level change.
4. Flag internal restructurings (one subsidiary drops, another rises within same family, net ~zero) explicitly as "filer restructuring, no net flow" — do not drop silently from the analysis.

**Why anchoring matters — verified empirically:** in a real-data Holders file, naive substring match on "Capital Group" or "Capital International" returned 17 entities — but only 1 was an actual Capital Group affiliate (Capital Research and Management Company). The other 16 were independent firms (Quadrant Capital Group LLC, Winton Capital Group Limited, Saban Capital Group LLC, L1 Capital International Pty Limited, etc.) whose names contain "Capital Group" but who file separately and have no economic relationship to Capital Group Companies, Inc. Aggregating these as one family would produce a fictitious flow signal.

*Insiders separated from institutions — wrong-denominator risk.* The Holders file mixes institutional filers, insiders (founders, officers, directors), and individual holders. Framework's "institutional concentration" and "institutional flow" must EXCLUDE insiders.

To classify a row as insider: extract all parenthetical content from the Holder name. If any parenthetical contains an insider role keyword AND is not a listing reference, classify as insider.

- **Insider role keywords (substring match, case-sensitive):** `Director`, `Officer`, `Founder`, `CEO`, `CFO`, `CTO`, `COO`, `Chairman`, `President`, `EVP`, `SVP`. The bare keyword approach correctly catches all variants: `(Director)`, `(Independent Director)`, `(Lead Independent Director)`, `(Outside Director)`, `(Non-Executive Director)`, `(President & CRO)`, `(Co-Founder, Chairman & CEO)`, `(Executive VP & Chief X Officer)`, etc.
- **Exclude these parenthetical patterns (listings/notes, not roles):** `NYSE:`, `NASDAQ:`, `NasdaqGS:`, `NasdaqCM:`, `TSX:`, `LSE:`, `BME:`, `HKEX:`, `Disclosed`, `N-PORT`, `GDR`, `ADR`. Institutional names sometimes have these in parens (e.g., `BlackRock, Inc. (NYSE:BLK)`); these are not role markers.
- **Do NOT use simple prefix matches like `(Director`** — these break on `(Independent Director)` and `(Lead Independent Director)` because the opening paren is followed by `Independent`, not `Director`. Empirically, Independent Directors are extremely common board roles; missing them produces wrong-denominator institutional percentages.

These insider rows belong in B3 item v (insider activity), not item m (institutional concentration). Empirically: in a real-data export of a founder-led large-cap, naively-computed "institutional %" = 83% included ~22M insider shares; true institutional % = ~80.7%.

*Materiality filter for "largest movers".* Without a filter, the largest absolute share-delta rows are dominated by tiny initiations (0 → 47,000 shares = "biggest adder!" when it's a $9M position in a $200B name = 0.0005%). Filter the universe to holders meeting either threshold before ranking:
- ≥0.1% of shares outstanding in either the prior-quarter OR latest-quarter column, OR
- ≥$50M position value in either column.
Then rank absolute Q/Q share delta within the filtered universe.

*13F coverage limitation — must be labeled in B3 output.* The Holders file reflects 13F filings, which cover:
- ONLY long equity positions in 13F-reportable securities
- NOT short positions, NOT options/swaps positions, NOT positions held under non-13F regimes (sovereign wealth funds, private bank custody, foreign holders below the threshold).
- 45-day lag from quarter-end (latest formal quarter column is filed by mid-second-month-after-quarter-end).
Framework's "institutional flow direction" output must be labeled as **long equity 13F flow only — does not reflect short positioning or derivatives**. For thesis-sensitive cases, cross-reference with short-interest data from Charting.

*Footnote rows must be dropped:* the last 1-2 rows often contain legend text ("CSO denotes Common Shares Outstanding..."). Drop via `dropna(subset=['Holder'])` and filter remaining rows for legend keywords.

**Charting file:** header position varies (commonly row 32); columns are `Pricing Date | [Metric Name]`. Date in Excel serial. Percentages stored as fractions (0.0305 = 3.05%). **Beta is NOT in the Charting export** — PM-verified empirically. Beta data is shown on the CIQ company tearsheet web page (5y monthly beta as a number), not exported in any XLSX module. Framework treats beta as a PM-declared input at Session C, not LLM-extracted from any file. PM reads the tearsheet number and declares; LLM does not search Charting (or any other XLSX) for a "Beta" column.

**Key Developments (real RTF):** pipe-delimited table with `Date | Type | Headline | Other Parties`, followed by "Situation:" paragraph per entry. Date as string ("May-11-2026"). Filter Type for category needed.

---

## Computational defaults (for Gate 5 historical drawdown and others)

When computing rolling drawdowns from CIQ Charting price history:
- 30-day, 60-day, 90-day rolling windows
- Use closing prices from the dated series (one observation per trading day)
- Drawdown defined as `(price_t / price_max_in_window) - 1`
- Worst drawdown over 5 years = min of the rolling series

---

## Business Relationships export (Customers & Suppliers) — supply-chain graph source

Empirically validated against 32 exports (16 names, both views each), 2026-06.

**File format:** real `.rtf` → `striprtf` (same as Key Developments; NOT the OLE-disguised `.doc` variant — always `file`-check first). After `striprtf` the table is **pipe-delimited** (one `|` per cell, trailing `|`).

**Layout.** Two view types, distinguished by the **column-header order** (the header row contains `Relationship Type`):

| Header order | View | col0 (the named party) | col1 |
|---|---|---|---|
| `Customer Name \| Supplier Name \| Relationship Type \| Primary Industry \| Source` | Customers | the customer (counterparty) | the focal (supplier) |
| `Supplier Name \| Customer Name \| Relationship Type \| Primary Industry \| Source` | Suppliers | the supplier (counterparty) | the focal (customer) |

So **col0 is always the counterparty, col1 always the focal** — identify the focal from the dominant col1 entity (robust to filename/folder), not the filename. Each data row is followed by a `Business Description: …` line (ignore). Entities are `Name (Exch:Ticker)`; private names have no parenthetical; a leading `*` marks a proprietary relationship (strip it). **There is no Current/Former column** — the export is headed "Recently disclosed … (within the last two years)", i.e. current-only.

**Direction:** Customers view → focal **→** counterparty (downstream); Suppliers view → counterparty **→** focal (upstream).

**Relationship-type filter (keep supply-chain only).** Observed types by frequency: Supplier (1475), Customer (631), Distributor (324), **Client Services (187)**, Creditor (166), Landlord (154), Licensor (85), Licensee (83), Borrower (65), Lessee (26), Lessor (16), Vendor (15), Tenant (11), Transfer Agent (6), Franchisee (4), Franchisor (1). **Keep:** Supplier, Customer, Distributor, Vendor, Manufacturer. **Drop:** the financial/legal/real-estate types (Creditor, Landlord, Licensor/ee, Borrower, Lessee/or, Tenant, Transfer Agent, Franchisee/or). **Client Services is excluded** by judgment (a softer client relationship, not a goods/services dependency) — revisit if a customer-graph wants it.

**Counterparty resolution:** resolve **US-listed** counterparties by ticker (exchange prefix Nasdaq/NYSE/OTC/BATS/Cboe/AMEX); **non-US** (e.g. TSE, LSE, BSE, KASE) and **private** (no ticker) counterparties are out of the US graph's scope — record them with a reason, never silently drop. A US ticker that fails to resolve (delisted/renamed) is flagged `unresolved_us`, not crashed. Empirically across the 16-name set: 3,257 rows → 812 dropped (non-supply-chain) → 2,445 supply-chain edges → **688 US-resolved**, 1,183 non-US, 522 private, 52 unresolved-US.

---

## What this file does NOT cover

Not a CIQ user manual. Not exhaustive of every CIQ module. If PM uploads a CIQ file type not described above and LLM can't determine structure from inspection, LLM surfaces to PM and asks for the first 20 rows pasted as text so PM can confirm format before LLM extracts.

For tool inventory and source-to-question mapping, see `data_sources.md`. This file is purely about extraction mechanics.
