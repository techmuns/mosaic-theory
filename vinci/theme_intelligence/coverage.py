"""Mechanism coverage — every economic proposition the source makes is accounted for.

WHY. On 2026-10-12 a cleaned re-analysis of Citi's Gridlock report kept, verified, the evidence of
"low-cost US natural gas gives the US a structural advantage" (page 37) — and no thesis carried it.
The figure / paragraph ledger could not see that: its figures were captured, its paragraph
anchored. The same run merged a fuel-cell share hypothesis into a gas-generation thesis because
both carried one identity key. Nothing flagged either.

Deterministic, after the thesis engine applied an article version — never a model call:

1. PROPOSITIONS — every hypothesis a model pass proposed (pass 1, pass 1b, and those a malformed
   answer NAMED but lost) ends ON A CARD, MERGED into one under the same identity key (stated,
   with how much evidence the two share — distinct evidence is an alert), or DROPPED with why.
2. EVIDENCE — verified MATERIAL facts (a figure, a forecast, an event, a measured metric) that no
   thesis links in any role and no market risk cites, grouped by page: EXCLUDED when the
   completeness pass judged that figure or paragraph immaterial (its reason), RELATED when pass 1b
   named a hypothesis for the paragraph, otherwise UNEXPLAINED — an alert for review.
3. RISKS — each market risk proposed: on which card(s), or dropped.
4. NAMES — organisations a CITED paragraph names in a list of examples ("across Renault, Volvo,
   Carwow and OLX") or as a dated source ("(CBRE, Feb 25)") that were never recorded — listed for
   review, never added automatically.

It never creates a card, never merges by similarity, and reads no prices or returns.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import TYPE_CHECKING

from vinci.theme_intelligence.schemas import (
    BlockCheck,
    ClaimKind,
    CompletenessReport,
    EvidenceGroup,
    FigureCheck,
    MechanismCoverage,
    PropositionFate,
)
from vinci.theme_intelligence.verify import norm_name, same_sentence_reread

if TYPE_CHECKING:
    from vinci.theme_intelligence.completeness import Merged
    from vinci.theme_intelligence.extract import LostItem
    from vinci.theme_intelligence.parse import ParsedDocument
    from vinci.theme_intelligence.store import Store
    from vinci.theme_intelligence.verify import VerifiedExtraction

MATERIAL_KINDS = frozenset({ClaimKind.METRIC, ClaimKind.FORECAST, ClaimKind.EVENT})

_NAME = r"[A-Z][A-Za-z0-9&.'’\-]*(?:\s+(?:of\s+)?[A-Z][A-Za-z0-9&.'’\-]*){0,3}"
_LIST = re.compile(rf"\b(?:across|including|such as|like|led by|among them)\s+"
                   rf"({_NAME}(?:\s*,\s*{_NAME})*(?:\s*,?\s+and\s+{_NAME})?)")
_MONTHS = ("Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|"
           "Sep|Sept|September|Oct|October|Nov|November|Dec|December")
_CITED = re.compile(rf"\(({_NAME}),\s*(?:{_MONTHS})\.?\s+\d{{1,2}}\)")
#: never an organisation: places, months, the publisher's own house names, unit / sector acronyms
_NOT_ORG = frozenset(n.lower() for n in (
    "U.S.", "US", "USA", "UK", "EU", "Europe", "European Union", "Asia", "APAC", "China", "India",
    "Japan", "Korea", "South Korea", "Taiwan", "Germany", "France", "Italy", "Spain", "Australia",
    "Brazil", "Mexico", "Canada", "Africa", "America", "North America", "Latin America",
    "Middle East", "Texas", "California", "Virginia", "Ohio", "Georgia", "Arizona", "Nevada",
    "Pennsylvania", "New York", "Illinois", "Indiana", "Louisiana", "Oklahoma", "Maryland",
    "North Carolina", "South Carolina", "Florida", "Utah", "Oregon", "Washington", "Iowa",
    "Wisconsin", "Michigan", "Tennessee", "Alabama", "Mississippi", "Colorado", "New Mexico",
    "Global", "AI", "EV", "EVs", "ESS",
    "GW", "MW", "LNG", "The", "This", "These", "That", "Those", "Figure", "Source", "Citi",
    "Citi Research", *(_MONTHS.split("|"))))


def coverage_of(*, doc: ParsedDocument, merged: Merged, ve: VerifiedExtraction,
                report: CompletenessReport, destinations: dict[str, tuple[str, str]],
                lost: Sequence[tuple[str, LostItem]], store: Store) -> MechanismCoverage:
    page = {b.block_id: b.page for b in doc.blocks}
    text = {b.block_id: b.text for b in doc.blocks}
    return MechanismCoverage(
        propositions=tuple(_propositions(merged, ve, destinations, lost)),
        uncarried=tuple(_uncarried(ve, report, destinations, page, store)),
        risks=tuple(_risks(merged, ve, destinations)),
        unrecorded_names=tuple(_names(ve, text, store)))


def _propositions(merged: Merged, ve: VerifiedExtraction, dest: dict[str, tuple[str, str]],
                  lost: Sequence[tuple[str, LostItem]]) -> list[PropositionFate]:
    out: list[PropositionFate] = []
    for h in merged.extraction.hypotheses:
        if h.local_id in dest:
            tid, how = dest[h.local_id]
            out.append(PropositionFate(hypothesis_id=h.local_id, title=h.title,
                                       fate="merged" if how.startswith("merged") else "card",
                                       thesis_id=tid, detail=how))
            continue
        why = [i for i in ve.issues if h.local_id in i.ref_id or f"{h.local_id}:" in i.detail]
        out.append(PropositionFate(
            hypothesis_id=h.local_id, title=h.title, fate="dropped",
            detail=(f"not verified ({why[0].code} — see the run's issues)" if why
                    else "not verified — no thesis was applied for it")))
    for label, item in lost:
        if item.field != "added_hypotheses":
            continue
        out.append(PropositionFate(
            hypothesis_id=item.local_id, title=item.title or "(no title in the malformed text)",
            fate="dropped",
            detail=(f"named in completeness part {label}'s malformed {item.field} (not valid "
                    f"JSON) — its evidence was kept; re-ask only that part: reask-part --part "
                    f"{label}")))
    return out


def _uncarried(ve: VerifiedExtraction, report: CompletenessReport,
               dest: dict[str, tuple[str, str]], page: dict[str, int | None],
               store: Store) -> list[EvidenceGroup]:
    material = [c for c in ve.verified_claims
                if c.value is not None or c.kind in MATERIAL_KINDS]
    linked = store.linked_claim_ids([c.claim_id for c in material])
    # a sentence an EARLIER version of this article already put on a card is carried by it
    # (a re-read keeps the earlier theses; verify.same_sentence_reread)
    if material:
        earlier = [c for c in store.claims_for_article(material[0].article_id)
                   if c.article_version_id != material[0].article_version_id]
        carried = store.linked_claim_ids([c.claim_id for c in earlier])
        held = [c for c in earlier if c.claim_id in carried]
        linked |= {c.claim_id for c in material
                   if any(same_sentence_reread(h, c) for h in held)}
    as_risk = {cid for r in ve.risks for cid in r.claim_ids}
    blocks: dict[str, BlockCheck] = {b.block_id: b for b in report.blocks}
    figures: dict[str, list[FigureCheck]] = {}
    for f in report.figures:
        figures.setdefault(f.block_id, []).append(f)
    groups: dict[tuple[int | None, str], tuple[list[str], list[str]]] = {}
    for c in material:
        if c.claim_id in linked or c.claim_id in as_risk:
            continue
        status, reason = "unexplained", ""
        bc = blocks.get(c.block_id)
        imm = [f for f in figures.get(c.block_id, [])
               if f.status == "immaterial" and f.figure.lower() in c.quote.lower()]
        if bc is not None and bc.status == "immaterial":
            status, reason = "excluded", f"paragraph judged immaterial: {bc.reason}"
        elif imm:
            status, reason = "excluded", f"figure {imm[0].figure!r} judged immaterial: " \
                                         f"{imm[0].reason}"
        elif bc is not None and bc.hypothesis_ids:
            tids = sorted({dest[h][0] for h in bc.hypothesis_ids if h in dest})
            if tids:
                status, reason = "related", f"pass 1b related its paragraph to {', '.join(tids)}"
        ids, reasons = groups.setdefault((page.get(c.block_id), status), ([], []))
        ids.append(c.claim_id)
        if reason and reason not in reasons:
            reasons.append(reason)
    return [EvidenceGroup(page=p, claim_ids=tuple(ids), status=s, reason="; ".join(rs)[:400])
            for (p, s), (ids, rs) in sorted(groups.items(), key=lambda kv: (kv[0][0] or 0,
                                                                              kv[0][1]))]


def _risks(merged: Merged, ve: VerifiedExtraction,
           dest: dict[str, tuple[str, str]]) -> list[str]:
    verified = {r.raw.statement: r for r in ve.risks}
    every = sorted({tid for tid, _ in dest.values()})
    out = []
    for r in merged.extraction.market_risks:
        v = verified.get(r.statement)
        if v is None:
            out.append(f"“{r.statement[:140]}” — dropped: not verified (its cited claims failed "
                       f"or were missing)")
            continue
        tids = sorted({dest[h][0] for h in v.related if h in dest}) if v.related else every
        out.append(f"“{r.statement[:140]}” — on {len(tids)} card(s): {', '.join(tids) or 'none'}")
    return out


def _names(ve: VerifiedExtraction, text: dict[str, str], store: Store) -> list[str]:
    """Organisations a CITED paragraph names that no mention records."""
    verified = list(ve.verified_claims)
    linked = store.linked_claim_ids([c.claim_id for c in verified])
    cited = sorted({c.block_id for c in verified if c.claim_id in linked})
    recorded = {norm_name(m.name_as_written) for m in ve.mentions}
    recorded_words = " ".join(sorted(recorded))
    out: list[str] = []
    seen: set[str] = set()
    for bid in cited:
        found: list[tuple[str, str]] = []
        for m in _LIST.finditer(text.get(bid, "")):
            found += [(n, "a list of examples") for n in re.split(r"\s*,\s*(?:and\s+)?|\s+and\s+",
                                                                  m.group(1))]
        found += [(m.group(1), "a dated source") for m in _CITED.finditer(text.get(bid, ""))]
        for name, how in found:
            name = re.split(r"[’']s\b", name)[0].strip(" .")  # "Siemens AG’s US" → "Siemens AG"
            key = norm_name(name)
            if (not name or name.lower() in _NOT_ORG or key in seen or key in recorded
                    or (len(key) > 3 and key in recorded_words)):
                continue
            seen.add(key)
            out.append(f"{name} ({how}, {bid})")
    return out
