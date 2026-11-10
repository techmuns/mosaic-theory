---
status: open
date: 2026-11-10
prs: []
supersedes:
superseded-by:
---

# `vinci.evals run` draws only registered builds ($0, harness only): a `register-run` registration pins each page's request with its transforms, read at a given CIQ root; `run --registration --build` refuses an unregistered, repeated, out-of-order, moved, too-early or concurrent build before any spend, and writes each build's start, end and gap into the ledger; the six panel pins equal #935's registered CAND requests byte for byte

**THE ASK.** Step 2 of the vote-rule design's sequence
(`docs/records/2026-11-10-the-proposal-vote-rule-design.md` §8), from the coordinator after #950
merged: `vinci.evals run` gains `--transform`, `--ciq-root` and a registration, and records the gap
between builds, each behind a test that fails first. Nothing paid runs here. The measurement itself
is step 3.

**WHAT WAS WRONG, at main `9da0d096`.**
- **`run` drew without transforms.** It defined no `--transform`, so `__main__.py` read
  `getattr(a, "transform", [])`, which is always `[]`, and passed no comps export. It would have
  drawn the raw committed layer, not the request the measurement registers.
- **`run` read its inputs at the default CIQ root.** It had no `--ciq-root`, so `panel_inputs` read
  `replay.DEFAULT_CIQ_ROOT`, the assembler checkout's path, which does not exist on this machine.
- **`run` checked no request pin.** It took no registration, so a paid `run` drew whatever the code
  captured. That broke the module's own line: "a registration written before the first draw".
- **No time was recorded between builds.** The guard's ledger rows carry `seconds` per call and no
  wall-clock time. So the design's condition that each build opens on an uncached draw could not
  be shown, only assumed.

**WHAT CHANGED.**
- **`vinci/evals/builds.py`** (new): one condition drawn as separate builds.
  - **`RunRegistration`** pins the commit (resolved, never a branch), the transforms in order, the
    pages, the draws a build, the builds a page and `min_gap_s`, with each page's request sha256
    (`Request.wire`, the same pin as `compare`'s) and the CIQ root read. It refuses a `min_gap_s`
    under the prompt cache's lifetime (`synthesis._CACHE_TTL_S`, 300 s).
  - **`register_run`** ($0) captures each page's request at the commit (`capture_at`), from the
    frozen inputs read at the given root, with the page's own comps export whenever transforms are
    named, as `compare` does.
  - **`prepare_build`** ($0) makes every refusal before a draw:
    - a page or build the registration does not name;
    - a request the ledger records under ANOTHER registration: one approval draws a request
      once, however reworded the note that gives a second registration its own sha;
    - a build the ledger already records;
    - a page's builds out of order;
    - a build starting sooner than `min_gap_s` after the last build of its request ended;
    - a previous build with no end row (so its gap cannot be shown);
    - a re-capture whose bytes are not the pinned ones.
  - **`run_build`** (PAID) holds a lock beside the ledger (`<ledger>.lock`, non-blocking)
    while it checks and claims a build, so two `run`s of one build cannot both pass the
    drawn-once check during their captures. A second claim is refused at once.
  - It records a `build_start` row (start time, gap and the request's pin) and draws through
    `replay.run_request`, behind the existing guard and cap. It then records a `build_end` row,
    written in a `finally` so that a build the cap stops still has one. The end row holds the end
    time, the draws priced, the usable count (None when stopped), and the first draw's
    `cache_read_input_tokens`, read from the guard's own ledger row: 0 shows an uncached opening.
  - **The gap is per request.** The prompt cache is keyed by the prompt, so only a build of the
    same request can warm it, and builds of other pages may run in between. A build of the same
    bytes under another approval's ledger is not visible here; the first draw's recorded cache-read
    tokens are what show the opening.
- **`vinci/evals/__main__.py`:**
  - **`register-run`** ($0) writes the registration outside the repository, once. Its pages are
    `compare.registered_pages`: the panel whole, or target pages outside it.
  - **`run` requires `--registration` and `--build`.**
    - `--ciq-root` sets where inputs are read. Without it, `run` reads at the root the
      registration recorded, never the assembler's default.
    - `--transform`, `--code-ref` and `--draws` are cross-checks against the registration, refused
      when they differ.
    - `--label` is refused, because a build's label is derived from the registration.
    - Without `--paid`, `run` makes every check and the pinned capture, then draws nothing.
  - The `capture` and `prove` branches are unchanged.

**HOW VERIFIED.**
- **Fail first.** The 15 tests in `tests/test_evals_run_builds.py`:
  - **Twelve, written before the code, fail on main `9da0d096`.** Eleven import a module that does
    not exist there. The twelfth, a paid `run` with no registration, fails by drawing: "DID NOT
    RAISE ReplayError".
  - **Three came from review round 0, each failing first against the branch before its fix:**
    - a run without `--ciq-root` read at the default, not the registered root;
    - a reworded second registration of the same request drew it again ("DID NOT RAISE");
    - a second `run` of one build, started while the first captured, drew too ("the second run
      drew").
- **The pages are real committed ones** (NFLX). Only the two licensed reads are stubbed (the
  transcripts and the comps export); the capture child runs in-process for speed. One test keeps
  the real child (`capture_at` at `HEAD`) and matches the pin to the in-process capture.
- **The real $0 dry run, on this machine, at main `9da0d096`'s code:**
  - **`register-run`:** the frozen panel's six pages; the eight transforms in order (`asof_cut`,
    `relabel_drawdown_shape`, `trailing_only_note`, `survival_read`, `peer_gap_question`,
    `print_row_guide`, `gap_types`, `current_buybacks`); 10 draws by 4 builds; the gap 300 s; the
    primary checkout's `data/manual/ciq`, read only.
    - It printed `registered 3cba8cd6c660afd5: pages ['BURL', 'CNXC', 'LLY', 'MCK', 'ROST', 'SMPL'],
      4 builds of 10 draws a page`. Every page was captured; no transform refused.
    - **The six pins equal #935's registered CAND pins, byte for byte:** BURL `47bbd4210ebc`, CNXC
      `eeadb7c6a74f`, LLY `9bb586e54132`, MCK `21800fb99664`, ROST `33261190dc69`, SMPL
      `4f3c3ca0d0f1` (`docs/records/2026-11-09-fix3b-measured-on-the-panel.md` §2).
    - So at main, `asof_cut` is the identity on the panel, and the measurement draws exactly the
      requests #935 drew for #930.
  - **`run --ticker LLY --build 1`** without `--paid`, against a scratch ledger: `LLY build 1:
    every check passed (first build); nothing drawn`. The re-capture matched its pin.
    - With the final code it was re-run without `--ciq-root` for BURL and LLY, both reading at the
      registration's root: "every check passed".
  - **`--build 2`:** `LLY: build 2 before build 1 — a page's builds are drawn in order`.
  - **A paid `run` with no registration:** `` `run` needs --registration ``.
  - **The ledger held only its approval line** afterwards. The registration and the ledger stayed
    in the session's scratch folder, outside the repository.
- **The evals suite** (`tests/test_evals_*.py`) passes, with the new file in it.
- **Review round 0** (`/code-review high --fix`) found 9 issues: 5 fixed (three by the reviewer,
  two after it, each behind a failing test), and 4 left as below. The PR body's table lists all 9.

**FOUND, NOT FIXED.**
- **A build stopped hard (SIGKILL, power loss) has a start row and no end.** That page is then
  stuck under its registration: the build is "drawn once", and the next cannot show its gap. This
  is fail-loud by design; a recovery path is an operator ruling.
- **The end row's `draws` counts priced draws only.** A draw the API refused (`APIError`) is written
  to the draws file, not the ledger, so a failed first draw records its cache state as None.
- **A build that sends nothing still uses its slot.** For example, a cap too low for one worst-case
  draw stops draw 1 before sending. Whether such a build may be retried is a design call.
- **`write_registration` and the pin hash repeat `compare`'s.** Sharing them would edit
  `compare.py`, which is in the scorer fingerprint, and would orphan every registration already
  written.
- **`capture` has the same two gaps `run` had:** no `--ciq-root`, and no comps export for a
  transform that reads one. It is a $0 command, outside this brief.
- **The measurement's scorer is not built.** Step 3 scores the draws at $0 with the record's
  pre-registered statistic: Pearson's dispersion test on per-build counts, plus each option's
  outcome per build.
  - That code does not exist yet.
  - It should be committed, and its fingerprint written into step 3's registration note, before
    the draw, so the score cannot be written after the result.
  - That is the coordinator's call: a small $0 PR, or the first commit of step 3.

**BOUNDARY.**
- **Code:** main `9da0d096`, plus this PR.
- **Tests:** the 15 in `tests/test_evals_run_builds.py`. Every evals test passes with them.
- **The dry run:** the six panel pages (freeze `bcda7ce3`) and their inputs as the panel file pins
  them (page blobs and transcript sha256s), read from the primary checkout's `data/manual/ciq`, on
  2026-11-10. No call was sent. The registration and ledger stay outside the repository. The root
  they record is a local path, and it is not quoted here.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** No draw was made.
- **Accepted:** an unregistered paid `run` is now refused, where before it drew. No record or
  runbook step used `run` unregistered (the RUNBOOKS §n paid path is `run-compare`).
  - Falsifier: a session's paid one-condition draw that cannot be expressed as a registration.
    None is known.
