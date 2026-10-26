---
id: 2026-10-26-review-gate-counts-only-opened-prs
status: shipped
date: 2026-10-26
prs: [803]
supersedes:
superseded-by:
---

# The review gate counts a `gh pr create` as a PR opened only when it opened one — a failed or refused create no longer voids the review before it

**WHAT.** `.claude/hooks/review_gate.py` needs a code review after the last PR the session
opened. It used to treat every earlier `gh pr create` call as a PR opened. Now it reads each
call's recorded outcome from the transcript:

- **Opened.** The call's result carries Claude Code's own record of a created PR
  (`toolUseResult.gitOperation.pr`, `action: "created"`). If there is no such record, the URL gh
  prints counts instead. The rule is `created_pr`, moved here from `codex_request.py`, which now
  imports it. So the gate counts a PR as opened exactly when Codex is asked to review it.
- **Not opened, so skipped.** The result is an error (`is_error: true`: refused by this hook, or a
  non-zero exit). Or the call ran but recorded no created PR: a failure that a pipe hid from the
  exit code.
- **Outcome unknown, so it counts as opened.** No result is recorded; or the result shares a
  transcript entry with other results, where Claude Code records no `toolUseResult` to read; or
  the call ran and printed nothing, so neither a record nor a URL exists
  (`gh pr create > pr.txt` opens a PR silently).

**WHY.**

- **The incident.** On 2026-10-23 a session ran `/code-review high`, then a `gh pr create` that
  failed on a wrong `--repo` (`nogods404/mosaic-theory`). The gate counted that failed call as a
  PR opened. When the real create came, the gate refused it, and the session had to run
  `/code-review high` a second time.
- **Why `is_error` alone would not have fixed it.** The failed create was piped through
  `tail -2`. It exited 0, and its result reads `is_error: false`. Four of the ten real failed
  creates read that way. Only the missing creation record shows that these opened no PR.
- **Why an unknown outcome counts as opened.** The brief suggested the opposite: an earlier create
  with no recorded result should not void a review. A probe in this session showed why that is
  unsafe. When one message makes several tool calls, an earlier call's result is not yet in the
  transcript when the next call runs. So an earlier `gh pr create` with no result may have just
  opened a PR. Skipping it would let a second PR from the same message open on the first PR's
  review. Counting it costs at most one extra review, the same fail-closed choice the gate already
  makes when it cannot tell which checkout a PR comes from.

**HOW VERIFIED.**

- **The live incident, run end to end.** The live transcript was cut at the refused create. Both
  hook scripts ran on it under the system `python3` 3.9, the interpreter hooks really use:

  | Gate | Exit | Output |
  |---|---|---|
  | `main` | 2 | "PR CREATION IS GATED ON A CODE REVIEW" |
  | this branch | **0** | none |

  The scratch checkout stood in for the session's branch, with one code file, so the gate's
  code-change rule applied.
- **Replay over every real create.** Old and new gates were run at every `gh pr create` in the
  session transcripts, each cut at that call. 4 verdicts differ, which are 2 distinct calls
  (forked transcripts carry their parent's calls). Both went from refused to allowed, and both
  are this bug:
  - the live incident above;
  - a create on 2026-10-17 that died on a network timeout (exit 1), whose retry 36 s later the old
    gate would have refused although an operator-typed `high` review preceded both. The gate did
    not exist yet, so no one was refused live.

  No verdict moved from allowed to refused.
- **Pins.** `tests/test_claude_hooks.py` has 5 new pins (46 passed in the file). Fixtures are
  copies of real transcript results:
  - a review, a failed create (piped, exit 1, or refused by this hook), then the real create →
    allowed. Red before the fix.
  - a review, a create that opened a PR (Claude Code's record, or gh's printed URL), then another
    create → refused. A failed retry before the PR opened, or a refusal after it, changes nothing.
    The review-then-refusal step was red before the fix.
  - a refused create with no review → refused. A refusal does not revive a review that an opened PR
    already used.
  - a create with no recorded result, a result in a shared entry, or a result that printed
    nothing → counts as opened.
  - `codex_request.created_pr is review_gate.created_pr`.
- **Mutants.** 11 of 11 killed, each restored byte for byte, run with `PYTHONDONTWRITEBYTECODE=1`:
  - an unknown outcome counts as not opened;
  - every create counts (the old rule);
  - an errored result counts as opened;
  - `is_error` ignored;
  - a shared entry's record attributed to every call in it;
  - a call that ran always counts, or never counts;
  - results not read at all;
  - a call that printed nothing read as failed;
  - the printed-URL fallback dropped;
  - `codex_request.py` keeping its own copy of the reading.

  A verbatim copy, which behaves identically, is killed only by the identity pin.

**BOUNDARY.**

- **Corpus.** Every `*.jsonl` under `~/.claude/projects/-Users-work-Documents-GitHub-mosaic-theory*/`
  on this machine, read 2026-10-26 at 11:15 UTC, after this change's review: 143 transcripts. The replay excluded this session's own
  transcript, leaving 142.
- **Creates.** A Bash `tool_use` matched by `opens_a_pr`. There were 387 distinct calls by
  `tool_use_id`, and 762 counted per transcript, because forks re-carry their parent's calls.
- **Outcomes of the 387:**

  | Outcome | Calls | What they were |
  |---|---|---|
  | Succeeded | 377 | Every one has `is_error: false`, `gitOperation.pr.action: "created"` and a PR URL. |
  | Failed, `is_error: true` | 6 | 2 refused by this gate, 1 network timeout, 2 shell parse errors before gh ran, 1 two-minute tool timeout. |
  | Failed, `is_error: false` | 4 | The wrong `--repo` piped through `tail -2`, two GitHub 502/GraphQL errors, and a failed push followed by a failed create. |
  | No result | 0 | |

- **Shared result entries.** 87,486 user entries carry a `tool_result`. 374 of them carry more
  than one, and every one of those records `toolUseResult: null` (counted at the first read, before
  this change's review).
- **The probe.** One run, on 2026-10-26. Two Bash calls were made in one message. The first slept
  2 s. The second ran at 10:53:35 UTC, after the first had finished, and found 0 results for the
  first in the transcript. The first's result entry is stamped 10:53:35.364.
- **The old gate.** `origin/main` at `545403de`. `review_gate.py` was last changed at `f62ddc32`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **ACCEPTED: a create that opens a PR inside a command that then fails reads as failed**
  (`gh pr create … && <a later step that fails>`, or an interrupt after gh printed its URL). Its result is an error, which carries no
  creation record. So the next PR in that session can open on the same review. This happened in 0
  of the 387 real creates. `codex_request.py` misses the same PR, because it fires only on
  success. The only fix would be to parse the error's rendered text for a PR URL, and the repo's
  rule is to read structured values where a structured record exists. **Falsifier:** an errored
  create whose output shows a PR it created.
- **The fix takes effect only once the primary checkout pulls `main`.** Hooks run from
  `$CLAUDE_PROJECT_DIR`'s copy (`2026-10-23-review-gate-judges-the-pr-checkout`).
- **Seen, not fixed (out of scope).** An operator-typed review is matched anywhere on a user
  entry's line, including inside a tool's printed output. A tool result that printed a typed
  `/code-review` command with a `high` argument would count as a review. There are 0 such results
  in the 143 transcripts, against 35 real typed `high` reviews.
