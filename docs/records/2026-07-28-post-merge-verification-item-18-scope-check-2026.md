---
id: 
status: recorded
date: 2026-07-28
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**POST-MERGE VERIFICATION + ITEM-18 SCOPE CHECK — 2026-07-28 (operator-directed, BEFORE any
build).**
(1) **ROUND-TRIP CLAIM VERIFIED, not asserted.** "Defaults False, so every committed dossier
round-trips" was a design claim. Checked on ALL ELEVEN committed dossiers (each predating #238, so
none carries a `material` key): **11/11 parse under the new `FinRow`, and 11/11 render
BYTE-IDENTICAL.** The optional-field default is confirmed, not assumed. PIN SCOPED AT REVIEW: the
first cut asserted live-render == committed `.md` fleet-wide, which DUPLICATED
`test_screening_context_reaches_every_committed_dossier_e2e` and — worse — never read `material`
at all, so deleting the field left it green. A test whose docstring claims one thing while its
assertion tests another reddens on unrelated renderer changes and stays silent on the regression
it is named for. Rewritten to read the FIELD (no `material` key in the committed JSON; every row
returns False); mutation-tested — default flipped to True CAUGHT, field removed CAUGHT, both of
which the first cut passed.
(2) **ITEM 18'S INPUT DOES NOT EXIST IN USABLE FORM — the operator caught P1's shape again, before
the build.** Confirmed and WORSE than the single example suggested: **all three** regression-trio
facts live inside the `thesis` PROSE string of the V-row payload, none of them structured —
loan-basis 1.2x, the $331.0M impairments, AND the ~2.1M-share buyback pace, all three in `thesis`
only. The payload's structured fields are `entry_price`, `ratio_at_entry`, `confidence`,
`horizon_days`, `kill_criteria`, `twin_call`, `machine_proposal`… — the DECISION metadata, never
the underlying facts. `log_verdict` takes `thesis: str`, so this is the write path's shape, not an
accident of one entry. A guard reading these would have no structured source and would fall back
to regexing free text — which fails on the first payload phrased differently. **18a (payload
structured-fact fields) must precede 18 (the guard); 18 is small once 18a exists.**
(3) **SCOPE — SMALL, AND NO BACKFILL IS REQUIRED.** The ledger holds **5 rows: 3 V-rows**
(`V-IT-…` BUY, `V-SMPL-…` BUY, `V-VRRM-…` AVOID_TERMINAL) **and 2 C-rows**. Structured fields are
ADDITIVE and OPTIONAL, so 18a binds FORWARD exactly like `BASIS_REQUIRED_FROM` / `FIELDED_REFS_FROM`
— the repo's established pattern — and the three existing V-rows stay untouched. **NO COMMITTED
DECISION IS REWRITTEN.** Consequence stated honestly: for those three legacy rows the guard has no
structured source, so 18 cannot check them; it binds to rows written after 18a.
