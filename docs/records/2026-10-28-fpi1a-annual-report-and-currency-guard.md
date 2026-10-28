---
status: shipped
date: 2026-10-28
prs: [844]
supersedes:
superseded-by:
---

# FPI1a: a 20-F or 40-F is read as the annual report, and a figure in another currency is never read as dollars

**WHAT.** STATE §5.0 row 4, step 2 of the build order in
`docs/records/2026-10-28-fpi-readiness-measured-per-name.md`, run after FPI4 (#840) and beside
FPI3 (#841). It does two things, in one PR because the first is unsafe without the second.

- **The currency guard** (`vinci/edgar/concepts.py`). Every XBRL money read in the repo goes
  through `points_for_tag`, and it returned every unit under a tag. QFIN's newest annual revenue
  was served as CNY 19,205,059,000 beside its USD convenience translation, and the screen divided
  $5.67 per ADS by a CNY EPS.
  - **`reporting_currency(facts)`**: the currency the filer's statements are in, counted on its
    balance-sheet totals (`Assets`, `Liabilities`, `LiabilitiesAndStockholdersEquity`,
    `StockholdersEquity`) in its newest annual report. It never reads the unit of one fact: QFIN's
    newest balance sheet carries CNY twice and its USD translation once.
  - **`points_for_tag` serves a money fact only in USD, and only for a filer reporting in USD.**
    A USD reporter loses its foreign figures (AQN's CAD statements from before it moved to USD).
    A filer reporting in another currency gets NO money fact, its USD convenience translation
    included: that is its newest year at one period-end rate, an FX policy, and FPI1b's to rule
    on. A unit with no currency (shares, pure) is served either way.
  - **`currency=REPORTING`** serves the filer's own currency, for a reading the currency cannot
    move. It is used in exactly two places: the EPS series every P/E percentile ranks, and the
    fiscal calendar (`_own_periods`, dates only).
  - **The P/E level** (`pe_current_and_percentile`, shared by the screen, the dossier, the
    peer-cohort command and the theme desk): an EPS in another currency leaves the level UNKNOWN,
    naming the currency. The percentile is kept: one series in one currency ranks the same in any.
  - **The snapshot** (`compute_fundamental_snapshot`): a non-USD reporter's every field is
    UNKNOWN with the currency named, rather than reading "not tagged".
  - **SBC** reads its USD facts raw, so it checks the currency itself.
  - **The reason, everywhere:** "the filer's US GAAP figures are in CNY, and a CNY figure is never
    read as dollars — converting it is STATE §5.0 row 4's FPI1b". It names the US GAAP figures
    because those are the only ones read: JMIA reports under IFRS in USD now, and its us-gaap
    facts, all older, are in EUR.
- **The annual-report gates**, each opened to a foreign filer's annual report.
  - **Segment profit** (`_segment_profit`): 10-K, 20-F, 40-F. The instance reader now refuses an
    IFRS instance, naming FPI1c, instead of reading it as a single-segment filer. It already
    refused a non-USD segment figure.
  - **SBC** (`_sbc_annual`): facts filed with a 10-K, 20-F or 40-F.
  - **Material contracts** (`_covenant_pointers` step 1): read from the newest annual report of
    any form. A 20-F files them as Exhibit 4.x, not 10.x, and only documents are read. A 40-F has
    no such exhibit class, so a filer whose newest is a 40-F is not read here.
  - **Debt maturities** (`_maturity_sources`): the latest 10-Q, 10-K, 20-F or 40-F. A maturity is
    a date, the same in any currency.
  - **The primary-source sections** (`_primary_source`): the latest 10-Q, or, for a filer that
    files none, its newest annual report when that is a 20-F. A 40-F is not read: its primary
    document is a cover. A filer
    reporting in another currency is not read at all, because the parser reads "$" amounts and
    its "US$" figures are convenience translations.
  - **The customer/supplier graph** (`latest_10k_excerpts`): 10-K, 20-F, 40-F.
  - **One list:** `concepts.ANNUAL_REPORT_FORMS`, made public from the fiscal calendar's private
    copy.

**WHY.** Tier 1 (66 primary lines, 11 in the queue) is US GAAP in USD and needed only the form
gates. #837 measured why the guard had to come with them: opening the gates alone serves QFIN's
CNY 19.2bn as $19.2bn. The record's step 2 wording was "a non-USD fact is never read as dollars".
This build reads it to include the USD convenience translations of a non-USD reporter: the record
itself says a translation "is not an FX policy. It is one rate applied to one year", and the FX
ruling is the operator's (step 6).

**THIS REVERSES ONE EARLIER READING.** #749 (2026-10-20) had pinned LPL's and HSAI's net debt as
read from their USD convenience translations (`test_every_leg_is_read_in_dollars`). Both now read
no net debt, and the pin says so. If the operator rules that a convenience translation IS a dollar
figure, it is one line, in `_served_currency`.

**HOW VERIFIED.**

1. **The screen's EDGAR fields, before (main 2d457a81) and after, on every line.** These are the
   2026-10-16 primary universe and the 2026-08-24 theme band, through the production
   `enrich_with_fundamentals`, on the 2026-10-16 store's bars, one companyfacts file per issuer
   for both runs, and FPI4's ADS ratio.
   - **2,935 lines; 2,349 with companyfacts.** The 586 without:
     - 582 theme-band names: 581 never fetched, and IBN, which has none at SEC;
     - 4 primary lines with none at SEC: PBT, SCZM, BTQ, AYA.
   - **2,259 report in USD or tag no us-gaap money fact: 0 fields change, values or notes.** Every
     Tier 0 (7) and Tier 1 (66) line is among them.
   - **90 report in another currency** (CNY 30, CAD 14, EUR 11, JPY 7, KRW 5, BRL 4, the rest 3
     or fewer). On them:
     - **The P/E level is withheld on exactly #837's 14 CNY-EPS lines:** QFIN (queue 1), HSAI
       (175), ATAT, ATHM, BILI, BZ, FINV, GDS, LI, MOMO, RERE, RLX, VIPS, YMM. QFIN's level read
       0.129x before.
     - **The percentile moves on none.** QFIN 0.0008, ATHM 0.292 and RLX 0.448 are identical
       before and after; the other 11 had none.
     - **G3's outcome moves on no line of the 2,349.**
     - **The snapshot's fields go UNKNOWN, naming the currency:** op-income sign 44, FCF sign 46,
       net leverage 8, net debt / OCF 11. These gate nothing; CP and ENB (10-K filers reporting in
       CAD) are among them.
     - **The share-count change is unchanged on all 90:** shares carry no currency.
2. **JOYY.** Its EPS is tagged in CNY and USD. The 2026-10-16 store holds 51 of its bars, so its
   screened percentile is UNKNOWN either way. On its own five-year closes (554 sessions,
   2021-10-18..2026-10-16, from the Polygon grouped cache):
   - **before:** 125 of 256 P/E observations read a CNY EPS and 131 a USD EPS;
   - **after:** all 256 read USD.
   The percentile is UNKNOWN both ways (256 points, under the 450 floor).
3. **The gates, before and after, on every primary FPI line** (the 266 rows of #837's primary
   population; filings to 2026-10-16; production functions; SEC documents as fetched 2026-10-28).
   The rows are 192 lines whose latest annual report is a 20-F, 63 a 40-F, 7 a 10-K and 4 none.
   On main, no gate read anything from a 20-F or 40-F.

   | gate | 20-F (192) | 40-F (63) |
   |---|---|---|
   | segment profit | 11 read; 110 refused IFRS; 4 refused not USD (GDS, HSAI, RLX, VIPS); 8 UNKNOWN, no profit measure tagged; 2 no readable single instance; 57 single-segment | 4 read; 54 refused IFRS; 1 no single instance; 4 single-segment |
   | SBC | 52 read; 19 withheld, currency; 121 no SBC tag | 5 read; 56 no SBC tag; 2 no companyfacts |
   | material contracts | 78 read (Exhibit 4.x); 114 none filed | none (no such class) |
   | maturity check, periodic read | 192 read, 99 stating maturities; PRE's fetch failed | 63 read, 2 stating maturities |
   | primary-source sections | 157 read; 34 withheld, currency; PRE failed | none read (one, CIGI, reads its 2004 10-Q, as on main) |
   | graph excerpts | 191 read; PRE failed | 63 read, 38 with no excerpt (a cover document) |

   - **Tier 1 (66, US GAAP in USD):**
     - segment profit: 15 read, 8 with no profit measure tagged, 1 instance unreadable (RZLV),
       42 single-segment;
     - SBC: 55 read;
     - material contracts: 24 read;
     - maturities: all 66 read, 35 stating maturities;
     - sections: 60 read;
     - graph: all 66 read.
   - **The first cut read a 40-F filer's OLD 20-F.** 6 lines' material contracts and 12 lines'
     sections came from a 20-F filed before the filer moved to 40-Fs, back to DSGX's of 2005 and
     DNN's of 2005. The newest annual report of any form now decides (pinned on NAK: a 40-F every
     year since 2017, a 20-F in 2016). Re-run on all 15 affected lines (the 12, plus CIGI, ARCO and
     QFIN as controls): no 40-F filer reads an old 20-F; ARCO and QFIN read as before.
   - **PRE's 20-F breaks `html_to_text`** (`ValueError: zip() argument 2 is shorter than argument
     1`, in the page-furniture strip #829 added). Every reader catches it and states it, and the
     graph's coverage loop records the name as an error. It is outside this build.
4. **The currency read on the corpus.** 2,543 cached companyfacts, one per CIK. It agrees with a
   count over every money fact of the newest annual report on 2,257 of 2,258, the exception
   being Fresenius Medical Care (its us-gaap totals stop at its last US GAAP 20-F, in USD). It
   never ties, and the runner-up is at most half.
5. **The IFRS refusal on the corpus.** Of the 252 readable latest 20-F / 40-F instances, 164 tag
   ifrs-full facts and no us-gaap fact, and every one is refused. LPL's declares the us-gaap
   namespace without using it, so the rule counts the facts' taxonomy, not the declarations; the
   first cut, on declarations, read LPL as a single-segment filer.
6. **Material contracts on the corpus.** Of the 192 latest 20-Fs, 78 carry an Exhibit 4.x
   document and 106 none (their contracts are incorporated by reference); ASR's carries page
   images named inside one. 48 of 63 latest 40-Fs carry 99.x exhibits and none carries a
   material-contracts class.
7. **Pins** (`tests/test_fpi1a_annual_report_currency.py`, 25, every one on a real filing):
   - **Positive:** a USD reporter's dollars still read; QFIN's own CNY revenue is there under
     `REPORTING`; the same EPS in dollars makes a level; AQN's 40-F SBC ($13.0M); ARCO's 20-F
     segments (three divisions); ARCO's seven Exhibit 4.x contracts; a 20-F or 40-F as the
     maturity check's periodic; a dollar reporter's 20-F read for sections; a 10-Q filer still
     read on its 10-Q; the graph on a 20-F.
   - **Negative:** QFIN's CNY revenue and its USD translation never served; QFIN's level withheld;
     its snapshot and SBC named; LPL's IFRS instance refused; ASR's images and ZLAB's 10-K
     Exhibit 4.5 not read as contracts; QFIN's 20-F not fetched for sections; NAK, a 40-F filer,
     not read on its 2016 20-F for contracts or sections.
   - **The four P/E callers** read EPS with `REPORTING` (AST), and the screen's end to end.
   - **The currency judged as of the blob:** JOYY CNY on 2022-04-28, USD on 2022-04-29.
   - Three existing pins changed:
     - #749's LPL net debt, now withheld (above);
     - a hand-rolled `Filing` stand-in given the real type's `form`;
     - the SBC note pin, matching the new wording.
8. **Mutations: 24 tried, 24 red.**
   - **The reader:** every currency served; the translation served; the currency counted over
     every filing; the currency read off the newest fact's unit; the fiscal calendar in dollars.
   - **The P/E and snapshot:** a foreign EPS makes a level; the screen reads EPS in dollars; the
     snapshot does not name the currency.
   - **SBC:** reads the translation; reads a 10-K only.
   - **Segment profit:** asks for a 10-K only; IFRS judged by declarations; IFRS not refused.
   - **Material contracts:** 10-K only; a 20-F read for ex-10; a 20-F image read; a 10-K's ex-4
     read as a contract.
   - **Maturities:** 10-Q / 10-K only.
   - **Material contracts and sections, the first cut:** read on an old 20-F.
   - **Sections:** no 20-F fallback; a 20-F before a 10-Q; a yuan reporter's 20-F read.
   - **Graph:** 10-K only.

**BOUNDARY.**
- The screen-field counts are over the 2026-10-16 primary universe (2,065, in_universe=1) and the
  2026-08-24 theme band (928) in the scratch clone of the 2026-10-16 store, at reference date
  2026-10-16, with companyfacts as fetched by 2026-10-28.
- The tiers are #837's.
- The gate counts are over #837's 266 primary rows (262 FPI-rule lines plus 4 unresolved), filings
  on or before 2026-10-16.
- The corpus counts are over 2,543 cached companyfacts, one per CIK, as cached on 2026-10-28.
- Code: before = main 2d457a81; after = this branch on main 68da34ae. #841 touches none of the
  readers measured.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A non-USD reporter's signs and one-currency ratios are withheld.** They could be read in its
  own currency; FPI1b converts them and they return, in dollars, through the same lines. No gate
  reads them. FALSIFIER: a gate that comes to read the snapshot's signs.
- **The guard judges the us-gaap figures only.** An IFRS filer's currency is FPI1c's to read from
  its own instance.
- **FX drift stays in a non-USD reporter's percentile:** a constant currency cancels in a rank,
  its drift over five years does not. This is unchanged from before, and FPI1b's to rule on.
- **A 40-F's sections and graph excerpts stay thin:** its primary document is a cover, its MD&A
  and business description are exhibits. Reading them is a follow-up.
- **Reported, not fixed:**
  - CIGI's gates read a 2003 10-K and a 2004 10-Q as its "latest" on main. The annual-report gates
    now take its 2026 40-F, but the sections pass, which reads a 10-Q first, still reads the 2004
    one. No gate bounds a "latest" filing's age. Of the 192 latest-20-F lines, none carries a 10-Q
    in its submissions index, so the 10-Q-first rule reaches no 20-F filer.
  - PRE's `html_to_text` failure (above).
  - 8 Tier 1 20-F filers tag segment contexts but no profit measure the reader knows (CMRE, DAC,
    GLNG, LAES, MLCO, NTB, PLGO, WB). Each reads UNKNOWN with that reason; widening the measure
    list is a reader change of its own.
