"""The forward-return engine: one ledger row per (publication, company) and per horizon.

TIMING (operator brief §4, and the CIQ pilot's own convention so the two reconcile):
- entry = the close of the first exchange session STRICTLY AFTER the public date (release time is
  never known here, so the publication day's own close is never assumed tradable);
- target = ``EDATE(entry, months)`` — calendar months, clamped to month-end like Excel's EDATE
  (the pilot's 'Target date' formula);
- exit = the first exchange session ON OR AFTER the target;
- a horizon is computed only when the exit session is on/before the last completed session AND
  the stock and the benchmark both have a real value on the entry and the exit session.

RETURNS. ``stock = adjClose_exit / adjClose_entry - 1``; ``excess = stock - benchmark``. The
primary benchmark is the CIQ MSCI World Net series; the S&P 500 Net (CIQ) is the regional
comparison for US listings; the SPDR sector ETF of the stock's SIC-derived sector is the
sector-adjusted comparison (PROXY).
"""

from __future__ import annotations

import bisect
import calendar
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from vinci.research_audit.benchmarks import Benchmark
from vinci.research_audit.classify import (
    NOT_LISTED_TEXT,
    Availability,
    Direction,
    direction_of,
    listing_of,
    role_of,
    signal_id_of,
)
from vinci.research_audit.prices import Series
from vinci.research_audit.workbook import AuditWorkbook, Mention, Publication
from vinci.sectors import industry_for_sic

HORIZONS = (6, 9, 12)
US_MICS = frozenset({"XNYS", "XNAS", "XASE", "ARCX", "BATS", "IEXG"})
STOCK_TYPES = frozenset({"CS"})

# Ledger statuses — every non-COMPLETE row says why, in one of these words.
COMPLETE = "COMPLETE"
NOT_SCORED_NONDIRECTIONAL = "NOT_SCORED_NONDIRECTIONAL"
UNAVAILABLE_POLYGON = "UNAVAILABLE_POLYGON"
NOT_LISTED = "NOT_LISTED"
BLOCKED_MONTH_ONLY_DATE = "BLOCKED_MONTH_ONLY_DATE"
IDENTITY_UNVERIFIED = "IDENTITY_UNVERIFIED"
INCOMPLETE_HORIZON = "INCOMPLETE_HORIZON"
NO_PRICE_AT_ENTRY = "NO_PRICE_AT_ENTRY"
NO_PRICE_AT_EXIT = "NO_PRICE_AT_EXIT"
DATA_DISCONTINUITY = "DATA_DISCONTINUITY"
BENCHMARK_MISSING = "BENCHMARK_MISSING"
DUPLICATE_MENTION = "DUPLICATE_MENTION_IN_PUBLICATION"


def edate(d: date, months: int) -> date:
    """Excel ``EDATE``: same day-of-month ``months`` later, clamped to that month's last day."""
    y, m0 = divmod(d.month - 1 + months, 12)
    year, month = d.year + y, m0 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def session_after(sessions: list[date], d: date) -> date | None:
    i = bisect.bisect_right(sessions, d)
    return sessions[i] if i < len(sessions) else None


def session_on_or_after(sessions: list[date], d: date) -> date | None:
    i = bisect.bisect_left(sessions, d)
    return sessions[i] if i < len(sessions) else None


# --- identity ---------------------------------------------------------------------------------

_STOP = frozenset({
    "inc", "incorporated", "corp", "corporation", "co", "company", "plc", "ltd", "limited",
    "the", "class", "a", "b", "c", "common", "stock", "shares", "share", "ordinary", "lp", "l",
    "p", "n", "v", "nv", "s", "sa", "ag", "se", "new", "units", "unit", "representing", "&",
    "partnership", "partner", "interests",
})


def _tokens(name: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9&]+", name.lower()) if t not in _STOP}


@dataclass(frozen=True)
class Identity:
    audit_ticker: str
    company: str
    status: str
    provider_ticker: str = ""
    provider_name: str = ""
    primary_exchange: str = ""
    security_type: str = ""
    currency: str = ""
    cik: str = ""
    composite_figi: str = ""
    share_class_figi: str = ""
    list_date: str = ""
    as_of: str = ""
    sic_code: str = ""
    sic_description: str = ""
    sector: str = "UNKNOWN"
    industry: str = "UNKNOWN"
    detail: str = ""
    listing_mic: str = ""
    listing_currency: str = ""
    alternatives: tuple[str, ...] = ()


def verify_identity(audit_ticker: str, company: str, details: dict[str, Any] | None,
                    as_of: date | None, first_entry: date | None,
                    alternatives: list[dict[str, Any]] | None = None,
                    sec: tuple[str, str] | None = None) -> Identity:
    """Polygon metadata vs the workbook's company. Every check must pass; a failure is reported
    with what Polygon said, and the name is not priced.

    ``sec`` is SEC's own (CIK, registrant title) for the ticker. It can rescue ONLY the name check,
    and only when Polygon's CIK equals SEC's CIK for the ticker and SEC's registrant title matches
    the workbook company — two independent sources agreeing on the issuer."""
    lst = listing_of(audit_ticker)
    # Name search is a substring match ("SAP" returns 50 unrelated lines); keep only results whose
    # name carries every significant token of the company, and say how many were dropped.
    found = alternatives or []
    want_alt = _tokens(company)
    alts = tuple(
        f"{a.get('ticker')} | {a.get('name')} | market={a.get('market')} "
        f"type={a.get('type')} | {a.get('primary_exchange')}"
        for a in found if want_alt and want_alt <= _tokens(str(a.get("name") or ""))
    )
    if lst.availability is Availability.NOT_LISTED:
        return Identity(audit_ticker, company, NOT_LISTED, detail="private company; not investable")
    if lst.availability is Availability.UNAVAILABLE_POLYGON:
        return Identity(
            audit_ticker, company, UNAVAILABLE_POLYGON, listing_mic=lst.exchange_mic,
            listing_currency=lst.currency,
            detail=(f"primary listing {lst.exchange_mic} ({lst.currency}) — Polygon carries US "
                    f"exchanges + US OTC only; name search returned {len(found)} line(s), "
                    f"{len(alts)} naming this issuer — recorded, NOT substituted"),
            alternatives=alts,
        )
    if details is None:
        return Identity(audit_ticker, company, IDENTITY_UNVERIFIED,
                        as_of=as_of.isoformat() if as_of else "",
                        detail="Polygon returned no ticker record at the as-of date")
    sic = str(details.get("sic_code") or "")
    ident = Identity(
        audit_ticker=audit_ticker, company=company, status="VERIFIED_POLYGON",
        provider_ticker=str(details.get("ticker") or ""), provider_name=str(details.get("name")),
        primary_exchange=str(details.get("primary_exchange") or ""),
        security_type=str(details.get("type") or ""),
        currency=str(details.get("currency_name") or "").upper(),
        cik=str(details.get("cik") or ""), composite_figi=str(details.get("composite_figi") or ""),
        share_class_figi=str(details.get("share_class_figi") or ""),
        list_date=str(details.get("list_date") or ""), as_of=as_of.isoformat() if as_of else "",
        sic_code=sic, sic_description=str(details.get("sic_description") or ""),
        industry=industry_for_sic(sic) if sic else "UNKNOWN",
        listing_mic=str(details.get("primary_exchange") or ""), listing_currency="USD",
    )
    problems: list[str] = []
    if ident.provider_ticker != audit_ticker:
        problems.append(f"ticker {ident.provider_ticker!r} != {audit_ticker!r}")
    want, got = _tokens(company), _tokens(ident.provider_name)
    note = ""
    if not want or not want <= got:
        sec_cik, sec_title = sec or ("", "")
        if sec and sec_cik == ident.cik.zfill(10) and want and want <= _tokens(sec_title):
            note = (f"; Polygon name {ident.provider_name!r} fails the name check, identity "
                    f"confirmed by SEC company_tickers: CIK {sec_cik} = {sec_title!r}")
        else:
            problems.append(f"name {ident.provider_name!r} does not contain {company!r}"
                            + (f" (SEC: CIK {sec_cik} {sec_title!r})" if sec else ""))
    if ident.primary_exchange not in US_MICS:
        problems.append(f"primary exchange {ident.primary_exchange!r} not a US venue")
    if ident.security_type not in STOCK_TYPES:
        problems.append(f"security type {ident.security_type!r} is not common stock")
    if ident.currency != "USD":
        problems.append(f"currency {ident.currency!r}")
    if first_entry and ident.list_date and date.fromisoformat(ident.list_date) > first_entry:
        problems.append(f"list_date {ident.list_date} after first entry {first_entry}")
    if problems:
        return Identity(**{**ident.__dict__, "status": IDENTITY_UNVERIFIED,
                           "detail": "; ".join(problems)})
    return Identity(**{**ident.__dict__, "detail": "ticker, name, US venue, common stock, USD, "
                                                   "listed before entry" + note})


# --- the ledger -------------------------------------------------------------------------------

@dataclass
class Obs:
    # source
    test_id: str
    pub_id: str
    publisher: str
    title: str
    channel: str
    public_date: str
    date_granularity: str
    underlying_date: str
    first_actionable_date: str
    url: str
    authors: str
    thesis_team: str
    signal_id: str
    thesis_category: str
    thesis_claim: str
    covering_analyst: str
    company: str
    audit_ticker: str
    region: str
    role_text: str
    audit_role: str
    rating: str
    direction: str
    place_in_source: str
    mention_src: str
    publication_src: str
    # instrument
    provider_ticker: str = ""
    identity_status: str = ""
    listing_mic: str = ""
    currency: str = ""
    sector: str = "UNKNOWN"
    industry: str = "UNKNOWN"
    sector_proxy: str = ""
    # horizon
    months: int | None = None
    entry_date: str = ""
    target_date: str = ""
    exit_date: str = ""
    entry_close: float | None = None
    exit_close: float | None = None
    entry_adj_close: float | None = None
    exit_adj_close: float | None = None
    stock_return: float | None = None
    price_return: float | None = None
    world_benchmark: str = ""
    world_entry: float | None = None
    world_exit: float | None = None
    world_return: float | None = None
    excess_vs_world: float | None = None
    # RECONCILIATION ONLY — the workbook's CIQ 'MSCI World Net' series, which validation shows is
    # NOT USD-denominated. Never used in a statistic; kept so the pilot's own figures reconcile.
    ciq_msci_series_return: float | None = None
    excess_vs_ciq_msci_series: float | None = None
    sp500_net_entry: float | None = None
    sp500_net_exit: float | None = None
    sp500_net_return: float | None = None
    excess_vs_sp500: float | None = None
    sector_entry: float | None = None
    sector_exit: float | None = None
    sector_return: float | None = None
    excess_vs_sector: float | None = None
    status: str = ""
    status_detail: str = ""
    price_source: str = ""
    flags: list[str] = field(default_factory=list)

    @property
    def scored_long(self) -> bool:
        return self.direction == Direction.LONG.value


@dataclass(frozen=True)
class EngineInputs:
    wb: AuditWorkbook
    identities: dict[str, Identity]
    series: dict[str, Series]
    sessions: list[date]
    last_session: date
    world: Benchmark  # the USD world benchmark used for scoring
    ciq_world: Benchmark  # reconciliation only (see Obs)
    sp500: Benchmark
    sector_proxies: dict[str, Benchmark]  # sector name -> PROXY benchmark


def _base(m: Mention, p: Publication, wb: AuditWorkbook) -> dict[str, Any]:
    sig_id = signal_id_of(m.pub_id, m.place, m.rating)
    sig = next((s for s in wb.signals if s.signal_id == sig_id), None)
    return {
        "pub_id": m.pub_id,
        "publisher": p.publisher,
        "title": p.title,
        "channel": p.channel,
        "public_date": p.public_date_raw,
        "date_granularity": p.granularity,
        "underlying_date": p.underlying_date_raw,
        "first_actionable_date": p.public_date_raw if p.public_date else "",
        "url": m.url or p.url,
        "authors": p.authors,
        "thesis_team": p.lead,
        "signal_id": sig_id,
        "thesis_category": (f"{sig.signal_id}: {sig.trade_interpretation}" if sig
                         else f"{p.pub_id} {p.channel} (no workbook signal for this row)"),
        "thesis_claim": p.claim,
        "covering_analyst": m.analyst,
        "company": m.company,
        "audit_ticker": m.ticker,
        "region": m.region,
        "role_text": m.role,
        "audit_role": role_of(m.role).value,
        "rating": m.rating,
        "direction": direction_of(m.rating).value,
        "place_in_source": m.place,
        "mention_src": m.src,
        "publication_src": p.src,
    }


def mention_key(m: Mention) -> tuple[str, str]:
    return (m.pub_id, m.company if m.ticker == NOT_LISTED_TEXT else m.ticker)


def primary_mentions(wb: AuditWorkbook) -> dict[tuple[str, str], Mention]:
    """One mention per (publication, ticker): the RATED row when the company is named twice in a
    publication (MS-03 names ServiceNow and Freshworks in Exhibit 6 unrated AND in Exhibit 79
    Equal-Weight), else the first. The other row is kept in the ledger as a duplicate, not dropped.
    Unlisted names share the ticker text 'Private / not listed', so they are keyed by company."""
    out: dict[tuple[str, str], Mention] = {}
    for m in wb.mentions:
        key = mention_key(m)
        cur = out.get(key)
        if cur is None or (direction_of(cur.rating) is Direction.NONDIRECTIONAL
                           and direction_of(m.rating) is not Direction.NONDIRECTIONAL):
            out[key] = m
    return out


def build_ledger(inp: EngineInputs) -> list[Obs]:
    wb = inp.wb
    out: list[Obs] = []
    primary = primary_mentions(wb)
    for m in wb.mentions:
        p = wb.publication(m.pub_id)
        base = _base(m, p, wb)
        direction = direction_of(m.rating)
        keep = primary[mention_key(m)]
        if keep is not m:
            out.append(Obs(test_id="", **base, status=DUPLICATE_MENTION,
                           status_detail=f"same company recorded again at {keep.src} "
                                         f"({keep.rating}); counted once, at that row"))
            continue
        if direction is Direction.NONDIRECTIONAL:
            out.append(Obs(test_id="", **base, status=NOT_SCORED_NONDIRECTIONAL,
                           status_detail="no analyst rating stated — a mention is not a "
                                         "recommendation; no return computed"))
            continue
        ident = inp.identities[m.ticker]
        for months in HORIZONS:
            o = Obs(test_id=f"{m.pub_id}-{m.ticker}-{months}m", **base, months=months)
            o.provider_ticker, o.identity_status = ident.provider_ticker, ident.status
            o.listing_mic, o.currency = ident.listing_mic, ident.listing_currency
            o.sector, o.industry = ident.sector, ident.industry
            _fill(o, ident, p, inp)
            out.append(o)
    _flag_overlaps(out)
    return out


def _fill(o: Obs, ident: Identity, p: Publication, inp: EngineInputs) -> None:
    assert o.months is not None
    if ident.status == UNAVAILABLE_POLYGON:
        o.status, o.status_detail = UNAVAILABLE_POLYGON, ident.detail
        return
    if ident.status == NOT_LISTED:
        o.status, o.status_detail = NOT_LISTED, ident.detail
        return
    pub_day = p.public_date
    if pub_day is None:
        o.status = BLOCKED_MONTH_ONLY_DATE
        o.status_detail = f"public date {p.public_date_raw!r} has {p.granularity} granularity"
        return
    if ident.status != "VERIFIED_POLYGON":
        o.status, o.status_detail = IDENTITY_UNVERIFIED, ident.detail
        return
    entry = session_after(inp.sessions, pub_day)
    if entry is None:
        o.status, o.status_detail = INCOMPLETE_HORIZON, "no session after the public date yet"
        return
    target = edate(entry, o.months)
    exit_ = session_on_or_after(inp.sessions, target)
    o.entry_date, o.target_date = entry.isoformat(), target.isoformat()
    if exit_ is None or exit_ > inp.last_session:
        o.status = INCOMPLETE_HORIZON
        o.status_detail = (f"target {target} is beyond the last completed session "
                           f"{inp.last_session}; not computed")
        return
    o.exit_date = exit_.isoformat()
    s = inp.series[ident.provider_ticker]
    pe, px = s.by_day.get(entry), s.by_day.get(exit_)
    if pe is None or pe.volume <= 0:
        o.status = NO_PRICE_AT_ENTRY
        o.status_detail = f"no traded bar on entry session {entry} (not carried forward)"
        return
    if px is None or px.volume <= 0:
        last = s.points[-1].day if s.points else None
        o.status = NO_PRICE_AT_EXIT
        o.status_detail = (f"no traded bar on exit session {exit_} (series ends {last}) — "
                           f"suspension / delisting / stale quote; not carried forward")
        return
    if why := s.blocked_between(entry, exit_):
        o.status, o.status_detail = DATA_DISCONTINUITY, why
        return
    o.entry_close, o.exit_close = pe.close, px.close
    o.entry_adj_close, o.exit_adj_close = pe.adj_close, px.adj_close
    o.stock_return = px.adj_close / pe.adj_close - 1.0
    o.price_return = None if any(
        q.split_factor != 1.0 for q in s.points if entry < q.day <= exit_
    ) else px.close / pe.close - 1.0
    o.price_source = f"entry {pe.source}; exit {px.source}"
    wr = inp.world.ret(entry, exit_)
    if wr is None:
        o.status = BENCHMARK_MISSING
        o.status_detail = f"{inp.world.code} has no value on {entry} or {exit_}"
        return
    o.world_benchmark = inp.world.code
    o.world_entry, o.world_exit = inp.world.levels[entry], inp.world.levels[exit_]
    o.world_return = wr
    o.excess_vs_world = o.stock_return - wr
    if (cr := inp.ciq_world.ret(entry, exit_)) is not None:
        o.ciq_msci_series_return, o.excess_vs_ciq_msci_series = cr, o.stock_return - cr
    if (sr := inp.sp500.ret(entry, exit_)) is not None:
        o.sp500_net_entry, o.sp500_net_exit = inp.sp500.levels[entry], inp.sp500.levels[exit_]
        o.sp500_net_return, o.excess_vs_sp500 = sr, o.stock_return - sr
    else:
        o.flags.append(f"{inp.sp500.code} missing on entry/exit")
    proxy = inp.sector_proxies.get(o.sector)
    if proxy is None:
        o.flags.append(f"no sector proxy for sector {o.sector!r}")
    else:
        o.sector_proxy = proxy.code
        if (xr := proxy.ret(entry, exit_)) is not None:
            o.sector_entry, o.sector_exit = proxy.levels[entry], proxy.levels[exit_]
            o.sector_return, o.excess_vs_sector = xr, o.stock_return - xr
        else:
            o.flags.append(f"{proxy.code} missing on entry/exit")
    o.status = COMPLETE
    for w in s.warnings:
        if any(tok in w for tok in (entry.isoformat(), exit_.isoformat())):
            o.flags.append(w)


def _flag_overlaps(rows: list[Obs]) -> None:
    """Flag a scored position that overlaps the SAME security held under another signal of the
    same publisher (e.g. SLB and BKR in both MS-01 and MS-02). Both rows stay; they are flagged,
    and the publisher table also reports a first-occurrence-only view."""
    done = [o for o in rows if o.status == COMPLETE]
    for o in done:
        for q in done:
            if q is o or q.audit_ticker != o.audit_ticker or q.publisher != o.publisher \
                    or q.pub_id == o.pub_id:
                continue
            if q.entry_date < o.exit_date and o.entry_date < q.exit_date:
                tag = f"OVERLAPS {q.pub_id} {q.months}m ({q.entry_date}→{q.exit_date})"
                if tag not in o.flags:
                    o.flags.append(tag)
