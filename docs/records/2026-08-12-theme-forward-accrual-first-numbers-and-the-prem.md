---
id: 
status: recorded
date: 2026-08-12
prs: [411]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**THEME FORWARD ACCRUAL — FIRST NUMBERS, AND THE PREMISE THAT WAS WRONG (2026-08-12, PR #411).**
A plan item asserted the theme ratification ledger "has never been written once", inferred from
`ratifiedCount: 0` across all three frontend mirrors. **That inference was wrong, and the reasoning
is worth keeping:** `ratifiedCount: 0` is the documented EMPTY-BUY reality (every committed name
PASSED, zero RATIFIED), not an unexercised path. All three themes DID freeze through
`append_record` → `freeze_baskets` → `measure_hold_none` — the mirrors carry `undefinedMeasures`,
cohort splits and honesty labels that only that path emits. The ledger and baskets are git-ignored
BY DESIGN (`.gitignore`: "derived, LOCAL-only … never committed").
**THE REAL GAP, which the wrong premise was pointing at from the side:** because those inputs are
local-only they were gone, so the forward measurement — the entire point of Stage 4, a number that
accrues over CALENDAR TIME — **could not be recomputed on any machine that did not run the freeze.**
Two themes passed their 30-day horizon in early August with their committed diagnostics still
reading `0 days forward from freeze`. Closed by `baskets_from_mirror` + `themes-forward
--from-mirror`, which rebuilds the baskets from the one durable artifact. **The ledger stays
un-committed — that remains the operator's call**, and the tension is real: the mirror is now
load-bearing for measurement, and nothing pins it against the ledger it was derived from.
**FIRST MEASURED READS (as-of 2026-08-11, 30d horizon, Polygon EOD, benchmark IWM):**
- **ai-datacenter** (frozen 07-02, 56 names): NAIVE-56 **−11.1%** raw, **−8.9%** vs IWM →
  declining to buy the tier was VINDICATED in this window. Exposure-carry divergence **−2.4%**
  (5 genuine-exposure −11.1% vs 51 other-PASSED −8.7%) — the exposure grade carried NO positive
  forward information here; it pointed slightly the wrong way.
- **defense-demand-shift** (frozen 07-03, 108 names): NAIVE-108 **−7.0%** raw, **−4.9%** vs IWM.
  Exposure-carry divergence **−1.0%**. Category split runs from `counter-uas` −0.2% and
  `munitions-scale` +0.3% to `unspecified` −9.5%.
- **truckload-supply-purge** (frozen 07-14): 30d horizon NOT reached at 29 days → every diagnostic
  `pending`, n=0. Correct, and kept as a negative pin.
**READ THESE AS THE HARNESS LABELS THEM, NOT AS AN EDGE RESULT.** Both diagnostics are
BETA-CONFOUNDED, the BUY leg does not exist so every RATIFIED-dependent spread is UNDEFINED, and one
30-day window on two drivers is far under the a-priori power floor (8 theme-quarters, 4 drivers).
The exposure-carry sign is the one genuinely informative datum, and it is NEGATIVE on both drivers
— worth watching, not concluding from.
**A MIRROR CARRIES NO REGISTRY KEY, so nothing binds a mirror file to a driver (review finding on
#412).** `ai-datacenter`'s mirror `driver` field reads **"AI-datacenter value chain"** — a human
label, not the key — and `defense`'s slug is `defense` against the registry key
`defense-demand-shift`. Two consequences: (a) taking the mirror's field as identity made ONE report
name two drivers (the CLI header printed the key, every confound string printed the label), now
fixed by making the caller's registry key authoritative; (b) **`--from-mirror <wrong file> --driver
<name>` cannot be caught by any machine check** — the CLI echoes the mirror's own slug/driver on
line two and asks the operator to confirm, which is mitigation, not a guard.
**~~CLOSING IT MEANS THE MIRROR CARRYING ITS REGISTRY KEY~~ — CLOSED 2026-08-12, THE OTHER WAY
ROUND.** The binding lives in the REGISTRY as `DriverSpec.mirror_slug`, not in the mirrors, for two
reasons: the three frozen `themes/*.json` are byte-identical thereafter by rule (RUNBOOKS §e), and a
driver's identity is the registry's business anyway. `baskets_from_mirror` now refuses a mismatch
before anything is measured — `--from-mirror frontend/themes/defense.json --driver ai-datacenter`
printed an AI-datacenter header over 108 DEFENSE names and now says so and stops. The check reads
the mirror's `slug` FIELD, not its filename, so a renamed file still binds correctly, and the three
bindings are pinned to exist, to point at a real file whose slug matches, and to be INJECTIVE.
**THE FIELD IS OPTIONAL AND ITS DEFAULT IS THE STRICT CASE.** Required looked stricter and was wrong
about the domain — the suite said so within a minute: `TOY_SPEC` in `test_themes_exposure.py` is a
synthetic driver proving the classifier is driver-agnostic, and a real driver exists before its
theme page is built. So an UNDECLARED binding cannot be verified and is REFUSED, rather than a
missing field failing at import for specs that will never have a mirror.
