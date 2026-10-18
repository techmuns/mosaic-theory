"""ENRICHMENT — the listed companies a thesis's own mechanism implies, as EXTERNAL HYPOTHESES.

Why (operator request 2026-10-14): the sources name almost no companies. Across the pilot's 13
articles, 109 named organisations held 0 potential beneficiaries; 0 of 15 theses named a US-listed
exposure. A thesis such as "HBM supply tightness benefits memory suppliers" then shows no company
at all, though its mechanism plainly reaches some. This step asks the model which listed companies
that mechanism reaches.

What it is — and is not:
- INPUT: the thesis card's own lines only (statement, transmission steps, the sectors and business
  groups its source names, the companies its source names). Never the article's text.
- OUTPUT: per company, the transmission step (`s03.N`) its earnings move through, which way, how,
  and what the company does. Every proposal is an EXTERNAL HYPOTHESIS: labelled ours, shown apart
  from what the source says, stored in its own table (`enrichments`), never in the sealed thesis
  version. NO PRIORITY RULE READS IT — the research action is decided without it (pinned).
- CHECKED, deterministically: the step must be one of the card's earnings steps (a price move is
  not one); a company the source already names is never proposed again; at most four per side.
  Every name then goes through the SAME SEC resolution as a source-named company — identity
  before ticker, point-in-time common equity. A ticker the SEC does not verify is never shown as
  one: the name stays, said unverified.
- NOT A RANKING, NOT A GATE. It selects on the mechanism the thesis states, not on a disclosure
  form, and it decides nothing. ACCEPTED RISK: a model's recall favours familiar large companies;
  the prompt asks for companies to whom the step is material, and the analyst checks each.

THE CONDITION (2026-10-15, operator: "how do you know if Atlassian, Twilio will be hurt?"). Every
proposal records the label of the step it rests on. A step that is not a fact — the source's
opinion, a forecast, our own inference — makes the direction a CONDITION: the company is EXPOSED,
and would benefit / be hurt only IF the step holds; every surface says so, never a bare "hurt".

THE BASIS. The model states how the company earns from the exposed line (`BASIS_MODELS`), and it
is CHECKED against the company's own latest annual report on or before the as-of: the filing's
OWN revenue-source sentences ("We derive our revenues from …", "Our revenue is primarily derived
from …") are found by their anchor, and the model words they contain are compared with the one
stated. A whole-filing phrase search was measured first and refused: real 10-Ks mention nearly
every model somewhere (Adobe matched 5 of 7, Salesforce's "per seat" hit was an attrition
sentence), so a hit proved nothing. DOES THIS SELECT ON FORM? It reads a disclosure, so its
"not described" is a statement about the filing's words, never about the business: it removes,
ranks and decides nothing — it is shown beside the proposal with the filing's sentence, for the
analyst to read.
"""

from __future__ import annotations

import functools
import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from vinci.netcache import HttpError
from vinci.theme_intelligence.cachefile import read_json, write_json
from vinci.theme_intelligence.cards import BASIS_LABEL, capped_label, not_a_sector, without_labels
from vinci.theme_intelligence.config import ENRICH_PROMPT_VERSION, LLM_MODEL
from vinci.theme_intelligence.extract import ToolClient, answer_list, cache_key, cost_of
from vinci.theme_intelligence.schemas import (
    CardContent,
    Direction,
    EnrichmentCandidate,
    EnrichmentSet,
    EntityType,
    Mention,
    MentionRole,
    Provenance,
    RecommendationStatus,
    ResolutionStatus,
)
from vinci.theme_intelligence.securities import AnnualReport, SecResolver
from vinci.theme_intelligence.verify import distinct_listings, norm_name, same_company

PER_SIDE = 4  # at most this many that could benefit, and as many that could be hurt

#: how a company earns from a line of business — and the words its OWN revenue-source sentence
#: uses for it (face-validity table, read only inside those sentences; never tuned)
BASIS_MODELS: dict[str, re.Pattern[str]] = {k: re.compile(v, re.I) for k, v in {
    "subscription": r"\bsubscriptions?\b|\bper[- ](?:seat|user)\b|\bseat[- ]based\b|"
                    r"\bsoftware[- ]as[- ]a[- ]service\b",
    "usage_based": r"\busage[- ]based\b|\bconsumption[- ]based\b|\bbased (?:up)?on (?:usage|"
                   r"consumption)\b|\bpay[- ]as[- ]you[- ]go\b",
    "transaction_fees": r"\btransaction(?:-based)? fees?\b|\bper[- ]transaction\b|"
                        r"\bpayment processing\b|\btake rate\b",
    "licences": r"\blicen[cs]es?\b|\blicensing\b|\bmaintenance\b",
    "product_sales": r"\bproduct sales\b|\bsales? of (?:our )?(?:products|hardware|systems|"
                     r"equipment)\b|\bhardware\b",
    "advertising": r"\badvertising\b",
    "services": r"\bprofessional services\b|\bservices revenues?\b|\bconsulting\b",
}.items()}
#: a filing's OWN statement of where its revenue comes from — the anchor the basis check reads
_REVENUE_SOURCE = re.compile(
    r"\b(?:we|the company)\s+(?:primarily\s+|principally\s+|mainly\s+)?(?:generate|derive|earn)s?"
    r"\s+(?:(?:substantially all|the (?:vast |substantial )?majority|most|a (?:significant |"
    r"substantial )?majority|a significant portion)\s+of\s+)?(?:our\s+|its\s+)?(?:total\s+)?"
    r"revenues?\b|\b(?:our|its)\s+(?:total\s+)?revenues?\s+(?:is|are|was|were)\s+(?:primarily\s+|"
    r"principally\s+|mainly\s+|predominately\s+|predominantly\s+)?(?:derived|generated|earned)\b",
    re.I)
#: how many of a filing's revenue-source sentences a proposal carries (the count is said)
BASIS_SENTENCES = 2
#: the steps by which a thesis reaches earnings — a market reaction is a price move, never one
EARNINGS_STEPS = ("industry_shift", "volumes", "pricing", "costs", "margins", "cash_flow",
                  "listed_earnings")
LABEL = "EXTERNAL HYPOTHESIS — not named by the source"

SYSTEM = """You propose the LISTED COMPANIES whose earnings a research thesis would move. Your \
answer is an EXTERNAL HYPOTHESIS for an analyst to check: it is shown apart from what the source \
says, labelled as ours, and never changes the thesis or its research action.

You receive ONE thesis: its statement, the steps by which it reaches company earnings (each with \
an id such as s03.1), the sectors and business groups its source names, and the companies its \
source already names.

Rules:
1. Propose only companies whose shares trade on a US exchange (NYSE or Nasdaq), as common stock \
or as an ADR. Give the ticker as it trades there.
2. Each company must be exposed THROUGH ONE OF THE GIVEN STEPS: give that step's id, whether its \
earnings would benefit or be hurt, and how — in at most 30 words, naming the part of its business \
that is exposed.
3. Prefer companies for which that business is a large share of revenue or profit. Propose a \
diversified group only when the step is material to it, and say why.
4. Never propose a company the source already names. Never propose a private company, an index, a \
fund or a government body.
5. Do not use share prices, valuations, ratings, price targets or returns: this is about which \
earnings the mechanism reaches, not about whether a stock is attractive.
6. At most four that could benefit and four that could be hurt. If no listed company is clearly \
exposed through a step, return none — an empty list is a correct answer — and say why in \
none_reason.
7. State the BASIS: the line of business the step reaches (revenue_line, at most 12 words) and \
how the company earns from it (revenue_model, one of the listed values) — as its own annual \
report would describe it. It is checked against that report; "other" when none fits.

The shape of ONE entry (illustrative — the company and step are not a suggestion):
{"name": "Micron Technology", "ticker": "MU", "exchange": "Nasdaq", "direction": "benefit", \
"step_id": "s03.1", "business": "memory chip maker (DRAM, NAND, HBM)", "exposure": "HBM is a \
growing share of its DRAM revenue; higher contract prices lift its margins directly.", \
"revenue_line": "DRAM and HBM memory chips", "revenue_model": "product_sales"}

Record the answer with the record_enrichment tool."""

TOOL: dict[str, Any] = {
    "name": "record_enrichment",
    "description": "The listed companies the thesis's own steps reach — external hypotheses.",
    "input_schema": {
        "type": "object",
        "properties": {
            "companies": {
                "type": "array", "maxItems": 2 * PER_SIDE,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "ticker": {"type": "string"},
                        "exchange": {"type": "string"},
                        "direction": {"type": "string", "enum": ["benefit", "hurt"]},
                        "step_id": {"type": "string"},
                        "business": {"type": "string",
                                     "description": "what the company does, at most 12 words"},
                        "exposure": {"type": "string",
                                     "description": "how the step moves its earnings, at most "
                                                    "30 words"},
                        "revenue_line": {"type": "string",
                                         "description": "the line of business the step reaches, "
                                                        "at most 12 words"},
                        "revenue_model": {"type": "string", "enum": [*BASIS_MODELS, "other"],
                                          "description": "how the company earns from that line"},
                    },
                    "required": ["name", "ticker", "direction", "step_id", "business",
                                 "exposure", "revenue_line", "revenue_model"],
                },
            },
            "none_reason": {"type": "string",
                            "description": "when no company is proposed: why"},
        },
        "required": ["companies"],
    },
}


def earnings_steps(card: CardContent) -> dict[str, tuple[str, str]]:
    """The card's stated steps to earnings: sentence id (`s03.N`) -> (step, text). A market
    reaction and a step the source leaves UNKNOWN are no mechanism."""
    return {f"s03.{i}": (st.step, without_labels(st.text))
            for i, st in enumerate(card.s03_transmission)
            if st.step in EARNINGS_STEPS and not st.text.startswith("UNKNOWN")}


def step_labels(card: CardContent) -> dict[str, Provenance]:
    """Each earnings step's label as the card states it (a conditional line is at most the
    source's opinion) — what makes a proposal's direction a fact or a condition."""
    return {f"s03.{i}": capped_label(st.provenance, st.text)
            for i, st in enumerate(card.s03_transmission)}


def models_in(sentence: str) -> set[str]:
    """The ways of earning a sentence names (`BASIS_MODELS`)."""
    return {k for k, rx in BASIS_MODELS.items() if rx.search(sentence)}


@functools.lru_cache(maxsize=16)  # one company is often proposed for several theses; a filing
# is ~0.5 MB of text, so the cache is kept small
def revenue_sources(text: str) -> tuple[str, ...]:
    """A filing's OWN revenue-source sentences that name a way of earning — each once, in the
    filing's order, each from its own "We derive / Our revenue is …" words: the page header or
    section title the text layer glued before it is left out (still a verbatim piece of the
    filing). A sentence about WHO pays ("sales to government customers", "customers outside
    the United States") names no way of earning and is not one."""
    out: list[str] = []
    for s in re.split(r"(?<=[.;])\s+", text):
        m = _REVENUE_SOURCE.search(s)
        if m is None or not 30 < len(s) < 700:
            continue
        own = s[m.start():].strip()
        if models_in(own) and own not in out:
            out.append(own)
    return tuple(out)


def _cut(s: str, n: int = 400) -> str:
    return s if len(s) <= n else s[:n].rstrip() + f" … [cut at {n} of {len(s)} characters]"


def check_basis(report: AnnualReport | None, why: str,
                model: str) -> tuple[str, tuple[str, ...], str, str]:
    """(status, the filing's own sentence(s), its source, a plain note) for one stated basis —
    see the module docstring. Never a verdict on the business: NOT_DESCRIBED is about the
    filing's words."""
    if model not in BASIS_MODELS:
        return "UNCHECKED", (), "", ("no basis stated" if not model else
                                     f"the basis “{BASIS_LABEL.get(model, model)}” names no way "
                                     f"of earning to look for")
    if report is None:
        return "UNCHECKED", (), "", why
    src = f"{report.form} filed {report.filed.isoformat()} ({report.accession})"
    sents = revenue_sources(report.text)
    if not sents:
        return "NOT_DESCRIBED", (), src, ("the filing states no revenue-source sentence naming a "
                                          "way of earning in the words this check reads — not "
                                          "found is not wrong; read the filing")
    hit = [s for s in sents if BASIS_MODELS[model].search(s)]
    pool = hit or sents
    shown = tuple(_cut(s) for s in pool[:BASIS_SENTENCES])
    more = f" (showing {len(shown)} of {len(pool)})" if len(pool) > len(shown) else ""
    if hit:
        # what else the same sentence names: a list that mentions it once among many is not
        # a filing calling it the main way of earning — the reader weighs it
        also = sorted(set().union(*(models_in(s) for s in hit)) - {model})
        return "IN_FILING", shown, src, (
            f"its revenue-source sentence names {BASIS_LABEL[model]}"
            + (f" — and also {', '.join(BASIS_LABEL[m] for m in also)}" if also else "") + more)
    named = sorted(set().union(*(models_in(s) for s in sents)))
    return "FILING_NAMES_OTHER", shown, src, (
        f"its revenue-source sentences name {', '.join(BASIS_LABEL[m] for m in named)} — not "
        f"{BASIS_LABEL[model]}{more}")


def named_by_source(card: CardContent) -> list[str]:
    """Every organisation the source names on this card — never proposed again."""
    av = card.s05_affected
    return list(dict.fromkeys(c.name_as_written for grp in (
        av.companies, av.instruments, av.private_or_unlisted, av.not_securities, av.also_named)
        for c in grp))


def user_message(card: CardContent, *, version: int, area: str, groups: list[str]) -> str:
    h = card.header
    steps = earnings_steps(card)
    av = card.s05_affected
    # only names that ARE sectors: a phrase, the whole market or an asset class is no population
    # to propose companies from (REVIEW of #737: "Treasurys; US equity; USD assets" fed a paid
    # call)
    sectors = "; ".join(f"{s.name} ({s.direction.value})" for s in av.sector_exposures
                        if not_a_sector(s.name) is None)
    named = named_by_source(card)
    lines = [f"THESIS {h.thesis_id} (version {version}): {h.title}",
             f"Area: {area} · Geography: {h.region}",
             "Statement: " + " ".join(without_labels(s.text) for s in card.s01_bottom_line),
             "Steps to company earnings:"]
    lines += [f"  [{sid}] ({step.replace('_', ' ')}) {text}"
              for sid, (step, text) in steps.items()]
    lines += [f"Sectors the source names as exposed: {sectors or 'none'}",
              f"Business groups the source names: {'; '.join(groups) or 'none'}",
              f"Companies the source already names (do NOT propose): {'; '.join(named) or 'none'}"]
    return "\n".join(lines)


@dataclass
class EnrichmentResult:
    enrichment: EnrichmentSet | None
    cached: bool = False
    usage: dict[str, int] | None = None
    cost_usd: float | None = None
    seconds: float = 0.0
    note: str = ""  # why no call was made (no stated step) — said, never silent
    notes: list[str] = field(default_factory=list)


def enrich_thesis(card: CardContent, *, version: int, area: str, groups: list[str],
                  client: ToolClient | None, cache_dir: Path, resolver: SecResolver,
                  as_of: date, run_id: str) -> EnrichmentResult:
    """One enrichment pass over one thesis version (see the module docstring). No stated step to
    earnings → no call, and the result says so."""
    tid = card.header.thesis_id
    steps = earnings_steps(card)
    if not steps:
        return EnrichmentResult(None, note="no stated step to company earnings — nothing for a "
                                           "company to be exposed through; no call made")
    user = user_message(card, version=version, area=area, groups=groups)
    model = client.model if client is not None else LLM_MODEL
    key = cache_key(model, ENRICH_PROMPT_VERSION, TOOL, SYSTEM, user)
    path = cache_dir / "enrich" / f"{key}.json"
    rec = read_json(path) if path.exists() else None  # a torn file reads as absent (U22)
    cached = rec is not None
    usage: dict[str, int] | None = None
    seconds = 0.0
    if rec is not None:
        out, usage = rec["output"], rec.get("usage")
    else:
        if client is None:
            raise RuntimeError("no cached enrichment for this thesis version and no LLM client "
                               "— run with ANTHROPIC_API_KEY set")
        t0 = time.monotonic()
        out = client.extract(system=SYSTEM, user=user, tool=TOOL)
        seconds = time.monotonic() - t0
        usage = getattr(client, "last_usage", None)
        write_json(path, {"model": model, "prompt_version": ENRICH_PROMPT_VERSION,  # kept FIRST
                          "usage": usage, "output": out}, sort_keys=True, indent=1)
    av = card.s05_affected  # every organisation the source names (`named_by_source`), listings too
    named_l = [(c.name_as_written, c.listings) for grp in (
        av.companies, av.instruments, av.private_or_unlisted, av.not_securities, av.also_named)
        for c in grp]
    labels = step_labels(card)
    refused: list[str] = []
    kept: list[EnrichmentCandidate] = []
    side_n = {Direction.POSITIVE: 0, Direction.NEGATIVE: 0}
    # a list sent as JSON text is decoded, anything else set aside AND SAID in the set's notes
    # (U20: `companies` as text gave 0 candidates, 0 refused, an empty note)
    rows, unread = answer_list(out, "companies")
    refused.extend(unread)
    for i, row in enumerate(rows):
        name = str(row.get("name") or "").strip()
        sid = str(row.get("step_id") or "").strip()
        direction = {"benefit": Direction.POSITIVE, "hurt": Direction.NEGATIVE}.get(
            str(row.get("direction") or ""))
        ticker = str(row.get("ticker") or "").strip().upper() or None
        # a company named like one the source names, or one already proposed: (why, its
        # listings, its name). With no ticker the names decide; with one, the SEC's verification
        # does, below — "Meta Materials" is not Meta Platforms (U11), while the pilot's second
        # "Rockwell" (a wrong ticker, DDAIF) stays a duplicate of Rockwell Automation (ROK)
        twins = [(w, ls, n) for w, pool in (
            ("the source already names it", named_l),
            ("proposed twice", [(k.name, k.listings) for k in kept]))
            for n, ls in pool if name and same_company(name, n)]

        why = ("no name" if not name else
               f"cites {sid or 'no step'}, not one of the card's steps to earnings "
               f"({', '.join(steps)})" if sid not in steps else
               "no direction (benefit or hurt)" if direction is None else
               twins[0][0] if twins and ticker is None else "")
        if not why and direction is not None and not twins and side_n[direction] >= PER_SIDE:
            why = f"more than {PER_SIDE} on one side"
        if why or direction is None:
            # numbered among the objects READ: an item set aside above is not counted
            refused.append(f"{name or f'object {i + 1} of {len(rows)} read'}: {why} — set aside")
            continue
        business = str(row.get("business") or "").strip()
        exposure = str(row.get("exposure") or "").strip()
        # the SAME resolution as a source-named company — identity before ticker, point in time.
        # A transient lookup object only: it is never stored as a mention (nothing the source
        # did not name is ever a mention). The identity check reads WHAT THE COMPANY DOES only —
        # the exposure sentence describes the mechanism, and its words misfired on the first real
        # pass (2026-10-14: a drug "pipeline" read as oil and gas and refused Merck; "nuclear
        # power demand" refused two uranium miners).
        lookup = Mention(
            mention_id="EN-lookup", article_id="", article_version_id="",
            name_as_written=name, normalized_name=norm_name(name), entity_type=EntityType.COMPANY,
            role=(MentionRole.POTENTIAL_BENEFICIARY if direction is Direction.POSITIVE
                  else MentionRole.POTENTIALLY_HARMED),
            role_detail=business, direction=direction,
            recommendation_status=RecommendationStatus.NOT_A_RECOMMENDATION, block_id="",
            quote="", ticker_hint=ticker)
        foreign = False
        basis_model = str(row.get("revenue_model") or "").strip()
        report: AnnualReport | None = None
        rwhy = "no verified US listing — no annual report to read"
        try:
            r = resolver.resolve(lookup, as_of=as_of)
            status, listings, registrant = r.status, r.listings, r.registrant
            rnote = r.note or r.method  # why — a refusal's reason sits in one or the other
            # a US line of a 20-F / 40-F filer (an ADR or a cross-listing): the resolver never
            # substitutes it for common equity; recorded as a fact, from the SEC's own data
            foreign = bool(status is ResolutionStatus.UNRESOLVED and r.cik
                           and resolver.is_foreign_private_issuer(r.cik, as_of=as_of))
            # the basis is read in the filing of the company the SEC verified — never of a
            # registrant the identity check refused
            # … and never for a duplicate about to be set aside (verified apart from EVERY
            # same-named company, or not at all)
            if r.cik and (listings or foreign) and basis_model in BASIS_MODELS and all(
                    distinct_listings(listings, tw[1]) for tw in twins):
                report, rwhy = resolver.annual_report(r.cik, as_of)
        except HttpError as exc:  # the SEC could not be read: the name stays, unverified
            status, listings, registrant = ResolutionStatus.UNRESOLVED, (), None
            rnote = f"the SEC could not be read ({exc}) — not verified"
            rwhy = rnote
        if twins:
            same = next((tw for tw in twins if not distinct_listings(listings, tw[1])), None)
            if same is not None:  # not verified apart: one company
                refused.append(f"{name}: {same[0]} — set aside")
                continue
            rnote = (f"{rnote} — named like {', '.join(tw[2] for tw in twins)}, but the SEC "
                     f"verifies a different listing ({', '.join(x.ticker for x in listings)})")
            if side_n[direction] >= PER_SIDE:
                refused.append(f"{name}: more than {PER_SIDE} on one side — set aside")
                continue
        side_n[direction] += 1
        bcheck, bquote, bsource, bnote = check_basis(report, rwhy, basis_model)
        kept.append(EnrichmentCandidate(
            enrichment_id="EC-" + hashlib.sha256(f"{tid}|{version}|{name}".encode())
            .hexdigest()[:14],
            thesis_id=tid, name=name, rationale=exposure, evidence=f"{sid}: {steps[sid][1]}",
            direction=direction, step_id=sid, business=business, ticker_hint=ticker,
            resolution_status=status, listings=listings, registrant=registrant,
            resolution_note=rnote, foreign_filer=foreign, step_label=labels.get(sid),
            revenue_model=basis_model, revenue_line=str(row.get("revenue_line") or "").strip(),
            basis_check=bcheck,
            basis_quote=bquote, basis_source=bsource, basis_note=bnote))
    if not kept and isinstance(out, dict) and out.get("none_reason"):
        refused.append(f"none proposed: {str(out['none_reason'])[:300]}")
    now = datetime.now(tz=UTC)
    es = EnrichmentSet(
        set_id="ES-" + hashlib.sha256(f"{tid}|{version}|{run_id}|{key}".encode()).hexdigest()[:14],
        thesis_id=tid, thesis_version=version, run_id=run_id, as_of=as_of, created_at=now,
        model=model, prompt_version=ENRICH_PROMPT_VERSION, candidates=tuple(kept),
        refused=tuple(refused))
    return EnrichmentResult(es, cached=cached, usage=usage,
                            cost_usd=0.0 if cached else cost_of(model, usage), seconds=seconds)
