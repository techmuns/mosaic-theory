---
status: shipped
date: 2026-11-19
prs: [1141]
supersedes:
superseded-by:
---

# Theme intelligence sends its independent model calls eight at once, and only the enrichment pass has any: a document's own calls are a chain, so an upload is no faster

**WHAT.** The operator asked on 2026-11-19 for the theme desk to run faster "without affecting
or without compromising the quality". This build maps every paid call and changes three things.
- **The spend guard reserves** (`vinci/theme_intelligence/budget.py`). A call is admitted only if
  its bound fits what is left once every call in flight is counted at its own bound. It holds that
  bound until the call settles at its actual cost. Calls in flight together can never jointly
  pass a run's or a document's limit. Each item of a concurrent pass draws on its own document
  (`SpendGuard.scope`). When the RUN's budget is what refuses, the pass first waits for the calls
  in flight (`reserve(make_room=)`), so it refuses exactly the call one-at-a-time would refuse.
  The guard's ledger rows are written at admission, in input order. **Both claims assume each
  call costs no more than its bound**, the guard's own premise: a call that costs more overruns
  alone or beside others, and `summary()` counts such calls (`calls_over_their_bound`).
- **The enrichment pass sends up to 8 calls at once** (`Pipeline._enrich_theses`; `enrich.py`
  split into `enrichment_request`, `ask_enrichment`, `enrichment_from`). Everything else stays on
  one thread, in input order: the registry reads, each call's admission, and, as each answer's
  turn comes, the SEC checks, the ledger row and the stored set. `enrich_thesis` is the same
  three steps in a row, for every other caller.
- **The setting.** `config.LLM_WORKERS = 8`, `Pipeline(llm_workers=)`, `--llm-workers` on `scan`,
  `enrich` and `reanalyse`. It applies only to a client that keeps each call's usage on its own
  thread (`ThemeLlmClient.usage_per_thread`). Any other client is sent one call at a time.

No prompt, model, tool schema, cache key or stored field changed.

**THE CALL MAP** (read 2026-11-19 at main `377bfe86`). A call is INDEPENDENT when its prompt holds
no other call's result and the order of its output does not matter.

| call | per | prompt holds | independent? |
|---|---|---|---|
| extraction, pass 1 (`extract.run_extraction`) | document, 1 | the registry's thesis keys (`_registry_context`), changed by every earlier document's engine run | **no**, across documents |
| compact re-extraction | document, only after the full one truncates | its own trigger is the first call's failure | **no** |
| completeness, pass 1b (`completeness.run_completeness`) | document, 1 or N parts of 50 gaps | the extraction; part *k* also gets parts 1…*k*−1's additions (`merge_completeness(x, _concat(outputs))`), and is skipped if they covered its gaps; a split half sees the half before it | **no**, a chain |
| `reask-part` | one part, by hand | that part's identical request | n/a (one call) |
| card review, pass 2 (`verify.review_card`) | thesis, 1–2, inside `Engine.apply` | the card the engine just built from the registry; the re-review is built from the first review's anchors | **no**: the engine is the registry's one writer |
| enrichment (`enrich.py`) | active thesis, 1 | that thesis's own card only (`user_message`) | **YES** |

"Per-figure verification" and "per-chunk extraction" have no model call. `verify_extraction` is
deterministic, and a document is extracted in ONE call. **Phase 2 (documents of one batch in
parallel) is NOT clean:** document *k+1*'s extraction prompt lists the theses documents 1…*k*
created. On 2026-11-19, TH-1838CDDC15 was matched by three of the eight uploads through that
list. Freezing the list at the batch start would change prompts, so it is left out.

**WHY.** Measured on the 2026-11-19 runs (local registry, `llm_calls.seconds`):
- **The Macro Outlook upload** (R-20261119T122245Z-ingest) took 1,427 s wall, 1,413.1 s of it in
  34 model calls: 19 completeness parts 898.4 s, 14 reviews 323.5 s, 1 extraction 191.1 s. Every
  one is a link of a chain, so an upload is not faster.
- **The weekly scan** (R-20261119T090734Z-scan, 1,372 s wall, 1,126 s model time) spent 101.1 s
  on 9 enrichment calls. That is the time this build removes.

**HOW VERIFIED.** At $0: no paid call, and every replay ran on a scratch data folder (never
`~/dev/mosaic-theory/data/theme_intelligence`). The scripts and their output are in the session
notes (`ti-concurrency-proof/`, outside the repo).

- **Replay A: three real uploads, real answers.** Each ran end to end on a scratch copy of the
  registry backup taken just before that upload. A RECORDED client answered each call with the
  answer the real run got for exactly that request (its cache file), with the real usage.
  - A request the real run never made would fail loud. None did.
  - The SEC was read offline from a copy of the primary's cache: 0 misses.
  - Bond Supply (9 calls, $1.9895), Macro Outlook (34 calls, $10.6432) and Markets Outlook (21
    calls, $3.9721) match the real runs' call counts and costs.
  - Main `377bfe86`, this branch with 1 worker and this branch with 8 wrote the same rows: 209,
    706 and 399 rows in 19 tables, one digest per document across the three.
  - Normalised: clock readings, durations, the SDK stamp, the scratch folder, and the ids and
    hashes that cover a clock are masked.
  - Against the REAL runs' own rows (backup after minus backup before), 22 of the 25 tables are
    identical. The other three differ in the file's name and folder (the replay copied it under
    its hash), in the state pull's migration stamps, and in one row the Macro upload's own state
    pull rewrote.
  - Macro and Markets were replayed as new (`force_new`). The real Markets upload was
    `--as-new`. The real Macro one read as new, but today the identity check on that backup holds
    it for REVIEW. Not investigated here (see FOUND, NOT FIXED).
- **Replay B: enrichment over the real registry.** 74 active theses, their real cards as the
  requests. The answers are a STAND-IN, a fixed function of each request: when this replay ran,
  no recorded enrichment answer was held on this machine (they live in the weekly job's Actions
  cache). SEC offline: 9 misses, the same in every run.
  - Main, 1 worker and 8 workers wrote identical output text, sets (in write order), ledger
    rows, cache files and run records.
  - CORRECTION (coordinator A's review, 2026-11-19): 14 REAL enrichment answers were written to
    the primary's `llm_cache/enrich` at 20:25–20:30 local time, after this replay. A's review
    replayed them at main, 1 worker and 8 workers: identical digests, and the ledger identical in
    rowid order.
- **Tests** (`tests/test_theme_intelligence_concurrency.py`, 10). Each was shown failing on the
  version it pins:
  - eight threads against a limit that holds three bounds: main's guard sent all 8 at once
    (`assert 8 == 3`), the reserving guard 3;
  - one-at-a-time and 8 workers give equal records with answers arriving last-first. It fails
    against a loop that writes answers as they COMPLETE;
  - the run budget binds at the 5th of 5 calls costing ~80% of their bound. It fails against
    admission on reservations alone (no `make_room`), which stopped one thesis early;
  - a billed failure on thesis 2 is raised at its turn, with thesis 1 written and nothing after
    it. Calls already sent for theses 3–5 are recorded and cached, and a re-run pays only for
    thesis 2. It fails against a "best effort" loop that skips failures;
  - a client without per-thread usage gets one call at a time;
  - (round 1) `[t0, t1, t0]` with t0 slowest: the second t0 reads its first turn's set ("already
    proposed … skipped"). It fails against mutant M3 of A's review, which drops the wait;
  - (round 1) three calls with EQUAL usage, the middle failing and the last answering first:
    each unused paid call is recorded under its own thesis. It fails against matching by usage
    alone, which recorded the last one's call under the first thesis's name (`recorded()` now
    matches the document's label too);
  - plus the reservation unit, the `make_room` unit, and the CLI flag.
- **Suite:** ruff, `mypy --strict` and the full offline suite are green.

**SPEED** (delay client: each call sleeps a fixed time). These are MODEL time. The stand-in
answers need ~0 s of SEC checks, and those stay serial on the main thread. On the 14 REAL
answers, A's review measured the serial SEC checks alone at 63.6 s with 1 worker and 48.7 s
with 8. So the 6.9× below is the speed-up of the model calls, not of the pass's wall time.
- **The enrichment pass:**

  | pass | 1 worker | 8 workers | main |
  |---|---|---|---|
  | 74 theses, 1.128 s a call | 86.9 s | 12.6 s | 86.1 s |
  | 9 theses, 11.28 s a call | 102.7 s | 23.7 s | — |

  11.28 s is the mean of the 111 real paid enrichment calls on record (5.73 to 18.14 s). The
  second row is the size of the 2026-11-19 scan's step. It saves ~79 s of its 1,372 s run.
- **The Macro Outlook-sized case**, its real call times scaled ×0.02: main 40.0 s, 1 worker 39.5 s,
  8 workers 39.8 s. **No speed-up, by the map.**

**BOUNDARY.**
- **Call times:** the local registry copied 2026-11-19 ~14:10 UTC (runs R-20261119T090734Z-scan
  and R-20261119T12–13*-ingest), non-cached rows, seconds as recorded.
- **"111 real enrichment calls":** every non-cached enrich row with seconds > 0 in that registry.
- **"74 active theses":** status ACTIVE in that copy.
- **Replays:** code at main `377bfe86` and this branch, 2026-11-19.
- **Timings:** wall clock on one Mac with nothing else running. Sleeps dominate them, so they
  measure overlap, not this machine.
- **A run's `llm_seconds`** is the SUM of its calls' own seconds, so with calls sent at once it can
  exceed the run's wall time (`schemas.WeeklyRun`).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A failed call, or an interrupt, can leave up to 7 calls already sent and paid.** One-at-a-time
  would not have sent them, so concurrency never lets the spend pass a limit, but it is not
  spend-neutral on that path. Each is recorded (`enrichment-unrecorded`) and its answer cached, so a re-run takes
  it at $0.
- **Rate limits were never measured for 8 enrichment calls at once on this key.** The SDK
  retries a 429 or 529 twice. FALSIFIER: an enrichment step's run warns "enrichment not run" with
  a rate-limit error. Then lower `--llm-workers`.
- **OPEN, for the operator:** the three levers that WOULD speed an upload, each a change of design:
  - completeness parts asked without the earlier parts' additions: a prompt change, 63% of
    Macro's model time;
  - card reviews made outside the engine's write loop: an engine change, 23%;
  - one registry list frozen per batch: a prompt change across documents.

  Each needs a ruling and a quality measurement first (STATE §5.0 row 32, item (35)).

**FOUND, NOT FIXED** (out of scope here; each a STATE §5.0 row 32 item).
- **The cross-setup check's theme-desk consumer fails on a WAL-mode registry**
  (`vinci/impact/run.py` `run_consumer`). Snapshotting the `--theme-data` folder's `registry.db`
  for the base side leaves `registry.db-wal` and `-shm` beside the SOURCE. The head side then
  symlinks every other entry of that folder, these two included, beside its own copy, and SQLite
  cannot open it: head exits 1 with `unable to open database file`, and the consumer reads
  DIFFERS. Seen on this PR's first impact run. Workaround used: `PRAGMA journal_mode=DELETE` on
  the copy passed. Fix: skip `-wal` / `-shm` / `-journal` when linking. Row 32, item (36).
- **The identity check holds the Goldman Sachs Macro Outlook for REVIEW** on its pre-upload backup:
  an uncertain match to the Bond Supply note, title overlap 6%, 56% of the held text found in
  the new document. The real upload read it as new. Two candidate causes, neither verified. The
  56% fits row 32 item (8)'s open note, "the identity check counts a publisher's legal footer as
  argument text" (Goldman's shared disclosure pages). Why the real upload did not match is
  possibly that the one-step upload's state pull held no article text to compare. Linked there.
