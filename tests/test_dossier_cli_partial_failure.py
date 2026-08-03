"""A MIXED COHORT — one name assembles, another refuses. The case `if dossiers:` misses.

REVIEW OF #325. The gate was described as stopping "the OLD page being published as fresh"; it does
no such thing when one name succeeds and another fails, because the mirror is a WHOLE-TREE rebuild.
Two things follow, and only one of them is a bug:

  * THE WHOLE-TREE MIRROR IS CORRECT and must stay. #319 asserts EVERY `frontend/dossiers/<T>.md`
    is byte-identical to its source, so mirroring only the successful names — or skipping on any
    error — strands whichever page had drifted, which is the FUBO defect the call exists to
    prevent. A refusal WRITES NOTHING, so a refused name's mirror copy is byte-identical to what it
    already served: a no-op, not a stale publish.
  * THE EXIT CODE WAS THE BUG. `_cmd_dossier` printed `errors` and returned 0, so a caller keying
    on the exit status read a refused assembly as a completed one. It bit immediately — the reroll
    harness written for this very task read exit 0 as convergence and stopped after one refused
    build.
"""
from __future__ import annotations

import argparse
import ast
import inspect
from pathlib import Path
from typing import Any

import pytest

from vinci import cli

ROOT = Path(__file__).resolve().parents[1]


class _FakeDossier:
    def __init__(self, ticker: str) -> None:
        self.ticker, self.rank, self.synthesis = ticker, 1, object()
        self.caveats: list[str] = []
        self.qa_flags: list[str] = []


def _run(monkeypatch: pytest.MonkeyPatch, *, done: list[str], errors: list[str]) -> tuple[int, int]:
    """Drive `_cmd_dossier` with a stubbed cohort. Returns (exit code, mirror call count)."""
    calls = {"mirror": 0}
    monkeypatch.setattr(cli, "load_finalists", lambda *a, **k: [object()], raising=False)
    import vinci.dossier.assemble as da
    import vinci.dossier.refresh as dr
    monkeypatch.setattr(da, "load_finalists", lambda *a, **k: [object()])
    monkeypatch.setattr(da, "assemble_cohort",
                        lambda *a, **k: ([_FakeDossier(t) for t in done], list(errors)))

    def _mirror() -> None:
        calls["mirror"] += 1

    monkeypatch.setattr(dr, "mirror_to_frontend", _mirror)
    args = argparse.Namespace(mode="assemble", top=10, ticker=None, no_llm=True, json=False,
                              show_proposal=False, peers=None, scenario=None)
    return cli._cmd_dossier(args), calls["mirror"]


def test_a_mixed_cohort_exits_non_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """ONE SUCCESS AND ONE FAILURE IS A FAILURE. Returning 0 here is what let a refused build read
    as a completed one."""
    rc, _ = _run(monkeypatch, done=["AORT"], errors=["SMPL: DossierAssemblyError: ..."])
    assert rc != 0, "a cohort with errors exited 0 — a caller cannot tell refusal from success"


def test_an_all_failed_cohort_exits_non_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    rc, mirrored = _run(monkeypatch, done=[], errors=["SMPL: DossierAssemblyError: ..."])
    assert rc != 0
    assert mirrored == 0, "nothing was written, so there was nothing to mirror"


def test_a_clean_cohort_exits_zero_and_mirrors(monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE CONTROL — the change must not make every run fail, and the mirror must still run
    on success or the served page goes stale (the defect this call was added for)."""
    rc, mirrored = _run(monkeypatch, done=["AORT", "SMPL"], errors=[])
    assert rc == 0
    assert mirrored == 1


def test_a_mixed_cohort_still_mirrors_the_whole_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    """DELIBERATE, NOT AN OVERSIGHT. The successful name's page MUST reach the served surface, and
    #319 requires every mirror to match its source — so a partial or skipped mirror would strand a
    drifted page. The refused name's copy is a no-op because a refusal writes nothing."""
    _, mirrored = _run(monkeypatch, done=["AORT"], errors=["SMPL: DossierAssemblyError: ..."])
    assert mirrored == 1, (
        "a mixed cohort skipped the mirror — the name that DID assemble is now stale on the served "
        "surface, which is the defect this call exists to prevent")


def test_the_exit_code_is_derived_from_errors_not_hardcoded() -> None:
    """STRUCTURAL, because `return 0` is what shipped and it reads as deliberate."""
    src = inspect.getsource(cli._cmd_dossier)
    returns = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Return)]
    finals: list[Any] = [n.value for n in returns if n.value is not None]
    assert any(isinstance(v, ast.IfExp) for v in finals), (
        "no conditional return in _cmd_dossier — the exit status is not derived from the error "
        "count, so a partial failure can exit 0 again")
