---
id:
status: shipped
date: 2026-11-03
prs: [886]
supersedes: 2026-11-02-googl-re-assembled-on-its-filed-q3-exports.md
superseded-by:
---

# GOOGL, LLY and AMZN re-assembled once each on the operator's 2026-11-02 re-exports: GOOGL's EV bridge agrees with its comps again, LLY's anchor base reads off its Q3 10-Q, and a new monitor day is filed at the 2026-11-02 close

**WHAT.** Path A of #886, the hand-off of 2026-11-03 09:01 UTC. The operator re-exported:
- GOOGL's Company Comparable Analysis;
- LLY's Financials Annual. The first 2026-11-02 file was a byte-identical copy of the Quarterly;
- AMZN's Q3 2026 call (Oct 29), comps and Key Developments.

Each name was built once, one at a time, on main `9e996d7f`, which carries #884 (C4), #885 and
#888. No re-roll. The new pages replace GOOGL's 2026-11-02 page, LLY's 2026-10-29 page and
AMZN's 2026-10-26 page.

| | GOOGL | LLY | AMZN |
|---|---|---|---|
| run, cost | `05a57bf8`, $4.43, 7 calls | `ac8b8b71`, $3.03, 6 calls | `f4458b22`, $5.82, 10 calls |
| lean (draws) | mixed → mixed (4/1 → 4/1) | strongly-bullish (5/5 → 5/5) | mixed (5/5) → strongly-bullish (3/2) |
| machine proposal | none → none | BUY → BUY | none → none (withheld: draws disagree) |
| R1 base $/sh (diluted) | 225.54 (223.50) → 225.54 (223.50) | 752.24 → 752.24 | 279.70 (276.27) → **282.39 (278.99)**, +1.0% |
| recipe: committed / machine hint | R3 / R4, unchanged | R1 / none, unchanged | R4 / R4, unchanged |
| comps data date | 2026-10-28 ($324.89) → **2026-10-30 ($279.84)** | 2026-10-28 → 2026-10-30 ($1,417.54) | 2026-10-06 → 2026-10-30 ($240.35) |
| page price | $279.84 (10-30) → $278.99 (11-02) | $1,288.30 (10-28) → $1,410.99 (11-02) | $248.00 (10-23) → $245.63 (11-02) |
| EV bridge: claims vs comps TEV − cap ($M) | −96,744 vs −105,158 → **−96,744 = −96,744** | 45,162 = 45,162 → 43,858 = 43,858 | 128,647 = 128,647 → 190,615 = 190,615 |
| material row (LTM, stated by the synthesis) | Gain (Loss) On Sale Of Invest. 129,109 | In Process R & D Exp. −8,070 | Gain (Loss) On Sale Of Invest. 69,158 |
| UNTRACEABLE caveats | 8 → 21 | 7 → 24 | 0 → 10 (its old page predates #859) |

- **The exports passed main's own readers before any spend.** Each name:
  - loads 11 files with none unrecognised;
  - every statement states its own period type and reaches 2026-09-30 as a filed column;
  - no press-release column is the newest, and every panel states USD;
  - the comps are stamped 2026-11-02.
- **GOOGL: two of its three unexplained scorecard checks clear.**
  - `ev_bridge_vs_ciq_tev` and `forward_multiple_vintage` read confirmed on
    `data/snapshots/data_quality/ciq/2026-11-04.json`.
  - `fcf_sign_vs_edgar_ocf` still differs. CIQ's levered FCF (LTM to 2026-09-30) is
    −$1,162.5M, while EDGAR's latest-quarter operating cash flow is positive. That is two
    measures disagreeing on capex, which the check's own tolerance names; no re-export clears it.
  - Market cap is $3,431,315.0M, at the 2026-10-30 close (was $3,977,463.7M at 10-28).
- **GOOGL's trailing 22.9x is CIQ's 2026-09-30 quarter-end multiple, not today's.**
  - `valuation.ev_ebitda` and `own_history.current` read Financials→Multiples "TEV/LTM EBITDA
    Close (latest)" (`as_of` 2026-09-30). The comps sheet reads 17.5x at the 10-30 close.
  - The page flags the gap ("EV/EBITDA cross-sheet gap"), and the bear point quotes the 22.9x.
  - R1's multiple is the band's median, 17.4518x, unchanged.
- **LLY's anchor base comes back.** #885's round 2 measured that, cut at the old 2026-10-28
  price date, an EDGAR-only recompute had no base. The page now prices at 2026-11-02, after
  its Q3 10-Q (filed 2026-10-29). So D&A (2,174, trailing twelve months to 2026-09-30) and net
  debt (45,980) read off that 10-Q, and the base is 752.2356, as committed.
- **LLY's press-release-era figures are gone.** The 10-29 page read a press-release Q3 column
  and FY2025 cash flow. Now:
  - `quality.free_cash_flow` 1,951.0 → 9,343.7 and `net_debt_to_ocf` 2.7 → 1.4, both LTM to
    Sep-30-2026, filed;
  - `anchor.ltm_fcf` 8,972.0 (FY2025) → 19,661.0 (LTM);
  - the EV-bridge lines read the filed Q3 column: total debt 54,908 → 49,503, cash 8,950 → 4,885;
  - preferred and minority now read "unread" (no row / 'NA'), not 0.0.
- **AMZN's R1 moves +1.0% on its Q3 10-Q** (filed 2026-10-30):
  - D&A 75,200 → 79,353 (twelve months to 2026-09-30);
  - net debt ex-lease 23,783 → 81,536 (total debt 133,320 → 181,267);
  - LTM revenue 775,680 → 797,455;
  - the ex-lease band median 26.1178x (34 quarters) → 25.7538x (35 quarters);
  - `ev_ebitda_ex_lease_at_price` 15.977484 → 15.106403.
  - Two new scorecard rows read unexplained:
    - `fcf_sign_vs_edgar_ocf` differs (levered FCF −$34,731.8M LTM against a positive OCF);
    - `ebitda_vs_xbrl` differs on the quarter to 2025-12-31 (CIQ 41,948 against 44,448 rebuilt,
      −2,500), which entered the LTM window with the new quarter.
- **What the merged cuts (#884 C4, #885, #888) moved.** Every page now prices at 2026-11-02,
  and each name's newest 10-Q was filed on or before that date. So the cuts exclude no filing on
  any of the three pages; their visible effect is C4's 52-week window, the 365 days ending on the
  price date:
  - **GOOGL:** low 244.15 → 270.70, high 408.61 (window 2025-11-02→2026-11-02, 251 bars). The
    share count, net debt and every anchor leg are the committed 11-02 page's own.
  - **LLY:** low 783.8454 → 850.51, high 1,321.21 → 1,449.68. Its 10-Q `0000059478-26-000108`
    and 8-K `…-000104` stay read. C4's predicted fallback to `…-000081` / `…-000077` applied only
    at the old 10-28 price date. Share count 940,745,031, filed 2026-10-29.
  - **AMZN:** the 52-week range is unchanged (196.00 / 287.20). Row 41's 274.35-versus-279.70
    question is moot: the page re-assembled at 282.39 on the 10-Q and the new comps.
- **The monitor day is NEW, not a re-cut.** `data/monitor/2026-11-02.json` was run with no
  `--ref` (RUNBOOKS §j); the 2026-10-30 day is untouched.
  - The book is on total return, with Tiingo's dividends on every leg.
  - GOOGL marks at $278.99: −19.29% against its $345.90 entry, −16.41% excess vs SPY.
  - BUY−AVOID is +73.96 pp (price return +73.95 pp), against +63.08 pp on 10-30.
  - The panel-emit pin is green on it. The newest `newer_filings` date is 2026-11-03 and the newest
    `last_evidence_date` is 2026-09-01, both on or before the run day.

**Known defect, recorded, not fixed (an artifact PR carries no code).** GOOGL's bear point says
"four straight quarters of material below-operating-line items".
- `vinci/dossier/mechanical.py:2185` takes `_nonop_common(...)[-4:]`: the last four quarters
  for which operating income, pre-tax income and revenue are all filed.
- GOOGL files no standalone Q4, so that window skips Q4 2025 and reaches back to Q3 2025. The
  four are not consecutive.
- R4's condition ("4 of the trailing 4 quarters carry material non-operating income") still holds
  on the four it reads. The fix is scheduled separately.

**WHY.** The hand-off found GOOGL's page disagreeing with itself. Its comps were dated 2026-10-28
at $324.89, before the Q3 10-Q and a −12.6% fall, while the page priced at $279.84. So the EV
bridge was off by $8,414M and three checks read "differs, unexplained". GOOGL is a live position.
The operator chose Path A: re-export, then rebuild all three pages once, after #885 so LLY's and
AMZN's anchors are rebuilt only once.

**HOW VERIFIED.**
- Gates, checked before any spend:
  - (1) `02314b24` and `9e996d7f` are on origin/main.
  - (2) The exports passed main's readers, as above.
  - (3) EDGAR submissions, fetched fresh 2026-11-03: GOOGL 10-Q 2026-10-29
    `0001652044-26-000084`, LLY 10-Q 2026-10-29 `0000059478-26-000108`, AMZN 10-Q 2026-10-30
    `0001018724-26-000040`. The store holds a 2026-11-02 close for each.
  - (4) Only #886's branch claims the names.
- Each page reads its Q2 and Q3 calls, and none carries a dropped-call flag.
- Re-derived from each committed page: the before figures above, and LLY's material row
  quoted in its bear point ("In Process R&D Exp. was $8,070.0M in the LTM").
- **The full offline suite, run for the first time on an artifact pass WITH the live CIQ folder
  linked** (`pytest -m "not network" -rs`; the shown runs are in #886's body). Without the folder
  about 550 tests skip; with it 74 do. Three groups of failures came out of it:
  - **3, fixed by data.** AMZN's tracking companyfacts fixture, regenerated as the fixture README
    requires in the PR that re-assembles a name (LLY's and GOOGL's came out byte-identical).
  - **5, fixed by test edits** (operator-approved 2026-11-04, "yes to both"). Each was a value
    pin on a living page. Each now reads the page itself, or a frozen vintage: AMZN's 2026-06-30
    companyfacts are frozen beside GOOGL's (`tests/fixtures/companyfacts_frozen/AMZN.json`).
    None of the new numbers is pinned, and two of the edited guards were mutation-checked.
  - **12, pre-existing on main** (`9e996d7f`, same folder, same failures):
    - SMPL ×6 and NCNO ×1: Drive's exports are 2026-10-28's, the pages 2026-08-17's.
    - NFLX ×1: the test pins FQ2, and the live export carries FQ3.
    - AORT ×1: comps and estimates are 2026-10-26's, Financials 2026-07-20's; the bridge correctly
      reads DISAGREES.
    - GOOGL and LLY ×1 each: CIQ's Consensus and Trends sheets differ by 4.7% and 5.1% after the
      Q3 revisions, against a 2% check; the right cells are read.
    - `test_store_freshness` ×1: the primary's store's newest bar is 2026-08-11, IWM's
      2026-07-02.
  - They are an operator follow-up in STATE §5.0 row 32 (28): AORT's Financials re-pull, the 2%
    tolerance, the primary store. The skip-when-not-the-page's-export test change is agent work
    in its own PR.

**BOUNDARY.**
- **Code:** main `9e996d7f` merged into #886 as `f1ccc813`. Extraction version
  `2026-11-03.ex-lease-share-cut`, model `claude-opus-4-8`.
- **Runs:** 3, on 2026-11-03 between 12:46 and 18:32 UTC, 23 calls, 0 failed, $13.28 at list
  price.
  - The machine slept during the first two (lid closed at 18:18 IST). GOOGL's 9,185 s and LLY's
    10,716 s are wall time, about 29 and 23 minutes of it awake (`pmset -g log`); AMZN's 814 s
    ran awake.
- **Draws:** 5 a name. The tallies are tallies, never rates.
- **UNTRACEABLE:** the page's caveats matching "untraceable figure".
- **Store:** a copy of the primary's `data/vinci.db` (sha `0263451a…`, bars to 2026-08-11)
  in this session's worktree; the primary was not written. Topped up by `vinci refresh … --aggs
  --start 2021-07-01 --end 2026-11-02`:
  - SPY, GOOGL, LLY and AMZN;
  - all 20 cohort members of GOOGL (12) and AMZN (21) that did not reach the 2026-11-02 close,
    so no stale 180-day return prints;
  - after the refresh, every cohort member's last bar is 2026-11-02.
  - Polygon served 2024-11-04..2026-11-02 (500 bars) to each name it had no history for. LLY's
    P/E percentile already rested on 478 observations (about 2 years). GOOGL's and AMZN's read
    UNKNOWN for their splits either way.
- **Monitor:** Polygon grouped-daily (the command keeps no store), and 7 Tiingo requests on a
  cold cache, 0 refused.
- **Scorecard:** CIQ source only, over the 27 pages in the working tree with the three new ones
  among them (git head `f1ccc813`, before the artifact commit), measured 2026-11-04.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$13.28.**
- **For the operator's look before merge:**
  - AMZN's lean moves mixed → strongly-bullish on a 3/2 split, so no proposal.
  - AMZN's R1 is +1.0%.
  - UNTRACEABLE counts rise on all three. They are this build's draws, read by #859's trace.
  - GOOGL's FCF-sign check stays unexplained, on the economics rather than the export.
