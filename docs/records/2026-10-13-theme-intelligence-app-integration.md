---
id: 2026-10-13-theme-intelligence-app-integration
status: recorded
date: 2026-10-13
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — the runner says what it cannot read, one theme across every page, and the desk inside the main app

**WHAT.** Three changes before merge, at the operator's request.
- **1. "Not checkable on this machine"** (`report.groups_unread`).
  - **The problem:** the weekly runner rebuilds the registry from the state branch's export, which
    carries no article text. So it could not read the business groups in a thesis's evidence
    paragraphs, and every surface then said "none" or "the source names no company or sector" — a
    false statement on every weekly readout.
  - **The fix:** a paragraph whose text is not held is now reported as *not checkable on this
    machine*. This holds on the card (HTML, Markdown and JSON), in the weekly report's why-lines
    and on the desk's reading page and research-action conditions.
  - **Unchanged:** where the text is held, nothing changes. Business groups never count toward a
    research action.
- **2. One theme (option A)** — `cards.THEME_CSS`, `cards.topnav`.
  - **What:** the desk, the Living Thesis Card and the weekly report now share one palette (light
    and dark, following the OS), one type and one nav bar: the desk's six screens, with the audit
    switch.
  - **What it fixes:** the desk had its own palette and nav, showed Research Now in green where the
    card showed it in red, and had no dark mode. The card's links led back to the old weekly
    report.
  - **The weekly report** keeps its own sections as a second row ("On this page").
  - **Every page** says `noindex, nofollow`.
- **3. Inside the main app (option C)** — `publish.py`, `frontend/views/intel/desk.js`,
  `frontend/app.js`.
  - **Publishing:** `python -m vinci.theme_intelligence publish` writes one run's desk into
    `frontend/theme-intelligence/`. That folder holds the standalone pages (`site/`), the desk's own
    script (`desk.js`), its component styles (`intel.css`) and `index.json`.
  - **In the app:** the app (Nostra Vinci) shows it as a **Theme intelligence** edge in its sidebar.
    This week, Themes, Articles, Review, Uploads and Sources are tabs. A thesis's reading page is a
    drill-down under Themes. The Full record and the weekly report open in a new tab.
  - **ONE RENDERER:** the app view fetches a published page, keeps its content, maps its links onto
    the app's routes and runs the desk's own script. No screen is re-implemented. The styles are
    scoped under `.intel` and pointed at the app's design tokens, so light and dark follow the
    app's toggle.
  - **Refused, with nothing written:** a registry holding test-domain articles (unless
    `--allow-test-data`, for a local preview), a folder holding anything but an earlier
    publication, and any page that would print a local path.
  - **Never published:** the card JSON and Markdown exports, the weekly report's JSON, CSV and
    Markdown, the validation log and the run manifest.
  - **The weekly Actions run does not publish.** It still commits only to the state branch, so
    publishing is a deliberate step that ends in an artifact-only commit.
- **Operator decision recorded** (CLAUDE.md §Security, `.gitignore`): `frontend/theme-intelligence/`
  is committable to the private repo and deployed on the authed internal site. It is derived
  analysis with titles, figures and short source quotes. It never carries article text, and it
  reverts to git-ignored with the dossiers if the repo or the deploy ever becomes public.
- **No publication is committed by this change:** the app shows "No theme-intelligence run is
  published yet" until one is.

**WHY.** The weekly readout should never say something it cannot know. One product should look and
navigate as one. And the operator uses the main app internally, so the desk belongs there.

**HOW VERIFIED.**
- **Runner simulation on a COPY of the real pilot** (export → re-import → render → compare every
  page with the local render): before, 4 pages said "none" where the runner could not read. Now
  those pages say *not checkable on this machine* (the local render is unchanged).
  - New test `tests/test_theme_intelligence_runner_parity.py`: a held paragraph shows the group;
    the exported registry shows "not checkable", never "none". Mutant (detection removed) killed.
- **One theme:** the desk, card and weekly report rendered from the real pilot, with screenshots
  at 1440 and 390 px. No horizontal overflow and no default-view ids. The theme-intelligence tests
  are green.
- **The app, local preview** (the real pilot published into the worktree's `frontend/`, served on
  localhost, not committed):
  - every tab, the area filter ("showing 2 of 4"), the thesis drill-down (frame title and Themes
    tab) and the Review filter work;
  - 32 new-tab links all resolve; 0 links outside the section's routes;
  - 0 console errors;
  - dark mode follows the app's toggle (panel `#ffffff` → `#12171f`);
  - no horizontal overflow at 1440 px (5 screens) or 390 px (7 screens), in headless Brave.
- **Publish tests** in `tests/test_theme_intelligence_publish.py` (8):
  - a test-domain registry refused;
  - exactly the pages the app shows, with no exports and no local paths;
  - a foreign folder never replaced; a re-publish replaces the last publication whole;
  - the app runs the desk's own script;
  - every style rule confined to the section;
  - every app token targeted exists, with no self-reference;
  - every class the desk shares with an app rule is reset;
  - a page carrying a local path refused.
- **Mutants:** 7 of 7 killed.
- **`node --check`** passes on the changed JS. Ruff, `mypy --strict` and the offline suite results
  are in the PR.

**BOUNDARY.**
- "Real pilot": a copy of `data/theme_intelligence/v2/pilot-2026-10-12/registry.db` at
  `R-20261012T133456Z-reassess`, rendered and published 2026-10-13 into scratch and into the
  worktree's untracked `frontend/theme-intelligence/`.
- "4 pages": the 2 cards and 2 reading pages of the two TrendForce theses (`TH-1516B6186B`,
  `TH-7C895A0A4E`), compared with scripts and footers removed.
- "32 new-tab links": distinct `theme-intelligence/site/…` hrefs across This Week, Review, Uploads
  and the reading pages of `TH-2FFD9B58A8` and `TH-7C895A0A4E`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0: no model call, no record written.
- **The app's phone layout stacks its sidebar above every section,** this one included. That is
  the app's existing design and was not changed here.
- **Each publication is a sizeable artifact commit:** one standalone page per thesis, and two card
  forms per thesis.
- **Publishing is manual.** Automating it would need the weekly run to commit to `main`, which is
  a policy change awaiting the operator's decision.
