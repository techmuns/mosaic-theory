---
id: 2026-10-17-theme-intelligence-desk-for-experts
status: recorded
date: 2026-10-17
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — the desk reads for an investment team: decision first, what is missing named, history folded

**WHAT.** The operator, 2026-10-17, on the "Why Watch · on hold" panel: "are the details
displayed as per what the team of investment experts will need? … are there other such issues in
other sections?" Then: "fix the bugs and redesign the decision panel". After the first pass:
"make it readable for the expert investment team … not just for this screen but the entire
theme-intelligence flow and subscreens and rows/elements, instead of asking me about it".

The rule applied on every page:
- the decision comes first;
- what a thesis lacks is named, not counted;
- history (retired or archived theses) is folded under a count, never mixed with the live
  theses;
- a number is never left without its label.

## The thesis page

**The panel** (`desk.thesis_page`) is now the decision box only, in this order:
1. **The label and what it means** (`_WATCH_KEY`): "On hold — the evidence itself falls short;
   new evidence is needed, not a data fix", or the "needs data" equivalent.
2. **What's missing.** Every unmet condition, timing included.
   - Under an unmet catalyst condition, **the evidence behind it** (`evidence_gap`) replaces the
     rule's generic detail ("none verified", "a forecast without a corroborating measurement").
     It gives the forecasts, counted (they are named under Key figures beside it), and the
     latest measured figure with its age against the rule's own window.
   - That figure is dated by `timewindow.observation_date`, extracted from `timing_of`, so the
     rule and the page share ONE reading.
   - Pilot, TH-FBDC863613: "Its latest measured figure, earnings growth 31% (2Q26), dates from
     30 Jun 2026 — 104 days before the as-of, outside the last quarter (92 days)".
3. **Clears when.** What would clear each open condition, keyed by its stored code
   (`WatchReason.code` → `_CLEARS`). A SKIP is keyed by the rule it failed; Research Now has
   none.
4. **Next step.**
5. **"N of M conditions met"**, folded. The exposure check names each exposure **with its
   direction**, by the desk's own `_lean`, e.g. "Magnificent 7 (could benefit)".
6. **Timing.** The near-term detail, then "the source's own horizon", told apart.

**What would raise or lower the call** moved out of the panel into the main column, under "What
would change the call", in two columns. In the panel it had doubled the panel's height beside a
short main column. On a phone the panel comes first.

**A fault found while checking the panel.** When the inflection reading is "incomplete" (a
measured change from the last quarter IS there; only its step to profits is missing), the
forecasts line would have said "no measured change … corroborates them", which is false.
- `evidence_gap` now says nothing in that case, and the condition keeps the rule's reason ("no
  stated step from the change to profits").
- No pilot thesis reads "incomplete" today: as of the published run, F12 reads "absent" on 21
  of the 23 and "not credible" on 2. So nothing published was wrong. The pin uses a real fixture
  version with its F12 reading changed.

## This week

Changes are now grouped by **what happened**, not by area. Before, a Research Now sat fourth in
its area beside retired theses. The groups, in this order:
1. Research Now
2. Moved this week (↑/↓). A thesis that is new AND moved goes here, since the move is the news;
   three pilot theses are both.
3. New this week
4. Updated with new evidence
5. Retired or archived this week — folded

Every row names its area in its meta line. A live Watch says **what it is missing**, by name
("Missing: near-term timing, named exposure, catalyst or measured change"; the full condition
names are the tooltip) in place of "3 conditions open". The short names are `_SHORT_GATE`.

## Themes

**One table** in place of nine per-area folds.
- Under each title: its area and, for a live Watch, the same "Missing:" line.
- The "N related theses" line under each title is gone (the thesis page lists them).
- Headers no longer break mid-word ("SOURCE S" before).
- The area filter and the sorts reach every row, as before.

## Articles

What an article produced lists its **live** theses. Retired or archived ones are folded under
"+N retired or archived", each still marked as before. Before, one pilot article listed nine
theses, most of them retired.

## Not changed, deliberately

- **Review** keeps every finding unfolded. It is the triage queue, and the line questioned plus
  what the review said are what is being triaged. A pinned rule (the tear-sheet test) already
  says so; the thesis page keeps the one-line form.
- **Sources** and **Uploads**: no change, beyond the Uploads fix below.
- **Dashboard**: the full weekly report, a secondary surface.

## The bugs

- **"What changed" read "showing 6 of 17 pieces of evidence from — the rest are in 04 KEY
  EVIDENCE".** The article id is audit-only, and "04" is the card's own section number.
  - `cards.more_line` recognises the closing note by its FIELDS (no claims, an UNKNOWN label, an
    article) and names its publisher.
  - The desk says it once, under the list, pointing at its Evidence tab. It is no longer counted
    as one more change: the fold read "4 more changes" for 3.
  - Stored versions are fixed at render. `engine._more_item` now writes the shared
    `MORE_POINTER`.
- **The dated-evidence lines read identically**, because their periods were audit-only. Each line
  now says its period.
- **Uploads said "Push before Monday 03:00 UTC".** The weekly run has been started by hand since
  #729, so the step now reads "before you start the weekly run (Actions → theme-intelligence-weekly
  → Run workflow)".

**DOES THIS SELECT ON FORM?** No.
- Nothing the rules read changed. The pages re-present the stored values.
- `observation_date` is the rule's own date logic, moved, not changed: `timing_of` calls it, and
  the suite pins `timing_of`.
- The "Missing:" line is the page's own ✗ list, shortened. A test holds the two equal.

## HOW VERIFIED

**Real run.** A backup copy of the live pilot registry, published with this branch:

| Surface | Count | Detail |
|---|---|---|
| Thesis pages | 23 | All 23 carry "What would change the call"; no panel carries raise/lower |
| This week | 18 rows | Moved 3, New 10, retired or archived 5 (folded); 13 "Missing:" lines, one per live Watch |
| Themes | 1 table, 23 rows | 13 "Missing:" lines; 0 related counts |
| Articles | 6 folds | — |

- The forecasts and measured-age lines are as in the first pass: 11 pages and 1 page.
- Placeholder scan over every published page (every fold open, audit layer hidden): 30 hits on
  this branch and 30 on main's published desk. All are ordinary English ("None of the 13 texts…")
  or an existing audit message on the full report, so the redesign adds none.

**Words on screen** (default view, folds closed; main's published desk → this branch):

| Page | Before | After |
|---|---|---|
| This week | 1,486 | 1,086 |
| Articles | 899 | 693 |
| Themes | 1,055 | 1,072 (the "Missing:" lines in, the related counts out) |
| Thesis page TH-FBDC863613 | 1,356 | 1,494 (the panel now says what is missing and what clears it) |

**Preview** (`docs/theme_intelligence/desk-for-experts-2026-10-17/screenshots/`):
- before (main's published desk) and after, for This week, Themes, Articles and the thesis
  pages TH-FBDC863613 and TH-2FFD9B58A8;
- the after pages again with every `<details>` opened (This week, the thesis page) and at 500px
  (This week, Themes, the thesis page);
- Uploads.

**Pins, end to end on committed fixtures:**
- `tests/test_theme_intelligence_decision_panel.py` (J.P. Morgan fixtures):
  - the panel's order;
  - raise/lower in the main column and never in the panel;
  - "Clears when" against the stored codes;
  - the evidence line replacing the generic detail;
  - NEGATIVE: an "incomplete" inflection keeps the rule's reason;
  - the measured figure's age;
  - directions, periods and the named note;
  - Uploads.
- `tests/test_theme_intelligence_desk.py` (the twelve-week stress registry):
  - This week's groups, in order, each row checked from its OWN chips, never from the grouping
    code;
  - every row's area;
  - "Missing:" equal to the thesis page's ✗ list, and absent on Research Now and archived rows;
  - Themes as one table, with the same "Missing:" equality and no related count.
- `tests/test_theme_intelligence_product_redesign.py`: the pilot's new-and-downgraded shape
  files under "Moved this week".
- `tests/test_theme_intelligence_reanalysis.py`: a retired thesis is folded and names nothing
  missing.
- `tests/test_theme_intelligence_group3.py`:
  - an article's retired thesis is folded with a true count;
  - NEGATIVE: before its retirement it is listed live;
  - the related-thesis pins now read the thesis pages.

**Mutation.** 19 mutants on the final code, all killed:
- This week: the Research Now group, the move group, new-before-moved, the group order, the
  area, the long names, the retired fold, an archived row naming what is missing;
- Themes: no "Missing:", no area, headers breaking;
- Articles: no fold, a wrong count, live theses folded;
- the panel: the generic detail kept, the evidence lines dropped, the "incomplete" guard, raise
  and lower back in the panel, raise and lower not rendered.

Four first-round survivors were equivalent mutants, i.e. conditions that can never fire:
- a retired thesis is always archived as of its run (`ARCHIVING` holds "RETIRED");
- a Skip archives at once.

The redundant conditions were removed rather than kept unpinned. One first-round survivor was a
weak assertion (the evidence line replacing the detail); it is now pinned on the panel's spans.
The first pass's 11 mutants (the key line, "Clears when", the evidence line, the rule's date,
directions, periods, the note's name and count, the Monday wording, a wrong clearing text) were
all killed on the first-pass code, before raise and lower moved out of the panel.

**Suite.** ruff and `mypy --strict` clean; `pytest -m "not network"`: 5856 passed, 513 skipped.

## BOUNDARY

- Measured 2026-10-17 on this branch over main 6965d5b4.
- Population: the pages published from a backup copy of the live pilot registry
  (`pilot-2026-10-12`, after its 2026-10-16 catch-up; run R-20261016T163302Z-market). That is 23
  thesis pages, 13 active theses and 13 articles in the week. "Before" is main's committed
  `frontend/theme-intelligence/site`.

## WHAT IT COSTS / WHAT IS ACCEPTED

- The published desk on main changes only when it is republished after this merges (an artifact
  pass).
- "Clears when" and the short condition names are fixed text per condition. A new condition shows
  its full name in lower case, and no clearing line, until one is added.
- The 2Q26 example shows the rule's own boundary (92 days). Whether that window is right is a
  rule question, not changed here.
- **Seen, not changed** (rule-level, so reported here and not fixed in a render PR): on
  TH-2FFD9B58A8 the timing section counts "6 measured observations dated within the last
  quarter" while the catalyst condition reads "none verified". The six are dated only by the
  article's publication date and are levels, not changes, so the rule is consistent; the page
  does not yet say why they do not count.
