"""A data-quality "not run" reason names only code that exists (fix request 2, order 6: audit
RBC-D10; 2026-11-10).

The CIQ scale check's reason named `ciq_scale_backfill.scale_check_backfill`, which #905 retired,
so on every page built since, the cause it gave could not be the cause. Each parenthesised code
name in a `not_run=` reason of a quality source is resolved here against `vinci.dossier`: a name
that no longer exists fails the suite, never a page's scorecard.
"""
from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

import vinci.quality.sources as sources
from vinci.quality.sources import ciq

_CODE_NAME = re.compile(r"\(([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\)")


def _not_run_reasons(path: Path) -> list[str]:
    """Every string a `not_run=` keyword is given in the module, implicit joins included — and
    the string of a module-level constant it names (`_ABSENT.format(key=key)`), which is where
    a reason shared by several checks lives."""
    tree = ast.parse(path.read_text())
    consts: dict[str, list[str]] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            strs = [n.value for n in ast.walk(stmt.value)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)]
            for t in stmt.targets:
                if isinstance(t, ast.Name):
                    consts[t.id] = strs
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "not_run":
            for n in ast.walk(node.value):
                if isinstance(n, ast.Constant) and isinstance(n.value, str):
                    out.append(n.value)
                elif isinstance(n, ast.Name):
                    out += consts.get(n.id, [])
    return out


def _named_and_missing(path: Path) -> tuple[list[str], list[str]]:
    """The code names the module's reasons give, and those that do not resolve under
    `vinci.dossier`."""
    named, missing = [], []
    for reason in _not_run_reasons(path):
        for mod, attr in _CODE_NAME.findall(reason):
            named.append(f"{mod}.{attr}")
            try:
                ok = hasattr(importlib.import_module(f"vinci.dossier.{mod}"), attr)
            except ModuleNotFoundError:
                ok = False
            if not ok:
                missing.append(f"{mod}.{attr}")
    return named, missing


def test_rbc_d10_every_code_name_a_not_run_reason_gives_exists() -> None:
    """(+) Before: `ciq_scale_backfill.scale_check_backfill`, a module #905 removed."""
    named, missing = [], []
    for path in sorted(Path(sources.__path__[0]).glob("*.py")):
        n, m = _named_and_missing(path)
        named += n
        missing += [(path.name, x) for x in m]
    # the guard reads the reasons it is meant to read: 4 today, `_ABSENT`'s among them
    assert "refresh.cross_check_transform" in named and len(named) >= 4, named
    assert missing == [], missing


def test_rbc_d10_the_scale_check_reason_states_todays_cause() -> None:
    """The retired back-fill is gone from the words, and the live one that writes the field —
    `vinci anchor-backfill`, through `cli._machine_anchor` — is named beside assembly."""
    got = ciq._ciq_scale_vs_revenue({"ticker": "ZZFX", "anchor": {}})
    assert got.not_run is not None
    assert "scale_check_backfill" not in got.not_run
    assert "assembly" in got.not_run and "anchor-backfill" in got.not_run


def test_rbc_d10_twin_a_reason_naming_a_removed_function_is_found(tmp_path: Path) -> None:
    """(−) The guard on a module whose reasons name something that does not exist — inline, and
    through a module-level constant."""
    mod = tmp_path / "fake.py"
    mod.write_text('x = ItemResult(not_run="gone (refresh.no_such_transform_anywhere)")\n'
                   '_R = ("also gone "\n      "(refresh.no_such_constant_anywhere)")\n'
                   'y = ItemResult(not_run=_R.format(key="k"))\n')
    named, missing = _named_and_missing(mod)
    want = ["refresh.no_such_transform_anywhere", "refresh.no_such_constant_anywhere"]
    assert named == missing == want
