---
id:
status: recorded
date: 2026-11-17
prs: [1094, 1095]
supersedes:
superseded-by:
---

# Fix 4b, the last synthesis-prompt fix, measured on the panel, no-worsening only ($30.74 of $35): no class metric worsens (M-LABEL nearest, 48 → 57 at p_upper 0.060); bear and bull points closed by a rebuttal fall from 23 of 398 in 13 of 30 draws to 0 of 399 (descriptive, pre-declared); the score's decision is "ships once the moves listed are explained in writing": LLY's lean (its BUY proposal goes to none) and SMPL's, explained here as within noise; the new no-cause ASK leads 2 of 5 MCK draws to call the move a "gradual bleed"

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

---

## RESULT (drawn once, 2026-11-17)

**THE GO-AHEAD.** The registration's row reached main in #1095 (`47da911d`, 07:50:26Z). Operator,
verbatim: **"Yes, start the draw"** (07:50Z). Coordinator B announced the draw on #1004
(issuecomment-6942084762). Pr-feedback round 1 ran first (Codex at its usage limit;
`/code-review high` in its place): two prose fixes and a dismissal. `compare --base 38c170fa --cand
6250ccc2` refused with all six pages IDENTICAL, so the bytes drawn are the bytes that ship.

**THE RUN** (`run-compare --paid`, drawn once).
- **Where from:** a clean checkout of main `47da911d`. Main differed from the registered scorer ref
  `4889ddba` by the registration row alone, so the scorer fingerprint is the registered `f4d14ee0…`.
  `vinci` imported from that checkout (printed before the run). Its `.env` was a symlink made for
  the run and removed after it.
- **The draws:** 60 of 60 returned. All 60 stopped on `tool_use`, `claude-opus-4-8` served every one,
  and all 60 rows state `anthropic` 2.6.0, so both arms ran on one SDK. No draw failed.
- **When:** 07:52:14Z to 09:25:06Z; the draws record 5,539.1 s of their own.
- **The cost: $30.7382 of $35,** from the run's own ledger. BASE $15.2301, CAND $15.5081. Cache writes
  2,214,356 tokens, cache reads 8,857,424, uncached input 1,420, output 498,505.

  | page | BASE | CAND |
  |---|---|---|
  | BURL | $2.4353 | $2.5862 |
  | CNXC | $2.1689 | $2.2727 |
  | LLY | $3.2059 | $3.1755 |
  | MCK | $2.4731 | $2.5030 |
  | ROST | $2.5266 | $2.4730 |
  | SMPL | $2.4203 | $2.4976 |

**THE SCORE, at $0** (`python -m vinci.evals score` from the same checkout, one score-log line at
2026-11-17T14:55:52+0530, scorer `f4d14ee0…`).

| metric | BASE → CAND (units, 30 draws each) | p_lower | p_upper | held out (BURL, CNXC, ROST) |
|---|---|---|---|---|
| M-ABSENT | 56 → 62 | 0.751 | 0.315 | 32 → 38 |
| M-LABEL | 48 → 57 | 0.975 | **0.060** | 21 → 23 |
| M-PATH | 3 → 6 | 0.891 | 0.276 | 2 → 1 |
| M-SIGN | 0 → 0 | 1 | 1 | 0 → 0 |
| M-GAP (barred, reported) | 8 → 9 | 0.704 | 0.500 | 2 → 2 |
| M-ECHO (reported) | 52 → 46 | 0.269 | 0.806 | 26 → 18 |

- **No class metric worsens at p_upper ≤ 0.05.** The nearest is M-LABEL at 0.060, close to the line,
  and it is not a worsening by the registered rule. Its rise is read below.
- **The decision, verbatim:** "ships once the moves listed are explained in writing" (`ships: False`).
  It lists two moves:
  - "LLY: the lean moved ({'strongly-bullish': 5} → {'strongly-bullish': 4, 'mixed': 1}; proposal
    BUY → None)";
  - "SMPL: the lean moved ({'mixed': 4, 'strongly-bearish': 1} → {'strongly-bearish': 4, 'mixed': 1};
    proposal None → None)".
- **The panel's committed-lean draws: 10 → 10.** The score lists no panel shift.

**PER PAGE** (a $0 script on the registered scorer's own functions, `panel_inputs`, `arm_layer`,
`draw_units` and `score_units`, writing no score log; it reproduces all six totals and the
committed-lean count exactly).

| page | M-ABSENT | M-LABEL | M-PATH | M-ECHO | M-GAP | leans BASE → CAND | committed |
|---|---|---|---|---|---|---|---|
| BURL (held out) | 12 → 17 | 11 → 11 | 0 → 0 | 7 → 5 | 0 → 0 | bullish 2, mixed 3 → mixed 5 | 2 → 0 |
| CNXC (held out) | 13 → 15 | 5 → 7 | 0 → 1 | 13 → 10 | 1 → 1 | mixed 5 → mixed 4, bearish 1 | 0 → 1 |
| LLY | 3 → 2 | 6 → 8 | 0 → 2 | 11 → 15 | 2 → 2 | bullish 5 → bullish 4, mixed 1 | 5 → 4 |
| MCK | 20 → 20 | 12 → 16 | 1 → 1 | 4 → 7 | 3 → 2 | bullish 2, mixed 3 → mixed 5 | 2 → 0 |
| ROST (held out) | 7 → 6 | 5 → 5 | 2 → 0 | 6 → 3 | 1 → 1 | mixed 5 → mixed 4, bullish 1 | 0 → 1 |
| SMPL | 1 → 2 | 9 → 10 | 0 → 2 | 11 → 6 | 1 → 3 | mixed 4, bearish 1 → bearish 4, mixed 1 | 1 → 4 |

**WHAT THE FIX DID, read as the note pre-declared (descriptive; no decision reads these).**
- **Item 1, the rebuttal pattern.** Bull and bear points matching #920's M3 regex
  (`outweigh\w*|genuine…but`):

  | | draws with one | points with one | points |
  |---|---|---|---|
  | BASE | 13 of 30 (BURL 3, LLY 5, MCK 4, ROST 1) | 23 | 398 |
  | CAND | 0 of 30 | 0 | 399 |

  Fisher's exact on the draws, two-sided: p 4.6 × 10⁻⁵. #920's V3 (the example alone) moved this
  3/5 → 2/5; removing rule 7's template takes it to zero. The phrase rule 7 now prescribes ("what
  would have to be true …") appears 4 times in CAND (CNXC 3, ROST 1) and never in BASE.
- **Item 2, the ASK, on MCK** (the one panel page whose ASK moves). "Cause named" and "played out"
  appear in 2 BASE draws and in no CAND draw; "no cause" appears in 1 CAND draw. **One side effect,
  attributable:** 2 of the 5 CAND draws restate the new ASK ("no discrete gap-down, so no drawdown
  cause is named") and then fill it with "a gradual bleed" ("bleed/run-up", "bleed/rise"), in a key
  unknown. That is the label fix 3a removed, on a page whose price is near its 52-week high. It is
  MCK's whole M-LABEL `bleed` rise (0 → 2). "Has not reversed"-type wording: 1 → 2 draws.
- **Item 3, path words.** M-PATH 3 → 6 (p_upper 0.276). Read hit by hit:
  - BASE's 3: MCK's "~2% every year" margin; ROST's "second consecutive quarter" of comps, twice
    (a quarterly claim the annual series cannot judge).
  - CAND's 6: LLY "compounded without interruption … rising every reported year" and an
    "uninterrupted" `evidence_balance` (3 hits, one draw), over EBITDA that dips FY2018 → FY2019;
    MCK "rising every year from $3,858M (FY18)" over a dip FY2019 → FY2020; SMPL's bear point "rose
    every year from FY15 … then FELL in FY26" over a dip FY2016 → FY2017; SMPL's twin "wrote down
    acquired assets every year" (not the revenue series); CNXC's "second consecutive quarter"
    (quarterly).
  - **So rule 9's clause did not stop path overreach on this panel.** Real annual overreaches are
    BASE 1 (MCK) and CAND 3 (LLY, MCK, SMPL). The words the clause names are still written.
    Inside noise either way.
- **Item 4, the example.** The old example's words cannot echo from CAND: its request no longer
  carries them ("and x net leverage leaving" was #953's LLY echo). The new example's own words do
  echo, on LLY: "fcf was m against m" and
  "interest coverage is x and" are CAND-only M-ECHO phrases. M-ECHO overall fell 52 → 46.

**M-LABEL's rise, 48 → 57 (p_upper 0.060), read by family** (unit-family pairs over 30 draws per
arm): no-adjusted-forward 31 → 33, trailing-only 16 → 17, bleed 10 → 11, segment-undisclosed 5 → 6,
runway-not-derivable 1 → 1.
- The rise is spread across families and pages: MCK 12 → 16, CNXC 5 → 7, LLY 6 → 8, SMPL 9 → 10,
  BURL and ROST level.
- **Fix 4b reaches one of them:** MCK's bleed 0 → 2, through the new ASK, as above. MCK's
  trailing-only 1 → 4 and the gap-statement family's 31 → 33 are not in any span fix 4b moves.
  This record does not explain them; at 5 draws an arm they read as noise.

**THE TWO LEAN MOVES THE RULE LISTS, EXPLAINED.**
- **LLY: bullish 5 → bullish 4, mixed 1; the proposal goes from BUY to none.**
  - LLY's request differs only in SYSTEM and the tool schema (fix 4b's text); its facts are
    byte-identical.
  - **Within noise.** One dissent in ten draws, landing in CAND, has probability 0.5. LLY has read
    3/2, 4/1 and 5/0 bullish/mixed across #930's, #931's and #953's runs, the last on byte-identical
    requests. The proposal flips because production proposes only on five of five (row 53
    item 5): the unanimity gate, the operator's to rule on.
  - **A direction the fix could cause, not shown:** LLY's BASE draws closed bear points with a
    bullish rebuttal in 5 of 5 draws (12 points), and its CAND draws in none. A bear point left
    standing could read a draw toward mixed. One draw cannot show it.
- **SMPL: mixed 4, bearish 1 → bearish 4, mixed 1; no proposal in either arm.**
  - SMPL's request also differs only in SYSTEM and the tool schema; its anchor span is byte-equal.
    It had no rebuttal-closed point in either arm, so item 1 cannot act through that route here.
  - **Within its own range.** Given 5 committed of 10, four or more landing in CAND has probability
    0.103. SMPL read bearish 3 / mixed 2 and 4 / 1 in #953's two arms.
- **Exploratory, chosen after seeing the result (not a test):** the three pages where BASE wrote
  rebuttals most (BURL, LLY, MCK: 12 of the 13 draws) moved committed-bullish 9 → 4. The other
  three (CNXC, ROST, SMPL) read 1 → 6 committed. The panel total is level at 10 → 10. Rule 7's template may have been carrying
  bullish weight inside bear points. This run cannot separate that from noise, and nothing here is
  registered to.

**W34, READ AGAIN ON THESE DRAWS.**
- **The committed-lean count #953 left unexplained (8 → 15).** On this run it is 10 → 10, and the
  score lists no panel shift.
  - This is not a re-measurement of #953. #953 drew fresh builds of its own two commits
    (`--from-impact`). This run replays the frozen panel pages at main and at the fix. Its BASE is
    main, #953 included: 10 committed of 30.
  - What it adds to "watch leans": on the next panel run, the count did not move past the line.
    The same caveat as #953's holds: each page's five BASE draws ran before its five CAND draws, so
    arm and time order coincide.
- **BURL's candidate arm (1 usable of 5 in #953):** all 5 of 5 returned here, and all 60 draws in the
  run did. #953's four failures ("credential validation failed") were transient, not tied to the
  request. BURL reads bullish 2 / mixed 3 → mixed 5 here; in #953 its BASE read mixed 5.

**FOUND, NOT FIXED.**
- **The no-cause ASK's wording invites "bleed".** "Shows no discrete gap-down" is restated and filled
  with "gradual bleed" in 2 of 5 MCK CAND draws. A rewording (one that does not name the absence of
  a gap-down as a shape) is a prompt change with its own panel check. It is the operator's call
  whether this ships first.
- **Path overreach is not reduced by rule 9's clause** on this panel (above).
- **Review round 0's two skips** stand (the `_OUTWEIGHED` guard; M-ECHO on the prescribed phrase,
  which appeared 4 times).

**THE `drawn` ROW.** The claim appended one `drawn` row (claimed 2026-11-17T07:52:45Z, approval
`fb38e46c…`). It is appended to `docs/evals/registrations.jsonl`, byte for byte, after the
`registered` row #1095 merged.

**BOUNDARY.**
- **Pages:** the frozen panel v2 (freeze `bcda7ce3`).
- **Draws:** 5 per page per arm, 60 in all, drawn once under registration `e309bd25…`, claimed
  2026-11-17T07:52:45Z, run from main `47da911d`.
- **Code:** base `4889ddba`, cand `38c170fa`; scorer fingerprint `f4d14ee0…`.
- **Units:** units with a hit, summed over a page-arm's draws. A committed lean is a strongly-bullish
  or strongly-bearish draw.
- **M3, the prescribed phrase and the MCK words:** case-insensitive regex over each draw's decoded
  bull and bear claims (M3) or whole decoded output (the others).
- **p-values:** the metrics' from the registered stratified exact test. The lean probabilities are
  hypergeometric per page, as stated beside each. Fisher's two-sided for M3.
- **Kept outside the repo:** the requests, draws, score log, ledger and breakdown.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$30.7382 of the $35 approval;** $4.26 unspent. The cap was not raised.
- **Accepted, with its falsifier: LLY's and SMPL's lean moves are noise.** Falsified if the next
  panel run on main with fix 4b reads LLY below 4 bullish of 5 again, or SMPL at 4+ bearish of 5
  again, on requests this change moved.
- **Accepted: MCK's "bleed" restatement ships with the fix unless the operator rules otherwise.** It
  is a key-unknown wording on one page, inside the registered rule (M-LABEL p_upper 0.060).
  Falsified as minor if a rebuilt anchored page whose at-anchor part names no cause carries
  "bleed" in a bull or bear point.

