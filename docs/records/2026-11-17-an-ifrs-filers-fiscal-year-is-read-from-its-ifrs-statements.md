---
status: shipped
date: 2026-11-17
prs: [1112]
supersedes:
superseded-by:
---

# A filer that moved its statements to IFRS no longer keeps a frozen us-gaap fiscal year: its ifrs-full flow years date its newest fiscal year, so the 17 us-gaap annuals the readers served years past it are withheld, and screen run 2026-10-16-01's rows for National Steel and Himax stop serving FY2009 and FY2017 signs; by operator ruling (2026-11-18), a us-gaap annual is withheld from the first IFRS year past it (STATE row 11 (a))

**WHAT.** `vinci.edgar.concepts.filer_fiscal_year` also reads the filer's `ifrs-full` statements.
- **`IFRS_FLOW_TAGS`** maps each of the eight `FLOW_CONCEPTS` to the ifrs-full tags carrying the same
  line, chosen by meaning:
  - revenue: `Revenue`, `RevenueFromContractsWithCustomers`;
  - operating income: `ProfitLossFromOperatingActivities`;
  - pre-tax income: `ProfitLossBeforeTax`;
  - net income: `ProfitLoss`, `ProfitLossAttributableToOwnersOfParent`;
  - diluted EPS: `DilutedEarningsLossPerShare`;
  - operating cash flow: `CashFlowsFromUsedInOperatingActivities`;
  - capex: `PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities`;
  - D&A: `DepreciationAndAmortisationExpense`.
- **The filter is unchanged.** Their points pass through the same loop and the same filter as the
  us-gaap aliases: an annual period (350–380d) whose end is on or before its filing date. A tie
  goes to the us-gaap alias. Each point is stamped `ifrs-full:<tag>`, so a note names where the
  year was read.
- **Only the period is read, in every unit, on both halves** (the us-gaap half since round 1). A
  period's dates carry no currency. The year is a `FiscalYear`, its period, tag, unit and filing,
  with no value (round 1), so no reader can take the point that dates it for a figure. No reader
  serves an IFRS figure, converted or not. That is FPI1b's, STATE row 4.
- **One fiscal year behind an IFRS year is withheld** (round 1, operator ruling 2026-11-18).
  `behind_filer` withholds a us-gaap annual 350d (`ANNUAL_STALE_DAYS`) or more behind a year the
  filer's IFRS statements date, and 700d (unchanged) behind a us-gaap year.

Every reader that judges an annual against the filer's year moves with it: `current_annual`, and
`current_pair` through `behind_filer`. Those readers are the screen's snapshot,
the anchor's FCF and D&A, and the CIQ-empty FCF fallback.

A withheld annual is UNKNOWN, and its note names the IFRS year: "stale annual operating_income:
OperatingIncomeLoss for the year to 2009-12-31, 5479d behind the filer's newest fiscal year
(ifrs-full:Revenue to 2024-12-31) — more than one fiscal year behind". One year behind an IFRS
year (round 1), Himax as filed 2019-03-28: "stale annual operating_income: OperatingIncomeLoss for
the year to 2017-12-31, 365d behind the filer's newest fiscal year (ifrs-full:Revenue to
2018-12-31) — filed under IFRS, so the last US GAAP year is not current".

Not changed:
- `concept_frontier`, the per-concept check, reads us-gaap only;
- `stale_served` and `filer_frontier`;
- every quarterly reader.

**WHY.** #1096's census found the gap (`docs/records/2026-11-17-the-monitors-stale-tag-row-is-retired.md`,
FOUND NOT FIXED 1). `filer_fiscal_year` read only us-gaap flows. When a filer's statements moved to
ifrs-full, its last us-gaap year read as its newest. `behind_filer` then measured that year
against itself (0d) and passed it. National Steel's last us-gaap 20-F is for FY2009, and its IFRS
20-Fs run to FY2024; Himax's are FY2017 and FY2025. The brief offered two fixes: count the IFRS
facts in "the filer's newest fiscal year", or refuse a us-gaap annual once the filer reports IFRS
later. This is the first. It is one definition, and every reader of it is covered at once.

**The tag set, by face validity.** On the 122 cached filers carrying ifrs-full, these tags date
the same newest year as ANY annual ifrs-full fact does on all 121 that tag an IFRS flow annual. The
122nd, Amber International, tags no IFRS annual, and its newest year is its us-gaap FY2024. So
reading by meaning costs no filer a year.

**Round 0's "one fiscal year behind stays" was false, and the operator ruled it out.** Round 0 left
the thresholds alone and said one fiscal year behind stays for an IFRS mover too. That was never
true for the anchor's D&A (review of #1112, item 2): `anchor._dep_amort_point` refuses a D&A 350d
or more behind the filer's newest fiscal year, since it is added to LTM EBIT. On Himax as filed
2019-03-28, main served FY2017's $16.68M and round 0 refused it, 365d behind `ifrs-full:Revenue`
to 2018-12-31, while the snapshot's EBITDA (same two legs, same year) stayed PRESENT. For every
other reader it held, and the review put that to the operator. The ruling withholds it everywhere
(ROUND 1 below).

**HOW VERIFIED.**
- **Census first, at main 6110795d, before any code.** It reproduces #1096's count exactly: 17
  served flow annuals ≥ 700d behind the filer's newest IFRS annual, in 5 filers:
  - Himax, all 8 concepts, FY2017;
  - National Steel, 6 concepts, FY2009 (it tags no revenue or EPS alias);
  - Avino, net income FY2019;
  - Americas Gold & Silver, net income FY2021;
  - Purple Biotech, net income FY2021.

  None is 350–699d behind, so no IFRS mover sits one year in on this cache.
- **The census at this branch.** The same 17 are withheld, and nothing else changes in a reader's
  result. 102 of the 122 filers' fiscal year moves:
  - the 5 movers;
  - 97 filers with no us-gaap flow annual at all (AstraZeneca, Spotify, POSCO …), whose year goes
    from none to their IFRS year, with no annual to judge either way.

  No annual goes UNKNOWN → served.
- **The screen's own code, on a real run.** `vinci.facts.screen_replay.screen_inputs` is the
  screen's `enrich_with_fundamentals` and fundamentals snapshot. It ran on every candidate row of
  screen run 2026-10-16-01, each at its own price-date cut and close, from the cached companyfacts.
  This is the replay's reference side; no fact store is read.

  | | BEFORE (main) | AFTER (this branch) |
  |---|---|---|
  | National Steel `op_income_sign` | PRESENT +1 (FY2009, filed 2010-06-01) | UNKNOWN, names FY2009 and `ifrs-full:Revenue to 2024-12-31`, 5,479d |
  | National Steel `fcf_sign` | PRESENT −1 (FY2009) | UNKNOWN, same year named |
  | Himax `op_income_sign` | PRESENT +1 (FY2017, 20-F filed 2018-03-28) | UNKNOWN, names FY2017 and `ifrs-full:Revenue to 2025-12-31`, 2,922d |
  | Himax `fcf_sign` | PRESENT −1 (FY2017) | UNKNOWN, same |
  | Himax snapshot EBITDA / diluted EPS | $24.83M / 0.08 (FY2017) | UNKNOWN, same |
  | National Steel snapshot EBITDA | UNKNOWN ("D&A filed negative" for 2009) | UNKNOWN, the note names the stale year |

  - **Data-record fields** (`fcf_sign`, `op_income_sign`, `net_leverage`, `net_debt_to_ocf`, the
    ones `candidate_records.jsonl` carries): 2 of the 768 replayed names move, 4 fields, every one
    PRESENT → UNKNOWN. Nothing else in any row moves. The P/E and its percentile, the gate inputs
    G3 reads, are identical on all 768.
  - **The committed record carried it.** `data/snapshots/candidate_records.jsonl` (that run's) holds
    National Steel's row with `op_income_sign` +1 and `fcf_sign` −1 as of 2010-06-01. #1096 had
    not measured whether either gap reached a screen row; this one did.
  - **No gate moves.** `vinci/screens/screen2.py` and `vinci/rank/` read none of the four fields.
    Their readers are their writer (`screens/assemble.py`) and the dossier's quality and survival
    lines. National Steel's run row was NOT_EVALUATED at G3 ("no diluted EPS in the filing
    history"), and its EPS history does not move. Himax's row failed at G2 (relative return, a
    price gate) and carries no candidate record.
- **The whole cache, today's blob, no cut** (`compute_fundamental_snapshot` on all 1,078): the
  same two filers and nothing else. That is 7 field moves:
  - `op_income_sign` 2, `fcf_sign` 2, EBITDA 1 and EPS 1, PRESENT → UNKNOWN;
  - National Steel's EBITDA note, reworded.
- **The 26 committed pages: none can move.** None of their 26 filers carries an ifrs-full fact, so
  no page's fiscal year can change; `python -m vinci.impact run` (the PR body) builds them at both
  refs.
- **Pins: 14** (11 at round 0; round 1 replaced one and added three, ROUND 1 below). Two are
  structural, both from `/code-review high` (round 0): `IFRS_FLOW_TAGS`
  covers exactly `FLOW_CONCEPTS`, and the page fixture builder
  (`scripts/build_companyfacts_fixture.py`) freezes the IFRS lines, which the dossier fixtures'
  pins now read. **Twelve are on 7 frozen real filers** (`tests/test_ifrs_fiscal_year.py`;
  `tests/fixtures/ifrs_movers/`, README there; Canopy Growth's cut in round 1). Each subset reads
  as its full blob at main and at this branch: fiscal year, all eight `current_annual`, and the
  snapshot, uncut and cut at 2026-10-16.
  - **Positive:** Himax's fiscal year; all eight of its concepts withheld, naming both ends; the
    snapshot's four annual fields; National Steel's run row through `screen_inputs` at the run's
    own cut and close, its IFRS year dated by a BRL period. Purple Biotech's IFRS revenue line
    stops at FY2020, and its year is still dated (`ProfitLoss`, FY2025). Round 1: Himax as filed
    by its first IFRS 20-F, one year behind and withheld (the ruling); the fiscal year carries no
    value (National Steel's BRL year); Canopy Growth's year dated by its CAD US GAAP 10-K.
  - **Negative:**
    - Himax as filed the day before its first IFRS 20-F (2019-03-27), its FY2017 annuals served
      (round 1; round 0's pin served them one year behind the IFRS year, which the ruling
      withholds);
    - Amber International's 6-K half-year to 2025-06-30, which does not date its fiscal year;
    - enCore Energy (IFRS 40-Fs to FY2023, then US GAAP 10-Ks), whose older IFRS years move
      nothing;
    - IAMGOLD (IFRS statements; its blob's one us-gaap tag is none of the eight lines), whose
      year is now dated, with every annual field still the plain-absence reading and no IFRS
      figure served.
  - **Fail first:** at round 0, 7 of the 9 on real filers failed on main's `vinci/`; the other
    two passed on both, as negatives should: enCore, and Amber's half-year. The two structural
    pins name `IFRS_FLOW_TAGS`, which main lacks. Round 1's three new positive pins fail on round
    0's `vinci/`, at the assertion each was written for (the operating income served; a `value`
    on the year; Canopy Growth's year read as FY2019); its new negative passes at both. The
    whole file against main's `vinci/` is the impact run's fail-first stage (the PR body).
- **Mutation, 6 mutants on this branch's `concepts.py`, in a scratch tree; 5 killed:**
  1. IFRS points dropped (main's rule): killed;
  2. IFRS read in dollars only: killed, by National Steel's BRL year;
  3. IFRS revenue line only: killed, by Purple Biotech;
  4. IFRS points bypass the annual and forward-dated filter: killed, by Amber's half-year;
  5. the threshold at one fiscal year (350d): killed;
  6. IFRS before us-gaap in a tie: **survives**. On this cache no filer's newest us-gaap and IFRS
     annuals end the same day (0 of 122), and the order decides only which tag a note names.

  Round 1, 6 mutants on round 1's `concepts.py`, each run against this file, `test_annual_pairs.py`
  and `test_stale_annual.py`; **6 killed**:
  1. an IFRS-dated year judged at two years, round 0's rule: killed by the ruling's pin;
  2. every year judged at one year: killed by `test_annual_pairs.py` (a us-gaap pair a year
     apart), the pin that now holds what round 0's mutant 5 tested;
  3. the us-gaap half in dollars only, round 0's: killed by Canopy Growth;
  4. the IFRS note saying "more than one fiscal year behind": killed by the ruling's pin;
  5. `FiscalYear.ifrs` never true: killed by the ruling's pin;
  6. the year returned as its point, value and all: killed.
- **No forward-dated IFRS annual exists on the cache** (0 of the ten tags' annual points end
  after their filing). That is why the filter is shared with the us-gaap loop, where Daily
  Journal's pin holds it, rather than a branch no real filer reaches.

**ROUND 1 (2026-11-18): coordinator A's review and the operator's ruling.** A's review of
ff894050 was independent and read-only. It found no defect in the round-0 code and re-measured
every number above exactly. It raised four items:
1. **The first IFRS year is still served: an operator call.** The operator ruled on 2026-11-18,
   in coordinator A's session: **"Withhold it (Recommended)"**. As relayed: in the year a filer
   first reports under IFRS, its last us-gaap annual is withheld, reading UNKNOWN, once an IFRS
   fiscal year past it is filed. It is no longer served as current. Built in `behind_filer`.
2. **The record was wrong about the anchor's D&A.** Corrected in WHY above, and in the
   extraction vintage's `names`.
3. **A latent currency mismatch.** The us-gaap half of `filer_fiscal_year` read dollars only, the
   IFRS half every currency. Both now read every unit for the date, and the year is returned with
   no value.
4. **Nits.** The README says which fixtures elsewhere date another year than their blob
   (`fpi1a_companyfacts/CGC.json`, `net_debt_shapes/LPL.json`). The PR title states both page
   boundaries (25 of 26 built, 0 move; PARR not built). IAMGOLD's row names its one us-gaap tag.
   The tie-break docstring now says us-gaap first, then concept, then alias.

**The rule reads the FILER's IFRS year, not the concept's own IFRS line.** The review placed the
gap in `concept_frontier` reading us-gaap only, and gave Himax's FY2018
`ProfitLossFromOperatingActivities` as filed the same day as its first IFRS 20-F. The cache says
otherwise. Himax first tagged that line on 2020-03-25, in its FY2019 20-F. Its first IFRS 20-F
(2019-03-28) dates FY2018 by `Revenue`, `ProfitLoss` and the cash-flow lines. Measured at every
one of the 1,233 days, a per-concept rule (withhold where the concept's own IFRS line is a fiscal
year past) catches 15 of the 16 readings below. It leaves the 16th served: Himax's operating
income, the line the screen's `op_income_sign` reads. The ruling says "an IFRS fiscal year past
it", which is the filer's year, so `behind_filer` carries the rule.

**What moves, round 0 → round 1:**
- **History:** 16 readings in 6 filers go served → withheld. They are 13 annuals, each for one
  window. Nothing goes withheld → served.

  | filer | annuals | window |
  |---|---|---|
  | Himax | all 8, FY2017 | 2019-03-28 → 2020-03-25 (363d) |
  | Avino | net income, FY2019 | 2021-03-18 → 2022-03-31 (378d) |
  | Nano Dimension | net income, FY2020 | 2022-03-31 → 2023-03-30 (364d) |
  | Purple Biotech | net income, FY2021 | 2023-03-03 → 2024-03-05 (368d) |
  | Americas Gold & Silver | net income, FY2021 | 2023-03-15 → 2024-03-29 (380d) |
  | enCore Energy | net income, FY2022 | 2024-03-28 → 2025-03-03 (340d; its FY2024 10-K then dates the year in us-gaap) |

  Base → round 1 is 155 readings in 7 filers: round 0's 139 and these 16.
- **The anchor on the same days:** only Himax on 2019-03-28. Its FCF goes from served (−$10.43M,
  FY2017) to refused. Its D&A was already refused at round 0 and still is; the reason is now the
  stale-annual note, naming the IFRS year.
- **Today, uncut, all 1,078 filers:** 0 readings move, 0 snapshot fields and 0 anchor readings.
  The 17 withheld at round 0 stay withheld, with the same notes. 10 fiscal years move, every one
  on a filer whose figures every reader withholds by currency:
  - 9 CNY US GAAP filers go from none to FY2025: JinkoSolar, Autohome, Qfin, Sound Group, RLX,
    BingEx, Hesai, Jinxin and Chagee;
  - Canopy Growth goes from `ifrs-full:Revenue` FY2019 (CAD) to its FY2026 10-K (CAD).
- **Screen run 2026-10-16-01, replayed through `screen_inputs`:** the same 768 of 2,065 rows,
  767 cut at 2026-10-16 and 1 at 2026-10-15. **0 of 768 names move.** Base → round 1 equals
  base → round 0 exactly: SID and HIMX, `op_income_sign` and `fcf_sign` PRESENT → UNKNOWN (4
  fields). The P/E fields are identical on all 768. No gate moves.
- **Pages:** the impact run (the PR body).

**BOUNDARY.**
- **Cache:** the primary checkout's SEC cache, read directly, with no TTL and no network. 1,078
  companyfacts blobs, one per CIK, fetched 2026-06-17..2026-11-17; 122 of them carry ifrs-full.
- **Code:** BEFORE is main 6110795d (a detached worktree), AFTER is this branch. Measured
  2026-11-17.
- **Units:**
  - the census: one served (filer, flow concept) annual;
  - the replay: one candidate row, or one field of one row;
  - the cache pass: one filer's snapshot field.
- **"Served":** `current_annual(facts, concept, filer_fiscal_year(facts))` returns a point.
  **"Behind":** the filer's newest IFRS annual period end, minus the served annual's period end.
- **Replay population:** screen run 2026-10-16-01's 2,065 candidate rows. 768 are replayed; 1,297
  have no cached companyfacts and are not read. Cut at each row's price date (2026-10-15 or
  2026-10-16), close the row's own `last`.
- **Pages:** the 26 under `data/dossiers/` at 6110795d.
- **Fixtures:** 7 filers, fetched 2026-06-18..2026-11-11 (the README has each).
- **Round 1, measured 2026-11-18:** the same cache, now 1,078 companyfacts fetched
  2026-06-17..2026-11-18, 122 with ifrs-full. BASE is main 8ea51e99, which this branch merged
  (`concepts.py` unchanged there since 6110795d); ROUND 0 is the merge 2dd8f49e; ROUND 1 is this
  branch's round-1 commit. The history pass cuts each of the 122 at every day it filed a row under
  a flow alias, a `SUBSTITUTES` tag, a currency anchor or an `IFRS_FLOW_TAGS` tag: 1,233 days. Its
  unit is one (filer, flow concept, day) reading; a WINDOW is one annual from the first day it
  moves to the next such day, when it is withheld at both refs or the filer's year moves.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The first IFRS year: accepted at round 0, RULED in round 1.** Round 0 left a us-gaap annual
   one fiscal year behind the filer's IFRS year current. The review put it to the operator, who
   ruled to withhold it (ROUND 1). The per-concept check (`concept_frontier`) still reads us-gaap
   only, and need not: the filer's IFRS year withholds the annual a fiscal year past it, whatever
   the concept's own IFRS line. **"Past it" is one fiscal year, 350d** (`ANNUAL_STALE_DAYS`, the
   10-27 per-concept rule's), set by the ruling and never by outcomes; every lag measured is
   365–366d. Falsifier: a served us-gaap annual 1–349d behind an IFRS-dated year (a transition
   period), which this leaves current. Measured at round 1: 0, uncut and on all 1,233 days.
2. **The tie order is unpinned** (round 0's mutant 6 above), for want of a real tie.
3. **An IFRS filer's figures are still not read.** This dates its year and serves nothing; serving
   IFRS figures, and converting them, is FPI1b (STATE row 4).
4. **Not touched:** STATE row 11 (b), net debt's cash instant with no age bound, is its own PR.
   The 52 combined annual figures whose legs stop a year apart stay refused, pending the
   operator's reading (`docs/records/2026-10-27-combined-annual-figures-read-one-fiscal-year.md`,
   WHAT IT COSTS 1).
