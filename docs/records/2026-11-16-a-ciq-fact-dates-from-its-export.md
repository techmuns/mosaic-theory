---
id:
status: open
date: 2026-11-16
prs: [1082]
supersedes:
superseded-by:
---

# A page is dated from the day its CIQ inputs were exported, never the close they describe. Each comps export's own stated date is recorded in the page's input record and counted in `analysis_as_of`. Seven of the nine pages that read early move at $0; NKE and ORKA wait for their next assembly (the Codex P1 on #1070)

**WHAT.**
- **The defect.** `date_semantics.analysis_as_of` was, by its own stated rule, the latest of the page's inputs' DATA dates. A CIQ export holds history as restated up to its export, so a CIQ fact is knowable from its export date, never from the close it describes (CLAUDE.md, PUBLISHED DATA). IT's page read 2026-11-11 while its comps panel, the source of its market cap and TEV, was exported 2026-11-12. Codex raised it as a P1 on #1070, and it was deferred there (`docs/records/2026-11-14-rebuild-group-3-it.md`, WHAT IT COSTS).
- **Why it could not be read.** No page recorded an export date as a structured field. The build knows the comps workbook's raw `As-Of Date:` header (`ciq_sheets.comps_export_stamp`), but the page carried it only inside the TEV `source_ref`'s text ("…data 2026-11-11, exported 2026-11-12"). That text is display, and no parser may read it.
- **The fix, in code:**
  - `inputs.export_dates(bundle)` is the one reader of the export date a workbook STATES of itself. Today that is only the comps workbook's header, read raw, never the assembler's corrected close.
  - The build records the date per input as `inputs.ciq[].export_date`, beside the sha256 it already records (`provenance.FileRead.export_date` → `CiqExport.export_date`). `load_bundle` records every file it read even when the date read raises.
  - **Named `export_date`, not `export_stamp`.** In `inputs`, an "export stamp" is a file's 10-hex sha256 prefix (`_STAMP`, `stamps`, `stamped_by`). A date under that name beside `stamped_by` would collide with it, so the date field is called `export_date`.
  - `date_semantics` names the latest such date (`ciq_exported_as_of`) and counts it in `analysis_as_of`. The rule text it then states is `valuation_basis.RULE_KNOWABLE`.
  - A page whose record states no export date keeps today's rule (`RULE_DATA_DATES`, word for word), and both new keys are ABSENT, never null. Such a page round-trips byte-identically: all 26 committed pages did before the pass.
  - Both fields sit OUTSIDE `mechanical`, which is the synthesis's only input, so no synthesis request moves.
- **The $0 path for committed pages.** `refresh.export_date_transform(ticker, roots)` is a `refresh_dossier` top-level step. `inputs` joins `_TOP_LEVEL_REFRESHABLE` for that ONE use.
  - It fills a comps row only when a file under the CIQ roots hashes to the FULL sha256 the page's own record names (`inputs.candidates`, the backfill's identity rule).
  - It reads the date off that file with the build's reader, under the file name the record gives when the same bytes sit under several names.
  - `refresh_dossier` refuses any other change to the record, and any move or removal of a date already recorded (`_only_export_dates`).
- **The pages.** Run over the 26 committed pages at main `c58d5b2f`, CIQ folder read only:

| page | record | comps export (stated) | `analysis_as_of` before → after |
|---|---|---|---|
| IT | build | 2026-11-12 | 2026-11-11 → **2026-11-12** |
| MCK | build | 2026-11-05 | 2026-11-04 → **2026-11-05** |
| TECX | build | 2026-11-09 | 2026-11-06 → **2026-11-09** |
| V | build | 2026-11-09 | 2026-11-06 → **2026-11-09** |
| VRRM | build | 2026-11-09 | 2026-11-06 → **2026-11-09** |
| WERN | build | 2026-11-12 | 2026-11-11 → **2026-11-12** |
| WLK | build | 2026-11-09 | 2026-11-08 → **2026-11-09** |
| EPAM | build | 2026-11-09 | 2026-11-11, unchanged |
| GOOGL | build | 2026-11-02 | 2026-11-11, unchanged |
| LLY | build | 2026-11-02 | 2026-11-11, unchanged |
| NCNO | build | 2026-10-28 | 2026-11-11, unchanged |
| NFLX | build | 2026-10-28 | 2026-11-04, unchanged |
| SMPL | build | 2026-11-04 | 2026-11-11, unchanged |
| TJX | build | 2026-10-18 | 2026-11-11, unchanged |
| UBER | build | 2026-11-05 | 2026-11-06, unchanged |
| VITL | build | 2026-11-09 | 2026-11-11, unchanged |
| AMZN BRBR BURL CNXC FUBO NKE ORKA PARR ROST TGT | backfill | not recorded | unchanged, unfilled |

  - **Unfilled: the 10 pages whose input record is a BACKFILL.** A backfilled record resolves only the exports a page stamped itself, and none of them stamped its comps export (`inputs.UNRECORDED_UNSTAMPED_CIQ`). So no record names a comps file to read. Among them, **NKE and ORKA keep an `analysis_as_of` before their comps export** (stated in their TEV `source_ref`s: NKE 2026-10-28 against 2026-10-29, ORKA 2026-10-23 against 2026-10-26) until their next assembly records the date.
  - No page whose record names a comps export failed to match: all 16 exports are still on the Drive folder at the sha256 their pages record.

**WHY.**
- **The rule is set by face validity:** what the page could have known, and when. No outcome was read.
- **Why only comps counts.** Of the CIQ inputs, only comps states its own export date on the corpus. CIQ stamps no Financials export. The page has only its filesystem `source_mtime`, which is not a date CIQ states and is absent on FUBO, ORKA and TECX, so it is not counted. The Estimates export states only a `≥` floor, already counted at its floor. An Estimates export that carried a header would already date the page through `forward_consensus.as_of`.
- **Why a column's stated filing date is not counted.** CLAUDE.md allows one as an alternative knowable date for a CIQ fact, but a filing inside an export cannot postdate the export, so it never moves a latest-of.
- **Readers, searched before any change.** `git grep -E "analysis_as_of|date_semantics|DateSemantics"` over `vinci/`, `frontend/`, `scripts/`, `tests/` and `.github/`. The sibling fields' names were searched as a second vocabulary. `git log -S analysis_as_of` on code paths finds only #702.
  - The field is read only by its writer, the schema, three docstrings and tests. The renderer, `dossier.js`, the ledger, scoring, the seal, the screen, the monitor and the verdict path do not read it.
  - `vinci/theme_intelligence` has its own `analysis_as_of`, a homonym.
  - So this is not a decision-path change.

**HOW VERIFIED.**
- **Fail first at base.** `tests/test_analysis_as_of_knowable.py` fails to import on main `c58d5b2f` (`export_date_transform`, `_only_export_dates` and `RULE_KNOWABLE` are new).
  - **On behaviour, at base:** IT's page as committed at `c58d5b2f`, given its comps export date 2026-11-12 in its record, derives `analysis_as_of` 2026-11-11 with no `ciq_exported_as_of`, and base's serializer drops the date. The same holds for UBER.
  - **At head:**
    - IT's page derives 2026-11-12 (positive).
    - UBER's derives 2026-11-06, its price date, with its export date 2026-11-05 named (negative: an export before the data keeps the page's date).
    - NKE's block is word for word the committed one (negative: no recorded date, no change).
  - Value pins read IT, UBER and NKE as committed at `c58d5b2f`, frozen byte-identical in `tests/fixtures/frozen_pages/` and each checked by its git blob. The export date is read through the production reader off `tests/fixtures/ciq_comps_export_date.json`: IT's and UBER's comps Financial Data sheets, cut to the 2 cells the reader reads. Those exports are the ones their pages record by sha256.
- **Guards, each with its negative.** These pins each run on a real page:
  - a record naming no comps export is left alone;
  - a same-named file with other bytes is left alone, because the identity is the sha256;
  - the seam refuses a changed sha256 or `recorded`;
  - `refresh_dossier` refuses a transform that drops an export from the record, and leaves the page's bytes as they were.
- **The real workbooks.** Two CIQ-bound pins skip without the folder and pass with it linked:
  - the transform fills IT's export date off its real export, with the record otherwise unchanged;
  - `load_bundle` under a recorder records 2026-11-12 on the comps read and nothing on IT's other ten exports.
- **The corpus pin, updated.** `test_valuation_basis.test_every_page_names_its_dates_from_its_layers` now reads each page's `inputs.ciq[].export_date`. It requires `ciq_exported_as_of` to be their latest and `analysis_as_of` to be the latest of the six data dates and the export dates.
- **End to end, on the committed corpus.** `test_no_committed_page_is_dated_before_a_ciq_export_it_records`: every page whose build recorded a comps export states that export's date, and no page is dated before an export date it records. It fails on the pages as they stood before the pass (EPAM first) and passes after it.
- **Code review** (`/code-review high --fix`, round 0), 9 findings:
  - **Fixed, each behind a test that failed before it:**
    - (1) `load_bundle` recorded nothing when the date read raised.
    - (2) the seam admitted moving or removing a date already recorded.
    - (3) a same-bytes copy under another name could be read as no comps export.
    - (4) a non-mapping record raised instead of being left alone.
    - (5) the reader's loop looked per-workbook but read one sheet.
  - **Fixed by a rename:** (6) the `export_stamp` name collision, now `export_date`.
  - **Dismissed:**
    - (7) hashing every candidate file: the probe that hashes the same files ran over all 26 pages in under 1 s (2026-11-15).
    - (8) the operator AS_OF sidecar: when it stands in for the comps header, `tev_as_of` and `market_cap_as_of` already are that date, uncorrected, so it is counted.
  - **Accepted, stated below:** (9) a build record carrying a date a later refresh wrote.

**BOUNDARY.**
- **Pages:** the 26 committed `data/dossiers/*/dossier.json` at main `c58d5b2f` (merged 2026-11-14, #1078).
- **The "9 of 26 read early" count:** each page's latest "exported YYYY-MM-DD" in a `source_ref` against its `analysis_as_of`, read at `c58d5b2f` on 2026-11-15. It was used to count, never to fill a field. That is the group 3 record's 8 at `4f7a5d64` plus WERN, landed by #1076.
- **CIQ:** the Drive folder (`data/manual/ciq`), read only, 2026-11-15/16. The 16 comps exports matched by full sha256 under `<root>/<TICKER>/`.
- **Moved:** 7 pages' `analysis_as_of`. 16 pages gain `inputs.ciq[comps].export_date`, `date_semantics.ciq_exported_as_of`, the new rule text and one `layer_refreshes` entry.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** No model call, no Polygon or Tiingo pull, no re-assembly.
- **NKE and ORKA still read early** until their next assembly, which records the date. That is a paid build each and not this PR's to spend; STATE §5.0 names them.
- **A build record now carries a field its build did not write.** The 16 build-recorded pages gain `export_date` from a later refresh. `layer_refreshes` names the write (`refresh`, `date_semantics` and `inputs`, at this vintage), the house record of a change made after assembly.
- **Accepted risk:** a comps header that ever stated something other than the export date would date the page by it.
  - The repo has measured the header as CIQ's export stamp, 11 of 11 against the store's prior close (`freshness.corrected_ciq_as_of`), and this rule relies on that.
  - **Falsifier:** a comps export whose `As-Of Date:` is earlier than its own printed close's trading day, which `assemble`'s date match would report as no match.
