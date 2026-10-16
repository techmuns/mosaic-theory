---
id: 2026-10-16-theme-intelligence-pilot-catch-up
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — the live pilot caught up with main: re-graded, priced, and the desk republished

**WHAT.** Operator, 2026-10-16: "yes, run the pilot catch-up". The pilot had last run on
2026-10-14, at the 14 Oct code. About 25 PRs since (the review groups, #730–#737) had not reached
its data or the desk. All steps were $0: no model call.

1. **Backup.** The live registry was copied, by SQLite's backup API on a read-only connection and
   before anything opened it, to
   `data/theme_intelligence/v2/pilot-2026-10-12/backups/registry-pre-v7-20261016T1630Z.db`
   (schema v5, integrity ok, 23 theses). The CLI's own `backup` command opens the store first, so
   it would have migrated the file before copying it.
2. **Checkout.** The pilot worktree moved from 11e77e49 to main a66a81e0 (#737). It was clean.
3. **Re-grade** (`reassess --as-of 2026-10-16`, run R-20261016T163144Z-reassess). 19 theses were
   re-graded from stored evidence and 5 changed. The first open migrated the registry v5 → v7.
   - TH-DEE87FCF51 (in-vivo gene editing): SKIP → WATCH · on hold, as STATE predicted.
   - The 7 SKIP theses were archived by the review groups' rules, leaving the active list.
   - TH-2FFD9B58A8 (AI boom / US risk premium): "0 listed · 3 sector" → no exposure (#737:
     Treasurys, US equity and USD assets are not sectors). WATCH · on hold before and after.
   - TH-1516B6186B, TH-16225B12C4 and TH-7C895A0A4E: WATCH → WATCH; the F6 value is restated in
     the current form.
   - Before: 19 active (12 WATCH, 7 SKIP), 4 archived. After: 13 active, all WATCH · on hold; 10
     archived.
4. **"Is it priced?"** (`market --as-of 2026-10-15`, run R-20261016T163302Z-market). All 13
   active theses are priced.
   - 2026-10-15 is the last complete session. The run was on Friday 16:30 UTC with the US market
     open, so today's bar would have been partial.
   - 51 rows (counted exposures plus the companies each thesis implies): 50 with a last close; 27
     with a P/E-against-its-own-history percentile, each labelled with its window; 5 with
     consensus revisions (the fund's dossier names).
   - Every figure not held says why: losses throughout, a share-basis change inside the window,
     too short a history, or stale annual EPS.
5. **Desk republished** (`publish`, at a66a81e0, from a SQLite-backup copy of the registry, the
   practice since #721). 79 files and 23 thesis pages from R-20261016T163302Z-market, all under
   `frontend/theme-intelligence/`.
   - Publishing left the live checksum unchanged.
   - A leak scan of the folder (local paths, keys, tokens) found nothing.
   - The full offline suite ran green on the published files before the commit.

**WHY.** The rulings and fixes of #730–#737 change what the desk says about real theses. They
apply only when the data is re-graded and the desk republished. On the published desk, the
exposure counts were 14 Oct's and "Is it priced?" read "not computed".

**HOW VERIFIED.**
- Each thesis's status, version, action, WATCH label and F6 were read from the pre-v7 backup and
  from the live registry after the re-grade, each through a copy. The changes above are the
  complete diff, and they match the predictions in STATE (8)(g) and #737's re-grade of a pilot
  copy (TH-2FFD9B58A8 the only exposure change).
- The market panels were read back from the registry: 13 contexts, the counts above.
- The published thesis page for TH-16225B12C4 was rendered and checked. Its panel prices Monster
  Beverage, Celsius, Keurig Dr Pepper and PepsiCo as of 2026-10-15, with P/E-history windows
  labelled "2y" / "5y" and "not held" where a figure is missing.
- The live registry's checksum: 5fcc240d4b087d2feb1f81e6d6fabc3c before (v5);
  7c5840a55993419a4e7abf3846004afe after the re-grade and the market step; unchanged by
  publishing.

**FOUND, NOT FIXED.** The CLI's `market` command does not load `.env` locally. `__main__.py`
calls `load_local_env()` only inside the model-client setup, which `market` never reaches.
- The first market attempt failed on a missing POLYGON_API_KEY before any fetch. It is recorded
  as FAILED run R-20261016T163210Z-market and kept: the registry is append-only.
- The rerun passed the repo's `.env` into the command's environment, as Actions injects its
  secrets. No value was printed.
- The Actions run is unaffected. The fix (load `.env` once at the CLI entry, with a test) is a
  separate change.

**BOUNDARY.**
- Run 2026-10-16 between 16:30 and 16:40 UTC, on the live registry at
  `data/theme_intelligence/v2/pilot-2026-10-12/` in the pilot worktree, with code at main
  a66a81e0.
- Re-grade as of 2026-10-16; prices and filings as of 2026-10-15.
- "Active" = status ACTIVE on the current thesis record.
- Market rows = each active thesis's current version: its counted exposures plus its enrichment's
  SEC-verified, US-filing companies.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The live registry is now v7, so code older than #731 refuses it. The v5 backup is beside it.
- The stored company proposals still predate their checked basis; only a paid re-enrichment
  refreshes them (an operator decision). For a thesis whose sector names #737 refuses, the
  enrichment prompt has changed, so its cached proposals no longer match, and its next enrichment
  is a fresh paid call.
