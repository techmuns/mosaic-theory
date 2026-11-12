---
id: 2026-11-12-twelve-word-guard-and-cut
status: shipped
date: 2026-11-12
prs: [1036]
supersedes:
superseded-by:
---

# The 12-word rule holds at build, and two committed claims that broke it are cut at $0 — a synthesis string sharing more than 12 consecutive words with the build's own calls is flagged and its page refused; LLY's and VITL's runs are cut to 12 words and "…"; WERN, named with them, shares at most 11 and is not cut

**WHAT.** RG-D19's residual (fix request 2), under the operator's ruling of 2026-11-11, verbatim
"$0 guard + redaction now (Recommended)". CLAUDE.md: NO PUBLIC FIELD QUOTES MORE THAN 12
CONSECUTIVE TRANSCRIPT WORDS. `tests/test_public_transcript_text.py` holds that between
quotation marks only. Codex (round 2 of #1006) found synthesis prose that copies a call's words
without them.

1. **The guard at build.** `synthesis.transcript_runs(synth, transcript)` names every synthesis
   string sharing more than `MAX_TRANSCRIPT_RUN` (12) consecutive words with the build's calls.
   - Citations (`source_ref`, a twin's `source`) are left out.
   - Words are split on whitespace, as the rule counts them, and folded by the verbatim check's
     key (case, quote marks, dashes), with edge punctuation read off.
   - `_validate(..., transcript=)` flags each run ("TRANSCRIPT-RUN <field>: shares N consecutive
     words …"), and `synthesize` passes its `transcript`.
   - `assemble._refuse_transcript_runs` refuses the page on the runs themselves, after
     `_require_synthesis` and before the write, never on the flag's wording. The confirmation and
     the panel replay flag a run and refuse nothing.
2. **The $0 cut.** `vinci transcript-run-cut` (`vinci/dossier/transcript_run_pass.py`) cuts each
   run to its first 12 words and "…". Nothing is reworded and no model is asked. The pass:
   - reads each page's calls as the build fed them (`confirmation.page_transcripts`);
   - is recorded as layer-refresh writer `transcript-run-cut`;
   - refuses a page whose call does not read, whose calls differ from its input record, or whose
     driver rows cite a call that is not on disk;
   - names a cut by word counts, the span removed and two hashes, never by its words.
3. **Pages cut:** LLY's and VITL's pages, their renders and frontend mirrors, and the frozen LLY
   synthesis in `tests/fixtures/material_direction/pages.json`.
4. **The gold set's copy.** The gold set's `LLY:bull_points:5` (`tests/fixtures/synthesis_gold/
   claims.jsonl`, line 220 of 644) is cut the same way, byte-equal to its page's cut, under the
   operator's ruling of 2026-11-12, verbatim "Cut it, same PR (Recommended)". The option read:
   "Cut to 12 words + '…', add a dated MANIFEST note, and merge only if the metric hits and every
   evals test come out identical."
   - `MANIFEST.source_sha256["claims.jsonl"]` is now `071fb70c…`.
   - A dated `amendments` entry keeps the old `dfba0584…` and quotes the ruling.
   - No label moves.

**WHO.** A built the guard, the pass and the unit tests: `claude/twelve-word-guard` `94fc4e0c`,
stacked on #1023, handed to B on 2026-11-12. B cherry-picked it onto main `85152609` and
measured it on the corpus. B also made the CLI and the pass name a cut without its words (A's
CLI printed the string before the cut, which holds the run), ran the cut, and fixed review
round 0 (below).

**WHY.** This repo is public. A copied run of 13 or more consecutive transcript words is
licensed text published, wherever it sits. The build has the words, since every call is the
synthesis's `transcript`, so it can refuse such a page before it is written.

**HOW VERIFIED.** All at $0. The calls are read in place, read only, from the primary checkout's
`data/manual/ciq`, which mirrors Drive.
- **Corpus before any cut:** the guard on all 27 committed pages, against each page's calls.
  - **2 pages fire:** LLY `bull_points[5].claim` (14 words) and VITL `bull_points[2].claim` (13).
  - 23 share no run of more than 12 words; ORKA and TECX have no call on disk.
  - Every call the three named pages cite (their driver rows' `transcript_sha256`) is on disk
    byte for byte. The counts are the same against the text the build sends
    (`transcript_for_synthesis`) and against the calls read one by one.
- **WERN is not cut.** Its `bull_points[5].claim`, named with LLY's and VITL's at 14 words on
  #1006 (A's count, 2026-11-11), shares at most **11** consecutive words with its calls: under
  the guard's fold, and under one that keeps only letters and digits.
  - The 15/14/14 on #1006 matches a count that admits one differing word: LLY 15, VITL 14, WERN 12
    under it.
  - Codex had said 13 and 13 for LLY and VITL.
  - The rule counts consecutive words, so a differing word ends a run.
- **The repo-wide scan:** every tracked text file (3,751), for any 13-word window of the two runs
  (folded as the guard folds; hashes of the windows below).
  - **Before the cut, 8 files:** LLY's `dossier.json` and `dossier.md`, VITL's `dossier.json`,
    the three frontend mirrors that follow them, `tests/fixtures/material_direction/pages.json`
    and `tests/fixtures/synthesis_gold/claims.jsonl`.
  - **After: 0 files.**
- **The gold set, before and after its cut.** Each item below is identical.
  - Every deterministic metric's fired set over the 644 claims, ids and hit detail: M-ABSENT 32,
    M-GAP 0, M-LABEL 69, M-PATH 6, M-SIGN 2. The claim is in none, nor in the frozen
    `metric_hits.json`.
  - `gold.summary` and `python -m vinci.evals gold`.
  - Every node of the 28 test files that import `vinci.evals`: 726 passed, the same 14 failed, 4
    skipped, 2 xfailed. The 14 read CIQ folders and transcripts this worktree's data link lacks.
- **Order 8's RG-D11 check** (#1030, `gold.verify_gold`, called from `load_gold`) reads
  `MANIFEST.source_sha256` at load time. It accepts this branch's gold folder, and refuses it
  under main's recorded sha. Order 8 does not edit the gold folder or the manifest, and its
  scorer fingerprint (`compare.SCORER_FILES`) holds no gold file. So S1's adoption carries the
  new sha by merging main after this lands; no code changes.
- **After the cut:** the guard fires on 0 of 27 pages. The pass's own dry run reads all 27
  unchanged through the new reader, and none is refused.
- **The cut, by position and hash:**
  - LLY `bull_points[5].claim`: 35 → 33 words, characters 108–123 of 220 cut to "…", sha256
    `9d75574cd14c7774` → `b919c6918c13249e`.
  - VITL `bull_points[2].claim`: 41 → 40 words, characters 214–217 of 221, sha256
    `a828b37c19013761` → `07951f83651a6a46`.
  - Each page moves in that string and one new `layer_refreshes` entry. Its render moves 2 or 3
    lines.
  - The removed runs' 13-word windows (sha256 of the folded words joined by single spaces):
    LLY `b0feea8c…6aebbbb` and `3314ffe3…fd5230e`; VITL `39541ce3…179dd5e8`.
- **Tests:** `tests/test_transcript_run_guard.py`.
  - Positive pins: a 13-word run is refused, and a 15-word run is found through capitals,
    curly quotes and commas.
  - Negative pins: runs of 11 and 12 words pass.
  - The cut keeps 12 words, keeps the text around them character for character, and a second
    pass cuts nothing.
  - A cut is named without four consecutive words of its string.
  - The pass refuses a page whose call does not read, or whose driver rows cite a call not on
    disk; the same page citing the call that is on disk is read.
  - The corpus check against the licensed calls skips in CI, which holds none.
  - The calls in the pins are built from the frozen SMPL page's own claim, so no fixture holds
    a transcript word.
- **Review round 0** (`/code-review high --fix`):
  - The pass now reads through `confirmation.page_transcripts` and refuses a page whose calls are
    not its own. A's version read whatever calls sat on disk.
  - The flag says "assembly refuses such a page", not "the page is refused".
- **The full suite found two more**, both fixed:
  - `test_prespend.py` pins every helper `assemble_one` calls after `synthesize`, and
    `_refuse_transcript_runs` is now classified there as a synthesis-decided refusal.
  - The corpus check failed on 25 pages against this worktree's older copy of the exports. A
    checkout whose calls are not the page's own cannot check the page, so it now skips and says
    why. A call that is the page's own and does not read still fails.
- **The impact check** (`python -m vinci.impact run`; base `85152609`, head `1f88e4d2`, VALID):
  - built 27 of 27, and 0 pages move; the guard refuses and does not write, and the cut is on the
    committed pages, not in the build;
  - 0 of 27 requests differ, and the frozen panel differs on 0 of 6, so the row-53 panel check
    is not owed;
  - 0 committed pages re-render differently, and the ledger, scoring report and monitor are
    identical at both refs;
  - fail first, over the two changed test files: 15 of 181 tests fail with base's code and none
    with head's. 138 pass at both (`test_prespend.py`'s other pins among them), and 28 skip
    (the corpus check, without the licensed calls).

**BOUNDARY.** "Words" are whitespace-split, as the rule and `test_public_transcript_text.py`
count them. The population is the 27 committed pages at main `85152609`, with each page's calls on
disk on 2026-11-12. The scan covers `git ls-files` with a `.json`, `.md`, `.jsonl`, `.txt`,
`.html`, `.js`, `.py` or `.csv` suffix, at this branch's head.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **History keeps the words.** The cut removes them from every tracked file. Git history, and the
  panel's frozen blobs read from it (`vinci/evals/synthesis_panel.json`'s freeze), still hold
  them, as the operator accepted when the repo went public (un-tracking would not un-publish
  history).
- **A refused build costs a re-run.** The draws are spent by the time the guard reads the
  synthesis; publishing would cost the licence.
- **The scorer fingerprint changes** (`synthesis.py` and `schemas.py` are in
  `compare.SCORER_FILES`), and panel draws now carry the TRANSCRIPT-RUN flag where they copy a run.

**FOUND, NOT FIXED.**
- The guard reads the synthesis only. Transcript driver rows are held by
  `test_public_transcript_text.py`; any other public field that could carry a transcript's words
  is not read against the calls.
- A cut drops the 12th word's own trailing punctuation with the run. Neither committed cut has
  any there.
