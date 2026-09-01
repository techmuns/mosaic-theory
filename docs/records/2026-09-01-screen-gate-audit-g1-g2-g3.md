---
id:
status: recorded
date: 2026-09-01
prs: []
supersedes:
superseded-by:
---

# The screen's three gates were measured separately, and G1's main intake is the universe's worst band

**RECORD-ONLY. Nothing promoted, no threshold moved, and no threshold may be set from any table
below** — that is the outcome-tuning this fund forbids. What these results legitimately do is
contradict two stated *premises*; see WHAT IT COSTS.

**Run 2026-08-13; recorded 2026-09-01** (the delay is itself recorded — the work sat on
`feat/dossier-evidence-line`, which was written against the pre-P1 STATE.md and became unmergeable
after the 2026-08-25 restructure; the branch is abandoned and its content lands here instead).
**Re-checked at recording time: the gates are UNCHANGED on main** — `drawdown_max -0.30`,
`drawdown_terminal_floor -0.85`, `idio_rel_max -0.15`, `multiple_floor_pctile 0.25`, and neither
`vinci/screens/screen2.py` nor the admission flow in `vinci/screens/run.py` was touched in the
intervening 103 commits. The audit therefore still describes the live screen.

## WHAT

Every number below is **forward 180d, sector-neutral on the MEDIAN**, over the whole liquid
universe (ADV ≥ $1M, ≥5 members/sector), across 30 as-of months from the backdated queues, with
**delisted names carried at −100%**.

**G1 (fall ≥30% off the 52w high, floored at −85%) admits the universe's worst band, and that
survives the full bar as a NEGATIVE.** Drawdown-bucketed:

| bucket | n | lift | win | shuffle | phases | |
|---|---|---|---|---|---|---|
| 0/−10% | 13,265 | +0.7 | 53% | 100% | mixed | mixed |
| −10/−20% | 10,859 | −0.3 | 49% | 82% | mixed | no |
| −20/−30% *(G1 rejects)* | 8,165 | −1.6 | 47% | 100% | all − | **survives, negative** |
| **−30/−50% *(admits)*** | **9,814** | **−2.3** | 47% | **100%** | **all −** | **SURVIVES, NEGATIVE** |
| −50/−70% *(admits)* | 4,266 | +3.3 | 54% | 100% | mixed | mixed |
| −70/−85% *(admits)* | 951 | +10.3 | 57% | 100% | mixed | mixed |
| worse than −85% *(rejects)* | 304 | +8.7 | 54% | 100% | all + | survives |

The −30/−50% band is **65% of everything G1 admits** (9,814 of 15,030) and is positive in only
**6 of 30 months**. The bad zone spans −20% to −50%: the −20/−30% band G1 already rejects is
negative too and also clears the bar.

**THE DEEP BUCKETS ARE NOT A FINDING — they are one episode.** −50/−70% and −70/−85% post large
lifts but **fail the phase test**, and the month table says why: their strength is concentrated in
**Mar–Aug 2025** (−50/−70%: +11.7 +23.6 +18.5 +13.6 +11.7 +14.0; −70/−85%: +31.8 +61.9 +51.5
+32.0 +12.1 +9.3), mixed-to-negative either side. **The worse-than−85% bucket "survives"
arithmetically and MUST NOT BE ACTED ON:** ~10 names/month, monthly medians spanning **−92.8 to
+164.8**, two-thirds of its entire lift is ONE month (drop 2025-06 and the lift falls **+8.7 →
+3.2** and the phase test fails), and its last four months are **−62.4, −21.9, −92.8, −34.0**.

**G2 (lag IWM by ≥15% over 180d) barely discriminates.** `beat IWM +0.8 · 0/−15% −0.2 ·
−15/−30% −1.1 · −30/−50% −0.7 · worse-than−50% −0.7`. Beating IWM differs from lagging it, but
**among laggards there is no dose-response** — all three admitted bands sit at −0.7 to −1.1.

**G3 is not functioning as a gate.** Census over 9,786 queue rows: **5,349 (55%) carry the literal
string `UNKNOWN`** — never valued, admitted anyway (the runner's own comment at
`vinci/screens/run.py` records 186 of 281 on the 2026-07-29 run; this is the multi-month version).
Only **542 rows (7%)** were valued AND at/below the floor, and those did **no better** — 47% win
vs 50% for the unvalued. The gate binds on 7% of the queue and carries no forward information
where it binds.

**THE FUNNEL COSTS AT EVERY STAGE:** whole liquid universe +0.0 → after G1 −0.2 → after G1+G2
−1.0 → **the actual queue −2.8**.

## WHY

Prompted by a cohort audit that kept pointing at the pool rather than the cohort. The queue's own
lag against its sectors was the thread: **−2.5 / −2.7 pts** at 120/180d, negative in **25 of 30
months** — real, consistent, and roughly what a deliberate falling-knife screen should cost. The
gates were then measured separately to find where it comes from.

**A CORRECTION TO A NUMBER THIS AUDIT ITSELF PRODUCED.** That lag was first reported as **−8.3 /
−11.2 pts**. It was an artifact: `sector_forward()` returns a **MEAN**, differenced against the
queue's **MEDIAN**; stock returns are right-skewed so the mean sits above the median by
construction. **The −11 figure must not be quoted.** Survivorship was ruled out separately — only
3–4 queue rows delist in the whole history, and carrying vs dropping them changes the lag by
<0.1 pt.

## HOW VERIFIED

The standing bar, identical to the panel and the issuance test: **≥99th percentile of a 300-draw
within-month shuffle null AND the same sign across four disjoint phase blocks.** Applied per
bucket, not just to the headline. G1 and G2 are pure price, so they were evaluated on the whole
liquid universe **including the names they reject** — which the queue by construction cannot show.
G3 needs a valuation history, so it was tested inside the queue via the `multiple_pctile` proxy.
**CORRECTED IN REVIEW (2026-09-01), and the correction narrows the limitation rather than removing it:** the gate's OWN outcome is not discarded — `vinci/screens/run.py` records `g3_multiple_floor` and `admitted` on every retained row's **`per_gate`** field, and four committed runs carry them over the full ~1,800-name population INCLUDING the G1/G2 rejects (`screen_runs/2026-07-29-03.jsonl`, `2026-08-12-01`, `2026-08-14-01`, `2026-08-24-01`). The real limit is HISTORY, not visibility: four point-in-time runs spanning 2026-07-29 to 2026-08-24 cannot carry a 30-month backdated forward test, so the proxy was still required for the table above — but **"the outcome is recorded nowhere" is false and must not be repeated.**

**Widening G1 downward to −20% was tested and REFUSED.** The `flat float + cash-burning` cohort was
rebuilt inside each drawdown band against **all liquid names in that band**, requiring EDGAR for
602 names the queue never fetched — **602/602 fetched, 100% coverage**, so this is not a
partial-data result:

| band | cohort n | /mo | lift | win | shuffle | phases | |
|---|---|---|---|---|---|---|---|
| −20/−30% *(the proposed addition)* | 229 | 7 | +2.7 | 52% | 80% | mixed | **FAILS** |
| −30/−50% *(admits today)* | 312 | 10 | +7.1 | 59% | 100% | same | survives |
| −50/−85% *(admits today)* | 183 | 7 | +28.0 | 65% | 100% | same | survives |

**Not a power problem** — 229 observations at the same monthly density as the bands where it works.

## WHAT IT COSTS / WHAT IS ACCEPTED

**NO THRESHOLD MAY BE SET FROM ANY TABLE ABOVE.** Choosing −50% because this data says so is
precisely the outcome-tuning the fund forbids. What these results legitimately do is **contradict
two stated PREMISES**:

- the code asserts a fall past −85% is *"the market pricing bankruptcy/zero … not a recoverable
  overshoot"* — those names did not behave that way, **though the one-month caveat above makes
  this the weaker of the two and it should not be leaned on**;
- the −30% entry assumes a 30% fall marks a recoverable overshoot — over 30 months that band
  behaves like ordinary drift-continuation.

Any new depth must be re-argued **from the thesis**, pre-registered, and validated forward.

**ONE DIRECTION IS NOW CLOSED on evidence rather than argument: widening G1 DOWNWARD is refused.**
The −50% and −85% edges remain open.

**THE TENSION THAT FORBIDS THE OBVIOUS FIX.** Tightening G1 to −50% would delete the band the
`flat float + cash-burning` cohort's edge lives in. Cohort vs its own pool, 180d: **SHALLOW
(−50 to −30%) raw +10.0, win 68%, 100th pct, all phases SAME → SURVIVES** (sector-neutral +9.4,
100th pct); **DEEP (≤−50%) raw +8.9, 73rd pct, MIXED → fails** (sector-neutral +6.1, 56th pct).
The reconciliation is coherent: in the DEEP band the pool already bounces on its own (+13.6 raw /
+2.0 sector-neutral) and the cohort adds nothing separable; in the SHALLOW band the pool drifts
down (−0.6 / −4.0) and the balance-sheet condition is what separates survivors. Read as **"the
shallow band needs a discriminator, the deep band does not"** — NOT as "raise G1 to −50%". DEEP is
also thinner (16–18 testable months, n=74–82 vs 25–27 months, n=117–126), so "fails" there is
partly untested, not disproven.

**THE TWO BAND VIEWS ARE DIFFERENT QUESTIONS AND BOTH STAND.** Cohort vs other QUEUE names answers
*"does this discriminate inside the funnel"*; cohort vs the WHOLE liquid universe answers *"is this
band worth being in at all"*. Neither licenses a threshold change, and the deep band's +28.0 rides
the same Mar–Aug 2025 episode (phase blocks +2.4 / +43.2 / +13.1 / +47.0).

## The cohort's own status (POST-HOC — not promotable)

`flat float + cash-burning` emerged from an **unregistered six-way split**. Its 265 qualifying rows
are only **70 distinct companies** (median 3 months each, max 12 — CLNE, KLC, NG, LGIH, ACHC).
One-observation-per-company, sunk INCLUDED: 180d **+13.4 lift, 65% win, 100th pct**; 120d +8.3,
57%, 98th. Sector-neutral it survives at **120d (100th pct)** and **misses at 180d (96th–98th)**.

**It is a DOWNSIDE filter, not an upside finder** — median winner +23.9 vs the pool's +21.2
(identical), median loser −19.2 vs −18.4 (identical), but names ending −30% or worse are **8–9% vs
the pool's 17%**, and the median worst-point-during-hold is **−13.5% vs −20.0%**. Mechanism is at
least coherent (a cash-burner that has not had to issue is not being forced to sell shares cheap
into weakness). **Only fresh pre-registered data can move it.** Sunk-INCLUDED vs sunk-EXCLUDED
differ by **3 companies**; that gap must not be read as a finding.

**ALSO TESTED AND DEAD:** adding "price above the 50d MA" to the cohort. It cuts 265 rows to 71,
drops testable months 29 → 10, and nothing survives; the surviving half is the one **below** the
50d. Above-the-50d **alone** is a clean null on 1,776 observations (49% win, fails the bar). This
is a static state filter at a fixed entry date and does **not** contradict the earlier R3
cost-of-waiting result, which moves the entry DATE.

## Method notes — three analysis errors made and caught inside this audit

Recorded so they are not repeated. **All three were caught by the number being physically
impossible or internally inconsistent, not by a test.**

1. Differencing a **MEAN** benchmark against a **MEDIAN** cell — three-quarters of a headline number.
2. `sector_forward()` returns **percent, not a fraction**; an extra `×100` produced −950-point "lifts".
3. An `UNKNOWN` sentinel is not caught by an empty-string check, which briefly reported 100%
   valuation coverage against the true 45%.

## Provenance

Scratchpad scripts `validate.py` / `sunk.py` / `ma50.py` / `payoff2.py` / `sector.py` / `fair.py` /
`gates.py` / `g1bar.py` / `tight.py` / `bands.py`. **NOT COMMITTED** — they reuse
`scripts/price_state_falsifier.py`'s `load_bars` / `load_sector_map` / `sector_forward` /
`ADV_FLOOR_BENCH` / `MIN_SECTOR_MEMBERS`, so every number above is re-derivable from the constants
stated here.
