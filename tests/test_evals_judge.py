"""The LLM judge at $0: its request is built by production's client from the frozen taxonomy and
the page's facts (never its synthesis); a missing or invalid verdict is never read as OK; kappa and
the per-class table are exact on known codings; and a judged half runs behind the guard and
resumes without paying twice."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from vinci.evals import gold as gd
from vinci.evals import judge as jg
from vinci.evals import replay as rp
from vinci.evals import report

ROOT = Path(__file__).resolve().parents[1]


def _history() -> None:
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{report.GOLD_REF}^{{commit}}"],
                      capture_output=True).returncode != 0:
        pytest.skip("the gold's freeze commit is not in this history")


@pytest.fixture(scope="module")
def gold() -> list[gd.GoldClaim]:
    return gd.load_gold()


def test_the_request_is_the_taxonomy_the_facts_and_the_claims(gold: list[gd.GoldClaim]) -> None:
    _history()
    page = report._frozen_page("TECX", report.GOLD_REF)
    claims = [(g.id, g.text) for g in gold if g.page == "TECX"]
    req = jg.judge_request(page, claims)
    assert req.kwargs == jg.judge_request(page, claims).kwargs          # deterministic
    assert (gd.GOLD_DIR / "TAXONOMY.md").read_text(encoding="utf-8") in req.system
    assert all(f'"id": "{i}"' in req.user for i, _ in claims)
    assert '"synthesis"' not in req.user and '"price_store"' not in req.user
    assert req.kwargs["tool_choice"] == {"type": "tool", "name": jg.JUDGE_TOOL["name"]}
    assert "cache_control" not in req.kwargs                              # one call per page


def test_a_missing_or_invalid_verdict_is_never_ok() -> None:
    raw = {"verdicts": [{"id": "a", "verdict": "OK", "material": True, "favours": "bull",
                         "fact": ""},
                        {"id": "b", "verdict": "NOT-A-CLASS", "material": True,
                         "favours": "bull", "fact": "x"},
                        {"id": "a", "verdict": "LABEL", "material": True, "favours": "bull",
                         "fact": "second answer for a"}]}
    out = jg.parse_verdicts(raw, ["a", "b", "c"])
    a = out["a"]
    assert a is not None and a.verdict == "OK" and a.material is False    # first wins; OK is
    assert out["b"] is None and out["c"] is None                          # never material


def test_kappa_on_known_codings() -> None:
    assert jg.cohen_kappa([True, False, True, False], [True, False, True, False]) == 1.0
    # po 0.5, pa 0.5, pb 0.5 -> pe 0.5 -> kappa 0
    assert jg.cohen_kappa([True, True, False, False], [True, False, True, False]) == 0.0
    with pytest.raises(ValueError):
        jg.cohen_kappa([], [])


def test_the_coders_agreement_reproduces_the_diagnosis(gold: list[gd.GoldClaim]) -> None:
    perfect = {g.id: jg.Verdict(g.id, g.verdict, g.material, g.favours or "neither", "")
               for g in gold}
    c = jg.calibrate(perfect, gold, "test")
    assert round(c.kappa_coders_all, 2) == 0.76 and c.kappa_final == 1.0 and c.missing == 0
    assert all(r.agree == r.gold for r in c.rows)
    assert c.bar()["kappa_ok"]


def test_a_judge_that_says_ok_everywhere_fails_the_bar(gold: list[gd.GoldClaim]) -> None:
    lazy = {g.id: jg.Verdict(g.id, "OK", False, "neither", "") for g in gold}
    c = jg.calibrate(lazy, gold, "test")
    assert c.kappa_final == 0.0 and c.bar() == {"kappa_ok": False, "classes_it_may_gate": []}
    silent = jg.calibrate({}, gold, "test")              # no verdicts: missing, coded error
    assert silent.missing == 314 and not silent.bar()["kappa_ok"]


class _FakeJudge:
    def __init__(self, ids: list[str]) -> None:
        self.ids, self.calls, self.messages = ids, 0, self

    def create(self, **kwargs: Any) -> Any:
        self.calls += 1
        block = SimpleNamespace(type="tool_use", input={"verdicts": [
            {"id": i, "verdict": "OK", "material": False, "favours": "neither", "fact": ""}
            for i in self.ids]})
        usage = SimpleNamespace(input_tokens=60000, output_tokens=2000,
                                cache_creation_input_tokens=0, cache_read_input_tokens=0)
        return SimpleNamespace(usage=usage, content=[block], model="claude-opus-4-8",
                               stop_reason="tool_use")


def test_a_half_is_judged_behind_the_guard_and_resumes_free(tmp_path: Path,
                                                            gold: list[gd.GoldClaim]) -> None:
    _history()
    sub = [g for g in gold if g.page == "TECX"]
    sdk = _FakeJudge([g.id for g in sub])
    ledger = tmp_path / "ledger.jsonl"
    rp.Budget.open(ledger, cap_usd=5.0, approval="operator: test")
    out = tmp_path / "judge"
    judged = jg.run_half("test", budget=rp.Budget.load(ledger), out_dir=out, sdk=sdk, gold=sub)
    assert sdk.calls == 1 and all(v is not None and v.verdict == "OK" for v in judged.values())
    spent = rp.Budget.load(ledger).spent()
    assert spent == pytest.approx((60000 * 5 + 2000 * 25) / 1e6)
    again = jg.run_half("test", budget=rp.Budget.load(ledger), out_dir=out, sdk=sdk, gold=sub)
    assert again == judged and sdk.calls == 1 and rp.Budget.load(ledger).spent() == spent
    with pytest.raises(rp.ReplayError, match="inside the repository"):
        jg.run_half("test", budget=rp.Budget.load(ledger), out_dir=ROOT / "judge-out", sdk=sdk,
                    gold=sub)
    rows = [json.loads(x) for x in (out / "judged.jsonl").read_text().splitlines()]
    assert [r["page"] for r in rows] == ["TECX"]
