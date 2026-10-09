---
id:
status: shipped
date: 2026-10-09
prs: [699]
supersedes:
superseded-by:
---

# The screening Method row names whose bit "applicable" is — UBER no longer reads "R4 … NOT applicable"

**WHAT.** The screening-context Method row prints the anchor's `applicable` bit. That bit is R1's:
whether R1's arithmetic, the rows beneath it, can anchor the name. It printed beside whatever
recipe the page is tagged. It now says whose bit it is, in both twins (`render.py`
`_screening_context_lines` and `dossier.js` `anchorInner`):
- **Beside an R1 tag:** the plain word stays ("applicable" / "NOT applicable"), so every R1 page is
  byte-identical.
- **Beside any other tag:** "R1 screen: applicable" / "R1 screen: NOT applicable".

The ten affected pages were re-rendered from their stored JSON, markdown only, and the mirror ran.
No JSON was written, so no `layer_refreshes` entry was added: no layer moved. No LLM ran.

**WHY.** After the operator's R4 re-tags (#698), UBER's page read "R4_forward_ev_ebit | NOT
applicable", a verdict on R4 the bit never made. AORT read "R2_NEEDED | applicable", the same
coupling in the other direction. Operator instruction, 2026-10-09: "start the Method row display
fix". The preview was approved the same day. This is the render twin of the gate coupling STATE
row 10 records (#670).

**WHAT MOVED** (measured against main @58dd1ef6):
- **Ten pages, one row each,** in both twins identically: AMZN, AORT, FUBO, GOOGL, MVST, NCNO,
  ORKA, TECX, UBER, VITL.
- **20 markdown files** (+10/−10 lines): ten `dossier.md` and their mirrors.
- **The other 16 pages,** all R1-tagged, are byte-identical in both twins.

| page | before | after |
|---|---|---|
| UBER | R4_forward_ev_ebit · NOT applicable | R4_forward_ev_ebit · R1 screen: NOT applicable |
| AMZN | R4_forward_ev_ebit · applicable | R4_forward_ev_ebit · R1 screen: applicable |
| AORT | R2_NEEDED · applicable | R2_NEEDED · R1 screen: applicable |
| GOOGL | R3_forward_pe · applicable | R3_forward_pe · R1 screen: applicable |
| MVST, NCNO, VITL | R2_NEEDED · NOT applicable | R2_NEEDED · R1 screen: NOT applicable |
| FUBO, ORKA, TECX | unknown · NOT applicable | unknown · R1 screen: NOT applicable |

**HOW VERIFIED.**
- **The preview,** before and after on the real pages in both twins (UBER, AMZN, AORT, and SMPL
  unchanged as the R1 control), was approved by the operator. The block is not collapsible, so the
  screen and print states are the same, and 0 `undefined` appeared.
- **Every page, both twins, main against this branch:** exactly the ten non-R1 pages change, and
  only the Method row moves on each.
- **The repo's render-drift pin** (`test_screening_context_reaches_every_committed_dossier_e2e`)
  requires each committed page to equal the live render. The ten re-rendered pages satisfy it, as
  earlier render fixes did (#659, #434).
- **Tests** (`tests/test_method_row.py`, 4):
  - every committed page's note equals the rule for its own anchor, in markdown;
  - the web twin says the same on every page (md/web parity);
  - a non-R1 tag never carries the bare verdict, CONSTRUCTED both ways on UBER's page;
  - an R1 tag keeps the plain word.
- **Mutation.** Four mutants, all killed:

  | mutant | tests failing |
  |---|---|
  | md reverts to the bare word | 4 |
  | md prefixes R1 pages too | 4 |
  | web reverts to the bare word | 2 |
  | web inverts the bit | 2 |

**BOUNDARY.**
- **Population:** the 26 committed dossiers at main @58dd1ef6.
- **Date:** measured 2026-10-09.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **R1_NOT_ROBUST (CNXC) still prints R1's description,** because its tag starts with "R1". That is
  unchanged here, and correct: CNXC's R1 computes, and the operator's tag says only that it is not
  robust.
- **Next in the ruled build order:** the first R4 record — `scenario-propose`, then the analyst's
  six inputs, then `scenario-create`.
