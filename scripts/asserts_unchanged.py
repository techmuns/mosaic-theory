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

A function whose assertions differ ONLY in which page reader they call (`_page("BRBR")[…]` →
`frozen_doc("BRBR")[…]`) is listed READER-ONLY, never counted as changed: the readers are
`tests/frozen_support.py`'s and every function of the module that reads a page (its source
names `dossier`).

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


#: every path below is the repository's (`git diff --name-only` and `git show BASE:path` both
#: speak root-relative paths), so the working-tree side is read from the root, never the cwd
ROOT = Path(_git("rev-parse", "--show-toplevel").strip())


def _is_pytest_call(node: ast.AST, names: tuple[str, ...]) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
        and node.func.attr in names and isinstance(node.func.value, ast.Name) \
        and node.func.value.id == "pytest"


#: The page readers a move swaps one for another inside an assert (`_page("BRBR")[...]` →
#: `frozen_doc("BRBR")[...]`): `tests/frozen_support.py`'s, plus every function of the module
#: that reads a page, its source naming `dossier` (found per file). They are normalized to one
#: name only for the READER-ONLY report.
SUPPORT_READERS = frozenset({"frozen_doc", "frozen_page", "living_doc"})


def readers(source: str) -> frozenset[str]:
    """The module's own page readers: its functions whose source names `dossier`."""
    tree = ast.parse(source)
    return SUPPORT_READERS | {n.name for n in ast.walk(tree)
                              if isinstance(n, ast.FunctionDef) and "dossier" in ast.unparse(n)}


class _Reader(ast.NodeTransformer):
    def __init__(self, names: frozenset[str]) -> None:
        self.names = names

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id in self.names:
            node.func = ast.Name(id="READ", ctx=ast.Load())
        return node


def assertions(fn: ast.AST, reader_names: frozenset[str] | None = None) -> list[str]:
    """The function's assertions in SOURCE order (an assert moved into a loop keeps its place;
    `ast.walk` alone is breadth-first, and would reorder it). With ``reader_names``, every call to
    one of them is dumped as `READ(...)`, so a swap of reader alone compares equal."""
    import copy

    out: list[tuple[int, int, str]] = []
    norm = _Reader(reader_names) if reader_names else None

    def dump(node: ast.AST) -> str:
        return ast.dump(norm.visit(copy.deepcopy(node)) if norm else node)

    for n in ast.walk(fn):
        if isinstance(n, ast.Assert):
            out.append((n.lineno, n.col_offset, dump(n)))
        elif isinstance(n, ast.With | ast.AsyncWith):
            out += [(i.context_expr.lineno, i.context_expr.col_offset, dump(i.context_expr))
                    for i in n.items if _is_pytest_call(i.context_expr, ("raises", "warns"))]
        elif isinstance(n, ast.Expr) and _is_pytest_call(n.value, ("fail",)):
            out.append((n.lineno, n.col_offset, dump(n)))
    return [d for *_, d in sorted(out)]


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


def compare(base: str, path: str) -> tuple[list[str], list[str], list[str], int, list[str]]:
    """(changed, vanished, new, functions compared, reader-only) for one file. A function whose
    assertions differ ONLY in which page reader they call (equal once every reader is `READ`) is
    reader-only, listed apart and never counted as changed."""
    try:
        src_before = _git("show", f"{base}:{path}")
    except subprocess.CalledProcessError:
        src_before = ""
    src_after = (ROOT / path).read_text() if (ROOT / path).exists() else ""
    before = functions(src_before) if src_before else {}
    after = functions(src_after) if src_after else {}
    names = (readers(src_before) if src_before else SUPPORT_READERS) | (
        readers(src_after) if src_after else SUPPORT_READERS)
    differ = [k for k in sorted(before.keys() & after.keys())
              if assertions(before[k]) != assertions(after[k])]
    reader_only = [f"{path}::{k}" for k in differ
                   if assertions(before[k], names) == assertions(after[k], names)]
    changed = [f"{path}::{k}" for k in differ if f"{path}::{k}" not in reader_only]
    vanished = [f"{path}::{k}" for k in sorted(before.keys() - after.keys())
                if k.rsplit(".", 1)[-1].startswith("test") or assertions(before[k])]
    new = [f"{path}::{k}" for k in sorted(after.keys() - before.keys())]
    return changed, vanished, new, len(before.keys() & after.keys()), reader_only


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    base = argv[0]
    files = [Path(f).resolve().relative_to(ROOT).as_posix() for f in argv[1:]]
    if not files:
        diffed = _git("diff", "--name-only", base, "--", ":(top)tests").splitlines()
        files = sorted(p for p in diffed
                       if p.endswith(".py") and not p.startswith("tests/fixtures/"))
    changed: list[str] = []
    vanished: list[str] = []
    new: list[str] = []
    reader_only: list[str] = []
    compared = asserts = 0
    for path in files:
        c, v, n, k, r = compare(base, path)
        changed, vanished, new, compared = changed + c, vanished + v, new + n, compared + k
        reader_only += r
        if (ROOT / path).exists():
            asserts += sum(len(assertions(f))
                           for f in functions((ROOT / path).read_text()).values())
    print(f"=== assertions at {base[:8]} vs the working tree: {len(files)} file(s), {compared} "
          f"function(s) in both, {asserts} assertion node(s) in the working tree ===")
    for label, rows in (("CHANGED", changed), ("VANISHED", vanished), ("READER", reader_only),
                        ("new", new)):
        for r in rows:
            print(f"  {label:8} {r}")
    print(f"--- changed {len(changed)}, vanished {len(vanished)}, reader-only {len(reader_only)} "
          f"(the same assertion through another page reader), new {len(new)}")
    return 1 if changed or vanished else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
