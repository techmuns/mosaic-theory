"""Suite-wide fixtures, and the deselected count a run on workers reports."""

from __future__ import annotations

import sys
from collections.abc import Generator, Sequence
from pathlib import Path
from typing import Any

import pytest

from vinci import netcache

#: The node ids `pytest_deselected` handed this process, in the order it handed them.
_DESELECTED = pytest.StashKey[list[str]]()
#: On the controller of a run on workers: each worker's deselected ids, or None if it sent none.
_WORKER_DESELECTED = pytest.StashKey[dict[str, list[str] | None]]()


def pytest_deselected(items: Sequence[pytest.Item]) -> None:
    """Keep the ids of the tests deselected (`-m "not network"` on the gate), for the worker to
    send back. On one process the terminal reporter counts them itself; on workers (pytest-xdist)
    the controller collects nothing, so its summary line dropped "39 deselected" (2026-11-13)."""
    if items:
        items[0].config.stash.setdefault(_DESELECTED, []).extend(i.nodeid for i in items)


def pytest_collection_finish(session: pytest.Session) -> None:
    """A worker sends its deselected ids once its collection, and so its deselection, is done:
    a worker that never got here sends none, which the controller reports as unknown, never 0."""
    output: dict[str, Any] | None = getattr(session.config, "workeroutput", None)
    if output is not None:
        output["deselected"] = list(session.config.stash.get(_DESELECTED, []))


@pytest.hookimpl(optionalhook=True)  # a pytest-xdist hook; without xdist it is never called
def pytest_testnodedown(node: Any, error: object | None) -> None:
    """The controller keeps what each worker sent when it finished (`workeroutput`)."""
    sent = getattr(node, "workeroutput", {}).get("deselected")
    node.config.stash.setdefault(_WORKER_DESELECTED, {})[node.gateway.id] = sent


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> Generator[None]:
    """On the controller of a run on workers, print the deselected count on the line above the
    summary line — after the `-rs` skip reasons, where one process prints "39 deselected" in the
    summary line itself. Printed beside it, not put into it: pytest's `stats` hold reports, and
    a plugin reading them (hypothesis's) fails on anything else.

    Every worker collects the whole suite and deselects by the same marks, so all send the same
    ids. A worker that sent none, or workers that disagree, is stated as such: an unknown count is
    never printed as a number."""
    try:
        return (yield)
    finally:
        sent = terminalreporter.config.stash.get(_WORKER_DESELECTED, None)
        lists = {tuple(ids) for ids in (sent or {}).values() if ids is not None}
        if sent and (None in sent.values() or len(lists) != 1):
            counts = ", ".join(f"{w} {'sent none' if ids is None else len(ids)}"
                               for w, ids in sorted(sent.items()))
            terminalreporter.write_line(f"deselected: UNKNOWN ({counts})", red=True)
        elif sent and (ids := next(iter(lists))):
            option = terminalreporter.config.option
            selection = (("-m", option.markexpr), ("-k", option.keyword))
            given = ", ".join(f'{flag} "{expr}"' for flag, expr in selection if expr)
            terminalreporter.write_line(
                f"{len(ids)} deselected" + (f" ({given})" if given else "")
                + f", the same {len(ids)} on each of the {len(sent)} workers")


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
def _no_evidence_spool(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test writes into the operator's evidence spool (RG-D19 PR 2). `assemble._write` spools
    a page's transcript evidence when ``$VINCI_EVIDENCE_SPOOL`` is set, and that folder is on the
    operator's shared Drive: a shell that has it set must never send a test's fixture rows there.
    A test that spools names its own temporary folder."""
    monkeypatch.delenv("VINCI_EVIDENCE_SPOOL", raising=False)


@pytest.fixture
def evidence_spool(tmp_path_factory: pytest.TempPathFactory,
                   monkeypatch: pytest.MonkeyPatch) -> Path:
    """A spool of the test's own, for a test that writes a page with transcript text (RG-D19 PR 3:
    `assemble._write` files those words before it writes the page, and refuses without a spool).
    Created here, by the test, as the operator creates the real one; never the operator's."""
    root = tmp_path_factory.mktemp("evidence-spool")
    monkeypatch.setenv("VINCI_EVIDENCE_SPOOL", str(root))
    return root


@pytest.fixture(autouse=True)
def _fresh_cover_cache() -> None:
    """The parsed-cover cache (`mechanical._COVER_TEXTS`) is module-global and keyed on the URL,
    so one test's served cover would answer the next test's refusing fetcher, in any file."""
    mech = sys.modules.get("vinci.dossier.mechanical")
    if mech is not None:
        mech._COVER_TEXTS.clear()  # noqa: SLF001
