---
id:
status: shipped
date: 2026-11-13
prs: [1058]
supersedes:
superseded-by:
---

# The transcript-run guard's three deferred findings are closed: the joined `.py` view is pinned through the real scan, the unreadable-call pin can no longer be silenced into a skip, and `py_strings` takes its line offsets where the tokenizer does

**WHAT.** The independent re-review of #1046 at `4fd3772e` said MERGE and deferred three findings,
because the bounded rounds were spent. #1046 merged as `01ab6923`, and this follow-up closes all
three, each behind a pin that fails under the defect. It changes only
`tests/test_tracked_files_hold_no_transcript_run.py`; no `vinci/` file moves.

1. **The joined view's wiring into the real scan was unpinned.** `scan_tracked` calls
   `scan_text(text, calls, f.endswith(".py"))`. Changing that to `False` left every test green,
   because the joined view was pinned on `scan_text` alone.
   Pin: `test_the_real_scan_reads_a_python_file_as_its_joined_literals`. It runs `scan_tracked`
   over a planted file that splits 13 words over two literals. As `.py` the scan must find one
   13-word run; as `.md`, none. The call is built from invented words, so the pin runs in CI.
2. **The unreadable-call pin could be silenced.** Reverting only the fail-loud skip half
   (`if not calls.calls:`) made the pin SKIP, green. The skip escaped `pytest.raises
   (AssertionError)`. The pin now reads each outcome through `_outcome`, which returns
   "passed", "failed: …" or "skipped: …", and asserts on it, so a skip is an asserted outcome and
   can no longer escape. Pin: `test_a_call_on_disk_that_does_not_read_fails_the_guard`.
3. **`py_strings` mis-mapped a file holding U+2028 or U+2029.** It took line offsets from
   `str.splitlines`, which also splits at those separators, while the tokenizer splits at "\n"
   only. Every offset after such a character pointed at the wrong text, and the view kept code
   where the literals were. `vinci/graph/filings.py` holds both characters inside a literal on
   line 29, and its view drifted from line 32.
   The offsets now come from the same `io.StringIO(text).readlines()` the tokenizer reads.
   Pin: `test_a_line_separator_inside_a_literal_moves_no_offset`, on that real file (CI-runnable):
   replacing the two characters with spaces must leave the view's words where they were.

**WHY.** A guard nobody can break unnoticed is the point of #1046, and these were three ways to
break it unnoticed: an unpinned wire, a pin that a skip could silence, and an offset that drifted
on one real file. Each was found by the independent re-review and deferred only because the
bounded rounds were spent, so they are closed here as their own small PR rather than left open.

**HOW VERIFIED.** $0.
- **Fail first, by mutation**, applied to this branch's guard and to main's:

  | defect, put back | the new pin | main's pins |
  |---|---|---|
  | the scan hands `False` for a `.py` file | fails | pass (unpinned) |
  | the fail-loud skip half reverted | fails | the unreadable-call pin SKIPS |
  | offsets from `str.splitlines` again | fails | pass (main carries it) |

- **The fix moves one view.** Over every tracked `.py` file, `py_strings` changes only for
  `vinci/graph/filings.py`. Its words with the separators in place now equal its words with them
  replaced; on main they differed from line 32.
- **The guard on this Mac**, on main `01ab6923` plus this branch: 91 calls read, 0 unreadable;
  3,128 files scanned; 108 runs shared with a call, 96 excused by an SEC document and 12 by a KD
  export, 0 unexcused.
  The counts differ from #1046's (113, 104 and 9) because main moved under it. MVST's pages were
  retired, so fewer runs are SEC-excused. The 2026-10-26 frozen pages of BRBR and BURL carry the
  same four KD-excused runs by hash, so they sit in 12 files rather than 9.
- **Gate**, at `18508617`:
  - `ruff check vinci tests` and `mypy --strict vinci`: clean.
  - The full `nice pytest -m "not network"`, CI-like (a worktree with no CIQ folder and no cache, as
    CI has): exit 0, no failure and no error, 1,062 s. The guard's call-reading tests skip, saying
    so, and the three new pins, which need no call, run.
- **Cross-setup validation** (`python -m vinci.impact run`, base `01ab6923`, head `18508617`):
  nothing moves, by construction. Base and head carry byte-identical `vinci/` trees and no frontend
  source change. Its fail-first part shows no node, because the fixes are pins in the test file
  itself; the mutation table above shows each failing under its defect.
- **Review round 0** (`/code-review high --fix`): 7 findings; 6 fixed, 1 dismissed (pinning on
  `vinci/graph/filings.py`'s real text is deliberate: corpus before synthetic).

**BOUNDARY.** The guard's words, calls and roots are #1046's
(`docs/records/2026-11-13-transcript-runs-cut-from-tracked-files.md`). The corpus is `git ls-files`
plus untracked, non-ignored files at this branch's head, and the calls are those in the store and
its `ciq-archive/` on this Mac on 2026-11-13.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Nothing new. The guard is still local only, and it still
reads only the calls on its disk (#1046's record).
