# Archetype scope pack 1: the findings (taxonomy, census, $0 probe, 5a builds, D13 audit)

> **What this file is.** The evidence behind `docs/scope-pack-archetypes-1.md`, committed by the
> operator's decision of 2026-11-19 ("Commit it"); the record is
> `docs/records/2026-11-19-archetype-scope-pack-1.md`. It is the archetype probe's working document,
> **scrubbed for this public repo**:
> - no local paths, emails, credentials or machine names;
> - no transcript words;
> - no text from another party's documents beyond an ID.
>
> **CIQ values.** Quoted only where their cell is recorded: the workbook's sha256[:10], sheet, row and
> column, knowable from the export date, 2026-11-19 (CIQ is not point-in-time). Every other CIQ value
> the working document held (multiples, band levels, consensus figures, values per share derived from
> them) is withheld here and marked *[CIQ value withheld]*. The scripts regenerate them
> (`scripts/archetype_probe/`), and the pack's §0 states each boundary. EDGAR figures (with
> accessions), SEC frame counts and Polygon closes stand as written.
>
> Sections were written in sequence (steps 2–4, then 5a, then the fresh-export rerun). A cell a later
> step changed shows the old reading struck and the new one beside it.


**Session:** archetype probe (started by coordinator B). **Date:** 2026-11-19. **Code:** `main` at
`8bc138cd` (#1133), read-only. **Cost:** $0. No LLM client was constructed, no paid run, no page
written, nothing committed, Drive read only. Every EDGAR read went through `vinci.sec.build_sec_http`
/ `EdgarClient` (the project's SEC user agent, the machine-wide SEC limiter), every Polygon read
through `PolygonEodClient` (3 calls in total: one grouped daily, two ticker details). Caches were
written only to a scratch folder outside every checkout. Scripts: `scripts/archetype_probe/` (README there).

**5a close-out added 2026-11-19 (§11)**, on `main` `9d036cbb`, still $0 and read-only. The §6
readiness grid is updated in place, and D11–D16 are added to §9. In short:
- **0 of 16 full $0 builds would pass the precheck today.** Every name without a CIQ export gets the
  same two refusals the paid build makes only after its spend, the proven-path control SPGI
  included. All four 2026-10-28 packs are outdated by a later filing.
- **A loss-maker never routes to `R2_NEEDED`** (D12).
- **EPD's P/E note states a false cause** (D13, the one wrong-output finding). Audited on the
  live corpus in §11e: the claim is TRUE on all 5 live pages and 107 of 109 candidate records, and
  FALSE on none. ORC's record is the near miss: its newest annual EPS is positive.
- **Nothing at intake refuses an out-of-scope kind** once its roster line is written. PCVX would be
  paid for in full after a re-export.
- **Fresh exports (§11f, main `6e03501f`, the operator's 2026-11-19 packs).** 3 of the 6 re-exported
  names now pass the precheck with 0 refusals: PLD, AWK and MORN. **AWK and MORN price on R1 at $0**
  (firm). PLD passes the precheck, yet nothing on its page can be priced. RIVN, DVN and AQN are
  refused before any model call. None of the three is a timing refusal; each is a fact about the
  export or about CIQ's own data: RIVN's CIQ export disagrees with itself (D18; no re-export clears
  it), DVN's quarterly file is a copy of its annual file, and AQN's pack was exported from its TSX
  listing (one panel in CAD). New: D17 (the R4 bridge reads a cash total that CIQ's REIT and
  utility balance sheets don't carry), D18, D19 (a missing required export only raises a caveat; it
  doesn't refuse). D11 now shows on two more refusal classes. No machine R4 proposal on any page.
- **MORN's EBITDA anomaly, tested (§11f addendum 1):** a definitional difference inside CIQ (its
  annual EBITDA excludes 'Other Amortization'; 719.4 + 102.7 = 822.1 exactly). No consumer reads
  the wrong figure, but two labels are missing or misleading: D20.
- **AQN and DVN, updated (§11f addendum 3).**
  - AQN can't be re-exported: CIQ has no NYSE:AQN listing (the operator). That is a finding, D21: a home-market primary listing puts one market-data panel in its trading currency and refuses a USD pack. Its population is not measurable from the data held. The substitute G17 test name is **DAC**, with TK as the alternate.
  - ~~DVN's 17:19Z quarterly re-export is an annual export again, so it is refused the same way and still owes a Period-Type-Quarterly export.~~ **2026-11-20:** DVN's quarterly re-export IS quarterly and passes the precheck, with R1's value withheld under W73. DAC's pack landed and passes, with R1 declining on a new finding, D22. Both in §11f addendum 4.
- **5b scope pack:** `docs/scope-pack-archetypes-1.md`, committed for review on the operator's
  decision of 2026-11-19 ("Commit it").

---

## 0. Bottom line

0. **The count.** The proven archetype (a 10-K operating company with positive recent operating
   income) is **793 of the screen band's 2,065 companies (38.4%, 42.7% of its cap)** and **435 of the
   large-cap band's 928 (46.9%, 60.1% of cap)**. Archetypes with **no recipe a page can be
   underwritten on today** are **42.9% of the screen band and 31.1% of the large-cap band**:
   pre-profit, pre-revenue, banks, lenders, insurers, broker-dealers, IFRS or non-USD FPIs, and
   filers with no annual report on file. The rest reach a recipe, though REITs, utilities and MLPs
   only on a basis that is not their valuation method.
1. **The pipeline is proven on one archetype, and the probe confirms that archetype is the one it
   serves:** a US-incorporated 10-K filer that is a profitable operating company and tags
   `OperatingIncomeLoss`, with one share class and debt in a tag the net-debt builder reads. SPGI,
   FICO, FDS, VRSK, MORN, LOW, TTWO, AWK, FCX, AQN (a 40-F filer reporting US GAAP in USD) and BRBR
   (the page control) pass every deterministic layer. Their fiscal years end in December, August,
   September, January and March, and two have negative equity (LOW, FICO).
2. **Everything else mostly REFUSES LOUDLY, as designed.** Banks, lenders and insurers have net
   debt refused by the SIC rule, and the anchor reads no margin. IFRS and non-USD foreign filers
   have every EDGAR money figure withheld, and CIQ refuses a non-USD workbook. Pre-profit and
   pre-revenue names route to `R2_NEEDED`, which is not built. That is the honest state. These
   names are not silently mis-valued, but nor can any of them get a page that answers its question.
3. **Three findings are "produces something wrong"** (all deterministic, all reproducible, none
   fixed — reported per "hold scope"):
   - **INVH (a REIT under SIC 6510):** the anchor takes a $59.5M ASC 606 *component* as total
     revenue for FY2015 and prints a **192.1% mid-cycle operating margin**. The `Revenues` line
     has 10 years and $2,729M for FY2025. The R1 value is then refused for a missing D&A tag, so
     the wrong number is the printed margin, not a price.
   - **NBIS (Nebius, an FPI whose business changed in 2024):** the R1 margin is **+15.2% from its
     FY2018–19 Yandex-era revenue tag**, while operating income was negative every year
     2021–2025. A divested business's margin passes the R2 gate. It is flagged
     `revenue_tag_conflict` and capped weak, but R1 rather than R2 is assigned.
   - **SCHW (SIC 6211):** net debt computes **−$12.85bn** for a savings-and-loan holding company.
     The 60/61/63 SIC rule does not cover 6211.
4. **Several pipeline-wide gaps surfaced that are not archetype-specific but hit some archetypes
   hard:** `OperatingIncomeLoss` is untagged by LLY, PFE, JPM, CB, PGR, AJG, SCHW, MTB and O, and
   stale since 2016 for DVN, so R1's margin then needs CIQ's financial summary (LLY's committed
   page does exactly that: "financial_summary (short history)", weak). Net debt refuses when debt
   sits in `UnsecuredLongTermDebt` (CME), `LongTermNotesAndLoans` (ORCL) or `NotesPayable` (O,
   VMRK), and when there is no debt at all (ISRG, TPL). Multi-class filers (EL, HSY, BRK) get no
   current cover share count. Nor do NEE and PLD, both combined filers whose counts stop at the
   Q1-2026 10-Q; the cause was not verified.
5. **The #1132 event rule reads 20-F, 40-F and 6-K correctly,** but for a foreign filer every
   6-K outdates a CIQ export. At the observed spacing, an export for NVO lives about 6 days
   (61 6-Ks a year), TSM 7, BABA 7, NBIS 8.5 and FNV 12. **207 of the screen band's 255 FPIs (81%)**
   filed six or more 6-Ks in 180 days. The inference, not measured (no FPI page was built): the gate
   will refuse most FPI builds unless the export is pulled within days of the build.
6. **Stage 2 is mostly a data-source build, not a code change.** Top-5 markets by domestic
   market cap at end-2025 (SIFMA Fact Book 2026, Table 3, WFE data): **US $68.9T, China $15.5T,
   India $10.6T, Japan $7.6T, Hong Kong $6.1T**. The UK is 6th at $5.6T; the EU as a bloc is
   $15.5T. In a 95-name large-cap list, **44 do not report to the SEC at all**, and of the 51 that
   do, **only 4 report US GAAP in USD** (SHOP, YUMC, ONC, ARM). The other 47: 35 IFRS, 11 US GAAP
   in another currency, and 1 with no XBRL companyfacts (ICICI). The operator's two named
   European names are both non-SEC: Saint-Gobain has an SEC CIK for an OTC line and files nothing,
   and EssilorLuxottica has no CIK at all.
7. **One named name, and two other probed names, changed identity this year:** **AVB deregistered** (Form 15-12G
   2026-08-27, 15-15D 2026-09-16), and **EQR's CIK is now "Vivmark Residential" (VMRK)**, with
   an 8-K carrying items 2.01 and 5.03 on 2026-08-17. **XOM moved to a successor CIK**
   (ExxonMobil Holdings Corp, 0002115436; the old CIK filed a 25-NSE on 2026-07-02). The successor
   has filed no 10-K yet, so every EDGAR leg is UNKNOWN. The fundamentals layer does not stitch a
   predecessor's history (`predecessor_cik` is used only by the price-tenure aliases).

---

## 1. Inputs and their boundaries

| input | what | boundary |
|---|---|---|
| primary universe | `data/snapshots/universe_snapshot.jsonl` (committed) | 2,065 lines = 2,065 distinct CIKs; as_of **2026-10-16**; band $300M–$10B; NYSE/Nasdaq/NYSE American; ADV ≥ $3M; SIC deny-list 6189/6221/6722/6726/6770 (`config.UniverseConfig.excluded_sic_codes`) — **banks, insurers and REITs are admitted** |
| theme universe | `data/snapshots/theme_universe_snapshot.jsonl` (committed) | 928 CIKs; as_of **2026-08-24**; band ≥ $10B (the large-cap set the operator's names mostly sit in) |
| union | both | **2,931 distinct CIKs** (62 sit in both: re-banded between the two dates) |
| SIC | EDGAR submissions, fetched 2026-11-19 via the repo's SEC client | per CIK; falls back to committed `issuers.jsonl` |
| tag signals | SEC XBRL frames (`EdgarClient.frame` URL shape), `us-gaap`, USD, `CY2025`/`CY2024` durations and `CY2025Q4I` instants | fetched 2026-11-19; frames are SEC's calendar-aligned one-fact-per-filer views, **not point-in-time** (FL-D12), adequate for a census, never for a value |
| FPI currency/namespace | companyfacts via `concepts.reporting_currency` + `filer_fiscal_year` | another checkout's SEC cache, read-only, where it held the document (its fetched_at stated per CIK), else fetched 2026-11-19 |
| stage-2 market sizes | SIFMA Capital Markets Fact Book **2026 Edition**, Table 3 p.13 (source: World Federation of Exchanges) | "market capitalization of listed domestic companies", $B, year-end **2025**; EU shown as a bloc, HK separate from China |
| probe | 64 tickers (61 reached a CIK; AVB, EQR, ABB did not — each checked by CIK) | cut 2026-11-19; prices = Polygon grouped daily **2026-11-18** |
| CIQ | the live CIQ folder (`<CIQ root>/{LLY,BRBR}`) + the dated 2026-10-28 packs (`<packs root>/{MTB,PLD,NVO,PCVX,RIVN}_<id>/2026-10-28`) | copied to scratch, read by the repo's readers, copies deleted; Drive never written |

---

## 2. The taxonomy — derived from what makes the pipeline behave differently

Method: start from B's dimensions, keep a split only where some layer's code takes a different
branch or reads a different tag; merge where it does not. The signal for each archetype is
observable without judgment.

### Axis A — filing regime (exactly one per company)

| archetype | signal | why the pipeline differs |
|---|---|---|
| A1 US 10-K, US-incorporated | latest annual `10-K`/`10-KT`; `stateOfIncorporation` a US state | the proven path |
| A2 10-K, foreign-incorporated | latest annual `10-K`; foreign incorporation code | same readers as A1; currency can still be non-USD (ENB: CAD) → FPI1a guard |
| A3 FPI, US GAAP, USD | `20-F`/`40-F`; newest fiscal year us-gaap; `reporting_currency` USD | EDGAR legs read; 6-K event cadence; ADS ratio (FPI4); insider window (FPI3) |
| A4 FPI, US GAAP, non-USD | as A3, currency ≠ USD | every money figure withheld (`foreign_currency`, FPI1a) until FPI1b's FX ruling |
| A5 FPI, IFRS | newest fiscal year is an `ifrs-full` year (`FiscalYear.ifrs_end`) | `IFRS_FLOW_TAGS` date the year only — "no reader serves an IFRS figure"; companyfacts lacks the newest IFRS year for 61/164 (FPI1c) |
| A6 non-SEC | no CIK, or a CIK with no annual report and 404 companyfacts | nothing to read: no fundamentals, no event rule, Polygon grouped daily carries no OTC line |
| (A7) no annual yet / successor | a 10-Q filer with no 10-K on its CIK | fiscal year undatable; everything UNKNOWN (XOM) |

### Axis B — statement form (exactly one; SIC first, tag overrides stated)

| archetype | signal | pipeline behaviour that justifies the split |
|---|---|---|
| B1 bank | SIC 6021/6022/6029/6035/6036 | net debt refused by SIC rule (`net_debt._NOT_APPLICABLE_SIC_GROUPS`); `OperatingIncomeLoss` untagged → anchor UNRESOLVED; CIQ carries no EBITDA/EV band (MTB: P/LTM EPS band only, no consensus multiples) |
| B2 lender / specialty finance | SIC 6099, 61xx | net debt refused (60/61); revenue tag often absent (SYF) |
| B3 insurer (underwriting) | SIC 6311/6321/6331/6351/6361/6399 | net debt refused (63); `OperatingIncomeLoss` untagged (CB, PGR) |
| B4 managed care | SIC 6324 | **behaves like an operating company on every layer except net debt, which the 63 rule refuses** (UNH, CNC) — a design question, not a bug |
| B5 insurance broker | SIC 6411 | net debt left in (fee business, by design); AJG tags no `OperatingIncomeLoss` |
| B6 broker-dealer / IB | SIC 6211 | **not** in the SIC rule: GS's builder refuses on under-capture (loud); SCHW computes a meaningless −$12.85bn (wrong); BLK (also 6211) is fine |
| B7 asset manager / exchange | SIC 6200/6282 | operating-like (CME, MORN pass the anchor) |
| B8 REIT | SIC 6798, **plus** INVH-type (6510 with `RealEstateInvestmentPropertyNet`) | revenue is LEASE income (not in `CONCEPT_ALIASES['revenue']`): INVH wrong margin, O/VMRK no reliable revenue tag; FFO/AFFO/"funds from operations": zero hits in `vinci/**/*.py`, none by `git log -S FundsFromOperations` or commit message; NAV/cap rate appear only in theme-intelligence prose |
| B9 real-estate operator | SIC 65xx | as B8 when it is a REIT by another code — counted separately so the overlap is visible |
| B10 regulated utility | SIC 4911/4924/4931/4932/4941/4961/4991 | R1 works mechanically (AWK, NEE); method gap (rate base / allowed ROE); NEE's co-registrant share count stops at Q1-2026 |
| B11 partnership / MLP | `PartnersCapital`/`LimitedPartnersCapitalAccount` frame, or "L.P." | EPS per unit not read (EPD's diluted EPS stale since 2011, MPLX none) → screen P/E UNKNOWN; R1 legs pass |
| B12 royalty / patent owner | SIC 6792/6794/6795 | operating-like; debt-free → net debt refused (TPL) |
| B13 holding / investment office | other SIC 67xx | (few) |
| B14 operating company | everything else | the proven path, split by axis C |

### Axis C — economic model (operating companies only; exactly one)

| archetype | signal | pipeline behaviour |
|---|---|---|
| C1 pre-revenue | < $10M revenue in both CY2024 and CY2025 frames | anchor UNRESOLVED (no revenue tag: PCVX) or margin not computable (VKTX); CIQ multiples NM |
| C2 pre-profit | `OperatingIncomeLoss` ≤ 0 in both CY2024 and CY2025 | anchor → `R2_NEEDED` (RIVN, CRWV) — **R2 is not built** (STATE row 10) |
| C3 reserve-based | SIC 1000/1040/1090/1220/1221/1311/1400 | R1 is mechanically fine where tagged (FCX); E&Ps often stop tagging `OperatingIncomeLoss` (DVN, stale since FY2016) |
| C4 profitable operating | positive operating income in a recent year | **the proven path** |
| (C5) OI untagged | revenue present, no `OperatingIncomeLoss` in either frame | R1 margin leg needs CIQ's `financial_summary` (weak) — counted as an overlap, not an archetype |

**Merged, because the pipeline does not branch on them:** compounder vs cyclical (R1's mid-cycle
median IS the cyclical treatment; both reach R1/R3/R4), subscription vs not (no RPO, deferred
revenue or bookings metric exists — found only as prose matchers in `render.py`/`synthesis.py`/
`filing_sections.py`), odd fiscal year (52/53-week and non-December years all dated correctly:
LOW 363d, BRBR, FDS, FICO, EL, ORCL, TTWO), negative equity (nothing reads book equity for value).

### Overlap flags (a company may carry several; each changes one layer)

share-count unreadable (multiple classes, co-registrant cover, period-average only) · depositary
(ADS) line · `OperatingIncomeLoss` untagged · lease-heavy · deferred-revenue/backlog heavy ·
capex-heavy · SBC-heavy · negative equity · non-December FY · transition period · M&A completed
(8-K 2.01) · Form 10 registrant (spin-off) · recent IPO · 6-K-heavy (event rule) · SIC 4922/4923
midstream.

---

## 3. The count

**Boundary for every count in this section:** the two committed universes (screen band
`universe_snapshot.jsonl` as_of 2026-10-16, 2,065 CIKs; large-cap band
`theme_universe_snapshot.jsonl` as_of 2026-08-24, 928 CIKs; union 2,931 distinct CIKs), unit =
company (CIK). Cap weights use each band's own snapshot cap at its own date; the union uses a
CIK's larger cap. SIC and forms were read 2026-11-19 (0 of 2,931 submissions failed); tag
signals come from SEC frames fetched 2026-11-19 (57 frames read, 4 returned 404: `SalesRevenueNet`
and `RoyaltyRevenue` have no CY2024/CY2025 frame); FPI currency comes from companyfacts (189 read
from the primary's cache, fetched 2026-08-06 → 11-13; 227 fetched 2026-11-19; 3 returned 404).

**Cross-check against an earlier independent measurement.** STATE row 4 (2026-10-28) counted 262
primary FPI-rule lines: 164 IFRS, 66 US GAAP USD, 21 US GAAP non-USD, 4 unresolved, 7 not FPIs.
This census, by latest annual form at 2026-11-19, counts 255 FPIs in the screen band: **165 IFRS,
65 US GAAP USD, 21 US GAAP non-USD (20 CNY, 1 HKD), 4 unread**. Same population, same split
within one company per cell.

### 3a. One archetype per company (the grid's rows)

Precedence, first match wins: no annual report → FPI IFRS → FPI US GAAP non-USD → FPI US GAAP
USD → statement form → economic model. A 10-K filer with a blank incorporation field (204 of
2,459) is classed by its business address.

| grid archetype | screen band n (%) | screen cap % | large-cap band n (%) | large-cap cap % | union n | e.g. |
|---|---|---|---|---|---|---|
| G01 **PROVEN PATH** · 10-K operating, positive OI | 793 (38.4%) | 42.7% | 435 (46.9%) | 60.1% | 1,202 | CECO, MATX, UHAL-B, AAL |
| G02 10-K operating · OI untagged | 60 (2.9%) | 3.2% | 60 (6.5%) | 6.6% | 115 | AIR, HRB, CMC, GATX |
| G03 10-K operating · pre-profit | 271 (13.1%) | 10.1% | 37 (4.0%) | 1.6% | 302 | COHU, KODK, KELYA, KLIC |
| G04 10-K operating · pre-revenue | 112 (5.4%) | 3.4% | 6 (0.6%) | 0.1% | 116 | CLDX, VGZ, GERN, ORKA |
| G05 10-K operating · reserve-based | 46 (2.2%) | 2.3% | 17 (1.8%) | 1.0% | 62 | CRK, PNRG, USLM, MUX |
| G05b 10-K operating · no USD frame data | 15 (0.7%) | 0.4% | 3 (0.3%) | 0.3% | 18 | MTH, ACHV, NB, TMQ |
| G06 bank | 161 (7.8%) | 6.5% | 27 (2.9%) | 3.2% | 184 | ASB, CBSH, SRCE, FFIN |
| G07 lender / specialty finance | 52 (2.5%) | 2.0% | 10 (1.1%) | 0.6% | 61 | FWDI, WRLD, CLSK, AGM |
| G08 insurer | 45 (2.2%) | 2.9% | 27 (2.9%) | 1.9% | 71 | LNC, MCY, ORI, RLI |
| G09 managed care | 4 (0.2%) | 0.2% | 6 (0.6%) | 0.7% | 10 | TRUP, OSCR, CLOV, ALHC |
| G10 broker-dealer / IB | 9 (0.4%) | 0.6% | 10 (1.1%) | 1.4% | 18 | JEF, OPY, WT, PIPR |
| G11 asset manager / exchange | 23 (1.1%) | 1.8% | 16 (1.7%) | 0.9% | 38 | AB, VRTS, SNEX, AMG |
| G12 insurance broker | 9 (0.4%) | 0.5% | 7 (0.8%) | 0.4% | 16 | CRVL, GSHD, BWIN, ACT |
| G13 REIT (SIC 6798) | 94 (4.6%) | 4.9% | 37 (4.0%) | 1.5% | 128 | ALX, CTO, CUZ, FRT |
| G13b real-estate operator (65xx; INVH-type REITs inside) | 20 (1.0%) | 0.8% | 3 (0.3%) | 0.1% | 23 | JOE, PDM, GTY, GOOD |
| G14 regulated utility | 29 (1.4%) | 1.9% | 35 (3.8%) | 1.7% | 64 | MSEX, MDU, NFG, AVA |
| G15 partnership / MLP | 15 (0.7%) | 0.6% | 7 (0.8%) | 0.3% | 22 | IEP, SPH, GEL, ARLP |
| G16 royalty / patent owner | 6 (0.3%) | 0.4% | 2 (0.2%) | 0.1% | 8 | APPS, PBT, SSRM, DLB |
| G16b holding / investment office | 1 (0.0%) | 0.1% | 0 | 0.0% | 1 | HASI |
| G17 FPI · US GAAP USD · operating | 57 (2.8%) | 2.2% | 11 (1.2%) | 0.6% | 68 | TATT, GILT, TK, NAT |
| G17b FPI · US GAAP USD · other form | 8 (0.4%) | 0.4% | 0 | 0.0% | 8 | CIGI, AQN, NMM, PLGO |
| G18 FPI · US GAAP non-USD (or unread) | 25 (1.2%) | 1.4% | 24 (2.6%) | 2.5% | 47 | AUGO, JKS, VNET, GDS |
| G19 FPI · IFRS (any form) | 165 (8.0%) | 9.2% | 141 (15.2%) | 12.7% | 297 | PHI, ASM, CMCL, WPP |
| G20 no annual report on file (new registrant / successor) | 45 (2.2%) | 1.5% | 7 (0.8%) | 1.8% | 52 | OGC, GORO, AVLN, PBLS |
| **total** | **2,065** | **$5.99T** | **928** | **$88.01T** | **2,931** | |

**Read:** the proven path is **38.4% of the screen band by count (42.7% by cap) and 46.9% of the
large-cap band (60.1% by cap)**. Financial balance-sheet forms (G06–G10) are **13.1%** of the screen
band (271 of 2,065); real estate (G13 + G13b) **5.5%** (114); SEC-filing foreign issuers (G17–G19)
**12.3%** of the screen band (255) and **19.0%** of the large-cap band (176); pre-profit + pre-revenue (G03 + G04) **18.5%** of the screen
band.

**Caveats on the operating-company split (G01–G05).** "Pre-profit" here means
`OperatingIncomeLoss` ≤ 0 in both the CY2024 and CY2025 frames. That is a proxy, not the anchor's
gate, which routes to `R2_NEEDED` only when the median over the filer's whole history is ≤ 0. The
two disagree on two probed names: TTWO is pre-profit by the proxy (FY2024–25 impairments) but has
a +6.3% 10-year median, so R1 passes; CRWV shows positive CY2025 operating income by the proxy
but a −0.9% three-year median, so it routes to R2. The proxy sizes the archetype; it does not
predict a page's recipe. Within G01, 103 screen-band names (13%) carry a share-count flag (per-class
cap, or no filed point-in-time count), 265 (33%) a non-December year and 208 (26%) an 8-K 2.01 in
the last two years.

### 3b. Overlap flags (a company may carry several)

| flag | screen band (of 2,065) | large-cap band (of 928) |
|---|---|---|
| acquisition/disposal completed (8-K item 2.01) in 2y | 464 (22.5%) | 135 (14.5%) |
| non-December fiscal year | 395 (19.1%) | 228 (24.6%) |
| SBC ≥ 10% of revenue | 300 (14.5%) | 80 (8.6%) |
| no filed point-in-time share count (cap on a period average / Polygon) | 229 (11.1%) | 92 (9.9%) |
| S-1 / F-1 / 424B4 in 3y (short public history) | 213 (10.3%) | 33 (3.6%) |
| ≥ 6 Form 6-Ks in 180d (the event rule outdates an export within ~a month) | 211 (10.2%) — **207 of the 255 FPIs (81%)** | 158 (17.0%) — **158 of 176 FPIs (90%)** |
| deferred revenue ≥ 25% or RPO ≥ 100% of revenue | 149 (7.2%) | 108 (11.6%) |
| capex ≥ 15% of revenue | 127 (6.2%) | 63 (6.8%) |
| negative equity | 115 (5.6%) | 40 (4.3%) |
| registered via Form 10 (spin-off / direct listing) | 115 (5.6%) | 24 (2.6%) |
| depositary (ADS) line | 85 (4.1%) | 106 (11.4%) |
| op-lease liability ≥ 20% of assets | 77 (3.7%) | 24 (2.6%) |
| `OperatingIncomeLoss` untagged, revenue present (operating cos.) | 65 (3.1%) | 65 (7.0%) |
| multiple share classes (per-class cap) | 39 (1.9%) | 18 (1.9%) |
| SIC 4922/4923 gas transmission (midstream, counted as operating) | 11 (0.5%) | 11 (1.2%) |
| transition period filed in 3y | 9 (0.4%) | 1 (0.1%) |

**REITs outside SIC 6798:** 13 companies carry `RealEstateInvestmentPropertyNet` ≥ 50% of assets
under another SIC (INVH 6510, TRNO, GTY, IIPR, UE, CURB, HPP, AHRT 6500, GOOD 6519, PDM 6512, JOE
6552, and SHO, XHR under 7011 hotels; all 13 shown). Of the 129 SIC-6798 companies, 91 carry the
tag at CY2025Q4I. A REIT rule keyed on SIC 6798 alone would miss INVH.

### 3c. The operator's named names in the census

| name | band | regime | form / model | flags |
|---|---|---|---|---|
| TTWO | large-cap | 10-K US | operating · pre-profit by proxy (anchor median +6.3%) | non-Dec FY; 424B4 in 3y |
| EL | large-cap | 10-K US | operating · positive OI | no filed point-in-time share count; non-Dec FY |
| BRBR | screen | 10-K US | operating · positive OI | negative equity; non-Dec FY |
| HSY | large-cap | 10-K US | operating · positive OI | — (share count refused at the probe) |
| LLY, PFE | large-cap | 10-K US | operating · **OI untagged** | — |
| ISRG, GILD, SPGI, FICO, FDS, VRSK, LOW, ORCL | large-cap | 10-K US | operating · positive OI | SPGI/ORCL deferred revenue; ORCL capex-heavy; FICO/LOW negative equity |
| CRWV | large-cap | 10-K US | operating · positive OI by proxy (anchor: R2) | deferred revenue, capex-heavy, SBC-heavy, no filed count |
| BRK-B | large-cap | 10-K US | **insurer** | multiple share classes |
| MORN | screen | 10-K US | asset manager | — |
| INVH | large-cap | 10-K US | **real-estate operator (a REIT under SIC 6510)** | — |
| NBIS | large-cap | **FPI 20-F US GAAP USD** | operating · pre-profit | deferred revenue, capex, SBC, 6-K-heavy |
| AVB | — | **not in either universe** (deregistered) | | |
| EssilorLuxottica, Saint-Gobain | — | **non-SEC** (stage 2) | | |

---

## 4. Stage 2 — top-5 markets and a representative large-cap list

**Top markets by domestic market cap, year-end 2025** (SIFMA Capital Markets Fact Book 2026
Edition, Table 3, p.13; source WFE; "market capitalization of listed domestic companies", $B):

| rank (country) | market | $T | note |
|---|---|---|---|
| 1 | US | 68.94 | 43.7% of $157.77T |
| 2 | China | 15.51 | mainland exchanges |
| — | EU (bloc) | 15.46 | not a country; shown as one line by SIFMA |
| 3 | India | 10.56 | |
| 4 | Japan | 7.61 | |
| 5 | Hong Kong | 6.09 | SAR; separate line from China |
| 6 | UK | 5.64 | |
| 7 | Canada | 4.62 | |

**So "top 5 countries" is ambiguous in two ways the operator must settle:** whether the EU counts
as one market (then: US, China, EU, India, Japan), and whether Hong Kong is counted apart from
China (if merged, the UK enters 5th).

**Representative large-cap list — 95 names, SEC status MEASURED per name.** Selection is general
knowledge of each market's largest listed companies, **not a measured market-cap ranking** (no
repo source holds non-US caps); every status below is measured. Three searches per name: (a) the
US ticker in SEC `company_tickers*.json`, (b) every name token as a substring of every issuer name
in that index, (c) EDGAR full-text search for the name in 20-F/40-F/6-K/10-K filed 2024-01-01 →
2026-11-19, counting only hits whose FILER is the name. **Truncation:** (c) read the first results
page per token (≤100 hits); a self-filed hit beyond it would be missed — (a) and (b) are
independent and also found nothing for every "not found" name.

| market (names) | current SEC reporter, US GAAP USD | current SEC reporter, US GAAP other currency | current SEC reporter, IFRS | 20-F, no companyfacts | lapsed SEC reporter | SEC CIK, OTC line only, no reports | not found |
|---|---|---|---|---|---|---|---|
| EU (27) | 0 | 1 (ASML EUR) | 10 | 0 | 1 | 2 | 13 |
| UK (10) | 1 (ARM) | 0 | 9 | 0 | 0 | 0 | 0 |
| Switzerland (6) | 0 | 0 | 2 | 0 | 1 (ABB) | 0 | 3 |
| Japan (14) | 0 | 2 (MUFG, MFG: JPY) | 5 | 0 | 1 (Hitachi) | 1 (SoftBank) | 5 |
| China / HK (20) | 2 (YUMC, ONC: 10-K) | 6 (CNY ADRs) | 0 | 0 | 1 (PetroChina) | 5 | 6 |
| India (11) | 0 | 1 (HDB: INR) | 4 | 1 (ICICI) | 0 | 0 | 5 |
| Canada (6) | 1 (SHOP: 10-K) | 1 (ENB: 10-K, CAD) | 4 (40-F) | 0 | 0 | 0 | 0 |
| Taiwan (1) | 0 | 0 | 1 (TSM) | 0 | 0 | 0 | 0 |
| **all (95)** | **4** | **11** | **35** | **1** | **4** | **8** | **32** |

Per name (status · CIK · latest annual): `stage2_rows.json`, regenerated by `scripts/archetype_probe/stage2.py`. The operator's two:
**EssilorLuxottica — not found** (no CIK by ticker or name; 24 full-text hits, none self-filed;
Polygon knows an OTC unsponsored ADR `ESLOY`, type ADRC); **Saint-Gobain — SEC CIK 0001012037 for
the OTC line `CODGF`, no annual report, companyfacts 404** (Polygon: `CODYY`, ADRC).

**Read:** **44 of 95 (46%) do not report to the SEC**; of the 51 that do, **47 need FX and/or IFRS
reading** before any EDGAR money leg returns a value — only 4 are on today's readable path. By
market, SEC reachability is highest for the **UK (10/10)** and Canada (6/6), then EU (11/27),
Switzerland (2/6), Japan (7/14), India (6/11), China/HK (8/20). Every Japanese, Indian, Swiss and
UK SEC reporter in the list files on 20-F; Canada's mostly on 40-F. Many FPIs switched to IFRS
while still carrying older us-gaap facts (Toyota, Sony, Honda) — the IFRS test must read the newest
fiscal year (`FiscalYear.ifrs_end`), not a concept count, or it misclasses them as US GAAP JPY (the
first cut of this table did).

---

## 5. The probe

**Sample:** 64 tickers requested — the operator's 22 (EssilorLuxottica and Saint-Gobain via the
stage-2 searches and Saint-Gobain's OTC CIK `CODGF`), ~2 large caps per hard archetype, and one
**median-cap screen-band name per hard archetype** chosen by a fixed rule (the median by cap
within the archetype in the 2026-10-16 screen band: BFC bank, NMIH insurer, PEB REIT, AQN
utility, SECZ lender, DRD foreign filer), so the screen population is represented, not only
large caps. 3 did not
resolve, each for a corporate reason checked by CIK: **AVB** (Form 15-12G 2026-08-27), **EQR**
(renamed — its CIK 0000906107 is now Vivmark Residential, `VMRK`, probed instead), **ABB**
(lapsed 20-F filer; last 20-F 2024-02-23). **O** was added as a second plain REIT.

**Layers run, each through the repo's own function** (nothing re-implemented):
`EntityResolver.resolve_ticker(enrich=True)` · submissions (`EdgarClient._submissions`) ·
`EdgarClient.companyfacts` + `concepts.facts_as_of(…, 2026-11-19)` · `concepts.reporting_currency`
· `concepts.filer_fiscal_year` · `client.compute_fundamental_snapshot` (the screen's EDGAR legs) ·
`anchor._total_revenue_series` → `midcycle.annual_series("operating_income")` →
`midcycle.margin_anchor`, in `compute_anchor`'s gate order, + `anchor._latest_dep_amort`,
`anchor._latest_fcf` · `net_debt.not_applicable(sic)` + `net_debt.net_debt` +
`anchor.lease_inclusive_net_debt` · `mechanical._edgar_shares_outstanding` + `resolver.ads_ratio`
· the event rule's own reads (`recent_filings(forms=EVENT_FORMS+EVENT_ANY_FORMS)` +
`client.events` 2.02), one year back · `PolygonEodClient.grouped_daily(2026-11-18)`. CIQ layer:
`CiqBundle.from_files` → `stated_currency`/`require_usd`, `require_filed_income_statement`,
`require_millions`, `own_history_bands`, `ev_ebitda_current`, `pe_ltm_current`, `net_debt`,
`ltm_ebitda`, `free_cash_flow`, `financial_summary_annual`, `forward_consensus`.

**What the anchor column means.** `compute_anchor` needs CIQ's own-history EV/EBITDA band FIRST;
without it the recipe is `unknown` for every name. So the column scores R1's EDGAR legs in the
order `compute_anchor` takes them: **W** = a positive median margin is computable (R1 would be
assigned once a CIQ band exists); **R** = `ANCHOR_UNRESOLVED` or `R2_NEEDED`; R3/R4 are
operator-tagged or machine-proposed from CIQ consensus, scored in the CIQ table.

**Score key:** **W** works · **R** refuses loudly (UNKNOWN with a stated reason, or a designed
refusal) · **X** produces something wrong · **N** not reachable · `·` layer not reached.

| name | archetype | identity | regime | companyfacts | fiscal yr | screen | shares | net debt | anchor | event rule | price |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SPGI | operating · data/ratings | W | W | W | W | W | W | W | W | W | W |
| FICO | operating · Sept FY, neg. equity | W | W | W | W | W | W | W | W | W | W |
| FDS | operating · Aug FY | W | W | W | W | W | W | W | W | W | W |
| VRSK | operating · data | W | W | W | W | W | W | W | W | W | W |
| MORN | asset mgr / data (SIC 6282) | W | W | W | W | W | W | W | W | W | W |
| LOW | operating · Jan FY, neg. equity | W | W | W | W | W | W | W | W | W | W |
| TTWO | operating · March FY | W | W | W | W | W | W | W | W | W | W |
| BRBR | operating · Sept FY (page control) | W | W | W | W | W | W | W | W | W | W |
| AWK | utility | W | W | W | W | W | W | W | W | W | W |
| FCX | reserve-based (mining) | W | W | W | W | W | W | W | W | W | W |
| EL | operating · 2 classes, June FY | W | W | W | W | W | R | W | W | W | W |
| HSY | operating · 2 classes | W | W | W | W | R | R | W | W | W | W |
| GILD | operating · biopharma | W | W | W | W | R | W | W | W | W | W |
| ISRG | operating · medtech, debt-free | W | W | W | W | R | W | R | W | W | W |
| ORCL | operating · May FY, capex/RPO heavy | W | W | W | W | R | W | R | W | W | W |
| LLY | operating · pharma (OI untagged) | W | W | W | W | R | W | W | R | W | W |
| PFE | operating · pharma (OI untagged) | W | W | W | W | R | W | W | R | W | W |
| CRWV | pre-profit · capex/lease heavy, IPO 2025 | W | W | W | W | R | R | R | R | W | W |
| RIVN | pre-profit | W | W | W | W | R | W | W | R | W | W |
| PCVX | pre-revenue biotech | W | W | W | W | R | W | R | R | W | W |
| VKTX | pre-revenue biotech | W | W | W | W | R | W | R | R | W | W |
| DVN | reserve-based (E&P) | W | W | W | W | R | W | W | R | W | W |
| XOM | successor registrant (2026) | W | R | W | R | R | W | W | R | W | W |
| MTB | bank | W | W | W | W | R | W | R | R | W | W |
| JPM | bank | W | W | W | W | R | W | R | R | W | W |
| AXP | lender (SIC 6199) | W | W | W | W | R | W | R | R | W | W |
| SYF | lender (SIC 6199) | W | W | W | W | R | W | R | R | W | W |
| CB | insurer | W | W | W | W | R | W | R | R | W | W |
| PGR | insurer | W | W | W | W | R | W | R | R | W | W |
| BRK-B | insurer-led conglomerate · 2 classes | W | W | W | W | R | R | R | R | W | W |
| UNH | managed care (SIC 6324) | W | W | W | W | W | W | R | W | W | W |
| CNC | managed care (SIC 6324) | W | W | W | W | R | W | R | W | W | W |
| AJG | insurance broker | W | W | W | W | R | W | W | R | W | W |
| GS | broker-dealer (SIC 6211) | W | W | W | W | R | W | R | R | W | W |
| SCHW | broker-dealer + bank (SIC 6211) | W | W | W | W | R | W | **X** | R | W | W |
| BLK | asset manager (SIC 6211) | W | W | W | W | R | W | W | W | W | W |
| CME | exchange (SIC 6200) | W | W | W | W | R | R | R | W | W | W |
| PLD | REIT (co-registrant OP) | W | W | W | W | R | R | W | W | W | W |
| INVH | REIT (SIC 6510) | W | W | W | W | R | W | W | **X** | W | W |
| O | REIT | W | W | W | W | R | W | R | R | W | W |
| VMRK | REIT · merged 2026 (ex-EQR) | W | W | W | W | R | W | R | R | W | W |
| NEE | utility (co-registrant) | W | W | W | W | R | R | W | W | W | W |
| EPD | MLP | W | W | W | W | R | W | W | W | W | W |
| MPLX | MLP | W | W | W | W | R | W | W | W | W | W |
| TPL | royalty | W | W | W | W | R | W | R | W | W | W |
| RGLD | royalty | W | W | W | W | R | W | W | W | W | W |
| NBIS | FPI 20-F US GAAP USD · transformed 2024 | W | W | W | W | R | W | W | **X** | W | W |
| ASML | FPI 20-F US GAAP EUR | W | W | R | W | R | W | R | R | W | W |
| BABA | FPI 20-F US GAAP CNY, ADS 8:1 | W | W | R | W | R | W | R | R | W | W |
| NVO | FPI 20-F IFRS (DKK) | W | W | R | W | R | R | R | R | W | W |
| TSM | FPI 20-F IFRS (TWD), ADS 5:1 | W | W | R | R | R | W | R | R | W | W |
| RY | bank · FPI 40-F IFRS CAD | W | W | R | W | R | W | R | R | W | W |
| FNV | royalty · FPI 40-F IFRS | W | W | R | W | R | W | R | R | W | W |
| BFC | bank · screen-band median cap | W | W | W | W | R | W | R | R | W | W |
| NMIH | insurer (6351) · screen-band median cap | W | W | W | W | R | W | R | R | W | W |
| PEB | REIT · screen-band median cap (D&A stale since 2019 → R1 value refused) | W | W | W | W | R | W | W | W | W | W |
| AQN | utility · 40-F US GAAP USD · screen-band median cap | W | W | W | W | W | W | W | W | W | W |
| SECZ | lender · no 10-K yet · screen-band median cap | W | R | W | R | R | W | R | R | W | W |
| DRD | FPI 20-F IFRS (ZAR), ADS 10:1 · screen-band median cap | W | W | R | R | R | W | R | R | W | W |
| CODGF | non-SEC (Saint-Gobain OTC line) | W | R | N | · | · | R | · | · | N | N |
| EssilorLuxottica | non-SEC | N | · | · | · | · | · | · | · | · | N (OTC `ESLOY` exists on Polygon, ADRC, not in grouped daily) |
| AVB / EQR / ABB | deregistered / renamed / lapsed | N | · | · | · | · | · | · | · | · | · |

**Evidence behind every X and every non-obvious R** (field → value → source; full per-name evidence
in `scores.md`, raw layer output per name in `probe/<T>.json`, both regenerated by `scripts/archetype_probe/`):

- **INVH anchor X** — `_total_revenue_series` → `RevenueFromContractWithCustomerExcludingAssessedTax`
  `{2015: 59,535,000}` (1 year; FY2016 disputed: "45M vs Revenues 923M (95% apart)");
  `Revenues` holds 10 years to FY2025 $2,729,296,000; `OperatingIncomeLoss` only FY2015–17 →
  `margin_anchor` `{2015: 1.921}`, median **1.9212**. D&A: "no D&A tag (combined or split)" → R1
  value refused; the 192% margin is what `AnchorMargin` would print. Cause: a REIT's rent is
  ASC 842 lease revenue, not ASC 606 — the 606 tag is the ancillary residue.
- **NBIS anchor X** — chosen `RevenueFromContractWithCustomerIncludingAssessedTax` `{2018: 1,837.6M,
  2019: 2,224.4M}` (3 disputed years dropped: "FY2020 … 273M vs Revenues 2,956M (91% apart)" …);
  `OperatingIncomeLoss` 2021–25 = −178.7M, −158.0M, −285.7M, −399.6M, −611.7M → margin
  `{2018: 0.163, 2019: 0.141}`, median **0.1521** → gate passes as R1 instead of `R2_NEEDED`.
- **SCHW net debt X** — `net_debt.not_applicable("6211")` → None; builder → `leverage_usd
  −12,850,000,000` at 2026-09-30.
- **CME net debt R** — "no debt/cash": its debt is `UnsecuredLongTermDebt` $3,425.1M (2026-09-30),
  not a core debt tag; cash $2,198.5M is tagged. **ORCL** — "EDGAR debt under-captured:
  NotesPayableCurrent $7,625M is more than the $0M of long-term debt read" (its long debt is
  `LongTermNotesAndLoans` $117,712M). **O** and **VMRK** — `NotesPayable` $26,452M / $6,002M
  under-captured. **ISRG**, **TPL**, **PCVX**, **VKTX** — no debt at all → "no debt/cash"
  (a debt-free company's net debt = −cash is refused, not computed).
- **Share count R** — `_edgar_shares_outstanding` → None: EL has no `dei` or `us-gaap` count;
  HSY's `dei` count ends 2014-02-07 (two classes); BRK's ends 2011-04-29; **NEE's and PLD's end at
  their Q1-2026 10-Q** (2026-03-31 / 2026-04-28), though both filed Q2 and Q3 10-Qs since. Both
  file combined reports with a subsidiary registrant (NEE with FPL, PLD with Prologis LP), so a
  dimensioned cover count is the likely cause — **a hypothesis, not verified here** (the instance
  was not read; nothing in `vinci/` matches `LegalEntityAxis` or co-registrant). CRWV reports a
  period average only.
- **Screen R** is common even on the proven path: `op_income_sign` "no operating_income" (LLY,
  PFE, JPM, CB, PGR, AJG, SCHW, MTB, O); `fcf_sign` "no OCF/capex" (LLY, CB, NEE, RGLD, PLD);
  `eps_diluted_annual` "no diluted EPS" (HSY, MPLX) or stale since 2011 (EPD).
- **XOM** — resolves to CIK 0002115436 "ExxonMobil Holdings Corp": 2 10-Qs, no 10-K, 98 us-gaap
  concepts → `filer_fiscal_year` None, every leg UNKNOWN; net debt reads the successor's 10-Q
  balance sheet ($22.10bn).
- **Event rule** — FPIs: NVO 61 6-Ks/365d (median gap 6d), TSM 45 (7d), BABA 40 (7d), FNV 24
  (12d), NBIS 22 (8.5d), RY 17 (14d), ASML 7 (28d). US 10-K filers: 8–11 events, median gap
  0–42d (an 8-K 2.02 and its 10-Q are often days apart), max gap 70–110d. CODGF: no filings → the
  rule has nothing to read (and the page carries no CIK path → refusal).

**CIQ layer** (the repo's readers on the exports that exist on Drive):

| name (export) | require_usd | filed IS | millions | EV/EBITDA own-history band | current multiples | consensus (NTM) | verdict |
|---|---|---|---|---|---|---|---|
| LLY (live) | pass | pass | pass | present, 39 closes to 2026-11-02 | present (EV/EBITDA, P/E) | present (TEV/EBIT, P/E) | **W** |
| BRBR (live) | pass | pass | pass | present, 28 closes to 2026-11-18 | present | present | **W** |
| MTB (bank, pack 10-28) | pass | **CiqPreliminaryError** (6 Press Release columns) | pass | **only P/LTM EPS** band (22 closes); no EV/EBITDA | EV/EBITDA "no TEV/LTM EBITDA Close carries a date"; P/E present | **empty** | **R** — no EBITDA, no LFCF row, no forward multiples |
| PLD (REIT, pack 10-28) | pass | **CiqPreliminaryError** | pass | present, 22 closes | present | present | **W after a post-10-Q re-pull** (the refusal is export timing); method gap: no FFO |
| NVO (FPI IFRS, pack 10-28) | **CiqCurrencyError** — 16 panels DKK | pass | pass | present (but in DKK terms) | present | present | **R** (FPI5) |
| PCVX (pre-revenue, pack 10-28) | pass | pass | pass | **none** ("no multiple has ≥4 quarterly closes") | NM | all NTM null | **R** (R2 territory) |
| RIVN (pre-profit, pack 10-28) | pass | pass | pass | **none** | NM | only TEV/REV | **R** (R2 territory; TEV/REV is the only live multiple) |

The dated packs are 2026-10-28 exports in a separate folder no code reads; they were the only
bank, REIT, IFRS and pre-profit exports on Drive. **No CIQ export exists on Drive for 20 of the
operator's 22 names** (only LLY and BRBR).

---

## 6. Readiness grid

Rows are the §3a archetypes; weight = share of the screen band / large-cap band by count. Cells
take the **probed names' scores** (§5): **W** works · **R** refuses loudly · **X** produces
something wrong · **N** not reachable; "W/R" means the archetype's probed names split, with the
names after the slash. "Recipe" is what the page could be underwritten on today.

**Updated by 5a (§11) in place:** a cell 5a changed shows the old reading struck (~~like this~~)
with the new one beside it, marked **5a:**. The last column is new: the full $0 build of §11
(`prespend`'s own command, main `9d036cbb`, 2026-11-19). "not shown: no export" = the cell needs
a CIQ export none of that archetype's 5a names has on Drive.

**Updated again by the fresh exports (§11f, main `6e03501f`, packs exported 2026-11-19):** the
cells for G03 (RIVN), G05 (DVN), G11 (MORN), G13 (PLD), G14 (AWK) and G17 (AQN) strike the
"not shown: no export" or stale-pack reading and add the new one beside it, marked **fresh:**.

| archetype (probed names) | weight screen / large-cap | identity | regime + event rule | EDGAR facts | fiscal yr | screen legs | shares | net debt | R1 EDGAR legs | CIQ | price | recipe today | full $0 build (5a) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G01 proven path (SPGI FICO FDS VRSK LOW TTWO BRBR EL HSY GILD ISRG ORCL) | 38.4% / 46.9% | W | W | W | W | W (R: HSY, GILD, ISRG, ORCL partial) | W/R (EL, HSY) | W/R (ISRG debt-free, ORCL tag) | W | W (LLY, BRBR) | W | R1 / R3 / R4 | SPGI, the CONTROL, built EDGAR-only: precheck STOP, the same two post-spend refusals every EDGAR-only name gets (no CIQ Financials; no market cap) and the same anchor stop (no own-history band) — so those are export effects, not archetype effects |
| G02 OI untagged (LLY PFE) | 2.9% / 6.5% | W | W | W | W | R | W | W | R → CIQ `financial_summary` fallback (LLY's page) | W | W | R1 on a weak CIQ margin | not built |
| G03 pre-profit (RIVN CRWV) | 13.1% / 4.0% | W | W | W | W | R | W/R (CRWV) — **5a:** CRWV R confirmed in the full build (no usable share count) | W/R (CRWV) — **5a:** CRWV's debt left the tags read (`LongTermDebt` $24,859M at 2026-03-31, none on the 2026-09-30 sheet; D4 class) | ~~R (`R2_NEEDED`)~~ **5a:** R, and the page reads `unknown`, not `R2_NEEDED` (D12) | ~~R (no band; TEV/REV only)~~ ~~**5a:** R — RIVN's pack refused before any model call (a material LTM row CIQ disagrees with itself on, 19.96%); no band, TEV/REV only~~ **fresh:** R again — the same row and the same disagreement (cells cited in D18), on a pack exported 22 days later: CIQ's own FY2025 cell, not timing, and the filed 10-Qs side with the quarterly export (D18). No re-export clears it. Pack inputs: TEV/REV only, no band | W | ~~**none** (R2 unbuilt)~~ **5a:** **none** — R2 unbuilt, AND the anchor never routes a name with no EV/EBITDA band to `R2_NEEDED` (D12), so R2's dispatch would not reach it | RIVN pack: refused pre-spend · RIVN EDGAR-only, CRWV: STOP at $0 (export-driven) · **fresh RIVN pack: refused pre-spend again (D18)** |
| G04 pre-revenue (PCVX VKTX) | 5.4% / 0.6% | W | W — **5a:** PCVX's event rule fires correctly (8-K item 2.02 of 2026-11-04 after its 2026-10-27 panel) | W | W | R | W | ~~R (debt-free)~~ **5a:** W on the page via CIQ's balance sheet (−$1,371.4M, `vendor_bridge`); the EDGAR refusal stands under it | R | R (all NM) | W | **none** | PCVX pack: the page BUILDS, every pre-spend check passes, both calls read; ONE post-spend refusal, freshness (timing) — a re-export clears it and the paid build then writes a page priced on nothing |
| G05 reserve-based (FCX DVN) | 2.2% / 1.8% | W | W | W | W | W/R (DVN) | W | W | W/R (DVN OI stale) — **5a:** confirmed; net debt/EBITDA UNKNOWN (newest year OI and D&A share is 2016) | ~~— **5a:** not shown: no export~~ **fresh:** R — the pack's `…Financials_Quarterly.xls` is byte-identical to its Annual (sha256 `78cd82c3d2…` both), so the loader refuses it (`CiqMislabelledError`) before any model call. ~~**Re-export (17:19Z):** R again, the same refusal. The new file (`b548221592`) differs from the Annual's bytes but is an annual export again ("Period Type: Annual", 12-month columns), so a Period-Type-Quarterly export is still owed.~~ **2026-11-20 re-export (`a532e1a269`, "Period Type: Quarterly"): W** — the precheck passes with 0 refusals; own-history EV/EBITDA band of 33 quarterly closes; bridge built. R1 applies but its value is withheld (W73): the band's newest close is the 2026-09-30 quarter-end, before DVN's 8-K item 2.02 of 2026-11-05. A probe variant without that file builds: 36 forward multiples, a positive NTM TEV/EBIT, FY P/E on normalized EPS, but no band and no bridge (both need the quarterly) | W | R1 (no PV-10 leg) — **fresh:** none on the variant's page (anchor `unknown`; all three templates refused) | DVN EDGAR-only: STOP at $0 (export-driven); 5 gaps vs the control · **fresh DVN pack: refused pre-spend (mislabelled quarterly; a precheck traceback, D11); the 17:19Z re-export refused the same way (annual again)** · variant without it: precheck PASS, nothing priceable (D19) |
| G06 bank (MTB JPM BFC) | 7.8% / 2.9% | W | W | W | W | R | W | R (SIC rule) — **5a:** the anchor block still computes $3,883M EDGAR net debt beside the refusal (JSON only, marked ineligible; D14) | R | R (P/E band only, no EBITDA, no forward multiples) — **5a:** confirmed (0 forward multiples; P/LTM EPS band, 22 closes); the pack itself is refused before any model call (Q3 press-release columns; timing) | W | **none** | MTB pack: refused pre-spend · MTB EDGAR-only: STOP at $0 (export-driven) · intake: nothing refuses a bank (§11c) |
| G07 lender (AXP SYF SECZ) | 2.5% / 1.1% | W | W/R (SECZ no 10-K) | W | W | R | W | R (SIC rule) | R | — | W | **none** | not built |
| G08 insurer (CB PGR NMIH BRK) | 2.2% / 2.9% | W | W | W | W | R | W/R (BRK) — **5a:** BRK R confirmed (no share count, no diluted WA tag) | R (SIC rule) — **5a:** BRK's anchor: "no debt/cash tag" | R | — | W | **none** | BRK-B EDGAR-only: STOP at $0, freshness also for no share count · intake: nothing refuses it (§11c) |
| G09 managed care (UNH CNC) | 0.2% / 0.6% | W | W | W | W | W/R | W | R (SIC rule — design question) | W | — | W | R1 / R3 | not built |
| G10 broker-dealer (GS SCHW; BLK) | 0.4% / 1.1% | W | W | W | W | R | W | R (GS) / **X (SCHW)** / W (BLK) | R / W (BLK) | — | W | none / R1 (BLK) | not built |
| G11 asset mgr / exchange (CME MORN) | 1.1% / 1.7% | W | W | W | W | W/R | W/R (CME) | W/R (CME tag) | W | ~~— **5a:** not shown: no export~~ **fresh:** W — the pack builds with no Credit Health Panel and no transcripts, both absent at the source (CIQ carries neither for MORN, per the operator; MORN's own site has typed transcripts the pipeline does not read); ex-lease EV/EBITDA band, 35 closes (rent material, ≥5% of EBITDA); 24 forward multiples, a positive NTM TEV/EBIT; bridge built. No credit-health score at all (its comps workbook lacks the sheet too) | W | R1 / R3 — **fresh:** R1 priced at $0 (firm; base value *[CIQ value withheld]*); R3 and R4 templates both emit; no machine R4 (1 of 3 conditions) | MORN EDGAR-only: STOP at $0 (export-driven); 1 gap vs the control (buyback share count) — the closest to the proven path of any 5a name · **fresh MORN pack: precheck PASS, 0 refusals** |
| G12 insurance broker (AJG) | 0.4% / 0.8% | W | W | W | W | R | W | W | R (OI untagged) | — | W | R1 on a CIQ margin | not built |
| G13 REIT + G13b (PLD O VMRK PEB INVH) | 5.5% / 4.3% | W | W | W | W | R — **5a:** PLD's FCF is UNKNOWN ("no OCF/capex": development spend is not under the capex tags read) | W/R (PLD) — **5a:** PLD R confirmed in the full build, and it also fires freshness ("missing shares outstanding") — **fresh:** W on the page, via CIQ's comps share count; the EDGAR cover count is still absent (D6) | W/R (O, VMRK tag) | W (PLD, PEB) / R (O, VMRK) / **X (INVH)** | ~~W (PLD band; no FFO)~~ **5a:** R in the full build — PLD's 2026-10-28 pack is refused before any model call (Q3 press-release columns; its 10-Q filed that same day; timing). The pack's band reads (EV/EBITDA, 22 closes), a positive NTM TEV/EBIT, FY P/E on GAAP EPS — **fresh:** W, the pack builds; band 39 closes, but R1 declines: no 'Net Rental Exp.' row, so rent is unmeasurable and treated as material, and the ex-lease band has no current ('Curr. Port. of Leases' reads '-' at 2026-09-30). No bridge (D17) | W | R1 without FFO — a method gap — **5a:** and R3 on this pack would price a GAAP P/E, the same gap — **fresh:** **none** on the page: R1 declines, R3 refused on row 10, R4 has no bridge (D17). The precheck still passes, so a paid build would write it (as PCVX would) | PLD pack: refused pre-spend · PLD EDGAR-only: STOP at $0; 7 gaps vs the control · **fresh PLD pack: precheck PASS, 0 refusals, nothing priceable** |
| G14 utility (AWK NEE AQN) | 1.4% / 3.8% | W | W | W | W | W/R | W/R (NEE) | W | W | ~~— **5a:** not shown: no export~~ **fresh:** W — the pack builds; EV/EBITDA band 39 closes; rent immaterial (<5% of EBITDA), so CIQ's history is kept; 36 forward multiples, a positive NTM TEV/EBIT; no bridge (D17) | W | R1 / R3 (no rate-base method) — **fresh:** R1 priced at $0 (firm; base value *[CIQ value withheld]*); R3 template emits; R4 refused (no bridge, D17); no machine R4 (1 of 3 conditions) | AWK EDGAR-only: STOP at $0 (export-driven); 2 gaps vs the control (stale buyback cash, impairment headroom) · **fresh AWK pack: precheck PASS, 0 refusals** |
| G15 MLP (EPD MPLX) | 0.7% / 0.8% | W | W | W | W | ~~R (per-unit EPS)~~ **5a:** R, and EPD's P/E note states a FALSE cause (D13) | W | W | W (D&A gaps) — **5a:** EPD's newest common OI + D&A year is 2020 → net debt/EBITDA UNKNOWN (D7) | — | W | R1 | EPD EDGAR-only: STOP at $0 (export-driven) · intake: nothing refuses an MLP (§11c) |
| G16 royalty (TPL RGLD) | 0.3% / 0.2% | W | W | W | W | R | W | W/R (TPL debt-free) | W | — | W | R1 | not built |
| G17 FPI US GAAP USD (NBIS AQN) | 3.1% / 1.2% | W | W (6-K over-refusal) | W | W | R/W | W — **5a:** NBIS's anchor has no diluted count (it reads a 10-Q quarter; a 20-F filer has none; D16) | W | ~~**X (NBIS)** / W (AQN)~~ **5a:** D2 does not reach an EDGAR-only page (the anchor stops at the band gate before the margin); with an export it reaches a page only if NBIS's export has an EV/EBITDA band — unknown, no export | ~~— **5a:** not shown: no export~~ **fresh (AQN):** R — the pack was exported from the TSX listing. Its quarterly Historical Capitalization states CAD (the sheet's own "trading currency"), while the other 17 money panels state USD, so `CiqCurrencyError` fires before any model call. Pack inputs: EV/EBITDA band 35 closes, a positive NTM TEV/EBIT, an NTM P/E. ~~Likely fix: an export from the NYSE:AQN listing (unverified).~~ **Refused: home-market primary listing (CAD capitalisation panel); no US listing in CIQ, per the operator** (D21). Substitute G17 test name: DAC (11f addendum 3). **DAC (2026-11-20 pack): W** — NYSE:DAC, every money panel USD, the precheck passes with 0 refusals; bridge built; diluted count read (quarterly XBRL on 6-K, so D16 does not bite); R1 declines on unmeasured rent (D22). NBIS: still no export | W | R1, with D2 risk | **fresh AQN pack: refused pre-spend (one CAD panel; a precheck traceback, D11)** · AQN, NBIS EDGAR-only: STOP at $0 (export-driven); AQN covenant pointers UNKNOWN (no agreement exhibit, 40-F), NBIS non-operating share UNKNOWN (no quarterly XBRL), so R4's condition 3 cannot be decided for a 20-F filer |
| G18 FPI US GAAP non-USD (ASML BABA) | 1.2% / 2.6% | W | W (6-K over-refusal) | R (FPI1a) | W | R | W (ADS 8:1 read) | R | R | R by analogy to NVO (non-USD workbook refused) — not run | W | **none** | not built (stage 2 / wait) |
| G19 FPI IFRS (NVO TSM RY FNV DRD) | 8.0% / 15.2% | W | W (6-K over-refusal) | R (no IFRS reader) | R/W (TSM, DRD stale) | R | W/R | R | R | R (NVO: DKK refused) | W | **none** | not built (stage 2 / wait) |
| G20 no annual on file (XOM SECZ) | 2.2% / 0.8% | W | R | W | R | R | W | W | R | — | W | **none** until a 10-K, or stitching | not built (wait) |
| stage 2 non-SEC (Saint-Gobain, EssilorLuxottica) | not in the universes | N / W (CODGF CIK) | N | N | N | N | N | N | N | not on Drive | N (OTC ADR not in grouped daily) | **none** | not built (stage 2 / wait) |

`—` = no CIQ export on Drive for any probed name of that archetype.

**The archetypes with no recipe a page could be underwritten on today** are G03, G04, G06, G07,
G08, G10, G18, G19 and G20. Together they are **885 of the screen band's 2,065 (42.9%)** and **289 of
the large-cap band's 928 (31.1%)**. G10 is counted whole even though BLK-type asset managers inside
it do reach R1. The rest (G01, G02, G05, G09, G11–G17) reach R1, R3 or R4 mechanically, but the
REIT, utility and MLP rows do so on a basis that is not how those businesses are valued, and that
needs the operator's acceptance or a recipe.

---

## 7. Options per archetype, for the operator's coverage decision

"Rough cost" is in build PRs of this repo's usual size (one code PR, its tests, a $0 refresh, a
record), plus the operator rulings each needs. It is an estimate from the code read, not a
measurement; **VERIFY-AT-BUILD**. "Out of scope" always means **refused loudly at intake** —
`coverage_roster`/`followed` already refuse a name before any model call, so declaring an
archetype out of scope is one guard keyed on the archetype's signal (≈1 PR), plus, if wanted, a
screen-side exclusion (a decision-path change: real old-vs-new screen run, operator approval).

| archetype | first-class support — what to build | rough cost | out of scope (refused loudly) | data-source build | dependencies |
|---|---|---|---|---|---|
| **A1/B14/C4 proven path** | close the cross-cutting gaps: D4 debt tags, D5 debt-free ruling, D6 share classes / co-registrants, D7 OI-untagged derivation | 4–6 PRs | — | — | D5 needs a ruling |
| **A3 FPI US GAAP USD** | D8 (6-K results classification), D2 guard (transformed history) | 2 PRs | 1 guard | — | ruling on what a "results" 6-K is |
| **A4 FPI US GAAP non-USD** | FPI1b (FX conversion: rate source, date rule, USD convenience translation) + its consumers | 3–5 PRs | 1 guard | an FX series — no FX reader exists in `vinci/` (not found under `C:EUR`, `forex`, `/fx/`); Polygon's FX endpoint is a candidate (a 2026-10-09 session note says it is served and not window-limited — VERIFY-AT-BUILD) | **operator FX ruling** (STATE row 4 says FPI1b waits on it) |
| **A5 FPI IFRS** | FPI1c (read the 20-F/40-F instance for the newest year), IFRS readers for revenue / `ProfitLossFromOperatingActivities` / D&A / debt / cash / shares (today `IFRS_FLOW_TAGS` only date the year), then FPI1b, then FPI5 (foreign-currency CIQ workbooks) | 6–10 PRs | 1 guard | — | FPI1b ruling; FPI5 |
| **A6 non-SEC** | not a code change: a fundamentals source per market (candidates to evaluate, none verified here: ESEF iXBRL annual reports for EU issuers; EDINET for Japan; exchange filings for HK/India), a local-exchange price source (Polygon carries only US lines; OTC unsponsored ADRs like `ESLOY`/`CODYY` exist but are not in the grouped daily), an event calendar for the freshness rule, and identity without a CIK (every reader keys on CIK today) | large: a new layer per source | 1 guard (today they already fail at identity) | **yes — this is the whole archetype** | licence + cost per source; an identity scheme beyond CIK |
| **A7 successor registrant** | D9 stitching | 1–2 PRs | — | — | a ruling on the cut at the succession date |
| **B1 bank / B2 lender / B6 broker-dealer with a bank book** | a new recipe (P/TBV against ROTCE; or P/E on normalised EPS with a credit-cost leg), bank tags (`Deposits`, net interest income, provision, `LoansAndLeasesReceivableNetReportedAmount`), a CIQ bank template (MTB's exports carry a P/LTM EPS band only, no EBITDA, no forward multiples), screen legs that do not read EV/EBITDA; D3 for SCHW | 6–10 PRs + face-validity rulings on the recipe | 1 guard (the screen already admits them; net debt and the anchor already refuse) | regulatory capital (CET1) is not in XBRL — FR Y-9C (FFIEC) would be a source | recipe rulings |
| **B3 insurer** | P/B against ROE, combined ratio / reserve development (`PremiumsEarnedNet`, `PolicyholderBenefitsAndClaimsIncurredNet` are tagged; not read anywhere — `git log -S PremiumsEarnedNet` finds nothing) | 5–8 PRs + rulings | 1 guard | statutory filings (NAIC) for reserve detail | recipe rulings |
| **B4 managed care** | a ruling: exempt SIC 6324 from the net-debt rule (UNH, CNC carry real debt and are valued on earnings) | 1 PR | — | — | the ruling |
| **B13 BRK / conglomerates** | sum-of-the-parts and a class-A/B equivalence; BRK refuses on every money layer today | large, judgment-heavy | **recommend: out of scope, or hand-built pages** | — | — |
| **B8 REIT** | stop D1 now (refuse R1 for a lease-revenue filer, 1 PR); then a REIT basis: lease revenue aliases, FFO/AFFO (NAREIT FFO is non-GAAP, not in us-gaap XBRL — from 8-K supplementals, or CIQ's REIT lines, unverified on the PLD pack), a P/FFO or EV/EBITDAre recipe; NAV/cap rate stays human | 1 PR now + 4–6 PRs | 1 guard | — | recipe ruling |
| **B10 utility** | R1 works mechanically; a rate-base/allowed-ROE method is a judgment; D6 for co-registrants (NEE) | 1–2 PRs (D6) | — | rate cases: state PUC filings (out of scope) | — |
| **B11 MLP** | per-unit EPS aliases (`…PerOutstandingLimitedPartnershipUnit…` — not found in `vinci/` under `LimitedPartnershipUnit`), unit counts; a distribution-coverage metric | 2 PRs | 1 guard | — | a ruling on K-1 names for the fund (tax, not code) |
| **B12 royalty / B5 broker / B7 asset manager / exchange** | ride the proven path; D4/D5/D7 cover their gaps | (in A1's PRs) | — | — | — |
| **C1 pre-revenue biotech** | an rNPV or cash-runway recipe needs pipeline data XBRL does not carry | large, judgment-heavy | **recommend: out of scope** (CIQ multiples are NM, the anchor already refuses) | clinical-trial registries | — |
| **C2 pre-profit growth** | finish R2 (STATE row 10: `R2_NEEDED` ≠ `terminal_margin.RECIPE_R2`, `scenario-create` never carries `survival_input`) | 3–5 PRs | 1 guard | — | R2 design rulings already partly made (recipe 3b) |
| **C3 reserve-based** | E&P `OperatingIncomeLoss` stops (DVN) → D7; a PV-10 leg (`StandardizedMeasureOfDiscountedFutureNetCashFlowsRelatingToProvedOilAndGasReserves` is a us-gaap tag — not found in `vinci/` under `StandardizedMeasure` / `ProvedDevelopedAndUndevelopedReserves` / `PV-10`, nor by `git log -S StandardizedMeasure`) | 2–3 PRs | — | — | — |

---

## 8. Scope questions the counts raise

Each is the operator's to decide; the count behind it is in §3 or §4.

1. **Banks, lenders, insurers and broker-dealers at stage 1?** G06, G07, G08 and G10 are 267 of
   the screen band (12.9%) and 74 of the large-cap band (8.0%), and the screen already admits
   them. Today every one refuses at
   net debt and the anchor (MTB, JPM, BFC, AXP, SYF, CB, PGR, NMIH, GS). The options are (a) out of
   scope, refused at intake, ~1 PR; or (b) a financials recipe, ~6–10 PRs plus recipe rulings. If
   (a), should the screen also stop surfacing them? That is a decision-path change and needs an
   old-vs-new run.
2. **REITs (5.5% / 4.3%): stop D1 now?** The REIT basis (FFO/AFFO) is a later choice. Stopping D1
   touches R1's anchor, which is a decision path, so it needs a ruling even though it only
   refuses. **INVH, the operator's own name, is the case.**
3. **Pre-profit and pre-revenue (18.5% / 4.6%):** finish R2 before onboarding them? CRWV (named)
   and NBIS route there or should. Should pre-revenue biotech be declared out of scope?
4. **SEC-filing foreign issuers (12.3% / 19.0%):** STATE row 4 already keeps them in scope ("foreign
   filers STAY") with an FPI build order. Three rulings gate the next steps:
   - the **FX ruling for FPI1b**, which every IFRS and non-USD name waits on;
   - **what a "results" 6-K is (D8)**: today 81% of the screen band's FPIs would have a CIQ export
     outdated within a month;
   - **whether a transformed business's history is refused (D2, NBIS)**.
5. **Managed care (UNH, CNC):** keep refusing net debt under the SIC 63 rule, or exempt SIC 6324?
6. **Stage 2, which markets count as "top 5"?** WFE/SIFMA end-2025: US, China, India, Japan, Hong
   Kong; the UK is 6th; the EU as a bloc sits between China and India. Is the EU one market, and is
   Hong Kong separate from China?
7. **Stage 2, which comes first?** By SEC reachability the UK (10 of 10) and Canada (6 of 6) lead,
   then the EU (11 of 27). Japan, India and China/HK reach at most about half. Almost every
   reachable European, UK, Japanese and Indian name is IFRS (35 of the 51 reporters), so **the IFRS
   build (FPI1c, IFRS readers, FPI1b, FPI5) is the stage-2 entry ticket for the SEC-reachable
   half**. The other half, the operator's two named European names included, needs a data-source
   decision.
8. **Non-SEC names (EssilorLuxottica, Saint-Gobain): which source?** The options are:
   - CIQ-only pages (the licence covers CIQ-derived facts, but CIQ is not point-in-time and the
     page loses its EDGAR cross-checks);
   - a filings source per market (e.g. ESEF iXBRL for EU issuers; not evaluated here);
   - out of scope until a source is chosen.
   Every reader keys on a CIK today, so any of these also needs an identity scheme.
9. **Named names that changed identity:**
   - **AVB** has deregistered, apparently into EQR, which now trades as Vivmark Residential
     (VMRK). Follow VMRK instead?
   - **XOM** has a successor CIK with no 10-K yet. Build D9 stitching if it is ever followed?
10. **BRK:** declare it out of scope, or allow a hand-built page? It refuses on every money layer
    and carries an A/B share-class equivalence.

**Which of the operator's named names a page could be built for today** (with a CIQ export, on
code at `8bc138cd`):

- **Ready on the proven path:** SPGI, FICO, FDS, VRSK, MORN, LOW, TTWO; LLY and BRBR already have
  pages.
- **Ready but leaning on CIQ to fill an EDGAR gap:** HSY and EL (share count), GILD and ISRG (D&A;
  ISRG's net debt), ORCL (net debt, D&A), PFE (operating margin). The anchor's vendor bridge fills
  these and flags `vendor_bridge`.
- **Not ready:**
  - CRWV — R2 is not built;
  - NBIS — the D2 margin and the 6-K cadence;
  - INVH — D1;
  - BRK — refuses on every money layer;
  - AVB — deregistered;
  - EssilorLuxottica and Saint-Gobain — no data source.

**No CIQ export exists on Drive yet for 18 of the 20 named SEC filers** (only LLY and BRBR).

---

## 9. Defects found in passing — reported, not fixed (hold scope)

Each is a deterministic, reproducible observation on `main` `8bc138cd` with the evidence above.
None was fixed; each would need its own PR with a failing test first.

| # | defect | class | names seen | where in code | smallest fix to consider |
|---|---|---|---|---|---|
| D1 | REIT revenue: the ASC 606 tag is a component; lease revenue (`OperatingLeasesIncomeStatementLeaseRevenue`) is not an alias → a 1-year component is chosen as total revenue → 192% margin printed | **X** | INVH; O and VMRK refuse ("no reliable revenue") for a sibling reason | `anchor._total_revenue_series` / `concepts.CONCEPT_ALIASES['revenue']` | refuse R1 for a lease-revenue filer until a REIT basis exists; or add the lease tags with a disputes test |
| D2 | a business transformation passes the margin gate on the predecessor's years | **X** | NBIS (Yandex → Nebius, 2024) | `midcycle.annual_series` keeps the longest undisputed alias, which here is the oldest | a `revenue_tag_conflict` covering the recent years refuses instead of capping weak; or the margin window ends at the newest disputed year |
| D3 | SIC 6211 holding companies with a bank book get a net debt | **X** | SCHW (−$12.85bn) | `net_debt._NOT_APPLICABLE_SIC_GROUPS = {60, 61, 63}` | add a tag test (a `Deposits` line beside 6211); the module's own comment says it chose SIC over `Deposits` because four non-financials tag `Deposits` — so the combination, not either alone |
| D4 | debt carried in tags the builder does not read → net debt refused | R | CME `UnsecuredLongTermDebt`; ORCL `LongTermNotesAndLoans`; O, VMRK `NotesPayable` | `net_debt._CORE_DEBT_TAGS` | widen the core tags, each measured on the corpus (the witness already catches the under-capture, so this is coverage, not safety) |
| D5 | a debt-free company's net debt is refused, not −cash | R | ISRG, TPL, PCVX, VKTX | `NetDebt.refusal` → `NO_DEBT_OR_CASH` | an operator ruling first: is "no debt tag and no debt witness" evidence of no debt? |
| D6 | no current cover share count for multi-class and (apparently) combined-registrant filers | R | EL, HSY, BRK; NEE, PLD (counts stop at the Q1-2026 10-Q) | `mechanical._edgar_shares_outstanding` reads undimensioned facts only | read per-class / per-registrant counts from the filing's instance, as MC2 reads segments |
| D7 | `OperatingIncomeLoss` untagged on a material share of filers (count in §3) → R1's margin needs CIQ's `financial_summary` (weak) | R | LLY, PFE, AJG, CB, PGR, JPM, MTB, SCHW, O; DVN stale since FY2016 | `CONCEPT_ALIASES['operating_income'] = ["OperatingIncomeLoss"]` | a stated derivation (e.g. revenue − `CostsAndExpenses`) with a basis label, or accept the CIQ fallback as designed |
| D8 | every 6-K outdates a CIQ export, so an FPI's export lives a week | R (over-refusal) | NVO 6d, TSM 7d, BABA 7d, NBIS 8.5d, FNV 12d | `freshness.EVENT_ANY_FORMS = ("6-K",)` (round 1 of #1132, deliberate) | read the 6-K's exhibit index for an earnings release, refusing only on those; an operator ruling on what "results" means for a 6-K |
| D9 | a successor registrant (holding-company reorganisation) starts with no history | R | XOM (CIK 0002115436, no 10-K yet) | fundamentals read one CIK; `predecessor_cik` is used only by `resolver/aliases.py` for prices | stitch predecessor companyfacts across an 8-K12B succession, cut at the succession date |
| D10 | the IFRS fiscal year can be a year stale in companyfacts | R | TSM (newest read FY2024; FY2025 20-F filed 2026-04-16) | known (FPI1c, STATE row 4) | FPI1c — read the instance |
| D11 *(5a)* | `vinci dossier precheck` ends in a TRACEBACK, not its own "the $0 build was REFUSED" line, on a CIQ loader refusal. Exit is still non-zero and nothing is spent, so it stays loud | R (form of the refusal) | PLD, MTB (2026-10-28 packs, `CiqPreliminaryError`); ~~by the same catch list NVO's `CiqCurrencyError` (a `ValueError`) — not run~~ **fresh packs (2026-11-19), observed:** DVN (`CiqMislabelledError`, its quarterly file is its annual) and AQN (`CiqCurrencyError`, one CAD panel). Both are raised before any model call in the paid path too (`page_inputs.load_bundle` / `assemble_mechanical`), so nothing is spent | `prespend.run` catches `DossierAssemblyError`, `SecRateLimitedError`, `LookupError`; `CiqPreliminaryError` → `CiqAmbiguousError` → `RuntimeError` | catch the CIQ loader's refusal classes beside them, so an artifact pass reads one verdict line |
| D12 *(5a)* | a loss-maker whose CIQ EV/EBITDA is NM gets `recipe_hint: unknown` ("own-history multiple missing"), never `R2_NEEDED`: `compute_anchor`'s band gate runs before the margin gate that routes to R2 | R (routing; fails closed) | committed on main `9d036cbb`: FUBO, ORKA, TECX; 5a: PCVX. NCNO reaches `R2_NEEDED` only because it has a positive band | `anchor.compute_anchor` gate order | part of the R2 build (stage-1 G03): route on the margin when the band is absent for NM reasons, so R2's dispatch can see the name |
| D13 *(5a)* | the P/E's refusal note states a FALSE cause: "a more recent annual figure exists and is negative". The branch fires whenever an older positive annual EPS exists and the current one is out of range; EPD has no later figure at all — `EarningsPerShareDiluted` stops at FY2011 (+2.38), and EPD reports per LP unit (`NetIncomeLossNetOfTaxPerOutstandingLimitedPartnershipUnitDiluted` +2.66 FY2025) | **X** (a false statement in a note; the value is correctly UNKNOWN) — **latent on the live corpus (§11e)** | EPD (JSON `mechanical.valuation.pe.note`; not on its rendered page; a 5a SCRATCH page, not a live one). ~~The same text is on 5 committed pages and in 109 committed candidate records — their truth is NOT audited here~~ **Audited (§11e, main `2ecf6da0`):** the claim is TRUE on all 5 live pages and 107 of 109 candidate records, and FALSE on none. Two records are OTHER: **ORC**, where a newer negative exists but its newest annual EPS, FY2025 basic, is +1.24; and **LPL**, where the newer negatives sit only under IFRS tags the reader does not serve. The mechanism stands: nothing checks for the newer figure, it is luck of the corpus. EPD-type tag changes (MLPs), diluted→basic changes (ORC) and US GAAP→IFRS changes (LPL) are the classes that would print it falsely | `screens/assemble.py:449-453` (`G3_EPS_TOO_OLD`) | split the branch: "a later year exists and is negative" vs "the tag stops at <year>"; pin on EPD's real companyfacts |
| D14 *(5a)* | the anchor block computes an EDGAR net debt for a bank/lender/insurer that `leverage_survival` refuses on the same page | observation (contained: JSON only, `scenario_eligibility` false, not rendered) | MTB $3,883M (debt 20,021 − cash 16,138) | `anchor.py` never calls `net_debt.not_applicable` (its only callers: `mechanical.py:2445`, `screens/assemble.py:731`) | the out-of-scope guard (step 6) makes it moot for G06–G08/G10; otherwise apply the SIC rule in the bridge too |
| D15 *(5a)* | RUNBOOKS §i step 1's follow-entry example has `reason` + `sleeve` only; `vinci.followed` refuses an entry without `followed_since` (`FollowedListError`) | doc | every new follow | `docs/RUNBOOKS.md` §i step 1 (no `followed_since` anywhere in the file) | add the field to the example |
| D16 *(5a)* | the anchor's diluted share count reads a 10-Q quarter only, so a 20-F filer never has one | R | NBIS ("tagged only over spans longer than a quarter … no 10-Q quarter is on file") | `anchor.py` diluted-WA reader | an FPI branch: the annual 20-F diluted WA, labelled as annual (part of the FPI build) |
| D17 *(5a fresh)* | the EV bridge reads only CIQ's subtotal row 'Total Cash & ST Investments', and CIQ's REIT and utility balance-sheet templates carry no such row. PLD's has only 'Cash And Equivalents'; AWK's has 'Cash And Equivalents', 'Short Term Investments' and 'Restricted Cash'. So no bridge is built, and R4 is unpriceable because of the sheet's FORM, not its substance. The parts reconcile to CIQ's own 'Net Debt': AWK 16,427.0 − 121.0 − 29.0 = 16,277.0 exactly (Financials_Quarterly `c5844ae7d9`, Balance Sheet rows 80 'Total Debt', 17 'Cash And Equivalents', 18 'Short Term Investments', 81 'Net Debt', column 39 [Q3 Sep-30-2026]); PLD 37,490.782 − 2,273.497 = 35,217.285 against 35,200.599, 16.7 apart, not explained by the rows shown (Financials_Quarterly `d360d90d26`, Balance Sheet rows 74, 23 and 75, column 39 [Q3 Sep-30-2026]). Both knowable 2026-11-19. The unbuilt reason also says "at its latest column" for a row absent from every column | R (selects on form) | PLD, AWK (fresh packs). Controls MORN and RIVN carry the row. **0 of the 26 committed pages** carry this reason; the corpus has no REIT or utility template | `ciq_sheets.py:4046` (`_row_at(bs, "Total Cash & ST Investments", col)`); the parts are already listed in `ciq_balance._CASH_PARTS` (`ciq_balance.py:437`) | build the cash leg from the parts when the subtotal is absent, pinned on PLD's and AWK's real sheets; or say plainly that the row is absent from the template |
| D18 *(5a fresh)* | RIVN's LTM refusal is caused by CIQ's own data, so **no re-export clears it**. CIQ's annual export shows '-' for 'Gain (Loss) On Sale Of Invest.' in FY2025 and each earlier year shown, yet an LTM of 405.0 (Financials_Annual `a710dc0303`, Income Statement row 41, column 7 [12 months Dec-31-2025] '-', column 8 [LTM 12 months Sep-30-2026] 405.0), which is 506 (9M 2026) − 101 (9M 2025) + nothing for FY2025. CIQ's quarterly export shows 506.0 in Q1 2026 and '-' around it (Financials_Quarterly `4835b5b653`, Income Statement row 42, columns 24–27 [Q4 2025 to Q3 2026]: '-', 506.0, '-', '-'). Both knowable 2026-11-19. The filings side with the quarterly export: RIVN's 10-Qs tag `IncomeLossFromEquityMethodInvestments` 101.0 for Q1/6M/9M 2025 and 506.0 for Q1/6M/9M 2026 (0001874178-26-000035, -000054, -000066). The FY2025 10-K tags no FY figure under that concept, so Q4 2025 is not decided. **The guard is right** (the page would print 405). The tie-break cannot decide it: "no reviewed mapping from the CIQ row … (`filed_tiebreak.MAPPING`)" | R (a correct refusal, durable) | RIVN: the 2026-10-28 pack (LTM to Jun-30) refused on the same row; the 2026-11-19 pack's cells are cited here | `ltm_quarters.refused` (correct); `filed_tiebreak.MAPPING` has no row for this CIQ line | a reviewed mapping of this CIQ row to `IncomeLossFromEquityMethodInvestments`, measured on RIVN, would let the filing decide for the quarterly side; or an operator ruling. Not a re-export |
| D19 *(5a fresh)* | a missing **required** CIQ export raises a caveat, never a refusal. DVN's fresh folder without its (mislabelled) quarterly Financials passes the precheck: exit 0, 0 post-spend refusals. The page raises "pull CIQ 'Financials — Quarterly'" plus 8 "NOT CHECKED" LTM flags, and its anchor stops at "own-history multiple missing", so a paid build would spend on a page with nothing to price | spend (fails open) | DVN-noQ, a variant this probe built: DVN's fresh folder minus the mislabelled file, not a pack the operator made. 11a showed that a pack with no Financials at all *is* refused (materiality) | `requirements.manifest_flags`, the only consumer of `missing_required` (`assemble.py:1240`): flags only. Searched, no refusal found: callers of `missing_required(` / `manifest_flags(` / `is_required(`; `git log -i --grep` "required export\|missing required\|quarterly export.*absent\|no quarterly"; `git log -S missing_required` (one hit, e2257fb2, the manifest's creation) | a precheck refusal, or at least a verdict line, when a module that `is_required` for the sleeve is absent (an operator ruling first) |
| D20 *(5a fresh, tested in 11f addendum 1)* | two CIQ EBITDA definitions on one page, each consumed consistently but not labelled. CIQ's annual EBITDA excludes the annual Cash Flow row 'Other Amortization'; its quarterly EBITDA includes it (MORN: 719.4 + 102.7 = 822.1 exactly; cells cited in 11f addendum 1). The LTM-quarters flag reports the 12.49% DIFFER with no cause. `ev_ebitda_basis` calls the annual figure "reported LTM EBITDA", which is within 2% of the filing-rebuilt figure on only 7 of 17 live pages | label (no value wrong) | MORN (scratch). Live: the "reported" label is on every page with `ev_ebitda_basis` (17 carry the filing figure to compare: 10 beyond 2%). The annual-vs-quarters gap's cause on live pages was not read | `ltm_quarters` flag text; `ev_ebitda_basis._ltm_ebitda` and its line | name the cause when annual EBITDA + annual 'Other Amortization' = the four quarters (a deterministic check, pinned on MORN's real sheets); relabel "reported" as "CIQ annual, pre-rent" |
| D21 *(5a fresh, the operator's fact on AQN)* | a foreign filer whose CIQ primary listing is a home-market listing gets that market's currency in its quarterly Historical Capitalization panel (the sheet's own header: "In Millions of the trading currency"). `CiqCurrencyError` then refuses the whole pack, though it reports US GAAP in USD and every other money panel states USD (AQN: 17 of 18 USD; one CAD). No re-export cures it: CIQ offers no NYSE:AQN listing (the operator, 2026-11-19) | refuses (over-refusal: one market-data panel refuses a USD pack) | AQN (fresh pack). Population at risk is not measurable from the data held (11f addendum 3): 0 of the 76 G17/G17b names show a non-US venue in EDGAR's `exchanges`. Proxies: 7 file 40-F, 7 are incorporated in Canada, 13 carry an ADS line. 0 live pages are FPIs | `ciq_sheets.require_usd` over `_MONEY_PANELS` (`ciq_sheets.py:7871`); the panel's only page-path reader is `lease_basis.observations` (`lease_basis.py:301`) | **smallest, FX-free:** refuse the panel, not the pack. When Historical Capitalization states a non-USD currency, `lease_basis` refuses its ex-lease band with that reason and every other panel is read. **Fuller:** read the panel's stated currency and convert at a dated rate (its 'Pricing as of' date), which waits on stage 2's FX ruling (SP-R5) |
| D22 *(2026-11-20: DAC, PLD)* | a lessor with no CIQ rent row is treated as having material rent, so R1 declines on the form of its statements. With no 'Net Rental Exp.' row, `lease_basis._materiality` returns "treated as material"; the ex-lease band then needs CIQ's lease rows to reconcile to EDGAR's, and on a lessor there is nothing to reconcile (DAC: 0 quarters, ≥4 needed). DAC tags no lessee lease cost or operating-lease liability in EDGAR at all, only $945.8M of lease payments it will receive in 12 months, against FY2025 operating income $498.8M + D&A $163.4M (20-F 0001104659-26-021574) | R (fails closed; selects on form) | DAC (2026-11-20 pack), PLD (2026-11-19 pack). **0 of the 26 committed pages** at main `6c22b222` | `lease_basis._materiality` | when CIQ states no rent row, measure rent from EDGAR (`OperatingLeaseCost` / `LeaseCost`), read a filer with no lessee-lease tag as immaterial and say so, and refuse only when EDGAR cannot decide either |

**Observation, not tested as a defect (5a fresh, MORN)** — *tested since; see D20 and 11f addendum 1.* One page carries two LTM EBITDAs 12.49% apart, and the LTM check flags it: CIQ's annual LTM is 719.4 and its four quarters sum to 822.1. EBITDA is not a materiality row, so this is a flag by design (`ltm_quarters.py` docstring), never a refusal. `ev_ebitda_basis` divides by 719.4. The ex-lease band, which R1 prices on, and `ev_ebitda_ex_lease_at_price` divide by 822.1. On the same ex-lease TEV the two denominators give multiples 14% apart (values withheld: the TEV is a CIQ value with no recorded cell). Which one the band should divide is a method question, not decided here; the repo's own divergence check passes MORN ("the EBITDA basis is not divergent"). It may be the same family as D18 (CIQ's annual and quarterly exports disagreeing). Not checked here: CIQ's FY2025 annual EBITDA reads 593.4 (Financials_Annual `fef17b2405`, Income Statement row 80, column 9 [12 months Dec-31-2025]; knowable 2026-11-19), and its 2025 quarters were not read.

Also seen in 5a, not a defect claim: FINRA's short-interest query returned HTTP 204 for BRK in all
three symbol forms tried (`BRK-B`, `BRK.B`, `BRK/B`, through `vinci.finra.short_interest_points`).
The page says UNKNOWN, so it is loud. The cause was not found.

Not defects, recorded for the record: AVB's and ABB's tickers no longer resolve because they no
longer report (Form 15 / lapsed 20-F) — the resolver's "renamed/delisted?" is correct; EQR's
ticker is gone because the company renamed (VMRK).

---

## 10. Reproduction and what this did not do

**Scripts:** `scripts/archetype_probe/`. Its README gives every script's step, inputs and
outputs, the environment variables that carry every machine path, and how to run each at $0. Each
script imports `vinci` from the checkout it runs in and prints `vinci.__file__` first.

**Not done, and why:**
- ~~**No full `prespend.mechanical_build` per archetype.**~~ **Done in 5a (§11a).**
- ~~**No R3/R4 proposal run.**~~ **Done in 5a where a consensus block exists (§11b).**
- **The census's economic-model and overlap flags use SEC frames (calendar-aligned, not
  point-in-time).** They size archetypes; they are never a value on a page.
- **Stage-2 market caps are not measured** — the 95 names are a representative list, not a
  ranked one; only their SEC status is measured.
- **Polygon:** 3 calls (grouped daily 2026-11-18; ticker details `ESLOY`, `CODYY`). OTC lines are
  not in the grouped daily; per-symbol OTC aggregates were not tried.

---

## 11. 5a close-out — the full $0 build, the R3/R4 runs, and intake for the out-of-scope kinds

Asked by B on 2026-11-19 after the operator adopted step 5 ("adopt and start 5a"). Run at $0 and
read-only: no LLM client constructed, nothing committed, no checkout's `data/` touched.

### Boundary of every count below

| | |
|---|---|
| code | main `9d036cbb` (the worktree detached there); `vinci.__file__` printed by every script = the worktree's |
| date | 2026-11-19 (IST), builds `assembled_at` 2026-11-19T14:1x–15:0xZ |
| data dir | a SCRATCH copy: the committed `data/snapshots`, `data/facts`, `data/graph_coverage.json`; a scratch `followed.json` + `coverage_roster.jsonl` naming only the 5a names (`intake`, sleeve `quality`, `followed_since` 2026-11-19 — choices of this probe, stated); the probe's own SEC cache |
| reference date | **2026-10-16** for every page — the maintenance route takes the fleet's newest screen run (`2026-10-16-01`), not the clock (`assemble._fleet_reference_date`); prices on the page still strike at the 2026-11-18 close (#1132) |
| prices | a fresh scratch store: `vinci refresh <names> SPY IWM MDY --aggs --start 2024-11-20 --end 2026-11-18`, 16 symbols, 7,914 bars (2 years: the plan's 730-day window; CRWV from its 2025-03-28 listing). Per-symbol aggs, the RUNBOOKS §i route |
| CIQ | Drive's only packs for these names: PLD, RIVN, MTB, PCVX, each dated **2026-10-28**, copied into scratch for the run and deleted after (checked: 0 `.xls`/`.rtf` left in scratch or here) |
| population | 13 names, 16 builds: 8 in-scope (PLD, AWK, RIVN, CRWV, MORN, DVN, AQN, NBIS), 4 out-of-scope (MTB, PCVX, BRK-B, EPD), 1 control (SPGI); PLD, RIVN, MTB built twice (with their pack, and EDGAR-only) |
| command | `vinci.dossier.prespend.run` — the body of `vinci dossier precheck --ticker <T>` — then `prespend.mechanical_build` again for the page it would write |

### 11a. The full deterministic build, one name per in-scope archetype

**No build of the 16 passes the precheck today. All 16 exit 1.** Three refusals come from the
exports' dates or shape, and one cause is shared by every name without an export. None is caused
by the archetype.

| name | archetype | CIQ pack | before any model call | post-spend refusals decided at $0 | fields the control has and this page lacks (EDGAR-only) | what the page says about value |
|---|---|---|---|---|---|---|
| PLD | G13 REIT | 2026-10-28 | **REFUSED** — `CiqPreliminaryError`: 6 latest columns are CIQ "Press Release" columns (Q3 2026); the 10-Q was filed 2026-10-28, the export's own day | — (no page) | — | — |
| PLD | G13 REIT | none | passes | 2: materiality (no CIQ Financials), freshness (no market cap, **no share count**) | 7 — no share count (D6), no FCF ("no OCF/capex"), impairment headroom, buybacks | anchor `unknown`: no own-history band |
| AWK | G14 utility | none | passes | 2 (export-driven) | 2 — stale buyback cash (2021), stale impairment headroom | anchor `unknown`: no band |
| RIVN | G03 loss-making | 2026-10-28 | **REFUSED** — a MATERIAL annual-summary LTM row the quarterly export does not support (Gain (Loss) On Sale Of Invest.; the 2026-11-19 pack's cells are cited in D18), and the filing cannot decide it (no reviewed CIQ→filed mapping) | — (no page) | — | — |
| RIVN | G03 loss-making | none | passes | 2 (export-driven) | 12 — P/E "negative economics", net debt/EBITDA meaningless, no goodwill or intangibles tag | anchor `unknown`, not `R2_NEEDED` (D12) |
| CRWV | G03 loss-making | none | passes | 2: + no share count | 11 — no share count, debt left the tags read (D4), P/E negative | anchor `unknown` |
| MORN | G11 asset mgr | none | passes | 2 (export-driven) | **1** — buyback share count | anchor `unknown` |
| DVN | G05 E&P | none | passes | 2 (export-driven) | 5 — OI + D&A newest common year 2016 (D7) | anchor `unknown` |
| AQN | G17 FPI 40-F | none | passes | 2 (export-driven) | 6 — covenant pointers (no agreement exhibit), buybacks, impairments | anchor `unknown` |
| NBIS | G17 FPI 20-F | none | passes | 2 (export-driven) | 6 — non-operating share (no quarterly XBRL), net debt/EBITDA meaningless; anchor diluted count UNKNOWN (D16) | anchor `unknown` — D2 not reached (below) |
| SPGI | G01 CONTROL | none | passes | 2 (export-driven) | — (39 of 106 Sourced fields present) | anchor `unknown` |

"Export-driven" = the two refusals SPGI gets too: `_materiality_check` · `MaterialityUnavailableError`
(no CIQ Financials workbook) and `_freshness_check` · `FreshnessError` (no market cap; the cap is
CIQ's comps figure, and the page's close × share count is only its cross-check). Both are refusals the
**paid build makes only after its LLM calls**; the precheck catches them at $0, which is what it is
for. "Fields the control has and this page lacks" compares each page's outermost Sourced fields with
SPGI's, built the same way (`diff5a.py`; lists not walked).

**What the build shows that the per-layer probe could not:**
1. **Without a CIQ export the anchor never reaches the archetype.** `compute_anchor`'s first gate
   is CIQ's own-history band, so every EDGAR-only page stops at "own-history multiple missing",
   SPGI included. The REIT margin defect (D1) and the transformed-history defect (D2) are both
   behind that gate. For NBIS, D2 reaches a page only if its export carries an EV/EBITDA band.
   Whether it does is unknown, because there is no export.
2. **The share-count gap (D6) becomes a hard stop.** PLD, CRWV and BRK-B have no usable count, and
   the freshness check refuses each of them for it, on top of the export refusals.
3. **The event rule (#1132) works on a real pack.** PCVX's 2026-10-27 panel predates its 8-K item
   2.02 of 2026-11-04 and is refused. PLD's pack was exported on its 10-Q day (2026-10-28). MTB's was
   exported between its 2026-10-16 release and its 2026-11-05 10-Q. Both still carry
   press-release columns.
4. **All four packs are outdated by a later filing.** PLD: 10-Q the same day. MTB: 10-Q
   2026-11-05. PCVX: 8-K item 2.02 2026-11-04. RIVN: 10-Q and 8-K item 2.02 2026-10-29. Three refuse
   on that (PLD and MTB as preliminary columns, PCVX by the event rule). RIVN refuses first on a CIQ
   self-disagreement, and the event rule would refuse it next. Packs exported weeks before a build
   will mostly refuse. That is the rule doing its job, not an archetype finding.

**Exports that would complete the CIQ-dependent cells** (the repo's own list,
`vinci dossier requirements --ticker <T>`, quality book). Not asked for yet:
- **AWK, CRWV, MORN, DVN, AQN, NBIS** (and BRK-B, EPD): Financials — Annual; Financials —
  Quarterly; Estimates Report; Business Relationships (Customers & Suppliers); and Company
  Comparable Analysis (required for the quality book).
- **PLD, MTB:** a re-export of both Financials now that the Q3 10-Q is in CIQ.
- **PCVX:** a re-export of the valuation panels dated after 2026-11-04.
- **RIVN:** both Financials re-exported after its 2026-10-29 10-Q, once its annual and quarterly
  agree on the gain row. The refusal says to read both before re-exporting.

*(For PLD, AWK, RIVN, MORN, DVN and AQN this list is superseded by §11f: the operator exported
them on 2026-11-19, and §11f states what is still owed.)*

### 11b. R3/R4 proposal runs, where a CIQ consensus block exists

Only **PCVX** produced a page carrying a consensus block, so it is the only name a proposal could
run on. The packs of PLD, RIVN and MTB were refused before a page existed, so a proposal cannot run
on them. For those three, the table shows what the page's own reader (`ciq_sheets.forward_consensus`,
`own_history_bands`) yields from the pack: the inputs a proposal would read once a re-export clears
the refusal. These are **inputs, not proposals** (`ciq5a.py`). The six EDGAR-only names have no
consensus block at all: R3 needs CIQ forward EPS and R4 needs CIQ NTM TEV/EBIT. **It cannot run for
them.**

| name | consensus | R4 (1) NTM EBIT > 0 | R4 (2) R1 cannot anchor | R4 (3) GAAP P/E + material non-op | machine proposal | R3 template (simulated tag) | R4 template (simulated tag) |
|---|---|---|---|---|---|---|---|
| PCVX (page) | 45 multiples, all NM except TEV/REV FY2027; EPS basis undetermined | unknown (no NTM TEV/EBIT) | met (R1 declines) | unknown (basis undetermined) | **none** — an unknown condition proposes nothing | REFUSED: `applicable` is R1's bit (STATE §5.0 row 10) | REFUSED: the point-in-time and diluted weighted-average share counts disagree by 5.93% |
| PLD (pack inputs) | 45 multiples; a positive NTM TEV/EBIT and an NTM P/E, FY P/E on **GAAP** EPS; EV/EBITDA band 22 closes | met | **likely not met** — the band exists, so R1 would get past its first gate; its margin and D&A gates are not decidable without the page | basis gaap; the non-op count needs the page | most likely R1 stays (not decidable before a re-export) | would price GAAP EPS, which is depreciation-burdened for a REIT — the §7 method gap, not a code gap | — |
| RIVN (pack inputs) | 54 multiples; TEV/REV only; no band | not met (no NTM TEV/EBIT) | — | undetermined | **none** | none possible (no forward EPS) | none possible (no forward EBIT) |
| MTB (pack inputs) | **0** forward multiples; P/LTM EPS band only (22 closes) | not met | — | — | **none** | none possible from this export | none possible |

The simulated tags re-derive `valuation_basis` through `schemas.dossier_json` (its one writer) and
call `propose.build_template`. They measure what an operator's R3 or R4 tag would hand the analyst;
**no tag was written anywhere**. On every EDGAR-only page both templates refuse: R3 on the row-10
coupling, R4 because no `ev_bridge` exists without CIQ's quarterly Balance Sheet.

### 11c. Intake for each out-of-scope kind — measured, not changed

The paid command's gates, in `cli._cmd_dossier`'s order, run as functions so nothing could reach a
model client (`intake5a.py`). State A is main as it is: a scratch copy of the committed data dir.
State B is after the operator's two intake steps (RUNBOOKS §i 1 + 1b): a follow entry and an
`intake` roster line.

| name | kind | state A — main today | state B — after the two steps | the paid build's pre-LLM part (5a build, state B) | post-spend refusals at $0 |
|---|---|---|---|---|---|
| MTB | bank | refused at `load_finalists`: `LookupError` "not in candidate_records.jsonl and not maintained", **before any client** | every gate passes → the CLI constructs the model client | with its pack: refused (`CiqPreliminaryError`, timing); EDGAR-only: passes | 2, export-driven |
| PCVX | pre-revenue biotech | same refusal | passes → model client | **with its pack: passes** (page built, both calls read, so `_refuse_unread_calls` would not fire) | **1: freshness (timing)**. A re-export after 2026-11-04 clears it, and the paid build would then run its covenant, driver and five synthesis calls and **write** a page whose recipe is `unknown` and is not priceable |
| BRK-B | conglomerate / insurer | same refusal | passes → model client | EDGAR-only: passes | 2 (+ no share count) |
| EPD | MLP | same refusal | passes → model client | EDGAR-only: passes | 2, export-driven |

**What intake does today, by route:**
- **Follow route.** Nothing reads the archetype. The roster line is the only gate, and the operator
  writes it by hand. Once it is there, a bank, a biotech, BRK or an MLP reaches the paid phases.
  Each is then stopped only by the export's dates or by a missing export, never because it is out
  of scope.
- **Screen route.** The universe's SIC deny-list (6189, 6221, 6722, 6726, 6770) admits all four
  kinds. A screen candidate with no roster line is refused by `require_buildable` before any model
  call (the CLI refuses the whole run), so the roster is the gate here too. With a line, nothing
  refuses the kind.
- **Searched for an archetype or scope guard at intake, not found.** Searches tried:
  - `grep -rniE "out[ _-]of[ _-]scope|OUT_OF_SCOPE|unsupported_sic|archetype"` over `vinci/`;
  - SIC-keyed refusals in `assemble.py`, `followed.py`, `coverage_roster.py`, `cli.py`, `mechanical.py`;
  - `git log --all -i --grep` for "out of scope" and "archetype";
  - `git log -S` for `OUT_OF_SCOPE` and `out_of_scope` (one hit, #19c's material-figure refusal, unrelated).

  The only SIC test on the build path is net debt's per-layer refusal (`mechanical.py:2445`).
  **The out-of-scope guard is the step-6 build**, for the scope pack, and is not built here.

### 11d. What 5a changes in the plan (for B)

- **G03 (loss-making, "once R2 is built"):** the R2 build must also change the anchor's routing
  (D12). Today a loss-maker with NM multiples never reaches `R2_NEEDED`, so R2's dispatch would not
  see RIVN, CRWV, FUBO, ORKA or TECX.
- **G13 REITs (refused until P/FFO):** confirmed. PLD's pack also offers no FFO line through the
  readers. R3 on it would price GAAP EPS. D6 (PLD's share count) stops the page on its own.
- **G17 FPI US GAAP USD:** two FPI gaps that §6 did not show — no diluted count for a 20-F filer
  (D16), and R4's condition 3 undecidable without quarterly XBRL. D2 is gated behind the CIQ band.
- **Out of scope at intake:** today nothing stops an out-of-scope name once its roster line is
  written. PCVX shows the cost: a clean re-export plus an `intake` line gives a fully paid build of
  a page priced on nothing. The step-6 guard belongs before the model client, at `require_buildable`
  or `load_finalists`.
- **Every first build will need fresh exports.** The four 2026-10-28 packs all refuse for date or
  shape reasons. That is RUNBOOKS §i step 3's job, but it means a 5b batch should budget a re-export
  pass before any precheck.

**New defects (§9):** D11–D16. D13 (EPD's false P/E cause) is the one wrong-output finding. The others
refuse loudly, or are a contained inconsistency (D14) or a doc gap (D15).

**Reproduction** (`scripts/archetype_probe/`; outputs regenerate under `<WORK>/out/`):
- `setup5a.py` writes the scratch follow list and roster;
- `build5a.py <T> | <T>:nociq` runs the precheck, the page, the R4 conditions and the three templates;
- `ciq5a.py` reads the packs' consensus inputs;
- `intake5a.py` runs the gates in states A and B;
- `diff5a.py` compares each page with the control.

Each script prints `vinci.__file__` and keeps every write in the scratch dir. Cost: $0 — 0 LLM calls;
Polygon 16 per-symbol aggs; EDGAR and FINRA reads through the repo's clients, cached in scratch
(one FINRA query per page, plus 3 direct ones for BRK).

### 11e. D13 on the live corpus — is "a more recent annual figure exists and is negative" true?

Asked by B after the 5a review. B confirmed the mechanism: `G3_EPS_TOO_OLD`
(`screens/assemble.py:79`, printed from :453) fires when `annual_eps_point_as_of` finds no
positive annual EPS within 470 days but an older positive exists. Nothing checks that a newer
figure exists.

**Boundary.**
- **Code and data:** main `2ecf6da0` (#1136; a descendant of 5a's `9d036cbb`; touches no screen
  or EDGAR code). Run 2026-11-19 (IST).
- **Population, pages:** the **5** `data/dossiers/*/dossier.json` whose
  `mechanical.valuation.pe.note` carries the text: CNXC, FUBO, TECX, WERN, WLK. On all 5 it is also
  in `pe_percentile_5y.note`. On WLK alone it is also restated by the synthesis
  (`key_unknowns[1]`) and RENDERED (`dossier.md:216`).
- **Population, records:** the **109** `data/snapshots/candidate_records.jsonl` records whose
  `data_record.fundamentals.pe.note` carries it. All are from screen run 2026-10-16 and are 109
  distinct names.
- **Unit:** one item = one page or one record. EPS values are as filed, in the filer's own unit.
- **Each item is judged at its own date:** a page's `reference_date` (2026-10-16 for four,
  2026-08-14 for FUBO), a record's `data_record.as_of` (2026-10-16).
- **Companyfacts:** fetched 2026-11-19 through the repo's SEC client and cut on `filed <= date`
  (`facts_as_of`). The screen cuts at the newest price bar on or before that date; this audit cuts
  at the date itself. Both dates are Fridays and trading days, so the two agree for any name with a
  bar that day. That is an approximation, stated.

**Method** (`scripts/archetype_probe/d13audit.py`).
1. Replay the reader exactly: `served_series(cut, "eps_diluted", currency=REPORTING, as_of=d)`,
   annual points (`is_annual`, 350–380 days). The note is REPRODUCED when the 470-day read returns
   None and the unbounded read returns a positive point P. **It reproduced on all 114.**
2. "Newer" = an annual point filed by d whose period ends after P's.
3. Search beyond the served series. Every us-gaap AND ifrs-full tag matching EarningsPerShare\*,
   EarningsLossPerShare, IncomeLossFromContinuingOperationsPer\*Share\*,
   \*PerOutstandingLimitedPartnershipUnit\* or \*PerLimitedPartnershipUnit\*: diluted, basic,
   basic-and-diluted and per-unit. Pro-forma, dividend and distribution tags are excluded, and the
   facts are read raw, because `points_for_tag` walks dei/us-gaap only.
4. For a TRUE item, check also whether a still-newer figure under another tag is positive. None was;
   two (NG, SSYS) carry a still-newer basic figure, and it is negative too.
5. **Control:** EPD at 2026-10-16, known from 5a to be false, reads **FALSE** ("the tag changed:
   newer annual EPS exists only under …PerOutstandingLimitedPartnershipUnit…, and it is POSITIVE").
   So the check can find a FALSE.

**Result.**

| population | TRUE | FALSE | OTHER |
|---|---|---|---|
| live pages (5) | **5** | **0** | 0 |
| candidate records (109) | **107** | **0** | 2 |
| control (EPD, 5a scratch page) | — | 1 (as expected) | — |

- **No live page reads FALSE.** The claim each of the five prints is true at its date, under the
  very tag the reader serves (table below).
- **ORC (record): OTHER, and its conclusion is false.**
  - The served diluted series stops at FY2019 (+0.43, `0001275477-20-000030`).
  - A newer negative exists: FY2021, −0.54, under `EarningsPerShareBasicAndDiluted`,
    `0001518621-22-000023`.
  - Its newest annual EPS is **positive**: FY2025 `EarningsPerShareBasic` +1.24,
    `0001437749-26-004889`, filed 2026-02-20.

  So "a more recent figure exists and is negative" is literally true, but "a business that no
  longer reports those earnings" is false for its latest year.
- **LPL (record, LG Display, 20-F): OTHER.**
  - The served series is US GAAP KRW and stops at FY2009 (+3,070).
  - The newer figures are negative but exist only under IFRS: `ifrs-full:DilutedEarningsLossPerShare`
    FY2024 −5,438 KRW/sh, `0000950170-25-058944`.

  The claim is true of the business and false of the series the reader served, since it never saw
  the IFRS figure (FPI1b/the IFRS build).
- **Units among the TRUE:** 111 USD/sh, 1 CNY/sh. **Served tags:** 111
  `EarningsPerShareDiluted`, 1 `IncomeLossFromContinuingOperationsPerDilutedShare`.

**For D13:** the defect is real in its mechanism and latent on the live corpus. Three kinds of
filer would print it falsely: an MLP's move to per-unit EPS (EPD), a diluted→basic move (ORC), and
a US GAAP→IFRS move (LPL). Stage 1 admits the second; the first is out of scope for stage 1
(SP-R4, ruled 2026-11-20); the third is stage 2. The fix in D13's row stands: split the branch on whether a newer
figure exists.

**TRUE, pages** — the newest figure newer than the latest positive one:

| name | judged at | latest positive annual EPS (end, value) | newer figure's tag | period end | value | accession |
|---|---|---|---|---|---|---|
| CNXC | 2026-10-16 | 2024-11-30 3.71 | EarningsPerShareDiluted | 2025-11-30 | -20.36 USD/sh | 0001803599-26-000027 |
| FUBO | 2026-08-14 | 2017-12-31 0.74 | EarningsPerShareDiluted | 2024-12-31 | -0.54 USD/sh | 0001628280-25-009420 |
| TECX | 2026-10-16 | 2023-12-31 0.27 | EarningsPerShareDiluted | 2025-12-31 | -4.05 USD/sh | 0001193125-26-076793 |
| WERN | 2026-10-16 | 2024-12-31 0.55 | EarningsPerShareDiluted | 2025-12-31 | -0.24 USD/sh | 0000793074-26-000071 |
| WLK | 2026-10-16 | 2024-12-31 4.64 | EarningsPerShareDiluted | 2025-12-31 | -11.7 USD/sh | 0001262823-26-000016 |

**TRUE, records** (107; the newest figure newer than the latest positive one):

| name | judged at | latest positive annual EPS (end, value) | newer figure's tag | period end | value | accession |
|---|---|---|---|---|---|---|
| AAOI | 2026-10-16 | 2017-12-31 3.67 | EarningsPerShareDiluted | 2025-12-31 | -0.64 USD/sh | 0001437749-26-005875 |
| ACDC | 2026-10-16 | 2022-12-31 2.06 | EarningsPerShareDiluted | 2025-12-31 | -2.22 USD/sh | 0001193125-26-106120 |
| ADNT | 2026-10-16 | 2024-09-30 0.2 | EarningsPerShareDiluted | 2025-09-30 | -3.39 USD/sh | 0001670541-25-000152 |
| ADTN | 2026-10-16 | 2020-12-31 0.05 | EarningsPerShareDiluted | 2025-12-31 | -0.52 USD/sh | 0001193125-26-073878 |
| AEHR | 2026-10-16 | 2024-05-31 1.12 | EarningsPerShareDiluted | 2026-05-29 | -0.23 USD/sh | 0001654954-26-006919 |
| AESI | 2026-10-16 | 2024-12-31 0.55 | EarningsPerShareDiluted | 2025-12-31 | -0.41 USD/sh | 0001193125-26-067145 |
| AHCO | 2026-10-16 | 2024-12-31 0.61 | EarningsPerShareDiluted | 2025-12-31 | -0.52 USD/sh | 0001628280-26-011213 |
| ALGM | 2026-10-16 | 2024-03-29 0.78 | EarningsPerShareDiluted | 2026-03-27 | -0.08 USD/sh | 0001193125-26-233537 |
| ALGT | 2026-10-16 | 2023-12-31 6.29 | EarningsPerShareDiluted | 2025-12-31 | -2.48 USD/sh | 0001362468-26-000008 |
| ALT | 2026-10-16 | 2016-12-31 2.95 | EarningsPerShareDiluted | 2025-12-31 | -1 USD/sh | 0001326190-26-000018 |
| AOSL | 2026-10-16 | 2023-06-30 0.42 | EarningsPerShareDiluted | 2026-06-30 | -1.41 USD/sh | 0001628280-26-059261 |
| ARRY | 2026-10-16 | 2023-12-31 0.56 | EarningsPerShareDiluted | 2025-12-31 | -0.73 USD/sh | 0001820721-26-000008 |
| AVAV | 2026-10-16 | 2025-04-30 1.55 | EarningsPerShareDiluted | 2026-04-30 | -5.4 USD/sh | 0001104659-26-078906 |
| AVTX | 2026-10-16 | 2017-12-31 0.42 | EarningsPerShareDiluted | 2025-12-31 | -5.84 USD/sh | 0001534120-26-000011 |
| AXTI | 2026-10-16 | 2022-12-31 0.37 | EarningsPerShareDiluted | 2025-12-31 | -0.49 USD/sh | 0001437749-26-008612 |
| BKD | 2026-10-16 | 2020-12-31 0.44 | EarningsPerShareDiluted | 2025-12-31 | -1.12 USD/sh | 0001332349-26-000032 |
| BRSP | 2026-10-16 | 2022-12-31 0.34 | EarningsPerShareDiluted | 2025-12-31 | -0.26 USD/sh | 0001717547-26-000008 |
| BTBT | 2026-10-16 | 2024-12-31 0.19 | EarningsPerShareDiluted | 2025-12-31 | -0.31 USD/sh | 0001213900-26-035544 |
| BW | 2026-10-16 | 2021-12-31 0.26 | EarningsPerShareDiluted | 2025-12-31 | -0.48 USD/sh | 0001630805-26-000018 |
| CAPR | 2026-10-16 | 2017-12-31 0.09 | EarningsPerShareDiluted | 2025-12-31 | -2.26 USD/sh | 0001104659-26-029580 |
| CBIO | 2026-10-16 | 2012-12-31 0.33 | EarningsPerShareDiluted | 2024-12-31 | -0.59 USD/sh | 0001558370-25-000948 |
| CC | 2026-10-16 | 2024-12-31 0.46 | EarningsPerShareDiluted | 2025-12-31 | -2.57 USD/sh | 0001193125-26-065201 |
| CCOI | 2026-10-16 | 2023-12-31 26.62 | EarningsPerShareDiluted | 2025-12-31 | -3.8 USD/sh | 0001104659-26-017968 |
| CE | 2026-10-16 | 2023-12-31 17.76 | EarningsPerShareDiluted | 2025-12-31 | -10.64 USD/sh | 0001306830-26-000031 |
| CORZ | 2026-10-16 | 2021-12-31 0.2 | EarningsPerShareDiluted | 2025-12-31 | -0.88 USD/sh | 0001628280-26-013305 |
| CPS | 2026-10-16 | 2019-12-31 3.92 | EarningsPerShareDiluted | 2025-12-31 | -0.23 USD/sh | 0001320461-26-000012 |
| CSIQ | 2026-10-16 | 2024-12-31 0.54 | EarningsPerShareDiluted | 2025-12-31 | -2.5 USD/sh | 0001104659-26-041976 |
| CTMX | 2026-10-16 | 2024-12-31 0.38 | IncomeLossFromContinuingOperationsPerDilutedShare | 2025-12-31 | -0.15 USD/sh | 0001193125-26-107146 |
| DJT | 2026-10-16 | 2022-12-31 0.58 | EarningsPerShareDiluted | 2025-12-31 | -2.8 USD/sh | 0001140361-26-007174 |
| DQ | 2026-10-16 | 2023-12-31 1.15 | EarningsPerShareDiluted | 2025-12-31 | -0.51 USD/sh | 0001104659-26-045134 |
| ECVT | 2026-10-16 | 2023-12-31 0.6 | EarningsPerShareDiluted | 2025-12-31 | -0.61 USD/sh | 0001708035-26-000053 |
| ELVN | 2026-10-16 | 2022-12-31 0.06 | EarningsPerShareDiluted | 2025-12-31 | -1.83 USD/sh | 0001193125-26-088232 |
| ENOV | 2026-10-16 | 2021-12-31 1.4 | EarningsPerShareDiluted | 2025-12-31 | -20.75 USD/sh | 0001420800-26-000012 |
| FMC | 2026-10-16 | 2024-12-31 2.72 | EarningsPerShareDiluted | 2025-12-31 | -17.88 USD/sh | 0000037785-26-000041 |
| FUBO | 2026-10-16 | 2017-12-31 0.74 | EarningsPerShareDiluted | 2024-12-31 | -0.54 USD/sh | 0001628280-25-009420 |
| FUN | 2026-10-16 | 2023-12-31 2.42 | EarningsPerShareDiluted | 2025-12-31 | -15.89 USD/sh | 0001999001-26-000048 |
| FWRD | 2026-10-16 | 2023-12-31 6.4 | EarningsPerShareDiluted | 2025-12-31 | -3.51 USD/sh | 0001628280-26-016793 |
| GT | 2026-10-16 | 2024-12-31 0.16 | EarningsPerShareDiluted | 2025-12-31 | -5.99 USD/sh | 0001628280-26-006708 |
| HIVE | 2026-10-16 | 2024-03-31 0.29 | EarningsPerShareDiluted | 2026-03-31 | -0.66 USD/sh | 0001062993-26-002973 |
| HROW | 2026-10-16 | 2019-12-31 0.01 | EarningsPerShareDiluted | 2025-12-31 | -0.14 USD/sh | 0001493152-26-008562 |
| HTZ | 2026-10-16 | 2023-12-31 1.39 | EarningsPerShareDiluted | 2025-12-31 | -2.43 USD/sh | 0001657853-26-000008 |
| HUN | 2026-10-16 | 2023-12-31 0.57 | EarningsPerShareDiluted | 2025-12-31 | -1.65 USD/sh | 0001437749-26-004524 |
| ICHR | 2026-10-16 | 2022-12-30 2.51 | EarningsPerShareDiluted | 2025-12-26 | -1.54 USD/sh | 0001652535-26-000012 |
| IONS | 2026-10-16 | 2019-12-31 1.9 | EarningsPerShareDiluted | 2025-12-31 | -2.38 USD/sh | 0000874015-26-000115 |
| IRD | 2026-10-16 | 2022-12-31 0.87 | EarningsPerShareDiluted | 2025-12-31 | -0.8 USD/sh | 0001140361-26-009247 |
| JBGS | 2026-10-16 | 2022-12-31 0.7 | EarningsPerShareDiluted | 2025-12-31 | -2.09 USD/sh | 0001104659-26-016450 |
| JBLU | 2026-10-16 | 2019-12-31 1.91 | EarningsPerShareDiluted | 2025-12-31 | -1.66 USD/sh | 0001158463-26-000007 |
| JBTM | 2026-10-16 | 2024-12-31 2.65 | EarningsPerShareDiluted | 2025-12-31 | -0.98 USD/sh | 0001433660-26-000053 |
| JKS | 2026-10-16 | 2023-12-31 15.23 | EarningsPerShareDiluted | 2025-12-31 | -21.33 CNY/sh | 0001104659-26-050737 |
| KODK | 2026-10-16 | 2024-12-31 0.9 | EarningsPerShareDiluted | 2025-12-31 | -1.78 USD/sh | 0001193125-26-104214 |
| LAES | 2026-10-16 | 2022-12-31 0.41 | EarningsPerShareDiluted | 2024-12-31 | -0.6 USD/sh | 0001193805-25-000334 |
| LASR | 2026-10-16 | 2018-12-31 0.32 | EarningsPerShareDiluted | 2025-12-31 | -0.47 USD/sh | 0001124796-26-000012 |
| LPTH | 2026-10-16 | 2020-06-30 0.03 | EarningsPerShareDiluted | 2026-06-30 | -0.38 USD/sh | 0001437749-26-030106 |
| LUMN | 2026-10-16 | 2021-12-31 1.91 | EarningsPerShareDiluted | 2025-12-31 | -1.75 USD/sh | 0000018926-26-000014 |
| LXRX | 2026-10-16 | 2019-12-31 1.16 | EarningsPerShareDiluted | 2025-12-31 | -0.14 USD/sh | 0001062822-26-000050 |
| MARA | 2026-10-16 | 2024-12-31 1.72 | EarningsPerShareDiluted | 2025-12-31 | -3.69 USD/sh | 0001507605-26-000007 |
| MATW | 2026-10-16 | 2023-09-30 1.26 | EarningsPerShareDiluted | 2025-09-30 | -0.79 USD/sh | 0000063296-25-000070 |
| MEC | 2026-10-16 | 2024-12-31 1.24 | EarningsPerShareDiluted | 2025-12-31 | -0.4 USD/sh | 0001104659-26-023496 |
| MGPI | 2026-10-16 | 2024-12-31 1.56 | EarningsPerShareDiluted | 2025-12-31 | -4.99 USD/sh | 0000835011-26-000031 |
| MIAX | 2026-10-16 | 2024-12-31 1.39 | EarningsPerShareDiluted | 2025-12-31 | -1 USD/sh | 0001438472-26-000023 |
| MIDD | 2026-10-16 | 2024-12-28 7.9 | EarningsPerShareDiluted | 2026-01-03 | -5.32 USD/sh | 0000769520-26-000011 |
| MP | 2026-10-16 | 2023-12-31 0.14 | EarningsPerShareDiluted | 2025-12-31 | -0.5 USD/sh | 0001801368-26-000008 |
| MYGN | 2026-10-16 | 2019-06-30 0.06 | EarningsPerShareDiluted | 2025-12-31 | -3.95 USD/sh | 0000899923-26-000018 |
| NG | 2026-10-16 | 2011-11-30 0.07 | EarningsPerShareDiluted | 2013-11-30 | -0.2 USD/sh | 0001102624-14-000184 |
| NKTR | 2026-10-16 | 2018-12-31 3.78 | EarningsPerShareDiluted | 2025-12-31 | -9.73 USD/sh | 0001193125-26-104547 |
| NTGR | 2026-10-16 | 2024-12-31 0.42 | EarningsPerShareDiluted | 2025-12-31 | -0.63 USD/sh | 0001193125-26-051346 |
| NXRT | 2026-10-16 | 2024-12-31 0.04 | EarningsPerShareDiluted | 2025-12-31 | -1.26 USD/sh | 0001193125-26-077343 |
| OFIX | 2026-10-16 | 2020-12-31 0.13 | EarningsPerShareDiluted | 2025-12-31 | -2.33 USD/sh | 0001193125-26-065189 |
| OI | 2026-10-16 | 2022-12-31 3.67 | EarningsPerShareDiluted | 2025-12-31 | -0.84 USD/sh | 0001104659-26-014319 |
| OIS | 2026-10-16 | 2023-12-31 0.2 | EarningsPerShareDiluted | 2025-12-31 | -1.86 USD/sh | 0001121484-26-000012 |
| OLN | 2026-10-16 | 2024-12-31 0.91 | EarningsPerShareDiluted | 2025-12-31 | -0.88 USD/sh | 0000074303-26-000027 |
| OVID | 2026-10-16 | 2021-12-31 1.76 | EarningsPerShareDiluted | 2023-12-31 | -0.74 USD/sh | 0001628280-24-009809 |
| OXM | 2026-10-16 | 2025-02-01 5.87 | EarningsPerShareDiluted | 2026-01-31 | -1.86 USD/sh | 0000075288-26-000026 |
| PLTK | 2026-10-16 | 2024-12-31 0.44 | EarningsPerShareDiluted | 2025-12-31 | -0.55 USD/sh | 0001828016-26-000010 |
| PPTA | 2026-10-16 | 2022-12-31 0.46 | EarningsPerShareDiluted | 2025-12-31 | -1.08 USD/sh | 0001104659-26-037403 |
| RCAT | 2026-10-16 | 2017-12-31 0.04 | EarningsPerShareDiluted | 2025-12-31 | -0.73 USD/sh | 0001628280-26-019861 |
| REZI | 2026-10-16 | 2024-12-31 0.61 | EarningsPerShareDiluted | 2025-12-31 | -3.77 USD/sh | 0001740332-26-000005 |
| RGNX | 2026-10-16 | 2021-12-31 2.91 | EarningsPerShareDiluted | 2025-12-31 | -3.76 USD/sh | 0001193125-26-094013 |
| RIOT | 2026-10-16 | 2024-12-31 0.34 | EarningsPerShareDiluted | 2025-12-31 | -1.95 USD/sh | 0001104659-26-022322 |
| RWT | 2026-10-16 | 2024-12-31 0.32 | EarningsPerShareDiluted | 2025-12-31 | -0.63 USD/sh | 0000930236-26-000007 |
| RYAM | 2026-10-16 | 2021-12-31 1.05 | EarningsPerShareDiluted | 2025-12-31 | -6.33 USD/sh | 0001597672-26-000010 |
| SEDG | 2026-10-16 | 2023-12-31 0.6 | EarningsPerShareDiluted | 2025-12-31 | -6.88 USD/sh | 0001178913-26-001595 |
| SHEN | 2026-10-16 | 2024-12-31 3.54 | EarningsPerShareDiluted | 2025-12-31 | -0.71 USD/sh | 0000354963-26-000125 |
| SLDP | 2026-10-16 | 2021-12-31 0.11 | EarningsPerShareDiluted | 2025-12-31 | -0.51 USD/sh | 0001104659-26-019435 |
| SNDX | 2026-10-16 | 2021-12-31 0.46 | EarningsPerShareDiluted | 2025-12-31 | -3.29 USD/sh | 0001193125-26-076536 |
| SPRY | 2026-10-16 | 2024-12-31 0.08 | EarningsPerShareDiluted | 2025-12-31 | -1.74 USD/sh | 0001193125-26-097478 |
| SRPT | 2026-10-16 | 2024-12-31 2.34 | EarningsPerShareDiluted | 2025-12-31 | -7.13 USD/sh | 0001193125-26-084144 |
| SSYS | 2026-10-16 | 2012-12-31 0.36 | EarningsPerShareDiluted | 2022-12-31 | -0.44 USD/sh | 0001213900-23-017015 |
| SUPN | 2026-10-16 | 2024-12-31 1.32 | EarningsPerShareDiluted | 2025-12-31 | -0.68 USD/sh | 0001356576-26-000011 |
| TDS | 2026-10-16 | 2021-12-31 1 | EarningsPerShareDiluted | 2025-12-31 | -0.65 USD/sh | 0001051512-26-000011 |
| TECX | 2026-10-16 | 2023-12-31 0.27 | EarningsPerShareDiluted | 2025-12-31 | -4.05 USD/sh | 0001193125-26-076793 |
| TMQ | 2026-10-16 | 2020-11-30 1.12 | EarningsPerShareDiluted | 2025-11-30 | -0.26 USD/sh | 0001104659-26-015668 |
| TNDM | 2026-10-16 | 2021-12-31 0.24 | EarningsPerShareDiluted | 2025-12-31 | -3.04 USD/sh | 0001438133-26-000010 |
| TROX | 2026-10-16 | 2022-12-31 3.16 | EarningsPerShareDiluted | 2025-12-31 | -2.97 USD/sh | 0001530804-26-000006 |
| TWI | 2026-10-16 | 2023-12-31 1.25 | EarningsPerShareDiluted | 2025-12-31 | -1 USD/sh | 0000899751-26-000007 |
| UAMY | 2026-10-16 | 2011-12-31 0.01 | EarningsPerShareDiluted | 2025-12-31 | -0.04 USD/sh | 0001104659-26-032049 |
| UCTT | 2026-10-16 | 2024-12-27 0.52 | EarningsPerShareDiluted | 2025-12-26 | -4 USD/sh | 0001628280-26-010744 |
| UEC | 2026-10-16 | 2022-07-31 0.02 | EarningsPerShareDiluted | 2026-07-31 | -0.28 USD/sh | 0001437749-26-031414 |
| URG | 2026-10-16 | 2018-12-31 0.03 | EarningsPerShareDiluted | 2025-12-31 | -0.2 USD/sh | 0001104659-26-025923 |
| UUUU | 2026-10-16 | 2023-12-31 0.62 | EarningsPerShareDiluted | 2025-12-31 | -0.38 USD/sh | 0001385849-26-000009 |
| VIAV | 2026-10-16 | 2025-06-28 0.15 | EarningsPerShareDiluted | 2026-06-27 | -0.13 USD/sh | 0001628280-26-056765 |
| WLK | 2026-10-16 | 2024-12-31 4.64 | EarningsPerShareDiluted | 2025-12-31 | -11.7 USD/sh | 0001262823-26-000016 |
| WSC | 2026-10-16 | 2024-12-31 0.15 | EarningsPerShareDiluted | 2025-12-31 | -0.29 USD/sh | 0001647088-26-000011 |
| WULF | 2026-10-16 | 2018-12-31 0.07 | EarningsPerShareDiluted | 2025-12-31 | -1.66 USD/sh | 0001083301-26-000031 |
| WYFI | 2026-10-16 | 2024-12-31 0.05 | EarningsPerShareDiluted | 2025-12-31 | -0.78 USD/sh | 0001213900-26-034341 |
| XENE | 2026-10-16 | 2014-12-31 3.28 | EarningsPerShareDiluted | 2025-12-31 | -4.36 USD/sh | 0001193125-26-076650 |
| XRAY | 2026-10-16 | 2021-12-31 1.87 | EarningsPerShareDiluted | 2025-12-31 | -3 USD/sh | 0000818479-26-000075 |

### 11f. Fresh exports — the six names re-run (asked by B, 2026-11-19, after reviewing 5a)

The operator exported fresh CIQ packs for PLD, AWK, RIVN, MORN, DVN and AQN. They landed on Drive
under `<CIQ root>/<T>/` (the loader's own layout; not the dated-pack tree the
2026-10-28 packs sit in). Everything else is as in 11a: the same scratch data dir and setup, $0,
read-only, nothing committed.

**Boundary**

| | |
|---|---|
| code | main `6e03501f` (#1142), worktree detached there; `vinci.__file__` = the worktree's, printed by every script. Since `9d036cbb`: 13 files changed under `vinci/` (`ev_ebitda_basis`, `anchor_split`, `schemas`, `render`, `refresh`, `theme_intelligence/*`), and nothing under `data/snapshots` |
| exports | 63 files: 11 each for PLD, AWK, RIVN, DVN and AQN, and 8 for MORN. File mtimes run from 2026-11-19 16:23:45Z to 16:48:48Z. Each one was copied to scratch, its sha256 checked equal to the Drive original, and the copies deleted after each name and again at the end (0 left). Drive was read only |
| hashes | the table below, sha256[:10]. They match the precheck's own "exports on disk" line for every name it reached |
| reference date | 2026-10-16 (the fleet's, on the maintenance route). Market panels as of 2026-11-18. Builds assembled 2026-11-19T16:51–16:59Z |
| prices | the 11a scratch store, not refreshed: 16 symbols, 7,914 bars, 2024-11-20 to 2026-11-18; 500 bars for each of the six |
| command | `fresh5a.py` → `build5a.one`: `prespend.run` (the body of `vinci dossier precheck`), then `mechanical_build`, the R4 conditions and the three templates. `variant5a.py` builds the DVN variant and reads the refused packs' inputs |

| name | files | sha256[:10] per workbook |
|---|---|---|
| PLD | 11 | call Q2 `303ac5eb7b` · call Q3 `c755a1e701` · comps `7088bad764` · credit health `f16a9dd1b3` · customers `6b56b2b14b` · estimates `3acc01857d` · fin annual `6e08c8defe` · fin quarterly `d360d90d26` · key devs `ad7462d040` · profile `1aa37d27d5` · suppliers `29dab1fff5` |
| AWK | 11 | call Q2 `a21452cd9e` · call Q3 `023f761abc` · comps `772889c139` · credit health `356e20a45f` · customers `580831478c` · estimates `ed013ff303` · fin annual `b0159b8252` · fin quarterly `c5844ae7d9` · key devs `e52ff76a5f` · profile `37f8bd31cf` · suppliers `2bda7be4dc` |
| RIVN | 11 | call Q2 `9f4e6c3fb4` · call Q3 `e711becf5e` · comps `a6985e24b8` · credit health `76eb3361eb` · customers `1dfa301226` · estimates `ced689eb4b` · fin annual `a710dc0303` · fin quarterly `4835b5b653` · key devs `e61b4bb3ac` · profile `6e4a77bbaa` · suppliers `54df6c5f14` |
| MORN | 8 | comps `0602e34839` · customers `f9b8f04310` · estimates `9219f3d78c` · fin annual `fef17b2405` · fin quarterly `b23ba84d1d` · key devs `298fc15b9d` · profile `e465113df5` · suppliers `d29dcfa3ff` |
| DVN | 11 | call Q2 `91cba31e64` · call Q3 `f6972fc5a9` · comps `095fad00c0` · credit health `0d3bcc2415` · customers `efa021c9ee` · estimates `1c9a07a3bf` · fin annual `78cd82c3d2` · **fin quarterly `78cd82c3d2`** (identical to the annual) · key devs `8233f15325` · profile `1228b5f589` · suppliers `214d50f20f` |
| AQN | 11 | call Q2 `478cd712d1` · call Q3 `2d5cfe1a89` · comps `508f6682b8` · credit health `f09c3d1791` · customers `c196a1ff8c` · estimates `702b5c635d` · fin annual `23292748b8` · fin quarterly `76c40e0928` · key devs `b7c5957e75` · profile `f836c70143` · suppliers `b34dc1c669` |

**Result: 3 of 6 pass the precheck, all with 0 refusals.** None of the three refusals is a timing
refusal. On the three pages that built, and on the DVN variant, the event rule found no 10-Q, 10-K
or 8-K item 2.02 filed after any panel. RIVN and AQN are refused before the rule runs.

| name | archetype | precheck | layers that build | anchor (machine tag) | machine R4 proposal | templates: R1 as tagged · R3, R4 simulated |
|---|---|---|---|---|---|---|
| PLD | G13 REIT | **PASS**, exit 0, 0 post-spend refusals | everything: Financials A+Q, estimates (45 multiples), comps (with Credit Health sheet), industry credit panel (Industrial REITs), 2 calls on file and both read (no unread-call flag), key devs, profile; 92 of 112 Sourced fields present. **No ev_bridge** (D17) | R1, **declines**. No 'Net Rental Exp.' row, so rent is unmeasurable and is treated as material; the ex-lease band then has no current ('Curr. Port. of Leases' reads '-' at 2026-09-30, and EDGAR has no complete operating-lease figure that day). `band_incoherent+lease_basis_unresolved+vendor_bridge`; own-history band of 39 closes | **none**, 2 of 3 met: (1) NTM TEV/EBIT positive; (2) R1 declines, and the EBITDA basis is divergent (consensus-implied D&A over twice the actuals); (3) not met (FY P/E on GAAP EPS, but only 1 of the trailing 4 quarters has material non-operating income; ≥2 is the rule) | R1 REFUSED (the anchor declines) · R3 REFUSED (`applicable` is R1's bit, STATE row 10), though `valuation_basis` marks R3 priceable · R4 REFUSED (no ev_bridge, D17) |
| AWK | G14 utility | **PASS**, exit 0, 0 refusals | everything; 93 of 111 present; industry credit panel (Water Utilities); the comp-set panel is withheld ("scale direction ambiguous"). **No ev_bridge** (D17) | **R1, firm.** Margin 33.8% (EDGAR, 8 FY median); EV/EBITDA band of 39 closes; rent immaterial (<5% of EBITDA), so CIQ's history is kept. Base value *[CIQ value withheld]*, against a $150.13 close (Polygon AWK, 2026-11-18) | **none**, 1 of 3 (NTM TEV/EBIT positive; R1 anchors; FY P/E on an indistinguishable basis) | **R1 TEMPLATE** (base leg filled: revenue, the EDGAR margin, the band's multiple) · **R3 TEMPLATE** · R4 REFUSED (no ev_bridge, D17) |
| MORN | G11 asset mgr / data | **PASS**, exit 0, 0 refusals, with no Credit Health Panel and no calls | Financials A+Q, estimates (24 multiples), comps, key devs, profile, customers/suppliers; 95 of 111 present; **ev_bridge built**. No credit-health score at all (below) and no management commentary (below) | **R1, firm.** Margin 17.4% (EDGAR, 10 FY median); ex-lease EV/EBITDA band of 35 closes (rent material, ≥5% of EBITDA). Base value *[CIQ value withheld]*, against a $237.70 close (Polygon MORN, 2026-11-18) | **none**, 1 of 3 (NTM TEV/EBIT positive; R1 anchors; FY P/E on normalized EPS, 0 of 4 quarters with material non-op) | **R1 TEMPLATE** · **R3 TEMPLATE** · **R4 TEMPLATE**, priceable, bridged on CIQ's TEV |
| RIVN | G03 loss-making | REFUSED, exit 1 (the precheck's own refusal line) | none: refused before any model call, on the same LTM row as the 2026-10-28 pack (D18) | — (no page) | pack inputs: 54 multiples, TEV/REV only, no own-history band (no multiple has ≥4 quarterly closes), so **none is possible** | none possible (no forward EPS or EBIT) |
| DVN | G05 E&P | REFUSED, as a **traceback** (D11) | none: `CiqMislabelledError` at the loader. The file named `…Financials_Quarterly.xls` is byte-identical to the Annual, and its Income Statement, Balance Sheet and Cash Flow each state Period Type 'annual' | — | — | — |
| DVN **re-export** (quarterly re-exported 2026-11-19 17:19Z; the other 10 files unchanged; all 11 sha-checked against Drive; build on main `6e03501f`) | G05 E&P | **REFUSED again**, the same `CiqMislabelledError`, as a traceback (D11) | none. The new file (`b548221592`, 339,466 bytes) differs from the Annual (`78cd82c3d2`, 360,970 bytes), but it is **an annual export again**: its Income Statement and Balance Sheet headers read "Period Type: Annual", and its Income Statement columns are 9 twelve-month periods (Restated FY2018 to FY2025, plus LTM to Sep-30-2026), one year shorter than the Annual file's 10. **Still owed: Financials exported with Period Type set to Quarterly** | — | — | — |
| DVN-noQ (a variant, **not the operator's pack**: the same folder without the mislabelled file) | | **PASS**, exit 0, 0 refusals (D19) | everything except what needs the quarterly: 91 of 111 present; a "pull CIQ 'Financials — Quarterly'" caveat; 8 LTM rows "NOT CHECKED" | `unknown`: own-history multiple missing (the band reads the quarterly export) | **none**, 2 of 3 (NTM TEV/EBIT positive; R1 declines, with consensus D&A divergent; FY P/E on normalized EPS) | all three REFUSED: R1 and R3 on the anchor; R4 for no bridge (no quarterly Balance Sheet) |
| AQN | G17 FPI 40-F | REFUSED, as a **traceback** (D11) | none: `CiqCurrencyError` before any model call, because one money panel states CAD (below). **Refused: home-market primary listing (CAD capitalisation panel); no US listing in CIQ, per the operator** (D21) | — | pack inputs: 42 multiples, a positive NTM TEV/EBIT, an NTM P/E, FY P/E basis undetermined; EV/EBITDA band 35 closes | — |

**Against 11a:**
- **PLD** went from refused (`CiqPreliminaryError`, 10-28 pack) to PASS. CIQ's comps count (950.5M) now supplies the share count that stopped the EDGAR-only page (D6 no longer stops it; EDGAR's cover count is still absent). The page still prices on nothing.
- **AWK and MORN** went from the two export-driven refusals to PASS and a firm R1. They are the first names outside G01 to reach a priced R1 at $0 in this probe.
- **RIVN**: the same refusal, now shown durable.
- **DVN and AQN**: no longer missing an export; each is now refused on a fact about the one it has.

**R3/R4 runs (item 4).** The three pages with a consensus block (PLD, AWK, MORN) get **no machine R4
proposal**: condition 3 fails on all three. The simulated tags hand the analyst:
- **AWK:** R1 and R3 templates;
- **MORN:** R1, R3 and R4 templates;
- **PLD:** nothing. R3 is refused on the row-10 coupling, and R4 is refused for want of a bridge (D17).

As in 11b, no tag was written anywhere.

**MORN — the two checks B asked for**
- **The operator's fact (2026-11-19, relayed by B), verbatim:** "MORN doesn't have earnings transcript and credit health on ciq, they do have typed transcript available on their website". The site named is MORN's own earnings page; it was **not fetched**. So MORN's missing transcripts and Credit Health Panel are **absent at the source** (CIQ carries neither for MORN). They are **not an export gap and not a defect**.
- ~~**Earnings calls: Morningstar holds none, by its own filings.**~~ **Withdrawn.** It overstated what the filings show, and the operator's fact contradicts it: MORN publishes typed transcripts on its site. What the SEC filings do show (`morn5a.py`, `morn5a_ctx.py`):
  - Each quarter MORN files an earnings 8-K (item 2.02, e.g. 0001289419-26-000056 of 2026-10-28). It carries a press release, a CEO letter and a supplement.
  - The press release says Morningstar answers selected investor questions in writing, in 8-Ks furnished monthly except in earnings months. Those 8-Ks (item 7.01, "Investor Questions and Answers") are on file: 2026-05-22, 06-25, 08-25, 09-25 and earlier.
  - EDGAR full-text search, scoped to MORN's CIK, 2023-01-01 to 2026-11-19:
    - "conference call": 0 hits in 8-Ks, 0 in 10-Ks;
    - "earnings conference call": 0;
    - "earnings call": 4 8-K hits, each about PitchBook's transcript *products*;
    - "written responses": 55 8-K hits; "investor questions": 67 (each shows 40 in `morn5a.json`).
  - So the filings announce no call. What the website's transcripts are of was not read here.
- **What the builder reads as a transcript, checked rather than assumed: one source, the name's CIQ manual folder.**
  - Every transcript read goes through `bundle.all_workbooks("transcript")`. That is the bundle built from `data/manual/ciq/<T>/` (`manual_store.LocalFolderStore`). The call sites are `ciq_sheets.py:5502` (the synthesis slice), `:5711` / `:5728` (unread-call checks), `:5758` (`management_commentary`); `assemble.py:819`, `:840`, `:1365`; `driver_pass.py:77`; `transcript_run_pass.py:129`; `confirmation.py:201`; `evals/replay.py:141`.
  - A file counts as a transcript **by its name**: `workbook_kind` matches the stem against `(earnings|conference) call(, <Mon> <d>, <yyyy>)?$` or `transcript$` (`ciq.py:361–362`).
  - **Not `.rtf` only.** The format is sniffed from the header bytes, never the extension (`ciq.classify`). `read_text` decodes real RTF (striprtf), an OLE-disguised `.rtf`/`.doc` (LibreOffice), a MIME doc or HTML (BeautifulSoup), and PDF (pdftotext) (`ciq.read_text`, from `ciq.py:196`).
  - No other transcript source was found:
    - nothing under `vinci/edgar/` or `vinci/eod/` mentions a transcript;
    - searched `transcript` across `vinci/` (the only reader outside the CIQ bundle is the separate theme desk, `theme_intelligence/cards.py`, which does not feed a page);
    - searched `prepared remarks|conference call|earnings call|call_text|investor relations|ir_site|company website`;
    - `git log -i --grep` for `transcript` (66 commits) and for `website|company-published|investor relations|IR page|prepared remarks` — no company-site transcript source.
  - **A consequence for any future use, read from the code, not run:** a company-published transcript would reach the builder only as a file dropped into the CIQ folder under that name rule. `management_commentary` would then label it `source_ref="CIQ transcript(s): …"` (`ciq_sheets.py:5765`), which is wrong provenance. So the source needs its own provenance, not just a file drop.
- **What the absence costs MORN's page** (transcripts are optional, `requirements.py` "Earnings-call transcript", `required=False`; the precheck passes):
  - `management_commentary`: status missing, with the note "no earnings-call transcript … pull it". That is wrong advice where CIQ has none to pull.
  - the paid build's transcript-driver phase and the synthesis's transcript slice, which would have no call to read. This is read from the design, not measured: a $0 build never produces those LLM-fenced rows, and PLD's and AWK's $0 pages have 0 of them too. MORN's 48 operating-driver rows are all anchored rows.
  - nothing stands in for them. The typed website transcripts are not read (above). The page cites none of MORN's 2026 item-7.01 Q&A 8-Ks (0001104659-26-034527, 0001289419-26-000031, -000035, -000044, -000048). The CEO letter is a separate exhibit beside EX-99.1 (its exhibit number was not read here), and the release parser takes EX-99.1, or a bare EX-99, only (`release_parse.py:73–74`). Nothing here works around that: it is a fact for the step-6 G11 notes.
- **What the absent Credit Health Panel costs** (also absent at the source, per the operator). The panel is optional (`requirements.py`, "Credit Health Panel (S&P-MI, industry peers)", `required=False`), and the precheck passes. On MORN, though, the page has **no credit-health score at all**:
  - the industry panel is absent;
  - MORN's comps workbook *also* carries no 'Credit Health Panel' sheet, so `leverage_survival.credit_health` is UNKNOWN ("comps workbook … has no 'Credit Health Panel' sheet").
  The requirement's own text says that without the panel "the page shows the comp-set panel". That holds only when the comps workbook carries that sheet. PLD's comps does. AWK's has it, but its scale direction is ambiguous, so it is not rendered.

**AQN — the stated currency, and the fix**
- **What each panel states.** Read per money panel through `ciq_sheets.stated_currency`, the assembler's own reader:
  - **17 of 18 state USD**: every Financials statement, annual and quarterly; Segments; Capital Structure; Estimates Consensus, Trends, Guidance and Surprise; and Comps ("US Dollar").
  - **One states CAD**: Financials (quarterly)→Historical Capitalization. `require_usd` refuses it; `require_millions` passes.
- **Why.** The sheet's own header (`aqnhc5a.py`) reads "In Millions of the trading currency" and "Currency: Trading Currency", and is titled "(TSX:AQN)". The Income Statement's header reads "the reported currency", and its Currency row reads USD in every column. At Q3 2026 its 'Currency' row reads CAD (Financials_Quarterly `76c40e0928`, Historical Capitalization row 15, column 35 [Q3 Sep-30-2026]), and the same workbook's Income Statement 'Currency' row reads USD (row 15, column 35); both knowable 2026-11-19. Its share price, market cap and TEV are stated in CAD; their values are withheld here.
- **The refusal protects a real reader.** `lease_basis.py:301` reads this sheet's TEV for the ex-lease band. A CAD TEV less USD leases over USD EBITDA would mix currencies.
- **The operator's fact (2026-11-19, relayed by B), verbatim:** "there's no nyse listing as such". CIQ offers no NYSE:AQN export, so **no re-export fixes the CAD panel**. Recorded as a finding (D21), not an operator to-do; the count and the smallest fix are in 11f addendum 3.
- ~~**Would an NYSE-listing export fix it? Very likely yes, but unverified.**~~ *(Withdrawn by the operator's fact above; the original reasoning follows, kept for the record.)* The sheet states its currency as the trading currency of the listing it was exported from, and NYSE:AQN trades in USD. It is unverified because no export on Drive comes from a second listing of the same company: NVO's pack is its Copenhagen line, in DKK on both sides. A second route is the export's own Currency setting (US Dollar instead of Trading Currency), also unverified. The page's prices already come from Polygon's NYSE AQN (USD), so a USD Historical Capitalization would agree with them.

**New defects (§9):**
- **D17:** the R4 bridge needs a cash subtotal that CIQ's REIT and utility templates lack. It selects on form; seen on PLD and AWK; 0 committed pages carry it.
- **D18:** RIVN's refusal is CIQ's FY2025 cell. The filed 10-Qs side with the quarterly export, and no re-export clears it.
- **D19:** a missing required export is a caveat, never a refusal. Seen on the DVN variant.
- **D11** is now observed on `CiqMislabelledError` and `CiqCurrencyError` too.
- One observation, not tested as a defect: MORN's page carries two LTM EBITDAs, 12.49% apart.

Nothing was fixed.

**What this changes for 5b (for B):**
- **A fresh export clears timing; it does not clear these.** Each of the three refusals now needs a different remedy:
  - DVN: ~~an operator re-export of the quarterly Financials. The 17:19Z re-export is an annual export again, so it still needs Period Type set to Quarterly~~ cleared by the 2026-11-20 quarterly re-export (addendum 4);
  - AQN: ~~an export from the NYSE:AQN listing, or with its currency set to USD~~ no export: CIQ has no NYSE:AQN listing (the operator). Code is the remedy (D21);
  - RIVN: code or a ruling (D18). Not an export.
- **PLD passes the precheck and its page prices on nothing.** This is the PCVX case again, so a paid build would write it. That is one more reason the step-6 guard must refuse G13 (REITs) until P/FFO exists, at or before `require_buildable`.
- **R4 on any REIT or utility waits on D17.** R1 on AWK does not.
- **G11: MORN's transcripts and Credit Health are absent at the source, not an export gap.** The page loses its commentary pointer, its transcript inputs to the paid build, and every credit-health score. Its "pull it" note is wrong advice there.
- **For the 5b scope pack, one line:** "company-published transcripts (e.g. MORN's site) are a candidate source; not read by the pipeline today." Any future use falls under the transcript rule: no public field quotes more than 12 consecutive transcript words, and a driver row quotes none. It would also need its own provenance (`management_commentary` labels every transcript "CIQ").
- **Exports still owed (not asked of the operator, per B):**
  - DVN: ~~Financials — Quarterly, **still owed**. The file on Drive was the Annual; the 17:19Z re-export is a second annual export (Period Type: Annual, 12-month columns). Not "none"~~ **none**: the 2026-11-20 re-export is quarterly (addendum 4);
  - AQN: ~~a pack from the NYSE:AQN listing, at least its quarterly Financials~~ none possible (no US listing in CIQ, per the operator). In its place, a substitute G17 test name for the operator to export: **DAC** (11f addendum 3), landed and built 2026-11-20 (addendum 4);
  - RIVN: none would help;
  - MORN: none. CIQ carries neither its transcripts nor its Credit Health Panel (the operator, 2026-11-19).

**Reproduction** (`scripts/archetype_probe/`; outputs regenerate under `<WORK>/out/`):
- `fresh5a.py [T …]`: copy and hash-check, the loader's view and per-panel currency, then the build. Writes `build5a_fresh/<T>.json`, `<T>.dossier.json`, `<T>.inputs.json` and `fresh5a.log`.
- `variant5a.py`: the DVN variant, plus the RIVN, AQN and DVN pack inputs.
- `bs5a.py PLD AWK MORN RIVN`: the balance-sheet cash and debt rows (D17).
- `aqnhc5a.py`: AQN's Historical Capitalization header.
- `morn5a.py` and `morn5a_ctx.py <acc …>`: MORN's filings.
- `rivn5a.py`: RIVN's filed facts (D18).

Each prints `vinci.__file__`, keeps every write in scratch, and deletes its workbook copies in a
`finally`. Cost: $0. 0 LLM calls. Polygon and FINRA: 0 network fetches. No cache file in either
namespace was written after 16:50Z, so each build's 14 Polygon responses and 1 FINRA response were
cache hits. EDGAR (companyfacts, submissions, efts, filing documents) went through the repo's
clients: 289 SEC and 28 efts cache files were written in scratch during this part.

#### 11f addendum 1 (after B's review): MORN's two LTM EBITDAs, tested

**Boundary.**
- MORN's fresh pack, exported and knowable 2026-11-19: Financials Annual `fef17b2405`, Quarterly `b23ba84d1d` (sha256[:10]).
- EDGAR companyfacts for MORN: 10-K 0001289419-26-000013 (FY2025); 10-Qs 0001289419-26-000025, -000041 and -000054 (2026, each carrying its 2025 comparative).
- main `6e03501f`; the live-corpus comparison reads the 26 committed pages there.
- Script `scripts/archetype_probe/mornebitda5b.py`.

| figure | value $M | source layer | what it includes / excludes |
|---|---|---|---|
| A — CIQ annual LTM | 719.4 | Financials Annual→Income Statement, row 80 'EBITDA', column 10 'LTM 12 months Sep-30-2026' (`fef17b2405`) | EBIT (row 82, 616.7) + annual Cash Flow row 20 'Depreciation & Amort., Total' (102.7 = row 18 'Depreciation & Amort.' 28.6 + row 19 'Amort. of Goodwill and Intangibles' 74.1). **Excludes** Cash Flow row 22 'Other Amortization' (102.7) |
| B — CIQ's four quarters | 822.1 | Financials Quarterly→Income Statement, row 82 'EBITDA', columns 36–39 (Q4 2025 to Q3 2026: 187.6 + 206.7 + 207.3 + 220.5) (`b23ba84d1d`) | each quarter = EBIT (row 84) + Income Statement row 26 'Depreciation & Amort.', i.e. **all** D&A, including what the annual export books as 'Other Amortization' (Q3 2026: 167.4 + 53.1 = 220.5) |
| filed | 848.9 | EDGAR `OperatingIncomeLoss` LTM 643.5 (FY2025 526.6 + 9M 2026 483.9 − 9M 2025 367.0) + `DepreciationDepletionAndAmortization` LTM 205.4 (189.9 + 158.3 − 142.8) | the filing's operating income plus all D&A |

**It reconciles exactly.**
- A + 'Other Amortization' = 719.4 + 102.7 = **822.1 = B**.
- FY2025 behaves the same way: EBITDA 593.4 = EBIT 506.2 + Cash Flow D&A total 87.2; Income Statement D&A 189.9 = 87.2 + 102.7. (Same workbook `fef17b2405`, column 9 [12 months Dec-31-2025]: Income Statement rows 80, 82 and 26; Cash Flow rows 20 and 22.)
- CIQ's Income Statement D&A (row 26; FY2025 189.9 at column 9, LTM 205.4 at column 10) equals the filed D&A.
- B against the filed figure (−26.8) is CIQ's EBIT against filed operating income (616.7 vs 643.5). The page's own `ebitda_reconciliation` already explains its quarters: Q4 2025 −19.1 is CIQ's itemised unusual items, and Q2 2026 −6.8 is matched to a sentence in a release.
- What 'Other Amortization' is, the export does not say. MORN tags no FY2025 fact of that size; the only FY2025 fact between $95M and $110M is an unrelated tax line.

**Each consumer, checked:**
- R1's ex-lease band divides B. R1's exit EBITDA is the EDGAR margin × revenue + all D&A. Both add back all D&A, so they are consistent.
- `ev_ebitda_ex_lease_at_price` divides B, consistent with the band.
- `ev_ebitda_basis` reads A. CIQ's headline TEV/LTM EBITDA multiple implies a denominator within 1% of A plus rent ($62.2M, EDGAR `OperatingLeaseCost` + `VariableLeaseCost`, FY2025): the same vendor definition, so it is consistent. (The multiple and TEV are withheld: no recorded cell.)
- The financial summary's LTM 'EBITDA ($M)' prints A.
- The LTM-quarters check flags A against B as DIFFER 12.49%, and states no cause.

**Classification: a definitional difference inside CIQ, used consistently. No consumer reads the
wrong figure for its own arithmetic. But it is not correctly labelled**, in two places:
1. The QA flag gives no cause, though one CIQ row reconciles it to the decimal.
2. `ev_ebitda_basis` calls A "reported LTM EBITDA" (`ev_ebitda_basis._ltm_ebitda`: the financial summary's annual LTM row), while the same page rebuilds the filed figure as 848.9. In this module, "reported" is house usage for CIQ's pre-rent annual figure, not the filing's. On the live corpus (main `6e03501f`; 26 pages, 17 carrying both figures) the annual LTM is within 2% of the filing-rebuilt figure on **7 of 17** (AMZN, BRBR, MCK, NCNO, NFLX, PARR, UBER). It is further on **10 of 17**: BURL 7.1%, CNXC 186.7%, EPAM 7.2%, IT 4.9%, NKE 6.3%, ROST 6.5%, TGT 6.6%, TJX 3.6%, VRRM 44.0%, WLK 71.4%.

Logged as **D20** (class: label; no value is wrong). Not tested further: the same annual-vs-quarters
gap shows on live pages (annual LTM against the four quarters: BRBR −17.2%, WLK +5.7%, CNXC +4.5%,
IT −4.3%), with causes not read.

#### 11f addendum 2: MORN's written Q&A is on EDGAR

The operator's "typed transcript" on MORN's site has an EDGAR counterpart already found in 11f: the
monthly **8-K item 7.01 "Investor Questions and Answers"** exhibits (EX-99.1; e.g.
0001289419-26-000048 of 2026-09-25). **Recorded for the 5b pack as the candidate source:** an
EDGAR read through the repo's own SEC client, not a website fetch.
- It is **not read today.** The page cites none of the 2026 Q&A 8-Ks, and `management_commentary` reads only the CIQ folder's transcripts.
- If it is ever used, it falls under the transcript rule: no public field quotes more than 12 consecutive words, and a driver row quotes none.
- The company-site transcripts stay a second candidate, not fetched.

#### 11f addendum 3: AQN's listing (D21), a substitute G17 test name, and DVN's re-export

**The operator's fact (2026-11-19, relayed by B), verbatim:** "there's no nyse listing as such".
CIQ offers no NYSE:AQN export, so the CAD capitalisation panel cannot be fixed by re-exporting.
It is recorded as a finding, **D21**, not an operator to-do. AQN's cell now reads **"refused:
home-market primary listing (CAD capitalisation panel); no US listing in CIQ, per the operator"**.

**How many G17/G17b names could hit it: not measurable from the data held.** Nothing new was fetched.
- **Population:** the census's G17 + G17b, union of both bands, read 2026-11-19 (the §3 boundary). That is **76** names: 65 in the screen band and 11 in the large-cap band.
- **The primary exchange is not in this data.** EDGAR's `exchanges` field (the submissions extract) lists only US venues and OTC for **all 76; 0 show a non-US venue**. CIQ's primary listing, the one that sets the panel's currency, is not in any input here.
- **Proxies, not counts of affected names** (`scripts/archetype_probe/aqnclass5b.py`):
  - **40-F filers: 7** (AQN, CIGI, DSGX, EPRX, FSV, MGA, SOBO). These file under the Canadian multijurisdictional form, so a TSX primary listing is the likely case for each, but it is not measured.
  - **Incorporated in Canada** (EDGAR `inc_desc`): **7** (AQN, CIGI, CSIQ, DSGX, EPRX, FSV, SOBO). Six overlap the 40-F list. MGA's incorporation field is blank, and CSIQ files a 20-F.
  - **With an ADS line: 13** (ARM, BLTE, DQ, EDU, JOYY, MLCO, NICE, PONY, SE, SIMO, TAL, TIGR, WB). An ADS means the US security is a receipt on shares that may be listed elsewhere, but some trade only in the US.
  - **Incorporation, all 76:** Israel 18 (dual-listing on TASE is common, not measured), blank 14, Cayman Islands 12, Bermuda 8, Marshall Islands 8, Ontario 5, United Kingdom 4, Netherlands 3, and 1 each Greece, British Columbia, British Virgin Islands and Canada (federal).
- **What a count needs:** each name's CIQ primary listing, which CIQ shows on the export's own title line (AQN's read "(TSX:AQN)"). So the first read of any G17 pack should be its title and its Historical Capitalization 'Currency' row, through `ciq_sheets.stated_currency`, as `fresh5a.py` does.

**The smallest fix.** The panel's **only page-path reader** is `lease_basis.observations`
(`lease_basis.py:301`), which takes TEV for the ex-lease band. Other uses: the CIQ quality
scorecard cross-checks it (`quality/sources/ciq.py:404, 782, 786`), and the currency guard lists it
(`ciq_sheets.py:7871`). Searched: `Historical Capitalization`, `Historical Capitalisation`, `hist_cap`,
`historical_cap` across `vinci/`, and `git log -S"Historical Capitalization" -- vinci`.
1. **FX-free, and smaller:** refuse the panel, not the pack. When the panel states a non-USD currency, `lease_basis` refuses its band with that reason, and the rest of the pack is read. Where rent is immaterial, R1 never needed the panel. Where it is material, R1 declines, as PLD's did. Whether AQN's rent is material was not measured, because its pack was refused before the page.
2. **Fuller:** read the panel's own stated currency and convert each column at a dated rate (its 'Pricing as of' date). This **depends on stage 2's FX ruling, SP-R5**: the rate source and the date convention.

**Substitute G17 test name for the operator to export: DAC (Danaos Corp).** Alternate: TK.
Evidence, all from data already held:

| criterion | DAC | TK (alternate) | TEN | NAT |
|---|---|---|---|---|
| 20-F, US GAAP, USD companyfacts | yes: latest 20-F filed 2026-02-27; companyfacts namespaces us-gaap only (309 concepts); reporting currency USD | yes: 20-F 2026-03-13; us-gaap only; USD | yes: 20-F 2026-04-06 | yes: 20-F 2026-04-29 |
| operating income, frames CY2024 / CY2025 ($M) | **540.9 / 498.8**; CY2025 revenue 1,042.5 | 365.2 / 302.8 | 278.6 / 252.3 | 77.3 / 46.3 |
| US primary listing: evidence in hand | EDGAR `exchanges` NYSE only; **no ADS line**; incorporated in the Marshall Islands (no home exchange there); one ticker | NYSE only; no ADS; Bermuda | NYSE; no ADS; Greece; **three tickers** (two preferreds, which add bridge lines) | NYSE; no ADS; incorporation blank |
| census overlap flags | **none** | capex-heavy | none | none |
| 6-Ks in 180 / 365 days (D8: fewer means an export lives longer) | 3 / 5 | 3 / 6 | 1 / 5 | 3 / 6 |
| band, cap | screen, $2.89bn | screen, $1.21bn | screen, $1.54bn | screen, $1.62bn |

**Why DAC:**
- the highest and steadiest operating income of the four;
- no overlap flags;
- a single ordinary line with no ADS and no preferred;
- an incorporation with no home exchange to be primary on.

**What the data cannot show:** that CIQ's primary listing for DAC is NYSE. The first check when the
pack lands: its title should read "(NYSE:DAC)", and its quarterly Historical Capitalization
'Currency' row should read USD. If either fails, TK is next, by the same check. **Done 2026-11-20: both pass** (every sheet titled "Danaos Corporation (NYSE:DAC)"; every money panel USD), so TK is not needed (addendum 4). GILT, a B candidate,
is weaker: 23 6-Ks in 180 days, so its export would last days until D8 is fixed. Its incorporation
field is blank, so a home listing can't be ruled out from this data.

**DVN's quarterly re-export (17:19Z): refused again** (the DVN rows in the 11f table and the G05
grid cell above).
- **Boundary:** main `6e03501f`; the CIQ root's `DVN/` folder, 11 files, each sha-checked equal to Drive. The quarterly is `b548221592` (339,466 bytes, mtime 2026-11-19 17:19Z); the other 10 match their 16:4xZ hashes. Copies were deleted (0 left). Run by `fresh5a.py DVN`; log `archetype-probe/out/5a/fresh/fresh5a_DVN2.log`.
- **Result:** `CiqMislabelledError`, before any model call, as a precheck traceback (D11). The file's Income Statement and Balance Sheet read "Period Type: Annual", and its columns are twelve-month periods from Restated FY2018 to FY2025, plus the LTM to Sep-30-2026.
- ~~**So DVN's exports owed are not "none":** a Financials export with Period Type set to **Quarterly** is still owed. The probe variant (DVN-noQ) remains the only view of DVN's other layers.~~ Superseded by the 2026-11-20 quarterly re-export (addendum 4).

#### 11f addendum 4 (2026-11-20): DVN's quarterly re-export and DAC's pack, built

**Boundary.**
- main **`6c22b222`**, the probe's scripts run against it at $0.
- The CIQ root's `DVN/` and `DAC/` folders were read only; every copy was sha-checked equal to its original and deleted after.
- The scratch data dir is 11a's, plus a follow entry and an `intake` roster line for DAC, and 500 DAC bars (2024-11-20 to 2026-11-18, one Polygon aggs call through `vinci refresh`).
- Reference date 2026-10-16; builds assembled 2026-11-20T06:43–06:47Z. CIQ values are knowable from the export date, 2026-11-20.

**DVN: the refusal clears.**
- **Files:** the quarterly is `a532e1a269` (564,746 bytes, "Period Type: Quarterly", 35 three-month columns); the annual is still `78cd82c3d2`; the other 9 files are unchanged.
- **Precheck: PASS,** exit 0, 0 post-spend refusals. 96 of 111 Sourced fields present.
- **Bands:** the own-history EV/EBITDA band has 33 quarterly closes, and a P/LTM EPS band 26. Rent is immaterial (<5% of EBITDA; EDGAR `LeaseCost` FY2025 $367M), so CIQ's history is kept. The bridge is built.
- **The 8 LTM rows,** "NOT CHECKED" without a quarterly:
  - revenue, EBITDA, EBIT and net income agree with their four quarters;
  - restructuring and merger charges DIFFER, flagged and not refused, since neither is a materiality row;
  - two unusual-item rows reconcile but are UNVERIFIED, because some quarters read '-'.
- **Anchor:** R1 applies, but its value is withheld (W73). The band's newest close is the 2026-09-30 quarter-end, and DVN filed its results 8-K item 2.02 (0001193125-26-449884) on 2026-11-05; an export carrying a close after that filing clears it. That export is optional, not owed. The margin is weak: CIQ's financial summary, since DVN's `OperatingIncomeLoss` has been untagged since FY2016 (D7).
- **Templates:** R1, R3 and R4 all emit. No machine R4 proposal (2 of 3 conditions).

**DAC: the first check passes, and the pack builds.**
- **Files:** quarterly `943da1a0b0`, annual `91d3245a0b`; 11 files in all, each sha-checked.
- **Precheck: PASS,** exit 0, 0 post-spend refusals. NYSE:DAC; every money panel USD (`require_usd` PASS).
- **The 6-K check.** CIQ's newest quarter is Q2 2026, and DAC has filed no Q3 2026 results.
  - A fresh EDGAR submissions read (2026-11-20T06:50Z) lists two filings since 2026-08-01, both 6-Ks:
    - 0001104659-26-089986 (2026-08-04): Q2 results, with interim statements;
    - 0001104659-26-115061 (2026-10-09): a short vessel report incorporated into the F-3, with no results or interim statements.
  - The event rule compares filings against the export-dated panels (`freshness.export_panels`, here dated 2026-11-20) and read 0 events. So the pass is correct, not SP-D8 over-refusal.
- **Diluted count read:** EDGAR `WeightedAverageNumberOfDilutedSharesOutstanding`. DAC furnishes quarterly XBRL on its 6-Ks, so D16 does not bite (NBIS stays the D16 case). The bridge is built.
- **Anchor:** R1 declines (D22). There is no 'Net Rental Exp.' row, so rent is treated as material, and 0 quarters reconcile CIQ's lease rows to EDGAR.
- **Templates:** R1 refused, R3 refused (STATE row 10), R4 TEMPLATE emits.

**Is DAC usable as Order 6's frozen fixture? Yes**, for the 6-K event rule and the US listing and USD panels. It does not test D21 or D16. Its R1 prices only after D22.

**AWK and MORN on main `6c22b222`:** both still pass with 0 refusals, and R1 prices on each as at `6e03501f`. Their bands' newest close (2026-11-18) is after their results filings.

