# Review guide for Gemini Code Assist — mosaic-theory

You are a second reviewer whose comments a Claude session triages. Every comment costs a triage,
so comment only on a defect you can state as a concrete failure: which input or state, which wrong
output. The full rules are in `CLAUDE.md`. Flag only what breaks one of the checks below.

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

## Do not comment on

- Style, naming, formatting, docstrings or comment wording — ruff and `mypy --strict` gate those.
- Defensive checks, abstractions or refactors with no failure you can name.
- Committed data, records and prose (they are ignored by `.gemini/config.yaml`).
- Anything you would rate below HIGH.

Do not push commits or post suggestion blocks meant to be applied as they stand: the PR's own
session is the only writer, and it fixes a finding only behind a test that fails first.
