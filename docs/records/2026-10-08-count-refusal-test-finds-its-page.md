---
id: 2026-10-08-count-refusal-test-finds-its-page
status: shipped
date: 2026-10-08
prs: [679]
supersedes:
superseded-by:
---

# The count-refusal test finds a page whose prose cites a count — it no longer names AMZN's

**WHAT.** `test_the_refresh_path_refuses_when_a_cited_count_vanishes` (from #674) no longer names
AMZN and its `3↑/0↓`. It now takes the first committed page whose stored prose cites a revision
count that its own mechanical layer carries. It erases that count everywhere, and expects the refresh
to be refused with nothing written. If no page cites a count, it skips and says so. Test-only change.

**WHY — THE TEST BROKE THE RULE IT LIVES UNDER.** CLAUDE.md's TEST-LAYER RULE says an e2e test on a
LIVING committed artifact asserts only phrasing-independent invariants. A page and a count chosen by
hand is an LLM-string pin: the prose re-draws on every re-assembly. The AMZN re-assembly of
2026-10-08 rewrote AMZN's synthesis, which no longer cites any count. The test went red on its own
precondition ("AMZN's prose no longer cites it") in the full-suite run before that artifact PR was
pushed. Caught there, so no red commit shipped.

**HOW VERIFIED.**
- **On main's artifacts:** the test picks AMZN `3↑/0↓` and passes.
- **On the re-assembled AMZN artifacts:** the AMZN PR is stacked on this one, and its full-suite run
  covers this test against the new page.
- **Mutation:** unwiring `moved_cited_counts` from `refresh_dossier` turns it red.

**BOUNDARY.**
- **Population:** the committed dossiers on main @9adcf9a3, with the re-assembled AMZN page in the
  stacked PR.
- **Date:** 2026-10-08.

**WHAT IT COSTS / WHAT IS ACCEPTED.** None new. The unit pin `test_a_count_the_prose_cites_may_not_vanish_from_the_page`
still covers the guard's logic on fixed text.
