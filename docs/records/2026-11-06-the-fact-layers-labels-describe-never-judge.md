---
status: open
date: 2026-11-06
prs: [923]
supersedes:
superseded-by:
---

# The fact layer's labels describe and never judge (fix 3a): of five labels the code wrote as conclusions, four are deleted and one is reworded to #920's tested words; the prompt the model sees shrinks by 4,013 characters over the 28 pages. The change is in code; no committed page carries it until it is rebuilt.

**THE RULINGS.**
- **Operator, 2026-11-06: "Start the label fix".** This follows the 2026-11-05/06 fidelity diagnosis.
  It double-coded 644 synthesis claims on the 28 pages: 43.9% misread a fact and 18.2% did so
  materially. The largest material class, LABEL, is the model repeating a misleading label the CODE
  wrote.
- **#920's pre-registered test proved the mechanism on one label**
  (`2026-11-05-nflx-synthesis-causality-test.md`): its neutral drawdown wording cut "bleed" and
  "gradual" from 5/5 draws to 1/5 (p = 0.048).
- **The coordinator added, 2026-11-06,** on the operator's question whether the fixes just add words:
  prefer deletion or shorter neutral wording; a label that cannot be stated neutrally from
  structured data is removed, not explained; add no instruction to the model; report what the model
  sees, per page; special-case no name.
- **Operator: "Build it first".** An evaluation harness gates every synthesis-prompt change, so this
  PR's MERGE waits until the harness has measured it on the evaluation panel against the current
  baseline.
- **The coordinator's round-2 review of #923 (2026-11-06)** brought the changes marked "(round 2)"
  below.
- **The rest of the label fix is elsewhere.** Fix 1 (#921) is merged. 3b, conflicting and stale
  values, follows 3a's review. The prompt's rules (7, 7b, 8, the follow ASK) are fix 4; this PR does
  not touch them.

**WHAT.** Every change is to a string the fact layer writes, or one the web renders. No figure moves,
and no name is special-cased.
1. **Drawdown shape: REWORDED** (`mechanical._CURRENT_WORDS.none_shape`).
   - **Before:** a rolling window with no single day of -10% or worse read "gradual bleed — no
     discrete gap-down detected", rising windows included.
   - **Now:** it reads #920's tested words, **"no single-day drop of -10% or worse in the window
     (detector threshold -10%)"**, with the percentage read off `GAP_DOWN_THRESHOLD`. This adds 25
     characters, the one item that grows. It is kept because it is the wording the test proved.
   - **The dated parts are UNCHANGED.** The at-anchor and since parts already stated the detector
     neutrally. A later build must not change the at-anchor part (#906), and SMPL's committed parts
     rebuild byte-identical (pinned).
   - **The renderers are unchanged.** Both fall through to the one-line fact for any shape that is
     not in the "discrete gap-downs —" form.
2. **Trailing EV/EBITDA note: DELETED where a forward multiple exists** (`mechanical.ev_ebitda_note`,
   the ONE rule that `_valuation` and `cli`'s `own-history-refresh` both apply).
   - **Before:** "trailing only — no forward basis; cannot distinguish…" (`TRAILING_ONLY_NOTE`, its
     text unchanged) fired whenever the GUIDANCE-adjusted forward figure was absent.
   - **Now it stands only where none of three sources counts:**
     - the page's consensus forward P/E (`valuation.forward_multiples`);
     - the name's numeric NTM cells on its comps sheet (`ciq_sheets.comps_ntm_multiples`, printed
       in `peer_comps.trading_multiples`).

       These two are in the facts the synthesis reads.
     - a forward-history series that may anchor a leg and has a band, i.e. a numeric latest close
       (round 2). The history sits beside the synthesis facts, not in them. Under this rule ORKA's
       NM-at-latest history (its only number a 2025 EV/NTM EBIT) counts for nothing, and neither
       does the context-only P/NTM EPS.
   - **Otherwise the note is removed.** The guided figure's absence is already stated on
     `ev_ebitda_adjusted_fwd`, and the forward multiples are their own facts.
   - Rule 7b's text is not edited.
3. **Survival read: the verdict tags DELETED** (`mechanical._survival_capacity`, copied to
   `leverage_survival.survival`).
   - " (a risk)", " — solvency risk" and the "— a risk" of " (cash not derived — a risk)" are removed.
   - What the machine did not compute stays said: "(cash not derived)" and "runway not assessable"
     (round 2).
   - "FCF-positive → self-funding" belongs to 3b's item 7 and is unchanged.
4. **Peer-delta question: asked only in a single direction, else DELETED**
   (`ciq_sheets._comps_deltas` → `_peer_gap_question`).
   - **Before:** every page asked whether "the discount" is EARNED (worse fundamentals).
   - **The direction** is now the sign of every gap the trading multiples carry, trailing AND forward
     (TEV/Rev, TEV/EBITDA, P/E and their three NTM twins, round 2). Each gap is rounded to the whole
     percent the headline prints, and measured against the self-computed peer median the headline
     and the grid use. One computation, `_peer_gaps`, serves this; `cross_sectional_valuation` now
     prints from it, byte-identically.
   - **When the question is asked:**
     - every known gap positive: "the premium … (better fundamentals)";
     - every known gap negative: the old discount question;
     - the gaps disagree, or none is known: no question. The bracket then reads
       "[justified-vs-residual inputs: the human judges — not computed here]".
   - **The web subtitle is fixed too (round 2).** It read "the reader judges whether the discount is
     earned or residual" on every page; that clause is deleted (`frontend/views/shared/dossier.js`,
     which has no Python twin).
5. **Catalyst print row: a guide that is not current is DELETED from it** (`_drawdown_guide_is_current`).
   - **Before:** the row said "the committed revised outlook (… the print is the checkpoint …)" on
     guides the prompt marks SUPERSEDED.
   - **Now** it names the drawdown guide only when it is the CURRENT guide, and drops "committed".
     Current is decided by the derivation the prompt's vintage mark uses: the release carrying the
     guide's accession, against the newest guide-bearing release. A guide with no newer guide-bearing
     release is current, as the mark reads it.
   - A superseded or undated guide leaves the row. The row then reads as on every page without a
     drawdown guide, and no longer cites it.
6. **The lint** (`tests/test_descriptive_labels.py::test_no_judgment_word_in_the_fact_layers_prose`).
   - **What it reads:** every non-docstring, non-regex string constant the fact layer can write. That
     is vinci/dossier, vinci/edgar, and the three field builders outside them that
     `test_extraction_version_drift` watches. It skips `synthesis.py` (the prompt, fix 4) and
     `verdict.py` (the lean vocabulary).
   - **What it refuses:** any word of a closed judgment list. Each entry is pinned live (round 2).
   - It caught this build's own first version-row text.

**WHY.** The machine assembles and cites; it never concludes (CLAUDE.md). Each of the five was a
conclusion the code wrote into a fact:
- a decline claimed of a name that rose;
- a blind-flag on a multiple that had forward cross-checks;
- a verdict on an unknown;
- a discount assumed of a premium;
- a superseded guide called committed.

#920 showed the model copies such a label into its prose.

**HOW VERIFIED.**
- **Pins that fail first** (`tests/test_descriptive_labels.py`, fixtures
  `tests/fixtures/descriptive_labels/`).
  - **The entry points:** every pin drives the production code — `_drawdown_cause` on the page's
    own closes, the prompt `synthesize` sends, `_valuation`, `own-history-refresh`,
    `_survival_capacity`, `peer_comps`, `_catalyst_calendar`, and the web twin in node.
  - **The data:** values frozen from the committed pages at main `bcda7ce3`, and eleven real CIQ
    comps sheets cut through the real decode path. Each cut reproduces its page's committed lines
    byte-for-byte. **No pin reads a living page** (round 2: two did; a rebuild that moves a page
    must not move a pin).
  - **Each fix has its negative:**
    - a window with gap-downs (SMPL's April);
    - the dated parts;
    - a page with no forward multiple at all;
    - a guided-forward page (VRRM);
    - a positive FCF (AORT);
    - PARR, at a discount on all six multiples (byte-identical);
    - the unchanged statistics;
    - a CURRENT guide.
  - **On main `bcda7ce3`** the final 65-test file runs 36 failed and 29 passed. The 29 are the
    negatives, the 19 pins on the lint's own list (they test the regex, not the code), and the two
    current-guide cases, whose row on main is not the generic one. **On the PR head `818c1cc7`**
    the six round-2 behaviour pins (the band rule ×2, "cash not derived", the WLK and AMZN clashes,
    the web subtitle) fail first.
- **Mutants: 11 of 11 caught** (round 2), each by a named pin, on a scratch copy of the fixed tree:
  - `comps_ntm_multiples` counting 'NM' cells;
  - `comps_ntm_multiples` counting trailing cells;
  - dropping `forward_multiples` from the rule;
  - the sign test without `round()`;
  - a guide with no newest release read as not current;
  - `cli` passing `peer_ntm=[]`;
  - `cli` passing `forward_multiples=False`;
  - the history counting any numeric close;
  - the question reading the trailing gaps only;
  - the lint without `bleed\w*`;
  - the lint without `solvency\s+risk`.
- **The lint on the live tree** found four strings on main `bcda7ce3`, all in `mechanical.py`: the
  "gradual bleed", the two "(a risk)", and "solvency risk". It found nothing else, and zero after
  the fix.
- **Before/after and prompt size over all 28 committed pages, $0.**
  - **BEFORE** is each page's committed mechanical layer. **AFTER** replaces only the five fields,
    each recomputed by this code.
  - **Items 1, 3 and 5** are recomputed from the page's committed structured fields.
  - **Items 2 and 4** use the page's own comps export, and only where it reproduces the committed
    line byte-for-byte. 24 of 28 do. AORT, BURL, MCK and NCNO's exports on disk are not the ones
    their pages were built from; on those four, item 2 is decided without the peer NTM cells and
    item 4 is not measured.
  - **Each prompt** is the real user message `synthesize` sends, captured by a client that records
    it and fails the draw.
- **The $0 pre-spend check** (`prespend.run`) on a sample, with the same check run on main's code
  over the same data, is in the PR body. The coordinator's `prespend.compare` on BRBR, LLY, VITL and
  AMZN, with all five labels changed, gives 0 regressions.

**MEASURED, ON THE 28 COMMITTED PAGES (main `bcda7ce3`):**

| item | pages that move | change in the prompt | detail |
|---|---|---|---|
| 1 drawdown shape | **17** at rebuild | +425 (+25 each) | the committed window has 18 no-gap pages. GOOGL's rebuild window holds its 2026-10-29 −12.6% (114.51 → 100.04), so its shape is discrete at rebuild and does not carry the new words (round 2). 11 of the 17 rose over their committed detector window (MCK +45.3%, LLY +36.6%, V +28.3%) |
| 2 trailing note | 24 | −2,808 (−117 each) | every page with a PRESENT trailing EV/EBITDA and no guided forward; 0 stay "trailing only" |
| 3 survival tags | 9 | −232 | AMZN, FUBO, ORKA, TECX, VITL, WERN, WLK (FCF negative, −28 each); IT, LLY (FCF unknown, −18 each); each twice, the block and its copy |
| 4 peer question | 16 of the 24 measurable | −781 | premium on all six 5 (LLY, NKE, ROST, TJX, V; ±0 characters); deleted 11: mixed 9 (AMZN, BRBR, FUBO, GOOGL, NFLX, TGT, UBER, VITL, WLK) and no gap known 2 (ORKA, TECX), −71 each. 8 at a discount on all six are unchanged (CNXC, EPAM, IT, MVST, PARR, SMPL, VRRM, WERN) |
| 5 print row | 3 | −617 | BRBR, VITL, VRRM: each guide SUPERSEDED, so the row reverts to the no-guide row |
| **all** | **28 of 28 on at least one** | **−4,013 of 10,075,466** | per-page table in the PR body |

**Item 4's median.** The signs come from the self-computed peer median, not CIQ's Summary Median row
that `trading_multiples` prints. Across the 123 known gaps on the 24 pages, the two disagree on one
sign: WLK's TEV/Rev, −4% against +0%. WLK is mixed either way.

**WHERE THIS DIFFERS FROM THE BRIEF'S COUNTS** (each measured here; boundary below):
- **Item 1:** 17 pages at rebuild, not 17 on the committed window — that window has 18 (GOOGL, above).
  The brief's ORKA +161.8%, TGT +69.8% and LLY +57.4% are each page's 251-point (~1-year) price
  series, not the detector's 180-day window (+4.4%, +18.5%, +36.6%).
- **Six final syntheses carry "bleed",** not five: BURL, NFLX, NKE, SMPL, TJX and UBER. SMPL's page
  was re-assembled on 2026-11-04 (#914).
- **Item 2:** 24 pages, not 17. The 17 matches no field measured here; 18 pages carry
  `forward_multiples`.
- **Item 5:** 3 pages, not 4. SMPL's rolling window has held no drawdown guide since #914; its April
  guide sits in the at-anchor part, which the print row does not read.

**BOUNDARY.**
- **Population and units:** the 28 `data/dossiers/<T>/dossier.json` at main `bcda7ce3`, counted in
  pages. Prompt sizes are characters of the synthesis user message.
- **Item 1's two windows:**
  - **The committed window** is the detector's 180 days ending on `drawdown_cause.gap_window_end`
    when that is set (MCK, NFLX, SMPL), else on the page's reference date.
  - **The rebuild window** is the 180 days ending on the page's last committed daily close; at
    rebuild, #906 ends it on the price date, so a later rebuild reads later closes.
  - **Measurement:** the move is the first close in the window to the last, from the page's rebased
    daily `stock_performance` series. A "-10% day" is `detect_gap_downs` re-run on those closes.
- **The synthesis "bleed" count** is a case-insensitive "bleed" in the committed `synthesis` JSON:
  LLM text, measured here, never pinned.
- **Item 4's directions** are the whole-percent signs `_peer_gaps` computes over the six trading
  multiples.

**WHAT MOVES, AND WHEN.**
- **No committed page is re-written:** no LLM call, no paid assembly.
- **Each page picks the labels up at its next assembly;** 28 of 28 move on at least one item.
- **Row 52's NFLX rebuild,** owed once after the prompt fixes, carries items 1, 2 and 4.
- **The merge waits** for the evaluation harness (operator, "Build it first").

**DEPENDS ON FIX 4.** The bear_points schema description at `synthesis.py:391` says a trailing
multiple "carries its forward or a 'trailing-only' blind-flag". After this PR, 24 of the 28 pages'
EV/EBITDA carries neither on the value itself; their forward multiples are separate facts
(`forward_multiples`, the peer comps' NTM row). That text is a prompt rule, so it is fix 4's: it is
deferred there (PR round 1), and fix 4 should retire or re-point it.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The lint's limits.**
  - **A closed list.** It refuses only a word it names; a judgment word not on it passes.
  - **Python string constants only.** It reads no JS and no rendered page, so the web furniture is
    pinned on its own (the peer subtitle). An LLM-written string or a verbatim quote is outside it by
    construction.
  - **The fact layer only.** Run over all of `vinci/` it also finds, none of them a dossier fact and
    none changed here:
    - the ranker's "bleed" (`vinci/rank/ranker.py:234`, on the ranked queue);
    - the screen's "distress" (`vinci/screens/run.py:195`);
    - the sleeves' and the prompt's "value trap";
    - the scoring report's "concern";
    - theme intelligence's "a risk".
- **A deleted label is information a draw no longer gets in that place.** Each deletion's content is
  elsewhere in the same facts:
  - the guided figure's absence, on `ev_ebitda_adjusted_fwd`;
  - an unknown leg's reason, on its own field;
  - the gaps' signs, in `cross_sectional` and `trading_multiples`;
  - the superseded guide, in `drawdown_cause.revised_guidance` under the prompt's own SUPERSEDED mark.
- **Two reads repeated (review of 3a, not changed).** `_valuation` builds `forward_multiple_history`
  again beside `assemble_one`'s own build of it. `_peer_gap_question` recomputes gaps that
  `cross_sectional_valuation` also computes. Both read cached sheets, and passing them through would
  widen `assemble_mechanical`'s signature.
- **Found, not fixed (out of scope):**
  - **The ranker's own character label**, "grind/bleed — no discrete gap-down"
    (`vinci/rank/ranker.py:234`), labels the ranked queue (`data/snapshots/ranked_queue.jsonl`). It
    reaches no page and no prompt, and it is coupled to `_CHAR_BLEED` and to
    `frontend/views/edge2/ranker.js`'s `/grind|bleed/`, so changing it is a ranker change.
  - **The no-guide print row** reads "the next reported quarter against the committed trajectory": a
    "committed" with no referent.
  - **"FCF-negative → burning cash" and "FCF-positive → self-funding" stay;** the second is 3b's
    item 7.
