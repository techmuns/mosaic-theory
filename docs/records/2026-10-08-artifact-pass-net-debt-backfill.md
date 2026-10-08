---
id:
status: shipped
date: 2026-10-08
prs: [685]
supersedes:
superseded-by:
---

# Anchor backfill: the securities leg reaches the five pages it moves — GOOGL's net debt reads −$121,683M, and nothing else moved

**WHAT.** `vinci anchor-backfill --tickers AMZN,GOOGL,UBER,VRRM,WLK`, the anchor-only writer:
- no re-assembly, no LLM;
- operator recipe tags preserved (AMZN and GOOGL stay `R3_forward_pe`);
- changed pages re-rendered from the stored record.

`mirror_to_frontend()` then ran once. `ANCHORS_AWAITING_BACKFILL` goes from `{AMZN, VRRM, WLK}`
back to empty, and §5.0 row 27's backfill item closes.

**WHY.** Operator instruction, 2026-10-08: "merge 684 and run the anchor backfill". #684 made the
anchor's net debt net the short-term securities a CIQ TEV nets
(`2026-10-08-net-debt-nets-short-term-securities.md`). These five are the names it moves.

**WHAT MOVED, measured against main @3817c7ad.**

*Files.* 19 changed besides this record and STATE.md: five `dossier.json`, four `dossier.md`, their nine frontend mirrors, and the test
constant. UBER's page prints no anchor net debt (its R1 anchor is inapplicable), so its `dossier.md`
has nothing to re-render.

*Fields.* In every `dossier.json`, every field outside `anchor` is unchanged. Inside `anchor`,
exactly three fields moved:
- `net_debt` (value and bridge text);
- `anchor_base_value_per_share`, where R1 applies;
- `computed_at`.

| name | net debt ($M) | screen value / share |
|---|---|---|
| GOOGL | +64,880 → −121,683 | $197.01 → $212.17 |
| AMZN | 163,782 → 119,007 | $245.46 → $249.57 |
| WLK | 4,233 → 4,024 | $104.35 → $105.98 |
| VRRM | 1,038.131 → 1,032.894 | $21.75 → $21.79 |
| UBER | 8,086 → 7,565 | — (R1 inapplicable) |

*Rendered pages.* One line changed on each of the four re-rendered pages: "Screen value / share".

**TWO EFFECTS, STATED SEPARATELY.** A backfill re-reads EDGAR, so it can carry fresh-facts drift
beside the change it was run for. Here that drift is **zero**:
- each new base equals what #684 measured on a frozen 2026-10-08 pull with the same code;
- no other anchor field moved — margin, multiple, D&A, diluted shares, LTM revenue and FCF are all
  byte-identical.

The whole move is the securities leg.

**HOW VERIFIED.**
- **Dry run first:** 5 of 5 changed, with the bases printed; the write matched it.
- **Diff:** a field-by-field diff of every page against main, shown above.
- **No leftover figures:** none of the old net-debt figures survives in any of the five pages' JSON
  or markdown.
- **Mirror:** byte-identical to its source for all five names (json and md).
- **Corpus pin:** `test_the_period_fix_moves_the_committed_anchor_and_exactly_these_names` passes
  with the set empty — committed JSON and a recompute from the fixtures agree on every applicable
  anchor.
- **Claim check, before the pass.** Open PRs #511, #611 and #616 were read file by file. None
  touches these five pages, their fixtures, or the test; #511 edits STATE.md only. The claim branch
  was pushed before the write.
- **Suite:** the full offline suite ran on the refreshed artifacts; counts in the PR.

**BOUNDARY.**
- **Population:** the five names #684 moves, of the 26 committed dossiers at main @3817c7ad.
- **EDGAR:** companyfacts read 2026-10-08 through the backfill's own `EdgarClient`.
- **CIQ:** Financials workbooks as on disk 2026-10-08 (the same files #684's fixture names by sha).
- **Units:** $M; per-share values in $ per diluted share.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Row 27 keeps two items, neither scheduled:**
  - the screen's EDGAR snapshot still nets cash only;
  - the debt-side gaps to CIQ are not itemized (AMZN −$9,640M, UBER −$1,775M).
- **The other 21 pages were not backfilled.** #684 does not move them, and a backfill there would
  only import fresh-facts drift unrelated to this change.
