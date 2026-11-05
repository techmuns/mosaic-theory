"""NO TEST READS A HELD NAME'S CIQ EXPORT — the guard on `tests/held_names.py`.

Three things are pinned here:

1. THE GUARD. No loop or parametrization over the committed pages or the CIQ folder, anywhere in
   `tests/`, lets its values reach code that can open a CIQ export without passing through
   `page_params` / `without_held`. A static scan (`unrouted`), with a positive and a negative pin
   for each shape it reads — the refused shapes are the ones that read BURL's real export on
   2026-11-05 (#911), copied from main `c4c9f432`.
2. THE HELPERS. A held name is skipped with the rule as its reason, or dropped before a loop body
   runs; every other value passes untouched, its case id unmoved.
3. THE BACKSTOP. The audit hook `tests/conftest.py` installs fails a test that opens a file in a
   held name's folder, before a byte is read, and lets every other open through.

WHAT THE SCAN CANNOT SEE (stated, not hidden): values that cross a module boundary — an
enumeration helper imported by another test module is judged in the module that defines it,
by the uses there; a production function that enumerates pages itself; a subprocess. The backstop
covers the first two in any linked run (it watches every open in the process); a subprocess runs
outside it — on main `c4c9f432` four tests run `vinci` in a child process, none on a held name.
"""
from __future__ import annotations

import ast
import os
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from tests import held_names as hn

ROOT = Path(__file__).resolve().parents[1]

# ==================================================================================================
# 1. THE GUARD — a static scan of the suite
# ==================================================================================================

#: Calls that enumerate a directory: `p.glob(..)`, `p.rglob(..)`, `p.iterdir()`, `os.listdir(p)`,
#: `os.scandir(p)`, `os.walk(p)`, `glob.glob(pattern)`.
_METHODS = frozenset({"glob", "rglob", "iterdir"})
_FUNCS = frozenset({"listdir", "scandir", "walk"})
#: A path into the committed pages (`data/dossiers`, `frontend/dossiers`) or into the CIQ folder
#: (`data/manual`), as a test spells it.
_PAGES = re.compile(r"""["'](?:data/|frontend/)?dossiers\b|["']dossiers["']""")
_CIQ = re.compile(r"""["']manual["']|\bdata/manual\b|\bmanual/ciq\b""")
#: Names whose use means the code can open a CIQ export: the store, the bundle, and every helper
#: of `tests/ciq_export_support.py` that builds one.
CIQ_READERS = frozenset({
    "LocalFolderStore", "CiqBundle", "export_sha", "page_export_sha", "skip_unless_pages_export",
    "skip_unless_export", "own_export_census", "archived_bundle", "archive_roots",
})
HELPERS = frozenset({"page_params", "without_held"})
#: Calls that pass an enumeration's items (or one of them) through unconsumed. Any other call an
#: enumeration passes into consumes it there — `CiqBundle.from_files(t, sorted(d.iterdir()))`
#: opens the files in that statement, whatever name the result is bound to.
_PASS_THROUGH = frozenset({"sorted", "list", "tuple", "set", "frozenset", "reversed", "filter",
                           "iter", "next", "enumerate", "zip"})


@dataclass(frozen=True)
class Site:
    """An enumeration the list does not see: where, over what, and the call as written."""
    path: str
    line: int
    root: str        # "pages" | "ciq"
    text: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line} [{self.root}] {self.text}"


def _call_name(node: ast.Call) -> str | None:
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


class _Module:
    """One test module's syntax tree, with what the scan asks of it."""

    def __init__(self, src: str) -> None:
        self.src = src
        self.lines = src.splitlines()
        self.tree = ast.parse(src)
        self.parents: dict[ast.AST, ast.AST] = {}
        self.defs: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {}
        self.uses: dict[str, list[ast.Name]] = {}
        #: (scope, name) -> every value assigned to the name in that scope (None: the module)
        self.binds: dict[tuple[ast.AST | None, str], list[ast.expr]] = {}
        self.params: dict[ast.AST, set[str]] = {}
        for node in ast.walk(self.tree):
            for child in ast.iter_child_nodes(node):
                self.parents[child] = node
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                self.defs.setdefault(node.name, []).append(node)
                a = node.args
                self.params[node] = {x.arg for x in (*a.posonlyargs, *a.args, *a.kwonlyargs)}
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                self.uses.setdefault(node.id, []).append(node)
            pairs: list[tuple[ast.expr, ast.expr]] = []
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Tuple) and isinstance(node.value, ast.Tuple) and len(
                            t.elts) == len(node.value.elts):
                        pairs += list(zip(t.elts, node.value.elts, strict=True))
                    else:
                        pairs.append((t, node.value))
            elif isinstance(node, ast.AnnAssign | ast.NamedExpr) and node.value is not None:
                pairs.append((node.target, node.value))
            for t, v in pairs:
                if isinstance(t, ast.Name):
                    self.binds.setdefault((self.enclosing_def(node), t.id), []).append(v)
        self._reach: dict[ast.AST, bool] = {}

    def values_of(self, name: ast.Name) -> list[ast.expr]:
        """The values ``name`` can hold where it is read: its own function's bindings (none, for
        a parameter), else an enclosing function's, else the module's."""
        scope = self.enclosing_def(name)
        while scope is not None:
            if (scope, name.id) in self.binds:
                return self.binds[(scope, name.id)]
            if name.id in self.params.get(scope, set()):
                return []
            scope = self.enclosing_def(scope)
        return self.binds.get((None, name.id), [])

    def root_of(self, expr: ast.AST, seen: frozenset[str] = frozenset()) -> str | None:
        """"ciq" / "pages" when ``expr`` is a path into the CIQ folder / the committed pages, read
        through the names it is built from; else None."""
        text = ast.get_source_segment(self.src, expr) or ""
        if _CIQ.search(text):
            return "ciq"
        if _PAGES.search(text):
            return "pages"
        for n in ast.walk(expr):
            if not isinstance(n, ast.Name) or n.id in seen:
                continue
            # a name's values, and — called — a function's results (`root = _root()`)
            vals = list(self.values_of(n))
            if isinstance(self.parents.get(n), ast.Call) and self.parents[n].func is n:  # type: ignore[attr-defined]
                vals += [r.value for d in self.defs.get(n.id, []) for r in ast.walk(d)
                         if isinstance(r, ast.Return) and r.value is not None
                         and self.enclosing_def(r) is d]
            for val in vals:
                got = self.root_of(val, seen | {n.id})
                if got:
                    return got
        return None

    def sites(self) -> list[tuple[ast.Call, str]]:
        out = []
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            recv: ast.AST | None = None
            if isinstance(f, ast.Attribute) and f.attr in _METHODS:
                recv = f.value
                if isinstance(recv, ast.Name) and recv.id == "glob" and node.args:
                    recv = node.args[0]     # glob.glob("data/dossiers/*")
            elif (isinstance(f, ast.Attribute) and f.attr in _FUNCS) or (
                    isinstance(f, ast.Name) and f.id in _FUNCS):
                recv = node.args[0] if node.args else None
            if recv is not None and (root := self.root_of(recv)):
                out.append((node, root))
        return out

    def reaches(self, node: ast.AST, seen: frozenset[str] = frozenset()) -> bool:
        """``node``'s code names a CIQ reader, spells a path into the CIQ folder, or calls (or
        takes as a fixture) a function of this module that does."""
        if node in self._reach:
            return self._reach[node]
        self._reach[node] = False          # a cycle reaches nothing new
        got = False
        for n in ast.walk(node):
            if (isinstance(n, ast.Name) and n.id in CIQ_READERS) or (
                    isinstance(n, ast.Attribute) and n.attr in CIQ_READERS):
                got = True
            elif isinstance(n, ast.Constant) and isinstance(n.value, str):
                got = bool(_CIQ.search(repr(n.value)))
            elif isinstance(n, ast.Name) and n.id not in seen:
                got = any(self.reaches(d, seen | {n.id}) for d in self.defs.get(n.id, [])) or any(
                    self.reaches(v, seen | {n.id}) for v in self.binds.get((None, n.id), []))
            if got:
                break
        if not got and isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            got = any(self.reaches(d, seen | {a.arg}) for a in node.args.args
                      if a.arg not in seen for d in self.defs.get(a.arg, []))
        self._reach[node] = got
        return got

    def stmt_of(self, node: ast.AST) -> ast.AST:
        while not isinstance(node, ast.stmt):
            node = self.parents[node]
        return node

    def enclosing_def(self, node: ast.AST) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        cur = node
        while cur in self.parents:
            cur = self.parents[cur]
            if isinstance(cur, ast.FunctionDef | ast.AsyncFunctionDef):
                return cur
        return None

    def route(self, node: ast.AST) -> str | None:
        """What ``node``'s value meets first on the way to its statement: "helper" (a held-list
        helper), "consumed" (any other call that is not a pass-through), or None."""
        cur = node
        while not isinstance(cur, ast.stmt):
            cur = self.parents[cur]
            if isinstance(cur, ast.Call):
                name = _call_name(cur)
                if name in HELPERS:
                    return "helper"
                if name not in _PASS_THROUGH:
                    return "consumed"
        return None

    def inert(self, node: ast.AST) -> bool:
        """``node`` is only asked whether it is empty, or how long it is — `assert pages`,
        `if not pages`, `len(pages)` — so none of its names reach anything."""
        parent = self.parents.get(node)
        if isinstance(parent, ast.Assert | ast.If | ast.IfExp | ast.While) and parent.test is node:
            return True
        if isinstance(parent, ast.UnaryOp) and isinstance(parent.op, ast.Not):
            return True
        return isinstance(parent, ast.Call) and _call_name(parent) in ("len", "bool") and (
            parent.args == [node])

    def declared_json_only(self, node: ast.AST) -> bool:
        """``node``'s statement (a decorator's own lines, for a parametrization) carries the
        committed-JSON-only declaration."""
        stmt = self.stmt_of(node)
        if isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):     # in a decorator
            first, last = node.lineno, node.end_lineno or node.lineno     # type: ignore[attr-defined]
        else:
            first, last = stmt.lineno, stmt.end_lineno or stmt.lineno     # type: ignore[attr-defined]
            body = getattr(stmt, "body", None)
            if isinstance(body, list) and body:                          # a header's lines only
                last = max(first, body[0].lineno - 1)
        # on the statement's own lines, or alone on the line above it
        above = self.lines[first - 2].strip() if first >= 2 else ""
        return above == hn.NO_CIQ_READ or any(
            hn.NO_CIQ_READ in self.lines[i - 1] for i in range(first, last + 1))

    def leaks(self, node: ast.AST, *, ciq: bool, seen: frozenset[str] = frozenset()) -> bool:
        """``node``'s values reach code that can open a CIQ export without passing a helper.
        ``ciq``: they come from the CIQ folder itself, so every consumer counts and no
        committed-JSON-only declaration applies."""
        route = self.route(node)
        if route == "helper" or self.inert(node) or (not ciq and self.declared_json_only(node)):
            return False
        stmt = self.stmt_of(node)
        name: str | None = None
        scope = self.enclosing_def(stmt)
        if route == "consumed":
            pass
        elif isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(
                stmt.targets[0], ast.Name):
            name = stmt.targets[0].id
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            name = stmt.target.id
        elif isinstance(stmt, ast.Return) and scope is not None:
            name, scope = scope.name, None
        if name is not None:
            # bound to a name (or returned): judged at every use — inside the function that
            # binds it, or anywhere in the module for a module-level name or a function's result
            if name in seen:
                return False
            consumers: list[ast.AST] = []
            for u in self.uses.get(name, []):
                if scope is not None and self.enclosing_def(u) is not scope:
                    continue
                call = self.parents.get(u)
                # a function's result is its CALL: follow on from there
                consumers.append(call if isinstance(call, ast.Call) and call.func is u
                                 and isinstance(stmt, ast.Return) else u)
            return any(self.leaks(u, ciq=ciq, seen=seen | {name}) for u in consumers)
        if ciq:
            return True
        # consumed in this statement, by the function it sits in (a decorator's: by its test)
        fn = self.enclosing_def(node)
        return self.reaches(fn if fn is not None else self.tree)


    def exports(self) -> dict[str, str]:
        """The module-level names (and functions) another module can import an enumeration's
        values through, each with its root: bound to one at module level, or returned by a
        top-level function, through pass-throughs only."""
        out: dict[str, str] = {}
        todo: list[tuple[ast.AST, str]] = list(self.sites())
        while todo:
            node, root = todo.pop()
            if self.route(node) is not None:
                continue
            stmt = self.stmt_of(node)
            name: str | None = None
            if isinstance(stmt, ast.Assign | ast.AnnAssign) and self.enclosing_def(stmt) is None:
                targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                if len(targets) == 1 and isinstance(targets[0], ast.Name):
                    name = targets[0].id
            elif isinstance(stmt, ast.Return):
                fn = self.enclosing_def(stmt)
                if fn is not None and self.enclosing_def(fn) is None:
                    name = fn.name
            if name is None or name in out:
                continue
            out[name] = root
            for u in self.uses.get(name, []):
                if self.enclosing_def(u) is None:
                    call = self.parents.get(u)
                    use = call if isinstance(call, ast.Call) and call.func is u else u
                    todo.append((use, root))
        return out

    def imported_leaks(self, path: str, exports: dict[str, dict[str, str]]) -> list[Site]:
        """Every name this module imports from another test module's ``exports`` whose values
        reach a CIQ reader here without a helper."""
        out = []
        for node in ast.walk(self.tree):
            if not (isinstance(node, ast.ImportFrom) and node.module
                    and node.module.startswith("tests.")):
                continue
            theirs = exports.get(node.module.removeprefix("tests."), {})
            for alias in node.names:
                root = theirs.get(alias.name)
                if root is None:
                    continue
                local = alias.asname or alias.name
                uses: list[ast.AST] = []
                for u in self.uses.get(local, []):
                    call = self.parents.get(u)
                    uses.append(call if isinstance(call, ast.Call) and call.func is u else u)
                if any(self.leaks(u, ciq=root == "ciq") for u in uses):
                    out.append(Site(path, node.lineno, root,
                                    f"{alias.name}, imported from {node.module}"))
        return out


def unrouted(path: str, src: str) -> list[Site]:
    """Every enumeration over the committed pages or the CIQ folder in ``src`` whose values reach
    code that can open a CIQ export without passing through `page_params` / `without_held`. A
    page enumeration may instead declare it reads committed JSON only; a CIQ-folder one may not."""
    mod = _Module(src)
    out = []
    for call, root in mod.sites():
        if mod.leaks(call, ciq=root == "ciq"):
            text = (ast.get_source_segment(src, call) or "").replace("\n", " ")
            out.append(Site(path, call.lineno, root, text[:100]))
    return sorted(out, key=lambda s: s.line)


def scan_suite(sources: dict[str, str]) -> list[Site]:
    """`unrouted` over every module, plus every enumeration's values imported from one test
    module into another and consumed there without a helper."""
    mods = {path: _Module(src) for path, src in sources.items()}
    exports = {Path(path).stem: mod.exports() for path, mod in mods.items()}
    bad = [s for path, src in sources.items() for s in unrouted(path, src)]
    bad += [s for path, mod in mods.items() for s in mod.imported_leaks(path, exports)]
    return bad


def _suite() -> list[Path]:
    """Every test-suite module the scan reads: `tests/*.py` and below, but `held_names.py` itself
    (it holds the helpers) and the fixtures generator directory."""
    return sorted(p for p in (ROOT / "tests").rglob("*.py")
                  if p.name != "held_names.py" and "fixtures" not in p.relative_to(ROOT).parts)


def test_no_loop_or_parametrization_over_pages_or_ciq_folders_bypasses_the_held_list() -> None:
    """THE GUARD. Every enumeration of the committed pages or the CIQ folder whose names reach a
    CIQ reader goes through `tests/held_names.py`, so no held name's export is opened."""
    files = _suite()
    assert len(files) > 300, f"scanned only {len(files)} modules — the suite moved?"
    bad = scan_suite({str(f.relative_to(ROOT)): f.read_text() for f in files})
    assert not bad, (
        f"{len(bad)} enumeration(s) over pages or CIQ folders reach a CIQ reader without the held "
        "list. Wrap a parametrization's values in page_params(...), a loop's in without_held(...)"
        f" (tests/held_names.py); a page loop that reads committed JSON only may instead carry "
        f"`{hn.NO_CIQ_READ}` on its statement:\n" + "\n".join(map(str, bad)))


def _scan(src: str) -> list[str]:
    return [s.text for s in unrouted("t.py", textwrap.dedent(src))]


#: The loop that read BURL's real export on 2026-11-05: `test_ev_bridge.py` at main `c4c9f432`,
#: `test_claims_equal_ciqs_current_figure_on_every_committed_name`, as written.
_EV_BRIDGE_LOOP = '''
    def test_claims_equal_ciqs_current_figure_on_every_committed_name() -> None:
        from vinci.dossier.ciq import CiqBundle

        root = ROOT / "data" / "manual" / "ciq"
        if not root.is_dir():
            pytest.skip("no CIQ exports on this machine")
        compared = 0
        for page in {pages}:
            folder = root / page.name
            if not folder.is_dir():
                continue
            b = CiqBundle.from_files(page.name, sorted(p for p in {files} if p.is_file()))
            compared += 1
'''


def test_the_loop_that_read_burl_is_refused_and_its_routed_form_is_not() -> None:
    """⊖/⊕ on the real shape. As written on main it is refused at both enumerations — the pages
    and the page's CIQ folder; routed through `without_held`, neither is."""
    raw = _scan(_EV_BRIDGE_LOOP.format(pages='sorted((ROOT / "data" / "dossiers").iterdir())',
                                       files="folder.iterdir()"))
    assert raw == ['(ROOT / "data" / "dossiers").iterdir()', "folder.iterdir()"]
    routed = _scan(_EV_BRIDGE_LOOP.format(
        pages='without_held(sorted((ROOT / "data" / "dossiers").iterdir()))',
        files="without_held(folder.iterdir())"))
    assert routed == []


#: The per-page parametrization that ran a CIQ reader on BURL: `test_forward_consensus.py` at
#: `c4c9f432` (eleven modules carry the same shape).
_PER_PAGE = '''
    from vinci.dossier.manual_store import LocalFolderStore

    COMMITTED = sorted(p.parent.name for p in (ROOT / "data" / "dossiers").glob("*/dossier.json")
                       if "forward_consensus" in json.loads(p.read_text()))

    @pytest.mark.parametrize("ticker", {values})
    def test_every_spread_sits_on_its_own_trends_figure(ticker: str) -> None:
        files = LocalFolderStore.from_config().files(ticker)
'''


def test_a_per_page_parametrization_into_a_ciq_reader_is_refused_unless_it_takes_page_params(
) -> None:
    """⊖/⊕ The module-level page list is judged at its use: raw into a test that reads the store,
    refused; through `page_params`, not."""
    assert _scan(_PER_PAGE.format(values="COMMITTED")) == [
        '(ROOT / "data" / "dossiers").glob("*/dossier.json")']
    assert _scan(_PER_PAGE.format(values="page_params(COMMITTED)")) == []


#: A CIQ-folder loop through a helper: `test_capital_panel_selection.py::_bundles` at `c4c9f432`
#: (the helper `test_liquidity_line.py` imports), as written.
_CIQ_FOLDERS = '''
    def _root():
        r = get_config().data_dir / "manual" / "ciq"
        if not r.is_dir() or not any({probe}):
            pytest.skip("licensed CIQ bundles unavailable (never committed)")
        return r

    def _bundles() -> list[tuple[str, CiqBundle]]:
        root = _root()
        ms = LocalFolderStore(root)
        out = []
        for tk in sorted(p.name for p in {listing} if p.is_dir()):
            files = ms.files(tk)
            if files:
                out.append((tk, CiqBundle.from_files(tk, files)))
        return out
'''


def test_a_loop_over_the_ciq_folder_is_refused_unless_it_takes_without_held() -> None:
    """⊖/⊕ Every enumeration of the CIQ folder goes through the list — the existence probe too,
    so a folder holding only held names reads as empty."""
    assert _scan(_CIQ_FOLDERS.format(probe="r.iterdir()", listing="root.iterdir()")) == [
        "r.iterdir()", "root.iterdir()"]
    assert _scan(_CIQ_FOLDERS.format(probe="without_held(r.iterdir())",
                                     listing="without_held(root.iterdir())")) == []


def test_the_committed_json_declaration_frees_a_page_loop_but_never_a_ciq_folder_loop() -> None:
    """⊕ A page loop in a test that also reads CIQ may declare it reads committed JSON only.
    ⊖ The same declaration on a CIQ-folder enumeration is ignored: that folder IS the exports."""
    page_loop = f'''
        def test_pages_and_store() -> None:
            store = LocalFolderStore.from_config()
            for p in sorted(DOSS.glob("*/dossier.json")):  {hn.NO_CIQ_READ}
                json.loads(p.read_text())
        DOSS = ROOT / "data" / "dossiers"
    '''
    assert _scan(page_loop) == []
    assert _scan(page_loop.replace(f"  {hn.NO_CIQ_READ}", "")) == [
        'DOSS.glob("*/dossier.json")']
    ciq_loop = f'''
        def test_folders() -> None:
            for d in sorted(CIQ.iterdir()):  {hn.NO_CIQ_READ}
                CiqBundle.from_files(d.name, [])
        CIQ = ROOT / "data" / "manual" / "ciq"
    '''
    assert _scan(ciq_loop) == ["CIQ.iterdir()"]


def test_asking_whether_a_list_is_empty_reads_none_of_it() -> None:
    """⊕ `assert pages`, `if not pages`, `len(pages)` in a test that reads the store pass no name
    on. ⊖ The same list iterated there does."""
    src = '''
        PAGES = sorted(p.parent.name for p in (ROOT / "data" / "dossiers").glob("*/dossier.json"))

        def test_store() -> None:
            assert PAGES, "no pages"
            if not PAGES or len(PAGES) < 20:
                pytest.skip("few pages")
            store = LocalFolderStore.from_config()
            {tail}
    '''
    assert _scan(src.format(tail="store.files('AMZN')")) == []
    assert _scan(src.format(tail="[store.files(t) for t in PAGES]")) == [
        '(ROOT / "data" / "dossiers").glob("*/dossier.json")']


def test_the_declaration_may_sit_alone_on_the_line_above() -> None:
    """⊕ A statement too long to carry it takes the declaration on its own line above — and only
    directly above: a line further up declares nothing."""
    src = f'''
        def test_pages_and_store() -> None:
            store = LocalFolderStore.from_config()
            {{gap}}{hn.NO_CIQ_READ}
            {{pad}}for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
                json.loads(p.read_text())
    '''
    assert _scan(src.format(gap="", pad="")) == []
    assert _scan(src.format(gap="", pad="x = 1\n            ")) == [
        '(ROOT / "data" / "dossiers").glob("*/dossier.json")']


def test_a_page_loop_that_reaches_no_ciq_reader_is_left_alone() -> None:
    """⊕ The committed page is not the export: a test that enumerates pages and reads only their
    JSON keeps the held pages, undeclared — even in a module whose OTHER tests read the store."""
    src = '''
        def test_every_page_parses() -> None:
            for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
                assert json.loads(p.read_text())

        def test_amzn_store() -> None:
            LocalFolderStore.from_config().files("AMZN")
    '''
    assert _scan(src) == []


def test_a_helper_that_returns_the_pages_is_judged_where_it_is_called() -> None:
    """⊖ A helper's result is followed to its callers: raw into a CIQ reader, refused (at the
    helper's enumeration); wrapped at the call, not. ⊕ A caller that reads no CIQ is not a leak."""
    src = '''
        def _pages() -> list[Path]:
            return sorted((ROOT / "data" / "dossiers").iterdir())

        def test_store() -> None:
            for d in {call}:
                LocalFolderStore.from_config().files(d.name)

        def test_names() -> None:
            assert len(_pages()) > 20
    '''
    assert _scan(src.format(call="_pages()")) == ['(ROOT / "data" / "dossiers").iterdir()']
    assert _scan(src.format(call="without_held(_pages())")) == []


def test_the_scan_reads_the_shapes_the_suite_uses_for_paths() -> None:
    """⊖ Each spelling of the two roots the suite uses is recognised: a relative string, a
    `get_config().data_dir` chain, `frontend/dossiers` and `os.listdir`."""
    for receiver in ('Path("data/dossiers")', 'Path("frontend/dossiers")',
                     'get_config().data_dir / "dossiers"', 'Path("data/manual/ciq")',
                     'get_config().data_dir / "manual" / "ciq"'):
        src = f'''
            def test_x() -> None:
                for p in sorted(({receiver}).iterdir()):
                    CiqBundle.from_files(p.name, [])
        '''
        assert _scan(src) == [f"({receiver}).iterdir()"], receiver
    src = '''
        def test_x() -> None:
            for n in os.listdir("data/manual/ciq"):
                CiqBundle.from_files(n, [])
    '''
    assert _scan(src) == ['os.listdir("data/manual/ciq")']


def test_the_scan_does_not_mistake_another_folder_for_the_pages() -> None:
    """⊕ A fixture folder named for CIQ, or the scenarios folder, is neither root."""
    src = '''
        FIX = ROOT / "tests" / "fixtures" / "ciq_synthetic"

        def test_x() -> None:
            for p in sorted(FIX.iterdir()):
                CiqBundle.from_files("ZZFX", [p])
            for p in sorted((ROOT / "scenarios").glob("*.json")):
                CiqBundle.from_files(p.stem, [])
    '''
    assert _scan(src) == []


# ==================================================================================================
# 2. THE HELPERS
# ==================================================================================================

def test_the_list_is_the_six_audit_packs() -> None:
    """The list lifts by a deliberate edit of BOTH this pin and `HELD_NAMES` — never by one line
    nobody reviewed (TeamNostra's packs, exported 2026-10-28)."""
    the_six = {"BURL", "MTB", "RIVN", "PCVX", "NVO", "PLD"}
    assert the_six == hn.HELD_NAMES


@pytest.mark.parametrize("item", [
    "BURL", "burl", Path("data/dossiers/BURL"), Path("data/dossiers/BURL/dossier.json"),
    "frontend/dossiers/BURL.json", Path("data/manual/ciq/BURL"),
    Path("data/manual/ciq/BURL/Burlington Stores Inc NYSE BURL Financials_Annual.xls"),
    Path("data/manual/ciq-archive/replaced-2026-10-28/BURL/x.xls"), ("BURL", 3), (7, "MTB"),
])
def test_every_shape_an_enumeration_yields_names_its_held_ticker(item: object) -> None:
    assert hn.held_in(item) in hn.HELD_NAMES


@pytest.mark.parametrize("item", [
    "AMZN", "BURLX", Path("data/dossiers/TJX/dossier.json"), "frontend/dossiers/ROST.json",
    Path("data/manual/ciq/TJX/BURL Customers.rtf"), Path("data/manual/ciq/TJX"), ("TJX", "x"), 3,
])
def test_no_other_shape_is_taken_for_a_held_name(item: object) -> None:
    """⊕ A file in another name's folder that merely MENTIONS a held ticker is not held: only a
    folder, a whole ticker string or a page's own file names one."""
    assert hn.held_in(item) is None


def test_page_params_skips_a_held_case_with_the_rule_and_moves_no_id() -> None:
    got = hn.page_params(["AMZN", "BURL", ("TJX", 1), ("NVO", 2)])
    assert got[0] == "AMZN" and got[2] == ("TJX", 1)
    for case, values in ((got[1], ("BURL",)), (got[3], ("NVO", 2))):
        assert case.values == values
        (mark,) = case.marks
        assert mark.name == "skip" and "held audit pack" in mark.kwargs["reason"]
        assert "tests/held_names.py" in mark.kwargs["reason"]
    kept = pytest.param("X", id="x")
    assert hn.page_params([kept]) == [kept]
    (held,) = hn.page_params([pytest.param("PLD", id="pld")])
    assert held.id == "pld" and held.marks[-1].name == "skip"


def test_without_held_drops_a_held_name_and_records_where() -> None:
    before = len(hn.LEFT_OUT)
    got = hn.without_held([Path("d/AMZN"), Path("d/BURL"), Path("d/RIVN/x.xls"), Path("d/TJX")])
    assert got == [Path("d/AMZN"), Path("d/TJX")]
    assert [t for _, t in hn.LEFT_OUT[before:]] == ["BURL", "RIVN"]
    assert all("test_without_held_drops_a_held_name_and_records_where" in w
               for w, _ in hn.LEFT_OUT[before:])
    del hn.LEFT_OUT[before:]


def test_skip_if_held_skips_with_the_rule() -> None:
    hn.skip_if_held("AMZN")          # no skip
    with pytest.raises(pytest.skip.Exception, match="held audit pack"):
        hn.skip_if_held(Path("data/dossiers/PCVX/dossier.json"))


# ==================================================================================================
# 3. THE BACKSTOP — the audit hook, through a real open()
# ==================================================================================================

@pytest.fixture
def fake_ciq(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fake CIQ folder standing in for `data/manual`, and the hook pointed at it. Every file is
    a sentinel: no export is ever involved."""
    manual = tmp_path / "manual"
    for rel in ("ciq/BURL/s.xls", "ciq/TJX/s.xls", "ciq/TJX/BURL Customers.rtf",
                "ciq-archive/replaced-2026-10-28/MTB/s.xls"):
        (manual / rel).parent.mkdir(parents=True, exist_ok=True)
        (manual / rel).write_text("SENTINEL")
    roots, held = hn.ciq_roots(manual)
    monkeypatch.setattr(hn, "CIQ_ROOTS", roots)
    monkeypatch.setattr(hn, "HELD_FOLDERS", held)
    return manual


def _refused(path: Path) -> bool:
    before = len(hn.REFUSED_OPENS)
    try:
        with open(path, encoding="utf-8") as fh:
            fh.read()
    except pytest.fail.Exception:
        assert hn.REFUSED_OPENS[before:] and hn.REFUSED_OPENS[-1][1] == os.path.abspath(path)
        del hn.REFUSED_OPENS[before:]     # this pin's own refusal, not a leak
        return True
    assert len(hn.REFUSED_OPENS) == before
    return False


def test_the_hook_refuses_an_open_in_a_held_folder_before_it_reads(fake_ciq: Path) -> None:
    """⊖ A live folder, the archive, a path spelled relative, and another case: all refused."""
    assert _refused(fake_ciq / "ciq" / "BURL" / "s.xls")
    assert _refused(fake_ciq / "ciq-archive" / "replaced-2026-10-28" / "MTB" / "s.xls")
    assert _refused(Path(os.path.relpath(fake_ciq / "ciq" / "BURL" / "s.xls")))
    if (fake_ciq / "ciq" / "burl").exists():          # a case-insensitive disk (macOS)
        assert _refused(fake_ciq / "ciq" / "burl" / "s.xls")


def test_the_hook_lets_every_other_open_through(fake_ciq: Path, tmp_path: Path) -> None:
    """⊕ Another name's export, a file there that names a held ticker, a held-named file outside
    the CIQ folder, and a listing of the held folder (names only, no export read)."""
    assert not _refused(fake_ciq / "ciq" / "TJX" / "s.xls")
    assert not _refused(fake_ciq / "ciq" / "TJX" / "BURL Customers.rtf")
    elsewhere = tmp_path / "elsewhere" / "BURL" / "s.xls"
    elsewhere.parent.mkdir(parents=True)
    elsewhere.write_text("x")
    assert not _refused(elsewhere)
    assert [p.name for p in (fake_ciq / "ciq" / "BURL").iterdir()] == ["s.xls"]


def test_the_hook_follows_a_held_folder_that_is_a_link(tmp_path: Path,
                                                        monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ A held name's folder linked to a target whose path carries no ticker: an open through the
    resolved target is still refused."""
    target = tmp_path / "Drive" / "Burlington Stores"
    target.mkdir(parents=True)
    (target / "s.xls").write_text("SENTINEL")
    (tmp_path / "manual" / "ciq").mkdir(parents=True)
    (tmp_path / "manual" / "ciq" / "BURL").symlink_to(target)
    roots, held = hn.ciq_roots(tmp_path / "manual")
    monkeypatch.setattr(hn, "CIQ_ROOTS", roots)
    monkeypatch.setattr(hn, "HELD_FOLDERS", held)
    assert _refused(target / "s.xls")
    assert _refused(tmp_path / "manual" / "ciq" / "BURL" / "s.xls")


def test_the_hook_is_installed_on_this_checkout() -> None:
    """The backstop watches this checkout's own `data/manual`, whether or not it exists."""
    assert str(ROOT / "data" / "manual") + os.sep in hn.CIQ_ROOTS


# ==================================================================================================
# 4. THE ARCHIVE SEARCH LISTS NO HELD FOLDER
# ==================================================================================================

def _archive(tmp_path: Path) -> Path:
    root = tmp_path / "ciq-archive"
    for rel in ("replaced-2026-10-28/SMPL/a.xls", "replaced-2026-10-28/BURL/a.xls",
                "replaced-2026-11-04/SMPL/a.xls", "kept/deeper/SMPL/a.xls",
                "replaced-x/NFLX/a.xls"):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text("SENTINEL")
    (root / "linked").mkdir()
    (root / "linked" / "SMPL").symlink_to(root / "replaced-2026-11-04" / "SMPL")
    return root


def test_the_archive_search_finds_what_rglob_finds(tmp_path: Path) -> None:
    """⊕ Same folders as the `rglob` it replaced, nested and linked ones included, for a name
    that is not held."""
    from tests.ciq_export_support import archived_folders

    root = _archive(tmp_path)
    for t in ("SMPL", "NFLX", "TJX"):
        assert archived_folders(root, t) == sorted(p for p in root.rglob(t) if p.is_dir()), t


def test_the_archive_search_never_lists_a_held_folder(tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ No listing of an archived held folder, whichever name is searched — and a held name
    searched for finds nothing."""
    from tests.ciq_export_support import archived_folders

    root = _archive(tmp_path)
    listed: list[str] = []
    real = os.scandir

    def spy(path: Any = ".") -> Any:
        listed.append(os.fspath(path))
        return real(path)

    monkeypatch.setattr(os, "scandir", spy)
    assert archived_folders(root, "SMPL")
    assert archived_folders(root, "BURL") == []
    assert listed and not [p for p in listed if "BURL" in Path(p).parts]
