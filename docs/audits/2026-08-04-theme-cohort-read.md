# Which themes hold multiple candidates — a read, not a recommendation

**Sources, both already on disk — no new screen run.**
`data/snapshots/screen_runs/2026-07-29-*.jsonl` → `data/snapshots/candidate_records.jsonl` (**331 candidates**,
`screen_run_at 2026-07-29`) intersected with `data/snapshots/candidate_themes.jsonl` (**35 clusters**).
**Which names to underwrite is the operator's and the analyst's call. Nothing below recommends one.**

**VINTAGE GAP, stated up front because it bounds every count here.** The clusters carry
`window.reference_date = 2026-06-17` (365-day window, 252 trading days); the candidates are from the
**2026-07-29** screen. **The theme membership is six weeks older than the candidate set**, so a name
that became a candidate after 06-17 cannot appear in a cluster no matter how well it fits. Every
"themes with ≥2 candidates" figure is therefore a **floor**, not a census.
`RunManifest` is still unpopulated in production, so a fresh run would be unattributable — which is
why this is a read of what exists rather than a re-run.

---

## 1. Which themes contain two or more candidates

**Six of the 35 clusters, covering 32 of the 331 candidates.** The rest of the distribution:
**5 clusters hold exactly one** candidate and **24 hold none**.

| cluster | candidates / members | sector(s) | SICs | admissible | coherence |
|---|---:|---|---|---|---:|
| **T002** | **16** / 18 | Financials, Materials | 1000, 1040, 1400, 6199, 6795 | yes | 0.385 |
| **T008** | **5** / 6 | Materials | 1040, 1090, 1400 | yes | 0.530 |
| **T014** | **3** / 5 | Materials | 1220, 1221, 3312 | yes | 0.601 |
| **T023** | **3** / 4 | Technology | 7371, 7372, 7374 | yes | 0.658 |
| **T037** | **3** / 3 | Technology | 3674 | yes | 0.514 |
| **T022** | **2** / 4 | Health Care | 2833 | yes | 0.652 |

All six pass admissibility (breadth, coherence, persistence; no `fail_reasons`). **T002 is the loosest**
— coherence 0.385, spanning two sectors and five SICs, and its own `shared_note` says a
cross-taxonomy cluster needs the analyst to *name the driver, or reject it as a driver-less momentum
bucket*. That note is unresolved for T002.

---

## 2. The candidates, with band · G3 · gap · bundle

**G3 is `UNKNOWN` for all 32 — 100%.** Against a base rate of **85.2% UNKNOWN across all 331**
(282 UNKNOWN / 49 PASS), the multi-candidate themes are **worse than the population, not better**.
Bands across all 331: A 171 · B 82 · C 78.

**Total gap is computable for ZERO of the 32 — for two MECHANICAL reasons, neither of them G3.** The
total needs a **TEV** (struck from the CIQ comps panel, so it needs a bundle) and **our own base leg**
(a scenario record). The 32 have **none of either**: zero bundles, zero scenario records. `G3` is a
screening gate and is **not** an input to `build_ev_gap` — see §5. This is not a gap in the read; it
is the state of the record.

**CIQ bundles: 14 on disk — and it is not the eleven.** `data/manual/ciq/` holds AORT, BRBR, CNXC,
**CPB**, EPAM, FUBO, IT, MVST, NCNO, **PENG**, SMPL, VITL, VRRM, **WERN**. Three names —
**CPB, PENG, WERN** — carry bundles without a dossier. **The intersection with the 32 is empty.**

| cluster | ticker | band | G3 | total gap | CIQ bundle | annual form | FY-end | EDGAR anchor margin |
|---|---|---|---|---|---|---|---|---:|
| T002 | ASM | A | UNKNOWN | n/a | no | 20-F/40-F | Dec-31 | none — no reliable total-revenue tag |
| T002 | EGO | C | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T002 | BVN | C | UNKNOWN | n/a | no | 20-F | Dec-31 | none |
| T002 | NG | A | UNKNOWN | n/a | no | 10-K | **Nov-30** | none — no overlapping op-income years |
| T002 | SA | C | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T002 | EXK | A | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T002 | AG | A | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T002 | SVM | B | UNKNOWN | n/a | no | 40-F | **Mar-31** | none |
| T002 | FSM | C | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T002 | GAU | A | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T002 | BTG | B | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T002 | SII | C | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T002 | OR | C | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T002 | SKE | C | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T002 | EQX | A | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T002 | TFPM | C | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T008 | DNN | C | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T008 | UEC | A | UNKNOWN | n/a | no | 10-K | **Jul-31** | none — no overlapping op-income years |
| T008 | URG | B | UNKNOWN | n/a | no | 40-F + 10-K | Dec-31 | 0.99% over 5 FY |
| T008 | UUUU | A | UNKNOWN | n/a | no | 10-K | Dec-31 | −119.39% over 4 FY |
| T008 | NXE | C | UNKNOWN | n/a | no | 40-F | Dec-31 | none |
| T014 | BTU | B | UNKNOWN | n/a | no | 10-K | Dec-31 | 11.18% over 18 FY |
| T014 | AMR | B | UNKNOWN | n/a | no | 10-K | Dec-31 | 9.59% over 9 FY |
| T014 | CNR | C | UNKNOWN | n/a | no | 10-K | Dec-31 | 16.22% over 3 FY |
| T023 | QUBT | A | UNKNOWN | n/a | no | 10-K | Dec-31 | −7,330.45% over 3 FY |
| T023 | RGTI | A | UNKNOWN | n/a | no | 10-K | Dec-31 | −733.74% over 4 FY |
| T023 | QBTS | A | UNKNOWN | n/a | no | 10-K | Dec-31 | −724.60% over 6 FY |
| T037 | CSIQ | A | UNKNOWN | n/a | no | 20-F | Dec-31 | 5.36% over 10 FY |
| T037 | DQ | A | UNKNOWN | n/a | no | 20-F | Dec-31 | 26.92% over 17 FY |
| T037 | JKS | A | UNKNOWN | n/a | no | 20-F | Dec-31 | 2.58% over 9 FY |
| T022 | TLRY | A | UNKNOWN | n/a | no | 10-K | **May-31** | −51.62% over 8 FY |
| T022 | CGC | A | UNKNOWN | n/a | no | 40-F + 10-K | **Mar-31** | −214.17% over 9 FY |

*(G1_drawdown and G2_idiosyncratic are PASS for all 32; only G3 is open. Coverage on the candidate
`data_record` runs 12–16 fields present against 8–12 unknown, and `market_cap.coverage_status` is
`unknown` for every one of the 32 — "needs shares".)*

---

## 3. Fiscal year-ends — where a cross-sectional comparison would inherit a mismatch

**Mostly clean.** Dec-31 dominates; the exceptions are named because they are the ones that would
propagate into a cohort comparison.

- **T014, T023, T037 — all members share Dec-31.** No mismatch to inherit.
- **T008 — UEC ends Jul-31 against four Dec-31 mates: a five-month offset**, the largest inside any
  theme here. A cross-sectional read across this theme compares UEC's FY to periods its peers have
  not reported.
- **T022 — the only theme where NO two members share a year-end.** TLRY **May-31** vs CGC **Mar-31**,
  two months apart and neither on the calendar year.
- **T002 — 14 of 16 on Dec-31**, with NG at **Nov-30** (one month) and SVM at **Mar-31** (three months).

For scale against the existing book: SMPL ends **August**, EPAM **December**, CNXC **November**.

---

## 4. Two structural findings that bear on the pick

**(a) 20 of the 32 are foreign private issuers.** Only 12 file a 10-K — NG, UEC, URG, UUUU, BTU, AMR,
CNR, QUBT, RGTI, QBTS, TLRY, CGC. The other 20 file **20-F or 40-F only**. Every one is US-*listed*
(the `country` field reads US for all 32, which is listing venue, not domicile), so a country filter
on the candidate record does not surface this — the filing form does.

**(b) The EDGAR anchor path produces a margin for 13 of the 32.** Measured by running the production
derivation (`_total_revenue_series` → `margin_anchor`) over cached companyfacts, not inferred:

- **19 produce nothing** — 17 for *no reliable total-revenue tag* (the IFRS filers have no us-gaap
  total-revenue concept), 2 (NG, UEC) for *no overlapping operating-income years*.
- **All 16 of T002 produce nothing.** The largest multi-candidate theme yields zero anchors.
- Of the 13 that compute, **7 return a negative or near-zero median** (QUBT −7,330%, RGTI −734%,
  QBTS −725%, CGC −214%, UUUU −119%, TLRY −52%, URG +0.99%) — i.e. pre-revenue or structurally
  loss-making over the window, where a median operating margin is not an anchor so much as a
  statement that there is little revenue to take a margin on.
- **6 return a positive multi-year median**: BTU 11.18% (18 FY), AMR 9.59% (9 FY), CNR 16.22% (3 FY),
  CSIQ 5.36% (10 FY), DQ 26.92% (17 FY), JKS 2.58% (9 FY). *Listed as a measurement of what the
  pipeline can currently produce — not as a shortlist.*

---

## 5. What this says about the G3 backlog — and what G3 does NOT block

**The screening picture.** The parked screen path's valuation branch is **85.2% of all candidates
unvalued**, and that number is **not** diluted inside the multi-candidate themes — it is **100%**
there. As a *screening* matter the theme route does not sidestep G3; it runs straight into it.

**BUT G3 IS NOT AN INPUT TO THE GAP, and the first cut of this section said it was.**
*(Corrected on review.)* `build_ev_gap` takes `levels, leg, tev, net_debt, shares, tev_as_of,
consensus_as_of` — **no G3**, and the identifier `G3_multiple_floor` appears nowhere in
`vinci/dossier/ev_gap.py` or `vinci/dossier/assemble.py`. The function's own docstring is explicit
that even the *consensus* side is optional and decides only the decomposition: *"absent levels …
does NOT mean no total."* So `G3=UNKNOWN` does not prevent a gap from being computed. Saying it does
overstates what the code enforces, by promoting a policy gate into a mechanical one.

**The two mechanical prerequisites for a TOTAL gap, and both are absent for all 32:**

| prerequisite | supplied by | present for the 32 |
|---|---|---:|
| **TEV** (+ net debt, shares for the bridge) | the CIQ comps panel → needs a bundle | **0 / 32** |
| **our own base leg** | a scenario record | **0 / 32** |

Measured: the 32 intersect the 14 CIQ bundles in **nothing**, and intersect the **7** committed
scenario records (AORT, EPAM, IT, MVST, NCNO, SMPL, WERN) in **nothing**.

**So the honest statement of the blockers, separated by kind:**
- **Mechanical** — no TEV and no own leg. Either alone is sufficient to make the total gap
  uncomputable, and both are missing.
- **Policy / screening** — *do not advance an unresolved-G3 candidate*. That is a rule about which
  names should proceed, not about which numbers can be produced.
- **Depth** — for the **19 with no EDGAR anchor**, the R1 path does not reach them either, which is a
  third and separate constraint.

**A related measurement that falls out of the same read:** only **7 scenario records exist at all**,
against **14 CIQ bundles** — so even among names that already have a bundle, **7 of 14 have no own
leg**. Of the eleven dossiers, **six carry a scenario record** (AORT, EPAM, IT, MVST, NCNO, SMPL);
WERN carries one with a bundle but no dossier.
