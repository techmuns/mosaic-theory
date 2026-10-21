---
id: 2026-10-21-theme-intelligence-enrich-is-a-refresh
status: recorded
date: 2026-10-21
prs: [763]
supersedes:
superseded-by:
---

# Theme intelligence: a company-proposal refresh (`enrich`) joins the scan's week, as a price refresh does

**WHAT.**
- `report.REFRESH_MODES = ("market", "enrich")` names the runs that change only what the stored
  theses SHOW and analyse no article:
  - their prices (`PRICE_ONLY_MODES`);
  - the companies their steps imply (`enrich`, display only, never read by a priority rule).
- Every refresh follows `report.follows`: it belongs to the week of the scan it follows, never a
  week of its own, never the next scan's.
- Only a price refresh sets the label's "prices as of …".

**WHY.** One of the review fixes of #760: the theses the one-registry merge left without company
proposals get them before the desk is republished.
- A manual `enrich` of those theses on a working copy of the registry of record (2026-10-21,
  run R-20261021T114639Z-enrich: 11 theses enriched, $0.4101) made the desk open on "21 Oct 2026
  — manual runs since the last weekly scan": 0 articles, 0 rows.
- That is the market step's defect (#759) through a mode the rule did not name. Caught on the
  working copy, before anything was pushed or published.

**HOW VERIFIED.**
- **The same working copy**, after the enrich and a $0 `market` run (R-20261021T115013Z-market):
  - with main 508922ba it opens on the empty "21 Oct" week;
  - with this branch, on "Week of 12–21 Oct 2026 · with research re-read after the scan": 15
    articles, 22 rows. The `enrich` run sits in that week.
- **Pins** (`tests/test_theme_intelligence_desk_weeks.py`, 2):
  - END TO END through `publish`: the refresh joins the scan week, the next scan's report never
    takes it, and a later-dated refresh never claims newer prices;
  - NEGATIVE: before any scan it is a manual run like the rest.
- **Mutation:** 4 mutants, all killed:
  - `enrich` not a refresh;
  - `follows` reading prices only;
  - the refresh dropped from the week;
  - `enrich` counted as prices (killed only after the pin gained the later-dated refresh).

**BOUNDARY.** The working copy is `theme-intelligence-state` d1d192b7 pulled into a fresh data
dir on 2026-10-21, plus the two runs above. The enrichment covers the 12 active theses without a
set for their current version, less TH-393DF5CD2B, which is held for review
(`REVIEW_NEEDED`) and is skipped by `enrich`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **`reassess` and `reanalyse` stay research.** They re-grade or re-read and can change an
  action, so they still open the week in progress.
- **Falsifier:** a manual mode that analyses no article and is not in `REFRESH_MODES` opening an
  empty week.
