"""`ciq_balance.extract`'s UNIT (scale) check has an outcome (wave 2, 2026-10-27).

It existed only as lines — "scale: every monetary figure within …" on a pass, a "SCALE:" failure
otherwise — so a check that never ran (no revenue to measure against) read like a pass in the
bridge's "N checks passed". Measured on the real workbooks of the 27 committed page names at
56500bb1: 25 agree, 2 not run (ORKA and TECX report no revenue), 0 differ.

The readers are replaced by the figures they return, so the outcome logic runs on real numbers
without the licensed workbook: VITL's revenue $371.6M and cash $126.1M (`test_ciq_balance`).
"""
from __future__ import annotations

from typing import Any

import pytest

from vinci.dossier import ciq_balance as cb
from vinci.dossier.schemas import CHECK_AGREE, CHECK_DIFFER, CHECK_NOT_RUN


class _NoWorkbook:
    def workbook(self, kind: str, freq: str | None = None) -> None:
        return None


def _extract(monkeypatch: pytest.MonkeyPatch, *, revenue: float | None,
             cash: float | None) -> Any:
    monkeypatch.setattr(cb, "_bs", lambda b, label: (cash, None) if label.startswith(
        "Total Cash") else (None, None))
    monkeypatch.setattr(cb, "_cf_row", lambda b, label, annual: revenue if label == (
        "Total Revenue") else None)
    # D&A is read with its column's period since the #830 review; no D&A row here either
    monkeypatch.setattr(cb, "_cf_cell", lambda b, label, annual: None)
    monkeypatch.setattr(cb, "_sourced", lambda b, fn: None)
    return cb.extract(_NoWorkbook(), "VITL")  # type: ignore[arg-type]


def test_a_millions_sheet_agrees(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _extract(monkeypatch, revenue=371.6, cash=126.1).scale_check == CHECK_AGREE


def test_a_whole_dollar_figure_differs(monkeypatch: pytest.MonkeyPatch) -> None:
    """The defect the check exists for: cash in whole dollars against revenue in $M."""
    got = _extract(monkeypatch, revenue=371.6, cash=126_100_000.0)
    assert got.scale_check == CHECK_DIFFER and not got.ok


def test_no_revenue_is_not_run_never_a_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    """ORKA's and TECX's shape: a figure, no revenue — the check had nothing to measure against."""
    assert _extract(monkeypatch, revenue=None, cash=126.1).scale_check == CHECK_NOT_RUN


def test_revenue_and_no_figure_is_not_run(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _extract(monkeypatch, revenue=371.6, cash=None).scale_check == CHECK_NOT_RUN


def test_a_folder_without_financials_is_not_run() -> None:
    assert cb.scale_outcome(_NoWorkbook(), "X") == CHECK_NOT_RUN  # type: ignore[arg-type]


def test_an_unreadable_workbook_is_not_run_not_a_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    """The bridge reads an unreadable workbook as no bridge and assembly goes on; the outcome must
    not raise where the bridge did not."""
    class _Held:
        def workbook(self, kind: str, freq: str | None = None) -> object:
            return object()

    def boom(_b: Any, _t: str) -> Any:
        raise ValueError("sheet unreadable")

    monkeypatch.setattr(cb, "extract", boom)
    assert cb.scale_outcome(_Held(), "X") == CHECK_NOT_RUN  # type: ignore[arg-type]


# --- the back-fill writes the outcome only behind its proof ---------------------------------------

def _page_copy(tmp_path: Any, ticker: str = "VRRM") -> Any:
    """A committed page copied out, its scale outcome removed — the state the back-fill met."""
    import json
    import pathlib

    src = pathlib.Path(__file__).resolve().parents[1] / "data" / "dossiers" / ticker
    dst = tmp_path / "dossiers" / ticker
    dst.mkdir(parents=True)
    doc = json.loads((src / "dossier.json").read_text())
    doc["anchor"].pop("ciq_scale_check", None)
    (dst / "dossier.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    return dst / "dossier.json", doc


class _Quarterly:
    path = "q.xls"

    def workbook(self, kind: str, freq: str | None = None) -> object | None:
        return self if freq == "quarterly" else None


def test_the_backfill_writes_only_the_pages_own_exports_outcome(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """VRRM's committed page: the quarterly export proven by its stamp → the outcome is written,
    and nothing else on the anchor moves; another sha → refused, the page untouched."""
    import json

    from vinci.dossier import ciq_scale_backfill as sb
    from vinci.dossier import ciq_sheets as cs

    path, doc = _page_copy(tmp_path)
    stamp = doc["ev_bridge"]["source_sha256"]
    monkeypatch.setattr(cb, "scale_outcome", lambda _b, _t: CHECK_AGREE)
    monkeypatch.setattr(sb, "scale_outcome", lambda _b, _t: CHECK_AGREE)

    monkeypatch.setattr(cs, "file_provenance", lambda _p: ("0123456789", None))
    refused: list[str] = []
    before = path.read_text()
    assert sb.scale_check_backfill(path, bundle=_Quarterly(), refused=refused) is False
    assert refused and "not the export the page stamps" in refused[0]
    assert path.read_text() == before

    monkeypatch.setattr(cs, "file_provenance", lambda _p: (stamp, None))
    assert sb.scale_check_backfill(path, bundle=_Quarterly(), refused=[]) is True
    after = json.loads(path.read_text())["anchor"]
    assert after.pop("ciq_scale_check") == CHECK_AGREE
    held = dict(doc["anchor"])
    assert after == held
    # a second run finds the outcome held and writes nothing
    assert sb.scale_check_backfill(path, bundle=_Quarterly(), refused=[]) is False
