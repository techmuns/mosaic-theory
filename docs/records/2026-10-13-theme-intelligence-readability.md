---
id: 2026-10-13-theme-intelligence-readability
status: recorded
date: 2026-10-13
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — the desk's screens re-laid for reading: one hierarchy per screen, less said twice, engine detail in the audit view

**WHAT.** A readability pass over the six desk screens and the thesis reading page, at the
operator's request ("not humanly readable and compressed at a lot of places with too many
verbose/non-useful information"). Render-time only (`vinci/theme_intelligence/desk.py`, the in-app
rules in `publish.py`): no record, no stored card and no research action changes.
- **This week.** A heading and one sentence, then five counts (articles read, theses new or changed,
  Research Now, findings to review, upload items). The changes are grouped by area, each one card:
  action, events, findings, title, mechanism, source and date, and the WATCH conditions still open
  as one badge. The articles are a list (state, title, publisher and date, what each produced).
  **Needs your attention** sits beside them. Every active thesis by area is one fold below.
- **Themes.** One table per area; an area opens only if it changed this week. The columns line up
  from one area to the next (fixed widths); the area name is no longer repeated on every row.
- **Articles.** Week navigation is older / newer, and every week in one fold. The article's title,
  publisher and route share one column; the follow-up's open items fold.
- **Review.** Findings grouped under their thesis (title, action, area, count), each finding three
  short lines: the quoted line, the review's words, one meta row ("Affects action", raised, age,
  the link). A line's "(scope: …)" note moves to the audit view, as on the reading page.
- **Uploads.** Each group (full report needed, blocked, manual-first …) is a list, not a wide table:
  the item and why, publisher and dates, the import command. Ten shown per group, the rest one click
  away. The weekly steps are four short lines beside it; the rules fold.
- **Sources.** One row per publisher: status now (with its reason), the health history, freshness
  and intake.
- **Reading page.** The thesis first, then three pairs side by side: why this action / what to
  investigate next, how it reaches fundamentals / what could prove it wrong, what changed / who is
  exposed. Long lists fold (conditions met, more risks, signals to watch, sibling theses).
- **Said once.** A figure whose metric already names its scope reads once ("observability software
  prices change", not "observability software — observability software prices change"). This is
  decided from the claim's structured scope and metric (`desk.figure_label`). The Full record keeps
  the sealed label. Labels are sealed in each stored version, so building them differently would
  have changed stored content; the fix is render-time for that reason.
- **Engine detail.** A source's registry id (`citi_must_c`) is in the audit view on Sources and
  Uploads (Uploads still carries it in the command to copy). No empty "—" or blank publisher is
  printed for an item without dates or a publisher.
- **Phone width.** The single column on a phone can shrink below a one-line command, so the Uploads
  panel no longer pushes the page 34 px wide at 390 px.

**WHY.** The desk is read by a person deciding where to spend research time. A screen should answer
its one question first, at a glance, and hold everything else one fold away. It should never say
the same thing twice or show what only the engine needs.

**HOW VERIFIED.**
- **In the app** (local preview of `frontend/`, headless Brave, the same-origin frame), on the
  SYNTHETIC 12-week registry and on a COPY of the real pilot:
  - page height at 1440 px, synthetic: This week 4,472 → 3,214 px; Themes 8,347 → 4,054; Review
    4,761 → 4,218; Uploads 14,501 → 4,132;
  - no horizontal overflow on any of the 7 routes (six screens + one reading page), at 1440 and
    390 px, on both registries; dark mode checked on 3 routes (real pilot);
  - the 390 px Uploads overflow (page 424 px wide) found here and fixed (390).
- **Standalone pages** (scratch checker): 0 broken links and 0 default-view hygiene problems (engine
  id, engine code, "page None", double escape) over 368 pages; every reading page reaches all nine
  card sections.
- **New pins** (`tests/test_theme_intelligence_desk.py`):
  - a metric naming its scope is not repeated, a scope it does not name is kept, and the Full record
    keeps the sealed label (positive + negative);
  - no source id in the default view of Sources or Uploads, the audit view keeps them, and the
    commands still carry them;
  - a finding's scope note is the audit view's, and a line without one is unchanged (negative).
  - Mutants: 4 of 4 killed (label rule removed; source id shown on Sources; on Uploads; scope split
    removed).
- **Two existing pins moved to the new structure:** Articles (`td.art a`) and This week
  (`ul.alist > li`, each naming its article).
- Ruff, `mypy --strict` and `node --check` are clean; the offline suite result is in the PR.

**BOUNDARY.**
- "Synthetic 12-week registry": `tests/theme_intelligence_stress.py` at 12 weeks (229 articles, 111
  theses, deterministic builder), rendered at its last scan.
- "Real pilot": a copy of `data/theme_intelligence/v2/pilot-2026-10-12/registry.db` at
  `R-20261012T133456Z-reassess` (4 theses, 5 articles).
- Heights: `documentElement.scrollHeight` of the app framed at exactly 1440 px. Before = commit
  `ed5dba69`'s renderer; after = this change. Both measured 2026-10-13 on the synthetic registry.
- "368 pages": every HTML page of the two standalone renders (real 18, synthetic 350), 2026-10-13.
- "4 of 4 mutants": run against the three new pins, 2026-10-13.
- In the real pilot, 2 of the 103 claims that carry a value have a metric that already names its
  scope (`claims` table of the copy, `value_text` not null).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0: no model call; nothing written to the registry.
- **Themes on a phone stays long** for a large registry (13,171 px at 390 px for the synthetic 96
  active theses): every area that changed this week is open, and each row stacks as a card.
  Search, filters and closed areas are the way through.
- **Uploads' list of articles to supply prints the article's web address before its title.** That
  line is built upstream as one string; splitting it at the desk would mean parsing a rendered
  string, which the repo forbids.
