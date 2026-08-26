---
id: 
status: shipped
date: 2026-08-03
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**A2b PERSISTENCE — BUILT 2026-08-03. THE FORM IS IN `mech.ev_gap` ON 10 OF 11 NAMES, AND THE
INSIDER LINE RODE THE SAME PASS.**
**WHAT LANDS.** `build_ev_gap` → route (three-ratio / two-ratio / price-implied-only) · the three
ratios + the gap · BOTH shape labels with a TRISTATE `agree` · BOTH vintages · the D&A convention.
Written through `refresh_dossier` (synthesis preserved) by `chain(ev_gap_transform,
insider_transform)` — ONE pass, because the render that drops "6m" ships on deploy while the value
lags, and running them apart is the #319 regression by construction.
**THE FLEET.** **3 computed** — SMPL `0.98 × 0.95 × 2.26 = 2.10` (the A2a acceptance target,
reproduced through the persistence path), EPAM `1.00 × 0.76 × 2.64 = 2.02`, IT
`1.00 × 0.87 × 1.88 = 1.65`. **All three `multiple-dominant`, all three agreeing across years** —
the uncomfortable label, and it does not move with the year on any name that can compute it.
**8 not-computed, every one with a stated reason:** 4 no scenario record (BRBR, CNXC, VITL, VRRM) ·
**3 R2 records (AORT, MVST, NCNO)** · 1 no consensus levels (FUBO, sealed).
**THE R2 SPLIT IS RECIPE-SHAPED, AND THE REFUSAL NAMES THE CONVENTION RATHER THAN AN ABSENCE.**
Only the three R1 records carry an absolute `d_and_a`; R2 carries `d_and_a_ratio`. Per the operator
ruling (2026-07-30) converting that at the anchor is the RESERVED ANALYST DECISION — "it moves
committed numbers and is a decision, not a build" — so A2 **prints the convention per name** and
refuses with *"states D&A as a RATIO OF REVENUE … the open analyst decision"*. "No D&A available"
would have sent a reader looking for a number the record already holds.
**THE OPERATOR'S CONSENSUS VINTAGE IS MORE PRECISE THAN THE EXPORT CAN ATTEST.** The brief said
"consensus from the 07-30 export"; `estimates_as_of` reads **`≥2026-07-21`** for SMPL — a FLOOR,
because its Estimates workbook carries no As-Of header. Persisted VERBATIM with the `≥`. TEV reads
**2026-07-24** as stated. Both come from structured readers (`comps_as_of` / `estimates_as_of`),
never a regex over a rendered `source_ref`.
**THREE THINGS THE GATE CAUGHT, all mine, none visible without it.**
(1) **I WROTE THROUGH FUBO'S SEAL.** `known_wrong.json` says `dossier.json` stays untouched until a
re-assembly exists; the pass wrote `ev_gap` into it. Reverted, and **`refresh_dossier` now REFUSES
a name carrying the sidecar** — keyed on its presence, so a name that acquires one is sealed
without editing that file.
(2) **MY NEW CONSENSUS VINTAGE SILENTLY RE-BROKE THE 07-30 STALENESS SPLIT.** `CONSENSUS_PANELS` is
an ALLOWLIST and everything else defaults to the GATING class, so `ev_gap.vintages.consensus_as_of`
put MVST's `≥2026-05-15` back in front of the export gate — 56d against the 45d ceiling — refusing
the build for "no analyst has revised it", **the exact condition the split had just stopped refusing
for and which no operator action clears.** Classified; `tev_as_of` correctly stays in the gating
class (the comps book is ours to re-export). **INVARIANT SHIPPED:** every dated panel key must be
consciously classified — and it found **two more on its first run** (`stock_info.as_of`,
`valuation.implied_expectations.tev_as_of`), both pre-existing, both where the silent default was
already CORRECT. The default is safe; it simply was not asserted.
(3) **FUBO MADE A FIXED LABEL IMPOSSIBLE, and the fix is better than the one I set out to make.**
Its record is sealed, so its VALUE can never be refreshed — a hardcoded `(Form 4)` would strand
that page with no horizon at all, which is #319 again. **The label is now DERIVED from the value on
both twins:** it carries "6m" only when the value does not state its own window. Refreshed pages
read `(Form 4) … in the last 182 days`; FUBO reads `(Form 4, 6m) … (net -311.4K sh)`. Neither can
lack a horizon, and the two can never drift out of step because one is computed from the other.
**RENDER'S TWO-SPEED PROBLEM IS DESIGNED OUT, not deferred.** Every return from `build_ev_gap`
carries `status` — so the render has a sentence for the intermediate state instead of an empty
block. `None` (never refreshed) and `status="not-computed"` (refreshed, could not compute, here is
why) are DIFFERENT and the render must tell them apart.
**TESTED THROUGH THE WRITTEN ARTIFACT** (`tests/test_ev_gap_persistence.py`, 14 pins incl. the
identity re-checked on what was WRITTEN, the seal in both directions, and the `≥` surviving the
write) — because six pure functions had no production caller and #316's positional swap survived
unit tests handing the function the same wrong order a caller would.
**FRONTEND BUILD IS STILL A SEPARATE STEP.** `refresh_dossier` writes `data/dossiers/*` only;
`frontend/build.py` is run by hand. Since #319 byte-pinned the mirror, forgetting it now turns the
suite RED instead of silently serving a stale page — **loud, not automatic.** Worth wiring into the
pass; recorded rather than done.
Gate: ruff + `mypy --strict` clean · **1630 passed, 3 skipped**.

**REVIEW OF #319 — I SHIPPED THE HALF THAT MADE THE SERVED PAGE WORSE, HAVING WRITTEN THE NOTE
EXPLAINING WHY THE HALVES WERE DIFFERENT. TWO INVARIANTS SHIPPED (2026-08-03).**
**THE FINDING.** The insider LABEL is render-only (deploys immediately); the insider VALUE is
mechanical (needs a re-assembly). #319 removed `6m` from the label because the value was about to
state its own window — so between the two, the deployed line read
`Insider activity (Form 4): … sells 0 (net +90.0K sh)` — **NO HORIZON ANYWHERE**, where the label
had supplied one before. Verified against the artifact, not reasoned: `main` renders
`(Form 4, 6m): … sells 0 (net +90.0K sh)`; the branch rendered `(Form 4): … sells 0 (net +90.0K sh)`.
**A strict regression on the served surface, in the flattering direction, inside the PR written to
stop exactly that** — and the delivery-path note in my own PR body described the split that caused
it. Naming a hazard is not the same as not walking into it.
**THE DECIDING TEST, worth keeping as a rule: `6m` is true of the OLD value AND of the NEW value's
182-day count window, so KEEPING it is correct in both states while REMOVING it is correct only
after a re-assembly. A change that is right only after a later step ships WITH that step.** Label
reverted on BOTH twins (it was hardcoded in `render.py` and `dossier.js` alike) and the artifacts
re-rendered, so every served `.md` is byte-identical to main again.
**INCIDENT 2, FOUND WHILE FIXING INCIDENT 1 AND MORE SERIOUS THAN IT: FUBO'S KNOWN-WRONG BANNER WAS
MISSING FROM THE WEB MIRROR.** `data/dossiers/FUBO/dossier.md` carried the 22-line
*"⚠ KNOWN-WRONG — do not read the figures on this page as current"* block; **`frontend/dossiers/
FUBO.md` — the page actually served — did not.** That sidecar exists precisely so FUBO "cannot LOOK
VALID while resting on a wrong share base", and **on the web it looked valid.** Pre-existing on
main; surfaced by running `frontend/build.py`, not caused by this build. The suite compared only
the SET of mirrored names, never the bytes, which is why a safety banner could go missing and stay
missing.
**INVARIANT RULE SATISFIED — `tests/test_served_surface_invariants.py`, 4 pins, both incidents
mutation-verified as CAUGHT:** (i) every committed insider line states a horizon in EITHER the
label or the value — deliberately permissive about WHERE, because the artifacts legitimately lag
the code, but never about NEITHER; its negative pin uses the REAL failing string #319 shipped;
(ii) every `frontend/dossiers/<T>.md` is BYTE-IDENTICAL to its `data/` source; (iii) conditional —
IF a name declares a `known_wrong.json` THEN both surfaces carry its banner (conditional so it
cannot rot when FUBO clears).
