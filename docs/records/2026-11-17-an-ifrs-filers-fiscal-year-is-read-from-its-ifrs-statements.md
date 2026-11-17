---
status: shipped
date: 2026-11-17
prs: [1111]
supersedes:
superseded-by:
---

# A filer that moved its statements to IFRS no longer keeps a frozen us-gaap fiscal year: its ifrs-full flow years date its newest fiscal year, so the 17 us-gaap annuals the readers served years past it are withheld, and screen run 2026-10-16-01's rows for National Steel and Himax stop serving FY2009 and FY2017 signs (STATE row 11 (a))

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
  goes to the us-gaap alias. Every unit is read, since a period's dates carry no currency, and each
  point is stamped `ifrs-full:<tag>`, so a note names where the year was read.
- **Only the period is read.** No reader serves an IFRS figure, converted or not. That is FPI1b's,
  STATE row 4.

Every reader that judges an annual against the filer's year moves with it: `current_annual`, and
`current_pair` through `behind_filer` (700d, unchanged). Those readers are the screen's snapshot,
the anchor's FCF and D&A, and the CIQ-empty FCF fallback.

A withheld annual is UNKNOWN, and its note names the IFRS year: "stale annual operating_income:
OperatingIncomeLoss for the year to 2009-12-31, 5479d behind the filer's newest fiscal year
(ifrs-full:Revenue to 2024-12-31) — more than one fiscal year behind".

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
reading by meaning costs no filer a year. The threshold is not touched. "One fiscal year behind
stays" holds for an IFRS mover too: as filed by Himax's first IFRS 20-F (FY2018), its FY2017
us-gaap annual is 365d behind and served; at the next 20-F it is 730d behind and withheld.

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
- **Pins: 9, on 6 frozen real filers** (`tests/test_ifrs_fiscal_year.py`;
  `tests/fixtures/ifrs_movers/`, README there). Each subset reads as its full blob at main and at
  this branch: fiscal year, all eight `current_annual`, and the snapshot, uncut and cut at
  2026-10-16.
  - **Positive:** Himax's fiscal year; all eight of its concepts withheld, naming both ends; the
    snapshot's four annual fields; National Steel's run row through `screen_inputs` at the run's
    own cut and close, its IFRS year dated by a BRL period. Purple Biotech's IFRS revenue line
    stops at FY2020, and its year is still dated (`ProfitLoss`, FY2025).
  - **Negative:**
    - Himax as filed by its first IFRS 20-F, one year behind and served;
    - Amber International's 6-K half-year to 2025-06-30, which does not date its fiscal year;
    - enCore Energy (IFRS 40-Fs to FY2023, then US GAAP 10-Ks), whose older IFRS years move
      nothing;
    - IAMGOLD (IFRS only), whose year is now dated, with every annual field still the
      plain-absence reading and no IFRS figure served.
  - **Fail first:** 7 of the 9 fail on main's `vinci/`. The other two pass on both, as negatives
    should: enCore, and Amber's half-year.
- **Mutation, 6 mutants on this branch's `concepts.py`, in a scratch tree; 5 killed:**
  1. IFRS points dropped (main's rule): killed;
  2. IFRS read in dollars only: killed, by National Steel's BRL year;
  3. IFRS revenue line only: killed, by Purple Biotech;
  4. IFRS points bypass the annual and forward-dated filter: killed, by Amber's half-year;
  5. the threshold at one fiscal year (350d): killed;
  6. IFRS before us-gaap in a tie: **survives**. On this cache no filer's newest us-gaap and IFRS
     annuals end the same day (0 of 122), and the order decides only which tag a note names.
- **No forward-dated IFRS annual exists on the cache** (0 of the ten tags' annual points end
  after their filing). That is why the filter is shared with the us-gaap loop, where Daily
  Journal's pin holds it, rather than a branch no real filer reaches.

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
- **Fixtures:** 6 filers, fetched 2026-06-18..2026-11-11 (the README has each).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The per-concept check stays us-gaap only.** `concept_frontier` does not read ifrs-full, so an
   IFRS mover's us-gaap annual is judged only against the filer's year, at 700d. One whose IFRS
   year is one fiscal year past its last us-gaap year keeps that us-gaap annual as current. That is
   the design for any filer one year behind, and no filer is in that shape on this cache.
   Falsifier: a cached filer whose newest IFRS annual is 350–699d past a served us-gaap annual.
2. **The tie order is unpinned** (mutant 6 above), for want of a real tie.
3. **An IFRS filer's figures are still not read.** This dates its year and serves nothing; serving
   IFRS figures, and converting them, is FPI1b (STATE row 4).
4. **Not touched:** STATE row 11 (b), net debt's cash instant with no age bound, is its own PR.
   The 52 combined annual figures whose legs stop a year apart stay refused, pending the
   operator's reading (`docs/records/2026-10-27-combined-annual-figures-read-one-fiscal-year.md`,
   WHAT IT COSTS 1).
