"""ONE FILE PER EXTRACTION VINTAGE, AND CURRENT IS THE HEAD (2026-11-11, fix request 2).

THE CHURN THIS ENDS. Every PR that changed extraction output appended a row at the END of one tuple
(`vinci/dossier/extraction_version.py`) and of its hand-kept web twin, and re-pinned a shared block
of drift hashes, so each merge sent every other such PR DIRTY on the same lines and each re-sync
cost a 30–80 minute re-gate. A vintage is now a file in `vinci/dossier/extraction_versions/`; the
old rows are frozen; the web reads a table `frontend/build.py` writes at deploy.

WHAT CANNOT MOVE. Every id a committed page carries stays byte-identical, and so does what
`stamp_label` / `stamp_detail` print for it — pinned here on the frozen table's digest, and on the
27 committed pages by the PR's own verify run.

WHY ANCESTRY AND NOT A SORT. Replayed in real merge order, 45 of the frozen table's 76 appends
would have left a date-sorted "current" where it stood, the stamp standing still while the code
moved. So a vintage names what it `follows`, current is the heads, and two vintages merged in
parallel stamp as their join — each pinned below, positive and negative.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

from tests.test_extraction_version import _web_table
from vinci.dossier import extraction_version as ev

ROOT = Path(__file__).resolve().parents[1]
#: The last frozen row — what the first vintage file follows.
P = ev.LEGACY_VERSIONS[-1][0]
_NAMES = "a vintage written for this test, which names more than twenty characters"


def _entry(d: Path, vid: str, follows: list[str], names: str = _NAMES, **extra: object) -> Path:
    path = d / f"{vid}.json"
    path.write_text(json.dumps({"id": vid, "follows": follows, "names": names, **extra}))
    return path


def _use(monkeypatch: pytest.MonkeyPatch, d: Path, *, with_tree: bool = False) -> tuple[str, ...]:
    """Point the stamp helpers at the frozen table plus the vintage files in ``d`` — and, with
    ``with_tree``, the tree's own vintage files too (what a file `new` writes here follows)."""
    entries = ev.read_entries(d) + (ev.read_entries() if with_tree else [])
    table, parents = ev.build_table(ev.LEGACY_VERSIONS, entries)
    monkeypatch.setattr(ev, "_NAMES", dict(table))
    monkeypatch.setattr(ev, "_PARENTS", parents)
    return ev.heads_of(parents)


# --- the frozen rows -----------------------------------------------------------------------------

def test_the_frozen_rows_never_change() -> None:
    """VALUE PIN ON A FROZEN LITERAL. The 77 rows a committed page may name were frozen at
    `2026-11-11.guides-as-stated`; this digest is theirs at the commit that froze them, so an edit
    to any row — id or words — reds here, where the old table relied on review alone."""
    digest = hashlib.sha256(json.dumps(ev.LEGACY_VERSIONS).encode()).hexdigest()[:16]
    assert (len(ev.LEGACY_VERSIONS), P, digest) == (77, "2026-11-11.guides-as-stated",
                                                    "6bda33aa663b55ac")


def test_the_frozen_rows_alone_are_the_table_as_it_was() -> None:
    """The migration moves nothing: with no vintage file, the table, its one head and what that
    head names are the frozen rows' own — the last row current, exactly as before the split."""
    table, parents = ev.build_table(ev.LEGACY_VERSIONS, [])
    assert table == ev.LEGACY_VERSIONS
    assert ev.heads_of(parents) == (P,)
    assert all(parents[v] == ((prev,) if prev else ()) for (v, _), prev in
               zip(table, [None, *(v for v, _ in table[:-1])], strict=True))


# --- a vintage file -------------------------------------------------------------------------------

def test_new_writes_one_file_following_every_head(tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """The one step a PR takes: a file named for its id, following the heads of the tree it was
    written in — and on reading it back, it is the one head."""
    path = ev.new_entry("an-example", _NAMES, on=date(2026, 11, 12), directory=tmp_path)
    assert path.name == "2026-11-12.an-example.json"
    assert json.loads(path.read_text()) == {
        "id": "2026-11-12.an-example", "follows": list(ev.HEADS), "names": _NAMES}
    assert _use(monkeypatch, tmp_path, with_tree=True) == ("2026-11-12.an-example",)


def test_new_refuses_a_counter_an_existing_id_and_an_existing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="holding a letter"):
        ev.new_entry("2", _NAMES, on=date(2026, 11, 12), directory=tmp_path)
    with pytest.raises(ValueError, match="already a declared vintage"):
        ev.new_entry("guides-as-stated", _NAMES, on=date(2026, 11, 11), directory=tmp_path)
    ev.new_entry("once", _NAMES, on=date(2026, 11, 12), directory=tmp_path)
    with pytest.raises(FileExistsError):
        ev.new_entry("once", _NAMES, on=date(2026, 11, 12), directory=tmp_path)


def test_new_refuses_a_short_names_and_leaves_no_file_when_the_read_back_fails(
        tmp_path: Path) -> None:
    """`new` holds the suite's twenty-character floor on `names`, and a file that does not read
    back (a malformed sibling in the folder) is removed again — nothing lands, as it says."""
    with pytest.raises(ValueError, match="more than twenty characters"):
        ev.new_entry("short", "too short", on=date(2026, 11, 12), directory=tmp_path)
    assert not list(tmp_path.iterdir())
    (tmp_path / "2026-11-12.stray 2.json").write_text("{}")
    with pytest.raises(ValueError, match="stray 2.json"):
        ev.new_entry("lands", _NAMES, on=date(2026, 11, 12), directory=tmp_path)
    assert not (tmp_path / "2026-11-12.lands.json").exists()


@pytest.mark.parametrize(("name", "body", "why"), [
    ("2026-11-12.2.json", {"id": "2026-11-12.2", "follows": [P], "names": _NAMES},
     "holding a letter"),
    ("2026-11-12.Mixed-Case.json", {"id": "2026-11-12.Mixed-Case", "follows": [P],
                                    "names": _NAMES}, "lowercase"),
    ("2026-13-01.bad-month.json", {"id": "2026-13-01.bad-month", "follows": [P],
                                   "names": _NAMES}, "real date"),
    ("2026-11-12.other.json", {"id": "2026-11-12.renamed", "follows": [P], "names": _NAMES},
     "named 2026-11-12.renamed.json"),
    ("2026-11-12.a 2.json", {"id": "2026-11-12.a", "follows": [P], "names": _NAMES},
     "named 2026-11-12.a.json"),
    ("2026-10-30.zero-coercion.json", {"id": "2026-10-30.zero-coercion", "follows": [P],
                                       "names": _NAMES}, "frozen table"),
    ("2026-11-12.typo.json", {"id": "2026-11-12.typo", "follow": [P], "names": _NAMES}, "keys"),
    ("2026-11-12.extra.json", {"id": "2026-11-12.extra", "follows": [P], "names": _NAMES,
                               "current": True}, "keys"),
    ("2026-11-12.orphan.json", {"id": "2026-11-12.orphan", "follows": [], "names": _NAMES},
     "follows must list"),
    ("2026-11-12.twice.json", {"id": "2026-11-12.twice", "follows": [P, P], "names": _NAMES},
     "follows must list"),
    ("2026-11-12.silent.json", {"id": "2026-11-12.silent", "follows": [P], "names": "  "},
     "names must say"),
    ("2026-11-12.note.json", {"id": "2026-11-12.note", "follows": [P], "names": _NAMES,
                              "note": 3}, "a note is text"),
])
def test_a_malformed_vintage_file_is_refused_by_name(tmp_path: Path, name: str,
                                                     body: dict[str, object], why: str) -> None:
    """NEGATIVE PINS, one per fault: each stops the read with the file's name and the reason —
    never a skip, which would stamp pages as if the vintage did not exist."""
    (tmp_path / name).write_text(json.dumps(body))
    with pytest.raises(ValueError) as err:
        ev.read_entries(tmp_path)
    assert why in str(err.value) and name in str(err.value)


def test_a_file_that_is_not_json_or_a_missing_folder_is_refused(tmp_path: Path) -> None:
    (tmp_path / "2026-11-12.broken.json").write_text("{not json")
    with pytest.raises(ValueError, match="not JSON"):
        ev.read_entries(tmp_path)
    with pytest.raises(RuntimeError, match="is missing"):
        ev.read_entries(tmp_path / "absent")


def test_the_readme_is_not_an_entry(tmp_path: Path) -> None:
    """POSITIVE PIN beside the negatives: the folder's README and a well-formed file read clean."""
    shutil.copy(ev.ENTRIES_DIR / "README.md", tmp_path / "README.md")
    _entry(tmp_path, "2026-11-12.fine", [P], note="a reader's note")
    assert ev.read_entries(tmp_path) == [("2026-11-12.fine", (P,), _NAMES)]


def test_a_follow_of_nothing_or_a_cycle_is_refused(tmp_path: Path) -> None:
    _entry(tmp_path, "2026-11-12.lost", ["2026-01-01.never-declared"])
    with pytest.raises(ValueError, match="which no vintage declares"):
        ev.build_table(ev.LEGACY_VERSIONS, ev.read_entries(tmp_path))
    for f in tmp_path.iterdir():
        f.unlink()
    _entry(tmp_path, "2026-11-12.a", ["2026-11-12.b"])
    _entry(tmp_path, "2026-11-12.b", ["2026-11-12.a"])
    with pytest.raises(ValueError, match="cycle"):
        ev.build_table(ev.LEGACY_VERSIONS, ev.read_entries(tmp_path))


# --- current is the heads ------------------------------------------------------------------------

def test_two_vintages_cut_from_one_main_stamp_as_their_join(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Two PRs cut from the same main each add a file following its head. Merged, in either order,
    the tree is the same two files — and the stamp is their join, naming both, never the one a
    sort happens to put last. The next vintage written there follows both and the join closes."""
    a, b = "2026-11-13.zeta-earlier-merged", "2026-11-12.alpha-later-merged"
    _entry(tmp_path, a, [P])
    _entry(tmp_path, b, [P])
    assert _use(monkeypatch, tmp_path) == (b, a)  # id order, whatever the merge order was
    joined = f"{b}+{a}"
    assert ev.declares(joined) and not ev.declares(a + "+" + b)
    assert ev.stamp_detail(joined) == (
        f"{joined} — vintages merged in parallel, none following another: [{b}] {_NAMES} "
        f"[{a}] {_NAMES}")
    _entry(tmp_path, "2026-11-14.after-both", [b, a])
    assert _use(monkeypatch, tmp_path) == ("2026-11-14.after-both",)
    table, _ = ev.build_table(ev.LEGACY_VERSIONS, ev.read_entries(tmp_path))
    assert [v for v, _ in table][-3:] == [b, a, "2026-11-14.after-both"]


def test_a_join_is_declared_only_as_a_set_of_heads(tmp_path: Path,
                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE PINS for the join: parts out of order, a part twice, a part an ancestor of
    another, or a part no vintage declares — none is a stamp the code can produce."""
    a, b = "2026-11-12.a", "2026-11-12.b"
    _entry(tmp_path, a, [P])
    _entry(tmp_path, b, [P])
    _use(monkeypatch, tmp_path)
    for bad in (f"{b}+{a}", f"{a}+{a}", f"{P}+{a}", f"{a}+1999-01-01.0", "+", f"{a}+"):
        assert not ev.declares(bad), bad
        assert ev.stamp_detail(bad).endswith("not a version this code declares; built by a "
                                             "different extractor"), bad
    assert ev.declares(f"{a}+{b}")


def test_includes_reads_ancestry_never_a_position(tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """What a stamp's code HOLDS: every vintage it follows, transitively, through each part of a
    join; unknown for a stamp the code does not declare, never "no"."""
    a, b = "2026-11-12.a", "2026-11-12.b"
    _entry(tmp_path, a, [P])
    _entry(tmp_path, b, [P])
    _use(monkeypatch, tmp_path)
    assert ev.includes(f"{a}+{b}", a) and ev.includes(f"{a}+{b}", "2026-07-28.1")
    assert ev.includes(a, b) is False and ev.includes(P, a) is False
    assert ev.includes("2026-11-04.footnote-every-figure", "2026-10-29.A-D14") is True
    assert ev.includes("2026-10-29.A-D14", "2026-11-04.footnote-every-figure") is False
    assert ev.includes("1999-01-01.0", P) is None and ev.includes(None, P) is None
    with pytest.raises(ValueError):
        ev.includes(a, "2099-01-01.never")


# --- the web reads the same table ----------------------------------------------------------------

def test_both_twins_agree_on_a_joined_stamp_e2e(tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    """The python helpers and the web's, on the table build.py writes from the same files: every
    join shape, good and bad, and the deploy that did not emit the table at all — which the web
    must SAY, never call 'not a version this code declares'."""
    if not shutil.which("node"):
        pytest.skip("node not available")
    a, b = "2026-11-12.a", "2026-11-12.b"
    _entry(tmp_path, a, [P])
    _entry(tmp_path, b, [P])
    _use(monkeypatch, tmp_path)
    table = _web_table(tmp_path)
    cases = [a, b, f"{a}+{b}", f"{b}+{a}", f"{a}+{a}", f"{P}+{a}", f"{a}+1999-01-01.0", P,
             "2026-07-28.1", "", None]
    dj = (ROOT / "frontend" / "views" / "shared" / "dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
const {{ renderDossier, useExtractionVersions }} = await import("{dj}");
const bare = {{ ticker: "X", name: "X Co", cik: "0", reference_date: "2026-06-01",
  assembled_at: "2026-06-01T12:00:00", mechanical: {{}}, synthesis: null }};
const strip = (s) => s.replace(/<[^>]*>/g, "").replace(/&amp;/g, "&").replace(/&#39;/g, "'")
  .replace(/&quot;/g, '"').replace(/&lt;/g, "<").replace(/&gt;/g, ">").trim();
const row = /"fact-label">Extraction<\\/div>\\s*<div class="fact-val">([\\s\\S]*?)<\\/div>/;
const detail = (html) => strip(row.exec(html)[1]);
useExtractionVersions({json.dumps(table)});
const out = {json.dumps(cases)}.map((v) => detail(renderDossier(
  v === null ? bare : {{ ...bare, extraction_version: v }}, null)));
useExtractionVersions(null);  // a deploy that did not emit the table
out.push(detail(renderDossier({{ ...bare, extraction_version: "{a}" }}, null)));
console.log(JSON.stringify(out));
"""
    got = json.loads(subprocess.run(["node", "--input-type=module", "-e", driver],
                                    capture_output=True, text=True, check=True, cwd=ROOT).stdout)
    assert got[:-1] == [ev.stamp_detail(v) for v in cases]
    assert got[-1] == (f"{a} — the extraction-version table did not load in this deploy, so what "
                       "this version names is not shown")
