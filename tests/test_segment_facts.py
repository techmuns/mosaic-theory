"""Segment PROFIT from a 10-K's own XBRL instance (vinci.edgar.segment_facts), pinned on
REAL filings.

Each fixture is the filer's own instance, trimmed to the facts the rules read and every context
those facts reference — so the distractors (prior years, geographic and expense-line axes, corporate
members) are the filer's, not hand-rolled. Each was proven, when frozen, to read IDENTICALLY to its
full instance. Value-level pins are safe here: these are frozen filings, not living artifacts.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from vinci.edgar import segment_facts as sf

_FIX = Path(__file__).resolve().parent / "fixtures" / "segment_facts"
_ROOT = Path(__file__).resolve().parents[1]


def _read(name: str) -> sf.SegmentProfitRead | None:
    path = next(_FIX.glob(f"{name}_*.xml"))
    return sf.parse_instance(path.read_text(), accession=path.stem.split("_", 1)[1])


def _m(read: sf.SegmentProfitRead) -> dict[str, tuple[float, float | None]]:
    return {f.segment: (f.profit / 1e6, None if f.revenue is None else f.revenue / 1e6)
            for f in read.figures}


def test_amzn_reconciles_to_the_dollar() -> None:
    """The standard shape: the business-segments axis, `OperatingIncomeLoss`. The three segments
    sum EXACTLY to the consolidated figure — the reconciliation, not an eyeball."""
    r = _read("AMZN")
    assert r is not None and r.measure == sf.OPERATING_INCOME
    assert _m(r) == {"Amazon Web Services": (45_606.0, 128_725.0),
                     "North America": (29_619.0, 426_305.0),
                     "International": (4_750.0, 161_894.0)}
    assert sum(f.profit for f in r.figures) == r.consolidated == 79_975e6


def test_googl_revenue_on_the_unqualified_business_axis_context() -> None:
    """Alphabet tags Cloud's INCOME on {segment, OperatingSegments} and its REVENUE on {segment}
    alone — one segment, stated twice. The identical-context join finds no revenue; the fallback,
    which exists only on the business-segments axis, finds it. The gap to consolidated is the
    reconciling items #578 pinned by hand from the rendered table: −16,760."""
    r = _read("GOOGL")
    assert r is not None
    got = _m(r)
    assert got["Google Cloud"] == (13_910.0, 58_705.0)
    assert got["Google Services"] == (139_404.0, 342_721.0)
    assert got["All Other"] == (-7_515.0, 1_537.0)
    assert r.consolidated is not None
    assert (r.consolidated - sum(f.profit for f in r.figures)) / 1e6 == pytest.approx(-16_760.0)


def test_epam_segments_are_geographies_on_the_filers_own_measure() -> None:
    """EPAM's operating segments ARE geographies — the geographical axis beside the
    operating-segments qualifier — on a filer-defined measure, `epam:SegmentOperatingProfitLoss`.
    Revenue comes from the IDENTICAL context; its business-axis 'Americas' revenue and its
    revenue-by-customer-location are different disclosures and are never name-joined in."""
    r = _read("EPAM")
    assert r is not None and r.measure == "epam:SegmentOperatingProfitLoss"
    assert r.measure_kind == "filer-defined segment measure"
    got = _m(r)
    assert set(got) == {"North America", "Europe"}
    assert got["North America"][0] == pytest.approx(522.115)
    assert got["Europe"][0] == pytest.approx(332.953)
    assert r.segments_total == pytest.approx(855_068e3) == sum(f.profit for f in r.figures)


def test_it_gross_profit_is_named_never_relabelled() -> None:
    """Gartner's segment measure is gross contribution, tagged `GrossProfit`. It is carried as a
    gross profit — calling it operating income would state a different figure under a familiar
    name, and the four segments sum to the consolidated gross profit exactly."""
    r = _read("IT")
    assert r is not None and r.measure == sf.GROSS_PROFIT and r.measure_kind == "gross profit"
    assert set(_m(r)) == {"Insights", "Conferences", "Consulting", "Other"}
    assert sum(f.profit for f in r.figures) == r.consolidated


def test_nikes_ebit_is_its_own_measure_and_outranks_its_gross_profit() -> None:
    """Nike's CODM runs its segments on EBIT, tagged `nke:EarningsBeforeInterestAndTaxes` — and the
    same filing tags `us-gaap:GrossProfit` on the SAME two segments. With only the ADJUSTED EBIT
    spelling recognised, gross profit won by default and NKE's first page (2026-09-22) printed
    NIKE Brand $19,300M / Converse $514M as "segment gross profit — the filer's measure".
    ⊕ EBIT is read; ⊖ the SAME filing with its EBIT facts removed falls back to gross profit —
    so the order, not the fixture, decides; ⊖ us-gaap's pre-tax income never reads as EBIT."""
    r = _read("NKE")
    assert r is not None and r.measure == "nke:EarningsBeforeInterestAndTaxes"
    assert r.measure_kind == "filer-defined segment measure"
    assert _m(r) == {"NIKE Brand": (5_855.0, 45_222.0), "Converse": (18.0, 1_174.0)}
    text = next(_FIX.glob("NKE_*.xml")).read_text()
    stripped = re.sub(r"<nke:EarningsBeforeInterestAndTaxes\b[^>]*>[^<]*"
                      r"</nke:EarningsBeforeInterestAndTaxes>", "", text)
    assert stripped.count("EarningsBeforeInterestAndTaxes") == 0 < text.count("<nke:Earnings")
    g = sf.parse_instance(stripped)
    assert g is not None and g.measure == sf.GROSS_PROFIT
    assert _m(g) == {"NIKE Brand": (19_300.0, 45_222.0), "Converse": (514.0, 1_174.0)}
    for us_gaap in ("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItems"
                    "NoncontrollingInterest", "OperatingIncomeLoss", "GrossProfit"):
        assert sf._FILER_MEASURE.search(us_gaap) is None, us_gaap


def test_a_plain_ebit_never_outranks_a_segment_specific_measure() -> None:
    """REVIEW OF #640. Filer measures are tried in name order, and "E" sorts before "S": a filer
    tagging a plain EBIT AND its CODM's `SegmentOperatingProfit` on the same segments would have
    had the plain EBIT printed as "the filer's own measure". Built on Nike's REAL instance — every
    EBIT fact kept, and a copy of each also tagged `nke:SegmentOperatingProfit` (EPAM's spelling).
    ⊕ the segment-specific spelling wins; ⊖ with no such spelling the plain EBIT still does."""
    text = next(_FIX.glob("NKE_*.xml")).read_text()
    both = re.sub(r"(<nke:EarningsBeforeInterestAndTaxes\b([^>]*)>([^<]*)"
                  r"</nke:EarningsBeforeInterestAndTaxes>)",
                  r"\1<nke:SegmentOperatingProfit\2>\3</nke:SegmentOperatingProfit>", text)
    assert both.count("<nke:SegmentOperatingProfit") == text.count("<nke:EarningsBefore") > 0
    r = sf.parse_instance(both)
    assert r is not None and r.measure == "nke:SegmentOperatingProfit"
    assert r.measure_kind == "filer-defined segment measure"
    n = _read("NKE")
    assert n is not None and n.measure == "nke:EarningsBeforeInterestAndTaxes"


def test_aort_members_that_carry_only_revenue_are_not_segments() -> None:
    """AORT tags four GEOGRAPHIC regions on the business-segments axis beside its two real segments.
    The regions carry revenue only, so the rule 'a segment is a member carrying the measure'
    excludes them without a list of names."""
    r = _read("AORT")
    assert r is not None and set(_m(r)) == {"Medical Devices", "Preservation Services"}
    assert sum(f.profit for f in r.figures) == r.consolidated


def test_eliminations_and_corporate_are_never_read_as_a_segment() -> None:
    """WERN and PARR tag INTERSEGMENT ELIMINATIONS and CORPORATE/reconciling items on the
    consolidation axis — WERN beside the segment axis itself. Admitted as segment contexts they
    would file an elimination under a segment's name (a second 'Truckload' row) or add a
    corporate line to the segments sum. Neither filing may yield anything but its real segments."""
    wern = _read("WERN")
    assert wern is not None
    assert [f.segment for f in wern.figures] == ["Truckload Transportation Services",
                                                 "Werner Logistics"]
    assert sum(f.profit for f in wern.figures) == wern.segments_total
    parr = _read("PARR")
    assert parr is not None
    assert _m(parr) == {"Refining": (487.032, 7_206.145), "Logistics": (97.558, 298.442),
                        "Retail": (74.706, 576.729)}

    # THE GUARD'S OWN PIN. On the fleet today eliminations carry REVENUE only, and the identical-
    # context join already keeps that revenue out — so the consolidation guard is a second layer
    # with no live witness. It is pinned on WERN's REAL elimination context
    # ({IntersegmentElimination, Truckload}), with an operating-income fact added there at the
    # elimination revenue's own value: admitted, it would become a second "Truckload" row.
    text = next(_FIX.glob("WERN_*.xml")).read_text()
    elim = re.search(
        r'<(?:\w+:)?context id="([^"]+)">(?:(?!</(?:\w+:)?context>).)*?'
        r'IntersegmentEliminationMember(?:(?!</(?:\w+:)?context>).)*?'
        r'TruckloadTransportationService', text, re.S)
    assert elim is not None, "WERN's elimination-on-a-segment context is not in the fixture"
    fact = re.search(rf'<us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax\b([^>]*'
                     rf'contextRef="{elim.group(1)}"[^>]*)>([^<]*)<', text)
    assert fact is not None
    extra = (f"<us-gaap:OperatingIncomeLoss{fact.group(1)}>{fact.group(2)}"
             f"</us-gaap:OperatingIncomeLoss>")
    guarded = sf.parse_instance(text.replace("</xbrl>", extra + "</xbrl>"))
    assert guarded is not None
    assert [f.segment for f in guarded.figures].count("Truckload Transportation Services") == 1


def test_operating_income_outranks_gross_profit_when_a_filer_tags_both() -> None:
    """The measure is chosen in a stated order: operating income, then a filer-defined segment
    measure, then gross profit. NO FILER ON THE FLEET TAGS BOTH on its segments, so this branch has
    no live witness — it is pinned on IT's real filing with an operating-income fact added on each
    of the SAME contexts at the SAME values, so no magnitude here is invented. Recorded as a branch
    with no corpus case, not as a measured behaviour."""
    text = next(_FIX.glob("IT_*.xml")).read_text()
    added = re.sub(r"(<us-gaap:GrossProfit\b([^>]*)>([^<]*)</us-gaap:GrossProfit>)",
                   r"\1<us-gaap:OperatingIncomeLoss\2>\3</us-gaap:OperatingIncomeLoss>", text)
    assert added.count("OperatingIncomeLoss") > text.count("OperatingIncomeLoss")
    r = sf.parse_instance(added)
    assert r is not None and r.measure == sf.OPERATING_INCOME
    assert r.measure_kind == "operating income"


def test_a_single_segment_filer_is_none_not_a_failure() -> None:
    """Since ASU 2023-07 a one-segment company tags that one segment (LLY); and TECX itemises its
    ONE segment's expenses on the income-statement-location axis beside the operating-segments
    qualifier. Both are single-segment filers — None, an answer. A rule accepting ANY axis beside
    the qualifier read TECX's five expense lines as five segments."""
    assert _read("LLY") is None
    tecx = next(_FIX.glob("TECX_*.xml")).read_text()
    assert "us-gaap:IncomeStatementLocationAxis" in tecx, "the distractor is in the fixture"
    assert sf.parse_instance(tecx) is None


def test_two_segments_without_a_profit_measure_refuse_loudly() -> None:
    """⊖ 'We could not find the profit' is a different fact from 'there is none'. EPAM's own filing
    with its segment measure removed still names two segments — and must raise, never return an
    empty breakdown."""
    text = next(_FIX.glob("EPAM_*.xml")).read_text()
    stripped = re.sub(
        r"<epam:SegmentOperatingProfitLoss[^>]*>[^<]*</epam:SegmentOperatingProfitLoss>", "", text)
    with pytest.raises(sf.SegmentFactsUnavailableError, match="no profit measure"):
        sf.parse_instance(stripped)


def test_a_measure_in_another_currency_is_refused() -> None:
    """⊖ A figure in a unit that is not USD is refused rather than printed unconverted — the scale
    defect this repo has recorded twice, arriving through currency instead of magnitude."""
    text = next(_FIX.glob("AMZN_*.xml")).read_text()
    # THE FACT THE PAGE PRINTS: AWS's FY2025 operating income. The guard is scoped to CURRENT-year
    # SEGMENT figures, so re-uniting a consolidated or a prior-year comparative would prove nothing
    # — both of which this pin did, silently, before it named its target by value.
    tag = re.search(r'<us-gaap:OperatingIncomeLoss\b[^>]*>45606000000<', text)
    assert tag is not None, "AWS FY2025 operating income is not in the fixture"
    unit = re.search(r'unitRef="[^"]+"', tag.group(0))
    assert unit is not None
    moved = tag.group(0).replace(unit.group(0), 'unitRef="eur"')
    # the unit is DECLARED, as a real instance declares it: the currency is read off the unit's own
    # <measure>, never off its id (review of #637)
    text = _declare_unit(text, "eur", "iso4217:EUR")
    with pytest.raises(sf.SegmentFactsUnavailableError, match="in EUR, not USD"):
        sf.parse_instance(text.replace(tag.group(0), moved, 1))


def _declare_unit(text: str, uid: str, measure: str) -> str:
    return text.replace("</xbrl>", f'<unit id="{uid}"><measure>{measure}</measure></unit>\n</xbrl>',
                        1)


# --- (review of #637) mutations of REAL fixtures, each a shape the first cut misread ------------
def test_the_currency_is_read_off_the_unit_not_its_id() -> None:
    """The unitRef is an ID the FILER chose ("usd", "U_USD", "U001"). The first cut refused any id
    without the letters "usd" in it — so a filer naming its dollar unit "U001" lost its whole block
    to UNKNOWN. ⊕ an opaque id declared as iso4217:USD reads identically; ⊖ an undeclared id is
    refused, never assumed to be dollars."""
    text = next(_FIX.glob("AMZN_*.xml")).read_text()
    assert text.count('<unit id="usd">') == 1
    opaque = text.replace('<unit id="usd">', '<unit id="U001">').replace(
        'unitRef="usd"', 'unitRef="U001"')
    r = sf.parse_instance(opaque)
    assert r is not None and _m(r)["Amazon Web Services"] == (45_606.0, 128_725.0)
    assert sum(f.profit for f in r.figures) == r.consolidated == 79_975e6
    undeclared = text.replace('<unit id="usd">', '<unit id="other">')
    with pytest.raises(sf.SegmentFactsUnavailableError, match="never declares"):
        sf.parse_instance(undeclared)


def test_a_segment_margin_percentage_is_not_a_currency_defect() -> None:
    """A filer that tags its segments' adjusted-EBITDA MARGIN (unit pure) matched the filer-measure
    pattern, and the first cut refused the whole filing as "not USD" — a percentage is not an
    unconverted currency. It is skipped; the dollar measure beside it still reads."""
    text = _declare_unit(next(_FIX.glob("AMZN_*.xml")).read_text(), "pure", "xbrli:pure")
    tag = re.search(
        r'<us-gaap:OperatingIncomeLoss\b[^>]*>45606000000</us-gaap:OperatingIncomeLoss>', text)
    assert tag is not None
    pct = (tag.group(0).replace("us-gaap:OperatingIncomeLoss", "amzn:SegmentAdjustedEBITDAMargin")
           .replace('unitRef="usd"', 'unitRef="pure"').replace(">45606000000<", ">0.354<"))
    if "xmlns:amzn=" not in text:
        text = text.replace("<xbrl ", '<xbrl xmlns:amzn="http://www.amazon.com/20251231" ', 1)
    r = sf.parse_instance(text.replace(tag.group(0), tag.group(0) + pct, 1))
    assert r is not None and r.measure == sf.OPERATING_INCOME and len(r.figures) == 3


def test_the_period_is_the_required_contexts_end_not_the_dei_value() -> None:
    """A 52/53-week filer may state DocumentPeriodEndDate as the nominal month-end while every
    context ends on the actual last day of its fiscal year. Matched on the VALUE, no fact is a
    fiscal-year fact, no segment is seen, and a three-segment filer returned None — "single
    segment", silently. The required context's own end is the period."""
    text = next(_FIX.glob("AMZN_*.xml")).read_text()
    pe = re.search(r"(<dei:DocumentPeriodEndDate[^>]*>)2025-12-31<", text)
    assert pe is not None
    shifted = text.replace(pe.group(0), pe.group(1) + "2026-01-02<", 1)
    r = sf.parse_instance(shifted)
    assert r is not None and len(r.figures) == 3 and r.period_end.isoformat() == "2025-12-31"


def test_a_segment_stated_twice_is_one_segment_not_two() -> None:
    """Alphabet states each segment on {segment} AND {segment, OperatingSegments}. The first cut
    keyed carriers by CONTEXT, so a profit tagged on both listed Cloud twice and summed it twice.
    ⊕ equal figures → one row, the reconciliation unchanged; ⊖ unequal figures → refused."""
    text = next(_FIX.glob("GOOGL_*.xml")).read_text()
    base = sf.parse_instance(text)
    assert base is not None
    bare = next(
        cid for cid, body in re.findall(r'<context id="([^"]+)">(.*?)</context>', text, re.S)
        if "goog:GoogleCloudMember" in body and "ConsolidationItemsAxis" not in body
        and "<startDate>2025-01-01</startDate>" in body
        and body.count("</xbrldi:explicitMember>") == 1)
    anchor = re.search(
        r'<us-gaap:OperatingIncomeLoss\b[^>]*>13910000000</us-gaap:OperatingIncomeLoss>', text)
    assert anchor is not None

    def with_bare(value: str) -> str:
        extra = (f'<us-gaap:OperatingIncomeLoss contextRef="{bare}" decimals="-6" id="f-dup" '
                 f'unitRef="usd">{value}</us-gaap:OperatingIncomeLoss>')
        return text.replace(anchor.group(0), anchor.group(0) + extra, 1)

    twice = sf.parse_instance(with_bare("13910000000"))
    assert twice is not None
    assert [f.segment for f in twice.figures].count("Google Cloud") == 1
    assert _m(twice) == _m(base)
    with pytest.raises(sf.SegmentFactsUnavailableError, match="twice with different figures"):
        sf.parse_instance(with_bare("13000000000"))


def test_humanise_keeps_the_filers_words() -> None:
    assert sf.humanise("amzn:AmazonWebServicesSegmentMember") == "Amazon Web Services"
    assert sf.humanise("parr:RefiningMember") == "Refining"
    assert sf.humanise("srt:NorthAmericaMember") == "North America"


def test_the_page_sentence_names_the_measure_and_the_reconciliation() -> None:
    """The ONE sentence both renderers print — written in mechanical, pinned on frozen filings."""
    from vinci.dossier.mechanical import _segment_profit_line
    amzn, googl, it = _read("AMZN"), _read("GOOGL"), _read("IT")
    assert amzn and googl and it
    a = _segment_profit_line(amzn)
    assert a.startswith("FY2025 segment operating income (10-K XBRL): Amazon Web Services $45,606M")
    assert a.endswith("segments sum $79,975M = consolidated $79,975M.")
    g = _segment_profit_line(googl)
    assert "All Other −$7,515M (margin n.m.)" in g        # −488.9% is arithmetic, not information
    assert "(−$16,760M not allocated to segments)" in g
    assert "gross profit — the filer's measure" in _segment_profit_line(it)
    nke = _read("NKE")
    assert nke is not None
    n = _segment_profit_line(nke)
    assert n == ("FY2026 segment profit on the filer's own measure, "
                 "nke:EarningsBeforeInterestAndTaxes (10-K XBRL): "
                 "NIKE Brand $5,855M (12.9% margin) · Converse $18M (1.5% margin) — "
                 "segments sum $5,873M.")
    assert "gross profit" not in n


def test_committed_pages_round_trip_without_the_new_key() -> None:
    """THE CORPUS CHECK for the additive claim: no committed page grows a key on round-trip — a page
    without the block gains no null, a page with one keeps it.

    Asserted as presence PARITY, not absence. The first version asserted the key never appears,
    which holds only until an artifact pass lands a real block — and it reddened on exactly that
    pass (AMZN, 2026-09-21), a guard written for a null key refusing a legitimate one."""
    from vinci.dossier.schemas import Dossier, dossier_json
    pages = sorted((_ROOT / "data" / "dossiers").glob("*/dossier.json"))
    assert pages, "no committed pages — the pin is blind"
    for jp in pages:
        raw = jp.read_text()
        written = dossier_json(Dossier.model_validate_json(raw))
        assert ('"segment_profit"' in written) is ('"segment_profit"' in raw), (
            f"{jp.parent.name} grew or lost the key on round-trip")
        assert '"segment_profit": null' not in written, f"{jp.parent.name} grew a null key"


def test_the_line_reaches_both_pages_and_a_single_segment_page_draws_nothing() -> None:
    """TEST-LAYER RULE — real committed JSON → render → assertion, in BOTH renderers. AMZN's page,
    given the block its own 10-K produces, prints the heading and the stored sentence; EPAM's page
    as committed (no block) prints no segment-profit line — and above all no UNKNOWN badge."""
    from vinci.dossier import render as dr
    from vinci.dossier.mechanical import _segment_profit_line
    from vinci.dossier.schemas import Dossier, SegmentEconomics, SegmentProfitRow, Sourced
    r = _read("AMZN")
    assert r is not None
    block = SegmentEconomics(
        measure=r.measure, measure_kind=r.measure_kind, fiscal_year_end=r.period_end.isoformat(),
        rows=[SegmentProfitRow(segment=f.segment, member=f.member, profit=f.profit / 1e6,
                               revenue=(f.revenue / 1e6 if f.revenue else None))
              for f in r.figures],
        segments_sum=sum(f.profit for f in r.figures) / 1e6, consolidated=79_975.0,
        line=_segment_profit_line(r))
    page = json.loads((_ROOT / "data/dossiers/AMZN/dossier.json").read_text())
    page["mechanical"]["concentration"]["segment_profit"] = json.loads(
        Sourced.present(block, source_ref="EDGAR 10-K fixture").model_dump_json())
    doc = Dossier.model_validate(page)
    md = dr.render_markdown(doc)
    assert "Segments (profit — the filer's own measure, 10-K)" in md and block.line in md
    epam = Dossier.model_validate_json((_ROOT / "data/dossiers/EPAM/dossier.json").read_text())
    assert "Segments (profit" not in dr.render_markdown(epam)

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const dj = pathToFileURL(path.resolve("frontend/views/shared/dossier.js")).href;
const { renderDossier } = await import(dj);
const on = renderDossier(JSON.parse(readFileSync(process.argv[1], "utf8")), null);
const epam = JSON.parse(readFileSync("data/dossiers/EPAM/dossier.json", "utf8"));
const off = renderDossier(epam, null);
console.log(JSON.stringify({ on: on.includes("Segment profit (the filer"),
  sentence: on.includes("Amazon Web Services $45,606M"),
  off: off.includes("Segment profit (the filer") }));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(page, fh)
    out = subprocess.run(["node", "--input-type=module", "-e", driver, fh.name], cwd=_ROOT,
                         capture_output=True, text=True, check=True)
    assert json.loads(out.stdout.strip().splitlines()[-1]) == {"on": True, "sentence": True,
                                                               "off": False}


def test_nikes_ebit_line_reaches_both_renderers_and_the_gross_profit_label_does_not_e2e() -> None:
    """TEST-LAYER RULE — the mislabel was OBSERVED on NKE's rendered page (its first assembly,
    2026-09-22), so it is pinned through the renderers: the block Nike's own 10-K produces, carried
    on a real committed page, prints the EBIT sentence in the Python AND the JS renderer, and
    neither prints "gross profit — the filer's measure". A carrier page is used because NKE's own
    page lands in the artifact pass that follows this change, never in a code commit."""
    from vinci.dossier import render as dr
    from vinci.dossier.mechanical import _segment_profit_line
    from vinci.dossier.schemas import Dossier, SegmentEconomics, SegmentProfitRow, Sourced
    r = _read("NKE")
    assert r is not None
    block = SegmentEconomics(
        measure=r.measure, measure_kind=r.measure_kind, fiscal_year_end=r.period_end.isoformat(),
        rows=[SegmentProfitRow(segment=f.segment, member=f.member, profit=f.profit / 1e6,
                               revenue=(f.revenue / 1e6 if f.revenue else None))
              for f in r.figures],
        segments_sum=sum(f.profit for f in r.figures) / 1e6, line=_segment_profit_line(r))
    page = json.loads((_ROOT / "data/dossiers/AMZN/dossier.json").read_text())
    page["mechanical"]["concentration"]["segment_profit"] = json.loads(
        Sourced.present(block, source_ref="EDGAR 10-K fixture").model_dump_json())
    md = dr.render_markdown(Dossier.model_validate(page))
    assert block.line in md and "nke:EarningsBeforeInterestAndTaxes" in md
    assert "gross profit — the filer's measure" not in md

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const dj = pathToFileURL(path.resolve("frontend/views/shared/dossier.js")).href;
const { renderDossier } = await import(dj);
const on = renderDossier(JSON.parse(readFileSync(process.argv[1], "utf8")), null);
console.log(JSON.stringify({ ebit: on.includes("nke:EarningsBeforeInterestAndTaxes"),
  sentence: on.includes("NIKE Brand $5,855M (12.9% margin)"),
  gp: on.includes("gross profit — the filer") }));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(page, fh)
    out = subprocess.run(["node", "--input-type=module", "-e", driver, fh.name], cwd=_ROOT,
                         capture_output=True, text=True, check=True)
    assert json.loads(out.stdout.strip().splitlines()[-1]) == {"ebit": True, "sentence": True,
                                                               "gp": False}
