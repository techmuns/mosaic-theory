---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
date-source: MIGRATION DATE — this record was cut out of STATE.md on 2026-08-26; the work it describes is earlier (2026-07-19, per the heading). The filename prefix is therefore the migration date, not the event date.
migrated-from: STATE.md §2 Built and verified
---

# **WERN — THE FUND'S FIRST REPRODUCIBLE 2:1 RUN (2026-07-19, #150). Result: FAIL at spot.

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **THE VERDICT (human, recorded in `scenarios/WERN.json` → `verdict`):** *"FAIL at 2:1 (ratio
    −0.35, reward −10.31 at spot 46.04). Base sits ~22% below spot; corroborated by EV/EBIT 16.1x
    at base and ~3.7% normalized FCF yield — priced to its own recovery. Quality franchise, not
    broken → WATCH, not AVOID."* The machine proposed nothing; it computed and recorded, and the
    human decided — the first end-to-end exercise of the 2026-07-13 division of labour.
  - **RE-UNDERWRITE TRIGGERS (a WATCH is a standing instruction, not a shrug):** (1) spot pulls to
    **~28–30**, where the base case offers 2:1; (2) a reported quarter proving normalized operating
    margin genuinely **>7.5%** (disclosed Dedicated segment economics, or a clean beat).
  - **`avoid_priced = true`** — the asymmetry is INVERTED at $46 (upside +6% to bull vs downside
    −22% to base / −64% to bear). Tracked for **avoid-leg short-alpha on PAPER**. Recording this
    creates no position: no code path here approaches execution.
  - **SCHEMA:** `VerdictStatus` gained `watch` (not underwritable at today's price, franchise
    intact — distinct from `passed`, which declines outright), and `Verdict` gained `rationale`,
    `reunderwrite_triggers`, `avoid_priced`, `avoid_priced_note`. *A verdict that says only "no"
    decays into a number nobody can re-check.* Display rounding lives in the frontend card
    (prices/ratio 2dp, multiples and $M 1dp); the RECORD stays full-precision.
  - The first underwrite carried end-to-end through a *named recipe* on a *versioned record*, so it
    can be re-run and audited rather than remembered — verified: re-running R1 against the committed
    record reproduces it EXACTLY.
  - **RECIPE #1 (`R1_midcycle_margin_evebitda`)** — mid-cycle operating margin on a mid-cycle
    revenue base × an exit **EV/LTM-EBITDA** multiple; reward/risk at SPOT per the ratified
    convention. Persisted as `scenarios/WERN.json` (schema + writer/reader in `vinci/scenarios.py`).
  - **RESULT (spot $46.04, Polygon EOD 2026-07-17 — live):** bear **$16.60** · base **$35.73** ·
    bull **$48.88** (bull PRINTED, never in the ratio). reward = base−spot = **−$10.31**; risk =
    spot−bear = **+$29.44**; **ratio −0.350 : 1 vs the 2:1 bar → FAIL.** Reward is NEGATIVE — the
    base case sits ~22% BELOW spot — so the name is not underwritable at $46 on these assumptions.
    Recorded honestly; a FAIL is a result, not an error.
  - **CAPITAL-INTENSITY CROSS-CHECKS (the point of the exercise):** base EV/EBIT **16.1x** against
    a 6.5x EBITDA turn, and normalized FCF of **$116M** on a $3.12B EV (~3.7%). The EBITDA multiple
    flatters a carrier whose D&A ($286M) EXCEEDS base EBIT ($194M) — which is exactly how the
    basis defect below stayed invisible.
  - **SOURCE-BOUND FACTS** (each `{value, unit, basis, source}` in the record): D&A **286.321**
    (consolidated FY2025 — 10-K acc 0000793074-26-000071 income statement; NOT the 277.879
    reportable-segment figure) · net debt **979.776** incl. operating + finance leases as of
    2026-03-31 (10-Q acc 0000793074-26-000096: LT debt 8.600 + 869.600 + finance leases 26.706 +
    26.878 + operating leases 48.832 + 60.704 − cash 61.544) · diluted shares **59.91M** (Q1-2026).
    The FCF cross-check additionally uses cash interest 39.053 (FY2025 filing) and a **25%
    normalized cash-tax rate — an ANALYST ASSUMPTION, labelled as such in the record**, touching
    the cross-check only, never value/share.
  - **INCIDENT→INVARIANT — #149 shipped an EV/EBIT ↔ EV/EBITDA basis defect (fixed + pinned).**
    The block offered ANCHOR D as a `TEV/LTM EBITDA` band and then computed `ev = operating_income
    × multiple` — an EBITDA multiple applied to EBIT, understating a capital-heavy name by
    ~(1 + D&A/EBIT)x (**WERN: ~7.5x** — base $4.66 on EBIT vs $35.73 on EBITDA). Fixed:
    `ev = (EBIT + d_and_a) × multiple`; `d_and_a` is REQUIRED by `build_scenario` (no default —
    omitting it is precisely how the defect returns); `MULTIPLE_BASIS = "EV/EBITDA"` is stamped
    onto every MidCycle record AND every scenario record; the CLI refuses a scenario without
    `dna=`. Pinned by `test_wern_multiple_is_ev_ebitda_not_ev_ebit`, which asserts the EBITDA
    values **and** that the EBIT-basis values are NOT produced. *A unit that is implicit will
    eventually be read wrong; a unit that travels with the record cannot be.*
  - **SHIPPED:** reusable scenario-card renderer in `frontend/build.py` (reads `scenarios/*.json`,
    attaches under any watchlist name, no full-dossier dependency). WERN's card renders under
    truckload-supply-purge. Verified: **1 of 16 committed frontend artifacts changed** — the WERN
    card only; `index.json`, `defense.json`, `ai-datacenter.json` and all dossiers byte-identical.
  - **DEFERRED (not built):** the full 18-section CIQ+LLM dossier for WERN — build only if the name
    pulls toward the ~$28–30 clearing price implied by the base case.
