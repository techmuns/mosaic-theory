---
id:
status: shipped
date: 2026-09-17
prs: [624]
supersedes:
superseded-by:
---

# A revenue year its tag cannot vouch for leaves the margin — WLK's cycle-average margin is 9.8%, not 16.3%

**WHAT.** When two XBRL revenue tags report the same fiscal year more than 25% apart, one of them is
not the right denominator. The R1 anchor (`vinci/dossier/anchor.py`) and the mid-cycle block
(`vinci/dossier/midcycle.py`) now share one check, `midcycle.tag_disputes`, which decides in two steps:

1. **The filing.** A margin divides operating income by revenue, so both must come from the same
   filing. If exactly one of the two revenue figures was filed with that year's operating income,
   that one wins.
2. **The size**, when the filing cannot tell them apart. A partial revenue line is always smaller
   than total revenue, so the smaller figure loses.

A year the tag in use loses leaves the margin history, and every margin read names the years it
left out. The conflict flag and the weak-confidence cap are unchanged.

**WHY.** WLK's `Revenues` tag is a partial line for FY2011–15: $108–446M, against `SalesRevenueNet`
$3,571–4,463M in the same 10-Ks. Two paths read it:
- the **anchor** flagged `revenue_tag_conflict` and capped the margin weak, and still took its
  median over those years — **16.31% on 15 years**;
- the **mid-cycle block** picked the longest tag with no check at all and printed a 15-year window,
  margins up to 886%, and the same 16.31%.

The clean decade, FY2016–25, gives **9.78%**. A flag printed beside a contaminated number does not
guard it.

**Two simpler rules were measured and rejected.**
- *Drop every disputed year.* VRRM's ASC-606 total is the LARGER figure in all six of its disputed
  years (its `Revenues` is a $13–133M line); that rule cut VRRM from 8 years to 2.
- *Drop the smaller figure* — this record's first version — was wrong on real filers. Across 424
  companies it moved 24, and 12 of those were **restatements**. After a divestiture the newest 10-K
  restates old years to continuing operations: a smaller figure, and the correct basis for the
  operating income filed beside it. Size alone dropped every one (Howmet FY2018 $6,778M against
  Arconic's $14,014M; Spectrum Brands, Ashland, Crane NXT, Enerpac, JBT Marel, Element Solutions,
  Amtech, NN, Applied Digital, Worthington), and flipped Amtech's anchor to the revenue-anchored
  recipe. The filing step keeps them.

**HOW VERIFIED.** Real runs on live EDGAR companyfacts, 2026-09-17:
- **424 companies**, old vs new code: every distinct filer behind 582 EX-99.1 exhibits pulled from
  EDGAR full-text search. 20 move, each read against its tags, values, filing dates and accessions:
  - **16 correct.** Impossible margins removed: Charter's anchor 1,176% (its 606 tag is $1.1bn of
    $55bn), McGrath 103%, Sunbelt 90% and Flowco 75% (rental companies tag only non-lease revenue as
    ASC 606 — Sunbelt $2.8bn of $10.9bn), EnPro's mid-cycle 525%, Global Partners' anchor on a
    partial 606 line, Apogee's four bogus years. Years whose older revenue sat beside restated
    operating income dropped: Worthington's anchor (0.93% → 3.85%), Spectrum Brands, JBT Marel,
    Enerpac, Natural Resource Partners, Rekor and Applied Digital in the mid-cycle series. Plus
    LifeMD and RF Industries.
  - **3 follow the rule but read poorly.** Talen and Seadrill have three-year histories, so one
    dropped year swings the median (Talen 7.5% → 2.0%). BRC Group is a financial company with no
    meaningful operating margin.
  - **1 wrong: Vistra Operations.** Its total revenue is SMALLER than its ASC-606 revenue in 2021
    because hedge losses sit inside it, in the same filing, so size marks the total as partial. The
    mid-cycle series switches tag, 10.7% → 12.4%.
- **The energy and chemical names from the first check**: PARR, OLN, HUN, TROX, EMN, DOW, LYB, CE,
  VLO, MPC, PSX, DK, CVI, PBF, DINO — none moves; WLK does, 16.31%/15y → 9.78%/10y.
- **The 19 committed dossiers**, from their frozen fixtures: full anchor record plus mid-cycle margin,
  **19/19 identical** to `main`. Nothing needs re-assembly.
- **Pins on real frozen companyfacts** (fixtures built with `scripts/build_companyfacts_fixture.py`):
  WLK through the anchor and through the mid-cycle record into its rendered line; VRRM unchanged with
  its six disputes flagged; WERN's 18-year series untouched; **HWM keeps its restated FY2018**
  (13.47%, 10 years); **WOR drops FY2022–23** (3.85%, 3 years).
- **Mutation: 16 of 16 killed** with bytecode caching off. That includes size-only, filing-only and
  ignoring our own filing. A same-length mutation restored within the same second once left stale
  bytecode behind, so caching stays off for every battery.

**BOUNDARY.** "Dispute": same fiscal year, annual duration, more than 25% apart relative to the
larger value. "Filed with": the accession of the latest-filed point for that year equals the
accession of that year's latest-filed `OperatingIncomeLoss` point. Population: the 424 distinct
filers behind the 582 exhibits (8-Ks filed 2025-09-01..2026-09-17); the 16 named energy and chemical
companies; the 19 committed dossiers.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A total made smaller by losses inside it** (Vistra Operations' hedges) is read as partial when
  the filing cannot separate the tags. 1 of 424.
- **Short histories swing.** Dropping one of three years moves a median a lot; those anchors are
  already capped weak by the conflict flag.
- **Excise-heavy filers.** A filer whose assessed taxes exceed 25% of revenue could lose years where
  both tags share a filing. None of the 424 was observed doing so.
- **Reported, not fixed: stale peer windows.** The mid-cycle peer band still takes each peer's
  longest tag, and no dispute is involved. OLN gets a 2008–2018 window at 9.75% where its 2016–2025
  series gives 4.63%; CE has the same shape (2007–2017, 6.73% vs 14.10%).
