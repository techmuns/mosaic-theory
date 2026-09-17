"""The MECHANICAL layer — deterministic, no LLM, every field a source-bound ``{value, source_ref}``.

Facts come from the screen's data-record (already EDGAR/EOD-bound), fresh EDGAR pulls (the 8-K
behind each gap-down; the share-count trend), EOD bars (the name's and IWM's window returns), the
graph (the exposed cross-section, a research INPUT — never a predictor), and the manual CIQ bundle.
Anything not found is UNKNOWN (looked for, absent) or MISSING (whole source absent, e.g. CIQ
un-pulled) — never
a fabricated number. This layer is the ONLY input the synthesis LLM is later given.
"""

from __future__ import annotations

import math
import re
import statistics
import time
import unicodedata
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from datetime import date, timedelta
from typing import Any, NamedTuple, TypeVar

from vinci.config import get_config
from vinci.dossier import ciq_sheets, edgar_fundamentals
from vinci.dossier.capital_allocation import (
    build_capital_allocation,
    build_peer_capital_intensity,
)
from vinci.dossier.ciq import CiqBundle

# Re-exported: the panel-stamp parser lives in `ciq_sheets`, the layer that produces the stamp.
# See the note at `_ITEM_TERMINATION` for why it moved.
from vinci.dossier.ciq_sheets import _cs_panel_filed
from vinci.dossier.ebitda_basis import read_basis as read_ebitda_basis
from vinci.dossier.freshness import _COVERAGE_GAP_DAYS
from vinci.dossier.midcycle import MIN_YEARS as _MIDCYCLE_MIN_YEARS
from vinci.dossier.schemas import (
    CapitalInstrument,
    CapitalStructure,
    CatalystCalendar,
    CatalystPath,
    CatalystRow,
    CohortMember,
    Concentration,
    ConsensusContext,
    ConsensusLevel,
    CovenantPointer,
    DilutionPipeline,
    DrawdownCause,
    FilingRef,
    FilingSectionExtract,
    FinancialSummary,
    IdiosyncraticVsShared,
    ImpliedExpectationRow,
    ImpliedExpectations,
    ImpliedValuation,
    LeverageSurvival,
    MechanicalLayer,
    OperatingDriver,
    OperatingDriversExtract,
    OwnershipEvents,
    OwnershipFiling,
    PeerComps,
    PerfPoint,
    PrimarySource,
    Quality,
    ReconciliationValue,
    RegistrationFiling,
    ReleaseExtract,
    SbcLine,
    Sourced,
    SourceStatus,
    StockInfo,
    StockPerformance,
    Valuation,
)
from vinci.edgar import filing_sections, primary_source, release_parse
from vinci.edgar.client import EdgarClient, Filing
from vinci.edgar.concepts import (
    CONCEPT_ALIASES,
    ConceptPoint,
    extract_points,
    latest_instant,
    points_for_tag,
)
from vinci.edgar.release_parse import GUIDANCE_REFUSAL_PREFIX
from vinci.edgar.submissions import FormerName
from vinci.eod import compute_price_features
from vinci.finra import FinraLayoutError, short_interest_points
from vinci.graph.exposure import ExposureGraph
from vinci.graph.filings import html_to_text, normalize_text
from vinci.monitor import benchmark_for_cap
from vinci.netcache import CachedHttp, HttpError
from vinci.resolver import EntityResolver, ResolutionError
from vinci.resolver.index import pad_cik
from vinci.schemas.data_record import DataRecord, Identity
from vinci.schemas.envelope import CoverageStatus, DataField, SourceTier
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import (
    DECLINE_WINDOW_DAYS,
    GAP_DOWN_THRESHOLD,
    pe_current_and_percentile,
    share_basis_change,
)
from vinci.store import Store
from vinci.universe import benchmark_identity

_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
_DECLINE_WINDOW_DAYS = 180  # the G2 decline window — keep the cohort comparison on the same window

#: The trailing-multiple blind-flag, carried ON the value so the synthesis cannot read a low
#: trailing multiple as evidence of anything by itself.
#:
#: BOOK-NEUTRAL, and it did not start that way. It read "cannot distinguish cheap-overshoot from
#: cheap-terminal" — one strategy's vocabulary on a caveat every book receives. It reached the
#: LLM and came back out in UBER's committed QUALITY read ("a trailing multiple that cannot
#: disambiguate overshoot from terminal re-rate"), so a name judged on whether its runway is
#: underpriced had its machine read phrased in the language of a de-rating hunt. The dichotomy the
#: caveat draws is real and general — temporary versus permanent — and only the words were
#: overshoot's.
#:
#: ONE DEFINITION. `cli.py`'s CIQ-ingest path carried a byte-copy of this string with a comment
#: saying it mirrored this one, which is the dual-write that let the wording sit unexamined in two
#: places at once. Both now read from here.
TRAILING_ONLY_NOTE = (
    "trailing only — no forward basis; cannot distinguish a temporarily depressed level from a "
    "permanently impaired one"
)


def _sourced(field: DataField[float] | DataField[int], *, source_ref: str) -> Sourced[float]:
    """Lift a screen data-record :class:`DataField` into a source-bound dossier fact."""
    if field.is_known and field.value is not None:
        return Sourced.present(float(field.value), source_ref=source_ref, note=field.note)
    return Sourced.unknown(note=field.note or "UNKNOWN in the screen data-record")


_S = TypeVar("_S")


def _prefer_ciq(ciq: Sourced[_S], edgar: Sourced[_S] | None) -> Sourced[_S]:
    """CIQ stays PRIMARY: keep the CIQ field whenever it is PRESENT; otherwise fall to the EDGAR
    fallback (itself PRESENT or fail-loud UNKNOWN). Never overrides a populated CIQ field."""
    if ciq.status is SourceStatus.PRESENT or edgar is None:
        return ciq
    return edgar


def _companyfacts_or_none(edgar: EdgarClient, cik: str | None) -> dict[str, Any] | None:
    """EDGAR companyfacts for the fallback, or None (no CIK / fetch failed) — never raises into the
    assembler; a None just leaves the CIQ field UNKNOWN (no fabrication)."""
    if not cik:
        return None
    try:
        return edgar.companyfacts(cik)
    except (HttpError, KeyError, ValueError):  # ValueError: pad_cik int() on a non-numeric CIK
        return None


def _at_latest_close(record: DataRecord, store: Store, edgar: EdgarClient) -> DataRecord:
    """The record's CURRENT-PRICE readings re-derived at the LATEST STORED CLOSE — the close the
    page's own price box shows — with everything else left as the screen recorded it.

    WHAT MOVES: ``prices.last`` and the trailing EDGAR P/E pair (``fundamentals.pe``,
    ``pe_pctile_vs_history``). Every dossier reader of those asks about NOW: the P/E field, the
    EDGAR-vs-CIQ conflict caveat, the P/E reconciliation's forward multiple "at the current price",
    and the adjusted P/E and forward EV "at current $price". The screen record answered all of them
    at its reference date. PARR, 2026-09-17: the page's price read $84.90 (2026-09-16) while its
    EDGAR P/E divided $74.33 (2026-08-24) — 10.4x instead of 11.9x — and the conflict caveat set
    that three-week-old multiple against CIQ's current one.

    WHAT DOES NOT: the drawdown and return features, and the stored screen record itself (the G3
    gate input). Those describe the screen's own as-of on purpose; only this in-memory copy moves.

    ONE FUNCTION FOR BOTH: the P/E pair comes from `pe_current_and_percentile`, the screen's own
    derivation, so the dossier's P/E and the screen's can differ only by the close they divide.

    FAIL-HONEST: no stored bars, or EDGAR facts that cannot be read, leave the reading UNKNOWN with
    its reason — never the screen's older-price figure carried forward as current."""
    bars = store.get_price_history(record.identity.internal_id)
    f = record.fundamentals
    if not bars:
        none: DataField[float] = DataField.unknown(
            source="EOD", tier=SourceTier.EOD,
            note="no stored price bars at assembly — no current close to price a reading on")
        return record.model_copy(update={
            "prices": record.prices.model_copy(update={"last": none}),
            "fundamentals": f.model_copy(update={"pe": none, "pe_pctile_vs_history": none})})
    bar = max(bars, key=lambda b: b.bar_date)
    last: DataField[float] = DataField.present(
        bar.close, as_of=bar.bar_date, source="EOD", tier=SourceTier.EOD)
    facts = _companyfacts_or_none(edgar, record.identity.cik)
    if facts is None:
        pe: DataField[float] = DataField.unknown(
            source="EDGAR", tier=SourceTier.DERIVED,
            note=f"EDGAR companyfacts unreadable at assembly — no P/E at the "
                 f"{bar.bar_date.isoformat()} close")
        pct = pe
    else:
        annual_eps = [p for p in extract_points(facts, "eps_diluted") if p.is_annual]
        pe, pct = pe_current_and_percentile(bars, annual_eps, reference_date=bar.bar_date)
    return record.model_copy(update={
        "prices": record.prices.model_copy(update={"last": last}),
        "fundamentals": f.model_copy(update={"pe": pe, "pe_pctile_vs_history": pct})})


def _close_on_or_before(bars: list[PriceBar], ref: date) -> float | None:
    elig = [b for b in bars if b.bar_date <= ref]
    return max(elig, key=lambda b: b.bar_date).close if elig else None


def _window_return(bars: list[PriceBar], ref: date, days: int) -> float | None:
    then = _close_on_or_before(bars, ref - timedelta(days=days))
    now = _close_on_or_before(bars, ref)
    return (now / then - 1.0) if (then and now and then > 0) else None


# --- drawdown cause: label by 8-K item codes + parse the catalyst from the filing TEXT --------

# 8-K item codes → standard titles (cause is read from the codes, never blanket "earnings").
_ITEM_TITLES: dict[str, str] = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "2.02": "Results of Operations and Financial Condition",
    "2.05": "Costs Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Failure to Satisfy a Listing Rule",
    "4.02": "Non-Reliance on Previously Issued Financial Statements",
    "5.02": "Departure/Election of Directors or Certain Officers",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}
# short per-code cause label for the per-gap summary (9.01 exhibits carry no event, omitted).
_CAUSE_BY_ITEM: dict[str, str] = {
    "1.01": "material agreement (1.01)", "1.02": "agreement termination (1.02)",
    "2.02": "earnings (2.02)", "2.05": "restructuring (2.05)", "2.06": "impairment (2.06)",
    "3.01": "delisting notice (3.01)", "4.02": "restatement (4.02)",
    "5.02": "management change (5.02)", "7.01": "Reg-FD (7.01)", "8.01": "other event (8.01)",
}


def item_labels(items: list[str]) -> list[str]:
    """Map 8-K item codes to "code title" so the cause is read from the codes, not guessed."""
    return [f"{c} {_ITEM_TITLES.get(c, 'Item ' + c)}" for c in items]


# The 8-K items that can actually MOVE a price (= the keys of _CAUSE_BY_ITEM). An 8-K carrying only
# items OUTSIDE this set is administrative — a routine annual-meeting vote (5.07), bylaw amendment
# (5.03), etc. — and does not explain a gap-down. 5.02 (management change) stays IN: a CEO departure
# genuinely moves a stock.
_EXPLANATORY_ITEMS = frozenset(_CAUSE_BY_ITEM)


def _is_explanatory(items: list[str]) -> bool:
    """Does this 8-K carry any item that could plausibly cause a gap-down?"""
    return bool(set(items) & _EXPLANATORY_ITEMS)


def _admin_label(items: list[str]) -> str:
    """Plain-English label for an administrative-only 8-K — no list repr, no house jargon."""
    if "5.07" in items:
        return "no earnings/guidance filing (annual-meeting 8-K only)"
    codes = ", ".join(c for c in items if c not in _EXPLANATORY_ITEMS) or "—"
    return f"no earnings/guidance filing (administrative 8-K only · items {codes})"


# (8.01 refinement) ANCHORED patterns on the parsed 8.01 body — a bare "other event" hides the one
# cause class 8.01 routinely carries: a securities offering. Deterministic two-step: an OFFERING
# CONTEXT anchor must fire first, then the instrument decides the label (notes → debt, stock →
# equity, neither → the honest generic). No context anchor → the label stays "other event".
_OFFERING_CTX = re.compile(r"underwriting agreement|public offering|to issue and sell", re.I)
_OFFERING_DEBT = re.compile(r"\bnotes?\b|debentures|principal amount", re.I)
_OFFERING_EQUITY = re.compile(r"common stock|ordinary shares|\bshares\b", re.I)


def _refine_801(label: str, events: list[str] | None) -> str:
    """Refine the 8.01 "other event" label from the filing's own parsed body — never a guess."""
    body = " ".join(e for e in (events or []) if e.startswith("8.01"))
    if not body or not _OFFERING_CTX.search(body):
        return label
    if _OFFERING_DEBT.search(body):
        return "debt offering (8.01)"
    if _OFFERING_EQUITY.search(body):
        return "equity offering (8.01)"
    return "securities offering (8.01)"


def _gap_label(items: list[str], events: list[str] | None = None) -> str:
    """A short cause label for one gap-down from its 8-K items. Never "earnings" without 2.02;
    an administrative-only 8-K (5.07 annual-meeting vote, etc.) is NOT a cause — it reads as no
    earnings/guidance filing, matching the 'no company filing' treatment of a gap with no 8-K.
    An 8.01 refines to its offering class when the parsed body anchors one (_refine_801)."""
    labels = [
        _refine_801(_CAUSE_BY_ITEM[c], events) if c == "8.01" else _CAUSE_BY_ITEM[c]
        for c in items
        if c in _CAUSE_BY_ITEM
    ]
    return " + ".join(labels) if labels else _admin_label(items)


def parse_8k_events(text: str, items: list[str], accession: str) -> list[str]:
    """Source-bound per-item catalyst summaries from the 8-K body — the customer/contract/executive
    action, not just the code. Fail loud (UNKNOWN — read by hand) when a body can't be parsed; never
    fabricate. Pure: the filing's own words in, capped summaries out."""
    out: list[str] = []
    for code in items:
        if code == "9.01":  # exhibits — no narrative event
            continue
        title = _ITEM_TITLES.get(code, f"Item {code}")
        m = re.search(rf"Item\s+{re.escape(code)}\b", text, re.IGNORECASE)
        body = ""
        if m:
            seg = text[m.end() : m.end() + 1400]
            nxt = re.search(r"Item\s+\d\.\d\d\b|\bSIGNATURES?\b", seg, re.IGNORECASE)
            seg = seg[: nxt.start()] if nxt else seg
            body = re.sub(r"\s+", " ", seg).strip(" .:;-—").strip()
        if len(body) >= 40:
            out.append(f"{code} {title}: {body[:400]}")
        else:
            out.append(f"{code} {title}: UNKNOWN narrative — read filing {accession} by hand")
    if not out:
        codes = ", ".join(items) or "—"
        out.append(f"only non-narrative items ({codes}) — read filing {accession} by hand")
    return out


def _drawdown_filings(
    edgar: EdgarClient, http: CachedHttp, cik: str, gap_dates: list[date]
) -> list[FilingRef]:
    if not gap_dates:
        return []
    filings = edgar.recent_filings(cik, forms=("8-K",), since=min(gap_dates) - timedelta(days=7))
    refs: list[FilingRef] = []
    for gd in gap_dates:
        lo, hi = gd - timedelta(days=1), gd + timedelta(days=4)
        near = sorted(
            (f for f in filings if lo <= f.filing_date <= hi), key=lambda f: f.filing_date
        )
        if not near:
            continue
        f = near[0]
        url, events = "", [f"UNKNOWN — no primary document for {f.accession}; read by hand"]
        if f.primary_doc:
            url = _ARCHIVE.format(
                cik=int(pad_cik(f.cik)), acc=f.accession.replace("-", ""), doc=f.primary_doc
            )
            try:
                events = parse_8k_events(
                    html_to_text(http.get_text(url, ttl_seconds=None)), list(f.items), f.accession
                )
            except HttpError:
                events = [f"UNKNOWN — could not fetch filing {f.accession}; read by hand"]
        refs.append(
            FilingRef(
                gap_date=gd.isoformat(), filing_date=f.filing_date.isoformat(), form=f.form,
                items=list(f.items), item_types=item_labels(list(f.items)),
                accession=f.accession, url=url, events=events,
                explanatory=_is_explanatory(list(f.items)),
            )
        )
    return refs


_INDEX = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/index.json"
_GUIDANCE_ANCHOR = re.compile(
    r"(?:revis|updat)\w*[^.]{0,80}?(?:full[- ]year|outlook|guidance)", re.I)
_MONEY = re.compile(r"\$\s?\d")
_METRIC = re.compile(r"\b(revenue|ebitda|eps|free cash flow|earnings per share)\b", re.I)


def _exhibit_991_url(http: CachedHttp, cik: str, accession: str) -> str | None:
    """The furnished Exhibit 99.1 (press release) URL, or None if the filing furnishes none.

    ONE detector, shared with the primary-source fetch: this module used to carry its own copy of
    the filename regex, and the two DRIFTED — the copy here never learned the '_' separator class,
    so it missed 'ex99_1.htm' that the other matched. The rule now lives once, in
    release_parse.exhibit_991_urls (EDGAR's SGML exhibit TYPE, filename match as fallback)."""
    urls = release_parse.exhibit_991_urls(http, cik, accession)
    return urls[0] if urls else None


def _extract_revised_guidance(text: str) -> str | None:
    """The REVISED full-year outlook block (figures verbatim) from a 99.1 press release. Anchored on
    'revis…/updat…(full-year|outlook|guidance)' so it surfaces a *changed* outlook, not an initial
    one ('updat' is load-bearing: SMPL's 2026-04-09 exhibit said 'Updating Fiscal Year 2026
    Outlook' — no 'revis…' verb anywhere — and the revis-only anchor read it as no-outlook while
    the gap-card parser extracted the same figures from the same exhibit).
    Verbatim — the figures are read from the primary source, never parsed into numbers here (no
    mis-extraction). Returns None when no revised-outlook section exists (→ UNKNOWN upstream).

    Among figures-bearing windows, an anchor that INTRODUCES a list (a ':' within 40 chars of the
    anchor) wins over a bare headline: SMPL's top headline ('Updates Fiscal Year 2026 Outlook
    Denver, CO …') passes the money+metric test on the RESULTS lede behind it, while the actual
    outlook bullets sit under the later 'Updating Fiscal Year 2026 Outlook:' heading. The first
    figures-bearing window stays as the fallback when no colon-introduced anchor exists."""
    fallback: str | None = None
    for m in _GUIDANCE_ANCHOR.finditer(text):  # skip the lede; take the anchor whose window has the
        window = " ".join(text[m.start() : m.start() + 800].split())  # the figures window
        if len(_MONEY.findall(window)) >= 2 and _METRIC.search(window):
            if ":" in text[m.start() : m.end() + 40]:
                return window
            if fallback is None:
                fallback = window
    return fallback


def _revised_guidance(http: CachedHttp, cik: str, filings: list[FilingRef]) -> Sourced[str]:
    """Follow the furnished 99.1 exhibit on the drawdown 8-Ks (the body only *points* to it) and
    surface the company's revised full-year guidance — the verdict-relevant number. Source-bound to
    the exhibit; fail loud UNKNOWN naming the accession(s). The UNKNOWN note distinguishes 'a 99.1
    WAS parsed but no revised-outlook block matched' from 'no 99.1 located' — it never claims the
    exhibit wasn't parsed when it was (SMPL: the gap card extracted this very exhibit's figures
    while this note said 'no … exhibit parsed' — an internal contradiction in one dossier)."""
    tried: list[str] = []
    parsed: list[str] = []
    for f in filings:
        if not ({"2.02", "7.01", "8.01"} & set(f.items)):  # press releases live under these items
            continue
        if f.accession in tried:  # two gap-downs can share ONE filing — list it once
            continue
        tried.append(f.accession)
        url = _exhibit_991_url(http, cik, f.accession)
        if url is None:
            continue
        try:
            text = html_to_text(http.get_text(url, ttl_seconds=None))
        except HttpError:
            continue
        parsed.append(f.accession)
        block = _extract_revised_guidance(text)
        if block:
            ref = f"EDGAR 8-K {f.accession} Ex-99.1 — {url}"
            return Sourced.present(block, source_ref=ref)
    if parsed:
        return Sourced.unknown(
            note=f"no revised-outlook block matched in the parsed 99.1 for 8-Ks {parsed}")
    if tried:
        # located/fetched: an accession lands here when no 99.1 URL was found OR the fetch
        # errored — the exhibit may exist unretrieved; never claim more precision than we have.
        # The "for 8-Ks ['…']" tail is the shape _clean_note/cleanNote singularize — keep it.
        return Sourced.unknown(note=f"no 99.1 exhibit located/fetched for 8-Ks {tried}")
    return Sourced.unknown(note="no results/Reg-FD/other-event 8-K at the gap-downs with a 99.1")


def _drawdown_cause(
    record: DataRecord, edgar: EdgarClient, http: CachedHttp
) -> tuple[DrawdownCause, list[str]]:
    """The drawdown block, plus any flags for the human-review channel.

    Returns flags rather than carrying them on `DrawdownCause` deliberately: a `qa_flags` field on
    the model (the shape `CatalystCalendar` and `OperatingDriversExtract` use) would add a key to
    every committed `dossier.json`, and this condition fires only on a degraded feed. A tuple keeps
    the artifact untouched — there is exactly one production caller."""
    gaps = sorted(e.event_date for e in record.events if e.event_type.value == "earnings_gap_down")
    cik = record.identity.cik
    # AN UNREADABLE FILING INDEX IS NOT THE SAME FINDING AS "THE COMPANY FILED NOTHING".
    # This was the one submissions call site of 13 with no handler, and the FIRST to run, so a
    # degraded feed raised out of `assemble_mechanical` and `assemble_cohort`'s per-name `task`
    # dropped the whole name into its `errors` list — the run survived and the name silently did
    # not appear. Returning `[]` here instead would be WORSE than that crash: every gap date would
    # then render "no company filing" below, which is a claim about the WORLD manufactured out of a
    # tooling failure. So the failure is carried as its own state and surfaces as UNKNOWN.
    # `not cik` is a LOOKUP FAILURE too, not an empty result: with no CIK the index was never read,
    # so the "no company filing" finding below was never established. Five siblings guard this the
    # same way (1938, 2083, 2384, 2592, 2933 — `note="no CIK for the filing-index lookup"`).
    lookup_failed = not cik
    why = "no CIK for the filing-index lookup" if not cik else "EDGAR filing index unavailable"
    filings: list[FilingRef] = []
    if cik:
        try:
            filings = _drawdown_filings(edgar, http, cik, gaps)
        # WIDER THAN HttpError, deliberately. `recent_filings` also raises `KeyError` on a
        # submissions doc missing a parallel array, and `ValueError` — which `json.JSONDecodeError`
        # subclasses — when SEC answers 200 with an HTML interstitial or a blank `filingDate`.
        # `assay.py:430` records that malformed shape as OBSERVED, and six siblings on this same
        # call already catch the wider tuple (3078, 3136; rank/structural.py:170). Catching only
        # HttpError left the name silently dropped through a neighbouring door.
        except (HttpError, KeyError, ValueError, IndexError):
            filings, lookup_failed = [], True
    by_gap = {f.gap_date: f for f in filings}
    shape: Sourced[str]
    if gaps and lookup_failed:
        shape = Sourced.unknown(
            note=f"{why} — the gap-down dates are known but their causes could not be read; "
            "read the filings at those dates by hand"
        )
    elif gaps:
        parts = [
            f"{gd.isoformat()} "
            f"{_gap_label(by_gap[gd.isoformat()].items, by_gap[gd.isoformat()].events)}"
            if gd.isoformat() in by_gap
            # state the WORLD, not our process: a hard fall on a day the company filed nothing is
            # itself a finding (it points away from company news), not a tooling miss.
            else f"{gd.isoformat()} no company filing"
            for gd in gaps
        ]
        shape = Sourced.present(
            "discrete gap-downs — " + "; ".join(parts),
            source_ref="EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)",
        )
    else:
        shape = Sourced.present(
            "gradual bleed — no discrete gap-down detected",
            source_ref="EOD gap-down detector (screen events): none",
        )
    dates_field: Sourced[list[str]] = (
        Sourced.present(
            [g.isoformat() for g in gaps], source_ref="EOD gap-down detector (screen events)"
        )
        if gaps
        else Sourced.unknown(note="no gap-down events on the data-record")
    )
    # THE MACHINE-TIER TWIN of the UNKNOWN note above. The human is told at the point of use
    # (`_fact` prints "_UNKNOWN_ — EDGAR filing index unavailable…"); this flag exists so a degraded
    # run is also MEASURABLE — greppable and countable across a batch, which the rendered note is
    # not. `"drawdown-cause:"` is on `flags._QA_MARKERS`, so it stays dev/JSON only (operator
    # ruling 2026-09-02 — an exception to that module's show-by-default rule, argued at the
    # hide-list entry). The exception holds ONLY while the block itself still names the outage;
    # both halves are pinned together in
    # tests/test_drawdown_filing_index_unavailable.py::
    # test_the_outage_flag_is_hidden_because_the_block_itself_already_says_so.
    drawdown_flags: list[str] = []
    if gaps and lookup_failed:
        # DISTINCT dates, not events: `gaps` is not de-duplicated upstream, and this count is the
        # only number the machine tier reports about the outage.
        n_dates = len({g.isoformat() for g in gaps})
        fix = "re-assemble when the feed recovers" if cik else "resolve the CIK, then re-assemble"
        drawdown_flags.append(
            f"drawdown-cause: {why} — {n_dates} gap-down date(s) carry no attributed cause; {fix}"
        )
    cause = DrawdownCause(
        shape=shape,
        gap_down_dates=dates_field,
        filings=filings,
        revised_guidance=(
            _revised_guidance(http, cik, filings)
            if cik and filings
            # the same distinction as `shape`: "we could not look" must not read as "there was
            # nothing to find", or a degraded run reports an absence it never established.
            else Sourced.unknown(
                note=f"{why} — no catalyst 8-K could be identified"
                if lookup_failed
                else "no catalyst 8-K to follow for a revised-guidance exhibit"
            )
        ),
        # the detector's own params, copied from the screen constants (ONE source of truth) so the
        # renderers can mark coverage honestly (window boundary + pre-window drops).
        gap_threshold=GAP_DOWN_THRESHOLD,
        gap_window_days=DECLINE_WINDOW_DAYS,
    )
    return cause, drawdown_flags


# --- (B1) informative drawdown: join each gap-down's 8-K to its parsed EX-99.1 drivers -----------
_DRIVER_METRICS = ("adjusted ebitda", "adjusted operating income", "adjusted net income",
                   "adjusted eps")
_METRIC_SHORT = {
    "adjusted ebitda": "adj EBITDA",
    "adjusted operating income": "adj operating income",  # pre interest/tax — never "net income"
    "adjusted net income": "adj net income",
    "adjusted eps": "adj EPS",
}


def _acc_of(source_ref: str) -> str | None:
    """The EDGAR accession embedded in a release source_ref ('8-K 0001628280-26-033601 EX-99.1')."""
    m = re.search(r"(\d{10}-\d{2}-\d{6})", source_ref)
    return m.group(1) if m else None


def _period_key(period: str) -> tuple[int, int]:
    """Sort key for a period: (year, quarter) — 'Q1 2026' → (2026, 1), '2025' → (2025, 0)."""
    ym = re.search(r"(\d{4})", period)
    qm = re.search(r"Q(\d)", period)
    return (int(ym.group(1)) if ym else 0, int(qm.group(1)) if qm else 0)


def _fmt_driver(metric: str, value: float) -> str:
    """$M for EBITDA/NI, $/sh for EPS; sign-aware ('-$5.5M', '$44.7M', '-$0.04')."""
    if "eps" in metric:
        return f"-${abs(value):.2f}" if value < 0 else f"${value:.2f}"
    return f"-${abs(value):,.1f}M" if value < 0 else f"${value:,.1f}M"


def guidance_refusal_flags(releases: Sequence[ReleaseExtract]) -> list[str]:
    """(item 22) Lift GUIDANCE REFUSALS off the releases so they reach the READER.

    ``qa_flags`` is the machine tier by design (``render.py``: "dev/JSON only"), and a release's
    own flags roll up nowhere — so a refused guidance sentence was invisible on every surface, the
    absent-and-silent shape the visible-absence rule prohibits. ``flags.partition`` routes anything
    off the QA hide-list to the human caveat channel, which is where "your guidance picture is
    incomplete, and here is the sentence" belongs.

    ONLY the refusals. The sibling ``no anchored pattern matched`` flags say a release stated no
    guidance at all — ordinary across the fleet, and promoting those would drown the channel and
    make the real refusals harder to see, not easier.

    A named function rather than an inline comprehension so the routing has a behavioural pin:
    inlined, the only available test was a source-text assertion."""
    return [f for r in releases for f in r.qa_flags
            if f.startswith(GUIDANCE_REFUSAL_PREFIX)]


def _fmt_guide_range(low: float | None, high: float | None, unit: str) -> str:
    """A guidance range, formatted from its OWN unit and at a precision that keeps the range a
    range. TWO defects, one root, and fixing either alone still prints a wrong number.

    UNIT. The old formatter had one branch for "%" and assumed "$M" for everything else, so VRRM's
    adjusted-EPS guide of $1.19–$1.25 **per share** printed as "$1.2–$1.2M" — wrong by 1e6. The
    unit was unexpressible upstream (``GuidanceItem.unit`` had no ``$/sh``), which is why the
    default was never questioned: every new metric inherits it.

    PRECISION. ``.1f`` collapsed 1.19–1.25 to "$1.2–$1.2" — a ZERO-WIDTH range, which reads as a
    point estimate the company never gave. Decimals are widened until the two bounds are actually
    distinguishable, so the printed range is the recorded one.
    """
    if low is None or high is None:
        return "stated, no number given"

    def pair(dp: int) -> tuple[str, str]:
        return f"{low:,.{dp}f}", f"{high:,.{dp}f}"

    base = {"$M": 1, "$/sh": 2, "%": 1}.get(unit, 1)
    dp = base
    while dp < 4 and low != high and pair(dp)[0] == pair(dp)[1]:
        dp += 1
    lo, hi = pair(dp)
    if unit == "%":
        return f"{lo}–{hi}% growth"
    if unit == "$/sh":
        return f"${lo}–${hi}/sh"
    return f"${lo}–${hi}M"


def _compose_gap_drivers(release: ReleaseExtract) -> Sourced[str] | None:
    """WHAT the results showed — the latest-period adjusted EBITDA / net income / EPS (with the
    prior-period contrast), one-off charges, and the forward outlook — from an already-parsed
    EX-99.1, source-bound to the exhibit. None when the exhibit parsed no drivers. Deterministic
    formatting of STORED values (no new number, no conclusion)."""
    parts: list[str] = []
    by_metric: dict[str, list[ReconciliationValue]] = {}
    for rc in release.reconciliation:
        by_metric.setdefault(rc.metric, []).append(rc)
    for metric in _DRIVER_METRICS:
        items = sorted(by_metric.get(metric, []), key=lambda x: _period_key(x.period), reverse=True)
        if not items:
            continue
        latest = items[0]
        s = f"{_METRIC_SHORT[metric]} {latest.period} {_fmt_driver(metric, latest.value)}"
        # the DIRECTION the release stated beside the level — a gap-down is about the delta
        if latest.change:
            s += f" ({latest.change})"
        # the prior contrast must match the period TYPE (annual vs quarterly) — an FY result pairs
        # with the prior FY, a quarter with the prior-year quarter, never FY vs Q4.
        latest_q = "Q" in latest.period.upper()
        prior = next(
            (i for i in items[1:]
             if i.period != latest.period and ("Q" in i.period.upper()) == latest_q),
            None,
        )
        if prior is not None:
            s += f" (vs {_fmt_driver(metric, prior.value)} {prior.period})"
        parts.append(s)
    for o in release.one_offs:
        # Trim at a CLAUSE boundary, not a character count: the old 48-char cut left dangling
        # connectives ("…charge associated with a", "…expenses in the"), which read as a
        # truncation artefact rather than a fact. Prefer the shortest complete noun phrase.
        desc = re.split(r"\s+(?:associated|related\s+to|in\s+the|for\s+the|due\s+to|which)\b",
                        o.description, maxsplit=1)[0].strip(" ,;")
        parts.append(f"${o.amount:,.1f}M {desc}")
    for g in release.guidance:
        if g.qualitative:
            outlook = "stated, no number given"  # honest: the company spoke, without a figure
        else:
            outlook = _fmt_guide_range(g.low, g.high, getattr(g, "unit", "$M"))
        parts.append(f"{g.period} {g.metric} outlook: {outlook}")
    if not parts:
        return None
    # DEDUP, order-preserving: a release that states the same one-off twice (IT's $150.0M Digital
    # impairment appeared in both the headline and the detail paragraph) must not read as a stutter
    # — identical segments carry no second fact.
    parts = list(dict.fromkeys(parts))
    return Sourced.present("; ".join(parts), source_ref=release.source_ref)


def _enrich_drawdown_drivers(mech: MechanicalLayer, primary: PrimarySource) -> MechanicalLayer:
    """(B1) Join each gap-down's 8-K accession to its parsed EX-99.1 release, attaching the driver
    summary to the FilingRef — the informative cause that replaces item-code boilerplate. Assemble/
    inform: it re-presents already-parsed facts, source-bound; renders no new conclusion."""
    dc = mech.drawdown_cause
    if not dc.filings:
        return mech
    rel_by_acc: dict[str, ReleaseExtract] = {}
    for r in primary.releases:
        acc = _acc_of(r.source_ref)
        if acc is not None:
            rel_by_acc[acc] = r
    new_filings = [
        f.model_copy(update={"drivers": _compose_gap_drivers(rel_by_acc[f.accession])})
        if f.accession in rel_by_acc else f
        for f in dc.filings
    ]
    if new_filings == list(dc.filings):
        return mech
    new_dc = dc.model_copy(update={"filings": new_filings})
    return mech.model_copy(update={"drawdown_cause": new_dc})


# --- idiosyncratic vs shared (graph cohort + EOD window returns) -------------------------------


def _cohort(
    graph: ExposureGraph, resolver: EntityResolver, store: Store, ticker: str, ref: date
) -> Sourced[list[CohortMember]]:
    node = graph.resolve(ticker, resolver)
    if node is None:
        return Sourced.unknown(
            note=f"{ticker} not in graph_coverage.json — no exposed cross-section to compare"
        )
    members: list[CohortMember] = []
    for x in graph.exposed_within(node, hops=2):
        if not x.ticker:
            continue
        try:
            bars = store.get_price_history(resolver.resolve_ticker(x.ticker).internal_id)
        except (ResolutionError, LookupError):
            bars = []
        members.append(
            CohortMember(
                ticker=x.ticker, hops=x.hops,
                ret_180d=_window_return(bars, ref, _DECLINE_WINDOW_DAYS) if bars else None,
                via=(" · ".join(x.path))[:200],
            )
        )
    if not members:
        return Sourced.unknown(note=f"{ticker} in graph but no US-listed exposed names to price")
    return Sourced.present(
        members, source_ref=f"graph_coverage.json node={node}; EOD {_DECLINE_WINDOW_DAYS}d ret"
    )


def _idio_read(name_180d: Sourced[float], cohort: Sourced[list[CohortMember]]) -> Sourced[str]:
    if cohort.status.value != "present" or not cohort.value or name_180d.value is None:
        return Sourced.unknown(
            note="no graph cohort to compare — see rel_vs_market for the name-vs-market read"
        )
    rets = [m.ret_180d for m in cohort.value if m.ret_180d is not None]
    if not rets:
        return Sourced.unknown(note="cohort names have no price history over the window")
    med = statistics.median(rets)
    gap = name_180d.value - med
    # MOVED, not "fell" — the verb is book-neutral because this layer is. The quality book's own
    # rendered heading already asks whether the price "moved alone", so "fell" contradicted the
    # heading above it on any name not being judged for a decline; the signed percentages beside
    # it carry the direction anyway. Latent when changed: no committed dossier reached this branch.
    if gap <= -0.15:
        read = f"moved ALONE (idiosyncratic): name {name_180d.value:.0%} vs cohort median {med:.0%}"
    elif med <= -0.20:
        read = (f"moved WITH cohort (shared/thematic): name {name_180d.value:.0%} "
                f"vs median {med:.0%}")
    else:
        read = f"mixed: name {name_180d.value:.0%} vs cohort median {med:.0%} (cohort steady)"
    return Sourced.present(read, source_ref=f"derived from {len(rets)} cohort names; face-validity")


def _resolve_benchmark(
    market_cap_musd: Sourced[float], ref: date, *, screen_cap_usd: float | None = None
) -> tuple[Identity, str]:
    """The dossier surface's benchmark = the SAME cap-band policy the monitor freezes at entry
    (``vinci.monitor.benchmark_for_cap``), applied to the CIQ cap ($M) at the reference date.
    One policy, two instants — the monitor's assignment stays frozen for scoring; this one gives
    the analytical context (exhibit + 180d relative) the right yardstick.

    Cap fallback order: CIQ cap → the SCREEN-TIME EOD×XBRL cap the ranker already froze at entry
    (``screen_cap_usd``, threaded from the ranked-queue row) → the small-cap IWM default. The
    ranker fallback exists because the CIQ cap is environment-sensitive (absent when re-assembling
    in an incomplete store), which silently flipped a mid-cap's benchmark to IWM (the IT MDY→IWM
    drift); the ranker's screen-time cap is present regardless and can't reselect on re-assembly.
    Every branch states its basis loudly — never a silent guess."""
    cap_m = market_cap_musd.value if market_cap_musd.status is SourceStatus.PRESENT else None
    if cap_m is not None and cap_m > 0:
        cap_usd = cap_m * 1e6  # CIQ panel is $M; the policy takes USD
        sym, band = benchmark_for_cap(cap_usd)
        basis = f"cap-band: ${cap_usd / 1e9:.1f}B @ {ref} → {band} → {sym}"
    elif screen_cap_usd is not None and screen_cap_usd > 0:
        sym, band = benchmark_for_cap(screen_cap_usd)
        basis = f"cap-band: ${screen_cap_usd / 1e9:.1f}B (screen-time, ranker) → {band} → {sym}"
    else:
        sym, basis = "IWM", "cap-band: cap UNKNOWN → small-cap default IWM"
    return benchmark_identity(sym), basis


def _idiosyncratic_vs_shared(
    record: DataRecord, store: Store, graph: ExposureGraph, resolver: EntityResolver, ref: date,
    *, bench: Identity, bench_basis: str,
) -> IdiosyncraticVsShared:
    sym = record.identity.eod_symbol
    bsym = bench.eod_symbol
    bars = store.get_price_history(record.identity.internal_id)
    name_ret = _window_return(bars, ref, _DECLINE_WINDOW_DAYS) if bars else None
    name_180d = (
        Sourced.present(
            name_ret, source_ref=f"EOD {sym} {_DECLINE_WINDOW_DAYS}d to {ref}"
        )
        if name_ret is not None
        else Sourced.unknown(note="name has no bars over the window")
    )
    bench_bars = store.get_price_history(bench.internal_id)
    mkt_ret = _window_return(bench_bars, ref, _DECLINE_WINDOW_DAYS) if bench_bars else None
    market_180d = (
        Sourced.present(
            mkt_ret, source_ref=f"EOD {bsym} {_DECLINE_WINDOW_DAYS}d to {ref} ({bench_basis})"
        )
        if mkt_ret is not None
        else Sourced.unknown(note=f"{bsym} benchmark bars unavailable — run `vinci refresh {bsym}`")
    )
    # rel is RECOMPUTED here on the same yardstick as market_180d. The screen record's G2 rel
    # (name−IWM, the universe-wide gate) stays in the record — mixing the two would put a
    # small-cap denominator under a mid/large-cap read.
    rel = (
        Sourced.present(
            name_ret - mkt_ret,
            source_ref=f"EOD {sym}−{bsym} {_DECLINE_WINDOW_DAYS}d to {ref} (assembly, cap-band)",
        )
        if (name_ret is not None and mkt_ret is not None)
        else Sourced.unknown(
            note=f"name−{bsym} needs both legs; "
                 f"missing {'name' if name_ret is None else bsym} bars"
        )
    )
    cohort = _cohort(graph, resolver, store, record.identity.ticker, ref)
    return IdiosyncraticVsShared(
        name_180d_return=name_180d, market_180d_return=market_180d, rel_vs_market=rel,
        cohort=cohort, read=_idio_read(name_180d, cohort),
        benchmark_symbol=bsym, benchmark_basis=bench_basis,
    )


_PERF_WINDOW_DAYS = 364  # 52 weeks — the Brief stock-performance exhibit window
# DAILY resolution (a 52-wk window holds ~251 trading days; the cap only guards a pathological
# store). Weekly-ish downsampling (the old cap of 60) SMOOTHED AWAY the very one-day gap-downs the
# What-broke chart marks (CNXC's -11.2% Jun-30 drop was invisible), and made the true 1-day gap %
# unrecoverable from the committed series (a weekly proxy misstated -12.7% as -21.7%). Daily points
# let the renderers derive each gap's exact close-to-close move — the detector's own formula on the
# same closes — instead of fabricating from a downsample. Cost: ~12KB/name of committed JSON.
_PERF_MAX_POINTS = 400


def _stock_performance(
    identity: Identity, store: Store, ref: date, *, bench: Identity
) -> StockPerformance | None:
    """52-week rebased price path — the name vs its cap-band benchmark, both indexed to 100 at the
    window start. Reads the SAME EOD closes the idio comparison uses (assemble/visualize, never
    conclude). Returns None (exhibit absent) when the name has <2 window bars — fail-loud, never a
    fabricated series. The benchmark is aligned to the name's trading days via as-of closes; a
    point's ``benchmark`` is None only when the index has no bar on/before that day (the name path
    still renders)."""
    sym = identity.eod_symbol
    lo = ref - timedelta(days=_PERF_WINDOW_DAYS)
    name_win = [b for b in store.get_price_history(identity.internal_id) if lo <= b.bar_date <= ref]
    if len(name_win) < 2:
        return None
    base_name = name_win[0].close
    if base_name <= 0:
        return None
    bench_bars = store.get_price_history(bench.internal_id)
    base_bench = _close_on_or_before(bench_bars, name_win[0].bar_date)

    def _rebased_bench(d: date) -> float | None:
        c = _close_on_or_before(bench_bars, d)
        return round(c / base_bench * 100.0, 2) if (c and base_bench) else None

    step = max(1, len(name_win) // _PERF_MAX_POINTS)
    idxs = list(range(0, len(name_win), step))
    if idxs[-1] != len(name_win) - 1:
        idxs.append(len(name_win) - 1)  # always pin the current (right-edge) point
    points = [
        PerfPoint(
            date=name_win[i].bar_date.isoformat(),
            name=round(name_win[i].close / base_name * 100.0, 2),
            benchmark=_rebased_bench(name_win[i].bar_date),
        )
        for i in idxs
    ]
    last_bench = _close_on_or_before(bench_bars, name_win[-1].bar_date)
    return StockPerformance(
        points=points,
        name_symbol=sym,
        benchmark_symbol=bench.eod_symbol,
        as_of=name_win[-1].bar_date,
        window_days=_PERF_WINDOW_DAYS,
        name_return=name_win[-1].close / base_name - 1.0,
        benchmark_return=(last_bench / base_bench - 1.0) if (last_bench and base_bench) else None,
        source_ref=(
            f"EOD {sym} vs {bench.eod_symbol} rebased to 100, "
            f"{name_win[0].bar_date}..{name_win[-1].bar_date}"
        ),
    )


# --- non-operating earnings share (EDGAR XBRL) ------------------------------------------------

#: A quarter is flagged only when BOTH arms pass, and each exists because the other is blind.
#:
#: SHARE OF PRE-TAX says the item is decision-relevant — a fifth or more of the pre-tax result
#: arriving from below the operating line is enough to make GAAP EPS the wrong operating anchor,
#: which is the reader's actual question. Alone it is unusable: its denominator passes through
#: zero, and on the live corpus that yields MVST at 1,833% and AORT at 1,607% on items of $14M
#: and $5M.
#:
#: SHARE OF REVENUE is the stabiliser — revenue does not cross zero, so it says the item is large
#: in the business's own terms rather than merely large against a thin quarter.
#:
#: MEASURED ON 13 NAMES x 4 QUARTERS of live companyfacts (2026-08-12). At 20%/5%: NFLX flags on
#: 2026-03-31 ALONE (40% of pre-tax, 21% of revenue — the $2.59bn WBD termination fee) and is quiet
#: on its other three quarters at 3-4%; UBER flags on the three quarters that are genuinely
#: non-operating-heavy and is quiet at 4% in 2025-06; MVST flags a -$122M charge against $91M of
#: revenue, a true positive rather than noise.
#:
#: AN OUTLIER TEST WAS TRIED FIRST AND REJECTED ON THE MEASUREMENT. Scoring each quarter against
#: the company's OWN trailing median catches NFLX cleanly (19x) and MISSES UBER (2.6x) — because
#: UBER revalues its portfolio every quarter, so a large non-operating swing IS its norm and its
#: median rises to meet it. The reader's question is not "is this unusual for them" but "how much
#: of this quarter's earnings is operating", which is true whether or not the company does it
#: habitually. Flagging novelty would have exempted the name that does it every quarter.
_NONOP_PRETAX_SHARE = 0.20
_NONOP_REVENUE_SHARE = 0.05


def _quarterly_map(facts: dict[str, Any], concept: str) -> dict[date, float]:
    """``{period_end: value}`` for ~quarterly points, merged ACROSS the concept's aliases.

    DELIBERATELY NOT :func:`extract_points`, which is first-alias-WITH-DATA-wins. That rule is
    right when reading one number by meaning and wrong when asking which PERIODS a concept covers,
    because an abandoned tag still has data — just old data. UBER stopped reporting
    `RevenueFromContractWithCustomerExcludingAssessedTax` after **2019-06-30** and has filed under
    `Revenues` ever since, so the preferred alias hands back a seven-year-stale quarter and this
    whole field silently resolved to 2019 (measured, not hypothesised — it is what the first cut
    did). Alias PRECEDENCE is preserved within a period, via `setdefault`: the first alias to
    supply a period keeps it, and only period COVERAGE is unioned.

    Duration-bounded at 80-100 days rather than trusting ``fp``: EDGAR stamps quarterly points
    inside a 10-K with ``fp="FY"``, the trapdoor `ConceptPoint.is_annual` documents at length. A
    10-Q's own quarter and a 10-K's embedded Q4 both land correctly because DURATION is the check.
    """
    out: dict[date, float] = {}
    for tag in CONCEPT_ALIASES[concept]:
        for p in points_for_tag(facts, tag):
            if p.period_start is None or p.value is None:
                continue
            if 80 <= (p.period_end - p.period_start).days <= 100:
                out.setdefault(p.period_end, float(p.value))
    return out


def _nonop_share_txt(share: float, *, compact: bool = False) -> str:
    """The pre-tax share of a non-operating block, in words.

    THE PERCENTAGE IS SUPPRESSED WHEN ITS DENOMINATOR IS THIN. A quarter netting to near-zero
    pre-tax yields a share in the hundreds or thousands, which reads as a data error and buries the
    figure that is real; the revenue-relative half still carries the magnitude. ``compact`` is the
    per-item form used when several quarters are listed on one line — same rule, fewer words.
    """
    if share <= 1.5:
        return f"{share:.0%} of pre-tax" if compact else f"{share:.0%} of pre-tax income"
    return ("exceeds pre-tax" if compact
            else "more than the entire pre-tax result, which nets near zero")


def _nonoperating_earnings(edgar: EdgarClient, cik: str, reference_date: date) -> Sourced[str]:
    """How much of the latest quarter's pre-tax result came from BELOW the operating line.

    DERIVED, NOT PICKED — and that distinction is the whole design. ``pretax - operating`` IS the
    non-operating block by the arithmetic of the income statement, so it needs no choice among the
    overlapping one-off tags a filer may or may not use (see `pretax_income` in
    `vinci.edgar.concepts` for the three-tags-three-values measurement that ruled that route out).
    Both legs are totals the filer states, for one period, from one filing.

    WHY A READER NEEDS IT: a quarter whose earnings are substantially non-operating cannot anchor a
    P/E or an EPS-based valuation. NFLX's Q1-2026 carries a $2.59bn Warner Bros. Discovery
    termination fee booked below the operating line — 40% of pre-tax — and UBER's Q2-2026 carries
    ~$1.39bn of investment revaluation. Neither is visible anywhere on today's pages: the CIQ
    unusual-items block is ANNUAL-only, so a quarterly one-off has no route to the surface until it
    lands in a fiscal year, and no XBRL non-operating concept was read at all before this.
    """
    try:
        facts = edgar.companyfacts(cik)
    except (HttpError, KeyError):
        return Sourced.unknown(note="EDGAR companyfacts unavailable")
    op = _quarterly_map(facts, "operating_income")
    pre = _quarterly_map(facts, "pretax_income")
    rev = _quarterly_map(facts, "revenue")
    missing = " + ".join(n for n, m in (("operating income", op), ("pre-tax income", pre),
                                        ("revenue", rev)) if not m)
    if missing:
        return Sourced.unknown(
            note=f"no quarterly {missing} in EDGAR XBRL — the non-operating share cannot be "
                 f"derived without all three from ONE period")
    # ONE PERIOD BY CONSTRUCTION, not by checking afterwards. Taking each concept's own latest
    # quarter and then asserting they agree is the same discipline stated worse: one stale
    # straggler refuses a name whose data is fine (it refused UBER, the case this exists for).
    # Intersecting first asks the right question — the newest quarter for which ALL THREE totals
    # were filed — so the subtraction is within one period because there was never another option.
    common = sorted(d for d in (set(op) & set(pre) & set(rev)) if d <= reference_date)
    if not common:
        return Sourced.unknown(
            note="operating income, pre-tax income and revenue never share a quarter in EDGAR "
                 "XBRL — subtracting across periods would not be a non-operating figure")
    # THE TRAILING FOUR QUARTERS, not just the newest — because the figure a reader is about to
    # divide by is an LTM one. NFLX settled it: the $2.59bn Warner Bros. Discovery termination fee
    # lands in Q1-2026, so a latest-quarter-only read reports Q2's ordinary -$124M and says
    # nothing, while the LTM EPS under a P/E still carries the whole fee. The analyst's objection
    # was to FY26 GAAP EPS, which is exactly this window.
    window = common[-4:]
    src = f"EDGAR XBRL pre-tax − operating, quarters {window[0]}..{window[-1]}"

    def _arms(d: date) -> tuple[float, float | None, float | None]:
        """``(gap, share of pre-tax, share of revenue)``.

        A ZERO PRE-TAX QUARTER IS THE MOST RELEVANT CASE, NOT AN ABSENT ONE (review finding, #415).
        Returning None for the share there dropped the quarter from `material` and printed "no
        material non-operating item" — but pre-tax of exactly zero with a non-zero gap means the
        below-the-line block precisely offsets operating income, which is the strongest possible
        statement that GAAP EPS is not an operating anchor. The share is genuinely undefined, so it
        is `inf`: the pre-tax arm passes, the REVENUE arm still has to carry the materiality, and
        the existing >1.5 branch renders the "nets near zero" wording instead of a nonsense
        percentage. A zero gap on zero pre-tax is a true nothing and stays 0.0.
        """
        g = pre[d] - op[d]
        share = (abs(g) / abs(pre[d]) if pre[d] else (math.inf if g else 0.0))
        return (g, share, (abs(g) / abs(rev[d]) if rev[d] else None))

    material = [(d, g, s, r) for d, g, s, r in ((d, *_arms(d)) for d in window)
                if s is not None and r is not None
                and s >= _NONOP_PRETAX_SHARE and r >= _NONOP_REVENUE_SHARE]
    if not material:
        end = window[-1]
        gap = _arms(end)[0]
        return Sourced.present(
            f"no material non-operating item in the four quarters to {end} — in the latest, "
            f"${gap / 1e6:,.0f}M against ${pre[end] / 1e6:,.0f}M pre-tax", source_ref=src)
    # EVERY MATERIAL QUARTER, NOT THE LARGEST ONE (2026-08-12). Naming only the biggest was chosen
    # for a reason that does not survive its own live case: UBER carries THREE material quarters —
    # 2025-09-30 +$1,507M, 2026-03-31 −$1,427M, 2026-06-30 +$1,387M — and the page named the first,
    # calling it "an earlier quarter still inside the trailing four". A reader is then told the
    # distortion sits behind them and the recent quarters are clean; both dropped quarters are the
    # RECENT ones, and one of them is the $1.4bn revaluation an analyst flagged against this very
    # field. The figure a reader divides by is an LTM one, so every quarter inside it counts.
    #
    # AND THE NET IS THE POINT THE LARGEST CANNOT MAKE. UBER's two unnamed quarters point OPPOSITE
    # WAYS and very nearly cancel; the trailing sum is what an LTM EPS actually carries, not the
    # biggest single item. Reporting the maximum implied a distortion the LTM does not have.
    if len(material) > 1:
        def signed(v: float) -> str:  # "+$1,507M" — the sign leads, the $ stays on the figure
            return f"{'+' if v >= 0 else '−'}${abs(v) / 1e6:,.0f}M"

        net = sum(_arms(d)[0] for d in window)
        items = " · ".join(
            f"{d} {signed(g)} ({_nonop_share_txt(s, compact=True)} · {r:.0%} of revenue)"
            for d, g, s, r in material)  # chronological — `material` is built in window order
        return Sourced.present(
            f"{len(material)} of the trailing four quarters carry a material block from BELOW the "
            f"operating line — {items} — netting {signed(net)} across the four. A trailing "
            f"EPS or P/E spanning them is not an operating anchor, and the LTM figure carries the "
            f"SUM, not the largest of them.",
            source_ref=src)
    end, gap, share, rev_share = material[0]
    assert share is not None and rev_share is not None
    share_txt = _nonop_share_txt(share)
    where = ("the latest quarter" if end == window[-1]
             else "an earlier quarter still inside the trailing four")
    return Sourced.present(
        f"${gap / 1e6:,.0f}M of the quarter ended {end} came from BELOW the operating line — "
        f"{share_txt}, and {rev_share:.0%} of revenue. Operating income ${op[end] / 1e6:,.0f}M → "
        f"pre-tax ${pre[end] / 1e6:,.0f}M. This is {where}, so a trailing EPS or P/E spanning it "
        f"is not an operating anchor.",
        source_ref=src)


# --- share-count trend + P/E-basis sanity (EDGAR XBRL) ----------------------------------------

_SHARES_WINDOW_DAYS = 730  # trailing ~2y — current capital-allocation posture, not a stale 7y delta


#: How far a share-count jump may sit from the filer's OWN stated factor and still be that event —
#: RELATIVE, and narrow, because the measurement says it can be. NFLX's cover count moves 9.96x
#: against 10.02x restated in EPS: **0.6% apart**. That gap has a physical cause and therefore a
#: bound — a cover count is an as-of headcount, so between the two cover dates the ORGANIC change
#: (NFLX was retiring ~0.7% of its shares per quarter) rides on top of the split factor. One
#: period's organic drift sits far inside 25%; a different corporate action does not.
#:
#: THE FIRST CUT USED A FACTOR OF 2 — 5x through 20x for a stated 10x — AND THAT WAS A DEFECT
#: rather than merely loose (review finding, #413). A 5x dilutive issuance sitting BEFORE a real
#: 10x split matched first, and the "post-change" segment then still crossed the true break: the
#: function emitted `+900.0%` wrapped in a sentence asserting the basis had been accounted for.
#: That is worse than the bug this code exists to fix, because it reads as checked.
_SPLIT_RATIO_TOL = 0.25


def _basis_break(pts: list[ConceptPoint], factor: float) -> int | None:
    """Index of the point sitting on the FAR side of a share-basis change, or None.

    ``factor`` is the filer's own restatement ratio (:func:`share_basis_change`, read off annual
    EPS). This locates WHERE it lands in the share series, which the factor alone cannot say.

    THE BEST MATCH, NOT THE FIRST — the second half of the #413 fix, and independent of the
    tolerance. Scanning for the first in-range jump makes the answer depend on the ORDER in which
    corporate actions happened, so a 5x raise preceding a 10x split wins on position rather than on
    fit. Choosing the closest ratio removes that sensitivity outright: with both a 5x and a 10x jump
    in a series whose stated factor is 10x, the split wins by an error of 0.6% against 50%.

    DIRECTION-FREE, matching the detector it corroborates: `share_basis_change` returns
    ``max(a/b, b/a)`` precisely because a reverse split contaminates identically, and it is the
    commoner event in the $300M-$10B hunting band. A one-directional scan here would re-open that
    blind spot on the side of the series where it actually bites — MVST trades at $0.92.
    """
    best: tuple[float, int] | None = None
    for i, (a, b) in enumerate(zip(pts, pts[1:], strict=False)):
        if not a.value or not b.value:
            continue
        ratio = max(a.value / b.value, b.value / a.value)
        err = abs(ratio - factor) / factor
        if err <= _SPLIT_RATIO_TOL and (best is None or err < best[0]):
            best = (err, i + 1)
    return best[1] if best is not None else None


def _split_straddled_trend(recent: list[ConceptPoint], brk: int, factor: float) -> Sourced[str]:
    """The reading for a window a share-basis change runs through — measured on ONE side of it.

    NO CROSS-BASIS PERCENTAGE IS PRINTED, not even a corrected one. Re-scaling the pre-change points
    by the factor would yield a comparable number, and it would be OUR arithmetic sitting in the
    slot a reader reads as the filer's — the move the buyback average was refused for. What the
    filer actually supports is the post-change series, so that is what is quoted, with the change
    named so the missing earlier half is explained rather than silently dropped.
    """
    post = recent[brk:]
    at = recent[brk].period_end
    rose = (recent[brk].value or 0) > (recent[brk - 1].value or 0)
    change = f"~{factor:.1f}x share-basis change at {at} (count {'rose' if rose else 'fell'})"
    src = f"EDGAR XBRL shares, post-basis-change {post[0].period_end}..{post[-1].period_end}"
    if len(post) < 2:
        return Sourced.present(
            f"NOT COMPARABLE across this window: {change}. Only one share count since it "
            f"({post[0].value:,.0f} at {post[0].period_end}) — no trend on the current basis yet.",
            source_ref=src)
    first, last = post[0], post[-1]
    pct = (last.value / first.value - 1.0) if first.value else 0.0
    word = "diluting" if pct > 0.02 else "buying back" if pct < -0.02 else "flat"
    # THE SPAN IS PRINTED BECAUSE THE BAND DID NOT MOVE. The +-2% label thresholds were set against
    # a ~2y window; a post-change window is whatever the filer's calendar leaves, and NFLX's is 0.5y
    # — where -1.4% reads "flat" while the same pace over two years would read "buying back". The
    # threshold is a face-validity constant and is NOT re-tuned here (that is a separate judgment,
    # and re-tuning it as a side effect of a split fix is how a calibration quietly drifts); making
    # the span explicit is what keeps the label honest at a length it was not calibrated for.
    span = (last.period_end - first.period_end).days / 365.0
    return Sourced.present(
        f"{word} over ~{span:.1f}y since a {change}: {first.value:,.0f} ({first.period_end}) → "
        f"{last.value:,.0f} ({last.period_end}), {pct:+.1%}. The pre-change count is a DIFFERENT "
        f"BASIS and is not compared — an endpoint delta across the change measures the "
        f"restatement, not dilution.",
        source_ref=src)


def _share_count_trend(edgar: EdgarClient, cik: str, reference_date: date) -> Sourced[str]:
    """Recent (trailing ~2y) share-count trend — a 7y endpoint delta hides the current posture.

    SPLIT-AWARE, because across a basis change the percentage is a lie of arithmetic. NFLX's
    committed page read *"diluting (trailing ~1.7y): 427,458,114 → 4,163,939,676, +874.1%"* with no
    flag anywhere: the filer executed a 10:1 forward split in Nov-2025 and restated its EPS
    comparatives but never the dei cover count, so the two endpoints are different units. On one
    basis the count FELL ~1.4% while the company was buying stock back — the label was not merely
    overstated, it pointed the opposite way.

    THE FACTOR IS READ FROM THE FILER, NEVER INFERRED FROM THE MAGNITUDE. `share_basis_change` finds
    one fiscal period reported at two values by two filings — a restatement the company itself
    performed. It is fed the ANNUAL EPS series and not the share series, and that is not an
    implementation detail: run against these very share points it returns None (a dei cover count is
    never re-filed for a prior period, so no ratio exists to read), and against the diluted
    weighted-average series it returns a confidently wrong 7.0x. Only EPS states 10.02x. A guard
    keyed to either of the other two would have shipped and never fired — which is why this was
    measured on all three before the branch was written.
    """
    try:
        facts = edgar.companyfacts(cik)
        pts = [p for p in extract_points(facts, "shares") if p.value]
    except (HttpError, KeyError):
        return Sourced.unknown(note="EDGAR companyfacts shares unavailable")
    pts.sort(key=lambda p: p.period_end)
    recent = [p for p in pts if (reference_date - p.period_end).days <= _SHARES_WINDOW_DAYS]
    if len(recent) < 2:
        return Sourced.unknown(
            note=f"<2 XBRL shares points in the trailing ~2y ({len(pts)} total) — no current trend"
        )
    # A basis change OUTSIDE the window is not this window's problem: every point in it then sits on
    # one basis and the ordinary reading is correct. Only a break INSIDE it makes the endpoints
    # incomparable — so the factor alone never suppresses a trend, its LOCATION does.
    factor = share_basis_change(extract_points(facts, "eps_diluted"))
    brk = _basis_break(recent, factor) if factor else None
    if brk is not None:
        return _split_straddled_trend(recent, brk, factor or 0.0)
    first, last = recent[0], recent[-1]
    pct = (last.value / first.value - 1.0) if first.value else 0.0
    word = "diluting" if pct > 0.02 else "buying back" if pct < -0.02 else "flat"
    span = (last.period_end - first.period_end).days / 365.0
    return Sourced.present(
        f"{word} (trailing ~{span:.1f}y): {first.value:,.0f} ({first.period_end}) → "
        f"{last.value:,.0f} ({last.period_end}), {pct:+.1%}",
        source_ref=f"EDGAR XBRL shares, trailing {first.period_end}..{last.period_end}",
    )


def _pe_reconciliation(
    record: DataRecord, edgar: EdgarClient, bundle: CiqBundle, revised_guidance: Sourced[str]
) -> tuple[str, str] | None:
    """Whether the trailing GAAP P/E is meaningful. Returns ``(flag, pe_note)`` or None — ``flag``
    is the full human-review line; ``pe_note`` is a SHORT caveat to carry ON the P/E field itself so
    the multiple never renders 'naked' as cheap (closes the gap where a distorted P/E showed clean).
    When the forward adjusted EPS is now in the dossier (99.1), RESOLVE the old 'verify against
    forward EPS' flag into a reconciliation — the trailing GAAP P/E is one-time-distorted and the
    clean read is the forward adjusted guide (this also subsumes the EDGAR-vs-CIQ P/E conflict).
    When the adjusted EPS isn't available the original open flag stands. None when trailing EPS is
    in line with recent history (no distortion)."""
    pe = record.fundamentals.pe
    if not pe.is_known or pe.value is None or not record.identity.cik:
        return None
    try:
        eps = sorted(
            (p for p in extract_points(edgar.companyfacts(record.identity.cik), "eps_diluted")
             if p.is_annual and p.value is not None),
            key=lambda p: p.period_end,
        )
    except (HttpError, KeyError):
        return None
    if len(eps) < 3:
        return None
    # A SHARE-BASIS CHANGE MAKES THIS COMPARISON MEANINGLESS, and the flag it produces is worse
    # than silence because it names the wrong cause. NFLX's committed page said "trailing EPS 2.53
    # is anomalous vs the recent median 7.00" — 2.53 is CORRECT, and the MEDIAN is the contaminated
    # figure, drawn across a 10:1 split the filer restated only two years of. A reader told to
    # "verify against normalized/forward EPS" is being sent after an earnings anomaly that does not
    # exist. Silent here rather than re-worded: the percentile beside it already refuses WITH the
    # split as its stated reason, and a second differently-worded split note is a claim that drifts.
    if share_basis_change(eps) is not None:
        return None
    latest, prior = eps[-1].value, [p.value for p in eps[:-1]][-4:]
    med = statistics.median(prior)
    if med == 0 or latest is None:
        return None
    if not ((latest > 0) != (med > 0) or latest / med > 2.5 or latest / med < 0.4):
        return None  # trailing EPS is in line with recent history — no distortion
    eps_m = _ADJ_EPS.search(revised_guidance.value or "")
    price = record.prices.last.value if record.prices.last.is_known else None
    ciq_pe = ciq_sheets.pe_ltm_current(bundle)
    if eps_m and price:  # RESOLVED — the forward adjusted EPS is now sourced
        lo, hi = float(eps_m.group(1)), float(eps_m.group(2))
        ciq_tail = ""
        if ciq_pe.status is SourceStatus.PRESENT and ciq_pe.value:
            # THE EPS DIRECTION IS ARITHMETIC ONLY ON ONE CLOSE. The tail always said CIQ's basis
            # was "(lower)" — right on its one live instance (VRRM, GAAP 5.6x vs CIQ 16.8x) and
            # wrong whenever CIQ is the lower multiple (NCNO's 419x vs 154x is that shape). When
            # both multiples divide the same close, the higher one rests on the smaller EPS; when
            # the closes differ, price moved between them too, so the date is stated instead.
            ciq_day = ciq_sheets.pe_ltm_asof(bundle)
            if ciq_day is not None and ciq_day == record.prices.last.as_of \
                    and ciq_pe.value != round(pe.value, 1):
                basis = "lower" if ciq_pe.value > pe.value else "higher"
                ciq_tail = (f"; CIQ P/LTM {ciq_pe.value:.1f}x, on the same close, uses a "
                            f"different ({basis}) trailing EPS basis")
            else:
                on = f" at its {ciq_day.isoformat()} close" if ciq_day is not None else ""
                ciq_tail = (f"; CIQ P/LTM {ciq_pe.value:.1f}x{on} uses a different trailing EPS "
                            f"basis")
        flag = (
            f"RESOLVED (P/E basis) — trailing GAAP P/E {pe.value:.1f}x is one-time-distorted: "
            f"latest GAAP EPS {latest:.2f} is ~{latest / med:.1f}× the recent median {med:.2f}, so "
            f"{pe.value:.1f}x is not a meaningful 'cheap' read. Clean read: forward adjusted guide "
            f"${lo:.2f}–${hi:.2f} → ~{price / ((lo + hi) / 2):.1f}x at the current price{ciq_tail}."
        )
        return flag, "one-time-distorted EPS — not a clean multiple; see the P/E-basis flag"
    flag = (  # adjusted EPS not available — the original open flag stands
        f"P/E may be distorted by non-recurring EPS — latest annual EPS {latest:.2f} vs "
        f"recent median {med:.2f}; verify against normalized/forward EPS (CIQ)"
    )
    note = (
        f"distorted — P/E rests on a non-current positive EPS; latest annual EPS is negative "
        f"({latest:.2f}). Not a meaningful multiple — see the P/E-basis flag"
        if latest < 0 else
        f"distorted — trailing EPS {latest:.2f} is anomalous vs the recent median {med:.2f}; "
        f"not a clean multiple — see the P/E-basis flag"
    )
    return flag, note


def _ltm_gaap_eps(fs: FinancialSummary | None) -> float | None:
    """The LTM GAAP DILUTED EPS as a STRUCTURED value from the financial-summary annual table —
    the 'EPS (GAAP, dil.)' row's ``values`` at the 'LTM' column. None when the summary, the table,
    the row, the LTM column, or the structured value is absent. Reads ``values`` (structured),
    NEVER ``cells`` (display) — the parsers-consume-structured-values rule; a display '(2.08)'/'—'
    is never parsed here."""
    if fs is None:
        return None
    annual = fs.annual
    if annual.status is not SourceStatus.PRESENT or annual.value is None:
        return None
    tbl = annual.value
    # PREFIX-match the LTM header — it can carry a Reclassified '(R)' suffix ('LTM (R)', ciq_sheets
    # tags every period column), exactly like the renderer's own LTM detection
    # (render.py startswith('LTM')). Exact '== "LTM"' would return None on a reclassified twin and
    # silently reintroduce the claim-#7 blind spot for it.
    i = next((k for k, c in enumerate(tbl.columns) if str(c).upper().startswith("LTM")), None)
    if i is None:
        return None
    for row in tbl.rows:
        if row.label == "EPS (GAAP, dil.)" and len(row.values) > i:
            return row.values[i]
    return None


def _eps_caveat_flags(
    record: DataRecord, bundle: CiqBundle, *, eps_resolved: bool,
    ltm_gaap_eps: float | None = None,
) -> list[str]:
    """Flag (a) that earnings power (company-adjusted, non-GAAP EPS) is not shown — UNLESS it now is
    (``eps_resolved``: the 99.1 adjusted EPS surfaced it, so the caveat is a resolved fact, not a
    warning); (b) when the EDGAR P/E conflicts ~Nx with CIQ P/LTM EPS, that the two divide by
    different earnings and the synthesis must not anchor on the LOWER of the two (whichever source
    it is) — kept UNLESS the LTM GAAP EPS is a known LOSS, where (d) owns it (stacking (b)+(d) is
    flag noise);
    (d) when a displayed trailing P/E multiple (EDGAR and/or CIQ) rests on NORMALIZED earnings
    while the LTM GAAP diluted EPS is a LOSS — SMPL showed EDGAR P/E 10.9x + CIQ P/LTM 16.0x beside
    an LTM GAAP dil EPS of −2.08 (LTM net income −$199M, the $249M impairment inside the window)
    with no basis label; (b) needs the two multiples ~2x apart, ``_pe_reconciliation`` checks the
    ANNUAL EPS (FY25 +1.02, in line) — both are blind to the LTM sign, the signal that is actually
    wrong; and (c) the ``ltm_gaap_eps``-UNAVAILABLE fallback of (d): CIQ prints a finite P/LTM
    while EDGAR shows no trailing P/E and the GAAP LTM sign can't be read."""
    pe = record.fundamentals.pe
    ciq_pe = ciq_sheets.pe_ltm_current(bundle)
    if not pe.is_known and ciq_pe.status is not SourceStatus.PRESENT:
        return []  # no EPS-based multiple shown at all — nothing to caveat
    out: list[str] = []
    # The bare 'GAAP EPS understates earnings power; adjusted not shown' caveat was DROPPED (2026-06
    # flag-noise audit): pure boilerplate that fired on 8/10 names — its only fact (adjusted EPS
    # UNAVAILABLE) already rides in a synthesis key_unknown, and asserting non-GAAP > GAAP with no
    # non-GAAP figure in hand is itself a mild assemble-not-conclude violation. The substantive,
    # source-bound EDGAR-vs-CIQ P/E conflict below stays.
    # the EDGAR-vs-CIQ P/E conflict: an open flag only while unresolved; when the adjusted EPS is
    # shown it folds into the resolved P/E reconciliation (_pe_reconciliation), not repeated here.
    if (
        not eps_resolved and pe.is_known and pe.value
        and ciq_pe.status is SourceStatus.PRESENT and ciq_pe.value
        and not (ltm_gaap_eps is not None and ltm_gaap_eps < 0)  # a GAAP LTM loss → (d) owns it
    ):
        ratio = max(pe.value, ciq_pe.value) / min(pe.value, ciq_pe.value)
        if ratio >= 2:
            # WHICHEVER MULTIPLE IS LOWER is the one a reader takes as 'cheap', and the inputs say
            # nothing about WHY the two differ. The first text blamed EDGAR every time ("EDGAR
            # trailing EPS is one-time-inflated … must not anchor on <EDGAR>x"), true only when
            # EDGAR is the lower multiple. PARR (EDGAR 10.4x on FY2025 EPS 7.16 vs CIQ 5.0x; its LTM
            # GAAP EPS row reads 17.09) and NCNO's committed page (416.2x vs 154.3x) carried the
            # warning on the HIGHER multiple, leaving the low one un-caveated. The two also differ
            # in more than earnings (price date, CIQ's own EPS definition), so no cause is named.
            low, low_src = ((pe.value, "EDGAR") if pe.value < ciq_pe.value
                            else (ciq_pe.value, "CIQ"))
            # EACH MULTIPLE'S CLOSE, stated in the one sentence that compares them: the EDGAR P/E
            # is priced at the latest stored close (`_at_latest_close`), CIQ's at its pull, and a
            # stale pull leaves them weeks apart (NCNO's P/LTM EPS close is 2026-07-17, VRRM's
            # 2026-03-31, against store prices through 2026-09-16).
            edgar_day = record.prices.last.as_of if record.prices.last.is_known else None
            ciq_day = ciq_sheets.pe_ltm_asof(bundle)
            if edgar_day is not None and edgar_day == ciq_day:
                closes = f", both at the {edgar_day.isoformat()} close"
            elif edgar_day is not None and ciq_day is not None:
                closes = (f" (EDGAR at the {edgar_day.isoformat()} close, CIQ at its "
                          f"{ciq_day.isoformat()} close — {abs((edgar_day - ciq_day).days)} days "
                          f"apart)")
            else:
                closes = ""
            out.append(
                f"EDGAR P/E ({pe.value:.1f}x) conflicts ~{ratio:.0f}x with CIQ P/LTM EPS "
                f"({ciq_pe.value:.1f}x){closes} — EDGAR divides by the latest fiscal-year GAAP "
                f"diluted EPS, CIQ by its own trailing-twelve-month EPS. The inputs do not say "
                f"which earnings recur, so the synthesis must not anchor on the lower {low:.1f}x "
                f"({low_src}) without naming the earnings behind it."
            )
    # (d) The real basis mismatch, keyed on the LTM GAAP EPS SIGN (the signal (b)/(c)/_pe_recon
    # miss). A displayed positive trailing P/E multiple — EDGAR and/or CIQ — while GAAP LTM diluted
    # EPS is a LOSS. What that PROVES is a NEGATIVE: the denominator is not the LTM GAAP EPS. Which
    # denominator it IS the inputs do not say, so the caveat must not pick one (item 19a): the
    # earlier text asserted "rest on normalized/adjusted earnings", while ``_pe_distortion_note``
    # concluded the OTHER candidate — "P/E rests on a non-current positive EPS" — from a real
    # comparison against the latest annual EPS. Both shipped on CNXC and FUBO, in one dossier, about
    # one number, with the note pointing the reader AT the contradicting flag ("see the P/E-basis
    # flag"). Naming both candidates and declaring the basis unstated is the only claim the inputs
    # support. Names both multiples that are shown.
    if ltm_gaap_eps is not None and ltm_gaap_eps < 0:
        shown: list[str] = []
        if pe.is_known and pe.value and pe.value > 0:
            shown.append(f"EDGAR P/E {pe.value:.1f}x")
        if ciq_pe.status is SourceStatus.PRESENT and ciq_pe.value and ciq_pe.value > 0:
            shown.append(f"CIQ P/LTM EPS {ciq_pe.value:.1f}x")
        if shown:
            # ONE plurality decision feeding every agreeing word. The verb was hardcoded `rest`
            # while the pronoun switched on `len(shown)` — two agreement calls from one fact, so
            # the singular case read "EDGAR P/E 6.0x rest … do not read it" on all three live
            # names (CNXC, FUBO, SMPL), every one of them single-multiple.
            plural = len(shown) > 1
            out.append(
                f"{' and '.join(shown)} {'do' if plural else 'does'} not rest on LTM GAAP "
                f"earnings — LTM GAAP diluted EPS is NEGATIVE ({ltm_gaap_eps:.2f}), so a positive "
                f"multiple must use some other denominator (an EPS from a non-current period, or "
                f"a normalized/adjusted figure — the displayed basis does not say which). Do not "
                f"read {'them' if plural else 'it'} as a GAAP trailing multiple."
            )
    # (c) FALLBACK, only when the LTM GAAP EPS sign is UNAVAILABLE: CIQ prints a finite trailing P/E
    # while EDGAR shows none (an absent EDGAR P/E is itself the negative-GAAP tell). With the sign
    # in hand (d) supersedes this, so gate on ltm_gaap_eps is None to avoid a double caveat.
    elif ltm_gaap_eps is None and not pe.is_known and (
        ciq_pe.status is SourceStatus.PRESENT and ciq_pe.value
    ):
        out.append(
            f"CIQ P/LTM EPS prints {ciq_pe.value:.1f}x while no GAAP trailing P/E is shown "
            f"(trailing GAAP EPS negative or unavailable) — the CIQ multiple rests on a "
            f"different earnings definition; do not read {ciq_pe.value:.1f}x as a GAAP "
            f"trailing P/E."
        )
    return out


def _leverage_basis_flag(net_lev: Sourced[float]) -> str | None:
    """The SHOWN net-debt/EBITDA (CIQ-reported or EDGAR GAAP EBITDA) is not the covenant
    basis: management and credit covenants typically define leverage on ADJUSTED EBITDA (a larger
    denominator → a lower ratio); that non-GAAP reconciliation lives in the earnings
    release/transcript (UNAVAILABLE). Flag the basis so the human doesn't read the reported ratio as
    the covenant ratio. Reads the RESOLVED ratio (the value the dossier actually shows), not the raw
    EDGAR record — so the flagged number can never disagree with the net-debt/EBITDA field.
    Gated on magnitude: below ~1.5x (incl. NET CASH) the reported ratio is already modest and the
    reported-vs-covenant-basis caveat — which only pushes the ratio LOWER — is immaterial review
    noise; it earns its place only when the reported ratio is large enough to look levered. (A 1.3x
    name reads as 'modest' on its own; the caveat changes no judgment there.)"""
    if net_lev.status is not SourceStatus.PRESENT or net_lev.value is None:
        return None
    if net_lev.value < 1.5:
        return None
    return (
        f"Net debt/EBITDA ({net_lev.value:.1f}x) is on REPORTED EBITDA (CIQ / consolidated GAAP), "
        f"not the covenant basis; management and credit covenants typically define leverage on "
        f"adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings "
        f"release/transcript (currently UNAVAILABLE) — do not read {net_lev.value:.1f}x as the "
        f"covenant-basis leverage."
    )


# max/min ratio above which the two CIQ EV/EBITDA sheets are flagged as materially disagreeing
# (~25% apart) — a multiple gap that changes the read. Below it the gap isn't decision-relevant.
_EV_EBITDA_CONFLICT_RATIO = 1.25
# days the Financials→Multiples latest Close may trail the assembly reference date before its
# "current" multiple (and the own-history range/percentile built on it) is treated as STALE. A live
# pull carries an intra-quarter Close within days of the reference; a wider gap means the latest
# column is a clean prior quarter-end that predates any subsequent re-rate (VRRM: 2026-03-31 close,
# 8.5x, vs a post-drawdown comps read of 4.7x). Half a quarter ≈ 45d cleanly separates the two.
_STALE_CLOSE_DAYS = 45


def _ev_ebitda_integrity_flag(bundle: CiqBundle, reference_date: date) -> str | None:
    """CIQ reports the name's current EV/EBITDA on TWO sheets — Financials→Multiples (TEV/LTM,
    ``ev_ebitda_current``, the own-history-range basis) and Comparable-Analysis Trading-Multiples
    (``comps_ev_ebitda``, the cross-sectional lead). A material disagreement is a DATA-INTEGRITY
    signal, not a stable 'basis difference': the usual causes are (1) a STALE Financials Close — its
    last dated column predates the reference date and a since-then re-rate (VRRM), or (2) the two
    sheets priced the name on different dates. Flag the specific cause when detectable, else a plain
    cross-sheet gap; route to the human caveat tier so the operator verifies rather than trusting it
    silently. (After the subject-by-ticker fix, the old MVST 10.0x-vs-38.4x 'conflict' — a comps row
    mis-read as Samsung SDI — no longer fires; the correct Microvast comps read agrees.)

    Staleness is only flagged when it MATTERS: if a present current comps figure AGREES with the
    stale Financials multiple, the staleness is immaterial (the price didn't move) and the inline
    as-of date on the range line already discloses it, so the bottom caveat is suppressed as noise
    (MVST: stale 10.0x vs current comps 11.1x). It fires when comps DISAGREES (VRRM — the read
    changes) or when comps is ABSENT (no way to confirm the stale price is still current)."""
    fin = ciq_sheets.ev_ebitda_current(bundle)
    comp = ciq_sheets.comps_ev_ebitda(bundle)
    fin_date = ciq_sheets.ev_ebitda_asof(bundle)
    stale_days = (reference_date - fin_date).days if fin_date is not None else None
    stale = stale_days is not None and stale_days > _STALE_CLOSE_DAYS

    comps_present = comp.status is SourceStatus.PRESENT
    disagree = False
    if fin.status is SourceStatus.PRESENT and comps_present:
        assert fin.value is not None and comp.value is not None
        lo, hi = sorted((fin.value, comp.value))
        disagree = lo > 0 and hi / lo >= _EV_EBITDA_CONFLICT_RATIO
    # a stale Close whose staleness a present, agreeing comps confirms immaterial adds nothing
    # beyond the inline as-of date — suppress it; keep it when comps disagrees or is absent.
    material_stale = stale and not (comps_present and not disagree)
    if not material_stale and not disagree:
        return None

    if material_stale:
        assert fin_date is not None and stale_days is not None
        head = (
            f"EV/EBITDA stale-price caveat — CIQ's Financials→Multiples current TEV/LTM "
            f"{_fmt_mult(fin)} is priced at its last Close {fin_date.isoformat()}, {stale_days}d "
            f"before the {reference_date.isoformat()} reference; for a since-re-rated name this "
            "'current' multiple AND the own-history range/percentile built on it are stale"
        )
        if disagree:
            head += (
                f". The Comparable-Analysis sheet reads {_fmt_mult(comp)} on a current price — "
                "prefer that figure and re-pull the Financials multiple."
            )
        else:
            head += " — read it as-of that date, not as today's multiple."
        return head
    return (
        f"EV/EBITDA cross-sheet gap — CIQ's Financials→Multiples reads {_fmt_mult(fin)} and its "
        f"Comparable-Analysis sheet reads {_fmt_mult(comp)} on the same concept; verify which the "
        "verdict should use (a stale Close, a different pricing date, or an EBITDA basis) before "
        "reading either."
    )


def _fmt_mult(s: Sourced[float]) -> str:
    """A Sourced EV/EBITDA multiple → 'N.Nx', or '?' when it isn't a present number."""
    return f"{s.value:.1f}x" if s.status is SourceStatus.PRESENT and s.value is not None else "?"


# --- adjusted-basis multiples + leverage (from the 99.1 guide + EDGAR net-debt/shares + EOD) ----

_NUM = r"(\d+(?:\.\d+)?)"  # a plain number — never swallow trailing punctuation (e.g. '1.25.')
_ADJ_EBITDA = re.compile(rf"Adjusted EBITDA of \$?{_NUM}\s*million to \$?{_NUM}\s*million", re.I)
_ADJ_EPS = re.compile(rf"Adjusted EPS of \$?{_NUM} to \$?{_NUM}", re.I)


def _adjusted_facts(
    record: DataRecord, edgar: EdgarClient, revised_guidance: Sourced[str],
    reference_date: date,
) -> tuple[Sourced[str], Sourced[str], Sourced[str]]:
    """Surface the adjusted (non-GAAP) figures the GAAP caveats called UNAVAILABLE — the 99.1
    revised guidance is in the dossier: adjusted EPS, forward EV/adj-EBITDA, and covenant-basis
    net-debt/adj-EBITDA. Each is UNKNOWN if its inputs aren't present — never fabricated (the GAAP
    caveat stays a flag whenever its adjusted counterpart can't be shown). Returns
    (adjusted_eps, ev_ebitda_adjusted_fwd, net_debt_to_ebitda_adjusted)."""
    src = revised_guidance.source_ref or "EDGAR 8-K Ex-99.1"
    text = revised_guidance.value or ""
    eb, eps = _ADJ_EBITDA.search(text), _ADJ_EPS.search(text)
    unk: Sourced[str] = Sourced.unknown(note="adjusted figure not in the 99.1 revised guidance")
    price = record.prices.last.value if record.prices.last.is_known else None

    adj_eps = unk
    if eps:
        lo, hi = float(eps.group(1)), float(eps.group(2))
        tail = f"; adj P/E ~{price / ((lo + hi) / 2):.1f}x at ${price:.2f}" if price else ""
        adj_eps = Sourced.present(
            f"FY26 guide ${lo:.2f}–${hi:.2f}{tail} — earnings power above the GAAP basis",
            source_ref=src,
        )

    cik = record.identity.cik
    try:
        snap = edgar.fundamental_snapshot(cik) if cik else None
        share_pts = (
            [p for p in extract_points(edgar.companyfacts(cik), "shares") if p.value] if cik else []
        )
    except (HttpError, KeyError):
        snap, share_pts = None, []
    net_debt = snap.net_debt.value if snap and snap.net_debt.is_known else None
    # THE SAME STALENESS BOUND AS THE STOCK-INFO BASIS, because this multiplies it by a price:
    # `ev = price * shares + net_debt` below. A multi-class filer whose newest undimensioned count
    # predates a split (Visa: 2010, then a 4-for-1 in 2015) would compute an EV wrong by that
    # split factor, on a page whose headline share basis was correctly refused. Guarding one
    # consumer of a bad number and leaving its neighbour is how the first fix would have half
    # landed — the fleet is unaffected either way (counts run 10–375d against a 540d bound).
    fresh_pts = [
        p for p in share_pts
        if (reference_date - p.period_end).days <= _SHARES_MAX_AGE_DAYS
    ]
    shares = max(fresh_pts, key=lambda p: p.period_end).value if fresh_pts else None

    ev_adj, nd_adj = unk, unk
    if eb:
        eb_lo, eb_hi = float(eb.group(1)), float(eb.group(2))
        eb_mid = (eb_lo + eb_hi) / 2 * 1e6  # $ (the guide is in $M)
        band = f"FY26 adj-EBITDA ${eb_lo:.0f}–${eb_hi:.0f}M"
        if net_debt is not None:
            nd_adj = Sourced.present(
                f"~{net_debt / eb_mid:.1f}x fwd-adj (net debt ${net_debt / 1e6:,.0f}M / {band})",
                source_ref=f"{src} (adj-EBITDA) + EDGAR net debt",
            )
            if price and shares:
                ev = price * shares + net_debt
                ev_adj = Sourced.present(
                    f"~{ev / eb_mid:.1f}x (fwd, at current ${price:.2f}; EV ${ev / 1e6:,.0f}M "
                    f"/ {band})",
                    source_ref=f"{src} (adj-EBITDA) + EDGAR net debt + EOD price × shares",
                )
    return adj_eps, ev_adj, nd_adj


# --- CIQ-sourced fields (workbook-addressed; the extractors fail loud MISSING/UNKNOWN) ---------


def _valuation(
    record: DataRecord, bundle: CiqBundle, adj_eps: Sourced[str], adj_ev: Sourced[str],
    *, pe_note: str | None = None,
) -> Valuation:
    f = record.fundamentals
    pe = _sourced(f.pe, source_ref="EDGAR XBRL eps_diluted × EOD latest stored close")
    if pe_note and pe.status is SourceStatus.PRESENT:
        pe = pe.model_copy(update={"note": pe_note})  # carry the distortion caveat ON the value
    # trailing-only blind-flag: a trailing multiple with NO forward counterpart cannot tell a
    # temporarily depressed level from a permanently impaired one — force the synthesis to declare
    # it is flying blind rather than imply trailing-cheap = a reversible de-rating.
    ev = ciq_sheets.ev_ebitda_current(bundle)
    if ev.status is SourceStatus.PRESENT and adj_ev.status is not SourceStatus.PRESENT:
        ev = ev.model_copy(update={"note": TRAILING_ONLY_NOTE})
    return Valuation(
        cross_sectional=ciq_sheets.cross_sectional_valuation(bundle),
        pe=pe,
        pe_percentile_5y=_sourced(
            f.pe_pctile_vs_history,
            source_ref="EDGAR/EOD P/E pctile vs ~5y, at the latest stored close",
        ),
        # The EDGAR screen field `f.ev_ebitda` carries EBITDA *dollars* (screens/assemble.py
        # populates it from ebitda_annual), not the multiple — so the dossier's EV/EBITDA is the
        # authoritative CIQ TEV/LTM multiple, never the EDGAR scalar (never a dollar figure here).
        ev_ebitda=ev,
        ev_ebitda_percentile_5y=(
            _sourced(f.ev_ebitda_pctile_vs_history, source_ref="EDGAR (screen data-record)")
            if f.ev_ebitda_pctile_vs_history.is_known
            else ciq_sheets.ev_ebitda_percentile(bundle)
        ),
        ev_ebitda_adjusted_fwd=adj_ev,
        adjusted_eps=adj_eps,
        range_position=ciq_sheets.range_position(bundle),
        own_history=ciq_sheets.own_history_bands(bundle),  # (P3) structured bands for the chart
    )


def _net_debt_to_ebitda(
    bundle: CiqBundle, edgar_net_lev: Sourced[float]
) -> tuple[Sourced[float], Sourced[float]]:
    """Net-debt/EBITDA via a DETERMINISTIC source hierarchy — no judge, no manual reconciliation.
    CIQ is the depth-stage authority: its Balance Sheet classifies the scattered instrument debt
    (convertible / notes / short-term / subordinated) that EDGAR XBRL under-captures, so CIQ Net
    Debt ÷ CIQ LTM EBITDA wins outright when present. Else the EDGAR XBRL screen figure as a clearly
    LABELLED breadth fallback (itself fail-loud when its inputs are missing/inconsistent). Returns
    ``(net_debt_to_ebitda, ciq_net_debt)`` — the latter feeds the survival readout."""
    ciq_nd = ciq_sheets.net_debt(bundle)
    ciq_eb = ciq_sheets.ltm_ebitda(bundle)
    if ciq_nd.status is SourceStatus.PRESENT and ciq_eb.status is SourceStatus.PRESENT:
        assert ciq_nd.value is not None and ciq_eb.value is not None
        if ciq_eb.value <= 0:
            return Sourced.unknown(
                note=f"CIQ EBITDA ${ciq_eb.value:,.0f}M <= 0 — ratio meaningless"
            ), ciq_nd
        # bind BOTH periods (the bracket shows whether EBITDA is the LTM column or a stale FY, and
        # whether net debt is the same period) — never a bare 'LTM' label the value may not have.
        nd_p = (ciq_nd.source_ref or "").split("[")[-1].rstrip("]")
        eb_p = (ciq_eb.source_ref or "").split("[")[-1].rstrip("]")
        return Sourced.present(
            round(ciq_nd.value / ciq_eb.value, 1),
            source_ref=(
                f"CIQ Net Debt ${ciq_nd.value:,.0f}M [{nd_p}] ÷ "
                f"CIQ EBITDA ${ciq_eb.value:,.0f}M [{eb_p}]"
            ),
        ), ciq_nd
    if edgar_net_lev.status is SourceStatus.PRESENT:
        # carry the caveat in the SOURCE_REF (shown on a PRESENT fact) — the note is dropped
        # by the renderer for PRESENT, so a note-only caveat would vanish from the dossier.
        caveat = "breadth estimate — may under-capture scattered debt; pull CIQ"
        return edgar_net_lev.model_copy(update={
            "source_ref": f"{edgar_net_lev.source_ref}; {caveat}",
            "note": f"EDGAR XBRL {caveat}",
        }), ciq_nd
    return Sourced.unknown(
        note=f"no CIQ Net Debt/EBITDA; EDGAR {edgar_net_lev.note or 'UNKNOWN'} — pull CIQ"
    ), ciq_nd


def _net_debt_to_ocf(
    ciq_nd: Sourced[float], ciq_ocf: Sourced[float], edgar_net_ocf: Sourced[float]
) -> Sourced[float]:
    """Net-debt/OCF on the SAME CIQ net-debt basis as net-debt/EBITDA (so the two reads can't
    disagree on whether net debt exists): CIQ Net Debt ÷ CIQ operating cash flow when both present,
    else the EDGAR XBRL screen figure as a labelled breadth fallback, else UNKNOWN/'pull CIQ'."""
    if ciq_nd.status is SourceStatus.PRESENT and ciq_ocf.status is SourceStatus.PRESENT:
        assert ciq_nd.value is not None and ciq_ocf.value is not None
        if ciq_ocf.value <= 0:
            return Sourced.unknown(note=f"CIQ OCF ${ciq_ocf.value:,.0f}M <= 0 — ratio meaningless")
        nd_p = (ciq_nd.source_ref or "").split("[")[-1].rstrip("]")
        ocf_p = (ciq_ocf.source_ref or "").split("[")[-1].rstrip("]")
        return Sourced.present(
            round(ciq_nd.value / ciq_ocf.value, 1),
            source_ref=(
                f"CIQ Net Debt ${ciq_nd.value:,.0f}M [{nd_p}] ÷ "
                f"CIQ OCF ${ciq_ocf.value:,.0f}M [{ocf_p}]"
            ),
        )
    if edgar_net_ocf.status is SourceStatus.PRESENT:
        caveat = "breadth estimate — may under-capture scattered debt; pull CIQ"
        return edgar_net_ocf.model_copy(update={
            "source_ref": f"{edgar_net_ocf.source_ref}; {caveat}",
            "note": f"EDGAR XBRL {caveat}",
        })
    return Sourced.unknown(
        note=f"no CIQ Net Debt/OCF; EDGAR {edgar_net_ocf.note or 'UNKNOWN'} — pull CIQ"
    )


def _survival_capacity(
    net_lev: Sourced[float], adj_lev: Sourced[str], fcf_sign: Sourced[float],
    *, net_debt: Sourced[float] | None = None,
) -> Sourced[str]:
    """Solvency as ONE block — net leverage + self-funding (FCF sign). Each leg is present or
    fail-loud UNKNOWN (itself a risk). ``net_debt`` (CIQ, $M) lets a non-formable ratio still report
    the known balance-sheet position — a net-cash name is not a 'solvency risk'. No new data source.
    (H3) The nearest-maturity year is retired here — the month-precision E2 maturity wall (rendered
    in the survival super-section) supersedes the coarse 'nearest maturity wall: YYYY' line."""
    present = SourceStatus.PRESENT
    parts: list[str] = []
    if net_lev.status is present and net_lev.value is not None:
        basis = "CIQ" if "CIQ" in (net_lev.source_ref or "") else "GAAP"
        lev = f"net-debt/EBITDA {net_lev.value:.1f}x ({basis})"
        if net_lev.value < 0:
            lev += " → net cash"
        if adj_lev.status is present and adj_lev.value:
            lev += f"; {adj_lev.value}"
        parts.append(lev)
    elif net_debt is not None and net_debt.status is present and net_debt.value is not None:
        # ratio not formable, but the CIQ balance-sheet position IS known — show it rather than a
        # bare 'solvency risk', which a net-cash name is not.
        nd = net_debt.value
        pos = f"net cash ${-nd:,.0f}M" if nd < 0 else f"net debt ${nd:,.0f}M"
        parts.append(f"{pos} (CIQ); net-debt/EBITDA N/A ({net_lev.note or 'not derivable'})")
    else:
        parts.append(
            f"net-debt/EBITDA UNKNOWN ({net_lev.note or 'not derivable'}) — solvency risk"
        )
    if fcf_sign.status is present and fcf_sign.value is not None:
        parts.append(
            "FCF-positive → self-funding" if fcf_sign.value > 0
            else "FCF-negative → burning cash (cash not derived — a risk)"
        )
    else:
        parts.append("FCF sign UNKNOWN — runway not assessable (a risk)")
    return Sourced.present(
        " | ".join(parts),
        source_ref="CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign "
        "(survival capacity)",
    )


def _quality(
    record: DataRecord, edgar: EdgarClient, bundle: CiqBundle, reference_date: date,
    adj_leverage: Sourced[str], *, fcf: Sourced[float], margin: Sourced[str],
    trajectory: Sourced[str],
) -> Quality:
    """``fcf`` / ``margin`` / ``trajectory`` arrive already resolved against the EDGAR fallback (CIQ
    primary; EDGAR fills only an empty CIQ field) — assembled in :func:`assemble_mechanical`."""
    f = record.fundamentals
    edgar_net_lev = _sourced(
        f.net_leverage, source_ref="EDGAR XBRL net-debt/EBITDA (screen data-record)"
    )
    # CIQ-primary deterministic hierarchy: CIQ Net Debt ÷ CIQ LTM EBITDA wins; EDGAR is the labelled
    # breadth fallback. ``ciq_nd`` (CIQ Net Debt) also feeds the survival readout when a ratio can't
    # form. EDGAR net-debt under-captures scattered debt (the MVST case) — never the shown figure.
    net_lev, ciq_nd = _net_debt_to_ebitda(bundle, edgar_net_lev)
    edgar_net_ocf = _sourced(
        f.net_debt_to_ocf,
        source_ref="EDGAR XBRL net-debt/OCF (screen data-record) — OCF basis, not EBITDA",
    )
    # net-debt/OCF on the SAME CIQ net-debt basis as net-debt/EBITDA, so the two leverage rows can't
    # disagree on whether net debt exists (EDGAR figure is the labelled breadth fallback).
    net_ocf = _net_debt_to_ocf(ciq_nd, ciq_sheets.ltm_ocf(bundle), edgar_net_ocf)
    fcf_sign = _sourced(f.fcf_sign, source_ref="EDGAR XBRL FCF sign (screen data-record)")
    liquidity = ciq_sheets.liquidity_covenant_flags(bundle)
    return Quality(
        fcf_sign=fcf_sign,
        free_cash_flow=fcf,
        margin_trend=margin,
        net_debt_to_ebitda=net_lev,
        net_debt_to_ocf=net_ocf,
        net_debt_to_ebitda_adjusted=adj_leverage,
        survival_capacity=_survival_capacity(
            net_lev, adj_leverage, fcf_sign, net_debt=ciq_nd
        ),
        interest_coverage=ciq_sheets.interest_coverage(bundle),
        share_count_trend=(
            _share_count_trend(edgar, record.identity.cik, reference_date)
            if record.identity.cik
            else Sourced.unknown(note="no CIK")
        ),
        nonoperating_earnings=(
            _nonoperating_earnings(edgar, record.identity.cik, reference_date)
            if record.identity.cik
            else Sourced.unknown(note="no CIK")
        ),
        liquidity_covenant_flags=liquidity,
        multi_year_trajectory=trajectory,
        roic_trend=ciq_sheets.roic_trend(bundle),  # (P3) structured ROIC series for the chart
    )


def _concentration(bundle: CiqBundle) -> Concentration:
    return Concentration(
        segments=ciq_sheets.segments(bundle),
        segment_ebitda=ciq_sheets.segment_ebitda(bundle),
        customers=ciq_sheets.customers(bundle),
        geographic=ciq_sheets.geographic(bundle),
    )


def _consensus(bundle: CiqBundle) -> ConsensusContext:
    # (A1) STRUCTURED forward-year levels ride the same block the prose fields come from. Wired
    # HERE as well as in the refresh transform, through ONE builder: without it the first name
    # underwritten after A1 would carry no consensus data and A2 would render nothing for it.
    levels = {m: [ConsensusLevel(fy=c.fy, median=c.median, high=c.high, low=c.low,
                                 std_dev=c.std_dev, estimates=c.estimates) for c in cells]
              for m, cells in ciq_sheets.consensus_levels(bundle).items()}
    return ConsensusContext(
        consensus_levels=levels or None,
        eps_trend=ciq_sheets.eps_revisions(bundle),
        revenue_trend=ciq_sheets.revenue_revisions(bundle),
        revision_history=ciq_sheets.consensus_view(bundle),
        surprise_history=ciq_sheets.surprise_history(bundle),
    )


def _parse_money(s: str | None) -> float | None:
    """The ONE money-string → float parser (comma/$/M-aware, (paren)-negative). Preferred path is
    ALWAYS a structured schema float; this is the SINGLE sanctioned fallback when a rendered string
    must be parsed (DESIGN RULE). The comma-blind regex truncated '$1,101.80M' → 1."""
    if not s:
        return None
    t = s.strip()
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace(",", "").replace("$", "").rstrip("Mm ").strip()
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def _bs_bridge_coherence(bundle: CiqBundle, implied: ImpliedValuation) -> Sourced[str]:
    """(C3 coherence gate) The Balance-Sheet cash & total debt must reconcile with the
    implied-valuation bridge (a DIFFERENT CIQ sheet). On disagreement, render BOTH with sources + a
    soft caveat — never silently prefer one."""
    bs_cash = ciq_sheets._bs_latest(bundle, "Total Cash & ST Investments")
    bs_debt = ciq_sheets._bs_latest(bundle, "Total Debt")
    # LOAD-BEARING: the STRUCTURED bridge floats (DESIGN RULE — never re-parse the display string).
    # The fallback parses the render string via the shared _parse_money() only for a legacy bridge
    # predating the structured fields (bridge_cash/debt None but the string carries a figure).
    br = implied.bridge.value if implied.bridge.status is SourceStatus.PRESENT else ""

    def _leg(structured: float | None, label: str) -> float | None:
        if structured is not None:
            return structured
        m = re.search(rf"{label} \$([\d,.]+)", br or "")
        return _parse_money(m.group(1)) if m else None

    bc = _leg(implied.bridge_cash, "cash")
    bd = _leg(implied.bridge_debt, "debt")
    src = "CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation"

    def close(a: float | None, b: float | None) -> bool:
        return a is not None and b is not None and abs(a - b) <= max(1.0, abs(b) * 0.05)

    def money(v: float | None) -> str:  # an ABSENT figure is UNKNOWN — never a fabricated $0
        return f"${v:,.0f}M" if v is not None else "UNKNOWN"

    # Each leg (cash / debt) is cross-checkable ONLY when both its figures are present. An absent
    # figure is UNKNOWN — it is never coerced to $0 and never read as a disagreement (fail loud):
    # real CIQ bridges omit a row routinely; "$0" would fabricate a number the source never gave.
    legs = (("cash", bs_cash.value, bc), ("debt", bs_debt.value, bd))
    checkable = [(n, a, b) for n, a, b in legs if a is not None and b is not None]
    if not checkable:
        return Sourced.unknown(note="coherence: BS & bridge cash/debt absent — not cross-checked")
    absent = [n for n, a, b in legs if a is None or b is None]
    tail = f" ({'/'.join(absent)} not cross-checked — absent, not zero)" if absent else ""
    if any(not close(a, b) for _n, a, b in checkable):
        pairs = "; ".join(f"{n} BS {money(a)} vs bridge {money(b)}" for n, a, b in legs)
        return Sourced.present(
            f"CAVEAT — the two CIQ sources DISAGREE: {pairs}; verify which the verdict should "
            "use — neither is silently preferred.",
            source_ref=src,
        )
    pairs = "; ".join(f"{n} BS {money(a)} / bridge {money(b)}" for n, a, b in checkable)
    return Sourced.present(
        f"{pairs} — reconcile with the implied-valuation bridge{tail}.",
        source_ref=src,
    )


def _financial_summary(bundle: CiqBundle, implied: ImpliedValuation) -> FinancialSummary:
    """(C) The Financial-Summary appendix — annual actuals+estimates (C1/C4), trailing-8-Q (C2), the
    balance-sheet posture (C3), and the BS↔bridge coherence gate. Estimate columns inherit the
    catalyst as-of (header > sidecar > floor)."""
    asof = ciq_sheets.estimates_as_of(bundle)
    annual = ciq_sheets.financial_summary_annual(bundle, as_of=asof.value)
    return FinancialSummary(
        annual=annual,
        quarterly=ciq_sheets.financial_summary_quarterly(bundle),
        balance_sheet=ciq_sheets.balance_sheet_posture(bundle),
        coherence=_bs_bridge_coherence(bundle, implied),
        as_of=asof,
        # DERIVED FROM THE TABLE JUST BUILT, not from a second extraction — the two EBITDA rows are
        # only comparable if they came from the same assembly of the same columns.
        ebitda_basis=read_ebitda_basis(annual.value),
    )


def _leverage_survival(quality: Quality, bundle: CiqBundle) -> LeverageSurvival:
    """(B2) One unified leverage & survival block: the name's CIQ NET-debt/EBITDA + the comps
    TOTAL-debt/EBITDA (name vs peer median) side by side, each basis LABELED — no net-vs-total
    mixing; interest coverage + the survival line reused from Quality (moved, not duplicated); the
    S&P-MI credit-health scores. The old Quality leverage lines render from HERE; a pre-B2
    dossier.json falls back to the Quality lines."""
    return LeverageSurvival(
        net_debt_to_ebitda=quality.net_debt_to_ebitda,
        total_debt_to_ebitda=ciq_sheets.comps_total_debt_ebitda(bundle),
        interest_coverage=quality.interest_coverage,
        survival=quality.survival_capacity,
        credit_health=ciq_sheets.credit_health(bundle),
    )


# (F1) Form 4 non-derivative transaction codes: open-market P (purchase) / S (sale) are the
# positioning SIGNAL; A (grant/award) is surfaced as 'grants'; every other non-open-market code
# (M option exercise, F tax withholding, C conversion, G gift, …) is bucketed as 'other' and
# LABELED — never silently dropped (that would misstate the counts). Counts + dates only.
_OPEN_MARKET_CODES = ("P", "S")

#: The COUNT window — unchanged at 182d, because it is not wrong: recent open-market buying after a
#: drawdown is the informative signal for an overshoot screen. It is now STATED on the face of the
#: value, since "sells 0" and "sells 0 in the last 182 days" are different claims.
_INSIDER_WINDOW_DAYS = 182
#: The LAST-OCCURRENCE scan. Not "window-free" — EDGAR's `recent` submissions feed is itself
#: bounded — so the horizon is printed with the answer, and an absence reads "no sale in the 3y
#: scanned" rather than a bare "none". 3y clears the SMPL case (its selling episode is ~21 months
#: back) with margin, at ~2 HTTP calls per filing against a cached, paced client.
_INSIDER_SCAN_DAYS = 1095

#: The dilution-pipeline scan. 3y because an S-3 shelf is effective for three years — a shelf
#: older than the window could not be drawn on today, so the window IS the relevance test, not a
#: budget choice. Shares one bounded, cached submissions read with the Form-4 scan above.
_DILUTION_SCAN_DAYS = 1095
#: Form families, grouped by WHAT THE FILING IS — the groups are the vocabulary of the composed
#: line. Shelf = registered capacity; 424B = a draw against it (the ATM/notes/secondary machinery);
#: S-1/F-1 = fresh registration outside a shelf; S-4 = shares registered to fund an ACQUISITION;
#: S-8 = employee-plan shares, REAL dilution but routine, so it is counted on its own and never in
#: the headline.
#:
#: THE TAXONOMY IS EXPLICIT AND ITS BOUNDARY IS TESTED (review finding, #457). `recent_filings`
#: drops any form not LITERALLY in the tuple, so a form missing here is invisible BEFORE
#: `_dilution_line` runs — and an incomplete list therefore reports a false CLEAN register rather
#: than an under-count, which is the dangerous direction. Two gaps were found:
#:
#: - **MEF variants** (`S-3MEF` etc.) — a Rule 462(b) filing that ADDS securities to an
#:   already-effective registration. Registered capacity by definition; absent from this fleet's
#:   3y window, included because absence from one corpus is not absence from the class.
#: - **S-4 / S-4/A** — measured, and PRESENT: **V carries five in-window** (2026-03-05,
#:   2026-04-06 + three in 2024). Shares issued to a target's holders dilute exactly like a
#:   secondary, so this became its own group rather than a silent omission.
#:
#: A form outside every tuple below is one this block does not claim to see; the completeness
#: pin (`test_the_form_taxonomy_covers_the_registration_families`) is what keeps that list honest.
_DILUTION_SHELF = ("S-3", "S-3/A", "S-3ASR", "S-3MEF", "F-3", "F-3/A", "F-3ASR", "F-3MEF")
_DILUTION_SUPPLEMENT = ("424B1", "424B2", "424B3", "424B4", "424B5", "424B6", "424B7", "424B8")
_DILUTION_FRESH = ("S-1", "S-1/A", "S-1MEF", "F-1", "F-1/A", "F-1MEF")
_DILUTION_MERGER = ("S-4", "S-4/A", "S-4MEF", "F-4", "F-4/A")
_DILUTION_EMPLOYEE = ("S-8", "S-8 POS")


def _dilution_line(filings: list[Filing], reference_date: date) -> tuple[list[Filing], str]:
    """(window-bounded filings, composed line) — the pure half, so tests drive it with REAL
    ``Filing`` objects and no network.

    THE UPPER BOUND IS APPLIED HERE AND STATED, not assumed: ``recent_filings`` takes only a
    ``since`` lower bound, so a filing dated AFTER the record's as-of would otherwise enter the
    counts — the exact post-as-of leak class item 9 measured (NFLX 58 / UBER 91 dates past their
    own reference_date). Every count below is over ``filing_date <= reference_date`` only.

    COUNTS, FORMS AND DATES ONLY — no reading. "2 shelfs + 9 supplements" on FUBO and "no shelf on
    file" on V are the two ends of the same stated fact; which one is a risk is the human's call.
    """
    since = reference_date - timedelta(days=_DILUTION_SCAN_DAYS)
    inwin = sorted(
        (f for f in filings if since <= f.filing_date <= reference_date),
        key=lambda f: f.filing_date, reverse=True)

    def part(forms: tuple[str, ...], label: str) -> str | None:
        hits = [f for f in inwin if f.form in forms]
        if not hits:
            return None
        newest = hits[0].filing_date.isoformat()
        forms_seen = sorted({f.form for f in hits})
        return f"{label} {len(hits)} ({'/'.join(forms_seen)}, last {newest})"

    bits = [p for p in (
        part(_DILUTION_SHELF, "shelf registrations"),
        part(_DILUTION_SUPPLEMENT, "prospectus supplements"),
        part(_DILUTION_FRESH, "fresh registrations"),
        part(_DILUTION_MERGER, "merger registrations"),
    ) if p]
    emp = part(_DILUTION_EMPLOYEE, "employee-plan (S-8)")
    yrs = _DILUTION_SCAN_DAYS // 365
    if not bits and not emp:
        line = (f"no registration statements or prospectus supplements on file in the "
                f"{yrs}y to {reference_date.isoformat()}")
    else:
        head = "; ".join(bits) if bits else "no shelf/supplement/fresh registration"
        tail = f" · {emp} — routine" if emp else ""
        line = f"{head}{tail} — {yrs}y window to {reference_date.isoformat()}"
    return inwin, line


def _dilution_pipeline(
    edgar: EdgarClient, cik: str | None, reference_date: date
) -> DilutionPipeline:
    """FORWARD dilution capacity from the EDGAR filing index — the fetch half.

    "NONE ON FILE" IS PRESENT, NOT UNKNOWN. An empty window is a stated fact about the register
    (no standing capacity), decision-relevant exactly like a never-impaired goodwill balance.
    UNKNOWN is reserved for the states where the register could not be READ — no CIK, or the
    fetch failing — and the two must never render alike."""
    all_forms = (_DILUTION_SHELF + _DILUTION_SUPPLEMENT + _DILUTION_FRESH
                 + _DILUTION_MERGER + _DILUTION_EMPLOYEE)
    if not cik:
        return DilutionPipeline(filings=[], window_days=_DILUTION_SCAN_DAYS,
                                line=Sourced.unknown(note="no CIK for the filing-index lookup"))
    try:
        raw = edgar.recent_filings(
            cik, forms=all_forms,
            since=reference_date - timedelta(days=_DILUTION_SCAN_DAYS))
    except HttpError as exc:
        return DilutionPipeline(
            filings=[], window_days=_DILUTION_SCAN_DAYS,
            line=Sourced.unknown(note=f"EDGAR filing-index fetch failed: {exc}"))
    inwin, line = _dilution_line(raw, reference_date)
    newest = f" · latest {inwin[0].accession}" if inwin else ""
    return DilutionPipeline(
        filings=[RegistrationFiling(form=f.form, filing_date=f.filing_date.isoformat(),
                                    accession=f.accession) for f in inwin],
        window_days=_DILUTION_SCAN_DAYS,
        line=Sourced.present(
            line,
            source_ref=("EDGAR filing index (S-3/F-3 · 424B · S-1/F-1 · S-4 · S-8), window "
                        f"{(reference_date - timedelta(days=_DILUTION_SCAN_DAYS)).isoformat()}"
                        f"→{reference_date.isoformat()}{newest}")))


_OWNERSHIP_SCAN_DAYS = 1095

#: SCHEDULE 13D/G FORM TYPES — BOTH EDGAR VOCABULARIES, and the pairing is the whole point.
#:
#: EDGAR renamed these form types: the same filing is indexed as ``SC 13D`` through 2024 and as
#: ``SCHEDULE 13D`` after. `recent_filings` matches EXACTLY (`form not in forms`), so a list
#: carrying one vocabulary silently drops the other — and because the rename is chronological,
#: the half it drops is the RECENT half, which is the half that decides anything.
#:
#: MEASURED ON THIS FLEET, 3y window: an ``SC 13``-only list sees 153 of 306 filings. AORT reads
#: 0 activist filings instead of 1; FUBO reads 0 instead of 2 — both flip from "no activist
#: interest on file" to having one. That is a false CLEAN, the dangerous direction, exactly as
#: `_DILUTION_SHELF`'s taxonomy note records for the registration families.
#:
#: THE TWO SCHEDULES STAY SEPARATE. 13D = crossed 5% WITH intent to influence (activist/control).
#: 13G = the passive short form (index funds, institutions). Summing them buries 51 activist
#: filings under 430 passive ones fleet-wide.
_OWNERSHIP_ACTIVIST = ("SC 13D", "SC 13D/A", "SCHEDULE 13D", "SCHEDULE 13D/A")
_OWNERSHIP_PASSIVE = ("SC 13G", "SC 13G/A", "SCHEDULE 13G", "SCHEDULE 13G/A")


#: SUBJECT-COMPANY ATTRIBUTION (review of #470). The submissions index is NOT issuer-only: it
#: also returns filings where the company is the REPORTING PERSON on somebody else's stock.
#: Measured on the fleet, UBER's export carries eight such filings — `SCHEDULE 13D/A` 2026-07-08
#: (`0001552781-26-000379`) has issuer **Grab Holdings** and reporting person Uber, as do its
#: Didi / Serve / Aurora siblings. Counted as inbound they said "nine parties are accumulating
#: UBER" when the truth is Uber disclosing stakes it HOLDS. Direction inverted, from real data.
#:
#: THIS IS THE #458 DEFECT AGAIN. The KD export was found "NOT issuer-only" and closed by
#: attribution; the same class was rebuilt here two builds later, because the verification asked
#: whether a COUNT moved and never whose filing it was.
#:
#: THE HEADER INDEX ANSWERS BOTH ERAS, which is why it is used instead of `primary_doc.xml`:
#: that XML exists only on post-2024 filings (101 of 254 in-window filings on this fleet have
#: none), while `<acc>-index-headers.html` carries the `SUBJECT COMPANY` / `FILED BY` blocks for
#: every filing back to the old `SC 13` vocabulary. Verified on both: UBER's new-vocabulary
#: foreign filing resolves to Grab's CIK, AORT's XML-less `SC 13G/A` resolves to AORT's own.
_SUBJECT_CIK_RE = re.compile(r"SUBJECT COMPANY.*?CENTRAL INDEX KEY:\s*(\d+)", re.S)


def _filing_subject_cik(edgar: EdgarClient, subject_cik: str, accession: str) -> str | None:
    """The CIK of the company a 13D/G is ABOUT, or None when the header cannot be read.

    None is UNATTRIBUTABLE and never means "ours" — a fetch failure that defaulted to keeping the
    filing would restore the exact defect this function exists to remove, silently."""
    acc = accession.replace("-", "")
    url = (f"https://www.sec.gov/Archives/edgar/data/{int(subject_cik)}/{acc}/"
           f"{accession}-index-headers.html")
    try:
        m = _SUBJECT_CIK_RE.search(edgar._http.get_text(url, ttl_seconds=86_400))
    except (HttpError, ValueError):
        return None
    return m.group(1).lstrip("0") if m else None


def _ownership_line(filings: list[Filing], reference_date: date) -> tuple[list[Filing], str]:
    """(window-bounded filings, composed line) — the pure half, driven in tests by REAL ``Filing``
    objects with no network.

    THE UPPER BOUND IS APPLIED HERE, not assumed: ``recent_filings`` takes only a ``since`` lower
    bound, so a filing dated after the record's as-of would otherwise enter the counts — the same
    post-as-of leak class item 9 measured. Every count below is over
    ``filing_date <= reference_date`` only.

    IT COUNTS FILINGS, AND SAYS SO — never holders, and never a direction of travel. Two things
    the index cannot support were asserted here and are now removed (review of #470):

    * **"activist/control" was inferred from the form type alone.** A 13D/A is how a position
      CHANGES, and the change can be an EXIT — AORT's single in-window filing is exactly such an
      `/A`. Reading "activist stake" off the form would print a departure as an arrival. The
      label now names the SCHEDULE and stops there; what the filing says is the human's to read.
    * **A count of FILINGS is not a count of HOLDERS.** Amendments are deliberately included, so
      three holders filing six annual `/A`s each would have printed as "21 holders". The label
      says filings because filings are what was counted.

    Amendments stay counted — a name with one 13D and fifteen amendments has an active
    situation, not a stale one — but the forms are listed so the human sees which it was."""
    since = reference_date - timedelta(days=_OWNERSHIP_SCAN_DAYS)
    inwin = sorted(
        (f for f in filings if since <= f.filing_date <= reference_date),
        key=lambda f: f.filing_date, reverse=True)

    def part(forms: tuple[str, ...], label: str) -> str | None:
        hits = [f for f in inwin if f.form in forms]
        if not hits:
            return None
        forms_seen = sorted({f.form for f in hits})
        last = hits[0].filing_date.isoformat()
        return f"{label} {len(hits)} ({'/'.join(forms_seen)}, last {last})"

    activist = part(_OWNERSHIP_ACTIVIST, "Schedule 13D filings")
    passive = part(_OWNERSHIP_PASSIVE, "Schedule 13G filings")
    yrs = _OWNERSHIP_SCAN_DAYS // 365
    if activist is None and passive is None:
        line = (f"no Schedule 13D/G beneficial-ownership filings in the {yrs}y to "
                f"{reference_date.isoformat()}")
    else:
        head = activist or "no 13D on file"
        tail = f" · {passive}" if passive else " · no 13G on file"
        line = f"{head}{tail} — {yrs}y window to {reference_date.isoformat()}"
    return inwin, line


def _ownership_events(
    edgar: EdgarClient, cik: str | None, reference_date: date
) -> OwnershipEvents:
    """Schedule 13D/G beneficial ownership from the EDGAR filing index — the fetch half.

    "NONE IN WINDOW" IS PRESENT, NOT UNKNOWN. Eight of this fleet's 14 names carry no 13D in
    window; that is a stated fact about who is accumulating, decision-relevant exactly like an
    empty shelf register. UNKNOWN is reserved for the states where the register could not be READ
    — no CIK, or the fetch failing — and the two must never render alike.

    KNOWN LIMIT, STATED RATHER THAN GUARDED: `recent_filings` reads only the submissions index's
    ``recent`` block, which EDGAR caps (~1000 filings) and paginates the overflow. Every name on
    this fleet reaches back past the 3y window today, so the counts are complete — but NFLX's
    index reaches only 2023-06 against a 2023-08 window start, roughly two months of headroom, so
    a heavy filer WILL eventually under-count. No guard is shipped because none can be shown
    firing on the live corpus; recorded in STATE with its unlock (read ``filings.files`` overflow
    pages) rather than built speculatively."""
    since = reference_date - timedelta(days=_OWNERSHIP_SCAN_DAYS)
    if not cik:
        return OwnershipEvents(filings=[], window_days=_OWNERSHIP_SCAN_DAYS,
                               line=Sourced.unknown(note="no CIK for the filing-index lookup"))
    try:
        raw = edgar.recent_filings(
            cik, forms=_OWNERSHIP_ACTIVIST + _OWNERSHIP_PASSIVE, since=since)
    except HttpError as exc:
        return OwnershipEvents(
            filings=[], window_days=_OWNERSHIP_SCAN_DAYS,
            line=Sourced.unknown(note=f"EDGAR filing-index fetch failed: {exc}"))
    # ATTRIBUTE BEFORE COUNTING. A filing this company FILED on somebody else's stock is not a
    # fact about this company's register, and counting it inverts the direction (see
    # `_filing_subject_cik`). Unattributable filings are dropped from the counts AND reported, so
    # a header that could not be read shortens the count visibly rather than silently.
    own: list[Filing] = []
    unattributed = 0
    for f in raw:
        if f.filing_date > reference_date:
            continue
        subject = _filing_subject_cik(edgar, cik, f.accession)
        if subject is None:
            unattributed += 1
        elif subject == str(int(cik)):
            own.append(f)
    inwin, line = _ownership_line(own, reference_date)
    if unattributed:
        line += (f" · {unattributed} filing(s) not attributable — subject company unread, "
                 f"excluded from the counts")
    newest = f" · latest {inwin[0].accession}" if inwin else ""
    return OwnershipEvents(
        filings=[OwnershipFiling(form=f.form, filing_date=f.filing_date.isoformat(),
                                 accession=f.accession) for f in inwin],
        window_days=_OWNERSHIP_SCAN_DAYS,
        line=Sourced.present(
            line,
            source_ref=("EDGAR filing index (SC 13D/G + SCHEDULE 13D/G — both vocabularies), "
                        f"window {since.isoformat()}→{reference_date.isoformat()}{newest}")))


#: SBC comes from ONE tag — measured, not assumed: `ShareBasedCompensation` answers on all 14
#: names, so no fallback taxonomy is invented for a gap that does not exist here. If a future
#: name misses it the block says UNKNOWN rather than reaching for a near-synonym that may mean
#: something else (`AllocatedShareBasedCompensationExpense` is a segment allocation, not the total).
_SBC_TAG = "ShareBasedCompensation"

#: REVENUE FOR THE SBC WINDOW. Ordered most-specific first. The ratio is only ever formed from a
#: fact whose period matches the SBC fact EXACTLY, so this list decides which tag answers, never
#: which period — a tag missing here yields UNKNOWN, never a silently different window.
_SBC_REVENUE_TAGS = ("RevenueFromContractWithCustomerExcludingAssessedTax",
                     "RevenueFromContractWithCustomerIncludingAssessedTax",
                     "Revenues", "SalesRevenueNet")


#: An ANNUAL period, in days. FUBO carries a `form=10-K`, `fp=FY` SBC fact spanning
#: 2009-02-20→2012-09-30 — **1,318 days**. Rendering that as "FY" would put a three-year stub
#: beside genuine annual intensities as if comparable, so duration is checked rather than trusted.
_SBC_ANNUAL_DAYS = (330, 400)


def _sbc_annual(node: dict[str, Any], reference_date: date) -> list[dict[str, Any]]:
    """The 10-K annual facts KNOWABLE at the as-of, newest period first.

    **BOUNDED ON `filed`, NOT ONLY ON `end`** (review of #471, and the #416/#426 lookahead class).
    A period ending before the as-of can be RESTATED long after it: FUBO's FY2021 SBC is
    $63,796,000 as filed 2022-03-01 and $53,150,000 as restated in the 2023 and 2024 10-Ks. An
    `end`-only bound hands a 2022-06-01 record the 2024 filing's number — 17% off, from data that
    did not exist at the as-of. Both the numerator and the denominator are bounded here."""
    out = []
    for x in node.get("units", {}).get("USD", []):
        if x.get("form") != "10-K" or not x.get("start") or not x.get("end"):
            continue
        filed = x.get("filed")
        if filed and date.fromisoformat(str(filed)) > reference_date:
            continue
        start, end = date.fromisoformat(str(x["start"])), date.fromisoformat(str(x["end"]))
        if end > reference_date:
            continue
        if not _SBC_ANNUAL_DAYS[0] <= (end - start).days <= _SBC_ANNUAL_DAYS[1]:
            continue
        out.append(x)
    return out


def _sbc_pick(cands: list[dict[str, Any]]) -> tuple[float, str, str] | None:
    """(value $M, start, end) for the newest period — or None when it is genuinely ambiguous.

    RESTATEMENT IS A VINTAGE, NOT A TIE. Several 10-K facts for one period are the SAME number
    restated, so the as-of-correct answer is the LATEST FILED one still inside the bound — not a
    refusal, and emphatically not `[-1]` of the API array, which is what the first cut used: a
    stable sort on `end` alone left the winner to array order while the denominator refused the
    identical ambiguity three lines below.

    Only a same-period, SAME-FILED disagreement is irreducible; that refuses."""
    if not cands:
        return None
    end = max(str(x["end"]) for x in cands)
    same_period = [x for x in cands if str(x["end"]) == end]
    newest_filed = max(str(x.get("filed") or "") for x in same_period)
    winners = [x for x in same_period if str(x.get("filed") or "") == newest_filed]
    vals = {round(float(x["val"]), 2) for x in winners}
    if len(vals) > 1:
        return None
    w = winners[-1]
    return float(w["val"]) / 1e6, str(w["start"]), str(w["end"])


def _sbc_line(facts: dict[str, Any], reference_date: date) -> SbcLine | None:
    """SBC as $ and as % of revenue over the SAME window — the pure half, driven in tests by a
    real companyfacts-shaped dict and no network.

    THE WINDOW IS THE WHOLE POINT. The first cut took each name's latest 10-K SBC and divided by
    the dossier's LTM revenue. FUBO's latest SBC is FY2024 while its LTM revenue is post-merger,
    so it read 0.7% against a true FY2024 ratio of 2.6% — understated 3.7x, and confidently,
    because both inputs were individually correct. The revenue fact is matched on the SBC fact's
    exact ``start``/``end``; nothing else is eligible.

    SAME WINDOW IS NECESSARY, NOT SUFFICIENT — SAME BASIS TOO. FUBO carries TWO revenue facts for
    2024-01-01→2024-12-31: $1,622.8M from the 10-K (``fp=FY``) and $402.3M from a 10-Q (``fp=Q1``,
    ``frame=CY2024``) whose period STRING looks annual. Both sides now run through
    ``_sbc_annual``, so the form, the duration and the as-of bound are identical by construction."""
    gaap = (facts.get("facts") or {}).get("us-gaap") or {}
    if _SBC_TAG not in gaap:
        return None
    picked = _sbc_pick(_sbc_annual(gaap[_SBC_TAG], reference_date))
    if picked is None:
        return None
    usd, start, end = picked

    rev: float | None = None
    rev_tag = ""
    ambiguous = False
    for tag in _SBC_REVENUE_TAGS:
        node = gaap.get(tag)
        if not node:
            continue
        same = [x for x in _sbc_annual(node, reference_date)
                if str(x["start"]) == start and str(x["end"]) == end]
        if not same:
            continue
        rev_tag = tag
        got = _sbc_pick(same)
        if got is None:
            ambiguous = True     # same period, same filing date, different values
        else:
            rev = got[0]
        break

    src = f"EDGAR XBRL {_SBC_TAG} (10-K, {start}→{end})"
    if rev is None or rev <= 0:
        why = (f"two {rev_tag} facts cover {start}→{end} with the same filing date and different "
               "values — the denominator is irreducibly ambiguous, so no ratio is formed"
               if ambiguous else
               f"no 10-K revenue fact covers {start}→{end} — the SBC window has no matching "
               "denominator, so no ratio is formed rather than one across two periods")
        pct = Sourced[float].unknown(note=why)
        line = f"stock-based compensation ${usd:,.1f}M (FY to {end}) · % of revenue UNKNOWN"
    else:
        pct = Sourced.present(100.0 * usd / rev, source_ref=f"{src} ÷ {rev_tag} (same window)")
        line = (f"stock-based compensation ${usd:,.1f}M = {100.0 * usd / rev:.1f}% of revenue "
                f"(${rev:,.1f}M, FY {start}→{end})")
    return SbcLine(expense=Sourced.present(usd, source_ref=src), pct_revenue=pct,
                   window_start=start, window_end=end,
                   line=Sourced.present(line, source_ref=src))


def _sbc(edgar: EdgarClient, cik: str | None, reference_date: date) -> SbcLine | None:
    """The fetch half. A FAILED READ IS UNKNOWN, NEVER AN ABSENT BLOCK (review of #471).

    `sbc` is registered in `_DROP_WHEN_NONE`, so returning None on a transient 503 would strip the
    line from the page AND the JSON — indistinguishable in the artifact diff from a company that
    genuinely reports no SBC. `_ownership_events` states this rule in its own docstring; this
    function contradicted it. None is reserved for "no SBC tag in the taxonomy at all"."""
    if not cik:
        return None
    try:
        raw = edgar.companyfacts(cik)
    except (HttpError, KeyError) as exc:
        note = f"EDGAR companyfacts fetch failed: {exc}"
        return SbcLine(expense=Sourced[float].unknown(note=note),
                       pct_revenue=Sourced[float].unknown(note=note),
                       window_start="", window_end="",
                       line=Sourced[str].unknown(note=note))
    return _sbc_line(raw, reference_date)


class Form4Line(NamedTuple):
    """ONE non-derivative Form 4 transaction, with everything a window-free read needs.

    CARRIES ITS OWN DATE, PRICE AND PERSON because a windowed COUNT mostly reports the window: for a
    sparse series the informative statement is *when the last one was*, not how many fell inside an
    arbitrary 182 days. `who` is the reporting owner's CIK, never the printed name — the same
    person is spelled inconsistently across filings ("SCALZO JOSEPH" vs "Scalzo Joseph E."), so a
    name-keyed count of PEOPLE would over-report.
    """

    code: str
    shares: float
    price: float
    on: date | None
    who: str
    role: str

    @property
    def usd(self) -> float | None:
        """Dollar value, or None when the filing states no price. A `G` (gift) or `A` (grant)
        carries shares at no price; multiplying by a defaulted 0.0 would report a real transfer as
        a $0 event, which reads as *nothing happened*."""
        return self.shares * self.price if self.price else None


def _form4_codes(
    http: CachedHttp, cik: str, accession: str, filed: date | None = None
) -> list[Form4Line]:
    """Every non-derivative transaction in ONE Form 4 — parsed from the raw ownership XML (never
    the xsl-styled view). Returns [] when the filing has no non-deriv table or its doc can't be
    fetched (fail-soft per filing; the block still assembles from the rest)."""
    accn = accession.replace("-", "")
    try:
        idx = http.get_json(_INDEX.format(cik=int(pad_cik(cik)), acc=accn), ttl_seconds=None)
    except (HttpError, ValueError):
        return []
    names = [str(it.get("name", "")) for it in idx.get("directory", {}).get("item", [])]
    xmlname = next(
        (n for n in names if n.lower().endswith(".xml") and "ownership" in n.lower()),
        next((n for n in names if n.lower().endswith(".xml")), None),
    )
    if not xmlname:
        return []
    try:
        raw = http.get_text(
            _ARCHIVE.format(cik=int(pad_cik(cik)), acc=accn, doc=xmlname), ttl_seconds=None)
        root = ET.fromstring(raw)
    except (HttpError, ET.ParseError, ValueError):
        return []
    owner = root.find(".//reportingOwner")
    rel = owner.find("reportingOwnerRelationship") if owner is not None else None

    def owner_text(node: ET.Element | None, path: str) -> str:
        return (node.findtext(path) or "").strip() if node is not None else ""

    who = owner_text(owner, "reportingOwnerId/rptOwnerCik")
    # ROLE, in decision-relevance order. `officerTitle` is FREE TEXT and EDGAR's own placeholder
    # "See Remarks" appears in it — AORT printed `last buy $0.26M, See Remarks, …` on the first
    # real run, machine dialect reaching the page. A placeholder is not a role, so it falls through.
    # `isTenPercentOwner` is separated from the generic "insider" because it changes what a large
    # sale MEANS: CNXC's 6,000,000 sh @ $22.25 = $133.5M on 2026-04-29 is a block holder
    # distributing, which a reader must not confuse with management selling.
    title = owner_text(rel, "officerTitle")
    if title.lower().strip(" .") in ("see remarks", "see remark", "n/a", "na", "-", ""):
        title = ""
    role = title or (
        "director" if owner_text(rel, "isDirector") in ("1", "true")
        else "10% owner" if owner_text(rel, "isTenPercentOwner") in ("1", "true")
        else "insider")
    out: list[Form4Line] = []
    for t in root.findall(".//nonDerivativeTransaction"):
        code = (t.findtext(".//transactionCoding/transactionCode") or "").strip()
        sh = t.findtext(".//transactionAmounts/transactionShares/value")
        px = t.findtext(".//transactionAmounts/transactionPricePerShare/value")
        raw_on = (t.findtext(".//transactionDate/value") or "").strip()
        try:
            on = date.fromisoformat(raw_on) if raw_on else None
        except ValueError:                       # pragma: no cover - malformed filing
            on = None
        # FALL BACK TO THE FILING DATE — a dateless transaction must NEVER VANISH. The first cut
        # filtered the window on `on is not None`, and a real fixture whose `S` line carries no
        # `<transactionDate>` silently became `sells 0`: a sale disappearing from the count, in the
        # flattering direction, inside the change written to stop exactly that. Section 16 requires
        # filing within two business days, so the filing date bounds the transaction date tightly
        # enough for a 182-day window and a "~Nmo ago".
        on = on or filed
        if code:
            out.append(Form4Line(code, float(sh) if sh else 0.0, float(px) if px else 0.0,
                                 on, who or accession, role))
    return out


def _insider_activity(
    edgar: EdgarClient, http: CachedHttp, cik: str | None, reference_date: date
) -> Sourced[str]:
    """(F1) Insider activity from EDGAR Form 4 — open-market P/S counts over a STATED window, plus
    the LAST buy and LAST sale over a longer stated scan. Counts and dates ONLY (no
    interpretation), source-bound to the latest accession; fail-loud UNKNOWN when none are on file.

    TWO HORIZONS, BOTH PRINTED, AND THAT IS THE POINT. The 182-day window is not wrong — it showed
    $1.11M of buying by two insiders after a crash, which is the informative signal for an
    overshoot screen. What it cannot say is that the same people sold $24.7M twenty-one months
    earlier, and **the omission ran in the flattering direction**: the page showed the buying and
    hid the selling. A windowed count on a sparse series mostly reports the window, so the last
    occurrence is reported ALONGSIDE it — window-free, and comparable across names in a way a
    windowed count is not.

    NEVER NETTED. `P` and `S` are reported as separate sides with their own counts, people and
    dollars. Netting $1.1M of buying against $12.4M of selling yields −$11.3M, which is less
    informative than the $1.1M alone — it destroys the informative half with the noisy half. The
    old form printed exactly that net; it was latent rather than live only because no sale fell
    inside the window.

    `F` (shares withheld for tax on vesting) IS NOT A SALE and never enters the sell side — it is a
    withholding event with no decision in it. Measured on SMPL: F is $1.24M against $24.72M of real
    sales, ~5% of dispositions, so the contamination is small AND excluded.
    """
    if not cik:
        return Sourced.unknown(note="no CIK for Form 4 lookup")
    try:
        filings = edgar.recent_filings(
            cik, forms=("4",), since=reference_date - timedelta(days=_INSIDER_SCAN_DAYS))
    except HttpError as exc:
        return Sourced.unknown(note=f"EDGAR Form 4 fetch failed: {exc}")
    if not filings:
        return Sourced.unknown(
            note=f"no Form 4 filings in the {_INSIDER_SCAN_DAYS // 365}y scanned")
    lines: list[Form4Line] = []
    for f in filings:
        lines.extend(_form4_codes(http, cik, f.accession, f.filing_date))
    return Sourced.present(
        compose_insider_line(lines, reference_date=reference_date,
                             last_filing=max(f.filing_date for f in filings)),
        source_ref=(f"EDGAR Form 4 (latest {filings[0].accession}; {len(filings)} filings in "
                    f"the {_INSIDER_SCAN_DAYS}d scanned; counts over {_INSIDER_WINDOW_DAYS}d)"))


def compose_insider_line(
    lines: list[Form4Line], *, reference_date: date, last_filing: date
) -> str:
    """The insider line, as a PURE function of parsed Form 4 rows.

    SPLIT OUT SO IT IS TESTABLE WITHOUT EDGAR. `_insider_activity` is a network path, so pinning
    its behaviour previously meant either a hand-rolled stub (the house rule forbids it: fixtures
    are built from the REAL type) or no pin at all. Every rule this line encodes — the window is
    stated, the sides are never netted, absence carries its horizon, the largest is reported when
    it is not the last — is a behaviour a reader depends on, so each gets a red.
    """
    win_start = reference_date - timedelta(days=_INSIDER_WINDOW_DAYS)
    win = [ln for ln in lines if ln.on is not None and ln.on >= win_start]

    def side(code: str) -> str:
        """One side of the window, NEVER netted against the other. $1.1M of buying against $12.4M
        of selling nets to −$11.3M, which is LESS informative than the $1.1M alone: netting
        destroys the informative half with the noisy half. Counts and PEOPLE travel with the
        dollars — one insider selling $12M is a different fact from six selling $2M."""
        rows = [ln for ln in win if ln.code == code]
        if not rows:
            return "0"
        usd = sum(x for ln in rows if (x := ln.usd) is not None)
        people = len({ln.who for ln in rows})
        return (f"{len(rows)} ({people} insider{'s' if people != 1 else ''}"
                + (f", ${usd / 1e6:.2f}M)" if usd else ")"))

    def _amount(ln: Form4Line) -> str:
        return f"${ln.usd / 1e6:.2f}M, " if ln.usd else ""

    def _event(ln: Form4Line, label: str) -> str:
        assert ln.on is not None
        months = round((reference_date - ln.on).days / 30.44)
        return f"{label} {_amount(ln)}{ln.role}, {ln.on.isoformat()} (~{months}mo ago)"

    def occurrences(code: str, label: str) -> str:
        """THE LAST AND THE LARGEST — the statements a windowed count cannot make. For a sparse
        series a count mostly reports the WINDOW: SMPL's "sells 0" is true of 182 days and false of
        21 months, and the omission runs in the flattering direction.

        BOTH, BECAUSE THE FIRST REAL RUN PROVED "LAST" ALONE REPRODUCES THE DEFECT. SMPL's most
        recent sale is $0.11M nine months back; printing only that states a trivial last sale and
        implies it is all there is, while the $24.7M episode 21 months back stays hidden — a
        smaller number in the SAME flattering direction as the count it replaced. The largest is
        omitted only when it IS the last, so the common case stays one clause.

        Absence carries its horizon — "no sale in the 3y scanned", never a bare "none", because
        this scan is bounded (EDGAR's `recent` feed is finite) and an unqualified absence would be
        the visible-absence rule broken by the fix written to honour it."""
        rows = [ln for ln in lines if ln.code == code and ln.on is not None]
        if not rows:
            return f"no {label} in the {_INSIDER_SCAN_DAYS // 365}y scanned"
        latest = max(rows, key=lambda r: r.on or date.min)
        out = _event(latest, f"last {label}")
        biggest = max(rows, key=lambda r: r.usd or 0.0)
        # SUPPRESSED WHEN IT RENDERS THE SAME. AORT's two largest buys differ by cents and both
        # print "$0.26M", so the second clause repeated a number the reader cannot tell apart —
        # noise dressed as a finding. Compared at the PRECISION SHOWN, not the underlying float.
        if biggest is not latest and _amount(biggest) != _amount(latest):
            out += f" · largest {label} " + _event(biggest, "").lstrip()
        return out

    counts: dict[str, int] = {}
    for ln in lines:
        counts[ln.code] = counts.get(ln.code, 0) + 1
    # (H5) PLAIN LABELS, sign-descriptors only — no interpretive language. THE WINDOW IS STATED ON
    # THE FACE OF EVERY COUNT THAT KEEPS ONE: "sells 0" and "sells 0 in the last 182 days" are
    # different claims, and only the second is one a reader can act on. 'grants' = the A code;
    # option-exercise (M) / tax-withheld (F) / conversions (C) stay under 'other', which MUST
    # REMAIN LAST — `render._fmt_insider` matches it with a `$`-anchored regex and silently leaves
    # raw machine dialect on the page if anything follows it.
    line = (f"Open-market buys {side('P')} · sells {side('S')} "
            f"— in the last {_INSIDER_WINDOW_DAYS} days · "
            f"{occurrences('P', 'purchase')} · {occurrences('S', 'sale')} · "
            f"grants {counts.get('A', 0)} · last filing {last_filing}")
    other = "/".join(
        f"{c}×{n}" for c, n in sorted(counts.items())
        if c not in _OPEN_MARKET_CODES and c != "A" and n
    )
    if other:
        line += f" · other {other}"
    return line


def _short_interest(
    finra: CachedHttp, record: DataRecord, reference_date: date, *, shares_out: float | None = None
) -> Sourced[str]:
    """(F2/H5) Latest FINRA settlement short interest, sign-descriptors only: prior → latest with a
    rising/falling trend + FINRA's own Δ%, the % of shares out (EDGAR XBRL count), days-to-cover vs
    the SCREEN 90d ADV, and the latest-4 settlements as a mini-row. No interpretation — a cross-
    reference for the human, never a conclusion; fail-loud UNKNOWN when no settlement is on file."""
    symbol = record.identity.ticker
    try:
        points = short_interest_points(
            finra, symbol, start=reference_date - timedelta(days=120), end=reference_date)
    except (HttpError, FinraLayoutError) as exc:
        return Sourced.unknown(note=f"FINRA short interest unavailable: {exc}")
    if not points:
        return Sourced.unknown(note="no FINRA short-interest settlement in the trailing window")
    latest = points[0]
    prior = points[1] if len(points) > 1 else None
    # (H5) prior → latest with a rising/falling sign-descriptor (a plain comparison, not a verdict)
    if prior is not None:
        trend = ("rising" if latest.shares_short > prior.shares_short
                 else "falling" if latest.shares_short < prior.shares_short else "flat")
        line = f"{prior.shares_short / 1e6:.1f}M → {latest.shares_short / 1e6:.1f}M sh"
        pct = f"{latest.change_percent:+.1f}%, " if latest.change_percent is not None else ""
        line += f" ({pct}{trend})"
    else:
        line = f"{latest.shares_short / 1e6:.1f}M sh"
        if latest.change_percent is not None:
            line += f" ({latest.change_percent:+.1f}%)"
    if shares_out and shares_out > 0:  # (H5) % of shares out, EDGAR XBRL count (omitted if absent)
        line += f" · {latest.shares_short / shares_out * 100:.1f}% of shares out (EDGAR XBRL)"
    adv = record.prices.adv_90d_shares
    if adv.coverage_status is CoverageStatus.PRESENT and adv.value:
        line += f" · DTC {latest.shares_short / adv.value:.1f}d"
        basis = f"DTC = {latest.shares_short:,} short ÷ {adv.value:,.0f} screen 90d ADV"
    else:
        basis = "screen 90d ADV unavailable — DTC omitted"
    # (H5) latest-4 settlements mini-row (dates + shares) — the recent trend, source-bound
    mini = " · ".join(f"{pt.settlement_date} {pt.shares_short / 1e6:.1f}M" for pt in points[:4])
    return Sourced.present(
        f"Short interest (FINRA, settle {latest.settlement_date}): {line} · recent: {mini}",
        source_ref=f"FINRA consolidated short interest (settle {latest.settlement_date}); {basis}")


#: How old the cover-page share count may be before it stops being a CURRENT count.
#:
#: NOT A PRECISION BOUND — a count a few quarters old is merely imprecise, and buybacks move it
#: slowly. This is a MAINTENANCE signal: an active filer tags this on every 10-Q and 10-K, so a
#: newest fact older than this means the filer STOPPED reporting it undimensioned, and what comes
#: back is not a stale number but a different era's number.
#:
#: 540 DAYS, SET AGAINST THE MEASURED FLEET, not picked round. The twelve committed names' counts
#: run 10–375 days old (FUBO oldest at 375, its record sealed); Visa's newest undimensioned fact is
#: ~6,040 days old. The bound clears the fleet's maximum by 165 days and still catches the case it
#: exists for by more than a decade, so it changes no existing name — verified by re-deriving all
#: twelve before and after.
#: How old a cover-page share count may be before it is REFUSED as a different share basis.
#:
#: 180 DAYS, AND THE PREVIOUS 540 IS WHY (2026-08-12). The bound was first set to clear the whole
#: committed fleet, whose counts ran 10–375 days old — but the 375 was FUBO, and FUBO is exactly the
#: name the bound needed to catch. It went dual-class in the intervening year (10-Q of 2026-08-05
#: states 30,204,277 Class A and 78,992,518 Class B), the undimensioned `dei` tag stopped being
#: populated at 2025-07-31, and the extractor kept serving that final single-class total of
#: 342,433,118. Divided into a Class-A-basis CIQ cap of $256.4M it implied $0.75/sh against an
#: $8.33 close — an 11.1x error, and `reconcile_cap` reads it as a corporate action, which it is.
#: So the bound was accommodating the defect it existed to prevent: Visa's 16 YEARS was caught and
#: FUBO's ONE was not, though both are the same thing — a filer that moved to per-class tagging.
#:
#: 180 is two quarters. A cover-page count is restated in every 10-Q, so two quarters of silence
#: means the tag stopped being maintained, not that the filer is slow. Measured rather than assumed:
#: on the committed fixtures the healthy names run 10–101 days (AORT/WERN at 101) and the next value
#: is FUBO's 375 — an empty band between them, so this sits 1.8x above the fleet and 2.1x below the
#: defect. Face-validity, not a number tuned to an outcome.
_SHARES_MAX_AGE_DAYS = 180

#: The same bound for a filer that reports ANNUALLY — a foreign private issuer on Form 20-F (or a
#: Canadian one on 40-F). This is the pre-2026-08-12 value, kept for exactly the population it was
#: safe for.
#:
#: 180 DAYS IS A 10-Q CADENCE, AND ASSUMING IT GLOBALLY BREAKS A REAL NAME (review finding, #432).
#: A 20-F filer restates its cover-page count ONCE a year and may file up to four months after its
#: fiscal year end, so a perfectly current count is routinely 181–365+ days old. Measured on our own
#: universe rather than argued: **ONON (On Holding, Swiss) files 20-F and 6-K and NO 10-Q**, and its
#: dei count is dated 2025-12-31 — **224 days** at a 2026-08-12 reference. A flat 180 would REFUSE a
#: current fact and strip its per-share and EV figures, usually to an unavailable CIQ bridge. The
#: defect this bound exists for is unaffected: FUBO (377d) files 10-Q so still gets 180, and Visa
#: (6,041d) is caught by either.
#: 540 = one annual cycle (365) + the 4-month FPI filing window + margin, and still 11x tighter than
#: Visa's gap.
_SHARES_MAX_AGE_ANNUAL_DAYS = 540


def _shares_max_age(edgar: EdgarClient, cik: str | None, as_of: date) -> int:
    """How stale a cover-page share count may be, given how often this filer actually reports.

    QUARTERLY IS THE STRICT DEFAULT, INCLUDING WHEN THE LOOKUP FAILS, and the asymmetry is
    deliberate: refusing a good count yields UNKNOWN, which is honest and recoverable; accepting a
    stale one puts a wrong share basis behind every per-share and EV figure on the page, which is
    the ~4x Visa error and the 11.1x FUBO one. When we cannot establish the cadence we take the
    tighter bound.

    A filer is treated as ANNUAL only on positive evidence — a 20-F/40-F on file and no 10-Q in the
    same window. The window is three years so a name that changed status is judged on its recent
    behaviour, not on one old filing.
    """
    if not cik:
        return _SHARES_MAX_AGE_DAYS
    try:
        recent = edgar.recent_filings(
            cik, forms=("10-Q", "20-F", "40-F"), since=as_of - timedelta(days=3 * 365))
    except Exception:
        return _SHARES_MAX_AGE_DAYS      # cadence unknown ⇒ the strict bound, never the loose one
    forms = {f.form for f in recent}
    annual_only = bool(forms & {"20-F", "40-F"}) and "10-Q" not in forms
    return _SHARES_MAX_AGE_ANNUAL_DAYS if annual_only else _SHARES_MAX_AGE_DAYS


def _edgar_shares_outstanding(
    edgar: EdgarClient, cik: str | None, *, as_of: date | None = None
) -> float | None:
    """(H5) Latest EDGAR XBRL shares outstanding (dei cover-page, us-gaap fallback), or None when
    absent OR STALE — the denominator for short interest as a % of shares out, and the share basis
    the cap reconciliation tests (never faked when missing).

    STALENESS IS REFUSAL, NOT A CAVEAT, and Visa is why. Visa stopped tagging the undimensioned
    ``dei:EntityCommonStockSharesOutstanding`` after 2010 — it reports per share CLASS, which this
    API view does not surface — so the newest fact available is 469,280,842 shares dated
    2010-01-27. That is not merely old: Visa split 4-for-1 in March 2015, so the count is from a
    different share basis entirely, and every per-share and EV figure built on it is wrong by ~4x.
    Returning it "with a note" would put that number on the page; returning None hands the caller
    the chance to bridge to a basis that agrees with the cap, or to say UNKNOWN.

    ``as_of`` defaults to today only so existing callers keep working; assembly passes its
    reference date so a build is reproducible rather than clock-dependent."""
    facts = _companyfacts_or_none(edgar, cik)
    if not facts:
        return None
    pt = latest_instant(extract_points(facts, "shares"))
    if pt is None:
        return None
    end = getattr(pt, "period_end", None)
    ref = as_of or date.today()
    if isinstance(end, date) and ref - end > timedelta(days=_shares_max_age(edgar, cik, ref)):
        return None
    return pt.value


def _catalyst_path(
    bundle: CiqBundle,
    reference_date: date,
    *,
    insider_activity: Sourced[str] | None = None,
    short_interest: Sourced[str] | None = None,
) -> CatalystPath:
    """Assemble the horizon-matched estimates/guidance/revision view from the five new Estimates
    sheets. The workbook as-of (freshest embedded data date) is resolved ONCE and threaded into
    every sub-field's source_ref. Each sub-field independently reads UNKNOWN/MISSING when its sheet
    is absent — a FRESH assembly always builds the block; raggedness lives one level down. The (F)
    positioning inputs are assembled upstream (they need EDGAR/FINRA + the record), slotted in."""
    asof = ciq_sheets.estimates_as_of(bundle)
    aod = asof.value
    return CatalystPath(
        as_of=asof,
        horizon_read=ciq_sheets.horizon_read(bundle, as_of=aod),
        acceleration_read=ciq_sheets.acceleration_read(bundle, as_of=aod),
        cross_name_anchor=ciq_sheets.cross_name_anchor(bundle, as_of=aod),
        guidance_bridge=ciq_sheets.guidance_bridge(
            bundle, as_of=aod, reference_date=reference_date, stale_after_days=_STALE_CLOSE_DAYS
        ),
        guidance_bridge_rows=ciq_sheets.guidance_bridge_rows(
            bundle, reference_date=reference_date, stale_after_days=_STALE_CLOSE_DAYS
        ),
        revision_events=ciq_sheets.revision_events(bundle, as_of=aod),
        consensus_stats=ciq_sheets.consensus_stats(bundle, as_of=aod),
        insider_activity=insider_activity,
        short_interest=short_interest,
    )


# --- (catalyst calendar, ratified 2026-07-24) dated events + what each tests ---------------------
# Face-validity constants (never outcome-tuned): a print rhythm needs ≥4 results 8-Ks to call;
# a sane quarterly gap sits in 60..120d (an irregular filer → REFUSE, never guess); maturities
# make the calendar when they fall within ~24 months of the reference date.
_CAL_MIN_PRINTS = 4
_CAL_GAP_DAYS = (60, 120)
_CAL_MATURITY_HORIZON_DAYS = 730


def _next_print_estimate(print_dates: list[date], ref: date) -> tuple[date, str] | None:
    """CADENCE-ESTIMATE of the next results print from the filer's OWN 2.02-8-K history: the
    median inter-print gap (≥ ``_CAL_MIN_PRINTS`` prints, gap within ``_CAL_GAP_DAYS``) rolled
    forward from the last print past ``ref``. None on any doubt — the caller emits a qa_flag and
    NO row (an estimate is labeled; a guess is forbidden)."""
    prints = sorted(set(print_dates))
    if len(prints) < _CAL_MIN_PRINTS:
        return None
    gaps = [(b - a).days for a, b in zip(prints, prints[1:], strict=False)]
    med = statistics.median(gaps)
    if not (_CAL_GAP_DAYS[0] <= med <= _CAL_GAP_DAYS[1]):
        return None  # irregular rhythm — refuse to call it
    step = timedelta(days=round(med))
    est = prints[-1] + step
    while est <= ref:
        est += step
    basis = (f"median {round(med)}d gap over {len(prints)} results 8-Ks; "
             f"last print {prints[-1].isoformat()}")
    return est, basis


# (source D, ratified 2026-07-24) a FORWARD action verb followed within a clause by a month name —
# "will become effective in September", "launching in Q..January 2028". Tight by design (the K6
# precision lesson): past-tense verbs are excluded by the alternation itself ("completed" is not
# "completes|completing"), and a backward reference ("last September") is rejected post-match.
_CAL_MONTHS = {m.lower(): i + 1 for i, m in enumerate(
    ("January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"))}
_CAL_FWD_EVENT = re.compile(
    r"\b(?:effective|launch(?:es|ing)?|open(?:s|ing)?|begin(?:s|ning)?|start(?:s|ing)?|"
    r"roll(?:s|ing)?\s+out|ship(?:s|ping)?|transition(?:s|ing)?|commenc(?:es|ing))\b"
    r"[^.]{0,60}?\b(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\b(?:\s+(\d{4}))?",
    re.IGNORECASE)
_CAL_BACKWARD = re.compile(r"\b(?:last|past|earlier|prior|previous|ago)\b", re.IGNORECASE)


def _dated_operating_events(
    od: OperatingDriversExtract | None, reference_date: date,
) -> list[CatalystRow]:
    """(source D) MANAGEMENT-STATED dated operating events mined from the already-extracted
    driver verbatims — a price increase 'effective in September', a launch, a plant opening.
    Month-granular dates render as YYYY-MM (never a fabricated day). Year resolution when
    unstated: the NEXT occurrence of that month on/after the reference month (a stated month is
    forward-looking by construction of the pattern). Past-resolved events are dropped — a
    calendar lists what is ahead. No match → no row, silently (no event stated is a normal
    state, unlike an unreadable DATE, which flags)."""
    if od is None:
        return []
    rows: list[CatalystRow] = []
    seen: set[tuple[str, str]] = set()
    for r in od.rows:
        text = r.verbatim or ""
        for m in _CAL_FWD_EVENT.finditer(text):
            if _CAL_BACKWARD.search(text[max(0, m.start() - 24):m.end()]):
                continue  # "last September" — a backward reference, not a calendar event
            month = _CAL_MONTHS[m.group(1).lower()]
            if m.group(2):
                year = int(m.group(2))
            else:
                year = reference_date.year + (1 if month < reference_date.month else 0)
            stamp = f"{year:04d}-{month:02d}"
            if stamp < reference_date.strftime("%Y-%m"):
                continue  # resolved to the past — not a calendar row
            # the event text: the CLAUSE carrying the match — from the last comma/semicolon
            # before the match (a long sentence's lead-in is throat-clearing, and a blind
            # 120-char cap was cutting the event itself) to the sentence end, condensed
            lo = text.rfind(". ", 0, m.start())
            lo = lo + 2 if lo != -1 else 0
            hi = text.find(". ", m.end())
            hi = hi if hi != -1 else len(text)
            cl = max(text.rfind(",", lo, m.start()), text.rfind(";", lo, m.start()))
            start = cl + 1 if cl != -1 else lo
            clause = " ".join(text[start:hi].split()).lstrip(",; ")
            event = clause if len(clause) <= 120 else clause[:117].rstrip() + "…"
            key = (stamp, clause[:60].lower())
            if key in seen:
                continue
            seen.add(key)
            rows.append(CatalystRow(
                event=event, expected_date=stamp, date_basis="stated",
                tests_what="a management-stated dated operating action — the thesis mechanism "
                           "on a timetable; the following print reads its result",
                source_ref=r.source_ref))
    return rows


def _catalyst_calendar(
    edgar: EdgarClient, cik: str, reference_date: date, mech: MechanicalLayer,
) -> CatalystCalendar:
    """Assemble the DATED catalyst rows — deterministic, source-bound, never weighted:
    A. the next results print (cadence-estimate from the filer's own 2.02 history);
    B. the committed revised-guidance checkpoint enriches the print row (the print TESTS the guide);
    C. in-horizon debt maturities from the capital-structure panel (stated ISO dates).
    Every miss is a loud qa_flag; an empty calendar is an honest outcome."""
    rows: list[CatalystRow] = []
    qa: list[str] = []
    # A + B — the next print, and what it tests
    try:
        filings = edgar.recent_filings(cik, forms=("8-K",))
        prints = [f.filing_date for f in filings if "2.02" in f.items]
    except Exception as exc:  # noqa: BLE001 — a feed miss is a loud flag, never an abort
        prints = []
        qa.append(f"catalyst: submissions feed unavailable ({type(exc).__name__}) — no print row")
    if prints:
        est = _next_print_estimate(prints, reference_date)
        if est is None:
            qa.append(f"catalyst: print cadence unreadable ({len(prints)} results 8-Ks / "
                      "irregular gaps) — no estimated print row (never guessed)")
        else:
            est_date, basis = est
            rg = mech.drawdown_cause.revised_guidance
            if rg.status is SourceStatus.PRESENT and rg.value:
                tests = ("the committed revised outlook (see Revised guidance — the print is the "
                         "checkpoint that confirms or refutes it)")
                src = f"cadence: EDGAR submissions ({basis}) · guide: {rg.source_ref}"
            else:
                tests = "the next reported quarter against the committed trajectory"
                src = f"cadence: EDGAR submissions ({basis})"
            rows.append(CatalystRow(
                event="Next results print", expected_date=est_date.isoformat(),
                date_basis="cadence-estimate", tests_what=tests, source_ref=src))
    # C — in-horizon maturities (stated dates from the capital-structure panel). ``instruments``
    # is Sourced[list[...]] — read the value only when PRESENT (absent panel = no rows, no guess).
    cs = mech.capital_structure
    if (cs is not None and cs.instruments.status is SourceStatus.PRESENT
            and cs.instruments.value):
        horizon = reference_date + timedelta(days=_CAL_MATURITY_HORIZON_DAYS)
        for inst in cs.instruments.value:
            if not inst.maturity_date:
                continue
            try:
                mat = date.fromisoformat(inst.maturity_date)
            except ValueError:
                qa.append(f"catalyst: unparseable maturity {inst.maturity_date!r} "
                          f"on {inst.description!r} — row skipped")
                continue
            if reference_date < mat <= horizon:
                amt = (f"${inst.principal_musd:,.1f}M " if inst.principal_musd is not None else "")
                rows.append(CatalystRow(
                    event=f"{inst.description} {amt}matures".replace("  ", " "),
                    expected_date=mat.isoformat(), date_basis="stated",
                    tests_what="refinance / repay / convert before the wall — the survival read",
                    source_ref="CIQ capital-structure panel (maturity_date)"))
    # D — management-stated dated operating events from the driver verbatims (source D,
    # ratified 2026-07-24; surfaced by SMPL's September price increase)
    rows.extend(_dated_operating_events(mech.operating_drivers, reference_date))
    rows.sort(key=lambda r: r.expected_date)
    return CatalystCalendar(rows=rows, qa_flags=qa)


def _catalyst_stale_flag(catalyst: CatalystPath, reference_date: date) -> str | None:
    """Fire the SHARED staleness caveat (same 45d knob as the EV/EBITDA stale-Close check) when the
    Estimates export's as-of trails the reference date by more than the constant — the revision
    breadth / guidance / consensus below may predate a since-then re-rate. UNKNOWN as-of → no fire
    (fail-quiet on absence; the sub-fields already read MISSING)."""
    aod = catalyst.as_of.value
    if not aod:
        return None
    if "operator-attested" in (catalyst.as_of.note or ""):  # R1: attested date trusted — no caveat
        return None
    if aod.startswith("≥"):  # FLOOR basis — a lower bound on the (un-stamped) export date
        # A floor F is a lower bound on the true export date E: an export cannot embed a revision
        # event dated after itself, so E >= F. Hence worst-case staleness (R - E) <= (R - F). When
        # even that worst case is within tolerance the data is PROVABLY fresh — no caveat (a floor
        # at/after the reference means the export post-dates the screen: fresher still). The floor
        # nature is never hidden: each read keeps its "≥F · export date unverified" suffix. The
        # caveat fires ONLY when the bound cannot rule out staleness.
        floor = date.fromisoformat(aod[1:])
        worst_case_stale = (reference_date - floor).days
        if worst_case_stale <= _STALE_CLOSE_DAYS:
            return None
        return (
            f"Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp; "
            f"its data is on/after {aod[1:]} (the latest embedded revision event), so it is up to "
            f"{worst_case_stale}d before the {reference_date.isoformat()} reference — beyond the "
            f"{_STALE_CLOSE_DAYS}d tolerance — and the true export date is unknown, so freshness "
            "cannot be confirmed. Re-pull CIQ Estimates, or attest the export date (AS_OF sidecar)."
        )
    stale_days = (reference_date - date.fromisoformat(aod)).days
    if stale_days <= _STALE_CLOSE_DAYS:
        return None
    return (
        f"Catalyst-path staleness caveat — the CIQ Estimates export is as-of {aod}, {stale_days}d "
        f"before the {reference_date.isoformat()} reference; the revision breadth, guidance bridge "
        "and consensus below may predate a since-then re-rate. Re-pull CIQ Estimates before "
        "relying on the horizon/acceleration reads."
    )


def _iso_or_none(stamp: str | None) -> date | None:
    """A clean ISO date, or None for anything else (a floor ``≥…``, a prose note, empty). The
    freshness gate fires only on a parseable as-of, so an odd stamp fails quiet."""
    if not stamp:
        return None
    try:
        return date.fromisoformat(stamp)
    except ValueError:
        return None


def _latest_earnings_print(edgar: EdgarClient, cik: str) -> date | None:
    """The latest EARNINGS print date on EDGAR — the newest 8-K carrying item 2.02 (Results of
    Operations). Fail-quiet: a submissions-feed miss or a name with no 2.02 on file returns None
    (the caller then raises no freshness caveat, never aborts)."""
    try:
        prints = [f.filing_date for f in edgar.recent_filings(cik, forms=("8-K",))
                  if "2.02" in f.items]
    except Exception:  # noqa: BLE001 — a feed miss silences the gate, never aborts the assembly
        return None
    return max(prints) if prints else None


def _panel_freshness_flag(
    ie: ImpliedExpectations | None, latest_print: date | None,
) -> str | None:
    """Fire a loud caveat when a CIQ valuation panel PREDATES the latest earnings print — the guard
    the SMPL 2026-07-24 stale-inputs incident earned (a recorded BUY read panels dated 2026-06-03 /
    2026-06-25 while the FQ3 print had landed 2026-07-09).

    ORTHOGONAL to the reference-date stale checks (``_catalyst_stale_flag`` / the EV/EBITDA
    stale-Close): those compare a panel's as-of to the REFERENCE date within a 45d tolerance, and a
    panel can sit inside that tolerance yet still predate a PRINT that landed after both the panel
    AND the reference (SMPL's panels were within 45d of its 2026-07-06 reference — the reference
    itself predated the print). ANCHORED — EDGAR item-2.02 filing dates + the panels' own CIQ as-of
    stamps; NO tunable knob (`older than the newest print` is a hard fact, not a face-validity
    band). Fail-quiet: no print, no valuation block, or an unparseable as-of → no caveat."""
    if ie is None or latest_print is None:
        return None
    stale = [(label, d) for label, stamp in (("valuation multiples", ie.multiples_as_of),
                                             ("implied-TEV inputs", ie.tev_as_of))
             if (d := _iso_or_none(stamp)) is not None and d < latest_print]
    if not stale:
        return None
    lag = (latest_print - min(d for _, d in stale)).days
    named = "; ".join(f"{label} as-of {d.isoformat()}" for label, d in stale)
    return (
        f"Panel-freshness caveat — {len(stale)} CIQ valuation panel(s) predate the latest earnings "
        f"print ({latest_print.isoformat()}, EDGAR 8-K item 2.02), the oldest by {lag}d: {named}. "
        "The valuation read may rest on a pre-print P&L — re-pull CIQ after the print before "
        "relying on it."
    )


# --- E1/E3/E4: structured capital structure + maturity-anchored 8-Ks + covenant pointers -----
def _maturity_8ks(
    edgar: EdgarClient, cik: str, instruments: list[CapitalInstrument], reference_date: date
) -> Sourced[str]:
    """(E3) 8-Ks filed within ±10d of any instrument maturity in the TRAILING 12m — where a
    recently-matured facility's resolution would be disclosed. POINTERS only ('read for
    resolution'); never an assumption of repayment or default."""
    mats = sorted({
        date.fromisoformat(i.maturity_date)
        for i in instruments
        if i.maturity_date
        and reference_date - timedelta(days=365)
        <= date.fromisoformat(i.maturity_date) <= reference_date
    })
    if not mats or not cik:
        return Sourced.unknown(note="no trailing-12m instrument maturity to anchor an 8-K")
    try:
        filings = edgar.recent_filings(cik, forms=("8-K",), since=min(mats) - timedelta(days=11))
    except HttpError as exc:
        return Sourced.unknown(note=f"EDGAR 8-K fetch failed: {exc}")
    lines: list[str] = []
    seen: set[str] = set()
    for m in mats:
        for f in sorted(filings, key=lambda f: abs((f.filing_date - m).days)):
            if abs((f.filing_date - m).days) > 10 or f.accession in seen:
                continue
            seen.add(f.accession)
            items = ", ".join(item_labels(list(f.items))) or "—"
            lines.append(
                f"8-K at maturity {m.isoformat()}: filed {f.filing_date.isoformat()} "
                f"[{f.accession}] {items} — read for resolution"
            )
    if not lines:
        dates = ", ".join(m.isoformat() for m in mats)
        return Sourced.unknown(note=f"no 8-K within ±10d of a trailing-12m maturity ({dates})")
    return Sourced.present(
        "; ".join(lines), source_ref="EDGAR 8-K submissions (±10d of instrument maturities)")


# (H1) agreement-class whitelist — only an instrument backed by a DISCRETE contract gets a filing
# lookup; a generic balance-sheet aggregate (Notes Payable, a lease) has no single agreement to
# point at and renders an honest "no contract-level filing expected" note.
_COVENANT_CLASS_RE = re.compile(
    r"\b(loan|credit|facilit|indenture|convertible|agreement|bond)\b", re.IGNORECASE)
# an EXECUTION filing carries the agreement as an EXHIBIT — a material-contract ex-10.x or a
# filename naming the contract; a primary 8-K body ('mvst-20240603.htm') matches none of these.
#: A MATERIAL-CONTRACT EXHIBIT FILENAME, across the conventions filers actually use.
#:
#: The shipped pattern was `ex-?10\d` — a DIGIT immediately after "10" — which matches only the
#: compacted form (`ex102` = exhibit 10.2). Measured against the real filenames in the fleet's own
#: filings, that is the minority convention, and the majority use a SEPARATOR:
#:
#:     ex102_q425.htm                    NFLX    compact       matched
#:     vitl-ex10_10.htm                  VITL    underscore    MISSED
#:     aort-20251231xexx1032.htm         AORT    double-x      MISSED
#:     fubo-20241231exx1026.htm          FUBO    double-x      MISSED
#:     f8k032018ex10-1_simplygood.htm    SMPL    hyphen        MISSED
#:     a19-22146_1ex10d1.htm             SMPL    d-separator   MISSED
#:
#: NFLX was the ONLY name it matched, and only by its filing agent's naming style — which is why
#: four names located no covenant exhibit at all. The fragment appears in BOTH pointer passes (the
#: 10-K exhibit index and this efts hit filter), so one flaw failed both routes on the same names
#: and the failure looked total rather than partial.
#:
#: `10` STAYS PINNED: exhibit 10.x is the material-contract class. UBER's `exhibit191` (19.1) and
#: SMPL's `exhibit211` (21.1) must NOT match — those are a clawback policy and a subsidiary list.
_EX10_RE = r"ex(?:hibit)?[-_x]?10[._\-d]?\d"
_AGREEMENT_EXHIBIT_RE = re.compile(
    rf"{_EX10_RE}|loan|credit|facilit|indenture|agreement|secur|pledge|guarant|warrant",
    re.IGNORECASE)


def _covenant_query(desc: str) -> str:
    """The canonical efts phrase for an instrument's agreement class — the CIQ label ('Convertible
    Loan With Shareholder') rarely matches the filing's contract name ('Loan and Security
    Agreement'), so query the class's standard agreement term instead of the raw label."""
    d = desc.lower()
    # A NOTE IS AN INDENTURE INSTRUMENT, like a bond. Without this, "2025 Convertible Notes" fell
    # through every branch to the "Loan Agreement" default — the wrong contract class entirely, and
    # the query UBER's and FUBO's convertible notes were searched under.
    if ("bond" in d or "note" in d) and "loan" not in d:
        return "Indenture"
    if "credit" in d:
        return "Credit Agreement"
    if "facilit" in d and "loan" not in d:
        return "Facility Agreement"
    return "Loan Agreement"  # loan / convertible-loan / default


def _exhibit_names(http: CachedHttp, cik: str, accession: str) -> list[str]:
    """The document filenames in one filing's index.json ([] on any fetch/parse failure)."""
    try:
        idx = http.get_json(
            _INDEX.format(cik=int(pad_cik(cik)), acc=accession.replace("-", "")), ttl_seconds=None)
    except (HttpError, ValueError):
        return []
    return [str(it.get("name", "")) for it in idx.get("directory", {}).get("item", [])]


#: CIQ writes its panel vintage as "A 2025 filed Jan-23-2026" — a MONTH-NAME date, which is
#: why `freshness._ISO` never matched it and the debt schedule has never carried an age.
#:
#: THE PARSER MOVED to `ciq_sheets` (imported at the top of this module and re-exported, so callers
#: and the existing test import are unchanged). It moved because a SECOND consumer appeared —
#: `_cs_details_freq` reads this same stamp when selecting a panel — and two regexes
#: over one string is the divergence this repo has paid for before: an unanchored `Mon-DD-YYYY`
#: search reads `A 2025 (Dec-31-2025) filed Jan-23-2026` as the PERIOD END, so the picker would
#: have ranked panels by a different date than the staleness banner below reports.
#:
#: EDGAR item 1.02 — "Termination of a Material Definitive Agreement". The one item code that says,
#: from the filer's own index and without reading a word of the filing, that an agreement the panel
#: may still list has ended.
_ITEM_TERMINATION = "1.02"


def _capital_structure_vintage(
    edgar: EdgarClient, cik: str, detail_as_of: str, reference_date: date,
) -> Sourced[str]:
    """How old the debt schedule is, and whether a TERMINATION has been filed since it was taken.

    THE PANEL HAS NEVER CARRIED AN AGE, and every name's is months old: measured across all 14
    committed dossiers the source filings run **82 to 280 days** behind their own build (SMPL 280,
    V 277, BRBR 265, NFLX 199 …). The cause is a format mismatch nobody had cause to notice —
    `freshness._PANEL_KEY` matches `detail_as_of`, but `freshness._ISO` wants `2026-01-23` and CIQ
    writes `Jan-23-2026`, so the key was found and the date never extracted.

    IT IS DELIBERATELY NOT ROUTED INTO `panel_age`/`check_freshness`. That was the obvious fix and
    the measurement refuses it: the export ceiling is **45 days** and ALL FOURTEEN names sit past
    it, so teaching the freshness gate this format would raise `FreshnessError` on the whole fleet.
    `check_freshness`'s own docstring names that failure mode — *"a guard that stops every build is
    a freeze wearing a guard's name"*. The age belongs beside the schedule it describes, where a
    reader is looking at the instruments, not in a gate that would stop the presses.

    EVERY DATE IS AS-OF-BOUNDED. The window is `panel filed < 1.02 <= reference_date`: an
    event after the record's as-of is not this record's to report, however true it is today.

    THE TERMINATION HALF IS WHY THIS EXISTS AT ALL. NFLX's committed page still lists the Warner
    Bros. Discovery bridge facility, whose commitments were terminated on 2026-02-27 — because the
    panel is dated 2026-01-23 and CANNOT know. Item 1.02 is carried in the filer's own submissions
    index, so no filing has to be read to see that one was filed after the panel was taken.

    A FLAG, NEVER A DELETION, and never an attempt to say WHICH instrument died: matching a
    termination to a facility means reading the 8-K, and a wrong match is worse than an honest
    "something ended after this snapshot — check". The human is told what to check and where.
    """
    filed = _cs_panel_filed(detail_as_of)
    if filed is None:
        return Sourced.unknown(
            note=f"the capital-structure panel states no source filing date ({detail_as_of!r}) — "
                 f"its age cannot be measured, so nothing here says how current the schedule is")
    age = (reference_date - filed).days
    src = f"CIQ Capital Structure Details — {detail_as_of}"
    try:
        # BOUNDED AT BOTH ENDS, and the upper bound is the one that bit (review finding, #416).
        # `recent_filings` returns the CURRENT submissions index, so an unbounded ">= filed" test
        # reports whatever has been filed by the time the code RUNS — not by the record's as-of.
        # Measured on the committed artifacts: UBER's 2026-07-29 record was flagged by an 8-K filed
        # 2026-08-07 (+9d) and VITL's 2026-07-06 record by one filed 2026-08-06 (+31d). That is the
        # lookahead class `close_as_of` exists to refuse one module over — it reports an event the
        # reader could not have known, and it makes the artifact irreproducible, because
        # re-assembling at the SAME reference_date yields a different answer as time passes.
        terminations = [f for f in edgar.recent_filings(cik, forms=("8-K",))
                        if _ITEM_TERMINATION in (f.items or [])
                        and filed < f.filing_date <= reference_date]
    except (HttpError, KeyError, ValueError):
        return Sourced.present(
            f"the debt schedule is {age}d old (source filed {filed}) — EDGAR was unreachable, so "
            f"whether an agreement has been terminated since is UNCHECKED", source_ref=src)
    if not terminations:
        return Sourced.present(
            f"the debt schedule is {age}d old (source filed {filed}); no Item 1.02 "
            f"(termination of a material agreement) has been filed since", source_ref=src)
    latest = max(terminations, key=lambda f: f.filing_date)
    more = f" (+{len(terminations) - 1} more)" if len(terminations) > 1 else ""
    return Sourced.present(
        f"the debt schedule is {age}d old (source filed {filed}) AND an Item 1.02 — termination of "
        f"a material definitive agreement — was filed {latest.filing_date}{more}, accession "
        f"{latest.accession}. The panel predates it and cannot reflect it: an instrument listed "
        f"below may already have been terminated. Verify before relying on this schedule.",
        source_ref=src)


#: The note for a search that RAN and located nothing — as opposed to one that could not run
#: (no CIK, or EDGAR/efts unreachable). Both come back UNKNOWN with a null value, so a caller that
#: keys on `bool(value)` cannot tell them apart and will report a completed search that never
#: happened. Shared as a constant rather than matched as a literal, so the two cannot drift.
COVENANT_SEARCH_FOUND_NOTHING = "no CIK-scoped agreement exhibit located across the filing history"


def _covenant_pointers(
    edgar: EdgarClient, http: CachedHttp, cik: str, instruments: list[CapitalInstrument],
    reference_date: date,
) -> Sourced[list[CovenantPointer]]:
    """(H1) Locate the EXECUTION filing (the 8-K/10-K carrying the agreement as an exhibit) for each
    AGREEMENT-CLASS instrument, SCOPED to the subject CIK. efts full-text is queried with ciks=<CIK>
    AND any cross-CIK hit is rejected (the E4 bug: an unscoped 'Convertible Bond' matched AXESSTEL's
    2005 8-K). A generic BS line (Notes Payable, a lease) gets an honest 'no contract-level filing'
    note. Deduped by accession; the located exhibit filenames feed the fenced E5 extraction."""
    if not cik:
        return Sourced.unknown(note="no CIK for covenant-pointer lookup")
    cik10 = pad_cik(cik)
    rows: list[CovenantPointer] = []
    seen: set[str] = set()

    # (1) latest 10-K material-contract exhibits (ex-10.x) — contracts incorporated by reference
    try:
        # AS-OF BOUNDED (review finding, #426). `recent_filings` returns TODAY's submissions
        # index, so `tenks[0]` is whatever is newest when the code RUNS — re-assembling a
        # historical dossier would attach a 10-K filed after its own reference date. Same class as
        # #416's termination lookahead, and the widened exhibit matcher makes it REACHABLE for the
        # four names that previously located nothing at all.
        tenks = [f for f in edgar.recent_filings(cik, forms=("10-K",))
                 if f.filing_date <= reference_date]
        if tenks:
            acc = tenks[0].accession
            exs = [n for n in _exhibit_names(http, cik, acc)
                   if re.search(_EX10_RE, n, re.I)]
            if exs:
                rows.append(CovenantPointer(
                    family="material contracts (10-K exhibit index)", filing="latest 10-K",
                    filing_date=tenks[0].filing_date.isoformat(), accession=acc, exhibits=exs))
                seen.add(acc)
    except (HttpError, KeyError, ValueError):
        pass

    # (2) per whitelisted family — efts (ciks-scoped) → keep only EXHIBIT-BEARING execution 8-Ks
    queries: dict[str, str] = {}  # family → canonical efts phrase
    generic: list[str] = []
    for i in instruments:
        fam = i.description.split(" With ")[0].split(" - ")[0].strip()
        if _COVENANT_CLASS_RE.search(i.description):
            queries.setdefault(fam, _covenant_query(i.description))
        elif fam not in generic:
            generic.append(fam)
    for fam, phrase in list(queries.items())[:6]:
        try:
            hits = edgar.fulltext_search(phrase, forms="8-K", ciks=cik10)
        except HttpError:
            continue
        added = 0
        for h in hits:
            if added >= 2:
                break
            # (H1a) DEFENSE-IN-DEPTH cross-CIK guard — reject any hit whose filer CIK ≠ the subject
            if h.cik and pad_cik(h.cik) != cik10:
                continue
            # …and never an execution filing the record's own as-of could not have seen.
            if h.file_date and h.file_date > reference_date:
                continue
            if h.accession in seen:
                continue
            exs = [n for n in _exhibit_names(http, cik, h.accession)
                   if _AGREEMENT_EXHIBIT_RE.search(n)
                   and n.lower().endswith((".htm", ".html", ".txt"))]  # .html: some filers use it
            if not exs:  # a mention-only 8-K (no agreement exhibit) is NOT a pointer
                continue
            seen.add(h.accession)
            rows.append(CovenantPointer(
                family=fam, filing="8-K",
                filing_date=h.file_date.isoformat() if h.file_date else "",
                accession=h.accession, exhibits=exs))
            added += 1

    # (3) generic balance-sheet aggregates — honest "no contract-level filing" note (not a pointer)
    for fam in generic[:4]:
        rows.append(CovenantPointer(
            family=fam, filing="—", filing_date="", accession="", exhibits=[],
            note="no contract-level filing expected (aggregate line item)"))

    if not any(r.accession for r in rows):
        return Sourced.unknown(note=COVENANT_SEARCH_FOUND_NOTHING)
    return Sourced.present(
        rows,
        source_ref="EDGAR 10-K exhibit index + CIK-scoped efts (agreement-class, exhibit-bearing)")


def _covenant_summary(rows_s: Sourced[list[CovenantPointer]]) -> str:
    """A one-line summary of the located pointers (back-compat covenant_pointers string)."""
    if rows_s.status is not SourceStatus.PRESENT or not rows_s.value:
        return ""
    located = [f"{r.family[:34]} [{r.accession}]" for r in rows_s.value if r.accession]
    return "; ".join(located) if located else "no contract-level filing located"


def _capital_structure(
    record: DataRecord, edgar: EdgarClient, http: CachedHttp, bundle: CiqBundle,
    reference_date: date,
) -> CapitalStructure:
    """(E1+E3+E4) Assemble the structured capital structure: CIQ instruments + summary aggregates,
    the maturity-anchored 8-Ks, and the covenant exhibit pointers. Covenant TERMS (E5, LLM) are
    filled in the synthesis phase; UNKNOWN here."""
    instruments, summary, detail_as_of = ciq_sheets.capital_structure_ciq(bundle)
    insts = (instruments.value
             if instruments.status is SourceStatus.PRESENT and instruments.value else [])
    cik = record.identity.cik
    pointer_rows = _covenant_pointers(edgar, http, cik or "", insts, reference_date)
    vintage = (_capital_structure_vintage(edgar, cik, detail_as_of, reference_date)
               if cik else Sourced.unknown(note="no CIK"))
    located = (pointer_rows.status is SourceStatus.PRESENT
               and any(r.accession for r in (pointer_rows.value or [])))
    summary_str = _covenant_summary(pointer_rows)
    pointers_str = (Sourced.present(summary_str, source_ref=pointer_rows.source_ref or "efts")
                    if located and summary_str else
                    Sourced.unknown(note=pointer_rows.note or "no CIK-scoped agreement exhibit"))
    # (E5, fenced) covenant TERMS are LLM-extractable ONLY from a located exhibit; the note is
    # opacity-as-signal — it tells the human whether any exhibit exists to read (a Tier-1 pointer
    # present) or whether the facility is wholly undocumented (extraction impossible, itself a
    # fact).
    terms_note = (
        "(E5) named covenant terms extract in the LLM phase from the located exhibit(s) above"
        if located else "(E5) no covenant exhibit located — nothing to extract named terms from")
    return CapitalStructure(
        instruments=instruments, summary=summary, detail_as_of=detail_as_of,
        maturity_filings=_maturity_8ks(edgar, cik or "", insts, reference_date),
        covenant_pointers=pointers_str, covenant_pointer_rows=pointer_rows,
        covenant_terms=Sourced.unknown(note=terms_note),
        panel_vintage=vintage,
    )


# --- (G) implied expectations: price-inverted, multiples-space ----------------------------------
# Every input is an ALREADY-ASSEMBLED Sourced field — these parsers read those assembled values,
# NEVER the workbook (no extraction; that would be an extractor change, out of scope). Deterministic
# arithmetic only: implied_level = TEV ÷ multiple. TEV is DERIVED (mcap + net debt) since it's
# not surfaced as a single field; the same two fields feed a vintage-coherence guard.
_IE_TOL = 0.10  # G5 vintage-coherence tolerance AND (condition b) the net-debt reconciliation band

# THE fixed, declared multiple set (no per-name curation). Each: (label, metric, kind, key). kind
# 'ladder' = the name's OWN NTM forward multiple (catalyst cross_name_anchor); 'peer' = the peer
# median (peer_comps trading_multiples). 'key' locates the number inside that assembled string.
_IE_MULTIPLE_SET: tuple[tuple[str, str, str, str], ...] = (
    ("name NTM TEV/EBITDA", "EBITDA", "ladder", "TEV/EBITDA"),
    ("peer-median NTM TEV/EBITDA", "EBITDA", "peer", "NTM TEV/EBITDA"),
    ("peer-median LTM TEV/EBITDA", "EBITDA", "peer", "TEV/EBITDA"),
    ("name NTM TEV/Rev", "Revenue", "ladder", "TEV/REV"),
    ("peer-median NTM TEV/Rev", "Revenue", "peer", "NTM TEV/Rev"),
    ("peer-median LTM TEV/Rev", "Revenue", "peer", "TEV/Rev"),
)


def _ie_ladder(cna: str | None, period: str, key: str) -> float | None:
    """A forward multiple from the cross_name_anchor ladder ('NTM: … TEV/EBITDA 7.54 …')."""
    if not cna:
        return None
    seg = next((s for s in cna.split(" | ") if s.strip().startswith(period)), None)
    if not seg:
        return None
    mo = re.search(rf"{re.escape(key)}\s+(-?\d+(?:\.\d+)?)", seg)
    return float(mo.group(1)) if mo else None


def _ie_peer_median(tm: str | None, label: str) -> float | None:
    """The peer-median multiple for an EXACT trading_multiples segment label ('NM' → None)."""
    if not tm:
        return None
    for seg in tm.split(";"):
        lab, _, rest = seg.partition(":")
        if lab.strip() == label:
            mo = re.search(r"Median\s+(-?\d+(?:\.\d+)?|NM)", rest)
            return float(mo.group(1)) if (mo and mo.group(1) != "NM") else None
    return None


def _ie_consensus_latest(ar: str | None, period: str, metric: str) -> float | None:
    """The latest consensus level for period+metric from the acceleration_read path string."""
    if not ar:
        return None
    seg = next((s for s in ar.split(" | ") if s.strip().startswith(f"{period} {metric}:")), None)
    mo = re.search(r"(-?\d+(?:\.\d+)?)\s*\(latest\)", seg) if seg else None
    return float(mo.group(1)) if mo else None


def _ie_bridge_net_debt(implied: ImpliedValuation) -> float | None:
    """Net debt implied by the cash/debt bridge (total debt − cash) — condition-b probe. Reads the
    STRUCTURED schema floats (DESIGN RULE); the old thousands-blind regex on the display string
    truncated '$1,101.80M' → 1 and fired a FALSE reconcile caveat. Legacy fallback parses the render
    string via the shared _parse_money() only when a structured field is absent."""
    cash, debt = implied.bridge_cash, implied.bridge_debt
    if (cash is None or debt is None) and implied.bridge.status is SourceStatus.PRESENT:
        br = implied.bridge.value or ""
        if cash is None and (m := re.search(r"cash \$([\d,.]+)", br)):
            cash = _parse_money(m.group(1))
        if debt is None and (m := re.search(r"total debt \$([\d,.]+)", br)):
            debt = _parse_money(m.group(1))
    return debt - cash if (cash is not None and debt is not None) else None


def _uncorrected_reason(stamp: date | None, price_bars: list[Any] | None,
                        printed_close: float | None) -> str:
    """WHY the comps as-of could not be corrected — the causes are different facts.

    THE STRING WAS TRUE OF ONE PATH AND BECAME FALSE OF THE OTHERS (review of #488). The original
    reason — "the store carries no bar at that panel's printed close" — described the only refusal
    that existed. The coverage precondition added a SECOND, and on it the store usually DOES carry
    the bar: HLF holds 12.45 on 2025-12-03 and its own regression pin asserts exactly that, while
    its dossier printed the no-bar sentence. A reason that names the wrong cause is worse than
    none, because it sends the reader to check a thing that is not wrong.

    ALL FOUR REFUSALS, IN THE ASSEMBLER'S OWN ORDER (review of #490). The first cut named two, but
    `assemble.py` never calls `date_of_close` at all unless BOTH the export stamp and the panel's
    printed close decode — the two `None` guards added by the review of #469. On either of those
    the store is untouched, so blaming it ("carries no bar at that panel's printed close" for a
    panel that prints no close) is the same wrong-cause defect one branch further out. Each guard
    that can suppress the correction states itself.
    """
    if stamp is None:
        return ("the panel carries no decodable export-stamp header, so there is no bound to "
                "correct against and the store was never consulted")
    if printed_close is None:
        return ("the panel prints no close price of its own, so there is nothing to match the "
                "store against")
    dates = [d for b in (price_bars or []) if isinstance(d := getattr(b, "bar_date", None), date)]
    frontier = max(dates, default=None)
    if frontier is not None and (stamp - frontier).days > _COVERAGE_GAP_DAYS:
        return (f"the price store ends {frontier.isoformat()}, before the {stamp.isoformat()} "
                "export stamp — the bar this panel names is absent, so any match would be "
                "coincidence")
    return "the store carries no bar at that panel's printed close"


def _implied_expectations(
    peer_comps: PeerComps, catalyst: CatalystPath, implied_val: ImpliedValuation, bundle: CiqBundle,
    price_bars: list[Any] | None = None,
) -> ImpliedExpectations | None:
    """(G) Assemble price-inverted expectations from ALREADY-SOURCED fields. TEV = mcap + net debt
    (simple-TEV basis — the cell is not surfaced and carries a stale second pricing vintage,
    so deriving from Latest-mcap is vintage-coherent). implied_level = TEV ÷ multiple for the fixed
    set. (H7) The EBITDA consensus anchors are the DIRECT Estimates→Trends latest levels (the single
    source of truth), NOT TEV ÷ ladder — the ladder-derived FY26 lives ONLY in the vintage-guard
    line; a G5 residual (FY26 probe) certifies the vintages. Returns None when TEV can't be derived
    (mcap / net debt absent) — the block won't render."""
    mc, grid = implied_val.market_cap, peer_comps.peer_grid
    if (mc.status is not SourceStatus.PRESENT or mc.value is None
            or grid is None or grid.status is not SourceStatus.PRESENT):
        return None
    name_row = next((r for r in (grid.value or []) if getattr(r, "is_name", False)), None)
    if name_row is None or name_row.net_debt is None:
        return None
    market_cap, net_debt = float(mc.value), float(name_row.net_debt)
    tev = market_cap + net_debt
    # CIQ's As-Of is the EXPORT date; the data is the PRIOR close (measured 11/11). Correct it
    # from the store's own prior BAR, never `date - 1` — two stamps in the fleet land on a Monday.
    #
    # SCOPE, STATED HONESTLY: this corrects the COMPS panel only. The offset was measured by
    # comparing CIQ's `Day Close Price Latest` against the store, and that column exists only on
    # Comparable Analysis → Financial Data. `mult_as_of` below comes from the ESTIMATES export,
    # whose convention has NOT been measured — correcting it too would be assuming the convention
    # generalises, which is the category-label rule. It stays uncorrected until measured.
    # STRUCTURED, NOT RE-PARSED — and it must not be corrected a SECOND time.
    # This read `_ie_asof(mc.source_ref)`: a regex over the rendered suffix, which is the "second
    # parser of one display string" `comps_as_of_date`'s own docstring says the extractor exists to
    # avoid. It survived because both parsers agreed while the suffix carried CIQ's raw header.
    # THE COLLISION (review of #466): the assembler now injects the CORRECTED comps as-of, so
    # the suffix carried it, this regex read it back out, and `corrected_ciq_as_of` walked it
    # back ANOTHER trading day — measured on NFLX, header 2026-08-17 → injected 2026-08-14 →
    # re-corrected 2026-08-13, on each of the 13 bundles the correction reaches. One panel, two
    # dates, both wrong.
    _cd, _ = ciq_sheets.comps_as_of_date(bundle)
    tev_as_of = _cd.isoformat() if _cd is not None else "UNKNOWN"
    _raw = ciq_sheets.comps_export_stamp(bundle)
    _export_stamp = _raw.isoformat() if _raw is not None else "UNKNOWN"
    _corrected = bundle.resolved_comps_as_of is not None
    mult_as_of = (
        (catalyst.as_of.value or "UNKNOWN").lstrip("≥")
        if catalyst.as_of.status is SourceStatus.PRESENT else "UNKNOWN")
    cna = (catalyst.cross_name_anchor.value
           if catalyst.cross_name_anchor.status is SourceStatus.PRESENT else None)
    tm = (peer_comps.trading_multiples.value
          if peer_comps.trading_multiples.status is SourceStatus.PRESENT else None)
    cna_src = catalyst.cross_name_anchor.source_ref or "CIQ Estimates→Multiples"
    tm_src = peer_comps.trading_multiples.source_ref or "CIQ Comparable Analysis→Trading Multiples"

    rows: list[ImpliedExpectationRow] = []
    for label, metric, kind, key in _IE_MULTIPLE_SET:
        mult = _ie_ladder(cna, "NTM", key) if kind == "ladder" else _ie_peer_median(tm, key)
        src = cna_src if kind == "ladder" else tm_src
        if mult is None or mult <= 0:  # NM/negative/absent → UNKNOWN row, never a fake multiple
            note = ("multiple NM/non-positive — no fundamental level implied" if mult is not None
                    else "multiple absent from the assembled comps")
            rows.append(ImpliedExpectationRow(
                label=label, metric=metric, multiple=mult, multiple_source=src,
                implied_level=None, is_identity=(kind == "ladder"), note=note))
        else:
            rows.append(ImpliedExpectationRow(
                label=label, metric=metric, multiple=mult, multiple_source=src,
                implied_level=round(tev / mult, 1), is_identity=(kind == "ladder")))

    # (H7/P8) BOTH the EBITDA and REVENUE consensus anchors are the DIRECT Estimates→Trends latest
    # levels (FY26E/FY27E), the SINGLE SOURCE OF TRUTH — NOT TEV ÷ ladder. The ladder FY26 (a26) is
    # kept ONLY for the G5 vintage-guard probe below (the ladder-derived figure now lives ONLY there
    # for both metrics). The TEV/Rev name-row identity still stands in the table (is_identity row).
    def _anchor(period: str, key: str = "TEV/EBITDA") -> float | None:
        mo = _ie_ladder(cna, period, key)
        return (tev / mo) if (mo and mo > 0) else None  # UNROUNDED; 1dp only at display

    def _direct_anchors(metric: str) -> Sourced[str]:
        # SAME DERIVATION AS THE SUMMARY COLUMNS — one helper, not a second literal pair. Two
        # hardcoded (FY 2026, FY 2027) tuples is how the anchors and the table come to name
        # different years on one page. NCNO/NIKE had already REPORTED FY2026, so asking Trends for
        # it returned nothing AND the failure note named years the sheet never offered.
        pairs = ciq_sheets.forward_estimate_fys(bundle)
        span = "/".join(display for _t, display in pairs) or "forward-year"
        vals = [(display, ciq_sheets.trends_fy_level(bundle, metric=metric, fy_label=trends_label))
                for trends_label, display in pairs]
        if not vals or all(v is None for _, v in vals):
            return Sourced.unknown(
                note=f"no direct {span} {metric} consensus in Estimates→Trends")
        txt = " · ".join(f"{lab} {(f'${v:.1f}M') if v is not None else 'n/a'}" for lab, v in vals)
        return Sourced.present(
            txt + f" (direct consensus {metric} — CIQ Estimates→Trends latest snapshot)",
            source_ref=f"CIQ Estimates→Trends ({span} consensus {metric}, latest snapshot)")

    a26 = _anchor("FY 2026")  # LADDER-derived FY26 — kept ONLY for the G5 vintage-guard probe below
    anchors = _direct_anchors("EBITDA")  # (H7) direct Trends, the single source of truth
    rev_anchors = _direct_anchors("Revenue")  # (P8) direct Trends — ladder only in the guard line

    # (G5) vintage-coherence: derived FY26 (TEV ÷ FY26 forward multiple, UNROUNDED) vs the DIRECT
    # FY26 EBITDA consensus (Estimates→Trends latest — SAME source as the anchors). NTM is not a
    # sourced level, so FY26 — the nearest direct consensus — is the probe; shared-TEV ladder certs.
    direct26 = ciq_sheets.trends_fy_level(bundle, metric="EBITDA", fy_label="FY 2026")
    coherent, pct = True, 0.0
    if direct26 and direct26 > 0 and a26 is not None:
        pct = abs(a26 - direct26) / direct26
        coherent = pct <= _IE_TOL
    # the residual is stated as a DECIMAL fraction, never a percentage — the block carries zero '%'
    # tokens (the value-space fence: nothing here is differenced into a percentage gap).
    if direct26 and a26 is not None:
        coherence_note = (
            f"vintage-coherent: derived FY26 ${a26:.1f}M vs direct consensus ${direct26:.1f}M "
            f"(residual {pct:.3f} ≤ {_IE_TOL:.2f} tolerance)" if coherent else
            f"multiple-pricing vintage differs from TEV as-of — re-pull comps (derived FY26 "
            f"${a26:.1f}M vs direct ${direct26:.1f}M, residual {pct:.3f} > {_IE_TOL:.2f})")
    else:
        coherence_note = "vintage-coherence UNKNOWN — no direct FY26 EBITDA consensus to probe"

    # (condition b) net-debt coherence vs the cash/debt bridge — reconcile or soft-caveat (C3).
    bridge_nd = _ie_bridge_net_debt(implied_val)
    nd_ok = bridge_nd is None or abs(bridge_nd - net_debt) <= _IE_TOL * max(1.0, abs(net_debt))
    tev_src = (
        f"TEV = mcap {market_cap:.1f} + net debt {net_debt:.1f} "
        # THREE STATES, DISTINGUISHABLE (review finding): corrected, nothing-to-correct, and
        # COULD-NOT-CORRECT. The first cut printed the last two identically, so a reader could not
        # tell a stamp that had been resolved against the store from one the store could not
        # resolve — and the unresolved one is a day too NEW, i.e. reads fresher than it is. An
        # uncorrectable stamp now says so on the page rather than passing as a corrected one.
        + (f"(CIQ Comparable Analysis→Financial Data, Latest, data {tev_as_of}, "
           f"exported {_export_stamp}" if _corrected else
           f"(CIQ Comparable Analysis→Financial Data, Latest, export stamp {_export_stamp} — "
           f"NOT date-corrected: "
           f"{_uncorrected_reason(_raw, price_bars, ciq_sheets.comps_printed_close(bundle))}")
        + ") — simple-TEV basis"
        + ("" if nd_ok else f"; ⚠ net-debt {net_debt:.1f} vs bridge {bridge_nd:.1f} — reconcile"))
    return ImpliedExpectations(
        rows=rows, tev=Sourced.present(round(tev, 1), source_ref=tev_src), anchors=anchors,
        rev_anchors=rev_anchors, heterogeneity_gate=implied_val.comparability_gate.value or "",
        tev_as_of=tev_as_of, multiples_as_of=mult_as_of, vintage_coherent=coherent,
        coherence_note=coherence_note, net_debt_reconciled=nd_ok)


_PS_TTL = 24 * 3600  # primary-source fetch cache TTL (seconds)


def _ltm_adj_ebitda(releases: list[ReleaseExtract]) -> float | None:
    """LTM adjusted EBITDA = FY + latest-Q − prior-year-Q, from the release recon values (the parser
    captures the prior-year comparison distinctly, period-labeled). None unless all three periods
    are present — never a partial guess (fail-loud).

    EXACT ONLY WHEN THE LATEST QUARTER IS Q1. The LTM ending Q1 of year Y is Q2..Q4 of Y−1 plus Q1
    of Y, which is FY(Y−1) − Q1(Y−1) + Q1(Y). Ending Q2 or Q3 it also needs every EARLIER quarter
    swapped, and this composition silently omits them: for Par Pacific at Q2 2026 it gives
    633.5 − 137.8 + 571.3 = $1,067.0M against a true $1,148.3M. That went unseen because
    mis-periodized FY rows kept tripping the guard below; once the release parser labels periods
    correctly the guard stops firing, so a later quarter is refused here instead — 'LTM
    unavailable' rather than a wrong LTM. A multi-quarter composition is a separate change."""
    vals: dict[str, float] = {}
    for r in releases:
        for rv in r.reconciliation:
            if rv.metric == "adjusted ebitda":
                vals.setdefault(rv.period, rv.value)
    quarters = [p for p in vals if re.fullmatch(r"Q[1-4]\s+20\d\d", p)]
    if not quarters:
        return None
    cur = max(quarters, key=lambda p: (int(p[3:7]), int(p[1])))  # latest (year, quarter)
    yr, qn = int(cur[3:7]), int(cur[1])
    if qn == 4:
        # the LTM ending Q4 of Y IS FY(Y) — no composition; refuse a year below its own Q4
        full = vals.get(str(yr))
        return round(full, 1) if full is not None and full >= vals[cur] else None
    if qn != 1:
        return None
    prior, fy = f"Q{qn} {yr - 1}", str(yr - 1)  # prior-year same quarter; the completed FY
    if prior not in vals or fy not in vals:
        return None
    if vals[fy] < vals[cur] or vals[fy] < vals[prior]:
        # A FULL-YEAR below one of its own quarters ⇒ a mis-periodized row (SMPL: a prior-year
        # QUARTER stamped with the bare year '2025' composed LTM = 66.2 − 73.9 + 57.0 = $49.3M →
        # a bogus ~6.6x net-debt/EBITDA in basis_triangulation, beside a real ~$220M LTM) or a
        # pathological quarter mix — refuse (→ 'LTM unavailable'), never a quarter-scale LTM.
        return None
    return round(vals[fy] - vals[prior] + vals[cur], 1)


def _latest_quarter_ocf_positive(facts: dict[str, Any] | None) -> bool | None:
    """Sign of the latest SINGLE-QUARTER operating cash flow (EDGAR) — the first self-funding input.
    Single-quarter = duration ≤ ~100 days (excludes 6/9-month YTD durations). None = unavailable."""
    if not facts:
        return None
    pts = [p for p in extract_points(facts, "operating_cash_flow")
           if p.period_start is not None and (p.period_end - p.period_start).days <= 100]
    return max(pts, key=lambda p: (p.period_end, p.filed)).value > 0 if pts else None


def _latest_balance_date(facts: dict[str, Any] | None) -> date | None:
    """The maturity-wall 'as of' — the most recent instant (balance-sheet) period_end in EDGAR."""
    if not facts:
        return None
    instants = [p.period_end for concept in ("long_term_debt", "debt_current")
                for p in extract_points(facts, concept) if p.is_instant]
    return max(instants) if instants else None


def _fy_reconciliation(releases: list[ReleaseExtract]) -> dict[str, float]:
    """The FULL-YEAR (bare 20YY period) recon values keyed by metric — the margin/revenue inputs."""
    out: dict[str, float] = {}
    for r in releases:
        for rv in r.reconciliation:
            if re.fullmatch(r"20\d\d", rv.period):
                out.setdefault(rv.metric, rv.value)
    return out


def _fy_impairment(releases: list[ReleaseExtract]) -> float | None:
    """The FY one-off impairment amount ($M) — the margin cross-check numerator."""
    for r in releases:
        for oo in r.one_offs:
            if "impair" in oo.description.lower():
                return oo.amount
    return None


#: The metric names that ARE the revenue line, as filers write them — the CROSS-CHECK's vocabulary,
#: not the page's.
#:
#: THE PARSER KEEPS THE FILER'S OWN WORD AND SHOULD (2026-08-12). `_guide_metric` folds "revenues" /
#: "total revenues" into `revenue` but leaves **net sales** alone, which is right for display:
#: BellRing guides "net sales" and its page should say so. The defect was that the guide-verify
#: consumer matched the string `"revenue"` exactly, so a net-sales guide was invisible to it and the
#: page reported **"release NO NUMERIC OUTLOOK → not cross-checked"** while the release stated one.
#:
#: BRBR IS THE PROOF: CIQ guides **2335.0–2375.0** and the 2026-08-04 release says *"Updated
#: fiscal year 2026 net sales outlook of $2.335-$2.375 billion"* — the SAME numbers, parsed
#: correctly, one metric-name away from a cross-source VERIFIED and reported as no outlook at all.
#: A verification that silently declines to run is worse than one that fails: it reads as
#: "checked, nothing to say".
#:
#: Fixed HERE rather than in `_guide_metric` deliberately — normalising at parse time would rename
#: the metric on the page, losing the filer's term, and churn every committed artifact and pin
#: that carries it. The synonym belongs to the consumer that needs it.
_REVENUE_LINE_METRICS: frozenset[str] = frozenset({"revenue", "net sales"})


def _release_revenue_guide(
    releases: list[ReleaseExtract],
) -> tuple[float | None, float | None, bool, str, str | None]:
    """The most-recent release's revenue guide as (low, high, qualitative, BASIS, PERIOD) — the
    cross-source comparison for guide verification. Releases are most-recent first; the first with
    a revenue guide wins (a QUALITATIVE-only outlook means the CIQ guide has no corroboration).

    THE BASIS RIDES WITH THE NUMBERS (2026-08-05). A release can guide revenue as a CHANGE
    ("-2% to +2% year-over-year"), and handing (low, high) onward without saying which kind they
    are is how -2..+2 gets compared against a 1,345..1,355 level guide. The caller refuses on it.

    THE PERIOD RIDES WITH THEM TOO (2026-08-12), for the same reason and after the same failure:
    the release can guide a YEAR while CIQ guides a QUARTER, and two numbers covering different
    spans cannot agree no matter how well each is parsed."""
    for r in releases:
        for g in r.guidance:
            if g.metric in _REVENUE_LINE_METRICS:
                return (g.low, g.high, g.qualitative, getattr(g, "basis", "level"),
                        getattr(g, "period", None))
    return (None, None, False, "level", None)


#: Display cap for a qualitative guide's verbatim in the MAIN BODY. The stored text is a 200-char
#: raw extract; the whole of it is not a decision value.
_GUIDE_VERBATIM_CAP = 110


def _current_guide(releases: list[ReleaseExtract]) -> Sourced[str]:
    """(item 1 clause (c)) The guide from the LATEST results filing that carries one.

    THE SPLIT. `_revised_guidance` walks the DRAWDOWN 8-Ks and answers "what did management say in
    the filing that caused the gap" — drawdown-vintage by construction, and correct as built. This
    answers the other question its docstring also claimed: "the verdict-relevant number", i.e. the
    guide that GOVERNS today. The two coincide until guidance is revised after the drawdown, and
    then they diverge — SMPL's bear argued April's guide while the base used July's, both in one
    document, neither labelled.

    Selection is by the release's OWN `filed` date, never by list position and never by parsing the
    accession out of `source_ref`. Absence is ATTRIBUTED, never silent."""
    dated = [r for r in releases if r.guidance and r.filed is not None]
    if not dated:
        undated = [r for r in releases if r.guidance]
        if undated:
            return Sourced.unknown(
                note=f"{len(undated)} release(s) carry a guide but none carries a filing date — "
                     "cannot say which governs")
        return Sourced.unknown(
            note=f"no guide in any of the {len(releases)} parsed release(s)" if releases
                 else "no EX-99.1 release parsed")
    latest = max(dated, key=lambda r: r.filed or date.min)
    filed = latest.filed
    assert filed is not None                            # `dated` filtered on it
    parts = []
    for g in latest.guidance:
        # REVIEW FIX (#254). The first cut printed "metric period: — $M" for BOTH a
        # qualitative guide and a high-only range: it read `low`/`high` and ignored the
        # `qualitative` flag and the `verbatim` text the model already carries. Live on 6 rows
        # across 4 names (AORT, IT, MVST, VITL) — every one of them qualitative — so a
        # reaffirmed-outlook statement rendered as an em-dash with a currency unit stuck to it:
        # a missing NUMBER where the filer made a non-numeric statement, which is a different
        # claim and the wrong one.
        if g.qualitative or (g.low is None and g.high is None):
            # the verbatim is a 200-char raw extract and carries page furniture ("Page 2 of 13 …")
            # on real filings, so cap it for a MAIN-BODY slot. Truncation is MARKED, never silent,
            # and the untruncated text stays in the release record.
            said = " ".join((g.verbatim or "").split())
            if len(said) > _GUIDE_VERBATIM_CAP:
                said = said[:_GUIDE_VERBATIM_CAP].rstrip() + "… (full text in the release record)"
            parts.append(f"{g.metric} {g.period}: {said}" if said
                         else f"{g.metric} {g.period}: qualitative guide, no figure given")
            continue
        if g.low is not None and g.high is not None:
            rng = f"{g.low:,.1f}–{g.high:,.1f}"
        elif g.low is not None:
            rng = f"≥ {g.low:,.1f}"          # a floor is not a point estimate; say which it is
        else:
            rng = f"≤ {g.high:,.1f}"         # was silently dropped — the bound is the whole guide
        parts.append(f"{g.metric} {g.period}: {rng} {g.unit}".strip())
    return Sourced.present(
        "; ".join(parts),
        source_ref=f"{latest.source_ref} (filed {filed.isoformat()})")


# ITEM 18 — the key an underwrite record uses for its typed covenant-basis leverage, under 18a's
# `facts` schema. NO committed record carries it today (the seven hold cash_interest, cash_tax_rate,
# d_and_a, d_and_a_ratio, diluted_shares, ltm_revenue, net_debt, share_growth, burn_to_breakeven),
# so every name currently takes the legacy branch. Named here so the typed branch is reachable the
# day an analyst writes one, rather than requiring a code change then.
COVENANT_LEVERAGE_FACT = "covenant_leverage"


def _covenant_basis(card: Any | None) -> str | None:
    """ITEM 18 — NO FALSE UNKNOWN. What the covenant-basis line may honestly say, given the fund's
    own underwrite record.

    > Any field the dossier would render as UNKNOWN must first be checked against the record.

    Three states, and only the middle one is new:

    * **no record** → None, and the historical "UNKNOWN (not disclosed)" stands. Most names are
      never underwritten; with nothing to contradict it, the line is honest.
    * **record, no typed fact** (every committed record today) → the vintage message. The record
      predates 18a's typed fields, so the basis exists only as V-row prose. UNKNOWN is FALSE here —
      that is the SMPL incident exactly.
    * **record with the typed fact** → render it, source-bound.

    NO PROSE IS READ. The legacy branch is chosen by the ABSENCE of a typed fact, never by
    inspecting the thesis text — a prose reader is out of scope by decision, and it would be the
    display-string parse this repo forbids besides."""
    if card is None:
        return None
    fact = (getattr(card, "facts", None) or {}).get(COVENANT_LEVERAGE_FACT)
    if fact is None:
        return primary_source.COVENANT_BASIS_NO_STRUCTURED_SOURCE
    return f"{fact.value:g}{fact.unit} ({fact.basis})"


def _primary_source(
    record: DataRecord, edgar: EdgarClient, http: CachedHttp,
    bundle: CiqBundle, reference_date: date, mech: MechanicalLayer,
    card: Any | None = None,
) -> tuple[PrimarySource, float, OperatingDriversExtract]:
    """(RC-1 C) Fetch the primary-source filings (recent 8-K EX-99.1 releases + the latest 10-Q),
    parse them, and run the four cross-source derivations over them + the CIQ/EDGAR mechanical
    layer. RESILIENT TO SOURCE MISSES: any fetch/parse miss becomes an honest UNKNOWN line + a QA
    flag — a missing source never aborts the assembly.

    **ONE DELIBERATE ABORT (item 18), and it is NOT a source miss.** If the underwrite record holds
    a typed covenant fact and this function would still emit ``covenant basis: UNKNOWN``, it RAISES.
    The resilience rule exists so an ABSENT source degrades to an honest UNKNOWN; it is not licence
    to ship a DISHONEST one. Bare ``ValueError`` on purpose — ``DossierAssemblyError`` lives in
    ``assemble.py``, which imports this module, so raising it here would cycle; ``assemble_cohort``
    collects either as a per-name error and the cohort continues.

    Also assembles the (PR-B) operating-driver rows over the SAME already-fetched text
    (A1 releases + A2 10-Q MD&A) plus CIQ Key Developments (A3) — zero extra I/O. Returns
    (PrimarySource, fetch-latency seconds, OperatingDriversExtract)."""
    t0 = time.perf_counter()
    cik = record.identity.cik
    qa: list[str] = []
    releases: list[ReleaseExtract] = []
    filing: FilingSectionExtract | None = None
    filing_as_of: date | None = None  # the parsed 10-Q's period end — the maturity-wall 'as of'
    # (PR-B) operating-driver rows accumulate over the same fetched text; a per-source miss flags.
    driver_rows: list[OperatingDriver] = []
    driver_qa: list[str] = []
    saw_release = saw_10q = False
    # (1) recent 8-K EX-99.1 earnings/event releases (one failing exhibit never drops the rest) -
    if cik:
        try:
            for f in edgar.recent_filings(cik, forms=("8-K",))[:10]:
                if not (set(f.items) & {"2.02", "8.01"}):
                    continue
                try:
                    urls = release_parse.exhibit_991_urls(http, cik, f.accession)
                    if not urls:
                        # DISCLOSE the empty read. An 8-K carrying item 2.02/8.01 almost always
                        # furnishes a press release, so finding none is a detection miss far more
                        # often than a filing that truly has none — and a silent zero here reads
                        # downstream as "this company said nothing", which is a different claim.
                        qa.append(f"primary-source: 8-K {f.accession} carries "
                                  f"{'/'.join(sorted(set(f.items) & {'2.02', '8.01'}))} but no "
                                  f"EX-99.1 exhibit was found")
                    for url in urls:
                        txt = normalize_text(html_to_text(http.get_text(url, ttl_seconds=_PS_TTL)))
                        src = f"8-K {f.accession} EX-99.1"
                        rel = release_parse.parse_release(txt, source_ref=src)
                        # the filing's own date, so a consumer can pick the FRESHEST guide
                        # without parsing the accession out of source_ref
                        releases.append(rel.model_copy(update={"filed": f.filing_date}))
                        saw_release = True
                        driver_rows += release_parse.operating_drivers(txt, source_ref=src)  # A1
                except Exception as exc:
                    qa.append(f"primary-source: EX-99.1 fetch/parse failed for 8-K {f.accession} "
                              f"({type(exc).__name__})")
        except Exception as exc:
            qa.append(f"primary-source: 8-K enumeration failed ({type(exc).__name__})")
    # (2) latest 10-Q filing sections ------------------------------------------------------------
    if cik:
        try:
            qs = edgar.recent_filings(cik, forms=("10-Q",))
            if qs and qs[0].primary_doc:
                url = filing_sections.filing_url(cik, qs[0].accession, qs[0].primary_doc)
                txt = normalize_text(html_to_text(http.get_text(url, ttl_seconds=_PS_TTL)))
                src = f"10-Q {qs[0].accession}"
                filing = filing_sections.parse_filing_sections(txt, source_ref=src)
                filing_as_of = qs[0].report_date  # the maturity-wall 'as of' — panel window base
                saw_10q = True
                driver_rows += filing_sections.results_attribution(txt, source_ref=src)  # A2
        except Exception as exc:
            qa.append(f"primary-source: latest 10-Q fetch/parse failed ({type(exc).__name__})")
    driver_rows += ciq_sheets.key_development_drivers(bundle)  # A3 (CIQ Key Developments)
    # per-source honest-miss flags (a fetched source that yielded no driver row) — never a fake row
    if saw_release and not any(r.source_ref.startswith("8-K") for r in driver_rows):
        driver_qa.append("operating-drivers: no anchored pattern matched — EX-99.1 pricing/KPI")
    if saw_10q and not any(r.source_ref.startswith("10-Q") for r in driver_rows):
        driver_qa.append("operating-drivers: no anchored pattern matched — 10-Q MD&A attribution")
    if not driver_rows:
        driver_qa.append("operating-drivers: no rows extracted (releases/10-Q/KD all missed)")
    op_drivers = OperatingDriversExtract(rows=driver_rows, qa_flags=driver_qa)
    latency = time.perf_counter() - t0
    facts = _companyfacts_or_none(edgar, cik)
    # (3) derivations over structured inputs (never re-parsing a display string) -----------------
    fcf = ciq_sheets.free_cash_flow(bundle)
    fcf_sign = fcf.value > 0 if fcf.value is not None else None
    self_fund = primary_source.self_funding(_latest_quarter_ocf_positive(facts), fcf_sign)
    # wall coherence — filing ≤12m vs CIQ panel same-window, tranche-matched, exclusive boundary.
    # Balance = the 10-Q's OWN period end (the wall's 'as of'), NOT the latest companyfacts instant
    # (which can be a later 10-K, shifting the window and dropping the 41.7M convertible bond).
    balance = filing_as_of or _latest_balance_date(facts)
    cs_layer = mech.capital_structure
    instruments = (cs_layer.instruments.value
                   if cs_layer is not None and cs_layer.instruments.value is not None else [])
    panel = [primary_source.PanelInstrument(
                i.description, i.principal_musd,
                date.fromisoformat(i.maturity_date) if i.maturity_date else None)
             for i in instruments]
    wall_qa: list[str] = []
    mw = filing.maturity_wall if filing is not None else None
    if balance is not None:
        filing_conv = next((t.amount for t in (mw.tranches if mw else [])
                            if "convert" in t.name.lower()), None)
        wall_line, wall_qa = primary_source.wall_coherence(
            mw.within_12m_total if mw else None, panel, balance=balance,
            filing_convertible=filing_conv,
            panel_convertible_principal=primary_source.panel_convertible_principal(panel, balance))
    else:
        wall_line = "wall coherence: UNKNOWN — no EDGAR balance-sheet date"
    qa += wall_qa
    # basis triangulation — each leverage row basis-labeled; FY margins from the release
    nde = mech.leverage_survival.net_debt_to_ebitda if mech.leverage_survival is not None else None
    tde = ciq_sheets.comps_total_debt_ebitda_value(bundle)
    net_debt = ciq_sheets.net_debt(bundle)
    fy = _fy_reconciliation(releases)
    tri = primary_source.basis_triangulation(
        f"{nde.value}x" if nde is not None and nde.status is SourceStatus.PRESENT else None,
        f"{tde.value}x" if tde.status is SourceStatus.PRESENT else None,
        net_debt.value if net_debt.status is SourceStatus.PRESENT else None,
        _ltm_adj_ebitda(releases),
        gaap_gross_margin=fy.get("gross margin"), impairment=_fy_impairment(releases),
        revenue=fy.get("revenue"), covenant_basis=_covenant_basis(card))
    # ITEM 18's RED, as a coherence assertion rather than a hope. It can only fire if this wiring
    # breaks — a typed fact present while the rendered line still claims ignorance of it. That is
    # the false UNKNOWN, and a build that would print one must fail rather than ship the page.
    if (card is not None
            and (getattr(card, "facts", None) or {}).get(COVENANT_LEVERAGE_FACT) is not None
            and f"covenant basis: {primary_source.COVENANT_BASIS_UNKNOWN}" in tri):
        raise ValueError(
            f"{record.identity.ticker}: the underwrite record holds a typed "
            f"{COVENANT_LEVERAGE_FACT} fact and the dossier would still render "
            f"'covenant basis: {primary_source.COVENANT_BASIS_UNKNOWN}' — a FALSE UNKNOWN "
            "(item 18). Refusing the build: a gap invites a look, an UNKNOWN closes the question.")
    # guide verification — CIQ revenue guide (point OR range) vs the release guide + prior-FY actual
    ciq_lo, ciq_hi, ciq_period = ciq_sheets.revenue_guide_lohi(
        bundle, reference_date=reference_date)
    rel_lo, rel_hi, rel_qual, rel_basis, rel_period = _release_revenue_guide(releases)
    guide = primary_source.guide_verification(
        "revenue", ciq_lo, ciq_hi,
        prior_fy_actual=fy.get("revenue"), release_qualitative=rel_qual,
        release_low=rel_lo, release_high=rel_hi, release_basis=rel_basis,
        ciq_period=ciq_period, release_period=rel_period)
    ps = PrimarySource(
        releases=releases, filing=filing,
        self_funding=Sourced.present(
            self_fund, source_ref="EDGAR latest-Q OCF sign + CIQ LTM FCF sign"),
        wall_coherence=Sourced.present(
            wall_line, source_ref="10-Q maturity wall vs CIQ capital panel (same window)"),
        basis_triangulation=Sourced.present(
            tri, source_ref="CIQ leverage bases + release LTM adj-EBITDA/margins"),
        guide_verification=Sourced.present(
            guide, source_ref="CIQ revenue guide vs release actual/outlook"),
        current_guide=_current_guide(releases),
        qa_flags=qa)
    return ps, latency, op_drivers


_ASSEMBLY_PRICE_STALE_DAYS = 7  # one weekly refresh cadence + a weekend; older ⇒ refresh was missed


def _price_stale_note(last_close: date | None, today: date) -> str | None:
    """Fail-loud staleness at ASSEMBLY time (vs today, not the reference date): an as-of document
    may legitimately trail the screen date, but a CMP printed from a close older than one refresh
    cadence silently misleads. Returns the caveat text, or None when fresh/unknowable."""
    if last_close is None:
        return None
    gap = (today - last_close).days
    if gap <= _ASSEMBLY_PRICE_STALE_DAYS:
        return None
    return (
        f"PRICE STALE AT ASSEMBLY: last stored close {last_close} is {gap} calendar days before "
        f"assembly — run `vinci refresh` before assembling"
    )


def _stock_info(
    record: DataRecord, store: Store, edgar: EdgarClient, bundle: CiqBundle,
    reference_date: date, market_cap: Sourced[float], *, today: date | None = None,
) -> StockInfo:
    """(Phase-2) The market-data 'stock info' box: CMP + 52-week range (EOD price features), shares
    outstanding (EDGAR XBRL), book value/share + market cap (CIQ). Each value is source-bound; a
    missing source stays UNKNOWN — never fabricated. Assemble/inform only: no gate, no conclusion.
    The 52-week high/low defer to UNKNOWN without ~a year of bars (the price-features rule)."""
    bars = store.get_price_history(record.identity.internal_id)
    cap_val = market_cap.value if market_cap.status is SourceStatus.PRESENT else None
    feats = compute_price_features(
        bars, reference_date=reference_date,
        staleness_days=get_config().price_staleness_days, market_cap=cap_val)
    sym = record.identity.eod_symbol
    shares = _edgar_shares_outstanding(edgar, record.identity.cik, as_of=reference_date)
    # THE DEPTH-STAGE BRIDGE, and only when EDGAR has nothing usable. A multi-class filer may stop
    # tagging the undimensioned cover-page count altogether (Visa: nothing since 2010, across a
    # 4-for-1 split), and the CIQ panel then carries the only current basis we have. It is taken
    # from the SAME ROW as the cap, so cap ÷ shares reproduces that panel's own close and the
    # reconciliation is coherent by construction rather than by luck.
    shares_src = "EDGAR XBRL shares outstanding"
    if not (shares and shares > 0):
        bridged = ciq_sheets.comps_shares_outstanding(bundle)
        if bridged.status is SourceStatus.PRESENT and (bridged.value or 0) > 0:
            shares = bridged.value
            shares_src = bridged.source_ref or "CIQ Comparable Analysis→Financial Data"
    price = _sourced(feats.last, source_ref=f"EOD {sym} last close")
    stale = _price_stale_note(feats.last.as_of, today or date.today())
    if stale and price.status is SourceStatus.PRESENT:
        price = price.model_copy(update={"note": stale})
    return StockInfo(
        price=price,
        high_52w=_sourced(feats.high_52w, source_ref=f"EOD {sym} 52-week high"),
        low_52w=_sourced(feats.low_52w, source_ref=f"EOD {sym} 52-week low"),
        shares_out=(
            Sourced.present(float(shares), source_ref=shares_src)
            if shares and shares > 0
            else Sourced.unknown(
                note="no usable share count — the EDGAR cover-page tag is absent or older than "
                     f"{_SHARES_MAX_AGE_DAYS}d, and no CIQ Financial Data panel supplies one")),
        book_value_ps=ciq_sheets.book_value_per_share(bundle),
        market_cap=market_cap,
        as_of=feats.last.as_of,
        # The CAP's own vintage, from the SAME derivation that stamps its source_ref (O3). Two
        # dates sit on the Snapshot line — a live close and a frozen panel — and until now only
        # the price's was structured, so the clause-(e) label borrowed a neighbouring panel's.
        market_cap_as_of=ciq_sheets.comps_as_of_date(bundle)[0],
    )



def _peer_capital_intensity(peers: Any, resolver: EntityResolver,
                            edgar: EdgarClient) -> Any:
    """The peer acquired-asset comparison, or None when the comps grid is absent.

    NONE MEANS NOT BUILT, never "the peers carry nothing" — the grid is the only source of peer
    tickers, so without it there is no set to compare against and a written block would be a claim
    about peers we never looked at.
    """
    grid = getattr(getattr(peers, "peer_grid", None), "value", None)
    if not grid:
        return None
    return build_peer_capital_intensity(
        grid, resolve=resolver.resolve_ticker, companyfacts=edgar.companyfacts)


#: How far back a former registrant name still marks the page. Sized to the DEEPEST window any
#: rendered block reads, which is the mid-cycle margin anchor (`midcycle.MIN_YEARS` = 10 fiscal
#: years) — that band feeds the R1 recipe's valuation, so a rename inside it can contaminate the
#: multiple itself, not merely a trend chart. The first cut used ~6y ("the 5-fiscal-year trend"),
#: which left renames 7-9 years old silently unmarked while the mid-cycle band averaged across two
#: businesses (review, #558). +1 year of report/filing lag. Face-validity; never outcome-tuned.
_FORMER_NAME_LOOKBACK_DAYS = (_MIDCYCLE_MIN_YEARS + 1) * 365

#: Tokens that style a registrant record without naming the business — legal-form suffixes plus
#: EDGAR's own "ET AL". Every member was demanded by a REAL restyle observed live (LLY files as
#: "LILLY ELI & CO ET AL"); the set stays CLOSED — grow it only from an observed false positive.
#:
#: NEITHER "holdings" NOR "group" IS A MEMBER, and that is deliberate: both are how shell and
#: SPAC vehicles are actually named (MVST's Tuscan Holdings, FUBO's FaceBank Group / Pulse
#: Evolution Group), so stripping either erases exactly the class this marker exists to catch —
#: "Ajax Capital Group, Inc." -> "Ajax Capital, Inc." is a real predecessor that would collapse to
#: silence. "group" was briefly a member on a justification traced to a MISIDENTIFIED CIK (Cowen
#: Group, probed in place of Artivion); removing it changes no live corpus result (review, #558).
_REGISTRANT_STYLE_TOKENS = frozenset(
    {"inc", "incorporated", "corp", "corporation", "co", "company", "ltd", "limited",
     "llc", "lp", "plc", "sa", "nv", "ag", "et", "al"})

#: EDGAR's conformed filer-record suffix: a state-of-incorporation marker appended to the NAME,
#: in either the open form ("APPLE COMPUTER INC/ FA", "fuboTV Inc. /FL") or the closed one
#: ("PITNEY BOWES INC /DE/", which this repo's own graph_coverage.json carries). The first cut
#: matched only the open form, so the closed one produced a false predecessor (review, #558).
_TRAILING_FILER_SUFFIX = re.compile(r"\s*/\s*[A-Za-z]{1,4}\s*\.?\s*/?\s*$")


def _registrant_key(name: str) -> frozenset[str]:
    """Style-insensitive identity for a registrant name, as a token set.

    Four restyle classes — none a predecessor — must collapse to the name in force: casing and
    punctuation ("APPLE INC" vs "Apple Inc."), word order (LLY filed as "LILLY ELI & CO" until
    2019), a trailing filer-record suffix (see above), and diacritics (a conformed
    "Societe Generale" against a later "Société Générale" — ASCII-only splitting shredded the
    accented form into fragments and produced a false predecessor on any such filer, which the
    US-only live sweep could not surface; review, #558).
    """
    bare = _TRAILING_FILER_SUFFIX.sub("", name)
    folded = unicodedata.normalize("NFKD", bare.casefold())
    stripped = "".join(c for c in folded if not unicodedata.combining(c))
    return frozenset(
        t for t in re.findall(r"[^\W_]+", stripped, flags=re.UNICODE)
        if t not in _REGISTRANT_STYLE_TOKENS)


def _former_name_flags(
    edgar: EdgarClient, cik: str, reference_date: date
) -> list[str]:
    """Human caveats for prior registrant names in force inside the rendered lookback, oldest first.

    AS-OF DISCIPLINE, the same rule the rest of this module runs on. A span that ends AFTER the
    reference date has not happened yet from the page's point of view: assembling AORT at a 2021
    reference used to announce the 2022-01-06 CryoLife -> Artivion rename, i.e. told the reader
    about their own future (review, #558 — the #416/#426 lookahead class). Only spans that CLOSED
    on or before the reference date are predecessors, and the baseline they are compared against is
    the name in force AT that date, never today's.

    The current name comes from the submissions payload itself, never from ``identity.name``:
    that field is resolver output persisted inside stored records, so a rename that happened after
    the record was screened — the freshest and most consequential case — would leave it holding the
    OLD name, which then matched the former row and silently suppressed the marker.

    A FETCH failure and a PARSE failure are reported differently: a systematic EDGAR format change
    must not read as one flaky request, which is what a blanket catch made it look like.
    """
    try:
        history = edgar.registrant_history(cik)
    except (HttpError, OSError, KeyError) as exc:
        return [f"former-name check unavailable ({type(exc).__name__}) — submissions feed did not "
                f"answer; rename history not checked"]
    except (ValueError, TypeError) as exc:
        return [f"former-name check FAILED TO PARSE ({type(exc).__name__}) — the submissions "
                f"rename rows did not match their expected shape; rename history not checked"]

    # the name in force AT the reference date: the span containing it, else today's current name
    covering = [r for r in history.former
                if r.to_date >= reference_date and (r.from_date or date.min) <= reference_date]
    as_of_name = min(covering, key=lambda r: r.to_date).name if covering else history.current

    cutoff = reference_date - timedelta(days=_FORMER_NAME_LOOKBACK_DAYS)
    cur = _registrant_key(as_of_name)
    # ONE row per registrant, the latest-closing. Spans are NEVER merged: a CIK that filed as Foo,
    # then Bar, then Foo again would otherwise print a single "Foo (first-from -> last-to)" span
    # that is false across the middle — and the caveat's whole value is being source-bound to a
    # literal filed span.
    best: dict[frozenset[str], FormerName] = {}
    for r in history.former:
        key = _registrant_key(r.name)
        if not key or key == cur or not (cutoff <= r.to_date <= reference_date):
            continue
        if key not in best or r.to_date > best[key].to_date:
            best[key] = r
    out = []
    for r in sorted(best.values(), key=lambda x: x.to_date):
        # EDGAR really does ship INVERTED rows (CIK 0000860730 Columbia/HCA: from 2000-05-26 to
        # 2000-05-19; COPT and TotalEnergies carry others). Printing "(2000-05-26 -> 2000-05-19)"
        # reads as a pipeline bug at the exact moment the caveat asks to be trusted as source-bound,
        # so an unusable start is dropped to the same "until <end>" form an absent one already uses
        # — the end date is the reliable field and the only one the window is measured on.
        usable_from = r.from_date if r.from_date is not None and r.from_date <= r.to_date else None
        since = f"{usable_from.isoformat()} \u2192 " if usable_from is not None else "until "
        span = f"{since}{r.to_date.isoformat()}"
        out.append(
            f'former registrant name: this CIK filed as "{r.name}" ({span}) '
            f"\u2014 multi-year series on this page may span a different underlying business; "
            f"verify continuity across the change (SEC submissions formerNames, CIK {cik})")
    return out


def assemble_mechanical(
    record: DataRecord,
    *,
    store: Store,
    edgar: EdgarClient,
    http: CachedHttp,
    finra: CachedHttp,
    graph: ExposureGraph,
    resolver: EntityResolver,
    bundle: CiqBundle,
    reference_date: date,
    screen_cap_usd: float | None = None,
    card: Any | None = None,
) -> tuple[MechanicalLayer, list[str]]:
    """Assemble the source-bound mechanical layer (no LLM) + any flags for human review (e.g. a
    distorted-P/E-basis warning). No conclusions. ``screen_cap_usd`` is the ranker's frozen
    screen-time cap — the benchmark-band fallback when the CIQ cap is absent (see below)."""
    # every "at the current price" reading below — P/E, its percentile, the adjusted and forward
    # multiples, the conflict caveat — reads the latest stored close, the one the price box shows
    record = _at_latest_close(record, store, edgar)
    # the catalyst 8-K's 99.1 (revised guidance) is fetched first: its adjusted EBITDA/EPS feed the
    # adjusted-basis multiples + leverage, which in turn RESOLVE the GAAP-only caveats below.
    drawdown, drawdown_flags = _drawdown_cause(record, edgar, http)
    adj_eps, adj_ev, adj_lev = _adjusted_facts(
        record, edgar, drawdown.revised_guidance, reference_date)
    pe_recon = _pe_reconciliation(record, edgar, bundle, drawdown.revised_guidance)
    # EDGAR fundamentals fallback: when the CIQ Financials subsheets are present-but-empty while CIQ
    # multiples ARE populated, fill free_cash_flow / margin_trend / multi_year_trajectory from EDGAR
    # XBRL. The "multiples present" signal is Financials→Multiples OR the comps Trading Multiples —
    # either proves the workbook is pulled (both read PRESENT for AORT). CIQ multiples stay primary;
    # a PRESENT CIQ field is never overridden (_prefer_ciq).
    peer_comps = ciq_sheets.peer_comps(bundle)
    key_ratios = ciq_sheets.key_ratios(bundle)  # (Phase-2) CIQ Ratios panel: RoE/RoCE/D:E/dividend
    return_ratios = ciq_sheets.return_ratios(bundle)  # (Phase-4) same panel, per-period
    ciq_fcf = ciq_sheets.free_cash_flow(bundle)
    ciq_margin = ciq_sheets.margin_trend(bundle)
    ciq_traj = ciq_sheets.multi_year_trajectory(bundle)
    edgar_fb = edgar_fundamentals.build_fallback(
        multiples=[ciq_sheets.ev_ebitda_current(bundle), peer_comps.trading_multiples],
        ciq_fundamentals=[ciq_fcf, ciq_margin, ciq_traj],
        facts_fn=lambda: _companyfacts_or_none(edgar, record.identity.cik),
    )
    fcf = _prefer_ciq(ciq_fcf, edgar_fb.free_cash_flow() if edgar_fb else None)
    margin = _prefer_ciq(ciq_margin, edgar_fb.margin_trend() if edgar_fb else None)
    trajectory = _prefer_ciq(ciq_traj, edgar_fb.multi_year_trajectory() if edgar_fb else None)
    # Flag the cross-source comparison ONLY when an EDGAR field reached the dossier (CIQ was
    # empty for it). Keying on the RESOLVED fields — not "EDGAR could supply" — avoids a false basis
    # warning when CIQ won every field. fundamental_deltas only (trading_multiples is CIQ-vs-CIQ).
    edgar_used = any(
        (s.source_ref or "").startswith("EDGAR XBRL companyfacts")
        for s in (fcf, margin, trajectory)
    )
    if edgar_used:
        peer_comps = edgar_fundamentals.flag_deltas_basis(peer_comps)
    quality = _quality(
        record, edgar, bundle, reference_date, adj_lev,
        fcf=fcf, margin=margin, trajectory=trajectory,
    )
    implied_val = ciq_sheets.implied_valuation(bundle, peer_comps.comparability)
    # cap-band benchmark for the dossier surface (exhibit + 180d relative) — the monitor's policy
    # applied at the reference date's CIQ cap; one yardstick across both consumers below.
    bench, bench_basis = _resolve_benchmark(
        implied_val.market_cap, reference_date, screen_cap_usd=screen_cap_usd)
    today = date.today()  # assembly instant — the staleness guard compares the store against NOW
    # (F) positioning inputs slotted into the catalyst path — free DATED feeds: EDGAR Form 4 insider
    # activity + FINRA short interest (DTC vs the screen ADV). Counts/shares/dates only.
    catalyst = _catalyst_path(
        bundle, reference_date,
        insider_activity=_insider_activity(edgar, http, record.identity.cik, reference_date),
        short_interest=_short_interest(
            finra, record, reference_date,
            # SAME as-of AS THE STOCK-INFO CALL. Left undated, this resolved the staleness bound
            # against `date.today()`, so a name whose cover-page count sits near the bound would
            # get a short-interest denominator depending on WHEN the build ran — a re-assembly
            # flipping with no data change, in a repo whose whole point is as-of discipline.
            shares_out=_edgar_shares_outstanding(
                edgar, record.identity.cik, as_of=reference_date)),
    )
    valuation = _valuation(
        record, bundle, adj_eps, adj_ev, pe_note=pe_recon[1] if pe_recon else None)
    # (G) price-inverted expectations (multiples-space) attach to Valuation. Built from already-
    # assembled fields only (peer multiples + the forward ladder + the derived TEV) — no extraction.
    valuation = valuation.model_copy(
        update={"implied_expectations":
                _implied_expectations(peer_comps, catalyst, implied_val, bundle,
                                     store.get_price_history(record.identity.internal_id))})
    mech = MechanicalLayer(
        valuation=valuation,
        quality=quality,
        concentration=_concentration(bundle),
        peer_comps=peer_comps,
        drawdown_cause=drawdown,
        idiosyncratic_vs_shared=_idiosyncratic_vs_shared(
            record, store, graph, resolver, reference_date,
            bench=bench, bench_basis=bench_basis,
        ),
        consensus_context=_consensus(bundle),
        catalyst_path=catalyst,
        # B2 unified leverage & survival (both bases + credit health) + B3 CIQ implied valuation
        # (posed; the comparability gate from peer_comps renders on its header).
        leverage_survival=_leverage_survival(quality, bundle),
        implied_valuation=implied_val,
        # C — Financial-Summary appendix (actuals + consensus), reconciled vs the implied bridge.
        financial_summary=_financial_summary(bundle, implied_val),
        # E — structured capital structure (instruments + summary + maturity 8-Ks + pointers).
        capital_structure=_capital_structure(record, edgar, http, bundle, reference_date),
        # Capital created or destroyed — EDGAR XBRL only. `build_capital_allocation` is total on a
        # facts dict (every field degrades to UNKNOWN-with-reason), so an absent companyfacts
        # yields a fully-stated block rather than a missing one.
        capital_allocation=build_capital_allocation(
            _companyfacts_or_none(edgar, record.identity.cik) or {}),
        # FORWARD dilution capacity — the buyback block's mirror. Filing-index only (bounded,
        # cached); "none on file" is a PRESENT finding, UNKNOWN is reserved for a failed read.
        dilution_pipeline=_dilution_pipeline(edgar, record.identity.cik, reference_date),
        ownership_events=_ownership_events(edgar, record.identity.cik, reference_date),
        sbc=_sbc(edgar, record.identity.cik, reference_date),
        # Peer acquired-asset intensity. Needs the comps grid (only it carries peer TICKERS) plus
        # one cached EDGAR call per peer; absent grid -> None, which keeps its NOT-BUILT meaning.
        peer_capital_intensity=_peer_capital_intensity(peer_comps, resolver, edgar),
        management_commentary=ciq_sheets.management_commentary(bundle),
        key_ratios=key_ratios,  # (Phase-2) the Motilal-style CIQ Ratios panel
        return_ratios=return_ratios,  # (Phase-4) per-period return-ratio series (chart + table)
        stock_info=_stock_info(  # (Phase-2) CMP + 52wk range + shares + book value + cap
            record, store, edgar, bundle, reference_date, implied_val.market_cap, today=today),
        # (Brief) 52-week rebased price path — name vs the cap-band benchmark (the idio closes).
        stock_performance=_stock_performance(
            record.identity, store, reference_date, bench=bench),
    )
    # (RC-1 C) primary-source layer — fetch 8-K EX-99.1 releases + the latest 10-Q, parse, and run
    # the four cross-source derivations over them + this mechanical layer. Resilient: a fetch/parse
    # miss becomes an UNKNOWN line + QA flag, never an abort. Attached via model_copy (frozen).
    primary, ps_latency, op_drivers = _primary_source(
        record, edgar, http, bundle, reference_date, mech, card)
    mech = mech.model_copy(update={
        "primary_source": primary, "operating_drivers": op_drivers})  # (PR-B) mechanism tier
    mech = _enrich_drawdown_drivers(mech, primary)  # (B1) gap-downs → parsed EX-99.1 drivers
    # (catalyst calendar) dated events + what each tests — needs drawdown_cause (the guide) and
    # capital_structure (maturities), both on mech by now; its misses ride the QA channel.
    calendar = _catalyst_calendar(edgar, record.identity.cik, reference_date, mech)
    mech = mech.model_copy(update={"catalyst_calendar": calendar})
    flags: list[str] = list(primary.qa_flags)
    flags += guidance_refusal_flags(primary.releases)
    flags += op_drivers.qa_flags  # (PR-B) operating-driver per-source honest-miss flags → QA
    flags += calendar.qa_flags  # (catalyst calendar) cadence/maturity honest-miss flags → QA
    si_asof = mech.stock_info.as_of if mech.stock_info is not None else None
    if (stale := _price_stale_note(si_asof, today)) is not None:
        flags.append(f"stock-info: {stale}")  # loud twin of the CMP-row note — machine-visible
    flags.append(f"primary-source: {len(primary.releases)} EX-99.1 release(s) + "
                 f"{'1' if primary.filing is not None else '0'} 10-Q parsed "
                 f"(+{ps_latency:.1f}s fetch)")
    if pe_recon is not None:
        flags.append(pe_recon[0])
    flags += _eps_caveat_flags(
        record, bundle, eps_resolved=adj_eps.status is SourceStatus.PRESENT,
        ltm_gaap_eps=_ltm_gaap_eps(mech.financial_summary))
    # the reported-leverage caveat is an open warning only while the covenant basis isn't shown;
    # reads the RESOLVED ratio so the flag can't quote a different number than the field shows
    if adj_lev.status is not SourceStatus.PRESENT and (
        lev := _leverage_basis_flag(mech.quality.net_debt_to_ebitda)
    ):
        flags.append(lev)
    # data-integrity check on the name's current EV/EBITDA: a stale Financials Close (predates the
    # reference date, so its "current" multiple + own-history range are stale) and/or a material gap
    # vs the current comps figure — flag so the human verifies rather than trusting one silently.
    if (ev_flag := _ev_ebitda_integrity_flag(bundle, reference_date)) is not None:
        flags.append(ev_flag)
    # catalyst-path staleness: the Estimates export's as-of vs the reference date (shared 45d knob).
    if mech.catalyst_path is not None and (
        cat_flag := _catalyst_stale_flag(mech.catalyst_path, reference_date)
    ):
        flags.append(cat_flag)
    # panel-freshness (the SMPL 2026-07-24 incident guard): a CIQ valuation panel that predates the
    # latest EARNINGS PRINT — orthogonal to the reference-date staleness above (a panel can sit
    # within the 45d reference tolerance yet still predate a print that landed after both).
    if (fresh_flag := _panel_freshness_flag(
        mech.valuation.implied_expectations if mech.valuation is not None else None,
        _latest_earnings_print(edgar, record.identity.cik),
    )) is not None:
        flags.append(fresh_flag)
    # former-registrant-name vintage (the reverse-merger class): multi-year blocks on this page can
    # silently span a DIFFERENT underlying business filed under the same CIK — FUBO (FaceBank),
    # TECX (AvroBio), ORKA (ARCA) are the live proof. The marker states the filed fact and directs
    # verification; it never asserts a mechanism (a bare rename — AAPL 2019 — is not a predecessor).
    flags += _former_name_flags(edgar, record.identity.cik, reference_date)
    flags += drawdown_flags  # degraded-feed twin of the UNKNOWN drawdown-cause note
    return mech, flags
