---
id: 2026-10-27-frozen-vintage-pins
status: shipped
date: 2026-10-27
prs: [810]
supersedes:
superseded-by:
---

# A test that compares EDGAR with a frozen CIQ figure reads a frozen companyfacts vintage, and the monitor-day pin checks each day against its own basis

**WHAT.** The second set of pins the 2026-10-26 artifact pass exposed. #809 fixed the first set.
Seven tests turned red once the pass did two things its runbooks require: regenerate NFLX's
companyfacts fixture after its page moved to the September-quarter 10-Q, and record a monitor day
at the latest close.

- **Six NFLX pins now read a frozen vintage.**
  - `test_net_debt_one_builder`: the shared-date net debt, and the notes in the borrowing tag.
  - `test_net_debt_securities_leg`: cash plus the securities leg, and the AFS total.
  - `test_share_basis_trend`: the post-split buyback reading.
  
  They compare EDGAR with CIQ figures frozen at NFLX's 2026-06-30 balance sheet, or pin a value read
  at that vintage ("−1.4%"). They read `tests/fixtures/companyfacts/NFLX.json`, which TRACKS the
  committed page (`scripts/build_companyfacts_fixture.py` is re-run in every PR that re-assembles a
  name), so the refresh moved EDGAR's side to 2026-09-30 while CIQ's side stayed put. The tests now
  read `tests/fixtures/companyfacts_frozen/NFLX.json`, the June-quarter vintage, whenever one is
  there. The tracking fixture keeps tracking.
- **`test_one_snapshot_holds_one_basis` checks each day against its own basis.** It asserted every
  committed monitor day is price return, which held only until the first total-return day under
  operator ruling B. Now:
  - a price day must carry the price basis and no `PX-EXC%` column;
  - a total day must carry the total basis and print price beside it;
  - the five days committed before the ruling (2026-07-20, 08-11, 09-16, 09-22, 10-09) must still be
    price return and present.

**WHY.** One fixture was serving two purposes: tracking the artifact for the dilution test, and
standing in as a frozen snapshot for shared-date comparisons. Every re-assembly that refreshes the
first breaks the second. Splitting them by vintage means a refresh never has to choose between the
two. Refreezing the frozen copy is a deliberate act, done together with its CIQ side.

**HOW VERIFIED.**
- **Main's state:** the four changed modules pass (96 passed).
- **The artifact pass's state** (NFLX tracking fixture at its September quarter; monitor day
  2026-10-23 on total return): the old modules fail (7 tests) and the changed ones pass (96 passed).
  The changed files were copied into the pass worktree and then restored.
- **No test in these modules compares NFLX's fixture with its committed page**, checked by reading
  every `_facts` and `NFLX` use. A frozen read cannot hide a page defect.

**BOUNDARY.** The frozen copy is `tests/fixtures/companyfacts/NFLX.json` exactly as committed at main
`121c29be`, with its cash instant at 2026-06-30. The test counts are the four modules' collected
tests on 2026-10-27.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **NFLX's frozen vintage does not follow its EDGAR filings.** It is refrozen only with a fresh CIQ
  export of the same balance-sheet date.
- **Any other name in this position joins the frozen folder the same way.** The loaders already
  prefer it.
