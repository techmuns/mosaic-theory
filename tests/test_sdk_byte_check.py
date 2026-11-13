"""THE $0 SDK BYTE CHECK IS ITSELF CHECKED (`scripts/sdk_byte_check/`; operator, 2026-11-13: "Check,
then pin newest (Recommended)").

Every `anthropic` bump goes behind that check, so a check that silently stopped finding differences
would wave the next bump through. These pins hold its three load-bearing parts on the installed SDK
(0.112.0 on the operator's Mac until its venv is re-synced, the lock's 2.6.0 in CI): the comparer
fails on one changed byte and on a request one side lacks; a capture through the real SDK keeps the
bytes it sends and is the same twice; and the impact child still reads only names the inputs module
serves, since `build_inputs.py` swaps that module in.
"""
from __future__ import annotations

import importlib.util
import json
import re
import socket
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "scripts" / "sdk_byte_check"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"_sdk_byte_check_{name}", HERE / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("the byte check opened a socket")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def _capture(out: Path) -> list[dict[str, Any]]:
    """The theme desk's two shapes and validate-keys' ping, as `capture.run` captures each path
    (the page and judge paths need step 2's inputs and the frozen gold pages)."""
    import anthropic

    cap_mod = _load("capture")
    index: list[dict[str, Any]] = []
    for name, fn in (("theme", cap_mod.theme), ("validate-keys", cap_mod.validate_keys)):
        cap = cap_mod.Capture(out, name)
        fn(cap)
        index += cap.index
    (out / "index.json").write_text(json.dumps(index))
    (out / "summary.json").write_text(json.dumps({"anthropic": anthropic.__version__,
                                                  "http_lib": cap_mod.HX.__name__}))
    return index


def test_a_capture_keeps_the_bytes_the_installed_sdk_sends_and_is_the_same_twice(
        tmp_path: Path, offline: None) -> None:
    import anthropic

    index = _capture(tmp_path / "a")
    assert [(r["path"], r["label"]) for r in index] == [
        ("theme", "extract"), ("theme", "completeness-split"), ("validate-keys", "ping")]
    ping = index[2]
    assert json.loads((tmp_path / "a" / ping["body_file"]).read_bytes()) == {
        "max_tokens": 1, "messages": [{"role": "user", "content": "ping"}],
        "model": "claude-opus-4-8"}
    assert ping["url"] == "https://api.anthropic.com/v1/messages"
    assert dict(ping["headers"])["user-agent"] == f"Anthropic/Python {anthropic.__version__}"
    body = json.loads((tmp_path / "a" / index[1]["body_file"]).read_bytes())
    blocks = body["messages"][0]["content"]
    assert [("cache_control" in b) for b in blocks] == [True, False], "the split did not split"
    from vinci.theme_intelligence.config import LLM_MAX_TOKENS
    assert body["max_tokens"] == LLM_MAX_TOKENS, "the theme desk's cap is production's"
    # the same paths again: every body the same, byte for byte
    _capture(tmp_path / "b")
    code, lines = _load("compare").compare(tmp_path / "a", tmp_path / "b")
    assert code == 0 and "bodies differing: 0" in lines, lines


def test_a_capture_refuses_to_write_inside_the_repo() -> None:
    """Its bodies carry licensed transcript text."""
    from vinci.evals.replay import ReplayError

    with pytest.raises(ReplayError, match="inside the repository"):
        _load("capture").run(ROOT / "sdk-capture-here", None, None)
    assert not (ROOT / "sdk-capture-here").exists()


def _fake_run(d: Path, bodies: dict[str, bytes], version: str, *, url: str = "u",
              extra: tuple[tuple[str, str], ...] = ()) -> None:
    d.mkdir(parents=True)
    rows = []
    for label, body in bodies.items():
        (d / f"{label}.body").write_bytes(body)
        rows.append({"path": "p", "label": label, "n": 1, "method": "POST", "url": url,
                     "headers": [["user-agent", f"Anthropic/Python {version}"],
                                 ["x-api-key", "sk-ant-secret"], *map(list, extra)],
                     "body_file": f"{label}.body"})
    (d / "index.json").write_text(json.dumps(rows))
    (d / "summary.json").write_text(json.dumps({"anthropic": version, "http_lib": "httpx"}))


def test_the_comparer_fails_on_one_changed_byte_and_on_a_missing_request(tmp_path: Path) -> None:
    cmp = _load("compare")
    _fake_run(tmp_path / "a", {"x": b'{"a":1}', "y": b'{"b":2}'}, "1")
    _fake_run(tmp_path / "same", {"x": b'{"a":1}', "y": b'{"b":2}'}, "2")
    _fake_run(tmp_path / "byte", {"x": b'{"a":1}', "y": b'{"b":3}'}, "2")
    _fake_run(tmp_path / "short", {"x": b'{"a":1}'}, "2")
    code, lines = cmp.compare(tmp_path / "a", tmp_path / "same")
    assert code == 0, lines
    assert "  user-agent: 'Anthropic/Python 1' -> 'Anthropic/Python 2'  (on 2 request(s))" in lines
    assert not any("sk-ant-secret" in x for x in lines), "a credential header was printed"
    code, lines = cmp.compare(tmp_path / "a", tmp_path / "byte")
    assert code == 1 and "bodies differing: 1 — [('p', 'y', 1)]" in lines, lines
    code, lines = cmp.compare(tmp_path / "a", tmp_path / "short")
    assert code == 1 and any(x.startswith("requests on one side only (1)") for x in lines), lines


def test_two_empty_captures_are_no_pass(tmp_path: Path) -> None:
    _fake_run(tmp_path / "a", {}, "1")
    _fake_run(tmp_path / "b", {}, "2")
    code, lines = _load("compare").compare(tmp_path / "a", tmp_path / "b")
    assert code == 1 and any(x.startswith("no request compared") for x in lines), lines


def test_the_ping_capture_keeps_the_processs_own_key(
        tmp_path: Path, offline: None, monkeypatch: pytest.MonkeyPatch) -> None:
    import os
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a-key-of-this-process")
    cap_mod = _load("capture")
    cap_mod.validate_keys(cap_mod.Capture(tmp_path, "validate-keys"))
    assert os.environ["ANTHROPIC_API_KEY"] == "a-key-of-this-process"


def test_the_impact_child_reads_only_names_the_inputs_module_serves() -> None:
    """`build_inputs.py` swaps `vinci.impact.run.CAPTURE_CHILD` for `impact_capture.py`: every
    `capture.<name>` the child reads must resolve there, or the inputs are never written."""
    from vinci.impact import run as impact_run

    assert impact_run.CAPTURE_CHILD.name == "capture_child.py"
    module = _load("impact_capture")
    read = set(re.findall(r"\bcapture\.(\w+)", (ROOT / "vinci" / "impact" / "child.py")
                          .read_text()))
    assert "capture_calls" in read
    assert [n for n in sorted(read) if not hasattr(module, n)] == []


V1 = "https://api.anthropic.com/v1/messages"
#: The headers 0.112.0 and 2.6.0 sent, as captured on 2026-11-13 (the key's value replaced).
OLD = [("accept-encoding", "gzip, deflate"), ("user-agent", "Anthropic/Python 0.112.0"),
       ("x-stainless-package-version", "0.112.0"), ("x-api-key", "sk-ant-k"),
       ("anthropic-version", "2023-06-01")]
NEW = [("accept-encoding", "gzip, deflate, zstd"), ("user-agent", "Anthropic/Python 2.6.0"),
       ("x-stainless-package-version", "2.6.0"), ("authorization", "Bearer sk-ant-k"),
       ("anthropic-version", "2026-10-21")]


def _headers_run(d: Path, version: str, headers: list[tuple[str, str]], url: str = V1) -> Path:
    d.mkdir(parents=True)
    (d / "x.body").write_bytes(b'{"a":1}')
    (d / "index.json").write_text(json.dumps([{
        "path": "p", "label": "x", "n": 1, "method": "POST", "url": url,
        "headers": [list(h) for h in headers], "body_file": "x.body"}]))
    (d / "summary.json").write_text(json.dumps({"anthropic": version, "http_lib": "httpx"}))
    return d


def _with(headers: list[tuple[str, str]], name: str, value: str) -> list[tuple[str, str]]:
    return [*[h for h in headers if h[0] != name], (name, value)]


def test_the_record_s_header_changes_pass_and_any_other_change_fails(tmp_path: Path) -> None:
    """Review of #1049. Round 1: a planted `/v1/messages?beta=true` exited 0, and so did an added
    header. Round 2: headers were accepted by NAME, so `anthropic-version: 2027-03-01` (the one
    header that changes what the server does) and `accept-encoding: gzip` exited 0. Now only the
    record's exact changes pass (`compare.ACCEPTED`), plus the SDK's version stamps moving by its
    version, which is all the next bump should show."""
    cmp = _load("compare")
    a = _headers_run(tmp_path / "a", "0.112.0", OLD)
    code, lines = cmp.compare(a, _headers_run(tmp_path / "b", "2.6.0", NEW))
    assert code == 0 and not any("NOT ACCEPTED" in x for x in lines), lines
    # the next bump: same API version and key header, only the version stamps move
    nxt = [(n, v.replace("2.6.0", "2.7.0")) for n, v in NEW]
    code, lines = cmp.compare(_headers_run(tmp_path / "n26", "2.6.0", NEW),
                              _headers_run(tmp_path / "n27", "2.7.0", nxt))
    assert code == 0, lines
    failing = {
        "url": (NEW, V1 + "?beta=true", "method/URL differing: 1"),
        "beta": ([*NEW, ("anthropic-beta", "files-api-2025-04-14")], V1, "anthropic-beta"),
        "api-version": (_with(NEW, "anthropic-version", "2027-03-01"), V1, "anthropic-version"),
        "encoding": (_with(NEW, "accept-encoding", "gzip"), V1, "accept-encoding"),
        "stamp": (_with(NEW, "user-agent", "Anthropic/Python 2.6.0 (patched)"), V1, "user-agent"),
    }
    for case, (headers, url, named) in failing.items():
        code, lines = cmp.compare(a, _headers_run(tmp_path / case, "2.6.0", headers, url))
        assert code == 1, (case, lines)
        assert any(named in x and ("NOT ACCEPTED" in x or case == "url") for x in lines), lines
