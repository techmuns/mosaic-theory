---
id: 2026-11-12-twelve-word-guard-and-cut
status: shipped
date: 2026-11-12
prs: [1036]
supersedes:
superseded-by:
---

# The 12-word rule holds at build, and the three committed claims that broke it are cut at $0 — a synthesis string sharing more than 12 consecutive words with the build's own calls is flagged and its page refused; LLY's, VITL's and WERN's runs (14, 13 and 14 words) are cut to 12 words and "…" everywhere they sat, the gold set's two copies included

**WHAT.** RG-D19's residual (fix request 2), under the operator's ruling of 2026-11-11, verbatim
"$0 guard + redaction now (Recommended)". CLAUDE.md: NO PUBLIC FIELD QUOTES MORE THAN 12
CONSECUTIVE TRANSCRIPT WORDS. `tests/test_public_transcript_text.py` holds that between
quotation marks only. Codex (round 2 of #1006) found synthesis prose that copies a call's words
without them.

1. **The guard at build.** `synthesis.transcript_runs(synth, transcript)` names every synthesis
   string sharing more than `MAX_TRANSCRIPT_RUN` (12) consecutive words with the build's calls.
   - Citations (`source_ref`, a twin's `source`) are left out.
   - A word ends at whitespace, at every dash form and at a slash. It is folded for case, quote
     marks, apostrophes and primes, with edge punctuation read off. This is the conservative
     reading (review round 2): "hotel—india" and "hotel -- india" are two words each, and
     "year-over-year" is three.
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
3. **Pages cut:** LLY's, VITL's and WERN's pages, their renders and frontend mirrors, and the
   frozen LLY synthesis in `tests/fixtures/material_direction/pages.json`.
4. **The gold set's copy.** The gold set's `LLY:bull_points:5` (`tests/fixtures/synthesis_gold/
   claims.jsonl`, line 220 of 644) is cut the same way, byte-equal to its page's cut, under the
   operator's ruling of 2026-11-12, verbatim "Cut it, same PR (Recommended)". The option read:
   "Cut to 12 words + '…', add a dated MANIFEST note, and merge only if the metric hits and every
   evals test come out identical."
   - `MANIFEST.source_sha256["claims.jsonl"]` is now `071fb70c…`.
   - A dated `amendments` entry keeps the old `dfba0584…` and quotes the ruling.
   - No label moves.
5. **WERN's gold-set copy.** `WERN:bull_points:5` (`claims.jsonl` line 604, the gold set's TEST
   half) was byte-equal to WERN's page before its cut (sha256 `30cdced31d1a3d6b`). It is cut the
   same way, under the operator's ruling of 2026-11-12, verbatim "Cut it, same condition
   (Recommended)". The option read: "12 words + '…' and a second dated MANIFEST note; merge only
   if the metric results, the gold summary and every evals test come out identical. Removes the
   last copy from the public repo."
   - `source_sha256["claims.jsonl"]` is now `ee4e1fbe…`.
   - A second dated amendment keeps `071fb70c…` and quotes the ruling.
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
- **Corpus before any cut** (main `85152609`'s pages, the guard's round-2 fold): the guard on all
  27 committed pages, against each page's calls.
  - **3 pages fire:** LLY `bull_points[5].claim` (14 words), VITL `bull_points[2].claim` (13) and
    WERN `bull_points[5].claim` (14).
  - 22 share no run of more than 12 words; ORKA and TECX have no call on disk.
  - Every call the three named pages cite (their driver rows' `transcript_sha256`) is on disk
    byte for byte. The counts are the same against the text the build sends
    (`transcript_for_synthesis`) and against the calls read one by one.
- **The counts, three ways.**

  | claim | the guard (round 2) | whitespace only (round 0) | A on #1006 | Codex on #1006 |
  |---|---|---|---|---|
  | LLY `bull_points[5]` | **14** | 14 | 15 | 13 |
  | VITL `bull_points[2]` | **13** | 13 | 14 | 13 |
  | WERN `bull_points[5]` | **14** | 11 | 14 | — |

  - Round 0 counted whitespace words only, as `test_public_transcript_text.py` does. It found
    LLY 14 and VITL 13, and read WERN's copy as 11 because its run crosses hyphenated compounds.
    WERN was left uncut.
  - The reviewer of round 2 reproduced a false negative: "hotel—india" against "hotel -- india"
    read as no copy at all.
  - Splitting at every dash form and slash finds WERN's 14, which is A's original count.
  - A's LLY 15 and VITL 14 match a count that admits one differing word; the rule's run ends at
    a differing word.
- **The repo-wide scan:** every tracked text file, for any 13-word window of the three runs
  (folded as the guard folds; hashes of the windows below).
  - **Before any cut, 12 files:** LLY's `dossier.json` and `dossier.md`, VITL's `dossier.json`,
    WERN's `dossier.json` and `dossier.md`, the five frontend mirrors that follow them,
    `tests/fixtures/material_direction/pages.json` and `tests/fixtures/synthesis_gold/claims.jsonl`.
  - **After: 0 files.**
- **The gold set, before any gold cut, after LLY's, and after WERN's.** Each item below is
  identical at all three, and so is each item read on the TEST half alone (314 claims; WERN's
  line is one).
  - Every deterministic metric's fired set over the 644 claims, ids and hit detail: M-ABSENT 32,
    M-GAP 0, M-LABEL 69, M-PATH 6, M-SIGN 2. The claim is in none, nor in the frozen
    `metric_hits.json`.
  - `gold.summary` and `python -m vinci.evals gold`.
  - Every node of the 28 test files that import `vinci.evals`: 726 passed, the same 14 failed, 4
    skipped, 2 xfailed. All 14 fail on main's code too, in a throwaway worktree with the same data
    link.
  - `WERN:bull_points:5`, like `LLY:bull_points:5`, is in no metric's fired set, computed or
    frozen.
- **Order 8's RG-D11 check** (#1030, `gold.verify_gold`, called from `load_gold`) reads
  `MANIFEST.source_sha256` at load time. It accepts this branch's gold folder with both cuts, and
  refuses it
  under main's recorded sha. Order 8 does not edit the gold folder or the manifest, and its
  scorer fingerprint (`compare.SCORER_FILES`) holds no gold file. So S1's adoption carries the
  new sha by merging main after this lands; no code changes.
- **After the cut:** the guard fires on 0 of 27 pages. The pass's own dry run reads all 27
  unchanged, and none is refused.
- **The cut, by position and hash:**
  - LLY `bull_points[5].claim`: 35 → 33 words, characters 108–123 of 220 cut to "…", sha256
    `9d75574cd14c7774` → `b919c6918c13249e`.
  - VITL `bull_points[2].claim`: 41 → 40 words, characters 214–217 of 221, sha256
    `a828b37c19013761` → `07951f83651a6a46`.
  - WERN `bull_points[5].claim`: 34 → 32 words as the guard counts them (27 by whitespace),
    characters 92–102 of 233, sha256 `30cdced31d1a3d6b` → `dcf2500bbb32b92f`. The 12th word
    begins a hyphenated compound, so the cut ends inside it ("year…"): exactly 12 words are
    kept.
  - Each page moves in that string and one new `layer_refreshes` entry. Its render moves 2 or 3
    lines.
  - The removed runs' 13-word windows (sha256 of the folded words joined by single spaces):
    LLY `b0feea8c…6aebbbb` and `3314ffe3…fd5230e`; VITL `39541ce3…179dd5e8`; WERN
    `cd7dd4bf…5bb0c79511` and `ea2f9a0f…fa140b3a719f`.
- **Tests:** `tests/test_transcript_run_guard.py`.
  - Positive pins: a 13-word run is refused, and a 15-word run is found through capitals,
    curly quotes and commas.
  - Round 2's pins: a run is found across every dash form and a slash joining two words, and
    across a hyphenated compound against its spaced words; these failed before the fold. One
    word's own apostrophe in every form is one mark (the prime failed before). A quoted run is
    refused. A key unknown and the decisive question are read. `synthesize` hands its
    transcript to the guard (a scripted model). The build's call is read off the parsed code, so
    a call commented out is no call.
  - Negative pins: runs of 11 and 12 words pass.
  - The cut keeps 12 words, keeps the text around them character for character, and a second
    pass cuts nothing.
  - A cut is named without four consecutive words of its string.
  - The pass refuses a page whose call does not read, or whose driver rows cite a call not on
    disk; the same page citing the call that is on disk is read.
  - The corpus check against the licensed calls skips in CI, which holds none.
  - The calls in the pins are built from the frozen SMPL page's own claims and from constructed
    words, so no fixture holds a transcript word.
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
- **Review round 2** (the coordinator's independent reviewer):
  - The fold split no word at a dash, a false negative it reproduced. It now splits at every dash
    form and slash and folds primes, and the re-measure found WERN's 14.
  - Five surviving mutants are now killed by pins: a case-fold-only reading, the build call
    commented out, `synthesize` handing `_validate` no transcript, a quoted-run exemption, and
    reading only `.claim` fields.
  - The stale counts (15/14/14) in the code's comments are corrected.
  - The false-positive class is recorded as accepted, with this record's own measurement.
  - STATE row 60 is left to S4's batched bookkeeping.
- **The impact check** (`python -m vinci.impact run`; last run base `68bd4b33`, head `e8a5060b`,
  after round 2 and the merge of main; VALID):
  - built 27 of 27, and 0 pages move; the guard refuses and does not write, and the cut is on the
    committed pages, not in the build;
  - 0 of 27 requests differ, and the frozen panel differs on 0 of 6, so the row-53 panel check
    is not owed;
  - 0 committed pages re-render differently, and the ledger, scoring report and monitor are
    identical at both refs;
  - fail first, over the two changed test files: 32 of 196 tests fail with base's code and none
    with head's. 136 pass at both (`test_prespend.py`'s other pins among them), and 28 skip
    (the corpus check, without the licensed calls).

**BOUNDARY.** "Words" are the guard's: split at whitespace, at every dash form and at a slash
(round 2). The round-0 counts in the table are whitespace-only. The population is the 27
committed pages at main `85152609`, with each page's calls on disk on 2026-11-12 (the Drive
mirror). The scan covers `git ls-files` with a `.json`, `.md`, `.jsonl`, `.txt`, `.html`, `.js`,
`.py` or `.csv` suffix, at this branch's head.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **History keeps the words.** The cut removes them from every tracked file. Git history, and the
  panel's frozen blobs read from it (`vinci/evals/synthesis_panel.json`'s freeze), still hold
  them, as the operator accepted when the repo went public (un-tracking would not un-publish
  history).
- **A refused build costs a re-run.** The draws are spent by the time the guard reads the
  synthesis; publishing would cost the licence.
- **The scorer fingerprint changes** (`synthesis.py` and `schemas.py` are in
  `compare.SCORER_FILES`), and panel draws now carry the TRANSCRIPT-RUN flag where they copy a run.

- **The guard cannot see provenance: the false-positive class, accepted.** A synthesis that
  copies a 10-Q, 8-K or Key Developments sentence that management also read on the call shares
  that run with the call. The page is refused after its paid draws, though the words are the
  filing's (review round 2).
  - Measured here, outside the synthesis, on the 25 committed pages with calls. Each figure is
    the longest run any mechanical string shares with its page's own calls, under the guard's
    fold:
    - MVST's driver-row quotes, 39 words;
    - BRBR's 24 and BURL's 23 (Key Developments rows);
    - EPAM's release QA flag, 16;
    - TJX's guidance quote, 14;
    - TJX's, CNXC's and ROST's driver rows, 13.
  - No committed synthesis trips it. Falsifier: a build refused for a run whose words are a
    filing's.

**FOUND, NOT FIXED.**
- The guard reads the synthesis only. Transcript driver rows are held by
  `test_public_transcript_text.py`; any other public field that could carry a transcript's words
  is not read against the calls.
- A cut drops the 12th word's own trailing punctuation with the run. Neither committed cut has
  any there.
