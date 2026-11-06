"""PR 2 of the synthesis eval harness: a target page outside the panel can be registered (record
§6.1 — #921's material-direction form is measured on NFLX, where it fires), and an unknown page is
refused."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from vinci.evals import compare as cm
from vinci.evals import replay as rp

ROOT = Path(__file__).resolve().parents[1]


def _history() -> None:
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", "dc5b8787^{commit}"],
                      capture_output=True).returncode != 0:
        pytest.skip("needs the full history")


def test_a_target_page_outside_the_panel_can_be_registered() -> None:
    _history()
    reg = cm.register("dc5b8787", "b109e26c", targets=["M-SIGN"], pages=["NFLX"])
    assert reg.pages == ("NFLX",) and reg.targets == ("M-SIGN",)
    assert reg.held_out == ()        # #921's own commit and record name NFLX: not held out
    panel = cm.register("dc5b8787", "b109e26c", targets=["M-SIGN"])
    assert panel.pages == tuple(rp.load_panel_file()["panel"])


def test_an_unknown_page_cannot_be_registered() -> None:
    with pytest.raises(rp.ReplayError, match="no frozen inputs"):
        cm.register("dc5b8787", "b109e26c", targets=["M-SIGN"], pages=["ZZZZ"])
