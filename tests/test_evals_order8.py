"""Fix request 2, order 8 — the evaluation harness (RG-D9 to RG-D15, and the two harness follow-ups
handed over on issue #1004: STATE row 53 item 6 and row 56). Each test names the defect it pins and
was shown failing on the merge-base before its fix.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "tests" / "fixtures" / "synthesis_gold"


# ------------------------------------------------- RG-D11: the gold's hashes are checked


def _gold_copy(tmp_path: Path) -> Path:
    dst = tmp_path / "gold"
    shutil.copytree(GOLD, dst)
    return dst


def test_the_committed_gold_loads_and_matches_its_manifest() -> None:
    """(+) Every committed gold file equals the sha256 its MANIFEST records (coder_a and coder_b
    split at the DEV half's claim count into their two recorded halves), so the gold loads."""
    from vinci.evals.gold import load_gold
    assert len(load_gold()) == 644


def test_a_label_edit_that_keeps_the_counts_is_refused(tmp_path: Path) -> None:
    """(−) RG-D11: one adjudicated non-material label changed LABEL → SIGN keeps every pinned count
    and moved M-LABEL's and M-SIGN's precision and recall, and `load_gold` raised nothing. The
    edited file no longer equals its recorded sha256: refused before any metric reads it."""
    from vinci.evals.gold import load_gold
    g = _gold_copy(tmp_path)
    rows = [json.loads(x) for x in (g / "adjudicated.jsonl").read_text().splitlines() if x.strip()]
    k = next(i for i, r in enumerate(rows) if r["verdict"] == "LABEL" and not r.get("material"))
    rows[k]["verdict"] = "SIGN"
    (g / "adjudicated.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="adjudicated.jsonl.*sha256"):
        load_gold(g)


def test_an_edit_inside_one_coder_s_half_is_refused(tmp_path: Path) -> None:
    """(−) A coder file is the two recorded halves concatenated: an edit inside either half is
    refused, naming the half whose hash moved."""
    from vinci.evals.gold import load_gold
    g = _gold_copy(tmp_path)
    lines = (g / "coder_b.jsonl").read_text().splitlines(keepends=True)
    lines[-1] = lines[-1].replace('"verdict": "OK"', '"verdict": "LABEL"', 1) if (
        '"verdict": "OK"' in lines[-1]) else lines[-1].replace('"verdict": "', '"verdict": "X', 1)
    (g / "coder_b.jsonl").write_text("".join(lines))
    with pytest.raises(ValueError, match="B_half2.jsonl"):
        load_gold(g)


# ------------------------------------- RG-D15: the model is production's, not a constant


def _page(t: str = "SMPL") -> dict[str, object]:
    """The committed page as a replay accepts it: since #1006 a filed transcript row's words are
    off the page, and the replay refuses such a row (`stripped_pages.replayable` drops them)."""
    from tests.stripped_pages import committed_page, replayable
    page: dict[str, object] = replayable(committed_page(t))
    return page


def test_a_capture_uses_the_model_the_code_under_test_configures(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) RG-D15: the harness's model was a constant (`capture_child.DEFAULT_MODEL`), so a
    candidate that changes `graph_llm_model` captured with the old model and a model change could
    not be measured. The capture now asks the configuration of the code under test."""
    import vinci.config as cfg
    from vinci.evals.capture_child import capture_calls
    monkeypatch.setattr(cfg, "get_config", lambda: cfg.Config(graph_llm_model="claude-test-x"))
    (call,) = capture_calls(_page(), None, draws=1)
    assert call["model"] == "claude-test-x"


def test_the_harness_names_no_model_of_its_own() -> None:
    """(+) No copy of production's model ID is written into the harness: it was a fifth copy,
    which no test pinned. The child's `--model` is a cross-check only, unset by default. The one
    model the harness names is the JUDGE's (`judge.JUDGE_MODEL`): an instrument, not production."""
    import re
    for f in sorted((ROOT / "vinci" / "evals").glob("*.py")):
        found = re.findall(r"""["']claude-[a-z0-9.-]+["']""", f.read_text())
        assert found == ([] if f.name != "judge.py" else found[:1]), f.name
        if f.name == "judge.py":
            assert len(found) == 1 and "JUDGE_MODEL = " + found[0] in f.read_text()
    from vinci.evals import capture_child
    assert not hasattr(capture_child, "DEFAULT_MODEL")


def test_the_judge_s_model_is_its_own_not_production_s(monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) Review round 0: the judge is the harness's measuring instrument, calibrated against the
    gold. Its model followed production's `graph_llm_model`, so a production model change would
    have changed the instrument silently, under the same `JUDGE_VERSION`. It is pinned."""
    import vinci.config as cfg
    from vinci.evals import judge
    monkeypatch.setattr(cfg, "get_config", lambda: cfg.Config(graph_llm_model="claude-test-x"))
    req = judge.judge_request(_page(), [("c1", "a claim")])
    assert req.model == judge.JUDGE_MODEL != "claude-test-x"


# ------------------------------------- RG-D12: the scorer is BASE's, never the candidate's


def _scorer_repo(tmp_path: Path) -> Path:
    """A git repository holding this checkout's scorer files, committed as BASE."""
    import subprocess

    from vinci.evals.compare import SCORER_FILES
    repo = tmp_path / "repo"
    for f in SCORER_FILES:
        (repo / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / f, repo / f)
    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"]):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    return repo


def test_a_checkout_whose_scorer_is_base_s_may_register_and_score(tmp_path: Path) -> None:
    """(+) The scorer files here equal BASE's: the fingerprint returned is BASE's."""
    from vinci.evals.compare import refuse_unless_scored_by_base, scorer_fingerprint
    repo = _scorer_repo(tmp_path)
    assert refuse_unless_scored_by_base("HEAD", root=repo) == scorer_fingerprint(repo)


def test_a_candidate_never_scores_itself(tmp_path: Path) -> None:
    """(−) RG-D12: the scorer was whichever checkout ran `register`, and the metrics read
    production's parsers (`synthesis.py` among the scorer files), so a candidate that edits them
    edited the scorer of its own measurement (fix 4a was scored by its own files, `755044b4`, not
    its parent's, `03e384a3`). A checkout whose scorer files differ from BASE's is refused, naming
    the files."""
    from vinci.evals.compare import refuse_unless_scored_by_base
    from vinci.evals.replay import ReplayError
    repo = _scorer_repo(tmp_path)
    (repo / "vinci/dossier/synthesis.py").write_text(
        (repo / "vinci/dossier/synthesis.py").read_text() + "\n# a candidate's parser edit\n")
    with pytest.raises(ReplayError, match="vinci/dossier/synthesis.py"):
        refuse_unless_scored_by_base("HEAD", root=repo)


def test_register_draw_and_score_each_refuse_a_candidate_scorer() -> None:
    """STRUCTURAL: the CLI calls the check before it registers, before it draws, and before it
    scores (a registration written before this rule, by a candidate's scorer, is refused too)."""
    src = (ROOT / "vinci" / "evals" / "__main__.py").read_text()
    for cmd, check, before in (
            ('a.cmd == "register"', "cm.fixed_scorer(", "cm.register("),
            ('a.cmd in ("compare", "run-compare")', "refuse_unless_registered_scorer(",
             "cm.run_compare("),
            ('a.cmd == "score"', "refuse_unless_registered_scorer(", "cm.score_run(")):
        body = src[src.index(cmd):]
        assert check in body[:body.index(before)], cmd


# ------------------------------------------- row 53 item 6: each arm scored against its own layer

_PHRASE = "the runway is twelve quarters long"


def _arm_reg() -> object:
    from vinci.evals import compare as cm
    return cm.Registration(base_ref="A", cand_ref="B", transforms=("relabel_drawdown_shape",),
                           pages=("NFLX",), draws=5, targets=("M-LABEL",), held_out=(),
                           scorer=cm.scorer_fingerprint())


def _arm_run(tmp_path: Path, reg: object, raw_base: dict[str, object],
             raw_cand: dict[str, object], name: str) -> Path:
    out = tmp_path / name
    out.mkdir()
    (out / "registration.json").write_text(reg.to_json(), encoding="utf-8")  # type: ignore[attr-defined]
    with (out / "draws.jsonl").open("w") as f:
        for cond, raw in (("BASE", raw_base), ("CAND", raw_cand)):
            for n in range(5):
                f.write(json.dumps({"label": f"NFLX:{cond}", "draw": n + 1, "raw": raw,
                                    "stop_reason": "tool_use"}) + "\n")
    return out


def test_each_arm_is_scored_against_the_layer_its_own_request_carried(tmp_path: Path,
        scorer_is_the_fingerprint: None) -> None:
    """(−) STATE row 53 item 6 (handed over on #1004): both arms were scored against the committed
    layer, BASE's, though CAND's request carried words its own transform wrote — so a CAND draw
    quoting them read as "quote: nowhere", an M-ABSENT worsening that was not there. Reproduced
    with BASE's layer for both; scored per arm, it is gone."""
    from vinci.evals import compare as cm
    from vinci.evals.capture_child import pre_synthesis_mech
    page = _page("NFLX")
    base_layer = pre_synthesis_mech(page)
    mc = base_layer.management_commentary
    assert mc is not None and _PHRASE not in (mc.value or "")
    cand_layer = base_layer.model_copy(update={"management_commentary": mc.model_copy(
        update={"value": f"{mc.value} Management: {_PHRASE}."})})
    raw = page["synthesis"]
    assert isinstance(raw, dict)
    cand = {**raw, "key_unknowns": [*raw["key_unknowns"], f"Management said '{_PHRASE}'."]}
    reg = _arm_reg()

    def own(r: object, t: str, cond: str, p: dict[str, object]) -> object:
        return base_layer if cond == "BASE" else cand_layer

    def base_for_both(r: object, t: str, cond: str, p: dict[str, object]) -> object:
        return base_layer

    old = cm.score_run(_arm_run(tmp_path, reg, raw, cand, "old"), reg,  # type: ignore[arg-type]
                       pages={"NFLX": page}, layer_for=base_for_both)  # type: ignore[arg-type]
    new = cm.score_run(_arm_run(tmp_path, reg, raw, cand, "new"), reg,  # type: ignore[arg-type]
                       pages={"NFLX": page}, layer_for=own)  # type: ignore[arg-type]
    absent = "M-ABSENT"
    assert old.metrics[absent].cand_total > old.metrics[absent].base_total   # the tilt
    assert new.metrics[absent].cand_total == new.metrics[absent].base_total  # scored per arm


def test_an_arm_s_layer_is_rebuilt_by_its_own_ref_as_capture_built_it() -> None:
    """(+) `replay.layer_at` runs the transforms in the same child, at the given ref, as
    `capture_at` does: for HEAD it equals the layer the in-process capture hands `synthesize`."""
    from vinci.evals.capture_child import transformed_mech
    from vinci.evals.replay import layer_at
    page = _page("NFLX")
    got = layer_at("HEAD", page, transforms=["relabel_drawdown_shape"])
    want = transformed_mech(page, transforms=["relabel_drawdown_shape"]).model_dump(mode="json")
    assert got == want


def test_with_no_transforms_both_arms_carry_the_committed_layer() -> None:
    """(+) No transform: both requests carried the committed layer, so both arms are scored
    against it, as before — no child is run."""
    from vinci.evals import compare as cm
    from vinci.evals.capture_child import pre_synthesis_mech
    page = _page("NFLX")
    reg = cm.Registration(base_ref="A", cand_ref="B", transforms=(), pages=("NFLX",), draws=5,
                          targets=("M-LABEL",), held_out=(), scorer=cm.scorer_fingerprint())
    for cond in ("BASE", "CAND"):
        assert cm.arm_layer(reg, "NFLX", cond, page) == pre_synthesis_mech(page)


# ------------------------- RG-D14 + RG-D9: a registrations index committed on main, drawn once


def _repo_with_index(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    """A git repository whose `origin/main` holds an index with ``rows``."""
    import subprocess

    from vinci.evals.registry import INDEX
    repo = tmp_path / "repo"
    (repo / INDEX).parent.mkdir(parents=True)
    (repo / INDEX).write_text("".join(json.dumps(r) + "\n" for r in rows))
    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "index"],
                 ["update-ref", "refs/remotes/origin/main", "HEAD"]):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    return repo


def _to_main(repo: Path) -> None:
    """Commit the working copy and make it origin/main, as a docs-only PR's merge does."""
    import subprocess
    for args in (["add", "-A"],
                 ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "merge"],
                 ["update-ref", "refs/remotes/origin/main", "HEAD"]):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _indexed(tmp_path: Path, regs: list[tuple[Any, str]]) -> Path:
    """A repository whose origin/main holds the row `registry.record_registered` writes for each
    (registration, approval): the index derives each row from its registration (#1030 round 2)."""
    from vinci.evals import registry
    repo = _repo_with_index(tmp_path, [])
    for reg, approval in regs:
        registry.record_registered(reg, approval=approval, root=repo)
    _to_main(repo)
    return repo


def _a_comparison(note: str = "one") -> Any:
    """A registered comparison with request pins (no git ref is read)."""
    from vinci.evals import compare as cm
    return cm.Registration(base_ref="a" * 40, cand_ref="b" * 40, transforms=(), pages=("BURL",),
                           draws=5, targets=("M-LABEL",), held_out=(), scorer="f" * 64,
                           requests={"BURL:BASE": "1" * 64, "BURL:CAND": "2" * 64}, note=note)


def _a_build_run(note: str = "one", **over: Any) -> Any:
    """A `register-run` registration of one page (no git ref is read)."""
    from vinci.evals import builds as bd
    kw: dict[str, Any] = {"code_ref": "0" * 40, "transforms": (), "pages": ("NFLX",),
                          "draws": 2, "builds": 3, "min_gap_s": 300.0,
                          "requests": {"NFLX": "1" * 64}, "inputs": {"ciq_root": "/ciq"},
                          "note": note}
    return bd.RunRegistration(**{**kw, **over})


def test_a_registration_main_does_not_hold_is_not_drawn(tmp_path: Path) -> None:
    """(−) RG-D14: "pre-registered before scoring" could not be checked from main, because squash
    merges removed the pre-registration commits. A registration is now a row of a committed index,
    and no paid draw (nor a score) happens until that row is on origin/main: main's own history
    then shows it was registered first."""
    from vinci.evals import registry
    from vinci.evals.replay import ReplayError
    repo = _repo_with_index(tmp_path, [{"event": "registered", "registration": "a" * 64}])
    registry.require_on_main("a" * 64, root=repo)                 # (+) on main: allowed
    with pytest.raises(ReplayError, match="not on origin/main"):
        registry.require_on_main("b" * 64, root=repo)


def test_a_registration_is_drawn_once_across_approvals(tmp_path: Path) -> None:
    """(−) RG-D9: "drawn once" held per approval ledger only, so the same registration was drawn
    again under a second approval. The index records each draw; a second approval is refused."""
    from vinci.evals import registry
    from vinci.evals.replay import ReplayError
    reg = _a_comparison()
    repo = _indexed(tmp_path, [(reg, "approval-1")])
    registry.claim_draw(reg, approval="approval-1", root=repo)
    with pytest.raises(ReplayError, match="drawn once"):
        registry.claim_draw(reg, approval="approval-2", root=repo)
    rows = [json.loads(x) for x in (repo / registry.INDEX).read_text().splitlines()]
    assert [r["event"] for r in rows] == ["registered", "drawn"]


def test_a_build_is_drawn_once_and_a_registration_s_builds_share_one_approval(
        tmp_path: Path) -> None:
    """(−) A `register-run` registration is drawn build by build: each build once, and every
    build under the approval that drew its first."""
    from vinci.evals import registry
    from vinci.evals.replay import ReplayError
    reg = _a_build_run()
    repo = _indexed(tmp_path, [(reg, "ap-1")])
    registry.claim_draw(reg, approval="ap-1", unit="NFLX:1", root=repo)
    registry.claim_draw(reg, approval="ap-1", unit="NFLX:2", root=repo)   # (+) next build
    with pytest.raises(ReplayError, match="drawn once"):
        registry.claim_draw(reg, approval="ap-1", unit="NFLX:1", root=repo)
    with pytest.raises(ReplayError, match="one approval"):
        registry.claim_draw(reg, approval="ap-2", unit="NFLX:3", root=repo)


def test_the_judge_s_test_half_is_read_once_across_approvals(tmp_path: Path) -> None:
    """(−) RG-D9: the judge's TEST half was refused again under one approval and read again under
    a second. The index records the read."""
    from vinci.evals import registry
    from vinci.evals.replay import ReplayError
    repo = _repo_with_index(tmp_path, [])
    registry.claim_judge_test(approval="ap-1", root=repo)
    with pytest.raises(ReplayError, match="TEST half"):
        registry.claim_judge_test(approval="ap-2", root=repo)


def test_the_cli_checks_the_index_before_it_draws_or_scores() -> None:
    """STRUCTURAL: register and register-run write the row; run-compare and run claim the draw
    after requiring the row on main; score and score-run require it; the judge's TEST half is
    claimed before it is read — by `run_half` itself since #1030's review round 2 (F5), so the
    library claims it too."""
    src = (ROOT / "vinci" / "evals" / "__main__.py").read_text()

    def before(cmd: str, check: str, act: str) -> None:
        body = src[src.index(cmd):]
        assert check in body[:body.index(act)], (cmd, check)
    before('a.cmd == "register"', "registry.record_registered(", "return 0")
    before('a.cmd == "register-run"', "registry.record_registered(", "return 0")
    before('a.cmd in ("compare", "run-compare")', "registry.require_on_main(", "cm.run_compare(")
    before('a.cmd in ("compare", "run-compare")', "registry.claim_draw(", "cm.run_compare(")
    before("def _run(", "registry.require_on_main(", "bd.run_build(")
    before("def _run(", "registry.claim_draw(", "bd.run_build(")
    before('a.cmd == "score"', "registry.require_on_main(", "cm.score_run(")
    before('a.cmd == "score-run"', "registry.require_on_main(", "ind.score(")
    judge = (ROOT / "vinci" / "evals" / "judge.py").read_text()
    body = judge[judge.index("def run_half("):]
    assert "registry.claim_judge_test(" in body[:body.index("rp.run_request(")]


def test_the_index_carries_no_path_and_no_text() -> None:
    """(+) The committed index holds shas, refs, pages, counts and dates only: no local path, no
    transcript, no ledger content (CLAUDE.md: commit nothing you would not publish)."""
    from vinci.evals.registry import INDEX
    index = ROOT / INDEX
    assert index.exists()
    for line in index.read_text().splitlines():
        if line.strip():
            assert "/Users/" not in line and "/private/" not in line and len(line) < 2000


# ------------------------------------------- held-out pages: six by a fixed rule, never metric data


def test_the_held_out_pages_are_six_by_the_fixed_rule() -> None:
    """(−) Fix request 2, order 8: no page was held out from the fixes. Six are now held out, by a
    rule fixed before any result: the committed pages outside the panel and outside the gold's
    DEV half (the pages metrics were built on), ordered by sha256 of the ticker; the first six a
    replay can draw — a page with no CIQ transcript (the panel file's own exclusion: TECX, ORKA)
    is passed over and the rule's next pick takes its place (B's check, gap 5). The pool is frozen
    in the file, so a page added later moves nothing."""
    import hashlib
    h = json.loads((ROOT / "vinci" / "evals" / "held_out_pages.json").read_text())
    rows = {r["ticker"]: r for r in json.loads(
        (ROOT / "vinci" / "evals" / "synthesis_panel.json").read_text())["rows"]}
    order = sorted(h["pool"], key=lambda t: hashlib.sha256(t.encode()).hexdigest())
    assert h["pages"] == [t for t in order if rows[t]["transcripts"] >= 1][:6]
    assert h["pages"] == ["NKE", "VITL", "PARR", "WLK", "TJX", "TGT"]
    assert sorted(h["passed_over"]) == ["ORKA", "TECX"]


def test_no_held_out_page_built_a_metric() -> None:
    """(+) The held-out pages are outside every artifact a metric was built or fit on: the panel,
    the gold's DEV half, and the pages M-GAP's gap types were frozen on."""
    h = set(json.loads((ROOT / "vinci" / "evals" / "held_out_pages.json").read_text())["pages"])
    evals = ROOT / "vinci" / "evals"
    panel = set(json.loads((evals / "synthesis_panel.json").read_text())["panel"])
    dev = set(json.loads((GOLD / "MANIFEST.json").read_text())["split"]["dev"]["pages"])
    gaps = json.loads((ROOT / "vinci" / "evals" / "synthesis_gap_types.json").read_text())
    gap_pages = set((gaps.get("pages") or gaps).keys())
    assert not h & panel and not h & dev and not h & gap_pages
    for t in h:   # every one is a committed page
        assert (ROOT / "data" / "dossiers" / t / "dossier.json").exists(), t


# ------------------------------------------------- RG-D13: M-GAP is reported, never a target


def test_m_gap_is_refused_as_a_target() -> None:
    """(−) RG-D13: M-GAP's truth is the candidate's own classifier output (#927's gap types), so
    "M-GAP 37 → 4" measured compliance with the new instruction, not fidelity to the page. Until
    an independent coding exists it is barred as a target (operator, 2026-11-11: "Bar it now")."""
    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    with pytest.raises(ReplayError, match="RG-D13"):
        cm.register("dc5b8787", "b109e26c", targets=["M-GAP"])
    with pytest.raises(ReplayError, match="RG-D13"):
        cm.register("dc5b8787", "b109e26c", targets=["M-LABEL", "M-GAP"])


def test_a_score_prints_m_gap_but_no_decision_reads_it(tmp_path: Path,
        scorer_is_the_fingerprint: None) -> None:
    """(−) A registration from before the bar (as #927's is) that targets M-GAP beside M-LABEL:
    on BURL, a CAND that drops "bleed" improves M-LABEL and leaves M-GAP flat. The decision once
    failed on M-GAP; it now rests on M-LABEL alone, and M-GAP is still printed."""
    from vinci.evals import compare as cm
    page = _page("BURL")
    raw = page["synthesis"]
    text = json.dumps(raw)
    assert "bleed" in text
    cand = json.loads(text.replace("gradual bleed", "decline").replace("bleed", "decline"))
    reg = cm.Registration(base_ref="A", cand_ref="B", transforms=(), pages=("BURL",), draws=5,
                          targets=("M-LABEL", "M-GAP"), held_out=(),
                          scorer=cm.scorer_fingerprint())
    out = tmp_path / "run"
    out.mkdir()
    (out / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    with (out / "draws.jsonl").open("w") as f:
        for cond, r in (("BASE", raw), ("CAND", cand)):
            for n in range(5):
                f.write(json.dumps({"label": f"BURL:{cond}", "draw": n + 1, "raw": r,
                                    "stop_reason": "tool_use"}) + "\n")
    s = cm.score_run(out, reg, pages={"BURL": page})
    assert "M-GAP" in s.metrics and "M-GAP" in cm.score_text(s)
    assert s.ships, s.reasons
    assert not any("M-GAP" in x for x in s.reasons)          # nothing that decides reads it
    assert s.barred == ("M-GAP",) and "RG-D13" in cm.score_text(s)


def test_a_registration_whose_only_target_is_barred_decides_nothing(tmp_path: Path,
        scorer_is_the_fingerprint: None) -> None:
    """(−) #927's shape: M-GAP its only target. It is scored and printed, and with no target left
    to decide, it does not ship — never "ships" on an empty set of targets."""
    from vinci.evals import compare as cm
    page = _page("BURL")
    raw = page["synthesis"]
    reg = cm.Registration(base_ref="A", cand_ref="B", transforms=(), pages=("BURL",), draws=5,
                          targets=("M-GAP",), held_out=(), scorer=cm.scorer_fingerprint())
    out = tmp_path / "run"
    out.mkdir()
    (out / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    with (out / "draws.jsonl").open("w") as f:
        for cond in ("BASE", "CAND"):
            for n in range(5):
                f.write(json.dumps({"label": f"BURL:{cond}", "draw": n + 1, "raw": raw,
                                    "stop_reason": "tool_use"}) + "\n")
    s = cm.score_run(out, reg, pages={"BURL": page})
    assert "M-GAP" in s.metrics and s.barred == ("M-GAP",)
    assert not s.ships and s.decision == cm.DOES_NOT_SHIP


# ------------------------- review round 0: a refused run never consumes its registration (RG-D9)


def test_a_run_compare_refused_at_0_dollars_claims_nothing(tmp_path: Path,
        scorer_is_the_fingerprint: None) -> None:
    """(−) `run-compare` claimed the draw in the index BEFORE `run_compare`'s $0 refusals (a run
    folder already holding draws, moved request bytes, a design already drawn), so one refusal
    left a `drawn` row and the registration could never be drawn. The claim now runs after them;
    (+) a run that passes them claims once, before the first draw."""
    from tests.test_evals_pr2_round2 import _budget, _captured, _FakeSdk, _reg
    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    c = _captured(_page("NFLX"))
    reg = _reg(c, draws=2)
    out = tmp_path / "run"
    out.mkdir()
    (out / "draws.jsonl").write_text("")
    claims: list[int] = []
    sdk = _FakeSdk()
    with pytest.raises(ReplayError, match="already holds draws"):
        cm.run_compare(c, budget=_budget(tmp_path), out_dir=out, registration=reg, sdk=sdk,
                       claim=lambda: claims.append(sdk.calls))
    assert claims == [] and sdk.calls == 0
    cm.run_compare(c, budget=_budget(tmp_path / "b"), out_dir=tmp_path / "fresh",
                   registration=reg, sdk=sdk, claim=lambda: claims.append(sdk.calls))
    assert claims == [0] and sdk.calls == 4


def test_a_build_refused_at_0_dollars_claims_nothing(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) `run` claimed the build's unit after a first `prepare_build` outside the ledger's lock
    (and then captured again inside `run_build`); a refusal inside the lock left the unit
    claimed. The claim is now made by `run_build`, under the lock, after its $0 checks."""
    from tests.test_evals_run_builds import _budget, _Clock, _FakeSdk, _register
    from vinci.evals import builds as bd
    from vinci.evals import replay as rp
    page = _page("NFLX")
    monkeypatch.setattr(rp, "panel_inputs", lambda t, **k: (page, None))
    monkeypatch.setattr(rp, "comps_export", lambda t, **k: None)
    monkeypatch.setattr(rp, "capture_at", lambda ref, p, tx, *, draws=5, transforms=(),
                        comps=None, **k: rp.capture(p, tx, draws=draws, transforms=transforms,
                                                    comps=comps))
    reg = _register(tmp_path)
    moved = bd.RunRegistration(**{**reg.__dict__, "requests": {"NFLX": "0" * 64}})
    budget, sdk, claims = _budget(tmp_path), _FakeSdk(), []
    with pytest.raises(rp.ReplayError, match="registered bytes"):
        bd.run_build(moved, "NFLX", 1, budget=budget, draws_out=tmp_path / "d.jsonl",
                     ciq_root=tmp_path / "ciq", sdk=sdk, clock=_Clock(),
                     claim=lambda: claims.append(sdk.calls))
    assert claims == [] and sdk.calls == 0
    bd.run_build(reg, "NFLX", 1, budget=budget, draws_out=tmp_path / "d.jsonl",
                 ciq_root=tmp_path / "ciq", sdk=sdk, clock=_Clock(),
                 claim=lambda: claims.append(sdk.calls))
    assert claims == [0] and sdk.calls == reg.draws


def test_the_approval_that_read_test_may_resume_it(tmp_path: Path) -> None:
    """(−) `judge.run_half` resumes a stopped TEST run into its own folder under the same
    approval, but the index refused every second claim, so a stopped TEST read could never be
    finished. The approval holding the read may claim it again (no second row); (+) another
    approval is still refused."""
    from vinci.evals import registry
    from vinci.evals.replay import ReplayError
    repo = _repo_with_index(tmp_path, [])
    registry.claim_judge_test(approval="ap-1", root=repo)
    registry.claim_judge_test(approval="ap-1", root=repo)
    rows = [json.loads(x) for x in (repo / registry.INDEX).read_text().splitlines() if x.strip()]
    assert [r["event"] for r in rows] == ["judge_test_read"]
    with pytest.raises(ReplayError, match="TEST half"):
        registry.claim_judge_test(approval="ap-2", root=repo)


# ------------------------------------------------------------- review round 0 (code-review high)


def test_register_pins_its_refs_to_commits(monkeypatch: pytest.MonkeyPatch,
                                           tmp_path: Path) -> None:
    """(−) Review round 0: a registration recorded `--base origin/main` as given, and RG-D14's own
    merge moves main between registering and drawing, so BASE's capture, its layer and its scorer
    would be read at a moved main. `register` resolves both refs to the commits they name."""
    from vinci.evals import __main__ as cli
    from vinci.evals import compare as cm
    from vinci.evals import registry
    seen: dict[str, object] = {}
    monkeypatch.setattr(cm, "fixed_scorer", lambda ref, **k: ("f" * 64, "0" * 40))
    monkeypatch.setattr(cm, "compare_requests", lambda base, cand, **k: seen.setdefault(
        "cap", cm.Captured(base, cand, ())))
    monkeypatch.setattr(cm, "refuse_if_unreached", lambda c: None)
    monkeypatch.setattr(cm, "registered_pages", lambda t: ("NFLX",))
    monkeypatch.setattr(cm, "register", lambda base, cand, **k: seen.update(
        refs=(base, cand)) or cm.Registration(base_ref=base, cand_ref=cand, transforms=(),
                                             pages=("NFLX",), draws=5, targets=("M-LABEL",),
                                             held_out=(), scorer="f" * 64))
    monkeypatch.setattr(cm, "write_registration", lambda reg, out: None)
    monkeypatch.setattr(registry, "record_registered", lambda *a, **k: {})
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps({"approval": {"cap_usd": 1.0, "approved": "test"}}) + "\n")
    cli.main(["register", "--base", "HEAD", "--cand", "HEAD", "--target", "M-LABEL",
              "--budget-ledger", str(ledger), "--out", str(tmp_path / "r.json")])
    import subprocess
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()
    assert seen["refs"] == (head, head)


def test_a_barred_target_keeps_its_place_in_the_registered_correction() -> None:
    """(−) Review round 0: dropping a barred target from Holm's family loosened the rule a
    registration was made under (two targets: the first needs p <= alpha/2; one: alpha). A barred
    target stays in the family at p = 1, its worst case, so its value is never read and the rule
    is never looser than registered."""
    from vinci.evals import compare as cm
    fam = cm.target_family(("M-LABEL", "M-GAP"), {"M-LABEL": 0.04, "M-GAP": 1e-11})
    assert fam == {"M-LABEL": 0.04, "M-GAP": 1.0}
    assert cm.holm(fam, 0.05) == {"M-LABEL": False, "M-GAP": False}   # 0.04 > 0.05 / 2
    assert cm.holm(cm.target_family(("M-LABEL",), {"M-LABEL": 0.04}), 0.05)["M-LABEL"]


# --------------------------------- --from-impact: a registration from an impact run's captures

BASE_953 = "586fdcfdcbf724a7c020a02fd165496bce4c665e"   # #953's parent, on main
CAND_953 = "7ec84833a60fbdc14580a5a8871585f4f8a1e0a8"   # #953's squash, on main


def _impact_export(tmp_path: Path, transcript: str | None = None
                   ) -> tuple[Path, dict[str, object]]:
    """An export in impact-check's format (`impact-captures-format.md`): per arm and page a $0
    build (`built.json`), the layer its synthesis received (`layer.json`) and the request it sent
    (`request.json`, one call), each hashed in `manifest.json`. CAND's layer carries a phrase
    BASE's does not, as #953's fresh builds carried a peer block the frozen page does not."""
    import hashlib

    from vinci.evals import replay as rp
    from vinci.evals.capture_child import pre_synthesis_mech
    page = _page("NFLX")
    base_layer = pre_synthesis_mech(page)
    mc = base_layer.management_commentary
    assert mc is not None
    cand_layer = base_layer.model_copy(update={"management_commentary": mc.model_copy(
        update={"value": f"{mc.value} Management: {_PHRASE}."})})
    out = tmp_path / "export"
    pages: dict[str, dict[str, object]] = {"NFLX": {"request_differs": True}}
    for arm, side, layer in (("BASE", "base", base_layer), ("CAND", "head", cand_layer)):
        d = out / side / "NFLX"
        d.mkdir(parents=True)
        built = {**page, "mechanical": json.loads(layer.model_dump_json())}
        (d / "built.json").write_text(json.dumps(built))
        (d / "layer.json").write_text(layer.model_dump_json())
        kwargs = rp.capture(built, transcript, draws=1).kwargs
        (d / "request.json").write_text(json.dumps(kwargs))
        sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731
        pages["NFLX"][arm] = {"built_sha256": sha((d / "built.json").read_bytes()),
                              "layer_sha256": sha((d / "layer.json").read_bytes()),
                              "request_wire_sha256": sha(rp.wire(kwargs).encode()),
                              "recapture_equal": True}
    (out / "manifest.json").write_text(json.dumps({
        "base": {"sha": BASE_953}, "cand": {"sha": CAND_953}, "pages": pages,
        "inputs": {"data_ref": CAND_953}}))
    return out, page


def test_a_registration_is_built_from_an_impact_export(tmp_path: Path) -> None:
    """(+) `captured_from_impact` reads the export as the comparison: its two commits, each
    page's two requests (pinned by the manifest's wire sha256), and the export's identity."""
    from vinci.evals import compare as cm
    out, _ = _impact_export(tmp_path)
    cap = cm.captured_from_impact(out)
    m = json.loads((out / "manifest.json").read_text())
    assert (cap.base_ref, cap.cand_ref) == (BASE_953, CAND_953) and cap.reaches
    assert cm.request_pins(cap) == {f"NFLX:{a}": m["pages"]["NFLX"][a]["request_wire_sha256"]
                                    for a in ("BASE", "CAND")}
    assert cap.inputs["impact"]["pages"] == m["pages"]


def test_an_impact_export_whose_file_moved_is_refused(tmp_path: Path) -> None:
    """(−) Every file is checked against the manifest's sha256: a layer edited after the run is
    refused, never scored."""
    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    out, _ = _impact_export(tmp_path)
    p = out / "head" / "NFLX" / "layer.json"
    p.write_text(p.read_text().replace(_PHRASE, "something else entirely here"))
    with pytest.raises(ReplayError, match="layer.json.*sha256"):
        cm.captured_from_impact(out)


def test_an_impact_arm_is_scored_against_its_own_fresh_layer(tmp_path: Path,
        scorer_is_the_fingerprint: None) -> None:
    """(−) The #953 retrospective's blocker (coordinator, 2026-11-11): `score_run` scored every
    draw against the FROZEN panel page, but an impact run's requests were built fresh on today's
    inputs and carried another layer. An impact registration's arms are scored against their own
    `layer.json` and `built.json`, never the frozen page (NFLX is no panel page: the frozen read
    fails outright)."""
    from vinci.evals import compare as cm
    out, page = _impact_export(tmp_path)
    cap = cm.captured_from_impact(out)
    reg = cm.Registration(base_ref=BASE_953, cand_ref=CAND_953, transforms=(), pages=("NFLX",),
                          draws=5, targets=(), held_out=(), scorer=cm.scorer_fingerprint(),
                          no_worsening=True, requests=cm.request_pins(cap), inputs=cap.inputs)
    raw = page["synthesis"]
    assert isinstance(raw, dict)
    cand = {**raw, "key_unknowns": [*raw["key_unknowns"], f"Management said '{_PHRASE}'."]}
    run = _arm_run(tmp_path, reg, raw, cand, "run")
    s = cm.score_run(run, reg)
    assert s.metrics["M-ABSENT"].cand_total == s.metrics["M-ABSENT"].base_total


def test_register_and_run_compare_read_an_impact_export_not_a_replay() -> None:
    """STRUCTURAL: `register --from-impact` builds the comparison from the export (no
    `compare_requests` replay), and `run-compare` of an impact registration rebuilds it from the
    same export, so the bytes drawn are the bytes the impact run captured."""
    src = (ROOT / "vinci" / "evals" / "__main__.py").read_text()
    assert '"--from-impact"' in src
    body = src[src.index('a.cmd == "register"'):]
    body = body[:body.index("return 0")]
    assert "cm.captured_from_impact(" in body
    rc = src[src.index('a.cmd in ("compare", "run-compare")'):]
    assert "cm.captured_from_impact(" in rc[:rc.index("cm.run_compare(")]


# ------------------- RG-D12 for a retrospective: a merged candidate is scored by main's scorer


def _scorer_history(tmp_path: Path) -> tuple[Path, str, str]:
    """A repository holding the scorer files: BASE, then CAND editing `synthesis.py`."""
    import subprocess
    repo = _scorer_repo(tmp_path)

    def git(*a: str) -> str:
        return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True,
                              text=True).stdout.strip()
    base = git("rev-parse", "HEAD")
    f = repo / "vinci/dossier/synthesis.py"
    f.write_text(f.read_text() + "\n# the candidate's edit\n")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "cand")
    return repo, base, git("rev-parse", "HEAD")


def _composite(tmp_path: Path) -> tuple[Path, str, str]:
    """BASE, then MAIN moving both a production file (`synthesis.py`) and the harness
    (`compare.py`) — #953's case, where main moved after BASE — with origin/main at MAIN, and the
    checkout holding BASE's production file under MAIN's harness: the composite #953 needs."""
    import subprocess
    repo, base, _ = _scorer_history(tmp_path)          # CAND's commit edits synthesis.py

    def git(*a: str) -> str:
        return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True,
                              text=True).stdout.strip()
    h = repo / "vinci/evals/compare.py"
    h.write_text(h.read_text() + "\n# main's newer harness\n")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "main")
    main = git("rev-parse", "HEAD")
    git("update-ref", "refs/remotes/origin/main", main)
    git("checkout", "-q", base, "--", "vinci/dossier/synthesis.py")
    return repo, base, main


def test_the_fixed_scorer_is_base_s_production_under_main_s_harness(tmp_path: Path) -> None:
    """(+) RG-D12, merged with B's scope (operator, 2026-11-11): BASE's production files, and
    origin/main's harness at registration, recorded as `scorer_ref`. One rule for a prospective
    change and a retrospective (#953) alike."""
    from vinci.evals import compare as cm
    repo, base, main = _composite(tmp_path)
    assert cm.fixed_scorer(base, root=repo) == (cm.scorer_fingerprint(repo), main)


def test_a_harness_main_does_not_hold_is_refused(tmp_path: Path) -> None:
    """(−) A candidate cannot bring its own harness either: a checkout whose harness files are not
    origin/main's is refused, naming them."""
    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    repo, base, _ = _composite(tmp_path)
    h = repo / "vinci/evals/compare.py"
    h.write_text(h.read_text() + "\n# a candidate's harness edit\n")
    with pytest.raises(ReplayError, match=r"vinci/evals/compare\.py"):
        cm.fixed_scorer(base, root=repo)


def test_the_impact_child_names_only_what_the_capture_module_has() -> None:
    """(−) `vinci/impact/child.py` loads this checkout's `capture_child.py` by path and read
    `capture.DEFAULT_MODEL`, which RG-D15 removes: an AttributeError the day the fallback ran."""
    import re

    from vinci.evals import capture_child
    src = (ROOT / "vinci" / "impact" / "child.py").read_text()
    for name in sorted(set(re.findall(r"\bcapture\.([A-Za-z_]\w*)", src))):
        assert hasattr(capture_child, name), name


# ------------------------------------------------- review round 0 (code-review high, 2026-11-11)


def _rewrite_manifest(out: Path, edit: object) -> None:
    m = json.loads((out / "manifest.json").read_text())
    edit(m)  # type: ignore[operator]
    (out / "manifest.json").write_text(json.dumps(m))


def test_an_impact_arm_the_export_did_not_prove_is_refused(tmp_path: Path) -> None:
    """(−) The manifest records per arm whether re-capturing from its `layer.json` gave its
    request byte for byte (`recapture_equal`). An arm it did not prove, or that records no proof,
    is refused: it would be scored against a layer its request may not have carried."""
    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    out, _ = _impact_export(tmp_path)
    _rewrite_manifest(out, lambda m: m["pages"]["NFLX"]["CAND"].update(recapture_equal=False))
    with pytest.raises(ReplayError, match="recapture_equal"):
        cm.captured_from_impact(out)
    _rewrite_manifest(out, lambda m: m["pages"]["NFLX"]["CAND"].pop("recapture_equal"))
    with pytest.raises(ReplayError, match="records no"):
        cm.captured_from_impact(out)
    _rewrite_manifest(out, lambda m: m["pages"]["NFLX"].pop("CAND"))
    with pytest.raises(ReplayError, match="NFLX:CAND records no"):
        cm.captured_from_impact(out)


def test_an_impact_arm_s_transcript_is_the_text_sent_not_its_section_header(
        tmp_path: Path) -> None:
    """(−) The transcripts section opens with an instruction header ("Derive NO numbers FROM THIS
    TEXT ..."). Read as the transcript, M-ABSENT would call a quote of those instruction words
    "transcript-only" where the frozen path, holding the raw text, calls it "nowhere"."""
    from vinci.evals import compare as cm
    text = "--- Q3 call ---\nManagement: the quarter was fine."
    out, _ = _impact_export(tmp_path, transcript=text)
    cap = cm.captured_from_impact(out)
    reg = cm.Registration(base_ref=BASE_953, cand_ref=CAND_953, transforms=(), pages=("NFLX",),
                          draws=5, targets=(), held_out=(), scorer=cm.scorer_fingerprint(),
                          no_worsening=True, requests=cm.request_pins(cap), inputs=cap.inputs)
    for cond in ("BASE", "CAND"):
        tx = cm.impact_arm(reg, "NFLX", cond)[2]
        assert tx is not None and tx.startswith("--- Q3 call ---") and text in tx
        assert "Derive NO numbers" not in tx


def test_register_from_impact_refuses_a_chosen_page(tmp_path: Path) -> None:
    """(−) `--ticker` beside `--from-impact` was silently replaced by the export's pages, so a
    registration the operator limited to one page was written over all of them."""
    from vinci.evals import __main__ as cli
    from vinci.evals import replay as rp
    from vinci.evals.replay import ReplayError
    out, _ = _impact_export(tmp_path)
    ledger = rp.Budget.open(tmp_path / "ledger.jsonl", cap_usd=1.0, approval="test").ledger
    with pytest.raises(ReplayError, match="--ticker"):
        cli.main(["register", "--from-impact", str(out), "--ticker", "NFLX", "--no-worsening",
                  "--budget-ledger", str(ledger), "--out", str(tmp_path / "r.json")])


def test_a_registered_scorer_ref_that_is_an_unmerged_candidate_is_refused(
        tmp_path: Path) -> None:
    """(−) RG-D12 at the draw and the score: a `scorer_ref` (the registered harness) that is not a
    commit on origin/main — a candidate's own — is refused even from a checkout holding exactly
    that scorer; (+) a harness on origin/main passes."""
    import subprocess

    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    repo, base, main = _composite(tmp_path)
    reg = cm.Registration(base_ref=base, cand_ref=main, transforms=(), pages=("NFLX",), draws=5,
                          targets=(), held_out=(), scorer=cm.scorer_fingerprint(repo),
                          no_worsening=True, scorer_ref=main)
    subprocess.run(["git", "-C", str(repo), "update-ref", "refs/remotes/origin/main", base],
                   check=True)
    with pytest.raises(ReplayError, match="not on origin/main"):
        cm.refuse_unless_registered_scorer(reg, root=repo)
    subprocess.run(["git", "-C", str(repo), "update-ref", "refs/remotes/origin/main", main],
                   check=True)
    cm.refuse_unless_registered_scorer(reg, root=repo)

def test_the_gold_report_never_scores_a_held_out_page(monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) B's check, gap 5: `python -m vinci.evals gold` — the command a metric change re-runs
    (RUNBOOKS §n step 7) — scored the held-out pages' TEST claims. It scores without them, and
    says how many it left out."""
    from vinci.evals import gold as gd
    from vinci.evals import report
    held = set(json.loads((ROOT / "vinci" / "evals" / "held_out_pages.json").read_text())["pages"])
    seen: list[set[str]] = []
    real = gd.precision_recall

    def spy(metric: str, cls: str, gold: list[gd.GoldClaim], fired: set[str], half: str) -> object:
        seen.append({g.page for g in gold})
        return real(metric, cls, gold, fired, half)
    monkeypatch.setattr(gd, "precision_recall", spy)
    text = report.gold_report()
    assert seen and all(not (pages & held) for pages in seen)
    assert "held out" in text


# ------------------------------------------------ B's check, gaps 3 and 6: the index's approvals


def test_pr2_s_test_read_is_on_record_so_a_second_is_refused(tmp_path: Path) -> None:
    """(−) B's check, gap 3: the index shipped empty, so `claim_judge_test` admitted a first TEST
    read from any approval — though PR 2 already read the 644-claim gold's TEST half on
    2026-11-06. That read is in the committed index, marked as recorded after the fact, and a
    TEST read under any approval is refused."""
    import subprocess

    from vinci.evals import registry
    from vinci.evals.replay import ReplayError
    rows = [json.loads(x) for x in (ROOT / registry.INDEX).read_text().splitlines() if x.strip()]
    (pr2,) = [r for r in rows if r["event"] == "judge_test_read"]
    assert pr2["read_at"].startswith("2026-11-06") and pr2["recorded_after_the_fact"] is True
    repo = _repo_with_index(tmp_path, rows)
    subprocess.run(["git", "-C", str(repo), "status"], check=True, capture_output=True)
    with pytest.raises(ReplayError, match="TEST half"):
        registry.claim_judge_test(approval="a-new-approval", root=repo)


def test_a_registration_is_drawn_only_under_the_approval_it_is_bound_to(tmp_path: Path) -> None:
    """(−) B's check, gap 6: "drawn once across approvals" saw only the draws in this checkout or
    on origin/main, so a second approval in another checkout could draw before the first's rows
    merged. The registered row, which must be on main before any draw, names its approval's
    sha256; a draw under any other approval is refused wherever it runs."""
    from vinci.evals import registry
    from vinci.evals.replay import ReplayError
    reg = _a_comparison()
    repo = _indexed(tmp_path, [(reg, "ap-1")])
    with pytest.raises(ReplayError, match="bound to approval"):
        registry.claim_draw(reg, approval="ap-2", root=repo)
    registry.claim_draw(reg, approval="ap-1", root=repo)        # (+) its own approval


def test_a_registration_names_its_approval() -> None:
    """(−) Gap 6: `register` and `register-run` bind the row to the approval (`--budget-ledger`),
    so the approval is opened before the registration, as RUNBOOKS §n step 4 orders."""
    import inspect

    from vinci.evals import registry
    assert "approval" in inspect.signature(registry.record_registered).parameters
    src = (ROOT / "vinci" / "evals" / "__main__.py").read_text()
    calls = [i for i in range(len(src)) if src.startswith("registry.record_registered(", i)]
    assert len(calls) == 2
    for i in calls:   # the registration itself: its key is derived from it (#1030 round 2, F1)
        call = src[i:src.index(")", i) + 1]
        assert call in ("registry.record_registered(reg, approval=approval)",
                        "registry.record_registered(breg, approval=approval)"), call
    for cmd in ('a.cmd == "register"', 'a.cmd == "register-run"'):
        body = src[src.index(cmd):]
        body = body[:body.index("return 0")]
        assert body.index("registry.approval_id(a.budget_ledger)") < body.index(
            "write_registration(")   # #1030 review round 1, item 7


@pytest.fixture()
def scorer_is_the_fingerprint(monkeypatch: pytest.MonkeyPatch) -> None:
    """RG-D12 whole is stood in by the fingerprint comparison, for a test of ANOTHER rule under
    a placeholder ref or #953's BASE (`tests/evals_scorer_stub.py`). Named, never autouse: this
    module holds RG-D12's own pins."""
    from tests.evals_scorer_stub import fingerprint_only
    from vinci.evals import compare as cm
    monkeypatch.setattr(cm, "refuse_unless_registered_scorer", fingerprint_only)
