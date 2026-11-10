---
status: open
date: 2026-11-10
prs: [951]
supersedes:
superseded-by:
---

# Publish the fact, not the quote, PR 2 of 3 (RG-D19): the private evidence store is a spool the operator creates and the ingest Mac uploads — one record per passage, never per row, and no folder is ever made by code

**WHAT.** This is the write path for the transcript evidence that PR 3 will take off the public
pages. It is built to the operator's ruling of 2026-11-10 (option 1; "yes to all", relayed by
the coordinator):
- the assembling Mac writes each record into a spool folder on the shared Drive, beside
  `manual/ciq`;
- the ingest Mac, the only one holding a read/write R2 token, uploads the spool to the private
  bucket.

Design record: `docs/records/2026-11-10-driver-facts-not-quotes.md`, §6 and §10.

What ships, all in `vinci/dossier/driver_evidence.py` plus one call site in `assemble._write`:
- **`EvidenceSpool`, named by `$VINCI_EVIDENCE_SPOOL`.** It NEVER creates its folder (the
  coordinator's rule, 2026-11-10). It refuses loud, naming the variable, when the variable is
  unset or the folder does not exist; the operator creates the folder by hand. It also refuses
  two places outright:
  - a folder inside this repository, because its files would be committed;
  - a folder under `manual/ciq`, the licensed exports, which nothing here writes to, moves or
    deletes.
- **It writes files only, flat.** A key's "/" is "__" in the file name, so not one sub-folder is
  made. Each write goes to an exclusive `.part` file first, then is renamed into place.
- **One record per PASSAGE.** A record holds the quote, the paragraph after it and the locator, and
  nothing of the page that cites it. Its key is
  `driver-evidence/v1/<transcript_sha256>/<paragraph>/<quote_sha256>.json`, or
  `…/unlocated/<sha256 of the call's file name>/…` for a call-only locator.
  - The same record twice is a no-op. Different bytes under one key are refused, in the spool
    and in the bucket (`R2Client.put_new`, `If-None-Match: *`).
- **Every read and every upload re-checks the record:** the quote must hash to the locator's
  `quote_sha256`, the record must sit under its own key, and it must be in its one
  serialisation.
- **`upload_spool(spool, client)`** is the ingest Mac's command:
  `python -m vinci.dossier.driver_evidence upload [--spool PATH]`.
  - It re-checks each record, PUTs it with `put_new` and reads it back.
  - It leaves every other file in the folder alone and reports it, a Drive conflict copy
    ("… 2.json") included.
  - It never deletes anything.
- **`assemble._write` spools a page's transcript evidence BEFORE it writes the page,** so a spool
  that is named but unusable stops the build first. `assemble_one` checks the spool once more
  as its first step, so that refusal comes before any paid phase, never after it (#915's lesson).
  A transcript row with no locator or no quote is named on stderr, never dropped silently.
- **"Inside this repository" means every working tree of it:** the running checkout, the main
  checkout and each linked worktree, read through git's common dir, compared by file identity
  (a case variant of the path on a case-insensitive volume is still inside).
- **A `.part` file already in the spool** (a build that died mid-write, or one writing now) is
  refused by name and left in place.
  - Until PR 3 strips the quote from the page, an unset spool is a loud stderr notice, not a stop.
    PR 3 makes it required, because the spool then holds the quote's only copy outside the
    licensed call.
- **`tests/conftest.py` unsets `$VINCI_EVIDENCE_SPOOL` for every test,** so a shell that has it
  set can never send a test's fixture rows to the operator's folder.

**WHY ONE RECORD PER PASSAGE, NOT PER ROW (found by the corpus test before it shipped).** The
first cut keyed a per-row record (the quote, its context and the model's stated value) by the
passage. The end-to-end pin over the committed pages refused it at once: one quote backs several
rows.

Measured over the 28 committed pages, 881 transcript rows, main `6fbbb4a2`:
- 881 transcript rows give **810 distinct (call, quote) keys**.
- **63 keys** back more than one row. In all 63, the quote and its context are byte-identical.
- In **62** of them, the model's stated value differs. ROST's two AUR rows are one example.

The stated value is a CLAIM, which the fact check read against the quote, and its words are the
quote's own. So it is not evidence, and the record does not hold it. Nor does the record hold the
extraction version, so a rebuild meets its own record and writes nothing.

**HOW VERIFIED.** `tests/test_driver_evidence.py`: 14 tests, all against local stand-ins.
- **The spool** is a pytest temporary folder.
- **R2** is `tests.test_facts_remote.FakeBucket`, the fact store's S3 stand-in, which keeps S3's
  conditional-write and Content-MD5 rules.
- **In the main checkout or a sibling worktree** (a fake git layout in the temporary folder):
  refused.
- **A leftover `.part`:** refused by name and kept.
- **A bad spool at `assemble_one`:** refused before the finalist is read.
- **Unset, missing, in the repo, under `manual/ciq`:** each is refused by name, and a missing
  folder is still absent afterwards.
- **A record** is written flat and once. A different passage under its key is refused, and no
  `.part` file is left behind.
- **A tampered quote** is refused at write and at read.
- **The upload:**
  - it writes each record once and reads it back;
  - a second run writes nothing;
  - a conflict-copy file is skipped, reported and kept;
  - a read-only token refuses loud and writes nothing.
- **End to end, on every committed page.** Each transcript row is given PR 3's call-only locator,
  then spooled and read back. The quote and context come back whole for every row, and the spool
  holds exactly one file per distinct key (810).
- **Assembly, on BRBR's committed page:**
  - unset: the page is written, with the notice;
  - set to a folder not yet created: the build stops before the page, and the folder is not
    made;
  - created: the evidence lands, then the page.

**BOUNDARY.**
- **Collision counts** are over the 28 committed `data/dossiers/*/dossier.json` at main
  `6fbbb4a2`. They cover rows with `tier == "llm-fenced"` whose `source_ref` names a call (881).
  The key is the call's file name plus `driver_extract.quote_key`.
- **Nothing was written to the Drive or to R2.** The operator has not created the folder, and its
  name is the coordinator's to give.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The evidence reaches R2 only at the next upload** on the ingest Mac. Until then it is on the
  Drive, which already holds the licensed exports.
- **A change to the paragraph rule or the speaker rule is refused, not absorbed.** Either rule
  changing for an existing key makes a different record, which the store refuses. Falsifier: a
  build refused with `EvidenceBytesDifferError`. The remedy is a new key version (`v2`), on the
  record.
- **The rename is not atomic against a second writer.** `os.replace` follows an existence check,
  so two writers racing on one key could both pass it, and the later rename silently replaces the
  earlier record. No later read can tell: `get` checks a record's integrity, not which writer
  came first.
  - The bytes are the same unless the two writers ran different paragraph or speaker rules.
  - A no-overwrite rename (`os.link`) would close the race, but may not be supported on the
    Drive's file system.
  - Accepted, with one assembling machine at a time. Falsifier: two machines assembling one name
    at once on different extraction versions.
- **Pages written outside `assemble._write` are not spooled.** `refresh.py`'s `write_dossier` is
  one. That is harmless while the page still carries its quote; PR 3, which strips it, must route
  every page write through the spool or refuse a stripped page that was not spooled.
- **The record does not hold the ticker.** It is the passage's, not the page's, so a second share
  class citing the same call meets the first one's record and writes nothing
  (`test_two_listings_citing_one_call_share_its_record`).
- **Cost:** $0. No model call, no page rebuilt, no Drive write, no R2 request.
