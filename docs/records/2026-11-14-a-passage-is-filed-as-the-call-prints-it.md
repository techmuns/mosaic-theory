---
id:
status: shipped
date: 2026-11-14
prs: [1077]
supersedes:
superseded-by:
---

# A transcript passage is filed as the call prints it, and a re-draw in another case or spacing is the passage the spool already holds: GOOGL's paid build was refused after every model call (run `8d2e72e8`, $3.84); the first bytes now stand, each such record is named on the page, and 0 of the spool's 2,757 files collide ($0)

**WHAT.**
- **The defect.** GOOGL's paid build wrote no page. It was run `8d2e72e8` on main `2bd2facf`, 2026-11-14 18:16:05Z → 18:25:59Z: 7 calls, 0 failed, $3.84. The spool refused it with `EvidenceBytesDifferError` on `driver-evidence/v1/cab0759d…/8/62fca102….json`, a passage of GOOGL's Q2 2026 call (paragraph 8), filed 2026-11-10.
  - The key hashes the quote FOLDED: whitespace collapsed and lower-cased (`quote_key`).
  - The record held the model's raw string (`extract_transcript_drivers`: `verbatim=quote`).
  - So a draw quoting a held passage with one letter's case or one space different shared its key and not its bytes. The write-once spool refuses that, after every paid call.
- **The mechanism, shown at $0** (no transcript word printed):
  - Given the stored quote and the call on disk, today's code rebuilds the stored record byte for byte: paragraph, speaker and context. The stored quote is the call's own text.
  - Re-drawing it exactly is a no-op. Flipping one letter's case, or turning one space into a line break, raises this error.
  - The failing draw's quote was never saved, because the build stops before it writes. So the variant is shown by construction, not observed.
- **The rulings.**
  - The operator, relayed 2026-11-14: "Fix, then one build at $5.78 (Recommended)". The option reads: a $0 evidence fix, a $0 re-check, then ONE paid GOOGL build capped at $5.78, #1041's rule on the last cost ($3.84 × 1.255 × 1.2).
  - The coordinator, on review round 1 (2026-11-14): the filing date "must come from a stable source or read UNKNOWN, never mtime, and no new field may be added to existing records". This supersedes the brief's "the filed-on date".
  - The coordinator chose (b) of three after the census below: file new passages as the call prints them, AND hold a passage that differs only in the key's fold as the same passage. Filing the call's words alone would leave the spool's 3 capital-letter records colliding on any re-draw, and the spool and bucket are write-once, so nothing can re-file them.
- **The rule.**
  1. `driver_extract.as_the_call_prints_it`: a located row files the CALL'S words at its quote's folded match. That is the same first occurrence `_paragraph_and_speaker` counts from, with its case kept and whitespace runs as one space. A span that does not fold back to the quote falls back to the model's string; its key is the same either way.
  2. `EvidenceSpool.file` (`put` delegates to it): a held passage record whose quote differs from the new one ONLY under the key's own fold is the same passage. The fold is `quote_key`, imported, never re-implemented; every other byte must match. The bytes filed first stand, untouched. A changed speaker, context, call name or word still refuses.
  3. `spool_dossier` names every such record on the page: one QA flag per record, never per row (`refolded_flag`), with its key and no transcript word. The day the record was filed reads UNKNOWN (review round 1). They are also listed in `SpoolReport.refolded` and counted in `already`.
  4. `upload_spool` holds the same rule against the bucket. A cleared spool ("the operator keeps or clears the folder") can file a passage afresh in the call's words while the bucket holds the model's case of it. The bucket's first bytes then stand, and the key is counted in `UploadReport.refolded`; anything else that differs still raises.
  5. `driver_evidence.py` now writes a page field, so it leaves `NOT_EXTRACTION` and is pinned. New vintage: `2026-11-14.a-passage-is-filed-as-the-call-prints-it`.

**WHY.** A write-once store keyed on a folded quote, holding an unfolded quote, refuses a page at random after its spend. On 2026-11-14 the eight committed rebuilds re-met 183 of their 381 located passages in a record filed before group 1, all byte-identical; GOOGL's was the first mismatch. Its build cost $3.84 and produced nothing.

**HOW VERIFIED.**
- **The census, read only** (`spool_canon_check.py`, kept outside the repo): every file in the operator's spool was read, and each passage was rebuilt under the new rule from its call on disk, matched by sha256, under that file's current name. The spool's names and mtimes are identical before and after.

| spool files, 2026-11-14 | count |
|---|---|
| all | 2,757 |
| claim records (no call text; the rule does not touch them) | 1,472 |
| passages reproduced byte for byte under the new rule | 1,098 |
| passages that differ, case only (one capital letter at the quote's start, where the call has lower case) | 3: UBER Q3 2026 call p69 (filed 2026-11-10), LLY Q3 2026 call p150 and LLY Q2 2026 call p99 (filed 2026-11-14 by LLY's rebuild) |
| passages whose call file is not on disk | 77 |
| call-only (unlocated) passages | 107 |

  - The 3 are held as filed. A re-draw of any of them is now the same passage, named on its page.
  - The 77 and the 107 were not checked. A key naming a call not on disk can only be re-drawn if that file returns. A fresh build never files a call-only record, because a row that cites a call always carries its locator.
- **Fail first** (`tests/test_evidence_same_passage.py`, 17 tests: 12 at the fix's first commit `d6a9d62e`, 4 added by review round 0, 1 by round 1). The fixture is a cut of GOOGL's real call, at most 10 consecutive words, plus the stored record's locator and sha256. On main's code, 12 fail locally (11 in the cross-setup run, where the real-call pin skips):
  - 9 on behaviour:
    - the row files the model's case and spacing;
    - the spool raises `EvidenceBytesDifferError`;
    - the bucket raises `RemoteBytesDifferError`;
    - the real call's re-drawn record hashes to `2769effe…`, not the spool's `aac26cb3…`;
    - the page is refused, so a file's time cannot even be tested there.
  - 3 because main lacks `as_the_call_prints_it`, `EvidenceSpool.file` and `SpoolReport.refolded`.
  - The 5 negative pins pass on both: a changed speaker, context or call name is refused under the key; one changed word is refused; a changed paragraph keys elsewhere; another record is refused at the bucket.
- **Review round 0** (`/code-review high --fix`). Three fixes, each pinned by a test red on `d6a9d62e`:
  - one flag per record, not per row (one passage backs several rows; 63 of 810 keys on the committed pages);
  - a lower case longer than its letter ("İ") before a quote no longer shifts the cut;
  - the upload rule above, with a negative pin: another context under the key is still refused.
- **The real call end to end** (the licensed call on disk, `VINCI_CIQ_ROOT`): the quote is the paragraph's words at the fixture's span, checked against its hash. A case flip and a spacing flip each now file the record whose sha256 the spool holds (`aac26cb3…`). In CI the pin skips, because no call is on disk.
- **No test reads or writes the operator's spool;** a pytest folder plays it.
- **The gate** (`bin/commit`, which commits only on exit 0, in a clean worktree with no git-ignored data):
  - at `cd5ace48`, the PR's code head: ruff clean; `mypy --strict` clean on 219 files; 11,457 passed, 670 skipped, 9 xfailed, 0 failed; the mirror in sync;
  - at `4b5efa2e` and `cdd25154`: 11,457 passed, 0 failed; at `b51703b6`: 11,456 passed, 0 failed; at `d6a9d62e`: 11,454 passed, 0 failed.
- **The local 12-word transcript guard** at `cd5ace48` (the operator's 66 current calls; the archive of replaced exports not read): 3,199 files scanned; 73 runs shared with a call, 60 excused by SEC filings and 13 by Key Developments exports; 0 unexcused, none in this change's files.
  - Two earlier runs at that head left 25 and then 4 calls unread, because LibreOffice produced no text; the third read all 66.
  - The guard's unchanged Markdown-link pin failed in that third run and passes alone. It reads a window of the calls on disk, and the same run at `b51703b6` passed it.
- **The cross-setup section** (`python -m vinci.impact run`, head `cd5ace48`, base `68e8c474`, patch-id `d0623d72`, the 11-11 store):
  - 13 tests fail at base and pass at head: 11 of the new file's, and the 2 extraction-version pins. The real-call pin skips there.
  - Of 25 pages built at $0, 0 move. PARR is not built: its mislabelled quarterly export.
  - 0 of 25 synthesis requests differ, and 0 of 6 frozen-panel requests, so no row-53 panel check is owed.
  - 0 committed pages re-render differently.

**BOUNDARY.**
- **Census:** the operator's spool as on 2026-11-14 after GOOGL's refused build (2,757 files, 4 of them written by that build); call files under the operator's `manual/ciq` on disk 2026-11-14, matched by sha256; code at main `68e8c474` (its `vinci/` is `2bd2facf`'s).
- **Re-meets:** today's eight committed rebuilds (NCNO, SMPL, TJX, EPAM, LLY, VITL, IT, WERN): located passages on each committed page, against the spool's file list before group 1.
- **Code:** branch `claude/evidence-files-the-calls-text`, cut from main `68e8c474`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The 3 records keep the model's capital letter privately.** No public fact moves: a page carries the fact and the locator, and the quote's hash is the fold's, the same either way.
- **The $0 precheck cannot see this class of refusal.** The spool is written after the paid draws, and the $0 check draws no transcript row, so it could not have stopped GOOGL's spend. Falsifier: another `EvidenceBytesDifferError` after spend. Under this rule that means something other than the fold differed.
- **A flag cannot name the day its record was filed, so the day reads UNKNOWN.**
  - The record carries no date, and adding a field would change every held record's bytes.
  - A file's time is no date of filing: a copy, a restore or a sync resets it (Codex P2, round 1).
  - Round 0 printed "already filed on <day>" from the file's time, and round 1's first fix (`cdd25154`) relabelled it "its spool file dated <day>". The coordinator ruled the day must come from a stable source or read UNKNOWN. No stable source holds it.
  - Pinned by `test_a_files_time_never_reaches_the_flag_and_the_filing_day_reads_unknown`: moving the held file's time changes nothing on the page.
- **The pre-existing match in `_paragraph_and_speaker` keeps the "İ" shift** that `as_the_call_prints_it` no longer has. Making them one shared helper is a refactor of code outside this change (review round 0, deferred). On the census, every one of the 1,098 located passages re-derives its paragraph byte for byte.
- **A known edge with no observed case: a word-final capital sigma.** `as_the_call_prints_it` lower-cases the call one character at a time (Σ → σ), while the key's `_norm` lower-cases the whole string (a Σ that ends a word → ς). So a quote whose matched words hold a capital Σ ending a word returns None, and the row files the model's string under the same key: never a wrong span. None of the 66 calls on disk holds a capital Σ (read 2026-11-14). The independent review of `cd5ace48` named it.
- **The equivalence is the key's fold, nothing wider.** A quote differing in punctuation, or in where it ends, is another passage with another key, and never a collision.
- **The run line `8d2e72e8` ($3.84, refused)** is not in this PR. It is committed with GOOGL's artifact PR, beside the new build's, because the cost-and-outcome series counts refusals.
