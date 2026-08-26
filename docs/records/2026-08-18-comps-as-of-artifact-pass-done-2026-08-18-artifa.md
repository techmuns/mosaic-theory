---
id: 
status: shipped
date: 2026-08-18
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**COMPS AS-OF ARTIFACT PASS DONE 2026-08-18 (`artifacts/comps-as-of-pass`) — 10 of 14 re-assembled,
and the last negative panel age but one is gone.**
- **SCOPED TO WHAT MOVES.** A full assembly is the ONLY path that applies the correction (the
  refresh path has no reference to the injection), and it RE-ROLLS SYNTHESIS — so only the 10 names
  whose stamp actually changes were rebuilt. **FUBO, MVST, UBER, VRRM deliberately skipped:** their
  stamps do not move, and re-rolling their prose for no change is churn on the LLM layer.
  Corrected: AORT/IT/VITL 07-30→07-29 · CNXC 07-29→07-28 · SMPL 08-12→08-11 · BRBR 08-09→08-07 ·
  EPAM/V 08-10→08-07 · NCNO 07-20→07-17 · **NFLX 08-17→08-14**.
- **NFLX's PANEL AGE WAS −3 DAYS — a panel dated LATER than the page reading it — and is now 0.**
  **MVST at −1 is the only negative left**, and it is unreachable: no bar uniquely carries its
  printed close, so the price-match refuses. The residue is now one visibly wrong page rather than
  an abstraction, and it still blocks the MVST re-measure.
- **EPAM FAILED THE FIRST ATTEMPT AND THE GUARD WORKED.** The LLM returned truncated output and the
  assembler REFUSED TO WRITE rather than replacing a committed synthesis with null — the guard
  naming the 2026-07-30 AORT incident. Clean on retry.
- **THREE TESTS REDDENED ON THE FRESH ARTIFACTS, and none was a defect in the fix.** All three
  shared one shape: **a fixture that BORROWED a property from live data instead of CONSTRUCTING
  it**, so each held only until the corpus moved.
  (a) `test_the_bridged_name_reconciles_...` compared V's frozen panel cap against the LIVE CMP —
  re-assembly moved the CMP 362.82→358.84 with cap and shares untouched, so a 1% tolerance broke on
  MARKET DRIFT, not a basis defect. Re-pointed to the panel's OWN printed close, where it now
  reconciles EXACTLY (362.50 vs 362.5) — which is what its docstring always claimed to test.
  (b)+(c) both dilution pins used `committed[0]` as "a record without the field". True only while
  NO dossier had been assembled since #457; AORT gained the field on rebuild, so they reddened
  because the FLEET MOVED FORWARD. Both now strip the key to construct the case.
- **AORT ADMITTED TO THE STALENESS SPLIT, re-measured as that assertion demands:** merged 49d
  (consensus/multiples from the ESTIMATES export, 2026-06-30) vs export age 20d. It read 44d before
  the pass and 49d after purely because `assembled_at` advanced five days — a CONSENSUS panel aged
  past the ceiling while the EXPORT panel stayed fresh, which is the distinction the split exists
  to draw. **That set will keep growing as names age; it is a TRIPWIRE, not an invariant** — the
  invariant is the per-name `exp.days <= merged` assert, which holds unconditionally.
