"""The refresh back-fill reads EDGAR as filed by the page's PRICE DATE, the cut assembly reads it at
(operator ruling C4, 2026-11-01: "Inputs are cut at the page's price date (filed on or before it;
latest such filing wins; nothing after a sealed verdict)").

Three back-fill paths in `vinci/dossier/refresh.py` read companyfacts past that cut — the open item
of `docs/records/2026-11-02-inputs-are-cut-at-the-pages-price-date.md`:
- `lease_basis_transform` and `valuation_bases_transform` read today's companyfacts uncut;
- `statement_recon_transform` read them as filed by the page's ASSEMBLY date, after its price.

REAL DATA. NCNO's committed page is priced 2026-08-17, and its committed companyfacts
(`tests/fixtures/companyfacts/NCNO.json`) carry the 10-Q it filed on 2026-08-25 — 481 facts dated
after the page's close, the very shape the cut exists to keep out. TJX's frozen companyfacts carry
the Q2 FY27 10-Q it filed on 2026-08-28; a page priced the day before must not read it however
late it was assembled.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from vinci.dossier import statement_recon as sr
from vinci.dossier.refresh import RefreshRefusedError, statement_recon_transform

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "companyfacts"
NCNO_PRICE = date(2026, 8, 17)


def _fixture(t: str) -> dict[str, Any]:
    out: dict[str, Any] = json.loads((FIXTURES / f"{t}.json").read_text())
    return out


def _filed(facts: dict[str, Any] | None) -> set[str]:
    return {p["filed"] for tags in (facts or {}).get("facts", {}).values()
            for tag in tags.values() for pts in tag["units"].values() for p in pts if "filed" in p}


def _ncno_mech() -> dict[str, Any]:
    page = json.loads((ROOT / "data" / "dossiers" / "NCNO" / "dossier.json").read_text())
    assert page["mechanical"]["stock_info"]["as_of"] == NCNO_PRICE.isoformat()
    mech: dict[str, Any] = page["mechanical"]
    return mech


def test_the_ncno_fixture_holds_a_filing_after_the_pages_price_date() -> None:
    """The premise, pinned: without a filing past the close, the two tests below test nothing."""
    later = {d for d in _filed(_fixture("NCNO")) if d > NCNO_PRICE.isoformat()}
    assert later == {"2026-08-25"}


def _edgar_serves(monkeypatch: pytest.MonkeyPatch, t: str) -> None:
    import vinci.edgar.client as ec

    monkeypatch.setattr(ec.EdgarClient, "from_config", staticmethod(
        lambda *_a, **_k: SimpleNamespace(companyfacts=lambda _cik: _fixture(t))))


def test_the_lease_basis_refresh_reads_edgar_as_filed_by_the_pages_price_date(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """THE DEFECT: the lease basis was built from today's companyfacts, so NCNO's back-fill read
    the 2026-08-25 10-Q into a page priced 2026-08-17. The export is the page's own (its bands'
    stamp), stood in here; what `lease_basis` is handed is what is pinned."""
    import vinci.dossier.ciq as ciq
    import vinci.dossier.ciq_sheets as cs
    import vinci.dossier.lease_basis as lb
    import vinci.dossier.manual_store as ms
    from vinci.dossier import refresh as rf

    mech = _ncno_mech()
    (stamp,) = {b["source_sha256"] for b in mech["valuation"]["own_history"]["value"]}
    _edgar_serves(monkeypatch, "NCNO")
    monkeypatch.setattr(ms.LocalFolderStore, "from_config", staticmethod(
        lambda *_a, **_k: SimpleNamespace(files=lambda _t: [])))
    wb = SimpleNamespace(path=Path("NCNO_financials_quarterly.xlsx"))
    monkeypatch.setattr(ciq.CiqBundle, "from_files", staticmethod(
        lambda _t, _p: SimpleNamespace(workbook=lambda *_a, **_k: wb)))
    monkeypatch.setattr(cs, "file_provenance", lambda _p: (stamp, None))
    handed: list[dict[str, Any] | None] = []
    monkeypatch.setattr(lb, "lease_basis", lambda _b, facts: handed.append(facts))

    rf.lease_basis_transform("NCNO", "0001902733")(json.loads(json.dumps(mech)))

    assert len(handed) == 1
    filed = _filed(handed[0])
    assert max(filed) <= NCNO_PRICE.isoformat(), sorted(filed)[-3:]
    # (−) the cut is a cut, not an emptying: every filing on or before the close is still read
    assert filed == {d for d in _filed(_fixture("NCNO")) if d <= NCNO_PRICE.isoformat()}


def test_the_valuation_bases_refresh_reads_edgar_as_filed_by_the_pages_price_date(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """THE SAME DEFECT in the three basis blocks: `with_valuation_bases` — the builder assembly and
    the back-fill share — was handed today's companyfacts. It is now handed what assembly hands it,
    EDGAR as filed by the page's price date."""
    import vinci.dossier.manual_store as ms
    import vinci.sec as sec
    from vinci.dossier import mechanical as dm
    from vinci.dossier import refresh as rf

    _edgar_serves(monkeypatch, "NCNO")

    def _no_folder(_t: str) -> list[Path]:
        raise FileNotFoundError(_t)

    monkeypatch.setattr(ms.LocalFolderStore, "from_config", staticmethod(
        lambda *_a, **_k: SimpleNamespace(files=_no_folder)))
    monkeypatch.setattr(sec, "build_sec_http", lambda *_a, **_k: None)
    real = dm.with_valuation_bases
    handed: list[dict[str, Any] | None] = []

    def spy(mech: Any, facts: dict[str, Any] | None, *a: Any, **k: Any) -> Any:
        handed.append(facts)
        return real(mech, facts, *a, **k)

    monkeypatch.setattr(dm, "with_valuation_bases", spy)
    out = rf.valuation_bases_transform("NCNO", "0001902733")(_ncno_mech())

    assert len(handed) == 1
    filed = _filed(handed[0])
    assert max(filed) <= NCNO_PRICE.isoformat(), sorted(filed)[-3:]
    assert filed == {d for d in _filed(_fixture("NCNO")) if d <= NCNO_PRICE.isoformat()}
    # the blocks still land: the cut changes what is read, never whether the block is written
    assert out["valuation"]["ev_ebitda_basis"] is not None


def _tjx_doc(*, price: str | None, reference: str | None = "2026-08-14") -> dict[str, Any]:
    fs: dict[str, Any] = {"annual": {"value": {
        "columns": ["FY26", "LTM", "FY27E"], "is_estimate": [False, False, True],
        "rows": [{"label": "Revenue ($M)", "values": [60372.0, 62363.0, 64000.0]}]}}}
    mech: dict[str, Any] = {"financial_summary": fs}
    if price is not None:
        mech["stock_info"] = {"as_of": price}
    doc: dict[str, Any] = {"ticker": "TJX", "cik": "0000109198",
                           "assembled_at": "2026-10-21T11:18:48Z", "mechanical": mech}
    if reference is not None:
        doc["reference_date"] = reference
    return doc


_TJX_FIGURES = [sr.CiqFigure("revenue", "FY26", date(2026, 1, 31), False, 60372.0),
                sr.CiqFigure("revenue", "LTM", date(2026, 8, 1), True, 62363.0)]


class _Edgar:
    def companyfacts(self, cik: str) -> dict[str, Any]:
        return _fixture("TJX")


def _rows(doc: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    refused: list[str] = []
    out = statement_recon_transform(doc, edgar=_Edgar(), refused=refused,
                                    figures_for=lambda _t: _TJX_FIGURES)(doc["mechanical"])
    blk: dict[str, Any] = out["financial_summary"].get("statement_reconciliation") or {}
    return blk, refused


def test_the_tjx_fixture_files_its_q2_10q_on_2026_08_28() -> None:
    assert "2026-08-28" in _filed(_fixture("TJX")) and "2026-08-27" not in _filed(_fixture("TJX"))


def test_the_statement_reconciliation_reads_edgar_as_filed_by_the_pages_price_date() -> None:
    """THE DEFECT: the reconciliation was bounded at the page's assembly date (2026-10-21), so a
    page priced 2026-08-27 read TJX's Q2 10-Q, filed the next day, into its LTM row. Now the facts
    are cut at the price date, as assembly cuts them, and the LTM row has no filing to set beside
    it. The block still states the assembly date as its `as_filed_by`, as assembly writes it."""
    blk, refused = _rows(_tjx_doc(price="2026-08-27"))
    assert refused == []
    by_col = {r["column"]: r["filing"] for r in blk["rows"]}
    assert by_col == {"FY26": 60372.0, "LTM": None}
    assert blk["as_filed_by"] == "2026-10-21"


def test_negative_a_page_priced_after_the_filing_still_reads_it() -> None:
    """(−) Priced on the filing's own day, the cut is inclusive (`asof.within_cut`)."""
    blk, refused = _rows(_tjx_doc(price="2026-08-28"))
    assert refused == []
    assert {r["column"]: r["filing"] for r in blk["rows"]} == {"FY26": 60372.0, "LTM": 62363.0}


def test_a_page_with_no_close_is_cut_at_its_reference_date() -> None:
    """`asof.page_price_date`'s fallback: no stored close → the page's reference date."""
    blk, _ = _rows(_tjx_doc(price=None, reference="2026-08-14"))
    assert {r["column"]: r["filing"] for r in blk["rows"]}["LTM"] is None
    blk, _ = _rows(_tjx_doc(price=None, reference="2026-09-01"))
    assert {r["column"]: r["filing"] for r in blk["rows"]}["LTM"] == 62363.0


def test_a_page_with_neither_date_is_refused_not_read_uncut() -> None:
    with pytest.raises(RefreshRefusedError, match="price date"):
        statement_recon_transform(_tjx_doc(price=None, reference=None), edgar=_Edgar(),
                                  refused=[])
