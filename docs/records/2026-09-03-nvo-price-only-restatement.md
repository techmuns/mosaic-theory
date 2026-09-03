---
id:
status: recorded
date: 2026-09-03
prs: []
supersedes:
superseded-by:
---

# NVO restated price-only — and the asymmetry, not the IRR convention, is what disqualifies it

**Step 10 work on a basket name.** NVO is one of the 15 ratified in `glp1-drug-value-chain`, is
WATCHLIST rather than a position, and its underwrite lives **outside the repo**. The 21 Sep CMD is
the nearest dated catalyst.

**BOUNDARY, and it is the whole caveat.** The legs below are **operator-recalled and are NOT repo
artifacts** — there is no `scenarios/NVO.json`, no archive entry, and zero rows in
`data/snapshots/decision_ledger.jsonl`. Everything here is an internal-consistency check on those
figures, not a computation from the record. Nothing may be underwritten from it until the legs are
confirmed against the operator's own record. Currency DKK; horizon 31 Dec 2027; read 2026-09-03.

## The restatement

```
spot 300.85   base 354.10   bear 250.90
reward = 354.10 - 300.85 =  53.25
risk   = 300.85 - 250.90 =  49.95
ratio  =  53.25 / 49.95  =  1.0661x
```

| | value | vs 1.75 eligibility | vs 2.0 bar |
|---|---|---|---|
| **asymmetry, price-only** | **1.0661x** | **FAIL** | **FAIL** |
| **base IRR, price-only** | **12.70%** at 1.363y horizon (13.09% at the actual 1.325y to 2027-12-31) | ≥12% → `minimum_met` | <15% → not preferred |

The 1.0661x reproduces the recalled 1.07x exactly. The 12.70% reproduces at a 1.363-year horizon;
the calendar horizon from 2026-09-03 to 2027-12-31 is 1.325 years and gives 13.09%. The recalled
figure therefore implies a slightly earlier start date than today — worth resolving, but it does not
move any tier.

## The finding: no IRR convention rescues this name

**NVO fails the asymmetry line under BOTH conventions.** Price-only the ratio is 1.07x. Even the
recalled *total-return* figure of 1.66–1.70x is **below the 1.75 eligibility line**. The gate outcome
does not turn on the price-only/total-return question at all — the ratio disqualifies it either way,
and `IRR NEVER REPLACES ASYMMETRY` is the house rule (`vinci/scenarios.py`: *"a 40% IRR on a 1.2:1
spread is a levered bet, not an underwrite"*).

That reframes what looked like an IRR-convention problem. It is an **asymmetry** problem.

## And the total-return figures do not reconcile by dividends

A 1.66x ratio requires a base leg of **383.77** and a 1.70x requires **385.77** — that is **+29.7 to
+31.7 DKK**, roughly **10% of spot**, added to the base. NVO's dividend over ~1.36 years at a ~2–3%
yield is about **10 DKK**, which would give a base of ~364 and a ratio of **1.27x**, not 1.70x.

**So the total-return figures are not a dividend restatement of these legs.** They imply different
legs, a different spot, or a different bear — and until that is resolved, the two readings are not two
views of one underwrite. This is the first thing to check against the operator's record, ahead of the
CMD.

## What is needed to take this further

Confirmed from the operator's own record: bear/base EPS and multiples (or values per share), spot with
its as-of date and source, horizon, and the share basis. With those, the name runs through
`scenario-propose`/`scenario-create` on the sanctioned path and both readings can sit on one record —
price-only gated, total-return recorded beside it, per the standing convention (Ruling 4, 2026-08-21;
`docs/records/2026-09-02-irr-total-return-already-ruled.md`).
