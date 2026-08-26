---
id: 
status: recorded
date: 2026-07-29
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**STANDING VERIFICATION GAP, recorded (operator 2026-07-29): THE VISUAL LAYER HAS ONE VERIFIER AND
IT IS THE OPERATOR.** Screenshot capture has failed twice — the 375px pane, and blank frames here —
so render changes are verified by DOM assertions, which confirm a string and check overflow but
CANNOT catch what the deploy check caught: a chart marker contradicting the prose beside it, on a
page nobody questioned because the CHANGE rendered correctly. **After every render change deploys,
the operator opens the live page.** Not the local preview. That is the only visual verification in
the loop, and it has already found the most consequential render defect in this work.
**COUNT HELD: P5 pt1 closes again on merge AND live-page confirmation — not on merge alone**, since
that is how it re-opened.

**P5 pt1 RE-OPENS — COUNT GOES 3 OF 13 BACK TO 2 OF 13. NOT a new finding: the SAME defect, one
consumer down (operator 2026-07-29).** The audit's words were *"SMPL printed 'P/LTM EPS 16.0x'
beside 'as-of 2026-07-23' while that 16.0x was the 2026-03-31 close."* **The chart does that
today** — the own-history exhibit stamped `bands[0].as_of` (the EV/EBITDA band's date) across every
panel, so CNXC's P/E panel plotted its 2025-12-31 close under **2026-07-17, 198 days out**, and
SMPL's under 2026-07-23 at **114**. Item 20 fixed the PROSE readings and left the exhibit — closed
in prose, open where the audit found it.
**FOUND ON THE DEPLOYED PAGE, from an operator screenshot.** Nothing local would have shown it: the
committed data is correct (the band carries `as_of: 2025-12-31`), the prose is correct (`P/LTM EPS
NM`), and only the RENDERED page puts the two together wrongly. **The deploy is confirmed CURRENT**
by the same screenshot — item 20's NM readings are live — so no third tracking column is needed;
what is needed is that a preview reads the page.
**FIXED: each panel states its OWN as-of; the shared caption carries NO date at all.** Removing it
entirely rather than conditionalising it means there is no shared stamp left that COULD misdate a
panel. Verified on all three shapes — CNXC (2026-07-17 / 2025-12-31), SMPL (2026-07-23 /
2026-03-31), AORT (both 2026-07-17, agreeing, still dated). Pinned on the REAL names because the
defect is that two panels DISAGREE and a synthetic fixture would not produce the disagreement;
mutation-verified by restoring the `bands[0]` stamp.
**CONSUMER ENUMERATION, both sides this time (operator):** `ownHistoryExhibit` is the ONLY JS
consumer of own_history bands (`snapshots.js`'s `band` is the unrelated screen band). So this is
the last round of item 20, not the fourth.
**AND IT CORRECTS A RULE I RECORDED.** The `[-1]` scan classified the own-history band as safe
under "the date travels with the value". That is true of the DATA and false of the RENDER — the
qualifier is now in docs/engineering.md, because a future reader would have trusted it as written.
