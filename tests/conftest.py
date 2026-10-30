"""Suite-wide fixtures."""

from __future__ import annotations

import sys

import pytest

from vinci import netcache


@pytest.fixture(autouse=True)
def _suite_sec_budget(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch,
                      tmp_path_factory: pytest.TempPathFactory) -> None:
    """A budget of the suite's own for every SEC request a test sends.

    Every SEC request takes its turn from ONE machine-wide budget (`vinci.netcache.sec_pace`), a
    file in the user's cache shared with every live `vinci` run on the machine. Offline tests drive
    real clients over mock transports, so a slot one takes from that file is a slot a live run
    waits for, and a mocked refusal would hold off every real SEC request on the machine for
    660 s. A test marked `network` sends real requests, so it keeps the machine's budget. A refusal
    a test provokes stops SEC traffic for the rest of the PROCESS (`netcache._SEC_STOPPED`), so
    it is cleared for the next test."""
    monkeypatch.setattr(netcache, "_SEC_STOPPED", None)
    if request.node.get_closest_marker("network") is None:
        monkeypatch.setenv("VINCI_SEC_PACE_FILE", str(tmp_path_factory.getbasetemp() / "sec-pace"))
    built = netcache._SEC_PACE  # noqa: SLF001 — rebuilt below when the budget it reads changed
    if built is not None and built._path != netcache._sec_pace_path():  # noqa: SLF001
        monkeypatch.setattr(netcache, "_SEC_PACE", None)


@pytest.fixture(autouse=True)
def _fresh_cover_cache() -> None:
    """The parsed-cover cache (`mechanical._COVER_TEXTS`) is module-global and keyed on the URL,
    so one test's served cover would answer the next test's refusing fetcher, in any file."""
    mech = sys.modules.get("vinci.dossier.mechanical")
    if mech is not None:
        mech._COVER_TEXTS.clear()  # noqa: SLF001
