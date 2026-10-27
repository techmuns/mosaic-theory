"""THE RELEASE SOURCE of the data-quality scorecard (`vinci.quality.sources.release`) — pinned on
REAL stored rows, at two layers.

* FROZEN FIXTURES (tests/fixtures/release_quality/): the stored release and covenant rows of 13
  pages, read out of git — five at dd85adf5, the commit BEFORE #778 fixed the parser's scale and
  period defects, and eight at 56500bb1 — and a slice of each filer's XBRL companyfacts fetched
  2026-10-27 (the four tags the checks read, periods from 2023). Every check is shown to fire on a
  failure that was real: VRRM's "$38" adjusted EBITDA, Visa's "Other revenue of $1.5 billion" filed
  as its revenue, Nike's quarterly margins filed under bare years, nCino's quarterly revenue guides
  under annual labels, and the covenant rates their own quotes do not state. EDGAR data is public.
* THE LIVE CORPUS (the committed pages): invariants only — every page is scored, and the
  committed snapshot carries counts and statuses, never a figure.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci.quality import core
from vinci.quality.core import CONFIRMED, DIFFERS_STATED, DIFFERS_UNEXPLAINED, UNCHECKED
from vinci.quality.sources import release as src

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "release_quality"
PAGES: dict[str, Any] = json.loads((FIX / "pages.json").read_text())
FACTS: dict[str, Any] = json.loads((FIX / "companyfacts.json").read_text())


def _page(key: str, *, facts: bool = True) -> src.Page:
    p = PAGES[key]
    return src.Page(p["ticker"], p["releases"], p["covenants"],
                  FACTS[p["ticker"]] if facts else None)


def _counts(check: str, key: str) -> dict[str, int]:
    r = next(c for c in src.CHECKS if c.id == check).run(_page(key))
    assert r.not_run is None and r.not_applicable is None, r
    return {k: v for k, v in r.counts.items() if v}


def _only(key: str, keep: Any) -> src.Page:
    """The page with only the rows ``keep(kind, row)`` admits — one real row under test."""
    p = PAGES[key]
    rels = [{**r, **{k: [x for x in r[k] if keep(k, x)] for k in ("reconciliation", "guidance",
                                                                  "one_offs", "event_impacts")}}
            for r in p["releases"]]
    return src.Page(p["ticker"], rels, [c for c in p["covenants"] if keep("covenant", c)],
                  FACTS[p["ticker"]])


# --- revenue_vs_xbrl ----------------------------------------------------------------------------

def test_reported_revenue_agrees_with_the_filers_xbrl() -> None:
    """POSITIVE: Concentrix's six revenue actuals, quarters and their prior-year comparisons."""
    assert _counts("revenue_vs_xbrl", "CNXC@56500bb1") == {CONFIRMED: 6}


def test_a_sub_line_filed_as_revenue_differs() -> None:
    """NEGATIVE, the real pre-#778 row: Visa's "Other revenue of $1.3 billion" stored as its revenue
    (and unscaled, 1.3). Its fiscal Q3 2026 has no 10-Q in the facts, so it is unchecked."""
    assert _counts("revenue_vs_xbrl", "V@dd85adf5") == {DIFFERS_UNEXPLAINED: 2, UNCHECKED: 1}


def _one_revenue_row(value: float, period: str = "Q3 2026") -> src.Page:
    p = PAGES["CNXC@56500bb1"]
    def mine(x: dict[str, Any]) -> bool:
        return bool(x["period"] == period and x["metric"] == "revenue")
    rel = next(r for r in p["releases"] if any(mine(x) for x in r["reconciliation"]))
    row = next(x for x in rel["reconciliation"] if mine(x))
    return src.Page("CNXC", [{**rel, "reconciliation": [{**row, "value": value}]}], [],
                  FACTS["CNXC"])


def test_the_revenue_tolerance_is_statement_recons_half_percent() -> None:
    """EDGE, on Concentrix's real Q3 2026 row ($2,453.7M; XBRL $2,453.679M): 0.4% away agrees,
    0.6% away differs (statement_recon.DIFFERENT_SHARE)."""
    assert src._revenue_vs_xbrl(_one_revenue_row(2453.7 * 1.004)).counts == {CONFIRMED: 1}
    assert src._revenue_vs_xbrl(_one_revenue_row(2453.7 * 1.006)).counts == {DIFFERS_UNEXPLAINED: 1}


def test_a_figure_another_filing_carries_is_a_stated_difference() -> None:
    """A RECAST, mutated into Concentrix's real facts: the 10-Q filed after the release restates
    Q3 2025 while the original 10-Q still carries the release's $2,483.3M — the difference names
    its reason, the earlier filing."""
    facts = json.loads(json.dumps(FACTS["CNXC"]))
    for unit in facts["facts"]["us-gaap"][
            "RevenueFromContractWithCustomerExcludingAssessedTax"]["units"].values():
        for row in unit:
            if row["end"] == "2025-08-31" and row["filed"] == "2026-10-07" and row.get(
                    "start") == "2025-06-01":
                row["val"] = 2_400_000_000
    page = _one_revenue_row(2483.3, "Q3 2025")
    got = src._revenue_vs_xbrl(src.Page("CNXC", page.releases, [], facts)).counts
    assert got == {DIFFERS_STATED: 1}, got


def test_a_fiscal_calendar_that_does_not_tile_places_nothing() -> None:
    """fuboTV moved its fiscal year: its fiscal 2025 and first quarter of 2026 both end 2025-12-31.
    A zero-day quarter once read a revenue of $0 — it is unchecked, never a difference."""
    cal = src._calendar(FACTS["FUBO"])
    assert src._place(cal, "Q1 2026") is None


# --- gross_margin_vs_xbrl -----------------------------------------------------------------------

def test_a_gross_margin_agrees_with_gross_profit_over_revenue() -> None:
    assert _counts("gross_margin_vs_xbrl", "SMPL@56500bb1") == {CONFIRMED: 5}


def test_a_quarters_margin_filed_under_a_year_differs() -> None:
    """NEGATIVE, the real pre-#778 rows: Nike's quarterly gross margins 49.2% / 40.2% / 40.6% filed
    as 2025 / 2025 / 2024 — set against those fiscal YEARS, all three differ."""
    assert _counts("gross_margin_vs_xbrl", "NKE@dd85adf5") == {DIFFERS_UNEXPLAINED: 3}


def test_the_margin_tolerance_is_a_tenth_of_a_point() -> None:
    """EDGE, on Simply Good's real rows: 0.09 point from gross profit ÷ revenue agrees, 0.11
    differs (release.MARGIN_TOL_PTS)."""
    p = _page("SMPL@56500bb1")
    rel = next(r for r in p.releases if any(x["metric"] == "gross margin"
                                            for x in r["reconciliation"]))
    row = next(x for x in rel["reconciliation"] if x["metric"] == "gross margin")
    cal = src._calendar(p.facts)
    _fp, _y, start, end = src._place(cal, row["period"])
    gp = src._governing(src._by_tag(p.facts, ("GrossProfit",), start, end)[0], src._filed(rel))
    rev = src._governing(src._by_tag(p.facts, src.CONCEPT_ALIASES["revenue"], start, end)[0],
                       src._filed(rel))
    implied = 100.0 * gp / rev
    for off, want in ((0.09, CONFIRMED), (0.11, DIFFERS_UNEXPLAINED)):
        one = src.Page("SMPL", [{**rel, "reconciliation": [{**row, "value": implied + off}]}], [],
                     p.facts)
        assert src._gross_margin_vs_xbrl(one).counts == {want: 1}, off


# --- guide_scale_vs_xbrl ------------------------------------------------------------------------

def test_a_revenue_guide_sits_within_twice_the_year_before() -> None:
    assert _counts("guide_scale_vs_xbrl", "AMZN@56500bb1") == {CONFIRMED: 2}


def test_a_quarterly_guide_under_an_annual_label_differs() -> None:
    """NEGATIVE, LIVE on the committed page: nCino's five quarterly revenue guides ($142–160M)
    labelled "2025"/"2026" — set against its ~$590M fiscal year, each reads about a quarter."""
    assert _counts("guide_scale_vs_xbrl", "NCNO@56500bb1") == {DIFFERS_UNEXPLAINED: 5}


def test_billions_read_as_millions_differ() -> None:
    """NEGATIVE, a mutation of Amazon's real Q3 2026 guide into the 2026-08-12 defect (the trailing
    'billion' dropped): 197.0–202.0 against a $180bn quarter reads ~0.001."""
    p = _page("AMZN@56500bb1")
    rels = [{**r, "guidance": [{**g, "low": g["low"] / 1000, "high": g["high"] / 1000}
                               for g in r["guidance"]]} for r in p.releases]
    r = src._guide_scale_vs_xbrl(src.Page(p.ticker, rels, [], p.facts))
    assert r.counts == {DIFFERS_UNEXPLAINED: 2}


def test_the_scale_band_is_a_factor_of_two_either_way() -> None:
    """EDGE, on Amazon's real Q3 2026 guide against its Q3 2025 net sales: a midpoint at 1.99x
    agrees, 2.01x and 1/2.01x differ (release.SCALE_BAND)."""
    p = _page("AMZN@56500bb1")
    rel = next(r for r in p.releases if r["filed"] == "2026-07-30")
    cal = src._calendar(p.facts)
    _fp, _y, start, end = src._place(cal, "Q3 2025")
    base = max(src._by_tag(p.facts, src.CONCEPT_ALIASES["revenue"], start, end)[0])[1]
    g = next(g for g in rel["guidance"] if g["metric"] == "net sales")
    for k, want in ((1.99, CONFIRMED), (2.01, DIFFERS_UNEXPLAINED),
                    (1 / 2.01, DIFFERS_UNEXPLAINED)):
        moved = {**g, "low": base * k, "high": base * k}
        one = src.Page("AMZN", [{**rel, "guidance": [moved]}], [], p.facts)
        assert src._guide_scale_vs_xbrl(one).counts == {want: 1}, k


# --- guide_period_forward -----------------------------------------------------------------------

def test_a_guide_labelled_with_a_future_period_is_forward() -> None:
    assert _counts("guide_period_forward", "TJX@56500bb1") == {CONFIRMED: 14}


def test_a_guide_labelled_with_a_closed_period_differs() -> None:
    """NEGATIVE, LIVE: Simply Good's July-2025 adjusted-EBITDA guide filed as "2024" and its
    October-2025 one as "2025" — fiscal years the filer had already closed."""
    assert _counts("guide_period_forward", "SMPL@56500bb1")[DIFFERS_UNEXPLAINED] == 2


def test_a_guide_with_no_year_is_unchecked_never_confirmed() -> None:
    p = _page("SMPL@56500bb1")
    no_year = [{**r, "guidance": [g for g in r["guidance"] if g["period"] == "next-fy"]}
               for r in p.releases]
    r = src._guide_period_forward(src.Page(p.ticker, no_year, [], p.facts))
    assert set(r.counts) == {UNCHECKED}


# --- figure_in_own_quote ------------------------------------------------------------------------

def test_every_release_figure_is_stated_in_its_own_quote() -> None:
    """POSITIVE: Simply Good's 55 stored release figures, each in its quote at its scale."""
    assert _counts("figure_in_own_quote", "SMPL@56500bb1") == {CONFIRMED: 55}


def test_vrrms_range_made_actual_is_not_in_its_quote_at_its_scale() -> None:
    """NEGATIVE, THE BRIEF'S NAMED FAILURE (docs/records/2026-10-22-release-actuals-at-their-
    scale.md): "$380 million to $385 million" read as an adjusted EBITDA of $38.0M, its quote cut
    to "Adjusted EBITDA of $38". The quote states $38 at no scale; a $M figure is not in it."""
    p = _only("VRRM@dd85adf5", lambda k, x: k == "reconciliation" and x["value"] == 38.0)
    assert src._figure_in_own_quote(p).counts == {DIFFERS_UNEXPLAINED: 1}


def test_unscaled_billions_are_not_in_their_quote() -> None:
    """NEGATIVE, real pre-#778 rows: Uber's "Adjusted EBITDA of $2.5 billion" stored as 2.5 ($M)."""
    p = _only("UBER@dd85adf5", lambda k, x: k == "reconciliation" and x["value"] == 2.5)
    assert src._figure_in_own_quote(p).counts == {DIFFERS_UNEXPLAINED: 1}


def test_a_quote_cut_at_its_cap_before_the_figure_states_why() -> None:
    """EPAM's guide quote reaches the 200-character cap at "$5.430 billion to": its high side is
    not in it, and the page says why — the cap (release_parse.VERBATIM_CAP)."""
    p = _only("EPAM@56500bb1", lambda k, x: k == "guidance" and x.get("high") == 5445.0)
    assert src._figure_in_own_quote(p).counts == {CONFIRMED: 1, DIFFERS_STATED: 1}


def test_a_covenant_rate_stated_in_its_quote_is_confirmed() -> None:
    """POSITIVE: TJX's floor "provided that if the Base Rate shall be less than 1.75%, such rate
    shall be deemed to be 1.75%" carries floor_pct 1.75."""
    p = _only("TJX@56500bb1", lambda k, x: k == "covenant" and x.get("floor_pct") == 1.75)
    assert src._figure_in_own_quote(p).counts == {CONFIRMED: 1}


def test_a_covenant_rate_its_quote_does_not_state_differs() -> None:
    """NEGATIVE, LIVE — item 17's question: a quote PRESENT in its exhibit need not SUPPORT the
    value. Amazon's "…at a rate per annum equal to the LIBO Rate … plus the Applicable Rate"
    carries a margin of 0.5% and a floor of 0 that the quote never states."""
    p = _only("AMZN@56500bb1", lambda k, x: k == "covenant" and x.get("margin_pct") == 0.5)
    assert src._figure_in_own_quote(p).counts == {DIFFERS_UNEXPLAINED: 2}


def test_the_quote_reader_reads_a_figure_at_its_own_scale() -> None:
    from vinci.edgar.release_parse import quoted_figures
    got = {(f.unit, f.value) for f in quoted_figures(
        "between $2.465 to $2.49 billion, EPS of $.97, decline 300 and 350 basis points, 4.250%, "
        "less than zero")}
    assert {("$M", 2490.0), ("$M", 2465.0), ("$", 0.97), ("bps", 350.0), ("bps", 300.0),
            ("%", 4.25), ("%", 0.0)} <= got
    assert ("$M", 2.465) not in got and ("$", 2.49) not in got


# --- what it reads ------------------------------------------------------------------------------

def test_a_page_without_cached_facts_runs_the_quote_check_alone(tmp_path: Path) -> None:
    """The source never fetches: with no SEC cache, every XBRL check is NOT RUN by name and the
    quote check still runs."""
    page = PAGES["CNXC@56500bb1"]
    d = tmp_path / "data" / "dossiers" / "CNXC"
    d.mkdir(parents=True)
    (d / "dossier.json").write_text(json.dumps({"ticker": "CNXC", "cik": page["cik"],
                                                "mechanical": {"primary_source": {
                                                    "releases": page["releases"]}}}))
    corpus = src.load(tmp_path)
    card = core.scorecard(src.SOURCE, corpus, measured_on="2026-10-27", git_head=None,
                          inputs_match_head=None)
    by = {c["id"]: c for c in card["checks"]}
    assert by["revenue_vs_xbrl"]["fleet"]["items_not_run"] == 1
    assert "no XBRL facts" in by["revenue_vs_xbrl"]["not_run"][0]["reason"]
    assert by["figure_in_own_quote"]["fleet"]["items_run"] == 1


def test_no_network_call_is_made(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from vinci.netcache import CachedHttp

    def refuse(*_a: object, **_k: object) -> str:
        raise AssertionError("the release source fetched")
    monkeypatch.setattr(CachedHttp, "_fetch_with_retries", refuse)
    test_a_page_without_cached_facts_runs_the_quote_check_alone(tmp_path)


def test_the_source_is_registered_and_validates() -> None:
    assert core.discover()["release"] is src.SOURCE
    assert {c.id for c in src.CHECKS} == {cid for f in src.FAMILIES for cid in f.checks}


# --- the live corpus: invariants only ------------------------------------------------------------

def test_every_committed_page_is_scored_on_the_committed_facts() -> None:
    """Every page reads; the XBRL checks run wherever the committed companyfacts fixture holds
    the filer, and the quote check runs on every page that stores a quoted figure."""
    def facts(t: str, _cik: str) -> dict[str, Any] | str:
        f = ROOT / "tests" / "fixtures" / "companyfacts" / f"{t}.json"
        return json.loads(f.read_text()) if f.exists() else "no committed fixture"
    corpus = src.read(ROOT, facts=facts)
    card = core.scorecard(src.SOURCE, corpus, measured_on=date.today().isoformat(), git_head=None,
                          inputs_match_head=None)
    pages = list((ROOT / "data" / "dossiers").glob("*/dossier.json"))
    assert card["boundary"]["items"] == len(pages)
    q = next(c for c in card["checks"] if c["id"] == "figure_in_own_quote")["fleet"]
    assert q["units"] > 0 and q["items_run"] + q["items_not_applicable"] == q["items"]


def test_the_committed_snapshot_is_counts_and_statuses_only() -> None:
    """No figure, quote or period label reaches a snapshot: every number in it is a count."""
    snaps = sorted((ROOT / "data" / "snapshots" / "data_quality" / "release").glob("*.json"))
    if not snaps:
        pytest.skip("no release snapshot committed yet")
    card = json.loads(snaps[-1].read_text())
    for c in card["checks"]:
        for row in c["by_name"].values():
            assert all(isinstance(v, int) for k, v in row.items() if k not in ("not_run",
                                                                              "not_applicable"))
    text = snaps[-1].read_text()
    for page in PAGES.values():
        for r in page["releases"]:
            for g in r["guidance"]:
                assert g["verbatim"] not in text


def test_a_scaled_count_is_not_money() -> None:
    """REVIEW FIX: Concentrix's real guide bullet "…assuming approximately 61.2 million diluted
    common shares outstanding" states a COUNT; read as $61.2M it could confirm a mis-scaled
    figure."""
    from vinci.edgar.release_parse import quoted_figures
    got = quoted_figures("Non-GAAP diluted EPS of $2.86 to $2.98, assuming approximately 61.2 "
                         "million diluted common shares outstanding")
    assert ("$M", 61.2) not in {(f.unit, f.value) for f in got}
    assert ("$", 2.98) in {(f.unit, f.value) for f in got}


def test_a_margin_divides_one_filings_figures() -> None:
    """REVIEW FIX: gross profit is set over the revenue its OWN filing states. Mutated into Simply
    Good's real facts: a recast revenue, 20% higher, filed the day after the release and before the
    10-K (the Q4 2025 row: release 2025-10-23, 10-K 2025-10-28). Dividing the 10-K's gross profit by
    the recast would read a margin no filing states."""
    p = _page("SMPL@56500bb1")
    rel = next(r for r in p.releases if any(x["metric"] == "gross margin" and x["period"] ==
                                            "Q4 2025" for x in r["reconciliation"]))
    row = next(x for x in rel["reconciliation"] if x["metric"] == "gross margin")
    one = src.Page("SMPL", [{**rel, "reconciliation": [row]}], [], p.facts)
    assert src._gross_margin_vs_xbrl(one).counts == {CONFIRMED: 1}
    _fp, _y, start, end = src._place(one.calendar, row["period"])
    facts = json.loads(json.dumps(p.facts))
    day_after = (src._filed(rel) + timedelta(days=1)).isoformat()
    for tag in src.CONCEPT_ALIASES["revenue"]:
        for rows in (facts["facts"]["us-gaap"].get(tag) or {}).get("units", {}).values():
            rows += [{**r, "filed": day_after, "val": r["val"] * 1.2} for r in list(rows)
                     if r["end"] == end.isoformat()]
    got = src._gross_margin_vs_xbrl(src.Page("SMPL", one.releases, [], facts)).counts
    assert got == {CONFIRMED: 1}, got
