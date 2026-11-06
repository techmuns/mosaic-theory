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


# ------------------------- the paid path sends production's request, key order included (PR 2)

def test_the_captured_request_keeps_productions_key_order() -> None:
    """The paid draws of PR 2's steps 1–2 sent the tool schema with its keys SORTED (bear_points
    before bull_points, evidence_balance before key_unknowns), because the capture normalised
    with sort_keys and `run_request` sends the capture. Dict equality ignores order, so the guard
    passed. The request sent must serialise byte for byte as production's."""
    import json

    from vinci.dossier.synthesis import tool_for
    nflx = json.loads((ROOT / "data/dossiers/NFLX/dossier.json").read_text())
    req = rp.capture(nflx, None)
    assert json.dumps(req.kwargs["tools"]) == json.dumps([tool_for(nflx["sleeve"])])


def test_run_request_sends_the_tool_in_productions_order(tmp_path: Path) -> None:
    import json
    from types import SimpleNamespace
    from typing import Any

    from vinci.dossier.synthesis import tool_for
    nflx = json.loads((ROOT / "data/dossiers/NFLX/dossier.json").read_text())
    sent: list[dict[str, Any]] = []

    class Sdk:
        messages: Any = None

        def __init__(self) -> None:
            self.messages = self

        def create(self, **kw: Any) -> Any:
            sent.append(kw)
            usage = SimpleNamespace(input_tokens=10, output_tokens=10,
                                    cache_creation_input_tokens=0, cache_read_input_tokens=0)
            block = SimpleNamespace(type="tool_use", input={"evidence_balance": "mixed — x"})
            return SimpleNamespace(usage=usage, content=[block], model="claude-opus-4-8",
                                   stop_reason="tool_use")
    ledger = tmp_path / "l.jsonl"
    rp.Budget.open(ledger, cap_usd=5.0, approval="operator: test")
    rp.run_request(rp.capture(nflx, None, draws=1), draws=1, budget=rp.Budget.load(ledger),
                   label="t", draws_out=tmp_path / "d.jsonl", sdk=Sdk())
    assert json.dumps(sent[0]["tools"]) == json.dumps([tool_for(nflx["sleeve"])])
