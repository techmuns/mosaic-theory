"""The import graph of a ``vinci/`` tree, read from its source (``ast``), never by importing it.

Every ``import vinci.x`` and ``from vinci.x import y`` counts, at any depth — a function-level
import is a dependency the moment the function runs — and so does a relative import. ``from
vinci.x import y`` also counts ``vinci.x.y`` when that is a module, since it imports the module.
A dynamic import (``importlib``, a path loaded by name) is invisible here: the downstream part says
"not reached" only of what this graph can see.
"""
from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path


def module_of(path: str) -> str | None:
    """``vinci/dossier/render.py`` → ``vinci.dossier.render``; a non-``vinci`` path → None."""
    p = Path(path)
    if p.suffix != ".py" or not p.parts or p.parts[0] != "vinci":
        return None
    parts = list(p.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def import_graph(code_root: Path) -> dict[str, set[str]]:
    """Each module under ``code_root/vinci`` → the ``vinci`` modules it imports."""
    files = sorted((code_root / "vinci").rglob("*.py"))
    mods = {m: f for f in files if (m := module_of(str(f.relative_to(code_root)))) is not None}
    out: dict[str, set[str]] = {}
    for mod, f in mods.items():
        pkg = mod if f.name == "__init__.py" else mod.rpartition(".")[0]
        deps: set[str] = set()
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            out[mod] = deps
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                deps.update(a.name for a in node.names if a.name.split(".")[0] == "vinci")
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = pkg.split(".")
                    base = base[:len(base) - (node.level - 1)]
                    target = ".".join([*base, *([node.module] if node.module else [])])
                else:
                    target = node.module or ""
                if target.split(".")[0] != "vinci":
                    continue
                deps.add(target)
                deps.update(f"{target}.{a.name}" for a in node.names
                            if f"{target}.{a.name}" in mods)
        # a submodule import also runs its packages' __init__
        expanded: set[str] = set()
        for d in deps:
            parts = d.split(".")
            expanded.update(".".join(parts[:i]) for i in range(1, len(parts) + 1))
        out[mod] = {d for d in expanded if d in mods and d != mod}
    return out


def direct_importers(graph: dict[str, set[str]], module: str) -> set[str]:
    return {m for m, deps in graph.items() if module in deps}


def importers(graph: dict[str, set[str]], modules: Iterable[str]) -> set[str]:
    """Every module that imports any of ``modules``, directly or through others."""
    rev: dict[str, set[str]] = {}
    for m, deps in graph.items():
        for d in deps:
            rev.setdefault(d, set()).add(m)
    seen: set[str] = set()
    stack = list(modules)
    while stack:
        for m in rev.get(stack.pop(), ()):
            if m not in seen:
                seen.add(m)
                stack.append(m)
    return seen


def closure(graph: dict[str, set[str]], modules: Iterable[str]) -> set[str]:
    """``modules`` and everything they import, directly or through others."""
    seen = set(modules)
    stack = list(seen)
    while stack:
        for d in graph.get(stack.pop(), ()):
            if d not in seen:
                seen.add(d)
                stack.append(d)
    return seen


def function_imports(code_root: Path, module: str, function: str) -> set[str]:
    """The ``vinci`` modules a top-level ``function`` of ``module`` can reach by import: the ones
    imported inside its body, and the module's own top-level imports (it runs with them loaded).
    A CLI handler's reach is its own, not the whole CLI's (`vinci.cli` imports every command)."""
    path = code_root / Path(*module.split(".")).with_suffix(".py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    mods = {m for f in (code_root / "vinci").rglob("*.py")
            if (m := module_of(str(f.relative_to(code_root)))) is not None}
    out: set[str] = set()

    def take(node: ast.AST) -> None:
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            out.add(node.module)
            out.update(f"{node.module}.{a.name}" for a in node.names)

    found = False
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            take(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function:
            found = True
            for inner in ast.walk(node):
                take(inner)
    if not found:
        raise LookupError(f"{module} defines no top-level {function}")
    expanded = {".".join(d.split(".")[:i]) for d in out for i in range(1, d.count(".") + 2)}
    return {d for d in expanded if d in mods}
