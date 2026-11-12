---
status: open
date: 2026-11-11
prs: [1026]
supersedes:
superseded-by:
---

# Issue #1004, the `customers()` hang: a CIQ RTF export now reads in time linear in its size (AMZN's 2.9 MB Customers export, 117 s → 0.31 s), and the text it yields is unchanged on all 144 RTF exports on disk; the two corpus tests that hung now run under a per-export bound

**WHAT.**
- **The defect.** `ciq.read_text` hands an RTF export to striprtf 0.0.32's `rtf_to_text`.
  - That function finds the font table with one `findall` over the whole file:
    `\\f(\d+).*?\\fcharset(\d+).*?([^;]+);`.
  - `\fcharset` occurs only in the font table, so every `\f<n>` font switch in the body starts a
    lazy scan that runs to the end of its line and fails.
  - CIQ's exports put megabytes on one line, so the read grew with the square of the file's
    size, and the time was all in that one `findall`. Profiled on V's 1.6 MB Customers export, it
    took 11.07 s of 11.32 s; this repo's own parse of the text took 0.007 s.
- **The two hung tests.**
  `tests/test_segment_absence_and_relationship_route.py::test_no_bundle_renders_our_own_parse_error_as_its_customer_field`
  and `::test_the_customers_export_is_chosen_by_name_not_by_file_order` call `customers()` on every
  CIQ folder. Every local gate deselected them, and CI skips them (no exports there).
- **The fix** (`ciq._bounded_font_scan`, called by `read_text` on the RTF route).
  - A newline goes before each `\f<n>` control word. Since `.` does not cross a newline, each
    failing scan now stops at the next switch.
  - RTF gives a newline no meaning outside binary data, and striprtf's token loop reads it as
    nothing.
  - An escaped backslash (`\\`) is matched first, so a literal "\f1" in the text is never split.
  - A file holding binary data (the `\binN` control word) is returned as it stands.
- **The bound.** Both corpus tests now refuse any single `customers()` call over 10 s
  (`_timed_customers`), so no gate needs to deselect them.
- **No extraction vintage.** The text is unchanged (HOW VERIFIED), so the drift pin for
  `vinci/dossier/ciq.py` is re-pinned as a refactor (`--repin --refactor`).

**WHY.** Issue #1004, the operator-approved split between the two fix-request-2 coordinators: "The
`customers()` hang on a large Customers RTF … Two CIQ-corpus tests … hang locally, so every local
gate deselects them, and CI skips them." The item went to this stream because it touches the CIQ
reader.

**HOW VERIFIED.**
- **Where the time went.** `customers()` timed per folder on `origin/main`'s code (`cbefc245`), in
  one process under a 90 s alarm per folder:
  - AMZN (2,945,535 B) did not finish;
  - GOOGL (2,609,888 B) 83.50 s, V (1,625,816 B) 10.31 s, EPAM (771,599 B) 5.18 s, WAT (81,564 B)
    3.08 s;
  - the other 31 folders 0.81 s or less.
- **The text is unchanged.** For every RTF export on disk, `rtf_to_text` on the raw file was
  compared byte for byte with `rtf_to_text` after the bounded scan: **144 of 144 equal**.
  - The files are 36 each of Customers, Suppliers, Key Developments and Public Company Profile.
  - 27 carry a `HYPERLINK` field, which striprtf rewrites before its font scan; all 27 are equal.
  - None holds `\bin` data.
- **The time.**
  - The same 144 files take 376.4 s in total before and 7.1 s after; the slowest single read
    after is 0.655 s.
  - AMZN Customers 117.39 s → 0.305 s; GOOGL Customers 86.86 s → 0.263 s; AMZN Suppliers
    (4,101,431 B) 65.36 s → 0.655 s.
- **Fail first.** All six tests fail on `cbefc245`'s code and pass on the fix (`vinci/` and
  tests in scratch trees, the CIQ folder linked):
  - `tests/test_rtf_font_scan_bound.py::test_a_long_line_of_font_switches_reads_within_a_bound`
    read the 644,986 B synthetic file in 28.2 s, against a bound of 5 s. The fix reads it in
    0.15 s.
  - The file's other three tests (the text unchanged; a `\bin` file left alone; only `\binN`
    leaves a file alone) fail where the
    function does not exist.
  - The two corpus tests fail on AMZN: 148.9 s and 120.0 s. With the fix, they pass over all 36
    folders in 3.17 s and 6.08 s.
- **The synthetic shape.** On `cbefc245`'s striprtf path, 2,000, 4,000 and 8,000 rows read in
  0.39, 1.55 and 6.02 s: quadratic. The bounded path reads 16,000 rows in 0.13 s and 64,000 in
  0.52 s.

**BOUNDARY.**
- The exports under the primary checkout's `data/manual/ciq/` on 2026-11-11: 36 folders, 144 RTF
  files (`classify` → RTF_TEXT, every subfolder included).
- striprtf 0.0.32, in the primary checkout's `.venv`.
- All times are wall-clock seconds on this machine on 2026-11-11, under load (load average 8–15).
  They show the shape (quadratic before, linear after) and the margin; they are not a benchmark.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The fix leans on striprtf's internals.** A later striprtf that changes its font-table pattern
  or its newline handling could make the step unneeded or wrong.
  - The guard: `::test_the_bounded_scan_leaves_striprtfs_text_unchanged` compares the text with
    and without the step on a sample with hex, Unicode, bold and escaped-backslash shapes.
  - The time bound fails if the scan becomes slow again.
- **Two latent shapes do move, none on disk.** striprtf's HYPERLINK rewrite and its font-table
  regex both stop at a newline, so the text CAN differ off the corpus:
  - a field whose `\fldinst` holds a `\f<n>` loses its `("url")` suffix (0 of the 27 HYPERLINK
    exports have that shape; counted 2026-11-11 over the same 144 files);
  - a font-table entry with no `\fcharset` no longer borrows the next entry's charset for its
    hex escapes.
  - The guard's sample carries the corpus's HYPERLINK shape (`\f<n>` in the result), so a
    corpus-shaped link that stopped rewriting would fail it.
- **Only `\binN` switches the step off.** `\binfsxn`, `\binsxn` and an escaped "\\bin" in the text
  hold no binary data and are bounded (`::test_only_the_bin_control_word_leaves_a_file_as_it_stands`);
  a bare substring check would have sent such a file back to the quadratic read in silence.
- **The bound is wall-clock.** At 10 s an export, it sits well above the 0.655 s the slowest RTF now
  takes, so a loaded machine should not trip it. A test that does trip it names the export and the
  seconds.
