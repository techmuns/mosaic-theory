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

WHICH HALF THIS COVERS: imports — static, star (by what the module exports) and literal-string
dynamic, the helper matched by its resolved name whatever its alias or argument form — and
attribute chains through an imported name (`schemas.LedgerEntry` after `from vinci import
schemas`); the Store's two ledger
readers by attribute name; and `decision_ledger` named in code (raw SQL, or the committed JSONL
by path), docstrings excepted. A path built from parts, `getattr` with a computed name, or a read
of `data/monitor/*.json` or the scoring report is NOT caught. None of the four does today (grep,
2026-10-26).

THE DECISION MODULES THE OLDER FENCES HELD DIRECT-ONLY, OR NOT AT ALL (2026-11-18). The ranker
(`vinci.rank`), the sleeve registry (`vinci.sleeves`), the proposal mapping
(`vinci.dossier.verdict`), the cap-band universe gate (`vinci.universe`) and the edge-basis gate
(`vinci.edge_basis`) each set a weight, a band, a vocabulary, a requirement or the proposal itself.
The ranker's, the registry's and the dossier's fences read `node.module` only, so
`from vinci import scoring` left them green (#800's hand-over showed it), and they never walk
through another module. The universe and the edge-basis gate had no fence. All five join `FENCED`,
measured green on main `322c6caa` before they joined. The whole dossier package is held
transitively against the scoring harness and the ledger. The monitor is the one outcome module it
may reach: the dossier takes the cap-band policy from it (the walker test below names that edge).

ONE NAMED ALLOWANCE. `vinci/dossier/verdict.py` imports `Verdict` from `vinci.schemas.ledger`.
`Verdict` is the label set its proposals are written in, an enum with no price on it, not the row
type. That one name is allowed in that one module; any other name from the ledger schema is
refused there, and a pin fails when the import goes, so the allowance cannot outlive its use.
"""

from __future__ import annotations

import ast
import functools
import importlib.util
import pathlib
import re
import shutil
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
VINCI = ROOT / "vinci"

#: THE SCREEN-BASKET BASELINE (#1004 item 2, 2026-11-13) reads forward returns of every screen
#: run's admitted and rejected names. It sits under `vinci.scoring` and is named here as well, so
#: moving it out of that package cannot quietly take it out of the fence.
SCREEN_BASELINE = "vinci.scoring.screen_baseline"
OUTCOME_LAYER = ("vinci.scoring", "vinci.ledger", "vinci.monitor", SCREEN_BASELINE)
DIRECT_ONLY = ("vinci.schemas.ledger",)
LEDGER_WRITE_PATHS = ("vinci.ledger", "vinci.store")
#: `Store` is a legitimate import of the screen (prices, candidates), and it also READS the ledger.
STORE_LEDGER_READERS = frozenset({"iter_ledger", "get_ledger_entry"})

#: The decision modules the older fences held direct-only, or not at all (2026-11-18, docstring).
DECISION_MODULES = ("vinci.rank", "vinci.sleeves", "vinci.dossier.verdict", "vinci.universe",
                    "vinci.edge_basis")
FENCED = ("vinci.screens", "vinci.cohort", "vinci.triggers", "vinci.scenarios", *DECISION_MODULES)

#: A name the direct ban would refuse, allowed in ONE module, with its reason (docstring).
DIRECT_ALLOWED: dict[str, frozenset[str]] = {
    "vinci.dossier.verdict": frozenset({"vinci.schemas.ledger.Verdict"}),
}

#: The dossier package's barrier: the monitor is the one outcome module it may reach (docstring).
DOSSIER_BARRED = ("vinci.scoring", "vinci.ledger", SCREEN_BASELINE)


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


def _star_names(module: str) -> set[str]:
    """What `from <module> import *` binds: its literal `__all__`, else every top-level name it
    defines or imports. An unknown (non-repo) module binds nothing this fence can name."""
    if module not in MODULES:
        return set()
    tree = ast.parse(MODULES[module].read_text())
    for node in tree.body:
        if (isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets)
                and isinstance(node.value, ast.List | ast.Tuple)):
            return {e.value for e in node.value.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)}
    names = _top_level_names(MODULES[module])
    for node in tree.body:
        if isinstance(node, ast.Import | ast.ImportFrom):
            names.update(a.asname or a.name.split(".")[0] for a in node.names if a.name != "*")
    return names


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
    A package import is a handle on everything the package re-exports (Codex P2 on #800).
    A star import yields each name the module exports (its `__all__`, else what it binds), and a
    dynamic import is matched by the helper's RESOLVED name, so an alias (`import_module as load`)
    or a `name=` keyword does not hide it (Codex P2 ×2, round 2)."""
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
                names = _star_names(base) if a.name == "*" else {a.asname or a.name}
                for n in names:
                    target = f"{base}.{n if a.name == '*' else a.name}"
                    out.add(target)
                    bound[n] = target

    def dotted(expr: ast.expr, *, imported_only: bool) -> str | None:
        """The dotted name an attribute chain resolves to through the import bindings; a chain
        rooted in an unbound local resolves to None when ``imported_only``."""
        attrs: list[str] = []
        while isinstance(expr, ast.Attribute):
            attrs.append(expr.attr)
            expr = expr.value
        if not isinstance(expr, ast.Name) or (imported_only and expr.id not in bound):
            return None
        return ".".join([bound.get(expr.id, expr.id), *reversed(attrs)])

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if (name := dotted(node, imported_only=True)) is not None:
                out.add(name)
        elif isinstance(node, ast.Call):
            called = dotted(node.func, imported_only=False)
            arg = node.args[0] if node.args else next(
                (k.value for k in node.keywords if k.arg == "name"), None)
            if (called is not None and called.rsplit(".", 1)[-1] in ("import_module", "__import__")
                    and isinstance(arg, ast.Constant) and isinstance(arg.value, str)):
                out.add(arg.value)
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


def _allowed(module: str, name: str) -> bool:
    """Whether ``name`` is ``module``'s one named allowance: the allowed name, an attribute of it,
    or the module the allowed name is imported from (`from M import X` also yields `M`)."""
    return any(name == a or name.startswith(a + ".") or name == a.rpartition(".")[0]
               for a in DIRECT_ALLOWED.get(module, frozenset()))


def _direct_hits(src: str, *, module: str, is_package: bool = False) -> list[str]:
    """The outcome-side names ``src`` imports directly, less ``module``'s named allowance."""
    return sorted(m for m in imported_names(src, module=module, is_package=is_package)
                  if (_under(m, OUTCOME_LAYER + DIRECT_ONLY) or m in LEDGER_SCHEMA_REEXPORTS)
                  and not _allowed(module, m))


# --- the fences ---------------------------------------------------------------------------------

@pytest.mark.parametrize("target", FENCED)
def test_no_gate_or_threshold_module_imports_the_outcome_layer(target: str) -> None:
    """Direct imports, file by file — the existing fences' shape, with the monitor added to the
    outcome layer and `vinci.schemas.ledger` (the row type, close rows' exit prices) beside it."""
    files = _files(target)
    assert files, f"{target}: the fence walked no file"
    for path in files:
        hits = _direct_hits(path.read_text(), module=_module_name(path),
                            is_package=path.name == "__init__.py")
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


def test_no_dossier_module_reaches_the_scoring_harness_or_the_ledger() -> None:
    """The dossier's own fence (`tests/test_dossier.py`) reads `node.module` only and stops at the
    file. This one walks. The dossier assembles, cites and proposes; reaching the spread or the
    ledger's write path is how it would start concluding from outcomes."""
    files = _files("vinci.dossier")
    assert len(files) > 40, f"the dossier fence walked {len(files)} files"
    for path in files:
        via = reach(_module_name(path))
        crossed = sorted(m for m in via if _under(m, DOSSIER_BARRED))
        assert not crossed, ("the dossier reaches the scoring harness or the ledger: "
                             + "; ".join(_chain(via, m) for m in crossed))


def test_the_proposal_mappings_one_allowance_is_in_use_and_names_only_the_labels() -> None:
    """`Verdict` is allowed in `vinci.dossier.verdict` and nothing else from the ledger schema is.
    The allowance must be in use (when the import goes, remove the allowance), and the row type
    planted beside it is refused."""
    src = MODULES["vinci.dossier.verdict"].read_text()
    assert "vinci.schemas.ledger.Verdict" in imported_names(src, module="vinci.dossier.verdict"), (
        "verdict.py no longer imports Verdict from the ledger schema: drop its allowance")
    assert _direct_hits(src, module="vinci.dossier.verdict") == []
    planted = src + "\nfrom vinci.schemas.ledger import LedgerEntry\n"
    assert _direct_hits(planted, module="vinci.dossier.verdict") == [
        "vinci.schemas.ledger.LedgerEntry"]
    # the allowance is the proposal mapping's alone: the same import from the ranker is refused
    assert _direct_hits("from vinci.schemas.ledger import Verdict\n",
                        module="vinci.rank.ranker") == [
        "vinci.schemas.ledger", "vinci.schemas.ledger.Verdict"]


def test_the_screen_basket_baseline_is_inside_the_fence() -> None:
    """#1004 item 2: the baseline measures whether the screen selects anything, so it must never
    be readable from the screen it measures. It exists, the fence names it, an import of it from a
    screen module is seen, and it reaches the screen's records — the one allowed direction."""
    assert SCREEN_BASELINE in MODULES, "the fence names a module that does not exist"
    hits = imported_names("from vinci.scoring.screen_baseline import report\n",
                          module="vinci.screens.run", is_package=False)
    assert any(_under(m, OUTCOME_LAYER) for m in hits), hits
    assert "vinci.screens.retention" in reach(SCREEN_BASELINE)


def _docstring_nodes(tree: ast.Module) -> set[int]:
    owners = [tree, *(n for n in ast.walk(tree)
                      if isinstance(n, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef))]
    return {id(o.body[0].value) for o in owners
            if o.body and isinstance(o.body[0], ast.Expr)
            and isinstance(o.body[0].value, ast.Constant)}


#: The dossier too: it may reach the monitor, but a ledger row read through the Store is the ledger.
@pytest.mark.parametrize("target", (*FENCED, "vinci.dossier"))
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
    # the decision modules of 2026-11-18, by file: the ranker's three, then one file each
    assert {"ranker.py", "structural.py", "profile.py", "sleeves.py", "verdict.py",
            "universe.py", "edge_basis.py"} <= scanned


# --- a planted import in a COPY of the tree is refused (the fence run on a real tree, not a string)

def _copy_tree(dest: pathlib.Path) -> pathlib.Path:
    """``vinci/``'s Python files and this test file, copied under ``dest`` as a repo holds them."""
    def not_python(folder: str, names: list[str]) -> list[str]:
        return [n for n in names if n == "__pycache__"
                or (not n.endswith(".py") and not pathlib.Path(folder, n).is_dir())]
    shutil.copytree(VINCI, dest / "vinci", ignore=not_python)
    (dest / "tests").mkdir()
    shutil.copy2(pathlib.Path(__file__), dest / "tests" / pathlib.Path(__file__).name)
    return dest


def _load_fence(root: pathlib.Path, tag: str) -> types.ModuleType:
    """This fence, imported from the copy under ``root``: ROOT, VINCI and MODULES are the copy's."""
    spec = importlib.util.spec_from_file_location(
        f"_fence_copy_{tag}", root / "tests" / pathlib.Path(__file__).name)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _plant(root: pathlib.Path, rel: str, line: str) -> None:
    with (root / rel).open("a") as fh:
        fh.write(f"\n{line}\n")


@pytest.mark.parametrize(("target", "rel"), [
    ("vinci.rank", "vinci/rank/ranker.py"),
    ("vinci.sleeves", "vinci/sleeves.py"),
    ("vinci.dossier.verdict", "vinci/dossier/verdict.py"),
    ("vinci.universe", "vinci/universe.py"),
    ("vinci.edge_basis", "vinci/edge_basis.py"),
])
def test_a_planted_import_in_a_copy_of_a_decision_module_is_refused(
        target: str, rel: str, tmp_path: pathlib.Path) -> None:
    """POSITIVE then NEGATIVE, on a copy of the real tree. The copy passes as copied; then
    `from vinci import scoring` — the shape the older fences could not see — is appended to the
    decision module's own file, and both of its fences refuse it."""
    root = _copy_tree(tmp_path)
    clean = _load_fence(root, "clean")
    assert target in clean.FENCED, f"{target} is not fenced"
    clean.test_no_gate_or_threshold_module_imports_the_outcome_layer(target)
    clean.test_no_gate_or_threshold_module_reaches_the_outcome_layer_through_another(target)
    _plant(root, rel, "from vinci import scoring")
    planted = _load_fence(root, "planted")
    with pytest.raises(AssertionError, match=re.escape(f"{rel} imports ['vinci.scoring']")):
        planted.test_no_gate_or_threshold_module_imports_the_outcome_layer(target)
    with pytest.raises(AssertionError, match=r"vinci\.scoring <- "):
        planted.test_no_gate_or_threshold_module_reaches_the_outcome_layer_through_another(target)


def test_a_planted_import_one_module_away_is_refused_by_the_walk_alone(
        tmp_path: pathlib.Path) -> None:
    """THE TRANSITIVE HALF. `vinci.schemas.cohort` is fenced by nothing, and the ranker's profile
    imports it. Plant the outcome import there and every direct check of the ranker stays green
    while the walk names the path, through the ranker and through the dossier."""
    root = _copy_tree(tmp_path)
    _plant(root, "vinci/schemas/cohort.py", "from vinci import scoring")
    planted = _load_fence(root, "one_away")
    planted.test_no_gate_or_threshold_module_imports_the_outcome_layer("vinci.rank")
    with pytest.raises(AssertionError, match=r"vinci\.scoring <- vinci\.schemas\.cohort <- .*"
                                             r"vinci\.rank"):
        planted.test_no_gate_or_threshold_module_reaches_the_outcome_layer_through_another(
            "vinci.rank")
    with pytest.raises(AssertionError, match=r"vinci\.scoring <- vinci\.schemas\.cohort <- .*"
                                             r"vinci\.dossier"):
        planted.test_no_dossier_module_reaches_the_scoring_harness_or_the_ledger()


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
    # Round 2 (Codex P2 ×2 on #800): a star import takes the package's re-exports by bare name,
    # and a dynamic import escapes when its helper is aliased or its target passed by keyword.
    "from vinci.schemas import *",
    "from importlib import import_module as load\nload('vinci.scoring')",
    "import importlib as il\nil.import_module(name='vinci.ledger')",
    "import importlib\nimportlib.import_module(name='vinci.monitor')",
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
    "from vinci.schemas.candidate import *",
    "from importlib import import_module as load\nload('vinci.scenarios')",
])
def test_words_about_the_outcome_layer_are_not_an_import(src: str) -> None:
    """POSITIVE PIN. A docstring, a comment or a string that is not imported does not cross; nor
    does a neighbour whose name merely starts the same way."""
    names = imported_names(src, module="vinci.screens.screen2")
    assert not any(_under(n, OUTCOME_LAYER + DIRECT_ONLY) or n in LEDGER_SCHEMA_REEXPORTS
                   for n in names), sorted(names)
