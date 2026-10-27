---
id: 2026-10-27-codex-rereviews-the-fix
status: shipped
date: 2026-10-27
prs: [815]
supersedes:
superseded-by:
---

# Codex reviews a PR twice when it finds something: the push that fixes it gets one more `@codex review`, posted by the hook, never a third

**WHAT.** Three changes.
- **The re-review is a hook, not a step to remember.** After a `git push`, `codex_request.py` posts
  a second `@codex review` on the PR when all of these hold:
  - the push landed: an open PR has the pushed branch as its head and the checkout's HEAD as its
    head commit;
  - the PR carries exactly one request so far;
  - Codex's own record on its summary comment (`codex-review-state:v1`) says its review completed
    and found something;
  - the push changed CODE, by the review gate's rule, since the commit Codex reviewed.
  
  With two requests on a PR it never asks again. The pr-feedback skill's §4 now says the hook does
  this, and §3 says to push a round's fixes together. CLAUDE.md's bounded-feedback rule says it too.
- **One shell reader for both hooks.** `review_gate._walk`'s token loop became
  `review_gate.commands()`, which yields each simple command with the directory it runs in. The PR
  gate reads creates through it, and `codex_request.pushed()` reads pushes through it.
- **A heredoc no longer swallows the rest of its marker's line.** `HEREDOC` removed everything from
  `<<'MSG'` to the terminator, including `&& git push` written after the marker on the same line.
  `review_gate.unheredoc()` now removes the body only.

Also, outside the repo: the operator allowed `mcp__ccd_pr__set_monitor` in the user settings
(`~/.claude/settings.json`, `permissions.allow`). The opener hook now tells the session to switch
Auto-fix on, so Codex's comments, on both reviews, wake it.

**WHY.**
- **The operator's rule (2026-10-27):** when Codex finds issues and the session fixes the PR,
  Codex reviews again. A fix written to answer Codex is code Codex never saw. A push does not
  re-trigger Codex, and the skill's hand-posted re-review fired only "when a FIX changed behaviour
  beyond the lines the comment named". That was a judgment call and a forgettable step.
- **Replayed on the real PRs #770–#813,** the rule asks on exactly #791, #793, #796 and #799. Those
  are the four where Codex found issues and the session then pushed code it never re-reviewed.
- **The Auto-fix half:** #813's session could not switch Auto-fix on because auto mode refused
  `set_monitor`. The tool asks the user per call, and a brief from another session is not the user
  asking. Without Auto-fix, neither of Codex's reviews reaches the session.

**HOW VERIFIED.**
- **Reader refactor, before the heredoc fix.** Over every Bash call in this project's transcripts,
  `_walk` gives the same answer as #813's on all 74,706 commands.
- **Heredoc fix:**
  - The push reader goes from 2,632 to 3,000 commands read as a push (+368).
  - PR creates read go from 1,034 to 1,037 (+3, all real `… <<'MSG' && git push … && gh pr create`
    forms), and none are lost.
  - `_walk`'s answer changes on 8 commands. Checked one by one, all 8 now raise on unbalanced
    quotes: the kept marker line opens a quote that closes only after the heredoc body. 5 open no
    PR. The other 3 are the +3 creates, caught by the gate's regex path; their checkout now reads
    as unknown, so they are gated as code.
- **Pushes still unread:** of the commands that name `git … push` on one line, 160 are not read as
  a push. A heuristic search for `git push` in command position, after quotes and heredocs are
  removed, finds a real push in 1 of them. The rest are mentions inside quotes or heredoc bodies.
  That 1 is a 30-line command whose `--body` quote runs across the heredoc, one of the 8 above.
- **History replay.** On PRs #770–#813, 26 carry Codex's state comment:
  - Codex found something on 7.
  - The hook would ask on 4 of them (#791, #793, #796, #799).
  - It would not ask on #800, which already had 3 requests posted by hand.
  - It would not ask on #810 or #811, where only records changed after the review.
- **Pins:** 8 new tests in `tests/test_claude_hooks.py`.
  - Each condition has its own negative pin. Codex's summary comment is #811's, verbatim except
    for the commit and the two values.
  - Push forms come from the transcripts: behind a commit heredoc, the gh credential helper with
    `HEAD:<branch>`, `cd`, `-C`, `env -u`, and an upstream named apart from the local branch.
  - A push that has not landed tells the session and does not ask.
  - The gate refuses a create on a heredoc marker line.
- **Mutation:** 15 mutants, one per condition, plus the reader and heredoc changes. All 15 are
  killed. The upstream-branch mutant survived the first run, and its pin was then added. The
  `--git-dir` and combined `-qn` mutants were added with the code review's fixes.
- **Gates:** `ruff` and `mypy --strict` are clean on both hooks. Both hooks parse as Python 3.9,
  the system `python3` the hooks run under.

**BOUNDARY.**
- **Transcript counts:** every Bash `tool_use` in
  `~/.claude/projects/-Users-work-Documents-GitHub-mosaic-theory*/*.jsonl`, 148 transcripts, read
  2026-10-27.
  - Each call counts once, so a command repeated across sessions counts each time.
  - The reader-equivalence run saw 74,706 calls. The heredoc count run saw 74,721, because this
    session's own calls landed between the two runs.
  - "Read as a push" means `pushed()` returned a directory.
- **History replay:** PRs #770–#813 in techmuns/mosaic-theory, read 2026-10-27. A PR counts when
  its conversation carries Codex's `codex-review-state:v1` comment. The state is Codex's LATEST
  review, decided at the PR's final head.
- **Mutation:** this branch's working tree before commit, with `tests/test_claude_hooks.py` run in
  full against each mutant.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **API calls:** every `git push` now makes one `gh pr list` call (about a second). A push whose
  PR head has not moved yet makes up to three calls with 2-second waits. No further look starts
  after 10 s, and the push path's gh calls are capped at 20 s each, so the hook stays inside its
  90 s.
- **The pushed commit is the checkout's HEAD.** A push of another ref onto the PR's branch
  (`git push origin other:code`) is not recognised as landed. It waits, and if Codex found issues
  and code changed, it tells the session to check by hand. Found by the code review and left as
  it is: the session is told, never silently skipped.
- **Trigger timing:** the re-review fires on the FIRST code push after Codex's findings. A code
  push before the round's fixes, such as a lint fix pushed early, spends it. The skill's §3 says to
  push a round's fixes together.
  - Falsifier: a PR whose second Codex review is of a commit older than its round-1 fix.
- **Codex's state comment is Codex's undocumented format.** If it changes, the re-review stops
  silently, because no record means no request.
  - Falsifier: a PR where Codex found something, the session pushed a code fix, and the PR still
    carries one request.
- **A command the shell reader cannot tokenize yields no push and no directory.** Those are a quote
  opened on a heredoc's marker line and closed after its body: 8 in the corpus, and at least 1
  holds a real push.
- **The `set_monitor` allow rule lives in the operator's user settings, not the repo.** Another
  machine or account does not have it, and on those the opener's instruction to switch Auto-fix on
  asks the user.
- **Found, not fixed (the operator's file):** `~/.claude/settings.json` → `autoMode.environment`
  still describes the repository as private. It has been public since 2026-10-22
  (`docs/records/2026-10-22-repo-made-public.md`), and auto mode's classifier reads that text.
