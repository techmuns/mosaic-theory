"""THE OUTCOME FENCES for the modules that had none — the screen gate, the cohort split, the trigger
evaluator and the scenario records may not reach forward-return data by any import path.

§7: no code path reads forward returns when setting a parameter. The ranker, themes, dossier and
sleeve registry each carry an AST fence saying so (`tests/test_rank.py`, `test_themes.py`,
`test_dossier.py`, `test_sleeves.py`). Verified 2026-10-26: no fence named `vinci/screens/`,
`vinci/cohort.py`, `vinci/triggers.py` or `vinci/scenarios.py`, and every gate, threshold and
trigger criterion those four hold is a parameter of exactly that kind.

WHAT IS THE OUTCOME LAYER. `vinci.scoring` (the BUY−AVOID spread at each horizon), `vinci.ledger`
(the verdict-write workflow) and `vinci.monitor`, which computes the interim spread, every leg's
excess return and the realized P&L. The older fences name only the first two.

THE MONITOR IS NOT FENCED LIKE THE OTHERS, AND CANNOT BE: it IS where forward returns are
computed (its own docstring), so "the monitor reads no returns" would be false by construction.
Its fence points the other way. It reports what has happened "without ever touching the frozen
record", so it must not reach a ledger WRITE path.

TRANSITIVE, NOT ONLY DIRECT. A direct-import fence is bypassed by one intermediate module:
`vinci/prose_lint.py` is fenced by nothing and `vinci.scenarios` imports it, so an outcome import
added there leaves every direct fence green. So the closure is walked here, lazy imports and
package `__init__` files included. `if TYPE_CHECKING:` imports are counted too, although they
never execute. That errs toward red: the ranker's TYPE_CHECKING import of `vinci.screens` reads
as reaching `vinci.store`, while a fresh `import vinci.rank` loads neither. `vinci.schemas.ledger`
is banned DIRECTLY only, because `vinci/schemas/__init__.py` re-exports it and any
`vinci.schemas.*` import therefore loads it.

WHICH HALF THIS COVERS: imports, static and literal-string dynamic, and attribute chains through
an imported name (`schemas.LedgerEntry` after `from vinci import schemas`); the Store's two ledger
readers by attribute name; and `decision_ledger` named in code (raw SQL, or the committed JSONL
by path), docstrings excepted. A path built from parts, `getattr` with a computed name, or a read
of `data/monitor/*.json` or the scoring report is NOT caught. None of the four does today (grep,
2026-10-26).
"""

from __future__ import annotations

import ast
import functools
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
VINCI = ROOT / "vinci"

OUTCOME_LAYER = ("vinci.scoring", "vinci.ledger", "vinci.monitor")
DIRECT_ONLY = ("vinci.schemas.ledger",)
LEDGER_WRITE_PATHS = ("vinci.ledger", "vinci.store")
#: `Store` is a legitimate import of the screen (prices, candidates), and it also READS the ledger.
STORE_LEDGER_READERS = frozenset({"iter_ledger", "get_ledger_entry"})

FENCED = ("vinci.screens", "vinci.cohort", "vinci.triggers", "vinci.scenarios")


def _module_name(path: pathlib.Path) -> str:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


MODULES: dict[str, pathlib.Path] = {_module_name(p): p for p in VINCI.rglob("*.py")}


def _top_level_names(path: pathlib.Path) -> set[str]:
    out: set[str] = set()
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            out.add(node.name)
        elif isinstance(node, ast.Assign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            out.update(t.id for t in targets if isinstance(t, ast.Name))
    return out


#: `from vinci.schemas import LedgerEntry` reaches the row type through the package's re-export,
#: and reads as `vinci.schemas.LedgerEntry` — so every name the ledger schema defines is banned
#: under the package too, not only under its own module path.
LEDGER_SCHEMA_REEXPORTS = frozenset(
    f"vinci.schemas.{n}" for n in _top_level_names(MODULES["vinci.schemas.ledger"]))


def _under(name: str, layer: tuple[str, ...]) -> bool:
    return any(name == m or name.startswith(m + ".") for m in layer)


def _files(name: str) -> list[pathlib.Path]:
    """A package's every module, or one module's file."""
    pkg = VINCI.joinpath(*name.split(".")[1:])
    return sorted(pkg.rglob("*.py")) if pkg.is_dir() else [MODULES[name]]


def imported_names(src: str, *, module: str, is_package: bool = False) -> set[str]:
    """Every dotted name ``src`` imports — `import a.b`, `from a import b` (as `a` AND `a.b`, so
    `from vinci import scoring` is seen), relative imports resolved against ``module``, imports
    inside functions, and `importlib.import_module("…")` / `__import__("…")` with a literal.

    PLUS every attribute chain rooted in a name an import bound, resolved to its dotted target:
    `from vinci import schemas` then `schemas.LedgerEntry` yields `vinci.schemas.LedgerEntry`.
    A package import is a handle on everything the package re-exports (Codex P2 on #800)."""
    pkg = module if is_package else module.rpartition(".")[0]
    tree = ast.parse(src)
    out: set[str] = set()
    bound: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name)
                head = a.name.split(".")[0]
                bound[a.asname or head] = a.name if a.asname else head
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = pkg.split(".")
                anchor = ".".join(parts[: len(parts) - (node.level - 1)])
                base = f"{anchor}.{base}" if base else anchor
            out.add(base)
            for a in node.names:
                out.add(f"{base}.{a.name}")
                bound[a.asname or a.name] = f"{base}.{a.name}"
        elif isinstance(node, ast.Call):
            fn = node.func
            called = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
            arg = node.args[0] if node.args else None
            if (called in ("import_module", "__import__") and isinstance(arg, ast.Constant)
                    and isinstance(arg.value, str)):
                out.add(arg.value)
    for node in ast.walk(tree):
        attrs: list[str] = []
        root: ast.expr = node if isinstance(node, ast.Attribute) else ast.Constant(None)
        while isinstance(root, ast.Attribute):
            attrs.append(root.attr)
            root = root.value
        if attrs and isinstance(root, ast.Name) and root.id in bound:
            out.add(".".join([bound[root.id], *reversed(attrs)]))
    return out


@functools.cache
def _vinci_deps(name: str) -> frozenset[str]:
    """The repo modules loading ``name`` loads directly — each imported name resolved to every
    known module on its dotted path, since importing `a.b.c` executes `a` and `a.b` too."""
    path = MODULES[name]
    deps: set[str] = set()
    for imp in imported_names(path.read_text(), module=name,
                              is_package=path.name == "__init__.py"):
        parts = imp.split(".")
        deps.update(c for i in range(1, len(parts) + 1) if (c := ".".join(parts[:i])) in MODULES)
    return frozenset(deps)


def reach(start: str) -> dict[str, str | None]:
    """Every repo module that loading ``start`` loads, mapped to the module that pulled it in."""
    via: dict[str, str | None] = {start: None}
    stack = [start]
    while stack:
        here = stack.pop()
        for dep in _vinci_deps(here):
            if dep not in via:
                via[dep] = here
                stack.append(dep)
    return via


def _chain(via: dict[str, str | None], end: str) -> str:
    links: list[str] = []
    node: str | None = end
    while node is not None:
        links.append(node)
        node = via[node]
    return " <- ".join(links)


# --- the fences ---------------------------------------------------------------------------------

@pytest.mark.parametrize("target", FENCED)
def test_no_gate_or_threshold_module_imports_the_outcome_layer(target: str) -> None:
    """Direct imports, file by file — the existing fences' shape, with the monitor added to the
    outcome layer and `vinci.schemas.ledger` (the row type, close rows' exit prices) beside it."""
    files = _files(target)
    assert files, f"{target}: the fence walked no file"
    for path in files:
        name = _module_name(path)
        hits = sorted(m for m in imported_names(path.read_text(), module=name,
                                                is_package=path.name == "__init__.py")
                      if _under(m, OUTCOME_LAYER + DIRECT_ONLY) or m in LEDGER_SCHEMA_REEXPORTS)
        assert not hits, (f"{path.relative_to(ROOT)} imports {hits} — a gate, threshold or "
                          f"trigger must never be able to read forward returns (§7)")


@pytest.mark.parametrize("target", FENCED)
def test_no_gate_or_threshold_module_reaches_the_outcome_layer_through_another(
        target: str) -> None:
    """The same line, held through every intermediate module: a direct-only fence is one
    re-export away from green while the line is crossed."""
    for path in _files(target):
        via = reach(_module_name(path))
        crossed = sorted(m for m in via if _under(m, OUTCOME_LAYER))
        assert not crossed, ("forward-return data is reachable: "
                             + "; ".join(_chain(via, m) for m in crossed))


def _docstring_nodes(tree: ast.Module) -> set[int]:
    owners = [tree, *(n for n in ast.walk(tree)
                      if isinstance(n, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef))]
    return {id(o.body[0].value) for o in owners
            if o.body and isinstance(o.body[0], ast.Expr)
            and isinstance(o.body[0].value, ast.Constant)}


@pytest.mark.parametrize("target", FENCED)
def test_no_gate_or_threshold_module_reads_the_ledger_through_the_store(target: str) -> None:
    """`vinci.screens.run` imports `Store` for prices and candidates, and `Store` also reads every
    logged verdict and close. The import is allowed; the two ledger readers are not, and neither is
    the table or file named in code (raw SQL on the Store's connection, or the committed JSONL by
    path). A docstring may name it."""
    for path in _files(target):
        tree = ast.parse(path.read_text())
        used = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        assert not (used & STORE_LEDGER_READERS), (
            f"{path.relative_to(ROOT)} calls {sorted(used & STORE_LEDGER_READERS)} — the ledger's "
            f"rows carry entry and exit prices, i.e. the outcome")
        docs = _docstring_nodes(tree)
        named = [n.lineno for n in ast.walk(tree)
                 if isinstance(n, ast.Constant) and isinstance(n.value, str)
                 and "decision_ledger" in n.value and id(n) not in docs]
        assert not named, (f"{path.relative_to(ROOT)} names `decision_ledger` in code at line(s) "
                           f"{named} — the ledger read by SQL or by file")


def test_the_monitor_cannot_reach_a_ledger_write_path() -> None:
    """The monitor's fence points the other way (module docstring): it computes returns, and it
    must never be able to change the record it measures."""
    via = reach("vinci.monitor")
    crossed = sorted(m for m in via if _under(m, LEDGER_WRITE_PATHS))
    assert not crossed, "the monitor reaches a ledger writer: " + "; ".join(
        _chain(via, m) for m in crossed)


# --- the walker can find what it looks for (corpus before synthetic) ------------------------------

def test_the_walker_finds_the_outcome_edges_the_live_tree_really_has() -> None:
    """A fence that finds nothing is suspect until shown it can find something. These edges are
    REAL and legitimate today: the CLI drives scoring and the ledger, and the dossier takes the
    cap-band policy from the monitor. If the walker stopped seeing them, every fence above would
    pass vacuously."""
    assert {"vinci.scoring", "vinci.ledger", "vinci.monitor"} <= set(reach("vinci.cli"))
    via = reach("vinci.dossier.mechanical")
    assert "vinci.monitor" in via and via["vinci.monitor"] == "vinci.dossier.mechanical"
    assert {"vinci.store", "vinci.store.store"} <= set(reach("vinci.screens"))
    assert len(reach("vinci.triggers")) > 20, "triggers → scenarios → dossier: the walk stopped"


def test_the_fences_scan_the_modules_they_name() -> None:
    scanned = {p.name for t in FENCED for p in _files(t)}
    assert {"screen2.py", "run.py", "assemble.py", "retention.py", "annotations.py",
            "cohort.py", "triggers.py", "scenarios.py"} <= scanned


# --- the parser: every import shape that crosses the line is seen -------------------------------

@pytest.mark.parametrize("src", [
    "import vinci.scoring",
    "import vinci.scoring.metrics as m",
    "from vinci.scoring import score_ledger",
    "from vinci import scoring",
    "from vinci import monitor as mon",
    "def f():\n    from vinci.monitor import compute_spread\n",
    "import importlib\nimportlib.import_module('vinci.ledger.workflow')",
    "__import__('vinci.scoring')",
    "from ..scoring import metrics",
    "from vinci.schemas import LedgerEntry",
    # THE PACKAGE, THEN AN ATTRIBUTE (Codex P2 on #800): the import names only `vinci.schemas`,
    # and the row type is reached through the package's re-export one attribute later.
    "from vinci import schemas\nx = schemas.LedgerEntry",
    "import vinci.schemas\nx = vinci.schemas.LedgerEntry",
    "import vinci.schemas as s\nx = s.LedgerEntry.model_fields",
    "import vinci.schemas.candidate\nx = vinci.schemas.ledger.LedgerEntry",
    "import vinci\nx = vinci.scoring.metrics",
])
def test_every_import_shape_reaching_the_outcome_layer_is_seen(src: str) -> None:
    """NEGATIVE PIN. Each of these crosses the line. `from vinci import scoring` is the shape the
    ranker/themes/dossier fences cannot see (they read only `node.module`, which is `vinci`)."""
    names = imported_names(src, module="vinci.screens.screen2")
    assert any(_under(n, OUTCOME_LAYER + DIRECT_ONLY) or n in LEDGER_SCHEMA_REEXPORTS
               for n in names), f"missed: {src!r} → {sorted(names)}"


@pytest.mark.parametrize("src", [
    '"""Never imports vinci.scoring — the docstring may say so."""',
    "# from vinci.scoring import score_ledger",
    "from vinci.schemas.candidate import GateResult",
    "from vinci.store import Store",
    "import vinci.scenarios",
    "x = 'vinci.scoring'",
    "import vinci.schemas.candidate\nx = vinci.schemas.candidate.CandidateRecord",
    "schemas = load()\nx = schemas.LedgerEntry",           # a local, not an import
])
def test_words_about_the_outcome_layer_are_not_an_import(src: str) -> None:
    """POSITIVE PIN. A docstring, a comment or a string that is not imported does not cross; nor
    does a neighbour whose name merely starts the same way."""
    names = imported_names(src, module="vinci.screens.screen2")
    assert not any(_under(n, OUTCOME_LAYER + DIRECT_ONLY) or n in LEDGER_SCHEMA_REEXPORTS
                   for n in names), sorted(names)
