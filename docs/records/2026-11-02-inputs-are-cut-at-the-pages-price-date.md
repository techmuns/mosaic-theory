---
id: 2026-11-02-asof-price-date
status: open
date: 2026-11-02
prs: [884]
supersedes:
superseded-by:
---

# Inputs are cut at the page's price date: the page's mechanical layer reads EDGAR as it stood on it, and its price box and 52-week chart end on it

**THE RULING** (operator, 2026-11-01, relayed by the coordinator; the operator's words: "Approve
both"), verbatim: "Inputs are cut at the page's price date (filed on or before it; latest such
filing wins; nothing after a sealed verdict)." It covers E1-D6 (the fundamentals snapshot and
`_adjusted_facts` get their as-of), X1(b) (share counts filed after the cut are never used) and
F-D4 (the price features are bounded at the frontier, so the 52-week window is the 365 days ending
on the price date). The option it chose over: cutting at the page's REFERENCE date, the screening
date, which falls before the price the page divides by (NFLX's and LLY's pages: reference
2026-10-16, price 2026-10-28).

**THE SEAL IS HONOURED BY CONSTRUCTION, AND NO SEAL DATE IS PASSED IN.** The coordinator's first
brief glossed the ruling as "where a ledger seal date exists, the cut is min(price date, seal
date)", and withdrew that gloss on 2026-11-02 (measured first: the committed pages of all four
sealed names — VRRM sealed 06-21, IT 07-21, SMPL 08-05, GOOGL 08-28 — were assembled after their
seals, so the gloss would have reverted each to its decision-day inputs). What the operator
approved is that nothing filed after a verdict is sealed may feed THAT verdict. The verdict's own
page is the committed dossier the operator logs it from: `cli` calls `ledger.log_verdict` with
`decided_at=datetime.now()` and seals that dossier's `assembled_at` beside it
(`proposal_assembled_at`), and a page's price date is a stored close no later than its assembly.
So its price date is on or before its seal, and the price-date cut alone keeps every later filing
out of it; no path was found by which a verdict's own page could carry a later price date. A
re-assembly after a verdict (VRRM, IT, SMPL, GOOGL today) reads current inputs, cut at its own price
date, and the sealed verdict and its evidence stay in the append-only ledger, which no re-assembly
rewrites. No seal date is wired into assembly: the dossier package imports no ledger
(`dossier/assemble.py`: "the structural no-verdict line is untouched"), and stays so.

**WHAT.** Phase 2, Session C, batch C4 (audit E1-D6, X1(b), F-D4), with review round 2's
re-cut: each source is cut ONCE, at the assembly's entry, rather than at each reader.
- **The page's cut** is its price date: `vinci.edgar.asof.page_price_date(price_as_of,
  reference_date)`, the latest stored close the page divides by (`mechanical._at_latest_close`
  put it on the record), or the reference date when the page has none. It is the one helper both
  cuts read. Session A's anchor cut (#885) reads the same close from `stock_info.as_of`; that
  session was told the helper's name and its fallback on 2026-11-02.
- **The entry cut.** `assemble_mechanical` hands every reader `AsOfEdgar(edgar, cut)` in place of
  the client. That view cuts four things:
  - companyfacts, pruned whole (`concepts.facts_as_of`, so an alias is chosen on the facts as
    they stood);
  - the fundamentals snapshot, computed at the cut;
  - the filing lists (`recent_filings`), which drop every filing made after it;
  - full-text search, bounded at efts (`enddt`), so its own match count counts only filings made
    by the cut.

  Every page reader that took a filing list or companyfacts now reads through it, including the
  ones review round 2 found reading past the cut: the primary-source releases and 10-Q (and so
  `_release_adjusted_eps`), the valuation (`_valuation(facts=)`), its stated bases
  (`with_valuation_bases`), capital allocation and the statement reconciliation. That last one is
  still handed `filed_by` = the assembly's day, but its facts are already cut. Documents are
  fetched by `http` only for filings a cut list named. Read through the wrapped client only to say
  what the cut left out: `_count_filed_after`, below.
- **F-D4.** `eod.compute_price_features` takes a `frontier`. No bar after it is read, and every
  window ends on the price date (the newest bar at or before it): the 52-week range, the trailing
  returns and the 90-day ADV. The page's price box (`_stock_info`) and `cli._cmd_eod` (its `--ref`)
  pass it, and `vinci eod` prints the span it read, not the whole store's. The page's 52-week
  chart (`_stock_performance`) reads the same window, the 365 days ending on the price date (it
  had ended on the reference date). The screen passes no frontier: its bars are cut at its
  reference date already (`screens.run._bars_to`), so its windows end there as before.
  `vinci/eod/features.py` joins the extraction-version drift guard's watched modules.
- **X1(b).** `mechanical._edgar_shares_outstanding` uses only a count FILED on or before its as-of,
  and chooses its tag on the facts as they stood then: the whole blob is cut before the alias is
  picked, so a tag first filed later cannot displace the one that stood. The page asks it at the
  cut, for the price box and for the short-interest denominator, which must match it.
  `_adjusted_facts`' share basis takes the same bound. When the cut removes the only fresh count,
  the UNKNOWN says so: the count, the date it was counted, and that it was filed after the price
  date (`_count_filed_after`, bounded to a count that would have been fresh then).
- **E1-D6.** The screen's `enrich_with_fundamentals` reads the snapshot and companyfacts as of its
  own price date, its newest bar at or before the reference date. It had read today's
  companyfacts, so a re-run of a past screen saw every filing made since.
- Test doubles of `fundamental_snapshot(_and_facts)` take the real `as_of` keyword now
  (`test_dossier`, `test_fpi1a_annual_report_currency`, `test_net_debt_one_builder`,
  `test_orchestrator`, `test_screen2`). `test_sec_refusals`' one-read test expects the snapshot as
  of the screen's date.

**WHY.** A page priced on one day read prices, counts and filings from later days:
- NFLX's and LLY's pages (reference 2026-10-16, price 2026-10-28) printed a 377-day "52-week"
  window and a chart that ended twelve days before the price they divide by;
- LLY's page took a share count, a results release and a 10-Q, all filed 2026-10-29, the day
  after its price;
- ORKA's page (price 2026-10-23) took a release filed 2026-10-26;
- the screen's fundamentals were whatever companyfacts held when the code ran, not what it held
  when the screen judged.

**HOW VERIFIED.**
- **Failing first.** `tests/test_asof_cut.py` has 16 tests, on real fixtures in
  `tests/fixtures/asof_cut`:
  - NFLX's and LLY's stored bars (`tests/fixtures/prices`);
  - LLY's, NFLX's and Recursion's share counts as filed;
  - LLY's submissions page, holding its 10-Q and results 8-K of 2026-10-29.

  On main `a7e1214b`, 14 fail. The 2 negative pins pass there and now: the screen's windows
  without a frontier, and NFLX's count, filed 2026-10-21, used on its 2026-10-28 page.

  Seven tests were added in review round 2. Six of them fail on round 1's head `e635f726`:
  - the release, the four facts readers and the chart, each through the whole
    `assemble_mechanical` on LLY's inputs;
  - the UNKNOWN reason;
  - Recursion's tag (its newest count, 530,628,653 on 2026-06-30, read under the tag as it
    stood);
  - `vinci eod`'s span.

  The seventh, the end-to-end share-count and window pin, passes there by design: it pins the
  page's wiring.
- **Mutation.**
  - Dropping the entry wrap (`AsOfEdgar`) fails 3: the release, the four facts readers and the
    UNKNOWN reason. The share count stays right through its own call-site cut.
  - Putting the chart back on the reference date fails 1.
- **The pages that cite a filing made after their price date, re-run through the real
  `assemble_mechanical`, main `a7e1214b` against the branch.** The run is cache-only, at each
  page's own reference date, on bars served only to its committed price date, with an empty CIQ
  bundle (so only the EDGAR-driven blocks compare). A scan of all 26 pages found 3 holding such a
  filing by their assembly date, and 2 of them citing it; NFLX's (1 filing) is cited nowhere.
  - **LLY** (price 2026-10-28). Main cites 10-Q 0000059478-26-000108 (primary-source filing,
    maturity wall, QA flags; the committed page also in its statement reconciliation) and 8-K
    0000059478-26-000104 (the newest release, the adjusted-EPS note), both filed 2026-10-29.
  - **ORKA** (price 2026-10-23). Main cites 8-K 0001213900-26-112281, filed 2026-10-26, as its
    newest release and in its adjusted-EPS note.
  - **On the branch** neither page cites any filing made after its price date:
    - LLY's newest release is 8-K 0000059478-26-000077 (filed 2026-08-05) and its filing is 10-Q
      0000059478-26-000081;
    - ORKA's newest release is 8-K 0001213900-26-086933 (filed 2026-08-10).

    Both adjusted-EPS lines stay UNKNOWN (no annual guide either release states), and their
    notes name the earlier release.
- **Every committed page** (26 that this session may open), against the values it COMMITS, at its
  own reference and price date. The inputs are the price store and SEC caches it was assembled
  from, read-only: mosaic-theory-ta's `data/vinci.db` and `data/cache/sec`, the b6-model-inputs
  worktree's, and the primary's.
  - **The 52-week window becomes the 365 days ending on the price date on 25**, every page but
    TECX, whose reference and price dates coincide. It ran 368–387 days before: EPAM, MVST and
    WERN 387; NFLX, LLY, CNXC, NKE, ROST and TJX 377; AMZN, AORT, BRBR, GOOGL, ORKA, PARR, TGT,
    UBER, V and WLK 372; FUBO, IT, NCNO, SMPL, VITL and VRRM 368.
  - **The 52-week high or low VALUE moves on 9**: BRBR high 34.88 → 33.805; CNXC high 48.08 →
    46.3075; GOOGL low 244.15 → 251.85; LLY low 783.8454 → 809.63; NFLX high 124.86 → 116.733;
    NKE high 70.44 → 69.1364; ORKA low 25.11 → 25.23; PARR low 33.83 → 34.37; ROST low
    154.691 → 157.39.
  - **The 52-week chart moves on the same 25.** It now ends on the price date, not the reference
    date: 10 pages from 2025-10-17..2026-10-16 to 2025-10-24..2026-10-23, 6 to
    2025-10-29..2026-10-28, 6 from 2025-08-15..2026-08-14 to 2025-08-18..2026-08-17, and 3 from
    2025-08-25..2026-08-24 to 2025-09-17..2026-09-16. Each page's benchmark return moves with it.
    The name's return over the window moves on all 25:
    AMZN +17.3% → +10.6%; AORT −48.2% → −46.3%; BRBR −71.4% → −71.1%; CNXC −37.9% → −28.4%;
    EPAM −35.5% → −23.6%; FUBO −76.7% → −77.3%; GOOGL +34.5% → +23.2%; IT −24.1% → −25.0%;
    LLY +56.6% → +58.4%; MVST −71.6% → −82.6%; NCNO −25.0% → −27.9%; NFLX −41.2% → −43.7%;
    NKE −44.9% → −43.2%; ORKA +161.8% → +194.1%; PARR +136.3% → +93.3%; ROST +51.6% → +44.0%;
    SMPL −60.2% → −61.7%; TGT +69.8% → +62.1%; TJX +2.4% → −2.3%; UBER −23.8% → −29.1%;
    V +17.8% → +17.4%; VITL −77.2% → −77.4%; VRRM −80.6% → −80.9%; WERN +30.1% → +29.7%;
    WLK −15.8% → −18.5%.
  - **The share count moves on 1, LLY**: 940,745,031 (counted 2026-10-26, filed 2026-10-29) →
    941,357,065 (counted 2026-08-03, filed 2026-08-05), and its short-interest denominator with
    it. LLY's anchor refuses its count either way. The anchor compares it with a Q3 weighted
    average from that same 2026-10-29 filing, read in `anchor.py`, Session A's file (open,
    below). NFLX's count, filed 2026-10-21, stands.
  - **The releases and 10-Q move on LLY and ORKA**, as above.
  - **The fundamentals move on none.** Only LLY's cache held a companyfacts row filed after its
    price date when it was assembled (its 2026-10-29 10-Q). LLY's adjusted lines are UNKNOWN (no
    revised guidance to read them from), and no committed page cites an EDGAR fallback figure at
    all. FUBO's, NKE's and V's counts are CIQ-bridged and unchanged.
- **The screen** (run `2026-10-16-01`): the 434 candidates that reached G3, each record built the
  screen's way on the bars to 2026-10-16 of the research-alpha-audit worktree's store and enriched
  from the NEWEST cached companyfacts across this machine's 24 SEC caches (all 434 were fetched
  2026-10-17 to 2026-11-02, after the screen's date), main `a7e1214b` against the branch.
  - **G3 moves on 0 and admission on 0.** Both sides reproduce the run's own outcome on all 434:
    G3 58 PASS, 91 FAIL and 285 UNKNOWN (the run's NOT_EVALUATED); admission 343 PASS, 91 FAIL.
  - **Of the evidence-strip readings, only BOOT's moves:** its share change (inform-only),
    −2.03% → −0.72%. Main read the count in its 10-Q filed 2026-10-28 (29,904,482, counted
    2026-10-23). P/E, its percentile, the FCF and operating-income signs, net leverage and net
    debt / OCF move on 0.
  - **CORRECTION to this record's first cut**, which reported 13 share-change moves and AIR's net
    debt / OCF: that run read mosaic-theory-ta's store, which holds a 2026-10-16 bar for 29 names
    only. For the 13 names that moved, the newest bar there at or before 2026-10-16 is
    2026-09-22, so the branch cut those records at 2026-09-22 and dropped filings the screen
    legitimately read. The audit store holds 2026-10-16 bars for 2,078 names, all 13 included.

**BOUNDARY.**
- Pages: their own `reference_date` and `date_semantics.price_as_of`, read 2026-11-02.
  - Store: `/Users/work/Documents/GitHub/mosaic-theory-ta/data/vinci.db` (frontier 2026-10-30).
  - SEC caches: those named above.
  - The two assembly re-runs (LLY, ORKA): an empty CIQ bundle and no FINRA; bars served to each
    page's committed price date.
- Screen: run `2026-10-16-01` (reference 2026-10-16), the 434 of 2,065 candidates whose row
  carries a G3 outcome.
  - Bars ≤ 2026-10-16 from
    `/Users/work/Documents/GitHub/mosaic-theory/.claude/worktrees/research-alpha-audit-bcba59/data/vinci.db`
    (frontier 2026-10-16; 2,078 names with a 2026-10-16 bar).
  - IWM as the record's benchmark.
  - Companyfacts: the newest cached copy across this machine's 24 `data/cache/sec` directories.
- Main: `a7e1214b`; round 1's head `e635f726`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A re-assembled page moves to the price date it is assembled at.** These comparisons hold each
  page at its committed price date; a re-assembly reads its new one.
- **The trailing returns and ADV of `compute_price_features` end on the price date too** when a
  frontier is passed. The page's price box shows only the price and the 52-week range, and
  `vinci eod` prints them for the date asked.
- **A page now prints an OLDER release and 10-Q than it did** when one was filed between its price
  and its assembly (LLY, ORKA). This is what the ruling asks: a page is read as it stood on its
  price.

**OPEN — NOT THIS PR.**
- **The anchor reads companyfacts uncut** (`dossier/assemble.py`'s own
  `EdgarClient.from_config(cfg).companyfacts(...)` for `_assembly_anchor` and the EDGAR net debt).
  Its share cross-check reads LLY's Q3 2026 weighted average, filed 2026-10-29. Session A's #885
  cuts the anchor's net debt at the page's price date, and Session A was told the shared helper.
- **The refresh back-fill's own reads** (`dossier/refresh.py`, Session A's file) fetch companyfacts
  uncut for the lease basis, the valuation bases and the statement reconciliation. The
  reconciliation is bounded at `assembled_at`, not the page's price date.
- **Readers that cut at the page's REFERENCE date** (the SBC, insider, ownership, dilution and
  Section 16 windows, the covenant and maturity reads) are stricter than the ruling and never
  later. They are unchanged, and now also read through the entry cut.
- **The rank's dilution series** (`rank/structural._shares_for`) reads companyfacts uncut, as the
  rank runs on today's data.
- **The page's quality block reads the screen record's fundamentals** (`record.fundamentals`,
  enriched at the SCREEN's price date), not the page's later one. That is never later than the
  cut, but it is a second, earlier cut on the same page (review round 1, deferred).
