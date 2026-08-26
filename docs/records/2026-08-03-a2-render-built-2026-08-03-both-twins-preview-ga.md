---
id: 
status: shipped
date: 2026-08-03
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**A2 RENDER — BUILT 2026-08-03, BOTH TWINS. ~~PREVIEW-GATED: PR OPEN, NOT MERGED~~ MERGED (stale note corrected 2026-08-18: zero PRs are open).**
**COVERAGE, PLAINLY: THE GAP STATEMENT REACHES 3 OF 11** — SMPL, EPAM, IT. The other eight carry a
STATED reason, not a blank. That is the honest headline, written here so no later summary has to
reconstruct it.
**THREE STATES, THREE SENTENCES, NEVER AN EMPTY BLOCK.** `None` -> *"MISSING REFRESH ... nothing has
been measured and nothing is being withheld"* (FUBO, sealed); `not-computed` -> the reason, plus the
route where the consensus side alone still decides one (*"still routes to two-ratio at FY2026, so
the form is known even though the comparison is not"* - VITL); `computed` -> the decomposition.
**ACCEPTANCE MET ON THE PAGE, not in the JSON:** SMPL reads **`multiple-dominant` at FY2026, and
FY2027 gives the same shape - the label does not move with the year.** The bridge lands at
**$25.67/sh**, the record's own base target - an independent cross-check that the persisted bridge
is right.
**THE BRIDGE IS PERSISTED, NOT RE-STRUCK IN THE RENDERER** - a second TEV in the render tree is
exactly what #320's review pinned against, and it would have agreed with the first until the day it
did not. Pinned structurally (`market_cap` must not appear in `_ev_gap_lines`).
**SIGMA PRINTS WITH ITS n OR NOT AT ALL**, and every dispersion carries base AND date
(`high-low / |median|, FY2026, as-of >=2026-07-21`). **THE FLOOR MARKER SURVIVES TO THE PAGE** - and
the first cut tested for ASCII `>=` while the marker is the Unicode form, so the caveat silently
never rendered: a missing precision-claim nobody could see, the same class as the value it guards.
**THE MIXED-BASIS TEV IS STAMPED AS TWO PANELS.** `_tev_stamp` prints
`2026-07-20 (BLENDED: market cap 2026-07-28 + net debt 2026-07-20; the older leads because it
bounds the pair)` on NCNO - 8 days apart - and stays PLAIN on SMPL where the panels agree, so the
caveat is not one that fires everywhere and is therefore read nowhere.
**`_implied_expectations_lines`'s DOCSTRING CORRECTED, and the distinction is the point:** the
never-differenced rule still binds THAT table and never bound the section. That table inverts a
PRICE, so differencing it against consensus yields an implied upside - a verdict in numbers. The EV
gap divides OUR OWN COMMITTED LEG by consensus and reconciles by identity - a decomposition of a
stated position, not a conclusion about what the price should be.
**RIDER SHIPPED: `mirror_to_frontend()` is wired into the pass.** A manual step in the delivery path
for the surface humans read is one forgetting from a stale page, and FUBO's missing KNOWN-WRONG
banner is what that looked like. #319's byte-identity pin made forgetting LOUD; this makes it
unnecessary. Both stay - the pin still catches a mirror written by another route.
**THE R2 REFUSAL IS RESTATED AS A HORIZON MISMATCH, AND THE OPERATOR'S REVISED EXPECTATION IS
CONFIRMED BY MEASUREMENT (report only, nothing built).** What they WOULD compute:
- **AORT** rev 1.31 x mgn 0.74 x mult 0.97 = **0.94** -> *timing-duration*; our margin **9.5%**
  (terminal) against consensus **19.4%** at FY2026 (near-term)
- **NCNO** rev 1.17 x mgn 0.73 x mult 1.00 = **0.85** -> *earnings*; **12.6%** vs **27.1%** at FY2027
- **MVST** rev 1.91 x mgn 1.07 x mult 0.79 = **1.61** -> *timing-duration*; **6.0%** vs **14.0%**
**Roughly HALF on every one, and the revenue ratios say the same from the other side** (1.31 / 1.17
/ 1.91 - our terminal revenue sits 17-91% above the near-term consensus). The refusal is NOT
over-cautious: the margin ratio would measure the distance between two HORIZONS rather than between
our view and the street's. The page now says exactly that instead of "the R2 recipe" - a reader can
judge the first and can only look up the second. **MVST is refused twice over** (coverage:
price-implied-only on one estimate), so **only AORT and NCNO turn on the convention.**
**ACCEPTED, WITH ITS REASON: one new duplicate-definition baseline entry** - the bridge-key set
`(net_debt, our_ev, shares, tev)` guarded in both twins. The JS cannot import the Python constant,
and the alternative is rendering a bridge without checking its legs, which puts `undefined` on the
page (#176's defect). Small enough that a drift shows as a missing bridge line on ONE twin, which
the parity pins already catch.
Gate: ruff + `mypy --strict` clean - **1689 passed, 3 skipped**.

**REVIEW OF #320 — THE STATED MECHANISM IS WRONG, THE ASKED-FOR TEST IS RIGHT, AND WRITING IT
FOUND THAT THE REVIEWER'S OWN SUGGESTED FIX WOULD HAVE BEEN UNDETECTABLE (2026-08-03).**
**THE CLAIM:** `ev_gap_transform` reads `implied_valuation.market_cap`, which "`ImpliedValuation`
does not have", so a second refresh gets `cap=None` and rewrites every scenario-backed record as
`not-computed`. **DISPROVED, two ways:** `ImpliedValuation.market_cap: Sourced[float]` is a DECLARED
REQUIRED field (`schemas.py:639`), and the value is present at 909.4 in SMPL's artifact **written by
the very pass under review**. A dropped field would have shown there first.
**AND THE SUGGESTED FIX WOULD HAVE BEEN A REGRESSION.** `stock_info.as_of` differs from
`comps_as_of` on **10 of 11 names** — MVST by 14 days (2026-07-08 vs 2026-06-24). The gap's
`net_debt` (peer_grid) and its persisted `tev_as_of` (`comps_as_of`) both come off the COMPS
workbook, so reading the STOCK panel's cap would put it under a comps-panel stamp — the
`financial_summary.as_of` defect, in the block whose docstring cites that defect.
**BUT THE ASKED-FOR TEST WAS MISSING AND IS NOW SHIPPED** (`test_ev_gap_transform_idempotent.py`,
10 pins): re-run `refresh_dossier(transform=ev_gap_transform)` on a real dossier in tmp, TWICE, and
assert the gap stays computed with the same ratios, vintages and label. Nothing in the persistence
file could catch that class — those pins read what was written ONCE. Mutation: reading a field the
model drops (the review's exact scenario) → **CAUGHT**.
**THE FINDING THE TEST PRODUCED, and it is worth more than the fix: SWAPPING TO
`stock_info.market_cap` PASSES EVERY BEHAVIOURAL TEST.** The two caps agree on all 11 names, so the
substitution moves no number today and the false stamp would surface only on the first name where
they diverge — long after the change. **The review's own suggestion was therefore unverifiable by
any output-level check.** Closed with a STRUCTURAL pin on the source (#310's precedent, where three
behavioural attempts could not redden): mutation with the pin → **CAUGHT**. A deliberate basis
change now has to move the STAMP too, and argue with a test.
**AND CI CAUGHT A REAL DEFECT THE LOCAL GATE COULD NOT — the first thing `gate.yml` has found
that `bin/commit` cannot.** The idempotency test went RED in CI and GREEN here, because this
worktree HAS the licensed CIQ exports and CI never can. Cause: with the bundle absent,
`ev_gap_transform` wrote **`None` over both vintages** while leaving the gap itself computed — so
**running the pass on any machine without the workbooks would silently strip the provenance off
every dossier**, a number keeping its value while losing the thing that says what it describes.
**FIXED IN THE BEHAVIOUR, NOT THE ASSERTION:** prior vintages are carried forward, and a readable
bundle that cannot date itself also keeps the prior stamp — "this export states no as-of" is a
different fact from "we never had one", and only the second justifies erasing a record. Same
principle `insider_transform` already states. Verified by reproducing CI's condition locally
(`git archive` with no `data/manual/ciq`): 10 passed; mutation with the carry-forward removed →
**CAUGHT**. **This is the CI asymmetry paying off in the direction nobody predicted:** the note
said CI is a floor that cannot see the CIQ-bound pins — it turns out CI sees a class the local
gate structurally cannot, namely everything that depends on the licensed export being ABSENT.

**~~PRE-EXISTING, SURFACED NOT FIXED: a MIXED-BASIS TEV~~ — RETRACTED 2026-08-03 (review of #321).
THE CLAIM WAS WRONG AND I MADE IT TWICE.** `stock_info.market_cap` is NOT a stock-panel figure: its
`source_ref` reads *"CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest)"* on
**all 11 committed names** — the SAME panel as peer_grid `net_debt`. So `recompute_derived`'s TEV is
SINGLE-basis and always was, and "the two caps agreeing is what hides it" had the causation
backwards: they agree because they are the same number from the same panel.
**THE COST OF THE WRONG CLAIM WAS A REAL DEFECT SHIPPED ON TOP OF IT.** A2's render acted on it and
printed *"BLENDED: market cap 2026-07-28 + net debt 2026-07-20"* on NCNO — using `stock_info.as_of`,
which is the **EOD PRICE date**, as if it were the cap's vintage. NCNO's cap and net debt are both
2026-07-20; the page labelled a single-vintage TEV as blended. **A fabricated provenance caveat, in
the block written to prevent fabricated provenance.** `_tev_stamp` and `_stock_as_of` are deleted
and their return is pinned structurally.
**AND THE SAME READ EXPOSED A REAL ONE the wrong claim was standing in front of:**
`ev_gap.vintages.tev_as_of` re-read `comps_as_of` off the CURRENT bundle while the cap and net debt
it stamps are the STORED ones — so AORT/IT/VITL carried a **2026-07-30 stamp on figures extracted
2026-06-25**, 35 days of false provenance. Fixed to read the stored
`implied_expectations.tev_as_of`, which is the TEV's own vintage and matches the stored cap's as-of
on all 11. **The lesson is the one the operator drew from the undetectable-swap finding: a value's
BASIS needs pinning, not just its output** — both caps agreed, so nothing behavioural could have
caught either error.
`test_the_two_market_caps_agree` stays: it is still true and still worth knowing, just not evidence
of what it was recorded as evidence for.
