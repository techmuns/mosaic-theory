"""Tier-3 — the DETERMINISTIC structural-disqualifier channel (DEMOTE-ONLY).

Reads the *free* EDGAR 8-K full text (item codes + body) and the shares-outstanding series for each
candidate and flags TERMINAL/STRUCTURAL signals only — going-concern, restatement (Item 4.02),
auditor resignation/dismissal (Item 4.01), delisting/deficiency (Item 3.01), and a dilution
death-spiral (shares rising into a falling price). A fired flag SINKS the name (caps its priority
score + sorts it to the bottom) so the team does not waste deep-pull time on a dead name.

Fenced hard, like the dossier-assembler and the LLM cause channel:
- It can ONLY demote. There is NO promote path — the classifier returns a flag (sink) or ``None``
  (UNCLASSIFIED → zero effect). It never raises a name's rank.
- Default is UNCLASSIFIED (``None``): only an EXPLICITLY matched signal demotes; never fabricated.
- It NEVER reads or touches forward returns. The "falling price" it uses is the candidate's already-
  computed TRAILING drawdown (historical/coincident), not a post-decision return.
- Every flag is source-bound to the specific 8-K (accession + item + date) — or the EDGAR shares
  series — so the human verifies the disqualification rather than trusting it.

Its ONLY job is triage hygiene — stop wasting CIQ effort on structurally-dead names. No prediction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

from vinci.edgar.client import EdgarClient
from vinci.edgar.concepts import extract_points
from vinci.graph.filings import html_to_text
from vinci.netcache import CachedHttp, HttpError
from vinci.rank.profile import StructuralDisqualifier
from vinci.resolver.index import pad_cik
from vinci.schemas.candidate import CandidateRecord
from vinci.schemas.data_record import PriceFeatures

_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
_FILINGS_WINDOW_DAYS = 540  # ~18 months of 8-Ks around the de-rating
_SHARES_WINDOW_DAYS = 730  # trailing ~2y for the dilution-trajectory (mirrors the dossier)
_DILUTION_SHARE_GROWTH = 0.50  # +50% shares over the window = aggressive dilution (face-validity)
_DILUTION_PRICE_DROP = -0.50  # ≤ −50% from the 52w high confirms the "into a falling price" leg

# item codes whose BODY we read (going-concern can sit in a results/other-event 8-K; 4.01 needs the
# auditor-exit text). Pure item-code signals (3.01, 4.02) don't need the body to fire.
_BODY_ITEMS = frozenset({"2.02", "4.01", "8.01", "4.02"})
_GOING_CONCERN = re.compile(r"going concern|substantial doubt", re.IGNORECASE)

# AUDITOR EXIT — a GENUINE auditor departure, not any resignation. The verb must sit next to an
# auditor token (the bug fired on a co-filed director "resigned" or a routine 4.01 firm switch).
# A RESIGNATION (auditor-initiated) fires on its own; a DISMISSAL (company-initiated — usually a
# routine switch / Big-4 upgrade: "dismissed X, engaged Y, no disagreements") fires ONLY with an
# affirmative cause marker, so an upgrade never sinks a good name. DEMOTE-ONLY → bias to precision:
# an ambiguous dismissal stays unflagged (safe under-demote; the name still reaches the dossier).
# Grounded in Item 4.01 + Reg S-K 304: disagreements / reportable events = the distress markers.
_AUDITOR_TOKEN = r"(?:accounting firm|auditors?|accountants?)"
_AUDITOR_VERB = r"(?:resign\w*|declin\w+ to (?:stand|be re-?engaged))"  # auditor-initiated exit
_PROX = 80  # chars between verb and auditor token — keeps the match within one sentence/clause
_AUDITOR_RESIGN = re.compile(
    rf"{_AUDITOR_VERB}[^.]{{0,{_PROX}}}{_AUDITOR_TOKEN}|{_AUDITOR_TOKEN}[^.]{{0,{_PROX}}}{_AUDITOR_VERB}",
    re.IGNORECASE,
)
_AUDITOR_DISMISS = re.compile(
    rf"dismiss\w*[^.]{{0,{_PROX}}}{_AUDITOR_TOKEN}|{_AUDITOR_TOKEN}[^.]{{0,{_PROX}}}dismiss\w*",
    re.IGNORECASE,
)
# affirmative cause — phrased to NOT match the routine "no disagreements or reportable events"
# boilerplate a clean switch discloses (so a Big-4 upgrade with a dismissal does not fire):
_AUDITOR_CAUSE = re.compile(
    r"material weakness|restat\w+|going concern|\ba reportable event"
    r"|\ba disagreement|disagreement[s]?\s+(?:with|regarding|concerning|over|about|as to)",
    re.IGNORECASE,
)


def _auditor_exit(body: str) -> bool:
    """True iff the 8-K text shows a GENUINE auditor exit (not any resignation). A resignation near
    an auditor token fires on its own (auditor-initiated → distress); a dismissal fires only with an
    affirmative cause marker (a bare company-initiated dismissal is a routine switch)."""
    if _AUDITOR_RESIGN.search(body):
        return True
    return bool(_AUDITOR_DISMISS.search(body) and _AUDITOR_CAUSE.search(body))


@dataclass(frozen=True)
class FilingText:
    """One 8-K's structural inputs: item codes + (optionally fetched) body text, source-bound."""

    accession: str
    filing_date: date
    items: tuple[str, ...]
    body: str  # "" when not fetched (pure item-code signals don't need it)


def _src(f: FilingText) -> str:
    return f"8-K {f.accession} item {', '.join(f.items) or '—'} filed {f.filing_date.isoformat()}"


def _dilution_spiral(
    shares: list[tuple[date, float]], prices: PriceFeatures
) -> StructuralDisqualifier | None:
    """Shares rising materially into a falling price = death-spiral signature. Uses the candidate's
    already-computed TRAILING drawdown (never a forward return)."""
    if len(shares) < 2:
        return None
    series = sorted(shares)
    anchor = series[-1][0] - timedelta(days=_SHARES_WINDOW_DAYS)
    window = [s for s in series if s[0] >= anchor] or series
    (d0, v0), (d1, v1) = window[0], window[-1]
    if v0 <= 0 or v1 <= 0:
        return None
    growth = v1 / v0 - 1.0
    dd = prices.drawdown_from_high
    fell = dd.is_evaluable and dd.value is not None and dd.value <= _DILUTION_PRICE_DROP
    if growth >= _DILUTION_SHARE_GROWTH and fell and dd.value is not None:
        return StructuralDisqualifier(
            signal="dilution-spiral (shares↑ into price↓)",
            source=f"EDGAR XBRL shares {v0:,.0f} ({d0.isoformat()}) → {v1:,.0f} ({d1.isoformat()})",
            detail=f"shares +{growth:.0%} into a {dd.value:.0%} drawdown — death-spiral signature",
        )
    return None


def classify_structural_disqualifier(
    filings: list[FilingText], shares: list[tuple[date, float]], prices: PriceFeatures
) -> StructuralDisqualifier | None:
    """The PURE classifier — terminal/structural signals only, DEMOTE-ONLY. Returns the single
    most-severe flag (source-bound) or ``None`` (UNCLASSIFIED). No network, no forward returns, no
    promote path: the only outputs are *a flag* (which sinks the name) or *None* (zero effect)."""
    for f in filings:  # (1) non-reliance / restatement — the financials can't be trusted
        if "4.02" in f.items:
            return StructuralDisqualifier(
                signal="non-reliance/restatement (4.02)", source=_src(f),
                detail="prior financial statements not to be relied upon",
            )
    for f in filings:  # (2) going-concern / substantial doubt in the filing text
        if f.body and _GOING_CONCERN.search(f.body):
            return StructuralDisqualifier(
                signal="going-concern / substantial doubt", source=_src(f),
                detail="filing text raises going-concern / substantial doubt",
            )
    for f in filings:  # (3) delisting / listing-deficiency notice
        if "3.01" in f.items:
            return StructuralDisqualifier(
                signal="delisting/deficiency notice (3.01)", source=_src(f),
                detail="delisting or listing-rule deficiency notice",
            )
    for f in filings:  # (4) auditor resignation / dismissal-for-cause (NOT a routine firm switch)
        if "4.01" in f.items and f.body and _auditor_exit(f.body):
            return StructuralDisqualifier(
                signal="auditor resignation/dismissal (4.01)", source=_src(f),
                detail="certifying accountant resigned, or was dismissed for cause",
            )
    return _dilution_spiral(shares, prices)  # (5) dilution death-spiral


# --- the network pass (free EDGAR 8-K text + shares series) — outside the pure classifier ---------


def _filings_for(
    edgar: EdgarClient, http: CachedHttp, cik: str, since: date
) -> list[FilingText] | None:
    """The name's recent 8-Ks, or **None if the filings index could not be fetched**.

    `[]` and `None` are different answers and must never be conflated: `[]` means the issuer filed
    no 8-Ks in the window (a real, clean result), `None` means we never found out. Returning `[]` on
    a failed fetch made an EDGAR outage look like a clean bill of health — see `StructuralScan`.

    A failure to fetch one filing's BODY is NOT a coverage failure: the index still carries the item
    codes, and the item-code-only signals (3.01 delisting, 4.02 restatement) still classify.
    """
    try:
        raw = edgar.recent_filings(cik, forms=("8-K",), since=since)
    except (HttpError, KeyError, ValueError):
        return None
    out: list[FilingText] = []
    for f in raw:
        body = ""
        if f.primary_doc and (_BODY_ITEMS & set(f.items)):
            url = _ARCHIVE.format(
                cik=int(pad_cik(f.cik)), acc=f.accession.replace("-", ""), doc=f.primary_doc
            )
            try:
                body = html_to_text(http.get_text(url, ttl_seconds=None))
            except HttpError:
                body = ""
        out.append(
            FilingText(
                accession=f.accession, filing_date=f.filing_date, items=tuple(f.items), body=body
            )
        )
    return out


def _shares_for(edgar: EdgarClient, cik: str) -> list[tuple[date, float]] | None:
    """The shares-outstanding series, or **None if companyfacts could not be fetched**.

    Same `[]` vs `None` distinction as :func:`_filings_for` — `[]` is an issuer with no share points
    in XBRL, `None` is a fetch that failed. The dilution-spiral leg reads this series, so silently
    returning `[]` disabled that signal without anyone being able to tell.
    """
    try:
        pts = extract_points(edgar.companyfacts(cik), "shares")
    except (HttpError, KeyError):
        return None
    return [(p.period_end, p.value) for p in pts if p.value is not None]


@dataclass(frozen=True)
class StructuralScan:
    """What the scan FOUND, and what it actually LOOKED AT.

    `covered` holds the internal_ids whose inputs were both retrieved, so the classifier ran on real
    evidence. Without it a caller cannot tell **"scanned and clean"** from **"never scanned"** —
    both are simply absent from `flags` — and a transient EDGAR outage reads as a clean bill of
    health for the whole cohort.

    That distinction is load-bearing because the weekly job REPLACES prior flags with this result
    (a live scan is authoritative). Treating an unscanned name as clean would erase a real 8-K
    disqualifier and lift it back above the 0.05 cap on the next run — reintroducing the exact
    #420 failure that the replace-semantics was written to fix.
    """

    flags: dict[str, StructuralDisqualifier]
    covered: frozenset[str]


def scan_structural(
    cands: list[CandidateRecord], *, edgar: EdgarClient, http: CachedHttp
) -> StructuralScan:
    """Network pass: for each candidate fetch its recent 8-Ks (free EDGAR text) + shares series,
    run the pure classifier, and report the FLAGGED names (DEMOTE-ONLY — unflagged names are simply
    absent from ``flags``) alongside the names actually COVERED. Cached via ``http``."""
    out: dict[str, StructuralDisqualifier] = {}
    covered: set[str] = set()
    for c in cands:
        rec = c.data_record
        cik = rec.identity.cik
        if not cik:
            continue
        # Per-name guard (mirrors assemble_cohort): one bad EDGAR response or a corrupt cache file
        # must not kill the whole pass. A skipped name is simply not triaged here — a safe
        # under-demote (it still reaches the dossier), never a fabricated flag. It is also NOT
        # marked covered, so a caller replacing prior flags leaves this name's alone.
        try:
            since = (rec.as_of or date.today()) - timedelta(days=_FILINGS_WINDOW_DAYS)
            filings = _filings_for(edgar, http, cik, since)
            shares = _shares_for(edgar, cik)
            if filings is None or shares is None:
                continue  # an input was never retrieved — classifying now would invent a verdict
            flag = classify_structural_disqualifier(filings, shares, rec.prices)
        except Exception:  # noqa: BLE001 — fail soft per name, never crash the cohort scan
            continue
        covered.add(rec.identity.internal_id)
        if flag is not None:
            out[rec.identity.internal_id] = flag
    return StructuralScan(flags=out, covered=frozenset(covered))
