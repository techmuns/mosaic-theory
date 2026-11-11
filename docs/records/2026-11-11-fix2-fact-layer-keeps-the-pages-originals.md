---
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, RFL-D3 (order 7): the fact layer keeps every response it reads, write-once by sha256, and the pages snapshot is re-ingested with all its originals and acceptance times. 28 companies; 27 of 27 page-cuts rebuild from the originals in R2

**WHAT.** The operator ruled 2026-11-11, verbatim: *"Keep the pages' originals (Recommended)"*. The
coordinator took option (A), re-ingesting the pages snapshot, because the committed one's
originals were not all recoverable.

- **The originals** (`vinci/facts/originals.py`).
  - **What is kept.** Every response the PAGES ingest reads: each company's companyfacts, and
    each SEC submissions page its acceptance times come from. The screen's ingest keeps none: the
    operator's ruling covers the pages, not the screen's universe (pinned by a test).
  - **How.** Gzipped (`mtime=0`) and named by the sha256 of the stored bytes,
    `originals/sec/<sha256>.json.gz`. The same body is a no-op; other bytes under a name are
    refused. Locally that is `write_object`; in R2, `put_new`'s `If-None-Match: *`.
  - **The manifest** records each original beside what it was read for: the response's own
    sha256, its URL and its `fetched_at`.
  - **Reading back.** `read_original` checks both hashes before it returns the text.
  - **Where.** Never in git: the originals sit under the git-ignored `data/facts/local` (or
    `$VINCI_FACTS_STORE`), and `upload` sends them to R2 beside the snapshot's objects.
    `upload_refusal` (RFL-D6) admits the EDGAR writer's `originals/sec/` namespace and no other.
- **The reader** (`FactStore.original`) rebuilds a company's response from its original, from the
  local root or from R2.
- **Parity** reads the snapshot's own original as its reference where one was kept, so a
  refetched cache no longer stops the comparison (#992 reported such a page CHANGED).
- **`verify`** reads every original back and checks it against both hashes. `verify_manifest`
  checks each original's name and that each company's original is the response it read.
- **The new pages snapshot** `edgar-e94e051d94ce1985` is schema v3: 28 companies, 525,552 rows,
  386 data objects, and an acceptance time for each of its 1,569 filings.
  - Of its 442 objects, 314 are shared by content with `edgar-4f3207f4da9fb71a`, so 128 are new
    in git.
  - Its 81 originals are 6,423,509 bytes stored (87,532,038 as fetched).
  - `current.json` moved forward. The old snapshot's manifest and objects stay, still
    addressable; nothing in git or R2 was deleted or overwritten.
- **Tests adjusted to the new current snapshot.**
  - The contract test now names v3's filings objects.
  - Three upload tests name the hold-era snapshot they are about, because CI has no originals.
  - One ingest premise reads "6 in listed".

**WHY.** The store kept derived rows, the response's URL, `fetched_at` and sha256, but not the
bytes, which a cache refetch overwrites. Eleven days after the committed pages snapshot was
ingested, only 22 of its 26 responses existed anywhere on this machine (by sha256, across 52 local
caches); AMZN's, GOOGL's, TECX's and WLK's were gone.

**HOW VERIFIED.**
- **Fail-first.** `tests/test_facts_originals.py`, 11 tests.
  - On main `bfd6a41a` the module does not exist, and all of them fail at collection.
  - The pages-only test also failed on this branch with the scope rule removed.
  - Here they pass.
  - All 181 fact-layer tests pass, with the local originals present and with them moved aside,
    as CI has none.
- **Live SEC fetches.** 16, all through the paced client and all strictly needed by the ingest:
  - MNST's companyfacts, its recent submissions page and its older page;
  - 13 older submissions pages that 11 page companies' recent pages list.
  LLY's companyfacts was already cached by then. Nothing else was fetched.
- **The ingest.**
  - **Scope.** All 28 scope names were read, none unread: the 27 pages' companies and MNST.
  - **Acceptance.** 1,569 of 1,569 accessions carry an acceptance time; 0 documents were unread.
  - **Verify.** `python -m vinci.facts verify`: every object sealed and its rows hashing to its
    name. 81 originals read back against both hashes, 0 problems.
- **The upload** (the first real one of originals).
  - 523 objects named: 442 snapshot objects and 81 originals, 13,820,431 bytes.
  - 209 written (8,495,938 bytes): the 128 new snapshot objects and the 81 originals. 314 were
    already there with the same bytes.
  - 523 of 523 read back against their sha256, 0 problems.
  - The bucket after it: 22,768 keys, every one named by a committed manifest. 0 are named by
    none, 0 are named and absent, and 0 have another size.
- **Verify from R2 into an empty cache.** 523 of 523 fetched and hashed, the 81 originals checked
  against both hashes, 0 problems.
- **Parity against the 27 committed pages, at each page's own price date.**
  - **From the local originals:** 27 of 27 zero-diff.
  - **From R2, with no SEC cache at all and an empty object cache:** 27 of 27 zero-diff. Each
    reference response was rebuilt from its original, 27 fetched.
- **A page fact rebuilt from its original in R2.** NFLX's FCF sign reads FY2025 operating cash
  flow of 10,149,273,000 and capex of 688,220,000 from 10-K 0001065280-26-000034. Its original
  states those values, and the store serves them (accepted 2026-01-23 21:06:33 UTC).
- **The old pages snapshot against the new**, each read at every committed page's price date on
  the day-level cut. BURL and MCK were not in the old one. Over the 25 pages in both:
  - **Old only:** 0 rows.
  - **Frame moved:** 2,385 rows. Each is the same row with only SEC's `frame` moved (FL-D12).
  - **New only:** 4,937 rows.
    - 4,061 were filed after the old copy's fetch day and by the page's date. The old snapshot
      was stale at 16 of the pages' own price dates (RFL-D1's case).
    - 531 were filed on the old copy's fetch day, 2026-10-27, and accepted after its fetch
      (10:08-10:09 UTC), by the new snapshot's acceptance times.
    - **345 are one filing: V's 10-Q 0001403161-26-000104, filed 2026-07-29.** The copy the old
      snapshot ingested (stated `fetched_at` 2026-10-27T10:09:07Z, its sha256 matching the
      manifest, recovered from a local cache) carries no V filing after 2026-07-01. The rows
      are explained: that copy lacked the filing. **Why it lacked a filing three months older
      than its stated fetch is not determined**: whether SEC served it so, or the cache entry's
      text predates its stamp.

**BOUNDARY.**
- **Snapshots.** `edgar-4f3207f4da9fb71a` (committed at `bfd6a41a`) against
  `edgar-e94e051d94ce1985` (ingested 2026-11-11 from the primary checkout's SEC cache).
- **Pages.** The 27 `data/dossiers/*/dossier.json` at `bfd6a41a`, each cut at its own price date
  (`parity.page_cut`).
- **R2.** The private bucket the four `R2_*` variables name, on 2026-11-11, read in full by the
  upload's audit.
- **Old-copy recovery.** The 52 local SEC cache directories found under this machine's worktrees
  and session scratchpads.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Every pages re-ingest adds its new originals to R2, and none is deleted.** Today that is
  6.4 MB. The screen's universe keeps no originals (operator: pages only).
- **A local original lives outside git.** On a machine that did not ingest, it is read from R2,
  and without R2 the rebuild raises. That is loud, by design.
- **V's missing 10-Q** is reported, not resolved. Falsifier: a fresh fetch of V's companyfacts
  that, cut at 2026-10-27, lacks the 10-Q, which would mean SEC served the old response so.
- **Nothing reads the store yet** (STATE §5.0 row 44). No page, screen or synthesis request moves.
