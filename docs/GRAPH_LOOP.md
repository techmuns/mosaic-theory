# Graph Loop — Validation Plan (Loop 2)

**Version:** v0.1 · **Status:** plan, not yet built · **Owner:** Munshot Research · **For:** Claude Code (build) + PM (run)
**Companion to** `MINIMAL_LOOP.md` (Loop 1). **Sequenced after it** for the forward part; the cheap tests below can run *alongside* Loop 1.

> **What this validates.** The **moat** — the parallel-native claim that we reason across the dependency graph better than a market that prices the obvious name first and traces the consequences slowly (the shock-propagation primitive, `EDGE_THESIS` v0.4, class A). Loop 1 asks whether the engine carries *any* information; Loop 2 asks whether the *distinctive* edge is real and capturable. It is the hardest thing to validate in the project, and the plan is built around that fact.

---

## First principles — two different things must be falsified (don't conflate them)

A shock re-rates the obvious names. The edge is the not-yet-priced second-order name. Whether that edge exists splits into two independent questions:

1. **Does the lag exist?** (Phenomenon — a market-structure fact.) Does the market actually fail to price graph-propagation promptly, or do event-driven funds and algos arbitrage it away within hours? This is true-or-false *independent of your ability to capture it.*
2. **Can the system capture it?** (Capability.) Can your graph + discriminator identify the right second-order names *ex-ante*, given that the graph is incomplete and entity-resolution is noisy?

These fail differently: the lag can be real but uncapturable (your graph misses the links that matter), or illusory (no lag regardless of how good your graph is). A plan that tests only the held P&L conflates them and learns nothing. **And a third object is implicated:** the dependency graph is a *new, unvalidated artifact* — Loop 2 is validating the discriminator *and* the graph at once, which confounds unless the graph is tested separately first.

## The hard truth — why this is harder than Loop 1

Loop 1's problems (tiny sample, forward latency, LLM hindsight) all carry over, and Loop 2 adds:
- **Rare triggers → sample starvation.** De-ratings happen daily; *shocks* of the relevant kind (sanctions, export bans, capacity exits, major-customer capex cuts, fuel/fertilizer/rare-earth disruptions) are a handful a year. You cannot accumulate 100 shock verdicts in a quarter. The forward capture test therefore takes **years**, not quarters.
- **Thin candidate set per shock.** Even when one hits, the names you'd act on are few. Shock × candidates = a very thin stream.
- **Maximal hindsight contamination.** Shocks are *highly memorable* news — the LLM knows exactly which stocks moved after the rare-earth ban. So the capture test is **forward-only, no exceptions** — backtesting the *judgment* on past shocks is pure leakage.
- **Confounding.** A "failure" could mean the lag isn't real *or* your graph missed the links *or* the discriminator is weak. The test order below exists to disentangle these.

## The three tests — ordered cheap-kill-first

Each can stop the edge before you pay for the next. The first two are cheap and need no live shocks; the third is slow and rare-trigger-limited.

### Test 0 — Graph quality (fast · now · no shocks needed · the gate)
Validate the dependency graph as an artifact, independent of any shock. On a sample of US names, extract edges and measure against ground truth:
- **Precision** — of extracted edges, how many are real (check against the actual 10-K text). Hallucinated edges (class-D fakes in the structure) must be near-zero.
- **Recall** — of *CIQ-known* relationships, how many you captured (CIQ Customers & Suppliers as a **partial** ground truth — a lower bound, since CIQ is itself incomplete).
- **Entity-resolution accuracy** — are edges wired to the right companies? (The ingestion-layer #1 risk, multiplied: one mis-linked node poisons every path through it.)
**Kill if** precision is low (the graph asserts false connections), recall is so low the graph can't represent the relationships that matter, or entity-resolution is unreliable. *If the graph is garbage, the edge is uncapturable regardless of whether the lag exists — stop here, cheaply.* Start **1-hop only** (direct suppliers/customers of the obviously-affected names); multi-hop amplifies incompleteness and resolution error exponentially.

### Test 1 — Phenomenon / does the lag exist (history · contamination-free *if done right* · fast-ish · a gate)
Does propagation-lag exist as a market regularity? This can use **history** — because it measures *realized price paths*, not LLM judgment, so it isn't hindsight-contaminated **provided the connected set is defined from point-in-time structured linkage, not the LLM's hindsight reading.** Method: for a set of past shocks, take the connected names from a **pre-shock** CIQ supplier snapshot, then measure their cumulative abnormal return in the window *after* the obvious names had already moved.
- Lag exists → the connected set keeps moving after the obvious names; **no lag** → they moved together or didn't move → **kill** (nothing to harvest).
- **Honest data caveat:** this requires *point-in-time* linkage (relationships as they stood before each shock). If only *current* CIQ links are available, the test is compromised by look-ahead/survivorship and gives only a weak read — **confirm whether point-in-time linkage is obtainable before relying on Test 1.**
- Sample-limited regardless (few past shocks) → directional, not statistical.

### Test 2 — Capture / can we flag them ex-ante (forward only · slow · rare-trigger · the real test)
Only meaningful once Test 0 (graph decent) and Test 1 (lag exists) clear. When a shock hits **live**, run the graph + discriminator *in the window before second-order names re-rate* and record paper verdicts. Two nested signals:
- **Connected vs control** — do the graph-flagged second-order names beat (a) a matched *unconnected* control (same sector/size, no graph link to the shock) and (b) still have upside vs the *already-moved obvious* names? This is the propagation-capture alpha.
- **BUY vs AVOID within the connected set** — the discriminator's **structural-vs-transitory** call (`EDGE_THESIS` v0.4): do "structural beneficiary" verdicts beat "transitory spike" verdicts? This tests the new discriminator condition.
Tiny N, accumulating over years → directional and process evidence, never near-term proof.

## The thin build (deliberately minimal — extends Loop 1)

Add to Loop 1's slice (EOD + EDGAR + US resolver + store + discriminator):
- **Graph builder** — EDGAR full-text search for who-names-whom (customer/supplier/partner) + a cheap LLM extracting named dependencies from 10-Ks/transcripts. **1-hop**, US-only, every edge **entity-resolved** to the internal key and stored with **provenance (the filing line)** and direction.
- **Graph-quality harness** — Test 0, run against CIQ + filing text.
- **Shock-trigger detector** — the fenced news layer detects a qualifying trigger and classifies the affected material/sector.
- **Propagation traversal** — given the shock, walk 1-hop to surface connected second-order names (consumers with the material in COGS, substitute producers, advantaged integrated names).
- **Discriminator** — the existing framework + the structural-vs-transitory test, run on the surfaced names → paper verdict (BUY-structural / AVOID-transitory), logged in the Loop 1 ledger.
**Not built here:** multi-hop graph, non-US, real-time, portfolio/execution.

## Pre-registered kill criteria (set before running)
- **Test 0:** kill if graph precision / recall / entity-accuracy below threshold.
- **Test 1:** kill if no measurable propagation-lag in the historical study.
- **Test 2:** kill if flagged connected names don't beat the unconnected control and the already-moved set over the propagation window.
- **Continue only if all three clear** — graph decent **and** lag exists **and** you can flag ex-ante. Humility clause: tiny N throughout; directional gates, not significance; Test 2 confidence takes years.

## Sequencing relative to Loop 1
- **Test 0 and Test 1 run *alongside* Loop 1** — they're cheap, offline, and need no live forward loop, so they de-risk the graph edge in parallel without waiting.
- **Test 2 runs *after* Loop 1 proves the engine carries information** — because (a) it reuses Loop 1's ingestion + discriminator + ledger, (b) if the discriminator carries no information, surfacing second-order names is pointless, and (c) the graph build is the hardest, so defer the forward capture infrastructure until the cheaper loop and the cheap tests clear. **Do not build the live capture rig on the strength of a plausible moat.**

## Honest limitations (Loop 2-specific, beyond Loop 1's)
- **Rare triggers** → Test 2 takes years; broadening the trigger taxonomy raises N but each trigger is weaker/noisier.
- **Graph incompleteness is structural** — filings disclose only material, named links; the second/third-order links you most want are often the undisclosed ones. There is a **recall ceiling** no amount of engineering removes: some real propagation paths are simply invisible to you.
- **Confound** — Test 0 isolates the graph; Test 2 still mixes graph-recall with discriminator-skill.
- **Contamination** — forward-only for Test 2 is mandatory; Test 1 is clean only with point-in-time linkage (data permitting).
- **A2** — US-only; non-US propagation is out of reach on free data, and non-US is where neglect is deepest.
- **Paper optimism, worse here** — capturing a shock means acting *fast*; a paper test ignores the real timing, slippage, and liquidity friction of buying into a moving second-order name.

---
*This validates the moat — but it is the hardest and slowest validation in the project. The point of the ordering is that Test 0 and Test 1 are cheap and can kill the edge early; only build the forward capture rig (Test 2) after Loop 1 and Test 1 clear. The moat is the destination; you reach it by disproving it cheaply at every cheaper stage first.*
