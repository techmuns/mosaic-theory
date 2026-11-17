---
id:
status: open
date: 2026-11-17
prs: [1094, 1095]
supersedes:
superseded-by:
---

# Fix 4b, the last synthesis-prompt fix: rule 7 hands the model no rebuttal to copy, rule 9 says what a path word claims, rule 13's example is neutral, and the drawdown anchor is asked only about a cause it names. Built and registered no-worsening on the panel ($0 so far); the draw waits for the registration's row to reach main

**WHAT.** Four prompt edits in `vinci/dossier/synthesis.py` (board item W11; issue #1004's split
table), each checked against main `4889ddba` before it was made (VERIFY-AT-BUILD):

| item | where it lived on main | found | the edit |
|---|---|---|---|
| 1. rule 7's rebuttal pattern | rule 7: a minority point "EACH framed as 'a genuine counter-point, OUTWEIGHED by <the dominant majority fact>' or 'what would have to be true …'", "(a real disconfirming fact SURVIVES, qualified)"; the same template in the `bull_points` and `bear_points` descriptions of the tool schema | present | A committed lean's minority point is stated as what would have to be true for the minority case. Under a mixed lean every point is stated plainly. On any lean a point never ends by rebutting itself: a fact that cuts the other way is a point on the other side, and the weighing is `evidence_balance`'s. Reading a point's own metric as the real signal or the misread (rule 9) is not a rebuttal. The schema's two descriptions say the same. |
| 2. the leading follow-up question | not in rules 7–13: the drawdown-anchor digest's closing line, "ASK: has the cause named at the {follow/underwrite} played out?", sent for every anchor | present | `_drawdown_anchor_ask` reads the at-anchor part's structure. A part whose gap-downs carry their 8-K keeps the question byte for byte (SMPL). A part with no gap-down (MCK's follow, 2026-05-02 to 2026-10-29), with gap-downs that have no company filing (NCNO's underwrite, TECX's follow), or that could not be read, is told it names no cause, never to state or assume one, and is asked what came after. |
| 3. "every step" | not prompt wording: it is the model's (#920's PATH control, NFLX "EBITDA margin has RISEN every step" over a series that dips FY2021→FY2022, EBITDA 6,402.9 → 5,969.5 $M) | the overreach is still on the panel (M-PATH 2–6 units per arm in the last three runs) | Rule 9 gains one clause: a path word ('every year', 'every step', 'without interruption', 'never fell') claims each period moved one way; write one only when every period the facts carry did, otherwise state the endpoints and the period that broke the run. |
| 4. a neutral example | rule 13's literal example: LLY's committed bear point, verbatim, closed by "genuine, but outweighed by 121.4x coverage and 0.9x net leverage …" | present | #920's V3 text, verbatim: fictional figures in the same shape (seven entries, six cited, one derived, in claim order), no rebuttal clause. |

Rules 7b and 8 carry none of the four wordings, and neither is edited. RG-D20 (#1009) edited
comments, docstrings and docs only; the six panel requests were byte-identical across it, so it
removed none of the four.

**WHY, and what #920 implies for the effect.** `docs/records/2026-11-05-nflx-synthesis-causality-test.md`
drew NFLX five times per variant.
- **Its V3 (this fix's item 4, the same text) moved nothing at n=5:** bear points closed by a
  rebuttal, 3/5 draws → 2/5 and 3 of 27 points → 3 of 27 (p 1.0). The rebuttals that stayed used
  RULE 7's words ("A genuine counter-point …, OUTWEIGHED by …"), in `mixed`-lean draws, where rule
  7 never prescribed them. So item 4 alone is expected to do nothing measurable; it removes the
  last copy of the pattern from the request, so the example no longer contradicts the new rule 7.
  The effect, if any, is expected from item 1, which #920 named "the likelier source" and did not
  test.
- **Item 2 is #920 §14's hypothesis, untested:** the ASK was asked of an anchor whose at-anchor part
  showed no gap-down, so no cause was ever named. On the frozen panel exactly one page carries that
  case (MCK); SMPL names its drops and its request does not move in this span.
- **Item 3:** PATH was #920's negative control, moving three draws in five with nothing aimed at it.
  M-PATH is that metric, and it is too narrow to be a target (TEST recall 1/12, STATE row 53).

**HOW VERIFIED ($0).**
- **Pins** (`tests/test_fix4b_prompt.py`, `tests/test_anchored_drawdown.py`): rule 7's old wording
  cannot return in any book's system prompt or tool schema (a closed list, each entry live) and rule
  7 is pinned by sha256; the framing rule 7 and the schema prescribe is one the false-balance guard
  (`_OUTWEIGHED`) reads; rule 13's example has no rebuttal and its shape and arithmetic hold; every
  path word rule 9 names is one M-PATH's frozen regex counts; the anchor ASK in four cases on SMPL's
  real anchored build (named → byte-identical, no gap-down, no company filing, unread). 30 nodes
  failed on main's code at the first commit (`f84101db`); the no-filing pin was added in review
  round 0 and fails there too.
- **The $0 compare** (`python -m vinci.evals compare --base origin/main --cand 38c170fa`, the panel
  rule first: it yields the frozen six). Every page differs; nothing outside the claimed spans moves.

  | page | SYSTEM | tool schema | USER | total |
  |---|---|---|---|---|
  | BURL, CNXC, LLY, ROST, SMPL | +499 | +88 | 0 lines | +587 |
  | MCK | +499 | +88 | `drawdown_anchor` +28 (5 diff lines) | +615 |

- **Across the committed pages:** 14 carry a drawdown anchor. 11 of them lose the leading ASK at
  their next build: 9 whose at-anchor part shows no gap-down (GOOGL, LLY, MCK, NFLX, TJX, UBER, V,
  WERN, WLK) and 2 whose only at-anchor drop has no company filing (NCNO, TECX). EPAM, IT and SMPL
  name their drops and keep the question byte for byte.
- **Cross-setup validation** (`python -m vinci.impact run`, $0, base `4889ddba` → head `38c170fa`):
  31 of the 63 changed-file test nodes fail on base and pass on head, none fail at head; 0 of the 15
  pages it could build move; all 15 requests move (SYSTEM and tool schema), the anchor span on NCNO
  and WERN only (TECX's $0 build on this store carries no anchor); the ledger, scoring report and
  monitor are identical at both refs. 11 pages were not built: 10 have no price history in this
  Mac's store (frontier 2026-08-05), and PARR's quarterly export is mislabelled.
- **The vintage and one re-pinned test.** Vintage `2026-11-17.synthesis-prompt-fix-4b`, with
  `synthesis.py` re-pinned to it. `test_the_prompts_literal_example_checks_clean_against_the_facts_it_cites`
  pinned that rule 13's example was LLY's real bear point. The example is fictional by design now,
  so the test checks the figure trace on LLY's frozen quality block with the four facts the example
  cites made to state its figures: it traces clean, and unfootnoted it flags exactly 1870, 6.2 and
  2.4, the figures its own ref does not state. `compare --base 38c170fa --cand b6a0a6a8` refuses
  ("reaches no page's request"): the registered bytes are the shipped ones.
- **Review round 0** (`/code-review high --fix`): three fixed (the no-filing case above; rule 7's
  clause contradicting rule 9's real-or-misread reading; the false-balance flag's text still asking
  for "qualified-as-outweighed"), two skipped (below).

**THE REGISTRATION** (RUNBOOKS §n step 4, before any draw).
- **The approval:** operator, 2026-11-16, verbatim **"Approve $35"** (relayed on #1004). One budget
  ledger opened at $35 with those words, outside the repository.
- **Registration** `e309bd25e58f714e099f5ac29d6897d4aa4760c98b025690c35f1b7770b2aa0b`:
  base `4889ddba` (main), cand `38c170fa`; the six panel pages, 5 draws per page per arm; alpha
  0.05, **no-worsening only, no target**; held out from this change: BURL, CNXC, ROST; scorer
  `scorer_ref` `4889ddba`, fingerprint `f4d14ee0…`, registered from a checkout of main.
- **Its note, inside the sha,** says what the run reads descriptively and decides nothing by: points
  matching #920's M3 regex per arm, M-PATH units, MCK's anchor answers; and that M-ECHO may rise on
  the phrase rule 7 now prescribes, which is not a worsening.
- **W34 rides on the same draws:** #953's committed-lean draws (8 → 15, unexplained) are read again
  in both arms, and BURL is read with five draws per arm (#953's CAND had one usable of five).
- **Its `registered` row reaches main in its own docs-only PR before any draw (RG-D14).**

**FOUND, NOT FIXED (review round 0's two skips).**
- **The false-balance guard still credits a self-rebuttal as sizing:** `_OUTWEIGHED` accepts
  "outweighed" and "does not offset" clauses, so a strong-lean draw whose near-symmetric minority
  points each end in the pattern rule 7 now forbids passes G.2. A guard that flags a self-rebuttal is
  a new QA check, outside the four prompt edits.
- **M-ECHO may rise:** rule 7 and the schema prescribe a literal phrase. Written into the note
  before any draw, not changed.

**BOUNDARY.** Pages: the frozen panel v2 (freeze `bcda7ce3`). Requests: main `4889ddba` against
`38c170fa`, no transform. Sizes: characters per section as `compare` prints them. Committed-page
counts: the 14 committed pages with a drawdown anchor at main `4889ddba`, read from
`data/dossiers/*/dossier.json` (`drawdown_cause.anchor.at_anchor.gaps`). No page is rebuilt for this fix: each carries it at its next
paid build.

**WHAT IT COSTS / WHAT IS ACCEPTED.** $0 so far. The panel draw is expected at about $26–30 of the
$35 approval. No target, so the run can show that nothing worsened, never that the fix helped.
