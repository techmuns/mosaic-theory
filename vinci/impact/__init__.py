"""THE IMPACT CHECK — a fix PR's cross-setup validation, base code against head code, at $0.

Operator, 2026-11-11: "we need to make sure the system verifies & validates fixes based on data
deterministically and its implication across the setup before being merged with main".
``python -m vinci.impact run --base origin/main --head HEAD --out <outside the repo>`` writes the
PR body's ``## Cross-setup validation (deterministic)`` section (RUNBOOKS §o), five parts, each
MEASURED on real committed data with code the only variable:

1. **fail first** — head's changed test files on base's ``vinci/`` and on head's (`run.fail_first`);
2. **pages** — every committed page built at $0 by both (`prespend.mechanical_build`, no LLM
   phase), compared VALUE by value, list members included (`values`);
3. **synthesis requests** — each side's request from its own build, byte for byte, and the six
   frozen panel pages from their frozen inputs (`evals.replay.capture_at`), with whether a STATE
   row-53 panel check is owed;
4. **rendered surface** — the committed JSON and the $0 page rendered by both, and
   ``frontend/build.py`` run by both;
5. **downstream readers** — the changed modules' importers (`graph`, static) and each offline
   consumer the diff reaches, run by both, outputs diffed.

Stamped (`stamp`) with base, head, date, the inputs boundary and the PR's own diff identity, so a
re-sync that only merges main keeps the report (`stamp.still_valid` states the rule). Nothing is
sent to a model and nothing is written to the repository: captured requests can carry licensed
transcript text, so the run folder is refused inside it.
"""
