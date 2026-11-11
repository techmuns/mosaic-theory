---
status: shipped
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, the CIQ reader's F27 edges (RBC-D3 and V1-O3, order 5; RBC-D5, order 6): a Customers list cut short is said, a row with its type blank is a row, and an empty view is named for what it shows. No page moves

**WHAT.**
- **RBC-D3** (`customer_roster`, `_ends_with_closing_line`).
  - **The defect.** There was no end-of-table check, so a Customers file cut to 40% of its bytes
    read its surviving rows as the whole list, PRESENT, with no note.
  - **The fix.** All 72 RTF relationship exports on disk end with CIQ's closing line,
    '*denotes proprietary relationship'. An RTF view without it now says the list may be cut
    short, naming the rows read, and gives no count: a cut list's length is not the company's
    count.
  - The spreadsheet route is not checked. No spreadsheet Customers export is on disk to show
    whether that form carries the line, so a rule there would be a guess.
- **V1-O3** (`_relationship_table`).
  - **The defect.** A row naming a party with its relationship type blank was dropped with no word.
  - **The fix.** It is kept as "type not stated" when it states any other column (the industry,
    the source or the supplier). A line naming nothing else is prose, not a row: the closing line,
    a sentence.
- **RBC-D5** (`_unread_view`, `ciq.read_text`'s thin-RTF guard).
  - **The defect.** A header with no rows, a "No Data Available" body and an "Entitlement Needed"
    body all read "could not parse the Business-Relationships table", blaming this reader for
    CIQ's own empty answer. A real RTF over 4 KB with fewer than 50 words was called "an
    OLE-disguised Word doc", though `classify` had already read its bytes as RTF.
  - **The fix.** Each empty shape is named. "Could not parse" is kept for a view showing none of
    them. The thin-RTF error now says what was seen: too few words from a file whose bytes are
    RTF, with no sentence saying the view is empty, and the two causes that fit.
  - "Entitlement Needed" is the contract's word. No export on disk carries it or "No Data
    Available".
- **Review round 0** (`/code-review high --fix`, 10 findings, all fixed):
  - The thin-RTF guard raised before `_unread_view` could run on any real-sized export (the
    smallest on disk is 70,162 B). `read_text` gains `thin_ok`, and `customer_roster` names the
    view's shape when it shows one, citing the file; otherwise the guard's word stands.
  - A header counts as header-only only when nothing but section heads, a repeated header or the
    closing line follows it. A header-only RTF view without the closing line may be cut short.
  - A cut file's prior rows are said to come from a list that may be cut short.
  - The cut check runs on `CiqFormat.RTF_TEXT` only, and one header test serves both readers.
  - `ciq_reread` refuses a PRESENT roster with no count, rather than raising and stopping the
    sweep.
  - The synthetic Customers RTF ends with CIQ's closing line, as every real export does
    (`generate.CLOSING_ROW`), and the committed ZZFX file is regenerated. The OLE test matches the
    new message.
- **Review round 0b** (after the rebuild onto main, 10 findings, 1 fixed): a Customers file cut
  before its table header read only "could not parse"; it now says it may be cut short and cites
  the file (`::test_rbc_d3_a_file_cut_before_its_table_says_it_may_be_cut`).
- **Found, not fixed** (round 0b): a real view of one or two rows in an RTF over 4 KB, under the
  thin-RTF guard's 50-word floor, is still refused by the guard, as it is on `origin/main`. Reading
  a thin file's table would relax a fail-loud check, which is the operator's call. The thinnest
  export on disk has 36 words, so the shape is plausible. A cut roster also renders "count not
  recorded on this page" (`render._fmt_customers`, `dossier.js` `fmtCustomers`), which reads as a
  page that predates the field; that is a render-layer change, outside this diff.
- **Built on #957** (merged as `507d4f32`). RBC-D6 there made `_relationship_table` the one
  reader of both routes, and this edits it. It was built and verified on #957's head `e7391bf1`,
  then rebuilt on `507d4f32`. Since that head, main changed none of the files this edits except
  the version table, where this row follows main's last.

**WHY.** Document 15:
- order 5: "a truncated Customers file" and "a blank-type customer row dropped";
- order 6: "an empty view is called a parse failure or an OLE-disguised Word doc".

**HOW VERIFIED.**
- **The census.** The 72 Customers and Suppliers exports in the 36 folders on disk (all RTF) all
  end with the closing line, and none has a table row after it. None carries a row naming a party
  with a blank type.
- **Before and after, on GOOGL's real Customers export** (read only; the cut and edited copies
  are written under the session scratchpad):

  | Case | At #957's head `e7391bf1` | Here |
  |---|---|---|
  | As exported | PRESENT, 653 rows | PRESENT, 653 rows, no note |
  | Cut to its first 40% of bytes | PRESENT, 251 rows, no note | PRESENT, 251 rows read, no count, "… does not end with CIQ's closing line … the list may be cut short: 251 row(s) read — re-export it" |
  | Its first row's relationship type removed | PRESENT, 652 rows (the row dropped) | PRESENT, 653 rows, the row as "… — type not stated" |
- **Fail first.** `tests/test_ciq_relationship_view_edges.py` has 18 tests. 15 fail on #957's
  `vinci/` (`e7391bf1`), run in a tree of its own. The 3 that pass there are the negative pins: a
  line naming nothing else is not a row; a file with no table still reads "could not parse"; a
  thin RTF showing no empty shape keeps the guard's own word.
- **No page moves.** `customer_roster` gives the same status, count and note at #957's head and
  here on all 36 folders on disk (0 of 36 move).

**BOUNDARY.** The exports under the primary checkout's `data/manual/ciq/` on 2026-11-11: 36
folders, 72 relationship exports. The mutated copies are written under pytest's `tmp_path` or the
session scratchpad, never in the repository.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A cut RTF view keeps its rows on the page with the note beside them. Withholding rows that were
  read would lose real evidence.
- The spreadsheet route has no end-of-table check until a spreadsheet export shows what its last
  line is.
- **Extraction version** `2026-11-10.relationship-view-edges`; the drift pins are re-pinned.
## Amendments

- **2026-11-11 — `status: open` → `shipped`** (the record-status sweep, `docs/records/2026-11-11-record-status-sweep.md`). This record's change merged to `main` as `c2a4d743` (#975) on 2026-11-11. `prs:` was left empty at merge; the front matter stays as merged, so this entry names the PR.
