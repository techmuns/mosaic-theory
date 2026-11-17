"""A FROZEN CUT IS THE COMMITTED PAGES, BYTE FOR BYTE (W27 follow-up, STATE row 41 (a)).

A value pin moved off a living page trusts its frozen copy in place of that page. The trust holds
only because the copy IS a committed page. So every file under
`tests/fixtures/frozen_pages/cut-<sha8>/<T>/` must equal `data/dossiers/<T>/<file>` at the commit
its folder names: the same git blob. This test refuses:

- a copy hand-edited to make a pin pass;
- a copy cut from a working tree that was never committed;
- a file the page never had;
- a cut whose commit is unknown.

Each cut is also headed. Its row in the frozen-pages README names it. Its own `README.md` lists
every copy with its two blobs, and the list must match the copies exactly.

CI checks out the whole history (`fetch-depth: 0`, gate.yml), so `git cat-file` reads any commit. A
checkout without the commit FAILS here. It never skips: a cut no check can read is not trusted.

CORPUS BEFORE SYNTHETIC: the first pin runs on the committed cut and must check every file in it.
The negatives then show the check firing on the real bytes, edited.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.frozen_support import CUT, CUT_SHA, FROZEN_PAGES, ROOT

_ROW = re.compile(r"^\| (?P<t>[A-Z][A-Z0-9.\-]*) \|.*\| `(?P<json>[0-9a-f]{40})` \| "
                  r"`(?P<md>[0-9a-f]{40})` \|$")


def _git(*args: str, stdin: str | None = None) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, input=stdin, capture_output=True, text=True,
                          check=True).stdout


def _blob_of(paths: list[Path]) -> dict[Path, str]:
    out = _git("hash-object", "--stdin-paths", stdin="".join(f"{p}\n" for p in paths))
    return dict(zip(paths, out.split(), strict=True))


def cut_problems(frozen_root: Path) -> tuple[list[str], int]:
    """(every way a cut under ``frozen_root`` is not its commit's pages, files checked)."""
    problems: list[str] = []
    checked = 0
    for cut in sorted(frozen_root.glob("cut-*")):
        sha8 = cut.name.removeprefix("cut-")
        try:
            sha = _git("rev-parse", "--verify", "--quiet", f"{sha8}^{{commit}}").strip()
        except subprocess.CalledProcessError:
            problems.append(f"{cut.name}: no commit {sha8} in this checkout")
            continue
        files = sorted(p for p in cut.rglob("*") if p.is_file())
        stray = [p for p in files if p.parent == cut and p.name != "README.md"]
        problems += [f"{p.relative_to(frozen_root)}: a cut holds only page folders and its "
                     f"README" for p in stray]
        pages = [p for p in files if p.parent != cut]
        want = {p: f"{sha}:data/dossiers/{p.relative_to(cut).as_posix()}" for p in pages}
        batch = _git("cat-file", "--batch-check=%(objectname) %(objecttype)",
                     stdin="".join(f"{v}\n" for v in want.values())).splitlines()
        have = _blob_of(pages) if pages else {}
        for (p, spec), line in zip(want.items(), batch, strict=True):
            checked += 1
            if line.endswith(" missing") or not line.endswith(" blob"):
                problems.append(f"{p.relative_to(frozen_root)}: not a page file at {sha8} "
                                f"({spec})")
            elif line.split()[0] != have[p]:
                problems.append(f"{p.relative_to(frozen_root)}: differs from {spec} (blob "
                                f"{have[p][:12]} vs committed {line.split()[0][:12]})")
        problems += _header_problems(cut, frozen_root, have)
    return problems, checked


def _header_problems(cut: Path, frozen_root: Path, have: dict[Path, str]) -> list[str]:
    out: list[str] = []
    top = frozen_root / "README.md"
    if f"| `{cut.name}/` |" not in (top.read_text() if top.exists() else ""):
        out.append(f"{cut.name}: no row in {top.name} heading it")
    own = cut / "README.md"
    if not own.exists():
        return [*out, f"{cut.name}: no README.md listing its copies"]
    rows = {m["t"]: (m["json"], m["md"]) for ln in own.read_text().splitlines()
            if (m := _ROW.match(ln))}
    folders = {p.name for p in cut.iterdir() if p.is_dir()}
    out += [f"{cut.name}/{t}: a copy its README does not list" for t in sorted(folders - set(rows))]
    out += [f"{cut.name}: its README lists {t}, which it does not hold"
            for t in sorted(set(rows) - folders)]
    for t in sorted(folders & set(rows)):
        listed = dict(zip(("dossier.json", "dossier.md"), rows[t], strict=True))
        for name, blob in listed.items():
            if have.get(cut / t / name) != blob:
                out.append(f"{cut.name}/{t}/{name}: its README states blob {blob[:12]}, the copy "
                           f"is {str(have.get(cut / t / name))[:12]}")
    return out


def test_every_file_in_every_cut_is_its_commits_page_byte_for_byte() -> None:
    """(+ · the committed cut) Every copy in every cut is the committed page at the cut's commit,
    and every cut is headed. All 52 files of `cut-4889ddba` are checked, so the walk is not
    vacuous."""
    problems, checked = cut_problems(FROZEN_PAGES)
    assert not problems, problems
    assert checked >= len(list(CUT.glob("*/dossier.*"))) == 52, checked


def test_the_cut_is_the_commit_frozen_support_names() -> None:
    """(+) The folder `frozen_support` reads is the cut of its stated commit."""
    assert CUT.name == f"cut-{CUT_SHA[:8]}"
    assert _git("rev-parse", f"{CUT_SHA[:8]}^{{commit}}").strip() == CUT_SHA


def _copy_cut(tmp_path: Path, tickers: tuple[str, ...] = ("SMPL",)) -> Path:
    """A real cut, reduced to ``tickers``, under a frozen root in ``tmp_path``, with both
    headers."""
    root = tmp_path / "frozen_pages"
    cut = root / CUT.name
    for t in tickers:
        shutil.copytree(CUT / t, cut / t)
    rows = [ln for ln in (CUT / "README.md").read_text().splitlines()
            if not (m := _ROW.match(ln)) or m["t"] in tickers]
    (cut / "README.md").write_text("\n".join(rows) + "\n")
    shutil.copy(FROZEN_PAGES / "README.md", root / "README.md")
    return cut


def test_an_unedited_copy_of_a_real_cut_passes(tmp_path: Path) -> None:
    """(+ · control) The tmp copy the negatives edit passes as it stands, so each negative's
    failure is its edit's."""
    _copy_cut(tmp_path, ("SMPL", "AMZN"))
    assert cut_problems(tmp_path / "frozen_pages") == ([], 4)


def test_a_one_byte_edit_to_a_copy_is_refused(tmp_path: Path) -> None:
    """(−) A copy edited by one byte, the shape a re-fitted pin would leave, is not the page."""
    cut = _copy_cut(tmp_path)
    page = cut / "SMPL" / "dossier.json"
    raw = bytearray(page.read_bytes())
    raw[-2] = ord(" ") if raw[-2] != ord(" ") else ord("\t")
    page.write_bytes(bytes(raw))
    problems, _ = cut_problems(tmp_path / "frozen_pages")
    assert any(p.startswith(f"{CUT.name}/SMPL/dossier.json: differs from") for p in problems), \
        problems
    assert any("its README states blob" in p for p in problems), problems


def test_a_file_the_page_never_had_is_refused(tmp_path: Path) -> None:
    """(−) A file the committed page folder did not hold is not part of a cut."""
    cut = _copy_cut(tmp_path)
    (cut / "SMPL" / "notes.json").write_text("{}\n")
    problems, _ = cut_problems(tmp_path / "frozen_pages")
    assert any("SMPL/notes.json: not a page file at 4889ddba" in p for p in problems), problems


def test_a_cut_of_an_unknown_commit_is_refused(tmp_path: Path) -> None:
    """(−) A folder named for no commit is a working-tree copy, never a cut."""
    cut = _copy_cut(tmp_path)
    cut.rename(cut.with_name("cut-0000dead"))
    problems, _ = cut_problems(tmp_path / "frozen_pages")
    assert problems == ["cut-0000dead: no commit 0000dead in this checkout"], problems


def test_a_cut_its_readmes_do_not_head_is_refused(tmp_path: Path) -> None:
    """(−) A cut with no row in the frozen-pages README, or a copy its own README does not list,
    is unheaded."""
    cut = _copy_cut(tmp_path, ("SMPL", "AMZN"))
    top = tmp_path / "frozen_pages" / "README.md"
    top.write_text(top.read_text().replace(f"| `{CUT.name}/` |", "| `elsewhere/` |"))
    own = cut / "README.md"
    own.write_text("\n".join(ln for ln in own.read_text().splitlines()
                             if not ln.startswith("| AMZN |")) + "\n")
    problems, _ = cut_problems(tmp_path / "frozen_pages")
    assert f"{CUT.name}: no row in README.md heading it" in problems, problems
    assert f"{CUT.name}/AMZN: a copy its README does not list" in problems, problems


@pytest.mark.parametrize("ticker", ["SMPL", "AMZN"])
def test_frozen_support_reads_the_cut_and_never_the_living_page(ticker: str) -> None:
    """(+ / −) `frozen_page` returns the cut's folder, and a name the cut lacks raises: it never
    falls back to `data/dossiers/`."""
    from tests.frozen_support import frozen_doc, frozen_page

    assert frozen_page(ticker) == CUT / ticker
    assert frozen_doc(ticker)["ticker"] == ticker
    with pytest.raises(FileNotFoundError, match="no frozen copy of ZZZZ"):
        frozen_page("ZZZZ")
