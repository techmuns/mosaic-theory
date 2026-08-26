---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **THE SEVENTH SIGHTING of the basis class, and the first one MEASURED FLEET-WIDE rather than

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **UBER is the proving case, verified against the PRIMARY SOURCE rather than assumed.** The
    actual row equals EDGAR `OperatingIncomeLoss + DepreciationDepletionAndAmortization` to the
    dollar for FY21–FY25 (−2,932 / −885 / 1,933 / 3,510 / 6,284 against CIQ's −2,932 / −885 /
    1,933 / 3,536 / 6,312), so it is **GAAP EBITDA with SBC expensed**. The consensus row implies
    **2,952 of D&A against 737** in the actuals — a gap that is Uber's ~1,826 of stock-based
    compensation. Consensus EBITDA adds SBC back; consensus EBIT does not.
  - **IT IS NOT A UBER QUIRK — 7 of 11 committed names carry a step.** VITL 5.38x, UBER 4.01x,
    MVST 2.93x, AORT 2.65x, NCNO **0.25x** (its estimates add back LESS — the inverse case a
    one-sided test would have reported as agreement, which is the `ratio >= 2` mistake #253 already
    paid for once). IT 1.82x and BRBR 1.76x are reported un-flagged; CNXC/EPAM/SMPL/VRRM consistent.
  - **DERIVED, NEVER TOLD.** The sheet does not state a basis, so none is read off a label and
    nothing is hardcoded per name. The table carries BOTH `EBITDA ($M)` and `EBIT ($M)` for every
    column, so `EBITDA − EBIT` is that column's IMPLIED D&A; depreciation does not step-change at
    the forecast boundary, a definition does. Thresholds are FACE-VALIDITY (2.0x / 0.5x — a
    doubling or halving is not an operating fact), never tuned, and the ratio is REPORTED between
    them because the honest answer there is "here is the number, you judge".
  - **How verified.** Guard mutation-tested against three defect shapes — one-sided test (the #253
    shape), a missing column zeroed rather than skipped, and the boundary flipped to a strict
    comparison; all three go red, restored green. Live-corpus pin asserts the fleet splits into
    BOTH flagged and clean, so the check cannot go vacuous in either direction. Gate: ruff +
    `mypy --strict vinci` clean, **1988 passed** (1984 with the DB and cache moved aside).
  - **The twin was caught by an existing pin, not by review.** `test_a_noop_refresh_is_byte_
    identical` reddened on nine names: the new optional field emitted `"ebitda_basis": null` into
    artifacts that predate it. Handled by the rule refresh.py had **already named twice** — an
    optional-with-None field added after the artifacts exist is dropped when None. **This is the
    THIRD instance, and three is where it stops being a coincidence:** the next such field should
    be handled by a general drop-when-None sweep rather than a fourth hand-written stanza. Not
    generalised here (rewriting working code inside a data-shaped PR); recorded so whoever adds the
    fourth has the argument in hand.
  - **Both surfaces carry it** — `render._ebitda_basis_lines` and `dossier.js:ebitdaBasisNote`, one
    definition per surface, printed ONLY when the rows disagree (a caveat shown on every name
    trains the reader to skip it, which is how the flagged names would then be missed). The
    structured `divergent`/`ratio` are what both renderers gate on; neither parses the prose.
  - **~~OPERATOR TO-DO — the other names still render unlabelled~~ — DONE 2026-08-08 (PR #371),
    with ELEVEN SYNTHESES KEPT.** `ebitda_basis_transform` back-fills the block from the STORED
    JSON alone — the purest transform yet (`ev_gap_transform` opens CIQ workbooks,
    `capital_allocation_transform` calls EDGAR; this one reads nothing outside the artifact,
    because the annual table already holds both rows and the flags). Every synthesis verified
    byte-identical before and after; the back-fill is idempotent (a second run moves nothing).
  - **CORRECTION TO THE COUNT ABOVE.** "7 of 11 carry a step" is right, but only **5 cross the
    shipped 2.0x/0.5x thresholds and print a caveat** — VITL 5.38x, UBER 4.01x, MVST 2.93x, AORT
    2.65x, NCNO 0.25x. IT 1.82x and BRBR 1.76x carry a real step and sit INSIDE the band, so they
    are recorded in JSON and deliberately not printed. The earlier "7 of 11" came from an
    exploratory 0.7–1.4 band, not the thresholds that shipped; both numbers are true of different
    questions and the distinction is the one that matters when reading the fleet.
  - **FUBO REFUSED, AND CORRECTLY.** It is SEALED by its own `known_wrong.json`: refreshing it
    "would make a page that says 'do not trust these figures' look freshly computed". It clears
    when a re-assembly exists, not when a transform runs — so FUBO alone carries no block, and
    ABSENT keeps its meaning of NOT YET REFRESHED rather than acquiring a false clean bill.
  - **THE DRY RUN MISSED THAT REFUSAL, and the reason is worth keeping.** The sandbox copied only
    `dossier.json` + `dossier.md` into a temp dir, so `known_wrong.json` was not there and FUBO
    refreshed happily in rehearsal before refusing on the real run. **A rehearsal that copies a
    subset of the inputs does not rehearse the guards that read the rest.** Copy the whole folder,
    or expect the guard to fire first in production.
