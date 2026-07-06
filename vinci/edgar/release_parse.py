"""(RC-1 A) DETERMINISTIC 8-K EX-99.1 earnings/guidance parser — heading/anchor-targeted, never an
LLM. Extracts, each source-bound to the exhibit: guidance ranges (+ QUALITATIVE-only markers where
the outlook names a metric but states no number), non-GAAP reconciliation ACTUALS, one-off items
(impairments/charges), and event-impact quantifications (the Avis class, 'expects to reduce X by
$A-$B').

Fail-loud (the PR-2 lesson): no anchored pattern → the field is simply absent + a ``qa_flag``
'no anchored pattern matched — {kind}', never a guessed number and never an analyst caveat. Coverage
is partial beyond the pinned names (guidance phrasing varies across the universe); a miss is honest
UNKNOWN, and an LLM-fenced escalation tier is a QUEUED item, built only on future-finalist evidence.

Text is read pre-normalized (vinci.graph.filings.normalize_text folds the nbsp EDGAR renders as
'$44.7\xa0million'), so a literal space in these anchors matches.
"""
from __future__ import annotations

import re

from vinci.dossier.schemas import (
    EventImpact,
    GuidanceItem,
    OneOffItem,
    ReconciliationValue,
    ReleaseExtract,
)
from vinci.netcache import CachedHttp, HttpError
from vinci.resolver.index import pad_cik

_INDEX = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/index.json"
_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"

# TOLERANT Ex-99.1 filename match: 'ex991' / 'dex991' / 'ex-99.1' / 'ex99_1' — ANY separators,
# including the '_' WORD char that the old \W* class dropped (→ vrrm-ex99_1.htm was missed).
# The final '1' requirement + (?!\d) exclude 99.2 / ex99_2 (the char after the separators is not 1).
_EX991 = re.compile(r"ex[\W_]*99[\W_]*d?[\W_]*1(?!\d)", re.I)


def _is_ex991(name: str) -> bool:
    low = name.lower()
    return low.endswith((".htm", ".html", ".txt")) and _EX991.search(low) is not None


def exhibit_991_urls(http: CachedHttp, cik: str, accession: str) -> list[str]:
    """ALL furnished Exhibit-99.1 press-release URLs in a filing (not first-match — a filing can
    carry more than one, and both must parse). Empty when none / the index is unreachable."""
    acc = accession.replace("-", "")
    try:
        idx = http.get_json(_INDEX.format(cik=int(pad_cik(cik)), acc=acc), ttl_seconds=None)
    except (HttpError, ValueError):
        return []
    return [
        _ARCHIVE.format(cik=int(pad_cik(cik)), acc=acc, doc=str(item.get("name", "")))
        for item in idx.get("directory", {}).get("item", [])
        if _is_ex991(str(item.get("name", "")))
    ]


# --- helpers -------------------------------------------------------------------------------------

_PERIOD = re.compile(r"\b(Q[1-4]\s+20\d\d|FY\s*20\d\d|(?:fiscal\s+)?20\d\d)\b", re.I)


def _money(s: str) -> float | None:
    try:
        return float(s.replace(",", "").replace("$", "").strip())
    except ValueError:
        return None


def _verbatim(text: str, start: int, end: int, *, cap: int = 200) -> str:
    """A ≤cap-char verbatim window, snapped back to the enclosing bullet/sentence, single-spaced."""
    lo0 = max(0, start - 170)
    b = max(text.rfind("•", lo0, start), text.rfind(". ", lo0, start))
    lo = (b + 1) if b != -1 else start
    return " ".join(text[lo:end].split())[:cap].strip()


def _period_near(text: str, start: int, end: int) -> str:
    m = _PERIOD.search(text, end, min(len(text), end + 60)) or _PERIOD.search(
        text, max(0, start - 60), start
    )
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def _norm_metric(raw: str) -> str:
    r = raw.lower()
    if "ebitda" in r:
        return "adjusted ebitda"
    if "per share" in r or "eps" in r:
        return "adjusted eps"
    return "adjusted net income"


def _release_period(text: str) -> str:
    """The release's PRIMARY fiscal period from its header — so a reconciliation ACTUAL is not
    mislabeled with the 'compared to … in {prior year}' comparison year that trails in-sentence."""
    head = text[:400]
    q = re.search(r"(first|second|third|fourth)\s+quarter\s+(?:of\s+)?(20\d\d)", head, re.I)
    if q:
        qn = ["first", "second", "third", "fourth"].index(q.group(1).lower()) + 1
        return f"Q{qn} {q.group(2)}"
    y = re.search(r"(?:reports|results|full[- ]year|fiscal)\D{0,25}?(20\d\d)", head, re.I)
    if y:
        return y.group(1)
    any_y = re.search(r"20\d\d", head)
    return any_y.group(0) if any_y else ""


# --- (1) non-GAAP reconciliation actuals ---------------------------------------------------------
# 'Non-GAAP adjusted EBITDA of positive $44.7 million' / '… of negative $5.5 million' / an adjusted
# net loss. NOT a guidance range: the (?! … to) tail rejects '… of $380 million to $385 million'.
_RECON = re.compile(
    r"(?:non-gaap\s+)?adjusted\s+"
    r"(ebitda|net\s+(?:income|loss|profit)|(?:diluted\s+)?(?:net\s+)?(?:income|loss)\s+per\s+share|"
    r"earnings\s+per\s+share|eps)\s+(?:of|was|totaled|of\s+approximately)\s+"
    r"(positive\s+|negative\s+)?\$?\s*([\d,.]+)\s*(?:million|billion)?"
    r"(?!\s*(?:million\s+|billion\s+)?to\b)",
    re.I,
)
_GROSS_MARGIN = re.compile(
    r"gross\s+margin\s+(?:of\s+|(?:decreased|increased|declined)\s+to\s+|was\s+)?([\d.]+)\s*%",
    re.I,
)
# headline reported revenue (a GAAP actual, period-labeled) — the cross-source input for guide
# verification (a CIQ FY guide that merely echoes this prior-FY actual is a vendor artifact). The
# (?! … to) tail rejects a guidance range ('revenue of $985 million to $995 million').
_REVENUE = re.compile(
    r"(?:full[- ]year|total|quarterly|net)?\s*revenue\s+of\s+(?:a\s+record\s+)?"
    r"\$?\s*([\d,.]+)\s*(?:million|billion)(?!\s+to\b)",  # unit mandatory — else a greedy
    re.I,  # number backtracks to a truncated match ('98' ⊂ '985 million to')
)


def _reconciliation(text: str, src: str, period: str) -> list[ReconciliationValue]:
    out: list[ReconciliationValue] = []
    seen: set[tuple[str, str]] = set()  # (metric, period) — current actual AND prior-year comp
    for m in _RECON.finditer(text):  # both captured, period-labeled, NEVER conflated
        is_comparison = "compared to" in text[max(0, m.start() - 26):m.start()].lower()
        metric_raw, sign, num = m.group(1), (m.group(2) or "").lower(), m.group(3)
        val, metric = _money(num), _norm_metric(m.group(1))
        if val is None:
            continue
        if "negative" in sign or "loss" in metric_raw.lower():
            val = -abs(val)
        # a 'compared to …' clause is the PRIOR-YEAR value — period from the trailing 'in {period}',
        # which must differ from the release period (else skip: never conflate prior with current).
        p = (_period_near(text, m.start(), m.end()) if is_comparison
             else (period or _period_near(text, m.start(), m.end())))
        if (is_comparison and (not p or p == period)) or (metric, p) in seen:
            continue
        seen.add((metric, p))
        out.append(ReconciliationValue(
            metric=metric, period=p, value=val,
            verbatim=_verbatim(text, m.start(), m.end()), source_ref=src,
        ))
    for m in _REVENUE.finditer(text):  # headline revenue actual (same current/prior discipline)
        val = _money(m.group(1))
        if val is None:
            continue
        is_comparison = "compared to" in text[max(0, m.start() - 26):m.start()].lower()
        p = (_period_near(text, m.start(), m.end()) if is_comparison
             else (period or _period_near(text, m.start(), m.end())))
        if (is_comparison and (not p or p == period)) or ("revenue", p) in seen:
            continue
        seen.add(("revenue", p))
        out.append(ReconciliationValue(
            metric="revenue", period=p, value=val,
            verbatim=_verbatim(text, m.start(), m.end()), source_ref=src,
        ))
    gm = next((mm for mm in _GROSS_MARGIN.finditer(text)
               if "adjusted" not in text[max(0, mm.start() - 12):mm.start()].lower()), None)
    if gm and (v := _money(gm.group(1))) is not None:
        out.append(ReconciliationValue(
            metric="gross margin", period=period, value=v,
            verbatim=_verbatim(text, gm.start(), gm.end()), source_ref=src,
        ))
    return out


# --- (2) guidance ranges + QUALITATIVE-only outlook ----------------------------------------------
_GUIDE_RANGE = re.compile(
    r"(total\s+revenue|revenue|adjusted\s+ebitda|adjusted\s+eps|adjusted\s+earnings\s+per\s+share|"
    r"free\s+cash\s+flow|gross\s+margin)\s+of\s+\$?\s*([\d,.]+)\s*(?:million|billion|%)?\s+to\s+"
    r"\$?\s*([\d,.]+)",
    re.I,
)
_OUTLOOK = re.compile(
    r"(20\d\d\s+outlook|financial\s+outlook|revised\s+(?:its\s+|full[- ]year\s+)?(?:financial\s+)?"
    r"outlook|(?:full[- ]year\s+)?guidance\s+for\s+20\d\d)",
    re.I,
)


def _guide_metric(raw: str) -> str:
    r = raw.lower()
    if "revenue" in r:
        return "revenue"
    if "ebitda" in r:
        return "adjusted ebitda"
    if "eps" in r or "per share" in r:
        return "adjusted eps"
    if "cash flow" in r:
        return "free cash flow"
    if "margin" in r:
        return "gross margin"
    return r.strip()


def _guidance(text: str, src: str) -> list[GuidanceItem]:
    out: list[GuidanceItem] = []
    seen: set[str] = set()
    for m in _GUIDE_RANGE.finditer(text):
        metric = _guide_metric(m.group(1))
        low, high = _money(m.group(2)), _money(m.group(3))
        if low is None or high is None or metric in seen:
            continue
        seen.add(metric)
        out.append(GuidanceItem(
            metric=metric, period=_period_near(text, m.start(), m.end()) or "next-fy",
            low=low, high=high, qualitative=False,
            verbatim=_verbatim(text, m.start(), m.end()), source_ref=src,
        ))
    # QUALITATIVE-only: an outlook section that names revenue but carries NO number in its window.
    om = _OUTLOOK.search(text)
    if om and "revenue" not in seen:
        window = text[om.start():om.start() + 700]
        has_rev_number = re.search(r"revenue\D{0,40}\$\s*[\d,]", window, re.I)
        if re.search(r"revenue", window, re.I) and not has_rev_number:
            ym = re.search(r"20\d\d", om.group(1))
            out.append(GuidanceItem(
                metric="revenue", period=ym.group(0) if ym else "next-fy",
                low=None, high=None, qualitative=True,
                verbatim=_verbatim(text, om.start(), om.start() + 200), source_ref=src,
            ))
    return out


# --- (3) one-off items (impairments / charges) ---------------------------------------------------
_ONEOFF = re.compile(
    r"\$\s*([\d,.]+)\s*(?:million|billion)\s+"
    r"((?:[\w'’-]+\s+){0,6}?(?:impairment|write[- ]?off|write[- ]?down|restructuring\s+charge|"
    r"one[- ]?time\s+charge)[\w\s,'’-]{0,80})",
    re.I,
)


def _one_offs(text: str, src: str) -> list[OneOffItem]:
    out: list[OneOffItem] = []
    for m in _ONEOFF.finditer(text):
        amt = _money(m.group(1))
        if amt is None:
            continue
        desc = " ".join(m.group(2).split())
        # trim the description at the next clause boundary
        desc = re.split(r"(?:,\s+which|\.\s|;\s)", desc)[0][:200].strip()
        out.append(OneOffItem(
            amount=amt, description=desc,
            verbatim=_verbatim(text, m.start(), m.end()), source_ref=src,
        ))
    return out


# --- (4) event-impact quantifications (the Avis class) -------------------------------------------
# 'reduce Commercial Services' 2026 annualized revenue by approximately $135 million to $145 million
#  and 2026 annualized segment profit by approximately $120 million to $125 million' — the 'reduce'
# governs both legs; the second inherits the direction (no 'reduce' of its own).
_IMPACT = re.compile(
    r"([\w'’\s]{0,60}?)\s+by\s+approximately\s+\$?\s*([\d,.]+)\s*(?:million|billion)?\s+to\s+"
    r"\$?\s*([\d,.]+)",
    re.I,
)
_DIR_BACK = re.compile(r"(reduc\w*|lower\w*|decreas\w*|increas\w*|rais\w*|improv\w*)", re.I)


def _impact_metric(phrase: str) -> str:
    r = phrase.lower()
    if "segment profit" in r:
        return "segment profit"
    if "revenue" in r:
        return "revenue"
    if "ebitda" in r:
        return "ebitda"
    if "eps" in r or "per share" in r:
        return "eps"
    return r.strip()


def _event_impacts(text: str, src: str) -> list[EventImpact]:
    out: list[EventImpact] = []
    for m in _IMPACT.finditer(text):
        phrase, low, high = m.group(1), _money(m.group(2)), _money(m.group(3))
        if low is None or high is None:
            continue
        # direction: the nearest reduce/increase verb in the ~90 chars before the phrase. A bare
        # 'X by approximately $A to $B' with no directional verb is not an event impact — skipped.
        pre = text[max(0, m.start() - 90):m.start() + len(phrase)]
        dirs = list(_DIR_BACK.finditer(pre))
        if not dirs:
            continue
        d = dirs[-1].group(1).lower()
        direction = "increase" if d.startswith(("increas", "rais", "improv")) else "reduce"
        period_m = re.search(r"(20\d\d\s+annualized|annualized|20\d\d)", phrase, re.I)
        out.append(EventImpact(
            metric=_impact_metric(phrase), effect=direction, low=low, high=high,
            period=period_m.group(1).strip() if period_m else "",
            verbatim=_verbatim(text, m.start(), m.end()), source_ref=src,
        ))
    return out


def parse_release(text: str, *, source_ref: str) -> ReleaseExtract:
    """Parse ONE 99.1 exhibit's normalized text into a source-bound ReleaseExtract. Each empty
    section fails loud with a qa_flag — a miss is UNKNOWN, never a fabricated value."""
    guidance = _guidance(text, source_ref)
    reconciliation = _reconciliation(text, source_ref, _release_period(text))
    one_offs = _one_offs(text, source_ref)
    event_impacts = _event_impacts(text, source_ref)
    flags: list[str] = []
    if not guidance:
        flags.append(f"no anchored pattern matched — guidance/outlook: {source_ref}")
    if not reconciliation:
        flags.append(f"no anchored pattern matched — non-GAAP reconciliation: {source_ref}")
    return ReleaseExtract(
        source_ref=source_ref, guidance=guidance, reconciliation=reconciliation,
        one_offs=one_offs, event_impacts=event_impacts, qa_flags=flags,
    )
