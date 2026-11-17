"""Show that moving a pin off a living page changed no assertion and disabled no test (W27
follow-up, STATE row 41 (a)).

A pin moved to a frozen copy, or an invariant moved to a roster walk, must assert exactly what it
asserted before, and still run; only the line that READS the page may change. This compares, for
each changed `tests/**/*.py` file, every function at BASE with the same function in the working
tree. It classifies each difference:

- **CHANGED** (fails the check): the function's assertions, in source order, differ. An assertion
  is an `assert` statement, a `with pytest.raises(...)` / `pytest.warns(...)` item (`match=`
  included), or a `pytest.fail(...)` call. `ast.dump` carries no line numbers, so a move that
  shifts lines compares equal, and a renamed variable, a changed literal or a dropped assert does
  not.
- **DISABLED** (fails): the test can now stop running. Either a skip, skipif, xfail or
  importorskip decorator appears or changes (one only REMOVED runs the test more, and is not
  DISABLED), or a skip call appears that BASE did not make. A skip call is `pytest.skip` /
  `pytest.xfail` / `pytest.importorskip`, or a call to a SKIP HELPER: an imported `skip_unless_*`
  (`tests/ciq_export_support.py`'s), or a function of the module that makes a skip call, itself
  or through another skip helper, to any depth. The calls are compared by WHAT they call, never
  counted: one skip traded for another is DISABLED, as a count would net it. Slices 2–4 of W27
  each added a helper skip that the first cut, counting bare calls only, missed, and A's review
  of #1106 and #1107 found two more: a skip two calls down, and a swap the count read as none.
- **CONTROL** (fails): an assertion's enclosing conditions differ, or the function gains an early
  exit. A condition is each enclosing `if` (its test), `while` or `try`. An early exit is a new
  `return`, `continue`, `break` or `raise`. A wrapped or bypassable assert reads like an unchanged
  one, so it is never silent.
- **READER-ONLY** (listed, passes): the assertions differ only in which page reader they call, as
  in `_page("BRBR")[…]` → `frozen_doc("BRBR")[…]`. The readers are `tests/frozen_support.py`'s and
  every function of the module whose source names `dossier`.
- **POPULATION** (listed, passes): what an assertion runs over changed: a `parametrize` decorator,
  or the iterable of an enclosing `for`, including an assert newly put in a loop. That is what a
  roster walk is. The walk's own floor (`covered_where`) is what keeps it from walking nothing, and
  each slice's record lists every population it changes.
- **VANISHED** (fails): a test, or a helper that asserts, is gone. A helper that asserts nothing
  may go.

A new function is listed for the reader. The exit code is 1 when anything is CHANGED, DISABLED,
CONTROL or VANISHED.

Usage: python scripts/asserts_unchanged.py BASE [FILE ...]
With no FILE, it takes every `tests/**/*.py` that differs from BASE in the working tree (less
`tests/fixtures/`). Read only.
"""
from __future__ import annotations

import ast
import copy
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


#: The page readers a move swaps one for another inside an assert: `tests/frozen_support.py`'s, plus
#: every function of the module whose source names `dossier` (found per file). They are normalized
#: to one name only for the READER-ONLY test.
SUPPORT_READERS = frozenset({"frozen_doc", "frozen_page", "living_doc"})
SKIP_CALLS = frozenset({"skip", "xfail", "importorskip"})
#: The prefix of the imported skip helpers (`tests/ciq_export_support.py`): their bodies are in
#: another module, so they are known by name.
SKIP_HELPER_PREFIXES = ("skip_unless", "_skip_unless")
SKIP_MARKS = frozenset({"skip", "skipif", "xfail"})
FAILING = ("CHANGED", "DISABLED", "CONTROL", "VANISHED")


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


def _is_pytest_call(node: ast.AST, names: frozenset[str] | tuple[str, ...]) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
        and node.func.attr in names and isinstance(node.func.value, ast.Name) \
        and node.func.value.id == "pytest"


def _parents(fn: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: node for node in ast.walk(fn) for child in ast.iter_child_nodes(node)}


@dataclass
class Facts:
    """What the comparison reads off one function."""
    asserts: list[str]
    reader_asserts: list[str]
    conditions: list[str]                    # per assertion: its enclosing conditions
    loops: list[str]                         # per assertion: its enclosing loops' iterables
    marks: list[str] = field(default_factory=list)       # skip/skipif/xfail decorators
    params: list[str] = field(default_factory=list)      # parametrize decorators
    skips: list[str] = field(default_factory=list)       # what each skip call calls
    exits: int = 0


def skippers(source: str) -> frozenset[str]:
    """The module's own skip helpers: its functions whose own body makes a skip call, a pytest
    one or a call to a skip helper, to any depth (`_the_bands_export` skips only through
    `skip_unless_export`)."""
    tree = ast.parse(source)
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)]
    found: frozenset[str] = frozenset()
    while True:
        more = frozenset(n.name for n in fns if n.name not in found and any(
            _is_pytest_call(c, SKIP_CALLS) or _is_skip_helper_call(c, found)
            for c in _own_nodes(n)))
        if not more:
            return found
        found |= more


def _callee(node: ast.Call) -> str:
    f = node.func
    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == "pytest":
        return f"pytest.{f.attr}"
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""


def _is_skip_helper_call(node: ast.AST, helpers: frozenset[str]) -> bool:
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
    return name in helpers or name.startswith(SKIP_HELPER_PREFIXES)


def facts(fn: ast.FunctionDef | ast.AsyncFunctionDef, reader_names: frozenset[str],
          helpers: frozenset[str] = frozenset()) -> Facts:
    parent = _parents(fn)
    norm = _Reader(reader_names)
    found: list[tuple[int, int, ast.AST]] = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Assert):
            found.append((n.lineno, n.col_offset, n))
        elif isinstance(n, ast.With | ast.AsyncWith):
            found += [(i.context_expr.lineno, i.context_expr.col_offset, i.context_expr)
                      for i in n.items if _is_pytest_call(i.context_expr, ("raises", "warns"))]
        elif isinstance(n, ast.Expr) and _is_pytest_call(n.value, ("fail",)):
            found.append((n.lineno, n.col_offset, n))
    found.sort(key=lambda x: (x[0], x[1]))
    out = Facts([], [], [], [])
    for *_, node in found:
        out.asserts.append(ast.dump(node))
        out.reader_asserts.append(ast.dump(norm.visit(copy.deepcopy(node))))
        conds: list[str] = []
        loops: list[str] = []
        cur: ast.AST = node
        while cur is not fn:
            up = parent[cur]
            if isinstance(up, ast.If | ast.While) and cur is not up.test:
                conds.append(f"{type(up).__name__}:{ast.dump(up.test)}"
                             f":{'else' if cur in up.orelse else 'body'}")
            elif isinstance(up, ast.Try):
                conds.append("Try")
            elif isinstance(up, ast.For | ast.AsyncFor | ast.comprehension):
                loops.append(ast.dump(up.iter))
            cur = up
        out.conditions.append(repr(conds))
        out.loops.append(repr(loops))
    for d in fn.decorator_list:
        call = d.func if isinstance(d, ast.Call) else d
        name = call.attr if isinstance(call, ast.Attribute) else getattr(call, "id", "")
        if name in SKIP_MARKS:
            out.marks.append(ast.dump(d))
        elif name == "parametrize":
            out.params.append(ast.dump(d))
    for n in _own_nodes(fn):
        if isinstance(n, ast.Call) and (_is_pytest_call(n, SKIP_CALLS)
                                        or _is_skip_helper_call(n, helpers)):
            out.skips.append(_callee(n))
        elif isinstance(n, ast.Return | ast.Continue | ast.Break | ast.Raise):
            out.exits += 1
    return out


def _own_nodes(fn: ast.AST) -> list[ast.AST]:
    """The function's own nodes: a helper `def` or `lambda` nested in it exits ITSELF, never the
    test, so its body is not counted."""
    out: list[ast.AST] = []
    todo = list(ast.iter_child_nodes(fn))
    while todo:
        n = todo.pop()
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda | ast.ClassDef):
            continue
        out.append(n)
        todo.extend(ast.iter_child_nodes(n))
    return out


def functions(source: str) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse(source)
    out: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef):
            out[n.name] = n
        elif isinstance(n, ast.ClassDef):
            out |= {f"{n.name}.{m.name}": m for m in n.body
                    if isinstance(m, ast.FunctionDef | ast.AsyncFunctionDef)}
    return out


def assertions(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """The function's assertions in source order."""
    return facts(fn, frozenset()).asserts


def compare_sources(before_src: str, after_src: str, path: str) -> dict[str, list[str]]:
    """Every difference between BASE's and the working tree's functions in one file, by category
    (the module docstring). Pure: it reads no file and runs no git."""
    before = functions(before_src) if before_src else {}
    after = functions(after_src) if after_src else {}
    names = (readers(before_src) if before_src else SUPPORT_READERS) | (
        readers(after_src) if after_src else SUPPORT_READERS)
    helpers = (skippers(before_src) if before_src else frozenset()) | (
        skippers(after_src) if after_src else frozenset())
    out: dict[str, list[str]] = {k: [] for k in (*FAILING, "READER", "POPULATION", "new")}
    for k in sorted(before.keys() & after.keys()):
        b, a = facts(before[k], names, helpers), facts(after[k], names, helpers)
        row = f"{path}::{k}"
        if b.asserts != a.asserts:
            out["READER" if b.reader_asserts == a.reader_asserts else "CHANGED"].append(row)
        if set(a.marks) - set(b.marks) or Counter(a.skips) - Counter(b.skips):
            out["DISABLED"].append(row)
        same = b.reader_asserts == a.reader_asserts
        if (same and b.conditions != a.conditions) or a.exits > b.exits:
            out["CONTROL"].append(row)
        if b.params != a.params or (same and b.loops != a.loops):
            out["POPULATION"].append(row)
    out["VANISHED"] = [f"{path}::{k}" for k in sorted(before.keys() - after.keys())
                       if k.rsplit(".", 1)[-1].startswith("test") or assertions(before[k])]
    out["new"] = [f"{path}::{k}" for k in sorted(after.keys() - before.keys())]
    return out


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    root = Path(_git("rev-parse", "--show-toplevel").strip())
    base = argv[0]
    files = [Path(f).resolve().relative_to(root).as_posix() for f in argv[1:]]
    if not files:
        diffed = _git("diff", "--name-only", base, "--", ":(top)tests").splitlines()
        files = sorted(p for p in diffed
                       if p.endswith(".py") and not p.startswith("tests/fixtures/"))
    total: dict[str, list[str]] = {}
    compared = asserts = 0
    for path in files:
        try:
            src_before = _git("show", f"{base}:{path}")
        except subprocess.CalledProcessError:
            src_before = ""
        src_after = (root / path).read_text() if (root / path).exists() else ""
        for k, rows in compare_sources(src_before, src_after, path).items():
            total.setdefault(k, []).extend(rows)
        if src_before and src_after:
            compared += len(functions(src_before).keys() & functions(src_after).keys())
        if src_after:
            asserts += sum(len(assertions(f)) for f in functions(src_after).values())
    print(f"=== assertions at {base[:8]} vs the working tree: {len(files)} file(s), {compared} "
          f"function(s) in both, {asserts} assertion node(s) in the working tree ===")
    for label in (*FAILING, "READER", "POPULATION", "new"):
        for r in total.get(label, []):
            print(f"  {label:10} {r}")
    print("--- " + ", ".join(f"{k.lower()} {len(total.get(k, []))}"
                             for k in (*FAILING, "READER", "POPULATION", "new")))
    return 1 if any(total.get(k) for k in FAILING) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
