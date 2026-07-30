# Correction — the SMPL basis reverse-solve was a fit, not a derivation

**2026-07-30.** Recorded because the memo carries the operator's figures, and the probe rule applies
to whoever wrote the probe.

## What was asserted

A reverse-solve offered as evidence that SMPL's engine converts operating margin to EBITDA before
applying the EV/EBITDA multiple:

```
1330 × 0.14 + 21.79 = 207.99
       × 12.5       = 2599.9
       − 326.8      = 2273.1
       ÷ 93.68M     = $24.26   against a recorded $24.24
```

The conclusion — the engine converts — is **correct**, and the code read confirms it
(`midcycle.scenario_value`: `oi = revenue × margin`, `ebitda = oi + d_and_a`, `ev = ebitda ×
multiple`).

## What was wrong

Two of the three inputs were not the record's:

| input | used in the solve | actual (`scenarios/SMPL.json`) |
|---|---|---|
| D&A | 21.79 | **21.431** |
| net debt | 326.8 | **324.582** |
| diluted shares | 93.68M | 93.677801M ✓ |

Run on the record's own facts the engine returns **$24.2406**, matching the stored
`result.per_scenario.base.value_per_share` to four decimals — bear `6.9540` and bull `40.2135`
likewise. The `$24.26 ≈ $24.24` near-match was two compensating input errors landing within two
cents of a figure that reproduces **exactly**.

## Why it is worth a note

A reverse-solve that lands close is the most persuasive possible form of a wrong measurement: the
closeness reads as confirmation. Here the true test was cheaper and available — recompute from the
record's own `facts` and compare to the stored `result`, which is exact rather than approximate.

Same rule as `docs/engineering.md` §*A probe must derive from the code, not restate it*: the record
already held the inputs, so fitting them was both more work and less evidence. **A derivation that
reproduces to the stored digit is a measurement; one that lands nearby is a fit.**

No committed number moves. The conclusion stands; only its support is corrected.
