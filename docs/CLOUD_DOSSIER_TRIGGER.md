# Cloud-triggered dossier assembly — design proposal

> **STATUS: PROPOSAL — NOT BUILT. Review-only.** A written design for *future* consideration,
> captured so the reasoning survives. Nothing here is implemented. It is **deferred** (see "When to
> build this") and gated by the guardrails in CLAUDE.md / STATE.md. If this conflicts with STATE.md
> on a matter of fact, STATE.md wins.
>
> _Authored 2026-06-26. **Adversarially audited 2026-06-26** — findings folded into the body and the
> risk register (§9); the load-bearing ones (CIQ-in-`llm_call.log`, ticker injection, publish-to-main
> irreversibility, the verdict boundary) are marked **must-resolve-before-build**._

## 1. The ask

Move the dossier-assembler from the current **local-manual** flow:
> export CIQ → drop into `data/manual/ciq/<ticker>/` on the laptop → run `vinci dossier` locally
> with keys in a local `.env` → `git commit`/`push` by hand → Cloudflare redeploys → visible

to a **cloud-triggered** flow:
> upload CIQ to a private store → click "Assemble" in the dossier section → it runs off the laptop,
> commits the dossier, and it appears on the dashboard.

## 2. Current state (ground truth, with file refs)

Two deliberately separate planes:

- **Backend (`vinci/`, Python).** Ingestion (Polygon EOD + EDGAR) → universe/screen/rank →
  dossier-assembler (CIQ + EDGAR + Anthropic) → ledger/scoring. Secrets via `os.environ` /
  `require_env()` (`config.py:136`), fail-loud. Local SQLite working DB (`data/vinci.db`,
  rebuildable from snapshots, never committed). `rebuild_from_snapshots` reconstructs it
  (`store/store.py:375`, called inside `run-weekly`/`run-monthly` via `orchestrator.py:42,72`).
- **Frontend (Cloudflare Pages, static).** Read-only viewer over *committed* snapshots/dossiers, now
  behind HTTP Basic Auth (`functions/_middleware.js`). Renders; never runs the pipeline; `build.py`
  "runs no pipeline; it only mirrors" (`frontend/build.py:1-14`).

Dossier path today (`vinci dossier --ticker X`):
1. reads **committed snapshots** `candidate_records.jsonl` + `ranked_queue.jsonl` directly from
   `snapshots_dir` (`assemble.py:56`); `load_finalists` raises `LookupError` if the ticker isn't in
   `candidate_records.jsonl` (`assemble.py:72`);
2. opens the local `vinci.db` for cached screen-time values (`assemble.py:116`);
3. reads CIQ from `data/manual/ciq/<ticker>/` via `LocalFolderStore` (`manual_store.py:35`,
   git-ignored, licensed);
4. pulls EDGAR (free) + calls Anthropic for synthesis;
5. writes `data/dossiers/<ticker>/{dossier.json,.md,llm_call.log}` **to local disk only**
   (`assemble.py:92`). **No auto-commit anywhere in `vinci/`.**

> **REQUIRED COMMITTED INPUTS (audit #1):** the assembler reads `candidate_records.jsonl` and
> `ranked_queue.jsonl` from `data/snapshots/` **as files**, NOT from the rebuilt DB. They are committed
> by the weekly workflow (`git add data/snapshots`) but are intentionally **not** mirrored to the
> frontend (`build.py:39-42`). A cloud runner therefore needs BOTH (a) these committed snapshot files
> AND (b) an explicit `rebuild_from_snapshots` for the DB reads at `assemble.py:116`. Neither alone is
> sufficient.

Visibility today = a **manual** `git add data/dossiers && commit && push` → Cloudflare auto-deploys →
`build.py` mirrors `data/dossiers/<ticker>/dossier.json` into `frontend/dossiers/<TICKER>.json`
(**uppercased**, `build.py:77`) + `index.json` → the viewer fetches it. **The git push is the trigger.**

Already cloud-automated (reuse this pattern): `weekly-screen.yml` + `monthly-score.yml` run on
**GitHub Actions `workflow_dispatch`** — operator-triggered, no cron (ruling 2026-08-24) —
with **GitHub Actions secrets** and auto-commit+push. The dossier-assembler is
the *only* piece still local-only.

## 3. The constraint that shapes the design

**Cloudflare Pages cannot run the Python backend.** It is a static host + small **JS** edge Functions
(like the auth gate). It cannot run Python / `xlrd` / LibreOffice / the SQLite pipeline / multi-minute
Polygon-EDGAR-Anthropic calls. Therefore:
- "Trigger from the dossier section" means a button calls **other compute** that runs the Python.
- `POLYGON_API_KEY` / `ANTHROPIC_API_KEY` live **where the Python runs** (GitHub Actions secrets or a
  container's secret store) — **never Cloudflare**. Cloudflare holds only `BASIC_AUTH_*` (the gate)
  plus, in this design, the single workflow-dispatch token (§6).

## 4. Target architecture (recommended)

```
authed user
   │  clicks "Assemble <TICKER>" (dossier section)
   ▼
Cloudflare Pages Function  (server-side; behind the Basic Auth gate; holds the dispatch token;
   │                        HARD-CODES workflow = dossier.yml; validates ticker)
   │  POST /repos/techmuns/mosaic-theory/actions/workflows/dossier.yml/dispatches { ref, inputs:{ticker} }
   ▼
GitHub Actions  ── dossier.yml (workflow_dispatch) ──────────────────────────────
   checkout (has committed candidate_records/ranked_queue) → install deps (+ LibreOffice/xlrd) →
   EXPLICIT rebuild_from_snapshots (fail-loud if rows==0) → re-validate ticker →
   pull CIQ for <ticker> from the private store into an ephemeral temp dir (NOT the repo tree) →
   `vinci dossier --ticker <ticker>` →
   commit ONLY data/dossiers/<ticker>/{dossier.json,.md} (default: to a branch + PR) → push
   ▼
human glance / merge  →  Cloudflare auto-deploys on push to main  →  build.py mirrors  →  visible
```

Why this shape: it reuses the **existing** Actions+commit pattern, keeps pipeline secrets in GitHub,
keeps the dispatch token server-side, and leaves the frontend a *dispatcher* — it triggers, it never
runs Python. The branch+PR default (vs straight-to-main) is deliberate — see audit #8 / R3.

## 5. Components & changes

### 5a. CIQ source: `LocalFolderStore` → `DriveStore`
The swap point already exists: `DriveStore` is a deferred stub (`manual_store.py:63`,
`NotImplementedError`). Implement `available()/files()/location()` against the chosen private store:
- **Cloudflare R2 / S3 (recommended).** You already run Cloudflare; an S3-compatible bucket with a
  **scoped, short-lived API token** is both simpler to wire AND a safer credential model than Drive.
- **Google Drive.** Matches "drive folder", but a service-account JSON key is long-lived and broadly
  forgeable if it leaks from a runner (audit #10) — prefer R2 unless Drive is a hard requirement.
Constraints: the store is private + access-controlled; CIQ is pulled **transiently into an ephemeral
temp dir on the runner, never the repo working tree** (so `git add` globbing can't sweep it); only the
DERIVED `dossier.json` is ever committed. Store choice is one config knob.

### 5b. `dossier.yml` GitHub Actions workflow (new)
`workflow_dispatch` with a required `ticker` input (+ optional `top`). Steps:
1. `actions/checkout` (brings the committed `candidate_records.jsonl` / `ranked_queue.jsonl`) +
   `setup-python`.
2. `pip install -e .` **and install LibreOffice/`xlrd`** (else transcripts = `UNAVAILABLE`, fail-loud
   — acceptable, but decide).
3. **Explicit DB rebuild** — `vinci dossier` does NOT rebuild today (audit #3), so invoke
   `rebuild_from_snapshots` directly (a small `python -c`, or add a `vinci rebuild` CLI), and
   **fail loud if it populated 0 rows**.
4. **Re-validate the `ticker` input inside the workflow** (audit #5) and bind it to an `env:` var —
   never interpolate `${{ inputs.ticker }}` inline in a shell `run:` line (command-injection sink).
5. Pull CIQ for `<ticker>` from the private store into a temp dir; point the assembler's store root at
   it.
6. `python -m vinci dossier --ticker "$TICKER"`.
7. Commit **only** `data/dossiers/<ticker>/{dossier.json,.md}` via an **explicit add-list** — never
   `data/manual/ciq`, never `llm_call.log`. Default target: a branch + PR (R3). Mirror the existing
   workflows' `git diff --staged --quiet || commit` idempotence. Before pushing, `git pull --rebase`
   to avoid racing the operator-triggered commit jobs (audit #7).

### 5c. Pages Function dispatcher (new `functions/api/assemble.js`)
Server-side handler. It inherits Basic Auth automatically — `_middleware.js:26` `onRequest` gates
**every** path including `/api/*` (audit #9, confirmed). It:
- reads a dispatch token from a Pages secret;
- **HARD-CODES the workflow filename** (`dossier.yml`) — never accepts a workflow name as input
  (audit #13 — keeps "assembly-only" a structural constraint, not a convention);
- **validates the ticker** with an anchored, letter-leading pattern `^[A-Z][A-Z.\-]{0,7}$` (audit #5
  — rejects `........` and over-long input);
- POSTs the `workflow_dispatch`; returns a job handle. **The token never reaches the browser.**

### 5d. Frontend dossier-section button + status
A single "Assemble" action calling the Function, then "assembling… appears after the next deploy
(~1–2 min)". Because the dossier appears only after build+deploy, poll for
`dossiers/<TICKER>.json` (**uppercase** the ticker — `build.py:77` uppercases on mirror, audit #11) /
`dossiers/index.json`, or surface the Actions run status. **No pipeline logic in the browser.**

## 6. Secrets & access model (where each secret lives)

| Secret | Lives in | Used by |
|---|---|---|
| `POLYGON_API_KEY`, `ANTHROPIC_API_KEY`, `SEC_USER_AGENT` | **GitHub Actions secrets** | the runner (pipeline) |
| R2/Drive credential (prefer a **scoped R2 token**, not a long-lived Drive JSON key) | **GitHub Actions secret** | the runner (pull CIQ) |
| GitHub `workflow_dispatch` token | **Cloudflare Pages secret** (read by the Function) | the dispatcher |
| `BASIC_AUTH_USER` / `BASIC_AUTH_PASS` | **Cloudflare Pages secret** | the auth gate (unchanged) |

Pipeline keys do **not** go to Cloudflare. **Token-scope reality (audit #6):** `workflow_dispatch`
cannot be granted by a bare `actions:write` — a fine-grained PAT needs **Actions: read+write AND
Contents: read**; a classic PAT needs full `repo`. Prefer a **short-lived GitHub App installation
token** over a long-lived PAT. **Blast radius:** a Pages Function secret is readable by ANY code
deployed to the project, and the project auto-builds from `main` on every push — so anyone who can
**merge to `main`** can add a Function that logs `env` and exfiltrate the token. The token's blast
radius is "anyone with merge rights," not merely "behind the auth gate." Scope it minimally and rotate.

## 7. Guardrails this honors (non-negotiable)

- **Verdict logging + the ledger stay CLI-only, forever — and structurally, not just by convention.**
  This proposal triggers *assembly* (assembles, never concludes). The Function dispatches ONLY
  `dossier.yml` (hard-coded), and a lint/test should assert no `functions/api/*` handler references
  `ledger`/`scoring`/`log-verdict` (audit #13). The dossier button is the one deliberate action added
  to an otherwise read-only surface — "the friction is the safeguard for the spread" (CLAUDE.md).
- **Raw CIQ is never committed — and never leaks via the LLM log (audit #4, BLOCKER).** CIQ moves from
  a local folder to a private R2/Drive; it is pulled into an ephemeral temp dir and never enters git.
  **`llm_call.log` embeds raw CIQ in the prompt** (`assemble.py:94` writes it; the prompt carries the
  CIQ-derived transcript/financials, `assemble.py:125-128`). It is git-ignored (`.gitignore:32`) AND
  must **never be uploaded as a workflow artifact, never echoed to the Actions log, never printed.**
  This is the single most likely CIQ leak in the cloud flow.
- **Secrets never in code/git.** All keys in Actions/Cloudflare secret stores; fail-loud if absent.
- **Fail-loud, never fabricate.** Missing CIQ → `MISSING` + "pull CIQ" flag (existing); a failed pull,
  empty DB rebuild, or missing key → the run fails loud, no partial dossier.

## 8. Publishing model — branch+PR is the DEFAULT, not an option (audit #8)

STATE.md §4 BLOCKER A is explicit: once licensed-adjacent data is served from a reachable URL it can't
be retracted. An auto-commit to `main` is mirrored by `build.py` and served (behind auth) within ~1–2
min with **no human glance**. The assembler's self-flags catch *synthesis-quality* issues
(uncited/untraceable/no-conclusion), **not** a licensing/extraction mistake that lands a verbatim CIQ
figure in a committed field. Therefore the default publish path is **commit to a branch → PR → human
glance → merge** (or, at minimum, a quarantine dir that `build.py` does NOT mirror until promoted).
Straight-to-`main` is an explicit opt-in only once the flow is trusted.

## 9. Risk register (post-audit)

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | UI action path erodes the read-only/verdict-CLI line | HIGH | Function dispatches ONLY `dossier.yml` (hard-coded); lint asserts no ledger/scoring ref in `functions/api/*`; no verdict API ever (§7) |
| R2 | Ticker → command injection in the workflow | HIGH | Validate at BOTH Function and workflow; anchored `^[A-Z][A-Z.\-]{0,7}$`; pass via `env:`, never inline `${{ }}` in `run:` (§5b/§5c) |
| R3 | Auto-publish to `main` serves an unreviewed dossier (irreversible) | HIGH | Branch+PR is the DEFAULT publish path (§8) |
| R4 | `llm_call.log` / temp CIQ leak from the runner | BLOCKER | Never commit/artifact/print the log; CIQ temp dir ephemeral + outside the repo tree (§7) |
| R5 | Dispatch-token blast radius = anyone who can merge to `main` | HIGH | GitHub App short-lived token, minimal scope, rotated; the merge-rights coupling is documented (§6) |
| R6 | Fresh-runner DB empty → silent field degradation | MEDIUM | Workflow MUST `rebuild_from_snapshots` explicitly + fail loud on 0 rows (§5b) |
| R7 | Concurrency: shared `vinci-scheduled` group (`cancel-in-progress:false`) DROPS queued clicks | MEDIUM | Use a SEPARATE per-ticker group `dossier-${{ inputs.ticker }}`; `git pull --rebase` before push to serialize only the commit (audit #7) |
| R8 | Credential longevity (Drive JSON) | MEDIUM | Prefer R2 scoped token over a long-lived service-account key (§5a/§6) |
| R9 | Deploy lag confuses the user | LOW | Button states the lag + polls the uppercased file / run status (§5d) |
| R10 | Cost/latency per click (runner + LibreOffice + Anthropic) | LOW | Fine at ~10/week; no auto-retry storms |

## 10. Phased rollout (each phase shippable + reversible)

1. **Phase 0 — `dossier.yml` with manual `workflow_dispatch` (GitHub UI).** Proves cloud assembly +
   commit, *no frontend change, no new token, no UI write-path*. Biggest laptop-freedom win, lowest
   risk. **Note (audit #14):** "lowest risk" is true for *UI surface* — Phase 0 still puts raw CIQ +
   `llm_call.log` on the runner, so the §7/R4 licensing guards apply from Phase 0, not just Phase 2.
2. **Phase 1 — `DriveStore`/R2 store.** Move CIQ off the laptop into the private store; the workflow
   pulls it. Config-gated; the `manual_store.py:63` swap point.
3. **Phase 2 — Pages Function dispatcher + the dossier-section button.** Only after Phases 0–1 are
   solid; this is the step that adds the UI action path (R1/R2/R5).

Stop after any phase — each is independently useful; Phase 0 alone removes the laptop dependency for
assembly.

## 11. Open decisions for the operator

- R2/S3 vs Google Drive for CIQ (R2 = simpler wiring + safer credential).
- Branch+PR (default, §8) vs straight-to-`main` (opt-in once trusted).
- Install LibreOffice in the workflow (transcripts) vs accept `UNAVAILABLE`.
- GitHub App token vs PAT for the dispatcher.
- Whether to also expose screen/ingestion via the same dispatcher (probably not — they
  already have their own `workflow_dispatch` entries).

## 12. What this explicitly does NOT change

The screen/rank/ledger/scoring decision path; the BUY−AVOID spread; the no-conclusion guarantee of the
dossier; and — the hard line — **logging a verdict stays a manual, CLI-only, human act** (enforced
structurally, §7, not merely promised).

## 13. When to build this

Deferred. Build it when the **manual local loop's friction actually bites** — you are assembling enough
finalists per week that the laptop-bound, hand-committed step is the real bottleneck (STATE.md §4:
"Drive adapter … trigger: the local-folder assembler is proven and the manual export→folder step is
the real friction. A convenience, not a milestone"). Until then the local flow is correct and cheaper.
The binding constraint on the fund remains **resolved BUY−AVOID verdicts**, not assembly ergonomics.
