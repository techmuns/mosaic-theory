**Stacked on #718** (base `claude/theme-intelligence-enrichment-basis`): the tear sheet builds on its condition and basis. Merge #718 first.

Operator, 2026-10-15: "this has made the view quite long and unable to read for a professional investment team". Choosing the whole page: "always consider the whole thesis page, as our goal is to make the views how an expert would look at". The full account is in `docs/records/2026-10-15-theme-intelligence-thesis-tear-sheet.md`.

**This is a render PR, so the preview rule applies: preview below, stopping for approval.**

## What changes

- **First band.** The thesis, its key figures and what changed sit on the left. The decision sits on the right: why this action and its unmet checks, timing, the next step, and when to raise or lower priority. The verdict, its reasons and its numbers are now read together.
- **Key figures.** Three distinct figures. A value and label stated twice (the pilot's "$26 billion · DTC cash-pay market size", at peak and at its peak) shows once.
- **Companies the thesis implies.** One row per company: ticker, company, direction, how it earns, and what its 10-K says. Rows are grouped under the step they rest on, so the step and its condition are said once per group. A row opens to the rationale, the listing, the basis and the filing's own sentence.
- **Open review findings.** One line each, opening to the review's words and the record. The Review tab keeps the full items.
- **Unchanged:** risks, the earnings chain, related theses and the tabs. Risks and the chain now sit side by side.
- Nothing is deleted. Every folded line is one click away, and the card stays the complete printed record.

## Preview

The pilot thesis "Direct-to-consumer cash-pay access…", before and after:

![before](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-tear-sheet/docs/theme_intelligence/tear-sheet-2026-10-15/screenshots/pilot-thesis-before.png?raw=true)
![after](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-tear-sheet/docs/theme_intelligence/tear-sheet-2026-10-15/screenshots/pilot-thesis-after.png?raw=true)

The demo thesis "Oversold software valuations…", which carries #718's basis, as served:

![demo desktop](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-tear-sheet/docs/theme_intelligence/tear-sheet-2026-10-15/screenshots/demo-thesis-desktop.png?raw=true)

The same page with every fold opened:

![demo opened](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-tear-sheet/docs/theme_intelligence/tear-sheet-2026-10-15/screenshots/demo-thesis-opened.png?raw=true)

The same page at phone width:

![demo phone](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-tear-sheet/docs/theme_intelligence/tear-sheet-2026-10-15/screenshots/demo-thesis-phone.png?raw=true)

## Real-run verification

**The pilot registry** (a copy: 23 thesis pages), measured as a reader sees it, with audit text, closed folds and hidden tabs left out:

| | Before | After |
|---|---|---|
| Visible words per page (median / max / min) | 1,178 / 2,073 / 918 | **899 / 1,533 / 704** |
| "Who is exposed" (median) | 323 | **169** |
| Open review findings (median / max) | 188 / 572 | **66 / 218** |
| First band: thesis, figures, what changed, decision (median) | — | 238 |

The pilot's checksum is unchanged.

**The demo registry** (J.P. Morgan "Software Shock"): eight implied companies under two steps, each step said once, with the 10-K column filled.

Checks:
- Pins: `tests/test_theme_intelligence_tear_sheet.py`, 5 tests. They cover the band, distinct figures, one row per company with its step said once, findings as one line here and full on Review, and that nothing is dropped. #718's display pin follows the rows.
- Mutants: 8 of 8 killed, and the unmutated baseline passes.
- `ruff check .` and `mypy --strict vinci` are clean.

Offline suite (`pytest -m "not network"`): **5,384 passed, 513 skipped, 37 deselected** (exit 0); record and STATE lints 721 passed.

## Disposition

| Item | Status | Note |
|---|---|---|
| First band: thesis, figures, what changed, decision | SHIPPED | on every thesis page |
| Three distinct key figures | SHIPPED | the pilot's duplicate $26B shows once |
| Implied companies as rows, step said once | SHIPPED | opens to rationale, listing, basis, filing |
| Review findings as one line | SHIPPED | the Review tab keeps the full items |
| Preview (as served, opened, phone; pilot before and after) | SHIPPED | awaiting approval |
| The weekly overview and Themes pages | SKIPPED | not asked here; the same rules can follow in a later PR |

Accepted, stated in the record:
- The group header is the step's own sentence, because the code never rewrites card text.
- The thesis page's folds don't open in print; the card is the printed record.
- The pilot's stored sets read "not stated" until enriched again.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

