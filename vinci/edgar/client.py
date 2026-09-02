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
from vinci.edgar.submissions import RegistrantHistory, parse_registrant_history
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
    report_date: date | None = None  # the period the filing reports ON (10-Q/K balance-sheet as-of)


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


# Interest-bearing-debt instrument tags used ONLY as a consistency witness (see
# _max_outstanding_debt) — instruments the LongTermDebt+current extraction does NOT read, so a large
# value here means that extraction missed debt. NOT summed (tags overlap; summing double-counts).
# Finance-lease tags are excluded (the "is a lease debt" question is genuinely nuanced).
_DEBT_WITNESS_TAGS: tuple[str, ...] = (
    "ShortTermBorrowings", "ConvertibleDebt", "ConvertibleDebtCurrent", "ConvertibleDebtNoncurrent",
    "NotesPayableCurrent", "NotesPayable", "LongTermNotesPayable", "SubordinatedDebtCurrent",
    "SubordinatedDebt", "SecuredDebt", "SecuredDebtCurrent", "LinesOfCreditCurrent",
    "LongTermLineOfCredit", "OtherLongTermDebt", "OtherLongTermDebtNoncurrent",
    "OtherLongTermDebtCurrent",
)


def _max_outstanding_debt(facts: dict[str, Any], ref_end: str | None) -> tuple[float, str] | None:
    """Largest SINGLE outstanding-debt instrument balance a filer reports AT OR AFTER ``ref_end``
    (the captured-debt period). A CONSISTENCY WITNESS only: if it exceeds the long-term+current
    extraction, that extraction missed debt (the MVST case — convertible / notes / short-term tags),
    and the caller fails loud rather than show a confident understated (false net-cash) figure.
    The ``ref_end`` filter drops a since-repaid instrument whose value persists at a STALE date,
    so a clean current balance sheet isn't false-flagged by a long-gone borrowing."""
    us = facts.get("facts", {}).get("us-gaap", {})
    best: tuple[float, str] | None = None
    for tag in _DEBT_WITNESS_TAGS:
        pts = us.get(tag, {}).get("units", {}).get("USD")
        if not pts:
            continue
        current = [p for p in pts if not ref_end or str(p.get("end", "")) >= ref_end]
        if not current:
            continue
        latest = max(current, key=lambda r: (r.get("end", ""), r.get("filed", "")))
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
    # debt and flips net-debt to a FALSE net-cash. If a single instrument (at/after the captured
    # period) exceeds the extracted total, fail loud (never a confident understated figure); CIQ's
    # balance sheet is the authority. No (ltd or dc) gate — a filer with ALL debt in witness tags
    # (debt_total 0) must fail loud too, not read as debt-free.
    ref_end = max((p.period_end.isoformat() for p in (ltd, dc) if p), default=None)
    witness = _max_outstanding_debt(facts, ref_end)
    undercaptured = bool(witness and witness[0] > debt_total * 1.10)
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


#: The XBRL tags accepted as a share count, in PRECEDENCE order. MODULE-LEVEL on purpose: a
#: consumer stamping provenance must read the tag from here, never through the client class — a
#: test (or any caller) that substitutes its own client would otherwise shadow the constant and
#: silently change what "approximate" means at the stamping site.
SHARES_TAG_DEI = "dei:EntityCommonStockSharesOutstanding"          # filed INSTANT count (primary)
SHARES_TAG_USGAAP = "us-gaap:CommonStockSharesOutstanding"         # filed INSTANT count (fallback)
SHARES_TAG_WAVG = "us-gaap:WeightedAverageNumberOfSharesOutstandingBasic"   # PERIOD AVERAGE

#: How many CIKs' submissions documents one client remembers at a time. TWO, not unbounded: one
#: assembly touches ONE CIK across ~13 reads, so 2 is already slack — while `vinci/cli.py`'s monitor
#: loop and the theme scans hold ONE client across MANY CIKs and read each exactly ONCE, where an
#: unbounded memo would be pure cost (a parsed submissions dict is 3.6-3.9x its text: ~0.53 MB at
#: the corpus median, ~17 MB at the 4.32 MB max — a 2,000-name sweep would retain ~1.0 GB unused).
_SUBMISSIONS_MEMO_MAX = 2


class EdgarClient:
    def __init__(self, http: CachedHttp, efts_http: CachedHttp | None = None) -> None:
        self._http = http
        # efts is rate-sensitive → its own slower client; falls back to the data client if unset.
        self._efts = efts_http or http
        # Per-INSTANCE memo of the parsed submissions document (see `_submissions`). Deliberately a
        # plain dict rather than `functools.lru_cache` on the method: an lru_cache keys on `self`
        # and would keep every client — and every document it ever touched — alive for the process
        # lifetime. This dies with the client, which is what "for the life of one run" means here.
        self._submissions_memo: dict[str, dict[str, Any] | HttpError] = {}

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

    def shares_outstanding_with_provenance(
        self, periods: Sequence[str], *, include_period_average: bool = False
    ) -> tuple[dict[str, float], dict[str, str]]:
        """``({cik10: shares}, {cik10: tag})`` — the ONE implementation, provenance included.

        THREE TIERS, strict precedence, later periods winning within a tier. ``dei
        EntityCommonStockSharesOutstanding`` is PRIMARY (the cover-page count); a name tagging
        shares only under ``us-gaap:CommonStockSharesOutstanding`` falls back to that frame with
        the SAME point-in-time discipline; both are filed INSTANT counts.

        THE THIRD TIER IS DIFFERENT IN KIND and is opt-in for exactly that reason
        (``include_period_average``, measured 2026-08-31):
        ``us-gaap:WeightedAverageNumberOfSharesOutstandingBasic`` is an AVERAGE OVER THE PERIOD,
        not a count on a date. It exists because a real and sizeable class of filers publishes NO
        instant count at all — 142 operating equities above $100M ADV were missing from the
        universe, 104 of them recoverable here, META among them (it reports neither instant tag;
        GOOGL reports the us-gaap one, which is the whole difference between the two). A period
        average is an acceptable input to a COARSE CAP BAND — but NOT confined to one, and the
        caller must know it: the same `market_cap` is read by `themes/residualize.build_factors`
        as the SIZE-FACTOR tercile input and rendered on the ranked queue by `rank/ranker.py`,
        neither of which carries the tag. So every value from this tier is returned WITH its tag —
        the caller stamps it, and a consumer needing a filed count reads the tag, not the number —
        and it can never overwrite a filed instant count: a name with dei or us-gaap keeps that
        number.

        The provenance map is returned BESIDE the values rather than derived by a second pass, so
        a value and its tag cannot drift apart.
        """
        values: dict[str, float] = {}
        tag_by_cik: dict[str, str] = {}

        def _merge(concept: str, namespace: str, tag: str, *, instant: bool) -> None:
            for period in periods:
                # duration frames (an average is measured OVER a quarter) drop the instant suffix
                key = period if instant else period.rstrip("I")
                try:
                    frame = self.frame(concept, namespace=namespace, period=key)
                except Exception:  # noqa: BLE001 — a missing/empty frame contributes nothing
                    continue
                for cik, val in frame.items():
                    # a LOWER-precedence tier never displaces a value already set by a higher one
                    if cik in values and tag_by_cik[cik] != tag:
                        continue
                    values[cik] = val
                    tag_by_cik[cik] = tag

        _merge("EntityCommonStockSharesOutstanding", "dei", SHARES_TAG_DEI,
               instant=True)
        _merge("CommonStockSharesOutstanding", "us-gaap", SHARES_TAG_USGAAP,
               instant=True)
        if include_period_average:
            _merge("WeightedAverageNumberOfSharesOutstandingBasic", "us-gaap",
                   SHARES_TAG_WAVG, instant=False)
        return values, tag_by_cik

    def shares_outstanding_by_cik(self, periods: Sequence[str]) -> dict[str, float]:
        """Point-in-time share counts only — the values half of
        :meth:`shares_outstanding_with_provenance`, with the period-average tier OFF.

        Kept as the default so every existing consumer (the leaders sweep, the assay basket) holds
        exactly the coverage it was verified on: opting into an approximate count is a decision a
        caller makes explicitly, never one it inherits."""
        return self.shares_outstanding_with_provenance(periods)[0]

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
        ciks: str | None = None,
        startdt: str | None = None,
        enddt: str | None = None,
    ) -> list[FtsHit]:
        """Search EDGAR full text for an exact phrase. Spaces → %20 (an efts requirement).

        ``ciks`` scopes the search to a single filer — pass the 10-digit ZERO-PADDED CIK (a bare
        integer returns nothing; efts requires the padded form). Without it a phrase like
        "Convertible Bond" matches ANY filer, so a covenant lookup MUST scope to the subject."""
        q = urllib.parse.quote(f'"{phrase}"')  # quote() => spaces become %20, not '+'
        url = f"{_EFTS}?q={q}&forms={forms}"
        if ciks:
            url += f"&ciks={pad_cik(ciks)}"  # 10-digit; a bare int yields an empty efts result
        if startdt and enddt:
            url += f"&startdt={startdt}&enddt={enddt}"
        data = cast(dict[str, Any], self._efts.get_json(url, ttl_seconds=_ONE_DAY))
        return parse_fts_response(data)

    # --- registrant names (reverse-merger / rename vintage) ------------------------------------
    def _remember_submissions(self, cik10: str, outcome: dict[str, Any] | HttpError) -> None:
        """Record one CIK's outcome, evicting oldest-first past ``_SUBMISSIONS_MEMO_MAX``."""
        self._submissions_memo[cik10] = outcome
        while len(self._submissions_memo) > _SUBMISSIONS_MEMO_MAX:
            self._submissions_memo.pop(next(iter(self._submissions_memo)))

    def _submissions(self, cik: int | str) -> dict[str, Any]:
        """The submissions document for a CIK. ONE fetch shape for every consumer in this class —
        the URL and the TTL are stated once, so a change to either cannot land at one call site and
        not the other (which would silently double the SEC request rate per dossier).

        MEMOIZED PER INSTANCE, success AND failure. `CachedHttp` caches on DISK only, so each of the
        ~13 reads one dossier assembly makes of this document cost a disk read plus TWO json parses
        (the cache envelope, then the payload). The parse saving is small and honest — ~8.6 ms per
        dossier, ~4.3 s per 500-name batch. **The failure memo is the point.** `_write_cache` runs
        only on success, so a degraded feed makes EVERY caller re-run the full retry storm
        (5 attempts, 1+2+4+8 s backoff ≈ 15.6 s; ≈165 s if SEC hangs to the 30 s timeout rather than
        erroring). Remembering the failure pays that storm ONCE per CIK per run.

        THE REMEMBERED FAILURE RE-RAISES — it never returns None or {}. Nearly every consumer treats
        "no filings" as a legitimate empty answer, so returning an empty document on a remembered
        failure would silently blank the 8-K / Form 4 / catalyst blocks across a degraded run with
        the suite green. Only `HttpError` is remembered; anything else propagates unmemoized.

        The document is returned BY REFERENCE, not copied: `copy.deepcopy` measures 1.86 ms against
        0.42 ms for a fresh parse, so copying would cost 4.4x the work it saves and make this a net
        pessimization. That is safe because no consumer mutates it — `parse_registrant_history` /
        `parse_former_names` and `recent_filings` only read — and that property is pinned by
        `test_submissions_memo.py::test_the_memoized_document_is_not_mutated_by_its_consumers`.

        SCOPE, stated because it is easy to overclaim: on a DEGRADED feed this helps only names
        whose assembly reaches a SECOND read. `vinci/dossier/mechanical.py:285`
        (`_drawdown_filings`) is the one submissions call site of 13 with no handler and the FIRST
        to run, so a name carrying
        `earnings_gap_down` events (9 of 17 committed dossiers) still aborts on its first storm and
        the memo is never read twice. Accepted knowingly — STATE.md §5.0 row 16.
        """
        cik10 = pad_cik(cik)
        remembered = self._submissions_memo.get(cik10)
        if remembered is not None:
            if isinstance(remembered, HttpError):
                # A FRESH equivalent, chained to the original: same type and same args, so every
                # existing `except HttpError` / `except (HttpError, KeyError)` handler behaves
                # identically, without re-raising one instance ~13 times and growing its traceback.
                raise HttpError(*remembered.args) from remembered
            return remembered
        try:
            raw = self._http.get_json(_SUBMISSIONS.format(cik=cik10), ttl_seconds=_ONE_DAY)
        except HttpError as exc:
            self._remember_submissions(cik10, exc)
            raise
        doc = cast(dict[str, Any], raw)
        self._remember_submissions(cik10, doc)
        return doc

    def registrant_history(self, cik: int | str) -> RegistrantHistory:
        """This CIK's current registrant name plus every prior span.

        Reads the SAME cached submissions JSON as :meth:`recent_filings` (1-day TTL), so after any
        filing scan this is a cache hit rather than a second fetch."""
        return parse_registrant_history(self._submissions(cik))

    # --- recent filings (8-K detection via submissions) ---------------------------------------
    def recent_filings(
        self, cik: int | str, *, forms: tuple[str, ...] = ("8-K",), since: date | None = None
    ) -> list[Filing]:
        cik10 = pad_cik(cik)
        data = self._submissions(cik10)
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
            rdate_raw = recent.get("reportDate", [""] * n)[i] or ""
            out.append(
                Filing(
                    cik=cik10,
                    form=form,
                    filing_date=fdate,
                    accession=recent["accessionNumber"][i],
                    items=[x.strip() for x in items_raw.split(",") if x.strip()],
                    primary_doc=recent.get("primaryDocument", [None] * n)[i],
                    report_date=date.fromisoformat(rdate_raw) if rdate_raw else None,
                )
            )
        return out
