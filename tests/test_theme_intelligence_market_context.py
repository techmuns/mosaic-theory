"""IS IT PRICED? — the market-context panel (operator, 2026-10-16: "add a clearly labelled 'is it
priced?' market-context panel beside the verdict … evidence for the human, never a model verdict,
and the evidence gates stay as they are").

- The figures are POINT IN TIME: a close after the date, or an EPS filed after it, is never read;
  a figure that cannot be measured is None with why.
- It is DISPLAY ONLY: stored apart from the thesis, labelled on every surface, and the research
  action is the same with or without it (the boundary itself is pinned in
  test_theme_intelligence_isolation.py).

Price series here are HYPOTHETICAL (labelled, deterministic) on the REAL types; the thesis records
are the committed J.P. Morgan fixture's. The real runs (live Polygon and SEC) are in the record.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from tests.theme_intelligence_support import JPM_AS_OF, ingest_jpm, make_pipeline
from vinci.edgar.concepts import ConceptPoint
from vinci.theme_intelligence.cards import (
    MARKET_HYPOTHESES,
    exposure_instruments,
    market_cell,
    market_html,
)
from vinci.theme_intelligence.market import (
    BENCHMARK,
    Closes,
    against,
    consensus_revisions,
    from_high,
    market_context,
    pe_against_history,
    split_sized_moves,
    vs_average,
)
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.schemas import (
    MARKET_LABEL,
    EnrichmentCandidate,
    EnrichmentSet,
    Listing,
    MarketFigure,
    PitStatus,
    ResearchAction,
    ResolutionStatus,
    RunStatus,
    ThesisVersion,
)
from vinci.theme_intelligence.store import MIGRATIONS, Store

AS_OF = date(2026, 2, 9)


def _days(end: date, n: int) -> list[date]:
    """The last `n` weekdays up to `end` — a HYPOTHETICAL trading calendar."""
    out: list[date] = []
    d = end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return out[::-1]


def _ramp(end: date, n: int, start: float = 100.0, step: float = 0.1) -> Closes:
    """HYPOTHETICAL closes rising by `step` a day to `end`."""
    return [(d, start + i * step) for i, d in enumerate(_days(end, n))]


# --- price position ------------------------------------------------------------------------------

def test_the_close_against_its_200_day_average() -> None:
    closes = _ramp(AS_OF, 260)
    f = vs_average(closes, AS_OF)
    last = closes[-200:]
    want = closes[-1][1] / (sum(c for _, c in last) / 200) - 1
    assert f.value == pytest.approx(want)
    assert last[0][0].isoformat() in f.basis and AS_OF.isoformat() in f.basis


def test_a_short_or_stale_series_has_no_200_day_average() -> None:
    """NEGATIVE: 199 closes is not a 200-day average; a last close 10 days old is not today's."""
    assert vs_average(_ramp(AS_OF, 199), AS_OF).value is None
    stale = _ramp(AS_OF - timedelta(days=10), 260)
    f = vs_average(stale, AS_OF)
    assert f.value is None and f.basis.startswith("not held")


def test_the_close_against_its_52_week_high_reads_closes_to_the_date() -> None:
    closes = [(d, 150.0 if i == 100 else 100.0) for i, d in enumerate(_days(AS_OF, 260))]
    f = from_high(closes, AS_OF)
    assert f.value == pytest.approx(100 / 150 - 1) and "150.00" in f.basis
    # NEGATIVE: closes held for only 100 days do not cover the 52 weeks; a higher close OLDER
    # than 52 weeks is not the 52-week high
    assert from_high(closes[-100:], AS_OF).value is None
    older = [(d, 200.0 if i == 120 else c) for i, (d, c) in enumerate(
        [(d, 150.0 if i == 300 else 100.0) for i, d in enumerate(_days(AS_OF, 420))])]
    assert AS_OF - timedelta(days=450) < older[120][0] < AS_OF - timedelta(days=365) < older[300][0]
    assert from_high(older, AS_OF).value == pytest.approx(100 / 150 - 1)


def test_nothing_after_the_date_is_read() -> None:
    """POINT IN TIME: a crash and a new high AFTER the date change no figure as of it."""
    closes = _ramp(AS_OF, 400)
    later = closes + [(AS_OF + timedelta(days=i), x) for i, x in ((1, 10.0), (2, 999.0))]
    bench = _ramp(AS_OF, 400, start=50.0, step=0.01)
    for f in (vs_average, from_high):
        assert f(later, AS_OF) == f(closes, AS_OF)
    assert against(later, bench, AS_OF, 91, "X") == against(closes, bench, AS_OF, 91, "X")


def test_the_return_against_the_benchmark() -> None:
    """A name flat while the benchmark rose 10% over the window is ~10 points behind it."""
    name = [(d, 100.0) for d in _days(AS_OF, 300)]
    days = _days(AS_OF, 300)
    bench = [(d, 100.0 if d <= AS_OF - timedelta(days=91) else 110.0) for d in days]
    f = against(name, bench, AS_OF, 91, "X")
    assert f.value == pytest.approx(-0.10) and "common last bar" in f.basis


# --- P/E against its own history -----------------------------------------------------------------

def _eps(period_end: date, filed: date, value: float) -> ConceptPoint:
    return ConceptPoint(concept="eps_diluted", tag="EarningsPerShareDiluted", unit="USD/shares",
                        value=value, period_start=period_end - timedelta(days=364),
                        period_end=period_end, filed=filed, fy=period_end.year, fp="FY",
                        form="10-K", accession="0000000000-00-000000")


def test_the_pe_reads_only_eps_filed_by_the_date() -> None:
    """POINT IN TIME: a 10-K filed after the date (EPS 10.0) is not read; the one filed before
    (EPS 5.0) is."""
    closes = [(d, 100.0) for d in _days(AS_OF, 480)]
    eps = [_eps(date(2023, 12, 31), date(2024, 2, 1), 5.0),
           _eps(date(2024, 12, 31), date(2025, 2, 1), 5.0),
           _eps(date(2025, 12, 31), AS_OF + timedelta(days=5), 10.0)]
    pe, pct = pe_against_history(closes, eps, AS_OF, "X")
    assert pe.value == pytest.approx(20.0)
    assert pct.value is not None and closes[0][0].isoformat() in pct.basis


def test_a_split_before_the_prices_held_does_not_refuse_their_range() -> None:
    """A 10:1 restatement of periods ending long before the first close held (outside the range
    plus its EPS reach-back) leaves the range buildable — the fund helper's own window rule, on
    the prices held (AMZN and GOOGL, 2026-10-16). NEGATIVE: a restatement INSIDE it refuses."""
    closes = [(d, 100.0) for d in _days(AS_OF, 480)]
    first = closes[0][0]
    now = [_eps(date(2024, 12, 31), date(2025, 2, 1), 5.0),
           _eps(date(2023, 12, 31), date(2024, 2, 1), 4.0)]
    old_split = [_eps(date(2019, 12, 31), date(2020, 2, 1), 30.0),
                 _eps(date(2019, 12, 31), date(2022, 2, 1), 3.0),
                 _eps(date(2020, 12, 31), date(2021, 2, 1), 40.0),
                 _eps(date(2020, 12, 31), date(2022, 2, 1), 4.0)]
    _pe, pct = pe_against_history(closes, now + old_split, AS_OF, "X")
    assert pct.value is not None
    inside = [_eps(date(2024, 12, 31), date(2025, 2, 1), 50.0),
              _eps(date(2024, 12, 31), date(2026, 2, 1), 5.0),
              _eps(date(2023, 12, 31), date(2024, 2, 1), 40.0),
              _eps(date(2023, 12, 31), date(2025, 2, 1), 4.0)]
    assert first - timedelta(days=470) < date(2023, 12, 31)
    _pe, pct = pe_against_history(closes, inside, AS_OF, "X")
    assert pct.value is None and "split" in pct.basis


# --- the context of a real thesis ----------------------------------------------------------------

def _jpm(tmp_path: Path) -> Pipeline:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=JPM_AS_OF)
    ingest_jpm(pipe)
    pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe


def _software(pipe: Pipeline) -> ThesisVersion:
    """The thesis whose ETF the source attaches (the software sell-off)."""
    (v,) = [v for t in pipe.store.theses()
            if (v := pipe.store.thesis_version(t.thesis_id, t.current_version)) is not None
            and any("IGV" in c.name_as_written
                    for c in exposure_instruments(v.content.s05_affected))]
    return v


def _prices(fail: tuple[str, ...] = ()) -> object:
    def get(symbol: str, start: date, end: date) -> Closes:
        if symbol in fail:
            raise RuntimeError(f"HYPOTHETICAL outage for {symbol}")
        return [(d, c) for d, c in _ramp(end, 400, start=50.0 + len(symbol))
                if start <= d <= end]
    return get


def _no_eps(cik: str) -> list[ConceptPoint]:
    return [_eps(date(2025, 12, 31), date(2026, 1, 30), 4.0)]


def test_the_context_prices_what_the_count_takes_and_names_what_it_cannot(
        tmp_path: Path) -> None:
    """The software thesis (committed fixture): its ETF is priced, with no P/E (a fund); its
    index, named with no traded ticker, is a row that says so. Revisions: not held, said."""
    pipe = _jpm(tmp_path)
    v = _software(pipe)
    ctx, errors = market_context(v.content.s05_affected, thesis_id=v.thesis_id,
                                 version=v.version, run_id="R-x", as_of=JPM_AS_OF,
                                 prices=_prices(), eps=_no_eps)  # type: ignore[arg-type]
    assert errors == [] and ctx.label == MARKET_LABEL
    by = {r.name: r for r in ctx.rows}
    igv = next(r for n, r in by.items() if "IGV" in n)
    assert igv.kind == "fund" and igv.ticker == "IGV" and igv.vs_200d.value is not None
    assert igv.pe.value is None and "a fund" in igv.pe.basis
    index = next(r for r in ctx.rows if r.ticker is None)
    assert "no traded ticker" in index.vs_200d.basis and index.last_close is None
    assert "a fund" in igv.revisions.basis and index.revisions.value is None


def test_a_failed_request_is_said_on_its_row_never_filled(tmp_path: Path) -> None:
    """NEGATIVE: an outage for one ticker leaves that row's figures not held and is reported; an
    outage for the benchmark leaves only the relative returns not held."""
    pipe = _jpm(tmp_path)
    v = _software(pipe)
    for fail, row_held, rel_held in ((("IGV",), False, False), ((BENCHMARK,), True, False)):
        ctx, errors = market_context(v.content.s05_affected, thesis_id=v.thesis_id,
                                     version=v.version, run_id="R-x", as_of=JPM_AS_OF,
                                     prices=_prices(fail), eps=_no_eps)  # type: ignore[arg-type]
        igv = next(r for r in ctx.rows if r.ticker == "IGV")
        assert errors and fail[0] in errors[0]
        assert (igv.vs_200d.value is not None) is row_held
        assert (igv.rel_3m.value is not None) is rel_held
        assert igv.rel_3m.basis.startswith("not held")


# --- stored, shown, and never read by the rules --------------------------------------------------

def test_the_step_stores_it_and_every_surface_shows_it_labelled(tmp_path: Path) -> None:
    """End to end: the market step stores one context per active thesis; the desk's thesis page
    shows "Is it priced?" beside the verdict, labelled, with how each figure is measured; the
    card's section 06 and the Markdown record carry it. The research action is unchanged, and a
    reassess after it makes no new version (the rules never read it)."""
    pipe = _jpm(tmp_path)
    before = {t.thesis_id: (t.current_version, pipe.store.thesis_version(
        t.thesis_id, t.current_version).priority.research_action)  # type: ignore[union-attr]
        for t in pipe.store.theses()}
    run, done = pipe.run_market(as_of=JPM_AS_OF, prices=_prices(),  # type: ignore[arg-type]
                                eps=_no_eps)
    assert run.status is RunStatus.SUCCEEDED and len(done) == len(before)
    for tid, (ver, _a) in before.items():
        m = pipe.store.market_context(tid, ver)
        assert m is not None and m.as_of == JPM_AS_OF
    out = Path(write_run_outputs(pipe.store, run.run_id, tmp_path / "out")["dir"])
    for tid in before:
        page = BeautifulSoup((out / "theses" / f"{tid}.html").read_text(), "html.parser")
        panel = next(s for s in page.select("section.panel")
                     if s.h2 is not None and s.h2.get_text() == "Is it priced?")
        text = panel.get_text(" ")
        assert MARKET_LABEL in text and JPM_AS_OF.isoformat() in text
        assert "Revisions: the next fiscal year's EPS consensus" in text
        # beside the verdict: right after the thesis and its Why box, before Who is exposed
        heads = [s.h2.get_text() for s in page.select("section.panel") if s.h2 is not None]
        assert heads.index("Is it priced?") + 1 == heads.index("Who is exposed")
        card = (out / "cards" / f"{tid}.html").read_text()
        assert "Is it priced? — market context" in card and MARKET_LABEL in card
        assert MARKET_LABEL in (out / "cards" / f"{tid}.md").read_text()
    software = next(tid for tid in before if "IGV" in (out / "theses" / f"{tid}.html").read_text())
    page = BeautifulSoup((out / "theses" / f"{software}.html").read_text(), "html.parser")
    assert page.select_one("details.mkth") is not None  # how each figure is measured
    assert re.search(r"[+−]\d+\.\d%", page.select_one("table.mktt").get_text(" "))  # type: ignore[union-attr]
    pipe.run_reassess(as_of=JPM_AS_OF)
    after = {t.thesis_id: (t.current_version, pipe.store.thesis_version(
        t.thesis_id, t.current_version).priority.research_action)  # type: ignore[union-attr]
        for t in pipe.store.theses()}
    assert after == before


def test_a_version_with_no_context_says_so_and_how_to_compute_it(tmp_path: Path) -> None:
    pipe = _jpm(tmp_path)
    run = pipe.store.runs()[-1]
    out = Path(write_run_outputs(pipe.store, run.run_id, tmp_path / "out")["dir"])
    t = pipe.store.theses()[0]
    page = BeautifulSoup((out / "theses" / f"{t.thesis_id}.html").read_text(), "html.parser")
    panel = next(s for s in page.select("section.panel")
                 if s.h2 is not None and s.h2.get_text() == "Is it priced?")
    assert "Not computed for this version" in panel.get_text(" ")
    assert f"market --as-of {run.as_of.isoformat()} --thesis {t.thesis_id}" in panel.get_text(" ")
    card = (out / "cards" / f"{t.thesis_id}.html").read_text()
    assert "Not computed for this version" in card


def test_a_context_written_after_a_run_is_not_shown_as_of_it(tmp_path: Path) -> None:
    """The desk renders a run as the registry held it: a context computed later is not shown on
    that run's pages (the next run's), and the store returns the latest one held at a moment."""
    pipe = _jpm(tmp_path)
    scan = pipe.store.runs()[-1]
    pipe.run_market(as_of=JPM_AS_OF, prices=_prices(), eps=_no_eps)  # type: ignore[arg-type]
    t = pipe.store.theses()[0]
    assert pipe.store.market_context(t.thesis_id, t.current_version,
                                     until=scan.finished_at) is None
    assert pipe.store.market_context(t.thesis_id, t.current_version) is not None
    out = Path(write_run_outputs(pipe.store, scan.run_id, tmp_path / "out")["dir"])
    assert "Not computed for this version" in (out / "theses" / f"{t.thesis_id}.html").read_text()


def test_market_contexts_are_append_only_and_a_v6_registry_migrates(tmp_path: Path) -> None:
    db = tmp_path / "r.db"
    Store(db, migrations=[m for m in MIGRATIONS if m[0] <= 6]).close()
    st = Store(db)
    assert st.schema_version() == 7
    st.close()
    pipe = _jpm(tmp_path / "p")
    pipe.run_market(as_of=JPM_AS_OF, prices=_prices(), eps=_no_eps)  # type: ignore[arg-type]
    conn = pipe.store.conn
    assert conn.execute("SELECT COUNT(*) FROM market_contexts").fetchone()[0] == 3
    for sql in ("DELETE FROM market_contexts", "UPDATE market_contexts SET payload='{}'"):
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            conn.execute(sql)


def test_the_research_action_is_the_same_whatever_the_market_says(tmp_path: Path) -> None:
    """Two registries, the same article: one priced by a market that crashed, one by a market
    that soared. Every thesis's action is the same — and the same as with no context at all."""
    def market(step: float) -> object:
        def get(symbol: str, start: date, end: date) -> Closes:
            return [(d, c) for d, c in _ramp(end, 400, start=100.0, step=step)
                    if start <= d <= end]
        return get

    actions = []
    for i, step in enumerate((None, -0.2, 0.5)):
        pipe = _jpm(tmp_path / str(i))
        if step is not None:
            pipe.run_market(as_of=JPM_AS_OF, prices=market(step),  # type: ignore[arg-type]
                            eps=_no_eps)
            pipe.run_reassess(as_of=JPM_AS_OF)
        actions.append(sorted(pipe.store.thesis_version(t.thesis_id, t.current_version)
                              .priority.research_action.value  # type: ignore[union-attr]
                              for t in pipe.store.theses()))
    assert actions[0] == actions[1] == actions[2]
    assert set(actions[0]) <= {a.value for a in ResearchAction}


# --- consensus revisions: the fund's dossiers, point in time ------------------------------------

FIXTURES = Path(__file__).parent / "fixtures" / "theme_intelligence" / "market"


def test_revisions_are_the_next_years_eps_over_three_months_with_who_revised() -> None:
    """The frozen copy of AMZN's dossier consensus (export on or after 2026-10-06, assembled
    2026-10-09): FY 2027 normalized EPS 9.89 → 10.47 over the 3 months, 21 analysts up, 2 down."""
    f = consensus_revisions("AMZN", date(2026, 10, 14), FIXTURES)
    assert f.value == pytest.approx(10.47 / 9.89 - 1) and f.detail == "21↑ 2↓"
    assert "FY 2027 EPS Normalized" in f.basis and "2026-10-06" in f.basis


@pytest.mark.parametrize(("as_of", "why"), [
    (date(2026, 10, 8), "look ahead"),    # after the floor, before the dossier was assembled
    (date(2026, 10, 1), "look ahead"),    # before the export's own floor
    (date(2026, 11, 20), "days older"),   # 45 days after the export: stale
])
def test_revisions_are_never_read_ahead_or_stale(as_of: date, why: str) -> None:
    f = consensus_revisions("AMZN", as_of, FIXTURES)
    assert f.value is None and why in f.basis


def test_revisions_not_held_are_said(tmp_path: Path) -> None:
    """NEGATIVE: a ticker with no dossier; a next-year line with no positive base."""
    assert "no CIQ consensus held for META" in consensus_revisions(
        "META", date(2026, 10, 14), FIXTURES).basis
    doc = json.loads((FIXTURES / "AMZN" / "dossier.json").read_text())
    for p in doc["forward_consensus"]["paths"]:
        for pt in p["points"]:
            if pt["months_ago"] == 3:
                pt["value"] = -1.0
    (tmp_path / "AMZN").mkdir()
    (tmp_path / "AMZN" / "dossier.json").write_text(json.dumps(doc))
    f = consensus_revisions("AMZN", date(2026, 10, 14), tmp_path)
    assert f.value is None and "no positive" in f.basis


# --- a split-sized move is said on its row --------------------------------------------------------

def test_a_one_day_move_the_size_of_a_split_is_flagged() -> None:
    """Moderna, 2026-08-19: 62.96 → 174.38 in a day — real news or an unadjusted split, and the
    row says to check. NEGATIVE: a 40% day is not split-sized; a jump AFTER the date is not read."""
    days = _days(AS_OF, 60)
    closes = [(d, 63.0 if i < 30 else 174.0) for i, d in enumerate(days)]
    (w,) = split_sized_moves(closes, AS_OF)
    assert "+176%" in w and days[30].isoformat() in w
    assert split_sized_moves([(d, 100.0 if i < 30 else 140.0) for i, d in enumerate(days)],
                             AS_OF) == []
    later = [(d, 100.0) for d in days] + [(AS_OF + timedelta(days=1), 300.0)]
    assert split_sized_moves(later, AS_OF) == []


# --- the companies the thesis implies -------------------------------------------------------------

def _candidate(name: str, ticker: str, *, verified: bool = True,
               foreign: bool = False) -> EnrichmentCandidate:
    pit = PitStatus.VERIFIED if verified else PitStatus.UNVERIFIED
    return EnrichmentCandidate(
        enrichment_id=f"E-{ticker}", thesis_id="TH-x", name=name,
        rationale="[HYPOTHETICAL] the thesis's step reaches its earnings", evidence="s03.1: x",
        resolution_status=ResolutionStatus.LISTED_EQUITY, foreign_filer=foreign,
        listings=(Listing(ticker=ticker, exchange="NASDAQ", pit_status=pit),))


def test_the_companies_the_thesis_implies_are_priced_apart_and_never_counted(
        tmp_path: Path) -> None:
    """End to end: an enrichment set beside the software thesis. Its SEC-verified US company is
    priced in its OWN labelled table on the desk, the card and the Markdown record; an unverified
    listing and a foreign filer are not priced; the count and the action are unchanged."""
    pipe = _jpm(tmp_path)
    v = _software(pipe)
    before = (v.priority.research_action, v.priority.factors)
    with pipe.store.tx():
        pipe.store.add_enrichment(EnrichmentSet(
            set_id="ES-1", thesis_id=v.thesis_id, thesis_version=v.version, run_id="R-x",
            as_of=JPM_AS_OF, created_at=datetime(2026, 2, 9, tzinfo=UTC), model="m",
            prompt_version="p", candidates=(_candidate("Adobe", "ADBE"),
                                            _candidate("Unverified Co", "UNVC", verified=False),
                                            _candidate("Foreign Co", "FRGN", foreign=True))))
    run, _done = pipe.run_market(as_of=JPM_AS_OF, prices=_prices(),  # type: ignore[arg-type]
                                 eps=_no_eps, dossiers=FIXTURES)
    m = pipe.store.market_context(v.thesis_id, v.version)
    assert m is not None and [r.ticker for r in m.hypotheses] == ["ADBE"]
    assert "ADBE" not in [r.ticker for r in m.rows]
    after = pipe.store.thesis_version(v.thesis_id, pipe.store.thesis(v.thesis_id).current_version)  # type: ignore[union-attr]
    assert after is not None and (after.priority.research_action, after.priority.factors) == before
    out = Path(write_run_outputs(pipe.store, run.run_id, tmp_path / "out")["dir"])
    page = BeautifulSoup((out / "theses" / f"{v.thesis_id}.html").read_text(), "html.parser")
    implied = page.select_one("table.mkth2")
    assert implied is not None and "Adobe" in implied.get_text(" ")
    assert MARKET_HYPOTHESES in page.get_text(" ")
    assert MARKET_HYPOTHESES in (out / "cards" / f"{v.thesis_id}.md").read_text()


def test_the_market_contexts_survive_the_state_branch_export(tmp_path: Path) -> None:
    """The Actions run keeps the registry as a JSONL export: the contexts travel with it."""
    pipe = _jpm(tmp_path / "p")
    pipe.run_market(as_of=JPM_AS_OF, prices=_prices(), eps=_no_eps,  # type: ignore[arg-type]
                    dossiers=FIXTURES)
    pipe.store.export_jsonl(tmp_path / "x")
    back = Store.import_jsonl(tmp_path / "x", tmp_path / "back.db")
    for t in back.theses():
        assert back.market_context(t.thesis_id, t.current_version) == \
            pipe.store.market_context(t.thesis_id, t.current_version)


def test_the_row_carries_and_shows_its_warning_and_the_revision_counts(tmp_path: Path) -> None:
    """The split-sized move reaches the row and the rendered table; the revision counts print
    beside the value (structured, never parsed back from the basis)."""
    pipe = _jpm(tmp_path)
    v = _software(pipe)

    def jumpy(symbol: str, start: date, end: date) -> Closes:
        days = _days(end, 400)
        return [(d, 50.0 if i < 380 or symbol == BENCHMARK else 120.0)
                for i, d in enumerate(days) if start <= d <= end]

    ctx, _errors = market_context(v.content.s05_affected, thesis_id=v.thesis_id,
                                  version=v.version, run_id="R-x", as_of=JPM_AS_OF,
                                  prices=jumpy, eps=_no_eps)
    igv = next(r for r in ctx.rows if r.ticker == "IGV")
    assert len(igv.warnings) == 1 and "+140%" in igv.warnings[0]
    html = market_html(ctx, missing="")
    assert "⚠" in html and "+140%" in html
    cell = market_cell(MarketFigure(value=0.0587, basis="b", detail="21↑ 2↓"), "rev")
    assert "+5.9% · 21↑ 2↓" in cell
