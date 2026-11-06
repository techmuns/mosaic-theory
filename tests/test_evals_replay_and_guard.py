"""The eval harness's $0 replay, log parser and paid-draw guard — all exercised at $0.

The replay is production's own request (`synthesize` → `AnthropicLlmClient`, only the SDK object
swapped); the guard is shown refusing BEFORE forwarding — a request that differs from the one
captured at $0, a draw whose worst case would cross the cap — and recording each call at
production's `cost_usd`. A fake SDK object stands in for the network; nothing is sent.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from vinci.dossier.synthesis import synthesize, system_for
from vinci.evals import capture_child as cc
from vinci.evals import replay as rp
from vinci.graph.llm import LlmClient, cost_usd

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def nflx() -> dict[str, Any]:
    page: dict[str, Any] = json.loads((ROOT / "data/dossiers/NFLX/dossier.json").read_text())
    return page


# ------------------------------------------------------------------------------- the capture

def test_capture_is_productions_request_and_sends_nothing(nflx: dict[str, Any]) -> None:
    req = rp.capture(nflx, None, draws=5)
    assert req.system == system_for(nflx["sleeve"])
    assert req.user.startswith(f"Name: {nflx['name']} (NFLX).")
    assert req.model == "claude-opus-4-8" and req.max_tokens == 16384
    assert req.kwargs["cache_control"] == {"type": "ephemeral"}   # a multi-draw build caches
    assert not {"temperature", "top_p", "top_k"} & set(req.kwargs)


def test_pre_synthesis_layer_undoes_the_post_synthesis_attachments(nflx: dict[str, Any]) -> None:
    mech = cc.pre_synthesis_mech(nflx)
    assert mech.ev_gap is None
    assert mech.capital_structure is None or mech.capital_structure.covenant_term_rows is None
    fs = mech.financial_summary
    assert fs is not None and fs.annual is not None and fs.annual.value is not None
    assert any(r.material for r in fs.annual.value.rows)         # #865 on: marks were read
    cleared = cc.pre_synthesis_mech(nflx, unmark_material=True)
    assert cleared.financial_summary is not None
    ann = cleared.financial_summary.annual
    assert ann is not None and ann.value is not None
    assert not any(r.material for r in ann.value.rows)            # before #865: never read


def test_capture_at_a_ref_runs_that_refs_code_and_matches_in_process(nflx: dict[str, Any]) -> None:
    """The child-process path, at HEAD, against the in-process capture — byte for byte. (At an
    older ref it proved the eight saved build logs; those logs hold licensed transcripts and stay
    out of the repository.)"""
    here = rp.capture(nflx, None)
    there = rp.capture_at("HEAD", nflx, None)
    assert there.kwargs == here.kwargs


def test_the_child_refuses_a_vinci_it_was_not_pointed_at(tmp_path: Path,
                                                         nflx: dict[str, Any]) -> None:
    (tmp_path / "page.json").write_text(json.dumps(nflx), encoding="utf-8")
    code = cc.main(["--page", str(tmp_path / "page.json"), "--out", str(tmp_path / "o.json"),
                   "--expect-root", str(tmp_path)])
    assert code == 2 and not (tmp_path / "o.json").exists()


# ------------------------------------------------------------------------ the log and the proof

class _FakeLlm(LlmClient):
    """Returns a fixed raw output and a usage record, so `synthesize` writes a real log."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self.raw = raw
        self.last_usage = {"input_tokens": 24, "output_tokens": 900, "max_tokens": 16384,
                           "cache_creation_input_tokens": 0, "cache_read_input_tokens": 1000}

    @property
    def model(self) -> str:
        return "claude-opus-4-8"

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        return self.raw


def test_parse_log_reads_productions_own_log_and_the_proof_is_exact(nflx: dict[str, Any]) -> None:
    raw = {"evidence_balance": "mixed — a test"}   # incomplete on purpose: still logged
    _s, _f, log = synthesize(cc.pre_synthesis_mech(nflx), llm=_FakeLlm(raw), ticker="NFLX",
                             name=nflx["name"], transcript=None, sleeve=nflx["sleeve"], draws=5)
    parsed = rp.parse_log("=== TIER-B DRIVER EXTRACT: NFLX ===\n...\n\n" + log)
    assert [d.status for d in parsed.draws] == ["incomplete"] * 5
    assert all(d.raw == raw for d in parsed.draws)
    proof = rp.prove(rp.capture(nflx, None), parsed)
    assert proof.identical and all(f.diff_lines == 0 for f in proof.fields)
    tampered = rp.LoggedBuild(parsed.model, parsed.sleeve, parsed.system,
                             parsed.user.replace("Name:", "Name :", 1), parsed.draws, None)
    bad = rp.prove(rp.capture(nflx, None), tampered)
    assert not bad.identical and bad.fields[1].first_difference == 4


# ------------------------------------------------------------------------------- the inputs

def test_a_changed_transcript_is_refused(tmp_path: Path) -> None:
    folder = tmp_path / "ACME"
    folder.mkdir()
    f = folder / "Acme Inc., Q3 2026 Earnings Call, Oct 20, 2026.rtf"
    f.write_text("{\\rtf1\\ansi Prepared remarks. Revenue grew.}", encoding="utf-8")
    import hashlib
    good = [{"file": f.name, "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}]
    assert "Revenue grew" in (rp.transcript_for("ACME", ciq_root=tmp_path, expected=good) or "")
    with pytest.raises(rp.ReplayError, match="differ from the panel"):
        rp.transcript_for("ACME", ciq_root=tmp_path, expected=[{**good[0], "sha256": "0" * 64}])


def test_a_page_blob_other_than_the_frozen_one_is_refused() -> None:
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()
    with pytest.raises(rp.ReplayError, match="the panel froze"):
        rp.page_at("NFLX", head, expect_blob="0" * 40)


# ------------------------------------------------------------------------------- the guard

class _FakeSdk:
    """The SDK object: counts calls and answers like `messages.create`."""

    def __init__(self, served: str = "claude-opus-4-8") -> None:
        self.calls = 0
        self.messages = self
        self.served = served

    def create(self, **kwargs: Any) -> Any:
        self.calls += 1
        usage = SimpleNamespace(input_tokens=24, output_tokens=7000,
                                cache_creation_input_tokens=190000 if self.calls == 1 else 0,
                                cache_read_input_tokens=0 if self.calls == 1 else 190000)
        block = SimpleNamespace(type="tool_use", input={"evidence_balance": "mixed — fake"})
        return SimpleNamespace(usage=usage, content=[block], model=self.served,
                               stop_reason="tool_use")


def test_paid_draws_are_priced_by_production_and_ledgered(tmp_path: Path,
                                                          nflx: dict[str, Any]) -> None:
    sdk = _FakeSdk()
    budget = rp.Budget(cap_usd=20.0, ledger=tmp_path / "ledger.jsonl")
    rp.run_paid(nflx, None, budget=budget, label="t", draws_out=tmp_path / "d.jsonl", sdk=sdk)
    rows = [json.loads(x) for x in (tmp_path / "ledger.jsonl").read_text().splitlines()]
    assert sdk.calls == 5 and len(rows) == 5
    want = sum(cost_usd("claude-opus-4-8", {**r["usage"], "max_tokens": 16384}) or 0
               for r in rows)
    assert budget.spent() == pytest.approx(want, abs=1e-5)


def test_the_cap_refuses_before_forwarding_and_synthesize_cannot_swallow_it(
        tmp_path: Path, nflx: dict[str, Any]) -> None:
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps({"usd": 18.5}) + "\n", encoding="utf-8")
    sdk = _FakeSdk()
    with pytest.raises(rp.BudgetStop, match="would cross the \\$20.00 cap"):
        rp.run_paid(nflx, None, budget=rp.Budget(cap_usd=20.0, ledger=ledger), label="t",
                   draws_out=tmp_path / "d.jsonl", sdk=sdk)
    assert sdk.calls == 0


def test_a_request_other_than_the_captured_one_is_refused(tmp_path: Path,
                                                          nflx: dict[str, Any]) -> None:
    mck = json.loads((ROOT / "data/dossiers/MCK/dossier.json").read_text())
    sdk = _FakeSdk()
    guard = rp.GuardedSdk(sdk, rp.capture(mck, None), rp.Budget(20.0, tmp_path / "l.jsonl"),
                         label="t", draws_out=tmp_path / "d.jsonl")
    with pytest.raises(rp.BudgetStop, match="differs from the one captured"):
        guard.create(**rp.capture(nflx, None).kwargs)
    assert sdk.calls == 0


def test_a_draw_served_by_another_model_stops_the_run(tmp_path: Path,
                                                      nflx: dict[str, Any]) -> None:
    sdk = _FakeSdk(served="claude-opus-5")
    with pytest.raises(rp.BudgetStop, match="served by 'claude-opus-5'"):
        rp.run_paid(nflx, None, budget=rp.Budget(20.0, tmp_path / "l.jsonl"), label="t",
                   draws_out=tmp_path / "d.jsonl", sdk=sdk)
    assert sdk.calls == 1 and len((tmp_path / "l.jsonl").read_text().splitlines()) == 1


def test_the_ledger_and_raw_draws_never_land_in_the_repository(tmp_path: Path,
                                                              nflx: dict[str, Any]) -> None:
    with pytest.raises(rp.ReplayError, match="inside the repository"):
        rp.Budget(cap_usd=1.0, ledger=ROOT / "data" / "ledger.jsonl")
    with pytest.raises(rp.ReplayError, match="inside the repository"):
        rp.GuardedSdk(_FakeSdk(), rp.capture(nflx, None), rp.Budget(1.0, tmp_path / "l.jsonl"),
                     label="t", draws_out=ROOT / "draws.jsonl")


def test_the_worst_case_has_no_guessed_price() -> None:
    assert rp.worst_case_usd("claude-opus-4-8", 192_000, 16_384) == pytest.approx(1.6096)
    with pytest.raises(rp.ReplayError, match="no list price"):
        rp.worst_case_usd("claude-unpriced", 1, 1)
