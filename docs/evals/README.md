# `docs/evals/` — the evaluation harness's committed records

`registrations.jsonl` is the registrations index (`vinci/evals/registry.py`; fix request 2, RG-D14
and RG-D9). One JSON row per event, appended, never edited:

- `registered`: written by `python -m vinci.evals register` / `register-run`. It is merged to main
  in a **docs-only PR before any paid draw**. `run-compare`, `run`, `score` and `score-run` refuse
  a registration whose row `origin/main` does not hold, so main's own history shows each
  registration before its draws.
- `drawn`: written by `run-compare` / `run` before a paid draw. A DESIGN is drawn once across
  approvals: each `registered` row carries its design key (`design`), and a registration whose
  design another registration has drawn is refused, whatever its words (#1030's review round 1). A
  `register-run` registration's builds are drawn once each, under one approval. The rows are
  committed with the run's record.
  - Since round 2, each `registered` row also records its request pins (`pins`), and both are
    derived from the registration, when the row is written and again at the draw.
  - A registration whose every pin another registration already drew is refused, except by the
    run a replication replicates.
- `judge_test_read`: written before the judge reads the gold's TEST half, which is read once.
  `judge.run_half` claims it itself (round 2).

A row holds shas, refs, pages, counts, an approval's sha256 and dates (a design key and a request
pin are sha256s): never a local path, a transcript or a ledger's contents.
