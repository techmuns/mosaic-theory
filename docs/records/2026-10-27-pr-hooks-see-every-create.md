---
id: 2026-10-27-pr-hooks-see-every-create
status: shipped
date: 2026-10-27
prs: [813]
supersedes:
superseded-by:
---

# Both PR hooks see every way this project has opened a PR — `env -u GH_TOKEN gh pr create` (#812's form), a `GH_TOKEN=$(…)` prefix, and `gh api` POSTing to the pulls endpoint

**WHAT.** `review_gate.opens_a_pr` decides whether a Bash command opens a PR. Both hooks use it: the
PreToolUse review gate and the PostToolUse `@codex review` request in `codex_request.py`. The gate
also uses it to decide which earlier calls count as PRs already opened. It now reads three more
forms as a create:

- **`env` with its own options.** `env -u NAME`, `--unset NAME`, `--unset=NAME`, `-i`, `--`, …,
  before `gh pr create`. The prefix grammar allowed a bare `env`, but not its options.
- **A VAR whose value holds a space.** `GH_TOKEN=$(cat ~/.mosaic_gh_token) gh pr create`. The value
  pattern was `\S*`, so it stopped at the space inside `$( … )`.
- **`gh api` POSTing to `repos/{owner}/{repo}/pulls`.** The method can be `-X POST`, `-XPOST`,
  `--method POST` or `--method=POST`. With no method given, gh POSTs when any field (`-f`, `-F`,
  `--field`, `--raw-field`) or `--input` is passed. Any other method, or another path, opens
  nothing. That covers a GET of `…/pulls` or `…/pulls?state=open`, `-X GET … -f state=open`,
  `pulls/N`, a merge (`PUT pulls/N/merge`), reviews, comments and replies, and a reopen
  (`PATCH pulls/N`). A short option's value may be attached (`-fhead=code`, `-XPOST`), as gh's
  flag parser allows; this branch's code review found that the first draft missed it.
- **`gh pr new`.** This is `gh pr create`'s own alias (`gh pr create --help`, gh 2.102.0).

The word-by-word reading (`pr_target`, now `_walk`) finds the PR's head branch, its base and the
directory it runs in. It changed in three ways:

- It skips `env`'s options.
- It reads `head=` and `base=` from a `gh api` create's fields, as it reads `--head` and `--base`
  from `gh pr create`.
- It joins a backslash-newline into one command. Before, a `\`-continued `gh api` call lost every
  field on its later lines.

Each piece of the prefix grammar matches only one way. A `$` opens a `$(…)` only where a `(`
follows it, and an `env -u`/`--unset` name never starts with `-`. This branch's first draft let
both match two ways, so a long run of either, ending in no create, backtracked exponentially:
22 `$(a)` segments took 1.2 s, and each one more doubled it. `main`'s grammar had neither
ambiguity. A hook runs on every Bash call, so a pin now holds the reading to linear time.

Quoted strings and heredoc bodies are still data. A commit message or a test file that mentions
any of these forms opens nothing. Commands after `;`, `&`, `|`, `(` or a newline still count.

`created_pr` needed **no change**. It is the reading that finds the URL of the PR a call opened.
Probed on #812's real API record (24,469 bytes), it already returns #812: the last PR URL in what
`gh api` prints is the record's own `_links.html.href`. A pin now holds that, with a body that
cites another PR.

**WHY.**

- **The live incident.** #812 was opened with
  `env -u GH_TOKEN -u GITHUB_TOKEN gh pr create …`. The gate never checked it, because the
  detector did not read it as a create, and no `@codex review` was posted (the session posted one
  by hand). CLAUDE.md says to fix what a hook reports and never edit around it. That holds only if
  the hook sees what it should.
- **The route the memory said to use.** The memory note `open-prs-as-nogods404` recommended
  `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/techmuns/mosaic-theory/pulls -X POST …`. That
  command never contains `gh pr create`, so neither hook could see it at all. It was last used on
  2026-10-11, before the gate existed (2026-10-22). It is the shape that bypasses both hooks the
  moment it is used again.
- **The spaced value.** It was not in the brief. It surfaced when the corpus was replayed (below),
  and it is the most common missed form.

**HOW VERIFIED.**

- **Probe table, before and after.** 29 command shapes, each run through `opens_a_pr`:

  | Shapes | `main` | this branch |
  |---|---|---|
  | 4 forms already read (`gh pr create`, `env gh …`, `GH_TOKEN= gh …`, `env GH_HOST=… gh …`) | True | True |
  | 5 `env`-option forms | **False** | True |
  | 2 spaced-value forms | **False** | True |
  | `gh pr new` | **False** | True |
  | 5 `gh api` creates (memory-note form, implied POST, `--method POST --input`, inside `N=$(…)`, behind `GH_TOKEN="$(…)"`) | **False** | True |
  | 8 `gh api` calls that open nothing (GET list, list with a query, `-X GET` with fields, `pulls/N`, merge, comment, review, PATCH) | False | False |
  | 3 mentions (two quoted in a commit message, one in a heredoc) and `gh pr view` | False | False |

  13 of the 29 rows were wrong on `main`; 0 are wrong on this branch.
- **Replay over every real Bash call in this project's transcripts.** Each call was run through
  `main`'s and this branch's `opens_a_pr`:
  - 531 creates on this branch against 395 on `main`. The 136 new ones are 14 `env`-option forms,
    60 spaced-value forms and 62 `gh api` creates. Every one of the 62 was checked to contain a
    `gh api` POST to a bare `…/pulls` endpoint.
  - 0 calls `main` read as a create are lost.
  - For the 395 creates `main` already read, `pr_target` gives the identical directory, head and
    base. Among the 136 new ones, 125 have a head read from the command. The one directory that
    differs from main's walk is a create that runs before a later `cd`, which main's walk never
    reached.
  - Ablation: without the continuation join, 11 of the 531 targets differ (the `head=` field on a
    continuation line).
- **The hooks, end to end on this checkout, under the system `python3` 3.9.6.** The PreToolUse
  gate ran with this session's own transcript, in which no code review had run, then with a copy
  ending in one `code-review high` call:

  | Hook | Command | No review | After review |
  |---|---|---|---|
  | `main` | #812's form | allowed, unchecked | allowed |
  | `main` | spaced value | allowed, unchecked | allowed |
  | `main` | `gh api` route | allowed, unchecked | allowed |
  | this branch | #812's form | **refused (exit 2)** | allowed |
  | this branch | spaced value | **refused (exit 2)** | allowed |
  | this branch | `gh api` route, `head=` this branch | **refused (exit 2)** | allowed |

  The `gh api` row was run after this branch's first commit. Before that commit it named a branch
  with no commits, so the PR it would open changed no code, and the gate rightly let it pass.
  `codex_request.py` ran with a stand-in `gh` that only logs, so nothing was posted:

  | Hook | Command | Request |
  |---|---|---|
  | `main` | #812's form | none (0 `gh` calls) |
  | `main` | `gh api` route, #812's real API record as the output | none (0 `gh` calls) |
  | this branch | #812's form | `pr comment …/pull/812 --body "@codex review"` |
  | this branch | `gh api` route, #812's real API record as the output | `pr comment …/pull/812 --body "@codex review"` |

- **Pins.** `tests/test_claude_hooks.py` has 6 new tests (52 pass in the file). Their commands are
  real ones from the transcripts, with titles, body paths and branch names shortened:
  - the `env`-option and spaced-value forms are read as creates, and their `--head` is read. The
    forms read before still are; mentions and `env -u … gh pr view` are not creates.
  - `gh api` creates are creates, and their `head`/`base` are read: implied POST, inside `$(…)`
    before a later `cd`, and continuation lines. 8 real non-create calls on a PR are not. A quoted
    or heredoc mention of the create is not.
  - end to end through the gate: each route is refused unreviewed and allowed after a review. Its
    named head decides whether it is code (`code` gated, `docs` free). The 8 non-creates pass.
  - a `gh api` PR opened earlier in the transcript uses up the review, whether gh printed the URL
    or the whole JSON record. A 422 that a pipe hid from the exit code voids nothing.
  - `codex_request.py` asks for one review on each route, with the URL read from the API record.
    On a checkout that changes code, the 8 non-creates post nothing.
  - the reading stays linear: 25 `$(a)` segments, 37 `-u` and 36 `--unset` with no create after
    them each finish in under 1 s.
- **Mutants.** 11 of 11 killed, against the 5 new tests, restored byte for byte, run with
  `PYTHONDONTWRITEBYTECODE=1`:
  - `main`'s own `review_gate.py` (5 of 5 red);
  - the prefix without `env` options; the prefix without the `$(…)` value;
  - no `gh pr new`;
  - the walk without `env` options; the walk without the continuation join;
  - any method counts; an implied POST ignored; any `…/pulls…` path counts;
  - no `gh api` route in `opens_a_pr`;
  - the `head=` field not read.

  The timing pin was run separately against four grammars: commit 1's, and each of its three
  ambiguities alone. 4 of 4 are killed, each by a run that takes seconds where the fix takes
  microseconds.

**BOUNDARY.**

- **Corpus.** Every `*.jsonl` under
  `~/.claude/projects/*mosaic-theory*/` (recursive) on this machine, read 2026-10-27, without
  this session's own transcript: 624 files.
- **Calls.** 51,853 distinct Bash `tool_use` ids, dated 2026-07-13 → 2026-10-27. Forked
  transcripts re-carry their parent's calls, so calls are counted by id.
- **Creates.** A call `opens_a_pr` reads as a create. On `main` that is `18d19bfb`; `review_gate.py`
  was last changed at `f62ddc32`.
- **Dates of the newly read creates.** Spaced value 2026-07-20 → 2026-09-30. `gh api` 2026-07-23 →
  2026-10-11. `env` option through 2026-10-27, #812 included.
- **The probe table.** 29 hand-picked shapes. A shape is not a corpus count.
- **Shell comments.** 51 of the 51,853 calls carry a shell comment outside a heredoc, and none of
  them is a create.
- **The 30,000-character cap.** Measured on the 60 most recently modified transcripts: 30,833
  recorded Bash outputs, the longest exactly 30,000 characters, each beyond that carrying a
  `persistedOutputPath`.
- **PR bodies citing another PR by full URL.** 0 of the 100 most recent PRs (#713–#812), fetched
  2026-10-27.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **It takes effect only once the primary checkout pulls `main`.** Hooks run from
  `$CLAUDE_PROJECT_DIR`'s copy (`2026-10-23-review-gate-judges-the-pr-checkout`). Until then,
  open PRs with a plain `gh pr create` (the memory note says so).
- **Seen, not fixed (no real create needs it):**
  - **A `#` comment line before a `gh api` create hides it.** The word-by-word reading drops the
    rest of the command after a `#` comment, so a comment line ahead of the create hides it from
    both hooks. 51 of 51,853 calls carry a comment, and 0 of the 531 creates. A quote-aware
    comment strip was written, changed nothing on the corpus, and was taken out (CLAUDE.md:
    don't build speculatively). **Falsifier:** a create whose command opens with a comment line.
  - **Creates that never call `gh`.** Python `urllib` calls on the pulls endpoint (32, 2026-07-30
    → 08-03) and `curl -X POST …/pulls` (21, 2026-07-31 → 08-01). All predate both hooks, and the
    Python ones sit in heredocs, which are data by this rule. 0 GraphQL `createPullRequest`.
  - **`"$(gh pr create …)"` inside double quotes.** It reads as data, though the shell runs it.
    0 real.
  - **A `#` inside a word cuts the walk.** The walk uses shlex's comment rule, which starts a
    comment at a `#` inside a word, as bash does not. So in `gh pr create --title fix#3 --head
    code`, the head is not read, and the gate judges the session's checkout. This predates the
    branch: `main` reads `gh pr create` the same way. Turning shlex comments off would make an
    apostrophe in a real comment line unbalance the quotes. Found by this branch's code review;
    0 real creates are affected.
  - **Other wrappers' options.** `nice -n 10`, `time -p` and `gh pr -R x create` are not read.
    0 real.
- **ACCEPTED: `created_pr` takes the last PR URL in the output.** A `gh api` create whose JSON
  record runs past Claude Code's 30,000-character cap is cut before `_links`. If its body also
  cites another PR by full URL, Codex would be asked to review that other PR. Reading the record's
  own `html_url` would close it, but neither half of the condition occurs in the data above, so no
  code was written. **Falsifier:** a `gh api` create whose recorded output is cut at 30,000
  characters, with a body that links another PR.
