---
id: 2026-10-07-a-rebuild-keeps-the-committed-recipe
status: shipped
date: 2026-10-07
prs: [670]
supersedes:
superseded-by:
---

# A re-assembly keeps the committed recipe — every hand re-tag on record had been erased by the next one

**WHAT.** `assemble._write` now applies `preserve_operator_tag` before it writes. That is the rule
`anchor-backfill` has used since July. When the committed anchor carries a RECIPE that differs from
the one this build computes, the committed recipe and its reason are written, and a caveat on the
page names both. A committed anchor block that does not validate is refused rather than
overwritten. `_write` returns the dossier it actually wrote, and `assemble_one` returns that.

The shared rule itself was narrowed in review (below): a placeholder hint is never kept, and under
an unchanged recipe the fresh reason always wins. Both write paths take that change.

**WHY.** Every hand re-tag on record was erased by the next full re-assembly — four of four:

| name | re-tag, by hand | erased by |
|---|---|---|
| AORT | `R2_NEEDED`, 07-21 (`feca6b93`) | re-assembly, 07-23 (`28baa8f5`) |
| CNXC | `R1_NOT_ROBUST`, 07-21 (`9b9228bc`) | re-assembly, 07-22 (`5d663ea3`) |
| VITL | `R2_NEEDED`, 07-21 (`9b9228bc`) | re-assembly, 07-22 (`4a4e00ee`) |
| GOOGL | `R3_forward_pe`, 09-01 (`c005449f`) | artifact pass, 09-18 (`0251f4cb`, #631) |

Assembly computed the anchor fresh and wrote it over the committed block; only `anchor-backfill`
called `preserve_operator_tag`. The consequence reached the scenario gate: `check_tier_agreement`
refuses an R3 record against an R1 hint, so on 2026-10-07 the gate refused GOOGL's own committed R3
record — the fund's first confirmed position — and refuses an AMZN R3 record for the same reason.
Found while checking what an AMZN scenario would need.

Two corpus "live cases" in `tests/test_propose.py` were the erasure itself. AORT's dossier "read R1
beside an R2 record" because its re-tag was gone, and VITL "read R1 + applicable False" for the same
reason. Both pins now assert what holds in either state, and the refusal branches are pinned on
their own shapes, so the restoration (#671) can land.

**REVIEW OF #670 — TWO THINGS THE FIRST CUT KEPT THAT ARE NOT RECIPES.** Both reproduced on the
committed corpus before fixing:

1. **A placeholder hint.** `unknown` / `ANCHOR_UNRESOLVED` is the machine saying it could not
   compute a recipe. Kept, it outlives the data gap that wrote it: FUBO, ORKA and TECX sit committed
   as `unknown`, and a later R1 would have been written as `unknown` + "own-history multiple
   missing" over an anchor marked applicable. A real recipe is still kept OVER a placeholder (NCNO
   07-23: `R2_NEEDED` → `unknown` on a data gap).
2. **A machine refusal reason under an unchanged recipe.** NFLX and V carry "R1 inputs incomplete".
   A later build still R1 and still not applicable for a DIFFERENT cause would have kept the old
   cause on the page, with a caveat on every rebuild. Under an unchanged recipe the reason is now
   always the build's.

**CORRECTIONS TO THIS RECORD'S FIRST DRAFT.** It said the rule "holds back exactly six of 521
transitions … it never holds back a recipe change that should have applied". Both halves were
wrong. The six silently excluded the four hand re-tag commits that the replay also flagged. And one
of the six — NCNO's 07-27 move OFF `unknown` — was the review's finding 1, called "right" in the
draft. The measurement is restated under BOUNDARY with its filter stated.

**HOW VERIFIED.**
- **Real replays through the fixed `_write`** (the full committed prior file from git, and the full
  dossier each build wrote):
  - the four erasing builds keep their recipe and reason, with the caveat on the page;
  - NCNO 07-23 keeps `R2_NEEDED` over `unknown`, with the caveat;
  - NCNO 07-27 writes the build's `R2_NEEDED` with no caveat;
  - NFLX with a new cause writes the build's reason with no caveat.
- **Corpus negative:** all 26 committed dossiers written over a copy of themselves → 0 anchor or
  caveat changes. Its limit is stated in the test: a build that agrees with itself never diverges.
- **Tests:** `tests/test_rebuild_keeps_committed_recipe.py`, 37 cases. Two frozen fixtures hold the
  verbatim blocks from git.
- **Six mutants, all killed:**
  - call removed → 6 fail; invalid block accepted → 1; guard always rewrites → 28;
  - caveat dropped → 5; placeholder kept again → 2; machine reason frozen again → 1.
- **The last mutant survived until a rule-level pin was added.** The assembly guard only ever
  applies a kept recipe, so it masked a regression inside the rule, which `anchor-backfill` writes
  unfiltered.
- Full offline suite green; `ruff` and `mypy --strict` clean (counts in the PR).

**BOUNDARY.** Every committed version of `data/dossiers/<T>/dossier.json` for the 26 names with a
committed dossier, main @`4ab4de36`, each compared with the version before it: 521 transitions.
- 505 change no hint or reason. 16 do.
- Of the 16, 4 are the hand re-tag commits themselves (`feca6b93`, `9b9228bc` ×2, `c005449f`) —
  edits, which the rule never runs on. 12 are builds.
- Under the fixed rule, 5 of the 12 builds are held back: the four erasures and NCNO 07-23. The
  other 7 flow through: NCNO 07-27, plus six GOOGL/NFLX applicability flips where the fresh reason
  wins.
- "Four of four": the hand re-tags named in `preserve_operator_tag`'s docstring (AORT, CNXC, VITL)
  plus GOOGL, whose reason opens "OPERATOR RE-TAG".
- "3 of 8": GOOGL's committed anchor versions, same history.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A committed recipe still outranks a different machine recipe.** Provenance is not recorded, so
  the machine's own real tag (say R1, if a name's margins turn negative and it proposes `R2_NEEDED`)
  is held like an operator's. No such build exists in the 521, and every divergence prints as a
  caveat. Falsifier: a recipe caveat that stands unacted across two re-assemblies of the same name —
  then recording provenance on the block (so only an operator's tag is kept) is due.
- **Reported, not fixed (§5.0 row 10).** `check_tier_agreement` reads `anchor.applicable`, the R1
  arithmetic's bit, as the RECIPE's. Replaying GOOGL's 09-18 build keeps `R3_forward_pe`, and the
  gate still refuses it, because that build found R1 inputs incomplete. GOOGL's `applicable` was
  False on 3 of its 8 committed anchors. Today GOOGL and AMZN both carry `applicable: true`, so an
  R3 re-tag passes the gate (measured 2026-10-07).
- **Not in this PR:** restoring the four tags — an artifact change, #671, stacked on this one.
