# DEPLOY — the authed Cloudflare Pages dashboard (runbook)

> Stand up the GitHub → Cloudflare Pages auto-deploy for the read-only ops dashboard
> (`frontend/`), gated behind **Cloudflare Access (Google login)**. This is the
> §4 CONDITIONAL item in STATE.md — it serves DERIVED, licensed-adjacent artifacts
> (per-ticker `dossier.json`, snapshots), so it is **authed-only** and carries one
> **irreversible** step. Read the whole file before connecting Cloudflare.
>
> **Repo-side scaffolding is already in place** (`wrangler.toml`,
> `functions/_middleware.js`, `frontend/build.py`). What remains is the **account-side**
> setup below, which only the operator can do (Cloudflare credentials), plus the two
> **BLOCKERS** that must pass before any licensed-derived data is served.

## Why this is handled with extra care

`frontend/dossiers/*.json` are DERIVED from licensed CIQ workbooks (extracted
`{value, source_ref}` facts + LLM synthesis + verbatim PUBLIC 10-K phrases — never
reproduced licensed CIQ). They are committed to this **private** repo for the authed
deploy (CLAUDE.md). **Once a reachable URL serves them unauthenticated, that cannot be
retracted.** Therefore: **Access is configured and proven BEFORE the site is reachable**,
and the origin is built to **fail closed**.

## The two BLOCKERS — both must pass before serving licensed data

- **BLOCKER A — prove the deployed URL rejects an unauthenticated request.** From a
  fresh incognito window (no Cloudflare cookies) and via `curl`, fetch the production
  URL **and** the `*.pages.dev` URL **and** a direct data path
  (`/dossiers/VRRM.json`, `/snapshots/ranked_queue.jsonl`). Each must return the
  Access/Google **challenge or `403`**, **never** content. This is the irreversible
  gate — do not proceed past it on a single untested assumption.
- **BLOCKER B — confirm `data/graph_coverage.json` is CIQ-free** *(only relevant if you
  choose to ship the graph; see "Optional: the graph" below)*. It must contain ONLY the
  EDGAR-10-K relationship/exposure map (verbatim 10-K evidence + graph counts), **zero**
  licensed CIQ financials. Until verified, the file stays git-ignored and the graph
  screen degrades to UNKNOWN (handled gracefully by `build.py`).

## Repo state this runbook assumes

- `frontend/` — the static dashboard (vanilla ES modules; renders only, never writes).
- `frontend/build.py` — the **Pages build step**. Mirrors committed snapshots + derived
  dossiers into `frontend/snapshots/` (git-ignored, regenerated every deploy) and
  `frontend/dossiers/` (committed + idempotently regenerated), and writes `manifest.json`.
  Stdlib-only (no pip deps).
- `data/dossiers/<TICKER>/dossier.json` — committed, derived, licensed-adjacent.
- `data/graph_coverage.json` — **git-ignored / absent by default.** Graph is optional.
- `functions/_middleware.js` — the fail-closed authed gate (defense-in-depth).
- `wrangler.toml` — declares `pages_build_output_dir = "frontend"` and enables Functions.

## Runbook (account-side — operator runs these)

**Order matters: configure Access + verify BLOCKER A BEFORE you share the URL.** (The
fail-closed Function already 403s every request until the env vars are set, so a deploy
that is merely *reachable* is not yet a leak — but the URL stays private until A passes.)

1. **Create the Pages project (Git integration).** Cloudflare dashboard → Workers & Pages
   → Create → Pages → Connect to Git → select `techmuns/mosaic-theory`. Production branch
   = `main`. (Connecting is fine; you gate *reachability* with Access in step 3, before
   you hand anyone the URL.)
2. **Build settings.**
   - Framework preset: **None**.
   - Build command: `python frontend/build.py`
   - Build output directory: `frontend`
   - Root directory: **leave BLANK** = the repository root (where `functions/`,
     `wrangler.toml`, and `frontend/` all live). Do NOT set it to `frontend` — every other
     field above is resolved relative to this, so the build command `python frontend/build.py`
     and the `functions/` discovery only work when the root is the repo root.
   - Build env var `PYTHON_VERSION = 3.11` (build.py is stdlib-only; no `requirements.txt`).
   - Confirm the build log shows **Functions** compiled (it picks up `functions/_middleware.js`).
3. **Turn on Access for the PRODUCTION URL (the gate). Do this before sharing any URL.**
   Cloudflare's one-click toggle protects *preview* URLs only; the production
   `<project>.pages.dev` needs one extra step (remove the wildcard):
   - Workers & Pages → your project → **Settings → Enable access policy**. This creates an
     Access application/policy for your **preview** deployments.
   - On that policy click **Manage** → it opens **Zero Trust → Access controls →
     Applications → your project → Configure**. Under **Public hostname**, in the
     **Subdomain** field **delete the `*` wildcard** and **Save**. Access now also covers the
     production `<project>.pages.dev` (you should end up with two policies — production +
     preview).
   - **Who can log in:** open that application's **policy** → **Allow** with a rule like
     **Emails** = your address(es); everyone else is blocked.
   - **Login method:** **One-time PIN** works with **zero extra setup** — the allowed email
     receives a 6-digit code. *(Google login is OPTIONAL and needs Google Cloud OAuth
     credentials: Zero Trust → Settings → Authentication → add Google. It changes nothing
     else — the Function validates the same Access JWT regardless of IdP — so add it later
     if you want it.)*
   - **Grab two values for step 4:** the application's **AUD** (Configure → **Additional
     settings → Application Audience (AUD) Tag**) and your **team domain**
     `<team>.cloudflareaccess.com` (Zero Trust → Settings; it's also in your Zero Trust
     dashboard URL).
4. **Wire the env vars so the fail-closed Function accepts the Access JWT** (see "How the
   gate works"). Workers & Pages → your project → **Settings → Variables and Secrets**
   (environment variables), **Production**:
   - `CF_ACCESS_TEAM_DOMAIN = <team>.cloudflareaccess.com`
   - `CF_ACCESS_AUD = <the production app's AUD Tag from step 3>`
   - *(optional)* `CF_ACCESS_ALLOWED_EMAILS = you@example.com,teammate@example.com`
   Then **Deployments → Retry deployment** (or push a commit) so the Function picks them up.
   **Until these are set the middleware denies every request (403)** — the safe default, so
   the site is already non-leaking even before you finish.
5. **BLOCKER A — verify auth rejection (the irreversible gate).** From incognito **and**
   `curl`, hit the production URL, a preview URL, and a data path (`/dossiers/VRRM.json`,
   `/snapshots/ranked_queue.jsonl`). Each must return the Access login challenge or `403` —
   **never** content. Then log in with an allowed email and confirm the dashboard renders.
   **Do not announce/share the URL until A passes on all three.**
6. **Done — the deploy is live and authed.** Pushes to `main` auto-deploy; `build.py`
   re-mirrors the snapshots each time.

## Optional: shipping the graph (gated on BLOCKER B)

The graph is OFF by default (`data/graph_coverage.json` git-ignored/absent → graph screen
shows UNKNOWN). To include it:
1. Regenerate `data/graph_coverage.json` (the EDGAR-10-K exposure build).
2. **Run BLOCKER B** — confirm it is CIQ-free (EDGAR-10-K relationship/exposure only).
3. Add the targeted `.gitignore` exception `!data/graph_coverage.json` **together with**
   committing the verified file (never add the exception before B passes — it invites an
   unverified `git add`). Raw CIQ in `data/manual/ciq/` stays ignored regardless.
4. Redeploy; `build.py` slims it into `frontend/snapshots/graph.json`.

## How the gate works (and why it fails closed)

Two layers, both required for "authed":
1. **Cloudflare Access (primary).** Sits in front of the project. An unauthenticated
   request is bounced to Google login; on success Access mints a signed, identity-level
   JWT (`Cf-Access-Jwt-Assertion` header / `CF_Authorization` cookie) carrying the email
   and the application `aud`.
2. **`functions/_middleware.js` (defense-in-depth).** Runs on **every** request —
   including direct `/dossiers/*.json` and `/snapshots/*.jsonl` fetches — and **denies
   unless** a valid Access JWT validates: signature against your team's
   `…/cdn-cgi/access/certs`, matching `aud`, not expired, optional email allowlist. If
   the Access policy is ever disabled or misconfigured, the origin still returns `403`.
   If `CF_ACCESS_TEAM_DOMAIN` / `CF_ACCESS_AUD` are unset, it denies **everything**.
   A bug in it can only DENY, never leak.

## Rollback / un-deploy

Disconnect the Pages project or delete the deployment to take the site offline. **Note
the asymmetry:** taking it down stops *future* serving but cannot retract data already
served while reachable — which is the entire reason BLOCKER A precedes step 6.

## If the repo or deploy ever goes public

`data/dossiers/`, `frontend/dossiers/`, and `data/graph_coverage.json` revert to
git-ignored / local-only (CLAUDE.md). The authed deploy is the **only** sanctioned place
these derived artifacts are served.
