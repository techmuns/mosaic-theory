---
id:
status: recorded
date: 2026-09-02
prs: []
supersedes:
superseded-by:
---

# The IRR "total-return fix" is already ruled — closed without a code change

**WHAT.** An "IRR total-return fix" was raised as the top of the desk queue, described as a defect
currently inverting a verdict. It is **not a defect**. `docs/records/2026-08-21-tiered-gates-…md`
**Ruling 4** (operator-ratified 2026-08-21) settled it:

> **THE IRR STAYS PRICE-ONLY**, convention stamped on the record ("price-only — excludes dividends;
> conservative for dividend payers"). *A dividend forecast is an assumption, and assumptions are
> analyst-stated.*

**Closed as ALREADY-RULED, not as done.** No code changed. `IRR_CONVENTION`, `annualised_irr` and
`base_irr` are untouched and correct as they stand.

**WHY IT LOOKED LIKE A BUG.** NVO's underwrite was carried at **15.45% / 1.66x, computed
total-return**, against a gate that is price-only. The mismatch is real but it is not the code's: a
total-return restatement is **something the analyst does**, not something the gate does. The
resolution is procedural — run the name **price-only**, record **both** figures, and let the gate
apply the price-only one.

**SCOPE OF RULING 4, worth stating since the two get conflated.** Ruling 4's objection is to a
dividend **forecast**. Using **declared/trailing** dividends would be a fact rather than a forecast,
so it is a *different* change that Ruling 4 does not directly cover. Neither change is being made.
Recorded so the distinction does not have to be re-derived next time.

## The reason to leave it alone while a name is pending

**GOOGL is committed at IRR 14.89% against a 15% floor** — a gap of **0.11pp**. Any dividend
inclusion above roughly a 0.11% yield flips its IRR test from FAIL to PASS. Its overall gate still
fails on asymmetry (1.692x vs the 2.0x bar), so **no position changes** — but the fund's first
confirmed position carries a recorded FAIL on precisely the test that was proposed for change.

That is the argument, and it is the repo's own standard rather than a preference. `IRR_FLOOR`'s
docstring: *"a per-name floor would be the easiest possible place to manufacture a pass. NOT tuned on
outcomes."* The tiered-gates record: *"the thresholds are the GOOGL memo's pre-existing hurdles, set
before any name was pending on them — GOOGL itself FAILED its own 1.75x. Never outcome-tuned."*

**Changing a return convention while a name is pending on it, in the direction that flips it to pass,
is that shape** — even when the intent is unrelated. Ruling 4 stands, and the case for leaving it
alone is stronger while NVO is on the watchlist than it was when the ruling was made.

## What is NOT established here

**NVO is WATCHLIST, not a position** — pending the 21 Sep CMD, which is why no scenario record and no
ledger row exist for it. The figures quoted above (limit DKK 297 preferred / 303–304 target, spot
300.85, base 354.1, bear 250.9, horizon 31 Dec 2027, price-only 12.7% / 1.07x, total-return 15.5% /
1.70x) are **recalled from a prior session and are not repo artifacts**. They must be confirmed
against the operator's own record before anything is computed from them. Nothing in this record
depends on them.
