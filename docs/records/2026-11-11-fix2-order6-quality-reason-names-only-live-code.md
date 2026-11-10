---
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, order 6, RBC-D10: the CIQ scale check's "not run" reason states today's cause, and every code name a quality reason gives must exist. The 2026-11-11 CIQ quality snapshot carries the new words (FUBO's row)

**WHAT.**
- **The defect.** `vinci/quality/sources/ciq.py`'s `ciq_scale_vs_revenue` said a page without
  `anchor.ciq_scale_check` either predates the field, or "the back-fill could not prove the
  folder's Financials export the page's own (`ciq_scale_backfill.scale_check_backfill`)". #905
  retired that back-fill and its module, so for any page built since, the second cause cannot be
  the cause. The words were kept on purpose so the latest committed scorecard reproduced byte for
  byte.
- **The fix.** The reason now reads "no anchor.ciq_scale_check — the page predates the field, or
  an anchor-backfill could not read its CIQ folder; an assembly, or an anchor-backfill that reads
  the folder, writes it". Two writers set the field: assembly (`assemble._assembly_anchor`) and the
  $0 `vinci anchor-backfill` (`cli._machine_anchor`, pinned in
  `tests/test_ciq_bridge_currency_and_scale.py`), which writes the anchor without it when the
  folder raises on read. (Review round 0: a first draft said "no back-fill writes it … only an
  assembly writes it", which `anchor-backfill` contradicts.)
- **The guard** (`tests/test_quality_not_run_reasons.py`). Every parenthesised code name in a
  `not_run=` reason of a quality source must resolve under `vinci.dossier`. It reads the reasons by
  the AST, so only those strings count, and follows a reason held in a module-level constant
  (`_ABSENT`, shared by the stored cross-checks). Today it resolves four names, the `refresh`
  functions the CIQ source cites. At `origin/main` it finds a fifth, the retired back-fill.
- **The artifact.** `data/snapshots/data_quality/ciq/2026-11-11.json`, regenerated at $0 from the
  committed pages (`vinci audit quality --source ciq --write`), in its own commit. It is the latest
  snapshot, so the reproduction pin now binds to it.

**WHY.** Document 15, order 6: "a 'not run' reason names a back-fill that was removed".

**HOW VERIFIED.**
- **The one page it reaches.** On the 27 committed pages, the reason prints for FUBO alone, whose
  page was assembled on 2026-08-18 at extraction version `2026-08-16.1`, before the field existed.
  So "predates the field" is its cause, not an assumption.
- **Fail first.** With `origin/main`'s `vinci/quality/sources/ciq.py` swapped in, 2 of the 3 new
  tests fail: the guard (it names `ciq_scale_backfill.scale_check_backfill`) and the reason pin. The
  third, the guard's negative twin on a constructed module, passes on both, as it should.
- **The snapshot.** The 2026-11-09 snapshot no longer matches the committed pages (inputs sha256
  `d1ebb5ba…` against today's `6088b98f…`, AORT retired and pages re-assembled since), so main's pin
  was asserting coherence only. The 2026-11-11 snapshot reproduces from today's pages byte for
  byte (`tests/test_quality_ciq.py::test_the_committed_snapshot_reproduces_from_the_pages_it_names`).
- **What else the snapshot moves.** It differs from 2026-11-09's in 273 leaf values. Two are this
  fix: FUBO's reason, in its page row and its not-run group. The rest are the pages committed
  since 2026-11-09, scored as they stand, not caused here:
  - AORT retired, so every check counts 27 pages, not 28;
  - TECX re-assembled with the fields it lacked, so it leaves six not-run groups;
  - EPAM, UBER, V, VITL, VRRM and WLK rebuilt, with counts moving both ways.

**BOUNDARY.** The 27 committed `dossier.json` pages at `origin/main` `7adfdae4`, scored on
2026-11-11.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- Earlier snapshots keep the old words. Each is a series point for the pages it names, and is
  never rewritten.
- The guard reads parenthesised `module.function` names only. A reason naming retired code in
  other words is not caught.
