# Theme admissibility — analyst sign-off review (walkable checklist)

> **What this is.** The human walk-through to **APPROVE / APPROVE-WITH-CONDITIONS / REJECT** the four
> admissibility criteria in `theme_admissibility.md`. Phase 1 (the real detection layer) has been gated
> on two things: (a) the data/method spikes returning go — **done** (`theme_admissibility_spike.md`
> Parts 1–4: SIC NO-GO → co-movement GO → GO CONFIRMED), and (b) **this a-priori sign-off, which only
> the human can give.** The machine does **not** self-approve (CLAUDE.md: the machine proposes; the
> human concludes). This doc supersedes the thin §6 checklist in `theme_admissibility.md` by pairing
> each criterion with a concrete judgeable question **and** the real spike evidence for/against.
>
> **How to walk it:** read each block, answer the *Judge this* question, tick one *Your call* box (and
> write the change/reason if not "approve as-is"). The two **RESIDUAL EDGES** (§B) and the
> **architecture revision** (§A) are the parts most worth your scrutiny — they are what the spikes
> changed or left forward-open. Sign at the end (§E). _Prepared 2026-06-29; analyst signs._

---

## §A — FIRST, the architecture revision the spikes produced (sign this before the criteria)

The spec (`theme_admissibility.md` §3) was written a-priori with a **KEY DESIGN DECISION: cluster on
ECONOMIC LINKAGE (SIC / supply-chain / end-market), NEVER on price; price is criterion-3 confirmation
only.** **The spikes overturned that decision empirically** and you are being asked to sign off on the
**revised** architecture, not the original §3:

- **Why it changed.** Spike Part 1 proved the economic-linkage data the §3 plan needed **does not exist
  at theme-grade resolution** — SIC is too coarse (SIC 7372 lumps 7 unrelated software names; SIC 2834
  is "all pharma," not "GLP-1"), graph-exposure is too sparse/wrong-typed, segments are per-finalist.
  **NO-GO on linkage-as-basis.**
- **What replaced it.** Parts 2–4 tested the basis §3 forbade — **residual co-movement** — and found it
  **viable**: it surfaces real cross-taxonomy themes SIC structurally cannot (quantum: 3 different SICs,
  one driver). So the working architecture is now: **residual co-movement FINDS candidate clusters
  (criterion 3 promoted from "confirmation" to BASIS); criterion-1 driver-naming VALIDATES them
  (rejecting the driver-less blobs co-movement admits).**
- **What did NOT change.** Criterion 1 is still the load-bearing gate; the machine still only proposes;
  the human still judges; "never tune on returns / validate forward" still holds.

**Judge this:** Do you accept the **revision** — residual co-movement as the clustering basis (because
theme-grade linkage data isn't available), with criterion-1 driver-naming carrying the full weight of
ensuring a nameable driver? Or do you want to hold the original §3 (linkage-as-basis), which the spikes
showed is not buildable on current data?

**Your call:** ☐ Accept the co-movement-basis revision  ☐ Hold §3 linkage-basis (blocks Phase 1 until a
finer linkage source exists)  ☐ Other: ________________

---

## §B — THE TWO RESIDUAL EDGES (the parts of the sign-off most likely to bite — do not skip)

These are real, named in the Phase-0.8 analysis, and **forward-open**, not settled. Signing off means
signing off *knowing* these.

### ☐ RESIDUAL EDGE 1 — the vol-strip may MISS real HIGH-VOL themes

The detector strips a **volatility factor** to dissolve the speculative-beta "glue" (Part 4 proved this
is *selective*, not a blunt threshold-raiser: low-vol HOUSING survived the strip 22→18, corr 0.37→0.35;
the fake 19-name spec-blob dissolved into its real parts uranium-6 / quantum-3 / eVTOL-2). **But the
strip discriminates on volatility LEVEL, not on whether the volatility is real-theme or fake-glue.**

- **Proven:** the strip preserves **low-vol macro** real themes (housing, vol-pctile 45) and **tight
  high-vol** themes (quantum, which survived because it is a tight knot).
- **UNPROVEN — the risk quadrant:** a **diffuse HIGH-VOL real theme** — e.g. **GLP-1 at peak trial-
  readout waves, AI-infra at capex-cycle inflections** — has shared movement that IS high-vol, so the
  vol-strip **may dissolve it along with the speculative glue.** This quadrant was not in the test set.
- **Consequence to accept:** the detector **may MISS real high-vol / event-driven themes** (false
  negatives), exactly the kind that spike hardest. This is a **recall** gap, not a false-positive gap.

**Judge this:** Is "the detector may miss real high-vol event-driven themes, and Phase-1 paper-validation
must explicitly watch for this" an acceptable known limitation to launch with?

**Your call:** ☐ Accept as a watched forward-validation item  ☐ Require a fix first (e.g. a separate
high-vol-theme detection path before Phase 1)  ☐ Other: ________________

### ☐ RESIDUAL EDGE 2 — emergent cross-taxonomy themes can only be validated FORWARD

Part 4's regime test proved **mature** themes recur across opposite regimes (housing, gold, shipping,
hotels all re-formed in the −29% 2021-22 drawdown *and* the +39% 2025-26 melt-up → not risk-on
artifacts). **But the method's unique value over SIC is the EMERGENT cross-taxonomy themes** (quantum is
the exemplar — 3 SICs SIC would never join). **Quantum could not be regime-tested at all: it is younger
than the available price history** (IPO'd after the 2021-22 window).

- **Structural, not fixable by more data:** the very themes that justify the method (new, cross-industry,
  pre-prior-regime) have **no prior regime to backtest against.** Their regime-robustness can be
  established **only FORWARD**, never retrospectively — which is also the fund's standing discipline
  (validate forward, never backtest).
- **Consequence to accept:** the headline reliability number (mature themes recur) **does not transfer**
  to the emergent themes that are the point. Those are a forward-validation bet.

**Judge this:** Do you accept that emergent-theme regime-robustness is an open **forward** question — one
paper-validation answers over time — not something this spike (or any backtest) can settle?

**Your call:** ☐ Accept — forward-validation owns it  ☐ Reject — need more assurance first  ☐ Other:
________________

---

## §C — The four criteria (state · judge · evidence)

### ☐ Criterion 1 — NAMEABLE SHARED DRIVER  *(the load-bearing discriminator)*
- **The claim:** an admissible theme has a *single articulable economic driver* the analyst can name
  ("GLP-1 adoption"); a momentum bucket has co-movement but no driver survives the naming test. Machine
  PROPOSES the candidate driver; analyst JUDGES it real.
- **Judge this:** Is "can a human name one economic driver for this basket?" genuinely the right line
  between a fund-edge theme and a replicable momentum bucket — and is machine-proposes / human-judges the
  right split?
- **Evidence FOR:** the method produces baskets where a driver is nameable — **housing** (builders +
  lumber + flooring + furniture, 14 SICs), **quantum** (RGTI/QUBT/QBTS), **uranium**, **hotels+lodging**
  (REITs + operators). The criterion also correctly *rejects*: the 19-name "speculative future-tech"
  blob has **no single nameable driver** → inadmissible, exactly as intended.
- **Evidence AGAINST / honest limit:** criterion 1 is doing **more** work under the revised architecture
  (it is now the *only* thing standing between co-movement and a blob — §A). And see Residual Edge 1: a
  real high-vol theme may never reach criterion 1 because the vol-strip removed it upstream.
- **Your call:** ☐ Approve as-is  ☐ Approve with change: ________________  ☐ Reject because: ____________

### ☐ Criterion 2 — BREADTH  *(necessary-condition gate)*
- **The claim:** "a basket, not a pair" — enough distinct names to be a cross-section. **No hardcoded N**
  a-priori; the floor is set later by face-validity / capacity, never by what N would have paid.
- **Judge this:** Is "no hardcoded N, basket-not-pair" right — or do you want a face-valid minimum named
  now (e.g. ≥5)?
- **Evidence FOR:** real themes came in as genuine cross-sections (housing 22, gold 13, hotels 15,
  shipping 8) — breadth was never the binding constraint. The "basket not pair" rule already bit
  usefully (trucking surfaced as a 2-name pair in the drawdown regime → correctly too thin to be a
  theme).
- **Evidence AGAINST / honest limit:** breadth interacts with the cap-ceiling caveat (§D) — a real
  mega-cap-led theme may appear as only a *few* in-universe satellites, brushing the breadth floor.
- **Your call:** ☐ Approve as-is  ☐ Set a face-valid floor of N = ____  ☐ Reject because: ____________

### ☐ Criterion 3 — COHERENCE  *(necessary, NOT sufficient)*
- **The claim:** co-movement must be the **residual shared variance after stripping market + broad-sector
  beta** (the G2 control discipline) — not index/sector beta. Necessary but not sufficient: coherence
  without a nameable driver is a momentum bucket.
- **Judge this:** Is residual-after-market-+-sector(+vol) the right control — and do you accept that
  coherence is *promoted to the clustering basis* (§A) while remaining insufficient on its own?
- **Evidence FOR:** stripping market + sector + vol was both **discriminating** (dissolved the fake
  speculative glue) and **selective** (preserved diffuse housing); fidelity held vendor-to-vendor
  (quantum 0.82 Polygon ≈ 0.81 Yahoo). The control did its job.
- **Evidence AGAINST / honest limit:** the vol leg carries Residual Edge 1 (may strip real high-vol
  themes). And the original spec flagged that a *sector* de-confounding leg did not exist in `vinci/`;
  the spikes built a throwaway cohort-mean version — Phase 1 must build it properly.
- **Your call:** ☐ Approve as-is  ☐ Approve with change: ________________  ☐ Reject because: ____________

### ☐ Criterion 4 — PERSISTENCE  *(necessary-condition gate)*
- **The claim:** co-movement must hold over **months-to-quarters**, not a one-week blip. Persistence
  admits a theme EXISTS; the **fork** (anticipation get-in-early vs participation get-in-late) judges
  lifecycle — detection does not.
- **Judge this:** Is the detection-admits-existence / fork-judges-lifecycle split the right resolution of
  the persistence-vs-"get-in-early" tension?
- **Evidence FOR:** the spikes used 6–12mo windows and themes were stable structures, not blips; the
  regime test confirmed the mature ones persist across *years* and *regimes*.
- **Evidence AGAINST / honest limit:** persistence + Residual Edge 1 compound — an event-driven theme is
  both high-vol (Edge 1) *and* potentially short-lived, the hardest case for a persistence-requiring,
  vol-stripping detector. Early lifecycle is the fork's job, but the detector must surface the theme at
  all first.
- **Your call:** ☐ Approve as-is  ☐ Approve with change: ________________  ☐ Reject because: ____________

---

## §D — Carried caveats (acknowledge, not necessarily blocking)

### ☐ Cap-ceiling is itself a validation question
The universe is $300M–$10B (the overshoot edge's band), so **mega-cap theme LEADERS are excluded**
(NVDA, LLY out of band). The detector surfaces themes' **small/mid-cap expressions** (housing, uranium,
shipping, quantum-small-caps) and independent small/mid themes — **not** the headline mega-cap-led
AI-infra / GLP-1. For the overshoot fund that operates in this band, that is arguably the right scope —
**but whether small/mid-cap theme detection is *useful* (vs the mega-cap themes the fund can't trade
anyway) is a judgement, not a settled fact.**
- **Your call:** ☐ Acknowledged, scope is right  ☐ Revisit universe for theme detection  ☐ Other: ______

### ☐ The real cross-taxonomy YIELD is a handful, not "56%"
Part 3 reported 56% of clusters "cross ≥2 SICs," but most of those are **sub-sector cohorts** (gold,
banks, shipping) that a sector map would also find; the **genuinely cross-taxonomy DRIVER themes that
justify the method** (housing, hotels+operators, staffing, quantum) are a **handful per run**, alongside
many cohorts and some spurious members (COLM in chemicals, PRGO in housing). Size expectations
accordingly: a few genuine cross-taxonomy themes per run, not dozens.
- **Your call:** ☐ Acknowledged, a-handful-per-run is acceptable yield  ☐ Yield too thin to justify
  Phase 1  ☐ Other: ________________

---

## §E — Structure/scope confirmations + final sign-off

Quick confirmations (each ☐ = "yes, this is right"):
- ☐ **Screen, not a ranker** — admissibility is binary; themes are not scored or ranked against each
  other.
- ☐ **Detection ≠ decision** — the layer surfaces structures + candidate drivers; it never outputs
  "this theme will pay," never selects/sizes/times. The fork + the human own everything downstream.
- ☐ **Machine proposes, human concludes** — the analyst names/ratifies every driver by hand.
- ☐ **Validate forward, never backtest; never tune thresholds on returns** — incl. the breadth floor,
  coherence cutoff, persistence window, and the vol-strip strength.
- ☐ **Anything missing?** A fifth criterion, or one to cut? ________________

### Post-review resolutions recorded (2026-06-29)

The a-priori walk produced **three design resolutions**, now recorded in `theme_admissibility.md` §7
(and §2 is amended) as Phase-1 build requirements + forward-validation items:
- **§B Residual Edge 1 (high-vol recall gap)** → resolved by a **separate UNPROMPTED high-vol detection
  path** (spec §7.3) — not a circular hand-picked check.
- **§B Residual Edge 2 (emergent regime-robustness)** → resolved as a **FORWARD** question via
  **analogy + attention-footprint** (spec §7.2) — not by backtest.
- **§C / review #10.1 (binary screen under-uses the machine)** → resolved by surfacing **strength &
  lifecycle signals** as human-judged inputs (spec §2 amended + §7.1) — never an auto-rank.

All three point at **text/attention analysis**; whether Phase 1 includes it is an **OPEN scoping
question** (spec §7.4), **not decided here**.

**RESOLVED (2026-06-29) — analyst decisions now recorded.** FINAL DECISION below = **APPROVE WITH
CONDITIONS**. The scoping/build decisions (now four) are decided and recorded in `STATE.md` §7:
(1) text/attention **IS** in Phase 1 (not deferred to 1.5); (2) **scoped to EMERGENCE themes**;
(3) **PARTICIPATION fork first**, anticipation deferred; (4) **detect BROAD, hold sub-$10B.**
**Phase 1 is unlocked-and-scoped** (no longer gated).

### FINAL DECISION (analyst — do not let the machine fill this in)

- ☐ APPROVE — *(not selected)*
- ☑ **APPROVE WITH CONDITIONS** — **SELECTED (2026-06-29).** The four criteria + the §A architecture
  revision (residual-co-movement basis, now recorded in spec §3.0) are **approved a-priori.** Conditions
  carried into Phase 1 as forward-validation watch-items + build requirements:
  - **watch (Edge 1):** the vol-strip may miss **high-vol / event-driven** real themes → watch via the
    **unprompted high-vol path** (spec §7.3).
  - **watch (Edge 2):** **emergent** cross-taxonomy themes' regime-robustness is **forward-only**, via
    **analogy + text-footprint** (spec §7.2) — never backtest.
  - **build properly:** the **sector-deconfounding leg** (replace the throwaway cohort-mean);
    multiple/longer **windows**; principled cluster selection (not a single τ).
  - **the three recorded resolutions** (spec §7): strength/lifecycle signals (§7.1), emergent-validation
    (§7.2), unprompted high-vol path (§7.3).
- ☐ REJECT — *(not selected)*

Analyst: **techmuns (operator)**   Date: **2026-06-29**   *(decision recorded into the doc per operator
instruction; the machine transcribes, it does not self-approve)*

> **DECISION RECORDED 2026-06-29: APPROVE WITH CONDITIONS.** Both gates are cleared — the data/method gate
> (the spikes) and the a-priori sign-off — and the four scoping/build decisions are set (`STATE.md` §7),
> so **Phase 1 is UNLOCKED and SCOPED to build.** The load-bearing open piece is now **forward, not
> pre-build:** the semantic exposure-classifier's discriminability (Parts 6–7 — detection/holding/timing
> legs are proven; *selection* is the forward gate). Edge 2 stays the lead horse (STATE.md §4 GOVERNOR)
> regardless.
