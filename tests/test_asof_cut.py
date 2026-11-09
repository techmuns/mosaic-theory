"""Phase 2 C4 — the as-of cut, under the operator's ruling of 2026-11-01, verbatim: "Inputs are cut
at the page's price date (filed on or before it; latest such filing wins; nothing after a sealed
verdict)."

- F-D4: the price features are bounded at the frontier, so the 52-week window is the 365 days
  ending on the price date. A page whose prices run past its reference date printed a 368–377-day
  "52-week" window (from the reference date less 365 to the newest bar).
- X1(b): a share count filed after the cut is never used. LLY's page (price date 2026-10-28) took
  its 2026-10-26 count, filed 2026-10-29.
- E1-D6: the fundamentals snapshot (the page's `_adjusted_facts`, the screen's enrichment) and the
  EDGAR fallback read companyfacts as they stood on the cut, not as they stand today.

- The entry cut (review of #884): `assemble_mechanical` hands every reader EDGAR as it stood on
  the price date (`vinci.edgar.asof.AsOfEdgar`), pinned end to end on LLY's page — its release and
  10-Q filed 2026-10-29, after its price, are read by no reader.

Fixtures are real: NFLX's and LLY's stored bars (`tests/fixtures/prices`), LLY's, NFLX's and
Recursion's share counts as filed and LLY's submissions page (`tests/fixtures/asof_cut`, the copy
the committed pages were assembled from)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, cast

from vinci.edgar.client import EdgarClient, Filing, FundamentalSnapshot
from vinci.eod import compute_price_features
from vinci.netcache import CachedHttp, HttpError
from vinci.schemas.market import PriceBar

_ROOT = Path(__file__).resolve().parent
_BARS = [PriceBar(**json.loads(line))
         for line in (_ROOT / "fixtures" / "prices" / "NFLX.jsonl").read_text().splitlines()
         if line.strip()]


def _shares(ticker: str) -> dict[str, Any]:
    return cast(dict[str, Any],
                json.loads((_ROOT / "fixtures" / "asof_cut" / f"{ticker}-shares.json").read_text()))


# ─── F-D4: the 52-week window ends on the price date ──────────────────────────────────────────

def test_the_52_week_window_is_the_365_days_ending_on_the_price_date() -> None:
    """NFLX's bars run to 2026-10-16; read for a 2026-10-02 reference, the window ran from
    2025-10-02 to 2026-10-16 — 379 days called 52 weeks."""
    f = compute_price_features(_BARS, reference_date=date(2026, 10, 2), staleness_days=5,
                               frontier=date(2026, 10, 16))
    assert f.last.as_of == date(2026, 10, 16)
    assert "52-week window 2025-10-16→2026-10-16" in (f.high_52w.note or "")


def test_no_bar_after_the_frontier_is_read() -> None:
    f = compute_price_features(_BARS, reference_date=date(2026, 10, 2), staleness_days=5,
                               frontier=date(2026, 10, 9))
    # 2026-10-09 is a trading day in the fixture, so the price date is exactly it
    assert f.last.as_of == date(2026, 10, 9)
    assert "52-week window 2025-10-09→2026-10-09" in (f.high_52w.note or "")


def test_without_a_frontier_the_screen_reads_as_before() -> None:
    """The negative pin: the screen passes no frontier, and its windows stay where they were."""
    f = compute_price_features(_BARS, reference_date=date(2026, 10, 16), staleness_days=5)
    assert "52-week window 2025-10-16→2026-10-16" in (f.high_52w.note or "")



def test_the_eod_command_prints_the_span_it_read(monkeypatch: Any, capsys: Any) -> None:
    """`vinci eod --ref` prints the bars its features were computed over, not the whole store's:
    asked for 2026-10-09, it printed NFLX's span to 2026-10-16 (review of #884)."""
    import argparse
    from types import SimpleNamespace

    from vinci import cli

    class _St:
        def __init__(self, path: object) -> None: ...
        def __enter__(self) -> _St: return self
        def __exit__(self, *a: object) -> None: ...
        def get_price_history(self, iid: str) -> list[PriceBar]: return _BARS

    ident = SimpleNamespace(ticker="NFLX", name="Netflix", internal_id="NFLX")
    monkeypatch.setattr(cli, "get_config",
                        lambda: SimpleNamespace(db_path="x", price_staleness_days=5))
    monkeypatch.setattr(cli.EntityResolver, "from_config",
                        classmethod(lambda c, cfg: SimpleNamespace(resolve_ticker=lambda t: ident)))
    monkeypatch.setattr(cli, "Store", _St)
    assert cli._cmd_eod(argparse.Namespace(ticker="NFLX", ref="2026-10-09")) == 0
    head = capsys.readouterr().out.splitlines()[0]
    upto = [b for b in _BARS if b.bar_date <= date(2026, 10, 9)]
    assert f"[{upto[0].bar_date}..2026-10-09 ({len(upto)} bars)]" in head

# ─── X1(b): a count filed after the cut is never used ─────────────────────────────────────────

class _Facts:
    """Serves one filer's companyfacts; its submissions index is empty (cadence unknown)."""

    def __init__(self, facts: dict[str, Any]) -> None:
        self.facts = facts
        self.asked: list[date | None] = []

    def companyfacts(self, cik: str) -> dict[str, Any]:
        return self.facts

    def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",),
                       since: date | None = None) -> list[Filing]:
        return []


def test_a_share_count_filed_after_the_price_date_is_never_used() -> None:
    """LLY's 2026-10-26 count (940,745,031) was filed 2026-10-29, after its page's 2026-10-28 price
    date: the count is the one filed by then (941,357,065, counted 2026-08-03, filed 08-05)."""
    from vinci.dossier.mechanical import _edgar_shares_outstanding
    got = _edgar_shares_outstanding(cast(EdgarClient, _Facts(_shares("LLY"))), "0000059478",
                                    as_of=date(2026, 10, 28))
    assert got == 941_357_065


def test_a_share_count_filed_by_the_price_date_is_used() -> None:
    """The negative pin: NFLX's 2026-09-30 count was filed 2026-10-21, before its 10-28 price
    date, and stands."""
    from vinci.dossier.mechanical import _edgar_shares_outstanding
    got = _edgar_shares_outstanding(cast(EdgarClient, _Facts(_shares("NFLX"))), "0001065280",
                                    as_of=date(2026, 10, 28))
    assert got == 4_106_325_903


# ─── E1-D6: the fundamentals are read as they stood on the cut ────────────────────────────────

class _Snapshots(_Facts):
    """Records the as-of each fundamentals read is asked for."""

    def fundamental_snapshot(self, cik: str, *, as_of: date | None = None) -> FundamentalSnapshot:
        from vinci.edgar.client import compute_fundamental_snapshot
        self.asked.append(as_of)
        return compute_fundamental_snapshot("x", self.facts, as_of=as_of)

    def fundamental_snapshot_and_facts(
            self, cik: str, *, as_of: date | None = None,
    ) -> tuple[FundamentalSnapshot, dict[str, Any]]:
        return self.fundamental_snapshot(cik, as_of=as_of), self.facts


def test_the_pages_adjusted_facts_read_the_snapshot_at_the_cut() -> None:
    from tests.test_dossier import _min_record
    from vinci.dossier import mechanical as dm
    from vinci.dossier import schemas as ds
    edgar = _Snapshots(_shares("NFLX"))
    rg = ds.Sourced.present("Adjusted EBITDA of $380 million to $385 million",
                            source_ref="EDGAR 8-K X Ex-99.1")
    dm._adjusted_facts(_min_record(pe=5.5, price=4.71), cast(EdgarClient, edgar), rg,
                       date(2026, 10, 16), cut=date(2026, 10, 28))
    assert edgar.asked == [date(2026, 10, 28)]


def test_the_screens_fundamentals_are_read_at_its_price_date() -> None:
    """The screen's enrichment read today's companyfacts, so a re-run of a past screen saw the
    filings made since. It reads them as of the run's price date — its newest bar."""
    from tests.test_screen2 import _rec
    from vinci.screens.assemble import enrich_with_fundamentals
    edgar = _Snapshots(_shares("NFLX"))
    bars = [b for b in _BARS if b.bar_date <= date(2026, 10, 9)]
    enrich_with_fundamentals(_rec(drawdown=-0.4, rel=-0.3, pe_pctile=0.1),
                             edgar=cast(EdgarClient, edgar), price_bars=bars,
                             reference_date=date(2026, 10, 10))
    assert edgar.asked == [date(2026, 10, 9)]


def test_the_screens_share_change_reads_no_count_filed_after_its_price_date() -> None:
    """NFLX's 2026-09-30 count, filed 2026-10-21, is not knowable on a 2026-10-16 screen."""
    from tests.test_screen2 import _rec
    from vinci.screens.assemble import enrich_with_fundamentals
    edgar = _Snapshots(_shares("NFLX"))
    got = enrich_with_fundamentals(_rec(drawdown=-0.4, rel=-0.3, pe_pctile=0.1),
                                   edgar=cast(EdgarClient, edgar), price_bars=_BARS,
                                   reference_date=date(2026, 10, 16))
    note = got.fundamentals.share_count_change_730d.note or ""
    assert "4,106,325,903" not in note


def test_the_fallbacks_facts_read_nothing_filed_after_the_cut() -> None:
    """The CIQ-empty EDGAR fallback is handed companyfacts as they stood on the page's price date:
    NFLX's 2026-09-30 count, filed 2026-10-21, is not there on a 2026-10-20 cut."""
    from vinci.dossier.mechanical import _companyfacts_as_of
    got = _companyfacts_as_of(cast(EdgarClient, _Facts(_shares("NFLX"))), "0001065280",
                              date(2026, 10, 20))
    assert got is not None
    rows = got["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]
    assert rows and all(r["filed"] <= "2026-10-20" for r in rows)
    assert any(r["filed"] == "2026-10-21"
               for r in _shares("NFLX")["facts"]["dei"]["EntityCommonStockSharesOutstanding"]
               ["units"]["shares"])


# ─── review round 2: the page, assembled end to end on LLY's real inputs ──────────────────────
# The cut is applied ONCE at `assemble_mechanical`'s entry (`vinci.edgar.asof.AsOfEdgar`), so no
# reader downstream can read past it. These pin the rendered fields, through the whole assembly
# (TEST-LAYER RULE): LLY's count, NFLX-style windows, the chart, and the releases read.

def _lly_bars() -> list[PriceBar]:
    return [PriceBar(**json.loads(line)) for line in
            (_ROOT / "fixtures" / "prices" / "LLY.jsonl").read_text().splitlines() if line.strip()]


def _iwm_bars() -> list[PriceBar]:
    return [PriceBar(**json.loads(line)) for line in
            (_ROOT / "fixtures" / "prices" / "IWM.jsonl").read_text().splitlines() if line.strip()]


class _LlySec:
    """Serves LLY's real share facts and submissions (with its 2026-10-29 8-K and 10-Q); every
    other URL — an exhibit, an index, a cover — is refused and recorded."""

    def __init__(self, facts: dict[str, Any] | None = None) -> None:
        self.facts = facts or _shares("LLY")
        self.sub = json.loads((_ROOT / "fixtures" / "asof_cut" / "LLY-submissions.json")
                              .read_text())
        self.urls: list[str] = []

    def get_json(self, url: str, *, ttl_seconds: float | None = None,
                 params: Any = None) -> dict[str, Any]:
        self.urls.append(url)
        if "/companyfacts/" in url:
            return self.facts
        if url.endswith("CIK0000059478.json"):
            return cast(dict[str, Any], self.sub)
        raise HttpError(f"not served: {url}")

    def get_text(self, url: str, *, ttl_seconds: float | None = None, params: Any = None) -> str:
        self.urls.append(url)
        raise HttpError(f"not served: {url}")


class _Store:
    def get_price_history(self, internal_id: str) -> list[PriceBar]:
        return _lly_bars() if internal_id.endswith("-LLY") else _iwm_bars()

    def price_frontier(self) -> date:
        return date(2026, 10, 16)


class _Refused:
    def __getattr__(self, name: str) -> Any:
        raise HttpError(f"not served: {name}")


def _assemble_lly(sec: _LlySec, ref: date = date(2026, 10, 2), bundle: Any = None,
                  flags: list[str] | None = None) -> Any:
    """LLY's page assembled at a 2026-10-02 reference date on bars that run to 2026-10-16 — its
    price date — with an empty CIQ bundle (or ``bundle``) and no network; the assembly's flags
    are appended to ``flags`` when given."""
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.mechanical import assemble_mechanical
    from vinci.graph.exposure import ExposureGraph
    from vinci.schemas.data_record import Identity
    from vinci.screens.assemble import build_price_record, enrich_with_fundamentals
    ident = Identity(internal_id="SEC-0000059478-LLY", issuer_id="ISS-0000059478",
                     cik="0000059478", ticker="LLY", mic="XNYS", exchange="NYSE",
                     eod_symbol="LLY", name="Eli Lilly and Company", sic="2834")
    edgar = EdgarClient(http=cast(CachedHttp, sec))
    bars = [b for b in _lly_bars() if b.bar_date <= ref]
    rec = build_price_record(ident, price_bars=bars, benchmark_bars=_iwm_bars(),
                             reference_date=ref, staleness_days=5)
    rec = enrich_with_fundamentals(rec, edgar=edgar, price_bars=bars, reference_date=ref)
    mech, _flags = assemble_mechanical(
        rec, store=cast(Any, _Store()), edgar=edgar, http=cast(CachedHttp, sec),
        finra=cast(Any, _Refused()), graph=ExposureGraph(), resolver=cast(Any, None),
        bundle=bundle if bundle is not None else CiqBundle.from_files("LLY", []),
        reference_date=ref)
    if flags is not None:
        flags += _flags
    return mech


def test_the_page_reads_the_count_filed_by_its_price_date_end_to_end() -> None:
    """LLY's 2026-10-26 count (940,745,031) was filed 2026-10-29, after the page's price date:
    the page's share count is the one filed by then, and its 52-week window ends on the price
    date — through the whole assembly, so removing any call-site cut fails here."""
    mech = _assemble_lly(_LlySec())
    si = mech.stock_info
    assert si.as_of == date(2026, 10, 16)
    assert si.shares_out.value == 941_357_065
    assert "52-week window 2025-10-16→2026-10-16" in (si.high_52w.note or "")


def test_the_page_reads_no_release_filed_after_its_price_date() -> None:
    """LLY's results 8-K of 2026-10-29 (0000059478-26-000104) is after the page's 2026-10-16
    price date: no reader fetches it (the committed page cited its EX-99.1 as the newest release
    against a 2026-10-28 price date)."""
    sec = _LlySec()
    _assemble_lly(sec)
    assert not any("000005947826000104" in u or "0000059478-26-000104" in u for u in sec.urls)



def _latest_filed(facts: dict[str, Any] | None) -> str | None:
    return max((r["filed"] for ns in (facts or {}).get("facts", {}).values() for c in ns.values()
                for rows in c.get("units", {}).values() for r in rows if r.get("filed")),
               default=None)


def test_every_facts_reader_reads_the_facts_as_they_stood(monkeypatch: Any) -> None:
    """The valuation, its stated bases, capital allocation and the statement reconciliation each
    take companyfacts: all four get the facts as they stood on the 2026-10-16 price date, never
    LLY's rows filed 2026-10-29 (the reconciliation's own `filed_by` was the assembly's day)."""
    from vinci.dossier import mechanical as dm
    from vinci.dossier import statement_recon
    seen: dict[str, str | None] = {}

    def spy(name: str, fn: Any, at: int | str) -> Any:
        def wrapped(*a: Any, **k: Any) -> Any:
            seen[name] = _latest_filed(k[at] if isinstance(at, str) else a[at])
            return fn(*a, **k)
        return wrapped

    monkeypatch.setattr(dm, "_valuation", spy("valuation", dm._valuation, "facts"))
    monkeypatch.setattr(dm, "with_valuation_bases",
                        spy("bases", dm.with_valuation_bases, 1))
    monkeypatch.setattr(dm, "build_capital_allocation",
                        spy("capital allocation", dm.build_capital_allocation, 0))
    monkeypatch.setattr(statement_recon, "attach", spy("recon", statement_recon.attach, 2))
    _assemble_lly(_LlySec())
    assert set(seen) == {"valuation", "bases", "capital allocation", "recon"}
    assert all(v is not None and v <= "2026-10-16" for v in seen.values()), seen

def test_the_52_week_chart_ends_on_the_price_date() -> None:
    """The price box's range and the chart beside it read one window: the 365 days ending on the
    price date (the chart had ended on the reference date)."""
    mech = _assemble_lly(_LlySec())
    pts = mech.stock_performance.points
    assert pts[-1].date == "2026-10-16" and pts[0].date >= "2025-10-16"


def test_a_count_filed_after_the_price_date_is_named_when_it_was_the_only_one() -> None:
    """With no other fresh count, the UNKNOWN said "absent or older than Nd"; the count exists and
    was filed after the price date, and the reason says so."""
    facts = json.loads(json.dumps(_shares("LLY")))
    rows = facts["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]
    facts["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"] = [
        r for r in rows if r["filed"] == "2026-10-29"]
    for tag in list(facts["facts"].get("us-gaap", {})):
        del facts["facts"]["us-gaap"][tag]
    si = _assemble_lly(_LlySec(facts)).stock_info
    assert si.shares_out.value is None
    note = si.shares_out.note or ""
    assert "filed 2026-10-29" in note and "2026-10-16" in note


def test_the_share_tag_is_chosen_on_the_facts_as_they_stood() -> None:
    """Recursion on 2026-06-30: chosen on today's facts, the dei cover tag looked current (a count
    filed 2026-08-05) and its only row by then was 2021's; on the facts as they stood, the
    balance-sheet count of 2026-03-31 (530,628,653, filed 2026-05-06) is the count."""
    from vinci.dossier.mechanical import _edgar_shares_outstanding
    got = _edgar_shares_outstanding(cast(EdgarClient, _Facts(_shares("RXRX"))), "0001601830",
                                    as_of=date(2026, 6, 30))
    assert got == 530_628_653


# ─── STATE row 57: what the cut leaves out is STATED, and CIQ's guidance is cut too ───────────
# Through the whole assembly (TEST-LAYER RULE), on LLY's real submissions page and its own
# Guidance sheet (export on disk 2026-11-09, cut down: `fixtures/ciq_guidance_asof_cut.json`).

def _lly_guidance() -> Any:
    from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
    rows = json.loads((_ROOT / "fixtures" / "ciq_guidance_asof_cut.json").read_text())[
        "names"]["LLY"]["sheets"]["estimates|Guidance"]
    path = Path("/fixture/LLY-estimates.xls")
    return CiqBundle(ticker="LLY", workbooks=(CiqWorkbook(kind="estimates", path=path,
                                                          fmt=CiqFormat.BIFF_XLS, freq=None),),
                     _cache={path: {"Guidance": rows}})


def test_a_results_8k_filed_after_the_price_date_is_named_and_never_read() -> None:
    """LLY's results 8-K of 2026-10-29 (0000059478-26-000104, items 2.02 and 9.01) follows the
    page's 2026-10-16 price date. The page names it — in its audit tier and in a caveat, as a
    filing, never a parse — and still fetches nothing of it."""
    from vinci.dossier.flags import partition
    sec, flags = _LlySec(), []
    ps = _assemble_lly(sec, flags=flags).primary_source
    # main reads the 8-K nowhere AND says so nowhere: the caveat is the regression's first check
    named = [f for f in flags if "0000059478-26-000104" in f]
    assert len(named) == 1, named
    (caveat,) = named
    assert caveat.startswith("as-of cut:")
    assert "8-K 0000059478-26-000104 (filed 2026-10-29)" in caveat and "2026-10-16" in caveat
    assert "primary_source.releases_after_price_date" in caveat
    assert partition([caveat])[0] == [caveat]
    assert [(r.filed, r.source_ref, r.items) for r in ps.releases_after_price_date] == [
        (date(2026, 10, 29), "8-K 0000059478-26-000104", ["2.02", "9.01"])]
    assert ps.releases == []
    # nothing of it is fetched, nor the 10-Q filed with it (0000059478-26-000108)
    for acc in ("0000059478-26-000104", "0000059478-26-000108"):
        assert not any(acc in u or acc.replace("-", "") in u for u in sec.urls), acc


def test_ciqs_guidance_dated_after_the_price_date_reaches_no_reader() -> None:
    """LLY's own Guidance sheet dates five cells after the 2026-10-16 price date — FY 2026's EPS
    (35.00–36.00) and revenue (91,000–92,000) guides of 2026-10-29 among them, which the page
    read as its latest guides. Cut, no guidance reader takes them, and none offers an older guide
    as the latest in their place (CIQ keeps each period's latest guide only, so FY 2026's guides
    of the price date are not on this export): the bridge, its rows and the revenue guide the
    check reads are UNKNOWN; the five cells are kept in the audit tier and named in a caveat; the
    synthesis's facts carry none of them."""
    flags: list[str] = []
    mech = _assemble_lly(_LlySec(), bundle=_lly_guidance(), flags=flags)
    cp = mech.catalyst_path
    # THE LEAK, as main assembled it: rows dated 2026-10-29 and their guides in the bridge
    assert [(r.metric, r.dated) for r in (cp.guidance_bridge_rows.value or [])
            if r.dated > "2026-10-16"] == []
    assert "35.00 - 36.00" not in (cp.guidance_bridge.value or "")
    # the guide check reads CIQ's revenue guide as it stood: main printed "CIQ 91000.0–92000.0"
    assert "91000" not in (mech.primary_source.guide_verification.value or "")
    assert mech.primary_source.guide_verification.value == (
        "guide verification (revenue): CIQ guide UNKNOWN — not cross-checked")
    from vinci.dossier.ciq_sheets import GUIDANCE_NOT_AT_CUT
    from vinci.dossier.schemas import SourceStatus
    from vinci.dossier.synthesis import NOT_SENT
    for field in (cp.guidance_bridge_rows, cp.guidance_bridge):
        assert (field.status, field.note) == (SourceStatus.UNKNOWN, GUIDANCE_NOT_AT_CUT)
    assert [(g.metric, g.period, g.read, g.dated) for g in cp.guidance_after_price_date] == [
        ("EPS Normalized", "FY 2026", "guide", "2026-10-29"),
        ("DPS", "FQ3 2026", "actual", "2026-10-29"),
        ("DPS", "FQ4 2026", "guide", "2026-10-26"),
        ("Revenue", "FY 2026", "guide", "2026-10-29"),
        ("Effective Tax Rate %", "FY 2026", "guide", "2026-10-29"),
    ]
    (caveat,) = [f for f in flags if f.startswith("as-of cut:") and "CIQ" in f]
    assert "EPS Normalized FY 2026 guide 35.00 - 36.00 (dated 2026-10-29)" in caveat
    assert "catalyst_path.guidance_after_price_date" in caveat
    sent = json.dumps(mech.model_dump(exclude=NOT_SENT), default=str)
    assert "35.00 - 36.00" not in sent and "91,000.00 - 92,000.00" not in sent


def test_an_uncut_client_reads_the_same_ten_8ks_as_the_cut_view() -> None:
    """The refresh's rebuild hands `_primary_source` an UNCUT client with the page's cut, whose
    list starts with LLY's real 2026-10-29 results 8-K. Taking the ten newest BEFORE cutting left
    that slot empty: the rebuild read nine 8-Ks where the assembly's cut view reads ten. (The
    submissions fixture holds that one 8-K; the ten before it are dated stand-ins, real type.)"""
    from datetime import timedelta

    from vinci.dossier.mechanical import _events_by_cut
    from vinci.edgar.client import events as eight_k_events
    cut = date(2026, 10, 16)
    (late,) = eight_k_events(EdgarClient(http=cast(CachedHttp, _LlySec())), "0000059478")
    assert late.filing_date > cut
    earlier = [late.model_copy(update={"filing_date": cut - timedelta(days=30 * k),
                                       "accession": f"0000059478-26-{k:06d}"})
               for k in range(10)]
    listed = [late, *earlier]
    assert [f for f in listed[:10] if f.filing_date <= cut] == earlier[:9]   # the old read
    kept, unread = _events_by_cut(listed, cut)
    assert kept[:10] == earlier          # what `AsOfEdgar` lists: the ten on or before the cut
    assert [(r.filed, r.source_ref, r.items) for r in unread] == [
        (date(2026, 10, 29), "8-K 0000059478-26-000104", ["2.02", "9.01"])]
    assert _events_by_cut(earlier, cut) == (earlier, [])      # a cut view: nothing to name


def _with_8ks(sec: _LlySec, *rows: dict[str, str]) -> _LlySec:
    """LLY's real submissions page with filings added, newest first — dated stand-ins of the real
    type, every column the page carries."""
    recent = sec.sub["filings"]["recent"]
    template = {k: v[1] for k, v in recent.items()}
    for row in rows:
        full = {**template, **row, "reportDate": row["filingDate"],
                "acceptanceDateTime": f"{row['filingDate']}T12:00:00.000Z"}
        for k in recent:
            recent[k].append(full[k])
    return sec


def test_only_results_8ks_after_the_price_date_are_named_and_one_before_it_is_read() -> None:
    """Two stand-ins beside LLY's real 2026-10-29 results 8-K: one carrying only 5.02, filed after
    the 2026-10-16 price date (no release to leave out, so not named), and a results 8-K filed
    before it, which is read (its exhibit index is requested; this harness serves none)."""
    sec = _with_8ks(_LlySec(),
                    {"accessionNumber": "0000059478-26-000099", "filingDate": "2026-10-20",
                     "form": "8-K", "items": "5.02"},
                    {"accessionNumber": "0000059478-26-000077", "filingDate": "2026-08-06",
                     "form": "8-K", "items": "2.02,9.01"})
    ps = _assemble_lly(sec).primary_source
    assert [r.source_ref for r in ps.releases_after_price_date] == ["8-K 0000059478-26-000104"]
    assert any("000005947826000077" in u for u in sec.urls)
    assert not any("000005947826000099" in u or "000005947826000104" in u for u in sec.urls)


def test_the_release_list_is_cut_even_when_the_client_is_not(monkeypatch: Any) -> None:
    """The refresh hands `_primary_source` an uncut client. Played here by a view that lists
    filings made after the cut: the results 8-K of 2026-10-29 is still never fetched, and named
    once; a 5.02-only 8-K after the cut (a stand-in) leaves no release out, so it is not named."""
    from vinci.dossier import mechanical as dm
    from vinci.edgar.asof import AsOfEdgar

    class _Leaky(AsOfEdgar):
        def recent_filings(self, cik: int | str, *, forms: tuple[str, ...] = ("8-K",),
                           since: date | None = None) -> list[Filing]:
            return (self.inner.recent_filings(cik, forms=forms) if since is None
                    else self.inner.recent_filings(cik, forms=forms, since=since))

    monkeypatch.setattr(dm, "AsOfEdgar", _Leaky)
    sec = _with_8ks(_LlySec(), {"accessionNumber": "0000059478-26-000099",
                                "filingDate": "2026-10-20", "form": "8-K", "items": "5.02"})
    ps = _assemble_lly(sec).primary_source
    assert not any("000005947826000104" in u for u in sec.urls)
    assert [r.source_ref for r in ps.releases_after_price_date] == ["8-K 0000059478-26-000104"]

