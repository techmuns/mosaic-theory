# Build Status — Audit

**Version:** v0.3 · **Date:** 2026-06-17 · **Owner:** Munshot Research
**Scope:** the full document set. Supersedes v0.2 (which predated the filled objective function, the locked US-first mandate, and the Loop 1 build plan).

> **Headline, read first.** Everything produced so far is **design / specification — implementation is uniformly zero.** No code, no ingestion, no running screen, no executed trade. The states below grade *design* completeness only. **The discipline now is to stop designing and start building Loop 1** — writing more specs for the un-validated layers is the exact drift the foundational audit warns against.

> **Shape, for orientation.** `funnel (breadth — automated, parallel) → depth (discriminator — serial, human-gated) → portfolio`, with monitoring feeding back. The **depth half already exists** as your A/B/C source-binding framework + CIQ extraction spec. The **breadth half is the new build.** The **moat** is the parallel-native claim — reasoning across the whole dependency graph and cross-section, which a human can't — of which the **shock-propagation edge** is the clearest instance. That moat is *unproven and the hardest to build*; it is validated only *after* the engine itself is shown to carry information.

---

## Artifact inventory — ten docs now exist (all design)

| Artifact | Version | State |
|---|---|---|
| `AI_NATIVE_FUND_BUILD_BRIEF.md` — 10 parts, phases 0–5, risks, open decisions | v0.1 | design; **most stale** — predates the loops, the validate-forward correction, and the edge reframe; component map still holds |
| `EDGE_THESIS.md` — Phase 0; edges + the parallel-native lens (the moat) | v0.4 | design |
| `OBJECTIVE_FUNCTION.md` — Phase 0 constraints, Goodhart-fenced | v0.2 | design; **values set; return target provisional** |
| `FUNNEL_SCREENS.md` — Phase 1 screen logic (gates, not scores) | v0.2 | design |
| `INGESTION_LAYER.md` — Phase 1 data spine spec | v0.2 | design |
| `FOUNDATIONAL_AUDIT.md` — first-principles audit; validate-forward correction | v0.2 | meta; **A6/A8 premises now resolved** (mandate filled, $1M committed); live questions stand |
| `MINIMAL_LOOP.md` — **Loop 1** validation plan (Edge 2) | v0.1 | plan |
| `GRAPH_LOOP.md` — **Loop 2** validation plan (the moat) | v0.1 | plan |
| `LOOP1_BUILD_PLAN.md` — Claude Code runbook for the Loop 1 build | v0.2 | plan; real-system in paper mode |
| `BUILD_STATUS.md` — this document | v0.3 | meta |
| A/B/C source-binding framework · `ciq_extraction_notes.md` · `data_sources.md` | — | **yours, mature/validated** (depth engine + CIQ parse + verified source map) |

## The reframe that governs everything (from the audit's correction)

You **cannot validate before building** — the engine has no prior runs, so there is nothing to backtest (and an LLM-based discriminator can't be backtested anyway — it has hindsight on known names). Validation **is** building the first real slice and running it forward in paper mode. Therefore the amber layers below are **deliberately deferred** until Loop 1 shows the engine carries information.

## Moving parts (design status + what's next)

| # | Layer | Design state | Disposition |
|---|---|---|---|
| 1 | Universe / tradeability gate | **Specced** (folded into ingestion) | built thin in Loop 1 (US, one cap band) |
| 2 | **Data spine + ingestion** | **Specced** (`INGESTION_LAYER` v0.2) | **thin version = the first build (Loop 1)** |
| 2b | Long-tail filing parser | concept only | **conditional** — only if the moat proves real |
| 3 | Breadth screens | **Specced** (`FUNNEL_SCREENS` v0.2) | **Screen 2 = the one screen in Loop 1** |
| 4 | Verification harness | discriminators specced; mechanism not | **deferred until Loop 1 clears** |
| 5 | Depth integration | minimal version in `MINIMAL_LOOP`; full spec not | minimal built in Loop 1; full spec **deferred** |
| 6 | Portfolio / sizing / risk | principles only | **deferred until Loop 1 clears** |
| 7 | Execution | IBKR named | **deferred until Loop 1 clears** |
| 8 | Monitoring / thesis-break / decay | concept only | **deferred until Loop 1 clears** |
| 9 | Objective function | **Written & filled** (`OBJECTIVE_FUNCTION` v0.2) | **values set; return target provisional, AUM soft-close deferred** |
| 10 | Business / ops / regulatory | not started | **parallel track — start now (longest lead)** |
| — | **Validation loops** | **specced** (`MINIMAL_LOOP`, `GRAPH_LOOP`); **build plan** (`LOOP1_BUILD_PLAN` v0.2) | **Loop 1 = build next; Loop 2 Test 0/1 alongside** |

## Pending design docs — by warrant (most are deferred)

- **Deferred until Loop 1 proves the engine** (do *not* write yet — premature): verification-harness spec (4), full depth-integration spec (5), portfolio/sizing/risk spec (6), execution spec (7), monitoring/decay spec (8).
- **Parallel track — start now** (slow, independent of the loop): the operational Phase-0 half — business / ops / **regulatory** plan (10). *The mandate values are now set; what remains here is operational, not the objective function.*
- **Conditional — only if earned**: proprietary long-tail data spec (2b, only if the moat is real); non-US fundamental parsers (post-loop, if a market earns it).

## Decisions ledger

**Decided / resolved:**
- **Validate forward, not before.** Build the first real slice and run it forward in paper mode; defer the amber layers until it clears. No backtest (no prior runs; LLM hindsight).
- **The moat is the parallel-native edge** — graph/cross-section reasoning a human can't do; **Edge 3 generalised to the shock-propagation primitive** (trigger × channel, two-sided, loser-leg → avoid/kill, not short). Edges 1 & 2 reframed as **value discipline executed at breadth** (parallel *detection*; the *judgment* is where specialists are advantaged).
- **Loop order:** Edge 2 validated first (most measurable); the graph edge is Loop 2.
- **US-first locked** — ex-China for all capital, ex-India additionally for LP capital; single-country cap n/a under a US-first book.
- **Objective function filled (v0.2):** ~$1.2M start ($200K own + $1M LP, 2-yr lock, return of capital after yr2); ~15% absolute floor as the real target, "beat index ≥2×" recorded as a *provisional stretch*; 30% max drawdown; single position 8–12%, sector/theme ~20%; long-biased, little/no leverage, hedges via index/ETF/futures only (no single-name shorts); AUM soft-close deferred at this size.
- **Capital is structured in a HK company, held in USD** — resolves inbound/round-tripping/SEBI-FPI; residual legal items (POEM, FEMA/LRS on the own $200K, India-sourced management activity, SFC Type 9) sit with counsel.
- No CIQ programmatic feed → CIQ is **depth-only**; breadth runs on EDGAR + EOD + (later) IBKR + web.
- Screens are **coarse gates, not scores**; **news fenced** to events/context.
- **Social / UGC / practitioner chatter out of scope** as a systematic layer (capacity-contradiction, adversarial/commoditised corpus, hindsight) — manual depth-stage channel-check exception only.
- Build with Claude Code; **configure-once automation** (no manual repeat deploys).

**Open — flagged where they block:**
- **Regulatory / counsel track** — HK **SFC Type 9** (*blocks running real LP money*; longest calendar lead), plus India **POEM** (HK co managed-from-India → possible Indian tax residency; likely moot at this size, live as it scales), **FEMA/LRS** treatment of the own $200K into a foreign financial-services entity, and India-sourced management activity. The structure is decided; these are the residual items.
- **Return target is provisional** — the "beat index ≥2×" stretch was recorded with pushback (it conflicts with the ~15% floor by regime); **re-set after Loop 1** shows a spread.
- **CIQ data-license scope** — *blocks automated storage* of CIQ-derived data.
- **Point-in-time supplier linkage** — *data dependency for graph Test 1*; confirm obtainable before relying on it.
- **FX-hedge policy.**
- **AUM soft-close** — deferred (not binding at ~$1.2M); revisit as it scales.

## Critical path (what actually moves this forward)

1. **The one build — the next action, not a doc:** **Loop 1's thin slice** — thin ingestion (US resolver + EOD + EDGAR + store) → Screen 2 → decision ledger → scoring harness — built to production quality and run forward in paper mode. See `LOOP1_BUILD_PLAN.md`.
2. **Alongside, cheap and offline:** graph **Test 0** (graph quality vs CIQ) and **Test 1** (does propagation-lag exist) — de-risk the moat in parallel; confirm point-in-time linkage first.
3. **Parallel track — start now:** regulatory / ops / counsel (HK SFC Type 9, POEM, FEMA) — longest lead, doesn't block code, blocks running money.
4. **Deferred:** the amber-layer specs — write only after Loop 1 shows a positive BUY−AVOID spread and sound twin-engagement.
5. **Re-set after Loop 1:** the return target (currently provisional).

> The two founder decisions that gated v0.2 — US-first, and the objective-function values — are now **closed**. What gates progress now is **one build (Loop 1)** and the **regulatory track**.

## Top-line assessment

- **Design is essentially complete for this stage; implementation is zero.** The correct move is to *stop specifying* and build Loop 1.
- **Phase 0's intellectual half is complete** — edge thesis (v0.4), objective function filled (v0.2), US-first locked. The **operational half (regulatory/counsel) and the build remain**; regulatory has the longest lead.
- **The moat (parallel-native graph edge) is the differentiator but is unproven and hardest** — validate the engine (Loop 1) before the moat (Loop 2); never build the graph rig on a plausible story.
- **Progress is gated by one build (Loop 1) and the regulatory track.** Everything else is downstream or deferred.

*Living document — update states as specs convert to built components and as open decisions close.*
