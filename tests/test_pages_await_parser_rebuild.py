"""The committed pages still carry what the release and 10-Q parsers read before audit E2's fixes.

The fixes are in code (`release_parse`, `filing_sections`, `primary_source`); the pages change only
when the combined artifact rebuild re-assembles them. Each pin asserts the CORRECTED reading on the
committed page — the real JSON, end to end — and is a strict xfail naming its defect, so:

* until the rebuild, the page still reads wrong and the pin is an expected failure;
* the rebuild that lands the fix makes it pass, and strict turns that pass into a failure until the
  marker is removed — the rebuild cannot land these pages without seeing each one;
* a page that no longer cites the source a pin names raises ``LookupError``, which the xfail
  (``raises=AssertionError``) does not absorb — a rebuild that moves to a newer filing fails loudly
  and re-points the pin, instead of leaving one that can never pass.

Facts only: every pin is a value a filing states, read by deterministic code — no LLM text.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

_PAGES = Path(__file__).resolve().parent.parent / "data" / "dossiers"


def _ps(ticker: str) -> dict[str, Any]:
    doc = json.loads((_PAGES / ticker / "dossier.json").read_text())
    ps: dict[str, Any] = doc["mechanical"]["primary_source"]
    return ps


def _release(ticker: str, accession: str) -> dict[str, Any]:
    for r in _ps(ticker).get("releases") or []:
        if accession in r["source_ref"]:
            return dict(r)
    raise LookupError(f"{ticker}'s page no longer cites 8-K {accession} — re-point this pin")


def _filing(ticker: str, accession: str) -> dict[str, Any]:
    f = _ps(ticker).get("filing") or {}
    if accession not in (f.get("source_ref") or ""):
        raise LookupError(f"{ticker}'s page no longer cites 10-Q {accession} — re-point this pin")
    return dict(f)


def _rows(r: dict[str, Any]) -> set[tuple[str, str, float]]:
    return {(x["metric"], x["period"], x["value"]) for x in r["reconciliation"]}


def _awaits(defect: str) -> pytest.MarkDecorator:
    return pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
        f"{defect} — fixed in code; the committed page waits for the combined artifact rebuild"))


@_awaits("audit E2-D5: FUBO's Q1 2026 adjusted EBITDA is the trailing-twelve-month $77.9M")
def test_fubo_q1_2026_adjusted_ebitda_is_the_quarters_own() -> None:
    rows = _rows(_release("FUBO", "0001493152-26-004826"))
    assert ("adjusted ebitda", "Q1 2026", 41.4) in rows
    assert not any(v == 77.9 for _m, _p, v in rows)


@_awaits("audit E2-D10: VITL's Q2 2026 adjusted EBITDA loss of $26.6M is dropped")
def test_vitl_q2_2026_adjusted_ebitda_loss_is_on_the_page() -> None:
    assert ("adjusted ebitda", "Q2 2026", -26.6) in _rows(_release("VITL", "0001193125-26-336692"))


@_awaits("audit E2-D12: VRRM carries a $94.3M cash-flow change as an impairment one-off")
def test_vrrm_one_offs_are_the_impairments_not_the_cash_flow_change() -> None:
    amounts = [o["amount"] for o in _release("VRRM", "0001193125-26-335111")["one_offs"]]
    assert 94.3 not in amounts and {64.0, 40.4} <= set(amounts)


@_awaits("audit E2-D11: 'Revenues of' was not read — EPAM, WERN and MVST carry no headline revenue")
def test_revenues_of_releases_carry_their_headline_revenue() -> None:
    expected = {
        ("EPAM", "0001352010-26-000043"): ("Q2 2026", 1415.0),
        ("EPAM", "0001352010-26-000026"): ("Q1 2026", 1400.0),
        ("WERN", "0000793074-26-000129"): ("Q2 2026", 933.9),
        ("WERN", "0000793074-26-000092"): ("Q1 2026", 808.6),
        ("WERN", "0000793074-26-000009"): ("Q4 2025", 737.6),
        ("MVST", "0001628280-26-055471"): ("Q2 2026", 87.3),
    }
    missing = [k for k, (p, v) in expected.items() if ("revenue", p, v) not in _rows(_release(*k))]
    assert not missing, f"no headline revenue row: {missing}"


@_awaits("audit E2-D15: WERN's and NFLX's 10-Qs state a ≤12m figure; the pages say none is stated")
def test_the_stated_twelve_month_walls_are_located() -> None:
    wern = _filing("WERN", "0000793074-26-000140")["maturity_wall"]
    nflx = _filing("NFLX", "0001065280-26-000291")["maturity_wall"]
    assert (wern["state"], wern["within_12m_total"]) == ("located", 0.0)
    assert (nflx["state"], nflx["within_12m_total"]) == ("located", 3194.0)
    assert nflx.get("basis") == "principal and interest"


@_awaits("audit E2-D16: VITL shows a receivables row (Customer C) as revenue concentration")
def test_vitl_concentration_carries_no_receivables_row() -> None:
    conc = _filing("VITL", "0001193125-26-336753")["concentration"]
    assert "Customer C" not in [c["name"] for c in conc["customers"]]
