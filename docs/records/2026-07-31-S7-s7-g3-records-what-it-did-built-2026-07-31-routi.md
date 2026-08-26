---
id: S7
status: recorded
date: 2026-07-31
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S7. G3 RECORDS WHAT IT DID — built 2026-07-31. Routing NOT decided.** G3 returned UNKNOWN when
nothing valued a name and the runner admitted it anyway, so **186 of the 281 in the 2026-07-29 pool
were never valued at all and every one passed**. UNKNOWN now maps to NOT_EVALUATED with a reason
carrying its CAUSE, and the retention row records the GATE'S result separately from the ADMISSION
(it previously wrote PASS whenever a candidate was produced — the silent pass one layer along).

**THREE CAUSES, THREE REASONS, full population (all 412 reaching G3, not a sample):**

| cause | count | what it means |
|---|---:|---|
| RESOLVES | 230 | a real judgment |
| `economics_negative_throughout` | **94** | an ANSWER about the business, not a data gap |
| `no_valuation_input_tagged` | 54 | a DATA gap |
| `history_below_floor` | 34 | a TIMING state — resolves by waiting |
| `no_price_at_reference` | 0 | infrastructure — named, though unreachable today |

**COUNTS CORRECTED AT REVIEW.** The first pass reported 48 / 85 / 49, measured on a WIDER
definition than the code uses — it counted "nothing tagged" only when BOTH EPS and the EBITDA
components were absent, while the code tests EPS alone (rightly, since EV/EBITDA cannot gate). The
label TEXT and the code agreed; the NUMBER described a different set, which is the record saying two
things. A FOURTH reason also existed as an inline literal, outside the taxonomy and outside the
count — now named `G3_NO_PRICE` and pinned exhaustive by an AST scan for inline `why` assignments.

**THE VALUATION OVERLAP across the 412:** P/E only **89** · EV/EBITDA only **4** · both **137** ·
neither **182**. Union 230.
**BUT THE GATE'S FIGURE IS 226 / 186, NOT 230 / 182 — corrected 2026-07-31.** The union is a
CAPABILITY count; `gate_g3_multiple_floor` reads `ev_ebitda_pctile_vs_history`, which
`enrich_with_fundamentals` sets UNKNOWN unconditionally, so EV/EBITDA **never decides**. The four
names the union credits to it — **ENPH, IDR, LAND, TRUP** — are not valued by the gate. Every G3
count published against a gate claim is P/E-only: **226 valued, 186 not.** Pinned on the code: as
long as the EV field is unconditionally UNKNOWN, a count crediting it is counting a path that
cannot fire.
**AND `UniverseRow.outcome` IS GONE.** It was the constant `FAIL` on all 5,871 rows of a run —
only DROPS emit a universe row, so it carried no information and misled: a name filtered by the cap
band was never assessed by a gate. `NOT_EVALUATED` would be wrong the other way (the band rule DID
assess it, just not against the gates), so the field is removed rather than set to a less-wrong
constant. `stage` + `reason` + `deciding_input` already say what happened. EV/EBITDA adds four names P/E could not reach — it is not an alternative
path, it is almost a subset. Of the 66 in-pool names with a deep EV/EBITDA series, **62 were already
judged by P/E and only 4 sit in the unvalued 186**, which is why the earlier reshape did not survive
measurement.

**THE POOL BOTH WAYS — NOT CHOSEN (operator's call, in parallel):**
- pool today: **281**
- if NOT_EVALUATED leaves the candidate set: **99**
- if carried as a labelled bucket: **281**, of which **182 labelled NOT_EVALUATED**

**CAN NEVER BE VALUED:** **133 of the 412** have never reported a positive annual EPS and never a
positive EBITDA — 133 of them are in the pool. No label built for that set here.

**FLOOR REUSED, NOT PICKED:** `_PE_MIN_POINTS = 450` already answers "how much history does a
trailing-range percentile need" for this same gate and same sentence; a second looser floor for the
EV/EBITDA path would have been a number chosen to make a build succeed. On that floor EV/EBITDA's
p50 depth is **0** (bimodal: 223 names at zero, 48 short, 141 deep), which is why it cannot gate.
