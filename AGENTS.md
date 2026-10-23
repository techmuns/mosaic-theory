# AGENTS.md — the cross-tool entry point

**This repo's rules live in [`CLAUDE.md`](CLAUDE.md). Read that file.** This one exists so a tool
that looks for `AGENTS.md` finds the door rather than inventing its own conventions.

`CLAUDE.md` is CANONICAL and this file is a POINTER, deliberately. The alternative — copying the
rules into both — is the twin-constant bug this repo has already paid for twice: a peer floor moved
from 6 to 5 in code while three surfaces went on saying "under 6", and eleven committed rows
contradicted their own caption. Rules restated in two places drift; a pointer cannot.
`tests/test_records_ledger.py::test_the_cross_tool_entry_point_points_and_does_not_copy` holds that.

## Where to look, by what you are doing

| you need… | read |
|---|---|
| how to work here — the non-negotiables, the guardrails, the build loop | `CLAUDE.md` |
| what is true right now, and what is open | `STATE.md` — start at **§5.0 OPEN NOW** |
| why something is the way it is; a past build, incident, ruling or falsification | `docs/records/` — `ls` is chronological, `grep` is the index |
| conventions, and what a house term means in plain words | `docs/engineering.md` |
| an operating loop to follow step by step | `docs/RUNBOOKS.md` |
| a superseded plan, kept for its reasoning | `planning/`, or any doc with a FOSSIL banner |

## The three rules most likely to bite a tool that skips CLAUDE.md

1. **Never merge.** Open a PR and stop. A human reviews and merges, per-PR, every time.
2. **Fail loud, never fabricate.** Missing data is `UNKNOWN` or an exception — never a guessed
   number. A fabricated value corrupts the judgement it feeds; a loud failure is cheap.
3. **Write a record, not an essay in STATE.md.** §5 is frozen. A build's narrative goes in a new
   file under `docs/records/`; STATE.md gets a §5.0 row and, at most, a ≤3-line claim with a
   pointer. See `docs/records/README.md`.

Everything else — the fund's guardrails, the brief and completion contracts, the security rules —
is in `CLAUDE.md`, and it is short enough to read in full.

## Code Review Rules

For Codex review of a PR: flag only what breaks one of the checks below, as a concrete failure.
Skip style and speculative hardening; never push a fix (`.claude/skills/pr-feedback/SKILL.md`).

### The decision line
- An LLM output that becomes a verdict, or a field that lets `Synthesis` carry one.
- A threshold, weight or mapping set from forward returns, or code that reads them to set a parameter.
- Any path toward placing an order or talking to a broker.

### Data integrity
- A missing value replaced by a guess, default or imputation instead of `UNKNOWN` or an exception.
- A value read from a date later than the run's as-of date (look-ahead).
- A number re-parsed from a display string instead of the structured value.
- A count printed beside a truncated list without saying it is truncated.

### Public repo
- A secret, token, raw CIQ export or `*.db` in the diff — this repository is public.
