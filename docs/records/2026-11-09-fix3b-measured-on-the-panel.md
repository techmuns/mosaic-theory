---
status: recorded
date: 2026-11-09
prs: [930]
supersedes:
superseded-by:
---

# Fix 3b (#930) measured on the panel, no-worsening only ($30.72 of $35): no class metric worsened (the lowest p_upper is M-PATH's 0.22); two modal leans moved and are explained here. LLY went bullish 3 / mixed 2 → bullish 5, so its proposal moves from none to BUY. That is within one page's noise (p 0.22), and the draws do not trace it to the text 3b deletes. The score's decision: "ships once the moves listed are explained in writing"

**THE APPROVAL.** Operator, 2026-11-09, verbatim: **"approve #930's panel check, cap $35"**.
- One budget ledger was opened with those words: `synthesis-eval-fix3b/ledger-fix3b.jsonl`, in
  the session family's notes folder.
- The registration, the run folder (`run-fix3b/`: draws, requests, score log) and the logs are
  kept there too, outside the repository. The requests carry licensed transcript text and never
  enter git.
- #930 was frozen at `e205bf66` for the measurement. The cap was not raised.

**THE RESULT IN SIX LINES.**
- **By the registered rule, fix 3b passes the no-worsening checks.** No class metric reaches
  p_upper ≤ 0.05 over 30 draws per arm. The score's decision is "ships once the moves listed are
  explained in writing"; §4 is that writing.
- **The class metrics:**
  - M-LABEL 30 → 33 (p_upper 0.26), gated on every family, as #930's §5 registered it;
  - M-ABSENT 58 → 58, M-PATH 2 → 5 (p_upper 0.22), M-SIGN 0 → 0;
  - M-GAP 3 → 1, and M-ECHO 60 → 50 (reported).
- **Two modal leans moved; one moved a proposal:**
  - **LLY:** bullish 3 / mixed 2 → bullish 5, so the proposal goes from none to **BUY**;
  - **BURL:** mixed 3 / bullish 2 → bullish 3 / mixed 2, with no proposal in either arm.
  - ROST's modal lean held (mixed), but its two committed draws went to none. The panel's
    committed-lean draws went 11 → 12.
- **Fix 3b's own changes:**
  - **Its deleted values:** none of the four stale buyback values it blanks appears in any draw of
    either arm. They are BURL's 52.30, LLY's 0.0 share count, MCK's 13.9M and MCK's 151.23.
  - **The self-funding read it drops from the survival line:** units that mention self-funding fell
    54 → 34 (descriptive, not a scored metric).
- **Spend:** $30.7240 of $35; 60 calls, none failed.

## 1. The $0 cross-check, before the ledger

- **The panel rule** yields the frozen six: BURL, CNXC, LLY, MCK, ROST and SMPL.
- **Setup:**
  - `compare` ran main `622786a2` → #930 `e205bf66` on panel v2, with the seven transforms
    `relabel_drawdown_shape trailing_only_note survival_read peer_gap_question print_row_guide
    gap_types current_buybacks`;
  - it ran from a detached checkout of `e205bf66`, as #931 ran from #927's head;
  - it read the primary checkout's `data/manual/ciq`, read only.
- **Inputs, by name and sha256**, as the panel freeze and each page's input record state them:
  - the page blobs `627fe21a` (BURL), `604d559d` (CNXC), `ef07b22f` (LLY), `761787c0` (MCK),
    `a4bf3989` (ROST) and `0b4ff8eb` (SMPL);
  - the six comps exports `e302c4c0…`, `aa822ebf…`, `ce7897dc…`, `158bc7e1…`, `7171baef…` and
    `647fa707…`, the same as #931's run;
  - every transcript.
- **The first compare was refused.** MCK's transcripts were on disk with a " (1)" suffix, though
  each sha256 matched the freeze. A transcript's file name enters the request, so the harness
  refuses a renamed file.
  - The coordinator put the choice to the operator.
  - The operator renamed the ten affected files in the Drive folder. Nothing was re-frozen.
  - The coordinator re-checked the names and sha256s, and step 1 was re-run from the top, clean.
- **Every page differs in `user.facts` only.** SYSTEM, the tool schema and every other kwarg are
  equal, byte for byte. Each diff is one of 3b's own spans:
  - **The survival line**, in its two places on each page:
    - the value loses its FCF tail: `| FCF-positive → self-funding` on five pages, and
      `| FCF sign UNKNOWN — runway not assessable` on LLY;
    - the source loses `+ FCF sign`.
  - **BURL:** the 2015 average repurchase cost (52.30) becomes UNKNOWN ("no current figure").
  - **LLY:**
    - the 2021 share count (0.0) becomes UNKNOWN, and its cash PERIOD MISMATCH note is dropped;
    - the average-price refusal reads "not current" for "absent";
    - one gap item is reworded to "the FCF sign (quality.fcf_sign)".
  - **MCK:** the 2019–20 share count (13.9M) and the 2020 average (151.23) become UNKNOWN, and the
    cash mismatch note is dropped.
- **Prompt size, in characters as `compare` measures each section.** SYSTEM and the tool schema are
  equal across arms on every page.

  | page | SYSTEM | tool | facts BASE → CAND | total BASE → CAND | Δ |
  |---|---|---|---|---|---|
  | BURL | 7,649 | 8,508 | 314,384 → 313,944 | 454,386 → 453,946 | −440 (−0.097%) |
  | CNXC | 7,649 | 8,508 | 267,743 → 267,649 | 366,839 → 366,745 | −94 (−0.026%) |
  | LLY | 7,680 | 8,679 | 454,222 → 453,784 | 649,734 → 649,296 | −438 (−0.067%) |
  | MCK | 7,680 | 8,679 | 340,029 → 339,276 | 486,456 → 485,703 | −753 (−0.155%) |
  | ROST | 7,680 | 8,679 | 314,294 → 314,200 | 461,376 → 461,282 | −94 (−0.020%) |
  | SMPL | 7,649 | 8,508 | 320,872 → 320,778 | 479,811 → 479,717 | −94 (−0.020%) |

  These are exactly the deltas #930's record §3 and §5 predicted.

## 2. What was registered, before any draw

- **Registration** `4d6fe10ef5203286dfa517b3233b76dd498608b5041d7854bf1660e617eb8223`:
  - `origin/main` (`622786a2` at registration) → `e205bf66` on panel v2, with the seven
    transforms and five draws per page per arm;
  - **no target**, `no_worsening`, alpha 0.05; held out: none;
  - all 12 requests pinned, and the draw's re-capture matched every one: BURL `43d44bd2ca22` /
    `47bbd4210ebc`, CNXC `8a08896ba503` / `eeadb7c6a74f`, LLY `6515cd17c893` / `9bb586e54132`, MCK
    `522283134401` / `21800fb99664`, ROST `a7f06a1747dc` / `33261190dc69`, SMPL `877bd445c600` /
    `4f3c3ca0d0f1` (BASE / CAND).
- **The scorer:** the files at `e205bf66`, fingerprint `ec145038…`.
- **The note,** inside the sha, is #930's §5 note verbatim: "fix 3b: no target can fire on the
  panel (3 units in #926's 60 draws, all LLY); the run reads the no-worsening checks only".
- **One deviation from #930's §5, ruled before any draw.** In the coordinator's words: "§5 proposed
  `--ship-alpha 0.01`; `register` refuses it with `--no-worsening` (since 2026-11-07); registered
  without it, nothing else changed (coordinator, before any draw)".
- **M-LABEL is gated on ALL its families.** No `--no-worsening-families` was registered and #931's
  three were not copied. The coordinator ruled this, for two reasons:
  - both arms carry `gap_types`, so the gap-statement miscount is common to both arms;
  - `runway-not-derivable` is the one family that reads 3b's survival-line change.
  - Every family is reported below.

## 3. The result, by the registered rule

| metric | BASE → CAND (units, 30 draws each) | p |
|---|---|---|
| M-LABEL (gated, all families) | 30 → 33 | p_upper 0.263 |
| M-ABSENT | 58 → 58 | p_upper 0.544 |
| M-PATH | 2 → 5 | p_upper 0.222 |
| M-SIGN | 0 → 0 | p_upper 1.00 |
| M-GAP | 3 → 1 | p_upper 0.875 |
| M-ECHO (reported) | 60 → 50 | p_upper 0.914 |

- **The score's decision:** "ships once the moves listed are explained in writing". The two moves it
  lists are BURL's and LLY's modal leans (§4).
- **M-LABEL by family**, as unit-family pairs over 30 draws per arm. No unit carried two families,
  so the pairs sum to the metric's units.

  | family | BASE → CAND | per page (BASE → CAND) |
  |---|---|---|
  | no-adjusted-forward | 24 → 27 | BURL 4 → 5, CNXC 3 → 4, MCK 3 → 4; LLY 5, ROST 4, SMPL 5 unchanged |
  | segment-undisclosed | 5 → 5 | MCK 5 → 5 |
  | bleed | 1 → 1 | ROST 1 → 0, SMPL 0 → 1 |
  | trailing-only | 0 → 0 | — |
  | runway-not-derivable | 0 → 0 | — |
  | pe-percentile-blocked | 0 → 0 | — |

  - **The one rise is `no-adjusted-forward`,** a gap-statement family (the draw says no adjusted
    forward basis or guide exists). It rose by one draw on each of three pages.
    - Fix 3b touches no forward, guidance or adjusted field on any page (§1).
    - Both arms carry the same `gap_types` block.
    - The gated whole moves at p_upper 0.263, so it is not a worsening by the registered rule.
  - **`runway-not-derivable` never fires in either arm,** so the run cannot show its effect.
- **Per page, units per draw:**

  | page | M-LABEL BASE / CAND | M-ABSENT BASE / CAND | M-PATH BASE / CAND | M-GAP BASE / CAND | M-ECHO BASE / CAND |
  |---|---|---|---|---|---|
  | BURL | 1,0,1,1,1 / 1,1,1,1,1 | 5,5,1,3,3 / 3,4,4,0,4 | 0,0,1,0,0 / 0,0,0,0,0 | 0,1,0,0,0 / 0,0,0,0,0 | 1,1,3,0,1 / 1,3,2,1,2 |
  | CNXC | 1,0,0,1,1 / 1,1,0,1,1 | 3,3,2,2,2 / 2,1,2,3,2 | 0,0,0,0,0 / 0,0,0,1,1 | 0 / 0 | 1,0,3,1,0 / 0,3,1,0,2 |
  | LLY | 1,1,1,1,1 / 1,1,1,1,1 | 0,0,1,0,1 / 0,1,0,1,0 | 0,0,0,0,0 / 0,0,0,0,1 | 0 / 0 | 4,4,5,2,4 / 2,2,3,2,4 |
  | MCK | 2,2,2,1,1 / 2,2,1,2,2 | 8,5,3,3,3 / 5,5,2,6,6 | 0,0,0,1,0 / 0,0,0,0,0 | 0 / 0 | 0,2,2,2,2 / 1,2,3,2,2 |
  | ROST | 2,0,1,1,1 / 1,0,1,1,1 | 1,0,0,0,1 / 0,0,0,2,0 | 0,0,0,0,0 / 0,1,0,0,0 | 0,0,2,0,0 / 0,0,0,0,0 | 2,1,3,3,1 / 1,2,1,0,1 |
  | SMPL | 1,1,1,1,1 / 2,1,1,1,1 | 1,1,1,0,0 / 1,0,2,0,2 | 0,0,0,0,0 / 0,0,1,0,0 | 0,0,0,0,0 / 0,0,1,0,0 | 1,1,4,3,3 / 1,2,1,1,2 |

- **M-PATH 2 → 5** is the class move nearest to 3b's subject, so its hits are listed.
  - **BASE's 2:** BURL and MCK, "every year" claims on EBITDA and revenue.
  - **CAND's 5:**
    - CNXC ×2: management's "second consecutive" record quarter of adjusted FCF;
    - LLY: EBITDA "climbed every year";
    - ROST: a second consecutive double-digit comp;
    - SMPL: two consecutive years of revenue decline.
  - **The two CNXC units are both self-funding bull points,** the subject of the read 3b removes
    from the survival line: with that line no longer saying "self-funding", two CAND draws argued
    it from the FCF figures and quoted management's path claim.
  - At p_upper 0.222 this is within noise. It is recorded as the one class move on 3b's subject,
    not explained away.
- **M-GAP 3 → 1:**
  - BASE: BURL ×1 (a bear point framing a missing item) and ROST ×2 (key unknowns called "risk");
  - CAND: SMPL ×1 (a single-segment bear point).
- **M-ECHO 60 → 50.** SYSTEM and the tool schema are byte-equal across arms, so both arms are scored
  against the same instruction text. By page it fell on LLY 19 → 13, ROST 10 → 5 and SMPL 12 → 7,
  and rose on BURL 6 → 9, MCK 8 → 10 and CNXC 5 → 6.

## 4. The lean and proposal moves, explained in writing as the rule requires

- **LLY: bullish 3 / mixed 2 → bullish 5; the proposal goes from none to BUY.**
  - **What the mixed draws weigh.** BASE's two mixed draws (draws 3 and 5) set earned fundamentals
    against the valuation premium (EV/EBITDA 28x against a 15.0x peer median, +87%) and persistent
    net-price erosion.
    - CAND's five bullish draws name the same two counterweights, for example "the premium price and
      persistent net-price erosion must still be beaten".
    - No mixed draw names the survival line, the FCF sign or the buyback as its counterweight.
  - **3b's LLY text sits in draws of both leans:**
    - All five BASE draws, three bullish and two mixed, list the FCF sign as a key unknown tied to
      the survival line's runway leg.
    - All five CAND draws list the FCF sign as a key unknown too, framed as a question of FCF
      basis.
    - The one draw that cites the share count 3b blanks (as period-mismatched, in a key unknown) is
      BASE draw 3, a mixed draw whose balance names the premium and price erosion.
  - **It is within one page's noise.**
    - Given 8 committed draws of LLY's 10, the chance that all five of CAND's draws are among them
      is 0.222.
    - In two runs of the prompt with #927's gap test, the same page read 4 / 1 (#931's CAND arm) and
      3 / 2 (this run's BASE): 7 of 10.
    - At a 0.7 rate, five of five occurs 16.8% of the time.
  - **It cannot be excluded either.** Fix 3b removes a caution-worded clause from LLY's survival
    line ("FCF sign UNKNOWN — runway not assessable"). Five draws per arm cannot tell a small effect
    in that direction from noise.
  - **The proposal is the unanimity gate's question (STATE row 53 item (5)).** A five-draw build
    proposes LLY's BUY only if no draw dissents. #931 recorded the same gate flipping the other
    way, BUY → withheld, on one dissent. The gate is the operator's to rule on.
- **BURL: mixed 3 / bullish 2 → bullish 3 / mixed 2; no proposal in either arm.**
  - The mixed draws in both arms name the same counterweights: decelerating comps, near-term
    estimate cuts, and a multiple still at a premium to peers.
  - Fix 3b removes a POSITIVE read from BURL's layer ("FCF-positive → self-funding") and the 2015
    average cost (52.30). The lean moved toward bullish, the opposite of what losing a positive
    read predicts.
    - Self-funding mentions on BURL held at 7 → 7.
    - 52.30 appears in no draw of either arm.
  - It is one draw. Given 5 committed of 10, three or more landing in CAND has probability 0.50.
- **ROST** is not flagged by the score, since its modal lean is mixed in both arms. Its
  distribution moved: bullish 2 / mixed 3 → mixed 5.
  - This IS the direction 3b's survival-line change would predict. BASE draw 1, a bullish draw,
    cites "FCF-positive and self-funding" in a bull point, and ROST's self-funding bull points fell
    4 → 2.
  - Against it: MCK, where self-funding mentions fell most (13 → 3), kept its leans exactly
    (mixed 3 / bullish 2 in both arms).
  - Given 2 committed of 10, both landing in BASE has probability 0.222.
- **The panel's committed-lean draws went 11 → 12,** in both directions: LLY +2, BURL +1, ROST −2.
  The exact stratified test gives p_upper 0.50 and two-sided 1.0.

## 5. What fix 3b's own spans did to the output (descriptive; no metric is fitted to them)

- **The four stale values 3b blanks never reached an output in either arm.** No unit in 60 draws
  contains BURL's 52.30, LLY's 2021-01-01 / 2021-06-30 share window, MCK's 13.9M or MCK's 151.23.
  - One CAND regex hit on "52.3" is CNXC's "−852.3", which is unrelated.
  - So on this panel, 3b's (a) half removes text the model was not using, and the run cannot show a
    benefit from it. That matches #930's own count of 3 units in #926's 60 draws, all on LLY.
- **The self-funding read is the half the output did use:**
  - units mentioning self-funding fell 54 → 34;
  - by page: MCK 13 → 3, CNXC 12 → 9, SMPL 10 → 8, BURL 7 → 7, LLY 7 → 5, ROST 5 → 2;
  - the remaining mentions draw on the layer's separate primary-source check ("self-funding: YES"),
    which 3b leaves in place.
- **LLY's units mentioning "runway" fell 34 → 23.** The survival line no longer ties the FCF sign to
  a runway, but the word also carries the growth "runway" in both arms.
- **No M-ABSENT hit in either arm flags one of 3b's deleted values** (71 BASE and 68 CAND hit
  rows).
  - The scorer reads CAND draws against BASE's layer (STATE row 53 item (6)). The two layers differ
    only in 3b's spans (§1), so the caveat could act only through them.
  - For M-ABSENT on this run, it had nothing to act on.

## 6. How the score was run

- **The CLI could not reach the transcripts.** `python -m vinci.evals score` takes no `--ciq-root`.
  Its default, `replay.DEFAULT_CIQ_ROOT`, is a home-relative path to the assembler's checkout,
  which does not exist on this machine.
- **The first invocation was refused before any scoring:** "BURL: transcripts on disk [] differ
  from the panel". No score was computed, and no score-log line was written; the run folder had no
  `score_log.jsonl` after it.
- **The score was then run once,** through the same `compare.score_run` the CLI calls:
  - its `pages` and `transcripts` were loaded by `replay.panel_inputs(…, ciq_root=…)`, at the root
    `run-compare` read;
  - `panel_inputs` checks every page blob and transcript sha256 against the freeze, as the CLI path
    does;
  - `score_run` wrote the run's one score-log line (20:17:55 +05:30).
- **Open (STATE row 53 item (8)):** `score` should take `--ciq-root`, as `compare`, `register` and
  `run-compare` do. That is a harness PR of its own.

## 7. What this measurement does not cover

- **No target.** No metric is fitted to 3b's two changes, so the run reads only that nothing
  worsened. On the panel, 3b's buyback half touches text the model never cited (§5).
- **`runway-not-derivable`**, the family that reads the survival line, fires 0 → 0. Its effect is
  unmeasured.
- **CAND is scored against BASE's layer** (STATE row 53 item (6), DEFERRED). §5 shows it had no value
  to act on here, but M-ECHO's index still reads BASE's layer for CAND.
- **Five draws per arm** cannot separate a small directional lean effect on LLY or ROST from noise
  (§4).

**BOUNDARY.**
- **Draws:** 60, `claude-opus-4-8` on every call, 60 of 60 ended in `tool_use`.
  - When: 2026-11-09, after the ledger opened (18:39:45 +05:30) and before the score
    (20:17:55 +05:30). Calls took 5,568.9 s summed.
  - Five per page per arm, BASE then CAND, page by page.
  - `draws.jsonl` sha256 `d9af8b0b581735b711dbabe89028e65ce58e514bad8c4ba41078cf940de6d2a5`.
- **Requests:** main `622786a2` and #930 `e205bf66`, each with the seven transforms, all 12 pinned.
  Pages: the frozen panel v2 (freeze `bcda7ce3`).
- **Units:** `units.draw_units`, counted per draw with at least one hit.
  - M-LABEL families are unit-family pairs.
  - The §5 counts are units whose text matches a regex: descriptive, not a metric.
- **Scorer:** the files at `e205bf66`, fingerprint `ec14503800776fe9…`.
- **p:**
  - for the metrics, the exact stratified permutation test over each page's ten draws;
  - for the lean moves, the per-page hypergeometric probability stated beside each;
  - for the committed-lean count, the exact stratified test over the six pages.
- **Cross-check sizes:** characters per section, as `compare` reports each request.
- **Spend:** production's `cost_usd`, summed from the ledger: BASE $15.3528 and CAND $15.3712.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $30.7240 of $35; $4.2760 unspent.
- **Accepted, with its falsifier: on this panel, fix 3b's buyback half is unmeasurable** (§5).
  - It is falsified as harmless if a page whose committed output cites a stale buyback leg goes on
    to cite it after 3b ships.
- **Recorded, not resolved:** LLY's proposal move to BUY rides on the unanimity gate. That is the
  operator's ruling (row 53 item (5)), not this run's.
