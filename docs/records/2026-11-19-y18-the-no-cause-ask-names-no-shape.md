---
id:
status: recorded
date: 2026-11-19
prs: [1124, 1125]
supersedes:
superseded-by:
---

# Y18: the drawdown anchor's no-cause question names no shape (operator 2026-11-18, "Reword it now"), measured on the panel, no-worsening only ($25.54 of $35). It ships by the registered rule, and every MCK draw now states that the page identifies no cause. Yet 3 of 5 still call the move a "gradual bleed" (2 of 5 on main), so the pre-declared 0 did not happen. Fix 4b's SMPL falsifier fires on this BASE

**WHAT.** One edit in `vinci/dossier/synthesis.py`, the no-cause branch of `_drawdown_anchor_ask`
(board item Y18). Fix 4b (#1094) sent it; `docs/records/2026-11-17-fix4b-the-rebuttal-the-ask-the-path-and-the-example.md`
accepted its one weakness "unless the operator rules otherwise", and the operator has ruled.

The wording was settled in writing before any code. MCK's line, as its panel request carries it:

| | the ASK, up to #1094's unchanged tail |
|---|---|
| main (#1094) | ASK: the part at the follow shows no discrete gap-down, so it names no cause — never state or assume one. Set the since part and the current facts against the follow: did a drop come after it, and what does its filing name; what does the current outlook say. |
| this change | ASK: the part at the follow names no cause — never state or assume one. From the since part and the current facts, state only what is dated and sourced after the follow: a later drop and the cause its filing names, and the current outlook; where nothing names a cause, say plainly that the page identifies no cause. |

- **Three branches, one question.** The branch is read from the part's structure, exactly as #1094 reads it (`gaps`, `GapDown.accession`, the shape's status), never from its shape string. Only the reason in brackets differs:
  - a part read with no gap-down: no reason, and no word for the part's price path;
  - drops with no company filing (NCNO's underwrite, TECX's follow): "(none of its drops carries a company filing)", where #1094 had "shows no gap-down with a company filing". That reason was first drafted as "none of its gap-downs …". The roster-walk pin caught it reusing the detector's word, the one the shape line pairs with "discrete", and it was amended before the compare;
  - a part not read: "(it could not be read: UNKNOWN)".
- **Unchanged:** the named branch (EPAM, IT, SMPL) byte for byte; the closing tail; rules 7, 9 and 13; the tool schema; every other span.
- **Vintage** `2026-11-19.synthesis-prompt-the-no-cause-ask-names-no-shape`, with `synthesis.py` re-pinned to it.

**WHY.** "Shows no discrete gap-down" describes an absence as a shape. In 2 of 5 MCK candidate draws
under fix 4b it was restated and filled with "a gradual bleed" ("bleed/run-up", "bleed/rise"),
which is MCK's whole M-LABEL `bleed` rise, 0 → 2. That is the label #923 (fix 3a) removed because
it names a shape as if it were a cause.

**Found while doing this, and why the old phrase led where it did:** MCK's FROZEN panel page still
carries the pre-#923 rolling label in `drawdown_cause.shape`: "gradual bleed — no discrete gap-down
detected" (`source_ref` "EOD gap-down detector, 2026-05-08 to 2026-11-04: none"). Fix 4b's
registration replays the frozen layer with no transform, and so does this one. "No discrete
gap-down" in the ASK therefore pointed at the one line of MCK's request that holds "bleed". The
reword names no gap-down at all in that branch, but the word stays in CAND's request, in the facts.
So the descriptive bleed count can stay above 0 with the ASK working as written.

**HOW VERIFIED ($0).**
- **Pins** (`tests/test_no_cause_ask.py`, 8 nodes; 7 fail on main `55b92b52`, run before the edit):
  - no-gap branch: the ASK states only that the part names no cause, with no shape word. The shape words are the detector's own ("gap-down", "discrete") and the M-LABEL `bleed` family, whose regex and "gradual" clause are imported from the registered scorer, never restated;
  - all three branches ask one question after their reason (dated and sourced after the anchor, or a plain no-cause statement);
  - the no-filing reason names the missing filing and never says "no gap-down" (the part has one);
  - the unread reason says why, with no shape word;
  - guard: the pre-#923 label and the current one give the same ASK, and it quotes neither;
  - e2e, MCK's frozen panel request captured through `synthesize`: the check first finds "bleed" in that very request (the frozen label), then finds none on the ASK line;
  - e2e, SMPL's frozen panel request keeps its named question (passes on main too, as it should);
  - roster walk over every covered page with an anchor: each no-cause ASK carries no shape word and the plain-statement option, each named page keeps its question, and both sides must be present.
  - #1094's two assertions on the old wording (`tests/test_anchored_drawdown.py`) were re-pinned to the new.
- **The $0 compare** (`python -m vinci.evals compare --base origin/main --cand f3503b39`; `panel`
  first: it yields the frozen six):

  | page | SYSTEM | tool schema | USER |
  |---|---|---|---|
  | BURL, CNXC, LLY, ROST, SMPL | equal | equal | IDENTICAL |
  | MCK | equal | equal | one line, the ASK: `drawdown_anchor` +57 characters |

  A diff of MCK's two captured requests shows exactly that one line; the `since` line is unchanged.
- **Across the committed pages** (`data/dossiers/*/dossier.json` at main `55b92b52`, the 14 with a
  drawdown anchor): 11 get the new question at their next paid build. Nine are read with no gap-down
  (GOOGL, LLY, MCK, NFLX, TJX, UBER, V, WERN, WLK) and two have unfiled drops (NCNO, TECX). The other
  three, EPAM, IT and SMPL, keep the named question byte for byte. Active pages among the 11:
  GOOGL, LLY, TJX, NCNO.
- **What the comparison covers and does not:** the panel carries one no-cause page, MCK, read with no
  gap-down. The no-filing and unread branches reach no panel page, as under #1094, and are covered
  by the pins alone.
- **Review round 0** (`/code-review high --fix`): four findings, none applied, so the registered
  bytes are the bytes that ship (see the PR's dispositions table).

**THE REGISTRATION** (RUNBOOKS §n step 4, before any draw).
- **The approval:** operator, 2026-11-18, verbatim **"Reword it now"**. One budget ledger was opened
  at $35 with those words, outside the repository (2026-11-19T00:08:21+0530).
- **Registration** `99267760ed0726c0d4602f99c1286096ab8e3b439baf65e068f7294f0c9bf205`: base `55b92b52`
  (main), cand `f3503b39`; the six panel pages, 5 draws per page per arm; alpha 0.05,
  **no-worsening only, no target** (M-GAP is barred, RG-D13). Held out from this change (named by
  `register`): BURL, CNXC, LLY, ROST, SMPL. Scorer: `scorer_ref` `55b92b52`, fingerprint
  `3f4bf55c…`, registered from a clean checkout of main.
- **BASE's six request pins equal fix 4b's CAND pins** (`e309bd25`), byte for byte. Five of the six
  pages are byte-identical across arms, so 50 of the 60 draws are an A/A floor: any move there is
  draw noise.
- **Its note, inside the sha,** pre-declares as descriptive, deciding nothing:
  - per page per arm, the M-LABEL `bleed`-family units and the draws matching `bleed\w*`, MCK above all, expected to go to 0 in CAND;
  - MCK's draws stating "identifies no cause";
  - the frozen-label caveat above;
  - fix 4b's two falsifiers, read on this BASE: LLY below 4 bullish of 5, or SMPL at 4+ bearish of 5.
- **Its `registered` row reaches main in its own docs-only PR, #1124, before any draw (RG-D14).**

**BOUNDARY.** Pages: the frozen panel v2 (freeze `bcda7ce3`). Requests: main `55b92b52` against
`f3503b39`, no transform. Sizes: characters per section as `compare` prints them. Committed-page
counts: the 14 committed pages with a drawdown anchor at main `55b92b52`, classified by the branch
`_drawdown_anchor_ask` takes on each page's `drawdown_cause.anchor.at_anchor`. Pins: the 8 nodes of
`tests/test_no_cause_ask.py`, run on main's `vinci/` before the edit. No page is rebuilt for this
change: each carries it at its next paid build.

## RESULT (drawn once, 2026-11-19)

**THE GO-AHEAD.** The registration's row reached main in #1124 (`9345f5dd`, 2026-11-18T19:35:18Z).
- Operator, verbatim, relayed by coordinator B: **"Yes to both"** (2026-11-18), then **"y18 paid draw allowed"**.
- B announced the draw on #1004 (issuecomment-6989404037).
- Pr-feedback round 1 ran first (Codex at its usage limit, so `/code-review high` in its place): one docs-only fix and two dispositions.
- `compare --base f3503b39 --cand 4356078a` refused with all six pages IDENTICAL, so the bytes drawn are the bytes that ship.
- This session could not start the paid run itself: its permission check refused the command twice, at $0. The operator ran the same command from the same clean checkout ("y18 draw has started already", 2026-11-19).

**THE RUN** (`run-compare --paid`, drawn once).
- **Where from:** a clean checkout of main `e6a6c318`. The 16 scorer files show no diff from the registered scorer ref `55b92b52`, and the score read the registered fingerprint `3f4bf55c…`. `vinci` was imported from that checkout and its path printed before the run. The checkout's `.env` was a symlink made for the run and removed after it.
- **The draws:** 60 of 60 returned and all 60 are usable. All stopped on `tool_use`, `claude-opus-4-8` served every one, and every row states `anthropic` 2.6.0, so both arms ran on one SDK.
- **When:** claimed 06:11:56Z, last draw written 07:45:19Z. The draws record 5,602.6 s of their own.
- **The cost: $25.5411 of $35,** from the run's own ledger (60 draw rows): BASE $15.5973, CAND $9.9438.
  - The split is the prompt cache. Each page's BASE arm drew first and wrote it; CAND read it on the five byte-identical pages, and MCK's CAND request, which differs, wrote its own.
  - Tokens: cache writes 1,291,097, cache reads 9,784,898, uncached input 1,420, output 502,889.

  | page | BASE | CAND |
  |---|---|---|
  | BURL | $2.6309 | $1.6132 |
  | CNXC | $2.3485 | $1.4574 |
  | LLY | $3.1099 | $1.5683 |
  | MCK | $2.4794 | $2.4207 |
  | ROST | $2.5295 | $1.4619 |
  | SMPL | $2.4990 | $1.4224 |

**THE SCORE, at $0** (`python -m vinci.evals score` from the same checkout, one score-log line at
2026-11-19T13:16:23+0530, scorer `3f4bf55c…`).

| metric | BASE → CAND (units, 30 draws each) | p_lower | p_upper | held out (BURL, CNXC, LLY, ROST, SMPL) |
|---|---|---|---|---|
| M-ABSENT | 55 → 54 | 0.5 | 0.575 | 44 → 34 |
| M-LABEL | 48 → 57 | 0.964 | **0.0758** | 36 → 42 |
| M-PATH | 4 → 3 | 0.5 | 0.787 | 4 → 3 |
| M-SIGN | 0 → 0 | 1 | 1 | 0 → 0 |
| M-GAP (barred, reported) | 3 → 12 | 1 | 0.00354 | 3 → 9 |
| M-ECHO (reported) | 65 → 60 | 0.348 | 0.721 | 53 → 50 |

- **No class metric worsens at p_upper ≤ 0.05.** No-worsening reads the four class metrics (M-ABSENT, M-LABEL, M-PATH, M-SIGN); the nearest is M-LABEL at 0.0758.
- **The decision, verbatim:** "ships" (`ships: True`, no reasons listed).
- **M-GAP's 0.00354 decides nothing.** It is barred (RG-D13: its truth is the candidate's own classifier output) and is not a class metric. Read anyway:
  - 9 of its 12 CAND units and all 3 BASE units sit on the five held-out pages, whose requests are byte-identical across arms. So 3 → 9 there is draw noise by construction.
  - MCK, the one page whose request moved, reads 0 → 3: bear points that hold "no forward", "unavailable" and "cannot be read" against the name.
  - On fix 4b's run, MCK's CAND arm (the same bytes as this BASE) read 2.
- **Committed-lean draws: 11 → 9.** The whole move is ROST's, explained below.

**PER PAGE** (a $0 script on the registered scorer's own functions, `panel_inputs`, `arm_layer`,
`draw_units` and `score_units`, writing no score log; it reproduces all six totals and every
page's leans exactly).

| page | M-ABSENT | M-LABEL | M-PATH | M-ECHO | M-GAP | leans BASE → CAND | committed |
|---|---|---|---|---|---|---|---|
| BURL (held out) | 15 → 11 | 9 → 9 | 0 → 0 | 11 → 6 | 0 → 0 | mixed 5 → mixed 5 | 0 → 0 |
| CNXC (held out) | 14 → 12 | 7 → 7 | 0 → 1 | 9 → 13 | 0 → 0 | mixed 5 → mixed 5 | 0 → 0 |
| LLY (held out) | 1 → 0 | 3 → 7 | 2 → 0 | 20 → 13 | 0 → 2 | bullish 4, mixed 1 → the same | 4 → 4 |
| MCK | 11 → 20 | 12 → 15 | 0 → 0 | 12 → 10 | 0 → 3 | mixed 4, bullish 1 → the same | 1 → 1 |
| ROST (held out) | 5 → 6 | 8 → 4 | 1 → 1 | 2 → 7 | 1 → 3 | bullish 2, mixed 3 → mixed 5 | 2 → 0 |
| SMPL (held out) | 9 → 5 | 9 → 15 | 1 → 1 | 11 → 11 | 2 → 4 | bearish 4, mixed 1 → the same | 4 → 4 |

**WHAT THE REWORD DID, read as the note pre-declared (descriptive; no decision reads these).**

| MCK, the one page whose question changed | BASE (main) | CAND (this change) |
|---|---|---|
| draws matching `bleed\w*` | 2 of 5 | 3 of 5 |
| M-LABEL `bleed` units | 2 | 3 |
| draws stating "identifies no cause" | 0 of 5 | 3 of 5 |
| draws restating "no discrete gap-down" | 5 of 5 | 4 of 5 |

- **The expectation, 0 in CAND, did not happen.** Three of five MCK CAND draws still call the move a gradual bleed:
  - "a gradual bleed/drift with no filing naming a driver" (draw 1);
  - "(gradual bleed/drift only)" (draw 3);
  - "a gradual bleed/rise with no catalyst 8-K to follow" (draw 4).

  BASE's two read "gradual bleed/re-rating" and "gradual bleed/rally". Every one of these, in both arms, is in a key unknown, none in a bull or bear point. At 5 draws an arm, 2 → 3 is no change in either direction (Fisher's two-sided p = 1.0).
- **What did change: the no-cause line now says the page identifies no cause.**
  - In all five MCK CAND draws the drawdown key unknown opens "The page identifies…". Three use the pre-declared words; draw 3 writes "identifies NO dated cause".
  - Draw 5 writes "identifies no discrete gap-down or named cause", fusing the plain statement with the detector's word.
  - No BASE draw does either. The phrase is among M-ECHO's CAND-only echoes on MCK (M-ECHO is reported, never decides).
- **Where the word comes from, read on the two requests.**
  - Each of MCK's two requests carries "bleed" exactly once, in the frozen rolling label "gradual bleed — no discrete gap-down detected".
  - It carries "no discrete gap-down" 7 times in BASE and 6 in CAND, all in its USER text: the reword removed the ASK's copy alone. The other six are:
    - the frozen label;
    - the at-follow and since parts, in the facts and again in the digest ("no discrete gap-down — no single day of -10% or worse from …");
    - the digest's literal example.
  - Every bleed sentence, in both arms, first restates "no discrete gap-down" and then names the path.
  - So the ASK was not the only route to the word. This run cannot separate the frozen label from the parts' phrase.
  - The registration's caveat said the count could stay above 0 with the ASK working as written. It did, and the ASK line itself carries no shape word (pinned). The caveat does not turn the miss into a result.
- **BURL and SMPL, held out and byte-identical across arms, carry "bleed" in both arms:** BURL 4 → 3 draws (4 → 4 matches), SMPL 3 → 3 draws (3 → 6). Every panel page but CNXC carries the frozen label once in both arms. LLY and ROST carry it too and wrote "bleed" in no draw.
- **What a rebuilt page would carry** (read at $0 on the committed pages at main `e6a6c318`):
  - The 9 pages whose rolling label is #923's read "no single-day drop of -10% or worse in the window (detector threshold -10%)", with no "bleed": LLY, NCNO, SMPL, TJX, UBER, V, VITL, WERN, WLK.
  - The eight pages still on the pre-#923 label (AMZN, BURL, MCK, NFLX, NKE, ORKA, ROST, TGT) are re-derived at their next build.
  - The anchor's dated parts, though, still read "no discrete gap-down — …" (`vinci/dossier/mechanical.py:821`, `_dated_words.none_shape`): in 22 parts across 13 of the 14 anchored pages. So does the literal example the digest sends with them (`_DRAWDOWN_ANCHOR_EXAMPLE`).
  - On a rebuilt MCK, then, "gradual bleed" leaves the request and "no discrete gap-down" stays. Whether the word leaves the draws with it is untested. Fix 4b's second falsifier is the test: a rebuilt no-cause anchored page carrying "bleed" in a bull or bear point.

**FIX 4b'S TWO FALSIFIERS, READ ON THIS BASE** (pre-declared). BASE's six request pins equal fix 4b's
CAND pins, so BASE is "the next panel run on main with fix 4b" its record names.
- **LLY: bullish 4, mixed 1.** Not below 4 of 5: it does not fire.
- **SMPL: bearish 4, mixed 1, which is 4+ bearish of 5 again: it fires.** CAND, byte-identical, reads the same.
  - On fix 4b's bytes, SMPL has read bearish 4 of 5 in three runs of five (fix 4b's CAND, this BASE, this CAND): 12 of 15.
  - On earlier requests it read bearish 1 (fix 4b's BASE), 3 and 4 (#953's two arms, as fix 4b's record states): 8 of 15.
  - Fix 4b's accepted risk, "LLY's and SMPL's lean moves are noise", is falsified for SMPL by the test it named.
  - This run does not say whether SMPL's bearish lean under fix 4b is the better read or a defect. No proposal moves (production proposes only on five of five), and Y18 does not touch SMPL's request. It is the operator's to rule.

**THE ONE LEAN MOVE, EXPLAINED.** The score lists none. ROST went from bullish 2, mixed 3 to mixed 5,
committed 2 → 0, which is the panel's whole 11 → 9. ROST is held out and its two requests are
byte-identical, so the move is draw noise by construction: two committed of ten both landing in BASE has
probability 0.222. MCK's leans did not move.

**MCK's M-ABSENT, 11 → 20, read by kind.**
- **The class test reads no worsening** (p_upper 0.575): it stratifies over all six pages, and the held-out five fell 44 → 34. MCK's +9 is still larger than any held-out page's own swing (at most 4).
- **Units with a figure only the call transcript states: 9 → 15.** MCK's Q2 FY27 call figures (340, 1.4, 44.20, 1.60) appear in both arms.
- **Units with a figure the page states nowhere: 2 → 5.** In CAND:
  - the FY27 FCF guide "$4,500–$4,900M" (3 units, draws 1–2);
  - "$7,305.9M" consensus;
  - a quoted "16.2x vs peer median 9.3x premium".
- **13 of CAND's 20 are in two draws** (8 and 5); BASE's draws read 1 to 4 each.
- **The same bytes as this BASE read 20 in fix 4b's CAND arm,** so MCK's request has read 20 and 11 in two runs.
- **One reading, not tested:** the new ASK asks for what is "dated and sourced after the follow", and MCK's call (2026-11-04) is dated after it. Review round 0 deferred exactly this ("state only" may narrow what a draw cites) to this check, and the check reads no worsening.

**M-LABEL, 48 → 57 (p_upper 0.0758), by page.**
- 6 of the 9 rise on the held-out pages, byte-identical across arms: SMPL 9 → 15, LLY 3 → 7, ROST 8 → 4.
- MCK reads 12 → 15: `bleed` 2 → 3, `trailing-only` 0 → 2, `no-adjusted-forward` 5 → 6, `segment-undisclosed` 5 → 5.

**FOUND, NOT FIXED.**
- **The anchor's dated parts still name an absence as a shape.**
  - `_dated_words.none_shape` (`vinci/dossier/mechanical.py:821`) writes "no discrete gap-down — no single day of -10% or worse from …" into every anchored page's at-anchor and since parts. The digest's literal example carries the same phrase.
  - On MCK's CAND request that is 5 of the 6 remaining copies; the sixth is the frozen label.
  - Changing it is a fact-layer label change on 13 committed pages, and a prompt change through the example. It would need its own panel check, and it is the operator's call.
- **Eight committed pages still carry the pre-#923 rolling label** (AMZN, BURL, MCK, NFLX, NKE, ORKA, ROST, TGT), each re-derived at its next build. The panel replays the frozen label with no transform, so it cannot show a rebuilt page's request.
- **`vinci/rank/ranker.py:235` still writes "grind/bleed — no discrete gap-down"** in the ranker's own label, not in the synthesis request.

**THE `drawn` ROW.** The claim appended one `drawn` row (claimed 2026-11-19T06:11:56Z, approval
`a518c9c5…`). It is appended to `docs/evals/registrations.jsonl`, byte for byte, after the
`registered` row #1124 merged.

**BOUNDARY (the result).**
- **Pages:** the frozen panel v2 (freeze `bcda7ce3`).
- **Draws:** 5 per page per arm, 60 in all, drawn once under registration `99267760…`, claimed 2026-11-19T06:11:56Z, run from main `e6a6c318`.
- **Code:** base `55b92b52`, cand `f3503b39`; scorer fingerprint `3f4bf55c…`.
- **Units:** units with a hit, summed over a page-arm's draws. A committed lean is a strongly-bullish or strongly-bearish draw.
- **The MCK words:** case-insensitive regex over each draw's whole decoded output (`bleed\w*`, `identifies no cause`, `no discrete gap-down`).
  - "Opens 'The page identifies'" was read by eye on all ten MCK drawdown key unknowns, every one printed.
  - The request counts are over each captured request's SYSTEM and USER text, every matching line printed.
- **Committed labels:** `drawdown_cause.shape` and the anchor parts' `shape` on every `data/dossiers/*/dossier.json` at main `e6a6c318`. 26 pages carry a rolling label naming a gap-down or a single-day drop; 14 carry an anchor.
- **p-values:** the metrics' from the registered stratified exact test. The lean probability is hypergeometric. Fisher's two-sided for MCK's bleed draws.
- **Kept outside the repo:** the requests, draws, score log, ledger and breakdown.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$25.5411 of the $35 approval;** $9.46 unspent. The cap was not raised.
- **Nothing is accepted by this record.** Two calls are the operator's:
  - whether Y18 ships with "bleed" still in 3 of 5 MCK draws. It ships by the registered rule, and the ASK line itself names no shape;
  - SMPL's lean under fix 4b, whose falsifier fired above.
