---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
date-source: MIGRATION DATE — this record was cut out of STATE.md on 2026-08-26; the work it describes is earlier (2026-07-20, per the heading). The filename prefix is therefore the migration date, not the event date.
migrated-from: STATE.md §2 Built and verified
---

# **SCHEMA 1.1 — STRUCTURED ASSUMPTION DERIVATIONS + THE STAMPED RECIPE FORMULA (2026-07-20,

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **RECORD-LEVEL FIX (the reproducibility unit — every future underwrite gets it for free):**
    `ScenarioRecord.assumptions: dict[axis → AssumptionDerivation{method, references[RefPoint
    {label,value,unit,source}]}]` + `recipe_formula` STAMPED by run_recipe from
    `midcycle.R1_FORMULA` (the ONE statement of the arithmetic, line-for-line beside
    `scenario_value`; a record claiming different arithmetic is REFUSED, never overwritten —
    the multiple_basis pattern). Blanks refused (label/unit/source/method); references may be
    EMPTY (a pure-judgment method honestly stated beats a fabricated reference).
  - **GUARDS BOTH WAYS, version-gated:** unknown axis for a known recipe → refused at ANY
    version (a typo'd axis silently dropping from the render is data loss); completeness
    (exactly revenue/margin/multiple for R1) binds FORWARD from `schema_version 1.1` — 1.0
    records stay valid (the reward/risk-convention binds-forward pattern). `AXES_BY_RECIPE`
    declares axes per recipe; unknown recipes unconstrained until they declare.
  - **RENDER (ONE card, both surfaces):** the stamped recipe chain prints inside the Scenarios
    fact above the legs table; a Method fact (always printed) states per-axis how each input
    was modeled; "Reference frames & chosen values" (collapsed `<details>`, own "M" endnote
    scope — print-fate invariant) juxtaposes each axis's source-cited reference values with the
    chosen bear/base/bull trio (juxtapose, never difference). Absent data renders NOTHING.
  - **WERN BACKFILL — transcribe + machine-verify (operator-decided):** every computable
    reference VERIFIED against a real EDGAR run before commit: anchor median 7.45%/18FY,
    FY2025 0.39%, FY2021 peak 11.31% (all match #150); **insurance run-rate 2018-22 avg
    verified == 4.06% EXACTLY** via `us-gaap:OperatingInsuranceAndClaimsCostsProduction ÷
    Revenues` (3.99/3.61/4.63/3.61/4.48) — upgraded from analyst-calc to tag-sourced; revenue
    refs filled from the run (FY2025 2,974.4 · FY2022 3,290.0 $M). Written through
    model_validate (guards ran); `result{}`/`verdict{}` byte-identical, pinned e2e
    (`run_recipe(rec).result == rec.result` — assumptions can never feed arithmetic).
  - **⚠ DATA-INTEGRITY DISPOSITION (operator to ratify at PR review):** the bull reason's
    "12-14% 2020-22 peaks" is NOT reproducible at the consolidated layer — the verified peaks
    are 9.59/11.31/9.82%. Committed as the VERIFIED FY2021 11.31% ref (label juxtaposes
    2020/2022); the analyst's reason prose left VERBATIM (frozen-rationale precedent); the
    12-14% figure NOT committed (DERIVED-PIN rule — unnamed layer mix). Two `confirm at
    review` sources remain on the Dedicated-mix refs (51.5%→73%) — analyst calculations whose
    filing basis the operator should confirm.
  - **Artifact notes:** the theme JSON's embedded card was surgically replaced (`data/forward/`
    absent locally — build_themes cannot re-run; PR#74 hand-correction precedent, byte-format
    asserted) → FOLLOW-UP §Next-steps: re-run the theme build from the freeze source when
    available. The 7 anchor-name frontend mirrors were regenerated (1df5c6a left them to
    deploy-time regen; the local build surfaced the drift — committed == deployed now).
  - **INVARIANT (incident → guard):** unreviewable methodology → version-gated completeness at
    the model boundary + formula stamp-and-refuse + the committed-WERN e2e pin. Gate: ruff +
    mypy --strict clean; **728 passed, 0 skipped** ON the committed artifacts; build ×2
    idempotent; browser-verified both surfaces, light + dark (canonical axis order pinned after
    a real render caught my modulo-sort bug putting revenue last).
  - Housekeeping: #157 (cites lift) MERGED as `33d1e59` — the card now owns its citations with
    no host pass; this entry's render work builds on that form.
