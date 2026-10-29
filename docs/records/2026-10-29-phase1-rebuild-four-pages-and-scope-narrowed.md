---
status: shipped
date: 2026-10-29
prs: [866]
supersedes:
superseded-by:
---

# Four pages re-assembled on the Phase 1 code (ROST, TJX, CNXC, NKE); NFLX and LLY refused by the material-figure guard and left as committed; the rebuild is narrowed to fourteen names

**WHAT.**

*The operator narrowed the combined rebuild (2026-10-29).* Relayed by the coordinating session, the
operator's words were: "PARR, UBER, GOOGL, NKE, ROST, AMZN, V, TJX, NFLX, LLY, MCK, SMPL, ORKA,
CNXC … we can ignore the others as we are not pursuing those names anymore".

Thirteen committed pages are therefore NOT rebuilt: WLK, BRBR, TGT, NCNO, AORT, VRRM, IT, EPAM,
FUBO, MVST, WERN, TECX and VITL. Consequences:
- **Their committed pages keep the values row 41 lists.**
- **VRRM's and IT's ledger rows still score.** Scoring reads the price store (row 38), not the
  pages: VRRM matures 2026-12-14, and IT and SMPL on 2027-01-16.
- **The six strict-xfail pins in `tests/test_pages_await_parser_rebuild.py` stay expected
  failures.** Every one of them sits on a not-pursued page (FUBO, VITL, VRRM, EPAM/WERN/MVST), or
  on WERN together with NFLX: NFLX's half reads the located wall, WERN's half keeps that pin an
  xfail.
- **The fourteen names:**
  - pages for PARR, UBER, GOOGL, NKE, ROST, AMZN, V, TJX, NFLX, LLY, SMPL, ORKA and CNXC;
  - plus MCK, which has no page and would be a first assembly. The operator ruled its sleeve
    `quality` on 2026-10-29, and its follow entry lands with its build.

*This pass (operator's go, "Go for group a" and the b1 go):*
- **Four pages re-assembled on main `8d351bb8`** (extraction version `2026-10-29.G-D3`): ROST,
  TJX, CNXC and NKE. Each now carries every Phase 1 change:
  - the CIQ reader (#861) and the quality checks (#863);
  - whole transcripts (#864) and the synthesis-input checks (#859): the UNTRACEABLE caveats are
    shown on the page;
  - the release and 10-Q parsers (#860);
  - the materiality guard on revenue (#858);
  - the D&A-window R1 base (#836).
- **Two builds REFUSED** by the 19c material-figure guard. No page was written; both committed
  pages are untouched and both run records are kept:
  - **NFLX** (run `e0ecf6df`, $5.06): "Merger & Related Restruct. Charges ($M) LTM = -2,800.0".
    The line is new in the 2026-10-28 export (blank FY17–FY25) and is 5.63% of LTM revenue
    ($49,734.6M).
  - **LLY** (run `41a3c51b`, $2.91): "In Process R & D Exp. ($M) LTM = -8,070.0". It is 9.33% of
    LTM revenue ($86,462.0M) now that Q3 is in the LTM column; it was −4,544.0 on the old export.
  - In both, the brief showed the row (the P1 brief fix) and the kept draw did not state it. The
    operator chose a prompt fix first (#865, merged before this PR): the synthesis is now asked
    for each material row. NFLX and LLY each build once on that code, in the next artifact PR.
- **GOOGL is held**:
  - its new EstimatesReport (2026-10-29) carries no As-Of header, and every one of its 250 Recent
    Changes rows is stamped with a time of day ("12:46 PM") rather than a date;
  - so `estimates_as_of` reads UNKNOWN, and its catalyst path would lose its export-relative
    anchor;
  - the operator's call: re-export that one file or build as is.

*CIQ synced into the assembler's copy (`mosaic-theory-ta`)*, archive-then-mirror, by sha256:
- **NCNO, NFLX, MCK and LLY** (2026-10-28 exports): old sets in
  `ciq-archive/replaced-2026-10-29/<T>/`.
  - LLY's and MCK's one-file Financials pairs are gone. #861's `CiqMislabelledError` no longer
    fires on the synced copies and still fires on the archived pairs.
  - LLY's committed page keeps its old reading until it is re-assembled. MCK has no page.
- **GOOGL, LLY and NKE** (2026-10-29 exports, Q3 / FQ1 FY27): old sets in
  `ciq-archive/replaced-2026-10-29b/<T>/`.
- 34 of 34 non-held folders mirror Drive.

| page | lean (draws) before → after | proposal before → after | R1 base $/sh (diluted) before → after | multiple | comps date | UNTRACEABLE on page | run $ (run) |
|---|---|---|---|---|---|---|---|
| ROST | mixed (5/5) → **strongly-bullish (3 / mixed 2)** | none → none (withheld: draws disagree) | 166.18 (165.27) → **167.59 (166.67)** | 14.845x → 14.845x | 09-25 | 0 → 13 | $2.24 (`2b562803`) |
| TJX | strongly-bullish (3 / mixed 1, 4 of 5 completed) → strongly-bullish (5/5) | withheld → **BUY** (sleeve overshoot) | 131.10 (129.57) → **132.14 (130.60)** | 15.845x → 15.845x | 10-16 | 0 → 15 | $4.32 (`8ad38af1`) |
| CNXC | mixed (5/5) → mixed (5/5) | none → none | 84.80 → **82.75** (R1_NOT_ROBUST) | 7.094x → 7.094x | 10-23 | 0 → 17 | $5.41 (`40520189`) |
| NKE | mixed (5/5) → mixed (5/5) | none → none | 101.07 (101.03) → **99.30 (99.26)** | 23.545x → 23.388x | 09-21 → **10-28** | 0 → 12 | $4.60 (`8a695c73`) |

**Material rows each synthesis must state** — a $0 prediction from the assembler's own
`financial_summary_annual` plus `mark_material_rows` on the export each build reads. It reproduces
both refusals and CNXC's pass exactly:

| page | material rows |
|---|---|
| ROST, TJX, NKE | none |
| CNXC | Impairment of Goodwill FY25 −1,523.3, LTM −2,573.3 (stated, so the build passed) |
| NFLX | Merger & Related Restruct. Charges LTM −2,800.0 (refused) |
| LLY | In Process R & D Exp. FY25 −2,910.0, LTM −8,070.0 (refused) |
| GOOGL | Gain (Loss) On Sale Of Invest. FY25 24,620.0, LTM 24,620.0 (held) |

**WHY.** Phase 1's code (#856–#864) moved values the committed pages still carried. Row 41 lists
them. Only a re-assembly lands them on a page.

**HOW VERIFIED.**
- **Inputs before any paid run:**
  - CIQ freshness: each page's comps data date against the 45-day gate, all inside it on
    2026-10-29.
  - The `-ta` price store was topped up to the 2026-10-28 close: 21 bars for ROST, TJX, CNXC, NFLX,
    SPY, MDY and IWM; 9 for GOOGL, LLY and NKE.
  - The claim `artifacts/rost-tjx-cnxc-nflx-2026-10-29` was pushed before work. No open PR touched
    `data/dossiers/`, and no other session was running.
- **One assembly at a time** (the LibreOffice collision #864 recorded).
- **The R1 moves are the ones #836 pre-measured, to the digit.** ROST 166.1793 → 167.5944, TJX
  131.1019 → 132.1391 and CNXC → 82.7509 equal the after-column of
  `docs/records/2026-10-28-the-anchors-d-and-a-covers-its-ltm-window.md`. NKE's #836 row was
  unchanged (its window was FY26). Its move here, 101.0715 → 99.2985, is the new FQ1 FY27 trailing
  window the 2026-10-29 export carries.
- **Fixtures:** ROST's, TJX's, CNXC's and NKE's companyfacts fixtures regenerate byte-identical.
  The price fixture is not rebuilt; it changes only when a name becomes newly maintained, and none
  did.
- **Monitor:** no monitor day is owed. The latest day's rows (GOOGL, IT, SMPL, VRRM) and panels
  (names with underwrite records) include none of the four pages. The panel-emit pin is in the
  suite below.
- **CIQ scorecard** rewritten over the final page set: `data/snapshots/data_quality/ciq/2026-10-29.json`.
- **Suite, CI-like** (CIQ copy, store and caches unlinked), on the merged tree at `efad380f`:
  8,144 passed, 0 failed, 545 skipped, 18 xfailed.
- **Suite, linked** (before the backfill-pin edit and the merge): 12 failed. One was this pass's:
  the backfill pin, fixed in the same PR. The other 11 fail identically on a clean `8d351bb8`
  worktree with the same links: SMPL ×6, NCNO, NFLX, GOOGL, AORT's EV bridge and store freshness,
  each a committed page compared with a workbook or store that has moved since.

**BOUNDARY.**
- **Pages:** 27 committed on main `8d351bb8`. 13 are kept by the narrowing (MCK has none), 13 are
  not pursued, and 1 is held separately. This pass re-assembled 4 of the 13 kept pages.
- **Runs:** 6 runs on 2026-10-29, 17:17–18:07 UTC: 4 written, 2 refused. 53 calls, 0 failed.
  **$24.55** in all ($24.545053), the sum of the six records' `usd` at list price, model
  `claude-opus-4-8`.
- **Draws:** 5 per build. The tallies are tallies, never rates.
- **UNTRACEABLE:** counted as the page's caveats matching "untraceable figure"; the before pages
  predate #859 and carry none.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$24.55**, of which $7.97 is the two refused builds.
- **Moves that need the operator's look before merge:**
  - TJX's proposal (withheld → BUY);
  - ROST's lean (mixed → strongly-bullish modal, with its proposal still withheld);
  - the four R1 bases.
- **Not edited here, and still naming not-pursued names:** §5.0 rows 27, 28, 30, 32 (10)/(20) and
  34. They describe pages that will not move. Reconciling them is its own edit.
