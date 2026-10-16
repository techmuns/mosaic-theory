---
id: 2026-10-16-theme-intelligence-cli-loads-dotenv
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — the CLI loads `.env` once at its entry point, so `market` runs locally

**WHAT.** During the live pilot's catch-up (2026-10-16), `market --as-of 2026-10-15` failed with
"Required environment variable 'POLYGON_API_KEY' is not set", although the key was in `.env`.
- The theme-intelligence CLI loaded `.env` only inside `_client`, the model-client setup.
  `market` never reaches it.
- Actions was unaffected: it injects its secrets as environment variables.
- The failed attempt is kept in the pilot registry as FAILED run R-20261016T163210Z-market.

The fix:
- `vinci/theme_intelligence/__main__.py` gains `entry(argv)`. The `python -m` block now calls it.
  It runs `load_local_env()` once, then `main(argv)`.
  - Locally that loads POLYGON_API_KEY, TIINGO_API_KEY and ANTHROPIC_API_KEY from the
    repo-root `.env`.
  - On Actions there is no `.env`, and an injected secret always wins (`override=False`,
    unchanged).
- `_client` no longer loads `.env` itself.

**WHY AT THE ENTRY POINT, NOT IN `main`.** `vinci/cli.py` loads inside its `main`, but here
tests call `main` directly; some delete `ANTHROPIC_API_KEY` to prove a command runs without it.
- `load_dotenv` sets variables for the whole process, and pytest's monkeypatch undoes only what
  it set. So one test calling a `main` that loads `.env` would hand every later test the real
  keys.
- Loading at the entry point, the rule `load_local_env`'s docstring states, keeps `main`
  hermetic.
- `_client`'s own call was the same leak in narrower form, which is why it went: every CLI run
  has already loaded `.env` before reaching it.

**HOW VERIFIED.**
- **Real run.** `market --as-of 2026-10-15 --thesis TH-16225B12C4`, each side on its own SQLite
  copy of the pilot registry, run with `python -m` and no API key in the inherited environment:
  - main a66a81e0: exit 1, "Required environment variable 'POLYGON_API_KEY' is not set";
  - this branch: exit 0, "market SUCCEEDED — 1 thesis(es) priced" (its 4 implied companies).
- **Pins** (`tests/test_theme_intelligence_cli_env.py`; each `.env` is a temporary file with
  placeholder values):
  - the entry point makes `.env`'s keys visible to `market`;
  - NEGATIVE: a secret already in the environment wins over `.env`;
  - NEGATIVE: `main` and `_client` never read `.env`.
- **Mutation.** 4 mutants, all killed: the entry not loading, `main` loading, `_client` loading
  again, and `.env` overriding.
- **Suite.** ruff and `mypy --strict` clean; `pytest -m "not network"`: 5843 passed.

**BOUNDARY.**
- Run 2026-10-16 around 16:57 UTC, on copies made from the pilot registry after its catch-up
  (v7).
- Each side used its own checkout's `.env`; both are links to the repo-root `.env`.

**WHAT IT COSTS / WHAT IS ACCEPTED.** A caller that imports `main` and expects it to read `.env`
now has to call `entry`. None exists: every caller found runs `python -m`, the six steps of the
weekly workflow and the manual runs.
