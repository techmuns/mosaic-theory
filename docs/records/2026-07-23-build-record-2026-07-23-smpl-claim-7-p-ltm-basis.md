---
id: 
status: recorded
date: 2026-07-23
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-23 SMPL claim-#7 P/LTM basis caveat (branch `fix/pltm-gaap-basis-caveat`).**
The step-2 re-assembly proved #198's FIX 3 does NOT fire for SMPL — its `fundamentals.pe` is PRESENT
at 10.86x, so the EDGAR-absent branch is skipped, and the existing conflict branch sees 16.0/10.86 =
1.47x < 2x. Deeper root cause found: `_pe_reconciliation` checks the ANNUAL EPS (FY25 +1.02, in
line) and is BLIND to the LTM — but SMPL's LTM GAAP dil EPS is genuinely **−2.08** (LTM net income
**−$199M**, the $249M impairment inside the trailing window), verified as the STRUCTURED `values`
LTM cell of the 'EPS (GAAP, dil.)' row (not a display-cell misread — the −2.08 is the real LTM, not
a fiscal-year value). So the dossier printed EDGAR P/E 10.86x + CIQ P/LTM 16.0x + peers "P/E NM"
beside a −$199M LTM loss with no basis label. FIX: a new `_ltm_gaap_eps(financial_summary)`
structured reader + a sign-keyed `(d)` branch in `_eps_caveat_flags` — when the LTM GAAP dil EPS is
NEGATIVE and a positive trailing P/E multiple (EDGAR and/or CIQ) is shown, emit a caveat naming each
multiple; `(c)` demoted to the LTM-sign-UNAVAILABLE fallback (gated `ltm_gaap_eps is None`, no double
caveat). Real run on SMPL: BEFORE 0 flags → AFTER "EDGAR P/E 10.9x and CIQ P/LTM EPS 16.0x rest on
normalized/adjusted earnings — LTM GAAP diluted EPS is NEGATIVE (−2.08); do not read them as a GAAP
trailing multiple." Gate: ruff · `mypy --strict` (110) · 1051 passed. Pins: `_ltm_gaap_eps`
structured-read (values-win-over-cell, missing row/col/value → None) + the `(d)` guard across the
five shapes (both-present names both; EDGAR-only singular; CIQ-only no `(c)` double; positive-LTM
quiet; None → `(c)` fallback preserved). **General, not SMPL-specific** — any name whose LTM crossed
negative on a recent one-off while annual stays positive was slipping the same gap. The committed
SMPL dossier surfaces the caveat on the (now-superseding) step-2 re-assembly, run AFTER this merges.
