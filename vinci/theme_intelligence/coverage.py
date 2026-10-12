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
from dataclasses import dataclass
from typing import TYPE_CHECKING

from vinci.theme_intelligence.schemas import (
    BlockCheck,
    ClaimKind,
    CompletenessReport,
    EvidenceGroup,
    FigureCheck,
    MechanismCoverage,
    PropositionFate,
    SourceRiskFlag,
)
from vinci.theme_intelligence.verify import (
    content_words,
    norm_name,
    overlap,
    same_sentence_reread,
    sentences,
)

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


#: How a SOURCE states a DOWNSIDE to its own argument — read from the verbatim text, never from the
#: model. Constructions, not the bare word: "risk" is as often the argument itself ("the risks of
#: continued dependence on imported oil" is the energy-security case) or a list item ("chip-policy
#: risk"). Face validity (2026-10-12, Citi Gridlock): "a portion of announced capacity RISKS
#: REMAINING 'bragawatts'", "raw-material inflation … MIGHT PUT DOWNWARD PRESSURE on the IRR of ESS
#: projects", "demand … DID NOT MATERIALIZE", "EXECUTION RISK REMAINS", "POSE UNCERTAINTY". A bare
#: "could lead to" is not one ("could lead to a further boom in the U.S. midstream space", p3).
RISK_CUE = re.compile(
    r"\b(?:risks\s+\w+ing\b|risks?\s+(?:that|remains?|persists?)\b|"
    r"(?:there\s+is|poses?|posing|carr(?:y|ies))\s+(?:an?\s+|some\s+|the\s+)?(?:\w+\s+)?risk|"
    r"(?:increased|increasing|rising|higher|growing|significant|material|key|execution|"
    r"cancellation)\s+(?:\w+\s+)?risks?\b|risks?\s+to\s+(?:growth|demand|earnings|margins|our|the|"
    r"this)\b|expos\w*\s+(?:\w+\s+){0,4}to\s+(?:\w+\s+){0,2}risks?\b|"
    r"downward\s+pressure|headwinds?\b|(?:did|do|does|may|might|could|would)\s+not\s+"
    r"materiali[sz]e|(?:may|might|could|would)\s+(?:also\s+)?(?:put|delay|derail|reduce|weigh|"
    r"pressure|hurt|limit|slow|disrupt|undermine|erode|threaten)\b|overbuil[dt]|"
    r"oversupply|excess\s+capacity|pushback|cost\s+overruns?|"
    r"(?:creat|pos|bring|add|rais|introduc|lead)\w*\s+(?:to\s+)?(?:\w+\s+){0,3}uncertaint)",
    re.I)
#: a source that says a risk is ABSENT states no risk ("we see little risk of industry
#: oversupply through 2030") — never flagged
RISK_NEGATED = re.compile(
    r"\b(?:little|low|limited|minimal|no|negligible|few)\s+(?:\w+\s+){0,2}risks?\b|\bde-?risk",
    re.I)
#: a risk sentence is REPRESENTED by a proposed risk / counter-claim / linked evidence quote
#: sharing at least this share of its content words; a proposed risk is GROUNDED in a paragraph
#: (and represents every risk sentence of it — one paragraph argues one risk) when it cites a
#: claim of that paragraph or this share of its own words is in that paragraph
RISK_REPRESENTED = 0.5
#: a risk STATEMENT has at least this many words (a heading is not one)
RISK_MIN_WORDS = 8
#: a model-written line restates a source sentence when it shares at least this many content words
#: AND RISK_REPRESENTED of the SHORTER text's — a paraphrase is shorter than the sentence it
#: condenses ("Surging raw-material cost inflation (lithium, copper, aluminum) could pressure ESS
#: project IRRs and progress": 9 of its 13 words in Citi's 30-word sentence, 0.69 — 0.30 of the
#: sentence's). Evidence quotes are held to the sentence's own share: a quote may carry only the
#: figure, not the risk clause beside it.
RISK_SHARED_MIN = 4


def _restates(sentence: set[str], line: set[str]) -> bool:
    shared = len(sentence & line)
    return bool(sentence and line) and shared >= RISK_SHARED_MIN and (
        shared / min(len(sentence), len(line)) >= RISK_REPRESENTED)
#: a sentence ending without terminal punctuation was cut by a page or column break — listed for
#: review, never put on a card as if it were the source's whole statement
_COMPLETE = re.compile(r"[.!?…][\"”’')\]]*\s*$")


@dataclass(frozen=True)
class SourceRisk:
    """A risk the SOURCE states in its own words, in a readable argument paragraph."""
    block_id: str
    page: int | None
    sentence: str
    #: hypotheses whose verified evidence (or pass-1b account) is in the same paragraph
    related: tuple[str, ...]
    #: the proposed risk / counter-claim already carrying it, or ""
    represented_by: str
    #: the completeness pass judged the paragraph immaterial: its reason, or ""
    excluded: str
    #: cut by a page / column break (no terminal punctuation) — never put on a card
    fragment: bool = False

    @property
    def omitted(self) -> bool:
        return not self.represented_by and not self.excluded


def scan_source_risks(doc: ParsedDocument, ve: VerifiedExtraction,
                      report: CompletenessReport) -> list[SourceRisk]:
    """Every risk the source states in a readable ARGUMENT paragraph (the completeness ledger's)
    and whether a risk a model pass proposed, or a counter-claim, already carries it.
    Deterministic, from the verbatim text, BEFORE any thesis is applied — pipeline.py puts an
    omitted one on the cards of the hypotheses whose evidence shares ITS paragraph (`related`),
    as the source's opinion; never on every card."""
    claims = {c.claim_id: c for c in ve.verified_claims}
    known = [f"proposed risk: {r.raw.statement}" for r in ve.risks]
    known += [f"counter-evidence: {claims[c].quote}" for h in ve.hypotheses for c in h.counter
              if c in claims]
    # a card's ALTERNATIVE MECHANISM is in its 07 too (observed 2026-10-12: the cleaned Gridlock
    # run wrote raw-material inflation on ESS returns as one — not a market risk, still carried)
    known += [f"alternative mechanism on its card: {t.text}" for h in ve.hypotheses
              for t in h.raw.opposing_explanations]
    where: dict[str, set[str]] = {}
    carried: dict[str, list[str]] = {}  # paragraph -> quotes a hypothesis cites from it
    for h in ve.hypotheses:
        for c in (*h.supporting, *h.dislocation, *h.catalyst, *h.counter):
            if c in claims:
                where.setdefault(claims[c].block_id, set()).add(h.raw.local_id)
                carried.setdefault(claims[c].block_id, []).append(claims[c].quote)
    hyp_ids = {h.raw.local_id for h in ve.hypotheses}
    checks = {b.block_id: b for b in report.blocks}
    for bid, bc in checks.items():
        where.setdefault(bid, set()).update(i for i in bc.hypothesis_ids if i in hyp_ids)
    blocks = {b.block_id: b for b in doc.blocks}
    grounded: dict[str, str] = {}  # paragraph -> the proposed risk drawn from it
    for r in ve.risks:
        rw = content_words(r.raw.statement)
        for bid in report.argument_blocks:
            b = blocks.get(bid)
            if b is not None and bid not in grounded and (
                    any(claims[c].block_id == bid for c in r.claim_ids if c in claims)
                    or overlap(rw, content_words(b.text)) >= RISK_REPRESENTED):
                grounded[bid] = f"proposed risk drawn from this paragraph: {r.raw.statement}"
    out: list[SourceRisk] = []
    for bid in report.argument_blocks:
        b = blocks.get(bid)
        if b is None:
            continue
        for s in sentences(b.text):
            if (not RISK_CUE.search(s) or RISK_NEGATED.search(s)
                    or len(s.split()) < RISK_MIN_WORDS):
                continue
            words = content_words(s)
            rep = next((k for k in known if _restates(words, content_words(k.partition(": ")[2]))),
                       "")
            rep = rep or next((f"evidence on its card: {q}" for q in carried.get(bid, ())
                               if overlap(words, content_words(q)) >= RISK_REPRESENTED), "")
            rep = rep or grounded.get(bid, "")
            chk = checks.get(bid)
            out.append(SourceRisk(
                block_id=bid, page=b.page, sentence=s.strip(), related=tuple(sorted(where.get(
                    bid, ()))), represented_by=rep,
                excluded=chk.reason if chk is not None and chk.status == "immaterial" else "",
                fragment=not _COMPLETE.search(s.strip())))
    return out


def _risk_flags(found: Sequence[SourceRisk], destinations: dict[str, tuple[str, str]],
                store: Store) -> list[SourceRiskFlag]:
    out = []
    for r in found:
        tids = tuple(sorted({destinations[h][0] for h in r.related if h in destinations}))
        out.append(SourceRiskFlag(
            block_id=r.block_id, page=r.page, sentence=r.sentence,
            represented_by=r.represented_by, excluded=r.excluded, fragment=r.fragment,
            thesis_ids=tids if r.omitted and not r.fragment else (),
            thesis_titles=tuple(t.title for tid in tids if (t := store.thesis(tid)) is not None)
            if r.omitted and not r.fragment else ()))
    return out


def coverage_of(*, doc: ParsedDocument, merged: Merged, ve: VerifiedExtraction,
                report: CompletenessReport, destinations: dict[str, tuple[str, str]],
                lost: Sequence[tuple[str, LostItem]], store: Store,
                risks_found: Sequence[SourceRisk] = (),
                reverified: Sequence[str] = ()) -> MechanismCoverage:
    page = {b.block_id: b.page for b in doc.blocks}
    text = {b.block_id: b.text for b in doc.blocks}
    return MechanismCoverage(
        propositions=tuple(_propositions(merged, ve, destinations, lost)),
        uncarried=tuple(_uncarried(ve, report, destinations, page, store)),
        risks=tuple(_risks(merged, ve, destinations)),
        unrecorded_names=tuple(_names(ve, text, store)),
        source_risks=tuple(_risk_flags(risks_found, destinations, store)),
        reverified=tuple(reverified))


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
        if item.field == "hypotheses":  # pass 1's own answer (a salvaged extraction)
            lost_why = item.note or "the text is not valid JSON even after deletion-only repair"
            out.append(PropositionFate(
                hypothesis_id=item.local_id, title=item.title or "(no title in the malformed text)",
                fate="dropped",
                detail=(f"{label}: named in the answer's malformed hypotheses and not recoverable "
                        f"without guessing ({lost_why}) — its evidence was kept; REVIEW REQUIRED")))
            continue
        if item.field != "added_hypotheses":
            continue
        out.append(PropositionFate(
            hypothesis_id=item.local_id, title=item.title or "(no title in the malformed text)",
            fate="dropped",
            detail=(f"completeness part {label}: {item.note} — its evidence was kept (see the "
                    f"facts below for any no thesis carries)" if item.note else
                    f"named in completeness part {label}'s malformed {item.field} (not valid "
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
    written: dict[tuple[int | None, str], list[str]] = {}  # the source's figures, as written
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
        written.setdefault((page.get(c.block_id), status), []).append(
            c.value_text or c.statement)
        if reason and reason not in reasons:
            reasons.append(reason)
    return [EvidenceGroup(page=p, claim_ids=tuple(ids), status=s, reason="; ".join(rs)[:400],
                          figures=tuple(written[(p, s)]))
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
