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

import threading
import urllib.parse
from collections import OrderedDict
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, NoReturn, cast

from pydantic import BaseModel

from vinci.config import Config, get_config
from vinci.edgar.concepts import (
    StaleAnnual,
    currency_withheld,
    current_annual,
    current_pair,
    facts_as_of,
    filed_at,
    filer_fiscal_year,
    foreign_currency,
    leg_refusal,
    negative_leg,
)
from vinci.edgar.net_debt import NO_DEBT_OR_CASH, Basis, net_debt
from vinci.edgar.submissions import RegistrantHistory, parse_registrant_history
from vinci.netcache import CachedHttp, HttpError, HttpNotFoundError
from vinci.resolver.index import pad_cik
from vinci.schemas.envelope import DataField, SourceTier
from vinci.sec import build_efts_http, build_sec_http

_COMPANYFACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
#: an older submissions page, named in the document's `filings.files`. NOT immutable: EDGAR
#: re-cuts the pages from the newest end whenever the recent page's boundary moves, so a page is
#: cached no longer than the document listing it (`_ONE_DAY`) and checked against that listing
_SUBMISSIONS_PAGE = "https://data.sec.gov/submissions/{name}"
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


#: efts serves at most this many hits per request; a later page is asked for with ``from=``.
FTS_PAGE_SIZE = 100
#: How many efts pages one ``fulltext_search`` reads before it stops and says so.
FTS_MAX_PAGES = 5


class FtsResult:
    """The hits one full-text search reads, beside efts's own count of what matched.

    THE COUNT TRAVELS WITH THE HITS (audit E1-D11). The search read one 100-hit page and returned it
    as the answer: 250 matches came back as 100, with nothing a caller could test. ``capped`` is
    the search saying it stopped short — read it, or say why not.

    A PAGE IS READ ONLY WHEN THE CALLER ITERATES INTO IT (review of #871). The covenant search stops
    at two exhibit-bearing hits, each costing an index fetch; reading every page up front cost up to
    four more efts requests a family for hits nobody looked at. The first page is read when the
    search is made, so its failure raises there, as it always has. A LATER page that fails ends the
    search with the hits already read and the reason in ``stopped`` — never by discarding them."""

    def __init__(self, hits: Sequence[FtsHit] = (), total: int = 0, *,
                 page: Callable[[int], dict[str, Any]] | None = None,
                 max_pages: int = FTS_MAX_PAGES) -> None:
        self._hits: list[FtsHit] = list(hits)
        self.total = total  # efts's ``hits.total.value`` — every match, read or not
        self.stopped: str | None = None  # why reading ended before every match, when it did
        self._page = page
        self._next = 0
        self._max_pages = max_pages
        if page is not None:
            self._read_next()

    def _read_next(self) -> bool:
        """Read the next page; False when there is none to read (or it could not be read)."""
        if (self._page is None or self.stopped is not None or self._next >= self._max_pages
                or (self._next and len(self._hits) >= self.total)):
            return False
        n = self._next
        try:
            data = self._page(n)
            got = parse_fts_response(data)
        except HttpError as exc:
            if n == 0:
                raise
            self.stopped = f"page {n + 1} could not be read ({type(exc).__name__})"
            return False
        self.total = max(int((data["hits"].get("total") or {}).get("value", 0)),
                         len(self._hits) + len(got))
        self._hits += got
        self._next += 1
        if not got:
            self._page = None
        return bool(got)

    def __iter__(self) -> Iterator[FtsHit]:
        i = 0
        while i < len(self._hits) or self._read_next():
            yield self._hits[i]
            i += 1

    @property
    def hits(self) -> list[FtsHit]:
        """Every hit the search can read — reads each remaining page."""
        while self._read_next():
            pass
        return self._hits

    @property
    def read(self) -> int:
        """How many hits have been read so far."""
        return len(self._hits)

    @property
    def capped(self) -> bool:
        """True while the hits read fall short of every match."""
        return len(self._hits) < self.total


class Filing(BaseModel, frozen=True):
    """A filing from the submissions feed (used for 8-K event detection)."""

    cik: str
    form: str
    filing_date: date
    accession: str
    items: list[str]  # 8-K item codes, e.g. ["2.02", "9.01"]
    primary_doc: str | None
    report_date: date | None = None  # the period the filing reports ON (10-Q/K balance-sheet as-of)


class AnnualRead(BaseModel, frozen=True):
    """The annual report a DOCUMENT reader reads, and every amendment of it (audit E1-D7,
    operator ruling 2026-11-01) — or, under the same rule, a 10-Q and its 10-Q/As
    (:func:`quarterly_report`, RE1-D12).

    The original is read. An annual /A takes its place only when it carries the period's
    FINANCIAL STATEMENTS — judged by what its accession carries in companyfacts, never by its form
    name (:func:`_statement_accessions`). One fact is not statements: a Part III 10-K/A with an
    Item 402(v) pay-versus-performance table tags the company's net income (Catalyst's carries one
    us-gaap fact and seven ecd), and read as "the annual" it left the segment read UNKNOWN and gave
    the exhibit index EX-31/32 alone (review round 2). A later /A is always named beside the read
    (:attr:`pointer`)."""

    filing: Filing  # the one to read: the original, or an /A carrying the period's statements
    original: Filing
    later: tuple[Filing, ...] = ()  # the annual /As of the original's period filed after it
    restating: frozenset[str] = frozenset()  # accessions among ``later`` carrying the statements
    unjudged: str = ""  # why ``later`` could not be judged, when it could not

    @property
    def judged(self) -> bool:
        return not self.unjudged

    @property
    def pointer(self) -> str | None:
        """One line naming every later /A with its accession, and why it is or is not read."""
        if not self.later:
            return None
        o = self.original
        parts = []
        for a in self.later:
            head = f"{a.form} {a.accession} (filed {a.filing_date}) amends {o.form} {o.accession}"
            if a.accession == self.filing.accession:
                parts.append(f"{head}; read in its place: it carries the period's financial "
                             f"statements")
            elif a.accession in self.restating:
                parts.append(f"{head}; not read: a later amendment carries the period's "
                             f"statements too")
            elif self.unjudged:
                parts.append(f"{head}; not read: not judged — {self.unjudged}")
            else:
                # a 10-K's Part III is its proxy items; a 20-F's is its financial statements
                kind = (" (a Part III or cover amendment)" if a.form in ("10-K/A", "10-KT/A")
                        else "")
                parts.append(f"{head}; not read: it carries no financial statements for the "
                             f"period{kind}")
        return "; ".join(parts)


class FundamentalSnapshot(BaseModel, frozen=True):
    """EDGAR-only fundamentals (no price). Non-distress signals + inputs for step-5 multiples."""

    cik: str
    op_income_sign: DataField[int]
    fcf_sign: DataField[int]
    net_leverage: DataField[float]
    net_debt_to_ocf: DataField[float]  # net debt / operating cash flow — survives untaggable D&A
    ebitda_annual: DataField[float]  # operating income + D&A (for EV/EBITDA in step 5)
    # borrowings + finance leases − cash − short-term investments, every line at ONE balance-sheet
    # date (vinci.edgar.net_debt, the LEVERAGE basis: operating leases out, as EBITDA is post-rent)
    net_debt: DataField[float]
    eps_diluted_annual: DataField[float]  # for P/E in step 5
    as_of: date | None


def _sign(x: float) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


def _present_f(value: float, as_of: date, filed: str) -> DataField[float]:
    """A PRESENT EDGAR figure whose SOURCE says where each leg was filed (audit E1-D5).

    In the source, NEVER the note (review of #875): `mechanical._sourced` carries a field's note
    onto the page, and the web renders any note on a present fact as a "⚠" caveat — a clean figure
    would have read as a warning on every page's Brief."""
    return DataField.present(value, as_of=as_of, source=f"EDGAR {filed}", tier=SourceTier.EDGAR)


def _present_i(value: int, as_of: date, filed: str) -> DataField[int]:
    return DataField.present(value, as_of=as_of, source=f"EDGAR {filed}", tier=SourceTier.EDGAR)


def _unknown_f(note: str) -> DataField[float]:
    return DataField.unknown(source="EDGAR", tier=SourceTier.EDGAR, note=note)


def _unknown_i(note: str) -> DataField[int]:
    return DataField.unknown(source="EDGAR", tier=SourceTier.EDGAR, note=note)


def _why(absent: str, *stale: StaleAnnual | None) -> str:
    """Why a field is UNKNOWN: every leg withheld as stale, by name — else the plain absence."""
    notes = [s.note for s in stale if s]
    return "; ".join(notes) if notes else absent


def all_unknown_snapshot(cik10: str, why: str = "no XBRL") -> FundamentalSnapshot:
    """Snapshot for an issuer with no usable XBRL — every field UNKNOWN (graceful degradation) —
    or none read in dollars, ``why`` naming its currency."""
    return FundamentalSnapshot(
        cik=cik10,
        op_income_sign=_unknown_i(why),
        fcf_sign=_unknown_i(why),
        net_leverage=_unknown_f(why),
        net_debt_to_ocf=_unknown_f(why),
        ebitda_annual=_unknown_f(why),
        net_debt=_unknown_f(why),
        eps_diluted_annual=_unknown_f(why),
        as_of=None,
    )


def compute_fundamental_snapshot(cik10: str, facts: dict[str, Any], *,
                                 as_of: date | None = None) -> FundamentalSnapshot:
    """Pure: derive the non-distress signals + step-5 inputs from a ``companyfacts`` dict.

    ``as_of`` reads the facts as they stood on that date — every row FILED after it is dropped
    before anything is read (:func:`vinci.edgar.concepts.facts_as_of`, which says why the cut is on
    the filing date and not the period end). ``None`` reads every row, as before: the latest the
    blob knows, which on a past date is a lookahead.
    """
    if as_of is not None:
        facts = facts_as_of(facts, as_of)
    # A FILER REPORTING IN ANOTHER CURRENCY (FPI1a): every leg below reads dollars only, so for it
    # each would read "not tagged". Every field names the currency instead. Its signs and
    # one-currency ratios could be read in its own currency; FPI1b converts them, and they return
    # then, in dollars, through these same lines.
    if (cur := foreign_currency(facts)) is not None:
        return all_unknown_snapshot(cik10, currency_withheld(cur))
    # EACH LEG IS THE LATEST ANNUAL ITS CONCEPT SERVES AS CURRENT, or it is withheld and named
    # (vinci.edgar.concepts.current_annual, §5.0 row 11). The latest annual alone was served however
    # old it was: Climb Global's FY2019 capex came off its FY2025 operating cash flow, and
    # AbCellera's FY2023 D&A was added to its FY2025 operating income.
    fy = filer_fiscal_year(facts)
    op, op_stale = current_annual(facts, "operating_income", fy)
    ocf, ocf_stale = current_annual(facts, "operating_cash_flow", fy)
    eps, eps_stale = current_annual(facts, "eps_diluted", fy)
    # A COMBINED FIGURE READS BOTH LEGS FOR ONE FISCAL YEAR (vinci.edgar.concepts.current_pair).
    # Each leg's own latest annual was combined, so a concept stopped on every alias was paired
    # with a current one: Johnson & Johnson's FY2014 operating income with its FY2025 D&A.
    fcf_legs, fcf_stale = current_pair(facts, "operating_cash_flow", "capex", fy)
    ebitda_legs, ebitda_stale = current_pair(facts, "operating_income", "dep_amort", fy)

    # EVERY PRESENT FIGURE SAYS WHERE IT WAS FILED (audit E1-D5): each leg's tag, period, form,
    # accession and day, and the figure it restates when a later filing restated it
    op_sign = (_present_i(_sign(op.value), op.filed, filed_at(op, facts)) if op
               else _unknown_i(_why("no operating_income", op_stale)))
    if fcf_legs:
        fcf_ocf, fcf_capex = fcf_legs
        # a capex filed negative is refused, never taken as filed (audit E1-D12)
        if (bad := negative_leg("capex", fcf_capex)) is not None:
            fcf_sign = _unknown_i(bad)
        else:
            fcf_sign = _present_i(_sign(fcf_ocf.value - fcf_capex.value),
                                  max(fcf_ocf.filed, fcf_capex.filed),
                                  f"{filed_at(fcf_ocf, facts)} − {filed_at(fcf_capex, facts)}")
    else:
        fcf_sign = _unknown_i(fcf_stale.note if fcf_stale else "no OCF/capex")

    ebitda_val: float | None = None
    ebitda_filed = ""
    ebitda_refused: str | None = None
    if ebitda_legs:
        eb_op, eb_da = ebitda_legs
        if (ebitda_refused := leg_refusal("D&A", eb_da)) is not None:
            ebitda = _unknown_f(ebitda_refused)
        else:
            ebitda_val = eb_op.value + eb_da.value
            ebitda_filed = f"{filed_at(eb_op, facts)} + {filed_at(eb_da, facts)}"
            ebitda = _present_f(ebitda_val, max(eb_op.filed, eb_da.filed), ebitda_filed)
    else:
        ebitda = _unknown_f(ebitda_stale.note if ebitda_stale else "no operating_income/D&A")

    # ONE builder, every line at ONE balance-sheet date (vinci.edgar.net_debt, §5.0 row 27 (1)):
    # each leg used to be read at its OWN latest date, so a tag the filer stopped using was served
    # for years. Its refusals carry the cases this block used to spell out: the under-capture
    # witness (the MVST case — a single instrument above the debt read is debt missed, never a
    # confident false net cash), and now a debt line absent from the balance sheet.
    nd = net_debt(facts)
    absent = nd is None or nd.nothing_to_read
    refusal = NO_DEBT_OR_CASH if nd is None else nd.refusal
    net_debt_val: float | None = None
    if absent:
        net_debt_f = _unknown_f(NO_DEBT_OR_CASH)
    elif refusal is not None:
        net_debt_f = _unknown_f(f"{refusal} — pull CIQ")
    else:
        assert nd is not None
        net_debt_val = nd.value(Basis.LEVERAGE)
        assert net_debt_val is not None
        net_debt_f = _present_f(net_debt_val, nd.filed,
                                f"net debt at {nd.at}, cash {filed_at(nd.cash, facts)}")
    # the ratios name the SAME reason, so a refused reading never reads as an absent one
    no_nd = ("no net-debt — debt/cash not in XBRL" if absent or refusal is None
             else f"no net-debt — {refusal}")

    # net leverage = net debt / EBITDA; UNKNOWN with the SPECIFIC missing input — never lump them.
    # "missing debt/cash" and "EBITDA<=0" are different facts: a positive-EBITDA name (e.g. one with
    # 10x interest coverage) reading "EBITDA<=0 or…" mis-reads as distress when the real gap is just
    # that no debt/cash line was in the XBRL.
    if net_debt_val is None:
        net_lev = _unknown_f(no_nd)
    elif ebitda_val is None:
        net_lev = _unknown_f(ebitda_refused or (ebitda_stale.note if ebitda_stale
                                                else "no EBITDA in XBRL"))
    elif ebitda_val <= 0:
        net_lev = _unknown_f("EBITDA<=0 (ratio meaningless)")
    elif not net_debt_f.as_of:
        net_lev = _unknown_f("net-debt as-of date missing")
    else:
        net_lev = _present_f(net_debt_val / ebitda_val, net_debt_f.as_of,
                             f"{net_debt_f.source.removeprefix('EDGAR ')} ÷ EBITDA {ebitda_filed}")

    # net debt / OCF — the leverage read that SURVIVES untaggable D&A (the MVST case): operating
    # cash flow already contains the D&A add-back EBITDA needs, and OCF is reliably tagged. Same
    # fail-loud discipline as net leverage: UNKNOWN naming the SPECIFIC missing input, not a guess.
    if net_debt_val is None:
        net_ocf = _unknown_f(no_nd)
    elif ocf is None:
        net_ocf = _unknown_f(_why("no operating cash flow in XBRL", ocf_stale))
    elif ocf.value <= 0:
        net_ocf = _unknown_f("OCF<=0 (ratio meaningless)")
    elif not net_debt_f.as_of:
        net_ocf = _unknown_f("net-debt as-of date missing")
    else:
        net_ocf = _present_f(net_debt_val / ocf.value, net_debt_f.as_of,
                             f"{net_debt_f.source.removeprefix('EDGAR ')} ÷ "
                             f"{filed_at(ocf, facts)}")

    eps_df = (_present_f(eps.value, eps.filed, filed_at(eps, facts)) if eps
              else _unknown_f(_why("no diluted EPS", eps_stale)))
    read = [op, ocf, eps, *(fcf_legs or ()), *(ebitda_legs or ())]
    filed_dates = [p.filed for p in read if p] + ([nd.filed] if nd else [])
    return FundamentalSnapshot(
        cik=cik10,
        op_income_sign=op_sign,
        fcf_sign=fcf_sign,
        net_leverage=net_lev,
        net_debt_to_ocf=net_ocf,
        ebitda_annual=ebitda,
        net_debt=net_debt_f,
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

    efts uses plural list fields: ``ciks``, ``root_forms`` (the form family, e.g. "8-K" even for an
    "8-K/A" amendment), and ``adsh`` (the accession), with sensible fallbacks.

    THE FORM IS THE FILING'S OWN (TeamNostra fix request 2, RE1-D11). ``form`` states it ("8-K/A"),
    ``root_forms`` its family ("8-K") and ``file_type`` the document the phrase matched ("EX-99.3").
    Read family first, an amendment was reported as "8-K": WERN's credit-agreement 8-K/A of
    2026-04-14 (``0000793074-26-000090``) was its covenant pointer's "8-K". The family is the
    fallback when efts states no form; the document type, the last — and only when it is the main
    document's (an exhibit type such as "EX-99.3" is no form, so the form is then None).
    """
    src = h.get("_source", {})
    ciks = src.get("ciks") or []
    cik = ciks[0] if ciks else None
    root_forms = src.get("root_forms") or []
    doc_type = src.get("file_type")
    if doc_type and str(doc_type).upper().startswith("EX-"):
        doc_type = None
    form = src.get("form") or (root_forms[0] if root_forms else None) or doc_type
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


def _page_filings(cik10: str, rows: dict[str, Any], forms: tuple[str, ...],
                  since: date | None) -> list[Filing]:
    """One submissions page's filings of ``forms`` filed on or after ``since``, in page order
    (newest first). The recent page and every older page share these parallel arrays."""
    out: list[Filing] = []
    n = len(rows.get("accessionNumber", []))
    for i in range(n):
        form = rows["form"][i]
        if form not in forms:
            continue
        fdate = date.fromisoformat(rows["filingDate"][i])
        if since and fdate < since:
            continue
        items_raw = rows.get("items", [""] * n)[i] or ""
        rdate_raw = rows.get("reportDate", [""] * n)[i] or ""
        out.append(
            Filing(
                cik=cik10,
                form=form,
                filing_date=fdate,
                accession=rows["accessionNumber"][i],
                items=[x.strip() for x in items_raw.split(",") if x.strip()],
                primary_doc=rows.get("primaryDocument", [None] * n)[i],
                report_date=date.fromisoformat(rdate_raw) if rdate_raw else None,
            )
        )
    return out


class _StalePageError(Exception):
    """An older submissions page disagrees with the document's listing of it: the two are of
    different vintages. Never an HttpError — `recent_filings` reads the window again, fresh."""


def _page_mismatch(listing: dict[str, Any], rows: dict[str, Any]) -> str | None:
    """How an older page's rows disagree with the document's listing of it, or None.

    Measured on the 35 document/page pairs this machine's caches hold from ONE run (fetched within
    an hour of each other): the row count is the listed `filingCount` on all 35, the oldest row
    is `filingFrom` on all 35, and the newest is at most `filingTo` + 1 day. A page of another
    vintage breaks one of the three — EDGAR re-cuts the pages from the newest end."""
    n = len(rows["accessionNumber"])
    dates = [d for d in rows["filingDate"] if d]
    count, frm, to = listing.get("filingCount"), listing.get("filingFrom"), listing.get("filingTo")
    if count is not None and n != count:
        return f"{n} rows where it lists {count}"
    if dates and frm and min(dates) != frm:
        return f"its oldest row is {min(dates)} where it lists {frm}"
    if dates and to and date.fromisoformat(max(dates)) > date.fromisoformat(to) + timedelta(days=1):
        return f"its newest row is {max(dates)} where it lists {to}"
    return None


@dataclass(frozen=True)
class _RememberedFailure:
    """A remembered ``HttpError``, stored as its TYPE and ARGS — never the instance.

    Storing the exception object keeps its ``__traceback__`` alive, and with it every frame the
    error propagated through and all of their locals — including
    ``CachedHttp._fetch_with_retries``'s ``resp`` (a full SEC error page) and the chained transport
    exception's own frames. Measured at ~12 MB pinned by ONE remembered failure, against the
    ~0.5 MB per document that ``_SUBMISSIONS_MEMO_MAX`` is sized for, and ``assemble_cohort`` runs
    8 clients at once. Type + args is everything the re-raise needs.
    """

    kind: type[HttpError]
    args: tuple[Any, ...]

    def raise_again(self) -> NoReturn:
        raise self.kind(*self.args)


class EdgarClient:
    def __init__(self, http: CachedHttp, efts_http: CachedHttp | None = None) -> None:
        self._http = http
        # efts is rate-sensitive → its own slower client; falls back to the data client if unset.
        self._efts = efts_http or http
        # Per-INSTANCE memo of the parsed submissions document (see `_submissions`). Deliberately a
        # plain mapping rather than `functools.lru_cache` on the method: an lru_cache keys on `self`
        # and would keep every client — and every document it ever touched — alive for the process
        # lifetime. This dies with the client, which is what "for the life of one run" means here.
        #
        # ORDERED + LOCKED. `OrderedDict` so a memo HIT can `move_to_end`, making eviction true LRU:
        # a plain dict evicts by FIRST INSERTION, which would drop the CIK currently being assembled
        # (the one with ~13 reads still ahead of it) the moment a second and third CIK were read.
        # The lock is not optional: this is the first mutable state on `EdgarClient`, and
        # `vinci/themes/exposure.py::scan_driver_exposure` drives ONE client from a
        # `ThreadPoolExecutor` — an unguarded `pop(next(iter(...)))` there raced into
        # `RuntimeError: dictionary changed size during iteration` and `KeyError` under test.
        self._submissions_memo: OrderedDict[str, dict[str, Any] | _RememberedFailure] = (
            OrderedDict()
        )
        self._submissions_lock = threading.Lock()

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
                except HttpNotFoundError:  # no frame for that period (yet) — it contributes nothing
                    continue
                # ANYTHING ELSE RAISES (2026-10-29, audit item E1-D9). A broad `except` here
                # skipped a refused or failing NEWEST frame, and the older period below it was
                # then served under the same tag with nothing to say it was a quarter stale.
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

    def fundamental_snapshot(self, cik: int | str, *,
                             as_of: date | None = None) -> FundamentalSnapshot:
        """Non-distress signals + step-5 inputs, each enveloped (UNKNOWN where XBRL is absent).
        ``as_of`` cuts at the filing date (:func:`compute_fundamental_snapshot`)."""
        return self.fundamental_snapshot_and_facts(cik, as_of=as_of)[0]

    def fundamental_snapshot_and_facts(
            self, cik: int | str, *, as_of: date | None = None,
    ) -> tuple[FundamentalSnapshot, dict[str, Any]]:
        """The snapshot AND the companyfacts it was computed from, from ONE read — ``{}`` with an
        all-UNKNOWN "no XBRL" snapshot when SEC holds no companyfacts for the CIK.

        ONLY A 404 IS "NO XBRL" (2026-10-29, audit item E1-D8). A broad `except` mapped every
        failure to it, so a 503 that outlived its retries recorded a filer as having no XBRL while
        the next request read its data; and a caller that read companyfacts a second time (the
        screen did) could disagree with its own snapshot. A throttle, a 5xx or a corrupt body
        now RAISES, with its real reason."""
        cik10 = pad_cik(cik)
        try:
            facts = self.companyfacts(cik10)
        except HttpNotFoundError:  # SEC holds no companyfacts for this CIK: no XBRL
            return all_unknown_snapshot(cik10), {}
        return compute_fundamental_snapshot(cik10, facts, as_of=as_of), facts

    # --- 8-K full-text search (the de-rating trigger) -----------------------------------------
    def fulltext_search(
        self,
        phrase: str,
        *,
        forms: str = "8-K",
        ciks: str | None = None,
        startdt: str | None = None,
        enddt: str | None = None,
        max_pages: int = FTS_MAX_PAGES,
    ) -> FtsResult:
        """Search EDGAR full text for an exact phrase. Spaces → %20 (an efts requirement).

        ``ciks`` scopes the search to a single filer — pass the 10-digit ZERO-PADDED CIK (a bare
        integer returns nothing; efts requires the padded form). Without it a phrase like
        "Convertible Bond" matches ANY filer, so a covenant lookup MUST scope to the subject.

        Reads the first page now and each later one only as the caller iterates, until every match
        is read or ``max_pages`` is spent; ``capped`` and ``stopped`` say which. The first page's
        URL carries no ``from=``, as it always has."""
        q = urllib.parse.quote(f'"{phrase}"')  # quote() => spaces become %20, not '+'
        url = f"{_EFTS}?q={q}&forms={forms}"
        if ciks:
            url += f"&ciks={pad_cik(ciks)}"  # 10-digit; a bare int yields an empty efts result
        if startdt and enddt:
            url += f"&startdt={startdt}&enddt={enddt}"
        def page(n: int) -> dict[str, Any]:
            return cast(dict[str, Any], self._efts.get_json(
                f"{url}&from={n * FTS_PAGE_SIZE}" if n else url, ttl_seconds=_ONE_DAY))
        return FtsResult(page=page, max_pages=max_pages)

    # --- registrant names (reverse-merger / rename vintage) ------------------------------------
    def _remember_submissions(
        self, cik10: str, outcome: dict[str, Any] | _RememberedFailure
    ) -> None:
        """Record one CIK's outcome, evicting LEAST-RECENTLY-USED past ``_SUBMISSIONS_MEMO_MAX``.

        Locked, and `popitem(last=False)` rather than `pop(next(iter(...)))` — the latter reads the
        mapping while mutating it, which races on the one client shared across threads."""
        with self._submissions_lock:
            self._submissions_memo[cik10] = outcome
            self._submissions_memo.move_to_end(cik10)
            while len(self._submissions_memo) > _SUBMISSIONS_MEMO_MAX:
                self._submissions_memo.popitem(last=False)

    def _recall_submissions(self, cik10: str) -> dict[str, Any] | _RememberedFailure | None:
        """The remembered outcome for ``cik10``, or None on a miss — refreshing LRU position.

        A separate reader so the whole hit path is inside one lock acquisition; the fetch on a miss
        deliberately runs OUTSIDE the lock (holding it across the network would serialise every
        worker, and a duplicate fetch is absorbed by the disk cache)."""
        with self._submissions_lock:
            remembered = self._submissions_memo.get(cik10)
            if remembered is not None:
                self._submissions_memo.move_to_end(cik10)
            return remembered

    def _submissions(self, cik: int | str, *, fresh: bool = False) -> dict[str, Any]:
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

        SCOPE. This helps any assembly that reaches a SECOND read, which is now all of them.
        Until 2026-09-02 it was not: `_drawdown_filings` was the one submissions call site of 13
        with no handler and the FIRST to run, so a name carrying `earnings_gap_down` events (9 of 17
        committed dossiers) aborted the whole assembly on its first storm and never reached the
        memo. `_drawdown_cause` now catches `HttpError` and degrades to UNKNOWN, so the measured
        187.4 s -> 15.5 s applies to every name rather than to the no-gap subset.

        ``fresh`` fetches past the memo and the disk cache: a window whose older page disagrees
        with this document's listing reads both again (:meth:`recent_filings`).
        """
        cik10 = pad_cik(cik)
        remembered = None if fresh else self._recall_submissions(cik10)
        if remembered is not None:
            if isinstance(remembered, _RememberedFailure):
                # A FRESH equivalent of the SAME type with the SAME args, so every existing
                # `except HttpError` / `except (HttpError, KeyError)` handler behaves identically.
                remembered.raise_again()
            return remembered
        try:
            raw = self._http.get_json(_SUBMISSIONS.format(cik=cik10),
                                      ttl_seconds=0.0 if fresh else _ONE_DAY)
        except HttpError as exc:
            self._remember_submissions(cik10, _RememberedFailure(type(exc), exc.args))
            raise
        if not isinstance(raw, dict):
            # FAIL LOUD rather than memoize a non-object. A JSON `null` body stored as `None` would
            # be indistinguishable from a memo MISS on every later read (re-fetching 13 times
            # silently), and would then `AttributeError` inside `recent_filings`' `data.get(...)`.
            # Raising here makes it an HttpError, which the consumers already degrade on.
            raise HttpError(
                f"submissions payload for CIK{cik10} is {type(raw).__name__}, not a JSON object"
            )
        self._remember_submissions(cik10, raw)
        return raw

    def registrant_history(self, cik: int | str) -> RegistrantHistory:
        """This CIK's current registrant name plus every prior span.

        Reads the SAME cached submissions JSON as :meth:`recent_filings` (1-day TTL), so after any
        filing scan this is a cache hit rather than a second fetch."""
        return parse_registrant_history(self._submissions(cik))

    def state_of_incorporation(self, cik: int | str) -> tuple[str, str] | None:
        """EDGAR's state-or-country-of-incorporation CODE for this CIK (``"A6"``, ``"E9"``,
        ``"X0"``) with EDGAR's own description of it, or None when EDGAR leaves it blank (it does
        for about a quarter of foreign filers). The code is the structured value; the description
        is for display only.

        CURRENT, NOT POINT-IN-TIME: the submissions document carries today's value, so a
        registrant that re-domiciled reads as it is now. Same cached document as
        :meth:`recent_filings`."""
        sub = self._submissions(cik)
        code = str(sub.get("stateOfIncorporation") or "").strip().upper()
        if not code:
            return None
        return code, str(sub.get("stateOfIncorporationDescription") or "").strip()

    # --- recent filings (8-K detection via submissions) ---------------------------------------
    def recent_page_span(self, cik: int | str) -> tuple[date, date] | None:
        """The first and last filing dates on the submissions document's RECENT page, or None
        when it holds no dated row. SEC: the recent page "contains at least one year's of filing
        or to 1,000 (whichever is more) of the most recent filings" (sec.gov's EDGAR API page) —
        so its span is how far a no-window read reaches back from the newest filing, the reach a
        view cut in the past applies from its cut (:class:`vinci.edgar.asof.AsOfEdgar`, RE1-D8).
        Same cached document as :meth:`recent_filings`."""
        recent = self._submissions(cik).get("filings", {}).get("recent", {})
        try:
            dates = [date.fromisoformat(d) for d in recent.get("filingDate") or [] if d]
        except ValueError as exc:
            raise HttpError(f"the submissions document for CIK{pad_cik(cik)} carries a filing "
                            f"date that is not a date: {exc}") from exc
        return (min(dates), max(dates)) if dates else None

    def recent_filings(
        self, cik: int | str, *, forms: tuple[str, ...] = ("8-K",), since: date | None = None
    ) -> list[Filing]:
        """The filer's filings of ``forms``, newest first — those filed on or after ``since``.

        A WINDOW READS EVERY PAGE IT OVERLAPS (audit E1-D10). The submissions document holds a
        filer's newest ~1,000 filings in `filings.recent` and lists the rest as older pages
        (`filings.files`); reading `recent` alone ended a long window silently at its first row
        (Gartner's recent page starts 2021-12-02). When ``since`` falls before the recent page, each
        older page whose span reaches ``since`` is read too, through the same SEC client and its
        shared limiter; a page that cannot be read RAISES, naming it — never a short list that reads
        as "no filings" (:meth:`_older_filings`). With no ``since`` only the recent page is read, as
        before: the caller asked for no window.

        A PAGE OF ANOTHER VINTAGE IS READ AGAIN, never joined (review round 2). EDGAR re-cuts the
        older pages from the newest end whenever the recent page's boundary moves, so a page cached
        apart from its document leaves a hole before the recent page or repeats its rows. Each page
        is checked against the listing that names it (:func:`_page_mismatch`); on a disagreement
        the document and its pages are fetched fresh once, and a second disagreement raises."""
        cik10 = pad_cik(cik)
        if since is None:
            recent = self._submissions(cik10).get("filings", {}).get("recent", {})
            return _page_filings(cik10, recent, forms, since)
        try:
            return self._window(cik10, forms, since, fresh=False)
        except _StalePageError:
            return self._window(cik10, forms, since, fresh=True)

    def _window(self, cik10: str, forms: tuple[str, ...], since: date, *,
                fresh: bool) -> list[Filing]:
        """The recent page's filings and every overlapping older page's, each accession once."""
        filings = self._submissions(cik10, fresh=fresh).get("filings", {})
        recent = filings.get("recent", {})
        out = _page_filings(cik10, recent, forms, since)
        seen = {f.accession for f in out}
        for f in self._older_filings(cik10, recent, filings.get("files") or [], forms, since,
                                     fresh=fresh):
            if f.accession not in seen:  # pages are disjoint; a repeat is a vintage's residue
                seen.add(f.accession)
                out.append(f)
        return out

    def _older_filings(self, cik10: str, recent: dict[str, Any], files: list[dict[str, Any]],
                       forms: tuple[str, ...], since: date, *, fresh: bool) -> list[Filing]:
        """The filings of ``forms`` on the older submissions pages a window from ``since``
        overlaps, newest page first — none when the recent page already reaches back to ``since``.

        Every way a page can fail to be read is an HttpError naming it: unreachable, answered
        with something that is not JSON (an interstitial's ValueError), not an object, missing its
        arrays, or listed with no name. Several windowed callers degrade only an HttpError to
        UNKNOWN, so any other exception here would abort an assembly over one page. A page whose
        rows disagree with its listing raises `_StalePageError` on a cached read, and an HttpError
        naming the disagreement on a ``fresh`` one."""
        why = f"so the filings window from {since} is incomplete"
        try:
            # a blank date on a row the caller did not ask for is not read here either
            dates = [date.fromisoformat(d) for d in recent.get("filingDate") or [] if d]
        except ValueError as exc:
            raise HttpError(f"the submissions document for CIK{cik10} carries a filing date that "
                            f"is not a date, {why}: {exc}") from exc
        if not files or (dates and min(dates) <= since):
            return []
        out: list[Filing] = []
        for page in files:
            name = page.get("name")
            if not name:
                raise HttpError(f"an older submissions page for CIK{cik10} is listed with no "
                                f"name, {why}")
            try:
                to = page.get("filingTo")
                # a page's rows run to its listed `filingTo` + 1 day (17 of 35 same-run pairs)
                if to and date.fromisoformat(to) + timedelta(days=1) < since:
                    continue  # wholly before the window
                rows = self._older_page(str(name), fresh=fresh)
                if not isinstance(rows, dict):
                    raise TypeError(f"{type(rows).__name__}, not a JSON object")
                stale = _page_mismatch(page, rows)
                if stale is None:
                    out += _page_filings(cik10, rows, forms, since)
            except (HttpError, ValueError, KeyError, TypeError, IndexError) as exc:
                raise HttpError(f"older submissions page {name} for CIK{cik10} could not be read, "
                                f"{why}: {type(exc).__name__}: {exc}") from exc
            if stale is not None:
                if not fresh:
                    raise _StalePageError(str(name))
                raise HttpError(f"older submissions page {name} for CIK{cik10} disagrees with the "
                                f"document's listing of it, read fresh ({stale}), {why}")
        return out

    def _older_page(self, name: str, *, fresh: bool = False) -> Any:
        """One older submissions page. Its FAILURE is remembered in the submissions memo under the
        page's name, as `_submissions` remembers the document's: one assembly makes several
        windowed reads of a filer, and a degraded feed would otherwise re-run the retry storm at
        each. A page READ is not remembered — the disk holds it, and a heavy filer's pages would
        evict the document. Only the first failing page of a window is ever reached, so a filer's
        memo holds at most its document and that page."""
        remembered = self._recall_submissions(name)
        if isinstance(remembered, _RememberedFailure):
            remembered.raise_again()
        try:
            return self._http.get_json(_SUBMISSIONS_PAGE.format(name=name),
                                       ttl_seconds=0.0 if fresh else _ONE_DAY)
        except HttpError as exc:
            self._remember_submissions(name, _RememberedFailure(type(exc), exc.args))
            raise


# --- amended filings (audit E1-D7, operator ruling 2026-11-01) ------------------------------
# Module functions over any client with `recent_filings` / `companyfacts`, so the readers' test
# doubles serve them unchanged.

def annual_report(edgar: EdgarClient, cik: int | str, *, forms: tuple[str, ...],
                  through: date | None = None) -> AnnualRead | None:
    """The newest annual report of ``forms`` filed by ``through`` (any day when None), as a
    DOCUMENT reader reads it — :class:`AnnualRead` holds the rule. None when there is none.

    An amendment belongs to the original when its period of report is the original's (or
    either does not state one) and it was filed on or after it. Companyfacts is read only when
    an amendment exists; when it cannot be read the original is read and the pointer says the
    amendment could not be judged."""
    amended = tuple(f"{f}/A" for f in forms)
    rows = [f for f in edgar.recent_filings(cik, forms=forms + amended)
            if through is None or f.filing_date <= through]
    originals = [f for f in rows if f.form in forms]
    if not originals:
        return None
    orig = max(originals, key=lambda f: f.filing_date)
    later = tuple(sorted(
        (f for f in rows if f.form in amended and f.filing_date >= orig.filing_date
         and (f.report_date is None or orig.report_date is None
              or f.report_date == orig.report_date)),
        key=lambda f: f.filing_date))
    if not later:
        return AnnualRead(filing=orig, original=orig)
    restating, unjudged = _statement_accessions(edgar, cik, orig, later)
    read = max((f for f in later if f.accession in restating),
               key=lambda f: f.filing_date, default=orig)
    return AnnualRead(filing=read, original=orig, later=later, restating=restating,
                      unjudged=unjudged)


def quarterly_report(edgar: EdgarClient, cik: int | str, *,
                     through: date | None = None) -> AnnualRead | None:
    """The newest 10-Q filed by ``through`` (any day when None), as a DOCUMENT reader reads it,
    under the SAME rule as :func:`annual_report` (TeamNostra fix request 2, RE1-D12): the original
    is read; a 10-Q/A takes its place only when it carries the quarter's financial statements,
    judged from companyfacts (a balance-sheet total at the quarter's end, an income line, and half
    the original's tags — :func:`_statement_accessions`); a later 10-Q/A is always named
    (:attr:`AnnualRead.pointer`). The readers listed ``forms=("10-Q",)``, so a 10-Q/A was neither
    read nor named. None when the filer has filed no 10-Q."""
    return annual_report(edgar, cik, forms=("10-Q",), through=through)


#: The balance-sheet totals and income-statement lines whose presence, for the period, marks an
#: amendment as carrying the statements (us-gaap, and ifrs-full's `Assets` / `Revenue` …).
_BALANCE_TOTALS = frozenset({"Assets", "LiabilitiesAndStockholdersEquity", "EquityAndLiabilities"})
_INCOME_LINES = frozenset({"Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                           "RevenueFromContractWithCustomerIncludingAssessedTax", "Revenue",
                           "NetIncomeLoss", "ProfitLoss", "OperatingIncomeLoss"})
#: …and the share of the original's own period tags it must carry. Set by face validity on the
#: cache (review round 2): the 27 cached /As that re-file statements carry 1.00–1.04 of their
#: original's tags; the pay-versus-performance /As 0.00–0.01, and BMO's 40-F/A 0.08 with no
#: income line. The threshold sits in that gap, not at any outcome.
_STATEMENT_SHARE = 0.5


def _period_tags(facts: dict[str, Any], accession: str,
                 end: str) -> tuple[frozenset[str], bool, bool]:
    """The us-gaap/ifrs-full tags ``accession`` carries for the period ending ``end``, whether one
    is a balance-sheet total stated at that instant, and whether one is an income line. The ecd
    namespace (pay versus performance) and dei never count."""
    tags: set[str] = set()
    balance = income = False
    for ns in ("us-gaap", "ifrs-full"):
        for tag, node in (facts.get("facts") or {}).get(ns, {}).items():
            for rows in node.get("units", {}).values():
                for r in rows:
                    if r.get("accn") != accession or r.get("end") != end:
                        continue
                    tags.add(tag)
                    balance |= tag in _BALANCE_TOTALS and not r.get("start")
                    income |= tag in _INCOME_LINES
    return frozenset(tags), balance, income


def _statement_accessions(edgar: EdgarClient, cik: int | str, orig: Filing,
                          later: tuple[Filing, ...]) -> tuple[frozenset[str], str]:
    """The accessions among ``later`` that carry the period's financial statements, and why none
    could be judged when none could ("" otherwise).

    An /A carries them when it states, for the original's period, a balance-sheet total AND an
    income line AND at least :data:`_STATEMENT_SHARE` of the tags the original states for it (the
    share is vacuous when the original states none: Willis Lease's 10-K carries no fact for FY2025
    and its 10-K/A 241). Companyfacts that cannot be read — unreachable, or a body that is not
    JSON — judges nothing; nor does an original whose period, and every /A's, carries no fact."""
    if orig.report_date is None:
        return frozenset(), "the original states no period of report"
    try:
        facts = edgar.companyfacts(cik)
    except HttpNotFoundError:
        facts = {}  # no XBRL at all: nothing carries statements
    except (HttpError, ValueError) as exc:  # ValueError: a 200 body that is not JSON
        return frozenset(), f"companyfacts could not be read ({type(exc).__name__})"
    end = orig.report_date.isoformat()
    base, _, _ = _period_tags(facts, orig.accession, end)
    carrying = set()
    for a in later:
        tags, balance, income = _period_tags(facts, a.accession, end)
        if balance and income and len(tags) >= _STATEMENT_SHARE * len(base):
            carrying.add(a.accession)
    if not base and not carrying:
        return frozenset(), "companyfacts carries no fact for the original either"
    return frozenset(carrying), ""


def events(edgar: EdgarClient, cik: int | str, *,
           since: date | None = None) -> list[Filing]:
    """The filer's 8-K EVENTS, newest first, for a reader that selects or classifies on item
    codes (audit E1-D7, operator ruling 2026-11-01: "the event is the original's").

    An 8-K/A's ORIGINAL is an 8-K of the same period of report that shares an item code with it
    other than 9.01 (the exhibits item every 8-K carries). It counts only for the codes it adds
    over its original(s), and is returned carrying those alone. One with no original is NEVER a
    new event and counts nothing (review round 2): matched on the report date alone, PHIN's 4.01
    8-K/A of 2026-02-12 met that day's earnings 8-K and "added" a second auditor change, and
    Worthington Steel's 8-K/A re-filing its 2026-06-25 earnings, with no original of its report
    date, moved the latest print to 07-10. Measured on the 477 cached 8-K/As filed in the year to
    2026-11-01, keyed so: 268 add nothing, 31 add a code, 178 have no original; MEDS's of
    2026-04-21 keeps the 3.01 its 2026-04-17 original lacks. Keyed instead on the same primary
    document, MEDS's lost it and PHIN's kept its 4.01."""
    # `since` only when given, as each reader asked before: a no-window read is the recent page
    rows = (edgar.recent_filings(cik, forms=("8-K", "8-K/A")) if since is None
            else edgar.recent_filings(cik, forms=("8-K", "8-K/A"), since=since))
    amends = [f for f in rows if f.form == "8-K/A"]
    if not amends:
        return rows
    if since is None:
        # NO WINDOW, so only the recent page was read, and no older page is read for an
        # original: one that lies there leaves its amendment with no original, counting nothing
        # (ORKA's 8-K/A of 2009 had sent the print, termination and release readers to pages
        # they had never needed).
        pool = rows
    else:
        # an original is filed on or after its own period of report, so this reaches every one
        lo = min(f.report_date or f.filing_date for f in amends)
        pool = rows if lo >= since else edgar.recent_filings(cik, forms=("8-K",), since=lo)
    by_date: dict[date, list[set[str]]] = {}
    for f in pool:
        if f.form == "8-K" and f.report_date is not None:
            by_date.setdefault(f.report_date, []).append(set(f.items))
    out: list[Filing] = []
    for f in rows:
        if f.form == "8-K":
            out.append(f)
            continue
        own = set(f.items) - {"9.01"}
        same_day = by_date.get(f.report_date, []) if f.report_date is not None else []
        originals = [c for c in same_day if own & (c - {"9.01"})]
        if not originals:
            continue  # no original: never a new event
        have = set().union(*originals)
        added = [x for x in f.items if x not in have]
        if added:
            out.append(f.model_copy(update={"items": added}))
    return out
