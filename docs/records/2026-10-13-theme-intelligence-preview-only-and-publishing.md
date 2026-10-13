---
id: 2026-10-13-theme-intelligence-preview-only-and-publishing
status: recorded
date: 2026-10-13
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — SemiAnalysis preview-only by decision, a Morgan Stanley article analysed, publishing decided

**WHAT.**
- **SemiAnalysis is preview-only** (operator decision 2026-10-13: "stay on its preview process as
  we dont want to buy its subscription"). A new channel setting, `paywalled_posts` (default
  `"request"`), is set to `"preview_only"` for SemiAnalysis in `sources.toml`.
  - A paid post's free preview is analysed and labelled a preview (still PARTIAL, never upgraded),
    and the full post is never requested.
  - **Health check:** still DEGRADED with completeness WARN, which says what it reads, but no
    upload request (`next_action`: "none to supply …").
  - **Desk Uploads and the weekly report's intake:** neither lists the preview nor shows the
    channel's request. That includes the request stored by the 2026-10-12 check, BEFORE the
    decision; `health.asks_only_for_previews` reads the stored test results.
  - **Articles:** says "Preview only — by decision, never requested".
  - **Sources:** says "paid posts read as their preview — by decision".
  - **The decision covers paid posts only.** A page that LINKS a fuller report is still requested
    (`linked_reports`). A page that is partial for any other reason (a teaser) still raises the
    check's request.
- **Morgan Stanley's "China's Next Industrial Revolution: The Industry 5.0 Opportunity"**, supplied
  by the operator (a PDF of the public page, dated 25 Sep 2026 on the page). It was analysed into
  the pilot registry after a backup (`backups/registry-20261013T164347Z.db`):

  | Run | Cost | Imported as | Figures | Result |
  |---|---|---|---|---|
  | `R-20261013T164348Z-ingest` | $0.8075 | a new article, read in full (its address found on morganstanley.com's own search: `/insights/articles/china-next-industrial-revolution-industry-5-outlook`) | 32 of 32 captured | two new theses, both SKIP: "China's $12tn Industry 5.0 capex supercycle benefits automation, robotics, semis, software suppliers" (`TH-A381AB426E`) and "Multipolar industrial reorg: regional specialization creates cross-market selection opportunity" (`TH-1838CDDC15`) |

  - **Why the scan could not fetch it.** Morgan Stanley's site drops every connection from the
    scan's honest research user agent, robots.txt included. A robots.txt that cannot be read
    fails closed, and the channel is manual-first by the 2026-10-11 decision. The same page opens
    in an ordinary browser. Reading it automatically through a browser would bypass the site's
    refusal of automated access, so the route stays an upload.
- **Publishing decided** (operator, 2026-10-13): publish the current snapshot once #703 is merged.
  Weekly publishing stays MANUAL for now (one `publish` and an artifact commit each week), to be
  revisited after the first few weekly runs. Recorded in the guide.
- **The Goldman Sachs link was checked, not changed.**
  - `https://www.goldmansachs.com/insights/goldman-sachs-research/` loads Goldman's research page
    in a browser on this machine, as do the no-"www" and `http://` forms (they redirect).
  - In the app it is a complete link opening in a new tab.
  - The earlier chat reply had written it without "https://", which the app can take for a
    file path. The browser pane inside the desktop app does not open new-tab links.
  - Morgan Stanley's "Where to look" page (`/what-we-do/research`) lists 23 article links,
    including the one supplied.

**WHY.** The operator's three decisions, and an article supplied by hand because the scan cannot
reach Morgan Stanley.

**HOW VERIFIED.**
- **Real run.** The one above: SUCCEEDED, $0.8075, 5 model calls (extract, complete, review).
- **The rendered desk from a copy of the updated registry:**
  - Uploads asks for nothing from SemiAnalysis; its remaining requests are Morgan Stanley's and
    Goldman Sachs's standing ones and Citi's, whose article reads "supplied and analysed";
  - Articles says "Preview only — by decision" on both SemiAnalysis previews;
  - 0 broken links and 0 default-view problems on the standalone pages;
  - no horizontal overflow on four routes at 1440 and 390 px.
- **Pins.**
  - Health: the same paywalled site asks for an upload under `"request"` and for nothing under
    `"preview_only"`, still DEGRADED with completeness WARN; a teaser on a preview-only channel
    is still requested (negative).
  - Desk and report: a preview-only paid post is never requested (Uploads, intake, the stored
    pre-decision request) and Articles says so. A `"request"` channel's preview, and a
    preview-only channel's page linking a fuller report, are still requested (negative).
  - Config: only SemiAnalysis is preview-only.
  - Mutants: 7 of 7 killed.
- Ruff and `mypy --strict` are clean; the offline suite result is in the PR.

**BOUNDARY.**
- **Pilot registry:** `data/theme_intelligence/v2/pilot-2026-10-12/registry.db` (the
  `theme-intelligence` worktree). Model calls 36 → 41; spend $7.0803 → $7.8878 of the $18 budget,
  from its `llm_calls` on 2026-10-13.
- **"23 article links":** anchors to `/insights/articles/` or `/ideas/` on
  morganstanley.com/what-we-do/research, read in a browser on 2026-10-13.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.8075 of model spend.
- **Reported, not fixed:**
  - The reader missed the article's printed date ("Sep 25, 2026" below the headline, after the
    site's menu lines). It was stated with `--published` (labelled operator-stated).
  - The article's title carries the browser tab's " | Morgan Stanley" suffix.
  - The run's own output pages failed to write: the desk code was edited while the run was
    still going, so the run's loaded config and its later-loaded desk module disagreed. The
    registry write had completed; nothing was lost.
- **OPEN, mine once #703 is merged:** publish the current snapshot (`publish`, then an artifact
  commit).
