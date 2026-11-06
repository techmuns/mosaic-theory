---
status: open
date: 2026-11-06
prs: [923]
supersedes:
superseded-by:
---

# The fact layer's labels describe and never judge (fix 3a): of five labels the code wrote as conclusions, four are deleted and one is reworded to #920's tested words; the prompt the model sees shrinks by 3,899 characters over the 28 pages, in code; no committed page carries it until it is rebuilt.

**THE RULINGS.** Operator, 2026-11-06: **"Start the label fix"**, after the 2026-11-05/06 fidelity
diagnosis (644 synthesis claims on the 28 pages double-coded: 43.9% misread a fact, 18.2%
materially; the largest material class, LABEL, is the model repeating a misleading label the CODE
wrote). #920's pre-registered test proved the mechanism on one label
(`2026-11-05-nflx-synthesis-causality-test.md`): its neutral drawdown wording cut "bleed"/"gradual"
from 5/5 draws to 1/5 (p = 0.048). The coordinator added, 2026-11-06, on the operator's question
whether the fixes just add words: **prefer deletion or shorter neutral wording; a label that cannot
be stated neutrally from structured data is removed, not explained; add no instruction to the
model; report what the model sees, per page; no name is special-cased.** And the operator ruled
**"Build it first"**: an evaluation harness gates every synthesis-prompt change, so this PR's MERGE
waits until the harness has measured it on the evaluation panel against the current baseline.
Fix 1 (#921) is merged; 3b (conflicting and stale values) follows 3a's review; the prompt's rules
(7, 7b, 8, the follow ASK) are fix 4 — not touched here.

**WHAT.** Every change is to a string the fact layer writes; no figure moves; no name is special-cased.
1. **Drawdown shape — REWORDED** (`mechanical._CURRENT_WORDS.none_shape`): a rolling window with no
   single day of -10% or worse read "gradual bleed — no discrete gap-down detected", rising
   windows included. It now reads #920's tested words, **"no single-day drop of -10% or worse in
   the window (detector threshold -10%)"** (+25 characters; the one item that grows, kept because
   it is the wording the test proved), the percentage read off `GAP_DOWN_THRESHOLD`. The dated
   at-anchor and since parts already stated the detector neutrally and are UNCHANGED: a later build
   must not change the at-anchor part (#906), and SMPL's committed parts rebuild byte-identical
   (pinned). Both renderers fall through to the one-line fact for any shape not in the
   "discrete gap-downs —" form, so neither changes.
2. **Trailing EV/EBITDA note — DELETED where a forward multiple exists**
   (`mechanical.ev_ebitda_note`, the ONE rule `_valuation` and `cli`'s `own-history-refresh` both
   apply). "trailing only — no forward basis; cannot distinguish…" (`TRAILING_ONLY_NOTE`, text
   unchanged) fired whenever the GUIDANCE-adjusted forward figure was absent. It now stands only
   where none of three CIQ sources holds a forward multiple — `valuation.forward_multiples`, the
   name's numeric NTM cells on the comps sheet (`ciq_sheets.comps_ntm_multiples`, printed in
   `peer_comps.trading_multiples`), `forward_multiple_history` — and is otherwise removed: the
   guided figure's absence is already stated on `ev_ebitda_adjusted_fwd`, and the forward
   multiples are their own facts. Rule 7b's text is not edited.
3. **Survival read — tags DELETED** (`mechanical._survival_capacity`, copied to
   `leverage_survival.survival`): " (cash not derived — a risk)", " (a risk)" and " — solvency
   risk" are removed; the leg's own field carries its reason. "FCF-positive → self-funding" is 3b's
   item 7 and is unchanged.
4. **Peer-delta question — asked only in a single direction, else DELETED**
   (`ciq_sheets._comps_deltas` → `_peer_gap_question`): every page asked whether "the discount" is
   EARNED (worse fundamentals). The direction is now the sign of each cross-sectional gap as the
   headline prints it (whole percent; one computation, `_peer_gaps`, which
   `cross_sectional_valuation` now prints from, byte-identically): "the premium … (better
   fundamentals)" where every known gap is positive, the old discount question where every one is
   negative, and no question — "[justified-vs-residual inputs: the human judges — not computed
   here]" — where they disagree or none is known.
5. **Catalyst print row — a non-current guide DELETED from it** (`_drawdown_guide_is_current`):
   "the committed revised outlook (… the print is the checkpoint …)" sat on guides the prompt marks
   SUPERSEDED. The row names the drawdown guide only when it is the CURRENT guide, by the derivation
   the prompt's vintage mark uses (the release carrying the guide's accession, the newest
   guide-bearing release), and without "committed"; a superseded or undated guide leaves the row,
   which then reads as on every page without a drawdown guide and no longer cites it.
6. **The lint** (`tests/test_descriptive_labels.py::test_no_judgment_word_in_the_fact_layers_prose`):
   no string the fact layer can write — every non-docstring, non-regex string constant in
   vinci/dossier, vinci/edgar and the three field builders outside them that
   `test_extraction_version_drift` watches, less `synthesis.py` (the prompt, fix 4) and
   `verdict.py` (the lean vocabulary) — carries a word of a closed judgment list ("a risk",
   "solvency risk", "bleed", "bearish", "bullish", "red flag", "concern" other than going-concern,
   "alarm", "worr…", "distress", "value trap"). It caught this build's own first version-row text.

**WHY.** The machine assembles and cites; it never concludes (CLAUDE.md). Each of the five was a
conclusion the code wrote into a fact: a decline claimed of a name that rose, a blind-flag on a
multiple with forward cross-checks, a verdict on an unknown, a discount assumed of a premium, and a
superseded guide called committed. #920 showed the model copies such a label into its prose.

**HOW VERIFIED.**
- **Pins that fail first on main** (`tests/test_descriptive_labels.py`, fixtures
  `tests/fixtures/descriptive_labels/`): every pin drives the production entry point —
  `_drawdown_cause` on the page's own closes, the prompt `synthesize` sends, `_valuation`,
  `own-history-refresh`, `_survival_capacity`, `peer_comps`, `_catalyst_calendar` — on values
  frozen from the committed pages at main `bcda7ce3` and seven real CIQ comps sheets (ROST, PARR,
  GOOGL, FUBO, LLY, EPAM, VRRM) cut through the real decode path, each reproducing its page's
  committed cross-sectional and fundamental-delta lines byte-for-byte. The fail-on-main count is in
  the PR body (measured on the final file). Each fix has its negative: a window with gap-downs
  (SMPL's April), the dated parts, a page with no forward multiple at all, a guided-forward page
  (VRRM), a positive FCF (AORT), a discount on both multiples (PARR, byte-identical), the unchanged
  statistics, a CURRENT guide.
- **The lint on the live tree** found four strings on main `bcda7ce3`, all in `mechanical.py` —
  the "gradual bleed", the two "(a risk)" and "solvency risk" — and nothing else; zero after.
- **Before/after and prompt size over all 28 committed pages, $0.** BEFORE is each page's committed
  mechanical layer; AFTER replaces only the five fields, each recomputed by this code (items 1, 3, 5
  from the page's committed structured fields; items 2 and 4 with the page's own comps export,
  used only where it reproduces the committed line byte-for-byte — 24 of 28 do; AORT, BURL, MCK and
  NCNO's exports on disk are not the ones their pages were built from, so item 2 is decided there
  from their committed forward history alone and item 4 is not measured). Each prompt is the real
  user message `synthesize` sends, captured by a client that records it and fails the draw.
- **The $0 pre-spend check** (`prespend.run`) on a sample: in the PR body, with the same check on
  main's code on the same data.

**MEASURED, ON THE 28 COMMITTED PAGES (main `bcda7ce3`):**

| item | pages that move | change in the prompt | detail |
|---|---|---|---|
| 1 drawdown shape | 18 | +450 (+25 each) | 12 of the 18 rose over their detector window (MCK +45.3%, LLY +36.6%, V +28.3%; AMZN, GOOGL, SMPL within +1%); 0 had a -10% day on the detector re-run over the page's own closes |
| 2 trailing note | 24 | −2,808 (−117 each) | every page with a PRESENT trailing EV/EBITDA and no guided forward; all 24 carry the forward history, 18 a forward P/E too; 0 stay "trailing only" |
| 3 survival tags | 9 | −498 | AMZN, FUBO, ORKA, TECX, VITL, WERN, WLK (FCF negative, −66 each), IT, LLY (FCF unknown, −18 each); each twice, the block and its copy |
| 4 peer question | 12 of the 24 measurable | −426 | premium 6 (LLY, NKE, ROST, TJX, V, WLK; ±0 characters), deleted 6 (BRBR, GOOGL, TGT mixed; FUBO, ORKA, TECX none; −71 each); the 12 at a discount unchanged |
| 5 print row | 3 | −617 | BRBR, VITL, VRRM: each guide SUPERSEDED, so the row reverts to the no-guide row |
| **all** | **28 of 28 on at least one** | **−3,899 of 10,075,466** | per-page table in the PR body |

**WHERE THIS DIFFERS FROM THE BRIEF'S COUNTS** (each measured here, boundary below):
- Item 1: 18 pages, not 17; **12** with a positive window move, not 8. The brief's ORKA +161.8%,
  TGT +69.8% and LLY +57.4% are each page's 251-point (~1-year) price series, not the detector's
  180-day window (+4.4%, +18.5%, +36.6%). Six final syntheses carry "bleed" (BURL, NFLX, NKE,
  SMPL, TJX, UBER), not five: SMPL's page was re-assembled on 2026-11-04 (#914).
- Item 2: 24 pages, not 17 — the 17 matches no field measured here (18 carry
  `forward_multiples`).
- Item 5: 3 pages, not 4: SMPL's rolling window holds no drawdown guide since #914; its April
  guide sits in the at-anchor part, which the print row does not read.

**BOUNDARY.** Population: the 28 `data/dossiers/<T>/dossier.json` at main `bcda7ce3`, unit pages;
prompt sizes in characters of the synthesis user message. Item 1's window: the detector's 180 days
ending on `drawdown_cause.gap_window_end` when set (MCK, NFLX, SMPL), else on the page's reference
date; the move is first close in it to last, from the page's rebased daily `stock_performance`
series; "-10% day" is `detect_gap_downs` re-run on those closes. The synthesis count is a
case-insensitive "bleed" in the committed `synthesis` JSON (LLM text, measured, never pinned). Item
4's directions are the whole-percent signs `_peer_gaps` computes.

**WHAT MOVES, AND WHEN.** No committed page is re-written (no LLM call, no paid assembly). Each
page picks the labels up at its next assembly; 28 of 28 move on at least one item. Row 52's NFLX
rebuild, owed once after the prompt fixes, carries items 1 and 2. The merge waits for the
evaluation harness (operator, "Build it first").

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The lint is a closed list.** It refuses only a word it names; a judgment word not on it
  passes. It reads code, not pages: an LLM-written string, a verbatim quote and the rendered
  furniture (render.py) are outside it by construction.
- **A deleted label is information a draw no longer gets in that place.** Each deletion's content
  is elsewhere in the same facts: the guided figure's absence on `ev_ebitda_adjusted_fwd`, an
  unknown leg's reason on its own field, the gaps' signs in `cross_sectional`, the superseded guide
  in `drawdown_cause.revised_guidance` under the prompt's own SUPERSEDED mark.
- **Two reads repeated (review of 3a, not changed):** `_valuation` builds
  `forward_multiple_history` again beside `assemble_one`'s own build of it, and
  `_peer_gap_question` recomputes the gaps `cross_sectional_valuation` already did. Both read
  cached sheets; passing them through would widen `assemble_mechanical`'s signature.
- **Found, not fixed (out of scope):** (a) the ranker's own character label "grind/bleed — no
  discrete gap-down" (`vinci/rank/ranker.py:234`) labels the ranked queue
  (`data/snapshots/ranked_queue.jsonl`), reaches no page and no prompt, and is coupled to
  `_CHAR_BLEED` and `frontend/views/edge2/ranker.js`'s `/grind|bleed/` — a ranker change; (b) the
  no-guide print row reads "the next reported quarter against the committed trajectory" (now on 28
  of 28 pages' rows where a print is estimated), a "committed" with no referent; (c) "FCF-negative
  → burning cash" and "FCF-positive → self-funding" stay — the second is 3b's item 7.
