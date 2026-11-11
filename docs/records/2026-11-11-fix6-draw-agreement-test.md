---
status: recorded
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix 6 is dropped ($0): a claim only one of the five draws makes is NOT more likely to misread a fact — the calibrated metric's errors sit on the claims most draws make (MH RR 0.30 [0.00, 0.70] on #926's run, replicated on two more), and the gold's 138 claims on the panel pages show no separation (AUC 0.49 [0.40, 0.58])

**WHAT.** Prompt fix 6 in the coordinator's program read "flag a claim only one of the five draws
makes; needs a $0 test first". This is that test. Each synthesis is drawn 5 times; the question was
whether a claim made by 1 of the 5 is more likely to misread a fact than one most draws make. If so,
cross-draw agreement would be a cheap, model-free error signal. **It is not.** On the one calibrated
draw-level metric (M-LABEL) the effect runs the wrong way: one-draw claims carry FEWER errors. On the
frozen gold, which covers all eleven error classes, recurrence across later draws does not separate
errors from correct claims. The bar registered before any label was read is not met on any part, so
**fix 6 is dropped and no code ships.**

**THE RESULT IN SIX LINES.**
- **#926's run (the pre-registered primary).** 60 draws, 1,910 units. Units only one draw makes:
  **2 of 99** carry an M-LABEL hit (2.0%). Units ≥3 draws make: **111 of 1,659** (6.7%).
  Mantel–Haenszel risk ratio over page × arm **0.30, 95% [0.00, 0.70]**. The bar was RR ≥ 2 with a
  lower bound above 1.
- **It replicates, in the wrong direction.** #921's panel run: 1 of 90 against 7.9%, RR 0.13
  [0.00, 0.42]. Fix 4a's run: 0 of 91 against 4.9%. The point estimate is below 1 at every
  threshold, with same-section matching, and within section and within length tertile. No pooled
  interval reaches 1.
- **The blind re-check does not move it.** All 280 units the matcher calls one-draw were re-read
  blind; 201 stay one-draw. On #926's run: **2 of 68** (2.9%) against 6.6%, RR **0.43
  [0.00, 0.97]**. Pooled over the three runs: 3 of 201, RR 0.22 [0.00, 0.46].
- **The gold shows nothing.** The 138 claims on the panel's six pages are the committed draw. How
  many of 15 later draws make each claim does not separate the 57 errors from the 81 correct claims:
  AUC **0.49 [0.40, 0.58]**; non-LABEL errors 0.51 [0.41, 0.62]; material errors 0.45 [0.30, 0.61].
- **Why.** The errors this program has measured are systematic. A label the fact layer wrote, or a
  figure the facts do not hold, is in every draw's prompt, so most draws repeat it. Agreement among
  five draws of ONE prompt measures sampling noise, not fidelity: they are not independent readers.
- **Even a flag with an effect would catch little.** One-draw units are 280 of 5,632 (5.0%), and
  they hold 3 of the 327 units with an M-LABEL hit (0.9%).

## 1. The data, and what each part can label

| source | what it is | what labels it | how it enters |
|---|---|---|---|
| **#926's run** (`r926`) | registration `cceba9d9`; base `e00db8cd`, cand `e91490ae`, fix 3a's five transforms; 5 draws × 6 pages × 2 arms = 60, all usable | M-LABEL, at the registered scorer `fc79a7be` | **primary**, both arms |
| #921's panel run (`r921`) | base `dc5b8787`, cand `b109e26c`, no transform; 60 draws | the same scorer | replication, named before any label was read; also the matcher's calibration run (its text only, §2) |
| fix 4a's run (`r927`) | base `15f45d38`, cand `564baad8`, six transforms; 60 draws | the same scorer | replication, named before any label was read |
| the gold | 644 claims on the 28 committed pages at `bcda7ce3`, double-coded blind, 172 adjudicated (`tests/fixtures/synthesis_gold/`) | its own final verdicts | secondary, on the 138 claims of the six panel pages |

- **The draws live in this session family's notes folder** (`synthesis-eval-fix3a/`, `synthesis-eval-pr2/`,
  `synthesis-eval-fix4a/`). They are model output. No request was read: requests carry licensed
  transcript text. M-LABEL reads no transcript; every page context was built with `transcript=None`.
- **The scorer reproduces #926's logged score exactly.** M-LABEL 69 / 47 units, M-ABSENT 60 / 48,
  M-PATH 7 / 4, M-SIGN 0 / 0. That uses `draw_units` and `score_units` from `git archive fc79a7be`,
  on the panel's frozen blobs read at `bcda7ce3`.
- **Only M-LABEL is fit to label a draw unit.** Its TEST precision is 22/32 and its recall 22/27
  (`docs/records/2026-11-06-synthesis-eval-harness-design.md`). M-ABSENT's TEST precision is 3/14 and
  its recall 3/32. M-PATH fires on 21 of 5,632 units and M-SIGN on none. M-ABSENT is reported in §4 as
  a proxy, never as a label.
- **The gold cannot label a draw unit directly.** It codes the 28 COMMITTED pages, and each page keeps
  only its chosen draw: `synthesize` writes the other four to `llm_call.log`, which is git-ignored and
  also carries the request. The gold's 28 pages are the panel's freeze (`synthesis_panel.json`
  `freeze_ref` = `bcda7ce3`), so the facts are identical. The committed draw came from an OLDER prompt
  than any BASE arm, though. The gold therefore measures **recurrence**: how many of a run's five BASE
  draws, by the same matcher, make the committed claim. That is a sixth draw from an earlier prompt,
  not a sixth draw of the same one. Transferring a gold verdict onto a matched draw unit was rejected:
  it would label a claim by its neighbour's coding.

## 2. "The same claim" — defined before any error label was read

**The matcher** was frozen before any label was computed. Times are file times, 2026-11-11 IST:
- **16:54:27** — `matcher.py` (sha256 `d8e1f3d4…`) and the plan (`c455cf91…`).
- **16:56:39** — the plan's addendum 1, the blind re-check (`9e304b0f…`).
- **16:57:37** — the first error label, `labels.jsonl`.

The matcher itself:
- **Tokens.** Each unit becomes its figures, read by production's `synthesis._claim_figure_ends`
  (the one parser), plus its content words (lower-case, three letters or more, a fixed stopword list,
  a light suffix strip).
- **Weights.** TF-IDF, with the IDF computed over one page × arm × run (all five draws).
  Similarity is cosine.
- **Agreement.** A unit is MADE by another draw when some unit of that draw has cosine ≥ τ.
  agreement = 1 + the number of such draws, so 1 to 5.
- **τ = 0.22** was chosen on 70 hand-labelled pairs from `r921`, never from `r926`. The pairs were
  drawn 10 per cosine bin and labelled blind to the cosine. Sensitivity runs at τ 0.15 and 0.30, and
  with same-section matching.

**How well it matches.**

| check | sample | result |
|---|---|---|
| pairs, calibration (`r921`) | 70, stratified by cosine | at τ 0.22: 62/70 strict, 65/70 counting partial overlaps; population-weighted accuracy 0.86 / 0.92 |
| pairs, held out (`r926`) | 35, 5 per bin, labelled after the freeze | 30/35 strict (pop-weighted 0.81), 33/35 loose (0.93); the misses are partial overlaps called matches |
| **"only one draw makes it"** (`r926`) | 15 random agreement-1 units, each against the best unit of the other four draws | **7 truly one-draw, 2 partial, 6 made by another draw in other words** (twins, paraphrased key unknowns) |
| blind re-check (all three runs) | all 280 matcher-agreement-1 units, each against the top 2 candidates of every other draw | **201 stay one-draw** counting only "yes" as made (72%); 128 counting "partial" as made too (46%) |

- **The weak point is the low end.** A lexical matcher misses paraphrase, and twins are the worst
  case. Misclassification that sends true multi-draw units into the agreement-1 cell dilutes that cell
  toward the overall rate. It cannot by itself push the cell BELOW the overall rate. The observed rate
  (2.0% against 6.7%) is below it, so the matcher's error cannot hide a positive effect.
- **So every agreement-1 unit was re-checked BLIND** (pre-registered as addendum 1, before any label).
  That covered 280 units across the three runs, plus the 34 gold claim-runs at recurrence 0 or 1.
  The work went to three independent subagents, one per run. Each saw the target and the top two
  candidates of every other draw, ordered by unit id with no cosine shown and no error label.
  - **Reliability.** On the 15 units this session hand-checked, the r926 reader agrees 13/15 when
    only "yes" counts as made, and 14/15 when "partial" counts too. Both strict differences are
    partial-versus-yes borderlines.
  - **The readers are three instances of one model.** Their consistency is not two independent
    readers, the same caveat M-GAP's gold states.
  - **Two exposures.** "Verified" below counts only "yes". "Verified-loose" counts "partial" as made.

## 3. The primary: M-LABEL by agreement

**#926's run, matcher exposure (τ 0.22, any section).** The interval is Wilson's.

| agreement | units with an M-LABEL hit | rate | 95% |
|---|---|---|---|
| 1 | 2 / 99 | 0.020 | [0.006, 0.071] |
| 2 | 3 / 152 | 0.020 | [0.007, 0.056] |
| 3 | 7 / 226 | 0.031 | [0.015, 0.063] |
| 4 | 8 / 344 | 0.023 | [0.012, 0.045] |
| 5 | 96 / 1,089 | 0.088 | [0.073, 0.106] |

- **The contrast.** Agreement 1 against agreement ≥ 3: crude 0.020 vs 0.067, risk difference −0.047
  [−0.069, −0.019].
- **The adjusted ratio.** MH RR over page × arm 0.30, 95% **[0.00, 0.70]**, from a cluster bootstrap
  over draws within each page × arm (2,000 resamples, seed 6).
- **What it rules out.** The registered bar was a doubling. The agreement-1 cell's upper Wilson bound
  (7.1%) barely reaches the ≥3 rate, so a doubling is excluded.

**Replication and sensitivity** (agreement 1 vs ≥ 3; MH RR over run × page × arm):

| exposure | r926 | r921 | r927 | pooled (5,632 units) |
|---|---|---|---|---|
| matcher τ 0.22 (registered) | 2/99 vs 6.7% — **0.30 [0.00, 0.70]** | 1/90 vs 7.9% — 0.13 [0.00, 0.42] | 0/91 vs 4.9% — 0 | 3/280 vs 6.5% — **0.16 [0.00, 0.34]** |
| τ 0.15 | 1/24 — 0.65 [0.00, 2.04] | 0/29 — 0 | 0/27 — 0 | 1/80 — 0.20 [0.00, 0.63] |
| τ 0.30 | 4/278 — 0.18 [0.05, 0.32] | 4/278 — 0.16 [0.04, 0.31] | 1/298 — 0.06 [0.00, 0.17] | 9/854 — 0.14 [0.07, 0.22] |
| same-section, τ 0.22 | 4/177 — 0.32 [0.08, 0.58] | 6/182 — 0.38 [0.12, 0.72] | 0/161 — 0 | 10/520 — 0.27 [0.12, 0.42] |
| **verified** (re-checked, "yes" only) | **2/68 vs 6.6% — 0.43 [0.00, 0.97]** | 1/66 vs 7.8% — 0.17 [0.00, 0.55] | 0/67 vs 4.8% — 0 | **3/201 vs 6.5% — 0.22 [0.00, 0.46]** |
| verified-loose ("partial" = made) | 1/38 — 0.39 [0.00, 1.24] | 0/45 — 0 | 0/45 — 0 | 1/128 — 0.12 [0.00, 0.37] |

- **A bootstrap "[0.00, 0.00]" is printed as "0".** It means an empty agreement-1 cell, where the
  ratio's interval is degenerate. The Wilson bound on that cell's rate is the honest statement:
  0/91 is at most 4.1% against 4.9%.
- **Every point estimate is below 1**: every exposure, every run and pooled.
- **Three r926 intervals reach past 1:**
  - τ 0.15: 1 of 24, upper bound 2.04. Only 24 units sit at agreement 1 there, and the two other
    runs read 0 of 27–29.
  - verified-loose: 1 of 38, upper bound 1.24.
  - verified and stratified by length: upper bound 1.46 (§4).
- **Not one pooled interval reaches 1.** Only τ 0.15's tiny r926 cell reaches a doubling.

## 4. Confounds, stated whichever way they cut

- **Length.** One-draw units are shorter: median 213 characters against 262 at agreement 5. A longer
  unit has more text for a label phrase to sit in. Within length tertiles (222 / 273 characters) the
  agreement-1 cells read 0/14 long, 2/32 mid, 0/53 short on r926. The MH RR stratified by length is
  **0.41 [0.00, 0.99]** on r926 and 0.22 [0.00, 0.47] pooled. On the verified exposure it is
  0.61 [0.00, 1.46] on r926 and 0.30 [0.00, 0.63] pooled.
- **Section.** Agreement-1 units lean to key unknowns (36 of 99 on r926) and twins (28). Twins carry
  no M-LABEL hit in any run (0 of 838 pooled). Key unknowns carry most of them (263 of 1,294 pooled),
  because "no forward/adjusted basis … trailing-only" is a key unknown nearly every draw writes.
  Within section the r926 cells are:

  | section | agreement 1 | agreement ≥ 3 |
  |---|---|---|
  | bear | 1/13 | 15/326 |
  | bull | 0/11 | 10/417 |
  | key unknowns | 1/36 | 86/366 |
  | decisive question | 0/9 | 0/291 |

  The MH RR stratified by section is **0.21 [0.00, 0.52]** on r926 and 0.11 [0.00, 0.22] pooled.
  On the verified exposure it is 0.28 [0.00, 0.69] and 0.14 [0.00, 0.28].
- **Bull vs bear.** The agreement-1 cells are 0/28 bull and 1/35 bear, pooled. That is too small to
  find an asymmetry and shows none.
- **Page × arm** is the stratum of every MH ratio above. On r926, 10 of the 12 page × arm cells have
  0 hits at agreement 1. ROST BASE (1/3) and SMPL BASE (1/9) hold the two.
- **The family of the error.** Pooled, 213 of 215 "no adjusted forward" hit-units and 128 of 130
  "trailing-only" ones sit at agreement ≥ 3. The two families are the code-written labels fix 3a
  targets. "Bleed" is the one family with a visible low-agreement share: 7 of 30 at agreement ≤ 2,
  against 13% of all units. That is post hoc and n = 30, so it is noted, not acted on.
- **M-ABSENT, as a proxy only** (TEST precision 3/14). Pooled MH RR 1.06 [0.65, 1.51]; stratified by
  section 1.05; by length 1.26 [0.78, 1.84]. One run, r921, reads 2.12 [1.11, 3.18]. It does not
  replicate: r926 reads 0.42 and r927 0.82. On the verified exposure r921 reads 1.00 [0.00, 2.15]
  and the pool 0.79 [0.37, 1.27]. A metric whose hits are 79% false on TEST cannot carry the decision
  either way.
- **The family figures above** count each hit-unit once under every family it matches.

## 5. The gold: recurrence of the committed claim across later draws

The 138 gold claims on the six panel pages hold 57 errors, 13 of them material. By class:
ABSENT 24, LABEL 13, OVERREACH 5, BASIS 4, STALE 3, PATH 3, CONFLICT 2, SIGN 2, PERIOD 1. Each
claim's recurrence is how many of a run's five BASE draws make it (matcher, IDF over that page's
BASE units plus its gold claims).

| recurrence, of 5 BASE draws | r926 | r921 | r927 |
|---|---|---|---|
| 0 | 2/7 errors | 2/6 | 2/3 |
| 1 | 0/2 | 3/7 | 2/9 |
| ≥ 2 | 55/129 (0.43) | 52/125 (0.42) | 53/126 (0.42) |

Pooled over the three runs (recurrence 0–15 of 15 later draws):

| recurrence | errors | rate | 95% |
|---|---|---|---|
| 0–4 | 3/9 | 0.33 | [0.12, 0.65] |
| 5–9 | 10/23 | 0.43 | [0.26, 0.63] |
| 10–14 | 17/42 | 0.40 | [0.27, 0.56] |
| 15 | 27/64 | 0.42 | [0.31, 0.54] |

- **Discrimination.** The chance that an error claim recurs LESS than a correct one is
  **AUC 0.488 [0.395, 0.579]** (bootstrap over claims, 2,000).
- **Subsets.** Material errors read 0.450 [0.304, 0.605]; errors outside LABEL 0.514 [0.414, 0.615].
- **Bear points** read 0.613 (16 errors / 18 OK). That is a post-hoc subgroup of 34 inside an AUC
  whose interval spans 0.5, so it is noted, not acted on.
- **The blind re-check changes nothing here either.** It re-read the 34 claim-runs at recurrence 0
  or 1, and moved r921's recurrence-0 cell from 6 claims to 9 (3/9 errors) and r927's from 3 to 6
  (4/6). The AUC on verified recurrence is **0.491 [0.396, 0.582]**; non-LABEL errors 0.518
  [0.417, 0.619]; material errors 0.449 [0.304, 0.605].
- **The recurrence-0 cells are small** (6–9 claims per run), so any one run's cell is noise. The
  pooled 0–15 grading is the measure.

## 6. The verdict

**Agreement does not predict error enough to act on, so fix 6 is dropped.**
- **The registered bar.** RR ≥ 2 with a lower bound above 1 on r926, replicated on r921 and r927,
  surviving section and length.
- **What r926 shows instead.** RR 0.30 [0.00, 0.70] on the matcher and 0.43 [0.00, 0.97] verified.
  Both replications agree in direction, at every sensitivity setting the plan named. The gold, which
  covers every class, shows AUC 0.49.
- **What would change this.** An error class that is NOT systematic: one a single draw invents and
  the others do not. The ABSENT class is the obvious candidate, but no calibrated metric reads it on
  a draw today (M-ABSENT's TEST recall is 3/32). Once a judge or metric reads ABSENT or OVERREACH on
  a draw at a stated precision, the same three runs re-score at $0. The matcher, the re-check, the
  scripts and every intermediate file are kept in the notes folder for that (BOUNDARY).
- **Not proposed instead.** Agreement-5 units do carry most label echoes (8.5% pooled, against 1–3%
  below). A flag on them would mark 57% of all units, and fix 3a already removes the labels at the
  source.

**HOW VERIFIED.**
- **Scorer.** It reproduces #926's logged totals exactly (§1).
- **Matcher.** Frozen, with the plan, before any label: sha256 and timestamp recorded. It was
  calibrated on another run and hand-checked on a held-out sample. Every agreement-1 unit was
  re-checked blind.
- **Commands.** Every count above was printed by a script run on the stored draws; the scripts are
  named in BOUNDARY. No paid call and no LLM API call was made. The subagents are this session's
  analysis readers, not API calls.

**BOUNDARY.**
- **Draw units.** Every unit of `draw_units` at `fc79a7be`, all sections, both arms: r926 1,910
  units / 60 draws; r921 1,882 / 60; r927 1,840 / 60. Pooled 5,632 units over 180 draws on BURL,
  CNXC, LLY, MCK, ROST and SMPL. Agreement is counted within one page × arm × run, out of 5 draws.
- **Error label.** "With an M-LABEL hit" means ≥ 1 hit on the unit, by `score_units` at `fc79a7be`,
  on the panel's blobs at `bcda7ce3`, with no transcript.
- **Gold.** The 138 claims on the six panel pages, of the 644-claim gold at `bcda7ce3`. Final label =
  the adjudicated record, else the agreed coding (`vinci/evals/gold.py`).
- **Measured** 2026-11-11 on main `e3f715b0`. The gold fixtures, `gold.py` and `units.py` are
  byte-identical to `3d55bc31`, where the scripts ran.
- **Files.** Scripts and outputs are in the notes folder
  `…/side-session-notes/local_7e5fb8ce-…/fix6-agreement-test/`: `matcher.py`, `PREREG.md`,
  `run_match.py`, `score_units.py`, `analyse.py`, `strat.py`, `gold_recur.py`, `gold_analyse.py`,
  `gold_auc.py`, and the calibration, evaluation and re-check samples with their labels.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** No paid call. Three analysis subagents read model output only.
- **Accepted: the test reads one error class on draws.** It reads LABEL through M-LABEL, and the gold
  through an older prompt's draw. A non-systematic class (one draw invents a figure the others do not)
  could still track agreement. **Falsifier:** a calibrated draw-level ABSENT or OVERREACH reader shows
  agreement-1 units at ≥ 2× the agreement-≥3 rate on these runs. Then this record is superseded and
  fix 6 reopens, narrowed to that class.
