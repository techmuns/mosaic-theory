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

import html
import re

from vinci.dossier.schemas import (
    DriverKind,
    EventImpact,
    GuidanceItem,
    OneOffItem,
    OperatingDriver,
    ReconciliationValue,
    ReleaseExtract,
)
from vinci.netcache import CachedHttp, HttpError
from vinci.resolver.index import pad_cik

_INDEX = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/index.json"
_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
_HEADERS = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{acc_dashed}-index-headers.html"

# TOLERANT Ex-99.1 filename match — the FALLBACK only (see exhibit_991_urls): 'ex991' / 'dex991' /
# 'ex-99.1' / 'ex99_1', any separators including the '_' WORD char that a \W* class drops.
# The final '1' + (?!\d) exclude 99.2 / 99.10. Filenames are a GUESS: filers also ship
# 'a991_pressrelease…', 'exhibit991…', 'exh991…' (unmatched here), and EPAM's 'exhibit99_q1x2026'
# matches only by the accident of "q1" — which is precisely why the TYPE lookup below leads.
_EX991_NAME = re.compile(r"ex[\W_]*99[\W_]*d?[\W_]*1(?!\d)", re.I)
# EDGAR's own per-document SGML header: <TYPE>EX-99.1 … <FILENAME>whatever.htm. Served
# HTML-ESCAPED inside the -index-headers page, so the caller unescapes before matching.
_SGML_DOC = re.compile(r"<TYPE>([^\s<]+)[\s\S]{0,400}?<FILENAME>([^\s<]+)", re.I)
_TEXT_DOC = (".htm", ".html", ".txt")


def _is_ex991(name: str) -> bool:
    """Filename-shaped guess at an Ex-99.1 press release (the fallback path)."""
    low = name.lower()
    return low.endswith(_TEXT_DOC) and _EX991_NAME.search(low) is not None


def _ex991_names_from_headers(http: CachedHttp, cik: str, accession: str) -> list[str] | None:
    """Filenames EDGAR itself types as EX-99.1, from the filing's SGML header.

    The AUTHORITATIVE source: the header states the exhibit designator, so no filename convention
    has to be guessed. Returns None when the header is unreachable/unparseable (caller falls back
    to the filename match) — distinct from [] which means 'read it, this filing furnishes none'."""
    acc = accession.replace("-", "")
    url = _HEADERS.format(cik=int(pad_cik(cik)), acc=acc, acc_dashed=accession)
    try:
        raw = http.get_text(url, ttl_seconds=None)
    except (HttpError, ValueError):
        return None
    text = html.unescape(raw)
    if "<TYPE>" not in text.upper():
        return None  # not the SGML shape we expect — fall back rather than assert absence
    return [
        fn for ty, fn in _SGML_DOC.findall(text)
        # EX-99.1 exactly — never EX-99.11/99.12, and never the EX-99.2 sibling
        if re.fullmatch(r"ex-?99[.\-]?1", ty.strip(), re.I) and fn.lower().endswith(_TEXT_DOC)
    ]


def exhibit_991_urls(http: CachedHttp, cik: str, accession: str) -> list[str]:
    """ALL furnished Exhibit-99.1 press-release URLs in a filing (not first-match — a filing can
    carry more than one, and both must parse).

    Reads the exhibit TYPE from EDGAR's SGML header rather than pattern-matching the FILENAME:
    filers name the same exhibit 'ex991', 'a991_pressrelease…', 'exhibit991…', 'exh991…' and
    'exhibit99_q1x2026', so a filename rule is a guess that silently loses press releases (measured
    2026-07-22: 24 of 53 across five names). The filename match stays as the fallback for a filing
    whose header cannot be read. Empty when the filing genuinely furnishes no Ex-99.1."""
    acc = accession.replace("-", "")
    names = _ex991_names_from_headers(http, cik, accession)
    if names is None:  # header unreadable → fall back to the filename guess
        try:
            idx = http.get_json(_INDEX.format(cik=int(pad_cik(cik)), acc=acc), ttl_seconds=None)
        except (HttpError, ValueError):
            return []
        names = [
            str(item.get("name", ""))
            for item in idx.get("directory", {}).get("item", [])
            if _is_ex991(str(item.get("name", "")))
        ]
    return [_ARCHIVE.format(cik=int(pad_cik(cik)), acc=acc, doc=n) for n in names]


# --- helpers -------------------------------------------------------------------------------------

_PERIOD = re.compile(r"\b(Q[1-4]\s+20\d\d|FY\s*20\d\d|(?:fiscal\s+)?20\d\d)\b", re.I)


def _near(a: float, b: float, *, tol: float = 0.10) -> bool:
    """Two magnitudes close enough to be the SAME item restated at a different rounding
    ($11.0M vs $11.3M), rather than two different charges ($12.0M vs $30.0M)."""
    hi = max(abs(a), abs(b))
    return hi == 0 or abs(a - b) / hi <= tol


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


# The DIRECTION a release states beside the level: "…$230.0 million, an increase of $21.5 million",
# "…of $3.26, an increase of 14.2%", "Revenues of $1.408 billion, up 12.8% year-over-year".
# A gap-down is about the DELTA, not the level, so the level alone cannot explain it.
_CHANGE = re.compile(
    r"^[^.•]{0,60}?\b(?:(an\s+increase|a\s+decrease|an\s+improvement|a\s+decline)\s+of|"
    r"(up|down|rose|fell|declined|increased|decreased))\s+"
    r"(?:by\s+)?(\$?\s*[\d,.]+\s*(?:million|billion|%)?)",
    re.I,
)
_DOWNWORDS = ("decrease", "decline", "down", "fell", "declined", "decreased")


def _change_after(text: str, end: int) -> str | None:
    """The change clause immediately following a metric's value, normalised to a signed token.

    Read only from the SAME sentence/bullet as the value (the window stops at the next '.'/'•'),
    so a delta belonging to a later metric is never attached to this one."""
    stop = len(text)
    for mark in (". ", "•", "; "):
        j = text.find(mark, end, end + 160)
        if j != -1:
            stop = min(stop, j)
    m = _CHANGE.search(text[end:stop])
    if not m:
        return None
    word = (m.group(1) or m.group(2) or "").lower()
    amt = " ".join(m.group(3).split()).replace("$ ", "$")
    sign = "-" if any(w in word for w in _DOWNWORDS) else "+"
    return f"{sign}{amt}"


def _norm_metric(raw: str) -> str:
    r = raw.lower()
    if "ebitda" in r:
        return "adjusted ebitda"
    if "per share" in r or "eps" in r:
        return "adjusted eps"
    # operating income / income from operations is PRE interest and tax — bucketing it into
    # "adjusted net income" (the old fall-through) states a different figure under a familiar
    # name, which is worse than not extracting it. It gets its own label.
    if "operating income" in r or "income from operations" in r:
        return "adjusted operating income"
    return "adjusted net income"


def _release_period(text: str) -> str:
    """The release's PRIMARY fiscal period from its header — so a reconciliation ACTUAL is not
    mislabeled with the 'compared to … in {prior year}' comparison year that trails in-sentence."""
    head = text[:400]
    # "Second Quarter of Fiscal Year 2026" / "of 2026" / "of fiscal 2026" — the FY phrasing between
    # 'quarter' and the year must not push this to the bare-year fallback (BellRing mislabelled its
    # quarterly figures with the year).
    q = re.search(
        r"(first|second|third|fourth)\s+quarter\s+"
        r"(?:of\s+)?(?:the\s+)?(?:fiscal\s+year\s+|fiscal\s+|fy\s*)?(20\d\d)",
        head, re.I)
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
    # "Adjusted X" OR "Non-GAAP X" — filers use either, and EPAM/CNXC never write "adjusted"
    # ("Non-GAAP Diluted EPS of $3.26"). A footnote MARKER may follow the metric name: BellRing
    # writes "Adjusted EBITDA* of $53.8 million", and the un-tolerated '*' silently dropped the
    # whole release. \*? also covers the †/‡ conventions via the [*†‡]? class.
    r"(?:non-gaap|adjusted)\s+"
    r"((?:diluted\s+)?(?:net\s+)?"
    r"(?:ebitda|income\s+from\s+operations|operating\s+income|net\s+(?:income|loss|profit)|"
    r"(?:income|loss)\s+per\s+share|earnings\s+per\s+share|eps))"
    # CONNECTOR: a verb ("of/was/totaled") OR a bare COLON — Gartner writes "adjusted EBITDA: $436
    # million, +5%" (period stated in the section header, not inline), which the verb-only connector
    # silently dropped. The currency-evidence + no-% guards below still gate every match, so a colon
    # can't admit a ratio ("adjusted EBITDA margin: 21%") or a non-amount.
    r"\s*[*†‡]?\s*(?::\s*|(?:of|was|totaled|of\s+approximately)\s+)"
    # CURRENCY EVIDENCE IS MANDATORY — a '$' before the number, or a million/billion after it.
    # Without this the pattern reads a RATIO as an amount: EPAM writes "non-GAAP income from
    # operations was 16.3% of revenues" (a margin), which was stored as $16.3M against a true
    # ~$230M on $1.4B revenue. A fabricated magnitude in a decision figure is the exact failure
    # this codebase refuses; a metric stated only as a percentage is simply not this extractor's.
    r"(positive\s+|negative\s+)?"
    r"(?:\$\s*([\d,.]+)\s*(?:million|billion)?|([\d,.]+)\s*(?:million|billion))"
    r"(?!\s*%)"
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
        # the amount comes from EITHER currency branch: "$53.8 million" (group 3) or
        # "53.8 million" (group 4). A bare number with neither marker no longer matches at all.
        metric_raw, sign = m.group(1), (m.group(2) or "").lower()
        num = m.group(3) or m.group(4)
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
            metric=metric, period=p, value=val, change=_change_after(text, m.end()),
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
    # Metric names as filers write them (net sales / total revenues — BellRing, Simply Good, nCino
    # all guide on these and were invisible), an optional footnote marker, and BOTH range
    # phrasings: "outlook of $X to $Y" and "expected to range between $X and $Y".
    r"(total\s+revenues?|net\s+sales|revenues?|adjusted\s+ebitda|adjusted\s+eps|"
    r"adjusted\s+earnings\s+per\s+share|free\s+cash\s+flow|gross\s+margin)"
    r"\s*[*†‡]?\s*(?:outlook\s+)?(?:of|expected\s+to\s+range\s+between|to\s+range\s+between|"
    r"between)\s+"
    # range separator: "to" / "and" / a bare hyphen or en/em dash ("$2.325-$2.365 billion" —
    # BellRing). The dash form carries no spaces, so \s* around it, not \s+.
    r"\$?\s*([\d,.]+)\s*(?:million|billion|%)?\s*(?:to|and|[-–—])\s*"
    r"\$?\s*([\d,.]+)\s*(million|billion)?",
    re.I,
)
# A GROWTH-RATE guide is a real number, not a qualitative outlook: EPAM guides
# "the year-over-year revenue growth rate to be in the range of 4.5% to 7.5%". The dollar-range
# pattern cannot see it, so it fell through to the QUALITATIVE marker — which asserts the company
# said nothing when it said the most decision-relevant thing in the release.
_GUIDE_PCT = re.compile(
    r"(revenue|net\s+sales|total\s+revenues?|adjusted\s+ebitda|gross\s+margin)"
    r"[^.]{0,60}?growth\s+rate[^.]{0,60}?"
    r"(?:in\s+the\s+range\s+of|between|of)\s+"
    r"([\d.]+)\s*%\s*(?:to|and|[-–—])\s*([\d.]+)\s*%",
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
        # UNITS: normalise to $M. Concentrix guides revenue in BILLIONS ("$2.465 to $2.49 billion")
        # while every other name guides in millions, and the composer prints the bare number — so an
        # un-scaled 2.465 read as $2.5M beside VRRM's 985.0 ($M). A magnitude error in a
        # decision figure is worse than an absent one, so scale here where the unit word is in hand.
        # Scale ONLY on the stated unit word — the trailing unit governs the whole range
        # ("$2.465 to $2.49 billion"). Inferring billions from magnitude would be a guess, and a
        # guessed magnitude is exactly the fabrication this codebase refuses.
        if (m.group(4) or "").lower().startswith("billion"):
            low, high = low * 1000.0, high * 1000.0
        seen.add(metric)
        out.append(GuidanceItem(
            metric=metric, period=_period_near(text, m.start(), m.end()) or "next-fy",
            low=low, high=high, qualitative=False,
            verbatim=_verbatim(text, m.start(), m.end()), source_ref=src,
        ))
    for m in _GUIDE_PCT.finditer(text):
        metric = _guide_metric(m.group(1))
        lo, hi = _money(m.group(2)), _money(m.group(3))
        if lo is None or hi is None or metric in seen:
            continue
        seen.add(metric)
        out.append(GuidanceItem(
            metric=metric, period=_period_near(text, m.start(), m.end()) or "next-fy",
            low=lo, high=hi, unit="%", qualitative=False,
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
    # The one-off IS usually the reason for the gap ("a pre-tax $11.3 million inventory-related
    # charge"), so the noun set must cover how filers actually write it — charge / costs /
    # expenses, not only impairment-family words. Each generic noun REQUIRES a qualifier before it
    # (restructuring, integration, one-time, inventory-related …) so routine operating costs
    # ("cost of goods sold", "interest expense") are never mistaken for a discrete item.
    r"\$\s*([\d,.]+)\s*(?:million|billion)\s+(?:of\s+|in\s+)?"
    r"((?:[\w'’-]+\s+){0,6}?"
    r"(?:impairment|write[- ]?off|write[- ]?down|"
    r"(?:restructuring|integration|one[- ]?time|transaction|acquisition[- ]related|"
    r"inventory[- ]related|impairment[- ]related|separation|transition|legal\s+settlement)"
    r"\s+(?:charge|charges|cost|costs|expense|expenses))"
    r"[\w\s,'’-]{0,80})",
    re.I,
)


def _one_offs(text: str, src: str) -> list[OneOffItem]:
    by_key: dict[str, OneOffItem] = {}
    # key → normalized FULL raw desc, for the identical-item (same-scope-two-figures) collapse
    raw_by_key: dict[str, str] = {}
    for m in _ONEOFF.finditer(text):
        amt = _money(m.group(1))
        if amt is None:
            continue
        raw_desc = " ".join(m.group(2).split())
        # trim at the next clause boundary AND at the first comma — a one-off's name rarely spans a
        # comma, so the comma introduces a SECOND, different item ("restructuring costs, integration
        # expenses of" → "restructuring costs", not a fragment dangling at "of").
        desc = re.split(r"(?:,\s|\.\s|;\s|\s+which\b)", raw_desc)[0][:200].strip()
        # belt-and-braces: never end on a bare preposition/conjunction
        desc = re.sub(r"\s+(?:of|in|for|to|by|and|the|a|an)$", "", desc, flags=re.I).strip()
        # PRIOR-PERIOD COMPARATIVES are not this period's one-off. A release states the current
        # charge and then restates last year's beside it ("and for the prior year period
        # integration expenses of $0.2 million"); listing both as drivers of THIS gap-down would
        # attribute a year-old item to today's move.
        # Look back only to the START OF THIS SENTENCE — a fixed character window reaches across
        # sentence boundaries and kills a current-period item merely because the preceding
        # sentence mentioned last year ("Compared with the prior year period, results improved.
        # The quarter included a $25.0 million impairment charge.").
        sent_start = max(text.rfind(". ", max(0, m.start() - 300), m.start()),
                         text.rfind("• ", max(0, m.start() - 300), m.start()))
        window = text[(sent_start + 1) if sent_start != -1 else max(0, m.start() - 90):m.start()]
        if re.search(r"prior[- ]year|prior\s+period|year[- ]ago", window, re.I):
            continue
        if re.match(r"^(?:and\s+)?(?:for|in)\b", desc, re.I):  # a dangling comparative fragment
            continue
        # ONE ROW PER DISTINCT ITEM. A press release repeats the same charge in the highlights and
        # again per segment, at different roundings ($11 million / $11.3 million), so a bare dedup
        # on the exact string leaves eight copies of one fact. Key on the item's NOUN PHRASE and
        # keep the most precise mention (the largest magnitude wins ties of rounding).
        # ONE ROW PER DISTINCT ITEM — but "distinct" needs the AMOUNT too. Keying on the noun
        # phrase alone collapsed two genuinely different charges ($12.0M European footprint and
        # $30.0M Asia exit both read "restructuring charges rel…"), silently dropping the smaller.
        # Same phrase AND a near-equal amount is one item restated at a different rounding
        # ($11.0M / $11.3M); a materially different amount is a different item.
        phrase = re.sub(r"[^a-z ]", "", desc.lower())[:24].strip()
        # default key CARRIES THE AMOUNT, so two different charges under the same phrase stay two
        # rows; the loop below re-uses an existing key when the amounts are near-equal (one item
        # restated at a different rounding, $11.0M/$11.3M) OR when the FULL raw descriptions are
        # byte-identical (the SAME item quoted at two reconciliation scopes — SMPL's OWYN
        # integration expense at $3.9M for the quarter and $6.5M year-to-date, both worded
        # identically). A DIFFERENT qualifier ($12M European vs $30M Asia restructuring) keeps two.
        raw_norm = re.sub(r"[^a-z ]", "", raw_desc.lower())[:60].strip()
        key = f"{phrase}|{amt}"
        for k, seen_item in by_key.items():
            same_rounding = k.startswith(phrase[:16]) and _near(amt, seen_item.amount)
            same_item = raw_by_key.get(k) == raw_norm
            if same_rounding or same_item:
                key = k
                break
        prev = by_key.get(key)
        # keep the FIRST occurrence for an identical-item collapse (the quarter is quoted first, and
        # the gap-down driver wants the QUARTER figure); a same-phrase non-identical mention is a
        # rounding tie ($11.0M/$11.3M) where the more precise (larger/longer) wins. ACCEPTED RISK:
        # two GENUINELY DIFFERENT charges worded byte-identically in the captured phrase (differing
        # only in amount, no distinguishing scope/qualifier text — indistinguishable from SMPL's
        # same-item QTD/YTD restatement) collapse to the first; recorded in STATE.md with its
        # falsifier. No local signal separates the two, so the code optimizes for the observed case.
        identical_item = raw_by_key.get(key) == raw_norm
        if prev is None or (not identical_item and (amt > prev.amount
                            or (amt == prev.amount and len(desc) > len(prev.description)))):
            by_key[key] = OneOffItem(
                amount=amt, description=desc,
                verbatim=_verbatim(text, m.start(), m.end()), source_ref=src,
            )
            raw_by_key[key] = raw_norm
    return list(by_key.values())


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


# --- (PR-B A1) operating drivers — pricing actions + narrow leading indicators -------------------
# DEMOTED per the pre-sign-off diagnosis: pricing language is REAL (VITL) but KPI yield on this
# cohort is thin/noisy, so KPI is narrow (a shipped/added verb must GOVERN the number+unit — not
# adjacency) with the two observed false-positive shapes pinned out: an expense line-item carrying a
# unit word (FUBO), and a product spec ('290Ah cell', MVST). Pricing rows are QUALITATIVE by default
# (a headline '7% increase' is revenue growth, NOT a price change) — value_num is set ONLY when a %
# binds tightly to the price. M&A/merger boilerplate ('purchase price adjustment') is excluded.
_PRICING = re.compile(
    r"(strategic\s+pricing\s+actions?|pricing\s+actions?|list\s+price\s+increases?|"
    r"price\s+increases?|rais(?:e|ed|ing)\s+(?:our\s+|list\s+)?prices?|"
    r"increas(?:e|ed|ing)\s+(?:our\s+|the\s+)?(?:average\s+)?(?:selling\s+)?prices?)",
    re.I)
_PRICING_PCT = re.compile(  # a % TIGHTLY bound to the price action (else stays qualitative) — the
    # gap forbids COMMAS and DIGITS and is short, so a nearby UNRELATED % ('net of 8% rebates',
    # 'offset by 4% higher logistics', '…to gross margin of 40%') can't misbind as the price change.
    r"pric\w+[^.,\d]{0,24}?(?:of|by)\s+([\d.]+)\s?%"
    r"|([\d.]+)\s?%\s+(?:list\s+)?price\s+increase", re.I)
_MA_CONTEXT = re.compile(
    r"purchase\s+price\s+adjustment|merger\s+agreement|acquisition\s+agreement|indemnif\w+|"
    r"escrow", re.I)
_KPI_UNIT = (r"MWh|GWh|units|vehicles|members|subscribers|customers|locations|stores|procedures|"
             r"shipments|deliveries|tons")
# a shipped/added/etc. verb must GOVERN the number+unit (≤40 chars before) — adjacency alone is not
# a KPI (rejects 'Subscriber related expenses 946,705' and the '290Ah cell' product spec).
_KPI = re.compile(
    r"(shipped|delivered|added|produced|served|installed|sold|reached|grew\s+to|"
    r"increased\s+to)\s+(?:approximately\s+|about\s+|~)?([\d,][\d,.]*)\s+(" + _KPI_UNIT + r")\b",
    re.I)
_KPI_EXCLUDE = re.compile(r"expense|cost\s+of", re.I)


def operating_drivers(text: str, *, source_ref: str) -> list[OperatingDriver]:
    """(PR-B A1) Pricing-action + narrow leading-indicator rows from a 99.1 release. Pricing rows
    are verbatim-bound and QUALITATIVE unless a % binds tightly to the price; KPI rows require a
    governing shipped/added verb. M&A boilerplate and expense-line unit words are excluded. Empty is
    an honest miss the collector flags — the diagnosis expects thin KPI yield on this cohort."""
    out: list[OperatingDriver] = []
    seen: set[str] = set()
    for m in _PRICING.finditer(text):
        window = text[max(0, m.start() - 60):m.end() + 60]
        if _MA_CONTEXT.search(window):  # a merger/indemnity 'price' clause is not a pricing action
            continue
        if re.search(r"\b(?:not|no|without|never)\s+\w*$|n['’]t\s+\w*$",
                     text[max(0, m.start() - 18):m.start()], re.I):
            continue  # a NEGATED statement ('did not raise prices', 'no price increases') isn't one
        phrase = re.sub(r"\s+", " ", m.group(0)).strip().lower()
        if phrase in seen:
            continue
        seen.add(phrase)
        pm = _PRICING_PCT.search(text[m.start():m.end() + 60])
        pct = _money(pm.group(1) or pm.group(2)) if pm else None
        out.append(OperatingDriver(
            kind=DriverKind.PRICING_ACTION, metric="pricing action", period=_period_near(
                text, m.start(), m.end()) or None,
            value=(f"{phrase} — {pct:g}%" if pct is not None else phrase),
            value_num=pct, unit="%" if pct is not None else None,
            verbatim=_verbatim(text, m.start(), m.end(), cap=200), source_ref=source_ref,
            tier="anchored",
        ))
        if len(seen) >= 4:  # dedup-cap pricing phrases (a release repeats them) — no silent flood
            break
    for m in _KPI.finditer(text):
        pre = text[max(0, m.start() - 32):m.start()]
        if _KPI_EXCLUDE.search(pre):  # 'Subscriber related expenses 946,705' is NOT a volume KPI
            continue
        num = _money(m.group(2))
        if num is None:
            continue
        unit = m.group(3)
        key = f"{num}|{unit.lower()}"
        if key in seen:
            continue
        seen.add(key)
        out.append(OperatingDriver(
            kind=DriverKind.LEADING_INDICATOR, metric=f"{m.group(1).lower()} ({unit.lower()})",
            period=_period_near(text, m.start(), m.end()) or None,
            value=f"{m.group(2)} {unit}", value_num=num, unit=unit,
            verbatim=_verbatim(text, m.start(), m.end(), cap=200), source_ref=source_ref,
            tier="anchored",
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
