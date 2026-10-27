---
status: shipped
date: 2026-10-27
prs: [817]
supersedes:
superseded-by:
---

# An annual reader withholds an annual its own concept has been reported past by a fiscal year — 120 served annuals in 78 cached filers, the six of 2026-10-26 among them; a concept stopped on every alias is still served, and that family is larger

**WHAT.** `vinci.edgar.concepts.current_annual(facts, concept)` returns the latest annual an annual
reader may serve AS CURRENT, or withholds it as a `StaleAnnual` naming both ends: the served
alias's annual and the newest period ANY alias of that concept carries. It is withheld when that
newer period ends `ANNUAL_STALE_DAYS` (= `ANNUAL_MIN_DAYS`, 350) or more after the annual: a whole
fiscal year has then closed past it and been reported. Two readers go through it:
- **The screen's snapshot** (`client.compute_fundamental_snapshot`): every annual leg
  (operating income, D&A, OCF, capex, diluted EPS). A withheld leg makes what it feeds UNKNOWN,
  and the note names it (`stale annual capex: PaymentsToAcquireProductiveAssets for the year to
  2019-12-31, 2373d behind PaymentsToAcquirePropertyPlantAndEquipment to 2026-06-30 — not the
  current year`). Net leverage and net debt / OCF forward that reason instead of "no EBITDA in
  XBRL" / "no operating cash flow in XBRL", which would send a reader looking for a missing tag.
- **The CIQ-empty FCF fallback** (`EdgarFundamentals.free_cash_flow`): it keys by period, so it
  never mixed years, but it served the latest year both legs share however old. That year is
  now judged against both legs' concepts.

`extract_points`, `_resolve`, `stale_served` and every quarterly reader are unchanged.

**WHY.** `extract_points` chooses an alias by how far its ANNUAL series reaches against its
siblings' (`SIBLING_LAG_DAYS`, 200). That is the right question for picking an alias and the
wrong one for "is this annual current": a filer that moves its annual to another tag, or stops
tagging the annual while still tagging quarters, leaves the walk serving a year that closed long
ago, and `latest_annual` takes it. Row 11 measured six such cases on 2026-10-26.

**The choice, by face validity.** The brief offered two: finish wiring `stale_served` with an
annual-grain threshold, or add a new check. `stale_served` measures the served alias's newest
point of ANY duration against the FILER's frontier (every tag). Both halves fail here:
- **Any duration:** AbCellera and KalVista still tag quarters on the served alias, so their lag
  (307d, 219d) sits under its 550d while the annual is two years old.
- **The filer's frontier:** it is any tag at all, including future-dated contexts. 28 of the
  2,161 cached filers have a frontier after 2026-10-27; Innodata's reaches 2034-03-31. Measured
  that way at annual grain (>550d), 645 served annuals in 410 filers trip. Of the 561 that their
  concept's own newest period does not explain, 142 sit under a frontier dated after
  2026-10-27.

The concept's OWN newest period is free of both: a later period of the same concept is the filer
saying, in its own filing, that this concept moved on. The census shows a clean gap. 14,791 of
14,918 served annuals trail their concept's newest period by at most 280d, a third-quarter 10-Q
in a 53-week year. Next are KalVista's seven at 335d: an eight-month transition period, after
which its last full year IS its newest annual. Nothing else sits below 365d. So the threshold is
the shortest fiscal year: above 335, at most 364 (a 52-week year one fiscal year behind). It is
set by that gap, never by what a reading would have paid.

**`stale_served` is kept, unwired** — not the dead path this replaces. It is the only reporter of
a stale INSTANT tag (V's 2010 cover-page share count, VITL's 2020 current debt), which an annual
check cannot see. Wiring it is row 11's first half (it needs companyfacts in the monitor), still
ACCEPTED.

**HOW VERIFIED.**
- **Census first, before any code** (main 47d8ca27, shared cache). It reproduces row 11:
  - 62 (filer, concept) cases in 60 filers where a skipped higher-priority alias carries a newer
    period.
  - 6 of them serve an annual more than 365d behind it. Climb Global capex FY2019 (2,373d),
    SL Green pre-tax FY2017 (2,282d), Comstock capex FY2023 (912d), DiamondRock D&A FY2017
    (3,103d), AbCellera D&A FY2023 (912d), KalVista revenue to 2024-04-30 (700d).
  - `stale_served` names 4 of them, not AbCellera or KalVista.
- **The check's own population is wider than that census, and is the same defect.** 120
  (filer, flow concept) in 78 filers serve an annual 350d or more behind their concept's newest
  period. Only 6 of the 120 are the higher-priority shape. 8 are a lower-priority alias that
  moved on. 106 are the served alias itself still carrying quarters with no annual since. One of
  them: Triumph Financial's capex alias has no annual after FY2014 but quarters to 2026-06-30,
  so the screen read its FY2014 capex.
- **BEFORE → AFTER, the same 2,161 blobs, today's blob, nothing written.** BEFORE, all 120 were
  served as current. AFTER, `current_annual` withholds exactly those 120 (lag 365..4,199d). By
  concept: capex 31, D&A 18, operating income 16, pre-tax 16, diluted EPS 14, revenue 14, OCF 6,
  net income 5.
  - **Screen data-record** (`fcf_sign`, `op_income_sign`, `net_leverage`, `net_debt_to_ocf`, the
    fields `candidate_records.jsonl` carries): 50 filers move. FCF sign 32, operating-income
    sign 16, net leverage 18 (13 PRESENT → UNKNOWN, 5 a reason that now names the stale leg),
    net debt / OCF 5 (4 + 1). EBITDA dollars: 26 PRESENT → UNKNOWN. Diluted EPS: 14, but the
    snapshot's EPS has no production reader; P/E reads its own series with its own age guard.
  - **No screen gate moves.** G1–G3 read drawdown, relative return and the multiple
    percentiles; none reads these fields.
  - **The CIQ-empty FCF fallback:** 159 filers PRESENT → UNKNOWN. That is more than the
    snapshot, because the fallback's latest year must be shared by both legs. Where capex
    stopped on every alias, that shared year is old, and the OCF leg's own concept has moved
    on. SL Green's was 2019.
  - **Every move is PRESENT → UNKNOWN, or a note naming the stale leg.** No value changed to
    another value.
- **The six, screen inputs before → after** (the snapshot on today's blob):

  | filer | stale leg | field | BEFORE | AFTER |
  |---|---|---|---|---|
  | Climb Global | capex FY2019 | `fcf_sign` | +1 (FY2025 OCF − FY2019 capex) | UNKNOWN, names capex FY2019 |
  | Comstock | capex FY2023 | `fcf_sign` | −1 (FY2025 OCF − FY2023 capex) | UNKNOWN, names capex FY2023 |
  | AbCellera | D&A FY2023 | EBITDA | −$192.7M (FY2025 op. income + FY2023 D&A) | UNKNOWN; op. income sign stays −1 |
  | DiamondRock | D&A FY2017, op. income FY2017 | `op_income_sign`, EBITDA, `net_leverage` | +1, $238.9M, 4.16x (2026 net debt / FY2017 EBITDA) | all UNKNOWN, both legs named |
  | SL Green | pre-tax FY2017 | — | no annual reader takes pre-tax | withheld at `current_annual`; the fallback FCF (2019, labelled "FY2021") → UNKNOWN |
  | KalVista | revenue to 2024-04-30 | — | read only by the fallback's trajectories | withheld at `current_annual`; no snapshot field moves |

  DiamondRock's operating income was not in row 11's six. Its `OperatingIncomeLoss` carries
  quarters to 2020-12-31 with no annual after FY2017, so it is withheld too (1,096d).
- **The 27 committed pages, each as filed by its own `assembled_at` and on today's blob:
  1 moves on re-assembly.** FUBO moved its fiscal year to end in September. Its newest annual is
  calendar 2024, against quarters into FY2026, so every annual leg is withheld (546d), and its
  page's `fcf_sign` (−1) becomes UNKNOWN. The survival line's "FCF-negative → burning cash"
  reads that sign. ORKA moves only the snapshot's EPS, which no page reads. **No page is
  re-assembled here.** FUBO refreshes in the November pass after the CIQ re-exports.
- **Pins: 22, on frozen real filers** (`tests/fixtures/stale_annual/`, cut 2026-10-27 from the
  shared cache, the README there). Each of the six is withheld with both ends named. PennyMac
  revenue, exactly one fiscal year behind (365d), is withheld. The threshold sits in the gap.
  Then, end to end through `compute_fundamental_snapshot`: Climb/Comstock `fcf_sign`, AbCellera
  EBITDA with its current operating-income sign kept, and DiamondRock net leverage over a real
  $993M net debt naming both legs. The fallback FCF covers Climb and SL Green refused,
  AbCellera's FY2025 pair served.
  - **Negative pins:** five current annuals on those same filers. ScanSource is an alias switch
    with a CURRENT annual: the plain tag outranks the served continuing-operations tag and
    carries 2026-03-31, and the year to 2025-06-30 is 274d behind and served. KalVista's
    transition period is not a fiscal year.
  - **The gap pin:** SL Green's capex is pinned as NOT caught (the falsifier, below).
- **Found in review (`/code-review high`), fixed behind pins that failed first:**
  - **A forward-dated context counted as a reported period.** 61 flow-alias points in 18 of the
    2,161 cached filers end AFTER the day they were filed. NAPCO's 10-Q filed 2025-05-05 tags net
    income for 2025-01-01..2025-09-30. As filed by that date, the current year to 2024-06-30 was
    withheld (457d), and so was Ionis's 2024 EPS as of 2025-07-30 and Morningstar's 2019 net income
    as of 2020-10-30. `concept_frontier` now skips a period ending after its own filing date.
    Today's blob withholds the same 120 either way; every snapshot and page result above is
    byte-identical before and after this fix. Pin:
    `test_a_forward_dated_context_is_not_a_reported_period`.
  - **Net debt / OCF's stale reason was unpinned.** A mutant reverting it to "no operating cash
    flow in XBRL" survived. Pinned on Greif: a real $748.6M net debt over OCF for the year to
    2024-10-31, which read 2.10x.
  - Not changed: `current_annual` parses each alias twice (once in the walk, once for the
    frontier). That is cheap beside the walk's full-blob frontier scan, and sharing the parse means
    reshaping `_resolve`. The snapshot's `as_of` now leaves out the filing dates of withheld legs,
    which is intended: it dates what was read.
- **Mutation, 10 mutants in a scratch copy of the tree, 10 killed:**
  - the served alias's newest point only (`stale_served`'s grain);
  - strictly more than a year (>365d);
  - `stale_served`'s 550d;
  - 280d, inside the normal band;
  - the screen's capex leg read unguarded;
  - the withheld leg not named;
  - the fallback judged on its capex leg only;
  - the filer's frontier in place of the concept's;
  - forward-dated points counted;
  - net debt / OCF's plain-absence note.
- **Suite:** ruff + `mypy --strict` clean, `pytest -m "not network"` 6,907 passed, 528 skipped, 0 failed (the final code, with this record and STATE.md).

**BOUNDARY.**
- **Census and before/after runs:** the shared SEC cache
  `/Users/work/Documents/GitHub/mosaic-theory-ta/data/cache/sec`, read-only. 2,161 companyfacts
  (fetched 2026-08-12..2026-10-26), of which 2,027 carry at least one flow concept. No `filed_by`
  cut (today's blob). BEFORE is main 47d8ca27, AFTER is this branch.
- **Unit:** one (filer, flow concept) for the census, and one filer for the field moves. The
  eight flow concepts are revenue, operating income, pre-tax income, net income, diluted EPS,
  OCF, capex and D&A.
- **Lag:** the served annual's period end to the newest period end any alias of the same concept
  carries, any duration. Measured 2026-10-27.
- **Pages:** the 27 under `data/dossiers/` at 47d8ca27, each as filed by its own `assembled_at`
  (2026-08-18 … 2026-10-26).
- **Fixtures:** 10 filers, fetched 2026-08-13 (Greif 2026-09-17; PennyMac and NAPCO 2026-09-23).
  Tags subset to the concepts each pin reads, plus `net_debt.READ_TAGS` for DiamondRock and
  Greif.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **OPEN — a concept stopped on EVERY alias is still served as current.** Its newest period IS
   the served annual's, so this check cannot see it. Measured against the filer's newest fiscal
   year instead (the newest annual any flow concept carries, period end on or before filed),
   410 served annuals in 346 filers trail it by more than 180d and are not withheld. 307 of
   them, in 274 filers, are screen legs: capex 133, D&A 113, operating income 60, OCF 1.
   - The screen still pairs years: 132 filers' FCF sign and 150 filers' EBITDA come from
     different fiscal years. Johnson & Johnson's `OperatingIncomeLoss` stops at FY2014,
     and is served beside FY2025 D&A. SL Green's capex is FY2019 beside FY2025 OCF.
   - **Two cheap closures exist; both are operator calls**, because ~275–350 names' screen
     inputs move.
     - (a) Pair the snapshot's legs on ONE period, as `anchor._latest_fcf` and the fallback
       already do ("an FY2025 OCF net of FY2024 capex is a number that never existed").
     - (b) Also measure against the filer's newest fiscal year. Its distribution separates at
       180d: 14,417 at 0–29d, 14 between 60d and 299d, then 487 at 360d or more.
   - Falsifier: `test_a_concept_stopped_on_every_alias_is_not_caught_and_says_so` reddens when
     either lands.
2. **`anchor._latest_fcf` reads `latest_annual` unguarded** (`vinci/dossier/anchor.py`, lane
   L2's file, not touched here). It requires one period, so it never mixes years, but it serves
   a pair both of whose legs are stale. FUBO's committed anchor carries "operating_cash_flow −
   capex (FY2024, same period)", and the R2 survival gate divides cash by that FCF when it is
   negative. The fix is one call (`current_annual` for each leg). Handed to L2.
3. **Seen, not fixed — the fallback labels a period with the FILING's fiscal year.**
   `edgar_fundamentals._period_label` prints `FY{fy}`, and companyfacts' `fy` is the fiscal year
   of the filing that reported the row, not of the period. So a comparative reads as a later
   year: Climb's 2019 FCF printed "[FY2020]", SL Green's "[FY2021]", DiamondRock's 2013
   "[FY2015]". The label understated exactly the staleness this record is about.
4. **A filer whose newest annual on EVERY concept is a fiscal year behind its quarters loses
   all its annual inputs** until a new full year is filed. 38 of the 120 are five such filers:
   FUBO, Starz, Greif, QuinStreet and Skydance. FUBO's is a fiscal-year change to September;
   the other four were not examined one by one. Their newest annual is genuinely not the current
   year, so UNKNOWN is the honest read, and it is the read FUBO's page will take.
