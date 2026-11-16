"""(E5 / H1d) The FENCED covenant-terms extractor — Tier-2, LLM.

The mechanical layer locates the *execution filing* that carries a debt agreement as an EXHIBIT
(``_covenant_pointers``, CIK-scoped + exhibit-verified). This layer reads that exhibit and pulls the
NAMED contractual terms — the conversion price/mechanics of a convertible above all — as
:class:`CovenantTerm` rows, each a ``{value, source_ref}`` bound to the exhibit or an explicit
UNKNOWN. It is **assembly-and-cite, never conclusion**: the tool schema has no verdict/risk field.

Fences (why this is safe to let an LLM do):
- **Verbatim only.** The model reports the value AS STATED — a number, a *formula* (MVST's stated
  conversion price is "$1.00 ÷ the applicable Conversion Rate", NOT a fabricated $/share), a date.
  It NEVER infers, computes, or estimates. A term the document omits is UNKNOWN, never guessed.
- **Machine-set source_ref.** The ``source_ref`` is set by THIS code to the exhibit actually fetched
  (``8-K <accession> · <filename>``) — the model cannot invent a citation; it fills only the value
  and a verbatim quote the human can grep for.
- **The quote is checked, not trusted.** A term is kept PRESENT only when its quote is a span of the
  exhibit text the model was sent (`vinci.verbatim`); otherwise it is UNKNOWN + a flag. The prompt
  asks for the exact clause, but only the document can show a clause was READ rather than recalled
  — and these exhibits are often years older than the model's training cutoff.
- **Fail loud.** A fetch failure, an over-large exhibit, or an LLM error yields UNKNOWN + a flag —
  the covenant-terms row set is never silently blank and never partially fabricated.
"""

from __future__ import annotations

import math
import re
from datetime import date
from decimal import Decimal
from typing import Any, Literal, NamedTuple

from vinci.dossier.schemas import (
    CapitalInstrument,
    CapitalStructure,
    CovenantExhibitOutcome,
    CovenantExhibitOutcomeKind,
    CovenantPointer,
    CovenantTerm,
    Sourced,
    SourceStatus,
)
from vinci.edgar.release_parse import figure_stated
from vinci.graph.filings import html_to_text
from vinci.graph.llm import LlmClient, LlmError
from vinci.netcache import CachedHttp
from vinci.resolver.index import pad_cik
from vinci.verbatim import SourceText

_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
# The note a refused term carries (#804). `governing_terms` reads it to tell a REFUSED statement
# from a term the exhibit never stated — no structured field carries that, and the committed rows
# predate one — so the writer and the reader share this one constant, and dossier.js mirrors it.
REFUSED_NOTE_PREFIX = "(E5) refused:"
# A refusal for what the VALUE states (audit E2-D19): the quote was found, but the value beside it
# states a year or a dollar figure the quote does not. It IS a refusal — a later one still withholds
# an older value in `governing_terms` — and the page's lead names it apart from a quote that was
# not found (`render._refused_newer_text`, dossier.js ``refusedNewerText``).
VALUE_REFUSED_NOTE_PREFIX = f"{REFUSED_NOTE_PREFIX} the value states"
# An exhibit larger than this is not sent in a single pass — extract by hand rather than silently
# truncate (a term past the cut would read as a false UNKNOWN). THAT REFUSAL IS UNCHANGED; only the
# threshold moved, because the old one was set against a window the configured model does not have.
#
# RAISED 600_000 → 1_200_000 ON MEASUREMENT (2026-09-28). BURL alone refused FOUR exhibits at
# 645,693 / 648,641 / 662,704 / 744,759 chars — 7–24% over the old cap — so its page reported the
# whole capital structure UNKNOWN and told the reader to extract by hand. Sent in full through this
# module's own extractor, the largest of them (744,759 chars) returned six of seven target terms,
# each verbatim-quoted: maturity extended to July 25 2030 from December 22 2026, $1.0bn commitments,
# Term SOFR + 1.125%/1.375%, and a SPRINGING fixed-charge covenant of 1.00:1.00 tested only during a
# Covenant Compliance Event. Material facts about a name at 3.8x net debt/EBITDA, withheld by a
# constant rather than by a limit.
#
# THE ARITHMETIC: `claude-opus-4-8` has a 1M-TOKEN window. English legal prose runs ~3.5–4 chars per
# token, so 1.2M chars ≈ 300–340K tokens — under a third of the window, leaving room for the system
# prompt, the tool schema and a 16K-token answer. The largest exhibit seen is 745K chars, so
# this clears it by 60% and stays far from the wall. Exceeding it still FLAGS, never truncates.
_MAX_EXHIBIT_CHARS = 1_200_000
# A RUNAWAY GUARD, NOT A SELECTOR (coverage rule, STATE row 63, 2026-11-16; operator: "Order now,
# coverage next (Recommended)"). Until then this was 4 and it CHOSE the exhibits: the first four
# debt contracts the round-robin reached were sent, so a page spent slots on documents that govern
# nothing (VRRM's revolver amendment, which its own amended-and-restated revolver replaced) and
# dropped live ones past them (AMZN's June 2026 term loan agreement). Now every debt contract the
# coverage rule (`_coverage`) does not find superseded or terminated is sent, and this only stops a
# runaway: a page with more live contracts than this sends the first ones in the loop's order and
# flags the rest loudly, as `cost_bound`.
# WHY 10. The busiest committed page sends 6 under the rule (BURL: its ABL agreement's four
# amendments, its term loan's 2014 amendment and a 2020 security agreement; 26 pages, main
# 51784e53, cache-only). The locator can return at most 13 targets per page: one 10-K row and two
# 8-Ks for each of the six families it searches (`mechanical._COVENANT_QUERY_CAP`). At the $0.69
# mean list price of a covenant call (107 calls in the committed run lines), 10 calls are about $7.
_MAX_EXHIBITS = 10
# the agreement documents worth extracting from — the loan/credit/security/indenture agreement (and
# a convertible's warrant), NOT the ancillary guaranty/pledge (which restate terms defined in the
# core agreement). Matched on the exhibit filename.
_CORE_AGREEMENT = ("loanandsecuri", "loansecuri", "creditagree", "loanagree", "indenture",
                   "securitiespurchase", "notepurchase", "convertible", "syndicatedloan", "warrant")

# The target terms every extraction answers — present-with-value or an explicit not-present — so the
# row set is stable and an absent term is a visible UNKNOWN, not a silent omission. The model MAY
# append additional material terms it finds; it may NOT drop one of these.
_TARGET_TERMS = (
    "Conversion price / mechanics",
    "Principal / commitment amount",
    "Interest / coupon rate",
    "Maturity date",
    "Financial-maintenance covenants",
    "Security / collateral / guarantors",
    "Mandatory prepayment / events of default",
)

_SYSTEM = (
    "You extract STATED contractual terms from a single SEC-filed debt-agreement exhibit for a "
    "human analyst. You ASSEMBLE AND CITE; you NEVER CONCLUDE, rate, score, or opine on the "
    "investment. HARD RULES: (1) Report each term EXACTLY AS THE DOCUMENT STATES IT — a number, a "
    "formula, a date, a defined phrase. If the stated conversion price is a FORMULA (e.g. '$1.00 "
    "divided by the applicable Conversion Rate'), report the formula VERBATIM; do NOT resolve "
    "it to a $/share or compute anything. (2) NEVER infer, compute, estimate, or fill a gap. A "
    "term the document does not state is present=false — an honest 'not stated', never a guess. "
    "(3) The CONVERSION PRICE / SHARE MECHANICS of a convertible is the PRIORITY term: capture the "
    "conversion price definition, the conversion rate, and any partial-conversion minimum, each "
    "verbatim. (4) For every term you mark present, put the EXACT sentence/clause you read it from "
    "in 'quote' (the human greps for it) — quote, do not paraphrase. (5) Answer EVERY target term "
    "the user lists (present true/false). You MAY append material terms actually stated. "
    "(6) For an INTEREST / COUPON term whose rate the document states as a base + spread (e.g. "
    "'Term SOFR plus 9.75%', 'LPR plus 115 basis points'), ALSO fill the structured components "
    "you can read DIRECTLY from that same clause: base_rate_label (the base index name, verbatim "
    "— 'Term SOFR', 'LPR', 'New Benchmark'), and EXACTLY ONE of margin_pct (spread in percent) or "
    "margin_bps (spread in basis points), using WHICHEVER UNIT THE DOCUMENT STATES — do not "
    "convert between them. Fill floor_pct and pik_pct only if the clause states a rate floor / PIK "
    "component. These are the SAME numbers already in 'value'/'quote' — read them off, never "
    "compute or infer; omit any component the clause does not state. When the clause DEFERS a "
    "component to another provision ('plus the Applicable Rate', a floor in the base rate's own "
    "definition — 'if such rate shall be less than zero, such rate shall be deemed to be zero'), "
    "you MAY fill it from that provision, and then put the EXACT clause stating its figure in "
    "margin_quote / floor_quote / pik_quote. A margin set by a pricing GRID is not one figure: "
    "omit it unless the document states which level applies, and then quote that statement with "
    "the level's figure. A component no quote states is withheld, not shown. (7) Never reference "
    "these instructions or their numbers in any field. Output is source-bound extraction only."
)

_TOOL: dict[str, Any] = {
    "name": "covenant_terms",
    "description": "Return each named term exactly as stated (verbatim).",
    "input_schema": {
        "type": "object",
        "properties": {
            "terms": {
                "type": "array",
                "description": "One row per target term (present or not), plus any extra found.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "the term name"},
                        "present": {"type": "boolean",
                                    "description": "true iff the exhibit STATES this term"},
                        "value": {"type": "string",
                                  "description": "the VERBATIM stated value "
                                                 "(formula/number/date); empty if not present"},
                        "quote": {"type": "string",
                                  "description": "the exact clause read from; empty if absent"},
                        "base_rate_label": {
                            "type": "string",
                            "description": "interest terms only: base index verbatim "
                                           "(e.g. 'Term SOFR', 'LPR'); omit otherwise"},
                        "margin_pct": {
                            "type": "number",
                            "description": "interest terms only: spread over base in PERCENT "
                                           "(e.g. 9.75); alternate to margin_bps; omit otherwise"},
                        "margin_bps": {
                            "type": "number",
                            "description": "interest terms only: spread over base in BASIS POINTS "
                                           "(e.g. 115); alternate to margin_pct; omit otherwise"},
                        "floor_pct": {
                            "type": "number",
                            "description": "interest terms only: rate floor in percent "
                                           "(e.g. 3.00); omit if none stated"},
                        "pik_pct": {
                            "type": "number",
                            "description": "interest terms only: PIK component in percent "
                                           "(e.g. 3.75); omit if none stated"},
                        "margin_quote": {
                            "type": "string",
                            "description": "the exact clause stating the margin's figure, ONLY "
                                           "when 'quote' does not (e.g. the Applicable Rate "
                                           "definition); omit otherwise"},
                        "floor_quote": {
                            "type": "string",
                            "description": "the exact clause stating the floor's figure, ONLY "
                                           "when 'quote' does not; omit otherwise"},
                        "pik_quote": {
                            "type": "string",
                            "description": "the exact clause stating the PIK figure, ONLY when "
                                           "'quote' does not; omit otherwise"},
                    },
                    "required": ["name", "present"],
                },
            },
        },
        "required": ["terms"],
    },
}


def _core_agreement_exhibits(rows: list[CovenantPointer]) -> list[tuple[CovenantPointer, str]]:
    """(P4) (pointer, filename) pairs for the CORE agreement exhibit of each pointer, ordered
    so EVERY DISTINCT live-wall instrument family gets its primary BEFORE any family's second
    (amendment) — a ROUND-ROBIN by family. This stops both slots being spent on one facility's
    original+amendment while a different live-wall facility (the syndicated loan) goes unextracted.
    Debt families (loan/credit/convertible/indenture) rank ahead of the 10-K contract index."""
    def fam_rank(fam: str) -> int:
        f = fam.lower()
        debt = any(k in f for k in ("convert", "loan", "credit", "facilit", "indenture", "bond"))
        return 0 if debt else (2 if "10-k" in f or "material contract" in f else 1)

    per_family: dict[str, list[tuple[CovenantPointer, str]]] = {}
    for r in sorted((r for r in rows if r.accession), key=lambda r: fam_rank(r.family)):
        docs = [n for n in r.exhibits if _DOCUMENT.search(n)]  # never an image (N3)
        core = [n for n in docs if any(k in n.lower() for k in _CORE_AGREEMENT)]
        # each pointer's PRIMARY target; the filing's other exhibits are read in the loop, and the
        # ones that govern debt are targeted too (`_located_exhibits`, `_governs`)
        for name in (core or docs)[:1]:
            per_family.setdefault(r.family, []).append((r, name))
    fams = sorted(per_family, key=lambda f: fam_rank(f))  # stable: debt families first
    picked: list[tuple[CovenantPointer, str]] = []
    depth = 0
    while any(len(per_family[f]) > depth for f in fams):  # round-robin across families
        for f in fams:
            if len(per_family[f]) > depth:
                picked.append(per_family[f][depth])
        depth += 1
    return picked


#: A located exhibit in the loop's order: its pointer, its filename, and whether it is its
#: pointer's PRIMARY target (`_core_agreement_exhibits`) or another exhibit of the same filing.
_Located = tuple[CovenantPointer, str, bool]
#: ONLY A DOCUMENT IS READ (#1090 verification, N3, deferred to the selector): a file E5 can read
#: as text, .htm, .html or .txt, as the locator reads only documents among a 20-F's exhibits
#: (`mechanical._EX4_20F_RE`). A filing also lists its page images: EPAM's 10-K row lists six
#: `.jpg`. An image holds no text, so it is never read and never a target, and one that cannot be
#: fetched never switches a page to "supersedes nothing". Measured over the 26 committed pages'
#: pointer rows (main 51784e53): 145 exhibits are `.htm` and 6 `.jpg`; no primary is an image.
_DOCUMENT = re.compile(r"\.(?:htm|html|txt)$", re.I)


def _located_exhibits(rows: list[CovenantPointer]) -> list[_Located]:
    """EVERY DOCUMENT OF EVERY LOCATED FILING, in the loop's order: each pointer's primary target in
    `_core_agreement_exhibits`' order, followed at once by the other documents of its filing, in the
    filing's own order (never a page image, `_DOCUMENT`). An exhibit is listed once, however many
    pointers carry its filing."""
    primaries = _core_agreement_exhibits(rows)
    primary = {(row.accession, filename) for row, filename in primaries}
    out: list[_Located] = []
    seen: set[tuple[str, str]] = set()
    for row, first in primaries:
        for filename in [first, *row.exhibits]:
            if (row.accession, filename) in seen or not _DOCUMENT.search(filename):
                continue
            seen.add((row.accession, filename))
            # a primary of ANY pointer stays a primary, whichever pointer's filing lists it first
            out.append((row, filename, (row.accession, filename) in primary))
    return out


#: A word for which the gate admits a CREDIT-SUPPORT document (`_DEBT`): a guaranty, a pledge, a
#: security or collateral agreement. It secures or guarantees debt that another agreement creates.
_CREDIT_SUPPORT = re.compile(r"(?:SECURITY|PLEDGE|GUARANTY|GUARANTEE)", re.I)


def _governs(title: str | None) -> bool:
    """IS THIS A CONTRACT THAT GOVERNS DEBT, by its own title? A debt agreement
    (`is_debt_agreement`) that the gate admits for at least one word that is not credit support
    (`_CREDIT_SUPPORT`): a credit, loan, financing or receivables agreement, an indenture, notes, a
    facility, and an amendment of any of them. One admitted ONLY for credit-support words ("PLEDGE
    AGREEMENT",
    "LIMITED RECOURSE GUARANTY", "RESTATED GUARANTEE AND COLLATERAL AGREEMENT") secures or
    guarantees obligations another agreement defines, so it is left to that agreement, as
    `_CORE_AGREEMENT` always left it; a title with both ("LOAN AND SECURITY AGREEMENT", "CREDIT AND
    GUARANTY AGREEMENT") governs."""
    if title is None or not is_debt_agreement(title):
        return False
    return any(not _CREDIT_SUPPORT.fullmatch(m.group(1)) for m in _DEBT.finditer(title))


def _source_ref(row: CovenantPointer, filename: str) -> str:
    return f"{row.filing} {row.accession} · {filename}"


def _fetch_exhibit(http: CachedHttp, cik: str, accession: str, filename: str) -> str | None:
    """The exhibit's plain text, or None on any fetch/parse failure (caller fails loud)."""
    url = _ARCHIVE.format(cik=int(pad_cik(cik)), acc=accession.replace("-", ""), doc=filename)
    try:
        return html_to_text(http.get_text(url, ttl_seconds=None))
    except Exception:  # noqa: BLE001 — a fetch/parse failure must degrade to UNKNOWN, never crash
        return None


def _opt_str(v: Any) -> str | None:
    """A tool 'string' field → the stripped str, or None when absent/blank/WRONG-SHAPE. A non-str
    (a list/dict/number/bool the LLM emitted despite the schema) is DROPPED, never ``str()``-ified
    into a garbage lead like ``"['Term SOFR']"`` — fail-soft, never fabricate."""
    if not isinstance(v, str):
        return None
    s = v.strip()
    return s or None


def _opt_float(v: Any) -> float | None:
    """A tool 'number' field → a FINITE float, or None when absent / unparseable / wrong-shape
    (fail-soft: an unreadable component drops out of the lead — never fabricates/crashes the row).
    A ``bool`` is DROPPED (``float(True)`` is ``1.0`` — would fabricate a '+1.00%' coupon whenever a
    stray '1' sits in the clause); a non-finite (nan/inf) is DROPPED (it can't appear verbatim in a
    clause and would crash the bps formatter's ``int()``). A legit '9.75' numeric string is kept."""
    if isinstance(v, bool) or v is None or (isinstance(v, str) and not v.strip()):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


#: The structured rate components a covenant row carries, and the unit each is stated in. The
#: data-quality release source scores each against its quote in that unit, as the gate below does.
RATE_COMPONENTS: dict[str, str] = {"margin_pct": "%", "margin_bps": "bps", "floor_pct": "%",
                                   "pik_pct": "%"}
#: The tool field carrying a component's own clause — one margin clause serves either unit.
_OWN_QUOTE = {"margin_pct": "margin_quote", "margin_bps": "margin_quote",
              "floor_pct": "floor_quote", "pik_pct": "pik_quote"}
_COMPONENT_NAME = {"margin_pct": "margin", "margin_bps": "margin", "floor_pct": "floor",
                   "pik_pct": "PIK"}


class RateComponents(NamedTuple):
    """The rate components a row may carry: each value (None where absent or withheld), the own
    clause of each kept by one, and why each withheld one was."""

    values: dict[str, float | None]
    quotes: dict[str, str]
    withheld: dict[str, str]


#: A currency marker before a covenant figure's digits. Every spelling of one currency maps to
#: ONE code (`_CURRENCY`), so like currencies compare: UBER's "$", AMZN's "US$", V's "U.S.$" and a
#: quote's "USD" are one currency; MVST's "RMB" is another. "US$", "C$" and "A$" precede "$".
_CUR = (r"(?<![A-Za-z])(?:U\.?\s?S\.?\s?\$|C\$|A\$)|\$|€|£|¥"
        r"|\b(?:USD|CAD|AUD|EUR|GBP|RMB|CNY|JPY|CHF)\b")
_CURRENCY = {"US$": "USD", "USD": "USD", "$": "USD", "C$": "CAD", "CAD": "CAD", "A$": "AUD",
             "AUD": "AUD", "€": "EUR", "EUR": "EUR", "£": "GBP", "GBP": "GBP", "RMB": "CNY",
             "CNY": "CNY", "¥": "JPY", "JPY": "JPY", "CHF": "CHF"}
#: The digits, optionally bracketed as MVST's agreement prints them ("RMB [800,000,000.00]").
_NUM = r"\[?\s*(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*\]?"
_SCALE = r"\s*(billion|bn|million|mm|thousand|[BMK](?![A-Za-z]))"
_SCALES = {"billion": 10**9, "bn": 10**9, "b": 10**9, "million": 10**6, "mm": 10**6, "m": 10**6,
           "thousand": 10**3, "k": 10**3}
#: A figure: a marker, its digits, an optional scale.
_FIGURE = re.compile(rf"({_CUR})\s*{_NUM}(?:{_SCALE})?", re.I)
#: A RANGE's high side after a figure: "-350 million", " and $500 million". With no marker of its
#: own it takes the low side's currency, and a low side stating no scale takes the high side's
#: ("$300-350 million"). A high side with neither a marker nor a scale is not a figure.
_RANGE_HIGH = re.compile(rf"\s*(?:-|–|—|to|and|through)\s*(?:({_CUR})\s*)?{_NUM}(?:{_SCALE})?",
                         re.I)
#: The replacement a conformed amendment prints right after the figure it strikes, with no marker
#: of its own: UBER's "$ 1,500,000,000 1,000,000,000", NFLX's "$ 500,000,000 . 750,000,000",
#: WERN's fused "$325,000,000350,000,000" (as `html_to_text` reads it) and "$ 12,000,000.00
#: 15,000,000.00". It is in the struck figure's currency. Read in a QUOTE only.
_REPLACEMENT = re.compile(r"\s*[.,]?\s*(\d{1,3}(?:,\d{3})+(?:\.\d+)?)(?!\d|,\d)")
#: A year: four digits, 1900–2099, with no digit, decimal point, thousands comma or "$" before and
#: no digit, "%" or decimal part after — "2031", "6/30/2029" and "FY2031" are years; the "2000" in
#: "0.2000%" is not.
_YEAR = re.compile(r"(?<![\d.,$])(?:19|20)\d{2}(?![\d%]|[.,]\d)")


class _Money(NamedTuple):
    currency: str      # one code per currency (`_CURRENCY`)
    amount: Decimal    # in units of that currency, its scale applied
    stated: str        # the figure as the text writes it
    span: tuple[int, int]


def _amount(num: str, scale: str | None) -> Decimal:
    return Decimal(num.replace(",", "")) * (_SCALES[scale.lower()] if scale else 1)


def _money(text: str, *, replacements: bool = False) -> list[_Money]:
    """Every figure ``text`` states with a currency marker, at its own scale (`_FIGURE`, a range's
    high side `_RANGE_HIGH`). A figure with no marker — "500 million euros", "zero", a percent —
    is not read here, and never named as dollars (`_bare` reads an unmarked amount).
    ``replacements`` also reads a conformed amendment's replacement after each figure
    (`_REPLACEMENT`); a QUOTE is read with it."""
    out: list[_Money] = []
    read_to = 0
    for m in _FIGURE.finditer(text):
        if m.start() < read_to:
            continue  # the high side of a range already read
        cur = _CURRENCY[re.sub(r"[\s.]", "", m[1]).upper()]
        hi = _RANGE_HIGH.match(text, m.end())
        if hi and not (hi[1] or hi[3]):
            hi = None  # "$500 million and 3 years": no marker, no scale — not a range
        # a low side borrows the high side's scale only when it is a short bare number ("$300" in
        # "$300-350 million"); "$5,000,000 and $2 million" is two whole amounts
        borrows = bool(hi and hi[3] and not m[3] and "," not in m[2])
        low_end = hi.end() if borrows and hi else m.end()
        out.append(_Money(cur, _amount(m[2], m[3] or (hi[3] if borrows and hi else None)),
                          " ".join(text[m.start():low_end].split()), (m.start(), m.end())))
        if hi:
            read_to = hi.end()
            hcur = _CURRENCY[re.sub(r"[\s.]", "", hi[1]).upper()] if hi[1] else cur
            own = hi.start(1) if hi[1] else hi.start(2)  # the high side's own words
            out.append(_Money(hcur, _amount(hi[2], hi[3] or (m[3] if "," not in hi[2] else None)),
                              " ".join(text[own:hi.end()].split()), (own, hi.end())))
        if replacements and (r := _REPLACEMENT.match(text, (hi or m).end())):
            out.append(_Money(out[-1].currency, _amount(r[1], None), r[1], (r.start(), r.end())))
    return out


#: A WHOLE DATE (TeamNostra fix request 2, RE2-D16): a year alone let "July 25, 2030" stand beside
#: a quote reading "December 22, 2030". Month-day-year, day-month-year and numeric forms compare as
#: one date; "March 29 , 2024" is how `html_to_text` reads a conformed copy's spacing, and
#: "December 22,2030" a comma with no space after it.
_MON = (r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|"
        r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?")
_DATE_SEP = r"(?:\s*,\s*|\s+)"
_DATE_MDY = re.compile(
    rf"\b{_MON}\s+(\d{{1,2}})(?:st|nd|rd|th)?{_DATE_SEP}((?:19|20)\d\d)\b", re.I)
_DATE_DMY = re.compile(
    rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?{_MON}{_DATE_SEP}((?:19|20)\d\d)\b", re.I)
_DATE_NUM = re.compile(r"(?<![\d./])(\d{1,2})/(\d{1,2})/((?:19|20)\d\d)(?!\d)")
#: A conformed amendment's struck date beside its replacement, read in a QUOTE: BURL's
#: "December 22 July 25 , 2026 2030" is December 22, 2026 struck for July 25, 2030.
_DATE_CONFORMED = re.compile(
    rf"\b{_MON}\s+(\d{{1,2}})\s+{_MON}\s+(\d{{1,2}})\s*,?\s+((?:19|20)\d\d)\s+((?:19|20)\d\d)\b",
    re.I)
_MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
#: A RATIO against one: "5.00x", "2.75 times", "4.50 to 1.00", "3.75:1.0". Only a denominator of
#: one is a covenant ratio — "3 to 5 years" is a span.
_RATIO = re.compile(r"(?<![\d.,])(\d+(?:\.\d+)?)\s*(?:x(?![a-z])|times\b|(?:to|:)\s*1(?:\.0+)?"
                    r"(?![\d]|\.\d))", re.I)
#: A conformed copy's struck ratio, read in a QUOTE: NFLX's "(b) 2.50 2.75 times".
_STRUCK = re.compile(r"(?<![\d.,])(\d+\.\d+)\s+$")
#: A PERCENT, in one unit with BASIS POINTS: "1.75%" is "175 bps", and a coupon's fraction
#: "5 1/4%" is 5.25% — never a "4%" read off the "/4%" ("50%/0%" is still two percents).
_PCT = re.compile(r"(?<![\d.,])(?<!\d/)(\d+(?:\.\d+)?)(?:\s+(\d)/(\d{1,2}))?\s*"
                  r"(%|percent\b|per\s+cent\b|bps\b|basis\s+points?\b)", re.I)
#: An AMOUNT WITH NO CURRENCY MARKER, read only where it cannot be a section, a count or a year:
#: comma-grouped ("1,000,000,000"), scaled ("500 million") or with three or more decimals
#: ("45.4545 shares"). "Section 6.02", "3 years" and "48.0" are not read. A comma AFTER the
#: amount ends it ("1,000,000,000, as reduced"), as it ends a conformed replacement.
#: The abbreviated scales `_SCALES` reads are read here too (Codex P2, round 1): "1.5bn" and
#: "500MM" were read as 1.5 and 500, too short to check, and stood PRESENT.
_BARE = re.compile(r"(?<![\d.,$€£¥\[])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
                   r"(?:\s*(billion|bn|million|mm|thousand)\b)?(?!\d|,\d|\.\d)", re.I)
_SECTION_LEAD = re.compile(r"(?:Sections?|§|Article|Art\.|Schedule|Annex|Exhibit|clause|"
                           r"paragraph|Part|Item)\s*$", re.I)


def _dates(text: str, *, conformed: bool = False) -> list[tuple[tuple[int, int, int], str,
                                                                 tuple[int, int]]]:
    """(year, month, day), the date as written, and its span — every whole date ``text`` states."""
    def mon(word: str) -> int:
        return _MONTHS.index(word[:3].lower()) + 1

    out = [((int(m[3]), mon(m[1]), int(m[2])), m[0], m.span()) for m in _DATE_MDY.finditer(text)]
    out += [((int(m[3]), mon(m[2]), int(m[1])), m[0], m.span()) for m in _DATE_DMY.finditer(text)]
    out += [((int(m[3]), int(m[1]), int(m[2])), m[0], m.span()) for m in _DATE_NUM.finditer(text)]
    if conformed:
        for m in _DATE_CONFORMED.finditer(text):
            out.append(((int(m[5]), mon(m[1]), int(m[2])), m[0], m.span()))
            out.append(((int(m[6]), mon(m[3]), int(m[4])), m[0], m.span()))
    return out


def _ratios(text: str, *, conformed: bool = False) -> list[tuple[Decimal, str, tuple[int, int]]]:
    out = [(Decimal(m[1]).normalize(), m[0], m.span()) for m in _RATIO.finditer(text)]
    if conformed:
        for m in _RATIO.finditer(text):
            if s := _STRUCK.search(text, max(0, m.start() - 12), m.start()):
                out.append((Decimal(s[1]).normalize(), s[0], s.span()))
    return out


def _pcts(text: str) -> list[tuple[Decimal, str, tuple[int, int]]]:
    """Each percent as a percent: a basis-point figure is divided by 100."""
    out = []
    for m in _PCT.finditer(text):
        v = Decimal(m[1]) + (Decimal(m[2]) / Decimal(m[3]) if m[2] and int(m[3]) else 0)
        out.append(((v / 100 if m[4].lower().startswith(("bp", "basis")) else v).normalize(),
                    m[0], m.span()))
    return out


def _bare(text: str, taken: list[tuple[int, int]]) -> list[tuple[Decimal, str]]:
    """Each amount ``text`` states with no currency marker, at its scale, outside ``taken``."""
    out = []
    for m in _BARE.finditer(text):
        if any(a <= m.start() < b for a, b in taken):
            continue
        num, scale = m[1], m[2]
        if not ("," in num or scale or len(num.partition(".")[2]) >= 3):
            continue
        if re.fullmatch(r"(?:19|20)\d\d", num) or _SECTION_LEAD.search(text, 0, m.start()):
            continue
        out.append((_amount(num, scale).normalize(), m[0].strip()))
    return out


def unstated_in_quote(value: str, quote: str) -> list[str]:
    """Each figure ``value`` states that ``quote`` does not (audit E2-D19; TeamNostra fix request
    2, RE2-D16), each as the value states it and once: its whole dates and lone years first, then
    its money, ratios, percents and unmarked amounts, each in the value's order. Empty when the
    quote states them all.

    THE QUOTE WAS CHECKED; THE VALUE BESIDE IT WAS NOT. #804 proves the quote is a span of the
    exhibit, but the model writes the value separately, so "June 15, 2031" stood beside a quote
    reading "June 15, 2030". Measured on the 13 in-scope committed pages at 8e6b12b1: 29 of 176
    PRESENT terms on 9 pages state a year or a dollar figure their quote does not.

    E2-D19 CHECKED YEARS AND CURRENCY FIGURES ONLY, and every other figure a value adds passed as
    PRESENT (RE2-D16): "5.00x" beside "4.50 to 1.00", "Term SOFR plus 2.00%" beside "1.75%",
    "July 25, 2030" beside "December 22, 2030", "Commitments of 1,000,000,000" beside
    "$750,000,000", "50.0000 shares" beside "45.4545 shares". Each class now compares in its own
    unit:

    * a MONEY figure is stated when the quote states the same amount in the same currency, at any
      scale ("$1.5 billion" is "$1,500,000,000"), or prints it as a conformed replacement;
    * a WHOLE DATE when the quote states the same day, in any form; a year outside a date when the
      quote states the year;
    * a RATIO when the quote states it against one, in any form ("4.50x" is "4.50 to 1.00"), or
      strikes it in a conformed copy;
    * a PERCENT when the quote states it as a percent or in basis points, and 0% when it reads
      "zero" (a floor);
    * an UNMARKED AMOUNT when the quote states the amount, marked or not.

    `release_parse.quoted_figures` is not used here: its figures carry no currency and no span, and
    it reads "zero" in every unit."""
    in_value = _money(value)
    taken = [f.span for f in in_value]
    dates = [d for d in _dates(value) if not any(a <= d[2][0] < b for a, b in taken)]
    taken += [d[2] for d in dates]
    quoted_dates = {d for d, _, _ in _dates(quote, conformed=True)}
    years = [y for y in _YEAR.finditer(value)
             if not any(a <= y.start() < b for a, b in taken)]
    # in the quote a year may be fused to a prefix ("FY2030"), so only digits may not touch it
    lone = [(y.start(), y[0]) for y in years if not re.search(rf"(?<!\d){y[0]}(?!\d)", quote)]
    whole = [(sp[0], s) for d, s, sp in dates if d not in quoted_dates]
    missing = [s for _, s in sorted(lone + whole)]
    quoted_money = _money(quote, replacements=True)
    stated = {(f.currency, f.amount) for f in quoted_money}
    missing += [f.stated for f in in_value if (f.currency, f.amount) not in stated]
    ratios = [r for r in _ratios(value) if not any(a <= r[2][0] < b for a, b in taken)]
    taken += [r[2] for r in ratios]
    quoted_ratios = {r for r, _, _ in _ratios(quote, conformed=True)}
    missing += [s for r, s, _ in ratios if r not in quoted_ratios]
    pcts = [p for p in _pcts(value) if not any(a <= p[2][0] < b for a, b in taken)]
    taken += [p[2] for p in pcts]
    quoted_pcts = {p for p, _, _ in _pcts(quote)}
    zero = re.search(r"\bzero\b", quote, re.I) is not None
    missing += [s for p, s, _ in pcts if p not in quoted_pcts and not (p == 0 and zero)]
    # a percent or a ratio in the quote states only itself (Codex P2, round 1): its "1.750%" is no
    # unmarked 1.750, so a value's "1.750 shares" is not stated by it
    typed = [sp for *_, sp in _ratios(quote, conformed=True)] + [sp for *_, sp in _pcts(quote)]
    quoted_amounts = {a for a, _ in _bare(quote, typed)} | {f.amount.normalize()
                                                             for f in quoted_money}
    missing += [s for a, s in _bare(value, taken) if a not in quoted_amounts]
    return list(dict.fromkeys(missing))


def _quoted_clauses(quote: str, kept: dict[str, str]) -> str:
    """The term's quote, and the own clause of each rate component KEPT by one (`rate_components`,
    each a span of the exhibit) — the exhibit text a value may state its figures from, and the text
    the page stores beside it (`component_quotes`). A withheld component's clause vouches for
    nothing: the page would cite a clause it does not keep (review round 0).

    The clauses are joined by " | ", which no conformed-copy reader (`_REPLACEMENT`, `_STRUCK`,
    `_DATE_CONFORMED`) or range reader crosses: one clause's last figure is never read as struck
    for, or replaced by, the next clause's first."""
    return " | ".join([quote, *dict.fromkeys(kept.values())])


def rate_components(t: dict[str, Any], quote: str, source: SourceText) -> RateComponents:
    """The model's rate components that a QUOTE STATES (`release_parse.figure_stated`, in the
    component's unit): the term's own quote, or a clause of the component's own that is a span of
    the exhibit (``source``). A component neither states is WITHHELD — its field stays None and the
    reason names the figure — never printed as a fact.

    THE QUOTE WAS CHECKED; THE COMPONENTS BESIDE IT WERE NOT (2026-10-28). #804 proved each quote is
    a span of its exhibit, and #829's `figure_in_own_quote` then found 29 of 48 committed rate
    components that their own quote does not state. Each is in its exhibit (checked one by one in
    the SEC cache): 21 floors and 3 margins in another clause — "plus the Applicable Rate" beside a
    definition stating 0.50%, a LIBO Rate "deemed to be zero" — and 5 margins that are one level of
    a pricing grid, only WLK's stating which level was in effect. The first kind is kept now with
    its own clause; the grid tier and anything else unquoted is withheld."""
    values: dict[str, float | None] = {}
    quotes: dict[str, str] = {}
    withheld: dict[str, str] = {}
    for key, unit in RATE_COMPONENTS.items():
        v = _opt_float(t.get(key))
        values[key] = None
        if v is None:
            continue
        if figure_stated(quote, v, (unit,)):
            values[key] = v
            continue
        own = _opt_str(t.get(_OWN_QUOTE[key])) or ""
        own_found = bool(own) and source.match(own).found
        if own_found and figure_stated(own, v, (unit,)):
            values[key], quotes[key] = v, own
            continue
        why = ("its own quote is not in the exhibit" if own and not own_found
               else "its own quote does not state it" if own
               else "the term's quote does not state it and no quote of its own was given")
        figure = f"{v:g} bps" if unit == "bps" else f"{v:g}%"
        withheld[key] = f"{_COMPONENT_NAME[key]} {figure} withheld — {why}"
    return RateComponents(values, quotes, withheld)



# --- WHAT IS THIS DOCUMENT? (identify-or-refuse) ----------------------------------------------
#
# THE POINTER'S ``family`` IS A GUESS, AND IT WAS BEING PRINTED AS A FACT. `_covenant_pointers`
# finds execution filings with a CLASS-GENERIC efts phrase ("Indenture", "Credit Agreement"), so
# two instrument families sharing a phrase partition ONE hit list under a global `seen` set — the
# second family is handed whatever the first did not take. Measured 2026-09-28 over the 26 committed
# dossiers: 11 of them have >=2 agreement-class families on one phrase. BURL's ABL amendment sat at
# position 14 of its "Indenture" list and was labelled a 2.25% convertible note; VRRM's revolving
# credit agreement was labelled a term loan; WERN's pointer labelled a STOCK PURCHASE AGREEMENT as
# an unsecured credit agreement, and NKE's and TGT's labelled EXECUTIVE OFFER LETTERS as material
# contracts — all four were being fed to a covenant-term extractor.
#
# The document is the only thing that knows what it is, so ask it. These read the exhibit's head
# deterministically (no LLM): `agreement_title` returns the contract's SELF-DECLARED name normalised
# to its BASE (so an amendment groups with what it amends), and `is_debt_agreement` decides whether
# a covenant extractor should see it at all. A document we cannot identify is REFUSED and flagged —
# never extracted under a guessed label.
_DOC_HDR = re.compile(r"^\s*EX-[\w\.\-]+\s+\d+\s+\S+\s+", re.I)
_BOILER = re.compile(
    r"\b(?:EX-[\w\.\-]+|Document|Exhibit\s+No\.?\s*[\d\.\-]+|Exhibit\s+[\d\.\-]+|"
    r"EXECUTION\s+(?:VERSION|COPY)|CONFORMED\s+COPY|Published\s+CUSIP\S*|"
    r"\d{4}-\d{2}-\d{2}|[\d]{4}-[\d\-]{4,})\b", re.I)
_W = r"[A-Z][A-Z0-9&'\.\-]*"
_NOUN = r"(?:AGREEMENT|INDENTURE|NOTES?|GUARANTY|GUARANTEE|DEBENTURE)"
#: The words a capitals title is built of, up to its noun — shared by `_HEADING_TITLE`.
_TITLE_WORDS = rf"(?:{_W}\s+|\d[\w\-]*\s+|NO\.\s+|OF\s+|TO\s+|AND\s+|THE\s+){{1,14}}"
_TITLE = re.compile(rf"\b({_TITLE_WORDS}{_NOUN})\b")
_ORD = (r"FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|TWELFTH|"
        r"THIRTEENTH|FOURTEENTH|FIFTEENTH|NO\.\s*\d+|\d+(?:ST|ND|RD|TH)?")
#: "SIXTH AMENDMENT TO ..." / "AMENDMENT NO. 3 TO ..." — the instance, stripped to reach the base.
_AMEND_PREFIX = re.compile(
    rf"^(?:(?:{_ORD})\s+)?(?:AMENDMENT|AMENDED)\s*(?:NO\.\s*\d+\s*)?(?:AND\s+RESTATEMENT\s+)?"
    rf"(?:TO|OF)\s+(?:THE\s+)?", re.I)
_LEAD_NOISE = re.compile(r"^(?:EXISTING\s+|THAT\s+CERTAIN\s+|THE\s+|TO\s+|A\s+)+", re.I)
#: A CUSIP or an amount fragment in front of the title ("65410VAW81 364-DAY CREDIT AGREEMENT";
#: "000 CREDIT AGREEMENT" from "$1,000"). The token must CONTAIN A DIGIT — without that guard
#: ``[A-Z0-9]{6,}`` also eats the first real word, turning "AMENDED AND RESTATED CREDIT AGREEMENT"
#: into "AND RESTATED CREDIT AGREEMENT". A hyphenated token is kept: "364-DAY" is part of the name.
#: A YEAR IS NOT A CODE. "2021 CREDIT AGREEMENT" and "2024 CREDIT AGREEMENT" are different
#: facilities, and stripping the year makes them one title — manufacturing exactly the
#: collision the collapse below has to resolve. 19xx/20xx is kept; "000" (from "$1,000")
#: and a CUSIP are still stripped. Measured 2026-09-28: NO title in the 144-head corpus
#: carries a leading year, so this changes nothing observable today — it is a latent case
#: closed at the same time as the collision it would cause.
#: CASE-INSENSITIVE ON THE CODE BRANCH. Filers emit the id in the document's own case, and
#: WERN's is LOWERCASE — "wern-20260605ex101 1758963679 24780046 AMENDMENT NO. 3 TO LOAN AND
#: SECURITY AGREEMENT". An `[A-Z0-9]` class never matched it, the id survived into the title,
#: and the trailing `.upper()` made the published heading LOOK uppercase, which is why a
#: hand-typed uppercase fixture passed while the real document still failed (#655). The DIGIT
#: requirement is what keeps this safe: a real word carries no digit, so "AMENDED" and
#: "amended" are both left alone, and a hyphen still protects "364-DAY" / "FIVE-YEAR".
#: A NUMBER BEFORE A DURATION IS PART OF THE NAME TOO, hyphen or not (2026-10-18). TJX's 2020
#: facility heads itself "364 DAY REVOLVING CREDIT AGREEMENT" — a space, no hyphen — and the bare
#: "364" read as an amount fragment, so the page published "DAY REVOLVING CREDIT AGREEMENT". A
#: number followed by DAY/WEEK/MONTH/YEAR(S) is kept; "000 CREDIT AGREEMENT" (from "$1,000") and
#: EPAM's "00 REVOLVING …" are still stripped. Measured over the 114 titled exhibits in the EDGAR
#: cache through `html_to_text`: 7 captured titles start with a bare number, and this changes
#: exactly one of them — TJX's.
_LEAD_CODE = re.compile(
    r"^(?:(?!(?:19|20)\d{2}\b)(?![\d,\.]+\s+(?i:DAY|WEEK|MONTH|YEAR)S?\b)"
    r"(?:[\d,\.]+|(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{6,})\s+)+")
#: An amendment whose own title does not name its contract ("AMENDMENT AND RESTATEMENT AGREEMENT")
#: says so in the next clause — "to that certain Credit Agreement dated ...".
_BASE_REF = re.compile(
    r"(?:to|amends?|amending)\s+th(?:at|e)\s+certain\s+([^,;\.]{6,90}?)\s*,?\s*dated|"
    r"\bthe\s+[\u201c\"]?((?:[A-Z][\w\-]*\s+){0,5}(?:Credit|Loan|Indenture|Note)\s*"
    r"[\w\s]{0,24}?Agreement)", re.I)
#: A one-word self-declared title, anchored at the START of the cleaned head
#: (see `agreement_title`).
_BARE_NOUN = re.compile(r"^(INDENTURE|DEBENTURE)\b", re.I)
#: AN AMENDMENT HEADING THAT NAMES NO CONTRACT (2026-11-04): "REPRICING AMENDMENT, DATED AS OF
#: MARCH 16, 2018, BY AND AMONG ..." and "AMENDMENT NO 2. (INCREMENTAL FACILITY AMENDMENT)" (SMPL),
#: "FIRST AMENDMENT THIS FIRST AMENDMENT ... to the Credit Agreement referenced below" (NCNO). Such
#: a document names its contract only in the recital, so `agreement_title` reads it there
#: (`_RECITAL_REF`). ANCHORED AT THE START of the cleaned head: TGT's 8-K cover document cites "the
#: Credit Agreement" too, and only the heading says a document IS an amendment. CAPITALS ONLY, for
#: `_IS_AMENDMENT`'s reason: a heading is set in capitals. A title-cased heading names its contract
#: itself (VRRM's "Amendment No. 4 to REVOLVING CREDIT Agreement"), and its recital's defined term
#: ("Credit Agreement") would mis-name it, so it is not read here. Measured at 4a820016 over the 184
#: exhibits on the pointer rows of the 25 committed pages that have them: it names six, four of
#: them a credit agreement (SMPL x2, NCNO's First Amendment, BURL's 2014 Amendment No. 4) and two an
#: office lease (NCNO, refused). Three of those four newly reach the extractor; BURL's is past its
#: cost bound. NOT "... OF AMENDMENT": a CERTIFICATE or ARTICLES OF AMENDMENT amends a charter.
_AMEND_HEAD = re.compile(r"^(?:(?!OF\b)[A-Z][A-Z\-]*\s+){0,3}AMENDMENT\b")
#: THE FIRST CONTRACT THE RECITAL NAMES, OF ANY KIND — what such an amendment amends. Not
#: `_BASE_REF`: its "the ... Agreement" branch names only a Credit/Loan/Indenture/Note agreement,
#: so it would skip "the Employment Agreement" an amendment amends and take a later "the Credit
#: Agreement" — an identity reader leaning toward the answer the gate passes (review round 0).
#: A DEFINED TERM IS CAPITALISED: title-case words, plus "and"/"of" ("Amended and Restated"), so
#: "the Lenders party to the Credit Agreement" names CREDIT AGREEMENT, not the sentence, and
#: SMPL's "the (a) Credit Agreement" is passed over for its "the “ Credit Agreement ”".
_RECITAL_REF = re.compile(
    r"\b(?:that\s+certain|the)\s+[\u201c\"]?\s*((?:(?:[A-Z][\w'\-]*|and|of)\s+){1,6}"
    r"(?:Agreement|Indenture|Lease|Notes?|Guarant(?:y|ee)|Plan|Letter))\b")
#: A TITLE-CASED HEADING IS READ IN CAPITALS (STATE row 63, 2026-11-16). `_TITLE` reads a heading
#: set in capitals, and five real debt contracts on committed pointer rows head themselves in title
#: case: VRRM's "Amendment No. 4 to REVOLVING CREDIT Agreement", CNXC's "Third Amendment to
#: Receivables Financing Agreement" and its Fourth, and NFLX's two "... Senior Notes due 2028
#: Purchase Agreement" heads. Each read as no title, so E5 refused it before any model call. A
#: heading's case is typography, not identity, so its words are upper-cased and read by `_TITLE`'s
#: grammar, then normalised exactly as a capitals title is. Two limits keep this a heading reader:
#: - THE HEADING RUN only: the words at the head's start, before its first prose word. That keeps
#:   the body out, for `_IS_AMENDMENT`'s reason: a base contract's body says "No amendment to this
#:   Agreement shall be effective ...", and that never starts a head. The run takes capitalised
#:   words, numbers and amounts, and only the lowercase words a title carries: `_TITLE`'s own OF,
#:   TO, AND and THE, and DUE, a note's maturity ("Senior Notes due 2028"). Any other lowercase
#:   word, or a mark such as "(", ":", "–" or "“", ends it. A sentence that opens inside the run
#:   ("... Agreement This Third Amendment ...") is cut where `_clean_title` cuts a capitals one.
#: - A CONTRACT NOUN ends the title: AGREEMENT, INDENTURE, GUARANTY or GUARANTEE, never an
#:   INSTRUMENT (NOTES, DEBENTURE). A press release headlines in title case too, and names the
#:   instrument it announces: CNXC's 2026 release "Concentrix Prices $600 Million Senior Notes
#:   Offering" read as "MILLION SENIOR NOTES" and passed the gate until this limit.
#: Measured over the 3,575 EDGAR archive documents in the operator's cache (2026-11-16), with the
#: guards below: 8 heads read as untitled gain a title. 6 are debt contracts: the five above, and
#: CNXC's Fifth Amendment to its Receivables Financing Agreement, which no committed pointer
#: targets. 2 are not, and the gate refuses both. One is an exchange agreement for convertible notes
#: (BURL). The other is a reader cut from an award agreement (LLY), not that document's own name.
#: Without the guards, a 9th read cut a VRRM press-release headline at "Termination of Agreement".
#: No other read moves.
_HEADING_RUN = re.compile(
    r"^(?:(?:[A-Z][\w&'\.\-]*,?|\$?\d[\w,\.%\-]*|of|to|and|the|due)\s+)+")
_HEADING_TITLE = re.compile(rf"\b({_TITLE_WORDS}(?:AGREEMENT|INDENTURE|GUARANTY|GUARANTEE))\b")
#: A TITLE-CASED RUN THAT IS NOT A CONTRACT'S OWN HEADING (#1088 review, round 1). In capitals a
#: heading is a contract's; in title case the same words may be a headline, an index, a contents
#: page or a notice ABOUT one, and each would pass the gate under the contract it names. These
#: hold the run to a contract's own heading, read in capitals:
#: - not an INDEX, a table of CONTENTS or a NOTICE OF ... lead ("Exhibit Index Exhibit No.
#:   Description 10.1 Credit Agreement", "Notice of Borrowing Under Credit Agreement");
_NOT_A_HEADING_LEAD = re.compile(r"^(?:EXHIBIT\s+INDEX|INDEX|TABLE\s+OF\s+CONTENTS|CONTENTS|"
                                 r"NOTICE\s+OF)\b")
#: - no REPORTING VERB before the noun: a headline reports ("... Announces Amendment to Credit
#:   Agreement", "... Closes $500 Million Revolving Credit Agreement"), a contract's name does not.
#:   Present tense only, as headlines are set: a past form is often a title's adjective (SECURED,
#:   EXTENDED, AMENDED AND RESTATED);
_REPORTING_VERB = re.compile(
    r"\b(?:ANNOUNCES|CLOSES|COMPLETES|ENTERS|PRICES|RECEIVES|REPORTS|SIGNS|SECURES|OBTAINS|"
    r"EXTENDS|EXPANDS|AMENDS|LAUNCHES|ISSUES|FILES|PROVIDES|DECLARES|AGREES|REACHES|TERMINATES|"
    r"UPSIZES|REFINANCES)\b")
#: - no amount IN WORDS in the title: a contract states its amount in digits ahead of its name
#:   ("$1,900,000,000 5.875% Senior Notes due 2028 Purchase Agreement"); "$500 Million" is a
#:   headline's, and reads as "MILLION REVOLVING CREDIT AGREEMENT";
#: - no ARTICLE heading in the title: "... Article I Definitions Article II The Guaranty" is a
#:   contents listing, which can run without its "Table of Contents" lead.
#: NOT A FIGURE RULE ON THE RUN: NFLX's own headings carry the issuer, the principal and the coupon
#: ahead of the name, so a run with figures is refused only where its title is.
_NOT_A_TITLE = re.compile(r"\b(?:MILLION|BILLION|THOUSAND)\b|\bARTICLE\s+[IVXLC\d]+\b")
#: The capture ran past the heading into the body — a title, not a sentence.
_PROSE = re.compile(r"\b(ENTERED|DATED|MADE|WHEREAS|BETWEEN|AMONG|BY\s+AND|HEREBY|PURSUANT|"
                    r"MEANING|ASCRIBED|THERETO|DEFINED|REFERRED)\b", re.I)
#: WARRANT and SECURITIES PURCHASE are here because ``_CORE_AGREEMENT`` deliberately TARGETS
#: those filenames (``securitiespurchase``, ``warrant``) — a convertible is issued under a
#: securities purchase agreement and its warrant, and without these two the gate refuses the
#: very documents the exhibit selector was written to fetch.
_DEBT = re.compile(r"\b(CREDIT|LOAN|INDENTURE|NOTES?|DEBENTURE|FACILIT\w*|REVOLV\w*|SECURITY|"
                   r"PLEDGE|GUARANTY|GUARANTEE|FINANCING|RECEIVABLES|BOND|WARRANT|"
                   r"SECURITIES\s+PURCHASE)\b", re.I)
#: Documents that reach a covenant pointer and are NOT debt: equity awards, offer and transition
#: letters, purchase and merger agreements, SPAC-era support/escrow papers, capped-call confirms.
_NOT_DEBT = re.compile(
    r"\b(STOCK\s+PURCHASE|SHARE\s+PURCHASE|ASSET\s+PURCHASE|SUBSCRIPTION|MERGER|EMPLOYMENT|"
    r"SEVERANCE|RETENTION|AWARD|INCENTIVE|OPTION|PUT-CALL|LEASE|SETTLEMENT|LICENSE|SUPPLY|"
    r"CONSULTING|SEPARATION|TRANSITION|REGISTRATION\s+RIGHTS|INVESTOR\s+RIGHTS|"
    r"TAX\s+RECEIVABLES?|LIMITED\s+LIABILITY\s+COMPANY|EMPLOYEE\s+MATTERS|ESCROW|INDEMNI\w*|"
    r"SUPPORT|FRAMEWORK|TRUST\s+AGREEMENT|VOTING\s+TRUST|STOCKHOLDER|"
    # TRUST appears ONLY as TRUST AGREEMENT / VOTING TRUST: a bond's own contract is routinely
    # titled "TRUST INDENTURE", and a bare \bTRUST\b refused every one of them.
    r"RECEIVABLES?\s+AGREEMENT)\b", re.I)


#: "SIXTH AMENDMENT TO ...", "AMENDMENT NO. 3 TO ..." — the document presents itself as amending
#: another contract, so it shares that contract's identity. Read from the HEAD only: a base
#: agreement mentions the word "amendment" throughout its own body (amendment clauses, defined
#: terms), so a whole-document search would call almost everything an amendment.
#: CASE-SENSITIVE ON PURPOSE — an agreement HEADING is set in capitals, and a base contract's body
#: is full of the same words in prose: "No amendment to this Agreement shall be effective without
#: ...". Matching case-insensitively called such a contract an amendment and re-opened the merge
#: from the other side. A title-cased heading is still caught by ``_AMEND_PREFIX`` on the parsed
#: title, which is case-insensitive; this fallback exists only for headings like CNXC's "AMENDMENT
#: AND RESTATEMENT AGREEMENT", which names no contract and so never reaches that prefix.
_IS_AMENDMENT = re.compile(
    rf"\b(?:AMENDMENT\s+(?:NO\.\s*\d+\s+)?TO|(?:{_ORD.upper()})\s+AMENDMENT|"
    rf"AMENDMENT\s+AND\s+RESTATEMENT\s+AGREEMENT)\b")


def is_amendment(text: str) -> bool:
    """Does the exhibit present itself as an amendment TO another contract?"""
    h = re.sub(r"\s+", " ", text[:1500])
    h = re.sub(r"\s+", " ", _BOILER.sub(" ", _DOC_HDR.sub("", h))).strip()
    m = _TITLE.search(h[:1500])
    if m is not None and _AMEND_PREFIX.search(_clean_title(m.group(1))):
        return True
    # A heading that is an amendment and names no contract (`_AMEND_HEAD`) — what `agreement_title`
    # reads from the recital. SMPL's two read True below only because `_ORD.upper()` turns `\d`
    # into `\D`, so `_IS_AMENDMENT` matches any capitals "<words> AMENDMENT"; they must not depend
    # on that.
    if m is None and _AMEND_HEAD.match(h):
        return True
    # A title-cased heading, read in capitals (`_HEADING_RUN`): CNXC's "Third Amendment to
    # Receivables Financing Agreement" is an amendment by its own heading, as a capitals one is.
    # Codes first, as `agreement_title` strips them: `_AMEND_PREFIX` is anchored at ^, so a filing
    # id in front of the heading ("20260605EX101 1758963679 ...", WERN's shape) would hide it.
    t = _heading_title(h) if m is None else None
    if t is not None and _AMEND_PREFIX.search(
            _LEAD_CODE.sub("", _clean_title(t.group(1))).strip(" .,-")):
        return True
    return bool(_IS_AMENDMENT.search(h[:900]))


def _heading_title(h: str) -> re.Match[str] | None:
    """The cleaned head's title-cased heading read in capitals: `_HEADING_TITLE` over the heading
    run (`_HEADING_RUN`) upper-cased. None when the head has no run, the run names no contract
    noun, or the run is not a contract's own heading (`_NOT_A_HEADING_LEAD`, `_REPORTING_VERB`,
    `_NOT_A_TITLE`)."""
    run = _HEADING_RUN.match(h)
    if run is None:
        return None
    words = run.group(0).upper()
    if _NOT_A_HEADING_LEAD.match(words):
        return None
    m = _HEADING_TITLE.search(words)
    if m is None or _REPORTING_VERB.search(words[:m.end()]) or _NOT_A_TITLE.search(m.group(1)):
        return None
    return m


def _clean_title(t: str) -> str:
    t = re.sub(r"\s+", " ", t).strip(" .,-")
    t = re.sub(r"\bTHIS\b.*$", "", t).strip(" .,-")  # the body sentence ran into the heading
    half = len(t) // 2  # filers emit the title twice: HTML <title> then the body heading
    if half and t[:half].strip() == t[half:].strip():
        t = t[:half].strip()
    return t


def agreement_title(text: str) -> str | None:
    """The agreement's SELF-DECLARED name, normalised to the BASE contract — or None when no
    agreement title is read from the head (an offer letter, a dealer confirmation, and any head
    whose title this reader does not parse). Deterministic."""
    h = re.sub(r"\s+", " ", text[:3000])
    h = re.sub(r"\s+", " ", _BOILER.sub(" ", _DOC_HDR.sub("", h))).strip()
    m = _TITLE.search(h[:1500])
    if m is None:
        # A bare one-word title. "INDENTURE dated as of ..." is the CANONICAL head of a note
        # indenture — the convertible document this extractor exists for — and `_TITLE` needs
        # at least one word BEFORE the noun, so it matched nothing and the indenture was
        # refused as "no agreement at all". Anchored at the head, so it cannot pick up a noun
        # from the body.
        b0 = _BARE_NOUN.match(h)
        if b0:
            return b0.group(1).upper()
        # An amendment heading naming no contract: the contract is the first one its recital
        # names (`_AMEND_HEAD`, `_RECITAL_REF`). Whether that contract is debt is
        # `is_debt_agreement`'s call, not this function's: an amendment to a lease is named for
        # the lease, and refused for it.
        r = _RECITAL_REF.search(h) if _AMEND_HEAD.match(h) else None
        if r is not None:
            return _as_title(_LEAD_NOISE.sub("", _clean_title(r.group(1))))
        # A title-cased heading, read in capitals (`_HEADING_RUN`) and normalised below exactly as
        # a capitals title is. Tried last, so every head an earlier branch titles keeps its
        # title.
        m = _heading_title(h)
        if m is None:
            return None
    # CODES FIRST, THEN THE AMENDMENT PREFIX. `_AMEND_PREFIX` is anchored at ^, so while a filing
    # id still sits in front of the title it cannot match and the amendment INSTANCE survives
    # normalisation. WERN's Amendment No. 3 is the real case: its head begins
    # "20260605EX101 1758963679 24780046 AMENDMENT NO. 3 TO LOAN AND SECURITY AGREEMENT", and with
    # the strips in the other order it published under exactly that string — a filing id rendered
    # as a contract name, and the amendment split from the base it amends into a SECOND group,
    # which is the merge failure the normalisation exists to prevent.
    t = _LEAD_CODE.sub("", _clean_title(m.group(1))).strip(" .,-")
    t = _LEAD_NOISE.sub("", _AMEND_PREFIX.sub("", t)).strip(" .,-")
    if t and not _DEBT.search(t) and re.search(r"AMENDMENT", h[:900], re.I):
        b = _BASE_REF.search(h)
        if b:
            cand = _LEAD_NOISE.sub("", _clean_title(b.group(1) or b.group(2))).strip(" .,-")
            if cand and _DEBT.search(cand):
                t = cand
    return _as_title(t)


def _as_title(t: str) -> str | None:
    """A captured name as a title: upper-cased, or None when it is a sentence or too short."""
    t = t.strip(" .,-").upper()
    if _PROSE.search(t):
        return None
    return t if len(t.split()) >= 2 and len(t) >= 8 else None


#: A PURCHASE CONTRACT: a debt contract the gate passes under which notes are SOLD TO INITIAL
#: PURCHASERS, while an indenture governs them. NFLX's "SENIOR NOTES DUE 2028 PURCHASE AGREEMENT"
#: names its notes and then "PURCHASE AGREEMENT". `extract_covenant_terms` gives one a cost-bound
#: slot only after every other debt contract has had one (operator, 2026-11-16).
#: TWO PURCHASE AGREEMENTS GOVERN, AND ARE NOT RANKED LAST (#1088 review, round 1):
#: - a private placement's NOTE PURCHASE AGREEMENT, under which notes are sold to insurers with
#:   their financial covenants and no indenture;
#: - a PIPE convertible's SECURITIES PURCHASE AGREEMENT, the document `_DEBT` admits SECURITIES
#:   PURCHASE for.
#: Read from the title, so a non-debt purchase agreement (WERN's STOCK PURCHASE) is refused before
#: this asks. Measured over the 3,575 cached EDGAR archive documents (2026-11-16): 3 titles the
#: gate passes match. Those are NFLX's two notes purchase agreements and a 2020 CONVERTIBLE SENIOR
#: NOTES DUE 2025 PURCHASE AGREEMENT (CIK 784199), which no committed page's pointer targets. That
#: one is an initial purchasers' agreement and is ranked last. None reads NOTE PURCHASE or
#: SECURITIES PURCHASE.
_PURCHASE_CONTRACT = re.compile(r"(?<!\bNOTE\s)(?<!\bSECURITIES\s)\bPURCHASE\s+AGREEMENT\b")


def is_debt_agreement(title: str | None) -> bool:
    """Should a COVENANT extractor see this document? Only a debt contract — never an equity award,
    an offer letter or a purchase agreement, whatever instrument the pointer guessed."""
    if not title:
        return False
    return bool(_DEBT.search(title)) and not _NOT_DEBT.search(title)


# --- the coverage rule (STATE row 63, 2026-11-16): which located debt contracts still govern ------
#
# A credit analyst reads every document that governs debt still outstanding: each live instrument's
# governing agreement and its amendment chain. They skip a document a later one displaced, and one
# whose debt has ended. Everything here is read from the DOCUMENTS' OWN WORDS, deterministically:
# - an exhibit's IDENTITY, the agreement it is (its title and its own date) and, for an amendment,
#   the agreement it amends ("to Revolving Credit Agreement, dated as of March 1, 2018");
# - what a later exhibit DISPLACES: an agreement it names by title and date and binds to a defined
#   term ("that certain Revolving Credit Agreement, dated as of the Original Closing Date (... the
#   “Original ABL Credit Agreement”)"), and then amends and restates, substitutes for, supersedes,
#   or states terminated ("the 2025 Credit Agreement has been, or concurrently ... will be,
#   terminated").
# An exhibit is SUPERSEDED when a located exhibit filed strictly later displaces the agreement it is
# or amends. Its notes are TERMINATED when its title states a maturity year before the page's
# reference date and the CIQ panel carries no instrument maturing that year. Anything else is
# READ, however old: a dead document the words cannot show dead costs a call, while a live one
# skipped would cost the page its terms.

#: A date as an agreement states it.
_REF_DATE = rf"{_MON}\s+\d{{1,2}}(?:st|nd|rd|th)?\s*,\s*(?:19|20)\d\d"
#: A word of an agreement's name in a recital or a definition: capitalised, a number ("364-Day",
#: "2025"), or the small words a name carries.
_REF_WORD = r"(?:[A-Z][\w'&\.\-]*|\d[\w\-]*|of|and|the)"
#: "<Name> Agreement, dated as of <date>" — the date may be a defined one ("the Original Closing
#: Date"), resolved by its own definition. A parenthetical between the two is skipped, except the
#: document's own ("(this “Amendment”)"), which dates the document itself, not what it names.
_REF_NAME = rf"(?P<name>(?:{_REF_WORD}\s+){{0,9}}?(?:Agreement|AGREEMENT|Indenture|INDENTURE))"
_REF_WHEN = (rf"dated\s+as\s+of\s+"
             rf"(?P<when>{_REF_DATE}|the\s+(?:[A-Z][\w\-]*\s+){{0,4}}Date)")
_NOT_OWN_PAREN = r"\((?!\s*this\b)"
_AGREEMENT_REF = rf"{_REF_NAME}\s*,?\s*(?:{_NOT_OWN_PAREN}[^()]{{0,200}}\)\s*,?\s*)?{_REF_WHEN}"
#: A defined term that names an AGREEMENT ("Existing Credit Agreement", "2025 Credit Agreement",
#: "Original ABL Credit Agreement"). Only such a term is bound: a recital's next quoted term may be
#: a party ("the “Administrative Agent”"), and nothing it says displaces an agreement.
_AGREEMENT_TERM = r"[“\"]\s*(?P<term>[A-Z0-9][^”\"]{0,60}?(?:Agreements?|Indenture))\s*[”\"]"
#: A recital: "party to that certain <agreement>, dated as of <date> (… the “<term>”)", or with
#: the term inside a parenthetical before the date (CNXC's 2021 amendment: "that certain Credit
#: Agreement (as amended, … the “Existing Credit Agreement”), dated as of October 16, 2020").
#: The gap between the agreement and its term never crosses a SECOND agreement (independent review,
#: F5): "that certain Credit Agreement, dated … and that certain Term Loan Agreement, dated … (the
#: “Existing Term Loan Agreement”)" binds the term to the Term Loan Agreement only. An AMENDMENT
#: named in the gap is the agreement's own history and may stand there: EPAM's "Credit Agreement
#: dated as of May 24, 2017, as amended by the First Amendment to Credit Agreement …, and the
#: Second Amendment … (as so amended, the “Existing Credit Agreement”)", TJX's "(as amended by that
#: certain First Amendment to 2026 Revolving Credit Agreement, …, the “2026 Revolving Credit
#: Agreement”)" (`_second_agreement`).
#: And the term a recital binds is never a DEFINITION's own ("“2025 Credit Agreement” means …"),
#: which the gap would otherwise reach across a sentence end (found writing review F3's pin).
_BIND_RECITAL = re.compile(
    rf"\b(?:that\s+certain|the)\s+{_AGREEMENT_REF}(?P<gap>[^“”\"]{{0,240}}?){_AGREEMENT_TERM}"
    rf"(?!\s*(?:means|shall\s+mean)\b)")
#: An agreement named in a recital's gap: its name's words, then the noun. "No. 1" is a word of an
#: amendment's name (#1090 verification, N1, deferred to the selector): without it the chain broke
#: at "No.", so UBER's "Amendment No. 1 to the Term Loan Agreement" read as "1 to the Term Loan
#: Agreement", a second agreement with no AMENDMENT in it, and the recital's true bind was refused.
_GAP_AGREEMENT = re.compile(r"(?:\b[A-Z0-9][\w'\-]*\s+|\bN[Oo]\.\s*|\bof\s+|\bto\s+|\band\s+|"
                            r"\bthe\s+){0,8}?\b(?:Agreement|AGREEMENT|Indenture|INDENTURE)\b")
#: AN AGREEMENT THAT IS THE OBJECT OF "AMENDMENT … TO" IS NAMED AS PART OF THE AMENDMENT (N1): in
#: "Amendment No. 1 to the Term Loan Agreement, dated as of June 13, 2018" the date is the
#: amendment's. A recital starting at that "the Term Loan Agreement" would bind its term to the
#: amendment's date: UBER's "Existing 2016 Loan Agreement" read as of 2018-06-13, not 2016-07-13,
#: and a recital of NKE's shape, "(as amended by the First Amendment to the Credit Agreement, dated
#: as of March 8, 2024, the “2022 Credit Agreement”)", displaced a live agreement of that date.
#: Read in the characters before the recital's start; such a recital binds nothing.
_OBJECT_OF_AMENDMENT = re.compile(r"\bAMENDMENT\b(?:\s+NO\.\s*\d+)?[^.;()“”\"]{0,40}?\bto\s+$",
                                  re.I)
_BIND_RECITAL_PAREN = re.compile(
    rf"\b(?:that\s+certain|the)\s+{_REF_NAME}\s*{_NOT_OWN_PAREN}[^()]{{0,200}}?{_AGREEMENT_TERM}"
    rf"[^()]{{0,120}}\)\s*,?\s*{_REF_WHEN}")
#: THE TERM DEFINED IN THE PARENTHETICAL THAT OPENS AT THE AGREEMENT'S DATE, however long its
#: history (STATE row 63, the selector, 2026-11-16): "the Amended and Restated First Lien Term Loan
#: Credit Agreement dated as of March 26, 2021 (as amended by that certain Amendment No. 1, …, as
#: amended by that certain Amendment No. 4, … prior to the Second Restatement Effective Date (as
#: defined below), the “Existing Credit Agreement”)" (VRRM's 2025 term-loan restatement: 454
#: characters, past `_BIND_RECITAL`'s 240). The parenthetical is read whole, one nested level deep,
#: and the term closes it; an agreement named inside it binds nothing (`_second_agreement`).
_BIND_RECITAL_AFTER = re.compile(
    rf"\b(?:that\s+certain|the)\s+{_REF_NAME}\s*,?\s*{_REF_WHEN}\s*\("
    rf"(?P<gap>(?:[^()]|\([^()]{{0,120}}\)){{0,900}}?){_AGREEMENT_TERM}\s*\)")
#: A definition: "“<term>” means [, collectively, (x)] that certain <agreement>, dated as of
#: <date>"; a collective one's "(y) that certain <agreement>" follows within `_DEFN_SPAN` chars,
#: and only in a definition that has its "(x)", before the next definition begins (independent
#: review, F3: a "(y)" in the NEXT definition is that definition's).
_BIND_DEFINITION = re.compile(
    rf"{_AGREEMENT_TERM}\s*(?:means|shall\s+mean)\s*,?\s*(?:collectively\s*,?\s*)?"
    rf"(?P<x>\(x\)\s*)?(?:that\s+certain\s+|the\s+)?{_AGREEMENT_REF}")
_NEXT_DEFINITION = re.compile(r"[“\"]\s*[A-Z0-9][^”\"]{0,80}[”\"]\s*(?:means|shall\s+mean)\b")
_BIND_SECOND = re.compile(rf"\(y\)\s*(?:that\s+certain\s+|the\s+)?{_AGREEMENT_REF}")
_DEFN_SPAN = 600
#: A term defined as two others: "“Existing Credit Agreements” means the Existing 3-Year Credit
#: Agreement and the Existing 364-Day Credit Agreement" (AMZN's 2023 five-year agreement).
_BIND_PAIR = re.compile(
    rf"{_AGREEMENT_TERM}\s*(?:means|shall\s+mean)\s*,?\s*(?:collectively\s*,?\s*)?the\s+"
    rf"(?P<a>[A-Z][^.;“”\"]{{3,60}}?)\s+and\s+the\s+(?P<b>[A-Z][^.;,“”\"]{{3,60}}?)\s*[.;]")
#: What the later document DOES to the bound agreement — the whole of it. Each was read on a
#: committed page's exhibit: amend and restate (VRRM, AMZN, EPAM, WLK, TJX), "an amendment and
#: restatement of" (AMZN 2020), "substituted for" (AMZN 2020), "provisions of … shall be superseded"
#: (CNXC), "has been … terminated" (NKE), "shall be terminated" (V), "commitments thereunder shall
#: have been terminated" (AMZN 2023), "evidence of termination of the" (TJX, a condition precedent;
#: a bare "termination of the" is also a conditional, "upon termination of the Credit Agreement").
#: "{t}" is the bound term. Over the 92 cached documents the gate passes, these read 29 displaced
#: agreements in 24 documents, each a whole-agreement restatement or termination by hand read.
_DISPLACING_VERBS: tuple[str, ...] = (
    r"\bamend(?:s|ed|ing)?\s+and\s+restate(?:s|d|ing)?\s+(?:in\s+(?:its|their)\s+entirety\s+)?"
    r"(?:the\s+)?{t}",
    r"\ban\s+amendment\s+and\s+restatement\s+of\s+the\s+{t}",
    r"\bsubstituted\s+for\s+(?:\([^)]{0,60}\)\s+)?(?:the\s+)?{t}",
    r"\bprovisions\s+of\s+the\s+{t}\s+shall\s+be\s+superseded",
    r"\bthe\s+{t}\s+(?:has|have)\s+been\s*,?\s+(?:or\s+[^.;]{0,80}?\s+will\s+be\s*,?\s+)?"
    r"terminated",
    r"\bthe\s+{t}\s+shall\s+(?:have\s+been|be)\s+terminated",
    r"\bunder\s+the\s+{t}\s+shall\s+have\s+been\s+paid\s+in\s+full\s+and\s+(?:all\s+)?(?:the\s+)?"
    r"commitments\s+thereunder\s+shall\s+have\s+been\s+terminated",
    r"\bcommitments\s+under\s+the\s+{t}\s+(?:shall\s+have\s+been|have\s+been|are\s+hereby|"
    r"will\s+be)\s+terminated",
    r"\bevidence\s+of\s+(?:the\s+)?termination\s+of\s+the\s+{t}",
    # the operative clause in the passive (the selector, 2026-11-16): "The Existing Credit
    # Agreement is, effective as of the Second Restatement Effective Date and immediately after
    # giving effect to the incurrence of the Initial Term Loans, hereby amended and restated in the
    # form attached as Exhibit B" (VRRM's 2025 and 2021 term-loan restatements). Over the 92 cached
    # gate passes it reads 49 times; the subject guard below refuses the 46 that restate a PART
    # ("Section 6.01(d) of the Credit Agreement is hereby amended and restated"), and the 3 it
    # admits are VRRM's two whole-agreement restatements (the second also restates its security
    # agreement)
    r"\b[Tt]he\s+{t}\s+is\s*,?\s*(?:[^.;()“”\"]{0,200}?,\s*)?hereby\s+amended\s+and\s+restated\b",
)
#: WHAT THE CLAUSE ENDS MUST BE THE AGREEMENT — its subject is checked on every form that has one.
#: - A clause opening on "the <term>" after a preposition is about something of or under it: a part
#:   ("Section 2.5.12 of the 2025 Credit Agreement has been … terminated"), a tranche ("the
#:   Revolving Commitments under the …"). This guard subsumes the part guard `_A_PART_OF` the rule
#:   first shipped, which every part reference reaches only through "of", "to", "in" or "under";
#:   the independent review (F6) showed removing it moved no pin, so it is removed.
_UNDER_THE = re.compile(r"\b(?:under|of|to|in|with|for)\s+$", re.I)
#: - "… outstanding under the <term> shall have been paid in full": what was outstanding must be
#:   ALL of it, in lower-case words ("all the principal, interest and fees outstanding", AMZN),
#:   never a tranche's defined term ("all the Revolving Loans outstanding") (review F4).
_ALL_OUTSTANDING = re.compile(
    r"\ball\s+(?:the\s+)?(?:[a-z]+,?\s+(?:and\s+)?){0,6}outstanding\s+$")
#: - "commitments under the <term> … terminated": all the commitments ("all", "the"), never a
#:   tranche's, in any case ("revolving commitments under the …") (F4).
_ALL_COMMITMENTS = re.compile(r"\b(?:all|the|and)\s+$", re.I)
#: What an amendment amends: in its heading ("to Revolving Credit Agreement, dated as of March 1,
#: 2018") or else the FIRST agreement its recital names ("party to that certain …", "pursuant to
#: the Credit Agreement (…) dated as of February 11, 2022" (NCNO), "reference is hereby made to the
#: (a) Credit Agreement, dated as of July 7, 2017" (SMPL), whose recital later names the acquired
#: company's March 25, 2015 credit agreement, repaid).
_AMENDS_HEADING = re.compile(rf"\b(?:to|of)\s+(?:the\s+|that\s+certain\s+)?{_AGREEMENT_REF}")
#: Where an amendment's HEADING ends: its parties ("is made by and among", "is entered into") or its
#: recitals ("W I T N E S S E T H", "WHEREAS"). The heading read stays before it, so a recital's
#: history ("as amended by that certain Amendment No. 1 to the Term Loan Agreement, dated as of
#: June 13, 2018", UBER) is never read as the base (independent review, F2).
_HEADING_END = re.compile(r"\b(?:WHEREAS|RECITALS|W\s?I\s?T\s?N\s?E\s?S\s?S\s?E\s?T\s?H|"
                          r"by\s+and\s+(?:among|between)|is\s+(?:made|entered\s+into))\b", re.I)
#: An amendment that RESTATES its agreement is that agreement anew, dated as of its own date
#: ("AMENDMENT AND RESTATEMENT AGREEMENT dated as of April 21, 2023", CNXC; VRRM's "Amendment AND
#: RESTATEMENT AGREEMENT NO. 2"). A plain amendment's own date is no agreement's (F1: NKE's
#: five-year First Amendment is dated as its 2024 364-day agreement).
_RESTATEMENT_HEAD = re.compile(r"\bAMENDMENT\s+AND\s+RESTATEMENT\s+AGREEMENT\b", re.I)
_AMENDS_RECITAL = re.compile(
    rf"\b(?:that\s+certain|to\s+the)\s+(?:\([a-z]\)\s+)?{_AGREEMENT_REF}")
#: An agreement's own date in its head: "dated as of March 7, 2025", "entered into as of …".
_OWN_DATE = re.compile(rf"\b(?:dated|entered\s+into|made(?:\s+and\s+entered\s+into)?)\s*,?\s+"
                       rf"(?:as\s+of\s+|on\s+)?(?:the\s+)?({_REF_DATE})", re.I)
#: "AMENDED AND RESTATED" (with its ordinal) is a version of an agreement, not another agreement:
#: CNXC's 2025 restatement names its predecessor "Amended and Restated Credit Agreement, dated as
#: of April 21, 2023", which E5 titles CREDIT AGREEMENT.
_RESTATED_WORDS = re.compile(r"\b(?:(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH)\s+)?AMENDED\s+AND\s+"
                             r"RESTATED\s+")
#: A panel row that may be notes: its CIQ type or its description names notes, bonds or debentures.
_NOTES_KIND = re.compile(r"\b(?:notes?|bonds?|debentures?)\b", re.I)
#: A title that states its notes' maturity: "SENIOR NOTES DUE 2024 PURCHASE AGREEMENT".
_NOTES_DUE = re.compile(r"\bNOTES\s+DUE\s+((?:19|20)\d\d)\b")
#: The head an identity is read from, and the longest verbatim clause kept as evidence.
_IDENTITY_HEAD = 6000
_EVIDENCE_CAP = 240


class AgreementKey(NamedTuple):
    """One agreement as documents name it: its name without the restatement words, upper-cased,
    and the date it is dated as of."""

    name: str
    dated: date


class Displaced(NamedTuple):
    """An agreement a document displaces, and the document's own words that say so."""

    key: AgreementKey
    words: str  # verbatim, single-spaced, ≤ `_EVIDENCE_CAP`


def _agreement_name(name: str) -> str:
    t = re.sub(r"\s+", " ", name).strip().upper()
    t = re.sub(r"^(?:THE|THAT CERTAIN|A)\s+", "", t)
    return _RESTATED_WORDS.sub("", t).strip()


def _ref_date(when: str, flat: str) -> date | None:
    """A reference's date: a date as written, or a defined one ("the Original Closing Date")
    resolved by its own definition in the same document ("“Original Closing Date” shall mean
    March 1, 2018"). None when neither reads."""
    got = _dates(when)
    if not got:
        name = re.sub(r"^the\s+", "", when.strip())
        m = re.search(rf"[“\"]\s*{re.escape(name)}\s*[”\"]\s+(?:means|shall\s+mean)\s+(?:the\s+)?"
                      rf"({_REF_DATE})", flat)
        got = _dates(m.group(1)) if m else []
    if not got:
        return None
    (y, mo, d), *_ = got[0]
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def _key(name: str, when: str, flat: str) -> AgreementKey | None:
    dated = _ref_date(when, flat)
    return AgreementKey(_agreement_name(name), dated) if dated is not None else None


def _flat_head(text: str) -> str:
    h = re.sub(r"\s+", " ", text[:_IDENTITY_HEAD * 2])
    return re.sub(r"\s+", " ", _BOILER.sub(" ", _DOC_HDR.sub("", h))).strip()[:_IDENTITY_HEAD]


def exhibit_identity(text: str, title: str,
                     amendment: bool) -> tuple[AgreementKey | None, AgreementKey | None]:
    """``(own, base)``: the agreement the exhibit is (its title and its own date) and, for an
    amendment, the agreement it amends — named in its heading ("to Revolving Credit Agreement,
    dated as of March 1, 2018") or, failing that, its recital's first "that certain <agreement>,
    dated as of <date>". A plain amendment has no ``own``: only an amendment AND RESTATEMENT is an
    agreement dated as of its own date. Either is None where its words do not read."""
    flat = re.sub(r"\s+", " ", text)
    head = _flat_head(text)
    own_m = _OWN_DATE.search(head)
    own = _key(title, own_m.group(1), flat) if own_m else None
    base = None
    if amendment:
        end = _HEADING_END.search(head)
        heading = head[:end.start()] if end else head[:600]
        # The heading's "AMENDMENT TO <agreement> dated as of <date>" may date the AMENDMENT
        # ("FIRST AMENDMENT TO CREDIT AGREEMENT AND JOINDER AGREEMENT dated as of December 27,
        # 2021", CNXC): a base dated as the exhibit itself is not its base, and the recital is
        # read instead.
        for rx, where in ((_AMENDS_HEADING, heading), (_AMENDS_RECITAL, head)):
            m = rx.search(where)
            key = _key(m.group("name"), m.group("when"), flat) if m is not None else None
            if key is not None and (own is None or key.dated != own.dated):
                base = key
                break
        if not _RESTATEMENT_HEAD.search(head[:400]):
            own = None  # a plain amendment is identified by what it amends (F1)
    return own, base


def displaced_agreements(text: str) -> list[Displaced]:
    """Every agreement the exhibit says it restates, replaces or terminates WHOLE: a defined term
    bound to "<agreement>, dated as of <date>" by a recital or a definition, and a displacing verb
    on that term (`_DISPLACING_VERBS`) whose subject is the whole agreement (`_displacing_words`).
    In document order, one entry per (term, agreement)."""
    flat = re.sub(r"\s+", " ", text)
    binds: dict[str, list[AgreementKey]] = {}

    def bind(term: str, key: AgreementKey | None) -> None:
        if key is not None and key not in binds.setdefault(term, []):
            binds[term].append(key)

    def amended(start: int) -> bool:
        """Is the recital at ``start`` the object of "Amendment … to" (`_OBJECT_OF_AMENDMENT`)?"""
        return bool(_OBJECT_OF_AMENDMENT.search(flat[max(0, start - 80):start]))

    for m in _BIND_RECITAL_PAREN.finditer(flat):
        if not amended(m.start()):
            bind(m.group("term"), _key(m.group("name"), m.group("when"), flat))
    # OVERLAPPING: a recital refused for a second agreement in its gap leaves that second
    # agreement's own recital, which starts inside the refused span, still to be read, unless that
    # agreement is the object of an amendment's name (N1)
    pos = 0
    while (r := _BIND_RECITAL.search(flat, pos)) is not None:
        pos = r.start() + 1
        if not _second_agreement(r.group("gap")) and not amended(r.start()):
            bind(r.group("term"), _key(r.group("name"), r.group("when"), flat))
    # and the term the parenthetical at the agreement's date defines, read the same way
    pos = 0
    while (r := _BIND_RECITAL_AFTER.search(flat, pos)) is not None:
        pos = r.start() + 1
        if not _second_agreement(r.group("gap")) and not amended(r.start()):
            bind(r.group("term"), _key(r.group("name"), r.group("when"), flat))
    for m in _BIND_DEFINITION.finditer(flat):
        bind(m.group("term"), _key(m.group("name"), m.group("when"), flat))
        if m.group("x") is None:
            continue
        nxt = _NEXT_DEFINITION.search(flat, m.end(), m.end() + _DEFN_SPAN)
        y = _BIND_SECOND.search(flat, m.end(), nxt.start() if nxt else m.end() + _DEFN_SPAN)
        if y is not None:
            bind(m.group("term"), _key(y.group("name"), y.group("when"), flat))
    for m in _BIND_PAIR.finditer(flat):
        a, b = binds.get(m.group("a").strip(), []), binds.get(m.group("b").strip(), [])
        if a and b:
            for k in a + b:
                bind(m.group("term"), k)
    out: list[Displaced] = []
    for term, keys in binds.items():
        words = _displacing_words(flat, term)
        if words is not None:
            out.extend(Displaced(k, words) for k in keys)
    return out


def _second_agreement(gap: str) -> bool:
    """Does a recital's gap name an agreement that is not an amendment (its history)?"""
    return any(not re.search(r"\bAMENDMENT\b", g.group(0), re.I)
               for g in _GAP_AGREEMENT.finditer(gap))


def _displacing_words(flat: str, term: str) -> str | None:
    """The first clause in which the document displaces ``term`` whole, verbatim, or None."""
    t = re.escape(term) + r"\b(?![’']s\b)"
    for tpl in _DISPLACING_VERBS:
        for m in re.finditer(tpl.replace("{t}", t), flat):
            before = flat[max(0, m.start() - 120):m.start()]
            # "the Revolving Commitments under the Existing Credit Agreement shall have been
            # terminated": a clause that opens on the term, after a preposition, is about something
            # of or under the agreement (a part, a tranche, its commitments), not the agreement
            if m.group(0).startswith("the") and _UNDER_THE.search(before):
                continue
            if m.group(0).startswith("under") and not _ALL_OUTSTANDING.search(before):
                continue
            if m.group(0).startswith("commitments") and not _ALL_COMMITMENTS.search(before):
                continue
            words = m.group(0).strip()
            return words if len(words) <= _EVIDENCE_CAP else words[:_EVIDENCE_CAP - 1] + "…"
    return None


def _same_agreement(a: AgreementKey | None, b: AgreementKey | None) -> bool:
    """One agreement: the same NAME and the same date (independent review, F1). A name that is only
    the other's tail is a doubt, and on any doubt about identity the exhibit is READ: EPAM's
    restatement names a "Credit Agreement" of May 24, 2017, which E5 titles by its cover,
    "REVOLVING CREDIT FACILITY CREDIT AGREEMENT", so that exhibit is read."""
    return a is not None and b is not None and a.dated == b.dated and a.name == b.name


def _confusable(a: AgreementKey, b: AgreementKey) -> bool:
    """Could a document mean either? The same date, and one name the other's whole tail ("CREDIT
    AGREEMENT" and "REVOLVING CREDIT AGREEMENT"; never "SECURITY AGREEMENT")."""
    if a.dated != b.dated:
        return False
    x, y = a.name.split(), b.name.split()
    n = min(len(x), len(y))
    return x[-n:] == y[-n:]


def _head_dates(text: str) -> set[date]:
    """Every whole date an exhibit's head states (`_flat_head`), as dates."""
    out: set[date] = set()
    for (y, mo, d), *_ in _dates(_flat_head(text)):
        try:
            out.add(date(y, mo, d))
        except ValueError:
            continue
    return out


def _matured_notes(title: str, reference: date | None,
                   instruments: list[CapitalInstrument] | None) -> str | None:
    """Why a title's notes have ended, or None: its stated maturity year is before the page's
    reference year AND the CIQ panel carries no instrument with principal maturing that year
    (a panel that still carries one is a disagreement, and the exhibit is read)."""
    m = _NOTES_DUE.search(title)
    # no panel (``instruments`` None, the panel UNKNOWN) says nothing about which notes remain:
    # missing data is never evidence of absence (Codex, PR #1090 round 1)
    if m is None or reference is None or instruments is None:
        return None
    # EVERY year the title states from its first "NOTES DUE" on: a multi-tranche purchase
    # agreement ("NOTES DUE 2024 AND 3.000% NOTES DUE 2031") has ended only when all have
    years = sorted({int(y) for y in re.findall(r"\b(?:19|20)\d\d\b", title[m.start():])})
    if not years or years[-1] >= reference.year:
        return None
    # the panel's own date (`ciq_maturity_date`, kept where a filing governs `maturity_date`) and
    # the governed one both count; an UNKNOWN principal is not an absent one, and neither is an
    # UNKNOWN maturity on a notes row, which may be these notes (Codex, PR #1090 round 2). An
    # undated row of another kind (commercial paper, a lease, a term loan) cannot be.
    if any(i.principal_musd != 0
           and (any((d or "")[:4] == str(y) for y in years
                    for d in (i.maturity_date, i.ciq_maturity_date))
                or (not i.maturity_date and not i.ciq_maturity_date
                    and _NOTES_KIND.search(f"{i.type} {i.description}")))
           for i in instruments):
        return None
    due = " and ".join(str(y) for y in years)
    return (f"its title states notes due {due}, before the page's reference date "
            f"({reference.isoformat()}), and the CIQ panel carries no instrument maturing in "
            f"{due}")


def _extract_from_exhibit(
    llm: LlmClient, text: str, *, name: str, ticker: str, source_ref: str,
    title: str | None = None, amendment: bool | None = None,
) -> tuple[list[CovenantTerm], list[str], str]:
    """Run the fenced tool against one exhibit → (rows, flags, raw-log). source_ref is machine-set
    here, so the model cannot invent a citation — it only fills value + a verbatim quote, and the
    quote is CHECKED against ``text``, the exhibit it was sent."""
    user = (
        f"Company: {name} ({ticker}). Exhibit: {source_ref}. Extract the terms STATED in the "
        f"exhibit below. Answer each target term (present true/false): {'; '.join(_TARGET_TERMS)}."
        f"\n\n=== EXHIBIT TEXT (verbatim, may be long) ===\n{text}"
    )
    raw = llm.extract(system=_SYSTEM, user=user, tool=_TOOL)
    source = SourceText(text)
    rows: list[CovenantTerm] = []
    flags: list[str] = []
    for t in raw.get("terms", []):
        term_name = str(t.get("name", "")).strip()
        if not term_name:
            continue
        val: Sourced[str]
        # (RC-1.5d) the optional interest-rate components — populated only on a present term; they
        # inherit ``value``'s citation (same clause). Non-interest terms simply leave them None.
        components: dict[str, Any] = {}
        stated = bool(t.get("present") and str(t.get("value", "")).strip())
        quote = str(t.get("quote", "")).strip()
        quoted = stated and source.match(quote).found
        # the components a quoted term keeps, read once: their own clauses state figures for the
        # value too (RE2-D16), and the stated branch stores them
        rc = rate_components(t, quote, source) if quoted else None
        if stated and not quoted:
            # REFUSED, NOT SHOWN. The value is withheld whole — the term stays in the row set as a
            # visible UNKNOWN whose note names the exhibit (so `governing_terms` still groups it by
            # accession), and the flag names the term. A quote that is not a span is no evidence the
            # clause was read: it may have been recalled, and a value bound to it is not
            # source-bound. THE COST, measured when this landed (2026-10-26, the 27 committed
            # dossiers at 545403de): 49 of 393 quoted terms fail. None of the 49 carries a figure
            # absent from its exhibit — they are reordered, stitched, or read across page furniture
            # — so the next re-assembly withholds values that were most likely read correctly.
            # That is the trade: the check proves reading, and a quote that cannot prove it is
            # refused rather than vouched for.
            why = ("the model gave no quote from" if not quote
                   else "the model's quote is not in")
            val = Sourced.unknown(note=f"{REFUSED_NOTE_PREFIX} {why} {source_ref}")
            flags.append(f"(E5) covenant term refused — {why} the exhibit, so it is UNKNOWN: "
                         f"{term_name} · {source_ref}")
        elif rc is not None and (unstated := unstated_in_quote(str(t["value"]),
                                                               _quoted_clauses(quote, rc.quotes))):
            # REFUSED FOR WHAT THE VALUE SAYS (audit E2-D19). The quote is the exhibit's own words;
            # a figure the value adds (any class, RE2-D16) is the model's, bound to nothing. The
            # value is withheld whole, as a quote refusal withholds it, and the flag names the
            # figures.
            # Measured at 8e6b12b1: 29 of 176 PRESENT terms on the 13 in-scope pages (9 pages);
            # none shown wrong — a sublimit read from another clause, a date added as context.
            shown = ", ".join(unstated)
            val = Sourced.unknown(note=f"{VALUE_REFUSED_NOTE_PREFIX} {shown}, which the model's "
                                       f"quote does not — {source_ref}")
            flags.append(f"(E5) covenant term refused — its value states {shown}, which its quote "
                         f"does not, so it is UNKNOWN: {term_name} · {source_ref}")
        elif rc is not None:
            note = f"verbatim: “{quote}”"
            val = Sourced.present(str(t["value"]).strip(), source_ref=source_ref, note=note)
            components = {
                "base_rate_label": _opt_str(t.get("base_rate_label")),
                **rc.values,
                "component_quotes": rc.quotes,
                "withheld_components": rc.withheld,
            }
            flags.extend(f"(E5) rate component not shown — {why}: {term_name} · {source_ref}"
                         for why in rc.withheld.values())
        else:
            val = Sourced.unknown(note=f"not stated in {source_ref}")
        rows.append(
            CovenantTerm(name=term_name, value=val, agreement_title=title,
                         agreement_is_amendment=amendment, **components)
        )
    return rows, flags, str(raw)


def _outcome(row: CovenantPointer, filename: str, kind: CovenantExhibitOutcomeKind,
             title: str | None = None, *, superseded_by: tuple[str, str] | None = None,
             evidence: str | None = None) -> CovenantExhibitOutcome:
    """What the loop did with ``row``'s targeted exhibit; ``title`` is the heading E5 read, None
    where it read none; ``superseded_by`` is the later exhibit's (accession, filename)."""
    acc, doc = superseded_by if superseded_by is not None else (None, None)
    return CovenantExhibitOutcome(accession=row.accession, filename=filename, family=row.family,
                                  outcome=kind, declared_title=title, superseded_by=acc,
                                  superseded_by_filename=doc, evidence=evidence)


class _Candidate(NamedTuple):
    """A located exhibit E5 identified as a debt contract: where it is, its text, and who it is."""

    i: int  # its index in the targets, and so in the outcomes
    row: CovenantPointer
    filename: str
    src: str
    text: str
    title: str
    own: AgreementKey | None
    base: AgreementKey | None


def _reference_date(cs: CapitalStructure) -> date | None:
    """The page's reference date, as the maturity check bounded its filings by it; None when the
    layer carries no check (then no notes are found matured, and every exhibit is read)."""
    if cs.maturity_check is None:
        return None
    try:
        return date.fromisoformat(cs.maturity_check.bound)
    except ValueError:
        return None


#: A candidate's verdict: its kind, the exhibit that superseded it, and the evidence.
_Verdict = tuple[Literal["live", "superseded", "terminated"], tuple[str, str] | None, str]


def _coverage(candidates: list[_Candidate], reference: date | None,
              instruments: list[CapitalInstrument] | None, *, all_read: bool = True,
              unnamed_dates: frozenset[date] = frozenset(),
              siblings: tuple[_Identity, ...] = ()) -> list[_Verdict]:
    """THE COVERAGE RULE — one ``(kind, superseded_by, evidence)`` per candidate, ``kind`` being
    ``live``, ``superseded`` or ``terminated``.

    SUPERSEDED: a candidate filed STRICTLY LATER displaces (`displaced_agreements`) the agreement
    this one is or amends (`exhibit_identity`, `_same_agreement`). The earliest such candidate is
    cited, with its own words. Two refusals keep a guess out:
    - a displaced agreement that could mean two agreements on the page is AMBIGUOUS, and decides
      none of them (`_ambiguous`): "Credit Agreement, dated as of March 1, 2018" would fit VRRM's
      revolver and its term loan, both dated that day. The page is every located exhibit and every
      debt agreement in a located filing beside one (``siblings``), which the loop reads too;
    - an empty or tied filing date cannot order two documents (the (X-4) rule of
      `governing_terms`), so it supersedes nothing.
    - a displaced agreement dated as a date an UNTITLED refused exhibit's head states
      (``unnamed_dates``) decides nothing: that exhibit's name was not read, so it may be the
      agreement displaced (Codex, PR #1090 round 1);
    - a page with a target that could not be read (``all_read`` False) supersedes NOTHING: the
      unread exhibit may be another agreement the displaced name fits, so no name on the page can
      be shown unambiguous (review round 0). It fails toward reading.
    TERMINATED: the title states notes whose maturity years are all past, and the CIQ panel carries
    none maturing then (`_matured_notes`). It reads only the exhibit's own title, so it applies
    whatever else on the page was read.
    Anything else is LIVE, and is read — whether the words show it live or show nothing."""
    displaced = [displaced_agreements(c.text) for c in candidates]
    pool = [i for c in candidates for i in _identities((c.row.accession, c.filename), c.own,
                                                        c.base)]
    pool += siblings
    out: list[_Verdict] = []
    for x in candidates:
        verdict: _Verdict = ("live", None, "")
        later = sorted((j for j, y in enumerate(candidates)
                        if all_read and y is not x and x.row.filing_date and y.row.filing_date
                        and y.row.filing_date > x.row.filing_date),
                       key=lambda j: candidates[j].row.filing_date)
        for j in later:
            hit = next((d for d in displaced[j]
                        if (_same_agreement(d.key, x.own) or _same_agreement(d.key, x.base))
                        and not _ambiguous(d.key, pool)
                        and d.key.dated not in unnamed_dates), None)
            if hit is not None:
                amends = _same_agreement(hit.key, x.base) and not _same_agreement(hit.key, x.own)
                y = candidates[j]
                verdict = ("superseded", (y.row.accession, y.filename),
                           f"“{hit.words}”, which names the {hit.key.name} dated "
                           f"{hit.key.dated.isoformat()} that this exhibit "
                           f"{'amends' if amends else 'is'}")
                break
        if verdict[0] == "live" and (why := _matured_notes(x.title, reference, instruments)):
            verdict = ("terminated", None, why)
        out.append(verdict)
    return out


#: One identity on the page: the exhibit (accession, file), an agreement it names, and whether that
#: is the agreement it IS (``own``) or the one it AMENDS (``base``).
_Identity = tuple[tuple[str, str], AgreementKey, Literal["own", "base"]]


def _identities(exhibit: tuple[str, str], own: AgreementKey | None,
                base: AgreementKey | None) -> list[_Identity]:
    """The identities one exhibit carries: the agreement it is, and the one it amends."""
    out: list[_Identity] = []
    if own is not None:
        out.append((exhibit, own, "own"))
    if base is not None:
        out.append((exhibit, base, "base"))
    return out


def _ambiguous(key: AgreementKey, pool: list[_Identity]) -> bool:
    """Could ``key`` mean two agreements on this page? Every identity CONFUSABLE with it is
    counted, located or in a located filing beside one (F1), as distinct agreements: an amendment
    and what it amends, or two amendments of one agreement, are one (the same base name); each
    exhibit that IS an agreement is its own, unless some amendment names it as its base. Two or
    more: ambiguous, so it decides nothing, and the exhibits are read."""
    bases = {k.name for _ex, k, role in pool if role == "base" and _confusable(key, k)}
    owns = {(ex, k.name) for ex, k, role in pool if role == "own" and _confusable(key, k)}
    return len(bases) + sum(1 for _ex, name in owns if name not in bases) > 1


#: The ``source_ref`` of the per-exhibit outcome list: the loop itself, since each outcome names
#: its own exhibit (accession and filename).
OUTCOMES_SOURCE_REF = "E5 extraction loop — one outcome per located agreement exhibit"


def extract_covenant_terms(
    cs: CapitalStructure, *, llm: LlmClient, http: CachedHttp, cik: str, ticker: str, name: str
) -> tuple[Sourced[list[CovenantTerm]] | None, Sourced[str], list[str], str,
           Sourced[list[CovenantExhibitOutcome]] | None]:
    """Fenced Tier-2 covenant-term extraction over the mechanically-located exhibits.

    Returns ``(term_rows, terms_summary, flags, log, outcomes)``:
    - ``term_rows``: ``Sourced[list[CovenantTerm]]`` (PRESENT with the exhibit ref) or ``None`` when
      there is nothing to extract from (no located exhibit) — the caller leaves the field unset.
    - ``terms_summary``: the one-line ``covenant_terms`` string (present count, or UNKNOWN cause).
    - ``flags``: fail-loud markers (fetch fail, over-large exhibit, LLM error, not-extracted tail).
    - ``log``: the raw model output(s), appended to the dossier's ``llm_call.log``.
    - ``outcomes``: what each located exhibit's branch of the loop did with it — one
      :class:`CovenantExhibitOutcome` per target, in the located order (`_located_exhibits`; STATE
      row 63), or ``None`` when no exhibit is located. A target is each pointer's primary exhibit
      (`_core_agreement_exhibits`) and every other exhibit of its filing that governs debt
      (`_governs`) or could not be read. Written beside each branch's flag, so a page states the
      cause from a structured field and never parses the flag.

    WHICH EXHIBITS ARE SENT is the coverage rule's (2026-11-16): every located exhibit is read
    first; every debt contract it does not find superseded or terminated (`_coverage`) is sent,
    purchase contracts last; and `_MAX_EXHIBITS` stops only a runaway, loudly.

    Fail-loud throughout: a fetch/LLM failure degrades a row set to UNKNOWN + a flag, never a blank
    or a fabricated value."""
    pointers = cs.covenant_pointer_rows
    if pointers is None or pointers.status is not SourceStatus.PRESENT or not pointers.value:
        return None, cs.covenant_terms, [], "", None
    targets = _core_agreement_exhibits(list(pointers.value))
    if not targets:
        note = "(E5) located pointers carry no core agreement exhibit to extract terms from"
        return None, Sourced.unknown(note=note), [], "", None

    rows: list[CovenantTerm] = []
    flags: list[str] = []
    logs: list[str] = []
    # one slot per target, in the located order: every branch below writes its target's slot, so
    # the outcomes list follows the targets whatever order the exhibits are sent in (STATE row 63).
    # A target is a pointer's primary exhibit, or another exhibit of its filing that governs debt
    # or could not be read; each gets its slot when step 1 reaches it.
    slots: list[CovenantExhibitOutcome | None] = []
    extracted = 0

    def send(i: int, row: CovenantPointer, filename: str, src: str, text: str,
             title: str) -> int:
        """One model call on an identified debt contract, or its refusal for size or an LLM error.
        Returns the calls it spent against the guard."""
        if len(text) > _MAX_EXHIBIT_CHARS:
            flags.append(
                f"(E5) covenant exhibit too large for single-pass extraction ({len(text)} chars) — "
                f"extract by hand: {src}"
            )
            slots[i] = _outcome(row, filename, "too_large", title)
            return 0
        try:
            got, refused, log = _extract_from_exhibit(
                llm, text, name=name, ticker=ticker, source_ref=src, title=title,
                amendment=is_amendment(text))
        except LlmError as exc:
            flags.append(f"(E5) covenant extraction LLM error — UNKNOWN: {src}: {exc}")
            slots[i] = _outcome(row, filename, "llm_error", title)
            return 0
        logs.append(f"=== COVENANT EXTRACT: {src} ===\n{log}")
        rows.extend(got)
        flags.extend(refused)
        # a call that returned no term rows still spent one of the guard's calls, as before; it is
        # not an extraction, and no flag has ever said so
        slots[i] = _outcome(row, filename, "extracted" if got else "no_terms_returned", title)
        return 1

    # 1. READ EVERY LOCATED EXHIBIT FIRST. Which documents govern is decided across all of them (a
    # later exhibit's own words say what it displaced), so each is fetched and identified before
    # any is sent. Fetching is not the cost the guard bounds: the model call is.
    # EVERY EXHIBIT OF A LOCATED FILING THAT GOVERNS DEBT IS A TARGET (STATE row 63, the selector,
    # 2026-11-16). Until then each pointer targeted ONE exhibit, chosen by its file name
    # (`_core_agreement_exhibits`), and the rest of its filing was never sent, so live governing
    # documents were dropped: VRRM's 2025 term-loan restatement (`vrrm-ex10_2.htm`) beside its A&R
    # revolver, NKE's five-year agreement beside a 364-day one, NFLX's delayed-draw term loan
    # agreement beside its revolver, TJX's 2030 revolving credit agreement. The primary is still
    # targeted as before, and refused as before. Each OTHER exhibit of its filing
    # (`_located_exhibits`) is a target when its own title names a contract that governs debt
    # (`_governs`), and is then read by the coverage rule like any target: a 2025 restatement
    # supersedes the 2021 one it restates. One that cannot be read is a target too: it may be such a
    # contract, so it is flagged and its outcome says so. The rest are read for who they are (below)
    # and never sent, and no outcome is written for them: an offer letter, a press release, a stock
    # plan, and a guaranty, pledge or security agreement, which secures what its credit agreement
    # defines.
    candidates: list[_Candidate] = []
    unnamed: set[date] = set()
    siblings: list[_Identity] = []
    for row, filename, primary in _located_exhibits(list(pointers.value)):
        src = _source_ref(row, filename)
        text = _fetch_exhibit(http, cik, row.accession, filename)
        if text is None:
            flags.append(f"(E5) covenant exhibit fetch failed — UNKNOWN: {src}")
            slots.append(_outcome(row, filename, "fetch_failed"))
            continue
        title = agreement_title(text)
        if not primary and not _governs(title):
            # THE FILING'S OTHER EXHIBITS THAT GOVERN NOTHING: never sent, but each is read for WHO
            # it is, so an agreement dated as a target cannot make a displaced name look
            # unambiguous by being unseen (#1090 review, F1)
            if not title:
                unnamed.update(_head_dates(text))
            elif is_debt_agreement(title):
                own, base = exhibit_identity(text, title, is_amendment(text))
                siblings += _identities((row.accession, filename), own, base)
            continue
        i = len(slots)
        slots.append(None)
        if not title or not is_debt_agreement(title):
            # IDENTIFY OR REFUSE. The pointer's family is a guess; the document's own heading is
            # evidence. Without this, an executive offer letter (NKE, TGT), a stock purchase
            # agreement (WERN) and a capped-call confirmation (UBER) were each handed to a covenant
            # extractor and whatever it returned was labelled as that instrument's terms.
            # WHAT THE READER DID, NOT WHAT THE DOCUMENT IS. A title read is the document's own
            # word, and the gate judged it. With none read, the reader knows only that: until
            # 2026-11-16 this flag said the exhibit "declares itself no agreement at all", which
            # VRRM's revolver amendment, a debt contract with a title-cased heading, did not
            # (STATE row 63). The wording is the renderer's (`render._NO_TITLE_READ`).
            flags.append(
                f"(E5) not a debt agreement — refused rather than extracted under the pointer's "
                f"guess ({row.family}): {src} declares itself “{title}”"
                if title else
                f"(E5) refused rather than extracted under the pointer's guess ({row.family}): "
                f"no agreement title was read from the head of {src}"
            )
            slots[i] = _outcome(row, filename, "not_debt_agreement", title)
            if not title:
                # NO NAME WAS READ, so this exhibit may be the agreement a later exhibit displaces.
                # Every date its head states is kept, and a displaced agreement of one of those
                # dates decides nothing (Codex, PR #1090 round 1). A refusal whose title WAS read
                # (an office lease, a stock purchase agreement) is known not to be one.
                unnamed.update(_head_dates(text))
            continue
        own, base = exhibit_identity(text, title, is_amendment(text))
        candidates.append(_Candidate(i, row, filename, src, text, title, own, base))

    # 2. THE COVERAGE RULE: skip what a later located exhibit displaced, and notes that matured.
    reference = _reference_date(cs)
    instruments = (list(cs.instruments.value or [])
                   if cs.instruments.status is SourceStatus.PRESENT else None)
    live: list[_Candidate] = []
    unread = sum(1 for o in slots if o is not None and o.outcome == "fetch_failed")
    if unread and len(candidates) > 1:
        flags.append(f"(E5) coverage: {unread} located exhibit(s) could not be read, so no exhibit "
                     f"on this page is found superseded; every debt contract read is sent")
    verdicts = _coverage(candidates, reference, instruments, all_read=not unread,
                         unnamed_dates=frozenset(unnamed), siblings=tuple(siblings))
    for c, (kind, by, evidence) in zip(candidates, verdicts, strict=True):
        if kind == "live":
            live.append(c)
            continue
        flags.append(f"(E5) exhibit not sent — {kind}: {c.src}"
                     + (f"; superseded by {by[0]} · {by[1]}" if by else "") + f" — {evidence}")
        slots[c.i] = _outcome(c.row, c.filename, kind, c.title, superseded_by=by,
                              evidence=evidence)

    # 3. SEND EVERY LIVE DEBT CONTRACT, in the targets' order, PURCHASE CONTRACTS LAST (operator,
    # 2026-11-16: "Order now, coverage next (Recommended)"). A notes purchase agreement is a debt
    # contract, and the gate passes it, but it is the sale of notes, not the contract that governs
    # them. NFLX's pointer files its 2018 and 2014 notes purchase agreements under a bridge-loan
    # family, so in the round-robin they came first (#1088). The guard stops only a runaway.
    ordered = ([c for c in live if not _PURCHASE_CONTRACT.search(c.title)]
               + [c for c in live if _PURCHASE_CONTRACT.search(c.title)])
    for c in ordered:
        if extracted >= _MAX_EXHIBITS:
            # LOUD, never quiet: the guard is not how exhibits are chosen, so hitting it means a
            # page located more live debt contracts than any committed page has
            flags.append(f"(E5) RUNAWAY GUARD: this page has {len(ordered)} live debt contracts "
                         f"and the guard is {_MAX_EXHIBITS} calls, so this one is not sent (cost "
                         f"bound): {c.row.family}·{c.filename}"
                         + (f" — a purchase agreement (“{c.title}”), ranked after every other "
                            f"debt contract" if _PURCHASE_CONTRACT.search(c.title) else ""))
            slots[c.i] = _outcome(c.row, c.filename, "cost_bound", c.title)
            continue
        extracted += send(c.i, c.row, c.filename, c.src, c.text, c.title)
    outcomes = [o for o in slots if o is not None]
    if len(outcomes) != len(slots):  # every branch above fills its slot; fail loud if not
        raise RuntimeError(f"E5 wrote {len(outcomes)} outcomes for {len(slots)} targets")

    found = Sourced.present(outcomes, source_ref=OUTCOMES_SOURCE_REF)
    if not rows:
        note = "(E5) covenant exhibits located but no terms extracted (see flags)"
        return None, Sourced.unknown(note=note), flags, "\n\n".join(logs), found
    present = sum(1 for r in rows if r.value.status is SourceStatus.PRESENT)
    term_rows = Sourced.present(
        rows, source_ref="fenced Tier-2 extraction (verbatim, source-bound)")
    summary = Sourced.present(
        f"{present} of {len(rows)} named terms extracted verbatim from {extracted} located "
        f"exhibit(s); see the covenant-terms table for each {{value, source_ref}}.",
        source_ref="fenced Tier-2 extraction",
    )
    return term_rows, summary, flags, "\n\n".join(logs), found


# --- (P5 core, shared by the P1 synthesis digest + the P5 render) term-governed collapse ----------

_ACC_RE = re.compile(r"\b(\d{10}-\d{2}-\d{6})\b")


def _acc_of(text: str | None) -> str:
    m = _ACC_RE.search(text or "")
    return m.group(1) if m else ""


#: The exhibit a term row cites: "<accession> · <file>", as `_source_ref` writes it into the row's
#: ``source_ref`` and every note that names the exhibit. This code sets that string, never a model.
_EXHIBIT_RE = re.compile(r"\b(\d{10}-\d{2}-\d{6}) · (\S+)")


def _exhibit_of(row: CovenantTerm) -> tuple[str, str]:
    """(accession, file) of the exhibit a term row was extracted from; ("", "") when neither its
    ``source_ref`` nor its note names one (a row written before the file was cited)."""
    for text in (row.value.source_ref, row.value.note):
        m = _EXHIBIT_RE.search(text or "")
        if m:
            return m.group(1), m.group(2)
    return "", ""


class GoverningTerm(NamedTuple):
    """One (family, term) collapsed to its GOVERNING value — the latest exhibit's PRESENT value
    (an amendment overrides the base). ``base_ref`` is the base exhibit; ``amended_by`` chains the
    later accessions that changed it. ``value`` is UNKNOWN when NO exhibit stated the term, or when
    a LATER exhibit stated it and its quote was refused (``refused_newer``, oldest→newest): the
    value in force is then not verified, and the latest PRESENT value moves to ``last_verified``.
    The optional interest-rate components (RC-1.5d) ride along from the WINNING exhibit's row so the
    render composes the value-lead from structure — they carry the same citation as ``value``, or as
    ``last_verified`` when a later refusal withholds the value."""

    family: str
    term: str
    value: Sourced[str]
    base_ref: str | None
    amended_by: tuple[str, ...]
    base_rate_label: str | None = None
    margin_pct: float | None = None
    margin_bps: float | None = None
    floor_pct: float | None = None
    pik_pct: float | None = None
    refused_newer: tuple[Sourced[str], ...] = ()
    last_verified: Sourced[str] | None = None
    #: the winning row's components kept by a clause of their own (`rate_components` checked each
    #: is a span of the exhibit stating the figure), so the lead's guard accepts them on it
    component_quotes: tuple[tuple[str, str], ...] = ()


def _ambiguous_titles(
    term_rows: list[CovenantTerm], meta: dict[str, tuple[str, str]]
) -> set[str]:
    """Titles that CANNOT identify one contract, so the collapse must not group by them.

    A title merges rows across pointer families — that is the point: BURL's four amendments to one
    credit agreement arrive under four different guessed instruments and must end up in ONE group.
    But two BASE contracts can share a name without being the same contract, and then the same
    merge DELETES one of them: two convertible series whose indentures are both titled "INDENTURE"
    collapse to one group, the earlier series' conversion price disappears, and the later indenture
    is published as an ``amended_by`` of it — a supersession that never happened, which is exactly
    what (X-4) below refuses to fabricate from dates.

    So a title is ambiguous when it covers MORE THAN ONE BASE DOCUMENT from DIFFERENT pointer
    families. Both halves matter. Amendments are excluded because an amendment shares its base's
    identity. Same-family bases are excluded because they were already one group before the title
    existed — Nike's two successive 364-day agreements share a pointer family, and collapsing a
    renewal onto its predecessor is the pre-existing behaviour here, not something this introduces.

    Measured 2026-09-28 over the 144-head corpus: 11 titles span >1 accession; 5 carry >=2 base
    documents. Withholding those 5 restores the pointer grouping exactly where the document cannot
    identify itself, and leaves all 6 genuine chains (BURL 5 accessions / 0 base, NFLX, UBER, MVST,
    PARR, WLK) merging as they should."""
    bases: dict[str, set[str]] = {}
    for row in term_rows:
        title = row.agreement_title
        if not title or row.agreement_is_amendment:
            continue
        acc = _acc_of(row.value.source_ref) or _acc_of(row.value.note) or ""
        fam = meta.get(acc, ("", ""))[0]
        bases.setdefault(title, set()).add(f"{fam}\x00{acc}")
    out: set[str] = set()
    for title, keys in bases.items():
        if len({k.split("\x00")[0] for k in keys}) > 1:
            out.add(title)
    return out


def governing_terms(
    term_rows: list[CovenantTerm], pointers: list[CovenantPointer]
) -> list[GoverningTerm]:
    """Collapse per-exhibit ``CovenantTerm`` rows into one GOVERNING value per (family, term): the
    latest-dated exhibit's PRESENT value wins (amendment over base), with the base ref + an
    ``amended by`` chain. Grouped by instrument family via the pointers' accession→(family, date)
    map, so a facility's terms never merge with another's. A term no exhibit stated stays
    UNKNOWN — but the collapse guarantees a PRESENT answer is never ordered below an UNKNOWN,
    except where a later exhibit stated the term and its quote was refused (see below).
    The winning row's interest components ride along so the render composes from structure."""
    meta = {p.accession: (p.family, p.filing_date) for p in pointers if p.accession}
    ambiguous = _ambiguous_titles(term_rows, meta)
    grouped: dict[tuple[str, str], list[tuple[str, CovenantTerm]]] = {}
    order: list[tuple[str, str]] = []
    labelled: list[tuple[str, str, str, CovenantTerm]] = []  # (label, accession, file, row)
    for row in term_rows:
        acc = _acc_of(row.value.source_ref) or _acc_of(row.value.note)
        fam, dt = meta.get(acc, ("(unmapped)", ""))
        # THE DOCUMENT OUTRANKS THE POINTER, BUT A TITLE MAY RELABEL A GROUP — NEVER MERGE TWO.
        # ``agreement_title`` is what the exhibit calls itself, normalised to the base contract so
        # an amendment groups with what it amends; ``family`` is the instrument the class-generic
        # efts phrase guessed, and on 11 of 26 committed names that guess is decided by which
        # family reached the shared hit list first. ``_ambiguous`` below withholds the title
        # wherever it cannot tell two contracts apart. Fall back for a row assembled before the
        # title was read.
        fam = (row.agreement_title
               if row.agreement_title and row.agreement_title not in ambiguous else fam)
        ex_acc, doc = _exhibit_of(row)
        labelled.append((fam, acc, doc if ex_acc == acc else "", row))
    # TWO EXHIBITS OF ONE FILING NEVER SHARE A GROUP (STATE row 63, the selector, 2026-11-16;
    # coordinator's ruling). A filing's exhibits share its filing date, so in one group the
    # collapse could not order them: the later in the list would govern every term and the earlier
    # one's base would be cited for it. Since the selector sends every exhibit of a filing that
    # governs debt, WLK's `0001193125-10-276447` sends its GO Zone (`dex101.htm`) and IKE Zone
    # (`dex102.htm`) bond loan agreements, both "LOAN AGREEMENT" of November 1, 2010, two
    # different contracts. So where two files of one accession share a label, each file's rows
    # form their own group, labelled with the file. A label one file per filing reaches is
    # unchanged, so a page with no such pair collapses exactly as before.
    files: dict[tuple[str, str], set[str]] = {}
    for fam, acc, doc, _row in labelled:
        if acc and doc:
            files.setdefault((fam, acc), set()).add(doc)
    for fam, acc, doc, row in labelled:
        dt = meta.get(acc, ("", ""))[1]
        if acc and doc and len(files[(fam, acc)]) > 1:
            fam = f"{fam} · {doc}"
        key = (fam, row.name)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append((dt, row))
    out: list[GoverningTerm] = []
    for fam, term in order:
        dated = sorted(grouped[(fam, term)], key=lambda dr: dr[0])  # oldest→newest (stable on ties)
        present = [(dt, r) for dt, r in dated if r.value.status is SourceStatus.PRESENT]
        value: Sourced[str]
        refused: tuple[Sourced[str], ...] = ()
        last_verified: Sourced[str] | None = None
        if present:
            gov_dt, gov_row = present[-1]  # latest PRESENT governs — its components ride along
            value = gov_row.value
            # A LATER REFUSAL WITHHOLDS THE VALUE, IT DOES NOT HAND IT TO THE OLDER EXHIBIT (#804's
            # follow-up). An amendment that never mentions a term leaves it in force, so a later
            # "not stated" row changes nothing. A later REFUSED row is different: that exhibit
            # STATED the term, and the source check withheld what it said. Letting the older value
            # govern then assumes the amendment did not change it — on BURL that put a LIBOR grid
            # from 2021 on the page as the rate in force over a 2025 amendment. So the value in
            # force is UNKNOWN, and the older one is kept, labelled, as the last verified value.
            # Only a strictly later, dated refusal counts — the (X-4) rule below: tied or empty
            # dates cannot establish that one exhibit came after another. Measured at 18d19bfb over
            # the 22 committed pages with term rows: 39 refused rows; 3 later than their group's
            # latest PRESENT row (NKE, BURL, NFLX), 6 earlier, 30 in groups with no PRESENT row,
            # 0 tied or undated.
            refused = tuple(r.value for dt, r in dated
                            if gov_dt and dt > gov_dt
                            and r.value.status is not SourceStatus.PRESENT
                            and (r.value.note or "").startswith(REFUSED_NOTE_PREFIX))
            if refused:
                last_verified = gov_row.value
                value = Sourced.unknown(note=(
                    f"(E5) not verified since {gov_dt}: {len(refused)} later exhibit(s) stated "
                    f"this term and each was refused "
                    f"({'; '.join(_acc_of(r.note) for r in refused)}); last verified in "
                    f"{gov_row.value.source_ref}"))
            base_ref = present[0][1].value.source_ref
            # (X-4) an ``amended by`` chain is a REAL base→amendment relationship — assert it ONLY
            # on a true chronology (distinct, non-empty dates). Tied/empty dates (filing_date may be
            # '') can't establish supersession, so we do NOT fabricate the chain from the arbitrary
            # input order — source-binding must not claim an amendment the dates don't show.
            pdates = [dt for dt, _ in present]
            ordered = all(pdates) and len(set(pdates)) == len(pdates)
            amended = (tuple(_acc_of(r.value.source_ref) for _, r in present[1:]
                             if _acc_of(r.value.source_ref)) if ordered else ())
        else:
            gov_row = dated[-1][1]
            value = gov_row.value
            base_ref, amended = None, ()
        out.append(GoverningTerm(
            fam, term, value, base_ref, amended,
            base_rate_label=gov_row.base_rate_label, margin_pct=gov_row.margin_pct,
            margin_bps=gov_row.margin_bps, floor_pct=gov_row.floor_pct, pik_pct=gov_row.pik_pct,
            refused_newer=refused, last_verified=last_verified,
            component_quotes=tuple(sorted(gov_row.component_quotes.items()))))
    return out


_DIGEST_CAP = 1500  # (P1) hard char cap on the synthesis digest — quotes excluded, values truncated
_DIGEST_VAL = 85  # per-value truncation — tuned so TWO facilities' key terms both fit the cap
_MAT_DIGEST_VAL = 300  # (M-3) the maturity RESOLUTION is the single most decision-critical survival
# fact and there is only one — give it room so the operative clause is not clipped away.
# (P1) the survival-DECISION terms the synthesis reasons with — conversion (dilution), principal
# (size), interest (cost), maturity (wall), the maintenance covenant (trip risk). Budget math: at 2
# facilities × these 5 × ~115 chars + headers + maturity event ≈ 1.4k < the 1.5k cap. The verbose
# events-of-default / security / agent / lender detail stays in the render table (not the digest).
_DIGEST_TERMS = ("conversion", "principal", "interest", "coupon", "maturity", "covenant",
                 "liquidity")
# matches "N shares … per $D": N (optionally paren-wrapped; boundary-anchored so a comma-grouped
# share COUNT like "1,250,000" cannot be misread as a rate) and the principal denomination D, which
# is CAPTURED, not assumed $1.00 — a bond's "45.4545 shares per $1,000" is $22.00/sh, NOT $0.02. The
# "shares"→"per" gap is bounded and stops at a clause break (';') so it never bridges an unrelated
# clause (a decimal in a § number stays inside one clause, so '.' is NOT a stop). D is pinned by a
# no-more-digits lookahead so "$1" cannot match inside "$1,000". Else → '' (LLM reads verbatim).
_CONV_RATE_RE = re.compile(
    r"(?<![\d,.])\(?(\d{1,4}(?:\.\d+)?)\)?\s*shares?\b[^;]{0,80}?"
    r"per\s*\$?\s*(1\.00|1,000|1000|100|1)(?![\d.,])", re.IGNORECASE)


def _derive_conversion(value: str) -> str:
    """(P1) A best-effort $/share from a stated conversion rate 'N shares … per $D' → $D ÷ N, so the
    synthesis reasons with the ACTUAL price (D is the captured principal denomination — $1.00 or the
    $1,000 bond convention — never assumed). '' when the rate isn't cleanly stated (the LLM then
    works from the verbatim mechanics) — never a fabricated or mis-scaled number."""
    m = _CONV_RATE_RE.search(value)
    if not m:
        return ""
    try:
        rate = float(m.group(1))
        denom = float(m.group(2).replace(",", ""))
    except ValueError:
        return ""
    if rate <= 0 or denom <= 0:
        return ""
    return f" (⇒ ~${denom / rate:.2f}/sh at {m.group(1)} sh per ${m.group(2)})"


def _clip(text: str, n: int) -> str:
    """Truncate ``text`` to ≤``n`` chars WITHOUT splitting a token — back off to the last whitespace
    before the cut, so a dollar/share figure is never chopped mid-digit into a corrupted number
    ('$5,000,000' → '$5,00…'); append '…' to mark it. Whitespace (incl. newlines) is collapsed first
    so the digest and the markdown list item stay single-line."""
    s = " ".join(text.split())
    if len(s) <= n:
        return s
    head = s[:n].rsplit(" ", 1)[0].rstrip()
    return (head or s[:n].rstrip()) + "…"


def covenant_digest(
    governing: list[GoverningTerm], maturity_event: Sourced[str] | None, *, fail_reason: str | None
) -> str:
    """(P1/FIX-0) The TERM→VALUE→source_ref digest fed to SYNTHESIS — survival-DECISION governing
    values (quotes EXCLUDED, conversion price derived), grouped by family, ≤``_DIGEST_CAP`` chars.
    NEVER a pointer/count. On extraction failure it is the honest ``extraction failed: <reason>``
    line (condition 3) — never a 'see the table' pointer to data the LLM cannot see."""
    if fail_reason:
        return f"COVENANT DIGEST — extraction failed: {fail_reason} (terms UNKNOWN, not pending)."
    present = [g for g in governing if g.value.status is SourceStatus.PRESENT
               and any(k in g.term.lower() for k in _DIGEST_TERMS)]
    body: list[str] = []
    fams: list[str] = []
    for g in present:
        if g.family not in fams:
            fams.append(g.family)
    for fam in fams:
        gs = [g for g in present if g.family == fam]
        acc = _acc_of(gs[0].base_ref) if gs else ""
        amend = sorted({a for g in gs for a in g.amended_by})
        amend_s = f" · amended by {', '.join(amend)}" if amend else ""
        body.append(f"[{fam} · {acc}{amend_s}]")
        for g in gs:
            raw = str(g.value.value)
            # (P1) lead the conversion line with the DERIVED $/share so it survives truncation, and
            # synthesis reasons with the actual price (dilution) — the verbatim mechanics follow.
            derived = _derive_conversion(raw) if "conversion" in g.term.lower() else ""
            val = (derived.strip().lstrip("(").rstrip(")") + " · " + raw) if derived else raw
            body.append(f"  {g.term}: {_clip(val, _DIGEST_VAL)}")  # (M-2) boundary-safe truncation
    if maturity_event is not None and maturity_event.status is SourceStatus.PRESENT:
        body.append(f"Maturity event ({maturity_event.source_ref}): "  # (M-3) boundary-safe + room
                    f"{_clip(str(maturity_event.value), _MAT_DIGEST_VAL)}")
    if not body:
        # (CC-2) extraction ran but produced no survival-DECISION content — say so honestly; never a
        # bare header implying data the LLM cannot see exists (the FIX-0 failure mode). Any located
        # non-digest terms (security, events-of-default) remain in the covenant render table.
        return ("COVENANT DIGEST — no survival-critical covenant/conversion/maturity terms found "
                "(any located terms are in the covenant table; terms UNKNOWN/other, not pending).")
    lines = ["COVENANT & MATURITY DIGEST (governing terms; verbatim quotes omitted):"] + body
    digest = "\n".join(lines)
    if len(digest) > _DIGEST_CAP:  # hard cap — drop trailing lines, never silently truncate a value
        kept: list[str] = []
        total = 0
        for ln in lines:
            if total + len(ln) + 1 > _DIGEST_CAP - 60:  # reserve room for the marker
                kept.append(f"… (+{len(lines) - len(kept)} lower-priority terms in the table)")
                break
            kept.append(ln)
            total += len(ln) + 1
        digest = "\n".join(kept)
    return digest


# --- (P3/FIX-3) maturity-event fenced extraction — the verbatim RESOLUTION at a maturity 8-K ----

_MATURITY_SYSTEM = (
    "You extract the VERBATIM resolution event from an SEC 8-K filed at a debt maturity "
    "— the Item 8.01 (Other Events) / 1.01 (Material Agreement) / 3.02 (Unregistered Sales) "
    "stating what happened to the maturing principal (repaid, refinanced, converted to equity, "
    "extended, defaulted). ASSEMBLE AND CITE; NEVER conclude. Quote the operative sentence(s) "
    "VERBATIM (≤400 characters), no paraphrase; set present=false if the body states no such event."
)
_MATURITY_TOOL: dict[str, Any] = {
    "name": "maturity_event",
    "description": "The verbatim maturity-resolution paragraph from the 8-K body (≤400 chars).",
    "input_schema": {
        "type": "object",
        "properties": {
            "present": {"type": "boolean", "description": "true iff the body states a resolution"},
            "verbatim": {"type": "string", "description": "the operative sentence(s), ≤400 chars"},
        },
        "required": ["present"],
    },
}


def _primary_body(exhibits: list[str]) -> str | None:
    """The 8-K PRIMARY body doc (the resolution text lives here, not in an ex-99 or an EDGAR
    index/XBRL scaffold file) — a .htm that is not an ex-NN exhibit nor an index/header/metalinks/
    filing-summary/XBRL-report (Rn.htm) file. Prefer the '…_8k.htm'/'form8k' body; else the first
    real candidate. None when the index carries only exhibits/scaffolding."""
    noise = re.compile(
        r"ex-?\d|exhibit|index|header|filingsummary|metalinks|^r\d+\.htm", re.IGNORECASE)
    cands = [n for n in exhibits
             if n.lower().endswith((".htm", ".html")) and not noise.search(n.lower())]
    body = next((n for n in cands if re.search(r"8-?k|form8", n.lower())), None)
    return body or (cands[0] if cands else None)


def extract_maturity_event(
    cs: CapitalStructure, *, llm: LlmClient, http: CachedHttp, cik: str, ticker: str, name: str
) -> tuple[Sourced[str] | None, list[str], str]:
    """(P3/FIX-3) Fenced verbatim extraction of the resolution event at the maturity-anchored 8-K
    (E3's ``maturity_filings``). Returns ``(event|None, flags, log)`` — PRESENT with the verbatim +
    ``8-K <acc> (<date>)`` ref, UNKNOWN when the body states none, or None when there is no maturity
    8-K to read. Fail-loud: a fetch/LLM failure, or a verbatim that is not a span of the body
    (`vinci.verbatim`), → UNKNOWN + flag, never a fabricated resolution."""
    mf = cs.maturity_filings
    if mf.status is not SourceStatus.PRESENT or not mf.value:
        return None, [], ""
    acc = _acc_of(mf.value)
    if not acc:
        return None, [], ""
    date_m = re.search(r"filed\s+(\d{4}-\d{2}-\d{2})", mf.value)
    ev_date = date_m.group(1) if date_m else ""
    from vinci.dossier.mechanical import _exhibit_names  # local: avoid a mechanical import cycle
    body = _primary_body(_exhibit_names(http, cik, acc))
    src = f"8-K {acc}" + (f" ({ev_date})" if ev_date else "")
    if body is None:
        return Sourced.unknown(note=f"(P3) no primary 8-K body located at {src}"), [], ""
    text = _fetch_exhibit(http, cik, acc, body)
    if text is None:
        return Sourced.unknown(note=f"(P3) maturity 8-K body fetch failed: {src}"), \
            [f"(P3) maturity 8-K fetch failed — UNKNOWN: {src}"], ""
    sent = text[:_MAX_EXHIBIT_CHARS]
    user = (f"Company: {name} ({ticker}). 8-K: {src}. Extract the maturity-resolution event.\n\n"
            f"=== 8-K BODY (verbatim) ===\n{sent}")
    try:
        raw = llm.extract(system=_MATURITY_SYSTEM, user=user, tool=_MATURITY_TOOL)
    except LlmError as exc:
        return Sourced.unknown(note=f"(P3) maturity-event LLM error: {src}"), \
            [f"(P3) maturity-event LLM error — UNKNOWN: {src}: {exc}"], ""
    log = f"=== MATURITY EVENT: {src} ===\n{raw}"
    if raw.get("present") and str(raw.get("verbatim", "")).strip():
        # The model's FULL verbatim is checked against the body it was sent — before the 400-char
        # cut below, which only shortens a span that has already been found.
        if not SourceText(sent).match(str(raw["verbatim"])).found:
            return (Sourced.unknown(note=f"(P3) refused: the model's verbatim is not in {src}"),
                    [f"(P3) maturity event refused — the model's verbatim is not in the 8-K body, "
                     f"so it is UNKNOWN: {src}"], log)
        # (D-2) collapse whitespace so the verbatim is ONE clean line in both the markdown list item
        # and the digest — an embedded newline otherwise breaks the .md item (the web HTML collapses
        # it), a py↔js render divergence.
        verbatim = " ".join(str(raw["verbatim"]).split())[:400]
        return Sourced.present(verbatim, source_ref=src), [], log
    return (Sourced.unknown(note=f"(P3) 8-K body at {src} states no maturity-resolution event"),
            [], log)
