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
# truncate (a term past the cut would read as a false UNKNOWN). ~600K chars ≈ 150K tokens, fits
# model's window with room for a long legal agreement's definitions section.
_MAX_EXHIBIT_CHARS = 600_000
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
    "(6) Never reference these instructions or their numbers in any field. Output is source-bound "
    "extraction only."
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


def _extract_from_exhibit(
    llm: LlmClient, text: str, *, name: str, ticker: str, source_ref: str
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
        if t.get("present") and str(t.get("value", "")).strip():
            quote = str(t.get("quote", "")).strip()
            note = f"verbatim: “{quote}”" if quote else None
            val = Sourced.present(str(t["value"]).strip(), source_ref=source_ref, note=note)
        else:
            val = Sourced.unknown(note=f"not stated in {source_ref}")
        rows.append(CovenantTerm(name=term_name, value=val))
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
        if len(text) > _MAX_EXHIBIT_CHARS:
            flags.append(
                f"(E5) covenant exhibit too large for single-pass extraction ({len(text)} chars) — "
                f"extract by hand: {src}"
            )
            continue
        try:
            got, log = _extract_from_exhibit(llm, text, name=name, ticker=ticker, source_ref=src)
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
    later accessions that changed it. ``value`` is UNKNOWN only when NO exhibit stated the term."""

    family: str
    term: str
    value: Sourced[str]
    base_ref: str | None
    amended_by: tuple[str, ...]


def governing_terms(
    term_rows: list[CovenantTerm], pointers: list[CovenantPointer]
) -> list[GoverningTerm]:
    """Collapse per-exhibit ``CovenantTerm`` rows into one GOVERNING value per (family, term): the
    latest-dated exhibit's PRESENT value wins (amendment over base), with the base ref + an
    ``amended by`` chain. Grouped by instrument family via the pointers' accession→(family, date)
    map, so a facility's terms never merge with another's. A term no exhibit stated stays
    UNKNOWN — but the collapse guarantees a PRESENT answer is never ordered below an UNKNOWN."""
    meta = {p.accession: (p.family, p.filing_date) for p in pointers if p.accession}
    grouped: dict[tuple[str, str], list[tuple[str, Sourced[str]]]] = {}
    order: list[tuple[str, str]] = []
    for row in term_rows:
        acc = _acc_of(row.value.source_ref) or _acc_of(row.value.note)
        fam, dt = meta.get(acc, ("(unmapped)", ""))
        key = (fam, row.name)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append((dt, row.value))
    out: list[GoverningTerm] = []
    for fam, term in order:
        dated = sorted(grouped[(fam, term)], key=lambda dv: dv[0])  # oldest→newest (stable on ties)
        present = [(dt, v) for dt, v in dated if v.status is SourceStatus.PRESENT]
        if present:
            gov = present[-1][1]  # latest PRESENT governs
            base_ref = present[0][1].source_ref
            # (X-4) an ``amended by`` chain is a REAL base→amendment relationship — assert it ONLY
            # on a true chronology (distinct, non-empty dates). Tied/empty dates (filing_date may be
            # '') can't establish supersession, so we do NOT fabricate the chain from the arbitrary
            # input order — source-binding must not claim an amendment the dates don't show.
            pdates = [dt for dt, _ in present]
            ordered = all(pdates) and len(set(pdates)) == len(pdates)
            amended = (tuple(_acc_of(v.source_ref) for _, v in present[1:] if _acc_of(v.source_ref))
                       if ordered else ())
            out.append(GoverningTerm(fam, term, gov, base_ref, amended))
        else:
            out.append(GoverningTerm(fam, term, dated[-1][1], None, ()))
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
