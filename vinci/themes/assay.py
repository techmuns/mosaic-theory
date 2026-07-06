"""Earliness-assay v0 harness — deterministic reads only (EDGAR full-text + Polygon), ZERO LLM.

Two axes per candidate theme, POINT-IN-TIME: (x) disclosed-activity velocity — new filers first-
mentioning the terms per quarter (efts); (y) an obvious basket's median excess re-rating vs IWM AND
SPY (Polygon, as-of only). Each quarter is placed in a QUADRANT (EARLY / PRICED / QUIET / NARRATIVE)
under a boundary SENSITIVITY GRID, and EARLY residence is measured per combo.

Assemble-not-conclude: the output is an ``AssayCard`` — no score, no rank, no verdict. Insufficient
data is ``None`` + a logged reason, NEVER a silent 0.0. Cache-first: every raw efts + grouped-daily
response is cached (``data/assay_cache/`` and the shared http cache), so a re-run is network-free.

The pure quadrant/residence math (``classify_quadrant``, ``early_residence``, the quarter helpers,
``new_filers_by_quarter``) has NO I/O and is unit-tested directly; the network readers take injected
clients so the module imports without touching the network.
"""

from __future__ import annotations

import json
import re
import statistics
import urllib.parse
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Protocol, cast

from vinci.netcache import CachedHttp, HttpError
from vinci.themes.assay_schemas import (
    AssayCard,
    BasketMember,
    CandidateSpec,
    QuarterRead,
    Residence,
)
from vinci.universe import recent_share_periods

_EFTS = "https://efts.sec.gov/LATEST/search-index"  # same literal as exposure.py / edgar/client.py
_ONE_WEEK = 7 * 24 * 3600
_CT_URL = "https://www.sec.gov/files/company_tickers.json"  # CIK<->ticker for SEC filers

# -- the verbatim mechanical basket rule, printed on every card --
THE_BASKET_RULE = (
    "At as-of, rank filers by DISTINCT filings mentioning ANY of the candidate's terms over the "
    "trailing 8 quarters (EDGAR full-text). Map CIK->ticker (SEC company_tickers). Keep common "
    "stocks whose as-of market cap (XBRL cover-page shares x Polygon close) is $100M-$10B (the "
    "Component-A cap band). Take the top 10 by mention count. Purely mechanical + ex-ante: no "
    "discretion, no forward information, no price used in selection."
)

# -- the pre-committed KILL CRITERION, printed VERBATIM in the retrocast --
KILL_CRITERION = (
    "If the retrocasts show that NEITHER ai-datacenter NOR defense-demand-shift had >=2 "
    "consecutive quarters of EARLY-quadrant residence before their re-rates - under ANY "
    "boundary combo in the sensitivity grid - the early-window premise is falsified and the "
    "assay build STOPS at this harness."
)

# -- boundary sensitivity grid: price-flat threshold x activity-rising test --
_PRICE_FLAT: dict[str, float] = {"flat20": 0.20, "flat30": 0.30}  # excess < threshold => price-flat
_ACTIVITY: tuple[str, ...] = ("medrise", "sloperise")  # > trailing-4q median | positive 4q slope
COMBOS: tuple[str, ...] = tuple(f"{p}_{a}" for p in _PRICE_FLAT for a in _ACTIVITY)
_REFERENCE_COMBO = "flat20_medrise"  # strictest; used for the single divergence-age summary

CAP_MIN, CAP_MAX = 100e6, 10e9
_8K_FAMILY = {"8-K", "6-K", "8-K/A"}  # 8-K / press family
_10K_FAMILY = {"10-K", "10-Q", "20-F", "40-F", "10-K/A", "10-Q/A"}  # periodic family
_BASELINE_LAG_Q = 8  # the price baseline is (as_of - 8 quarters)

Quadrant = str  # "EARLY" | "PRICED" | "QUIET" | "NARRATIVE" | "UNKNOWN"


class PriceCloseFn(Protocol):
    """Injected as-of close lookup: (ticker, day) -> close|None (None = no bar, never faked)."""

    def __call__(self, ticker: str, day: date) -> float | None: ...


# ==================================================================================================
# Quarter helpers (pure)
# ==================================================================================================
def quarter_of(d: date) -> tuple[int, int]:
    return d.year, (d.month - 1) // 3 + 1


def quarter_label(y: int, q: int) -> str:
    return f"{y}Q{q}"


def quarter_start(y: int, q: int) -> date:
    return date(y, 3 * (q - 1) + 1, 1)


def quarter_end(y: int, q: int) -> date:
    return date(y, 12, 31) if q == 4 else date(y, 3 * q + 1, 1) - timedelta(days=1)


def add_quarters(y: int, q: int, n: int) -> tuple[int, int]:
    """Shift (y, q) by n quarters (n may be negative)."""
    idx = (y * 4 + (q - 1)) + n
    return idx // 4, idx % 4 + 1


def quarters_ending(as_of: date, n: int) -> list[tuple[int, int]]:
    """The n (year, quarter) pairs ending at the quarter that CONTAINS as_of, oldest first."""
    ey, eq = quarter_of(as_of)
    out = [add_quarters(ey, eq, -i) for i in range(n)]
    return list(reversed(out))


# ==================================================================================================
# Velocity read (efts) — cache-first, loud degradation on a page cap
# ==================================================================================================
def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "term"


def _form_family(src: dict[str, Any]) -> str:
    ft = src.get("file_type") or (src.get("root_forms") or [None])[0] or ""
    ft = str(ft).upper()
    if ft in _8K_FAMILY:
        return "8k"
    if ft in _10K_FAMILY:
        return "10k"
    return "other"


def _efts_page(
    efts: CachedHttp, phrase: str, startdt: str, enddt: str, frm: int
) -> tuple[list[tuple[str, str, str]], int]:
    """One efts page: [(cik10, file_date, form_family)] + total. Fail-loud on a throttle body."""
    q = urllib.parse.quote(f'"{phrase}"')
    url = f"{_EFTS}?q={q}&startdt={startdt}&enddt={enddt}&from={frm}"
    data = cast(dict[str, Any], efts.get_json(url, ttl_seconds=_ONE_WEEK))
    hits = data.get("hits")
    if not isinstance(hits, dict) or "hits" not in hits:
        raise HttpError(f"efts returned no hits structure (throttled/error?): {str(data)[:180]}")
    rows: list[tuple[str, str, str]] = []
    for h in hits["hits"]:
        src = h.get("_source", {})
        cik = (src.get("ciks") or [None])[0]
        if cik is not None:
            rows.append((str(cik).zfill(10), str(src.get("file_date", "")), _form_family(src)))
    return rows, int(hits.get("total", {}).get("value", 0))


def term_quarter_read(
    efts: CachedHttp, cache_root: Path, phrase: str, y: int, q: int, *, max_pages: int
) -> dict[str, Any]:
    """First-mention dates + total + form split for ONE (term, quarter), cached under
    ``cache_root/<slug>__<yQq>.json``. ``capped`` is True when total exceeded the page cap — the
    per-CIK enumeration (thus the new-filer count) is then a LOWER BOUND (loud, never faked)."""
    cache_root.mkdir(parents=True, exist_ok=True)
    path = cache_root / f"{_slug(phrase)}__{y}Q{q}.json"
    if path.exists():
        return cast(dict[str, Any], json.loads(path.read_text()))
    startdt, enddt = quarter_start(y, q).isoformat(), quarter_end(y, q).isoformat()
    first_dates: dict[str, str] = {}
    cik_counts: Counter[str] = Counter()
    forms: Counter[str] = Counter()
    total = 0
    capped = False
    for page in range(max_pages):
        rows, total = _efts_page(efts, phrase, startdt, enddt, page * 100)  # efts page = 100 hits
        for cik, fdate, fam in rows:
            forms[fam] += 1
            cik_counts[cik] += 1
            if cik not in first_dates or (fdate and fdate < first_dates[cik]):
                first_dates[cik] = fdate
        if (page + 1) * 100 >= total:  # stop by POSITION vs total — cik-less hits never truncate
            break
    else:
        capped = True  # ran the full page cap without reaching total → enumeration is a LOWER BOUND
    out = {"first_dates": first_dates, "cik_counts": dict(cik_counts), "total": total,
           "forms": dict(forms), "capped": capped}
    path.write_text(json.dumps(out))
    return out


def new_filers_by_quarter(
    cik_first_quarter: dict[str, tuple[int, int]], ordered_quarters: list[tuple[int, int]]
) -> dict[tuple[int, int], int]:
    """Given each CIK's earliest-mention quarter, count NEW filers per quarter (pure)."""
    counts: dict[tuple[int, int], int] = dict.fromkeys(ordered_quarters, 0)
    for yq in cik_first_quarter.values():
        if yq in counts:
            counts[yq] += 1
    return counts


# ==================================================================================================
# Quadrant + residence (pure — the load-bearing math, unit-tested directly)
# ==================================================================================================
def _activity_rising(velocity: list[int], i: int, test: str) -> bool | None:
    """Is quarter i 'activity-rising'? None if the trailing-4q window is incomplete (data gap)."""
    if i < 4:
        return None
    prior = velocity[i - 4 : i]
    if test == "medrise":
        return velocity[i] > statistics.median(prior)
    # sloperise: positive OLS slope over the trailing 4 quarters (x = 0..3)
    xs = [0.0, 1.0, 2.0, 3.0]
    ys = [float(v) for v in prior]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    cov = sum((x - mx) * (yv - my) for x, yv in zip(xs, ys, strict=True))
    slope = cov / denom if denom else 0.0
    return slope > 0


def classify_quadrant(
    excess_iwm: float | None, excess_spy: float | None, rising: bool | None, flat_threshold: float
) -> Quadrant:
    """Place one quarter in the velocity x price quadrant under one boundary combo.

    price-flat = excess vs BOTH benchmarks < threshold. EARLY = rising + flat; PRICED = rising +
    moved; QUIET = thin + flat; NARRATIVE = thin + moved. UNKNOWN on a price/activity gap."""
    if excess_iwm is None or excess_spy is None or rising is None:
        return "UNKNOWN"
    flat = excess_iwm < flat_threshold and excess_spy < flat_threshold
    if rising and flat:
        return "EARLY"
    if rising and not flat:
        return "PRICED"
    if not rising and flat:
        return "QUIET"
    return "NARRATIVE"


def early_residence(quadrants: list[Quadrant]) -> Residence:
    """Longest run of consecutive EARLY quarters + total EARLY quarters (pure)."""
    longest = run = total = 0
    for qd in quadrants:
        if qd == "EARLY":
            run += 1
            total += 1
            longest = max(longest, run)
        else:
            run = 0
    return Residence(longest_early_run=longest, total_early_quarters=total)


def divergence_age(quadrants: list[Quadrant]) -> int | None:
    """Quarters of standing activity-vs-price divergence to the as-of: the length of the trailing
    contiguous EARLY run ending at the last quarter. None if the last quarter is not EARLY."""
    age = 0
    for qd in reversed(quadrants):
        if qd == "EARLY":
            age += 1
        else:
            break
    return age or None


# ==================================================================================================
# Basket construction + pricing (network via injected clients)
# ==================================================================================================
def company_ticker_map(sec_http: CachedHttp) -> dict[str, str]:
    """{cik10: TICKER} for all SEC filers with a ticker (one cached bulk pull). Point-in-time note:
    reflects the CURRENT ticker for a CIK (SEC does not publish historical ticker maps here)."""
    data = cast(dict[str, Any], sec_http.get_json(_CT_URL, ttl_seconds=_ONE_WEEK))
    out: dict[str, str] = {}
    for rec in data.values():
        cik = rec.get("cik_str")
        tick = rec.get("ticker")
        if cik is not None and tick:
            out[str(cik).zfill(10)] = str(tick).upper()
    return out


def build_basket(
    mention_counts: Counter[str],
    ct_map: dict[str, str],
    shares_by_cik: dict[str, float],
    close_at: dict[str, float | None],
) -> tuple[list[BasketMember], list[str]]:
    """Top-10 obvious basket by mention count, cap-banded ($100M-$10B). close_at = {ticker: close}
    at as-of. Returns (members, drops); each drop carries a logged reason (never a silent gap)."""
    members: list[BasketMember] = []
    drops: list[str] = []
    for cik, n in mention_counts.most_common():
        if len(members) >= 10:
            break
        ticker = ct_map.get(cik)
        if not ticker:
            drops.append(f"CIK {cik} (n={n}): no ticker in company_tickers (private/foreign)")
            continue
        shares = shares_by_cik.get(cik)
        price = close_at.get(ticker)
        if shares is None or price is None:
            members_method = (
                f"dropped: no {'shares (XBRL)' if shares is None else ''}"
                f"{' & ' if shares is None and price is None else ''}"
                f"{'price (Polygon)' if price is None else ''} at as-of"
            )
            drops.append(f"{ticker} (CIK {cik}, n={n}): {members_method}")
            continue
        cap = shares * price
        if not (CAP_MIN <= cap <= CAP_MAX):
            drops.append(f"{ticker} (n={n}): cap ${cap / 1e9:.2f}B outside $100M-$10B band")
            continue
        members.append(BasketMember(
            ticker=ticker, cik=cik, mention_count=n, cap_asof=cap,
            cap_method="xbrl_cover_shares x polygon_close"))
    return members, drops


def basket_cumret(
    tickers: list[str], baseline: date, target: date, price_fn: PriceCloseFn
) -> float | None:
    """Median cumulative return of the basket from ``baseline`` to ``target``. None if fewer than
    3 members have BOTH closes — never fabricates or partially-fills."""
    rets: list[float] = []
    for t in tickers:
        p0, p1 = price_fn(t, baseline), price_fn(t, target)
        if p0 and p1 and p0 > 0:
            rets.append(p1 / p0 - 1.0)
    return statistics.median(rets) if len(rets) >= 3 else None


def _benchmark_cumret(
    sym: str, baseline: date, target: date, price_fn: PriceCloseFn
) -> float | None:
    p0, p1 = price_fn(sym, baseline), price_fn(sym, target)
    return (p1 / p0 - 1.0) if (p0 and p1 and p0 > 0) else None


class SharesSource(Protocol):
    """The one EDGAR method the assay needs — a bulk XBRL cover-page shares frame merge."""

    def shares_outstanding_by_cik(self, periods: Any) -> dict[str, float]: ...


# ==================================================================================================
# Orchestration — one candidate's card (network via injected clients)
# ==================================================================================================
def assay_candidate(
    candidate: CandidateSpec,
    as_of: date,
    quarters: int,
    *,
    efts: CachedHttp,
    sec_http: CachedHttp,
    edgar: SharesSource,
    price_fn: PriceCloseFn,
    cache_root: Path,
    max_pages: int = 8,
) -> AssayCard:
    """Assemble one candidate's AssayCard at ``as_of`` over N quarters. Deterministic reads only
    (efts + Polygon via ``price_fn``); no LLM. Cache-first (re-runs are network-free)."""
    qs = quarters_ending(as_of, quarters)  # oldest first
    trailing8 = set(qs[-_BASELINE_LAG_Q:])  # basket ranks over the trailing 8 quarters
    cik_first: dict[str, str] = {}
    cik_counts: Counter[str] = Counter()
    total_by_q: dict[tuple[int, int], int] = dict.fromkeys(qs, 0)
    f8_by_q: dict[tuple[int, int], int] = dict.fromkeys(qs, 0)
    f10_by_q: dict[tuple[int, int], int] = dict.fromkeys(qs, 0)
    capped: list[str] = []
    for term in candidate.terms:
        for y, q in qs:
            r = term_quarter_read(efts, cache_root, term, y, q, max_pages=max_pages)
            total_by_q[y, q] += int(r["total"])
            f8_by_q[y, q] += int(r["forms"].get("8k", 0))
            f10_by_q[y, q] += int(r["forms"].get("10k", 0))
            if r["capped"]:
                capped.append(f"{term} {y}Q{q}")
            for cik, fdate in r["first_dates"].items():
                if cik not in cik_first or (fdate and fdate < cik_first[cik]):
                    cik_first[cik] = fdate
            if (y, q) in trailing8:
                for cik, c in r["cik_counts"].items():
                    cik_counts[cik] += int(c)

    cik_first_q = {cik: quarter_of(date.fromisoformat(d)) for cik, d in cik_first.items() if d}
    new_by_q = new_filers_by_quarter(cik_first_q, qs)
    velocity = [new_by_q[yq] for yq in qs]

    ct = company_ticker_map(sec_http)
    # POINT-IN-TIME: reuse the universe helper's 40-day filing-lag gate so basket cap-banding never
    # sees shares disclosed AFTER as_of (no lookahead — a future-quarter frame is excluded).
    shares = edgar.shares_outstanding_by_cik(recent_share_periods(as_of))
    close_at: dict[str, float | None] = {
        ct[cik]: price_fn(ct[cik], as_of) for cik in cik_counts if cik in ct
    }
    basket, drops = build_basket(cik_counts, ct, shares, close_at)
    tickers = [m.ticker for m in basket]

    baseline_yq = qs[max(0, len(qs) - 1 - _BASELINE_LAG_Q)]
    baseline_date = quarter_end(*baseline_yq)

    reads: list[QuarterRead] = []
    price_gap = False
    for i, (y, q) in enumerate(qs):
        qe = quarter_end(y, q)
        b_cum = basket_cumret(tickers, baseline_date, qe, price_fn) if tickers else None
        iwm = _benchmark_cumret("IWM", baseline_date, qe, price_fn)
        spy = _benchmark_cumret("SPY", baseline_date, qe, price_fn)
        ex_iwm = b_cum - iwm if (b_cum is not None and iwm is not None) else None
        ex_spy = b_cum - spy if (b_cum is not None and spy is not None) else None
        gaps: list[str] = []
        if b_cum is None:
            gaps.append("basket price gap: <3 members priced at baseline/quarter-end")
        if iwm is None or spy is None:
            gaps.append("benchmark price gap: IWM/SPY close unavailable (Polygon history window)")
        if ex_iwm is None or ex_spy is None:
            price_gap = True
        quad: dict[str, str] = {}
        for p_name, thresh in _PRICE_FLAT.items():
            for a_name in _ACTIVITY:
                quad[f"{p_name}_{a_name}"] = classify_quadrant(
                    ex_iwm, ex_spy, _activity_rising(velocity, i, a_name), thresh)
        reads.append(QuarterRead(
            quarter=quarter_label(y, q), new_filers=new_by_q[y, q],
            total_mentions=total_by_q[y, q], mentions_8k_family=f8_by_q[y, q],
            mentions_10k_family=f10_by_q[y, q], basket_excess_iwm=ex_iwm,
            basket_excess_spy=ex_spy, quadrant_by_combo=quad, data_gaps=gaps))

    residence = {c: early_residence([r.quadrant_by_combo[c] for r in reads]) for c in COMBOS}
    div_age = divergence_age([r.quadrant_by_combo[_REFERENCE_COMBO] for r in reads])

    caveats = [
        "POINT-IN-TIME: efts filings + Polygon closes are read as-of; no forward information used.",
        "Forward multiples / valuation are UNAVAILABLE in this stack (v0 reads filings+prices).",
        f"Basket cap = XBRL cover-page shares x Polygon close (best-effort); {len(drops)} dropped.",
        "v0 limits: no commitment/'money' extraction (8-K terms = v1); no attention prior; the "
        "form-family split is PRINTED, not weighted; ZERO LLM calls.",
    ]
    if capped:
        caveats.append(
            f"LOUD DEGRADATION: {len(capped)} term-quarter(s) hit the {max_pages}-page efts cap; "
            f"new-filer counts there are a LOWER BOUND (e.g. {capped[:3]}).")
    if price_gap:
        caveats.append("PRICE GAP: some quarters lack basket/benchmark closes (Polygon history "
                       "window) -> those quadrants are UNKNOWN, not classified.")
    caveats.extend(f"basket drop: {d}" for d in drops[:12])
    return AssayCard(
        candidate_key=candidate.key, as_of=as_of.isoformat(), quarters=tuple(reads),
        basket=tuple(basket), basket_rule=THE_BASKET_RULE, residence_by_combo=residence,
        divergence_age_quarters=div_age, caveats=caveats)


def kill_verdict(cards: list[AssayCard]) -> tuple[str, list[str]]:
    """Honest three-way verdict over the retrocast cards. PASS if any card+combo shows >=2
    consecutive EARLY quarters; INCONCLUSIVE if none does but a price gap prevented classifying
    (never a false FALSIFIED); FALSIFIED only when price is present and no >=2 EARLY run exists."""
    evidence: list[str] = []
    passed = False
    for card in cards:
        for combo, r in card.residence_by_combo.items():
            if r.longest_early_run >= 2:
                evidence.append(
                    f"{card.candidate_key} as-of {card.as_of}: {combo} longest EARLY run="
                    f"{r.longest_early_run}")
                passed = True
    if passed:
        return "PASS (survives — early-window premise NOT falsified)", evidence
    gapped = any("PRICE GAP" in c for card in cards for c in card.caveats)
    if gapped:
        return "INCONCLUSIVE — price axis gapped; the kill criterion cannot be evaluated", evidence
    return (
        "FALSIFIED — no >=2q EARLY residence under any combo (assay build STOPS at this harness)",
        evidence,
    )


def render_markdown(card: AssayCard) -> str:
    """The human-facing card: quarterly table, basket + provenance, residence per combo, caveats."""
    out = [f"# Earliness assay v0 — {card.candidate_key} (as-of {card.as_of})", "",
           f"**Basket rule:** {card.basket_rule}", "",
           "## Quarterly read (velocity x price)", "",
           "| quarter | new filers | mentions | 8-K fam | 10-K fam | vs IWM | vs SPY | quadrant "
           f"({_REFERENCE_COMBO}) |", "|---|---|---|---|---|---|---|---|"]
    for r in card.quarters:
        ei = "—" if r.basket_excess_iwm is None else f"{r.basket_excess_iwm:+.0%}"
        es = "—" if r.basket_excess_spy is None else f"{r.basket_excess_spy:+.0%}"
        out.append(
            f"| {r.quarter} | {r.new_filers} | {r.total_mentions} | {r.mentions_8k_family} "
            f"| {r.mentions_10k_family} | {ei} | {es} | {r.quadrant_by_combo[_REFERENCE_COMBO]} |")
    out += ["", "## Obvious basket (mechanical, ex-ante)", ""]
    if card.basket:
        out += ["| ticker | CIK | mentions | cap | method |", "|---|---|---|---|---|"]
        for m in card.basket:
            cap = "—" if m.cap_asof is None else f"${m.cap_asof / 1e9:.2f}B"
            out.append(f"| {m.ticker} | {m.cik} | {m.mention_count} | {cap} | {m.cap_method} |")
    else:
        out.append("_(empty — no members survived the cap band / CIK->ticker / price gates)_")
    out += ["", "## EARLY residence per boundary combo", "",
            "| combo | longest EARLY run | total EARLY quarters |", "|---|---|---|"]
    for c in COMBOS:
        rr = card.residence_by_combo[c]
        out.append(f"| {c} | {rr.longest_early_run} | {rr.total_early_quarters} |")
    age = "—" if card.divergence_age_quarters is None else str(card.divergence_age_quarters)
    out += ["", f"**Divergence age (quarters, {_REFERENCE_COMBO}):** {age}", "", "## Caveats", ""]
    out += [f"- {c}" for c in card.caveats]
    return "\n".join(out) + "\n"


def emit(card: AssayCard, out_dir: Path) -> Path:
    """Write the JSON + markdown card under ``out_dir``; return the JSON path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{card.candidate_key}__asof_{card.as_of}"
    (out_dir / f"{stem}.md").write_text(render_markdown(card))
    jpath = out_dir / f"{stem}.json"
    jpath.write_text(json.dumps(card.model_dump(mode="json"), indent=2))
    return jpath
