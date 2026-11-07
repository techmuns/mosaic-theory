"""#926 review round 2 (the coordinator's, the last): the replication rule's holes, closed.

F1: a DESIGN is drawn once per approval, whatever its note or inputs, and a first run's one
replication is drawn once too. F2: a replication is scored only as one of a real first run that the
ledger records. F3: that first run is complete, registered under its sha, and its own
ledger-backed score decided "replication required". F4: every design field counts, and Holm across
two targets is applied through `score_run`. Every test here failed on f6318798.
"""
from __future__ import annotations

import dataclasses
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from vinci.evals import compare as cm
from vinci.evals import replay as rp

ROOT = Path(__file__).resolve().parents[1]
QUOTE = "Management said 'we will double the dividend next spring'."


@pytest.fixture(scope="module")
def nflx() -> dict[str, Any]:
    page: dict[str, Any] = json.loads((ROOT / "data/dossiers/NFLX/dossier.json").read_text())
    return page


def _reg(**over: Any) -> cm.Registration:
    base: dict[str, Any] = {"base_ref": "A", "cand_ref": "B", "transforms": (), "pages": ("NFLX",),
                            "draws": 5, "targets": ("M-LABEL",), "held_out": (),
                            "scorer": cm.scorer_fingerprint(), "ship_alpha": 0.01,
                            "rule": cm.REPLICATION_RULE}
    return cm.Registration(**{**base, **over})


def _clean(raw: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = json.loads(json.dumps(raw).replace("gradual bleed", "decline")
                                     .replace("bleed", "decline"))
    return out


def _quoted(raw: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = json.loads(json.dumps(raw))
    out["key_unknowns"] = [*out["key_unknowns"], QUOTE]
    return out


def _run(path: Path, reg: cm.Registration, base: list[Any], cand: list[Any]) -> Path:
    path.mkdir(parents=True)
    (path / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    with (path / "draws.jsonl").open("w") as f:
        for cond, raws in (("BASE", base), ("CAND", cand)):
            for raw in raws:
                f.write(json.dumps({"label": f"NFLX:{cond}", "raw": raw,
                                    "stop_reason": "tool_use"}) + "\n")
    return path


def _ledger(tmp_path: Path) -> rp.Budget:
    return rp.Budget.open(tmp_path / "ledger.jsonl", cap_usd=5.0, approval="operator: test")


def _record(b: rp.Budget, reg: cm.Registration, folder: Path) -> None:
    b.record({"registration": reg.sha, "out_dir": str(folder), "usd": 0.0})


def _in_band(raw: dict[str, Any]) -> tuple[list[Any], list[Any]]:
    """Four of five CAND draws drop the label: M-LABEL p_lower 6/252 = 0.024."""
    return [raw] * 5, [_clean(raw)] * 4 + [raw]


def _scored_first(tmp_path: Path, nflx: dict[str, Any], first: cm.Registration | None = None,
                  ) -> tuple[cm.Registration, Path, rp.Budget]:
    first = first or _reg()
    b = _ledger(tmp_path)
    folder = _run(tmp_path / "first", first, *_in_band(nflx["synthesis"]))
    _record(b, first, folder)
    s = cm.score_run(folder, first, pages={"NFLX": nflx}, ledger=b.ledger)
    assert s.decision == cm.REPLICATION_REQUIRED
    return first, folder, b


# ---------------------------------------------------- F1. a design is drawn once per approval

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


def _captured(nflx: dict[str, Any]) -> cm.Captured:
    base = rp.capture(nflx, None, draws=2)
    c = cm.Captured("A", "B", ())
    c.requests[("NFLX", "BASE")] = base
    c.requests[("NFLX", "CAND")] = rp.Request({**base.kwargs, "system": base.system + " "})
    c.diffs.append(cm.PageDiff("NFLX", False, 0, False, {}, {}))
    return c


@pytest.mark.parametrize("change", [{"note": "the same design, other words"},
                                    {"inputs": {"ciq_root": "/ciq/"}}])
def test_a_design_drawn_once_is_not_drawn_again_under_another_sha(
        tmp_path: Path, nflx: dict[str, Any], change: dict[str, Any]) -> None:
    """The reviewer's probes: the first run's design re-registered with only `--note` changed,
    and `/ciq` against `/ciq/` — two shas over one design, each drawable once."""
    c = _captured(nflx)
    first = _reg(draws=2, requests=cm.request_pins(c), inputs={"ciq_root": "/ciq"})
    b = _ledger(tmp_path)
    sdk = _FakeSdk()
    cm.run_compare(c, budget=b, out_dir=tmp_path / "first", registration=first, sdk=sdk)
    again = dataclasses.replace(first, **change)
    assert again.sha != first.sha
    with pytest.raises(rp.ReplayError, match="design was already drawn"):
        cm.run_compare(c, budget=b, out_dir=tmp_path / "again", registration=again, sdk=sdk)
    assert sdk.calls == 4 and not (tmp_path / "again").exists()


def test_a_first_run_has_one_replication_drawn_once(tmp_path: Path,
                                                    nflx: dict[str, Any]) -> None:
    """Two replications of one first run, differing only in `--note`, were both accepted."""
    c = _captured(nflx)
    first = _reg(draws=2, requests=cm.request_pins(c))
    b = _ledger(tmp_path)
    sdk = _FakeSdk()
    cm.run_compare(c, budget=b, out_dir=tmp_path / "first", registration=first, sdk=sdk)
    rep = dataclasses.replace(first, replicates=first.sha)
    cm.run_compare(c, budget=b, out_dir=tmp_path / "rep", registration=rep, sdk=sdk)
    assert sdk.calls == 8                                      # the one replication is drawn
    rep2 = dataclasses.replace(rep, note="another replication")
    with pytest.raises(rp.ReplayError, match="design was already drawn"):
        cm.run_compare(c, budget=b, out_dir=tmp_path / "rep2", registration=rep2, sdk=sdk)
    assert sdk.calls == 8


def test_a_recorded_run_must_be_checkable(tmp_path: Path, nflx: dict[str, Any]) -> None:
    c = _captured(nflx)
    reg = _reg(draws=2, requests=cm.request_pins(c))
    b = _ledger(tmp_path)
    b.record({"registration": "e" * 64, "out_dir": str(tmp_path / "gone"), "usd": 0.0})
    with pytest.raises(rp.ReplayError, match="no registration.json"):
        cm.run_compare(c, budget=b, out_dir=tmp_path / "r", registration=reg, sdk=_FakeSdk())


def test_the_ciq_root_is_recorded_resolved(tmp_path: Path) -> None:
    empty = {"panel": [], "pages": {}}
    spellings = [tmp_path, Path(f"{tmp_path}/"), tmp_path / "." / "x" / ".."]
    got = {cm.compare_requests("A", "B", panel=empty, ciq_root=p).inputs["ciq_root"]
           for p in spellings}
    assert got == {str(tmp_path.resolve())}


# ------------------------------------------- F2. a replication is one of a real first run

def test_a_replication_ships_at_alpha_as_one_of_its_recorded_first_run(
        tmp_path: Path, nflx: dict[str, Any]) -> None:
    raw = nflx["synthesis"]
    first, _folder, b = _scored_first(tmp_path, nflx)
    rep = _reg(replicates=first.sha)
    folder = _run(tmp_path / "rep", rep, *_in_band(raw))
    _record(b, rep, folder)
    s = cm.score_run(folder, rep, pages={"NFLX": nflx}, ledger=b.ledger)
    assert s.decision == "replicated: ships" and s.ships
    flat = _reg(replicates=first.sha, note="a second, flat")
    folder2 = _run(tmp_path / "rep2", flat, [raw] * 5, [raw] * 5)
    _record(b, flat, folder2)
    s2 = cm.score_run(folder2, flat, pages={"NFLX": nflx}, ledger=b.ledger)
    assert s2.decision == cm.DOES_NOT_SHIP and any("does not replicate" in r for r in s2.reasons)


def test_a_replication_of_no_recorded_first_run_is_never_scored(
        tmp_path: Path, nflx: dict[str, Any]) -> None:
    """The bypass: a hand-written registration with `replicates="0"*64` scored "replicated:
    ships" at p 0.0238."""
    rep = _reg(replicates="0" * 64)
    b = _ledger(tmp_path)
    folder = _run(tmp_path / "rep", rep, *_in_band(nflx["synthesis"]))
    _record(b, rep, folder)
    with pytest.raises(rp.ReplayError, match="0 run"):
        cm.score_run(folder, rep, pages={"NFLX": nflx}, ledger=b.ledger)
    with pytest.raises(rp.ReplayError, match="approval's ledger"):
        cm.score_run(folder, rep, pages={"NFLX": nflx})


def test_a_replication_of_another_design_is_never_scored(tmp_path: Path,
                                                         nflx: dict[str, Any]) -> None:
    first, _folder, b = _scored_first(tmp_path, nflx)
    rep = _reg(replicates=first.sha, targets=("M-ABSENT",))
    folder = _run(tmp_path / "rep", rep, *_in_band(nflx["synthesis"]))
    _record(b, rep, folder)
    with pytest.raises(rp.ReplayError, match=r"these differ: \['targets'\]"):
        cm.score_run(folder, rep, pages={"NFLX": nflx}, ledger=b.ledger)


# ------------------------------------------ F3. the first run is complete and decided the band

def _history() -> None:
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", "b109e26c^{commit}"],
                      capture_output=True).returncode != 0:
        pytest.skip("needs the full history")


def _real_first(**over: Any) -> cm.Registration:
    return cm.register("dc5b8787", "b109e26c", targets=["M-LABEL"], pages=["NFLX"],
                       ship_alpha=0.01, **over)


def _replicate(first: cm.Registration, b: rp.Budget, **over: Any) -> cm.Registration:
    return cm.register("dc5b8787", "b109e26c", targets=["M-LABEL"], pages=["NFLX"],
                       ship_alpha=0.01, replicates=first, ledger=b.ledger, **over)


def test_a_replication_registers_against_a_complete_first_run(tmp_path: Path,
                                                              nflx: dict[str, Any]) -> None:
    _history()
    first, _folder, b = _scored_first(tmp_path, nflx, _real_first())
    rep = _replicate(first, b)
    assert rep.replicates == first.sha and rep.sha != first.sha
    with pytest.raises(rp.ReplayError, match="approval's ledger"):
        cm.register("dc5b8787", "b109e26c", targets=["M-LABEL"], pages=["NFLX"],
                    ship_alpha=0.01, replicates=first)
    with pytest.raises(rp.ReplayError, match="itself a replication"):
        _replicate(rep, b)
    with pytest.raises(rp.ReplayError, match=r"these differ: \['draws'\]"):
        _replicate(first, b, draws=4)


def _first_folder(tmp_path: Path, first: cm.Registration, *, registered: cm.Registration,
                  rows: int, log: list[dict[str, Any]]) -> rp.Budget:
    folder = tmp_path / "first"
    folder.mkdir()
    (folder / "registration.json").write_text(registered.to_json(), encoding="utf-8")
    (folder / "draws.jsonl").write_text("".join('{"label": "NFLX:BASE"}\n' for _ in range(rows)))
    (folder / "score_log.jsonl").write_text("".join(json.dumps(r) + "\n" for r in log))
    b = _ledger(tmp_path)
    b.record({"registration": first.sha, "out_dir": str(folder), "usd": 0.0})
    return b


def test_a_folder_holding_another_registration_is_not_the_first_run(tmp_path: Path) -> None:
    """C14: the folder/sha check dropped."""
    _history()
    first = _real_first()
    other = _real_first(note="another registration")
    b = _first_folder(tmp_path, first, registered=other, rows=10, log=[
        {"registration": first.sha, "decision": cm.REPLICATION_REQUIRED, "ledger": "x"}])
    with pytest.raises(rp.ReplayError, match="holds registration"):
        _replicate(first, b)


def test_another_registrations_score_rows_never_count(tmp_path: Path) -> None:
    """C15: another registration's rows counted."""
    _history()
    first = _real_first()
    b = _first_folder(tmp_path, first, registered=first, rows=10, log=[   # the LAST row is foreign
        {"registration": first.sha, "decision": "ships", "ledger": "x"},
        {"registration": "c" * 64, "decision": cm.REPLICATION_REQUIRED, "ledger": "x"}])
    with pytest.raises(rp.ReplayError, match="decided 'ships'"):
        _replicate(first, b)


@pytest.mark.parametrize(("rows", "log", "match"), [
    (0, [], "0 run"),                                        # a folder with no draws
    (9, [], "holds 9 draws"),                                # an incomplete run
    (10, [{"decision": cm.REPLICATION_REQUIRED, "ledger": None}], "never scored with a ledger"),
])
def test_a_first_run_must_be_complete_and_scored_with_its_ledger(
        tmp_path: Path, rows: int, log: list[dict[str, Any]], match: str) -> None:
    _history()
    first = _real_first()
    b = _first_folder(tmp_path, first, registered=first, rows=rows,
                      log=[{"registration": first.sha, **r} for r in log])
    with pytest.raises(rp.ReplayError, match=match):
        _replicate(first, b)


# ---------------------------------------------- F4. every design field; Holm over two targets

#: Written out, not read from `cm.DESIGN_FIELDS`, so a field dropped from it fails here.
DESIGN = ["base_ref", "cand_ref", "transforms", "pages", "draws", "targets", "alpha",
          "ship_alpha", "scorer", "requests", "no_worsening", "rule"]


@pytest.mark.parametrize("name", DESIGN)
def test_every_design_field_makes_another_design(name: str) -> None:
    a = SimpleNamespace(**{k: getattr(_reg(), k) for k in DESIGN})
    b = SimpleNamespace(**{**a.__dict__, name: ("changed", getattr(a, name))})
    assert cm.design_differs(a, b) == [name]


def test_words_inputs_and_the_link_are_not_the_design() -> None:
    a = _reg()
    b = dataclasses.replace(a, note="words", inputs={"ciq_root": "/x"}, held_out=("NFLX",),
                            replicates="f" * 64)
    assert cm.design_differs(a, b) == [] and a.sha != b.sha


def test_a_replication_with_other_request_bytes_is_another_design(
        tmp_path: Path, nflx: dict[str, Any]) -> None:
    """C3: `requests` dropped from the design check."""
    _history()

    def captured(system: str) -> cm.Captured:
        c = cm.Captured("dc5b8787", "b109e26c", ())
        c.requests[("NFLX", "BASE")] = c.requests[("NFLX", "CAND")] = rp.Request(
            {"system": system})
        return c
    first, _folder, b = _scored_first(tmp_path, nflx, _real_first(captured=captured("x")))
    with pytest.raises(rp.ReplayError, match=r"these differ: \['requests'\]"):
        _replicate(first, b, captured=captured("y"))


@pytest.mark.parametrize(("cand", "decision"), [
    ("both", "ships"),                              # M-LABEL 0.004, M-ABSENT 0.004
    ("absent_only", cm.DOES_NOT_SHIP),              # M-LABEL 1: one target fails
    ("label_in_band", cm.REPLICATION_REQUIRED),     # M-LABEL 0.024, M-ABSENT 0.004
])
def test_holm_over_two_targets_through_score_run(tmp_path: Path, nflx: dict[str, Any],
                                                 cand: str, decision: str) -> None:
    """C10 (`any` for `all`) and the Holm step: with two targets the smaller p is held to
    ship_alpha/2 and the other to ship_alpha; every target must pass for the run to ship."""
    raw = nflx["synthesis"]
    reg = _reg(targets=("M-LABEL", "M-ABSENT"))
    base = [_quoted(raw)] * 5
    cands = {"both": [_clean(raw)] * 5, "absent_only": [raw] * 5,
             "label_in_band": [_clean(raw)] * 4 + [raw]}[cand]
    s = cm.score_run(_run(tmp_path / "r", reg, base, cands), reg, pages={"NFLX": nflx})
    assert s.metrics["M-ABSENT"].p_lower == pytest.approx(1 / 252)
    assert s.decision == decision, (s.metrics["M-LABEL"].p_lower, s.reasons)


# ------------------------------------------------ F7. the scorer fingerprint covers the score

def test_the_scorer_fingerprint_covers_what_the_score_runs() -> None:
    """`pre_synthesis_mech` builds the layer a draw is scored against, `panel_inputs` and the panel
    file give the inputs, and the schemas validate the layer: a change to any moves a score."""
    for f in ("vinci/evals/capture_child.py", "vinci/evals/replay.py",
              "vinci/evals/synthesis_panel.json", "vinci/dossier/schemas.py",
              "vinci/evals/metrics.py", "vinci/evals/compare.py", "vinci/dossier/mechanical.py"):
        assert f in cm.SCORER_FILES, f
        assert (ROOT / f).exists()


# ------------------------------------------------- F8. the print row's basis, read in one place

def test_the_cadence_basis_is_read_by_one_helper() -> None:
    from vinci.evals import variants as vr
    basis = "median 84d gap over 23 results 8-Ks; last print 2026-10-29"
    assert vr.cadence_basis(f"cadence: EDGAR submissions ({basis})") == basis
    assert vr.cadence_basis(f"cadence: EDGAR submissions ({basis}) · guide: 8-K 0001 ex99") == basis
    for bad in ("CIQ capital-structure panel (maturity_date)",
                f"cadence: EDGAR submissions ({basis}",
                ""):
        with pytest.raises(vr.TransformError, match="not the cadence read"):
            vr.cadence_basis(bad)


BLEED = ["The share price shows a gradual bleed.", "A slow bleed in the multiple continues."]
QUOTES = [QUOTE, "The CFO said 'we expect margins of ninety percent next year'."]


def _level(raw: dict[str, Any], n: int) -> dict[str, Any]:
    """Level 0: the label cleaned, no quote; level n >= 1: the committed text plus n - 1 extra
    "bleed" units and n fabricated quotes — M-LABEL and M-ABSENT rise together (NFLX: 3/2, 4/3,
    5/4 units)."""
    out = _clean(raw) if n == 0 else json.loads(json.dumps(raw))
    out["key_unknowns"] = [*out["key_unknowns"], *BLEED[:max(0, n - 1)], *QUOTES[:n]]
    return out


@pytest.mark.parametrize(("base", "cand", "p", "decision"), [
    # C6: both targets at 2/252 = 0.0079 — each <= ship alpha 0.01, but Holm holds the smaller to
    # 0.005, so the run is in the replication band; a raw cut at 0.01 would ship it
    ([1, 2, 2, 2, 2], [0, 0, 0, 0, 1], 2 / 252, cm.REPLICATION_REQUIRED),
    # C7: both at 11/252 = 0.0437 — each <= alpha 0.05, but Holm holds the smaller to 0.025, so it
    # does not ship; a raw cut at 0.05 would send it to a replication
    ([0, 1, 2, 2, 2], [0, 0, 0, 0, 1], 11 / 252, cm.DOES_NOT_SHIP),
])
def test_holm_separates_two_targets_from_a_raw_cut(tmp_path: Path, nflx: dict[str, Any],
                                                   base: list[int], cand: list[int], p: float,
                                                   decision: str) -> None:
    raw = nflx["synthesis"]
    reg = _reg(targets=("M-LABEL", "M-ABSENT"))
    s = cm.score_run(_run(tmp_path / "r", reg, [_level(raw, n) for n in base],
                          [_level(raw, n) for n in cand]), reg, pages={"NFLX": nflx})
    assert s.metrics["M-LABEL"].p_lower == pytest.approx(p)
    assert s.metrics["M-ABSENT"].p_lower == pytest.approx(p)
    assert s.decision == decision, s.reasons
