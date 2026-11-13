"""Fix request 2, order 8 — round 1 of the coordinator's review of #1030 (2026-11-12, at 7073ea09;
its independent reviewer's repro scripts `shop.py`, `mutate.py`, `mutate2.py`).

Each FIX's test fails on 7073ea09 for its item's own reason. Each PIN names the mutant that
survived the suite there and dies here. $0: no key, no network. A paid path runs with the client
class spied, so a refusal is shown to come before any client exists.
"""
from __future__ import annotations

import dataclasses
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.test_evals_order8 import (
    BASE_953,
    CAND_953,
    _a_build_run,
    _arm_run,
    _impact_export,
    _indexed,
    _page,
    _repo_with_index,
)
from tests.test_evals_order8_gaps import _budget, _Spy

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def spy(monkeypatch: pytest.MonkeyPatch) -> type[_Spy]:
    from vinci.evals import replay as rp
    _Spy.built = 0
    monkeypatch.setattr(rp, "AnthropicLlmClient", _Spy)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return _Spy


def _registered(sha: str, approval: str, design: str, kind: str = "compare") -> dict[str, Any]:
    """A `registered` row as `registry.record_registered` writes it, design key included."""
    return {"event": "registered", "registration": sha, "kind": kind, "refs": {}, "pages": [],
            "draws": 5, "approval": approval, "design": design,
            "registered_at": "2026-11-12T00:00:00Z"}


def _drawn(sha: str, approval: str, unit: str | None = None) -> dict[str, Any]:
    return {"event": "drawn", "registration": sha, "approval": approval, "unit": unit,
            "drawn_at": "2026-11-12T00:00:01Z"}


def _first_run() -> Any:
    from vinci.evals import compare as cm
    return cm.Registration(base_ref="a" * 40, cand_ref="b" * 40, transforms=(), pages=("BURL",),
                           draws=5, targets=("M-LABEL",), held_out=(), scorer="f" * 64,
                           ship_alpha=0.01, requests={"BURL:BASE": "1" * 64,
                                                      "BURL:CAND": "2" * 64}, note="first run")


# --------------------- item 1: a DESIGN is drawn once across approvals, whatever its note


def test_a_design_is_drawn_once_across_approvals_whatever_its_note(tmp_path: Path) -> None:
    """(−) Item 1, reproduced by the reviewer's `shop.py`. The index keyed "drawn once" on the
    registration's sha, and a new `--note` gives one design a new sha. Opening a second approval,
    re-registering the same design with new words and drawing again was allowed: result shopping
    that walked around the replication rule. `run_compare`'s own drawn-once-per-design check read
    only the current approval's ledger."""
    from vinci.evals import compare as cm
    from vinci.evals import registry
    from vinci.evals.replay import ReplayError
    r1 = _first_run()
    r2 = dataclasses.replace(r1, note="first run (re-registered)")
    assert not cm.design_differs(r1, r2) and r1.sha != r2.sha
    a1, a2 = "1" * 64, "2" * 64
    repo = _indexed(tmp_path, [(r1, a1), (r2, a2)])
    registry.claim_draw(r1, approval=a1, root=repo)
    # "design was already drawn": the design rule's own refusal, not round 2's request-pins one
    with pytest.raises(ReplayError, match="design was already drawn"):
        registry.claim_draw(r2, approval=a2, root=repo)


def test_a_run_design_is_drawn_once_across_approvals_whatever_its_note(tmp_path: Path) -> None:
    """(−) Item 1 for `register-run`: a `RunRegistration` carries a `note` too, so one build design
    re-registered under a second approval could draw builds the first had not. A design whose
    builds were drawn under one registration is refused under any other."""
    from vinci.evals import registry
    from vinci.evals.replay import ReplayError
    r, s = _a_build_run("one"), _a_build_run("two")
    a1, a2 = "1" * 64, "2" * 64
    repo = _indexed(tmp_path, [(r, a1), (s, a2)])
    registry.claim_draw(r, approval=a1, unit="NFLX:1", root=repo)
    with pytest.raises(ReplayError, match="design was already drawn"):
        registry.claim_draw(s, approval=a2, unit="NFLX:2", root=repo)


def test_a_replication_is_its_own_design_and_is_drawn_once_too(tmp_path: Path) -> None:
    """(+/−) The replication rule's one other draw survives the design key: a replication of a
    drawn first run shares its design but names it (`replicates`), so its key differs and it is
    drawn once; a second replication of the same run, new words or not, is refused. (+) Round 2
    (F3): the replication draws exactly the bytes its first run drew, and the request-pins rule
    exempts the run it replicates, so it is still drawn."""
    from vinci.evals import compare as cm
    from vinci.evals import registry
    from vinci.evals.replay import ReplayError
    r1 = _first_run()
    rep = dataclasses.replace(r1, replicates=r1.sha, note="its replication")
    rep2 = dataclasses.replace(rep, note="its replication, re-registered")
    assert not cm.design_differs(r1, rep) and rep.requests == r1.requests
    assert cm.draw_key(r1) != cm.draw_key(rep) == cm.draw_key(rep2)
    assert cm.draw_key(r1) == cm.draw_key(dataclasses.replace(r1, note="other words"))
    a1, a2 = "1" * 64, "2" * 64
    repo = _indexed(tmp_path, [(r1, a1), (rep, a1), (rep2, a2)])
    registry.claim_draw(r1, approval=a1, root=repo)
    registry.claim_draw(rep, approval=a1, root=repo)
    with pytest.raises(ReplayError, match="design was already drawn"):
        registry.claim_draw(rep2, approval=a2, root=repo)


def test_a_run_registration_s_design_ignores_its_words_and_its_paths() -> None:
    """(+) `builds.draw_key`: the note and the recorded inputs (a path's spelling) are not the
    design; what is drawn is."""
    from vinci.evals import builds as bd
    r = bd.RunRegistration(code_ref="0" * 40, transforms=(), pages=("NFLX",), draws=2, builds=2,
                           min_gap_s=300.0, requests={"NFLX": "1" * 64},
                           inputs={"ciq_root": "/ciq"}, note="one")
    assert bd.draw_key(r) == bd.draw_key(dataclasses.replace(
        r, note="two", inputs={"ciq_root": "/elsewhere/ciq"}))
    assert bd.draw_key(r) != bd.draw_key(dataclasses.replace(r, draws=3))


def test_the_index_records_each_registration_s_design(tmp_path: Path) -> None:
    """(+) `record_registered` writes the design key the claim reads — derived from the
    registration since round 2, as are its request pins — and a registered row with none is
    refused at the claim rather than read as a design of its own."""
    from vinci.evals import compare as cm
    from vinci.evals import registry
    from vinci.evals.replay import ReplayError
    t = _first_run()
    repo = _repo_with_index(tmp_path, [])
    registry.record_registered(t, approval="1" * 64, root=repo)
    row = registry.working_rows(repo)[-1]
    assert (row["registration"], row["design"], row["pins"]) == (t.sha, cm.draw_key(t),
                                                                 t.requests)
    legacy = _repo_with_index(tmp_path / "legacy", [
        {k: v for k, v in _registered(t.sha, "1" * 64, "x").items() if k != "design"}])
    with pytest.raises(ReplayError, match="no design"):
        registry.claim_draw(t, approval="1" * 64, root=legacy)


# ---------------------------- item 2: drawn only once MAIN holds the registration (mutant M1)


def test_a_draw_right_after_register_before_its_row_merges_is_refused(tmp_path: Path) -> None:
    """PIN, mutant M1 (`require_on_main` reads the working copy): the real misuse is a draw made
    straight after `register`, whose row sits in this checkout's index and not yet on main. The
    only negative pin used a sha absent everywhere, so reading the working copy survived."""
    from vinci.evals import registry
    from vinci.evals.replay import ReplayError
    repo = _repo_with_index(tmp_path, [])
    with (repo / registry.INDEX).open("a") as f:
        f.write(json.dumps(_registered("v" * 64, "1" * 64, "d" * 64)) + "\n")
    assert any(r["registration"] == "v" * 64 for r in registry.working_rows(repo))
    with pytest.raises(ReplayError, match="not on origin/main"):
        registry.require_on_main("v" * 64, root=repo)


# ------------------------- item 3: each arm's layer is rebuilt at its OWN ref (mutant M11)


def _transform_reg() -> Any:
    from vinci.evals import compare as cm
    return cm.Registration(base_ref="A", cand_ref="B", transforms=("relabel_drawdown_shape",),
                           pages=("NFLX",), draws=5, targets=("M-LABEL",), held_out=(),
                           scorer=cm.scorer_fingerprint(),
                           inputs={"ciq_root": "/ciq", "pages": {"NFLX": {"comps": "c",
                                                                           "ciq": "q"}}})


def test_each_arm_s_layer_is_rebuilt_at_its_own_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    """PIN, mutant M11 (`arm_layer` rebuilds both arms at BASE's ref): the item-6 test injects
    `layer_for`, so the production function never ran. Here `arm_layer` itself runs, with the
    child stood in: BASE's layer is built at BASE's ref and CAND's at CAND's."""
    from vinci.evals import compare as cm
    from vinci.evals import replay as rp
    from vinci.evals.capture_child import pre_synthesis_mech
    page = _page("NFLX")
    layer = pre_synthesis_mech(page).model_dump(mode="json")
    seen: list[str] = []
    monkeypatch.setattr(cm, "_transform_inputs",
                        lambda t, root, tr: (None, None, {"comps": "c", "ciq": "q"}))
    monkeypatch.setattr(rp, "layer_at", lambda ref, p, **k: seen.append(ref) or layer)
    reg = _transform_reg()
    for cond in ("BASE", "CAND"):
        cm.arm_layer(reg, "NFLX", cond, page)
    assert seen == ["A", "B"]


def test_an_arm_whose_ciq_inputs_moved_is_not_rebuilt(monkeypatch: pytest.MonkeyPatch) -> None:
    """PIN, mutant M8 (`arm_layer` skips the recorded CIQ-input check): inputs that are not the
    ones the registration recorded are refused before any child is run."""
    from vinci.evals import compare as cm
    from vinci.evals import replay as rp
    from vinci.evals.replay import ReplayError
    monkeypatch.setattr(cm, "_transform_inputs",
                        lambda t, root, tr: (None, None, {"comps": "c", "ciq": "moved"}))
    monkeypatch.setattr(rp, "layer_at", lambda *a, **k: pytest.fail("a child was run"))
    with pytest.raises(ReplayError, match="CIQ inputs"):
        cm.arm_layer(_transform_reg(), "NFLX", "CAND", _page("NFLX"))


# ------------------- item 4: RG-D12 and the export's identity, in the LIBRARY (D1, M5, M7, M10)


def _impact_reg(tmp_path: Path) -> tuple[Any, Any, Path]:
    from vinci.evals import compare as cm
    out, _ = _impact_export(tmp_path)
    cap = cm.captured_from_impact(out)
    reg = cm.Registration(base_ref=BASE_953, cand_ref=CAND_953, transforms=(), pages=("NFLX",),
                          draws=5, targets=(), held_out=(), scorer=cm.scorer_fingerprint(),
                          no_worsening=True, requests=cm.request_pins(cap), inputs=cap.inputs)
    return cap, reg, out


def test_library_run_compare_refuses_production_files_that_are_not_bases(
        tmp_path: Path, spy: type[_Spy]) -> None:
    """(−) D1 at the draw. The library `run_compare` compared only the fingerprint with the
    registered one, so a registration whose fingerprint matched this checkout, but whose BASE
    holds other production files, was drawn; only the CLI ran RG-D12's whole check. Here BASE is
    #953's parent, whose four production files all differ from this checkout's."""
    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    cap, reg, _ = _impact_reg(tmp_path)
    with pytest.raises(ReplayError, match="BASE's production files"):
        cm.run_compare(cap, budget=_budget(tmp_path), out_dir=tmp_path / "run",
                       registration=reg, claim=lambda: None)
    assert spy.built == 0


def test_library_run_compare_refuses_a_scorer_that_is_not_the_registered_one(
        tmp_path: Path, spy: type[_Spy]) -> None:
    """PIN, mutant M10 (the library's fingerprint check removed): the CLI ran the same check, so
    no test reached it. A registration naming another scorer is refused by the library alone."""
    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    cap, reg, _ = _impact_reg(tmp_path)
    with pytest.raises(ReplayError, match="not the registered scorer"):
        cm.run_compare(cap, budget=_budget(tmp_path), out_dir=tmp_path / "run",
                       registration=dataclasses.replace(reg, scorer="f" * 64), claim=lambda: None)
    assert spy.built == 0


def test_library_score_run_refuses_production_files_that_are_not_bases(tmp_path: Path) -> None:
    """(−) D1 at the score ("no score-time check"): the library `score_run` compared only the
    fingerprint, so the same registration was scored by production files that are not BASE's."""
    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    _, reg, _ = _impact_reg(tmp_path)
    raw = _page("NFLX")["synthesis"]
    assert isinstance(raw, dict)
    with pytest.raises(ReplayError, match="BASE's production files"):
        cm.score_run(_arm_run(tmp_path, reg, raw, raw, "run"), reg)


def test_run_compare_refuses_an_impact_export_whose_manifest_moved(
        tmp_path: Path, spy: type[_Spy], monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) Mutant M5's guard, moved into the library: `run-compare`'s CLI compared the export's
    manifest sha256 with the registered one, but the library `run_compare` did not. A manifest
    rewritten after registration (here only its layout, so every file it hashes still checks) is
    not the export registered, and nothing is drawn from it. RG-D12 is stood in: BASE is #953's."""
    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    _, reg, out = _impact_reg(tmp_path)
    m = json.loads((out / "manifest.json").read_text())
    (out / "manifest.json").write_text(json.dumps(m, indent=2))
    moved = cm.captured_from_impact(out)
    monkeypatch.setattr(cm, "refuse_unless_registered_scorer", lambda r, **k: None)
    with pytest.raises(ReplayError, match="manifest"):
        cm.run_compare(moved, budget=_budget(tmp_path), out_dir=tmp_path / "run",
                       registration=reg, claim=lambda: None)
    assert spy.built == 0


def test_an_impact_request_edited_after_its_run_is_refused(tmp_path: Path) -> None:
    """PIN, mutant M7 (the request's wire sha256 not checked): `request.json` is hashed by its
    wire bytes only, so this check is its one guard; an edited request is refused."""
    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    out, _ = _impact_export(tmp_path)
    p = out / "head" / "NFLX" / "request.json"
    kwargs = json.loads(p.read_text())
    kwargs["system"] = f"{kwargs['system']} Also: be bullish."
    p.write_text(json.dumps(kwargs))
    with pytest.raises(ReplayError, match="wire sha256"):
        cm.captured_from_impact(out)


# ------------------------ item 6: the fingerprint covers the files the scorer reads through


@pytest.mark.parametrize("rel", ["vinci/sleeves.py", "vinci/dossier/midcycle.py",
                                 "vinci/schemas/ledger.py"])
def test_the_fingerprint_moves_on_a_file_the_scorer_reads_through(tmp_path: Path,
                                                                  rel: str) -> None:
    """(−) Item 6: `derive_proposal` reads `vinci/sleeves.py`, and the scorer imports
    `vinci/dossier/midcycle.py` and `vinci/schemas/ledger.py`; an edit to any of them changed a
    score's definitions without moving the fingerprint. Each is a PRODUCTION file, BASE's."""
    from vinci.evals import compare as cm
    root = tmp_path / "root"
    for f in {*cm.SCORER_FILES, rel}:
        (root / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / f, root / f)
    before = cm.scorer_fingerprint(root)
    (root / rel).write_text((root / rel).read_text() + "\n# an edit\n")
    assert cm.scorer_fingerprint(root) != before
    assert rel in cm.PRODUCTION_SCORER_FILES


# --------------------------- item 7: register checks its approval before it writes anything


def test_register_with_no_budget_ledger_writes_no_registration(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) Item 7: `register` wrote the registration file, then refused for want of
    `--budget-ledger`, and the file left behind blocked the retry ("written once"). The approval
    is now required before anything is written. RG-D12 is stood in: BASE is #953's."""
    from vinci.evals import __main__ as cli
    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    out, _ = _impact_export(tmp_path)
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()
    monkeypatch.setattr(cm, "fixed_scorer", lambda base, **k: (cm.scorer_fingerprint(), head))
    monkeypatch.setattr(cm, "refuse_unless_scored_by_base",
                        lambda base_ref, **k: cm.scorer_fingerprint())
    from vinci.evals import registry
    indexed: list[str] = []   # never this repository's index, even if the refusal regresses
    monkeypatch.setattr(registry, "record_registered", lambda sha, **k: indexed.append(sha))
    target = tmp_path / "r.json"
    with pytest.raises(ReplayError, match="--budget-ledger"):
        cli.main(["register", "--from-impact", str(out), "--no-worsening", "--out", str(target)])
    assert not target.exists() and indexed == []


# ------------- found while pinning round 1: an approval's identity outlives its ledger's growth


def test_an_approval_keeps_its_identity_as_its_ledger_grows(tmp_path: Path) -> None:
    """PIN, mutant M6 (the approval's identity is the sha256 of its WHOLE ledger): it survived
    the suite, and under it every draw the ledger records would change the approval's identity,
    so a registration bound to it (gap 6) could not be drawn past its first row. The identity is
    the ledger's FIRST line, where the approval's words, cap and opening time are written."""
    from vinci.evals import registry
    b = _budget(tmp_path)
    before = registry.approval_id(b.ledger)
    b.record({"registration": "r" * 64, "out_dir": str(tmp_path / "run"), "usd": 0.0})
    assert registry.approval_id(b.ledger) == before
