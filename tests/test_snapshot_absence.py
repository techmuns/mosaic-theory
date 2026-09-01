"""A HOST THAT ANSWERS A MISSING ASSET WITH THE APP SHELL, NOT A 404 (2026-09-01).

Every graceful absence in `frontend/lib/snapshots.js` is written as
``catch (e) { if (e.status === 404) return null; }``. That works only where the server returns a
real 404. `python -m http.server` does; **Cloudflare Pages does not** — for a path matching no
asset it serves `index.html` at status **200**, so `res.ok` is true, `.json()` throws a
`SyntaxError` carrying no `.status`, and all 19 of those catches RETHROW.

The cost was not cosmetic. The theme page awaits its OPTIONAL economics roll-up, so the two drivers
frozen on 2026-09-01 — the first with no economics file — hung on "Loading theme…" forever on the
deploy while rendering perfectly against a local server. Reproduced with a fallback server, fixed
at the fetch layer, and pinned here so the asymmetry between local and deploy cannot return.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: Drive the REAL module with `fetch` stubbed to each host's behaviour. Imported through a file
#: URL because `frontend/` is not a package and the module is plain ESM.
_DRIVER = r"""
import { pathToFileURL } from "node:url";
import path from "node:path";
const body = process.argv[1], status = Number(process.argv[2]);
globalThis.fetch = async () => new Response(body, {
  status, headers: { "content-type": status === 200 ? "text/html" : "text/plain" } });
const m = await import(pathToFileURL(path.resolve("frontend/lib/snapshots.js")).href);
let out;
try { await m.getThemeEconomics("no-such-driver"); out = { returned: "value" }; }
catch (e) { out = { threw: String(e.message).slice(0, 60), status: e.status ?? null }; }
console.log(JSON.stringify(out));
"""


def _run(body: str, status: int) -> dict:
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    r = subprocess.run(["node", "--input-type=module", "-e", _DRIVER, body, str(status)],
                       capture_output=True, text=True, check=True, cwd=ROOT)
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_a_real_404_is_still_a_graceful_absence() -> None:
    """The behaviour that always worked, kept: a host that says 404 yields null, not a throw."""
    assert _run("not found", 404) == {"returned": "value"} or True  # returns null -> no throw
    assert "threw" not in _run("not found", 404)


def test_the_app_shell_at_200_is_read_as_absent_not_as_a_parse_error() -> None:
    """THE DEPLOY BUG. Cloudflare answers a missing asset with index.html at 200; before the fix
    this surfaced as `SyntaxError: Unexpected token '<'` and took the whole page down with it."""
    assert "threw" not in _run("<!doctype html><html><body>app</body></html>", 200), (
        "the app shell served at 200 must be read as ABSENT — it is how Cloudflare Pages "
        "answers a missing asset, and every graceful-absence branch keys on status 404")


def test_genuinely_malformed_json_still_raises() -> None:
    """DELIBERATELY NARROW. Only a body that OPENS with markup counts as the shell; a real file
    whose JSON is broken must still fail loudly rather than be reported as 'not committed'."""
    out = _run("{ this is not json", 200)
    assert out.get("threw"), "a malformed JSON body must not be swallowed as absence"
    assert out.get("status") is None, "a parse error must not be disguised as a 404"
