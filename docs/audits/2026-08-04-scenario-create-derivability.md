# `scenario-create` — what a proposer can default, and what it cannot

**Step 1 report. STEP 2 NOT BUILT — the stop condition fired.** Three of the nine numbers have no
defensible default, and the operator's rule is explicit: *a proposer that invents a number is worse
than a form.* Which three, and the measured evidence that the plausible-looking substitute is wrong,
are below.

**The rider ran first because it could have stopped everything. It did not — see §3.**

---

## 1. The nine numbers — anchor, committed leg, deviation

R1 is `EBIT = revenue × op margin` → `EBITDA = EBIT + D&A` → `EV = EBITDA × exit multiple` →
`equity = EV − net debt` → `value/share = equity ÷ diluted shares`. Three legs × three modelled
inputs = nine numbers. `d_and_a`, `net_debt` and `diluted_shares` are `facts`, not judgment, and all
three already sit in every dossier.

**SMPL, calibrating:**

| leg · axis | committed | computed anchor | source of the anchor | deviation |
|---|---:|---:|---|---:|
| bear · revenue | **1,180.0** | — | **none** | **—** |
| base · revenue | 1,330.0 | 1,351.7 | `consensus_levels.Revenue` FY2026 median | **−1.6%** |
| bull · revenue | **1,420.0** | — | **none** | **—** |
| bear · margin | 10.00% | **9.5788%** | min of the EDGAR per-FY operating-margin series (FY2020) | +0.42pp |
| base · margin | 14.00% | **15.4481%** | `anchor.margin.value` — median over 8 FY | **−1.45pp** |
| bull · margin | 16.50% | **17.3494%** | max of the same series (FY2022) | −0.85pp |
| bear · multiple | 7.00x | **6.1094x** | `own_history.low` — trading-range low | +0.89x |
| base · multiple | 12.50x | **17.8514x** | `own_history.median` — trailing median | **−5.35x** |
| bull · multiple | **16.00x** | — | **none established** | **—** |

**Six of nine have a defensible, source-bound default. Three do not.**

**R2** differs only in what the numbers mean — terminal-year revenue, terminal EBIT margin, exit
multiple, plus a per-leg `years_to_terminal` and a `tier`. **The derivability picture is the same or
worse**: R2's terminal year is further out than any consensus row reaches, so even the base-revenue
anchor that R1 gets from `consensus_levels` has no counterpart.

---

## 2. The three that cannot be defaulted — and why the obvious substitute is wrong

### revenue · bear and bull

`consensus_levels` carries `low`, `median`, `high` and `std_dev` per FY, so a low/high default looks
available. **Measured, it is not.**

SMPL's FY2026 consensus range is **1,345.0 – 1,357.0** — a 12.0 spread, **0.9% wide**. The committed
legs are **bear 1,180.0** and **bull 1,420.0**.

- Defaulting bear revenue to the consensus low would propose **1,345.0** against an analyst bear of
  **1,180.0** — **14.0% too generous**, in the leg that sets the risk denominator and therefore the
  reward:risk ratio.
- Defaulting bull to the consensus high would propose **1,357.0** against **1,420.0** — 4.4% short.

**The reason is structural, not a calibration miss: consensus dispersion measures DISAGREEMENT AMONG
FORECASTERS, not the downside scenario.** Eleven analysts modelling the same guidance agree within
1%; a bear case models a world none of them is forecasting. The two quantities are not the same kind
of thing, and a proposer that silently substituted one for the other would understate risk on every
name — a systematic error in the direction that flatters.

### multiple · bull

`own_history` gives `low`, `p25`, `median`, `p75`, `high`, `current`. Bear anchors to `low` and base
to `median` — both used by the committed record, both reproducing exactly today. **The bull has no
established anchor.** `p75` (20.88x) and `high` (28.88x) are the candidates, but SMPL's analyst chose
**16.00x — BELOW the trailing median of 17.85x.** So neither candidate reflects the practice, and a
low/median/p75 trio is an arbitrary mix rather than a principled one.

---

## 3. Rider — do SMPL's frozen references still reproduce?

**Recomputed against today's data. The answer splits exactly along static-vs-live, and it is the
cleanest possible demonstration of P3 pt1's consequence.**

| axis | reference | committed | today | |
|---|---|---:|---:|---|
| revenue | FY2025 reported revenue | 1,450.9 | 1,450.9 | **reproduces** |
| revenue | LTM revenue | 1,416.208 | **1,392.235** | **MOVED −23.97** |
| revenue | consensus FY26E revenue | 1,334.0 | **1,351.7** | **MOVED +17.70** |
| **margin** | screening median (naive, 8 FY) | 15.45 | **15.4481** | **reproduces** |
| **margin** | 7yr clean median (FY2025 adjusted) | 15.51 | **15.5107** | **reproduces** |
| **margin** | FY2020 worst clean year | 9.58 | **9.5788** | **reproduces** |
| **margin** | FY2022 best clean year | 17.35 | **17.3494** | **reproduces** |
| **margin** | FY2025 adjusted ex $60.9M impairment | 15.01 | **15.0103** | **reproduces** |
| multiple | trading-range low | 6.11 | 6.1094 | **reproduces** |
| multiple | trailing median | 17.85 | 17.8514 | **reproduces** |
| multiple | current multiple (0th pctile) | 5.65 | **5.3399** | **MOVED −0.31** |

**Every STATIC reference reproduces. Every LIVE one has moved.** Because none is stamped, you cannot
tell whether the three that moved were correct when struck — which is precisely P3 pt1's cost, now
demonstrated rather than argued.

**All five MARGIN references reproduce exactly.** So the 14% rests on sound inputs, and **§D is purely
a disclosure defect — not a decision-path finding.** The build was not stopped by the rider.

**Is SMPL among the revenue-alias-affected names? NO — measured directly rather than looked up.**

| ticker | `RevenueFromContractWithCustomer…Excluding` | `Revenues` | first-hit == longest? |
|---|---|---|---|
| **SMPL** | **8 FY (2019–2026)** | 3 FY (2018–2020) | **YES — not exposed** |
| **BRBR** | **1 FY (2026 only)** | **7 FY (2020–2026)** | **NO — exposed** |

SMPL's longest-coverage tag is also the first alias, so first-hit-wins and longest-coverage agree and
the margin anchor is unaffected. `_total_revenue_series` also returns `conflicts: []`.

**BUT BRBR IS THE WERN SHAPE, and BRBR is now the cohort partner.** Its ASC-606 tag holds **one**
fiscal year while `Revenues` holds seven. `midcycle` selects longest-coverage, so BRBR's committed
anchor is correct (`OperatingIncomeLoss / Revenues`, median over 8 FY = 16.0404%). **The exposure is
the SHARED extractor**, which is still first-hit-wins and would read BRBR's revenue as a single year.
Recorded in STATE as a live item now that BRBR is on the critical path.

---

## 4. What Step 2 would look like, if the operator wants it at 6-of-9

Not built, per the stop condition. Stating the shape so the decision is a decision:

- **Six axes default** to their computed anchor with `source_ref` carried through; any deviation is
  an explicit adjustment carrying its reason, and a deviation without a reason is **refused**. That
  makes §D structurally impossible — 14% can only be written as *anchor 15.4481%, −1.45pp, reason
  stated*.
- **Three cells (revenue bear, revenue bull, multiple bull) are REQUIRED INPUTS with no proposal.**
  The writer refuses without them rather than defaulting.
- Also enforced, as briefed: `RefPoint.vintage` inherited on every emitted reference (which is what
  would have prevented this rider from being necessary); the recipe tier checked against the dossier
  hint with a **refusal on disagreement** — AORT already disagrees, so that guard has a live case on
  day one; and **refuse, never default, on a missing leg**.

**A 6-of-9 proposer does not invent anything** — it defaults what is derivable and refuses what is
not. Whether that clears the bar set by *"a proposer that invents a number is worse than a form"* is
the operator's call, not mine, which is why this stops here.
