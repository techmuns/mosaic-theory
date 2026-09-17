---
id:
status: shipped
date: 2026-09-17
prs: [624]
supersedes:
superseded-by:
---

# A revenue year the smaller tag cannot vouch for leaves the margin — WLK's cycle-average margin is 9.8%, not 16.3%

**WHAT.** When two XBRL revenue tags report the same fiscal year more than 25% apart, the year now
leaves the margin history **only where the tag in use reports the smaller figure**. The R1 anchor
(`vinci/dossier/anchor.py`) and the mid-cycle block (`vinci/dossier/midcycle.py`) share one check,
`midcycle.tag_disputes`, and every margin read names the years it left out. The conflict flag and
the weak-confidence cap are unchanged.

**WHY.** WLK's `Revenues` tag is a partial line for FY2011–15: $108–446M, against
`SalesRevenueNet` $3,571–4,463M in the same years. Two paths read it:
- the **anchor** flagged `revenue_tag_conflict` and capped the margin weak, and still took its
  median over those years — **16.31% on 15 years**;
- the **mid-cycle block** picked the longest tag with no check at all and printed a 15-year window,
  margins up to 886%, and the same 16.31%.

The clean decade, FY2016–25, gives **9.78%**. A flag printed beside a contaminated number does not
guard it.

The direction is the rule because a disagreement alone does not say which tag is wrong, and a
partial line is always smaller than the total. **Dropping every disputed year was measured and
rejected.** VRRM's ASC-606 total is the LARGER figure in all six of its disputed years (its
`Revenues` is a $13–133M line), and that rule would have cut VRRM's margin history from 8 years to
2 and its median from 20.91% to 12.89%.

**HOW VERIFIED.**
- **Both rules, live EDGAR, 35 names**: the 19 with committed dossiers, WLK, PARR, seven chemical
  peers (OLN HUN TROX EMN DOW LYB CE) and seven refiners (VLO MPC PSX DK CVI PBF DINO). Disputes
  exist on 2 names, WLK and VRRM. "Drop every disputed year" changes both; the shipped rule changes
  WLK only.
- **Old vs new code, the 19 committed dossiers**, recomputed from their frozen companyfacts
  fixtures: full anchor record plus mid-cycle margin, **19/19 identical**. No committed artifact
  moves and nothing needs re-assembly. Control inside the same script: WLK reads 16.31% / 15 years
  on the old code and 9.78% / 10 years on the new.
- **Pins on real frozen companyfacts.** WLK was added with
  `scripts/build_companyfacts_fixture.py WLK`, pinned through the anchor and through the mid-cycle
  record into its rendered line. VRRM stays at 20.9061% / 8 years with its six disputes still
  flagged. WERN's 18-year `Revenues` series is untouched.
- **Mutation: 13 of 13 killed**, run with bytecode caching off. A same-length mutation (`0.25` →
  `0.90`) restored within the same second left stale bytecode behind and reddened the suite after
  the restore; the battery was re-run clean.

**BOUNDARY.** Counts measured 2026-09-17 on live EDGAR companyfacts, then frozen in the fixtures.
A "dispute" is: same fiscal year, annual duration, values more than 25% apart relative to the
larger. The population is the 35 names listed above. The 19/19 comparison uses each name's
committed dossier `mechanical` block and its committed fixture.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Excise-heavy filers.** A filer whose assessed taxes exceed 25% of revenue (tobacco-style
  excise) would lose those years, because the tax-inclusive tag is larger by definition. None of
  the 35 names has that shape. Falsifier: a name whose excluded years are all
  including-tax-vs-excluding-tax disputes.
- **Reported, not fixed: stale peer windows.** The mid-cycle peer band still takes each peer's
  longest tag, and no dispute is involved. That gives OLN a 2008–2018 window at 9.75% where its
  2016–2025 series gives 4.63%; CE has the same shape (2007–2017, 6.73% vs 14.10%).
