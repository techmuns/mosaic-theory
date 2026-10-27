"""FOREIGN PRIVATE ISSUERS LEAVE THE PRIMARY POPULATION (operator ruling 2026-10-27, STATE row 33).

Until STATE row 4's FPI readiness lands, the dossier altitude cannot underwrite a foreign private
issuer (IFRS, 6-K events, Section-16 gaps, foreign-currency workbooks), and on 2026-10-16 they were
255 of the 2,065 names the screen judged. A line is one when the feed types it a depositary
receipt or foreign ordinary (ADRC / GDR / OS), OR its issuer's latest periodic report filed by the
reference date is a 20-F or 40-F — never by country of incorporation alone. One switch,
`UniverseConfig.exclude_foreign_private_issuers`, re-admits them all.

Every line below is REAL: its Polygon record, its 2026-10-16 close, 90-day ADV and share count, and
its EDGAR filing index, frozen in `tests/fixtures/foreign_private_issuers.json`.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci import universe as uni
from vinci.config import Config, UniverseConfig
from vinci.eod import RawBar
from vinci.resolver.instrument import latest_report
from vinci.schemas.data_record import Identity
from vinci.universe import DROP_STAGES, build_universe

_FIX: dict[str, Any] = json.loads(
    (Path(__file__).parent / "fixtures" / "foreign_private_issuers.json").read_text())["lines"]
_REF = date(2026, 10, 16)


def _subs(t: str) -> dict[str, Any]:
    return {"filings": {"recent": _FIX[t]["recent_filings"]}}


def _ident(t: str) -> Identity:
    cik = _FIX[t]["cik"]
    return Identity(internal_id=f"SEC-{cik}-{t}", issuer_id=f"ISS-{cik}", cik=cik, ticker=t,
                    mic="XNAS", exchange="Nasdaq", eod_symbol=t,
                    name=_FIX[t]["polygon_reference"]["name"])


def _run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, tickers: list[str], *,
         exclude: bool | None = None, band_name: str = "primary", unread: bool = False,
         ) -> tuple[dict, set[str], dict[str, dict]]:
    """The REAL builder over real lines, one issuer each; returns (stats, admitted, drops)."""
    idents = [_ident(t) for t in tickers]

    class _R:
        @classmethod
        def from_config(cls, cfg: object) -> _R: return cls()
        def iter_universe(self, exchanges: object) -> Iterator[Identity]: yield from idents
        def sic_for(self, cik: str) -> tuple[str, str]: return ("4412", "Deep Sea Transport")
        def registered_line(self, *_: object) -> None: return None     # no cover read
        def latest_report(self, cik: str, as_of: date) -> tuple[str, date, str] | None:
            t = next(t for t in tickers if _FIX[t]["cik"] == cik)
            assert "recent_filings" in _FIX[t], f"{t} is decided by its type, never its filings"
            if unread:
                from vinci.netcache import HttpError
                raise HttpError("503 from the SEC on an older submissions page")
            return latest_report(_subs(t), as_of)

    class _E:
        @classmethod
        def from_config(cls, cfg: object) -> _E: return cls()
        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            if day != _REF:
                return {}
            return {t: RawBar(ticker=t, open=_FIX[t]["close"], high=_FIX[t]["close"],
                              low=_FIX[t]["close"], close=_FIX[t]["close"],
                              volume=_FIX[t]["adv_90d"] / _FIX[t]["close"]) for t in tickers}
        def security_types(self) -> dict[str, str]:
            return {t: _FIX[t]["polygon_reference"]["type"] for t in tickers}
        def share_class_counts(self, asked: object) -> dict[str, float]:
            # an ADR is sized by its ADS count, which is what its committed row was sized by
            return {t: _FIX[t]["share_count"] for t in asked  # type: ignore[attr-defined]
                    if _FIX[t]["polygon_reference"]["type"] == "ADRC"}

    class _Ed:
        @classmethod
        def from_config(cls, cfg: object) -> _Ed: return cls()
        def shares_outstanding_with_provenance(
            self, periods: object, *, include_period_average: bool = False
        ) -> tuple[dict[str, float], dict[str, str]]:
            filed = {_FIX[t]["cik"]: _FIX[t]["share_count"] for t in tickers
                     if _FIX[t]["polygon_reference"]["type"] == "CS"}
            return filed, dict.fromkeys(filed, "dei:EntityCommonStockSharesOutstanding")

    monkeypatch.setattr(uni, "EntityResolver", _R)
    monkeypatch.setattr(uni, "PolygonEodClient", _E)
    monkeypatch.setattr(uni, "EdgarClient", _Ed)
    cfg = Config(data_dir=tmp_path) if exclude is None else Config(
        data_dir=tmp_path, universe=UniverseConfig(exclude_foreign_private_issuers=exclude))
    stats = build_universe(cfg, reference_date=_REF, share_periods=["CY2026Q2I"],
                           band_name=band_name, retain_run_id="2026-10-16-01",
                           retain_dir=tmp_path / "retain")
    table = "universe_snapshot" if band_name == "primary" else "theme_universe_snapshot"
    admitted = {json.loads(x)["internal_id"].split("-", 2)[2] for x in
                (tmp_path / "snapshots" / f"{table}.jsonl").read_text().splitlines() if x.strip()}
    from vinci.screens.retention import run_path
    drops = {r["ticker"]: r for r in (json.loads(x) for x in run_path(
        "2026-10-16-01", tmp_path / "retain").read_text().splitlines() if x.strip())}
    return stats, admitted, drops


def test_an_adr_line_leaves_on_the_feeds_own_type(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """POSITIVE — HIMX, Himax Technologies' ADS: typed ADRC by the feed, $2.03B on its ADS count on
    2026-10-16. It leaves at the named stage, and no SEC call is spent deciding it."""
    assert _FIX["HIMX"]["polygon_reference"]["type"] == "ADRC"
    stats, admitted, drops = _run(monkeypatch, tmp_path, ["HIMX"])
    assert "foreign_private_issuer" in DROP_STAGES
    assert admitted == set() and stats["foreign_private_issuer"] == 1
    assert drops["HIMX"]["stage"] == "foreign_private_issuer"
    assert drops["HIMX"]["deciding_input"]["value"] == "ADRC"


def test_a_common_stock_typed_20f_filer_leaves_on_its_filing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """POSITIVE — ZIM, typed CS by the feed: its latest periodic report by 2026-10-16 is the 20-F
    filed 2026-03-09 (75 rows down an index of 6-Ks). The type alone would have kept it."""
    assert _FIX["ZIM"]["polygon_reference"]["type"] == "CS"
    _, admitted, drops = _run(monkeypatch, tmp_path, ["ZIM"])
    assert admitted == set()
    row = drops["ZIM"]
    assert row["stage"] == "foreign_private_issuer"
    assert row["deciding_input"] == {
        "value": "20-F", "as_of": "2026-03-09",
        "source": "SEC 20-F 0001178913-26-000784 (latest periodic report)",
        "note": None, "span_days": None, "observations": None}


def test_a_foreign_domiciled_10q_filer_stays(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """NEGATIVE — RIG, Transocean: incorporated in Switzerland (EDGAR stateOfIncorporation V8) but
    filing 10-K / 10-Q. Domicile is not the test; how the issuer files is."""
    assert _FIX["RIG"]["state_of_incorporation"] == "V8"
    assert latest_report(_subs("RIG"), _REF) == ("10-Q", date(2026, 8, 7), "0001451505-26-000061")
    stats, admitted, _ = _run(monkeypatch, tmp_path, ["RIG"])
    assert admitted == {"RIG"} and stats.get("foreign_private_issuer", 0) == 0


def test_one_switch_readmits_every_foreign_private_issuer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """RE-ADMITTING IS ONE SWITCH, and it restores exactly the population before the ruling."""
    stats, admitted, _ = _run(monkeypatch, tmp_path, ["HIMX", "ZIM", "RIG"], exclude=False)
    assert admitted == {"HIMX", "ZIM", "RIG"} and stats.get("foreign_private_issuer", 0) == 0


def test_the_default_excludes_and_the_theme_band_keeps_them(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The ruling is about the population the spread accumulates against: the primary band
    excludes by default, and the theme altitude keeps its foreign megacaps."""
    assert Config().universe.exclude_foreign_private_issuers is True
    assert Config().theme_universe.exclude_foreign_private_issuers is False
    _, admitted, _ = _run(monkeypatch, tmp_path, ["HIMX", "ZIM", "RIG"])
    assert admitted == {"RIG"}


def test_an_amendment_never_decides_how_an_issuer_files() -> None:
    """A 20-F/A restates an earlier year. Laid on top of RIG's real index (its accession and date
    are invented; the form is the case), it must not turn a 10-Q filer into a foreign issuer."""
    recent = {k: list(v) for k, v in _FIX["RIG"]["recent_filings"].items()}
    for k, v in zip(("form", "filingDate", "accessionNumber", "primaryDocument"),
                    ("20-F/A", "2026-10-01", "0001451505-26-999999", "rig-20fa.htm"), strict=True):
        recent[k].insert(0, v)
    assert latest_report({"filings": {"recent": recent}}, _REF)[0] == "10-Q"  # type: ignore[index]
    # and a report filed after the reference date is not yet the issuer's word
    assert latest_report(_subs("ZIM"), date(2026, 3, 8)) != latest_report(_subs("ZIM"), _REF)


def test_every_admitted_type_but_common_stock_is_a_foreign_line() -> None:
    """No OS or GDR line sat in the 2026-10-16 population, so no real record pins those two. What
    does: the ruling names every type the allowlist admits besides CS, and a type added to the
    allowlist later must be classed one way or the other, deliberately."""
    from vinci.universe import FOREIGN_LINE_TYPES
    assert set(FOREIGN_LINE_TYPES) == set(Config().universe.allowed_security_types) - {"CS"}


class _PagedIndex:
    """ZIM's REAL filing index, split where its 20-F falls: every row before it as the RECENT
    block, the 20-F and the rows after it as one older page (the split is the construction — a
    heavy 6-K filer's recent block runs out before its annual report; every row is ZIM's)."""

    def __init__(self, *, page_from: str = "2025-01-01", page_fails: bool = False) -> None:
        rows = _FIX["ZIM"]["recent_filings"]
        i = rows["form"].index("20-F")
        self.recent = {k: v[:i] for k, v in rows.items()}
        self.page = {k: v[i:] for k, v in rows.items()}
        self.page_from, self.page_fails = page_from, page_fails
        self.asked: list[str] = []

    def get_json(self, url: str, *, ttl_seconds: float | None = None,
                 params: object = None) -> Any:
        self.asked.append(url.rsplit("/", 1)[-1])
        if url.endswith(f"CIK{_FIX['ZIM']['cik']}.json"):
            return {"filings": {"recent": self.recent, "files": [
                {"name": "CIK0001654126-submissions-001.json", "filingFrom": self.page_from,
                 "filingTo": "2026-03-31"}]}}
        if self.page_fails:
            from vinci.netcache import HttpError
            raise HttpError("503 from the SEC")
        return self.page


def test_a_20f_older_than_the_recent_block_is_found_on_the_older_pages() -> None:
    """CODEX, #828 round 1. Reading only the RECENT block took "no periodic report there" for "not
    a foreign private issuer" and admitted the line — absence read off incomplete data. The older
    pages are walked until a periodic report is found."""
    from vinci.resolver import EntityResolver
    http = _PagedIndex()
    assert latest_report({"filings": {"recent": http.recent}}, _REF) is None   # the old reading
    got = EntityResolver(http=http).latest_report(_FIX["ZIM"]["cik"], _REF)  # type: ignore[arg-type]
    assert got == ("20-F", date(2026, 3, 9), "0001178913-26-000784")
    assert http.asked[-1] == "CIK0001654126-submissions-001.json"


def test_an_older_page_that_cannot_be_read_fails_loud() -> None:
    """A page the SEC will not serve is not "no report": the reader raises rather than answer
    None, which the builder would read as a domestic filer."""
    from vinci.netcache import HttpError
    from vinci.resolver import EntityResolver
    with pytest.raises(HttpError):
        EntityResolver(http=_PagedIndex(page_fails=True)).latest_report(  # type: ignore[arg-type]
            _FIX["ZIM"]["cik"], _REF)


def test_a_page_that_starts_after_the_reference_date_is_never_read() -> None:
    """POINT IN TIME, and no wasted call: a page of filings made after the build's date cannot hold
    the report the build may read."""
    from vinci.resolver import EntityResolver
    http = _PagedIndex(page_from="2026-11-01")
    assert EntityResolver(http=http).latest_report(  # type: ignore[arg-type]
        _FIX["ZIM"]["cik"], _REF) is None
    assert http.asked == ["CIK0001654126.json"]


def test_an_issuer_whose_index_cannot_be_read_is_held_out_under_its_own_reason(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """#828, round 1 (the lane owner's ruling): an unread filing index is held out at
    `fpi_status_unread`, counted — never admitted as a domestic filer, and never the build's end.
    RIG, a real 10-Q filer, shows it: unread, it does not get in on the absence of an answer."""
    assert "fpi_status_unread" in DROP_STAGES
    stats, admitted, drops = _run(monkeypatch, tmp_path, ["RIG"], unread=True)
    assert admitted == set() and stats["fpi_status_unread"] == 1
    assert drops["RIG"]["stage"] == "fpi_status_unread"
