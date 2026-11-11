"""RF-D5's remainder (TeamNostra fix request 2; #991's record, FOUND NOT FIXED): the price ingest
names what it restated, found moved in price alone, or could not anchor — and the UNATTENDED
callers threw that summary away. `vinci refresh` prints it; the weekly screen
(`screens.run.screen_universe`), `run-monthly` (`orchestrator.run_monthly`) and the weekly job's
price-fixture build (`scripts/build_price_fixture.py`) did not, so an unanchored name was shown on
no path no one watches. Each now prints `eod.client.basis_lines(summary)` to stderr.

Pinned at the CALL SITE, on the stream the operator reads, not at the helper: a helper test stays
green when a call site drops it.
"""
from __future__ import annotations

import inspect
import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.dividend_support import no_dividends, no_splits
from tests.test_per_row_benchmark import AS_OF, _assignment, _Feed, _ident, _row
from vinci.config import Config
from vinci.eod.client import basis_lines
from vinci.store import Store

ROOT = Path(__file__).resolve().parents[1]

#: the summary shape both ingest paths return, naming one name in each list
_NAMED = {"restated": {"AAA": [0.5]}, "price_only": {"BBB": [1.04]}, "unanchored": ["CCC"]}


def test_basis_lines_names_every_listed_name_once() -> None:
    lines = basis_lines(_NAMED)
    assert len(lines) == 3
    assert "AAA restated ×0.5" in lines[0]
    assert "BBB moved ×1.04 in price alone" in lines[1]
    assert "CCC UNANCHORED" in lines[2]
    # (−) a summary that names nothing says nothing — the routine refresh stays quiet
    assert basis_lines({"restated": {}, "price_only": {}, "unanchored": []}) == []
    assert basis_lines({}) == []


def test_the_weekly_screen_prints_what_its_refresh_named(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """THE DEFECT: `screen_universe` called `ingest_prices` twice (the universe, the benchmark)
    and discarded both summaries."""
    from vinci.screens import run as screen_run
    from vinci.screens import screen_universe

    calls: list[int] = []

    def ingest(*_a: Any, **_k: Any) -> dict[str, Any]:
        calls.append(1)
        return _NAMED if len(calls) == 1 else {"unanchored": ["IWM"]}

    monkeypatch.setattr(screen_run, "ingest_prices", ingest)
    with Store(tmp_path / "s.db") as store:
        screen_universe(store, object(), object(),  # type: ignore[arg-type]
                        reference_date=date(2026, 6, 12), lookback_days=30, staleness_days=5)
    err = capsys.readouterr().err
    assert len(calls) == 2
    for name in ("AAA restated", "BBB moved", "CCC UNANCHORED", "IWM UNANCHORED"):
        assert f"PRICE BASIS: {name}" in err, err


def test_run_monthly_prints_what_its_refresh_named(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """THE SAME DEFECT in `run-monthly`'s refresh, which feeds scoring: through the real
    `run_monthly` and the real ingest, with one name the summary is made to carry."""
    from vinci import orchestrator

    cfg = Config(data_dir=tmp_path / "data")
    cfg.ensure_dirs()
    with Store(cfg.db_path) as store:
        store.upsert_security(_ident("NAME"))
        store.append_ledger(_row("NAME", "IWM"))
        store.export_snapshots(cfg.snapshots_dir)
    (cfg.data_dir / "monitor").mkdir()
    (cfg.data_dir / "monitor" / "benchmark_assignments.json").write_text(json.dumps(
        {"NAME": json.loads(_assignment("NAME", "MDY", ruled=True).model_dump_json())}))
    real = orchestrator.ingest_prices

    def ingest(*a: Any, **k: Any) -> dict[str, Any]:
        out = real(*a, **k)
        return {**out, "unanchored": ["NAME"]} if "IDX-" not in str(a[2]) else out

    monkeypatch.setattr(orchestrator, "PolygonEodClient", _Feed)
    monkeypatch.setattr(orchestrator, "default_dividends", lambda **_kw: no_dividends)
    monkeypatch.setattr(orchestrator, "default_splits", lambda *_a, **_k: no_splits)
    monkeypatch.setattr(orchestrator, "ingest_prices", ingest)
    orchestrator.run_monthly(cfg, as_of=AS_OF)
    assert "PRICE BASIS: NAME UNANCHORED" in capsys.readouterr().err


def test_the_price_fixture_build_prints_what_its_refresh_named() -> None:
    """A script run by the weekly job, not importable as a module function: its source must hand
    the per-symbol summary to `basis_lines` (it called the ingest and dropped the result)."""
    src = (ROOT / "scripts" / "build_price_fixture.py").read_text()
    assert "summary = ingest_prices_per_symbol(" in src
    assert "basis_lines(summary)" in src


def test_every_unattended_ingest_call_keeps_its_summary() -> None:
    """No ingest call in the two unattended modules is a bare statement again."""
    from vinci import orchestrator
    from vinci.screens import run as screen_run

    for fn in (screen_run.screen_universe, orchestrator.run_monthly):
        for ln in inspect.getsource(fn).splitlines():
            if "ingest_prices(" in ln:
                assert "basis_lines(" in ln, (fn.__name__, ln)
