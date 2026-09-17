---
id:
status: shipped
date: 2026-09-17
prs: [622]
supersedes:
superseded-by:
---

# A release figure carries the period its own text names — 34 of 43 bare-year rows on committed pages were wrong

**WHAT.** `vinci/edgar/release_parse.py::_reconciliation` labelled every non-GAAP actual, headline
revenue and gross margin with the release HEADER's period. A header naming a fourth quarter AND its
full year ("Fourth Quarter and Full Year 2025") fell through to the bare year, and every consumer
reads a bare year as a full year. It now labels each figure from evidence about that figure
(`_figure_period`), and skips a figure nothing places. `_ltm_adj_ebitda` now refuses after Q1.

**WHY IT MATTERED.** The labels are inputs, not decoration. `_fy_reconciliation` takes the first
bare-year row per metric as the full-year margin/revenue input — SMPL's Q4 $66.2M, CNXC's Q4
$378.6M, VRRM's fabricated 38.0. `_ltm_adj_ebitda` composes LTM from them. The synthesis prompt
carries each row as `reconciliation (metric period): value`. And the true full-year figure was
DROPPED: rows dedupe on `(metric, period)`, so Par Pacific's "$633.5 million for the full year"
arrived second, wearing the same label as its Q4 $113.1M, and was discarded.

**THIS WAS KNOWN ONCE AND GUARDED DOWNSTREAM.** `_ltm_adj_ebitda`'s guard (#198) quotes the SMPL
case — "a prior-year QUARTER stamped with the bare year '2025'" — and refuses a full year below one
of its own quarters. That blocked the symptom in one consumer when the full year happened to be
smaller, and left the parser, `_fy_reconciliation` and the synthesis reading the wrong labels.

**THE SHAPES, from the committed pages' own sentences** (43 bare-year rows, 10 of 19 dossiers):

| shape | rows | e.g. |
|---|---:|---|
| Q4 figure as the full year | 14 | CNXC "Revenue of $2,552.9 million" under "Fourth Quarter Fiscal 2025 Highlights" |
| year-to-date as the full year | 8 | MVST "$54.4 million in YTD 2025" |
| prior-year quarter as a bare year | 4 | WERN "$0.53 in the prior year OMAHA, Neb., February 5, 2026" → 2026 |
| truncated outlook read as an actual | 4 | VRRM "Adjusted EBITDA of $380 million to $385 million" → 38.0 |
| FuboTV letters | 4 | Q1 fiscal 2026 figures as fiscal 2026 |
| correct | 9 | VITL "Fiscal Year 2025 Net Revenue of $759.4 million" |

**HOW VERIFIED.** Real runs, not assertion:

- **Corpus before/after** over the 91 EX-99.1 exhibits the committed fleet parses, plus PARR's and
  WLK's six: 162 → 175 rows — 126 unchanged, 21 relabelled, 30 added, 17 removed. Every removal was
  classified against its sentence and every one was a wrong row. A separate scan of all 175 output
  rows for year-to-date wording, outlook lead-ins, truncated ranges and year/quarter word conflicts
  found one survivor: VRRM's Q1-2026 "adjusted eps 1.3", a truncated outlook range present before
  this change too (reported below).
- **Consumer effect** on committed pages' own release sets: the full-year adjusted-EBITDA input
  moves BRBR 117.4 → 481.6, CNXC 378.6 → 1,469.3, MVST 54.4 → 44.7, SMPL 66.2 → 278.2, VITL 29.9 →
  114.0, VRRM 38.0 → 415.9, UBER 2.5 → absent. LTM moves only for MVST (32.1 → unavailable).
- **23 tests** on real exhibit text (`tests/test_release_periods.py` + one LTM pin). Each fixture is
  real text joined in filing order at sentence/bullet boundaries, proven at generation to emit —
  for every pinned figure — exactly what its FULL filing emits, in both directions. Twice a trimmed
  excerpt removed a real sentence break and changed a label that the full filing got right.
- **19 mutations, one per rule, each killed** by the test that guards it. Two rules are defended in
  depth (year-to-date as a current figure; the clause-bounded comparison look-back); their single
  mutations are masked by the second layer, and removing both layers is killed. Mutation testing
  found two defects of this change's own that the corpus diff had not: heading words read as letters
  only ("Q3 Fiscal 2026 Highlights" became "Fiscal 2026", a full-year section — FUBO's Q1 figures
  were still filed as fiscal 2026), and a list's last bullet running into the next list's lead-in.

**BOUNDARY.** Corpus = every EX-99.1 whose accession appears in `primary_source.releases` of a
committed `data/dossiers/*/dossier.json` at `origin/main 0341af2` (91 exhibits, 19 names), plus
PARR's and WLK's 2026 earnings exhibits (6). "Bare-year rows" = reconciliation rows whose `period`
is exactly `20YY` in the committed JSON (43, 10 dossiers). Measured 2026-09-17. Values in $M or
$/share as filed.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **Committed pages still carry the wrong rows until re-assembled.** This is code only. The ten
  affected dossiers (AORT BRBR CNXC FUBO MVST SMPL UBER VITL VRRM WERN) pick it up at their next
  assembly, which re-runs synthesis — an operator decision. STATE §5.0 row 28.
- **Some correct figures are now skipped rather than labelled.** A figure in a combined release with
  no evidence of its own (VITL's "• Gross Margin of 35.8%, compared to 36.1%") is left out, not
  guessed. Precision over coverage; a header that names two periods cannot choose between them.
- **LTM is unavailable after Q1** until a multi-quarter composition exists. It was wrong there.
- **REPORTED, NOT FIXED — each its own change:** (1) `_RECON`'s `$([\d,.]+)` backtracks past its own
  `(?! … to)` guard and reads an outlook range as an actual ("$1.3⟨2 to $1.38⟩"); (2) billion-scale
  values are stored unscaled (UBER 2.5, FUBO 1.482) although `ReconciliationValue.value` is
  documented as $M; (3) `test_primary_source_assembly_mvst_live` unpacks 2 of `_primary_source`'s 3
  return values and fails on `main` — network-marked, so CI never runs it; (4) pro forma figures
  are stored under the plain metric name.
