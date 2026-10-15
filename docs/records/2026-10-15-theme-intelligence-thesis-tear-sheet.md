---
id: 2026-10-15-theme-intelligence-thesis-tear-sheet
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — the thesis page as a tear sheet

**WHAT.** Operator, 2026-10-15, on the thesis page after the enrichment condition and basis (#718):
"this has made the view quite long and unable to read for a professional investment team". Then,
choosing the whole page: "always consider the whole thesis page, as our goal is to make the views
how an expert would look at". The thesis page is rebuilt as a tear sheet. Its order is what an
expert reads first, and every line it no longer shows at once is one click away.

| Part | Before | Now |
|---|---|---|
| **First band** | "The thesis" alone; "Why <action>" and "What to investigate next" side by side below it; the strongest figures far down, after exposure and risks | **One band**: the thesis, its key figures and what changed on the left; the decision on the right (why this action, its unmet checks, timing, the next step, when to raise or lower) |
| **Key figures** | up to 4, one value and label could show twice ("$26 billion · DTC cash-pay market size", at peak and at its peak) | **three distinct figures** (value and label once) |
| **Companies the thesis implies** | one paragraph per company, each repeating its step's full sentence, the basis and the filing note | **one row per company** (ticker, company, direction, how it earns, what its 10-K says), grouped under the step it rests on, so the step and its condition are said **once per group**; a row opens to the rationale, the listing, the basis and the filing's own sentence |
| **Open review findings** | each finding in full (the quoted line, the review's words, the meta row) | **one line each** (affects action, kind, the line clamped), opening to the review's words and the record; the Review tab keeps the full items |
| Risks, the chain, related theses, the tabs | as before | as before; risks and the earnings chain sit side by side under exposure |

**WHY.** The first screen showed the thesis and two "why" blocks. The figures and the companies came
after hundreds of words of exposure prose, and a reader could not see the decision, its reasons and
its numbers together.

**HOW VERIFIED.**
- **Real data: the pilot registry** (a copy; 23 thesis pages, run R-20261014T110419Z-reanalyse),
  measured as a reader sees it (audit-view text, closed folds and hidden tabs left out):
  - **visible words per page: median 1,178 → 899** (−24%), max 2,073 → 1,533, min 918 → 704;
  - "Who is exposed" median 323 → 169;
  - open review findings 188 → 66 (max 572 → 218);
  - the first band (thesis, figures, what changed, decision) has a median of 238 visible words.
  - The pilot's checksum is unchanged.
- **Real data: the demo registry** (J.P. Morgan "Software Shock", with #718's basis): eight implied
  companies under two steps, each step said once; the 10-K column filled; desktop, opened and phone
  widths.
- **Preview** (the preview rule: as served, every fold opened, phone width; and the pilot page
  before and after): images in `docs/theme_intelligence/tear-sheet-2026-10-15/screenshots/`.
- **Pins:** `tests/test_theme_intelligence_tear_sheet.py`, 5 tests on the 6-week stress registry and
  the hypothetical enrichment thesis:
  - the band's content and order;
  - three distinct figures (positive and negative);
  - one row per company with its step said once;
  - findings as one line on the thesis page and full on the Review tab;
  - nothing folded is dropped.
  - #718's display pin follows the rows.
- **Mutants: 8 of 8 killed.** An unmutated baseline passes.
- Ruff and `mypy --strict vinci` clean; the offline suite result is in the PR.

**BOUNDARY.**
- Code: #718's head (467f5088) against this branch, 2026-10-15.
- Pilot: a copy (SQLite backup API) of `v2/pilot-2026-10-12/registry.db` under the
  `theme-intelligence` worktree's `data/theme_intelligence/`, rendered for its latest run.
- "Visible words": a page's main element with `.aud` text, the bodies of closed `<details>` (their
  summary kept) and `[hidden]` panels removed, split on whitespace.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no model or SEC requests.
- **The step's own sentence is the group's header**, cut to the line on a phone. The code never
  rewrites card text into a shorter condition.
- **The thesis page's folds do not open when printed.** The complete printed record is the card
  (`cards/*.print.html`), as before.
- **The pilot's stored enrichment sets have no basis** (proposed before #718). Their rows read "not
  stated" until enriched again, at a paid call per thesis.
- **Stacked on #718**, which this redesign builds on.
