# Theme forward-validation — the Stage-4 protocol (a-priori, before logging)

> **Status: DRAFT for analyst review (2026-07-01; REVISED same day). A-priori — written BEFORE any
> theme-enabler paper-hold is logged, so its criteria cannot be reverse-engineered from outcomes.**
> **REVISION (2026-07-01):** the primary measure gained a **CO-PRIMARY control** — RATIFIED vs a NAIVE
> BASELINE from the same surfaced set (§3–§4) — because RATIFIED−PASSED alone tests only whether the
> analyst *sorted the tier* (partly guaranteed by competent disclosure-reading), not whether the
> apparatus beats a replicable method (the fund's actual edge-filter, STATE.md §4). A **statistical-power
> caveat** (§4) was added confronting the tiny sample. An amendment, not a redesign — every other measure
> is preserved. The analogue of
> `docs/theme_admissibility.md` (which specified what makes a cluster an admissible THEME before any
> detection code) and of Edge-2's ranking axes (STATE.md §2 — face-validity, never return-tuned). Where
> admissibility specified DETECTION, this specifies MEASUREMENT: once the analyst has ratified a set of
> early enablers, how is their forward performance scored — the real gate.
> **Theme-AGNOSTIC:** the protocol works for ANY human-ratified enabler set; the **AI-datacenter value
> chain** (Stage-3 build-2 — STATE.md §4, THEME/TREND FAMILY) is its FIRST application, not baked into it.
> **Gated on (a) analyst sign-off of this spec AND (b) the analyst's ratified committed-tier picks** —
> the logging harness is the NEXT build, not this doc. **Edge 2 stays the lead horse** (STATE.md §4
> GOVERNOR): this track is PARALLEL, LOW-CADENCE, ADDITIVE — it must not starve overshoot verdict-logging.
> **Forward-only** (STATE.md §1/§7): the spread accrues over calendar time; no backtest, no tuning on
> returns. **Machine assembles evidence; human ratifies; protocol measures** — the dead-signal line
> (STATE.md §3) is never crossed.

---

## 0. The one thing this protocol measures

Stage-3 build-2 surfaced a tier of candidate enablers with legible provenance (450 surfaced; **63 at
the committed-or-better "real activity" tier**). It did **not** decide which are real early bets — that
is the analyst's ratification (a HUMAN pick, never the machine's grade auto-promoted). This protocol
answers the one question the whole theme-edge arc reduces to:

> **Did the analyst's SELECTION of early enablers — ratifying a subset of the machine-surfaced tier —
> out-return the naive "hold the whole surfaced tier"?**

That question has **TWO CO-PRIMARY measures** — because two different things must BOTH be true for the
edge to be real, and each measure isolates one of them:

- **RATIFIED − PASSED-BUT-SURFACED** — did the analyst *sort the surfaced tier* correctly (selection
  WITHIN the tier). The **BUY−AVOID spread transposed to themes** (STATE.md §1, the fund's only
  proof-of-edge).
- **RATIFIED − a NAIVE BASELINE from the same surfaced set** — did the machine's semantic surfacing PLUS
  the human's judgment *beat a replicable method* (equal-weighting the whole committed-or-better tier, or
  a keyword/co-movement screen's picks). This is the fund's own edge-filter: a theme is an edge **ONLY IF
  AI-assembly beats a NAIVE BASELINE** (STATE.md §4/§7 THEME family — momentum-adjacent, replicable
  methods capture much of any theme move).

**Why both, and why the second is not optional:** PASSED is a **QUALITY-SORTED** set — the analyst
declined those names for reading thinner — so a positive RATIFIED−PASSED is **partly guaranteed by
competent disclosure-reading** (table-stakes) and does NOT isolate the semantic-primary early-detection
edge from generic 10-K-reading skill. Only RATIFIED − NAIVE isolates whether the whole apparatus beats a
dumb alternative. **Both positive** = the edge is real (selection works AND the apparatus beats
replicable). **Positive RATIFIED−PASSED with ~0 RATIFIED−NAIVE** = the analyst sorts well but the
apparatus doesn't beat equal-weighting the surfaced names — a **partial-kill the protocol must surface**
(§3–§4). Together they isolate the fund's actual edge — **deep human judgment on finalists, fed by the
funnel** (CLAUDE.md) — from the two things that are NOT the edge: "the theme went up" (market/momentum
beta, replicable — STATE.md §7) and "sub-$10B has more theme-beta" (a holding-bound question, STATE.md §7
holding-universe study), both demoted to SECONDARY context (§3).

A second, subordinate question validates the semantic-primary *mechanism* (§5): **did entering EARLY (at
ratification, before the name co-moves) beat entering LATE (once it is obvious)?** That is the test the
entire Stage-3 arc was built to justify (semantic-from-disclosure is early; co-movement is structurally
late — STATE.md §4 build-1/2).

Everything below serves these measures (two co-primary edge tests + the early-detection mechanism).
Nothing below lets the machine render any of these verdicts.

---

## 1. What is a theme-enabler paper-hold

A **theme-enabler paper-hold** is a committed-tier-or-better name that the **ANALYST has RATIFIED** as a
real early enabler of a named driver. Three things are load-bearing:

- **The machine SURFACES the candidate + the source-bound evidence** (build-2: the grade, the driver-tie,
  the chain layer, the verbatim grade-driving fact + its `source_ref`). It proposes; it does not hold.
- **The human RATIFIES** — reads the provenance, judges the enabler real and early, and logs the pick by
  hand. **The paper-hold is the human's act.** A machine grade of `committed`/`quantified`/`binding` is a
  **CANDIDATE**, never a hold: no code path turns `exposure_basis ≥ committed` into a paper-hold (§6, the
  dead-signal firewall). This mirrors Edge-2 exactly — the BUY/AVOID verdict is the human's, logged by
  hand (STATE.md §1); the machine's ranker orders, it never decides.
- **The passed candidates are logged too** — every name the machine surfaces at the committed-or-better
  tier is either RATIFIED or explicitly PASSED (with a one-line reason). This is not bookkeeping
  pedantry: **the PASSED set is the AVOID leg of the spread** (§3). A protocol that logs only the
  ratified names has no counterfactual and measures nothing — the exact defect that leaves Edge-2's
  spread empty today (STATE.md §2: one unresolved AVOID leg, 0 resolved verdicts). Both legs, from day one.

### The ratification record (the unit of the ledger)

Append-only, one row per surfaced committed-or-better name, JSONL like every other snapshot (STATE.md
§1: committed state stays diff-able). Fields:

| field | meaning |
|---|---|
| `ticker`, `cik` | identity |
| `driver` | the theme (e.g. "AI-datacenter value chain") — the theme-AGNOSTIC key |
| `chain_layer` | the value-chain layer (build-2 provenance: chips/HBM/packaging/thermal/power/optical/operator/cloud) |
| `machine_grade` | `binding` / `quantified` / `committed` — the machine's tier, recorded as the INPUT the human judged, **never the decision** |
| `driver_tie` | `chain-specific` / `indirect` / `not-driver` (the build-2 gate) |
| `grade_fact`, `source_ref` | the verbatim disclosed fact that set the grade + its filing/accession (so the analyst — and any later auditor — verifies the mechanism, not the summary; CLAUDE.md source-bind) |
| `disposition` | **`RATIFIED`** or **`PASSED`** — the human's act (the BUY/AVOID leg) |
| `rationale` | one line, the analyst's economic reasoning (why real + early, or why passed) — the human's judgment, source-bound |
| `ratification_date` | the date the human logged the disposition — **the entry-reference clock** (§2) |
| `first_disclosure_date` | filing date of `grade_fact` — the earliest the exposure was knowable (a §2 comparator) |
| `theme_confirmation_date` | the theme's Stage-2 mega-cap confirmation date, if any (context: was this ratified BEFORE the theme was obvious?) |
| `comovement_onset_date` | **logged FORWARD** — the first date the name enters Component A's theme cluster (§5); empty until it happens (or never) |

`disposition`, `rationale`, and `ratification_date` are the human's. Everything else is machine-assembled
provenance the human judged against. **No `score`, `rank`, `verdict`, or `buy` field** — the schema
cannot conclude (the same guard as `ExposureAssessment`, STATE.md §4 build-1).

---

## 2. The entry reference — when the clock starts

The early-detection thesis is *entering early beats entering late* (STATE.md §7 anticipation). The
protocol must **TEST** that, not assume it — so the choice of when the return-clock starts is itself a
claim to be measured, not a convenience.

**PRIMARY clock = the RATIFICATION DATE.** Reasoning from first principles:

- **You can only act on what you have ratified.** The forward return that validates the EDGE is the
  return available from the moment the human *could have acted* — which is ratification, not any earlier
  unobservable point. Starting the clock before ratification would credit the strategy with a move it
  could not have captured (it had not yet decided) — hindsight, forbidden (STATE.md §1). This is exactly
  Edge-2's rule: the verdict's forward-return clock starts at the verdict date, not at the drawdown that
  preceded it.
- It is the **honest, reproducible** timestamp: the ledger row's own creation date, unfakeable after the
  fact.

**Comparator timestamps, logged but NOT the primary clock** (each exists only to TEST early-beats-late,
never to backdate the edge):

- **`first_disclosure_date`** — the filing date of the grade-driving fact (earliest the exposure was
  public). The gap **first-disclosure → ratification** is the **funnel-latency cost**: how much of the
  move elapsed between the fact being disclosable and the human ratifying it. A funnel that surfaces real
  enablers but slowly loses that early return — measuring it keeps the pipeline honest about its own speed.
- **`comovement_onset_date`** — when the name later becomes obvious (§5). The gap **ratification →
  onset** is the early-detection alpha (the whole-thesis test).
- **`theme_confirmation_date`** — the theme-level Stage-2 mega-cap confirmation. Ratifying an enabler
  BEFORE its theme's confirmation is the strongest early claim; after, a weaker one. Logged as context;
  it is a theme-level stamp, not a per-name entry clock.

So: **the clock starts at ratification** (the only honest, actionable point), and the three comparator
stamps let the protocol *measure* how early that was — rather than assuming it was early.

---

## 3. The counterfactual — the load-bearing design choice

What are the ratified enablers measured AGAINST? The measure must isolate the EDGE — not generic
disclosure-reading skill, not beta. There are **two CO-PRIMARY counterfactuals** (both must be positive
for the edge to be real) and two SECONDARY context comparators. *(This §3 was REVISED 2026-07-01: the
original made RATIFIED−PASSED the sole primary; the co-primary naive-baseline control was added because
RATIFIED−PASSED alone does not isolate the fund's edge — see 3a.)*

### 3a. CO-PRIMARY 1 — vs the surfaced-but-PASSED names: did the human sort the tier?

The machine surfaced the whole committed-or-better tier; the human ratified some (BUY) and passed the
rest (AVOID). **RATIFIED − PASSED is the BUY−AVOID spread for themes** (STATE.md §1). If ratified
out-returns passed, the human's SELECTION added value *within* the surfaced tier.

**But this measure does NOT, alone, isolate the fund's edge — the flaw this revision fixes.** PASSED is a
**QUALITY-SORTED** set: the analyst declined those names *because they read thinner* (weaker
grade-driving fact, softer driver-tie, more deferred terms). So a positive RATIFIED−PASSED spread is
**partly GUARANTEED by competent disclosure-reading** — any diligent reader's kept names tend to
out-read their discarded ones. That is **table-stakes**, not the semantic-primary early-detection edge.
RATIFIED−PASSED answers "did the human sort the tier correctly" — necessary, but not sufficient. Hence
CO-PRIMARY 2.

### 3b. CO-PRIMARY 2 — vs a NAIVE BASELINE from the same surfaced set: did the apparatus beat a replicable method?

The fund's own edge-filter, made concrete: a theme is an edge **ONLY IF AI-assembly beats a NAIVE
BASELINE** (STATE.md §4/§7 — themes are momentum-adjacent; replicable methods capture much of any theme
move). The naive baseline is the decision a DUMB method makes on the SAME surfaced set. Log at least two:

- **(i) EQUAL-WEIGHT-THE-WHOLE-TIER** — hold all committed-or-better names equal-weighted, NO selection
  (~56 for the AI-datacenter build-2 tier). The "machine surfaced, hold everything" baseline. RATIFIED
  beating this shows the tier + the human's selection beats holding the surfaced tier blindly.
- **(ii) A KEYWORD / CO-MOVEMENT SCREEN's picks** — what the replicable method the fund must beat would
  hold: the top names by chain-keyword density (the dumb keyword screen, no semantic discrimination),
  and/or the names already in Component A's co-movement cluster (the "late/obvious" replicable method,
  §5). RATIFIED beating this shows semantic surfacing + human judgment beats what a cheap quant could run.

**RATIFIED − NAIVE** (benchmark-adjusted, §4) is what isolates "the machine's semantic surfacing + the
human's judgment beat a replicable method" — **THE fund's edge claim** (CLAUDE.md §1; STATE.md §4).

### 3c. The logic — both must be positive; the partial-kill the protocol MUST surface

- **RATIFIED − PASSED** isolates *the human sorted the tier* (selection within tier).
- **RATIFIED − NAIVE** isolates *the whole apparatus (semantic surfacing + selection) beat a replicable
  method* (the edge-filter).
- **BOTH positive** = the edge is real: selection adds value within the tier AND the tier+selection beats
  a dumb alternative.
- **Positive RATIFIED−PASSED but ~0 RATIFIED−NAIVE** = the analyst sorts well, yet the whole apparatus
  does not beat equal-weighting the surfaced names — a **PARTIAL-KILL**: the human-in-the-loop has skill,
  but the semantic-primary apparatus adds nothing a keyword/equal-weight method wouldn't. This is the
  single most likely way a plausible-looking edge is really just disclosure-reading riding a replicable
  base — the protocol MUST be able to surface it, not hide it inside a positive RATIFIED−PASSED.

### 3d. SECONDARY context (logged, not the edge verdict)

- **vs a market benchmark (IWM, sub-$10B-matched)** — the did-the-tier-make-money floor; beating IWM only
  proves theme-beta (replicable). If the ratified basket can't beat IWM at all, the funnel surfaced junk.
- **vs the theme's MEGA-CAP leaders** — did the early sub-$10B enablers capture MORE theme move than the
  obvious large-caps (the *"sub-$10B is higher theme-beta"* question, STATE.md §7 holding-universe study,
  hindsight-prone). A holding-CEILING input, **not** the selection edge.

### 3e. Consequence — both co-primaries require their control set LOGGED from row one

RATIFIED−PASSED requires the **AVOID leg**: every surfaced committed-or-better name is ratified-OR-passed
and logged (§1) — no passed set → no counterfactual → the measure is empty (the exact defect leaving
Edge-2's spread empty today, STATE.md §2). RATIFIED−NAIVE requires the **naive baskets frozen at
ratification time** (the whole tier + the keyword/co-movement picks, as of the ratification date) so the
comparison is honest and never re-drawn later. Design both control sets in from row one.

---

## 4. What "captured the enabler return" means

Defined precisely so it cannot drift:

- **Success measure — benchmark-relative forward return, accumulated over the theme horizon.** For each
  logged name, the forward return from its entry reference (§2: EOD close on `ratification_date`, via the
  existing Polygon client) to each rolling horizon, **minus IWM over the same window** (strip market beta
  — "the control says no," STATE.md §7). Benchmark-adjustment is not optional: an un-adjusted "they went
  up" is beta, and the control that should read ~0 on pure beta is the honest number.
- **Horizon — months-to-quarters** (STATE.md §7: theme rotations resolve over months-to-quarters).
  Evaluate at rolling checkpoints (e.g. 1 / 3 / 6 / 12 months) per name; the edge **accumulates forward
  over calendar time** exactly like the BUY−AVOID spread — it is not read off at a single fixed date.
- **The DISCRIMINATION measures — TWO CO-PRIMARY spreads** (both benchmark-adjusted, both accumulated as
  rows season; **both must be positive** for the edge to be real — §3c):
  - **RATIFIED − PASSED** (§3a, selection within the tier): `mean(adj. fwd return | RATIFIED) −
    mean(adj. fwd return | PASSED)`. Positive = the human sorted the tier; ~0 = added nothing over the
    grade; negative = anti-selective (sorted it backwards). *Partly guaranteed by disclosure-reading
    skill — necessary, not sufficient (§3a).*
  - **RATIFIED − NAIVE** (§3b, the apparatus beats a replicable method — the fund's edge-filter):
    `mean(adj. fwd return | RATIFIED) − mean(adj. fwd return | NAIVE)` for EACH naive basket
    (equal-weight-whole-tier; keyword/co-movement picks). Positive = the semantic apparatus + selection
    beat the dumb method; **~0 = they did NOT — the PARTIAL-KILL (§3c)**, which the protocol must surface,
    never bury inside a positive RATIFIED−PASSED.
  Each counts as "large enough to be real, not noise" only against the ≥2-quarter resolved bar (STATE.md
  §4) **AND** the power floor (§4-power below).

"Captured the enabler return" is therefore **not** "the name went up," and **not even** "the ratified set
beat the passed set" alone — it is "ratified beat **both** the passed set **and** a naive baseline, after
the market is stripped, over months-to-quarters, accumulated forward — subject to the power floor below."

### 4-power. Statistical power — confront the tiny sample HONESTLY

The sample is **small by construction**, and the protocol must say so BEFORE the first data point, so
early results are not over-read (the fund's discipline everywhere: don't round thin evidence up to
signal — CLAUDE.md; STATE.md §7 "the control says no"):

- **The numbers.** A committed-or-better tier is ~56 names (AI-datacenter build-2); the analyst ratifies
  perhaps **~10–20**; emergence themes confirm only **a few times a year**. So the spread accrues on a
  **handful of names over quarters**, not thousands of observations.
- **Names within a theme are NOT independent.** They co-move (that is what makes them a theme), so the
  effective sample is far smaller than the name count — closer to **THEMES × QUARTERS** than to names. Ten
  ratified names in one theme-quarter is ≈ ONE independent observation of "did selection work here," not ten.
- **Therefore early results are DIRECTIONAL / ANECDOTAL, NOT statistically significant.** A positive (or
  negative) spread on the first one or two themes is **consistent with noise** and must NOT be read as
  validation OR kill. Small-cap cross-sectional return variance is large; a few names' idiosyncratic moves
  swamp a real selection signal at this n.
- **A pre-registered bar (rough, set NOW to prevent post-hoc over-reading).** Treat the spread as merely
  **suggestive** until it has accumulated on the order of **≥8–12 independent THEME-QUARTERS spanning ≥4–5
  distinct drivers** (so it is not one theme's idiosyncrasy), with the **sign consistent across drivers**
  (not one blowout theme carrying the mean). Below that, report the number and its direction but label it
  explicitly **UNPOWERED**. This is a floor for taking the spread seriously, not a significance test — the
  honest posture is that real confidence needs **many themes over many quarters, likely multiple YEARS** at
  the fund's theme-confirmation cadence. Both co-primary spreads (§4) and the early-detection gap (§5) are
  subject to this same floor.
- **Consequence for cadence.** Because the binding scarcity is theme-quarters, this track's value is
  **cumulative and slow** — another reason it is parallel/low-cadence and must NEVER pull attention from
  Edge-2's faster-seasoning overshoot verdicts (§6 GOVERNOR). It is a long accrual, not a quick read.

---

## 5. The early-detection test (first-class)

This is the one test that validates the WHOLE semantic-primary thesis — that reading the disclosure
surfaces the enabler **before** co-movement does (STATE.md §4 build-1/2: co-movement is structurally
late; the three-diagnostic convergence). It must be a first-class logged quantity, not an afterthought.

- **`comovement_onset_date`, logged FORWARD.** Define co-movement-onset **operationally**: the first date
  the ratified name appears in **Component A's theme cluster** (the co-movement detector, STATE.md §4
  Stage-1, run on a low cadence over the paper-track window). That is the moment the name stops being an
  idiosyncratic early bet and becomes an *obvious* member of the theme — precisely what the late
  co-movement path would have caught. Stamp the date the first time it happens.
- **The measured quantity:** for each ratified enabler, the benchmark-adjusted return from
  **ratification → onset** (the early phase the semantic path claims) versus the return **from onset
  forward** (the late/obvious phase co-movement detection delivers). **If ratification-to-onset captures
  materially more than post-onset, early beat late — the semantic-primary thesis is validated forward.**
- **The null outcome is also logged and meaningful:** a ratified enabler that **never** co-moves (onset
  stays empty) is a real datum, not a gap — the exposure was real by disclosure but the market never
  repriced the name *as a theme member*. Enough of those would say "early enablers surface real business
  but do not reliably get repriced into the theme" — a finding about the thesis, surfaced honestly rather
  than hidden.

This links the two detection paths the arc built: the enabler is surfaced by **semantics** (Stage 3)
before it shows up in **co-movement** (Stage 1), and **the gap between the two is the early-detection
alpha.** Making onset a logged field is what turns that claim into a measured number.

---

## 6. The governor boundary

**Parallel, low-cadence, additive — Edge 2 stays the lead horse** (STATE.md §4 GOVERNOR; §7 discipline):

- **Parallel, not instead.** The binding constraint on proving *anything* is resolved overshoot verdicts
  (STATE.md §4). This track runs WHILE those season; it never takes their place. The 2-person failure
  mode is spreading thin and validating nothing — so this track earns its parallelism only by (a) having
  this validation design specified a-priori (that is this doc) and (b) not diluting the lead loop.
- **Low-cadence by nature.** Theme enablers resolve over months-to-quarters (§4), so ratification and
  logging are low-frequency acts — a handful of dispositions per theme, updated monthly/quarterly. This
  is structurally cheap: it does **not** compete with the daily overshoot-verdict cadence for the scarce
  analyst attention the GOVERNOR protects.
- **Additive, not a new pipeline.** It reuses what exists — build-2's surfaced set (the candidates), the
  Component-A detector (onset, §5), and the Polygon EOD client (returns, §4). The logging harness is a
  thin append-only ledger, the same shape as Edge-2's verdict log — not a new data system.

**The dead-signal firewall (non-negotiable, STATE.md §3):** the protocol **LOGS human-ratified picks and
measures them forward. It NEVER auto-selects, auto-ranks, or turns a grade into a hold.** The division of
labor is explicit and enforced:

> **machine ASSEMBLES the evidence (build-2) → human RATIFIES the pick (§1) → protocol MEASURES it forward (§4–5).**

A machine grade auto-promoted to a paper-hold would be the machine rendering the verdict — the exact
failure this whole project is built to avoid (CLAUDE.md; STATE.md §3 keeps the falsified mechanical
signal dead). The `RATIFIED`/`PASSED` `disposition` is the human-judgment firewall: it is written by a
person, and no code path may set it. The protocol's outputs (§4 spread, §5 early-detection gap) are
measurements of the human's picks, never instructions to make new ones.

---

## 7. Forward-only

The RATIFIED − PASSED spread and the early-detection gap **accrue over calendar time**, like every edge
this fund measures (STATE.md §1 validate-forward; §7). Stated explicitly:

- **No backtest.** No prior run of ratified/passed dispositions exists; you cannot ratify in hindsight
  (§2). The track proves itself only forward, from the first logged disposition onward.
- **No tuning on returns.** Every parameter of this protocol — the entry reference (§2), the primary
  counterfactual (§3), the horizon and "large enough to be real" bar (§4), the onset definition (§5) — is
  fixed **now, by face-validity / first principles, BEFORE any hold is logged.** None is chosen by what
  would have paid; no code path reads forward returns when setting them (the ranker's no-forward-returns
  AST guard is the template, STATE.md §4). Registering the spec a-priori — the whole point of writing this
  before the harness — is what makes that guarantee checkable.

---

## 8. Scope — what this protocol does and does NOT do

**IN scope (this spec):** define how a human-ratified enabler set is scored forward — the entry
reference, the counterfactual, the success + discrimination measures, the early-detection test, and the
ledger that records them.

**OUT of scope (downstream, gated, or forbidden):**
- **Selecting or ranking the enablers** — that is the analyst's ratification (§1); the machine surfaces
  and the human picks. No enabler score, no ordering of ratified names against each other.
- **Sizing, timing, or executing** any position — this is a PAPER measurement track; capital is gated on
  the spread, per STATE.md §4 (and, for real money, the §6-SFC regulatory gate). Nothing here reaches a
  broker.
- **Deciding the theme is real / admissible** — that is `theme_admissibility.md` (detection), upstream.
  This protocol takes the ratified enablers as given and measures them.
- **The calibration / machine-triage layer** (STATE.md §4 build-2 NEXT) — a separate, volume-gated build;
  independent of this measurement spec.
- **Multi-driver expansion** (robotics / GLP-1 / nuclear) — the protocol is theme-agnostic and will
  accept those sets when they exist, but standing up new drivers is a separate build.

---

## 9. Analyst review checklist (sign off before the logging harness is built)

The human reviews this doc for **a-priori sense** (STATE.md §7: criteria set before code, by
face-validity). Confirm or correct each:

1. **Are the TWO CO-PRIMARY edge tests right** — RATIFIED−PASSED (§3a, selection *within* the tier) AND
   RATIFIED−NAIVE (§3b, the apparatus beats a replicable method), with **both required positive** (§3c)?
   In particular: is the diagnosis correct that **RATIFIED−PASSED ALONE is insufficient** because PASSED
   is quality-sorted (a positive spread is partly guaranteed by disclosure-reading skill), and that the
   naive-baseline control is what isolates the fund's edge-filter (STATE.md §4)?
2. **Are the NAIVE BASELINES right (§3b)** — equal-weight-the-whole-tier + a keyword/co-movement screen's
   picks — and is the **PARTIAL-KILL** case (positive RATIFIED−PASSED but ~0 RATIFIED−NAIVE = skill
   riding a replicable base) the right thing for the protocol to surface?
3. **Is the statistical-power posture right (§4-power)** — early results DIRECTIONAL, not significant; the
   pre-registered **UNPOWERED floor** (~≥8–12 theme-quarters spanning ≥4–5 drivers, sign consistent across
   drivers) before the spread is taken seriously? Correct and bearable, or different numbers named now?
4. **Is ratification-date the right entry clock (§2)** — "you can only act on what you ratified," with
   first-disclosure / onset / theme-confirmation as comparators to test early-beats-late?
5. **Is requiring BOTH control sets logged acceptable analyst load (§3e)** — the AVOID leg (every surfaced
   committed+ name ratified-or-passed) AND the naive baskets frozen at ratification — or name a lighter
   sampling that still yields valid counterfactuals?
6. **Is co-movement-onset (§5) the right operationalization of "became obvious"** — "first appears in
   Component A's cluster," and the null (never co-moves) outcome handled right?
7. **Are the horizon and resolved-observation bar (§4) right** — months-to-quarters checkpoints and the
   ≥2-quarter resolved bar (on TOP of the §4-power floor), or different windows named now?
8. **Is the governor boundary (§6) sufficient** to keep this from starving Edge-2 verdict-logging — is
   low-cadence/additive the right shape, and is the dead-signal firewall stated strongly enough?
9. **Anything missing or over-built** — a measure that should be cut, or one this omits.

Until the analyst signs off **and** hands over a ratified committed-tier enabler set, the logging harness
is **not** built. This doc is the contract those two gates are checked against.

---

## 10. What comes next (gated — NOT built here)

- **This is documentation only.** No `vinci/` code; no logging harness; suite untouched.
- **The NEXT build — the forward-validation logging harness** (the append-only ratification ledger of §1
  + the §4/§5 forward-return + onset machinery) — is **gated on (a) this spec's sign-off and (b) the
  analyst's ratified committed-tier picks** (there is nothing to log until the human has ratified a set).
- **Edge 2 stays the lead horse** (STATE.md §4 GOVERNOR). This track is parallel, low-cadence, additive,
  and forward-only. **The forward paper track is the only arbiter — this spec defines the arbiter; it does
  not claim the enablers outperform.**
