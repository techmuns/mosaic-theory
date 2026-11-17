"""Count the tests that read a LIVING committed page by its ticker, by name and by kind (W27).

A retirement still has to re-point every test that reads the retired name's living page by name
(`data/dossiers/<T>/…`): the coverage roster removes the other files a retirement touched, not
these. This prints, for each name with a committed page at REF, the test functions that read its
page, split into two kinds:

- VALUE — the function asserts a figure, a date or a phrase: an `assert` comparison with an
  operand that is a number literal other than 0 or 1, a `pytest.approx(...)` call, or a string
  literal holding a digit or a space. A value read off a re-drawn page belongs on a frozen
  fixture (CLAUDE.md TEST-LAYER RULE).
- INVARIANT — any other function: presence, citation, ordering or guard behaviour, which the rule
  allows on a living page, and which still breaks when that name leaves.

WHAT COUNTS AS A READ, by the AST of each `tests/**/*.py` at REF (never `tests/fixtures/`):
1. a string literal naming `dossiers/<T>` (a path segment), not under `frozen_pages`;
2. `<dossiers> / "<T>"`, where `<dossiers>` is a literal ending in `dossiers`, a `Path(...)` of
   one, a `… / "dossiers"` chain, or a name assigned one anywhere in the module;
3. `<dossiers> / <name>` or `f"…dossiers/{name}…"` where `<name>` is bound to literal tickers:
   by a `for` over a literal list or tuple, by `@pytest.mark.parametrize` on the function, or as
   a parameter of a helper (followed through helpers calling helpers, in one module) that a
   function calls with a literal ticker or a name so bound;
4. a literal ticker used as a subscript key (`idx["SMPL"]`) in a function that reads pages.
A read inside a helper or at module level is charged to each test function that calls the helper
or names the module-level binding, and takes that test's kind. A read the AST cannot see (a
ticker built at run time, a page reached through another module's helper) is not counted, so
every count is a lower bound.

Usage: python scripts/named_page_pins.py [REF] [--names T,U] [--list]
REF defaults to HEAD. Read only: it reads git objects at REF and writes nothing.
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from collections import defaultdict

SEG = re.compile(r"(?:^|/)dossiers/([A-Z][A-Z0-9.\-]*)(?:/|$)")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def pages_at(ref: str) -> set[str]:
    out = set()
    for path in git("ls-tree", "-r", "--name-only", ref, "data/dossiers").splitlines():
        parts = path.split("/")
        if len(parts) == 4 and parts[3] == "dossier.json":
            out.add(parts[2])
    return out


def test_files(ref: str) -> list[str]:
    return sorted(p for p in git("ls-tree", "-r", "--name-only", ref, "tests").splitlines()
                  if p.endswith(".py") and not p.startswith("tests/fixtures/"))


def _const_str(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


class Module:
    def __init__(self, tree: ast.Module, names: set[str]) -> None:
        self.tree, self.names = tree, names
        self.doss_names = {t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
                           for t in n.targets if isinstance(t, ast.Name)
                           and self.is_doss(n.value, set())}
        # one more pass: a name assigned from another dossiers name
        self.doss_names |= {t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
                            for t in n.targets if isinstance(t, ast.Name)
                            and self.is_doss(n.value, self.doss_names)}

    def is_doss(self, node: ast.AST, known: set[str] | None = None) -> bool:
        known = self.doss_names if known is None else known
        s = _const_str(node)
        if s is not None:
            return s.rstrip("/").endswith("dossiers") and "frozen_pages" not in s
        if isinstance(node, ast.Name):
            return node.id in known
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            r = _const_str(node.right)
            return r is not None and r.rstrip("/").endswith("dossiers") and \
                "frozen_pages" not in ast.unparse(node.left)
        if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) \
                == "Path" and len(node.args) == 1:
            return self.is_doss(node.args[0], known)
        return False

    def direct(self, scope: ast.AST) -> tuple[set[str], set[str]]:
        """(literal tickers read in scope, names used as the ticker segment in scope)."""
        lits, vars_ = set(), set()
        for n in ast.walk(scope):
            s = _const_str(n)
            if s is not None and "frozen_pages" not in s:
                lits |= {m for m in SEG.findall(s) if m in self.names}
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div) and self.is_doss(n.left):
                r = _const_str(n.right)
                if r in self.names:
                    lits.add(r)
                elif isinstance(n.right, ast.Name):
                    vars_.add(n.right.id)
            if isinstance(n, ast.JoinedStr):
                for a, b in zip(n.values, n.values[1:], strict=False):
                    if (_const_str(a) or "").endswith("dossiers/") and \
                            isinstance(b, ast.FormattedValue) and isinstance(b.value, ast.Name):
                        vars_.add(b.value.id)
        return lits, vars_

    def bound(self, scope: ast.AST, var: str) -> set[str]:
        """Literal tickers `var` is bound to in scope: a for-loop or a parametrize decorator."""
        out = set()
        for n in ast.walk(scope):
            if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == var \
                    and isinstance(n.iter, ast.List | ast.Tuple | ast.Set):
                out |= {v for e in n.iter.elts if (v := _const_str(e)) in self.names}
        if isinstance(scope, ast.FunctionDef):
            for d in scope.decorator_list:
                first = d.args[0] if isinstance(d, ast.Call) and d.args else None
                argnames = (_const_str(first) if first is not None else "") or ""
                if isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "parametrize" \
                        and var in argnames.replace(" ", "").split(","):
                    for e in ast.walk(d.args[1]) if len(d.args) > 1 else []:
                        if (v := _const_str(e)) in self.names:
                            out.add(v)
        return out


def kind(fn: ast.FunctionDef) -> str:
    for n in ast.walk(fn):
        if not isinstance(n, ast.Assert):
            continue
        for c in ast.walk(n.test):
            if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "approx":
                return "value"
            if not isinstance(c, ast.Compare):
                continue
            for op in [c.left, *c.comparators]:
                v = op.value if isinstance(op, ast.Constant) else None
                if isinstance(v, bool) or v is None:
                    continue
                if isinstance(v, int | float) and v not in (0, 1):
                    return "value"
                if isinstance(v, str) and (re.search(r"\d", v) or " " in v):
                    return "value"
    return "invariant"


def scan(ref: str, names: set[str], files: list[str]) -> dict[str, dict[str, set[str]]]:
    found: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for path in files:
        _scan_module(path, ast.parse(git("show", f"{ref}:{path}")), names, found)
    return found


def _scan_module(path: str, tree: ast.Module, names: set[str],
                 found: dict[str, dict[str, set[str]]]) -> None:
    mod = Module(tree, names)
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    params = {name: [a.arg for a in fn.args.args] for name, fn in funcs.items()}
    own: dict[str, set[str]] = {}
    seg_vars: dict[str, set[str]] = {}
    for name, fn in funcs.items():
        lits, vars_ = mod.direct(fn)
        seg_vars[name] = vars_
        own[name] = lits | {t for v in vars_ for t in mod.bound(fn, v)}
        # rule 4: a page-reading function that keys what it read by a literal ticker
        if any(mod.is_doss(n) for n in ast.walk(fn)):
            own[name] |= {k for n in ast.walk(fn) if isinstance(n, ast.Subscript)
                          if (k := _const_str(n.slice)) in names}
    # helpers, to a fixed point: a parameter that reaches a page path, directly or through
    # another helper's parameter
    helper: dict[str, set[int]] = {n: {params[n].index(v) for v in seg_vars[n]
                                       if v in params[n]} for n in funcs}
    changed = True
    while changed:
        changed = False
        for name, fn in funcs.items():
            for n in ast.walk(fn):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                        and n.func.id in helper and n.func.id != name:
                    for i in helper[n.func.id]:
                        if i < len(n.args) and isinstance(n.args[i], ast.Name) \
                                and n.args[i].id in params[name]:
                            j = params[name].index(n.args[i].id)
                            if j not in helper[name]:
                                helper[name].add(j)
                                changed = True

    def reads_of(name: str, seen: frozenset[str] = frozenset()) -> set[str]:
        fn, out = funcs[name], set(own[name])
        for n in ast.walk(fn):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id in funcs and n.func.id not in seen | {name}):
                continue
            callee = n.func.id
            out |= reads_of(callee, seen | {name}) if not helper[callee] else set(own[callee])
            for i in helper[callee]:
                if i < len(n.args):
                    v = _const_str(n.args[i])
                    if v in names:
                        out.add(v)
                    elif isinstance(n.args[i], ast.Name):
                        out |= mod.bound(fn, n.args[i].id)
        return out

    mod_reads: dict[str, set[str]] = {}
    for n in tree.body:
        if isinstance(n, ast.Assign):
            lits, _ = mod.direct(n.value)
            for t in n.targets:
                if isinstance(t, ast.Name) and lits:
                    mod_reads[t.id] = lits
    for name, fn in funcs.items():
        if not name.startswith("test"):
            continue
        reads = reads_of(name)
        for n in ast.walk(fn):
            if isinstance(n, ast.Name) and n.id in mod_reads:
                reads |= mod_reads[n.id]
        k = kind(fn)
        for t in reads:
            found[t][k].add(f"{path}::{name}")


def main(argv: list[str]) -> int:
    # `--names T,U` (as the usage line spells it) or `--names=T,U`
    only: list[str] | None = None
    args: list[str] = []
    rest = iter(argv)
    for a in rest:
        if a == "--names":
            only = [t.strip().upper() for t in next(rest, "").split(",") if t.strip()]
        elif a.startswith("--names="):
            only = [t.strip().upper() for t in a.split("=", 1)[1].split(",") if t.strip()]
        elif not a.startswith("--"):
            args.append(a)
    ref = args[0] if args else "HEAD"
    pages, files = pages_at(ref), test_files(ref)
    found = scan(ref, pages, files)
    names = sorted(only or pages,
                   key=lambda t: (-sum(len(v) for v in found[t].values()), t))
    print(f"=== tests reading a living page by name at {git('rev-parse', '--short', ref).strip()} "
          f"· {len(pages)} pages · {len(files)} test files scanned ===")
    tv = ti = 0
    for t in names:
        v, i = found[t]["value"], found[t]["invariant"]
        files = {s.split("::")[0] for s in v | i}
        tv, ti = tv + len(v), ti + len(i)
        print(f"{t:6} value {len(v):3}  invariant {len(i):3}  files {len(files):3}")
        if "--list" in argv:
            for s in sorted(v):
                print(f"    value      {s}")
            for s in sorted(i):
                print(f"    invariant  {s}")
    every = {s for t in names for k in found[t].values() for s in k}
    print(f"--- (test function, name) pairs: value {tv}, invariant {ti}; distinct test functions "
          f"{len(every)} in {len({s.split('::')[0] for s in every})} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
