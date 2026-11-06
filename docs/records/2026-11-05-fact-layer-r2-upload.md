---
id: 2026-11-05-fact-layer-r2-upload
status: open
date: 2026-11-05
prs: [912, 913]
supersedes:
superseded-by:
---

# The fact layer's R2 location: both snapshots are uploaded and every object read back against its sha256, a reader on a clean location reads them from the bucket by the committed manifests, and validate-keys pings the bucket (closes STATE row 32, item (30))

**WHAT.** The "THEN the agent writes the upload path" step of STATE row 32 (30). The operator
approved it on 2026-11-05 ("Yes, start it"), after creating the bucket and putting its four values
(`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`) in this Mac's `.env` and
in the repo's Actions secrets.

- **`r2://` is a reader's location** (`$VINCI_FACTS_STORE`, `--store`, `FactStore(root=…)`). It
  names the bucket the four variables configure, and nothing may follow the scheme (the bucket is
  `$R2_BUCKET`). A missing variable raises `R2NotConfiguredError` naming the VARIABLE. A reader
  fetches each object it touches into a local cache (`$VINCI_FACTS_CACHE`, else the git-ignored
  `data/cache/facts`) by its manifest entry and hashes it before use. A key the bucket lacks
  raises `RemoteObjectMissingError`; bytes that do not hash to the entry raise; a cached copy that
  does not hash is fetched again. There is no fallback between locations: the committed objects can
  be on disk and `r2://` still never reads them.
- **A writer never writes to `r2://`.** `store_root` (where an ingest writes) refuses it: an ingest
  writes a local directory, and `python -m vinci.facts upload --name <pages|screen> --exclude …`
  copies a snapshot up from the machine that wrote it.
- **Immutable remotely, as locally.** The key is the manifest's path, so two snapshots that share
  a partition share one key. Each PUT sends `If-None-Match: *`, which R2 evaluates atomically
  (Cloudflare's S3 API page, updated 2026-10-14: "at most one succeeds"), the body's `Content-MD5`
  (R2 refuses a body that does not match it) and the body's sha256 in the signature. When a key
  exists, its bytes are read back: the same bytes are a no-op, other bytes raise
  `RemoteBytesDifferError` and are never overwritten. After an upload every object is read back and
  hashed against the manifest.
- **Only sealed bytes go up, and only the manifest's.** The upload verifies the local copy against
  the manifest (presence, size, sha256, rows, schema) before any request, and reads objects from
  the manifest's entries, never by listing the directory. Every path is checked to be a
  content-addressed key before it is joined to a directory or sent (round 0).
- **The held names.** The ingest's `--exclude` carries to the upload
  (`scope.require_upload_exclusions`, before any request): it refuses fewer names than the snapshot
  and every current snapshot of its source were written excluding, and it refuses if any company in
  the snapshot carries a ticker on the list. Each refusal names counts, never a name.
- **validate-keys** gains `check_r2`: one signed HeadBucket, PASS/FAIL and the HTTP status only,
  the `padded()` check on all four values, REQUIRED (a missing or refused value turns the run red).
  The workflow passes the four secrets; `.env.example` lists the four names.
- **One writer, read-only readers.** Only `upload` writes. HeadBucket and every read should pass
  with a read-only token, but that is UNTESTED: only this Mac's Read & Write pair was used (round
  2). A token that may not write stops the upload at its first refused PUT (pinned on the fake
  bucket, which refuses every PUT with 403), and counts
  the rest as not attempted.
- **The endpoint is never printed.** Errors name the operation, the key and the status (and S3's
  error code), never a URL; a transport error is re-raised as its type name only. A logging filter
  on the `httpx` and `httpcore.*` loggers (which print each request's URL) replaces the four values.
  `R2Config` and `R2Client` print none of them.
- **No manifest changes.** Where the objects are read from is the reader's choice, not a manifest
  field, so the upload changed no manifest, no `storage` value and no snapshot id. Workstream B
  reuses the ids.

**THE DEPENDENCY: A SIGV4 SIGNER OVER HTTPX, NOT BOTO3.** `vinci/facts/sigv4.py`, 94 lines,
standard library only.
- **For it.**
  - No new core dependency. httpx is already one, so there is no env drift and nothing new in CI's
    install.
  - The fact layer makes four kinds of request (HeadBucket, GetObject, PutObject,
    ListObjectsV2), all of small objects, so there is no multipart. The largest object is an order
    object of the screen snapshot, 71,058 bytes; its largest data object is 39,969. In the pages
    snapshot the largest is an order object of 40,056 bytes (corrected in round 2: the figure first
    given was the largest DATA object).
  - It reproduces AWS's four worked S3 examples byte for byte (`tests/fixtures/facts/sigv4_aws_s3_
    examples.json`). Each example's inputs and signature were read from an independent
    implementation's tests (ytsaurus), because AWS's page renders by script; the first signature
    appears in four more implementations found by a code search for it.
  - validate-keys loads the same file by path, since the workflow installs only anthropic and httpx,
    and a test holds the file to the standard library. The key check signs exactly as the uploads do.
  - It types cleanly under `mypy --strict`.
- **Against it.** It is signing code this repo now owns.
  - Retries (429/5xx, and 409 on a PUT, 4 retries with backoff) are written here rather than
    inherited.
  - An S3 feature beyond these five requests would have to be added by hand.
- **boto3, measured 2026-11-05** (`pip download boto3 --only-binary=:all:`). boto3 1.43.124 is
  7 wheels: 16,836,474 bytes downloaded and 23,081,536 unpacked, botocore alone 20,749,074. None of
  the seven is in the root `.venv` today. It would also need type stubs for `mypy --strict`, and it
  would add a dependency to validate-keys' install line.
- **Env drift, said anyway.** This PR adds no package, so a local suite that is red on it is not
  drift from this change.

**THE COMMITTED STOPGAP PARQUET (the pages snapshot's 379 objects, 6,584,136 bytes) STAYS
COMMITTED.** The ADR said it "moves to R2 when the bucket exists". It is now IN R2, and readers
anywhere can take it from there. Un-tracking it is not done, for three reasons:
- It would not remove anything from public history.
- The manifest's `storage: git` is inside the hashed body, so changing it would give the pages
  snapshot a new id, and workstream B reuses the ids.
- The offline suite reads those objects: `tests/test_facts_contract.py` and the parity pins.

So the cost the ADR guarded against, git growth, is unchanged by this PR. It stays bounded by the
50 MB cap test. Where the NEXT pages snapshot's objects go is part of the open git-growth ruling
(STATE row 44), not taken here.

**HOW VERIFIED.** Every run is on the real bucket, from this Mac, with the four values from the
primary checkout's `.env` (loaded into the process, never printed). All on 2026-11-05, on branch
`claude/fact-layer-r2-upload` off main `097098f9`.

1. **validate-keys:** `check_r2` printed `R2: PASS — HeadBucket HTTP 200`. That was the R2 check
   alone: the script's other checks call Anthropic, Polygon, Tiingo and SEC, and SEC is not
   probed.
2. **Upload: pages** (`edgar-4f3207f4da9fb71a`, from the committed `data/facts/objects`).
   - 379 objects named (353 data + 26 order), 6,584,136 bytes.
   - Written 379 (6,584,136 bytes); already there 0.
   - Read back and hashed against the manifest: 379 of 379; 0 problems. 23.4 s.
3. **Upload: screen** (`edgar-6e0e4626855b9fce`, from
   the lasting directory outside every worktree that `$VINCI_FACTS_STORE` names (STATE row 44), `--workers 32`).
   - 22,359 objects named (20,667 data + 1,692 order), 388,278,069 bytes.
   - Written 22,180 (385,338,653 bytes). Already there with the same bytes: 179 (2,939,416
     bytes), the objects the pages snapshot shares with it.
   - Read back and hashed against the manifest: 22,359 of 22,359; 0 problems. 11 min 3 s
     (06:34:25–06:45:28 UTC).
4. **The bucket against both committed manifests,** listed after the screen upload.
   - 22,559 keys, 391,922,789 bytes: exactly the 22,559 distinct objects the two manifests name.
   - 0 keys named by no manifest, so nothing a manifest excludes (a held name's objects included)
     is in the bucket.
   - 0 named objects absent; 0 with a size other than the manifest's.
5. **The live guards,** on the pages objects already in the bucket.
   - A second pages upload wrote 0 and found 379 of 379 already there with the same bytes. Each
     PUT came back 412, so R2 honours `If-None-Match: *`; all 379 read back clean.
   - A PUT of different bytes under an existing key was refused with `RemoteBytesDifferError`, and
     the key still held its sealed 9,592 bytes. The `If-None-Match` proof in the bullet above is
     what made this probe safe to run.
   - A fetch of a key the bucket lacks raised `RemoteObjectMissingError`; a fetch whose entry
     states another sha256 raised. Neither wrote to the cache.
   - An upload passed five exclusions where the snapshot was written with six: refused before any
     request, naming counts only.
6. **A reader on a clean location.** A copy of the branch's own files only (`git ls-files -co
   --exclude-standard`): no `.env`, no `data/cache`, no local store, and its committed
   `data/facts/objects` DELETED, so the pages snapshot too could come only from R2. The
   primary checkout's SEC cache was read, read-only, for the references.
   - **`verify --store r2://` on both, from an empty cache.** pages: 379 objects fetched (6,584,136
     bytes). screen: 22,180 fetched (385,338,653 bytes), and 179 already cached by the pages run.
     Each was hashed against its entry, then deep-verified: its rows hash to its name, and every
     order object maps every row. 0 problems on either. 12.8 s and 7 min 48 s.
   - **Parity through R2.** `parity --store r2://` over the 130 page-cuts slice 1 defined (each
     page's price date, 2020-06-30, 2023-12-31, 2025-06-30, and each page's filing eve; the held
     names passed as `--exclude`): 130 compared, 130 zero-diff. 2 min 4 s.
   - **The screen replay through R2.** `screen-replay --store r2:// --run 2026-10-16-01
     --filing-eve` (12 min 38 s).

     | cut | names | rows compared | row diffs | order diffs | fields compared | field mismatches |
     |---|--:|--:|--:|--:|--:|--:|
     | price date | 2,064 (434 reached G3) | 28,089,606 | 0 | 0 | 32,148 | 0 |
     | filing eve | 2,064 (434 reached G3) | 27,590,689 | 0 | 0 | 32,148 | 0 |

     744 name-cuts were unread: the 372 names not in the SEC cache, at both cuts, as in slice 2a.
     None was unread that the snapshot does not name unread.
7. **Tests.** `tests/test_facts_remote.py` holds 37 tests (39 cases, one parametrized over three
   statuses) after round 2.
   - The signer reproduces AWS's four examples; the secret, day, region and path each change the
     signature; the signer imports only the standard library.
   - The rest run the REAL committed pages snapshot through a fake bucket (an
     `httpx.MockTransport` that keeps S3's If-None-Match, Content-MD5, payload-hash and
     ListObjectsV2-paging rules):
     - upload once, then again (0 written);
     - other bytes under a key refused and kept;
     - a body changed after its digest, caught by the read-back;
     - an unsealed local copy sends nothing;
     - a token the fake bucket refuses writes to stops at its first PUT;
     - a reader with an empty cache reads all 26 companies identically to the committed objects;
     - a missing or altered remote object raises, with no fallback;
     - a corrupted cache copy is fetched again;
     - a manifest path that is not a key is never used;
     - the bucket is listed across pages;
     - both exclusion refusals, including the CLI before any request;
     - the location rules;
     - no value in a repr, an error or the request log;
     - validate-keys on 200/403/404, unset and padded values, the run's verdict, and its loading
       of the same signer.

   Two existing pins changed:
   - `test_facts_naming`'s fail-loud message: it said "not shared until R2", now false.
   - The Tiingo verdict test stubs every check, now including `check_r2`.
8. **Mutation.** 15 mutants of the new filters (the two exclusion checks, If-None-Match, the 412
   compare, the fetch hash, the read-back hash, the local pre-verify, the stop on a refused
   request, the log filter, the padded config, the `r2://` suffix rule, the reader's fetch, the key
   check, validate-keys' padded check and its verdict). Each is caught by 1–3 tests and was
   restored with its sha256 checked (`PYTHONDONTWRITEBYTECODE=1`, `__pycache__` cleared).

**BOUNDARY.**
- **Population.** The two committed manifests at main `097098f9`:
  - pages `edgar-4f3207f4da9fb71a`: 26 companies, 353 data + 26 order objects;
  - screen `edgar-6e0e4626855b9fce`: 1,692 companies, 20,667 data + 1,692 order objects.
  - They share 179 objects, so 22,559 are distinct (391,922,789 bytes).
- **Unit.** An object is one Parquet file under one key. Bytes are the file's size as the manifest
  states it.
- **Window.** The bucket's whole contents at each listing (no prefix).
- **When.** 2026-11-05, 06:33–06:45 UTC for the uploads.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The bucket's free tier.** These uploads cost about 22.6k Class A PUTs plus a few dozen list
  calls, and about 45k Class B GETs, against a monthly 1M Class A and 10M Class B. Storage is
  0.39 GB against 10 GB-month.
- **This Mac holds the only write token** (the operator was advised Read & Write in `.env`, Read
  only in GitHub; which they chose is not tested here). If CI holds the write pair, nothing in CI
  writes: only `upload` does, and no workflow runs it.
- **Three round-0 findings SKIPPED,** each real and none affecting correctness:
  - **A PUT that lands but answers 5xx or times out** is retried, gets 412, and is counted
    "already there", not "written". Every object is still read back against its sha256.
    *Falsifier:* `written + present` ≠ the objects named.
  - **Thread-local `httpx.Client`s:** each worker pool opens its own, at most 2× workers for the
    length of one command. Sharing one would lean on a thread-safety guarantee not checked here.
  - **`FactStore` over `r2://` fetches one object at a time** on first touch. A whole-snapshot read
    from a cold cache should run `verify --store r2://` first, which fetches in parallel.
- **Review round 1** (an in-session `/code-review high`: Codex failed on its usage limit). Five
  findings: 2 FIXED, each behind a test that failed on the PR head, and 3 DISMISSED.
  - FIXED: the upload's bucket audit raised, AFTER a finished upload, on a manifest
    `load_manifest` refuses. It now counts that manifest as not read. The live re-run printed
    "against the 2 committed manifests it reads (0 manifests not read …)": 22,559 keys, the same
    22,559 objects.
  - FIXED: a listing that is not S3's XML raised `ParseError`. It is now an `R2RequestError`
    naming the operation.
  - DISMISSED, each with its reason in the PR's table: the audit's population is printed beside
    its counts; a failed fetch is listed twice by `verify --store r2://`, both lists labelled and
    the exit status right; there is one log filter per distinct configuration.
- **Review round 2** (the coordinator's review of `d4177d47`, the last allowed round). Four
  guards were unpinned: each survived its mutant over `tests/test_facts_remote.py`,
  `test_facts_layer.py` and `test_facts_naming.py` (99 tests then).
  - Every corruption fixture had changed the object's SIZE, so a length compare could stand in
    for the sha256 at the fetch, the read-back, the 412 compare and the cached copy. Each is now
    pinned with a same-size bit flip.
  - The loop that holds an upload to every CURRENT snapshot's exclusion count, and the snapshot's
    own count, are pinned. That loop is the case of an old manifest written with no exclusion.
  - The fake bucket now re-signs every request it receives (method, raw path and query as sent,
    the headers it says it signed, the body's own hash) and refuses a mismatch with 403
    SignatureDoesNotMatch. A client signing one path or query and sending another had passed.
  - Pinned too: the re-hash inside each PUT, a retried 503, a truncated listing with no token,
    the account-id format, and the write to a temporary file renamed into place.

  The real defects, each behind a test that FAILED on `d4177d47`:
  - The bucket audit never affected the exit status. A key no committed manifest names, or a
    named key of another size, now fails the run. Named-and-absent does not, since a committed
    manifest may not have been uploaded yet.
  - A cache write that failed (disk full on the 388 MB pull) escaped `fetch_all` as an OSError
    and left its temporary file. It is now a counted error, and the file is removed.
  - An httpx error that is not a transport error (`DecodingError`) escaped `_request` with the
    URL, and so the ACCOUNT ID, in its message. It is now retried and reported by type only.
  - A value copied unedited from `.env.example` (each begins `replace-with-`) passed `from_env`
    and made five signed attempts at a host that does not exist. It is now refused by the
    variable's name, as `config.sec_user_agent` refuses its own placeholder.

  The docstring of `require_upload_exclusions` now states its limit: it is a count check plus a
  match on the names PASSED, so as many invented names pass it.

  18 mutants: the 4 surviving classes above, the 5 small guards, and one for each new fix. All
  18 were caught and restored with their sha256 checked.
- **NOT DECIDED HERE** (open operator rulings):
  - the manifest growth policy (the ADR's open item; STATE row 44);
  - slice 2b.
## Amendments

**2026-11-06 — "The held names" bullet above is REMOVED.** The operator lifted the hold on
2026-11-05: *"i dont want mosaic theory to hold back any names for teamnostra repo, its two
separate setups"*. `scope.require_upload_exclusions` is gone, and `upload` no longer takes
`--exclude`: a snapshot goes up whole, and a copied command that passes the flag is refused before
any request. Every other guard here stands, and its pins still catch their mutants (read-back hash,
bucket audit). Record: `docs/records/2026-11-06-the-fact-layer-holds-back-no-name.md`.
