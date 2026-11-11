---
status: open
date: 2026-11-10
prs: [941, 951, 1006]
supersedes:
superseded-by:
---

# Publish the fact, not the quote, PR 3 of 3 (RG-D19, RG-D8): the 25 committed pages, their mirrors and the 8 page fixtures carry each transcript row's fact and locator and none of its words; the words are in the operator's spool; the rule is in CLAUDE.md, and its test fired 6,284 times before the pass and 0 after

**WHAT.** The last PR of the stream. Design: `docs/records/2026-11-10-driver-facts-not-quotes.md`.
Store: `docs/records/2026-11-10-driver-evidence-store.md`.

1. **The $0 pass, `vinci driver-facts-pass`** (`vinci/dossier/driver_pass.py`). No model call, no
   network, no re-assembly. For each committed page:
   - it gives each transcript row the fact code reads from its own quote (`check_fact`);
   - it gives each row a locator;
   - it files the row's passage and its stated value in the spool;
   - it writes the page through the recorded writer `driver-facts-pass`.

   The one serializer then leaves each row's `verbatim`, `following_context` and `value` off the
   page.
2. **The rule, in CLAUDE.md** (operator ruling 2026-11-10, relayed by the coordinator: "yes to
   all"). No public field quotes more than 12 consecutive transcript words, and a driver row
   quotes none. `tests/test_public_transcript_text.py` holds it on every committed page, mirror
   and test fixture.
3. **The 8 page fixtures** (coordinator, 2026-11-10: "Include the 8 fixtures and their 193 rows in
   PR 3"). They are passed with `--pages` and written UNRECORDED: a frozen page carries no refresh
   entry. Their passages and claims are in the same spool as the pages'.
4. **No test reads git history or the private store** (coordinator, 2026-11-10). `tests/pre_strip.py`,
   which read the pre-strip pages at `586fdcfd`, is deleted (RG-D22/RH-D5; row 56). In its place
   is `tests/stripped_pages.py`:
   - a test that needs only the FACT pins on the committed page;
   - a test that needs a row's WORDS reads them from the licensed CIQ call ON DISK, by the
     row's locator, checked by the file's sha256 and the quote's. It skips in CI, naming the
     missing export;
   - the pass's and the store's own tests run on a real page whose transcript rows are invented
     ones (`synthetic_page`), never licensed text.
5. **A full locator is given only when the row's words are exactly that file's** (found in the
   rehearsal). See WHY.
6. **A build never writes a page holding words it could not file** (`/code-review high`, round
   0, finding 1). Before this, the serializer kept an unfiled row's words, and `_write` wrote
   them, printing that they were "kept only in the licensed call".
   - Now a row that names its call but has no locator is filed call-only.
   - A row that cites no call, or states no value, makes `_write` refuse the page. The page
     pass keeps the same rule.
   - None of the 1,042 committed rows cites no call.
7. **The vintage is its own entry file.** `2026-11-10.driver-text-filed` is
   `vinci/dossier/extraction_versions/2026-11-10.driver-text-filed.json`.
   - The re-sync onto #988 and #989 (`76c21609`) moved it out of the frozen table, following
     `2026-11-10.kind-by-exact-name`.
   - The re-sync onto #986 (`cb8f8a7f`) re-created it with `new_entry`. It now follows main's two
     heads, `2026-11-11.dividend-level-na-unstated` and
     `2026-11-11.same-day-filings-and-alias-by-day`, so it is again the one head.
   - The id the pages carry is unchanged, and so is its names text, byte for byte.
8. **A cited call that is on disk and does not read refuses the page** (found on the re-sync onto
   #986, 2026-11-11).
   - FUBO's dry run there located 0 of its 8 rows, where the first real pass had located all 8.
     Another session's LibreOffice conversion was running, and LibreOffice fails a conversion
     while another runs.
   - The reader leaves out a call whose read fails. So before this, the pass would have written
     those rows call-only because of a failed read, not because the file lacks the quote.
   - `prepare` now refuses such a page, unwritten and unspooled, just as
     `confirmation.page_transcripts` (#982) refuses the same failure.
   - Pinned by `test_a_cited_call_on_disk_that_does_not_read_refuses_the_page`, which runs through
     the real `_calls_on_disk` with a file on disk. On the unfixed pass it failed:
     `'written' == 'refused'`.
   - The first real write is unaffected. Each of its call-only rows was measured: its context is
     not the file's, or its call is not in today's CIQ folder (WHERE THE LOCATOR REACHES).
9. **The vote rule's ten-draw confirmation reads the words back from the store** (#982 meeting
   PR 3 on the re-sync onto #986; operator, 2026-11-11, relayed by the coordinator: "Read them
   back from the store (Recommended)").
   - `log-verdict` seals a proposal only from C(iv)'s confirmation, which draws ten syntheses
     on the committed page's layer (`confirmation.layer_as_synthesized`). After PR 3 that
     layer's filed transcript rows hold no words. The confirmation would have drawn on their
     figures alone, less evidence than the build had, and the ledger would have sealed it.
   - Main's parity test (`test_the_layer_is_read_as_the_replay_harness_reads_it`) failed on the
     merge for this reason: PR 3's replay reader refuses such a page, and the confirmation's
     reader did not.
   - `confirmation.with_words` now reads each stripped row's quote, context and stated value
     back (`driver_evidence.rehydrate` over `EvidenceSpool.from_env().get`) before the draws.
   - It refuses before any draw, recording nothing, when the store is not configured, a record
     is missing from it, or a row still holds no words. The words are never guessed.
   - The reuse key still reads the committed layer, whose locators carry the words' hashes, so a
     recorded confirmation is found without the store.
   - `confirmation.py` is #982's decision path. The change adds no verdict field and does not
     touch the proposal mapping; it gives the draws the input the build had.
   - Pinned on a stripped page holding invented rows, re-filled from a temporary store:
     - its ten requests are byte-identical to those on the same page before its words came off;
     - drawn without the read-back, they differ;
     - with no store, or an empty one, it is refused before any draw.

     Both pins failed on main's `confirmation.py` (the requests differed; `DID NOT RAISE`). The
     parity test now compares the two readers on each committed page with its words
     (`stripped_pages.replayable`).

**THE FIRST REAL WRITE** to the operator's spool (`$VINCI_EVIDENCE_SPOOL`, the operator's
`driver-evidence` folder beside `manual/ciq` on the shared Drive) happened on 2026-11-10 from
17:45:41Z to 17:47:22Z, on the assembling Mac, from this branch at `0908e091` (code, tests, the
review fixes and main merged), before PR 3 opened.
- The folder held 0 entries before.
- It wrote 2,266 files, flat and write-once, with no `.part` left: 976 located passages, 107
  call-only passages (`unlocated/`) and 1,183 claims, from the pages and the fixtures.
- The ingest Mac uploads them to the private bucket. Nothing here touches R2, and nothing was
  written under `manual/ciq`.

**FUBO, PASSED AGAIN ON THE RE-SYNC ONTO #986** (2026-11-11, 08:27:59Z to 08:28:04Z, in the
merge's resolution).
- #993 rebuilt FUBO's page at $0, so the merge took main's page and ran the pass on it.
- It ran only after a dry run with no other conversion running located 8 of 8 rows.
- The spool wrote 0 files; all 16 were already held.
- The 8 rows are identical to PR 3's own, and the rest of the page, refresh entries included, is
  main's. One refresh entry is added: `driver-facts-pass`.

**WHY.**
- **The rule had to be held by a test, not by memory.** Before the pass, at `70fa224d`, it fired
  6,284 times on 58 of the 67 committed pages scanned (BOUNDARY). Every hit was a driver row
  publishing its own words:

  | Tree | Pages hit | Violations |
  |---|---|---|
  | `data/dossiers` | 25 | 2,881 |
  | `frontend/dossiers` | 25 | 2,881 |
  | `tests/fixtures` | 8 | 522 |

  By field: `verbatim` 2,277, `value` 2,277, `following_context` 1,730. The synthesis, `period`
  and `metric` halves fired 0. All 2,277 transcript rows (1,042 × 2 + 193) lacked the fact or the
  locator that the second test now requires. After the pass, both fire 0.
- **The fixtures are public files too.** A frozen page fixture held the same words a live page
  did, so the scan covers `tests/fixtures/`.
- **A full locator claims the passage is that file's words at that place.** The rehearsal's
  fixtures pass stopped, unwritten, at the UBER fixture of 2026-10-26:
  `EvidenceBytesDifferError` on the key that the live UBER page's passage had just taken. Both
  pages hold the same quote, at the same paragraph of the same file (the sha256 the live page
  was built from). The fixture's context is one comma apart from the context the file gives
  after the quote, so the two passages contended for one write-once key.
  - The fix: `prepare` gives a full locator only when the row's context is also the one that
    file gives after the quote, through the extractor's own derivation
    (`driver_extract._following_paragraph`). Otherwise the row's locator is call-only: its call
    and its quote's hash, no paragraph, no file hash.
  - Pinned by `test_a_context_from_another_export_of_the_call_gets_no_file_hash`, shown failing
    on the unfixed pass (`('ccc…', 1) == (None, None)`).
  - It moves 9 rows: BRBR 1, IT 1, WERN 5, and the fixtures VRRM (2026-08-18) 1 and UBER
    (2026-10-26) 1. Of these, 3 hold no context where the file has one, 5 hold a shorter one,
    and 1 differs by a comma.
  - **The cause of the 7 page rows is not recorded.** Their pages' input records are backfills
    that list no transcript, so whether their export changed cannot be read. No row's quote
    occurs twice in its call, so the derivation did not pick another occurrence.

**WHERE THE LOCATOR REACHES** (the pass's own output; BOUNDARY):

| | Files | Rows | Located | Call-only | Of which, context not the file's |
|---|---|---|---|---|---|
| Committed pages | 25 written (ORKA, TECX hold no transcript text) | 1,042 | 1,029 | 13 | 7 |
| Page fixtures | 8 | 193 | 57 | 136 | 2 |

- Each of the 1,235 rows was given its fact; no committed row had one before.
- Every other call-only row cites a call that is not in today's CIQ folder (measured per row):
  - the 6 page rows are NCNO's;
  - the fixtures' 134 are AORT 27, the two VITL fixtures 22 each, UBER 22, VRRM 16, V 10,
    EPAM 9 and SMPL 6.
- No row is call-only because its quote went unfound in a call that is on disk.
- A call-only row's words are still filed, under `unlocated/<sha256(call)>/`. Its claim is filed
  as every row's is.

**WHAT ELSE PR 1's §9 ASKED, AND WHERE IT LANDED.**
- `propose.py` and the digest read a stripped row as NOT ON THIS PAGE
  (`synthesis.STRIPPED_VALUE`), never as a value rebuilt from its figures. PR 3's first commit
  rebuilt it (`figures_text`), and Codex's round-1 P1 on #1006 showed that the figures are not
  the claim: TGT's "3/4" of sales read "approximately 3; 4" in the scenario template, and a
  qualitative row lost its fact to "stated, with no figure". `tests/test_driver_facts_page_pass.
  py::test_no_committed_stripped_row_is_rebuilt_in_the_scenario_template` failed on every
  committed page with a stripped row at `6fe06f1c`. The figures stay in `dossier.json`; a reader
  that needs the words reads them back from the store, as the confirmation does.
- **The figure trace** (`synthesis._values_by_ref`) runs only in a build, at `_validate`, on the
  build's own layer. That layer still holds the words, because they are spooled and stripped
  later, at `_write`. **So no production path traces a stripped row, and no committed point's
  flags move:** flags are sealed at build time, and the pass re-runs no check.
- **`metrics.segment_profit`** reads a row's `verbatim` and `following_context`. It never sees a
  stripped row:
  - every `PageContext` is built either from a page at a frozen git ref (the gold's `GOLD_REF`,
    the panel's `freeze_ref`), whose historical blob keeps its words;
  - or through `capture_child.pre_synthesis_mech`, which refuses a stripped page.
- **The replay** refuses a stripped page (PR 3's first commit), because it cannot rebuild the
  request the build sent. A panel frozen AFTER this pass would need the store to replay byte for
  byte. This gap is stated in PR 1's record and remains open.

**HOW VERIFIED.**
- **Rehearsal first,** into a throwaway spool in the session's scratchpad, never the Drive:
  the pages, then the fixtures, then the rule test, then the full offline suite. Then the tree
  was reverted.
  - The suite's two failures were fixed in the test commit: the panel test's AORT blob, and
    the drift pin of the moved `driver_pass.py`.
  - After the review fixes, a second rehearsal into a fresh throwaway spool was byte-identical
    to the first: all 108 written page files and all 2,266 spool records.
- **The real pass** ran from `0908e091` into the operator's spool. It is byte-identical to both
  rehearsals: the sha256 of each of the 108 written files and of each of the 2,266 spool
  records was compared, and the same 108 files changed, nothing else.
- **The rendered `.md` pages never printed a driver row's words.** The rule test scans JSON only,
  so this was searched separately:
  - 2,980 thirteen-word openings of the pre-pass quotes and contexts were searched for in the 56
    `.md` renders (pages and mirrors): 0 found, before the pass and after it;
  - the same search finds 201 of 203 synthesis bull-point openings in the same files, so it can
    find what the render prints;
  - the pass moved only each `.md`'s refresh stamp;
  - the web page reads the mirrored JSON, which the test does scan.
- **The CI-skip class.** These tests need a row's real quote, read from its call on disk. Each
  skips in CI, naming the missing export, and ran locally against the operator's CIQ folder, read
  in place:
  - `tests/test_driver_facts.py::test_every_committed_figure_with_a_change_refuses_the_opposite_claim`
  - `tests/test_driver_facts.py::test_every_committed_rows_figures_are_its_quotes`
  - `tests/test_model_input_checks.py::test_every_committed_transcript_row_passes_and_a_rescaled_one_does_not`
  - `tests/test_driver_evidence.py::test_every_committed_rows_locator_finds_its_passage_on_disk`

  These are the four the gate reports as one skip group at `tests/stripped_pages.py:70`, and no
  other test moved into a skip.
- **Two tests that main brought in stood a live page in for a frozen one.**
  `tests/test_evals_run_builds.py` (#958) and `tests/test_evals_independence.py` (#978) feed
  the replay the committed NFLX page, and on the passed page their 22 capturing tests failed: the
  replay refuses a page whose transcript rows carry no words. Each fixture now reads the page
  through `stripped_pages.replayable`, which is the identity on a page that still holds its
  words.
  - The builds test passes on the tree before the pass and after it (16 of 16).
  - The independence test passes on the passed tree (32 of 32 across the two files).
  - Production reads every panel page at its `freeze_ref`, so it is unaffected.
- **The confirmation's requests, on every committed page** ($0, 2026-11-11, head `e7cc0b2a`
  against base `65758333`; PR #1006 Section D part 6). `confirm` was run with a capturing client
  that records each of its ten requests and answers with a scripted draw. CIQ was read in place,
  and every store access was a read: the operator's spool held 2,266 files before and after.
  - The re-filled page's requests are byte-identical to those on the same page before its words
    came off (base's page through `driver_pass.prepare`) on **27 of 27** pages. V was measured
    on a re-run alone, after its Q4 2026 call did not read on four tries while another session's
    conversion ran.
  - Without the read-back, the request differs on **25 of 25** pages with transcript rows. ORKA
    and TECX hold none.
  - The identity check was verified on 9 pages. On the other 18 it was bypassed, and labelled
    so: their input record is a backfill, so `confirm` refuses them before any draw ("cannot
    identify the transcripts"), with or without this PR.
- **Section D part 2 at the new base** (2026-11-11, 11:02–11:21Z): `prespend.mechanical_build`
  ran at base `65758333` and head `e7cc0b2a`. Both read one read-only copy of a store holding bars
  for every page (sha256 `4e77757f5cb3…`), each build on a fresh clone of it. **27 of 27** pages
  built on both sides, and only `extraction_version` moves.
- **The gate** (`bin/commit`: ruff, `mypy --strict`, `pytest -m "not network" -rs`) was green
  at every commit of this PR except the mechanical re-sync `76c21609` (rule A). That one was
  checked as its commit message lists, and the `bin/commit` after it ran the full suite on top of
  it. The re-sync onto #986 (`cb8f8a7f`) resolved a semantic conflict (WHAT item 9), so it went
  through `bin/commit` itself.
  The last commit only adds this PR's number and the two results above to this record. It was
  committed plainly after the records and shared-file tests ran green, since it changes no code.

**THE SCHEMA EDIT, DISCLOSED.** `vinci/dossier/schemas.py` is a decision-line file. Its hook
(`.claude/hooks/decision_path_guard.py`) asks the operator before an Edit or a Write, once per
file per session. In this session it asked on 2026-11-09 (PR 1), and the edit went through.
- PR 3's change to the file (2026-11-10: the optional text fields, `value_sha256`, the strip
  rule) was made by a script under that approval, so no second prompt appeared.
- The review round moved one doc comment in it.
- The change adds no verdict field and touches no decision field. `Synthesis` is untouched.

**BOUNDARY.**
- **Firing counts:** `tests/test_public_transcript_text.py`'s two corpus checks (`violations()`;
  fact + locator) run over every `*.json` with a `mechanical` key, under `data/dossiers`,
  `frontend/dossiers` and `tests/fixtures`. Read from the blobs at `70fa224d` (`#953` merged into
  this branch) by a one-off script, not a test: 67 pages, 6,284 violations. After the pass, on
  the committed tree at `c3fedcc7` and every commit after it: 0 and 0.
- **The pass's counts:** `vinci driver-facts-pass`'s own per-page output.
  - `--ciq-root` was the operator's CIQ folder, read only, at its state on 2026-11-10.
  - Population: every `data/dossiers/*/dossier.json` (27; 25 with transcript text), plus the 8
    files under `tests/fixtures/` that hold transcript rows.
  - Unit: transcript driver rows (`tier == "llm-fenced"` with text).
- **Spool files:** one file per record (passage or claim), counted in the folder after the real
  pass.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The words are gone from git, not from history.** Every committed byte before this PR is
  public and stays so (the 2026-10-22 decision). The rule binds the tree from here on.
- **The model's value phrase is private now.** It carries the comparison basis
  ("year-over-year") that `figures` does not. A reader who needs it follows the locator. The loss
  is stated in PR 1's §5.
- **A test that needs the words does not run in CI.** It runs only where the CIQ exports are on
  disk. Falsifier: a change that breaks the up/down check passes CI. The fact-level pins, which
  do run in CI, catch the same class on the committed figures, but not against the sentence.
- **9 rows lose a paragraph pointer** they could have had. Their words are filed, and the
  call-only key is exact for what they hold.
- **Owed after merge:** the ingest Mac's upload of the spool (operator). RG-D8's clause-binding
  half is still not built (strict xfail), so RG-D8 stays `in progress` after this PR.
- **The bookkeeping is the coordinator's.** STATE row 60 and the fix log are applied in its
  batched bookkeeping PR (operator, 2026-11-10), from this PR's "Bookkeeping for the
  coordinator" section, so this PR edits neither.
