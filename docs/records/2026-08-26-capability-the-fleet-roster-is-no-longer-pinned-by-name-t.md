---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **The fleet ROSTER is no longer pinned by name — the fleet can grow (2026-08-07, PR #366).** Two

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - `test_ev_gap_routing`: `len(got) == 10` → `unrouted <= UNROUTED_BY_DESIGN` (`{FUBO}`, no EBITDA
    consensus block — a coverage property, not an extraction failure). Strictly sharper: the count
    reds identically whichever way the fleet moves, while the subset relation reds only on the real
    regression — a name silently dropping out of consensus coverage.
  - `test_freshness`: `basis_fail == {"FUBO"}` → `basis_fail == basis_break - over_ceiling`, using
    `recon.corporate_action` as the computable predicate. This is the treatment the same test
    already applied to `age_fail` in 2026-07-29 — the hardcoded line sat directly beneath the
    comment explaining why hardcoded sets are wrong. `quiet == {…10 names…}` DELETED: it is
    `fleet − age_fail − basis_fail` by construction, so with both refusal sets derived it added
    only a roster pin. What it reached for is proved by the reconciled/drifting split beneath it.
  - **A FALSE CLAIM WAS WRITTEN AND THEN MEASURED OUT.** The first draft asserted the new
    subtraction pinned the refusal ORDER ("flip the two blocks and this equality breaks"). It does
    not: `over_ceiling` is EMPTY on the live corpus (every comps re-export landed), so
    `basis_break ∩ over_ceiling = ∅` and no corpus state reaches the precedence. Caught by running
    the mutation rather than trusting the reasoning. The order IS load-bearing — age is remediable
    by a re-export, a share-basis break explicitly is not — so it is pinned on CONSTRUCTED inputs
    in `test_age_is_refused_before_the_share_basis`, and the comment now states the vacuity plainly.
  - **A STALE-BYTECODE TRAP invalidated one mutation run, and is worth knowing.** The order-flip
    mutation is a block SWAP, so the file size is unchanged; the restored file did not invalidate
    its `.pyc` and pytest ran the MUTATED module against restored source — `inspect.getsource`
    showed the correct order while the loaded code had the flipped one. Every mutation result here
    was re-taken with `__pycache__` cleared. **Any size-preserving mutation test must clear
    bytecode**, or it measures the wrong module and can report a live pin as vacuous.
  - **How verified.** Both pins green on the committed fleet, and green again with a 12th name
    (UBER) dropped in — the case that reddened both before. Mutation-tested: consensus coverage
    lost → RED; refusal order flipped → RED (constructed pin only, as documented); corporate-action
    detection silenced → RED; restored → green. Gate: ruff + `mypy --strict vinci` clean,
    **1941 passed**.
  - **`test_dilution_denominator` was NOT a roster pin and is untouched** — it globs the directory
    and asserts `len(served) == len(names)`, already self-consistent. Its only per-name coupling is
    the committed companyfacts fixture, which fails-not-skips BY DESIGN (D17), so a new name needs
    `scripts/build_companyfacts_fixture.py` run in the PR that assembles it. Verified working for
    UBER (23 tags, 316 KB). That cost is deliberate and was left alone.
