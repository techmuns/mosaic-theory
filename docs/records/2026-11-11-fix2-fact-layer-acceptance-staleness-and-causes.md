---
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, the fact layer (RFL-D1, order 5; RFL-D7 to D10, order 6; RFL-D2, D4 to D6, order 7): a cut stands at the close and reads SEC's acceptance time, a read past its copy's fetch is refused, the reader checks what the manifest seals, and every failure names its cause. RFL-D3 is the operator's call. The store holds what it held; nothing reads it yet

**WHAT.** All in `vinci/facts`. STATE §5.0 row 44 stands: nothing reads the store, and both
committed snapshots are unchanged.

- **RFL-D2, the acceptance time** (schema v3, `FILING_COLUMNS`, `edgar_ingest.acceptance_rows`,
  `reader._visible`).
  - **The defect.** The cut was `filed_date <= as_of`, and companyfacts dates a filing to the day.
    A replay priced at a day's close saw every filing of that day, whenever SEC accepted it.
  - **What the ingest stores now.** One FILINGS object per entity: each accession its data rows
    carry, with SEC's `acceptanceDateTime`. It is read from the cached submissions documents,
    the recent page and every older page it lists, and never fetched. The clock is UTC, as
    written. An accession gets no time, and is named in the manifest's `acceptance` entry with
    why, when no document read lists it, when its page is not cached, or when SEC's filing date
    is not the rows' `filed`.
  - **The cut.** A read of a DATE stands at its 16:00 New York close; a read of a zone-aware
    DATETIME stands at that instant (`cut_instant`). A row with an acceptance time is in the cut
    from that time. A row without one is in when filed on an earlier day and out when filed on a
    later day. Filed ON the cut's day, it cannot be placed, and the key raises
    `FactCutUndeterminedError` rather than guessing which side of the close it fell.
  - **`basis="filed"`** keeps the old day-level cut, which the page's reader (`facts_as_of`)
    still makes. Parity and the screen replay use it, because they compare against that reader.
  - **Versions.** The contract is versioned, so schema v2 snapshots, both committed ones
    included, are still read, and verified against v2's contract. They state no acceptance time,
    so a key filed on the cut's own day raises.
- **RFL-D1, staleness** (`FactStore.is_stale`, `FactStaleError`, `stale_ok`).
  - **The defect.** A read whose cut is past the moment the entity's copy was fetched served the
    copy's latest value as the value as of the cut.
  - **The fix.** Such a read now raises, naming the fetch. With `stale_ok=True` every fact
    carries `fetched_at` and `stale=True`.
  - **Where the line falls.** For the day-level cut the copy must be fetched after its day ends
    in New York; for the acceptance cut, after the cut itself.
- **RFL-D4, the reader checks what the manifest seals** (`FactStore.__init__`, `_path`). On open it
  recomputes the snapshot id from the manifest's content. On the first read of each object it
  hashes the bytes against the entry, and the rows against the object's content-addressed name:
  data, order and filings objects alike, from disk or from R2.
- **RFL-D5, not held is its own error** (`FactNotHeldError`; `FrameResult.not_held`). "The snapshot
  does not hold the entity" (it was not ingested) is no longer `FactUnknownError`, "nothing filed".
- **RFL-D6, the upload checks the source** (`remote.upload_refusal`).
  - **The check.** A snapshot is uploaded only for a source this code writes (`UPLOADABLE`:
    `edgar` and its one writer), made by that writer, with every object under that source.
  - **When.** Before any request: `upload_snapshot` raises, and `python -m vinci.facts upload`
    prints the cause before it opens the client.
  - **Why not CIQ.** A `ciq` snapshot has no writer here. Nothing shows its rows carry what the
    licence ruling of 2026-11-04 requires of a published value, and the ADR's slice 4 keeps CIQ
    outputs local.
- **RFL-D7, a changed response is said** (`parity.compare_page`). A page whose cached response is
  not, by sha256, the one the snapshot ingested is reported CHANGED, with both copies' fetch times,
  and compared no further, as the screen replay already did. Every page's fetch time is now the
  snapshot's copy's, never the cache's.
- **RFL-D8, duplicates held once are named** (`parity.held_once`). Later exact duplicates are
  dropped from the reference as the ingest drops them. They are counted beside the snapshot's own
  count, and a page is zero-diff only when the second covers the first.
- **RFL-D9, nothing is written before every response is checked** (`__main__._shape_problems`).
  One row of an unknown shape stopped the ingest after earlier companies' objects were written,
  and no manifest named them. Every cached response, and its submissions documents, is now read
  first. One the ingest cannot store faithfully stops the run before any object is written, and
  every such entity is named. Objects are content-addressed and may be another snapshot's, so none
  is ever deleted.
- **RFL-D10, an unread response names its cause** (`edgar_ingest.unread_reason`). It says "has no
  'facts' key (its keys: …)", "'facts' holds no fact row", or "N fact rows all lack a filed date".
  Before, all three were "no row with a filed date".
- **Review round 0** (`/code-review high --fix`, 9 findings, 7 fixed, each behind a test that
  failed first where it changes behaviour):
  - the response-for-its-own-CIK check moved into the check pass, so it too refuses before any
    write;
  - only the filings the data rows carry are parsed strictly, so an odd time on a Form 4 the
    store never reads stops nothing;
  - a row the cut cannot place decides its key only on its own day, so a later day's filing in
    an evening cut wins;
  - one definition of "rows hash to the name" (`store.rows_match_name`) serves the reader and
    `verify`;
  - the summary line counts the stated acceptance times;
  - a document is parsed once;
  - two unused members were removed.
- **RFL-D3, originals: not built.** TeamNostra's done-when: "Keeping originals is your call;
  TeamNostra's G0 builds its own original store". It is a decision for the operator. The
  numbers: the 25 cached page responses here are 67.9 MB raw and 4.8 MB gzipped. The screen's 524
  cached here are 1,095.7 MB raw and 76.5 MB gzipped, about 295 MB gzipped for all 1,692 scaled by
  rows.

**WHY.** Order 7's done-when: "Before the fact layer serves a page or a replay: acceptance time
stored and used in cuts; the reader verifies the snapshot id and rows; the two errors are
distinct." Order 5's: "a stale fact-layer read" as a passing test. Order 6's: "each failure states
its real cause".

**HOW VERIFIED.**
- **RFL-D2, on real data, at main `946943ec`.**
  - **The leak.** Of the 175,193 latest facts (as of 2026-11-11) of the committed pages snapshot
    whose accession is on a cached submissions recent page (26 companies), 84,466 were accepted
    after their own filing day's 16:00 New York close. Every one was served to a replay at that
    close. TGT's 10-K 0000027419-17-000008 was filed 2017-03-08 and accepted 16:22 EST, and
    `get(as_of=2017-03-08)` returned its 552,675,341.
  - **A schema-v3 ingest of the pages scope** from this machine's cache, into a scratch directory
    and never committed (`edgar-921d04330af15837`): 26 entities and 478,521 rows. 1,247 of 1,426
    accessions carry an acceptance time. The 179 without are each named "listed by no
    submissions document read": 13 older pages are not cached here. The filings objects total
    64,713 bytes.
  - **What the cut holds back.** Each company's last 8 days with a latest fact: 208 filing days.
    On them, 38,810 facts filed that day are served by the day-level cut and held back by the
    acceptance cut at that day's close, on 24 companies, with 0 undetermined. TGT's 10-K of
    2025-03-12 is one: accepted 20:36:03 UTC, 16:36 EDT.
- **Parity on the committed pages snapshot, main against this branch, one cache state.**
  - **Method.** Each page company's cached companyfacts sha256 was recorded before, between and
    after the two runs, and it did not move.
  - **The 10 zero-diff pages** (BRBR, CNXC, FUBO, NCNO, NFLX, NKE, ROST, TGT, TJX, V) have
    identical counts at both. Main showed the cache's fetch time for them (2026-11-11, and
    2026-08-12 for V); this branch shows the snapshot's (2026-10-27).
  - **The 14 pages main reported "with a diff"** (6 to 1,115 row differences each, laid on the
    store) are each CHANGED here, with both copies' fetch times: AMZN, EPAM, GOOGL, IT, MVST,
    ORKA, PARR, SMPL, TECX, UBER, VITL, VRRM, WERN and WLK. UBER's cached copy is older than the
    snapshot's (2026-08-12 against 2026-10-27).
  - **3 UNREAD at both.** BURL and MCK are not held, now "not ingested". LLY is not cached.
- **`python -m vinci.facts verify`** passes the committed pages snapshot here: every object's
  bytes as sealed and its rows hashing to its name, against schema v2's contract.
- **Tests.** `tests/test_facts_fix2.py` has 31 cases: 27 written first and 4 from review round
  0. On main all 27 first ones fail; the 10 negative pins among them fail there only because main
  has no `basis`, `stale_ok`, `fetched_at` or `upload_refusal`, not on behaviour. Each of the
  review's 3 behaviour tests failed on this branch before its fix. 169 fact-layer tests pass. The 138 existing fact-layer tests pass, with these changes:
  - 11 test functions in `test_facts_layer.py` now name `basis="filed"`, because they read on a
    filing day or against `facts_as_of`;
  - one is renamed for RFL-D5 (`…raises_not_held`);
  - the parity-skip test reads the new summary line;
  - two fake stores in `test_facts_screen.py` take the new keywords;
  - the constructed manifests in three test files carry a `fetched_at`.

**BOUNDARY.**
- **Pages snapshot.** `edgar-4f3207f4da9fb71a` as committed at `946943ec`.
- **SEC cache.** The primary checkout's on 2026-11-11, by symlink, read only.
- **Leak count.** Latest facts by `store.latest(as_of=2026-11-11)`, those whose accession is on
  the entity's cached recent page, against a 16:00 America/New_York close of the row's own
  `filed_date`.
- **"Held back" count.** On the scratch v3 snapshot, each company's last 8 distinct
  latest-fact filing days, the keys whose day-level latest filing is dated that day.
- **Originals sizes.** The cached copies' bytes, which are not necessarily the ingested copies.
- **Screen snapshot.** Not replayed. Its objects are not on this machine, and 1,191 of its 1,692
  responses are not in this cache.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Every read of a committed (v2) snapshot on a filing's own day now raises for that key**,
  until 2b re-ingests with acceptance times. Nothing reads the store, so no page or screen moves.
  Falsifier: a reader that switches to the store on a v2 snapshot.
- **A row without an acceptance time, filed the day after a non-EDGAR trading day**, is out of
  that day's cut though it may have been public. EDGAR closed on Columbus Day; a Friday 18:00
  filing is dated Tuesday. That is an omission, not a leak. It cannot arise for an accession with
  a stated time.
- **A date's cut is 16:00 New York on every day.** On the NYSE's early-close days (13:00, about
  three a year) a filing accepted between 13:00 and 16:00 is inside that day's cut. A reader
  that needs the exchange's own close passes a zone-aware datetime.
- **The cut reads acceptance; companyfacts lags it.** A copy fetched minutes after a filing's
  acceptance may not carry it yet, so a copy fetched just past the cut is "not stale" and can
  still lack it.
- **The reader hashes every object's rows once per open store.** On the pages snapshot that is
  467,887 rows. On a screen replay it is 28M, read once each.
- **Not in this PR.** FL-D11 (a swap after the first read is served; `verify=False`) is a note no
  ID asks for. Switching any reader to the store is 2b's, with the operator's approval.
