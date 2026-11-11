---
id: 2026-11-11-fix2-rg-d1-d7-one-figure-model
status: shipped
date: 2026-11-11
prs: [1018]
supersedes:
superseded-by:
---

# Fix request 2, RG-D1 to RG-D7 (with the prompt fixes 2 and 5): the claim trace reads one figure model — a figure traces only to one cell of its cited fact that agrees with it on magnitude to its written precision, unit and sign, under the period and on the table row its clause names; durations, the three unbound fields and call-cited figures are traced too; the primary-source digest prints its units — in code, no page carries it until it is re-assembled

**WHAT.** TeamNostra's fix request 2, order 4, "Synthesis and driver checks" (document 15 §3; the
group G notes, `notes/G.md` §5 of the fix pack): `vinci/dossier/synthesis._validate` traced a
synthesis figure by magnitude alone, at nine scales, within 2% or 0.05, against every number of the
cited fact's subtree. Now ONE figure model reads both sides — a claim's figure (`_ClaimFigure`) and
a fact's cell (`_Cell`) come out of one reader (`_figure_at`), and a figure traces when one cell
agrees with it on every axis its writing states (`_trace`):

| ID | Defect (G notes) | Now |
|---|---|---|
| RG-D1 | sign ignored: "+$198.8M" profit for a −198.8 loss | a written sign, or a change word beside the figure ("rose", "down by", "a 27% decline"), must match the cell's sign or its own words; a charge's sign ("a −$331.0M writedown") is a convention and is not compared |
| RG-D2 | unit ignored: "$29.1M" and "29.1x" for a −29.09% return | a percent meets a percent or a fraction, a multiple a multiple, money and counts are read in raw units, thousands, millions or billions; a cell's unit comes from its table row's label, its field name (`ev_ebitda`, `ebitda_margin`) or its own text |
| RG-D3 | a cited fact is its whole subtree (the annual table: 315 numbers; 78.3% of random $M figures traced) | each number is a CELL with its table row and column period; a period the figure's clause names excludes cells of other periods; a table row its subject names excludes the table's other rows |
| RG-D4 | any figure of 0.05 or less traces | no floor: magnitude within half a unit of the figure's last written digit; a stored value is exact; a text cell is as precise as its own writing |
| RG-D5 | "47 months", "95 days" never traced | a duration is a figure unless the words around it make it a window ("over the past 12 months", "180 days ago"); hyphenated and "y" forms stay labels unless they name a stated length ("an 83-day DSO", "the band spans ~9y") — closes STATE row 45 |
| RG-D6 | figures in `key_unknowns`, the decisive question and `evidence_balance` never traced | traced against every cell of the page (weaker than a point's trace, measured below) |
| RG-D7 | a call-cited figure gets a QA note the page hides | it traces only to a CHECKED figure of that call's driver rows (`DriverFigure`, or for a row built before those existed its value and quote — never the paragraph after the quote); otherwise it is an Untraceable caveat the reader sees |
| fix 5 | every claim bound to a fact the page carries | for figures, no route skips the trace any more (RG-D5, RG-D6, RG-D7) |
| fix 2 (part) | digest figures without their structured unit or sign | the primary-source digest prints each level guide's unit (`GuidanceItem.unit`), each event impact's $M, and a reconciliation's stated change |

Each caveat says why where a cell came close ("the cited fact states it with the opposite sign
(−155.9 on Net income ($M))", "… for another period, not FY2025", "… on another line, not EBITDA
($M)"), and `flags.revoice` names the three unbound fields in plain words.

**WHY.** The trace is the only check between a synthesis figure and the page's value (G notes §3,
Question 15). The 644-claim diagnosis found 43.9% of claims misread a fact; a trace that passes a
flipped sign, a wrong unit or another year's value lets the misread reach the reader as a cited
figure. The rules were chosen by face validity on the corpus (below), never on forward returns.

**HOW VERIFIED.** All at $0; the trace runs after the draw is chosen and moves no lean, no proposal
and no ledger row (`synthesize`: `_validate` runs on the kept draw).

1. **The G notes' own constructed replies, on their own input** (`tests/fixtures/frozen_pages/
   2026-08-18/SMPL/dossier.json`): all 13 point replies and the 3 unbound-field figures give no
   reader-visible caveat at main `c0d6d830` (the transcript one a QA note) and exactly one each on
   the branch; the four true controls (FY25 revenue $1,450.9M, a loss of $198.8M, fell 29%,
   −29.1%) give none at either.
2. **Random dollar figures** (the G notes' `demo_trace_rate`, seed 20261109, 2,000 figures
   $1.0M–$100,000.0M at 1 dp), on the same page: against the annual table main traces 1,567
   (78.3%, the G notes' figure exactly), the branch 141 (7.0%, chance hits on the table's small
   exact cells — capex −1.5, restructuring −0.3), and 0 when the claim says "FY25 revenue";
   against the one-number return fact 49 (2.5%) → 0.
3. **End-to-end pins on the panel's frozen SMPL page** (`synthesis_panel.json`'s freeze
   `bcda7ce3`, a git blob): `tests/test_figure_trace_fix_request_2.py` — each defect's constructed
   reply with this page's own values, each with its true control; RG-D6 and RG-D7; the random rate
   (136 of 2,000 here, 0 when named); the reader's rules one by one, positive and negative. FAILED
   at main: 34 nodes across the new file and the rewritten pins below (run with main's
   `synthesis.py` and `flags.py` in this tree).
4. **The corpus, before any synthetic** — the 28 pages at the freeze, their own committed
   syntheses (1,723 figures in bull, bear and decisive-evidence points): trace flags 347 at main →
   413. Of the 94 new: 33 are figures cited to a call that no checked figure of it states (the 26
   hidden TRANSCRIPT-FIGURE notes, now caveats, and 7 that traced only through the paragraph after
   a quote or another number of the call's text); the rest name their reason — a figure the cited fact does not state to its written precision
   (PARR's "$1,333.5M" where the fact states $1,332.1M; IT's "9.3-year" span where it is 9.2;
   LLY's ROIC cited to the annual table), another period (Visa's "+17% in Q2" matching a different
   metric of Q3), or another row. 0 are refused for their sign. Two of main's flags no longer
   fire: BURL's "fell 24%" (−23.5%, a true rounding) and WERN's "(14x)" span (a collision with the
   13.5x peer median at the half-unit boundary, below).
5. **The 190 stored panel draws** (`synthesis-eval-*/run-*/draws.jsonl` in the session notes, each
   validated against its page's freeze layer; 15,295 figures): 2,076 → 2,912 trace flags; of the
   426 no longer raised, 351 are the hidden transcript notes (now 455 call-cited caveats), 37 are
   relabels (a range's second figure "−10" now "10", still flagged), 36 are labels no longer read
   as figures (bare years "until 2028", form names "8-K", "0 up"), and 2 trace now: BURL's "~24%"
   (a true rounding) and NFLX's "18" against a 17.51 (a collision, below). Every looser rule the
   first cut had that admitted a coincidence on these draws was closed before this measurement:
   a hedge widens a figure only as far as its trailing zeros say it was rounded, a bare single
   digit meets only a whole number, extra precision over a text cell only in that cell's unit, and
   a scaled money amount sits at most 5% from its cell.
6. **The gold's DEV half only** (14 pages AMZN…NFLX, the 197 bull and bear claims the coding
   names; the TEST half not read): flagged at main / branch — SIGN 2 / 3 of 3, PERIOD 2 / 3 of 3,
   UNIT 1 / 1 of 1, ABSENT 9 / 13 of 19, all error classes 42 / 51 of 82, and claims coded OK 40 /
   51 of 115. The OK claims flagged are figures their cited fact does not state (EPAM's LTM revenue
   cited to a call, GOOGL's Q3 revenue cited to the multi-year table) or call-cited figures from the
   paragraph after a quote: true by the trace's per-fact rule, which is narrower than the coders'
   "consistent with the page". On the unbound fields (DEV key unknowns, questions, balances), 0 of
   63 OK units flagged, 1 of 26 ABSENT.
7. **The $0 panel compare** (`python -m vinci.evals compare --base origin/main --cand <branch>`):
   BURL, CNXC, LLY and SMPL differ in the primary-source digest only (+35, +66, +3, +60
   characters); MCK and ROST are byte-identical; every SYSTEM prompt is equal. The diff is the
   intended lines: "guidance (revenue 2026): 80000.0–83000.0 $M", "reconciliation (adjusted ebitda
   Q4 2026): 57.5 (-13.2%)".
8. **Pins that encoded the defects**, rewritten with the reason in each docstring:
   `test_dossier.py`'s two transcript-route tests (G-D7's soft note), the rank test's {0, 2, 5,
   18} (→ {2}: 0, 5 and 18 traced through RG-D4/RG-D2 coincidences), "the band spans ~9y" (a
   label → a figure), "5-10%" (the dash no sign), the G-D6 draw's 195 of 199 (→ 199), and two
   footnote-position tests whose claims RG-D1/RG-D2 now refuse for a second reason.

**BOUNDARY.** Freeze `bcda7ce3` (the 28 `data/dossiers/*/dossier.json` there); main `c0d6d830`,
branch head `7de1a7d3`; "figures" are the numbers `_claim_figure_ends(durations=True)` reads in
bull, bear and decisive-evidence points; "trace flags" are UNTRACEABLE, UNDERIVED and
TRANSCRIPT-FIGURE flags of `_validate`; the 190 draws are every line with a `raw` in the four
`draws.jsonl` of `synthesis-eval-pr2`, `-fix3a`, `-fix4a` (panel pages BURL, CNXC, LLY, MCK, ROST,
SMPL and NFLX's ten), validated against the freeze layer (a CAND arm's transform is not re-applied:
an approximation for those arms); random rates are 2,000 figures (seed 20261109) per point fact and
300 figures (seed 20261111) per page pool; the gold is `tests/fixtures/synthesis_gold/` final labels.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **More caveats on the next builds.** On the freeze syntheses, +66 trace flags over 1,723 figures
  (+3.8 points); on the draws, +836 over 15,295. No committed page moves until it is re-assembled.
- **A whole-number collision survives** (WERN's "14x", NFLX's "18"): a figure written to the unit
  is ±0.5 at its own precision, and a large fact can hold an unrelated number that close. A
  tighter tolerance refuses true roundings ("fell 24%" for −23.5%). Falsifier: a coded sample of
  traced whole-number figures with more than one in twenty bound to the wrong cell.
- **RG-D6 is weak where no table row is named**: against a whole page 41–79% of random one-decimal
  percents and 26–35% of random $M figures pass (BURL, CNXC, LLY, MCK, ROST, SMPL at the freeze).
  Two stricter pools refused real figures (named metrics held to the page's labelled lines: about
  thirty true key unknowns on the freeze pages — ratios sitting in unlabelled fields beside a named
  row; the field held to the facts its points cite: 135 of 375 real figures). Binding these fields
  for real needs a footnote on them — a schema and prompt change of its own, proposed below.
- **A period is read where it is written**: a figure's clause names it, or nothing is checked; "In
  FY25, revenue was $1,168.7M" (the period in another clause) still passes. Precision over recall.

**NOT DONE, AND WHY** (each the PR's disposition table):
- **Fix 2, the drivers digest** (prints `value`, ignores `value_num`; no period): it is in
  `synthesis.prompt_driver_value`, which #1006 rewrites (committed transcript rows lose their
  `value`). Done after #1006 merges, as the brief orders.
- **Fix 2, a reconciliation's unit**: `ReconciliationValue` has no unit field (its comment states
  "$M (or $/share for EPS)"; a gross-margin reconciliation prints "34.0"); adding it edits
  `schemas.py` and `release_parse.py`, both on A's unmerged `claude/fixreq2-e2-remainder`.
- **Fix 2, the surprise "+0%"**: CIQ writes 0.0 where it computed no surprise — BURL's FY2021
  GAAP-EPS surprise cell is 0.0 while its own rows state actual −3.28 against estimate −3.40 — and
  `ciq_sheets.surprise_history` prints `{v:+.0%}`, so "+0%" reads as a met estimate. It is a CIQ
  reader fix in the facts, with its own CIQ fixtures and a page rebuild; proposed as its own build.
- **The paid panel check** for the request move (proposed, not run): one no-worsening registration
  on the panel once the drivers-digest part lands, so a single run measures all of fix 2, under
  the harness rules on `main` then (S1's committed index and held-out pages); about $30 (fix 3a
  $30.72, fix 4a $30.31 for 60 draws), cap $40. The digest move is not a FACTS-section move, so the
  2026-11-11 FACTS-only ruling is not assumed to cover it.
