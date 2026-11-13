---
id:
status: shipped
date: 2026-11-13
prs: [1046]
supersedes:
superseded-by:
---

# The 27 transcript runs in tracked files are cut: the audit's 21, the 4 the new guard found, and the 2 its review found split across string literals; from six records, four tests and a comment. Every tracked file is now read against the calls on this disk: a local guard fails on any 13-word window a file shares with a call unless it finds that window, computed, in a cached SEC document or a Key Developments export

**WHAT.** Three operator rulings.
- 2026-11-12, verbatim "Cut all 21 + guard (Recommended)". The option read: "One $0 PR. Each run
  is cut to 12 words or fewer. Each record gets a dated redaction amendment naming count, position
  and hash only, as #1036 did. A local-only test scans every tracked file against the transcripts
  on disk, and skips in CI where they are absent."
- 2026-11-13, verbatim "Cut all 25, one PR (Recommended)". The option read: "Cut the 4 extra runs
  the same way as the 21: a dated redaction on the record, made-up sentences in the tests, a
  shorter docstring. One PR, landing before #953's paid run registers." The operator reconsidered
  whether transcript text needs cutting at all, given the CIQ licence, and kept the 12-word cap
  (#1043).
- 2026-11-13, verbatim "Cut 27 + widen guard (Recommended)", after the independent review of #1046
  at `4af35acb`. The option read: "Cut both with made-up sentences of the same shape, and add the
  joined-string view to the guard. It also fixes two minors: the redaction entry's line number,
  and the count check over every entry. Then I merge once it is re-reviewed."

CLAUDE.md: NO PUBLIC FIELD QUOTES MORE THAN 12 CONSECUTIVE TRANSCRIPT WORDS, and this repo is public.

1. **The audit's 21.** A's audit of main `407dc809` found them, and this build re-found each at the
   same word count. GOOGL's reads 22 here, because this fold also splits at a slash. Line 72 of the
   earnings record holds two runs, so the 21 rows are 22 runs.
2. **The 4 the guard found.** A's audit could not read their calls, which were offloaded when it
   ran. Once the store was local again the guard read them, and found 4 runs at 8 sites:
   - BRBR Q3 2026 call, 3 runs: the 2026-08-10 BRBR record :35 and :40;
     `tests/test_following_context.py` :3, :29, :32, :34; the comment at
     `vinci/dossier/schemas.py:2472`;
   - WLK Q1 2026 call, 1 run: `tests/test_driver_facts.py:219`.
   Neither a cached filing nor a KD export holds any of them. WLK's own Q1 release and 10-Q are in
   the cache and were read.
2b. **The 2 the review found** (round 1). Both are in `tests/test_following_context.py`, each split
   over two string literals that the code joins at run time, so every view read each as two
   runs under 13:
   - :54–55: VRRM's Q1 2026 call, 20 words at word 1,011, run sha256 `1b84fa4e096f56bd`;
   - :86–87: SMPL's Q3 2026 call, 13 words at word 684, sha `4a2bbaf5b9a0a026`.
   The guard now reads a `.py` file's literals joined. Over all 753 tracked `.py` files at
   `4af35acb`, that view finds exactly these 2 runs that no other view found, and nothing excuses
   either.
3. **How each is cut.**
   - **Six records**, cut in place: 21 runs, 38 spans cut to "…". Each record gets a dated
     `## Amendments` REDACTION entry naming the ruling. Each run is named by the line it starts
     on and the line(s) its cut spans sit on, as merged (review round 1: a run's first line is not
     always the line cut); by its length and the words kept; by its call and its word offset in
     that call; and by the sha256 of its words. No entry names a word.
     - `2026-09-03-glp1-shortlist-step-8.md`: lines 128 and 131, both inside its second amendments
       section.
     - `2026-09-03-glp1-step10-references-and-bdx-gate.md`: 76, 78 and 99.
     - `2026-09-10-glp1-earnings-vs-revenue-exposure.md`: 21, 29, 38, 72 (two runs) and 74.
     - `2026-09-10-mck-gated-on-driver-tie.md`: 25, 26, 32, 34 and 56.
     - `2026-09-10-wat-glp1-base-sized.md`: 27, 90 and 100.
     - `2026-08-10-b1-four-findings-from-bellring-s-stage-1-underwr.md`: 35 and 40, under the
       ruling of 2026-11-13.
     Each run keeps at most 12 of its words, chosen to carry the figure or claim the record relies
     on. #1036 kept the first 12 words of a run, which here would have cut WST's percentage away
     from what it is a percentage of. Nothing is reworded.
   - **Four tests**, each given a CONSTRUCTED passage of the real one's shape, so each still runs
     in CI:
     - `tests/test_dossier.py:9923` (SMPL): a lead-in of over 100 characters, a comma, then the
       clause with its action and month;
     - `tests/test_dossier.py:10010` (GOOGL): a retrospective "since" governing a launch verb and
       a month;
     - `tests/test_driver_facts.py:215` (WERN): a growth figure, its change word after it, then a
       second figure;
     - `tests/test_driver_facts.py:219` (WLK): a figure, "decreased by", a second figure;
     - `tests/test_following_context.py` (BRBR): a quoted figure, then in the same paragraph a
       sentence opening "This is" that reverses its reading, then a blank line and the next
       section. The module docstring describes the passage by its shape;
     - `tests/test_following_context.py:54–55` (VRRM): a figure, then an amplifying sentence
       opening "This is a";
     - `tests/test_following_context.py:86–87` (SMPL): a figure ending its paragraph, a blank
       line, then another speaker's figure.
   - **One comment**, `vinci/dossier/schemas.py` (`OperatingDriver.following_context`'s `#:` lines),
     is shortened to say the same thing without the call's words. The extraction pin hashes tokens
     without comments, so it does not move.
4. **The ledger's fourth permitted change: a REDACTION** (`tests/test_records_ledger.py`
   `_redaction_violations`, README item 4). A merged record's text may change only by spans
   replaced with "…", under an appended `**<date> — REDACTION: <n> spans cut to “…”**` entry whose
   `<n>` matches. The record must otherwise be its merged self: front matter included, existing
   amendments may be cut but not reworded, and nothing may be added before the entry.
5. **The guard** (`tests/test_tracked_files_hold_no_transcript_run.py`, local only).
   - It reads every tracked text file (raw, JSON-unescaped, HTML-unescaped and, for a `.py` file,
     its string literals joined as the code joins them: `py_strings`; and with each Markdown link
     read as its text) against every call in the store, its `ciq-archive/` and
     `VINCI_TRANSCRIPT_ROOTS`, read by production's `ciq.read_text`.
   - A call on disk that does not read FAILS the test, naming the file and its error: a call left
     out of the scan is never a pass. Only a disk with no call skips (CI).
   - It fails on any 13-word window a file shares with a call, unless it COMPUTES that the window
     is also in a cached SEC document or a Key Developments export. KD excuses are counted apart:
     KD's publication is unruled (STATE row 60, item 3b).
   - It skips in CI, saying so, and prints its boundary everywhere else.
   - It caches window hashes in `.pytest_cache`, never a word, and recomputes every excuse from its
     source on each run.
   - It ships with NO allowlist.

**WHY.** #1036's build guard reads a synthesis at build, and `test_public_transcript_text.py` reads
the fields code knows are transcript text. Nothing read a record, a test, a fixture or a comment
against the calls themselves, so 27 runs of 13 to 40 of a call's words sat in public files.
- Records written before the rule held 21 of them.
- Tests held the rest. One of their docstrings called its sentence "the REAL Q3 transcript
  sentence".
- A production comment held one.
An appended correction cannot un-publish words the body still carries, so the records are cut in
place, under the rulings.

**HOW VERIFIED.** $0. No model, Polygon or Tiingo call. The calls were read in place, read only,
from the Drive mirror.
- **The cuts, mechanically.** Each record is its merged self with spans replaced by "…": the
  ledger guard permits each with its entry and refuses each without. No record holds a run of 13+
  words against the calls afterwards, and no run keeps more than 12 of its words.
- **The tests still pin what they pinned.** Each was given a mutation of the code it guards. Every
  mutation turns BOTH the old test (with the call's sentence) and the new one (constructed) red,
  and neither is red unmutated:
  - SMPL: the clause read from the sentence's start;
  - GOOGL: the `since` check removed;
  - WERN: a change word handed to the next figure;
  - BRBR: the context run past its paragraph, and the digest's continues line dropped;
  - WLK: a fall after "by" handed to the figure before.
- **The guard bites.**
  - Its pins, on a real call read at run time, catch 13 words in a comment, behind markdown marks,
    JSON-escaped, and joined by bare dashes. They pass 12 words, and a run with its 7th word
    changed.
  - An excuse needs a source holding all 13 words, and a window both KD and SEC hold is the SEC
    document's.
  - Six mutants of the guard are each killed: a 14-word window, no unescaped view, no dash split, a
    narrow edge set, KD not ceding to SEC, and no scan.
  - CORPUS BEFORE SYNTHETIC: on #1036's parent `68bd4b33` it finds the LLY, VITL and WERN runs
    #1036 cut, and at head nothing in those files.
- **The guard on this Mac, at `06019c70`** (main `98707f29` plus this branch after review rounds 1
  and 2, with the joined and Markdown-link views and the fail-loud read; its own boundary print,
  the same at `17f4e3be` before them):
  - calls: 91 read, 19 duplicate files by sha256, 0 unreadable;
  - tracked files (and untracked, not ignored): 3,095 scanned; skipped: 680 binary (a NUL byte),
    1 not UTF-8;
  - runs of 13+ words shared with a call: 113 (294 distinct windows);
  - excused by an SEC document in the cache: 104;
  - excused by a KD export: 9 (BRBR's driver row and BURL's two, on each page and its mirror, and
    V's, on its page, its mirror and its 2026-10-26 frozen page);
  - unexcused: 0.
- **The audit's 98 other runs** (the 119 less the 21): each read from its file at `407dc809` at the
  audit's own positions.
  - **77** are confirmed, every window, in the source their file names: 66 SEC filings and 11 KD
    exports. The three in `tests/fixtures/prespend/2026-11-04/MNST-mechanical.json` needed their
    named MNST filings fetched first, at $0, through the repo's own paced SEC client (CIK 865752;
    0001104659-26-092046, -26-020525, -26-057188, -25-107778).
  - **21** are found, every window, in another cached SEC document. 20 are the same issuer's
    release or 10-Q (TJX, FUBO, VRRM, MVST), where a test or comment names its source beyond the
    5 lines the check read. The WERN release fixture's run is safe-harbour boilerplate found in
    other issuers' 8-Ks.
  - **0** are found in no source.
  - The audit's "71 unconfirmable" were unconfirmable because the SEC cache was offloaded. All
    18,757 cache files are local now (`brctl download`, 0 failed).
- **Review round 0** (`/code-review high --fix`): 10 findings; 7 fixed (2 partly by the review
  itself), 1 dismissed, 1 deferred, 1 partial. The fixes:
  - the boundary no longer goes through `capsys`: xlrd, first imported here, kept its closed
    buffer and broke a later test;
  - the SEC prefilter reads JSON escapes as spaces, with a pin;
  - "0 SEC unreadable" is no longer printed after a clean read;
  - unstaged files are read, with a pin;
  - a run on a line is dropped only when a longer run holds every window it holds, with a pin;
  - `_call_words` catches `UnicodeDecodeError`;
  - the six-record count.
  Each new pin fails on the code before its fix. The redaction rule's "any span" is recorded below
  as accepted risk.
- **Review round 1** (the coordinator's independent review of `4af35acb`): FIX FIRST, ruled "Cut 27
  + widen guard (Recommended)".
  - The two joined-literal runs are cut, and the joined view `py_strings` is added. Its pins:
    - a CI-runnable pin on the view itself: names, prefixes, quotes, fields, format specs and
      comments blanked; lines kept; an untokenizable file yields no view;
    - the review's two planted shapes (two assignments, and an implicit concatenation with an
      f-string), each caught as Python and missed as any other file, with a 12-word negative;
    - a corpus pin: on main `98707f29` the view finds both runs in the file, and at head none.
    Each new sentence's mutation (a continuation kept only when it opens contrastively; the
    context reaching past a blank line) turns both the old test and the new one red. With the
    view switched off, all three new pins fail.
  - Minor: each REDACTION table names the line(s) its cut spans sit on beside the line the run
    starts on.
  - Minor: `_redaction_violations` counts EVERY appended entry, not only the last. A new pin
    fails on the old function.
- **Review round 2** (Codex's first review, of `4af35acb`; its second, of `ad53d5c8`, found nothing
  major; the coordinator's go-ahead): one fix commit.
  - P1, fail loud: a call on disk that does not read was dropped, and the guard passed on the calls
    that did. Now the test fails, naming each such file and its error; a store holding only such
    calls fails too, and only a disk with no call skips.
    Pin: `test_a_call_on_disk_that_does_not_read_fails_the_guard`, which builds its own store and
    so runs in CI.
  - P2: one word written as a Markdown link (`[word](url)`) broke a 13-word run, since the word
    read as "word](https:". A view now reads `[text](url)` as `text` and `![alt](url)` as `alt`.
    Pins: `test_a_markdown_link_reads_as_its_text` (CI-runnable), and
    `test_thirteen_words_with_one_inside_a_markdown_link_are_caught`, which plants 13 call words
    with one in a link, then in an image's alt text, plus a 12-word negative.
  - All three pins fail on the guard at `ad53d5c8` and pass at head.
  - On the corpus the link view finds no new run: 162 tracked text files hold a Markdown link, and
    none holds a window only that view sees.
- **Gate.**
  - `ruff check vinci tests` and `mypy --strict vinci` (218 files): clean.
  - The full `nice pytest -m "not network"`, CI-like (a worktree with no CIQ folder and no cache, as
    CI has): exit 0 at `17f4e3be`, no failure and no error, 1,198 s; exit 0 at `95b3aff9` after
    round 1, 1,514 s; and exit 0 at `06019c70` after round 2, no failure and no error, 1,434 s. The guard and its call-reading pins skip,
    saying so; the pins that need no call run.
  - Linked mode: `tests/test_driver_facts.py` fails the same two tests on main `407dc809` and on
    this branch. Both read the operator's local PARR quarterly Financials, which CIQ mislabelled.
- **Cross-setup validation** (`python -m vinci.impact run`, base `98707f29`, head `06019c70` after
  round 2, $0, vendor pulls refused; the same at `17f4e3be` and at round 1's head, over 438 and
  442 tests):
  - 0 of 445 tests fail on base code and pass on head; 0 fail at head;
  - pages built 26 of 27 (PARR refused at both refs by that mislabelled export), 0 move;
  - 0 of 26 synthesis requests differ, and 0 of 6 frozen panel pages, so the row-53 panel check is
    not owed;
  - 0 of 27 committed pages re-render differently, 0 frontend files differ;
  - the ledger, scoring report and monitor are identical at both refs.
  The tool's defaults point at the git common dir. In the `~/dev` clone that dir has no `data/` or
  `.env`, so `--ciq-root`, `--cache-root` and `--env-file` were named. Without them, 0 of 27 pages
  build.

**BOUNDARY.** 
- **Words** are the guard's: split at whitespace, at every dash form and at a slash; edge marks
  off; lower-cased; apostrophes folded. The audit counted A (whitespace) and B (hyphens split) and
  agrees on all 21 counts but GOOGL's.
- **Calls:** the store `data/manual/ciq` and its `ciq-archive/`, on this Mac, 2026-11-13. That is
  110 call files, 91 distinct; one WERN Q1 2026 call left the Drive folder during the session.
- **Tracked files:** `git ls-files --cached --others --exclude-standard` at this branch's head:
  3,776 files, of which 3,095 are text (at `17f4e3be` and at `95b3aff9`).
- **SEC cache:** `data/cache/sec`, 18,757 files, all local.
- **KD:** 63 exports in the store and archive. One GOOGL `.xls` is read by its cells.
- **The audit:** main `407dc809`, 3,080 text files, and the 361 call files it read from across the
  Mac.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Git history keeps the old text**, as the operator accepted. No history is rewritten, and
  `vinci/evals/synthesis_panel.json`'s frozen blobs are untouched.
- **The guard sees only the calls on its disk.** A store-only default would have missed the two MCK
  Q4 2026 runs: that call left the store on 2026-11-05 and sits only in `ciq-archive/`. So the
  archive is a default root. A call kept elsewhere is read only when its folder is named in
  `VINCI_TRANSCRIPT_ROOTS`. 17 of the audit's 119 runs matched only calls kept outside both, in
  other folders on this Mac. All 17 are among the 98 found in a filing or KD export. Falsifier: a
  run the default roots miss, found by a wider sweep.
- **The scorer fingerprint moves.** `vinci/dossier/schemas.py` is in `compare.SCORER_FILES`, which
  hashes raw bytes, so a comment-only edit moves `scorer_fingerprint()`. No registration exists
  yet, so nothing recorded under the old fingerprint is orphaned. This PR lands before #953's paid
  run registers, as the ruling says. The extraction pin does not move: it hashes tokens without
  comments.
- **A REDACTION is checked for form, not for meaning** (review round 0). CI cannot tell a cut
  transcript run from any other cut span, so a redaction that drops a word turning a claim ("not")
  would pass. Each entry names every cut run by line, length, call and the sha256 of its words, so
  a reader with the calls re-derives each. Falsifier: a REDACTION whose cut changes what a record
  claims.
- **A cut record reads less smoothly.** Each keeps the figure or claim it relies on, and the call is
  named so a reader can check the rest.
- **An excuse is a computed coincidence, not provenance.** A window found in a filing is excused
  though the file may have copied it from the call. Whether to excuse windows found only in KD is
  the operator's open question; they are reported apart and not refused.
