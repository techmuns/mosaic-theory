# Foundational Audit — the whole build, questioned at the premise

**Version:** v0.2 · **Date:** 2026-06-16 · **Owner:** Munshot Research
**Changelog (v0.2):** corrected Part C and A3. The original framing — "validate the engine before building it" — was circular: this system has **no prior runs**, so its alpha cannot be backtested. Validation now = building a minimal forward-running loop that generates a fresh paper track record. (Earlier references to HCG/UMAC/Qantas were unrelated past work mistakenly cited as outputs of this framework — removed.)
**Mandate of this audit:** not error-hunting. Question the *fundamentals* of the six documents against the actual goal — **an AI-native long fund producing gains for LPs that are difficult to replicate.** Audits: `BUILD_BRIEF`, `EDGE_THESIS`, `FUNNEL_SCREENS`, `OBJECTIVE_FUNCTION`, `INGESTION_LAYER`, `BUILD_STATUS`.

> **Headline finding.** The *thinking* has outrun the *validation of the premise.* The epistemic machinery we've built — gates not scores, Goodhart-fences, validate-not-optimize, source-grounding, the fraud detector, catalysts-aren't-edges, UNKNOWN→defer — is genuinely strong and is the real asset. But it is excellent machinery for executing an edge whose **existence-versus-peers, whose alpha, and whose claimed non-replicability remain unproven**, designed ahead of a mandate that would shape it. This is the same pattern that recurred all conversation — drift into *how* while *whether* stays unexamined — now applied to the whole edifice. The fix is not more machine. It is a **minimal, forward-running loop** that produces a real (paper) track record to test whether the approach works — *before* the full apparatus is built. (You can't validate before building: the engine doesn't exist and has no prior runs, so the two are the same act.)

---

## Part A — Foundational challenges (load-bearing premises, stress-tested)

**A1 — "Non-replicable for LPs" rests on the wrong axis.** The thesis derives non-replicability from *capacity*: giants can't fish small/illiquid names, so your seat is unique. True that giants can't come — but it does **not** follow that the niche is uncrowded or the returns non-replicable. These names are the home turf of a large population of **small-cap and EM specialist boutiques** who *can* reach them, have been there for decades, and often hold deep local and management relationships a two-person remote shop lacks. Those specialists are your real competition, not Bridgewater. So non-replicability cannot come from "we're smaller than the giants" — it has to come from **beating the incumbent specialists**, and that case is never made. *This is the deepest hole in the build.*

**A2 — The two core advantages may cancel.** AI-native breadth needs rich, machine-readable data to work — which exists for the **US** (EDGAR), the most picked-over, least-neglected, most-competed segment on earth. Neglect — the actual mispricing source — is deepest in **non-US / EM small caps**, exactly where (we established) there is *no free fundamental feed* and the screens collapse to price-only. So the fund's two pillars point at different geographies and partly negate each other: where AI-breadth works, neglect is shallow; where neglect is deep, AI-breadth can't operate. `FUNNEL_SCREENS` flagged this as operational friction; the *fundamental* reading is that it may gut the core synthesis.

**A3 — The engine doesn't exist yet, so its alpha is currently *unknowable*.** The fund leans on "the depth half mostly exists (your A/B/C source-binding framework)." But **rigor is not alpha** — a process can be beautifully disciplined (source-binding, gates, evidence cards) and still produce zero or negative selection return. And crucially: **this system has no prior runs.** There is no historical set of *its* decisions to mine; nothing shows its verdicts predict returns because it has produced none yet. So the question isn't "did past runs make money" (there are none) — it is the forward question, answerable only one way: **build a minimal version, run it on paper, and measure.** This is the highest-priority empirical unknown, and it cannot be resolved by analysis — only by a live loop. *(See the corrected Part C.)*

**A4 — No beta/alpha decomposition.** A long-biased, concentrated small-cap book earns mostly **market + small-cap beta** — which *is* replicable (a small-cap index, levered). The non-replicable part is the **selection alpha** on top — precisely what A1–A3 cast doubt on. No document separates expected return into beta vs alpha. An LP underwrites alpha; if the engine delivers leveraged small-cap beta dressed as alpha, you're charging 2-and-20 for something cheaper elsewhere. Until the return is decomposed, the LP pitch can't be honest.

**A5 — The edges aren't novel, and may be *disadvantaged* versus their natural holders.** Edge 1 (orphaned quality) and Edge 2 (overshot de-rating) are classic value/contrarian setups — fine, edges needn't be novel. But they're exactly what small-cap value specialists have run for decades, and the *discriminators* we wrote are the hard part they're better placed to win. Especially Edge 2: judging "exaggerated-and-temporary vs secular-and-terminal" often demands deep industry knowledge, channel checks, and management access — a sector specialist has these; a remote AI-augmented generalist does not. We called Edge 2's discriminator "an untested claim about you." Sharper: it may be **structurally weaker** than the incumbents'. (Edge 1's persistence argument is the one that survives — see Part B.)

**A6 — Architecture built ahead of the mandate.** Return target, risk appetite, horizon, and capital are blank (`OBJECTIVE_FUNCTION` §5), yet these are the **shape-determining** inputs: a 15%/patient-family-office machine differs fundamentally from a 30%/redeemable-LP machine — in concentration, liquidity, even which edges fit. We designed the machine before knowing what it's for. The disciplined order is mandate → architecture; we did the reverse, risking that parts are simply wrong once the mandate exists.

**A7 — Possibly over-engineered for the actual cadence.** A concentrated 8–15-name, weeks-to-quarters book initiates maybe a *handful of positions a quarter* — it needs tens of good ideas a year, not an automated firehose. Does that justify the full automated breadth apparatus? Maybe deep *manual* sourcing of a few names serves a concentrated long book better. (Counter, which must be stated rather than assumed: the funnel's value is *serendipity* — surfacing names you'd never have thought to examine — not throughput. If that's the justification, say so; if not, the apparatus may be solving a problem the fund doesn't have.)

**A8 — There is no fund, no LPs, no track record.** "Gains for LPs" presumes LPs. A two-person shop with no track record raising institutional capital is extraordinarily hard — allocators buy track record, infrastructure, pedigree. Realistically the first capital is your own (and friends/family), and "non-replicable LP returns" is a *someday* goal. The documents speak as if the LP vehicle exists. Honest sequence: prove alpha on own capital → build a track record → *then* LPs.

## Part B — What survives scrutiny (the audit cuts both ways)

- **The discipline architecture is genuinely sound and is the moat-in-waiting.** Gates-not-scores, the Goodhart-fenced objective function, validate-never-optimize, source-grounding, the fraud detector ("name the risk you bear or you're the patsy"), catalysts-aren't-edges, UNKNOWN→defer, and the meta-stability governance of the objective function — this is correct, hard-won epistemics that most funds lack. It is the strongest thing built.
- **Edge 1's persistence argument holds.** The constraint on the other side is structural (mandate/benchmark/liquidity) *and* the labor to underwrite long-tail names is a cost others won't pay — it survives the whiteboard test. Of the three edges, this is the one with a defensible "why it persists."
- **The funnel→depth contract is clean.** Recall-first screen → coarse gates → candidate carries its twin-to-rule-out → depth runs the discriminator. The division of labor is right.
- **The cost architecture (post-v0.2 ingestion split) is sound** — free/cheap EOD for breadth, IBKR scoped to execution; near-zero data cost, which suits the two-person economics.

So: **strong machine, unproven premise.** The quality of execution-thinking is real; the foundation under it is assumed.

## Part C — The reprioritization this audit forces: you can't validate before building, so build the *minimal loop* and validate forward

The original version of this section was circular — it said "validate the engine before building it," but **the engine doesn't exist and has no prior runs**, so there is nothing to backtest. Validation and building the first thin version are the *same act*. So the real first move is not analysis; it is the smallest thing that produces evidence:

1. **Build a deliberately minimal end-to-end loop.** Thin ingestion → *one* screen → the depth discriminator on a *few* names → a **recorded paper decision**. This is Phase 2 in the build brief ("one loop end-to-end"). Run it forward long enough to produce verdicts you can score. The evidence is a *fresh paper track record* — never a backtest of runs that never happened.
2. **Measure forward.** Hit-rate and return-vs-benchmark of the paper decisions, plus whether the discriminator actually **separates the edge from its twin in live cases** (does "orphaned" beat "value trap," "overshoot" beat "terminal"?). *(Answers A3 — the only way it can be answered.)*
3. **Answer the peer question now (no runs needed).** Name the specific, repeatable advantage over the *incumbent specialists who can also reach these names* — not the giants who can't. This is a reasoning task you can do today; if the honest answer is "nothing yet," that's the finding, and the strategy narrows or changes. *(Answers A1, A5.)*
4. **Decompose the expected return.** Beta vs small-cap tilt vs selection alpha — reasoned a priori for an honest LP pitch, then confirmed by the loop. *(Answers A4.)*

Build the *minimal loop* before the *full apparatus*. If the loop shows no edge over benchmark and no twin-separation, you've saved months of building a beautiful machine around a hollow core.

## Part D — Remaining documents (pending), with reprioritization

**Elevated to next (the corrected priority):**
- **Minimal-loop plan** — the thin end-to-end slice (Phase 2: thin ingestion → one screen → depth on a few names → recorded paper decisions) **plus** the forward-measurement protocol (hit-rate, return-vs-benchmark, twin-separation). *Not a backtest* — this system has no past runs, so the evidence is generated forward. The audit makes this the most important missing document.

**Phase 1–2 build specs still unwritten:**
- **Verification harness spec** (Part 4) — the bull/bear/judge mechanism + dossier format, built on your existing source-binding discipline (the ~60% that already exists).
- **Depth-stage integration spec** (Part 5) — how a candidate-record hands off to the CIQ / A-B-C framework; discriminator run → evidence card → decision.
- **Portfolio construction / sizing / risk spec** (Part 6) — sizing rules, concentration/exposure limits, the drawdown ladder, hedge policy — and the beta/alpha decomposition.
- **Execution spec** (Part 7) — IBKR order handling, liquidity-aware execution.
- **Monitoring / thesis-break / decay spec** (Part 8) — position monitoring, kill-criteria tracking, decay detection, the recall feedback loop.
- **Proprietary long-tail data spec** (Part 2b) — *only if* the manufactured-data moat is real; currently asserted, never specced.

**Foundation / business (start the long-lead one now, in parallel):**
- **Mandate** — complete `OBJECTIVE_FUNCTION` §5 (capital, return/risk targets, horizon, LP terms) + the operational Phase-0 half. *Shape-determining; arguably should precede the build specs above.*
- **Business / ops / regulatory plan** (Part 10) — HK structure, SFC Type 9, fund vehicle, service providers, capital plan. Longest calendar lead; doesn't block code, blocks running money.

---
*Bottom line: the machine is well-built and the epistemics are right. The premise — that this beats the specialists who can also fish here, that the engine makes money, that the return is non-replicable alpha rather than replicable beta — is unproven, and (since the system has no prior runs) provable only forward. Build the minimal loop (Part C) before the full apparatus (Part D).*
