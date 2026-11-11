---
status: recorded
date: 2026-11-11
prs: [1005]
supersedes:
superseded-by:
---

# Fix 6 is dropped ($0): a claim only one of the five draws makes is no more likely to misread a fact — in each of six arm-runs, at the registered threshold, one-draw claims carry no more M-LABEL or M-GAP hits than claims most draws make (3 M-LABEL hits and 0 M-GAP hits at agreement 1, in all six together), and the gold's recurrence AUC is 0.46–0.52 in every arm

**THE START.**
- **The operator, 2026-11-11, verbatim:** **"Yes, start fix 6"**.
- **The brief** is the coordinator's of 2026-11-09, updated 2026-11-11. The update named the
  M-GAP gold and the other stored runs, and set **"Analyse each arm on its own; never pool across
  prompt versions."**
- **The lane.** Analysis only. A fix 6 build would be coordinated on GitHub issue #1004 first.
  No paid or LLM API call was made.

**WHAT.**
- **Fix 6** was "flag a claim only one of the five draws makes; needs a $0 test first". This is
  that test.
- **The question.** Each synthesis is drawn 5 times. Is a claim 1 of the 5 draws makes more likely
  to misread a fact than one most draws make? If yes, cross-draw agreement would be a cheap,
  model-free error signal.
- **It is not.** Each arm of each stored run was read on its own (six arm-runs, six pages each).
  - **On both calibrated draw-level metrics,** one-draw claims carry no more errors than majority
    claims. In most arms they carry none.
  - **On the frozen 644-claim gold,** which covers all eleven error classes, recurrence across
    later draws does not separate errors from correct claims.
- **The bar was registered before any label was read,** and no arm meets it. **Fix 6 is dropped;**
  no code and no proposal ship.

**THE RESULT IN SIX LINES.**
- **#926's run, M-LABEL** (the pre-registered primary). "Majority" here means units that ≥3 draws
  make.
  - BASE: **2 of 48** one-draw units carry a hit, against 65 of 827 majority units (7.9%). MH risk
    ratio over pages **0.50 [0.00, 1.13]**.
  - CAND: **0 of 51**, against 46 of 832 (5.5%).
  - After the blind re-check: BASE 2/33, 0.72 [0.00, 1.64]; CAND 0/35.
  - The bar was RR ≥ 2 with a lower bound above 1.
- **The four replication arms read the same way.**
  - #921's run: BASE 1/49 (RR 0.24), CAND 0/41.
  - Fix 4a's run: BASE 0/41, CAND 0/50.
  - Across the six arm-runs, 3 M-LABEL hits sit at agreement 1. No arm's interval clears 1 under
    any registered exposure.
  - Only two estimates anywhere exceed 1, both on #926's BASE arm, both near 1, and both resting on
    one or two hits: 1.07 at τ 0.15 (1 of 11 units), and 1.06 stratified by length.
- **M-GAP, the other calibrated metric, reads 0 hits at agreement 1 in all six arm-runs**
  (0 of 17 to 0 of 31 each).
  - Majority units read 8.4–12.2%, and 1.3% in fix 4a's CAND arm, which removed the rule M-GAP
    catches.
  - The M-GAP gold has 221 of #926's units, double-coded. It holds 51 errors, and none of them sits
    at agreement 1.
- **The 644-claim gold shows nothing.** It holds the 138 committed claims on the panel's six pages.
  How many of an arm's five draws make each claim does not separate its errors from its correct
  claims: AUC **0.46–0.52 in each of the six arm-runs**, and every interval spans 0.5.
- **Why.** The draws are independent samples of one prompt's distribution; #978 found no dependence
  between them. Agreement therefore estimates how much of that distribution a claim holds. An error
  built into the prompt holds much of it, so most draws repeat it. Because the draws are
  independent, agreement cannot see a cause that every draw shares.
- **Even an effect would catch little.** One-draw units are 41–51 of the 905–961 units in each
  arm-run (about 5%). They hold 0–2 of each arm's 35–69 M-LABEL hit-units.

## 1. The data, and what each part can label

| run | registration | base / cand | transforms | draws |
|---|---|---|---|---|
| **#926's** (`r926`, primary) | `cceba9d9` | `e00db8cd` / `e91490ae` (#923) | fix 3a's five | 60: 5 × 6 pages × 2 arms |
| #921's panel run (`r921`) | `7169261d` | `dc5b8787` / `b109e26c` | none | 60 |
| fix 4a's run (`r927`) | `06ed949b` | `15f45d38` / `564baad8` (#927) | six | 60 |

- **Six arm-runs, never pooled.** Each arm of each run is its own prompt version. Every ratio
  below is a Mantel–Haenszel ratio over that arm-run's six pages. Its interval is a cluster
  bootstrap over draws within each page (2,000 resamples, seed 6).
  - An earlier version of this record, in this PR, headlined figures pooled across runs and arms.
    They pointed the same way. They are withdrawn, not quoted, under the brief's no-pooling rule.
- **What was read.** The draws are model output, kept in this session family's notes folder
  outside the repo. No request was read: requests carry licensed transcript text. No metric here
  reads a transcript, so every page context was built with `transcript=None`.
- **Not used.** #921's NFLX run, one page with 10 draws. One page cannot carry a page-stratified
  ratio, and the six-page runs decide.

**The labels, and how each applies:**

| label | what it is | how it labels a draw unit |
|---|---|---|
| **M-LABEL** | code-written labels repeated against the page's facts; TEST precision 22/32, recall 22/27 | directly. Scorer `git archive fc79a7be`, #926's registered one, on the panel's frozen blobs at `bcda7ce3`. It reproduces #926's logged totals exactly: M-LABEL 69/47, M-ABSENT 60/48, M-PATH 7/4, M-SIGN 0/0 |
| **M-GAP** | a gap the page's gap test does not type a change, framed as a risk or carried by a bear point; met its TEST bar (precision 0.833, recall 0.882, kappa 0.827, `docs/records/2026-11-09-m-gap-gold-and-metric.md`) | directly, on key-unknown and bear-point units. Main's `gap_framing` at `8a72be4c`, with each page's blob checked. It reproduces fix 4a's recorded 37 → 4 |
| **the M-GAP gold** | 221 of #926's draw units (key unknowns and bear points), double-coded blind: a SUBJECT census of 161 gap-stating units plus 60 RANDOM | directly. The gold IS draw units, matched by page, arm, draw and unit id |
| **the 644-claim gold** | the 28 committed pages at `bcda7ce3`, double-coded, 172 adjudicated | **not directly.** A committed page keeps only its chosen draw; the other four went to the git-ignored `llm_call.log`, which also carries the request. The facts are the panel's own (`freeze_ref` = `bcda7ce3`), but the committed draw came from an OLDER prompt than any arm. So the gold measures **recurrence**: how many of an arm's five draws make the committed claim. Copying a gold verdict onto a matched draw unit was rejected, because it would label a claim by its neighbour's coding |

- **M-ABSENT, M-PATH and M-SIGN are not used as labels.** M-ABSENT's TEST precision is 3/14.
  M-PATH fires on 21 units of the three runs and M-SIGN on none.

## 2. "The same claim" — defined before any error label was read

**The order of events.** Times are file times, 2026-11-11 IST.

| time | what was written |
|---|---|
| **16:54:27** | `matcher.py` (sha256 `d8e1f3d4…`) and the plan (`c455cf91…`) |
| **16:56:39** | the plan's addendum 1: the blind re-check |
| **16:57:37** | the first M-LABEL label |
| **17:10:10** | addendum 2, the brief update: per-arm reporting, M-GAP and its gold. The plan is now `9c0260f3…` |
| after 17:10:10 | M-GAP's hits computed, and the M-GAP gold's labels opened |

**The matcher.** It is unchanged since 16:54:27.
- **Tokens.** Each unit becomes its figures, as production's `synthesis._claim_figure_ends` reads
  them (the one parser), plus its content words: lower-case, three letters or more, a fixed
  stopword list, a light suffix strip.
- **Weights.** TF-IDF, with the IDF computed over one page × arm × run. Similarity is cosine.
- **Agreement.** A unit is MADE by another draw of its arm when some unit of that draw has
  cosine ≥ τ. agreement = 1 + the number of such draws, so 1 to 5.
- **The threshold.** τ = 0.22, chosen on 70 hand-labelled pairs from `r921`, never from `r926`.
  The pairs were drawn 10 per cosine bin and labelled blind to the cosine and to every label.

**How well it matches.**

| check | sample | result |
|---|---|---|
| pairs, calibration (`r921`) | 70, stratified by cosine | at τ 0.22: 62/70 strict, 65/70 counting partial overlaps; population-weighted accuracy 0.86 / 0.92 |
| pairs, held out (`r926`) | 35, 5 per bin, labelled after the freeze | 30/35 strict (pop-weighted 0.81), 33/35 loose (0.93) |
| "only one draw makes it" (`r926`) | 15 random agreement-1 units, each against the best unit of the other four draws | 7 truly one-draw, 2 partial, 6 made by another draw in other words (twins, paraphrased key unknowns) |
| **blind re-check** (all three runs) | all 280 matcher-agreement-1 units, each against the top 2 candidates of every other draw, ordered by id, no cosine, no label | **201 stay one-draw** counting only "yes" as made (72%); 128 counting "partial" too (46%) |

- **The weak point is the low end.** A lexical matcher misses paraphrase. Misclassification
  dilutes the one-draw cell toward its arm's overall rate. It cannot by itself push the cell below
  that rate.
- **The re-check.** It was pre-registered as addendum 1 and run by three independent subagents, one
  per run, which saw no label.
  - **Reliability:** on the 15 units this session hand-checked, the `r926` reader agrees 13/15 when
    only "yes" counts as made, and 14/15 when "partial" counts too.
  - **A caveat:** the three readers are instances of one model, so their consistency is not that of
    independent readers.
  - **The exposures.** "Verified" counts only "yes". "Verified-loose" counts "partial" as made.

## 3. M-LABEL, by arm-run

Each cell gives one-draw units, then majority units (≥3 draws). RR is MH over pages, 95% bootstrap.

| arm-run | units / hits | matcher | verified | verified-loose |
|---|---|---|---|---|
| **r926 BASE** | 949 / 69 | 2/48 vs 65/827 (7.9%) — **0.50 [0.00, 1.13]** | 2/33 vs 7.8% — **0.72 [0.00, 1.64]** | 1/18 — 0.64 [0.00, 2.13] |
| **r926 CAND** | 961 / 47 | 0/51 vs 46/832 (5.5%) — 0 | 0/35 vs 5.5% — 0 | 0/20 — 0 |
| r921 BASE | 943 / 68 | 1/49 vs 8.0% — 0.24 [0.00, 0.73] | 1/39 — 0.29 [0.00, 0.89] | 0/30 — 0 |
| r921 CAND | 939 / 65 | 0/41 vs 7.8% — 0 | 0/27 — 0 | 0/15 — 0 |
| r927 BASE | 935 / 43 | 0/41 vs 5.3% — 0 | 0/33 — 0 | 0/20 — 0 |
| r927 CAND | 905 / 35 | 0/50 vs 4.4% — 0 | 0/34 — 0 | 0/25 — 0 |

- **"0" marks an empty hit cell.** There the ratio's bootstrap interval is degenerate, and the
  Wilson bound on the cell's rate is the statement. For example, r926 CAND reads 0/51, at most
  7.0%, against 5.5%.
- **The three hits at agreement 1, all verified one-draw:**
  - r926 BASE, ROST draw 3, a key unknown ("bleed");
  - r926 BASE, SMPL draw 2, a bear point ("bleed");
  - r921 BASE, MCK draw 1, a key unknown ("trailing-only" and "no adjusted forward").
- **Thresholds** (registered sensitivity; matcher exposure; one-draw hits / units in each arm):

  | setting | r926 BASE | r926 CAND | r921 BASE | r921 CAND | r927 BASE | r927 CAND |
  |---|---|---|---|---|---|---|
  | τ 0.15 | 1/11, RR 1.07 [0.00, 3.50] | 0/13 | 0/17 | 0/12 | 0/12 | 0/15 |
  | τ 0.30 | 4/143, 0.31 [0.08, 0.56] | 0/135 | 2/148, 0.14 | 2/130, 0.18 | 0/147 | 1/151, 0.12 |
  | same-section, τ 0.22 | 3/85, 0.42 [0.00, 0.84] | 1/92, 0.18 | 5/91, 0.62 [0.12, 1.31] | 1/91, 0.13 | 0/77 | 0/84 |

  No lower bound clears 1. The only estimate above 1 is τ 0.15's r926 BASE, on a single hit.
- **No single arm is large enough to exclude a doubling tightly.** r926 BASE's verified cell is
  2/33, Wilson [0.017, 0.196], against 7.8%. What decides it:
  - the bar needs a lower bound above 1, and none of the six arms has one;
  - not one arm shows an excess;
  - four of the six hold no hit at all in their one-draw cell.

## 4. M-GAP and its gold, by arm-run

**M-GAP's hits** on key-unknown and bear-point units.

| arm-run | units / hits | matcher: one-draw vs majority | verified one-draw |
|---|---|---|---|
| r926 BASE | 396 / 39 | 0/24 vs 38/345 (11.0%) | 0/15 |
| r926 CAND | 403 / 29 | 0/25 vs 29/347 (8.4%) | 0/21 |
| r921 BASE | 393 / 40 | 0/31 vs 40/328 (12.2%) | 0/24 |
| r921 CAND | 401 / 42 | 0/17 vs 41/354 (11.6%) | 0/11 |
| r927 BASE | 388 / 37 | 0/17 vs 36/343 (10.5%) | 0/15 |
| r927 CAND (fix 4a) | 372 / 4 | 0/30 vs 4/304 (1.3%) | 0/27 |

**The M-GAP gold** (`r926` only; 221 units; outcome = the gold's `error`):
- **BASE:** 110 units, 27 errors. Agreement 1 holds 0/4 by the matcher and 0/4 verified. The
  majority holds 27/103.
- **CAND:** 111 units, 24 errors. Agreement 1 holds 0/5 by the matcher and 0/3 verified. The
  majority holds 24/102.
- **The SUBJECT census** (gap-stating units) has 1 unit at agreement 1 per arm, and neither is an
  error.
- **What the gap gold says.** The gap-stating units are what nearly every draw writes, so the one
  question this gold can answer at agreement 1 has almost no units to answer it with. All 51 of its
  errors sit on units several draws make. Fix 4a's prompt rule ("a missing disclosure is a BEARISH
  risk", replaced by #927) was in every draw's request.

## 5. The 644-claim gold: recurrence of the committed claim, by arm-run

The gold holds 138 claims on the six panel pages, with 57 errors (13 material).
- **The claims by half:** DEV (BURL, CNXC, LLY, MCK) 94 claims, 39 errors; TEST (ROST, SMPL)
  44 claims, 18 errors.
- **The errors by class:** ABSENT 24, LABEL 13, OVERREACH 5, BASIS 4, STALE 3, PATH 3, CONFLICT 2,
  SIGN 2, PERIOD 1.
- **Recurrence** is how many of the arm-run's five draws make the claim, by the same matcher, with
  the IDF over that arm's units plus the gold claims. BASE arms use the blind re-check of the 34
  low-recurrence claim-runs; CAND arms use the matcher alone.

| arm-run | recurrence 0: errors | recurrence ≥3: errors | AUC, error recurs less [95%] | DEV | TEST | non-LABEL |
|---|---|---|---|---|---|---|
| r926 BASE | 2/7 | 47/116 | 0.461 [0.375, 0.547] | 0.453 | 0.472 | 0.480 |
| r926 CAND | 1/3 | 49/115 | 0.508 [0.424, 0.592] | 0.516 | 0.495 | 0.512 |
| r921 BASE | 3/9 | 48/114 | 0.502 [0.418, 0.589] | 0.500 | 0.503 | 0.515 |
| r921 CAND | 2/5 | 46/113 | 0.518 [0.432, 0.605] | 0.521 | 0.505 | 0.530 |
| r927 BASE | 4/6 | 48/116 | 0.510 [0.425, 0.600] | 0.504 | 0.527 | 0.528 |
| r927 CAND | 4/9 | 42/107 | 0.524 [0.435, 0.615] | 0.520 | 0.531 | 0.527 |

- **The recurrence-0 cells hold 3–9 claims,** so a single cell is noise. The AUC uses every claim.
- **RUNBOOKS §n step 7.** The gold's TEST half was "read once" for metric calibration. It is read
  here as an outcome for a signal fitted to nothing in it. That is stated so that any later
  agreement-based metric tuned with this result in mind says it reads TEST in-sample.

## 6. Confounds, per arm-run, stated whichever way they cut

- **Length.** One-draw units are shorter: median 205–228 characters, against 256–269 at
  agreement 5, in every arm-run. A longer unit has more room for a label phrase.
  - Verified, MH over page × length tertile: r926 BASE **1.06 [0.00, 2.63]**; r921 BASE 0.37
    [0.00, 1.07]; the other four arms 0.
  - r926 BASE's 1.06 rests on two hits. With τ 0.15's 1.07 (§3), it is one of the two estimates
    above 1 anywhere, and neither interval excludes 1 or reaches the bar.
- **Section.** One-draw units lean to key unknowns and twins: 23–40 of each arm's 41–51.
  - Twins carry no M-LABEL hit in any arm.
  - Key unknowns carry most hits, because "no forward/adjusted basis … trailing-only" is a key
    unknown nearly every draw writes.
  - Verified, MH over page × section: r926 BASE 0.58 [0.00, 1.47]; r921 BASE 0.16 [0.00, 0.41];
    the other four arms 0.
- **Bull vs bear.** Bull points hold 2–6 one-draw units per arm and bear points 3–9. No bull point
  at agreement 1 carries an M-LABEL hit; one bear point does. The cells are too small to find an
  asymmetry, and they show none. A flag would have had to be symmetric anyway.
- **Page** is the stratum of every ratio.

## 7. What cross-draw agreement can and cannot mean here

- **#978's independence result is what this needs, not a counter to it.** It tested the LEAN
  across builds and found no overdispersion (X² 11.58 on 15 df). Independent samples make agreement
  an unbiased estimate of a claim's share of the prompt's distribution. They do not make that share
  track fidelity: a misreading the prompt induces is a high-share claim.
- **The vote rule (#982) is not touched by this.** It gates the decision variable, the lean, where
  the draws' spread IS the uncertainty it reports. Fix 6 asked a different question: whether a
  CLAIM's spread reports its error. It does not.
- **Ten draws would not help.** The ten-draw confirmation that C(iv) runs at `log-verdict` would
  estimate each claim's share more precisely, but would not change what the share measures. At five
  draws the measured errors already sit at the top of the agreement scale.

## 8. The verdict

**Agreement does not predict error enough to act on, so fix 6 is dropped. No design is proposed.**
- **The registered bar.** RR ≥ 2 with a lower bound above 1 on #926's run in each arm, replicated in
  direction on r921's and r927's arms, surviving section and length.
- **What the runs show.** In #926's arms the point estimate is 0.50 and 0, or 0.72 and 0 verified.
  No arm of any run has a lower bound above 1. M-GAP reads zero one-draw hits in all six arm-runs.
  The gold's AUC is 0.46–0.52 in each arm.
- **What would reopen it: an error class that is not systematic.** That is a misreading one draw
  invents and the others do not. ABSENT (a figure the facts do not hold) is the plain candidate,
  with OVERREACH next.
  - No calibrated reader of either class exists on a draw today: M-ABSENT's TEST precision is 3/14,
    and the judge failed its bar.
  - Once one exists at a stated precision, these six arm-runs re-score at $0. The matcher, the blind
    re-check and every script are kept for that (BOUNDARY).
  - **Falsifier:** that reader finds one-draw units at ≥ 2× the majority rate, with a lower bound
    above 1, in #926's arms and in the same direction elsewhere. Then this record is superseded and
    fix 6 reopens, narrowed to that class, to be coordinated on #1004.
- **Not proposed instead.** Majority units do carry the label and gap errors. A flag on them would
  mark most of a page's units, and fixes 3a and 4a already remove those errors at the source.

**HOW VERIFIED.**
- **The scorers.** M-LABEL's scorer reproduces #926's logged totals exactly, and M-GAP's reproduces
  fix 4a's recorded 37 → 4.
- **The matcher.** Frozen, with its plan, before any label; both addenda were written before the
  labels they govern (§2). It was calibrated on another run, hand-checked on a held-out sample, and
  every one-draw unit was re-checked blind.
- **The counts.** Every count above was printed by a script run on the stored draws (BOUNDARY).
  The three subagents are this session's readers, not API calls.

**BOUNDARY.**
- **Draw units.** Every unit of `draw_units` at `fc79a7be` (`units.py` is unchanged on main
  `8a72be4c`), all sections. Per arm-run, 30 draws over BURL, CNXC, LLY, MCK, ROST and SMPL:

  | arm-run | units |
  |---|---|
  | r926 BASE / CAND | 949 / 961 |
  | r921 BASE / CAND | 943 / 939 |
  | r927 BASE / CAND | 935 / 905 |

  M-GAP reads key-unknown and bear-point units only: 372–403 per arm-run. Its gold holds 110–111
  units per arm of `r926`.
- **Agreement** is counted within one page × arm × run, out of its 5 draws.
- **"A hit"** is ≥ 1 hit on the unit:
  - M-LABEL by `score_units` at `fc79a7be`, on the panel's blobs at `bcda7ce3`, with no transcript;
  - M-GAP by `gap_framing` at main `8a72be4c`, with each page's blob checked against
    `synthesis_gap_types.json`.
- **The golds.**
  - The 644-claim gold's final label is the adjudicated record, else the agreed coding
    (`vinci/evals/gold.py`), on the 138 claims of the six panel pages.
  - The M-GAP gold's `error` comes from `tests/fixtures/synthesis_gap_gold/gold.jsonl`, on 221
    units.
- **Measured** 2026-11-11. The gold fixtures, `gold.py` and `units.py` are byte-identical between
  `3d55bc31`, where the first scripts ran, and `e3f715b0`, this PR's base.
- **Files.** Scripts and outputs are in the notes folder
  `…/side-session-notes/local_7e5fb8ce-…/fix6-agreement-test/`:
  - the matcher and its plan: `matcher.py`, `PREREG.md` with both addenda;
  - the scoring scripts: `run_match.py`, `score_units.py`, `score_mgap.py`;
  - the analysis scripts: `analyse2.py` (per arm-run), `gold_recur_arms.py`, `gold_arms.py`;
  - the calibration, evaluation and re-check samples with their labels.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** No paid or LLM API call; three analysis subagents read model output only.
- **Accepted: the test reads two error classes on draws**, LABEL and gap framing, both of them
  systematic. It reads the gold's other classes only through an older prompt's draw. A
  non-systematic class could still track agreement; the falsifier in §8 says what would show it.
