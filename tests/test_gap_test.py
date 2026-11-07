"""Fix 4a — THE GAP TEST (operator ruling 2026-11-07, verbatim: "Yes, use the test").

A missing item is sorted into one of four types — our gap, does not apply, the company's normal
practice, a change or deviation — or "type not determined" (`vinci/dossier/gaps.py`), and the
synthesis prompt's rule 8 lets ONLY a change or deviation be raised as a risk. Every pin below runs
END TO END on real committed page JSON — the 28 pages as committed at the panel's freeze
(`vinci/evals/synthesis_panel.json`'s ``freeze_ref``), never a living page — through the harness
transform that writes the field from the page's own layer (`variants.gap_types`). Each type has a
positive pin (a page that reads it) and a negative one (a page that must not).

TYPE 4 ON THE CORPUS: NONE. No committed page reads a change or deviation once CIQ's Guidance
sheet is asked to agree (`test_no_frozen_page_reads_a_change`). FUBO's release record looks like a
withdrawn guide — its April release states a Fiscal 2026 adjusted-EBITDA guide and the two since
state none — but CIQ records an EBITDA guide on 2026-08-05, so its gap reads ours. The positive
pin therefore moves that ONE CIQ row to the April release's date, the shape a withdrawn guide would
leave, on FUBO's otherwise real page.
"""
from __future__ import annotations

import copy
import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, get_args

import pytest

from vinci.dossier import ciq_sheets, gaps, mechanical
from vinci.dossier import synthesis as syn
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.schemas import GAP_TYPES, DisclosureGap, GapType, MechanicalLayer, Sourced
from vinci.evals import replay as rp
from vinci.evals import variants as vr
from vinci.evals.capture_child import capture_calls, pre_synthesis_mech
from vinci.sleeves import SLEEVES

ROOT = Path(__file__).resolve().parents[1]
PANEL = rp.load_panel_file()
#: the 28 pages committed at the freeze (`git ls-tree <freeze> data/dossiers/`)
CORPUS = (
    "AMZN", "AORT", "BRBR", "BURL", "CNXC", "EPAM", "FUBO", "GOOGL", "IT", "LLY",
    "MCK", "MVST", "NCNO", "NFLX", "NKE", "ORKA", "PARR", "ROST", "SMPL", "TECX",
    "TGT", "TJX", "UBER", "V", "VITL", "VRRM", "WERN", "WLK",
)
SINGLE = ("BURL", "CNXC", "LLY", "ROST", "SMPL")   # the panel's single-segment pages
SEGMENTS: dict[str, Any] = json.loads(
    (ROOT / "tests/fixtures/ciq_segments_eval_panel.json").read_text())["names"]
OUR, NA, PRACTICE, CHANGE, UNDETERMINED = GAP_TYPES


def _history() -> None:
    import subprocess
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e",
                       f"{PANEL['freeze_ref']}^{{commit}}"], capture_output=True).returncode != 0:
        pytest.skip("the panel's freeze commit is not in this history")


_PAGES: dict[str, dict[str, Any]] = {}


def _page(t: str) -> dict[str, Any]:
    _history()
    if t not in _PAGES:
        _PAGES[t] = rp.page_at(t, PANEL["freeze_ref"])
    return copy.deepcopy(_PAGES[t])


def _mech(t: str, edit: Callable[[dict[str, Any]], None] | None = None) -> MechanicalLayer:
    page = _page(t)
    if edit is not None:
        edit(page["mechanical"])
    return pre_synthesis_mech(page)


def _gaps(t: str, edit: Callable[[dict[str, Any]], None] | None = None) -> list[DisclosureGap]:
    out = vr.gap_types(_mech(t, edit)).disclosure_gaps
    assert out is not None
    return out


def _entry(gs: list[DisclosureGap], field: str) -> DisclosureGap:
    (hit,) = [g for g in gs if field in g.fields]
    return hit


# ---------------------------------------------------------------------------- 1. our gap

def test_mcks_segment_gap_is_ours() -> None:
    """(+) MCK's segment profit is UNKNOWN ("no profit measure … is tagged on two or more
    segments") while CIQ splits its revenue five ways — a read we did not make, never a signal
    about McKesson."""
    g = _entry(_gaps("MCK"), "concentration.segment_profit")
    assert g.type == OUR
    assert g.fields == ["concentration.segment_profit", "concentration.segment_ebitda"]
    assert "5 lines" in g.basis and "XBRL read failed" in g.basis


@pytest.mark.parametrize("t", SINGLE)
def test_a_single_segment_filers_segment_gap_is_not_ours(t: str) -> None:
    """(−) A single-segment filer's absent segment EBITDA is no read we failed to make."""
    assert _entry(_gaps(t), "concentration.segment_ebitda").type != OUR


def test_llys_runway_leg_is_our_gap() -> None:
    """(+) LLY's FCF sign is UNKNOWN ("no OCF/capex"), so its survival line said "runway not
    assessable", while the page's own annual table states LTM cash flow."""
    g = _entry(_gaps("LLY"), "quality.fcf_sign")
    assert g.type == OUR and "financial_summary.annual" in g.basis


def test_a_known_fcf_sign_has_no_runway_gap() -> None:
    """(−) BURL's FCF sign is present: no entry names it."""
    assert not [g for g in _gaps("BURL") if "quality.fcf_sign" in g.fields]


@pytest.mark.parametrize("t,metric,on", [("MCK", "EPS Normalized", "2026-11-04"),
                                         ("LLY", "EPS Normalized", "2026-10-29"),
                                         ("ROST", "EPS (GAAP)", "2026-08-20")])
def test_a_guide_ciq_records_at_the_newest_release_is_our_gap(t: str, metric: str,
                                                              on: str) -> None:
    """(+) The release parser read no guide from the newest release of MCK, LLY or ROST, and CIQ
    records one on that release's date: the absent adjusted-EPS guide is our gap."""
    g = _entry(_gaps(t), "valuation.adjusted_eps")
    assert g.type == OUR and f"{metric} guidance dated {on}" in g.basis


# ---------------------------------------------------------------------------- 2. does not apply

@pytest.mark.parametrize("t", SINGLE)
def test_a_single_segment_filer_has_no_segment_breakout_to_give(t: str) -> None:
    """(+) CIQ reads one segment and the 10-K tags fewer than two: does not apply."""
    g = _entry(_gaps(t), "concentration.segment_ebitda")
    assert g.type == NA and "one segment" in g.basis


def test_a_multi_segment_filers_segment_gap_does_not_read_as_inapplicable() -> None:
    """(−) MCK reports five segments: its segment profit applies."""
    assert _entry(_gaps("MCK"), "concentration.segment_ebitda").type != NA


def test_the_drawdown_fields_do_not_apply_without_a_gap_down_8k() -> None:
    """(+) BURL's window holds no gap-down 8-K, and the revised outlook and the two company-
    adjusted figures read only such an 8-K's outlook: one entry, does not apply."""
    g = _entry(_gaps("BURL"), "drawdown_cause.revised_guidance")
    assert g.type == NA
    assert g.fields == ["drawdown_cause.revised_guidance", "valuation.ev_ebitda_adjusted_fwd",
                        "quality.net_debt_to_ebitda_adjusted"]


def test_a_window_with_a_gap_down_8k_is_not_inapplicable() -> None:
    """(−) CNXC's window holds its 2026-06-29 8-K, whose release the parser read a guide from
    while the outlook reader matched none: our gap, not inapplicable."""
    g = _entry(_gaps("CNXC"), "drawdown_cause.revised_guidance")
    assert g.type == OUR and "2026-06-29" in g.basis
    assert g.source_ref is not None and "0001803599-26-000133" in g.source_ref


# --------------------------------------------------------------- 3. company's normal practice

def test_smpl_has_given_no_adjusted_eps_guide_in_anything_read() -> None:
    """(+) None of SMPL's six releases states an adjusted-EPS guide and CIQ, reaching its newest,
    records none since the oldest: the company's practice (it guides net sales and adjusted
    EBITDA)."""
    g = _entry(_gaps("SMPL"), "valuation.adjusted_eps")
    assert g.type == PRACTICE and "6 releases" in g.basis


def test_a_guide_ciq_records_is_not_practice() -> None:
    """(−) MCK's releases read no guide either, but CIQ records one: not the company's practice."""
    assert _entry(_gaps("MCK"), "valuation.adjusted_eps").type != PRACTICE


def _ciq_row(metric: str, on: str) -> Callable[[dict[str, Any]], None]:
    def edit(m: dict[str, Any]) -> None:
        rows = m["catalyst_path"]["guidance_bridge_rows"]["value"]
        rows.append({**rows[0], "metric": metric, "dated": on})
    return edit


def test_the_second_read_decides_practice() -> None:
    """(−) The same SMPL page with ONE CIQ EPS row added on its newest release's date is no longer
    practice: the type comes from the two reads together, not from the releases alone. (Not "our
    gap" either: the parser read that release's other guides, so the row is not one it missed.)"""
    g = _entry(_gaps("SMPL", _ciq_row("EPS Normalized", "2026-10-27")), "valuation.adjusted_eps")
    assert g.type == UNDETERMINED and "records one since" in g.basis


def test_one_release_is_no_practice() -> None:
    """(−) SMPL cut to its newest release: one release shows no practice."""
    def edit(m: dict[str, Any]) -> None:
        rels = m["primary_source"]["releases"]
        m["primary_source"]["releases"] = [max(rels, key=lambda r: r["filed"])]
    g = _entry(_gaps("SMPL", edit), "valuation.adjusted_eps")
    assert g.type == UNDETERMINED and g.basis == "one release was read"


# ----------------------------------------------------------------- 4. change or deviation

def test_no_frozen_page_reads_a_change() -> None:
    """THE CORPUS FINDING, pinned: none of the 28 frozen pages reads type 4 once both reads must
    agree. A page that starts to is a finding to read before this pin moves."""
    found = {t: [g.item for g in _gaps(t) if g.type == CHANGE] for t in CORPUS}
    assert {t: v for t, v in found.items() if v} == {}


_FUBO_ADJ = "valuation.ev_ebitda_adjusted_fwd"


def test_fubos_silent_releases_are_not_a_change() -> None:
    """(−) FUBO as committed: CIQ records an EBITDA guide on 2026-08-05, the date of a release the
    field reads and the parser read nothing from — our gap, never a withdrawn guide."""
    g = _entry(_gaps("FUBO"), _FUBO_ADJ)
    assert g.type == OUR and "EBITDA guidance dated 2026-08-05" in g.basis


def _redate(metric: str, on: str) -> Callable[[dict[str, Any]], None]:
    def edit(m: dict[str, Any]) -> None:
        for r in m["catalyst_path"]["guidance_bridge_rows"]["value"]:
            if r["metric"] == metric:
                r["dated"] = on
    return edit


def test_a_guide_stated_then_absent_with_ciq_agreeing_is_a_change() -> None:
    """(+) FUBO with CIQ's EBITDA row moved to the April release: the guide stated on 2026-04-06
    is absent from both releases since (a full quarter, to 2026-08-05), and CIQ — which still
    reaches 2026-08-05 through its free-cash-flow row — records none after April. A change, with
    the evidence the ruling demands: what, where, when it stopped."""
    g = _entry(_gaps("FUBO", _redate("EBITDA", "2026-04-06")), _FUBO_ADJ)
    assert g.type == CHANGE
    assert g.disclosed == "adjusted ebitda guide for Fiscal 2026"
    assert g.source_ref is not None and "0001493152-26-015252" in g.source_ref
    assert g.stopped == "2026-05-06"
    assert g.stopped_ref is not None and "0001493152-26-021406" in g.stopped_ref


def test_a_stop_shorter_than_a_quarter_is_not_a_change() -> None:
    """(−) The same edit with FUBO's 2026-08-05 release dropped: one release a month later is no
    stop (it could be any 8-K)."""
    def edit(m: dict[str, Any]) -> None:
        _redate("EBITDA", "2026-04-06")(m)
        rels = m["primary_source"]["releases"]
        m["primary_source"]["releases"] = [r for r in rels if r["filed"] != "2026-08-05"]
    assert _entry(_gaps("FUBO", edit), _FUBO_ADJ).type != CHANGE


def test_a_stop_ciq_cannot_see_is_not_a_change() -> None:
    """(−) The same edit with CIQ's free-cash-flow row dated in April too: CIQ's export no longer
    reaches the releases since, so it cannot agree that the guide stopped."""
    def edit(m: dict[str, Any]) -> None:
        _redate("EBITDA", "2026-04-06")(m)
        _redate("Free Cash Flow", "2026-04-06")(m)
    g = _entry(_gaps("FUBO", edit), _FUBO_ADJ)
    assert g.type == UNDETERMINED and "before the newest release read" in g.basis


@pytest.mark.parametrize("kw", [{}, {"disclosed": "x", "stopped": "2026-01-01"}])
def test_a_change_names_what_where_and_when(kw: dict[str, str]) -> None:
    """(−) A change without all of its evidence is refused at construction."""
    with pytest.raises(ValueError, match="what was disclosed"):
        DisclosureGap(item="x", fields=["f"], type=CHANGE, basis="b", **kw)


@pytest.mark.parametrize("kind", [t for t in GAP_TYPES if t != CHANGE])
def test_only_a_change_carries_a_stop(kind: GapType) -> None:
    with pytest.raises(ValueError, match="only a change"):
        DisclosureGap(item="x", fields=["f"], type=kind, basis="b", stopped="2026-01-01")


# ---------------------------------------------------------------- 5. type not determined

def test_a_ciq_export_short_of_the_newest_release_decides_nothing() -> None:
    """(+) IT's CIQ guides all date 2026-05-05 and its newest release is 2026-08-04: CIQ cannot
    speak for that release, so the adjusted-EPS gap's type is not determined."""
    g = _entry(_gaps("IT"), "valuation.adjusted_eps")
    assert g.type == UNDETERMINED and "2026-05-05" in g.basis and "2026-08-04" in g.basis


@pytest.mark.parametrize("t", ["ORKA", "TECX"])
def test_no_second_read_gives_no_company_type(t: str) -> None:
    """(+) ORKA and TECX carry no CIQ Guidance sheet: every guide gap is not determined."""
    for field in ("valuation.adjusted_eps", "primary_source.current_guide"):
        assert _entry(_gaps(t), field).type == UNDETERMINED


def test_a_decidable_gap_is_determined() -> None:
    """(−) SMPL's adjusted-EPS gap is decided (practice), not left undetermined."""
    assert _entry(_gaps("SMPL"), "valuation.adjusted_eps").type != UNDETERMINED


# ------------------------------------------------------------ structured values only, all 28

def _blank_notes(o: Any) -> None:
    if isinstance(o, dict):
        if "note" in o and set(o) >= {"status", "value", "source_ref"}:
            o["note"] = None
        for v in o.values():
            _blank_notes(v)
    elif isinstance(o, list):
        for v in o:
            _blank_notes(v)


@pytest.mark.parametrize("t", CORPUS)
def test_the_types_read_no_note(t: str) -> None:
    """Every fact's note blanked, the page sorts its gaps exactly as before: the reason a field is
    UNKNOWN is read from statuses, lists, dates and table cells, never from a rendered string
    (CLAUDE.md)."""
    assert _gaps(t, _blank_notes) == _gaps(t)


def test_the_constant_and_the_literal_agree() -> None:
    assert get_args(GapType) == GAP_TYPES


# --------------------------------------------------------------- the builder and its roster

def _segments_bundle(t: str) -> CiqBundle:
    path = Path("/frozen") / f"{t}-financials-annual.xls"
    sheets = {k.split("|")[1]: copy.deepcopy(v) for k, v in SEGMENTS[t]["sheets"].items()}
    return CiqBundle(ticker=t, workbooks=(CiqWorkbook(kind="financials", path=path,
                                                     fmt=CiqFormat.BIFF_XLS, freq="annual"),),
                     _cache={path: sheets})


@pytest.mark.parametrize("t", PANEL["panel"])
def test_the_builders_roster_is_the_transforms_on_each_panel_pages_own_export(t: str) -> None:
    """The builder counts CIQ's roster (`ciq_sheets.segment_count`); the transform reads the count
    the committed segments line states (`variants.segment_count_from_line`). On each panel page's
    own export — proved its own by rebuilding the committed segment lines — the two agree, and so
    the gap list the builder writes is the transform's."""
    b, mech = _segments_bundle(t), _mech(t)
    assert ciq_sheets.segments(b) == mech.concentration.segments
    assert ciq_sheets.segment_ebitda(b) == mech.concentration.segment_ebitda
    assert ciq_sheets.segment_count(b) == vr.segment_count_from_line(mech.concentration.segments)
    assert (gaps.disclosure_gaps(mech, segment_count=ciq_sheets.segment_count(b))
            == vr.gap_types(mech).disclosure_gaps)


def _roster(*items: tuple[str, float]) -> CiqBundle:
    rows: list[list[Any]] = [["For the Fiscal Period Ending", "12 months\nDec-31-2025"],
                             ["Revenues", None], *([n, v] for n, v in items),
                             ["  Total Revenues", sum(v for _, v in items)]]
    path = Path("/synthetic.xls")
    return CiqBundle(ticker="X", workbooks=(CiqWorkbook(kind="financials", path=path,
                                                       fmt=CiqFormat.BIFF_XLS, freq="annual"),),
                     _cache={path: {"Segments": rows}})


@pytest.mark.parametrize("items,want", [
    ((("Retail", 100.0),), 1), ((("Retail", 97.0), ("", 3.0)), None),
    ((("A", 60.0), ("B", 40.0)), 2), ((), None)])
def test_segment_count_and_the_rendered_line_never_disagree(
        items: tuple[tuple[str, float], ...], want: int | None) -> None:
    """A lone segment at ≥99.5% is 1 (the line's "— single segment"); one short of it is None; a
    split is its length; no roster is None — and the transform's reading of the rendered line
    agrees every time."""
    b = _roster(*items)
    assert ciq_sheets.segment_count(b) == want
    assert vr.segment_count_from_line(ciq_sheets.segments(b)) == want


def test_the_assembly_writes_the_gap_test_last() -> None:
    """Through the whole assembly (LLY's real inputs, no network, an empty CIQ bundle): the page
    carries `disclosure_gaps`, written by the gap test from the finished layer."""
    from tests.test_asof_cut import _assemble_lly, _LlySec
    mech = _assemble_lly(_LlySec())
    assert mech.disclosure_gaps is not None
    assert mech.disclosure_gaps == gaps.disclosure_gaps(mech, segment_count=None)


# ------------------------------------------------------------------------- the transform

def _leaves(o: Any, path: str = "") -> Iterator[tuple[str, Any]]:
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _leaves(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _leaves(v, f"{path}[{i}]")
    else:
        yield path, o


@pytest.mark.parametrize("t", PANEL["panel"])
def test_the_transform_moves_only_its_own_field_and_is_idempotent(t: str) -> None:
    mech = _mech(t)
    out = vr.gap_types(mech)
    la, lb = dict(_leaves(mech.model_dump(mode="json"))), dict(_leaves(out.model_dump(mode="json")))
    moved = {k for k in la.keys() | lb.keys() if la.get(k) != lb.get(k)}
    assert moved and all(k.startswith("disclosure_gaps") for k in moved)
    assert vr.gap_types(out) is out


def test_the_transform_is_the_identity_at_a_ref_without_the_test(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """At main (no `mechanical.disclosure_gaps`) the layer is returned unchanged."""
    monkeypatch.delattr(mechanical, "disclosure_gaps")
    mech = _mech("MCK")
    assert vr.gap_types(mech) is mech


@pytest.mark.parametrize("line,want", [
    ("Retail - Apparel — single segment", 1), ("A 59%; B 41%", 2), ("A 97%", None),
    ("Refining 97%; Retail 8%; Logistics 4%; Corporate and Other -8%", 4)])
def test_the_segments_line_reads_as_its_count(line: str, want: int | None) -> None:
    assert vr.segment_count_from_line(Sourced.present(line, source_ref="r")) == want


@pytest.mark.parametrize("line", ["Retail, 100", "A 59%, B 41%", "A — single segment; B 3%"])
def test_a_segments_line_that_is_not_the_lean_roster_is_refused(line: str) -> None:
    with pytest.raises(vr.TransformError, match="lean roster"):
        vr.segment_count_from_line(Sourced.present(line, source_ref="r"))


def test_an_unknown_segments_line_has_no_count() -> None:
    assert vr.segment_count_from_line(Sourced.unknown(note="no roster")) is None


# ------------------------------------------------------------------------------ the prompt

#: RULE 8'S OLD WORDING AND THE TRAILING-ONLY ASK — a closed list; each entry pinned live below.
OLD_WORDING = ("OPACITY-AS-SIGNAL", "is NOT neutral", "BEARISH risk", "trailing-only",
               "blind-flag")


def old_wording(text: str) -> list[str]:
    return [w for w in OLD_WORDING if w.lower() in text.lower()]


@pytest.mark.parametrize("sleeve", sorted(SLEEVES))
def test_rule_8s_old_wording_cannot_return(sleeve: str) -> None:
    """The prompt no longer tells the model a missing disclosure is a bearish risk, nor asks a
    trailing multiple for a "trailing-only" tag, in any book's system prompt or tool schema."""
    assert old_wording(syn.system_for(sleeve) + json.dumps(syn.tool_for(sleeve))) == []


@pytest.mark.parametrize("phrase", OLD_WORDING)
def test_every_entry_of_the_old_wording_list_is_live(phrase: str) -> None:
    assert old_wording(syn.system_for("overshoot") + f" {phrase} ") == [phrase]


@pytest.mark.parametrize("sleeve", sorted(SLEEVES))
def test_rule_8_names_the_five_types_the_layer_writes(sleeve: str) -> None:
    rule = syn.system_for(sleeve).split("(8) ", 1)[1].split(" (9) ", 1)[0]
    assert rule.startswith("THE GAP TEST")
    for t in GAP_TYPES:
        assert f"'{t}'" in rule, t
    assert "disclosure_gaps" in rule


def _user(t: str, transforms: list[str]) -> str:
    (call,) = capture_calls(_page(t), None, draws=1, transforms=transforms)
    content = call["messages"][0]["content"]
    return content if isinstance(content, str) else str(content[0]["text"])


def test_the_request_carries_the_typed_gaps_and_touches_nothing_else() -> None:
    """THE ARTIFACT (TEST-LAYER RULE): MCK's captured request carries its typed gaps as the facts'
    last key, and removing that one value leaves the request the untransformed one sends."""
    plain, typed = _user("MCK", []), _user("MCK", ["gap_types"])
    assert '"disclosure_gaps": null' in plain
    start = typed.index('"disclosure_gaps": [')
    end = typed.index("\n  ]", start) + len("\n  ]")
    block = json.loads("{" + typed[start:end] + "}")["disclosure_gaps"]
    assert block[0]["item"] == "segment profit by segment" and block[0]["type"] == OUR
    assert typed[:start] + '"disclosure_gaps": null' + typed[end:] == plain
    assert typed[end:].startswith("\n}")   # the layer's last key


def test_the_layer_drops_the_field_until_built() -> None:
    """A page built before the gap test round-trips without the key (`DROP_WHEN_NONE`)."""
    from vinci.dossier.schemas import DROP_WHEN_NONE
    assert ("", "disclosure_gaps") in DROP_WHEN_NONE
    assert "disclosure_gaps" not in _page("MCK")["mechanical"]
