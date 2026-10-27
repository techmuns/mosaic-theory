"""A release ACTUAL is read at its own scale, never out of a range, never off a sub-line
(2026-10-22).

THE DEFECTS, measured on the 118 EX-99.1 exhibits the 27 committed pages cite (main f49c380a):
- RANGE INTO ACTUAL. `_RECON`'s `(?!… to)` lookahead backtracked into the digits: Verra Mobility's
  card printed "adj EBITDA 2026 $38.0M" out of "$380 million to $385 million" and "adj EPS $1.30"
  out of "$1.32 to $1.38", for 104 days.
- UNSCALED BILLIONS. "$2.5 billion" (Uber), "$6.3B" (Visa) and "$1.549 billion" (fuboTV) were
  stored as 2.5 / 6.3 / 1.549 in fields that hold $M.
- SUB-LINES AS TOTALS. Visa's "Other revenue of $1.5 billion" was its revenue.
- And Simply Good's visible card printed its basis-point gross-margin guide as "$-350.0–$-300.0M".

Every excerpt below is VERBATIM from the cited exhibit (accession in each test). Each RED pin was
run against main's parser at build time and read the defect there (the PR shows the run); the pins
themselves assert the fixed behaviour only, so they need no copy of the old parser.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import mechanical as dm
from vinci.dossier import refresh as rf
from vinci.edgar import release_parse as rp

_PAGES = sorted(Path("data/dossiers").glob("*/dossier.json"))

# 8-K 0001193125-26-209031 (Verra Mobility, Q1 2026): the guidance list under "reaffirming"
_VRRM_Q1_26 = (
    "Verra Mobility Announces First Quarter 2026 Financial Results • Total revenue of $223.6 "
    "million • Net income of $26.7 million • Net cash provided from operations of $40.8 million "
    "• Reaffirming fiscal year 2026 guidance MESA, Ariz., May 6, 2026 /PRNewswire/ – Verra "
    "Mobility Corporation (NASDAQ: VRRM), a leading provider of smart mobility technology "
    "solutions. We are providing the following forward-looking guidance, which includes Adjusted "
    "EBITDA, Adjusted EPS, and Free Cash Flow, all of which are non-GAAP financial measures "
    "(defined below). Based on our first quarter 2026 results and our outlook for the remainder of "
    "the year, we are reaffirming 2026 full year guidance for all financial measures. • Total "
    "Revenue of $1,020 million to $1,030 million • Adjusted EBITDA of $405 million to $415 million "
    "• Adjusted EPS of $1.32 to $1.38 • Free Cash Flow of $150 million to $160 million ")

# 8-K 0001403161-26-000103 (Visa, fiscal Q3 2026): the headline bullets and the revenue paragraph
_V_Q3_26 = (
    "Visa Reports Fiscal Third Quarter 2026 Results San Francisco, CA, July 28, 2026 – Visa "
    "(NYSE: V) • GAAP net income of $5.6B or $2.97 per share and non-GAAP net income of $6.3B or "
    "$3.32 per share • Net revenue of $11.6B, an increase of 14%, or 13% on a constant-dollar "
    "basis • Data "
    "processing revenue rose 17% over the prior year to $6.0 billion. International transaction "
    "revenue grew 6% over the prior year to $3.9 billion. Other revenue of $1.5 billion rose 45% "
    "over the prior year.")

# 8-K 0000027419-26-000020 (Target, Q1 2026)
_TGT_Q1_26 = (
    "MINNEAPOLIS (May 20, 2026) – Target Corporation (NYSE: TGT) today announced its first quarter "
    "2026 financial results. The Company reported first quarter GAAP and Adjusted earnings per "
    "share (EPS) of $1.71, compared with prior-year GAAP EPS 2 of $2.27 and Adjusted EPS of "
    "$1.30.  The attached tables provide a reconciliation of non-GAAP to GAAP measures.")

# 8-K 0000027419-26-000012 (Target, Q4 2025): a hyphenated combined header and its Q4 sentence
_TGT_Q4_25 = (
    "Target Corporation Reports Fourth Quarter and Full-Year 2025 Earnings MINNEAPOLIS (March 3, "
    "2026) – Target Corporation (NYSE: TGT) today announced its fourth-quarter and full-year 2025 "
    "results. The Company reported fourth-quarter GAAP earnings per share (EPS) of $2.30 and "
    "Adjusted EPS of $2.44, compared with GAAP and Adjusted EPS of $2.41 in 2024. GAAP EPS was "
    "$8.13 and Adjusted EPS was $7.57 for full-year 2025, compared with GAAP and Adjusted EPS of "
    "$8.86 in the prior year.")

# 8-K 0000320187-26-000076 / -000026 (Nike): year-first headers over the income statement — the
# header, then (the release's prose elided) the sentences that close it and the statement's title
_NKE_PRE_TABLE = (
    " * Non-GAAP financial measure. See additional information in the accompanying Divisional "
    "Revenues table. (Tables Follow) NIKE, Inc. CONSOLIDATED STATEMENTS OF INCOME (Unaudited) ")
_NKE_Q4_26 = (
    "NIKE, INC. REPORTS FISCAL 2026 FOURTH QUARTER AND FULL YEAR RESULTS" + _NKE_PRE_TABLE
    + "THREE MONTHS ENDED % "
    "TWELVE MONTHS ENDED % (In millions, except per share data) 5/31/2026 5/31/2025 Change "
    "5/31/2026 5/31/2025 Change Revenues $ 10,972 $ 11,097 -1 % $ 46,398 $ 46,309 0 % Gross "
    "margin 49.2 % 40.3 % 42.9 % 42.7 %")
_NKE_Q3_26 = (
    "NIKE, INC. REPORTS FISCAL 2026 THIRD QUARTER RESULTS" + _NKE_PRE_TABLE
    + "THREE MONTHS ENDED % NINE MONTHS ENDED % "
    "(In millions, except per share data) 2/28/2026 2/28/2025 Change 2/28/2026 2/28/2025 Change "
    "Revenues $ 11,279 $ 11,269 0 % $ 35,426 $ 35,212 1 % Gross margin 40.2 % 41.5 %")

# 8-K 0001193125-26-239351 (Verra Mobility): one verb governing two impact ranges
_VRRM_AVIS = (
    "Verra Mobility expects the termination to reduce Commercial Services’ 2026 annualized revenue "
    "by approximately $135 million to $145 million and 2026 annualized segment profit by "
    "approximately $120 million to $125 million, before taking into account expense reductions.")


def _rows(parser: Any, text: str) -> set[tuple[str, str, float]]:
    return {(r.metric, r.period, round(r.value, 4))
            for r in parser.parse_release(text, source_ref="t").reconciliation}


def _refusals(text: str) -> list[str]:
    return [f for f in rp.parse_release(text, source_ref="t").qa_flags
            if f.startswith(rp.RECON_REFUSAL_PREFIX)]


# --- the parser ----------------------------------------------------------------------------------

def test_a_guidance_range_is_never_an_actual() -> None:
    """THE RED (VRRM Q1 2026): main read "$1.32 to $1.38" as an actual adjusted EPS of $1.30 for the
    quarter. Now no row, and the refusal is LOUD, quoting the range."""
    assert not any(m == "adjusted eps" for m, _p, _v in _rows(rp, _VRRM_Q1_26))
    assert any("Adjusted EPS of $1.32 to $1.38" in f for f in _refusals(_VRRM_Q1_26))


@pytest.mark.parametrize("sentence", [
    "Adjusted EBITDA of $380 million to $385 million",                # VRRM 0001193125-26-239351
    "non-GAAP operating income of $1,200 million to $1,230 million",  # CNXC 0001803599-26-000133
    "Fiscal 2026 Pro Forma Adjusted EBITDA of $80-100 million",       # FUBO 0001493152-26-015252
    "Adjusted EBITDA of $2.37 billion to $2.47 billion",              # UBER 0001543151-26-000011
])
def test_every_range_shape_is_refused(sentence: str) -> None:
    text = f"Results for the second quarter of 2026. • {sentence} •"
    assert _rows(rp, text) == set(), sentence
    assert _refusals(text), sentence


def test_a_billion_is_a_thousand_millions() -> None:
    """THE RED (Visa fiscal Q3 2026): "$6.3B" stored as 6.3 and "Other revenue of $1.5 billion" as
    the revenue. Now $6,300M net income and the $11,600M NET revenue — the sub-line refused."""
    new = _rows(rp, _V_Q3_26)
    assert ("adjusted net income", "Q3 2026", 6300.0) in new
    assert ("revenue", "Q3 2026", 11600.0) in new
    assert not any(v < 1000 for m, _p, v in new if m != "adjusted eps")
    assert any("'other'" in f for f in _refusals(_V_Q3_26))


@pytest.mark.parametrize(("sentence", "value"), [
    ("Adjusted EBITDA of $2.5 billion, up 35%", 2500.0),        # UBER 0001543151-26-000011
    ("Adjusted EBITDA was $86.0 million", 86.0),
    ("Adjusted EBITDA of $500 thousand", 0.5),
    ("Adjusted EBITDA of $6.3B", 6300.0),
])
def test_each_scale_is_read(sentence: str, value: float) -> None:
    text = f"Acme Reports Second Quarter 2026 Results • {sentence} •"
    assert ("adjusted ebitda", "Q2 2026", value) in _rows(rp, text), sentence


def test_a_total_without_a_scale_and_a_per_share_with_one_are_refused() -> None:
    """NEGATIVE: a total whose magnitude is unstated is not given one ($M is never assumed), and a
    per-share figure that states a scale is not a per-share figure."""
    for sentence in ("Adjusted EBITDA of $436 for the quarter", "Adjusted EPS of $1.30 million"):
        text = f"Acme Reports Second Quarter 2026 Results • {sentence} •"
        assert _rows(rp, text) == set(), sentence
        assert _refusals(text), sentence
    ok = "Acme Reports Second Quarter 2026 Results • Non-GAAP EPS of $0.81, up 8% •"
    assert ("adjusted eps", "Q2 2026", 0.81) in _rows(rp, ok)


def test_a_sub_line_is_not_the_companys_revenue() -> None:
    """fuboTV 0001493152-26-021406, verbatim: "North America revenue of $1.57 billion" took the
    quarter's revenue slot from the company's "$1.574 billion". NEGATIVE: Organogenesis's "Net
    product revenue" IS its total — its release names no other revenue line."""
    text = ("Fubo Reports Second Quarter Fiscal 2026 Results • We delivered North America revenue "
            "of $1.57 billion and total subscribers of 5.9 million. • Revenue of $1.574 billion, "
            "compared to $1.125 billion in Q2 fiscal 2025")
    new = _rows(rp, text)
    assert not any(v == 1570.0 for _m, _p, v in new)
    assert any("'america'" in f for f in _refusals(text))
    orgo = ("Organogenesis Holdings Inc. Reports Third Quarter 2025 Financial Results • Net "
            "product revenue of $150.5 million for the third quarter of 2025")
    assert ("revenue", "Q3 2025", 150.5) in _rows(rp, orgo)
    both = orgo + ". Collaboration revenue of $9.0 million for the third quarter of 2025."
    assert ("revenue", "Q3 2025", 150.5) not in _rows(rp, both)


def test_a_figure_joined_to_a_compared_amount_is_refused() -> None:
    """Target, verbatim: "…compared with prior-year GAAP EPS of $2.27 and Adjusted EPS of $1.30."
    Main dropped "$1.30." only because the full stop made it unreadable; read, it would be the
    PRIOR year's figure filed as the quarter's. It is neither — refused, loudly."""
    assert not any(v == 1.3 for _m, _p, v in _rows(rp, _TGT_Q1_26))
    assert any("joined by 'and'" in f for f in _refusals(_TGT_Q1_26))


def test_a_hyphenated_or_year_first_header_is_read() -> None:
    """THE RED (Target, Nike): "Fourth Quarter and Full-Year 2025" and "FISCAL 2026 THIRD QUARTER"
    were read by neither header pattern, so each release fell to an unknown frame and its quarter
    figures took bare years — Target's Q4 adjusted EPS of $2.44 as FY2025, Nike's Q3 gross margin
    of 40.2% as 2025. The quarter is read, and Target's true FY2025 $7.57 with it."""
    assert rp._release_frame(_TGT_Q4_25)[:3] == ("combined", 4, "2025")
    assert rp._release_frame(_NKE_Q4_26)[:3] == ("combined", 4, "2026")
    assert rp._release_frame(_NKE_Q3_26)[:3] == ("quarter", 3, "2026")
    tgt = _rows(rp, _TGT_Q4_25)
    assert {("adjusted eps", "Q4 2025", 2.44), ("adjusted eps", "2025", 7.57)} <= tgt
    # the excerpt's quarterly margin no longer takes a bare year (its label on the full release —
    # Q3 2026 — is pinned on Nike's committed page, end to end, below)
    assert not any(m == "gross margin" and p.isdigit() for m, p, _v in _rows(rp, _NKE_Q3_26))


def test_a_quarter_compared_with_a_bare_year_is_refused() -> None:
    """Target, verbatim: "…Adjusted EPS of $2.44 [Q4 2025], compared with … $2.41 in 2024." The
    $2.41 is the prior-year fourth quarter; filed as FY2024 it was a quarter wearing a year, and
    reading "2024" as Q4 2024 is an inference the release does not make — refused, loudly."""
    assert not any(v == 2.41 for _m, _p, v in _rows(rp, _TGT_Q4_25))
    assert any("a quarter compared with a bare year" in f for f in _refusals(_TGT_Q4_25))


def test_a_date_column_is_not_a_figures_period() -> None:
    """Nike's income statement heads its columns "5/31/2026 5/31/2025": the Q4 gross margin of
    49.2% (the first column) took "2025" from the second. A year inside a numeric date is not
    evidence — and under a combined Q4-and-year header the figure is left unlabelled."""
    assert not any(m == "gross margin" for m, _p, _v in _rows(rp, _NKE_Q4_26))


def test_both_impact_legs_are_read_at_their_scale() -> None:
    """VRRM, verbatim: the second leg inherits the first's "reduce". A match that consumed the high
    side's unit moved the second leg's look-back past that verb and dropped it."""
    got = [(i.metric, i.effect, i.low, i.high) for i in rp._event_impacts(_VRRM_AVIS, "t")]
    assert got == [("revenue", "reduce", 135.0, 145.0),
                   ("segment profit", "reduce", 120.0, 125.0)], got
    big = _VRRM_AVIS.replace("$135 million to $145 million", "$1.35 billion to $1.45 billion")
    assert rp._event_impacts(big, "t")[0].low == 1350.0
    # a bare low side takes the HIGH side's unit, read just after the match ("$1.35 to $1.45
    # billion"); with no unit on either side the magnitude is unstated and nothing is read
    bare = _VRRM_AVIS.replace("$135 million to $145 million", "$1.35 to $1.45 billion")
    assert (rp._event_impacts(bare, "t")[0].low, rp._event_impacts(bare, "t")[0].high) == (
        1350.0, 1450.0)
    none = _VRRM_AVIS.replace("$135 million to $145 million", "$135 to $145")
    assert [i.metric for i in rp._event_impacts(none, "t")] == ["segment profit"]


def test_a_one_off_in_billions_is_in_millions() -> None:
    text = "The quarter included a $1.2 billion goodwill impairment charge related to the segment."
    assert [o.amount for o in rp._one_offs(text, "t")] == [1200.0]


# --- review of #778: each finding's failure scenario, pinned ------------------------------------

@pytest.mark.parametrize("sentence", [
    "Adjusted EBITDA of $380 million to approximately $385 million for the fourth quarter of 2025.",
    "Revenue of $985 million to approximately $995 million for the fourth quarter of 2025.",
    "Adjusted EPS of $1.32 to about $1.38 for the fourth quarter of 2025.",
])
def test_a_qualified_range_is_still_a_range(sentence: str) -> None:
    """(1) A qualifier between the separator and the high side kept the low side as an actual."""
    assert _rows(rp, f"Acme Reports Fourth Quarter 2025 Results • {sentence}") == set(), sentence


def test_a_per_share_impact_is_read_and_an_unscaled_total_impact_is_said() -> None:
    """(2) A per-share impact states no scale and was dropped with no note; it is read as stated.
    NEGATIVE: a total impact with no scale is refused LOUDLY, never silently."""
    eps = ("The divestiture is expected to reduce 2026 adjusted EPS by approximately $0.10 to "
           "$0.15 per share.")
    assert [(i.metric, i.low, i.high) for i in rp._event_impacts(eps, "t")] == [("eps", 0.1, 0.15)]
    notes: list[str] = []
    bare = "The exit is expected to reduce 2026 revenue by approximately $135 to $145."
    assert rp._event_impacts(bare, "t", notes) == []
    assert notes and notes[0].startswith(rp.IMPACT_REFUSAL_PREFIX)


@pytest.mark.parametrize("sentence", [
    "Other net revenue of $1.5 billion for the fourth quarter of 2025",
    "International total revenue of $2.1 billion for the fourth quarter of 2025",
    "Digital net revenue of $2.0 billion for the fourth quarter of 2025",
    "U.S. revenue of $5.0 billion for the fourth quarter of 2025.",
])
def test_a_qualifier_before_a_total_word_or_an_abbreviation_is_a_sub_line(sentence: str) -> None:
    """(3) A total word skipped the qualifier check; (4) an abbreviation's full stop read as a
    clause start. Both are sub-lines, refused."""
    text = f"Acme Reports Fourth Quarter 2025 Results. {sentence}"
    assert not any(m == "revenue" for m, _p, _v in _rows(rp, text)), sentence
    assert any("a sub-line" in f for f in _refusals(text)), sentence


def test_a_company_total_still_reads() -> None:
    """NEGATIVE for (3)/(4): a total word at a clause start, or after a sentence's full stop."""
    for sentence in ("Total net revenue of $11.6 billion for the fourth quarter of 2025",
                     "Revenue of $5.0 billion for the fourth quarter of 2025"):
        text = f"Acme Reports Fourth Quarter 2025 Results. {sentence}"
        assert any(m == "revenue" and v in (11600.0, 5000.0) for m, _p, v in _rows(rp, text))


def test_a_forward_verb_is_not_called_a_sub_line() -> None:
    """(5) "expects revenue of" was refused as a SUB-LINE qualified by 'expects' — a wrong reason;
    the figure is forward-looking and simply not an actual."""
    text = ("Acme Reports Fourth Quarter 2025 Results. The company expects revenue of $3.0 billion "
            "for the first quarter of 2026.")
    assert not any(m == "revenue" for m, _p, _v in _rows(rp, text))
    assert not any("sub-line" in f for f in _refusals(text))


def test_a_moved_impairment_rebuilds_the_lines(monkeypatch: pytest.MonkeyPatch) -> None:
    """(6) The triangulation reads the FY impairment from the one-offs this transform re-reads. On a
    page whose ONLY moved input is a billion-scale impairment (1.2 → 1,200) — no reconciliation row,
    so nothing else the lines read moves — the proven rebuild must still run."""
    mech = json.loads(Path("data/dossiers/VRRM/dossier.json").read_text())["mechanical"]
    acc = "0001193125-26-209031"
    src = f"8-K {acc} EX-99.1"
    mech["primary_source"]["releases"] = [{
        "source_ref": src, "reconciliation": [], "event_impacts": [], "qa_flags": [],
        "one_offs": [{"amount": 1.2, "description": "goodwill impairment charge",
                      "verbatim": "v", "source_ref": src}]}]
    _offline(monkeypatch,
             {acc: ["The quarter included a $1.2 billion goodwill impairment charge."]})
    calls: list[str] = []
    monkeypatch.setattr(rf, "_rebuild_release_lines", lambda t, *a, **k: calls.append(t))
    out = rf.release_figures_transform("VRRM", "x")(mech)
    assert out["primary_source"]["releases"][0]["one_offs"][0]["amount"] == 1200.0
    assert calls == ["VRRM"]


def test_a_per_share_impact_cited_in_prose_refuses() -> None:
    """(7) A per-share impact was labelled $M, so "$0.10 per share" in the prose was never seen."""
    before = {"primary_source": {"releases": [{"source_ref": "8-K x EX-99.1", "event_impacts": [
        {"metric": "eps", "effect": "reduce", "low": 0.10, "high": 0.15, "period": "2026",
         "verbatim": "v", "source_ref": "8-K x EX-99.1"}]}]}}
    after = {"primary_source": {"releases": [{"source_ref": "8-K x EX-99.1"}]}}
    hits = rf.moved_cited_release_figures(before, after, _doc("cuts EPS by $0.10 per share"))
    assert hits and "$/sh" in hits[0]


def test_releases_without_a_cik_refuse() -> None:
    """(8) The transform returned the page unchanged without a CIK and the refresh reported
    success — the old rows stood. It refuses, naming why."""
    mech, _acc = _vrrm_with_the_old_row()
    with pytest.raises(rf.RefreshRefusedError, match="no CIK"):
        rf.release_figures_transform("VRRM", None)(mech)


def test_the_refresh_rebuilds_through_the_assemblers_builder(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(10) ONE composition: the refresh's proof and rebuild call `mechanical._release_lines`, the
    builder `_primary_source` calls — not a hand copy that could drift from it."""
    from types import SimpleNamespace

    import vinci.dossier.ciq as ciq_mod
    import vinci.dossier.manual_store as ms
    from vinci.dossier.schemas import ReleaseExtract
    from vinci.edgar.primary_source import GuideVerification

    seen: list[int] = []

    def fake(rels: list[Any], **_k: Any) -> tuple[str, GuideVerification]:
        seen.append(len(rels))
        check: Any = "not_run" if len(seen) % 2 else "agree"      # the old rows', the new rows'
        return (f"tri {len(seen)}", GuideVerification(f"guide {len(seen)}", check))

    monkeypatch.setattr(dm, "_release_lines", fake)
    monkeypatch.setattr(ms.LocalFolderStore, "from_config", staticmethod(
        lambda _c: SimpleNamespace(files=lambda _t: [])))
    monkeypatch.setattr(ciq_mod.CiqBundle, "from_files", staticmethod(lambda _t, _f: object()))
    mech = json.loads(Path("data/dossiers/CNXC/dossier.json").read_text())["mechanical"]
    mech["primary_source"]["basis_triangulation"]["value"] = "tri 1"
    mech["primary_source"]["guide_verification"]["value"] = "guide 1"
    # the planted lines are the fake's, so the page's own stored outcome is not theirs
    mech["primary_source"].pop("guide_verification_check", None)
    rels = [ReleaseExtract.model_validate(r) for r in mech["primary_source"]["releases"]]
    rf._rebuild_release_lines("CNXC", mech, rels, rels, None)
    assert mech["primary_source"]["basis_triangulation"]["value"] == "tri 2"
    assert seen == [len(rels), len(rels)]
    # THE OUTCOME FOLLOWS ITS LINE: the rebuilt guide line's, never the old one's
    assert mech["primary_source"]["guide_verification_check"] == "agree"
    # and a stored outcome the OLD rows do not give back refuses, as a stored line does
    mech["primary_source"]["basis_triangulation"]["value"] = "tri 3"
    mech["primary_source"]["guide_verification"]["value"] = "guide 3"
    mech["primary_source"]["guide_verification_check"] = "differ"
    with pytest.raises(rf.RefreshRefusedError, match="guide_verification_check does not reproduce"):
        rf._rebuild_release_lines("CNXC", mech, rels, rels, None)


# --- the visible card ----------------------------------------------------------------------------

def test_a_basis_point_guide_prints_in_basis_points() -> None:
    """THE RED (SMPL's card): "$-350.0–$-300.0M" for "decline between 300 and 350 basis points"."""
    assert dm._fmt_guide_range(-350.0, -300.0, "bps") == "−350 to −300 bps"
    assert dm._fmt_guide_range(-375.0, -375.0, "bps") == "−375 bps"
    assert dm._fmt_guide_range(50.0, 112.5, "bps") == "+50 to +112.5 bps"
    assert dm._fmt_guide_range(1.19, 1.25, "$/sh") == "$1.19–$1.25/sh"     # unchanged


# --- the citation guard --------------------------------------------------------------------------

def _mech(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"primary_source": {"releases": [{"source_ref": "8-K x EX-99.1",
                                             "reconciliation": rows}]}}


def _row(metric: str, period: str, value: float) -> dict[str, Any]:
    return {"metric": metric, "period": period, "value": value, "verbatim": "v",
            "source_ref": "8-K x EX-99.1"}


def _doc(prose: str) -> dict[str, Any]:
    return {"synthesis": {"bull_points": [prose]}}


def test_prose_citing_the_old_wrong_figure_refuses() -> None:
    """(+) A stored synthesis quoting VRRM's card as printed — "$38.0M" — refuses the refresh."""
    before = _mech([_row("adjusted ebitda", "2026", 38.0)])
    after = _mech([])
    assert rf.moved_cited_release_figures(before, after, _doc("adj EBITDA of $38.0M"))


@pytest.mark.parametrize("prose", [
    "adjusted EBITDA of $2.5 billion, up 35%",                # the TRUE figure, at its own scale
    "CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m)",  # FUBO's source_ref: months, not $M
])
def test_prose_not_citing_the_old_figure_does_not_refuse(prose: str) -> None:
    """(−) The fix must not be blocked by the truth it restores, nor by a bare "2m"."""
    before = _mech([_row("adjusted ebitda", "Q4 2025", 2.5)])
    after = _mech([_row("adjusted ebitda", "Q4 2025", 2500.0)])
    assert rf.moved_cited_release_figures(before, after, _doc(prose)) == []


def test_the_refresh_itself_refuses_a_page_citing_the_old_figure(tmp_path: Path) -> None:
    """THE WIRING, through `refresh_dossier` on a real page: VRRM's committed page with main's
    "$38.0M" row put back and its synthesis quoting it — a refresh that drops the row is refused,
    and the page on disk is untouched."""
    doc = json.loads(Path("data/dossiers/VRRM/dossier.json").read_text())
    rel = doc["mechanical"]["primary_source"]["releases"][0]
    rel["reconciliation"].append(_row("adjusted ebitda", "2026", 38.0))
    doc["synthesis"]["bull_points"] = [*doc["synthesis"]["bull_points"], "adj EBITDA of $38.0M"]
    page = tmp_path / "VRRM" / "dossier.json"
    page.parent.mkdir()
    page.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    (tmp_path / "VRRM" / "dossier.md").write_text("")
    text = page.read_text()

    def drop(mech: dict[str, Any]) -> dict[str, Any]:
        out = json.loads(json.dumps(mech))
        out["primary_source"]["releases"][0]["reconciliation"].pop()
        return out

    with pytest.raises(rf.RefreshRefusedError, match="release recon adjusted ebitda 2026"):
        rf.refresh_dossier(page, transform=drop)
    assert page.read_text() == text


def test_a_relabel_is_not_a_move() -> None:
    """(−) SMPL: its 34.3% Q4 margin, once filed as the year, is still on the page."""
    before = _mech([_row("gross margin", "2025", 34.3)])
    after = _mech([_row("gross margin", "Q4 2025", 34.3)])
    assert rf.moved_cited_release_figures(before, after, _doc("gross margin of 34.3%")) == []


# --- the transform, offline ----------------------------------------------------------------------

def _offline(monkeypatch: pytest.MonkeyPatch, texts: dict[str, list[str]]) -> None:
    """EDGAR served from `texts` (accession → exhibit texts), through the transform's own seams."""
    from types import SimpleNamespace

    import vinci.sec as sec

    monkeypatch.setattr(rp, "exhibit_991_urls",
                        lambda _h, _c, acc: [f"{acc}#{i}" for i in range(len(texts.get(acc, [])))])
    def get_text(url: str, ttl_seconds: Any = None) -> str:
        acc, i = url.split("#")
        return texts[acc][int(i)]
    monkeypatch.setattr(sec, "build_sec_http", lambda _cfg: SimpleNamespace(get_text=get_text))
    monkeypatch.setattr("vinci.graph.filings.html_to_text", lambda s: s)


def _vrrm_with_the_old_row() -> tuple[dict[str, Any], str]:
    """VRRM's committed mechanical layer with main's wrong row put back on its Q1 release."""
    mech = json.loads(Path("data/dossiers/VRRM/dossier.json").read_text())["mechanical"]
    rel = next(r for r in mech["primary_source"]["releases"]
               if "0001193125-26-209031" in r["source_ref"])
    rel["reconciliation"].append(_row("adjusted eps", "Q1 2026", 1.3))
    return mech, "0001193125-26-209031"


def test_the_transform_removes_the_wrong_row(monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) Re-read through the fixed parser, VRRM's Q1 release no longer carries the $1.30 the range
    made. Only this release is served; every other exhibit maps back unread-changed."""
    mech, acc = _vrrm_with_the_old_row()
    texts: dict[str, list[str]] = {}
    for r in mech["primary_source"]["releases"]:
        a = dm._acc_of(r["source_ref"])
        assert a is not None
        texts.setdefault(a, []).append(_VRRM_Q1_26 if a == acc else "Acme. No figures here.")
    _offline(monkeypatch, texts)
    monkeypatch.setattr(rf, "_rebuild_release_lines", lambda *a, **k: None)
    out = rf.release_figures_transform("VRRM", "x")(mech)
    rel = next(r for r in out["primary_source"]["releases"] if acc in r["source_ref"])
    assert not any(r["metric"] == "adjusted eps" and r["value"] == 1.3
                   for r in rel["reconciliation"])
    assert any(f.startswith(rp.RECON_REFUSAL_PREFIX) for f in rel["qa_flags"])


def test_an_exhibit_count_that_moved_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) A filing that now lists a different number of exhibits cannot be mapped back."""
    mech, acc = _vrrm_with_the_old_row()
    _offline(monkeypatch, {acc: []})
    with pytest.raises(rf.RefreshRefusedError, match="cannot map them back"):
        rf.release_figures_transform("VRRM", "x")(mech)


def test_a_line_that_does_not_reproduce_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) The triangulation is rebuilt only after it reproduces from the OLD rows: a stored line
    the inputs read now cannot rebuild is refused, never overwritten."""
    from types import SimpleNamespace

    import vinci.dossier.ciq as ciq_mod
    import vinci.dossier.manual_store as ms
    from vinci.dossier import ciq_sheets
    from vinci.dossier.schemas import ReleaseExtract, Sourced

    mech = json.loads(Path("data/dossiers/CNXC/dossier.json").read_text())["mechanical"]
    mech["primary_source"]["basis_triangulation"]["value"] = "not what the inputs build"
    monkeypatch.setattr(ms.LocalFolderStore, "from_config", staticmethod(
        lambda _c: SimpleNamespace(files=lambda _t: [])))
    monkeypatch.setattr(ciq_mod.CiqBundle, "from_files", staticmethod(lambda _t, _f: object()))
    monkeypatch.setattr(ciq_sheets, "comps_total_debt_ebitda_value",
                        lambda _b: Sourced[float].unknown(note="x"))
    monkeypatch.setattr(ciq_sheets, "net_debt", lambda _b: Sourced[float].unknown(note="x"))
    monkeypatch.setattr(ciq_sheets, "revenue_guide_lohi",
                        lambda _b, **_k: (None, None, None, None))
    rels = [ReleaseExtract.model_validate(r) for r in mech["primary_source"]["releases"]]
    with pytest.raises(rf.RefreshRefusedError, match="does not reproduce"):
        rf._rebuild_release_lines("CNXC", mech, rels, rels, None)


# --- the committed pages, end to end -------------------------------------------------------------

def test_no_committed_actual_is_an_unscaled_billion_e2e() -> None:
    """Every committed reconciliation row whose own words state billions holds ≥ $1,000M — on all
    27 pages. (Before the 2026-10-22 pass: UBER ×3, V ×6, FUBO ×3 held under 7.)"""
    bad = []
    for p in _PAGES:
        d = json.loads(p.read_text())
        for r in (d["mechanical"].get("primary_source") or {}).get("releases") or []:
            for rv in r.get("reconciliation") or []:
                says_bn = "billion" in rv["verbatim"].lower() or "B " in rv["verbatim"] + " "
                total = "eps" not in rv["metric"] and "margin" not in rv["metric"]
                if says_bn and total and abs(rv["value"]) < 1000:
                    bad.append((p.parent.name, rv["metric"], rv["period"], rv["value"]))
    assert not bad, bad


def _bps_segments() -> dict[str, list[str]]:
    """Per committed page: the card segment of every guide whose STORED unit is `bps`."""
    out: dict[str, list[str]] = {}
    for p in _PAGES:
        d = json.loads(p.read_text())
        rel_by_acc = {dm._acc_of(r["source_ref"]): r
                      for r in d["mechanical"]["primary_source"].get("releases") or []}
        for f in (d["mechanical"].get("drawdown_cause") or {}).get("filings") or []:
            rel, drv = rel_by_acc.get(f.get("accession")), (f.get("drivers") or {}).get("value")
            if not rel or not drv:
                continue
            for g in rel.get("guidance") or []:
                if g.get("unit") == "bps" and not g.get("qualitative"):
                    head = f"{g['period']} {g['metric']} outlook: "
                    out.setdefault(p.parent.name, []).extend(
                        seg for seg in drv.split("; ") if seg.startswith(head))
    return out


def test_a_bps_guide_prints_in_bps_on_every_card_md_and_web_e2e() -> None:
    """INVARIANT, every committed page (TEST-LAYER RULE: a living artifact gets a structural pin,
    never a value): each card segment for a guide whose stored unit is `bps` prints in basis
    points — never "$…M", the shape SMPL's card carried — and both renderers print that segment."""
    segs = _bps_segments()
    assert segs, "no committed card carries a bps guide — this pin checked nothing"
    for t, items in segs.items():
        md = Path(f"data/dossiers/{t}/dossier.md").read_text()
        for seg in items:
            assert seg.endswith(" bps") and "$" not in seg, (t, seg)
            assert seg in md, (t, seg)
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync, existsSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const want = {json.dumps(segs)};
const out = {{}};
for (const [t, items] of Object.entries(want)) {{
  const d = JSON.parse(readFileSync(`frontend/dossiers/${{t}}.json`));
  const cp = `frontend/scenarios/${{t}}.json`;
  const h = renderDossier(d, null, existsSync(cp) ? JSON.parse(readFileSync(cp)) : null);
  out[t] = items.filter((s) => !h.includes(s));
}}
console.log(JSON.stringify(out));
"""
    res = json.loads(subprocess.run(["node", "--input-type=module", "-e", driver],
                                    capture_output=True, text=True, check=True).stdout)
    assert all(not missing for missing in res.values()), res


def test_vrrms_card_never_shows_the_range_made_figures_md_and_web_e2e() -> None:
    """VRRM's card, both renderers: the strings the range-made actuals printed never return. An
    ABSENCE of the observed defect — a correct re-read can never produce it, so this cannot rot."""
    md = Path("data/dossiers/VRRM/dossier.md").read_text()
    bad = ("adj EBITDA 2026 $38.0M", "adj EPS 2026 $1.10", "adj EPS 2025 $1.30",
           "adj EPS Q1 2026 $1.30")
    assert not [b for b in bad if b in md]
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync, existsSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const d = JSON.parse(readFileSync("frontend/dossiers/VRRM.json"));
const cp = "frontend/scenarios/VRRM.json";
const h = renderDossier(d, null, existsSync(cp) ? JSON.parse(readFileSync(cp)) : null);
console.log(JSON.stringify({json.dumps(list(bad))}.filter((b) => h.includes(b))));
"""
    res = json.loads(subprocess.run(["node", "--input-type=module", "-e", driver],
                                    capture_output=True, text=True, check=True).stdout)
    assert res == [], res
