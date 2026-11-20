"""W85's panel draw (2026-11-20): registration 2f2314b0 was claimed, then stopped before any
call, and a claim is drawn once. Coordinator B's fix, approved by the operator ("Yes, void it
and fix"):

(i)  every paid client is built, its key read, BEFORE the draw is claimed: `run-compare` and
     `run` claimed first and built the client inside `run_request`, so a checkout with no
     ``ANTHROPIC_API_KEY`` left a `drawn` row in the index and a claim in the ledger, and
     nothing drawn;
(ii) a claim that drew nothing is VOIDED (`void-claim`), in the ledger and the index, and the
     void is honoured by `claim_draw`, `_drawn_pins` and `run_compare`'s ledger checks only
     while the run has no draws, its claim recorded $0.00 and nothing was recorded after it.

$0: no key, no network. A real Anthropic client is never built (`no_network`); a draw that passes
every refusal reaches `_SendSpy`, which stops it before anything is sent.
"""
from __future__ import annotations

import functools
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from tests.test_evals_order8 import _impact_export, _to_main
from tests.test_evals_order8_gaps import _SendSpy
from tests.test_evals_order8_round2 import (
    _approvals,
    _builds_through_the_cli,
    _register,
    _run_compare,
    index,  # noqa: F401 — the CLI's index fixture
)
from vinci.evals import registry
from vinci.evals.replay import ReplayError


class _NoNetwork:
    """`anthropic.Anthropic`, replaced: it may be built (the $0 capture builds one with a
    placeholder key and swaps it out at once), and it never sends, key or no key."""

    def __init__(self, *a: Any, **k: Any) -> None:
        pass

    def with_options(self, **k: Any) -> _NoNetwork:
        return self

    @property
    def messages(self) -> Any:
        raise AssertionError("a request reached the Anthropic API")


@pytest.fixture()
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    import anthropic
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(anthropic, "Anthropic", _NoNetwork)


@pytest.fixture()
def send_spy(monkeypatch: pytest.MonkeyPatch, no_network: None) -> type[_SendSpy]:
    """`AnthropicLlmClient`, replaced by one that builds and stops at its first send: a draw
    that reaches it passed every refusal, and its claim."""
    from vinci.evals import replay as rp
    _SendSpy.built = _SendSpy.sent = 0
    monkeypatch.setattr(rp, "AnthropicLlmClient", _SendSpy)
    return _SendSpy


@pytest.fixture()
def voids(index: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:  # noqa: F811
    """`void-claim` writes the temporary repository's index, as the CLI's other commands do."""
    monkeypatch.setattr(registry, "record_void",
                        functools.partial(registry.record_void, root=index))
    yield index


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def _events(repo: Path, event: str) -> list[dict[str, Any]]:
    return [r for r in registry.working_rows(repo) if r.get("event") == event]


def _void_claim(registration: Path, ledger: Path, out_dir: Path) -> int:
    from vinci.evals import __main__ as cli
    return cli.main(["void-claim", "--registration", str(registration), "--budget-ledger",
                     str(ledger), "--out-dir", str(out_dir)])


def _stopped_claim(tmp_path: Path, repo: Path) -> tuple[Path, Path, Path, Any]:
    """REGISTRATION 2f2314b0's STATE, as main's order left it on 2026-11-20 (bbbd3d4b): the
    registration on main; its `drawn` row in the working index; the ledger's approval line and
    then the claim, `{"out_dir", "registration", "usd": 0.0}`, as its last row; a run folder
    holding `registration.json` and `requests.jsonl` and no `draws.jsonl`. Written here as
    `run_compare` wrote it before its first client, since the fixed order never leaves it."""
    from vinci.evals import replay as rp
    export, _ = _impact_export(tmp_path)
    ledger, _ = _approvals(tmp_path)
    reg = _register(export, ledger, tmp_path / "r1.json", "--no-worsening")
    _to_main(repo)
    registry.claim_draw(reg, approval=registry.approval_id(ledger), root=repo)
    run1 = tmp_path / "run1"
    run1.mkdir()
    (run1 / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    rp.Budget.load(ledger).record({"registration": reg.sha, "out_dir": str(run1), "usd": 0.0})
    (run1 / "requests.jsonl").write_text(json.dumps({"ticker": "NFLX"}) + "\n")
    assert [set(r) for r in _rows(ledger)] == [{"approval"}, {"out_dir", "registration", "usd"}]
    assert [r["event"] for r in registry.working_rows(repo)] == ["registered", "drawn"]
    return tmp_path / "r1.json", ledger, run1, reg


# ------------------------------------------- (i) the client, and its key, before the claim


def test_a_paid_compare_with_no_key_is_refused_with_nothing_claimed(
        tmp_path: Path, index: Path, no_network: None) -> None:  # noqa: F811
    """(−) The 2f2314b0 failure, end to end through the CLI. On bbbd3d4b `run-compare --paid`
    from a checkout with no key claimed the registration — a `drawn` row, a ledger claim, the run
    folder written — and only then raised building the client. Refused now before the claim:
    no `drawn` row, no ledger row after the approval, no run folder."""
    export, _ = _impact_export(tmp_path)
    ledger, _ = _approvals(tmp_path)
    _register(export, ledger, tmp_path / "r1.json", "--no-worsening")
    _to_main(index)
    with pytest.raises(ReplayError, match="ANTHROPIC_API_KEY.*nothing is claimed or drawn"):
        _run_compare(tmp_path / "r1.json", ledger, tmp_path / "run1")
    assert _events(index, "drawn") == []
    assert [set(r) for r in _rows(ledger)] == [{"approval"}]
    assert not (tmp_path / "run1").exists()


def test_a_paid_build_with_no_key_is_refused_with_nothing_claimed(
        tmp_path: Path, index: Path, no_network: None,  # noqa: F811
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) The same order in `run`: `run_build` claimed the build's unit and wrote its start row,
    then `run_request` raised building the client, so the build could never be drawn. Refused
    now before the claim."""
    from vinci.evals import __main__ as cli
    _builds_through_the_cli(tmp_path, monkeypatch)
    ledger, _ = _approvals(tmp_path)
    assert cli.main(["register-run", "--code-ref", "HEAD", "--ticker", "NFLX", "--draws", "2",
                     "--builds", "2", "--ciq-root", str(tmp_path / "ciq"), "--budget-ledger",
                     str(ledger), "--out", str(tmp_path / "r1.json")]) == 0
    _to_main(index)
    with pytest.raises(ReplayError, match="ANTHROPIC_API_KEY.*nothing is claimed or drawn"):
        cli.main(["run", "--registration", str(tmp_path / "r1.json"), "--ticker", "NFLX",
                  "--build", "1", "--budget-ledger", str(ledger), "--draws-out",
                  str(tmp_path / "d1.jsonl"), "--paid"])
    assert _events(index, "drawn") == []
    assert [set(r) for r in _rows(ledger)] == [{"approval"}]


# --------------------------------------- (ii) a claim that drew nothing is voided, and only it


def test_the_stopped_2f2314_claim_is_voided_and_drawn_again(
        tmp_path: Path, voids: Path, send_spy: type[_SendSpy]) -> None:
    """(+) B's pin: the real 2f2314b0 shape is voidable. Before the void, a re-draw into a fresh
    folder is refused (the ledger's "already drawn under this approval"); `void-claim` writes one
    `void` row to the index, naming the claim it cancels, and one to the ledger, right after the
    claim; the same registration is then drawn into a fresh folder — it passes every refusal,
    is claimed once more, and reaches the send."""
    registration, ledger, run1, reg = _stopped_claim(tmp_path, voids)
    with pytest.raises(ReplayError, match="already drawn under this approval"):
        _run_compare(registration, ledger, tmp_path / "run2")
    assert send_spy.built == 0
    assert _void_claim(registration, ledger, run1) == 0
    (void,) = _events(voids, "void")
    (claimed,) = _events(voids, "drawn")
    assert (void["registration"], void["approval"], void["voids"]) == (
        reg.sha, claimed["approval"], claimed["drawn_at"])
    assert _rows(ledger)[-1] == {"void": reg.sha, "out_dir": str(run1), "usd": 0.0}
    _to_main(voids)   # the void row is committed with the run's record before the re-draw
    with pytest.raises(AssertionError, match="a paid client sent a draw"):
        _run_compare(registration, ledger, tmp_path / "run2")
    assert (send_spy.built, send_spy.sent) == (2, 1)   # NFLX BASE and CAND, before the claim
    assert len(_events(voids, "drawn")) == 2
    assert [r["out_dir"] for r in _rows(ledger) if "registration" in r] == [
        str(run1), str(tmp_path / "run2")]


def _a_failed_call(run1: Path, ledger: Path) -> None:
    """A call that failed: `GuardedSdk` writes its draws row (unpriced, so no ledger row)."""
    (run1 / "draws.jsonl").write_text(json.dumps({
        "label": "NFLX:BASE", "draw": 1, "usd": 0.0, "raw": None, "stop_reason": None,
        "error": "APIConnectionError: Connection error.", "sdk_version": "0.0"}) + "\n")


def _a_priced_call(run1: Path, ledger: Path) -> None:
    """A priced call recorded in the ledger, its draws row gone from the folder."""
    from vinci.evals import replay as rp
    rp.Budget.load(ledger).record({"label": "NFLX:BASE", "draw": 1, "usd": 0.0123,
                                   "usage": {"input_tokens": 1, "output_tokens": 1}})


def _a_spent_claim(run1: Path, ledger: Path) -> None:
    """A claim row that is not $0.00 (the approval line kept byte for byte: it is the approval's
    identity)."""
    lines = ledger.read_text(encoding="utf-8").splitlines(keepends=True)
    claim = {**json.loads(lines[-1]), "usd": 0.5}
    ledger.write_text("".join(lines[:-1]) + json.dumps(claim, sort_keys=True) + "\n")


@pytest.mark.parametrize(("spend", "refusal"), [
    (_a_failed_call, "holds draws"),
    (_a_priced_call, "recorded in the ledger after"),
    (_a_spent_claim, r"not \$0\.00"),
], ids=["one failed draw", "one priced call", "a claim not $0.00"])
def test_a_run_that_drew_is_never_voided(tmp_path: Path, voids: Path,
                                         send_spy: type[_SendSpy], spend: Any,
                                         refusal: str) -> None:
    """(−) B's pin: a run with one draw is not voidable — a failed call (its draws row written),
    a priced call (its ledger row recorded) or a claim that is not $0.00. Nothing is written to
    the index or the ledger, and the registration stays drawn."""
    registration, ledger, run1, _ = _stopped_claim(tmp_path, voids)
    spend(run1, ledger)
    before = ledger.read_bytes()
    with pytest.raises(ReplayError, match=refusal):
        _void_claim(registration, ledger, run1)
    assert _events(voids, "void") == [] and ledger.read_bytes() == before
    with pytest.raises(ReplayError, match="already drawn"):
        _run_compare(registration, ledger, tmp_path / "run2")
    assert send_spy.built == 0


def test_a_void_is_checked_again_when_it_is_read(tmp_path: Path, voids: Path,
                                                 send_spy: type[_SendSpy]) -> None:
    """(−) A void is honoured only while its run still drew nothing: draws written into the
    voided folder after the void refuse the re-draw, before any client. A second void of the
    same claim is refused (the claim is no longer live)."""
    registration, ledger, run1, _ = _stopped_claim(tmp_path, voids)
    assert _void_claim(registration, ledger, run1) == 0
    _to_main(voids)
    with pytest.raises(ReplayError, match="nothing is voided"):
        _void_claim(registration, ledger, run1)
    _a_failed_call(run1, ledger)
    with pytest.raises(ReplayError, match="now holds draws"):
        _run_compare(registration, ledger, tmp_path / "run2")
    assert send_spy.built == 0 and len(_events(voids, "drawn")) == 1


def test_an_index_void_alone_draws_nothing(tmp_path: Path, voids: Path,
                                           send_spy: type[_SendSpy]) -> None:
    """(−) The two halves are both required. A `void` row written to the index alone (no ledger
    void) leaves the ledger's claim live: the re-draw is refused before any client."""
    registration, ledger, run1, reg = _stopped_claim(tmp_path, voids)
    registry.record_void(reg, approval=registry.approval_id(ledger), root=voids)
    _to_main(voids)
    with pytest.raises(ReplayError, match="already drawn under this approval"):
        _run_compare(registration, ledger, tmp_path / "run2")
    assert send_spy.built == 0


def test_a_void_that_cancels_no_claim_is_refused(tmp_path: Path) -> None:
    """(−) The index's half: a `void` row honoured by `claim_draw` and `_drawn_pins` cancels
    exactly the claim it names. One naming no claim, or a claim voided twice, refuses every
    claim — the index is inconsistent — rather than being passed over. (+) The claim it names is
    cancelled: the registration's pins no longer count as drawn."""
    from tests.test_evals_order8 import _a_comparison, _indexed
    reg = _a_comparison()
    a = "1" * 64
    repo = _indexed(tmp_path, [(reg, a)])
    registry.claim_draw(reg, approval=a, root=repo)
    void = registry.record_void(reg, approval=a, root=repo)
    rows = registry._rows_everywhere(repo)
    assert [r["event"] for r in rows] == ["registered"] and registry._drawn_pins(rows, set()) == {}
    path = repo / registry.INDEX
    good = path.read_text(encoding="utf-8")
    for extra in ({**void, "voids": "2026-01-01T00:00:00Z"},        # names no claim
                  {**void, "voided_at": "2026-12-31T00:00:00Z"}):   # the same claim, twice
        path.write_text(good + json.dumps(extra, sort_keys=True) + "\n", encoding="utf-8")
        with pytest.raises(ReplayError, match="not one claim voided once"):
            registry.claim_draw(reg, approval=a, root=repo)


def test_a_build_registration_s_claim_is_never_voided(tmp_path: Path) -> None:
    """(−) Only a comparison's one claim is voided; a build's unit is not."""
    from tests.test_evals_order8 import _a_build_run, _indexed
    reg = _a_build_run()
    a = "1" * 64
    repo = _indexed(tmp_path, [(reg, a)])
    registry.claim_draw(reg, approval=a, unit="NFLX:1", root=repo)
    with pytest.raises(ReplayError, match="build registration"):
        registry.record_void(reg, approval=a, root=repo)
