"""A thesis a publication drops is answered by name, and a desk left behind is said (the review of
#760, 2026-10-21).

The one-registry publication dropped 14 theses' pages: a link someone saved answered with "This page
is not in the published research desk" at best — and, on a host answering a real 404, with "No
theme-intelligence run is published yet". `publish` now keeps every dropped thesis in index.json's
"retired" (title, day, last run), carried forward; the app's view names it. And the app shows a
PUBLISHED copy that nothing kept current: `publish --check` says when it is behind, and the
weekly job runs it every week. HYPOTHETICAL articles; no network, no model call.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.test_theme_intelligence_publish import AS_OF, _pipe, _run
from vinci.theme_intelligence import publish
from vinci.theme_intelligence.schemas import RunStatus

ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "frontend" / "views" / "intel" / "desk.js").resolve().as_uri()
WORKFLOW = ROOT / ".github" / "workflows" / "theme-intelligence-weekly.yml"


def _theses(m: dict[str, Any]) -> set[str]:
    return {Path(f).stem for f in m["files"] if f.startswith("site/theses/TH-")}


def test_a_dropped_thesis_is_kept_as_retired_by_name_and_leaves_when_it_returns(
        tmp_path: Path) -> None:
    pipe2 = _pipe(tmp_path / "second", n=2)
    out = tmp_path / "pub"
    first = publish.publish(pipe2.store, _run(pipe2), out, allow_test_data=True)
    assert first["retired"] == {}  # a first publication drops nothing
    title = {t: re.search(r"<h1[^>]*>(.*?)</h1>", (out / "site" / "theses" / f"{t}.html")
                          .read_text(), re.S).group(1) for t in _theses(first)}  # type: ignore[union-attr]
    pipe = _pipe(tmp_path)
    m = publish.publish(pipe.store, _run(pipe), out, allow_test_data=True)
    dropped = _theses(first) - _theses(m)
    assert dropped and set(m["retired"]) == dropped
    for tid in dropped:
        entry = m["retired"][tid]
        assert entry["title"] and entry["title"] in title[tid]
        assert entry["last_run"] == first["run_id"] and re.fullmatch(r"\d{4}-\d\d-\d\d",
                                                                     entry["retired_on"])
    again = publish.publish(pipe.store, _run(pipe), out, allow_test_data=True)
    assert again["retired"] == m["retired"]  # carried forward, unchanged
    back = publish.publish(pipe2.store, _run(pipe2), out, allow_test_data=True)
    assert back["retired"] == {}  # NEGATIVE: a thesis published again leaves the list


def _view(fetches: dict[str, Any], route: list[str]) -> str:
    """The app's view under node: `fetches` maps a path suffix to (status, body) — a dict body is
    JSON, a str body HTML; anything else answers 404."""
    js = f"""
const table = {json.dumps(fetches)};
globalThis.fetch = async (url) => {{
  const key = Object.keys(table).find((k) => url.endsWith(k));
  const [status, body] = key ? table[key] : [404, ""];
  return {{ ok: status === 200, status,
           text: async () => typeof body === "string" ? body : JSON.stringify(body),
           json: async () => body }};
}};
globalThis.DOMParser = class {{ parseFromString() {{ return {{ querySelector: () => null }}; }} }};
const {{ render }} = await import({json.dumps(VIEW)});
const root = {{ innerHTML: "" }};
await render(root, {json.dumps(route)}, {{ item: {{}}, frame: (_i, o) => o.bodyHtml }});
console.log(JSON.stringify(root.innerHTML));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", js], capture_output=True,
                         text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return str(json.loads(out.stdout.strip().splitlines()[-1]))


@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_a_saved_link_to_a_retired_thesis_is_answered_by_name_end_to_end(tmp_path: Path) -> None:
    """END TO END: the index.json a real republish writes, read by the app's own view. A real 404
    (a host that answers one) and Cloudflare's app-index answer (HTTP 200) are both named."""
    pipe2 = _pipe(tmp_path / "second", n=2)
    out = tmp_path / "pub"
    publish.publish(pipe2.store, _run(pipe2), out, allow_test_data=True)
    pipe = _pipe(tmp_path)
    m = publish.publish(pipe.store, _run(pipe), out, allow_test_data=True)
    (tid, entry), = m["retired"].items()
    index = json.loads((out / "index.json").read_text())
    app_index = '<html><body><main class="main" id="main"></main></body></html>'
    for page in ([404, ""], [200, app_index]):
        html = _view({"index.json": [200, index], f"theses/{tid}.html": page},
                     ["themes", tid])
        assert f"This thesis was retired from the research desk on {entry['retired_on']}." in html
        assert entry["title"] in html and entry["last_run"] in html


@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_a_page_not_in_the_desk_never_reads_as_nothing_published() -> None:
    """NEGATIVE: a thesis that was never retired is "not in the published research desk"; a real
    404 for it no longer claims no run is published. The desk's home missing still does."""
    index = {"retired": {}}
    page = _view({"index.json": [200, index]}, ["themes", "TH-ABC123"])
    assert "This page is not in the published research desk." in page
    assert "No theme-intelligence run is published yet" not in page
    assert "retired" not in page
    home = _view({"index.json": [200, index]}, [])
    assert "No theme-intelligence run is published yet" in home


def test_publish_check_says_when_the_app_is_behind_the_registry(tmp_path: Path) -> None:
    pipe = _pipe(tmp_path)
    out = tmp_path / "pub"
    nothing = publish.publication_lag(pipe.store, out)
    assert nothing is not None and nothing.startswith("nothing is published")
    m = publish.publish(pipe.store, _run(pipe), out, allow_test_data=True)
    assert publish.publication_lag(pipe.store, out) is None  # NEGATIVE: current says nothing
    pipe.start_run("market", as_of=AS_OF)
    newer = pipe.finish_run(RunStatus.SUCCEEDED)
    lag = publish.publication_lag(pipe.store, out)
    assert lag is not None and m["run_id"] in lag and newer.run_id in lag
    assert "republish" in lag


def test_the_weekly_job_says_when_the_app_is_behind_and_never_fails_on_it() -> None:
    """The check runs after the state-branch commit, warns (::warning::), and cannot fail the
    job — the desk being behind is a to-do, never a broken week."""
    text = WORKFLOW.read_text()
    steps = re.split(r"\n(?=      - (?:name|uses):)", text)
    names = [s.split("\n", 1)[0].strip() for s in steps]
    check = [i for i, s in enumerate(steps) if "publish --check" in s]
    commit = [i for i, n in enumerate(names) if n.startswith("- name: Commit the registry")]
    assert check and commit and check[0] > commit[0]
    step = steps[check[0]]
    assert "continue-on-error: true" in step and "::warning::" in step and "exit 0" in step
    assert re.search(r"if:\s*always\(\)", step)
