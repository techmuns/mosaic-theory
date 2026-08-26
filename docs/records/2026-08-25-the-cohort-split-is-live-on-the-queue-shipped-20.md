---
id: 
status: shipped
date: 2026-08-25
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**THE COHORT SPLIT IS LIVE ON THE QUEUE — SHIPPED 2026-08-25 (`feat/cohort-split-in-the-queue`),
INFORM-ONLY.** The `Idio (vs mkt)` column asserted a name fell for its own reasons; G2 strips
MARKET beta but not SECTOR, so for roughly one in five persistent decliners that assertion was
false. The cell now carries the split — `industry -37% → name -10%` — plus a plain-words call
(*name-specific* / *industry-wide* / *too close* / *too few peers*), inside the column that made the
claim. *(The `coh`/`own` abbreviations it first shipped with were the code's terms, not a reading;
translated at the surface in the same PR.)* **No 14th column**: the table already runs to 13 and overruns a 1280px laptop.

**IT NEVER RE-ORDERS ANYTHING, and that is measured rather than cautious.** Ranking by the residual
was pre-registered, tested over four snapshots and FALSIFIED (§ experiment record 2026-08-25). The
read is attached by the WRITER after `rank_candidates` returns, beside `sector`/`industry`/`context`
— proven end-to-end: a re-rank with the split attached leaves order and every score IDENTICAL, with
`cohort` the only differing field. Pinned by `test_attaching_the_split_changes_no_order_and_no_score`.

**THE CALL ABSTAINS ON TWO GUARDS, AND THE FIRST CUT'S SINGLE GUARD WAS UNSUPPORTED.** The
original rule made a call on any cohort of 6+ and abstained only inside a fixed 10-point band.
**Measured afterwards, the median of a 6-8 name cohort moves ±20 POINTS under resampling** —
double the band it was abstaining inside — so those calls were stable week to week (the same names
keep the same returns) and entirely arbitrary (dependent on whichever handful the screen admitted).
*A reliable measurement of an arbitrary quantity is the worst of both.*

Raising the peer floor is the obvious fix and is a **bad trade, measured**: at 15 peers only ONE of
the queue's top ten keeps a cohort. The rule now requires the margin to clear **both** (a) 10 points
— the TEMPORAL guard, from the four-snapshot stability curve — and (b) **the cohort's own median
uncertainty**, the exact distribution-free interval from binomial order statistics. That keeps six
of the top ten's seven cohort-having names, because a large margin clears even a loose cohort: the
rule calibrates itself instead of legislating a count. **`MIN_PEERS` is now DERIVED** (5 — where the
interval becomes bounded at all), not asserted. Live: 93 own · 26 cohort · 74 unresolved · 75
no-cohort.

**EXACT, NOT BOOTSTRAPPED, deliberately** — a seeded resample inside a committed artifact re-draws
every run. A MAD-based normal approximation was tried first and REJECTED: against the bootstrap its
per-cohort ratio ranged 0.06x–1.73x, so it would have waved calls through on wildly unstable medians.

**IS SIC TOO CRUDE? TESTED, AND NO — BUT ONLY AT THE FINE GRAIN.** Permutation test over the 1,755
screened names, each grouping against its OWN random null (200 regroupings at identical size
distribution): SIC **industry** eta-sq 0.151 vs null 95% ≤ 0.074 (excess **0.098**); SIC **sector**
0.060 vs ≤ 0.013 (excess 0.054); **2-digit SIC** 0.081 vs ≤ 0.045 (excess 0.055). So the shipped
grain carries nearly twice the signal of the coarser ones, and **widening to sector to fix the
"too few peers" gaps would halve it** — the opposite of the intuitive fix. *(A first pass over all
319 raw industry buckets read INSIDE the null; that was an artifact of 254 sub-6 buckets inflating
the null, and restricting to cohorts the code actually forms inverted it. Fine partitions explain
variance at random — always compare against a null with the same bucket-size distribution.)*

**FENCED LIKE THE LABELS.** `vinci.cohort` is sector-derived, so `vinci.rank`/`vinci.screens` may
not import it; the SCHEMA (`vinci/schemas/cohort.py`) is deliberately sector-free so
`RankedCandidate` can CARRY a read while the derivation stays outside. Both halves pinned by AST.

**INCIDENT → INVARIANT (shipped Y): `vinci rank` WAS WIPING THE STRUCTURAL FLAGS.** Found while
wiring this. #420 added `carry_forward_assessment` so a refresh could not un-sink a name an 8-K had
capped — but wired it into `run_weekly` ONLY. A hand-run `vinci rank` passed no flags and destroyed
all of them: on the committed queue a plain re-rank restored **58** structurally-disqualified names,
and **SOC — carrying a "going-concern / substantial doubt" 8-K, capped at 0.05 and sunk to rank
212 — came back at RANK 7.** The manual path is the one an operator reaches for precisely when
working the queue by hand. Now carries forward; `--structural` still overrides with a fresh scan.
Pinned by `test_the_rank_cli_carries_forward_the_structural_flags`.
