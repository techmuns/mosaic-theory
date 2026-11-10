"""#925 review round 2 (the coordinator's): ONE registration is drawn ONCE, on the request bytes it
pins, and a score reports every run under its sha; a no-worsening-only comparison can be
registered where no target can fire, and a panel page is never chosen (so none is dropped); the
judge's bar is conjunctive; a judge folder holds one judge's run and TEST is read once per
approval; a capture's draws are compared in order. Every test here failed on a946e82d (the last
one, a pin with no bug behind it, fails on the order-blind mutant instead).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tests.pre_strip import pre_strip_text
from vinci.evals import compare as cm
from vinci.evals import gold as gd
from vinci.evals import judge as jg
from vinci.evals import replay as rp
from vinci.evals import report

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def nflx() -> dict[str, Any]:
    page: dict[str, Any] = json.loads(pre_strip_text("NFLX"))
    return page


@pytest.fixture(scope="module")
def gold() -> list[gd.GoldClaim]:
    return gd.load_gold()


class _FakeSdk:
    def __init__(self) -> None:
        self.calls = 0
        self.messages = self

    def create(self, **kwargs: Any) -> Any:
        self.calls += 1
        usage = SimpleNamespace(input_tokens=10, output_tokens=10,
                                cache_creation_input_tokens=0, cache_read_input_tokens=0)
        block = SimpleNamespace(type="tool_use", input={"evidence_balance": "mixed — fake"})
        return SimpleNamespace(usage=usage, content=[block], model="claude-opus-4-8",
                               stop_reason="tool_use")


def _captured(nflx: dict[str, Any], *, reorder_cand: bool = False) -> cm.Captured:
    base = rp.capture(nflx, None)
    kw = json.loads(json.dumps({**base.kwargs, "system": base.system + " "}))
    if reorder_cand:   # the same request with the tool schema's fields in another order
        props = kw["tools"][0]["input_schema"]["properties"]
        kw["tools"][0]["input_schema"]["properties"] = dict(reversed(list(props.items())))
    c = cm.Captured("A", "B", ())
    c.requests[("NFLX", "BASE")], c.requests[("NFLX", "CAND")] = base, rp.Request(kw)
    c.diffs.append(cm.PageDiff("NFLX", False, 0, False, {}, {}))
    return c


def _reg(c: cm.Captured | None = None, **over: Any) -> cm.Registration:
    base: dict[str, Any] = {"base_ref": "A", "cand_ref": "B", "transforms": (), "pages": ("NFLX",),
                            "draws": 5, "targets": ("M-LABEL",), "held_out": (),
                            "scorer": cm.scorer_fingerprint(),
                            "requests": cm.request_pins(c) if c is not None else {}}
    return cm.Registration(**{**base, **over})


def _budget(tmp_path: Path, *rows: dict[str, Any]) -> rp.Budget:
    ledger = tmp_path / "ledger.jsonl"
    b = rp.Budget.open(ledger, cap_usd=5.0, approval="operator: test")
    for r in rows:
        b.record(r)
    return rp.Budget.load(ledger)


# --------------------------------------------------- 1. one registration, drawn once, pinned

def test_a_registration_the_ledger_already_records_is_never_drawn_again(
        tmp_path: Path, nflx: dict[str, Any]) -> None:
    """Ledger (a) row 73: ed155786 recorded a second time, for a second out-dir, after its run had
    completed 10/10 — only a kill stopped the re-draw."""
    c = _captured(nflx)
    reg = _reg(c)
    budget = _budget(tmp_path, {"registration": reg.sha, "out_dir": str(tmp_path / "first"),
                                "usd": 0.0})
    sdk = _FakeSdk()
    with pytest.raises(rp.ReplayError, match="drawn ONCE"):
        cm.run_compare(c, budget=budget, out_dir=tmp_path / "second", registration=reg, sdk=sdk)
    assert sdk.calls == 0 and not (tmp_path / "second").exists()


def test_a_capture_whose_bytes_differ_from_the_registered_ones_is_refused(
        tmp_path: Path, nflx: dict[str, Any]) -> None:
    """The NFLX re-draw's requests sent `bull_points` first under the sha that had registered the
    alphabetised ones — equal as dicts, different bytes, one sha."""
    reg = _reg(_captured(nflx))
    moved = _captured(nflx, reorder_cand=True)
    assert moved.requests[("NFLX", "CAND")].kwargs == _captured(nflx).requests[
        ("NFLX", "CAND")].kwargs                                     # equal as dicts
    sdk = _FakeSdk()
    with pytest.raises(rp.ReplayError, match=r"not the registered bytes \(\['NFLX:CAND'\]"):
        cm.run_compare(moved, budget=_budget(tmp_path), out_dir=tmp_path / "run",
                       registration=reg, sdk=sdk)
    assert sdk.calls == 0


def test_a_registration_without_pinned_bytes_is_never_drawn(tmp_path: Path,
                                                            nflx: dict[str, Any]) -> None:
    sdk = _FakeSdk()
    with pytest.raises(rp.ReplayError, match="pins no request bytes"):
        cm.run_compare(_captured(nflx), budget=_budget(tmp_path), out_dir=tmp_path / "run",
                       registration=_reg(), sdk=sdk)
    assert sdk.calls == 0


def test_a_pinned_registration_is_drawn_and_recorded_once(tmp_path: Path,
                                                          nflx: dict[str, Any]) -> None:
    """The positive pin: the registered bytes are drawn, the sha lands in the ledger, and the
    same registration into a fresh folder is then refused."""
    c = _captured(nflx)
    reg = _reg(c, draws=2)
    budget = _budget(tmp_path)
    sdk = _FakeSdk()
    cm.run_compare(c, budget=budget, out_dir=tmp_path / "run", registration=reg, sdk=sdk)
    assert sdk.calls == 4
    assert [r["out_dir"] for r in budget.rows() if r.get("registration") == reg.sha] == [
        str(tmp_path / "run")]
    with pytest.raises(rp.ReplayError, match="drawn ONCE"):
        cm.run_compare(c, budget=budget, out_dir=tmp_path / "again", registration=reg, sdk=sdk)


def _run_dir(path: Path, reg: cm.Registration, raw: dict[str, Any], n: int = 5) -> Path:
    path.mkdir()
    (path / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    with (path / "draws.jsonl").open("w") as f:
        for cond in cm.CONDITIONS:
            for _ in range(n):
                f.write(json.dumps({"label": f"NFLX:{cond}", "raw": raw,
                                    "stop_reason": "tool_use"}) + "\n")
    return path


def test_score_reports_every_run_under_its_sha_and_refuses_two_with_draws(
        tmp_path: Path, nflx: dict[str, Any]) -> None:
    reg = _reg()
    one = _run_dir(tmp_path / "one", reg, nflx["synthesis"])
    empty = tmp_path / "stopped"          # registered, killed before its first call
    budget = _budget(tmp_path, {"registration": reg.sha, "out_dir": str(one), "usd": 0.0},
                     {"registration": reg.sha, "out_dir": str(empty), "usd": 0.0})
    s = cm.score_run(one, reg, pages={"NFLX": nflx}, ledger=budget.ledger)
    assert s.runs == ((str(one), 10), (str(empty), 0))
    assert f"{empty} (0 draws)" in cm.score_text(s)
    two = _run_dir(tmp_path / "two", reg, nflx["synthesis"])
    budget.record({"registration": reg.sha, "out_dir": str(two), "usd": 0.0})
    with pytest.raises(rp.ReplayError, match="drawn more than once"):
        cm.score_run(one, reg, pages={"NFLX": nflx}, ledger=budget.ledger)
    stray = _run_dir(tmp_path / "stray", reg, nflx["synthesis"])
    with pytest.raises(rp.ReplayError, match="not a run the ledger records"):
        cm.score_run(stray, reg, pages={"NFLX": nflx}, ledger=budget.ledger)


def test_a_registration_written_before_the_new_fields_keeps_its_sha() -> None:
    """#921's NFLX registration as written on 2026-11-06 (its file is outside the repository; its
    fields are the record's §1) — the ledger records this sha, so a later field must not move
    it."""
    reg = cm.Registration.from_json(json.dumps({
        "alpha": 0.05, "base_ref": "dc5b8787", "cand_ref": "b109e26c", "draws": 5,
        "held_out": [], "pages": ["NFLX"],
        "rule": "design record §6: each target p_lower <= alpha after Holm across the "
                "targets; no other class metric p_upper <= alpha; every lean, proposal and the "
                "panel's committed-lean count explained if moved",
        "scorer": "66f62b52830ef892cb6fb049d732648f7902ca6ba151cd79fcc083cc99d976c0",
        "targets": ["M-SIGN"], "transforms": []}))
    assert reg.sha == "ed155786e6d0b0863673899f1a3e872a00e7ac79f2b8c55e6194515630307ee8"


# -------------------------------------------- 2. no-worsening only; the panel registered whole

def test_a_no_worsening_registration_ships_on_no_change_and_blocks_on_a_worsening(
        tmp_path: Path, nflx: dict[str, Any]) -> None:
    reg = _reg(targets=(), no_worsening=True, rule=cm.NO_WORSENING_RULE)
    raw = nflx["synthesis"]
    s = cm.score_run(_run_dir(tmp_path / "same", reg, raw), reg, pages={"NFLX": nflx})
    assert s.ships, s.reasons
    worse_raw = json.loads(json.dumps(raw))
    worse_raw["key_unknowns"] = [*worse_raw["key_unknowns"],
                                 "Management said 'we will double the dividend next spring'."]
    out = tmp_path / "worse"
    out.mkdir()
    (out / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    with (out / "draws.jsonl").open("w") as f:
        for cond, r in (("BASE", raw), ("CAND", worse_raw)):
            for _ in range(5):
                f.write(json.dumps({"label": f"NFLX:{cond}", "raw": r,
                                    "stop_reason": "tool_use"}) + "\n")
    s2 = cm.score_run(out, reg, pages={"NFLX": nflx})
    assert not s2.ships and any("M-ABSENT worsens" in x for x in s2.reasons), s2.reasons
    assert not any("target" in x for x in s2.reasons)


def test_a_target_is_declared_or_no_worsening_is_never_both() -> None:
    with pytest.raises(ValueError, match="declares no target"):
        _reg(no_worsening=True)
    with pytest.raises(ValueError, match="not a deterministic metric"):
        _reg(targets=())


def test_a_panel_page_is_never_chosen_so_none_is_dropped() -> None:
    """The reviewer registered the panel minus LLY at $0 (sha 3dfb40b1)."""
    panel = rp.load_panel_file()["panel"]
    minus_lly = [t for t in panel if t != "LLY"]
    with pytest.raises(rp.ReplayError, match="panel page is never chosen"):
        cm.register("dc5b8787", "b109e26c", targets=["M-SIGN"], pages=minus_lly)
    with pytest.raises(rp.ReplayError, match="panel page is never chosen"):
        cm.register("dc5b8787", "b109e26c", targets=["M-SIGN"], pages=["NFLX", "LLY"])
    assert cm.registered_pages(None) == tuple(panel)
    assert cm.registered_pages(["NFLX"]) == ("NFLX",)


# ---------------------------------------------------------------- 3. the bar is conjunctive

def test_a_class_meeting_its_recall_gates_nothing_while_kappa_fails() -> None:
    """The logged TEST output read "kappa NOT MET; classes it may gate: ['ABSENT']"."""
    absent = jg.ClassRow("ABSENT", gold=32, judged=22, agree=16, material_gold=12,
                         material_caught=8, material_same=7)
    c = jg.Calibration(half="test", pages=("NKE",), half_pages=14, claims=314, missing=1,
                       kappa_final=0.23, kappa_a=0.26, kappa_b=0.21, kappa_coders=0.75,
                       kappa_coders_all=0.76, error_rate_judge=0.089, error_rate_gold=0.417,
                       class_agree_on_both_error=(17, 26), material_agree_on_both_error=(16, 26),
                       rows=(absent,))
    bar = c.bar()
    assert not bar["kappa_ok"] and bar["classes_it_may_gate"] == []
    assert bar["classes_meeting_recall_only"] == ["ABSENT"]
    line = jg.calibration_text(c).splitlines()[-1]
    assert "classes it may gate: none" in line and "gating nothing" in line
    passing = jg.Calibration(**{**c.__dict__, "kappa_final": 0.7})
    assert passing.bar()["classes_it_may_gate"] == ["ABSENT"]


# -------------------------------------------- 5. one judge per folder; TEST once per approval

def _history() -> None:
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{report.GOLD_REF}^{{commit}}"],
                      capture_output=True).returncode != 0:
        pytest.skip("the gold's freeze commit is not in this history")


class _FakeJudge:
    def __init__(self, ids: list[str]) -> None:
        self.ids, self.calls, self.messages = ids, 0, self

    def create(self, **kwargs: Any) -> Any:
        self.calls += 1
        block = SimpleNamespace(type="tool_use", input={"verdicts": [
            {"id": i, "checked": "found", "verdict": "OK", "material": False,
             "favours": "neither", "fact": ""} for i in self.ids]})
        usage = SimpleNamespace(input_tokens=100, output_tokens=100,
                                cache_creation_input_tokens=0, cache_read_input_tokens=0)
        return SimpleNamespace(usage=usage, content=[block], model="claude-opus-4-8",
                               stop_reason="tool_use")


def test_a_folder_judged_by_another_version_is_refused_not_rejudged(
        tmp_path: Path, gold: list[gd.GoldClaim]) -> None:
    """The reviewer pointed v2 at v1's `judge-dev` folder: rows `{page, raw}` only, and it reported
    v1's kappa as its own with no call."""
    _history()
    sub = [g for g in gold if g.page == "AMZN"]
    out = tmp_path / "judge-dev"
    out.mkdir()
    v1 = {"page": "AMZN", "raw": {"verdicts": [
        {"id": g.id, "verdict": "OK", "material": False, "favours": "neither", "fact": ""}
        for g in sub]}}
    (out / "judged.jsonl").write_text(json.dumps(v1) + "\n")
    sdk = _FakeJudge([g.id for g in sub])
    with pytest.raises(rp.ReplayError, match="never mixes judges"):
        jg.run_half("dev", budget=_budget(tmp_path), out_dir=out, sdk=sdk, gold=sub)
    assert sdk.calls == 0


def test_a_stored_row_is_stamped_and_another_claim_set_is_refused(
        tmp_path: Path, gold: list[gd.GoldClaim]) -> None:
    _history()
    sub = [g for g in gold if g.page == "AMZN"]
    out = tmp_path / "judge"
    budget = _budget(tmp_path)
    sdk = _FakeJudge([g.id for g in sub])
    jg.run_half("dev", budget=budget, out_dir=out, sdk=sdk, gold=sub)
    row = json.loads((out / "judged.jsonl").read_text().splitlines()[0])
    assert row["version"] == jg.JUDGE_VERSION and row["claims"] == [g.id for g in sub]
    assert len(row["request"]) == 64
    jg.run_half("dev", budget=budget, out_dir=out, sdk=sdk, gold=sub)   # same judge: resumes free
    assert sdk.calls == 1
    with pytest.raises(rp.ReplayError, match="never mixes judges"):
        jg.run_half("dev", budget=budget, out_dir=out, sdk=sdk, gold=sub[:-1])
    assert sdk.calls == 1


def test_test_is_read_once_per_approval(tmp_path: Path, gold: list[gd.GoldClaim]) -> None:
    _history()
    sub = [g for g in gold if g.page == "TECX"]
    budget = _budget(tmp_path)
    sdk = _FakeJudge([g.id for g in sub])
    first = tmp_path / "judge-test"
    jg.run_half("test", budget=budget, out_dir=first, sdk=sdk, gold=sub)
    assert [r["judge_test_read"] for r in budget.rows() if "judge_test_read" in r] == [
        str(first.resolve())]
    jg.run_half("test", budget=budget, out_dir=first, sdk=sdk, gold=sub)   # its own resume
    with pytest.raises(rp.ReplayError, match="scored ONCE"):
        jg.run_half("test", budget=budget, out_dir=tmp_path / "again", sdk=sdk, gold=sub)
    assert sdk.calls == 1
    # ledger (b): TEST was read before the marker existed — fourteen `judge:test:*` call rows
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    old = _budget(legacy, {"label": "judge:test:TECX", "draw": 1, "usd": 0.8})
    with pytest.raises(rp.ReplayError, match="scored ONCE"):
        jg.run_half("test", budget=old, out_dir=legacy / "v3", sdk=sdk, gold=sub)
    assert sdk.calls == 1


# ------------------------------------------------------- 7. a capture's draws, in order

def test_one_capture_whose_draws_differ_only_in_order_is_refused(nflx: dict[str, Any]) -> None:
    """A pin: `_one` compares each draw's request in order (`replay.wire`); with dict equality it
    passes two requests that send different bytes."""
    first = rp.capture(nflx, None, draws=1).kwargs
    moved = json.loads(json.dumps(first))
    props = moved["tools"][0]["input_schema"]["properties"]
    moved["tools"][0]["input_schema"]["properties"] = dict(reversed(list(props.items())))
    assert moved == first
    with pytest.raises(rp.ReplayError, match="different requests"):
        rp._one([first, moved], 2)
