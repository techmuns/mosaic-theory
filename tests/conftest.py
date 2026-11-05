"""Suite-wide fixtures."""

from __future__ import annotations

import sys
from collections.abc import Iterator

import pytest

from tests import held_names
from vinci import netcache

# THE HELD NAMES: no test opens a held audit pack's CIQ export (tests/held_names.py). Installed at
# import, so collection-time code is covered too; an audit hook cannot be removed, and it acts only
# on an open under this checkout's `data/manual`.
held_names.CIQ_ROOTS, held_names.HELD_FOLDERS = held_names.ciq_roots()
sys.addaudithook(held_names.refuse_held_open)


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


@pytest.fixture(autouse=True)
def _held_names_stay_unopened(request: pytest.FixtureRequest) -> Iterator[None]:
    """Names the running test for the held list's records, and FAILS a test that opened a held
    name's export even though it swallowed the hook's own failure (an `except BaseException`, a
    worker thread). The hook refuses the open first, so no byte of the file was read."""
    held_names.CURRENT_TEST[0] = request.node.nodeid
    before = len(held_names.REFUSED_OPENS)
    yield
    held_names.CURRENT_TEST[0] = "<between tests>"
    refused = held_names.REFUSED_OPENS[before:]
    if refused:
        pytest.fail(f"{len(refused)} open(s) of a held name's CIQ export refused: "
                    + "; ".join(p for _, p in refused), pytrace=False)


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    """A loop that left a held name out says so: per loop, the names it dropped."""
    if not held_names.LEFT_OUT:
        return
    by: dict[str, set[str]] = {}
    for where, t in held_names.LEFT_OUT:
        by.setdefault(where, set()).add(t)
    terminalreporter.write_sep("-", f"held names left out of {len(by)} loop(s) "
                                    "(tests/held_names.py)")
    for where in sorted(by):
        terminalreporter.write_line(f"{where}: {', '.join(sorted(by[where]))}")
