---
id: S13
status: recorded
date: 2026-08-01
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S13. G3'S GATE INPUTS REACH THE RETENTION ROW — built 2026-08-01. NO RE-RUN; the -03 run stands.**

`gate_inputs` carried `drawdown_from_high`, `rel_ret_vs_market`, `last` — all price, all G1/G2. G3
is the VALUATION gate and **none of its inputs were recorded**, so a row said what G3 decided and
why but never the number it decided on. Retention exists to falsify the screen; for G3 it could not.
G1 and G2 were falsifiable from their rows since the grain shipped.

**MECHANISM ESTABLISHED FROM CODE FIRST (the framing was not taken on trust).**
`gate_g3_multiple_floor` reads `rec.fundamentals.ev_ebitda_pctile_vs_history`, falling back to
`rec.fundamentals.pe_pctile_vs_history`. Both sit on **the same `rec` object `_gate_inputs` already
receives** — so the inputs WERE reachable at the write point and the fix is an addition, not a
plumbing change.

**CORRECTION TO THE BRIEF'S SECOND CLAIM — this does NOT give `.pe.as_of` a reader.** G3 reads the
PERCENTILE field, not `fundamentals.pe`. The reader this creates is for
**`pe_pctile_vs_history.as_of`**. Both carry the #300 EPS-period stamp (`assemble.py` stamps the
percentile `as_of=cur_pt.period_end` with a comment saying why: every P/E in the trailing range
carries the same EPS-vintage lag). So the stamp *class* gains its first reader — but a re-run of
the AST sweep for `.pe.as_of` specifically will still return **zero**. `fundamentals.pe` remains
unread on every surface.

**BOTH G3 INPUTS ARE RECORDED, not only the one that decided.** The gate resolves a preference —
EV/EBITDA first, P/E second — and a row carrying only the winner cannot say WHY that one was used.
Declared in the gate's own order, pinned.

**WHAT A G3 ROW CARRIES AFTER THIS — verified on six REAL records at reference 2026-07-29, one per
G3 state, built through `build_data_record` from the live store + EDGAR** (no screen re-run):

| ticker | G3 | `pe_pctile_vs_history` | as_of | note |
|---|---|---|---|---|
| PSN | PASS | 0.0008 | 2025-12-31 | 1254 P/E observations over 1825d; … |
| AMPH | FAIL | 0.2616 | 2025-12-31 | 1254 P/E observations over 1825d; … |
| ASM | NOT_EVAL | None | None | no valuation input tagged |
| CATX | NOT_EVAL | None | None | economics negative throughout |
| LUMN | NOT_EVAL | None | None | last positive annual EPS older than one filing cycle |
| MZTI | NOT_EVAL | None | None | history below the floor — only 271 P/E points |

`ev_ebitda_pctile_vs_history` is present on all six and UNKNOWN on all six
(*"EV/EBITDA deferred — needs net-debt/EV"*) — consistent with the earlier finding that EV/EBITDA
cannot gate today. **Recording it is what makes that visible per-row instead of per-audit.**

**THE STAMP IS THE POINT: `as_of=2025-12-31` on a 2026-07-29 run — 210 days older.** A row stamping
the run date would claim a freshness the number does not have, the exact shape that let a stale
benchmark pass for a current one. Pinned as a RELATION (the field's own stamp, strictly older than
the run), not as a literal date.

**THE 282 NOT_EVALUATED NAMES DO CARRY ENOUGH TO SAY WHY LATER — measured on the -03 run.** Of 413
that reached G3: 49 PASS, 82 FAIL, **282 NOT_EVALUATED**, split **95** negative-economics · **89**
EPS-too-old · **54** nothing-tagged · **44** short-history. Each writes value None, NO stamp, and
the cause on the input's own `note`. The cause was previously only in the gate's `reason` string;
it is now attached to the INPUT, so a later analysis can group by input state without re-parsing
prose. **What they still cannot support:** any distribution of the P/E percentile itself for those
names — there is no number, and this build does not invent one.

**ONE SHARED `_stamped` HELPER** converts every DataField to a StampedInput. Two conversions would
drift and the drifted one would be whichever nobody re-read (the divergent-parser class). Pinned by
AST: `_gate_inputs` may not construct a `StampedInput` directly.

**span_days/observations DELIBERATELY ABSENT on the G3 inputs.** The percentile's window (1825d)
and point count live in the field's note as PROSE; the structured values do not reach here.
Recovering them would be the display-string re-parse this repo bans — left absent and said so
rather than reconstructed.

**MUTATIONS — five, all RED.** A G3 input absent from the row; the stamp replaced by the run date;
the G3 block dropped entirely (the pre-build state); NOT_EVALUATED inputs skipped by a
value-is-None guard; the preference order reversed.

**REVIEW FINDING (#305) — THE TEST SHAPE HAD DRIVEN THE PRODUCTION SIGNATURE.** The first cut typed
`_stamped(f: object)` and read `getattr(f, "value", None)`. It did so ONLY because the test fixtures
were a hand-rolled four-attribute stub rather than a real `DataField` — the fixture's shape dictated
the production contract, which is backwards. **Consequence had it shipped:** a renamed or mistyped
attribute becomes a silent `None`, writing "the gate could not see this" onto EVERY row — a
fabricated NOT_EVALUATED across the whole corpus, inside the rows that exist to BE the evidence.
Fail-quiet in the worst possible place, against the fail-loud rule.

**AND THE TYPE CHECKER CANNOT SEE IT — measured, both ways:**

| written as | `mypy --strict` |
|---|---|
| `getattr(f, "valu", None)` | **Success: no issues found** |
| `f.valu` | **error: "DataField[Any]" has no attribute "valu"; maybe "value"?** |

So a defaulting `getattr` on a typed model does not merely read loosely — it REMOVES the attribute
from static checking entirely, moving the error from compile time to "caught only if a test happens
to cover that field". Fixed: `_stamped(f: DataField[Any])` with direct attribute access, and the
fixtures now build real `DataField`s (which also buys the coverage contract — PRESENT must carry
both value and as_of, UNKNOWN neither). All five mutations re-run RED against the tightened code.

**RULE: a defaulting `getattr` on a TYPED object is an un-typing operation.** Use it only where the
container genuinely may not have the attribute (`getattr(rec, "fundamentals", None)` — `rec` is
untyped at that boundary); never to read a field off a model whose type is known.
