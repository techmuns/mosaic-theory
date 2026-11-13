"""THREE MODULES WITH NO CALLER ARE REMOVED, NOT LEFT DEAD (2026-11-13; issue 1004, lane 4).

The operator approved retiring dead code "reliably" (2026-11-13, on B's design note); each module
below was shown to have no caller first, under two vocabularies, `git log --all -i --grep`,
`git log -S`, and every importer in `vinci/`, `scripts/`, `tests/`, `frontend/`, the workflows, the
CLI entry points and string imports.
Record: `docs/records/2026-11-13-three-uncalled-modules-retired.md`.

- `vinci/rank/cause.py` — the Tier-3 LLM cause classifier and its `vinci rank --cause-file`
  loader. Never fed: all 343 rows of the committed queue read `unclassified`. The ranker no longer
  reads a cause; the queue keeps its `cause_class` field and the "· LLM: —" label as constants.
- `vinci/dossier/tagger.py` — the propose-only recipe tagger. No code called it; it was last run by
  hand for #671's record (2026-10-07).
- `vinci/edgar/segments.py` — the R-file segment-economics reader (MC2). Its last caller, the
  monitor panels, left with #910 on 2026-11-05; `vinci/edgar/segment_facts.py` reads segment profit
  from the XBRL instance instead. RE2-D15's defect in it (fixed in 670a784c, #969) went with it.

Restore any of them from the commit before this PR's squash (see the record).
"""
from __future__ import annotations

import ast
import importlib.util
import inspect
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

RETIRED = ("vinci.rank.cause", "vinci.dossier.tagger", "vinci.edgar.segments")
#: The trees an importer can live in: the package, the tests, the scripts and the frontend builder.
SCANNED = ("vinci", "tests", "scripts", "frontend", ".github")
#: What `vinci/rank` must not import now that its one LLM channel has left: no model output can
#: reach the queue's sort.
LLM_CLIENTS = ("vinci.graph.llm", "vinci.theme_intelligence.llm", "anthropic")


def _module_of(path: Path) -> str:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def imported_names(source: str, module: str, is_package: bool = False) -> list[tuple[int, str]]:
    """Every module name `source` imports, each as its full dotted name with its line: `import a.b`,
    `from a import b` (as `a` and `a.b`, since `b` may be a module), a relative `from . import b`
    resolved against `module`, and `importlib.import_module` / `__import__` called with a
    literal."""
    out: list[tuple[int, str]] = []
    pkg = module.split(".") if is_package else module.split(".")[:-1]
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out += [(node.lineno, a.name) for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                up = pkg[: len(pkg) - (node.level - 1)]
                base = ".".join([*up, *([base] if base else [])])
            out.append((node.lineno, base))
            out += [(node.lineno, f"{base}.{a.name}") for a in node.names]
        elif (isinstance(node, ast.Call) and node.args
              and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            f = node.func
            name = (f.attr if isinstance(f, ast.Attribute)
                    else f.id if isinstance(f, ast.Name) else "")
            if name in ("import_module", "__import__"):
                out.append((node.lineno, node.args[0].value))
    return out


def importers_of(target: str, sources: list[tuple[str, str, str, bool]]) -> list[str]:
    """`path:line` of every import of `target`, or of a name under it, in (path, module, source,
    is_package) rows, each line once."""
    hits = [f"{path}:{line}" for path, mod, src, is_pkg in sources
            for line, name in imported_names(src, mod, is_pkg)
            if name == target or name.startswith(target + ".")]
    return list(dict.fromkeys(hits))


def _tree() -> list[tuple[str, str, str, bool]]:
    rows = []
    for top in SCANNED:
        for path in sorted((ROOT / top).rglob("*.py")):
            rows.append((path.relative_to(ROOT).as_posix(), _module_of(path),
                         path.read_text(encoding="utf-8"), path.name == "__init__.py"))
    return rows


@pytest.mark.parametrize("module", RETIRED)
def test_a_retired_module_is_gone_and_nothing_imports_it(module: str) -> None:
    """(+) The source file is absent and nothing in the scanned trees imports it, by any form.
    A leftover `__pycache__/*.pyc` is not importable without its source, so `find_spec` is None."""
    assert not (ROOT / (module.replace(".", "/") + ".py")).exists(), f"{module} is back"
    assert importlib.util.find_spec(module) is None, f"{module} is importable again"
    found = importers_of(module, _tree())
    assert not found, f"still importing {module}: {found}"


def test_the_scan_finds_every_import_form() -> None:
    """(-) Each form a caller could take is found — a scan that missed one would pass over a live
    caller — and (+) a sibling module of the same package is not mistaken for the retired one."""
    planted = [
        ("a.py", "a", "import vinci.rank.cause\n", False),
        ("b.py", "b", "from vinci.rank.cause import classify_cause\n", False),
        ("c.py", "c", "from vinci.rank import cause\n", False),
        ("vinci/rank/d.py", "vinci.rank.d", "from . import cause\n", False),
        ("vinci/rank/__init__.py", "vinci.rank", "from .cause import x\n", True),
        ("e.py", "e", "import importlib\nimportlib.import_module('vinci.rank.cause')\n", False),
        ("f.py", "f", "__import__('vinci.rank.cause.sub')\n", False),
    ]
    assert importers_of("vinci.rank.cause", planted) == [
        "a.py:1", "b.py:1", "c.py:1", "vinci/rank/d.py:1", "vinci/rank/__init__.py:1",
        "e.py:2", "f.py:1"]
    clean = [("g.py", "g", "from vinci.rank import ranker, profile\nimport vinci.rank.causes\n",
              False)]
    assert importers_of("vinci.rank.cause", clean) == []


def test_the_ranker_reads_no_cause_and_imports_no_model() -> None:
    """The decision-path half (`vinci/rank`). (+) No ranking entry point takes a cause any more,
    and no module of the package imports an LLM client itself. (`structural.py` reads
    `vinci.graph.filings`, whose package `__init__` loads `vinci.graph.llm`; nothing in
    `vinci/rank` calls it.) (-) The scan names a planted client import."""
    from vinci import orchestrator
    from vinci.rank import ranker

    assert "annotations" not in inspect.signature(ranker.rank_candidates).parameters
    assert "cause_class" not in inspect.signature(ranker.rank_candidate).parameters
    assert list(inspect.signature(ranker.character_axis).parameters) == ["rec"]
    assert "annotations" not in inspect.signature(orchestrator.rank_from_snapshots).parameters
    rank = [r for r in _tree() if r[0].startswith("vinci/rank/")]
    assert {Path(r[0]).name for r in rank} >= {"ranker.py", "profile.py", "structural.py"}
    for client in LLM_CLIENTS:
        assert not importers_of(client, rank), f"vinci/rank imports {client}"
    planted = [("vinci/rank/x.py", "vinci.rank.x",
                "from vinci.graph.llm import LlmClient\n", False)]
    assert importers_of("vinci.graph.llm", planted) == ["vinci/rank/x.py:1"]


def test_vinci_rank_runs_on_the_committed_queue(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                               capsys: pytest.CaptureFixture[str]) -> None:
    """END TO END, the command an operator runs: `vinci rank --no-write` over the committed
    snapshots. The first cut of this retirement left the summary line reading the removed cause
    map, and the name then resolved to `from __future__ import annotations`, so the command
    crashed after ranking; no unit test reached the line. Every row it ranks carries the
    retired slot's constant."""
    from vinci import cli

    snaps = ROOT / "data" / "snapshots"
    if not (snaps / "candidate_records.jsonl").is_file():
        pytest.skip("no committed candidate records")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "snapshots").symlink_to(snaps)
    monkeypatch.chdir(tmp_path)
    before = (snaps / "ranked_queue.jsonl").stat().st_mtime_ns
    assert cli._cmd_rank(cli.build_parser().parse_args(["rank", "--no-write", "--top", "1"])) == 0
    out = capsys.readouterr().out
    assert "=== Ranked queue · " in out and "cause annotations" not in out
    assert (snaps / "ranked_queue.jsonl").stat().st_mtime_ns == before, "--no-write wrote"
    rows = [ln for ln in (snaps / "ranked_queue.jsonl").read_text().splitlines() if ln.strip()]
    assert rows and all('"cause_class":"unclassified"' in ln for ln in rows)
