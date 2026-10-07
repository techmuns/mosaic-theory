---
id: 2026-10-07-forward-multiple-history
status: shipped
date: 2026-10-07
prs: [676]
supersedes:
superseded-by:
---

# The forward multiples get their history — EV/NTM Revenue, EBITDA and EBIT, with P/NTM EPS as context only, outside the synthesis

**WHAT.** A new dossier-level field, `forward_multiple_history`. One builder,
`ciq_sheets.forward_multiple_history`, serves both assembly and a refresh step. It covers four
rows of the quarterly Financials→Multiples export, each matched by EXACT label:

| metric | sheet row |
|---|---|
| EV/NTM Revenue | `TEV/NTM Total Revenues` |
| EV/NTM EBITDA | `TEV/NTM EBITDA` |
| EV/NTM EBIT | `TEV/NTM EBIT` |
| P/NTM EPS | `P/NTM EPS` |

Each series carries:
- **`points`** — every dated Close, in time order. A cell that is not a number keeps what it said:
  'NM' or '-'.
- **`band`** — the current close against its own history, from `_own_history_band`, the same
  helper as the trailing bands.

P/NTM EPS carries `context_only` and a note that cites the 2026-09-03 ruling. The layer also
carries `withheld` (every band not written, and why), `as_of`, and the export's file name and
sha256.

`forward_multiple_history_transform` lands the layer on a committed page. It does so only when the
page's trailing bands name the export on disk: their stored `source_sha256` must be that file's.
**This PR changes no committed page.**

**WHY.**
- The quarterly Multiples sheet has 14 series, and the page kept two: trailing EV/EBITDA and
  trailing P/E. Today's FORWARD levels were on the page (Estimates→Multiples) but not their
  history. That was item B1 of the analyst team's AMZN feedback (2026-10-07).
- RUNBOOKS step 10's R3 method uses the forward history as a corroborator. Own-history quartiles
  and the EV/NTM EBIT cross-check test whether today's anchor is distorted; they never generate a
  leg.

**THREE READ RISKS, FOUND ON THE REAL EXPORTS AND CLOSED:**
1. **Label clash.** The sheet prints `TEV/NTM EBITDA` directly above `TEV/NTM EBIT`, so a prefix
   match on the EBIT label returns the EBITDA row. All rows are matched exactly. A test shows the
   prefix read still lands wrong on AMZN, and that the layer does not.
2. **'NM' and '-' were one state.** `_multiples_close` maps both to None. Across the four forward
   rows of the 26 exports there are 218 'NM' cells (a negative or nil denominator) and 62 '-' cells
   (no figure). `_multiples_close_cells` now returns the cell as exported, and `_multiples_close`
   is that read plus `clean_num`. Its output is identical to before on every multiple row of the
   26 sheets (357 rows).
3. **An older close standing in for current.** V's EV/NTM EBIT reads '-' on its latest column
   (2026-08-07) and a number on the quarter-end before it. The shared helper refuses to backward-fill,
   so V's band is withheld and the reason says it met '-'.

**WHAT IT HOLDS, measured on the 26 names' exports:**
- 104 series, 3,296 points and 79 bands.
- 25 withheld entries. 23 are a latest close that is not a number: AORT 3, FUBO 2, LLY 2, NFLX 1,
  ORKA 4, TECX 4, UBER 4, V 1, VITL 2. The other 2 are FUBO's fewer-than-four-closes.
- Bands on 4 of 4 series for 17 names.

**THE TWO EXPORTS ON ONE PAGE ARE NOT THE SAME DAY.** The layer's `as_of` is the Financials export's
latest close, which can differ from the page's Estimates `as_of` floor by a long way:
- 89 days in the other direction (MVST: Multiples newer);
- 104 days older (VRRM);
- AMZN 20 days older (2026-09-16 against ≥2026-10-06); median −0.5 days.

The layer states its own `as_of`, so a reader does not take its 'current' for the Estimates
figure.

**A BAND SPANS REGIMES; READ THE PATH.** AMZN's EV/NTM EBIT band reads current 22.6x, median 52.6x
and percentile 0 over 38 closes from 2017-03-31 (a 9.5-year span). By calendar year the path is a
compression, interrupted in 2020, not a stable range that the current close has dropped out of:

| year | range |
|---|---|
| 2017 | 73–110x |
| 2019 | 50–62x |
| 2020 | 55–97x |
| 2021 | 48–67x |
| 2023 | 39–61x |
| 2024 | 30–36x |
| 2025 | 26–30x |
| 2026 | 22.6–24.3x |

So "0th percentile" here says the multiple sits at the low end of a nine-year de-rating. It does not
say the multiple is cheap against a stable distribution. A step-10 author must answer RUNBOOKS
class (c), the percentile extreme, from the path, not from the rank.

**HOW VERIFIED.**
- **Corpus pins, all 26 names:**
  - every point equals its exact row's Close cell. The expected value is read independently of
    `_multiples_close_cells`;
  - every band equals the shared helper's result, or is named in `withheld` with the latest
    cell's own text.
- **Observed-shape pins:**
  - the label clash (AMZN);
  - V's '-' at the latest close, gated on that export's sha;
  - ORKA's 'NM' against V's '-';
  - P/NTM EPS is the only context-only row.
- **Column order.** The same real AMZN sheet with its date columns reversed yields the same layer.
  Every committed export runs oldest to newest, so without this a dropped sort would pass.
- **The anchor still reads trailing.** `own_history_bands` carries exactly the two trailing
  multiples.
- **Refresh, end to end on AMZN.** The layer equals the builder's output. Synthesis, anchor,
  mechanical layer and rendered page are unchanged.
- **Negative pins.** Mixed stamps, foreign stamps, and no bands each leave the page alone.
- **Dry run through `refresh_dossier` on copies of all 26 committed folders:**
  - landed on 23;
  - left FUBO, ORKA and TECX alone (no stamped trailing band);
  - refused none;
  - nothing moved outside the new key, `dossier.md` was byte-identical, and `anchor` stayed last.
- **Mutation.** Eleven mutants, all killed. The no-stamp-check mutant first SURVIVED: the sha
  comparison alone refused both negative cases. It is now pinned by a page whose two bands name
  different exports.

| mutant | tests failing |
|---|---|
| prefix match | 29 |
| series keeps the band's own series | 22 |
| markers folded to 'NM' | 20 |
| backward-fill into the band | 7 |
| P/NTM EPS not context-only | 1 |
| no vintage gate | 1 |
| no allowlist | 1 |
| assembly wiring dropped | 1 |
| `null` instead of absent | 1 |
| no time sort | 1 |
| single-stamp check removed | 1 |

The CIQ-backed tests skip in CI; the licensed workbooks are never committed.

**BOUNDARY.**
- **Population:** the 26 committed dossiers on main @3b5c5262, and their on-disk quarterly
  Financials and Estimates exports.
- **Date:** measured 2026-10-07.
- **Units:** a point is one dated Close column of one row. A band is the trailing bands' own
  statistic: current = the latest dated close, excluded from history.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Three pages stay without the layer** until they are re-assembled: FUBO, ORKA and TECX have no
  stamped trailing band. FUBO's and ORKA's hash sits in a display string, and reading it there
  would be the parse-the-rendered-string class. On ORKA and TECX, every one of the four forward
  rows is non-numeric (pre-revenue), so their layer would carry no band.
- **The layer is in the JSON tier only, like `forward_consensus`.** Whether the synthesis gets a
  digest of either is the next decision (§5.0 row 30).
