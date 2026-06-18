# AI-Native Long Fund — Build Blueprint

**Version:** v0.1 · **Status:** working draft · **Owner:** Munshot Research

**Mandate:** $5–30M USD · long-biased · sector- and geography-agnostic **ex-China** · weeks-to-quarters horizon
**Stack in hand:** S&P Capital IQ (exports + charting) · Interactive Brokers (HK domicile, API execution)

> This is an internal engineering/operating document, not a client deliverable. It is meant to be edited, versioned, and executed against in phases.

---

## 0. Framing — the constraint is the strategy

You are not trying to out-return funds with impeccable records at their own game. You are occupying the part of the market their **size forbids them from entering**. This is the master fact, and the whole design falls out of it:

- **Alpha and capacity are inversely related.** The most-watched, most-efficient names are where large books are *forced* to live, because only deep liquidity absorbs billions. A name trading $2M/day is uninvestable to a $5B fund — its own entry moves the price and the position can never matter to its P&L. Your $5–30M is a **passport**, not a handicap.
- **"Non-replicable for LPs" means dies-at-scale, not a bigger number.** No large vehicle can package a capacity-constrained, ex-China, under-covered-equity edge, because the edge evaporates above a certain AUM. The LP is buying *access to something structurally inaccessible* — the cleanest definition of non-replicable, available to you *because* you are small.
- **The fee math forbids closet indexing.** 2% on $15M barely covers a real operation. The business only survives on genuine performance, so the economics force real alpha or death. That is healthy — it removes the lazy option.

**The right question** is therefore *not* "how do we perform like the greats?" It is: **what can $5–30M + two people + parallel cognition do that a $5B fund cannot?** Everything below answers that.

---

## 1. The edge, in one line

> Coverage-at-depth across the under-covered ex-China small/mid-cap and special-situations universe — the breadth of a thirty-analyst shop run by two people via parallel cognition, every thesis adjudicated by a verification harness, every position sized where your capital is invisible.

The model does the *reading*; the harness enforces *truth*; the humans own the *objective and the trigger*. The model is rented and commoditizes in months — it is never the edge.

---

## 2. How your two tools map onto the system — and the gap that is your moat

### Capital IQ — the fundamental spine
Gives you standardized + as-reported financials, screening, comps, consensus estimates, ownership and transactions data, and charting via the Excel plug-in / exports. It is the backbone of the universe filter, the comps engine, and the "knowable fundamentals" layer.

Two problems to engineer around, plus one caution:
- **Look-ahead and survivorship are baked into default views.** CIQ's "latest" pulls show *restated* financials, *current* index membership, and *current* entity names. Backtesting or signal-validating against those is fiction — you will discover "edges" that were unknowable at the time. **You must use as-first-reported figures with their report dates, and snapshot point-in-time.** This is non-negotiable and is workstream #2.
- **Coverage thins exactly in your target pond.** CIQ is strong on developed and larger-EM names — i.e. the efficient water you *don't* want to fish — and progressively thinner on micro-caps and frontier names, which is where your edge lives. So CIQ alone biases you toward the crowded end. The fix is a long-tail primary-filing parser (workstream #2b) for the names CIQ underserves. **That manufactured long-tail dataset is part of your moat precisely because the names are too small for any vendor to bother with.**
- **Caution:** respect CIQ's licensing/ToS on automated extraction, storage, and redistribution. Confirm the permitted scope before building scheduled pulls. *(Not legal advice — confirm with counsel and your CIQ agreement.)*

### IBKR (HK) — the tradeable universe, execution, and risk surface
Defines what is *actually* tradeable (broad global venue access), automates execution (Python API — `ib_async`/`ib_insync` is the pragmatic wrapper for a two-person shop; the official `ibapi` and the Web/Client-Portal API are alternatives), and provides positions, account state, market data, and historical bars for the technical/charting layer.

Design consequences:
- **Geography-agnostic is bounded by IBKR's venues.** "Anywhere ex-China" in practice means "anywhere ex-China *that IBKR trades, with market data available and acceptable commissions*." The capacity gate (§4) must intersect with this.
- **Long-bias is reinforced by borrow reality.** Small-cap borrow is scarce, expensive, and recall-prone. Shorting individual small caps is its own fat-left-tail trap. Express hedges and beta management through **liquid index/sector ETFs or futures** on IBKR; reserve single-name shorts for the rare case with overwhelming edge *and* locatable, affordable borrow.

### The gap between them is what you build
CIQ ends at "here are fundamentals (with look-ahead) for the well-covered names." IBKR ends at "here is what you can trade and how." Neither gives you: point-in-time integrity, long-tail coverage, mechanized disconfirmation, or the orchestration that fuses fundamentals + tradeability + cognition into *surfaced, sourced theses*. **That gap is the entire moat.** Two shops on the same rented model and the same two vendors diverge completely on how well they build it.

---

## 3. The moving parts (system map)

Each layer is a workstream. "Moat?" flags whether it is defensible or commodity.

| # | Layer | Fed by | Moat? |
|---|-------|--------|-------|
| 1 | **Capacity & tradeability gate** (hard pre-filter) | CIQ screen ∩ IBKR tradeable ∩ liquidity floor | No (but mandatory) |
| 2 | **Data spine + point-in-time discipline** | CIQ exports normalized & date-stamped | **Yes** (integrity) |
| 2b | **Long-tail filing parser** | Primary filings via AI cognition | **Yes** (manufactured data) |
| 3 | **Idea generation — the fleet** | Screens + event detection + thesis construction | No |
| 4 | **Verification / adjudication harness** | Outputs of #3, grounded in #2/#2b | **Yes** (the core moat) |
| 5 | **Valuation & analysis engine** | CIQ comps + AI synthesis on survivors | Partial |
| 6 | **Portfolio construction, sizing, risk** | #4 output + #1 constraints | Partial |
| 7 | **Execution** | IBKR API | No (craft) |
| 8 | **Monitoring, thesis-break & decay detection** | Live data + #4 kill-criteria | **Yes** (loop velocity) |
| 9 | **Meta-governance + objective function** | Human-owned | **Yes** (undelegatable) |
| 10 | **Business / ops / regulatory** | HK structure, audit, LP reporting | No (table stakes) |

The money and the durability sit in the **unglamorous layers** (2, 2b, 4, 8). The glamorous "we use a great model" layer (3, 5) is the commodity everyone will have.

---

## 4. The capacity & liquidity gate — concrete rules

Applied **before any analysis**. No point reading a name you cannot trade at size.

1. **Tradeable on IBKR** with market data available and commission/fees acceptable relative to expected edge.
2. **Liquidity floor — the binding rule.** Target position must be exitable in ~1–3 trading days at ≤ ~20% participation of 20-day median dollar ADV. Concretely: **target position ≤ ~15–20% of 20-day median ADV.**
   - *Worked example:* a name trading $2M/day → at 20% participation you can move ~$400K/day → a $1M position takes ~2.5 days to exit. A $2M position (~100% of daily volume) breaches the rule. So at this liquidity, ~$0.8–1.2M is the position ceiling regardless of conviction.
3. **Market-cap band** (tunable starting point): ~$200M–$5B. Below the floor you lose tradeability, borrow, and CIQ coverage; above the ceiling you drift into the efficient water big funds own.
4. **Borrow test (any short):** locatable, affordable, low recall risk. Most small caps fail → defaults the book to long-biased; hedges via ETFs/futures.
5. **Concentration:** 8–15 positions; hard single-name cap (e.g. 12–15% of NAV); aggregate single-name exit-time ceiling.
6. **Currency:** USD reporting over multi-currency exposure via IBKR → explicit FX-hedge policy decision (see §9).

These are starting values to be tuned against realized fills, not laws.

---

## 5. The verification / adjudication harness — spec

The single most important build. Cheap parallel generation manufactures thousands of beautiful, significant-looking, false signals; this layer is what stands between you and a gorgeous backtest that loses real money.

A thesis only reaches a human **after** clearing every gate below.

1. **Structured sourced claim set.** A thesis enters as discrete claims, each tagged to a primary source — a specific CIQ field *with its as-reported date*, or a filing line/URL. Unsourced claims are quarantined, not trusted.
2. **Adversarial pass.** A *bear* agent tries to kill the thesis using only checkable facts; a *bull* agent defends; a *judge* scores the exchange and **explicitly flags every unsupported or hallucinated claim**.
3. **Mandatory fields** (no thesis advances without them):
   - **Kill-criteria** — the observable events that would falsify the thesis, defined *now*, so monitoring can watch for them.
   - **Other-side test** — "Who is selling to me, and why?" A non-hand-wavy answer is required. Usually you are being paid a premium for being short a tail (deal break, liquidity hole, jump); naming it is the point.
   - **Disconfirmation** — "What would make this wrong, and is that observable today?"
4. **Look-ahead audit.** Confirm no input uses restated or otherwise future-knowable data. This is where CIQ default-view discipline is enforced mechanically.
5. **Quant-signal gate** (for any statistical signal): out-of-sample + walk-forward validation, and a multiple-testing correction (deflated Sharpe) so that scanning many features doesn't hand you chance artifacts.
6. **Human gate.** Only post-clearance does the thesis surface, as a **one-page dossier**: sourced claims, the surviving bear case, kill-criteria, sizing rationale tied to §4, and the other-side answer. The human makes the accountable trigger decision and may veto — but is adjudicating *real, sourced* theses, not raw model output.

---

## 6. Build sequence (phased)

Build the moat and the bottleneck first. Prove one loop before scaling breadth.

- **Phase 0 — Found it.** Write the **objective function** and the **hard constraints** (what the system optimizes, and what it will *never* do). Stand up the fund/ops/regulatory skeleton (§9/§10). Secure capital. Founder-level, pre-code.
- **Phase 1 — Data spine, narrow.** Point-in-time normalization + entity resolution of CIQ exports for **one** universe slice (one market/sector you know well). Establish IBKR connectivity in **paper** mode and pull historical bars. Boring; foundational.
- **Phase 2 — One loop, end to end.** A single strategy on that slice: generate → verify → size → (paper) execute → monitor. Prove the loop with paper or minimal capital. **Velocity beats breadth here** — you're testing whether the *process* compounds, not how many names it covers.
- **Phase 3 — Harden verification.** Build out the adversarial harness, OOS/walk-forward gates, and decay detection. Add the **long-tail filing parser** (#2b) for names CIQ underserves. This is where you stop fooling yourself.
- **Phase 4 — Scale breadth, then diversify.** Point the fleet at the rest of the ex-China universe. Add a **second low-correlation strategy** — what turns a single edge into a portfolio.
- **Phase 5 — Institutionalize.** Compounding research memory, monitoring dashboard, LP reporting, and a deliberate **soft-close discipline** (§8). *Any web surface (dashboard, LP portal) deploys via the standing GitHub → Cloudflare Pages automation — configured once, then automatic; no manual redeploys.*

---

## 7. Two people — labor allocation

The org chart is a system architecture with humans only at the irreducible nodes.

**Human nodes (cannot be delegated to the system you're building):**
- Setting the objective function and risk appetite (the principal choosing what to optimize).
- The final, accountable trigger decision.
- Judgment when the world leaves the training distribution (regime breaks the model has never seen).
- Detecting when the machine is **confidently wrong** — because models fail silently, not loudly.

**Machine (the fleet):** universe coverage, first-pass analysis on everything, the adversarial verification swarm, and continuous position monitoring.

**Suggested split between the two of you:** one owns research judgment + portfolio decisions; one owns the system, data integrity, and execution engineering. **Both must internalize the objective function** — it is the shared contract. Mitigate key-person fragility by keeping the system documented and reproducible enough to survive either of you being unavailable.

---

## 8. Risk register (the disconfirmation — read this twice)

- **Goodhart's law at machine speed — your dominant risk.** A powerful optimizer pointed at "maximize backtested Sharpe" finds overfit, short-volatility disasters with breathtaking efficiency. Mitigant: the §5 harness and an honest objective function. Risk scales *with* the capability of your system.
- **Hallucinated theses.** The model asserts false facts confidently. Mitigant: every load-bearing claim traces to a checkable source, or it doesn't size.
- **CIQ look-ahead.** Default views bury survivorship and restatement bias. Mitigant: point-in-time discipline (#2). Skip it and your backtest is a lie.
- **Liquidity asymmetry.** The thinness that gives you edge means easy entry, brutal exit; small caps gap in drawdowns. Mitigant: size for the exit, not the entry (§4).
- **The growth paradox.** The strategy works *because* it's small; the business will want to grow AUM; growth erodes the capacity edge that is the whole thesis. **Resolve deliberately:** soft-close at a defended AUM cap, graduate to larger-capacity strategies (accepting lower edge), or choose to stay small and excellent. Pretending the tension doesn't exist is how a great small fund becomes a mediocre medium one.
- **The model is rented.** Frontier capability commoditizes in months and is available to every competitor. The moat is data integrity + the verification harness + loop velocity + research memory — **never the model.**
- **Key-person fragility.** Two people, no redundancy → reproducibility and documentation are survival, not hygiene.
- **Regulatory / data-license.** HK structure and CIQ extraction scope are real constraints, not afterthoughts (§9). *Not legal or financial advice — resolve with counsel.*

---

## 9. Open decisions to resolve (not mine to answer)

1. **HK structure & licensing.** Managing third-party LP capital from a HK base typically implicates SFC **Type 9 (asset management)** licensing, and a fund vehicle decision (offshore Cayman/BVI fund with a HK investment manager, or onshore HK **OFC** / **LPF**). This is a counsel-and-structuring question; flagged, not answered.
2. **CIQ license scope** for automated extraction, storage, and any onward use.
3. **FX-hedge policy** for USD-reported, multi-currency exposure.
4. **The AUM cap you will defend** — the number at which you soft-close to protect the edge.
5. **Long-only vs long-biased-with-hedges**, and the permitted hedge instruments (ETFs/futures vs single-name shorts).

---

*End v0.1. Next concrete step: Phase 1 — build the point-in-time CIQ normalizer against a real export schema and stand up paper-mode IBKR connectivity.*
