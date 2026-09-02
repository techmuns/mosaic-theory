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

## The reason to leave it alone — evidenced at the date the ruling was made

**When Ruling 4 was made on 2026-08-21, GOOGL's then-live underwrite was IRR 14.89% against the 15%
floor — 0.11pp short — and reward/risk 1.692x against the 2.0x bar.** Any dividend inclusion above
roughly a 0.11% yield would have flipped its IRR test from FAIL to PASS.

**The operator ruled price-only anyway, declining the change that would have rescued their own name.**
That is the face-validity evidence, and it is stronger than a present-tense argument: the convention
was fixed while the fund's own candidate was inside the margin the change would have closed.

The standard it satisfies is the repo's own. `IRR_FLOOR`'s docstring: *"a per-name floor would be the
easiest possible place to manufacture a pass. NOT tuned on outcomes."* The tiered-gates record: *"the
thresholds are the GOOGL memo's pre-existing hurdles, set before any name was pending on them —
GOOGL itself FAILED its own 1.75x. Never outcome-tuned."*

**Changing a return convention while a name sits inside the margin it would close is that shape** —
which is exactly the position the ruling was made from, and declined.

> **Those GOOGL figures are the ARCHIVE, and the first draft of this record stated them in the
> present tense.** `scenarios/archive/GOOGL-2026-08-17.json` carries 1.692x / 14.89% / gate FAIL /
> `pending_analyst`. The LIVE record `scenarios/GOOGL.json` was reissued at a verified spot by #567
> and carries **2.4299x / 17.11% / gate PASS / `confirmed`** at $339.35. **GOOGL passes the IRR test
> today.** The draft read a superseded archive as current — the same read-at-the-wrong-boundary
> error this session has now produced seven times. The argument survives and improves, because it
> belongs at the ruling's date rather than today's.
>
> **Where the stale figure came from, and it is still there:** STATE.md §5.0 row 9 cites
> `scenarios/GOOGL.json` by name while quoting the archive's numbers, and STATE.md:649 repeats them.
> #567 confirmed GOOGL **without touching STATE.md** — a merged build that changed reality without
> updating the snapshot. Flagged for the operator; not corrected here, since whether row 9 now closes
> is their call, not this record's.

## What is NOT established here

**NVO is WATCHLIST, not a position** — pending the 21 Sep CMD, which is why no scenario record and no
DECISION-ledger row exist for it. Precisely: no `scenarios/NVO.json`, no archive entry, zero rows in
`data/snapshots/decision_ledger.jsonl`. It is **not** absent from the repo, though — it carries a
`disposition: ratified` BUY row in `data/themes/ledgers/glp1-drug-value-chain.jsonl` (2026-09-01) on
a driver whose forward clock is running. "Not a position" holds; "no ledger row" holds only under the
decision-ledger reading, and is stated that way here rather than loosely. The figures quoted above (limit DKK 297 preferred / 303–304 target, spot
300.85, base 354.1, bear 250.9, horizon 31 Dec 2027, price-only 12.7% / 1.07x, total-return 15.5% /
1.70x) are **recalled from a prior session and are not repo artifacts**. They must be confirmed
against the operator's own record before anything is computed from them. Nothing in this record
depends on them.
