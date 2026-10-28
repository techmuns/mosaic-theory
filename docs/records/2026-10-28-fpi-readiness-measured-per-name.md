---
status: recorded
date: 2026-10-28
prs: [837]
supersedes:
superseded-by:
---

# What stops the pipeline underwriting a foreign private issuer, measured per name: four tiers, two premises corrected, and a build order

**WHAT.** STATE §5.0 row 4 carried FPI1–FPI5 as one block, to be built "when a foreign filer
lands". This record measures, for every foreign line in three populations, which of those gaps
stand between that line and an underwrite. It sorts the lines into tiers and proposes the build
order. No pipeline code is built here, and #828 (held by the operator) is not touched.

**THE TIERS** (each line's latest annual report, read from the filing's own XBRL instance).

| tier | what it is | primary (262) | of which in the ranked queue (56) | theme band (176) |
|---|---|---:|---:|---:|
| **0** | depositary line whose issuer files 10-K/10-Q: not an FPI at all | 7 | 2 | 1 |
| **1** | 20-F/40-F, US GAAP, USD | 66 | 11 | 11 |
| **2** | 20-F/40-F, US GAAP, not USD | 21 | 3 | 21 |
| **3a** | 20-F/40-F, IFRS, USD | 90 | 25 | 55 |
| **3b** | 20-F/40-F, IFRS, not USD | 74 | 14 | 86 |
| unresolved | the latest annual's instance carries no us-gaap/ifrs-full fact, or none was found | 4 | 1 | 2 |

**Ranked-queue names by tier** (rank in the committed queue):
- **Tier 0 (2):** GPCR 16, DBVT 314.
- **Tier 1 (11):** DQ 30, FVRR 39, PONY 75, CSIQ 113, WB 119, TATT 165, SSYS 205, MLCO 219,
  BRSL 240, LAES 284, RZLV 304.
- **Tier 2 (3):** QFIN 1, JKS 24, HSAI 175. All three report in CNY.
- **Tier 3a (25):** SLI 20, SGML 25, IPX 29, BLDP 49, LAR 51, USAS 60, BTDR 66, BGSI 96,
  BLSH 135, JMIA 138, AAUC 144, GIL 154, EXK 159, GLOB 170, SVM 185, SII 190, ITRG 224, EQX 226,
  GROY 234, BBUC 253, TTAM 264, AGRO 270, POET 292, CRML 294, AG 339.
- **Tier 3b (14):** NAK 35 (CAD), ALM 57 (CAD), NBTX 61 (EUR), LPL 95 (KRW), CYD 106 (CNY),
  ATS 108 (CAD), DNN 127 (CAD), IMTX 131 (EUR), SA 199 (CAD), ABVX 201 (EUR), NXE 236 (CAD),
  STN 238 (CAD), SID 256 (BRL), IVA 318 (EUR).
- **Unresolved (1):** ASM 139. It is a 40-F filer, and its instance (`avino_40f_htm.xml`) carries no
  us-gaap/ifrs-full fact. companyfacts reads it as IFRS through FY2024.

**Every primary line by tier** (the 2026-10-16 population):
- **T0 (7):** AUTL CMPS DBVT GPCR IMCR SLN ZLAB
- **T1 (66):** ALLT AQN ARCO ASC BLTE BORR BRSL BULL CAMT CGNT CIGI CLBT CMRE CSIQ DAC DOX DQ
  DRTS DSGX EDU EPRX FLNG FSV FVRR GILT GLBE GLNG GSL HSHP INMD ITRN JOYY KRNT LAES MLCO MNDY NAT
  NICE NMM NTB NVGS ODD PERI PLGO PONY RDWR RSKD RZLV SB SBLK SFL SHIP SIMO SMWB SOBO SSYS TAL TATT
  TEN TIGR TK TNK VTEX WB WIX XNDU
- **T2 (21):** ATAT ATHM BILI BZ FINV GDS HSAI IQ JKS KC LI MOMO NIO QFIN RERE RLX TJGC VIPS VNET
  XPEV YMM
- **T3a (90):** AAUC AG AGRO ALVO AMBP ARIS BBUC BEP BEPC BGSI BIPC BLDP BLSH BLX BTDR BTG BVN BWLP
  CAAP CMBT CMCL CPA CRML DHT DLO ECO EFXT EGO ELE ENLT EQX ERO EXK FSM GAU GHRS GIL GLOB GPRK GROY
  GSM HAFN HBM HELP HIMX ICL IHS IPX ITRG JMIA KLAR KYIV LAR LEGN LSPD MEOH MESO MMYT MRX MTA NEWP
  NEXA NEXN OPRA OR PAM PAX POET PRE SCZM SGHC SGML SII SLI SOPH SQM STNG SVM TFII TFPM TLX TRMD TTAM
  USAS VEON VIST VLRS VZLA WFG ZIM
- **T3b (74):** ABVX AFYA ALM ASR ASTL ATS BBAR BIRK BMA BSBR BTE CAE CEPU CIG CYD DNN DOO DRD DRUG
  GFR GGAL GGB GOOS GRFS HSLV IFS IMOS IMTX INTR IVA KARO KOF KT LKFT LPL MANU MNSO NAK NBTX NOMD
  NXE OBE OGG OMAB PAC PAGS PDS PHI PHVS RNW SA SBSW SID SKE SRAD STN STNE STVN SUPV TAC TBBB TEO
  TGB TGS TIMB TKC TME TSAT TV UGP VET WPP WRD ZGN
- **Unresolved (4):** AUGO and BTQ (no XBRL instance in the annual filing's index); ASM and CGAU
  (an instance with no us-gaap/ifrs-full fact).

**Theme band by tier** (the 2026-08-24 snapshot):
- **T0 (1):** ONC.
- **T1 (11):** AER ARM CHKP ESLT ICLR MGA NBIS NVMI SE STM TSEM.
- **T2 (21):** ASML BABA BEKE BIDU EMA FTS FUTU HDB HTHT IX JD LI MFG MUFG NIO NMR NTES PDD TCOM
  TRP ZTO.
- **T3a (55)** includes TTE, SHEL, HSBC, NVS, RIO, BHP, BP, UBS and VALE.
- **T3b (86)** includes TSM (TWD), NVO (DKK), SAP (EUR), TM and SONY (JPY), ASND (EUR), and
  RY and TD (CAD).
- **Unresolved (2):** IBN and CNI.
- ASML is Tier 2: it files US GAAP in EUR.

**THE GAPS, MAPPED.** Each tier inherits the gaps of the tiers above it.

| gap | what it is today | who it blocks |
|---|---|---|
| **FPI4** ADS ratio | Nothing converts a per-ordinary-share figure to the per-ADS price. The universe sizes ADRs on Polygon's ADS-denominated count (#541), so caps are right; per-share bridges are not. | every depositary line, Tier 0 included |
| **FPI1a** 20-F/40-F as the annual report | The dossier's annual readers ask for a 10-K. Segment profit (`mechanical.py:2091`), material contracts (`:3627`), debt maturities (`:3779`), SBC (`:2564–2565`), `graph/filings.py:162`; the primary-source pass reads the latest 10-Q's sections (`:4692`). | Tiers 1–3 |
| **FPI1b** non-USD facts | `concepts.extract_points` returns every unit under one concept. On QFIN, `latest_annual` of revenue is **CNY 19,205,059,000**, served beside USD convenience-translation facts. Only some consumers filter to USD (`net_debt.py`, `statement_recon.py`, SBC). | Tiers 2 and 3b |
| **FPI1c** IFRS | `concepts._NAMESPACES = ("dei", "us-gaap")`. No `ifrs-full` reader exists outside the theme altitude (searched for `ifrs` case-insensitively across `vinci/`, and `git log -S'ifrs-full' -- vinci`). | Tier 3 |
| **FPI2** 6-K | The dossier's event readers are 8-K-only (`mechanical.py:362, 3237, 3363, 3425, 3577, 4662`). So is the structural scan (`rank/structural.py:181`), whose `[]` is defined as "a real, clean result", which for an FPI is a result never looked for. The ranker's de-rating triage already reads 6-K (`triage.FORMS`, #515). | Tiers 1–3 |
| **FPI3** Section 16 | **The premise changed; see below.** | exempt-jurisdiction FPIs |
| **FPI5** foreign-currency CIQ | `require_usd` refuses before assembly. **No line in any of the three populations has a CIQ export** in the assembler's copy (35 folders). The one foreign-currency export there, ONON (CHF), is in neither snapshot. | nobody yet |

**PER-GAP MEASUREMENTS.**

- **Form.**
  - **Primary:** 192 lines' latest annual report is a 20-F, 63 a 40-F and 7 a 10-K.
  - **Theme band:** 136 are a 20-F, 39 a 40-F and 1 a 10-K.
- **Reporting currency** (the modal iso4217 unit of the instance's monetary facts).
  - **Primary, 255 20-F/40-F filers:** USD 156, CNY 24, CAD 23, EUR 12, BRL 10, ARS 7, MXN 6,
    ZAR 3, GBP 2, KRW 2, six others 1 each, unread 4.
  - **Theme band, 175 filers:** USD 66, EUR 24, CAD 21, CNY 11, JPY 9, GBP 9, KRW 6, BRL 6,
    TWD 4, INR 3, the rest 2 or fewer each.
  - **Cross-check:** companyfacts' modal unit for the same accession never disagrees with the
    instance's, where companyfacts carries the accession.
  - **USD convenience translations.** Many CNY reporters also tag USD facts, as a single
    period-end convenience translation of the latest year:
    - QFIN: 10 of companyfacts' 38 revenue facts are USD.
    - JKS: CNY 1,850 against USD 210 of the instance's monetary facts.
    - **A convenience translation is not an FX policy.** It is one rate applied to one year.
- **Basis, and companyfacts' coverage of it.**
  - **The finding.** companyfacts does **not** carry the latest annual's facts for 61 of 164
    primary IFRS filers and 38 of 141 theme IFRS filers. For SQM, KT, IPX, ATS and CYD its
    newest `ifrs-full` annual facts are a year older than the filing. It does carry them for 86
    of 87 primary US GAAP filers (DOX is the exception).
  - **The cause is not established, and it is not the taxonomy version.** 56 of 145 instances
    on the 2025-03-27 IFRS taxonomy are missing, against 5 of 19 on 2024-03-27.
  - **Consequence for FPI1c:** an IFRS reader built on companyfacts would serve last year's
    numbers as current for about a third of Tier 3. It must read the filing's own instance, as
    MC2 does for segment profit.
  - **Queue names affected:** IPX, BTDR, LPL, CYD, ATS, SVM, SID, AGRO, CRML and IVA.
- **ADS ratio (FPI4).**
  - **Where it is read.** Every depositary title on the latest periodic cover is read, not only
    the row the symbol is tagged to. HSBC, SAP and WPP tag their symbol on the ordinary-share row;
    TSM and ASML list only their common shares.
  - **Fallback.** Where no title states a ratio, anchored patterns over the filing's text are
    used.
  - **Rule.** A ratio is known only when exactly one value is stated.
  - **Primary:** **81 of 85** depositary-typed lines are known: 57 from a 12(b) title, 24 from the
    filing text.
    - 55 have a ratio other than 1, from 0.2 to 25.
    - Unknown: BMA, GGB and TV. Ambiguous (states 1 and 0.5): GRFS.
  - **Theme:** 94 of 105 are known.
    - Unknown: ASML, ASX, DEO, E, HMY, ING, PBR and WDS.
    - Ambiguous: BIDU, FMS and TCOM. BIDU's and TCOM's filings state both their current ratios
      and the ratios they replaced.
  - **Queue:** all **16** depositary lines are known.
    - Ratios: QFIN 2, GPCR 3, JKS 4, IPX 10, DQ 5, LPL 0.5, JMIA 2, MLCO 3, DBVT 5.
    - Ratio 1: NBTX, PONY, WB, HSAI, ABVX, SID and IVA.
  - **Polygon's type is right in every case checked.** No CS-typed primary line's cover
    registers ADSs. In the theme band, ASND is typed CS and trades as an ADS at 1:1, so its
    EDGAR-count size stands.
- **Interim results (FPI2).**
  - **Window:** 6-Ks filed in the 183 days to 2026-10-16, newest first, up to 40 per issuer.
  - **Test:** an exhibit or 6-K body that names revenue, a profit line and an interim period, and
    carries ≥20 thousands-grouped numbers.
  - **Result:** found for **246 of 255** primary filers and 169 of 175 theme filers.
  - **Not found:**
    - Primary: BLTE, BVN, DRD, IMOS, IPX, OMAB, SGHC, TJGC, VIST.
    - Theme: DB, ESLT, HMY, NOK, NVS; HSBC's 113 6-Ks were cut at the 40 examined.
  - **The numbers are rarely machine-readable.** Only **33 of 255** primary filers (28 of 175
    theme) furnished a 6-K whose XBRL carries a 3-to-9-month duration fact in companyfacts in
    the 365 days to 2026-10-16. Queue names among them: ABVX, AGRO, ASM, CRML, IPX, SLI, SSYS,
    TATT, USAS.
  - **So interim and trailing figures come from CIQ or a 6-K release parser.**
- **Section 16 (FPI3): THE PREMISE IS OUT OF DATE.**
  - **What row 4 assumed:** "the insider signal is empty… for FPIs forever".
  - **The statute changed.** The Holding Foreign Insiders Accountable Act (enacted 2025-12-18,
    effective **2026-03-18**) brought FPI directors and officers under Section 16(a). 10% holders
    are not covered, and 16(b) still does not apply.
  - **One exemption.** An SEC order of 2026-03-05 exempts insiders who report under the Canadian
    (SEDI, NI 55-104), Chilean, EEA, Korean, Swiss or UK regimes.
  - **The filings show it.** Across the 419 20-F/40-F issuers measured, 208 filed their first
    Form 3 (read over each issuer's whole filing index) in March 2026, and there were 3,181
    Form 3s in that month alone (filings read back to 2025-01-01).
  - **Primary filers since 2026-03-18:** **170 of 192** 20-F filers and **2 of 63** 40-F
    filers (Canadian, exempt) have filed Forms 3/4/5. In the queue: 25 of 33 20-F filers and 0 of
    21 40-F filers.
  - **Theme band:** 83 of 136 20-F filers and 4 of 39 40-F filers. The 20-F filers with none are
    mostly from exempt regimes: ASML, SAP, NVO, BP, SHEL, KB, KT, SQM, NVS, UBS.
  - **What FPI3 now is:**
    - the insider scan's 2-year window (`mechanical.py:2802`) must state that an FPI's insiders
      report only from 2026-03-18, because absence before that date is not "no activity";
    - insiders under an exempt regime need an explicit "reports abroad" state, not "no Form 4
      filings".
- **The screen reads foreign EPS.** Measured, reported, not fixed.
  - **What the screen does.** Its G3 P/E (`screens/assemble.py:302`) divides the USD price per
    ADS by whatever annual diluted EPS `annual_eps_point_as_of` picks.
  - **QFIN:** that is **CNY 22.01 per ordinary share**, so the screened P/E is 5.67 / 22.01 =
    **0.258×**. Per ADS in USD it is 5.67 / (2 × 3.15) = 0.90×.
  - **The level is not persisted.** The screen run and the queue carry only the percentile.
  - **The percentile is consistent for most lines.** For 86 of the 89 foreign lines with an EPS
    pick, the 1,825-day history picks one unit throughout. A constant currency and ratio cancel
    in a percentile, so they distort it only through FX drift.
  - **Three histories switch unit, and their percentile is corrupt:** JOYY (primary, CNY↔USD);
    FUTU and NBIS (theme). None is in the queue.
  - **Non-USD picks** (re-measured on the 2026-10-28 companyfacts fetches; no pick changed from
    the first pass): 14 primary lines read a CNY EPS, QFIN (1) and HSAI (175) among them.
    17 theme lines read a CNY, JPY, CAD or EUR EPS.

**GPCR, FOR #828 (reported, not acted on).**
- **The type branch catches 7 non-FPIs.** #828 excludes a line when Polygon types it
  `ADRC`/`GDR`/`OS` *or* its latest periodic report is a 20-F/40-F.
- **They are domestic filers.** All 7 `ADRC` lines whose issuer files 10-K/10-Q are US GAAP and
  USD, file Forms 3/4 under Section 16 like any domestic issuer, and have a cover-stated ADS
  ratio:
  - GPCR 3 (rank 16);
  - DBVT 5 (rank 314);
  - AUTL 1, CMPS 1, IMCR 1, SLN 3, ZLAB 10.
- **Structure Therapeutics (GPCR)** filed its latest 10-Q on 2026-08-06 and 32 Forms 3/4/5 in
  the year to 2026-10-16.
- **The pipeline reads every one of them today.** Their only gap is FPI4, for a per-share bridge.
- **A rule by filing form alone** (20-F/40-F) would keep all 7. That moves #828's 262 to 255,
  the measurement row 33 started from.

**PROPOSED BUILD ORDER** (cheapest first; each step names what it unlocks, cumulatively, in the
ranked queue).

1. **FPI4, ADS ratio per depositary line.**
   - **The build:** read every depositary 12(b) title on the latest periodic cover, then the
     anchored filing-text patterns. Require exactly one value, else **REFUSE**. Store the ratio
     with its accession.
   - **Unlocks:** per-share bridges on 81 of 85 primary depositary lines and on the 2 Tier 0
     queue names (GPCR, DBVT). **2 queue names underwritable**: Tier 0 then needs nothing a
     domestic name does not.
   - **Cost:** small. The cover reader exists (`resolver/instrument.py`); the measurement code
     shows the patterns and their two fraction traps (SMFG "3/5 of one share", KT "one-half of
     one share").
2. **FPI1a with a unit guard: a 20-F/40-F is an annual report, and a non-USD fact is never read
   as dollars.**
   - **The build:** open the 10-K-only gates listed above. Make every `extract_points` consumer
     that expects dollars refuse a non-USD unit rather than take `latest_annual`'s pick. The
     guard must land in the same PR, because opening the gates without it serves QFIN's
     CNY 19.2bn as $19.2bn.
   - **Unlocks:** Tier 1 annual EDGAR blocks, 66 primary names (11 in the queue).
3. **FPI3 restated: insider scan windowed and labelled.**
   - **The build:** start an FPI's window at 2026-03-18, and give exempt-regime insiders a
     "reports under <regime>" state.
   - **Cost:** cheap, and independent of 1–2.
4. **FPI2, 6-K at the dossier and structural-scan altitudes.**
   - **The build:** 6-Ks as unclassified events. A 6-K carries no item code, so it is
     read-required, the same as triage. The structural scan should read 6-K, so an FPI's empty
     8-K list stops reading as clean.
   - **Interim numbers:** from 6-K XBRL where furnished (33 names), else CIQ.
   - **Unlocks:** with 1–3 and a USD CIQ export, **Tier 1 is underwritable: 13 queue names**
     cumulative (Tier 0 + Tier 1).
5. **FPI1c, IFRS from the filing's own instance**, with an `ifrs-full` alias map. Not from
   companyfacts (the 61-of-164 gap above).
   - **Unlocks:** Tier 3a, 90 primary names (25 in the queue). **38 queue names** cumulative.
6. **FPI1b, an FX policy. An OPERATOR RULING comes first** (which rate, which date, spot or
   period average, and how a reported-currency figure is shown).
   - **Unlocks:** Tiers 2 and 3b, 95 primary names (17 in the queue). **55 of 56 queue names**
     cumulative; ASM stays unresolved.

**FPI5 may need no build, but that is UNVERIFIED.** The operator can export Tier 1–3 workbooks
in USD (CIQ converts), and `require_usd` passes them. No foreign filer's USD export has yet been
run through the parser, so the first one is a pilot: it must assemble on a real page before this
is believed (off-December fiscal years are MC4's, and IFRS line labels are untested). A native-currency reader is worth building only after
step 6's ruling, and only if native exports are wanted.

**Not reached by #828's words, and not by any tier.** OGC, GORO, AYA and MDA have filed no
periodic report. Each has furnished an interim-results 6-K in the window. Their first annual
report tiers them.

**HOW VERIFIED.**
- **Recount, reproduced exactly.** 262 = 85 `ADRC` + 114 20-F + 63 40-F (#828's split); 56
  queue names; 10 in the top 50.
  - Types come from the 2026-10-17 Polygon reference pull in the 2026-10-16 replay cache, with
    the network refused.
  - The 85 `ADRC` lines are exactly the 85 rows the committed snapshot sized "ADS-denominated".
- **Every per-name value is read from a real SEC document:**
  - submissions indexes (older pages walked where needed);
  - companyfacts, fetched 2026-10-28;
  - each latest annual's XBRL instance;
  - each latest periodic cover;
  - 6-K filing indexes and exhibits.
- **Fetches.** About 6,300 live fetches, written only to this session's scratch cache. Reads hit
  the replay cache where it held the document; nothing in the primary checkout or the replay
  worktree was written.
- **Two parser errors were caught and fixed before any number here was taken.**
  - **The first cut read currency from the `Assets` unit.** It returned USD for QFIN, whose
    Assets carry a USD convenience translation, which would have put QFIN in Tier 1.
  - **The first ratio patterns read fractions as counts.** SMFG's "3/5 of one share" came out
    as 3 and KT's "one-half of one share" as 1.
  - **Ratios checked by hand against known values:** TSM 5, BABA 8, JD 2, PDD 4, TM 10, HMC 3,
    BP 6, SHEL 2, HSBC 5, HDB 3, UMC 5, NTES 5, MFG 2, SMFG 0.6, KT 0.5, LPL 0.5, QFIN 2, GPCR 3.
- **The 6-K test, sampled.** Of 8 accepted documents drawn at random, 7 are interim results or
  interim statements. One (NTB) is a bank's Pillar 3 capital disclosure: period-labelled, with
  income figures, but not a results release. The issuer-level answer still holds, because
  Butterfield furnishes quarterly results. **A "found" can therefore be a near-miss document; a
  "not found" means not found under this test, not that none exists.**
- **The Section-16 statute and order** were checked against law-firm summaries of the HFIAA and
  of the SEC's 2026-03-05 order. The order's own text was not read; its jurisdiction list should
  be checked against it before step 3 is built.
- **Scripts:** session scratchpad, `stage1_populations.py` → `stage5_final.py`. Not committed;
  this PR carries only the record and the STATE row.

**BOUNDARY.**
- **Primary population:** the committed `data/snapshots/universe_snapshot.jsonl` (2,065 lines,
  as of 2026-10-16).
- **Ranked queue:** the committed `ranked_queue.jsonl` (343 names, run 2026-10-16-01).
- **Theme band:** the committed `theme_universe_snapshot.jsonl` (928 lines, as of 2026-08-24).
- **The FPI rule:** #828's, applied to filings on or before **2026-10-16**. It is applied to the
  theme band with the same cutoff, not that snapshot's own date.
- **Polygon types:** the 2026-10-17 reference pull.
- **Per-name reads, all filed on or before 2026-10-16:**
  - the latest 10-K/20-F/40-F/10-KT and its instance (up to four instance files per filing);
  - companyfacts as fetched 2026-10-28;
  - the newest of up to three periodic covers.
- **Windows:**
  - 6-Ks: 183 days to 2026-10-16, up to 40 per issuer.
  - 6-K XBRL interim facts: filed in the 365 days to 2026-10-16, duration 80–280 days.
  - Section-16 filings: Forms 3/4/5 and their amendments, filed 2026-03-18 to 2026-10-16. The
    month histogram runs from 2025-01-01.
  - The screen's EPS-unit history: weekly, over 1,825 days to 2026-10-16.
- **Units:**
  - Tier counts are LINES. The 419 in the Section-16 histogram are ISSUERS.
  - Ratios are ordinary shares per ADS.
- **Code** cited at `1114490b`.
- **The measured inputs did not change** between `89d37d23`, where they were read, and
  `1114490b`: the three snapshots, `edgar/concepts.py` and `screens/assemble.py`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The tiers come from each filing's own instance, not companyfacts.** The brief asked for
   companyfacts. The two never disagree on currency where both exist, but companyfacts lacks the
   latest IFRS year for about a third of Tier 3, so it could not tier those names.
   FALSIFIER: a name whose companyfacts basis or currency, once it carries the year, differs from
   the instance's.
2. **The 6-K test is an anchored proxy (see the sample).** It can accept a period-labelled
   non-results document. The build of step 4 must not reuse it as a classifier.
3. **The cause of companyfacts' missing IFRS year is not established.** Step 5 avoids depending
   on it, by reading the instance.
4. **The screen's EPS defect is reported, not fixed.** Its persisted percentile is wrong only on
   JOYY, FUTU and NBIS, and none is in the queue. Step 2's unit guard is where the level gets its
   fix; the screen's series should take one unit per issuer, which is a decision-path change
   owing its own shown run.
