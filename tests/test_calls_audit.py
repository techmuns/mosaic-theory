"""The LLM second reading — resumability, blast radius, and vocabulary agreement.

No network here: the client is a stub. What is pinned is the machinery around the call, which is
where a run of thousands of PAID calls actually gets hurt — one malformed response aborting the
batch, or a resume that re-pays for work already done.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from vinci.calls.audit import (
    ACTIONS,
    BIASES,
    CLASSES,
    SPECS,
    TARGET_TYPES,
    TOOL,
    audit_post,
    load_audit,
    run_audit,
)
from vinci.graph.llm import LlmClient, LlmError

POST = {"id": "1", "d": "2026-01-05", "t": "2026-01-05T14:00:00+00:00",
        "tk": ["$AAA"], "txt": "$AAA looks strong"}

GOOD: dict[str, Any] = {
    "post_class": "signal_candidate", "is_retrospective": False, "is_conditional": False,
    "probability": None, "summary": "likes it",
    "tickers": [{"ticker": "AAA", "bias": "bullish", "action": "none", "target": None,
                 "target_type": "none", "horizon_lo_days": None, "horizon_hi_days": None,
                 "spec": "C", "note": "says strong"}],
}


class _Stub(LlmClient):
    def __init__(self, *answers: Any) -> None:
        self._answers = list(answers)
        self.calls: list[str] = []

    @property
    def model(self) -> str:
        return "stub"

    def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(user)
        a = self._answers.pop(0) if self._answers else GOOD
        if isinstance(a, Exception):
            raise a
        return dict(a)


def test_one_bad_post_is_recorded_not_raised() -> None:
    """A run is thousands of paid calls. If a single malformed response aborted it, the operator
    loses every call still in flight and has to reason about what landed — so the failure is
    written onto the row and the batch continues."""
    r = audit_post(_Stub(LlmError("model returned prose")), POST, ["AAA"])
    assert r.error and "LlmError" in r.error
    assert r.tickers == [] and r.tweet_id == "1"

    r2 = audit_post(_Stub({"post_class": "signal_candidate"}), POST, ["AAA"])
    assert r2.error and "ValidationError" in r2.error, "a short response was accepted as a reading"


def test_a_response_missing_only_the_ticker_array_keeps_what_it_did_return() -> None:
    """OBSERVED TWICE ON THE REAL CORPUS. The model returned post_class, probability and a summary
    and simply omitted the ticker array. Failing the whole row threw away a correct post-level
    reading to punish a missing sub-field — but an EMPTY list must never pass silently either,
    because "no view on any ticker" is indistinguishable from a correct `none` on every one."""
    partial = {k: v for k, v in GOOD.items() if k != "tickers"}
    r = audit_post(_Stub(partial), POST, ["AAA"])
    assert r.post_class == "signal_candidate", "the post-level reading was discarded"
    assert r.summary == "likes it"
    assert r.tickers == []
    assert r.error and "no ticker array" in r.error, "an empty reading passed as a complete one"


def test_a_resumed_run_does_not_pay_twice(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE MONEY PIN. Appended as results land, and already-present ids are skipped, so an
    interruption costs the in-flight call and nothing else."""
    d = tmp_path / "acct"
    d.mkdir()
    monkeypatch.setattr("vinci.calls.audit.account_dir", lambda h, **k: d)
    posts = [dict(POST, id=str(i)) for i in range(1, 6)]

    first = _Stub(*([GOOD] * 5))
    c1 = run_audit("acct", posts=posts[:3], tickers_of=lambda p: ["AAA"], client=first, workers=2)
    assert c1["attempted"] == 3 and c1["skipped"] == 0
    assert len(first.calls) == 3

    second = _Stub(*([GOOD] * 5))
    c2 = run_audit("acct", posts=posts, tickers_of=lambda p: ["AAA"], client=second, workers=2)
    assert c2["skipped"] == 3, "a resume re-read the corpus but did not skip what was done"
    assert c2["attempted"] == 2, f"a resume re-paid for {c2['attempted'] - 2} finished call(s)"
    assert len(second.calls) == 2

    assert set(load_audit("acct")) == {"1", "2", "3", "4", "5"}
    assert len((d / "audit.jsonl").read_text().strip().splitlines()) == 5


def test_the_reading_is_recorded_per_ticker_not_per_post(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """His Monthly BX Cycle Report names eight tickers and marks them in BOTH directions, so a
    post-level verdict would flatten a bullish and a bearish call into one."""
    d = tmp_path / "acct"
    d.mkdir()
    monkeypatch.setattr("vinci.calls.audit.account_dir", lambda h, **k: d)
    both = dict(GOOD, tickers=[
        dict(GOOD["tickers"][0], ticker="AAA", bias="bullish"),
        dict(GOOD["tickers"][0], ticker="BBB", bias="bearish"),
    ])
    r = audit_post(_Stub(both), dict(POST, tk=["$AAA", "$BBB"]), ["AAA", "BBB"])
    assert {t.ticker: t.bias for t in r.tickers} == {"AAA": "bullish", "BBB": "bearish"}


def test_the_tool_vocabulary_matches_what_the_rest_of_the_system_accepts() -> None:
    """The schema's enums, the workbook's dropdowns and the tape's editor are three surfaces over
    one vocabulary. If the model can return a value the sheet cannot offer, the reading is
    unusable at exactly the rows where it disagrees — which are the only rows that matter."""
    props = TOOL["input_schema"]["properties"]
    tk = props["tickers"]["items"]["properties"]
    assert tk["bias"]["enum"] == BIASES
    assert tk["action"]["enum"] == ACTIONS
    assert tk["target_type"]["enum"] == TARGET_TYPES
    assert tk["spec"]["enum"] == SPECS
    assert props["post_class"]["enum"] == CLASSES

    # BEHAVIOURAL COVER FOR AN ACCEPTED TWIN. These four vocabularies are written out in BOTH
    # `vinci/calls/audit.py` and `frontend/views/calls/tape.js`, and the duplicate detector's
    # baseline accepts that (neither side can import the other, and DERIVING the lists from the
    # corpus would silently drop any value with zero rows — leaving the operator unable to SET it,
    # which is the same defect inverted). What must not happen is one side gaining a value the
    # other cannot express: the model would return a reading the sheet cannot offer and the tape
    # cannot store, at exactly the rows where the two readers disagree. So every value is asserted
    # present on the JS side here.
    tape = Path(__file__).resolve().parents[1] / "frontend" / "views" / "calls" / "tape.js"
    if tape.is_file():
        src = tape.read_text()
        for name, values in (("bias", BIASES), ("action", ACTIONS),
                             ("target_type", TARGET_TYPES), ("post_class", CLASSES)):
            for v in values:
                assert f'"{v}"' in src, (
                    f"the tape cannot express {name}={v!r} — the audit can return it, so a "
                    f"disagreement on that value would be unreadable and unsavable")
        for sp in SPECS:
            assert f'["{sp}"' in src or f'"{sp}",' in src or f"'{sp}'" in src, (
                f"the tape has no spec tier {sp!r}")

    # and every required field is actually required, or the model may omit the disagreement
    req = set(tk_req := TOOL["input_schema"]["properties"]["tickers"]["items"]["required"])
    assert {"ticker", "bias", "action", "target", "target_type", "spec"} <= req, tk_req


def test_a_run_with_nothing_to_do_makes_no_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = tmp_path / "acct"
    d.mkdir()
    monkeypatch.setattr("vinci.calls.audit.account_dir", lambda h, **k: d)
    (d / "audit.jsonl").write_text(json.dumps({
        "tweet_id": "1", "post_class": "noise", "is_retrospective": False,
        "is_conditional": False, "probability": None, "tickers": []}) + "\n")
    stub = _Stub()
    counts = run_audit("acct", posts=[POST], tickers_of=lambda p: ["AAA"], client=stub, workers=2)
    assert stub.calls == [] and counts["attempted"] == 0 and counts["skipped"] == 1
