# Funnel Screens — Phase 1 (Top of Funnel)

**Version:** v0.2 · **Status:** working draft · **Owner:** Munshot Research
**Upstream:** `EDGE_THESIS.md` v0.4 (Phase 0). Each screen here is the breadth instrument for one edge defined there.

**Changelog (v0.2):** the interior is rebuilt to match the scaffold. Three changes — (1) **scoring/ranking replaced by coarse gates** (a screen is a classifier of "is this name in the setup region," not a measurement of how good it is); (2) an **ingestion layer + contract** added beneath the screens, since a screen is only as reliable as its inputs; (3) **news fenced to event-detection and context only** — never a quality, neglect, or ordering signal. Each screen's signals are now vetted for reliability rather than listed for plausibility, and missing-data behaviour is made explicit.

**Purpose:** convert each edge's *setup signature* into cheaply-observable gates that triage the gated universe (thousands) into a per-edge shortlist (dozens) for the CIQ depth stage. The screen finds the **setup**, never the **edge** — the discriminator is downstream.

---

## Design principles (first principles)

1. **A screen approximates a setup signature with cheap signals.** It does not analyse the business; it finds names that *look like* the setup.
2. **Recall over precision — deliberately.** Cast wide, tolerate false positives. The CIQ depth stage and the bull/bear/judge harness reject the twins. A screen that tries to pre-judge quality with cheap data fails twice: it misses real setups *and* manufactures false confidence.
3. **Classify, don't score.** Each screen is a small conjunction of coarse gates derived from the setup definition — not a weighted composite. Reasons in the gating section below; this is the load-bearing change from v0.1.
4. **CIQ appears in no screen — there is no programmatic feed.** Breadth is built only from: **SEC EDGAR** (US issuers — XBRL fundamentals, full-text filing search, Form 4; the only free programmatic *fundamental* source), the **IBKR API** (global — price, 90D ADV, listing currency, vol, options, coarse scanner; the tradeability/liquidity/stress layer), and **web/news** (events and context only). *Koyfin free tier is UI-only → manual cross-check. TradingView unverified → excluded.*
5. **News is fenced.** News is reliable for *what happened* (a guidance cut, a contract, a downgrade) and useless-to-harmful for *how good/important* something is. News volume/intensity is the hype channel the flow-chasing twin lives in; ranking on it imports the exact noise the discriminator exists to remove. **News contributes detected events and context flags — it never gates and never orders.**
6. **The universe gate runs first, for all screens** (the capacity gate from the build brief): ex-China; tradeable on IBKR with data; liquidity floor (target position ≤ ~15–20% of IBKR 90D ADV); market-cap band.
7. **The screen→depth contract:** each candidate ships with its full signal vector, the trigger, the UNKNOWN gates depth must resolve, and *the specific twin to rule out.* A verdict is never the output.

## Ingestion layer & contract (beneath the screens)

Ingestion is a distinct layer — the data spine from the build brief — and the screens are merely its consumers. A stale price, a missed filing, a duplicated headline, or a mis-resolved ticker produces confident garbage regardless of gate logic. So the screens declare a contract with ingestion rather than assuming clean inputs.

**Pipeline stages:** pull → normalise → **entity-resolve** → time-stamp → store → refresh → dedupe.

**The contract each screen depends on:**
- **Freshness:** price/ADV daily; EDGAR filings same-day; news timestamped and deduplicated before it reaches a screen.
- **Completeness, declared:** known coverage per source, with gaps flagged *explicitly* so a gate can return UNKNOWN rather than silently failing or imputing.
- **A stable entity key** mapping each name across EDGAR (CIK), IBKR (conid), news, and Koyfin. Without it you cannot join price to fundamentals to filings — entity resolution is the foundation, not a detail.
- **Point-in-time stamping** on every datum (as-of / knowable date). It matters mainly when you later validate; stamping from day one makes that cheap instead of impossible.

**Source-reliability tiers (they are not interchangeable):** EDGAR (structured, authoritative) > IBKR (reliable, but rate-limited and gated by market-data entitlements) > news (noisy, unreliable — fenced to events/context per principle 5).

## The coverage asymmetry — sharpened by the gate framing

EDGAR is **US-only** and the only free programmatic *fundamental* feed. Under gates, the bite is now precise rather than hand-waved:

- **US names:** all gates evaluate — a real filter.
- **Non-US ex-China names:** every *fundamental* gate (cheapness-vs-history, non-distress, multiple-at-floor) returns **UNKNOWN→defer**; only the *price/liquidity* gates (global, via IBKR) evaluate. Screen 1 in particular degrades to a near pass-through (see its note); Screen 2 survives best because two of its three gates are price-based.

The standing tension: **your edge is richest where coverage is thinnest** (under-covered non-US/EM), but **your breadth tooling is cheapest where data is free and programmatic** (the US). *Recommendation (overrule if you disagree — it nudges against your geography-agnostic mandate):* prove the loop **US-first**, where the funnel is high-recall and the EDGAR+IBKR clients are reusable anyway; for non-US, accept that the screen is weak and substitute **human domain-driven sourcing** into the depth stage, building EDINET/DART/Companies House parsers only once a specific market earns it.

## Scoring → gating: how candidates are selected reliably

The naive composite — normalise signals, weight, sum, rank, take top N — is fragile here, and every failure traces to the word *reliably*: weights are an overfitting surface (Goodhart at machine speed); heterogeneous, differently-reliable signals aren't commensurable in one sum; missing data (the majority case) breaks composites; a scalar destroys the *why* depth needs; and fine ranking is false precision for a deliberately loose screen.

So each screen is a **conjunction of coarse gates**, each returning **PASS / FAIL / UNKNOWN**:
- **Admission rule:** a name is a candidate iff no gate FAILs and every *evaluable* hard gate PASSes. UNKNOWN gates do not block — they are carried forward as depth tasks. (Consequence: where the evaluable set is thin — non-US — filtering power is correspondingly weak, and the doc says so rather than pretending otherwise.)
- **Coarse by design = robust:** a name either fell 30%+ or it didn't; small measurement error doesn't flip a coarse gate the way it flips a composite rank. That stability *is* the reliability — reproducible, deterministic given the data, stable week-to-week.
- **Graceful degradation:** a gate that can't be evaluated returns UNKNOWN→defer, never a corrupted number.
- **Validate, don't optimise:** gates are set by face-validity and a handful of *known historical setups* (do real orphaned/de-rated names pass? are obvious non-setups excluded?). They are **never** tuned on forward returns — that reintroduces look-ahead and overfitting. Thresholds below are illustrative starting points to be calibrated to the *actual gated universe*, by face-validity, not by P&L.
- **Ordering, only as coarse triage:** if depth runs ~10/week and a screen returns 40, sort into 2–3 bands by the *single most reliable* signal for that screen — never a continuous composite. Every candidate still arrives with its full vector.
- **Honest scope of this choice:** gates-over-scores is situation-specific, not a universal law. Composite factor scoring is appropriate for systematic factor funds with clean, abundant, homogeneous data and real out-of-sample infrastructure. Every one of those preconditions fails for you — which is *why* gates dominate here.

---

## Screen 1 — Orphaned quality

**Setup signature:** a sound business, cheap and under-attended, while flow crowds into a hot theme elsewhere.

**Gates (conjunction):**
- **G1 — Low attention.** Daily turnover (90D ADV × price ÷ market cap) in the low tail of its cap band. *Source:* IBKR + shares. *Missing:* shares absent → UNKNOWN; otherwise always evaluable. *(Turnover, not news frequency, is the reliable neglect proxy.)*
- **G2 — Hasn't re-rated.** Trailing 6–12m total return flat/negative and not in a strong uptrend. *Source:* IBKR price. *Missing:* none.
- **G3 — Cheap vs own history.** Current EV/EBITDA (or P/E) in the bottom third of its trailing 3–5y range. *Source:* EDGAR XBRL + IBKR price. *Missing (non-US):* UNKNOWN→defer.
- **G4 — Not distressed** (light filter, *not* the soundness discriminator). Positive trailing FCF or operating income, and net leverage below a coarse ceiling. *Source:* EDGAR XBRL. *Missing (non-US):* UNKNOWN→defer.

**Attached context (never gates):** an identifiable hot theme drawing flow away (ETF flows via Koyfin manual; sector relative strength via IBKR; theme *event* from news). Present strengthens the case; absence does not exclude.
**Triage band:** cheapness percentile (US); turnover (non-US/fallback).
**Deferred to depth — rule out the *value trap*:** confirm (1) fundamentals genuinely stable/improving, (2) neglect is flow-driven not informed-specialist (Holders / Insider), (3) a catalyst exists.
**Non-US note:** G3 and G4 go UNKNOWN, so the screen filters only on G1+G2 (neglected + hasn't run) → a near pass-through. For non-US this screen does not really discriminate; lean on human domain-sourcing + depth.

## Screen 2 — Overshot de-rating

**Setup signature:** a sharp, name-specific decline + multiple compressed toward floor + (often) capitulation/stress. This screen degrades least across geographies — two of three gates are global price signals.

**Gates (conjunction):**
- **G1 — Sharp drawdown.** ≤ −30% from the trailing 52-week high, the decline recent/ongoing. *Source:* IBKR price. *Missing:* none. (The cleanest gate in the system.)
- **G2 — Idiosyncratic.** Underperformed its sector/market by a wide margin over the decline window — name-specific, not beta. *Source:* IBKR price vs sector index/ETF. *Missing:* no clean benchmark → UNKNOWN (rare).
- **G3 — Multiple at/near floor.** Current multiple in the bottom decile/quartile of its trailing range. *Source:* EDGAR XBRL + price. *Missing (non-US):* UNKNOWN→defer.

**Attached signals (point depth where to look; never gate — requiring them would lose recall on real overshoots that lack liquid options or clean filings):** *threat/event* — guidance-cut 8-K (EDGAR, US), earnings gap-down (IBKR price + report calendar), downgrade *event* (news); *stress* — elevated implied vol where options liquid (IBKR), volume spike (IBKR), elevated short interest (Koyfin/IBKR).
**Triage band:** drawdown depth + multiple-at-floor (US).
**Deferred to depth — rule out *terminal decline*:** judge real-and-permanent vs exaggerated-and-temporary; inflection vs mid-bleed; name the reversal. **This is the dangerous judgment and it is depth's, not the screen's** — the screen establishes only that a name has been hit and de-rated, never *why* or *whether it reverts*. No threat-detection gate, deliberately: gating on detected threats would import news noise and miss de-ratings whose threat isn't loudly reported.

## Screen 3 — Second-order propagation

A *sourcing lens* with one gate, not a symmetric filter — consistent with Edge 3 booking through Edge 1. It builds a candidate set from a relationship graph, then gates.

**Step A — detect the wave:** a hot theme (ETF flows via Koyfin manual; theme *event* via news) plus a ripping basket of obvious beneficiaries (IBKR relative strength).
**Step B — construct the second-order set (the AI-native, highest-value component):**
- **EDGAR full-text search for the obvious name(s) appearing as a named customer / supplier / partner in *other* companies' filings** (US, programmatic — exactly the dependency-graph trace the thesis calls for).
- LLM extraction of named dependencies from the obvious beneficiaries' 10-Ks / transcripts.
- News *events* — contracts, design wins, partnerships (event detection only).
**Step C — gate:**
- **G1 — Hasn't re-rated.** The second-order name's trailing return over the theme window materially lags the obvious basket (still flat/cheap — the propagation lag). *Source:* IBKR price. *Missing:* none. (The one hard gate.)
- **Materiality of the link + standalone viability:** UNKNOWN→defer in essentially every case — these need Customers & Suppliers / Segments, i.e. depth. The screen confirms a link *exists* and the name *hasn't moved*; depth confirms the link is *material* and the name *stands alone*.

**Triage band:** specificity/count of filing mentions of the link — coarse, and explicitly weak ordering.
**Deferred to depth — rule out *top-of-theme flow-chasing*:** confirm material *economic* exposure, re-confirm not-already-re-rated, and confirm it **stands alone if the flow reverses** — if not, it is naked flow-riding → reject (out of scope).
**Coverage note:** the EDGAR full-text trick is US-only; for non-US second-order names the map leans on LLM extraction + news and is weaker.

---

## Recall management (you cannot measure it, so you manage it)

There is no ground truth for the setups a screen silently missed, so recall can't be computed — only managed: keep gates loose (principle 2); face-test against known historical setups before trusting a screen; watch **depth's rejection reasons** as the feedback loop — if depth keeps rejecting candidates for something a cheap gate could have caught, tighten that gate; if it rejects for reasons only depth can see, that is the *correct* division of labour, leave the screen alone; and periodically sample the **excluded** set to check you are not systematically blind to a whole setup type.

## Throughput, cadence, overlap

- **Funnel math:** gated universe (thousands) → per-screen shortlist (dozens) → CIQ depth (manual, a handful at a time) → portfolio (8–15). Size the shortlist to depth's *manual* throughput — no point surfacing 200 names if you can run the discriminator on ~10/week.
- **Cadence:** Screens 1 and 3 on a periodic full scan (e.g. weekly); Screen 2 is also **event-driven** — trigger intra-week on large single-day movers and material 8-Ks, since de-ratings are events.
- **Overlap is fine:** a name may fire on several screens. Route to depth once, carrying *all* triggers and *all* twins-to-rule-out.

## Build note (for Claude Code)

Build order: the **ingestion layer first** — EDGAR client, IBKR client, entity resolver, store with freshness/PIT stamping and dedupe — because the screens are consumers of it and reliability is bounded by it. Then per-screen **gate evaluators** (PASS/FAIL/UNKNOWN, *not* scorers) emitting **candidate records**: full signal vector + trigger + UNKNOWN-gates-for-depth + twin-to-rule-out + triage band. The EDGAR and IBKR clients are shared across all three screens; the **relational graph builder** is Screen 3's unique, most novel piece. Spec'd in markdown, tested against known historical setups (face-validity, never forward-return tuning), committed alongside the framework. Any later dashboard deploys via GitHub → Cloudflare Pages, configured once.
