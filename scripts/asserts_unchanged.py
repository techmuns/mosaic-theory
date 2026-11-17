"""Show that moving a pin off a living page changed no assertion (W27 follow-up, STATE row 41 (a)).

A pin moved to a frozen copy, or an invariant moved to a roster walk, must assert exactly what it
asserted before; only the line that READS the page may change. This compares, for each changed
`tests/**/*.py` file, every function at BASE with the same function in the working tree, by the
AST of its assertions, in order:
- every `assert` statement;
- every `with pytest.raises(...)` / `pytest.warns(...)` item, `match=` included;
- every `pytest.fail(...)` call.

`ast.dump` carries no line numbers, so a move that shifts lines compares equal, and a renamed
variable, a changed literal or a dropped assert does not.

It prints each function whose assertions changed, each test or asserting helper that vanished
(a helper that asserts nothing may go), and each new function (a new helper is expected; a new
test is listed for the reader). It exits 1 when any assertion changed or any such function
vanished.

Usage: python scripts/asserts_unchanged.py BASE [FILE ...]
With no FILE, it takes every `tests/**/*.py` that differs from BASE in the working tree (less
`tests/fixtures/`). Read only.
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def _is_pytest_call(node: ast.AST, names: tuple[str, ...]) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
        and node.func.attr in names and isinstance(node.func.value, ast.Name) \
        and node.func.value.id == "pytest"


def assertions(fn: ast.AST) -> list[str]:
    out: list[str] = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Assert):
            out.append(ast.dump(n))
        elif isinstance(n, ast.With | ast.AsyncWith):
            out += [ast.dump(i.context_expr) for i in n.items
                    if _is_pytest_call(i.context_expr, ("raises", "warns"))]
        elif isinstance(n, ast.Expr) and _is_pytest_call(n.value, ("fail",)):
            out.append(ast.dump(n))
    return out


def functions(source: str) -> dict[str, ast.AST]:
    tree = ast.parse(source)
    out: dict[str, ast.AST] = {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef):
            out[n.name] = n
        elif isinstance(n, ast.ClassDef):
            out |= {f"{n.name}.{m.name}": m for m in n.body
                    if isinstance(m, ast.FunctionDef | ast.AsyncFunctionDef)}
    return out


def compare(base: str, path: str) -> tuple[list[str], list[str], list[str], int]:
    """(changed, vanished, new, functions compared) for one file."""
    try:
        before = functions(_git("show", f"{base}:{path}"))
    except subprocess.CalledProcessError:
        before = {}
    after = functions(Path(path).read_text()) if Path(path).exists() else {}
    changed = [f"{path}::{k}" for k in sorted(before.keys() & after.keys())
               if assertions(before[k]) != assertions(after[k])]
    vanished = [f"{path}::{k}" for k in sorted(before.keys() - after.keys())
                if k.rsplit(".", 1)[-1].startswith("test") or assertions(before[k])]
    new = [f"{path}::{k}" for k in sorted(after.keys() - before.keys())]
    return changed, vanished, new, len(before.keys() & after.keys())


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    base, files = argv[0], argv[1:]
    if not files:
        files = sorted(p for p in _git("diff", "--name-only", base, "--", "tests").splitlines()
                       if p.endswith(".py") and not p.startswith("tests/fixtures/"))
    changed: list[str] = []
    vanished: list[str] = []
    new: list[str] = []
    compared = asserts = 0
    for path in files:
        c, v, n, k = compare(base, path)
        changed, vanished, new, compared = changed + c, vanished + v, new + n, compared + k
        if Path(path).exists():
            asserts += sum(len(assertions(f)) for f in functions(Path(path).read_text()).values())
    print(f"=== assertions at {base[:8]} vs the working tree: {len(files)} file(s), {compared} "
          f"function(s) in both, {asserts} assertion node(s) in the working tree ===")
    for label, rows in (("CHANGED", changed), ("VANISHED", vanished), ("new", new)):
        for r in rows:
            print(f"  {label:8} {r}")
    print(f"--- changed {len(changed)}, vanished {len(vanished)}, new {len(new)}")
    return 1 if changed or vanished else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
