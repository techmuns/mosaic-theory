---
id: 2026-10-07-artifact-pass-forward-multiple-history
status: shipped
date: 2026-10-07
prs: [677]
supersedes:
superseded-by:
---

# Artifact pass: 23 pages carry the forward-multiple history; FUBO, ORKA and TECX wait for a re-assembly

**WHAT.** One pass over the 26 committed dossiers through `refresh_dossier`. The step
`top_level=forward_multiple_history_transform` writes #676's `forward_multiple_history` layer, and
`mirror_to_frontend()` runs once at the end. There is no LLM call and no re-assembly, and every
stored synthesis is kept.

**WHY.** Operator instruction, 2026-10-07: "merge 676 and run the artifact pass".

**WHAT MOVED, measured against main @bc3954c2:**
- **Files.** 46 changed, nothing else: 23 `dossier.json` and their 23 frontend mirrors. Each
  `dossier.json` gains one block, before `anchor`: +18,773 lines in all, none removed.
- **Unchanged on 26 of 26:** every `dossier.md`, the synthesis, the anchor and the mechanical layer.
  No renderer reads the layer.
- **Landed on 23.** Each layer equals the builder's output. Its `source_sha256` is the one export
  the page's trailing bands name, and that export is the file on disk.
  - Bands on all four series: 17 names.
  - Partial: AORT 1, LLY 2, NFLX 3, V 3 and VITL 2 of 4.
  - None: UBER, whose latest column reads '-' on all four rows.
  - Every missing band is named in the layer's `withheld`.
- **Left alone: FUBO, ORKA and TECX.** Their pages carry no trailing band, so no stamped export,
  and the step refuses to guess (#676's record). Their files are byte-identical.

**HOW VERIFIED.**
- **Per name, printed by the pass:**
  - whether the layer landed or was left alone;
  - the layer's vintage beside the page's stamp;
  - the layer's as-of date;
  - bands and withheld counts;
  - equality with the builder.
  On every name, nothing moved outside the new key, and `anchor` stayed last.
- **Refusals.** None.
- **Frontend mirror.** Byte-identical to its source: md 26 of 26, json 26 of 26.
- **Claim check, before the pass.** Every open PR (#511, #611, #616, #676) was read file by file;
  none touches `data/dossiers` or `frontend/dossiers`. The claim branch was pushed before the pass
  ran.
- **Suite.** The full offline suite ran on the refreshed artifacts; the counts are in the PR.

**BOUNDARY.**
- **Population:** the 26 committed dossiers on main @bc3954c2, and their on-disk quarterly
  Financials exports.
- **Date:** measured 2026-10-07.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Three names lack the layer** until a re-assembly. For ORKA and TECX it would carry no band
  anyway: every forward cell is non-numeric.
- **The layer's `as_of` is the Financials close, not the Estimates date.** AMZN's is 2026-09-16
  against ≥2026-10-06, and the spread across names is in #676's record.
