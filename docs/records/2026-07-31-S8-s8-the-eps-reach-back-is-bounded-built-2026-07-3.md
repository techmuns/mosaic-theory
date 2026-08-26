---
id: S8
status: recorded
date: 2026-07-31
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S8. THE EPS REACH-BACK IS BOUNDED — built 2026-07-31, solo (guard).** `annual_eps_as_of` took
the latest POSITIVE annual figure with no age limit, so a name loss-making for years was valued on
pre-loss earnings — measured p90 **4.8 years**, max **16.6 years**.

**DERIVED FROM THE FILING CADENCE, not the population** (the population is a continuous tail with no
separation to read a bound off): **470d = 365** annual reporting period **+ 90** latest statutory
10-K deadline **+ 15** NT extension. Measured on periods ending ≥2022 across the 230 names G3
resolves: p50 **57d** · p90 **78d** · p95 **89d** — matching the SEC schedule (60/75/90) exactly.
The next-older annual figure sits at **730d**, so the bound has **260 days of margin** and cannot be
reached by a filer who is merely late.

**THE BOUND LIVES IN THE SHARED READER**, as the default on `annual_eps_as_of`. Two consumers reach
it through `pe_current_and_percentile` — G3 and `cli.py`'s `_pc_valuation` peer-cohort command — and
bounding at the gate alone would have left the peer-cohort command valuing names on sixteen-year-old
earnings. Neither caller can opt out by omission; a pin refuses any widened call site.

**TWO CAUSES, SEPARATED.** A name leaves RESOLVES either because its CURRENT earnings are out of
range, or because per-bar bounding shortened its history under the 450-point floor. Of the **226**
(the gate's resolving set, P/E-only — not 230):

| leaving RESOLVES | count |
|---|---:|
| `G3_EPS_TOO_OLD` | **78** |
| `G3_SHORT_HISTORY` | **17** |
| **total** | **95** (44 of them in the pool) |

`G3_EPS_TOO_OLD` is a FIFTH reason, distinct from `G3_NEGATIVE_ECONOMICS`: that name has never
earned anything, this one HAS but the last positive year is too far back. They resolve differently —
one needs a different valuation basis, the other needs the company to file again.

**NEW CAUSE SPLIT, all 412:** RESOLVES **131** · `G3_NEGATIVE_ECONOMICS` 95 · `G3_EPS_TOO_OLD` 88 ·
`G3_NO_INPUT` 54 · `G3_SHORT_HISTORY` 44.

**THE POOL BOTH WAYS — NOT CHOSEN:** 281 today · **51** if NOT_EVALUATED leaves the candidate set ·
**281 with 230 labelled** if carried as a bucket.

**NO COMMITTED ARTIFACT MOVES — verified at review.** The shared reader has a second consumer,
`cli.py`'s `_pc_valuation`, whose output IS persisted ("dated + immutable snapshot" with a
`valuation` key), so the bound could have silently changed a committed number. It does not:
`data/scan_history/` is untracked and holds nothing, so no peer-cohort snapshot exists. And the
dossiers' `mechanical.valuation.own_history` is CIQ-sourced (`EV/EBITDA (TEV/LTM)`, n_closes 42),
not from `pe_current_and_percentile` — confirming a third time that the dossier is not a consumer
of this path.

**AORT IS AMONG THE HISTORY-SHORTENED** — a committed dossier, 1,132 → **112** P/E points under the
bound. So is BHC (1,254 → 111) and ALLT (1,254 → 86). The dossiers are not re-screened by this
change, but AORT's screen provenance now includes a G3 that would defer.
