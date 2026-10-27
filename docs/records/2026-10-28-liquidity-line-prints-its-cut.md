---
id:
status: shipped
date: 2026-10-28
prs: []
supersedes:
superseded-by:
---

# The flat liquidity line prints its own truncation: a panel with more instruments than it shows ends "— showing 11 of N instruments"

**WHAT.**

- **The defect.** `quality.liquidity_covenant_flags` prints the first 11 of a panel's instruments
  (`ciq_sheets.LIQUIDITY_LINE_ROWS`) and said nothing about the rest. On 9 of the 27 committed pages
  the panel holds more, and the line read as the whole schedule.
  - The line renders only on a page with no structured capital table (none of the 27), so its
    reader is the JSON and the synthesis, which is handed the mechanical layer whole.
  - Found by #826 (`docs/records/2026-10-27-debt-maturities-against-the-filings.md`, "found, not
    fixed"); ruled FIX by the wave's coordinator on 2026-10-27.
- **The fix.** One helper, `ciq_sheets.liquidity_cut(shown, total)`, writes the mark. Both builders
  use it, so the twin stays one format:
  - `liquidity_covenant_flags(bundle)`, the workbook reader, now counts every instrument row to the
    panel's terminator and still prints the first 11;
  - `liquidity_line(instruments)`, the structured builder that #826's governed maturities rebuild
    the line from, through the shared `liquidity_segments`.
  - A line that prints every instrument carries no mark and is byte-identical to before.
- **Back-fill.** `refresh.liquidity_line_transform` writes the mark through `refresh_fleet`, under a
  kept synthesis, and reads no workbook. It writes only behind a reproduction: the stored line must
  equal the unmarked join of the page's own instruments (`liquidity_segments`). A line that does
  not is refused and named.

**HOW VERIFIED.**

- **The pages that cut (counted before writing):** 9 of 27 — AMZN 16, GOOGL 19, LLY 56, NFLX 22,
  NKE 12, TGT 15, UBER 15, V 21, WLK 16 instruments.
- **Twin parity on the real workbooks.** The workbook reader and the structured builder give the
  same line on 27 of 27 names in the assembler's read-only copy, the 9 cut lines included (WLK: "…
  — showing 11 of 16 instruments").
- **A dry run on a scratch copy of the pages:** 9 moved, 18 unchanged, 0 refused. On each moved
  page exactly two things changed: the line's value and one appended layer record. `dossier.md`
  gained only its refresh line.
- **The real run, through `refresh_fleet`:** the same 9 moved, 18 unchanged, 0 refused.
- **Pins** (`tests/test_liquidity_line.py`, 5):
  - the workbook reader on 13 rows ("showing 11 of 13") against 11 rows (no mark);
  - twin parity on the licensed exports (skips where none are present, as its neighbours do; run
    green in a scratch tree linked to the assembler's copy);
  - end to end over the committed pages: every line is its instruments' line, a cut one ends with
    its own count, an uncut one has no mark;
  - the back-fill: it marks LLY's reproducing line and nothing else, is idempotent, and refuses a
    line that does not reproduce.
- **Mutation:** 7 mutants, each in a scratch copy whose baseline passes with the real workbooks
  linked; **7 of 7 killed.** They cover the mark dropped, the mark on an uncut line, the count
  stopping at the cut, either builder losing the mark, the line printing a twelfth row, and the
  back-fill without its proof.
- **Suite:** the full offline suite at this PR's head (counts in the PR).

**BOUNDARY.**

- **Pages:** the 27 committed pages at 3ab4747f (main); the unit is one page's line, cut when its
  panel lists more than 11 instruments.
- **Workbooks:** the assembler's read-only copy
  (`mosaic-theory-ta/data/manual/ciq`), read 2026-10-28, one bundle per page name.
- **Mutation counts:** over `tests/test_liquidity_line.py`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The line still prints 11 instruments.** The mark says how many it left out; the full schedule is
  `capital_structure.instruments`. Raising the cap would make the synthesis input longer on the
  large filers and is a separate choice.
