"""Orchestrate one audit run: workbook + Polygon + grouped cache → ledger, aggregates, validation,
and every deliverable (A–G in the operator brief), written under ``out``."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from vinci.research_audit import aggregate as ag
from vinci.research_audit.benchmarks import (
    Benchmark,
    CurrencyFit,
    TrackingReport,
    ciq_benchmarks,
    converted_benchmark,
    currency_fit,
    proxy_benchmark,
    tracking_difference,
)
from vinci.research_audit.classify import Availability, Direction, direction_of, listing_of
from vinci.research_audit.engine import (
    COMPLETE,
    HORIZONS,
    EngineInputs,
    Identity,
    Obs,
    build_ledger,
    edate,
    session_after,
    verify_identity,
)
from vinci.research_audit.fetch import (
    CALENDAR_SYMBOL,
    SECTOR_ETFS,
    WINDOW_START,
    WORLD_PROXY,
    Fetched,
)
from vinci.research_audit.polygon import PolygonAudit
from vinci.research_audit.prices import Series, build_series, load_grouped_window
from vinci.research_audit.report import (
    identity_rows,
    obs_rows,
    price_rows,
    write_csv,
    write_json,
    write_workbook,
)
from vinci.research_audit.sec_sources import (
    SectorAssignment,
    assign_sectors,
    sec_http,
    sec_tickers,
    sector_fund_holdings,
)
from vinci.research_audit.validation import (
    MATERIAL_PP,
    ciq_pilot_arithmetic,
    path_diagnostics,
    pilot_vs_polygon,
)
from vinci.research_audit.workbook import AuditWorkbook, file_sha256

#: Calendar windows reported for every proxy-vs-index comparison (the dollar fell hard in H1 2025).
WINDOWS = [("H1-2025", date(2025, 1, 2), date(2025, 6, 30)),
           ("CY-2025", date(2024, 12, 31), date(2025, 12, 31)),
           ("CY-2024", date(2023, 12, 29), date(2024, 12, 31))]
#: The CIQ series counts as USD only if, read as exported, it is the best currency fit AND tracks
#: the USD proxy within this many points per 21-session window (RMS).
USD_MAX_RMS_GAP = 0.01


def _pct(x: float | None, nd: int = 1) -> str:
    return "n/a" if x is None else f"{x * 100:+.{nd}f}%"


def _identities(wb: AuditWorkbook, f: Fetched,
                sec: dict[str, tuple[str, str]]) -> dict[str, Identity]:
    out: dict[str, Identity] = {}
    for m in wb.mentions:
        if direction_of(m.rating) is Direction.NONDIRECTIONAL or m.ticker in out:
            continue
        first = min((p.public_date for mm in wb.mentions if mm.ticker == m.ticker
                     if (p := wb.publication(mm.pub_id)).public_date), default=None)
        out[m.ticker] = verify_identity(
            m.ticker, m.company, f.details.get(m.ticker), f.details_as_of.get(m.ticker), first,
            f.searches.get(m.ticker), sec.get(m.ticker))
    return out


def _currency_verdict(fits: list[CurrencyFit]) -> str:
    best = fits[0]
    usd = next(c for c in fits if c.hypothesis.startswith("USD"))
    is_usd = best is usd and usd.rms_21_session_gap <= USD_MAX_RMS_GAP
    head = ("CIQ 'MSCI World Net' series CONSISTENT WITH USD" if is_usd else
            f"CIQ 'MSCI World Net' series is NOT USD-denominated — best fit {best.hypothesis} "
            f"(converted to USD it tracks URTH within {best.annualized_diff * 100:+.2f}%/yr, "
            f"21-session RMS gap {best.rms_21_session_gap * 100:.2f}pp; read as USD the RMS gap "
            f"is {usd.rms_21_session_gap * 100:.2f}pp)")
    return head + f" over {best.first}→{best.last}, n={best.n_common}"


def run_audit(wb: AuditWorkbook, pa: PolygonAudit, f: Fetched, *, grouped_cache: Path,
              cache_dir: Path, out: Path, today: date) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    input_sha_before = file_sha256(wb.path)
    sec = sec_http(cache_dir)
    ids = _identities(wb, f, sec_tickers(sec))
    verified = sorted(i.provider_ticker for i in ids.values() if i.status == "VERIFIED_POLYGON")
    symbols = sorted({CALENDAR_SYMBOL, WORLD_PROXY, *verified, *SECTOR_ETFS})
    missing = [s for s in symbols if s not in f.live]
    if missing:
        raise RuntimeError(f"fetch stage did not acquire {missing} — re-run fetch")

    grouped = load_grouped_window(grouped_cache, WINDOW_START, f.end, set(symbols))
    spy = build_series(CALENDAR_SYMBOL, live=f.live[CALENDAR_SYMBOL], grouped=grouped,
                       dividends=f.dividends[CALENDAR_SYMBOL], splits=f.splits[CALENDAR_SYMBOL],
                       sessions=None)
    sessions = [p.day for p in spy.points]
    series: dict[str, Series] = {CALENDAR_SYMBOL: spy}
    for sym in symbols:
        if sym != CALENDAR_SYMBOL:
            series[sym] = build_series(sym, live=f.live[sym], grouped=grouped,
                                       dividends=f.dividends[sym], splits=f.splits[sym],
                                       sessions=sessions)

    # Calendar cross-check: a pre-live cache day with rows must be a SPY session and vice versa.
    first_live = spy.first_live_day or f.end
    cache_days = {d for d, g in grouped.items() if g is not None and g.n_rows > 0}
    cache_none = sorted(d for d, g in grouped.items() if g is None and d < first_live)
    pre = [d for d in sessions if d < first_live]
    cal = {
        "sessions_total": len(sessions), "first_session": sessions[0],
        "last_session": sessions[-1], "first_live_session": first_live,
        "pre_live_sessions_from_cache": len(pre),
        "cache_days_with_rows_not_spy_sessions": sorted(d for d in cache_days
                                                        if d < first_live and d not in pre),
        "spy_sessions_without_cache_rows": sorted(d for d in pre if d not in cache_days),
        "pre_live_weekdays_missing_from_cache": cache_none,
    }

    # Sector: which Vanguard sector fund's N-PORT holds the stock, as of its first entry.
    first_entry: dict[str, date] = {}
    names: dict[str, list[str]] = {}
    for t, i in ids.items():
        if i.status != "VERIFIED_POLYGON":
            continue
        pub_days = [p.public_date for m in wb.mentions if m.ticker == t
                    if (p := wb.publication(m.pub_id)).public_date]
        e = session_after(sessions, min(pub_days)) if pub_days else None
        if e is not None:
            first_entry[t], names[t] = e, [i.provider_name, i.company]
    sectors = assign_sectors(sector_fund_holdings(sec, SECTOR_ETFS), names, first_entry,
                             SECTOR_ETFS)
    for t, a in sectors.items():
        ids[t] = Identity(**{**ids[t].__dict__, "sector": a.sector or "NO SECTOR FUND"})

    ciq_world, sp500 = ciq_benchmarks(wb)
    proxies = {s: proxy_benchmark(series[s], lab) for s, lab in
               [(CALENDAR_SYMBOL, "S&P 500"), (WORLD_PROXY, "MSCI World Net USD")]}
    world = proxies[WORLD_PROXY]
    sector_proxies: dict[str, Benchmark] = {
        a.sector: proxy_benchmark(series[a.etf], f"US {a.sector} sector (MSCI US IMI 25/50)")
        for a in sectors.values() if a.status == "ASSIGNED"}
    fx = {pair: {b.day: b.close for b in bars} for pair, bars in f.fx.items()}
    fits = currency_fit(ciq_world, world, fx)
    best_pair = next((c.hypothesis for c in fits if c.hypothesis.startswith("C:")), "")
    derived = converted_benchmark(ciq_world, best_pair, fx[best_pair]) if best_pair else None
    track_world = tracking_difference(world, derived, WINDOWS) if derived else None
    track_ciq_raw = tracking_difference(world, ciq_world, WINDOWS)
    track_spx = tracking_difference(proxies[CALENDAR_SYMBOL], sp500, WINDOWS)

    ledger = build_ledger(EngineInputs(wb=wb, identities=ids, series=series, sessions=sessions,
                                       last_session=f.end, world=world, ciq_world=ciq_world,
                                       sp500=sp500, sector_proxies=sector_proxies))
    aggs = ag.aggregates(ledger)
    pubs = ag.publisher_comparison(ledger, list(wb.publications), list(wb.signals))
    dist = [*ag.distribution(ledger, "LONG"), *ag.distribution(ledger, "NEUTRAL"),
            *ag.distribution(ledger, "UNDERWEIGHT")]
    worst = ag.worst_outcomes(ledger)
    arith = ciq_pilot_arithmetic(wb)
    pilot = pilot_vs_polygon(wb, ledger)
    paths = [path_diagnostics(wb, series, t) for t in ("AXP", "BKR")]
    qa = _qa(ledger, series, wb, input_sha_before)

    # ---- deliverables ------------------------------------------------------------------------
    audit_of = {i.provider_ticker: t for t, i in ids.items() if i.provider_ticker}
    led_rows = obs_rows(ledger)
    write_csv(out / "article_company_return_ledger.csv", led_rows)
    write_csv(out / "prices_daily.csv", price_rows(series, audit_of))
    write_csv(out / "benchmarks_daily_ciq.csv", [
        {"date": r.day, "msci_world_net_level": None if r.msci_world_net is None
         else 100 * (1 + r.msci_world_net), "sp500_net_level": None if r.sp500_net is None
         else 100 * (1 + r.sp500_net), "ciq_row": r.row} for r in wb.ciq_daily])
    id_rows = identity_rows(ids, series)
    for r in id_rows:
        asg = sectors.get(str(r["audit_ticker"]))
        r["sector_source"] = (f"{asg.status}: {asg.detail}" if asg else
                              "not assessed (identity not verified)")
        r["sector_benchmark_proxy"] = f"{asg.etf}_TR_PROXY" if asg and asg.etf else ""
    for sym in sorted(set(symbols) - set(verified)):
        ser = series[sym]
        id_rows.append({"audit_ticker": f"(benchmark) {sym}", "status": "BENCHMARK PROXY",
                        "provider": "Polygon", "provider_ticker": sym,
                        "security_identity": str((f.details.get(sym) or {}).get("name")),
                        "currency": "USD", "exchange": (f.details.get(sym) or {}).get(
                            "primary_exchange"),
                        "first_bar": ser.points[0].day, "last_bar": ser.points[-1].day,
                        "n_bars": len(ser.points), "first_live_bar": ser.first_live_day,
                        "cache_live_overlap": f"{ser.overlap.n_overlap} sessions, "
                                              f"{ser.overlap.n_mismatch} mismatches",
                        "dividends_applied": len(ser.dividends_used),
                        "blocks": "; ".join(b.reason for b in ser.blocks),
                        "warnings": " | ".join(ser.warnings)})
    write_csv(out / "ticker_coverage.csv", id_rows)
    requests = _ciq_requests(wb, ids, ledger)
    write_csv(out / "ciq_export_requests.csv", requests)
    board = [*ag.leaderboard(aggs["covering_analyst"]), *ag.leaderboard(aggs["thesis_team"]),
             *ag.leaderboard(aggs["named_author"])]
    write_csv(out / "author_leaderboard.csv", board)
    write_csv(out / "publisher_comparison.csv", pubs)
    agg_rows = [r for k in ("article", "thesis_category", "publisher", "region", "sector",
                            "industry", "publication_year") for r in aggs[k]]
    write_csv(out / "aggregates.csv", agg_rows)
    write_csv(out / "distribution.csv", dist)
    write_csv(out / "worst_outcomes.csv", obs_rows(worst))
    prov = [{"kind": "polygon_api", **c.__dict__} for c in pa.calls]
    prov += [{"kind": "polygon_grouped_cache", "day": d, "fetched": g.fetched_at,
              "rows_in_file": g.n_rows, "symbols_found": len(g.bars)}
             for d, g in sorted(grouped.items()) if g is not None]
    write_csv(out / "provenance_log.csv", prov)

    verdict = _currency_verdict(fits)
    summary = _summary(wb, f, ledger, pubs, ids, verdict, track_world, pilot, cal, today)
    sheets: dict[str, tuple[str, list[dict[str, Any]]]] = {
        "Ticker Map": ("TICKER MAP | AUDIT → PROVIDER → IDENTITY → CCY → EXCHANGE || Every rated "
                       "ticker; non-US primaries are UNAVAILABLE_POLYGON and never substituted.",
                       id_rows),
        "CIQ Export Requests": ("CIQ EXPORT REQUESTS || Instruments Polygon cannot supply.",
                                requests),
        "Validation": ("VALIDATION | CIQ PILOT vs POLYGON || Same sessions, same benchmark "
                       "series; only the stock source differs.", pilot),
        "Validation Paths": ("VALIDATION | DAILY PATH + EX-DATE DIAGNOSTICS || CIQ 'Dividend Adj' "
                             "vs Polygon TR and price-only.",
                             [{k: v for k, v in p.items() if k != "ex_dates"} for p in paths]
                             + [e for p in paths for e in p["ex_dates"]]),
        "Benchmarks & Tracking": ("BENCHMARKS | INDEX vs PROXY TRACKING || " + verdict,
                                  _tracking_rows(ciq_world, sp500, derived, proxies,
                                                 sector_proxies, fits,
                                                 [t for t in (track_world, track_ciq_raw,
                                                              track_spx) if t])),
        "Aggregates": ("AGGREGATES || By article, thesis category, publisher, region, sector, "
                       "industry, publication year. LONG rows are the scored set.", agg_rows),
        "Author Leaderboard": ("AUTHOR / TEAM LEADERBOARD || Ranked only where n>=10 at 12m; "
                               "covering analyst = rating owner; thesis team = publication lead; "
                               "named author = shared credit.", board),
        "Publisher Comparison": ("PUBLISHER COMPARISON || All six publishers; zero observations "
                                 "is reported as zero, never as a track record.", pubs),
        "Distribution": ("DISTRIBUTION OF EXCESS vs URTH TR (PROXY for MSCI World Net USD) || "
                         "plus the worst LONG outcomes below", dist + obs_rows(worst)),
        "Provenance": ("PROVENANCE || Every Polygon response used and every cached grouped-daily "
                       "file read.", prov),
    }
    xlsx = out / f"Research_Alpha_Historical_Audit_UPDATED_{today.isoformat()}.xlsx"
    wcounts = write_workbook(wb.path, xlsx, wb, ledger, series, audit_of, sheets, summary,
                             WORLD_PROXY)

    input_sha_after = file_sha256(wb.path)
    qa.append(("input workbook unchanged (sha256 before == after)",
               input_sha_before == input_sha_after, input_sha_after))
    manifest = {
        "run_at_utc": datetime.now(tz=UTC).isoformat(), "today": today,
        "last_completed_session": f.end, "input_workbook": str(wb.path),
        "input_sha256": input_sha_before, "ciq_exports_named": [wb.ciq_index_export,
                                                                wb.ciq_equity_export],
        "polygon_responses_used": len(pa.calls), "grouped_cache_dir": str(grouped_cache),
        "symbols_priced": symbols, "workbook": xlsx.name, "workbook_counts": wcounts,
        "qa": [{"check": c, "pass": ok, "detail": d} for c, ok, d in qa],
    }
    write_json(out / "run_manifest.json", manifest)
    (out / "coverage_report.md").write_text(_coverage_md(wb, ids, series, ledger, requests, cal))
    (out / "validation_log.md").write_text(_validation_md(
        wb, f, arith, pilot, paths, fits, verdict,
        [t for t in (track_world, track_ciq_raw, track_spx) if t], cal, series, qa, ids,
        sectors))
    return manifest


# --- QA -------------------------------------------------------------------------------------------

def _qa(ledger: list[Obs], series: dict[str, Series], wb: AuditWorkbook,
        sha: str) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    done = [o for o in ledger if o.status == COMPLETE]

    def chk(name: str, bad: list[str]) -> None:
        out.append((name, not bad, f"{len(bad)} violation(s): {bad}" if bad else "ok"))

    chk("every ledger row carries a status", [o.test_id or o.company for o in ledger
                                              if not o.status])
    chk("no nondirectional / duplicate mention carries a return",
        [o.company for o in ledger if o.months is None and o.stock_return is not None])
    chk("COMPLETE rows: entry and exit bars exist (no carry-forward)",
        [o.test_id for o in done if date.fromisoformat(o.entry_date) not in
         series[o.provider_ticker].by_day or date.fromisoformat(o.exit_date) not in
         series[o.provider_ticker].by_day])
    chk("COMPLETE rows: exit on/after target, entry strictly after public date",
        [o.test_id for o in done if o.exit_date < o.target_date
         or o.entry_date <= o.public_date[:10]])
    chk("COMPLETE rows: stock return == exit adjClose / entry adjClose - 1",
        [o.test_id for o in done if abs((o.exit_adj_close or 0) / (o.entry_adj_close or 1) - 1
                                        - (o.stock_return or 0)) > 1e-12])
    chk("COMPLETE rows: excess == stock - benchmark",
        [o.test_id for o in done if abs((o.stock_return or 0) - (o.world_return or 0)
                                        - (o.excess_vs_world or 0)) > 1e-12])
    chk("only Overweight rows are direction LONG",
        [o.test_id for o in ledger if o.direction == "LONG" and o.rating != "Overweight"])
    chk("no UNAVAILABLE_POLYGON listing was priced",
        [o.test_id for o in ledger if listing_of(o.audit_ticker).availability
         is Availability.UNAVAILABLE_POLYGON and o.stock_return is not None])
    chk("every workbook test row has a ledger row",
        sorted({t.test_id for t in wb.tests} - {o.test_id for o in ledger}))
    chk("exits never after the last completed session",
        [o.test_id for o in done if o.exit_date > max(p.day for p in series["SPY"].points)
         .isoformat()])
    return out


# --- text reports ---------------------------------------------------------------------------------

def _ciq_requests(wb: AuditWorkbook, ids: dict[str, Identity],
                  ledger: list[Obs]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t, i in sorted(ids.items()):
        if i.status == "VERIFIED_POLYGON":
            continue
        rows = [o for o in ledger if o.audit_ticker == t and o.months is not None]
        pubs = sorted({f"{o.pub_id} ({o.rating}, {o.public_date})" for o in rows})
        starts = [date.fromisoformat(o.public_date) for o in rows if o.date_granularity == "Day"]
        out.append({
            "audit_ticker": t, "company": i.company, "reason": i.status,
            "primary_exchange_mic": i.listing_mic, "listing_currency": i.listing_currency,
            "publications": "; ".join(pubs),
            "window_from": min(starts).isoformat() if starts else "",
            # last publication + 12 calendar months + 2 weeks: covers the 12m exit session
            "window_to": (edate(max(starts), 12) + timedelta(days=14)).isoformat()
            if starts else "",
            "fields_requested": ("daily close (local), dividend-adjusted / total-return series "
                                 "(gross), cash dividends with ex-dates, split factors, "
                                 "local→USD FX close for the same sessions, trading-halt / "
                                 "delisting events"),
            "polygon_lines_found_NOT_substituted": " || ".join(i.alternatives),
            "detail": i.detail,
        })
    out.append({"audit_ticker": "MSCI World Net (benchmark)", "company": "MSCI World Index",
                "reason": "BENCHMARK NOT USD", "fields_requested": (
                    "re-export MSCI World Net Return in USD with the currency shown (the "
                    "supplied series fits EUR, see validation_log.md §6), daily, 2023-01-03 to "
                    "date; until then URTH TR is used as a labelled PROXY")})
    return out


def _tracking_rows(ciq_world: Benchmark, sp500: Benchmark, derived: Benchmark | None,
                   proxies: dict[str, Benchmark], sectors: dict[str, Benchmark],
                   fits: list[CurrencyFit], tracks: list[TrackingReport]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    roles = {ciq_world.code: "RECONCILIATION ONLY — not USD (see currency fit); never scored",
             sp500.code: "regional comparison for US listings (USD; tracks SPY within 0.4%/yr)",
             f"{WORLD_PROXY}_TR_PROXY": "PRIMARY world benchmark for every excess return",
             f"{CALENDAR_SYMBOL}_TR_PROXY": "session calendar; S&P 500 proxy for diagnostics"}
    for b in (ciq_world, sp500, *proxies.values(), *([derived] if derived else [])):
        rows.append({"code": b.code, "label": b.label, "kind": b.kind,
                     "role": roles.get(b.code, "tracking-difference reference only"),
                     "source": b.source, "first": min(b.levels), "last": max(b.levels),
                     "n_values": len(b.levels)})
    for sec, b in sorted(sectors.items()):
        rows.append({"code": b.code, "label": b.label, "kind": b.kind,
                     "role": f"sector-adjusted comparison for stocks held by the {sec} fund",
                     "source": b.source, "first": min(b.levels), "last": max(b.levels),
                     "n_values": len(b.levels),
                     "tracking_difference": ("UNMEASURED — no sector index series is entitled "
                                             "on this Polygon plan (index aggregates answer 403);"
                                             " the ETF's TR is net of its fees")})
    for c in fits:
        rows.append({"code": "CURRENCY FIT", "label": c.hypothesis, "kind": "TEST",
                     "first": c.first, "last": c.last, "n_values": c.n_common,
                     "tracking_difference": (
                         f"URTH {c.proxy_total * 100:+.2f}% vs CIQ series as {c.hypothesis} "
                         f"{c.converted_total * 100:+.2f}%; {c.annualized_diff * 100:+.2f}%/yr; "
                         f"21-session RMS gap {c.rms_21_session_gap * 100:.2f}pp")})
    for t in tracks:
        rows.append({"code": "TRACKING", "label": f"{t.proxy} vs {t.index}", "kind": "PROXY-INDEX",
                     "first": t.first, "last": t.last, "n_values": t.n_common,
                     "tracking_difference": (
                         f"total {t.proxy_total * 100:+.2f}% vs {t.index_total * 100:+.2f}%; "
                         f"annualized difference {t.annualized_diff * 100:+.2f}%/yr; daily "
                         f"tracking error {t.daily_te_annualized * 100:.2f}%/yr (close-time "
                         f"mismatch inflates it)")})
        for name, a, b2 in t.by_year + t.windows:
            rows.append({"code": "TRACKING", "label": f"{t.proxy} vs {t.index}",
                         "kind": "WINDOW", "first": name, "tracking_difference":
                         f"proxy {a * 100:+.2f}% vs index {b2 * 100:+.2f}% "
                         f"(gap {(a - b2) * 100:+.2f}pp)"})
    return rows


def _headline(ledger: list[Obs]) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    for h in HORIZONS:
        st = ag.horizon_stats([o for o in ledger if o.direction == "LONG"], h)
        lines.append((f"LONG (Overweight) {h}M vs URTH TR (PROXY, MSCI World Net USD)",
                      f"n={st[f'{h}m_completed']} completed; win rate "
                      f"{_pct(st[f'{h}m_win_rate_vs_world'], 0).lstrip('+')}; median excess "
                      f"{_pct(st[f'{h}m_median_excess_vs_world'])}; mean "
                      f"{_pct(st[f'{h}m_mean_excess_vs_world'])}; EW cohort "
                      f"{_pct(st[f'{h}m_ew_cohort_excess_vs_world'])} over "
                      f"{st[f'{h}m_n_cohorts']} cohorts; sector-adjusted median "
                      f"{_pct(st[f'{h}m_median_excess_vs_sector'])} "
                      f"(n={st[f'{h}m_n_sector_adjusted']}); worst "
                      f"{_pct(st[f'{h}m_worst_excess_vs_world'])} {st[f'{h}m_worst_name']}"))
    return lines


def _summary(wb: AuditWorkbook, f: Fetched, ledger: list[Obs], pubs: list[dict[str, Any]],
             ids: dict[str, Identity], verdict: str, tw: TrackingReport | None,
             pilot: list[dict[str, Any]], cal: dict[str, Any],
             today: date) -> list[tuple[str, str]]:
    n_by: dict[str, int] = {}
    for o in ledger:
        n_by[o.status] = n_by.get(o.status, 0) + 1
    idc: dict[str, int] = {}
    for i in ids.values():
        idc[i.status] = idc.get(i.status, 0) + 1
    worst_pilot = max((abs(r.get("diff_stock_pp", 0.0)) for r in pilot), default=0.0)
    flips = [r["test_id"] for r in pilot if r.get("usd_outcome_differs_from_pilot")]
    done = [o for o in ledger if o.status == COMPLETE and o.direction == "LONG"]
    cohorts = sorted({(o.publisher, o.pub_id, o.entry_date) for o in done})
    proxy_td = (f"URTH vs the CIQ series converted to USD: {tw.annualized_diff * 100:+.2f}%/yr "
                f"over {tw.first}→{tw.last}" if tw else "tracking difference not measurable")
    lines = [
        ("Run date / last completed session", f"{today} / {f.end} (from SPY bars)"),
        ("Input workbook (unchanged)", f"{wb.path.name} sha256 {wb.sha256}"),
        ("Scope of the evidence", "26 publications / 97 mention rows from the workbook's "
         "non-random public-access sample. Only rows with a STATED analyst rating are signals; "
         "only Overweight is scored as a long."),
        *_headline(ledger),
        ("Publishers with scored observations", "; ".join(
            f"{p['publisher']}: {p['12m_completed']}" for p in pubs)),
        ("Ledger row statuses", "; ".join(f"{k}={v}" for k, v in sorted(n_by.items()))),
        ("Rated-ticker identity outcomes", "; ".join(f"{k}={v}" for k, v in sorted(idc.items()))),
        ("Price data", f"Polygon. This plan serves daily bars only from "
         f"{cal['first_live_session']}; earlier sessions come from the repo's cached Polygon "
         f"grouped-daily responses (fetched 2026-08-06), un-adjusted with Polygon split events "
         f"and reconciled bar-for-bar against live bars on the overlap (see Ticker Map)."),
        ("World benchmark (all excess returns)", "URTH total return — PROXY for MSCI World "
         f"Net USD; {proxy_td}. " + verdict + ". The CIQ series is therefore kept only as a "
         "reconciliation column and never scored."),
        ("CIQ pilot reproduction", f"6 AXP/BKR horizons recomputed from Polygon on CIQ's own "
         f"sessions and benchmark series; largest stock-return gap {worst_pilot:.2f}pp "
         f"(material threshold {MATERIAL_PP:.2f}pp). Against the USD benchmark the pilot's "
         f"outcome label changes on {len(flips)} of {len(pilot)} rows: {', '.join(flips) or '—'}."),
        ("Interpretation limits", f"Every scored LONG observation comes from {len(cohorts)} "
         f"publication cohort(s): {'; '.join(f'{a} {b} (entry {c})' for a, b, c in cohorts)}. "
         "Names within a cohort share an entry close, so they are cross-sectionally correlated, "
         "not independent trials; horizons overlap (6m ⊂ 9m ⊂ 12m). Non-US primary listings are "
         "excluded (UNAVAILABLE_POLYGON), tilting the sample to US names. A pilot read of the "
         "channels sampled, not a measure of publisher skill."),
    ]
    return lines


def _coverage_md(wb: AuditWorkbook, ids: dict[str, Identity], series: dict[str, Series],
                 ledger: list[Obs], requests: list[dict[str, Any]], cal: dict[str, Any]) -> str:
    md: list[str] = ["# Ticker coverage and unresolved-data report", ""]
    n_m = len(wb.mentions)
    by_status: dict[str, list[Obs]] = {}
    for o in ledger:
        by_status.setdefault(o.status, []).append(o)
    md += [f"Population: all {n_m} 'Company Mentions' rows of `{wb.path.name}` "
          f"(sha256 `{wb.sha256[:12]}…`), {len(ledger)} ledger rows "
          f"(rated rows × 3 horizons + unrated/duplicate rows × 1).", "",
          "| status | ledger rows |", "|---|---:|"]
    md += [f"| {k} | {len(v)} |" for k, v in sorted(by_status.items())]
    md += ["", "## Rated tickers", "",
          "| audit ticker | company | status | provider | bars | live from | overlap "
          "(n / mismatches) | divs | splits | gaps | blocks |", "|---|---|---|---|---:|---|---|"
          "---:|---|---:|---|"]
    for t, i in sorted(ids.items()):
        s = series.get(i.provider_ticker) if i.provider_ticker else None
        md.append(f"| {t} | {i.company} | {i.status} | {i.provider_ticker or '—'} | "
                 f"{len(s.points) if s else 0} | {s.first_live_day if s else '—'} | "
                 f"{f'{s.overlap.n_overlap} / {s.overlap.n_mismatch}' if s else '—'} | "
                 f"{len(s.dividends_used) if s else '—'} | "
                 f"{'; '.join(f'{x.execution_date} {x.split_to:g}:{x.split_from:g}' for x in s.splits_used) if s and s.splits_used else '—'} | "  # noqa: E501
                 f"{len(s.gaps) if s else '—'} | "
                 f"{'; '.join(b.reason for b in s.blocks) if s and s.blocks else '—'} |")
    md += ["", "## Unresolved (every rated row that is not COMPLETE)", ""]
    unresolved = [o for o in ledger if o.months is not None and o.status != COMPLETE]
    md += [f"{len(unresolved)} rows (of {sum(1 for o in ledger if o.months is not None)} rated "
          f"rows). Grouped by reason:", ""]
    reasons: dict[str, list[Obs]] = {}
    for o in unresolved:
        reasons.setdefault(o.status, []).append(o)
    for k, v in sorted(reasons.items()):
        names = sorted({f"{o.audit_ticker} ({o.pub_id})" for o in v})
        md.append(f"- **{k}** — {len(v)} rows, {len(names)} signals: {', '.join(names)}")
    md += ["", "## Not scored: no stated rating", ""]
    nd = by_status.get("NOT_SCORED_NONDIRECTIONAL", [])
    md.append(f"{len(nd)} mention rows carry 'Not stated' — retained with their role, never "
             f"converted to a recommendation: " + ", ".join(
                 f"{o.company} ({o.pub_id}, {o.audit_role})" for o in nd))
    dup = by_status.get("DUPLICATE_MENTION_IN_PUBLICATION", [])
    md += ["", f"{len(dup)} duplicate mention rows (same company twice in one publication; the "
          f"rated row is the one counted): " + ", ".join(f"{o.company} ({o.mention_src})"
                                                          for o in dup)]
    md += ["", "## Session calendar", "",
          f"- {cal['sessions_total']} sessions {cal['first_session']} → {cal['last_session']} "
          f"(SPY bars; live from {cal['first_live_session']}).",
          f"- Cache days with rows that are not SPY sessions: "
          f"{len(cal['cache_days_with_rows_not_spy_sessions'])} "
          f"{cal['cache_days_with_rows_not_spy_sessions']}",
          f"- SPY sessions with no cached grouped rows: "
          f"{len(cal['spy_sessions_without_cache_rows'])} {cal['spy_sessions_without_cache_rows']}",
          f"- Pre-live weekdays with no cache file: "
          f"{len(cal['pre_live_weekdays_missing_from_cache'])} "
          f"{cal['pre_live_weekdays_missing_from_cache']}", "",
          "## CIQ export requests", "",
          f"{len(requests)} requests (see `ciq_export_requests.csv`)."]
    return "\n".join(str(x) for x in md) + "\n"


def _validation_md(wb: AuditWorkbook, f: Fetched, arith: list[dict[str, Any]],
                   pilot: list[dict[str, Any]], paths: list[dict[str, Any]],
                   fits: list[CurrencyFit], verdict: str, tracks: list[TrackingReport],
                   cal: dict[str, Any], series: dict[str, Series],
                   qa: list[tuple[str, bool, str]], ids: dict[str, Identity],
                   sectors: dict[str, SectorAssignment]) -> str:
    md: list[str] = ["# Source, provenance and validation log", ""]
    md += ["## 1. Inputs", "",
          f"- Workbook: `{wb.path}` sha256 `{wb.sha256}`; sheets read: "
          f"{', '.join(wb.sheet_names)}.",
          f"- CIQ exports named by the workbook: `{wb.ciq_index_export}`, "
          f"`{wb.ciq_equity_export}`. The raw .xls files were not found on disk; their data is "
          f"used as transcribed in 'CIQ Daily Data' ({len(wb.ciq_daily)} rows).",
          f"- Last completed session: {f.end} (newest SPY bar requested through the day before "
          f"the run date).", ""]
    md += ["## 2. Polygon plan window (measured)", "",
          "- `GET /v2/aggs/ticker/AXP/range/1/day/2024-01-02/2024-01-10` → 403 NOT_AUTHORIZED "
          "('Your plan doesn't include this data timeframe'); the same call for "
          "2024-10-01→2024-10-15 returns bars from 2024-10-09. Index aggregates (`I:SPX`) → 403 "
          "(not entitled).",
          f"- Therefore sessions before {cal['first_live_session']} come from the repo's netcache "
          f"of grouped-daily responses (adjusted=true, fetched 2026-08-06) and are un-adjusted "
          f"with Polygon's split events; reference endpoints (details/dividends/splits) are not "
          f"window-limited.", ""]
    md += ["## 3. Cache ↔ live overlap reconciliation (raw close, tolerance 1bp)", "",
          "| symbol | overlap sessions | mismatches | max rel diff | examples |",
          "|---|---:|---:|---:|---|"]
    for sym, s in sorted(series.items()):
        md.append(f"| {sym} | {s.overlap.n_overlap} | {s.overlap.n_mismatch} | "
                 f"{s.overlap.max_rel_diff:.2e} | {'; '.join(s.overlap.examples) or '—'} |")
    md += ["", "## 4. Corporate actions, blocks and warnings", ""]
    for sym, s in sorted(series.items()):
        if s.splits_used or s.blocks or s.warnings:
            splits = [(str(x.execution_date), x.ratio) for x in s.splits_used]
            md.append(f"- **{sym}**: splits {splits}; blocks {[b.reason for b in s.blocks]}; "
                      f"warnings {s.warnings}")
    n_div = sum(len(s.dividends_used) for s in series.values())
    md.append(f"- Dividends applied (all symbols): {n_div} cash distributions, all USD.")
    md += ["", "## 5. Identity verification", "",
          "| audit ticker | status | Polygon record | detail |", "|---|---|---|---|"]
    for t, i in sorted(ids.items()):
        md.append(f"| {t} | {i.status} | {i.provider_name or '—'} {i.primary_exchange} "
                 f"{i.security_type} {i.currency} | {i.detail} |")
    md += ["", "## 6. Benchmarks", "", f"**{verdict}.**", "",
           "Currency test — the CIQ series converted to USD under each hypothesis, against URTH "
           "(iShares MSCI World ETF, USD) total return:", "",
           "| hypothesis | window | URTH | CIQ series as hypothesis | diff %/yr | "
           "21-session RMS gap |", "|---|---|---:|---:|---:|---:|"]
    for cf in fits:
        md.append(f"| {cf.hypothesis} | {cf.first}→{cf.last} (n={cf.n_common}) | "
                  f"{cf.proxy_total * 100:+.2f}% | {cf.converted_total * 100:+.2f}% | "
                  f"{cf.annualized_diff * 100:+.2f} | {cf.rms_21_session_gap * 100:.2f}pp |")
    md += ["", "Consequence: every excess return in this audit is against **URTH total return, "
           "labelled PROXY for MSCI World Net USD**; its tracking difference is measured against "
           "the CIQ series converted at the best-fit currency (DERIVED) below. The pilot's own "
           "'excess vs World' figures subtract a non-USD index from USD stock returns; they are "
           "reproduced in §8 on their own terms and re-stated in USD.", ""]
    for tr in tracks:
        md.append(f"- {tr.proxy} vs {tr.index}: {tr.first}→{tr.last}, n={tr.n_common}; total "
                  f"{tr.proxy_total * 100:+.2f}% vs {tr.index_total * 100:+.2f}%; "
                  f"{tr.annualized_diff * 100:+.2f}%/yr; windows: " + "; ".join(
                      f"{n} {a * 100:+.2f}% vs {b * 100:+.2f}%"
                      for n, a, b in tr.by_year + tr.windows))
    md.append("- SPY is labelled 'SPY total return (PROXY for the S&P 500)' everywhere; the "
              "S&P 500 Net TR used for the regional comparison is the CIQ index series, not SPY.")
    md += ["", "### Sector assignment (Vanguard sector fund N-PORT holdings)", "",
           "| ticker | status | sector | ETF | evidence |", "|---|---|---|---|---|"]
    for t, sa in sorted(sectors.items()):
        md.append(f"| {t} | {sa.status} | {sa.sector or '—'} | {sa.etf or '—'} | {sa.detail} |")
    md += ["", "## 7. CIQ pilot arithmetic (workbook self-consistency)", "",
          "| test | CIQ rows | stored stock TR | recomputed | stored world | recomputed |",
          "|---|---|---:|---:|---:|---:|"]
    for a in arith:
        md.append(f"| {a['test_id']} | {a['ciq_rows']} | {a['stored_stock_tr']:.6f} | "
                 f"{a['recomputed_stock_tr']:.6f} | {a['stored_world']:.6f} | "
                 f"{a['recomputed_world']:.6f} |")
    md += ["", "## 8. CIQ pilot vs Polygon", "",
           "**(a) Reproduction** — same sessions, same CIQ benchmark series; only the stock "
           "source differs:", "",
           "| test | sessions | CIQ stock | Polygon TR | Polygon price-only | Δ stock (pp) | "
           "CIQ excess | Polygon excess, same CIQ series | Δ excess (pp) | outcome agrees | "
           "verdict |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for r in pilot:
        if "polygon_stock_tr" not in r:
            md.append(f"| {r['test_id']} | — | — | — | — | — | — | — | — | — | {r['verdict']} |")
            continue
        md.append(f"| {r['test_id']} | {r['polygon_entry']}→{r['polygon_exit']} "
                  f"({'same' if r['same_sessions'] else 'DIFFERENT'}) | "
                  f"{_pct(r['ciq_stock_tr'], 2)} | {_pct(r['polygon_stock_tr'], 2)} | "
                  f"{_pct(r['polygon_price_only'], 2)} | {r['diff_stock_pp']:+.2f} | "
                  f"{_pct(r['ciq_excess'], 2)} | {_pct(r['polygon_excess_same_benchmark'], 2)} | "
                  f"{r['diff_excess_pp']:+.2f} | {r['sign_agrees']} | {r['verdict']} |")
    md += ["", "**(b) Currency** — the same stock returns against the USD world benchmark "
           "(URTH TR, PROXY):", "",
           "| test | pilot excess (non-USD benchmark) | pilot outcome | USD benchmark return | "
           "USD excess | USD outcome | currency effect (pp) | outcome changes |",
           "|---|---:|---|---:|---:|---|---:|---|"]
    for r in pilot:
        if "usd_excess" not in r:
            continue
        eff = r["currency_effect_pp"]
        md.append(f"| {r['test_id']} | {_pct(r['ciq_excess'], 2)} | {r['ciq_outcome']} | "
                  f"{_pct(r['usd_benchmark_return'], 2)} | {_pct(r['usd_excess'], 2)} | "
                  f"{r['usd_outcome']} | {'n/a' if eff is None else f'{eff:+.2f}'} | "
                  f"{'YES' if r['usd_outcome_differs_from_pilot'] else 'no'} |")
    md += ["", "### Path diagnostics (whole common window)", ""]
    for p in paths:
        md.append(f"- **{p['ticker']}** ({p['n_common']} common sessions {p['base']}→"
                 f"{p['last_common']}): end level CIQ {p['end_ciq']:.4f} vs Polygon TR "
                 f"{p['end_polygon_tr']:.4f} vs price-only {p['end_polygon_price']:.4f}; "
                 f"mean |gap| vs TR {p['mean_abs_gap_vs_tr']:.4f}, "
                 f"vs price {p['mean_abs_gap_vs_price']:.4f} "
                 f"→ CIQ closer to **{p['ciq_closer_to']}**; daily return diff mean "
                 f"{p['daily_ret_diff_pp_mean']:+.4f}pp, sd {p['daily_ret_diff_pp_sd']:.4f}pp, "
                 f"max |{p['daily_ret_diff_pp_maxabs']:.3f}|pp; weekdays in CIQ but not Polygon "
                 f"({len(p['weekdays_in_ciq_not_polygon'])}): {p['weekdays_in_ciq_not_polygon']}"
                 f"; Polygon days not in CIQ ({len(p['polygon_days_not_in_ciq'])}): "
                 f"{p['polygon_days_not_in_ciq']}.")
        md.append("")
        md.append("  | ex-date | cash | CIQ 1d | Polygon TR 1d | Polygon price 1d | div yield |")
        md.append("  |---|---:|---:|---:|---:|---:|")
        for e in p["ex_dates"]:
            md.append(f"  | {e['ex_date']} | {e['cash']} | {_pct(e['ciq_1d'], 3)} | "
                     f"{_pct(e['polygon_tr_1d'], 3)} | {_pct(e['polygon_price_1d'], 3)} | "
                     f"{e['dividend_yield_1d'] * 100:.3f}% |")
        md.append("")
    md += ["## 9. QA checks", "", "| check | result | detail |", "|---|---|---|"]
    for c, ok, d in qa:
        md.append(f"| {c} | {'PASS' if ok else 'FAIL'} | {d} |")
    md += ["", "## 10. Statistics conventions", "",
          "- Win rate = share of completed observations with excess > 0 (a tie is not a win).",
          "- EW cohort excess = mean over publication cohorts of each cohort's equal-weighted "
          "mean excess (a buy-and-hold equal-weight basket from a common entry has exactly that "
          "return).",
          "- Sector-adjusted = stock TR minus the SPDR sector ETF TR (PROXY) of the stock's "
          "SIC-derived sector (`vinci.sectors.sector_for_sic`) — a coarse SIC→GICS-like map, "
          "not GICS.",
          f"- Material CIQ/Polygon gap threshold: {MATERIAL_PP}pp of stock return.",
          f"- Sample-size flag: fewer than {ag.SMALL_SAMPLE_N} completed observations."]
    return "\n".join(str(x) for x in md) + "\n"

