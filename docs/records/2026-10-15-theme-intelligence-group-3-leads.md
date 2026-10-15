---
id: 2026-10-15-theme-intelligence-group-3-leads
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — group 3 of the verified review leads, the published desk: U36, U52, U54, U47, U13, U32

**WHAT.** Operator, 2026-10-15: "pickup the pending items so we can reach the error-free state".
Group 3 of the suggested order in `docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`
is the published desk. U31b sits on U36's lines, so it is fixed here too.

| Lead | Defect (pilot or stress registry) | Fix |
|---|---|---|
| U52 | Two unit helpers. The card printed "$10 billion bn", "8.5 month months", "roughly half %". The desk's helper dropped every unit beside a word ("more than 60" for 60 countries, "five" for five years). On the pilot they disagreed on 29 of 205 distinct value/unit pairs. | ONE helper (`cards.unit_shown`), which the desk now calls. It knows a unit's written forms (billion/bn, times/x, ppt/percentage points, singular/plural, a share word for %). A unit the value does not write is kept, even beside words. |
| U36 | Cuts that did not say so. TH-BF20FBC464's Research Now rule named 4 of its 10 near-term windows; the desk's 300-character cut of its F5 note removed priority's own "showing 4 of 10"; a reading page showed 3 of a thesis's 11 "What changed" lines; 3 of 62 dated-evidence lines were cut mid-sentence; and the U36 list of CLI, pipeline, health, state, qa, ingest and securities notes. | A new `display.py` holds `clip` (moved from `cards.py`, now naming where the rest is) and `first_of` ("showing n of N"). Every site U36 names uses one of them. The Research Now rule and the Skip rule count what they list. "What changed" shows 3 and folds the rest ("8 more changes"). |
| U31b | Health's stored affected list is cut at 10, with a closing "… and N more" line. A reader that counted the stored list said "showing 3 of 11" of 25. | `ManualAction.affected_total` keeps the total. `health.affected_shown` is the one reader. A check stored before the field says "of more than 10". |
| U54 | Two "this week" pages disagreed. The full weekly report covered the LAST run ("14 Oct", 6 theses, 3 articles); This week covered the week ("12–14 Oct", 18, 13). | The report covers the desk's week (`desk_weeks`). Its window spans those runs. It counts each article ONCE, by the Articles screen's census (`desk.analysed_articles`); the runs' counters summed an article re-analysed in the week twice. Both pages name the retired theses, and each review count states its population. |
| U47 | The engine filed a root-to-child link as PARENT_CHILD adjacent support (card TH-A097D4722F: "ADJACENT SUPPORT (parent / child)"). Themes counted it as related while the page folded it into "same broader area" (TH-DEE87FCF51: "2 related theses"). | The engine files an area-root link as the same broader area (SIBLING, no evidence role). The desk reads the registry's links once (`Desk.related_of`) for the page and the Themes count, including links stored the old way. |
| U13 | Retired theses listed unmarked ("· new evidence") in the article lists. An older run's view carried today's `retired` flag. | An article list marks a retired or archived thesis. `theses_as_of_run` keeps `retired` only once the RETIRED event came before the run ended. |
| U32 | (a) The Themes filter said "showing 111 of 257" with 84 on screen, and a sort left the top rows hidden past the 25-row cap. (b) Desk pages had no print rule opening their folds. (c) Search never read the area name; "Latest evidence" was named but not applied; Themes' related count differed from the page. (d) `report_print.html` repeated 42 ids. (e) `publish` deleted stray files its docstring said it refused. | (a) A capped table carries its cap. A filter or sort re-applies it to what remains (`recap`), and the count says how many match. (b) Every fold opens before printing, as on the card. (c) Search reads the area. The default sort is "Research action, then latest evidence" (the page's own order). One reading of links, as under U47. (d) Each embedded card's ids are prefixed with its thesis id (`report.scoped_ids`). (e) A file the last publication did not write is never deleted: the publish is refused and nothing is written. |

**WHY.** These are the defects a reader of the published desk sees: a unit said twice or
dropped, a list cut without a word, two pages answering "this week" two ways, a related count that
disagrees with its page, a retired thesis that looks live.

**HOW VERIFIED.**
- **The pilot, rendered before and after** (a copy; run R-20261014T110419Z-reanalyse; $0, no
  model call):
  - **U52:** 64 duplicated-unit strings over 77 published pages before, 0 after. Of 205 distinct
    value/unit pairs, all 29 the helpers disagreed on now read right. 14 change from the card's
    old output, each a dropped duplicate.
  - **U54:**

    | | Report before | Report after | This week |
    |---|---|---|---|
    | Window | 14 Oct | 12–14 Oct | 12–14 Oct |
    | Articles | 3 | 13 (3 in part) | 13 (10 in full, 3 preview) |
    | Theses | 6 | 15 + 3 retired | 18, 3 of them retired |
    | Watch / Skip | — | 12 / 7 | of 19 active |

  - **U36:**
    - "What changed" folds its rest on 20 of 23 reading pages;
    - the 3 cut dated-evidence lines are marked;
    - TH-BF20FBC464's F5 note says it is cut.
  - **U13:** 6 article-list links to retired theses are marked.
  - **U32c/U47:** Themes' related count differed from the page on 15 of 23 theses before, 0
    after. TH-DEE87FCF51 reads 4, as its page does.
  - **U32d:** report_print.html had 479 ids, 42 repeated. After: 1,057 ids, 0 repeated.
- **TH-BF20FBC464's rule through `Engine.reassess`'s own state build** (scratch copy, captured
  at `compute_priority`, nothing written): stored v3 "near-term window(s) C-…; C-…; C-…; C-…"
  with no count; the current code "… (showing 4 of 10)". The action is unchanged (RESEARCH NOW).
- **The desk script in a browser** (a SYNTHETIC 52-week stress registry: 257 theses, its Memory
  area 46 and Power & grid 31, over the 25-row cap):
  - Archived alone: 111 rows shown, "111 of 257 match".
  - Every status: "257 of 257 match", 230 on screen. Each capped area says "Showing 25 of 46".
  - Sorted by sources: the 25 shown are the top 25.
  - The default sort restores the page's order.
  - "power & grid" finds 12 (0 before).
  - `beforeprint` opened 12 of 12 folds.
- **Render time:**

  | Registry | main (7a45244c) | This branch |
  |---|---|---|
  | Pilot, 5 runs | 0.67 s median | 0.86 s (the article census) |
  | 52 weeks, 3 runs | 11.3 s | 8.2 s |

  The 52-week render is faster because the links are read once rather than one table scan per
  page.
- **Pins:** `tests/test_theme_intelligence_group3.py`, 32 tests, each fix with its negative.
  - End to end through the real engine: units on the page and the card; the fold; one week with
    each article once; the two-run, two-day week; the retired marked only from its retirement;
    the area-root and legacy links; the printed report's ids; publish.
  - `compute_priority` on the real `ThesisState`.
  - The JS is pinned for its parts; its behaviour is the browser run above.
  - Two existing pins asserted the old behaviour and now assert the new one:
    - the engine's PARENT_CHILD for an area root;
    - publish deleting a hand-placed file.
- **Mutants: 22 of 22 killed.** An unmutated baseline passes. One survived the first pass (the
  report covering only the last run). The two-run, two-day pin was added for it.
- Ruff and `mypy --strict vinci` clean. The offline suite result is in the PR.

**BOUNDARY.**
- Code: main 7a45244c against this branch, 2026-10-15.
- Pilot: a copy (SQLite backup API) of `v2/pilot-2026-10-12/registry.db` under the
  `theme-intelligence` worktree's `data/theme_intelligence/`. Its checksum is unchanged
  (5fcc240d4b087d2feb1f81e6d6fabc3c).
- Value/unit pairs: distinct (value_text, unit) over the pilot's claims and every thesis
  version's key evidence.
- Duplicated-unit strings: a regex for the U52 shapes over every `.html` of the render, tags
  stripped.
- Stress registry: `tests/theme_intelligence_stress.py`, 52 weeks, seed 7, built at this branch.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no model or SEC requests.
- **Stored text is never rewritten.** The pilot's cards keep "ADJACENT SUPPORT (parent / child)",
  and TH-BF20FBC464 v3 keeps its uncounted rule, until a new version is written. The desk reads
  both kinds of link the same.
- **With this taxonomy (two levels) the engine no longer creates PARENT_CHILD.** Every parent is
  an area root. The branch stays for a deeper taxonomy. An area-root link prints "SIBLING with",
  the card's existing words for a sibling with no evidence role.
- **The two review counts measure different populations, by design:** the report counts this
  week's cards, This week counts every active thesis. Each label now says which.
- **The print rule is the card's:** a `beforeprint` handler. A browser that prints without that
  event keeps closed folds closed. This supersedes the tear sheet record's "the thesis page's folds
  do not open when printed".
- **Not every `[:N]` changed.** Hash and id slices are not truncations of reader text. U36's
  named sites are fixed; the rest of the U-list stays as planned.
