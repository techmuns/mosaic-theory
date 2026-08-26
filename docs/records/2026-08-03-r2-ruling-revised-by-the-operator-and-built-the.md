---
id: 
status: shipped
date: 2026-08-03
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**R2 RULING REVISED BY THE OPERATOR AND BUILT — THE TOTAL GAP NEVER NEEDED CONSENSUS (2026-08-03).**
`our_EV / TEV` uses OUR leg and the MARKET's price. Only the MARGIN DECOMPOSITION is horizon-mixed,
and the first cut suppressed BOTH — **withholding a statement that was computable the whole time.**
The numbers were already on the record from the R2 report: **AORT 0.94, NCNO 0.85, MVST 1.61.**
**THE CONFLATION WAS MINE, and it has a precise name:** converting D&A from a RATIO is internal to
our own leg — our revenue against our own stated D&A share, every term on one basis. The reserved
analyst decision was never that; it is whether our TERMINAL margin may be compared to a NEAR-TERM
consensus margin, which is a question about the DECOMPOSITION. Treating one as the other cost six
names a number.
**BUILT: all three R2 names route to `price-implied-only`** — total stated, decomposition
suppressed with its reason, **no shape label** (the label ranks three ratios; none were struck, and
emitting one would assert an attribution the numbers do not support).
**TWO REASONS, NEVER MERGED — recording one would put a FALSE sentence on one page.**
· **MVST — COVERAGE.** Its consensus reads `2/2` and `1/1`, below the floor, so the margin question
never arises and the horizon text would be false there.
· **AORT, NCNO — HORIZON.** Coverage is fine; our terminal-state margin against a near-term
consensus forecast is the binding problem.
**THE TWO MARGINS PRINT AS FIGURES, NEVER DIVIDED** — AORT `14.4% vs 19.4%`, NCNO `19.7% vs 27.1%`,
MVST `14.9% vs 14.0%`. A ratio of 0.74 mixing a view difference and a horizon difference in unknown
proportion is uninterpretable and no caveat rescues it; the figures let a reader see the distance
and judge its cause, which is strictly more information than the ratio they replace.
**TWO COVERAGES, RECORDED SEPARATELY BECAUSE THEY ARE DIFFERENT CLAIMS: TOTAL GAP 6 OF 11 ·
DECOMPOSITION 3 OF 11.** One number would hide the difference — and it is load-bearing at the A4
gate, where **option 1 is satisfied by the TOTAL**, so six names can now state a variant expectation
where three could before.
**A TEST HELD THE OVER-BROAD REFUSAL IN PLACE**, and it is the second instance in three PRs
(#321's pin held the fabricated blend). `test_a_ratio_recipe_refuses_by_naming_the_convention`
asserted the refusal as a property; it now asserts the suppression. **A pin enforces a defect as
readily as a property, and neither the suite nor CI can tell which it is doing.**
Acceptance, all met on the PAGE: MVST reads a coverage reason · AORT and NCNO state a total gap with
the horizon reason and both margins as figures · SMPL, EPAM, IT unchanged and still
multiple-dominant · no shape label anywhere it cannot be ranked.
Gate: ruff + `mypy --strict` clean · **1796 passed, 3 skipped**.

**REVIEW OF #322 — `EdgeBasis.needs` WAS DEAD METADATA, AND THE GATE PASSED EXACTLY WHAT IT WAS
WRITTEN TO STOP (2026-08-03).** Every basis declared what evidence it requires; nothing read the
field. So `--edge-basis watchlist` with no note SUCCEEDED and sealed *"No variant; watchlist,
awaiting a named observation"* — **a label naming no observation, a promise the row does not keep.**
Same class as the dead `mirror_to_frontend`: a declaration that reads like a contract and enforces
nothing. A whitespace note even appended a dangling `· `.
**FIXED: `needs` IS ENFORCED via an explicit `note_required` field.** Five of the six require a
non-blank note stating exactly what `needs` says; **only `variant-expectation` is exempt, because
its evidence is the PERSISTED GAP the machine already holds** — demanding a note there would make
the human retype a number the row can read, and a retyped number can disagree. Pinned so a seventh
basis cannot inherit silence by omission.
**PLACEHOLDERS REFUSED LIKE BLANKS** (`n/a`, `TBD`, `-`, `?`, whitespace) — the Form-4
"See Remarks" rule: a placeholder that satisfies a check is worse than a blank, because the blank
at least fails loudly.
**A DATELESS EVENT TRIGGER IS MARKED, NOT REFUSED.** `needs` is "a named date OR trigger" and only
the date half is machine-checkable; refusing a dateless trigger would push the analyst to invent a
date — the failure the escape options exist to prevent. So the row reads
*"event or structural — trigger stated, NO DATE given · index deletion at rebalance"*: the absence
is legible instead of assumed away.
**SHOWN RUN, real CLI:** bare `--edge-basis watchlist` → **REFUSED**, naming what is needed; with
`--edge-note "awaiting FQ3 gross margin above 24%"` → **LOGGED**.
**A CONSTRUCTOR HAZARD FOUND WHILE FIXING IT:** inserting a field ahead of `note` silently re-bound
every positional prose argument into the new slot. All six are now keyworded, so field order cannot
re-bind again — the address-by-position class, in a dataclass.
Gate: ruff + `mypy --strict` clean · full suite green.
