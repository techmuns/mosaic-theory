"""Publishing the research desk into the main app (option C, 2026-10-13, PR #703).

`publish` renders a run and writes `frontend/theme-intelligence/`: the standalone pages (site/), the
desk's own script (desk.js) and its component styles scoped under `.intel` and re-pointed at the
app's design tokens (intel.css). Pinned here: what is published and what never is (the per-card
JSON / Markdown exports, the run manifest, local paths); a test-domain registry is refused by
default; a folder holding anything else is never replaced; a re-publish replaces the last one; the
app's script is the desk's script; every style rule is confined to the section; every app token
it points at exists in the app's stylesheet, with no self-reference; and every class the desk
shares with an app rule is reset. HYPOTHETICAL articles; no network, no model call.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence import desk, publish
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.publish import APP_COLLISIONS, APP_TOKENS, PublishError
from vinci.theme_intelligence.schemas import RunStatus

ROOT = Path(__file__).resolve().parents[1]
APP_CSS = (ROOT / "frontend" / "assets" / "styles.css").read_text()
AS_OF = date(2026, 10, 12)
LINES = ("Memory suppliers raised HBM contract prices 12% in 3Q26.",
         "DRAM contract prices rose 9% in 3Q26.")


def _pipe(tmp_path: Path, n: int = 1) -> Pipeline:
    pipe = make_pipeline(tmp_path)
    for k in range(n):
        pipe.start_run("ingest", as_of=AS_OF)
        art = Hypo(f"publish-{k}", "Test Publisher", date(2026, 10, 6),
                   [("paragraph", LINES[k])])
        ingest(pipe, art.doc(), extraction(
            [claim("c1", "b001", LINES[k].rstrip("."), f"prices up ({k})", metric="price change",
                   value=12 if k == 0 else 9, value_text="12%" if k == 0 else "9%", unit="%",
                   period="3Q26")],
            [hyp("h1", ("HBM", "DRAM")[k] + " contract prices rise",
                 node="ai_infrastructure.memory", mechanism="pricing_cycle", geography=("US",
                                                                                     "Korea")[k],
                 supporting=["c1"])]), as_of=AS_OF, publisher=art.publisher)
        pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe


def _run(pipe: Pipeline) -> str:
    return max(pipe.store.runs(), key=lambda r: r.started_at).run_id


def test_a_test_domain_registry_is_never_published_unless_asked(tmp_path: Path) -> None:
    pipe = _pipe(tmp_path)  # the hypothetical articles live on the reserved .test domain
    out = tmp_path / "frontend" / "theme-intelligence"
    with pytest.raises(PublishError, match="reserved test domain"):
        publish.publish(pipe.store, _run(pipe), out)
    assert not out.exists()  # refused: nothing written
    m = publish.publish(pipe.store, _run(pipe), out, allow_test_data=True)
    assert m["test_data"] is True


def test_the_publication_holds_the_pages_the_app_shows_and_nothing_else(tmp_path: Path) -> None:
    pipe = _pipe(tmp_path)
    out = tmp_path / "pub"
    m = publish.publish(pipe.store, _run(pipe), out, allow_test_data=True)
    files = sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())
    assert files == sorted([*m["files"], "index.json"])
    for need in ("site/index.html", "site/themes.html", "site/articles.html", "site/review.html",
                 "site/uploads.html", "site/sources.html", "site/dashboard.html",
                 "site/report_print.html", "desk.js", "intel.css"):
        assert need in files, need
    (t,) = pipe.store.theses()
    for need in (f"site/theses/{t.thesis_id}.html", f"site/cards/{t.thesis_id}.html",
                 f"site/cards/{t.thesis_id}.print.html"):
        assert need in files, need
    assert not [f for f in files if f.endswith((".json", ".md", ".csv")) and f != "index.json"]
    local = (str(tmp_path), str(Path.home()))
    for f in files:
        text = (out / f).read_text()
        assert not [x for x in local if x in text], f  # no local path is published
    assert (out / "desk.js").read_text().endswith(desk.JS)  # the app runs the desk's own script
    meta = json.loads((out / "index.json").read_text())
    assert meta["kind"] == publish.KIND and meta["run_id"] == _run(pipe) and meta["theses"] == 1


def test_a_folder_holding_anything_else_is_never_replaced(tmp_path: Path) -> None:
    pipe = _pipe(tmp_path)
    out = tmp_path / "pub"
    out.mkdir()
    (out / "notes.txt").write_text("someone else's file")
    with pytest.raises(PublishError, match="not a theme-intelligence publication"):
        publish.publish(pipe.store, _run(pipe), out, allow_test_data=True)
    assert (out / "notes.txt").read_text() == "someone else's file"


def test_a_republish_replaces_the_last_publication_whole(tmp_path: Path) -> None:
    """A page the last publication wrote and this one does not is removed (a republish is whole);
    a file the last publication did NOT write is never deleted — the publish is refused and
    nothing is written (U32e: the docstring promised the refusal, the code deleted the file)."""
    pipe2 = _pipe(tmp_path / "second", n=2)
    out = tmp_path / "pub"
    first = publish.publish(pipe2.store, _run(pipe2), out, allow_test_data=True)
    pipe = _pipe(tmp_path)
    m = publish.publish(pipe.store, _run(pipe), out, allow_test_data=True)
    gone = set(first["files"]) - set(m["files"])
    assert gone and all(not (out / f).exists() for f in gone)  # the last publication's own page
    assert m["theses"] == 1
    (out / "site" / "notes.html").write_text("an operator's file, not a publication's")
    before = sorted(p.name for p in out.rglob("*"))
    with pytest.raises(publish.PublishError, match="did not write"):
        publish.publish(pipe2.store, _run(pipe2), out, allow_test_data=True)
    assert (out / "site" / "notes.html").exists()  # NEGATIVE pin: never deleted …
    assert sorted(p.name for p in out.rglob("*")) == before  # … and nothing written


def _rules(css: str) -> list[tuple[str, str]]:
    """(selector, body) of every rule, @media blocks opened."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"@media[^{]*\{", "", css)
    return [(s.strip(), b) for s, b in re.findall(r"([^{}]+)\{([^{}]*)\}", css) if s.strip()]


def test_every_style_rule_is_confined_to_the_section() -> None:
    css = publish.app_css()
    rules = _rules(css)
    assert rules
    for sel, _b in rules:
        for one in sel.split(","):
            one = one.strip()
            assert one.startswith((".intel", "#intel-audit")), one


def test_every_app_token_the_section_uses_exists_and_none_refers_to_itself() -> None:
    app_tokens = set(re.findall(r"(--[\w-]+)\s*:", APP_CSS))
    for name, value in APP_TOKENS.items():
        target = re.fullmatch(r"var\((--[\w-]+)\)", value)
        assert target is not None, value
        assert target.group(1) in app_tokens, f"{name} -> {target.group(1)} is not an app token"
        assert target.group(1) != name, f"{name} refers to itself (a cycle)"
    # every desk token the components read is either mapped or one the app already defines
    used = set(re.findall(r"var\((--[\w-]+)\)", publish.app_css()))
    assert used <= set(APP_TOKENS) | app_tokens, used - set(APP_TOKENS) - app_tokens


def test_every_class_the_desk_shares_with_an_app_rule_is_reset(tmp_path: Path) -> None:
    """An app rule written for one of its OWN class names (`.main`, `.tabs`, `.flag` …) applies
    inside the section too: each such name the desk's markup uses must be reset in intel.css."""
    pipe = _pipe(tmp_path, n=2)
    out = tmp_path / "pub"
    publish.publish(pipe.store, _run(pipe), out, allow_test_data=True)
    desk_classes: set[str] = set()
    pages = [*(out / "site").glob("*.html"), *(out / "site" / "theses").glob("*.html")]
    for p in pages:
        if p.name in ("dashboard.html", "report_print.html"):
            continue  # opened as standalone pages, never inside the app
        page = BeautifulSoup(p.read_text(), "html.parser")
        for part in page.select("main.wrap, .testdata"):  # what the app shows of a page
            for el in [part, *part.find_all(class_=True)]:
                desk_classes |= set(el.get("class") or [])
    app_bare = {sel[1:] for sel, _b in _rules(APP_CSS) if re.fullmatch(r"\.[\w-]+", sel)}
    harmless = {"muted"}  # the app's rule only sets the same muted colour
    shared = (desk_classes & app_bare) - harmless
    assert shared <= set(APP_COLLISIONS), shared - set(APP_COLLISIONS)
    css = publish.app_css()
    for cls in APP_COLLISIONS:
        assert re.search(r"\.intel \." + cls + r"\{", css), cls


def test_a_page_carrying_a_local_path_is_never_published(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE pin: were a rendered page ever to print where the registry lives, the publication
    is refused whole — nothing written."""
    pipe = _pipe(tmp_path)
    real = publish.write_run_outputs

    def leaky(store: Any, run_id: str, out: Path) -> dict[str, Any]:
        res = real(store, run_id, out)
        page = Path(res["dir"]) / "index.html"
        page.write_text(page.read_text() + f"<!-- {store.path} -->")
        return res

    monkeypatch.setattr(publish, "write_run_outputs", leaky)
    out = tmp_path / "pub"
    with pytest.raises(PublishError, match="local path"):
        publish.publish(pipe.store, _run(pipe), out, allow_test_data=True)
    assert not out.exists()
