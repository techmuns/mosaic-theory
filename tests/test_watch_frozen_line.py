"""THE WATCH LINE (STATE row 41 (b); B's design, issue #1004 comment 6847522000 item 6; the
operator's marking, comment 6847554747, 2026-11-13, "go ahead").

A watch page is kept as committed with no paid rebuild until its name goes active, so it says so
near its top, on both surfaces: the move's date and ruling from the coverage roster, and the known
defects it keeps until then, from `data/watch_defects.json`. The line is read from the roster at
RENDER time (md) and at DEPLOY time (web, `snapshots/coverage.json`), never stored in the page, so
a move to active removes it at the next render with no page edit.

Every pin reads the REAL committed roster, defect file and pages. The anchors are the roster's and
the defect file's own text, composed by `WatchNotice` — committed data, not an LLM's words.
"""
from __future__ import annotations

import html
import importlib.util
import json
import re
import shutil
import subprocess
from datetime import date
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from vinci import coverage_roster as roster
from vinci.dossier.assemble import _read_scenario_card
from vinci.dossier.render import render_markdown
from vinci.dossier.schemas import Dossier

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOSS = DATA / "dossiers"
LATEST = roster.current(DATA)
WATCH = sorted(t for t, m in LATEST.items() if m.status == "watch")
ACTIVE = sorted(t for t, m in LATEST.items() if m.status == "active")
BRIEF = "# Brief — first cut"


def _page(t: str, root: Path = DOSS) -> dict[str, Any]:
    out: dict[str, Any] = json.loads((root / t / "dossier.json").read_text())
    return out


def _md(t: str, root: Path = DOSS) -> str:
    d = Dossier.model_validate_json((root / t / "dossier.json").read_text())
    return render_markdown(d, card=_read_scenario_card(t), dossiers_root=root)


def _notice(t: str) -> roster.WatchNotice:
    n = roster.watch_notice(DATA, t, _page(t))
    assert n is not None, f"{t} is on watch and has no notice"
    return n


def _as_watch(t: str) -> roster.WatchNotice:
    """The notice an ACTIVE name WOULD print were it on watch — what its page must not carry."""
    m = LATEST[t]
    return roster.WatchNotice(move=roster.Move(date=m.date, ticker=t, status="watch",
                                               ruling=m.ruling, source=m.source,
                                               record=m.record), defects=())


def _md_text(md: str) -> str:
    """The md watch block as plain text: from its head to the blank line after it."""
    start = md.index("> **Frozen since")
    block = md[start:md.index("\n\n", start)]
    lines = [re.sub(r"^\d+\. ", "", ln.removeprefix(">").strip()) for ln in block.split("\n")]
    return " ".join(ln.replace("**", "") for ln in lines if ln)


def _build() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_watch_build", ROOT / "frontend" / "build.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_pins_walk_the_operators_marking() -> None:
    """Non-vacuous: the 15 watch names and the 11 active names of the 2026-11-13 marking."""
    assert len(WATCH) == 15 and len(ACTIVE) == 11, (WATCH, ACTIVE)


# --- md, end to end: committed JSON + the committed roster → render_markdown ------------------


def test_md_every_watch_page_prints_its_line_above_the_brief_e2e() -> None:
    for t in WATCH:
        md, n = _md(t), _notice(t)
        head = f"> **{n.head()}** {n.ruling()} {n.kept()}"
        assert md.count(head) == 1, f"{t}: the watch line is not printed once"
        assert md.index(head) < md.index(BRIEF), f"{t}: the watch line is below the Brief"
        assert md.index("_" + f"{Dossier.model_validate(_page(t)).assembled_at:%B %-d, %Y}") \
            < md.index(head), f"{t}: the watch line is above the page's own date"
        for x in n.defects:
            assert md.count(x.sentence()) == 1, f"{t}: a listed defect is not printed once"
            assert md.index(x.sentence()) < md.index(BRIEF)
        assert (n.defects_head() in md) == bool(n.defects), (
            f"{t}: the defects heading must print exactly when defects are listed")


def test_md_no_active_page_prints_a_watch_line_e2e() -> None:
    for t in ACTIVE:
        md, n = _md(t), _as_watch(t)
        assert n.head() not in md and n.kept() not in md, f"{t}: an active page prints the line"
        assert n.defects_head() not in md


def test_the_committed_md_and_its_web_mirror_carry_the_line_e2e() -> None:
    """The artifact pass happened: each committed watch page's md, and its served mirror, carry
    the line the renderer prints today; no active page's does."""
    for t in WATCH:
        n = _notice(t)
        for path in (DOSS / t / "dossier.md", ROOT / "frontend" / "dossiers" / f"{t}.md"):
            assert n.head() in path.read_text(), f"{path}: the watch line is not committed"
    for t in ACTIVE:
        for path in (DOSS / t / "dossier.md", ROOT / "frontend" / "dossiers" / f"{t}.md"):
            assert _as_watch(t).head() not in path.read_text(), f"{path}: carries a watch line"


# --- the defect file: its citations resolve, and every defect is on its page --------------------


def _open_rows() -> set[int]:
    """STATE.md §5.0 OPEN NOW's row numbers, read as the session-start hook reads them."""
    lines = (ROOT / "STATE.md").read_text().splitlines()
    head = next(i for i, x in enumerate(lines) if x.startswith("### 5.0"))
    end = next((i for i, x in enumerate(lines[head + 1:], head + 1) if x.startswith("### ")),
               len(lines))
    return {int(m.group(1)) for x in lines[head + 1:end]
            if (m := re.match(r"^\|\s*(\d+)\s*\|", x))}


def test_every_defect_cites_an_open_state_row_and_a_record_that_exist() -> None:
    """A defect names the open STATE row that tracks it and the record that measured it. A row
    closed while a watch page still carries its defect turns this red: re-point it, or the
    page's defect is no longer tracked anywhere."""
    defects = roster.read_defects(DATA)
    assert defects, "no defect is listed — the pins below would pass vacuously"
    rows = _open_rows()
    assert len(rows) >= 10, f"read only {len(rows)} §5.0 rows — the table moved"
    for t, ds in defects.items():
        for x in ds:
            assert x.state_row in rows, f"{t}: STATE row {x.state_row} is not an open §5.0 row"
            assert (ROOT / x.record).is_file(), f"{t}: {x.record} does not exist"


def test_every_defect_is_on_its_page_and_listed_for_a_covered_name() -> None:
    """Each defect's page field still holds the value it was measured at, on the committed page,
    and its name is on watch or active. A rebuild or refresh that fixes one turns this red until
    the entry is removed, so the line never names a defect the page no longer has."""
    defects = roster.read_defects(DATA)
    pages = {t: _page(t) for t in defects if (DOSS / t / "dossier.json").is_file()}
    assert set(pages) == set(defects), "a defect is listed for a name with no committed page"
    assert roster.defect_problems(LATEST, defects, pages) == []


# --- going active: one roster line removes the line, with no page edit ----------------------


def _scratch(tmp_path: Path, tickers: tuple[str, ...] = ("UBER",), *,
             extra_line: str = "", defects: str | None = None) -> Path:
    """A data dir holding the committed roster (+ ``extra_line``), the committed defect file (or
    ``defects``) and the named pages, copied so a case can change one of them."""
    data = tmp_path / "data"
    for t in tickers:
        (data / "dossiers" / t).mkdir(parents=True)
        shutil.copy(DOSS / t / "dossier.json", data / "dossiers" / t / "dossier.json")
    (data / roster.ROSTER_NAME).write_text(
        (DATA / roster.ROSTER_NAME).read_text() + extra_line, encoding="utf-8")
    (data / roster.DEFECTS_NAME).write_text(
        defects if defects is not None else (DATA / roster.DEFECTS_NAME).read_text(),
        encoding="utf-8")
    return data


def _move(t: str, status: str, when: str = "2026-11-17") -> str:
    return roster.render_line(roster.Move(date=date.fromisoformat(when), ticker=t, status=status,
                                          ruling="test", source="test", record=None)) + "\n"


def test_a_name_moved_to_active_loses_the_line_on_both_surfaces(tmp_path: Path,
                                                                 monkeypatch: Any) -> None:
    before = _scratch(tmp_path / "before")
    after = _scratch(tmp_path / "after", extra_line=_move("UBER", "active"))
    n = _notice("UBER")
    assert n.head() in _md("UBER", before / "dossiers")
    md = _md("UBER", after / "dossiers")
    assert n.head() not in md and n.kept() not in md and n.defects_head() not in md
    assert all(x.sentence() not in md for x in n.defects)
    # the web: the deploy snapshot from the moved roster, rendered by the production page
    build = _build()
    monkeypatch.setattr(build, "COVERAGE", after / roster.ROSTER_NAME)
    monkeypatch.setattr(build, "WATCH_DEFECTS", after / roster.DEFECTS_NAME)
    snap = build._coverage_snapshot(["UBER"])
    assert snap["names"]["UBER"]["status"] == "active" and "defects" not in snap["names"]["UBER"]
    assert 'class="ds-frozen' not in _web(snap, ("UBER",))["UBER"]["header"]


# --- the guards: positive and negative pins ---------------------------------------------------


def test_a_defect_the_page_no_longer_holds_refuses_the_render(tmp_path: Path) -> None:
    """NEGATIVE: PARR's page with its stored 225 bps margin changed — the value its listed defect
    is bound to has moved, so the render refuses, naming the field, rather than print a defect
    the page no longer has. POSITIVE: the unchanged copy renders its line. (The check reads the
    page as its one writer writes it, `dossier_json`, which re-derives `valuation_basis`, so a
    stored value is what a test moves here.)"""
    data = _scratch(tmp_path, ("PARR",))
    n = _notice("PARR")
    assert n.head() in _md("PARR", data / "dossiers")
    [x] = n.defects
    page = _page("PARR", data / "dossiers")
    assert roster.page_value(page, x.page_field) == 225.0
    page["mechanical"]["capital_structure"]["covenant_term_rows"]["value"][2]["margin_bps"] = 200.0
    (data / "dossiers" / "PARR" / "dossier.json").write_text(json.dumps(page, indent=2))
    with pytest.raises(roster.WatchDefectError, match=f"PARR: {x.page_field} holds 200.0"):
        _md("PARR", data / "dossiers")


def test_a_defect_listed_for_a_retired_or_unlisted_name_is_refused(tmp_path: Path) -> None:
    raw = json.loads((DATA / roster.DEFECTS_NAME).read_text())
    for gone in ("MVST", "ZZZZ"):          # retired on the roster; never on it
        bad = dict(raw, **{gone: raw["UBER"]})
        data = _scratch(tmp_path / gone, defects=json.dumps(
            dict(sorted(bad.items())), indent=2, ensure_ascii=False) + "\n")
        with pytest.raises(roster.WatchDefectError, match=gone):
            _md("UBER", data / "dossiers")


def test_a_watch_page_whose_tree_has_no_defect_file_is_refused(tmp_path: Path) -> None:
    """An absent defect file beside a roster is not "no defects": the page would print its line
    as if it kept none. The reader refuses it directly too."""
    data = _scratch(tmp_path)
    (data / roster.DEFECTS_NAME).unlink()
    with pytest.raises(roster.WatchDefectError, match="no known-defect file"):
        _md("UBER", data / "dossiers")
    with pytest.raises(roster.WatchDefectError, match="no known-defect file"):
        roster.read_defects(data)


def test_a_tree_with_no_roster_renders_no_line_and_the_reader_still_refuses(
        tmp_path: Path) -> None:
    """A scratch tree holding no roster (a test's or a probe's copy) renders no line, rather
    than paste the live roster onto a copy built to differ from it. The data tree always holds
    one, and the committed pages are pinned above; the roster's own reader still refuses an
    absent file."""
    data = _scratch(tmp_path)
    (data / roster.ROSTER_NAME).unlink()
    assert _notice("UBER").head() not in _md("UBER", data / "dossiers")
    with pytest.raises(roster.CoverageRosterError, match="no coverage roster"):
        roster.watch_notice(data, "UBER", _page("UBER", data / "dossiers"))


def _one(**change: Any) -> str:
    entry = json.loads((DATA / roster.DEFECTS_NAME).read_text())["UBER"][0]
    entry.update(change)
    return json.dumps({"UBER": [entry]}, indent=2, ensure_ascii=False) + "\n"


@pytest.mark.parametrize("case, text, says", [
    ("extra field", _one(extra=1), "exactly"),
    ("full stop", _one(defect="It is wrong."), "full stop"),
    ("a record outside docs/records", _one(record="STATE.md"), "docs/records"),
    ("a row that is no number", _one(state_row="28"), "STATE.md row number"),
    ("a field that is no pointer", _one(page_field="valuation_basis.priceable"), "JSON pointer"),
    ("a null value", _one(page_value=None), "scalar"),
    ("a name with no defect", '{\n  "UBER": []\n}\n', "lists no defect"),
    ("not canonical", _one().replace("  ", "    "), "canonical"),
])
def test_a_malformed_defect_file_is_refused(tmp_path: Path, case: str, text: str,
                                            says: str) -> None:
    (tmp_path / roster.DEFECTS_NAME).write_text(text, encoding="utf-8")
    with pytest.raises(roster.WatchDefectError, match=says):
        roster.read_defects(tmp_path)


def test_the_committed_defect_file_reads() -> None:
    """POSITIVE: the committed file passes every check above."""
    assert roster.render_defects(roster.read_defects(DATA)) == (DATA / roster.DEFECTS_NAME
                                                                ).read_text()


def test_the_deploy_snapshot_refuses_without_the_defect_file(tmp_path: Path,
                                                            monkeypatch: Any) -> None:
    build = _build()
    monkeypatch.setattr(build, "WATCH_DEFECTS", tmp_path / roster.DEFECTS_NAME)
    with pytest.raises(SystemExit, match="no known-defect file"):
        build._coverage_snapshot(WATCH)


def test_the_deploy_snapshot_is_the_backend_notice_on_the_committed_tree() -> None:
    """The stdlib twin copies what `watch_notice` reads: each published name's move, and a watch
    name's defects, field for field."""
    snap = _build()._coverage_snapshot(roster.covered_pages(DATA))
    assert sorted(snap["names"]) == roster.covered_pages(DATA)
    for t, c in snap["names"].items():
        m = LATEST[t]
        assert (c["status"], c["date"], c["ruling"], c["source"], c["record"]) == (
            m.status, m.date.isoformat(), m.ruling, m.source, m.record)
        if m.status == "watch":
            assert c["defects"] == [{"defect": x.defect, "state_row": x.state_row,
                                     "record": x.record} for x in _notice(t).defects]
        else:
            assert "defects" not in c


# --- web twin (dossier.js), end to end: the deploy snapshot → the production renderDossier ------

_DRIVER = """
const handler = { get: () => stub, apply: () => stub, construct: () => ({}) };
const stub = new Proxy(function(){}, handler);
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
import { readFileSync } from "node:fs";
const { renderDossier, useCoverage } = await import(__DJ__);
useCoverage(__TABLE__);
const out = {};
for (const t of __TICKERS__) {
  const d = JSON.parse(readFileSync(__ROOT__ + "/data/dossiers/" + t + "/dossier.json"));
  const html = renderDossier(d, null, null);
  const tabs = html.indexOf('<div class="ds-tabs"');
  out[t] = { header: html.slice(0, tabs), rest: html.slice(tabs) };
}
console.log(JSON.stringify(out));
"""


def _web(table: dict[str, Any] | None, tickers: tuple[str, ...]) -> dict[str, dict[str, str]]:
    if not shutil.which("node"):
        pytest.skip("node not available")
    driver = (_DRIVER
              .replace("__DJ__", json.dumps((ROOT / "frontend/views/shared/dossier.js").as_uri()))
              .replace("__ROOT__", json.dumps(str(ROOT)))
              .replace("__TABLE__", json.dumps(table))
              .replace("__TICKERS__", json.dumps(list(tickers))))
    res = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True, cwd=ROOT)
    out: dict[str, dict[str, str]] = json.loads(res.stdout)
    return out


@lru_cache(maxsize=1)
def _web_committed() -> dict[str, dict[str, str]]:
    snap = _build()._coverage_snapshot(roster.covered_pages(DATA))
    return _web(snap, tuple(WATCH + ACTIVE))


def _frozen_block(header: str) -> str:
    start = header.index('<div class="ds-frozen">')
    depth, i = 0, start
    for m in re.finditer(r"<div\b|</div>", header[start:]):
        depth += 1 if m.group(0) == "<div" else -1
        if depth == 0:
            i = start + m.end()
            break
    return header[start:i]


def _web_text(block: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", block)).split())


def test_web_every_watch_page_prints_its_line_in_the_header_e2e() -> None:
    """In the page header — above the tier tabs, outside every <details> — so the collapsed page,
    the force-opened one and both PDF scopes (the header prints in each) carry it; and its words
    are the md line's, from the same roster and defect file."""
    pages = _web_committed()
    for t in WATCH:
        header, rest = pages[t]["header"], pages[t]["rest"]
        assert header.count('<div class="ds-frozen">') == 1, f"{t}: no watch line in the header"
        assert "ds-frozen" not in rest, f"{t}: a watch line below the header"
        assert "<details" not in header, f"{t}: the header holds a <details>"
        assert _web_text(_frozen_block(header)) == " ".join(_md_text(_md(t)).split()), (
            f"{t}: the web line and the md line say different things")


def test_web_no_active_page_prints_a_watch_line_e2e() -> None:
    pages = _web_committed()
    for t in ACTIVE:
        assert "ds-frozen" not in pages[t]["header"] + pages[t]["rest"], (
            f"{t}: an active page prints a watch line")


def test_web_a_roster_that_did_not_load_is_said_never_silence() -> None:
    """NEGATIVE: with no coverage table the page cannot tell a watch page from an active one, so
    it says the roster did not load — on every page — rather than print nothing."""
    pages = _web(None, ("UBER", "SMPL"))
    for t in ("UBER", "SMPL"):
        assert 'class="ds-frozen ds-frozen-unknown"' in pages[t]["header"]
        assert '<div class="ds-frozen">' not in pages[t]["header"]
