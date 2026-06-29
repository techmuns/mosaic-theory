# Theme admissibility — the Phase-0 spec (a-priori, before code)

> **Status: APPROVED WITH CONDITIONS (2026-06-29); §3 amended (§3.0); Phase 1 UNLOCKED & SCOPED.**
> _(Sign-off + the four scoping/build decisions: `theme_admissibility_review.md` FINAL DECISION + STATE.md
> §7. §3.0 records the co-movement-basis amendment; §7 the conditions/resolutions. The remaining
> open piece is forward, not pre-build: the semantic exposure-classifier's discriminability.)_
> This is the admissibility specification for the theme-detection layer, written **before** any
> detection code exists, the analogue of Edge-2's ranking axes (STATE.md §2 ranker: face-validity
> weights, never return-tuned). It defines what makes a detected cluster an **admissible THEME**. It is
> a-priori and interpretable; it is **NOT tuned to known themes** — do not reverse-engineer the criteria
> from "AI capex" or "GLP-1" and call them validated. **Gate status:** the data/method spikes returned
> **GO** (`docs/theme_admissibility_spike.md`, 4 parts); the a-priori review
> (`docs/theme_admissibility_review.md`) produced **three design resolutions, now recorded in §7**
> (which AMEND §2 and add forward-validation requirements). Phase 1 remains gated on **(a) the human's
> FINAL sign-off** (the review doc's decision block) and **(b) two scoping decisions** — text/attention
> in Phase 1 vs deferred, and run-universe (§7.4). Edge 2 stays the lead horse (STATE.md §4 GOVERNOR);
> parallel paper-track scoping, validation-design-first.

---

## 0. The one distinction this whole spec exists to draw

A detected cluster of co-moving names is one of two things, and telling them apart **is** the spec:

- **A THEME** — a basket of names linked by a **single nameable economic driver** ("hyperscaler AI
  capex," "GLP-1 adoption," "a steel-tariff input-cost shock"). Driver-linked, judgment-amenable, the
  fund's edge: a human can reason across the cross-section about whether the driver is real, durable,
  early or late.
- **A MOMENTUM BUCKET** — a basket of names that merely **moved together**. Return-linked,
  replicable, and **already captured by the naive momentum baseline** the theme edge must beat
  (STATE.md §7 THEME/TREND FAMILY: theme bets are momentum-adjacent — an edge ONLY IF AI-assembly
  beats a naive momentum baseline; momentum itself is not the edge — it retired graph-momentum, §3).

The entire admissibility test is: **is this a theme, or is it a momentum bucket wearing a theme's
clothes?** If the machine cannot surface a driver a human can name, the fund has assembled nothing the
baseline didn't already have. That is why criterion 1 below is load-bearing and the other three are
supporting gates.

This mirrors the fund's one line (CLAUDE.md, STATE.md §7 edge filter): **the machine PROPOSES — it
assembles the cluster and the candidate driver(s) the names share; the ANALYST JUDGES** whether the
driver is real and nameable. Detection that *concludes* "this is the AI theme, buy it" has crossed the
line this project exists to avoid (an LLM verdict on a high-stakes call is confident, fluent noise).

---

## 1. The four criteria

### Criterion 1 — NAMEABLE SHARED DRIVER  *(the discriminating gate — load-bearing)*

An admissible theme has a **single articulable economic driver** the analyst can name: one sentence,
in economic terms, that says *why these names move together* — a shared end-market, a shared input
cost, a shared regulatory change, a shared technology-adoption S-curve, a shared customer/supplier
choke-point. "Hyperscaler AI capex." "GLP-1 weight-loss adoption." "Onshoring of leading-edge fab
capacity." Not "they all went up."

- **Machine's job (PROPOSE):** assemble and surface *what the names share* — the common
  supply-chain node, end-market, input, sub-sector, or relationship — as **candidate** driver(s),
  each source-bound to the linkage evidence that suggested it (a 10-K end-market phrase, a shared
  customer edge, a shared input). The machine may name a *candidate*; it never ratifies it.
- **Analyst's job (JUDGE):** decide whether that candidate driver is **real and nameable** — a true
  economic mechanism, not a post-hoc story fit to a price blob. This verdict is the human's, by hand,
  exactly as the BUY/AVOID verdict is (STATE.md §1).
- **Why it discriminates:** a momentum bucket has co-movement but **no driver survives the naming
  test** — the only thing the names share is the return. The moment the honest answer to "name the
  driver" is "they all rallied," the cluster is a momentum bucket and is **inadmissible**, however
  tight its co-movement. This is the criterion the naive baseline cannot pass: a momentum screen
  groups by return and can never name *why*.

A theme **fails** criterion 1 when: no single driver covers the basket (it is two themes, or noise);
the only shared attribute is price action; or the "driver" is a tautology of the return ("the
high-momentum names"). Multi-driver blobs are **split or rejected**, not force-named.

### Criterion 2 — BREADTH  *(necessary-condition gate)*

An admissible theme spans **enough distinct names to be a cross-section, not a pair.** This is the
fund's structural edge — *reason across the cross-section* (CLAUDE.md: breadth a human can't assemble
unaided) — and, under the objective (STATE.md §1, returns→AUM→moat), a **capacity** dimension: a
broader theme is more deployable (more eligible names to size into without slippage).

- **No hardcoded N a-priori.** The rule is **"a basket, not a pair"** — two names sharing a customer
  is a *relationship*, not a theme. The minimum-breadth threshold is set later by face-validity on
  what reads as a cross-section (and, downstream, by capacity math against AUM), **never** by what N
  would have paid. A pre-committed magic number here would be exactly the return-untethered guess the
  fund forbids.
- Breadth is a **gate, not a score**: a 9-name theme is not "better" than a 6-name theme. Themes are
  not ranked against each other (see §2 structure).

### Criterion 3 — COHERENCE  *(necessary-condition gate — necessary, NOT sufficient)*

The names' co-movement must be **attributable to the driver — not to market or broad-sector beta
alone.** This is the **same de-confounding discipline as Edge-2's G2** (STATE.md §2: G2 idiosyncratic
= name return minus the benchmark's; "the control says no," CLAUDE.md). The theme is the **RESIDUAL
shared variance** that remains **after stripping market beta and broad-sector beta** — the variance
the names share *with each other* that they do **not** share with the index or their sector at large.

- A "semis sold off" cluster that is **just SOXX beta** is not a theme — strip the sector and the
  shared residual vanishes. A real theme leaves a shared residual after the sector is removed (e.g.
  the AI-infrastructure subset of semis co-moves *beyond* the semis index).
- **Honest gap, recorded:** Edge-2's G2 as built strips **market beta only** (name vs IWM, 180d
  trailing) — the **SIC peer-cohort / sector leg was deferred and never built** (STATE.md §2 G2
  caveat: "no SIC-cohort code exists anywhere in `vinci/`"). Criterion 3 as specified wants market
  **+ sector** stripped. So the coherence test, done properly, **requires a de-confounding leg the
  codebase does not yet have** — a fact the data-availability spike must weigh, and a dependency
  Phase 1 inherits.
- **NECESSARY BUT NOT SUFFICIENT.** Coherence without a nameable driver is **a momentum bucket** —
  tightly co-moving names with no shared economic cause is the *definition* of the thing the baseline
  already captures. Criterion 3 confirms the names move together for a *reason*; **criterion 1 decides
  whether that reason is nameable.** Coherence alone never admits a theme.

### Criterion 4 — PERSISTENCE  *(necessary-condition gate)*

The shared co-movement must **hold over a months-to-quarters window, not a one-week blip** (STATE.md
§7: theme rotations resolve over **months-to-quarters**). A single week of joint movement is noise or
a one-off event, not a theme.

- Persistence **admits that a theme EXISTS** — it is durable enough to be a standing structure a human
  can study. It does **NOT** judge *where in its life* the theme is.
- **Tension with the anticipation edge, resolved explicitly.** The fund's theme-anticipation
  hypothesis is *get in early* (STATE.md §7), which is in apparent tension with "require persistence."
  The resolution is a **clean division of labor: DETECTION admits persistent themes (this spec); the
  FORK judges lifecycle stage** (early-vs-late) downstream. Detection answers *is this a real theme?*;
  the fork (theme-anticipation get-in-early vs theme-participation get-in-late, STATE.md §7 siblings)
  answers *is it early enough to act, or late and exhausted?* Persistence here is an existence test,
  not a timing call — timing would be the dead mechanical-signal failure (STATE.md §3), and is the
  human's judgment, not detection's output.

---

## 2. Structure — a SCREEN, not a ranker

- **Criteria 2, 3, 4 are necessary-condition GATES: PASS/FAIL admissibility.** A candidate cluster is
  admissible only if it is broad enough AND coheres beyond beta AND persists. Any one failing →
  inadmissible. They are **not** weighted, scored, or traded off against one another.
- **Criterion 1 is the discriminating gate** — the machine proposes the candidate driver; the analyst
  passes or fails the cluster on whether that driver is real and nameable. It is the gate the other
  three feed: a cluster can clear 2–4 and still be a momentum bucket, and criterion 1 is what catches
  it.
- **This is a SCREEN, not a ranker. Themes are NOT ranked against each other.** There is no
  "theme priority score," no composite, no ordering of theme vs theme. Admissibility is binary: a
  cluster either is a theme worth a human's cross-sectional reasoning, or it is not. (Contrast Edge-2's
  *ranker*, which orders *names within* the overshoot queue — there, ordering scarce analyst attention
  is the job; here, the job is to admit or reject a structure, and ranking themes would smuggle in a
  machine judgment about which theme matters, which is the analyst's call.)
- **AMENDED BY ANALYST SIGN-OFF (resolution 1, §7.1) — the layer ALSO surfaces STRENGTH & LIFECYCLE
  SIGNALS, as human-judged inputs.** A *pure* binary admit/reject under-uses the machine: it forces the
  human to hand-assess theme strength and lifecycle, which is machine-automatable from public price data.
  So **admissibility stays binary** (the four-criteria PASS/FAIL above is unchanged), but for each
  admitted theme the layer ALSO assembles and PRESENTS machine-assessed **strength & lifecycle signals**
  — at minimum the price-derivable ones: **momentum / relative-strength**, **breadth** (membership
  expanding or contracting), **crowding / over-extension**. **BOUNDARY (critical):** these are **INPUTS
  THE HUMAN JUDGES, never an auto-rank that becomes the decision** — "rank by momentum and auto-bet the
  top" is the dead-signal / replicable failure (STATE.md §3). The machine assembles the strength
  evidence; the human judges which themes to act on. (Surfacing lifecycle *signals* ≠ judging lifecycle
  *stage* — the latter stays the fork's / human's verdict, §4.) See §7.1 for the full resolution.

```
                 ┌─────────────────────────────────────────────┐
  candidate      │  GATE 2  breadth     (basket, not a pair)    │
  cluster  ──▶   │  GATE 3  coherence   (residual beyond beta)  │  ──▶  all PASS?
  (from          │  GATE 4  persistence (months-to-quarters)    │        │
   linkage)      └─────────────────────────────────────────────┘        ▼
                                                          ┌──────────────────────────────┐
                                                          │ GATE 1  NAMEABLE DRIVER        │
                                                          │  machine PROPOSES candidate(s) │
                                                          │  ANALYST judges real+nameable  │ ──▶ ADMISSIBLE THEME
                                                          └──────────────────────────────┘     (else: momentum
                                                                                                 bucket / reject)
```

---

## 3. THE KEY DESIGN DECISION — the clustering basis  *(AMENDED 2026-06-29 — see §3.0)*

### 3.0 — AMENDMENT: the spikes overturned the original "never price" (supersedes §3.1 below)

**Recorded resolution (Phase-0.6/0.7/0.8 spike evidence + analyst sign-off, 2026-06-29).** The original
a-priori decision below (§3.1, "cluster on economic LINKAGE, NEVER price") is **SUPERSEDED**. The
clustering basis is **residual CO-MOVEMENT** — market + broad-sector + **volatility** factors stripped —
with **Criterion-1 driver-naming as the blob-filter.** Why the change:

- **The linkage-only plan was not buildable** (Part 1 / Phase-0): economic-linkage data at theme-grade
  resolution does not exist in the pipeline — SIC is too coarse ("all software," "all pharma"),
  graph-exposure too sparse, segments per-finalist. **NO-GO on linkage-as-basis.**
- **Co-movement works where linkage couldn't** (Parts 2–4): residual co-movement surfaces real
  cross-taxonomy themes no available linkage data could find — **housing (14 SICs / 5 sectors), quantum
  (3 SICs SIC splits apart).** So §3.1's fear ("price gives only driver-less blobs") was **only partially
  right**: co-movement yields **BOTH** driver-less blobs **AND** genuine driver-nameable cross-taxonomy
  themes that the coarse linkage data was blind to.
- **The blobs are handled in two stages** (Part 4 vol-strip selectivity + Criterion 1): the **vol-strip
  dissolves the speculative-beta blobs** — proven *selective*, it broke the 19-name future-tech blob into
  smaller sub-clusters whose sizes match its real sub-themes (uranium / quantum / eVTOL — inferred from
  the blob's membership) while leaving diffuse low-vol housing intact — and **Criterion-1 driver-naming
  rejects whatever remains driver-less.**

**The DISCIPLINE survives; only the absolute is overturned.** Raw price-clustering **ALONE** — *without*
the vol-strip AND Criterion-1 — would still yield momentum buckets (§3.1's core point holds, and is the
exact failure to avoid). The amended basis is **not** "price-clustering alone": it is price co-movement
**de-confounded (market+sector+vol) and driver-filtered (Criterion-1)**, which is admissible. The "never
touch price" absolute is wrong; the "never let raw return *be* the driver" discipline is right and intact.

### 3.1 — Original a-priori decision *(SUPERSEDED by §3.0; kept verbatim as the origin record)*

**Detection must cluster names by ECONOMIC LINKAGE — shared supply-chain / end-market / input-cost /
sub-sector — NOT by price co-movement.** This is recorded explicitly because it is the decision that
makes or breaks criterion 1, and the easy/wrong default (cluster on returns — it's one correlation
matrix away) is the one to forbid.

- **Why not price.** Clustering on price co-movement produces **driver-less blobs**: it groups names
  *by the very return* that criterion 1 must look past, so by construction it yields momentum buckets
  that **fail criterion 1**. You cannot recover a nameable economic driver from a correlation matrix —
  the matrix has thrown the economics away. Price-clustering would build a momentum strategy and call
  it a theme detector; that is the exact failure mode (STATE.md §7: momentum is replicable and is NOT
  the edge; §3 retired graph-momentum for it).
- **What price IS for.** Price co-movement is **criterion 3's CONFIRMATION** — *given* an
  economically-linked candidate basket, do those names also cohere in the market beyond beta? Price
  enters **after** the economic grouping, to confirm the linkage shows up as shared residual variance.
  It is the **check**, never the **basis**.
- **One-line rule:** group by *why they should move together* (economics), then check *whether they
  do* (price residual). Never the reverse.

**Consequence for Phase 1 (the data requirement).** Clustering on economic linkage requires
**economic-linkage data at theme-grade resolution** — fine enough to separate "GLP-1 names" from "all
of healthcare," "AI-infrastructure semis" from "all semis." Whether the existing pipeline (EDGAR SIC,
graph-exposure, segments) carries linkage at that resolution is **not assumed here** — it is the
question the data-availability spike (STEP 2) answers, and Phase 1 is gated on its go/no-go.

---

## 4. Scope — what admissibility does and does NOT do

**IN scope (this spec):** decide whether a candidate cluster is an admissible theme — a binary
screen on the four criteria, machine-proposes-driver / analyst-judges.

**OUT of scope (downstream, gated, or forbidden):**
- **Ranking themes against each other** — there is no theme score (§2).
- **Judging lifecycle STAGE** (early-vs-late, get-in-early vs get-in-late) — that is **the fork**
  (STATE.md §7 anticipation/participation siblings), downstream of detection. *(Distinct from
  resolution 1 / §7.1: the layer DOES surface machine-assessed lifecycle/strength SIGNALS as inputs —
  surfacing the evidence is IN scope; rendering the early-vs-late VERDICT stays OUT, the fork's/human's
  call.)*
- **Selecting names within an admitted theme, sizing, or timing entry/exit** — later layers; timing
  especially is the human's judgment (a machine timing call is the dead signal, STATE.md §3).
- **Predicting a tradeable return** — detection surfaces a structure for human reasoning; it never
  outputs "this theme will pay." The instant the cluster's *output is the decision*, it has left the
  thesis (STATE.md §7 edge filter).
- **The baseline-beat validation itself** — admissibility says "this is a theme"; whether
  AI-assembled theme selection beats a naive momentum baseline is the **kill criterion** (STATE.md §7),
  measured forward, on resolved verdicts, never backtested. A separate deliverable.

---

## 5. Standing disciplines this spec inherits (non-negotiable)

- **The machine assembles and proposes; the human concludes** (CLAUDE.md). Detection proposes clusters
  + candidate drivers; the analyst renders the "this is a real, nameable theme" verdict.
- **Validate forward, never backtest; never tune on forward returns.** The four criteria and any
  threshold Phase 1 introduces (minimum breadth, coherence cutoff, persistence window) are set by
  **face-validity** — do the admitted clusters look structurally like themes — **never** by what
  grouping would have paid. No code path reads forward returns when setting these (the ranker's
  no-forward-returns AST guard is the template).
- **The control says no** (criterion 3). Trust the de-confounded residual over the persuasive raw
  co-movement; a "theme" that is all sector beta should read ~0 after the control, and that zero is
  the answer.
- **Source-bind the driver evidence** (CLAUDE.md). The candidate driver the machine proposes points to
  the primary linkage evidence (the 10-K phrase, the relationship edge, the shared input) so the
  analyst verifies the mechanism rather than trusting the summary.
- **Fail loud.** A cluster whose linkage data is missing/too-coarse to propose a driver is reported as
  such (inadmissible-for-lack-of-evidence), never force-fit a fabricated driver to clear criterion 1.

---

## 6. Analyst review checklist (sign off before Phase 1 is built)

The human reviews this doc for **a-priori sense** (STATE.md §7 discipline: criteria set before code,
by face-validity). Confirm or correct each:

1. **Is criterion 1 (nameable driver) genuinely the right discriminator** between a fund-edge theme
   and a replicable momentum bucket — and is "the analyst names the driver" the correct human/machine
   split (machine proposes, human judges)?
2. **Is the economic-linkage-not-price clustering decision (§3) correct** — is price-as-confirmation
   (not basis) the right call, and is the "driver-less blob" failure mode real?
3. **Is the screen-not-ranker structure right** — is binary admissibility (no theme score, themes not
   ranked against each other) the right shape, vs. some prioritization?
4. **Is the detection-admits-existence / fork-judges-lifecycle split (criterion 4) the right
   resolution** of the persistence-vs-anticipation tension?
5. **Is "no hardcoded N" for breadth (criterion 2) right**, or does the analyst want a face-valid
   floor named now?
6. **Anything missing** — a fifth criterion, or a criterion that should be cut?

Until the analyst signs off **and** the spike returns go, Phase 1 is not built. This doc is the
contract those gates are checked against. **The walkable version of this checklist is
`docs/theme_admissibility_review.md`** (per-criterion question + real spike evidence + the residual
edges); the spike returned **GO** (`theme_admissibility_spike.md`, 4 parts); and the review's three
design resolutions are recorded in **§7 below**.

---

## 7. Analyst sign-off resolutions (recorded design decisions + forward-validation items)

The a-priori review (`docs/theme_admissibility_review.md`) produced **three resolutions**. They are
**design decisions and FORWARD-VALIDATION items, recorded here as Phase-1 build requirements — NOT
things to re-test in a spike** (the four-spike arc is complete; no further pre-build spike is needed).
The final APPROVE sign-off and the two scoping decisions (§7.4) remain the human's.

### 7.1 — Surface STRENGTH & LIFECYCLE signals, not just a binary admit/reject  *(resolves review #10.1 — the most important change; amends §2)*

A *pure* binary admissibility screen UNDER-USES the machine — it forces the human to hand-assess theme
strength and lifecycle, which is exactly the work that is **machine-automatable from public price data**
(and that institutional thematic platforms, e.g. **BlackRock THRO**, explicitly automate). **Phase-1
requirement:** for each admissible theme, the layer must ALSO **surface machine-assessed strength &
lifecycle signals** — at minimum the price-derivable ones: **momentum / relative-strength**, **breadth**
(is membership expanding or contracting), and **crowding / over-extension**. **BOUNDARY (critical):**
these are **INPUTS THE HUMAN JUDGES, never an auto-rank that becomes the decision.** "Rank themes by
momentum and auto-bet the top" is the dead-signal / replicable failure (STATE.md §3, §7 edge filter).
The machine ASSEMBLES and PRESENTS the strength evidence; the human judges which themes to act on. This
keeps "screen, not ranker" for **admissibility** (still binary PASS/FAIL) while adding a **signal layer**
that is assembled-and-presented, not auto-ranked. (Surfacing lifecycle SIGNALS ≠ judging lifecycle
STAGE — the latter stays the fork's / human's verdict, §4.)

### 7.2 — Emergent-theme validation is FORWARD, by analogy + attention-footprint  *(resolves Residual Edge 2 / review #3)*

Emergent cross-taxonomy themes (quantum-class) have **no prior regime to backtest** — structural, not
fixable by more data, and these are exactly the method's unique value-add over SIC. **Resolution
(institutional standard, consistent with the fund's validate-forward discipline):** their robustness is
established **FORWARD**, by (a) **ANALOGY** — an emergent deep-tech cohort is validated against how
*prior* emergent-tech cohorts behaved in their early phase; and (b) **TEXT / ATTENTION FOOTPRINT** — a
real emerging theme has a persistent, growing **news / filing / transcript signature even with no price
history** (the mechanism BlackRock/THRO and the academic THEME system use). **Recorded:** emergent-theme
regime-robustness is a **FORWARD**-validation question answered by analogy + attention-footprint, **NOT
by backtest**. *(The attention-footprint leg depends on the text/attention scoping question, §7.4.)*

### 7.3 — A separate UNPROMPTED high-vol detection path  *(resolves Residual Edge 1 / review #2)*

The vol-strip is proven selective for low-vol macro themes but may **silently MISS** diffuse
high-vol / event-driven real themes (**GLP-1 at readouts, AI-infra at capex, defense at conflict**). The
resolution is **NOT a hand-picked-theme check** — testing whether the strip preserves themes you
*pre-declared* real is circular and only catches what you already knew to look for. **Phase-1
requirement:** a **separate HIGH-VOL detection path** that surfaces high-vol theme candidates
**UNPROMPTED**, which the analyst then judges. The risk being guarded is **silent false-negatives** (real
high-vol themes the analyst didn't know to look for); only an unprompted path tests that — a hand-picked
check does not. Validated forward.

### 7.4 — CROSS-CUTTING: text/attention analysis + the OPEN scoping question (the human decides)

All three resolutions point at **TEXT / ATTENTION ANALYSIS** as a common complementary tool: high-vol
themes have **news signatures** (7.3), emergent themes have **attention footprints** (7.2), and
lifecycle/strength is partly an **attention signal** (7.1). The institutional evidence is consistent that
serious thematic detection **PAIRS price-co-movement with text-attention**. **OPEN SCOPING QUESTION (for
the human — NOT decided here):** does **Phase 1 include text/attention**, or is **Phase 1 co-movement-only**
(with the price-derivable strength signals of 7.1) and **text/attention deferred to a Phase 1.5**?
**Flag:** text-ingestion is a **NEW data pipeline** (news / transcripts) **not currently in `vinci/`** —
a real build cost, not a tweak. This is one of the **two scoping decisions** (with **run-universe** —
broad-for-discovery vs the overshoot set) that Phase 1 is gated on, alongside the human's final sign-off.
