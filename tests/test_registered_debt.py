"""A LINE ITS ISSUER REGISTERS AS DEBT LEAVES THE UNIVERSE (2026-10-27), whatever the feed types it.

The reference feed types 58 debt lines `CS` in its 2026-10-17 pull (ADAMK "Adamas Trust, Inc.
9.600% Senior Notes Due 2031", TMUSI, XELLL ...), so the instrument allowlist admits them. ADAMK
sat in the primary population until 2026-09-01 and left only because ADAM out-traded it; the 2,113
sign-off named the residual: "a mistyped line that is its issuer's MOST traded would still be
admitted".

The deterministic field is the issuer's own: the cover page of its latest periodic report tags every
12(b) security with `dei:TradingSymbol` and `dei:Security12bTitle` in one context. Every cover below
is REAL — the verbatim tags, frozen in `tests/fixtures/cover_page_12b_titles.json`.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci import universe as uni
from vinci.config import Config
from vinci.eod import RawBar
from vinci.resolver import EntityResolver
from vinci.resolver.instrument import (
    RegisteredLine,
    cover_lines,
    is_debt_title,
    latest_periodic,
    registered_line,
    symbol_key,
)
from vinci.schemas.data_record import Identity
from vinci.universe import build_universe

_FIX = json.loads((Path(__file__).parent / "fixtures" / "cover_page_12b_titles.json").read_text())
_COVERS: dict[str, dict[str, Any]] = _FIX["covers"]
_ADAMAS = "0001273685"


def _html(issuer: str) -> str:
    return "".join(_COVERS[issuer]["ix"])


def _line(issuer: str, ticker: str) -> RegisteredLine | None:
    c = _COVERS[issuer]
    return registered_line(_html(issuer), ticker, form=c["form"],
                           filed=date.fromisoformat(c["filed"]), accession=c["accession"])


# --- the title rule, on every real title in the fixture ------------------------------------------

def test_every_note_on_a_real_cover_reads_as_debt() -> None:
    """POSITIVE: each issuer's own debt titles — senior notes with a year, a month and a year, and a
    plain "Notes due" (Brown-Forman's euro note)."""
    debt = [(issuer, sym, title) for issuer in _COVERS
            for sym, title in cover_lines(_html(issuer)) if title and "Notes" in title]
    # 12 T-Mobile + 4 Adamas + 3 Coca-Cola FEMSA (registered, no US symbol) + Brunswick + B-F
    assert len(debt) == 21, debt
    assert [d for d in debt if not is_debt_title(d[2])] == []
    assert is_debt_title("5.500% Senior Notes due March 2070")   # TMUSZ, verbatim


def test_equity_titles_on_real_covers_never_read_as_debt() -> None:
    """NEGATIVE: common in five spellings, LP units, an ADS of units, cumulative preferred and a
    mandatory-convertible preferred depositary. None is debt; the rule infers nothing else."""
    titles = [t for issuer in _COVERS for _s, t in cover_lines(_html(issuer))
              if t and "Notes" not in t]
    assert len(titles) == 18, titles
    assert not [t for t in titles if is_debt_title(t)]
    assert not is_debt_title(None)


def test_a_symbol_is_matched_however_it_is_spelled() -> None:
    """SEC writes UHAL-B, U-Haul's cover writes UHAL.B, Brown-Forman's writes BFB."""
    assert symbol_key("UHAL-B") == symbol_key("UHAL.B") == "UHALB"
    reg = _line("Brown-Forman", "BF-B")
    assert reg is not None and reg.symbol == "BFB" and not reg.is_debt
    reg = _line("U-Haul Holding", "UHAL-B")
    assert reg is not None and reg.title == "Series N Non-Voting Common Stock, $0.001 par value"


def test_a_symbol_absent_from_the_cover_is_not_evidence() -> None:
    """ADAMK listed on 2026-08-14 (its 8-A12B), after Adamas's 2026-07-31 10-Q, so that cover does
    not carry it. Absence is not a title: the reader says None, never 'debt'."""
    assert _line("Adamas Trust", "ADAMK") is None
    reg = _line("Adamas Trust", "ADAMG")
    assert reg is not None and reg.is_debt and reg.accession == "0001273685-26-000069"


# --- which cover: the latest periodic report filed by the build's date ----------------------------

def test_the_cover_is_the_latest_periodic_report_filed_by_the_reference_date() -> None:
    """POINT IN TIME. Adamas's real filing index: an 8-K, an 8-A12B, two 424B5s and an S-3ASR are
    not periodic reports; a 10-Q filed after the reference date is not yet the issuer's word."""
    subs = {"filings": {"recent": _FIX["adamas_recent_filings"]}}
    assert latest_periodic(subs, date(2026, 10, 16)) == (
        "10-Q", date(2026, 7, 31), "0001273685-26-000069", "adam-20260630.htm")
    assert latest_periodic(subs, date(2026, 7, 30)) == (
        "10-Q", date(2026, 5, 1), "0001273685-26-000045", "adam-20260331.htm")
    assert latest_periodic({"filings": {"recent": {}}}, date(2026, 10, 16)) is None


class _Http:
    """Serves the frozen submissions block and the frozen cover — and records what was asked."""

    def __init__(self) -> None:
        self.asked: list[tuple[str, float | None]] = []

    def get_json(self, url: str, *, ttl_seconds: float | None = None,
                 params: object = None) -> Any:
        assert url.endswith(f"CIK{_ADAMAS}.json"), url
        return {"filings": {"recent": _FIX["adamas_recent_filings"]}}

    def get_text(self, url: str, *, ttl_seconds: float | None = None,
                 params: object = None) -> str:
        self.asked.append((url, ttl_seconds))
        assert url == _COVERS["Adamas Trust"]["url"], url
        return _html("Adamas Trust")


def test_the_resolver_reads_the_cover_its_filing_index_names() -> None:
    """End to end through `EntityResolver.registered_line`: the filing index names the document,
    the document is read once and cached for good (a filed document never changes)."""
    http = _Http()
    resolver = EntityResolver(http=http)  # type: ignore[arg-type]
    reg = resolver.registered_line(_ADAMAS, "ADAMG", date(2026, 10, 16))
    assert reg == RegisteredLine(symbol="ADAMG", title="9.125% Senior Notes due 2030",
                                 form="10-Q", filed=date(2026, 7, 31),
                                 accession="0001273685-26-000069")
    assert http.asked == [(_COVERS["Adamas Trust"]["url"], None)]
    assert resolver.registered_line(_ADAMAS, "ADAM", date(2026, 10, 16)).is_debt is False  # type: ignore[union-attr]


# --- the gate, through the REAL builder -----------------------------------------------------------

#: Adamas Trust on 2026-10-16: closes and 90-day ADVs from the grouped-daily bars; the common's
#: per-class count from Polygon (89,879,786 — the same count the filed XBRL tier gives).
_CLOSE = {"ADAM": 7.64, "ADAMG": 24.43}
_ADV = {"ADAM": 8_973_284.438597068, "ADAMG": 339_652.5510874353}
_COUNT = 89_879_786.0


def _adamas(ticker: str) -> Identity:
    return Identity(internal_id=f"SEC-{_ADAMAS}-{ticker}", issuer_id=f"ISS-{_ADAMAS}",
                    cik=_ADAMAS, ticker=ticker, mic="XNAS", exchange="Nasdaq",
                    eod_symbol=ticker, name="Adamas Trust, Inc.")


def _run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, adv: dict[str, float],
         types: dict[str, str] | None = None) -> tuple[dict, set[str], list[dict]]:
    idents = [_adamas("ADAM"), _adamas("ADAMG")]
    ref = date(2026, 10, 16)

    class _R:
        @classmethod
        def from_config(cls, cfg: object) -> _R: return cls()
        def iter_universe(self, exchanges: object) -> Iterator[Identity]: yield from idents
        def sic_for(self, cik: str) -> tuple[str, str]: return ("6798", "Real Estate Inv Trusts")
        def registered_line(self, cik: str, ticker: str, as_of: date) -> RegisteredLine | None:
            assert as_of == ref
            return _line("Adamas Trust", ticker)

    class _E:
        @classmethod
        def from_config(cls, cfg: object) -> _E: return cls()
        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            if day != ref:
                return {}
            return {t: RawBar(ticker=t, open=p, high=p, low=p, close=p, volume=adv[t] / p)
                    for t, p in _CLOSE.items()}
        def security_types(self) -> dict[str, str]: return types or {"ADAM": "CS", "ADAMG": "CS"}
        def share_class_counts(self, tickers: object) -> dict[str, float]:
            return {"ADAM": _COUNT} if "ADAM" in tickers else {}  # type: ignore[operator]

    class _Ed:
        @classmethod
        def from_config(cls, cfg: object) -> _Ed: return cls()
        def shares_outstanding_with_provenance(
            self, periods: object, *, include_period_average: bool = False
        ) -> tuple[dict[str, float], dict[str, str]]:
            return {_ADAMAS: _COUNT}, {_ADAMAS: "dei:EntityCommonStockSharesOutstanding"}

    monkeypatch.setattr(uni, "EntityResolver", _R)
    monkeypatch.setattr(uni, "PolygonEodClient", _E)
    monkeypatch.setattr(uni, "EdgarClient", _Ed)
    stats = build_universe(Config(data_dir=tmp_path), reference_date=ref,
                           share_periods=["CY2026Q2I"], retain_run_id="2026-10-16-01",
                           retain_dir=tmp_path / "retain")
    snap = tmp_path / "snapshots" / "universe_snapshot.jsonl"
    admitted = {json.loads(x)["internal_id"].split("-", 2)[2]
                for x in snap.read_text().splitlines() if x.strip()}
    from vinci.screens.retention import run_path
    rows = [json.loads(x) for x in run_path("2026-10-16-01", tmp_path / "retain").read_text()
            .splitlines() if x.strip()]
    return stats, admitted, rows


def test_a_registered_note_that_out_trades_its_common_is_not_admitted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THE CASE THE SIGN-OFF LEFT OPEN. Every input is Adamas's real 2026-10-16 state except ONE:
    ADAMG's ADV is raised from $0.34M to $9.5M, past the common's $8.97M — the only way a note
    reaches this gate today: on 2026-10-16 each of the 58 fails the band, the $3M ADV floor or the
    share count first. Before the
    cover was read, the note took the issuer's slot; now it leaves on its own title."""
    stats, admitted, rows = _run(monkeypatch, tmp_path,
                                 adv={"ADAM": _ADV["ADAM"], "ADAMG": 9_500_000.0})
    assert admitted == {"ADAM"}, "a senior note was admitted as the issuer's equity"
    [drop] = [r for r in rows if r["ticker"] == "ADAMG"]
    assert drop["stage"] == "non_common_equity"
    assert "9.125% Senior Notes due 2030" in drop["reason"]
    assert drop["deciding_input"] == {
        "value": "9.125% Senior Notes due 2030", "as_of": "2026-07-31",
        "source": "SEC 10-Q 0001273685-26-000069 cover page (dei:Security12bTitle)",
        "note": None, "span_days": None, "observations": None}
    assert stats.get("duplicate_class", 0) == 0, "the note never competed for the slot"


def test_the_common_on_the_same_cover_is_admitted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """NEGATIVE, same cover: the common the issuer registers as "Common Stock" is untouched — sized
    and admitted exactly as before, by its own count."""
    stats, admitted, _ = _run(monkeypatch, tmp_path, adv=_ADV)
    assert "ADAM" in admitted
    assert stats["in_universe"] == 1

