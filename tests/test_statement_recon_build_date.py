"""The statement reconciliation is dated by the filings it read, never by the day it was built
(operator ruling 2 of 2026-11-12, relayed on #1004: "Fix now, by B (Recommended)").

THE DEFECT. Assembly called `statement_recon.attach(..., filed_by=datetime.now(UTC).date())`, so
`financial_summary.statement_reconciliation.as_filed_by` held the build's own UTC date, and a row
with no filing figure said "as filed by <that date>". Both reach the synthesis request's facts, so
the same code on the same inputs sent different requests on different days: A's impact sweep found
it on BURL and CNXC, panel pages, through #984. The facts were already cut at the page's price date
(`AsOfEdgar`), so the date was not even the cut the block was read at.

NOW the block reads the facts as filed by the page's price date, a row with no figure names that
date, and `as_filed_by` is the latest filing date of the filings the rows read (each row's
`accession`) — None when no row read one.

REAL DATA. NIKE's committed companyfacts (`tests/fixtures/companyfacts/NKE.json`, May fiscal year;
its Q1 FY27 10-Q 0000320187-26-000193 was filed 2026-10-02) and its stored bars
(`tests/fixtures/prices/NKE.jsonl`, to 2026-10-16), against the committed synthetic CIQ exports
(`tests/fixtures/ciq_synthetic`, whose fiscal years also end May 31 and whose LTM ends 2026-08-31).
The CIQ figures are invented, so every row differs from its filing; the dates are NIKE's own.
"""
from __future__ import annotations

import datetime as _dt
import json
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.dossier import statement_recon as sr

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
NKE_10Q = "0000320187-26-000193"        # Q1 FY27, to 2026-08-31, filed 2026-10-02
NKE_10K = "0000320187-26-000088"        # FY26, to 2026-05-31, filed 2026-07-15


# --- a faked UTC day ------------------------------------------------------------------------------


#: the real class, held before any fake replaces the module's attribute
_REAL_DATETIME = _dt.datetime


class _DatetimeMeta(type):
    def __instancecheck__(cls, obj: Any) -> bool:
        return isinstance(obj, _REAL_DATETIME)

    def __subclasscheck__(cls, sub: Any) -> bool:
        return isinstance(sub, type) and issubclass(sub, _REAL_DATETIME)


_AT: list[_dt.datetime] = []


class _FrozenDatetime(_dt.datetime, metaclass=_DatetimeMeta):
    """`datetime` whose `now` is the faked instant; every other method is the real class's."""

    @classmethod
    def now(cls, tz: _dt.tzinfo | None = None) -> _dt.datetime:  # type: ignore[override]
        # naive `now()` is LOCAL wall time, as the real call's is
        if tz is not None:
            return _AT[0].astimezone(tz)
        return _AT[0].astimezone().replace(tzinfo=None)

    @classmethod
    def utcnow(cls) -> _dt.datetime:  # type: ignore[override]
        return _AT[0].astimezone(_dt.UTC).replace(tzinfo=None)


@contextmanager
def _utc_day(at: _dt.datetime) -> Iterator[None]:
    """Every clock a page build reads, set to ``at``: ``date.today()`` (it reads `time.time`) and
    ``datetime.now()``, three ways — each loaded `vinci` module's own binding of the class, and the
    `datetime` module's attribute, which a function-local ``from datetime import datetime`` and a
    ``datetime.datetime.now`` both read (review: a mutant importing the class inside
    `assemble_mechanical` passed the first version of this fake). A module imported for the first
    time inside the block reads the module's attribute, so it is faked too; the caller still
    builds once BEFORE (`_warm`), so no import happens inside it."""
    _AT[:] = [at]
    undo: list[tuple[Any, str, Any]] = [(time, "time", time.time),
                                        (_dt, "datetime", _REAL_DATETIME)]
    time.time = lambda: at.timestamp()
    _dt.datetime = _FrozenDatetime  # type: ignore[misc]
    try:
        for name, mod in list(sys.modules.items()):
            if mod is not None and (name == "vinci" or name.startswith("vinci.")):
                for attr, val in list(vars(mod).items()):
                    if val is _REAL_DATETIME:
                        undo.append((mod, attr, val))
                        setattr(mod, attr, _FrozenDatetime)
        yield
    finally:
        for mod, attr, val in reversed(undo):
            setattr(mod, attr, val)


# --- NIKE's page, assembled offline ---------------------------------------------------------------


def _assemble_nke(last_close: _dt.date = _dt.date(2026, 10, 16)) -> Any:
    """NIKE's mechanical layer, assembled on its real companyfacts and on its stored bars up to
    ``last_close`` (the page's price date), with the synthetic CIQ exports and no network: every
    other SEC request is refused, as `tests/test_asof_cut.py`'s harness refuses it."""
    from tests.test_asof_cut import _iwm_bars, _Refused
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.mechanical import assemble_mechanical
    from vinci.edgar.client import EdgarClient
    from vinci.graph.exposure import ExposureGraph
    from vinci.netcache import CachedHttp, HttpError
    from vinci.schemas.data_record import Identity
    from vinci.schemas.market import PriceBar
    from vinci.screens.assemble import build_price_record, enrich_with_fundamentals

    facts = json.loads((FIX / "companyfacts" / "NKE.json").read_text())
    bars = [b for b in (PriceBar(**json.loads(x)) for x in
                        (FIX / "prices" / "NKE.jsonl").read_text().splitlines() if x.strip())
            if b.bar_date <= last_close]

    class Sec:
        def get_json(self, url: str, **_k: Any) -> dict[str, Any]:
            if "/companyfacts/" in url:
                return cast(dict[str, Any], facts)
            raise HttpError(f"not served: {url}")

        def get_text(self, url: str, **_k: Any) -> str:
            raise HttpError(f"not served: {url}")

    class Store:
        def get_price_history(self, internal_id: str) -> list[PriceBar]:
            return bars if internal_id.endswith("-NKE") else _iwm_bars()

        def price_frontier(self) -> _dt.date:
            return last_close

    ident = Identity(internal_id="SEC-0000320187-NKE", issuer_id="ISS-0000320187",
                     cik="0000320187", ticker="NKE", mic="XNYS", exchange="NYSE",
                     eod_symbol="NKE", name="NIKE, Inc.", sic="3021")
    sec = Sec()
    edgar = EdgarClient(http=cast(CachedHttp, sec))
    rec = build_price_record(ident, price_bars=bars, benchmark_bars=_iwm_bars(),
                             reference_date=last_close, staleness_days=5)
    rec = enrich_with_fundamentals(rec, edgar=edgar, price_bars=bars, reference_date=last_close)
    bundle = CiqBundle.from_files("NKE", sorted([*(gen.HERE / gen.TICKER).iterdir(),
                                                 gen.HERE / gen.ESTIMATES_XLS]))
    mech, _flags = assemble_mechanical(
        rec, store=cast(Any, Store()), edgar=edgar, http=cast(CachedHttp, sec),
        finra=cast(Any, _Refused()), graph=ExposureGraph(), resolver=cast(Any, None),
        bundle=bundle, reference_date=last_close)
    return mech


def _request(mech: Any) -> str:
    """The synthesis request for the layer, captured as the impact check captures it
    (`vinci.evals.capture_child`, nothing sent), the layer marked material first as
    `assemble_one` marks it."""
    from vinci.dossier.assemble import _mark_material
    from vinci.evals.capture_child import capture_calls, jsonable

    page = {"ticker": "NKE", "name": "NIKE, Inc.", "sleeve": "overshoot",
            "mechanical": json.loads(_mark_material(mech).model_dump_json())}
    return json.dumps([jsonable(c) for c in capture_calls(page, None, draws=1)])


@pytest.fixture(scope="module")
def _warm() -> Any:
    return _assemble_nke()


def _recon(mech: Any) -> Any:
    fs = mech.financial_summary
    assert fs is not None and fs.statement_reconciliation is not None
    return fs.statement_reconciliation


# --- the request ----------------------------------------------------------------------------------


@pytest.mark.parametrize("last_close", [_dt.date(2026, 10, 16), _dt.date(2026, 9, 30)])
def test_the_same_inputs_built_on_two_utc_days_send_byte_identical_requests(
        _warm: Any, last_close: _dt.date) -> None:
    """FAILED at main, at both price dates. Priced 2026-10-16, every row reads a filing and the one
    line that differed was `"as_filed_by"` ("2026-10-18" against "2026-10-21"). Priced 2026-09-30,
    before the 10-Q, the LTM rows have no figure, and their notes carried the build's day too: the
    only place a clock read inside the block can still show (review: a mutant restoring
    `filed_by=datetime.now(UTC).date()` passed the first price date alone). Both days fall within
    the 7 days the price-staleness note allows (`mechanical._ASSEMBLY_PRICE_STALE_DAYS`) after
    each close, so the clock read assembly makes on purpose stays silent on both."""
    assert _recon(_warm).rows, "the reconciliation must read NIKE's filings, or this proves nothing"
    sent = []
    # noon UTC: `date.today()` reads the LOCAL calendar, which is the UTC day from UTC-11 to +11
    for lag in (2, 5):
        day = last_close + _dt.timedelta(days=lag)
        at = _dt.datetime(day.year, day.month, day.day, 12, 0, tzinfo=_dt.UTC)
        with _utc_day(at):
            assert _dt.date.today() == day                # the fake reaches both clocks
            sent.append(_request(_assemble_nke(last_close)))
    assert sent[0] == sent[1]


def test_the_faked_day_reaches_a_clock_read_that_is_still_made(_warm: Any) -> None:
    """(−) The fake is not inert: a close older than the staleness bound on the faked day prints the
    faked day's gap (`mechanical._price_stale_note`), so the identity above is not a fake that
    changed nothing."""
    with _utc_day(_dt.datetime(2026, 11, 1, 12, 0, tzinfo=_dt.UTC)):
        note = _assemble_nke().stock_info.price.note or ""
    assert "16 calendar days before assembly" in note


# --- the date the block states --------------------------------------------------------------------


def test_the_block_is_dated_by_the_latest_filing_its_rows_read(_warm: Any) -> None:
    """(−) A REAL FILING DATE STILL REACHES THE FIELD. FAILED at main (the build's UTC day): the
    LTM rows read NIKE's Q1 FY27 10-Q, filed 2026-10-02, the latest filing any row names."""
    rec = _recon(_warm)
    assert {r.accession for r in rec.rows if r.is_ltm} == {NKE_10Q}
    assert rec.as_filed_by == "2026-10-02"


def test_a_filing_after_the_price_date_is_neither_read_nor_the_blocks_date() -> None:
    """Priced 2026-09-30, two days before the 10-Q: the LTM rows have no figure and say so AS FILED
    BY THE PRICE DATE, and the block is dated by the FY26 10-K (filed 2026-07-15), the latest filing
    a row read — not the price date, and not the build's day. FAILED at main (the build's UTC day,
    in the field and in both LTM notes)."""
    rec = _recon(_assemble_nke(_dt.date(2026, 9, 30)))
    ltm = [r for r in rec.rows if r.is_ltm]
    assert ltm and all(r.filing is None and "as filed by 2026-09-30" in (r.note or "")
                       for r in ltm)
    assert {r.accession for r in rec.rows if not r.is_ltm and r.column == "FY26"} == {NKE_10K}
    assert rec.as_filed_by == "2026-07-15"


# --- `reconcile` itself ---------------------------------------------------------------------------


def _tjx() -> dict[str, Any]:
    out: dict[str, Any] = json.loads((FIX / "companyfacts" / "TJX.json").read_text())
    return out


def test_a_block_whose_rows_read_no_filing_states_no_date() -> None:
    """None, never a date: TJX's FY26 10-K was filed 2026-03-31, so as filed by 2026-03-30 the row
    has no filing figure and the block read no filing. FAILED at main ("2026-03-30")."""
    fig = sr.CiqFigure("revenue", "FY26", _dt.date(2026, 1, 31), False, 60372.0)
    rec = sr.reconcile([fig], _tjx(), filed_by=_dt.date(2026, 3, 30))
    assert rec is not None and rec.rows[0].filing is None
    assert rec.as_filed_by is None


def test_the_date_is_the_latest_of_the_rows_filings_not_the_cut() -> None:
    """(−) Two rows, two filings: the FY26 10-K (2026-03-31) and the Q2 10-Q (2026-08-28) the LTM
    is composed from. As filed by 2026-10-21 the block is dated 2026-08-28. FAILED at main
    ("2026-10-21", the date passed in)."""
    figs = [sr.CiqFigure("revenue", "FY26", _dt.date(2026, 1, 31), False, 60372.0),
            sr.CiqFigure("revenue", "LTM", _dt.date(2026, 8, 1), True, 62363.0)]
    rec = sr.reconcile(figs, _tjx(), filed_by=_dt.date(2026, 10, 21))
    assert rec is not None
    assert [r.accession for r in rec.rows] == ["0000109198-26-000008", "0000109198-26-000048"]
    assert rec.as_filed_by == "2026-08-28"
