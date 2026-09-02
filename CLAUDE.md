# CLAUDE.md — working instructions for the mosaic-theory repo

> This file is HOW to work in this repo. STATE.md is WHAT is true right now; `docs/records/`
> is HOW IT GOT THAT WAY (one immutable file per entry). `AGENTS.md` points other tools here.
> docs/engineering.md is the fuller engineering handbook (conventions, practices, workflow).
> **The operating loops (monthly sweep, group-review recording, survivor checks, theme-advance,
> verification, sacred files, UI rule, calendar) live in docs/RUNBOOKS.md — follow them before
> improvising.**
> Non-negotiable behavior and the fund guardrails live HERE; project state lives in STATE.md;
> detailed practice lives in engineering.md. Never duplicate state into this file — they drift.
> If this file conflicts with STATE.md on a matter of fact, STATE.md wins; this file governs behavior.

## The one thing this fund is

An AI-native, long-biased, US-first concentrated equity fund. The edge is **deep human judgment on
a few finalists, fed by an AI funnel that achieves breadth and cross-sectional reasoning a human
can't.** Everything you build serves that division of labor:
- **AI does** breadth, parallel assembly, and reasoning across the whole universe/graph.
- **The machine PROPOSES; the human decides** *(2026-07-13 pivot)* — the Brief leads with a
  machine-proposed verdict derived DETERMINISTICALLY from its committed evidence lean
  (`vinci/dossier/verdict.py`: a face-validity-frozen 3-row mapping; `mixed` proposes nothing).
  The **human's confirm/override is the verdict of record**; the ledger seals the proposal +
  disposition beside it, so the spread decomposes into the machine baseline vs the human delta.
- The edge is the discriminator's hit-rate, measured by the **BUY−AVOID forward-return spread** —
  accumulated forward over calendar time (human-final = PRIMARY; the machine-proposal curve and
  the override subset accumulate beside it). That number is the only thing that proves the fund
  works.

The line that must not blur (re-pointed by the pivot): **the LLM never free-writes a verdict**
(the proposal is plain-code derivation of the lean; `Synthesis` has no verdict field — test-pinned),
**the proposal mapping is never outcome-tuned**, and **no code path approaches execution**. If a
change crosses any of these — STOP and flag it. ACCEPTED RISK (recorded in STATE.md with its
falsifier): a machine proposal ANCHORS the human — if the override rate collapses toward ~0 or the
human spread tracks the machine spread within noise, the anchoring concern is confirmed → revisit
verdict placement.

## Session ritual (every time)

1. **Read STATE.md first** — the authoritative record of built / falsified / deferred / next.
   **§5.0 OPEN NOW is that answer** — read it, and RE-read it before proposing next steps, however
   long the session has run. §5 below it is a ~9,900-line append-only archive: it is history, not a
   to-do list, and it CONTRADICTS itself where closed items were never struck. *Never answer "what
   is next" from conversation memory — on 2026-08-25 an agent verified the weekly run green that
   morning, recorded it DONE itself, and proposed re-triggering it that afternoon while a stale
   entry below still read "STILL OPEN".* State established earlier in a session decays; the file
   does not. The full history now lives in **`docs/records/`** — one immutable file per entry,
   opened on demand rather than read up front (`ls`/`grep`/`git log` are the index; there is no
   curated one, which would rot).
2. End every build by **writing a RECORD and updating the SNAPSHOT** — two files, two jobs.
   **§5 IS FROZEN to new entries (2026-08-25, P0).** A build's narrative — what happened, why, how
   verified, what it cost — goes in a NEW file under **`docs/records/`** (see its README; copy
   `TEMPLATE.md`). STATE.md then gets only what changed about *current truth*: a §5.0 OPEN NOW row
   if something opened, its removal if something closed, and at most a ≤3-line claim pointing at
   the record. **CLOSING an item means DELETING its §5.0 row AND striking its entry below.**
   A build that changes reality without doing both leaves the record lying.
   *Why frozen: §5 reached 9,876 lines / 804 bold headers, 51 with a done-marker — appended like a
   journal, trusted like a snapshot, and it came to answer one question two ways. A record's body
   is immutable, so a reversal adds a file and flips a status instead of rewriting a claim.*
3. Keep STATE.md accuracy-first: falsified is falsified, unproven is unproven. Never upgrade a hedged
   claim to a confident one to make progress look better.
4. **A REBASE SILENTLY EATS STATE ENTRIES — re-check after every one.** Run
   `git diff origin/main -- STATE.md`: it must be NON-EMPTY for a build that changed reality, and
   STATE.md must appear in the PR's own file list before you merge. Every build appends near the
   same region, so a rebase onto a moved `main` conflicts there almost every time, and resolving
   toward the incoming side drops the local addition leaving no marker that survives to review.
   Twice already: **#443 MERGED with no STATE entry at all**, and #447 nearly did.
   `tests/test_state_identifiers.py` DOES read STATE.md — but it lints identifier uniqueness and
   reference resolution, and **a dropped entry leaves a smaller file that is still internally
   consistent, so it passes.** Completeness is not lintable (nothing knows which builds owed an
   entry), so this is a step here rather than a guard.

## Non-negotiable behavior (every build)

- **Fail loud, never fabricate.** Missing data is `UNKNOWN`/raise — never a guessed number, never a
  silent imputation. A fabricated value corrupts the judgment it feeds; a loud failure is cheap.
- **Hold scope.** Make only the change asked. No refactoring adjacent code, no "clean up while I'm
  here." Find something else wrong → report it, don't fix it silently. Scope creep is how a
  verified-green module acquires a new bug.
- **CORPUS BEFORE SYNTHETIC.** Run every new check against the LIVE COMMITTED CORPUS before
  believing it — a check that finds nothing there is SUSPECT until you have shown it can find
  something. A mutation drawn from the guard's own pattern list tests the list, not the guard
  (#302's hygiene guard passed its mutation while running green over six live violations), and
  a fixture hand-rolled to the shape the test needs will dictate the production signature
  (#305). Fixtures are built from the REAL type. *(D22 — the suite is unverified evidence;
  production is mutation-tested and the suite is not.)*
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
- **Never assert a capability is ABSENT off one search.** Before any "X doesn't exist / isn't
  handled" claim: search ≥2 vocabularies (house term AND plain words — glossary:
  docs/engineering.md §House vocabulary), run `git log --all -i --grep=<concept>` AND `git log
  -S<term>` (pickaxe searches diff content, vocabulary-independent), and READ the definition of
  every symbol the search surfaces near the topic — a call site's name is a claim, not proof.
  Still not found → report "not found under <searches tried>", NEVER "doesn't exist".
  **When probing a PRIOR RUN, read its PARAMETERS FIRST — window, forms, reference date.** A probe at
  different parameters measures a different question, and the mismatch reads exactly like a defect in
  the thing probed. (AES/ETN were escalated as "silent recall loss" off a 400-day probe of a scan run
  at 290 days; at the scan's own window they match nothing, and the absence was correct behaviour.)
  **And TEST AN ANOMALY BEFORE IT EARNS A RECORD ENTRY** — that one reached an escalation, a STATE.md
  row, a record and a commit message before it was re-probed at the right window. Flagging rather
  than asserting is necessary and was done; it is not sufficient. (Two real
  incidents: the ranker's screen-time cap and the D3 bull/bear ordering were both denied while
  existing — generic-vocabulary greps missed the house terms.)
- **Coin a term → translate it once, at coin-time.** A PR that introduces a house term (the next
  D3 / twin / assay) states its plain-English equivalent where it is coined — in the squash title
  or body ("D3 — deterministic ORDERING of bull/bear points") — and appends ONE line to the
  glossary (docs/engineering.md §House vocabulary). The coiner is the only scalable translator;
  git log then answers existence questions in either vocabulary forever. No other capability
  index is maintained — derive from git/code, never dual-write (a curated index rots and its
  gaps re-create the false "not listed → doesn't exist" inference).
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
- **The machine assembles, cites, and PROPOSES — it never free-concludes** *(2026-07-13 pivot)*.
  The proposal is a deterministic, face-validity-frozen derivation of the synthesis's committed
  lean — never an LLM-written verdict (an LLM verdict on a single high-stakes name is confident,
  fluent noise; `Synthesis` still has no verdict field). `mixed` proposes NOTHING — a two-sided
  read is the human's call, never a coin-flip. The human logs the verdict of record by hand
  (confirm/override); the ledger seals the proposal + disposition beside it.
- **A GRADE IS ECONOMIC SUBSTANCE; DISCLOSURE FORM IS A SEPARATE FIELD.** `ExposureConcreteness` /
  `ExposureBasis` record what KIND of evidence a filing offers — a $32,549 binding contract and a
  $60.7bn one are the SAME basis by design. **Nothing may rank economic capture from them alone**;
  substance needs MAGNITUDE + KIND, neither of which is a structured field today. **Before any new
  gate ships, answer in writing: DOES THIS SELECT ON FORM?** Four surfaces have already failed that
  question — `machine_grade` graded form and was read as size; the `ai-compute-platform` prefilter
  used OBSERVER vocabulary and so excluded the observed (GOOGL was missing from a scan of the
  compute layer); the disclosure-asymmetry concession read a disclosure asymmetry as an economic
  one; and a $100m materiality gate selected on CURRENCY of disclosure, admitting a bond issuance
  and an intercompany loan while excluding the two largest contracted-capacity names. Same error,
  four surfaces — which is why the rule is here and not in one more gate.
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
     amendment chains, per-item revision detail): a collapsed `<details>` on web, **PRINT-EXPANDED**
     *(operator decision 2026-07-21 — previously excluded from print)*: every `<details>` force-opens
     in the PDF regardless of on-screen state, its summary printing as the section header, so the
     export is the COMPLETE record. The web surface stays collapsed — only the print fate flipped.
     **ONE EXCEPTION — BULK AUDIT TIERS (`details.ds-bulk`), 2026-07-29 (PR #269):** a tier whose
     expansion is a BULK LOG rather than provenance for a rendered claim prints as a POINTER, not in
     full — the 250-event revision log ran to three pages mid-report. The carve-out is by explicit
     CLASS, never by a size heuristic, and the pointer must name where the full record lives
     (`dossier.json` + the web). Provenance — quotes, accessions, agreement terms, amendment chains
     — is NOT bulk and still prints in full. Adding a `ds-bulk` is a decision to make the PDF
     incomplete for that block: take it deliberately, and record it here.
  3. **JSON** — machine-complete, the full record behind every curated value.
  The **Financial-Summary appendix is decision data → it STAYS in print** (it is not provenance).
  Curating never deletes a fact — a moved fact is reachable in the expanded web on-demand tier, the
  printed PDF, or the JSON. (Discipline/methodology language lives in `source_ref`s + JSON.)
- **Exhibits cite via ENDNOTES, never an inline caption.** An SVG exhibit's provenance is a `citeMark` →
  the tier's Sources list (where every other cite resolves) — NEVER an inline `Source: …` caption under the
  chart. The exhibit visualizes data already cited by its sibling table/fact (financial_summary /
  range_position / trajectory), so a caption just duplicates the source in the wrong place. (Recurred on
  three exhibits; guarded by a `>Source:`-scan test.)

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
  **PER ASSERTION, not per test:** the no-LLM-string-pin rule binds each INDIVIDUAL assertion — one
  test may mix deterministic pins with a brittle one (test_t2 pinned the interest rate deterministically
  yet reddened on its conversion sub-assertion), so a class sweep must scan ASSERTIONS, never test names.
  **Never pin an LLM-COMPOSED string** (synthesis text, an LLM-extracted covenant/twin composite):
  it reworders on every re-assembly, so an exact-string pin is guaranteed to rot the committed
  artifact. LLM-adjacent tests assert **deterministic ANCHORS** (the components present,
  order/phrasing-free — "components-present-together IS the composite-or-absent rule"), **structure**,
  and **guard behavior**. **A classifier / derivation / formatter result on LLM text is an LLM-string
  pin IN DISGUISE** — `_point_tier(claim)==1`, `_derive_conversion(clause)=="…"`, `fmt(x)=="…"` red on
  a reword exactly like a literal `in`; the sweep criterion is *does the assertion's truth depend on
  LLM-composed text through ANY function* (classifier/deriver/formatter), not just literal tokens.
  **An e2e test on a LIVING committed artifact asserts PHRASING-INDEPENDENT INVARIANTS only** (presence
  + citation, monotonic/structural ordering, guard behavior); a VALUE-level pin (a specific tier, a
  specific $/sh, an exact composite) lives on a FROZEN fixture, never on the re-drawn artifact.
  *Facts are stable; framing is weather — and weather applies to CI.*
- **INVARIANT RULE.** Every incident closes by shipping a machine check (lint / guard / coherence
  test), or is recorded in STATE.md as consciously accepted risk. STATE.md keeps the table:
  incident → invariant → shipped Y/N.
- **PREVIEW RULE.** Render/layout PRs run a Phase-1 preview from committed JSON and **STOP for
  approval**; data/extractor PRs go straight to build with real-run verification.
  **EXTENDED 2026-07-21 — a card preview MUST include the EXPANDED / print-tier state, not just the
  visible one.** Since the T1 amendment every `<details>` force-opens in the PDF, so the audit tier
  is ALWAYS in the export even while collapsed on screen. Cause of the extension: #176's synthetic
  R2 preview checked the visible tier, passed, and shipped a renderer that printed `undefined`
  three times inside the collapsed reference table — in every PDF, invisible to the preview that
  approved it. Render collapsed AND force-open; capture both.
- **OPERATOR-ACTION RULE.** Operator to-dos arising from builds/audits are recorded **by the build
  itself** — chat is not a ledger. Since 2026-08-25 that means a row in **STATE.md §5.0 OPEN NOW**
  (owner + what unlocks it) and, where the item has reasoning worth keeping, a file under
  **`docs/records/`**. Never appended to §5, which is frozen.
- **ARTIFACT-PASS RULE.** The standing post-merge artifact pass (re-assemble dossiers → build frontend
  → commit `data/dossiers/*` + `frontend/dossiers/*` → push) runs the **FULL offline suite green
  BEFORE pushing** — an artifact commit is **not exempt from green-main**, because tests read the
  committed artifacts (a re-assembled dossier can turn a pinned test red). Verifying the rendered
  surface is necessary but **not sufficient**; run `pytest -m "not network"` on the freshly-committed
  artifacts too.

## Tone

Terse rules, not prose. The *why* lives in STATE.md §7, docs/engineering.md, and the planning fossils.
This file is the checklist you actually follow.
