"""THE EX-LEASE EV/EBITDA HISTORY — one basis across ASC 842, for the names where rent matters.

WHY (2026-10-19). R1 re-rates mid-cycle EBITDA (EBIT + D&A, REPORTED, i.e. after rent) at the
median of CIQ's own TEV/LTM EBITDA history, then subtracts lease-inclusive net debt. CIQ's history
is on two bases: since ASC 842 its TEV carries operating leases and its EBITDA adds rent back
(EBITDAR in all but name), and before 842 it did neither. Measured on the committed fleet's CIQ
exports: TJX's implied margin reads reported EBITDA on 9 closes and EBITDA+rent on 27; BURL 9 and
20. So R1 priced reported EBITDA at an EBITDA+rent multiple and then took the leases off again —
on TJX, rent 45% of EBITDA, that understated the anchor by about a third.

THE FIX IS THE EXPERT CONVENTION, ONE PAIR PER SIDE. EV including leases goes with EBITDA plus
rent; EV excluding operating leases goes with reported EBITDA. R1's numerator is reported EBITDA,
so its history and its bridge are both put on the second basis:

    multiple_t = (CIQ TEV_t − operating leases inside TEV_t) ÷ CIQ LTM EBITDA_t

at every quarter the CIQ export prices (Historical Capitalization: TEV at the balance-sheet date,
priced at the filing date). Finance leases stay in — they are debt under either convention.

WHAT IS INSIDE CIQ's TEV IS CHECKED, NOT ASSUMED. CIQ's Total Debt carries two lease rows ('Curr.
Port. of Leases', 'Long-Term Leases'). Those rows less EDGAR's finance leases must equal EDGAR's
operating-lease liability on the same date, within :data:`RECONCILE_TOL`; where CIQ files its
finance leases outside the lease rows, the rows alone must equal it (UBER). A date that matches
neither is UNRECONCILED and left out of the band; too many of them and there is no band.

MATERIALITY DECIDES WHETHER R1 NEEDS THIS AT ALL. Rent below :data:`MATERIALITY` of EBITDA moves
the anchor by roughly that fraction or less, so an immaterial name keeps CIQ's history (no churn
on LLY, V, GOOGL…). A material name with no usable ex-lease band has NO usable multiple — the
anchor refuses rather than fall back to the mixed series. Rent that cannot be measured counts as
material: an unmeasured number is never assumed small.

Every threshold here is set by face validity, never by what any name's anchor would come to.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, NamedTuple

from vinci.dossier.ciq import CiqBundle, CiqUnavailableError, clean_num, excel_date
from vinci.dossier.ciq_sheets import _MIN_CONFIDENT_CLOSES, _own_history_band, file_provenance
from vinci.dossier.schemas import LeaseBasis, LeaseObservation, OwnHistoryBand
from vinci.edgar.concepts import points_for_tag

#: Rent ÷ EBITDA at which leases are material. R1's understatement on the mixed history is about
#: the multiple × rent, i.e. roughly this fraction of EV — five percent is the first level a
#: reader of an anchor would call a different number rather than the same one.
MATERIALITY = 0.05
#: How far CIQ's operating leases may sit from EDGAR's on one date. A tolerance on the LEASE
#: balance, so the error it admits is a fraction of a fraction of TEV.
RECONCILE_TOL = 0.02
#: A band survives at most this share of unreconciled dates among those EDGAR lets us check, and
#: needs at least `MIN_RECONCILED` checked ones — a year of quarters — to say the split is CIQ's.
MAX_UNRECONCILED_SHARE = 0.10
MIN_RECONCILED = 4
#: EDGAR's operating figure must sit on the balance-sheet date (a week either side for 52/53-week
#: years); a finance-lease figure may come from the nearest filing within about two quarters,
#: because many filers tag it only at year-end.
_OPERATING_NEAR_DAYS = 7
_FINANCE_NEAR_DAYS = 200
#: four consecutive quarters end ~273 days after the first one ends; a gap outside this means a
#: quarter is missing (or the columns are not quarters at all), and no LTM is summed across it.
_LTM_SPAN_DAYS = (240, 300)
#: CIQ's lease rows below this share of EDGAR's operating figure, where that figure is a LATER
#: COMPARATIVE: CIQ's balance sheet for the quarter, as originally filed, predates the standard.
_PRE_ADOPTION_SHARE = 0.5
#: A figure first filed more than this many days after its period end was not in the period's own
#: report (a 10-Q is due within 40-45 days, a 10-K within 60-90): it is a comparative a later
#: filing added — TJX's 2019-02-02 opening balance, TGT's 2017 quarters restated when it adopted
#: ASC 842 early in 2018. CIQ's balance sheet for such a quarter is the one ORIGINALLY filed.
_ORIGINAL_FILING_DAYS = 100

METRIC = "EV/EBITDA ex-lease (TEV less operating leases / LTM EBITDA)"
SOURCE_REF = (
    "CIQ Financials (Quarterly)→Historical Capitalization 'Total Enterprise Value' less the "
    "operating leases inside it (Balance Sheet 'Curr. Port. of Leases' + 'Long-Term Leases' less "
    "EDGAR FinanceLeaseLiability), over Income Statement 'EBITDA' summed over four quarters; "
    "checked against EDGAR OperatingLeaseLiability. Materiality: CIQ Financials (Annual)→Income "
    "Statement 'Net Rental Exp.' / 'EBITDA'")

_OPERATING_TAGS = ("OperatingLeaseLiability", "OperatingLeaseLiabilityCurrent",
                   "OperatingLeaseLiabilityNoncurrent")
_FINANCE_TAGS = ("FinanceLeaseLiability", "FinanceLeaseLiabilityCurrent",
                 "FinanceLeaseLiabilityNoncurrent")

Rows = list[list[Any]]


class Rent(NamedTuple):
    rent: float | None
    ebitda: float | None
    fiscal_year: date | None


def _header_date(cell: Any) -> date | None:
    """A CIQ column header → its period-end date. Headers arrive as an Excel serial or as stacked
    text ('3 months\\nQ1\\nApr-30-2016', 'Reclassified\\n12 months\\nDec-31-2017'), whose LAST
    line is the date. An LTM column is not a fiscal period and is refused here."""
    if isinstance(cell, (int, float)) and not isinstance(cell, bool):
        return excel_date(cell)
    text = str(cell or "").strip()
    if not text or "LTM" in text:
        return None
    return excel_date(text.splitlines()[-1].strip())


def _row(rows: Rows, label: str, *, prefix: bool = False) -> list[Any] | None:
    for r in rows:
        if not r:
            continue
        head = str(r[0]).strip()
        if head == label or (prefix and head.startswith(label)):
            return r
    return None


def _cells(header: list[Any] | None, row: list[Any] | None) -> dict[date, Any]:
    """{period-end: raw cell} for one row under its header."""
    if header is None or row is None:
        return {}
    out: dict[date, Any] = {}
    for h, v in zip(header[1:], row[1:], strict=False):
        d = _header_date(h)
        if d is not None:
            out[d] = v
    return out


def _dated(header: list[Any] | None, row: list[Any] | None) -> dict[date, float | None]:
    """{period-end: value} for one row under its header; `clean_num` maps NA/NM/'-' to None."""
    return {d: clean_num(v) for d, v in _cells(header, row).items()}


def rent_share(bundle: CiqBundle) -> Rent:
    """Rent and EBITDA ($M) on the latest full fiscal year CIQ's ANNUAL income statement reports
    both for. (None, None, None) when the export or either row is absent."""
    try:
        rows = bundle.sheet("financials", "Income Statement", freq="annual")
    except CiqUnavailableError:
        return Rent(None, None, None)
    header = _row(rows, "For the Fiscal Period Ending", prefix=True)
    rent = _dated(header, _row(rows, "Net Rental Exp."))
    ebitda = _dated(header, _row(rows, "EBITDA"))
    both = [d for d in rent if rent[d] is not None and ebitda.get(d) is not None]
    if not both:
        return Rent(None, None, None)
    fy = max(both)
    return Rent(rent[fy], ebitda[fy], fy)


def _instants(facts: dict[str, Any], tag: str) -> dict[date, float]:
    """{period_end: $M} for one balance-sheet tag, the latest filing winning each date."""
    best: dict[date, tuple[date, float]] = {}
    for p in points_for_tag(facts, tag):
        if p.is_instant and (p.period_end not in best or p.filed >= best[p.period_end][0]):
            best[p.period_end] = (p.filed, p.value / 1e6)
    return {d: v for d, (_f, v) in best.items()}


def _first_filed(facts: dict[str, Any], tag: str) -> dict[date, date]:
    """{period_end: the EARLIEST filing date carrying it} for one balance-sheet tag."""
    out: dict[date, date] = {}
    for p in points_for_tag(facts, tag):
        if p.is_instant and (p.period_end not in out or p.filed < out[p.period_end]):
            out[p.period_end] = p.filed
    return out


def _complete(facts: dict[str, Any], total: str, cur: str, non: str) -> dict[date, float]:
    """The COMPLETE liability by date: the total tag, else current + noncurrent where BOTH are
    tagged that day. A noncurrent-only date is not a complete figure (TGT's 10-Qs) and is absent."""
    out = _instants(facts, total)
    c, n = _instants(facts, cur), _instants(facts, non)
    for d in c.keys() & n.keys():
        out.setdefault(d, c[d] + n[d])
    return out


def _complete_first_filed(facts: dict[str, Any], total: str, cur: str,
                          non: str) -> dict[date, date]:
    """When each date's COMPLETE figure first existed in a filing — the total tag's first filing,
    else the later of the two parts' (a sum exists once both parts have been filed)."""
    out = _first_filed(facts, total)
    c, n = _first_filed(facts, cur), _first_filed(facts, non)
    for d in c.keys() & n.keys():
        out.setdefault(d, max(c[d], n[d]))
    return out


def _near(series: dict[date, float], at: date, days: int) -> float | None:
    close = [d for d in series if abs((d - at).days) <= days]
    return series[min(close, key=lambda d: abs((d - at).days))] if close else None


def _first_operating(facts: dict[str, Any]) -> date | None:
    """The first date EDGAR reports a positive operating-lease liability under ANY of the three
    tags — the filer's adoption of ASC 842 as its filings show it."""
    dates = [d for t in _OPERATING_TAGS for d, v in _instants(facts, t).items() if v > 0]
    return min(dates) if dates else None


class _Split(NamedTuple):
    operating: float
    status: str
    finance_inside: bool | None   # which decomposition reconciled (None: not checked)


def _reconciles(rows_sum: float, fin: float, op_edgar: float) -> bool | None:
    """Whether CIQ's lease rows decompose as EDGAR's operating leases plus its finance leases
    (True), or ARE the operating leases with finance filed elsewhere (False); None: neither."""
    for fin_in in (True, False):
        if abs(max(rows_sum - (fin if fin_in else 0.0), 0.0) - op_edgar) <= (
                RECONCILE_TOL * op_edgar):
            return fin_in
    return None


def _split(rows_sum: float, fin: float, op_edgar: float | None, *, adopted: bool,
           comparative: bool, nearest: bool | None) -> _Split:
    """How much of CIQ's lease rows is OPERATING on one date, and how sure we are.

    ``comparative``: EDGAR's operating figure for the date was first filed AFTER the period's own
    report (:data:`_ORIGINAL_FILING_DAYS`) — an adoption-date opening balance or a restated
    comparative. CIQ's balance sheet for that quarter is the one originally filed, so a short lease
    row there is the standard not yet applied. Where the figure WAS in the period's own report, a
    short row is a data gap and the quarter is unreconciled — wherever it sits in the history
    (review of #750: a position-based rule let any early short quarter pass as pre-adoption).
    ``nearest``: the split the nearest reconciled quarter (either side) proved, for a quarter
    EDGAR gives no complete figure to check; None when no quarter reconciled at all."""
    if not adopted or (op_edgar is not None and op_edgar <= 0):
        return _Split(0.0, "pre-adoption", None)
    if op_edgar is None:
        inside = nearest if nearest is not None else True
        return _Split(max(rows_sum - (fin if inside else 0.0), 0.0), "unchecked", None)
    proved = _reconciles(rows_sum, fin, op_edgar)
    if proved is not None:
        return _Split(max(rows_sum - (fin if proved else 0.0), 0.0), "reconciled", proved)
    if comparative and rows_sum < _PRE_ADOPTION_SHARE * op_edgar:
        return _Split(0.0, "pre-adoption", None)
    return _Split(max(rows_sum - fin, 0.0), "unreconciled", None)


def observations(bundle: CiqBundle, facts: dict[str, Any]) -> list[LeaseObservation]:
    """Every quarter the quarterly export can price on the ex-lease basis, oldest first."""
    hc = bundle.sheet("financials", "Historical Capitalization", freq="quarterly")
    bs = bundle.sheet("financials", "Balance Sheet", freq="quarterly")
    inc = bundle.sheet("financials", "Income Statement", freq="quarterly")
    hc_head = _row(hc, "Balance Sheet as of", prefix=True)
    tev = _dated(hc_head, _row(hc, "= Total Enterprise Value", prefix=True))
    # A DATE ROW, read as dates: a serial, a datetime or 'Mar-28-2017' text all parse; a numeric
    # read would drop the last two and silently date those quarters at their balance sheet
    priced = {d: excel_date(c) for d, c in _cells(
        hc_head, _row(hc, "Pricing as of", prefix=True)).items() if c not in (None, "")}
    bs_head = _row(bs, "Balance Sheet as of", prefix=True)
    cur_l = _dated(bs_head, _row(bs, "Curr. Port. of Leases"))
    lt_l = _dated(bs_head, _row(bs, "Long-Term Leases"))
    ebitda_q = _dated(_row(inc, "For the Fiscal Period Ending", prefix=True), _row(inc, "EBITDA"))

    op_edgar = _complete(facts, *_OPERATING_TAGS)
    op_filed = _complete_first_filed(facts, *_OPERATING_TAGS)
    fin_edgar = _complete(facts, *_FINANCE_TAGS)
    first_op = _first_operating(facts)
    quarters = sorted(ebitda_q)

    # PASS 1 — every priceable quarter's inputs, and which split each checkable one reconciles on
    rows_in: list[tuple[date, float, float, float, float | None]] = []
    for d in sorted(tev):
        t = tev[d]
        if t is None or d not in ebitda_q:
            continue
        k = quarters.index(d)
        window = quarters[k - 3:k + 1] if k >= 3 else []
        if len(window) != 4 or not (_LTM_SPAN_DAYS[0] <= (window[-1] - window[0]).days
                                    <= _LTM_SPAN_DAYS[1]):
            continue
        ltm_parts = [ebitda_q[q] for q in window]
        if any(v is None for v in ltm_parts):
            continue
        rows_in.append((d, t, sum(v for v in ltm_parts if v is not None),
                        (cur_l.get(d) or 0.0) + (lt_l.get(d) or 0.0),
                        _near(op_edgar, d, _OPERATING_NEAR_DAYS)))
    fin_at = {d: (_near(fin_edgar, d, _FINANCE_NEAR_DAYS) or 0.0) if fin_edgar else 0.0
              for d, *_ in rows_in}
    proved = {d: fi for d, _t, _l, rs, oe in rows_in if oe is not None and oe > 0
              and (fi := _reconciles(rs, fin_at[d], oe)) is not None}

    def _comparative(d: date) -> bool:
        near = [k for k in op_filed if abs((k - d).days) <= _OPERATING_NEAR_DAYS]
        k = min(near, key=lambda x: abs((x - d).days)) if near else None
        return k is not None and (op_filed[k] - k).days > _ORIGINAL_FILING_DAYS

    # PASS 2 — each quarter's split, with its context from BOTH sides
    out: list[LeaseObservation] = []
    for d, t, ltm, rows_sum, op_e in rows_in:
        fin = fin_at[d]
        adopted = first_op is not None and d >= first_op - timedelta(days=_OPERATING_NEAR_DAYS)
        nearest = (proved[min(proved, key=lambda p: (abs((p - d).days), p))]
                   if proved else None)
        sp = _split(rows_sum, fin, op_e, adopted=adopted, comparative=_comparative(d),
                    nearest=nearest)
        pd = priced.get(d)
        usable = sp.status != "unreconciled" and ltm > 0
        out.append(LeaseObservation(
            balance_sheet_date=d.isoformat(), pricing_date=pd.isoformat() if pd else None,
            tev=round(t, 3), leases_in_tev=round(rows_sum, 3),
            finance_leases=round(rows_sum - sp.operating, 3),
            operating_leases=round(sp.operating, 3),
            edgar_operating_leases=round(op_e, 3) if op_e is not None else None,
            ltm_ebitda=round(ltm, 3),
            multiple=round((t - sp.operating) / ltm, 6) if usable else None,
            status=sp.status))
    return out


#: EDGAR's own lease-cost tags, in preference order, read beside CIQ's rent as a cross-check.
#: Measured 2026-10-19: CIQ's 'Net Rental Exp.' IS the filer's `LeaseCost` to the dollar on most
#: committed names (TJX 3,814, ROST 1,104.7, CNXC 444, NFLX 711.0, SMPL 13.186) — so VITL's $288M
#: beside its own $293.0M is the company's disclosed total lease cost, not a vendor defect.
_LEASE_COST_TAGS = ("LeaseCost", "OperatingLeaseCost")
#: Beyond this factor either way the two rent figures are named as disagreeing on the page.
_RENT_DISAGREE = 1.5


def edgar_lease_cost(facts: dict[str, Any] | None, fy: date | None) -> tuple[float, str] | None:
    """($M, tag) — EDGAR's annual lease cost for the fiscal year ending within a week of ``fy``,
    under the first tag in :data:`_LEASE_COST_TAGS` that reports it; None when none does."""
    if facts is None or fy is None:
        return None
    for tag in _LEASE_COST_TAGS:
        best: tuple[date, float] | None = None
        for p in points_for_tag(facts, tag):
            if p.is_annual and abs((p.period_end - fy).days) <= _OPERATING_NEAR_DAYS and (
                    best is None or p.filed >= best[0]):
                best = (p.filed, p.value / 1e6)
        if best is not None:
            return best[1], tag
    return None


def rent_disagrees(rent: float, lease_cost: float) -> bool | None:
    """Whether CIQ's rent and EDGAR's lease cost sit more than `_RENT_DISAGREE` apart either way;
    None when either is not positive (there is no ratio). ONE definition: the page's sentence and
    the data-quality scorecard's CIQ source (`vinci.quality.sources.ciq`) both read it."""
    if rent <= 0 or lease_cost <= 0:
        return None
    return max(rent, lease_cost) / min(rent, lease_cost) > _RENT_DISAGREE


def _cross_check(r: Rent, edgar: tuple[float, str] | None) -> str:
    """The sentence naming EDGAR's lease cost beside CIQ's rent — and saying so when they differ."""
    if edgar is None or r.rent is None:
        return ""
    v, tag = edgar
    far = rent_disagrees(r.rent, v) is True
    return (f"; EDGAR {tag} that year: ${v:,.0f}M"
            + (" — CIQ's rent and EDGAR's lease cost DISAGREE; read both" if far else ""))


def _materiality(r: Rent) -> tuple[bool, str]:
    if r.rent is None or r.ebitda is None or r.fiscal_year is None:
        return True, ("rent could not be measured (no fiscal year where CIQ's annual income "
                      "statement reports both 'Net Rental Exp.' and 'EBITDA') — treated as "
                      "material")
    if r.ebitda <= 0:
        return True, (f"EBITDA is not positive in FY{r.fiscal_year.year} — rent's share cannot "
                      "be measured, treated as material")
    share = r.rent / r.ebitda
    fy = f"FY ending {r.fiscal_year.isoformat()}"
    if share >= MATERIALITY:
        return True, (f"rent {share:.1%} of EBITDA ({fy}: ${r.rent:,.0f}M of ${r.ebitda:,.0f}M) "
                      f"— material (≥{MATERIALITY:.0%}); R1 uses the ex-lease history")
    return False, (f"rent {share:.1%} of EBITDA ({fy}: ${r.rent:,.0f}M of ${r.ebitda:,.0f}M) — "
                   f"immaterial (<{MATERIALITY:.0%}); R1 keeps CIQ's TEV/LTM EBITDA history")


def lease_basis(bundle: CiqBundle, facts: dict[str, Any] | None) -> LeaseBasis | None:
    """The page's lease basis, or None when the quarterly CIQ export is absent (there is then no
    CIQ history for R1 either, so there is nothing to choose between)."""
    wb = bundle.workbook("financials", freq="quarterly")
    if wb is None:
        return None
    r = rent_share(bundle)
    material, why = _materiality(r)
    edgar = edgar_lease_cost(facts, r.fiscal_year)
    why += _cross_check(r, edgar)
    base: dict[str, Any] = {
        "edgar_lease_cost": round(edgar[0], 3) if edgar else None,
        "edgar_lease_cost_tag": edgar[1] if edgar else None,
        "rent_expense": r.rent, "rent_ebitda": r.ebitda,
        "rent_to_ebitda": (round(r.rent / r.ebitda, 6)
                           if r.rent is not None and r.ebitda else None),
        "rent_fiscal_year": r.fiscal_year.isoformat() if r.fiscal_year else None,
        "threshold": MATERIALITY, "material": material, "materiality": why,
        "source_ref": SOURCE_REF,
    }
    if not material:
        return LeaseBasis(**base)
    if facts is None:
        return LeaseBasis(**base, refusal="EDGAR companyfacts unavailable — the operating leases "
                                          "inside CIQ's TEV cannot be separated from its finance "
                                          "leases")
    try:
        obs = observations(bundle, facts)
    except CiqUnavailableError as exc:
        return LeaseBasis(**base, refusal=f"the quarterly export cannot be read for it: {exc}")
    counts = {s: sum(1 for o in obs if o.status == s)
              for s in ("reconciled", "unreconciled", "unchecked", "pre-adoption")}
    tally = {"reconciled_dates": counts["reconciled"],
             "unreconciled_dates": counts["unreconciled"],
             "unchecked_dates": counts["unchecked"], "pre_adoption_dates": counts["pre-adoption"],
             "observations": obs}
    checked = counts["reconciled"] + counts["unreconciled"]
    refusal = None
    if counts["reconciled"] < MIN_RECONCILED:
        refusal = (f"only {counts['reconciled']} quarter(s) reconcile CIQ's lease rows to EDGAR's "
                   f"operating leases (≥{MIN_RECONCILED} needed) — what CIQ's TEV holds as "
                   "operating leases is unverified")
    elif counts["unreconciled"] > MAX_UNRECONCILED_SHARE * checked:
        bad = [o.balance_sheet_date for o in obs if o.status == "unreconciled"]
        refusal = (f"{counts['unreconciled']} of {checked} checkable quarters do not reconcile "
                   f"CIQ's lease rows to EDGAR's operating leases within {RECONCILE_TOL:.0%} "
                   f"(more than {MAX_UNRECONCILED_SHARE:.0%}): {', '.join(bad)}")
    band: OwnHistoryBand | None = None
    if refusal is None:
        sha, mtime = file_provenance(wb.path)
        band, refusal = history(obs, source_file=wb.path.name, source_sha256=sha,
                                source_mtime=mtime)
    return LeaseBasis(**base, **tally, ex_lease_band=band, refusal=refusal)


def history(obs: list[LeaseObservation], *, source_file: str | None = None,
            source_sha256: str | None = None, source_mtime: str | None = None,
            ) -> tuple[OwnHistoryBand | None, str | None]:
    """(band, None) or (None, why) — the ex-lease band over these quarters.

    EVERY QUARTER GOES IN, unpriced ones included: `_own_history_band` applies the latest-cell
    rule itself, so an unpriced LATEST quarter refuses the band instead of an older quarter standing
    in as its "current" (item 20 — no backward-fill on any time series; review of #750)."""
    pairs: list[tuple[Any, float | None]] = [
        (date.fromisoformat(o.pricing_date or o.balance_sheet_date), o.multiple) for o in obs]
    last = obs[-1] if obs else None
    if last is not None and last.multiple is None:
        why_not = ("does not reconcile" if last.status == "unreconciled"
                   else "has no positive LTM EBITDA")
        return None, (f"the latest quarter ({last.balance_sheet_date}) {why_not}, so the history "
                      "has no current — an older quarter is not one")
    band = _own_history_band(METRIC, pairs, source_file=source_file,
                             source_sha256=source_sha256, source_mtime=source_mtime)
    if band is None or band.n_closes < _MIN_CONFIDENT_CLOSES:
        n = band.n_closes if band is not None else sum(1 for _d, v in pairs if v is not None)
        return None, f"only {n} ex-lease quarter(s) of history (≥{_MIN_CONFIDENT_CLOSES} needed)"
    return band, None
