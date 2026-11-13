---
status: shipped
date: 2026-11-12
prs: [1042]
supersedes:
superseded-by:
---

# The per-machine preview config leaves git, and the local-path guard reads `.claude/` and `bin/` too; `bin/commit` was already clean and the records stay as written (STATE row 49 closed under the coordinator's default 6, not an operator ruling)

**WHAT.**
- **The authority.** This builds default 6 of
  `docs/records/2026-11-12-operator-delegation-and-defaults.md`: *untrack `.claude/launch.json`,
  clean `bin/commit`, and the records stay as written*. It is a default the coordinator adopted
  under the operator's delegation, not an operator ruling, and the operator can reverse it.
- **`.claude/launch.json` is no longer tracked, and is git-ignored.** The Claude desktop app reads
  it to start preview servers. Each entry names its own checkout's absolute folders, and
  `tests/test_config.py::test_every_preview_server_serves_an_absolute_directory` requires that. So
  a shared copy always named other machines' users, worktrees and session scratchpads, in a public
  repo. Each checkout now keeps its own copy, out of git. No example file ships: an example would
  need an absolute folder to pass that test, and the desktop app writes a new file when a checkout
  has none.
- **The guard reads two more folders.** `tests/test_no_local_paths.py`'s `SCANNED` is now
  `data`, `frontend`, `scenarios`, `tests/fixtures`, `.claude` and `bin`. That widening is what
  row 49 asked for. The guard reads tracked files and untracked ones that are not ignored, so the
  `.gitignore` line is what keeps each checkout's own `launch.json` out of the scan.
- **`tests/test_config.py`'s preview test** reads the local `launch.json` where a checkout has one.
  Where it has none (CI, a fresh worktree) it skips and prints why. Before this change it would
  have crashed in CI, where the file no longer exists.
- **`bin/commit` is unchanged.** Its one hit, the venv default naming one machine's checkout, was
  removed by #996 (fix request 2, RH-D3) on 2026-11-11. That was the last change to the file, and
  the widened guard now holds it at zero.
- **The records stay as written**, per the default. `docs/records/` stays outside the guard.
- **Two edits from the pre-PR review.**
  - RUNBOOKS' monthly-score step no longer counts `launch.json` among the primary's files that
    make `bin/commit` refuse.
  - The guard's scratch-repo helper (`_repo`) switches off the machine's global git excludes.
    Otherwise a global `bin/` or `.claude/` ignore, both common, would make its pins test that
    machine rather than this repository's `.gitignore`. The reviewer reproduced that failure
    with a global `bin/` ignore.

**WHY.** Row 49 (2026-11-05) surveyed every tracked file outside the guard's four artifact
folders. It found per-machine paths in four places: the preview config, `bin/commit`, records'
prose, and one theme-intelligence run log. The default sorts them. The two config files are
per-machine settings, the kind the Claude Code settings docs keep out of git (as this repo already
does for `.claude/settings.local.json`), so they get fixed and guarded. A record's body is
immutable once merged, so the records stay. The run log is one the default does not name, so
it stays too (below).

**HOW VERIFIED.** All on branch `claude/defaults-6-7-d8490f`, cut from main `407dc809`:
- **The new pin failed first.**
  `test_the_agent_config_and_the_local_gate_are_read_and_the_preview_config_is_not` builds a
  scratch repository with THIS repository's `.gitignore` copied in, not restated. Before the fix
  it failed listing no hits at all, because the scan did not reach `.claude/` or `bin/`. With
  `SCANNED` widened and the ignore line not yet added, it failed again, because it read the
  untracked `.claude/launch.json`.
- **Corpus before synthetic.** With `SCANNED` widened and `.claude/launch.json` still tracked,
  the live guard
  (`test_no_committed_page_mirror_or_fixture_carries_an_absolute_local_path`) failed with **18
  hits in 1,441 files, all 18 in `.claude/launch.json`**, the count row 49 gave. Once the file was
  untracked and ignored (it still exists in the working tree, as it does in every checkout),
  `python -m tests.test_no_local_paths` printed **0 in 1,440 files**.
- **Mutants, three, all killed:**
  - the `.gitignore` line removed: the new pin and the live guard both fail;
  - `bin` dropped from `SCANNED`: the new pin fails;
  - `.claude` dropped from `SCANNED`: the new pin fails.
- **The preview test** passes with this worktree's local `launch.json` present. With the file
  moved aside it skips, giving its reason.
- **The pull hazard, reproduced in two scratch repositories.** A commit that deletes a tracked
  file deletes it from every checkout that pulls it:
  - an unmodified local copy is deleted by the pull;
  - a modified one makes the pull ABORT ("Your local changes … would be overwritten").

  Copying the file aside, discarding the local change, pulling, and copying it back restored the
  modified copy, which then shows as ignored. The PR body gives the steps. This change touches no
  other checkout.

**BOUNDARY.**
- "18 hits in 1,441 files" is the guard's own count over `SCANNED`'s six folders: tracked files
  plus untracked ones that are not ignored, in this worktree at main `407dc809` with this branch's
  test and `.claude/launch.json` still tracked. "0 in 1,440" is the same scan after it was
  untracked.
- What stays outside the guard, measured over the 2,321 tracked files outside the six folders, on
  this branch's index (3,761 files, main `407dc809` plus this change):
  - `docs/records/`: 52 hits in 27 files. Prose, staying as written by the default. Row 49 counted
    19 in 16 at main `c4c9f432`; later records added the rest.
  - `docs/theme_intelligence/state-pull-ledger-2026-10-11/run-log.txt`: 2 hits, a session
    scratchpad in a committed run log. The default does not name it and nothing here changes it.
  - `STATE.md`: 7 hits, all in row 38's prose naming the two machines' user folders.
  - `tests/*.py`: 70 hits in 6 files, and `vinci/*.py`: 3 hits in 2 files. These are synthetic
    test literals, placeholder docstrings and one regex, not a checkout's paths.
- This record adds none.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Every checkout loses its local `launch.json` on the pull that brings this change, or the
  pull aborts if the copy is modified.** The steps in the PR body keep it. A checkout that skips
  them has the desktop app write a new file the next time a preview starts.
- **Git history still holds every committed `launch.json`**, as it holds the price-store paths
  (`docs/records/2026-11-05-no-committed-page-carries-a-local-path.md`). No history rewrite is
  proposed.
- **The preview test no longer runs in CI.** It never checked anything there but a file that
  described other machines. It still runs wherever a checkout has its own copy.
- **The run log's 2 hits and `STATE.md`'s 7 stay unguarded.** Row 49 is closed because its
  decided work is done. Reopening it for either is the coordinator's call.
