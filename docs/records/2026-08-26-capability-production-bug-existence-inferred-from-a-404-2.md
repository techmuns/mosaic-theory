---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **PRODUCTION BUG — EXISTENCE INFERRED FROM A 404 (2026-07-20, fix/existence-from-index; MERGED

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **CAUSE.** The dossier view PROBED for `dossiers/<T>.json` and read "no dossier" off a **404**.
    True on a plain static server; NOT on the authed Pages origin — `functions/_middleware.js`
    runs on EVERY request and a miss that fails inside `ctx.next()` falls through its bare
    `catch {}` to `challenge()` = **401**. `getDossier` tolerates only 404 → rethrew → the awaited
    `Promise.all` rejected → the render died at "Loading dossier…" before reaching the underwrite
    fallback. **A host-semantics dependency that local dev can never expose.**
  - **WHY ONLY WERN.** It is the only ticker with an underwrite record but NO dossier — the only
    page whose NORMAL path requires a MISSING file. Every other name has a real dossier.json and
    never takes the branch. (Unknown tickers hung identically; nothing links to one.)
  - **FIX — absence is DATA, not an error code.** `dossiers/index.json` + `scenarios/index.json`
    already list exactly what the build emitted, so the view asks them and fetches only what is
    known to exist. No probe, no error-code interpretation, no dependence on host 404 semantics.
    The helpers stay FAIL-LOUD (a 500/401 on a file that SHOULD exist must still throw, never
    silently degrade to "nothing committed yet") — the fix stops ASKING for known-absent files.
  - **Verified by REPRODUCTION, not reasoning:** a local origin answering 401 for a miss (the
    middleware's behavior) reproduced the hang exactly; after the fix WERN renders "first
    analysis" + the card with the origin still returning 401; VRRM renders; unknown ZZZZ shows the
    honest notice. The regression pin FAILS on the pre-fix JS (demonstrated).
  - **INVARIANT** (per the incident rule): `test_dossier_view_resolves_existence_from_the_index_
    never_from_a_404` — the per-name fetches must be index-gated and appear exactly once, so an
    unguarded probe cannot creep back.
  - **STILL OPEN (flagged, not fixed — scope):** `getThemeDriver(slug)` is the one remaining
    per-name probe with the same assumption; unreachable today because the router only offers
    slugs from the themes index. Every other 404-degrading helper reads a whole-file artifact that
    IS committed (audited: 10 of them, all present), so none take the 404 path in production.
  - **GENERAL LESSON:** a static-server 404 is not a contract. Any "does this artifact exist?"
    question must be answered by a committed manifest, never by interpreting a transport error.
