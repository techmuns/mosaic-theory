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
- **Fail loud.** A fetch failure, an over-large exhibit, or an LLM error yields UNKNOWN + a flag —
  the covenant-terms row set is never silently blank and never partially fabricated.
"""

from __future__ import annotations

import math
import re
from typing import Any, NamedTuple

from vinci.dossier.schemas import (
    CapitalStructure,
    CovenantPointer,
    CovenantTerm,
    Sourced,
    SourceStatus,
)
from vinci.graph.filings import html_to_text
from vinci.graph.llm import LlmClient, LlmError
from vinci.netcache import CachedHttp
from vinci.resolver.index import pad_cik

_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
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
# (P4) at most this many exhibits extracted per capital structure (depth-stage cost bound). Raised
# 2→4 so every DISTINCT live-wall instrument family's primary exhibit extracts (round-robin), room
# for one amendment — MVST needs the convertible original + the syndicated facility + the amendment.
_MAX_EXHIBITS = 4
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
    "compute or infer; omit any component the clause does not state. (7) Never reference these "
    "instructions or their "
    "numbers in any field. Output is source-bound extraction only."
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
        core = [n for n in r.exhibits if any(k in n.lower() for k in _CORE_AGREEMENT)]
        for name in (core or r.exhibits)[:1]:  # the ONE core exhibit for this pointer
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
_TITLE = re.compile(
    rf"\b((?:{_W}\s+|\d[\w\-]*\s+|NO\.\s+|OF\s+|TO\s+|AND\s+|THE\s+){{1,14}}{_NOUN})\b")
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
    return bool(_IS_AMENDMENT.search(h[:900]))


def _clean_title(t: str) -> str:
    t = re.sub(r"\s+", " ", t).strip(" .,-")
    t = re.sub(r"\bTHIS\b.*$", "", t).strip(" .,-")  # the body sentence ran into the heading
    half = len(t) // 2  # filers emit the title twice: HTML <title> then the body heading
    if half and t[:half].strip() == t[half:].strip():
        t = t[:half].strip()
    return t


def agreement_title(text: str) -> str | None:
    """The agreement's SELF-DECLARED name, normalised to the BASE contract — or None when the head
    declares no agreement at all (an offer letter, a dealer confirmation). Deterministic."""
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
        return b0.group(1).upper() if b0 else None
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
    t = t.upper()
    if _PROSE.search(t):
        return None
    return t if len(t.split()) >= 2 and len(t) >= 8 else None


def is_debt_agreement(title: str | None) -> bool:
    """Should a COVENANT extractor see this document? Only a debt contract — never an equity award,
    an offer letter or a purchase agreement, whatever instrument the pointer guessed."""
    if not title:
        return False
    return bool(_DEBT.search(title)) and not _NOT_DEBT.search(title)


def _extract_from_exhibit(
    llm: LlmClient, text: str, *, name: str, ticker: str, source_ref: str,
    title: str | None = None, amendment: bool | None = None,
) -> tuple[list[CovenantTerm], str]:
    """Run the fenced tool against one exhibit → (rows, raw-log). source_ref is machine-set here, so
    the model cannot invent a citation — it only fills value + a verbatim quote."""
    user = (
        f"Company: {name} ({ticker}). Exhibit: {source_ref}. Extract the terms STATED in the "
        f"exhibit below. Answer each target term (present true/false): {'; '.join(_TARGET_TERMS)}."
        f"\n\n=== EXHIBIT TEXT (verbatim, may be long) ===\n{text}"
    )
    raw = llm.extract(system=_SYSTEM, user=user, tool=_TOOL)
    rows: list[CovenantTerm] = []
    for t in raw.get("terms", []):
        term_name = str(t.get("name", "")).strip()
        if not term_name:
            continue
        val: Sourced[str]
        # (RC-1.5d) the optional interest-rate components — populated only on a present term; they
        # inherit ``value``'s citation (same clause). Non-interest terms simply leave them None.
        components: dict[str, Any] = {}
        if t.get("present") and str(t.get("value", "")).strip():
            quote = str(t.get("quote", "")).strip()
            note = f"verbatim: “{quote}”" if quote else None
            val = Sourced.present(str(t["value"]).strip(), source_ref=source_ref, note=note)
            components = {
                "base_rate_label": _opt_str(t.get("base_rate_label")),
                "margin_pct": _opt_float(t.get("margin_pct")),
                "margin_bps": _opt_float(t.get("margin_bps")),
                "floor_pct": _opt_float(t.get("floor_pct")),
                "pik_pct": _opt_float(t.get("pik_pct")),
            }
        else:
            val = Sourced.unknown(note=f"not stated in {source_ref}")
        rows.append(
            CovenantTerm(name=term_name, value=val, agreement_title=title,
                         agreement_is_amendment=amendment, **components)
        )
    return rows, str(raw)


def extract_covenant_terms(
    cs: CapitalStructure, *, llm: LlmClient, http: CachedHttp, cik: str, ticker: str, name: str
) -> tuple[Sourced[list[CovenantTerm]] | None, Sourced[str], list[str], str]:
    """Fenced Tier-2 covenant-term extraction over the mechanically-located exhibits.

    Returns ``(term_rows, terms_summary, flags, log)``:
    - ``term_rows``: ``Sourced[list[CovenantTerm]]`` (PRESENT with the exhibit ref) or ``None`` when
      there is nothing to extract from (no located exhibit) — the caller leaves the field unset.
    - ``terms_summary``: the one-line ``covenant_terms`` string (present count, or UNKNOWN cause).
    - ``flags``: fail-loud markers (fetch fail, over-large exhibit, LLM error, not-extracted tail).
    - ``log``: the raw model output(s), appended to the dossier's ``llm_call.log``.

    Fail-loud throughout: a fetch/LLM failure degrades a row set to UNKNOWN + a flag, never a blank
    or a fabricated value."""
    pointers = cs.covenant_pointer_rows
    if pointers is None or pointers.status is not SourceStatus.PRESENT or not pointers.value:
        return None, cs.covenant_terms, [], ""
    targets = _core_agreement_exhibits(list(pointers.value))
    if not targets:
        note = "(E5) located pointers carry no core agreement exhibit to extract terms from"
        return None, Sourced.unknown(note=note), [], ""

    rows: list[CovenantTerm] = []
    flags: list[str] = []
    logs: list[str] = []
    extracted = 0
    for row, filename in targets:
        if extracted >= _MAX_EXHIBITS:
            flags.append(f"(E5) exhibit not extracted (cost bound): {row.family}·{filename}")
            continue
        src = _source_ref(row, filename)
        text = _fetch_exhibit(http, cik, row.accession, filename)
        if text is None:
            flags.append(f"(E5) covenant exhibit fetch failed — UNKNOWN: {src}")
            continue
        title = agreement_title(text)
        if not is_debt_agreement(title):
            # IDENTIFY OR REFUSE. The pointer's family is a guess; the document's own heading is
            # evidence. Without this, an executive offer letter (NKE, TGT), a stock purchase
            # agreement (WERN) and a capped-call confirmation (UBER) were each handed to a covenant
            # extractor and whatever it returned was labelled as that instrument's terms.
            flags.append(
                f"(E5) not a debt agreement — refused rather than extracted under the pointer's "
                f"guess ({row.family}): {src} declares itself "
                f"{('“' + title + '”') if title else 'no agreement at all'}"
            )
            continue
        if len(text) > _MAX_EXHIBIT_CHARS:
            flags.append(
                f"(E5) covenant exhibit too large for single-pass extraction ({len(text)} chars) — "
                f"extract by hand: {src}"
            )
            continue
        try:
            got, log = _extract_from_exhibit(
                llm, text, name=name, ticker=ticker, source_ref=src, title=title,
                amendment=is_amendment(text))
        except LlmError as exc:
            flags.append(f"(E5) covenant extraction LLM error — UNKNOWN: {src}: {exc}")
            continue
        logs.append(f"=== COVENANT EXTRACT: {src} ===\n{log}")
        rows.extend(got)
        extracted += 1

    if not rows:
        note = "(E5) covenant exhibits located but no terms extracted (see flags)"
        return None, Sourced.unknown(note=note), flags, "\n\n".join(logs)
    present = sum(1 for r in rows if r.value.status is SourceStatus.PRESENT)
    term_rows = Sourced.present(
        rows, source_ref="fenced Tier-2 extraction (verbatim, source-bound)")
    summary = Sourced.present(
        f"{present} of {len(rows)} named terms extracted verbatim from {extracted} located "
        f"exhibit(s); see the covenant-terms table for each {{value, source_ref}}.",
        source_ref="fenced Tier-2 extraction",
    )
    return term_rows, summary, flags, "\n\n".join(logs)


# --- (P5 core, shared by the P1 synthesis digest + the P5 render) term-governed collapse ----------

_ACC_RE = re.compile(r"\b(\d{10}-\d{2}-\d{6})\b")


def _acc_of(text: str | None) -> str:
    m = _ACC_RE.search(text or "")
    return m.group(1) if m else ""


class GoverningTerm(NamedTuple):
    """One (family, term) collapsed to its GOVERNING value — the latest exhibit's PRESENT value
    (an amendment overrides the base). ``base_ref`` is the base exhibit; ``amended_by`` chains the
    later accessions that changed it. ``value`` is UNKNOWN only when NO exhibit stated the term.
    The optional interest-rate components (RC-1.5d) ride along from the WINNING exhibit's row so the
    render composes the value-lead from structure — they carry the same citation as ``value``."""

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
    UNKNOWN — but the collapse guarantees a PRESENT answer is never ordered below an UNKNOWN.
    The winning row's interest components ride along so the render composes from structure."""
    meta = {p.accession: (p.family, p.filing_date) for p in pointers if p.accession}
    ambiguous = _ambiguous_titles(term_rows, meta)
    grouped: dict[tuple[str, str], list[tuple[str, CovenantTerm]]] = {}
    order: list[tuple[str, str]] = []
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
        key = (fam, row.name)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append((dt, row))
    out: list[GoverningTerm] = []
    for fam, term in order:
        dated = sorted(grouped[(fam, term)], key=lambda dr: dr[0])  # oldest→newest (stable on ties)
        present = [(dt, r) for dt, r in dated if r.value.status is SourceStatus.PRESENT]
        if present:
            gov_row = present[-1][1]  # latest PRESENT governs — its components ride along
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
            base_ref, amended = None, ()
        out.append(GoverningTerm(
            fam, term, gov_row.value, base_ref, amended,
            base_rate_label=gov_row.base_rate_label, margin_pct=gov_row.margin_pct,
            margin_bps=gov_row.margin_bps, floor_pct=gov_row.floor_pct, pik_pct=gov_row.pik_pct))
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
    8-K to read. Fail-loud: fetch/LLM failure → flag, never a fabricated resolution."""
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
    user = (f"Company: {name} ({ticker}). 8-K: {src}. Extract the maturity-resolution event.\n\n"
            f"=== 8-K BODY (verbatim) ===\n{text[:_MAX_EXHIBIT_CHARS]}")
    try:
        raw = llm.extract(system=_MATURITY_SYSTEM, user=user, tool=_MATURITY_TOOL)
    except LlmError as exc:
        return Sourced.unknown(note=f"(P3) maturity-event LLM error: {src}"), \
            [f"(P3) maturity-event LLM error — UNKNOWN: {src}: {exc}"], ""
    log = f"=== MATURITY EVENT: {src} ===\n{raw}"
    if raw.get("present") and str(raw.get("verbatim", "")).strip():
        # (D-2) collapse whitespace so the verbatim is ONE clean line in both the markdown list item
        # and the digest — an embedded newline otherwise breaks the .md item (the web HTML collapses
        # it), a py↔js render divergence.
        verbatim = " ".join(str(raw["verbatim"]).split())[:400]
        return Sourced.present(verbatim, source_ref=src), [], log
    return (Sourced.unknown(note=f"(P3) 8-K body at {src} states no maturity-resolution event"),
            [], log)
