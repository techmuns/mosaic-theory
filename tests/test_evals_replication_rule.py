"""The replication rule (coordinator, 2026-11-07, for #923's measurement) and the scorer's fixed
definitions.

A first run registered with ``ship_alpha`` SHIPS at p_lower <= ship_alpha; in (ship_alpha, alpha]
it needs a FRESH, separately registered replication of the same design reaching p_lower <= alpha;
above alpha it does not ship. A replication is registered only for a first run whose own score
decided "replication required", in the same design — anything else is result-shopping. The draws
are built from NFLX's real committed synthesis: its "bleed" wording is what M-LABEL counts.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.stripped_pages import replayable_text
from vinci.dossier import mechanical
from vinci.evals import compare as cm
from vinci.evals import metrics as mt
from vinci.evals import replay as rp


@pytest.fixture(autouse=True)
def _production_files_are_bases(monkeypatch: pytest.MonkeyPatch) -> None:
    """These tests pin registration's OTHER rules on old commits (`dc5b8787` → `b109e26c`). Since
    order 8, `cm.register` refuses a checkout whose production files are not BASE's (RG-D12, B's
    check, gap 1), which today's checkout never is for an old BASE; that rule has its own pins
    (`tests/test_evals_order8_gaps.py`), so here it is stubbed to this checkout's fingerprint."""
    monkeypatch.setattr(cm, "refuse_unless_scored_by_base",
                        lambda base_ref, **k: cm.scorer_fingerprint())

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def nflx() -> dict[str, Any]:
    page: dict[str, Any] = json.loads(replayable_text("NFLX"))
    return page


def _reg(**over: Any) -> cm.Registration:
    base: dict[str, Any] = {"base_ref": "A", "cand_ref": "B", "transforms": (), "pages": ("NFLX",),
                            "draws": 5, "targets": ("M-LABEL",), "held_out": (),
                            "scorer": cm.scorer_fingerprint(), "ship_alpha": 0.01,
                            "rule": cm.REPLICATION_RULE}
    return cm.Registration(**{**base, **over})


def _run(path: Path, reg: cm.Registration, base: list[Any], cand: list[Any]) -> Path:
    path.mkdir()
    (path / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    with (path / "draws.jsonl").open("w") as f:
        for cond, raws in (("BASE", base), ("CAND", cand)):
            for raw in raws:
                f.write(json.dumps({"label": f"NFLX:{cond}", "raw": raw,
                                    "stop_reason": "tool_use"}) + "\n")
    return path


def _clean(raw: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(raw)
    assert "bleed" in text
    out: dict[str, Any] = json.loads(text.replace("gradual bleed", "decline")
                                     .replace("bleed", "decline"))
    return out


def test_a_first_run_ships_only_at_the_ship_alpha(tmp_path: Path, nflx: dict[str, Any]) -> None:
    """Every CAND draw drops the label: p_lower = 1/252 = 0.004 <= 0.01 — it ships."""
    raw = nflx["synthesis"]
    s = cm.score_run(_run(tmp_path / "r", _reg(), [raw] * 5, [_clean(raw)] * 5), _reg(),
                     pages={"NFLX": nflx})
    assert s.metrics["M-LABEL"].p_lower == pytest.approx(1 / 252)
    assert s.decision == "ships" and s.ships, s.reasons


def test_a_first_run_in_the_band_requires_a_replication(tmp_path: Path,
                                                        nflx: dict[str, Any]) -> None:
    """Four of five CAND draws drop it: p_lower = 6/252 = 0.024, in (0.01, 0.05]. Without the
    rule (alpha 0.05 alone) the same draws ship — the band is the rule's own effect."""
    raw = nflx["synthesis"]
    cand = [_clean(raw)] * 4 + [raw]
    s = cm.score_run(_run(tmp_path / "r", _reg(), [raw] * 5, cand), _reg(), pages={"NFLX": nflx})
    assert s.metrics["M-LABEL"].p_lower == pytest.approx(6 / 252)
    assert s.decision == cm.REPLICATION_REQUIRED and not s.ships
    assert any("replication band" in r for r in s.reasons)
    log = json.loads((tmp_path / "r" / "score_log.jsonl").read_text().splitlines()[-1])
    assert log["decision"] == cm.REPLICATION_REQUIRED and log["ship_alpha"] == 0.01
    plain = _reg(ship_alpha=None, rule=cm.Registration.rule)
    s2 = cm.score_run(_run(tmp_path / "plain", plain, [raw] * 5, cand), plain,
                      pages={"NFLX": nflx})
    assert s2.decision == "ships" and s2.ships


def test_a_first_run_above_alpha_does_not_ship(tmp_path: Path, nflx: dict[str, Any]) -> None:
    raw = nflx["synthesis"]
    s = cm.score_run(_run(tmp_path / "r", _reg(), [raw] * 5, [raw] * 5), _reg(),
                     pages={"NFLX": nflx})
    assert s.decision == cm.DOES_NOT_SHIP and not s.ships


def test_a_worsening_blocks_whatever_the_target_does(tmp_path: Path,
                                                     nflx: dict[str, Any]) -> None:
    raw = nflx["synthesis"]
    worse = _clean(raw)
    worse["key_unknowns"] = [*worse["key_unknowns"],
                             "Management said 'we will double the dividend next spring'."]
    s = cm.score_run(_run(tmp_path / "r", _reg(), [raw] * 5, [worse] * 5), _reg(),
                     pages={"NFLX": nflx})
    assert s.metrics["M-LABEL"].p_lower <= 0.01
    assert s.decision == cm.DOES_NOT_SHIP and any("M-ABSENT worsens" in r for r in s.reasons)


# (a replication's score — the link to a real first run — is pinned in test_evals_pr926_round2.py)


def test_the_rule_refuses_an_incoherent_registration() -> None:
    with pytest.raises(ValueError, match="must lie in"):
        _reg(ship_alpha=0.05)
    with pytest.raises(ValueError, match="no-worsening"):
        _reg(targets=(), no_worsening=True)
    with pytest.raises(ValueError, match="under the replication rule"):
        _reg(ship_alpha=None, replicates="f" * 64)


def _history() -> None:
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", "b109e26c^{commit}"],
                      capture_output=True).returncode != 0:
        pytest.skip("needs the full history")


# (a replication's registration against the ledger: test_evals_pr926_round2.py)


def test_a_registration_records_the_inputs_its_capture_read() -> None:
    _history()
    c = cm.Captured("dc5b8787", "b109e26c", ())
    c.requests[("NFLX", "BASE")] = c.requests[("NFLX", "CAND")] = rp.Request({"system": "x"})
    c.inputs = {"ciq_root": "/ciq", "pages": {"NFLX": {
        "comps": {"file": "Company Comparable Analysis Netflix.xls", "sha256": "a" * 64},
        "transcripts": [{"file": "t.rtf", "sha256": "b" * 64}]}}}
    reg = cm.register("dc5b8787", "b109e26c", targets=["M-LABEL"], pages=["NFLX"], captured=c)
    assert reg.inputs == c.inputs
    again = cm.Registration.from_json(reg.to_json())
    assert again.sha == reg.sha and again.inputs == c.inputs


def test_the_trailing_only_family_is_fixed_to_the_old_wording() -> None:
    """Coordinator, 2026-11-07: M-LABEL counts the OLD label, whatever the code under test
    writes. The wording cannot be retyped (`test_sleeves`), so it is pinned by its sha256 — the
    text main and #923 (e91490ae) both carry."""
    assert hashlib.sha256(mechanical.TRAILING_ONLY_NOTE.encode()).hexdigest() == \
        "cbf0eed933cf5404bff6b923ae0a221ea785933982c0b13ccd931e604128229f" == \
        mt.TRAILING_ONLY_SHA256
    assert mt.LABEL_FAMILIES["trailing-only"].search(
        "trailing only — no forward basis; the level is unexplained")
    assert mt.LABEL_FAMILIES["bleed"].pattern == r"\bbleed\w*"


def test_a_changed_trailing_only_wording_stops_the_scorer_loading(
        monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib
    monkeypatch.setattr(mechanical, "TRAILING_ONLY_NOTE", "trailing multiple; no NTM cell found")
    try:
        with pytest.raises(RuntimeError, match="metric change"):
            importlib.reload(mt)
    finally:
        monkeypatch.undo()
        importlib.reload(mt)
    restored = hashlib.sha256(mechanical.TRAILING_ONLY_NOTE.encode()).hexdigest()
    assert restored == mt.TRAILING_ONLY_SHA256


def test_a_registration_states_its_coverage_in_its_sha() -> None:
    """The coordinator's ruling for #923 (2026-11-07): the registration itself says the target
    covers items 1-2 and items 3-4 are read only through the no-worsening checks — in the sha, so
    it is written before the draw and cannot be edited after."""
    plain = _reg()
    noted = _reg(note="M-LABEL covers items 1-2 only")
    assert noted.sha != plain.sha and "note" not in json.loads(plain.to_json())
    assert cm.Registration.from_json(noted.to_json()).note == "M-LABEL covers items 1-2 only"


@pytest.fixture(autouse=True)
def _scorer_is_the_fingerprint(monkeypatch: pytest.MonkeyPatch) -> None:
    """These tests pin the harness's other rules under placeholder refs or old commits. Since
    #1030's review round 1 the library runs RG-D12 whole (BASE's production files, the harness
    at `scorer_ref`), which no such ref holds; it is stood in by the fingerprint comparison
    these tests were written against (`tests/evals_scorer_stub.py`). RG-D12's own pins are in
    `tests/test_evals_order8.py` and `tests/test_evals_order8_round1.py`."""
    from tests.evals_scorer_stub import fingerprint_only
    monkeypatch.setattr(cm, "refuse_unless_registered_scorer", fingerprint_only)
