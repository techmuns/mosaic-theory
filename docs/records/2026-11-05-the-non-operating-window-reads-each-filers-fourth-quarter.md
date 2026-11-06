---
status: open
date: 2026-11-05
prs: []
---

# The non-operating read's trailing four quarters include each filer's fiscal Q4. The window skipped it on every committed page whose window spans one, because none of those 10-Ks tags a Q4 duration, and it reached a year back instead

**WHAT.** `mechanical._nonop_window` builds the one window that the non-operating sentence
(`quality.nonoperating_earnings`) and its structured count (`quality.nonoperating_quarters`, which
feeds R4's condition 3) both read. It replaces `_nonop_common(...)[-4:]`, which was the newest four
quarters with an 80-100-day fact for operating income, pre-tax income and revenue.

- **The quarters are the filer's calendar.** They are every period end a 10-Q or 10-K states as
  its own (`concepts.fiscal_calendar`), plus every ~quarterly fact's end, up to the reference date.
  Two ends within `filed_tiebreak.SAME_END_DAYS` (7 days) are one quarter, dated as the calendar
  dates it.
- **A missing total is derived.** Where no ~quarterly fact states a total, it is derived by
  `filed_tiebreak.filed_quarter`: the longer period ending there less the period one quarter
  shorter from the same start, on one tag, with the shorter filed on or before the longer. For a
  fourth quarter that is the year less the nine months. The cite names both filings.
- **The end rule is unchanged.** The window ends at the newest quarter where all three totals are
  filed or derivable. The four quarters are the calendar's quarters ending there, within 300 days
  (`lease_basis._LTM_SPAN_DAYS`).
- **A short window says so.** If one of the four quarters cannot be read, the window is short. The
  count (`window`), the sentence ("3 available quarters of the trailing four … The window is
  short: …") and the cite all say so. No older quarter is read in its place.
- **A restated year is never paired with nine months filed before the restatement** (review round
  2). `filed_quarter` read the latest longer period and the latest shorter one filed on or before
  it. That alone does not make one basis. A 10-K/A, an 8-K recast or a later 10-K can restate the
  YEAR before any restated nine months exist, and the whole restatement then lands in the fourth
  quarter. The helper now reads such a quarter as missing, so the window is short. The fix sits in
  the helper, so #891's tiebreak reads it too.
  - **UBER.** Its FY2019 revenue was 14,147 in the 10-K and 13,000 in the 8-K recast of
    2021-01-14. Its nine months, 10,078, were filed before the recast. As filed by 2021-01-31,
    13,000 − 10,078 = 2,922 is on neither basis; as filed, the quarter was 4,069.
  - **The other cases the coordinator's reviewer found.** VRRM Q4-2020 pre-tax (a 10-K/A),
    FUBO Q4-2014 (operating income from a 2016 restatement) and FUBO Q4-2019 (a 10-K/A).
- **A derived revenue below zero is no quarter.** A quarter cannot sell less than nothing.
  - **The two negatives.** FUBO's quarter to 2019-12-31 read −1.563M as filed by 2020-08-15. Its
    quarter to 2024-12-31 read −777.2M, from a Q1-2025 10-Q fact dated as the whole of 2024; the
    restatement rule already refuses that one.
  - **A derived ZERO stands.** Both parts filed as 0 is a pre-revenue quarter. ORKA's page window
    holds three such quarters (2021), and FUBO's shell years hold more. The revenue arm already
    reads a zero denominator as undefined, never material. Refusing zero would push ORKA's window
    end back years, which is why the guard is `< 0` and not the review's `≤ 0`.
- **Extraction version** `2026-11-05.nonop-window-fourth-quarter` is recorded in both twins.
  The drift table is re-pinned; `mechanical.py` and `filed_tiebreak.py` moved.

**THE EXISTING HELPER WAS REUSED, NOT REWRITTEN.** I searched three vocabularies: "derived Q4 /
fourth quarter / implied Q4", "nine months / year-to-date / YTD", and "TTM / LTM / trailing four".
I also ran `git log -S"less the nine months"` (→ #891, #829, #634) and `git log -S"_quarter_cited"`
(→ #827). The searches found three derivations:

- `ebitda_recon._quarter_cited` returns $M. It pairs each part with its own latest filing and does
  not tie the two vintages together.
- `filed_tiebreak.filed_quarter` returns dollars, the derived flag and the parts.
  - **Since #891 round 2** (MVST's restated nine-month line, Codex's finding), its shorter part is
    never a later comparative: the shorter is filed on or before the longer.
  - **That rule alone does not tie the two parts to one basis.** A year restated after its nine
    months were filed still paired with them. That is round 2's fix here (above).
- `quality/sources/release._figures` belongs to the scorecard.

The window reuses `filed_quarter` and its `_quarter_ref` cite. No fourth derivation was added.

**WHY.** On 2026-11-04 the defect was measured on GOOGL's committed page (main `1b8a5a2f`). On
2026-11-05 it was re-measured on `c4c9f432`, and the old code reproduced every committed page's
count and sentence (below).

- **GOOGL.** Its FY2025 10-K (0001652044-26-000018) tags no Q4 duration. The window therefore read
  2025-09-30, 2026-03-31, 2026-06-30 and 2026-09-30: +$140,237M, 4 of 4 material. The trailing four
  replace 2025-09-30 with 2025-12-31, derived as follows ($M):
  - operating income 129,039 − 93,105 = 35,934;
  - pre-tax income 158,826 − 119,709 = 39,117;
  - revenue 402,836 − 289,007 = 113,829.

  That quarter's block is +$3,183M, 8.1% of pre-tax and 2.8% of revenue, under the 20% bar. The
  window is then +$130,661M, 3 of 4 material.
- **The whole corpus.** None of the 26 committed pages with a fiscal-year end among their six
  latest quarters tags a Q4 duration in its 10-K (§ BOUNDARY; FUBO, the 27th, has no fiscal-year
  end there). So every window that spanned a fiscal Q4 skipped it.
- **What it feeds.** `nonoperating_quarters.material` feeds R4's eligibility rule ("material in ≥2
  of the trailing four", `recipe_proposal.R4_MIN_MATERIAL_QUARTERS`).

**HOW VERIFIED.** All runs were $0: no assemble, no LLM, no network.

- **Old against new, on all 27 committed pages.** Each page ran at its own `reference_date`, on
  `tests/fixtures/companyfacts/<T>.json` as committed. "Old" is main's `vinci` exported from
  `c4c9f432`; "new" is this branch.
- **The harness is checked first.** The old code reproduced the committed `nonoperating_quarters`
  (material, window and source_ref) and the committed sentence on **27 of 27** pages. 13 of those
  27 carry no structured count, so for them only the sentence was compared.
- **BURL is included** since the operator's ruling of 2026-11-05 (verbatim: "i dont want mosaic
  theory to hold back any names for teamnostra repo, its two separate setups"). The first two
  runs here excluded it as a held audit pack, under the rule that ruling reverses.
- **The outcome.** 21 of 27 reads move, and **R4's proposal flips on none**:

| page | ref date | old window → new window | old Σ $M → new Σ $M | material old → new | derived | R4 c3 / proposed |
|---|---|---|---|---|---|---|
| AMZN | 2026-10-16 | 2025-09-30..2026-09-30 → 2025-12-31..2026-09-30 | +78,919 → +69,799 | 3/4 → **2/4** | 2025-12-31 | T/T → T/T |
| AORT | 2026-10-16 | 2025-06-30..2026-06-30 → 2025-09-30..2026-06-30 | −19.2 → −18.4 | 0/4 → 0/4 | 2025-12-31 | F → F |
| BURL | 2026-10-16 | UNKNOWN both (no quarterly operating income; its FY2025 10-K tags no Q4 for pre-tax or revenue either) | — | — | — | — |
| BRBR | 2026-10-16 | 2025-06-30..2026-06-30 → 2025-09-30..2026-06-30 | −78.4 → −79.1 | 0/4 → 0/4 | 2025-09-30 | F → F |
| CNXC | 2026-10-16 | 2025-08-31..2026-08-31 → 2025-11-30..2026-08-31 | −220.8 → −249.0 | 0/4 → 0/4 | 2025-11-30 | F → F |
| EPAM | 2026-08-24 | 2025-06-30..2026-06-30 → 2025-09-30..2026-06-30 | −11.8 → −14.5 | 0/4 → 0/4 | 2025-12-31 | F → F |
| FUBO | 2026-08-14 | unchanged (its new fiscal year ends in September; no derived quarter in the window) | +4.6 | 0/4 | — | F → F |
| GOOGL | 2026-10-16 | 2025-09-30..2026-09-30 → **2025-12-31**..2026-09-30 | **+140,237 → +130,661** | **4/4 → 3/4** | 2025-12-31 | T/T → T/T |
| IT | 2026-08-14 | 2025-06-30..2026-06-30 → 2025-09-30..2026-06-30 | −73.7 → −84.8 | 0/4 → 0/4 | 2025-12-31 | F → F |
| LLY | 2026-10-16 | UNKNOWN both (no quarterly operating income at all) | — | — | — | — |
| MVST | 2026-08-24 | 2024-09-30..2025-09-30 → 2025-03-31..**2025-12-31** | −86.9 → −41.5 | 4/4 → 4/4 | 2025-12-31 | F → F |
| NCNO | 2026-08-14 | UNKNOWN both (no quarterly pre-tax income) | — | — | — | — |
| NFLX | 2026-10-16 | 2025-09-30..2026-09-30 → 2025-12-31..2026-09-30 | +2,185.5 → +2,135.4 | 1/4 → 1/4 | 2025-12-31 | F → F |
| NKE | 2026-10-16 | UNKNOWN both (no quarterly operating income) | — | — | — | — |
| ORKA | 2026-10-16 | 2018-03-31, 2019-03-31, 2020-03-31 → 2021-06-30..2021-12-31, **short 3 of 4** | +0.093 → +0.011 | 0/3 → 0/3 | 2021-06-30, 09-30, 12-31 | F → F |
| PARR | 2026-10-16 | 2025-06-30..2026-06-30 → 2025-09-30..2026-06-30 | −68.0 → −53.4 | 0/4 → 0/4 | 2025-12-31 | F → F |
| ROST | 2026-10-16 | 2025-08-02..2026-08-01 → 2025-11-01..2026-08-01 | +130.8 → +132.6 | 0/4 → 0/4 | 2026-01-31 | F → F |
| SMPL | 2026-10-16 (#914's re-assembly, merged here at `9c78839a`; its 2026-08-14 page read the same) | 2025-03-01..2026-02-28 → 2025-05-31..2026-02-28 | −18.8 → −16.8 | 0/4 → 0/4 | 2025-08-30 | F → F |
| TECX | 2026-09-22 | UNKNOWN both (the three totals never share a quarter) | — | — | — | — |
| TGT | 2026-10-16 | 2025-08-02..2026-08-01 → 2025-11-01..2026-08-01 | −391 → −364 | 0/4 → 0/4 | 2026-01-31 | F → F |
| TJX | 2026-10-16 | 2017-10-28..2018-11-03 → 2018-05-05..**2019-02-02** | −546.1 → −590.0 | 0/4 → 0/4 | 2019-02-02 | F → F |
| UBER | 2026-10-16 | 2025-06-30..2026-06-30 → 2025-09-30..2026-06-30 | **+1,521 → −16** | **3/4 → 4/4** | 2025-12-31 (−$1,483M, itself material) | T/T → T/T |
| V | 2026-10-16 | 2025-03-31..2026-03-31 → 2025-06-30..2026-03-31 | +88 → +160 | 0/4 → 0/4 | 2025-09-30 | F → F |
| VITL | 2026-08-14 | 2025-06-29..2026-06-28 → 2025-09-28..2026-06-28 | +1.1 → +1.4 | 0/4 → 0/4 | 2025-12-28 | F → F |
| VRRM | 2026-08-14 | 2025-06-30..2026-06-30 → 2025-09-30..2026-06-30 | −41.5 → −41.0 | 1/4 → 1/4 | 2025-12-31 | F → F |
| WERN | 2026-08-24 | 2025-06-30..2026-06-30 → 2025-09-30..2026-06-30 | −35.6 → −37.2 | 0/4 → 0/4 | 2025-12-31 | F → F |
| WLK | 2026-10-16 | 2025-06-30..2026-06-30 → 2025-09-30..2026-06-30 | −69 → −45 | 0/4 → 0/4 | 2025-12-31 | F → F |

The R4 columns read as follows. For the 12 pages that carry no structured count, the "material"
column is the sentence's count. "c3" is condition 3; "proposed" is the full three-condition
proposal, judged on the committed page with R1 standing in as
`tests/test_r4_machine_proposal._r1` builds it. AMZN, GOOGL and UBER are proposed under both
windows, and no other page is.

**AMZN NOW SITS EXACTLY AT CONDITION 3's THRESHOLD: 2 material quarters of 4, against the ruled
≥2.** Its two material quarters are 2026-03-31 (+$15,982M, 40% of pre-tax) and 2026-06-30
(+$53,396M, 66%); 2025-12-31 is under the bar. So one quarter decides it.
- **The FY2026 10-K** puts 2026-12-31 in place of 2025-12-31, and both material quarters stay in
  the four.
- **The quarter to 2027-03-31** pushes 2026-03-31 out. From then on, condition 3 holds only if a
  newer quarter is material, and otherwise the proposal flips.

**The pins.** Since review round 2, every value pin reads a FROZEN copy:
`tests/fixtures/companyfacts_frozen/nonop_window/`, five tracking files as committed at
`c4c9f432`. Each pin cuts its copy at a stated date (`concepts.facts_as_of`), a page's price date
where there is one: GOOGL 2026-11-02 and ORKA 2026-10-23.

The first cut of these pins read the TRACKING fixture uncut, and the coordinator's reviewer
showed what that costs. The tracking fixture is rewritten at every re-assembly. A refresh that
only adds a comparative row names new accessions in the cite. GOOGL's uncut fixture also reads a
10-Q filed after the page's price date.

Every pin fails on `c4c9f432` or on a mutant that switches its guard off. The `c4c9f432` runs used
main's `vinci` from a scratch root, because `python -m pytest` in the worktree imports the
worktree's own code.

- **The positive pin: GOOGL's untagged Q4.** It reads 3 of 4 to 2026-09-30, from 2025-12-31,
  netting +$130,661M. The cite names both of the derived quarter's accessions. On main it reads
  (4, 4).
- **The negative pin: ORKA as filed.** Its 2021-03-31 has no pre-tax income filed or derivable, so
  the window is 3 of 4 to 2021-12-31 and says so. On main it read three quarters across two years
  (2018-03-31..2020-03-31) as "the four quarters".
- **The measured shape.** This is GOOGL's real fixture with one real row removed: the Q3 10-Q's
  nine-month pre-tax figure. It reads 3 of 4 to 2026-09-30 and never 2025-09-30. On main it reads
  4 from 2025-09-30.
- **The clustering pin: WOR, reference date 2024-08-15, facts as filed by 2025-04-15.** Its stray
  pre-tax and revenue period ending 2024-02-28 is a comparative in the 10-Q filed 2025-04-09, and
  it sits beside 2024-02-29; the two are one quarter. Mutation: with clustering switched off, the
  same quarter is read twice, and 2023-08-31 falls out of the four. (At a 2024-08-15 cut the
  stray is not yet filed, and the mutant survived.)
- **The calendar-gap pin (round 2).** This is GOOGL's real facts without its Q1-2026 10-Q
  (0001652044-26-000048, every row it carries). The pin reads (2, 3) and says "1 sits on no
  filing's calendar". It kills three mutants: M7 (the uncalendared count forced to 0), M11 (the
  300-day span widened to 400, which read 2025-09-30 back in as (3, 4)) and M9 (a stated quarter
  re-read through the derivation, which the positive pin catches by citing exactly one quarter).
- **The restatement pins (round 2).**
  - UBER Q4-2019 revenue is 4,069 as filed by 2020-12-31 and missing as filed by 2021-01-31.
    UBER's window at that cut reads 3 of 4 and names 2019-12-31.
  - FUBO as filed by 2017-06-30 reads 3 of 4 to 2015-09-30 with 2014-12-31 missing, and 2
    material, where it was 3 of 4.
  - FUBO as filed by 2025-06-30 reads 3 of 4, with 2024-12-31's revenue missing.
- **The revenue-guard pin (round 2).** FUBO as filed by 2020-08-15: the helper reads −1.563M and
  the window's reader refuses it. ORKA's derived zero for 2021-06-30 stands.
- **End to end through the assembly's own quality builder** (`mechanical._quality`, round 2):
  - GOOGL's frozen facts as filed by 2026-11-02, an empty CIQ bundle, reference date 2026-10-16;
  - the count is (3, 4, 2026-09-30), and the sentence and the count cite one window;
  - condition 3, with the EPS basis STATED (GAAP, as the page states it) rather than read off the
    living page, reads "3 of the trailing 4" and holds, asserted unconditionally (main: 4).
- **Mutation.** All six guards are killed: the restatement rule, the revenue guard, M7, M9, M11
  and clustering.
- **One check over all fixture pages.** The sentence and the count now cite one window on every
  page with a fixture. A short window's sentence says it is short.
- **Two UBER pins moved.** UBER's pins at REF 2026-07-29 were written on the window that skipped
  2025-12-31. They now read 4 material quarters, netting −$16M.

**WHICH COMMITTED PAGES WOULD MOVE — none is re-written here.** The owed Phase 1 rebuild (§5.0
row 41) carries this fix onto its pages, and the pages not being rebuilt keep their values.

**Round 2 moves no page.** The run on the round-2 code is identical to the run above: 27 pages,
BURL's row included. So
is the same run cut at each page's own price date (`date_semantics.price_as_of`), for old and new
alike. All 34 of #891's tiebreak decisions are unchanged: BDX, CELH, EPAM, NFLX, NKE and WAT,
every LTM row of each, read through `filed_tiebreak.decide` as `tests/test_filed_tiebreak.py`
drives it.

- **The structured count.** 14 committed pages carry it, and every one's window moves: AMZN, AORT,
  BRBR, CNXC, GOOGL, NFLX, ORKA, PARR, ROST, TGT, TJX, UBER, V, WLK. Its `material` changes on
  three: AMZN 3→2, GOOGL 4→3, UBER 3→4.
- **The sentence only.** Seven more pages carry the sentence but no count, and the sentence moves:
  EPAM, IT, MVST, SMPL, VITL, VRRM, WERN.
- **Unchanged.** FUBO is unchanged. BURL, LLY, NCNO, NKE and TECX stay UNKNOWN.
- **The Phase 1 names.**
  - NFLX, UBER, PARR, ORKA and V have committed pages, and all five move.
  - So does SMPL, whose sentence moves; row 41 owes it via row 36 (its Q1 FY27 10-Q).
  - MCK, MNST and CELH have no committed page among the 26.

**DOES THIS SELECT ON FORM?** It is not a new gate. One dependence on form is real: whether a
quarter can be read depends on whether the filer tags its parts. A quarter that cannot be read is
never counted material, so a short window can only lower `material` against a full one. It never
proposes R4 where a full window would not.

**BOUNDARY.**

- **Code.** `c4c9f432` (main) against this branch, measured on 2026-11-05.
- **Re-measured after main moved.** The run was repeated on the merge with main `3e97ee7d`
  (`9c78839a`), with "old" re-exported from `3e97ee7d`. #914 had re-assembled SMPL, and #915's
  stamp change touches no window code. The result is the same: main reproduces 27 of 27, 21 of 27
  reads move, R4 flips on none, and cut and uncut agree on every page.
- **Population.** All 27 committed pages under `data/dossiers/`, BURL included. The operator ruled
  on 2026-11-05: "i dont want mosaic theory to hold back any names for teamnostra repo, its two
  separate setups". The PR's first runs excluded BURL as a held audit pack, and its body claimed
  "held packs never read". Both are withdrawn: no name is held back, and the suite's loops run every
  page.
- **Inputs.** Each page's own `reference_date`, and each fixture as committed at `c4c9f432`.
- **Units.** Σ is the sum of pre-tax − operating over the window, in $M.
- **"No 10-K tags a Q4"** is checked per page on the 6 calendar quarter ends up to its reference
  date. That is 26 pages: FUBO's six hold no fiscal-year end. Every fiscal-year end among them
  needed the derivation for each total that has any quarterly fact.
- **"Moves"** means the window's quarters, the count or the sentence differ.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **THE WINDOW'S END CAN STILL BE STALE — reported, not fixed.**
   - **The rule.** The end is still the newest quarter carrying all three totals. That
     intersection-first rule is documented (one stale alias once refused UBER).
   - **The stale pages.** TJX reads to 2019-02-02 at a 2026-10-16 reference date: operating income
     has been untagged since. ORKA reads to 2021-12-31. MVST reads to 2025-12-31 at 2026-08-24:
     pre-tax income is untagged for 2026's first two quarters. SMPL reads to 2026-02-28 at
     2026-10-16: pre-tax income is untagged for 2026-05-30.
   - **It is stated, but not flagged.** Each page names its end date, so the stale end is not
     silent. It is also not flagged as stale.
   - **Why it needs a ruling.** Anchoring the window at the filer's latest quarter instead would
     move R4's inputs for a different reason (§5.0 row 51).
2. **ONE QUARTER'S THREE TOTALS CAN COME FROM DIFFERENT VINTAGES — accepted, stated.** Each total
   is derived on its own tag, from that tag's own latest pair, so one quarter can mix filings
   across totals:
   - **TJX 2019-02-02.** Operating income is the 2019 10-K less the 2018 10-Q. Pre-tax income is
     the 2021 10-K's comparative less the 2019 10-Q's comparative.
   - **ORKA 2021-12-31.** Operating income is the 2023 10-K less a 2022 10-Q comparative. Pre-tax
     income and revenue are the 2022 10-K less the 2021 10-Q.

   The figures agree across those vintages today: no total was restated between them. So the
   subtraction is one basis in value, if not in filing.
   - **Falsifier:** a derived quarter whose totals' filings state different figures for the same
     period.
   - **What the restatement rule covers.** It covers WITHIN one total (round 2). It does not cover
     ACROSS the three.
3. **Ends within a week are one quarter.**
   - **The risk.** After FUBO's combination, its filings carry two entities' quarters three days
     apart (2024-12-28 / -31, 2025-03-29 / -31, 2025-06-28 / -30). Inside a window they would be
     read as one quarter.
   - **Why it is accepted.** They fall outside FUBO's window at its reference date, and FUBO's page
     is sealed (`known_wrong.json`).
   - **Falsifier:** a page whose window holds such a pair.
