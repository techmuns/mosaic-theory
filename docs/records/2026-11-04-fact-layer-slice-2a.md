---
id: 2026-11-04-fact-layer-slice-2a
status: shipped
date: 2026-11-04
prs: [901, 904]
supersedes:
superseded-by:
---

# The fact layer's slice 2a: each object is named by its rows, so a refresh rewrites only what a filing touched; the screen's universe is in the store; and the screen's EDGAR inputs read from it match the screen's own read with zero diffs

**WHAT.** Three changes, all in shadow. No reader is switched; the screen still reads EDGAR.

1. **Objects are named by content** (schema v2, manifest v2). This is the condition the ADR set
   before any second snapshot (`docs/records/2026-11-04-fact-layer-adr.md`, OPEN ITEM).
   - A data object (source × entity × filed year) is named `content_id`: the sha256 of its rows'
     canonical text, sorted, under a header naming its columns and types.
   - It no longer holds `source_position`. The response's order is kept in one **order object** per
     entity: each response position maps to (data object, row).
   - The writer refuses any pyarrow but **26.0.1**, which `pyproject.toml` pins exactly. The name
     hashes decoded values, so it never depends on pyarrow; the bytes do, so they are pinned too.
     Both, not either.
   - The manifest now states each snapshot's `name` (`pages`, `screen`) and `storage`.
     `storage: git` means its objects are committed under `data/facts/objects`. `storage: local`
     means they are only on the machine that ingested them, at `$VINCI_FACTS_STORE` or the
     git-ignored `data/facts/local`.
   - `current.json` names one snapshot per (source, name): `edgar` and `edgar:screen`. A local
     snapshot opened where its objects are not raises `FactsStoreNotPresentError` at open.
2. **The pages snapshot is re-ingested** as `edgar-4f3207f4da9fb71a`.
   - It holds the same 467,887 rows as slice 1's `edgar-47231ad69c9fc59f`. That snapshot is
     removed from the tree and archived at `48c12137`:
     `git show 48c12137:data/facts/manifests/edgar-47231ad69c9fc59f.json`.
   - The committed objects are now 6.6 MB: 5.94 MB of data and 0.64 MB of order. Slice 1's were
     7.24 MB.
3. **The screen's universe is in the store**, as `edgar-6e0e4626855b9fce` (`name: screen`,
   `storage: local`).
   - Its population is screen run 2026-10-16-01's universe: 2,065 candidates, 1 excluded by
     operator instruction, so 2,064 companies.
   - 1,692 are ingested. 372 are unread, each named in the manifest with its reason: all 372 are
     "not in the SEC cache".
   - It holds 28,089,606 rows in 20,667 data objects (348.7 MB) plus 1,692 order objects (39.6 MB).
     That is far past the 50 MB committed cap, so only its 10.1 MB manifest is committed. **Its
     objects are not shared with any other machine or with CI until R2 exists** (STATE.md §5.0
     row 32 (30)).
4. **The screen's EDGAR inputs, replayed** (`python -m vinci.facts screen-replay`). For every
   name, the screen's own code runs on both sides at the same cut and the same close:
   `enrich_with_fundamentals`, plus the snapshot and the annual EPS series it reads.
   - One side is the cached companyfacts response, handed over whole, as `EdgarClient` hands it.
   - The other side is the store's `companyfacts_as_of`.
   - **Zero diffs** at the run's price date and at each name's filing eve.

Two defects were found and fixed on the way, each behind a test that failed first:

- **The ingest refused values float64 holds exactly.** The guard was `abs(v) > 2**53`, so it
  refused 4 of the screen's companies: AEIS, DXPE and PFIS on `dei:EntityPublicFloat`, and EEFT's
  FY2020 cover share count. EEFT's count is 52,752,851,000,000,000 (accn 0001213900-21-010724),
  which is a filer scale error, and its odd part is under 2**53. The guard is now an exact round
  trip, and `EXTRACTOR_VERSION` moved from 1 to 2.
- **The held-name guard could not protect a scope's FIRST snapshot.** It compared a run only with
  the same scope's current snapshot, and the screen had none. It now also checks how many names
  the run was told to exclude (`scope.exclusions_listed`) against EVERY current snapshot of the
  source. Run with no `--exclude`, the screen ingest refused before reading anything: *"told to
  exclude 0 name(s) … written excluding 6"*. It names counts only.

The row comparison also gained a check. Two blobs holding the same lists in another
namespace/unit order now differ: a reader takes the FIRST namespace present (`points_for_tag`).

**WHY.** The ADR's order: slice 2 is "the screen reads the same facts" behind a zero-diff replay,
and before it, a second snapshot must not rewrite every partition. In slice 1 one new filing moved
every later row's `source_position`. On NFLX, FUBO and NKE's previous cache copies the coordinator
measured 0 of 17, 0 of 14 and 0 of 17 earlier-year partitions shared.

**HOW VERIFIED.**

*Same data under the new names.* Every row of slice 1's 353 objects was compared with every row of
the new 353 data objects, put back in order through the 26 order objects. Result: 26 of 26 entities
and 467,887 of 467,887 rows identical in every field and in order, `source_position` included.
`extractor_version` is 1 → 2 by construction and differs nowhere else. Re-ingesting gives the same
snapshot id and no object rewritten.

*Sharing across a refresh.* The "previous cache copy" is the cached response without the rows of
its last filing day; every other row is verbatim and in order. Both copies were written to one
store:

| name | last filing day removed | rows removed | slice 1 code (48c12137): earlier-year partitions shared | slice 2a code, frames left in place | slice 2a code, frames where SEC puts them | objects a realistic refresh writes |
|---|---|---|---|---|---|---|
| NFLX | 2026-10-21 | 395 | 0 of 17 | 17 of 17 | **16 of 17** (133 frames moved) | 3: 72,660 of 338,021 bytes |
| FUBO | 2026-08-05 | 357 | 0 of 14 | 14 of 14 | **14 of 14** (28 moved) | 2: 39,416 of 253,539 bytes |
| NKE | 2026-10-02 | 201 | 0 of 17 | 17 of 17 | **16 of 17** (99 moved) | 3: 60,613 of 302,651 bytes |

*Corrected in review round 2 of #904.* The first draft of this record claimed 17 of 17, 14 of 14 and
17 of 17. That modelled the previous copy with each `frame` left where today's response puts it.
SEC instead puts a period's `frame` on its LATEST-filed row: the reviewer counted 101,313 of the
101,317 multi-filed framed keys on the committed pages that way. So the copy before a filing
carried that period's frame on an older row. `frame` is row content, so the new filing also renames
the partition of the year that row was filed in (2025 for NFLX and NKE). The realistic column is
measured with the reviewer's previous-copy builder (`sec_previous`), on the same cached responses.
A refresh therefore writes the new filing's year, the year whose frames moved, and the order
object. Across snapshots
of different scope, all 165 data objects and 14 order objects of the 14 page companies also in the
screen's universe are the same objects (same cached response, same names).

*Page parity, the 130 cuts of slice 1, on `edgar-4f3207f4da9fb71a`:*

| cut | pages | rows compared | filed after the cut | row diffs | order diffs | keys compared | key diffs | ambiguous keys | `get()` sampled | `get()` diffs |
|---|---|---|---|---|---|---|---|---|---|---|
| each page's price date | 26 | 467,382 | 505 | 0 | 0 | 246,984 | 0 | 4 | 5,200 | 0 |
| 2020-06-30 | 26 | 228,494 | 239,393 | 0 | 0 | 125,098 | 0 | 1 | 4,600 | 0 |
| 2023-12-31 | 26 | 358,286 | 109,601 | 0 | 0 | 191,789 | 0 | 1 | 5,200 | 0 |
| 2025-06-30 | 26 | 417,048 | 50,839 | 0 | 0 | 220,874 | 0 | 1 | 5,200 | 0 |
| each page's filing eve | 26 | 459,811 | 8,076 | 0 | 0 | 242,986 | 0 | 1 | 5,200 | 0 |
| **all** | **130** | **1,931,021** | 408,414 | **0** | **0** | 1,027,731 | **0** | 8 | 25,400 | **0** |

*The screen snapshot verifies deep.* `python -m vinci.facts verify --name screen` checks every
object present with its sealed bytes, all 28,089,606 rows hashing to their objects' names, and every
order object a bijection. It is clean, in 4 min 7 s.

*The screen replay, run 2026-10-16-01, on `edgar-6e0e4626855b9fce`* (14 min 10 s):

| cut | names | of them reached G3 | unread (not in the SEC cache) | rows compared | store rows | row diffs | order diffs | fields compared | field mismatches |
|---|---|---|---|---|---|---|---|---|---|
| the run's price date | 2,064 | 434 | 372 | 28,089,606 | 28,089,606 | 0 | 0 | 32,148 | 0 |
| (of them, reached G3) | 434 | 434 | 0 | 5,809,678 | 5,809,678 | 0 | 0 | 8,246 | 0 |
| each name's filing eve | 2,064 | 434 | 372 | 27,590,689 | 27,590,689 | 0 | 0 | 32,148 | 0 |
| (of them, reached G3) | 434 | 434 | 0 | 5,693,772 | 5,693,772 | 0 | 0 | 8,246 | 0 |

**The price-date cut proves the read, not the cut.** The newest filing anywhere in the screen
snapshot is 2026-10-07, before the run's 2026-10-16 price date, so that cut excludes 0 rows. The
cut is exercised by the filing eves (2025-05-21 → 2026-10-06), which exclude 498,917 rows.

The 19 fields per name-cut are:
- the record's 9 `Fundamentals` fields: P/E and its percentile, both signs, both leverages, the
  share-count change, and the deferred EV/EBITDA pair;
- the snapshot's 9;
- the annual diluted EPS series, point by point.

The P/E LEVEL is the run's own last close over each side's EPS. The percentile needs the run's full
bar history and is UNKNOWN on both sides; its EDGAR input, the EPS series, is compared in full.

*Mutants of each new filter* (each source file restored and its sha256 re-checked):

| mutant | tests | on the live corpus |
|---|---|---|
| the name hashes `source_position` too | 5 sharing pins fail | sharing back to 0 of 17 / 0 of 14 / 0 of 17 |
| the replay ignores the order object | order pins and the replay pins fail | page parity: 26 of 26 pages with an order diff |
| the store sorts namespaces, list-order check removed | the list-order pin fails | page parity: 0 of 26 caught |
| the store sorts namespaces, list-order check kept | the order pin fails | page parity: 21 of 26 caught (5 pages already list them sorted) |
| the value guard is a size limit again | the EEFT pin fails | the measurement of record: 4 of 1,692 cached companies refused |
| the writer's pin is not checked | the pin's test fails | — |
| a local snapshot opens where its objects are not | the fail-loud pin fails | — |
| the exclusion list is checked only against the same scope | 3 guard pins fail | not run live: it would read a held name |
| the replay compares no field | the field pin fails | — |
| the replay compares no row | the late-store and field pins fail | — |

*The replay's power on the live corpus.* The replay's real code was run over the 434 names that
reached G3, each against a deliberately broken store. A "name" here is a company at one cut.

| broken store | at the price date | at the filing eve |
|---|---|---|
| reads one day LATE | 0 of 434 (nothing was filed on 10-17) | **434 of 434**, all by the rows; no field moves |
| reads one day EARLY | 0 of 434 (nothing filed on 10-16) | **10 of 434** (the names with a filing ON the eve); 5 with a field mismatch: the share-count change (5), the snapshot's as-of (5), net debt (3) |
| loses the `dei` namespace | **432 of 434**; the share-count change differs on 413 | **427 of 434**; 412 |
| returns namespaces sorted | **329 of 434**, by the list-order check alone | **300 of 434** |

No screen field moves under the late store, because the screen cuts whatever it is handed again
(`enrich_with_fundamentals` and `compute_fundamental_snapshot` both apply `facts_as_of` at its own
cut). Only the rows can see a store that reads late, which is why the replay compares both.

**REVIEW ROUND 2 OF #904 (coordinator), fixed behind tests that failed first on `cfa588a3`:**
- **The held-name guard dead-ended every later screen run.** It compared this run's in-scope
  exclusion count with the previous snapshot's, so a run whose universe no longer held the excluded
  name was refused with every `--exclude` passed (0 < 1). It now compares only over the same
  population: the same rule and as many names selected. A later run is accepted, and a same-run
  re-ingest that drops the exclusion is still refused (checked on the committed manifests).
- **The row comparison is now pinned on values.** One `val` changed with count and order
  unchanged gives 2 differing rows. That pin is the one that fails under the reviewer's `val`-blind
  mutant; every other pin passed it.
- An int given for a float64 column is named as the float it is stored as, so its object hashes to
  its own name.
- A corrupt cache entry is "unreadable", not "not in the SEC cache".
- The replay refuses a ticker that `securities.jsonl` maps to another CIK than the one the snapshot
  ingested.
- The replay's truncation line states example lines, rows and lists in their own units.
- Units here: MB is 10^6 bytes, MiB is 2^20.

**BOUNDARY.**
- Every count is measured 2026-11-04 on main `f419b845` plus this branch.
- The SEC cache read is the primary checkout's `data/cache/sec`, read only, never fetched. Its
  copies were fetched 2026-10-27 for the pages and 2026-08-06 → 2026-10-27 for the screen.
- The pages population is slice 1's rule (committed pages plus followed names): 28 selected, 1
  excluded by operator instruction, 26 ingested, 1 unread (not cached).
- The screen population is run 2026-10-16-01's candidate rows (2,065), each CIK read from the
  committed `securities.jsonl` through `universe_snapshot.jsonl` at the run's `universe_as_of`
  (2026-10-16).
- Rows are companyfacts rows (one per filing's statement of a period). Bytes are Parquet object
  bytes. "Names" in the replay are companies; a name-cut is one company at one cut.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **DEFERRED, OWNED IN STATE.md §5.0 row 44: the screen snapshot's objects exist in ONE SESSION
  WORKTREE** (corrected in review round 2 of #904; the first draft said "on one machine").
  - They are in `.claude/worktrees/quirky-khayyam-b2ec8b/data/facts/local`: 22,359 objects, 388.3
    MB by the manifest and 414 MiB on disk. It is the only `data/facts/local` on this machine; the
    reviewer scanned every worktree, and the primary has none.
  - 22,180 of them exist nowhere else. The other 179 are the pages snapshot's committed objects.
  - Archiving the session deletes its worktree (RUNBOOKS §k), and the committed manifest would then
    name objects that exist nowhere. They are reproducible only from the same cache vintage.
  - Readers without them fail loud (`FactsStoreNotPresentError`).
  - Their home is R2 (row 32 (30)) or, until R2 exists, a lasting directory outside any session's
    worktree, set as `$VINCI_FACTS_STORE`. Falsifier: a reader that opens this snapshot anywhere
    without the objects and does not raise.
- **The replay compares the store with the screen's code over the SAME cached response, not with
  what run 2026-10-16-01 read on its day.** The screen re-reads a cache copy older than a day, so
  on 2026-10-16 it may have read a later copy than the one held now. 2b, which switches the reader,
  needs the run to refresh the store itself.
- **DEFERRED to the operator: git growth** (measured in review round 2 of #904; the policy is
  the operator's).
  - The screen manifest is 10,144,124 bytes pretty-printed and 8,308,803 compact. It has one entry
    per object, each carrying a `path` that is derivable
    (`source/entity/filed_year/content_id.parquet`).
  - `fetched_at` is in the hashed manifest body, so a refetch of unchanged data is a new snapshot id
    and a new 10 MB manifest.
  - `extractor_version` is inside every `content_id`, so a version bump with unchanged values
    renames all 353 of the pages' data objects: about 6.6 MB of public history per bump.
  - The reviewer's estimate: weekly screen manifests kept in the tree come to about 525 MB a year;
    removed from the tree at each supersede, about 7 MB a year packed.
  - *Fixed in round 2:* the 50 MB cap now counts manifests as well as objects. The committed
    fact-layer bytes are 16.9 MB: 6,584,136 of objects and 10,314,757 of manifests. History is
    still not counted.
- **DEFERRED to 2b, before anything reads the screen from the store: there is no staleness signal.**
  - `get`, `frame`, `latest` and `companyfacts_as_of` never compare `as_of` with the response's
    `fetched_at`. A read as of a date after the fetch returns the copy as fetched, with no warning.
  - 1,677 of the screen snapshot's 1,692 copies were fetched before 2026-10-01 (range 2026-08-06 →
    2026-10-27; measured on `edgar-6e0e4626855b9fce`'s manifest).
  - A company the snapshot does not hold raises the same `FactUnknownError` as "nothing filed by
    the date", so a reader cannot tell the two apart.
- **DEFERRED: opening a local snapshot checks only that its directory exists.** An empty
  `data/facts/local` opens, and the first read then fails loud on the missing object.
- **The order objects are rewritten on every refresh** of a company whose response changed: 0.64 MB
  for the 26 page companies, delta-encoded (2.18 MB dictionary-encoded).
## Amendments

**2026-11-06 — the held-name guard this record extends is REMOVED.** The operator lifted the hold
on 2026-11-05: *"i dont want mosaic theory to hold back any names for teamnostra repo, its two
separate setups"*. `scope.require_exclusions` is gone, and with it the first-snapshot and
same-population comparisons above. So is `screen_scope_names`' `exclude`. A screen ingest takes no
`--exclude`. The committed screen manifest still states 1 excluded of a list of 6, and the screen
replay still reads that count. Record:
`docs/records/2026-11-06-the-fact-layer-holds-back-no-name.md`.
