"""The CIQ bridge refuses a foreign-currency workbook on BOTH write paths, and the anchor stores its
scale check's outcome (wave 2, 2026-10-27; #819's review finding 1 and its unscored scale check).

#819 refused a money panel stating another currency before ASSEMBLY (`ciq_sheets.require_usd`), but
`anchor-backfill` reads the same workbook through `anchor.ciq_bridge` — and that path read ONON's
CHF figures as dollars. ONON states CHF on 15 money panels (measured 2026-10-27 on the assembler's
copy); the shape is frozen here as one CHF Financials panel beside the USD comps label.

The bridge's UNIT check (`ciq_balance.extract`) produced only lines; its outcome now rides on the
anchor as `ciq_scale_check`, set by both callers — the assembly's `_assembly_anchor` and the
backfill's `_machine_anchor`.
"""
from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from vinci.dossier import anchor as an
from vinci.dossier import assemble as asm
from vinci.dossier import ciq_balance, ciq_sheets
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.ciq_balance import CiqFacts
from vinci.dossier.ciq_sheets import CiqCurrencyError
from vinci.dossier.schemas import CiqCurrency, PanelCurrency

ROOT = pathlib.Path(__file__).resolve().parents[1]
CUT: dict[str, dict[str, Any]] = json.loads(
    (ROOT / "tests" / "fixtures" / "anchor_ciq_bridge.json").read_text())["names"]
T0 = datetime(2026, 10, 27, tzinfo=UTC)

#: ONON's shape: a Financials panel stating CHF beside the comps book's 'US Dollar'
_CHF = CiqCurrency(panels=[
    PanelCurrency(panel="Financials (quarterly)→Income Statement", stated=["CHF"],
                  where="the per-column 'Currency' row", check="differ"),
    PanelCurrency(panel="Comparable Analysis", stated=["US Dollar"],
                  where="the 'Currency:' label", check="agree")], check="differ")
_USD = CiqCurrency(panels=[_CHF.panels[1]], check="agree")
_FACTS = CiqFacts(ticker="ONON", as_of=None, source_file="x.xls", source_sha256="0" * 10)


def _bridge(monkeypatch: pytest.MonkeyPatch, currency: CiqCurrency) -> Any:
    monkeypatch.setattr(ciq_sheets, "stated_currency", lambda _b: currency)
    monkeypatch.setattr(ciq_balance, "extract", lambda _b, _t: _FACTS)
    return an.ciq_bridge(CiqBundle.from_files("ONON", []), "ONON")


def test_the_bridge_refuses_a_workbook_stating_another_currency(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Before: the bridge handed ONON's CHF facts on as dollars. Now it raises, as assembly does."""
    with pytest.raises(CiqCurrencyError, match="CHF"):
        _bridge(monkeypatch, _CHF)


def test_a_usd_workbook_still_bridges(monkeypatch: pytest.MonkeyPatch) -> None:
    """Negative pin: a workbook stating USD bridges as before."""
    ciq, _note = _bridge(monkeypatch, _USD)
    assert ciq is _FACTS


def test_the_backfill_path_does_not_swallow_the_refusal(
        monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """`_machine_anchor` (anchor-backfill / anchor-retag) catches every bridge exception as 'no
    workbook' except the ones the operator must clear — the currency refusal is one of them now,
    so the name fails loud instead of being anchored EDGAR-only."""
    from vinci import cli

    monkeypatch.setattr(ciq_sheets, "stated_currency", lambda _b: _CHF)
    page = CUT["GOOGL"]["page"]
    d = SimpleNamespace(mechanical=SimpleNamespace(model_dump=lambda mode, m=page["mechanical"]: m))
    resolver = SimpleNamespace(resolve_ticker=lambda _t: SimpleNamespace(cik="0"))
    edgar = SimpleNamespace(companyfacts=lambda _cik: CUT["GOOGL"]["companyfacts"])
    with pytest.raises(CiqCurrencyError):
        cli._machine_anchor("GOOGL", d, json.dumps(page), SimpleNamespace(data_dir=tmp_path),
                            resolver, edgar)


@pytest.mark.parametrize("outcome", ["agree", "differ", "not_run"])
def test_assembly_stores_the_scale_outcome_on_the_anchor(
        outcome: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every outcome reaches the anchor as computed, a differ included — the bridge itself is then
    refused (handed on as None), so the outcome is read again, and the anchor says why in a
    structured field rather than a dropped note."""
    monkeypatch.setattr(asm, "ciq_bridge", lambda _b, _t: (None, "CIQ extraction REFUSED"))
    monkeypatch.setattr(ciq_balance, "scale_outcome", lambda _b, _t: outcome)
    page = CUT["GOOGL"]["page"]
    got = asm._assembly_anchor(page["mechanical"], facts=CUT["GOOGL"]["companyfacts"],
                               bundle=CiqBundle.from_files("GOOGL", []), ticker="GOOGL",
                               computed_at=T0)
    assert got.ciq_scale_check == outcome


def test_an_anchor_without_the_outcome_writes_no_key() -> None:
    """ABSENT, never null: a committed anchor predating the field round-trips byte-identically."""
    a = an.Anchor.model_validate(CUT["GOOGL"]["anchor"])
    assert a.ciq_scale_check is None
    assert "ciq_scale_check" not in a.model_dump_json(exclude=an.anchor_absent_fields(a))


def test_a_bridged_read_carries_its_own_outcome(monkeypatch: pytest.MonkeyPatch) -> None:
    """Where the bridge handed facts on, their own outcome is stored — the workbook is not read
    twice (code review)."""
    import dataclasses

    facts = dataclasses.replace(_FACTS, scale_check="agree")
    monkeypatch.setattr(asm, "ciq_bridge", lambda _b, _t: (facts, None))

    def never(_b: Any, _t: str) -> Any:
        raise AssertionError("read again")

    monkeypatch.setattr(ciq_balance, "scale_outcome", never)
    page = CUT["GOOGL"]["page"]
    got = asm._assembly_anchor(page["mechanical"], facts=CUT["GOOGL"]["companyfacts"],
                               bundle=CiqBundle.from_files("GOOGL", []), ticker="GOOGL",
                               computed_at=T0)
    assert got.ciq_scale_check == "agree"
