---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **R1 APPLICABILITY GATES — RATIFIED AND SHIPPED 2026-07-22 (`vinci audit r1`).** The hand audit

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **THRESHOLDS RATIFIED** as committed constants: growth-era-only band `min/median ≥ 0.55`; short
    band `< 3.0y OR < 12 closes`; margin median unusable at `spread > 8pp`, `ramp > 3pp`, or a
    negative median; leverage at `net debt > 50% of anchor equity` or `one turn > 30% of spot`;
    bear admissibility above the CURRENT multiple (loud) or above the band minimum (note). Face
    validity only — no threshold has seen a forward return.
  - **THRESHOLD RULING (2026-07-22).** *"0.55 stands as ratified; AORT's band (0.58) reclassifies
    to growth-era-only, divergence from the hand audit recorded deliberately: constants ratified
    blind to their reclassifications are not re-tuned to match prior judgment; a tripwire's false
    positive costs one evidence pull, its false negative costs an IT. Consequence-free today
    (AORT is R2-gated)."*
  - **AUDIT CADENCE ADOPTED:** run before any new BUY verdict, and monthly. First artifact:
    `docs/audits/2026-07-22-r1-applicability.md`.
  - **SCHEMA 1.2** — the bear leg carries `bear_basis` (own-history | bear-state-comps |
    peer-reference | analyst) and `margin_basis` (EBIT | EBITDA), required at write from 1.2.
    `margin_basis` binds only where a margin EXISTS: an EV/Revenue leg refuses a margin outright,
    so demanding its label would have made that basis unwritable (caught in review of PR #192).
  - **MVST CLASSIFIED `peer-reference` (2026-07-22, operator ruling).** Classified from recorded
    prose: the exit is set at the closest economic analogue, with the bear taken as a stated
    discount below it — a peer anchor with an analyst haircut is still a peer anchor. All seven
    records now carry both labels.
  - **STANDING RESULT: 10 names audited · 19 flags · 1 clean (BRBR).** Seven read "gate exists and
    FIRED" — existing machinery caught them. **Three read "NO GATE": IT, SMPL, EPAM.**
