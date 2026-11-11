"""STATE §5.0 row 42 (1): one name whose filings window cannot be read drops ITS row, not the day.

Since #878 a filings window that reaches past a heavy filer's recent submissions page reads the
older pages it overlaps, and a page it cannot read raises `HttpError` naming it. Every windowed
caller turned that into its UNKNOWN except `vinci monitor` (`cli._cmd_monitor`, a 760-day window
with no handler): one such name aborted the WHOLE monitor day — no book, no spread, no other
name's row — after every price had been fetched. The same was true of a submissions document that
could not be read at all (a 404, or a 200 interstitial, whose body is not JSON: `ValueError`).

Now the name's freshness row is not written and the day says so by name, as one unreadable record
date already does (`UnreadableEvidenceDateError`); every other name's row is written as before.
An SEC REFUSAL still stops the day: `SecRateLimitedError` is not an `HttpError` on purpose, so a
run never keeps sending into a fair-access block.

REAL DATA through the real command (TEST-LAYER RULE — the failure was a day never written): the
committed ledger, securities and assignments (`tests/test_monitor_ref_date_bound.py`'s harness),
and for IT a REAL `EdgarClient` behind a real `CachedHttp`, served Gartner's committed submissions
document and its older page -001 (`tests/fixtures/submissions_pages/`, #878's fixtures) by a mock
transport. That committed document's recent page begins 2021-12-02, so a 760-day window reaches
page -001 only from a day before 2024-01-01: the older-page case is a re-cut of 2023-09-01, the
real command's one path to it on committed data. Other names keep the harness's frozen filings.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.test_monitor_ref_date_bound import IT_REC, WERN_REC, _rows, _wire, _written
from vinci.edgar.client import EdgarClient
from vinci.netcache import CachedHttp, SecRateLimitedError

ROOT = Path(__file__).resolve().parents[1]
_FIX = ROOT / "tests" / "fixtures" / "submissions_pages"
DOC = (_FIX / "IT.json").read_text()
PAGE1 = (_FIX / "IT-submissions-001.json").read_text()
IT_CIK = "0000749251"
INTERSTITIAL = "<!DOCTYPE html><html><body>Please wait while we verify your request…</body></html>"

#: A re-cut whose 760-day window (from 2021-08-02) reaches page -001 (2021-03-02 → 2021-11-30).
OLD_REF = "2023-09-01"
#: Frozen watch records whose evidence predates OLD_REF, so each gets a row on that day — the
#: harness's IT / WERN shapes, underwritten 2021-07-01.
IT_2021: dict[str, Any] = {
    "ticker": "IT", "underwrite_date": "2021-07-01",
    "verdict": {"status": "watch", "reunderwrite_triggers": ["contract value turns negative"]}}
WERN_2021: dict[str, Any] = {
    "ticker": "WERN", "underwrite_date": "2021-07-01",
    "verdict": {"status": "watch", "reunderwrite_triggers": ["spot pulls to ~28-30"]}}


class _Sec:
    """The SEC as a transport for IT: its document as ``doc`` says, its page -001 as ``page``
    says (``ok`` = the committed page). Counts what reached the wire."""

    def __init__(self, *, doc: str = "ok", page: str = "ok") -> None:
        self.doc, self.page = doc, page
        self.page_requests = 0

    def _answer(self, how: str, body: str) -> httpx.Response:
        if how == "404":
            return httpx.Response(404, text="not served")
        return httpx.Response(200, text=INTERSTITIAL if how == "interstitial" else body)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.endswith(f"CIK{IT_CIK}.json"):
            return self._answer(self.doc, DOC)
        if url.endswith("-submissions-001.json"):
            self.page_requests += 1
            return self._answer(self.page, PAGE1)
        return httpx.Response(404, text="not served")


def _route_it(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sec: _Sec | None = None,
              *, raise_for_it: BaseException | None = None) -> None:
    """After `_wire`: IT's filings come from a real `EdgarClient` over ``sec`` (or raise
    ``raise_for_it``); every other name's from the harness's frozen filings."""
    from vinci import cli
    frozen_cls = cli.EdgarClient
    http = CachedHttp(cache_dir=tmp_path / "sec-cache", user_agent="test test@example.com",
                      min_interval_sec=0.0, namespace="sec")
    http._client = httpx.Client(transport=httpx.MockTransport(sec or _Sec()))  # noqa: SLF001
    real = EdgarClient(http=http)

    class _Routed:
        def __init__(self, frozen: Any) -> None:
            self.frozen = frozen

        @classmethod
        def from_config(cls, cfg: object) -> _Routed:
            return cls(frozen_cls.from_config(cfg))

        def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",),
                           since: date | None = None) -> list[Any]:
            if str(cik) != IT_CIK:
                return list(self.frozen.recent_filings(cik, forms=forms, since=since))
            if raise_for_it is not None:
                raise raise_for_it
            return real.recent_filings(cik, forms=forms, since=since)

    monkeypatch.setattr(cli, "EdgarClient", _Routed)


def _recut(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ref: str,
           records: list[dict[str, Any]], sec: _Sec | None = None) -> dict[str, Any]:
    from vinci import cli
    _wire(tmp_path, monkeypatch, records)
    _route_it(tmp_path, monkeypatch, sec)
    scratch = tmp_path / "scratch"
    assert cli._cmd_monitor(argparse.Namespace(ref=ref, out=str(scratch))) == 0
    return _written(scratch / "data/monitor")


def _unread_notes(snap: dict[str, Any], ticker: str) -> list[str]:
    return [n for n in snap["notes"] if n.startswith(f"FILINGS {ticker}:")]


@pytest.mark.parametrize("how", ["interstitial", "404"])
def test_an_unreadable_older_page_drops_its_row_not_the_day(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, how: str) -> None:
    """THE DEFECT (row 42 (1)). IT's window from 2021-08-02 needs page -001, and SEC answers it
    with an interstitial or a 404. On main `_cmd_monitor` raised the page's `HttpError`: no day.
    ⊕ the day is written; ⊖ IT has no row; ⊕ WERN, read AFTER IT, still has its row; ⊕ the day
    names IT, the window and the page — never a silent drop."""
    sec = _Sec(page=how)
    snap = _recut(tmp_path, monkeypatch, OLD_REF, [IT_2021, WERN_2021], sec)
    assert sec.page_requests >= 1                       # the window really reached the page
    assert set(_rows(snap)) == {"WERN"}
    [note] = _unread_notes(snap, "IT")
    assert "since 2021-08-02" in note and "CIK0000749251-submissions-001.json" in note
    assert note.endswith("its freshness row is NOT written")


def test_negative_a_readable_older_page_is_read_into_the_row(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) The same re-cut with page -001 served: IT's row is written and its newer filings
    include the page's 10-Q of 2021-08-03 and 8-K of 2021-11-02 — the rows only that page holds —
    and the day carries no unread-window note."""
    sec = _Sec()
    snap = _recut(tmp_path, monkeypatch, OLD_REF, [IT_2021, WERN_2021], sec)
    assert sec.page_requests == 1
    rows = _rows(snap)
    assert set(rows) == {"IT", "WERN"}
    assert {"10-Q 2021-08-03 acc 0000749251-21-000030",
            "8-K 2021-11-02 acc 0000749251-21-000036"} <= set(rows["IT"].newer_filings)
    assert not _unread_notes(snap, "IT")


@pytest.mark.parametrize("how", ["interstitial", "404"])
def test_an_unreadable_submissions_document_drops_its_row_not_the_day(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, how: str) -> None:
    """The routine-window case on the committed 2026-09-22 day: IT's submissions document itself
    cannot be read — a 404 (`HttpError`) or a 200 interstitial (`ValueError`, the CLI's other
    submissions read catches it as one). ⊖ IT has no row; ⊕ WERN's row is EXACTLY the committed
    day's (newer filings and evidence date); ⊕ the day names IT."""
    snap = _recut(tmp_path, monkeypatch, "2026-09-22", [IT_REC, WERN_REC], _Sec(doc=how))
    rows = _rows(snap)
    assert set(rows) == {"WERN"}
    committed = _rows(json.loads((ROOT / "data/monitor/2026-09-22.json").read_text()))
    assert rows["WERN"].newer_filings == committed["WERN"].newer_filings
    assert rows["WERN"].last_evidence_date == committed["WERN"].last_evidence_date
    [note] = _unread_notes(snap, "IT")
    assert "since 2024-08-23" in note


def test_negative_an_sec_refusal_still_stops_the_day(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) SEC REFUSING this process is not one name's unreadable window: it stops the run, so
    the monitor never sends on into a fair-access block. Nothing is written."""
    from vinci import cli
    _wire(tmp_path, monkeypatch, [IT_REC, WERN_REC])
    _route_it(tmp_path, monkeypatch,
              raise_for_it=SecRateLimitedError("SEC refused https://data.sec.gov/ with 403"))
    scratch = tmp_path / "scratch"
    with pytest.raises(SecRateLimitedError):
        cli._cmd_monitor(argparse.Namespace(ref="2026-09-22", out=str(scratch)))
    assert not list((scratch / "data/monitor").glob("*.json"))
