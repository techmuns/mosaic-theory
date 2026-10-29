"""Stage 3, build 1 — the SEMANTIC-PRIMARY exposure detector, as a SCALE-DISCRIMINATION test.

A NEW early-detection path, PARALLEL to A's co-movement (it does not touch detection/B/C). The three
diagnostics converged: co-movement is structurally LATE (it fires only once names already co-move —
mid-run), semantic-from-disclosure DISCRIMINATES real driver-exposure from beta where co-movement
can't (the probe), and the real enablers are exposed-by-business but not-yet-co-moving (CAMT/AEHR,
invisible to correlation). So semantic exposure-detection is the early-detection basis.

Build 1 is NOT the multi-driver universe scan — it is the scale test on ONE ground-truth driver
(the AI-datacenter buildout): does the discrimination proven on 6 hand-checked names SURVIVE at
universe scale against the Part-6 flood of cheap "we do AI" disclosure?

THE DISCLOSURE-SOURCE LESSON (from the probe's IREN miss): annuals are too infrequent — confirming
events (hyperscaler contracts) arrive as 8-Ks / the latest 10-Q. So the detector reads the recent
MATERIAL-EVENT STREAM (8-K + latest 10-Q + latest annual), not just the annual.

It ASSEMBLES AND CITES; it does NOT conclude/rank/select — the human judges (the dead-signal line).
``exposure_basis`` is DERIVED from the source-bound, cite-checked facts (not trusted from the LLM):
no cited concrete fact → ``no-theme-exposure-disclosed`` (fail-loud; a mention is not exposure).
Reuses ``dossier/synthesis.py``'s ARCHITECTURE (fenced LLM, verdict-free tool, cite-check), not its
task. Keys from env via the committed clients; nothing logged to the ledger.
"""

from __future__ import annotations

import concurrent.futures as cf
import re
import urllib.parse
from collections.abc import Sequence
from datetime import date, timedelta
from typing import Any, cast

from vinci.edgar import EdgarClient
from vinci.graph.llm import LlmClient, LlmError
from vinci.netcache import CachedHttp, HttpError, SecRateLimitedError
from vinci.progress import ProgressFn, ProgressReporter
from vinci.themes.schemas import (
    DriverSpec,
    DriverTie,
    ExposureAssessment,
    ExposureBasis,
    ExposureConcreteness,
    ExposureFact,
)
from vinci.verbatim import comparison_key

_EFTS = "https://efts.sec.gov/LATEST/search-index"
_ONE_WEEK = 7 * 24 * 3600

# AI-datacenter's driver description + pre-filter vocabulary + layer tags moved to
# ``vinci.themes.drivers.AI_DATACENTER`` (a DriverSpec). This module is driver-AGNOSTIC — it takes a
# DriverSpec and contains NO theme-specific strings. (The build-1 "~50%" example was dropped there.)

_CONCRETE_RANK: dict[ExposureConcreteness, int] = {
    ExposureConcreteness.NONE: 0,
    ExposureConcreteness.STATED_INTENT: 1,
    ExposureConcreteness.COMMITTED_CAPACITY: 2,
    ExposureConcreteness.QUANTIFIED_REVENUE: 3,
    ExposureConcreteness.BINDING_CONTRACT: 4,
}
_BASIS_FOR: dict[int, ExposureBasis] = {
    0: ExposureBasis.NONE_DISCLOSED,
    1: ExposureBasis.ASPIRATIONAL,
    2: ExposureBasis.COMMITTED_CAPACITY,
    3: ExposureBasis.QUANTIFIED_REVENUE,
    4: ExposureBasis.BINDING_CONTRACTS,
}
# REAL (the false-positive bar) = a CONTRACTED or QUANTIFIED driver exposure. committed-capacity is
# the transitioning MIDDLE (capex/MW toward the driver, no paying customer yet) — not REAL.
_REAL = {ExposureBasis.BINDING_CONTRACTS, ExposureBasis.QUANTIFIED_REVENUE}

# recommendation / verdict language — the detector assembles, never concludes (synthesis.py's lint)
_DIRECTIONAL = re.compile(
    r"\b(buy|sell|overweight|underweight|recommend\w*|undervalued|overvalued|price target|"
    r"fair value|outperform|attractive|well-positioned to win|should (rise|outperform|win))\b",
    re.IGNORECASE,
)


def is_real_exposure(a: ExposureAssessment) -> bool:
    """REAL = a CONTRACTED (binding-contract) or QUANTIFIED (chain-attributable revenue) exposure
    — a factual bucket of disclosure concreteness for the false-positive count, not a verdict."""
    return a.exposure_basis in _REAL


def _effective_rank(conc: ExposureConcreteness, tie: DriverTie) -> int:
    """The fact's effective grade AFTER the DRIVER-TIE gate (audit error-mode #2, a SEPARATE gate):
    a terms-binding / quantified fact counts fully ONLY if it is DRIVER-SPECIFIC. An INDIRECT tie
    caps it at committed-capacity (borderline — real activity, only a generic/weak tie to the
    driver); a NOT-DRIVER tie (an adjacent-but-distinct market) caps it at stated-intent (a mention,
    not exposure to THIS driver). Driver-AGNOSTIC — what each tie MEANS is defined per-theme by the
    DriverSpec's tie_taxonomy; this gate only reads the tie the LLM returned."""
    r = _CONCRETE_RANK[conc]
    if tie is DriverTie.DRIVER_SPECIFIC:
        return r
    if tie is DriverTie.INDIRECT:
        return min(r, _CONCRETE_RANK[ExposureConcreteness.COMMITTED_CAPACITY])
    return min(r, _CONCRETE_RANK[ExposureConcreteness.STATED_INTENT])


def provenance_tag_of(text: str, tags: tuple[tuple[str, tuple[str, ...]], ...]) -> str:
    """A PROVENANCE tag (not a grade): which of the theme's sub-structure tags a disclosed fact
    names, by a keyword read of ``tags`` (the DriverSpec's ``provenance_tags``, ordered
    most-specific first — e.g. for AI-datacenter, the value-chain layers), for by-tag aggregation.
    Approximate (a fact spans tags; the human reads the verbatim fact). First match wins;
    'unspecified' if none match or the theme supplied no tags.

    SINGLE-TAG, DELIBERATELY KEPT — see :func:`provenance_tags_of` for the multi-tag form. A
    caller that aggregates BY NAME (one row per company) wants one tag; a caller reporting a
    name's full exposure wants all of them."""
    return provenance_tags_of(text, tags)[0]


def provenance_tags_of(text: str, tags: tuple[tuple[str, tuple[str, ...]], ...]) -> tuple[str, ...]:
    """EVERY sub-structure tag a disclosed fact names — not just the first.

    WHY BOTH FORMS EXIST (measured on `glp1-demand-shift`, 2026-08-19). A driver whose structure
    is DIRECTIONAL rather than sequential can have one company genuinely on two sides: SMPL is
    suppressed as snacking and helped as protein — that duality IS its thesis — and HLF's
    meal-replacement is a weight-loss METHOD competing with incretins AND nutrition support for
    incretin users. First-match returned ONE tag for both, so the two-sided design lived in the
    DriverSpec prose and never reached the output: zero of eleven names carried two tags.
    The spec licensed it and the resolver could not express it.

    ORDER IS PRESERVED from the spec's `provenance_tags`, so the most-specific tag still leads and
    `provenance_tag_of` keeps its exact previous behaviour by taking [0]. 'unspecified' when
    nothing matches, so the return is never empty and no caller needs a guard."""
    t = text.lower()
    hits = tuple(tag for tag, kws in tags if any(k in t for k in kws))
    return hits or ("unspecified",)


def grade_driving_fact(a: ExposureAssessment) -> ExposureFact | None:
    """The disclosed fact whose EFFECTIVE grade (after the driver-tie gate) set the exposure_basis —
    the human's first-read provenance. None when no fact credits any exposure (basis none)."""
    graded = [f for f in a.disclosed_facts if _effective_rank(f.concreteness, f.driver_tie) > 0]
    return max(graded, key=lambda f: _effective_rank(f.concreteness, f.driver_tie), default=None)


# --------------------------------------------------------------------------------------------------
# Pre-filter — which universe CIKs even MENTION the driver (the cheap keyword 'flood')
# --------------------------------------------------------------------------------------------------
def _efts_url(phrase: str, ciks: list[str], frm: int, forms: str, startdt: str, enddt: str) -> str:
    q = urllib.parse.quote(f'"{phrase}"')
    url = f"{_EFTS}?q={q}&forms={forms}&startdt={startdt}&enddt={enddt}&from={frm}"
    return url + "&ciks=" + ",".join(ciks) if ciks else url


def parse_efts_ciks(data: dict[str, Any]) -> tuple[list[str], int]:
    """The CIKs (zero-padded) on one efts page + the total hit count. Fail-loud on a throttle/error
    body (no ``hits`` key) — returning [] would make a failed search look like 'no mentions'."""
    hits = data.get("hits")
    if not isinstance(hits, dict) or "hits" not in hits:
        raise HttpError(f"efts returned no hits structure (throttled/error?): {data}")
    out = [str(c).zfill(10) for h in hits["hits"]
           if (c := (h.get("_source", {}).get("ciks") or [None])[0])]
    total = int(hits.get("total", {}).get("value", 0))
    return out, total


def mention_prefilter(
    efts: CachedHttp,
    ciks_padded: list[str],
    phrases: tuple[str, ...],
    *,
    startdt: str,
    enddt: str,
    forms: str = "8-K,10-Q,10-K,20-F,40-F,6-K",  # incl. foreign issuers (20-F/6-K) — CAMT etc.
    max_pages: int = 5,
    skip_errors: bool = False,
    skipped: list[str] | None = None,
    progress: ProgressFn | None = None,
) -> dict[str, set[str]]:
    """Batched-CIK efts: which universe CIKs mention each driver phrase recently. Returns
    ``{cik10: {phrases}}`` — the keyword 'flood' the semantic layer must then discriminate.

    Default is fail-loud (a bad efts body raises). ``skip_errors=True`` (for a long universe scan)
    skips a batch×phrase that errors after retries and keeps going — a conservative recall gap (a
    missed mention just means a name is not scanned), never a fabricated mention.

    PASS ``skipped`` TO LEARN HOW BIG THAT GAP WAS. Until 2026-09-02 the skip was silent and
    uncounted, which made every downstream denominator "N that SUCCEEDED" out of an unknown base —
    a scan reporting 745 graded names could have dropped any number and nothing said so. Each
    entry is one ``batch×phrase`` query that errored, and a batch holds up to 100 CIKs, so one
    entry can cost up to 100 names their match on that phrase. An empty list is the only thing
    that licenses reading the yield as complete."""
    matched: dict[str, set[str]] = {}
    batches = [ciks_padded[i:i + 100] for i in range(0, len(ciks_padded), 100)]
    rep = ProgressReporter("efts prefilter", len(batches) * len(phrases), emit=progress)
    done = 0
    for batch in batches:
        bset = set(batch)
        for phrase in phrases:
            frm = 0
            for _ in range(max_pages):
                try:
                    data = cast(dict[str, Any],
                                efts.get_json(_efts_url(phrase, batch, frm, forms, startdt, enddt),
                                              ttl_seconds=_ONE_WEEK))
                    page, total = parse_efts_ciks(data)
                except HttpError as exc:
                    if not skip_errors:
                        raise
                    if skipped is not None:  # COUNT the gap — a silent skip is an unknown base
                        skipped.append(f"{phrase!r} × batch of {len(batch)} CIKs "
                                       f"(from={frm}): {type(exc).__name__}: {exc}")
                    break  # transient efts error — skip this batch×phrase, keep scanning
                for c in page:
                    if c in bset:
                        matched.setdefault(c, set()).add(phrase)
                frm += 100
                if frm >= total or not page:
                    break
            done += 1
            rep.tick(done)
    return matched


# --------------------------------------------------------------------------------------------------
# Disclosure stream — the recent MATERIAL-EVENT stream (8-K + latest 10-Q + latest annual)
# --------------------------------------------------------------------------------------------------
_TAGBLOCK = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_ENT = re.compile(r"&#x[0-9a-fA-F]+;|&#\d+;|&[a-z]+;")


def _to_text(html: str) -> str:
    t = _TAGBLOCK.sub(" ", html)
    t = _TAG.sub(" ", t).replace("&amp;", "&").replace("&nbsp;", " ")
    return _WS.sub(" ", _ENT.sub(" ", t)).strip()


def _doc_url(cik: str, accession: str, primary_doc: str) -> str:
    return (f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
            f"{accession.replace('-', '')}/{primary_doc}")


_BUSINESS_PAT: tuple[str, ...] = (
    r"item\s*1\.?\s*business", r"item\s*1\b", r"business\s+overview",
    r"information on the company", r"\boverview\b",
)
_MDNA_PAT: tuple[str, ...] = (
    r"management.s discussion", r"item\s*2\b", r"recent developments", r"subsequent events",
)


def _section(text: str, patterns: tuple[str, ...], n: int) -> str:
    """The first ``n`` chars from where ``text`` enters a target section (Item 1 Business / MD&A),
    skipping the cover/TOC near the top — so the LLM reads BUSINESS PROSE, not cover/XBRL
    boilerplate (the bug that read the real enablers CAMT/AEHR as 'none' off the document head)."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m and m.start() > 1200:
            return text[m.start():m.start() + n]
    return text[:n]


def recent_disclosure_stream(
    edgar: EdgarClient,
    http: CachedHttp,
    cik: str,
    *,
    since: date,
    annual_lookback_days: int = 470,
    max_8k: int = 6,
    annual_chars: int = 16000,
    quarterly_chars: int = 10000,
    eightk_chars: int = 3500,
) -> list[tuple[str, str]]:
    """Pull the recent stream: latest annual (10-K/20-F/40-F, BUSINESS section) + latest 10-Q (MD&A
    / subsequent events) + 8-Ks filed since ``since``. Each item is ``(ref, text)``, ``ref`` the
    citable tag. The annual uses a WIDER lookback than the 8-K window so the latest annual is kept
    (the baseline of what the business IS); the 8-K stream catches recent material events (the IREN
    lesson — a hyperscaler contract filed as an 8-K). Section-extracted so the LLM reads prose, not
    the cover/XBRL. Fail-loud: a filing whose doc will not fetch is skipped, never fabricated."""
    fils = edgar.recent_filings(
        cik, forms=("10-K", "20-F", "40-F", "10-Q", "8-K"),
        since=since - timedelta(days=annual_lookback_days),
    )
    annuals = sorted((f for f in fils if f.form in ("10-K", "20-F", "40-F")),
                     key=lambda f: f.filing_date, reverse=True)
    quarters = sorted((f for f in fils if f.form == "10-Q"),
                      key=lambda f: f.filing_date, reverse=True)
    eightks = sorted((f for f in fils if f.form == "8-K" and f.filing_date >= since),
                     key=lambda f: f.filing_date, reverse=True)[:max_8k]
    plan: list[tuple[Any, int, tuple[str, ...]]] = []
    if annuals:
        plan.append((annuals[0], annual_chars, _BUSINESS_PAT))
    if quarters:
        plan.append((quarters[0], quarterly_chars, _MDNA_PAT))
    plan += [(f, eightk_chars, ()) for f in eightks]
    out: list[tuple[str, str]] = []
    for f, budget, pats in plan:
        if not f.primary_doc:
            continue
        try:
            html = http.get_text(_doc_url(f.cik, f.accession, f.primary_doc), ttl_seconds=_ONE_WEEK)
        except (HttpError, OSError):
            continue
        text = _to_text(html)
        chunk = _section(text, pats, budget) if pats else text[:budget]
        out.append((f"{f.form} {f.filing_date} (accession {f.accession})", chunk))
    return out


# --------------------------------------------------------------------------------------------------
# The fenced LLM exposure assessment (synthesis.py's architecture; assemble-not-conclude)
# --------------------------------------------------------------------------------------------------
EXPOSURE_TOOL: dict[str, Any] = {
    "name": "assemble_driver_exposure",
    "description": (
        "From ONLY the supplied filing-stream text, assemble the source-bound evidence of this "
        "company's DISCLOSED exposure to the NAMED DRIVER. You ASSEMBLE AND CITE; you do NOT rate, "
        "score, recommend, predict, or decide theme membership or investment merit — there is no "
        "verdict field, the human judges. A passing mention of the driver ('we use AI', 'exploring "
        "AI') is STATED-INTENT, not exposure; reserve binding-contract / quantified-revenue for a "
        "disclosed signed agreement (named counterparty + terms) or a disclosed $/% of revenue."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "disclosed_facts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "fact": {
                            "type": "string",
                            "description": "A SPECIFIC disclosed fact of driver exposure — "
                            "customer/tenant (named OR anonymized), contracted MW/capacity/TCV, "
                            "$/% revenue, agreement + binding terms. Paraphrase the filing; use "
                            "NO outside facts.",
                        },
                        "concreteness": {
                            "type": "string",
                            "enum": [c.value for c in ExposureConcreteness],
                            "description": "TYPE-APPROPRIATE strength. binding-contract = the "
                            "TERMS BIND (executed order form / min-volume / take-or-pay / "
                            "make-whole / quantified TCV / prepayment) — a FRAMEWORK, 'subject to "
                            "further agreement', sole-OPTION or backstop-only is "
                            "committed-capacity, NOT binding. quantified-revenue = a $/% BOTH "
                            "quantified AND attributable to a specific part of the driver — "
                            "BLENDED/general revenue is committed-capacity. committed-capacity = "
                            "committed MW/capex or real-but-not-contracted activity. stated-intent "
                            "= strategy/exploring. none.",
                        },
                        "driver_tie": {
                            "type": "string",
                            "enum": [t.value for t in DriverTie],
                            "description": "The SEPARATE tie gate — how specifically the fact ties "
                            "to THE DRIVER (the user message defines what driver-specific / "
                            "indirect / not-driver MEAN for this driver): driver-specific = tied "
                            "to a NAMED "
                            "element of the driver's structure; indirect = a generic/weak tie to "
                            "the driver; not-driver = an adjacent-but-distinct market.",
                        },
                        "source_ref": {
                            "type": "string",
                            "description": "Copy VERBATIM the '(accession ...)' tag of the stream "
                            "item it came from.",
                        },
                    },
                    "required": ["fact", "concreteness", "driver_tie", "source_ref"],
                },
            },
            "primary_business": {
                "type": "string",
                "description": "What the filings say the business primarily IS today — one short "
                "phrase, from the text.",
            },
            "key_unknowns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "What the disclosure does NOT resolve (driver revenue not broken "
                "out, contract contingencies, mention-only no terms).",
            },
        },
        "required": ["disclosed_facts", "primary_business", "key_unknowns"],
    },
}

# Driver-AGNOSTIC system prompt: the GENERAL grading rules (type-appropriate concreteness + the
# two-axis structure). What driver-specific / indirect / not-driver MEAN for a theme is NOT here
# — it is supplied per-theme by the DriverSpec (injected into the user message). No theme-specific
# strings, no per-theme example facts.
_SYSTEM = (
    "You read ONE company's recent SEC filing STREAM (latest annual + latest 10-Q + recent 8-Ks) "
    "and assemble its DISCLOSED exposure to a named driver, for a human analyst. Use ONLY the "
    "supplied text — never your own memory, never the web. Ground every fact in the filings and "
    "copy the '(accession ...)' tag of the item it came from as source_ref. If something is not "
    "disclosed, put it in key_unknowns; do NOT infer or supply it. You do NOT recommend, rate, "
    "score, predict, or decide theme membership or investment merit — there is no verdict field; "
    "the human judges. Grade EACH fact on TWO INDEPENDENT axes — concreteness (its strength) and "
    "driver_tie (its specificity to THE DRIVER, defined in the user message). A passing MENTION of "
    "the driver (a strategy nod, an 'exploring' or 'well-positioned' remark, a title/appointment) "
    "is STATED-INTENT, not exposure. CONCRETENESS is TYPE-APPROPRIATE. For a CONTRACT, grade "
    "binding-contract ONLY if the TERMS BIND — an executed order form, a minimum-volume / "
    "take-or-pay / make-whole obligation, a quantified total-contract-value, or a prepayment; a "
    "'definitive'/'master' agreement whose PRICING or VOLUME is 'subject to further agreement', or "
    "that grants only an OPTION or a BACKSTOP, is committed-capacity AT MOST — the LABEL "
    "'definitive' does not make the terms bind. Do NOT require a NAMED customer: an ANONYMIZED "
    "counterparty with BINDING terms is fully binding — penalize DEFERRED TERMS, never customer "
    "anonymity. For REVENUE, grade quantified-revenue ONLY if the $/% is BOTH quantified AND "
    "attributable to a SPECIFIC part of the driver; BLENDED/general revenue (not broken out to the "
    "driver) is committed-capacity at most. DRIVER_TIE is the SEPARATE gate — even a terms-binding "
    "contract is NOT real exposure if its tie is indirect. The user message defines what "
    "driver-specific / indirect / not-driver MEAN for THIS driver; grade the fact's tie by that "
    "definition. Judge the disclosed substance, not the vocabulary."
)


_ACC_RE = re.compile(r"\d{10}-\d{2}-\d{6}")   # an EDGAR accession, e.g. 0001628280-26-013305
_PROPER_RE = re.compile(r"\b[A-Z][A-Za-z0-9&.]{2,}\b")   # proper-noun-ish tokens (CoreWeave, HBM)
# a FINANCIAL FIGURE — a $-amount, or a magnitude with a scale word. These (with company-specific
# names) are the load-bearing, hard-to-fabricate tokens; a bare small integer or a YEAR carries no
# such weight, so a '$' or a scale word is REQUIRED here (a bare '400' / '2026' is not a figure).
_SCALE_WORDS: dict[str, int] = {
    "k": 1_000, "thousand": 1_000, "m": 1_000_000, "mm": 1_000_000, "million": 1_000_000,
    "b": 1_000_000_000, "bn": 1_000_000_000, "billion": 1_000_000_000,
}
_FIGURE_RE = re.compile(
    r"\$\s*(\d[\d,]*(?:\.\d+)?)\s*(thousand|million|billion|mm|bn|k|m|b)?\b"       # $-prefixed
    r"|(?<![\w$])(\d[\d,]*(?:\.\d+)?)\s*(thousand|million|billion|mm|bn|k|m|b)\b",  # scale-suffixed
    re.IGNORECASE,
)
# common words that happen to be capitalized/numeric but do NOT discriminate a real fact from a
# fabricated one (they appear in almost any filing) — excluded from the grounding check
_GROUNDING_STOP = {
    "the", "this", "that", "for", "with", "and", "our", "its", "company", "corp", "inc", "llc",
    "corporation", "approximately", "including", "revenue", "agreement", "contract", "customer",
    "products", "services", "million", "billion", "the company",
}


def _cited_filing_text(ref: str, stream: list[tuple[str, str]]) -> str | None:
    """The ONE stream item a fact's ref names, or None — and None means UNCITED (audit G-D5).

    The model is told to copy the item's '(accession ...)' tag, so a ref resolves by the single
    accession it carries, or by being that item's whole ref (on the verbatim check's key). The cite
    used to be a substring test either way, so ``''`` — a substring of every ref — was cited, and
    since it carries no accession the grounding below was SKIPPED and its concreteness credited the
    basis. A ref naming two filings resolves to neither: a fact has one source."""
    accessions = set(_ACC_RE.findall(ref))
    if len(accessions) == 1:
        acc = accessions.pop()
        return next((text for r, text in stream if acc in _ACC_RE.findall(r)), None)
    if accessions:
        return None
    key = comparison_key(ref)
    return next((text for r, text in stream if key and comparison_key(r) == key), None)


def _driver_vocab(spec: DriverSpec) -> frozenset[str]:
    """The DRIVER'S OWN vocabulary (prefilter terms + provenance-tag keywords), tokenized to
    lowercase words + singular stems. These are theme-GENERIC — the LLM writes them in BOTH a
    positive claim AND its NEGATIVE reasoning ('… NOT tied to attritable UAVs, counter-UAS,
    loitering munitions …'), so they cannot discriminate a real fact from a fabricated one here.
    Excluded from the grounding tokens so a fact grounds on its COMPANY-specific tokens (a
    counterparty, a $-figure), not the theme's own words — a fabricated counterparty / figure is
    NEVER driver vocabulary, so it is still caught."""
    words: set[str] = set()
    kw_iter = (kw for _, kws in spec.provenance_tags for kw in kws)
    for phrase in (*spec.prefilter_terms, *kw_iter):
        for w in re.split(r"[\s/&.-]+", phrase.lower()):
            if len(w) >= 2:
                words.add(w)
                words.add(w.rstrip("s"))   # UAV/UAVs, munition/munitions
    return frozenset(words)


def _figure_forms(mantissa: str, scale: str) -> set[str]:
    """The comma-free digit forms a filing might carry for one financial figure: the bare mantissa
    and, if a scale word is present, the scale-multiplied integer — so a fact's '$47,829K' /
    '$9.5 million' matches a filing's '47,829' / '9.5 million' / raw integer. Comma variants are
    covered by comma-stripping the filing side before matching."""
    bare = mantissa.replace(",", "")
    forms = {bare}
    if scale and scale.lower() in _SCALE_WORDS:
        # bare is regex-guaranteed a plain decimal (digits + at most one '.'), so float() is safe
        forms.add(str(int(round(float(bare) * _SCALE_WORDS[scale.lower()]))))
    return forms


def _fact_grounded(
    fact_text: str, filing_text: str, driver_vocab: frozenset[str] = frozenset()
) -> bool:
    """FUZZY grounding: does the LLM's paraphrased ``fact``'s LOAD-BEARING content appear in the
    cited filing? The load-bearing, fabrication-resistant tokens are (1) COMPANY-specific proper
    nouns (a counterparty / product / program) and (2) FINANCIAL FIGURES — NOT the driver's own
    vocabulary (excluded via ``driver_vocab``; the LLM uses it in reasoning), NOT bare years/counts.
    Figures match under scale-word + comma NORMALIZATION. Require >=half the distinctive tokens to
    appear (substring); ADDITIONALLY a quantitative claim whose EVERY figure is absent fails closed
    (a fabricated / mis-cited number). A fact with NO distinctive tokens is not checkable and passes
    (low-risk). Ungrounded = the audit's fact/accession-mismatch mode (a fabricated fact carrying a
    real accession), which does NOT scale to hand-check at multi-theme volume; fail loud."""
    fl = filing_text.lower()
    fl_nc = fl.replace(",", "")   # comma-normalized filing for figure matching
    raw = {t.lower() for t in _PROPER_RE.findall(fact_text)} - _GROUNDING_STOP
    propers = {p for p in raw if p not in driver_vocab and p.rstrip("s") not in driver_vocab}
    figures: list[set[str]] = []
    for m in _FIGURE_RE.finditer(fact_text):
        mant, scale = m.group(1) or m.group(3) or "", m.group(2) or m.group(4) or ""
        if len(mant.replace(",", "").replace(".", "")) >= 2:
            figures.append(_figure_forms(mant, scale))
    if not propers and not figures:
        return True
    figure_hits = sum(any(f in fl_nc for f in forms) for forms in figures)
    if figures and figure_hits == 0:
        return False   # a quantitative claim whose every figure is absent — fail-closed
    proper_hits = sum(1 for p in propers if p in fl)
    return (proper_hits + figure_hits) / (len(propers) + len(figures)) >= 0.5


def assess_exposure(
    spec: DriverSpec,
    ticker: str,
    cik: str,
    stream: list[tuple[str, str]],
    *,
    llm: LlmClient,
) -> ExposureAssessment:
    """Run the fenced LLM over the disclosure stream → a cite-checked, verdict-free assessment for
    the driver defined by ``spec`` (theme-parameterized; AI-datacenter is one DriverSpec instance).
    The ``exposure_basis`` is DERIVED from the CITED + GROUNDED facts' max concreteness (not trusted
    from the LLM): no cited concrete fact → ``no-theme-exposure-disclosed`` (fail-loud; a mention is
    not exposure). Cite-check is TWO-STAGE: the accession must trace to the stream AND the fact's
    load-bearing text must be grounded in that filing (``_fact_grounded``) — an ungrounded fact is
    fail-closed. An empty stream yields NONE + a flag; an LLM error yields ``unassessed-error`` + a
    flag — never a fabricated exposure, and never a false NONE."""
    stream_refs = [ref for ref, _ in stream]
    base = ExposureAssessment(
        ticker=ticker, cik=cik, driver=spec.description,
        exposure_basis=ExposureBasis.NONE_DISCLOSED,
        disclosed_facts=[], primary_business="", key_unknowns=[], stream_refs=stream_refs,
        model=llm.model,
    )
    if not stream:
        return base.model_copy(update={"flags": ["no recent filings fetched — cannot assess"]})
    fenced = "\n\n".join(f"=== {ref} ===\n{text}" for ref, text in stream)
    user = (f"Company ticker: {ticker}. DRIVER to assess exposure to:\n{spec.description}\n\n"
            f"HOW A FACT TIES TO THIS DRIVER (grade driver_tie by this):\n{spec.tie_taxonomy}\n\n"
            f"Recent filing stream (cite the '(accession ...)' tag; use ONLY this):\n\n{fenced}")
    try:
        raw = llm.extract(system=_SYSTEM, user=user, tool=EXPOSURE_TOOL)
    except LlmError as exc:
        return base.model_copy(update={
            "exposure_basis": ExposureBasis.UNASSESSED_ERROR, "flags": [f"LLM error: {exc}"]})

    driver_vocab = _driver_vocab(spec)   # driver's own words — excluded from grounding
    flags: list[str] = []
    facts: list[ExposureFact] = []
    best = 0
    for item in raw.get("disclosed_facts", []) or []:
        if not isinstance(item, dict):
            continue
        try:
            conc = ExposureConcreteness(str(item.get("concreteness", "none")))
        except ValueError:
            conc = ExposureConcreteness.NONE
        try:
            tie = DriverTie(str(item.get("driver_tie", "indirect")))
        except ValueError:
            tie = DriverTie.INDIRECT  # missing/invalid tie → conservative (caps at committed)
        ref = str(item.get("source_ref", ""))
        fact_text = str(item.get("fact", ""))
        filing_text = _cited_filing_text(ref, stream)
        if filing_text is None:
            flags.append(f"UNCITED fact (ref not in stream): '{fact_text[:60]}'")
            conc = ExposureConcreteness.NONE  # uncited fact can't credit the basis (fail-closed)
        elif not _fact_grounded(fact_text, filing_text, driver_vocab):
            flags.append(f"UNGROUNDED fact-text (not found in cited filing): '{fact_text[:60]}'")
            conc = ExposureConcreteness.NONE  # ungrounded fact can't credit the basis
        if _DIRECTIONAL.search(fact_text):
            flags.append(f"DIRECTIONAL language in fact: '{fact_text[:60]}'")
        facts.append(
            ExposureFact(fact=fact_text, concreteness=conc, driver_tie=tie, source_ref=ref)
        )
        best = max(best, _effective_rank(conc, tie))
    primary = str(raw.get("primary_business", ""))
    if _DIRECTIONAL.search(primary):
        flags.append(f"DIRECTIONAL language in primary_business: '{primary[:60]}'")
    return base.model_copy(update={
        "exposure_basis": _BASIS_FOR[best],
        "disclosed_facts": facts,
        "primary_business": primary,
        "key_unknowns": [str(u) for u in (raw.get("key_unknowns") or [])],
        "flags": flags,
    })


# --------------------------------------------------------------------------------------------------
# The universe scan (build 1 — the scale-discrimination test)
# --------------------------------------------------------------------------------------------------
_ABORT_AFTER = 3  # consecutive same-4xx (quota/auth) failures that abort a scan before poisoning


class ScanAbortedError(RuntimeError):
    """Raised when a scan aborts fast on 3 consecutive same-4xx (quota/auth) failures — the run is
    stopped BEFORE writing a poisoned queue (the 2026-07-13 quota incident: 22 error records a naive
    run persisted as tier none). Carries the status, assessed-so-far, and the un-scanned names."""

    def __init__(self, status: int, reason: str, remaining: list[str],
                 assessed: list[ExposureAssessment]) -> None:
        self.status = status
        self.reason = reason
        self.remaining = remaining
        self.assessed = assessed
        super().__init__(
            f"scan ABORTED after {_ABORT_AFTER} consecutive HTTP {status} failures ({reason}); "
            f"{len(remaining)} names un-scanned — refusing to write a poisoned queue")


def _client_error_status(exc: BaseException) -> int | None:
    """The HTTP status if ``exc`` is a 4xx CLIENT error (quota/auth → SYSTEMIC), else None (5xx/
    network → a per-name transient that must NOT trip the abort). Reads the anthropic SDK's
    ``status_code`` (APIStatusError); absent → None."""
    status = getattr(exc, "status_code", None)
    return status if isinstance(status, int) and 400 <= status < 500 else None


def scan_driver_exposure(
    spec: DriverSpec,
    names: list[tuple[str, str]],
    *,
    edgar: EdgarClient,
    sec_http: CachedHttp,
    efts_http: CachedHttp,
    llm: LlmClient,
    startdt: str,
    enddt: str,
    max_workers: int = 8,
    progress: ProgressFn | None = None,
) -> tuple[dict[str, set[str]], list[ExposureAssessment]]:
    """Scan the sub-$10B universe for exposure to ONE driver (``spec``). Returns the prefilter (the
    keyword flood, from ``spec.prefilter_terms``) + the per-candidate assessments (the
    discrimination). The human reads the flagged set + each one's disclosed-fact basis to audit the
    false-positive rate directly."""
    ciks = [c for _, c in names]
    ticker_by_cik = {c: t for t, c in names}
    prefilter_skips: list[str] = []
    matched = mention_prefilter(efts_http, ciks, spec.prefilter_terms, startdt=startdt, enddt=enddt,
                                skip_errors=True, skipped=prefilter_skips, progress=progress)
    if prefilter_skips:
        # NOT a warning to be scrolled past: the scan's denominator is now unknown, so every count
        # derived from it ("N graded", any share of N) is N-that-succeeded over an unknown base.
        print(f"!! PREFILTER RECALL GAP — {len(prefilter_skips)} batch×phrase quer(ies) "
              f"errored and were SKIPPED. Each batch holds up to 100 CIKs, so this scan's "
              f"population is a LOWER BOUND and its denominator is unknown. "
              f"Do not report a share of it.")
        for line in prefilter_skips[:10]:
            print(f"   {line}")
        if len(prefilter_skips) > 10:
            print(f"   … and {len(prefilter_skips) - 10} more")
    candidates = sorted(matched)
    since = date.fromisoformat(startdt)
    rep = ProgressReporter("exposure scan", len(candidates), emit=progress)
    out: list[ExposureAssessment] = []

    def work(cik: str) -> ExposureAssessment:
        stream = recent_disclosure_stream(edgar, sec_http, cik, since=since)
        return assess_exposure(spec, ticker_by_cik[cik], cik, stream, llm=llm)

    streak = 0  # consecutive same-4xx failures — abort-fast at _ABORT_AFTER (don't poison)
    last_status: int | None = None
    with cf.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(work, c): c for c in candidates}
        for i, fut in enumerate(cf.as_completed(futures), 1):
            c = futures[fut]
            try:
                out.append(fut.result())
                streak = 0  # a success breaks the systemic-failure streak
            except Exception as exc:  # noqa: BLE001 — fail-loud per name, never drop silently
                if isinstance(exc, SecRateLimitedError):
                    # SEC REFUSED THE RUN (2026-10-29): stop, never grade it as one more failed name
                    # — the next name would wait out SEC's hold, send, and be refused again.
                    for f in futures:
                        f.cancel()
                    raise SecRateLimitedError(
                        f"the exposure scan STOPPED — {exc} — {len(out)} of {len(candidates)} "
                        f"name(s) assessed") from exc
                status = _client_error_status(exc)
                if status is not None and status == last_status:
                    streak += 1
                elif status is not None:
                    streak = 1  # first of a new same-4xx streak
                else:
                    streak = 0  # 5xx/network transient — does NOT trip the abort
                last_status = status
                out.append(ExposureAssessment(
                    ticker=ticker_by_cik[c], cik=c, driver=spec.description,
                    exposure_basis=ExposureBasis.UNASSESSED_ERROR, disclosed_facts=[],
                    primary_business="", key_unknowns=[], stream_refs=[],
                    flags=[f"scan error: {type(exc).__name__}: {exc}"]))
                if status is not None and streak >= _ABORT_AFTER:
                    for f in futures:
                        f.cancel()  # cancel PENDING; running finish on __exit__, results discarded
                    done = {a.cik for a in out}  # what the loop processed (not future.done())
                    remaining = sorted(ticker_by_cik[cc] for cc in candidates if cc not in done)
                    reason = f"{type(exc).__name__}: {exc}"
                    raise ScanAbortedError(status, reason, remaining, out) from exc
            rep.tick(i)
    return matched, flag_intra_population_control(out)


# --------------------------------------------------------------------------------------------------
# Same asset, two tickers (2026-09-02)
# --------------------------------------------------------------------------------------------------
# BTBT holds ~70.5% of WYFI, and BOTH graded binding-contract in the ai-compute-platform scan — one
# asset counted twice in a nine-name tier. It had already been caught by hand once on the parent
# sheet and came back unnoticed, so the catch belongs in the scan, not in the reader.
#
# This FLAGS and never drops. Which side of a control pair carries the exposure is an adjudication
# (the parent may be a holding company whose only exposure IS the sub, or the sub may be a sliver of
# a diversified parent) — assemble-not-conclude.
_MAJORITY_CONTROL = re.compile(
    r"majority[- ](?:equity|ownership|owned|stake|interest)"
    r"|majority stake"
    r"|controlling (?:equity |ownership |financial )?interest"
    r"|(?:5[1-9]|[6-9][0-9]|100)(?:\.[0-9]+)?%[^.]{0,40}(?:equity|ownership|stake|interest|owned)"
    r"|wholly[- ]owned subsidiary",
    re.I,
)
# A ticker cited the way a filing actually cites another PUBLIC company: exchange-qualified.
# The bare-symbol form cannot be used — an unqualified \b[A-Z]{2,5}\b scan of this corpus matched
# the English words "AI" (C3.ai) and "IT" (Gartner) and produced 8 false pairs against 1 true one.
_QUALIFIED_TICKER = re.compile(
    r"\((?:nasdaq|nyse|nyse american|amex|cboe)[^)]{0,20}:\s*([A-Z]{1,5})\)", re.I)
_CONTROL_WINDOW = 250  # chars either side of the control phrase the ticker cite must fall within


def flag_intra_population_control(
    rows: Sequence[ExposureAssessment],
) -> list[ExposureAssessment]:
    """Flag every pair where one scanned issuer discloses MAJORITY CONTROL of ANOTHER scanned
    issuer, so a tier cannot silently count one asset twice. Both sides are flagged, since either
    row may be the one a reader opens.

    PRECISION was verified on the live 745-name ai-compute-platform corpus: one pair (BTBT -> WYFI),
    zero false positives. **RECALL IS UNKNOWN** — not low, UNKNOWN: there is no ground-truth set of
    control pairs for this universe, so nothing here quantifies what fraction it finds. What IS
    measurable is how rare its only input signal is: ``disclosed_facts`` are driver-exposure
    extracts rather than filing text, and an exchange-qualified subsidiary cite appeared in 2 of
    those 745 rows.

    Read ``control_pair_coverage`` beside any result. An empty return is NOT a clean bill, and a
    scan that reports no pairs must never print as though it had cleared the population — that is
    the shape of a check that returns the same answer whatever it is given. The complete source is
    EDGAR Exhibit 21 (Subsidiaries of the Registrant), not extracted anywhere in this repo yet.
    """
    in_population = {r.ticker for r in rows}
    controls: dict[str, list[tuple[str, str]]] = {}   # parent -> [(sub, quoted phrase)]
    for row in rows:
        text = " ".join(f.fact for f in row.disclosed_facts)
        for m in _MAJORITY_CONTROL.finditer(text):
            window = text[max(0, m.start() - _CONTROL_WINDOW): m.end() + _CONTROL_WINDOW]
            for sub in _QUALIFIED_TICKER.findall(window):
                if sub in in_population and sub != row.ticker:
                    pair = (sub, m.group(0))
                    if pair not in controls.setdefault(row.ticker, []):
                        controls[row.ticker].append(pair)
    if not controls:
        return list(rows)
    flagged: list[ExposureAssessment] = []
    for row in rows:
        notes: list[str] = []
        for sub, phrase in controls.get(row.ticker, []):
            notes.append(
                f"CONTROL PAIR: this issuer discloses majority control of {sub}, also in this scan "
                f"('{phrase}') — counting both double-counts one asset")
        for parent, pairs in controls.items():
            for sub, phrase in pairs:
                if sub == row.ticker:
                    notes.append(
                        f"CONTROL PAIR: {parent}, also in this scan, discloses majority control of "
                        f"this issuer ('{phrase}') — counting both double-counts one asset")
        flagged.append(row.model_copy(update={"flags": [*row.flags, *notes]}) if notes else row)
    return flagged


def control_pair_coverage(rows: Sequence[ExposureAssessment]) -> str:
    """What the control-pair check could SEE, stated whether or not it found anything.

    A zero-pair result is the dangerous one: it reads as "population clean" when it may mean
    "population unreadable". This exists so the scan cannot print a pass it has not earned — the
    same failure shape as a magnitude check that answered YES for every name and therefore measured
    nothing. The wording says UNKNOWN even when pairs WERE found, because finding one bounds
    nothing about the rest.
    """
    n = len(rows)
    readable = sum(
        1 for r in rows
        if _QUALIFIED_TICKER.search(" ".join(f.fact for f in r.disclosed_facts))
    )
    pairs = sum(1 for r in rows for f in r.flags if f.startswith("CONTROL PAIR"))
    share = f"{readable / n:.1%}" if n else "n/a"
    return (
        f"control pairs: {pairs} flag(s) over {n} rows — COVERAGE UNKNOWN. The check reads "
        f"driver-exposure extracts, not filings, and can only see an exchange-qualified subsidiary "
        f"cite: {readable} of {n} rows ({share}) carry one. With no ground-truth set its recall is "
        f"unquantified, so this neither clears the population nor bounds how many pairs remain. "
        f"Complete source: EDGAR Exhibit 21, not extracted."
    )
