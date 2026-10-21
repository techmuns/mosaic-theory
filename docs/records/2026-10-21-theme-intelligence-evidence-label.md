---
id: 2026-10-21-theme-intelligence-evidence-label
status: recorded
date: 2026-10-21
prs: [766]
supersedes:
superseded-by:
---

# Theme intelligence: new evidence is no longer called a confirmation

**WHAT.** Operator ruling (f), 2026-10-21 ("go with your picks").
- The card's change label for class `NEW` reads **"New supporting evidence — not a
  confirmation"**. It read "Direct confirmation — new evidence".
- "Direct confirmation — independent source" stays on `INDEPENDENT_CONFIRMATION`, the only class
  that confirms a figure the thesis already holds: a different origin, the same measure and the
  same value.
- One mapping changes (`cards._CHANGE_TAG`), so the card's sources table and the weekly report
  both read the new words. The desk already said "new evidence".
- `docs/theme_intelligence.md` is updated to match.

**WHY.**
- `engine.classify_claim` gives `NEW` to three kinds of evidence:
  - a later reading of a series already held;
  - new evidence from an origin already counted;
  - new evidence from an origin the thesis did not yet hold.
- None of them confirms a held figure, so "confirmation" overstated each one. In the pilot, all 4
  NEW lines carried it and none was independent (3 other Morgan Stanley articles, 1 the same
  article re-read).
- The example wording first offered, "More evidence — same publisher", would have been wrong
  for the third kind. In the preview fixture, the NEW line comes from a different origin
  (Samsung Electronics, "independent origins 1→2") and strengthens the thesis without
  confirming any figure.

**HOW VERIFIED.**
- **Real registry.** `theme-intelligence-state` 9939047e was published with main 03e4b923 (before)
  and with this branch (after).
  - Before: the old label appeared **48** times, the new one 0.
  - After: the old label appeared **0** times, the new one 48.
  - Both runs touched the same 5 pages: TH-38CA111885 (10 lines) and TH-DEB6560D7F (6), each on
    its card and print card, plus 16 lines in the printable weekly report.
  - The label renders on the cards' and the report's "02 What changed?" evidence lines, one per
    claim-level link of class NEW (25 in the registry).
  - Before, every one of those lines contradicted its own reason: "Direct confirmation — new
    evidence … ⟨new evidence from an origin already counted — not an independent
    confirmation⟩".
  - Screenshots: `docs/theme_intelligence/evidence-label-2026-10-21/card-{before,after}.png` (a
    card's What-changed lines, print state) and `report-{before,after}.png` (the printable weekly
    report).
- **Fixture preview, PREVIEW RULE.** The overlap test's two-publisher card, on screen and in
  print: `before.png` / `after.png` (its sources table).
- **Correction.** This record first said no live card carried a NEW line. It had counted
  article-level contributions (30 novelty_unverified, 2 contradictory). The label renders per
  claim, so the live desk carried it, as above (code review of #766, 2026-10-21).
- **The app changes only when the desk is republished.** The publication holds rendered pages,
  and `publish --check` compares runs, not rendering code. The republish follows this merge as
  its own artifact PR.
- **Pins:**
  - END TO END: `test_independent_evidence_next_week_versions_the_same_thesis` renders the card
    and now requires the new words, and no "Direct confirmation", on its NEW line;
  - NEGATIVE: only `INDEPENDENT_CONFIRMATION` may say "confirmation".
- **Mutation:** 3 mutants, all killed (the old label back, NEW claiming confirmation, the
  independent label changed).

**BOUNDARY.** Live counts are occurrences on the pages `publish` writes from `theme-intelligence-state`
9939047e, rendered by main 03e4b923 (before) and by this branch (after), on 2026-10-21. The pilot's 4 are
article-level contributions in its archived registry.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Wording only, $0. A NEW line no longer says whether its
origin is new to the thesis; that stays in the audit view's change reason.
