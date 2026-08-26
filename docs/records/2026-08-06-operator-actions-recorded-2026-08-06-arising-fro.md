---
id: 
status: recorded
date: 2026-08-06
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**OPERATOR ACTIONS — RECORDED 2026-08-06, arising from the rank re-run and the EPAM/IT re-assemblies.**

**O4 — SETTLED, NOT PENDING: WERN FAILS ON ITS OWN NUMBERS AND A HORIZON CHANGES NOTHING
(recorded 2026-08-06).** WERN has been carried as "failing without a horizon", which reads as an
underwrite awaiting one field. It is not. Measured on the committed record at spot $46.04:

    legs   bear 16.59 · base 35.71 · bull 48.85
    reward -10.33   risk 29.45   ratio -0.3509   bar 2.0   FAIL

**THE REWARD IS NEGATIVE — the base case sits $10.33 BELOW spot.** The name is worth less on its
own underwrite than the market pays. So the missing horizon is not what fails it: stating one
would leave `ratio -0.35` against a 2.0 bar and add an IRR that is negative for the same reason.
`gate` reads UNDEFINED only because `irr_undefined` is contagious, which makes the record LOOK
incomplete when it is decided. **No horizon is owed and none should be sought** — the ratio test
already answered. WERN also has **no dossier** (the only underwrite record without one).

**Not "pending a field" — settled AVOID on the numbers.** Recorded so it stops appearing in
queues as unblocked work.
