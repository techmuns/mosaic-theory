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


# ------------------------------------------------------------------ review round 1 (#1059)

def _page_side(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, side: str,
               capture: Any) -> pathlib.Path:
    """`child.page` itself, the call site that writes ``request.json``, on the frozen TECX page:
    only the $0 build and the CIQ reads are stubbed (to that page, and to no transcript)."""
    from vinci.dossier import ciq, ciq_sheets, prespend
    from vinci.dossier.schemas import Dossier

    frozen = Dossier.model_validate_json(PAGE.read_text(encoding="utf-8"))
    monkeypatch.setattr(prespend, "mechanical_build", lambda ticker, cfg: frozen)
    monkeypatch.setattr(ciq.CiqBundle, "from_files", classmethod(lambda cls, t, files: None))
    monkeypatch.setattr(ciq_sheets, "transcript_for_synthesis", lambda bundle: None)
    out = tmp_path / "pages" / side / "TECX"
    child.page("TECX", out, capture=capture, requests=True, committed=False)
    assert not (out / "request.error.json").exists(), (out / "request.error.json").read_text()
    return out


class _AlphabetisedCapture:
    """Production's capture, with PR 2's defect planted in what it returns."""

    def __getattr__(self, name: str) -> Any:
        return getattr(cap, name)

    def capture_calls(self, *a: Any, **k: Any) -> list[dict[str, Any]]:
        return [_alphabetised_tool(cap.jsonable(c)) for c in cap.capture_calls(*a, **k)]


def test_the_page_writes_its_request_in_the_captured_order_and_a_reorder_reaches_the_compare(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
        real_request: dict[str, Any]) -> None:
    """THE CALL SITE (review round 1, finding 1): every earlier pin called `write_request`
    directly, so putting the old line back in `child.page` (``_side_file(out / "request.json",
    …)``, the reviewer's mutant M4) left the suite green and the blind spot open."""
    base = _page_side(tmp_path, monkeypatch, "base", cap)
    head = _page_side(tmp_path, monkeypatch, "head", _AlphabetisedCapture())
    written = json.loads((base / "request.json").read_text(encoding="utf-8"))["calls"]
    assert len(written) > 1
    # the top level in the captured order (the page's five draws add `cache_control` at the end)
    assert [k for k in written[0] if k in real_request] == list(real_request)
    assert list(written[0]) != sorted(written[0])
    assert list(written[0]["tools"][0]["input_schema"]["properties"]) == list(
        real_request["tools"][0]["input_schema"]["properties"])
    assert (head / "request.json").exists()
    s = rn.Settings(repo=ROOT, base="b", head="h", out=tmp_path, ciq_root=tmp_path,
                    cache_root=tmp_path, store=tmp_path, env_file=None)
    got = rn.compare_page(s, "TECX")["request"]
    assert got["identical"] is False and got["key_order_only"] is True


class _ReachedError(Exception):
    """Raised by the first step after the run folder's identity check."""


def _resume(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
            marker: dict[str, str] | None) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / "pages").mkdir()
    s = rn.Settings(repo=ROOT, base="b", head="h", out=out, ciq_root=tmp_path,
                    cache_root=tmp_path, store=tmp_path / "vinci.db", env_file=None, resume=True)
    # no git here (the fail-first run holds the tree without .git): the refs resolve to one sha,
    # and the out-inside-the-repo guard is not what this pins
    sha = "a" * 40
    monkeypatch.setattr(rn.st, "sha", lambda repo, ref: sha)
    monkeypatch.setattr(rn.st, "merge_base", lambda repo, a, b: sha)
    monkeypatch.setattr(rn, "_inside", lambda path, repo: False)
    run_id = {"base": sha, "head": sha, "store": str(s.store)}
    if marker is not None:
        run_id = {**run_id, **marker}
    (out / "run.json").write_text(json.dumps(run_id), encoding="utf-8")

    def reached(*a: Any, **k: Any) -> Any:
        raise _ReachedError

    monkeypatch.setattr(rn.st, "diff_identity", reached)
    rn.run(s)


def test_resume_refuses_a_run_folder_written_by_other_check_code(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Review round 1, finding 2: a folder started before this change holds sorted request sides;
    resumed, its rebuilt sides are written in captured order, and every such page would read KEY
    ORDER ONLY with no code change behind it. The folder names the check's own child and capture
    code, so a folder from other code is refused as "one run, one folder"."""
    with pytest.raises(rn.ImpactError, match="one run, one folder"):
        _resume(tmp_path, monkeypatch, None)    # a marker written before the change


def test_resume_continues_a_run_folder_written_by_the_same_check_code(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from vinci.impact.run import CAPTURE_CHILD, CHILD, file_sha256

    with pytest.raises(_ReachedError):
        _resume(tmp_path, monkeypatch, {"child": file_sha256(CHILD),
                                        "capture": file_sha256(CAPTURE_CHILD)})


def test_a_key_order_move_names_the_arguments_it_moved_in(
        tmp_path: pathlib.Path, real_request: dict[str, Any]) -> None:
    """Review round 1, finding 3: a reorder inside ``messages`` printed "system same; tool schema
    same; USER −0 +0", naming nothing. The diff names each argument whose order moved, and the
    order of the arguments themselves."""
    from vinci.impact import report

    inner = copy.deepcopy(real_request)
    inner["messages"][0] = dict(reversed(list(inner["messages"][0].items())))
    got = _compare(tmp_path / "m", real_request, inner, child.write_request)
    assert got["key_order_only"] is True and got["order_moved"] == ["messages"]
    tools = _compare(tmp_path / "t", real_request, _alphabetised_tool(real_request),
                     child.write_request)
    assert tools["order_moved"] == ["tools"]
    top = _compare(tmp_path / "a", real_request, _tools_before_system(real_request),
                   child.write_request)
    assert top["order_moved"] == ["(the arguments' own order)"]
    lines = report.requests_lines({"pages": {"results": [
        {"ticker": "TECX", "status": "same", "request": got}]}})
    row = next(ln for ln in lines if ln.startswith("- **TECX**"))
    assert "KEY ORDER ONLY" in row and "messages" in row
