---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

12. **TESTS-WRITE-TO-TMP — CONVENTION WRITTEN DOWN 2026-07-27** (the flag above, closed):
   *"A test that writes MUST write under pytest's `tmp_path`, never into the repo. A test that
   mutates a committed artifact makes the suite order-dependent and can leave a dirty tree that
   the next artifact pass commits by accident."* Already de-facto practice in 23 test files; it
   was carrying no STATE record, so it could not be cited, taught, or enforced. Recorded now as
   what it is — an adopted convention, not an aspiration.
