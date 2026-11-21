---
id:
status: shipped
date: 2026-11-21
prs: [1179]
supersedes:
superseded-by:
---

# The transcript-run guard's 95 "unexcused" runs at #1178's head are 95 sentences of SEC filings that the calls also read, so nothing is cut: a worktree read only its own SEC cache, and its verdict was the checkout's, not the corpus's. A worktree now reads its primary checkout's cache too and gives the primary's verdict, 0 unexcused

**WHAT.** CLAUDE.md: NO PUBLIC FIELD QUOTES MORE THAN 12 CONSECUTIVE TRANSCRIPT WORDS.
`tests/test_tracked_files_hold_no_transcript_run.py` holds the rule on every tracked file, against
the calls on this disk. A window shared with a call is excused only where the guard finds it,
computed, in a cached SEC document or a Key Developments (KD) export.

1. **The report.** On 2026-11-21 the guard ran in the BRBR rebuild's worktree at #1178's head
   `66f82c08`, with `data/manual/ciq` linked to the Drive store. It failed on 95 unexcused runs and
   printed 12 of them. The same guard in the primary checkout at main `d16347f2` (#1178 merged)
   passed 14 of 14. That read as a fail-open blind spot, most likely archived calls the primary
   did not see.
2. **Reproduced, both sides, and the archived-calls cause refuted.** Here at `d16347f2`, with the
   same two roots (the linked store and the Drive `ciq-archive`), the guard read 104 calls (22
   duplicate files by sha256, 0 unreadable). It scanned 3,646 files and found 138 runs of 13+
   words. The call roots are the same in every checkout, because the store is a link to one
   folder, so both checkouts read the same 104 calls. The SEC cache is not the same in every
   checkout. The guard read `data/cache/sec` of the checkout it ran in, and `data/` is per
   worktree (RUNBOOKS, preamble). The base code's own functions gave three results, one per cache:

   | SEC cache the excuse read | its files | SEC documents read | unexcused | SEC-excused | KD-excused |
   |---|---|---|---|---|---|
   | none | — | 0 | 95 | 0 | 43 |
   | this worktree's own | 52 | 0 | 95 | 0 | 43 |
   | the primary checkout's | 18,773 | 2,782 | **0** | 114 | 24 |

   The reporting worktree's cache held 1 file. The primary's pass was the rule working as written.
   It was not a fail-open. The worktree's 95 failures were fail-closed, from a missing excuse
   source.
3. **Classified, each run.** Every window of all 95 runs is in a cached SEC filing: **95 of 95
   have a non-transcript source, and 0 are transcript text alone**. The filings are 21 documents:
   - 14 8-K Ex-99.1 earnings releases: EPAM's three 2026 quarters, AMZN's two, WERN's two, and
     TJX's, SMPL's, MVST's, VRRM's, IT's, CNXC's and FUBO's;
   - 5 main documents of a 10-Q or 10-K: MVST's two 2026 10-Qs, BRBR's, IPX's and MITK's;
   - 2 MNST 8-K full submissions, each an Ex-99.1 release plus an Ex-99.2 NielsenIQ data deck.

   None of the 21 is a filed call transcript. None holds the word "transcript" or the speaker label
   "Operator". The MNST submissions' "Q&A" matches are inside uuencoded image bytes. Each run is a
   sentence that management read from its own release or filing on the call. The guard's
   docstring names this case: "Management reads its release on the call".
4. **Where the 95 sit, and what writes them.**
   - **28 on committed pages, each a field read from a release.** EPAM has 18, across
     `data/dossiers/` and `frontend/dossiers/`. They are the guidance-refusal flags that
     `vinci/edgar/release_parse.py` writes on a release (`mechanical.primary_source.releases[i].qa_flags`),
     their copies in `caveats`, and the page's rendering of them. SMPL has 6:
     - `mechanical.drawdown_cause.anchor.at_anchor.revised_guidance.value`, the verbatim Ex-99.1
       outlook from `mechanical._revised_guidance`, with the 8-K accession in its `source_ref`;
     - a release one-off's `verbatim`.

     TJX has 4, each a release guidance row's `verbatim`.
   - **49 in test pages and fixtures** (frozen pages of EPAM, MVST, SMPL and TJX, prespend and
     release fixtures, and one release `.htm`).
   - **14 in test files.**
   - **3 in `vinci/edgar/release_parse.py` comments, and 1 in a record.**

   The full list is kept out of the repo, in the coordinator's session notes. It gives each run's
   file, line, length, call and word offset, run sha256, kind and excusing document, and no word
   of a call.
5. **So nothing is cut.** No page is re-rendered and no test text changes: the rule's own excuse
   covers every run. There is no artifact PR.
6. **The fix (this PR).** `sec_caches()` returns this checkout's `data/cache/sec` and its primary
   checkout's (`vinci.impact.run.primary_checkout`, the cache that §o's run also defaults to),
   deduplicated. `find_outside_calls` takes a list of caches, in that order:
   - its full read reads a name in EVERY cache that holds it (`_sec_files`), so a bad copy in one
     cache cannot shadow a good copy in another (review round 0);
   - its lookup of a remembered URL tries each cache in turn, until a copy reads and is that URL's
     cache record;
   - its memo's listing covers every cache.

   The boundary now prints a line naming each cache and its file count, so a run whose excuse
   source is empty says so beside its count of unexcused runs.

**WHY.** A guard's verdict must belong to the corpus, not to the checkout that runs it. Read from a
worktree, the guard reported 95 release sentences as breaches of the operator's rule. A session
believing them would have cut 28 page sites and 63 test sites (49 in test pages and fixtures, 14
in test files) that the rule allows, or concluded that the primary's pass was a fail-open. Both
are wrong, and both came from one per-worktree directory read as if it were shared.

**HOW VERIFIED.**
- **Fail first.** `test_a_worktree_reads_the_primary_checkouts_sec_cache` runs the guard itself in
  a git worktree of a temporary repository. A release holding a planted call's 13 words sits in the
  primary's `data/cache/sec` only. On the unchanged guard it FAILED: "1 run(s) … page.md:1 — 13
  words", with "excuse sources read: none", the 95 failures' shape. On the fix it passes. Its
  negative half removes the release from every cache, and the guard must then fail. The call is
  invented words, so the test runs in CI.
- **The round-0 pin.** `test_a_bad_copy_in_one_cache_does_not_shadow_a_good_one_in_the_next`
  FAILS with the name-once read restored, and FAILS with the remembered lookup cut to the first
  cache; it passes on the fix. Its words are invented, so it runs in CI.
- **The real run.** The whole guard file from this worktree, store linked, at `cfbe62a2`, the
  PR's last code commit (the commit carrying this record changes only the record): 16 passed. The
  boundary read 104 calls, 3,647 files scanned and 138 runs. It named both caches, this checkout's
  (52 files) and the primary's (18,773 files): 114 SEC-excused, 24 KD-excused, 0 unexcused. That
  is the primary's own verdict, now given from a worktree. (3,647 files rather than item 2's 3,646:
  this record is one more file.)
- **The 21 excusing documents** were each read for transcript markers (counts above), and the two
  MNST submissions' document types were listed (`8-K`, `EX-99.1`, `EX-99.2`, XBRL, graphics).

**BOUNDARY.**
- **Every count:** measured 2026-11-21 on this Mac, at main `d16347f2` (tree identical to #1178's
  head `66f82c08`), by the guard's own functions (`read_calls`, `scan_tracked`,
  `find_outside_calls`). The one exception is the real run under HOW VERIFIED, made at this PR's
  `cfbe62a2`.
- **Calls:** the transcript files under the linked store and the Drive `ciq-archive`. 104 distinct
  by sha256; 126 files.
- **Files:** every file git tracks or would offer to, 3,646 read. 680 were skipped as binary and 1
  as not UTF-8.
- **A run:** 13+ consecutive words of a call, as the guard counts words.
- **"Excused":** every window of the run is in a cached SEC Archives document (or in a KD export,
  counted apart).
- **The cache counts:** directory entries of each `data/cache/sec` on 2026-11-21.
- **"SEC documents read" (2,782):** documents the anchor prefilter let through, on the first
  uncached pass. A warm run reads fewer, because the remembered documents come first; the real run
  read 24.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A worktree now depends on the primary's cache. A filing absent from both caches still fails
  closed, the direction the rule wants. The guard fetches nothing.
- Each run now lists the primary's directory too: 18,773 `stat` calls, 0.05 s here.
- **24 runs excused only by a KD export are unchanged and still pass, counted apart.** Whether KD
  text may be public is the operator's unruled question (STATE row 60, item 3b). This build does not
  rule on it.
- **History.** Nothing was cut, so no text left main and no history question arises.
