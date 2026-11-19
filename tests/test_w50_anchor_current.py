"""W50 (STATE §5.0 row 10, open item (b)) — the page's R1 screening anchor prices TODAY'S multiple.

Recipe 3a (#1093) made R1's PROPOSED base multiple the band's current, the median beside it; the
page's own anchor (`anchor.multiple`) still priced the median, so SMPL's page read 18.2256x where
its template proposed 5.1351x. These pins hold the anchor to the same multiple, built from the REAL
committed pages and their committed companyfacts fixtures (no CIQ bundle: the pins choose pages
whose bridge EDGAR completes alone). Value pins read the frozen cut (`frozen_support.frozen_doc`);
the invariants walk the roster (`covered_where`), as every pin has since W27's slices.

Positive: every covered page's anchor (a roster walk) prices its band's current, the one the
proposal proposes; the
base is struck on it; the median and the close date sit beside it; the lease prefix readers key on
is kept. Negative: a band with no usable current (dropped, None, NM, 0, negative, infinite) prices
NOTHING and says why, never the median; the gate then refuses an R1 record; a committed (pre-W50)
anchor round-trips byte-identically and renders its median words on both surfaces, while a
derived one renders today's.
"""
from __future__ import annotations

import json
import math
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.anchor_reads import NO_BARS, NO_FILINGS
from tests.frozen_support import covered_pages, covered_where, frozen_doc, frozen_page
from tests.w73_lly_expected import as_derived
from vinci.dossier import anchor as anc
from vinci.dossier import propose
from vinci.dossier import render as dr
from vinci.dossier.schemas import Dossier, dossier_json

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "data" / "dossiers"
FACTS = ROOT / "tests" / "fixtures" / "companyfacts"
NOW = datetime(2026, 11, 17, tzinfo=UTC)


def _doc(t: str) -> dict[str, Any]:
    """``t``'s FROZEN copy (the cut at 4889ddba) — a value pin never reads a living page."""
    return frozen_doc(t)


def _derive(doc: dict[str, Any]) -> anc.Anchor:
    facts = json.loads((FACTS / f"{doc['ticker']}.json").read_text())
    return anc.compute_anchor(doc["mechanical"], facts=facts, computed_at=NOW,
                              filings=NO_FILINGS, eod_closes=NO_BARS)


def _band(doc: dict[str, Any]) -> dict[str, Any]:
    """The band R1 prices on, as the anchor itself selects it (`r1_multiple_band`)."""
    band = anc.r1_multiple_band(doc["mechanical"]).band
    assert isinstance(band, dict), f"{doc['ticker']}: no R1 band on the page"
    return band


def _without_current(doc: dict[str, Any], current: Any, *, drop: bool = False) -> dict[str, Any]:
    """The REAL page with its R1 band's `current` replaced (or removed) — no committed page has
    ever carried an unusable current (recipe 3a's `git log -S` over the pages), so the negative is
    cut from a real one and says so."""
    d: dict[str, Any] = json.loads(json.dumps(doc))
    band = _band(d)
    if drop:
        band.pop("current")
    else:
        band["current"] = current
    return d


def _base_at(a: anc.Anchor, multiple: float) -> float:
    """R1's arithmetic (`midcycle.scenario_value`) on the anchor's own inputs at `multiple`."""
    assert a.ltm_revenue and a.margin and a.d_and_a and a.net_debt
    assert None not in (a.ltm_revenue.value, a.margin.value, a.d_and_a.value, a.net_debt.value)
    shares = anc.per_share_shares(a.model_dump(mode="json"))
    assert shares
    ev = (a.ltm_revenue.value * a.margin.value + a.d_and_a.value) * multiple  # type: ignore[operator]
    return (ev - a.net_debt.value) * 1e6 / shares  # type: ignore[operator]


# --- (+) the anchor prices the current, the one the template proposes -------------------------
def test_every_covered_page_prices_the_current_its_template_proposes() -> None:
    """(+) THE POINT OF W50, on every committed page whose anchor reaches the multiple leg: the
    screen's multiple IS the band's current and IS recipe 3a's proposed base multiple — one number
    on the page and in the template, the median beside it. Phrasing-free, so it holds as the
    living pages are rebuilt."""
    compared = []
    walked = covered_where(
        lambda t, d: (FACTS / f"{t}.json").exists()
        and anc.r1_multiple_band(d.get("mechanical") or {}).band is not None,
        "carries an R1 band and a committed companyfacts fixture")
    for _t, doc in walked:
        a = _derive(doc)
        if a.multiple is None:
            continue                      # stopped before the multiple leg (no band, R2, ...)
        band = _band(doc)
        assert a.multiple.statistic == anc.MULTIPLE_CURRENT, doc["ticker"]
        assert a.multiple.value == pytest.approx(float(band["current"])), doc["ticker"]
        assert a.multiple.median == pytest.approx(float(band["median"])), doc["ticker"]
        assert a.multiple.as_of == str(band["as_of"]), doc["ticker"]
        prop = [x for x in propose.propose_anchors(doc) if x.axis == "multiple"]
        if prop and anc.lease_basis_mismatch(doc) is None:
            assert prop[0].schema_value == pytest.approx(a.multiple.value), doc["ticker"]
        compared.append(doc["ticker"])
    # no fixed floor: `covered_where` fails loud when nothing qualifies, and a retirement edits no
    # test (tests/test_named_page_pins.py); this asserts only that the walk reached the leg once
    assert compared, "no covered page reached the multiple leg — the invariant walked nothing"


def test_smpl_strikes_its_screen_value_on_the_current_not_the_median() -> None:
    """(+) SMPL, the brief's case: ex-lease band current 5.135093x, median 18.2256495x (as of
    2026-10-27 on the page at this commit — read from the page, never typed). The base is R1's
    arithmetic at the CURRENT, and it is not the value the median would strike."""
    doc = _doc("SMPL")
    band = _band(doc)
    a = _derive(doc)
    assert a.applicable and a.anchor_base_value_per_share is not None and a.multiple is not None
    assert a.multiple.value == pytest.approx(float(band["current"]))
    assert a.anchor_base_value_per_share == pytest.approx(_base_at(a, float(band["current"])),
                                                          rel=1e-4)
    assert a.anchor_base_value_per_share != pytest.approx(_base_at(a, float(band["median"])),
                                                          rel=1e-2)
    # the lease prefix every reader keys on is kept, and the citation names the statistic priced
    assert a.multiple.source.startswith("valuation.lease_basis.ex_lease_band.current")
    assert anc.anchor_prices_ex_lease(a.model_dump(mode="json"))
    assert anc.lease_basis_mismatch({**doc, "anchor": a.model_dump(mode="json")}) is None


def test_a_page_on_ciqs_own_history_cites_its_current() -> None:
    """(+) BRBR, CIQ's own band (rent immaterial): the citation names `own_history.current`, the
    anchor reads lease-inclusive, and the lease test still finds the anchor on the page's basis."""
    doc = _doc("BRBR")
    a = _derive(doc)
    assert a.multiple is not None and a.multiple.source == "valuation.own_history.current"
    assert a.multiple.value == pytest.approx(float(_band(doc)["current"]))
    assert not anc.anchor_prices_ex_lease(a.model_dump(mode="json"))
    assert anc.lease_basis_mismatch({**doc, "anchor": a.model_dump(mode="json")}) is None


# --- (-) no usable current: nothing priced, never the median ----------------------------------
@pytest.mark.parametrize("current, drop", [(None, True), (None, False), ("NM", False), (0, False),
                                           (-3.2, False), (math.inf, False), (True, False)])
def test_no_usable_current_prices_nothing_and_never_the_median(current: Any, drop: bool) -> None:
    """(-) SMPL's real page with its band's current made unusable: no multiple, no screen value,
    `applicable` False, and the reason names the missing current and the median it refused to
    put in its place. An "NM" cell raised in `_band_read` before (float("NM"))."""
    doc = _without_current(_doc("SMPL"), current, drop=drop)
    a = _derive(doc)
    assert a.multiple is not None and a.multiple.value is None
    assert a.multiple.statistic == anc.MULTIPLE_CURRENT
    assert a.anchor_base_value_per_share is None and a.anchor_base_value_per_share_diluted is None
    assert a.applicable is False and a.recipe_hint == anc.RECIPE_R1
    assert a.reason is not None and "no usable current multiple" in a.reason
    assert "never priced in its place" in a.reason
    assert a.multiple.median == pytest.approx(float(_band(doc)["median"]))


def test_the_gate_refuses_an_r1_record_where_the_screen_has_no_current() -> None:
    """(-) `check_tier_agreement` reads `applicable`: a page whose band carries no usable current
    refuses an R1 record, as a page with an incomplete bridge already does — and the real page,
    current intact, does not."""
    real = _doc("SMPL")
    real["anchor"] = _derive(real).model_dump(mode="json")
    propose.check_tier_agreement(real, anc.RECIPE_R1)
    gone = _without_current(_doc("SMPL"), None, drop=True)
    gone["anchor"] = _derive(gone).model_dump(mode="json")
    with pytest.raises(propose.ProposalRefusedError, match="applicable=False"):
        propose.check_tier_agreement(gone, anc.RECIPE_R1)


def test_one_reader_decides_a_usable_current() -> None:
    """(-) The proposal and the anchor share ONE test of a usable current, so a page can never
    propose a multiple its screen refuses (or the reverse)."""
    assert propose._usable_multiple is anc.usable_multiple
    for v in (None, "NM", 0, -1.0, math.nan, math.inf, True):
        assert anc.usable_multiple(v) is None, v
    assert anc.usable_multiple(5.135093) == 5.135093


# --- (-) the gap sentence no longer claims a matched median pair ------------------------------
@pytest.mark.parametrize("ticker, side, word", [("WLK", "BELOW", "overstate"),
                                                ("NFLX", "ABOVE", "understate")])
def test_the_gap_sentence_names_the_unmatched_pair(ticker: str, side: str, word: str) -> None:
    """(-) Where the twelve months sit five points or more off the median, today's multiple was
    struck on off-median earnings. The sentence says which way that pushes the value (arithmetic at
    one price), and no longer says R1 pairs the median with the median multiple."""
    a = _derive(_doc(ticker))
    assert a.midcycle_gap is not None, f"{ticker}'s own numbers no longer fire the flag"
    assert a.midcycle_gap.ltm_side.upper() == side
    read = a.midcycle_gap.read
    assert "with the median multiple" not in read
    # (W73) the multiple is the history's latest close, dated, never "today's"
    assert "at its own history's multiple at the latest close" in read and f"can {word}" in read
    assert "today" not in read


# --- (-) committed pages keep what they priced, on both surfaces ------------------------------
def test_committed_pages_round_trip_and_state_what_they_priced() -> None:
    """(-) Every committed anchor round-trips byte-identically, whichever statistic it priced. One
    written before W50 carries no `statistic` and gains none of `statistic`, `as_of` or `median`
    (absent, never null). One written since states `statistic` and `median`, and `as_of` wherever
    its band dates the close (absent, never null, where it does not). The fleet holds both kinds
    while the watch pages wait for their next build, so the pin states the rule for each kind,
    never a count of either (the first cut asserted every page predated W50, which held only
    until the refresh)."""
    seen = 0
    for t in covered_pages():
        raw = (PAGES / t / "dossier.json").read_text()
        if _round_trips_by_its_kind(t, raw):
            seen += 1
    assert seen, "no covered page carries an anchor multiple — the round-trip checked nothing"


def _round_trips_by_its_kind(t: str, raw: str) -> bool:
    """The per-kind rule on one page's text; False when the page has no anchor multiple."""
    doc = Dossier.model_validate_json(raw)
    if doc.anchor is None or doc.anchor.multiple is None:
        return False
    out = dossier_json(doc)
    mult = json.loads(out)["anchor"]["multiple"]
    if doc.anchor.multiple.statistic is None:
        assert not {"statistic", "as_of", "median"} & set(mult), t
    else:
        assert doc.anchor.multiple.statistic == anc.MULTIPLE_CURRENT, t
        assert mult.get("statistic") == anc.MULTIPLE_CURRENT, t
        assert mult.get("median") is not None, t
        assert mult.get("as_of", "absent") is not None, t     # absent is allowed; null never
    # (W73) LLY's one expected leaf (tests/w73_lly_expected.py)
    assert out == as_derived(t, raw), f"{t} does not round-trip byte-identically"
    return True


def test_a_w50_anchor_round_trips_by_the_same_rule() -> None:
    """(+) The W50 branch of the rule above, run on main as well as after a refresh. SMPL's frozen
    page carries the anchor W50 derives for it, is written by the one writer, and is held to the
    same rule. Main's pages carry no W50 anchor yet, so without this the branch ran on no page
    (review round 1 of #1117: a mutant breaking it passed on main)."""
    page = {**_doc("SMPL"), "anchor": json.loads(_derive(_doc("SMPL")).model_dump_json())}
    raw = dossier_json(Dossier.model_validate(page))
    assert _round_trips_by_its_kind("SMPL", raw)


def _md(a: anc.Anchor | None) -> str:
    return "\n".join(dr._screening_context_lines(a))


def test_both_renderers_print_what_each_anchor_priced() -> None:
    """(+/-) TEST-LAYER RULE, real committed JSON → render → assertion. SMPL's COMMITTED anchor
    (median) prints the median words on both surfaces; its W50 anchor prints today's multiple, the
    close it was struck at and the median beside it, and none of the median-pricing words."""
    page = _doc("SMPL")
    committed = Dossier.model_validate(page).anchor
    derived = _derive(page)
    assert derived.multiple is not None and derived.multiple.median is not None
    old, new = _md(committed), _md(derived)
    assert "Median multiple, own history" in old and dr._SCREEN_METHOD_R1 in old
    # (W73) the row is named for the dated close, never "current"
    assert "Multiple at the latest close, own history" not in old
    assert "Multiple at the latest close, own history" in new
    assert dr._SCREEN_METHOD_R1_DATED in new   # (W73) a derived anchor records its verdict
    assert f"close of {derived.multiple.as_of}" in new
    assert f"median {derived.multiple.median:.1f}x beside it, not used" in new
    assert "Median multiple, own history" not in new and dr._SCREEN_SUBTITLE not in new

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    after = {**page, "anchor": json.loads(derived.model_dump_json(
        exclude=anc.anchor_absent_fields(derived) or None))}
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const dj = pathToFileURL(path.resolve("frontend/views/shared/dossier.js")).href;
const { renderDossier } = await import(dj);
const out = {};
for (const [k, f] of [["old", process.argv[2]], ["new", process.argv[3]]]) {
  out[k] = renderDossier(JSON.parse(readFileSync(f, "utf8")), null);
}
process.stdout.write(JSON.stringify(out));
"""
    tmp = ROOT / ".pytest_w50_tmp"
    tmp.mkdir(exist_ok=True)
    try:
        (tmp / "drv.mjs").write_text(driver)
        (tmp / "after.json").write_text(json.dumps(after))
        before = frozen_page("SMPL") / "dossier.json"
        res = subprocess.run(["node", str(tmp / "drv.mjs"), str(before), str(tmp / "after.json")],
                             cwd=ROOT, capture_output=True, text=True, check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    html = json.loads(res.stdout)
    assert "Median multiple, own history" in html["old"]
    assert "Multiple at the latest close, own history" not in html["old"]
    assert "Multiple at the latest close, own history" in html["new"]
    assert "Median multiple, own history" not in html["new"]
    assert f"median {derived.multiple.median:.1f}x beside it, not used" in html["new"]


# --- review round 0 (`/code-review high --fix`) -----------------------------------------------
def test_the_lease_line_never_says_r1_prices_a_current_it_does_not_have() -> None:
    """(-) SMPL is lease-material: its md lease line names what R1 prices. With a usable current it
    says the current; with none it says R1 prices nothing — never that it prices a current."""
    from vinci.dossier.render import render_markdown

    def lease_line(doc: dict[str, Any]) -> str:
        page = {**doc, "anchor": json.loads(_derive(doc).model_dump_json())}
        md = render_markdown(Dossier.model_validate(page))
        lines = [ln for ln in md.splitlines() if "Multiple basis — read before the level" in ln]
        assert len(lines) == 1, lines
        return lines[0]

    ok = lease_line(_doc("SMPL"))
    assert "R1 prices that history's current multiple" in ok
    gone = lease_line(_without_current(_doc("SMPL"), -1.0))
    assert "R1 prices nothing on it" in gone and "prices that history's current" not in gone


# --- review round 1 (`/code-review high`, Codex failed at its usage limit) -------------------
@pytest.mark.parametrize("ticker", ["WLK", "NFLX"])
def test_the_gap_sentence_never_points_at_the_value(ticker: str) -> None:
    """(-) The gap flag also rides on an R1 anchor that publishes NO value (inputs incomplete), so
    the sentence says "an R1 value", never "the value" or "this value" — the rule the code comment
    beside the tails states, and the W50 tails first broke."""
    a = _derive(_doc(ticker))
    assert a.midcycle_gap is not None
    read = a.midcycle_gap.read
    assert "the value" not in read and "this value" not in read, read
    assert "an R1 value can" in read
