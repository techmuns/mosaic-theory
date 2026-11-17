"""THE WATCH LINE (STATE row 41 (b); B's design, issue #1004 comment 6847522000 item 6; the
operator's marking, comment 6847554747, 2026-11-13, "go ahead").

A watch page is kept as committed with no paid rebuild until its name goes active, so it says so
near its top, on both surfaces: the move's date and ruling from the coverage roster, and the known
defects it keeps until then, from `data/watch_defects.json`. The line is read from the roster at
RENDER time (md) and at DEPLOY time (web, `snapshots/coverage.json`), never stored in the page, so
a move to active removes it at the next render with no page edit.

TWO KINDS OF PIN, so the feature's own lifecycle never reddens the suite (A's review of #1100):
- THE COMMITTED TREE: every pin walks the names the roster itself lists as watch or active, and
  the entries the defect file itself holds — never a count, a name or an entry written here. A
  name moved to active, or an entry removed once its page moves past it, changes what they walk,
  never whether they can run.
- THE LIFECYCLE AND THE GUARDS: a synthetic data tree around ONE FROZEN PAGE
  (`tests/fixtures/frozen_pages/2026-11-09/UBER`, never regenerated), with a roster line and a
  defect written here. Value pins live there only.

The anchors are the roster's and the defect file's own text, composed by `WatchNotice` —
committed data, not an LLM's words.
"""
from __future__ import annotations

import copy
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
from vinci.dossier import refresh
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


def _watching() -> list[str]:
    if not WATCH:
        pytest.skip("no name is on watch on the committed roster: no page prints the line")
    return WATCH


def _notice(t: str, data: Path = DATA) -> roster.WatchNotice:
    n = roster.watch_notice(data, t, _page(t, data / "dossiers"))
    assert n is not None, f"{t} is on watch and has no notice"
    return n


def _as_watch(t: str) -> roster.WatchNotice:
    """The notice an ACTIVE name WOULD print were it on watch — what its page must not carry."""
    m = LATEST[t]
    return roster.WatchNotice(move=roster.Move(date=m.date, ticker=t, status="watch",
                                               ruling=m.ruling, source=m.source,
                                               record=m.record), defects=())


def _frozen_markers(t: str) -> tuple[str, ...]:
    """What a watch line prints whatever its move's date: an active page carries neither, so a
    stale line left from an earlier watch move is caught, not only one dated as the active move."""
    return (f"{t} is on watch.", _as_watch(t).kept())


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


def test_the_committed_pins_walk_the_rosters_own_lists() -> None:
    """Non-vacuous and lifecycle-proof: the pins below walk every name the roster lists as watch
    or active, each of which has a committed page — so a move changes the lists they walk, never
    whether they run. (The first cut asserted the marking's 15 and 11.)"""
    assert WATCH or ACTIVE, "the roster lists no watch or active name"
    assert set(WATCH) | set(ACTIVE) <= set(roster.covered_pages(DATA))
    assert all((DOSS / t / "dossier.json").is_file() for t in WATCH + ACTIVE)


# --- md, end to end: committed JSON + the committed roster → render_markdown ------------------


def test_md_every_watch_page_prints_its_line_above_the_brief_e2e() -> None:
    for t in _watching():
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
        md = _md(t)
        assert not any(m in md for m in _frozen_markers(t)), f"{t}: an active page prints the line"
        assert _as_watch(t).defects_head() not in md


def test_the_committed_md_and_its_web_mirror_carry_the_line_e2e() -> None:
    """The artifact pass happened: each committed watch page's md, and its served mirror, carry
    the line the renderer prints today; no active page's carries one, whatever date it names."""
    for t in WATCH:
        n = _notice(t)
        for path in (DOSS / t / "dossier.md", ROOT / "frontend" / "dossiers" / f"{t}.md"):
            assert n.head() in path.read_text(), f"{path}: the watch line is not committed"
    for t in ACTIVE:
        for path in (DOSS / t / "dossier.md", ROOT / "frontend" / "dossiers" / f"{t}.md"):
            text = path.read_text()
            assert not any(m in text for m in _frozen_markers(t)), f"{path}: carries a watch line"


# --- the defect file: its citations resolve, and every defect is on its page --------------------


def _listed() -> dict[str, tuple[roster.Defect, ...]]:
    defects = roster.read_defects(DATA)
    if not defects:
        pytest.skip("the committed defect file lists no defect: no citation to resolve")
    return defects


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
    rows = _open_rows()
    assert len(rows) >= 10, f"read only {len(rows)} §5.0 rows — the table moved"
    for t, ds in _listed().items():
        for x in ds:
            assert x.state_row in rows, f"{t}: STATE row {x.state_row} is not an open §5.0 row"
            assert (ROOT / x.record).is_file(), f"{t}: {x.record} does not exist"


def test_every_defect_is_on_its_page_and_listed_for_a_covered_name() -> None:
    """Each defect's page field still holds the value it was measured at, on the committed page,
    and its name is on watch or active. A rebuild or refresh that fixes one is refused at its
    render until the entry is removed; this holds every committed page to the same."""
    defects = roster.read_defects(DATA)
    pages = {t: _page(t) for t in defects if (DOSS / t / "dossier.json").is_file()}
    assert set(pages) == set(defects), "a defect is listed for a name with no committed page"
    assert roster.defect_problems(LATEST, defects, pages) == []


def test_the_committed_defect_file_reads() -> None:
    """POSITIVE: the committed file passes every check below."""
    assert roster.render_defects(roster.read_defects(DATA)) == (DATA / roster.DEFECTS_NAME
                                                                ).read_text()


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


# --- a synthetic tree around one FROZEN page: the lifecycle and the guards ----------------------

FROZEN = ROOT / "tests" / "fixtures" / "frozen_pages" / "2026-11-09"
SUBJECT = "UBER"            # frozen there, assembled 2026-11-09: NOT priceable on R4
CONFLICT = "/valuation_basis/conflicts/0"
CONFLICT_HOLDS = ("the bridge (5356.0) disagrees with CIQ's TEV less market cap (8973.0) by "
                  "more than 0.5 ($M)")
ROW = "/mechanical/capital_structure/covenant_term_rows/value/0/name"   # a field a refresh moves
ROW_HOLDS = "Conversion price / mechanics"
_ENTRY: dict[str, Any] = {
    "defect": "Its R4 valuation is not priceable: a test's defect", "state_row": 28,
    "record": "docs/records/2026-11-12-rebuild-prep-prechecks-on-all-27-pages.md",
    "page_field": CONFLICT, "page_value": CONFLICT_HOLDS, "measured": "a frozen fixture"}


def _line(t: str, status: str, when: str) -> str:
    return roster.render_line(roster.Move(date=date.fromisoformat(when), ticker=t,
                                          status=status, ruling=f"a test's {status}",
                                          source="a test", record=None)) + "\n"


WATCHED = _line(SUBJECT, "watch", "2026-11-13")


def _defects(**by_name: list[dict[str, Any]]) -> str:
    return json.dumps(dict(sorted(by_name.items())), indent=2, ensure_ascii=False) + "\n"


def _one(**change: Any) -> str:
    return _defects(**{SUBJECT: [dict(_ENTRY, **change)]})


def _tree(tmp_path: Path, *, moves: str = WATCHED, defects: str | None = None) -> Path:
    """A data dir: the frozen page, the roster ``moves`` and the defect file ``defects`` (absent
    when None; the synthetic entry by default)."""
    data = tmp_path / "data"
    (data / "dossiers" / SUBJECT).mkdir(parents=True)
    shutil.copy(FROZEN / SUBJECT / "dossier.json", data / "dossiers" / SUBJECT / "dossier.json")
    (data / roster.ROSTER_NAME).write_text(moves, encoding="utf-8")
    (data / roster.DEFECTS_NAME).write_text(_one() if defects is None else defects,
                                            encoding="utf-8")
    return data


def _render(data: Path) -> str:
    d = Dossier.model_validate_json((data / "dossiers" / SUBJECT / "dossier.json").read_text())
    return render_markdown(d, dossiers_root=data / "dossiers")


def _sentence(entry: dict[str, Any] = _ENTRY) -> str:
    return roster.Defect(**entry).sentence()


def _deploy(build: ModuleType, data: Path, monkeypatch: Any) -> dict[str, Any]:
    monkeypatch.setattr(build, "DOSS", data / "dossiers")
    monkeypatch.setattr(build, "COVERAGE", data / roster.ROSTER_NAME)
    monkeypatch.setattr(build, "WATCH_DEFECTS", data / roster.DEFECTS_NAME)
    out: dict[str, Any] = build._coverage_snapshot([SUBJECT])
    return out


def test_the_frozen_page_holds_the_synthetic_defects() -> None:
    """The fixture the cases below stand on: the frozen page holds both bound values, read as
    its one writer writes it — so a case that moves one moves it from a known value."""
    page = _page(SUBJECT, FROZEN)
    for pointer, want in ((CONFLICT, CONFLICT_HOLDS), (ROW, ROW_HOLDS)):
        assert roster.page_value(page, pointer) == want, pointer


def test_a_name_moved_to_active_loses_the_line_on_both_surfaces(tmp_path: Path,
                                                                 monkeypatch: Any) -> None:
    before = _tree(tmp_path / "before")
    after = _tree(tmp_path / "after", moves=WATCHED + _line(SUBJECT, "active", "2026-11-17"))
    n = _notice(SUBJECT, before)
    md = _render(before)
    assert n.head() in md and _sentence() in md          # POSITIVE: on watch, it prints
    md = _render(after)
    assert n.head() not in md and n.kept() not in md and n.defects_head() not in md
    assert _sentence() not in md
    # the web: the deploy snapshot from the moved roster, rendered by the production page
    build = _build()
    snap = _deploy(build, after, monkeypatch)
    assert snap["names"][SUBJECT]["status"] == "active" and "defects" not in snap["names"][SUBJECT]
    assert 'class="ds-frozen' not in _web(snap, (SUBJECT,), after / "dossiers")[SUBJECT]["header"]
    shown = _web(_deploy(build, before, monkeypatch), (SUBJECT,), before / "dossiers")
    assert _web_text(_frozen_block(shown[SUBJECT]["header"])) == " ".join(
        _md_text(_render(before)).split())


def _move_row(page: dict[str, Any], change: str) -> None:
    rows = page["mechanical"]["capital_structure"]["covenant_term_rows"]["value"]
    if change == "moved":
        rows[0]["name"] = f"{rows[0]['name']} (moved)"
    else:
        rows.clear()


@pytest.mark.parametrize("change", ["moved", "missing"])
def test_a_defect_its_page_no_longer_holds_is_dropped_at_render_and_refused_at_publish(
        tmp_path: Path, monkeypatch: Any, change: str) -> None:
    """A listed defect whose field the page no longer holds — moved, or gone — is DROPPED by the
    renderer, which stays side-effect free (a fresh $0 build of a watch name, as the cross-setup
    harness renders one, holds none of its committed page's defects: ORKA's reads 93 sells where
    its committed page's bound line reads 98). PUBLISHED, the page would look clean, so the deploy
    refuses it, naming the field, and the suite's check names the entry. POSITIVE: the unchanged
    page prints it on both surfaces. (Operator, 2026-11-17: "Refuse where pages are saved or
    published".)"""
    entry = dict(_ENTRY, page_field=ROW, page_value=ROW_HOLDS)
    data = _tree(tmp_path, defects=_defects(**{SUBJECT: [entry]}))
    assert _sentence(entry) in _render(data)
    build = _build()
    assert [d["defect"] for d in _deploy(build, data, monkeypatch)["names"][SUBJECT]["defects"]] \
        == [entry["defect"]]
    page = _page(SUBJECT, data / "dossiers")
    _move_row(page, change)
    (data / "dossiers" / SUBJECT / "dossier.json").write_text(json.dumps(page, indent=2))
    md = _render(data)
    assert _notice(SUBJECT, data).head() in md and _sentence(entry) not in md
    with pytest.raises(SystemExit, match=re.escape(ROW)):
        _deploy(build, data, monkeypatch)
    problems = roster.defect_problems(roster.current(data), roster.read_defects(data),
                                      {SUBJECT: page})
    assert len(problems) == 1 and ROW in problems[0], problems


def _mover(row: int) -> refresh.Transform:
    def move(mech: dict[str, Any]) -> dict[str, Any]:
        out = copy.deepcopy(mech)
        out["capital_structure"]["covenant_term_rows"]["value"][row]["name"] += " (moved)"
        return out
    return move


def test_a_refresh_that_moves_a_bound_value_saves_nothing(tmp_path: Path,
                                                         monkeypatch: Any) -> None:
    """THE SAVE PATH (`refresh_dossier`): a $0 refresh whose transform moves a watch page's bound
    value is refused, naming the field and the entry to remove, and neither artifact is written;
    `refresh_fleet` reports the page refused and carries on. POSITIVE: a refresh that moves a
    field no defect is bound to saves the page, line and defect included."""
    entry = dict(_ENTRY, page_field=ROW, page_value=ROW_HOLDS)
    data = _tree(tmp_path, defects=_defects(**{SUBJECT: [entry]}))
    path = data / "dossiers" / SUBJECT / "dossier.json"
    assert refresh.refresh_dossier(path, transform=_mover(1)) is True
    assert _sentence(entry) in (path.parent / "dossier.md").read_text()
    before = {p.name: p.read_bytes() for p in path.parent.iterdir()}
    with pytest.raises(refresh.RefreshRefusedError,
                       match=re.escape(ROW) + ".*" + re.escape(roster.DEFECTS_NAME)):
        refresh.refresh_dossier(path, transform=_mover(0))
    assert {p.name: p.read_bytes() for p in path.parent.iterdir()} == before
    monkeypatch.chdir(tmp_path)         # the fleet mirrors from the cwd: there is none here
    out = refresh.refresh_fleet(tmp_path, transform_for=lambda _t: _mover(0))
    assert out["refused"] == [SUBJECT] and out["moved"] == []
    assert {p.name: p.read_bytes() for p in path.parent.iterdir()} == before


def test_a_defect_listed_for_a_retired_or_unlisted_name_is_named_and_breaks_no_other_page(
        tmp_path: Path) -> None:
    """A stale entry (a name retired by one roster line, or never on the roster) is named by the
    suite's check, and stops no other watch page's render — the W27 one-line retirement must
    not take the fleet's renders down with it."""
    for gone, moves in (("ZRTD", WATCHED + _line("ZRTD", "retired", "2026-11-14")),
                        ("ZZZZ", WATCHED)):
        data = _tree(tmp_path / gone, moves=moves, defects=_defects(
            **{SUBJECT: [_ENTRY], gone: [_ENTRY]}))
        assert _sentence() in _render(data)
        problems = roster.defect_problems(roster.current(data), roster.read_defects(data), {})
        assert len(problems) == 1 and problems[0].startswith(gone), problems


def test_a_watch_page_whose_tree_has_no_defect_file_is_refused(tmp_path: Path) -> None:
    """An absent defect file beside a roster is not "no defects": the page would print its line
    as if it kept none. The reader refuses it directly too. POSITIVE: an empty file is "none"."""
    data = _tree(tmp_path / "empty", defects=_defects())
    assert _notice(SUBJECT, data).head() in _render(data)
    assert _sentence() not in _render(data)
    data = _tree(tmp_path / "absent")
    (data / roster.DEFECTS_NAME).unlink()
    with pytest.raises(roster.WatchDefectError, match="no known-defect file"):
        _render(data)
    with pytest.raises(roster.WatchDefectError, match="no known-defect file"):
        roster.read_defects(data)


def test_a_tree_with_no_roster_renders_no_line_and_the_reader_still_refuses(
        tmp_path: Path) -> None:
    """A scratch tree holding no roster (a test's or a probe's copy) renders no line, rather
    than paste the live roster onto a copy built to differ from it. The data tree always holds
    one, and the committed pages are pinned above; the roster's own reader still refuses an
    absent file."""
    data = _tree(tmp_path)
    head = _notice(SUBJECT, data).head()
    (data / roster.ROSTER_NAME).unlink()
    assert head not in _render(data)
    with pytest.raises(roster.CoverageRosterError, match="no coverage roster"):
        roster.watch_notice(data, SUBJECT, _page(SUBJECT, data / "dossiers"))


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


def test_the_deploy_snapshot_refuses_without_the_defect_file(tmp_path: Path,
                                                            monkeypatch: Any) -> None:
    data = _tree(tmp_path)
    (data / roster.DEFECTS_NAME).unlink()
    with pytest.raises(SystemExit, match="no known-defect file"):
        _deploy(_build(), data, monkeypatch)


@pytest.mark.parametrize("fault", ["absent", "not JSON", "not held"])
def test_a_deploy_the_defect_file_stops_leaves_the_served_mirror_as_it_was(
        tmp_path: Path, monkeypatch: Any, fault: str) -> None:
    """W27's order, check before wipe, holds for the defect file too: a deploy it stops leaves
    the served `frontend/dossiers` and `frontend/snapshots` as they were. (The first cut built
    the coverage snapshot after `shutil.rmtree` of both, so an absent file deleted the mirror.)"""
    data = _tree(tmp_path)
    path = data / roster.DEFECTS_NAME
    if fault == "absent":
        path.unlink()
    elif fault == "not JSON":
        path.write_text("{", encoding="utf-8")
    else:
        path.write_text(_one(page_value="a value the page does not hold"), encoding="utf-8")
    build = _build()
    out_doss, out_snap = tmp_path / "out" / "dossiers", tmp_path / "out" / "snapshots"
    for d in (out_doss, out_snap):
        d.mkdir(parents=True)
        (d / "served.json").write_text("{}")
    # every folder main() writes points into tmp_path, so a build that does NOT stop (the
    # regression this pins) writes nothing in the checkout
    for name, value in (("DOSS", data / "dossiers"), ("COVERAGE", data / roster.ROSTER_NAME),
                        ("WATCH_DEFECTS", path), ("ROOT", tmp_path), ("OUT_DOSS", out_doss),
                        ("OUT_SNAP", out_snap), ("OUT_SCEN", tmp_path / "out" / "scenarios"),
                        ("OUT_MON", tmp_path / "out" / "monitor")):
        monkeypatch.setattr(build, name, value)
    with pytest.raises((SystemExit, ValueError)):
        build.main([])
    assert (out_doss / "served.json").is_file() and (out_snap / "served.json").is_file()


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
  const d = JSON.parse(readFileSync(__DOSS__ + "/" + t + "/dossier.json"));
  const html = renderDossier(d, null, null);
  const tabs = html.indexOf('<div class="ds-tabs"');
  out[t] = { header: html.slice(0, tabs), rest: html.slice(tabs) };
}
console.log(JSON.stringify(out));
"""


def _web(table: dict[str, Any] | None, tickers: tuple[str, ...],
         doss: Path = DOSS) -> dict[str, dict[str, str]]:
    if not shutil.which("node"):
        pytest.skip("node not available")
    driver = (_DRIVER
              .replace("__DJ__", json.dumps((ROOT / "frontend/views/shared/dossier.js").as_uri()))
              .replace("__DOSS__", json.dumps(str(doss)))
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
    for t in _watching():
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


def test_web_a_roster_that_did_not_load_is_said_never_silence(tmp_path: Path) -> None:
    """NEGATIVE: with no coverage table the page cannot tell a watch page from an active one, so
    it says the roster did not load rather than print nothing."""
    data = _tree(tmp_path)
    header = _web(None, (SUBJECT,), data / "dossiers")[SUBJECT]["header"]
    assert 'class="ds-frozen ds-frozen-unknown"' in header
    assert '<div class="ds-frozen">' not in header
