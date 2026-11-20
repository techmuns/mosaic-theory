---
status: shipped
date: 2026-11-20
prs: [1153]
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
  - a home directory: `/Users/…`, `C:\Users\…` or `C:/Users/…`, `/home/<name>/`, `~/`;
  - a network share;
  - a session folder named from a home directory (`-Users-<name>-`);
  - a home-directory path cut at its start (`sers/<name>/…`);
  - this machine's own home directory.
- **Shapes, never every slash.** "$40 /kW/month", "(/kWh/yr)" and a URL's `/home/` path pass.
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
  - **The tip as committed:** the guard finds 95 shapes in 77 fields:
    - `output_dir`: 57 fields, 67 shapes;
    - `evidence_location`: 17 fields, 25 shapes;
    - `warnings`: 3 fields, 3 shapes.

    By shape: a macOS home directory 35, a session folder named from one 42, this machine's home
    directory 18. A path can show more than one shape.
  - **This code's export of the same registry:** 0.
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
- **Tests:** `tests/test_theme_intelligence_local_paths.py`, 42 tests.
  - **The guard:** the 15 shapes the review and the tip hold, and 11 that must pass.
  - **The traceback:** none of its cut points leaves a home directory, with the old `format_exc()`
    cut as the control that does.
  - **Creation:** a run's and a version's paths are relative, and a re-render from another working
    directory writes under the data directory.
  - **The export:** legacy rows are rewritten and every other row is written as stored, checked
    against the export WITHOUT the rewrite. This is not the round trip against itself that finding 5
    called a no-op.
  - **The refusals:** `export-state` and `state push` refuse a path in a field nothing rewrites.
  - **The reader:** four pins.
- **Mutations: 16 mutants on the final code, all killed.**
  - A first run of 17 left three alive, and each was fixed:
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
