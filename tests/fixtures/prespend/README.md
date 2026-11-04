# Pre-spend check fixtures

The check's own $0 builds (`vinci dossier precheck`, `vinci/dossier/prespend.py`), frozen as
written. Each one is the mechanical layer only: no synthesis, no LLM phase. These track no page and
are never regenerated. Refreeze one only together with the pins that read it.

| file | built | from | what is pinned on it |
|---|---|---|---|
| `2026-11-04/SMPL-mechanical.json` | 2026-11-04 by `prespend.mechanical_build("SMPL")`, serialised with `dossier_json` | the operator's 2026-11-04 CIQ exports (Financials annual `cc99900b61`, quarterly `3a3e2873fa`, Estimates `fd3fbcf38f`, comps `647fa70755`), code at main `cfedcb39` plus this check, and a copy of the store the paid run `4f30d3a2` used (SMPL and IWM bars to 2026-11-03; SPY, GOOGL, LLY and AMZN refreshed to 2026-11-02 afterwards for the GOOGL check — the same 13 regressions before and after) | against `frozen_pages/2026-08-18/SMPL/`: the 12 fields the paid 2026-11-04 page lost, plus `ev_bridge` (`test_prespend.py`) |
| `2026-11-04/SMPL-forecast.json` | the same run, `prespend.forecast_llm_fields` | the build above, with SEC reads live | the forecast for the three LLM-written `capital_structure` fields: no call reaches a model, so `covenant_term_rows` is absent (both credit exhibits refused as "not a debt agreement") |
