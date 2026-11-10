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
    """Every string a `not_run=` keyword is given in the module, implicit joins included."""
    out: list[str] = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.keyword) and node.arg == "not_run":
            out += [n.value for n in ast.walk(node.value)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    return out


def test_rbc_d10_every_code_name_a_not_run_reason_gives_exists() -> None:
    """(+) Before: `ciq_scale_backfill.scale_check_backfill`, a module #905 removed."""
    named, missing = [], []
    for path in sorted(Path(sources.__path__[0]).glob("*.py")):
        for reason in _not_run_reasons(path):
            for mod, attr in _CODE_NAME.findall(reason):
                named.append(f"{mod}.{attr}")
                try:
                    ok = hasattr(importlib.import_module(f"vinci.dossier.{mod}"), attr)
                except ModuleNotFoundError:
                    ok = False
                if not ok:
                    missing.append((path.name, f"{mod}.{attr}"))
    assert len(named) >= 3, named   # the guard reads the reasons it is meant to read (3 today)
    assert missing == [], missing


def test_rbc_d10_the_scale_check_reason_states_todays_cause() -> None:
    got = ciq._ciq_scale_vs_revenue({"ticker": "ZZFX", "anchor": {}})
    assert got.not_run is not None
    assert "scale_check_backfill" not in got.not_run and "assembly writes it" in got.not_run


def test_rbc_d10_twin_a_reason_naming_a_removed_function_is_found(tmp_path: Path) -> None:
    """(−) The scan on a module whose reason names something that does not exist."""
    mod = tmp_path / "fake.py"
    mod.write_text('x = ItemResult(not_run="gone (refresh.no_such_transform_anywhere)")\n')
    names = [n for r in _not_run_reasons(mod) for n in _CODE_NAME.findall(r)]
    assert names == [("refresh", "no_such_transform_anywhere")]
    assert not hasattr(importlib.import_module("vinci.dossier.refresh"), names[0][1])
