"""Count the tests that read a LIVING committed page by its ticker, by name and by kind (W27).

A retirement still has to re-point every test that reads the retired name's living page by name
(`data/dossiers/<T>/…`, or its web mirror `frontend/dossiers/<T>.json` / `.md`): the coverage
roster removes the other files a retirement touched, not these. This prints, for each name with a
committed page at REF, the test functions that read its page, split into two kinds:

- VALUE — the function asserts a figure, a date or a phrase: an `assert` comparison with an
  operand that is a number literal other than 0 or 1, a `pytest.approx(...)` call, or a string
  literal holding a digit or a space. A value read off a re-drawn page belongs on a frozen
  fixture (CLAUDE.md TEST-LAYER RULE).
- INVARIANT — any other function: presence, citation, ordering or guard behaviour, which the rule
  allows on a living page, and which still breaks when that name leaves.

WHAT COUNTS AS A READ, by the AST of each `tests/**/*.py` at REF (never `tests/fixtures/`):
1. a string literal naming `dossiers/<T>` (a path segment, or the mirror's `<T>.json` / `<T>.md`),
   not under `frozen_pages`;
2. `<dossiers> / "<T>"`, where `<dossiers>` is a literal ending in `dossiers`, a `Path(...)` of
   one, a `… / "dossiers"` chain, or a name assigned one (in the function, else in the module);
3. `<dossiers> / <name>` or `f"…dossiers/{name}…"` where `<name>` is bound to literal tickers:
   by a `for` over a literal list or tuple, by `@pytest.mark.parametrize` on the function, or as
   a parameter of a helper (followed through helpers calling helpers, in one module, and into the
   helpers of the support modules it imports from) that a function calls with a literal ticker
   or a name so bound;
4. a literal ticker used as a subscript key (`idx["SMPL"]`) of a name the function filled from
   page reads (assigned from one, or written in a loop over one);
5. a JavaScript template path `dossiers/${t}` in a string (a node driver), charged to every page
   ticker the same string quotes (`for (const t of ["TJX", "NFLX"])`).

WHAT DOES NOT COUNT (each was a false positive of the first scan, slices 1–4 of W27):
- a path rooted in a pytest tmp directory (`tmp_path / "data" / "dossiers" / "AMZN"`, or a name
  assigned from one): a scratch tree the test writes, never the committed page;
- a git object path (`f"{rev}:data/dossiers/NFLX/dossier.json"`): a page as it was at a commit,
  other than `HEAD:`, whose object is the living page;
- a name bound to a dossiers folder in ANOTHER function: bindings are read per function first.

A read inside a helper or at module level is charged to each test function that calls the helper
or names the module-level binding, and takes that test's kind. A read the AST cannot see is not
counted, so every count is a LOWER BOUND: `tests/test_named_page_pins.py`'s ratchet holds it, and
a retirement replayed with the whole suite is the proof. Not seen today (the code review of slice
5 and A's review of #1111; `tests/test_named_page_pins.BLIND` lists them with an example each): a
ticker built at run time, or held in a module constant; a loop or parametrize over a module
constant; a fixture that reads a page; `+` or `.format`, and JavaScript concatenation; a test
method in a class, or an `async` test; a support helper that reads a fixed ticker rather than a
parameter; a ticker passed to a helper by keyword; and a page reached through a module outside
`tests/` (`frontend/build.py`). Seen since A's review: a parameter that DEFAULTS to the living
folder (`def _page(t, root=DOSS)`), a ticker bound in the function itself, tuple assignment, and
multi-argument `Path`, `joinpath` and `os.path.join`.

Usage: python scripts/named_page_pins.py [REF] [--names T,U] [--list] [--worktree]
REF defaults to HEAD. Read only: it reads git objects at REF (or the working tree with
`--worktree`) and writes nothing.
"""
from __future__ import annotations

import ast
import functools
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

#: A page by its path segment, or its web mirror by `<T>.json` / `<T>.md`.
SEG = re.compile(r"(?:^|/)dossiers/([A-Z][A-Z0-9.\-]*?)(?:/|\.(?:json|md)\b|$)")
#: A git object path, `<rev>:data/dossiers/…`: the page as it was at a commit, never the living one.
GITREV = re.compile(r"[^\s\"'`]*:(?:data/|frontend/)?dossiers/[^\s\"'`]*")
#: A JavaScript template path over a ticker variable, in a node driver string.
JS_TEMPLATE = re.compile(r"dossiers/\$\{")
JS_QUOTED = re.compile(r"[\"']([A-Z][A-Z0-9.\-]*)[\"']")
#: The pytest fixtures that name a scratch directory.
TMP_ROOTS = frozenset({"tmp_path", "tmp_path_factory", "tmpdir"})

Found = dict[str, dict[str, set[str]]]


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


def sources_at(ref: str) -> dict[str, str]:
    return {p: git("show", f"{ref}:{p}") for p in test_files(ref)}


def worktree(root: Path) -> tuple[set[str], dict[str, str]]:
    """(the page names, every `tests/**/*.py` source) as the working tree holds them."""
    pages = {p.parent.name for p in (root / "data" / "dossiers").glob("*/dossier.json")}
    files = {p.relative_to(root).as_posix(): p.read_text()
             for p in sorted((root / "tests").rglob("*.py"))
             if "fixtures" not in p.relative_to(root / "tests").parts
             and "__pycache__" not in p.parts}
    return pages, files


def _const_str(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _names_in(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


@functools.lru_cache(maxsize=8192)
def _assigned(scope: ast.AST) -> tuple[tuple[str, ast.AST], ...]:
    """(name, value) for every plain-name assignment in scope (`=`, annotated, walrus)."""
    out: list[tuple[str, ast.AST]] = []
    for n in ast.walk(scope):
        if isinstance(n, ast.Assign):
            out += [(t.id, n.value) for t in n.targets if isinstance(t, ast.Name)]
            # `DOSS, OTHER = Path("data/dossiers"), …`: each name takes its own element
            out += [(e.id, v) for t in n.targets if isinstance(t, ast.Tuple | ast.List)
                    and isinstance(n.value, ast.Tuple | ast.List)
                    and len(t.elts) == len(n.value.elts)
                    for e, v in zip(t.elts, n.value.elts, strict=True) if isinstance(e, ast.Name)]
        elif (isinstance(n, ast.AnnAssign) and n.value is not None
              and isinstance(n.target, ast.Name)) or isinstance(n, ast.NamedExpr):
            assert n.value is not None and isinstance(n.target, ast.Name)
            out.append((n.target.id, n.value))
    return tuple(out)


def _docstrings(tree: ast.AST) -> set[int]:
    """The ids of every docstring node: prose about a page, never a read of one."""
    out: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) \
                and n.body and isinstance(n.body[0], ast.Expr) \
                and _const_str(n.body[0].value) is not None:
            out.add(id(n.body[0].value))
    return out


def _param_defaults(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[tuple[int | None, str,
                                                                         ast.AST]]:
    """(positional index or None for keyword-only, name, default) of every defaulted parameter."""
    pos = [*fn.args.posonlyargs, *fn.args.args]
    out: list[tuple[int | None, str, ast.AST]] = [
        (len(pos) - len(fn.args.defaults) + i, a.arg, d) for i, (a, d) in enumerate(
            zip(pos[len(pos) - len(fn.args.defaults):], fn.args.defaults, strict=True))]
    out += [(None, a.arg, d) for a, d in zip(fn.args.kwonlyargs, fn.args.kw_defaults, strict=True)
            if d is not None]
    return out


def _join(node: ast.AST) -> tuple[ast.AST | None, list[ast.expr]] | None:
    """(the base, the parts) of a path join that is not `/`: `Path(a, b, …)` (base None),
    `x.joinpath(a, …)` (base x), `os.path.join(a, b, …)` (base None); else None."""
    if not isinstance(node, ast.Call) or node.keywords:
        return None
    f = node.func
    if (isinstance(f, ast.Name) and f.id in ("Path", "PurePath")) or (
            isinstance(f, ast.Attribute) and f.attr in ("Path", "PurePath")):
        return None, list(node.args)
    if isinstance(f, ast.Attribute) and f.attr == "joinpath":
        return f.value, list(node.args)
    if isinstance(f, ast.Attribute) and f.attr == "join" and isinstance(f.value, ast.Attribute) \
            and f.value.attr == "path":
        return None, list(node.args)
    return None


def _tmp_closure(scope: ast.AST, start: set[str]) -> set[str]:
    """``start`` and every name scope assigns from one of them: a path built in a tmp directory."""
    out = set(start)
    grew = True
    while grew:
        more = {t for t, v in _assigned(scope) if t not in out and _names_in(v) & out}
        out |= more
        grew = bool(more)
    return out


def _string_tickers(s: str, names: set[str]) -> set[str]:
    """The page tickers a string literal reads: its path segments and mirror files, less any git
    object path, plus every quoted ticker of a JavaScript template over a ticker variable."""
    # HEAD's own object IS the committed living page, so only another revision's is dropped
    s = GITREV.sub(lambda m: m.group() if m.group().startswith("HEAD:") else "", s)
    out = {m for m in SEG.findall(s) if m in names}
    if JS_TEMPLATE.search(s):
        out |= {m for m in JS_QUOTED.findall(s) if m in names}
    return out


class Module:
    def __init__(self, tree: ast.Module, names: set[str]) -> None:
        self.tree, self.names = tree, names
        self.docs = _docstrings(tree)
        self.funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        self._tmp_cache: dict[int, set[str]] = {}
        self._known_cache: dict[int, set[str]] = {}
        # the MODULE's own tmp names only: a name one function assigns from `tmp_path` is that
        # function's, never another's (`tmp_in` adds each function's own), as for `doss_names`
        top = ast.Module(body=[n for n in tree.body if not isinstance(
            n, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)], type_ignores=[])
        self.tmp_names = _tmp_closure(top, set(TMP_ROOTS))
        self.tmp_params = self._tmp_params()
        self.doss_names = self._dossiers_names(tree, set())

    def _tmp_params(self) -> dict[str, set[str]]:
        """Per module function, the parameters EVERY call site in the module passes a tmp
        directory (`_copy("UBER", tmp_path)` → `_copy`'s `root`). A helper also called with the
        real root anywhere is not one, so a living read through it still counts."""
        params = {n: [a.arg for a in f.args.args] for n, f in self.funcs.items()}
        out: dict[str, set[str]] = {n: set() for n in self.funcs}
        for _ in range(3):   # a tmp parameter handed on to another helper
            sites: dict[str, list[tuple[ast.Call, set[str]]]] = defaultdict(list)
            for name, f in self.funcs.items():
                tmp = _tmp_closure(f, self.tmp_names | out[name])
                for n in ast.walk(f):
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                            and n.func.id in self.funcs:
                        sites[n.func.id].append((n, tmp))
            for callee, calls in sites.items():
                for i, p in enumerate(params[callee]):
                    def passes_tmp(call: ast.Call, tmp: set[str], i: int = i, p: str = p) -> bool:
                        arg = call.args[i] if i < len(call.args) else next(
                            (k.value for k in call.keywords if k.arg == p), None)
                        return arg is not None and bool(_names_in(arg) & tmp)
                    if calls and all(passes_tmp(c, t) for c, t in calls):
                        out[callee].add(p)
        return out

    def tmp_in(self, scope: ast.AST) -> set[str]:
        if not isinstance(scope, ast.FunctionDef):
            return self.tmp_names
        if id(scope) not in self._tmp_cache:
            self._tmp_cache[id(scope)] = _tmp_closure(
                scope, self.tmp_names | self.tmp_params.get(scope.name, set()))
        return self._tmp_cache[id(scope)]

    def _dossiers_names(self, scope: ast.AST, outer: set[str],
                        tmp: set[str] | None = None) -> set[str]:
        """The names bound to a dossiers folder in scope, its own bindings first: a name the scope
        assigns is the scope's, whatever another scope binds it to."""
        pairs = _assigned(scope)
        own = {t for t, _ in pairs}
        known = outer - own
        if isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef):
            # a parameter whose DEFAULT is the living folder (`def _page(t, root=DOSS)`) is one;
            # a call that hands it another root reads that root instead (`default_roots`)
            known |= {n for _, n, d in _param_defaults(scope)
                      if n not in own and self.is_doss(d, known, tmp)}
        for _ in range(3):   # a name assigned from another dossiers name
            known |= {t for t, v in pairs if self.is_doss(v, known, tmp)}
        return known

    def default_roots(self, fn: ast.FunctionDef) -> list[tuple[int | None, str]]:
        """(index, name) of each parameter whose default is the living dossiers folder."""
        return [(i, n) for i, n, d in _param_defaults(fn) if self.is_doss(d)]

    def _tmp_rooted(self, node: ast.AST, tmp: set[str] | None = None) -> bool:
        while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            node = node.left
        return bool(_names_in(node) & (self.tmp_names if tmp is None else tmp))

    def is_doss(self, node: ast.AST, known: set[str] | None = None,
                tmp: set[str] | None = None) -> bool:
        known = self.doss_names if known is None else known
        s = _const_str(node)
        if s is not None:
            return s.rstrip("/").endswith("dossiers") and "frozen_pages" not in s
        if isinstance(node, ast.Name):
            return node.id in known
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            r = _const_str(node.right)
            if r is not None and r.rstrip("/").endswith("dossiers") and \
                    "frozen_pages" not in ast.unparse(node.left):
                return not self._tmp_rooted(node, tmp)
            return False
        if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) \
                == "Path" and len(node.args) == 1:
            return self.is_doss(node.args[0], known, tmp)
        joined = _join(node)
        if joined is not None and joined[1]:
            base, parts = joined
            last = _const_str(parts[-1])
            text = ast.unparse(node)
            rooted = base if base is not None else parts[0]
            return last is not None and last.rstrip("/").endswith("dossiers") and \
                "frozen_pages" not in text and not self._tmp_rooted(rooted, tmp)
        return False

    def known_in(self, scope: ast.AST) -> set[str]:
        if not isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef):
            return self.doss_names
        if id(scope) not in self._known_cache:
            self._known_cache[id(scope)] = self._dossiers_names(
                scope, self.doss_names, self.tmp_in(scope))
        return self._known_cache[id(scope)]

    def direct(self, scope: ast.AST) -> tuple[set[str], set[str]]:
        """(literal tickers read in scope, names used as the ticker segment in scope)."""
        known, tmp = self.known_in(scope), self.tmp_in(scope)
        lits, vars_ = set(), set()
        tmp_args: set[int] = set()   # literals that extend a tmp-rooted path
        for n in ast.walk(scope):
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div) and self._tmp_rooted(n, tmp):
                tmp_args |= {id(c) for c in ast.walk(n.right)}
        for n in ast.walk(scope):
            s = _const_str(n)
            if s is not None and "frozen_pages" not in s and id(n) not in tmp_args \
                    and id(n) not in self.docs:
                lits |= _string_tickers(s, self.names)
            if isinstance(n, ast.JoinedStr):
                text = "".join(_const_str(v) or "\x00" for v in n.values)
                if JS_TEMPLATE.search(text) and "frozen_pages" not in text:
                    lits |= {m for m in JS_QUOTED.findall(text) if m in self.names}
                for a, b in zip(n.values, n.values[1:], strict=False):
                    if (_const_str(a) or "").endswith("dossiers/") and \
                            not GITREV.search(_const_str(a) or "") and \
                            isinstance(b, ast.FormattedValue) and isinstance(b.value, ast.Name):
                        vars_.add(b.value.id)
            joined = _join(n)
            if joined is not None and "frozen_pages" not in ast.unparse(n):
                base, parts = joined
                at = base is not None and self.is_doss(base, known, tmp)
                for k, part in enumerate(parts):
                    if at:   # the part after a dossiers folder is the page
                        c = _const_str(part)
                        if c in self.names:
                            lits.add(c)
                        elif isinstance(part, ast.Name):
                            vars_.add(part.id)
                        break
                    c = _const_str(part)
                    at = (c is not None and c.rstrip("/").endswith("dossiers")) or \
                        (k == 0 and self.is_doss(part, known, tmp))
                    if k == 0 and self._tmp_rooted(part, tmp):
                        break
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div) and \
                    self.is_doss(n.left, known, tmp):
                r = _const_str(n.right)
                if r in self.names:
                    lits.add(r)
                elif isinstance(n.right, ast.Name):
                    vars_.add(n.right.id)
        return lits, vars_

    def page_vars(self, fn: ast.AST) -> set[str]:
        """The names a function fills from page reads: assigned from an expression that reads
        pages, or written (`x[k] = …`, `x.append(…)`) inside a loop over one."""
        known, tmp = self.known_in(fn), self.tmp_in(fn)

        def reads(expr: ast.AST, pv: set[str]) -> bool:
            return any(self.is_doss(c, known, tmp) for c in ast.walk(expr)) \
                or bool(_names_in(expr) & pv)

        pv: set[str] = set()
        for _ in range(3):
            for t, v in _assigned(fn):
                if reads(v, pv):
                    pv.add(t)
            for loop in (n for n in ast.walk(fn) if isinstance(n, ast.For | ast.comprehension)):
                if not reads(loop.iter, pv):
                    continue
                body = loop.body if isinstance(loop, ast.For) else []
                for n in (c for b in body for c in ast.walk(b)):
                    if isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Store) and \
                            isinstance(n.value, ast.Name):
                        pv.add(n.value.id)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and \
                            isinstance(n.func.value, ast.Name) and \
                            n.func.attr in ("append", "add", "update", "setdefault"):
                        pv.add(n.func.value.id)
        return pv

    def bound(self, scope: ast.AST, var: str) -> set[str]:
        """Literal tickers `var` is bound to in scope: a for-loop, a parametrize decorator, or an
        assignment in the scope itself (`t = "AMZN"`, `a, t = …, "AMZN"`)."""
        out = {v for t, val in _assigned(scope)
               if t == var and (v := _const_str(val)) in self.names}
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


def _module_name(path: str) -> str:
    return path[:-3].replace("/", ".")


def _imports(tree: ast.Module) -> tuple[dict[str, tuple[str, str]], dict[str, str]]:
    """(local name → (module, function) for `from tests.m import f [as g]`,
    alias → module for `import tests.m as a` / `from tests import m`)."""
    funcs: dict[str, tuple[str, str]] = {}
    mods: dict[str, str] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.split(".")[0] == "tests":
            for a in n.names:
                if n.module == "tests":
                    mods[a.asname or a.name] = f"tests.{a.name}"
                else:
                    funcs[a.asname or a.name] = (n.module, a.name)
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] == "tests" and a.asname:
                    mods[a.asname] = a.name
    return funcs, mods


def _helpers(tree: ast.Module, mod: Module, ext: dict[str, dict[str, set[int]]]
             ) -> tuple[dict[str, ast.FunctionDef], dict[str, set[str]], dict[str, set[str]],
                        dict[str, list[str]], dict[str, set[int]], dict[str, set[int]]]:
    """A module's functions, their own literal reads and segment names, parameters, which
    parameters reach a page path (to a fixed point, local helpers and imported ones alike), and
    the imported helpers by local name."""
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    params = {name: [a.arg for a in fn.args.args] for name, fn in funcs.items()}
    own: dict[str, set[str]] = {}
    seg_vars: dict[str, set[str]] = {}
    for name, fn in funcs.items():
        lits, vars_ = mod.direct(fn)
        seg_vars[name] = vars_
        own[name] = lits | {t for v in vars_ for t in mod.bound(fn, v)}
        # rule 4: a literal ticker keying a name the function filled from page reads (the fill
        # is traced only where a name is keyed by a literal ticker at all)
        keyed = [(n.value.id, k) for n in ast.walk(fn) if isinstance(n, ast.Subscript)
                 and isinstance(n.value, ast.Name) if (k := _const_str(n.slice)) in mod.names]
        if keyed:
            pv = mod.page_vars(fn)
            own[name] |= {k for v, k in keyed if v in pv}
    imp_funcs, imp_mods = _imports(tree)
    imported: dict[str, set[int]] = {}
    for local, (m, f) in imp_funcs.items():
        if f in ext.get(m, {}) and ext[m][f]:
            imported[local] = ext[m][f]
    helper: dict[str, set[int]] = {n: {params[n].index(v) for v in seg_vars[n]
                                       if v in params[n]} for n in funcs}

    def callee_params(n: ast.Call) -> set[int] | None:
        f = n.func
        if isinstance(f, ast.Name):
            return helper.get(f.id) if f.id in funcs else imported.get(f.id)
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and \
                f.value.id in imp_mods:
            return ext.get(imp_mods[f.value.id], {}).get(f.attr) or None
        return None

    changed = True
    while changed:
        changed = False
        for name, fn in funcs.items():
            for n in ast.walk(fn):
                if not isinstance(n, ast.Call) or getattr(n.func, "id", None) == name:
                    continue
                for i in callee_params(n) or set():
                    if i < len(n.args) and isinstance(n.args[i], ast.Name) \
                            and n.args[i].id in params[name]:
                        j = params[name].index(n.args[i].id)
                        if j not in helper[name]:
                            helper[name].add(j)
                            changed = True
    ext_calls = {**imported, **{f"{a}.{f}": ps for a, m in imp_mods.items()
                                for f, ps in ext.get(m, {}).items() if ps}}
    return funcs, own, seg_vars, params, helper, ext_calls


def support_helpers(sources: dict[str, str], names: set[str]) -> dict[str, dict[str, set[int]]]:
    """For each support module (`tests/**/*.py` not named `test_*`), its functions whose
    parameter reaches a page path, and which parameters: `living_doc(T)`, `page_export_sha(T)`.
    Two passes, so a helper calling another support module's helper is followed."""
    ext: dict[str, dict[str, set[int]]] = {}
    support = {p: s for p, s in sources.items() if not Path(p).name.startswith("test_")
               and "dossiers" in s}
    for _ in range(2):
        for path, src in support.items():
            tree = ast.parse(src)
            _, _, _, _, helper, _ = _helpers(tree, Module(tree, names), ext)
            ext[_module_name(path)] = helper
    return ext


def scan_sources(sources: dict[str, str], names: set[str]) -> Found:
    found: Found = defaultdict(lambda: defaultdict(set))
    ext = support_helpers(sources, names)
    # EXACT, NOT A HEURISTIC: every rule needs `dossiers` in the module's text, or a call to a
    # support helper whose parameter reaches a page path, so a module with neither has no pair
    readers = {f for helpers in ext.values() for f, ps in helpers.items() if ps}
    for path, src in sources.items():
        if "dossiers" in src or any(f in src for f in readers):
            _scan_module(path, ast.parse(src), names, found, ext)
    return found


def scan(ref: str, names: set[str], files: list[str]) -> Found:
    return scan_sources({p: git("show", f"{ref}:{p}") for p in files}, names)


def _scan_module(path: str, tree: ast.Module, names: set[str], found: Found,
                 ext: dict[str, dict[str, set[int]]] | None = None) -> None:
    mod = Module(tree, names)
    funcs, own, _, _, helper, ext_calls = _helpers(tree, mod, ext or {})

    def call_params(n: ast.Call) -> tuple[str | None, set[int]]:
        f = n.func
        if isinstance(f, ast.Name) and f.id in funcs:
            return f.id, helper[f.id]
        key = f.id if isinstance(f, ast.Name) else (
            f"{f.value.id}.{f.attr}" if isinstance(f, ast.Attribute)
            and isinstance(f.value, ast.Name) else "")
        return None, ext_calls.get(key, set())

    roots = {n: mod.default_roots(f) for n, f in funcs.items()}

    def elsewhere(n: ast.Call, callee: str, fn: ast.FunctionDef) -> bool:
        """The call hands ``callee`` a root other than the living folder its parameter defaults to
        (`_page("NCNO", FROZEN_0818)`), so it reads no living page through that parameter."""
        known, tmp = mod.known_in(fn), mod.tmp_in(fn)
        for i, p in roots.get(callee, []):
            arg = n.args[i] if i is not None and i < len(n.args) else next(
                (k.value for k in n.keywords if k.arg == p), None)
            if arg is not None and not mod.is_doss(arg, known, tmp):
                return True
        return False

    def reads_of(name: str, seen: frozenset[str] = frozenset()) -> set[str]:
        fn, out = funcs[name], set(own[name])
        for n in ast.walk(fn):
            if not isinstance(n, ast.Call):
                continue
            local, idx = call_params(n)
            if local is not None:
                if local in seen | {name}:
                    continue
                if roots.get(local) and elsewhere(n, local, fn):
                    continue
                out |= reads_of(local, seen | {name}) if not helper[local] else set(own[local])
            for i in idx:
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


def pairs(found: Found) -> set[tuple[str, str]]:
    """Every (test function, ticker) pair the scan found."""
    return {(s, t) for t, kinds in found.items() for k in kinds.values() for s in k}


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
    if "--worktree" in argv:
        pages, sources = worktree(Path(git("rev-parse", "--show-toplevel").strip()))
        where = "the working tree"
    else:
        ref = args[0] if args else "HEAD"
        pages, sources = pages_at(ref), sources_at(ref)
        where = git("rev-parse", "--short", ref).strip()
    found = scan_sources(sources, pages)
    names = sorted(only or pages,
                   key=lambda t: (-sum(len(v) for v in found[t].values()), t))
    print(f"=== tests reading a living page by name at {where} "
          f"· {len(pages)} pages · {len(sources)} test files scanned ===")
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
          f"{len(every)} in {len({s.split('::')[0] for s in every})} files — a LOWER BOUND (a read "
          f"through a non-`tests` module, or a ticker built at run time, is not seen), and the "
          f"value/invariant split is a mechanical heuristic, read each site before acting on it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
