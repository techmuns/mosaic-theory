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
- **Work on a local branch, never directly on main. The agent opens a PR and STOPS — it never merges
  to main itself.** Green (ruff + `mypy --strict` + `pytest`) is *necessary but not sufficient*: a
  human reviews and merges. Merge only on **explicit, per-PR** approval — a prior "yes" is never
  standing permission for the next change. Decision-path changes (screen / ranker / ledger / scoring /
  freeze) also require a real shown run before merge — see docs/engineering.md for the full workflow.
- **Derived data artifacts may be auto-committed; code may not.** Regenerable, assemble-not-conclude
  artifacts — snapshot JSONL, the scoring report, per-ticker `dossier.json`/`.md` — may be committed by
  the pipeline / CI / a narrowly-scoped artifact step. **Never bundle a code change into an artifact
  commit**, and never let an artifact path become a backdoor for logic changes.
- **Don't build speculatively.** If a change can't be proven by a real run (data, creds, or environment
  unavailable), do NOT write it — propose it and surface the blocker. Prefer the simplest working path
  before writing any new code.
- **Push when done** — commit, then push to origin. Unpushed work is a single point of failure.
  (Cloudflare Pages auto-deploy applies ONLY to a frontend reading committed snapshots — not backend.)

## Security & secrets (non-negotiable)

- **Secrets never touch code or git.** API keys (Polygon, Anthropic), tokens, credentials live in env
  vars / GitHub Actions secrets ONLY. Never hardcoded, committed, or printed to logs/stdout. A key in
  the repo is the single most likely real security incident here. Read secrets from env; fail loud if
  absent.
- **Never commit or log, ever:** the **raw licensed CIQ workbooks** (`data/manual/ciq/`), the working
  DB (`*.db`), any credential/token, (later) any LP/investor PII. Pasted licensed CIQ tables are never
  committed. Raw CIQ stays git-ignored REGARDLESS of repo/deploy privacy.
- **DERIVED analytical artifacts ARE committable — to the PRIVATE/authed repo ONLY** (this repo is
  private; the Cloudflare deploy is authed/internal). They are derived analysis, NOT reproduced
  licensed content: code, JSONL snapshots/docs, **`data/graph_coverage.json`** (the EDGAR-10-K-derived
  customer/supplier **exposure map** — every edge carries a verbatim 10-K phrase + accession; it
  borrows only CIQ's relationship-*type* taxonomy, never workbook data), and the per-ticker
  **`data/dossiers/<TICKER>/dossier.json`** (extracted facts, each a `{value, source_ref}`). The
  committable set: snapshots (ranked queue, ledger, universe/screen counts) + `graph_coverage.json` +
  per-ticker `dossier.json`. **If the repo or the deploy ever becomes public, the graph + dossiers
  revert to git-ignored / local-only.** (`data/graph_test0.json` — the falsified Edge-3 test artifact —
  stays git-ignored; only `graph_coverage.json` is authorized.)
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
- **Parsers consume structured values, never rendered strings — display formatting is never
  load-bearing.** An extractor that produces a display string ALSO exposes its structured value(s); every
  consumer reads the structured value. If a string-parse is truly unavoidable it goes through ONE shared,
  tested helper — never an ad-hoc regex. (A thousands-blind re-parse of a `$1,101.80M` display string read
  it as `1` and fired a false reconcile caveat; two divergent parsers of the same string is the bug class.)
- **Three-tier human surface (DESIGN RULE v2).** `dossier.json` is machine-complete — every extracted
  fact stays in it. The rendered surface is THREE TIERS:
  1. **MAIN BODY** — decision values; ALWAYS printed. The human's decision surface.
  2. **ON-DEMAND** — context & audit (provenance: verbatim quotes, accessions, reference/agreement terms,
     amendment chains, per-item revision detail): a collapsed `<details>` on web, **EXCLUDED from print**.
  3. **JSON** — machine-complete, the full record behind every curated value.
  The **Financial-Summary appendix is decision data → it STAYS in print** (it is not provenance). Provenance
  appendices are the audit tier → on-demand. Curating never deletes a fact — a moved fact is reachable in
  the expanded web on-demand tier or the JSON. (Discipline/methodology language lives in `source_ref`s + JSON.)

## Stack & layout (orientation)

- Python; `vinci/` package (resolver, eod, edgar, universe, screens, ledger, scoring, graph, store).
- SQLite store + **append-only** ledger (no ledger-DELETE; the spread IS the accumulated ledger).
  Snapshots committed as **JSONL, not binary** — keep committed state diff-able.
- EOD via Polygon grouped-daily (5y); fundamentals via EDGAR XBRL + 8-K. No CIQ programmatic feed —
  CIQ is depth-stage, manual.
- **Manual** = the CIQ export + the verdict. **Automated** = everything mechanical in between.
- Fuller engineering conventions (reproducibility, re-run safety, as-of discipline, testing, code
  workflow) live in **docs/engineering.md**.

## Build-loop contract (how a brief enters and a PR leaves)

These govern the build LOOP itself. They are checklist, not aspiration — a build that skips one is
incomplete regardless of code state.

- **BRIEF CONTRACT — a build brief is malformed unless:**
  - every asserted data value carries its as-of/vintage; drift-prone values are marked
    **VERIFY-AT-BUILD** (never trusted from the brief);
  - every verify-gate naming a data value declares its **supplying layer** (assembled field vs new
    extraction) — the extractor boundary is checked at drafting, not discovered at build;
  - every new guard ships a **positive AND a negative pin** — what it must reject, with a real
    observed failure shape where one exists;
  - any summary/digest destined for an LLM phase carries a **shape contract + one literal example**
    (term → value → source_ref), never a pointer/count description.
  - **VOCABULARY.** In a brief, **"anchored" = DETERMINISTIC** (heading/regex, CI-pinnable on committed
    real-text fixtures); **"LLM-fenced" = an LLM extraction phase**. Bare **"fenced" is MALFORMED** — it
    conflates the two. Use structured-value determinism where the facts are numeric/verbatim (regex
    fidelity beats paraphrase risk); reserve LLM-fenced for a coverage-evidenced escalation tier.
  - **DERIVED-PIN SOURCE LAYERS.** A derived pin value must name the source LAYER of every component;
    a pin reachable only by MIXING layers (e.g. a filing's repayment amount summed into a CIQ-panel
    principal total) is MALFORMED — surface the mix, never force the number to match.
- **COMPLETION CONTRACT.** Every PR description ends with a per-brief-item disposition table —
  **SHIPPED / PARTIAL / SKIPPED / STOPPED** (+ a one-line reason for anything not SHIPPED) — and the
  real-run verify outputs. A build without this table is incomplete regardless of code state.
- **TEST-LAYER RULE.** A behavior observed failing in the rendered artifact is regression-pinned
  **end-to-end** (real committed JSON → render → assertion). Unit pins may accompany, never
  substitute. A second production failure of a pinned behavior ⇒ the pin was at the wrong layer.
  **Never pin an LLM-COMPOSED string** (synthesis text, an LLM-extracted covenant/twin composite):
  it reworders on every re-assembly, so an exact-string pin is guaranteed to rot the committed
  artifact. LLM-adjacent tests assert **deterministic ANCHORS** (the components present,
  order/phrasing-free — "components-present-together IS the composite-or-absent rule"), **structure**,
  and **guard behavior**. *Facts are stable; framing is weather — and weather applies to CI.*
- **INVARIANT RULE.** Every incident closes by shipping a machine check (lint / guard / coherence
  test), or is recorded in STATE.md as consciously accepted risk. STATE.md keeps the table:
  incident → invariant → shipped Y/N.
- **PREVIEW RULE.** Render/layout PRs run a Phase-1 preview from committed JSON and **STOP for
  approval**; data/extractor PRs go straight to build with real-run verification.
- **OPERATOR-ACTION RULE.** Operator to-dos arising from builds/audits are appended to STATE.md
  §Next-steps **by the build itself** — chat is not a ledger.
- **ARTIFACT-PASS RULE.** The standing post-merge artifact pass (re-assemble dossiers → build frontend
  → commit `data/dossiers/*` + `frontend/dossiers/*` → push) runs the **FULL offline suite green
  BEFORE pushing** — an artifact commit is **not exempt from green-main**, because tests read the
  committed artifacts (a re-assembled dossier can turn a pinned test red). Verifying the rendered
  surface is necessary but **not sufficient**; run `pytest -m "not network"` on the freshly-committed
  artifacts too.

## Tone

Terse rules, not prose. The *why* lives in STATE.md §7, docs/engineering.md, and the planning fossils.
This file is the checklist you actually follow.
