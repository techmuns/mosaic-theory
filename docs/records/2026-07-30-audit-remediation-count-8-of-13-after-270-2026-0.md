---
id: 
status: recorded
date: 2026-07-30
prs: [270]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**AUDIT-REMEDIATION COUNT — 8 of 13 after #270 (2026-07-30).** Three read-only verifications were
run BEFORE building, at the operator's direction, and two of the three changed the plan:

1. **P3 pt 1 is NOT closed by item 16's `role` — it stays open.** Measured on the committed record,
   not reasoned from the schema. Three independent reasons, any one sufficient: (i) **the row is
   untagged** — `scenarios/SMPL.json .assumptions.revenue.references[1]` (`label` "LTM revenue",
   `value` 1416.208, `source` "committed dossier anchor block") carries no `role` at all, and only
   **34 of 119** fleet reference rows do, because `FIELDED_REFS_FROM = "1.3"` binds at WRITE and
   legacy rows stay legal forever; (ii) **`REF_ROLES` has no vintage member** — {median, mean,
   percentile, band_low, band_high, trough, peak, current, reported, consensus, guidance,
   peer_median, peer, analogue} types WHICH STATISTIC, never AS-OF, and the nearest (`reported`)
   would assert something false; (iii) **different defect classes** — `role` fixed a SELECTION
   defect (the masthead's `find(/median/i)` picking by array order), while P3 pt 1 is a DISCLOSURE
   defect: the row is correctly typed and legitimately used, but its value is frozen entry-vintage
   (1,416.208 vs live 1,392.235) and its source claims a provenance that now belongs to a different
   number. Neither `role`, `leg` nor `excluded` can express either half — `excluded` would be a lie
   in the other direction, since the row IS used. **So the stop point is 9, not 10** — the
   operator's own 9-branch, reached independently.
2. **19a does NOT batch with 29 + `spot_as_of` — split, and the reason is mechanism, not files.**
   Files ARE disjoint but the attribution was off: 19a lives in **`vinci/dossier/mechanical.py`**,
   not `ciq_sheets.py`. The disqualifier is that they are different KINDS of change: 19a is a
   one-file derivation fix verified by calling a function on real bundles — no schema, no
   migration, no record touched — whereas 29 + `spot_as_of` are schema-gated field additions on
   `ScenarioRecord` touching all 7 committed records, `_schema.json`/`_seal.json`/
   `_amendment_index.json`, both render twins, and a forward gate. Batching them means the
   migration's green suite vouches for the derivation fix too. **And 29 cannot close its half in
   any case** — this file's own closure table says ANALYST-DATA items close on "guard ships **AND**
   the surfaced instance is adjudicated", so shipping the typed field surfaces SMPL's bull-leg
   violation (1,420 vs LTM 1,392) and leaves the half open pending an operator ruling. Shipping it
   now would add schema churn for **zero** count movement.
3. **`_figure_cited` (#268) tolerates rounding, with one gap that would refuse a CORRECT page.**
   Measured, not reasoned: `$392M` against a row holding 391.9 **matches** (the `f"{a:.0f}"` form),
   as do `$391.9M`, `$1,523M` and `$61M`. **The live gap is unit-shifting: `$1.5bn` against
   −1,523.3 does NOT match** — and CNXC's −1,523.3 is one of only **two** guarded figures on the
   corpus, so the spurious-refusal risk is concentrated exactly where the guard applies. Also
   missed: `$392.0M`. Truncation (`$391M`) and 2-s.f. (`$390M`) are correctly refused — accepting
   those would widen toward false positives. **NOT loosened on report** — the instruction was to
   answer, not to widen on the operator's say-so.
   **BUILT 2026-07-30 (PR #271) — scale-aware, tolerance UNCHANGED.** Past $1bn the value is also
   emitted in billions at 1 and 2 dp (`$1.5bn` / `$1.52bn` / `$1.5 billion` / `$1.5B`), plus the
   bare integer ONLY when `|b − round(b)| < 0.05` — `$2bn` is a fair citation of 2,000.4 and a lossy
   one of 1,523.3, and the second is the case the guard must refuse. `$392.0M` added via
   `f"{round(a):.1f}"`. Sub-$1bn values get NO billions form, so `$0.4bn` against 391.9 stays
   refused exactly like `$390M`. `$1523M` matching was recorded as a defect above and is NOT — a
   separator-free rounded form is a correct citation; the earlier expectation was wrong.
   Real-run on CNXC's actual row: `$1.5bn` / `$1.5 billion` / `$1,523.3M` all ACCEPT, `$1.6bn`
   REFUSES. Mutations: block removed → 6 red; 2-s.f. billions admitted → 2 red.
   **PATTERN, and it earns its own line — A GUARD'S COVERAGE GAP BECAME THE NEXT DELIVERY'S
   BLOCKER.** 19c (#268) refuses a build whose synthesis omits a material figure. Two PRs later the
   19a artifact pass needed CNXC re-assembled — and 19c would have refused a CORRECT CNXC page,
   because its matcher knew only millions while the natural citation of −1,523.3 is `$1.5bn`. The
   guard was not wrong about the page; it was blind about the FORM. Generalised:
   **a guard that refuses on ABSENCE inherits the completeness of its own recogniser — every form it
   fails to recognise is a false refusal waiting for the first author who writes that way.** So a
   presence guard's recogniser needs its own coverage measurement, not just its decision logic
   tested. The tell here was cheap and was already in hand: the corpus had only TWO guarded figures
   and one of them sat past the recogniser's ceiling.

**THE FIVE DEFERRALS, closed out 2026-07-30 — the audit-remediation program stops here at 8 of 13.**
Every one is deferred for a stated reason, and one of them is not a build at all:
1. **P3 pt 2 / item 29 — UNCLOSEABLE BY CODE.** The bull leg (1,420) sits above the LTM it claims to
   sit "just under" (1,392). A guard can only SURFACE that; the remedy is **an analyst re-setting the
   bull leg or restating the method**, which is a DECISION, not a build. This file's own closure
   table says analyst-data items close on "guard ships **AND** the surfaced instance is
   adjudicated" — so shipping the typed field would buy a schema change across seven records, the
   seal, the amendment index and both twins for **zero count movement**. Not deferred for cost:
   deferred because code cannot close it.
2. **`spot_as_of`** — completes clause (e) for P4 pt 2. Needs a schema field + forward gate + render
   on both twins + a migration of seven records whose struck date exists ONLY in analyst prose
   (`spot_source`, phrased differently per record). Composing it by parse is the forbidden
   display-string read; the honest route is to DERIVE it — match the recorded `spot` against the
   Polygon store's bar for the candidate date and fail loud on mismatch — which is its own build.
3. **1(b) — stale price / P4 pt 1.** Its structured half IS `spot_as_of`, so it inherits (2).
4. **P7 pt 2 / item 24 — wrong share basis.** Operator-deferred; untouched this run.
5. **P3 pt 1 — the mislabelled frozen reference.** Verified NOT closed by item 16's `role` (untagged
   row · `REF_ROLES` has no vintage member · disclosure vs selection defect). Needs the frozen
   marker + vintage in the record itself.

**CONSCIOUSLY DEFERRED (operator-directed 2026-07-30), with reasons — not forgotten, not blocked:**
- **1(b) — stale price / P4 pt 1.** Deferred by the operator this run. Its structured half is
  `spot_as_of`, which is itself deferred with 29 (see above), and its migration needs each record's
  struck DATE — which exists only inside analyst free text (`spot_source`, phrased differently per
  record). Composing it by parse is the forbidden display-string read; the honest route is to
  DERIVE it (match the recorded `spot` against the Polygon store's bar for the candidate date and
  fail loud on mismatch), which is its own build with its own verification.
- **P7 pt 2 — wrong share basis (item 24).** Deferred by the operator this run; untouched.
