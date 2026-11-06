---
id: 2026-11-04-fact-layer-adr
status: open
date: 2026-11-04
prs: [895, 896]
supersedes:
superseded-by:
---

# The fact layer: every extracted fact persisted point-in-time, so "as of the price date" is one query. Slice 1 holds EDGAR companyfacts for the 26 page companies, and it matches the page's own as-of read on every committed page with zero diffs (ADR)

**WHAT.** The decision, approved by the operator on 2026-11-04, verbatim: *"Yes, start the fact
layer on the minimal stack (Parquet, R2, DuckDB, Python API)"*. And its first slice, shipped here.

- **Storage.** Facts are immutable Parquet objects, one per **source × entity × filed year**.
  Each object is named by the sha256 of its own bytes
  (`<source>/<entity>/<filed_year>/<sha256>.parquet`) and is never overwritten. *Corrected in
  review round 2:* an unchanged partition is NOT yet shared between snapshots. Each row carries
  `source_position`, its index in the whole response, so one new filing shifts every later row and
  rewrites every partition after it. On NFLX, FUBO and NKE's previous cache copies the coordinator
  measured 0 of 17, 0 of 14 and 0 of 17 earlier-year partitions shared, with rows identical once
  `source_position` is stripped; every refresh would add about 7 MB to public history. The bytes
  also embed the writing pyarrow's version. See the OPEN ITEM below.
- **In git.** One JSON manifest per snapshot (`data/facts/manifests/<snapshot_id>.json`): the
  snapshot id, every object's path, sha256, rows and bytes, the schema version and contract hash,
  and each entity's source response (URL, `fetched_at`, response sha256, row counts). The snapshot
  id is derived from that content, so ingesting the same cache twice gives the same id.
  `data/facts/current.json` names each source's current snapshot. The schema is a data contract,
  `data/facts/schema.json`, and a test fails when the code's schema differs from it.
- **Engine.** DuckDB, embedded and in memory; there is no DuckDB database file. Point-in-time is
  `WHERE filed_date <= :as_of`, and the latest such filing wins.
- **API.** `vinci/facts/`: `open_store()` → `FactStore.get(entity, "<taxonomy>:<tag>", Period,
  as_of)`, `FactStore.frame(concept, period, as_of, entities=…)` (every requested entity lands in
  `facts`, `unknown` or `ambiguous`), `latest(entity, as_of)` and `companyfacts_as_of(entity,
  as_of)`. A `Fact` carries the value, a structured `source_ref` (accession and tag), the filed
  date and the snapshot id.
  - Nothing is imputed. Nothing filed by the as-of raises `FactUnknownError`.
  - When the latest day's filings state different values, `FactAmbiguousError` is raised. The
    store never picks one.
- **One writer per source.** `vinci/facts/edgar_ingest.py` is the only writer for `edgar`. It
  reads the SEC cache through `CachedHttp`'s own key scheme with no TTL, and it never builds a
  request. It keeps every filing's version of every fact (originals, comparatives and
  restatements) and drops only exact duplicates, counted. A row of a shape it could not replay
  raises. A row with no `filed` date is shape-checked like any other, then dropped (as
  `facts_as_of` drops it), and NAMED in the manifest beside its count (none in snapshot 1).
- **The held-name exclusion cannot be forgotten.** It is a command-line flag (`--exclude`), so
  the ingest refuses to write a snapshot that excludes fewer names than the current one
  (`scope.require_exclusions`, before anything is read or written). The refusal names the counts,
  never a name, because a manifest's tickers are public and permanent.
- **Location.** A local directory today: `$VINCI_FACTS_STORE`, defaulting to
  `data/facts/objects`. A remote name (`r2://`, `s3://`) raises `RemoteStoreNotConfiguredError`.
  No R2 bucket or credential exists (checked 2026-11-04: none in `.env`, none in the GitHub
  secrets), so no upload code was written. A real run could not prove it. The operator action is
  a STATE.md §5.0 item.
- **Shadow only.** No page or screen reader reads the store in this slice. The page keeps
  `AsOfEdgar` and the screen keeps its own path.

**WHY.** Extracted facts did not persist outside each page. The screen computed its fundamentals
separately from the page, and "as of the price date" was threaded reader by reader: #884, #885 and
#888 each fixed a different reader reading past a page's price date in the same month. The store's
schema has a point-in-time `fundamentals` table (`vinci/store/schema.py`) that no code writes or
reads (no hit for `INTO fundamentals` / `FROM fundamentals` in `vinci/`, `scripts/` or `tests/`,
and none in `git log -S"INTO fundamentals"`). It is left as it was; removing it is not this
slice's scope. A fact layer makes the cut one predicate, and lets the screen and the page share
one set of facts.

Size decided the vehicle. Measured 2026-11-04 on the SEC cache: 2,253 companies hold 34,582,442
EDGAR facts, about 8.5 GB as JSONL and 0.6 GB gzipped. That is too big for git, so the data goes
in object storage with its manifest in git (the DVC / lakeFS pattern).

**ALTERNATIVES CONSIDERED.**
- **JSONL in git.** Diffable, but 8.5 GB for EDGAR alone, past GitHub's 100 MB file limit and
  1–5 GB repo guidance, and every refresh grows the history forever. Kept for the manifest, which
  is small.
- **Hosted Postgres (Neon / Supabase).** Transactions for many writers, but this design has ONE
  writer per source. It adds a server, credentials and a network dependency to every read. It is
  the move if many concurrent writers are ever needed, which DuckDB's own documentation suggests.
- **Dolt / DoltHub.** Branch, merge, row diffs and `AS OF` built in. But it brings a second
  version-control system beside git, a server or hosted remote for reads, and its `AS OF` is
  commit-time, not filing-time. The filing-time cut still has to be a column predicate.
- **Graph-first (a graph database).** The numbers are tables. Relationships (the exposure map,
  ownership) start as edge tables in this store. A graph engine waits for a measured traversal
  need.
- **Not now:** an MCP server (tool poisoning and prompt injection are real; the Python API and CLI
  come first), and an Iceberg catalog (R2 Data Catalog is the upgrade path in the same bucket, but
  it was in beta).

**GUARDS.**
- **One writer per source.** DuckDB allows one read-write process. No writable DuckDB file is ever
  shared: each writer publishes Parquet and a manifest, and agents only read.
- **Content-addressed, immutable objects.** `store.write_object` refuses different bytes under an
  existing name. Partitions are written with fixed options in `source_position` order, so the same
  rows give the same bytes under the same pyarrow version. That makes a re-ingest of the SAME cache
  reproducible; it does not make a refresh share partitions (corrected above).
- **The stopgap cap is a test.** `tests/test_facts_contract.py` fails when the committed objects
  pass 50 MB (with its negative pin), so the Parquet leaves git for R2 before history grows past
  it.
- **The manifest matches its files, in CI.** `tests/test_facts_contract.py` checks:
  - every manifest entry carries its keys, else a `FactsStoreError` names the entry (round 2);
  - every committed manifest's id recomputes, its totals add up, and each entity's `rows_kept`
    equals the rows its files hold (round 1);
  - every object it names exists, hashes to its name and holds the stated rows under the contract;
  - no object sits outside every manifest;
  - `current.json` resolves.

  The reader re-hashes each object the first time it touches it, and refuses bytes the manifest
  did not seal.
- **The contract is a tripwire.** `schema_sha256` is the committed contract's hash, so any column
  change (a doc string included) fails verification until the contract is regenerated and
  `SCHEMA_VERSION` bumped in one reviewed diff.
- **Coarse partitions.** 353 objects for 26 companies (about 14 filed years each). Compaction
  waits for a measured small-file cost.
- **Licence.** The operator ruled on 2026-11-04 that the licence covers publishing CIQ-derived
  facts and Polygon and Tiingo prices. CLAUDE.md states it as the **PUBLISHED DATA** rule (#894,
  `docs/records/2026-11-04-licence-covers-publishing-ciq-derived-facts-and-prices.md`), with three
  conditions on every published value:
  - it carries its source_ref;
  - it carries its knowable date (for CIQ, the export date or a column's stated filing date, never
    the period end);
  - it is extracted, not copied: the workbook file never enters git or the bucket.

  Slice 1 publishes EDGAR facts only. Those are public filings, and each row carries its accession
  (the source_ref) and its filed date (the knowable date).
- **CIQ is not point-in-time.** An export carries restated history as of its export date. When
  CIQ arrives (slice 4), each CIQ fact's knowable date is the export date, or a column's stated
  filing date, never its period end. Otherwise the store re-creates look-ahead.

**THE SLICE PLAN** (each one PR, each proven by a zero-diff replay of the committed pages):
1. **EDGAR** companyfacts, every version kept; `facts_as_of` becomes a query. Shadow-run against
   the page's EDGAR read. *This record.*
2. **The screen reads the same facts.**
3. **Release and 8-K figures, with their verbatim spans.**
4. **CIQ readers.** Their outputs, local only, keyed to the workbook's sha256 and stamped with the
   export date as the knowable date.
5. **AI-read extractions as their own tier.** Quote, model and prompt hash, reusable when the
   inputs have not changed.
6. **The page's readers move over one at a time**, each behind a zero-diff replay.

**HOW VERIFIED.**
- **Ingest.** Cache-only, from the primary checkout's `data/cache/sec`; every copy was fetched
  2026-10-27.
  - 26 companies; 467,887 rows in the responses; 467,887 rows kept.
  - 0 exact duplicates, 0 rows without a filed date.
  - 353 objects, 7,241,790 bytes.
  - Snapshot `edgar-47231ad69c9fc59f`. A second run wrote the identical id and objects.
- **Parity.** `python -m vinci.facts parity --cache-dir <the SEC cache> --exclude <each held
  name> --also-at 2020-06-30 --also-at 2023-12-31 --also-at 2025-06-30 --filing-eve` (the held
  names are never written here; the ingest refuses a run that drops one). For each page,
  `facts_as_of(companyfacts, page_price_date(...))` against the store at the same as-of, three ways:
  - every row, every field, in order;
  - the latest filing for every (taxonomy, tag, unit, period), from plain Python against the
    store's SQL: a same-day disagreement must be ambiguous on both sides, and on a same-value tie
    the filing the store NAMES must be the reference's (round 2; before, accessions were compared
    as a set, which could not see which one was named);
  - a deterministic sample of up to 200 keys per page through the public `get()`, compared the
    same way.

  | cut | pages | rows compared | rows filed after the cut | row diffs | keys compared | key diffs | keys restated | ambiguous keys | `get()` sampled | `get()` diffs |
  |---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
  | each page's price date | 26 | 467,382 | 505 | 0 | 246,984 | 0 | 9,756 | 4 | 5,200 | 0 |
  | 2020-06-30 | 26 | 228,494 | 239,393 | 0 | 125,098 | 0 | 6,275 | 1 | 4,600 | 0 |
  | 2023-12-31 | 26 | 358,286 | 109,601 | 0 | 191,789 | 0 | 8,471 | 1 | 5,200 | 0 |
  | 2025-06-30 | 26 | 417,048 | 50,839 | 0 | 220,874 | 0 | 9,112 | 1 | 5,200 | 0 |
  | eve of each page's last filing day | 26 | 459,811 | 8,076 | 0 | 242,986 | 0 | 9,658 | 1 | 5,200 | 0 |

  **130 page-cuts, 130 zero-diff, 1,931,021 rows** (the first four cuts' 104, 1,471,210 rows, as
  first measured; the eve cuts added in round 2).
  The EVE is the day before the last day anything was filed on or before the page's price date:
  a store reading one day late passes every cut that falls between filings, and the eve is the cut
  that sees it. *At the page price dates the cut excludes rows on only TWO
  pages*: NCNO (481 rows filed after 2026-08-17) and MVST (24 after 2026-09-16). Every other page's
  cache copy was fetched within days of its price date, with nothing filed in between. That is why
  the three earlier cuts were run: they exclude 50,839–239,393 rows each. At 2020-06-30, 3 pages'
  companies had filed nothing, so 23 pages were sampled.
- **The parity can find a diff.** Run on the live pages under six mutants of the reader:
  - **Cut removed from `get` / `latest`:** NCNO (481 key diffs) and MVST (24).
  - **Cut removed from the row replay:** NCNO (481 row diffs) and MVST (24).
  - **Earliest filing wins:** all 26 pages, 1,862–9,053 key diffs each.
  - **Reading one day late** (both cut sites, round 2): 0 of 26 price-date cuts, 26 of 26 eves
    (7,567 key diffs).
  - **Lowest accession wins a same-value tie** (round 2): 7 of 26 price-date cuts, 6 of 26 eves.
  - **No form preference on a tie** (round 2): NKE on both cut sets (6 key diffs).

  Restored, sha256 unchanged. The last three also fail tests (6, 1 and 1 of the 46 then in
  `tests/test_facts_layer.py`).
- **Tests.** `tests/test_facts_layer.py` holds 47 pins on FROZEN slices of three real cached
  responses (`tests/fixtures/facts/`: NFLX, FUBO, NKE). Each slice carries its URL, `fetched_at`
  and response sha256.
  - **Filed after the as-of.** NFLX FY2023 diluted EPS is absent on 2024-01-25 and present on its
    filing day, 2024-01-26.
  - **Restated.** It reads 12.03 (`…-25-000044`, filed 2025-01-27) at 2026-01-22, and 1.2
    (`…-26-000034`, filed 2026-01-23) from 2026-01-23.
  - **Missing.** A missing concept, a missing period or an entity outside the snapshot raises
    UNKNOWN.
  - **Same-day disagreement.** FUBO's 2019-12-31 discount was stated as 710000 by a 10-K/A and as
    456000 by a 10-Q/A, both filed 2020-08-11, so it is ambiguous that day. It reads 456000 the day
    before and 710000 (`…-20-015517`) two days after.
  - **Row replay.** The store equals `facts_as_of` row for row at six as-ofs on both slices.
  - **Ties (round 2).** NKE's FY2024 net income, stated identically by its 10-K (`…-26-000088`) and
    its DEF 14A (`…-26-000089`) on 2026-07-15, names the 10-K. FUBO's 2016-11-16 cover count,
    stated identically by two 10-Qs on 2016-11-23, names the greater accession (`…-16-015421`).
  - **The held-name guard (round 2).** An ingest without the exclusion the current snapshot has
    refuses, names only the counts and writes nothing. On the live corpus it refused against
    `edgar-47231ad69c9fc59f`; with the exclusion, the snapshot came back byte-identical.

  - **No count is read as zero (round 2).** A current snapshot that states no exclusion count
    refuses the run rather than reading it as 0 (the zero-coercion lint caught the first draft).

  `tests/test_facts_contract.py` holds 8 more: the negative pin of the manifest check, and the
  50 MB stopgap cap with its own negative pin.
  - **Mutation.** With the cut neutralized in the latest-filing SQL, 7 tests fail. With it
    neutralized in the row replay, 10 fail (`PYTHONDONTWRITEBYTECODE=1`, `__pycache__` cleared).

**BOUNDARY.**
- **Population.** The committed pages (`data/dossiers/*/dossier.json`, 27) plus the followed
  names (`data/followed.json`, 16) give 28 tickers.
  - One committed page is excluded by a standing operator instruction. It is counted in the
    manifest's scope and never named.
  - MNST (followed, no page) resolved to CIK 865752 from the cached `company_tickers.json`
    (fetched 2026-10-27). Its companyfacts are NOT in the cache, so it is listed as unread in the
    manifest and was not fetched.
  - So: 26 companies ingested, 26 pages compared.
- **Window.** All filings in each cached response.
- **Unit.** Rows are companyfacts fact rows; keys are (taxonomy, tag, unit, period start, period
  end).
- **When.** Measured 2026-11-04 on branch `claude/fact-layer-edgar-slice1-416d05` off main
  `a439eabe`.
- **What parity compares.** The two readers over the SAME cached copy. It is not a claim that each
  page's own assembly read that copy.
- **What is not stored.** A tag's `label` and `description` (no EDGAR reader reads them: searched
  `"label"`, `"description"`, `.get("label")` and `entityName` in `vinci/edgar`, `vinci/dossier`
  and `vinci/screens`; every hit read a CIQ or table label). Parity compares fact rows.
- **Ambiguous keys.** 14 (taxonomy, tag, unit, period, filed-day) groups across the 26 responses
  state two values on one day. 4 stay ambiguous at the page cuts:
  - EPAM's three S-8 fee rows of 2026-08-06 (`ffd:` namespace);
  - ROST's 2010-11-18 cover share count: 19,084,540 by a 10-Q and 119,084,540 by a 10-Q/A, both
    filed 2010-12-08.

  The store refuses both. Whether an amendment filed the same day should win is a ruling for
  slice 6, not taken here.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Two new core dependencies,** `duckdb>=2.0` and `pyarrow>=26.0` (2.0.0 and 26.0.1 installed
  into the root `.venv` on 2026-11-04; no numpy pulled in). A local suite that has not synced
  `pip install -e ".[dev]"` reads red from env drift, not code.
- **The Parquet is committed as a STOPGAP** because it is 7.2 MB, under the 50 MB line. It moves
  to R2 when the bucket exists, and the manifest stays in git. *Falsifier:* the committed objects
  exceeding 50 MB means they leave git first.
- **The snapshot id is not a row column** (the draft's column list had one), so that an
  unchanged partition CAN be the same object across snapshots; the reader stamps the id from the
  manifest. Today it is not (the OPEN ITEM below).
- **Values are float64.** The ingest refuses an integer above 2^53 (none in this population) and a
  non-finite value. The replay writes an integral value back as an integer, which is equal
  (`==`) to every source value measured: 437,406 integers, and 30,481 floats with none integral.
- **A same-value tie** (two filings on the latest day stating the same value) names a PERIODIC
  report over any other form (`reader.PERIODIC_FORMS`: 10-K, 20-F, 40-F, 10-Q and, by prefix,
  their amendments and the 10-KT, the forms the page's readers filter on), then the greatest
  accession, and lists the others in `concurrent_accessions`. At the 26 page cuts there are 240
  such ties; the form preference moves 3 of them, all NKE's net income for FY2024–FY2026, from the
  DEF 14A to the 10-K (round 2). The choice is deterministic, not a claim that one filing is the
  source; a same-day DISAGREEMENT still raises.
- **Two findings DEFERRED from the pre-PR review (round 0):**
  - `edgar_ingest.read_cached` builds one `CachedHttp` (and its unused HTTP client) per URL read:
    negligible at 26 entities, and no request is sent. Revisit when the ingest runs over the whole
    cache.
  - `store.verify_manifest` raised `KeyError` on an entry missing a key, rather than naming it.
    FIXED in round 2 (a typed `FactsStoreError` naming the entry).
- **One finding DEFERRED from review round 1 (in-session `/code-review high`, Codex having
  failed on its usage limit):** an object's name hashes its Parquet BYTES, and those embed the
  writing pyarrow's version (`created_by`). Re-ingesting identical rows under a newer pyarrow
  therefore writes a second copy of every partition under new names, and a new snapshot id, with
  no change in the data. Naming objects by a canonical hash of their ROWS instead would change
  the design's "content-addressed object names" from bytes to rows, so it is the operator's call.
  *Corrected in round 2:* this said the writer's pyarrow was "pinned in practice by the one writer
  per source". It is not pinned at all: `pyproject.toml` says `pyarrow>=26.0`, there is no lock
  file, and CI installs the latest. *Falsifier:* a re-ingest that changes `created_by` and nothing
  else.
- **OPEN ITEM, BEFORE ANY SECOND SNAPSHOT OR ANYTHING REACHES R2** (STATE.md §5.0 row 44): name
  each object by a canonical hash of its ROWS without `source_position`, keeping the order
  separately, and pin the writer's pyarrow. Until then every refresh rewrites every partition, and
  the 50 MB cap test is the brake on what that costs git.
## Amendments

**2026-11-06 — the held-name exclusion under WHAT and GUARDS is REMOVED.** The operator lifted the
hold on 2026-11-05: *"i dont want mosaic theory to hold back any names for teamnostra repo, its two
separate setups"*. `scope.require_exclusions` is gone, and `ingest` no longer takes `--exclude`, so
a copied command that passes it is refused before anything is read. `parity --exclude` stays as an
ordinary skip, and its output counts what it leaves out. The committed manifests still state their
counts (1 of 6). New manifests state 0 and 0. Record:
`docs/records/2026-11-06-the-fact-layer-holds-back-no-name.md`.
