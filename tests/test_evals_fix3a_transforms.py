"""Fix 3a's five transforms (vinci/evals/variants.py) — the harness's way of letting #923's label
changes reach a replay of the committed layer.

Two properties, pinned on the FROZEN panel pages (`synthesis_panel.json`'s freeze) and their own
comps sheets (`tests/fixtures/ciq_comps_eval_panel.json`, cut from the exports that rebuild each
page's committed comps lines):

- AT MAIN EACH TRANSFORM IS THE IDENTITY: main's code regenerates exactly the committed field;
- AT A CODE THAT REWRITES THE LABEL, ONLY THAT FIELD MOVES. The code under test here is main, so a
  stand-in for #923's rule is installed where the transform looks for it; the real #923 code is
  read by the $0 cross-check (`compare main e91490ae`), not by a unit test.

A transform never guesses: a field it cannot regenerate from the ref's code and the page's own
facts is refused (`TransformError`) — a comps export that is not the page's own, or a survival line
that needs the CIQ net debt the layer does not carry.
"""
from __future__ import annotations

import copy
import json
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import ciq_sheets, mechanical
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.schemas import MechanicalLayer, Sourced
from vinci.evals import capture_child as cc
from vinci.evals import replay as rp
from vinci.evals import variants as vr
from vinci.evals.capture_child import pre_synthesis_mech

ROOT = Path(__file__).resolve().parents[1]
PANEL = rp.load_panel_file()
COMPS: dict[str, Any] = json.loads(
    (ROOT / "tests/fixtures/ciq_comps_eval_panel.json").read_text())["names"]
NEW = ("trailing_only_note", "survival_read", "peer_gap_question", "print_row_guide")


def _history() -> None:
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e",
                       f"{PANEL['freeze_ref']}^{{commit}}"], capture_output=True).returncode != 0:
        pytest.skip("the panel's freeze commit is not in this history")


def _page(t: str) -> dict[str, Any]:
    _history()
    return rp.page_at(t, PANEL["freeze_ref"])


def _comps(t: str) -> CiqBundle:
    path = Path("/frozen") / f"{t}-comps.xls"
    sheets = {k.split("|")[1]: copy.deepcopy(v) for k, v in COMPS[t]["sheets"].items()}
    return CiqBundle(ticker=t, workbooks=(CiqWorkbook(kind="comps", path=path,
                                                     fmt=CiqFormat.BIFF_XLS, freq=None),),
                     _cache={path: sheets})


def _ctx(t: str, comps: str | None = "own") -> tuple[MechanicalLayer, vr.Context]:
    page = _page(t)
    bundle = _comps(t if comps == "own" else comps) if comps else None
    return pre_synthesis_mech(page), vr.Context(page=page, comps=bundle)


def _leaves(o: Any, path: str = "") -> Iterator[tuple[str, Any]]:
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _leaves(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _leaves(v, f"{path}[{i}]")
    else:
        yield path, o


def _moved(a: MechanicalLayer, b: MechanicalLayer) -> set[str]:
    la, lb = dict(_leaves(a.model_dump(mode="json"))), dict(_leaves(b.model_dump(mode="json")))
    return {k for k in la.keys() | lb.keys() if la.get(k) != lb.get(k)}


# ------------------------------------------------------------- 1. the identity at main

@pytest.mark.parametrize("t", PANEL["panel"])
def test_each_fix3a_transform_is_the_identity_at_main(t: str) -> None:
    mech, ctx = _ctx(t)
    for name in vr.FIX_3A:
        assert vr.TRANSFORMS[name](mech, ctx) == mech, (t, name)
    out = mech
    for name in vr.FIX_3A:
        out = vr.TRANSFORMS[name](out, ctx)
    assert out == mech


def test_fix3a_names_its_five_transforms_in_order() -> None:
    assert vr.FIX_3A == ("relabel_drawdown_shape", "trailing_only_note", "survival_read",
                         "peer_gap_question", "print_row_guide")
    assert set(vr.FIX_3A) <= set(vr.TRANSFORMS)


# ---------------------------------------------- 2. the comps export is the page's own, or none

def test_the_comps_export_must_rebuild_the_pages_committed_comps_lines() -> None:
    mech, ctx = _ctx("LLY")
    assert vr.own_comps(mech, ctx) is ctx.comps
    _m, wrong = _ctx("LLY", comps="SMPL")                     # another page's export
    with pytest.raises(vr.TransformError, match="not the page's own export"):
        vr.peer_gap_question(mech, wrong)
    _m, none = _ctx("LLY", comps=None)
    with pytest.raises(vr.TransformError, match="none was given"):
        vr.peer_gap_question(mech, none)
    moved = _comps("LLY")                                     # one NTM cell of the name moved
    tm = moved.sheet("comps", "Trading Multiples")
    tgt = ciq_sheets._comps_layout(tm, "LLY")[2]
    assert tgt is not None
    tm[tgt][7] = 99.0
    with pytest.raises(vr.TransformError, match="trading_multiples"):
        vr.own_comps(mech, vr.Context(page=ctx.page, comps=moved))


# --------------------------------------------- 3. at a code that rewrites it, only that field

def test_trailing_only_note_moves_only_the_note(monkeypatch: pytest.MonkeyPatch) -> None:
    mech, ctx = _ctx("LLY")
    assert mech.valuation.ev_ebitda.note == mechanical.TRAILING_ONLY_NOTE
    seen: list[dict[str, Any]] = []

    def rule(**kw: Any) -> str | None:   # #923's shape: deleted where a forward basis exists
        seen.append(kw)
        return None if kw["forward_multiples"] else mechanical.TRAILING_ONLY_NOTE
    monkeypatch.setattr(mechanical, "ev_ebitda_note", rule, raising=False)
    out = vr.trailing_only_note(mech, ctx)
    assert _moved(mech, out) == {"valuation.ev_ebitda.note"}
    assert out.valuation.ev_ebitda.note is None
    assert seen[0]["forward_multiples"] is True and seen[0]["guided_forward"] is False
    assert seen[0]["forward_history"] is not None and seen[0]["peer_ntm"] == []


def test_trailing_only_note_reads_the_ntm_cells_only_when_they_decide(
        monkeypatch: pytest.MonkeyPatch) -> None:
    mech, ctx = _ctx("LLY")
    monkeypatch.setattr(mechanical, "ev_ebitda_note",
                        lambda **kw: None if kw["peer_ntm"] else mechanical.TRAILING_ONLY_NOTE,
                        raising=False)
    monkeypatch.setattr(ciq_sheets, "comps_ntm_multiples",
                        lambda b: ["NTM TEV/EBITDA"], raising=False)
    assert vr.trailing_only_note(mech, ctx).valuation.ev_ebitda.note is None
    _m, none = _ctx("LLY", comps=None)
    with pytest.raises(vr.TransformError, match="none was given"):
        vr.trailing_only_note(mech, none)


def test_survival_read_moves_only_the_line_in_both_places(
        monkeypatch: pytest.MonkeyPatch) -> None:
    mech, ctx = _ctx("LLY")
    assert mech.quality.survival_capacity.value.endswith("(a risk)")   # type: ignore[union-attr]
    main = mechanical._survival_capacity

    def untagged(*a: Any, **k: Any) -> Sourced[str]:
        s = main(*a, **k)
        return s.model_copy(update={"value": str(s.value).replace(" (a risk)", "")})
    monkeypatch.setattr(mechanical, "_survival_capacity", untagged)
    out = vr.survival_read(mech, ctx)
    assert _moved(mech, out) == {"quality.survival_capacity.value",
                                 "leverage_survival.survival.value"}
    assert out.quality.survival_capacity.value == (
        "net-debt/EBITDA 0.9x (CIQ) | FCF sign UNKNOWN — runway not assessable")


def test_survival_read_refuses_a_line_that_needs_the_ciq_net_debt() -> None:
    mech, ctx = _ctx("LLY")
    q = mech.quality
    gone = mech.model_copy(update={"quality": q.model_copy(update={
        "net_debt_to_ebitda": Sourced.unknown(note="not derivable")})})
    with pytest.raises(vr.TransformError, match="CIQ net debt"):
        vr.survival_read(gone, ctx)


def test_peer_gap_question_moves_only_the_deltas_value(monkeypatch: pytest.MonkeyPatch) -> None:
    mech, ctx = _ctx("LLY")      # LLY trades at a premium on every multiple; main asks "discount"
    main = ciq_sheets._comps_deltas

    def premium(b: CiqBundle, src: str) -> Sourced[str]:
        s = main(b, src)
        return s.model_copy(update={"value": str(s.value).replace(
            "is the discount EARNED (worse fundamentals)",
            "is the premium EARNED (better fundamentals)")})
    monkeypatch.setattr(ciq_sheets, "_comps_deltas", premium)
    out = vr.peer_gap_question(mech, ctx)
    assert _moved(mech, out) == {"peer_comps.fundamental_deltas.value"}
    assert "is the premium EARNED" in str(out.peer_comps.fundamental_deltas.value)


def test_peer_gap_question_refuses_deltas_the_export_does_not_rebuild(
        monkeypatch: pytest.MonkeyPatch) -> None:
    mech, ctx = _ctx("LLY")
    main = ciq_sheets._comps_deltas
    monkeypatch.setattr(ciq_sheets, "_comps_deltas", lambda b, src: main(b, src).model_copy(
        update={"value": "EBITDA margin name 1% vs peer-median 2%  [other]"}))
    with pytest.raises(vr.TransformError, match="operating statistics"):
        vr.peer_gap_question(mech, ctx)


def _brbr() -> tuple[MechanicalLayer, vr.Context]:
    page = _page("BRBR")
    return pre_synthesis_mech(page), vr.Context(page=page)


def test_print_row_guide_moves_only_the_print_rows_test_and_source(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """BRBR's drawdown guide was superseded; #923 names it only when current. The stand-in drops
    the guide before main's own calendar builder runs, which is what #923 writes for BRBR."""
    mech, ctx = _brbr()
    row = next(r for r in mech.catalyst_calendar.rows   # type: ignore[union-attr]
               if r.event == mechanical.PRINT_EVENT)
    assert row.tests_what.startswith("the committed revised outlook")
    main_cal = mechanical._catalyst_calendar
    edgar_reads = (mechanical.eight_k_events, mechanical._next_print_estimate)

    def not_current(e: Any, cik: str, ref: Any, m: MechanicalLayer) -> Any:
        dc = m.drawdown_cause
        assert dc is not None
        return main_cal(e, cik, ref, m.model_copy(update={"drawdown_cause": dc.model_copy(
            update={"revised_guidance": Sourced.unknown(note="superseded")})}))
    monkeypatch.setattr(mechanical, "_catalyst_calendar", not_current)
    out = vr.print_row_guide(mech, ctx)
    i = next(i for i, r in enumerate(mech.catalyst_calendar.rows)  # type: ignore[union-attr]
             if r.event == mechanical.PRINT_EVENT)
    assert _moved(mech, out) == {f"catalyst_calendar.rows[{i}].tests_what",
                                 f"catalyst_calendar.rows[{i}].source_ref"}
    new = out.catalyst_calendar.rows[i]   # type: ignore[union-attr]
    assert new.tests_what == "the next reported quarter against the committed trajectory"
    assert new.expected_date == row.expected_date and " · guide: " not in str(new.source_ref)
    assert (mechanical.eight_k_events, mechanical._next_print_estimate) == edgar_reads


def test_print_row_guide_is_the_identity_at_main_on_a_superseded_guide() -> None:
    mech, ctx = _brbr()
    assert vr.print_row_guide(mech, ctx) == mech


# ------------------------------------------------- 4. the capture child hands them the context

def test_variants_load_by_path_as_the_capture_child_loads_them() -> None:
    """The child loads `variants.py` by path, unregistered — a dataclass in it then failed to
    resolve its annotations (`sys.modules[...]` was None) on every capture with a transform."""
    m = cc.load_variants()
    assert set(vr.FIX_3A) <= set(m.TRANSFORMS) and m.Context(page={}).comps is None


def test_a_capture_hands_the_transforms_the_page_and_its_comps(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    page = _page("LLY")
    wb = tmp_path / "Company Comparable Analysis Eli Lilly and Company.xls"
    wb.write_bytes(b"placeholder")
    opened: list[list[Path]] = []

    def from_files(ticker: str, paths: list[Path]) -> CiqBundle:
        opened.append(paths)
        return _comps(ticker)
    monkeypatch.setattr(CiqBundle, "from_files", staticmethod(from_files))
    base = rp.capture(page, None, draws=1)
    got = rp.capture(page, None, draws=1, transforms=list(vr.FIX_3A), comps=wb)
    assert opened == [[wb]] and got.wire() == base.wire()     # at main: the identity, end to end
    # the capture's TransformError is the by-path module's own class: a RuntimeError either way
    with pytest.raises(RuntimeError, match="none was given"):
        rp.capture(page, None, draws=1, transforms=["peer_gap_question"])


def test_comps_export_finds_one_export_and_refuses_two(tmp_path: Path) -> None:
    assert rp.comps_export("LLY", ciq_root=tmp_path) is None
    d = tmp_path / "LLY"
    d.mkdir()
    (d / "Eli Lilly NYSE LLY Financials_Annual.xls").write_bytes(b"x")
    (d / "~$Company Comparable Analysis Eli Lilly.xls").write_bytes(b"x")   # a lock file
    assert rp.comps_export("LLY", ciq_root=tmp_path) is None
    one = d / "Company Comparable Analysis Eli Lilly and Company.xls"
    one.write_bytes(b"x")
    assert rp.comps_export("LLY", ciq_root=tmp_path) == one
    (d / "Company Comparable Analysis Eli Lilly (2).xls").write_bytes(b"x")
    with pytest.raises(rp.ReplayError, match="2 comps exports"):
        rp.comps_export("LLY", ciq_root=tmp_path)
