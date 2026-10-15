Operator, 2026-10-15: "pickup the pending items so we can reach the error-free state". This is group 3 of the verified U-list, the published desk. U31b sits on U36's lines and is fixed here too. The full account is in `docs/records/2026-10-15-theme-intelligence-group-3-leads.md`.

**This is a render PR, so the preview rule applies: preview below, stopping for approval.**

## What changes

| Lead | What a reader saw | Now |
|---|---|---|
| U52 | "$10 billion bn", "8.5 month months", "roughly half %" on cards; "more than 60" with its unit dropped on the desk | One unit helper for both. A unit written another way is carried (billion/bn, times/x, ppt, singular/plural, a share word). A unit the value lacks is kept. |
| U36 | Cut lines and lists that did not say so, e.g. a Research Now rule naming 4 of 10 windows, and 3 of 11 "What changed" lines shown | `display.clip` / `display.first_of` at every site U36 names. Rules count what they list. "What changed" shows 3 and folds the rest. |
| U31b | "showing 3 of 11" for 25 affected articles | The total is a stored field (`affected_total`) with one reader. |
| U54 | The full weekly report (last run: 14 Oct, 6 theses, 3 articles) beside This week (12–14 Oct, 18, 13) | The report covers the desk's week, counts each article once, and names the retired. Each review count states its population. |
| U47 | An area-root link printed as "ADJACENT SUPPORT (parent / child)" and counted as related on Themes, while the page folded it | The engine files it as the same broader area. The page and Themes read links one way, including links stored the old way. |
| U13 | Retired theses unmarked in article lists; an older run's view carried today's flag | Marked "retired — replaced on re-analysis"; the as-of view keeps `retired` only from its retirement. |
| U32 | Filter count vs rows on screen; a sort hiding top rows; no print rule; search blind to the area; "Latest evidence" not applied; 42 repeated ids in the printed report; publish deleting stray files | Re-cap after filter and sort, with "N of M match"; folds open for print; search reads the area; the default sort is the page's own order; card ids scoped; publish refuses instead of deleting. |

## Preview

The pilot's full weekly report, before and after: the window, articles and thesis counts now match This week.

![weekly report before](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-group-3-desk/docs/theme_intelligence/group-3-2026-10-15/screenshots/weekly-report-before.png?raw=true)
![weekly report after](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-group-3-desk/docs/theme_intelligence/group-3-2026-10-15/screenshots/weekly-report-after.png?raw=true)

This week, after (the retired named in the tile; the findings tile states its population):

![this week after](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-group-3-desk/docs/theme_intelligence/group-3-2026-10-15/screenshots/this-week-after.png?raw=true)

The same page with every fold opened (the article list marks retired theses):

![this week opened](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-group-3-desk/docs/theme_intelligence/group-3-2026-10-15/screenshots/this-week-after-opened.png?raw=true)

A reading page, after: "What changed" shows 3 and folds 4 more:

![thesis after](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-group-3-desk/docs/theme_intelligence/group-3-2026-10-15/screenshots/thesis-after.png?raw=true)

The same page with every fold opened:

![thesis opened](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-group-3-desk/docs/theme_intelligence/group-3-2026-10-15/screenshots/thesis-after-opened.png?raw=true)

The card's key evidence, before ("roughly half %", "$26 billion bn") and after:

![card before](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-group-3-desk/docs/theme_intelligence/group-3-2026-10-15/screenshots/card-key-evidence-before.png?raw=true)
![card after](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-group-3-desk/docs/theme_intelligence/group-3-2026-10-15/screenshots/card-key-evidence-after.png?raw=true)

Themes on a SYNTHETIC 52-week stress registry (the default sort is the page's own order; capped areas re-cap):

![themes 52 weeks](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-group-3-desk/docs/theme_intelligence/group-3-2026-10-15/screenshots/themes-52-weeks-after.png?raw=true)

## Real-run verification

**The pilot** (a copy; run R-20261014T110419Z-reanalyse; $0, no model call), rendered before and after:

| Check | Before | After |
|---|---|---|
| Duplicated-unit strings over 77 published pages | 64 | **0** |
| Report window / articles / theses | 14 Oct / 3 / 6 | **12–14 Oct / 13 / 15 + 3 retired** (This week: 12–14 Oct / 13 / 18, 3 retired) |
| Themes related count ≠ the page's | 15 of 23 theses | **0 of 23** |
| Cut dated-evidence lines marked | 0 of 3 | **3 of 3** |
| Repeated ids in report_print.html | 42 | **0** |
| Article-list links to retired theses marked | 0 | **6** |

The pilot's checksum is unchanged (5fcc240d4b087d2feb1f81e6d6fabc3c).

**TH-BF20FBC464's Research Now rule** (through `Engine.reassess`'s own state build, captured at `compute_priority`, nothing written): the stored v3 rule names 4 windows with no count; the current code adds "(showing 4 of 10)". The action is unchanged.

**The desk script in a browser** (52-week stress registry: 257 theses; Memory 46 and Power & grid 31, over the 25-row cap):
- Archived alone shows 111 rows, "111 of 257 match" (was "showing 111 of 257" with 84 on screen).
- Sorted by sources, the 25 shown are the top 25.
- "power & grid" finds 12 (0 before).
- `beforeprint` opens 12 of 12 folds.

**Render time**, main 7a45244c → this branch:
- pilot: 0.67 s → 0.86 s (the article census);
- 52 weeks: 11.3 s → 8.2 s (links read once).

Checks:
- Pins: `tests/test_theme_intelligence_group3.py`, 32 tests, each fix with its negative. Two pins of the old behaviour were updated: the engine's PARENT_CHILD for an area root, and publish deleting a hand-placed file.
- Mutants: 22 of 22 killed, and the unmutated baseline passes.
- `ruff check .` and `mypy --strict vinci` are clean.

Offline suite (`pytest -m "not network"`): **5,491 passed, 513 skipped, 37 deselected** (exit 0); record and STATE lints 731 passed.

## Disposition

| Item | Status | Note |
|---|---|---|
| U52 one unit helper | SHIPPED | 29 of 205 pilot pairs read right; 64 → 0 duplicated strings |
| U36 truncations print their own | SHIPPED | every site U36 names, plus the Skip rule's list |
| U31b affected total | SHIPPED | the same lines as U36 |
| U54 one week on both pages | SHIPPED | same span, each article once, retired named, populations stated |
| U47 area-root links | SHIPPED | engine plus one reader; stored cards keep their old words |
| U13 retired marked | SHIPPED | article lists and the as-of view |
| U32 a–e | SHIPPED | JS behaviour verified in a browser; pinned structurally in the suite |
| STATE row 32: #715–#719 merged | SHIPPED | with their merge commits |
| Preview | SHIPPED | awaiting approval |

Accepted, stated in the record:
- Stored card text and stored rules are never rewritten; they change with the next version.
- With a two-level taxonomy the engine no longer creates PARENT_CHILD.
- The two review counts measure different populations; each now says which.
- Print relies on the `beforeprint` event, as the card does.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

