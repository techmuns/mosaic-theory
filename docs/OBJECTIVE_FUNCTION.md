# Objective Function & Constraints — Phase 0

**Version:** v0.2 · **Status:** scaffold + decided content; **[TO SET] slots filled (2026-06-17); return target set provisionally; only the AUM soft-close stays deferred** · **Owner:** Munshot Research
**Changelog (v0.2):** filled the principal's [TO SET] slots — capital ($200K own + $1M LP first close, 2–3yr), 30% max-drawdown, concentration (~8–12% name / ~20% sector/theme / country n/a under US-first), long-biased with little/no leverage, LP terms (2yr lock → return of capital), and deontological lines (ex-China for all capital; LP capital additionally ex-India). **Return target** now set **provisionally** (§1) — deliberately not anchored hard, since selection alpha is unvalidated until Loop 1. **Still deferred:** the **AUM soft-close** (not binding at ~$1.2M). Also corrected a stale internal pointer (the slots live in §1–§4; there is no '§5').
**Pairs with** `EDGE_THESIS.md` v0.4. Together they are Phase 0's intellectual content — the edge thesis says *where alpha comes from*; this says *what we optimize and the fences we may never cross to do it.* (The ops/capital/regulatory skeleton is the remaining operational half of Phase 0, still pending per `BUILD_STATUS.md`.)

> **Whose document this is.** Setting the objective function is the principal's irreducible job — it encodes your risk appetite, capital, and values, and it is the one thing that must not be delegated to the system being built. What follows fills only what our prior work has *already determined* (tagged **DERIVED**); every value- and risk-laden choice is left to you (tagged **TO SET**), each with the test it must satisfy. Where a default is proposed it is tagged **[PROPOSED — confirm or kill]** and is mine to be overruled, not yours to inherit.

---

## How to read this (first principles)

An objective function is two things: **(a) what we maximize**, and **(b) the constraints we may never cross to maximize it.** For an AI-native fund there is a special hazard — part of the optimizer is a machine that takes the spec *literally* and games it at speed. That is Goodhart's law at machine speed, the dominant risk in the build. So every constraint below is written as a **fence against a specific way the objective would be gamed**, and each names the failure it prevents. That construction — fences against named failure modes, not a generic policy checklist — is what makes this *this fund's* objective function.

The ordering rule, stated because a literal optimizer will otherwise violate it: **when the objective and a constraint conflict, the constraint wins.** The objective is subordinate to the fences.

## 1. The objective (what we maximize)

- **For whom, over what horizon:** **[SET]** — ~**$1.2M at first close**: **$200K own** + **$1M LP already raised**, committed **2–3 years** (return of capital after year 2 — see §2 LP terms). *(Partly closes audit A8 — LP capital is committed. But the engine is still unvalidated, so deployment must be **phased against Loop 1**, not switched on at full size. See PM note.)*
- **What we maximize: risk-adjusted return per unit of capacity-constrained capital — not raw return, and explicitly not AUM.** **[DERIVED:** the edge dies at scale, so the goal is return *at a defended AUM*, never AUM × return.**]**
- **Target:** **[SET — provisional, pending Loop 1].** You specified **mid-double-digit absolute (~15%)** and/or **beat the benchmark by ≥2×**. Recorded as: **a relative goal — beat a US small/mid-cap index by a wide margin — with ~15% absolute as a provisional floor and ≥2× index as a *stretch aspiration*, not a hard constraint.** **[Why not both as hard floors]:** the two conflict by regime (a +25% market makes 2× = +50%, unreachable within §2; a flat market makes +15% the binding one), and **≥2× index *sustained* is an elite, rare bar** — held as a hard target it would pressure the concentration and leverage fences, i.e. it is the single value most able to Goodhart the fund. *Test (unchanged):* achievable by the two core edges at the chosen AUM **without breaching any constraint in §2**. **Binding caveat:** selection alpha is **unproven until Loop 1**, so this is explicitly **provisional** — a *consistency condition*, re-set upward only once the loop shows a real BUY−AVOID spread. Under a 30% max-drawdown with little/no leverage, a high fixed absolute (e.g. 30%/yr) presupposes large validated alpha and is barely reachable — do not anchor there.

## 2. Constraints as fences (each names the failure it prevents)

### Risk & capital — fence against *"maximize return → take uncompensated tail risk"*
- **Max-drawdown line:** **[SET] 30% (fund-level / portfolio peak-to-trough).** Breach forces de-risking on a **tiered drawdown ladder** **[PROPOSED — de-gross in steps as the drawdown deepens toward 30%]**. *Prevents:* ruin from an un-sized left tail. **[CONFIRM]** you also named per-*name* drawdown as a review trigger (§4): read as **30% = the fund de-risk line**, while individual-name drawdowns feed **monitoring/kill-criteria** (a separate mechanism). Confirm that split.
- **Concentration:** **[DERIVED]** 8–15 positions; **[SET]** single-position cap **~8–12% of NAV**, **sector/theme cap ~20%**, **country cap n/a** under US-first (revisit if the universe goes multi-country). *Prevents:* blow-up from one name; a hidden theme bet masquerading as stock-picking. *(~8–12% × ~10 names ≈ fully invested — consistent with long-biased.)*
- **Leverage:** **[SET]** long-biased; **little-to-no leverage** (gross ≈ 100%, net long); **hedges permitted only to protect longs when needed** (index/ETF/futures — no single-name shorts; small-cap borrow is scarce, per the edge thesis). *Prevents:* levering a thin edge into ruin.
- **Liquidity / capacity:** **[DERIVED]** target position ≤ ~15–20% of IBKR 90D ADV; size for the **exit**, not the entry. *Prevents:* the small-cap illiquidity trap (easy in, brutal out).
- **The risk borne must be named:** **[DERIVED — the fraud detector]** every position states the risk borne / service provided / why the counterparty loses. No nameable answer → no trade. *Prevents:* being the adversely-selected party (there is no "free money").

### Process integrity — fence against *"speed → act on ungrounded or hallucinated theses"*
- **Source-binding:** every load-bearing claim traces to a primary source. *Prevents:* sizing into fiction.
- **Harness gate:** a position requires a thesis that survives bull/bear/judge with its **twin actively ruled out** (value trap / terminal decline / flow-chasing). *Prevents:* confirmation-driven entry into the twin.
- **Human owns the trigger:** the machine surfaces candidates; it never executes unilaterally. *Prevents:* a silent machine error becoming a live trade.

### AI-native integrity — fence against *"maximize backtested Sharpe → overfit"*
- **Validate, never optimize on forward returns:** gates and signals are set by face-validity and known historical cases; no P&L tuning, ever. *Prevents:* look-ahead and data-mined pseudo-edges — the dominant AI failure.
- **Minimise fittable parameters:** gates over composite scores. *Prevents:* the overfitting surface.
- **Deflated / out-of-sample standards** for any quantitative claim. *Prevents:* chance artifacts manufactured at scale.

### Strategy identity — fence against *"maximize 'looks like an edge' → drift and flow-chasing"*
- **In scope** **[DERIVED]:** long-biased; ex-China; small/mid-cap and special situations; Edge 1 and Edge 2 core; Edge 3 (propagation) as a **sourcing lens only**.
- **Out of scope (hard)** **[DERIVED]:** misunderstood-adoption as a *primary* thesis; naked flow-riding / theme-adjacency without standalone economics; out-of-capacity strategies; thesis types whose data lies outside the verified inventory. *Prevents:* drift into crowded, uncompensated, or flow-borne bets and into setups the data cannot support.

### Business integrity — fence against *"maximize AUM → erode the edge"*
- **Soft-close at a defended AUM cap:** **[OPEN — deferred]**, derivable once the gated universe is known (from the position-size-vs-ADV math). **Not binding at ~$1.2M** — set before any raise beyond the first close. The capacity edge *is* the thesis; growth that erodes it is forbidden, not an aspiration. *Prevents:* the growth paradox eating the fund.
- **LP liquidity terms matched to book illiquidity:** **[SET]** first close — **2-year lock, then return of capital**. *Well-matched:* a weeks-to-quarters book turns faster than a 2-year lock, so forced-sale risk is low. *Prevents:* a liquidity mismatch in which redemptions force fire-sales of illiquid names.

## 3. Lines we will never cross (hard — no trade-off at any price)

- **No trading on material non-public information.** Edge 1 and Edge 2 touch ownership and insider data, so this is live: every thesis stays strictly on the **public-synthesis** side of the line; a leak or tip is never actionable. *(Anticipated pre-announcement run-ups are tradeable only when inferred from public filings and base rates, never from non-public knowledge.)*
- **[SET] Jurisdictions:** **ex-China for all capital** (per mandate); **LP capital additionally may not be invested in India.** No sector/theme restrictions. *(Own capital is not India-restricted — see PM note on whether to run a separate own-capital sleeve or apply a blanket ex-India to the whole book; under US-first the distinction is near-moot operationally.)* **[FLAG → legal/ops track, updated 2026-06-17]:** capital is raised in a **HK company and held in USD** (not Indian jurisdiction), which addresses the inbound / round-tripping concern — you are not investing *into* India, so SEBI-FPI is not in play. The residual, subtler items for cross-border (India + HK) counsel: **(i) POEM** — a HK company *effectively managed from India* can be deemed Indian tax-resident (likely moot at ~$1.2M given the turnover threshold, but live as you scale toward the mandate); **(ii)** FEMA **Overseas Investment / LRS** treatment of the resident's own **$200K** placed into a foreign financial-services entity (OI rules scrutinise exactly this); **(iii)** the **India-sourced management/advisory activity** (fee income, permanent-establishment questions) and **HK SFC Type 9** licensing for the management itself. *Not legal advice — confirm with a qualified India/HK adviser.* **[CONFIRM]** any hard leverage ceiling beyond the §2 'little/no leverage' fence.
- **The objective function may not be altered by the system — only by deliberate human decision** (see §4).

## 4. Governance of the objective function itself (meta-stability — the capstone fence)

The constraint that keeps the other constraints from eroding.
- **Version-controlled.** This is v0.2.
- **Changed only by explicit human decision** — never implicitly by the system, and never as a post-hoc rationalisation after a painful loss or a tempting win.
- **Every proposed change must state which fence it loosens and which Goodhart failure that re-exposes** — so erosion is visible, deliberate, and on the record, not silent.
- **Reviewed on a cadence** **[SET]** — **monthly**, and immediately on a drawdown breach (the fund-level 30% line, and any per-name kill-criteria / drawdown trigger).
- **Human ownership map (the irreducible nodes):** objective & risk appetite (principal); final trigger (PM); out-of-distribution judgment; detecting confidently-wrong machine output. The machine owns none of these — it may inform every one of them and decide none.

## 5. Slots to set — the ledger (yours, each with its test)

| Slot | Test it must satisfy | Default |
|---|---|---|
| Capital base & source (own / LP, amount) | determines whether SFC licensing binds; sets the AUM math | — |
| Investment horizon & capital lock-up | must match the weeks-to-quarters edge horizon and the book's illiquidity | — |
| Return / risk-adjusted target | achievable by Edges 1–2 at chosen AUM **within** §2 | — |
| Max-drawdown line | the level that, breached, forces de-risking | tiered ladder **[PROPOSED]** |
| Single-position / sector / country caps | no single name, theme, or country can sink the book | single-name ~12–15% **[PROPOSED]** |
| Leverage (gross/net) | a thin edge must not be levered into ruin | long-biased, ~none **[PROPOSED]** |
| Hedge policy *(the open long-only-vs-hedged decision)* | hedges via liquid ETFs/futures, not single-name small-cap shorts | hedge beta only, surgically **[PROPOSED]** |
| AUM soft-close cap | the level at which capacity erodes the edge | derive from universe math |
| LP liquidity / redemption terms | matched to book illiquidity (no fire-sale risk) | — |
| Deontological lines | non-negotiable, return-independent | MNPI line **[DERIVED]**; rest **[TO SET]** |
| Review cadence | frequent enough to catch drift, not so frequent it invites tampering | quarterly + on breach **[PROPOSED]** |
| *Cross-ref (from `BUILD_STATUS`)* | HK structure & SFC Type 9 · CIQ data-license scope · FX-hedge policy | open |

---

*End v0.2. Closes the **intellectual** half of Phase 0: the principal's values are set (return target provisionally, pending Loop 1; AUM soft-close deferred until the universe is known). The operational half — ops/capital/regulatory — is still pending per `BUILD_STATUS.md`.*
