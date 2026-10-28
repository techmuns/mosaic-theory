---
id:
status: shipped
date: 2026-10-28
prs: [838]
supersedes:
superseded-by:
---

# An EDGAR figure is labelled with its OWN fiscal year, and a covenant rate component is shown only where a quote states it — the two defects waves 1 and 2 found and left open

**WHAT.**

**1. A period is named by the fiscal year its own annual report gives it, never by the filing that carried it.**
- `vinci.edgar.concepts.fiscal_year_of(fiscal_year_ends(facts), point)` returns the year as an
  `int`, or `None`. The two label sites print from it:
  - `edgar_fundamentals._period_label`: the CIQ-empty fallback's FCF source, margin trend and
    multi-year trajectory;
  - `anchor._period_label`: the anchor's EDGAR D&A source and its FCF basis and source.
  `None` prints the period's end date (`2026-01-03` in the fallback, `year to 2026-01-03` in the
  anchor).
- **The calendar is #829's, reused, not a second one.** `release._calendar` moved to
  `concepts.fiscal_calendar` and the release source imports it. Its output is unchanged: the
  release scorecard on the committed pages is identical, main against this branch, apart from one
  check's second-source text.
- `fiscal_year_ends` is the same pass over the filings (`_own_periods`) with every end kept, not
  only the original filing's. It also reads a foreign filer's 20-F / 40-F. The quarterly calendar
  the release checks use still reads only 10-Q/10-K.
- **The year is refused when** two stamps claim the period, when its year's stamp also names
  another period, or when the stamp is more than one from the calendar year the period ends in.
  A point that is not a full year (a quarter tagged `fp=FY`, a 10-Q's trailing twelve months) is
  never a fiscal year.

**2. A covenant rate component is kept only when a quote STATES it.**
- `covenant_extract.rate_components` keeps a margin, floor or PIK when one of two quotes states its
  figure in its unit (`release_parse.figure_stated`, the scorecard's own test, now shared):
  - the term's own quote, or
  - a clause of the component's own (`margin_quote` / `floor_quote` / `pik_quote`, new tool
    fields) that is a span of the exhibit.
- A component kept by its own clause stores it in `CovenantTerm.component_quotes`.
- Any other component is WITHHELD:
  - its field stays `None`, so the page's lead never composes it;
  - `CovenantTerm.withheld_components` names the figure and why;
  - an `(E5) rate component not shown — …` flag is raised.
- Both new fields are dropped from the JSON when empty, so all 27 committed pages round-trip byte
  for byte.
- The prompt now asks for the clause that states a deferred component ("plus the Applicable Rate",
  a base rate "deemed to be zero"). It asks the model to omit a pricing-grid margin unless the
  document names the level in force.
- The release source's `figure_in_own_quote` reads a component's own clause where it has one. It
  counts a withheld component as EXCLUDED, under a stated rule.

**WHY.**

*1.* companyfacts' `fy` is the fiscal year of the FILING that reported a fact. #817 (record item 3)
found Climb Global's 2019 FCF printed "[FY2020]". #821 and #822 found the anchor and the fallback
label the same way. The census below shows the fallback's series were wrong almost everywhere:
- `annual_by_period` keeps the latest-FILED point for each period, which for every year but the
  newest is a later 10-K's comparative;
- so a 10-K's three income-statement columns all carried its stamp. CECO's margin trend read
  "FY2025 9% → FY2025 9% → FY2025 17%".

Reading the period's own 10-K fixes that. The census then showed the stamps themselves cannot
always be trusted:
- **Two periods under one stamp.** Kroger's 10-Ks for the years to 2025-02-01 and 2026-01-31 are
  both stamped 2025; Wolverine's to 2024-12-28 and 2026-01-03 both 2024. The calendar keeps the
  earlier filing, and main printed the later year under the wrong stamp: BJ's Restaurants' year
  to 2025-12-30 read "FY2023", Core & Main's year to 2026-02-01 read "FY2023".
- **A stamp that is not a year.** Priority Technology stamps two 10-Ks 43465 and 43830 (the
  spreadsheet serials of 2018-12-31 and 2019-12-31). Main's fallback printed "FY43465 344".
- **A filer with no 10-K.** TAT Technologies and Gilat file 20-Fs, so a 10-K-only calendar placed
  none of their years.

*2.* #804 checks that each covenant quote is a span of its exhibit. #829's `figure_in_own_quote`
then found 29 of 48 committed rate components that their own quote does not state. Before
anything changed, each of the 29 was looked up in its exhibit (the SEC cache, `html_to_text`):

| diagnosis | n | names |
|---|--:|---|
| **composite stated in parts** — true, in another clause: a floor in the base rate's definition | 21 | AMZN, AORT ×2 (2.00%), BRBR (0.75%), BURL, CNXC, EPAM ×2, IT ×2, NCNO, NFLX ×3, NKE, TJX (0.75%), UBER ×3, WERN, WLK |
| **composite stated in parts** — a single-rate margin in the "Applicable Rate" definition | 3 | AMZN 2020 (0.50%), NFLX 2019 and 2021 (0.75%) |
| **one level of a pricing grid**, its level in force stated elsewhere | 1 | WLK 125 bps ("As of the date hereof, Pricing Level III is in effect") |
| **a WRONG value** — one level of a pricing grid stored as THE margin, no level stated | 4 | AMZN 2014 0.625% (by rating), BURL 1.50% (by availability), NCNO 2.00% (by leverage), PARR 225 bps (revolver > 3.50x, or term 3.00–3.50x) |
| a quote window that cut the figure | 0 | covenant quotes are not capped; the 5 cut quotes are release figures (EPAM 1, TJX 2, VRRM 2), untouched here |
| absent from the exhibit | 0 | |

- **The wrong values.** The extractor's deterministic gate is the fix for them: none has a quote
  stating it, so all four are withheld.
- **The composites.** Each component now carries its own clause. On the committed rows, which
  predate the field, they are withheld until the next re-assembly asks for the clause.

**HOW VERIFIED.**

*Label census — the real readers on both checkouts.* `label_census.py` runs on main 1114490b and
on this branch over the 2,161 companyfacts blobs in the shared SEC cache (read by hash, never
fetched; fetched 2026-08-12 → 2026-10-26).
- **Only labels change.** With every label token masked, 0 fields differ: no value, status or
  other text moves.

| reader | filers changed | labels changed | labels on the branch |
|---|--:|--:|--:|
| fallback FCF source (`free_cash_flow`) | 24 | 24 | 1,695 |
| fallback margin trend | 1,416 | 37,478 | 43,041 |
| fallback multi-year trajectory | 1,955 | 48,051 | 53,482 |
| anchor EDGAR D&A source | 18 | 18 | 2,147 |
| anchor FCF basis + source | 18 | 36 | 3,970 |

- **The fallback's series.** Comparatives move back to their own year: in the trajectory, 9,136
  by one year, 32,019 by two, 288 by three or four. 6,346 fall to a date (a stamp that cannot
  name the year, or a pre-XBRL year no annual report in companyfacts states); 256 gain a year.
- **The anchor.** 3 labels move a year, all AnaptysBio's: its year to 2025-12-31 read "FY2026"
  and now reads FY2025. 17 D&A and 34 FCF labels fall to a date. By cause:
  - a stamp naming two periods: 15 filers per field. These include Lindsay, IES, Post, Huntsman,
    BJ's and Core & Main, whose main label was a wrong year;
  - no annual report states the period: Fresenius 2016 and First Tracks 2025.
- **Stamps.** 116 of the 2,161 filers carry 123 stamps naming two periods; 1 filer (Priority)
  carries 2 stamps that are no year.

*The 27 committed pages: 0 printed labels move.*
- Each anchor's D&A and FCF label is the same on main and the branch: every served anchor point is
  a current year, read from its own 10-K.
- No page reads the CIQ-empty fallback.
- AMZN's fallback FCF (computed, not printed) moves from "[FY2026]" to "[2026-06-30]": a 10-Q's
  trailing column is no fiscal year.

*Covenant components — the real command, before and after.* `vinci audit quality --source release`,
cwd a scratch copy of the 27 pages with the shared SEC cache linked read-only:

| run | figures | confirmed | differs (stated) | differs (unexplained) | excluded |
|---|--:|--:|--:|--:|--:|
| BEFORE — main 1114490b, committed pages | 440 | 406 | 5 | **29** | 0 |
| branch, committed pages | 440 | 406 | 5 | 29 | 0 |
| AFTER — branch, each covenant row through the gate | 411 | 406 | 5 | **0** | **29** |

- **The AFTER pages.** Each of the 36 rows carrying a component, passed through
  `rate_components` on the model output the page stores: its components and its quote. That is
  what extraction now writes for that same answer.
- **Main and the branch on the committed pages.** The whole card is identical apart from one
  check's second-source text.

*The extractor, the real model.* `_extract_from_exhibit` on this branch, `claude-opus-4-8`, three
cached exhibits:
- **AMZN 2020:** margin 0.50% KEPT with the "Applicable Rate" definition as its own clause; floor
  0 KEPT with the Screen Rate proviso ("would be less than zero, such Screen Rate shall be deemed
  to be zero").
- **BRBR 2021:** floor 0.75% KEPT with "in the case of Term Loans, less than 0.75% per annum".
- **NCNO 2024:** floor 0 KEPT with its own clause; the 2% grid margin came back with a clause that
  is not in the exhibit, and was WITHHELD and flagged.
- **Cost:** 334,932 input and 5,488 output tokens.

*The page lead.* Passed through the gate with the same model output, 9 printed interest leads on 8
pages move (`lead_census.py`, committed rows against gated rows):
- **AMZN 2020** "LIBO Rate + 0.50% (Floor 0.00%)" → none.
- **AMZN 2014** "Eurocurrency Rate + 0.625%" (a grid tier) → none.
- **AORT** "Adjusted Term SOFR + 4.75% (Floor 2.00%)" → "+ 4.75%".
- **BRBR** none (its unquoted 0.75% floor tripped the render guard) → "Eurodollar Rate + 4.00%".
- **NCNO** QA note → none.
- **NFLX** "+ 0.75% (Floor 0.00%)" → none.
- **PARR** "LIBOR Rate + 225 bps" (a grid tier) → none.
- **UBER** "+ 2.75% (Floor 0.00%)" → "+ 2.75%".
- **WLK** "+ 125 bps (Floor 0.00%)" → none.

*Pins, on frozen real inputs.*
- **`tests/test_period_labels.py`** (7):
  - positive: Climb's 2019 point, served from the FY2020 10-K, labels FY2019, and the fallback's
    FCF series reads FY2015…FY2019, once each;
  - negative: Climb's FY2025 keeps its label; TAT's year is read from its 20-F;
  - refused: Wolverine's stamp naming two periods; Priority's 43465; Climb's FY2018 fourth
    quarter, tagged `fp=FY`.
  - Inputs: `tests/fixtures/stale_annual/CLMB.json`, extended from the same 2026-08-13 blob with
    the calendar's tags; Wolverine, TAT and Priority cut to `tests/fixtures/fiscal_calendar/`.
  - On main, the fallback series, Priority and Wolverine pins fail; the 20-F pin passes, since
    main read TAT's current year off the stamp.
- **`tests/test_covenant_rate_components.py`** (29), on the 36 committed rows frozen in
  `tests/fixtures/covenant_components/` and five windows of four real exhibits:
  - the gate withholds exactly the 29, by name, and keeps the 19;
  - a component its term quote states is kept with no clause of its own;
  - an own clause in the exhibit that states the figure keeps it (AMZN margin and floor, AORT's
    2.00% floor);
  - an own clause not in the exhibit withholds (AMZN's own stitched `value`);
  - an own clause stating another figure withholds;
  - the grid limit is pinned (below);
  - end to end: the extractor's row, its flags, its JSON, and the lead the page prints. Main
    printed "LIBO Rate + 0.50% (Floor 0.00%)" for this exact input; the branch prints none;
  - every committed row serialises unchanged;
  - the scorecard reads the own clause and counts a withheld component as excluded.
- **Mutation:** 14 mutants, one per rule, all killed:
  - labels: the filing's `fy`, the collision refusal, the year check, the annual check, 20-F, the
    anchor label, the fallback label;
  - components: the term-quote check, the own-quote span check, the own-quote figure check, the
    scorecard's own-clause read, the excluded count, the empty-key drop, the flag.
- **Four existing tests read companyfacts with no calendar evidence**, so the label they pinned
  fell to a date:
  - `test_anchor.py`'s trailing-window test gains Amazon's real FY2025 net income row (accession
    0001018724-26-000004, the 10-K its other rows come from) and keeps "latest FY2025";
  - `test_dep_amort_split_requires_the_same_fiscal_period` is synthetic with no annual report, so
    it now asserts "split, year to 2025-11-30";
  - `tests/fixtures/anchor_ciq_bridge.json` (GOOGL, ORKA) gains the calendar tags under its own
    rule ("the tags whose removal changes the chain's output"): GOOGL's from its source fixture at
    47d8ca27; ORKA's `NetIncomeLoss` from the cache cut as of that fixture's newest filing, whose
    shared tags equal it exactly. The change is additions only: removing them gives back the old
    bytes.
- The full offline suite and ruff + `mypy --strict vinci` are clean on the PR's head (counts in
  the PR body).

**BOUNDARY.**
- **Label census.** 2,161 companyfacts blobs in `mosaic-theory-ta/data/cache/sec`, fetched
  2026-08-12 → 2026-10-26, read 2026-10-28. Main 1114490b against this branch.
  - Unit: a period label — `FY####`, an ISO date, or `year to` / `12m to` a date — in the five
    reader outputs named.
  - "Changed": a different token at the same position.
- **Pages.** The 27 `data/dossiers/*/dossier.json` at 1114490b; their 27 CIKs are all in the cache.
- **Covenant counts.**
  - Population: PRESENT `covenant_term_rows` whose value is PRESENT with a `verbatim: “…”` note.
  - 48 components on 36 rows, on 17 pages.
  - Unit: one structured component (`margin_pct`, `margin_bps`, `floor_pct`, `pik_pct`).
- **Exhibit diagnosis.** One exhibit per row, from the shared SEC cache, read 2026-10-28.
- **Real model run.** Three exhibits, one call each, 2026-10-28.
- **Lead census.** Governing interest terms with a PRESENT shown value: 38 on 17 pages.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Pages move only at re-assembly** (the November artifact pass). Printed labels: none of the 27.
  Interest leads on 8 pages move if the model answers as it did (AMZN, AORT, BRBR, NCNO, NFLX,
  PARR, UBER, WLK); the composites come back where the model gives their clause.
  - Meanwhile the committed pages still print 6 leads composed with a figure their quote does not
    state: AMZN ×2, AORT, NFLX, UBER, WLK.
  - The scorecard keeps counting them as 29 differs-unexplained until those pages are re-assembled.
- **ACCEPTED RISK: a grid tier quoted with its grid passes.** The gate proves a quote STATES the
  figure, not that it is the one in force. The prompt asks the model to omit a grid margin unless
  the level is named, and NCNO's real run shows it did not: the clause it gave was not a span, so
  the gate withheld it. A verbatim grid would pass.
  - Pinned by `test_a_grid_tier_quoted_with_its_grid_passes_and_says_so`.
  - **Falsifier:** a grid rule in the gate, and that pin then fails.
  - Raised by Codex in review round 2 (P2) and DEFERRED, owner in §5.0 row 34. Counting a
    clause's figures would withhold AMZN's true single-rate definition (0.00% / 0.50% / 0.04%
    by loan type); grid words with a level-in-force phrase are a vocabulary gate this build
    could measure on only three real rows; and a stated level proves the closing date, not today.
- **ACCEPTED RISK: a wrong stamp that names ONE period is printed.** Only a collision or a
  non-year is detectable from companyfacts. Kroger's stamps skip 2023 (2022 → the year to
  2023-01-28, 2024 → the year to 2024-02-03), so one of them is not a name Kroger uses.
  - **Falsifier:** a page label disagreeing with the filer's own 10-K cover.
- **A stamp naming two periods names neither.** The year correct under that stamp (BGC's
  2025-12-31) also prints as a date: 15 filers per anchor field on the cache. A date is the
  honest form when the stamp cannot say which period it meant.
- **Found, not fixed (release scorecard, #829's lane).** `fiscal_calendar` keeps the EARLIER
  filing's period for a stamp naming two, so a release check could place a label wrong under
  such a stamp. Kroger's (FY, 2025) is the year to 2025-02-01. None of the 27 pages is among the
  116 such filers, so no committed check moves.
- **Fixed in review round 1 (Codex P2):** the page's interest-lead guard
  (`render._compose_interest_lead`, `dossier.js composeInterestLead`) checked every component's
  digits against the model's `value` string. On the real run that suppressed AMZN's and BRBR's
  leads ("rate component 0.5 not stated in the clause") although their own clauses state them.
  The governing term now carries `component_quotes`, and the guard accepts a component kept by
  one. Pinned in both engines on the frozen real-run rows
  (`real_run_2026-10-28.json`): AMZN "LIBO Rate + 0.50% (Floor 0.00%)", BRBR "Eurodollar
  Rate + 4.00% (Floor 0.75%)"; the same rows without their clauses still suppress. 3 mutants
  killed. All 27 committed pages render byte-identical, since none carries an own clause.
- **Found in review, not fixed:**
  - the anchor's D&A vintage note still names its oldest stale candidate `FY{end year}`, the
    calendar year, not the filer's fiscal year.
- **Not done here:** the 5 release figures cut by the 200-character quote cap (EPAM 1, TJX 2,
  VRRM 2), the root fix #829 deferred in `release_parse._verbatim`. None of the 29 is a cut
  window, so the brief's case for it did not arise.

**Incident → invariant.**
- Filing-year labels → `fiscal_year_of`, pinned on Climb, Wolverine, TAT and Priority.
- Unquoted rate components → `rate_components`, pinned on the 36 committed rows and real exhibit
  text.
- Shipped: Y.
