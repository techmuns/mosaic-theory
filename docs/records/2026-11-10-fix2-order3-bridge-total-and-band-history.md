---
status: shipped
date: 2026-11-10
prs: [960]
supersedes:
superseded-by:
---

# Fix request 2, order 3, three of document 11's partly fixed items finished (A-D2, D-D3, BC-D10): the EV bridge's note says what its claims total leaves out and whether anything checks it; the mid-cycle multiple band is the own-history band's population, so an export-day close is no longer history; one anchor-bridge figure a unit step from its own parts is refused, not scored "agree". 13 committed bridges gain the note when refreshed; no committed page carries a mid-cycle band

**WHAT.**
- **A-D2's remainder** (`ciq_sheets.ev_bridge`, through `claims_left_out_note`). #877 made an
  unread preferred or minority leg `unread` with its reason instead of a 0.0 line. But `claims`
  still summed only the legs CIQ states, and nothing at bridge level said so. The verifier's
  case: ORCL's quarterly total read 136,086 with 'Total Pref. Equity' at '-', against 141,040
  with the cell read. The note now names each leg left out, with its reason, and says what
  checks the total:
  - CIQ's current TEV less market cap counts every claim: when it agrees, the note says so;
  - when it disagrees, the note says so beside the existing DISAGREES line;
  - with no comps export, nothing checks the total, and the note says that.
- **D-D3's remainder** (`midcycle.multiple_anchor`). #872 refused an NM latest close, but the
  band still took every close, the current one included. The verifier measured 39 closes
  against `own_history_bands`' 38. The current column is the export day's close (AMZN's export
  of 2026-09-16 adds one), which the quarter has not completed, and contract §4.2 leaves it out.
  The band is now the own-history band's population: every dated close before the latest. A
  sheet whose closes carry no date builds no band, as `_own_history_band` builds none.

- **BC-D10's remainder** (`ciq_balance._unit_steps`). #863 made the anchor bridge read each
  statement's unit line. Its magnitude band against revenue, [1e-4, 1000]x, is seven orders
  wide, so one cell divided by 1,000 sits inside it. The verifier's case: ORCL's cash ÷ 1000,
  every unit line stating Millions, gave `ok True`, outcome `agree`. Each bridge figure is now
  re-read from its own parts: cash and total debt from their balance-sheet rows at the same
  column, D&A, operating cash flow and capex from the four quarters ending on the annual column.
  One a unit step from its re-read (within 2× of 1,000× or 1,000,000×, either way) is a SCALE
  failure, so the bridge is refused and the outcome is `differ`.

**WHY.** Document 15's Appendix A lists all three as partly fixed:
- A-D2: "the claims total still omits the unread leg, with no note at bridge level".
- D-D3: "the incomplete last column still enters the mid-cycle band".
- BC-D10: "the magnitude band is unchanged, so one figure 1,000× off still scores agree".

**HOW VERIFIED.**
- **Fail first.** Run against `origin/main`'s `vinci/` from the primary checkout's licensed
  folder: `tests/test_bridge_total_and_band_history.py` 4 of 4 fail;
  `tests/test_ciq_bridge_unit_step.py` 6 of 7 (the pass is the corpus negative). AMZN's band reads
  (39, 24.334641) against the own-history band's (38, 24.394374).
- **The old pins.** Two pins in `tests/test_midcycle.py` pinned the defect (the current close
  counted) and are restated.
- **The frozen bridge cases.** `tests/fixtures/ev_bridge_cases.json` is re-derived by
  `claims_left_out_note`, the function that writes the note: 8 of 8 cases carry an unread leg.
  FUBO's and MVST's exports on disk are the frozen ones, and their live reads equal the
  re-derived cases.
- **Page impact, read from the committed JSON.** 13 of the 26 committed bridges carry an unread
  leg: AMZN, EPAM, GOOGL, LLY, MCK, NFLX, SMPL, TECX, UBER, V, VITL, VRRM and WLK (FUBO's page
  carries no bridge). Each gains the note when its bridge is next written. The bridge is
  printed on neither the page nor the web, and is not in the synthesis request
  (`Dossier.ev_bridge`, not the mechanical layer), so no `.md`, no request and no panel moves.
  No committed page carries a mid-cycle band (0 of 27).

**BOUNDARY.**
- Bridge counts: the 27 committed `data/dossiers/*/dossier.json` at `9da0d096`, by
  `ev_bridge.lines[*].unread`.
- Band counts: the exports on disk under the primary's `data/manual/ciq/` on 2026-11-10.
- Frozen cases: `tests/fixtures/ev_bridge_cases.json`, 8 cases.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The bridges are refreshed in a later page pass, not here.** `refresh.ev_bridge_transform`
  writes the note at $0 only where the page's own exports are on disk. Driver facts PR 3 also
  rewrites every page's JSON, so the pass runs after it merges. Pages whose exports were
  re-exported since their build carry the note only from their next assembly.
- **BC-D10: why a re-read and not a band.** The corpus rules out a band. Of 176,052
  consecutive non-zero period pairs on the 36 Financials exports, 201 step by within 2× of
  1,000× or 1,000,000×, 9 of them on rows the bridge reads, all real (SMPL's 2016 stub-period
  Total Debt, 333.0 → 0.19 → 192.1; EPAM's, MNST's and NKE's quarterly operating cash flow).
  Against its own parts, every bridge figure re-reads within 0.93–1.36× (cash and total debt
  exactly; BDX's flows read three quarters), none near a unit step. A figure with no re-read
  (no quarterly export, no part valued) is still screened by the band alone. Falsifier: a real
  export whose re-read is a unit step from its figure.
- **Extraction version** `2026-11-10.bridge-total-and-band`; the drift pins are re-pinned.
## Amendments

- **2026-11-12 — what this PR's next build changes, from A's impact sweep** (operator ruling 3, 2026-11-12, verbatim: "Yes, as appended amendments (Recommended)"). The body above is unchanged. A re-ran this PR with `vinci.impact`: base code against head code on the same inputs, which shows what each page's NEXT build would change (A on #1004, 2026-11-12 09:51Z, 40 of 49 PRs covered: https://github.com/techmuns/mosaic-theory/issues/1004#issuecomment-6820345324).
  - **#960:** the bridge note reaches 27 pages, not 13. The body says "13 of the 26 committed bridges".
  - The figure is A's, from that comment; S4 did not re-run the sweep. The sweep's own record, with all 49 rows (base, head, coverage, moves and each body's claim), follows.
