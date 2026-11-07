"""Fix 3a's five transforms (vinci/evals/variants.py) — the harness's way of letting #923's label
changes reach a replay of the committed layer.

Two properties, pinned on the FROZEN panel pages (`synthesis_panel.json`'s freeze) and their own
comps sheets (`tests/fixtures/ciq_comps_eval_panel.json`, cut from the exports that rebuild each
page's committed comps lines):

- UNDER THE CHECKOUT'S CODE EACH TRANSFORM MOVES ONLY ITS OWN FIELD, IS IDEMPOTENT, AND WRITES THAT
  CODE'S LABEL (a deterministic anchor per transform). Identity at the measured BASE ref
  (`e00db8cd`, the code that built the frozen pages) is #926's recorded evidence — shown on 28 pages
  and run by its CI — and cannot hold in-process once the checkout writes #923's labels (merged
  into #923, 2026-11-07, coordinator ruling); idempotence is that identity for a page already
  carrying the checkout's labels, which is what every rebuilt page will be;
- AT A CODE THAT REWRITES THE LABEL, ONLY THAT FIELD MOVES. A stand-in for each rule is installed
  where the transform looks for it, so these pins hold at main and at #923 alike; the real #923
  code is also read by the $0 cross-check (`compare main e91490ae`).

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
from vinci.dossier.schemas import CatalystRow, MechanicalLayer, Sourced
from vinci.evals import capture_child as cc
from vinci.evals import compare as cm
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


# ------------------------------- 1. under the checkout's code: own field, idempotent, its label

def _print_row(mech: MechanicalLayer) -> int:
    cal = mech.catalyst_calendar
    assert cal is not None
    return next(i for i, r in enumerate(cal.rows) if r.event == mechanical.PRINT_EVENT)


def _own(name: str, mech: MechanicalLayer) -> set[str]:
    """The fields each transform may move — and no other."""
    if name == "print_row_guide":
        i = _print_row(mech)
        return {f"catalyst_calendar.rows[{i}].tests_what",
                f"catalyst_calendar.rows[{i}].source_ref"}
    return {"relabel_drawdown_shape": {"drawdown_cause.shape.value"},
            "trailing_only_note": {"valuation.ev_ebitda.note"},
            "survival_read": {"quality.survival_capacity.value",
                              "leverage_survival.survival.value"},
            "peer_gap_question": {"peer_comps.fundamental_deltas.value"}}[name]


@pytest.mark.parametrize("t", PANEL["panel"])
def test_each_fix3a_transform_moves_only_its_own_field_and_is_idempotent(t: str) -> None:
    """Under the checkout's code, on every frozen panel page: each transform moves a subset of its
    own field(s), and applying it to its own output changes nothing; so does the five in order.
    (Identity at the measured BASE ref, `e00db8cd`, is #926's recorded evidence; the in-process pin
    is own-field, idempotence and the anchor, the last in
    `test_each_fix3a_transform_writes_the_checkouts_label`.)"""
    mech, ctx = _ctx(t)
    out = mech
    for name in vr.FIX_3A:
        one = vr.TRANSFORMS[name](mech, ctx)
        assert _moved(mech, one) <= _own(name, mech), (t, name, _moved(mech, one))
        assert vr.TRANSFORMS[name](one, ctx) == one, (t, name, "not idempotent")
        out = vr.TRANSFORMS[name](out, ctx)
    assert _moved(mech, out) <= set().union(*(_own(n, mech) for n in vr.FIX_3A))
    again = out
    for name in vr.FIX_3A:
        again = vr.TRANSFORMS[name](again, ctx)
    assert again == out


def test_each_fix3a_transform_writes_the_checkouts_label() -> None:
    """One deterministic anchor per transform, on a frozen page where it moves, under the
    checkout's code (#923's): code-written strings, so exact values. (Identity at the measured BASE
    ref, `e00db8cd`, is #926's recorded evidence; this pin is the in-process one.)"""
    mech, ctx = _ctx("LLY")
    assert mech.drawdown_cause is not None and mech.drawdown_cause.shape.value != (
        mechanical._CURRENT_WORDS.none_shape)   # the frozen page carries the BASE wording
    shape = vr.relabel_drawdown_shape(mech, ctx).drawdown_cause
    assert shape is not None and shape.shape.value == (
        "no single-day drop of -10% or worse in the window (detector threshold -10%)")
    assert mech.valuation.ev_ebitda.note == mechanical.TRAILING_ONLY_NOTE
    assert vr.trailing_only_note(mech, ctx).valuation.ev_ebitda.note is None  # forward P/E there
    line = vr.survival_read(mech, ctx).quality.survival_capacity.value
    assert line == "net-debt/EBITDA 0.9x (CIQ) | FCF sign UNKNOWN — runway not assessable"
    assert "(a risk)" not in str(line)
    def deltas(t: str) -> str:
        m, c = _ctx(t)
        return str(vr.peer_gap_question(m, c).peer_comps.fundamental_deltas.value)
    tail = "the human judges — not computed here]"
    # LLY: every known gap of the six trading multiples above the peer median — the premium
    assert deltas("LLY").endswith("  [justified-vs-residual inputs: is the premium EARNED (better "
                                  f"fundamentals) or RESIDUAL (unexplained)? {tail}")
    # MCK: its six gaps are MIXED on its own export — the question is deleted (what the paid
    # measurement drew; the cut once nulled the peers' NTM cells, which turned it "premium")
    assert deltas("MCK").endswith(f"  [justified-vs-residual inputs: {tail}")
    # SMPL: every known gap below the peer median — the discount question, as committed
    assert deltas("SMPL").endswith("  [justified-vs-residual inputs: is the discount EARNED (worse "
                                   f"fundamentals) or RESIDUAL (unexplained)? {tail}")
    b, bctx = _brbr()   # BRBR's drawdown guide is superseded: the row names it no more
    row = vr.print_row_guide(b, bctx).catalyst_calendar.rows[_print_row(b)]  # type: ignore[union-attr]
    assert row.tests_what == "the next reported quarter against the committed trajectory"
    assert " · guide: " not in str(row.source_ref)


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
        """…and rebuilds a calendar whose OTHER rows differ from the committed ones (V18: the
        whole rebuilt calendar replacing the committed rows): only the print row may be taken."""
        dc = m.drawdown_cause
        assert dc is not None
        cal = main_cal(e, cik, ref, m.model_copy(update={"drawdown_cause": dc.model_copy(
            update={"revised_guidance": Sourced.unknown(note="superseded")})}))
        extra = CatalystRow(event="a row only the rebuild has", expected_date="2099-01-01",
                            date_basis="stated", tests_what="nothing", source_ref="test")
        return cal.model_copy(update={"rows": [*cal.rows, extra]})
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


def test_print_row_guide_on_a_superseded_guide_moves_only_the_row_and_is_idempotent() -> None:
    """BRBR's superseded drawdown guide, under the checkout's code: only the print row's test and
    source move, and a second application changes nothing. (Identity at the measured BASE ref,
    `e00db8cd`, is #926's recorded evidence; the in-process pin is own-field, idempotence and the
    anchor in `test_each_fix3a_transform_writes_the_checkouts_label`.)"""
    mech, ctx = _brbr()
    out = vr.print_row_guide(mech, ctx)
    assert _moved(mech, out) <= _own("print_row_guide", mech)
    assert vr.print_row_guide(out, ctx) == out


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
    def five(m: MechanicalLayer) -> MechanicalLayer:   # the same five, in-process, on the page
        ctx = vr.Context(page=page, comps=_comps("LLY"))
        for name in vr.FIX_3A:
            m = vr.TRANSFORMS[name](m, ctx)
        return m
    want = rp.capture(page, None, draws=1, transform=five)
    got = rp.capture(page, None, draws=1, transforms=list(vr.FIX_3A), comps=wb)
    # the child opened the page's export and handed it, with the page, to the five transforms: its
    # request is the transformed layer's, end to end (identity at the measured BASE ref, e00db8cd,
    # is #926's recorded evidence — merged into #923, 2026-11-07)
    assert opened == [[wb]] and got.wire() == want.wire()
    assert got.wire() != rp.capture(page, None, draws=1).wire()   # and the five did move LLY
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


# ------------------------------------------------ #926 review round 2: the surviving mutants

def test_a_note_that_is_not_the_trailing_only_note_is_never_rewritten(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """V2: the reader's own note is left as committed, whatever the ref's rule returns."""
    mech, ctx = _ctx("LLY")
    v = mech.valuation
    own = mech.model_copy(update={"valuation": v.model_copy(update={
        "ev_ebitda": v.ev_ebitda.model_copy(update={"note": "the reader's own caveat"})})})
    monkeypatch.setattr(mechanical, "ev_ebitda_note", lambda **kw: None, raising=False)
    assert vr.trailing_only_note(own, ctx) == own


def test_the_ntm_cells_are_read_only_from_the_pages_proved_export(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """V3: an export that does not rebuild the page's comps lines is never read for NTM cells."""
    mech, _ctx_own = _ctx("LLY")
    _m, wrong = _ctx("LLY", comps="SMPL")
    monkeypatch.setattr(mechanical, "ev_ebitda_note",
                        lambda **kw: None if kw["peer_ntm"] else mechanical.TRAILING_ONLY_NOTE,
                        raising=False)
    monkeypatch.setattr(ciq_sheets, "comps_ntm_multiples", lambda b: ["NTM P/E"],
                        raising=False)
    with pytest.raises(vr.TransformError, match="not the page's own export"):
        vr.trailing_only_note(mech, wrong)


def test_an_export_whose_peer_medians_differ_is_not_the_pages_own() -> None:
    """V12: every peer's TEV/EBITDA moved — the name row and the summary rows (all that
    `trading_multiples` reads) unchanged, so only the cross_sectional check can refuse it."""
    mech, ctx = _ctx("LLY")
    moved = _comps("LLY")
    tm = moved.sheet("comps", "Trading Multiples")
    _hdr, peers, _tgt = ciq_sheets._comps_layout(tm, "LLY")
    for i in peers:
        tm[i][2] = 1.0
    assert ciq_sheets._comps_multiples(moved, vr.COMPS_SRC).value == \
        mech.peer_comps.trading_multiples.value
    with pytest.raises(vr.TransformError, match="cross_sectional"):
        vr.own_comps(mech, vr.Context(page=ctx.page, comps=moved))


def _garbage_comps(tmp_path: Path) -> Path:
    d = tmp_path / "LLY"
    d.mkdir()
    wb = d / "Company Comparable Analysis Eli Lilly and Company.xls"
    wb.write_bytes(b"not a workbook")
    return wb


def test_capture_at_hands_the_child_the_comps_export(tmp_path: Path) -> None:
    """X2: with `--comps` dropped the child reports "none was given"; given, it reads the file
    and refuses it as not the page's own."""
    page = _page("LLY")
    wb = _garbage_comps(tmp_path)
    with pytest.raises(rp.ReplayError) as got:
        rp.capture_at("HEAD", page, None, draws=1, transforms=["peer_gap_question"], comps=wb)
    assert "not the page's own export" in str(got.value), str(got.value)[-400:]
    with pytest.raises(rp.ReplayError, match="none was given"):
        rp.capture_at("HEAD", page, None, draws=1, transforms=["peer_gap_question"])


def test_compare_requests_hands_each_page_its_comps_export(tmp_path: Path) -> None:
    """X3: `compare_requests` finds the page's export under the CIQ root and passes it on."""
    _history()
    wb = _garbage_comps(tmp_path)
    panel = {"freeze_ref": PANEL["freeze_ref"], "panel": ["LLY"],
             "pages": {"LLY": {"dossier_blob": PANEL["pages"]["LLY"]["dossier_blob"],
                               "transcripts": []}}}
    with pytest.raises(rp.ReplayError) as got:
        cm.compare_requests("HEAD", "HEAD", transforms=["peer_gap_question"], panel=panel,
                            ciq_root=tmp_path)
    assert "not the page's own export" in str(got.value), str(got.value)[-400:]
    assert wb.exists()


def test_a_survival_copy_that_is_not_the_builders_copy_is_refused(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """V7: `leverage_survival.survival` is the builder's copy of `quality.survival_capacity`; a
    page where they differ is refused, never half-rewritten."""
    mech, ctx = _ctx("LLY")
    ls = mech.leverage_survival
    assert ls is not None
    odd = mech.model_copy(update={"leverage_survival": ls.model_copy(update={
        "survival": ls.survival.model_copy(update={"value": "another line"})})})
    main = mechanical._survival_capacity
    monkeypatch.setattr(mechanical, "_survival_capacity", lambda *a, **k: main(*a, **k).model_copy(
        update={"value": str(main(*a, **k).value).replace(" (a risk)", "")}))
    with pytest.raises(vr.TransformError, match="not the copy"):
        vr.survival_read(odd, ctx)


def test_a_rebuilt_print_row_on_another_date_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """V15: only what the row tests is re-derived; a rebuild that moves its date is refused."""
    mech, ctx = _brbr()
    main_cal = mechanical._catalyst_calendar

    def moved(e: Any, cik: str, ref: Any, m: MechanicalLayer) -> Any:
        cal = main_cal(e, cik, ref, m)
        return cal.model_copy(update={"rows": [
            r.model_copy(update={"expected_date": "2099-12-31"})
            if r.event == mechanical.PRINT_EVENT else r for r in cal.rows]})
    monkeypatch.setattr(mechanical, "_catalyst_calendar", moved)
    with pytest.raises(vr.TransformError, match="committed date"):
        vr.print_row_guide(mech, ctx)


def test_a_calendar_with_two_print_rows_is_refused() -> None:
    """V17: one calendar, one print row — two are refused, never one chosen."""
    mech, ctx = _brbr()
    cal = mech.catalyst_calendar
    assert cal is not None
    row = next(r for r in cal.rows if r.event == mechanical.PRINT_EVENT)
    two = mech.model_copy(update={"catalyst_calendar": cal.model_copy(
        update={"rows": [*cal.rows, row]})})
    with pytest.raises(vr.TransformError, match="2 print rows"):
        vr.print_row_guide(two, ctx)
