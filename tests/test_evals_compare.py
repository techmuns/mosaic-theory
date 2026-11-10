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

from tests.pre_strip import pre_strip_text
from vinci.dossier import mechanical
from vinci.evals import compare as cm
from vinci.evals import replay as rp
from vinci.evals import variants

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def nflx() -> dict[str, Any]:
    page: dict[str, Any] = json.loads(pre_strip_text("NFLX"))
    return page


def _reg(pages: tuple[str, ...] = ("NFLX",), base: str = "A", cand: str = "B") -> cm.Registration:
    return cm.Registration(base_ref=base, cand_ref=cand, transforms=(), pages=pages, draws=5,
                           targets=("M-LABEL",), held_out=(), scorer=cm.scorer_fingerprint())


def _has_865() -> bool:
    return subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e",
                           f"{rp.MATERIAL_MARKED_BEFORE_SYNTHESIS}^{{commit}}"]).returncode == 0


def test_a_comparison_that_reaches_no_request_is_refused(tmp_path: Path,
                                                         nflx: dict[str, Any]) -> None:
    if not _has_865():
        pytest.skip("#865 is not in this history (shallow clone)")
    req = rp.capture_at("HEAD", nflx, None)
    c = cm.Captured("HEAD", "HEAD", ())
    c.requests[("NFLX", "BASE")] = c.requests[("NFLX", "CAND")] = req
    c.diffs.append(cm.PageDiff("NFLX", True, 0, True, {}, {}))
    with pytest.raises(rp.ReplayError, match="does not reach the synthesis request"):
        cm.refuse_if_unreached(c)
    with pytest.raises(rp.ReplayError, match="does not reach"):
        cm.run_compare(c, budget=rp.Budget.open(tmp_path / "l.jsonl", cap_usd=1.0,
                                                approval="operator: test"),
                       out_dir=tmp_path / "run", registration=_reg(base="HEAD", cand="HEAD"))


def test_the_relabel_transform_reads_the_code_under_tests_own_words(
        nflx: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    """With the code's words equal to the committed shape (main's wording) the transform is the
    identity; with the code's words changed — as fix 3a changes them — the request changes in that
    span only. Both wordings are set here, so the pin holds on main and on fix 3a's branch alike
    (merged into #923, 2026-11-06: the first cut read the code's words as main's)."""
    old = "gradual bleed — no discrete gap-down detected"
    new = "no single-day drop of -10% or worse in the window (detector threshold -10%)"

    def words(none_shape: str) -> None:
        monkeypatch.setattr(mechanical, "_CURRENT_WORDS", mechanical._CURRENT_WORDS.__class__(
            **{**mechanical._CURRENT_WORDS.__dict__, "none_shape": none_shape}))

    words(old)
    base = rp.capture(nflx, None, transforms=["relabel_drawdown_shape"])
    assert base.kwargs == rp.capture(nflx, None).kwargs
    words(new)
    cand = rp.capture(nflx, None, transforms=["relabel_drawdown_shape"])
    assert base.system == cand.system
    assert new not in base.user
    assert new in cand.user and cand.user.count(new) == 1
    # the prompt carries the facts as JSON (the dash escaped): ONE span changes, #920 V2's
    assert base.user.count(json.dumps(old)) == 1
    assert base.user.replace(json.dumps(old), json.dumps(new)) == cand.user


def test_the_transform_leaves_a_gap_down_window_alone() -> None:
    cnxc = json.loads(pre_strip_text("CNXC"))
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
    (out / "registration.json").write_text(_reg().to_json(), encoding="utf-8")
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
    s = cm.score_run(_draws(tmp_path, raw, cand), _reg(), pages={"NFLX": nflx})
    r = s.metrics["M-LABEL"]
    assert r.cand_total < r.base_total and r.p_lower <= cm.ALPHA
    assert s.ships, s.reasons
    assert s.leans["NFLX"]["BASE"] == s.leans["NFLX"]["CAND"]

    worse = json.loads(text)
    worse["key_unknowns"] = [
        *worse["key_unknowns"],
        "Management said 'we will double the dividend next spring' on the call."]
    s2 = cm.score_run(_draws(tmp_path, raw, worse, name="worse"), _reg(), pages={"NFLX": nflx})
    assert not s2.ships
    assert any("M-ABSENT worsens" in x for x in s2.reasons)
    assert any("target M-LABEL does not improve" in x for x in s2.reasons)


def test_a_truncated_or_incomplete_draw_is_not_scored(nflx: dict[str, Any]) -> None:
    raw = nflx["synthesis"]
    assert cm.usable({"raw": raw, "stop_reason": "tool_use"})
    assert not cm.usable({"raw": raw, "stop_reason": "max_tokens"})       # partial tool input
    assert not cm.usable({"raw": {"evidence_balance": "mixed — x"}, "stop_reason": "tool_use"})
    assert not cm.usable({"raw": None, "stop_reason": "tool_use"})


def test_a_target_that_is_not_a_metric_is_refused() -> None:
    with pytest.raises(ValueError, match="not a deterministic metric"):
        cm.Registration(base_ref="A", cand_ref="B", transforms=(), pages=("NFLX",), draws=5,
                        targets=("LABEL",), held_out=(), scorer="x")


# ------------------------------------------------- round 1 (in-session /code-review high, #924)

def _page(t: str) -> dict[str, Any]:
    page: dict[str, Any] = json.loads(pre_strip_text(t))
    return page


def _lean_raw(raw: dict[str, Any], lean: str) -> dict[str, Any]:
    out = json.loads(json.dumps(raw))
    out["evidence_balance"] = f"{lean} — {lean} on balance (test)"
    return out


def _rows(path: Path, rows: list[tuple[str, str, dict[str, Any] | None, str]],
          reg: cm.Registration) -> Path:
    path.mkdir()
    (path / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    with (path / "draws.jsonl").open("w") as f:
        for label, cond, raw, stop in rows:
            f.write(json.dumps({"label": f"{label}:{cond}", "raw": raw, "stop_reason": stop})
                    + "\n")
    return path


def test_a_rerun_into_a_used_out_dir_is_refused(tmp_path: Path, nflx: dict[str, Any]) -> None:
    """Draws append; a second run into the same folder would score two runs as one."""
    base = rp.capture(nflx, None)
    cand = rp.Request({**base.kwargs, "system": base.system + " "})
    c = cm.Captured("A", "B", ())
    c.requests[("NFLX", "BASE")], c.requests[("NFLX", "CAND")] = base, cand
    c.diffs.append(cm.PageDiff("NFLX", False, 0, False, {}, {}))
    out = tmp_path / "run"
    out.mkdir()
    (out / "draws.jsonl").write_text("{}\n", encoding="utf-8")
    reg = cm.Registration(**{**_reg().__dict__, "requests": cm.request_pins(c)})
    with pytest.raises(rp.ReplayError, match="already holds draws"):
        cm.run_compare(c, budget=rp.Budget.open(tmp_path / "l.jsonl", cap_usd=1.0,
                                                approval="operator: test"),
                       out_dir=out, registration=reg)


def test_a_page_with_no_usable_draw_in_a_condition_blocks_never_vanishes(
        tmp_path: Path, nflx: dict[str, Any]) -> None:
    raw = nflx["synthesis"]
    rows = [("NFLX", "BASE", raw, "tool_use")] * 5 + [("NFLX", "CAND", raw, "max_tokens")] * 5
    s = cm.score_run(_rows(tmp_path / "r", rows, _reg()), _reg(), pages={"NFLX": nflx})
    assert not s.ships
    assert any("NFLX" in r and "no usable draw" in r for r in s.reasons), s.reasons


def test_a_panel_shift_in_committed_leans_must_be_explained(tmp_path: Path,
                                                            nflx: dict[str, Any]) -> None:
    """Record §6.3: two of five draws turn committed on three pages; no modal lean or proposal
    moves (mixed 3 / bullish 2 proposes nothing), but the panel count does — p 0.022."""
    raw = nflx["synthesis"]
    mixed, bull = _lean_raw(raw, "mixed"), _lean_raw(raw, "strongly-bullish")
    rows: list[tuple[str, str, dict[str, Any] | None, str]] = []
    for t in ("NFLX", "MCK", "LLY"):
        rows += [(t, "BASE", mixed, "tool_use")] * 5
        rows += [(t, "CAND", mixed, "tool_use")] * 3 + [(t, "CAND", bull, "tool_use")] * 2
    reg = _reg(pages=("NFLX", "MCK", "LLY"))
    s = cm.score_run(_rows(tmp_path / "r", rows, reg), reg,
                     pages={t: _page(t) for t in ("NFLX", "MCK", "LLY")})
    assert any("committed-lean draws" in r for r in s.reasons), s.reasons


def test_an_identical_tally_in_another_order_is_not_a_lean_move(tmp_path: Path,
                                                                nflx: dict[str, Any]) -> None:
    raw = nflx["synthesis"]
    m, b, x = (_lean_raw(raw, k) for k in ("mixed", "strongly-bullish", "strongly-bearish"))
    rows = [("NFLX", "BASE", r, "tool_use") for r in (m, b, m, b, x)]
    rows += [("NFLX", "CAND", r, "tool_use") for r in (b, m, b, m, x)]
    s = cm.score_run(_rows(tmp_path / "r", rows, _reg()), _reg(), pages={"NFLX": nflx})
    assert not any("lean moved" in r for r in s.reasons), s.reasons
