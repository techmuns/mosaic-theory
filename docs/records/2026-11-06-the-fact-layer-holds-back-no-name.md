---
status: open
date: 2026-11-06
prs: []
supersedes:
superseded-by:
---

# The fact layer holds back no name: ingest and upload take no exclusion list, a copied `--exclude` is refused before anything is read, and new manifests state both exclusion counts as 0 (closes STATE row 50)

**THE RULING.** The operator, 2026-11-05, verbatim: *"i dont want mosaic theory to hold back any
names for teamnostra repo, its two separate setups"*
(`docs/records/2026-11-05-mosaic-theory-holds-back-no-name.md`, #919). #919 removed the hold from
`inputs-backfill` and the suite. It left the fact layer's guard alone, because removing it changes
the fact layer's ingest, its upload and what future snapshots contain. That guard is STATE row 50,
which this change closes.

**WHAT IS REMOVED.** All of it served the hold. The slice-1 ADR's own heading for it is *"The
held-name exclusion cannot be forgotten"*.
- `vinci/facts/scope.py` **`require_exclusions`**. Before anything was read, it refused an ingest
  that passed fewer `--exclude` names than any current snapshot of its source was written with,
  or one that excluded fewer than the same population's snapshot. It also refused when a current
  snapshot stated no count.
- **`require_upload_exclusions`**. Before any request, it refused an upload that passed fewer
  names than the snapshot and every current snapshot were written with. It also refused a
  snapshot that stated no count, and one with a company carrying a listed ticker.
- **`_prior_scope`**, the reader both guards shared.
- **The `exclude` parameter of `screen_scope_names`**. Only the ingest passed it. The function
  now returns `(names, rule)`.
- **`--exclude` on `ingest` and on `upload`.** The flag is removed, not turned into an ordinary
  skip, for two reasons:
  - **A copied command line must fail loudly.** Commands that pass the held names are on record:
    the R2 record gives the upload as `upload --name <pages|screen> --exclude …`, and a working
    note kept outside the repo gives the screen re-ingest as `ingest --scope screen --run
    2026-10-16-01 --exclude` with all six. On main, a copied ingest command is ACCEPTED: it writes
    a permanent public manifest that silently lacks the six, which puts the lifted hold back in
    force. With the flag gone, argparse refuses it (exit 2) before any file is read or any request
    is sent.
  - **Neither command has anything to skip.** An ingest's population is its rule's (the committed
    pages plus the followed names, or one screen run's universe). An upload sends one snapshot
    whole. `inputs-backfill` is different: its skip leaves a page as it was and writes nothing
    about the name, so it keeps the flag (#919).
- Hold wording is gone from the docstrings and `--help` of `scope.py`, `__main__.py`,
  `remote.upload_snapshot` and `screen_replay`.

**WHAT STAYS.**
- **`parity --exclude`, as an ordinary skip.** Parity writes nothing, and the skip is still needed:
  the committed pages snapshot `edgar-4f3207f4da9fb71a` holds neither BURL (it was excluded under
  the hold) nor MCK (its page came after the snapshot, #918). Parity's output now COUNTS what the
  skip leaves out: *"N name(s) of the pages' scope left out by --exclude"*. `inputs-backfill`
  prints its skip the same way. Under the hold the output said nothing about these names, because
  a held name was never to be named.
- **Every other upload guard.** These are the local pre-verify, `If-None-Match`, the PUT's
  re-hash, the sha256 read-back, and the bucket audit that fails the run on a key no committed
  manifest names. They are untouched; HOW VERIFIED shows them still caught.

**THE MANIFEST: BOTH FIELDS KEPT, WRITTEN AS 0.** A new manifest's `scope` carries
`excluded_by_operator_instruction: 0` and `exclusions_listed: 0`. These are the same keys the two
committed manifests carry.
- **Why keep them rather than drop them:**
  - `screen_replay.replay_run` reads `excluded_by_operator_instruction`. The population it replays
    is `names_selected` less that count, and the committed screen snapshot needs it (2,065 − 1).
    Dropping the field from new manifests would leave that reader two choices: read an absent
    count as 0, which this repo refuses (the zero-coercion rule), or branch on the field's
    presence.
  - `store.load_manifest` refuses any `manifest_version` other than 2. Marking a shape change with
    a version bump would therefore make both committed manifests unreadable. `scope` is free-form
    inside version 2, so keeping its shape needs no bump.
  - Every manifest, old and new, then has one scope shape.
- **What it costs.** The name `excluded_by_operator_instruction` describes an instruction that no
  longer exists, and in new manifests it is always 0. The comment where the ingest writes it, and
  `scope.py`'s docstring, both say so. *Falsifier:* a new manifest whose count is anything but 0.
  The ingest writes the literal, and two pins fail on any other value.
- **NOT changed:**
  - the snapshot-id derivation (`store.snapshot_id_for`: the sha256 of the canonical body
    without its id). A new snapshot's id moves only because its content does;
  - `MANIFEST_VERSION` (2), `SCHEMA_VERSION` (2) and the schema contract;
  - `vinci/dossier/inputs.py` `sealed_by`. It reads only each manifest's `snapshot_id` and each
    entity's `response_sha256`, never the scope.
- **Committed manifests are not rewritten.** Both still state 1 excluded of a list of 6. That is
  history, and their ids are unchanged.

**NOT DONE.**
- No ingest and no upload was run.
- The six names are in no snapshot. The pages snapshot still lacks BURL, and the screen snapshot
  still lacks the one name it excluded.
- Widening a snapshot's scope is a separate operator decision (fact-layer slice 2b; STATE row 44).
  This change only stops the code requiring a list.

**ALSO REMOVED, AS A SIDE EFFECT.** `_prior_scope` refused an ingest when `current.json` pointed
at a missing manifest, because it read every current snapshot. Nothing at ingest does that now.
The committed tree is still checked in CI: `tests/test_facts_contract.py` holds that
`current.json` resolves. A dangling pointer in an uncommitted store now surfaces at the next
`load_manifest` of that name, which raises *"no manifest"*.

**ALSO RECORDED HERE: THE OPERATOR'S GIT-GROWTH RULING FOR SLICE 2b (2026-11-06).** The ruling,
verbatim: *"Yes, keep newest only"*. This record carries it because the coordinator relayed it to
this change; nothing here implements it.
- **What it means.** 2b's git-growth policy keeps only the NEWEST screen manifest in the repo
  tree. Older screen manifests stay in git history and in R2. The 10.1 MB committed screen
  manifest, `edgar-6e0e4626855b9fce`, is today's newest.
- **Who implements it.** The 2b build, which writes the next screen snapshot.
- **STATE row 44** now reads that item as ruled. Its other two sub-items stay open for 2b to
  propose with numbers: `fetched_at` inside the snapshot id, and `extractor_version` inside every
  object's name.

**HOW VERIFIED.** All on branch `claude/distracted-hellman-b11386`, off main `7a79c091` (#919
merged).
1. **Nine new pins, each failing on main first for the guard's own reason.** The branch's three
   test files were run against main's code in a detached checkout of `7a79c091`.
   - `test_an_ingest_needs_no_exclusion_list`, case "the committed snapshots": the two committed
     manifests are current (each 1 of 6). Main refused with *"told to exclude 0 name(s) … written
     excluding 6"*.
   - The same test, case "a snapshot stating no count": main refused with *"states no exclusion
     count"*.
   - `test_an_ingest_given_exclude_fails_loud_and_writes_nothing`: main accepted the flag (*DID NOT
     RAISE SystemExit*) and wrote a snapshot.
   - `test_the_parity_skip_is_an_ordinary_skip_and_its_output_counts_it`: main's output has no
     count line.
   - `test_a_screen_ingest_needs_no_exclusion_list`: the frozen run, whose rule is the committed
     screen snapshot's own. Main refused with *"… excluding 6"*.
   - `test_the_committed_snapshot_uploads_with_no_exclusion_list`: the real pages snapshot through
     the fake bucket. Main refused with *"exclude 0 … excluding 6; nothing was uploaded"*.
   - `test_an_upload_given_exclude_fails_loud_before_any_request`: main raised `FactsStoreError`
     (1 < 6), not argparse's exit. The branch makes 0 requests.
   - `test_a_snapshot_naming_no_exclusion_uploads_beside_the_committed_ones`, two cases. With both
     counts 0, main refused on the current snapshots' 6. With no count, main refused because the
     snapshot states none. On the branch both upload, and the bucket audit runs over every
     manifest in the tree and passes.

   Five re-expressed tests also fail on main, each for the expected reason: three read
   `screen_scope_names`' new two-value return, and two are uploads that main refuses without
   `--exclude`. On the branch all fourteen pass.
2. **Twelve pins removed**, because each asserted a refusal that no longer exists:
   - in `test_facts_layer.py`, the ingest refusal and the no-count refusal;
   - in `test_facts_screen.py`, the three first-snapshot pins, the three same-population pins of
     #904's round 2, and the excluded-name scope pin;
   - in `test_facts_remote.py`, the two upload refusals and the current-list loop.

   The upload tests that passed `--exclude ×6` only to get past the guard (the audit pins) now pass
   none.
3. **The live corpus.** A probe calls the selection and the two guards and never runs an ingest or
   an upload. It ran over the committed tree and the primary checkout's SEC cache, read-only.
   - Main's code: the next pages selection, with no `--exclude`, is 29 names and includes BURL;
     `require_exclusions` refused it (*"… written excluding 6 …"*), and
     `require_upload_exclusions(load_manifest(), [])` refused too.
   - The branch: the same 29 names, and neither function exists. The 29 are the committed pages
     snapshot's 28, plus MCK (its page came after the snapshot).
4. **Parity on the live pages** (read-only), against the committed `edgar-4f3207f4da9fb71a` at
   each page's price date, 22.5 s:
   - with no `--exclude`: 28 page-cuts, 26 zero-diff. BURL is unread (*"not in snapshot"*), and
     MCK is unread (*"not in the SEC cache"*). Exit 1, and the output says *"0 name(s) … left
     out"*;
   - with `--exclude BURL --exclude MCK`: 26 of 26 zero-diff, *"2 name(s) of the pages' scope left
     out by --exclude"*. Exit 0.
5. **The kept upload guards still fire.** Three mutants were run over `tests/test_facts_remote.py`
   (40 tests), each with `PYTHONDONTWRITEBYTECODE=1` and `__pycache__` cleared, then restored with
   the sha256 checked:
   - the read-back hash disabled: caught by `test_the_read_back_catches_bytes_the_bucket_changed`;
   - the audit's "named by none" count forced to 0: caught by
     `test_the_upload_fails_when_the_bucket_holds_what_no_manifest_names` and
     `test_the_bucket_is_listed_across_pages_and_a_stray_key_is_counted`;
   - the audit's FAIL disabled: caught by the first of those two.
6. **The gate.** ruff, `mypy --strict` and `pytest -m "not network"`: counts in the PR body.

**BOUNDARY.**
- **Committed manifests.** The two at main `7a79c091`:
  - pages `edgar-4f3207f4da9fb71a`: names_selected 28, 1 excluded, a list of 6, 26 ingested;
  - screen `edgar-6e0e4626855b9fce`: names_selected 2,065, 1 excluded, a list of 6.
- **The live selection.** The pages rule over the 28 committed `data/dossiers/*/dossier.json` and
  the names `data/followed.json` follows on 2026-11-06: 29 names. CIKs come from each page or from
  the cached `company_tickers.json`; 0 were unresolved.
- **Parity.** One cut per page, at its price date. Unit: page-cuts. MCK's companyfacts are not in
  the SEC cache, so it would be unread under any snapshot.
- **Tests.** Counts are tests (parametrized cases counted separately) in `tests/test_facts_layer.py`,
  `test_facts_screen.py` and `test_facts_remote.py` at the branch's head.
- **When.** 2026-11-06.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A mislabelled constant field** in every new manifest (above).
- **Parity still needs a skip** until the pages snapshot is re-ingested. That re-ingest would add
  BURL and MCK's response (once cached), and it waits on the operator's slice-2b and git-growth
  rulings (row 44).
