---
id:
status: shipped
date: 2026-08-30
prs: [521]
supersedes:
superseded-by:
---

# The first real thesis card — `ai-value-migration` declared (supply-side, three falsifiers, a scheduled-print confirming)

**WHAT.** The operator's first REAL thesis card, declared through the operator-record path built
in the theme-thesis brief (`vinci theme-thesis declare ai-value-migration --file card.json`) and
committed at `data/themes/thesis/ai-value-migration.json`. This is a JUDGMENT artifact, not a
build — every field traces to the operator, and the card's own `note` records the provenance:

- **mechanism: supply-side** — operator-approved 2026-08-30, settled by their own three-class
  framing: all three winners capture value *whichever model wins*, because open-source
  proliferation makes frontier-grade capability abundant — one supply shock, three landing zones.
- **market_mistake / null_thesis** — composed from the operator's stated thesis (2026-08-29:
  the ~3-6-month frontier-to-open catch-up window; migration above/below the model layer) plus
  the three-beneficiary-class refinement (2026-08-30: hyperscaler-platform / app-workflow-moat /
  silicon-ecosystem-moat, the tags of PR #520).
- **falsifiers (3)** — operator-selected 2026-08-30 from an offered set, deadlines as shown at
  selection: window WIDENS beyond ~12 months (2027-06-30); model-IP pricing power RISES without
  churn (2027-03-31); app-layer gross margins COMPRESS from model-licensing costs (2027-06-30).
- **first_confirming** — the operator-approved scheduled-print shape, corrected from an earlier
  contingent-outcome draft the operator rejected ("may or may not decline"): anchored to
  disclosures that LAND ON SCHEDULE, one representative per beneficiary class from the operator's
  own named companies, due 2026-12-15 (one full Oct–early-Dec print cycle). **The single
  composition inference: NVDA as the silicon-ecosystem representative** — the operator named the
  class, not the ticker; flagged in the card's note.

**WHY.** Closes the first half of §5.0 row 6 ("Declare the first REAL thesis card"). Until this
card, every driver stamped `THESIS UNSTATED`, new Stage-4 freezes refused, and the monitor
printed a stated absence each run. The remaining five drivers still do — that is row 6's
remaining half, at the operator's pace.

**HOW VERIFIED (real runs, live data dir).**
- Declare CLI: `OK — card written … mechanism: supply-side · falsifiers: 3 dated ·
  first-confirming due 2026-12-15`; `mirror_slug` machine-stamped `""` (the driver is slugless —
  no frontend mirror until its page exists, the glp1 precedent).
- Freeze gate both ways: `require_thesis_card("ai-value-migration")` PASSES;
  `require_thesis_card("glp1-drug-value-chain")` still refuses loudly.
- Monitor sweep, first real rows: `vinci monitor` on the live book rendered all FOUR dated
  triggers under THEME FALSIFIERS with `(by <date>)` + basis lines, no ⚑ (every window still
  open), and wrote a snapshot carrying 4 typed `theme_falsifiers` rows. **That day file is
  deliberately NOT committed** (review 2026-08-31): the Sunday run keyed it `as_of 2026-08-28`
  — an as-of artifact carrying rows from a card declared 2026-08-30, i.e. evidence predating
  the thing it evidences. The console run above is the verification; the operator's next
  scheduled run writes the first committed day with theme rows, honestly dated.
- Frontend build: `0 thesis card(s) [none]` mirrored — correct by design for a slugless card.
- ARTIFACT-PASS: full offline suite on the freshly-written artifacts — green, exit 0;
  ruff + `mypy --strict` untouched (no code changed in this PR).

**REVIEW ROUND (2026-08-31, medium code-review of this PR — two findings applied).**
1. The committed monitor day was withdrawn (above): as-of discipline — replaying the monitor
   history must never show a card two days before it existed, and an honest re-run of
   2026-08-28 would have produced a different file for the same key. Related, recorded for the
   sweep's own follow-up (separate from this PR): the sweep clock uses the calendar `ref` while
   the snapshot is stamped to the last trading day, and the passed-deadline render drops the
   row's kind — both live in merged monitor code, not here.
2. `first_confirming.basis` had restated the nine-ticker roster the trigger already names —
   two lists that could drift in an artifact that is supersede-archived, never edited. The card
   was re-declared with the basis carrying the WINDOW and provenance only; the names live once,
   in the trigger.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The card's note references PR #520 (the silicon-ecosystem-moat tag) which may merge after this
  card — the note is rationale text, nothing binds mechanically; if #520 were rejected the note's
  tag name would need an amendment via supersede (cards are supersede-archived, never edited).
- The falsifier deadlines are judgment calls the operator selected from offered shapes — the
  sweep flags the closed windows; whether a falsifier FIRED stays the human's read.
- Declaring did NOT re-run the themes-forward freeze for this driver (no basket exists for it
  yet); the gate's PASS was shown directly. The first real freeze under a declared card remains
  ahead.
