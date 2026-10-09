---
id:
status: shipped
date: 2026-10-09
prs: [698]
supersedes:
superseded-by:
---

# AMZN and UBER are re-tagged R4 — the operator's call on the machine's proposal, two fields each, R1's arithmetic untouched

**WHAT.** Both anchors' `recipe_hint` is set by hand to `R4_forward_ev_ebit`, each with an operator
reason:
- **AMZN:** R3 → R4.
- **UBER:** `R2_NEEDED` → R4.

The JSON diff is two lines per page (`recipe_hint`, `reason`). The write was byte-preserving
(`replace_anchor_block`), and the script asserted that every other key and every byte before the
anchor were unchanged. The pages were re-rendered from the stored record and the mirror ran. No
LLM ran, there was no re-assembly, and no code changed. Like #671's hand restores, a hand re-tag is
not a code writer, so it adds no `layer_refreshes` entry.

**WHY.** Operator instruction, 2026-10-09: "merge 697 and re-tag AMZN and UBER to R4". On
2026-10-09 the operator ruled that the machine's R4 proposal never overwrites a committed recipe,
and that the operator re-tags both names (`2026-10-09-r4-machine-proposal.md`).

**THE REASONS ARE DRAFTED FROM MEASURED VALUES.** Measured 2026-10-09 on the committed pages, with
the non-operating count from the merged extractor. The machine itself proposes R4 for both, with all
three conditions met:

| | AMZN | UBER |
|---|---|---|
| 1. NTM EBIT > 0 | CIQ NTM TEV/EBIT 23.3x | 15.4x |
| 2. R1 cannot anchor | EBITDA basis divergent, 3.14× | R1 declines (no positive operating margin over available history); EBITDA basis divergent, 4.01× |
| 3. R3 cannot price it cleanly | FY P/E struck on GAAP EPS; 3 of 4 quarters material | GAAP; 3 of 4 |

UBER's reason also states why R2 does not fit: it is the pre-profit, survival-gated recipe, and
UBER trades at 15.4x forward EBIT.

**WHAT IT MOVES.**
- **The scenario gate.** It accepts an R4 record on both pages and refuses an R3 one
  (`check_tier_agreement`). UBER's R1 `applicable=False` no longer blocks it (the R4 exception,
  #691).
- **The template.** `scenario-propose` emits the R4 template on both real pages, with each page's
  CIQ bridge as `net_debt`: AMZN $128,647M, UBER $10,423M.
- **A re-assembly keeps the tag** (`_keep_committed_recipe`). The machine's proposal now agrees
  with it, so no "recipe kept" caveat will name a different recipe.

**HOW VERIFIED.**
- The JSON diff on each page is exactly `recipe_hint` and `reason`, asserted by the write.
- Each `dossier.md` moved two lines: the Method row and the reason.
- The mirror is byte-identical for both pages.
- The gate and template checks were run on the re-tagged pages (above).
- **The re-tag turned nine tests red, as the artifact-pass rule anticipates.** They assumed the old
  tags: AMZN as "the R3 page", each page's committed anchor standing in for R1's read, UBER
  committed `R2_NEEDED`, and every template having a revenue axis. They were fixed in a test-only
  commit, each keeping its invariant:
  - GOOGL is now the R3 page;
  - R1's stand-in is R1's own tag for its `applicable` bit;
  - the pre-re-tag tags are constructed in a temp copy where the test needs disagreement;
  - the driver no-truncation check reads every axis the template carries, so it now covers the
    R4 template too.

  New pins cover the committed state: the two R4 pages get the R4 template, and a committed R4
  that the build also proposes draws no "recipe kept" caveat. Three proposal mutants were re-run
  against the updated tests, and all were killed.
- **Claim check:** open PRs #511, #611, #616 and #695 touch no dossier page. The claim branch was
  pushed before the edit.
- **Suite:** the full offline suite ran on the committed artifacts; the counts are in the PR.

**BOUNDARY.**
- **Population:** AMZN's and UBER's committed dossiers at main @f487eeb3.
- **Date:** measured and edited 2026-10-09.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **UBER's page reads "Method | R4_forward_ev_ebit | NOT applicable".** The screening-context
  Method row, in both twins, prints R1's `applicable` bit beside whatever recipe is tagged. On an
  `R2_NEEDED` page that read correctly (R1 not applicable, R2 needed). Beside R4 it reads as a
  verdict on R4, which it is not. AMZN shows "applicable", the same coupling in the benign
  direction. Fixing it changes the render, so it goes under the preview rule as its own PR. This
  is the render twin of the gate coupling §5.0 row 10 records (#670).
- **Next:** the first R4 record — `scenario-propose`, then the analyst's six inputs, then
  `scenario-create`.
