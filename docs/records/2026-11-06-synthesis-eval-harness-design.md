---
status: open
date: 2026-11-06
prs: [924]
supersedes:
superseded-by:
---

# The synthesis-prompt evaluation harness (PR 1, $0): a frozen 644-claim gold set, a six-page panel chosen by rule, a byte-identical $0 replay, deterministic fidelity metrics and a pre-registered decision rule — every prompt change is measured against them before it ships

**THE RULING.** Operator, 2026-11-06: **"Build it first"** — an evaluation harness before any more
synthesis-prompt changes or paid rebuilds. The 2026-11-05/06 fidelity diagnosis found 283 of the
644 claims on the 28 committed pages misread a fact (43.9%) and 117 did so materially (18.2%);
#920 proved one cause at n=5 on NFLX; #921 (signed material figures) is merged and fix 3a (label
text) is in flight, and neither was gated on a MEASURED improvement.

**PRE-REGISTRATION.** Everything from here to the RESULTS line was written, committed and pushed
before any metric was scored on the gold set, before any logged or #920 draw was re-scored, and
before any replay was proved against a log. The commit that first carries this file is the
timestamp. The panel below was computed by its rule before this file was written — the rule reads
page attributes only (§2), never a metric or a draw.

**SCOPE.** Measurement only. No paid call in PR 1, no page rewritten, nothing on the decision path
changed; `vinci/evals/` is imported by nothing in `vinci/dossier/`, `vinci/ledger/` or
`vinci/rank/`. No prompt, metric or threshold here is set on forward returns; fidelity to the
page's own facts is the only target.

## 1. The gold set (frozen)

- **What:** 644 synthesis claims from the 28 committed pages (`claims.jsonl`: id, page, text),
  each coded twice, blind, against the frozen `TAXONOMY.md` (OK or one of 11 classes, plus
  `material`, `favours`, `fact`); the 172 claims the two coders disagreed on (verdict or
  materiality) were adjudicated blind.
- **The final label:** the adjudicated record where one exists, else the agreed coding. On the
  frozen copy this reproduces the diagnosis: **283 errors (43.9%), 117 material (18.2%)**; material
  by class LABEL 23, SELECTIVE 22, ABSENT 21, OVERREACH 11, BASIS 10, PATH 10, STALE 9, SIGN 5,
  CONFLICT 5, PERIOD 1. A test pins these counts.
- **Committed** under `tests/fixtures/synthesis_gold/`: `claims.jsonl`, `coder_a.jsonl`,
  `coder_b.jsonl`, `adjudicated.jsonl`, `TAXONOMY.md`, and `MANIFEST.json` (each source file's
  sha256 in the diagnosis's scratch folder, the counts, the split). The claims are synthesis text
  already on committed pages; the coders' `fact` notes are ≤20 words citing JSON paths. No
  transcript text, no local path.
- **The corpus they were graded against** is main `3e97ee7d` plus #918's NFLX and MCK pages. On the
  freeze commit `bcda7ce3` the 28 `dossier.json` files are exactly that corpus: `git diff
  3e97ee7d bcda7ce3 -- data/dossiers` touches only NFLX and MCK, i.e. #918.
- **Provenance, stated because it bounds what agreement with it means.** The coders read flattened
  page facts (the diagnosis's `coderA/<T>.core|.dig|.flat` files). The inputs do not state who
  coded; the layout is that of model agents. If so, the gold is MODEL-labelled, double-blind and
  adjudicated, and a judge's agreement with it (§9) is agreement with that process, not with a
  human analyst. kappa 0.76 between the two coders (as the diagnosis reported it) is the ceiling a
  judge can be expected to reach.
- **DEV / TEST split, fixed now.** The diagnosis's two halves are page-disjoint: **DEV** = the 14
  pages AMZN … NFLX (330 claims), **TEST** = the 14 pages NKE … WLK (314 claims). Metric code may
  be revised against DEV only. It is frozen at a commit before TEST is scored; **TEST precision and
  recall are the headline**, DEV's are reported as in-sample.

## 2. The panel, and how it was chosen

The rule is `vinci/evals/panel.py` (its docstring is the specification); the frozen result, with
every page's attributes and exclusion reason, is `vinci/evals/synthesis_panel.json`.

- **Eligible:** sleeve `quality` or `overshoot`; built under the five-draw gate (`draw_agreement`
  on the page); at least one CIQ transcript in `mosaic-theory-ta/data/manual/ciq/<T>`. 16 of 28.
  Excluded: EPAM, FUBO, IT, MVST, NCNO, VITL, VRRM, WERN (single-draw builds, 2026-08/09); ORKA,
  TECX (no transcript); PARR, WLK (`ultra_short_term`).
- **Strata** (all read from the committed page): sleeve; sector; a material financial-summary row;
  a CIQ forward multiple on the page; the price change over the gap-down detector's own window
  (180 days from `stock_performance`'s last point; rising ≥ +5%, falling ≤ −5%, else flat); the
  committed build's lean tally.
- **Motivated a fix:** the ticker is named in the subject of a commit on main that changed
  `vinci/dossier/synthesis.py` or `vinci/dossier/mechanical.py`, or in the title of a record such a
  commit added — AMZN, FUBO, GOOGL, MVST, NCNO, NFLX, SMPL, TJX, UBER, VRRM — plus **LLY**, the
  case of STATE row 47, which fix 3a (in flight, branch `claude/awesome-kilby-7c25a5`) closes; its
  record's title names no ticker, so the title rule alone would have missed it.
- **Constraints:** 3 quality + 3 overshoot; ≥2 held out and ≥2 motivated; 1–2 pages one draw from a
  modal-lean change; ≥2 with a material row and ≥2 without; ≥2 rising and ≥2 falling windows; a
  page without a forward basis when any eligible page lacks one (none does — vacuous).
- **Objective, lexicographic:** most distinct sectors; then a page one draw from a PROPOSAL change;
  then material balance; then rising/falling balance. **Tie-break:** smallest
  sha256(`"mosaic-theory synthesis-eval panel v1 2026-11-06"` + sorted tickers).
- **Search:** all 8,008 six-page subsets of the 16; 812 satisfy the constraints; 7 tie at the best
  score (5 sectors, a proposal-boundary page, 3/3 material, 2/2 rising-falling); the hash picks:

| page | sleeve | sector | material row | window (180d) | committed tally | motivated | boundary |
|---|---|---|---|---|---|---|---|
| **CNXC** | overshoot | Technology | yes | falling (−8.2%) | mixed 5 | held out | — |
| **LLY** | quality | Health Care | yes | rising (+42.9%) | strongly-bullish 5 | yes (row 47) | proposal: one dissent withholds BUY |
| **MCK** | quality | Industrials | no | rising (+45.3%) | mixed 4 / bullish 1 | held out | — |
| **NKE** | overshoot | Consumer Discretionary | no | falling (−20.1%) | mixed 5 | held out | — |
| **ROST** | quality | Consumer Discretionary | no | flat (+3.8%) | bullish 3 / mixed 2 | held out | modal lean |
| **SMPL** | overshoot | Consumer Staples | yes | flat (+0.2%) | mixed 4 / bearish 1 | yes | — |

- **Held out: CNXC, MCK, NKE, ROST.** From this commit on, a prompt-fix PR may not cite a held-out
  page's claims or draws as the case that motivates it; if one must, the panel is re-drawn by this
  rule with that page counted motivated, and the PR says so.
- **"One draw from a proposal change", corrected.** The brief lists UBER, BRBR, AMZN, BURL and
  ROST. Production proposes only on a UNANIMOUS tally (`verdict.derive_proposal`), so a 3–2 page
  has no proposal and one draw cannot give it one: those five are one draw from a change of the
  page's MODAL lean. The pages one draw from a change of the proposal itself are LLY and TJX
  (5–0: one dissent withholds) and V (4–1: one more agreeing draw proposes). The rule carries both.
- **NFLX is not on the panel.** It is the case #920 and #921 were built on; it is measured as a
  TARGET page in PR 2 (§8), outside the panel.

## 3. The replay harness

`vinci/evals/replay.py` re-derives #920's method from its record (§1–§2, §7 there):

- **Inputs, frozen:** a panel page's `dossier.json` read at `freeze_ref` by git (the blob sha is
  in the panel file and checked); its CIQ transcripts from the `-ta` copy, each file's sha256
  checked against the panel file (and against the page's own `inputs.ciq` record where it has one).
  A changed export refuses the replay — the inputs are never silently today's.
- **The mechanical layer as the synthesis read it:** the committed layer with the two
  post-synthesis attachments undone, read off `assemble.py`: `ev_gap` (recomputed after synthesis
  by `ev_gap_transform`) and `capital_structure.covenant_term_rows` (attached after synthesis) set
  to null. Everything else — the Tier-2 covenant digest, the maturity event, the Tier-B driver
  rows, the material marks — is the committed page.
- **Capture at $0:** `vinci.dossier.synthesis.synthesize` through the production client
  `vinci.graph.llm.AnthropicLlmClient`, with only the innermost SDK object (`client._client`)
  replaced by a recorder that records the request and raises, so every byte is built by production
  code and nothing leaves the machine. All draws of a capture must send one identical request.
- **A given code version:** the harness captures with the code it is imported from; `--code-ref
  <git ref>` instead extracts that ref's `vinci/` package (`git archive`) into a temporary folder
  and runs the capture there in a child process, so a log can be proved against the code that
  wrote it.
- **The proof:** SYSTEM, USER, model and max_tokens equal to the logged ones, by length, full
  sha256 and a 0-line unified diff, as #920 §2 did. The logs that match a committed page: CNXC,
  NKE, ROST, TJX (built on `8d351bb8`, 2026-10-29) and NFLX, MCK (built on `c4c9f432`,
  2026-11-05). GOOGL's and LLY's logs belong to builds the committed pages superseded
  (2026-11-02 and 2026-10-29; the pages are from 2026-11-03); they are proved against the page at
  the commit that build wrote, if git still has it, else reported as not provable.
- **Paid draws, ONLY under a budget guard** (no paid call in PR 1; the guard is shown at $0):
  the guard wraps the SDK object and, before forwarding each request, (1) asserts the request
  EQUALS the one captured at $0 for that page and code; (2) refuses it if spend so far plus the
  WORST CASE of one more draw would cross the cap — the worst case being the whole prompt written
  to cache (1.25 × input price) plus `max_tokens` of output; before the first response of a page
  the prompt size is bounded from its character count at the most conservative chars-per-token
  ratio measured on the logs, after it from the response's own count. After each response it
  checks the served model equals the requested one, prices the call with production's `cost_usd`,
  and appends to a spend ledger kept OUTSIDE the repository (raw draws can quote transcripts; the
  harness refuses an output folder inside the checkout). `BudgetStop` is not an `LlmError`, so
  `synthesize` cannot swallow it: the run stops.
- **What the replay cannot do.** It replays a committed mechanical layer, so a change to the words
  the MECHANICAL layer writes (`mechanical.py` labels — fix 3a is exactly this) does not reach the
  request by replay alone. Such a change is measured through a VARIANT TRANSFORM (#920's V2
  pattern): a function from the committed layer to the layer the candidate code writes, which calls
  the candidate's own code for the fields it changes, plus a $0 check that the transform equals what
  the candidate's builder writes for those fields on a `vinci dossier precheck` build of the same
  page. The hook ships here; each such change ships its own transform. A full "rebuild the
  mechanical layer at $0 and overlay the committed page's LLM-extracted blocks" mode is a separate
  build (it needs the store and EDGAR cache a page was built from — STATE row 48's gate).

## 4. The deterministic metrics

All run at $0 on any synthesis text. The scoring unit of a DRAW is the prose unit, as in #920 §4:
each bull/bear claim, each key unknown, the decisive question and each piece of its evidence, each
twin's `distinguishing_fact`, and `evidence_balance` — `source_ref` and `figures` are never scored.
On the GOLD the unit is the claim as coded (a decisive-question claim is the whole question object
as the coders saw it). Each metric returns, per unit, its hits with the phrase and the fact behind
them.

- **M-LABEL — a code-written label repeated against the page's own facts** (gold class LABEL).
  Five families, each a wording AND the fact on the same page that makes it misleading. The family
  fires on the wording whether or not the page still carries the label, so a fix that removes the
  label is measured by whether the claim goes:
  1. *trailing-only*: "trailing only / no forward basis / cannot distinguish a temporarily depressed
     level…" (the code's `TRAILING_ONLY_NOTE`) on a page with a forward basis (§2's attribute).
  2. *bleed*: "bleed", or "gradual" in a clause about the price path, on a page whose detector found
     no gap-down (the shape the code writes as "gradual bleed — no discrete gap-down detected"). The
     detector measures single-day drops only; gradualness is never measured, so the wording is
     unsupported whatever the window did.
  3. *no adjusted forward*: "no forward/adjusted basis", "ev_ebitda_adjusted_fwd UNKNOWN", "no
     revised guidance (parsed)" on a page with a forward basis or guidance-bridge rows.
  4. *segment undisclosed*: "segment EBITDA/profit not disclosed", "segment_ebitda UNKNOWN" on a page
     stating a segment profit (`concentration.segment_profit` present, or a driver row giving
     segment operating profit or contribution margin).
  5. *P/E percentile blocked*: "percentile cannot be built", "share-basis change / stock split …
     percentile" on a page whose `valuation.own_history` carries a P/E series with a percentile.
- **M-SIGN — a material figure framed against its sign** (gold class SIGN): production's
  `synthesis.material_direction_flags` (#921), called UNCHANGED on a one-unit carrier `Synthesis`
  per unit; a hit is a flag the empty carrier does not produce (the claim-independent "not checked"
  notices are subtracted as a set, never parsed from the text).
- **M-PATH — monotone wording against the page's own series** (gold class PATH). #920's frozen
  PATH regex (`every step/year`, `without interruption`, `never reverse*`, `uninterrupted`,
  `unbroken`, `monoton*`, `year after year`, `straight-line`, `in every year`, `consecutive`, …)
  in a unit naming a series the page's annual table carries (revenue, EBITDA, EBIT/operating
  income, net income, EPS, FCF, a margin). The series is read from the table's STRUCTURED `values`
  (a margin is the ratio of two structured rows; display cells are never parsed), over the span the
  unit names (its FY / LTM tokens) or the whole actual history; estimate columns are excluded. The
  unit fires when that span has a year-on-year step against the claimed direction (rise words vs
  fall words; with neither, against the span's net direction). A unit naming no series the page
  carries is reported as unchecked, never as a pass.
- **M-ABSENT — a figure the page's facts do not state** (gold class ABSENT). Each figure the unit
  writes, found by production's `_claim_figure_ends` (which already skips dates, periods,
  durations and identifiers) and read as written by `_written` (value, half a unit of its last
  digit, unit). It is FOUND when a number the pre-synthesis mechanical layer states
  (production's `_stated_numbers`, `primary_source` included) lies inside the written interval at
  an admissible scale for its unit: % at ×1 or ×100; money at ×1, ×10³, ×10⁶ or ×10⁹; multiples,
  ranks and plain numbers at ×1 (a rank also as a stated percentile's rank; a four-digit plain
  number also as a stated year). Approximate wording ("~", "about", "roughly", "nearly",
  "approximately", "around") widens the interval to ±5%. An absent figure is then looked for in the
  page's transcripts: **transcript-only** if its digits appear there as a number, **nowhere**
  otherwise. Limits, stated: a figure DERIVED from two facts (a sum, a ratio) reads as absent; a
  coincidental match at an admissible scale reads as found.
- **M-ECHO — the prompt's own instruction words in the prose** (no gold class: reported, not
  P/R-measured). Instruction text = SYSTEM + the tool schema's descriptions + USER with its facts
  JSON and transcript block removed. An instruction shingle is a five-word sequence (lowercase
  alphabetic tokens) of the instruction text that appears nowhere in the facts text (the facts
  JSON, `primary_source`, the transcripts). A unit echoes when it contains one; the phrase is
  reported. Measured on the gold pages whose exact request is known (the six logs) and, for the
  others, on the current code's replay of their request (stated as such).
- **M-SIZE — prompt size per section**: characters of SYSTEM, the tool schema, and each USER
  section (facts, primary-source digest, operating drivers, transcripts, material figures, drawdown
  anchor — split on the prompt's own `=== … ===` header lines), with tokens estimated from the
  chars-per-token ratio measured on the logs' own usage (stated as an estimate).
- **Precision and recall on the gold, per metric:** a claim is positive when the metric fires on
  it; gold-positive when its final verdict is the metric's class. Reported per half: TP, FP, FN,
  precision and recall with Wilson 95% intervals, recall on the class's MATERIAL claims, and
  "any-error precision" — the share of fired claims the gold calls any error (a claim carries one
  primary class, so a true misreading can be filed under another).

## 5. The noise floor, and how it is measured at $0

- **The A/A data that exists:** eight logs of five draws each on one identical request (§3) — the
  five-draw build's own replicates — and #920's 20 NFLX draws (control = the NFLX log, plus V1–V3).
- **Per metric:** each logged draw is scored; per page, the per-draw count's range and SD; and the
  **minimum detectable reduction (MDR)**: the smallest uniform reduction δ (flagged units per
  draw, floored at 0) such that the §6 test, with base = the logged draws and candidate = base − δ,
  reaches p ≤ 0.05. That is the effect a change must produce to be seen, given the variance the
  production draws actually show.
- **Wiring check against #920 (pre-registered expectations):** scored with the harness's metrics,
  #920's draws must reproduce its one effect — M-LABEL/bleed, control 5/5 draws vs V2 ≤ 1/5
  (p ≤ 0.05, as #920 found by reading) — and its per-draw M-PATH and M-SIGN calls are compared with
  #920 §9's adjudicated PATH and M1 columns (agreement reported draw by draw). A metric that misses
  #920's effect, or disagrees with its adjudication on more than one draw in five, is reported as
  such before it is trusted.
- **In PR 2** the decision test's own null (exchangeable draws within page) is the noise model, and
  a fresh baseline replicates the logs' variance on the current code.

## 6. The decision rule (pre-registered)

- **Design:** BASE = the code on main; CAND = the PR's code (plus its variant transform, §3); the
  same frozen panel inputs; five sequential, cached draws per page per condition — production's
  `SYNTHESIS_DRAWS`, so each condition costs what a build costs. 30 draws per condition.
- **Per metric, per draw:** the count of prose units it flags. **Test:** the exact stratified
  permutation test (`vinci/evals/stats.py`): within each page the ten draws are exchangeable under
  the null; the statistic is the candidate total over the panel; the null distribution is exact
  (252 relabelings per page, convolved). One-sided p for improvement, `p_lower`; for worsening,
  `p_upper`.
- **A change ships only if ALL hold:**
  1. **its declared TARGET metric improves beyond noise:** `p_lower ≤ 0.05` on the panel (with two
     targets, Holm across them). A change whose target never fires on the panel is measured on a
     TARGET page outside it as well (NFLX for #921), 5 v 5 by the same test, and must not worsen
     the panel;
  2. **no other class worsens beyond noise:** `p_upper > 0.05` for every other deterministic metric
     (M-LABEL, M-SIGN, M-PATH, M-ABSENT) — and for every judged class once a calibrated judge runs
     (§9). No multiplicity correction here: a false alarm blocks a change pending a written
     explanation, which is the safe direction;
  3. **the lean does not shift unexplained:** per page, the lean tally of each condition is
     reported; a change of any page's modal lean, a change of any page's proposal (unanimity), or
     `p ≤ 0.05` either way on the panel count of committed-lean draws must be explained in the PR in
     writing before review — never silently accepted;
  4. **prompt size and instruction echo are reported:** M-SIZE per section, base vs candidate, and
     M-ECHO counts and phrases. A rise in echo is named in the PR with the phrases (V1's "ADDS … to
     pre-tax income" is the precedent).
- **Generalisation:** the target's effect on the held-out pages alone is reported beside the panel
  figure. An effect significant on the panel but opposite in sign on the held-out pages is flagged
  "may not generalise" for the coordinator; n is too small for it to be a test.

## 7. What n can and cannot show

Computed with the exact tests in `vinci/evals/stats.py` (math, not data):

- **One page, 5 v 5 (#920's design, Fisher two-sided):** 5/5 vs 0/5 p 0.008; 5/5 vs 1/5 or 4/5 vs
  0/5 p 0.048; 5/5 vs 2/5 or 3/5 vs 0/5 p 0.167; 4/5 vs 1/5 p 0.206; 2/5 vs 0/5 p 0.444; 1/5 vs
  0/5 p 1.0. A one-page change needs a four-draw swing; a three-of-five swing is noise.
- **The panel, six pages 5 v 5, a 0/1 metric at the same rate on every page (`p_lower`):** at
  base 1/5 everywhere (6 of 30 draws), 0/5 everywhere gives p 0.016; at 2/5 (12 of 30), 1/5
  everywhere gives p 0.089 — not evidence — and 0/5 gives 0.0001; at 3/5 (18 of 30), 2/5
  everywhere gives p 0.108, and the candidate must fall to 10 of 30 (p 0.041) — an EIGHT-draw
  swing; at 4/5 (24 of 30), 3/5 everywhere gives p 0.089 and 2/5 gives 0.003.
- **So:** one draw fewer per page is never evidence on this panel; about a third fewer flagged draws
  across the panel is the smallest effect it sees at a mid base rate. A metric that fires on one
  page only reduces to that page's 5 v 5, whatever the panel's size.
- **What it cannot show:** a rare error's reduction (base ≤ 1 draw per page) is invisible unless it
  goes to zero everywhere; an effect on a sleeve, sector or window state the panel does not hold;
  anything about the hours between conditions (the model id is the same; stationarity is assumed,
  as in #920 — PR 2 runs base and candidate interleaved by page to bound it); and anything about
  forward returns, which it never reads.

## 8. Costs

- **Measured, synthesis, five draws per page** (production `cost_usd` over each written build's
  `assemble_dossier_framing` calls in `data/snapshots/assembly_runs/`, list price $5/$25 per Mtok,
  cache write 1.25×, read 0.1×): CNXC $1.7256 (138,197 prompt tokens), LLY $2.6656 (249,916), MCK
  $2.4341 (182,872), NKE $2.1620 (194,155), ROST $1.9901 (172,459), SMPL $2.4867 (179,677) — **the
  panel at $13.46 per condition** at the cache behaviour those builds had. Worst case per draw
  (every draw writing the whole prompt, 16,384 output tokens): CNXC $1.27, LLY $1.97, MCK $1.55,
  NKE $1.62, ROST $1.49, SMPL $1.53 — **$47.2 per condition** if every draw missed cache.
- **PR 2, proposed, each step separately approvable:**
  1. **Baseline:** the panel on current main — 30 draws, ~$13.5 expected.
  2. **#921 re-check:** the panel on #921's parent `dc5b8787` — 30 draws, ~$13.5 — against (1);
     plus NFLX, the page #921 targets, 5 v 5 at both code versions — 10 draws, ~$5.
  3. **Judge calibration** (§9), if approved: ~$25–30.
  - **Proposed caps:** steps 1–2 under one hard guard cap of **$45** (expected ~$32); step 3 under
    its own cap of **$35**. Nothing is spent until the operator approves a step and its cap.
- **This PR:** $0. No API call of any kind (no token counting either).

## 9. The LLM judge — a proposal, NOT run in PR 1

- **What it does:** applies the same `TAXONOMY.md` to every prose unit of a DRAW — OK or one class,
  `material`, `favours`, `fact` — reading the page's facts, which are cached per page so a page's
  ten draws (two conditions × five) pay one cache write. The draw's text is untrusted data in the
  prompt; the verdicts come back through a forced tool with a fixed schema (one entry per unit id),
  so the parse is deterministic. It is never told which condition a draw came from.
- **Calibrated before it is trusted:** run once on the DEV half's 330 gold claims (its prompt may be
  revised there), frozen, then once on TEST's 314. Reported on TEST: Cohen's kappa against the
  final labels on OK-vs-error, per-class agreement (recall and precision of each class), materiality
  agreement, and kappa against each coder separately. **Trusted only if** TEST kappa OK-vs-error is
  ≥ 0.6 and within 0.15 of the coders' own 0.76, and, for any class it will gate, recall ≥ 0.5 on
  that class's material claims. A class it cannot read stays gated by its deterministic metric only.
- **Known biases, named:** the generator is `claude-opus-4-8`; a judge of the same model may prefer
  its own phrasing (self-preference). The gold coders were very likely models too (§1), so
  calibration cannot fully separate the two. A judge of another model is the mitigation; the repo's
  client forces `tool_choice`, which `claude-sonnet-5-5` and `claude-opus-5-5` reject, so that
  needs a client change and is not proposed for PR 2.
- **Cost estimates** (`claude-opus-4-8` list price, the model the repo's config prices; page facts
  ~90–250K tokens, ~150K typical, from the logged prompts less their transcripts):
  - *Calibration:* one call per page with all its claims (as the coders coded a page): ~$0.94 cache
    write + ~$0.05 output ≈ **$1.0 per page; DEV + TEST ≈ $28**. Judging each claim in its own call
    would be ≈ $73. The Batch API halves list price but makes cache hits unreliable; not assumed.
  - *Per evaluation* (six pages × ten draws): per page one write (~$0.94), nine reads (~$0.075 each)
    and ten draws' prose in (~8K tokens, $0.04 each) and verdicts out (~2K tokens, $0.05 each) ≈
    **$2.5 per page, ≈ $15 per evaluation** — about half again on top of the ~$27 of synthesis draws
    a two-condition evaluation costs.
- **If that is too costly:** the deterministic metrics gate LABEL, SIGN, PATH and ABSENT — 59 of the
  117 material errors (LABEL 23, ABSENT 21, PATH 10, SIGN 5) — at $0 per evaluation; judging ONE
  draw per page per condition (12 draws, ≈ $7) adds a coarse read of SELECTIVE, OVERREACH, BASIS,
  STALE and CONFLICT (the other 57 material errors and PERIOD's 1), enough to see a large shift and
  not a small one; say which in the PR.

## 10. What stays open after PR 1

- PR 2 (paid; §8) — baseline, #921 re-check, judge calibration — each on the operator's approval.
- The mechanical-layer "rebuild" mode (§3), needed so a `mechanical.py` change is measured without
  a hand-written transform; fix 3a is its first user, and until it exists fix 3a ships its own
  transform.
- PATH's consensus-revision form (a cumulative revision written as the current state — CNXC's and
  FUBO's gold cases) is not in M-PATH v1; its recall is reported, not hidden.

**BOUNDARY.** Gold counts: the 644 claims of the 28 pages at `bcda7ce3` (= the graded corpus), one
unit per claim, final label = adjudicated else agreed. Panel: the 28 pages at `bcda7ce3`, the
`-ta` CIQ folders on 2026-11-06, git history of main to `bcda7ce3`. Costs: the latest written build
per page in `data/snapshots/assembly_runs/` at `bcda7ce3`, synthesis phase only, `cost_usd` at
`LLM_PRICE_PER_MTOK` (`claude-opus-4-8` $5/$25). Window changes: `stock_performance` points as
committed, 180 calendar days back from the last point.

---

## RESULTS

*Nothing below this line existed when the pre-registration above was pushed.*

**Order of events (git).** Pre-registration `8c18fb42` (2026-11-06 17:21:42 +05:30) → metric code
revised on DEV only → metric code FROZEN `a677d1a1` (17:39:58) → TEST scored once → the noise
floor, the #920 check and the panel's baseline requests. Every number below is from those runs.

**THE RESULT IN SEVEN LINES.**
- **The replay is exact:** all 8 saved build logs reproduce byte for byte at the code that wrote
  them (SYSTEM, USER, model, max_tokens), $0.
- **M-LABEL generalises** — TEST precision 22/32 (69%), recall 22/27 (81%), material recall 14/17.
- **M-SIGN and M-PATH are narrow** — on TEST they fire on 0 and 3 claims, recall 0/5 and 1/12:
  each catches one form of its class, and TEST's errors are mostly the other forms.
- **M-ABSENT does not generalise** — DEV precision 15/18, recall 15/45; TEST 3/14 and 3/32.
- **So the deterministic metrics gate LABEL; ABSENT, PATH's other forms, SELECTIVE, OVERREACH,
  BASIS, STALE and CONFLICT need the judge** — §9's fallback sentence was too generous, measured.
- **The noise floor:** on the 40 logged draws a uniform 1-unit-per-draw reduction is detectable for
  M-LABEL, M-ABSENT and M-ECHO; M-SIGN and M-PATH almost never fire on the panel pages (0 and 1 of
  25 draws), so a fix aimed at them must be measured on a page where they fire.
- **#920 check: two pre-registered expectations FAIL** (§R5): the bleed family reaches 4/5 → 1/5
  draws (p 0.206), not #920's 5/5 → 1/5; and M-SIGN agrees with #920's M1 reading on 13 of 20.

### R1. The byte-identity proofs ($0; `python -m vinci.evals prove`)

| page | code (build) | page at | SYSTEM chars | USER chars | SYSTEM / USER sha256 (16) | identical |
|---|---|---|---:|---:|---|---|
| NFLX | `c4c9f432` | `bcda7ce3` | 7,364 | 474,921 | `8fcfd615fd0dff95` / `618e478112ec0f1d` | **yes** (= #920 §2) |
| MCK | `c4c9f432` | `bcda7ce3` | 7,395 | 468,215 | `c39f5394e3bc6c9a` / `88710212607580c7` | **yes** |
| CNXC | `8d351bb8` | `bcda7ce3` | 5,270 | 348,558 | `2cb3c22d1150784d` / `93854093723dffd1` | **yes** |
| NKE | `8d351bb8` | `bcda7ce3` | 5,270 | 498,011 | `2cb3c22d1150784d` / `27c193aa27d43e6e` | **yes** |
| ROST | `8d351bb8` | `bcda7ce3` | 5,301 | 443,339 | `b38004f0750d2510` / `5f49eb901b3ad488` | **yes** |
| TJX | `8d351bb8` | `bcda7ce3` | 5,270 | 437,727 | `2cb3c22d1150784d` / `8f65a9df6eb82a55` | **yes** |
| GOOGL | `c3721704^` | `c3721704` | 5,301 | 669,729 | `b38004f0750d2510` / `ca9156b3cb3cebe2` | **yes** |
| LLY | `11cbc939^` | `11cbc939` | 5,301 | 623,008 | `b38004f0750d2510` / `27399f24f6edc822` | **yes** |

- Each: the full sha256 equal, a 0-line unified diff, the model equal, max_tokens equal to every
  logged draw's usage; five draws, one identical request. GOOGL's and LLY's logs are of builds the
  committed pages superseded; their pages are at the artifact commits those builds wrote
  (`c3721704`, `11cbc939`), and the code is each commit's parent.
- **A third post-synthesis attachment, found by the proof.** CNXC first differed on ONE line of
  348,558 characters: a financial-summary row read `"material": false` in the log and `true` on the
  page. At `8d351bb8` `assemble.py` ran `_mark_material` AFTER `synthesize` (lines 1095 → 1119);
  #865 (`a15a2abf`, 2026-10-30) moved it before. §3 named two attachments; there are three for a
  pre-#865 build. `capture_at` now clears the annual table's marks for a ref older than `a15a2abf`
  (`git merge-base --is-ancestor`); the replay at current code reads the committed marks, as
  current assembly does.

### R2. The metrics on the gold — DEV in-sample, TEST held out (the headline)

`python -m vinci.evals gold`. Positive = the metric fires on the claim; gold-positive = the final
verdict is its class. Brackets: Wilson 95%.

| metric | half | fired | TP | FP | FN | precision | recall | material recall | any-error precision |
|---|---|---:|---:|---:|---:|---|---|---|---|
| M-LABEL | DEV | 37 | 26 | 11 | 3 | 70% [54–83] | 90% [74–96] | 6/6 | 32/37 |
| **M-LABEL** | **TEST** | 32 | 22 | 10 | 5 | **69% [51–82]** | **81% [63–92]** | **14/17** | 25/32 |
| M-SIGN | DEV | 2 | 2 | 0 | 2 | 100% [34–100] | 50% [15–85] | 1/2 | 2/2 |
| **M-SIGN** | **TEST** | 0 | 0 | 0 | 5 | — | **0% [0–43]** | 0/3 | — |
| M-PATH | DEV | 3 | 3 | 0 | 4 | 100% [44–100] | 43% [16–75] | 1/4 | 3/3 |
| **M-PATH** | **TEST** | 3 | 1 | 2 | 11 | **33% [6–79]** | **8% [1–35]** | 0/6 | 3/3 |
| M-ABSENT | DEV | 18 | 15 | 3 | 30 | 83% [61–94] | 33% [21–48] | 3/9 | 16/18 |
| **M-ABSENT** | **TEST** | 14 | 3 | 11 | 29 | **21% [8–48]** | **9% [3–24]** | 1/12 | 7/14 |

- **The DEV revisions before the freeze** (each made on a DEV claim, listed so the in-sample
  figures can be discounted): M-ABSENT — the universe drops numeric-only dated series of ≥30 points
  (daily prices, quarterly multiples), admits money at ×1/×10⁶ only, reads figures written inside
  fact strings at face ("$578 billion"), lets a range's first figure borrow the second's scale
  word, and gains the QUOTE family (a quoted phrase of ≥3 words no fact's text carries), with
  possessives never read as quotes; M-LABEL — segment-undisclosed is not misleading on a
  single-segment filer, "gradual" counts only in a decline clause with no rise word, "until/without
  a forward basis" joins trailing-only, "EBITDA" joins no-adjusted-forward, and a sixth family,
  runway-not-derivable (a fix-3a label), was added; M-PATH — a hedge ("almost unbroken") is not a
  monotone claim, and the margin series is matched after "operating/EBIT margin".
- **Why TEST falls (read, not tuned on):**
  - *M-SIGN* is #921's flag — a MATERIAL financial-summary figure framed against its sign. None of
    TEST's five SIGN errors is that form (NKE's peer-gap direction, VRRM's P/E read against its
    non-operating part, SMPL ×2, V ×1); it fires on NFLX's two claims and nothing else in 644, as
    #921 recorded.
  - *M-PATH*: of TEST's 11 misses, 5 are a CUMULATIVE consensus revision written as the current
    state (SMPL, TGT, UBER, WERN, WLK) — the form §10 pre-registered as not in v1 — 2 a
    deceleration read as a trend (V), and 4 other path readings (NKE, TGT, WERN, WLK). The
    monotone-wording form M-PATH reads is the one TEST hit.
  - *M-ABSENT*: TEST's false positives are consensus-history start points and net-debt bridge
    figures. Most of its false negatives carry no figure and no quote — paraphrased management
    statements — which no deterministic check reads.
- **EXPLORATORY, not pre-registered — M-ABSENT with the WHOLE PAGE as its universe** (the coders
  read `dossier.json`; the spec reads the layer the model saw): TEST precision 3/9, recall 3/32;
  DEV 13/15, 13/45. The mismatch explains some TEST false positives, not the recall.

### R3. The noise floor ($0, the 40 logged draws: 8 builds × 5 draws on one identical request)

Units flagged per draw, scored at the page each build read (unmarked before #865):

| metric | units / draw (mean) | mean within-page SD | draws with any | MDR, 8 pages | MDR, the 5 panel pages with a log |
|---|---:|---:|---:|---|---|
| M-LABEL | 3.02 | 0.75 | 40/40 | 1 unit/draw (p < 0.001) | 1 (p < 0.001) |
| M-SIGN | 0.12 | 0.08 | 4/40 (all NFLX) | 2 (p 0.024) | none: 0/25 draws fire |
| M-PATH | 0.17 | 0.24 | 6/40 | 1 (p 0.034) | none: 1/25 draws fire |
| M-ABSENT | 1.62 | 0.94 | 27/40 | 1 (p 0.002) | 1 (p 0.013) |
| M-ECHO | 0.95 | 0.76 | 26/40 | 1 (p < 0.001) | 1 (p 0.001) |

- **MDR** = the smallest uniform reduction (flagged units per draw, floored at 0) the §6 test sees
  at p ≤ 0.05 with the logged draws as base. The "panel pages with a log" are CNXC, LLY (its
  superseded build), MCK, NKE, ROST — SMPL has none.
- **Per page, per draw** (units): M-LABEL CNXC 1,1,2,1,2 · NKE 5,4,4,4,5 · ROST 2,1,1,4,2 ·
  TJX 3,3,2,3,4 · NFLX 4,4,6,5,4 · MCK 3,3,4,3,4 · GOOGL 3,4,3,3,6 · LLY 1,1,1,3,2.
- **Leans in the logs:** ROST 3 bullish / 2 mixed and MCK 4/1, GOOGL 4/1 — the committed tallies.
- **Chars per prompt token**, SYSTEM + USER over draw 1's prompt tokens: 2.541 (LLY) to 2.601 (MCK,
  ROST) across the 8. The guard bounds a prompt at 2.0 chars per token before its first response —
  over-estimating tokens by ~27% — and at the response's own count after it.

### R4. M-ECHO and M-SIZE

- **Echoes found in the logged draws** (5-word instruction shingles absent from the facts): "a
  confidence-gated input, not …" on all 8 pages; "the cause named at the follow" (NFLX, MCK — the
  anchor ASK #920 §14 suspected); "a genuine counter-point, outweighed by the …" (TJX, LLY — rule
  7); "a risk, not a neutral gap" (MCK — the opacity rule); "… x net leverage leaving reinvestment"
  (NFLX — rule 13's old LLY example, which V3 replaced). Some shingles are digest templates once the
  numbers drop out ("10-Q states $M due $M"); the phrase is always printed so a reader can tell.
- **The panel's baseline requests at main's synthesis code** (in-process capture; the frozen
  inputs, blobs and transcript sha256s checked), characters:

| page | SYSTEM | tool | facts | primary source | drivers | transcripts | material | anchor | total | est. tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CNXC | 7,364 | 8,488 | 266,787 | 5,362 | 16,336 | 60,095 | 1,146 | — | 365,578 | ~142K |
| LLY | 7,395 | 8,659 | 452,630 | 1,475 | 53,062 | 123,471 | 1,145 | — | 647,837 | ~252K |
| MCK | 7,395 | 8,659 | 338,147 | 1,398 | 15,202 | 110,887 | — | 2,581 | 484,269 | ~188K |
| NKE | 7,364 | 8,488 | 351,264 | 1,364 | 34,458 | 110,948 | — | — | 513,886 | ~200K |
| ROST | 7,395 | 8,659 | 312,639 | 1,274 | 16,351 | 113,098 | — | — | 459,416 | ~179K |
| SMPL | 7,364 | 8,488 | 319,322 | 6,116 | 20,788 | 111,505 | 1,134 | 3,239 | 477,956 | ~186K |

  MCK's USER sha256 equals its log's (`88710212…`): it carries no material row, so #921 did not
  change its request.

### R5. The wiring check against #920 (pre-registered expectations, scored as written)

#920's 20 NFLX draws (control + V1–V3, local), scored by the harness at NFLX's page:

| check | expectation | result |
|---|---|---|
| M-LABEL bleed, control vs V2 | 5/5 vs ≤1/5, p ≤ 0.05 | **4/5 vs 1/5, p 0.206 — FAILS**; units 9 → 1 |
| bleed per draw vs #920's M2a | ≤1 in 5 disagree | 19/20 agree (misses C5's "gradual multiple de-rate") |
| M-PATH per draw vs #920's PATH | ≤1 in 5 disagree | 18/20 agree (V1-4, V2-4: harness yes, #920 a borderline no) |
| M-SIGN per draw vs #920's M1 | ≤1 in 5 disagree | **13/20 — FAILS**: 7 draws the harness flags, #920 did not |

- **Why M-SIGN differs:** #920's M1 rule removed the verbatim plural label ("…Restruct. Charges")
  before reading cost words; production's flag, by #921's review round 2, counts calling the figure
  by a label whose word contradicts its sign as the framing. The two measure different things; the
  harness carries production's.
- **Why the bleed check fails at draw level:** "gradual" in C5 sits in a clause the frozen rule
  reads as not a decline. The unit count (9 → 1) carries the effect; the draw count does not reach
  #920's.

### R6. What this changes, stated for the coordinator (a proposal — the pre-registered rule is NOT edited)

1. **Targets.** Only M-LABEL is fit to be a change's TARGET metric. A change aimed at ABSENT, PATH's
   revision form or any judged class has no valid deterministic target until the judge is
   calibrated; a change aimed at #921's material-direction form is measured on NFLX (where it fires
   2/5 draws), not the panel.
2. **The no-worsening gates (§6.2) stay as pre-registered**, read as PROXIES: M-ABSENT counts
   figures and quotes the facts do not state (TEST precision 21% against ABSENT errors); a
   worsening blocks pending a written explanation, which is the safe direction.
3. **§9's fallback sentence is superseded by R2:** without the judge, a change is gated on LABEL
   and on these proxies only.
4. **PR 2's caps hold** (§8). The guard's pre-response bound makes its worst case per draw $1.55
   (CNXC) to $2.43 (LLY); with the steps 1–2 cap at $45 against ~$32 expected, the headroom (~$13)
   exceeds any one draw's worst case.

### R7. Main against a branch — the first comparison the harness runs ($0 steps shown)

Asked for by the coordinating session after the first results: fix 3a (the label fix) waits on this
harness, so a two-version comparison must be the first thing it can run. `vinci/evals/compare.py`:

- **`python -m vinci.evals compare --base <ref> --cand <ref> [--transform NAME]`** ($0) captures
  every panel page at both refs (`capture_at`, frozen inputs) and REFUSES when no page's request
  differs. **`run-compare … --cap USD --out-dir DIR --paid`** draws them page by page, BASE then
  CAND, five each, under one guard and cap, sending the $0-captured request itself through
  production's `AnthropicLlmClient.extract` (`replay.run_request`) — so a branch without the
  harness is drawn by this one. **`score --out-dir DIR --target M-LABEL`** ($0) applies §6.
- **Real runs, 2026-11-06:**
  - `--base origin/main --cand HEAD` (this branch changes no synthesis code): IDENTICAL on all six
    pages → **REFUSED**, as designed.
  - `--cand claude/awesome-kilby-7c25a5` (fix 3a at `818c1cc7`), no transform: IDENTICAL on all six
    → **REFUSED** — its changes are to `mechanical.py`'s words, which a replay of the committed
    layer cannot see.
  - The same with `--transform relabel_drawdown_shape` (`variants.py`, which re-reads the no-gap-down
    shape from the ref's OWN `mechanical._CURRENT_WORDS`, so it is the identity at main): **differs
    on LLY, MCK, NKE, ROST and SMPL** — one USER line each (a 5-line `-n0` diff), +25 characters, the
    drawdown shape only; SYSTEM equal; **CNXC unchanged** (its window has gap-downs).
- **What that does and does not cover:** fix 3a rewrites five labels; the transform re-derives ONE
  (the drawdown shape — #920's V2, the one with evidence). The trailing EV/EBITDA note, the survival
  read, the peer-gap question and the catalyst print row need their own transforms (or the
  rebuilt-layer mode, §10) before a paid comparison measures them; a comparison run now measures
  fix 3a's drawdown wording alone, and its PR must say so.
- **Tests** (`tests/test_evals_compare.py`, $0): an unreached comparison is refused; the transform
  is the identity at main and, with the code's words changed, changes exactly the one escaped JSON
  span; a gap-down window is untouched; the scorer, on draws built from NFLX's COMMITTED synthesis
  text, ships a CAND whose "bleed" wording is gone (M-LABEL down on every draw, lean unchanged) and
  blocks one that adds a quote no fact carries (M-ABSENT worsens).
- **The gold copy:** the coordinating session named a durable copy of the gold set; its 8 source
  files are byte-equal to the frozen ones and its `final.py` gives 283/644 and 117/644
  (`MANIFEST.json`, `durable_copy`).

### R8. Review round 2 (the coordinator's, on `58e97056`): what changed, and what it changes

The panel, held-out set and paid path above are SUPERSEDED where this section says so; every
earlier number stands as measured.

1. **The cap was per run; it is now per approval.** Each `run-compare` built its ledger in its own
   out-dir, and a used out-dir is refused, so every run started at $0 (three $3-capped runs spent
   $4.90 under the reviewer's mock). Now ONE ledger per operator approval: `budget-open` writes
   the approved cap and the operator's words as its first line, and every paid command needs
   `--budget-ledger`, reads that cap (`--cap` may only lower it) and appends to the same file —
   a resume included. **Retries are metered:** the SDK's own `max_retries=2` sent attempts the
   guard never saw (seven HTTP attempts behind five ledger rows); the guarded client now runs at
   `max_retries=0`, and a failed attempt is a recorded, unpriced, failed draw.
2. **`score` is bound to a registration written before any draw** (`register`): base and
   candidate refs, transforms, pages, draws per condition, target metric(s) (Holm when more than
   one, as §6.1 says), the rule, the scorer's fingerprint and the change's held-out pages, hashed.
   `run-compare` draws exactly it and records its sha256 in the budget ledger. `score` takes no
   target: it refuses draws on other pages or in other counts, a run drawn under another
   registration, and a scorer whose files differ, and appends every score to `score_log.jsonl`.
3. **The held-out rule, applied as written, holds out NOTHING.** The motivated set now reads the
   subjects AND bodies of the prompt commits and the full record of the fix in flight (fix 3a's,
   `4449189d`, committed eleven minutes before this pre-registration). Bodies alone name 28 of
   28 pages and fix 3a's record names 27, so **no page of this corpus is held out from the
   diagnosis-era fixes**, and the v1 constraint (≥2 held out, ≥2 motivated) admits no panel. It is
   dropped, stated in the panel file, and holding out becomes **per change**: the panel pages the
   change's own commits and records do not name, computed at registration. The v1 tie-break salt
   was a written string, and variants of it reached all seven tied panels; the salt is now the
   freeze commit's full sha, a value nobody chose.

   | | panel | feasible / tied | held out |
   |---|---|---|---|
   | v1 (`8c18fb42`) | CNXC, LLY, MCK, NKE, ROST, SMPL | 812 / 7 | CNXC, MCK, NKE, ROST |
   | **v2 (this round)** | **BURL, CNXC, LLY, MCK, ROST, SMPL** | 906 / 7 | none from the corpus; per change |

   NKE leaves and BURL (overshoot, Consumer Discretionary, a falling window, a 3–2 modal
   boundary) joins; strata coverage is unchanged (5 sectors, a proposal-boundary page, 3/3
   material, 2/2 rising-falling). The coordinator's own re-run, which kept the held-out constraint
   with only MCK, NKE and ROST made motivated, gave BRBR, CNXC, LLY, MCK, NFLX, TGT; under the rule
   as written that reading is not available. The DEV/TEST re-split the review asked for is moot:
   it applied only if CNXC or MCK stayed held out, and nothing is. **But four of v2's six pages
   (BURL, CNXC, LLY, MCK) are DEV pages that shaped the metrics**, so the metrics read their draws
   in-sample (item 10 below).
4. **The gold reads its pages at the freeze**, `bcda7ce3`, by git — never the living tree, where a
   one-byte rebuild silently skipped 8 of 13 per-claim pins and every M-SIGN and M-PATH pin.
   `gold` prints which living pages have moved since; the score does not move with them.
5. **Five mutants survived round 1's 59 tests**: the paid guard comparing SYSTEM only, or refusing
   only when SYSTEM and USER both differ; `compare` judging identity on USER only; an M-PATH or
   M-SIGN worsening never blocking; a proposal change alone never blocking. Each is now pinned,
   and each mutant fails its pin, as do six more on this round's guards (retries back on, a cap
   above the approval, the child keeping its key, the child's network open, an unchecked scorer,
   draws on unregistered pages). The earlier "7 guards mutation-checked" counted round 0's seven
   only; it was never a claim about every guard.
6. **The $0 capture child holds no key and no network:** `child_env` strips every Anthropic
   credential and the child disables socket connects at its entry point, so a candidate whose
   code built its own client inside `synthesize` cannot spend during `compare`.
7. **`capture --out` refuses a path inside the repository** before it captures (it had written a
   whole request, transcripts included, into `tests/fixtures/` under the reviewer's run).
8. **The scorer's definitions are pinned:** `TRAILING_ONLY_NOTE`, `material_direction_flags`,
   `SYNTHESIS_TOOL`, `split_lean`/`derive_proposal` come from the checkout running `score`; the
   registration records a sha256 over those files and the scorer's own, and `score` refuses
   another.
9. **What byte identity covers:** SYSTEM, USER, model and max_tokens against the build logs. The
   logs hold no tools, tool_choice or cache_control; those are compared only between a $0 capture
   and its paid request (the guard), never against a log.
10. **What each metric can gate, plainly:**
    - **M-LABEL** — the only target. TEST precision 22/32 and recall 22/27 overall; on v1's TEST
      pages 4/11 and 4/4; on v2's TEST pages (ROST, SMPL) 3/6 and 3/3; on v2's DEV pages 9/10 and
      9/10, in-sample. Its false positives are mostly claims the gold files under another error.
    - **M-SIGN** — one narrow form: a MATERIAL financial-summary figure, from an identified
      statement, cited by its value, framed only against its sign. TEST recall 0/5 is by
      construction: none of TEST's SIGN errors is that form. It gates #921's form and nothing else.
    - **M-PATH** — monotone wording over an annual series; not the cumulative-revision form.
    - **M-ABSENT** — a no-worsening proxy (TEST precision 3/14); never a target.

- **CI and local resolve different `anthropic` SDKs:** `pyproject`'s unpinned `anthropic>=0.112` gives 2.6.0 (on `httpx2`) on CI and 0.112.0 (on `httpx` 0.28.1) locally; #924's gate failed once on that (a test-only fix, `9bcdded1`, passing on both), and whether to pin is the operator's call.

**BOUNDARY (results).** R8's panel: the same 28 frozen rows at `bcda7ce3` with `motivated` recomputed (subjects + bodies of the prompt commits to `bcda7ce3`, the fix-3a record at `4449189d`). Proofs: the 8 logs in the session-notes `llm-logs/` folder (copied
2026-11-06), at the codes and page commits in R1. Gold P/R: 644 claims at `bcda7ce3`'s pages,
metric code `a677d1a1`, DEV = 330 claims / 14 pages, TEST = 314 / 14. Noise floor: 40 draws, unit =
prose units of `units.draw_units`, counted as distinct units with ≥1 hit per draw. #920: its 20
local draws, NFLX page at `bcda7ce3` (= #918's). Sizes: characters of the captured request at main's
synthesis code; tokens estimated at 2.57 chars per token (the logs' mean). No API call was made.
