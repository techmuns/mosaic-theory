---
id:
status: open
date: 2026-11-19
prs: []
supersedes:
superseded-by:
---

# W73: R1 prices a DATED close judged by the event rule, never "today's"; both W62 clocks retire for `freshness.first_event_after`; a close after the page's date is refused (W68); the proposal takes R1's own dated close and verdict; `_r1_current` carries its own close's date and divides nothing across dates (W65's finding B); a 10% price-drift FLAG sits beside the multiple; IN CODE, no committed page re-rendered; preview APPROVED ("Approve with corrections"; the flag: "Proceed at 10%") ($0, code only)

**THE RULINGS.** The operator's words, 2026-11-19, each relayed verbatim by coordinator B:
- **"Approve with corrections"**, answering B's question "Approve W73 with the two corrections, the
  drift flag included?". It covers:
  - option (c);
  - both W62 clocks retired for the event rule, plus a price-drift flag (correction 1);
  - W61's line becoming "at 16.3x (the 2026-08-28 close)";
  - the anchor backfill as a SEPARATE $0 artifact PR after this one, no artifacts here;
  - LLY handled by a narrow expected-difference allowance rather than an xfail (correction 2).
- **"Proceed at 10%"**, answering "Proceed with the drift flag at 10% as measured?".
- **W65's deferred finding B** (`_r1_current` on a `dates_differ` or `date_unstated` reading) was
  folded in by B, behind a test that fails first.

**WHAT.**
- **The statistic is unchanged; its label and judge are new.** R1 prices its band's latest close,
  W50's value:
  - CIQ's history: the partial column at the export date where CIQ writes one, else the last
    quarter-end;
  - the ex-lease history: the last observation.
  - It is labelled with its date everywhere and never called "today's".
- **The event rule judges the close** (`anchor.close_verdict`, through `freshness.first_event_after`,
  which #1132's `event_verdict` now calls, so the two cannot disagree).
  - A report the rule counts, filed strictly after the close and on or before the page's price
    date, refuses it. The forms are #1132's own: 10-Q, 10-K, 8-K item 2.02, 20-F, 40-F, 10-KT,
    10-QT and every 6-K.
  - A refusal withholds the screen VALUE only. `applicable`, the recipe and the tier are untouched
    (W62's rule).
- **Also refused, never passed:**
  - an undated close or page;
  - a filing list that was not read;
  - a close AFTER the page's price date (W68: GOOGL's 2026-11-19 export closes 2026-11-18,
    against its page's 11-11).
- **Retired:** W62's 30-day CIQ clock (`anchor_split.STALE_CLOSE_DAYS`) and the ex-lease due date
  (`anchor.ex_lease_next_due`).
- **`anchor.multiple` records the verdict**: `close_stale`, and `close_note`, the words both
  renderers print verbatim.
- **`compute_anchor` takes two REQUIRED keywords**, `filings` and `eod_closes`, so every caller says
  what it read (as `panel_age` takes no default).
  - Assembly reads the filings after the close (`read_filing_events(…, since=anchor.r1_close(…))`)
    and the store it built the page's close from.
  - `anchor-backfill` (`cli._machine_anchor`) reads the same. A store it cannot read is stated on
    the page ("not measured"), never taken as no move.
- **The proposal** (`propose.py`):
  - its base multiple is R1's dated close, and it reads the verdict R1's anchor RECORDED — one
    decider, never re-decided;
  - it is refused, with what clears it, in four cases: the anchor was refused; the anchor carries
    no verdict (derived before W73); it prices another close (a band refreshed after it, or an
    anchor from before W50); or it prices no multiple (an R2 page);
  - its label and vintage state the date ("EV/EBITDA … multiple at the 2026-08-28 close");
  - the median beside it appears only next to a proposed close.
- **`valuation_basis._r1_current`** (W65's finding B):
  - CIQ's multiple is dated by its own close, through W65's `ev_ebitda_basis.multiple_close`;
  - it is re-stated at the page's price only through a TEV within W65's `SAME_PRICE_DAYS` of that
    close;
  - a `dates_differ` or `date_unstated` pairing is never called "measured";
  - every string stays byte-identical where the two dates agree.
- **THE PRICE-DRIFT FLAG** (correction 1; `anchor.CloseDrift` on `anchor.multiple.close_drift`, its
  words in `close_drift_note`):
  - It is the stock's move from the multiple's close to the page's close: PRICE ÷ PRICE ONLY. The
    page's `stock_info.price` is set over the store's EOD bar on or before the multiple's date,
    within `freshness.MAX_STORE_LAG_DAYS`. A close on the page's own date is the page's close, so
    it measures 0 with no bar read.
  - It is a dated FLAG in the multiple row, never a withholding.
  - A whole-number ratio (`freshness.whole_number_ratio`) states a share-basis change and no move.
  - A move that cannot be measured says so.
  - **The words carry the direction** ("⚠ the stock has fallen 24.2% since that close"). The
    screening block prints no signed percentage, and
    `test_screening_context_never_differences_the_anchor_against_spot` is unedited.
- **The labels move on an anchor that records a W73 verdict:**
  - the method row: "mid-cycle margin × its own history's multiple at the latest close";
  - the subtitle;
  - the multiple row: "Multiple at the latest close, own history | … | close of <date> · <pass> ·
    <flag> · median … beside it, not used";
  - the W61 split line ("at 16.3x (the 2026-08-28 close)") and its arithmetic ("passed by the
    event rule: …");
  - the leverage line, the stored BASIS text, the mid-cycle sentences and the refusal reasons.
  - **An anchor derived before W73 prints its own words** until it is re-derived, as one derived
    before W50 prints the median's (`render._screens_at_dated_close`, its twin in `anchorInner`).
    So the 26 committed `dossier.md` render byte-identically.
- **A new extraction vintage:**
  `2026-11-19.the-screening-anchor-prices-a-dated-close-judged-by-the-event-rule`, following
  W65's. It re-pins `anchor.py`, `anchor_split.py`, `assemble.py`, `freshness.py`,
  `mechanical.py` and `valuation_basis.py`.

**WHY.**
- "Today's multiple" (W50) was a claim about a date, and the close it named could be weeks old.
- The fence (2026-11-13, "Keep it off") forbids the honest repair, re-striking at the page's close.
  It would make W61's V0 the quote exactly.
- So the close stays dated and is judged by what can outdate it: the company reporting again. A
  close taken after the latest report is the market's read of everything reported.
- **What the two clocks got wrong:**
  - W62's 30-day clock refused BRBR's 09-21 close although nothing was reported before its 10-23
    page.
  - Its ex-lease due date passed PARR, TGT and TJX after each had reported. At a build on
    2026-11-19 that was 7 to 41 days of passing.
- **The proposal took the stale close silently.** It reached `scenario-create`'s deviation check as
  GOOGL's 22.9x.
- **The rejected options** (measured on the 26 pages in the approved preview):
  - (a) the last quarter-end close is struck before that quarter's own results, so it is stale for
    most of every quarter: 7 of 7 CIQ-history pages;
  - (b) the median re-opens the bias W50 removed (SMPL $46.48 vs $11.37).
- **DOES THIS SELECT ON FORM?** No. The rule reads filing dates, the flag reads two closes, and
  `_r1_current` reads two dates.

**THE DRIFT FLAG'S THRESHOLD: 10% (`anchor.DRIFT_FLAG_MOVE`).**
- **Rationale, set BEFORE any page was measured.** A tenth of the price is about one standard
  deviation of a month's move at a 30% annual volatility. That is the scale W61 used for the effects
  the split separates ("a month moves a share price about as much as the effects the screen
  separates"). So the flag marks a move as large as those effects, not day-to-day noise. No outcome
  and no forward return was read.
- **Why a FIXED size and not a volatility-scaled one** (B's note): the flag measures the size of the
  ERROR in the per-share screen value, the price having moved off the close the multiple is struck
  at. It does not measure how UNUSUAL the move is for that stock.
  - A 24% move in a volatile name misstates the screen value by as much as a 24% move in a quiet one.
  - A volatility-scaled line would flag the quiet name's 10% and pass the volatile name's 24%: the
    wrong way round for this purpose.
- **Sensitivity (TRANSPARENCY, NOT TUNING).** The partition at other limits, shown after the 10% line
  was fixed and never used to choose it. Pages with a measured move: 21 of 26.

| limit | pages flagged |
|---|---|
| ±5% | 10: BRBR, BURL, CNXC, GOOGL, NKE, PARR, SMPL, TGT, VRRM, WLK |
| **±10%** | **6: BURL, CNXC, GOOGL, PARR, SMPL, VRRM** |
| ±15% | 3: CNXC, SMPL, VRRM |
| ±20% | 2: SMPL, VRRM |

**HOW VERIFIED.**
- **The real run (head against main's own code, the `anchor-backfill` path).**
  - Each committed page at `2ecf6da0` was re-derived through main's code and through head's,
    written only to scratch. Inputs:
    - the committed companyfacts fixture;
    - the CIQ exports, read-only;
    - the filings fixture (head);
    - a read-only copy of #1132's impact store for the EOD bars (head).
  - **One value moves: BRBR**, withheld → $12.32.
  - **GOOGL** stays withheld, now naming the 2026-10-28 filing.
  - **Six pages are flagged:** VRRM −24.2% (EOD $2.19 on 11-06 → $1.66 on 11-17), SMPL +29.6%,
    GOOGL −14.7%, CNXC +16.7%, BURL −14.6% and PARR +10.3%.
  - **Outside `anchor`, only LLY's `valuation_basis.current_multiple.as_of` moves**, 2026-10-30 →
    2026-11-02.
  - **No mechanical-layer field moves on any page.** The synthesis reads no R1 anchor block (a
    grep of `synthesis.py` for `anchor` finds only the drawdown anchor), so no synthesis request
    changes.
  - **The control:** the store's bar on each page's own date equals `stock_info.price` on all 15
    pages it reaches (page dates up to 2026-11-10).
- **Pins:**
  - `tests/test_w73_dated_multiple.py` has 16 tests, every guard pinned positive AND negative on
    real pages, real filings and real EOD closes. W68 is pinned on GOOGL's real 2026-11-19
    Multiples sheet, cut through the decode path (`tests/fixtures/ciq_googl_multiples_2026_11_19.json`,
    sha 976c63d857; operator ruling 2026-11-04, #891). It decodes to the export's own band.
  - All 16 fail on main `2ecf6da0`. Finding B's pin fails at the defect itself: main labels IT's
    multiple 2026-12-31, the TEV's date.
  - `tests/test_w62_anchor_stale_multiple.py` is removed: its subject, the two clocks, is retired.
    Its still-valid pins move here: the value withheld and never the recipe; the "not priced" row
    on both renderers; the mid-cycle "would price".
- **Mutation:** 26 of 26 mutants red. They include:
  - the event rule never refusing; a filing on the close outdating it; a close after the page
    passing; unread filings passing;
  - a refusal flipping `applicable`;
  - the drift line at 25%; only rises flagged; no split check; no store-lag window; a signed
    percentage in the note; the drift reading the anchor;
  - each proposal refusal removed;
  - `_r1_current` rescaling across dates, calling every pairing measured, or labelling with the
    TEV's date;
  - either renderer printing the dated words on a pre-W73 anchor, or dropping the flag;
  - the split's "today's" back;
  - `committed_gap_split` re-deciding a verdict.
- **The rewritten pins** (116 failures in 42 files on the first cut, every one a pin of the
  behaviour changed). Every test that derives an anchor states its two reads (`tests/anchor_reads.py`:
  `NO_FILINGS`, `NO_BARS`, the real `page_filings`, `rederived` through the real path).
  - W62's hold-open helper now holds the event rule and the flag.
  - The approved W61 line is re-pinned to the operator's new words.
  - The proposal's pins derive their page's anchor first.
  - The field-set pin gains the four fields.
  - The stale-notice pin reads the anchor's recorded verdict.
  - LLY's pinned date moves to its own close (2026-11-02), which the event rule does not refuse.
- **LLY (correction 2):** `tests/w73_lly_expected.py` lets seven round-trip pins see one expected
  difference only: LLY's `valuation_basis.current_multiple.as_of`, only to 2026-11-02. Every other
  byte of every page is compared as before, so it is not an xfail. The artifact PR restates LLY and
  deletes the module.
- **The fence test** `test_screening_context_never_differences_the_anchor_against_spot` is green and
  byte-for-byte unedited.
- <full-suite result, impact section and review rounds: in the PR body>

**BOUNDARY.**
- Pages: `data/dossiers/*` at main `2ecf6da0` (26 pages; 11 active + 15 watch); the cut
  `cut-4889ddba` and VRRM's 2026-11-18 copy for the pins.
- Multiple legs: 23 pages have a band with a usable current; 21 have a measured move.
- Filings: every 10-Q, 10-K and 8-K item 2.02 each filer made 2026-08-01..2026-11-19 (EDGAR
  submissions, read 2026-11-19).
- EOD bars: `polygon-grouped`, 2026-08-05..2026-11-10, in a copy of #1132's impact store, made
  2026-11-19.
- Every verdict and move is measured at each page's own price date (`stock_info.as_of`).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The flag does not withhold.** VRRM's $1.34 is still struck on an EV the price has since left
  (net debt 77% of EV, about 4.3% per share for each 1%). The page now SAYS so, but only a test on
  the price could refuse it, and that is the fence.
- **FALSIFIER for the 10% line:** a page just under the line later shown to have been misleadingly
  priced means the line is too high. NKE at +9.7% is the nearest case on the corpus.
- **The anchor now reads EDGAR submissions and the EOD store** after its close. An unreadable feed
  withholds the VALUE, and an unread store states "not measured". Neither refuses the build.
- **Conservative by construction:**
  - A 10-Q filed after the same quarter's 8-K item 2.02 refuses a close struck between the two
    (#1132's shape). 0 pages today.
  - Between a results 8-K and its 10-Q, a re-export may not yet carry the new ex-lease observation.
- **Until each page's anchor is re-derived:**
  - the proposal refuses its base multiple and says why (the 14 R1-shaped templates);
  - the page keeps W50's words.
  - The separate $0 artifact PR carries the active pages, BRBR excluded; a watch page takes it at
    its next build.
- **Follow-up, not here:** `mechanical._STALE_CLOSE_DAYS` (45 days) still ages the same close in the
  assembly's EV/EBITDA integrity caveat (`_ev_ebitda_integrity_flag`). That is a caveat only, and
  never gates.
