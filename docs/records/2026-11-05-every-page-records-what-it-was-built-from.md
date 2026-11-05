---
status: open
date: 2026-11-05
prs: [911]
supersedes:
superseded-by:
---

# Every page records what it was built from: each CIQ export, HTTP response and price series by its full sha256, on the page and in the build's run record — workstream B's design and its first slice (provenance only; the gate is slice 2)

**WHAT.** Workstream B of the 2026-11-04 root-cause review, approved by the operator on
2026-11-05. It addresses two of the review's five causes of defects reaching committed pages:
*pages that do not record their inputs*, and *checks that run only where the data is not* (CI
skipped 501 CIQ-dependent tests on main because the exports are absent; with them linked, real
page defects appeared). The design, as approved, has four parts; this record specifies all four
and ships the first.

1. **Provenance (THIS PR).** Every build records the full sha256 of every input it read, on the
   page and in its assembly-run record. A page built before the record existed is backfilled from
   its own stamps where those inputs are still on this machine; everything else says
   `unrecorded`, with why.
2. **The gate** (slice 2). Inside `vinci dossier assemble` and `precheck`, a check registry runs on
   the build's own inputs: the per-page invariants that now live only in the test suite, the
   page's reconciliations and the basis checks. A FLAG prints on the page's first screen; a HARD
   refuses the write; every result goes into the run record. EVERY NEW CHECK STARTS AS FLAG, and
   one becomes HARD only by the operator's ruling.
3. **Elsewhere** (slice 3). In CI or on another machine, a check runs only when the inputs present
   hash to the page's record; otherwise it reports *not checkable here*, never a pass and never a
   silent skip.
4. **A corpus job** (slice 4). A PR that adds or changes a check runs it over every committed page
   whose inputs are present, before merge.

**THE RENDER DECISION — JSON-ONLY (decided before the build, 2026-11-05).** The block is not
rendered, so the PREVIEW RULE does not apply to this PR and no committed `dossier.md` changes.
- Its readers are machines: the precheck now, and the gate and the elsewhere-check later.
- DESIGN RULE v2 puts machine-complete provenance in the JSON tier.
- The first thing a human must see from it is a gate FLAG ("inputs unrecorded", "this export is
  not the page's"), and that belongs to slice 2's first-screen lines. Rendering the block now would
  re-render all 26 pages for a table no reader acts on, and slice 2 would then re-render them
  again. Slice 2 carries one preview, collapsed and force-open.

**THE VERSION ROW.** `2026-11-05.input-record` is appended to the extraction-version table,
and to its twin in `frontend/views/shared/dossier.js`. A page now carries a block it did not, though
no extracted value changes. The drift pins are re-pinned at it.

**THE MODELS LIVE APART** (`vinci/dossier/inputs_schema.py`). The page schema imports the models
only. Importing `inputs.py` from `schemas.py` let the monitor reach `vinci.store`, a ledger writer,
through every module that reads a page; `test_outcome_import_fences` caught it on this branch's
first gate run.

## The manifest (schema 1) — `vinci/dossier/inputs.py`

ONE IDENTITY PER LAYER, each the one that layer already uses. Nothing here is a new scheme:

| input | identity | why this one |
|---|---|---|
| a CIQ export | sha256 of the file's bytes, all 64 hex | every page stamp is already its first 10 hex (`ciq_sheets.file_provenance`); the fact layer's slice 4 keys CIQ facts on it |
| an HTTP response (SEC, Polygon, FINRA) | `response_sha256` = sha256 of the cached text, UTF-8, under `source_url` and `fetched_at` | the fact layer's own rule and field names (`edgar_ingest.CachedResponse.sha256`, a snapshot manifest's `entities[]`): the page's input and a snapshot's entity are one identity |
| a price series | `rows_sha256` over one canonical JSON line per bar (`[date, open, high, low, close, volume, source]`, prices as floats), oldest first, through `newest_bar` — TAKEN WHEN READ (`provenance.note_series_read`, review round 2) | a store holding more bars later re-hashes the rows through `newest_bar` and compares; a restated or refiled bar changes it. The store is shared across checkouts, so the first draft's re-read after the build could name a bar the build never saw |
| the record | `inputs_id` = `inputs-<16 hex>` over the identities above only (never names, times or counts) | the shape of the fact layer's `<source>-<16 hex>` snapshot id. Two builds from identical inputs carry one id. **Set only on a COMPLETE record**: a partial record has no identity |

THE SHAPE — one literal example, abridged (a real $0 build's record, `vinci dossier precheck
--ticker GOOGL --inputs-json …`, 2026-11-05):

```json
{"schema_version": 1, "recorded": "build", "extraction_version": "2026-11-04.guidance-quote-cut",
 "covers": ["ciq", "responses", "prices"], "inputs_id": "inputs-…",
 "ciq": [{"kind": "estimates", "freq": null, "file": "AlphabetIncNasdaqGSGOOGLEstimatesReport.xls",
          "sha256": "9a120cb5aef38a465b1a78bc3177a0fcef8baff03249ba0284ceac8443264fc8",
          "bytes": 9437505, "stamped_by": null}, "… 10 more"],
 "responses_listed": "all",
 "responses": [{"namespace": "sec",
                "source_url": "https://data.sec.gov/api/xbrl/companyfacts/CIK0001065280.json",
                "fetched_at": "…Z", "response_sha256": "…", "bytes": …,
                "sealed_by": ["edgar-4f3207f4da9fb71a"]}, "… 1,079 more"],
 "responses_digest": {"count": 1080, "by_namespace": {"efts": 1, "finra": 1, "polygon": 14,
                      "sec": 1064}, "sha256": "…"},
 "prices": [{"internal_id": "…", "ticker": "GOOGL", "bars": 480, "first_bar": "…",
             "newest_bar": "2026-10-30", "rows_sha256": "…"}, "… 14 more"],
 "unrecorded": []}
```

- `recorded`: `build` (recorded as the build read) or `backfill` (resolved afterwards from the
  page's own stamps).
- `extraction_version`: the code vintage that wrote THIS record. On a backfill it is not the
  page's assembly vintage.
- `covers` states the classes this record IDENTIFIES: all three on a build, only `ciq` on a
  backfill (review round 2: a backfill listed all three beside empty lists).
- `not_covered` states, on every record, what a build reads that no record covers
  (`inputs.NOT_COVERED`), so "complete" means complete within these bounds:
  - the committed repository files (`data/graph_coverage.json`, `scenarios/<T>.json`,
    `data/followed.json`, the screen snapshots, the committed page), which the commit the page
    lands in versions;
  - the price store's securities rows read through `Store.get_security` (the SIC behind the
    sector label, the stored name), which are git-ignored and NOT versioned by a commit;
  - a credential in a URL's path or a POST body (only query values, path parameters and userinfo
    are redacted).
- `unrecorded`: every input, or class of inputs, the record cannot identify, each with why. An
  export that could not be hashed is listed here and never given a hash.
- `sealed_by`: the committed fact-layer snapshots (`data/facts/manifests/`) whose entity carries
  this exact `response_sha256`.

**TWO HOMES, ONE RECORD (decided on the first real run).** GOOGL's $0 build read 1,080 responses:

- 540 EDGAR filing documents and 510 filing indexes;
- 14 Polygon reference pages, 11 companyfacts, 2 ticker files;
- one each of efts, FINRA and submissions.

In full the record is 357,516 bytes (GOOGL's first $0 precheck, `--inputs-json`, pydantic's
`model_dump_json(indent=2)`), against GOOGL's 635,125-byte committed page. So:

- **the assembly-run record carries the record IN FULL.** That is what a refused build leaves
  behind, so a refusal can be replayed on the inputs that produced it;
- **the page carries it with its response list cut to the fact layer's sources**
  (`responses_listed: "fact_layer_sources"`, `for_page`). Every CIQ export and every price series
  stays listed. The cut responses are counted and hashed in `responses_digest`, and the page's
  `inputs_id` is the full record's, so the run record carrying the same id IS the full list.
  On GOOGL's $0 cohort build (below) the page's block is 9,922 bytes of a 574,248-byte page; the
  run record's is 305,934.

## How it lines up with the fact layer's snapshot ids

The record reuses the fact layer's identities; it does not mint parallel ones
(`docs/records/2026-11-04-fact-layer-adr.md`, `vinci/facts/`, `data/facts/manifests/`).

- **Today the page reads SEC responses through the cache, not the store** (the fact layer is in
  shadow, STATE §5.0 row 44). So a response is recorded by the fact layer's `response_sha256`,
  and `sealed_by` names every committed snapshot that sealed that exact response. On GOOGL's
  build, 1 of its 11 companyfacts responses is sealed by `edgar-4f3207f4da9fb71a` (the pages
  snapshot of 26 entities, GOOGL's among them): the response for NFLX, read as a comparable.
  GOOGL's own (CIK 1652044) is NOT. Its cache copy is newer than the one the
  snapshot ingested on 2026-10-27, because `EdgarClient.companyfacts` re-reads a copy older than a
  day. **This is the freshness gap the fact-layer slice 2b note names, now visible per page.**
- **When a page reads the store** (fact layer slice 6), the record gains a `facts` class: the
  `snapshot_id` and entity read, and the as-of. The response it replaces is identified by the
  snapshot's own `entities[].response_sha256`, so a page recorded before the move and one recorded
  after are comparable without translation. Not built here: no page reads the store, and a class
  no build writes cannot be proven by a real run.
- **CIQ** (fact layer slice 4) keys facts on the workbook's sha256, the same 64 hex this record
  carries.
- **Prices** are not in the fact store. When G puts them in the shared store, a series entry names
  that snapshot as a response entry does. Until then `rows_sha256` is the identity.
- **The id**: `inputs-<16 hex>` mirrors `<source>-<16 hex>`. Both hash canonical JSON with
  sorted keys, and neither changes with the time it was computed.

## Where it is recorded — `vinci/provenance.py`

Three doors, each the only one for its class:

- **`CachedHttp.get_text` / `post_json`** — every SEC, Polygon and FINRA response, served from the
  cache or fetched. `grep` for `httpx.`, `urlopen` and `requests.` outside `netcache.py` finds
  only theme intelligence (2026-11-05).
- **`Store`'s per-name price readers.** `get_price_history`, the one every page reader uses,
  reports the rows it returns, so the series is identified at read time. A read of PART of a series
  (`close_on`, `close_as_of`, `latest_close`, `last_bar_before`, `bar_dates`,
  `price_frontier_for`, `bars_on`) is recorded as partial and makes the record incomplete: no page
  path calls one (searched in `vinci/dossier`, `vinci/edgar` and `vinci/resolver`, 2026-11-05).
- **The assembler's CIQ bundle** (`inputs.load_bundle`, called as `assemble_one` builds it). It
  records:
  - every workbook, the one door every page reader reads CIQ through;
  - the `AS_OF` sidecar, which sets the comps and estimates as-of;
  - each unrecognised file, whose NAME moves a caveat;
  - on a loader refusal, every file in the folder.

**THE EXIT CODE, DECIDED (round 2).** When a written build's run record cannot carry its input
record, the CLI still exits 1: every error does, and a record that could not be built is one.
The line says the build's outcome stands ("page written; nothing to re-run for it"), so a reroll
keyed on the exit status must read the line, not re-run the paid build.

A recorder is context-local and nested. A read reaches the open recorder and every one around it.
A cohort worker starts with none, so one page's reads never reach another's. Two reads happen
BEFORE a page's build starts, and the build folds both in:

- the finalist's own record (a maintained name reads its price history and companyfacts in
  `_standalone_record`), via `Finalist.reads`;
- the resolver's index (two SEC ticker files, loaded once per cohort), via
  `EntityResolver.index_reads`.

A secret-shaped query value is redacted before it is recorded. Every client in this repo sends
its key in a header, so none matches today; the guard is for the URL that one day does.

## The check registry's shape (slice 2 builds it; specified here so slices 2–4 agree)

```python
@dataclass(frozen=True)
class Check:
    id: str                          # "consensus_spread_on_its_trends_figure" — stable, greppable
    what: str                        # plain English, one line: what a failure means for the page
    level: Literal["FLAG", "HARD"]   # FLAG on creation; HARD only by an operator ruling
    ruled: str | None                # the record carrying the ruling (quote + date) when HARD
    reads: tuple[str, ...]           # the input classes it needs: "ciq:estimates",
                                     # "ciq:financials/quarterly", "sec:companyfacts", "prices"
    run: Callable[[Dossier, CiqBundle | None], Sequence[Finding]]
```

- **`REGISTRY: tuple[Check, ...]`** is one module, and a test pins that every HARD names its
  ruling.
- **Inside the build:** each check runs on the build's own bundle and page, before `_write`. Its
  result is `{id, level, outcome: pass | flag | refuse, findings}`.
  - A `refuse` raises `DossierAssemblyError`. The page is not written, and the run record keeps
    the result and the inputs.
  - A `flag` goes on the page's first screen and into the run record.
  - The precheck runs the same registry at $0 and prints the same results.
- **Elsewhere (slice 3):** `checkable(page, check)` asks whether every input class in `check.reads`
  is present AND hashes to the page's record.
  - If not, the outcome is `not_checkable`, naming the input, the recorded hash and the present
    one. It is reported, never counted as a pass, never skipped silently.
  - The test helpers `skip_unless_pages_export` and `skip_unless_export`
    (`tests/ciq_export_support.py`, #889) become calls to it, keyed on the record's full sha256
    instead of a 10-hex stamp.
- **The corpus job (slice 4):** `vinci dossier checks --all` runs a changed check over every
  committed page whose inputs are present, and prints per page `pass | flag | refuse |
  not_checkable`, with its boundary. A PR that adds or changes a check carries that output in its
  body before merge. CI cannot run it (no inputs); the PR's session does, locally, until G's
  shared store makes the inputs present elsewhere.

## The inventory, re-measured on main `097098f9` (2026-11-05)

Three runs of `pytest -m "not network" -p no:cacheprovider -rs` on detached checkouts of main
`097098f9`, each with a JUnit file. All three collect the same 9,314 test ids, and 39 are
deselected as `network`.

| run | `data/` holds | passed | skipped | failed | xfailed | wall |
|---|---|--:|--:|--:|--:|--:|
| A — as CI | nothing git-ignored (no `manual/`, `cache/`, `vinci.db`) | 8,749 | 557 | 0 | 8 | 6m27s |
| B — the assembler's copy | `mosaic-theory-ta`'s `manual/`, `cache/` and `vinci.db` | 9,222 | 78 | 6 | 8 | 21m01s |
| C — the Drive folder | a scratch copy of the Drive CIQ folder and its `ciq-archive`, held names removed; B's cache and store | 9,188 | 114 | 4 | 8 | 24m32s |

**The 557 skips of run A**, bucketed by skip message (a regex over the message: `ciq|export|data/
manual|workbook|\.xls` → CIQ; then `vinci.db|store`; then "has no rows in this run"):

| bucket | skips | in run B |
|---|--:|---|
| CIQ export absent | **501** | B: 471 pass, 5 fail, 25 skip · C: 437 pass, 3 fail, 61 skip |
| price store absent | 5 | 4 pass, 1 fails (`test_store_freshness`) |
| theme-intelligence tables empty | 5 | still skip |
| other (premise cleared, no live exemplar, no chdir …) | 46 | still skip |

The review's 501 reproduces exactly on `097098f9`. They sit in 33 files and 108 test functions.
The largest: `test_forward_layers_basis` (110), `test_forward_multiple_history` (62),
`test_historical_forecast_error` (60), `test_forward_consensus` (56),
`test_horizon_read_block_bounds` (56) and `test_consensus_rows` (23).

**The per-page test cases.**
- **Parametrized by page:** 1,548 collected ids in 133 functions across 56 files carry a
  committed page's ticker as a token of their parameter id (27 pages, the held one included). 427
  of them skip in run A.
- **Of those, 324 are the CIQ-dependent per-page invariants the gate exists to run:** 12 functions
  × 27 pages, every one skipped in CI. All 12 are in the table below, rows 3 and 5–9 and the row
  marked 9b. Rows 4 (`ev_bridge`, one test that loops over the pages) and 10
  (`consensus_rows`, 11 ids) are proposed checks too, but are NOT among the 324.
- **Loop-style:** 357 further test functions read the committed corpus without a per-page
  parameter. This is a source scan, not a collection: a test function, or a module helper it
  calls, names `dossiers` and globs or loops. The count is a heuristic.

**Run B's 6 failures.** Each is a check meeting an input that is not the page's, or a real defect:

| test | what it met |
|---|---|
| `test_ev_bridge::…claims_equal_ciqs_current_figure…` | AORT: 202.393 vs 330.7 — AORT's comps and estimates are 2026-10-26's, its Financials 2026-07-20's (STATE row 32 (28)) |
| `test_forward_consensus::…spread_sits_on_its_own_trends_figure[GOOGL]` | EPS Normalized FY2026 14.80 vs 14.14 against the 2% check (row 32 (28), the operator's tolerance ruling) |
| `test_forward_multiple_history::test_the_refresh_lands_the_layer_and_moves_nothing_else` | AMZN: the assembler's copy holds `e10ed62223` / `e5abf9d69d`, the page was built from `1b971fda50` / `796a53f316` (Drive's) — a test keyed on no export identity |
| `test_forward_multiple_history::test_a_page_that_cannot_name_this_export_is_left_alone` | the same AMZN export mismatch |
| `test_historical_forecast_error::…only_from_the_pages_own_export` | the same AMZN export mismatch |
| `test_store_freshness::…includes_the_benchmark…` | the assembler's store: 8 gated names 7–24 days behind the fleet |

Run B's two passed→skipped cases are #889's guard working: NCNO's and SMPL's estimates exports
on disk are not their pages'.

**Run C's 4 failures** are main's own with the exports the pages were built from:
- GOOGL's and LLY's consensus spreads against the 2% check (LLY: Cash From Operations FY2026,
  33,690.7 vs 35,514.33). Both are the operator's open tolerance ruling, row 32 (28).
- The store's freshness, as in B.
- **`test_forward_multiple_history::test_the_refresh_lands_the_layer_and_moves_nothing_else`**,
  on AMZN's own export. The refresh now records itself in `layer_refreshes`, and the rendered
  stamp line gains "· layers refreshed to …". The test asserts the `dossier.md` is unchanged. It
  is a pre-existing defect on main, hidden in CI by the skip. Reported, not changed here.

Of run A's 501 CIQ skips, run B still skips 25 and run C 61. 61 = 25 + 39 − 3:
- run C skips 39 cases run B ran: 17 are AORT's (the Drive copy holds no AORT folder), 12 are
  BURL's (its folder was removed), and 10 are pins frozen on exports Drive has replaced (AMZN's
  pre-2026-10-08 Estimates and the archived ones it holds);
- run C RUNS 3 cases run B skipped, all passing on Drive's exports:
  `test_ev_bridge::test_the_refresh_lands_the_layer_only_from_the_pages_own_exports` and SMPL's
  two `test_fiscal_year_change_marker` cases (`…live_export_reads_every_latest_figure`,
  `…latest_reads_equal_its_export_with_the_old_calendar_cut_out`).

**HELD NAMES AND THE SUITE (found here, reported, not changed).** The suite parametrizes over
every committed page, so with a CIQ folder linked it runs CIQ readers on BURL's export. AT LEAST
these — *corrected in review round 2: the first draft said "13 cases", which undercounted*:

- 12 per-page CIQ cases;
- `test_ciq_empty_view_and_exhibit_cap::test_the_real_burl_export_is_read_as_empty_not_broken`,
  which reads BURL's real export by design;
- every loop-style test that globs `data/dossiers/*` and reads each page's CIQ folder:
  `test_ev_bridge::test_claims_equal_ciqs_current_figure_on_every_committed_name` is one, and it
  has no exclusion. Run B stopped at AORT's assertion first; a linked run where AORT passes reads
  BURL's. Loop-style tests are not counted one by one here.

A per-page parametrization exclusion would therefore NOT cover all of it. The coordinator is
proposing the suite-wide exclusion to the operator as its own follow-up; it is not built here.

Run B did that before this was noticed: the assembler's copy holds a BURL folder. STATE row 28's
2026-11-04 measurement, with the Drive folder linked, will have done the same. Run C was stopped
and re-run on a copy with BURL's folder removed. No page, no LLM call and no extractor output came
of it, but the standing instruction says never to run an extractor on a held name.

## PROPOSED HARD / FLAG — for the operator to rule on (nothing is HARD by this PR)

Every check below starts as FLAG in slice 2. The proposal column is a recommendation set by face
validity: what a failure means for the page, never what would have paid. "Fails today" is run
B's or C's result on the committed corpus.

| # | check (now in the suite) | per page | fails today | proposed | why |
|---|---|---|---|---|---|
| 1 | **the build's inputs are recorded** — no `unrecorded` on a build's record (new) | all | — (backfilled pages are not builds) | **HARD** | a page that cannot say what it read cannot be checked anywhere else; refusing costs one re-run |
| 2 | **one export per kind on a page** — every block's stamp is the record's export of that kind (new; the "two vintages on one page" class) | all | 0 of 26 backfilled | **HARD** | two exports of one kind on one page is the `forward_multiple_history` refusal's rule, page-wide |
| 3 | `forward_consensus::spread_sits_on_its_own_trends_figure` | 27 | GOOGL (EPS Normalized FY2026, 4.7%) and LLY (Cash From Operations FY2026, 33,690.7 vs 35,514.33, 5.1%), both runs B and C | FLAG | the 2% tolerance is unruled (row 32 (28)); a HARD at an unruled tolerance would be tuning |
| 4 | `ev_bridge::claims_equal_ciqs_current_figure` | all | AORT | FLAG | the page already states DISAGREES; the remedy is a re-export, not a refusal |
| 5 | `forward_consensus::revision_counts_are_bounded_by_their_own_block` | 27 | 0 | HARD | a count outside its block is a mis-read, never a judgment |
| 6 | `forward_multiple_history::every_point_is_its_own_rows_close_cell` and `…every_band_is_the_trailing_bands_own_stat…` | 27 + 27 | 0 | HARD | a point off its own cell is a fabricated number |
| 7 | `historical_forecast_error::every_observation_is_its_fiscal_year_cells…` and `…identity_holds` | 27 + 27 | 0 | HARD | the same: an observation not its cells is not the export's |
| 8 | `forward_layers_basis` (ladder string = structured cells; NTM cells are the sheet's; settled columns are quarter-ends; reconciliations are the layer's own means) | 4 × 27 | 0 | HARD for the first two, FLAG for the reconciliations | a string or cell not the sheet's is a parse defect; a reconciliation gap is information |
| 9 | `horizon_read_block_bounds::every_line_is_its_own_blocks_counts` | 27 | 0 | HARD | a line counted from another block is a mis-read |
| 9b | `horizon_read_block_bounds::the_fix_moves_only_metrics_whose_block_ended_in_the_wrong_place` | 27 | 0 | — (stays a test) | it pins a past fix's effect against the committed pages, not a property of a page; a build has nothing to check it against |
| 10 | `consensus_rows::range_check_holds_on_every_resolved_cell` | 11 | 0 | FLAG | a range check is a plausibility bound, set by face validity, not a mis-read |
| 11 | the price store's freshness against the fleet (`test_store_freshness`) | — | B: 8 names 7–24d | FLAG | stale is said, not refused; the existing 45-day panel ceiling stays the HARD |
| — | **already HARD in code, unchanged:** `_freshness_check` (45-day panel ceiling, share basis), `_materiality_check`, the uncited-material-figure guard, `_refuse_degraded_drawdown_overwrite`, the filed-tiebreak refusal | | | HARD | ruled earlier; the registry lists them so a reader sees every refusal in one place |

## The remaining slices

2. **The gate.** The registry, every check above as FLAG, its results in the run record (run
   record schema 3), and the first-screen FLAG lines. A render change, so a preview from committed
   JSON, collapsed and force-open, and a STOP for approval. Checks 1 and 2 first: they need only
   this record.
3. **Elsewhere.** `checkable` and `not_checkable`. The #889 helpers re-keyed on the record's full
   sha256. CI reports the CIQ-dependent per-page cases as `not_checkable` by name and count,
   instead of 501 skips.
4. **The corpus job.** `vinci dossier checks --all`, its output carried in the PR body of any
   check change.
5. **Refresh writers record their reads.** A layer refresh (`ev_bridge_transform`,
   `forward_multiple_history_transform`, `historical_forecast_error_transform`,
   `ciq_currency_transform`) reads CIQ exports after the build. Each should append what it read to
   the page's record, marked as the refresh's. Today a refreshed page's record names only its
   build's inputs.
6. **G's shared store.** Once the R2 bucket exists (row 32 (30)), a page's inputs are fetched by
   these hashes. A CIQ export's sha256 and a response's `response_sha256` are the keys.

**HOW VERIFIED.** Real runs at $0 on 2026-11-05, every one on this branch. Runs 1–6 were made at
`f610675f` and earlier, under the round-0 rules, and their ids are not comparable with run 7's: the
id now hashes distinct responses and its tuples changed (review round 2). Sources:
- CIQ: the assembler's copy (`mosaic-theory-ta`) for the precheck runs, and a scratch copy of the
  operator's Drive folder (the held names removed) for the cohort build.
- SEC and Polygon: an APFS clone of the assembler's HTTP cache.
- Prices: a clone of its store.
- Nothing was paid, and nothing under `data/dossiers/` was written except by the backfill.

1. **`vinci dossier precheck --ticker GOOGL --inputs-json …`, three times.**
   - Each run: 0 regressions, 0 post-spend refusals; 111 s.
   - **Run 1** read 11 CIQ exports, 1,080 responses (sec 1,064, polygon 14, efts 1, finra 1) and
     15 price series: `inputs-c187737a460eba8a`.
     - Its record carried 48 copies fetched DURING the run: the cache's one-day TTL refreshed
       Polygon's reference pages, eleven companyfacts, the submissions document and new filings.
     - One URL appears twice, in two versions.
   - **Runs 2 and 3** read the refreshed copies: 1,079 responses, both
     **`inputs-61f9ab71f8be35d5`**. The same inputs give the same id, and inputs that moved give
     another, with the record saying which moved.
   - **The census fix.** Run 1 also found a defect this PR then fixed. The precheck's own stamp
     census walks every key ending `sha256`, so it listed the backfilled full hashes as two extra
     stamps, "NOT on disk". It now leaves the record out (`_stamps`, pinned on every committed
     page). Run 2's census reads `9a120cb5ae ×3 (on disk); f494e7869b ×8 (on disk)`.
2. **`vinci dossier precheck --ticker AMZN`** — the record catching a moved input.
   - The assembler's copy holds AMZN exports `e10ed62223` / `e5abf9d69d`; the page was built from
     Drive's `1b971fda50` / `796a53f316`.
   - The field comparison reads **0 regressions**: presence did not move.
   - The INPUTS block reads, abridged to its two lines: `ciq: 0 same, 2 changed, 0 only on the
     page, 7 only here` and `changed: estimates, financials/quarterly`.
   - 565 responses, 24 price series; 172 s.
3. **A real `assemble_cohort(…, llm=None)` for GOOGL into a scratch data dir** (its `dossiers/`
   and `snapshots/` copies, never the worktree's).
   - **First try: REFUSED** by `_refuse_synthesis_overwrite`, since a mechanical-only build may not
     replace a committed synthesis. Its run record (schema 2) carries the full record: 11 CIQ
     exports, 1,077 responses, 15 series, nothing unrecorded, `inputs-438fe66b53fdd293`; a
     306,768-byte line. **A refusal now says what it read.**
   - **With the scratch copy of the page removed, WRITTEN.**
     - The page's block: `recorded: build`; 11 CIQ exports; 11 responses listed
       (`fact_layer_sources`) of a digest over 1,077; 15 series; 0 unrecorded.
     - The run record's block: the same, with all 1,077 listed.
     - **The same `inputs_id` and digest on both, and the same id the refused build carried.**
   - 1,077 responses here against the precheck's 1,079: the two the precheck reads beyond the
     build are the 2026-03-30 10-Q's index and document (`…/000165204426000031/`), which its
     covenant FORECAST fetches as the paid build's covenant phase does; a build with no LLM client
     skips that phase.
   - Of the eleven companyfacts responses, one — the response for NFLX, read as a comparable — is
     sealed by `edgar-4f3207f4da9fb71a`, the 26-entity pages snapshot. The other ten, GOOGL's own included, were refetched on 2026-11-05, after the
     snapshot's 2026-10-27 ingest. That is the fact layer's 2b freshness gap, per page.
4. **The backfill**: `vinci dossier inputs-backfill --all --exclude BURL` with the four roots
   (assembler's copy + archive, Drive + archive), dry run, then `--write`.
   - **The stamps, as first run.** 26 pages, 50 key stamps resolved. *Corrected in review round
     2:* that counted only keys ending `sha256`. Four pages also stamp an export inside an anchor
     input's source string (`CiqBridge.stamp`, `<file> sha <10 hex>`), which the first backfill
     never read: TECX's quarterly Financials (`dce450e41b`, `anchor.net_debt.source`) and the
     annual Financials of GOOGL (`482debf275`, `anchor.d_and_a.source`), CNXC (`e96007d828`, the
     same) and LLY (`0fa91cd481`, `anchor.ltm_fcf.source`). The population was 54 distinct stamps,
     50 resolved and 4 never attempted; run 7 resolves all 54.
   - **The diff.** 26 `dossier.json` files and their 26 `frontend/dossiers/` mirrors: +2,878 lines,
     0 deleted. No `dossier.md` changed.
   - **Roots.** With the assembler's copy alone, LLY's two stamps resolve nowhere (its pages were
     built from Drive). That is why the four roots are named.
   - **Deterministic.** A fresh backfill of every page as committed at `HEAD` gives the written
     bytes: 26 of 26 identical. (A second `--write` then kept every record; since round 2 it
     re-backfills a backfill's record, and writes the same bytes.)
   - No page carries two exports of one kind (proposed check 2: 0 of 26).
5. **Mutation** (`PYTHONDONTWRITEBYTECODE=1`, `__pycache__` cleared, each restored). 10 mutants
   against `tests/test_input_manifest.py`, 10 killed:
   - a response not recorded;
   - a stamp resolved to any file;
   - redaction off;
   - an incomplete record keeping its id;
   - a refused build recording nothing;
   - a recorder not nested;
   - the page keeping every response;
   - the census reading the record's hashes;
   - the store not recording a series;
   - a series hashed without its `source` column. This one SURVIVED first: a bar whose only change
     is `+refiled:` now changes the identity, pinned.
6. **The suite at `f610675f`** (superseded by run 7's), with run C's environment in this
   worktree.
   - ruff and `mypy --strict` are clean (187 files).
   - `pytest -m "not network"`: 9,214 passed, 112 skipped, **4 failed — run C's 4 on main, none
     new**.
   - 24 new ids: 23 in `test_input_manifest.py`, and 1 from the record-hygiene test, which reads
     this record.
   - 2 of run C's skips pass here. Both read `frontend/snapshots/`, which the backfill's
     `frontend/build.py` run generated (git-ignored); that is environment, not code.
   - The first gate run on this branch found 3 failures that are now fixed:
     - the monitor's import fence (the models now live apart, above);
     - the extraction-version drift pin (the version row, above);
     - the §5.0 owner cell's format.
7. **Re-run after review round 2** (the code at the round-2 head; CIQ from the scratch Drive copy
   with the held names removed, cache and store as above).
   - **The backfill** with the same four roots: 26 pages, 54 of 54 distinct stamps resolved.
     - CNXC, GOOGL, LLY and TECX gain the export their anchor string stamps.
     - AMZN, IT, ORKA and UBER gain the string sites that repeat a key stamp.
     - Every page's block changes form (`covers`, `not_covered`, the sorted `unrecorded`), and only
       its block: 26/26 pages equal outside it, key order kept.
     - A fresh backfill reproduces the written bytes, 26/26; each mirror equals its page; BURL's
       page is untouched.
     - `--all` without `--exclude` is refused.
   - **`precheck --ticker GOOGL`, twice.** Both runs: 0 regressions, 0 post-spend refusals, 11 CIQ
     exports, 1,079 responses, 15 price series — and **both `inputs-a35469e571d905aa`**. The
     census now reads `482debf275 ×1 (on disk); 9a120cb5ae ×3 (on disk); f494e7869b ×8 (on
     disk)`, and `ciq: 3 same` against the corrected record.
   - **Mutation.** The reviewer's eight survivors and this round's nine fixes, 17 mutants against
     `tests/test_input_manifest.py` on the corrected corpus: 17 killed, each by its own pin.
   - **Fails first.** The round-2 test file, run against `ed20e835`: every test of a fixed
     behaviour fails there. The pins written for the reviewer's surviving mutants pass there,
     because the behaviour they pin already worked: the backfill's pre-write refusal, the
     finalist's and the resolver's reads, and two redaction shapes.
   - **The gate**: ⟨GATE-R2⟩.

**BOUNDARY.**
- Commit: every count is on main `097098f9` or this branch on top of it, 2026-11-05.
- Population: the 27 committed pages minus the held one (26), unless a row says 27. The suite's
  population is 9,314 collected ids.
- The backfill searched four roots, each by name only:
  - the assembler's CIQ copy and its `ciq-archive`;
  - the operator's Drive CIQ folder and its `ciq-archive`.
- Unit: a response is one cache entry (a URL, or a POST cache key), and a series is one internal
  id.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Run records grow by about 0.3 MB per build** (GOOGL: 306 KB on one line; AMZN's 565
  responses about half that). A 17-page artifact pass adds about 5 MB uncompressed to
  `data/snapshots/assembly_runs/`. Accepted while G's shared store does not exist.
  *Falsifier:* the directory passing 50 MB, the fact layer's stopgap line. Then the full lists
  move to R2 under their `inputs_id` and the run record keeps the digest.
- **A page grows by its block**: 1,876–2,909 bytes backfilled (26 pages, the block's bytes in
  the committed file, after round 2; 1.8–2.8 KiB), about 10 KB built (GOOGL's cohort build).
- **Hashing cost**: every response text read is hashed once per fetched copy (GOOGL: 51.6 MB of
  text), and every series' rows once. Not measured apart from the build: the precheck took 111 s
  with it, against no baseline taken without it.
- **`dossier.md` is unchanged and nothing renders.** A human sees no input record until slice 2's
  FLAG lines.
- **Accepted: a backfilled page's record is partial by construction.** `responses` and `prices`
  are `unrecorded` on all 26, and so is every export the page never stamped (comps, transcripts,
  capital structure, and the annual Financials except on CNXC, GOOGL and LLY, whose anchors stamp
  it). Only a re-assembly records them.
- **Accepted: refresh writers do not yet record their reads** (slice 5). A page a layer refresh
  moves still names only its build's inputs.
- **Found and reported, not changed (scope):**
  - the suite reads the held page's export when a CIQ folder is linked (above; the coordinator
    is taking it to the operator);
  - `compare` keys a series by `newest_bar` and `rows_sha256`, so the precheck reads a store that
    only appended bars as "changed". Slice 3's `checkable` re-hashes through the recorded
    `newest_bar` instead.
- **Review round 0** (`/code-review high --fix`): 7 findings — 4 FIXED, 3 SKIPPED, each listed in
  the PR's dispositions table.
- **Review round 1** (an in-session `/code-review high`, as Codex failed on its usage limit):
  6 findings, 4 FIXED behind tests that failed first, 2 DISMISSED.
  - A record that cannot be built no longer costs the run record its line.
  - A fact-layer manifest that cannot be read is `unrecorded` (`responses:sealed_by`) rather than
    refusing a build after its paid phases.
  - An unhashable export's reason carries no local path.
  - The `stamps` docstring now states its 10-hex rule.
- **Review round 2** (the coordinator's review of `ed20e835`, the last round): 19 items. Each has
  a row in the PR's dispositions table. Two are DEFERRED, and they are in STATE row 48's open list:
  - no test runs a REAL build's record end to end. It needs the licensed exports, so it is slice
    3's `not_checkable`; the real runs above stand in for it;
  - `Store.get_security`'s rows are not recorded. They are named in `not_covered` instead of being
    hooked as a fourth class.
