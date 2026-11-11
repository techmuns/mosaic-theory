"""EVERY MODULE A PAGE BUILD REACHES IS WATCHED, OR SAYS WHY NOT (fix request 2, 2026-11-11).

THE GAP. 26b's drift guard watches a DECLARED set: vinci/dossier, vinci/edgar and the modules named
in `EXTRA_WATCHED`. Nothing checked that the set covers what a page build actually runs: the theme
session found `mechanical` building every page's P/E pair from `vinci/screens/assemble.py`, which
nothing watched, so a change to that rule could move pages with no pin noticing.

THE RULE, NOW A TEST. Start from every watched module and from `vinci/dossier/render.py` (it renders
every page). Follow every `import` of a `vinci` module, module-level or inside a function, together
with the packages that import passes through. Every module reached must be watched, or be in
`NOT_EXTRACTION` with the reason it cannot change a page value. The walk stops at a
`NOT_EXTRACTION` module: what it imports is reached through it only, and it changes no page value.
Two exceptions: `render.py`, a start node though `NOT_EXTRACTION`; and a package's `__init__.py`,
passed through, because what it imports is what it re-exports (`from vinci.rank import X` reaches
`vinci/rank/ranker.py` only through `vinci/rank/__init__.py`). A module that newly joins
the reach is therefore unclassified, and this test fails until someone decides which it is.

WHAT "CAN CHANGE A PAGE VALUE" MEANS (the criterion each reason applies): given the same source
data, a change to the module's code can change a field a page carries — a value, a basis, a label, a
threshold, or the text an extractor reads. Transport, caching, storage, progress output and types
whose validators only refuse cannot.

STATIC, AND SAYS SO. Imports are read from the source, not executed. A module loaded by name at run
time (`importlib`) is not followed. None is on the page path at the commit this was written
(`frontend/build.py` loads itself, and the facts layer's signer by path, outside it).
"""
from __future__ import annotations

import ast
import functools
import os
from pathlib import Path

import pytest

from tests.test_extraction_version_drift import NOT_EXTRACTION, current_hashes

ROOT = Path(__file__).resolve().parents[1]
#: Renders every page, and is `NOT_EXTRACTION` (re-rendered, never re-extracted): a start node.
RENDER = "vinci/dossier/render.py"


@functools.cache
def _names(directory: Path) -> frozenset[str]:
    try:
        return frozenset(os.listdir(directory))
    except OSError:
        return frozenset()


def module_file(dotted: str, root: Path = ROOT) -> str | None:
    """`vinci.a.b` → `vinci/a/b.py` or `vinci/a/b/__init__.py`, relative to ``root``, or None.
    Every component must exist with exactly its case: a case-blind filesystem reads
    `vinci/store/Store.py` (a class imported from the package) as `vinci/store/store.py`."""
    for rel in (dotted.replace(".", "/") + ".py", dotted.replace(".", "/") + "/__init__.py"):
        path = root / rel
        if path.is_file() and all(part.name in _names(part.parent)
                                  for part in (path, *path.parents) if root in part.parents):
            return rel
    return None


@functools.cache
def imports_of(rel: str, root: Path = ROOT) -> frozenset[str]:
    """Every `vinci` module ``rel`` imports, anywhere in it, with each package on the way."""
    pkg = rel.removesuffix(".py").replace("/", ".")
    pkg = pkg.removesuffix(".__init__") if rel.endswith("__init__.py") else pkg.rpartition(".")[0]
    named: set[str] = set()
    for node in ast.walk(ast.parse((root / rel).read_text())):
        if isinstance(node, ast.Import):
            named |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = pkg.split(".")[: len(pkg.split(".")) - node.level + 1]
                base = ".".join([*parts, *([node.module] if node.module else [])])
            else:
                base = node.module or ""
            named |= {base} | {f"{base}.{a.name}" for a in node.names}
    out: set[str] = set()
    for dotted in named:
        if dotted.split(".")[0] != "vinci":
            continue
        parts = dotted.split(".")
        for i in range(1, len(parts) + 1):
            hit = module_file(".".join(parts[:i]), root)
            if hit and hit != rel:
                out.add(hit)
    return frozenset(out)


def watched() -> set[str]:
    """The drift guard's watched set, exactly as it hashes it (`current_hashes`, which both the
    old pin block and per-module pin files read)."""
    return set(current_hashes())


def unclassified(watch: set[str], reasons: dict[str, str],
                 root: Path = ROOT) -> dict[str, str]:
    """Each module the page build reaches that is neither in ``watch`` nor in ``reasons``, mapped
    to the module it was reached through."""
    via: dict[str, str] = {}
    stack = sorted(watch | {RENDER})
    seen = set(stack)
    while stack:
        rel = stack.pop()
        # A package's `__init__.py` is passed THROUGH even when excluded: its reason covers its own
        # code, and its imports are the modules it re-exports — `from vinci.rank import X` reaches
        # `vinci/rank/ranker.py` only this way.
        if rel in reasons and rel != RENDER and not rel.endswith("/__init__.py"):
            continue
        for dep in sorted(imports_of(rel, root)):
            if dep not in seen:
                seen.add(dep)
                via[dep] = rel
                stack.append(dep)
    return {m: by for m, by in sorted(via.items()) if m not in watch and m not in reasons}


def test_every_module_a_page_build_reaches_is_watched_or_says_why_not() -> None:
    """The rule, on the tree as it stands."""
    gaps = unclassified(watched(), NOT_EXTRACTION)
    assert not gaps, (
        "modules a page build reaches that the drift guard neither watches nor excludes with a "
        f"reason (module → reached through): {gaps}. If its code can change a page value, add it "
        "to EXTRA_WATCHED in tests/test_extraction_version_drift.py and re-pin; if it cannot, add "
        "it to NOT_EXTRACTION there with the reason.")


def test_the_rule_finds_the_module_that_proved_it() -> None:
    """NEGATIVE PIN on the real tree: unwatch `vinci/screens/assemble.py` — the module that
    builds every page's P/E pair and was unwatched until this change — and the rule names it, and
    only it. (On main before this change it named 63 modules, this one among them.)"""
    gaps = unclassified(watched() - {"vinci/screens/assemble.py"}, NOT_EXTRACTION)
    assert list(gaps) == ["vinci/screens/assemble.py"], gaps


@pytest.mark.parametrize("mod", ["vinci/rank/ranker.py", "vinci/resolver/resolver.py"])
def test_the_rule_finds_a_module_reached_only_through_its_package(mod: str) -> None:
    """NEGATIVE PIN on the real tree: a page build reaches these only as a name its package
    re-exports (`from vinci.rank import load_candidates_from_snapshot`, `from vinci.resolver import
    EntityResolver`), and the package's `__init__.py` is `NOT_EXTRACTION`. Unwatched, each is still
    named — the walk passes through a re-export rather than stopping at it."""
    gaps = unclassified(watched() - {mod}, NOT_EXTRACTION)
    assert list(gaps) == [mod], gaps


def test_the_walk_stops_at_an_excluded_module_and_reads_every_import_form(tmp_path: Path) -> None:
    """On a small tree: a function-local import and a relative one are followed, a package on the
    way is reached, and a module reached only through an excluded one is not."""
    files = {
        "vinci/__init__.py": "",
        "vinci/p/__init__.py": "",
        "vinci/p/page.py": "def f():\n    from vinci.q import deep\n    from . import sib\n",
        "vinci/p/sib.py": "",
        "vinci/q/__init__.py": "",
        "vinci/q/deep.py": "import vinci.r.only_via_deep\n",
        "vinci/r/__init__.py": "",
        "vinci/r/only_via_deep.py": "",
        "vinci/dossier/render.py": "",
    }
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text)
    reasons = {"vinci/q/deep.py": "excluded", "vinci/dossier/render.py": "render"}
    gaps = unclassified({"vinci/p/page.py"}, reasons, tmp_path)
    assert set(gaps) == {"vinci/__init__.py", "vinci/p/__init__.py", "vinci/p/sib.py",
                         "vinci/q/__init__.py"}, gaps
