---
id: 2026-11-04-a-fiscal-year-change-is-no-column
status: open
date: 2026-11-04
prs: []
supersedes:
superseded-by:
---

# A fiscal-year change is no column: CIQ's "Fiscal Year Change" header marker is registered as a known non-period cell, and a page with no EV bridge says why

**WHAT.** SMPL's 2026-11-04 CIQ Financials exports reach back to 2015, past its 2016–17 fiscal-year
change, so every period header carries an undated `'Fiscal\nYear\nChange'` column between the old
calendar (the Conyers Park SPAC's December periods) and the new one (the Atkins predecessor's
August years, then SMPL's own). `ciq_sheets.latest_cell` (PR #872 round 2) refuses any undated
header cell, so SMPL's one assembly on those exports (run `4f30d3a2`, $2.27, held uncommitted on
`artifacts/smpl-2026-11-04`) read 13 CIQ readers UNKNOWN and built no EV bridge, with nothing said.

1. `ciq_sheets.PERIOD_HEADER_MARKERS` — a CLOSED registry, matched whitespace-normalised and
   exactly, holding one entry, `"Fiscal Year Change"` (both spellings CIQ writes: `'Fiscal\nYear\nChange'`
   on the statements, `' Fiscal Year Change'` on the Capital Structure Summary). `is_period_marker`
   reads it; `calendar_segments` numbers the fiscal calendars a header's markers divide.
2. `latest_cell` skips a registered marker; any other undated cell still returns "unplaced" (the
   `'Jun-30-2026A'` step-back #872 closed stays closed, pinned beside a marker too).
3. `_fin_periods` drops it as a column, so the annual and quarterly summary tables and the Ratios
   panel no longer print a column labelled `Fiscal Y`. **The column goes, its break stays:** the
   annual growth row and the quarterly QoQ / YoY rows read `— (basis)` across two calendars, as
   they did (by accident — the marker column's cells were `FYC`) while the marker sat between them.
   The quarterly revenue YoY (`_quarterly_revenue_yoy`, found in review) takes its prior-year
   quarter only within the latest column's calendar: an old-calendar quarter of the same number
   was a match across the change, and on SMPL's shape a second candidate that left the read
   empty (the SPAC's Q1 Mar-31-2017 and the predecessor's FQ1 Nov-26-2016 both read Q1 FY2017).
   SMPL's own latest quarter, FQ4 FY2026, has one candidate either way.
4. The Capital Structure Summary's order check runs within the LATEST calendar: the whole row never
   ascends on SMPL (Dec-31-2016 precedes Aug-29-2015). No earlier calendar may state a later date
   than the last column (the guarantee the whole-row check gave, now its own refusal), and the
   term-loan step's other end is never taken across the change.
5. `ciq_sheets.ev_bridge` returns `EvBridgeUnbuilt(reason, source_file, source_sha256)` where it
   returned a bare `None` in six places. The page carries it as `Dossier.ev_bridge_unbuilt`, ABSENT
   whenever `ev_bridge` is present and on every page built before it (committed pages round-trip
   byte-identically); a validator refuses a page carrying both, and `ev_bridge_transform` clears
   the reason when it lands a bridge. The three readers that refuse on a missing bridge name the
   reason: `valuation_basis`'s R4 conflict (and so its `qa_flag`), `propose.r4_bridge_fact`'s
   refusal, and the quality check's `not_run`.
6. Extraction version `2026-11-04.fiscal-year-change-marker`, with its JS twin.

**THE WEB RENDERER WAS CHECKED AND RENDERS NO BRIDGE.** `frontend/views/shared/dossier.js` prints
neither `ev_bridge` nor `valuation_basis` (only the extraction-version legend names them), and the
markdown renderer neither, so the reason reaches the JSON, the R4 conflict/qa flag, the proposer and
the scorecard — not a section of the web page. Giving the bridge a web section is a render PR under
the PREVIEW RULE; not built here.

**WHY.** A known CIQ layout cell was indistinguishable from an unknown one, so a header shape that
names no period refused a whole page. The registry is closed rather than a pattern because the
refusal is the protection: #872 found that skipping an undated newest column (`'Jun-30-2026A'`)
serves the column before it as the latest. Only a cell known to name no period is skipped.

**HOW VERIFIED.** On SMPL's live 2026-11-04 export (Financials_Quarterly / _Annual as on the Drive
at 2026-11-04), branch head vs `main` `cfedcb39`:
- **The 13 UNKNOWN fields read present**: net debt, total debt, LTM EBITDA, LTM OCF, free cash flow,
  interest coverage, balance-sheet posture, book value per share, key ratios, segments, geography,
  the Capital Structure Summary; segment EBITDA's note is the filing fact again ("single-segment
  reporting (Branded Nutritional Foods and Snacking Products)", where main read "the reason for the
  absence is undetermined"). The EV bridge builds at the Aug-29-2026 balance sheet and agrees with
  CIQ's own TEV less market cap within $0.5M. ON THE HELD PAGE (run `4f30d3a2`'s `dossier.json`,
  copied to the session notes folder, never committed) the marker left 10 fields UNKNOWN — interest
  coverage ×2 (quality, leverage), segments, segment EBITDA, geography, the Capital Structure
  Summary, the balance-sheet posture, key ratios, book value per share, and the BS-vs-bridge
  coherence read — and the bridge absent; each reads present on this branch (coherence checked with
  the export's own comparability gate). Net debt, total debt, LTM EBITDA, OCF and FCF were covered
  on that page by their EDGAR fallbacks and now read CIQ's figure. (The brief counted 12.)
- **The marker and the old calendar touch no latest read**: cutting every column up to and
  including the marker out of every Financials sheet in memory leaves all 18 latest reads tried
  (the 13, segment EBITDA, both Capital Structure Summary frequencies, the bridge, `ciq_balance.extract`)
  identical; a header with no marker runs exactly main's code path.
- **No output names the marker**, and no summary/ratios column is labelled `Fiscal Y`.
- **Fails first**: main's code on the same header shapes — all three SMPL statement headers
  "unplaced", `_fin_periods` emitting `'Fiscal Y'`, the CS Summary refusing on order.
- Pins (`tests/test_fiscal_year_change_marker.py`, 27): POSITIVE on SMPL's verbatim header cells
  (invented values) and end to end through the frozen ZZFX BIFF exports with SMPL's shape written
  into every statement (each latest read equal to the unedited bundle's); NEGATIVE — five
  unregistered undated labels (a near miss, a case change, the `FYC` a data cell carries) still
  "unplaced", the same e2e shape under `Fiscal Period Change` refusing every reader and the bridge,
  the growth break shown absent without a marker, three CS Summary refusals kept; the bridge's
  four unbuilt reasons; the corpus census as a check.

**BOUNDARY.** Census: every Financials export on the Drive at 2026-11-04 — 74 current in 37
folders and 26 archived in 13; the period and balance-sheet header rows of 909 sheets, 21,565
non-empty cells, Key Stats (headers suffixed `A`/`E`, read by no reader) and the Capital Structure
Details instrument table excluded: 17 undated cells, all SMPL's, all `Fiscal Year Change`. The
brief's statements-only count reproduces: 222 statement sheets, 4,983 cells, 6 undated, all SMPL.
The 13 / 18 reader counts are this branch's readers on SMPL's 2026-11-04 export, 2026-11-04.

**ITEM 4 — MEASURED, NOT BUILT: which history statistics on SMPL's page reach across the change.**
On the 2026-11-04 export, at this branch. Two different things sit before SMPL's change: the
SPAC's December calendar (BEFORE the marker: Dec-31-2016, and quarters Sep-30-2016, Dec-31-2016,
Mar-31-2017 — revenue `-`, EBIT −0.7) and the Atkins predecessor's August years (AFTER the marker,
on SMPL's own calendar: FY15, FY16, and FY17 to the 2017-07-07 merger close). The marker separates
calendars, not entities.

| statistic | reaches before the change? |
|---|---|
| own-history EV/EBITDA and P/E bands, `ev_ebitda_percentile`, `range_position`, `midcycle.multiple_anchor`, `forward_multiple_history` | **No.** The two pre-merger Multiples closes (2017-03-31, 2017-06-30) read NM; the first close in a band is 2017-12-29 (36 closes, 8.85y). |
| ex-lease band (SMPL's R1 history series) | **Shrinks, nothing mixed.** Its LTM EBITDA is four quarters by DATE order, and the SPAC's Dec-2016 / Mar-2017 quarters now interleave with the predecessor's: the 2017-08-26 and 2017-11-25 windows are refused (35 valid from 2018-02-24, against 36 from 2017-08-26 on the replaced 2026-10-28 export, whose first window was three predecessor quarters and one successor). |
| annual financial summary (Appendix + JSON; the Brief shows FY23–FY26) | **Yes.** Columns FY16 (SPAC), FY15, FY16 (R), FY17 (R); one growth cell spans pre-merger years (FY17 (R) vs FY16 (R)); `FY16` is two different years. |
| quarterly summary (JSON; the Brief shows the trailing 8) | **Yes.** 43 columns; the first 6 are SPAC or predecessor quarters and the 7th (to Aug-26-2017) straddles the merger close, as FY17 (R) does; `Q1-17` is two different quarters. |
| return ratios table (prints every column) | **Yes.** FY16 (SPAC), FY15, FY16, FY17 — out of date order, `FY16` twice. |
| margin trend, multi-year trajectory | **Yes, predecessor only.** 12 points from 2015 (the SPAC column has no revenue/EBITDA and drops out); ROIC from 2017. |
| historical forecast error | **Predecessor year.** Fiscal years from 2017, mostly predecessor. |
| anchor's mid-cycle margin | **Not CIQ.** EDGAR's median over 8 FY of SMPL's own filings; outside this measurement. |

**PROPOSED TO THE OPERATOR (a ruling, not a build):** (a) CUT the old calendar — every column
before a registered fiscal-year change — from every history statistic and table: on SMPL it carries
no operating data, and it is what makes labels collide (`FY16` ×2, `Q1-17` ×2) and breaks date order;
mechanically it is `calendar_segments` applied at the readers above. (b) LABEL, not cut, the
predecessor years after it: no CIQ cell marks a predecessor/successor boundary, so cutting them would
need a hand-entered merger date per name; labelling them "predecessor (pre-2017-07-07)" from a
per-name note is the smaller change. Recommendation: (a) now, (b) only if a second name needs it.

**WHAT IT COSTS / WHAT IS ACCEPTED.** A NEW undated header shape still refuses every latest read on
its page until it is registered here by a reviewed edit — deliberately: the alarm is the corpus
census test, which goes red on the export that carries it, before any page is built on it.
FALSIFIER: an export where a registered marker sits in a header whose LATEST column is on the old
calendar (the latest date before the marker) — `latest_cell` would still serve it as the latest,
since it reads by date; none exists in the corpus.
