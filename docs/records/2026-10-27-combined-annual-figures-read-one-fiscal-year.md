---
status: shipped
date: 2026-10-27
prs: [821]
supersedes:
superseded-by:
---

# A combined annual figure reads both legs for ONE fiscal year, and no annual more than one fiscal year behind the filer is served as current — 132 FCF signs and 150 EBITDAs stop pairing two years; #817's open half closed

**WHAT.** Two rules in `vinci.edgar.concepts`, read by the screen's snapshot, the anchor and
the CIQ-empty fallback:
- **(a) `current_pair(facts, first, second)`.** A figure built from two annual legs reads both
  for the newest fiscal year they BOTH carry, same start and same end. It no longer reads each
  leg's own latest year. This is the CIQ-empty fallback's pairing, moved down so all three
  readers share it (`annual_by_period` moved with it unchanged). That year is judged on both
  counts below, and each leg also against its own concept, as #817 judges one annual.
- **(b) `behind_filer` / `FILER_STALE_DAYS` (700d = two shortest fiscal years).** A single leg's
  year, or a pair's shared year, may be at most ONE fiscal year behind the filer's newest fiscal
  year. Otherwise it is UNKNOWN, and the note names the year: "newest year both
  operating_cash_flow and capex carry ends 2019-12-31, 2192d behind the filer's newest fiscal
  year (Revenues to 2025-12-31) — more than one fiscal year behind".
  - `filer_fiscal_year` is the newest ANNUAL period any alias of the eight flow concepts
    carries. A period ending after its own filing date is skipped, as #817 did for NAPCO.
    The frontier of any tag is never used.
  - `current_annual` now applies (b) after #817's check. `StaleAnnual.against_filer` marks
    which check refused.

Readers:
- **Screen snapshot** (`client.compute_fundamental_snapshot`): FCF sign (operating cash flow −
  capex) and EBITDA (operating income + D&A) read `current_pair`. Net leverage forwards
  EBITDA's reason. The single-leg figures (operating-income sign, net debt / OCF, diluted EPS)
  read `current_annual`. Nothing else in the snapshot combines annual legs.
- **Anchor** (`anchor._latest_fcf`, rule (c)): reads `current_pair`. A refusal is named in
  `ltm_fcf.source` ("UNKNOWN — newest year both …"). The existing CIQ vendor fill still fills
  the hole when the workbook carries both legs.
- **Fallback** (`EdgarFundamentals.free_cash_flow`): reads `current_pair`. Its trajectories and
  margin series are unchanged.

**WHY.** #817 withheld an annual its own concept had been reported past. A concept that stopped
on EVERY alias passed: its newest period IS the served annual's. The snapshot then combined
each leg's own latest annual, so two fiscal years went into one number, and such a number never
existed. Johnson & Johnson's `OperatingIncomeLoss` ends at FY2014 and was added to FY2025 D&A.
SL Green's capex ends at FY2019 and came off FY2025 operating cash flow.

**One choice made in reading the design, flagged for the operator.** The design says a shared
year one fiscal year behind stays. I kept #817's per-leg check at the shared year, as the fallback
has applied it since #817. So a pair whose legs stop one year apart is REFUSED: the leg that moved
on has been reported past the shared year, and that year is not its current one.
- 52 pairs on the census are this shape (29 FCF, 23 EBITDA). Valero's capex ends at FY2024
  beside FY2025 operating cash flow; USA TODAY's operating income ends at FY2024 beside FY2025
  D&A.
- The other reading would serve them at FY2024. That loosens a merged rule, and it puts
  comparative rows under labels built from companyfacts' `fy` — the FILING's fiscal year, a
  defect #817 recorded (item 3). The anchor's FY2024 pair would read "latest FY2025".
- "One fiscal year behind stays" therefore holds for single figures, and for a pair whose two
  legs both stop there (none on the census). It is pinned on USA TODAY's FY2024 operating-income
  sign.
- If the operator wants the other reading, it is one line (`legs = ()` in `current_pair`, the
  M6 mutant below) plus a label fix.

**The threshold, by face validity.** Each annual the screen served on main, measured against
its filer's newest fiscal year:
- 8,811 at 0–29d;
- 10 at 60–299d (a 10-Q's trailing column, a transition period);
- 53 at 360–371d (one fiscal year behind);
- NOTHING from 372d to 727d;
- 273 at 728d or more.

700d sits in that gap. It is set by the gap, never by what a reading would have paid.

**HOW VERIFIED.**
- **Census first** (main 64f91b2a, shared cache, today's blob). It reproduces #817's open
  family exactly.
  - 410 served annuals in 346 filers sit more than 180d behind their filer's newest fiscal year.
  - 132 filers' FCF sign and 150 filers' EBITDA pair two different years.
- **BEFORE → AFTER, the same 2,161 blobs, nothing written.** Every move is PRESENT → UNKNOWN
  or a reworded UNKNOWN note, apart from one correction (Amazon, below). Nothing goes UNKNOWN →
  PRESENT.

  | field | PRESENT → UNKNOWN | value changed | UNKNOWN, note now names the year |
  |---|---|---|---|
  | `fcf_sign` | 132 | 0 | 32 |
  | EBITDA dollars | 149 | 1 | 27 |
  | `net_leverage` | 69 | 1 | 32 |
  | `op_income_sign` | 50 | 0 | 0 |
  | `net_debt_to_ocf` | 0 | 0 | 0 |
  | diluted EPS (no production reader) | 13 | 0 | 0 |
  | CIQ-empty fallback FCF | 0 | 0 | 159 |
  | anchor EDGAR FCF | 5 | 0 | 485 (a reason where there was none) |

  - **Data-record fields.** 208 filers' `fcf_sign`, `op_income_sign`, `net_leverage` or
    `net_debt_to_ocf` go PRESENT → UNKNOWN or change value (`candidate_records.jsonl` carries
    those fields).
  - **#817's family after:** 69 served annuals in 63 filers remain more than 180d behind, every
    one at 181–371d, one fiscal year (capex 25, D&A 12, operating income 10, EPS 9, the rest
    non-screen).
  - **What decides a pair refusal.** Every pair refused AT a shared year shows a leg whose own
    concept moved past that year. (b) also names the year in 125 FCF / 144 EBITDA notes and is
    never the sole reason on today's blobs. 5 FCF / 3 EBITDA pairs share no year at all and
    say so. (b) is decisive for single figures: 50 operating-income signs, 13 EPS.
  - **The one value change is a correction.** Amazon's EBITDA was FY2025 operating income
    ($79.975bn) plus D&A for the trailing year to 2026-06-30 ($75.2bn) = $155.18bn. Both legs
    are now FY2025: $79.975bn + $65.756bn = $145.73bn. Net leverage moves 0.153x → 0.163x.
  - **The anchor's 5:** FUBO, Starz, QuinStreet, Bally's and Skydance, the shape #817 named
    (every annual a fiscal year behind its quarters). Bally's and Skydance were labelled
    "latest FY2025" for the year to 2024-12-31: the `fy` defect above.
  - **The fallback's status moves on none.** #817's per-leg check already refused every pair
    this refuses; only the note changes.
- **No gate or ranker moves.** `vinci/screens/screen2.py` reads `ev_ebitda_pctile_vs_history`
  and nothing else from these records. No screen gate or `vinci/rank` reads `fcf_sign`,
  `op_income_sign`, `net_leverage`, `net_debt_to_ocf` or EBITDA dollars; grep over `vinci/`
  finds only their writer (`screens/assemble.py`) and the dossier. The fields feed the
  finalist's quality and survival lines (`mechanical._quality`, `_survival_capacity`,
  `render.py`). This changes what the human reads, not who passes.
- **Named cases:**

  | filer | figure | BEFORE | AFTER |
  |---|---|---|---|
  | Johnson & Johnson | EBITDA | $29.09bn (FY2014 op. income + FY2025 D&A) | UNKNOWN: "newest year both … carry ends 2014-12-28, 4018d behind the filer's newest fiscal year (… to 2025-12-28)" |
  | Johnson & Johnson | net leverage | 0.94x | UNKNOWN, the same reason |
  | Johnson & Johnson | op. income sign | +1 (FY2014) | UNKNOWN, 4,018d behind |
  | Johnson & Johnson | FCF sign, anchor FCF | +1; $19.70bn FY2025 | unchanged (a current pair) |
  | SL Green | FCF sign | −1 (FY2025 OCF − FY2019 capex) | UNKNOWN, names 2019-12-31, 2,192d behind |
  | SL Green | anchor FCF | UNKNOWN, no reason | UNKNOWN, the same note |
  | SL Green | EBITDA | $914.7M FY2025 | unchanged (a current pair) |

- **The 27 committed pages.** Each was read as filed by its own `assembled_at` and on today's
  blob; both agree. One moves where a reader sees it: **FUBO**.
  - Its anchor `ltm_fcf` ("operating_cash_flow − capex (FY2024, same period)", −$82.2M) becomes
    UNKNOWN, naming the year to 2024-12-31. On re-assembly the existing CIQ vendor fill supplies
    a stamped vendor-basis figure if FUBO's workbook carries both cash-flow legs; that was not
    checked here (the workbook is git-ignored).
  - No sealed scenario record exists for FUBO.
  - Its `fcf_sign` → UNKNOWN is #817's move; only the note is reworded here.
  - Three pages compute differently in fields they do not show:
    - AMZN: EDGAR EBITDA and net leverage. The page shows CIQ's 0.8x.
    - TJX: operating-income sign and EDGAR net leverage. `OperatingIncomeLoss` ends at FY2018;
      the page shows CIQ's 0.9x and renders no operating-income sign.
    - ORKA: EBITDA dollars, no page reader.
  - IT's and LLY's anchor text is unchanged.
  - **No page is re-assembled here**; they refresh in the November artifact pass.
- **Pins: 12 new** (`tests/test_annual_pairs.py`), on 8 frozen real filers
  (`tests/fixtures/annual_pairs/`, README there; each subset checked against the full blob at
  cut time).
  - **Positive:** J&J EBITDA, net leverage and op. income sign; SL Green FCF sign and anchor
    FCF; the fallback's note; Valero FCF and USA TODAY EBITDA, a pair a year apart with one
    leg moved on; FUBO's anchor `ltm_fcf` read off `_bridge_inputs`.
  - **Negative:** J&J's FCF and SL Green's EBITDA, current pairs. Amazon's EBITDA reads one
    period. USA TODAY's FY2024 operating-income sign, one fiscal year behind, stays. The
    threshold sits in the gap. Daily Journal as filed 2013-08-14: a forward-dated context (its
    10-Q tags the year to 2013-09-30) does not date the fiscal year, so its FY2011 EPS ($5.68)
    is served. Innodata: a 2034 share-option context is its frontier, not its fiscal year.
  - **#817's falsifier** (`test_a_concept_stopped_on_every_alias_is_not_caught_and_says_so`)
    reddened as it was written to, and is now
    `test_a_concept_stopped_on_every_alias_is_withheld_against_the_filer`.
- **Mutation: 14 mutants in a scratch copy of the tree, 14 killed:**
  - M1: pair each leg's own latest year.
  - M2: threshold at one fiscal year (350d).
  - M3: rule (b) off.
  - M4: (b) dropped for single legs.
  - M5: (b) dropped for pairs.
  - M6: the per-leg check dropped at the shared year.
  - M7: forward-dated annuals counted.
  - M8: the filer's frontier of any tag.
  - M9: any duration dates the fiscal year (killed through the note's fiscal year).
  - M10: the anchor's old rule.
  - M11: net leverage's plain-absence note.
  - M12: the fallback's old body.
  - M13, M14: the snapshot's FCF and EBITDA reading each leg's current annual.
- **Suite:** ruff + `mypy --strict vinci` clean, `pytest -m "not network"` 6,936 passed, 533 skipped, 0 failed (the final code, with this record and STATE.md).

**BOUNDARY.**
- **Census:** the shared SEC cache `/Users/work/Documents/GitHub/mosaic-theory-ta/data/cache/sec`,
  read-only.
  - 2,161 companyfacts, fetched 2026-08-12..2026-10-26; 2,008 carry an annual flow period.
  - No `filed_by` cut (today's blob). BEFORE is main 64f91b2a, AFTER this branch. Measured
    2026-10-27.
- **Units:**
  - the field-move counts: one filer;
  - #817's family: one (filer, flow concept) served annual;
  - the threshold gap: one served screen leg (operating income, D&A, OCF, capex, EPS);
  - the 52 pairs: one (filer, FCF | EBITDA).
- **Lag:** a served annual's (or shared year's) period end to the filer's newest fiscal year's
  period end. The newest fiscal year is the newest annual period (350–380d) of the eight flow
  concepts' aliases, period end on or before filed.
- **Pages:** the 27 under `data/dossiers/` at 64f91b2a, each as filed by its own `assembled_at`
  (2026-08-18 … 2026-10-26) and on today's blob.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The one-year-apart pairs are refused** (52 on the census): the choice above. Its falsifier
   is `test_a_pair_a_year_apart_goes_unknown_when_one_leg_moved_on`, which reddens if the
   operator rules the other way.
2. **A served figure one fiscal year behind does not say so.** The snapshot's PRESENT fields
   carry a filing date, not a period. 17 single figures in 16 filers (operating-income sign 9,
   EPS 8) are served for the year before the filer's newest. That is the design. A note naming
   the year would be one line per field, but no field carries such a note today, and adding one
   changes what pages print. Not done here.
3. **Seen, not fixed — `fy` labels a comparative with the filing's fiscal year.** This is #817's
   item 3, met again in the anchor (`anchor._period_label`): Bally's and Skydance's year to
   2024-12-31 read "latest FY2025". They are withheld now, so no served label is wrong on
   today's census, but the label function is unchanged.
4. **The anchor's D&A (`_latest_dep_amort`) picks by vintage with no staleness check.** A D&A
   stopped on every alias would still be served there. Out of this brief's scope (it names
   `_latest_fcf`); reported, not fixed.
