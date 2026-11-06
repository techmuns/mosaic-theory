---
status: open
date: 2026-11-06
prs: []
supersedes:
superseded-by:
---

# The fact layer's labels describe and never judge (fix 3a): five labels the code wrote as conclusions now state what was found, in code; no committed page carries them until it is rebuilt.

**THE RULING.** Operator, 2026-11-06: **"Start the label fix"**, after the 2026-11-05/06 fidelity
diagnosis (644 synthesis claims on the 28 pages double-coded: 43.9% misread a fact, 18.2%
materially; the largest material class, LABEL, is the model repeating a misleading label the CODE
wrote). #920's pre-registered test proved the mechanism on one label
(`2026-11-05-nflx-synthesis-causality-test.md`): its neutral drawdown wording cut "bleed"/"gradual"
from 5/5 draws to 1/5 (p = 0.048). Fix 1 (signed material figures, #921) is merged. This is fix
3a, the text of five labels; 3b (conflicting and stale values) follows its review, and the
prompt's rules (7, 7b, 8, the follow ASK) are fix 4 — not touched here.

**WHAT.** Every change is to a string the fact layer writes; no figure moves.
1. **Drawdown shape** (`mechanical._CURRENT_WORDS.none_shape`): a rolling window with no
   single day of -10% or worse read "gradual bleed — no discrete gap-down detected", rising
   windows included. It now reads #920's tested words, **"no single-day drop of -10% or worse in
   the window (detector threshold -10%)"**, the percentage read off `GAP_DOWN_THRESHOLD`. The
   dated at-anchor and since parts already said "no discrete gap-down — no single day of -10% or
   worse from A to B" and are UNCHANGED: a later build must not change the at-anchor part (#906),
   and SMPL's committed parts rebuild byte-identical (pinned). Both renderers fall through to the
   one-line fact for any shape not in the "discrete gap-downs —" form, so neither changes.
2. **Trailing EV/EBITDA note** (`mechanical.ev_ebitda_note`, the ONE rule `_valuation` and
   `cli`'s `own-history-refresh` both apply). "trailing only — no forward basis; cannot
   distinguish…" (`TRAILING_ONLY_NOTE`, text unchanged) fired whenever the
   GUIDANCE-adjusted forward figure was absent. It now stands only where none of three CIQ forward
   sources holds a multiple: `valuation.forward_multiples` (consensus forward P/E), the name's
   numeric NTM cells on the comps sheet (`ciq_sheets.comps_ntm_multiples`, printed in
   `peer_comps.trading_multiples`), and `forward_multiple_history`. Otherwise the note states the
   absence and where the forward multiples are, e.g. LLY: *"no guidance-adjusted forward
   EV/EBITDA; CIQ consensus forward multiples on the page: forward P/E
   (`valuation.forward_multiples`); the name's NTM TEV/Rev, NTM TEV/EBITDA, NTM P/E
   (`peer_comps.trading_multiples`); the EV/NTM Revenue, EV/NTM EBITDA, EV/NTM EBIT, P/NTM EPS
   history (`forward_multiple_history`)"*. The peer-comps NTM cells are in the facts the synthesis
   reads; `forward_multiple_history` sits beside them (#673, #676), named for the human page. A
   page with the guided forward keeps no note, as before. Rule 7b's text is not edited.
3. **Survival read** (`mechanical._survival_capacity`, copied to `leverage_survival.survival`):
   "(cash not derived — a risk)" → "(no runway derived: this block reads no cash balance)";
   "FCF sign UNKNOWN — runway not assessable (a risk)" → "FCF sign UNKNOWN (<the field's own
   reason>) — runway not assessable"; "— solvency risk" → "— leverage not assessable".
   "FCF-positive → self-funding" is item 7's (3b) and is unchanged.
4. **Peer-delta question** (`ciq_sheets._comps_deltas` → `_peer_gap_question`): every page asked
   whether "the discount" is EARNED (worse fundamentals). The direction is now the sign of each
   cross-sectional gap as the headline prints it (whole percent; one computation,
   `_peer_gaps`, which `cross_sectional_valuation` now prints from, byte-identical): "the
   premium … (better fundamentals)", "the discount … (worse fundamentals)", "the premium on
   EV/EBITDA and the discount on P/E … (by the fundamentals)" where they differ, the multiple named
   where only one is known, and "is any gap to the peer median EARNED …" where none is.
5. **Catalyst print row** (`mechanical._drawdown_guide_print_tests`): "the committed revised
   outlook (… the print is the checkpoint that confirms or refutes it)" on a guide the prompt marks
   SUPERSEDED. The row now LEADS with the same `guidance_vintage_mark` the prompt puts on that
   field (one derivation: the release carrying the guide's accession, the newest guide-bearing
   release), drops "committed", and keeps the checkpoint clause only for a CURRENT or undated guide.
6. **The lint** (`tests/test_descriptive_labels.py::test_no_judgment_word_in_the_fact_layers_prose`):
   no string the fact layer can write — every non-docstring, non-regex string constant in
   vinci/dossier, vinci/edgar and the three field builders outside them that
   `test_extraction_version_drift` watches, less `synthesis.py` (the prompt, fix 4) and
   `verdict.py` (the lean vocabulary) — carries a word of a closed judgment list ("a risk",
   "solvency risk", "bleed", "bearish", "bullish", "red flag", "concern" other than going-concern,
   "alarm", "worr…", "distress", "value trap"). It caught this build's own first version-row text,
   which quoted the old words.

**WHY.** The machine assembles and cites; it never concludes (CLAUDE.md). Each of the five was a
conclusion the code wrote into a fact: a decline claimed of a name that rose, a blind-flag on a
multiple with three forward cross-checks, a verdict on an unknown, a discount assumed of a premium,
and a superseded guide called committed. #920 showed the model copies such a label into its prose.

**HOW VERIFIED.**
- **Pins that fail first on main** (`tests/test_descriptive_labels.py`, fixtures
  `tests/fixtures/descriptive_labels/`): every pin drives the production entry point —
  `_drawdown_cause` on the page's own closes, the prompt `synthesize` sends, `_valuation`,
  `own-history-refresh`, `_survival_capacity`, `peer_comps`, `_catalyst_calendar` — on values
  frozen from the committed pages at main `bcda7ce3` and four (now seven) real CIQ comps sheets cut
  through the real decode path, each reproducing its page's committed cross-sectional and
  fundamental-delta lines byte-for-byte. The counts on main are in the PR body. Each fix has its
  negative: a window with gap-downs (SMPL's April), the dated parts, a page with no forward
  multiple at all, a guided-forward page (VRRM), a positive FCF (AORT), a discount on both
  multiples (PARR), the unchanged statistics, a CURRENT guide.
- **The lint on the live tree** found four strings on main `bcda7ce3`, all in `mechanical.py` —
  the "gradual bleed", the two "(a risk)" and "solvency risk" — and nothing else; zero after.
- **Before/after over all 28 committed pages, $0** (the table is in the PR body; the script and
  its output are in the session scratchpad, not committed). Items 1, 3 and 5 are recomputed from
  each page's own committed structured fields; items 2 and 4 read the name's NTM cells and the gap
  signs from the page's own CIQ comps export, accepted only where that export reproduces the
  committed `trading_multiples` / `cross_sectional` lines byte-for-byte (24 of 28 do; AORT, BURL,
  MCK and NCNO's exports on disk are not the ones their pages were built from).
- **The $0 pre-spend check** (`prespend.run`, what `vinci dossier precheck --ticker <T>` runs) on
  a sample, with the five labels printed from the page it built: in the PR body.

**MEASURED, ON THE 28 COMMITTED PAGES (main `bcda7ce3`):**

| item | pages that move | detail |
|---|---|---|
| 1 drawdown shape | 18 | 12 of the 18 rose over their detector window (MCK +45.3%, LLY +36.6%, V +28.3%; AMZN, GOOGL and SMPL within +1%); 0 had a -10% day on the detector re-run over the page's own closes |
| 2 trailing note | 24 | every page with a PRESENT trailing EV/EBITDA and no guided forward; all 24 carry the forward history, 18 a forward P/E too, and the 20 whose export is on disk numeric NTM cells; 0 stay "trailing only"; VRRM (guided) unchanged; FUBO, ORKA, TECX have no PRESENT multiple |
| 3 survival read | 9 | 7 negative-FCF pages (AMZN, FUBO, ORKA, TECX, VITL, WERN, WLK), 2 unknown-FCF (IT, LLY); each twice, the block and its copy; 0 carried "solvency risk" |
| 4 peer question | 16 of the 24 recomputed | premium on both 5 (LLY, NKE, ROST, TJX, V); mixed 3 (BRBR, GOOGL, TGT); one multiple named 5 (CNXC, MVST, SMPL, WERN a discount on EV/EBITDA, WLK a premium); none 3 (FUBO, ORKA, TECX); the 8 at a discount on both unchanged; AORT, BURL, MCK, NCNO not recomputed (export not the page's own) |
| 5 print row | 3 | BRBR, VITL, VRRM, each guide SUPERSEDED by a later one |

**WHERE THIS DIFFERS FROM THE BRIEF'S COUNTS** (each measured here, boundary below):
- Item 1: 18 pages, not 17; **12** with a positive window move, not 8. The brief's ORKA +161.8%,
  TGT +69.8% and LLY +57.4% are each page's 251-point (~1-year) price series, not the detector's
  180-day window (+4.4%, +18.5%, +36.6%). Six final syntheses carry "bleed" (BURL, NFLX, NKE,
  SMPL, TJX, UBER), not five: SMPL's page was re-assembled on 2026-11-04 (#914).
- Item 2: 24 pages, not 17 — the 17 matches no field measured here (18 carry
  `forward_multiples`).
- Item 5: 3 pages, not 4: SMPL's rolling window holds no drawdown guide since #914; its April
  guide sits in the at-anchor part, which the print row does not read.

**BOUNDARY.** Population: the 28 `data/dossiers/<T>/dossier.json` at main `bcda7ce3`, unit pages.
Item 1's window: the detector's 180 days ending on `drawdown_cause.gap_window_end` when set (MCK,
NFLX, SMPL), else on the page's reference date; the move is first close in it to last, from the
page's rebased daily `stock_performance` series; "-10% day" is `detect_gap_downs` re-run on those
closes. The synthesis count is a case-insensitive "bleed" in the committed `synthesis` JSON (LLM
text, measured, never pinned). Item 4's directions are the whole-percent signs `_peer_gaps`
computes. The pre-spend sample's date and exports are in the PR body.

**WHAT MOVES, AND WHEN.** No committed page is re-written (no LLM call, no paid assembly). Each
page picks the labels up at its next assembly; 28 of 28 move on at least one item (the list is in
the PR body). Row 52's NFLX rebuild, owed once after the prompt fixes, carries items 1 and 2.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The lint is a closed list.** It refuses only a word it names; a judgment word not on it
  passes. It reads code, not pages: an LLM-written string, a verbatim quote and the rendered
  furniture (render.py) are outside it by construction.
- **The note names `forward_multiple_history`, which the synthesis does not read.** The pointer
  it can follow is the peer-comps NTM; the history is named for the human page.
- **Found, not fixed (out of scope):** (a) the ranker's own character label "grind/bleed — no
  discrete gap-down" (`vinci/rank/ranker.py:234`) labels the ranked queue
  (`data/snapshots/ranked_queue.jsonl`), reaches no page and no prompt, and is coupled to
  `_CHAR_BLEED` and `frontend/views/edge2/ranker.js`'s `/grind|bleed/` — a ranker change; (b) the
  print row with no drawdown guide still reads "the next reported quarter against the committed
  trajectory" (25 of 28 pages), a "committed" with no referent; (c) "FCF-negative → burning cash"
  and "FCF-positive → self-funding" stay — the second is 3b's item 7.
