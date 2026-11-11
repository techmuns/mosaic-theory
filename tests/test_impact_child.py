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
