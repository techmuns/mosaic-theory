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
    TermContribution,
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

# -- v1 additions (computed ALONGSIDE the recorded v0 basis; adoption pending operator sanction) --
_ANCHOR_LOOKBACK_Q = 12  # calendar-anchored new-filer lookback (fixed, window-INDEPENDENT)
_TOP_TERMS = 5  # decomposition: how many top contributing terms to list per quarter
_DERATE_THRESHOLD = -0.20  # excess vs BOTH benchmarks below this ⇒ DERATED-EARLY annotation
_CAP_QOQ_FLAG_X = 5.0  # print-only sanity: a member cap moving >5x in one QoQ step is flagged
_WUR_TYPES = {"WARRANT", "UNIT", "RIGHT", "RIGHTS"}  # Polygon security types excluded from baskets
_WUR_SUFFIX: tuple[str, ...] = ("WS", "RT", "W", "U", "R")  # warrant/unit/right suffix fallback

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
def _rising_inputs(velocity: list[int], i: int) -> tuple[float | None, float | None]:
    """(trailing-4q median, OLS slope) for quarter i — the classifier's medrise/sloperise inputs.
    The trailing window is ``velocity[i-4:i]``: the 4 quarters STRICTLY BEFORE i (EXCLUSIVE of the
    current quarter). (None, None) if that window is incomplete (i < 4 — a data gap)."""
    if i < 4:
        return None, None
    prior = velocity[i - 4 : i]
    med = float(statistics.median(prior))
    xs = [0.0, 1.0, 2.0, 3.0]
    ys = [float(v) for v in prior]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    cov = sum((x - mx) * (yv - my) for x, yv in zip(xs, ys, strict=True))
    return med, (cov / denom if denom else 0.0)


def _activity_rising(velocity: list[int], i: int, test: str) -> bool | None:
    """Is quarter i 'activity-rising'? None if the trailing-4q window is incomplete (data gap).
    medrise = velocity[i] > trailing-4q median; sloperise = positive OLS slope over the 4q."""
    med, slope = _rising_inputs(velocity, i)
    if med is None or slope is None:
        return None
    return velocity[i] > med if test == "medrise" else slope > 0


def classify_quadrant(
    excess_iwm: float | None, excess_spy: float | None, rising: bool | None, flat_threshold: float,
    *, symmetric: bool = False,
) -> Quadrant:
    """Place one quarter in the velocity x price quadrant under one boundary combo.

    flat = excess vs BOTH < threshold (v0, ONE-SIDED). EARLY = rising+flat; PRICED = rising+moved;
    QUIET = thin+flat; NARRATIVE = thin+moved. UNKNOWN on a gap. ``symmetric=True`` uses a ±band
    (|excess| < threshold) — a REPORTED-ONLY variant, fed to no verdict."""
    if excess_iwm is None or excess_spy is None or rising is None:
        return "UNKNOWN"
    if symmetric:
        flat = abs(excess_iwm) < flat_threshold and abs(excess_spy) < flat_threshold
    else:
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
# v1 velocity axis — calendar-anchored filers + decomposition (aggregation over cached reads)
# ==================================================================================================
def _contiguous_quarters(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    """All (y,q) from start to end inclusive, oldest first."""
    out = [start]
    while out[-1] != end:
        out.append(add_quarters(out[-1][0], out[-1][1], 1))
    return out


def cik_sets_by_quarter(
    terms: tuple[str, ...], quarters: list[tuple[int, int]], *,
    efts: CachedHttp, cache_root: Path, max_pages: int,
) -> dict[tuple[int, int], set[str]]:
    """{(y,q): set of CIKs mentioning ANY term that quarter}, from the cached per-(term,quarter)
    reads. Cache-first — a re-run is network-free."""
    out: dict[tuple[int, int], set[str]] = {}
    for y, q in quarters:
        s: set[str] = set()
        for term in terms:
            r = term_quarter_read(efts, cache_root, term, y, q, max_pages=max_pages)
            s |= set(r["cik_counts"].keys())
        out[y, q] = s
    return out


def window_relative_new_filers(
    cik_sets: dict[tuple[int, int], set[str]], window_qs: list[tuple[int, int]]
) -> dict[tuple[int, int], int]:
    """RECORDED v0 basis: a CIK is 'new' in the FIRST window quarter it appears (dedup from the
    window start — window-relative, hence a start burn-in the anchored definition removes)."""
    seen: set[str] = set()
    out: dict[tuple[int, int], int] = {}
    for yq in window_qs:
        cur = cik_sets.get(yq, set())
        out[yq] = len(cur - seen)
        seen |= cur
    return out


def anchored_new_ciks(
    cik_sets: dict[tuple[int, int], set[str]], yq: tuple[int, int],
    lookback: int = _ANCHOR_LOOKBACK_Q,
) -> set[str]:
    """The CIKs 'new' in quarter yq under a FIXED trailing-``lookback``q window: in yq, absent from
    EACH of the prior ``lookback`` quarters (window-INDEPENDENT — no burn-in)."""
    prior: set[str] = set()
    for k in range(1, lookback + 1):
        prior |= cik_sets.get(add_quarters(yq[0], yq[1], -k), set())
    return cik_sets.get(yq, set()) - prior


def anchored_new_filers(
    cik_sets: dict[tuple[int, int], set[str]], window_qs: list[tuple[int, int]],
    lookback: int = _ANCHOR_LOOKBACK_Q,
) -> dict[tuple[int, int], int]:
    """v1 calendar-anchored new-filer counts per window quarter (adoption PENDING SANCTION)."""
    return {yq: len(anchored_new_ciks(cik_sets, yq, lookback)) for yq in window_qs}


def per_term_new_contribution(
    terms: tuple[str, ...], yq: tuple[int, int], new_ciks: set[str], *,
    efts: CachedHttp, cache_root: Path, max_pages: int, top: int = _TOP_TERMS,
) -> tuple[TermContribution, ...]:
    """Top terms by how many of ``new_ciks`` mentioned that term in ``yq`` (aggregation from the
    cached reads). A new CIK may count under >1 term, so contributions can exceed new_filers."""
    contrib: list[TermContribution] = []
    for term in terms:
        r = term_quarter_read(efts, cache_root, term, yq[0], yq[1], max_pages=max_pages)
        c = len(set(r["cik_counts"].keys()) & new_ciks)
        if c:
            contrib.append(TermContribution(term=term, new_filers=c))
    contrib.sort(key=lambda t: (-t.new_filers, t.term))
    return tuple(contrib[:top])


def _derated(excess_iwm: float | None, excess_spy: float | None) -> bool:
    """DERATED-EARLY: basket underperformed BOTH benchmarks by more than |threshold| (< −20%)."""
    return (excess_iwm is not None and excess_spy is not None
            and excess_iwm < _DERATE_THRESHOLD and excess_spy < _DERATE_THRESHOLD)


def theme_placebo_ratio(theme_new: int, placebo_new: int) -> float | None:
    """theme / placebo anchored new-filers; None where placebo = 0 (never a divide-by-zero)."""
    return theme_new / placebo_new if placebo_new else None


def is_warrant_unit_right(ticker: str, sec_type: str | None) -> tuple[bool, str]:
    """(exclude?, reason) for a warrant/unit/right class. Metadata-PRIMARY (Polygon security type);
    a conservative ticker-suffix fallback fires ONLY when the type is absent (delisted/unknown), and
    every suffix hit is logged loudly so a false exclusion is visible, never silent."""
    if sec_type and sec_type.upper() in _WUR_TYPES:
        return True, f"polygon type={sec_type.upper()}"
    if sec_type is None:
        for suf in _WUR_SUFFIX:
            if ticker.endswith(suf) and len(ticker) >= len(suf) + 3:
                return True, f"ticker suffix -{suf} (no polygon type)"
    return False, ""


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
    *,
    price_date: str,
    security_types: dict[str, str] | None = None,
    shares_source: str = "xbrl_cover_page (recent_share_periods)",
) -> tuple[list[BasketMember], list[str]]:
    """Top-10 obvious basket by mention count, cap-banded ($100M-$10B); warrant/unit/right classes
    are EXCLUDED (metadata-primary, suffix-fallback). ``close_at`` = {ticker: as-of close}. Returns
    (members, drops); each drop carries a logged reason (never a silent gap)."""
    sec_types = security_types or {}
    members: list[BasketMember] = []
    drops: list[str] = []
    for cik, n in mention_counts.most_common():
        if len(members) >= 10:
            break
        ticker = ct_map.get(cik)
        if not ticker:
            drops.append(f"CIK {cik} (n={n}): no ticker in company_tickers (private/foreign)")
            continue
        wur, why = is_warrant_unit_right(ticker, sec_types.get(ticker))
        if wur:
            drops.append(f"{ticker} (CIK {cik}, n={n}): warrant/unit/right excluded [{why}]")
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
            cap_method="xbrl_cover_shares x polygon_close",
            shares_source=shares_source, share_count=shares, price_date=price_date))
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
    security_types: dict[str, str] | None = None,
    placebo_terms: tuple[str, ...] | None = None,
) -> AssayCard:
    """Assemble one candidate's AssayCard at ``as_of`` over N quarters. Deterministic reads only
    (efts + Polygon via ``price_fn``); no LLM. Cache-first (re-runs are network-free).

    Records BOTH velocity definitions side by side: ``new_filers`` (RECORDED window-relative v0
    basis, mechanism UNCHANGED) and ``new_filers_anchored`` (v1 fixed-12q lookback — window-
    independent, adoption PENDING SANCTION). Nothing here reclassifies the recorded verdict.
    """
    qs = quarters_ending(as_of, quarters)  # oldest first
    trailing8 = set(qs[-_BASELINE_LAG_Q:])  # basket ranks over the trailing 8 quarters
    window = set(qs)
    ext_qs = _contiguous_quarters(add_quarters(qs[0][0], qs[0][1], -_ANCHOR_LOOKBACK_Q), qs[-1])

    cik_first: dict[str, str] = {}  # RECORDED: earliest-mention date per CIK within the window
    cik_counts: Counter[str] = Counter()  # basket mention counts (trailing 8 quarters)
    cik_sets: dict[tuple[int, int], set[str]] = {}  # v1: CIK set per quarter (window+lookback)
    total_by_q: dict[tuple[int, int], int] = dict.fromkeys(qs, 0)
    f8_by_q: dict[tuple[int, int], int] = dict.fromkeys(qs, 0)
    f10_by_q: dict[tuple[int, int], int] = dict.fromkeys(qs, 0)
    capped: list[str] = []
    for term in candidate.terms:
        for y, q in ext_qs:
            r = term_quarter_read(efts, cache_root, term, y, q, max_pages=max_pages)
            cik_sets.setdefault((y, q), set()).update(r["cik_counts"].keys())
            if (y, q) not in window:
                continue
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

    # RECORDED window-relative velocity (v0 basis — mechanism unchanged, byte-identical to v0)
    cik_first_q = {cik: quarter_of(date.fromisoformat(d)) for cik, d in cik_first.items() if d}
    new_by_q = new_filers_by_quarter(cik_first_q, qs)
    velocity = [new_by_q[yq] for yq in qs]
    # v1 calendar-anchored velocity (alongside; adoption PENDING)
    anchored_by_q = anchored_new_filers(cik_sets, qs)
    velocity_anchored = [anchored_by_q[yq] for yq in qs]
    # placebo ratio series (None-safe) — theme cards only, never a placebo self-ratio
    placebo_by_q: dict[tuple[int, int], int] = {}
    if placebo_terms and not candidate.is_placebo:
        placebo_sets = cik_sets_by_quarter(
            placebo_terms, ext_qs, efts=efts, cache_root=cache_root, max_pages=max_pages)
        placebo_by_q = anchored_new_filers(placebo_sets, qs)

    ct = company_ticker_map(sec_http)
    # POINT-IN-TIME: reuse the universe helper's 40-day filing-lag gate so basket cap-banding never
    # sees shares disclosed AFTER as_of (no lookahead — a future-quarter frame is excluded).
    shares = edgar.shares_outstanding_by_cik(recent_share_periods(as_of))
    close_at: dict[str, float | None] = {
        ct[cik]: price_fn(ct[cik], as_of) for cik in cik_counts if cik in ct
    }
    basket, drops = build_basket(
        cik_counts, ct, shares, close_at, price_date=as_of.isoformat(),
        security_types=security_types)

    baseline_yq = qs[max(0, len(qs) - 1 - _BASELINE_LAG_Q)]
    baseline_date = quarter_end(*baseline_yq)
    qends = [quarter_end(yy, qq) for (yy, qq) in qs]

    # print-only cap sanity: flag any member whose computed cap moves >5x in one QoQ step
    flagged: list[BasketMember] = []
    for m in basket:
        flag: str | None = None
        if m.share_count is not None:
            sc = m.share_count
            caps = [sc * p for qe in qends if (p := price_fn(m.ticker, qe)) is not None]
            for a, b in zip(caps, caps[1:], strict=False):
                if a > 0 and b > 0 and max(a, b) / min(a, b) > _CAP_QOQ_FLAG_X:
                    flag = f"cap moved >{_CAP_QOQ_FLAG_X:.0f}x QoQ (price glitch? sanity-only)"
                    break
        flagged.append(m.model_copy(update={"cap_qoq_flag": flag}) if flag else m)
    basket = flagged
    tickers = [m.ticker for m in basket]

    reads: list[QuarterRead] = []
    sym_series: dict[str, list[str]] = {c: [] for c in COMBOS}
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
        quad_anch: dict[str, str] = {}
        for p_name, thresh in _PRICE_FLAT.items():
            for a_name in _ACTIVITY:
                combo = f"{p_name}_{a_name}"
                rising = _activity_rising(velocity, i, a_name)
                quad[combo] = classify_quadrant(ex_iwm, ex_spy, rising, thresh)
                quad_anch[combo] = classify_quadrant(
                    ex_iwm, ex_spy, _activity_rising(velocity_anchored, i, a_name), thresh)
                sym_series[combo].append(
                    classify_quadrant(ex_iwm, ex_spy, rising, thresh, symmetric=True))
        med, slope = _rising_inputs(velocity, i)
        new_ciks = anchored_new_ciks(cik_sets, (y, q))
        top_terms = per_term_new_contribution(
            candidate.terms, (y, q), new_ciks, efts=efts, cache_root=cache_root,
            max_pages=max_pages)
        pr: float | None = None
        if placebo_by_q:
            pr = theme_placebo_ratio(anchored_by_q[y, q], placebo_by_q.get((y, q), 0))
        reads.append(QuarterRead(
            quarter=quarter_label(y, q), new_filers=new_by_q[y, q],
            new_filers_anchored=anchored_by_q[y, q], total_mentions=total_by_q[y, q],
            mentions_8k_family=f8_by_q[y, q], mentions_10k_family=f10_by_q[y, q],
            basket_excess_iwm=ex_iwm, basket_excess_spy=ex_spy, quadrant_by_combo=quad,
            quadrant_by_combo_anchored=quad_anch, rising_median_4q=med, rising_slope_4q=slope,
            top_terms=top_terms, placebo_ratio=pr, derated_early=_derated(ex_iwm, ex_spy),
            data_gaps=gaps))

    residence = {c: early_residence([r.quadrant_by_combo[c] for r in reads]) for c in COMBOS}
    residence_anch = {
        c: early_residence([r.quadrant_by_combo_anchored[c] for r in reads]) for c in COMBOS}
    residence_sym = {c: early_residence(sym_series[c]) for c in COMBOS}
    div_age = divergence_age([r.quadrant_by_combo[_REFERENCE_COMBO] for r in reads])

    caveats = [
        "POINT-IN-TIME: efts filings + Polygon closes are read as-of; no forward information used.",
        "Forward multiples / valuation are UNAVAILABLE in this stack (v1 reads filings+prices).",
        f"Basket cap = XBRL cover-page shares x Polygon close (best-effort); {len(drops)} dropped; "
        "warrant/unit/right classes EXCLUDED.",
        "v1 limits: no commitment/'money' extraction; no attention prior; the form-family "
        "split is PRINTED, not weighted; ZERO LLM calls.",
        f"VELOCITY: `new filers` = window-relative (RECORDED v0 basis); `anchored` = fixed "
        f"{_ANCHOR_LOOKBACK_Q}q lookback (window-independent). Anchored adoption is PENDING "
        "SANCTION — it does NOT reclassify the recorded verdict.",
        "RISING-TEST inputs (median, slope) are over the trailing 4q EXCLUSIVE of the current "
        "quarter (velocity[i-4:i]).",
        "SYMMETRIC ±band residence is REPORTED-ONLY (|excess| < threshold); fed to NO verdict.",
    ]
    if placebo_by_q:
        caveats.append("RATIO = theme anchored-filers / placebo anchored-filers "
                       "(a listing-wave null; None where placebo = 0).")
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
        residence_by_combo_anchored=residence_anch, residence_by_combo_symmetric=residence_sym,
        divergence_age_quarters=div_age, is_placebo=candidate.is_placebo, caveats=caveats)


def kill_verdict(cards: list[AssayCard], *, anchored: bool = False) -> tuple[str, list[str]]:
    """Honest three-way verdict over the retrocast cards. PASS if any card+combo shows >=2
    consecutive EARLY quarters; INCONCLUSIVE if none does but a price gap prevented classifying
    (never a false FALSIFIED); FALSIFIED only when price is present and no >=2 EARLY run exists.

    ``anchored=False`` (default) reads the RECORDED ``residence_by_combo``. ``anchored=True`` reads
    ``residence_by_combo_anchored`` (v1 velocity) for the SIDE-BY-SIDE print; NEVER overwriting the
    recorded verdict — the caller prints both and the operator sanctions adoption."""
    label = "ANCHORED" if anchored else "RECORDED"
    evidence: list[str] = []
    passed = False
    for card in cards:
        res = card.residence_by_combo_anchored if anchored else card.residence_by_combo
        for combo, r in res.items():
            if r.longest_early_run >= 2:
                evidence.append(
                    f"[{label}] {card.candidate_key} as-of {card.as_of}: {combo} longest EARLY "
                    f"run={r.longest_early_run}")
                passed = True
    if passed:
        return f"PASS ({label}: survives — early-window premise NOT falsified)", evidence
    gapped = any("PRICE GAP" in c for card in cards for c in card.caveats)
    if gapped:
        return (
            f"INCONCLUSIVE ({label}) — price axis gapped; the kill criterion cannot be evaluated",
            evidence,
        )
    return (
        f"FALSIFIED ({label}) — no >=2q EARLY residence under any combo (build STOPS here)",
        evidence,
    )


def render_markdown(card: AssayCard) -> str:
    """The human-facing card: quarterly table (BOTH filer definitions + classifier inputs + ratio +
    DERATED), per-term decomposition, basket + cap provenance, residence THREE ways, caveats."""
    kind = "placebo · VALIDATION INSTRUMENT" if card.is_placebo else "theme"
    out = [f"# Earliness assay v1 — {card.candidate_key} ({kind}, as-of {card.as_of})", "",
           f"**Basket rule:** {card.basket_rule}", "",
           "## Quarterly read (velocity x price)", "",
           "new(win) = window-relative RECORDED v0 basis · new(anch) = calendar-anchored 12q (v1, "
           "PENDING) · ratio = theme/placebo anchored filers · med4q/slope4q = rising-test "
           "inputs over velocity[i-4:i]", "",
           "| quarter | new(win) | new(anch) | ratio | mentions | 8-K | 10-K | med4q | slope4q "
           "| vs IWM | vs SPY | quad rec | quad anch |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in card.quarters:
        ei = "—" if r.basket_excess_iwm is None else f"{r.basket_excess_iwm:+.0%}"
        es = "—" if r.basket_excess_spy is None else f"{r.basket_excess_spy:+.0%}"
        ratio = "—" if r.placebo_ratio is None else f"{r.placebo_ratio:.2f}"
        med = "—" if r.rising_median_4q is None else f"{r.rising_median_4q:.0f}"
        slp = "—" if r.rising_slope_4q is None else f"{r.rising_slope_4q:+.0f}"
        qr = r.quadrant_by_combo[_REFERENCE_COMBO]
        if r.derated_early and qr == "EARLY":
            qr += "†"
        qa = r.quadrant_by_combo_anchored[_REFERENCE_COMBO]
        out.append(
            f"| {r.quarter} | {r.new_filers} | {r.new_filers_anchored} | {ratio} "
            f"| {r.total_mentions} | {r.mentions_8k_family} | {r.mentions_10k_family} "
            f"| {med} | {slp} | {ei} | {es} | {qr} | {qa} |")
    out += ["", "_quad = ref combo (flat20_medrise); † = DERATED-EARLY (excess < −20% vs BOTH). "
            "Rising inputs are trailing 4q EXCLUSIVE of the current quarter._",
            "", "## Top terms driving new filers (anchored, per quarter)", ""]
    term_lines = [f"- {r.quarter}: " + ", ".join(f"{t.term} ({t.new_filers})" for t in r.top_terms)
                  for r in card.quarters if r.top_terms]
    out += term_lines or ["_(no anchored new filers in-window)_"]
    out += ["", "## Obvious basket (mechanical, ex-ante)", ""]
    if card.basket:
        out += ["| ticker | CIK | mentions | cap | shares | shares src | price date | qoq flag |",
                "|---|---|---|---|---|---|---|---|"]
        for m in card.basket:
            cap = "—" if m.cap_asof is None else f"${m.cap_asof / 1e9:.2f}B"
            sh = "—" if m.share_count is None else f"{m.share_count / 1e6:.1f}M"
            out.append(
                f"| {m.ticker} | {m.cik} | {m.mention_count} | {cap} | {sh} "
                f"| {m.shares_source} | {m.price_date} | {m.cap_qoq_flag or '—'} |")
    else:
        out.append("_(empty — no members survived cap band / CIK->ticker / warrant / price gates)_")
    out += ["", "## EARLY residence per boundary combo (run/total)", "",
            "| combo | RECORDED (v0) | anchored (v1, pending) | symmetric (reported-only) |",
            "|---|---|---|---|"]
    for c in COMBOS:
        rr, ra, rs = (card.residence_by_combo[c], card.residence_by_combo_anchored[c],
                      card.residence_by_combo_symmetric[c])
        out.append(f"| {c} | {rr.longest_early_run}/{rr.total_early_quarters} "
                   f"| {ra.longest_early_run}/{ra.total_early_quarters} "
                   f"| {rs.longest_early_run}/{rs.total_early_quarters} |")
    out += ["", "_RECORDED = window-relative velocity (the verdict basis). anchored = v1 velocity "
            "(PENDING SANCTION). symmetric = ±band flat rule (fed to NO verdict)._"]
    age = "—" if card.divergence_age_quarters is None else str(card.divergence_age_quarters)
    out += ["", f"**Divergence age (quarters, {_REFERENCE_COMBO}, RECORDED):** {age}", "",
            "## Caveats", ""]
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
