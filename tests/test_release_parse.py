"""(RC-1 A) Release-parser regression pins — committed REAL EDGAR EX-99.1 excerpts (public domain),
so the pins verify in CI WITHOUT network. The 99.1 locator (tolerant + multi-variant + negative) is
pinned on real filenames. A miss fails LOUD (qa_flags), never fabricating a value (the PR-2 lesson).
"""
from __future__ import annotations

import typing
from typing import Any

from vinci.edgar import release_parse as rp
from vinci.netcache import CachedHttp, HttpError

_SRC = "8-K 0000000000-00-000000 Ex-99.1"


def _by(items: list[Any], **kw: Any) -> Any:
    return next((i for i in items if all(getattr(i, k) == v for k, v in kw.items())), None)


def test_a1_pricing_action_qualitative_and_ma_excluded() -> None:
    """(PR-B A1) Pricing-action rows are verbatim-bound and QUALITATIVE by default — a headline
    '7% increase' is revenue growth, NOT a price change, so value_num stays None. M&A/merger
    'purchase price adjustment' boilerplate is NOT a pricing action (excluded)."""
    # VITL-shaped real language → a qualitative pricing-action row, value_num None
    vitl = rp.operating_drivers(
        "Reflecting Strong Consumer Demand and Successful Strategic Pricing Actions; the 7% "
        "increase from 2024 results.", source_ref=_SRC)
    assert len(vitl) == 1 and vitl[0].kind.value == "pricing_action"
    assert vitl[0].value_num is None  # the headline 7% is revenue growth, not the price action
    assert "pricing action" in vitl[0].value.lower() and vitl[0].tier == "anchored"
    # a % TIGHTLY bound to the price → captured
    tight = rp.operating_drivers("We implemented a list price increase of 7% in March.",
                                 source_ref=_SRC)
    assert tight and tight[0].value_num == 7.0 and tight[0].unit == "%"
    # ⊖ M&A boilerplate: 'purchase price adjustment' / merger context is not a pricing action
    assert rp.operating_drivers(
        "Subject to purchase price adjustments and indemnification under the merger agreement.",
        source_ref=_SRC) == []
    # ⊖ a nearby UNRELATED % must NOT misbind as the price change — the row stays QUALITATIVE
    for txt in (
        "Net price increases, net of 8% rebates, contributed to the quarter.",
        "Pricing actions, offset by 4% higher logistics costs, in the period.",
        "Pricing actions contributed to gross margin of 40% in the period.",
    ):
        rows = rp.operating_drivers(txt, source_ref=_SRC)
        assert rows and rows[0].value_num is None, f"misbound %: {txt!r} → {rows[0].value_num}"
    # ⊖ a NEGATED pricing statement is not a pricing action
    assert rp.operating_drivers(
        "We did not raise prices during the quarter.", source_ref=_SRC) == []
    assert rp.operating_drivers(
        "There were no price increases in the period.", source_ref=_SRC) == []


def test_a1_leading_indicator_governed_and_false_positives_excluded() -> None:
    """(PR-B A1) A KPI row requires a shipped/added verb GOVERNING the number+unit — the two
    observed false-positive shapes are pinned OUT: an expense line-item carrying a unit word
    (FUBO), and a product spec ('290Ah cell', MVST)."""
    kpi = rp.operating_drivers("We shipped approximately 536 MWh in the quarter.", source_ref=_SRC)
    assert len(kpi) == 1 and kpi[0].kind.value == "leading_indicator"
    assert kpi[0].value_num == 536.0 and kpi[0].unit == "MWh"
    # ⊖ expense line-item carrying a unit word (adjacency, no governing verb)
    assert rp.operating_drivers("Subscriber related expenses 946,705 subscribers.",
                                source_ref=_SRC) == []
    # ⊖ product spec — a number+unit with no shipped/added verb
    assert rp.operating_drivers(
        "the launch of our 290Ah cell-based platform.", source_ref=_SRC) == []


def test_ex991_locator_tolerant_multi_and_negative() -> None:
    r"""Tolerant 99.1 filename match — the three observed forms (ex991 / dex991 / the ex99_1
    underscore the old \W* class silently dropped); 99.2 / 99_2 NEVER match (the negative pin)."""
    for name in ("mvst2025q4ex991earningspre.htm", "d123116dex991.htm", "vrrm-ex99_1.htm",
                 "ex-99.1.htm", "dex99d1.txt"):
        assert rp._is_ex991(name), name
    for name in ("vrrm-ex99_2.htm", "d1dex992.htm", "ex99_2.htm", "ex-99.2.htm",
                 "primary-doc.htm", "ex991.pdf"):
        assert not rp._is_ex991(name), name


# --- REAL EDGAR excerpts (public domain), normalized (nbsp already folded) ------------------------

_MVST_FY25 = (
    "Exhibit 99.1 Microvast Reports 2025 Financial Results • Full Year revenue of $427.5 "
    "million, an increase of 12.6% compared to $379.8 million in 2024 • Gross margin decreased "
    "to 28.6%, compared to 31.5% in 2024, this change was primarily attributable to a $32.5 "
    "million inventory impairment charge related to specialized ESS components. • Non-GAAP "
    "adjusted EBITDA of positive $44.7 million, compared to Non-GAAP adjusted EBITDA of negative "
    "$44.8 million in 2024. • Capital expenditures of $38.7 million. 2026 Outlook & "
    "Forward-Looking Information • While we are navigating evolving tariff structures, we expect "
    "continued revenue growth in 2026 • We are targeting a strong gross margin position."
)


def test_release_parse_mvst_fy25() -> None:
    """FY2025 pins: adj EBITDA +44.7 (period 2025, NOT the 'compared to … 2024' clause), GAAP gross
    margin 28.6, the $32.5M ESS impairment, and a QUALITATIVE 2026 outlook (named, no number)."""
    ex = rp.parse_release(_MVST_FY25, source_ref=_SRC)
    ebitda = _by(ex.reconciliation, metric="adjusted ebitda")
    assert ebitda is not None and ebitda.value == 44.7 and ebitda.period == "2025"
    gm = _by(ex.reconciliation, metric="gross margin")
    assert gm is not None and gm.value == 28.6
    assert len(ex.one_offs) == 1
    assert ex.one_offs[0].amount == 32.5 and "ESS" in ex.one_offs[0].description
    rev = _by(ex.guidance, metric="revenue")
    assert rev is not None and rev.qualitative and rev.low is None and rev.period == "2026"


_MVST_Q1 = (
    "Exhibit 99.1 Microvast Reports First Quarter 2026 Financial Results • Net loss of $23.0 "
    "million, compared to net profit of $61.8 million in Q1 2025. Non-GAAP adjusted net loss was "
    "$14.6 million, compared to non-GAAP adjusted net profit of $19.3 million in Q1 2025. • "
    "Non-GAAP adjusted EBITDA of negative $5.5 million in Q1 2026, compared to non-GAAP adjusted "
    "EBITDA of $28.5 million in Q1 2025."
)


def test_release_parse_mvst_q1_26() -> None:
    """Q1-26 pins: adj EBITDA −5.5 and adj net loss −14.6 ('was $14.6 million', sign from 'loss');
    the 'compared to … Q1 2025' comparisons ($19.3M profit, $28.5M) are NOT taken as current."""
    ex = rp.parse_release(_MVST_Q1, source_ref=_SRC)
    ebitda = _by(ex.reconciliation, metric="adjusted ebitda", period="Q1 2026")
    assert ebitda is not None and ebitda.value == -5.5
    ni = _by(ex.reconciliation, metric="adjusted net income", period="Q1 2026")
    assert ni is not None and ni.value == -14.6  # a NET LOSS ⇒ negative, from 'was $14.6 million'
    # the prior-year-Q comparison is captured DISTINCTLY (period-labeled, never conflated) — this is
    # the LTM input: LTM adj EBITDA = FY 44.7 − prior-Q 28.5 + current-Q (−5.5) = 10.7 → the 18.7x.
    prior = _by(ex.reconciliation, metric="adjusted ebitda", period="Q1 2025")
    assert prior is not None and prior.value == 28.5


_VRRM_AVIS = (
    "Exhibit 99.1 Verra Mobility Corporation Receives Termination of Agreement Notice From Avis "
    "Budget Group. The Company expects the termination to reduce Commercial Services’ 2026 "
    "annualized revenue by approximately $135 million to $145 million and 2026 annualized segment "
    "profit by approximately $120 million to $125 million, before taking into account expected "
    "cost reduction initiatives. The Company revised its financial outlook for 2026 to the "
    "following: • Total Revenue of $985 million to $995 million • Adjusted EBITDA of $380 million "
    "to $385 million • Adjusted EPS of $1.19 to $1.25 • Free Cash Flow of $140 million to $150 "
    "million."
)


def test_release_parse_vrrm_avis() -> None:
    """VRRM Avis pins: the event-impact quantifications (revenue reduce 135–145, segment profit
    reduce 120–125, 2026 annualized) AND the revised guide (revenue 985–995, adj EBITDA 380–385)."""
    ex = rp.parse_release(_VRRM_AVIS, source_ref=_SRC)
    rev_i = _by(ex.event_impacts, metric="revenue")
    assert rev_i is not None and rev_i.effect == "reduce"
    assert (rev_i.low, rev_i.high) == (135.0, 145.0)
    seg_i = _by(ex.event_impacts, metric="segment profit")
    assert seg_i is not None and (seg_i.low, seg_i.high) == (120.0, 125.0)
    rev_g = _by(ex.guidance, metric="revenue")
    assert rev_g is not None and not rev_g.qualitative and (rev_g.low, rev_g.high) == (985.0, 995.0)
    eb_g = _by(ex.guidance, metric="adjusted ebitda")
    assert eb_g is not None and (eb_g.low, eb_g.high) == (380.0, 385.0)


def test_release_parse_fail_loud_no_pattern() -> None:
    """A release with none of the anchored patterns fails LOUD: qa_flags name the misses and NO
    value is fabricated (the PR-2 lesson — a miss is UNKNOWN, never an analyst caveat)."""
    ex = rp.parse_release("The company issued a press release with no structured guidance today.",
                          source_ref=_SRC)
    assert ex.reconciliation == [] and ex.guidance == [] and ex.event_impacts == []
    assert ex.one_offs == [] and any("no anchored pattern matched" in f for f in ex.qa_flags)


# --- Ex-99.1 discovery: EDGAR's SGML TYPE leads, the filename guess is the fallback ---------------
# REAL filenames observed 2026-07-22 across every 2.02/8.01 8-K of the eleven committed names.
_EX991_REAL_NAMES = (
    "aort-2025x8k063025ex991.htm", "form8k-ex991.htm", "ex991nov25sharerepurchasepr.htm",
    "ex99-1.htm", "it-12312025xex991.htm", "it-09302025xex991_gdm.htm",
    "mvst2026q1ex991earningspre.htm", "vitl-ex99_1.htm", "d123116dex991.htm", "vrrm-ex99_1.htm",
    # the five conventions the filename rule NEVER matched (24 of 53 releases lost)
    "brbrexh991-q12026earningsr.htm", "exhibit991-pressrelease.htm", "exhibit991q22026.htm",
    "exhibit991pressreleaseofnc.htm", "a991_pressreleasexq2x2026.htm",
    "exhibit99_q1x2026.htm",  # EPAM — its only '1' comes from "q1"; no filename rule can win here
)


class _FakeHttp:
    """Minimal CachedHttp stand-in — records calls, serves canned header/index payloads."""

    def __init__(self, header_text: str | None, index_names: list[str] | None = None) -> None:
        self._header, self._names, self.calls = header_text, index_names or [], []

    def get_text(self, url: str, **_kw: object) -> str:
        self.calls.append(url)
        if self._header is None:
            raise HttpError("no header")
        return self._header

    def get_json(self, url: str, **_kw: object) -> dict[str, object]:
        self.calls.append(url)
        return {"directory": {"item": [{"name": n} for n in self._names]}}


def _headers_html(pairs: list[tuple[str, str]]) -> str:
    """The -index-headers page as EDGAR serves it: SGML tags HTML-ESCAPED."""
    body = "".join(
        f"&lt;DOCUMENT&gt; &lt;TYPE&gt;{ty} &lt;SEQUENCE&gt;{i} &lt;FILENAME&gt;{fn} "
        f"&lt;DESCRIPTION&gt;{ty} &lt;/DOCUMENT&gt;"
        for i, (ty, fn) in enumerate(pairs, start=1)
    )
    return f"<html><body><pre>&lt;SEC-HEADER&gt;{body}</pre></body></html>"


def test_ex991_urls_prefer_the_sgml_type_over_the_filename() -> None:
    """The authoritative path: EDGAR types the exhibit, so a press release is found REGARDLESS of
    its filename — including EPAM's 'exhibit99_q1x2026.htm', which no filename rule can classify
    (its '1' is the quarter). EX-99.2 in the same filing is never picked up."""
    http = _FakeHttp(_headers_html([
        ("8-K", "epam-20260507.htm"),
        ("EX-99.1", "exhibit99_q1x2026.htm"),
        ("EX-99.2", "someother.htm"),
    ]))
    urls = rp.exhibit_991_urls(typing.cast(CachedHttp, http), "0001352010", "0001352010-26-000026")
    assert len(urls) == 1 and urls[0].endswith("/exhibit99_q1x2026.htm")
    assert not rp._is_ex991("exhibit99_q1x2026.htm"), "the filename rule alone would have missed it"


def test_ex991_urls_return_every_furnished_release_and_reject_neighbours() -> None:
    """A filing can furnish more than one 99.1; 99.10/99.11 are DIFFERENT exhibits, and a
    non-text document is never fetched as prose."""
    http = _FakeHttp(_headers_html([
        ("EX-99.1", "a991_pressreleasexq2x2026.htm"),
        ("EX-99.1", "second-release.htm"),
        ("EX-99.10", "ex9910.htm"),
        ("EX-99.11", "ex9911.htm"),
        ("EX-99.1", "deck.pdf"),
    ]))
    urls = rp.exhibit_991_urls(typing.cast(CachedHttp, http), "0001702744", "0001702744-26-000010")
    assert [u.rsplit("/", 1)[1] for u in urls] == [
        "a991_pressreleasexq2x2026.htm", "second-release.htm"]


def test_ex991_urls_fall_back_to_the_filename_when_the_header_is_unreadable() -> None:
    """Header unreachable → the filename guess still finds the conventionally-named exhibit
    (degrade, never crash); a filing that furnishes none returns []."""
    http = _FakeHttp(None, index_names=["it-12312025xex991.htm", "it-20260129.htm"])
    urls = rp.exhibit_991_urls(typing.cast(CachedHttp, http), "0000749251", "0000749251-26-000028")
    assert len(urls) == 1 and urls[0].endswith("/it-12312025xex991.htm")
    empty = _FakeHttp(None, index_names=["primary-doc.htm", "FilingSummary.xml"])
    assert rp.exhibit_991_urls(typing.cast(CachedHttp, empty), "1", "0-0-0") == []


def test_sgml_detection_covers_every_real_filename_the_regex_missed() -> None:
    """The full observed corpus: TYPE-based discovery finds all of them, and the filename rule is
    measurably weaker — the gap this change closes."""
    http = _FakeHttp(_headers_html([("EX-99.1", n) for n in _EX991_REAL_NAMES]))
    urls = rp.exhibit_991_urls(typing.cast(CachedHttp, http), "1", "0-0-0")
    assert len(urls) == len(_EX991_REAL_NAMES), "TYPE lookup must find every real press release"
    by_name = sum(1 for n in _EX991_REAL_NAMES if rp._is_ex991(n))
    assert by_name < len(_EX991_REAL_NAMES), "the filename rule is a strict subset (the bug)"


# --- parser COVERAGE: verbatim sentences from the real releases the locator fix recovered ---------
# Each is the exact phrasing that yielded NOTHING before (recovering the document is not the same
# as reading it). Frozen strings — no network.

def test_recon_tolerates_footnote_markers_and_the_non_gaap_phrasing() -> None:
    """BellRing footnotes its non-GAAP measure ('Adjusted EBITDA* of $53.8 million') and the
    un-tolerated '*' dropped the WHOLE release; EPAM/Concentrix never write "adjusted" at all
    ('Non-GAAP Diluted EPS of $3.26'). Both are the same fact in different house style."""
    r = rp.parse_release("BellRing reported Adjusted EBITDA* of $53.8 million for the quarter.",
                         source_ref=_SRC)
    assert [(v.metric, v.value) for v in r.reconciliation] == [("adjusted ebitda", 53.8)]
    r2 = rp.parse_release("EPAM Reports Non-GAAP Diluted EPS of $3.26, up year-over-year.",
                          source_ref=_SRC)
    assert [(v.metric, v.value) for v in r2.reconciliation] == [("adjusted eps", 3.26)]


def test_one_off_covers_the_generic_nouns_but_needs_a_qualifier() -> None:
    """The one-off IS usually the reason for the gap, and filers write 'charge'/'costs'/'expenses'
    far more often than 'impairment'. A qualifier is REQUIRED so routine operating lines are never
    promoted to a discrete item."""
    r = rp.parse_release(
        "Results were impacted by the current year $11.3 million inventory-related charge.",
        source_ref=_SRC)
    assert [(o.amount, "inventory-related charge" in o.description) for o in r.one_offs] \
        == [(11.3, True)]
    r2 = rp.parse_release("Excluding $4.5 million in restructuring costs for the period.",
                          source_ref=_SRC)
    assert [o.amount for o in r2.one_offs] == [4.5]
    # ⊖ routine operating lines are NOT one-offs (no qualifier before the generic noun)
    for routine in ("Cost of goods sold was $210.0 million for the quarter.",
                    "Interest expense of $12.4 million was recorded.",
                    "Selling expenses of $88.0 million in the period."):
        assert rp.parse_release(routine, source_ref=_SRC).one_offs == [], routine


def test_one_off_reports_each_item_once_and_skips_prior_year_comparatives() -> None:
    """A release states the same charge in the highlights and again per segment, at different
    roundings — eight rows for one fact. And it restates LAST year's item beside this year's;
    attributing a year-old expense to today's gap-down would be a false cause."""
    text = ("Highlights: a pre-tax $11 million inventory-related charge. "
            "Segment results were impacted by the current year $11.3 million inventory-related "
            "charge associated with a third-party supplied ingredient. "
            "Adjusted EBITDA included, for the prior year period, integration expenses of "
            "$0.2 million.")
    offs = rp.parse_release(text, source_ref=_SRC).one_offs
    assert len(offs) == 1, [o.description for o in offs]
    assert offs[0].amount == 11.3, "the most precise mention of the item wins the rounding tie"
    assert "0.2" not in str(offs[0].amount)


def test_guidance_reads_filer_metric_names_range_words_and_scales_billions() -> None:
    """'net sales' / 'total revenues' are how these filers guide, the range is written 'to', 'and'
    or a bare hyphen, and Concentrix guides in BILLIONS while everyone else uses millions — an
    unscaled 2.465 would read as $2.5M beside VRRM's 985.0 ($M)."""
    g = rp.parse_release(
        "Updated fiscal year 2026 net sales outlook of $2.325-$2.365 billion and "
        "Adjusted EBITDA* outlook of $315-$335 million.", source_ref=_SRC).guidance
    by = {x.metric: (x.low, x.high) for x in g}
    assert by["net sales"] == (2325.0, 2365.0), "billions must normalise to $M"
    assert by["adjusted ebitda"] == (315.0, 335.0)
    g2 = rp.parse_release(
        "Total revenues expected to range between $157.75 million and $159.75 million.",
        source_ref=_SRC).guidance
    # 'Total revenues' normalises to the canonical 'revenue' (nCino's phrasing, one metric key)
    assert [(x.metric, x.low, x.high) for x in g2] == [("revenue", 157.75, 159.75)]


def test_one_off_dedup_is_amount_aware_and_the_prior_year_guard_is_sentence_bounded() -> None:
    """(review fixes) Two failure modes of the dedup/exclusion pair, each found by stress-testing
    the widened extractor rather than by a live release:

    1. Keying on the NOUN PHRASE alone collapsed two genuinely different charges — $12.0M
       European-footprint and $30.0M Asia-exit restructuring both read "restructuring charges rel…"
       — and silently dropped the smaller. Distinctness needs the amount too; only a NEAR-equal
       amount means one item restated at a different rounding.
    2. A fixed character look-back reached across a sentence boundary and killed a current-period
       charge because the PRECEDING sentence mentioned last year. The window is bounded by the
       sentence, so a genuine in-sentence comparative is still excluded."""
    two = rp.parse_release(
        "Results included $12.0 million of restructuring charges related to the European "
        "footprint, and $30.0 million of restructuring charges related to the Asia exit.",
        source_ref=_SRC).one_offs
    assert sorted(o.amount for o in two) == [12.0, 30.0], "distinct charges must both survive"

    one = rp.parse_release(
        "Highlights: a pre-tax $11 million inventory-related charge. Segment results were impacted "
        "by the current year $11.3 million inventory-related charge associated with a supplier.",
        source_ref=_SRC).one_offs
    assert [o.amount for o in one] == [11.3], "one item at two roundings is ONE row, most precise"

    kept = rp.parse_release(
        "Compared with the prior year period, results improved. The quarter included a "
        "$25.0 million impairment charge on the Digital unit.", source_ref=_SRC).one_offs
    assert [o.amount for o in kept] == [25.0], "a prior-year mention in a PRIOR sentence must not "\
        "suppress this period's charge"

    dropped = rp.parse_release(
        "Adjusted EBITDA included, for the prior year period, integration expenses of "
        "$0.2 million.", source_ref=_SRC).one_offs
    assert dropped == [], "an in-sentence prior-year comparative is still not this period's cause"


def test_recon_requires_currency_evidence_and_never_reads_a_ratio_as_an_amount() -> None:
    """(fabrication guard) A margin is not an amount. EPAM states 'non-GAAP income from operations
    was 16.3% of revenues'; the widened metric list matched it and stored 16.3, which rendered as
    '$16.3M' against a true ~$230M on $1.4B revenue — a decision figure wrong by ~14x.

    An amount must therefore CARRY its currency: a '$' before the number, or an explicit
    million/billion after it. A bare number, and any number trailed by '%', is not this
    extractor's fact — honest absence beats a fabricated magnitude."""
    # ⊖ the ratio that caused it — and any bare, unqualified number
    for ratio in ("Non-GAAP Income from Operations was 16.3% of revenues.",
                  "non-GAAP income from operations was 14.3% of revenues, up 120bps.",
                  "Adjusted EBITDA was 22.5% of sales.",
                  "Adjusted EBITDA of 53.8."):
        assert rp.parse_release(ratio, source_ref=_SRC).reconciliation == [], ratio
    # ⊕ every legitimate currency shape still parses
    cases = {
        "Adjusted EBITDA* of $53.8 million.": ("adjusted ebitda", 53.8),
        "Non-GAAP Diluted EPS of $3.26, up.": ("adjusted eps", 3.26),
        "Non-GAAP adjusted EBITDA of negative $5.5 million.": ("adjusted ebitda", -5.5),
        "Adjusted EBITDA of 57 million.": ("adjusted ebitda", 57.0),  # unit, no $ sign
    }
    for text, want in cases.items():
        got = [(v.metric, v.value) for v in rp.parse_release(text, source_ref=_SRC).reconciliation]
        assert got == [want], f"{text} → {got}"


def test_committed_dossiers_carry_no_ratio_as_a_currency_amount() -> None:
    """(committed-artifact invariant) Every stored CURRENCY value must show currency evidence in
    its own verbatim — a '$' before it, or a million/billion after it.

    Deliberately NOT "the verbatim contains a %": EPAM's bad row read
    '…non-GAAP income from operations was 14.3' — the window ended before the '%', so a
    percent-scan passes it while the value is still a ratio. The invariant has to assert what a
    currency amount MUST look like, not guess at what a bad one happens to contain."""
    import json
    import re as _re
    from pathlib import Path
    currency = {"adjusted ebitda", "adjusted operating income", "adjusted net income",
                "adjusted eps"}
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        for rel in ((json.loads(p.read_text())["mechanical"].get("primary_source") or {})
                    .get("releases") or []):
            for v in (rel.get("reconciliation") or []):
                if v["metric"] not in currency:
                    continue
                # match the magnitude AS THE FILER WROTE IT: a stored 59.0 comes from "$59
                # million", so an integral value must not be searched for as "59.0".
                a = abs(v["value"])
                vb = str(v.get("verbatim") or "")
                mag = _re.escape(str(int(a)) if a == int(a) else str(a))
                has_currency = _re.search(rf"\$\s*{mag}", vb) or _re.search(
                    rf"{mag}\s*(?:million|billion)", vb, _re.I)
                assert has_currency, (
                    f"{p.parent.name}: {v['metric']}={v['value']} has no currency evidence "
                    f"in its source — …{vb[-70:]!r}")


def test_recon_captures_the_direction_stated_beside_the_level() -> None:
    """A gap-down is about the DELTA, not the level: '$230.0M' alone cannot explain why a stock
    fell. The release states the change in the same sentence, so it is captured and rendered.
    Verbatim forms observed across the five recovered releases."""
    cases = {
        "Non-GAAP income from operations was $230.0 million, an increase of $21.8 million, "
        "or 10.5%, compared to $208.2 million.":
            ("adjusted operating income", 230.0, "+$21.8 million"),
        "Adjusted EBITDA of $55.5 million decreased 18.4% versus the year ago period.":
            ("adjusted ebitda", 55.5, "-18.4%"),
        "Non-GAAP Diluted EPS of $3.26, an increase of 14.8%.": ("adjusted eps", 3.26, "+14.8%"),
    }
    for text, (metric, value, change) in cases.items():
        got = [(v.metric, v.value, v.change)
               for v in rp.parse_release(text, source_ref=_SRC).reconciliation]
        assert (metric, value, change) in got, f"{text[:50]} → {got}"
    # a level with NO stated change carries None — never an invented direction
    plain = rp.parse_release("Adjusted EBITDA* of $53.8 million.", source_ref=_SRC).reconciliation
    assert [v.change for v in plain] == [None]


def test_change_never_borrows_a_delta_from_a_neighbouring_metric() -> None:
    """The change must belong to ITS value: the window stops at the sentence/bullet boundary, so a
    later metric's delta is never attached to an earlier one."""
    text = ("• Adjusted EBITDA of $55.5 million • Adjusted EPS of $0.45, an increase of 14.8%")
    rows = {v.metric: v.change for v in rp.parse_release(text, source_ref=_SRC).reconciliation}
    assert rows.get("adjusted ebitda") is None, "EBITDA must not borrow the EPS delta"
    assert rows.get("adjusted eps") == "+14.8%"


def test_growth_rate_guidance_is_a_real_range_not_a_qualitative_marker() -> None:
    """EPAM guides 'the year-over-year revenue growth rate to be in the range of 4.5% to 7.5%'.
    The dollar-range pattern cannot see a RATE, so it fell through to the QUALITATIVE marker —
    which asserts the company said nothing when it gave the most decision-relevant number in the
    release. A rate guide is a number, carried with unit='%'."""
    g = rp.parse_release(
        "2026 Outlook. The Company expects the year-over-year revenue growth rate to be in the "
        "range of 4.5% to 7.5% for 2026.", source_ref=_SRC).guidance
    assert [(x.metric, x.low, x.high, x.unit, x.qualitative) for x in g] == \
        [("revenue", 4.5, 7.5, "%", False)]
    # a genuinely number-free outlook is STILL qualitative — the honest-absence path is intact
    q = rp.parse_release(
        "2026 Outlook. The Company expects continued revenue growth in the coming year.",
        source_ref=_SRC).guidance
    assert all(x.qualitative for x in q) and all(x.low is None for x in q)


def test_release_period_handles_fiscal_year_phrasing() -> None:
    """BellRing dates its release 'Second Quarter of Fiscal Year 2026'; the FY words between
    'quarter' and the year must not push _release_period to the bare-year fallback (which
    mislabelled the quarterly figures as '2026')."""
    assert rp._release_period("Reports Results for the Second Quarter of Fiscal Year 2026.") \
        == "Q2 2026"
    assert rp._release_period("Reports Fourth Quarter of 2025 Results.") == "Q4 2025"
    assert rp._release_period("Reports First Quarter Fiscal 2027 Results.") == "Q1 2027"
    # a pure full-year release still reads the year
    assert rp._release_period("Reports Full Year 2025 Financial Results.") == "2025"


def test_one_off_collapses_the_same_item_at_two_scopes_but_keeps_distinct_qualifiers() -> None:
    """Three behaviours that must hold together:

    - SAME item, two scopes (SMPL's OWYN integration expense, $3.9M for the quarter and $6.5M YTD,
      both worded identically) → ONE row, the first (quarter);
    - DIFFERENT qualifier ($12M European vs $30M Asia restructuring) → two rows;
    - the description never dangles at a second item ('restructuring costs, integration expenses
      of' → 'restructuring costs')."""
    owyn = (
        "Excluding $3.9 million of one-time OWYN integration expenses in the current year period, "
        "gross margin was 32.8%. Excluding $6.5 million of one-time OWYN integration expenses in "
        "the current year period, gross margin was 32.9%.")
    got = rp.parse_release(owyn, source_ref=_SRC).one_offs
    assert [o.amount for o in got] == [3.9], f"same item two scopes → one row: {got}"

    distinct = ("$12.0 million of restructuring charges related to the European footprint, and "
                "$30.0 million of restructuring charges related to the Asia exit.")
    assert sorted(o.amount for o in rp.parse_release(distinct, source_ref=_SRC).one_offs) \
        == [12.0, 30.0]

    dangling = "Excluding for the current period $4.5 million in restructuring costs, integration."
    off = rp.parse_release(dangling, source_ref=_SRC).one_offs
    assert [o.description for o in off] == ["restructuring costs"], off
