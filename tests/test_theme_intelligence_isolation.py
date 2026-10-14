"""The boundary: theme intelligence is a research tool, never on the fund's decision path.

- no fund module imports `vinci.theme_intelligence` (it cannot feed screen / ranker / dossier /
  verdict / scoring / freeze / ledger / portfolio), and the package imports only the shared
  plumbing it is allowed (config + secrets loading, the existing LLM client, the HTTP cache);
- its own database lives under `data/theme_intelligence/`, never the fund's store;
- no record it can write has a buy / sell / target / weight / trade field;
- its priority constants read no prices, returns or outcomes (never tuned on what paid).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from pydantic import BaseModel

from vinci.theme_intelligence import schemas
from vinci.theme_intelligence.config import DEFAULT_DATA_DIR, Paths

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "vinci" / "theme_intelligence"
ALLOWED_VINCI_IMPORTS = {"vinci.config", "vinci.graph.llm", "vinci.netcache"}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def test_no_fund_module_imports_theme_intelligence() -> None:
    offenders = [str(p.relative_to(ROOT)) for p in (ROOT / "vinci").rglob("*.py")
                 if PKG not in p.parents and any(m.startswith("vinci.theme_intelligence")
                                                 for m in _imports(p))]
    assert offenders == []


def test_theme_intelligence_imports_only_shared_plumbing() -> None:
    used = {m for p in PKG.rglob("*.py") for m in _imports(p)
            if m.startswith("vinci") and not m.startswith("vinci.theme_intelligence")}
    assert used <= ALLOWED_VINCI_IMPORTS, used - ALLOWED_VINCI_IMPORTS


def _code_strings(path: Path) -> list[str]:
    """String constants in CODE — docstrings (which may name what the code never touches) are
    excluded."""
    tree = ast.parse(path.read_text())
    docs = {id(n.body[0].value) for n in ast.walk(tree)
            if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and n.body and isinstance(n.body[0], ast.Expr)
            and isinstance(n.body[0].value, ast.Constant)}
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
            and isinstance(n.value, str) and id(n) not in docs]


def test_its_registry_is_its_own() -> None:
    assert Path("data/theme_intelligence") == DEFAULT_DATA_DIR
    assert Paths(DEFAULT_DATA_DIR).db.parent == DEFAULT_DATA_DIR
    for p in PKG.rglob("*.py"):
        for s in _code_strings(p):
            assert "vinci.db" not in s and "data/snapshots" not in s, (p.name, s)


def test_no_record_has_a_trading_field() -> None:
    forbidden = re.compile(r"^(buy|sell|buy_sell|target|price_target|target_price|weight|"
                           r"position|position_size|allocation|order_size|trade|broker|"
                           r"execution)$")
    seen: set[str] = set()
    hits: list[str] = []
    for name in dir(schemas):
        obj = getattr(schemas, name)
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel:
            for f in obj.model_fields:
                seen.add(f)
                if forbidden.match(f):
                    hits.append(f"{name}.{f}")
    assert len(seen) > 100  # the walk really covered the schema
    assert hits == []


def test_priority_reads_no_prices_or_returns() -> None:
    src = (PKG / "priority.py").read_text().lower()
    code = "\n".join(line for line in src.splitlines() if not line.strip().startswith("#"))
    body = code.split('"""', 2)[-1]  # skip the module docstring that names the rule
    for word in ("polygon", "forward_return", "close_price", "eod", "spread", "ledger",
                 "return_"):
        assert word not in body, word
