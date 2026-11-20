---
status: shipped
date: 2026-11-20
prs: [1156]
supersedes:
superseded-by:
---

# The theme registry stores and exports no local path, and `export-state` and `state push` refuse one; the PDF reader keeps a headline that opens large type (replaces #1143)

**WHAT.** The operator ruled on 2026-11-20, relayed by coordinator A, verbatim:
- on the licence: "Yes, full text may be public";
- on history: "No rewrite, fix paths ahead (Recommended)";
- on the desk: "Keep the 400 cap (Recommended)".

So this PR replaces #1143 with its path and reader halves only. **There are no quote caps and no
section drops in the export.** The licence ruling is recorded in
`docs/records/2026-11-20-licence-covers-publishing-theme-source-text.md` (#1151).

**Paths, where they are created** (`vinci/theme_intelligence/localpaths.py`):
- A run's `output_dir` is stored relative to the data directory, as `runs/<run id>`.
- A version's `evidence_location` is stored relative too, as `http_cache/…`.
- The 10 sites that stored `traceback.format_exc()[-1500:]` now store `traceback_text()`.
  - It scrubs the whole traceback first: each file is named relative to the checkout or the Python
    installation, and any other home-directory or temporary path is cut to its file name.
  - Only then does it cut.
  - A path that ends, or is cut, at its username keeps no part of it: `/Users/work` reads
    `⟨local path⟩`, never `⟨local path⟩/work`. Nor does a folder named after one
    (`pytest-of-alice`). Only a FILE name after the user's segment survives (round 2, S1).
  - This machine's home is replaced only as a whole prefix, so `/Users/macbook` is not
    `/Users/mac` + `book` (S1).
  - `Pipeline._issue` scrubs a detail BEFORE its id hashes it, so a detail naming no path keeps
    the id it always had. So do the two issues built from a review's exception and the two run
    warnings built from one (N5).
  - A file under the data directory is named relative to it before that scrub
    (`llm_cache/…/answer.json.torn-…`), so a set-aside cache file is still named. The gate's run
    of `test_a_torn_file_is_recorded_on_the_run_that_set_it_aside` caught the round-2 scrub
    reducing it to a bare `⟨local path⟩`.
  - `finish_run` scrubs the exception's message too, which every caller stores before the
    traceback (found by the pre-PR review).
  - The old cut could fall inside `/Users/<name>` and leave `sers/<name>/…` (#1143 review, finding 6).
- `report.write_run_outputs` and QA's render check resolve `output_dir` under the data directory
  (`run_dir`). So a re-render without `--out` no longer writes into the current working directory
  (finding 10). A legacy value relative to another working directory resolves there too.

**Paths in rows stored before this change.** An export writes them relative as well. It touches
three fields only:
- a run's `output_dir`;
- the tracebacks in a run's `warnings`, a traceback cut mid-path included;
- a version's `evidence_location`.

A row that holds none is written exactly as stored. The branch's history is not rewritten.

**The guard** (`localpaths.export_findings`):
- **What it reads.** Every string of every exported JSONL file, JSON held as text included. It
  never reads the rewrite's field list, so a path in a field nothing rewrites is still refused.
- **What it refuses:**
  - a home directory: `/Users/…` (either case), `C:\Users\…` or `C:/Users/…`, `/home/<name>`,
    `/root/`, `~/` or `~<name>/`, a URL-encoded `%2FUsers%2F`;
  - a mounted volume (`/Volumes/<name>`) and a network share (`\\server\share`, `//server/share`);
  - a temporary or scratch folder (`/tmp/`, `/private/tmp/`, `/var/folders/`, `/private/var/
    folders/`): 42 of the tip's 77 path fields were one, and before round 2 they were caught only
    through the `-Users-work-` in their names (#1156 review, S2);
  - a session folder named from a home directory (`-Users-<name>-`);
  - a home-directory path cut at its start (`sers/<name>/…`);
  - this machine's own home directory, as a whole path prefix only (round 2, N2).
- **Keys are read too,** and a refusal never prints a key that is not a plain name (round 2, N1).
- **Shapes, never every slash.** "$40 /kW/month", "(/kWh/yr)", "~3/4" and a URL's own path
  (`https://api.example.com/Users/123`, `…/home/…`, `…/root-cause`) pass: a shape that can begin a
  URL's path is refused only where no letter, digit, dot or hyphen comes before it, `localhost`
  excepted (`file://localhost/Users/…`).
- **It names the shape, never the path.**
- **Where it runs:**
  - in `export-state`, which exits 1 and writes nothing, so the weekly workflow's push step stops
    before its commit;
  - in `state push`, which raises before its commit.

**The reader** (#1143 review, findings 8 and 9):
- #1143's fix stays: large type running past `HEADING_MAX_CHARS` (150) is a paragraph.
- A headline that OPENS such a run stays the heading, and its paragraph starts at the next line. A
  headline is a first line narrower than `HEADLINE_MAX_WIDTH` (0.75) of the run's widest line.
- A heading continues onto the next line only in its own type size. That keeps a wide two-line
  headline set above large type, which the width rule alone cannot tell from a paragraph.
- `PARSER_VERSION` is `ti-parse-9`.

**WHY.**
- The state branch is public, and at `a74c4e30` 77 of its fields named a home folder of the
  machine that wrote them.
- Finding 8 measured what #1143's reader cost: at least 21 of A-f6805a6ed17c's 40 merges opened
  with a real headline, which it filed as body text.

**HOW VERIFIED.**
- **The live registry** (a copy of `theme-intelligence-state@a74c4e30`, 25 JSONL files, 8,899 rows):
  - **The tip as committed:** the guard finds 137 shapes in 77 fields: `output_dir` 57 fields,
    `evidence_location` 17, `warnings` 3. By shape: a macOS home directory 35, a temporary folder
    42, a session folder named from a home directory 42, this machine's home directory 18. A path
    can show more than one shape. Before round 2 the same fields showed 95: the temporary-folder
    shape is new.
  - **This code's export of the same registry:** 0.
  - **No false alarm.** The guard finds nothing in:
    - the 3,251 blocks of source text recovered for 51 of the 57 versions;
    - the 334 files of main's committed desk at `cd082d0b`.

    The weekly runs' 5 public job logs hold 68 lines of the runner's own `/home/runner/…` and
    temporary paths; a log is not an export.
  - **Rows written as stored:** 8,745 are byte-identical to the tip. The 154 that change are every
    version (57) and every run (97). Their changed keys are `evidence_location` 57, `output_dir` 97
    and `warnings` 4. The 4th warning is a CI traceback whose `/opt/hostedtoolcache/…` frames now
    read `<site-packages>/…`.
  - **Round trip:** export → import → export is identical (meta excluded), and all 97 imported runs
    hold `runs/<run id>`.
- **The reader, on the 18 uploaded PDFs held locally.** Each was read with main `51c84843`'s reader,
  #1143's (`2bbc6efd`) and this one:
  - **Unchanged:** the text is identical under all three, in all 18, and 15 read identically.
  - **A-f6805a6ed17c:** headings 63 / 23 / 42, i.e. this reader keeps the 21 real headlines #1143
    lost ("1. Diversified returns", "Overweight the US", "What are the risks?", the four numbered
    risks), and 148 of its 230 other blocks change section against #1143. The longest section is
    1,089 / 149 / 149 characters.
  - **A-84d70c2ec04f:** headings 31 / 14 / 15. One 146-character heading set in two type sizes is
    read as two. The longest section is 1,204 / 146 / 142.
  - **A-0be56cc89833:** headings 29 / 25 / 30, a two-column page (see below). The longest section
    is 240 / 148 / 148.
  - **Blocks whose section runs over 150 characters:** 283 / 0 / 0.
  - **The width rule:** 60 runs cross the length. The 11 that open with a headline are at most 0.56
    of the run's widest line, and the 49 others at least 0.86.
- **Tests:** `tests/test_theme_intelligence_local_paths.py`, 73 tests.
  - **The guard:** the shapes the two reviews and the tip hold (27), and 17 that must pass.
  - **The scrub:** six paths that end at or hold a username, and this machine's home outside
    `/Users` (`/opt/someone`) or inside a longer name (`/Users/macbook`).
  - **The traceback:** none of its cut points leaves a home directory, with the old `format_exc()`
    cut as the control that does.
  - **Creation:** a run's and a version's paths are relative, and a re-render from another working
    directory writes under the data directory.
  - **The export:** legacy rows are rewritten and every other row is written as stored, checked
    against the export WITHOUT the rewrite. This is not the round trip against itself that finding 5
    called a no-op.
  - **The refusals:** `export-state` and `state push` refuse a path in a field nothing rewrites.
  - **The reader:** four pins.
- **Mutations: 31 on the final code, all killed** (15 from round 1, 16 from round 2).
  - Round 2's left three alive, each fixed:
    - a pass of `legacy_traceback` over non-frame home paths, now pinned;
    - the session-folder shape, now pinned without a temporary root;
    - a length check on the home directory that the boundary already did, now removed.
  - A first run of round 1's 17 left three alive, each fixed:
    - a frame renaming that duplicated the scrub, now removed;
    - a fixture whose cut fragment held no username, now holding one;
    - a size-rule fixture the width rule already passed, now a wide two-line headline.
  - **The scrub:** cut before it; another home left in the message.
  - **The export:** its rewrite off; `output_dir` not rewritten; legacy frames not renamed.
  - **Creation:** `output_dir` or `evidence_location` absolute again.
  - **The render:** resolved against the working directory.
  - **The refusals:** `export-state` or `state push` unguarded.
  - **The guard:** three of its shapes removed or widened.
  - **The reader:** three of its rules off.

**BOUNDARY.**
- **Path counts:** the 25 JSONL files of `theme-intelligence-state@a74c4e30`, every string,
  `localpaths.PATH_SHAPES` plus this machine's home directory. A "field" is one (file, row, field
  path); a "shape" is one shape found in one field.
- **Reader counts:** the 18 uploaded PDFs held on this Mac, matched to the registry's 27 document
  records by file sha256 (the other 9 files are gone). They are in
  `data/theme_intelligence/documents/` and `~/Downloads/articles/`.
- **Width ratios:** each crossing's first line against the widest line of its run, by `x1 − x0`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The guard refuses home-directory, username and scratch-folder shapes, not every absolute
  path** (Codex P2 on #1156, deferred). A machine path that names no person, such as
  `/opt/build/report.pdf`, in a field nothing rewrites would pass.
  - The scope is A's brief: "any home-directory or username path shape", widened in round 2 to
    scratch folders.
  - #1143's catch-every-absolute-path regex is what read "$40 /kW/month" as a path (review finding 6).
  - The three fields that held paths are relative wherever they are created.
  - *Falsifier:* an absolute path ANYWHERE in an exported string, mid-string included:
    `rg '(^|[^A-Za-z0-9.:/-])/(opt|mnt|srv|var|data|etc)/'` over the branch's `registry/`.
- **A false positive blocks the weekly's commit step, and nothing overrides it** (round 2, N4).
  - None was found in the export, the source text or the desk.
  - A research string that does trip a shape stops `export-state`; the remedy is a change to the
    shape, in code, under review.
- **An exception message reaches a stored row from about 40 more sites,** in market, discovery,
  securities, health and enrichment notes, interpolating `{exc}`. Those are not scrubbed where they
  are written (N5). Each such row reaches the branch only through `export-state` or `state push`,
  which refuse it. The refusal now names the way out: the row is append-only, so its writer is
  scrubbed, and on Actions the next run restores the branch, which does not hold it; locally
  `state pull --force` rebuilds the registry (backing it up first).
- **Code from before this PR reads a relative `output_dir` against the working directory** (N6). A
  checkout older than this one, re-rendering a registry exported by this one, writes a run's
  readout under its current directory's `runs/<run id>`. Run current code.
- **`readouts/` on the state branch is not guarded.** The workflow copies it after `export-state`.
  It held 0 home-directory paths at `a74c4e30`, and the runner writes its manifest's folder relative
  to its working directory.
  - *Falsifier:* a home-directory shape in a `readouts/` file on the branch.
- **A two-column page set in alternating type sizes** (A-0be56cc89833, the Security Supercycle) now
  reads as 5 one-line headings, where #1143 read one 183-character paragraph. The text is identical,
  and neither reading is right, because the reader interleaves the columns.
- **This Mac's own registry keeps the absolute paths it already holds** until a `state pull`
  rebuilds it from a relative export. Every consumer resolves either form.
- **Not re-read:** the 9 documents whose files are gone, and the web pages (the reader change is
  PDF-only).
