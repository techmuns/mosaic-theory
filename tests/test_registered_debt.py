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
    match_line,
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
    """NEGATIVE: common in five spellings, LP units, an ADS of units, cumulative preferred, a
    mandatory-convertible preferred depositary and a rights-plan preferred. None is debt."""
    titles = [t for issuer in _COVERS for _s, t in cover_lines(_html(issuer))
              if t and "Notes" not in t]
    assert len(titles) == 20, titles
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


#: a Part III 10-K/A filed after the 10-Q — the shape of a periodic report whose cover tags no
#: trading symbol (its accession and document are invented; its form is the real case's)
_UNTAGGED = ("10-K/A", "2026-09-30", "0001273685-26-000080", "adam-20251231x10ka.htm")
_UNTAGGED_URL = ("https://www.sec.gov/Archives/edgar/data/1273685/000127368526000080/"
                 "adam-20251231x10ka.htm")


class _Http:
    """Serves the frozen submissions block and the frozen cover — and records what was asked."""

    def __init__(self, *, with_untagged_amendment: bool = False) -> None:
        self.asked: list[tuple[str, float | None]] = []
        recent = {k: list(v) for k, v in _FIX["adamas_recent_filings"].items()}
        if with_untagged_amendment:
            for k, v in zip(("form", "filingDate", "accessionNumber", "primaryDocument"),
                            _UNTAGGED, strict=True):
                recent[k].insert(0, v)
        self._recent = recent

    def get_json(self, url: str, *, ttl_seconds: float | None = None,
                 params: object = None) -> Any:
        assert url.endswith(f"CIK{_ADAMAS}.json"), url
        return {"filings": {"recent": self._recent}}

    def get_text(self, url: str, *, ttl_seconds: float | None = None,
                 params: object = None) -> str:
        self.asked.append((url, ttl_seconds))
        if url == _UNTAGGED_URL:
            return "<html><body>Amendment No. 1 — Part III only</body></html>"
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
                                 accession="0001273685-26-000069", common_elsewhere=True)
    reg = resolver.registered_line(_ADAMAS, "ADAM", date(2026, 10, 16))
    assert reg is not None and not reg.is_debt
    # one issuer's lines share one cover: the document is read and parsed once
    assert http.asked == [(_COVERS["Adamas Trust"]["url"], None)]


def test_a_cover_that_tags_no_symbol_defers_to_the_report_before_it() -> None:
    """A Part III 10-K/A tags no trading symbol. Taken as "the cover" it would hide the 10-Q's —
    ADAMG's notes title among them — until the next quarter. The newest cover that DOES tag its
    symbols is read instead."""
    http = _Http(with_untagged_amendment=True)
    reg = EntityResolver(http=http).registered_line(  # type: ignore[arg-type]
        _ADAMAS, "ADAMG", date(2026, 10, 16))
    assert reg is not None and reg.is_debt and reg.accession == "0001273685-26-000069"
    assert [u for u, _ in http.asked] == [_UNTAGGED_URL, _COVERS["Adamas Trust"]["url"]]
    # the negative: a report filed after the reference date is not read at all
    http = _Http(with_untagged_amendment=True)
    EntityResolver(http=http).registered_line(  # type: ignore[arg-type]
        _ADAMAS, "ADAMG", date(2026, 9, 29))
    assert [u for u, _ in http.asked] == [_COVERS["Adamas Trust"]["url"]]


def test_a_symbol_tagged_twice_is_debt_only_if_every_context_says_so() -> None:
    """Mission Produce's real cover tags AVO to its rights-plan preferred, not its common. A cover
    that tagged a common's symbol into a notes context too must not exclude the common; a symbol
    whose only context is a note still reads as debt."""
    c = _COVERS["Brown-Forman"]
    meta = {"form": c["form"], "filed": date.fromisoformat(c["filed"]), "accession": c["accession"]}
    lines = cover_lines(_html("Brown-Forman"))
    note = next(t for s, t in lines if s == "BF28")
    common = next(t for s, t in lines if s == "BFB")
    twice = match_line([("BFB", note), ("BFB", common)], "BF-B", **meta)
    assert twice is not None and not twice.is_debt and twice.title == common
    only = match_line([("BFB", note)], "BF-B", **meta)
    assert only is not None and only.is_debt


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


def _build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, cover: str, idents: list[Identity],
           ref: date, closes: dict[str, float], adv: dict[str, float],
           class_counts: dict[str, float], filed_count: float, types: dict[str, str],
           sic: tuple[str, str], band_name: str = "primary",
           ) -> tuple[dict, set[str], list[dict]]:
    """The REAL builder over one issuer's lines, its cover read from the frozen fixture."""
    cik = idents[0].cik
    run_id = f"{ref.isoformat()}-01"

    class _R:
        @classmethod
        def from_config(cls, cfg: object) -> _R: return cls()
        def iter_universe(self, exchanges: object) -> Iterator[Identity]: yield from idents
        def sic_for(self, cik: str) -> tuple[str, str]: return sic
        def registered_line(self, cik: str, ticker: str, as_of: date) -> RegisteredLine | None:
            assert as_of == ref
            return _line(cover, ticker)
        def latest_report(self, *_: object) -> None: return None       # domestic 10-Q filers

    class _E:
        @classmethod
        def from_config(cls, cfg: object) -> _E: return cls()
        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            if day != ref:
                return {}
            # one bar, so ADV = close x volume = the measured 90-day ADV
            return {t: RawBar(ticker=t, open=p, high=p, low=p, close=p, volume=adv[t] / p)
                    for t, p in closes.items()}
        def security_types(self) -> dict[str, str]: return types
        def share_class_counts(self, tickers: object) -> dict[str, float]:
            return {t: class_counts[t] for t in tickers if t in class_counts}  # type: ignore[attr-defined]

    class _Ed:
        @classmethod
        def from_config(cls, cfg: object) -> _Ed: return cls()
        def shares_outstanding_with_provenance(
            self, periods: object, *, include_period_average: bool = False
        ) -> tuple[dict[str, float], dict[str, str]]:
            return {cik: filed_count}, {cik: "dei:EntityCommonStockSharesOutstanding"}

    monkeypatch.setattr(uni, "EntityResolver", _R)
    monkeypatch.setattr(uni, "PolygonEodClient", _E)
    monkeypatch.setattr(uni, "EdgarClient", _Ed)
    stats = build_universe(Config(data_dir=tmp_path), reference_date=ref,
                           share_periods=["CY2026Q2I"], band_name=band_name,
                           retain_run_id=run_id, retain_dir=tmp_path / "retain")
    table = "universe_snapshot" if band_name == "primary" else "theme_universe_snapshot"
    snap = tmp_path / "snapshots" / f"{table}.jsonl"
    admitted = {json.loads(x)["internal_id"].split("-", 2)[2]
                for x in snap.read_text().splitlines() if x.strip()}
    from vinci.screens.retention import run_path
    rows = [json.loads(x) for x in run_path(run_id, tmp_path / "retain").read_text()
            .splitlines() if x.strip()]
    return stats, admitted, rows


def _run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *,
         adv: dict[str, float]) -> tuple[dict, set[str], list[dict]]:
    return _build(monkeypatch, tmp_path, cover="Adamas Trust",
                  idents=[_adamas("ADAM"), _adamas("ADAMG")], ref=date(2026, 10, 16),
                  closes=_CLOSE, adv=adv, class_counts={"ADAM": _COUNT}, filed_count=_COUNT,
                  types={"ADAM": "CS", "ADAMG": "CS"}, sic=("6798", "Real Estate Inv Trusts"))


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



# --- preferred: excluded only beside a common the same cover registers under another symbol -------

_MCHP = "0000827054"
_FEED = _FIX["polygon_reference_2026_10_17"]


def test_a_preferred_depositary_beside_its_common_is_excluded() -> None:
    """POSITIVE — MCHPP, on Microchip's real 10-Q cover (filed 2026-08-06): "Depositary Shares, each
    representing a 1/20th interest in a share of 7.50% Series A Mandatory Convertible Preferred
    Stock", beside "Common Stock" registered as MCHP. The feed's own record types it CS."""
    assert _FEED["MCHPP"]["type"] == "CS"
    reg = _line("Microchip Technology", "MCHPP")
    assert reg is not None and reg.common_elsewhere and reg.excluded_class == "preferred"
    # ...and every preferred series Adamas registers beside ADAM
    for sym in ("ADAMN", "ADAMM", "ADAML", "ADAMZ"):
        assert _line("Adamas Trust", sym).excluded_class == "preferred"  # type: ignore[union-attr]


def test_the_issuers_common_is_never_excluded() -> None:
    """NEGATIVE, same issuers: MCHP, ADAM, UHAL / UHAL.B and Brown-Forman's two common classes."""
    for cover, sym in (("Microchip Technology", "MCHP"), ("Adamas Trust", "ADAM"),
                       ("U-Haul Holding", "UHAL"), ("U-Haul Holding", "UHAL-B"),
                       ("Brown-Forman", "BF-A"), ("Brown-Forman", "BF-B")):
        reg = _line(cover, sym)
        assert reg is not None and reg.excluded_class is None, (cover, sym, reg)


def test_a_preferred_title_without_a_common_elsewhere_excludes_nothing() -> None:
    """THE OBSERVED FAILURE SHAPE — Mission Produce's real cover (10-Q filed 2026-09-08) tags AVO,
    its COMMON stock ("Mission Produce, Inc. Common Stock" in the feed's own record), to "Series A
    Junior Participating Preferred Stock" — its rights plan — and leaves "Common Stock" with no
    symbol. A preferred title alone would delete a common stock from the population."""
    assert _FEED["AVO"]["type"] == "CS"
    reg = _line("Mission Produce", "AVO")
    assert reg is not None and "Preferred" in (reg.title or "")
    assert not reg.common_elsewhere and reg.excluded_class is None


#: Microchip on 2026-09-22, the second weekly MCHPP sat in the primary population: closes and
#: 90-day ADVs from the grouped-daily bars; per-class counts from Polygon (MCHPP's 27,000,000 is its
#: committed $1,746.9M cap at $64.70; MCHP's 543,008,370 its share_class_shares_outstanding).
_MCHP_CLOSE = {"MCHP": 75.82, "MCHPP": 64.70}
_MCHP_ADV = {"MCHP": 821_380_364.9841999, "MCHPP": 15_899_610.073576568}
_MCHP_COUNT = {"MCHP": 543_008_370.0, "MCHPP": 27_000_000.0}


def _microchip(ticker: str) -> Identity:
    return Identity(internal_id=f"SEC-{_MCHP}-{ticker}", issuer_id=f"ISS-{_MCHP}", cik=_MCHP,
                    ticker=ticker, mic="XNAS", exchange="Nasdaq", eod_symbol=ticker,
                    name="MICROCHIP TECHNOLOGY INC")


def _run_microchip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                   band_name: str) -> tuple[dict, set[str], list[dict]]:
    return _build(monkeypatch, tmp_path, cover="Microchip Technology",
                  idents=[_microchip("MCHP"), _microchip("MCHPP")], ref=date(2026, 9, 22),
                  closes=_MCHP_CLOSE, adv=_MCHP_ADV, class_counts=_MCHP_COUNT,
                  filed_count=_MCHP_COUNT["MCHP"],
                  types={t: _FEED[t]["type"] for t in ("MCHP", "MCHPP")},
                  sic=("3674", "Semiconductors & Related Devices"), band_name=band_name)


def test_mchpp_leaves_the_population_it_sat_in(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THE REAL CASE. On 2026-09-22 MCHPP was a $1.75B line in the $300M-$10B primary band and was
    screened; MCHP, $41.2B, was out of band. Now the preferred leaves on its own title."""
    stats, admitted, rows = _run_microchip(monkeypatch, tmp_path, "primary")
    assert "MCHPP" not in admitted, "a preferred depositary was admitted as Microchip's equity"
    [drop] = [r for r in rows if r["ticker"] == "MCHPP"]
    assert drop["stage"] == "non_common_equity"
    assert "a preferred security" in drop["reason"]
    assert drop["deciding_input"]["source"] == (
        "SEC 10-Q 0000827054-26-000038 cover page (dei:Security12bTitle)")
    [common] = [r for r in rows if r["ticker"] == "MCHP"]
    assert common["stage"] == "out_of_band", "the common leaves on its size, never its title"


def test_mchp_is_kept_where_its_size_belongs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """NEGATIVE through the builder: in the theme band ($10B-$10T) Microchip's common is admitted;
    the cover rule takes only the preferred."""
    _, admitted, _ = _run_microchip(monkeypatch, tmp_path, "theme")
    assert admitted == {"MCHP"}
