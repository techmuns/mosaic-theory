"""The committed pages AS THEY WERE before the RG-D19 page pass took their transcript words off
them (`vinci.dossier.driver_pass`), read from git at `PRE_STRIP_REF`, a commit on main.

A test that replays a page, or checks a property of a row's own quote, needs the words the build
had. Those are no longer on the live pages, which this public repo serves, but they are still in
its history at this commit. That history is the published past, so reading it here publishes
nothing new.

CI checks out full history (`gate.yml`: `fetch-depth: 0`). Where the commit cannot be read (a
shallow clone, or no git), the test skips and says why.
"""

from __future__ import annotations

import functools
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
#: main as it stood just before the page pass's commit
PRE_STRIP_REF = "586fdcfdcbf724a7c020a02fd165496bce4c665e"


@functools.cache
def _ref() -> str:
    try:
        got = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet",
                              f"{PRE_STRIP_REF}^{{commit}}"], capture_output=True, text=True)
    except OSError as exc:
        pytest.skip(f"git is not available to read the pre-strip pages: {exc}")
    if got.returncode != 0:
        pytest.skip(f"the pre-strip commit {PRE_STRIP_REF[:12]} is not in this clone (shallow?)")
    return got.stdout.strip()


@functools.cache
def pre_strip_text(ticker: str) -> str:
    """``data/dossiers/<ticker>/dossier.json`` at `PRE_STRIP_REF`, as text."""
    out = subprocess.run(["git", "-C", str(ROOT), "show", f"{_ref()}:data/dossiers/{ticker}/"
                          "dossier.json"], capture_output=True, text=True)
    if out.returncode != 0:
        raise FileNotFoundError(f"{ticker}: no committed page at {PRE_STRIP_REF[:12]}")
    return out.stdout


def pre_strip_page(ticker: str) -> dict[str, Any]:
    page: dict[str, Any] = json.loads(pre_strip_text(ticker))
    return page


def pre_strip_tickers() -> list[str]:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "--name-only",
                          f"{_ref()}:data/dossiers"], capture_output=True, text=True, check=True)
    return sorted(t for t in out.stdout.split() if t)


def pre_strip_pages() -> list[tuple[str, dict[str, Any]]]:
    return [(t, pre_strip_page(t)) for t in pre_strip_tickers()]
