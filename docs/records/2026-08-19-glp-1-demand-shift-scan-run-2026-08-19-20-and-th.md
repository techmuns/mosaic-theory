---
id: 
status: recorded
date: 2026-08-19
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**GLP-1 DEMAND-SHIFT SCAN — RUN 2026-08-19/20, AND THREE PROPERTIES IT EXPOSED.** The driver
shipped at #484 (both directions, zero tickers). Full scan: universe 1802 → **869 prefiltered →
869 assessed, 0 scan-errors → 77 surfaced → 18 driver-specific**.

**1 — THE SCAN UNDER-SURFACES DIVERSIFIED NAMES WITH SMALL EXPOSED SEGMENTS, and this is a
PROPERTY to state rather than a defect to find later.** POST is the specimen: in-universe at
$3.56bn, assessed, and surfaced **`indirect`** — not because it lacks exposure but because its
GRADE-DRIVING fact was not its driver-specific one. Its facts split three ways: `indirect` on RTE
cereal, `not-driver` on granola/peanut butter, and ONE `driver-specific` fact (Weetabix/Lacka
Foods protein). `grade_driving_fact` returns the highest-ranked SINGLE fact, so a conglomerate
with one exposed segment grades on its bulk. **Arguably CORRECT for a concentrated fund —
concentrated exposure is the point — but it means the scan answers "is this name a play" and NOT
"does this name have exposure", and those differ for every diversified holder.**

**2 — THE UNIVERSE BOUNDARY, AND GLANBIA IS NOT AN FPI PROBLEM.** The honest claim is *"no better
candidate among SEC FILERS under $10bn"*. Two of the operator's three named shelf competitors are
excluded by CONSTRUCTION, not judgment — and for DIFFERENT reasons:
  * **GLANBIA (Optimum Nutrition, Isopure, think!, SlimFast — the same shelf as Quest and Premier
    Protein) IS NOT IN EDGAR AT ALL.** No CIK in `company_tickers.json`; Euronext Dublin / LSE
    listed with no US listing, so no 20-F and no 6-K. **#485's FPI1–FPI5 gaps therefore DO NOT
    TOUCH IT** — closing all five reaches Novo Nordisk and AstraZeneca (SEC filers on 20-F/6-K)
    and leaves Glanbia exactly as unreachable. The THEME altitude cannot help either: the scan is
    an efts full-text search over SEC filings. **Reaching it needs a NON-EDGAR SOURCE — a
    different order of change from the nine gaps.**
  * **HERSHEY is in EDGAR (CIK 47111) and reachable.** The screen band does not bind FOLLOWED
    names — UBER at $139bn and V at $665bn are the existence proof — so the cap is a policy bound,
    not a data one. **But it is not a substitute for SMPL:** chocolate, sweets and salty snacks are
    all discretionary calories, and ONE Bars is its only benefiting line. **It is the POST shape at
    larger scale** — reachable, and a different thesis.

**3 — A FIX APPLIED AT ONE CALL SITE AND NOT ITS SIBLING, AND IT CHANGED THE ANSWER.** The
two-sided design was corrected in the DriverSpec prose and in the resolver (`provenance_tags_of`,
multi-match; `provenance_tag_of` delegates and takes [0] so the other three drivers are untouched)
— but `cli.py` had **TWO** tag print sites and only one was updated. The committed-capacity block
still called `_tag`, so **12 of the 18 driver-specific names printed under-tagged**, and the
reported conclusion — *"no benefiting-side name competes with SMPL"* — was FALSE: **SMPL's own
second tag and BJRI's were both hidden.** Corrected list: 23 names carry multiple tags fleet-wide;
SMPL and BJRI are `suppressed-volume+benefiting-nutrition`, HLF likewise at the quantified grade.
**Same shape as the contamination caught in `assumptions` and invisible in its sibling `facts`.
The sibling call site is the check that was missing, and this one moved a decision input.**

**RECORDED, NOT FIXED — the grade axis is noise for a demand-shift driver.**
`binding-contracts-with-terms` = **0** at full scale; **42 of 77** landed `committed-capacity-or-
capex`, a grade meaning *capex/MW toward the driver*, which a DEMAND shift cannot have. Only 6
reached `quantified-revenue`. The axis was built for a supply-side driver and carries this one
poorly. Whether grades can be per-driver is a DESIGN question with no decision behind it.

**RECORDED, NOT FIXED — the exclusion clause cannot fire from either end.** The taxonomy excludes
the incretin MANUFACTURERS (structurally absent: sub-$10bn universe) and the prescribing/telehealth
CHANNELS (present but DROPPED BY THE PREFILTER — TDOC was picked for the adversarial set and never
reached classification). **Keep the clause** — it documents intent and the universe bound may
change — **but a clean run is no evidence it works.** Clearest instance yet of a guard that cannot
fire.
