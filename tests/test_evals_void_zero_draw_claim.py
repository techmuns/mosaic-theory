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

Round 2 (coordinator A's independent review of #1167; the operator, 2026-11-20: "Yes, take it
over"): an index void is honoured only once its row is ON MAIN; a void is never written while a
run under its approval is in flight (the ledger's lock); a voided folder is never drawn into
again; a void names its claim by the claim's own row, carries the operator's ruling, and is
re-checked on the folder it voided, wherever it is read; and every condition of the void is
pinned (A's mutants M5, M8, M12, M13, M14, M18).

$0: no key, no network. A real Anthropic client is never built (`no_network`); a draw that passes
every refusal reaches `_SendSpy`, which stops it before anything is sent.
"""
from __future__ import annotations

import functools
import hashlib
import json
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from tests.test_evals_order8 import _impact_export, _repo_with_index, _to_main
from tests.test_evals_order8_gaps import _SendSpy, scorer_is_the_fingerprint  # noqa: F401
from tests.test_evals_order8_round2 import (
    _approvals,
    _builds_through_the_cli,
    _register,
    _run_compare,
    index,  # noqa: F401 — the CLI's index fixture
)
from vinci.evals import registry
from vinci.evals.replay import ROOT, ReplayError

#: The operator's words a void records (a test value: the CLI takes them from `--ruling`).
RULING = '"Yes, void it and fix" (operator, 2026-11-20)'


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


def _void_claim(registration: Path, ledger: Path, out_dir: Path, ruling: str = RULING) -> int:
    from vinci.evals import __main__ as cli
    return cli.main(["void-claim", "--registration", str(registration), "--budget-ledger",
                     str(ledger), "--out-dir", str(out_dir), "--ruling", ruling])


def _stopped_claim(tmp_path: Path, repo: Path, run1: Path | None = None
                   ) -> tuple[Path, Path, Path, Any]:
    """REGISTRATION 2f2314b0's STATE, PRODUCED BY THE REAL `run_compare` (A's review of #1167,
    item 5; B's first version wrote the claim row by hand, and `compare._is_claim` matches a
    claim by its exact key set): the registration on main; `run-compare --paid` through the CLI,
    its client built, its draw claimed, and stopped by the send spy at its FIRST send, before
    anything is sent. What it leaves is what 2f2314b0's stop left: its `drawn` row in the
    working index; the ledger's approval line and then the claim, `{"out_dir", "registration",
    "usd": 0.0}`, as its last row; a run folder holding `registration.json` and
    `requests.jsonl` and no `draws.jsonl`. ``run1`` may be relative (item 9)."""
    export, _ = _impact_export(tmp_path)
    ledger, _ = _approvals(tmp_path)
    reg = _register(export, ledger, tmp_path / "r1.json", "--no-worsening")
    _to_main(repo)
    run1 = tmp_path / "run1" if run1 is None else run1
    with pytest.raises(AssertionError, match="a paid client sent a draw"):
        _run_compare(tmp_path / "r1.json", ledger, run1)
    assert _SendSpy.sent == 1   # stopped AT the first send: nothing was sent
    assert [set(r) for r in _rows(ledger)] == [{"approval"}, {"out_dir", "registration", "usd"}]
    assert _rows(ledger)[-1] == {"registration": reg.sha, "out_dir": str(run1), "usd": 0.0}
    assert sorted(p.name for p in run1.iterdir()) == ["registration.json", "requests.jsonl"]
    assert [r["event"] for r in registry.working_rows(repo)] == ["registered", "drawn"]
    _SendSpy.built = _SendSpy.sent = 0
    return tmp_path / "r1.json", ledger, run1, reg


def _drew(run1: Path, ledger: Path) -> None:
    """What `GuardedSdk` leaves after one PRICED draw: its ledger row, then its draws row."""
    from vinci.evals import replay as rp
    row = {"label": "NFLX:BASE", "draw": 1, "usage": {
        "input_tokens": 1, "output_tokens": 1, "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0}, "usd": 0.0123}
    rp.Budget.load(ledger).record(row)
    (run1 / "draws.jsonl").write_text(json.dumps({**row, "raw": {"x": 1}}) + "\n")


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


class _Refused:
    """An injected SDK that answers every call as the API answers a revoked key (401). A key
    out of credit is answered with a 400 the same way: a refused call, never billed."""

    def __init__(self) -> None:
        self.messages = self
        self.calls = 0

    def create(self, **kw: Any) -> Any:
        import anthropic
        import httpx
        self.calls += 1
        req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        raise anthropic.AuthenticationError("invalid x-api-key",
                                            response=httpx.Response(401, request=req), body=None)


def test_a_key_the_api_refuses_is_claimed_and_its_run_is_never_voided(
        tmp_path: Path, no_network: None, scorer_is_the_fingerprint: None) -> None:  # noqa: F811
    """(−) THE LIMIT (i) LEAVES, PINNED AS ACCEPTED (A's review of #1167, item 3; probe P4).
    Building a client reads the key but never sends it, so (i) refuses only an ABSENT key. A key
    that is present but refused — revoked (401), or its account out of credit (400) — is claimed,
    and every draw is sent and refused: each writes its failed draws row, $0 is spent, and the
    run, holding draws, is never voided. No check before the claim is built: it would have to be
    free, and whether the free endpoints (`models`, `count_tokens`) refuse an account out of
    credit was not tested — no real key is run at $0. So the re-draw procedure checks the key FIRST
    (`check_anthropic` in `.github/scripts/validate_keys.py`, one call of one output token on
    claude-opus-4-8, the model the panel's requests name), and `void-claim` prints that step."""
    from tests.test_evals_order8_gaps import _budget, _captured_and_registration
    from vinci.evals import compare as cm
    c, reg = _captured_and_registration()
    budget = _budget(tmp_path)
    sdk = _Refused()
    run1 = tmp_path / "run1"
    cm.run_compare(c, budget=budget, out_dir=run1, registration=reg, sdk=sdk,
                   claim=lambda: None)
    n = len(reg.pages) * len(cm.CONDITIONS) * reg.draws
    assert sdk.calls == n == len(_rows(run1 / "draws.jsonl"))
    assert all(r["raw"] is None and "AuthenticationError" in r["error"]
               for r in _rows(run1 / "draws.jsonl"))
    assert [set(r) for r in budget.rows()] == [{"approval"}, {"out_dir", "registration", "usd"}]
    assert budget.spent() == 0.0
    with pytest.raises(ReplayError, match="holds draws"):
        cm.void_unspent_claim(reg, budget=budget, out_dir=run1)


# --------------------------------------- (ii) a claim that drew nothing is voided, and only it


def test_the_stopped_2f2314_claim_is_voided_and_drawn_again(
        tmp_path: Path, voids: Path, send_spy: type[_SendSpy],
        capsys: pytest.CaptureFixture[str]) -> None:
    """(+) B's pin: the 2f2314b0 shape, left by the real `run_compare`, is voidable. Before the
    void, a re-draw into a fresh folder is refused (the ledger's "already drawn under this
    approval"); `void-claim` writes one `void` row to the index, naming the claim it cancels by
    that claim's own row and carrying the operator's ruling, and one to the ledger, right after
    the claim, naming the folder it voided resolved; it prints the procedure that follows —
    merge to main, check the key, a fresh folder (item 3). Once the void is on main the same
    registration is drawn into a fresh folder — it passes every refusal, is claimed once more,
    and reaches the send."""
    registration, ledger, run1, reg = _stopped_claim(tmp_path, voids)
    with pytest.raises(ReplayError, match="already drawn under this approval"):
        _run_compare(registration, ledger, tmp_path / "run2")
    assert send_spy.built == 0
    capsys.readouterr()
    assert _void_claim(registration, ledger, run1) == 0
    said = capsys.readouterr().out
    assert all(s in said for s in ("to main", "check_anthropic", "fresh folder")), said
    (void,) = _events(voids, "void")
    (claimed,) = _events(voids, "drawn")
    claim_id = hashlib.sha256(json.dumps(claimed, sort_keys=True).encode()).hexdigest()
    assert set(void) == {"event", "registration", "approval", "voids", "claimed_at", "ruling",
                         "voided_at"}
    assert (void["registration"], void["approval"], void["voids"], void["claimed_at"],
            void["ruling"]) == (reg.sha, claimed["approval"], claim_id, claimed["drawn_at"],
                                RULING)
    last = _rows(ledger)[-1]
    assert {k: v for k, v in last.items() if k != "voided_at"} == {
        "void": reg.sha, "out_dir": str(run1), "folder": str(run1.resolve()), "usd": 0.0,
        "ruling": RULING}
    assert last["voided_at"] == void["voided_at"]
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
    void), even on main, leaves the ledger's claim live: the re-draw is refused before any
    client."""
    registration, ledger, run1, reg = _stopped_claim(tmp_path, voids)
    registry.record_void(reg.sha, approval=registry.approval_id(ledger), ruling=RULING,
                         root=voids)
    _to_main(voids)
    with pytest.raises(ReplayError, match="already drawn under this approval"):
        _run_compare(registration, ledger, tmp_path / "run2")
    assert send_spy.built == 0


def test_a_void_that_cancels_no_claim_is_refused(tmp_path: Path) -> None:
    """(−) The index's half: a `void` row honoured by `claim_draw` and `_drawn_pins` cancels
    exactly the claim it names. One on main naming no claim, or a claim voided twice, refuses
    every claim — the index is inconsistent — rather than being passed over. (+) The claim it
    names is cancelled once the void is on main: the registration's pins no longer count as
    drawn."""
    from tests.test_evals_order8 import _a_comparison, _indexed
    reg = _a_comparison()
    a = "1" * 64
    repo = _indexed(tmp_path, [(reg, a)])
    registry.claim_draw(reg, approval=a, root=repo)
    void = registry.record_void(reg.sha, approval=a, ruling=RULING, root=repo)
    _to_main(repo)
    rows = registry._rows_everywhere(repo)
    assert [r["event"] for r in rows] == ["registered"] and registry._drawn_pins(rows, set()) == {}
    path = repo / registry.INDEX
    good = path.read_text(encoding="utf-8")
    for extra in ({**void, "voids": "0" * 64},                       # names no claim
                  {**void, "voided_at": "2026-12-31T00:00:00Z"}):   # the same claim, twice
        path.write_text(good + json.dumps(extra, sort_keys=True) + "\n", encoding="utf-8")
        _to_main(repo)
        with pytest.raises(ReplayError, match="not one claim voided once"):
            registry.claim_draw(reg, approval=a, root=repo)


def test_a_build_registration_s_claim_is_never_voided(tmp_path: Path) -> None:
    """(−) Only a comparison's one claim is voided; a build's unit is not. Read off the index's
    own `registered` row (round 2: `record_void` takes the sha, and the kind is the index's)."""
    from tests.test_evals_order8 import _a_build_run, _indexed
    reg = _a_build_run()
    a = "1" * 64
    repo = _indexed(tmp_path, [(reg, a)])
    registry.claim_draw(reg, approval=a, unit="NFLX:1", root=repo)
    with pytest.raises(ReplayError, match="build registration"):
        registry.record_void(reg.sha, approval=a, ruling=RULING, root=repo)
    assert _events(repo, "void") == []


# ---------------------- round 2 (A's review of #1167): the void, honoured only once on main


#: Registration 2f2314b0 as main's index holds it (line 11), and the `drawn` row the stopped run
#: left uncommitted in the operator's scratch checkout, as bbbd3d4b's `claim_draw` wrote it.
REAL_SHA = "2f2314b07ebf7402332534c96505ed1fb4d8844ac3dd175141657532b6ed64b0"
REAL_APPROVAL = "1d6fdd4eddba28a7ebb76aea9ad03a83c7d9e07aa532666f1ab8ecd1efc54da6"
REAL_DRAWN = {"approval": REAL_APPROVAL, "drawn_at": "2026-11-20T12:55:17Z", "event": "drawn",
              "registration": REAL_SHA, "unit": None}


def test_the_real_2f2314_row_is_voided_by_its_claim_and_only_once_the_void_is_on_main(
        tmp_path: Path) -> None:
    """A's review of #1167, item 5: the index half on the REAL registered row, read from this
    checkout's committed index, not a synthetic one. A repository whose main holds that row
    byte for byte, and whose working copy adds the `drawn` row the stopped run left. (−) Before
    the void, all 12 of its request pins count as drawn, so no registration pinning them is
    drawn. (−) A void under another approval is refused (A's mutant M8). (+) `record_void` under
    its own approval, 1d6fdd4e, names that claim by its row, stamps its `drawn_at`
    12:55:17Z, carries the ruling and no path (the repository is public). (−) While the void
    is in this checkout only, it cancels nothing (item 1a), and a second void is refused.
    (+) On main, the claim is cancelled: the 12 pins no longer count as drawn."""
    lines = [x for x in registry.main_rows(ROOT, "HEAD") if x.get("registration") == REAL_SHA]
    assert [r["event"] for r in lines] == ["registered"]
    (real,) = lines
    assert (real["approval"], real["kind"], len(real["pins"])) == (REAL_APPROVAL, "compare", 12)
    repo = _repo_with_index(tmp_path, [])
    (repo / registry.INDEX).write_text(json.dumps(real, sort_keys=True) + "\n", encoding="utf-8")
    _to_main(repo)
    with (repo / registry.INDEX).open("a", encoding="utf-8") as f:
        f.write(json.dumps(REAL_DRAWN, sort_keys=True) + "\n")
    drawn = registry._drawn_pins(registry._rows_everywhere(repo), set())
    assert drawn == dict.fromkeys(real["pins"].values(), REAL_SHA)
    before = (repo / registry.INDEX).read_bytes()
    with pytest.raises(ReplayError, match="claimed under approval"):
        registry.record_void(REAL_SHA, approval="2" * 64, ruling=RULING, root=repo)
    assert (repo / registry.INDEX).read_bytes() == before
    void = registry.record_void(REAL_SHA, approval=REAL_APPROVAL, ruling=RULING, root=repo)
    assert {k: v for k, v in void.items() if k != "voided_at"} == {
        "event": "void", "registration": REAL_SHA, "approval": REAL_APPROVAL,
        "voids": hashlib.sha256(json.dumps(REAL_DRAWN, sort_keys=True).encode()).hexdigest(),
        "claimed_at": "2026-11-20T12:55:17Z", "ruling": RULING}
    assert not any("/" in str(v) for k, v in void.items() if k != "ruling")
    assert registry._drawn_pins(registry._rows_everywhere(repo), set()) == drawn
    with pytest.raises(ReplayError, match="already voided"):
        registry.record_void(REAL_SHA, approval=REAL_APPROVAL, ruling=RULING, root=repo)
    _to_main(repo)
    rows = registry._rows_everywhere(repo)
    assert [r["event"] for r in rows] == ["registered"]
    assert registry._drawn_pins(rows, set()) == {}


def _index_void_over_a_run_that_drew(tmp_path: Path, repo: Path) -> tuple[Path, Path]:
    """A's probe P3: a run that DREW — its `drawn` row committed on main, a priced call in its
    ledger and its folder — and then, in this checkout only, an index void of its claim written
    outside `void-claim` (whose ledger half refuses it), and a fresh ledger file holding the
    approval's first line byte for byte, so the same approval with no claim recorded."""
    registration, ledger, run1, reg = _stopped_claim(tmp_path, repo)
    _drew(run1, ledger)
    _to_main(repo)
    registry.record_void(reg.sha, approval=registry.approval_id(ledger), ruling=RULING,
                         root=repo)
    copied = tmp_path / "copied-ledger.jsonl"
    copied.write_text(ledger.read_text(encoding="utf-8").splitlines(keepends=True)[0])
    assert registry.approval_id(copied) == registry.approval_id(ledger)
    return registration, copied


def _cli_void_not_yet_merged(tmp_path: Path, repo: Path) -> tuple[Path, Path]:
    """A's probe P2: the CLI's own void of a stopped claim, its index row not yet on main."""
    registration, ledger, run1, _ = _stopped_claim(tmp_path, repo)
    assert _void_claim(registration, ledger, run1) == 0
    return registration, ledger


@pytest.mark.parametrize("state", [_index_void_over_a_run_that_drew, _cli_void_not_yet_merged],
                         ids=["an index void over a run that drew", "the CLI's void, unmerged"])
def test_a_void_only_in_this_checkout_re_opens_nothing(
        tmp_path: Path, voids: Path, send_spy: type[_SendSpy], state: Any) -> None:
    """(−) A's review of #1167, item 1a, the BLOCKER (probes P2 and P3). `_live` read the working
    copy and main alike, so a void row in this checkout alone — uncommitted, unreviewed — took
    a claim out of the index, and the ledger's half is one approval's file outside the
    repository. On 3fbd246b both reach the send: a registration that DREW, its `drawn` row on
    main, re-drawn under a copied ledger; and a stopped claim re-drawn before its void was
    merged. An index void is honoured now only once its row is ON MAIN, as a registration is
    drawn only once its row is (RG-D14): both are refused at the claim, before any send and
    with no run folder written."""
    registration, ledger = state(tmp_path, voids)
    with pytest.raises(ReplayError, match=r"already drawn \(at"):
        _run_compare(registration, ledger, tmp_path / "run2")
    assert send_spy.sent == 0 and not (tmp_path / "run2").exists()


class _VoidsInFlight(_SendSpy):
    """The send spy, which at its first send — the run's lock held, its claim written, its call
    about to leave — runs `void-claim` on that run, keeps what it answered, and stops."""
    args: tuple[Path, Path, Path] | None = None
    answered: object = None

    def extract(self, **k: Any) -> Any:
        assert _VoidsInFlight.args is not None
        try:
            _VoidsInFlight.answered = _void_claim(*_VoidsInFlight.args)
        except ReplayError as exc:
            _VoidsInFlight.answered = exc
        return super().extract(**k)


def test_a_void_while_its_run_is_in_flight_is_refused(
        tmp_path: Path, voids: Path, send_spy: type[_SendSpy],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) A's review of #1167, item 1b (probe P6; B's round-0 DEFER #2). `void-claim` read the
    ledger unlocked, and `run_compare` held no lock, so a void written while the run's first
    call was in flight was accepted: the call then completed, approval 1's ledger refused, and
    a twin of the DRAWN design under approval 2 reached the send. `run_compare` now holds the
    ledger's lock (`builds._claim`, non-blocking) for the whole run, and `void-claim` takes it:
    the void is refused with nothing written. (+) Once the run has stopped, with nothing
    recorded after its claim, the same void is accepted — the lock was the refusal."""
    from vinci.evals import replay as rp
    export, _ = _impact_export(tmp_path)
    ledger, _ = _approvals(tmp_path)
    _register(export, ledger, tmp_path / "r1.json", "--no-worsening")
    _to_main(voids)
    run1 = tmp_path / "run1"
    _VoidsInFlight.args, _VoidsInFlight.answered = (tmp_path / "r1.json", ledger, run1), None
    monkeypatch.setattr(rp, "AnthropicLlmClient", _VoidsInFlight)
    with pytest.raises(AssertionError, match="a paid client sent a draw"):
        _run_compare(tmp_path / "r1.json", ledger, run1)
    assert isinstance(_VoidsInFlight.answered, ReplayError), _VoidsInFlight.answered
    assert "another run holds" in str(_VoidsInFlight.answered)
    assert _events(voids, "void") == [] and not any("void" in r for r in _rows(ledger))
    assert _void_claim(tmp_path / "r1.json", ledger, run1) == 0


def test_a_re_draw_into_the_voided_folder_is_refused(
        tmp_path: Path, voids: Path, send_spy: type[_SendSpy]) -> None:
    """(−) A's review of #1167, item 2 (probe P1). The folder check read only `draws.jsonl`, so
    after the void the failed command re-run into the SAME folder passed: claimed, and drawing
    into the voided folder, after which every read of the approval's ledger refuses ("now holds
    draws") and the approval is stranded. A folder that already holds a run's
    `registration.json` is refused before any client, claim or write. (+) A fresh folder is
    drawn."""
    registration, ledger, run1, _ = _stopped_claim(tmp_path, voids)
    assert _void_claim(registration, ledger, run1) == 0
    _to_main(voids)
    before = ledger.read_bytes()
    with pytest.raises(ReplayError, match="registration.json.*fresh folder"):
        _run_compare(registration, ledger, run1)
    assert (send_spy.built, send_spy.sent) == (0, 0) and ledger.read_bytes() == before
    assert len(_events(voids, "drawn")) == 1 and not (run1 / "draws.jsonl").exists()
    with pytest.raises(AssertionError, match="a paid client sent a draw"):
        _run_compare(registration, ledger, tmp_path / "run2")


def _between(ledger: Path) -> None:
    """A priced call recorded BETWEEN the claim and its void (the race item 1b closes, or a hand
    edit); no draws file is written, so only the row order tells."""
    lines = ledger.read_text(encoding="utf-8").splitlines(keepends=True)
    call = json.dumps({"label": "NFLX:BASE", "draw": 1, "usd": 0.0123, "usage": {}},
                      sort_keys=True) + "\n"
    ledger.write_text("".join(lines[:-1]) + call + lines[-1])


def _claim_not_zero(ledger: Path) -> None:
    """The voided claim rewritten as not $0.00 (the approval line kept byte for byte)."""
    lines = ledger.read_text(encoding="utf-8").splitlines(keepends=True)
    claim = {**json.loads(lines[-2]), "usd": 0.5}
    ledger.write_text("".join(lines[:-2]) + json.dumps(claim, sort_keys=True) + "\n" + lines[-1])


@pytest.mark.parametrize(("edit", "refusal"), [
    (_between, r"does not directly follow a \$0\.00 claim"),          # A's mutant M5
    (_claim_not_zero, r"does not directly follow a \$0\.00 claim"),   # A's mutant M12
], ids=["a row between the claim and its void", "the claim not $0.00"])
def test_a_ledger_void_that_no_longer_follows_a_zero_claim_is_refused_when_read(
        tmp_path: Path, voids: Path, send_spy: type[_SendSpy], edit: Any,
        refusal: str) -> None:
    """(−) A's review of #1167, item 4 (mutants M5 and M12 passed all 62 tests). A ledger void
    is honoured only while its row DIRECTLY follows a claim of that run that recorded $0.00. A
    priced call recorded between them, or the claim rewritten as spent, refuses the re-draw
    when the ledger is read, before any client, though the index void is on main."""
    registration, ledger, run1, _ = _stopped_claim(tmp_path, voids)
    assert _void_claim(registration, ledger, run1) == 0
    _to_main(voids)
    edit(ledger)
    with pytest.raises(ReplayError, match=refusal):
        _run_compare(registration, ledger, tmp_path / "run2")
    assert send_spy.built == 0


def test_a_void_names_the_folder_its_claim_wrote(
        tmp_path: Path, voids: Path, send_spy: type[_SendSpy]) -> None:
    """(−) A's review of #1167, item 4 (mutant M13). `void-claim --out-dir` must be the folder
    the claim wrote: otherwise its draws and registration checks read another folder. Here the
    claimed folder holds a failed draw and a clean copy elsewhere is named: refused, nothing
    written."""
    registration, ledger, run1, _ = _stopped_claim(tmp_path, voids)
    _a_failed_call(run1, ledger)
    other = tmp_path / "other"
    other.mkdir()
    shutil.copy(run1 / "registration.json", other / "registration.json")
    before = ledger.read_bytes()
    with pytest.raises(ReplayError, match="not one into"):
        _void_claim(registration, ledger, other)
    assert _events(voids, "void") == [] and ledger.read_bytes() == before


def _another_registration(run1: Path, tmp_path: Path) -> None:
    """The claimed folder's `registration.json` replaced by another registration's."""
    l2 = tmp_path / "approval-2.jsonl"
    other = _register(tmp_path / "export", l2, tmp_path / "r2.json", "--no-worsening",
                      "--note", "other words")
    (run1 / "registration.json").write_text(other.to_json(), encoding="utf-8")


def _no_registration(run1: Path, tmp_path: Path) -> None:
    (run1 / "registration.json").unlink()


@pytest.mark.parametrize(("change", "refusal"), [
    (_another_registration, "does not hold registration"),
    (_no_registration, "no registration.json"),
], ids=["another registration", "none"])
def test_a_void_needs_its_folder_to_hold_its_registration(
        tmp_path: Path, voids: Path, send_spy: type[_SendSpy], change: Any,
        refusal: str) -> None:
    """(−) A's review of #1167, item 4 (mutant M14). The folder voided must hold the voided
    registration's own `registration.json`: one holding another registration's, or none, is
    refused, nothing written."""
    registration, ledger, run1, _ = _stopped_claim(tmp_path, voids)
    change(run1, tmp_path)
    before = ledger.read_bytes()
    with pytest.raises(ReplayError, match=refusal):
        _void_claim(registration, ledger, run1)
    assert _events(voids, "void") == [] and ledger.read_bytes() == before


def test_a_void_needs_exactly_one_live_claim_of_its_registration(tmp_path: Path) -> None:
    """(−) A's review of #1167, item 4 (mutant M18). The index half voids a comparison's ONE live
    claim: none, or two (another checkout's claim beside this one's), is refused, nothing
    written."""
    from tests.test_evals_order8 import _a_comparison, _indexed
    reg, a = _a_comparison(), "1" * 64
    repo = _indexed(tmp_path, [(reg, a)])
    with pytest.raises(ReplayError, match="0 live claim"):
        registry.record_void(reg.sha, approval=a, ruling=RULING, root=repo)
    registry.claim_draw(reg, approval=a, root=repo)
    with (repo / registry.INDEX).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"event": "drawn", "registration": reg.sha, "approval": a,
                            "unit": None, "drawn_at": "2026-11-21T00:00:00Z"},
                           sort_keys=True) + "\n")
    with pytest.raises(ReplayError, match="2 live claim"):
        registry.record_void(reg.sha, approval=a, ruling=RULING, root=repo)
    assert _events(repo, "void") == []


def test_a_re_claim_in_the_voided_claim_s_second_stays_live(tmp_path: Path) -> None:
    """(−) A's review of #1167, item 7 (probe P7). A void named its claim by ``drawn_at``, to the
    second, and the index merges byte-identical rows: a re-claim in the same second as the
    voided claim was the same row, so the void erased it too, and a THIRD claim was accepted.
    A claim now carries its own id, and a void names its claim by that claim's row: the
    re-claim stays live, and a third is refused."""
    from tests.test_evals_order8 import _a_comparison, _indexed
    reg, a = _a_comparison(), "1" * 64
    repo = _indexed(tmp_path, [(reg, a)])
    with mock.patch.object(registry, "_now", return_value="2026-11-20T12:55:17Z"):
        registry.claim_draw(reg, approval=a, root=repo)
        registry.record_void(reg.sha, approval=a, ruling=RULING, root=repo)
        _to_main(repo)
        registry.claim_draw(reg, approval=a, root=repo)   # the same second
        with pytest.raises(ReplayError, match="already drawn"):
            registry.claim_draw(reg, approval=a, root=repo)
    assert len(_events(repo, "drawn")) == 2


def test_a_void_without_the_operator_s_words_is_refused(
        tmp_path: Path, voids: Path, send_spy: type[_SendSpy]) -> None:
    """(−) A's review of #1167, item 8: a void records who ruled it and why — the operator's
    words (`--ruling`) and when, in both rows. Without the words it is refused, nothing
    written."""
    registration, ledger, run1, _ = _stopped_claim(tmp_path, voids)
    before = ledger.read_bytes()
    with pytest.raises(ReplayError, match="operator's words"):
        _void_claim(registration, ledger, run1, ruling="  ")
    assert _events(voids, "void") == [] and ledger.read_bytes() == before


def _draws_written_later(run1: Path) -> None:
    _a_failed_call(run1, run1)


def _folder_moved(run1: Path) -> None:
    run1.rename(run1.with_name("run1-moved"))


@pytest.mark.parametrize(("after", "refusal"), [
    (_draws_written_later, "now holds draws"),
    (_folder_moved, "no longer holds"),
], ids=["draws written into it later", "the folder moved"])
def test_a_void_is_re_checked_on_the_folder_it_voided_wherever_it_is_read(
        tmp_path: Path, voids: Path, send_spy: type[_SendSpy],
        monkeypatch: pytest.MonkeyPatch, after: Any, refusal: str) -> None:
    """(−) A's review of #1167, item 9. The read-time check looked for `draws.jsonl` under the
    path the claim recorded, so a run drawn into a RELATIVE folder and read from another
    directory, or a voided folder moved, passed vacuously: a file that is not there was read as
    no draws. The void now records the folder resolved, and is honoured only while that folder
    holds the voided registration and no draws: here the run is drawn into ``run1`` from
    ``tmp_path`` and the ledger read from elsewhere."""
    monkeypatch.chdir(tmp_path)
    registration, ledger, run1, _ = _stopped_claim(tmp_path, voids, run1=Path("run1"))
    assert _void_claim(registration, ledger, Path("run1")) == 0
    _to_main(voids)
    after(tmp_path / "run1")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    with pytest.raises(ReplayError, match=refusal):
        _run_compare(registration, ledger, tmp_path / "run2")
    assert send_spy.built == 0
