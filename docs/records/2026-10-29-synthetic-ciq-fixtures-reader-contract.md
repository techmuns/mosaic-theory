---
id: 2026-10-29-synthetic-ciq-fixtures-reader-contract
status: open
date: 2026-10-29
prs: []
supersedes:
superseded-by:
---

# CI opens a CIQ-format file for the first time: synthetic BIFF, RTF and `.xlsx` exports for an invented issuer, and a reader-contract suite with zero skips (audit H-D2, H-D3)

**WHAT.**
- **A committed generator writes the exports.** `tests/fixtures/ciq_synthetic/generate.py` writes
  six small files for an invented issuer, Zinnober Fixture Works Inc (`ZZFX`):
  - a Financials Annual and a Financials Quarterly export, as BIFF `.xls`;
  - the Customers and Suppliers views, as real RTF;
  - the same Quarterly export as `.xlsx`;
  - the same Quarterly export as BIFF in the 1904 date system.

  The outputs are committed beside it. `python -m tests.fixtures.ciq_synthetic.generate --check`
  reports drift, and so does a test.
- **The layout copies only what the readers address.** That means sheet names, the "Period Type:"
  and "Currency" cells, the period-header shapes and the row labels. The issuer's fiscal year ends
  in May, so its quarters carry CIQ's `3 months\nFQ4/CQ2\nMay-31-2026` shape.
- **The values are invented.** Every number, name and date is made up. The cells that name a data
  vendor say "Synthetic fixture" instead.
- **`tests/test_ciq_reader_contract.py` reads these files through the real decode path:** bytes →
  `classify` → xlrd, openpyxl or striprtf → `CiqBundle` → the readers. It never skips. It pins
  today's behaviour for:
  - `CiqBundle.from_files`;
  - `read_sheets` and `read_text` on each format;
  - `excel_date`;
  - the period headers;
  - `stated_currency`, including a CHF variant that shows the check can fire;
  - all eight UNAVAILABLE markers, each decoded from a real BIFF cell and a real `.xlsx` cell;
  - the `.xlsx` path end to end, against its BIFF twin.
- **Known defects are pinned as `xfail(strict=True, raises=AssertionError)`, each naming its
  defect,** so a fix turns the pin into an unexpected pass and fails the run until the marker
  goes. There are 15 such cases from 8 tests:
  - **A-D2:** an UNAVAILABLE 'Total Pref. Equity' cell enters the EV bridge as a 0.0 claim. One
    case per marker, so 8.
  - **A-D3, two tests:** an `FQ1/CQ3` quarter is labelled `FY..` in the quarterly summary, and the
    same-quarter revenue YoY drops out of the multi-year trajectory.
  - **A-D4:** a 1904-system workbook decodes every serial 1,462 days early. The latest close reads
    2022-10-22, not 2026-10-23.
  - **A-D5:** a right-to-left sheet serves its oldest year as the latest. The export's `Order:`
    cell is never read.
  - **A-D11:** an annual-only folder prints `Balance Sheet 'Net Debt' [46173.0]`.
  - **A-X1:** a file named `_Quarterly` whose Period Type cell reads Annual is served as quarterly.
  - **New, found by this suite, under H-D3:** openpyxl returns an empty cell as `None`, and
    `ciq_sheets._currency_rows` reads it with `str()`. The two-column Capital Structure Summary
    'Currency' row therefore states the currency `"None"`, and `stated_currency` on an `.xlsx`
    export reads DIFFER, which `require_usd` would refuse. It is latent, because no real export
    is OOXML today.
- **`openpyxl>=3.1` is now a declared runtime dependency.** `xlwt>=1.3` joins the `dev` extra.
- **`gate.yml`'s pytest step gains `-rs`,** so CI prints every skip's reason.

**WHY.**
- **CI could not open a single CIQ-format file.** Every real CIQ export is licensed and git-ignored,
  so on 0fa8ce4a:
  - CI held no CIQ-format file at all;
  - the 480 tests that read one skipped there;
  - no BIFF writer was installed;
  - openpyxl was neither declared nor installed, so `read_sheets` raised on any `.xlsx`.
- **The fixes that come next would be invisible to CI.** The next reader fixes (audit batches B3–B5:
  markers read as 0, quarter labels, positional "latest", period type from the filename) change
  exactly this layer. Without files CI can open, they would regress there unseen.
- **Why `xlwt` for BIFF.**
  - It is pure Python and writes BIFF8 that xlrd reads.
  - Its output is byte-for-byte deterministic: two builds were byte-equal, and so was a re-run
    over the committed files.
  - It can write the 1904 date system, which A-D4 needs and only a real BIFF file can carry.
  - It has not released since 1.3.0 (2017). Here that is a property: its bytes cannot drift under
    a release.
  - **Rejected:** a hand-written BIFF/OLE writer is too much new code to trust. A LibreOffice
    `.xlsx`→`.xls` conversion is not reproducible on a runner without soffice.
- **Why declare openpyxl rather than refuse `.xlsx`.** `read_sheets` already has the OOXML branch,
  and the classifier routes any zip to it. A refusal would replace a working reader with an error.
  The fixture also showed the branch reads every number and date as its BIFF twin does: one test
  compares them cell by cell. The one place it diverges is the `None` defect above, which the
  suite now pins.
  - **Typing:** openpyxl 3.1.5 ships no `py.typed`, so `ciq.py:174`'s
    `# type: ignore[import-untyped]` is still needed, and `mypy --strict vinci` stays clean with
    it installed. `types-openpyxl` is not added, because under `warn_unused_ignores` it would
    redden that line.
- **The `.xlsx` comparison is by values, not bytes.** A drift check on the `.xlsx` compares decoded
  cell values, not bytes, because openpyxl's XML may change across releases while its values may
  not. Its zip and document timestamps are still pinned, so a re-run is a no-op in git.

**HOW VERIFIED.**
- **New suite on clean code:** 65 passed, 15 xfailed, **0 skipped**. The worktree has no
  `data/manual/` directory, as on a CI runner.
- **Mutation, before and after.** Three mutants of `ciq.excel_date`, each run against the whole
  offline suite in a fresh worktree of 0fa8ce4a (no CIQ data), and then against the new suite. The
  "before" counts are for the whole suite on 0fa8ce4a; the "after" counts are for the new suite only.

  | Mutant | Before (current suite) | After (new suite) |
  |---|---|---|
  | **Rounding a fractional serial instead of truncating it** | **green: 7,779 passed, 534 skipped** | **red: 1 failed** |
  | The 1900 epoch shifted one day | red: 23 failed | red: 9 failed, the BIFF Balance Sheet serials among them |
  | The `datetime` branch deleted (what openpyxl returns for a date) | red: 2 failed | red: 6 failed, all on the `.xlsx` path |

  Each mutant was reverted after its run; `git diff -- vinci/` is empty, and the new suite is back
  to 65 passed, 15 xfailed.
- **The "invisible" claim holds for some mutants, not all.** A blanket "a mutated `excel_date`
  leaves CI green" is true only of some mutants. Of the three tried, only the rounding one was
  invisible to the current suite.
- **The only test that catches the rounding mutant is a unit literal (46173.75 → 2026-05-31), not a
  file read.** The fixture's date cells are whole serials, as CIQ's are, and inventing a time of day
  to make a file-level test fire would be fabricating a shape.
- **Toolchain:** ruff (`vinci tests frontend`) and `mypy --strict vinci` (215 files) are clean.
  Full `pytest -m "not network"`: FULL_SUITE_TOTALS.
- **Skip reasons are now printed:** `-rs` prints `SKIPPED [n] file:line: reason` lines, so the CI
  log will show which tests skipped and why.

**BOUNDARY.** All counts were measured on 2026-10-29, offline (`-m "not network"`, 38 deselected), on
macOS, Python 3.12, openpyxl 3.1.5, xlwt 1.3.0.
- **"480 skip in CI"** is the audit's verified count on 0fa8ce4a: the tests skipped for want of the
  licensed CIQ folder, in 27 files. This build changes none of them.
- **The mutation rows** are the whole offline suite at 0fa8ce4a, run in a fresh worktree with no
  `data/manual/`, one mutant at a time (534 skips each, the same total as unmutated). The "after"
  counts are `tests/test_ciq_reader_contract.py` alone, at this branch's head.
- **"65 passed, 15 xfailed"** is that file alone. 15 is 8 xfail tests: 7 plain, plus 1
  parametrized over the 8 markers.
- **"0 real exports are OOXML"** is the audit's magic-byte census of the licensed corpus, which this
  build did not re-run.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The fixture is a layout, not a sample.** It reproduces the cells the readers address, not
  everything a real export holds: there are no Estimates, comps, Key Developments or transcript
  files. A reader that keys on a cell absent here is not covered by it. Adding one is a change to
  the generator plus a re-run, never a hand edit, because the drift test refuses one.
- **xlwt is unmaintained.** It works on Python 3.12 today. If a future Python breaks it, the
  reproducibility tests fail red and do not skip. The committed BIFF files keep reading, since the
  reader is xlrd.
- **The 480 licensed-data skips remain, by design.** Most pin values per real ticker, which no
  synthetic file can stand in for. This build adds the decode layer they never had in CI; it does
  not convert them.
