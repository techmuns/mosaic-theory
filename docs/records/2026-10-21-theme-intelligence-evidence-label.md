---
id: 2026-10-21-theme-intelligence-evidence-label
status: recorded
date: 2026-10-21
prs: []
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
- **Preview, PREVIEW RULE.** The overlap test's two-publisher card was rendered with main and
  with this branch, on screen (sources section collapsed, as the page opens) and in print (every
  section open). The same line reads "Direct confirmation — new evidence" before and "New
  supporting evidence — not a confirmation" after, in both states.
  - Screenshots: `docs/theme_intelligence/evidence-label-2026-10-21/` (before, after).
- **Live surfaces.** The shared registry holds no `NEW` line today (9939047e: 30
  novelty_unverified contributions, 2 contradictory). The next one arrives when a source adds to
  a thesis it does not originate.
- **Pins:**
  - END TO END: `test_independent_evidence_next_week_versions_the_same_thesis` renders the card
    and now requires the new words, and no "Direct confirmation", on its NEW line;
  - NEGATIVE: only `INDEPENDENT_CONFIRMATION` may say "confirmation".
- **Mutation:** 3 mutants, all killed (the old label back, NEW claiming confirmation, the
  independent label changed).

**BOUNDARY.** Live counts are from `theme-intelligence-state` 9939047e; the pilot counts are from
its archived registry, 2026-10-21.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Wording only, $0. A NEW line no longer says whether its
origin is new to the thesis; that stays in the audit view's change reason.
