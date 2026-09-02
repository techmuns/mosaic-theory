---
id:
status: open
prs: []
date: 2026-09-01
supersedes:
superseded-by:
---

# Cloudflare answers a missing asset with the app shell, and 19 graceful-absence branches keyed on 404

**WHAT.** `frontend/lib/snapshots.js` now treats a response whose body OPENS WITH MARKUP as an
absent artifact — raising the tagged 404 its callers are written to expect — in both `_json` and
`_jsonl`. Nothing else changes.

**WHY.** Every optional artifact in the viewer is fetched as
`catch (e) { if (e.status === 404) return null; }` — **19 sites**. That works only where the server
returns a real 404. `python -m http.server` does. **Cloudflare Pages does not**: for a path matching
no asset it serves `index.html` at status **200**, so `res.ok` is true, `.json()` throws a
`SyntaxError` carrying no `.status`, and all 19 catches RETHROW.

The theme detail page awaits its OPTIONAL economics roll-up. The two drivers frozen 2026-09-01 are
the first with no economics file, so on the deploy the page hung on **"Loading theme…"** forever
with `Uncaught (in promise) SyntaxError: Unexpected token '<'` — while rendering perfectly against a
local server. Every optional artifact absent from a deploy had the same failure available to it;
the theme pages are only where it surfaced first.

**WHAT IT WAS NOT.** The build was green — Python 3.13.3, all 5 themes emitted, 347 files uploaded,
`Success: Your site was deployed!`. Not a missing file (baskets, ledgers, scan history and both
theme JSONs are tracked), not a size limit (largest file 2.4 MB of a 21 MB deploy), not the auth
middleware (a blanket gate with no per-path rules), not the Python version. Each of those was
checked and cleared before the real cause was found, and a tracked-files-only rebuild rendered the
page fine — which is exactly what made the asymmetry invisible.

**HOW VERIFIED — reproduced before it was fixed.** A local static server that answers a missing path
with `index.html` at 200 (`/tmp/nocache/spa.py`) reproduced the deploy byte for byte: raw slug in
the breadcrumb, `Loading theme…`, and the same `SyntaxError: Unexpected token '<'`. With the fix the
same server renders the full page with no console errors. Three pins in
`tests/test_snapshot_absence.py` drive the REAL module with `fetch` stubbed per host behaviour;
removing the shell guard reds the deploy pin.

**DELIBERATELY NARROW.** Only a body that OPENS with `<` counts as the shell. A genuinely malformed
JSON file still raises its `SyntaxError` with no `status`, pinned by its own test — "unparseable
means absent" would turn a corrupt artifact into a silent blank section, which is the same class of
bug pointing the other way.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **A LOCAL PREVIEW CANNOT PROVE A DEPLOY.** The whole defect lives in the difference between two
   hosts' 404 behaviour, and every local check — including a tracked-files-only rebuild — passed.
   Verifying frontend absence paths now requires the SPA-fallback server, not `http.server`.
   FALSIFIER: if a second deploy-only frontend defect appears, the preview server should default to
   the fallback behaviour rather than being the special case.
2. **`context.json` still has no entry for either 2026-09-01 driver** — a separate, still-open gap.
   `driver_summary` is mechanical (a verbatim quote of the spec's first sentence) but
   `analyst_notes` are the operator's and are not invented here. `tests/test_theme_context.py`
   checks a HARDCODED map of the three July slugs, so the two new drivers escape that guard
   entirely; deriving it from the registry is the follow-up, and it will fail until the notes exist.
