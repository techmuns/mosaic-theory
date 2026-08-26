---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **FOUND, NOT FIXED — `scenario-propose` CRASHES on any name whose R1 anchor is inapplicable

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **Pre-existing and NOT UBER-specific — `NCNO` crashes identically**, and NCNO is an underwritten
    name. Confirmed against the live corpus: FUBO/MVST/VITL/AORT refuse gracefully (share-count
    disagreement), SMPL succeeds, UBER and NCNO crash. The follow-key diff never touches
    `propose.py`.
  - **The anchor layer was RIGHT to refuse** — UBER's `anchor.applicable=false`, reason *"no
    positive operating margin over available history — needs revenue-anchored recipe"*. So the real
    gap is that the underwrite template is R1-shaped and has no EV/Revenue path, which is the
    capability PR #188 shipped and FUBO deferred. A `.get()` alone would only convert the crash into
    a graceful refusal; it would not make an R2 name underwritable.
  - **FIXED 2026-08-08 (PR #372) — AND THE DIAGNOSIS CHANGED THE FIX.** The brief above proposed a
    `.get()` with a composed fallback. **Measured, that is the wrong fix**: with only the fallback,
    `scenario-propose NCNO` emits `2 of 9 pre-filled · recipe: R2_NEEDED` — a plausible, fillable
    template stamped with a string that **is not a recipe id** (`RECIPE_R2` is
    `R2_terminal_margin`), inviting an underwrite on a margin the revenue basis does not read. A
    crash is bad; a plausible wrong template is worse, because it is actionable. So the fix REFUSES
    at the top of `build_template`, quoting the dossier's own `reason` and `recipe_hint` rather
    than composing a second wording. The `.get()` ships too, as the backstop one layer under it.
  - **THE PROPOSE PATH HAD NO TIER AWARENESS AT ALL, which is the finding under the finding.**
    `check_tier_agreement` knows this exact state and is wired into `scenario-create` and
    `scenario-supersede` — **`_cmd_scenario_propose` never calls it**, and `KeyError` is not in the
    exception set that command catches. The guard for this case existed and could not reach it.
  - **THE REMEDY IS PER CAUSE — three live shapes refuse here, only one is about EV/Revenue.**
    MVST/NCNO/UBER hint `R2_NEEDED` (no positive operating margin); **FUBO** hints `unknown` (own
    -history multiple missing); **VITL** hints `R1_midcycle_margin_evebitda` while marked
    inapplicable (own-history band failed a coherence guard). A single EV/Revenue remedy line
    appended to all three would send two of them to fix something unrelated.
  - **THE BRIEF'S SWEEP WAS STALE, and the refusal set is not stable.** It recorded
    "FUBO/MVST/VITL/AORT refuse, SMPL succeeds". Re-measured on current main: **EPAM and IT now
    refuse too** (share counts drift as prices and share counts update), so six refused and four
    built. Any future brief quoting a refusal roster should re-measure rather than cite.
  - **FOUND, NOT FIXED (downstream, scope) — `check_tier_agreement` PASSES a `recipe_id` of
    `"R2_NEEDED"`**, because it tests `.startswith("R2")` and `"R2_NEEDED"` satisfies that while
    being a HINT, not a recipe. The axes guard then leaves it unconstrained ("an unknown recipe_id
    is unconstrained until it declares its axes"), so such a record would validate and only fail at
    `run_recipe`. Unreachable via propose now that the template refuses, but a hand-written record
    still reaches it.
