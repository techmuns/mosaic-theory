---
id:
status: shipped
date: 2026-11-13
prs: []
supersedes:
superseded-by:
---

# The 21 audited transcript runs are cut from five records and three tests, and every tracked file is now read against the calls on this disk — a local guard fails on any 13-word window a file shares with a call unless it finds that window, computed, in a cached SEC document or a Key Developments export

**WHAT.** The operator's ruling of 2026-11-12, verbatim "Cut all 21 + guard (Recommended)". The
option read: "One $0 PR. Each run is cut to 12 words or fewer. Each record gets a dated redaction
amendment naming count, position and hash only, as #1036 did. A local-only test scans every
tracked file against the transcripts on disk, and skips in CI where they are absent." CLAUDE.md:
NO PUBLIC FIELD QUOTES MORE THAN 12 CONSECUTIVE TRANSCRIPT WORDS, and this repo is public.

1. **The 21 runs are cut.** A's audit of main `407dc809` found them, and this build re-found each
   one at the same word count. GOOGL's reads 22 here, because this fold also splits "I/O" at its
   slash. Line 72 of the earnings record holds two runs, so the 21 rows are 22 runs.
   - **Five records**, cut in place: 19 runs, 35 spans cut to "…". Each record gets a dated
     `## Amendments` REDACTION entry naming each run by its line as merged, its length and the
     words kept, its call, its word offset in that call, and the sha256 of its words. No entry
     names a word.
     - `2026-09-03-glp1-shortlist-step-8.md`: lines 128 and 131. Both sit inside its second
       amendments section.
     - `2026-09-03-glp1-step10-references-and-bdx-gate.md`: lines 76, 78 and 99.
     - `2026-09-10-glp1-earnings-vs-revenue-exposure.md`: lines 21, 29, 38, 72 (two runs) and 74.
     - `2026-09-10-mck-gated-on-driver-tie.md`: lines 25, 26, 32, 34 and 56.
     - `2026-09-10-wat-glp1-base-sized.md`: lines 27, 90 and 100.
     Each run keeps at most 12 of its words, chosen to carry the figure or claim the record relies
     on. #1036 kept the first 12 words of a run, which here would have cut WST's percentage away
     from what it is a percentage of. Nothing is reworded.
   - **Three tests**, each given a CONSTRUCTED sentence of the real one's shape, so each still runs
     in CI:
     - `tests/test_dossier.py:9923` (SMPL, 39 words): a lead-in of over 100 characters, a comma,
       then the clause with its action and month;
     - `tests/test_dossier.py:10010` (GOOGL): a retrospective "since" governing a launch verb and a
       month, then a figure;
     - `tests/test_driver_facts.py:215` (WERN, 14 words): a growth figure, its change word after it,
       then a second figure.
2. **The ledger's fourth permitted change: a REDACTION** (`tests/test_records_ledger.py`
   `_redaction_violations`, README item 4). A merged record's text may change only by spans
   replaced with "…", under an appended `**<date> — REDACTION: <n> spans cut to “…”**` entry whose
   `<n>` matches. The record must otherwise be its merged self: front matter included, existing
   amendments may be cut but not reworded, and nothing may be added before the entry.
3. **The guard** (`tests/test_tracked_files_hold_no_transcript_run.py`, local only).
   - It reads every tracked text file (raw, JSON-unescaped, HTML-unescaped) against every call in
     the store, its `ciq-archive/` and `VINCI_TRANSCRIPT_ROOTS`, read by production's
     `ciq.read_text`.
   - It fails on any 13-word window a file shares with a call, unless it COMPUTES that the window
     is also in a cached SEC document or a Key Developments export. KD excuses are counted apart:
     KD's publication is unruled (STATE row 60, item 3b).
   - It skips in CI, saying so, and prints its boundary everywhere else.
   - It caches window hashes in `.pytest_cache`, never a word, and recomputes every excuse from its
     source on each run.

**WHY.** #1036's build guard reads a synthesis at build, and `test_public_transcript_text.py` reads
the fields code knows are transcript text. Nothing read a record, a test, a fixture or a comment
against the calls themselves, so 21 runs of 14 to 40 of a call's words sat in public files. Five
records written before the rule held 18 of them, and three tests held the rest, one of whose
docstrings called its sentence "the REAL Q3 transcript sentence". An appended correction cannot
un-publish words the body still carries, so the records are cut in place, under the ruling.

**HOW VERIFIED.** $0. No model, Polygon or Tiingo call. The calls were read in place, read only,
from the Drive mirror.
«VERIFIED»

**BOUNDARY.** «BOUNDARY»

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Git history keeps the old text**, as the operator accepted. No history is rewritten, and
  `vinci/evals/synthesis_panel.json`'s frozen blobs are untouched.
- **The guard sees only the calls on its disk.** A store-only default would have missed the two MCK
  Q4 2026 runs: that call left the store on 2026-11-05 and sits only in `ciq-archive/`. So the
  archive is a default root. A call kept elsewhere is read only when its folder is named in
  `VINCI_TRANSCRIPT_ROOTS`. 47 of the audit's 119 runs matched copies outside both, and 17 of those
  matched calls this Mac holds nowhere else. Falsifier: a run the default roots miss, found by a
  wider sweep.
- **A cut record reads less smoothly.** Each keeps the figure or claim it relies on, and the call is
  named so a reader can check the rest.
- **An excuse is a computed coincidence, not provenance.** A window found in a filing is excused
  though the file may have copied it from the call. Whether to excuse windows found only in KD is
  the operator's open question; they are reported apart and not refused.
