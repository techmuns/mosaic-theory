---
status: open
date: 2026-11-10
prs: [965]
supersedes:
superseded-by:
---

# Fix request 2, order 6, the CIQ reader's RA-D16 and RA-D15: the LTM flag quotes each quarter's own cell instead of '-', and an empty `.xlsx` cell states no currency, so an all-USD `.xlsx` export is not refused as foreign. No figure moves; five pages' QA flags reword when re-assembled

**WHAT.**
- **RA-D16** (`ltm_quarters.QuarterCell.text`, `_cell_words`). The flag that checks an LTM against
  its four quarters printed every quarter carrying no figure as '-'. The auditor's ORCL case read
  "… + - (Q3 2026-02-28) + …" for an 'NA' cell, and the same for 'NM', a blank and 'Entitlement
  Needed'. The flag now quotes the cell as exported: 'NA', 'NM', blank, or absent when the row has
  no such cell. Its "UNVERIFIED, because … read(s)" line says the same words.
- **RA-D15** (`ciq_sheets._currency_rows`, and the comps book's `_comps_label`). openpyxl hands an empty cell back as None, and
  `str(None)` made a two-column 'Currency' row state the currency "None". An all-USD `.xlsx`
  export was refused as foreign (`require_usd`). This is H-D3's case, which
  `tests/test_ciq_reader_contract.py` kept as a strict xfail; the xfail is lifted.

**WHY.** Document 15, order 6: "each failure states its real cause".

**HOW VERIFIED.**
- **Fail first.** `tests/test_ltm_flag_and_xlsx_currency.py` fails 7 of 7 on `origin/main`'s
  `vinci/` and passes here. The real-export pin marks the newest quarter of an agreeing row on
  AMZN's export, as it stands, with four of document 7's markers; AMZN's annual export carries an
  LTM column, SMPL's does not. The twins run on the synthetic issuer and its `.xlsx`.
- **No figure moves; five pages' QA text does, once re-assembled.** Every export on disk is BIFF
  (`.xls`), so RA-D15 changes no read. The flag is QA text, written only where a quarter carries no
  figure, and '-' is itself a marker: EPAM, MCK, VITL, VRRM and WLK commit UNVERIFIED flags printing
  `- (Q…)`, which re-read on their exports on disk as `'-' (Q…)` (review 2026-11-10; the
  "read(s) '-'" tail is unchanged). A row that stops short of a quarter's column reads `absent`,
  pinned through `check`.

**BOUNDARY.** The exports under the primary checkout's `data/manual/ciq/` on 2026-11-10.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Order 6's other three CIQ-reader IDs are not in this PR:
- **RBC-D2** is one defect with RA-D10 and goes with order 5's file-kind fix.
- **RBC-D5** (an empty view called a parse failure or an "OLE-disguised Word doc") edits the
  relationship reader #957 refactors, so it stacks on #957.
- **RBC-D10** (a "not run" reason naming the removed back-fill) is text in every committed CIQ
  quality scorecard since 2026-10-28, and the latest must reproduce byte for byte. Its fix comes
  with a regenerated scorecard, as an artifact commit.

**Extraction version** `2026-11-10.loud-with-the-right-cause`; the drift pins are re-pinned.
