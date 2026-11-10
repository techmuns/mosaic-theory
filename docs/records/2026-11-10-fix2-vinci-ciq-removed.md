---
status: open
date: 2026-11-10
prs: []
supersedes:
superseded-by:
---

# Fix request 2: `vinci/ciq/` is removed, not left dead (A-D13, A-D16, RBC-D7 = BC-D1 and BC-D2; with them BC-D3, BC-D5, BC-D6 and BC-D7's graph half). Its last caller left in #905; the graph extractor keeps the one taxonomy it took. No page, request or output moves

**WHAT.** Document 15 asks of A-D13, A-D16 and RBC-D7: "no production caller: fix or remove".
This removes the package:
- **Deleted:** `vinci/ciq/__init__.py`, `manual.py` (89 lines) and `relationships.py` (168),
  and `tests/test_ciq.py`, whose four parser tests read them.
- **Moved, not deleted:** `tests/test_ciq.py`'s other two tests pin the live extractor
  `vinci.dossier.ciq_sheets._capital_summary` (a descending export is refused; the period label
  names the columns, #328) and never read `vinci.ciq`. They move verbatim to
  `tests/test_capital_summary_labels.py`.
- **Moved:** `SUPPLY_CHAIN_TYPES`, the five relationship types, now lives in
  `vinci/graph/extract.py`. That is the one thing `vinci/graph/extract.py` imported from the
  package; the value is unchanged.

The defects TeamNostra reproduced in the package go with it:
- **A-D13:** `extract_text` read an OLE `.xls` as empty text.
- **A-D16:** a diagnostic PNG aborted the store's load.
- **BC-D1:** a 4-column view was read by position, so every row was dropped as "not supply
  chain".
- **BC-D2:** the focal group was read as its own counterparty.
- **BC-D3, BC-D5 and BC-D6:** a non-relationship document, a truncated view, and a blank-type
  row.
- **BC-D7's graph half:** a former customer counted as current. Its dossier half was fixed in
  #881; its spreadsheet half is RBC-D6 (#957).

The live F27 reader, `vinci.dossier.ciq_sheets.customer_roster`, is untouched. Two of its own
residuals remain open under their own IDs: RBC-D3, a truncated file read as complete, and V1-O3,
a blank-type row dropped.

**WHY.** Removal over repair:
- After #905 nothing outside the tests called the package.
- A repaired parser no code reads would still need fixing, testing and auditing, and would
  still be dead.
- The coordinator's brief asked for removal, with the evidence below, as its own small PR.

**HOW VERIFIED.**
- **No caller** (2026-11-10, at `9da0d096`):
  - `rg -n "vinci\.ciq\b"` over every `.py` file finds `vinci/graph/extract.py:26` (the
    taxonomy) and `tests/test_ciq.py` only.
  - `rg -nw` for each public name (`load_ciq_edges`, `parse_relationships`,
    `LocalFolderManualStore`, `extract_text`, `CiqFormatError`, `CiqEdge`, `ParsedRelationships`,
    `ParsedRow`) finds nothing outside the package and that test.
  - `git log -S load_ciq_edges` gives three commits: `4016f236` added the parser, `b1d0fbe4`
    added Test 0's use of it, and `3ad14793` (#905) removed that use, `vinci graph-test0`.
- **The pin.** `tests/test_vinci_ciq_removed.py` fails on `origin/main` (the package is found)
  and passes here. It also pins the taxonomy byte for byte, and the extractor's own check that
  its direction map covers the vocabulary.
- **No output moves.**
  - `vinci/ciq/` is outside the extraction-version drift test's watched set ("vinci/ciq builds
    no page field"), and the moved constant has the same value.
  - So no extraction version is declared, no page moves, and every synthesis request is
    unchanged.
  - The drift test's docstring is corrected to say the package is gone.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- `docs/ciq_extraction_notes.md` still describes the removed parser's column assumption. That
  file is order 9's (G-D8 to G-D15, another stream), so it is not edited here.
- The history keeps the code: `git show 9da0d096:vinci/ciq/relationships.py`.
