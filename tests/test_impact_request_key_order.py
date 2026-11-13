"""The impact check sees a synthesis request that differs only in KEY ORDER (2026-11-13).

THE BLIND SPOT. The impact child wrote each page side's ``request.json`` key-sorted (`_side_file`),
and `run.request_diff` compared the two sides byte for byte (`replay.wire`) — of two sorted copies.
A change that only reorders the tool schema's fields or the top-level arguments therefore read
"identical", and that is the defect class PR 2 drew: production's tool schema sent alphabetised in
all 70 draws (`capture_child.jsonable`). Found preparing #953's retrospective panel check, where
the run's sorted ``request.json`` could not be exported as the request production sends.

THE FIX: the child writes the request in the captured key order (`child.write_request`), the
comparison is exact, and a difference that is key order alone is named (`key_order_only`).

Each pin is on a REAL request: production's own capture (`capture_child.capture_calls`, the client
that sends nothing) of a frozen committed page, with the reorder planted on top of it."""
from __future__ import annotations

import copy
import json
import pathlib
from typing import Any

import pytest

from vinci.evals import capture_child as cap
from vinci.impact import child
from vinci.impact import run as rn

ROOT = pathlib.Path(__file__).resolve().parents[1]
#: A frozen committed page with no transcript rows, so it captures offline at $0 (every other
#: frozen page holds driver rows whose words are in the private store, and capture refuses them)
PAGE = ROOT / "tests" / "fixtures" / "frozen_pages" / "2026-09-28" / "TECX" / "dossier.json"


@pytest.fixture(scope="module")
def real_request() -> dict[str, Any]:
    doc = json.loads(PAGE.read_text(encoding="utf-8"))
    calls = cap.capture_calls(doc, None, model="claude-opus-4-8", draws=1)
    return cap.jsonable(calls[0])


def _alphabetised_tool(k: dict[str, Any]) -> dict[str, Any]:
    """PR 2's defect, planted: the tool schema's fields in alphabetical order, every value equal."""
    out = copy.deepcopy(k)
    props = out["tools"][0]["input_schema"]["properties"]
    assert list(props) != sorted(props), "the fixture's schema must not already be alphabetical"
    out["tools"][0]["input_schema"]["properties"] = {f: props[f] for f in sorted(props)}
    return out


def _tools_before_system(k: dict[str, Any]) -> dict[str, Any]:
    """The top-level arguments reordered: ``tools`` before ``system``, every value equal."""
    keys = list(k)
    assert keys.index("system") < keys.index("tools")
    order = [x for x in keys if x != "system"]
    order.insert(order.index("tools") + 1, "system")
    return {x: copy.deepcopy(k[x]) for x in order}


def _compare(tmp_path: pathlib.Path, base: dict[str, Any], head: dict[str, Any],
             write: Any) -> dict[str, Any]:
    """Both sides written as the child writes them, then compared as the run compares them."""
    s = rn.Settings(repo=ROOT, base="b", head="h", out=tmp_path, ciq_root=tmp_path,
                    cache_root=tmp_path, store=tmp_path, env_file=None)
    for side, k in (("base", base), ("head", head)):
        page = tmp_path / "pages" / side / "TECX"
        page.mkdir(parents=True, exist_ok=True)
        (page / "built.json").write_text(PAGE.read_text(encoding="utf-8"), encoding="utf-8")
        write(page / "request.json", [k] * 5)
    result: dict[str, Any] = rn.compare_page(s, "TECX")["request"]
    return result


def _sorted_writer(path: pathlib.Path, calls: list[dict[str, Any]]) -> None:
    child._side_file(path, {"calls": calls})   # how request.json was written before 2026-11-13


@pytest.mark.parametrize("plant", [_alphabetised_tool, _tools_before_system])
def test_a_request_that_differs_only_in_key_order_was_invisible_when_written_sorted(
        tmp_path: pathlib.Path, real_request: dict[str, Any], plant: Any) -> None:
    """THE BLIND SPOT, kept as a pin: a sorted record erases the reorder, so the run compares two
    identical files. This is why the request is never written by `_side_file`."""
    got = _compare(tmp_path, real_request, plant(real_request), _sorted_writer)
    assert got["identical"] is True


def test_an_alphabetised_tool_schema_is_a_request_move_and_named_key_order_only(
        tmp_path: pathlib.Path, real_request: dict[str, Any]) -> None:
    got = _compare(tmp_path, real_request, _alphabetised_tool(real_request),
                   child.write_request)
    assert got["identical"] is False
    assert got["key_order_only"] is True
    assert got["tools_equal"] is False
    assert got["system_equal"] is True
    assert got["sections"] == [] and got["other_kwargs"] == []


def test_reordered_top_level_arguments_are_a_request_move_and_named_key_order_only(
        tmp_path: pathlib.Path, real_request: dict[str, Any]) -> None:
    got = _compare(tmp_path, real_request, _tools_before_system(real_request),
                   child.write_request)
    assert got["identical"] is False
    assert got["key_order_only"] is True
    assert got["tools_equal"] is True and got["system_equal"] is True
    assert got["sections"] == [] and got["other_kwargs"] == []


def test_a_changed_value_is_never_key_order_only(
        tmp_path: pathlib.Path, real_request: dict[str, Any]) -> None:
    head = copy.deepcopy(real_request)
    head["max_tokens"] = int(head["max_tokens"]) + 1
    got = _compare(tmp_path, real_request, head, child.write_request)
    assert got["identical"] is False and got["key_order_only"] is False
    assert got["other_kwargs"] == ["max_tokens"]


def test_the_same_request_on_both_sides_is_identical_and_names_no_order(
        tmp_path: pathlib.Path, real_request: dict[str, Any]) -> None:
    got = _compare(tmp_path, real_request, copy.deepcopy(real_request), child.write_request)
    assert got["identical"] is True and "key_order_only" not in got


def test_the_written_request_reads_back_in_the_captured_order(
        tmp_path: pathlib.Path, real_request: dict[str, Any]) -> None:
    """What a panel export takes from the run: the bytes production sends (`replay.wire`), not a
    sorted copy of them."""
    from vinci.evals.replay import wire

    child.write_request(tmp_path / "request.json", [real_request])
    back = json.loads((tmp_path / "request.json").read_text(encoding="utf-8"))["calls"][0]
    assert wire(back) == wire(real_request)
    assert list(back["tools"][0]["input_schema"]["properties"]) == list(
        real_request["tools"][0]["input_schema"]["properties"])


def test_the_report_names_a_key_order_only_request_and_no_other(
        tmp_path: pathlib.Path, real_request: dict[str, Any]) -> None:
    """The rendered section 3, from two real compared requests: a key-order-only page is counted
    among those that differ and NAMED so; a page whose value moved is not."""
    from vinci.impact import report

    order = _compare(tmp_path / "o", real_request, _alphabetised_tool(real_request),
                     child.write_request)
    head = copy.deepcopy(real_request)
    head["max_tokens"] = int(head["max_tokens"]) + 1
    value = _compare(tmp_path / "v", real_request, head, child.write_request)
    r = {"pages": {"results": [{"ticker": "ORDER", "status": "same", "request": order},
                               {"ticker": "VALUE", "status": "same", "request": value}]}}
    lines = report.requests_lines(r)
    assert lines[0].startswith("### 3. Synthesis requests — 2 of 2 pages' requests differ")
    row = {ln.split("**")[1]: ln for ln in lines if ln.startswith("- **")}
    assert "KEY ORDER ONLY" in row["ORDER"] and "tool schema DIFFERS" in row["ORDER"]
    assert "KEY ORDER ONLY" not in row["VALUE"]
