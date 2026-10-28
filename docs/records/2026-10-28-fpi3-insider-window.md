---
status: shipped
date: 2026-10-28
prs: [841]
supersedes:
superseded-by:
---

# FPI3: a foreign private issuer's insider window starts 2026-03-18 and says so, and one whose insiders report under an SEC-exempted regime reads "Reports abroad (SEC order N)"; 27 of 27 domestic pages unchanged

**WHAT.** The dossier's insider block (`mechanical._insider_activity`) now reads a foreign
private issuer on its own window. Domestic filers are read exactly as before. "Foreign private
issuer" means the latest annual report filed on or before the reference date is a 20-F or 40-F,
which is #837's rule.
- **Window.** An FPI's Forms 3/4/5 are read only from **2026-03-18**, the day the Holding Foreign
  Insiders Accountable Act brought its directors and officers under Section 16(a). They are read
  up to the reference date and no later.
  - The 182-day count window is cut at 2026-03-18 when it would reach past it, and then reads
    "in the last 44 days, since 2026-03-18".
  - An absence reads "no sale since 2026-03-18", never "no sale in the 3y scanned".
  - The line names the annual report that makes the issuer an FPI, and counts what was filed:
    "filed since: 12 Form 3, 7 Form 4".
  - A Form 3 shows an insider registered here. That separates "registered, no trades" (SSYS,
    SID) from "files abroad".
- **Reports abroad.** An FPI incorporated in a jurisdiction on an SEC exemptive order, that has
  filed no Form 3/4/5 since 2026-03-18, reads `Reports abroad (SEC order <release>)`.
  - The line names the jurisdiction and where it was read, and the regulation the insiders may
    report under instead.
  - It states the window, and the one order condition SEC data cannot show.
  - It is PRESENT and source-bound to the release, the incorporation code and the empty filing
    index.
- **No order, no filings.** An FPI in such a jurisdiction is UNKNOWN with its window and the
  reason, for example "incorporated in Cayman Islands …, which no SEC exemptive order covers".
  It is never "no insider activity".
- **Files here, jurisdiction unread.** An FPI whose jurisdiction is neither recorded in EDGAR
  nor tagged on its cover is read, and the line says "whether an SEC exemptive order lets its
  insiders report abroad is unread", because an order could make its counts partial (IBN).
- **Files here and on an order.** An FPI in an order's jurisdiction whose insiders do file here
  is READ. The order is named beside the counts: "its directors and officers may report under
  EU MAR instead (SEC order 34-104931), so these counts can be partial".
- **Domestic filers: unchanged**, byte for byte. Shown on 27 of 27 committed dossiers and on the
  two 10-K depositary lines in the queue.
- **Screens and ranker: nothing to change.** No screen or ranker signal reads insider activity
  (see HOW VERIFIED), so the window had no gate to reach.

**THE ORDERS** (read at sec.gov 2026-10-28; the Division's HFIAA page, last updated 2026-05-20,
lists these two and no other).
- **34-104931, 2026-03-05:** Canada (NI 55-104), Chile, the EEA (EU MAR; the order's fn. 8: the
  27 EU states plus Iceland, Liechtenstein, Norway), Korea, Switzerland (SIX Listing Rules), the
  UK (UK MAR).
- **34-105517, 2026-05-20:** Australia (Corporations Act s205G, **directors only**), India (SEBI
  insider-trading regulations), Singapore (SFA Part 7, **directors and the chief executive**).
  - Under this order the rest of an issuer's officers still file Forms 3/4, and the line says so.
  - Before 2026-05-20 these three jurisdictions are on no order, and the line says the order
    takes effect later.
- **Eligibility, as both orders state it:** the directors and officers of an FPI that is
  (i) incorporated or organized in a qualifying jurisdiction and (ii) subject to a qualifying
  regulation, provided they report under it. An insider outside the regulation's covered
  category still files (March fn. 10; May fn. 4).
- #837's session verified the same list independently (its round 1, `6613fa18`).

**THE RULE THAT PICKS THE STATE, stated once.** The FILINGS decide; incorporation only names the
order.
1. **Jurisdiction.** It comes from EDGAR's `stateOfIncorporation` code. Where EDGAR leaves it
   blank, it comes from the annual report's own cover tag `dei:EntityIncorporationStateCountryCode`.
   Never from the business address: #837 measured that proxy wrong on CYD and JOYY.
   - **A cover shows a NAME, not a code.** The tag carries the `ixt-sec:edgarprovcountryen`
     transform. All six queue covers with a blank EDGAR code carry a name, and AGRO's is "Grand
     Duchy of Luxembourg", which is not EDGAR's table name.
   - **Names are matched by EDGAR's own grammar for that transform.** It is transcribed for the
     qualifying codes from `edgarProvCountryNamePattern` in the Arelle/EDGAR renderer plugin.
     Matching is full-string, never substring: "Northern Ireland" must not read as Ireland, and
     "Netherlands Antilles" must not read as the Netherlands.
2. **Code to regime.** `REGIMES` maps 50 codes: 12 Canadian, 30 EEA, and CL, KR, CH, UK, AU, IN
   and SG. Every code is pinned against EDGAR's own state-and-country table, frozen from sec.gov.
   Jersey, Guernsey, the Isle of Man and Gibraltar are not the UK, and are absent.
3. **Filings.**
   - Any Form 3/4/5 filed 2026-03-18 to the reference date: the line is read. The order is named
     if the issuer's regime is in force.
   - None, and a regime in force: "Reports abroad".
   - None, and no regime: UNKNOWN with the window and the reason.
- **Why the filings decide.** Incorporation is condition (i) only. Whether the issuer is subject
  to the regulation (condition ii; for EU or UK MAR, a listing on an EEA or UK venue) is not
  recorded anywhere in EDGAR.
  - #837 counted 23 primary issuers in a March-order jurisdiction whose insiders file Forms 3/4
    anyway; in the queue these include IMTX, JMIA, GLOB, BRSL and TTAM.
  - Reading incorporation alone would have hidden their filings behind "Reports abroad".

**THE REAL RUN, before (origin/main `1114490b`) → after (this branch), per name.** Both versions
ran in one process on one document set. The second, sequential pass made **zero** new fetches
(11,752 cached documents before and after), so the two read identical documents.

*The 56 foreign lines in the ranked queue (#837's per-name list), by transition (rank in the
queue):*

| before | after | n | names |
|---|---|--:|---|
| UNKNOWN "no Form 4 filings in the 3y scanned" | **Reports abroad (34-104931)** | 27 | SLI 20, SGML 25, NAK 35, BLDP 49, LAR 51, ALM 57, USAS 60, NBTX 61, LPL 95, BGSI 96, ATS 108, DNN 127, ASM 139, AAUC 144, GIL 154, EXK 159, SVM 185, SA 199, ABVX 201, ITRG 224, EQX 226, GROY 234, NXE 236, STN 238, POET 292, IVA 318, AG 339 |
| PRESENT, Form 4 over 3y | **Reports abroad (34-104931)** | 1 | SII 190: one Form 4 in 2024, none since 2026-03-18 |
| PRESENT, Form 4 over 3y | **read from 2026-03-18** | 14 | QFIN 1, JKS 24, FVRR 39, BTDR 66, PONY 75, CYD 106, WB 119, BLSH 135, TATT 165, HSAI 175, MLCO 219, BBUC 253, LAES 284, CRML 294 |
| PRESENT, Form 4 over 3y | **read from 2026-03-18, order named** | 9 | IPX 29 (34-105517, directors only), CSIQ 113, IMTX 131, JMIA 138, GLOB 170, BRSL 240, TTAM 264, AGRO 270, RZLV 304 (34-104931) |
| UNKNOWN "no Form 4 filings in the 3y scanned" | **read from 2026-03-18** | 2 | SSYS 205, SID 256: Forms 3 only (10 and 14), so registered here with no trades |
| UNKNOWN "no Form 4 filings in the 3y scanned" | **UNKNOWN: no Form 3/4/5 since 2026-03-18, on no order** | 1 | DQ 30 (Cayman Islands) |
| PRESENT, Form 4 over 3y | **unchanged (10-K filer)** | 2 | GPCR 16, DBVT 314 |

- **Counts by state, after.** Of the 54 FPIs:
  - 28 read "Reports abroad";
  - 25 are read from 2026-03-18, 9 of them with an order named;
  - 1 (DQ) is UNKNOWN with its window.
  - The 2 depositary lines that file a 10-K (GPCR, DBVT) are unchanged.
- **What the old line got wrong.**
  - 24 of the 54 FPIs had a PRESENT old line, and 20 of those claimed an absence over "the 3y
    scanned" (IPX: "no sale in the 3y scanned").
  - The other 30 read UNKNOWN "no Form 4 filings in the 3y scanned". Of those, 27 report abroad,
    2 file Forms 3 here, and 1 (DQ) files nothing.
- **Cross-check against #837's per-order count.** #837 counted the queue's 54 20-F/40-F names:
  - **March-order jurisdiction:** 36 (8 file, 28 do not). #837 had 35 (8 and 27), with BLDP's
    jurisdiction unread; its 40-F cover reads "British Columbia, Canada".
  - **May-order jurisdiction:** IPX alone, and it files. Same as #837.
  - **Neither:** 17 (16 file; DQ does not). #837 had 18 with BLDP.
  - **The other five blank-EDGAR names read from their covers:** ASM and STN ("Canada"),
    AGRO ("Grand Duchy of Luxembourg"), CYD ("Bermuda"), TATT ("Israel").
- **The 27 committed dossiers, all 10-K filers: 27 of 27 byte-identical,** status, value, note
  and source_ref.
  - Names: AMZN, AORT, BRBR, BURL, CNXC, EPAM, FUBO, GOOGL, IT, LLY, MVST, NCNO, NFLX, NKE,
    ORKA, PARR, ROST, SMPL, TECX, TGT, TJX, UBER, V, VITL, VRRM, WERN, WLK.
  - The first, parallel pass showed GOOGL different: 462 against 464 grants, over the same 511
    filings. A few Form 4 documents had failed to fetch under load during the "before" call and
    were dropped silently. On the warm pass the two are identical (see FOLLOW-UPS, item 2).
- **Invariants over the 54 FPIs, after:**
  - every one of the 53 PRESENT values states "in the last N days", which is what the renderer
    reads to drop the stale "6m" from the label;
  - none says "scanned";
  - none says "no insider activity".

**Three real lines.**
- **SLI**, before: UNKNOWN "no Form 4 filings in the 3y scanned". After: "Reports abroad (SEC
  order 34-104931) — incorporated in Canada (EDGAR state of incorporation), so its directors and
  officers may report under NI 55-104 instead of Forms 3/4/5 · none filed with the SEC in the
  last 224 days, since 2026-03-18 when Section 16(a) reached this foreign private issuer's
  insiders (HFIAA) · the order also requires the issuer to be subject to NI 55-104, which SEC
  data does not show".
- **IPX**, before: "… · no sale in the 3y scanned · …". After: "… · no sale since 2026-03-18 · …
  · foreign private issuer (20-F filed 2026-09-29): … filed since: 10 Form 3, 19 Form 4;
  incorporated in Australia (EDGAR state of incorporation): its directors may report under
  Corporations Act s205G instead from 2026-05-20 (SEC order 34-105517), so these counts can be
  partial; its other officers still file Forms 3/4 · other M×1".
- **DQ**, before: UNKNOWN "no Form 4 filings in the 3y scanned". After: UNKNOWN "foreign private
  issuer (20-F filed 2026-04-20): no Form 3/4/5 filed in the last 224 days, since 2026-03-18 when
  Section 16(a) reached its insiders (HFIAA) — incorporated in Cayman Islands (EDGAR state of
  incorporation), which no SEC exemptive order covers (34-104931, 34-105517)".

**HOW VERIFIED.**
- **Frozen real fixtures.** `tests/fixtures/section16/` holds seven cases. Each is every SEC
  document the block reads for one issuer at 2026-10-28, with the submissions index trimmed to
  the annual-report and Form 3/4/5 rows it reads. Each fixture was replayed through both versions
  and had to reproduce the live output before it was written.
  - **QFIN:** 20-F, Cayman; the positive case.
  - **IPX:** Australia; the May order, and the reference-date bound.
  - **SLI:** 40-F, British Columbia; labelled "Reports abroad".
  - **BLDP:** blank EDGAR code, read from the cover.
  - **DQ:** on no order; the negative pin.
  - **IBN** (as of 2026-04-01): India, the May order. Blank EDGAR code, and a 20-F that is not
    inline XBRL, so the jurisdiction is unread. Its 6.3 MB cover is cut to the first 100,000
    bytes, which holds the cover page.
  - **DBVT:** a French company that files 10-K; domestic. Its whole `Sourced` must equal what
    origin/main produced from the same documents.
- **Code table.** `tests/fixtures/sec_reference/edgar_state_country_codes.json` is EDGAR's code
  table, parsed deterministically from the sec.gov page (309 codes).
- **End to end.** A committed dossier (WERN) carries the real FPI values through
  `render._positioning_lines`. The label is "Insider activity (Form 4)", and IPX's trailing
  `other M×1` still collapses to "other filings 1".
- **Mutation, one per rule: 10 of 10 killed.**
  - window floor dropped from the FPI line;
  - count window never cut;
  - FPI read not bounded at the reference date (this survived the first pass, and the IPX
    as-of-2026-05-01 pin was added to kill it);
  - no code maps to a regime;
  - May order in force before its date;
  - an order-jurisdiction issuer with no filings stays UNKNOWN;
  - a 10-K filer read as an FPI;
  - cover fallback never read;
  - cover names matched by substring;
  - an unread jurisdiction left silent on a read line.
  - The source was restored byte-identical and `__pycache__` cleared after each mutation.
- **The cover fallback, measured on the whole primary population.** A peer session reported the
  dei tag absent on CYD's and JOYY's covers and eight issuers unresolved. Measured over #837's
  255 primary FPI lines:
  - 48 have a blank EDGAR code, and **all 48 covers carry the tag**. 20 map to an order's
    jurisdiction and 28 name a place on no order. **0 of the 255 end with their jurisdiction
    unread.**
  - CYD reads "Bermuda" and JOYY "Cayman Islands". ASR, BLDP, MGA, PAAS, SB, STVN, TAK and TSM
    all resolve; STVN reads "Italy", in the EEA.
  - Of the 255, 109 sit in a jurisdiction on an order in force at 2026-10-28. #837 counted 107;
    the difference is exactly BLDP and STVN, the two it could not place.
  - **The one miss among the 11 names checked is IBN** (theme band, not primary). Its 20-F
    carries no inline XBRL at all; the cover prints "India" as text. Printed text is not parsed
    (CLAUDE.md: parsers consume structured values), so IBN reads "unread" and says so.
- **Gates (item 4): no screen or ranker reads insider activity.** Searches tried:
  - `insider`, `Form 4`, `forms=("4"`, `16(a)`, `beneficial own`, `Form4`, `catalyst_path`,
    `insider_activity` and `dossier.mechanical` across `vinci/rank`, `vinci/screens`,
    `vinci/scoring`, `vinci/ledger`, `vinci/triage.py`, `vinci/universe.py` and
    `vinci/orchestrator.py`;
  - `git log -S"insider"` and `git log -S"Form4Line"` on rank, screens and scoring;
  - `git log --all -i --grep=insider`.
  - The one positioning surface, the queue's evidence strip (`vinci/evidence.py`), has no
    insider leg. It is AST-fenced from `rank` and `screens` by
    `test_the_scorer_and_the_screen_can_never_read_the_evidence_strip`.
  - Result: not found under those searches. No gate exists to window, and none was added.
- **No page was re-assembled.** The run calls `_insider_activity` directly; no committed artifact
  changed.

**BOUNDARY.**
- **Reference date:** 2026-10-28 for every name. #837 measured to 2026-10-16; the counts above
  agree with it except where stated.
- **Populations:**
  - the 56 foreign lines of the committed `data/snapshots/ranked_queue.jsonl` (run 2026-10-16-01,
    343 names), as #837's record lists them by tier;
  - the 27 committed `data/dossiers/*/dossier.json`.
- **Unit:** a name, which is an issuer here. Each of the 83 maps to one CIK through SEC's
  `company_tickers_exchange.json`.
- **FPI test:** the newest 10-K, 10-KT, 20-F or 40-F (no amendments) filed on or before the
  reference date, in the issuer's `recent` submissions block.
- **Windows:**
  - FPI Forms 3/4/5 and their amendments, filed 2026-03-18 to the reference date;
  - domestic Form 4s over 1,095 days, as before;
  - the count window: 182 days, cut at 2026-03-18 for an FPI.
- **Data:**
  - SEC documents fetched 2026-10-28, read through to the primary checkout's SEC cache read-only;
  - the two orders and EDGAR's code table read at sec.gov 2026-10-28;
  - Arelle/EDGAR `transform/__init__.py` read 2026-10-28.
- **Cover-tag coverage:** #837's 255 primary FPI lines, as listed by tier in its record, plus
  JOYY, IBN, MGA, PAAS, TAK and TSM. Each issuer's latest annual report on or before
  2026-10-28; the tag is read from that report's primary document.
- **Other-issuer measurement** (FOLLOW-UPS, item 1): Form 4s filed 2023-10-29 to 2026-10-28 in
  each of the 27 dossier issuers' `recent` indexes, 5,407 in all; each one's XML was read.
- **Code:** `1114490b` before; this branch after. The branch was rebased onto `1341c021`
  (#837); `vinci/dossier/mechanical.py` and `vinci/edgar/client.py` are identical at both, so
  the "before" is current main's code.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **"Reports abroad" rests on condition (i) and on an empty filing index, not on condition
   (ii).** The line says so in words. FALSIFIER: an issuer labelled "Reports abroad" whose
   insiders turn out to be subject to no qualifying regulation (for example, listed only in New
   York) and simply not filing. The label would then be wrong, and the absence a compliance
   question.
2. **Incorporation is CURRENT, not point-in-time.** EDGAR's submissions document carries today's
   value. A re-domiciled issuer read at an old reference date shows where it is incorporated now.
3. **Forms 3 and 5 are counted from the index, unparsed.** A Form 3/5 the FPI files as a HOLDER
   of another issuer would count as its own insiders filing.
   - Measured on Form 4: none of the queue FPIs' Form 4s since 2026-03-18 names another issuer.
     This is the same defect as FOLLOW-UPS item 1, and that item's fix covers both paths.
   - FALSIFIER: an FPI read "from 2026-03-18" whose only filings since are about another issuer.
4. **A cover that is not inline XBRL leaves the jurisdiction unread** (IBN), and the line says
   so. Printed text is not parsed. FALSIFIER: a primary-population FPI with a blank EDGAR code
   and an untagged cover; on 2026-10-28 there are 0 of 255.
5. **No annual report in the `recent` block reads as domestic** (today's behaviour). This covers
   an issuer with no periodic report yet (#837 lists OGC, GORO, AYA and MDA) and a late filer
   whose last annual has rolled out of `recent`. None of the 83 names is either.

**FOLLOW-UPS (found on this run, reported, not fixed: each changes the DOMESTIC line, which this
build must not).**
1. **A Form 4 the company files as a HOLDER of another issuer enters its own insider line.**
   - 19 of the 5,407 Form 4s in the 27 dossiers' 3-year scans name another issuer: AMZN 2 (Air
     Transport Services Group), GOOGL 11 (Ethos Technologies, Prime Medicine, Starco Brands, Verve
     Therapeutics), UBER 6 (Aurora Innovation, Neutron Holdings).
   - **UBER's committed line, "sells 4 (2 insiders, $1135.10M)", is mostly Uber selling Aurora
     stock:** $479.25M, $471.60M and $182.24M, 2026-06-04 to 09-17.
   - **GOOGL's "last purchase $4.95M, 10% owner"** is Alphabet buying Prime Medicine (Form 4
     filed 2025-08-05).
   - `_form4_codes` reads `reportingOwner` but never `issuer/issuerCik`.
2. **A Form 4 whose documents fail to fetch is dropped silently.** `_form4_codes` returns `[]`, so
   counts shrink with no mark on the line; this was GOOGL's 462 against 464 grants on the loaded
   first pass.
3. **The domestic read is not bounded at the reference date.** `recent_filings` has no upper bound
   and `compose_insider_line` counts every row from the window start, so a re-dated read counts
   later filings while stating "in the last 182 days". The FPI path is bounded. Shown on IBN:
   origin/main read as of 2026-04-01 prints "last sale $0.63M, director, 2026-04-24 (~-1mo ago)",
   a sale three weeks after its reference date (the fixture's `origin_main`).
4. **An UNKNOWN insider value keeps the label "(Form 4, 6m)"** while its note states another
   horizon. This is `render.py`/`dossier.js`'s label derivation, domestic and FPI alike.
