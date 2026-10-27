---
status: shipped
date: 2026-10-27
prs: [822]
supersedes:
superseded-by:
---

# A re-tagged annual leg is read from its new tag where the filer proved it is the line — 24 FCF signs and 13 EBITDAs come back as one fiscal year; nothing else moves

**WHAT.** `vinci.edgar.concepts.annual_line(facts, concept)` is a concept's annual values by period
end: the served alias's, continued past their last year by a substitute the filer has PROVEN to
be the same line. `current_annual` and `current_pair` read it, so the screen's snapshot, the
anchor's FCF and the CIQ-empty fallback all take it.
- **Candidates by meaning (`SUBSTITUTES`):** the whole line under another name, or a split that
  sums to it.
  - capex: `PaymentsToAcquireOtherPropertyPlantAndEquipment`,
    `PaymentsToAcquireOtherProductiveAssets`, `PaymentsForCapitalImprovements`;
  - D&A: `Depreciation` + `AmortizationOfIntangibleAssets`.
  - Never a component: no PP&E class, no capex net of proceeds, no `Depreciation` alone, no
    "other" D&A.
  - None for operating income or operating cash flow: none exists on the census.
  - None for EPS: its one candidate recovered none of 23 legs, and no production code reads
    the snapshot's EPS.
- **Accepted per filer, on evidence:**
  1. In the LATEST year both the old line and the substitute carry (the handover), the
     substitute reports the old line's figure within `SUBSTITUTE_TOLERANCE` (0.1%). No such
     year → refused.
  2. It continues unbroken from the old line's last year: each year at most one fiscal year after
     the one before, and none of them zero. A missing year or a zero ends the line.
  3. It serves only years AFTER the old line's last. A year the aliases report is never replaced.
  4. Two accepted substitutes that disagree are refused together.
- **The rest of the read:** the substitute's tags join the concept's frontier for #817's check
  (`concept_frontier(..., substitute)`).
  - The anchor's FCF source names the tag: "capex read from
    PaymentsToAcquireOtherPropertyPlantAndEquipment, the filer's line once its capex tags
    stopped".
  - The fallback reads its value and tags from the pair `current_pair` returns. Its own period map
    has no substituted year, so reading it would raise.

**WHY.** #821 withheld every annual leg more than one fiscal year behind the filer, or reported
past. Many of those filers had not stopped reporting the line; they moved it to another tag.
Professionals do not fill such a gap with last year's figure. They read the filing, where the line
continues under its new name. Every earlier mixed-year figure stays refused. What returns is a
same-year figure read from the filer's own current line.

**The guard, by face validity** (the operator's rule, 2026-10-27: accept a substitute only where,
in a year the filer reported both, they agree within a tolerance; with no overlap year, read the
10-K; otherwise UNKNOWN).
- **A re-tag is the same line, so at the handover it carries the same number.** On the
  substitutes above, for the legs #821 withholds, 112 have a year in common with the old line:
  - 44 match within 0.05%;
  - NOTHING falls from 0.05% to 0.15%;
  - then a continuum: AbCellera's split 0.15% (30% the year before), DiamondRock 0.40%,
    Elastic 0.68%, Semtech 0.92%, Thor 1.13%, Grocery Outlet 1.63%, Ecovyst 23%, and 51 beyond
    5%.

  The tolerance sits in the one empty band. It is set by that gap, never by outcomes.
- **Thor shows why "close" is not "same".** Its FY2025 10-K, one accession, tags $121.616M under
  `PaymentsToAcquireProductiveAssets` and $122.987M under
  `PaymentsToAcquireOtherPropertyPlantAndEquipment` for the same year: two quantities. Grocery
  Outlet's split is short in both years both carry (−1.45%, −1.63%), so a component is left out.
- **The latest year, not every year.** Scotts' split matches its combined D&A exactly from FY2018
  to FY2024. It differs 5–17% in FY2014–FY2017, which the filings of those years tagged on
  another basis. An every-year rule refused the operator's own positive case.
- **The continuation rule came from the census, not from design.** Lantheus'
  `PaymentsToAcquireOtherProductiveAssets` matched capex at the FY2023 handover ($45.345M), then
  read $80.911M and, for FY2025, $0, while `PaymentsForCapitalImprovements` carried $36.089M.
  DiamondRock's `PaymentsForCapitalImprovements` skips FY2019–FY2021. Both would have been
  served without it.

**DOES THIS SELECT ON FORM?** (CLAUDE.md, before any new gate.) No — it selects on a FIGURE.
A substitute is admitted by a numeric identity in the filer's own filings (the old line's dollars
at the handover), never by which tag or disclosure style a filer uses. The candidate list is by
MEANING and only proposes; a filer with the "right" tag but a different number is refused (Thor,
Grocery Outlet, Ecovyst), and the census shows a filer with no qualifying tag is not penalised
beyond #821's refusal, which stands as it was. What it cannot see is a line whose COMPOSITION
changed after the handover (cost 1).

**HOW VERIFIED.**
- **Census first: every leg #821 withholds** (main 56500bb1, shared cache, today's blob).
  - 707 withheld (filer, concept) legs in 318 filers. 360 are STOPPED: the latest annual is at
    least 300 days before the filer's newest fiscal year (capex 159, D&A 107, operating income
    69, EPS 23, OCF 2). The other 347 are the current leg of a refused pair, or belong to a filer
    with no newer annual at all.
  - Classified under this rule:

    | outcome | legs |
    |---|---|
    | substitute accepted | 43 (capex 29, D&A 14) |
    | refused: disagrees at the handover | 65 (capex 26, D&A 39) |
    | refused: no year both carry | 7 (capex 3, D&A 4) |
    | no substitute carries a later year | 151 (capex 101, D&A 50) |
    | no substitute exists for the concept | 94 (operating income 69, EPS 23, OCF 2) |

  - The operator's named cases:
    - Scotts: accepted, $80.6M = $80.6M at FY2024; FY2025 $75.0M.
    - Ecovyst: refused, $68.383M vs $89.362M.
    - Grocery Outlet: refused, −1.63%.
    - Thor: refused, 1.13%.
    - Global Ship Lease: refused; at FY2024, capital improvements $12.840M vs capex $6.850M.
    - Valero: no substitute; no tag of that meaning carries its FY2025 capex.
- **BEFORE → AFTER, the same 2,161 blobs, nothing written.** BEFORE is main 56500bb1 (its census
  is byte-identical to #821's). Every move is UNKNOWN → PRESENT or a reworded UNKNOWN note.
  Nothing goes PRESENT → UNKNOWN, and no value changes.

  | field | UNKNOWN → PRESENT | UNKNOWN, note now names the substitute |
  |---|---|---|
  | `fcf_sign` | 24 | 5 |
  | EBITDA dollars | 13 | 1 |
  | `net_leverage` | 7 | 0 |
  | anchor EDGAR FCF | 24 | 5 |
  | CIQ-empty fallback FCF | 24 | 5 |
  | `op_income_sign`, `net_debt_to_ocf`, EPS | 0 | 0 |

  - **Data-record fields:** 31 filers' `fcf_sign` or `net_leverage` go UNKNOWN → PRESENT.
  - **FCF signs recovered** (capex via the substitute, every handover exact): American Battery
    Technology, BRC, Bakkt, Choice Hotels, Churchill Downs, Douglas Emmett, Evolent, Farmer
    Brothers, Global Net Lease, Graphic Packaging, Innospec, Materion, Myriad Genetics, Navios
    Maritime Partners, PENN Entertainment, Perdoceo, ProAssurance, Roper, RadNet, Ryman,
    Scholastic, Sunoco, Warrior Met Coal, York Water.
  - **EBITDAs recovered** (D&A via the split): ACADIA, Clarus, Cognex, DXP, FormFactor,
    GameStop, IDEX, Littelfuse, National Presto, Power Solutions, Scotts ($433.6M = FY2025
    operating income $358.6M + $75.0M), Western Union, TriMas.
  - Accepted but still withheld, the line ending early or another leg stale: DiamondRock, Lantheus
    and Siga (a zero in FY2022) among them.
- **No gate or ranker moves:** these fields have no gate reader (#821's census).
- **The 27 committed pages:** each read as filed by its own `assembled_at` and on today's blob.
  **None moves.** No page is re-assembled.
- **The anchor's existing D&A split (`anchor._latest_dep_amort`), checked against the same rule,
  as the operator asked.**
  - **No committed page reads an undercount through it.** Two pages read the split, CNXC
    ($660.433M) and WERN ($286.4M). Neither filer ever tagged a combined line, so there is no
    year to test. Each page's own CIQ cash-flow D&A for the same year agrees: CNXC $660.433M
    exactly, WERN $286.321M (+0.03%).
  - **Across the cache, the split is the anchor's D&A for 169 filers.** 111 have no combined line
    in any year the split carries, so the rule cannot test them. In 13 the split matches the
    combined line at the handover. In **45 it disagrees** (Merck −9.2%, Fiserv −6.2%, Grocery
    Outlet −1.6%). This reader is NOT changed here; see the costs.
- **Pins: 10** (`tests/test_retagged_legs.py`), on 9 frozen real filers
  (`tests/fixtures/retagged_legs/`, README there; each subset checked against the full blob at
  cut time).
  - **Positive:** Scotts D&A and EBITDA, with an aliased FY2015 never replaced. Choice Hotels'
    capex through the screen, the anchor (whose source names the tag) and the fallback.
  - **Negative:** Ecovyst and Grocery Outlet, a component. Thor, two quantities. Pacific
    Biosciences, no year in common. Global Ship Lease. Lantheus, a zero. DiamondRock, a missing
    year. The tolerance in its gap.
  - **The one synthetic pin, disclosed:** no filer of the 2,161 carries two accepted substitutes
    for one leg. That rule is pinned on Choice Hotels' real file with one tag's later values
    raised 10%, with a negative beside it.
  - #821's pins (`tests/test_annual_pairs.py`) are unchanged and green. Valero's FCF and USA
    TODAY's EBITDA are still refused.
- **Mutation: 12 mutants in a scratch copy of the tree, 12 killed:**
  - R1: agreement in every overlap year.
  - R2: tolerance 2%.
  - R3: tolerance 30%.
  - R4: no overlap year accepted.
  - R5: a zero does not end the line.
  - R6: a missing year does not end it.
  - R7: the frontier ignores the substitute's tags.
  - R8: disagreeing substitutes, the first wins.
  - R9: the substitute replaces aliased years.
  - R10: pairs read the aliases only.
  - R11: the anchor source omits the tag.
  - R12: the fallback reads its own period map.
- **Suite:** ruff + `mypy --strict vinci` clean, `pytest -m "not network"` 6,993 passed, 533 skipped, 0 failed (the final code, with this record and STATE.md).

**BOUNDARY.**
- **Census:** the shared SEC cache `/Users/work/Documents/GitHub/mosaic-theory-ta/data/cache/sec`,
  read-only.
  - 2,161 companyfacts, fetched 2026-08-12..2026-10-26.
  - No `filed_by` cut (today's blob). BEFORE is main 56500bb1, AFTER this branch. Measured
    2026-10-27.
- **Units:**
  - field moves: one filer;
  - legs: one (filer, concept) withheld by #821, stopped = latest annual at least 300 days before
    the filer's newest fiscal year;
  - the tolerance distribution: one (stopped leg, substitute) with a year in common with the old
    line, measured at the latest such year;
  - the anchor split: one filer whose `_latest_dep_amort` reads the split.
- **Pages:** the 27 under `data/dossiers/` at 56500bb1, each as filed by its own `assembled_at`
  and on today's blob.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **An old handover is trusted as long as the line runs unbroken.** Clarus's handover is FY2011,
   Douglas Emmett's FY2012, Innospec's FY2015. The unbroken run is the only evidence after that
   year; a filer that quietly narrowed the line later is not caught. Falsifier: a recovered
   leg's FY2025 figure disagreeing with the filing's cash-flow line on a page's CIQ check.
2. **The anchor's D&A split stays unguarded:** 45 cached filers would read a split that disagrees
   with their combined line, though no committed page does.
   - Guarding it is a decision for the operator, not a fix. Refusing the split leaves the anchor
     a stale combined figure, since the anchor's D&A has no staleness check (#821 record, item
     4). It also moves the R1 EBITDA basis.
   - Open in STATE.md §5.0 row 11.
3. **Seen, not fixed:** the fallback's `_period_label` still prints the filing's `fy`
   (#817 item 3).
4. **A summed split cites one filing.** Its point carries the later-filed leg's accession and
   date (`ConceptPoint` holds one); the tag string names both tags. Where the two legs' latest rows
   come from different 10-Ks, the cited accession holds only one of them.
