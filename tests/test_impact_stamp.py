"""The impact report's stamp and the re-sync rule (`vinci.impact.stamp.still_valid`), on a real
git history built in a temporary folder, and the static import graph on the committed tree."""
from __future__ import annotations

import pathlib
import subprocess

from vinci.impact import graph as ig
from vinci.impact import stamp as st

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def _commit(repo: pathlib.Path, files: dict[str, str], msg: str) -> str:
    for rel, text in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


def _repo(tmp: pathlib.Path) -> tuple[pathlib.Path, str, str]:
    """main with two modules; a PR branch that edits one of them and STATE.md."""
    repo = tmp / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    lines = "\n".join(f"x{i} = {i}" for i in range(40))
    base = _commit(repo, {"vinci/a.py": lines + "\n", "vinci/b.py": "y = 1\n",
                          "STATE.md": "s\n"}, "base")
    _git(repo, "checkout", "-q", "-b", "pr")
    head = _commit(repo, {"vinci/a.py": lines.replace("x39 = 39", "x39 = 390") + "\n",
                          "STATE.md": "s\nrow\n"}, "fix")
    return repo, base, head


def _stamp(repo: pathlib.Path, base: str, head: str) -> dict[str, object]:
    return {"base": {"sha": st.sha(repo, base)}, "head": {"sha": st.sha(repo, head)},
            "diff_identity": st.diff_identity(repo, base, head)}


def test_the_identity_covers_behaviour_paths_only(tmp_path: pathlib.Path) -> None:
    repo, base, head = _repo(tmp_path)
    ident = st.diff_identity(repo, base, head)
    assert ident["paths"] == ["vinci/a.py"]
    assert ident["all_paths"] == ["STATE.md", "vinci/a.py"]
    assert ident["patch_id"]


def test_a_resync_merging_main_elsewhere_keeps_the_report(tmp_path: pathlib.Path) -> None:
    repo, base, head = _repo(tmp_path)
    stamp = _stamp(repo, base, head)
    _git(repo, "checkout", "-q", "main")
    main2 = _commit(repo, {"vinci/b.py": "y = 2\n", "STATE.md": "t\n"}, "main moves")
    _git(repo, "checkout", "-q", "pr")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "merge", "-q", "-X", "ours",
         "--no-edit", "main")
    res = st.still_valid(repo, stamp, base=main2, head="HEAD")
    assert res.valid, res.reasons


def test_main_editing_a_file_the_pr_changes_needs_a_rerun(tmp_path: pathlib.Path) -> None:
    """Even when the merge is clean and the PR's own hunk is untouched (so its patch-id is the
    same), a file both sides edited can interact: re-run."""
    repo, base, head = _repo(tmp_path)
    stamp = _stamp(repo, base, head)
    _git(repo, "checkout", "-q", "main")
    text = (repo / "vinci/a.py").read_text().replace("x0 = 0", "x0 = -1")
    main2 = _commit(repo, {"vinci/a.py": text}, "main edits a.py far from the PR's hunk")
    _git(repo, "checkout", "-q", "pr")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "merge", "-q", "--no-edit", "main")
    now = st.diff_identity(repo, main2, "HEAD")
    assert now["patch_id"] == stamp["diff_identity"]["patch_id"]   # type: ignore[index]
    res = st.still_valid(repo, stamp, base=main2, head="HEAD")
    assert not res.valid
    assert "main changed 1 file(s) the PR also changes" in res.reasons[0]


def test_a_new_commit_of_the_prs_code_needs_a_rerun(tmp_path: pathlib.Path) -> None:
    repo, base, head = _repo(tmp_path)
    stamp = _stamp(repo, base, head)
    _commit(repo, {"vinci/b.py": "y = 3\n"}, "more code")
    res = st.still_valid(repo, stamp, base=base, head="HEAD")
    assert not res.valid and "diff identity moved" in res.reasons[0]


def test_a_bookkeeping_commit_keeps_the_report(tmp_path: pathlib.Path) -> None:
    repo, base, head = _repo(tmp_path)
    stamp = _stamp(repo, base, head)
    _commit(repo, {"STATE.md": "s\nrow\nmore\n", "docs/records/x.md": "r\n"}, "bookkeeping")
    assert st.still_valid(repo, stamp, base=base, head="HEAD").valid


def test_the_import_graph_sees_function_level_and_relative_imports() -> None:
    graph = ig.import_graph(ROOT)
    # `prespend` imports `assemble` inside its functions only
    assert "vinci.dossier.assemble" in graph["vinci.dossier.prespend"]
    assert "vinci.dossier.prespend" in ig.direct_importers(graph, "vinci.impact.values")
    assert ig.module_of("vinci/dossier/__init__.py") == "vinci.dossier"
    assert ig.module_of("tests/test_x.py") is None
    # the screen does not read the release parser; the dossier does
    screens = ig.closure(graph, [m for m in graph if m.startswith("vinci.screens")])
    assert "vinci.edgar.release_parse" not in screens
    assert "vinci.dossier.mechanical" in ig.importers(graph, ["vinci.edgar.release_parse"])
