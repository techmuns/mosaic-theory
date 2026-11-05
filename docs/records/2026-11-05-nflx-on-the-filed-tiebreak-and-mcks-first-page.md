---
status: shipped
date: 2026-11-05
prs: [918]
supersedes:
superseded-by:
---

# NFLX re-assembled once on the filed tiebreak, and MCK's first page: NFLX states its merger row as the quarterly +2,800.0 with a caveat naming the annual −2,800.0; MCK lands under the quality book, lean mixed

**WHAT.** Two paid builds in the Phase 1 rebuild (STATE §5.0 row 41), one at a time, on main
`c4c9f432`, extraction version `2026-11-05.input-record`, model `claude-opus-4-8`. Both are priced at
the 2026-11-04 close, the latest at build time (06:58 ET on 2026-11-05).

| page | run | calls (failed) | cost | lean (draws) before → after | proposal before → after | R1 base $/sh (diluted) before → after |
|---|---|---|---|---|---|---|
| NFLX | `56f6a840` | 10 (0) | **$5.55** | mixed (mixed 4 / strongly-bullish 1) → **mixed (5 of 5)** | none → none | 54.435 (53.6425) → **54.435 (53.6425)**, unchanged |
| MCK | `d4304414` | 11 (0) | **$7.40** | — (first page) → **mixed (mixed 4 / strongly-bullish 1)** | — → none (withheld) | — → **484.7056 (483.0321)** |

*NFLX's merger row — the operator's ruling "NFLX: B" (#891), confirmed on the written page.*
- The annual summary's `Merger & Related Restruct. Charges ($M)` LTM cell reads **2,800** (value
  +2800.0). The committed page read −2,800.
- Its footnote [20] cites the quarterly export's row, "four quarters to 2026-09-30, its breakdown
  reconciling in every quarter to EDGAR XBRL us-gaap:NonoperatingIncomeExpense as filed by
  2026-11-04", with accessions 0001065280-25-000406 (Q3 2025 10-Q), 0001065280-26-000034 (FY2025
  10-K, which supplies the derived Q4), 0001065280-26-000138, -000212 and -000291 (the 2026 10-Qs).
- The main-body caveat leads the analyst caveats, after the follow notice. It opens "CIQ READING
  CONFIRMED BY THE FILING", says "the annual export's LTM reads -2,800.0", gives the four quarters
  (45.5 / 45.473; 2,852.2 / 2,852.166; 51.7 / 51.661; 43.0 / 43.006 filed), and says the annual
  export reaches the same filed total, 2,992.3, only through +5,554.7 under Other Non-Operating —
  so the quarter-by-quarter breakdown is what decides it.
- The `ciq-ltm-quarters` QA flag stays: the annual LTM −2,800.0 against the quarters' +2,800.0,
  "DIFFER by 5,600.0 $M".
- **For the operator's look — the synthesis reads the label, not the sign.** A bear point says "A
  $2,800.0M Merger & Related Restruct. Charge sits in the LTM … though it is a one-time rather
  than recurring drag", and a key unknown speaks of "restructuring/aborted-deal costs". The page
  states +2,800.0, filed inside non-operating income: a one-off INCOME item in the trailing period,
  not a cost. The 19c guard checks that the figure is stated, not its direction. Not re-drawn: a
  re-roll to clean the prose is selection on outcome (RUNBOOKS §i).

*NFLX: everything else that moved against the committed page (#867, assembled 2026-10-29).*
- **Fields** (`prespend.compare`, the precheck's own comparison, run on the committed and the
  written page): 116 compared; **0 lost**; **2 gained** — `drawdown_cause.anchor.at_anchor.shape`
  and `drawdown_cause.anchor.since.shape`; 0 moved to a dated part.
- **Values moved on 9 Sourced fields** outside lists: `stock_info.price` 61.99 → 66.39 (2026-10-28 →
  2026-11-04 close); `high_52w` 124.86 → 116.733 and `low_52w` 61.51 → 61.3922 (the C4 cut: a
  365-day window ending on the price date, was 377 days); `valuation.pe` 24.50 → 26.24 and the
  forward multiples (P/FY26E 17.36 → 18.60), on the price; the merger row (above); and three
  covenant blocks.
- **Anchor:** recipe `R1_midcycle_margin_evebitda` both ways, recomputed 2026-11-05 with every
  input unchanged — margin 11.4915% (19-FY EDGAR median), multiple 37.730565x (ex-lease band median
  over 35 quarters), D&A 392.188 and net debt 6,909.441 to 2026-09-30, 4,106,325,903 shares.
- **Valuation basis:** still not priceable on the same one conflict (the share counts differ by
  2.16%); EV/EBITDA ex-lease at the page price 16.385 → 17.518.
- **Phase 1 items now on the page:** the pointer-cap row ("showing 4 of 13 aggregate lines", row
  41 C1); the covenant (E5) refusals — 6 values stating a currency figure their quote does not,
  and one margin (3%, the 2009 revolver) withheld because its own quote does not state it (row 41
  D2, row 34); the EV bridge's preferred and minority lines unread, each naming the absent row (A-D2,
  were 0.0); the quality FCF sign's accession (C2); consensus levels footnoted; the peer
  capital-intensity rows cited and read at the new price date (AMZN's and ROKU's impairment windows
  now end 2026-09-30, on filings made since the last build).
- **Covenant term rows 33 → 28.** They are LLM-extracted and lie in a list, so the precheck forecasts
  rather than compares them ("decided by the paid draw"). Five row names of the earlier draw are
  absent from this one: Applicable Margin (Pricing Grid), Commitment Fee, Default Rate, Letter of
  Credit Sublimit and Optional increase (accordion).
- **Counts:** caveats 39 → 14; UNTRACEABLE caveats 33 → 8; QA flags 24 → 30.
- **Lean:** "Mixed — near-floor multiple on all-time-high, still-compounding EBITDA and intact
  pricing/churn flywheel, set against a sustained idiosyncratic de-rate with sharply negative
  estimate breadth." The draws now agree; mixed proposes nothing either way.

*MCK, a first page* (sleeve `quality`, ruled 2026-10-29).
- **Follow entry** added to `data/followed.json` in its own commit (RUNBOOKS §i step 1). The reason
  quotes the operator's 2026-10-29 rebuild list and the sleeve ruling and states nothing else.
- **Inputs:** 11 exports, the operator's 2026-11-05 re-export, every sha256 equal to Drive's; the
  Q2 FY27 call (2026-11-04) among them. Primary source: 10-Q 0000927653-26-000281 and the 8-K
  release filed 2026-11-04. Price $1,069.44 (2026-11-04), market cap $124,686.4M → SPY.
- **Anchor:** `R1_midcycle_margin_evebitda`, firm. Margin 1.1544% (10-FY EDGAR median), multiple
  10.485817x (ex-lease band median; rent 7.9% of EBITDA, material), D&A 776.0 and net debt 2,869.0 to
  2026-09-30, 115,456,664 shares. Base **$484.71** a share. Valuation basis priceable, no conflicts;
  EV/EBITDA ex-lease 16.805x at the page price; the band's current reading is 17.332x (2026-11-04).
- **Lean:** "mixed — operating momentum is strongly bullish, but a trailing multiple at its own
  9.5-year ceiling leaves expectations fully priced." Draws mixed 4 / strongly-bullish 1, so the
  page says the draws disagreed.
- **Counts:** 118 Sourced fields outside lists (101 present, 17 unknown); all six top-level blocks
  present; 15 caveats (12 UNTRACEABLE); 47 QA flags. No material unusual item demanded a statement
  (0 at $0), so no filed tiebreak ran. The LTM-against-quarters check writes 8 QA flags, none on a
  material row: EBITDA and EBIT differ by 2.23% and 2.44% (tolerance 2%), Legal Settlements and
  Other Unusual Items differ, and four more unusual rows reconcile on the one quarter carrying a
  figure and say UNVERIFIED.
- **Fixtures:** MCK's companyfacts (32 tags) and price series (483 bars to 2026-11-04) are new;
  IWM's price fixture gains 13 bars and changes none of its existing 470.

*Each page's `inputs` block* (#911's record, written by the build, not backfilled).

| page | `inputs_id` | CIQ exports | responses (digest sha256) | price series to 2026-11-04 | unrecorded |
|---|---|---|---|---|---|
| NFLX | `inputs-1551f42b79740589` (was `null`, a backfill of CIQ only) | 11 | 1,329: sec 1,312, polygon 14, efts 2, finra 1 (`d945f7c6…`); 9 companyfacts listed, NFLX's own sealed by `edgar-4f3207f4da9fb71a` | IWM `debd2403e95d`, SPY `f447a7f3453b`, NFLX `7c56cad950e1` | none |
| MCK | `inputs-cf05f5b9609b56d5` | 11 | 363: sec 347, polygon 14, efts 1, finra 1 (`1c55b0e9…`); 8 companyfacts listed, none sealed | IWM, SPY, MCK `8d893cd4f534` | none |

NFLX's CIQ rows: comps `7356f91da573`, credit health `8e682d3eb47a`, customers `0841b3f8721e`,
suppliers `b1108f2c70da`, estimates `a1a68bc0b24c`, annual `8ae9f12b10ac`, quarterly
`512a1e9a0abc`, key developments `2544fa8c2814`, profile `3d65f6e0ca5e`, Q2 and Q3 2026 calls
`d43cfe18e388` and `832ec9a909d2`.

*Operator rulings of 2026-11-05, relayed by the coordinating session and recorded here.*
- **PARR is excluded from the Phase 1 rebuild** — the operator verbatim: "we can exclude PARR".
- **UBER waits for a Financials re-export.** Its 2026-11-05 exports' six latest columns (Q3 2026)
  are 'Press Release' columns: CIQ had not processed the 10-Q filed 2026-11-04, so assembly would
  refuse them. Not run.

**WHY.** NFLX's last assembly was refused because its two CIQ exports disagreed on the merger row;
the operator ruled the filed tiebreak's containing line decides it (#891, merged `f419b845`), and
this is the separate artifact pass that ruling left. MCK is the rebuild's one first assembly. The
operator approved $50 for the remaining pages on 2026-11-05.

**HOW VERIFIED.**
- **Inputs:** each folder's 11 files hashed against Drive (read-only) before any build: all equal.
- **Prices:** `vinci refresh … --aggs --start 2021-07-01 --end 2026-11-04` for NFLX, SPY, IWM, MDY
  and MCK, written to the assembler's store (`mosaic-theory-ta/data/vinci.db`, linked). The stored
  NFLX closes run without a gap from 2026-10-16 to 11-04. MCK had no bars before.
- **$0 precheck, each name, before its spend** (paste of the boundary lines):
  - NFLX: committed 2026-10-29T19:09:38Z `2026-10-29.D-D5-prompt`; exports on disk 11, "the committed
    page's export stamps: 512a1e9a0a ×9 (on disk); a1a68bc0b2 ×3 (on disk)"; 115 Sourced fields + 6
    blocks compared; **0 regressions, 0 post-spend refusals**; oldest panel 9 days old (a build is
    refused on it from 2026-12-12).
  - MCK: no committed page; **0 post-spend refusals**; oldest panel 1 day old (refused from
    2026-12-20).
- **The merger row predicted at $0** (`prespend.mechanical_build`, no LLM call) before the spend:
  +2,800.0 and the caveat, identical to the written page.
- **One build each, run alone**, no LibreOffice conversion running beside it (checked).
- **Fixtures:** `build_companyfacts_fixture.py NFLX` regenerated byte-identical; MCK's two are new.
- **The suite:**
  - **Linked** — `data/manual` → a scratch copy of the assembler's CIQ folder made with the six
    held packs excluded at copy time (no held file was copied or read); `data/cache` and
    `data/vinci.db` → `-ta`. `pytest -m "not network"` on the artifact commits (`4232df61`):
    **11 failed, 9,339 passed, 89 skipped, 8 xfailed** (36 min).
    - **5 were this pass's:** MCK, a new fleet name, was missing from the SEC-reference slice
      (`test_maintenance_path` ×3, `test_sec_reference_fixture` ×2). Its builder, re-run as the test
      asks, adds one row to each ticker file; all five then pass.
    - **6 fail identically on main `c4c9f432` with the same links** (a detached checkout, run from
      inside it), none on NFLX or MCK: AORT's EV-bridge claims (202.393 against CIQ's current
      330.7); GOOGL's FY2026 EPS Normalized spread against its Trends figure (14.80 against 14.14,
      a 2% check); three AMZN refresh pins (`test_forward_multiple_history` ×2,
      `test_historical_forecast_error` ×1 — the assembler's AMZN export is not the page's; Drive's
      is); and `test_store_freshness`, which reads the shared store: its names sit 5–29 days
      behind its 2026-11-04 newest bar (FUBO and VITL were already 24 days behind the 2026-10-30
      newest bar before this pass's refresh).
  - **CI-like** (the three links removed, as CI runs): on the final tree (artifacts, fixtures, this record and the STATE edits): **1 failed, 8,872 passed, 567 skipped, 8 xfailed** (10 min). The one failure was
    this record's empty `prs:` trail (`test_a_shipped_record_names_the_pr_that_carried_it`), filled
    before the push; the records tests then pass. #917 (open) is the PR that keeps every test off
    the held packs' exports; until it merges, a linked suite needs a copy made without them, as here.

**BOUNDARY.**
- **Runs:** 2, on 2026-11-05: `56f6a840` 11:58:05–12:08:03 UTC (597.6 s) and `d4304414`
  12:20:02–12:29:21 UTC (559.2 s); 21 calls, 0 failed, **$12.95** ($5.548677 + $7.404056) at list
  price. NFLX: 5 framing draws, 4 covenant, 1 operating drivers. MCK: the same plus 1 maturity event.
- **Draws:** 5 a name. Tallies are tallies, never rates.
- **Fields:** outermost Sourced fields outside lists, the committed page (git `c4c9f432`) against the
  written one; "values moved" compares the `value` of fields present on both.
- **UNTRACEABLE:** caveats matching "untraceable figure".
- **Responses:** counted from each page's `inputs.responses_digest`. Each precheck read a different
  set from its build — NFLX 1,330 (sec 1,313, `inputs-a7d22b739d2a04cd`) against 1,329; MCK 337 (sec
  321, `inputs-7f8cacbcd0231c03`) against 363 — so neither `inputs_id` equals its precheck's.
  Measured, not attributed: the paid LLM phases fetch exhibits the $0 forecast does not reach.
- **Store:** the assembler's `-ta` store, frontier 2026-11-04 after the refresh.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$12.95** of the operator's $50; $37.05 remains for V, ORKA, SMPL and UBER.
- **For the operator's look before merge:** NFLX's synthesis calls the +2,800.0 a charge and a drag
  (above); MCK's first lean and anchor (R1 base $484.71 against a $1,069.44 price).
- **Both pages still carry `price_store`'s absolute local paths** (`declared_path` in this worktree,
  `resolved_path` in `mosaic-theory-ta`). #915 rewrites every committed page's stamp, NFLX's
  included, and changes the writer; whichever of the two PRs merges second must re-run #915's rewrite
  on NFLX and MCK. Not fixed here.
- **The non-operating read's trailing-four-quarters window fix is in flight** (#916). NFLX and MCK
  pick it up only at their next assembly.
