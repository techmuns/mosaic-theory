---
id: 2026-10-30-edgar-provenance
status: open
date: 2026-10-30
prs: []
supersedes:
superseded-by:
---

# The EDGAR fallback says where each figure was filed and refuses a negative capex or D&A, and the screen, rank and theme desk read a late-tagged share count as #871 does

**WHAT.** Phase 2, Session C, batch C2 (audit E1-D5, E1-D12, and the share readers C1 deferred).
- **Every EDGAR fallback figure says where it was filed (E1-D5).** `concepts.filed_at` names a
  point's tag, period, form, accession and filing day; `concepts.superseded` finds the period's
  first filing when it stated another figure — compared at the coarser of the two precisions, so a
  rounding re-report (−69,100,000 for −69,075,000) is not a restatement (review round 2). A line
  the filer splits into two tags says "restatement not checked".
  - The screen's fundamental snapshot (`client.compute_fundamental_snapshot`) carries it in the
    SOURCE of every PRESENT field (`EDGAR <where>`), never the note: the operating-income and FCF
    signs, EBITDA, EPS, net debt (its cash line, restatement checked), net leverage and net debt /
    OCF. A page receives it through the quality block (`mechanical._sourced`) as an
    accession-bearing `source_ref` — an endnote citation. (Review round 2: carried as the NOTE,
    the web Brief rendered it as a "⚠" caveat on every clean figure, since `dossier.js` shows any
    note on a present fact.)
  - The CIQ-empty fallback (`edgar_fundamentals`) names the accession in its FCF source, notes a
    restated FCF leg, and its trajectory and margin trend end with every printed figure a later
    filing restated, with the figure first filed: WOR's "FY2022 revenue 1,309 restates 5,242 first
    filed 2022-08-01 (0000950170-22-013641)".
- **A capex or D&A leg the figure cannot use is refused, naming it (E1-D12).**
  `concepts.leg_refusal`: a capex or D&A filed negative (`negative_leg`), and — whatever its sign —
  a D&A leg under `DepreciationAmortizationAndAccretionNet` (`NOT_D_AND_A`), which nets accretion
  income against depreciation and amortization and is not a D&A figure (review round 2: refusing
  it only when negative selected on sign). The snapshot's FCF sign or EBITDA reads UNKNOWN with
  the tag and accession, and net leverage says the same; the fallback leaves the period out and
  its trajectory and margin trend say "withheld". Never sign-flipped.
- **The share readers outside the dossier read a count tagged after its own filing by #871's rule**
  (audit X1(a), operator ruling 2026-10-30 "Yes, cross-check"), through #871's module: the
  screen's share change (`screens.assemble.share_change_field`) and the rank's dilution demote
  (`rank/structural._shares_for`) through `cover_count.share_series`, and the theme desk's basis
  check (`theme_intelligence.market.desk_points`, the only change in that file) through
  `cover_count.date_counts`, since it needs each count's filing date. None is assembling one
  name, so none fetches a cover: such a count is dated at its filing day, printed "filed <date>",
  and still cross-checked against its filing's other counts. A count its own filing contradicts
  voids a change only when it would itself be an ENDPOINT (`concepts.refused_endpoint`; review
  round 2 — the change reads its endpoints and nothing between): then the screen's change is
  UNKNOWN, naming it, and the rank raises `ShareCountRefusedError`, so the name is NOT scanned
  (`StructuralScan.not_scanned` holds why) and a prior flag stands — never a clean empty series
  the weekly replace would read as clean. The theme desk keeps a refused count, names it as a
  "shares" break (the kind its P/E guard holds the P/E back for) and never measures across it,
  and prints a filing-day bound as "filed <date>".

**WHY.** D5: a fallback figure with no accession cannot be checked, and a restated year printed
silently reads as the filer's original: WOR's FY2022 revenue fell from 5,242 to 1,309 after the
steel spin-off and the page showed the later figure alone. D12: a payment and an expense are filed
positive; taken as filed, WOR's capex negated made FCF 282.0 where it is 170.2 and the sign stayed
PRESENT. The share readers: REPX's 2024 count, tagged 2029, became the screen's and the rank's
newest point and anchored a window with nothing else in it; THM's 2033 tag did the same.

**HOW VERIFIED.**
- **Failing first.** `tests/test_edgar_fallback_provenance_and_sign.py` (8) was run before any of
  this code changed: 7 failed on main's behaviour — no accession on any snapshot field or in the
  fallback's FCF source, no restatement note, a negated capex leaving `fcf_sign` PRESENT, a negated
  D&A leaving EBITDA PRESENT — and the eighth (real legs read as before) passed.
  `tests/test_share_readers_cover_dated.py` (9) does not import on main (`share_change_field`,
  `desk_points`); main's behaviour on the same fixtures is in the shown run below (REPX's change
  UNKNOWN). Fixtures are WOR's committed companyfacts and the AAL, REPX, THM and VRRM share subsets.
- **Shown run, the screen decision path.** Every candidate of screen run `2026-10-16-01` with a
  cached companyfacts blob (1,695 of 2,065), through main (`8e6b12b1`) and through the branch, the
  same inputs, nothing fetched:
  Re-run on the review-round-2 head:
  - the operating-income and FCF signs, net debt / OCF and EPS move on none;
  - EBITDA goes UNKNOWN on 20 — 17 whose D&A leg is `DepreciationAmortizationAndAccretionNet`
    (LPX, PEBO, CVBF, DORM, MNRO, BZH, IMAX, OGE, MKTX, OOMA, HROW, AOSL, VISN, LNTH, ABTC, CCC,
    SOC) and 3 whose D&A is filed negative (THG, SID, AVBP); net leverage goes UNKNOWN with it on
    12 of them;
  - the screen's share change and the rank's dilution read move on 2: REPX (UNKNOWN → +3.1%) and
    AAL (+0.3% → +0.7%, its endpoint now its filing day 2026-07-23). NovaGold reads main's +31.1%:
    its refused 2025 count lies between the endpoints (review round 2; round 1 had voided it);
  - the dilution-spiral flag set is IDENTICAL, 61 names on both sides; and none of the 22 names
    that move passed the screen (FAIL or NOT_EVALUATED). No screen or rank decision moves.
  - The coordinator's reviewer counts 9 more names whose rank series loses points to a refused
    count with no value move: ATLC, DCTH, FBK, HZO, IOVA, LINC, NUTX, ORA, THRM.
- **Every committed page** (26 that this session may open; main against the branch, cached inputs):
  the snapshot's values and statuses and the dossier's share reads are identical.
- **The corpus** (the latest companyfacts per CIK, 2,225 USD reporters): 0 of 1,625 current FCF
  pairs carry a negative capex leg; 8 of 1,241 current EBITDA pairs a negative D&A leg (7 under
  `DepreciationAmortizationAndAccretionNet` — 5 Invesco DB funds, Hanover, ArriVent — and National
  Steel's 2009 `DepreciationAndAmortization`). By tag, the 1,241 current D&A legs read
  `DepreciationDepletionAndAmortization` 977 positive / 0 negative, `DepreciationAndAmortization`
  218 / 1, `DepreciationAmortizationAndAccretionNet` 28 / 7, the split `Depreciation +
  AmortizationOfIntangibleAssets` 10 / 0 (the coordinator's reviewer's count): the 35 under the
  accretion tag are refused. Of the snapshot's 8,369 current legs (`current_annual` for operating
  income, OCF and EPS, `current_pair` for capex and D&A), 13 carry a first filing stating another
  figure when compared exactly (EPS 6, OCF 3, operating income 2, capex 1, D&A 1 — the reviewer's
  13; this record's first count, 15, read capex by `current_annual`), and 10 when compared at the
  coarser precision: the 3 OCF ones are rounding re-reports (−69,100,000 for −69,075,000).
- **WOR's trajectory now ends** "[restated: FY2022 revenue 1,309 restates 5,242 first filed
  2022-08-01 (0000950170-22-013641); FY2023 revenue 1,418 restates 4,916 …; FY2022 operating income
  49 restates 329 …; FY2023 operating income 30 restates 212 …]", and its FCF source names
  10-K 0001193125-26-325872.

**BOUNDARY.**
- Cached companyfacts: the primary checkout's `data/cache/sec`, the latest blob per CIK (2,253;
  2,225 report in USD), fetched 2026-08-06 to 2026-10-27, read 2026-10-30. "Current" pairs and
  legs are `concepts.current_pair` / `current_annual`, as the snapshot reads them.
- Screen candidates: the `grain: candidate` rows of `data/snapshots/screen_runs/2026-10-16-01.jsonl`
  (2,065), joined to a CIK through `data/snapshots/securities.jsonl` and to a cached blob: 1,695.
  The spiral flag is the demote's two thresholds (`_DILUTION_SHARE_GROWTH`, `_DILUTION_PRICE_DROP`)
  on the replayed share change and the run's own drawdown input.
- Main: `8e6b12b1`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Pages gain an accession-bearing citation at re-assembly.** The snapshot's provenance reaches a
  page through the quality block's FCF sign and leverage (`mechanical._sourced`) as its
  `source_ref` — rendered as an endnote, never as a "⚠" caveat (the round-1 claim that "a PRESENT
  fact renders its value and citation, not its note" held only for the markdown renderer;
  `dossier.js` shows any note on a present fact). Every committed page gains it at its next
  re-assembly, since a maintained name builds its data record afresh then
  (`assemble.build_data_record`); a new candidate takes its record from the next screen run's
  `candidate_records.jsonl`. Added to STATE row 41. No value moves on a
  committed page: the EDGAR fallback reaches none of them.
- **A real issuance AT AN ENDPOINT reads UNKNOWN.** The cross-check cannot tell an issuance from
  a slip, so a genuine count refused at an end of the window makes the change UNKNOWN, and the
  rank leaves that name unscanned (a prior flag stands). Between the endpoints it changes nothing
  (NovaGold). Falsifier: a dilution the rank should demote, left unscanned instead.
- **The accretion tag's EBITDA is refused, sign-blind.** 35 current pairs, 20 of the screen
  candidates replayed. `anchor.py` (Session A's file) still reads `dep_amort` through
  `CONCEPT_ALIASES`, which holds the tag.
- **Outside an assembly no cover is fetched**, so a late-tagged count on the screen, the rank or
  the theme desk is dated at its filing day ("filed <date>"), up to its form's lead later than it
  was counted.
- **The anchor's FCF twin takes `abs(capex)`** (`anchor.py`, Session A's file) where the snapshot
  and the fallback now refuse a negative capex. 0 of 1,625 current pairs carry one today.

**OPEN — NOT THIS PR.**
- **The universe's share frames** (`client.frame`, `shares_outstanding_with_provenance`) take
  neither rule. A frame row carries an accession and an instant but no filing date and no cover,
  and the universe pass may not fetch per filer. Measured: 13 share counts tagged after their own
  filing have an instant inside the five frames the 2026-10-16 universe reads (`CY2025Q2I` to
  `CY2026Q2I`), 10 of them filed into those frames by SEC (Omega Flex, Farmers National Banc,
  Anteris, Bank7, JJSF, Loar, Trilogy Metals, VRRM ×2, NovaGold); each of the 10 is its filing's
  cover count, tagged days to weeks late, and reaches only the coarse cap band.
- **`frame` drops each row's accession** (E1-D5): carrying it means a third return from
  `shares_outstanding_with_provenance` and a field on the universe row (`vinci/universe.py`,
  `screens/retention.UniverseRow`), neither Session C's file.
- **The anchor's `abs(capex)`, and its `dep_amort` read of the accretion tag**, above — Session
  A's file.
- **The rank's dilution detail** (`structural._dilution_spiral`) prints a filing-day bound as the
  count's own date: `_shares_for` returns bare tuples, so the bound would have to be threaded
  through `classify_structural_disqualifier`'s signature (nit 7 of review round 2; the screen and
  the theme desk print "filed").
