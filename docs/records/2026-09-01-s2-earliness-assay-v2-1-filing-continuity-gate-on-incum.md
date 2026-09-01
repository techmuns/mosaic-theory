---
id:
status: recorded
date: 2026-09-01
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §2 (capability entry, compacted)
date-source: the migration date — the capability is older and is dated in the body
---

# Earliness-assay v2.1 — filing-continuity GATE on incumbent first-mentions (the SANCTIONED FINAL velocity-axis iteration); SCOPE-STOP EXECUTED.

*The one-line summary stays in STATE.md §2 with a pointer here. This is the detail that stood beneath it, verbatim.*

- **Earliness-assay v2.1 — filing-continuity GATE on incumbent first-mentions (the SANCTIONED FINAL
  velocity-axis iteration); SCOPE-STOP EXECUTED.** One bounded apparatus repair after the v2 CONFOUNDED
  result. **OPERATOR SANCTION (2026-07-08, verbatim):** "One bounded apparatus repair sanctioned after
  the v2 CONFOUNDED result. This is the FINAL velocity-axis iteration: the criterion below executes the
  scope-stop with no further apparatus appeals." SCOPE FROZEN — tiers / thresholds / combos / anchored
  definition / basket rule ALL untouched; the ONLY change is the gate. **THE GATE:** an incumbent
  first-mention COUNTS (new gated HEADLINE) only if the CIK filed in EACH of the 4 calendar quarters
  immediately before the mention quarter, read from the cached data.sec.gov submissions `recent` window
  (a cache HIT — zero fresh network on already-seen CIKs) — so a counted first mention can only mean
  first ADOPTION, never first appearance / re-engagement. Continuity is UNDECIDABLE when cached `recent`
  cannot reach back that far AND older-archive pages exist → gate-unknown (fail-loud, never assumed
  continuous). Prior series stay printed. **PRE-COMMITTED FINAL CRITERION (verbatim):** "(i) The gated
  placebo incumbent-specific series must show NO self-qualifying run (same run definition as v2). (ii) If
  and only if the placebo is clean, the identical contrast criterion applies to the gated theme series on
  the two positive controls. (iii) If the placebo STILL self-qualifies OR neither positive control shows
  contrast, the SCOPE-STOP EXECUTES FINALLY: velocity axis demoted to printed diagnostic, further
  velocity iteration BARRED, assay ships reduced (price-gate + decomposition + human reading)."
  **ACCEPTANCE RUN (2026-07-08, live EDGAR + Polygon + data.sec.gov, cache-first, ZERO LLM; retrocast +
  3 single-card commands OK):** the gate had REAL effect — it ~halved the placebo (defense-aligned gated
  placebo = `[107,97,82,107,107,74,56,68,77,63,63,70,79,94,75,110]` vs ungated
  `[171,171,134,190,173,161,113,166,167,169,122,136,150,149,102,168]`; gate-unknown only 1–11/quarter, so
  coverage is good) and cut the themes ~30% (gated defense@2023-01-01 =
  `[29,38,43,69,34,32,43,90,68,44,27,71,40,28,23,67]`; gated ai-datacenter@2022-07-01 =
  `[14,20,21,14,13,28,9,15,20,46,28,16,21,34,14,14]`). **BUT the gated placebo STILL self-qualifies** (a
  ≥2-quarter run strictly above its own trailing-4q median, floor ≥3) → BOTH positive controls
  `CONFOUNDED` → **FINAL OUTCOME: SCOPE-STOP EXECUTES FINALLY** (criterion iii). Per the sanction this is
  TERMINAL: the **velocity axis is DEMOTED to a printed diagnostic, further velocity-axis iteration is
  BARRED**, and the assay ships REDUCED — price-axis PRICED-gate + incumbent-specific decomposition +
  human reading. **RECORDED / ANCHORED kill verdict UNCHANGED** — PASS (RECORDED) / PASS (ANCHORED),
  AGREE; the gate is additive and did not touch the EARLY-residence verdict. The gate itself is RETAINED
  as a printed diagnostic (it demonstrably separates continuous adopters from re-engagement / first-
  appearance flow — the placebo's spurious "incumbents" nearly halve under it), NOT a live velocity
  signal. The control did its job a third and final time: it said no. On `feat/assay-v2-1`; PR to be
  opened, NOT merged.**
- _Whole suite green (ruff + mypy --strict clean; `pytest -m "not network"` = 534 passed, 1 skipped;
  +3 gate tests: continuity-gate math, filed_quarters parse/404/throttle, gated-placebo-collapse
  property)._
