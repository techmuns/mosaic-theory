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
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from vinci.netcache import HttpError
from vinci.theme_intelligence.config import ENRICH_PROMPT_VERSION, LLM_MODEL
from vinci.theme_intelligence.extract import ToolClient, cache_key, cost_of
from vinci.theme_intelligence.schemas import (
    CardContent,
    Direction,
    EnrichmentCandidate,
    EnrichmentSet,
    EntityType,
    Mention,
    MentionRole,
    RecommendationStatus,
    ResolutionStatus,
)
from vinci.theme_intelligence.securities import SecResolver
from vinci.theme_intelligence.verify import norm_name

PER_SIDE = 4  # at most this many that could benefit, and as many that could be hurt
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

The shape of ONE entry (illustrative — the company and step are not a suggestion):
{"name": "Micron Technology", "ticker": "MU", "exchange": "Nasdaq", "direction": "benefit", \
"step_id": "s03.1", "business": "memory chip maker (DRAM, NAND, HBM)", "exposure": "HBM is a \
growing share of its DRAM revenue; higher contract prices lift its margins directly."}

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
                    },
                    "required": ["name", "ticker", "direction", "step_id", "business",
                                 "exposure"],
                },
            },
            "none_reason": {"type": "string",
                            "description": "when no company is proposed: why"},
        },
        "required": ["companies"],
    },
}


def _plain(text: str) -> str:
    """A card line without its system labels ⟨…⟩."""
    return re.sub(r"\s*⟨[^⟩]*⟩\s*", " ", text).strip()


def earnings_steps(card: CardContent) -> dict[str, tuple[str, str]]:
    """The card's stated steps to earnings: sentence id (`s03.N`) -> (step, text). A market
    reaction and a step the source leaves UNKNOWN are no mechanism."""
    return {f"s03.{i}": (st.step, _plain(st.text)) for i, st in enumerate(card.s03_transmission)
            if st.step in EARNINGS_STEPS and not st.text.startswith("UNKNOWN")}


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
    sectors = "; ".join(f"{s.name} ({s.direction.value})" for s in av.sector_exposures)
    named = named_by_source(card)
    lines = [f"THESIS {h.thesis_id} (version {version}): {h.title}",
             f"Area: {area} · Geography: {h.region}",
             "Statement: " + " ".join(_plain(s.text) for s in card.s01_bottom_line),
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


def _same_name(a: str, b: str) -> bool:
    """One company spelt two ways ("Micron" / "Micron Technology"): one token list leads the
    other."""
    x, y = norm_name(a).split(), norm_name(b).split()
    n = min(len(x), len(y))
    return n > 0 and x[:n] == y[:n]


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
    cached = path.exists()
    usage: dict[str, int] | None = None
    seconds = 0.0
    if cached:
        rec = json.loads(path.read_text())
        out, usage = rec["output"], rec.get("usage")
    else:
        if client is None:
            raise RuntimeError("no cached enrichment for this thesis version and no LLM client "
                               "— run with ANTHROPIC_API_KEY set")
        t0 = time.monotonic()
        out = client.extract(system=SYSTEM, user=user, tool=TOOL)
        seconds = time.monotonic() - t0
        usage = getattr(client, "last_usage", None)
        path.parent.mkdir(parents=True, exist_ok=True)  # the paid answer is kept FIRST
        path.write_text(json.dumps({"model": model, "prompt_version": ENRICH_PROMPT_VERSION,
                                    "usage": usage, "output": out}, sort_keys=True, indent=1))
    named = named_by_source(card)
    refused: list[str] = []
    kept: list[EnrichmentCandidate] = []
    side_n = {Direction.POSITIVE: 0, Direction.NEGATIVE: 0}
    rows = out.get("companies") if isinstance(out, dict) else None
    for i, row in enumerate(rows if isinstance(rows, list) else []):
        if not isinstance(row, dict):
            refused.append(f"entry {i + 1}: not an object — set aside")
            continue
        name = str(row.get("name") or "").strip()
        sid = str(row.get("step_id") or "").strip()
        direction = {"benefit": Direction.POSITIVE, "hurt": Direction.NEGATIVE}.get(
            str(row.get("direction") or ""))
        why = ("no name" if not name else
               f"cites {sid or 'no step'}, not one of the card's steps to earnings "
               f"({', '.join(steps)})" if sid not in steps else
               "no direction (benefit or hurt)" if direction is None else
               "the source already names it" if any(_same_name(name, n) for n in named) else
               "proposed twice" if any(_same_name(name, k.name) for k in kept) else "")
        if not why and direction is not None and side_n[direction] >= PER_SIDE:
            why = f"more than {PER_SIDE} on one side"
        if why or direction is None:
            refused.append(f"{name or f'entry {i + 1}'}: {why} — set aside")
            continue
        side_n[direction] += 1
        business = str(row.get("business") or "").strip()
        exposure = str(row.get("exposure") or "").strip()
        ticker = str(row.get("ticker") or "").strip().upper() or None
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
        try:
            r = resolver.resolve(lookup, as_of=as_of)
            status, listings, registrant = r.status, r.listings, r.registrant
            rnote = r.note or r.method  # why — a refusal's reason sits in one or the other
            # a US line of a 20-F / 40-F filer (an ADR or a cross-listing): the resolver never
            # substitutes it for common equity; recorded as a fact, from the SEC's own data
            foreign = bool(status is ResolutionStatus.UNRESOLVED and r.cik
                           and resolver.is_foreign_private_issuer(r.cik, as_of=as_of))
        except HttpError as exc:  # the SEC could not be read: the name stays, unverified
            status, listings, registrant = ResolutionStatus.UNRESOLVED, (), None
            rnote = f"the SEC could not be read ({exc}) — not verified"
        kept.append(EnrichmentCandidate(
            enrichment_id="EC-" + hashlib.sha256(f"{tid}|{version}|{name}".encode())
            .hexdigest()[:14],
            thesis_id=tid, name=name, rationale=exposure, evidence=f"{sid}: {steps[sid][1]}",
            direction=direction, step_id=sid, business=business, ticker_hint=ticker,
            resolution_status=status, listings=listings, registrant=registrant,
            resolution_note=rnote, foreign_filer=foreign))
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
