---
id:
status: shipped
date: 2026-11-17
prs: []
supersedes:
superseded-by:
---

# Each LibreOffice conversion runs under a user profile of its own, removed after, and a paid build that cannot read a call refuses before its first model call. VRRM's Q1 2026 call (run `6043fb83`, $5.15) was lost to two conversions sharing LibreOffice's one default profile. Reproduced at $0: 4 of 14 conversions lost under the default profile, 0 of 14 with a profile each. Under the same load, VRRM's own two calls: main's command lost Q1 in 5 of 5 trials, this code read 2 of 2 in 5 of 5. No text moves.

**WHAT.**
- **The cause.** `ciq.read_text` (`vinci/dossier/ciq.py`, the OLE branch) ran `soffice --headless --convert-to txt` with no `-env:UserInstallation`. So every build, precheck and suite conversion on the machine ran under LibreOffice's one default profile.
  - LibreOffice runs one instance per user profile. A second start under the same profile passes its request to the running instance. In every loss measured here, that second start exited 0 and wrote no `.txt` ("produced no .txt output").
  - VRRM's record names the function `ciq.extract_text`, and so does `vinci/impact/child.py`'s `own_soffice_profile` docstring. No function of that name exists. The conversion is `read_text`, and the docstring is left as it is.
- **The fix: one helper, `ciq.libreoffice_convert(soffice, src, to, outdir)`.**
  - It runs one conversion with `-env:UserInstallation=<a tempfile.TemporaryDirectory>` and removes that folder when it returns. It never raises on LibreOffice's exit: the caller reads it.
  - Every `soffice` call site goes through it:
    - `ciq.read_text`, the one production conversion;
    - `tests/test_ciq_file_kinds_and_pdf_profile.py::test_ra_d17_a_pdf_tearsheet_reads_its_industry`, the suite's one direct conversion, which ran under the default profile in any suite where SMPL's export is linked.
  - **Searched:** `git grep -i` for `soffice`, `libreoffice`, `UserInstallation`, `convert-to` and `--headless` over `vinci/`, `tests/`, `.github/`, `scripts/` and `.claude/hooks/`. Three production files name LibreOffice's binary:
    - `ciq.py`, the conversion;
    - `vinci/impact/child.py` (`own_soffice_profile`), a `subprocess.run` wrapper that adds a per-process profile unless the arguments already carry one;
    - `vinci/impact/run.py` (`_own_profile_here`), which loads that wrapper for the parent's panel replay.
  - The wrapper is **kept**. The impact check builds old refs, whose `read_text` predates this. On this code the wrapper sees the flag and adds nothing.
- **Why per conversion, not per process.** `assemble_all` builds up to 8 names on threads of ONE process (`max_workers=8`). A per-process profile would still be shared by them.
- **The pre-spend question: yes, the paid build spent.**
  - `assemble_one` reads the slice (`ciq_sheets.transcript_for_synthesis`) before its `if llm is not None:` block. A call missing from it was flagged and the build went on to its covenant, driver and five synthesis calls. That is how run `6043fb83` spent $5.15 on a page that was held.
  - **Now:** `assemble._refuse_unread_calls` raises `DossierAssemblyError` when a paid build (`llm` not None) has a call on file missing from the slice. It runs right after the slice is read, before `extract_covenant_terms`, the first paid phase.
  - **The $0 build is untouched.** `llm` is None for the precheck's `prespend.mechanical_build` and for the impact child, so they keep the flag.
  - **In a batch,** a refused name is a per-name error with its run line written (`assemble_all` records refused builds), at $0.
  - "Missing" has one reader, `ciq_sheets.unread_calls`, which the flag and the refusal share. It is every call on file whose read failed or gave no prose. A call cut at the ceiling is in the slice, so it is not missing.
- **How RA-D11 (#957, fixed) relates.** RA-D11 turned LibreOffice's non-zero exit from a crash (`CalledProcessError`) into a `CiqParseError`, so one failed read left out and named its call instead of killing the build. That stays, and it is what lets this refusal name the call. The refusal moves the loud part, for a paid build only, from a flag after the spend to a refusal before it. Three readers of the same calls already refused a call on disk that does not read: `driver_pass.prepare`, `transcript_run_pass.run` and `confirmation.page_transcripts`. The build was the one that went on. The fix-log row for RA-D11 stays `fixed`.
- **Not in the precheck.** The precheck's $0 build reads the calls at precheck time, so it cannot forecast a failure at build time. The paid build now refuses at $0 on its own read, so nothing is spent either way.
- **Vintage `2026-11-17.a-paid-build-reads-every-call`.** `assemble.py`, `ciq.py` and `ciq_sheets.py` are re-pinned to it. A paid page of this vintage read every call on file.

**WHY.** VRRM's AVOID is scored on 2026-12-16, and its rebuild (STATE row 32 (32)) was ruled to run "while no other LibreOffice conversion runs", which needed every session on the machine idle. The machine runs several sessions at once, each running suites. A rule the machine cannot keep is not a control, so the cause is removed instead. A flag on a page the build paid for is the wrong place to learn that a call was lost: the page is held and the money is gone.

**HOW VERIFIED.**
- **Reproduced at $0**, on a generated RTF of synthetic text, through `soffice` directly:
  - **Two at once, no stagger.** Under the default profile, only the first trial lost one conversion: 1 of 6 (3 trials) and 1 of 20 (10 trials). With a profile each, 0 of 6 and 0 of 20.
  - **The second start staggered** 0.0, 0.2, …, 1.2 s into the first (7 offsets, 14 conversions a mode). Under the default profile, 4 of 14 were lost, at the offsets 0.0–0.6 s, each with exit 0 and no `.txt`. With a profile each, 0 of 14 were lost.
- **Pins, each failing first on main's code:**
  - `test_four_conversions_at_once_all_read` runs real LibreOffice on 4 generated OLE documents behind `.rtf` names, started 0.15 s apart. On main's `read_text` it failed **8 of 8** runs, each losing 2 of 4 ("produced no .txt output"). On this code it passed **10 of 10**. The fixture then made its document with its own `soffice` command. The review moved it onto `libreoffice_convert`, so at main's code it now fails at the missing helper, not the collision.
  - `test_each_conversion_is_handed_a_profile_of_its_own_and_it_is_removed_after` uses a stub that logs its arguments and writes into the profile it is handed. On main it failed: no `-env:UserInstallation` was logged.
  - `test_a_failed_conversion_is_loud_and_its_profile_is_removed_too` uses the same stub, exiting 1. On main it failed: no profile was logged. On this code it raises `CiqParseError` and the profile is gone.
  - Three refusal pins in `tests/test_libreoffice_exit.py` (paid refusal, $0 and whole-read negatives, source order before the covenant phase) failed on main, where `_refuse_unread_calls` did not exist. A fourth, on AMZN's real calls, runs where the licensed folder is linked.
  - RA-D11's stub now finds the source and `--outdir` by name, not by position, because the profile flag comes first.
- **VRRM's real calls under the shape of run `6043fb83`.** VRRM's two calls (both OLE) were read through `transcript_for_synthesis` while two conversions of a generated file ran under the default profile, started at 0.0 and 0.5 s; the read started at 0.2 s. 5 trials each:
  - **main's command** (the helper swapped for main's exact argument list): Q1 lost in **5 of 5** trials and Q2 in 2 of 5, so 7 of 10 calls lost. The refusal named each lost call.
  - **this code:** 2 of 2 read in **5 of 5** trials, 0 of 10 lost.
  - **No text moves.** Read alone, main's command and this code give the same text: Q1 6,584 words, sha256 `f0f9d7d495…`; Q2 7,464 words, `a6904be912…`; the whole slice `87ecb881f9dc…`.
- **Nothing left behind.** After 10 pin runs and 10 VRRM trials, the temp dir held 0 `vinci-soffice-profile-*` folders.
- **Gate:** GATE_LINE
- **Impact check:** IMPACT_LINE

**BOUNDARY.**
- Every run was on this machine (macOS 14.5, LibreOffice 26.2.4.2), on 2026-11-17, against main `6b5fbe51` and this branch.
- **A conversion is "lost"** when `soffice` exits non-zero or writes no `.txt`. A call is "lost" when it is missing from `transcript_for_synthesis`'s slice (`ciq_sheets.unread_calls`).
- Word counts are `str.split` on each call's section of the slice, after the reader strips the boilerplate. Hashes are sha256 of that section.
- "0 of 26 committed pages carry the flag" is `grep -l "transcripts on file but unparseable" data/dossiers/*/dossier.json` at main `6b5fbe51`.
- Timings come from 4 conversions of a 3,000-line generated RTF per profile mode.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **About 0.9 s more per conversion.** That is LibreOffice's first-start set-up on a fresh profile: about 2.0 s against about 1.1 s warm, over 4 conversions each. A build pays it once per call read, and a local suite once per conversion it runs.
  - A copied warm template profile measured about 0.15 s extra. It was not taken: it needs state shared across the process and clean-up at exit.
- **A call that never reads now blocks every paid build of its name until it is re-exported.** A corrupt export is an example. 0 of 26 committed pages carry the flag today, so no current name is blocked. **Falsifier:** a paid build refused on a call that reads when run alone means the cause is the reader, not the load.
- **A profile can be left behind.** A process killed mid-conversion cannot clean up, and a profile LibreOffice still holds when it returns is left, not raised (`ignore_cleanup_errors`, from the review). An `OSError` there would escape `transcript_for_synthesis`, which skips only a `CiqParseError`, and turn one read into a crash: the class RA-D11 closed. Each leftover is about 0.5 MB in the temp dir. 0 were left in this record's runs.
- **Wording left as it is.** The flag (`unparsed_transcript_flag`) and the refusals of `driver_pass`, `transcript_run_pass` and `confirmation` still name "a conversion while another runs" as a cause. That stays true of main's code and of any older checkout; it no longer describes this code's conversions.
- **The VRRM rebuild is unchanged.** It is still owner A, still after #1089, and still capped at $7.76, as ruled. Once this merges it no longer needs every session idle (STATE row 32 (32)).
