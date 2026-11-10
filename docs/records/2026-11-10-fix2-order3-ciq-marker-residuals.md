---
status: open
date: 2026-11-10
prs: []
supersedes:
superseded-by:
---

# Fix request 2, order 3, the CIQ reader's residuals (RA-D3, RA-D8, RA-D13, RBC-D6, RA-D11): a marker is a stated gap, never an older guide, a dropped segment or an empty consensus with no reason; the spreadsheet Customers route reads through the RTF route's reader; a failed LibreOffice conversion is a call left out and named. No committed figure moves; ORKA's and TECX's pages gain a `consensus_levels_note` when next assembled

**WHAT.** Five defects TeamNostra's re-audit (document 14) found in code document 12's fixes
touched, each reproduced on the CIQ exports on disk before the fix (in memory: no export is
written), each now behind tests that fail on `origin/main` `5e3def4a`:
- **RA-D3, Guidance** (`ciq_sheets._guidance_reads`). A dated column whose Guidance cell is a
  marker was skipped before its date was read, so the next older dated guide became the
  "latest" and went to the guide check. On SMPL's export, with both revenue guides of
  2026-10-27 (FQ1 2027 and FY 2027) set to 'NA', the read was FQ4 2026's 322.00–332.00 of
  2026-07-09. Now the newest date CIQ gives a guide is the latest whatever its cell holds:
  when no cell at that date reads, the read is `unread` (`_GuidanceRead.unread`, the cell
  named), the bridge says "an older guide is never read in its place", and the guide check
  receives no guide. Such a cell dated after the page's price date is a guide given after
  it, so the sheet is withheld (STATE row 57's rule).
- **RA-D8, Segments** (`_segment_section`, `_segment_roster`). A segment whose latest cell is a
  marker left the mix, and the count the gap test reads fell with it. UBER, with Delivery's
  latest cell set to 'NA', printed "Mobility 57%; Freight 10%" and a count of 2. CIQ also
  marks a segment the period does not report (EPAM's Russia), so a marked row is a hidden
  segment only when the rows that read no longer sum to the total (`_SEGMENT_RECONCILE_TOL`,
  0.5%, the lean collapse's 99.5%). Then the field is UNKNOWN naming the row, and the count is
  None.
- **RA-D13, Consensus** (`consensus_block`). One marker in the probe cell, the Market Summary's
  or the block's, left `consensus_levels` empty with nothing said. Now
  `consensus_levels_read` returns why, and assembly writes it beside the field
  (`ConsensusContext.consensus_levels_note`; in `synthesis.NOT_SENT` and `DROP_WHEN_NONE`, so
  no request moves; ORKA's and TECX's pages gain the note when next assembled, below).
- **RBC-D6, the spreadsheet Customers route** (`customer_roster`). It had its own reader, which
  missed #881's and item 33's fixes: a prior section, a repeated header, a Supplier Name
  column and the recent section's own "There are no recently disclosed customers listed".
  Both formats now go through one reader (`_relationship_table`). An RTF line is split on its
  pipes, a sheet row taken as read, and the line-level rules apply to the cells joined back.
- **RA-D11, LibreOffice** (`ciq.read_text`). `check=True` raised `CalledProcessError`, which no
  caller catches, so the G-D4 skip-and-flag path (`unparsed_transcript_flag`) never ran. A
  non-zero exit is now a `CiqParseError` naming the exit and LibreOffice's words. With AMZN's
  first call failing under a stub `soffice`, the slice holds the others and the flag names
  that call.

**WHY.** Document 12's fixes made every latest-cell reader refuse a marker (`latest_cell`).
These readers walk a sheet their own way and kept the step-back. The audit's done-when for
order 3 is each reproduction as a passing test.

**HOW VERIFIED.**
- **Fail first.** The new tests (`tests/test_ciq_marker_residuals.py`,
  `tests/test_libreoffice_exit.py`, `tests/test_customers_sheet_route.py`) were run against
  `origin/main`'s `vinci/` (extracted by `git archive`), from the primary checkout so the
  licensed folder is read:
  - 37 of 38, 3 of 3 and 5 of 6 fail there. The passes are the negatives: the corpus pin that
    real '-' segment rows stay silent, and the plain-sheet pin.
  - The real-export pins run on each export as it stands and assert invariants, not values.
  - Each has a constructed twin that runs on CI.
- **No page moves ($0 compare).** Every touched reader was dumped at both codes on all 36
  folders on disk: `guidance_bridge`, `guidance_bridge_rows`, `revenue_guide_lohi`,
  `segments`, `segment_ebitda`, `geographic`, `segment_count`, `consensus_levels` and
  `customer_roster`. 0 of the 324 (folder, reader) cells differ. Every synthesis request is
  byte-identical (the new field is not sent), so no panel check is owed.
- **Two pages gain a note (review round 0, `consensus_levels_read` on the same 36 folders).**
  That compare dumped `consensus_levels`, not the new note. Read directly, 2 of the 36 folders
  return one: ORKA and TECX, the two pre-revenue names `tests/test_consensus_transform.py`
  exempts. Their pages carry no levels today and will carry `consensus_levels_note` when next
  assembled; no figure moves. The refresh transform now removes the note wherever it writes
  levels, so a page never carries both.
- **The censuses behind "latent".**
  - Guidance: 0 of the 5,417 columns that carry a date or a guide hold a date over a cell
    that does not read.
  - Segments: on the 69 blocks, the rows that read sum to their total within 0.0051%. 28 of
    them sit beside a row CIQ marks '-' at the latest column.
  - Customers: all 36 Customers exports are RTF.
  - Transcripts: all 68 are OLE Word files read through LibreOffice.

**BOUNDARY.** The exports on disk under the primary's `data/manual/ciq/` on 2026-11-10 (36
ticker folders, the 27 pages' and nine others), read through `vinci` at `5e3def4a` and at this
branch. The marker list is document 7's eight (blank, '-', '—', 'NM', 'NA', 'N/A', 'Entitlement
Needed', 'No Data Available'). The census counts are over those folders' current exports only,
not `ciq-archive/`, which is absent on this machine.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Not reproduced on a real spreadsheet.** No spreadsheet Customers export is on disk. The
  RBC-D6 pin lays TECX's and HLF's real RTF tables out as sheets and asserts the two routes
  read alike. Falsifier: the first real `.xls` Customers export whose read differs from its
  RTF twin's.
- **Found, not fixed.** `read_text`'s `pdftotext` call keeps `check=True`, the same shape as
  RA-D11 on the PDF route. No audit ID names it. Reported in the PR.
- **Found, not fixed: a numeric zero is no figure to `_stat_num`.** It reads `str(v or "")`, so a
  numeric 0.0 cell is no number, while the Market Summary's, stringified first, reads 0. ORKA's
  and TECX's consensus blocks are lost to that falsy zero, not to absent coverage, which the
  exemptions' stated reason says. Their note states it as it is ("row N reads 0.0 at FY2026,
  which this reader does not count as a figure"), so it names the real cause rather than
  quoting '0.0' as a marker (review round 0). Fixing `_stat_num` would identify a block on two
  pages (a decision-path change), so it is reported, not made here.
- **Extraction version** `2026-11-10.marker-residuals`; the drift pins are re-pinned.
