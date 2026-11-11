# CIQ Extraction Reference

Critical rules for LLM extracting from CIQ files. Empirically validated against real CIQ exports. Generic to any name. **Superseded where it differs from the code** (`vinci/dossier/ciq.py`, `vinci/dossier/ciq_sheets.py`) or the CIQ field contract: see *2026-11-11 corrections* at the end of this file.

This file is consult-as-needed. It once pointed to "Session B PM PROVIDES in checklist.md" for the most important rules. **`checklist.md` is not in this repository** (`git ls-files` finds none, and no commit on any branch or on `origin/main` ever added one, 2026-11-11); it belongs to the session framework these notes came from. The Session A/B/C, B1/B3 and checklist-item references below are that framework's, not this repo's (G-D14).

---

## File format reality

CIQ extensions mislead about actual format. Always verify with `file` command before parsing; never trust the extension:

| Extension | Actual format | Parser to use |
|---|---|---|
| `.xls` | Legacy BIFF (Excel 97-2003 binary) | `xlrd` library only. openpyxl fails with explicit error. |
| `.rtf` (Key Developments) | Real RTF text (36 of 36 on disk, 2026-11-11). CIQ has also sent Key Developments as a spreadsheet, which the reader refuses (see *Key Developments* below) | `striprtf` library |
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

1. **Missing data:** a cell carrying no number is one of eight markers, the code's set `ciq._UNAVAILABLE_CELLS`: blank, `-`, `—`, `NM`, `NA`, `N/A`, `Entitlement Needed`, `No Data Available` (G-D11; this line listed three). `ciq.read_cell` returns no value and the marker as written, so a caller can say why there is no number; `clean_num` returns None for every marker and never 0. Text that is neither a number nor a marker is unparseable, and `read_cell` says so by returning neither. On the 170 spreadsheets on disk (36 folders, 2026-11-11; blanks not counted): `-` 958,269 cells in 170 workbooks, `NA` 43,655 in 97, `NM` 33,734 in 125, `Entitlement Needed` 16,515 in 36, `No Data Available` 69 in 54, `N/A` 18 in 13, `—` 0. `NM` says the metric cannot be computed (a negative or near-zero base), which is a different statement from `-`; see *`NM`* under the comps section. Never fabricate, estimate, or interpolate. Surface to PM with options: re-export with different settings, source externally per data_sources.md, or proceed with the gap noted.

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
| Supplemental | 5y annual industry-specific KPIs (where available) | 8Q quarterly industry-specific KPIs (where available) | LOAD-BEARING when A2 confirming metric is industry-specific (SaaS NDR/ARR/cRPO, banks NIM/NCO/loan growth, REITs FFO/AFFO/occupancy, energy production volumes, retailers same-store sales). ~~Frequently empty for tech/software~~ (G-D11): it is a "No Data Available" shell in 1 of the 72 Financials workbooks on disk (FUBO's Annual; 36 folders, 2026-11-11) and has rows in the other 71. No extractor reads it (`Supplemental` matches nothing under `vinci/`, 2026-11-11). When empty, the metrics are still load-bearing but must be extracted from transcripts/IR releases, NOT skipped. |
| Industry Specific | Same as Supplemental | Same as Supplemental | Conditional on sector. **Frequently empty across all sectors** — a "No Data Available" shell in 47 of the 72 Financials workbooks on disk (2026-11-11). CIQ stores industry KPIs in Supplemental for some sectors and Industry Specific for others. Check both; use whichever has data. Empty in both = "No Data Available" message, not a missing file. No extractor reads it. |
| Pension OPEB | Current + 2-3 prior years of defined-benefit pension obligation, funded status, assumed discount rate and return rate | Annual file sufficient (Pension OPEB is reported annually in financial statements regardless of quarterly toggle) | **Conditional on industry — load-bearing for defined-benefit-heavy industries** (industrials, autos, airlines, banks, legacy manufacturers); **immaterial for most tech/software/SaaS** (DC plans only; subsheet shows "No Data Available"). Empty subsheet for tech/software is correct, not a gap. |
| Segments | 5y annual revenue mix by segment, segment-level growth differentiation, geographic concentration, segment margin (where reported) | 8Q quarterly segment data; catches segment inflection earlier than annual lag | LOAD-BEARING annual (for B3 item h); quarterly is preferred when CIQ has it but not strictly required. |

**File-level metadata in CIQ Financials exports (deterministic grounding requirement):** the export's Period Type setting appears in the Income Statement subsheet at **row 7, the value in the cell labelled "Period Type:"** (verbatim values: `Annual` or `Quarterly`). The period-column frequency markers appear in **row 14** (verbatim form: `12 months | Jan-31-2022 ...` for annual, `3 months | Q1 | Apr-30-2020 ...` for quarterly; the latest column may be prefixed `Press Release` or `LTM`).

Any judgment the LLM forms about a file's frequency, coverage, or adequacy MUST be grounded in a VERBATIM read of these specific cells — read and quote `Income Statement` row 7 Period Type cell, plus the first and last row-14 period headers — NOT inferred from the data's shape, column count, or any other proxy. Shape inference ("this file has many columns, so it must be quarterly") is the failure surface that produced wrong frequency/staleness flags in practice: the same LLM that misread frequency-by-shape read the Multiples date columns correctly when it read the actual cells. Forced verbatim cell reads are reliable; shape inference is not.

If the verbatim read shows a mismatch between the file's actual Period Type and what the framework's B1/B3 step expects for that slot — OR shows the latest period is older than the most recent reported print the thesis relies on — this is a **data-integrity trigger**, not a thing to silently work around. It is governed by the **Session B Part 0 Data-Integrity Gate** (`checklist.md`, opening of the B1 file-read prompt; that file is not in this repository, G-D14): the LLM STOPS, quotes the verbatim read, names the mitigation it would otherwise apply, and asks PM to choose (re-upload / correct-my-read / proceed-with-mitigation-knowingly). The LLM does NOT aggregate, derive, or substitute a non-CIQ source on its own authority. See the Part 0 gate spec for trigger set (T1-T4), non-triggers, and resolution handling.

**Industry Specific / Pension OPEB / Supplemental empty-subsheet rule:** when these subsheets contain "No Data Available", this is expected behavior for sectors where the industry-specific KPIs aren't aggregated to structured CIQ data. Do NOT treat empty as a missing file. The framework still needs the equivalent metrics from other sources (transcripts, IR releases, formal annual filing); the gap is just that CIQ hasn't aggregated them for this sector. *This rule is for these three unread subsheets only (G-D11). On a subsheet the code does read, a "No Data Available" shell is reported as a bad or partial export to re-export (`ciq.is_no_data_shell`, `ciq_sheets._no_data_note`): AORT's 2026-07 export held one while CIQ had the data. In a single cell, "No Data Available" is one of the markers in rule 1.*

## Dossier extractor semantics (code-matched spec — `vinci/dossier/ciq_sheets.py`, `mechanical.py`)

This section is the spec the dossier extractors actually implement. It must not lag the code; each
rule names the function so a future session can find and extend it. All rules are name-agnostic
(no ticker literals); the VRRM figures below are illustrative.

**Geographic Segments — location and extraction.** The Segments subsheet contains a `Geographic
Segments` section AFTER the `Business Segments` section (≈ row 38 on the verified export), with its
own period header and a `Revenues` block listing countries (e.g. United States / Australia / United
Kingdom / Canada / ALL Other) down to a `Total Revenue` row, structured identically to the business
`Revenues` block. `geographic()` extracts it via `_segment_section(after_label="Geographic Segment")`:
find the `Geographic Segments` header, scope the `Revenues` / `Total Revenue` search to rows after it
(so the GEOGRAPHIC block is found, not the first/business one), and parse country revenue shares the
same way as business-segment revenue share. Fail loud UNKNOWN only if the section is genuinely absent.

**Clean revenue YoY comes from the QUARTERLY file, not the annual one** (`margin_trend` /
`multi_year_trajectory` via `_quarterly_revenue_yoy()`). The annual Income Statement's latest column
is LTM, whose only same-basis prior column is Reclassified — so a clean annual YoY is genuinely
impossible (the LTM-vs-FY guard and the Reclassified-boundary guard both correctly refuse). The
quarterly Income Statement gives a clean same-basis YoY: the latest quarter vs the SAME quarter a
year earlier (Q1-2026 vs Q1-2025), matched on the quarter token (Q1/Q2/Q3/Q4) AND the same
Reclassified basis. Guards stay intact: never YoY across a Reclassified boundary, never mix LTM with
FY, never compare different quarters. If no same-quarter same-basis prior exists, the YoY is simply
omitted (returns None) — never fabricated.

**"Margin trend" = the margin TRAJECTORY, never revenue growth** (`margin_trend()`). The field is the
gross-margin and EBITDA-margin series per period across the years (e.g. EBITDA margin 42%→37%
compression), so the *trend* is visible. Each margin is a ratio WITHIN a single column, so it is
never computed across the Reclassified boundary (the basis is marked `(R)`). Revenue GROWTH (YoY) is
a top-line metric and lives in the multi-year trajectory/growth field — it must NOT be reported under
a margin label. Do not conflate top-line growth with margin trend.

**Segment EBITDA is PRE-CORPORATE; consolidated EBITDA is the multiples/leverage/coverage base.** The
Segments EBITDA section sums to SEGMENT EBITDA (pre-corporate; e.g. 416 = CS+Parking+Gov segment
EBITDA). The CONSOLIDATED EBITDA (Income Statement; e.g. 362) is lower by the unallocated-corporate
item (≈54). These two "EBITDA" bases must never be silently mixed:
- Segment EBITDA SHARES (`segment_ebitda()`) are computed on the segment sum and labelled "% of
  segment-EBITDA sum (pre-corporate)"; the field also surfaces the consolidated EBITDA (matched to
  the same fiscal period via `_consolidated_ebitda()`) and the reconciling unallocated-corporate item.
- MULTIPLES / LEVERAGE / COVERAGE (EV/EBITDA, net-debt/EBITDA, interest coverage) use CONSOLIDATED
  EBITDA, not the segment sum.
- When labelling any EBITDA figure, state the base.

**P/E-distortion RESOLUTION path** (`_pe_reconciliation()`, replaces the old open `_pe_basis_flag`).
When the trailing GAAP EPS denominator is far out of line with recent history (latest annual EPS
> ~2.5× or < ~0.4× the recent median), the trailing GAAP P/E is one-time-distorted and not a
meaningful cheap/expensive read. Resolve rather than flag-and-defer, by reconciling the surfaced reads:
trailing GAAP P/E (distorted; e.g. 5.5x on a one-time-elevated EPS 0.85 vs ~0.28 median) → forward
ADJUSTED EPS from the catalyst 8-K's Ex-99.1 revised guidance (e.g. $1.19–1.25 → adj P/E ~3.9x at the
current price, the clean earnings-power read) → the CIQ P/LTM EPS multiple (uses a different, lower
trailing EPS basis). The EDGAR-vs-CIQ P/E conflict folds into this resolved statement (not a separate
flag). The resolved statement is emitted only when the forward adjusted EPS is actually sourced;
otherwise the original "verify against normalized/forward EPS (CIQ)" flag stands. (Consensus GAAP FY
is a third clean read when surfaced — currently only revision *breadth* is extracted, not the point
estimate.)

**Adjusted-basis multiples** (`_adjusted_facts()`). When the Ex-99.1 furnishes forward adjusted
EBITDA/EPS, surface forward EV/adj-EBITDA = (EOD price × EDGAR shares + EDGAR net-debt) ÷ FY-guide
adj-EBITDA, and covenant-basis net-debt/adj-EBITDA = net-debt ÷ FY-guide adj-EBITDA, ALONGSIDE the GAAP
trailing TEV/LTM and GAAP net-debt/EBITDA — source-bound to the 99.1 (adj-EBITDA) + EDGAR + EOD. Only
figures actually present in the 99.1 are used; if absent, the GAAP caveat stays an open flag (never
fabricate the adjusted side). The leverage field is labelled `(fwd-adj)` because it uses forward, not
trailing, EBITDA.

**Surprise basis** (`surprise_history()`). ~~Estimates→Surprise is by FISCAL YEAR (no quarterly
view)~~ (G-D8): the sheet has a quarterly view. On the 36 Estimates exports on disk (2026-11-11),
every Surprise sheet has a 'Fiscal Quarters' section, 35 a 'Fiscal Years' section (FUBO's has
quarters only) and 10 a 'Calendar Years' section too. `surprise_history()` reads the FISCAL-YEAR
table only, so the surfaced surprise is annual: the GAAP-EPS row of the company's OWN listing's block
(`_surprise_eps_block`, never the sheet's first listing) and the Revenue row, each against its own
block's year header. The 'Calendar Years' repeat is never read as FY. No extractor reads the
quarterly section's values: searched 2026-11-11 for `Fiscal Quarters` and `Calendar Quarters` (each
is matched only as a section end, by `_SURPRISE_BANNER`) and read every `sheet("estimates", "Surprise")`
call, all of which read the fiscal-year section or check the sheet is there.
FUBO and ORKA have no fiscal-year header of three or more years, so their surprise reads UNKNOWN.
The EPS row is GAAP-EPS basis (distinct from the 99.1 adjusted guide) and is labelled as such;
`+beat / −miss`.

**Transcript: POINTED-TO in the dossier, WHOLE for the synthesis — never embedded, never
curated.** Two separate paths, by design:
- DOSSIER (`management_commentary()`): a POINTER only — the call/file identifier + "read in full for
  management posture/tone", source-bound to the file. NO machine-selected excerpt and NO full embed.
  A machine-chosen "salient extract" is the relevance judgment this project forbids (the machine
  widens/points, never decides what matters); the full embed was also a duplicate (the human holds
  the file) that bloated the synthesis prompt and truncated it.
- SYNTHESIS + DRIVER-EXTRACTION LLM INPUT (`transcript_for_synthesis()`): every call on file, WHOLE
  (operator ruling 2026-10-29, "Whole transcripts") — boilerplate stripped (operator intro /
  forward-looking-statements legalese / leading estimates table / TOC, via `_transcript_prose`'s
  hand-off anchor), then prepared remarks and the full Q&A. A call past `_TRANSCRIPT_CEILING`
  (100,000 characters, a safety bound) ends in a cut marker and a QA flag, and a call on file that
  does not read is named in a QA flag (`unparsed_transcript_flag`). Not a topic/relevance
  selection — no name-specific topics are hardcoded; it works for any ticker. (Until 2026-10-29
  each call was cut at a fixed 12,000-character budget with no marker.) The one slice has two
  readers, and only one of them derives no numbers (G-D13; this said "no numbers derived" of both):
  - the DRIVER STEP (`driver_extract.extract_transcript_drivers`, run before the synthesis) DOES
    read figures from it. Each row's quote must be in the slice, every number in its `value` must
    equal a number of that quote in the quote's unit, and `check_fact` sets the row's `figures` and
    `value_status`. The rows enter the mechanical layer as `operating_drivers`;
  - the SYNTHESIS takes the slice as qualitative context only. Its prompt says to derive no numbers
    from the text and to cite the `operating_drivers` fact instead (`synthesize`); points still bind
    to the mechanical facts' source_refs.

  The slice itself is NOT part of the mechanical-layer dump, so it does not enlarge the
  number-trace haystack; the driver rows read from it are.

**Synthesis truncation is fail-loud, not silently-blank** (`llm.extract` + `synthesize`). Corrected
2026-11-11 (G-D13) to what the code does:
- The forced tool marks SIX fields required (`synthesis._TOOL_TEMPLATE`): `bull_points`,
  `bear_points`, `twin_reference_cases`, `decisive_question`, `key_unknowns`, `evidence_balance`.
- If the model is cut at `max_tokens` mid-tool-call, `AnthropicLlmClient.extract` raises
  `LlmError` (it checks `stop_reason`).
- `synthesize` rejects a draw missing any of the first FIVE (the structural fields). With several
  draws, that draw is skipped and the build goes on; the whole synthesis is UNAVAILABLE, with a loud
  flag, only when no draw is usable. Missing trailing fields are never defaulted to blank, which
  would be indistinguishable from a genuine empty field.
- A draw missing `evidence_balance` is NOT refused; the code chooses this on purpose (`synthesize`:
  "flag, don't drop"). Its lean counts as unparsed, a bucket of its own in the draws' vote, so it
  never joins another draw's lean. If the kept draw is the one missing it, the page is flagged ("evidence_balance
  MISSING", the G.2 check in `synthesis._validate`) and carries no machine proposal
  (`verdict.derive_proposal`: "no machine read on this dossier").
- ~~The output cap is 8192 tokens.~~ The output cap is **16,384 tokens**: the default `max_tokens`
  of `vinci/graph/llm.py:AnthropicLlmClient`, which the dossier command builds through
  `from_config` without overriding it.

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

**Estimates Report → Surprise sheet — per-share AND company-level metrics, consensus-not-guidance** (G-D8; this said "limited to per-share metrics … NO Revenue surprise, NO EBITDA surprise", which the exports contradict). Census of the 36 Estimates exports on disk (2026-11-11), blocks by label:
- **Per listing** (headed `<exchange>:<symbol> (<currency>)`): EPS Normalized 36, EPS (GAAP) 36, DPS 34, Book Value / Share 33, CFPS 32, Net Asset Value Per Share 28, EPS (Excl. Excep, GW) 6.
- **Company Level** (headed `Company Level (<currency>)`, 36 of 36): Revenue, EBITDA, EBIT, EBT (Excl. Excep), EBT (GAAP), Net Income (Excl. Excep), Net Income (GAAP), Net Debt and Capital Expenditure, each on all 36; EBT and Net Income (Excl. Excep, GW) on 3 and 6.
- Each block carries Difference / Actual / Estimate / Announced Date / Acctg. Standard rows, and on 33 of 36 sheets some blocks also carry Guidance Low / Guidance / Guidance High rows. The blocks repeat per section (Fiscal Years, Fiscal Quarters, and on 10 sheets Calendar Years; see *Surprise basis* above).

What the code reads, all from the Fiscal Years section: Revenue beside GAAP EPS (`surprise_history`); Revenue, EBITDA, EBIT and Capital Expenditure, actual against the final consensus (`historical_forecast_error`); Net Debt, against the balance sheet (`_consensus_net_debt_check`). A quarterly Revenue beat/miss is on the sheet but read by no extractor. Also note: Surprise measures actual-vs-CONSENSUS-estimate, NOT actual-vs-MANAGEMENT-GUIDANCE — these can diverge (a name can beat consensus while missing its own prior guide). Framework's B3 item o "guidance hit rate" requires the Guidance sheet + quarterly actuals composition, not the Surprise sheet alone.

**Estimates Report → Consensus sheet — multi-listing column risk:** large-cap names often have multiple listing columns side-by-side: e.g., a primary listing (USD on US exchange) next to a GDR/ADR equivalent on a foreign exchange in local currency, or multi-class share variants. LLM picking "first non-blank consensus PT" could pick the foreign-currency-denominated equivalent and produce a number in wrong currency. **Always read column header to confirm primary listing and verify currency before extracting any price/PT/multiple value.**

**Holders file — SUPERSEDED (G-D9, 2026-11-11). No code reads a holders export, so the rules below describe no extraction in this repo.**
- `ciq._WORKBOOK_KEYWORDS` has no ownership kind, so a holders or Public Ownership export is an unrecognised file. Assembly names it in a caveat as "not recognised and NOT READ" (`assemble.py`).
- `requirements.CIQ_MODULES` lists no ownership module.
- The page's ownership facts come from EDGAR: Schedule 13D/G filings (`mechanical._ownership_events`) and Form 4 (`mechanical._insider_activity`; `requirements.EDGAR_FREE_INPUTS`). Short interest comes from FINRA (`requirements.FREE_FEED_INPUTS`).
- None of the 36 folders holds a holders, Public Ownership or Insider Trading export (2026-11-11).
- If a CIQ holder field is built, the field contract's F26 governs: the largest holder and the % **as CIQ shows it**. Shares alone give no % (UNAVAILABLE), and insiders CIQ lists as holders are kept. Two rules below contradict it and do not carry over: dividing shares by shares outstanding to make a %, and setting insiders aside before the holders are ranked.

The original rules, kept as history: **Holders file — comprehensive rules.** Header at row 17. Columns: `Holder | [Date1] Common Stock Equivalent Held | [Date2] ... | Latest Common Stock Equivalent Held`. The file lists ~4,000-5,000+ holders for large-cap names; only a fraction are material.

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

**Key Developments** (corrected 2026-11-11, G-D12; this was headed "real RTF" and gave one fixed header). The reader is `ciq_sheets.key_developments`.
- **Format.** All 36 exports on disk are real RTF (2026-11-11), read with `striprtf`. CIQ has also sent one as a spreadsheet (GOOGL's of 2026-09-22, since replaced). The reader refuses a spreadsheet and says so in a QA flag; it never reads one quietly (audit A-D9).
- **Header.** The table is pipe-delimited and its columns are found by header label (`_kd_columns`), never by position. 29 of the 36 carry `Date | Company | Type | Headline | Other Parties` and 7 carry `Date | Type | Headline | Other Parties`. An export with no `Date | Type | Headline` header is flagged as not read, unless the view says in CIQ's words that it has nothing to list.
- **Rows.** Each entry is followed by a "Situation:" paragraph (all 36 exports). The date is a string ("May-11-2026").
- **Filter.** Types pass an INCLUDE list (`_KD_KEEP`). A corporate-event type must be the subject's own event (`_KD_CORPORATE`, `_kd_subject_row`): Company-column match, or the headline's actor where there is no Company column, and always the headline's actor for a Private Placement.

---

## Computational defaults (for Gate 5 historical drawdown and others)

When computing rolling drawdowns from CIQ Charting price history:
- 30-day, 60-day, 90-day rolling windows
- Use closing prices from the dated series (one observation per trading day)
- Drawdown defined as `(price_t / price_max_in_window) - 1`
- Worst drawdown over 5 years = min of the rolling series

---

## Business Relationships export (Customers & Suppliers) — the customer roster (a graph source until #905)

**STATUS, 2026-11-11 (G-D10).** This section was written for `vinci/ciq/relationships.py`, which turned both views into graph edges. That parser had no production caller after #905 and was removed in #964 (`docs/records/2026-11-10-fix2-vinci-ciq-removed.md`; its code: `git show 9da0d096:vinci/ciq/relationships.py`). From *Layout* down, this section is the removed parser's, kept as history. What the code does now:
- **One reader, the Customers file only.** `ciq_sheets.customer_roster` (F27) picks the Customers file by name. No code reads the Suppliers file for a page. RTF and spreadsheet exports go through the same table reader (`_relationship_table`). On disk (36 folders, 2026-11-11) all 36 Customers and all 36 Suppliers files are real RTF.
- **No relationship-type filter.** Every row is kept with its type printed beside it. A row whose type is blank is kept as "type not stated" when it names anything else (V1-O3). On the 35 Customers files with a table, the 2,289 recent rows read: Customer 978, Client Services 921, Distributor 241, Licensee 126, Lessee 12, Borrower 6, Franchisee 3, Tenant 2. BURL's file has no table and says it has none.
- **The five supply-chain types now live in `vinci/graph/extract.py:SUPPLY_CHAIN_TYPES`.** They are the allowed relationship values of the 10-K extraction tool (`EXTRACT_TOOL`), which reads EDGAR 10-K text, never a CIQ export.
- **Columns by header text, never position.** Customers files: 23 carry `Customer Name | Supplier Name | Relationship Type | Primary Industry | Source` and 12 carry `Customer Name | Relationship Type | Primary Industry | Source`. In the five-column view the row prints both parties as stated (`customer ← supplier`); which one is the focal company is not inferred. Suppliers files: 32 five-column, 4 four-column.
- **Not current-only.** All 36 Customers files carry a 'Recently Disclosed Customers' section, and 3 also carry 'Prior and Not Recently Disclosed Customers'. Prior rows are noted beside the value, never counted as current (`_prior_note`).
- **Every view ends with CIQ's closing line** '*denotes proprietary relationship' (72 of 72 files). An RTF view without it may be cut short. The reader says so and gives no count (`_ends_with_closing_line`, RBC-D3).
- **No counterparty is resolved.** The roster prints each row as CIQ states it.

History (the removed parser's, 2026-06): Empirically validated against 32 exports (16 names, both views each), 2026-06.

**File format:** real `.rtf` → `striprtf` (same as Key Developments; NOT the OLE-disguised `.doc` variant — always `file`-check first). After `striprtf` the table is **pipe-delimited** (one `|` per cell, trailing `|`).

**Layout.** Two view types, distinguished by the **column-header order** (the header row contains `Relationship Type`):

| Header order | View | col0 (the named party) | col1 |
|---|---|---|---|
| `Customer Name \| Supplier Name \| Relationship Type \| Primary Industry \| Source` | Customers | the customer (counterparty) | the focal (supplier) |
| `Supplier Name \| Customer Name \| Relationship Type \| Primary Industry \| Source` | Suppliers | the supplier (counterparty) | the focal (customer) |

So **col0 is always the counterparty, col1 always the focal** — identify the focal from the dominant col1 entity (robust to filename/folder), not the filename. Each data row is followed by a `Business Description: …` line (ignore). Entities are `Name (Exch:Ticker)`; private names have no parenthetical; a leading `*` marks a proprietary relationship (strip it). **There is no Current/Former column** — the export is headed "Recently disclosed … (within the last two years)", i.e. current-only.

**Direction:** Customers view → focal **→** counterparty (downstream); Suppliers view → counterparty **→** focal (upstream).

~~**Relationship-type filter (keep supply-chain only).**~~ *Superseded (G-D10): the live reader filters no type; see STATUS above.* The removed parser's 2026-06 observed types by frequency: Supplier (1475), Customer (631), Distributor (324), **Client Services (187)**, Creditor (166), Landlord (154), Licensor (85), Licensee (83), Borrower (65), Lessee (26), Lessor (16), Vendor (15), Tenant (11), Transfer Agent (6), Franchisee (4), Franchisor (1). **Keep:** Supplier, Customer, Distributor, Vendor, Manufacturer. **Drop:** the financial/legal/real-estate types (Creditor, Landlord, Licensor/ee, Borrower, Lessee/or, Tenant, Transfer Agent, Franchisee/or). **Client Services is excluded** by judgment (a softer client relationship, not a goods/services dependency) — revisit if a customer-graph wants it.

**Counterparty resolution:** resolve **US-listed** counterparties by ticker (exchange prefix Nasdaq/NYSE/OTC/BATS/Cboe/AMEX); **non-US** (e.g. TSE, LSE, BSE, KASE) and **private** (no ticker) counterparties are out of the US graph's scope — record them with a reason, never silently drop. A US ticker that fails to resolve (delisted/renamed) is flagged `unresolved_us`, not crashed. Empirically across the 16-name set: 3,257 rows → 812 dropped (non-supply-chain) → 2,445 supply-chain edges → **688 US-resolved**, 1,183 non-US, 522 private, 52 unresolved-US.

---

## Company Comparable Analysis export (peer comps) — valuation-comparability source

`Company Comparable Analysis <name>.xls` — a BIFF `.xls` (xlrd; same reader as Financials). Workbook kind `comps` (filename keyword "comparable"/"comps"), one snapshot file per name. Staged for all current targets (FUBO, VRRM, MVST, BRBR, EPAM).

**EDGE STANCE — this file carries CONSENSUS framings the fund's edge must RESIST, not ingest.** Auto-peer-medians and implied-upside are the face-value comp read; the edge-worthy parts are the peer-set COMPOSITION (who anchors the median) and the fundamental DELTAS (is the discount earned or residual). The extractor captures the roster + market-cap dispersion + business descriptions + deltas — NOT just the summary statistics most comp-parsing stops at — and the synthesis POSES the justified-vs-residual question rather than reading "cheap vs median."

**Layout (constant across names):** title rows carry the target name + as-of date; each data sheet has a header row whose col0 is `Company Name`, followed by ~10 peer rows. Address by sheet NAME — some files carry extra `Credit Health Panel` / `Disclaimer` sheets; ignore them. Find the header by the `Company Name` label, not a hardcoded row index.

**Six sheets — what each feeds:**

| Sheet | Carries | Feeds (extractor) |
|---|---|---|
| **Financial Data** | peer roster + per-peer Market Cap, net debt, TEV, LTM & NTM rev/EBITDA/EBIT/EPS | `peer_set` (roster + market caps → heterogeneity) |
| **Trading Multiples** | LTM TEV/Rev, TEV/EBITDA, TEV/EBIT, P/E, P/TangBV + NTM fwd TEV/Rev, TEV/EBITDA, P/E + High/Low/Mean/Median | `trading_multiples` (name vs peer stats; trailing-vs-forward spread) |
| **Operating Statistics** | margins, 1yr growth, Total Debt/Capital, Total Debt/EBITDA, NTM LT EPS growth, 5y beta | `fundamental_deltas` (growth/margin/leverage/beta — earned-vs-residual). **No concentration here** — concentration stays from EDGAR/CIQ customers+segments, unchanged |
| **Business Description** | peer business description + HQ | `comparability` / `peer_set` (judge comparability by what businesses DO, not size) |
| **Implied Valuation** | peer multiples → target implied value/upside + High/Low/Mean/Median | **SKIPPED** — see below |
| **Valuation Chart** | empty (chart object; ~11 metadata cells, no tabular rows) | **SKIPPED** — not an omission; a CIQ-UI chart container with no data |

**`NM` is a stated marker with no number** (G-D11; this read "`NM` is a REAL value, not missing"). `NM` (Not Meaningful) means a multiple isn't computable — a peer with negative tangible book → P/TangBV `NM`, or negative EBITDA → TEV/EBITDA `NM` (FUBO's own EBITDA multiple is `NM`). In the code it is one of the eight markers (`ciq._UNAVAILABLE_CELLS`): `read_cell` gives no value and the marker `NM`, and `clean_num` gives None, as for `-`. What the code keeps is the STATEMENT: the comps extractor PRESERVES the literal `NM` in its cell (`ciq_sheets._comps_cell`), because it is informative (it signals peer-set heterogeneity), and the Multiples readers say "NM at the latest Close" and refuse a percentile or band rather than reach back to an older close (`ev_ebitda_percentile`, `range_position`, `_own_history_band`, `ev_ebitda_current`, `pe_ltm_current`). `-` is true-missing (a target-row gap) → drop from numerics. Neither carries a number; the two say different things, so never conflate them.

**Implied Valuation — DELIBERATELY SKIPPED (decision, 2026-06).** This sheet applies peer multiples to the target's metrics to derive an implied value/upside — the single most CONSENSUS artifact in the file. We surface NO implied-value/upside number: it is peer-median × target-metric (zero information beyond the peer multiples + target absolutes already captured), and even framed it becomes the anchor the edge exists to resist (the dead-signal/consensus trap). The edge-worthy substitute — the peer-multiple GAP carried WITH composition + deltas — lets the human form the divergent view without a consensus number. Recorded so the skip reads as deliberate.

---

## What this file does NOT cover

Not a CIQ user manual. Not exhaustive of every CIQ module. If PM uploads a CIQ file type not described above and LLM can't determine structure from inspection, LLM surfaces to PM and asks for the first 20 rows pasted as text so PM can confirm format before LLM extracts.

For tool inventory and source-to-question mapping, see `data_sources.md`. This file is purely about extraction mechanics.

---

## 2026-11-11 corrections

**Reference notes, not the spec.** These notes were written for a chat-session LLM reading CIQ files
by hand (the Sessions A–C framework), and came into this repo on 2026-06-18 (`5a1469b2`). Here code
reads the exports. Where this file differs from the code (`vinci/dossier/ciq.py`,
`vinci/dossier/ciq_sheets.py`) or from the CIQ field contract (TeamNostra's; held by the operator,
not committed), the code and the contract are right.

Corrected 2026-11-11 (fix request 2, order 9). Each correction was checked against the code and the
36 ticker folders under `data/manual/ciq/` on that date. Every line that code or tests cite by number
(61, 63-66, 74, 116, 126, 136-138, 197, 204) keeps its number; corrections above line 205 are
made in place on the same line.
- **G-D8.** The Surprise sheet has fiscal-quarter and company-level (Revenue, EBITDA …) blocks; the
  code reads its fiscal-year table only. *Surprise basis*; *Estimates Report → Surprise sheet*.
- **G-D9.** No code reads a holders export; the holder rules are marked superseded. *Holders file*.
- **G-D10.** The live relationships reader keeps every relationship type; the supply-chain filter
  was the removed `vinci/ciq/` parser's. *Business Relationships export*.
- **G-D11.** The missing-data markers are the code's set, and `NM` is a marker with no number.
  Universal rule 1; the *Supplemental* / *Industry Specific* rows and the empty-subsheet rule;
  *`NM`* under comps.
- **G-D12.** Key Developments: RTF on disk, but a spreadsheet export has occurred and is refused,
  and the header varies. The file-format table; *Key Developments*.
- **G-D13.** The driver step reads figures from the transcripts; the output cap is 16,384 tokens; a
  missing `evidence_balance` is flagged, not refused. *Transcript*; *Synthesis truncation*.
- **G-D14.** `checklist.md` is not in this repository. Line 5; the Part 0 gate paragraph under
  *Financials export*.
- **G-D15.** Nothing here: the temperature and re-roll statements are corrected in
  `docs/engineering.md` and `docs/RUNBOOKS.md`.
