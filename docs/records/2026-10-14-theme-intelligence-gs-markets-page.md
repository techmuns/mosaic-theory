---
id: 2026-10-14-theme-intelligence-gs-markets-page
status: recorded
date: 2026-10-14
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — Goldman Sachs's Markets page a second place to look; Bank of America stays retired

**WHAT.**
- **Goldman Sachs Markets as a second "Where to look"** (operator decision 2026-10-14: "Add
  Goldman's Markets page as a second 'Where to look' link? — Yes").
  - **Config:** a channel setting `research_pages` holds further pages of a channel's research
    for a PERSON to check. They are shown beside `entry_url` and never discovered, fetched or
    health-checked. Goldman Sachs carries `https://www.goldmansachs.com/insights/markets`.
  - **Where it shows:** Uploads ("Where to look: goldmansachs.com/insights/goldman-sachs-research
    · goldmansachs.com/insights/markets") and Sources ("research pages: …").
  - **The Research page stays the main one:** deep thematic pieces, about two a month. Markets is
    shorter articles each week, plus podcasts and videos (2026-10-14 comparison).
- **Bank of America stays retired** (operator, 2026-10-14: "No"), though it is on the operator's
  original shortlist. Nothing changes; the guide says so.

**WHY.** The operator's two answers to the open questions of
`docs/records/2026-10-14-theme-intelligence-ms-batch-citi-links.md`.

**HOW VERIFIED.**
- **Pins:**
  - Sources shows Goldman's two pages in order, while Morgan Stanley (no extra page) shows
    exactly one (negative);
  - Uploads links both Goldman pages;
  - config: only Goldman has extra pages.
  - Mutants: 2 of 2 killed.
- **The live local preview** (the app on 127.0.0.1:8895, the pilot registry published, not
  committed): Goldman's request links both pages, and Morgan Stanley's links its one; no console
  errors.
- Ruff and `mypy --strict` are clean; the offline suite result is in the PR.

**WHAT IT COSTS / WHAT IS ACCEPTED.** $0. The Markets page is never read by the scan: Goldman
refuses automated access, and its research arrives by upload.
