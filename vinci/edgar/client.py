"""The EDGAR client — US fundamentals (XBRL), de-rating event detection (8-K), and recent filings.

Three jobs, all free/public (no credential):
- ``companyfacts`` / ``fundamental_snapshot`` → the non-distress fundamentals Screen-2 needs
  (FCF sign, operating-income sign, net leverage) plus EBITDA / net-debt / EPS inputs that step 5
  combines with EOD price for the EV/EBITDA & P/E multiples. Point-in-time, as-reported.
- ``fulltext_search`` (efts) → guidance-cut / de-rating language in 8-Ks = the trigger. (Note: efts
  requires spaces in a quoted phrase encoded as %20, not '+', or it silently returns zero hits.)
- ``recent_filings`` (submissions) → recent 8-Ks with item codes (2.02 results, 7.01 Reg FD).

Missing fundamentals degrade to UNKNOWN (the envelope), never a crash. The snapshot *math* lives in
the pure :func:`compute_fundamental_snapshot` so it is unit-testable without the network.
"""

from __future__ import annotations

import urllib.parse
from collections.abc import Sequence
from datetime import date
from typing import Any, cast

from pydantic import BaseModel

from vinci.config import Config, get_config
from vinci.edgar.concepts import extract_points, latest_annual, latest_instant
from vinci.netcache import CachedHttp, HttpError
from vinci.resolver.index import pad_cik
from vinci.schemas.envelope import DataField, SourceTier
from vinci.sec import build_efts_http, build_sec_http

_COMPANYFACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
_FRAMES = "https://data.sec.gov/api/xbrl/frames/{ns}/{concept}/{unit}/{period}.json"
_EFTS = "https://efts.sec.gov/LATEST/search-index"
_ONE_DAY = 86_400.0


class FtsHit(BaseModel, frozen=True):
    """One EDGAR full-text-search hit (a filing matching the query)."""

    accession: str
    cik: str | None
    form: str | None
    file_date: date | None
    display_names: list[str]


class Filing(BaseModel, frozen=True):
    """A filing from the submissions feed (used for 8-K event detection)."""

    cik: str
    form: str
    filing_date: date
    accession: str
    items: list[str]  # 8-K item codes, e.g. ["2.02", "9.01"]
    primary_doc: str | None


class FundamentalSnapshot(BaseModel, frozen=True):
    """EDGAR-only fundamentals (no price). Non-distress signals + inputs for step-5 multiples."""

    cik: str
    op_income_sign: DataField[int]
    fcf_sign: DataField[int]
    net_leverage: DataField[float]
    net_debt_to_ocf: DataField[float]  # net debt / operating cash flow — survives untaggable D&A
    ebitda_annual: DataField[float]  # operating income + D&A (for EV/EBITDA in step 5)
    net_debt: DataField[float]  # total debt - cash (for EV in step 5)
    eps_diluted_annual: DataField[float]  # for P/E in step 5
    as_of: date | None


def _sign(x: float) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


def _present_f(value: float, as_of: date) -> DataField[float]:
    return DataField.present(value, as_of=as_of, source="EDGAR", tier=SourceTier.EDGAR)


def _present_i(value: int, as_of: date) -> DataField[int]:
    return DataField.present(value, as_of=as_of, source="EDGAR", tier=SourceTier.EDGAR)


def _unknown_f(note: str) -> DataField[float]:
    return DataField.unknown(source="EDGAR", tier=SourceTier.EDGAR, note=note)


def _unknown_i(note: str) -> DataField[int]:
    return DataField.unknown(source="EDGAR", tier=SourceTier.EDGAR, note=note)


def all_unknown_snapshot(cik10: str) -> FundamentalSnapshot:
    """Snapshot for an issuer with no usable XBRL — every field UNKNOWN (graceful degradation)."""
    return FundamentalSnapshot(
        cik=cik10,
        op_income_sign=_unknown_i("no XBRL"),
        fcf_sign=_unknown_i("no XBRL"),
        net_leverage=_unknown_f("no XBRL"),
        net_debt_to_ocf=_unknown_f("no XBRL"),
        ebitda_annual=_unknown_f("no XBRL"),
        net_debt=_unknown_f("no XBRL"),
        eps_diluted_annual=_unknown_f("no XBRL"),
        as_of=None,
    )


# Outstanding-debt instrument tags used ONLY as a consistency witness (see _max_outstanding_debt) —
# the instruments the LongTermDebt+current extraction below does NOT read, so a large value here
# means that extraction missed debt. NOT summed (the tags overlap; summing would double-count).
_DEBT_WITNESS_TAGS: tuple[str, ...] = (
    "ShortTermBorrowings", "ConvertibleDebt", "ConvertibleDebtCurrent", "ConvertibleDebtNoncurrent",
    "NotesPayableCurrent", "NotesPayable", "SubordinatedDebtCurrent", "SubordinatedDebt",
    "SecuredDebt", "SecuredDebtCurrent",
)


def _max_outstanding_debt(facts: dict[str, Any]) -> tuple[float, str] | None:
    """Largest SINGLE outstanding-debt instrument balance a filer reports (latest instant of any
    witness tag). A CONSISTENCY WITNESS only: if it exceeds the long-term+current extraction, that
    extraction missed debt (the MVST case — convertible / notes / short-term tags), and the caller
    fails loud rather than show a confident understated (often false net-cash) figure."""
    us = facts.get("facts", {}).get("us-gaap", {})
    best: tuple[float, str] | None = None
    for tag in _DEBT_WITNESS_TAGS:
        pts = us.get(tag, {}).get("units", {}).get("USD")
        if not pts:
            continue
        latest = max(pts, key=lambda r: (r.get("end", ""), r.get("filed", "")))
        val = latest.get("val")
        if val is not None and (best is None or float(val) > best[0]):
            best = (float(val), tag)
    return best


def compute_fundamental_snapshot(cik10: str, facts: dict[str, Any]) -> FundamentalSnapshot:
    """Pure: derive the non-distress signals + step-5 inputs from a ``companyfacts`` dict."""
    op = latest_annual(extract_points(facts, "operating_income"))
    da = latest_annual(extract_points(facts, "dep_amort"))
    ocf = latest_annual(extract_points(facts, "operating_cash_flow"))
    capex = latest_annual(extract_points(facts, "capex"))
    eps = latest_annual(extract_points(facts, "eps_diluted"))
    ltd = latest_instant(extract_points(facts, "long_term_debt"))
    dc = latest_instant(extract_points(facts, "debt_current"))
    cash = latest_instant(extract_points(facts, "cash"))

    op_sign = _present_i(_sign(op.value), op.filed) if op else _unknown_i("no operating_income")
    if ocf and capex:
        fcf_sign = _present_i(_sign(ocf.value - capex.value), max(ocf.filed, capex.filed))
    else:
        fcf_sign = _unknown_i("no OCF/capex")

    ebitda_val: float | None = None
    if op and da:
        ebitda_val = op.value + da.value
        ebitda = _present_f(op.value + da.value, max(op.filed, da.filed))
    else:
        ebitda = _unknown_f("no operating_income/D&A")

    debt_total = (ltd.value if ltd else 0.0) + (dc.value if dc else 0.0)
    # CONSISTENCY GUARD: the LongTermDebt+current extraction misses debt booked under convertible /
    # notes / short-term / subordinated tags (the MVST case) — a partial sum that understates gross
    # debt and flips net-debt to a FALSE net-cash. If a single such instrument exceeds the extracted
    # total, fail loud (never a confident understated figure); CIQ's balance sheet is the authority.
    witness = _max_outstanding_debt(facts)
    undercaptured = bool((ltd or dc) and witness and witness[0] > debt_total * 1.10)
    net_debt_val: float | None = None
    if undercaptured:
        assert witness is not None
        net_debt = _unknown_f(
            f"EDGAR debt under-captured: {witness[1]} ${witness[0] / 1e6:,.0f}M alone exceeds the "
            f"${debt_total / 1e6:,.0f}M long-term+current extracted — pull CIQ"
        )
    elif (ltd or dc) and cash:
        net_debt_val = debt_total - cash.value
        filed = max(p.filed for p in (ltd, dc, cash) if p)
        net_debt = _present_f(debt_total - cash.value, filed)
    else:
        net_debt = _unknown_f("no debt/cash")

    # net leverage = net debt / EBITDA; UNKNOWN with the SPECIFIC missing input — never lump them.
    # "missing debt/cash" and "EBITDA<=0" are different facts: a positive-EBITDA name (e.g. one with
    # 10x interest coverage) reading "EBITDA<=0 or…" mis-reads as distress when the real gap is just
    # that no debt/cash line was in the XBRL.
    if net_debt_val is None:
        net_lev = _unknown_f("no net-debt — debt/cash not in XBRL")
    elif ebitda_val is None:
        net_lev = _unknown_f("no EBITDA in XBRL")
    elif ebitda_val <= 0:
        net_lev = _unknown_f("EBITDA<=0 (ratio meaningless)")
    elif not net_debt.as_of:
        net_lev = _unknown_f("net-debt as-of date missing")
    else:
        net_lev = _present_f(net_debt_val / ebitda_val, net_debt.as_of)

    # net debt / OCF — the leverage read that SURVIVES untaggable D&A (the MVST case): operating
    # cash flow already contains the D&A add-back EBITDA needs, and OCF is reliably tagged. Same
    # fail-loud discipline as net leverage: UNKNOWN naming the SPECIFIC missing input, not a guess.
    if net_debt_val is None:
        net_ocf = _unknown_f("no net-debt — debt/cash not in XBRL")
    elif ocf is None:
        net_ocf = _unknown_f("no operating cash flow in XBRL")
    elif ocf.value <= 0:
        net_ocf = _unknown_f("OCF<=0 (ratio meaningless)")
    elif not net_debt.as_of:
        net_ocf = _unknown_f("net-debt as-of date missing")
    else:
        net_ocf = _present_f(net_debt_val / ocf.value, net_debt.as_of)

    eps_df = _present_f(eps.value, eps.filed) if eps else _unknown_f("no diluted EPS")
    filed_dates = [p.filed for p in (op, da, ocf, capex, eps, ltd, dc, cash) if p]
    return FundamentalSnapshot(
        cik=cik10,
        op_income_sign=op_sign,
        fcf_sign=fcf_sign,
        net_leverage=net_lev,
        net_debt_to_ocf=net_ocf,
        ebitda_annual=ebitda,
        net_debt=net_debt,
        eps_diluted_annual=eps_df,
        as_of=max(filed_dates) if filed_dates else None,
    )


def parse_fts_response(data: dict[str, Any]) -> list[FtsHit]:
    """Parse an efts response into hits — **fail loud** if it is an error/throttle response.

    efts signals throttling/errors with a body like ``{"message": ...}`` (no ``hits`` key).
    Returning [] there would let a failed search look like 'no de-rating events' — so we raise."""
    hits = data.get("hits")
    if not isinstance(hits, dict) or "hits" not in hits:
        raise HttpError(f"efts returned no hits structure (throttled/error?): {data}")
    return [parse_fts_hit(h) for h in hits["hits"]]


def parse_fts_hit(h: dict[str, Any]) -> FtsHit:
    """Pure parser for one efts hit (unit-testable).

    efts uses plural list fields: ``ciks``, ``root_forms`` (canonical form, e.g. "8-K" even for an
    "8-K/A" amendment), and ``adsh`` (the accession). We read those, with sensible fallbacks.
    """
    src = h.get("_source", {})
    ciks = src.get("ciks") or []
    cik = ciks[0] if ciks else None
    root_forms = src.get("root_forms") or []
    form = (root_forms[0] if root_forms else None) or src.get("file_type") or src.get("form")
    fd = src.get("file_date")
    accession = src.get("adsh") or str(h.get("_id", "")).split(":", 1)[0]
    return FtsHit(
        accession=accession,
        cik=str(cik) if cik else None,
        form=form,
        file_date=date.fromisoformat(fd) if fd else None,
        display_names=list(src.get("display_names", [])),
    )


class EdgarClient:
    def __init__(self, http: CachedHttp, efts_http: CachedHttp | None = None) -> None:
        self._http = http
        # efts is rate-sensitive → its own slower client; falls back to the data client if unset.
        self._efts = efts_http or http

    @classmethod
    def from_config(cls, config: Config | None = None) -> EdgarClient:
        cfg = config or get_config()
        return cls(http=build_sec_http(cfg), efts_http=build_efts_http(cfg))

    # --- XBRL fundamentals --------------------------------------------------------------------
    def companyfacts(self, cik: int | str) -> dict[str, Any]:
        cik10 = pad_cik(cik)
        data = self._http.get_json(_COMPANYFACTS.format(cik=cik10), ttl_seconds=_ONE_DAY)
        return cast(dict[str, Any], data)

    def frame(
        self, concept: str, *, namespace: str = "dei", unit: str = "shares", period: str
    ) -> dict[str, float]:
        """One XBRL concept across **all filers** for a period → ``{cik10: val}`` (breadth tool).

        ``period`` is a frame key, e.g. ``CY2026Q1I`` (instant) or ``CY2025`` (annual duration).
        Used by the universe builder to size every name's market cap without per-name pulls.
        """
        url = _FRAMES.format(ns=namespace, concept=concept, unit=unit, period=period)
        data = cast(dict[str, Any], self._http.get_json(url, ttl_seconds=_ONE_DAY))
        out: dict[str, float] = {}
        for row in data.get("data", []):
            if row.get("val") is not None and row.get("cik") is not None:
                out[pad_cik(row["cik"])] = float(row["val"])
        return out

    def shares_outstanding_by_cik(self, periods: Sequence[str]) -> dict[str, float]:
        """Merge shares-outstanding frames over recent ``periods`` (later win) for coverage."""
        merged: dict[str, float] = {}
        for period in periods:
            try:
                merged.update(self.frame("EntityCommonStockSharesOutstanding", period=period))
            except Exception:  # noqa: BLE001 — a missing/empty frame just contributes nothing
                continue
        return merged

    def fundamental_snapshot(self, cik: int | str) -> FundamentalSnapshot:
        """Non-distress signals + step-5 inputs, each enveloped (UNKNOWN where XBRL is absent)."""
        cik10 = pad_cik(cik)
        try:
            facts = self.companyfacts(cik10)
        except Exception:  # noqa: BLE001 — absent/!XBRL issuer → all UNKNOWN, never crash
            return all_unknown_snapshot(cik10)
        return compute_fundamental_snapshot(cik10, facts)

    # --- 8-K full-text search (the de-rating trigger) -----------------------------------------
    def fulltext_search(
        self,
        phrase: str,
        *,
        forms: str = "8-K",
        startdt: str | None = None,
        enddt: str | None = None,
    ) -> list[FtsHit]:
        """Search EDGAR full text for an exact phrase. Spaces → %20 (an efts requirement)."""
        q = urllib.parse.quote(f'"{phrase}"')  # quote() => spaces become %20, not '+'
        url = f"{_EFTS}?q={q}&forms={forms}"
        if startdt and enddt:
            url += f"&startdt={startdt}&enddt={enddt}"
        data = cast(dict[str, Any], self._efts.get_json(url, ttl_seconds=_ONE_DAY))
        return parse_fts_response(data)

    # --- recent filings (8-K detection via submissions) ---------------------------------------
    def recent_filings(
        self, cik: int | str, *, forms: tuple[str, ...] = ("8-K",), since: date | None = None
    ) -> list[Filing]:
        cik10 = pad_cik(cik)
        raw = self._http.get_json(_SUBMISSIONS.format(cik=cik10), ttl_seconds=_ONE_DAY)
        data = cast(dict[str, Any], raw)
        recent = data.get("filings", {}).get("recent", {})
        out: list[Filing] = []
        n = len(recent.get("accessionNumber", []))
        for i in range(n):
            form = recent["form"][i]
            if form not in forms:
                continue
            fdate = date.fromisoformat(recent["filingDate"][i])
            if since and fdate < since:
                continue
            items_raw = recent.get("items", [""] * n)[i] or ""
            out.append(
                Filing(
                    cik=cik10,
                    form=form,
                    filing_date=fdate,
                    accession=recent["accessionNumber"][i],
                    items=[x.strip() for x in items_raw.split(",") if x.strip()],
                    primary_doc=recent.get("primaryDocument", [None] * n)[i],
                )
            )
        return out
