"""Main against a branch — the harness's first comparison, exercised at $0.

A comparison whose two requests are identical on every page is REFUSED (a `mechanical.py` label
change without its transform is exactly that); a transform that re-reads a label from the code
under test reaches the request in the one span it changes; and the scorer applies the
pre-registered rule to draws built from REAL committed synthesis text.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import mechanical
from vinci.evals import compare as cm
from vinci.evals import replay as rp
from vinci.evals import variants

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def nflx() -> dict[str, Any]:
    page: dict[str, Any] = json.loads((ROOT / "data/dossiers/NFLX/dossier.json").read_text())
    return page


def _has_865() -> bool:
    return subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e",
                           f"{rp.MATERIAL_MARKED_BEFORE_SYNTHESIS}^{{commit}}"]).returncode == 0


def test_a_comparison_that_reaches_no_request_is_refused(nflx: dict[str, Any]) -> None:
    if not _has_865():
        pytest.skip("#865 is not in this history (shallow clone)")
    req = rp.capture_at("HEAD", nflx, None)
    c = cm.Captured("HEAD", "HEAD", ())
    c.requests[("NFLX", "BASE")] = c.requests[("NFLX", "CAND")] = req
    c.diffs.append(cm.PageDiff("NFLX", True, 0, True, {}, {}))
    with pytest.raises(rp.ReplayError, match="does not reach the synthesis request"):
        cm.refuse_if_unreached(c)
    with pytest.raises(rp.ReplayError, match="does not reach"):
        cm.run_compare(c, budget=rp.Budget(1.0, Path("/nonexistent-outside/l.jsonl")),
                       out_dir=Path("/nonexistent-outside/run"))


def test_the_relabel_transform_reads_the_code_under_tests_own_words(
        nflx: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    """At main the transform is the identity (the committed shape IS main's wording); with the
    code's words changed — as fix 3a changes them — the request changes in that span only."""
    base = rp.capture(nflx, None, transforms=["relabel_drawdown_shape"])
    assert base.kwargs == rp.capture(nflx, None).kwargs
    new = "no single-day drop of -10% or worse in the window (detector threshold -10%)"
    monkeypatch.setattr(mechanical, "_CURRENT_WORDS", mechanical._CURRENT_WORDS.__class__(
        **{**mechanical._CURRENT_WORDS.__dict__, "none_shape": new}))
    cand = rp.capture(nflx, None, transforms=["relabel_drawdown_shape"])
    assert base.system == cand.system
    assert new not in base.user
    assert new in cand.user and cand.user.count(new) == 1
    old = "gradual bleed — no discrete gap-down detected"
    # the prompt carries the facts as JSON (the dash escaped): ONE span changes, #920 V2's
    assert base.user.count(json.dumps(old)) == 1
    assert base.user.replace(json.dumps(old), json.dumps(new)) == cand.user


def test_the_transform_leaves_a_gap_down_window_alone() -> None:
    cnxc = json.loads((ROOT / "data/dossiers/CNXC/dossier.json").read_text())
    from vinci.evals.capture_child import pre_synthesis_mech
    mech = pre_synthesis_mech(cnxc)
    assert mech.drawdown_cause is not None
    assert mech.drawdown_cause.shape.value.startswith("discrete gap-downs")
    assert variants.relabel_drawdown_shape(mech) is mech


def test_an_unknown_transform_is_refused(nflx: dict[str, Any]) -> None:
    with pytest.raises(KeyError, match="no transform"):
        rp.capture(nflx, None, transforms=["no_such_variant"])


def _draws(tmp_path: Path, raw_base: dict[str, Any], raw_cand: dict[str, Any],
           name: str = "run") -> Path:
    out = tmp_path / name
    out.mkdir()
    with (out / "draws.jsonl").open("w") as f:
        for cond, raw in (("BASE", raw_base), ("CAND", raw_cand)):
            for n in range(5):
                f.write(json.dumps({"label": f"NFLX:{cond}", "draw": n + 1, "raw": raw,
                                    "stop_reason": "tool_use"}) + "\n")
    return out


def test_the_scorer_applies_the_rule_to_real_synthesis_text(tmp_path: Path,
                                                            nflx: dict[str, Any]) -> None:
    """BASE = NFLX's committed synthesis, five times; CAND = the same with its "bleed" wording
    replaced — the change fix 3a aims at. M-LABEL falls on every draw, nothing else moves, the
    lean holds: the rule ships it. Then a CAND that adds a quote the facts never carry worsens
    M-ABSENT, and the rule blocks it."""
    raw = nflx["synthesis"]
    text = json.dumps(raw)
    assert "bleed" in text
    cand = json.loads(text.replace("gradual bleed", "decline").replace("bleed", "decline"))
    panel = {"panel": ["NFLX"], "motivated": {"by_commit": {"NFLX": ["x"]}, "in_flight": {}}}
    s = cm.score_run(_draws(tmp_path, raw, cand), target="M-LABEL", panel=panel,
                     pages={"NFLX": nflx})
    r = s.metrics["M-LABEL"]
    assert r.cand_total < r.base_total and r.p_lower <= cm.ALPHA
    assert s.ships, s.reasons
    assert s.leans["NFLX"]["BASE"] == s.leans["NFLX"]["CAND"]

    worse = json.loads(text)
    worse["key_unknowns"] = [
        *worse["key_unknowns"],
        "Management said 'we will double the dividend next spring' on the call."]
    s2 = cm.score_run(_draws(tmp_path, raw, worse, name="worse"), target="M-LABEL", panel=panel,
                      pages={"NFLX": nflx})
    assert not s2.ships
    assert any("M-ABSENT worsens" in x for x in s2.reasons)
    assert any("target M-LABEL does not improve" in x for x in s2.reasons)


def test_a_truncated_or_incomplete_draw_is_not_scored(nflx: dict[str, Any]) -> None:
    raw = nflx["synthesis"]
    assert cm.usable({"raw": raw, "stop_reason": "tool_use"})
    assert not cm.usable({"raw": raw, "stop_reason": "max_tokens"})       # partial tool input
    assert not cm.usable({"raw": {"evidence_balance": "mixed — x"}, "stop_reason": "tool_use"})
    assert not cm.usable({"raw": None, "stop_reason": "tool_use"})


def test_a_target_that_is_not_a_metric_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not a deterministic metric"):
        cm.score_run(tmp_path, target="LABEL")
