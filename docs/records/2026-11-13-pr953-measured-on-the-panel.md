---
id:
status: recorded
date: 2026-11-13
prs: [953]
supersedes:
superseded-by:
---

# #953 (RD-D1) measured on the panel after it merged, no-worsening only ($26.26 of $35.18): no class metric worsens (the nearest is M-PATH, 3 → 6 at p_upper 0.131), but the decision is "ships once the moves listed are explained in writing": LLY's and MCK's leans moved, and the panel's committed-lean draws rose 8 → 15 (two-sided p 0.0274); BURL's candidate arm has 1 usable draw of 5. The operator keeps the FACTS-only ruling and watches leans: "Keep it, watch leans (Recommended)"

**THE APPROVAL.**
- **The operator's approval of the run, verbatim:** **"Run it now, $35 cap (Recommended)"**.
- **The cap ruling, 2026-11-13, verbatim:** **"Estimate +20%, max $40 (Recommended)"**. The
  estimate was $29.32 by E2's cost model, so the cap is $35.18.
- **The go-ahead, 2026-11-13, verbatim:** **"Post, then register and draw (Recommended)"**.
- **The announcement:** posted on #1004 (issuecomment-6852843703) before the registration.
- **The budget:** one ledger for this check alone, opened at $35.18 with those three quotes. The
  sha256 of its first line is `fe8b9706…`, which is the `registered` row's approval.

**THE DESIGN** (RUNBOOKS §n, a retrospective `register --from-impact`).
- **The change measured:** #953, RD-D1 (fix request 2). It reports impairment headroom as goodwill
  and intangibles at one date, or UNKNOWN naming the dates, and a peer row never totals a missing
  leg as 0.0. #953 merged before any panel check: the hand-built compare of the time could not see
  its request move. Bookkeeping batch 3 (item 2) made this run the falsifier of the operator's
  ruling that a FACTS-only request move owes no paid panel by default ("Not needed; #953 is the
  test (Recommended)").
- **The export:** `pr953-586fdcfd-7ec84833`, whose `manifest.json` has sha256
  `0fb65dad551f641e3999312e65aeca3e58e4543efc5ca35444d3807167f1a2d7`.
  - It holds fresh $0 builds of the six panel pages, each made with its own arm's code.
  - All 12 arms are recapture-equal.
  - It is kept outside every repository, because requests carry licensed transcript text.
- **The registration:** sha256 `978a6a52d5f299719d8e8d2fa327336d9e1cd1f46e1720f6cc5dc48da24dd460`.
  - Its fields:
    - base `586fdcfd`, cand `7ec84833` (#953);
    - pages BURL, CNXC, LLY, MCK, ROST and SMPL;
    - 5 draws per page per arm;
    - alpha 0.05, no-worsening only, no target;
    - held out: CNXC and LLY;
    - `scorer_ref` `6a5a28f5`, scorer fingerprint `2dca01b7bf56…`.
  - Its `registered` row reached main in #1063 (`50d8337b`) before any draw (RG-D14).
- **The checkout it was drawn and scored from:** #953's BASE with main's `vinci/evals`,
  `docs/evals`, `tests/fixtures/synthesis_gold` and `vinci/graph/llm.py` (RUNBOOKS §n, as #1057
  states it). It was not refreshed between registration, draw and score.
- **What moves in the requests.** Only the `facts` section moves. The system prompt and the tool
  schema are byte-equal in the two arms on all six pages.

  | Page | facts, characters | USER lines changed | what moves |
  |---|---|---|---|
  | BURL | +1,082 | −57 +57 | `peer_capital_intensity`: 6 rows, BURL's own among them, go from a figure to null, each with a note naming its dates; GAP's figures change; URBN's and ANF's write-down windows move; the medians move |
  | CNXC | −2 | −9 +9 | `peer_capital_intensity`: FISV's and SSNC's figures, and one median |
  | LLY | 0 | none (byte-identical) | — |
  | MCK | +45 | −18 +18 | its own intangibles line (IntangibleAssetsNetExcludingGoodwill → FiniteLivedIntangibleAssetsNet, $1,678.0M → $3,942.0M) and its peer row ($12,950.0M → $15,214.0M); two peers' figures at rounding level; one peer leaves a median (7 → 6) |
  | ROST | +915 | −54 +54 | `peer_capital_intensity`: 5 rows, ROST's own among them, go from a figure to null, each with a note naming its dates; two notes added; GAP's figures change; URBN's and ANF's write-down windows move; the medians move |
  | SMPL | +223 | −14 +14 | `peer_capital_intensity`: MZTI's figures change, and JJSF's go to null with a note; the medians move |

**BEFORE THE SCORE: ONE ARM IS SHORT, AND IT IS THE PAGE THAT MOVED MOST.** These were found at $0
from `draws.jsonl`, before the score was run. The coordinator chose to score as registered, blind
to the result.
- **BURL:CAND has 1 usable draw of 5.**
  - Its draws 1 to 4 each failed with `InternalServerError: credential validation failed`. Each
    got no response and cost $0. The harness turns the SDK's retries off by design (one guarded
    call is one HTTP attempt), so each failed attempt is a failed draw.
  - Its draw 5 succeeded, on the same request bytes ($1.2317, the draw that wrote the cache).
  - **The timestamps.** The draw rows carry no timestamp, so the window is derived:
    - `requests.jsonl` was written at 13:14:27.7Z, and the last draw row at 14:36:45.3Z: 4,937.6 s.
    - The 56 priced draws record 4,932.0 s of their own. Everything else, including all four
      failed calls, fits in the remaining 5.6 s (8.4 s at most, allowing for each recorded duration
      being rounded to 0.1 s).
    - The failures came right after BURL:BASE's five draws, which took 402.2 s. So they fell
      between about 13:21:09.9Z and 13:21:18Z.
  - **One burst, not spread out.** The failures are the run's attempts 6 to 9, consecutive, with
    no other call between them. **No other arm hit this error or any other.** The other 55 draws
    all returned. The same request succeeded on the next attempt. That fits a transient fault on
    the credential path, not something specific to the request.
  - **What the registered rule does with it.** `score` refuses a page only when an arm has no
    usable draw. So BURL compares 5 BASE draws against 1 CAND draw, and the score prints "draws
    with no usable output: {'BURL:CAND': 4}". A re-draw into a second folder would leave the
    registration unscorable ("drawn more than once … none of them is scored").
- **BURL is the page with the largest facts move:** +1,082 characters, and 57 lines out and 57 in.
  ROST is next (+915; −54 +54). **So the falsifier is weakest exactly where #953 moved the most.**
  That limits what this result can say about the FACTS-only ruling, whichever way it reads.
- **The ledger shows 56 priced draws against the run's 60.**
  - The ledger records a draw only when it has a response to price.
  - `draws.jsonl` records every attempt: 60 rows, 5 for each of the 12 arms.
  - 60 − 4 failed = 56.
  - LLY's two arms did not share draws, although their requests are byte-identical. Each arm was
    drawn 5 times.

**THE RUN** (`run-compare --paid`, drawn once).
- **Who ran it.** The operator ran the draw command themselves, from a terminal, on 2026-11-13.
  The session preparing it had its own run of that command refused by its permission check, and
  did not work around the refusal.
  - The coordinator reports the run was made from the composite checkout above, with `.env` linked
    for it and unlinked after. `.env` is confirmed absent from the checkout afterwards, and the
    draw rows' SDK, 0.112.0, is the shared venv's.
  - It ran once: the ledger records one run folder under the registration, holding 60 draws.
  - The draw calls only the Anthropic API: `vinci/evals/` names neither Polygon nor Tiingo.
- **The draws:** 60 attempts, of which 56 returned.
  - Every one of the 56 stopped on `tool_use`, `claude-opus-4-8` served all of them, and all 56
    are usable.
  - Every one of the 60 draw rows states `sdk_version` **0.112.0**, so both arms ran on one SDK
    (STATE row 62). `replay.one_sdk` admits the run.
  - All 12 requests in the run's `requests.jsonl` hash to the registration's pins.
- **The cost: $26.2649**, from the run's own ledger. That is 10.4% under the $29.32 estimate, with
  $8.92 of the $35.18 cap left.
  - **Why it came in under:** BURL:CAND's four failed draws cost nothing. LLY:CAND read the cache
    LLY:BASE had written, because the two requests are byte-identical: its draw 1 cost $0.3061,
    against BASE's $1.6823.
  - Cache writes: 1,838,327 tokens. Cache reads: 7,895,814. Uncached input: 1,344. Output: 432,828.

  | Page | BASE | CAND |
  |---|---|---|
  | BURL | $2.2035 | $1.2317 (1 draw) |
  | CNXC | $2.0247 | $2.0383 |
  | LLY | $2.9666 | $1.6165 |
  | MCK | $2.3387 | $2.3619 |
  | ROST | $2.4050 | $2.3963 |
  | SMPL | $2.3000 | $2.3816 |

**THE SCORE, at $0** (`vinci.evals score`, from the same checkout, one score-log line at
2026-11-13T20:10:44+0530, scorer `2dca01b7bf56…`).

| Metric | BASE | CAND | p_lower | p_upper | held out (CNXC, LLY) |
|---|---|---|---|---|---|
| M-ABSENT | 99 | 68 | 0.330 | 0.746 | 19 → 20 |
| M-ECHO | 65 | 51 | 0.132 | 0.915 | 28 → 24 |
| M-LABEL | 30 | 22 | 0.137 | 0.969 | 9 → 8 |
| M-PATH | 3 | 6 | 0.975 | 0.131 | 0 → 4 |
| M-SIGN | 0 | 0 | 1 | 1 | 0 → 0 |

- **No class metric worsens at p_upper ≤ 0.05.** The class metrics are M-ABSENT, M-LABEL, M-PATH
  and M-SIGN. M-ECHO is printed but is not one of them. The nearest to the line is M-PATH, at
  p_upper 0.131.
- **The decision, verbatim:** "ships once the moves listed are explained in writing" (`ships:
  False`). The rule lists three moves:
  - "LLY: the lean moved ({'mixed': 1, 'strongly-bullish': 4} → {'strongly-bullish': 5}; proposal
    None → BUY)";
  - "MCK: the lean moved ({'mixed': 4, 'strongly-bullish': 1} → {'strongly-bullish': 4, 'mixed':
    1}; proposal None → None)";
  - "the panel's committed-lean draws moved 8 → 15 (two-sided p 0.0274)" (record §6.3).
- **M-GAP is not scored.** An impact arm is a fresh build with no page blob, and M-GAP is barred as
  a target in any case (RG-D13).

**THE TOTALS ARE NOT LIKE FOR LIKE: BURL HAS 5 BASE DRAWS AND 1 CAND DRAW.** The test is stratified
by page, so it compares within each page. The raw totals do not, and BURL's missing draws carry
most of the fall in M-ABSENT: without BURL, M-ABSENT is 65 → 63, M-LABEL 25 → 21, M-PATH 2 → 6
and M-ECHO 61 → 49.

Per page, units with a hit summed over the arm's usable draws (5, except BURL:CAND's 1):

| Page | M-ABSENT | M-LABEL | M-PATH | M-ECHO | M-SIGN | committed leans |
|---|---|---|---|---|---|---|
| BURL | 34 → 5 | 5 → 1 | 1 → 0 | 4 → 2 | 0 → 0 | 0 → 0 |
| CNXC (held out) | 14 → 17 | 4 → 3 | 0 → 4 | 14 → 10 | 0 → 0 | 0 → 0 |
| LLY (held out, identical request) | 5 → 3 | 5 → 5 | 0 → 0 | 14 → 14 | 0 → 0 | 4 → 5 |
| MCK | 27 → 23 | 6 → 3 | 0 → 0 | 12 → 9 | 0 → 0 | 1 → 4 |
| ROST | 14 → 9 | 5 → 4 | 2 → 2 | 10 → 9 | 0 → 0 | 0 → 2 |
| SMPL | 5 → 11 | 5 → 6 | 0 → 0 | 11 → 7 | 0 → 0 | 3 → 4 |

- These per-page counts come from a $0 script. It ran the registered scorer's `score_run` on a
  copy of the run folder, with no ledger so the real run's score log stays one line, and recorded
  the inputs to `stats.stratified_exact`. It reproduces the scorer's five totals and the
  committed-lean count exactly.
- **M-PATH's rise is all CNXC: 0 → 4.** M-PATH counts monotone wording ("every year",
  "unbroken"…) set against the page's own series. CNXC's request moved by 2 characters in its peer
  table. This record does not explain the rise, and the rule does not read it as a worsening.
- **M-ECHO phrases in CAND only, as `score` printed them.** These are 5-word runs from the
  request's instructions; by construction none is transcript text.
  - "ltm vs ntm peer spread" (BURL)
  - "capex m m reflecting heavy" (BURL)
  - "earned value trap or residual" (CNXC)
  - "vendor normalised x net debt" (CNXC)
  - "edge must resist not echo" (LLY)
  - "and x net leverage leaving" (LLY)
  - "earnings ltm levered fcf was" (MCK)
  - "a multiple at its own" (MCK)
  - "read beside the forward ntm" (ROST)

**THE THREE MOVES THE RULE LISTS, AND WHAT THIS RECORD CAN SAY ABOUT EACH.**

| Page | BASE leans | CAND leans | Proposal |
|---|---|---|---|
| BURL | mixed 5 | mixed 1 (1 draw) | none → none |
| CNXC | mixed 5 | mixed 5 | none → none |
| LLY | strongly-bullish 4, mixed 1 | strongly-bullish 5 | none → **BUY** |
| MCK | mixed 4, strongly-bullish 1 | strongly-bullish 4, mixed 1 | none → none |
| ROST | mixed 5 | mixed 3, strongly-bullish 2 | none → none |
| SMPL | strongly-bearish 3, mixed 2 | strongly-bearish 4, mixed 1 | none → none |

- **LLY: explained, it is not #953's. LLY is the control.** LLY's two requests are byte-identical,
  so this move cannot come from the change: it is draw noise.
  - One draw of five went from mixed to strongly-bullish: draw noise of about 1 in 5 on this page
    in this run. On byte-identical requests in RE2-D16's run, MCK and ROST moved by 2 to 3 draws in
    5, so 1 in 5 is not the ceiling.
  - The proposal flips because production proposes only on unanimous draws
    (`verdict.derive_proposal`): 4 of 5 proposes nothing, 5 of 5 proposes BUY. **One identical
    request moved a proposal in this run.** That is the noise floor of a 5-draw proposal on a page
    that sits one draw from unanimity.
- **MCK: not distinguishable from noise at 5 draws; not attributed.**
  - The move is 3 draws of 5. It is the same size, and the same shape, as MCK's move on a
    BYTE-IDENTICAL request in RE2-D16's run (mixed 4 / strongly-bullish 1 → mixed 1 /
    strongly-bullish 4; `docs/records/2026-11-11-re2-d16-measured-on-the-panel.md`).
  - Read against the words #953 moved: 2 of the 4 strongly-bullish CAND draws mention none of
    "goodwill", "intangib…" or "impairment", and the CAND draw that stays mixed mentions them most
    (8 times). No draw in either arm states the moved figures ($15,214M, $3,942M, $12,950M or
    $1,678M, in the forms searched), and none names BHIC or MEDS, the two peers whose rows moved.
    This finds no sign that the moved lines carry the move; it does not show that they do not.
- **The panel's committed-lean count, 8 → 15: measured, not explained.** It is the one move past
  the registered line. It is not attributed to #953, and not dismissed as noise.
  - By page: LLY 4 → 5, MCK 1 → 4, ROST 0 → 2, SMPL 3 → 4, BURL 0 → 0 (on 1 CAND draw), CNXC
    0 → 0. The test is stratified by page and two-sided: p 0.0274.
  - **LLY's +1 is noise by construction** (identical request). Without it the count is 4 → 10.
  - ROST's two strongly-bullish CAND draws mention none of the words above. They also mention
    none of "acquisit…", "M&A", "capital intensity", "write-down", "wrote down", "written down" or
    "write-off", nor URBN, ANF or VSXY, three of the peers whose rows moved. BURL, GAP, TJX and
    CURV, the others, were not searched.
  - **One alternative this design cannot exclude:** each arm's five draws run consecutively, with
    BASE's before CAND's on every page. So arm and time order go together, and a drift in serving
    over the ~7 minutes between them would read as the change. Nothing here shows such a drift; the
    design cannot rule it out.

**WHAT THIS MEANS FOR BATCH 3'S FACTS-ONLY RULING** ("Not needed; #953 is the test
(Recommended)"). One change, five moved pages, all of them FACTS-only moves, 5 draws per arm.
- **What it supports:** on these five pages, no class metric worsened beyond the registered line.
  Read as "a FACTS-only move worsens a class metric", the falsifier did not fire.
- **What it does not support:**
  - **That a FACTS-only move leaves the synthesis alone.** The panel's committed-lean count moved
    past the registered line (8 → 15, p 0.0274), and the rule leaves it to a written explanation
    that this record cannot give. More committed leans is not a worsening under any registered
    metric, but it is a measured effect on output.
  - **Anything about BURL, the largest move.** It is measured against one CAND draw, so the
    falsifier is weakest exactly where #953 moved the most.
  - **Any other change.** #953 moves peer capital-intensity rows and one intangibles line. A
    FACTS-only move of another kind, or of another size, is not measured here.
  - **Small worsenings.** At 5 draws per arm, a class metric could worsen by less than this design
    detects.
  - **Improvement.** There is no target, so nothing here says FACTS-only moves improve a read.

**THE OPERATOR'S RULING** (2026-11-13, after reading this result), verbatim: **"Keep it, watch
leans (Recommended)"**.
- **FACTS-only request moves still owe no paid panel by default.** Batch 3's item 2 stands.
- **The panel-level committed-lean shift** (8 → 15 draws, two-sided p 0.0274) is recorded as
  measured and NOT explained.
- **The next panel run re-checks leans before any conclusion is drawn.** That is the "watch leans"
  item:
  - its owner is the fix-request-2 coordinator (A), and the next panel run unlocks it;
  - it is kept in this record, which reads `recorded`, so no §5.0 row opens for it.
- **The written explanations the registered rule asks for**, as this record gives them above:
  - LLY's move is on byte-identical requests, so LLY is the control and shows draw noise of about
    1 in 5 on a page;
  - MCK's move matches an identical-request move in an earlier run (RE2-D16's);
  - the panel shift is unexplained.

**THE `drawn` ROW.**
- **What this record commits** is the one `drawn` row the draw's claim appended in the composite
  checkout, byte for byte. It is appended to main's `docs/evals/registrations.jsonl` after the
  `registered` row.
- **Its fields:** claimed at 2026-11-13T13:14:27Z; approval `fe8b9706…`, which equals the
  `registered` row's approval and the sha256 of the ledger's first line.

**BOUNDARY.**
- **Pages:** the six panel pages, as fresh builds from the impact export above.
- **Draws:** 5 attempts per page per arm, 60 in all, drawn once under registration `978a6a52…` and
  claimed at 2026-11-13T13:14:27Z. 56 returned; BURL:CAND has 1 usable draw.
- **Code:** base `586fdcfd`, cand `7ec84833`, scorer `scorer_ref` `6a5a28f5` (fingerprint
  `2dca01b7…`), drawn and scored in one composite checkout, read with main at `81f97600`.
- **Counts:** every metric count is the number of units with a hit, summed over a page-arm's usable
  draws. A committed lean is a draw whose lean is strongly-bullish or strongly-bearish.
- **Mention counts:** case-insensitive regex over each usable draw's whole tool output. Three
  vocabularies, as named above: goodwill / intangibles / impairment on all six pages; the moved
  figures, acquisitions, M&A, capital intensity and write-downs on MCK and ROST; write-offs and the
  moved peers' names (URBN, ANF, VSXY, BHIC, MEDS) on BURL, MCK and ROST. "Mentions none" means
  none under these searches, not that no draw reads the moved lines.
- **Request sizes:** characters of the USER `facts` section, as the registration records them;
  lines from a diff of the two arms' captured USER messages.
- **Cost:** $26.2649 of the $35.18 approval, from the run's own ledger.
- **SDK:** `anthropic` 0.112.0, as stated by all 60 draw rows.
- **Kept outside the repo:** the requests, draws, score log and ledger, under
  `/Users/mac/dev/panel-exports/pr953-run/`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **BURL is scored on one CAND draw, as the registered rule allows.** The coordinator chose that
  before the score was seen. *Falsifier:* a later check on BURL whose metrics or lean differ from
  this run's BASE arm by more than its 5-draw spread.
- **The committed-lean move is left unexplained, and FACTS-only moves still owe no paid panel**
  (the operator's "Keep it, watch leans (Recommended)"). The next panel run re-checks leans before
  any conclusion is drawn. *Falsifier:* a later panel run whose committed-lean count moves past
  the registered line again on a FACTS-only change would say FACTS-only moves do move leans. A
  later registration that draws the arms interleaved and finds the count unmoved would point to
  draw order instead.
