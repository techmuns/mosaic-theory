# Engineering practices — mosaic-theory

> The fuller "how we build" handbook. **CLAUDE.md** holds the non-negotiable, every-build behavior and
> the fund guardrails; **STATE.md** holds project state; this file holds engineering conventions,
> practice, and the code workflow. This is deliberately SMALL — a 2-person paper-mode team doesn't need
> a full standards manual, and writing one for contributors who don't exist is premature. It captures
> only what is load-bearing today, and is the designated home for standards to grow into as the team
> and blast radius grow.

## Principles that protect the fund (load-bearing now)

The BUY−AVOID spread's integrity depends on these. They are real today.

### Reproducibility — the spread must be reconstructable
- Same inputs → same outputs. A run's result must be reproducible from committed state (JSONL
  snapshots) + the code at that commit.
- LLM calls (the ranker's Tier-3 cause-classifier, the dossier-assembler) are NON-DETERMINISTIC.
  Therefore: pin what you can (low/0 temperature where a stable label is wanted); **log the model
  identifier and the raw LLM output** alongside any artifact derived from it; and never let an LLM
  output silently become a NUMBER that feeds the spread. LLM output may annotate or classify; the
  numeric inputs to the spread come from deterministic computation on real data.
- Anything stochastic gets a seed where the library allows; record the seed.

### As-of discipline — never use data that didn't exist at the decision time
- Every datum carries (or resolves to) its as-of date. No value is used at a decision point if it
  postdates that point. The `close_as_of` entry-price freeze (clamped to `bar_date ≤ reference_date`,
  fail-loud) is the canonical instance; the rule is general — apply it anywhere data meets a decision.
- This is the lookahead guard, generalized. Backfilling future data into the store is allowed for
  storage but must never leak into a decision via an unclamped read.

### Re-run safety / idempotency — the pipeline will be re-run
- The weekly screen and monthly score will be re-run, interrupted, partially-failed, and resumed.
  Running a step twice must not corrupt or double-count state.
- The append-only ledger (INSERT-only, overwrite rejected at the DB layer) is one piece. The property
  is broader: prefer idempotent writes; make resumption safe; don't assume a step runs exactly once.

### Testing
- **Regression test for every bug fix** — and it must demonstrate the previously-broken case, not just
  pass. (Template: the lookahead guard test constructs a future-dated bar and asserts the freeze ignores
  it.)
- New modules carry tests for their fail-loud paths (UNKNOWN/raise on missing data), not just happy path.
- `pytest -m "not network"` is the offline gate; network-dependent tests are marked and excluded there.

## Code workflow (current — calibrated for a 2-person paper-mode team)

The invariant that prevents spiral, regardless of process: **main is always runnable** — anyone can pull
main and run the weekly loop. Everything below serves that, kept as light as the current blast radius
(2 people, paper, no live capital, no external users) justifies.

Every change, regardless of size:
1. **Work on a local branch**, not directly on main. Costs nothing; lets you abandon a half-done change
   cleanly.
2. **Green before it lands:** full offline suite (`pytest -m "not network"`) + ruff + `mypy --strict`.
3. **Bug fix → regression test** that would have caught it (and demonstrates the previously-broken case).
4. **Decision-path changes get a real shown run.** Anything touching how a candidate is screened, ranked,
   logged, priced, or scored (screen / ranker / ledger / scoring / freeze) gets run on real data and
   eyeballed before landing — NOT just green tests. Tests catch what you thought to test; the manual run
   catches what you didn't. (The lookahead bug passed every test and was still wrong — this step is why.)
   Non-decision-path changes (docs, comments, behavior-preserving refactors) skip this.
5. **Merge to main and push.** Focused, single-purpose commit; honest message.

Deliberately SKIPPED now (premature at 2 people — see deferred triggers): formal PR review (can't
meaningfully self-review; becomes rubber-stamping), protected-branch CI merge gates, long-lived feature
branches with verification environments.

## Conventions (light — expand as needed)

- **Quality gate:** ruff + `mypy --strict` clean before commit.
- **Persistence:** SQLite store; committed analytical state as JSONL (diff-able), never binary `.db`.
- **Secrets / data boundary:** see CLAUDE.md (Security). Not duplicated here.
- **Commits:** focused, single-purpose, honest messages; push to origin when done.

## House vocabulary (glossary — plain words first)

Idiosyncratic terms, one line each: *term → plain meaning → home*. This is a TRANSLATION table,
not a capability index — capabilities are discovered from git log + code (CLAUDE.md's
existence-check rule); this only bridges vocabulary. Coined a new term? Add its line in the same
PR (CLAUDE.md: coin-time translation).

- **D1/D2/D3** — dossier-restructure build tags; **D3 = deterministic render-side ORDERING of
  bull/bear points** — `render.py` `_ordered_points`; never an LLM/schema field. HYBRID since
  2026-07-24: the bull case leads with crux-linked mechanism points (balance sheet demoted to the
  enabler slot); the bear case stays survival-first (a T1 fact is never demoted below a narrative
  point); mechanism-bearing refs break ties.
- **twin (renderers)** — the py↔md and js↔web render PAIR that must not drift
  (`vinci/dossier/render.py` ↔ `frontend/views/shared/dossier.js`); "twin pins" = tests on both.
- **twin (reference cases)** — UNRELATED same word: synthesis's named analogue companies
  (`twin_reference_cases`, `synthesis.py`).
- **anchor (R1 block)** — the persisted spot-independent screening anchor (mid-cycle margin ×
  own-history multiple) — `vinci/dossier/anchor.py`. In BRIEFS, "anchored" = deterministic
  regex/heading extraction (CLAUDE.md §BRIEF CONTRACT, VOCABULARY).
- **R1 / R2** — the two underwrite recipes: `R1_midcycle_margin_evebitda` (mean-revert margin ×
  own-history EV/EBITDA) and `R2_terminal_margin` (terminal-margin bridge when R1 can't anchor) —
  `vinci/scenarios.py`, `vinci/dossier/terminal_margin.py`.
- **BAR / HURDLE** — operator-ratified fund-wide constants: BAR = the 2:1 reward/risk bar
  (`midcycle.py`); HURDLE = the 15% PV discount rate (`terminal_margin.py`).
- **band / own-history** — a name's OWN trailing multiple range (low–median–high + percentile);
  `band_guards.py` disqualifies unusable bands.
- **seal** — append-only integrity on recorded rationale: sha-digest manifest
  (`scenarios/_seal.json`); text grows only by dated `[amended …]` tags — `vinci/seal.py`.
  "Seal-once / k=1" = the machine proposal is derived once from the committed dossier and sealed.
- **lean / evidence_balance** — synthesis's one-line strongly-bearish|mixed|strongly-bullish read;
  the machine PROPOSAL derives deterministically from it (`vinci/dossier/verdict.py`), hidden
  until the human's verdict of record is logged.
- **mech / mechanical** — the deterministic assembled-facts layer of a dossier
  (`vinci/dossier/mechanical.py`); **synthesis** = the LLM framing layer (no verdict field).
- **what-broke / gap card / event ledger** — the drawdown anatomy: per-gap-down 8-K cards, the
  annotated daily chart, the per-gap list ("What broke — and did it fall alone?", both renderers).
- **idio / idio strip** — idiosyncratic-vs-shared decomposition (name vs benchmark/cohort) in the
  what-broke section.
- **one-off / recon** — EX-99.1 release-parse extractions: one-off charges (`OneOffItem`) and
  non-GAAP reconciliation actuals (`ReconciliationValue`) — `vinci/edgar/release_parse.py`.
- **drivers / operating drivers** — extracted operating mechanisms (volume/pricing/capacity/mix,
  dated events) feeding synthesis rule 12 — `vinci/dossier/driver_extract.py`.
- **three tiers** — the human surface: main body (decision values) / on-demand `<details>`
  (print-EXPANDED audit tier) / machine-complete JSON — CLAUDE.md three-tier rule.
- **uw-card / tear sheet** — the underwrite scenario card rendered from `scenarios/<T>.json` —
  `frontend/views/shared/uw-card.js`.
- **ledger / spread** — the append-only paper-verdict ledger; the **BUY−AVOID forward-return
  spread** is THE fund metric. **close row** = the ledger's position-closed row (with a stated
  reason); **watch** = a `VerdictStatus` on the underwrite record — not underwritable at today's
  price, franchise intact, no position (`scenarios.py`).
- **themes lane** (`vinci/themes/`): **theme** = a ratified thematic driver; **DriverSpec** = its
  verbatim definition; **sweep** = the monthly theme sweep; **radar** = the frontend triage inbox;
  **assay** = the evidence test of a theme (**retrocast** = assay on deeper history);
  **freeze** = the frozen theme source artifact that must reproduce byte-identical.
- **mirror** — the committed `frontend/` copy of data snapshots the static dashboard serves
  (`frontend/build.py`); an artifact pass is incomplete until source AND mirror are synced.
- **re-assemble vs re-render** — re-assemble = full pipeline re-run INCLUDING the LLM synthesis
  (facts + framing both move); re-render = deterministic md/web redraw from committed JSON (no
  LLM, framing frozen). Operationally different — always say which.
- **brief item codes** — parenthesized tags in comments/commits (`(K6)`, `(H3)`, `(RC-1 A)`,
  `(B1)`, `T1`, `C1/C2`, `PR-B`) are line items of a SPECIFIC build brief, not durable
  vocabulary — grep STATE.md for the brief that defined them.
- **governor** — the build-sequencing rule for deferred capabilities (STATE.md §4). **fossils** —
  the archived planning/decision documents ("planning fossils").
- **face-validity** — parameters set because the output looks structurally right, NEVER tuned on
  forward returns (CLAUDE.md guardrail). **assemble-not-conclude** — the machine assembles,
  cites, proposes; it never free-writes a verdict.

## Local setup (every laptop, every contributor)

Secrets live in the environment (CLAUDE.md), loaded the SAME way on every machine so runs are
reproducible across people and laptops (12-factor config):

1. `git clone …` && `cd mosaic-theory`
2. `python -m venv .venv && . .venv/bin/activate`
3. `pip install -e ".[dev]"` — **re-run after any `git pull` that changes dependencies.**
4. `cp .env.example .env`, then fill `POLYGON_API_KEY` / `ANTHROPIC_API_KEY` / `SEC_USER_AGENT`.
   `.env` is git-ignored and per-laptop — it never leaves the machine, never enters git.

`vinci` auto-loads the repo-root `.env` at startup (`config.load_local_env`) — no manual `source`
step. In CI no `.env` exists (git-ignored) and GitHub Actions secrets are injected instead; the same
code reads `os.environ` either way, and an injected secret is never overridden by a file. **The
committed `.env.example` is the shared contract:** when a new required key is added, add it there so
every laptop picks it up on the next `git pull`.

## Deferred — expand when the team grows / blast radius increases

Stubs, intentionally not written yet (premature for a 2-person team; documented so the gap is visible and
has a home). Each carries the trigger that should prompt adopting it:

- **Real PR review** — trigger: a SECOND person is committing code. Self-review at 2 people is rubber-
  stamping; with two committers, review catches what one person misses.
- **Protected main + CI gate** (block merge on red suite/lint; run tests in CI, not just locally) —
  trigger: live capital, OR CI is set up. Until then the gate is the human running the suite green locally.
- **Release tagging / change log** — trigger: LP-facing outputs or real-money operation, where you must
  point to "the exact version that produced this result."
- **Branching model** (beyond branch→merge) — trigger: parallel workstreams that can't land independently.
- **Dependency / environment reproducibility** (pinned versions, lockfile, reproducible runtime).
- **Module / interface conventions** (how new screens/edges/adapters are added — e.g. the swappable
  ManualDataStore interface for the dossier-assembler's local→Drive path).
- **Logging / observability standards** for the operating pipeline.
- **Onboarding doc** for a new team member.

> When you add a practice here, keep it a CONVENTION (how we build over time). If a rule is high-stakes
> and must be followed on EVERY build, it belongs in CLAUDE.md instead.
