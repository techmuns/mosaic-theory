"""Step 4 — the $0 deterministic probe, one name at a time, through the repo's OWN readers.

No LLM client is constructed; nothing under the worktree's data/ is written; every HTTP cache
write lands in the scratchpad (probe_common.CFG). Each layer is recorded as what the code
RETURNED or RAISED, verbatim (truncated where long, and said so), never re-interpreted here.
Usage: probe.py TICKER [TICKER ...]   (resumable: a ticker with out/probe/<T>.json is skipped
unless --force)."""

from __future__ import annotations

import datetime as dt
import json
import statistics
import sys
import traceback
from typing import Any

from probe_common import CFG, OUT, edgar, sec_http

TODAY = dt.date(2026, 11, 19)
PRICE_DAY = dt.date(2026, 11, 18)
PDIR = OUT / "probe"
PDIR.mkdir(parents=True, exist_ok=True)


def cut(s: Any, n: int = 400) -> Any:
    if isinstance(s, str) and len(s) > n:
        return s[:n] + f" …[truncated, {len(s)} chars]"
    return s


def err(exc: BaseException) -> dict:
    tb = traceback.extract_tb(exc.__traceback__)
    where = f"{tb[-1].filename.split('/')[-1]}:{tb[-1].lineno}" if tb else "?"
    return {"raised": type(exc).__name__, "message": cut(str(exc)), "at": where}


def df(field: Any) -> dict:
    """A DataField as recorded: value, status, note, source."""
    return {
        "value": field.value,
        "status": str(field.coverage_status),
        "note": cut(field.note, 300),
        "source": cut(field.source, 120),
    }


_PRICES: dict | None = None


def prices() -> dict:
    global _PRICES
    if _PRICES is None:
        from vinci.eod.client import PolygonEodClient

        cli = PolygonEodClient.from_config(CFG)
        _PRICES = dict(cli.grouped_daily(PRICE_DAY).items())
    return _PRICES


def probe(ticker: str) -> dict:
    from vinci.dossier import anchor as an
    from vinci.dossier import midcycle as mc
    from vinci.dossier.freshness import EVENT_8K_ITEM, EVENT_ANY_FORMS, EVENT_FORMS
    from vinci.dossier.mechanical import _edgar_shares_outstanding
    from vinci.edgar import net_debt as nd
    from vinci.edgar.client import compute_fundamental_snapshot
    from vinci.edgar.client import events as eight_k_events
    from vinci.edgar.concepts import (
        IFRS_NAMESPACE,
        facts_as_of,
        filer_fiscal_year,
        reporting_currency,
    )
    from vinci.resolver import EntityResolver
    from vinci.resolver.index import to_eod_symbol

    out: dict[str, Any] = {
        "ticker": ticker,
        "probed_at": dt.datetime.now().isoformat(timespec="seconds"),
        "cut": TODAY.isoformat(),
    }
    ed = edgar()
    res = EntityResolver.from_config(CFG)
    # L0 identity
    try:
        ident = res.resolve_ticker(ticker, enrich=True)
        cik = ident.cik
        out["identity"] = {
            "cik": cik,
            "name": ident.name,
            "exchange": ident.exchange,
            "sic": ident.sic,
            "sic_desc": ident.sic_description,
            "eod_symbol": ident.eod_symbol,
        }
    except Exception as exc:  # noqa: BLE001
        out["identity"] = err(exc)
        return out
    sic = ident.sic
    # L1 submissions → filing regime
    try:
        sub = ed._submissions(cik)
        rec = sub["filings"]["recent"]
        rows = list(zip(rec["form"], rec["filingDate"], strict=False))
        ann = [(f, x) for f, x in rows if f in ("10-K", "10-KT", "20-F", "40-F")]
        out["filings"] = {
            "latest_annual": max(ann, key=lambda z: z[1]) if ann else None,
            "n_10q_365": sum(1 for f, x in rows if f == "10-Q" and x >= "2025-11-19"),
            "n_6k_365": sum(1 for f, x in rows if f == "6-K" and x >= "2025-11-19"),
            "fye": sub.get("fiscalYearEnd"),
            "tickers": sub.get("tickers"),
            "inc": sub.get("stateOfIncorporationDescription") or sub.get("stateOfIncorporation"),
            "category": sub.get("category"),
        }
    except Exception as exc:  # noqa: BLE001
        out["filings"] = err(exc)
    # L2 companyfacts
    try:
        whole = ed.companyfacts(cik)
        facts = facts_as_of(whole, TODAY)
        ns = facts.get("facts") or {}
        out["companyfacts"] = {
            "namespaces": {k: len(v) for k, v in ns.items()},
            "ifrs_full_present": bool(ns.get(IFRS_NAMESPACE)),
            "reporting_currency": reporting_currency(facts),
        }
    except Exception as exc:  # noqa: BLE001
        out["companyfacts"] = err(exc)
        facts = None
    if facts is not None:
        # L3 fiscal year
        try:
            fy = filer_fiscal_year(facts)
            out["fiscal_year"] = (
                None
                if fy is None
                else {
                    "tag": fy.tag,
                    "unit": fy.unit,
                    "start": str(fy.period_start),
                    "end": str(fy.period_end),
                    "days": (fy.period_end - fy.period_start).days if fy.period_start else None,
                    "filed": str(fy.filed),
                    "form": fy.form,
                    "ifrs_end": str(fy.ifrs_end) if fy.ifrs_end else None,
                }
            )
        except Exception as exc:  # noqa: BLE001
            out["fiscal_year"] = err(exc)
        # L4 the screen's EDGAR fundamentals
        try:
            snap = compute_fundamental_snapshot(cik, whole, as_of=TODAY)
            out["screen_fundamentals"] = {
                k: df(getattr(snap, k))
                for k in (
                    "op_income_sign",
                    "fcf_sign",
                    "net_leverage",
                    "net_debt_to_ocf",
                    "ebitda_annual",
                    "net_debt",
                    "eps_diluted_annual",
                )
            }
        except Exception as exc:  # noqa: BLE001
            out["screen_fundamentals"] = err(exc)
        # L5 anchor gates (R1's EDGAR legs, in compute_anchor's order)
        try:
            rev_s, conflicts = an._total_revenue_series(facts)
            oi_s = mc.annual_series(facts, "operating_income")
            a: dict[str, Any] = {
                "revenue_tag": rev_s.tag if rev_s else None,
                "revenue_years": rev_s.years[-12:] if rev_s else [],
                "revenue_tag_conflicts": [cut(c, 200) for c in conflicts][:3],
                "revenue_conflicts_total": len(conflicts),
                "opinc_tag": oi_s.tag,
                "opinc_years": oi_s.years[-12:],
            }
            if rev_s is None:
                a["gate"] = "ANCHOR_UNRESOLVED: no reliable total-revenue tag"
            else:
                ma = mc.margin_anchor(rev_s, oi_s)
                a["margin_median"] = ma.median
                a["margin_years"] = ma.n_years
                a["margin_by_year_last5"] = {
                    y: round(v, 4) for y, v in sorted(ma.by_year.items())[-5:]
                }
                if ma.median is None:
                    a["gate"] = "ANCHOR_UNRESOLVED: operating margin not computable"
                elif ma.median <= 0:
                    a["gate"] = "R2_NEEDED: no positive operating margin over history"
                else:
                    a["gate"] = (
                        "R1 EDGAR legs pass (margin>0); R1 still needs CIQ's own-history "
                        "EV/EBITDA band, else recipe 'unknown'"
                    )
            da = an._latest_dep_amort(facts)
            a["d_and_a"] = (
                da if isinstance(da, str) else {"value": da[0], "tag": da[1], "end": da[2]}
            )
            fcf = an._latest_fcf(facts)
            a["fcf"] = fcf if isinstance(fcf, str) else {"value": fcf[0], "src": cut(fcf[1], 120)}
            out["anchor_gates"] = a
        except Exception as exc:  # noqa: BLE001
            out["anchor_gates"] = err(exc)
        # L6 net debt — the SIC rule first, then the builder (both bases the anchor reads)
        try:
            na = nd.not_applicable(sic)
            n = nd.net_debt(facts, as_of=TODAY)
            lev = n.value(nd.Basis.LEVERAGE) if n is not None else None
            incl = an.lease_inclusive_net_debt(facts, as_of=TODAY)
            out["net_debt"] = {
                "sic_rule": na,
                "builder_refusal": n.refusal if n else "None returned",
                "leverage_usd": lev,
                "at": str(n.at) if n else None,
                "debt_usd": n.debt if n else None,
                "cash_usd": n.cash.value if n else None,
                "operating_leases_usd": n.operating_leases if n else None,
                "lease_inclusive_musd": incl[0],
                "lease_inclusive_src": cut(incl[1], 200),
            }
        except Exception as exc:  # noqa: BLE001
            out["net_debt"] = err(exc)
    # L7 share count (the mechanical reader) and the ADS ratio when the line is depositary
    try:
        cnt = _edgar_shares_outstanding(ed, cik, as_of=TODAY, http=sec_http())
        src = ident.model_dump() if hasattr(ident, "model_dump") else {}
        out["shares"] = {"edgar_count": cnt}
        try:
            r = res.ads_ratio(cik, TODAY)
            out["shares"]["ads_ratio"] = {
                "status": r.status,
                "ordinary_per_ads": r.ordinary_per_ads,
                "form": r.form,
                "reason": cut(r.reason, 200),
            }
        except Exception as exc:  # noqa: BLE001
            out["shares"]["ads_ratio"] = err(exc)
        out["shares"]["note_ads"] = (
            "ads_ratio is read for every line here; only a depositary line uses it"
        )
        del src
    except Exception as exc:  # noqa: BLE001
        out["shares"] = err(exc)
    # L8 the event rule's filings (1 year), and the spacing that bounds a CIQ export's life
    try:
        start = TODAY - dt.timedelta(days=365)
        periodic = ed.recent_filings(cik, forms=(*EVENT_FORMS, *EVENT_ANY_FORMS), since=start)
        prints = [f for f in eight_k_events(ed, cik, since=start) if EVENT_8K_ITEM in f.items]
        evs = sorted({(f.filing_date, f.form) for f in [*periodic, *prints]})
        days = [d for d, _ in evs]
        gaps = [(b - a).days for a, b in zip(days, days[1:], strict=False)]
        out["event_rule"] = {
            "events_365": len(evs),
            "by_form": {f: sum(1 for _, g in evs if g == f) for f in {g for _, g in evs}},
            "median_gap_days": statistics.median(gaps) if gaps else None,
            "max_gap_days": max(gaps) if gaps else None,
            "last_event": str(days[-1]) if days else None,
        }
    except Exception as exc:  # noqa: BLE001
        out["event_rule"] = err(exc)
    # L9 price
    try:
        sym = ident.eod_symbol or to_eod_symbol(ticker)
        bar = prices().get(sym)
        out["price"] = {
            "symbol": sym,
            "close_2026_11_18": bar.close if bar else None,
            "in_grouped_daily": bar is not None,
        }
        eps = (out.get("screen_fundamentals") or {}).get("eps_diluted_annual", {}).get("value")
        if bar and isinstance(eps, (int, float)) and eps:
            out["price"]["close_over_edgar_eps"] = round(bar.close / eps, 3)
        count = (out.get("shares") or {}).get("edgar_count")
        if bar and isinstance(count, (int, float)):
            out["price"]["cap_close_x_edgar_count"] = bar.close * count
    except Exception as exc:  # noqa: BLE001
        out["price"] = err(exc)
    return out


def main(argv: list[str]) -> None:
    force = "--force" in argv
    for t in [a for a in argv if not a.startswith("--")]:
        p = PDIR / f"{t}.json"
        if p.exists() and not force:
            continue
        try:
            o = probe(t)
        except Exception as exc:  # noqa: BLE001
            o = {"ticker": t, "fatal": err(exc)}
        p.write_text(json.dumps(o, indent=1, default=str))
        print(t, "done", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
