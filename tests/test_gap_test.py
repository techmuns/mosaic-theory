"""Fix 4a — THE GAP TEST (operator ruling 2026-11-07, verbatim: "Yes, use the test").

A missing item is sorted into one of four types — our gap, does not apply, the company's normal
practice, a change or deviation — or "type not determined" (`vinci/dossier/gaps.py`), and the
synthesis prompt's rule 8 lets ONLY a change or deviation be raised as a risk. Every pin below runs
END TO END on real committed page JSON — the 28 pages as committed at the panel's freeze
(`vinci/evals/synthesis_panel.json`'s ``freeze_ref``), never a living page — through the harness
transform that writes the field from the page's own layer (`variants.gap_types`). Each type has a
positive pin (a page that reads it) and a negative one (a page that must not); an edit of a real
page is named as such, and changes one field.

TYPE 4: NO PATH EMITS IT (coordinator review of #927, F5). Measured on the corpus, the release
parser's blanks are mostly misses, and CIQ is shown re-dating a guide reaffirmed unchanged once
(AORT's 2026 revenue) and never otherwise, so "stated, then absent, CIQ silent" is no evidence of a
stop. The strongest such shape — FUBO's real page with its one refuting CIQ row moved to April —
reads "type not determined", saying why; no frozen page reads a change.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, cast, get_args

import pytest

from vinci.dossier import ciq_sheets, filed_tiebreak, gaps, mechanical
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
ADJ = "valuation.ev_ebitda_adjusted_fwd"
EPS = "valuation.adjusted_eps"


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


Edit = Callable[[dict[str, Any]], None]


def _mech(t: str, edit: Edit | None = None) -> MechanicalLayer:
    page = _page(t)
    if edit is not None:
        edit(page["mechanical"])
    return pre_synthesis_mech(page)


def _gaps(t: str, edit: Edit | None = None) -> list[DisclosureGap]:
    out = vr.gap_types(_mech(t, edit)).disclosure_gaps
    assert out is not None
    return out


def _entry(gs: list[DisclosureGap], field: str) -> DisclosureGap:
    (hit,) = [g for g in gs if field in g.fields]
    return hit


def _ciq_rows(m: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], m["catalyst_path"]["guidance_bridge_rows"]["value"])


def _redate(metric: str, on: str) -> Edit:
    def edit(m: dict[str, Any]) -> None:
        for r in _ciq_rows(m):
            if r["metric"] == metric:
                r["dated"] = on
    return edit


def _ciq_row(metric: str, on: str) -> Edit:
    def edit(m: dict[str, Any]) -> None:
        rows = _ciq_rows(m)
        rows.append({**rows[0], "metric": metric, "dated": on})
    return edit


# ---------------------------------------------------------------------------- 1. our gap

def test_mcks_segment_gap_is_ours() -> None:
    """(+) MCK's segment profit is UNKNOWN while CIQ splits its revenue across five segments — a
    read we did not make, never a signal about McKesson."""
    g = _entry(_gaps("MCK"), "concentration.segment_profit")
    assert g.type == OUR
    assert g.fields == ["concentration.segment_profit", "concentration.segment_ebitda"]
    assert "across 5 segments" in g.basis and "read is UNKNOWN" in g.basis


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
    g = _entry(_gaps(t), EPS)
    assert g.type == OUR and f"{metric} guidance dated {on}" in g.basis


@pytest.mark.parametrize("t,on", [("SMPL", "2026-10-27"), ("UBER", "2026-08-05")])
def test_the_adjusted_figures_are_our_gap_where_the_company_guides_adjusted_ebitda(
        t: str, on: str) -> None:
    """(+) F2, live on the panel: SMPL's and UBER's releases guide adjusted EBITDA, and the two
    company-adjusted figures read only a gap-down 8-K's outlook — so their absence is our scope,
    and the basis names the guide and its release."""
    g = _entry(_gaps(t), ADJ)
    assert g.fields == [ADJ, "quality.net_debt_to_ebitda_adjusted"]
    assert g.type == OUR
    assert f"the release filed {on} states an adjusted ebitda guide" in g.basis
    assert g.source_ref is not None


def test_a_ciq_adjusted_ebitda_guide_alone_also_makes_the_figures_ours() -> None:
    """(+) BRBR's parser reads no adjusted-EBITDA guide, CIQ records one (2026-08-04): ours."""
    g = _entry(_gaps("BRBR"), ADJ)
    assert g.type == OUR and "EBITDA guidance dated 2026-08-04" in g.basis


def test_a_company_that_guides_no_adjusted_ebitda_is_not_our_gap() -> None:
    """(−) CNXC guides adjusted operating income, never adjusted EBITDA, in anything read."""
    assert _entry(_gaps("CNXC"), ADJ).type == PRACTICE


# ---------------------------------------------------------------------------- 2. does not apply

@pytest.mark.parametrize("t", SINGLE)
def test_a_single_segment_filer_has_no_segment_breakout_to_give(t: str) -> None:
    """(+) CIQ reads one segment and the page states no 10-K segment profit: does not apply."""
    g = _entry(_gaps(t), "concentration.segment_ebitda")
    assert g.type == NA and "reads one segment" in g.basis


def test_a_multi_segment_filers_segment_gap_does_not_read_as_inapplicable() -> None:
    """(−) MCK reports five segments: its segment profit applies."""
    assert _entry(_gaps("MCK"), "concentration.segment_ebitda").type != NA


def test_the_outlook_does_not_apply_without_a_gap_down_8k() -> None:
    """(+) BURL's window was read and holds no gap-down 8-K, and the revised outlook reads only
    such an 8-K's: does not apply — the adjusted figures are their own item (F2)."""
    g = _entry(_gaps("BURL"), "drawdown_cause.revised_guidance")
    assert g.type == NA and g.fields == ["drawdown_cause.revised_guidance"]
    assert "each window read" in g.basis


def test_a_window_with_a_gap_down_8k_is_not_inapplicable() -> None:
    """(−) CNXC's window holds its 2026-06-29 8-K, whose release the parser read a guide from
    while the outlook reader matched none: our gap, not inapplicable."""
    g = _entry(_gaps("CNXC"), "drawdown_cause.revised_guidance")
    assert g.type == OUR and "2026-06-29" in g.basis
    assert g.source_ref is not None and "0001803599-26-000133" in g.source_ref


def _lookup_failed(m: dict[str, Any]) -> None:
    """BRBR's current window as `mechanical._read_gaps` writes it when the filing index could not
    be read: the gap-down dates known, no filing, the shape UNKNOWN."""
    dc = m["drawdown_cause"]
    dc["filings"] = []
    dc["shape"] = {"value": None, "source_ref": None, "status": "unknown",
                   "note": "EDGAR filing index unavailable — the gap-down dates are known but "
                           "their causes could not be read; read the filings at those dates by "
                           "hand"}
    dc["revised_guidance"] = {"value": None, "source_ref": None, "status": "unknown",
                              "note": "no catalyst 8-K to follow for a revised-guidance exhibit"}


def _at_anchor_unread(m: dict[str, Any]) -> None:
    """MCK's at-anchor window as `mechanical._gap_window` writes it when the stored closes do not
    cover it: nothing read, every part UNKNOWN."""
    unread = {"value": None, "source_ref": None, "status": "unknown",
              "note": "no stored close on or before 2026-10-29, so this window is not read"}
    a = m["drawdown_cause"]["anchor"]["at_anchor"]
    a.update(shape=dict(unread), gap_down_dates=dict(unread), filings=[],
             revised_guidance=dict(unread))


@pytest.mark.parametrize("t,edit,field", [
    ("BRBR", _lookup_failed, "drawdown_cause.revised_guidance"),
    ("MCK", _at_anchor_unread, "drawdown_cause.anchor.at_anchor.revised_guidance")])
def test_a_window_we_could_not_read_is_our_gap_never_inapplicable(t: str, edit: Edit,
                                                                   field: str) -> None:
    """(−) F1: `filings` is also [] when the 8-K index lookup failed or the window was never read
    — one-field edits of real pages, the shapes `mechanical` writes. Our gap, not 'does not
    apply'."""
    g = _entry(_gaps(t, edit), field)
    assert g.type == OUR and ".shape" in g.basis


# --------------------------------------------------------------- 3. company's normal practice

def test_smpl_has_given_no_adjusted_eps_guide_in_anything_read() -> None:
    """(+) None of SMPL's six releases states an adjusted-EPS guide and CIQ, reaching its newest,
    records none since the oldest — its last EPS guide is dated 2023-06-29, which the basis states
    (F10: more than four quarters before the page's price date)."""
    g = _entry(_gaps("SMPL"), EPS)
    assert g.type == PRACTICE and "6 releases" in g.basis
    assert "CIQ's last such guide is dated 2023-06-29" in g.basis


def test_a_guide_ciq_records_is_not_practice() -> None:
    """(−) MCK's releases read no guide either, but CIQ records one: not the company's practice."""
    assert _entry(_gaps("MCK"), EPS).type != PRACTICE


def test_the_second_read_decides_practice() -> None:
    """(−) SMPL with ONE CIQ EPS row added on its newest release's date is no longer practice."""
    g = _entry(_gaps("SMPL", _ciq_row("EPS Normalized", "2026-10-27")), EPS)
    assert g.type == UNDETERMINED and "records one since" in g.basis


def test_one_release_is_no_practice() -> None:
    """(−) SMPL cut to its newest release: one release shows no practice."""
    def edit(m: dict[str, Any]) -> None:
        rels = m["primary_source"]["releases"]
        m["primary_source"]["releases"] = [max(rels, key=lambda r: r["filed"])]
    g = _entry(_gaps("SMPL", edit), EPS)
    assert g.type == UNDETERMINED and g.basis == "one release was read"


def test_a_stop_inside_four_quarters_is_not_practice() -> None:
    """(−) F10, the coordinator's default: GOOGL with its CIQ EPS rows re-dated to 2026-01-15 —
    before every release read, inside four quarters of its price date — would be a change, which
    one read cannot show: not determined."""
    def edit(m: dict[str, Any]) -> None:
        _redate("EPS Normalized", "2026-01-15")(m)
        _redate("EPS (GAAP)", "2026-01-15")(m)
    g = _entry(_gaps("GOOGL", edit), EPS)
    assert g.type == UNDETERMINED and "within four quarters" in g.basis


@pytest.mark.parametrize("t,field", [("MVST", ADJ), ("MVST", EPS), ("PARR", ADJ), ("PARR", EPS),
                                     ("VITL", EPS), ("IT", EPS)])
def test_a_ciq_export_short_of_the_newest_release_decides_nothing(t: str, field: str) -> None:
    """(−) F4, guard G9 (CIQ's reach): on each real entry, CIQ's export does not reach the newest
    release read, so CIQ cannot agree on the span: not practice."""
    g = _entry(_gaps(t), field)
    assert g.type == UNDETERMINED and "before the newest release read" in g.basis


def test_a_ciq_guide_inside_the_span_read_is_not_practice() -> None:
    """(−) F4, guard G10 (the span runs from the OLDEST release read): NCNO's CIQ EPS guide is
    dated 2025-12-03, inside its releases' span though before the newest."""
    g = _entry(_gaps("NCNO"), EPS)
    assert g.type == UNDETERMINED and "records one since 2025-05-28" in g.basis


# ----------------------------------------------------------------- 4. change or deviation

def test_no_frozen_page_reads_a_change() -> None:
    """THE CORPUS FINDING, pinned: none of the 28 frozen pages reads type 4."""
    found = {t: [g.item for g in _gaps(t) if g.type == CHANGE] for t in CORPUS}
    assert {t: v for t, v in found.items() if v} == {}


def test_fubos_silent_releases_are_not_a_change() -> None:
    """(−) FUBO as committed: its April release states a Fiscal 2026 adjusted-EBITDA guide, the two
    since state none — and the company-adjusted figures are ours, since the company guides it."""
    assert _entry(_gaps("FUBO"), ADJ).type == OUR


def test_the_strongest_stop_shape_is_still_not_a_change() -> None:
    """(−) F5: TGT's March release states an adjusted-EPS guide and its two releases since (to
    2026-08-19) state none; its two CIQ EPS rows — the only evidence refuting a stop — moved to the
    March release, CIQ still reaching the newest through its other rows. The shape a withdrawn
    guide would leave, and neither half of it is evidence: not determined, saying why."""
    def edit(m: dict[str, Any]) -> None:
        _redate("EPS Normalized", "2026-03-03")(m)
        _redate("EPS (GAAP)", "2026-03-03")(m)
    g = _entry(_gaps("TGT", edit), EPS)
    assert g.type == UNDETERMINED
    assert "no evidence of a stop" in g.basis and "2026-03-03" in g.basis


@pytest.mark.parametrize("kw", [
    {}, {"disclosed": "x", "stopped": "2026-01-01"},
    {"disclosed": "x", "stopped": "2026-01-01", "stopped_ref": "r"}])
def test_a_change_names_what_where_and_when(kw: dict[str, str]) -> None:
    """(−) S1: a change without all of its evidence — `source_ref` included — is refused."""
    with pytest.raises(ValueError, match="what was disclosed"):
        DisclosureGap(item="x", fields=["f"], type=CHANGE, basis="b", **kw)


def test_a_change_with_all_its_evidence_stands() -> None:
    """(+) The schema's one positive for type 4: what, where and when, all stated."""
    g = DisclosureGap(item="x", fields=["f"], type=CHANGE, basis="b", disclosed="d",
                      source_ref="r", stopped="2026-01-01", stopped_ref="r2")
    assert g.stopped == "2026-01-01"


@pytest.mark.parametrize("kind", [t for t in GAP_TYPES if t != CHANGE])
@pytest.mark.parametrize("leg", ["disclosed", "stopped", "stopped_ref"])
def test_only_a_change_carries_a_stop(kind: GapType, leg: str) -> None:
    """(−) S2: no other type carries any leg of a stop."""
    with pytest.raises(ValueError, match="only a change"):
        DisclosureGap(item="x", fields=["f"], type=kind, basis="b", **{leg: "v"})


# ---------------------------------------------------------------- 5. type not determined

@pytest.mark.parametrize("t", ["ORKA", "TECX"])
def test_no_second_read_gives_no_company_type(t: str) -> None:
    """(+) ORKA and TECX carry no CIQ Guidance sheet: every guide gap is not determined."""
    for field in (EPS, "primary_source.current_guide"):
        assert _entry(_gaps(t), field).type == UNDETERMINED


@pytest.mark.parametrize("t", ["AMZN", "AORT", "GOOGL", "NKE", "TJX", "WLK"])
def test_segment_ebitda_beside_a_10k_segment_measure_is_not_decided_by_one_read(t: str) -> None:
    """(+) F3: the 10-K's segments carry the filer's own measure, and that ONE read cannot show the
    filer discloses no segment EBITDA (the instance read tries its measures in a fixed order)."""
    g = _entry(_gaps(t), "concentration.segment_ebitda")
    assert g.type == UNDETERMINED and "one read cannot show" in g.basis


def test_a_decidable_gap_is_determined() -> None:
    """(−) SMPL's adjusted-EPS gap is decided (practice), not left undetermined."""
    assert _entry(_gaps("SMPL"), EPS).type != UNDETERMINED


# ------------------------------------------------------ survival: inapplicable leverage (G13)

@pytest.mark.parametrize("t", ["ORKA", "TECX"])
def test_leverage_on_non_positive_ebitda_does_not_apply(t: str) -> None:
    """(+) F4, guard G13: ORKA's and TECX's LTM EBITDA is not positive."""
    g = _entry(_gaps(t), "quality.net_debt_to_ebitda")
    assert g.type == NA and "not positive" in g.basis


def test_unknown_leverage_on_positive_ebitda_is_not_inapplicable() -> None:
    """(−) FUBO's net leverage is UNKNOWN without a non-positive LTM EBITDA on the page."""
    assert _entry(_gaps("FUBO"), "quality.net_debt_to_ebitda").type == UNDETERMINED


# ------------------------------------------------------------------ as of the price date (F12)

def test_a_release_after_the_price_date_is_not_read() -> None:
    """ORKA's 2026-10-26 release postdates its 2026-10-23 price date: the gap test does not read
    it (the layer itself still carries it — STATE row 57)."""
    mech = _mech("ORKA")
    assert gaps.price_date(mech) is not None and gaps.price_date(mech).isoformat() == "2026-10-23"
    assert mech.primary_source is not None
    assert max(r.filed for r in mech.primary_source.releases if r.filed).isoformat() == "2026-10-26"
    read = gaps.releases_read(mech)
    assert read is not None and all(r.filed and r.filed.isoformat() <= "2026-10-23" for r in read)


def test_a_guide_after_the_price_date_changes_no_type() -> None:
    """SMPL with a release AND a CIQ EPS row, both dated after its 2026-11-03 price date, each
    stating an adjusted-EPS guide: its practice entry is unchanged."""
    def edit(m: dict[str, Any]) -> None:
        rels = m["primary_source"]["releases"]
        late = copy.deepcopy(max(rels, key=lambda r: r["filed"]))
        late["filed"] = "2026-11-10"
        late["guidance"] = [{"metric": "adjusted eps", "period": "next-fy", "low": 1.0,
                             "high": 2.0, "unit": "$/sh", "basis": "level",
                             "qualitative": False, "verbatim": "x",
                             "source_ref": late["source_ref"]}]
        rels.append(late)
        _ciq_row("EPS Normalized", "2026-11-10")(m)
    assert _entry(_gaps("SMPL", edit), EPS) == _entry(_gaps("SMPL"), EPS)


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


def test_the_tiebreak_cannot_rewrite_a_row_the_gap_test_reads() -> None:
    """F8: the filed tiebreak rewrites LTM cells AFTER the assembly types the gaps; the rows it may
    rewrite and the rows the survival items read are disjoint, so no entry can go stale."""
    rewritable = set(filed_tiebreak.MAPPING) | set(filed_tiebreak.CONTAINING)
    assert rewritable and not rewritable & set(gaps.ANNUAL_ROWS_READ)


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
    ((("A", 60.0), ("B", 40.0)), 2), ((), None),
    ((("A", 66.0), ("B", 38.0), ("Intersegment Sales", -4.0)), 2),
    ((("A", 97.0), ("Retail", 8.0), ("Corporate and Other", -5.0)), 2),
    ((("Retail", 101.0), ("Eliminations", -1.0)), 1)])
def test_segment_count_and_the_rendered_line_never_disagree(
        items: tuple[tuple[str, float], ...], want: int | None) -> None:
    """A lone segment at ≥99.5% is 1; one short of it is None; a split is its segments, its
    reconciling lines left out (F11: eliminations, intersegment, corporate); no roster is None —
    and the transform's reading of the rendered line agrees every time."""
    b = _roster(*items)
    assert ciq_sheets.segment_count(b) == want
    assert vr.segment_count_from_line(ciq_sheets.segments(b)) == want


def _assemble_lly(bundle: CiqBundle) -> MechanicalLayer:
    """LLY's page assembled on its real inputs (`tests/test_asof_cut.py`'s harness: no network),
    with ``bundle`` as its CIQ."""
    from datetime import date

    from tests.test_asof_cut import _iwm_bars, _lly_bars, _LlySec, _Refused, _Store
    from vinci.dossier.mechanical import assemble_mechanical
    from vinci.edgar.client import EdgarClient
    from vinci.graph.exposure import ExposureGraph
    from vinci.schemas.data_record import Identity
    from vinci.screens.assemble import build_price_record, enrich_with_fundamentals
    ref = date(2026, 10, 2)
    sec = _LlySec()
    ident = Identity(internal_id="SEC-0000059478-LLY", issuer_id="ISS-0000059478",
                     cik="0000059478", ticker="LLY", mic="XNYS", exchange="NYSE",
                     eod_symbol="LLY", name="Eli Lilly and Company", sic="2834")
    edgar = EdgarClient(http=cast(Any, sec))
    bars = [b for b in _lly_bars() if b.bar_date <= ref]
    rec = build_price_record(ident, price_bars=bars, benchmark_bars=_iwm_bars(),
                             reference_date=ref, staleness_days=5)
    rec = enrich_with_fundamentals(rec, edgar=edgar, price_bars=bars, reference_date=ref)
    mech, _flags = assemble_mechanical(
        rec, store=cast(Any, _Store()), edgar=edgar, http=cast(Any, sec),
        finra=cast(Any, _Refused()), graph=ExposureGraph(), resolver=cast(Any, None),
        bundle=bundle, reference_date=ref)
    return mech


def test_the_assembly_hands_the_builder_its_ciq_segment_count() -> None:
    """F7, through the whole assembly with LLY's real cut Segments sheet: the count reaches the
    gap test (a builder handed None would write "the roster cannot be read")."""
    mech = _assemble_lly(_segments_bundle("LLY"))
    assert mech.disclosure_gaps is not None
    assert mech.disclosure_gaps == gaps.disclosure_gaps(mech, segment_count=1)
    seg = next(g for g in mech.disclosure_gaps if g.item == "segment profit by segment")
    assert "reads one segment" in seg.basis


def test_the_assembly_writes_the_gap_test_last() -> None:
    """Through the whole assembly with an empty CIQ bundle: the field is written from the finished
    layer."""
    mech = _assemble_lly(CiqBundle.from_files("LLY", []))
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
    ("Refining 97%; Retail 8%; Logistics 4%; Corporate and Other -8%", 3),
    ("Performance and Essential Materials 66%; Housing and Infrastructure Products 37%; "
     "Intersegment Sales -4%", 2)])
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

#: RULE 8 ITSELF (F6): a code-written constant, so its exact text is pinned — a token lint passes
#: "a company's normal practice may be raised as a risk" and "read as bearish". Moving it is a
#: prompt change, measured on the panel (RUNBOOKS §n).
RULE_8_SHA256 = "6e7c6f88b703710714adf7f54d64e84a15f84d17de039857b48ca6a5675c6fff"


def old_wording(text: str) -> list[str]:
    return [w for w in OLD_WORDING if w.lower() in text.lower()]


def _rule_8(sleeve: str) -> str:
    return "(8) " + syn.system_for(sleeve).split("(8) ", 1)[1].split(" (9) ", 1)[0]


@pytest.mark.parametrize("sleeve", sorted(SLEEVES))
def test_rule_8s_old_wording_cannot_return(sleeve: str) -> None:
    """The prompt no longer tells the model a missing disclosure is a bearish risk, nor asks a
    trailing multiple for a "trailing-only" tag, in any book's system prompt or tool schema."""
    assert old_wording(syn.system_for(sleeve) + json.dumps(syn.tool_for(sleeve))) == []


@pytest.mark.parametrize("phrase", OLD_WORDING)
def test_every_entry_of_the_old_wording_list_is_live(phrase: str) -> None:
    assert old_wording(syn.system_for("overshoot") + f" {phrase} ") == [phrase]


@pytest.mark.parametrize("sleeve", sorted(SLEEVES))
def test_rule_8_is_exactly_the_gap_test(sleeve: str) -> None:
    """F6: every book's rule 8 is the one text, by sha256, naming the five types the layer
    writes."""
    rule = _rule_8(sleeve)
    assert hashlib.sha256(rule.encode()).hexdigest() == RULE_8_SHA256
    assert rule.startswith("(8) THE GAP TEST") and "disclosure_gaps" in rule
    for t in GAP_TYPES:
        assert f"'{t}'" in rule, t


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


# ------------------------------------------------------------- review round 0 (code-review high)

def test_a_filing_that_cannot_be_placed_decides_neither_drawdown_item() -> None:
    """(−) CNXC with its gap-down 8-K's date unreadable: the outlook AND the company-adjusted
    EBITDA read 'type not determined'."""
    def edit(m: dict[str, Any]) -> None:
        m["drawdown_cause"]["filings"][0]["filing_date"] = "n/a"
    gs = _gaps("CNXC", edit)
    assert _entry(gs, "drawdown_cause.revised_guidance").type == UNDETERMINED
    assert _entry(gs, ADJ).type == UNDETERMINED


@pytest.mark.parametrize("t,claim", [("EPAM", "the page states no segment profit from the 10-K"),
                                     ("MCK", "the 10-K segment-profit read is UNKNOWN")])
def test_a_segment_gap_claims_no_xbrl_read_it_did_not_make(t: str, claim: str) -> None:
    """F9: an absent `segment_profit` (a single-segment instance, no CIK, no annual report) and an
    UNKNOWN one (any failed read) are stated as no more than the page shows."""
    g = next(g for g in _gaps(t) if g.item == "segment profit by segment")
    assert claim in g.basis
    for overclaim in ("tags fewer than two", "found segment contexts", "on its axis"):
        assert overclaim not in g.basis


# -------------------------------------------------- review round 2: guards no real entry decides

def _tgt_stop(m: dict[str, Any]) -> None:
    _redate("EPS Normalized", "2026-03-03")(m)
    _redate("EPS (GAAP)", "2026-03-03")(m)


def test_a_stop_shorter_than_a_quarter_is_not_the_stop_shape() -> None:
    """(−) G6: TGT's stop edit with its releases after March cut to one, on 2026-04-15 — six weeks
    after the guide, which any 8-K could be: not the stop shape at all."""
    def edit(m: dict[str, Any]) -> None:
        _tgt_stop(m)
        rels = [r for r in m["primary_source"]["releases"] if r["filed"] <= "2026-05-20"]
        for r in rels:
            if r["filed"] == "2026-05-20":
                r["filed"] = "2026-04-15"
        m["primary_source"]["releases"] = rels
    g = _entry(_gaps("TGT", edit), EPS)
    assert g.type == UNDETERMINED and "do not span a full quarter" in g.basis


def test_a_stop_ciq_cannot_see_is_not_the_stop_shape() -> None:
    """(−) G7: TGT's stop edit with every CIQ row dated in March: CIQ's export no longer reaches
    the releases since, so CIQ cannot be silent about them."""
    def edit(m: dict[str, Any]) -> None:
        for r in _ciq_rows(m):
            r["dated"] = min(r["dated"], "2026-03-03")
    g = _entry(_gaps("TGT", edit), EPS)
    assert g.type == UNDETERMINED and "before the newest release read" in g.basis


def test_a_failed_10k_read_on_a_single_segment_filer_decides_nothing() -> None:
    """(−) G12: ROST with its 10-K segment-profit read UNKNOWN: CIQ's one segment and a failed read
    do not agree, so not 'does not apply'."""
    def edit(m: dict[str, Any]) -> None:
        m["concentration"]["segment_profit"] = {
            "value": None, "source_ref": None, "status": "unknown",
            "note": "10-K XBRL instance unreadable (HttpError)"}
    g = _entry(_gaps("ROST", edit), "concentration.segment_profit")
    assert g.type == UNDETERMINED and "read is UNKNOWN" in g.basis


def test_an_fcf_sign_with_no_ltm_cash_flow_on_the_page_is_not_ours() -> None:
    """(−) G14: LLY with its annual table's LTM FCF, CFO and Capex cells blank: nothing on the page
    shows the read we missed."""
    def edit(m: dict[str, Any]) -> None:
        t = m["financial_summary"]["annual"]["value"]
        col = t["columns"].index("LTM")
        for r in t["rows"]:
            if r["label"] in ("FCF ($M)", "CFO ($M)", "Capex ($M)"):
                r["values"][col] = None
    g = _entry(_gaps("LLY", edit), "quality.fcf_sign")
    assert g.type == UNDETERMINED


def test_one_unreadable_ciq_date_refuses_the_second_read() -> None:
    """(−) G1: MCK with one CIQ guide row's date unreadable — it could be the row that refutes a
    type — has no second read: its EPS gap is not determined, never ours off the other rows."""
    def edit(m: dict[str, Any]) -> None:
        _ciq_rows(m)[-1]["dated"] = "—"
    g = _entry(_gaps("MCK", edit), EPS)
    assert g.type == UNDETERMINED and "no second read" in g.basis


def test_an_undated_release_refuses_the_ladder() -> None:
    """(−) G2: SMPL with one release's filing date missing: the releases cannot be ordered or cut,
    so no guide entry is decided."""
    def edit(m: dict[str, Any]) -> None:
        m["primary_source"]["releases"][0]["filed"] = None
    g = _entry(_gaps("SMPL", edit), EPS)
    assert g.type == UNDETERMINED and "carries no filing date" in g.basis


def test_a_declared_dividend_is_no_guide() -> None:
    """(−) G4: WLK with its capex and interest guides dated back to 2019 and its DPS row on its
    2026-08-04 release: a declared dividend is not an outlook, so the current guide is not our
    gap."""
    def edit(m: dict[str, Any]) -> None:
        for r in _ciq_rows(m):
            if r["metric"] in ("Capital Expenditure", "Interest Expense"):
                r["dated"] = "2019-01-01"
            if r["metric"] == "DPS":
                r["dated"] = "2026-08-04"
    assert _entry(_gaps("WLK", edit), "primary_source.current_guide").type != OUR


def test_a_two_segment_filer_is_not_single_segment() -> None:
    """(−) G11: EPAM's CIQ roster names two segments: its absent segment profit is ours."""
    g = _entry(_gaps("EPAM"), "concentration.segment_ebitda")
    assert g.type == OUR and "across 2 segments" in g.basis
