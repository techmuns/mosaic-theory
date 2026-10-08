---
id:
status: shipped
date: 2026-10-08
prs: [687]
supersedes:
superseded-by:
---

# Artifact pass: every page states which EPS line its forward P/E is struck on — AMZN, AORT, UBER and VRRM on GAAP, and nothing else moved

**WHAT.** One pass over the 26 committed dossiers through `refresh_dossier`, with one top-level
step, `forward_consensus_transform` — #686's `forward_consensus.pe_eps_basis`.
`mirror_to_frontend()` then ran once.
- **No LLM, no re-assembly:** every stored synthesis is kept.
- **No code changes.**
- **The operator's ruling on #686's review finding 2** ("keep the current rule") is recorded as an
  amendment to `2026-10-08-pe-eps-basis.md`, and in STATE row 10.

**WHY.** Operator instruction, 2026-10-08: "keep the current rule, merge 686 and run the artifact
pass".

**WHAT MOVED, measured against main @56526e37.**
- **Files.** 52 changed and nothing else: 26 `dossier.json` and their frontend mirrors.
- **JSON.** +1,081 / −26 lines. The 26 removed lines are each page's last `forward_consensus` key,
  `source_sha256`, gaining a trailing comma with its value unchanged.
- **Unchanged.** On every page:
  - no other top-level key moved;
  - no other `forward_consensus` key moved (paths, spreads, revisions, `withheld`, the ladder,
    reconciliations, as-of, source);
  - `dossier.md` is byte-identical, since the field is not rendered;
  - `anchor` is still the last field.

**What the pages now say:**

| scope | gaap | normalized | indistinguishable | undetermined |
|---|---|---|---|---|
| FY rows | 4 (AMZN, AORT, UBER, VRRM) | 18 | 1 (NFLX) | 3 (FUBO, ORKA, TECX) |
| NTM row | 4 (AMZN, AORT, UBER, VRRM) | 12 | 2 (GOOGL, NFLX) | 8 |

These are identical, name by name, to #686's dry run on copies.

**HOW VERIFIED.**
- **The page's own export, by hash.** Before each write, the on-disk Estimates export's sha256 was
  checked against the `forward_consensus.source_sha256` the page carries. 26 of 26 matched; none was
  skipped or refused.
- **Per-page diff.** Every key except `pe_eps_basis` was compared against main, as was the rendered
  page. No problems on any name.
- **Mirror.** Byte-identical to its source: json 26 of 26, md 26 of 26.
- **Claim check, before the pass.** Open PRs #511, #611 and #616 were read file by file. None
  touches `data/dossiers` or `frontend/dossiers`; #511 edits STATE.md only. The claim branch was
  pushed before the pass ran.
- **Suite.** The full offline suite ran on the refreshed artifacts; the counts are in the PR.

**BOUNDARY.**
- **Population:** the 26 committed dossiers at main @56526e37, and each one's on-disk Estimates
  export (hash-matched).
- **Date:** measured 2026-10-08.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The page does not show it yet.** The basis is in the JSON (machine-complete); rendering it is a
  layout change under the preview rule, not taken here.
- **Next in the ruled build order:** step (3), the EV/NTM EBIT recipe (STATE row 10).
