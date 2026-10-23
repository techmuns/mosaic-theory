---
id: 2026-10-23-review-gate-judges-the-pr-checkout
status: open
date: 2026-10-23
prs: []
supersedes:
superseded-by:
---

# The review gate judges the checkout the PR comes from — `--head`, else a leading `cd`, else the session folder; unknown is gated

**WHAT.** `.claude/hooks/review_gate.py` now decides which tree a `gh pr create` publishes before
it measures code changes. In order:

1. `--head <branch>` (`-H`, `--head=`): that branch's commits since its merge base with `--base`
   (default `main`), which is the PR's exact content.
2. Otherwise, the directory the command `cd`s into before `gh pr create`, read the way the shell
   will run it: `shlex`, quotes, `&&`, `;`, newlines, heredoc bodies stripped. This means that
   checkout's commits plus its uncommitted changes.
3. Otherwise, the hook's `cwd`.

Three edge cases:

- **A `cd` the hook cannot resolve** (`cd "$W"`, `cd -`), or a `cd` into a directory that does not
  exist, with no `--head`, is UNKNOWN. Unknown is gated like code, and the refusal says why.
- **A resolved directory that is a checkout of another repository** is left alone.
- **The refusal names what it judged:** `branch X` or `the checkout at …`.

**WHY.** The gate read only the hook's `cwd`, i.e. the SESSION's folder. It fired live on
2026-10-23, the first time it ran in a real session.

- **The false positive, seen live.** PR #787 is docs only and was opened with
  `cd <its checkout> && gh pr create`. The gate refused it for 3 code files. Those were
  already-merged commits on the session's own stale branch (`claude/bounded-pr-review`).
- **The false negative, the reverse.** A session sitting in a clean folder could open a code PR
  from another checkout, or by `--head`, without a review.

**HOW VERIFIED.**

- **On the real checkouts,** with an empty transcript, so only the code-change decision is in play:

  | Case | Old gate (`main`) | New gate |
  |---|---|---|
  | The live false positive: session folder on the stale branch, PR from #787's docs-only checkout | exit 2, "3 code file(s)" | **exit 0** |
  | The reverse: a docs-only folder, `--head claude/bounded-pr-review`, a branch with 3 code files | exit 0 | **exit 2**, naming the branch |

- **`tests/test_claude_hooks.py` adds 6 pins** (31 passed in the file):
  - a leading `cd` to a docs-only checkout is not gated, quoted or not;
  - a code PR from another checkout is gated, and passes once reviewed;
  - `--head code` and `-H code` are gated, while `--head docs` and `--head=docs` are not;
  - an unresolvable `cd "$W"` is gated as unknown, unless reviewed or `--head` names a branch;
  - a PR from another repository's checkout is left alone;
  - `--head` is read through wrapper words (`time`, `env`) and GitHub's cross-fork
    `owner:branch` form.
- **Two existing pins changed meaning, not wording.** `cd x && gh pr create` (`x` does not exist)
  and `cd x\ngh pr create` now fail closed as unknown. The first version read a missing directory
  as "another repo" and let them through; both pins caught it, and the missing-directory rule
  followed.
- **Mutants.** Each was killed and restored:
  - judging the session `cwd` again → 5 pins;
  - ignoring `--head` → 2;
  - letting an unknown checkout through → 3;
  - reading a missing directory as another repo → 2;
  - the tokenizer, the regex, and the fork split, each without its fix → the new pin.

**This change's own pre-PR review** (`/code-review high --fix`) found 2 issues, both fixed and
pinned:

- **GitHub's cross-fork `--head owner:branch`** named no ref, so it was treated as code.
- **A wrapper word before `gh`** (`time gh pr create`, `env A=1 gh pr create`) hid the command
  completely. The tokenizer did not parse it, and the older gate's own `PR_CREATE` regex did not
  recognise it as opening a PR at all. Before this PR, `time gh pr create` on a code branch
  bypassed the gate.

**ALSO FOUND: hooks run from the PRIMARY checkout's copy.** The live refusal used the pre-#784
wording ("add a 'Code review (high)' section"). The session's worktree holds the new wording; the
primary checkout, at `ca17bc05` on 2026-10-23, holds the old. `.claude/settings.json` runs hooks
from `$CLAUDE_PROJECT_DIR`, which resolves to the primary checkout. So **a hook change takes effect
only when the primary checkout pulls `main`**. This fix included.

**BOUNDARY.**

- **Exit codes.** One run each, with an empty transcript file, on 2026-10-23.
- **The old gate.** `origin/main:.claude/hooks/review_gate.py` at `1256451d`.
- **Code files.** Matched by the gate's CODE pattern against the merge base with `origin/main`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **ACCEPTED: a `cd` hidden behind a variable fails closed.** The agent either names `--head` or
  runs a review. One extra step is the price of not guessing.
- **ACCEPTED: `-R other/repo` with a `--head` from this repo's checkout** is still judged in this
  repo.
