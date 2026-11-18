"""W61 — the R1 screening anchor split into a MARGIN effect and a MULTIPLE effect (`anchor_split`).

The anchor prices today's multiple (W50) on a mid-cycle EBITDA, so one level hides which of the two
did the work. The split states the anchor as V0 — the value today's multiple puts on the EBITDA it
is STRUCK ON — plus a margin effect, with the multiple effect beside it, never in it.

Every value pin reads the frozen cut at main 4889ddba (`frozen_support.frozen_doc`), whose 26
anchors all predate W50 and price the MEDIAN, so each is pinned to rebuild the committed median
anchor exactly: V0 + margin effect + multiple effect. The negatives are cut from those real pages,
each saying what it changed. One end-to-end pin runs `compute_anchor` on a real page and its
committed companyfacts fixture, since a pin on the helper alone stays green when the call site goes.

Positive: the split rebuilds every committed screen value on the cut (18 pages); E_cur is the
multiple's own denominator on its own lease basis (LLY's reported LTM EBITDA, WERN's ex-lease
observation); leverage is FLAGGED past half the EV (VRRM, BRBR) and not below it (IT, WERN); a
close past 30 days is stale (TJX), a nearer one is not (LLY). Negative: a denominator the page
cannot identify is REFUSED, never substituted (GOOGL, and LLY under three cut-from-real mutations);
no term reads the page's price; a split that does not rebuild the published value raises; an
anchor written before W61 serialises with no `gap_split` key.
"""
from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.frozen_support import CUT, frozen_doc
from vinci.dossier import anchor as anc
from vinci.dossier import anchor_split as sp

ROOT = Path(__file__).resolve().parents[1]
FACTS = ROOT / "tests" / "fixtures" / "companyfacts"
NOW = datetime(2026, 11, 18, tzinfo=UTC)

#: The cut's pages that carry a screen value and split (measured on the cut, 2026-11-18).
SPLIT_ON_CUT = ("AMZN", "BRBR", "BURL", "CNXC", "EPAM", "IT", "LLY", "MCK", "NFLX", "NKE", "PARR",
                "ROST", "SMPL", "TGT", "TJX", "VRRM", "WERN", "WLK")


def _split(doc: dict[str, Any]) -> sp.AnchorGapSplit:
    s = anc.committed_gap_split(doc)
    assert s is not None, f"{doc['ticker']}: no split"
    return s


def _copy(doc: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = json.loads(json.dumps(doc))
    return out


def test_the_split_rebuilds_every_committed_screen_value_on_the_cut() -> None:
    """Both identities, on every cut page with a screen value: V0 + margin = the anchor at today's
    multiple, and + the multiple effect = the anchor at the median, which is the committed value
    (every anchor on the cut predates W50). GOOGL alone is refused; the rest carry no value."""
    split, refused, none = [], [], []
    for folder in sorted(p for p in CUT.iterdir() if (p / "dossier.json").is_file()):
        doc = frozen_doc(folder.name)
        s = anc.committed_gap_split(doc)
        if s is None:
            assert doc["anchor"].get("anchor_base_value_per_share") is None, folder.name
            none.append(folder.name)
            continue
        base = doc["anchor"]["anchor_base_value_per_share"]
        assert abs(s.anchor_at_median - base) <= sp.REPRODUCE_TOL, (folder.name, s, base)
        if s.refusal:
            refused.append(folder.name)
            continue
        split.append(folder.name)
        assert s.value_at_current_ebitda is not None and s.margin_effect is not None
        assert abs(s.value_at_current_ebitda + s.margin_effect - s.anchor_at_current) < 1e-3
        assert abs(s.anchor_at_current + s.multiple_effect - s.anchor_at_median) < 1e-3
    assert tuple(split) == SPLIT_ON_CUT
    assert refused == ["GOOGL"]
    assert len(none) == 7, none


def test_lly_reads_its_reported_ltm_ebitda_and_a_large_negative_margin_effect() -> None:
    """LLY's margins rose: its mid-cycle EBITDA is 0.60x the EBITDA CIQ's 27.9x is struck on, so
    reverting the margin takes $577.74 off a $1,397.90 value at current EBITDA. The multiple effect
    (median 25.7x under today's) is beside it, −$67.92."""
    s = _split(frozen_doc("LLY"))
    assert s.current_ebitda == 46489.0
    assert "indistinguishable" in (s.current_ebitda_source or "")
    assert s.current_multiple == pytest.approx(27.85306)
    assert s.median_multiple == pytest.approx(25.682746)
    assert s.value_at_current_ebitda == pytest.approx(1397.8967, abs=1e-4)
    assert s.margin_effect == pytest.approx(-577.7445, abs=1e-4)
    assert s.multiple_effect == pytest.approx(-67.9166, abs=1e-4)
    assert s.anchor_at_current == pytest.approx(820.1522, abs=1e-4)
    assert s.anchor_at_median == pytest.approx(752.2356, abs=1e-4)
    assert s.leverage_flag is False and s.net_debt_to_ev == pytest.approx(0.03551, abs=1e-5)
    assert (s.multiple_close, s.price_date, s.close_age_days, s.stale_close) == (
        "2026-11-02", "2026-11-11", 9, False)


def test_wern_reads_the_ex_lease_observation_the_current_is_struck_on() -> None:
    """On the ex-lease basis E_cur is the observation whose multiple IS the band's current: WERN's
    2026-11-09 close, $360M over four quarters to 2026-09-30. Mid-cycle EBITDA is above it (a
    trough), so the margin effect is positive."""
    doc = frozen_doc("WERN")
    s = _split(doc)
    obs = [o for o in doc["mechanical"]["valuation"]["lease_basis"]["observations"]
           if o.get("multiple") == s.current_multiple]
    assert len(obs) == 1 and s.current_ebitda == obs[0]["ltm_ebitda"]
    assert (s.multiple_close, s.current_ebitda_through) == ("2026-11-09", "2026-09-30")
    assert s.value_at_current_ebitda == pytest.approx(27.8951, abs=1e-4)
    assert s.margin_effect is not None and s.margin_effect == pytest.approx(12.0394, abs=1e-4)
    assert s.margin_effect > 0 and s.leverage_flag is False


@pytest.mark.parametrize(("ticker", "ratio", "flagged"), [
    ("VRRM", 0.766052, True), ("BRBR", 0.524119, True), ("IT", 0.125451, False),
    ("WERN", 0.325707, False)])
def test_leverage_is_flagged_past_half_the_ev_and_never_refused(
        ticker: str, ratio: float, flagged: bool) -> None:
    """Net debt over the EV today's multiple puts on current EBITDA; past 0.5 a FLAG, and the
    split still stands. VRRM's 4.27x: each 1% of EV moves its value per share 4.27%."""
    s = _split(frozen_doc(ticker))
    assert s.net_debt_to_ev == pytest.approx(ratio, abs=1e-6)
    assert s.leverage_flag is flagged
    assert s.refusal is None and s.value_at_current_ebitda is not None
    if ticker == "VRRM":
        assert s.equity_sensitivity == pytest.approx(4.2745, abs=1e-4)


def test_net_debt_beyond_the_ev_flags_and_states_no_sensitivity() -> None:
    """VRRM's real inputs with its net debt raised past the EV its current multiple implies (a cut
    from the real page): V0 turns negative, the flag holds, the sensitivity is undefined (None)."""
    doc = frozen_doc("VRRM")
    a = doc["anchor"]
    ev0 = _split(doc).current_multiple * 346.364
    s = sp.gap_split(doc["mechanical"], ex_lease=False, current=3.556605, median=13.8658905,
                     close="2026-11-06", revenue=a["ltm_revenue"]["value"],
                     margin=a["margin"]["value"], d_and_a=a["d_and_a"]["value"],
                     net_debt=ev0 * 1.1, shares=anc.per_share_shares(a) or 0.0,
                     price_date=date(2026, 11, 6))
    assert s.value_at_current_ebitda is not None and s.value_at_current_ebitda < 0
    assert s.leverage_flag is True and s.equity_sensitivity is None


def test_a_close_past_thirty_days_is_stale() -> None:
    """TJX's ex-lease current is the 2026-08-28 quarterly close, 75 days before its 2026-11-11
    price date: stale, and V0 is that day's value. LLY's 9 days are not."""
    s = _split(frozen_doc("TJX"))
    assert (s.multiple_close, s.price_date, s.close_age_days, s.stale_close) == (
        "2026-08-28", "2026-11-11", 75, True)
    assert sp.STALE_CLOSE_DAYS == 30
    assert _split(frozen_doc("LLY")).stale_close is False


def test_googl_is_refused_never_substituted() -> None:
    """CIQ's 22.9x divides GOOGL's TEV by $144.8bn, neither its reported LTM EBITDA ($185.5bn) nor
    that plus rent, so the EBITDA it is struck on is not identified: no V0 and no margin effect,
    and reported EBITDA is NOT put in its place. The multiple effect, which reads none, stands."""
    s = _split(frozen_doc("GOOGL"))
    assert s.refusal and "not_reproduced" in s.refusal
    assert (s.current_ebitda, s.value_at_current_ebitda, s.margin_effect, s.net_debt_to_ev,
            s.leverage_flag) == (None, None, None, None, None)
    assert s.multiple_effect == pytest.approx(-67.3569, abs=1e-4)
    assert s.anchor_at_median == pytest.approx(225.539, abs=1e-3)


@pytest.mark.parametrize("cut", ["ebitda_plus_rent", "not_reproduced", "other_multiple", "absent"])
def test_a_ciq_denominator_the_page_does_not_measure_is_refused(cut: str) -> None:
    """LLY with its `ev_ebitda_basis` cut (it reads indistinguishable on the real page): a multiple
    struck on EBITDA plus rent, one that reproduces neither, a basis measured on another multiple,
    or no basis at all — each refused, the split's anchor unchanged."""
    doc = _copy(frozen_doc("LLY"))
    eb = doc["mechanical"]["valuation"]["ev_ebitda_basis"]
    if cut == "absent":
        del doc["mechanical"]["valuation"]["ev_ebitda_basis"]
    elif cut == "other_multiple":
        eb["multiple"] = 30.0
    else:
        eb["reading"] = cut
    s = _split(doc)
    assert s.refusal is not None and s.value_at_current_ebitda is None
    assert s.anchor_at_median == pytest.approx(752.2356, abs=1e-4)


def test_an_ex_lease_current_no_observation_carries_is_refused() -> None:
    """WERN with its band's current moved off every observation (a cut from the real page): the
    split names that no observation carries it, never reading another quarter's EBITDA."""
    doc = _copy(frozen_doc("WERN"))
    anc.r1_multiple_band(doc["mechanical"]).band["current"] = 7.5  # type: ignore[index]
    s = _split(doc)
    assert s.refusal and "no ex-lease observation" in s.refusal
    assert s.current_ebitda is None


def test_no_term_reads_the_pages_price() -> None:
    """The ImpliedValuation fence: the split is levels, never a gap to the price. SMPL's anchor sits
    under its page price, yet its margin effect is POSITIVE (+$1.62): the multiple's close of
    2026-10-27 predates the price's rise, which an EBITDA backed out of the price would fold in.
    The price moved by half leaves every number the same."""
    doc = frozen_doc("SMPL")
    s = _split(doc)
    assert s.margin_effect == pytest.approx(1.6183, abs=1e-4) and s.current_ebitda == 205.585
    moved = _copy(doc)
    moved["mechanical"]["stock_info"]["price"]["value"] *= 1.5
    assert _split(moved) == s


def test_a_split_that_does_not_rebuild_the_published_value_raises() -> None:
    """The reader refuses to split a number other than the one the anchor publishes."""
    doc = _copy(frozen_doc("LLY"))
    doc["anchor"]["anchor_base_value_per_share"] += 1.0
    with pytest.raises(ValueError, match="splitting another number"):
        anc.committed_gap_split(doc)


def test_a_derived_anchor_carries_its_split_at_todays_multiple() -> None:
    """End to end: `compute_anchor` on SMPL's real page and committed companyfacts writes the split,
    and it rebuilds the base it published at today's multiple (W50)."""
    doc = frozen_doc("SMPL")
    facts = json.loads((FACTS / "SMPL.json").read_text())
    a = anc.compute_anchor(doc["mechanical"], facts=facts, computed_at=NOW)
    assert a.anchor_base_value_per_share is not None and a.gap_split is not None
    assert a.gap_split.refusal is None
    assert sp.reproduces(a.gap_split, a.anchor_base_value_per_share, anc.MULTIPLE_CURRENT)
    assert a.gap_split.current_multiple == a.multiple.value  # type: ignore[union-attr]


def test_an_anchor_written_before_the_split_serialises_without_it() -> None:
    """Every committed anchor predates W61: validated and written back, it carries no `gap_split`
    key (absent, never null), so committed pages round-trip byte-identically."""
    a = anc.Anchor.model_validate(frozen_doc("LLY")["anchor"])
    assert a.gap_split is None
    assert '"gap_split"' not in a.model_dump_json(exclude=anc.anchor_absent_fields(a) or None)


def test_the_words_stay_inside_the_fence_and_carry_their_flags() -> None:
    """Every cut page's main-body line and arithmetic, the two strings both renderers print
    verbatim: never a signed percentage or a word of the ImpliedValuation fence (the screening
    block's own test, `test_parity_pins`), each term's figure present, and the stale and leverage
    sentences present exactly when their flags are set."""
    import re
    seen = 0
    for folder in sorted(p for p in CUT.iterdir() if (p / "dossier.json").is_file()):
        s = anc.committed_gap_split(frozen_doc(folder.name))
        if s is None:
            continue
        seen += 1
        text = " ".join([s.read, s.stale_line or "", s.leverage_line or "", *s.arithmetic])
        assert not re.search(r"[+-]\d+(\.\d+)?%", text), (folder.name, text)
        assert "`" not in text, (folder.name, "the web prints a backtick literally")
        for bad in ("spot", "upside", "discount", "price"):
            assert bad not in text.lower(), (folder.name, bad)
        assert f"${s.anchor_at_current:,.2f}" in s.read, folder.name
        assert f"${abs(s.multiple_effect):,.2f}" in s.read, folder.name
        if s.margin_effect is not None and s.value_at_current_ebitda is not None:
            assert f"${abs(s.margin_effect):,.2f}" in s.read, folder.name
            assert f"${s.value_at_current_ebitda:,.2f}" in s.read, folder.name
        assert (s.stale_line is not None) is bool(s.stale_close), folder.name
        assert (s.leverage_line is not None) is bool(s.leverage_flag), folder.name
        if s.stale_line is not None:
            assert str(s.close_age_days) in s.stale_line and str(s.multiple_close) in s.stale_line
        if s.leverage_line is not None and s.equity_sensitivity is not None:
            assert f"{s.equity_sensitivity:.1f}%" in s.leverage_line, folder.name
    assert seen == len(SPLIT_ON_CUT) + 1   # and GOOGL, refused


@pytest.mark.parametrize(("ticker", "line"), [
    ("LLY", "Screen value $820.15 at today's 27.9x = $1,397.90 on current EBITDA ($46,489M) − "
            "$577.74 margin reversion (mid-cycle 0.60× current). Median 25.7x: $67.92 lower "
            "(not used)."),
    ("WERN", "Screen value $39.93 at today's 6.9x = $27.90 on current EBITDA ($360M) + $12.04 "
             "margin reversion (mid-cycle 1.29× current). Median 6.7x: $1.61 lower (not used)."),
    ("IT", "Screen value $136.91 at today's 9.4x = $185.70 on current EBITDA ($1,421M) − $48.79 "
           "margin reversion (mid-cycle 0.77× current). Median 23.0x: $234.77 higher (not used)."),
])
def test_the_main_body_line_is_the_approved_one(ticker: str, line: str) -> None:
    """The operator approved this line's shape on LLY (2026-11-18: "Approve, shorter line"). The
    shape holds on every page: the margin sign follows the margin effect (WERN's is +), "lower" or
    "higher" follows the multiple effect (IT's is higher), and the ratio is the computed one. A
    deterministic string on a frozen page, so it is pinned word for word."""
    assert _split(frozen_doc(ticker)).read == line


def test_review_round_0_a_close_in_another_shape_or_after_the_page_never_misleads() -> None:
    """Review round 0: an unparseable close states no age and never raises (a display field must
    not sink the anchor); a close AFTER the page's stored close says so, never "-3 days"; and
    `compute_anchor` stamps the STORED close, as `committed_gap_split` reads it."""
    doc = frozen_doc("LLY")
    a = doc["anchor"]
    kw: dict[str, Any] = {"ex_lease": False, "current": 27.85306, "median": 25.682746,
                          "revenue": a["ltm_revenue"]["value"], "margin": a["margin"]["value"],
                          "d_and_a": a["d_and_a"]["value"], "net_debt": a["net_debt"]["value"],
                          "shares": anc.per_share_shares(a) or 0.0}
    odd = sp.gap_split(doc["mechanical"], close="Nov-02-2026", price_date=date(2026, 11, 11), **kw)
    assert odd.close_age_days is None and odd.stale_close is None
    after = sp.gap_split(doc["mechanical"], close="2026-11-14", price_date=date(2026, 11, 11),
                         **kw)
    assert after.close_age_days == -3
    assert any("3 days AFTER" in x for x in after.arithmetic)
    assert not any("-3 days" in x for x in after.arithmetic)
    # SMPL with its stored close's DATE cut (a cut from the real page) and that same day given as
    # the reference date: the facts read the same filings, but there is no stored close to name
    facts = json.loads((FACTS / "SMPL.json").read_text())
    smpl = _copy(frozen_doc("SMPL"))
    day = date.fromisoformat(smpl["mechanical"]["stock_info"].pop("as_of"))
    derived = anc.compute_anchor(smpl["mechanical"], facts=facts, computed_at=NOW,
                                 reference_date=day)
    assert derived.gap_split is not None and derived.gap_split.price_date is None
    assert derived.gap_split.stale_line is None
