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
from datetime import date, timedelta
from typing import Any, cast

from vinci.edgar import EdgarClient
from vinci.graph.llm import LlmClient, LlmError
from vinci.netcache import CachedHttp, HttpError
from vinci.progress import ProgressFn, ProgressReporter
from vinci.themes.schemas import (
    DriverTie,
    ExposureAssessment,
    ExposureBasis,
    ExposureConcreteness,
    ExposureFact,
)

_EFTS = "https://efts.sec.gov/LATEST/search-index"
_ONE_WEEK = 7 * 24 * 3600

# The ONE driver for build 1 — ground truth established by the semantic probe (REAL = CIFR/WULF
# binding hyperscaler leases, CAMT ~50% HBM rev, AEHR 34% AI burn-in; BETA = CLSK/MARA aspirational,
# VECO/ACLS ion-implant/diversified, and the flood of "we mention AI" names).
AI_DATACENTER_DRIVER = (
    "the AI-DATACENTER VALUE CHAIN — any layer of the chain that builds or supplies AI-datacenter "
    "compute: chips/GPU → HBM & memory → advanced packaging → thermal/cooling → power DELIVERED TO "
    "AI datacenters → optical interconnect → colocation/operator → AI-cloud. UPSTREAM ENABLERS ARE "
    "IN SCOPE (e.g. HBM / advanced-packaging metrology with quantified revenue) — they need not be "
    "datacenters themselves. Exposure must be CHAIN-SPECIFIC (a named layer) and grounded in "
    "disclosed activity — NOT generic power/equipment that merely 'could' feed a datacenter, NOT "
    "edge/on-device AI (the opposite of a datacenter), NOT a 'broad AI market' adjacency."
)

# Broad pre-filter net. Part-6 lesson: the driver-text is 'data center'/'HPC', not just 'AI' — cast
# WIDE so the SEMANTIC layer does the discrimination, not the keyword screen. 'artificial
# intelligence' is included precisely to pull in the cheap-mention flood the test must survive.
DRIVER_PHRASES: tuple[str, ...] = (
    "data center", "high-performance computing", "hyperscaler", "high bandwidth memory",
    "advanced packaging", "colocation", "artificial intelligence", "GPU",
)

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
    a terms-binding / quantified fact counts fully ONLY if it is CHAIN-SPECIFIC. An INDIRECT tie
    caps it at committed-capacity (borderline — real activity, soft datacenter tie, e.g. a fuel-cell
    CEPA 'for data center'); a NOT-DRIVER tie (edge/on-device, 'broad AI' adjacency) caps it at
    stated-intent (a mention, not exposure to THIS driver)."""
    r = _CONCRETE_RANK[conc]
    if tie is DriverTie.CHAIN_SPECIFIC:
        return r
    if tie is DriverTie.INDIRECT:
        return min(r, _CONCRETE_RANK[ExposureConcreteness.COMMITTED_CAPACITY])
    return min(r, _CONCRETE_RANK[ExposureConcreteness.STATED_INTENT])


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
    progress: ProgressFn | None = None,
) -> dict[str, set[str]]:
    """Batched-CIK efts: which universe CIKs mention each driver phrase recently. Returns
    ``{cik10: {phrases}}`` — the keyword 'flood' the semantic layer must then discriminate.

    Default is fail-loud (a bad efts body raises). ``skip_errors=True`` (for a long universe scan)
    skips a batch×phrase that errors after retries and keeps going — a conservative recall gap (a
    missed mention just means a name is not scanned), never a fabricated mention."""
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
                except HttpError:
                    if not skip_errors:
                        raise
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
                            "quantified AND attributable to a specific chain layer — "
                            "BLENDED/general revenue is committed-capacity. committed-capacity = "
                            "committed MW/capex or real-but-not-contracted activity. stated-intent "
                            "= strategy/exploring. none.",
                        },
                        "driver_tie": {
                            "type": "string",
                            "enum": [t.value for t in DriverTie],
                            "description": "The SEPARATE tie gate. chain-layer-specific = a "
                            "named AI-datacenter value-chain layer (GPU/compute, HBM/memory, "
                            "advanced packaging, thermal/cooling, power DELIVERED TO AI "
                            "datacenters, optical interconnect, colocation/operator, AI-cloud). "
                            "indirect = a generic/weak datacenter tie (generic power/equipment "
                            "'for data center', no AI/GPU language). not-driver = edge/on-device "
                            "AI (opposite of a datacenter) or a 'broad AI market' adjacency.",
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

_SYSTEM = (
    "You read ONE company's recent SEC filing STREAM (latest annual + latest 10-Q + recent 8-Ks) "
    "and assemble its DISCLOSED exposure to a named driver, for a human analyst. Use ONLY the "
    "supplied text — never your own memory, never the web. Ground every fact in the filings and "
    "copy the '(accession ...)' tag of the item it came from as source_ref. If something is not "
    "disclosed, put it in key_unknowns; do NOT infer or supply it. You do NOT recommend, rate, "
    "score, predict, or decide theme membership or investment merit — there is no verdict field; "
    "the human judges. Grade EACH fact on TWO INDEPENDENT axes — concreteness (its strength) and "
    "driver_tie (its specificity to the AI-datacenter VALUE CHAIN). A passing MENTION ('exploring "
    "AI', 'appointed an SVP of AI', 'AI is a tailwind') is STATED-INTENT, not exposure. "
    "CONCRETENESS is TYPE-APPROPRIATE. For a CONTRACT, grade binding-contract ONLY if the TERMS "
    "BIND — an executed order form, a minimum-volume / take-or-pay / make-whole obligation, a "
    "quantified total-contract-value, or a prepayment; a 'definitive'/'master' agreement whose "
    "PRICING or VOLUME is 'subject to further agreement', or that grants only an OPTION or a "
    "BACKSTOP, is committed-capacity AT MOST — the LABEL 'definitive' does not make the terms "
    "bind. Do NOT require a NAMED customer: an ANONYMIZED counterparty with BINDING terms is fully "
    "binding — penalize DEFERRED TERMS, never customer anonymity. For REVENUE, grade "
    "quantified-revenue ONLY if the $/% is BOTH quantified AND attributable to a SPECIFIC chain "
    "layer; BLENDED/general revenue ('supporting data center, AI and enterprise', not broken out) "
    "is committed-capacity at most. DRIVER_TIE is the SEPARATE gate — even a terms-binding "
    "contract is NOT real exposure if its tie is indirect. Grade chain-layer-specific ONLY for a "
    "named AI-datacenter chain layer (GPU/compute, HBM/memory, advanced packaging, "
    "thermal/cooling, power DELIVERED TO AI datacenters, optical interconnect, "
    "colocation/operator, AI-cloud); grade indirect for a generic/weak datacenter tie (generic "
    "power or equipment 'for data center applications' with NO AI/GPU language); grade not-driver "
    "for edge/on-device AI (the OPPOSITE of a datacenter) or a 'broad AI market' adjacency. "
    "UPSTREAM ENABLERS ARE IN SCOPE: a chip/HBM/packaging/thermal/power/optical supplier with "
    "quantified chain-attributable revenue (e.g. ~50% from HBM/advanced-packaging) is "
    "chain-layer-specific, even though it is not itself a datacenter. Judge the disclosed "
    "substance, not the vocabulary."
)


def _ref_traces(ref: str, universe: set[str]) -> bool:
    return any(ref == u or ref in u or u in ref for u in universe)


def assess_exposure(
    ticker: str,
    cik: str,
    driver: str,
    stream: list[tuple[str, str]],
    *,
    llm: LlmClient,
) -> ExposureAssessment:
    """Run the fenced LLM over the disclosure stream → a cite-checked, verdict-free assessment. The
    ``exposure_basis`` is DERIVED from the CITED facts' max concreteness (not trusted from the LLM):
    no cited concrete fact → ``no-theme-exposure-disclosed`` (fail-loud; a mention is not exposure).
    Fail-loud — an empty stream or an LLM error yields a NONE assessment + a flag, never a
    fabricated exposure."""
    stream_refs = [ref for ref, _ in stream]
    base = ExposureAssessment(
        ticker=ticker, cik=cik, driver=driver, exposure_basis=ExposureBasis.NONE_DISCLOSED,
        disclosed_facts=[], primary_business="", key_unknowns=[], stream_refs=stream_refs,
        model=llm.model,
    )
    if not stream:
        return base.model_copy(update={"flags": ["no recent filings fetched — cannot assess"]})
    fenced = "\n\n".join(f"=== {ref} ===\n{text}" for ref, text in stream)
    user = (f"Company ticker: {ticker}. DRIVER to assess exposure to:\n{driver}\n\n"
            f"Recent filing stream (cite the '(accession ...)' tag; use ONLY this):\n\n{fenced}")
    try:
        raw = llm.extract(system=_SYSTEM, user=user, tool=EXPOSURE_TOOL)
    except LlmError as exc:
        return base.model_copy(update={"flags": [f"LLM error: {exc}"]})

    refs = set(stream_refs)
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
        cited = _ref_traces(ref, refs)
        if not cited:
            flags.append(f"UNCITED fact (ref not in stream): '{fact_text[:60]}'")
            conc = ExposureConcreteness.NONE  # uncited fact can't credit the basis (fail-closed)
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
def scan_driver_exposure(
    names: list[tuple[str, str]],
    *,
    driver: str,
    phrases: tuple[str, ...],
    edgar: EdgarClient,
    sec_http: CachedHttp,
    efts_http: CachedHttp,
    llm: LlmClient,
    startdt: str,
    enddt: str,
    max_workers: int = 8,
    progress: ProgressFn | None = None,
) -> tuple[dict[str, set[str]], list[ExposureAssessment]]:
    """Scan the sub-$10B universe for exposure to ONE driver. Returns the prefilter (the keyword
    flood) + the per-candidate assessments (the discrimination). The human reads the flagged
    set + each one's disclosed-fact basis to audit the false-positive rate directly."""
    ciks = [c for _, c in names]
    ticker_by_cik = {c: t for t, c in names}
    matched = mention_prefilter(efts_http, ciks, phrases, startdt=startdt, enddt=enddt,
                                skip_errors=True, progress=progress)
    candidates = sorted(matched)
    since = date.fromisoformat(startdt)
    rep = ProgressReporter("exposure scan", len(candidates), emit=progress)
    out: list[ExposureAssessment] = []

    def work(cik: str) -> ExposureAssessment:
        stream = recent_disclosure_stream(edgar, sec_http, cik, since=since)
        return assess_exposure(ticker_by_cik[cik], cik, driver, stream, llm=llm)

    with cf.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(work, c): c for c in candidates}
        for i, fut in enumerate(cf.as_completed(futures), 1):
            c = futures[fut]
            try:
                out.append(fut.result())
            except Exception as exc:  # noqa: BLE001 — fail-loud per name, never drop silently
                out.append(ExposureAssessment(
                    ticker=ticker_by_cik[c], cik=c, driver=driver,
                    exposure_basis=ExposureBasis.NONE_DISCLOSED, disclosed_facts=[],
                    primary_business="", key_unknowns=[], stream_refs=[],
                    flags=[f"scan error: {type(exc).__name__}: {exc}"]))
            rep.tick(i)
    return matched, out
