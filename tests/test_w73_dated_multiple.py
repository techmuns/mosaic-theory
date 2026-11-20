"""W73 (STATE §5.0 row 10; operator 2026-11-19: "Approve with corrections", the drift flag
"Proceed at 10%") — R1 prices a DATED close, judged by the EVENT RULE, never "today's".

The screen prices its band's latest close (W50's statistic, unchanged). Whether that close may be
priced is the EVENT RULE's verdict at the page's price date (`anchor.close_verdict`, read through
`freshness.first_event_after`, which #1132's `event_verdict` calls too): refused once the company
has filed a report the rule counts (10-Q, 10-K, 8-K item 2.02, a foreign or transition filer's)
on or after the close's day (W82; strictly after, for the ex-lease close) and on or before the
page's date; refused when the close is AFTER the page's date (W68), undated, or the filings were
not read. It replaces both of W62's clocks: the
30-day limit on CIQ's history and the ex-lease due date. A refusal withholds the VALUE, never the
recipe (W62's rule): `applicable`, the tag and the tier untouched, the dated multiple on show with
the median beside it, never priced in its place. Never re-struck at the page's close (the
2026-11-13 fence).

The scenario proposal (`propose.py`) takes R1's own dated close and the verdict R1's anchor
RECORDED, and refuses with its reason otherwise. `valuation_basis._r1_current` dates CIQ's
multiple by its own close and divides nothing across two dates (W65's finding B). A price-drift
FLAG (`anchor.close_drift`) states the stock's move since the close beside it, PRICE ÷ PRICE,
beyond 10%, in words ("has fallen 24.2%"), never a signed percentage and never a withholding.

Built from the REAL frozen pages (the cut at 4889ddba; VRRM's rebuilt page frozen 2026-11-18),
their committed companyfacts fixtures, the filers' real filings
(`tests/fixtures/event_rule_filings.json`), real EOD closes (`tests/fixtures/w73_eod_closes.json`)
and GOOGL's real 2026-11-19 Multiples sheet cut through the decode path
(`tests/fixtures/ciq_googl_multiples_2026_11_19.json`). A negative cut from a real page says so.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.anchor_reads import NO_BARS, NO_FILINGS, page_filings, rederived
from tests.frozen_support import CUT, frozen_doc
from tests.stale_gate_support import stale_gate_held_open
from vinci.dossier import anchor as anc
from vinci.dossier import freshness, propose
from vinci.dossier import render as dr
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.schemas import Dossier

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
FACTS = FIX / "companyfacts"
NOW = datetime(2026, 11, 19, tzinfo=UTC)
VRRM_1118 = FIX / "frozen_pages" / "2026-11-18" / "VRRM" / "dossier.json"
SIGNED_PCT = re.compile(r"[+-]\d+(\.\d+)?%")
#: GOOGL's verdict on the cut: its 2026-09-30 close predates Alphabet's Q3 results release.
GOOGL_NOTE = ("the company reported after the 2026-09-30 close (8-K item 2.02, filed "
              "2026-10-28); a CIQ export carrying a close after that filing, on or before the "
              "page's close, clears it")


def _copy(doc: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = copy.deepcopy(doc)
    return out


def _bars(t: str) -> list[tuple[date, float]]:
    raw = json.loads((FIX / "w73_eod_closes.json").read_text())["closes"][t]
    return [(date.fromisoformat(b["bar_date"]), float(b["close"])) for b in raw]


def _derive(doc: dict[str, Any], *, filings: Any = None, eod: Any = NO_BARS,
            **kw: Any) -> anc.Anchor:
    """The anchor `compute_anchor` writes on ``doc`` with its filer's REAL filings unless told
    otherwise (the event rule's pins never hold it open)."""
    facts = json.loads((FACTS / f"{doc['ticker']}.json").read_text())
    return anc.compute_anchor(doc["mechanical"], facts=facts, computed_at=NOW,
                              filings=page_filings(doc["ticker"]) if filings is None else filings,
                              eod_closes=eod, **kw)


def _refused(a: anc.Anchor) -> bool:
    return anc.DQ_STALE_MULTIPLE in (a.data_quality or "")


def _googl_priceable(doc: dict[str, Any] | None = None) -> tuple[dict[str, Any], Any]:
    """GOOGL's cut page and the CIQ read that supplies the D&A EDGAR lacks — the one the committed
    page records it read (28,540 $M over the twelve months to 2026-09-30, Financials_Annual sha
    482debf275), as the real `CiqFacts` type the bridge returns. R1 can then price GOOGL."""
    from vinci.dossier.ciq_balance import CiqFact, CiqFacts

    d = _copy(doc if doc is not None else frozen_doc("GOOGL"))
    da = frozen_doc("GOOGL")["anchor"]["d_and_a"]
    wb = ("Alphabet Inc NasdaqGS GOOGL Financials_Annual.xls", "482debf275")
    fact = CiqFact(value=da["value"], unit="$M", basis="depreciation and amortisation, LTM "
                   "(cash-flow statement)", source=da["source"], workbooks=(wb,), period="LTM",
                   period_end=date(2026, 9, 30))
    ciq = CiqFacts(ticker="GOOGL", as_of=None, source_file=wb[0], source_sha256=wb[1],
                   facts={"d_and_a": fact}, checks=[], failures=[])
    return d, ciq


def _googl_1119_band() -> list[dict[str, Any]]:
    """GOOGL's own-history bands from its REAL 2026-11-19 export's Multiples sheet (sha
    976c63d857), through the real decode path (`ciq_sheets.own_history_bands`)."""
    from vinci.dossier import ciq_sheets as cs

    raw = json.loads((FIX / "ciq_googl_multiples_2026_11_19.json").read_text())["names"]["GOOGL"]
    path = Path("/frozen/GOOGL-financials-quarterly.xls")
    sheets = {k.split("|")[2]: v for k, v in raw["sheets"].items()}
    b = CiqBundle(ticker="GOOGL", workbooks=(CiqWorkbook(kind="financials", path=path,
                                                         fmt=CiqFormat.BIFF_XLS,
                                                         freq="quarterly"),),
                  _cache={path: sheets})
    got = cs.own_history_bands(b)
    assert got.value, got.note
    return [x.model_dump(mode="json") for x in got.value]


def _md_screen(md: str) -> str:
    i = md.index("### Screening context")
    ends = [x for x in (md.find("\n## ", i), md.find("\n### ", i + 5)) if x > 0]
    return md[i:min(ends)] if ends else md[i:]


def _with_anchor(doc: dict[str, Any], a: anc.Anchor) -> dict[str, Any]:
    d = _copy(doc)
    d["anchor"] = json.loads(a.model_dump_json(exclude=anc.anchor_absent_fields(a) or None))
    return d


# --- (+/−) the event rule on the corpus -----------------------------------------------------------
def test_the_cut_refuses_exactly_googl_by_its_filings() -> None:
    """(+) Every page of the cut whose anchor reaches the multiple leg, derived with its filer's
    real filings: only GOOGL is refused — Alphabet's Q3 results (8-K item 2.02, 2026-10-28)
    postdate its 2026-09-30 close. (−) Every other one passes, BRBR (32 days, which W62's clock
    refused) and the ex-lease pages 56 to 79 days old among them. The counts are held: a sweep that
    measured nothing is suspect."""
    refused, passed = {}, []
    for folder in sorted(CUT.iterdir()):
        if not (folder / "dossier.json").is_file():
            continue
        a = _derive(frozen_doc(folder.name))
        if a.multiple is None:   # stopped before the multiple leg (NCNO: the R2 hint)
            continue
        if _refused(a):
            assert a.anchor_base_value_per_share is None and a.gap_split is None, folder.name
            refused[folder.name] = a.multiple.close_note
        else:
            assert a.multiple.close_stale is False, folder.name
            passed.append(folder.name)
    assert refused == {"GOOGL": GOOGL_NOTE}
    assert len(passed) == 20, passed   # 21 anchors reach the multiple leg at the cut
    assert {"BRBR", "TJX", "PARR", "ROST", "TGT", "BURL", "VRRM", "IT"} <= set(passed)


def test_googl_withholds_its_value_and_keeps_its_recipe() -> None:
    """(+) GOOGL, priceable once its CIQ read supplies the D&A: no screen value and no split; the
    22.9x close kept on show with its date and the median beside it; the flag, one detail line
    naming the filing, the reason and the "not priced" note. (−) `applicable` and the recipe stay:
    a refusal is not inapplicability. Held open, the same page prices — the rule alone withheld."""
    doc, ciq = _googl_priceable()
    a = _derive(doc, ciq=ciq)
    assert a.anchor_base_value_per_share is None and a.gap_split is None
    assert a.applicable is True and a.recipe_hint == anc.RECIPE_R1
    assert a.multiple is not None and a.multiple.as_of == "2026-09-30"
    assert a.multiple.value == pytest.approx(22.888839) and a.multiple.close_stale is True
    assert a.multiple.close_note == GOOGL_NOTE == a.value_withheld
    line = [x for x in a.data_quality_detail if x.startswith(anc.DQ_STALE_MULTIPLE)]
    assert len(line) == 1 and "8-K item 2.02 0001652044-26-000080 filed 2026-10-28" in line[0]
    why = a.reason or ""
    for part in ("valuation.own_history", "22.8888x at the 2026-09-30 close",
                 "refused by the event rule", "never priced in its place", "R1 still applies",
                 "a CIQ export carrying a close after that filing, on or before the page's close"):
        assert part in why, (part, why)
    with stale_gate_held_open():
        held = _derive(doc, ciq=ciq)
    assert held.anchor_base_value_per_share is not None and held.gap_split is not None
    for k in ("margin", "ltm_revenue", "d_and_a", "net_debt", "shares_outstanding"):
        assert getattr(a, k) == getattr(held, k), k


def test_brbr_prices_where_the_thirty_day_clock_refused() -> None:
    """(−) BRBR's CIQ close of 2026-09-21 is 32 days before its 2026-10-23 page, past W62's 30-day
    clock, and BellRing reported nothing between (its results came 2026-11-18): priced, no flag,
    the pass stated in its words."""
    a = _derive(frozen_doc("BRBR"))
    assert a.anchor_base_value_per_share is not None and not _refused(a)
    assert a.multiple is not None and a.multiple.close_stale is False
    assert a.multiple.close_note == "nothing reported after it by the page's close of 2026-10-23"
    assert a.value_withheld is None


def test_the_anchor_reads_the_export_gates_own_rule() -> None:
    """ONE RULE: on every cut page whose band is CIQ's history, the anchor's verdict names the same
    first filing #1132's `event_verdict` finds against a panel dated at the close. The EX-LEASE
    band takes the one strict reading of that rule, by ruling (W82; operator 2026-11-19, "Yes,
    option 1 + W84"): its close is CIQ's pricing date of the quarter's own report, so a filing ON
    the close does not outdate it — TJX's 10-Q of 2026-08-28 is the day of its ex-lease close, and
    the export gate's reading refuses it. Both kinds are walked: a sweep of one is suspect."""
    seen = {False: 0, True: 0}
    for folder in sorted(CUT.iterdir()):
        if not (folder / "dossier.json").is_file():
            continue
        mech = frozen_doc(folder.name)["mechanical"]
        sel = anc.r1_multiple_band(mech)
        band = sel.band
        if not isinstance(band, dict) or not band.get("as_of"):
            continue
        page = anc.price_as_of(mech)
        assert page is not None, folder.name
        filings = page_filings(folder.name)
        cv = anc.close_verdict(band["as_of"], page, filings, priced_at_its_report=sel.ex_lease)
        if sel.ex_lease:
            want = freshness.first_event_after(band["as_of"], filings, upto=page,
                                               same_day_counts=False)
            assert (cv.filing, cv.stale) == (want, want is not None), folder.name
        else:
            ev = freshness.event_verdict({"close": {"as_of": band["as_of"]}}, filings,
                                         built_at=page)
            assert (cv.filing, cv.stale) == ((ev.stale[0].filing, True) if ev.stale
                                             else (None, False)), folder.name
        seen[sel.ex_lease] += 1
    assert seen[False] >= 5 and seen[True] >= 14, seen
    tjx = page_filings("TJX")
    assert any(f.filing_date == "2026-08-28" and f.form == "10-Q" for f in tjx)
    assert anc.close_verdict("2026-08-28", date(2026, 11, 11), tjx,
                             priced_at_its_report=True).stale is False
    assert anc.close_verdict("2026-08-28", date(2026, 11, 11), tjx).stale is True


def test_tjx_is_refused_once_it_has_reported_where_the_cadence_passed_it() -> None:
    """(+) TJX's 2026-08-28 ex-lease close on a page priced 2026-11-19: TJX filed its Q3 results
    (8-K item 2.02) on 2026-11-18, so the close is refused — where W62's due date passed it until
    2026-12-29. (−) On its own 2026-11-11 page it passes: nothing was filed between."""
    d = _copy(frozen_doc("TJX"))
    d["mechanical"]["stock_info"]["as_of"] = "2026-11-19"
    late = _derive(d)
    assert late.anchor_base_value_per_share is None and _refused(late)
    assert late.multiple is not None and late.multiple.close_note == (
        "the company reported after the 2026-08-28 close (8-K item 2.02, filed 2026-11-18); a CIQ "
        "export carrying a close after that filing, on or before the page's close, clears it")
    on_time = _derive(frozen_doc("TJX"))
    assert on_time.anchor_base_value_per_share is not None and not _refused(on_time)


# --- (+/−) W68: a close after the page's date -----------------------------------------------------
def test_a_close_after_the_page_is_refused_on_googls_real_2026_11_19_export() -> None:
    """(+) W68, on GOOGL's REAL 2026-11-19 export (its Multiples sheet cut through the decode path):
    the band's latest close is a partial column at 2026-11-18, 17.577692x — AFTER the page's
    2026-11-11 close. Refused, never read as −7 days and fresh; a close after the page is one no
    holding-open makes knowable. (−) The same band on a page priced 2026-11-18 passes and prices."""
    bands = _googl_1119_band()
    eb = next(b for b in bands if "EBITDA" in b["metric"])
    assert (eb["as_of"], eb["current"]) == ("2026-11-18", pytest.approx(17.577692))
    doc, ciq = _googl_priceable()
    doc["mechanical"]["valuation"]["own_history"]["value"] = bands
    a = _derive(doc, ciq=ciq)
    assert a.anchor_base_value_per_share is None and _refused(a) and a.applicable is True
    assert a.value_withheld == (
        "the 2026-11-18 close is 7 days after the page's close of 2026-11-11, which could not know "
        "it; a page priced on or after that close clears it")
    with stale_gate_held_open():
        assert _derive(doc, ciq=ciq).anchor_base_value_per_share is None
    later = _copy(doc)
    later["mechanical"]["stock_info"]["as_of"] = "2026-11-18"
    priced = _derive(later, ciq=ciq)
    assert priced.anchor_base_value_per_share is not None and not _refused(priced)
    assert priced.multiple is not None and priced.multiple.as_of == "2026-11-18"


def test_an_unread_filing_list_or_an_undated_close_withholds() -> None:
    """(+) Filings that were not read, or a close with no date, cannot be judged: withheld, never
    priced as if fresh, each saying why. (−) A page with no stored close but a reference date is
    measured against that date."""
    unread = anc.compute_anchor(frozen_doc("LLY")["mechanical"], computed_at=NOW, filings=None,
                                filings_unread="EDGAR timed out", eod_closes=NO_BARS,
                                facts=json.loads((FACTS / "LLY.json").read_text()))
    assert unread.anchor_base_value_per_share is None and _refused(unread)
    assert "the event rule could not run — EDGAR timed out" in (unread.reason or "")
    d = _copy(frozen_doc("LLY"))
    anc.r1_multiple_band(d["mechanical"]).band.pop("as_of")   # type: ignore[union-attr]
    undated = _derive(d)
    assert undated.anchor_base_value_per_share is None and _refused(undated)
    d = _copy(frozen_doc("LLY"))
    day = date.fromisoformat(d["mechanical"]["stock_info"].pop("as_of"))
    assert _derive(d).anchor_base_value_per_share is None
    dated = _derive(d, reference_date=day)
    assert dated.anchor_base_value_per_share is not None and not _refused(dated)


# --- (+/−) the scenario proposal takes R1's dated close and its verdict ---------------------------
def test_the_proposal_takes_r1s_dated_close_and_its_recorded_verdict() -> None:
    """(+) TJX re-derived with its real filings: the base multiple is the 2026-08-28 close, dated in
    its label and vintage, the anchor's pass in its source. (−) GOOGL re-derived with its real
    filings: no base multiple, the refusal names the filing, the median never in its place."""
    tjx = rederived(frozen_doc("TJX"), filings=page_filings("TJX"))
    m = next(a for a in propose.propose_anchors(tjx) if a.axis == "multiple")
    assert m.schema_value == pytest.approx(16.3423) and m.vintage == "2026-08-28"
    assert m.label.endswith("multiple at the 2026-08-28 close")
    assert "nothing reported after it by the page's close of 2026-11-11" in m.source
    assert propose.multiple_base_refusal(tjx) is None
    googl = rederived(frozen_doc("GOOGL"), filings=page_filings("GOOGL"))
    assert not [a for a in propose.propose_anchors(googl) if a.axis == "multiple"]
    why = propose.multiple_base_refusal(googl) or ""
    assert "the 2026-09-30 close is refused by the event rule" in why and GOOGL_NOTE in why
    assert "never put in its place" in why
    assert propose.multiple_base_corroborator(googl) is None


def test_the_proposal_refuses_an_anchor_that_states_no_verdict_or_prices_another_close() -> None:
    """(−) The refusals besides the event rule's, each naming what clears it: VRRM's page frozen
    2026-11-18, whose anchor (W50 + W61) prices the close but states no verdict; the cut's TJX,
    whose anchor priced the median before W50; an anchor that prices no multiple (NCNO, R2); and an
    anchor that prices another close than the band now carries (a band refreshed after it)."""
    w50 = json.loads(VRRM_1118.read_text())
    assert w50["anchor"]["multiple"]["statistic"] == anc.MULTIPLE_CURRENT
    why = propose.multiple_base_refusal(w50) or ""
    assert "carries no event-rule verdict on the 2026-11-06 close" in why
    assert "re-derive the anchor (anchor-backfill)" in why
    pre_w50 = propose.multiple_base_refusal(frozen_doc("TJX")) or ""
    assert "does not price the 2026-08-28 close" in pre_w50 and "the median" in pre_w50
    ncno = rederived(frozen_doc("NCNO"))
    assert "prices no multiple" in (propose.multiple_base_refusal(ncno) or "")
    moved = rederived(frozen_doc("TJX"), filings=page_filings("TJX"))
    anc.r1_multiple_band(moved["mechanical"]).band["as_of"] = "2026-08-29"   # type: ignore[index]
    assert "does not price the 2026-08-29 close" in (propose.multiple_base_refusal(moved) or "")


# --- (+/−) the price-drift flag (correction 1; "Proceed at 10%") ----------------------------------
def test_vrrm_is_flagged_beside_its_multiple_and_its_value_stands() -> None:
    """(+) VRRM's rebuilt page: its 2026-11-06 close (EOD $2.19) against its 2026-11-17 close
    ($1.66), a 24.2% fall, beyond the 10% line: flagged in words beside the multiple, the value
    untouched (a flag, never a withholding), the structured block cap_cross_check's shape."""
    doc = json.loads(VRRM_1118.read_text())
    a = _derive(doc, eod=_bars("VRRM"))
    assert a.anchor_base_value_per_share is not None and not _refused(a)
    assert a.multiple is not None and a.multiple.close_drift is not None
    dr_ = a.multiple.close_drift
    assert (dr_.close_date, dr_.close_bar_date, dr_.close_eod, dr_.page_date) == (
        "2026-11-06", "2026-11-06", 2.19, "2026-11-17")
    assert dr_.move == pytest.approx(1.66 / 2.19 - 1, abs=1e-6) and dr_.beyond_tolerance
    assert dr_.tolerance == anc.DRIFT_FLAG_MOVE == 0.10 and not dr_.corporate_action
    assert a.multiple.close_drift_note == "⚠ the stock has fallen 24.2% since that close"
    with_flag = a
    held = _derive(doc, eod=NO_BARS)
    assert with_flag.anchor_base_value_per_share == held.anchor_base_value_per_share
    blk = _md_screen(dr.render_markdown(Dossier.model_validate(_with_anchor(doc, a))))
    assert ("close of 2026-11-06 · nothing reported after it by the page's close of 2026-11-17 · "
            "⚠ the stock has fallen 24.2% since that close · median") in blk
    assert not SIGNED_PCT.search(blk)


def test_a_small_move_or_a_same_date_close_is_not_flagged() -> None:
    """(−) TJX: the oldest active close (2026-08-28, 75 days) moved +1.0% to its page (EOD $135.12
    → $136.44): measured, not flagged, no note. IT: its multiple's close IS its page's close, so
    the move is 0 with no bar read at all."""
    tjx = _derive(frozen_doc("TJX"), eod=_bars("TJX"))
    assert tjx.multiple is not None and tjx.multiple.close_drift is not None
    assert tjx.multiple.close_drift.move == pytest.approx(136.44 / 135.12 - 1, abs=1e-6)
    assert not tjx.multiple.close_drift.beyond_tolerance and tjx.multiple.close_drift_note is None
    it = _derive(frozen_doc("IT"), eod=NO_BARS)
    assert it.multiple is not None and it.multiple.close_drift is not None
    assert it.multiple.close_drift.move == 0 and it.multiple.close_drift_note is None
    assert it.multiple.close_drift.source_ref == "the page's own close (stock_info.price)"


def test_a_share_basis_change_or_a_missing_bar_states_no_move() -> None:
    """(−) Cut from real bars: TJX's close halved (a 2-for-1 split between it and the page, at a
    whole-number ratio to the page's close) states a share-basis change and no move; VRRM with no
    bar within the store's 4-day lag of its close, or no store read at all, states "not measured"
    — never "no move"."""
    doc = json.loads(VRRM_1118.read_text())
    split = _derive(frozen_doc("TJX"), eod=[(d, c / 2) for d, c in _bars("TJX")])
    assert split.multiple is not None and split.multiple.close_drift is not None
    assert split.multiple.close_drift.corporate_action
    assert not split.multiple.close_drift.beyond_tolerance
    assert "share-basis change, so no move is stated" in (split.multiple.close_drift_note or "")
    gap = _derive(doc, eod=[(d, c) for d, c in _bars("VRRM") if d <= date(2026, 11, 1)])
    assert gap.multiple is not None and gap.multiple.close_drift is None
    assert gap.multiple.close_drift_note == (
        "the stock's move since that close is not measured: the EOD store has no close on or "
        "within 4 days before 2026-11-06")
    facts = json.loads((FACTS / "VRRM.json").read_text())
    none = anc.compute_anchor(doc["mechanical"], facts=facts, computed_at=NOW,
                              filings=NO_FILINGS, eod_closes=None)
    assert none.multiple is not None and "no EOD closes were passed" in (
        none.multiple.close_drift_note or "")


def test_the_flag_reads_the_page_and_one_bar_never_the_anchor() -> None:
    """FENCE (2026-11-13, "anchor ÷ price stays unprinted"): moving the anchor's own value — its
    margin — moves no drift figure, and the note carries no signed percentage."""
    doc = json.loads(VRRM_1118.read_text())
    a = _derive(doc, eod=_bars("VRRM"))
    moved = _copy(doc)
    moved["mechanical"]["valuation"]["own_history"]["value"][0]["median"] *= 2
    b = _derive(moved, eod=_bars("VRRM"))
    assert a.multiple is not None and b.multiple is not None
    assert a.multiple.close_drift == b.multiple.close_drift
    assert not SIGNED_PCT.search(a.multiple.close_drift_note or "")


# --- (+/−) valuation_basis._r1_current (W65's deferred finding B) ---------------------------------
def test_r1_current_dates_its_multiple_by_its_own_close_and_divides_nothing_across_dates() -> None:
    """(+) FAILS ON MAIN 2ecf6da0. IT's page with its comps TEV dated 2026-12-31 and W65's basis
    reading `dates_differ`: the multiple carries its OWN close (2026-11-11), its source never calls
    the pairing measured, and no value is re-stated at the page's price through a TEV of the wrong
    date — the basis field says why. Main labelled it 2026-12-31, printed "its pairing, measured:
    dates_differ" and returned 9.400001. (−) IT as committed (one date): its value and every string
    as before. LLY: its 2026-11-02 close, where the comps TEV is 2026-10-30 (3 days, within W65's
    4), so its value stands."""
    from vinci.dossier import valuation_basis as vb

    page = frozen_doc("IT")   # the cut: its comps TEV and its multiple are both of 2026-11-11
    moved = _copy(page)
    moved["mechanical"]["valuation"]["implied_expectations"]["tev_as_of"] = "2026-12-31"
    moved["mechanical"]["valuation"]["ev_ebitda_basis"]["reading"] = "dates_differ"
    got = vb._r1_current(moved, False)
    assert got is not None and got["as_of"] == "2026-11-11"
    assert "its pairing, measured: dates_differ" not in got["source"]
    assert "its pairing not measured: dates_differ" in got["source"]
    assert "value_at_page_price" not in got
    assert got["value_at_page_price_basis"].startswith(
        "not re-stated at the page's price: the snapshot TEV is dated 2026-12-31 and the "
        "multiple's close 2026-11-11, 50 days apart")
    same = vb._r1_current(page, False)
    assert same is not None and same["value_at_page_price"] == pytest.approx(9.400001)
    assert same["as_of"] == "2026-11-11" and same["source"].endswith("measured: indistinguishable")
    lly = vb._r1_current(frozen_doc("LLY"), False)
    assert lly is not None and lly["as_of"] == "2026-11-02" and "value_at_page_price" in lly


# --- (+/−) labels: no surface calls an old close "today's" ----------------------------------------
def test_no_derived_line_or_renderer_label_calls_the_close_todays() -> None:
    """(+) Every string the anchor writes on a priced, a refused and a flagged page, and the
    renderers' own R1 labels, name the close by its date; none says "today's". (−) The W61 line
    names the close: "at 16.3x (the 2026-08-28 close)"."""
    doc, ciq = _googl_priceable()
    pages = [_derive(frozen_doc("TJX")), _derive(doc, ciq=ciq),
             _derive(json.loads(VRRM_1118.read_text()), eod=_bars("VRRM"))]
    for a in pages:
        text = json.dumps(json.loads(a.model_dump_json()))
        assert "today's" not in text and "Today's" not in text, a.multiple
    assert pages[0].gap_split is not None
    assert "at 16.3x (the 2026-08-28 close) = " in pages[0].gap_split.read
    for label in (dr._SCREEN_METHOD_R1_DATED, dr._SCREEN_SUBTITLE_DATED):
        assert "today" not in label
    js = (ROOT / "frontend" / "views" / "shared" / "dossier.js").read_text()
    assert "Multiple at the latest close, own history" in js
    # the RENDERED block of a page whose anchor W73 derived says "today" nowhere; a page derived
    # before keeps W50's words until it is re-derived, as one derived before W50 keeps the median's
    for a, doc in ((pages[0], frozen_doc("TJX")), (pages[2], json.loads(VRRM_1118.read_text()))):
        blk = _md_screen(dr.render_markdown(Dossier.model_validate(_with_anchor(doc, a))))
        assert "today" not in blk.lower(), blk
        assert dr._SCREEN_METHOD_R1_DATED in blk and dr._SCREEN_SUBTITLE_DATED in blk
    # (−) VRRM's page frozen 2026-11-18: its anchor (W50 + W61) records no W73 verdict
    old = _md_screen(dr.render_markdown(Dossier.model_validate(json.loads(VRRM_1118.read_text()))))
    assert dr._SCREEN_METHOD_R1_CURRENT in old and "Current multiple, own history" in old


def test_the_web_prints_the_dated_multiple_and_its_flag_collapsed_and_open(tmp_path: Path) -> None:
    """(+) END TO END on `renderDossier`: VRRM's row reads the dated close, the pass and the flag;
    GOOGL's "not priced" row names its filing. The block holds no <details>, so collapsed and
    force-open are one. (−) VRRM's page frozen 2026-11-18, whose anchor (W50 + W61) records no
    W73 verdict, keeps W50's words until it is re-derived, as the markdown does."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    vrrm = json.loads(VRRM_1118.read_text())
    googl, ciq = _googl_priceable()
    pages = {"VRRM": _with_anchor(vrrm, _derive(vrrm, eod=_bars("VRRM"))),
             "GOOGL": _with_anchor(googl, _derive(googl, ciq=ciq)),
             "OLD": json.loads(VRRM_1118.read_text())}
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const dj = pathToFileURL(path.resolve("frontend/views/shared/dossier.js")).href;
const { renderDossier } = await import(dj);
const pages = JSON.parse(readFileSync(process.argv[2], "utf8"));
const out = {};
for (const [k, doc] of Object.entries(pages)) out[k] = renderDossier(doc, null);
process.stdout.write(JSON.stringify(out));
"""
    # tmp_path, never a fixed folder in the checkout (2026-11-20); node still runs from ROOT
    (tmp_path / "drv.mjs").write_text(driver)
    (tmp_path / "pages.json").write_text(json.dumps(pages))
    res = subprocess.run(["node", str(tmp_path / "drv.mjs"), str(tmp_path / "pages.json")],
                         cwd=ROOT, capture_output=True, text=True, check=True)
    out: dict[str, str] = json.loads(res.stdout)

    def block(h: str) -> str:
        i = h.index('<div class="uw-screen">')
        depth = 0
        for m in re.finditer(r"<div\b|</div>", h[i:]):
            depth += 1 if m.group(0) == "<div" else -1
            if depth == 0:
                return h[i:i + m.end()]
        raise AssertionError("unclosed screening block")

    v, g, old = block(out["VRRM"]), block(out["GOOGL"]), block(out["OLD"])
    assert "Current multiple, own history" in old and "today&#39;s multiple" in old
    assert "Multiple at the latest close" not in old
    assert "Multiple at the latest close, own history" in v
    assert ("close of 2026-11-06 · nothing reported after it by the page&#39;s close of "
            "2026-11-17 · ⚠ the stock has fallen 24.2% since that close") in v
    assert ">not priced<" in g and "8-K item 2.02, filed 2026-10-28" in g
    for b in (v, g):
        row = re.search(r"Multiple at the latest close, own history.*?</tr>", b, re.S)
        assert row is not None and "<details" not in row.group(0)
        assert not SIGNED_PCT.search(re.sub(r"<[^>]+>", " ", b))


# --- (+) assembly reads the store while it is open (found by the impact run, 2026-11-19) -----
def test_assembly_reads_every_store_call_inside_its_with_block() -> None:
    """REGRESSION (W73, caught by `vinci.impact run` on this PR's first head): `assemble_one` read
    the anchor's EOD closes with `store.get_price_history` AFTER its `with Store(...)` block had
    closed the store, so every $0 build raised `sqlite3.ProgrammingError` inside the anchor and fell
    back to "anchor computation failed" — 25 of 25 pages lost their anchor. Every reference to
    `store` in `assemble_one` must sit lexically inside the `with Store(...) as store:` block that
    opens it: a call on it AND the name handed on, since a helper given the closed store after the
    block reads it just the same (B's review of #1144: a `_eod_closes(store, id)` read after the
    block passed the first cut of this pin, which saw only `store.<call>`, and all 671 tests of
    B's mutation set)."""
    import ast
    import inspect
    import textwrap

    from vinci.dossier import assemble

    tree = ast.parse(textwrap.dedent(inspect.getsource(assemble.assemble_one)))
    blocks = [n for n in ast.walk(tree) if isinstance(n, ast.With) and any(
        isinstance(i.optional_vars, ast.Name) and i.optional_vars.id == "store" for i in n.items)]
    assert len(blocks) == 1, "assemble_one opens its store in one with-block"
    inside = {id(n) for n in ast.walk(blocks[0])}
    uses = [n for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "store"]
    read = any(isinstance(p, ast.Attribute) and p.value is n for p in ast.walk(tree) for n in uses)
    assert read, "the scan found no store read: it checks nothing"
    outside = [n.lineno for n in uses if id(n) not in inside]
    assert not outside, f"the store is used after its with-block closed (source lines {outside})"


def test_a_zero_dollar_build_of_it_computes_its_anchor_end_to_end(tmp_path: Path) -> None:
    """END TO END (TEST-LAYER RULE; coordinator B, 2026-11-19): the closed-store defect was OBSERVED
    in built pages — the impact run's $0 builds wrote "anchor computation failed: ProgrammingError"
    on 25 of 25 — so it is pinned on a real build: IT, a committed active page, through
    `prespend.mechanical_build` in the impact check's own child (`vinci/impact/child.py`), from the
    committed data at HEAD, the licensed CIQ export and SEC cache in place, a COPY of the price
    store, the cache frozen and every socket refused. The anchor must be COMPUTED: never the
    fallback, R1's inputs and multiple present, and the W73 verdict recorded on its close.

    LOCAL ONLY: it needs the CIQ export, the SEC cache and a store, none of them committed, so it
    skips where they are absent (CI), as the suite's other licensed-input pins do."""
    from vinci.impact import run as rn

    primary = rn.primary_checkout(ROOT)
    ciq, cache, db = (primary / "data" / "manual" / "ciq", primary / "data" / "cache",
                      primary / "data" / "vinci.db")
    env_file = primary / ".env"   # vendor keys the build reads at start; every socket is refused
    if not ((ciq / "IT").is_dir() and cache.is_dir() and db.is_file() and env_file.is_file()):
        pytest.skip("no licensed CIQ export, SEC cache, price store or .env on this machine")
    box = tmp_path / "inputs"
    rn._extract(ROOT, "HEAD", ["data", "scenarios", "frontend"], box)
    store = tmp_path / "impact-store" / "data" / "vinci.db"   # the layout `Store` stamps from
    rn.snapshot_store(db, store)
    (box / "data" / "manual").mkdir(parents=True, exist_ok=True)
    for link, target in ((box / "data" / "manual" / "ciq", ciq), (box / "data" / "cache", cache),
                         (box / "data" / "vinci.db", store)):
        link.symlink_to(target.resolve())
    out = tmp_path / "out"
    code = Path(anc.__file__).resolve().parents[2]   # the checkout whose vinci is under test
    done = subprocess.run(
        [rn.sys.executable, "-P", str(rn.CHILD), "--tickers", "IT", "--out", str(out),
         "--expect-root", str(code / "vinci"), "--capture-child", str(rn.CAPTURE_CHILD),
         "--frozen-cache", "--no-network", "--no-requests", "--no-committed"],
        cwd=box, env=rn.child_env(code, env_file), capture_output=True, text=True, timeout=900)
    built_path = out / "IT" / "built.json"
    assert built_path.exists(), (done.returncode, (out / "IT" / "build.error.json").read_text()
                                 if (out / "IT" / "build.error.json").exists()
                                 else done.stdout[-2000:] + done.stderr[-2000:])
    page = json.loads(built_path.read_text())
    a = page["anchor"]
    notes = json.dumps([a.get("reason"), page.get("caveats"), page.get("qa_flags")])
    assert "anchor computation failed" not in notes, notes[:600]
    assert a["recipe_hint"] == anc.RECIPE_R1, a.get("recipe_hint")
    for k in ("margin", "ltm_revenue", "net_debt", "multiple"):
        assert a.get(k), (k, a.get(k))
    assert a["multiple"]["statistic"] == anc.MULTIPLE_CURRENT
    assert a["multiple"].get("close_note"), a["multiple"]   # the event rule judged the close


# --- an SEC refusal stops the run (B's review of #1144, finding A) -----------------------------

def _refused_by_sec(monkeypatch: pytest.MonkeyPatch) -> Any:
    """SEC's refusal as `netcache` raises it: the process stopped first (`_SEC_STOPPED`), then the
    error. Every later SEC request in the process is refused unsent (`netcache._pace`)."""
    from vinci import netcache

    refusal = netcache.SecRateLimitedError(
        "SEC refused https://data.sec.gov/submissions/CIK0001652044.json with 429 (test)")

    def refuse(*_a: Any, **_k: Any) -> Any:
        monkeypatch.setattr(netcache, "_SEC_STOPPED", refusal)
        raise refusal
    return refuse


def test_the_event_rules_reader_lets_an_sec_refusal_through_and_states_any_other_miss(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ `read_filing_events` caught every exception, an SEC refusal included, and returned it as
    the list's reason: the anchor then WITHHELD a value because SEC throttled the run, and the
    export gate refused as "could not run". A refusal stops the run (`netcache`: not an
    `HttpError`, on purpose). ⊕ Any other miss is still the reason, never a pass
    (`test_event_rule`'s feed-down pin)."""
    from types import SimpleNamespace

    from vinci.dossier.mechanical import read_filing_events
    from vinci.netcache import HttpError, SecRateLimitedError

    mech = frozen_doc("GOOGL")["mechanical"]
    refused = SimpleNamespace(recent_filings=_refused_by_sec(monkeypatch))
    with pytest.raises(SecRateLimitedError, match="429"):
        read_filing_events(refused, "0001652044", mech, date(2026, 11, 19),  # type: ignore[arg-type]
                           since=date(2026, 9, 30))

    def down(*_a: Any, **_k: Any) -> Any:
        raise HttpError("submissions feed: 503 after retries (test)")
    filings, unread = read_filing_events(SimpleNamespace(recent_filings=down),  # type: ignore[arg-type]
                                         "0001652044", mech, date(2026, 11, 19),
                                         since=date(2026, 9, 30))
    assert filings is None and unread is not None and "HttpError" in unread


def test_an_sec_refusal_stops_anchor_backfill_before_it_writes_a_page(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ THE COMMAND (`anchor-backfill`) on a copy of GOOGL's frozen page, EDGAR's companyfacts its
    committed fixture and its submissions read refused by SEC: before the fix it returned 0 and
    REWROTE the page, R1's value withheld because "the event rule could not read the company's
    filings (… SecRateLimitedError …)". The backfill has no `_refuse_after_sec_refusal` before its
    write, so every name after the refusal would be written the same way. Now the refusal stops
    the run and the page is byte-identical."""
    import argparse
    from types import SimpleNamespace

    from vinci import cli
    from vinci.edgar.client import EdgarClient
    from vinci.netcache import SecRateLimitedError
    from vinci.resolver import EntityResolver

    facts = json.loads((FIX / "anchor_ciq_bridge.json").read_text())["names"]["GOOGL"][
        "companyfacts"]
    folder = tmp_path / "dossiers" / "GOOGL"
    folder.mkdir(parents=True)
    shutil.copy(CUT / "GOOGL" / "dossier.json", folder / "dossier.json")
    before = (folder / "dossier.json").read_bytes()
    edgar = SimpleNamespace(companyfacts=lambda _cik: facts,
                            recent_filings=_refused_by_sec(monkeypatch))
    monkeypatch.setattr(cli, "get_config",
                        lambda: SimpleNamespace(data_dir=tmp_path, db_path=tmp_path / "vinci.db"))
    monkeypatch.setattr(EntityResolver, "from_config", classmethod(
        lambda cls, cfg: SimpleNamespace(resolve_ticker=lambda _t: SimpleNamespace(
            cik="0001652044", internal_id="googl"))))
    monkeypatch.setattr(EdgarClient, "from_config", classmethod(lambda cls, cfg: edgar))
    with pytest.raises(SecRateLimitedError, match="429"):
        cli._cmd_anchor_backfill(argparse.Namespace(tickers="GOOGL", dry_run=False))
    assert (folder / "dossier.json").read_bytes() == before
    assert not (folder / "dossier.md").exists()


def test_the_precheck_reports_an_sec_refusal_at_the_export_gate_as_a_stop(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """#1132'S CIQ-EXPORT GATE reads the same list. In the $0 precheck (`prespend.run`), SEC
    refusing its post-spend read was a `_freshness_check` refusal that "could not run"; it is now
    the refusal itself, said as the check's stop line, exit 1, as a refusal inside the $0 build is
    (never a traceback). In the paid build the gate's read (`assemble_one`) sits outside any
    handler, so the refusal leaves `assemble_one` and `assemble_cohort` stops the cohort on it,
    where a `FreshnessError` was one failed name. The page is not written either way
    (`_refuse_after_sec_refusal`)."""
    from types import SimpleNamespace

    from vinci.config import Config
    from vinci.dossier import prespend
    from vinci.edgar.client import EdgarClient

    folder = tmp_path / "dossiers" / "GOOGL"
    folder.mkdir(parents=True)
    shutil.copy(CUT / "GOOGL" / "dossier.json", folder / "dossier.json")
    built = Dossier.model_validate_json((folder / "dossier.json").read_text())
    monkeypatch.setattr(prespend, "mechanical_build", lambda t, cfg: built)
    monkeypatch.setattr(prespend, "forecast_llm_fields", lambda d, http: {})
    monkeypatch.setattr(EdgarClient, "from_config", classmethod(
        lambda cls, cfg=None: SimpleNamespace(recent_filings=_refused_by_sec(monkeypatch))))
    out: list[str] = []
    assert prespend.run("GOOGL", Config(data_dir=tmp_path), emit=out.append) == 1
    stop = "=== pre-spend check · GOOGL: SEC REFUSED the export gate's read"
    assert out[-1].startswith(stop), out
    assert "SecRateLimitedError" in out[-1] and "429" in out[-1]
