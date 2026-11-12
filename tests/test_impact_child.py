"""The impact check's child process (`vinci.impact.child`): what keeps two builds of one page on
one input identical."""
from __future__ import annotations

import pathlib
import subprocess
from typing import Any

import pytest

from vinci.impact import child


def test_every_libreoffice_conversion_runs_under_the_processs_own_profile(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Found on the first corpus run (#955, MCK): two builds converting transcripts at once under
    LibreOffice's shared profile, one lost a call ("transcripts on file but unparseable"), and the
    page, its request and the row-53 verdict all moved with no code change. `ciq.extract_text`
    calls `subprocess.run` with ``soffice``; each child gives it a profile of its own."""
    seen: list[Any] = []
    monkeypatch.setattr(subprocess, "run", lambda args, *a, **k: seen.append(args))
    child.own_soffice_profile(tmp_path / "lo")
    subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "--convert-to", "txt", "x.doc"])
    subprocess.run(["pdftotext", "-layout", "x.pdf", "-"])
    flag = f"-env:UserInstallation={(tmp_path / 'lo').resolve().as_uri()}"
    assert seen == [["/opt/homebrew/bin/soffice", flag, "--headless", "--convert-to", "txt",
                     "x.doc"], ["pdftotext", "-layout", "x.pdf", "-"]]


def test_a_vendor_response_the_cache_lacks_is_refused_not_fetched(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Coordinator, 2026-11-11: "No Polygon or Tiingo bulk pulls without asking me." A sweep of
    old refs reads responses today's cache may lack (`run-monthly` re-ingests the universe's
    grouped-daily bars); each is refused, loud, while an SEC miss is still fetched (paced)."""
    from vinci import netcache

    fetched: list[str] = []
    monkeypatch.setattr(netcache.CachedHttp, "_fetch_with_retries",
                        lambda self, url, **kw: fetched.append(url) or "body")
    monkeypatch.setattr(netcache.CachedHttp, "_read_cache", lambda self, url, ttl: None)
    monkeypatch.setenv(child.NO_VENDOR_PULLS, "1")
    child.freeze_cache()

    class _Http:
        def _cache_path(self, url: str) -> pathlib.Path:
            return pathlib.Path("polygon") / "x.json"

    http = _Http()
    with pytest.raises(RuntimeError, match="pull is the operator's call"):
        netcache.CachedHttp._fetch_with_retries(  # type: ignore[arg-type]
            http, "https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/2026-11-09")
    with pytest.raises(RuntimeError, match="api.tiingo.com"):
        netcache.CachedHttp._fetch_with_retries(  # type: ignore[arg-type]
            http, "https://api.tiingo.com/tiingo/daily/MCK/prices")
    assert netcache.CachedHttp._fetch_with_retries(  # type: ignore[arg-type]
        http, "https://data.sec.gov/api/xbrl/companyfacts/CIK0000927653.json") == "body"
    assert fetched == ["https://data.sec.gov/api/xbrl/companyfacts/CIK0000927653.json"]
