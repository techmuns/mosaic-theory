---
id: 2026-11-02-asof-price-date
status: open
date: 2026-11-02
prs: [884]
supersedes:
superseded-by:
---

# Inputs are cut at the page's price date: the 52-week window is the 365 days ending on it, a share count filed after it is never used, and the fundamentals are read as they stood on it

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

**WHAT.** Phase 2, Session C, batch C4 (audit E1-D6, X1(b), F-D4).
- **The page's cut** is its price date — the latest stored close it divides by, which
  `mechanical._at_latest_close` already put on the record (`assemble_mechanical`'s `cut`).
- **F-D4.** `eod.compute_price_features` takes a `frontier`: no bar after it is read, and every
  window — the 52-week range, the trailing returns, the 90-day ADV — ends on the price date, the
  newest bar at or before it. The page's price box (`_stock_info`) and `cli._cmd_eod` (its `--ref`)
  pass it. The screen passes none: its bars are cut at its reference date already
  (`screens.run._bars_to`), so its windows end there as before.
- **X1(b).** `mechanical._edgar_shares_outstanding` uses only a count FILED on or before its
  as-of, and the page asks it at the cut (the price box, and the short-interest denominator, which
  must match it). `_adjusted_facts`' share basis takes the same bound.
- **E1-D6.** The page's `_adjusted_facts` reads the fundamentals snapshot and companyfacts as they
  stood on the cut (`fundamental_snapshot(as_of=…)`, `concepts.facts_as_of`), and so does the CIQ-empty
  EDGAR fallback (`_companyfacts_as_of`). The screen's `enrich_with_fundamentals` reads them as of
  its own price date (its newest bar at or before the reference date): it read today's
  companyfacts, so a re-run of a past screen saw every filing made since.
- Test doubles of `fundamental_snapshot(_and_facts)` take the real `as_of` keyword now
  (`test_dossier`, `test_fpi1a_annual_report_currency`, `test_net_debt_one_builder`,
  `test_orchestrator`, `test_screen2`); `test_sec_refusals`' one-read test expects the snapshot as
  of the screen's date.

**WHY.** A page priced on one day read prices, counts and filings from later days. NFLX's and
LLY's pages (reference 2026-10-16, price 2026-10-28) printed a 377-day "52-week" window; LLY's
took a share count filed 2026-10-29, the day after its price; and the screen's fundamentals were
whatever companyfacts held when the code ran, not when the screen judged.

**HOW VERIFIED.**
- **Failing first.** `tests/test_asof_cut.py` (8), on real fixtures — NFLX's stored bars
  (`tests/fixtures/prices/NFLX.jsonl`) and LLY's and NFLX's share counts as filed
  (`tests/fixtures/asof_cut`, the copy their committed pages were assembled from): 6 failed on main
  `936dd707` (no `frontier`; LLY's 2026-10-29 count used; no `cut`; the screen's snapshot read
  with no as-of; its share change reading NFLX's count filed 2026-10-21 on a 2026-10-16 screen);
  the 2 negative pins (the screen's windows without a frontier; NFLX's count filed 2026-10-21 used
  on its 2026-10-28 page) pass on main and now.
- **Every committed page** (26 that this session may open), against the values it COMMITS, at its
  own reference and price date, from the price store and SEC caches it was assembled from
  (mosaic-theory-ta's `data/vinci.db` and `data/cache/sec`, the b6-model-inputs worktree's, the
  primary's; read-only):
  - **the 52-week window becomes the 365 days ending on the price date on 25** (every page but
    TECX, whose reference and price dates coincide): 368–387 days before (EPAM, MVST and WERN 387;
    NFLX, LLY, CNXC, NKE, ROST, TJX 377; AMZN, AORT, BRBR, GOOGL, ORKA, PARR, TGT, UBER, V, WLK 372;
    FUBO, IT, NCNO, SMPL, VITL, VRRM 368);
  - **the 52-week high or low VALUE moves on 9**: BRBR high 34.88 → 33.805; CNXC high 48.08 →
    46.3075; GOOGL low 244.15 → 251.85; LLY low 783.8454 → 809.63; NFLX high 124.86 → 116.733;
    NKE high 70.44 → 69.1364; ORKA low 25.11 → 25.23; PARR low 33.83 → 34.37; ROST low 154.691 →
    157.39;
  - **the share count moves on 1, LLY**: 940,745,031 (counted 2026-10-26, filed 2026-10-29) →
    941,357,065 (counted 2026-08-03, filed 2026-08-05); its short-interest denominator with it.
    LLY's anchor refuses its count either way (the anchor compares it with a Q3 weighted average
    from that same 2026-10-29 filing, read in `anchor.py`, Session A's file — open below). NFLX's
    count, filed 2026-10-21, stands;
  - **the fundamentals move on none**: only LLY's cache held a filing after its price date when it
    was assembled (its 2026-10-29 10-Q), and LLY's adjusted lines are UNKNOWN (no revised guidance
    to read them from); no committed page cites an EDGAR fallback figure at all. FUBO's, NKE's
    and V's counts are CIQ-bridged and unchanged.
- **The screen** (run `2026-10-16-01`: the 434 candidates that reached G3, each record built the
  screen's way on the store's bars to 2026-10-16 and enriched from the NEWEST cached companyfacts
  across this machine's 24 SEC caches — all 434 fetched after 2026-10-16 — main against the
  branch): **G3 moves on 0 and admission on 0.** The share change (an inform-only evidence-strip
  reading) moves on 13 — AIR, APLD, BOOT, CRML, IPX, KBH, NB, NG, PKE, TLRY, TMQ, UEC, WINA — and
  net debt / OCF on 1 (AIR 7.85 → 8.21), each now reading no filing made after the screen's date.
  (On the primary cache alone, whose blobs for these names were fetched in August, nothing can
  move: 0 carry a row filed after 2026-10-16.)

**BOUNDARY.**
- Pages: their own `reference_date` and `date_semantics.price_as_of`; the store
  `/Users/work/Documents/GitHub/mosaic-theory-ta/data/vinci.db` (frontier 2026-10-30) and the SEC
  caches named above, read 2026-11-02.
- Screen: run `2026-10-16-01` (reference 2026-10-16), the 434 of 2,065 candidates whose row
  carries a G3 outcome; bars ≤ 2026-10-16 from the store above; IWM as the record's benchmark.
- Main: `936dd707`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A page re-assembled moves to the price date it is assembled at**: these comparisons hold each
  page at its committed price date; a re-assembly reads its new one.
- **The trailing returns and ADV of `compute_price_features` end on the price date too** when a
  frontier is passed; the page's price box shows only the price and the 52-week range, and
  `cli._cmd_eod` prints them for the date asked.

**OPEN — NOT THIS PR.**
- **The anchor's own share cross-check** (`anchor.py`, Session A's file) reads a weighted average
  filed after the page's price date (LLY's Q3 2026, filed 2026-10-29).
- **Readers that cut at the page's REFERENCE date** (the SBC, insider, ownership, dilution and
  Section 16 windows, the covenant and maturity reads) read nothing after it — stricter than the
  ruling, never later — and are unchanged.
- **The rank's dilution series** (`rank/structural._shares_for`) reads companyfacts uncut, as the
  rank runs on today's data.
