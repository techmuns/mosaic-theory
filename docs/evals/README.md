# `docs/evals/` — the evaluation harness's committed records

`registrations.jsonl` is the registrations index (`vinci/evals/registry.py`; fix request 2, RG-D14
and RG-D9). One JSON row per event, appended, never edited:

- `registered`: written by `python -m vinci.evals register` / `register-run`. It is merged to main
  in a **docs-only PR before any paid draw**. `run-compare`, `run`, `score` and `score-run` refuse
  a registration whose row `origin/main` does not hold, so main's own history shows each
  registration before its draws.
- `drawn`: written by `run-compare` / `run` before a paid draw. A registration is drawn once across
  approvals, and a `register-run` registration's builds once each, under one approval. The rows are
  committed with the run's record.
- `judge_test_read`: written before the judge reads the gold's TEST half, which is read once.

A row holds shas, refs, pages, counts, an approval's sha256 and dates: never a local path, a
transcript or a ledger's contents.
