# CLAUDE.md — working instructions for the mosaic-theory repo

> This file is HOW to work in this repo. STATE.md is WHAT is true about the project right now.
> docs/engineering.md is the fuller engineering handbook (conventions, practices, workflow).
> Non-negotiable behavior and the fund guardrails live HERE; project state lives in STATE.md;
> detailed practice lives in engineering.md. Never duplicate state into this file — they drift.
> If this file conflicts with STATE.md on a matter of fact, STATE.md wins; this file governs behavior.

## The one thing this fund is

An AI-native, long-biased, US-first concentrated equity fund. The edge is **deep human judgment on
a few finalists, fed by an AI funnel that achieves breadth and cross-sectional reasoning a human
can't.** Everything you build serves that division of labor:
- **AI does** breadth, parallel assembly, and reasoning across the whole universe/graph.
- **The human decides** — the verdict on a finalist is never the machine's.
- The edge is the discriminator's hit-rate, measured by the **BUY−AVOID forward-return spread** —
  accumulated forward over calendar time. That number is the only thing that proves the fund works.

If a change blurs that line — code starting to make the judgment instead of feeding it — STOP and
flag it. That incremental blur is the failure mode this whole project is built to avoid.

## Session ritual (every time)

1. **Read STATE.md first** — the authoritative record of built / falsified / deferred / next.
2. End every build by **updating STATE.md**: built → how-verified; falsified → why; deferred →
   unlock trigger. A build that changes reality without updating STATE.md leaves the record lying.
3. Keep STATE.md accuracy-first: falsified is falsified, unproven is unproven. Never upgrade a hedged
   claim to a confident one to make progress look better.

## Non-negotiable behavior (every build)

- **Fail loud, never fabricate.** Missing data is `UNKNOWN`/raise — never a guessed number, never a
  silent imputation. A fabricated value corrupts the judgment it feeds; a loud failure is cheap.
- **Hold scope.** Make only the change asked. No refactoring adjacent code, no "clean up while I'm
  here." Find something else wrong → report it, don't fix it silently. Scope creep is how a
  verified-green module acquires a new bug.
- **Verify by showing real runs, not asserting.** "Tests pass" is not verification. Run it on real
  data, show the output, and demonstrate the **non-trivial / previously-broken** case specifically —
  not the easy case that was never in doubt. (The lookahead fix is the template.)
- **Suite stays green** — ruff + `mypy --strict` clean; `pytest -m "not network"` passes. No red commit.
- **Regression-test every bug fix** — a fix without a test that would have caught it isn't done.
- **Work on a local branch, never directly on main; merge only when green.** Decision-path changes
  (screen / ranker / ledger / scoring / freeze) also require a real shown run before merge — see
  docs/engineering.md for the full workflow.
- **Push when done** — commit, then push to origin. Unpushed work is a single point of failure.
  (Cloudflare Pages auto-deploy applies ONLY to a frontend reading committed snapshots — not backend.)

## Security & secrets (non-negotiable)

- **Secrets never touch code or git.** API keys (Polygon, Anthropic), tokens, credentials live in env
  vars / GitHub Actions secrets ONLY. Never hardcoded, committed, or printed to logs/stdout. A key in
  the repo is the single most likely real security incident here. Read secrets from env; fail loud if
  absent.
- **Never commit or log, ever:** licensed CIQ data and CIQ-derived relationship data (git-ignored,
  manual-pull: `data/manual/ciq`, `data/graph_*.json`, `*.db`); any credential/token; (later) any LP/
  investor PII. Committed artifacts are: code, JSONL snapshots, STATE.md/docs. Format NOTES are fine;
  pasted licensed tables are not.
- **Execution is human-authorized and paper-gated** (when execution is built): nothing places a trade
  without an explicit, deliberate human action; default is paper; no code path reaches a live broker
  autonomously. State this in any execution code from its first line.

## Project guardrails (these encode the edge — violating them breaks the thesis)

- **Validate forward, never backtest.** No prior runs exist; alpha is provable only by a fresh forward
  paper track record. Never build or "validate" against historical outcomes.
- **Never tune on forward returns.** Any ranker/weight/threshold/score is set by FACE-VALIDITY (does the
  output look structurally right) — NEVER by what would have paid. No code path reads forward returns
  when setting parameters. Tuning on outcomes = overfit, replicable signal = the thing this fund is not.
- **The control says no.** When a result depends on adjustment (sector/benchmark/factor), trust the
  de-confounded/control number over the persuasive raw one. Don't round noise up to signal. A control
  that should read ~0 but reads ±X tells you X is the noise floor.
- **The machine assembles and cites; it does not conclude.** Anything that surfaces/ranks/assembles
  ORDERS or INFORMS — it never renders the BUY/AVOID verdict. The human logs that by hand. An LLM
  verdict on a single high-stakes name is confident, fluent noise.
- **Source-bind everything** — claims (especially in dossiers) point to the primary cell/filing, so the
  human verifies rather than trusts the summary.

## Stack & layout (orientation)

- Python; `mosaic/` package (resolver, eod, edgar, universe, screens, ledger, scoring, graph, store).
- SQLite store + **append-only** ledger (no ledger-DELETE; the spread IS the accumulated ledger).
  Snapshots committed as **JSONL, not binary** — keep committed state diff-able.
- EOD via Polygon grouped-daily (5y); fundamentals via EDGAR XBRL + 8-K. No CIQ programmatic feed —
  CIQ is depth-stage, manual.
- **Manual** = the CIQ export + the verdict. **Automated** = everything mechanical in between.
- Fuller engineering conventions (reproducibility, re-run safety, as-of discipline, testing, code
  workflow) live in **docs/engineering.md**.

## Tone

Terse rules, not prose. The *why* lives in STATE.md §7, docs/engineering.md, and the planning fossils.
This file is the checklist you actually follow.
