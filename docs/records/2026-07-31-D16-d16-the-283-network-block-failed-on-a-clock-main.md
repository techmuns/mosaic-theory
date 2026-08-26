---
id: D16
status: recorded
date: 2026-07-31
prs: [283]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
date-source: git (first commit containing this text)
---

**D16. THE #283 NETWORK BLOCK FAILED ON A CLOCK — MAIN WENT RED ON AN UNCHANGED COMMIT.** The
`offline_edgar` fixture raised `AssertionError` on any attempted fetch. Correct for a SILENT live
call; wrong for the case that actually occurred — a cached companyfacts entry aged past its TTL
mid-session, so the client wanted to re-fetch and three corpus pins reddened on a commit that had
been green forty minutes earlier. **A cache-warmth condition became a broken build.** The cold-cache
guard counts entries, but it cannot see an entry that exists and has expired, so the warmth check
passed and the block fired. **FIXED: the block now `pytest.skip`s with a stated reason** — it still
stops the fetch, still says why, and no longer depends on a clock. *A guard that fails on a clock is
a guard that gets disabled.* (Second time in two PRs that this fixture's own guard needed
correcting — first `is_dir()` on a directory the client creates, now TTL. D15 applies to it.)
**PROCESS FAILURE ALONGSIDE IT, recorded because it is the more dangerous one:** the commit ran
`pytest ... | tail -1 && git commit && git push`, and `tail` exits 0 regardless — so a RED suite
pushed. The gate must be its own command whose exit status is read, never piped into a chain.
