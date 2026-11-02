---
id: 2026-11-01-small-items
status: open
date: 2026-11-01
prs: []
supersedes:
superseded-by:
---

# Four small CIQ reader fixes: a 1904 workbook's true dates, an unread Key Developments export named, a positive capex never netted, and a prior customer never current (audit A-D4, A-D9, D-D9; the relationships sections)

**WHAT.**
- **A-D4, the 1904 date system (`ciq.read_sheets`).** xlrd hands back a 1904 workbook's date cell
  as that system's serial, and every reader decodes serials on the 1900 system, so each date read
  four years and a day early. A 1904 workbook's date cells are now moved onto the 1900 serials
  (+1,462 days) as the sheet is read. A 1900 workbook is returned exactly as before. The strict
  xfail is removed.
- **A-D9, an unread Key Developments export (`ciq_sheets.key_developments`).** The reader reads the
  RTF export's text. A spreadsheet export, an undecodable one, or one with no 'Date | Type |
  Headline' header returned [] with no trace. The collector's only flag fires when every source
  misses, so a page with a release row lost its events silently.
  - It now returns the rows and a QA flag naming the file and why. `mechanical._primary_source`
    adds the flag to `OperatingDriversExtract.qa_flags`.
  - `key_development_drivers` keeps its signature (rows only).
- **D-D9, a positive capex (`ciq_balance.extract`).** The FCF fill subtracts capex's magnitude
  (`abs` in the bridge, `o - abs(c)` in the anchor), which assumes CIQ's outflow sign. A positive
  'Capital Expenditure' at the annual sheet's latest column is now unavailable, with its reason.
  The anchor's `ltm_fcf` UNKNOWN source names it ("CIQ's capex: …"), and nothing is netted.
- **The relationships sections (`ciq_sheets._relationships`, `customers`).** A Customers view not
  filtered to recent disclosures heads two sections. Its rows under 'Prior and Not Recently
  Disclosed Customers' were read as current. The recent section's own "There are no recently
  disclosed customers listed" went unread, because `is_empty_view` was consulted only when no row
  parsed anywhere.
  - Each row is now filed under its section. The value is the recent rows.
  - Prior rows are said in the field's note, never counted.
  - A recent section stating none reads UNKNOWN, citing CIQ's statement, with the prior rows in
    the note.
  - A view heading no section reads exactly as before.
- **Fixtures.** The synthetic generator gains a Key Developments `.xls`, in the one real
  spreadsheet export's layout (header row 14, date-typed first column), and a Customers view in the
  observed prior-section shape. Every name in both is invented. `--check` reports 9 of 9 outputs
  matching the generator.

**WHY.**
- **Live:** TECX's committed page prints "Customers: 2 mapped client relationship(s)". They are two
  2023 AVROBIO counterparties under the prior section, while the recent section states none.
- **Latent:** a 1904 workbook (0 on file); a Key Developments spreadsheet (one on file, archived);
  a positive capex at an annual latest column (0 on file).

**HOW VERIFIED.**
- **Failing first, on main 01c95fde** (this branch's tests and fixtures on main's code): 6 of the 6
  new tests fail.
  - The 1904 workbook decodes 2022-10-22 for 2026-10-23.
  - The positive capex is netted.
  - The prior-section view reads PRESENT.
  - `key_developments` and `_relationships` do not exist.
  - Main's operating-drivers flags for the Key Developments spreadsheet hold only "no rows
    extracted (releases/10-Q/KD all missed)"; here the flag names the file.
  - Negative pins pass on both sides: a negative capex fills the FCF; an export not on file, or
    one read whose rows the filter drops, raises no flag; a view heading no section reads as
    before.
- **Corpus, Key Developments** (52 non-held exports on file 2026-11-01, found recursively: 34
  current, 18 archived): 2,303 rows kept; the flag fires on 1, `ciq-archive/replaced-2026-09-22/
  GOOGL/… Key Developments.xls`, and on 0 of the 51 RTFs.
- **Corpus, Customers** (52 non-held Customers exports, current and archived, found recursively;
  raw-byte scan): every one heads 'Recently Disclosed Customers'. Two also head 'Prior and Not Recently Disclosed
  Customers', and both state the recent section empty: TECX's and HLF's. HLF has no page. On the
  live exports, TECX and HLF read UNKNOWN with their 2 prior rows in the note, and ROST (control)
  reads its one row as before.
- **Replay** under main 01c95fde's code and this branch's, over the 26 committed pages' names on
  their current `-ta` exports (held pack excluded, 2026-11-01):
  - `customers` differs on 1 of 26, TECX (PRESENT → UNKNOWN, as above);
  - `ciq_balance.extract`'s facts and unavailable reasons differ on 0 (capex a fact on 25; LLY's
    unavailable at a '-' on both sides). These are the CIQ inputs of the anchor's FCF fill, so the
    fill moves on none;
  - the Key Developments rows differ on 0 of 1,103;
  - `read_sheets` differs on 0 of the 117 spreadsheets in those folders (a hash of each).

**BOUNDARY.**
- **1904 census** (2026-11-01, the non-held `-ta` workbooks on file, current and archived): 238
  workbooks, all 1900-system. They carry 116,442 date-typed cells, and 0 dates sit in a number
  cell.
- **Capex census** (same date and population): 104 Cash Flow sheets carry 2,288 valued 'Capital
  Expenditure' cells. 3 are positive, all on quarterly sheets (SMPL, TECX), and 0 sit at an annual
  sheet's latest column, the cell the fill reads.
- **Key Developments:** 52 exports (above). **Customers:** 52 exports (above). A first pass by
  fixed-depth glob counted 51 of each (2,183 rows), missing
  `ciq-archive/kept-2026-10-20-GOOGL-only-local-copy/`: one RTF of each kind, its Key Developments
  reading 120 rows with no flag and its Customers view heading only the recent section.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Pages.** TECX (not pursued, so not rebuilt; STATE row 41) keeps its line. At a re-assembly it
  would read UNKNOWN — "CIQ discloses no recently disclosed customers for TECX" — with the 2 prior
  rows in the note. No other committed page moves.
- **Not built, reported.**
  - A Key Developments spreadsheet is flagged, not read. Reading it through `read_sheets` is a
    route of its own, and no current export needs it.
  - The spreadsheet form of a Customers view (`_parse_relationship_sheet`) has no section split,
    and no export on file is one.
  - The anchor's EDGAR FCF (`_latest_fcf`, `abs(capex.value)`) still assumes a sign, outside this
    brief. #875 refuses a capex filed negative there.
- **`mechanical.py` is touched in one place** (Session C's file, finished): three lines that carry
  the flag into `driver_qa`.
