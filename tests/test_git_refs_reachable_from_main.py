"""A TEST MAY EXECUTE A GIT REF ONLY IF MAIN CAN REACH IT (STATE §5.0 row 56; handed over on issue
#1004; `docs/records/2026-11-07-a-test-named-a-squashed-branch-commit.md`).

`tests/test_evals_round2.py` read `4449189d:docs/records/…`, #923's branch head. Its squash merge
left that commit outside every clone's history, so main's `gate` went red at `a9c59287`. Every hex
literal a test or the harness hands to git must be a commit `origin/main` reaches: a branch commit
passes on its own PR and breaks the day the PR is squashed.

WHAT COUNTS AS HANDED TO GIT (the record's list, read from the source, never from a run):
- a ``<sha>:<path>`` string, which `git show` and `git archive` read;
- a hex literal in an argument list whose first item is ``"git"``;
- a hex literal passed as a ref to a function that runs git with it: a ``*_ref`` / ``base`` /
  ``cand`` / ``ref`` keyword, or a positional argument of the harness's ref-taking functions.

Provenance text (docstrings, comments, a record's hash in a dict) is not handed to git and is not
checked. The lint reads no network and draws nothing.
"""
from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HEX = re.compile(r"^[0-9a-f]{7,40}$")
REF_PATH = re.compile(r"(?<![0-9a-f])([0-9a-f]{7,40}):[\w./-]")
#: Keywords that carry a git ref into the harness (`capture_at(code_ref=…)`, `register(base_ref…)`).
REF_KEYWORDS = frozenset({"ref", "code_ref", "base_ref", "cand_ref", "page_ref", "base", "cand"})
#: Functions whose positional arguments include a ref they hand to git.
REF_FUNCTIONS = frozenset({"capture_at", "layer_at", "page_at", "compare_requests", "register",
                           "change_names", "in_flight_names", "refuse_unless_scored_by_base",
                           "scorer_fingerprint_at", "_scorer_files_at", "git_show",
                           "fixed_scorer", "_is_ancestor"})
SCANNED = ("tests", "vinci/evals")


def _name(node: ast.expr) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    return node.id if isinstance(node, ast.Name) else ""


def _hexes(node: ast.AST) -> list[str]:
    """Every hex literal in a constant, a list or tuple of constants, or an f-string's parts."""
    out: list[str] = []
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            s = n.value.strip()
            if HEX.match(s) and re.search(r"[a-f]", s) and re.search(r"[0-9]", s):
                out.append(s)
    return out


def refs_handed_to_git(source: str) -> list[tuple[int, str]]:
    """(line, sha) for each hex literal ``source`` hands to git, by the module docstring's rules."""
    tree = ast.parse(source)
    docstrings = {id(b[0].value) for d in ast.walk(tree)
                  if isinstance(d, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                    ast.AsyncFunctionDef))
                  and (b := d.body) and isinstance(b[0], ast.Expr)
                  and isinstance(b[0].value, ast.Constant) and isinstance(b[0].value.value, str)}
    found: set[tuple[int, str]] = set()
    for n in ast.walk(tree):
        if (isinstance(n, ast.Constant) and isinstance(n.value, str)
                and id(n) not in docstrings):
            found.update((n.lineno, m.group(1)) for m in REF_PATH.finditer(n.value))
        if isinstance(n, (ast.List, ast.Tuple)) and n.elts:
            first = n.elts[0]
            if isinstance(first, ast.Constant) and first.value == "git":
                found.update((n.lineno, h) for e in n.elts[1:] for h in _hexes(e))
        if isinstance(n, ast.Call):
            for kw in n.keywords:
                if kw.arg in REF_KEYWORDS:
                    found.update((kw.value.lineno, h) for h in _hexes(kw.value))
            if _name(n.func) in REF_FUNCTIONS:
                found.update((a.lineno, h) for a in n.args for h in _hexes(a))
    return sorted(found)


def _unreachable(sha: str) -> str | None:
    """Why ``sha`` is not a commit ``origin/main`` reaches, or None when it is."""
    ok = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{sha}^{{commit}}"],
                        capture_output=True).returncode == 0
    if not ok:
        return "is no commit in this clone"
    rc = subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", sha, "origin/main"],
                        capture_output=True).returncode
    return None if rc == 0 else ("is not reachable from origin/main" if rc == 1 else
                                 f"cannot be placed against origin/main (exit {rc})")


@pytest.fixture(scope="module")
def has_main() -> None:
    if subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "origin/main"],
                      capture_output=True).returncode != 0:
        pytest.skip("no origin/main in this clone (the gate fetches full history: fetch-depth 0)")


def _scan() -> dict[str, list[tuple[int, str]]]:
    out: dict[str, list[tuple[int, str]]] = {}
    for top in SCANNED:
        for f in sorted((ROOT / top).rglob("*.py")):
            refs = refs_handed_to_git(f.read_text(encoding="utf-8"))
            if refs:
                out[str(f.relative_to(ROOT))] = refs
    return out


def test_every_ref_a_test_hands_to_git_is_reachable_from_main(has_main: None) -> None:
    """(+) On the live corpus: every hex literal handed to git is a commit origin/main reaches."""
    scan = _scan()
    assert scan, "the lint found no ref on the corpus: it is suspect until it finds one"
    bad = [f"{f}:{line} {sha} {why}" for f, refs in scan.items() for line, sha in refs
           if (why := _unreachable(sha)) is not None]
    assert not bad, "a ref only a branch reaches breaks the day it is squashed:\n" + "\n".join(bad)


def test_the_incident_s_own_source_is_refused(has_main: None) -> None:
    """(−) The real failure: `tests/test_evals_round2.py` as merged at `a9c59287` (main) handed
    `4449189d:docs/records/` to `in_flight_names`, a commit no clone holds. The lint finds it and
    refuses it."""
    src = subprocess.run(["git", "-C", str(ROOT), "show", "a9c59287:tests/test_evals_round2.py"],
                         capture_output=True, text=True, check=True).stdout
    refs = refs_handed_to_git(src)
    assert ("4449189d" in {sha for _, sha in refs})
    assert _unreachable("4449189d") is not None


def test_provenance_text_is_not_handed_to_git() -> None:
    """(+) A hash in a docstring, a comment or a dict of record hashes is not checked."""
    ref_path = "4449" + "189d:docs/records/"   # joined at run time: no such literal here
    src = (f'"""Scored by 755044b4abf5 at 564baad8, read as {ref_path}."""\n'
           "# fix 4a's parent 03e384a3\n"
           'PIN = {"scorer": "755044b4abf5", "sha256": "5b8e82e76cbc"}\n')
    assert refs_handed_to_git(src) == []
