---
id: 2026-10-07-artifact-pass-horizon-read-and-forward-consensus
status: shipped
date: 2026-10-07
prs: [675]
supersedes:
superseded-by:
---

# Artifact pass: the 26 pages print each metric's own revision counts and carry the forward-consensus layer — no LLM, every synthesis kept

**WHAT.** One pass over all 26 committed dossiers through the one write path, `refresh_dossier`:
- `transform=horizon_read_transform` lands #674's correction of `catalyst_path.horizon_read`;
- `top_level=forward_consensus_transform` writes #673's `forward_consensus` layer;
- `mirror_to_frontend()` runs once at the end.

There is no LLM call and no re-assembly. Both steps are deterministic reads of the on-disk CIQ
Estimates export, and every stored synthesis is kept.

**WHY.** Operator instruction, 2026-10-07: "merge 674 and run the artifact pass". STATE §5.0 row 30
items (A) and (B) waited on it.

**WHAT MOVED, measured against main @c2014d76:**
- **Files.** 104 changed: for each name, `dossier.json`, `dossier.md`, `frontend/dossiers/<T>.json`
  and `frontend/dossiers/<T>.md`. Nothing else.
- **Inside each `dossier.json`, exactly two things:**
  - the `horizon_read` value;
  - a new `forward_consensus` block, which sits before `anchor`, so `anchor` stays the last field.
  Synthesis, anchor and every other mechanical field are unchanged on 26 of 26.
- **`horizon_read`.** These are the figures #674 measured, now on the pages: 114 lines corrected,
  24 added, 2 removed (431 → 453). 51 of the corrected lines flip net direction.
- **`forward_consensus`.** These are #673's fleet figures: 676 paths, 624 spreads and 1,971 revision
  counts. 21 cells are withheld, each with its reason: 14 on the pre-revenue ORKA and TECX, 6 on
  CNXC, 1 on WERN.
- **Rendered pages.** Only the horizon block's revision lines and its '+N non-headline rows' tally
  moved. Every `dossier.md` is byte-identical to #674's horizon-only dry run, and no renderer (page
  or web) reads `forward_consensus`.

**VINTAGE — EACH PAGE GETS ITS OWN EXPORT.** The correction and the layer both come from the export
the page was assembled from:
- **`horizon_read`.** The old bounding rebuilds the stored string byte-for-byte on 26 of 26. This
  is the transform's own gate.
- **`forward_consensus`.** Its `as_of` equals the page's `catalyst_path.as_of` on 26 of 26. The
  export floors run from ≥2026-05-15 (MVST) to ≥2026-10-06 (AMZN, NFLX).

**HOW VERIFIED.**
- **Per name.** The pass printed, for each of the 26:
  - the corrected value equals the own-block read;
  - the vintage is equal;
  - `anchor` is still last;
  - no JSON path moved outside the two fields.
- **Refusals.** None. No `known_wrong.json` seal exists.
- **Frontend mirror.** Byte-identical to its source: md 26 of 26, json 26 of 26.
- **Claim check.** Before the pass, per RUNBOOKS ("A FLEET-WIDE PASS CLAIMS EVERY NAME"), every open
  PR (#511, #611, #616) was read file by file; none touches `data/dossiers` or `frontend/dossiers`.
  The claim branch was pushed before the pass ran.
- **Suite.** The full offline suite ran on the refreshed artifacts; the counts are in the PR.

**BOUNDARY.**
- **Population:** the 26 committed dossiers on main @c2014d76, and their on-disk CIQ Estimates
  exports.
- **Date:** measured 2026-10-07.
- **Units:** a line is one metric × one FQ period. The layer's counts are as #673 defines them.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The layer is in the JSON tier only.** No page renders `forward_consensus`, and the synthesis
  does not read it. Whether it gets a digest is row 30's next decision.
- **Every stored synthesis was drawn from the wrong counts** (#674's record). None cites a count
  that moved. Whether an uncited count moved a lean cannot be answered from the text. Re-drawing
  one means re-assembling the name, which is the operator's call.
- **Size.** The layer adds 50,711 lines of JSON across the 26 `dossier.json`, and the same again
  in their frontend mirror.
