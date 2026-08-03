# Is BRBR the cohort partner? — a read

**Report only. No assembly, no build, no name recommended.** Everything below is measured off the
committed artifacts and cached EDGAR facts.

---

## 0. Correlated-shock RISK on the sourcing route — a hypothesis, and the check that tests it

**Stated as a risk, not a proved property** *(corrected on review; the first cut said "by
construction")*.

**What the selection rule actually establishes:** the screen establishes that each constituent
independently passed a **drawdown-based gate** (`G1_drawdown` PASS, ≤ −30% from the 52w high), and
the cluster establishes **business similarity** — residualized co-movement over a 365-day window
(`residual_basis: market+sector+size+vol`, with breadth, coherence and persistence tests).

**What it does NOT establish: that those drawdowns share ONE causal event.** Residual co-movement
over a year is equally consistent with a persistent correlated *factor* (a metal price, a rate
regime) carrying no single event, or with **several idiosyncratic events that happen to fall inside
the same year and the same business grouping**. Presenting the correlated-shock reading as proved by
the selection rule would discount the whole sourcing route on an inference the rule cannot support.

**So the requirement: before any cohort is called common-shock, run an EVENT/DATE ALIGNMENT CHECK.**
The data is already on disk — each candidate record carries a typed, dated `trigger_reason`
(e.g. *"earnings_gap_down on 2026-02-05 + drawdown −71.7% ≤ −30%"*).

### The check, run over the six multi-candidate themes

| theme | distinct trigger dates | span | reading |
|---|---:|---|---|
| **T002** gold & silver (16) | **1** — 2026-01-30 for **15 of 16** | — | **aligned** (1 undated price-drop trigger) |
| **T023** quantum (3) | **1** — 2026-02-05 for all three | — | **aligned** |
| **T022** cannabis (2) | **1** — 2026-04-23 for both | — | **aligned** |
| **T008** uranium (5) | **3** — 02-04, 03-16, 06-05 | **4 months** | **scattered** (+1 undated) |
| **T037** solar (3) | **3** — 02-27, 04-16, 04-29 | **2 months** | **scattered** |
| **T014** coal (3) | **1** dated; 2 are undated price-drop triggers | — | **untestable** |

**Three of six align on a single date; two scatter; one cannot be tested.** So the correlated-shock
reading is **real for some themes and false for others** — which is exactly why it has to be checked
per cohort rather than assumed from the route.

**And it lands opposite to the intuition about T002.** The mixed-taxonomy cluster — two sectors, five
SICs, coherence 0.385, the one whose own `shared_note` warns it may be a driver-less momentum
bucket — is the **most** date-aligned of the six, at 15 of 16 names on one day. Loose taxonomy did
not predict scattered events.

**One caveat the check cannot resolve, and it should not be read past.** A shared *date* is evidence
of a common *move*. The label `earnings_gap_down` attributing that move to **earnings** for fifteen
different issuers on a single day is **not** established by this field, and is implausible on its
face — confirming it would need the per-name filing dates. **Read the date alignment; do not read the
attribution.**

**BRBR does not come from this route at all** — it comes from the existing book, and its relation to
SMPL is product-market (protein snacking) rather than a shared drawdown, so the correlated-shock
question does not arise for it.

---

## 1. BRBR — fiscal year-end, verified rather than taken on trust

Derived from **annual duration facts** (`fp: FY`, `start`→`end` spanning 350–380 days), the method
that survives the cover-page trap.

| name | FY-end | calendar type | evidence |
|---|---|---|---|
| **BRBR** | **Sep-30** | **fixed month-end** | a single value across 1,325 annual duration facts |
| **SMPL** | **late August** | **52/53-week (drifts)** | Aug-31 · Aug-29 · Aug-25 · Aug-28 · Aug-27 across years |
| **CPB** | **late Jul / early Aug** | **52/53-week (drifts)** | Jul-31 · Jul-28 · Aug-02 · Jul-29 · Jul-30 · Aug-01 |

**Your reading is confirmed: BellRing September against SMPL's late August.** SMPL's FY2025 ended
**Aug-30-2025**, so the offset to BRBR's Sep-30 is **≈31 days** — with the wrinkle that SMPL's end
date *moves* year to year while BRBR's does not, so the offset is ~30–36 days rather than a constant.

**One correction to the framing.** This is **not** tighter than anything in the theme read: **T014,
T023 and T037 are internally aligned at zero offset** (all members Dec-31). What is true is narrower
and still useful — **BRBR/SMPL is the tightest alignment among *reachable* pairings**, since those
three themes are blocked on bundles, scenario records and EDGAR anchors regardless of their calendars.

*(For the record, CPB sits ≈27 days on the other side of SMPL — marginally closer than BRBR, in the
opposite direction.)*

---

## 2. What BRBR's scenario record would need

**Every mechanical input already exists in the committed dossier.** `ScenarioRecord.facts` wants
`d_and_a`, `net_debt`, `diluted_shares`:

| fact | BRBR | source | status |
|---|---:|---|---|
| `d_and_a` | **18.6 $M** | EDGAR `DepreciationDepletionAndAmortization` (combined, FY2025) | **HAVE** |
| `net_debt` | **1,181.9 $M** | EDGAR: debt 1,185 + finance leases 0 + operating leases 30 − cash 33 | **HAVE** |
| `diluted_shares` | **116,277,850** | `stock_info.shares_out` | **HAVE** |
| *(context)* `ltm_revenue` | 2,331.7 $M | committed `financial_summary.annual` (LTM) | HAVE |
| *(context)* anchor `margin` | 16.0404% | EDGAR `OperatingIncomeLoss / Revenues`, median over 8 FY | HAVE |
| *(context)* anchor `multiple` | 19.7614x | `valuation.own_history.median`, 27 quarters | HAVE |

**What the ANALYST must supply — and it is the only real work:**

- **`scenarios`: bear · base · bull**, each requiring `revenue`, `margin`, `multiple` and a
  **non-blank `reason`** (schema-enforced: *"refusing to record a scenario assumption with no stated
  reason"*), plus **`bear_basis`** on the bear leg (one of own-history / bear-state-comps /
  peer-reference / analyst) and **`margin_basis`** (EBIT | EBITDA).
- **`assumptions`**: a per-axis `AssumptionDerivation` (revenue / margin / multiple) with a
  **non-blank `method`** sentence and its reference frame. Ratification (`ratified_by`, `ratified`)
  is a second, separate human act — *"the machine never sets them."*
- **Administrative**: `spot`, `spot_source`, `underwrite_date`, `analyst`.

**Not required on an R1 record:** `tier`, `survival_input`, and per-leg `years_to_terminal` are all
R2-only and stay `None` — so BRBR skips the survival-gate machinery entirely.

---

## 3. Would BRBR's `consensus_levels` support a decomposition?

**Yes — and the pipeline has already decided so.** BRBR's committed `ev_gap` reads:

```
form:   "three-ratio"
status: "not-computed"
reason: "no scenario record for this name — the route is known, the gap is not"
```

**The route is already resolved to the full three-ratio decomposition. The single missing input is
the scenario record, and the artifact says so in its own words.**

| | SMPL | BRBR |
|---|---|---|
| Revenue coverage | 9 / 11 | **13 / 13** |
| Revenue dispersion | 0.89% | **2.07%** |
| EBITDA coverage | 10 / 10 | **12 / 12** |
| EBITDA dispersion | 4.67% | **6.58%** |
| caution carried | no | **no** |
| **anchor FY** | **2026** | **2026** |
| **adjacent FY** | **2027** | **2027** |
| forward span | FY2026 → FY2033 | FY2026 → FY2030 |

Both legs sit far above `CAUTION_ESTIMATES` (5) and far below `MAX_DISPERSION` (50%). **BRBR's
coverage is better than SMPL's on both legs**; SMPL's forward span runs three years longer, though
the tail years are 1–2 estimates each and neither name's anchor depends on them.

**They share the anchor year (FY2026) and the adjacent year (FY2027)** — so a cross-sectional
comparison of the two decompositions is on one horizon, with no year-alignment adjustment needed.

---

## 4. R1 or R2?

**R1 fits.** BRBR's anchor carries `recipe_hint: R1_midcycle_margin_evebitda` with
`applicable: True`, and its gap is routed `three-ratio` — **so the gap DECOMPOSES**, it does not fall
back to price-implied-only.

**A correction to the comparison, and it runs your way.** The R2 discriminator in a committed record
is **`tier`** (schema: *"(R2) TIER … None on R1 records"*). Reading the seven committed records:

| record | `tier` | ⇒ |
|---|---|---|
| **AORT** | **B** | R2 |
| **MVST** | **B** | R2 |
| **NCNO** | **A** | R2 |
| EPAM · IT · SMPL · WERN | None | R1 |

**So AORT, MVST and NCNO are exactly the three R2 records — your framing was right.** What the read
adds is a discrepancy worth knowing: **AORT's DOSSIER hint says `R1_midcycle_margin_evebitda`,
`applicable: True`, while AORT's RECORD is R2 (`tier: B`).** The hint is a dossier-side suggestion
and the record governs; they disagree for this one name.

**And BRBR is not alone in being one underwrite away.** Three committed dossiers carry
`form: three-ratio` with `status: not-computed` and the identical reason:

| name | Revenue | EBITDA | caution |
|---|---|---|---|
| **BRBR** | 13/13, disp 2.07% | 12/12, disp 6.58% | none |
| **VRRM** | 8/8, disp 1.43% | 6/6, disp 1.00% | none |
| **CNXC** | 3/3, disp 0.75% | 3/3, disp 4.27% | **thin, caution carried on both legs** |

*(VITL routes `two-ratio` — its EBITDA dispersion is 263.7%, past the 50% ceiling, so its margin
ratio is suppressed. FUBO has no recipe at all.)*

---

## 5. CPB — the fallback, briefly

- **Fiscal year-end:** 52/53-week, ending **late July / early August** (Jul-28 → Aug-02). CIK
  `0000016732`, Nasdaq.
- **Bundle:** **kind-for-kind identical to BRBR's** — comps, Financials Annual, Financials Quarterly,
  Estimates Report, Customers, Suppliers, Key Developments, Public Company Profile, and **two
  earnings-call transcripts** (Q2 FY2026 Mar-11, Q3 FY2026 Jun-08). Nothing BRBR has is missing.
- **Can it assemble?** Its bundle is complete against the same kinds as a name that demonstrably
  assembled. **That is a bundle-completeness inference, not a demonstration** — no assembly was run,
  so nothing here proves the extractors succeed on Campbell's exports.
- **Everything downstream is unknown until it assembles:** no dossier means no `recipe_hint`, no
  `consensus_levels`, no anchor block, no route. Against BRBR — which needs *only* an analyst
  record — CPB needs an assembly first and then the same record.

---

## 6. Are EPAM and IT already a cohort?

**Mechanically, yes — both are complete and comparable today, at zero further work.**

| | EPAM | IT |
|---|---:|---:|
| total gap | **2.0196** | **1.6460** |
| revenue ratio | 1.0012 | 1.0002 |
| margin ratio | 0.7637 | 0.8744 |
| multiple ratio | **2.6413** | **1.8820** |
| shape (anchor / adjacent) | multiple-dominant / multiple-dominant, **agree** | multiple-dominant / multiple-dominant, **agree** |
| anchor FY | **2026** | **2026** |

Same anchor year, same shape, both decomposed. **Both revenue ratios are ~1.00** — our top line and
the street's agree almost exactly on each — so on both names the disagreement is the multiple, with
margin doing more secondary work on EPAM (0.76) than on IT (0.87).

**Peer-set overlap — the answer to "enough to treat as one":**

- Raw overlap is 6 of 12 each, but that **counts each other and the synthetic `Peer median` row.**
- **Genuine third-party overlap is three names: CTSH, DOX, EFOR.**
- EPAM's non-shared peers are IT-services and engineering: ACN, GLOB, DXC, SOP, and two
  non-US-ticker rows (`4307`, `301236`).
- IT's non-shared peers are information services and ratings: EFX, FDS, MCO, SPGI, TRU, VRSK.
- **Each name appears in the other's peer set.**

So the sets **intersect at the IT-services tail of Gartner's comp set** and diverge everywhere else:
roughly one third shared, two thirds pointing at different cross-sections — engineering hours on one
side, subscription research and ratings on the other. **They are a usable pair on horizon, shape and
completeness, and a weak one on comparability** — which is the trade the operator already named.
