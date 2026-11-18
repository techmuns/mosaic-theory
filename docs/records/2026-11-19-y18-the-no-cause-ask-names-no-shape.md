---
id:
status: open
date: 2026-11-19
prs: [1124, 1125]
supersedes:
superseded-by:
---

# Y18: the drawdown anchor's no-cause question names no shape (operator 2026-11-18, "Reword it now"). On the panel one line of one request moves (MCK's ASK, +57 characters); registered `99267760`, no-worsening only, before any draw

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

**WHAT IT COSTS / WHAT IS ACCEPTED.** $0 so far. The draw is capped at the $35 approval, and about
$26–31 is expected (fix 4b's run cost $30.74 on the same pages).
