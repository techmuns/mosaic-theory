# DEPLOY — the authed Cloudflare Pages dashboard (runbook)

> Stand up the GitHub → Cloudflare Pages auto-deploy for the read-only ops dashboard
> (`frontend/`), gated behind **HTTP Basic Auth** — a Pages Function that requires a
> username/password. **No Cloudflare Zero Trust / Access, and no payment method,
> required.** This is the §4 CONDITIONAL item in STATE.md — it serves DERIVED,
> licensed-adjacent artifacts (per-ticker `dossier.json`, snapshots, the graph), so it
> is **authed-only** and carries one **irreversible** concern (BLOCKER A). Read the whole
> file before pointing anyone at the URL.
>
> Repo-side scaffolding is in place (`wrangler.toml`, `functions/_middleware.js`,
> `frontend/build.py`). What remains is the **dashboard** setup below.

## ⚠ The gate MUST be on the PRODUCTION branch

Cloudflare Pages builds from one **production branch** (e.g. `main`). The gate
(`functions/_middleware.js` + `wrangler.toml`) only protects a deployment if it is
**present on that branch**. If the gate lives only on a feature branch, the production
deploy has **NO gate** and serves the committed licensed dossiers unauthenticated — an
incognito visit shows the dashboard instead of a login prompt. **Merge the gate to the
production branch before (or together with) connecting the project.**

## Why this is handled with extra care

`frontend/dossiers/*.json` are DERIVED from licensed CIQ workbooks (extracted
`{value, source_ref}` facts + LLM synthesis + verbatim PUBLIC 10-K phrases — never
reproduced licensed CIQ). They are committed to this **private** repo for the authed
deploy (CLAUDE.md). **Once a reachable URL serves them unauthenticated, that cannot be
retracted.** So the origin is built to **fail closed**, and you confirm the gate works
(BLOCKER A) before sharing the URL.

## The two BLOCKERS

- **BLOCKER A — prove the deployed URL rejects an unauthenticated request.** From a fresh
  incognito window and via `curl --silent -o /dev/null -w "%{http_code}"`, fetch the
  production URL, a preview URL, **and** a direct data path (`/dossiers/VRRM.json`,
  `/snapshots/ranked_queue.jsonl`). Each must return **`401`** (the Basic Auth challenge),
  **never** `200`-with-content. This is the irreversible gate.
- **BLOCKER B — `data/graph_coverage.json` is CIQ-free. ✅ VERIFIED 2026-06-26.** All 339
  edges are EDGAR-10-K relationship data (customer/supplier/manufacturer/distributor/
  vendor) with verbatim 10-K `evidence`; the only financial words appear solely inside
  that public 10-K prose (0 in structured fields); aggregates are pure graph counts.
  Re-run the check if the file is regenerated.

## Repo state this runbook assumes

- `frontend/` — the static dashboard (vanilla ES modules; renders only, never writes).
- `frontend/build.py` — the **Pages build step** (stdlib-only). Mirrors committed snapshots
  + derived dossiers + the slimmed graph into `frontend/` and writes `manifest.json`.
- `data/dossiers/<TICKER>/dossier.json` and `data/graph_coverage.json` — committed, derived,
  licensed-adjacent (private repo only).
- `functions/_middleware.js` — the fail-closed Basic Auth gate.
- `wrangler.toml` — declares `pages_build_output_dir = "frontend"` and enables Functions.

## Runbook (dashboard — operator runs these)

**The fail-closed Function returns 401 to everyone until `BASIC_AUTH_*` are set, so a
reachable deploy is not yet a leak — but keep the URL private until BLOCKER A passes.**

0. **Make sure the gate is on the production branch** (see the ⚠ box). If Pages builds
   from `main`, `functions/` + `wrangler.toml` must be on `main`.
1. **Create / connect the Pages project (Git integration).** Cloudflare dashboard →
   Workers & Pages → Create → Pages → Connect to Git → select `techmuns/mosaic-theory`.
   Production branch = `main`.
2. **Build settings.**
   - Framework preset: **None**.
   - Build command: `python frontend/build.py`
   - Build output directory: `frontend`
   - Root directory: **leave BLANK** = the repository root (where `functions/`,
     `wrangler.toml`, and `frontend/` all live). Do NOT set it to `frontend`.
   - Build env var `PYTHON_VERSION = 3.11` (build.py is stdlib-only; no `requirements.txt`).
   - Confirm the build log shows **Functions** compiled (it picks up `functions/_middleware.js`).
3. **Set the Basic Auth credentials.** Workers & Pages → your project →
   **Settings → Variables and Secrets**, for **Production** (and Preview if you use it):
   - `BASIC_AUTH_USER = <a username>`
   - `BASIC_AUTH_PASS = <a strong password>` — add it as an **encrypted secret**, not plaintext.
   Then **Deployments → Retry deployment** (or push a commit) so the Function picks them up.
4. **BLOCKER A — verify auth rejection (the irreversible gate).** Run the incognito + `curl`
   checks above; every path must return `401`. Then enter the username/password in the
   browser prompt and confirm the dashboard renders. **Do not share the URL until A passes
   on all three paths.**
5. **Done — the deploy is live and authed.** Pushes to `main` auto-deploy; `build.py`
   re-mirrors the snapshots each time. Share the URL + credentials with your teammate over
   a secure channel (never commit them).

## How the gate works (and why it fails closed)

`functions/_middleware.js` runs on **every** request — including direct `/dossiers/*.json`
and `/snapshots/*` fetches. It requires an HTTP Basic Auth credential matching
`BASIC_AUTH_USER` / `BASIC_AUTH_PASS` (constant-time compared); anything else gets `401`
with a `WWW-Authenticate: Basic` challenge (the browser login prompt). If either env var is
unset, it denies **everything**. A bug in it can only DENY, never leak. Basic Auth rides
inside TLS, so credentials are encrypted in transit; for a small internal dashboard a single
strong shared credential is sufficient.

## The graph (BLOCKER B passed)

`data/graph_coverage.json` is committed (with a `!data/graph_coverage.json` `.gitignore`
exception) and CIQ-free (verified above). `build.py` slims it into
`frontend/snapshots/graph.json` (only `evidence` = public 10-K phrases + graph counts), so
the served graph is CIQ-free by construction.

## Rollback / un-deploy

Delete the deployment or the project to take the site offline. **Note the asymmetry:** this
stops *future* serving but cannot retract data already served while reachable — which is why
BLOCKER A precedes sharing the URL.

## If the repo or deploy ever goes public

`data/dossiers/`, `frontend/dossiers/`, and `data/graph_coverage.json` revert to
git-ignored / local-only (CLAUDE.md). The authed deploy is the **only** sanctioned place
these derived artifacts are served.
