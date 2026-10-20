---
id: 2026-10-20-artifact-pass-net-debt-and-lease-basis
status: shipped
date: 2026-10-20
prs: []
supersedes:
superseded-by:
---

# Artifact pass: the one net-debt builder (#749) and R1's lease basis (#750) land on the committed pages together

**WHAT.** One pass for both merged PRs, which move the same retail anchors. Operator, 2026-10-20:
"merge 749", after the plan "merge, then the single artifact pass that lands both".
1. `refresh.lease_basis_transform` on all 27 committed dossiers, through `refresh_dossier`.
2. `vinci anchor-backfill` on every name except NKE (reason below).
3. The anchors of four pages were restored to their committed state, keeping each page's lease
   basis (below).
4. AMZN's operator re-tag reason was put back verbatim (below).
5. CNXC's companyfacts fixture was refreshed to the vintage its anchor now reads.
6. `mirror_to_frontend()` ran once, and `ANCHORS_AWAITING_BACKFILL` emptied.

**WHAT MOVED** (committed → new; R1 base value per diluted share, net debt $M).

| name | base | net debt | basis |
|---|---|---|---|
| AMZN | 249.57 → 276.71 | 119,007 → 23,783 | ex-lease (R4 recipe; R1's arithmetic kept on the block) |
| AORT | 19.79 → 25.50 | 331 → 290 | ex-lease |
| BURL | 183.42 → 322.06 | 5,338 → 1,210 | ex-lease |
| CNXC | 62.55 → 93.27 | 5,249 (CIQ fill) → 4,131 | ex-lease |
| EPAM | 352.35 → 398.58 | −637 → −764 | ex-lease |
| NFLX | — → 52.00 | — → 5,181 | ex-lease, newly valued |
| PARR | 34.01 → 47.86 | 949 → 567 | ex-lease |
| ROST | 132.16 → 166.18 | 451 → −3,270 | ex-lease |
| SMPL | 43.33 → 44.10 | 325 → 273 | ex-lease |
| TGT | 137.57 → 158.47 | 14,804 → 9,946 | ex-lease |
| TJX | 88.52 → 129.10 | 8,313 → −3,133 | ex-lease |
| VITL | — → 29.84 | 87 → 17 | ex-lease, newly valued |
| WERN | 30.82 → 32.53 | 897 → 784 | ex-lease |
| WLK | 105.98 → 115.51 | 4,024 → 3,215 | ex-lease |
| NCNO | (R2, no base) | 255 → 243 | ex-lease |
| UBER | (R4, no base) | 7,565 → 9,562 | lease-inclusive (ex-lease band refused) |
| TECX | (no base) | −208 → −223 | CIQ fill: EDGAR now refuses its phantom 2023 debt |

- BRBR, GOOGL, IT, LLY, MVST, V and VRRM gained only the lease-basis block; their anchors are
  unchanged. FUBO gained nothing. NKE and ORKA are unchanged.
- Every page's lease-basis conflict ("the anchor predates the page's lease basis") is cleared.
  IT's and LLY's share-count conflicts predate this pass and remain.

**THREE EFFECTS, STATED SEPARATELY.** Each name was recomputed on fixed inputs (the pages after
step 1, the frozen companyfacts fixtures) with main just before #749, with #749, and live:
- **#750's lease basis** carries most of every move: e.g. BURL 183.42 → 319.93, TJX 88.52 → 129.10.
- **#749's net-debt reading** adds BURL 319.93 → 322.06, TGT 155.94 → 158.47, WERN 32.39 → 32.53
  and AMZN 276.81 → 276.71. It also values NFLX (its EDGAR net debt now reads), and moves UBER's
  and TECX's net-debt fields.
- **Fresh-EDGAR drift** is zero on every name except two:
  - CNXC +3.19, a 10-Q filed after its fixture: its diluted shares 60,862,000 → 60,910,000. Kept,
    because #750 moves CNXC anyway; stated here; the fixture refreshed in the same pass.
  - NKE −0.66, which NEITHER change moves, so NKE was not backfilled (#685's rule: a backfill
    elsewhere imports only drift).

**WHAT WAS DELIBERATELY NOT WRITTEN.**
- **Four anchors restored.** The backfill also moved GOOGL, LLY, FUBO and MVST's anchors for
  reasons unrelated to either PR:
  - GOOGL's CIQ workbook filename (same sha);
  - LLY's, FUBO's and MVST's CIQ vendor fills, the pre-existing fills `test_dilution_denominator`
    records as "their own decision".
  Their files were restored and the lease-basis block re-applied alone.
- **AMZN's operator reason restored.** `anchor.preserve_operator_tag` keeps a committed reason
  only when the recipe CHANGES. It rests on "no operator note under an unchanged recipe appears in
  the committed history", and AMZN breaks that: its reason is the 2026-10-09 OPERATOR RE-TAG to
  R4, and since #697 the machine proposes R4 itself, so the backfill replaced the note with its
  own text. Put back verbatim through the anchor writer's own calls (`write_recorded`, then the
  re-render); open as STATE row 27 (7).

**HOW VERIFIED.**
- **Dry run first:** 27 names, 22 changed, bases printed; the write matched it on every kept name.
- **Field diff:** the lease step changed only `valuation.lease_basis`, `layer_refreshes`, and the
  derived `valuation_basis`/`qa_flags` conflict. Its page diffs are citation renumbering (one new
  source note) plus the basis line; no line was lost (checked on TJX line by line).
- **Corpus pin:** `test_the_period_fix_moves_the_committed_anchor_and_exactly_these_names` passes
  with the set EMPTY, so every committed anchor equals a fresh recompute from the fixtures.
- **Suite (CI-equivalent):** store and workbooks moved aside, 6,007 passed / 525 skipped.
  - With the workbooks present, 457 more tests run and 5 fail. They fail identically on main
    53cbe9fe, untouched by this pass: they read this machine's CIQ folders (an MCK panel stamp, a
    duplicate GOOG folder of "2.12.06 PM" exports, a share-basis row). CI never runs them.

**BOUNDARY.**
- **Code:** main 53cbe9fe (#749 on #750/#751).
- **Pages:** the 27 committed dossiers.
- **CIQ:** the primary checkout's workbooks, copied read-only 2026-10-20 (36 folders).
- **EDGAR:** companyfacts read live 2026-10-20 by the backfill's own client.
- **Units:** $M; bases in $ per diluted share.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The anchors move a lot**, by design of #750, which the operator merged:
  - BURL +76%, TJX +46%, CNXC +49%, PARR +41%;
  - ROST's and TJX's net debt turn to net cash once operating leases leave the bridge.
  The page's displayed band stays CIQ's (as #750 recorded).
- **NKE has no lease basis.** Its CIQ folder is named `NIKE` and the transform looks folders up by
  ticker. NKE is a lease-heavy retailer, so its page still prices R1 on CIQ's mixed history. Open
  as STATE row 27 (6).
