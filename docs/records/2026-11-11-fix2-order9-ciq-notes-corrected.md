---
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, order 9, G-D8 to G-D15: `docs/ciq_extraction_notes.md` is corrected against the code and marked superseded where it differs; the temperature and re-roll statements in `docs/engineering.md` and `docs/RUNBOOKS.md` match the code. Docs only

**WHAT.**
- **The ruling direction.** Each contradiction is resolved one way: the code is right, and the docs
  change to match it. Document 12 §4 asked for the notes file to be "corrected or marked superseded";
  this does both.
- **The notes file** (`docs/ciq_extraction_notes.md`):
  - line 3 gains a pointer: "Superseded where it differs from the code … see *2026-11-11
    corrections* at the end";
  - a closing section, "## 2026-11-11 corrections", gives one line per ID;
  - each wrong statement is corrected where it stands.
- **The eight IDs:**
  - **G-D8:** the Surprise sheet has fiscal-quarter and company-level (Revenue, EBITDA …) blocks; the
    code reads its fiscal-year table only.
  - **G-D9:** no code reads a holders export; the holder rules are marked superseded, and the field
    contract's F26 rules govern any future reader.
  - **G-D10:** the live relationships reader (`customer_roster`, F27) keeps every relationship type;
    the supply-chain filter belonged to the removed `vinci/ciq/` parser (#964), and the
    `SUPPLY_CHAIN_TYPES` list now serves only the 10-K graph extraction.
  - **G-D11:** the missing-data markers are the code's eight (`ciq._UNAVAILABLE_CELLS`), and `NM` is
    a stated marker with no number, never a value.
  - **G-D12:** Key Developments are RTF on disk, but a spreadsheet export has occurred and is refused,
    and the header varies (columns found by label).
  - **G-D13:** the driver step reads figures from the transcripts; the output cap is 16,384 tokens; a
    missing `evidence_balance` is flagged, not refused.
  - **G-D14:** `checklist.md` is not in this repository; no "Last verified" date was ever recorded;
    Koyfin is a manual cross-check no code reads (`docs/data_sources.md`).
  - **G-D15:** pass no sampling parameter (`vinci/graph/llm.py`, "DO NOT ADD THEM BACK"), in
    `docs/engineering.md`; never re-roll a WRITTEN synthesis for cleaner flags, and a build the 19c
    guard refuses is re-run as its own error says, in `docs/RUNBOOKS.md`.

**WHY.** Document 15, order 9: "the notes file corrected or marked superseded". Document 14: the file
"still says 'NM is a REAL value, not missing'".

**THE GUARD.** `tests/test_ciq_notes_follow_the_code.py` has one test per ID, and two for G-D15.
Each ties a corrected claim to the code it describes: the doc must state it, and the code must still
hold it, read from the symbol itself (`ciq._UNAVAILABLE_CELLS`, the client's `max_tokens` default,
`synthesis._TOOL_TEMPLATE`, `llm._REJECTED_SAMPLING_PARAMS`, the 19c error's own words). A doc
that drifts, or code that moves under it, fails that ID's test. The fix log's `fixed` status needs
a test node, and a docs-only change gave none.

**HOW VERIFIED.**
- **Fail first.** On `origin/main`'s docs (`173b4818`), all 9 tests fail, each on its doc claim:
  for example, rule 1 names 2 of the 7 non-blank markers, and the notes give an 8,192-token cap.
  Here, all 9 pass.
- **Every claim checked against the code or the exports.** The CIQ export claims were counted on the
  36 ticker folders under the primary checkout's `data/manual/ciq/` on 2026-11-11 (382 export files),
  read only, through `classify`, `read_sheets`, `read_text` and the live readers.
  - Surprise sections, of 36 sheets: 'Fiscal Quarters' 36, 'Fiscal Years' 35, 'Calendar Years' 10;
    a 'Company Level' block on all 36.
  - Markers in 170 spreadsheets (blank cells not counted): `-` 958,269 cells, `NA` 43,655, `NM`
    33,734, `Entitlement Needed` 16,515, `No Data Available` 69, `N/A` 18, `—` 0.
  - Customers files: 2,289 recent rows on the 35 with a table, by type: Customer 978, Client
    Services 921, Distributor 241, Licensee 126, Lessee 12, Borrower 6, Franchisee 3, Tenant 2.
  - Key Developments: 36 of 36 `rtf_text`; 29 five-column and 7 four-column headers.
  - `checklist.md`: `git ls-files | grep -ci checklist` gives 0, and no commit on any branch or tag
    ever added one.
- **No code-cited line moved.** Code and tests cite these note lines by number: 61, 63-66, 74, 116,
  126, 136-138, 197, 204. Each holds the same content after the edit: 61 is corrected in place on the
  same line, and the rest are byte-identical to `origin/main`. All growth starts at line 208.
- **The lints that read docs pass:** `test_record_hygiene`, `test_config`, `test_no_local_paths`,
  `test_records_ledger`, `test_state_identifiers`, `test_fix_log`, `test_cohort_split`.

**BOUNDARY.** The exports above on 2026-11-11; the repository at `origin/main` `91b1af4a`, and the tests at `173b4818`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Found, not fixed (code comments, outside a docs PR):**
  - `ciq_sheets.py:384` cites notes "line 197" for the Close-column rule, which sits at line 291;
  - "~line 204" (`ciq_sheets.py:1100`, `tests/test_dossier.py:3693`) points at the adjusted-basis
    paragraph, where the same-quarter YoY rule they mean is at lines 159-167;
  - a `ciq_sheets.py` section comment still says transcripts carry "no numbers derived", and another
    still describes the fixed four-column Key Developments header;
  - the `surprise_history` docstring (`ciq_sheets.py:2159`) still says the sheet is "by FISCAL YEAR
    (no quarterly view)", the claim G-D8 corrects.

  These were already wrong on main. Fixing them changes code.
- **For the operator:** whether Koyfin is still used (it decides whether it stays in the source
  inventory), and whether re-running a build until the 19c guard passes, which no code caps, is
  acceptable. The docs now state what the code does.
- **Untouched, separate IDs:** the notes' fixed row positions (RG-D20(i)); `docs/data_sources.md`'s
  source map still lists CIQ Holders, Charting and Insider Trading, which no code reads; and the
  notes' own Insider Trading rules (the date, forward-fill and *Transaction Type filtering*
  sections) and *Charting file* rules still read as live, though no code reads either export (no
  `charting` kind since #908; insider activity comes from Form 4).
