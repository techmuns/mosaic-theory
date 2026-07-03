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

from typing import Any

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
# at most this many exhibits are extracted per capital structure (depth-stage cost bound); the rest
# are logged as located-but-not-extracted. Convertible-family agreements are preferred (the
# conversion price is the priority deliverable).
_MAX_EXHIBITS = 2
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
    """(pointer, filename) pairs for the CORE agreement exhibit of each located pointer — the loan/
    credit/security/indenture/warrant document, NOT ancillary guaranty/pledge restatements. Loan/
    convertible families first (conversion price is the deliverable), then 10-K, then rest; cap."""
    picked: list[tuple[CovenantPointer, str]] = []
    def rank(r: CovenantPointer) -> int:
        fam = r.family.lower()
        conv_loan = "convert" in fam or "loan" in fam
        return 0 if conv_loan else (1 if "10-k" in r.filing.lower() else 2)
    for r in sorted((r for r in rows if r.accession), key=rank):
        core = [n for n in r.exhibits if any(k in n.lower() for k in _CORE_AGREEMENT)]
        # fall back to the first agreement-class exhibit if none matched the core-name list
        for name in (core or r.exhibits)[:1]:
            picked.append((r, name))
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
