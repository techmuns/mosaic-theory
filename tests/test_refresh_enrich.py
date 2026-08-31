"""`vinci refresh` enriches the SIC it stores — and a flaky SEC never stops a price backfill.

`refresh` is how a name OUTSIDE the cap band enters the entity master, and `build_universe` never
comes back to enrich one it does not admit — so whatever `refresh` stores is what that name keeps.
It stored no SIC, which is why NFLX has none and why Gartner's class was exposed at all (#523).

These pin the whole point: the SIC must reach the STORE (not merely be fetched), an SEC failure
must degrade to UNKNOWN rather than abort the bars, and an unknown TICKER must still fail loud —
the identity is not the adornment.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pytest

from vinci import cli
from vinci.resolver import UnknownSymbolError
from vinci.schemas.data_record import Identity

_UNSET = object()


def _ident(ticker: str, cik: str) -> Identity:
    return Identity(
        internal_id=f"SEC-{cik}-{ticker}", issuer_id=f"ISS-{cik}", cik=cik, ticker=ticker,
        mic="XNAS", exchange="Nasdaq", eod_symbol=ticker, name=f"{ticker} Inc", currency="USD")


class _Resolver:
    """A resolver whose SIC lookup can be made to fail, publish nothing, or answer."""

    def __init__(self, sic: Any = "7372", *, raises: Exception | None = None,
                 unknown: frozenset[str] = frozenset(), desc: Any = _UNSET) -> None:
        self._sic, self._raises, self._unknown = sic, raises, unknown
        # EDGAR's real shape for a SIC-less issuer is `sicDescription: ""` (observed on FSK), so
        # the default mirrors the live payload rather than a tidied-up None.
        self._desc = ("Services-Prepackaged Software" if sic else "") if desc is _UNSET else desc
        self.sic_calls: list[str] = []

    def resolve_ticker(self, ticker: str, *, enrich: bool = False) -> Identity:
        if ticker in self._unknown:
            raise UnknownSymbolError(f"no US issuer for ticker {ticker!r}")
        return _ident(ticker, "0001065280")

    def sic_for(self, cik: str) -> tuple[str | None, str | None]:
        self.sic_calls.append(cik)
        if self._raises is not None:
            raise self._raises
        return (self._sic, self._desc)


class _Config:
    """Config whose every path is inside tmp_path, so `ensure_dirs` cannot escape it."""

    def __init__(self, root: Path) -> None:
        self.data_dir = root / "data"
        self.cache_dir = self.data_dir / "cache"
        self.snapshots_dir = self.data_dir / "snapshots"
        self.db_path = self.data_dir / "test.db"

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.cache_dir, self.snapshots_dir):
            d.mkdir(parents=True, exist_ok=True)


class _Store:
    def __init__(self) -> None:
        self.upserted: list[Identity] = []

    def __enter__(self) -> _Store:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def upsert_security(self, ident: Identity, **kw: Any) -> None:
        self.upserted.append(ident)


def _run(monkeypatch: pytest.MonkeyPatch, resolver: _Resolver, tickers: list[str],
         tmp_path: Path) -> tuple[int, _Store, list[Identity]]:
    """Drive the REAL `_cmd_refresh` with the network ends stubbed.

    Pinned through the COMMAND, not through `_resolve_for_refresh` alone: a helper-level test stays
    green if the call site stops calling it, and the thing that matters is the identity that
    reaches `upsert_security` and the bar-ingest.
    """
    store = _Store()
    ingested: list[Identity] = []
    # `get_config` IS STUBBED, and that is not incidental: `_cmd_refresh` calls `cfg.ensure_dirs()`,
    # which mkdirs data/, data/cache/ and data/snapshots/ RELATIVE TO THE CWD. Unstubbed, running
    # this file from anywhere but the repo root litters that directory — invisible from the root,
    # where those dirs already exist. Found by running the suite from an empty cwd (review of #528).
    monkeypatch.setattr(cli, "get_config", lambda: _Config(tmp_path))
    monkeypatch.setattr(cli, "EntityResolver", type("R", (), {
        "from_config": staticmethod(lambda *a, **k: resolver)}))
    monkeypatch.setattr(cli, "PolygonEodClient", type("C", (), {
        "from_config": staticmethod(lambda *a, **k: object())}))
    monkeypatch.setattr(cli, "Store", lambda *a, **k: store)
    monkeypatch.setattr(cli, "ingest_prices",
                        lambda c, s, secs, **k: ingested.extend(secs) or "ok")
    monkeypatch.setattr(cli, "ingest_prices_per_symbol",
                        lambda c, s, secs, **k: ingested.extend(secs) or "ok")
    args = argparse.Namespace(tickers=tickers, start="2026-01-01", end="2026-02-01", aggs=False)
    return cli._cmd_refresh(args), store, ingested


def test_refresh_stores_the_sic_it_fetched(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """THE POINT OF THE CHANGE: the SIC must reach the STORE. Fetching it and dropping it on the
    floor is exactly the dead write #83 fixed in `build_universe`."""
    r = _Resolver(sic="7372")
    code, store, _ = _run(monkeypatch, r, tmp_path=tmp_path, tickers=["NFLX"])
    assert code == 0
    assert r.sic_calls == ["0001065280"], "the SIC was never fetched"
    assert [i.sic for i in store.upserted] == ["7372"]
    assert store.upserted[0].sic_description == "Services-Prepackaged Software"


def test_a_failing_sic_lookup_degrades_to_unknown_and_still_ingests_bars(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
        tmp_path: Path) -> None:
    """THE NEGATIVE PIN, and the reason this is not just `enrich=True`.

    Every ticker is resolved BEFORE any bars are fetched, so an un-caught SEC error would abort the
    whole backfill before it started. A price job must not refuse to run because data.sec.gov was
    flaky — the SIC is an adornment, the bars are the job. Safe because `upsert_security` COALESCEs
    (#523): an UNKNOWN can no longer erase a stored SIC.
    """
    r = _Resolver(raises=RuntimeError("HTTP 503 from data.sec.gov"))
    code, store, ingested = _run(monkeypatch, r, tmp_path=tmp_path, tickers=["NFLX"])
    assert code == 0, "a flaky SEC must not fail a price backfill"
    assert [i.ticker for i in ingested] == ["NFLX"], "the bars were never fetched"
    assert store.upserted and store.upserted[0].sic is None
    out = capsys.readouterr().out
    assert "SIC lookup FAILED" in out and "503" in out, "the degradation must be said out loud"


def test_an_unknown_ticker_still_fails_loud(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
        tmp_path: Path) -> None:
    """The IDENTITY is not the adornment. A ticker that resolves to no issuer is skipped and
    reported — never carried forward on a guess — while its siblings still refresh."""
    r = _Resolver(unknown=frozenset({"ZZZZ"}))
    code, store, ingested = _run(monkeypatch, r, tmp_path=tmp_path, tickers=["NFLX", "ZZZZ"])
    assert code == 0
    assert [i.ticker for i in store.upserted] == ["NFLX"] == [i.ticker for i in ingested]
    assert "skip ZZZZ" in capsys.readouterr().out


def test_an_issuer_edgar_publishes_no_sic_for_is_reported_not_inferred(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
        tmp_path: Path) -> None:
    """ABSENT is distinct from BROKEN — the distinction #523/#525 exist to keep visible. A BDC's
    empty SIC is a fact about EDGAR, not a failed lookup, and must never be back-filled by
    inference from the name or the exchange."""
    r = _Resolver(sic=None)
    code, store, _ = _run(monkeypatch, r, tmp_path=tmp_path, tickers=["FSK"])
    assert code == 0 and store.upserted[0].sic is None
    out = capsys.readouterr().out
    assert "publishes no SIC" in out and "never inferred" in out
    assert "FAILED" not in out, "an absence must not be reported as a failure"


def test_an_empty_sic_description_is_stored_as_none_not_as_a_blank(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """EDGAR returns `sicDescription: ""` for a SIC-less issuer — observed live on FSK. That must
    reach the store as None, because `upsert_security` COALESCEs `sic_description` and SQL COALESCE
    treats '' as PRESENT: a blank would OVERWRITE a stored description instead of deferring to it,
    re-opening on the sibling column the erasure #523 closed."""
    r = _Resolver(sic=None, desc="")   # EDGAR's literal payload for a SIC-less issuer
    _, store, _ = _run(monkeypatch, r, tmp_path=tmp_path, tickers=["FSK"])
    assert store.upserted[0].sic_description is None, "'' must be normalised to absent"


def test_benchmark_etfs_stay_resolver_exempt(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """SPY/IWM/MDY are synthetic `IDX-*` identities, not SEC issuers. They must never reach the
    resolver or the SIC fetch — a SIC on one would be invented (pinned in
    `tests/test_entity_master_sic.py` on the artifact side)."""
    r = _Resolver()
    code, store, _ = _run(monkeypatch, r, tmp_path=tmp_path, tickers=["IWM"])
    assert code == 0
    assert r.sic_calls == [], "a benchmark ETF must never be sent to EDGAR"
    assert store.upserted[0].internal_id == "IDX-IWM" and store.upserted[0].sic is None


def test_a_run_that_lost_every_sic_says_so_once_at_the_end(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
        tmp_path: Path) -> None:
    """PER-NAME LINES ARE NOT A SIGNAL (review of #528). On a long refresh during an SEC outage —
    or after a change that breaks `sic_for`, since `except Exception` catches an AttributeError
    just as readily — every name degrades, the individual lines scroll past inside Polygon's
    progress output, and the run still ends `done:` with exit 0. Read as a clean refresh, that
    re-digs wholesale the exact hole this command exists to stop. So the tally is printed ONCE, AT
    THE END, naming the count and the names."""
    r = _Resolver(raises=RuntimeError("HTTP 503 from data.sec.gov"))
    code, _, ingested = _run(monkeypatch, r, tmp_path=tmp_path, tickers=["NFLX", "IT", "IWM"])
    assert code == 0 and len(ingested) == 3, "the bars are still the job"
    out = capsys.readouterr().out
    assert "WARNING: 2/2 SIC lookup(s) FAILED" in out, "a systemic failure must be legible"
    assert "NFLX, IT" in out, "the tally must name the affected names"
    # the benchmark is resolver-exempt, so it is neither attempted nor counted
    assert "IWM" not in out.split("WARNING:")[1]
    assert out.rindex("WARNING:") > out.rindex("done:"), "the tally must come AFTER the run summary"


def test_a_clean_run_prints_no_failure_tally(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
        tmp_path: Path) -> None:
    """The complement: a warning that fires when nothing went wrong trains the operator to ignore
    it. An issuer EDGAR simply publishes no SIC for is not a failure and must not be tallied."""
    _run(monkeypatch, _Resolver(sic=None), tmp_path=tmp_path, tickers=["FSK"])
    assert "WARNING" not in capsys.readouterr().out
