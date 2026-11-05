---
status: shipped
date: 2026-11-05
prs: [915]
supersedes:
superseded-by:
---

# No committed page, mirror or fixture carries an absolute local path: the price-store stamp names each store by its checkout's folder, and the 118 paths already committed are rewritten in place. Git history still holds them.

**WHAT.**
- **The writer.** `assemble._price_store_stamp` wrote `price_store.declared_path` and `resolved_path`
  as `str(declared)` and `str(declared.resolve())`, absolute local paths. It now writes each one's
  checkout folder name through one function, `assemble.store_checkout`:
  `<checkout>/data/vinci.db` → `<checkout>` (for example `mosaic-theory-wb`).
  - It refuses any store it cannot name: a relative path, a store not at
    `<checkout>/data/vinci.db`, or one with no folder above `data/`. A `data/vinci.db` symlinked
    into `~<user>/stores/` would otherwise stamp the username. The refusal message names no folder
    above the file, because a build's run record commits it.
  - Round 2 moved the stamp to the top of `assemble_one`, before any paid phase. Built where the
    page is, after `synthesize`, a refusal would have spent the build's LLM calls and then thrown
    the build away.
- **The schema.** `PriceStoreStamp` keeps its two field names and their `str` type. Only the
  documented meaning changes: each value is a folder name, never a path. So pages from earlier in
  git history still parse, and no reader of the shape had to change.
- **The guard.** `tests/test_no_local_paths.py` reads every file under every committed artifact
  folder: all of `data/`, `frontend/` and `scenarios/`, plus `tests/fixtures/`.
  - That covers files tracked, and files untracked and not ignored, so an artifact pass is checked
    before `git add`.
  - It takes in the build run records (`data/snapshots/assembly_runs/`), whose exception text and
    input manifests a build writes.
  - It fails on an absolute path under `/Users/`, `/private/`, `/home/`, `/Volumes/`, `/root/` or
    WSL's `/mnt/<drive>/`; on a drive letter (`C:\…`, `D:/…`); and on the dashed form a Claude
    project folder takes (`-Users-<user>-…`), whatever key the path sits in.
  - It does not read inside compressed binaries (an `.xlsx`'s zip members, a PDF's Flate streams,
    Parquet pages). Its docstring lists every blind spot.
  - The failure prints every hit as `file:line` beside the count, never a cut list.
  - `python -m tests.test_no_local_paths` prints the same list.
  - It also asserts end to end, from committed JSON through the render to the committed `.md`, that
    each page prints the price-store line its stamp renders.
- **The clean.** `scripts/rewrite_store_stamps.py` reduces a committed absolute stamp to the same
  folder name, by the same function.
  - It edits only the two `"key": "value"` spans in the file's own text, never a `json.load → dump`
    round trip.
  - It then proves the result parses to the input with exactly those two values changed.
  - A second run changes nothing.
  - It ran on the 27 pages and 5 fixtures. `frontend/build.py` rebuilt the 27 mirrors.
- **The version.** `2026-11-05.store-checkout-name` is appended to `EXTRACTION_VERSIONS` and to its
  web twin, and the drift test is re-pinned at it. `assemble.py` is a watched module, and what a
  page carries changed.

**THIS DOES NOT REMOVE THE PATHS FROM PUBLIC GIT HISTORY.** The repository has been public since
2026-10-22. Every commit that added a stamp, from #410 on, still carries its absolute paths. So do
the blobs of every earlier version of these pages, PR diffs, and any fork or clone made before this
change. Those paths name two macOS usernames, worktree names and Claude session scratch
directories. History was not rewritten, and no history rewrite is proposed here. This change stops
the current tree carrying them, and the guard stops new ones landing in its four folders. Anyone
weighing the exposure should treat everything those paths reveal as already published.

**WHY.**
- **The leak.** A 2026-11-05 review of #911 found the paths. #911 fixed the same class of leak for
  its own new field, in an `OSError` reason, and left this older one out of its scope.
- **What the page needs.** The rendered page never printed these paths: `render._price_store_line`
  prints only `Path(…).parent.parent.name`. The docstring claim that "the full declared and resolved
  paths stay in `dossier.json`" was the leak itself. Nothing else needed the full path:
  - **The render** reads only the folder name.
  - **The spot audit's tests** (`tests/test_spot_audit.py`) read only that the two values differ
    across a symlink and name the two checkouts.
  - **#911's manifest backfill** (`inputs.py`) reads `price_store.frontier` only.
  - **Prespend** compares `price_store` by presence, not value: it is not one of the `BLOCKS` it
    compares.
- **Why a folder-name stamp renders the same line.** A bare folder name has no grandparent, so the
  render's existing `or stamp.declared_path` fallback prints it as stored. The render code is
  unchanged; only its docstring was corrected.
- **How the readers were found.** Searches under two vocabularies, `declared_path`/`resolved_path`
  and `price_store`/`PriceStoreStamp`/"store stamp". Dictionary access as `"price_store"`,
  `.price_store` and `price_store]`. `git log -S` on all three terms, and a read of each hit's
  definition. They found:
  - **Writers:** `_price_store_stamp`, with its one call site in `assemble_one`.
  - **Readers:** `render._price_store_line`, `inputs.py:456` (frontier only), and the five tests in
    `tests/test_spot_audit.py`.
  - **Not found:** no reader in `frontend/views/*.js`, `prespend.py`, `refresh.py` or `scripts/`.
- **Why the pages keep their own extraction version and gain no `layer_refreshes` entry.** The
  brief asked that each page's diff touch only the two fields. The rewrite changes provenance
  strings, not an extracted value. A refresh entry would have been a third field. The cost is that
  a page's `extraction_version` does not date its stamp's form, and the new version row says so.

**HOW VERIFIED.** All on this branch, cut from main `c4c9f432` (#911 merged):
- **The writer's pin failed first.** On the old writer,
  `test_the_price_store_stamp_names_checkouts_never_an_absolute_local_path` failed. Its stamp came
  out as a path under pytest's temp root, `/private/var/folders/…/pytest-of-<user>/…/link-worktree/
  data/vinci.db`: the leak's own shape, username included. It passes on the new one.
- **Corpus before synthetic.** Run over main `c4c9f432`'s blobs, the guard lists **118 hits in 59
  of 433 tracked files**: 54 in pages, 54 in mirrors, 10 in fixtures. Every hit sits on a
  `declared_path` or `resolved_path` line (59 + 59). That matches the review's 54 page paths, their
  54 mirrors, and the fixtures it named. On the cleaned tree the guard lists **0**.
  - Round 2 widened the scope to all four folders (1,100 files at `c4c9f432`) and added the dashed
    and mount-root forms. On main's blobs that guard lists **144 hits on the same 118 lines of the
    same 59 files**. The 26 extra are the dashed `-Users-<user>-…` session folder inside the 26
    `/private/tmp/claude-501/…` stamps: real corpus shapes, so the dashed pattern is corpus-tested.
    The rest of the four folders held none. On the cleaned tree it lists **0**, in about 2 s: a
    literal trigger in front of the patterns stands in for 20 s of regex over 147 MB.
- **The pattern's first cut was wrong twice, and the corpus caught both.**
  - A bare `[A-Za-z]:/` matched the `https:` of URLs in 24 committed `.md` files (12 pages and their 12 mirrors). The drive letter
    now has to stand alone, and URLs are a negative pin.
  - The first lookbehind skipped a path after `-`, so it missed `${VENV:-/Users/…}` in `bin/commit`.
    The wider survey below turned that up, and it is now a positive pin.
  - Over the 547 binary files tracked on 2026-11-05 (47 MB), the 3-character drive-letter pattern
    matched 82 times, all random bytes, and the POSIX roots matched 0. So a binary file is read for
    the POSIX roots only, and that has a pin of its own.
- **Each diff is two lines.** For each of the 32 rewritten JSON files, a script compared HEAD's
  blob with the new text:
  - exactly 2 lines removed and 2 added, all of them `declared_path`/`resolved_path`;
  - the rest parses equal;
  - each new value equals the old path's grandparent folder name.
  - Result: 32 of 32 OK. The 27 mirrors are byte copies of their pages (`cmp`).
- **The rendered pages are byte-identical.** All 27 pages were rendered from their committed JSON
  with this tree's code, before and after the rewrite, through the call `assemble._write` makes.
  - **Before** the rewrite, all 27 renders equalled the committed `dossier.md` byte for byte.
  - **After**, `diff -r` of the two render sets is empty.
  - No `dossier.md` or `frontend/dossiers/*.md` changed (`git diff --quiet`).
- **Mutation, round 2 (coordinator review).** 30 mutants, each applied to the code, run against
  its tests, then restored: **30 killed, 0 survived**.
  - **Writer:** dropping `.absolute()`; stamping `str(declared)` or `str(declared.resolve())`;
    removing each refusal; and moving the stamp back after the paid phases.
  - **Guard:**
    - each lookbehind and lookahead character;
    - binary files skipped, or every file read as binary;
    - a folder dropped from `SCANNED`, or `.json` only;
    - the first line only;
    - no dashed pattern, or a trigger without `/mnt/`;
    - untracked files not read;
    - no cut mark.
  - **Script:** each refusal; reducing by its own `parent.parent.name`; always writing; never
    writing; the missing-field guard; and the parse-equality proof.
  - Two survived the first run, the `/mnt/` trigger and the parse proof. Each got a pin and is now
    killed.
- **What the rewrite read.** Committed JSON and committed scenario cards only. It ran no assemble,
  precheck, extractor, store, CIQ export or LLM. That includes BURL, one of the six held audit
  names: operator ruling D-D4 allows a deterministic rewrite of its committed JSON, and its CIQ
  export was never opened. This worktree links no CIQ folder, store or `.env`, so the suite read no
  CIQ export.

**BOUNDARY.**
- **118 / 59 / 433:** matched path starts under the first guard's pattern, over the files
  `git ls-tree -r` lists under `data/dossiers`, `frontend/dossiers` and `tests/fixtures` at main
  `c4c9f432` (2026-11-05).
- **144 / 118 / 59 / 1,100:** matched starts, distinct lines and files under the round-2 pattern,
  over the files `git ls-tree -r` lists under `data`, `frontend`, `scenarios` and `tests/fixtures`
  at main `c4c9f432`. 147 MB is the same files read on this branch.
- **54 page paths:** 27 pages × 2 fields.
- **32 rewritten files:** 27 pages plus 5 fixtures:
  - `band_checks/VITL`
  - `frozen_pages/2026-08-18/SMPL`
  - `prespend/2026-11-04/{MNST-mechanical, SMPL-mechanical, SMPL-mechanical-anchored}`
- **60 files in the artifact commit:** the 32 above, the 27 mirrors, and the frozen-pages README.
- **The 547 binary files and 82 drive-letter matches:** every tracked file not valid UTF-8, at main
  `c4c9f432`.
- **Out-of-scope counts below:** the round-2 pattern over the other 1,973 tracked files at
  `c4c9f432`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Which machine is lost.** Two machines' checkouts with the same folder name now stamp alike,
  where the absolute path told them apart. Nothing compares two stamps today. The render never
  showed the machine, and keeping it is the leak.
- **Edges the writer and the guard do not cover.**
  - The writer refuses a store not at `<checkout>/data/vinci.db`. A checkout folder that is itself
    a username (`/Users/<user>/data/vinci.db` → `<user>`) still has that shape, so it is stamped,
    and it passes the guard.
  - A relative path, a Linux `/tmp/…` or `/var/…`, a bare username, and the inside of a
    compressed binary are not caught.
- **Pages assembled on the old writer land after this one.** Two were in flight on 2026-11-05:
  #914 (SMPL re-assembled) and the NFLX rebuild, with UBER, MCK and PARR to follow as their
  re-exports arrive. Each was built on a branch cut before this writer, so its page and mirror
  carry absolute paths. Whichever of that PR and this one merges second runs
  `scripts/rewrite_store_stamps.py data/dossiers/<T>/dossier.json`, then `frontend/build.py`, on
  the merged tree, and shows the guard reads 0. Until then the guard fails on that page and its
  mirror, which is the point of it. A page assembled from main after this merges stamps folder
  names by itself.
- **Local paths outside the guard's four folders**, none of them an artifact (the round-2 pattern,
  the other 1,973 tracked files at `c4c9f432`):

  | where | hits | files | what |
  |---|---|---|---|
  | `.claude/launch.json` | 18 | 1 | per-machine preview config, naming both users' checkouts and session scratchpads |
  | `bin/commit` | 1 | 1 | the venv default |
  | `docs/records/` | 19 | 16 | prose quoting paths |
  | `docs/theme_intelligence/` | 2 | 1 | a text file |

  These are reported, not fixed: they are out of this build's scope (STATE.md §5.0 row 49). The
  `.claude/launch.json` question, whether a per-machine file stays tracked at all, is the operator's.
- **Falsifier.** A file under `data/`, `frontend/`, `scenarios/` or `tests/fixtures/` carrying a
  path of a form the guard's docstring says it catches, while this test is green.
