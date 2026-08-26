---
id: 
status: recorded
date: 2026-08-21
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**A STORED DERIVATION OUTLIVES THE CODE THAT PRODUCED IT — THIRD INSTANCE (2026-08-21, review of
#488).** Recorded as a CLASS because the individual fixes keep landing while the shape recurs.

**THE DEFECT.** `pe_current_and_percentile` refuses a percentile when the filer rescaled per-share
figures — correctly, since split-adjusted prices over as-filed EPS divide one basis by the other.
Its own sentence says *"inside the window"*, and **the call passed the FULL annual history**, so a
rescaling that predates the trailing range refused a percentile it cannot touch. Declared-vs-
enforced, in a guard.

**MEASURED, NOT ESTIMATED.** Across all 16 committed companyfacts fixtures only TWO names carry any
basis change: **HLF** (full 2.0032 → windowed None — WRONGLY WITHDRAWN, its 2018 2:1 split sits
EIGHT YEARS before a window opening 2021-08-15) and **NFLX** (10.02 either way — a correct refusal,
its 10:1 is inside). **Exposure among committed dossiers: exactly one name.** The 1,802-name
universe is UNMEASURED — companyfacts for every name is not held locally, and the fixtures cover
the dossier fleet only.

**AND I RATIFIED IT BEFORE THE REVIEW CAUGHT IT.** Seeing the detector fire on HLF, I verified the
split from the filing (8-K 0001193125-18-136523, "(5) Effect a two-for-one stock split", 73,825,918
for) and added HLF to `SPLIT_NAMES` — **the allowlist whose own test exists to catch exactly this
collateral damage**. The split is real; its LOCATION is what mattered, and I checked the wrong
property. `SPLIT_NAMES` now means "rescaled INSIDE the window", never "has ever split".

**THE CLASS, AND WHY THE CODE FIX DOES NOT CLOSE THE ARTIFACT.** `valuation.pe_percentile_5y` reads
`f.pe_pctile_vs_history` from the **screen data-record**, which is SERIALIZED AT SCREEN TIME. So
fixing the computation corrects no name already screened: HLF's dossier still carries the false
note *"a share-basis change falls inside the window"* after a full re-assembly, because assembly
reads the persisted record rather than recomputing. **`vinci screen` has no per-ticker option** —
it is the whole-universe weekly job — so the artifact closes on the next screen run, not here.
**THE ARTIFACT WAS THEREFORE HELD OUT OF #488**: shipping it would publish a known-false claim on
the decision surface, and the code fixes stand on their own.

**THIS IS THE THIRD OF THE SHAPE, and the other two are already in this file:** the SEAL MANIFEST
holding a predecessor's hash after a supersede, and `extraction_version` not restamping on refresh.
**A derived value written once and read forever is invisible to the fix that corrects its
producer.** The general remedy is not obvious — recomputing on read costs the reproducibility the
stored record exists for — so this is recorded as a CLASS to reason about, not a build.

**THE OTHER SEVEN REVIEW FINDINGS, all applied:** multi-tag made OPT-IN per spec
(`DriverSpec.multi_tag`, default False) — unconditional multi-match put a HEADWIND truckload name
in the TAILWIND bucket (`"less-than-truckload carrier"` → `('ltl','asset-based-tl')`) and made
nearly every AI-datacenter name read as colocation, since its prefilter guarantees "data center"
appears; the uncorrected-comps reason now NAMES WHICH CAUSE applies (the coverage guard added a
second `None` path on which the store DOES carry the bar — HLF holds 12.45 on 2025-12-03 and its
own pin asserts it, while the page printed "no bar at that panel's printed close");
`_COVERAGE_GAP_DAYS` no longer claims to be an absolute calendar bound (Sandy 2012 closed the NYSE
Mon–Tue, a FIVE-day gap — the error direction is safe, the claim was overstated); the per-tag
header says so; the dead `_tag` helper is gone; a superseded comment removed.

**TWO PINS ADDED WHERE THE DEFECTS LIVED, both mutation-verified.** A STRUCTURAL pin that both CLI
print sites resolve through ONE gated helper — the sibling-call-site defect that made 12 of 18
names print under-tagged and produced a FALSE conclusion. And a CALL-SITE pin for the windowed
split check: **un-windowing leaves the existing fleet test green**, because that test windows its
own points and so guards the FUNCTION while the defect was at the CALL SITE. Pin-the-artifact-not-
the-helper, in the pin written to catch it.

**AND THE WINDOW ITSELF WAS ONE REACH-BACK TOO NARROW (review of #490, applied on the same
branch).** The corrected call windowed the split check on the TRAILING RANGE — but the range does
not read EPS points dated inside it. Each bar reads `annual_eps_as_of(bar_date)`, which reaches
back up to `MAX_EPS_AGE_DAYS` (470) past a period end, so the periods that can FEED an observation
start at `window − 470`, not at `window`. DEMONSTRATED on a synthetic whose shape is ordinary: a
2:1 split whose 10-K restates FY2020 and FY2021 under a window opening 2021-08-15 leaves FY2021 as
the only restated period inside the range — ONE agreeing factor, below `_SPLIT_MIN_PERIODS` — so
the refusal never fires while every bar before the restatement filing still divides a split-
adjusted price by an as-filed EPS (4.40, not 2.20). A published percentile built across two bases,
which is the ORIGINAL defect, re-entered through the fix for its over-firing. `_split_start` is now
`_PE_WINDOW_DAYS + MAX_EPS_AGE_DAYS`; re-measured on all 16 committed fixtures, HLF still returns
None and NFLX still returns 10.02, so the #488 correction is untouched and only its boundary moved.
Pinned with a mutation-verified negative (revert the reach-back → the new pin alone reddens).
**THE SHAPE: a window that names a RANGE OF OBSERVATIONS is not the window of the INPUTS those
observations are built from** — whenever a lookup reaches back, the guard on its inputs must reach
back with it.

**AND THE REFUSAL REASON NAMED TWO CAUSES WHERE FOUR EXIST (same review).** `_uncorrected_reason`
was given the coverage cause and the no-bar cause, but `assemble.py` never calls `date_of_close` AT
ALL unless both the export stamp and the panel's printed close decode (the two `None` guards from
the review of #469). On either, the store is never consulted — and the page still printed "the
store carries no bar at that panel's printed close" for a panel that prints no close. Same
wrong-cause defect, one branch further out; each suppressing guard now states itself.

**THE PRE-ASSEMBLY SET — the plan itself, recorded here because it lived only in CHAT until
2026-08-17 (an OPERATOR-ACTION RULE slip: chat is not a ledger, and the set was already three PRs
old before it reached STATE).** Agreed after the operator's push-back that a full fleet assembly
per fix is wasteful — validate on 1–2 names, batch the fixes, assemble ONCE:
- **PR-1 — KD event coverage.** MERGED #458.
- **PR-2 — the `(latest)` family / Multiples vintage.** MERGED #459 (and it absorbed the band
  backward-fill, same root cause).
- **PR-3 — as-of bounding.** **RE-SCOPED 2026-08-16 on measurement, NOT dropped.** The ~12-field
  sweep this set was sized against is a 2026-07-29 figure; against the current as-of the live leak
  is MVST's CIQ panel (8 fields, 1 day) and VRRM's future-dated share count. Build against those,
  not against the July number. Still the highest-stakes class in the queue — the fund's edge is
  FORWARD-validated, so lookahead is the one defect that can invalidate the track record itself.
- **PR-4 — the capital-allocation render gate.** **DROPPED 2026-08-16, measured:** the whole
  section renders only inside `financialSnapshot()`, but **all 14 committed dossiers carry a
  financial summary**, so the gate hides nothing from anyone today. It is a guard against a name
  not in the universe. Re-open if a name ever assembles without a financial summary.
**THE ORDERING LESSON.** PRs 1–2 were recurrence guards for shapes the corpus does not contain
(76/76 metric-series already dated and ascending). **PR-2 ALONE consumed ~1.7M review tokens across
two `/code-review` rounds** — and earned them: round 2 caught a fatal defect in round 1's own fix,
where a single blank pad column disabled the sort and published the OLDEST close under a confident
ISO date. The deeper cost is structural, though: when a guard targets a shape the corpus does not
contain, neither the build nor the review can be settled by looking at the data, so review reasons
hypothetically — and hypothetical space is unbounded. Each fix adds new hypothetical surface and the
next pass finds more. **That is the fix→review→fix loop, and it is a property of SPECULATIVE
TARGETS, not of the reviewer.** The artifact pass below is backed by a defect a reader meets TODAY.
**Observed defects outrank latent guards in the queue order** — the correction this set earned.
