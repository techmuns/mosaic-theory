# Minimal Loop — Validation Plan (Phase 2)

**Version:** v0.1 · **Status:** plan, not yet built · **Owner:** Munshot Research · **For:** Claude Code (build) + PM (run)
**Upstream:** `FOUNDATIONAL_AUDIT.md` v0.2 (Part C). This is the elevated next step — and the **last spec before code.** Everything after this is *build the slice and run it*, not more design.

> **What this is.** Not an MVP, a **falsification experiment.** Its only job is to produce honest evidence on the audit's open unknowns — does the depth engine generate alpha (A3), does the discriminator separate edge from twin, is there alpha after beta (A4) — *before* the full apparatus (harness, portfolio, execution, monitoring) is built. It is deliberately cheap: free EOD + free EDGAR + the existing depth framework + paper trades. Time is the only real cost.

---

## First principles — what this falsifies, and why it must run forward

**The unknowns it tests:** (A3) the engine's decisions don't beat a benchmark; (mechanism) the discriminator doesn't actually separate "orphaned" from "value trap" or "overshoot" from "terminal" in live cases; (A4) any return is just beta, not selection.

**Why forward, not a backtest — this is non-negotiable.** The discriminator is partly LLM-driven, and an LLM *already knows* what happened after any historical date for well-known names. So any "historical" test is contaminated by hindsight — the model will score the name knowing it recovered or collapsed. You cannot fence that out for names with post-cutoff memory. **Forward paper trading is the only clean method.** (A pseudo-historical test on genuinely obscure names is tempting but still leaks; do not rely on it.)

**Two timescales of evidence — don't confuse them:**
- **Fast (weeks):** does the pipeline run, is the data reliable, do the screens surface plausible names, and — auditable immediately — does the discriminator's *reasoning* genuinely engage the twin with sourced evidence? This is process validation; available almost at once.
- **Slow (quarters → years):** does it actually *make money* and separate edge from twin in realized returns? This is alpha validation, and it is **irreducibly slow** — a verdict can't be scored until its thesis horizon passes.

## The hard truth, up front — sample size

A concentrated, weeks-to-quarters, low-turnover book initiates a *handful of positions a quarter*. A held book therefore yields ~10–30 decisions a year — **statistically tiny.** A year of paper P&L on a few held names proves nothing on its own. Confront this honestly: the loop gives **directional + process evidence and starts the track-record clock** — it does *not* deliver statistical proof of alpha for years.

**The move that buys sample: measure the discriminator as a *classifier*, not the book's P&L.** You don't have to hold a name to score the *verdict*. Run the discriminator on **every** Screen-2 survivor throughput allows (5–10/week → 60–120 a quarter), recording **BUY** and **AVOID-as-twin** verdicts alike, then measure the forward return of all BUY-verdicts versus all AVOID-verdicts. This decouples *decision quality* (measurable across many verdicts) from *portfolio construction* (a few positions) — and the **BUY−AVOID spread** is benchmark-free and uses the whole sample. It is the cleanest test of whether the discriminator carries information at all.

---

## Part 1 — The slice (deliberately minimal)

- **Universe: US only, one cap band.** US because EDGAR gives free programmatic fundamentals, so *every gate evaluates* (non-US would collapse the screen to price-only — useless for validating the discriminator's fundamental judgment). A few hundred names is enough.
- **Thin ingestion** (a subset of `INGESTION_LAYER`): EOD prices+volume (Stooq) · EDGAR (XBRL fundamentals + 8-K full-text) · a simple US entity resolver (CIK↔ticker — far easier than the global case) · a local store with the `(value, as_of, source, coverage)` envelope. **Not** built for the loop: IBKR client, news client, options/IV, non-US — none are needed for a US paper test.
- **One screen: Screen 2 (overshot de-rating).** Chosen deliberately: its twin (terminal vs temporary) **resolves fastest** — a de-rated name bounces or keeps bleeding within months, scoreable inside the loop's life; it is **event-driven**, so candidate flow is highest (more verdicts = more sample); and its gates are clean price/EDGAR signals. Screens 1 and 3 have slow-resolving twins (neglect ending, "stands alone") — wrong for a first validation.
- **The depth discriminator: your existing A/B/C source-binding framework, unchanged.** Run it (manual CIQ pull + the A/B/C process) on the week's Screen-2 survivors. Throughput is capped by the manual stage (~5–10/week) — fine, and exactly why the classifier framing matters.
- **A decision ledger.** For every name the discriminator judges: timestamp, verdict (BUY / AVOID-terminal), the twin call, entry price, thesis, kill-criteria, horizon, and confidence. **Log AVOIDs too** — they are half the experiment.

## Part 2 — The protocol (run + measure)

**Cadence:** weekly screen run → discriminator on survivors → log verdicts. Mark-to-market monthly. First directional read at ~1 quarter; meaningful read at ~4 quarters.

**Outcome metrics (slow — at thesis horizon + interim):**
1. **BUY−AVOID forward-return spread** — the primary metric. Positive and persistent ⇒ the discriminator carries information. Benchmark-free; uses every verdict.
2. **Hit-rate** — % of BUYs beating benchmark; % of AVOIDs lagging it.
3. **Return vs a US small-cap index** — the BUY book's excess return, gross then net of estimated costs.
4. **Beta/alpha split** — regress the BUY book on market + size factors; is there residual alpha or is it all beta (A4)? *Report with wide error bars — tiny n.*
5. **Twin-realisation audit** (Screen-2-specific) — did AVOID-as-terminal names keep falling, and BUY-as-overshoot names bounce? Directly tests the central judgment.

**Process metrics (fast — weeks):** pipeline operability · data-record reliability (validated against known names) · screen yield + candidate plausibility · **reasoning audit** (did the discriminator actually engage the twin with sourced evidence, or rationalise?) · verdict consistency (signal, not noise).

## Part 3 — Pre-registered go / kill criteria (set firmly *before* running)

Fix these before seeing any results — otherwise you'll rationalise post-hoc (the Goodhart-fence discipline applied to the experiment itself).
- **Continue if:** the BUY−AVOID spread is clearly positive over ≥2 quarters of *resolved* verdicts, **and** the reasoning audit shows genuine twin-engagement, **and** the process is operable.
- **Kill / rethink if:** the spread is ≈0 or negative (the discriminator adds no information), **or** all return is explained by beta (no selection skill), **or** the loop can't be operated reliably.
- **Humility clause:** with tiny n these are *directional gates, not significance tests.* You are seeking the **absence of a clear negative + a plausible positive + sound sourced reasoning, sustained** — not a p-value.

## Part 4 — What runs alongside (the loop does *not* answer these)

- **The peer question (A1/A5):** write the specific, repeatable advantage over the *specialists who can also reach these names*. This is a reasoning task to do in parallel — though the loop can inform it (if one sub-type's hit-rate is strong, that's a candidate advantage). Until answered, the non-replicability claim is unproven regardless of the loop.
- **Beta exposure, a priori (A4):** state the market/size beta you are taking *before* measuring residual alpha, so the LP story is honest from the start.

## Part 5 — Honest limitations (read before trusting any result)

- **Paper is optimistic.** Perfect fills, no slippage, no liquidity impact (a real small-cap entry moves the price), no behavioural pressure of real money. Real results will be *worse* — discount accordingly.
- **Latency is irreducible.** Verdicts resolve only at horizon; no statistical confidence for ~years. This is directional + process evidence, not proof.
- **Tiny sample.** No significance near-term; the classifier framing mitigates but does not cure it.
- **Survivorship** in the universe seed (per `INGESTION_LAYER`) — snapshot the universe as you go.
- **Contamination is why this runs forward** — restated, because the temptation to "just backtest it" will recur and must be refused.

---

*Cost ≈ zero; the cost is patience. This is the gate before the amber layers (harness, portfolio, execution, monitoring) — build none of them until the loop shows a positive BUY−AVOID spread and sound twin-engagement. If it shows neither, you've learned the cheapest possible way that the engine doesn't yet have an edge. Next action is no longer a spec — it's building this thin slice in Claude Code and starting the clock.*
