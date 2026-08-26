---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
date-source: MIGRATION DATE — this record was cut out of STATE.md on 2026-08-26; the work it describes is earlier (2026-07-22, per the heading). The filename prefix is therefore the migration date, not the event date.
migrated-from: STATE.md §2 Built and verified
---

# **R2 `EV/Revenue` BASIS (`vinci/dossier/terminal_margin.py`) — SHIPPED 2026-07-22 as a CAPABILITY,

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **Margin and D&A are structurally ABSENT, not computed-and-ignored.** The engine REFUSES a
    margin or a D&A ratio on an EV/Revenue leg; `ebit_t`/`d_and_a_t`/`ebitda_t` are `None`;
    `_run_r2` neither requires nor accepts a `d_and_a_ratio` FACT; the methodology axes drop
    `margin` (`scenarios.axes_for`); the card suppresses the margin row in BOTH the collapsed and
    the force-open print state. An input a computation never reads renders as a driver the reader
    cannot identify as inert — refusing is the only version of this that stays honest. The pin is
    written as a refusal for that reason: "value unchanged when margin changes" would pass just as
    happily on a renderer that still printed it.
  - **`R2_FORMULA` is UNCHANGED, byte for byte.** EV/Revenue carries its own chain
    (`R2_FORMULA_REVENUE`, 6 lines vs 9): a record stamped `EBIT_T = terminal revenue × terminal
    margin` that never computed one would describe an arithmetic it did not run, which is the one
    thing the stamp exists to prevent. *Verified:* NCNO/AORT/MVST all still stamp `R2_FORMULA` and
    re-validate under the new model; every committed record is byte-identical (only the derived
    `scenarios/_schema.json` moved).
  - Dilution, the burn landing in terminal net debt, the survival gate, the 15% hurdle and the 2:1
    bar are untouched — only the terminal valuation differs. ruff + `mypy --strict` clean, 950
    passed (+9). PR #187.
  - **ITS INTENDED TRIGGER WAS FALSIFIED MID-BUILD (recorded honestly).** The basis was queued
    against FUBO, and FUBO is not the company the brief described — see §5. The capability stands on
    its own reasoning; the next genuinely pre-profit name uses it. **No record has ever been written
    on this basis**, so it is shipped-and-UNEXERCISED: the first real use must re-verify the
    arithmetic against a hand computation rather than trust the pins alone.
