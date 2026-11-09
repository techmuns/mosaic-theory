---
status: recorded
date: 2026-11-09
prs: [931]
supersedes:
superseded-by:
---

# Fix 4a (#927) measured on the panel under the replication rule ($30.31 of $70): M-GAP 37 → 4 units at p_lower 2.6 × 10⁻¹¹, under the 0.01 ship bar, so it ships by the registered rule with no replication; no class worsens; LLY's lean move withholds its BUY and is explained as one dissent in ten; the pre-registered audit could not assess M-GAP's precision on CAND output (4 flags, 1 a real error) and found no misses

**THE APPROVAL.** Operator, 2026-11-09, verbatim: **"Approve, cap $70"**, answering "Cap for fix 4a's
paid measurement (about $31 expected)?".
- One budget ledger was opened with those words: `synthesis-eval-fix4a/ledger-fix4a.jsonl` in the
  session family's notes folder.
- The registration, raw draws, score log and audit are kept there too, outside the repository. The
  requests carry licensed transcript text and stay in the session's scratch folder only.
- #927 was frozen at `564baad8` for the measurement. The cap was not raised.

**THE RESULT IN SIX LINES.**
- **By the registered rule, #927 SHIPS on its first run.** The target M-GAP fell **37 → 4** units
  over 30 draws per arm (p_lower 2.6 × 10⁻¹¹, against the 0.01 ship bar), so no replication.
- **No class worsened beyond noise:**
  - M-LABEL's gated families (bleed, trailing-only, pe-percentile-blocked) fell 10 → 1;
  - its reported gap-statement families went 33 → 34 (p_upper 0.50), as #927's compliant lines
    were expected to read;
  - M-ABSENT 58 → 61 (p_upper 0.41), M-PATH 3 → 2, M-SIGN 0 → 0.
- **Three modal leans moved:**
  - LLY's moved its proposal: bullish 5/5 → 4/1, which withholds its BUY;
  - MCK and SMPL moved no proposal.
  - Each is within one page's noise (§4), and none of the three cites a gap.
- **The pre-registered audit:** M-GAP flagged only 4 of 372 CAND units. That is under 5, so by
  the registration's own rule its precision on CAND output is NOT ASSESSABLE. Blind coders found
  1 of the 4 a real gap-framing error, and 0 errors among 20 unflagged CAND gap-subject units.
- **The audit cannot have made the result.** M-GAP's false flags raise CAND's count, so they bias
  the test against #927. With only 1 true error, CAND's true count is lower than 4.
- **Spend:** $30.3130 of $70; 60 calls, none failed.

## 1. The $0 cross-check, before the registration

`compare` main `15f45d38` → #927 `564baad8`, panel v2, with the five `FIX_3A` transforms and
`gap_types`, run from a detached checkout of `564baad8`, on the primary checkout's `data/manual/ciq`
read only.
- **No other kwarg differs.** Each request moves in exactly three places, the same on every page:
  - **SYSTEM:** one region, from rule 7b's example (its "tagged 'trailing-only'" is gone) to the
    end of rule 8, which becomes THE GAP TEST ("ONLY a change or deviation may be raised as a risk
    … Every other gap, listed or not, is an unknown for key_unknowns with what would resolve it and
    when — never bearish").
  - **The tool schema:** only `bear_points`' clause. "carries its forward or a 'trailing-only'
    blind-flag" becomes "is read beside the forward (NTM) multiple wherever the page carries one".
  - **USER:** byte for byte, BASE plus one inserted `disclosure_gaps` block, 1,073 to 2,045
    characters by page.
- **Size per request:** BURL +0.32%, CNXC +0.37%, LLY +0.31%, MCK +0.48%, ROST +0.44%, SMPL
  +0.40%. That is inside #927's reported +0.31% to +0.49%.

## 2. What was registered, before any draw

- **Registration** `06ed949b46f187039fa14c168f6dcd130d296b2be9924c69d7914884b029ebfa`:
  - `15f45d38` → `564baad8` on panel v2, the six transforms, five draws per page per arm;
  - target **M-GAP**; alpha 0.05, ship alpha **0.01** (the replication rule);
  - `no_worsening_families` M-LABEL = bleed, trailing-only, pe-percentile-blocked;
  - all 12 requests pinned (the draw's re-capture matched every one); held out: none.
- **The scorer:** the files at `564baad8`, fingerprint `755044b4…`.
- **The note**, inside the sha, states the coverage:
  - M-GAP reads the gap framing (fix 4a's items a–b) on the six frozen pages only;
  - item (c), the removed trailing-only ask, is read only through M-LABEL's gated trailing-only
    family;
  - the gap-statement families and the whole metric are reported, never gated.
- **The note also pre-registers the audit (§5):** after the draws and before the score is read,
  code every CAND unit M-GAP flags plus an equal random sample (at least 20) of unflagged CAND
  gap-subject units, blind.
  - If M-GAP's precision there is below 0.80, the result is UNPROVEN.
  - With fewer than 5 flags, precision is not assessable, and is reported as such.
- **Inputs, by sha256** (the registration's `inputs`), under the primary checkout's `data/manual/ciq`:
  the same six comps exports and twelve transcripts as #926's run (`e302c4c0…`, `aa822ebf…`,
  `ce7897dc…`, `158bc7e1…`, `7171baef…`, `647fa707…`).

## 3. The result, by the registered rule

| metric | BASE → CAND (units, 30 draws each) | p |
|---|---|---|
| **M-GAP (target)** | **37 → 4** | **p_lower 2.6 × 10⁻¹¹** |
| M-LABEL[bleed+trailing-only+pe-percentile-blocked] (gated) | 10 → 1 | p_upper 1.00 (p_lower 0.005) |
| M-LABEL[reported: no-adjusted-forward+segment-undisclosed+runway-not-derivable] | 33 → 34 | p_upper 0.50 |
| M-LABEL (whole, reported) | 43 → 35 | p_upper 0.98 |
| M-ABSENT | 58 → 61 | p_upper 0.41 |
| M-PATH | 3 → 2 | p_upper 0.75 |
| M-SIGN | 0 → 0 | — |
| M-ECHO (reported) | 59 → 59 | p_upper 0.55 |

- **The score's decision:** "ships once the moves listed are explained in writing" (§4 is that
  writing), in the ship band below 0.01.
- **Per page, M-GAP units per draw, and M-LABEL's gated families:**

  | page | M-GAP BASE | M-GAP CAND | gated M-LABEL BASE → CAND |
  |---|---|---|---|
  | BURL | 2, 1, 1, 0, 0 | 0, 0, 0, 0, 0 | 0 → 0 |
  | CNXC | 2, 1, 1, 1, 1 | 0, 0, 0, 1, 0 | 1 → 0 |
  | LLY | 1, 3, 1, 1, 1 | 0, 0, 0, 0, 0 | 2 → 0 |
  | MCK | 1, 1, 1, 1, 1 | 0, 0, 1, 0, 1 | 1 → 0 |
  | ROST | 1, 1, 1, 1, 1 | 0, 0, 0, 0, 0 | 3 → 0 |
  | SMPL | 3, 1, 1, 3, 2 | 0, 0, 0, 0, 1 | 3 → 1 |

- **Every page falls**, and every BASE draw carries at least one framed gap except two of BURL's.
- **Item (c)** reads through the gated trailing-only family, which fell with the rest (10 → 1).

## 4. The lean moves, explained in writing as the rule requires

- **LLY: bullish 5/5 → bullish 4 / mixed 1; the proposal moves BUY → withheld.**
  - LLY's request carries the gap block and the new rules 7b and 8. The CAND "mixed" lean weighs
    "exceptional earned fundamentals" against "a fully-paid 28x multiple with net-price erosion and
    ~$2bn non-recurring 2026 revenue". That is no gap and no reading of the gap test.
  - One dissent in ten registered draws: the chance it lands in CAND's five is 0.5.
  - This is the boundary property #925's record found on the same page (STATE row 53 item (5)): a
    five-draw build withholds LLY's BUY on any dissent, about 22.6% of the time at a 1-in-20 rate.
  - It cannot be attributed to #927, and it is the unanimity gate's question, the operator's.
- **MCK: mixed 3 / bullish 2 → bullish 3 / mixed 2; no proposal moves.**
  - Every draw in both arms names the same counterweight, a multiple at its own-history ceiling.
  - On this page alone, three or more committed of five has p_upper 0.50.
- **SMPL: mixed 4 / bearish 1 → mixed 2 / bearish 3; no proposal moves.**
  - Both arms cite the same decline facts (guided FY27 sales −13% to −17%, falling consumption and
    consensus, the impairment).
  - On this page, three or more bearish of five has p_upper 0.26.
- **The panel's committed-lean draws** went 12 → 15 (two-sided p 0.55), in both directions: SMPL +2,
  MCK +1, ROST +1, LLY −1.

## 5. The pre-registered audit — M-GAP on gap-test output

- **The sample.**
  - CAND's `key_unknowns` and bear points: 372 units; M-GAP flags **4**.
  - Of the 55 unflagged units matching the fix 4a subject selector, 20 were drawn by
    `random.Random(int('564baad8', 16))`; the minimum of 20 applied, since the 4 flags were fewer.
  - All 24 were shuffled and coded blind (no arm, no flag) by two coders under the 221-gold
    taxonomy.
  - The coders agreed on every `gap`, `error` and `item`, so no adjudication was needed.
- **Precision on the flags: 1 of 4, by the pre-registered rule NOT ASSESSABLE** (fewer than 5
  flags).
  - The true error is SMPL's "the consolidated figure masks whether Quest is already subsidising
    terminal Atkins/OWYN decline".
  - The three false flags:
    - two put "risk" beside an "unknown" that is no missing item at all, which the coders coded
      `gap: false`: MCK's integration risk of a just-closed deal, and CNXC's impairment risk on a
      consensus swing;
    - one states a real gap (MCK's segment profit) but names the segment's concentration as the
      risk, not the gap, and the coders read it as neutral.
- **Misses: 0 of 20** unflagged CAND gap-subject units are errors.
- **What this means for the result:** the false flags raise CAND's count, so they cannot have
  produced a ship. With 1 true error in CAND's 4, the true fall is larger than the score shows.
  What the audit cannot do is put a number on M-GAP's precision on gap-test output: four flags are
  too few, which is the success case.

## 6. What this measurement does not cover

- **Item (c)** is read only through M-LABEL's gated trailing-only family, never by a metric
  designed for it.
- **M-GAP on bear points** remains untested; no CAND bear point was flagged.
- **A type-4 page:** none is on the panel. M-GAP never met a change it should allow.
- **Precision on CAND output** is not assessable at 4 flags (§5).

**BOUNDARY.**
- **Draws:** 60, `claude-opus-4-8`, 2026-11-09, between the ledger's opening (15:01 +05:30) and the
  score (16:38 +05:30). Five per page per arm, BASE then CAND, page by page. `draws.jsonl` sha256
  `da7ebf56…`.
- **Requests:** main `15f45d38` and #927 `564baad8`, each with the five `FIX_3A` transforms and
  `gap_types`, all 12 pinned. Pages: the frozen panel v2 (freeze `bcda7ce3`).
- **Units:** `units.draw_units`, counted per draw with at least one hit.
- **Scorer:** the files at `564baad8`.
- **p:** the exact stratified permutation test over each page's ten draws.
- **Cross-check sizes:** each request's kwargs serialised in order, BASE against CAND.
- **Audit:** CAND `key_unknowns` and `bear_points` units; the fix 4a subject selector; the
  taxonomy sha256 `961db53a…`.
- **Spend:** production's `cost_usd`, summed from the ledger.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $30.3130 of $70; $39.6870 unspent.
- **Accepted, with its falsifier: M-GAP's precision on gap-test output is unknown** (4 flags).
  - It only biases the result against #927.
  - It is falsified as harmless if a later run on gap-test output, with enough flags to assess,
    shows M-GAP MISSING framed gaps that coders find: the audit's 0 of 20 is the first check of
    that direction.
