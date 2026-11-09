"""STATE row 57 — the fact layer cuts its releases and CIQ's guidance at the page's price date,
where it builds them, so every reader inherits the cut; what the cut leaves out is kept in the
JSON's audit tier and named in a caveat, never dropped silently.

- Releases: assembly has read EDGAR as it stood on the price date since #884, so no release filed
  after it is fetched; the 8-Ks it leaves out are now NAMED (`primary_source.
  releases_after_price_date`). A page built before #884 keeps such a release: ORKA's, at the
  panel's freeze, holds one filed 2026-10-26 beside its 2026-10-23 price date. `asof_cut`
  (`vinci/evals/variants.py`) cuts a committed layer by the same rule, for the $0 measurement.
- CIQ's Guidance sheet: a cell CIQ dates after the price date is not read. An actual is cut
  alone; a GUIDE withholds the whole read, because CIQ keeps each period's latest guide only and
  the one standing on the price date may have been overwritten (`ciq_sheets._reads_at_cut`).

Fixtures are real: the pages committed at the panel's freeze, and UBER's and LLY's Guidance
sheets as exported (on disk 2026-11-09), cut down to the cells these pins read
(`tests/fixtures/ciq_guidance_asof_cut.json`). The assembly end of both halves is pinned in
`tests/test_asof_cut.py`, on LLY's real inputs."""
from __future__ import annotations

import copy
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier import gaps
from vinci.dossier import mechanical as dm
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.flags import partition
from vinci.dossier.schemas import (
    GuideAfterPriceDate,
    MechanicalLayer,
    ReleaseAfterPriceDate,
    ReleaseExtract,
    SourceStatus,
)
from vinci.dossier.synthesis import NOT_SENT
from vinci.edgar.asof import within_cut
from vinci.evals import replay as rp
from vinci.evals import variants as vr
from vinci.evals.capture_child import capture_calls, pre_synthesis_mech

ROOT = Path(__file__).resolve().parents[1]
PANEL = rp.load_panel_file()
GUIDANCE: dict[str, Any] = json.loads(
    (ROOT / "tests/fixtures/ciq_guidance_asof_cut.json").read_text())["names"]
D = date.fromisoformat
UNKNOWN = SourceStatus.UNKNOWN

#: the 28 pages committed at the freeze (`git ls-tree <freeze> data/dossiers/`)
CORPUS = (
    "AMZN", "AORT", "BRBR", "BURL", "CNXC", "EPAM", "FUBO", "GOOGL", "IT", "LLY",
    "MCK", "MVST", "NCNO", "NFLX", "NKE", "ORKA", "PARR", "ROST", "SMPL", "TECX",
    "TGT", "TJX", "UBER", "V", "VITL", "VRRM", "WERN", "WLK",
)
#: ORKA's EX-99.1 of 2026-10-26, on a page priced 2026-10-23
ORKA_LATE = "8-K 0001213900-26-112281 EX-99.1"
ORKA_ACC = "0001213900-26-112281"


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


def _mech(t: str, edit: Any = None) -> MechanicalLayer:
    page = _page(t)
    if edit is not None:
        edit(page["mechanical"])
    return pre_synthesis_mech(page)


def _bundle(t: str, edit: Any = None) -> CiqBundle:
    rows = copy.deepcopy(GUIDANCE[t]["sheets"]["estimates|Guidance"])
    if edit is not None:
        edit(rows)
    path = Path(f"/fixture/{t}-estimates.xls")
    return CiqBundle(ticker=t, workbooks=(CiqWorkbook(kind="estimates", path=path,
                                                      fmt=CiqFormat.BIFF_XLS, freq=None),),
                     _cache={path: {"Guidance": rows}})


# ─── the rule ─────────────────────────────────────────────────────────────────────────────────

def test_the_cut_reads_the_price_date_itself_and_nothing_after_it() -> None:
    day = D("2026-10-23")
    assert within_cut(day, day)
    assert not within_cut(day + timedelta(days=1), day)
    assert within_cut(day + timedelta(days=9_999), None)


def test_the_release_cut_keeps_a_release_filed_on_the_price_date() -> None:
    """ORKA's own four releases: cut on the day the last was filed, all four are read; a day
    before it, that one is the only one left out — each side in the order given."""
    rels = _mech("ORKA").primary_source.releases  # type: ignore[union-attr]
    kept, after = gaps.releases_by_cut(rels, D("2026-10-26"))
    assert kept == list(rels) and after == []
    kept, after = gaps.releases_by_cut(rels, D("2026-10-25"))
    assert [r.source_ref for r in after] == [ORKA_LATE]
    assert kept == list(rels[1:])


def test_an_undated_release_cannot_be_cut() -> None:
    undated = ReleaseExtract(source_ref="8-K X EX-99.1")
    with pytest.raises(ValueError, match="no filing date"):
        gaps.releases_by_cut([undated], D("2026-10-23"))
    assert gaps.releases_by_cut([undated], None) == ([undated], [])


# ─── CIQ's Guidance sheet, on real exports ────────────────────────────────────────────────────

def _blank_fq4_guides(rows: list[list[Any]]) -> None:
    """UBER's one edit: its two FQ4 2026 guides (EPS Normalized, EBITDA — both dated
    2026-11-04) removed, guide and date, so the cut meets only the FQ3 actuals of that day."""
    starts = cs._guidance_starts(rows)
    for i, bi in enumerate(starts):
        if str(rows[bi][0]).strip() not in ("EPS Normalized", "EBITDA"):
            continue
        end = starts[i + 1] if i + 1 < len(starts) else len(rows)
        gdate, guide, _ = cs._guidance_rows(rows, bi, end)
        assert gdate is not None and guide is not None
        header = cs._nearest_period_header(rows, bi)
        assert header is not None
        (j,) = [j for j in range(1, len(header)) if str(header[j]).strip() == "FQ4 2026"]
        rows[gdate][j] = rows[guide][j] = "-"


def test_a_guide_dated_after_the_price_date_withholds_the_guidance_read() -> None:
    """UBER's export dates its FQ4 2026 guides 2026-11-04. At a 2026-11-03 price date neither is
    read — and no other guide is offered as the latest in their place: CIQ keeps each period's
    latest guide only, so nothing on the sheet shows what stood on the price date. The bridge,
    its rows and the revenue guide read UNKNOWN, saying why; all four cells after the cut are
    listed."""
    b, cut = _bundle("UBER"), D("2026-11-03")
    rows = cs.guidance_bridge_rows(b, reference_date=D("2026-10-16"), cut=cut)
    flat = cs.guidance_bridge(b, reference_date=D("2026-10-16"), cut=cut)
    assert (rows.status, rows.note) == (UNKNOWN, cs.GUIDANCE_NOT_AT_CUT)
    assert (flat.status, flat.note) == (UNKNOWN, cs.GUIDANCE_NOT_AT_CUT)
    assert cs.revenue_guide_lohi(b, reference_date=D("2026-10-16"), cut=cut) == (None,) * 4
    after = cs.guidance_after_cut(b, cut=cut)
    rows_ = GUIDANCE["UBER"]["sheets"]["estimates|Guidance"]
    for g in after:   # each ref is the address its value is read from
        r, c = (int(x) - 1 for x in g.source_ref.split("row ")[1].split(", column "))
        assert str(rows_[r][c]).strip() == g.value, g
    assert [(g.metric, g.period, g.read, g.value, g.dated) for g in after] == [
        ("EPS Normalized", "FQ3 2026", "actual", "0.88", "2026-11-04"),
        ("EPS Normalized", "FQ4 2026", "guide", "0.95 - 0.99", "2026-11-04"),
        ("EBITDA", "FQ3 2026", "actual", "2963.0", "2026-11-04"),
        ("EBITDA", "FQ4 2026", "guide", "3,130.00 - 3,230.00", "2026-11-04"),
    ]


def test_a_guide_dated_on_the_price_date_is_read() -> None:
    """The boundary, on the same sheet: at a 2026-11-04 price date the guides of that day are the
    latest, and their FQ3 actuals count."""
    b, cut = _bundle("UBER"), D("2026-11-04")
    got = cs.guidance_bridge_rows(b, reference_date=D("2026-10-16"), cut=cut).value or []
    eps = next(r for r in got if r.metric == "EPS Normalized")
    assert (eps.latest_guide, eps.period, eps.dated, eps.record) == (
        "'0.95 - 0.99'", "FQ4 2026", "2026-11-04", "actual ≥ floor 3/3")
    assert cs.guidance_after_cut(b, cut=cut) == []
    assert got == (cs.guidance_bridge_rows(b, reference_date=D("2026-10-16")).value or [])


def test_an_actual_reported_after_the_price_date_leaves_the_record_and_rebuilds_the_page() -> None:
    """With UBER's FQ4 guides edited out, what the cut meets on its page's 2026-10-23 price date
    is the FQ3 actuals CIQ dates 2026-11-04. They leave the delivery record — and today's export,
    cut so, rebuilds the committed page's seven rows exactly, CIQ's block order apart (main read
    3/3 and 24/24, and FQ3 2026 as the most recent outcome, from results not yet out)."""
    b = _bundle("UBER", _blank_fq4_guides)
    page = _mech("UBER")
    cut = gaps.price_date(page)
    assert cut == D("2026-10-23")
    got = cs.guidance_bridge_rows(b, reference_date=D("2026-10-16"), cut=cut).value or []
    committed = page.catalyst_path.guidance_bridge_rows.value  # type: ignore[union-attr]
    assert committed is not None
    assert sorted(got, key=lambda r: r.metric) == sorted(committed, key=lambda r: r.metric)
    assert [(g.metric, g.read, g.dated) for g in cs.guidance_after_cut(b, cut=cut)] == [
        ("EPS Normalized", "actual", "2026-11-04"), ("EBITDA", "actual", "2026-11-04")]
    uncut = {r.metric: r for r in cs.guidance_bridge_rows(b, reference_date=D("2026-10-16")).value
             or []}
    assert (uncut["EPS Normalized"].record, uncut["EPS Normalized"].most_recent) == (
        "actual ≥ floor 3/3", "FQ3 2026 MET")


def test_lilly_s_export_cut_at_its_pages_price_date_rebuilds_the_page() -> None:
    """The positive half on a second real sheet: LLY's export holds nothing dated after its
    committed page's 2026-11-02 price date, and cut there it reads exactly the page's rows."""
    page = _mech("LLY")
    cut = gaps.price_date(page)
    assert cut == D("2026-11-02")
    b = _bundle("LLY")
    assert cs.guidance_after_cut(b, cut=cut) == []
    got = cs.guidance_bridge_rows(b, reference_date=D("2026-10-16"), cut=cut).value
    assert got == page.catalyst_path.guidance_bridge_rows.value  # type: ignore[union-attr]


# ─── the frozen pages, through the harness transform ──────────────────────────────────────────

@pytest.mark.parametrize("t", [t for t in CORPUS if t != "ORKA"])
def test_a_page_with_nothing_after_its_price_date_is_left_exactly_as_committed(t: str) -> None:
    m = _mech(t)
    assert vr.asof_cut(m, vr.Context(page=_page(t))) == m


def test_orkas_late_release_reaches_neither_its_guide_nor_its_adjusted_eps() -> None:
    """ORKA's 2026-10-26 EX-99.1 sits in the committed list beside a 2026-10-23 price date. Cut,
    it leaves `releases` for the audit tier, and the two fields read from the list are re-derived
    from the three left: the current guide counts three releases, and the adjusted-EPS note names
    the 2026-08-10 release as the newest. Nothing else moves."""
    before = _mech("ORKA")
    after = vr.asof_cut(before, vr.Context(page=_page("ORKA")))
    ps, ps0 = after.primary_source, before.primary_source
    assert ps is not None and ps0 is not None
    assert [r.source_ref for r in ps.releases] == [r.source_ref for r in ps0.releases[1:]]
    assert ps.releases_after_price_date == [
        ReleaseAfterPriceDate(filed=D("2026-10-26"), source_ref=ORKA_LATE)]
    assert ps.current_guide is not None
    assert ps.current_guide.note == "no guide in any of the 3 parsed release(s)"
    assert after.valuation.adjusted_eps.note == (
        "no revised guidance at the drawdown to read an adjusted figure from; the newest EX-99.1 "
        "release, 8-K 0001213900-26-086933 EX-99.1 (filed 2026-08-10), states no annual "
        "adjusted-EPS guide the parser reads")
    untouched = {"primary_source": {"releases", "current_guide", "releases_after_price_date"},
                 "valuation": {"adjusted_eps"}}
    assert after.model_dump(exclude=untouched) == before.model_dump(exclude=untouched)
    assert vr.asof_cut(after, vr.Context(page=_page("ORKA"))) == after   # idempotent


def test_orkas_late_release_is_in_no_synthesis_request() -> None:
    """End to end: the request the synthesis would send for ORKA's frozen page names the
    2026-10-26 release; cut, it does not."""
    (base,) = capture_calls(_page("ORKA"), None, draws=1)
    (cand,) = capture_calls(_page("ORKA"), None, draws=1, transforms=["asof_cut"])
    assert ORKA_ACC in json.dumps(base)
    assert ORKA_ACC not in json.dumps(cand)


def test_the_transform_refuses_what_it_cannot_rebuild() -> None:
    def cited(m: dict[str, Any]) -> None:
        m["quality"]["fcf_sign"]["source_ref"] = ORKA_LATE

    def undated(m: dict[str, Any]) -> None:
        m["primary_source"]["releases"][0]["filed"] = None

    for edit, why in ((cited, "cited by a field"), (undated, "no filing date")):
        with pytest.raises(vr.TransformError, match=why):
            vr.asof_cut(_mech("ORKA", edit), vr.Context(page=_page("ORKA")))

    def late_ciq(m: dict[str, Any]) -> None:
        m["catalyst_path"]["guidance_bridge_rows"]["value"][0]["dated"] = "2026-11-04"

    with pytest.raises(vr.TransformError, match="CIQ guide row"):
        vr.asof_cut(_mech("SMPL", late_ciq), vr.Context(page=_page("SMPL")))


def test_a_late_release_carrying_content_is_refused() -> None:
    """A dropped release with a guide in it feeds readers the transform does not re-derive."""
    m = _mech("SMPL")
    ps = m.primary_source
    assert ps is not None
    guided = next(r for r in ps.releases if r.guidance)
    late = guided.model_copy(update={"filed": D("2026-11-04")})
    m = m.model_copy(update={"primary_source": ps.model_copy(
        update={"releases": [late, *ps.releases]})})
    with pytest.raises(vr.TransformError, match="carries content"):
        vr.asof_cut(m, vr.Context(page=_page("SMPL")))


def test_the_transform_is_the_identity_where_the_code_has_no_cut(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delattr(gaps, "releases_by_cut")
    m = _mech("ORKA")
    assert vr.asof_cut(m, vr.Context(page=_page("ORKA"))) is m


# ─── what the cut leaves out: never sent, always stated ───────────────────────────────────────

def test_the_audit_tier_never_reaches_the_synthesis() -> None:
    cut_cell = GuideAfterPriceDate(metric="EPS Normalized", period="FQ4 2026", read="guide",
                                   value="0.95 - 0.99", dated="2026-11-04",
                                   source_ref="CIQ Estimates→Guidance, row 18, column 30")
    m = _mech("UBER")
    assert m.catalyst_path is not None
    m = m.model_copy(update={"catalyst_path": m.catalyst_path.model_copy(
        update={"guidance_after_price_date": [cut_cell]})})
    sent = json.dumps(m.model_dump(exclude=NOT_SENT), default=str)
    assert "guidance_after_price_date" not in sent and "0.95 - 0.99" not in sent
    assert "primary_source" not in m.model_dump(exclude=NOT_SENT)


def test_the_caveat_names_each_input_left_out_and_where_the_json_keeps_it() -> None:
    rel = ReleaseAfterPriceDate(filed=D("2026-10-29"), source_ref="8-K 0000059478-26-000104",
                                items=["2.02", "9.01"])
    actual = GuideAfterPriceDate(metric="EBITDA", period="FQ3 2026", read="actual",
                                 value="2963.0", dated="2026-11-04",
                                 source_ref="CIQ Estimates→Guidance, row 55, column 29")
    guide = actual.model_copy(update={"read": "guide", "period": "FQ4 2026",
                                      "value": "3,130.00 - 3,230.00"})
    one, two = dm.after_price_date_flags(D("2026-10-23"), [rel], [actual])
    assert "8-K 0000059478-26-000104 (filed 2026-10-29)" in one
    assert "2026-10-23" in one and dm.RELEASES_AFTER in one
    assert "EBITDA FQ3 2026 actual 2963.0 (dated 2026-11-04)" in two and dm.GUIDANCE_AFTER in two
    assert "not read at all" not in two          # an actual alone leaves only the record
    (withheld,) = dm.after_price_date_flags(D("2026-10-23"), [], [actual, guide])
    assert "not read at all" in withheld
    assert partition([one, two, withheld])[0] == [one, two, withheld]   # human caveats
    assert dm.after_price_date_flags(D("2026-10-23"), [], []) == []
    assert dm.after_price_date_flags(D("2026-10-23"), None, None) == []


def test_the_refresh_reads_ciqs_guide_as_it_stood_on_the_pages_price_date(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The refresh that rebuilds the guide line re-reads today's export; it reads the guide at
    the PAGE's price date, the one the assembly cut at."""
    from types import SimpleNamespace

    import vinci.dossier.ciq as ciq_mod
    import vinci.dossier.manual_store as ms
    from vinci.dossier import refresh as rf
    from vinci.edgar.primary_source import GuideVerification

    cuts: list[Any] = []

    def fake(rels: list[Any], **k: Any) -> tuple[str, GuideVerification]:
        cuts.append(k["cut"])
        return ("tri", GuideVerification("guide", "not_run"))

    monkeypatch.setattr(dm, "_release_lines", fake)
    monkeypatch.setattr(ms.LocalFolderStore, "from_config", staticmethod(
        lambda _c: SimpleNamespace(files=lambda _t: [])))
    monkeypatch.setattr(ciq_mod.CiqBundle, "from_files", staticmethod(lambda _t, _f: object()))
    mech = _page("CNXC")["mechanical"]
    mech["primary_source"]["basis_triangulation"]["value"] = "tri"
    mech["primary_source"]["guide_verification"]["value"] = "guide"
    mech["primary_source"].pop("guide_verification_check", None)
    rels = [ReleaseExtract.model_validate(r) for r in mech["primary_source"]["releases"]]
    rf._rebuild_release_lines("CNXC", mech, rels, rels, None)
    assert cuts == [D("2026-10-28"), D("2026-10-28")]
    assert cuts[0] == gaps.price_date(MechanicalLayer.model_validate(mech))


def test_the_transform_refuses_a_late_release_cited_by_accession_alone() -> None:
    """A field may cite the dropped 8-K without its exhibit suffix, dashed or not."""
    for ref in (f"8-K {ORKA_ACC}", ORKA_ACC.replace("-", "")):
        def cited(m: dict[str, Any], ref: str = ref) -> None:
            m["quality"]["fcf_sign"]["source_ref"] = ref

        with pytest.raises(vr.TransformError, match="cited by a field"):
            vr.asof_cut(_mech("ORKA", cited), vr.Context(page=_page("ORKA")))


def test_the_transform_refuses_a_ciq_row_whose_date_does_not_parse() -> None:
    def garbled(m: dict[str, Any]) -> None:
        m["catalyst_path"]["guidance_bridge_rows"]["value"][0]["dated"] = "n/a"

    with pytest.raises(vr.TransformError, match="does not parse"):
        vr.asof_cut(_mech("SMPL", garbled), vr.Context(page=_page("SMPL")))


def test_the_transform_refuses_a_guide_line_this_code_does_not_rebuild() -> None:
    def edited(m: dict[str, Any]) -> None:
        m["primary_source"]["current_guide"]["note"] = "a guide line another code version wrote"

    with pytest.raises(vr.TransformError, match="current_guide does not reproduce"):
        vr.asof_cut(_mech("ORKA", edited), vr.Context(page=_page("ORKA")))

