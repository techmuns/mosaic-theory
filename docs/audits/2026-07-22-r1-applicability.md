# R1 APPLICABILITY AUDIT — 2026-07-22

Read-only. Flags PRINT, never block (the linter model): the machine surfaces, the human concludes.

## Ratified thresholds

- growth-era-only band: `min/median >= 0.55`
- short band: `span < 3.0y` OR `< 12 closes`
- margin median unusable: FY spread > 8%, sustained ramp > 3%, or a negative median
- leverage: net debt > 50% of anchor equity; one turn > 30% of spot
- bear admissibility: bear multiple above the CURRENT multiple (loud), or above the band minimum (note)

## Dispositions

- **AORT** — gate exists and FIRED — via R2_NEEDED (2 flags)
- **BRBR** — clean
- **CNXC** — gate exists and FIRED — via R1_NOT_ROBUST (3 flags)
- **EPAM** — *** NO GATE — new exposure (1 flag)
- **FUBO** — gate exists and FIRED — via anchor not applicable, unknown (3 flags)
- **IT** — *** NO GATE — new exposure (2 flags)
- **MVST** — gate exists and FIRED — via anchor not applicable, R2_NEEDED (3 flags)
- **NCNO** — gate exists and FIRED — via anchor not applicable, R2_NEEDED (2 flags)
- **SMPL** — *** NO GATE — new exposure (1 flag)
- **VITL** — gate exists and FIRED — via band_incoherent+band_unreconciled, anchor not applicable, R2_NEEDED (2 flags)

## Matrix

### AORT — gate exists and FIRED

- `margin` — stable: n=10 med 5.1% spread 11.7% shift -2.6%
- `band` — 42q / 10.3y from 2016-03-31 · min 18.75 med 32.11 cur 20.58 · min/med 0.58
- `bear` — 9.0x · bear_basis=analyst margin_basis=EBIT
- `leverage` — net debt 202.4 = 18.6% of anchor equity · 1 turn = $0.81 = 3.2% of spot
- `perimeter` — 0 dated M&A mention(s); event_impacts empty on 6/6 releases
- `entity` — diluted 49,731,000 vs outstanding 48,543,350 · gap 0.98x
- `data` — guards=clean · d_and_a[consolidated latest FY] · ltm_fcf[absent]
  - **FLAG**: FY margin spread 11.7% exceeds 8% — the median averages two regimes
  - **FLAG**: GROWTH-ERA-ONLY band: min/median 0.58 >= 0.55 — the window never visits a bear state
  - note: event_impacts EMPTY on every release — this check is running on a text scan, not on structured capture

### BRBR — clean

- `margin` — stable: n=9 med 16.3% spread 7.4% shift +2.1%
- `band` — 27q / 6.6y from 2019-12-31 · min 4.29 med 19.76 cur 8.19 · min/med 0.22
- `bear` — no scenario record
- `leverage` — net debt 1,181.9 = 18.0% of anchor equity · 1 turn = $3.31 = 25.1% of spot
- `perimeter` — 0 dated M&A mention(s); event_impacts empty on 1/1 releases
- `entity` — diluted 118,700,000 vs outstanding 116,277,850 · gap 0.98x
- `data` — guards=clean · d_and_a[consolidated latest FY] · ltm_fcf[absent]
  - note: event_impacts EMPTY on every release — this check is running on a text scan, not on structured capture

### CNXC — gate exists and FIRED

- `margin` — stable: n=4 med 7.7% spread 4.5% shift -1.5%
- `band` — 23q / 5.6y from 2020-12-31 · min 4.39 med 6.89 cur 3.88 · min/med 0.64
- `bear` — no scenario record
- `leverage` — net debt 5,248.7 = 138.6% of anchor equity · 1 turn = $21.47 = 100.4% of spot
- `perimeter` — 0 dated M&A mention(s); event_impacts empty on 0/0 releases
- `entity` — diluted 61,078,000 vs outstanding 61,018,350 · gap 1.00x
- `data` — guards=clean · d_and_a[consolidated latest FY] · ltm_fcf[absent]
  - note: thin history: 4 completed FYs
  - **FLAG**: GROWTH-ERA-ONLY band: min/median 0.64 >= 0.55 — the window never visits a bear state
  - **FLAG**: net debt 139% of anchor equity exceeds 50%
  - **FLAG**: ONE TURN of multiple = 100% of spot (over 30%) — the multiple IS the valuation

### EPAM — *** NO GATE — new exposure

- `margin` — stable: n=9 med 13.2% spread 4.0% shift -1.0%
- `band` — 38q / 9.3y from 2017-03-31 · min 4.26 med 22.41 cur 4.87 · min/med 0.19
- `bear` — 6.0x · bear_basis=own-history margin_basis=EBIT
- `leverage` — net debt -749.0 = -4.1% of anchor equity · 1 turn = $14.50 = 16.9% of spot
- `perimeter` — 0 dated M&A mention(s); event_impacts empty on 0/0 releases
- `entity` — diluted 54,183,000 vs outstanding 52,244,451 · gap 0.96x
- `data` — guards=clean · d_and_a[consolidated latest FY] · ltm_fcf[latest FY2025 (not LTM)]
  - **FLAG**: BEAR MULTIPLE ABOVE CURRENT: 6.00x vs 4.87x — the downside case assumes a re-rating UP
  - note: bear multiple 6.00x above the band minimum 4.26x
  - note: ltm_fcf is latest FY2025 (not LTM) — not a trailing twelve months

### FUBO — gate exists and FIRED

- `margin` — stable: n=4 med -4.1% spread 1.7% shift +0.6%
- `band` — NO COMMITTED BAND
- `bear` — no scenario record
- `leverage` — anchor not applicable — no base value published (guard behaviour)
- `perimeter` — 0 dated M&A mention(s); event_impacts empty on 3/3 releases
- `entity` — diluted 30,049,437 vs outstanding 342,433,118 · gap 11.40x
- `data` — guards=clean · d_and_a[consolidated latest FY] · ltm_fcf[latest FY2024 (not LTM)]
  - **FLAG**: median FY margin is NEGATIVE (-4.1%) — no mid-cycle margin exists to revert to
  - note: thin history: 4 completed FYs
  - **FLAG**: no committed multiple band — R1 has nothing to revert to
  - note: event_impacts EMPTY on every release — this check is running on a text scan, not on structured capture
  - **FLAG**: diluted-vs-outstanding gap 11.40x — per-share math may be on the wrong share base
  - note: ltm_fcf is latest FY2024 (not LTM) — not a trailing twelve months

### IT — *** NO GATE — new exposure

- `margin` — ramp: n=9 med 18.1% spread 16.7% shift +11.1%
- `band` — 38q / 9.3y from 2017-03-31 · min 7.46 med 23.38 cur 7.97 · min/med 0.32
- `bear` — 7.5x · bear_basis=bear-state-comps margin_basis=EBIT
- `leverage` — net debt 1,688.2 = 6.9% of anchor equity · 1 turn = $15.94 = 11.3% of spot
- `perimeter` — 2 dated M&A mention(s); event_impacts empty on 5/5 releases
- `entity` — diluted 69,965,000 vs outstanding 66,951,889 · gap 0.96x
- `data` — guards=clean · d_and_a[consolidated latest FY] · ltm_fcf[free cash flow]
  - **FLAG**: FY margin spread 16.7% exceeds 8% — the median averages two regimes
  - note: bear multiple 7.50x above the band minimum 7.46x
  - **FLAG**: perimeter event detected — check whether trailing facts straddle it: EBITDA-basis triangulation (each leverage basis-labeled):
  net debt / EBITDA (C
  - note: event_impacts EMPTY on every release — this check is running on a text scan, not on structured capture

### MVST — gate exists and FIRED

- `margin` — ramp: n=8 med -34.3% spread 141.2% shift +33.8%
- `band` — 6q / 1.3y from 2025-03-31 · min 9.98 med 19.31 cur 8.95 · min/med 0.52
- `bear` — 6.0x · bear_basis=ABSENT margin_basis=ABSENT
- `leverage` — anchor not applicable — no base value published (guard behaviour)
- `perimeter` — 0 dated M&A mention(s); event_impacts empty on 4/4 releases
- `entity` — diluted 385,272,000 vs outstanding 333,157,384 · gap 0.86x
- `data` — guards=clean · d_and_a[consolidated latest FY] · ltm_fcf[latest FY2025 (not LTM)]
  - **FLAG**: median FY margin is NEGATIVE (-34.3%) — no mid-cycle margin exists to revert to
  - **FLAG**: SHORT band: 1.3y / 6 closes (floor 3.0y / 12)
  - **FLAG**: bear_basis ABSENT — the multiple's provenance is unstated
  - note: event_impacts EMPTY on every release — this check is running on a text scan, not on structured capture
  - note: ltm_fcf is latest FY2025 (not LTM) — not a trailing twelve months

### NCNO — gate exists and FIRED

- `margin` — ramp: n=9 med -20.4% spread 35.2% shift +24.0%
- `band` — 10q / 2.3y from 2024-03-28 · min 25.76 med 82.91 cur 27.84 · min/med 0.31
- `bear` — 10.0x · bear_basis=peer-reference margin_basis=EBIT
- `leverage` — anchor not applicable — no base value published (guard behaviour)
- `perimeter` — 0 dated M&A mention(s); event_impacts empty on 0/0 releases
- `entity` — diluted 109,458,472 vs outstanding 109,552,950 · gap 1.00x
- `data` — guards=clean · d_and_a[consolidated latest FY] · ltm_fcf[latest FY2026 (not LTM)]
  - **FLAG**: median FY margin is NEGATIVE (-20.4%) — no mid-cycle margin exists to revert to
  - **FLAG**: SHORT band: 2.3y / 10 closes (floor 3.0y / 12)
  - note: ltm_fcf is latest FY2026 (not LTM) — not a trailing twelve months

### SMPL — *** NO GATE — new exposure

- `margin` — stable: n=4 med 16.9% spread 0.9% shift -0.3%
- `band` — 35q / 8.6y from 2017-12-29 · min 6.11 med 17.85 cur 5.65 · min/med 0.34
- `bear` — 7.0x · bear_basis=own-history margin_basis=EBIT
- `leverage` — net debt 324.6 = 8.2% of anchor equity · 1 turn = $2.56 = 20.0% of spot
- `perimeter` — 0 dated M&A mention(s); event_impacts empty on 0/0 releases
- `entity` — diluted 93,677,801 vs outstanding 88,460,545 · gap 0.94x
- `data` — guards=clean · d_and_a[consolidated latest FY] · ltm_fcf[absent]
  - note: thin history: 4 completed FYs
  - **FLAG**: BEAR MULTIPLE ABOVE CURRENT: 7.00x vs 5.65x — the downside case assumes a re-rating UP
  - note: bear multiple 7.00x above the band minimum 6.11x

### VITL — gate exists and FIRED

- `margin` — ramp: n=4 med 8.8% spread 10.4% shift +3.5%
- `band` — 24q / 5.8y from 2020-09-30 · min 1.27 med 4.20 cur 1.48 · min/med 0.30
- `bear` — no scenario record
- `leverage` — anchor not applicable — no base value published (guard behaviour)
- `perimeter` — 0 dated M&A mention(s); event_impacts empty on 6/6 releases
- `entity` — diluted 44,587,704 vs outstanding 42,848,454 · gap 0.96x
- `data` — guards=band_incoherent+band_unreconciled · d_and_a[consolidated latest FY] · ltm_fcf[absent]
  - **FLAG**: FY margin spread 10.4% exceeds 8% — the median averages two regimes
  - note: thin history: 4 completed FYs
  - note: event_impacts EMPTY on every release — this check is running on a text scan, not on structured capture
  - **FLAG**: band guard(s) tripped: band_incoherent+band_unreconciled

