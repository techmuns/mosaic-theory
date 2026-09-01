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

# Earliness-assay v1 — velocity-axis hardening + card legibility (`feat/assay-v1`; ZERO LLM, backend-only, nothing deploys). Everything below is computed ALONGSIDE the recorded v0 basis; the recorded v0 PASS is UNCHANGED and anchored-definition adoption is PENDING OPERATOR SANCTION.

*The one-line summary stays in STATE.md §2 with a pointer here. This is the detail that stood beneath it, verbatim.*

- **Earliness-assay v1 — velocity-axis hardening + card legibility (`feat/assay-v1`; ZERO LLM,
  backend-only, nothing deploys). Everything below is computed ALONGSIDE the recorded v0 basis; the
  recorded v0 PASS is UNCHANGED and anchored-definition adoption is PENDING OPERATOR SANCTION.**
  WHAT CHANGED (each recorded side-by-side, never overwriting v0): (1) CALENDAR-ANCHORED new-filers —
  a CIK is new in the calendar quarter of its first mention vs a FIXED trailing-12q lookback,
  window-INDEPENDENT (fixes the window burn-in); cards print BOTH columns (window-relative = the
  recorded basis). (2) PER-TERM DECOMPOSITION — top terms by new-filer contribution per quarter.
  (3) PLACEBO candidate `placebo-boilerplate` (near-universal boilerplate ≈ raw new-registrant flow,
  `is_placebo`, operator-swappable); theme cards print a per-quarter RATIO = theme/placebo anchored
  filers (None-safe). (4) BASKET INTEGRITY — warrant/unit/right classes EXCLUDED (Polygon-type
  primary + suffix fallback; LIDRW no longer leaks), per-member cap provenance (shares source/count,
  price date), a print-only >5x-QoQ cap sanity flag. (5) CLI SELF-HEALING — cache-first retries with
  backoff on transient efts 5xx, fail-loud with the exact missing read on exhaustion. PRESENTATION-
  ONLY (fed to NO verdict): the classifier-input columns (trailing-4q median + OLS slope, window
  documented EXCLUSIVE of the current quarter), the DERATED-EARLY annotation (excess < −20% vs BOTH),
  and the SYMMETRIC ±20/±30 band residence row (|excess| < threshold). +7 network-free tests; ruff +
  `mypy --strict vinci` clean; suite 520 passed (the 1 failure is the pre-existing `test_t2` dossier
  case, unrelated).
  **ACCEPTANCE RUN (2026-07-07, live EDGAR + Polygon, ZERO LLM) — SIDE-BY-SIDE VERDICTS (verbatim):**
  RECORDED (window-relative v0 basis): `PASS (RECORDED: survives — early-window premise NOT
  falsified)`. ANCHORED (v1 velocity, PENDING SANCTION): `PASS (ANCHORED: survives — early-window
  premise NOT falsified)`. **AGREEMENT: verdicts AGREE (PASS); anchored adoption remains PENDING
  OPERATOR SANCTION.** The RECORDED residence matches the v0 record (merged #86) EXACTLY — the
  window-relative mechanism is unchanged and v1 reclassified no recorded case (no warrants in the
  recorded baskets, so the warrant-exclusion fix cannot move them); the anchored velocity clears
  ≥2q EARLY on the SAME cases (defense-demand-shift @ 2023-01-01: RECORDED flat20_medrise 2/2,
  flat20_sloperise 3/3 → ANCHORED 5/5, 5/6 — the burn-in fix LENGTHENS the runs, itself a claim to
  sanction, not adopt).
  **PLACEBO / RATIO / DECOMPOSITION FINDINGS — THE CONTROL SPEAKS (recorded VERBATIM, honestly):** the
  placebo null FIRES. For defense-demand-shift @ 2022-01-01 the RATIO (theme/placebo anchored
  new-filers) is 0.99, 0.79, 0.96, 0.81, 0.77, 0.99, 0.92, 1.00 across 2020Q1..2021Q4 — ~1 throughout
  and NOT rising; the placebo shows the SAME 2021Q1 spike (placebo anchored 586 vs defense 454). So
  the 2021 new-filer surge underlying defense's EARLY residence is LARGELY A LISTING-WAVE ARTIFACT,
  not defense-specific acceleration. The 2021 filers are driven by GENERIC terms — defense (194/163/
  207/162 per 2021 quarter), military (93/83/82/98) — the shift-specific terms (drone, munitions,
  missile, autonomy) are secondary. The SYMMETRIC ±band row shows defense-2023's EARLY SURVIVES a
  symmetric flat rule (flat20_medrise 2/2) — so the recorded PASS is NOT merely a one-sided-flat
  artifact — but defense-2022's collapses to 0/0 (its EARLY was deep-underperformance-classified-as-
  flat, flagged DERATED†). **NET (honest): the recorded PASS stands and is robust to the symmetric
  band, but the velocity axis is substantially CONFOUNDED by the 2021 listing wave (ratio ~1) and
  driven by generic defense terms — the "earliness" is a price-flat-while-registrants-flood pattern,
  not demonstrated theme-SPECIFIC anticipation. A CONTROL-SAYS-NO caveat for any live use.** On
  `feat/assay-v1`; PR opened, NOT merged. Anchored adoption + velocity-confound remediation are v2
  briefs, PENDING OPERATOR SANCTION.**
  **— AUDIT (2026-07-07, 6-lens adversarial review of PR #91, each finding double-verified): 1 real
  fix.** The warrant/unit/right ticker-suffix fallback was UNSOUND — bare single-letter W/U/R with a
  len>=4 gate false-positived on common stocks (SNOW ends W, PLTR ends R), and on a Polygon
  security-type OUTAGE (security_types=None) it was applied to EVERY ticker, mass-excluding commons.
  FIX: bare-letter suffix now requires the >=5-char base+class-letter shape (keeps the real cases —
  LIDRW/CORZR/SHAZW len-5 — drops the 4-char common false-positives) AND is DISABLED entirely on a
  metadata outage (metadata is the only authority; no common excluded on a guess). Proven
  non-regressive: re-running ai-datacenter@2026-06-01 left the basket + recorded quadrants/residence
  byte-identical (CORZR/SHAZW still excluded). +negative pins (SNOW/PLTR/PANW kept) + an outage pin.
  Two low fixes: the cap-QoQ sanity flag now compares only CALENDAR-ADJACENT priced quarter-ends (was
  mislabeling a gap-straddling move 'QoQ'); STATE wording "byte-identical to the merged v0 record"
  tightened to a precise numeric-match statement. All else the audit raised was refuted or cosmetic.**
