"""Pass 1b — WHOLE-ARTICLE completeness: a deterministic ledger, then an independent re-read.

WHY. Checking completeness against the claims the first model selected checks the model against
itself. The ledger here is built from the ARTICLE TEXT before any model output is consulted:
every figure a body block states, and every argument block. Then

1. COVERAGE (deterministic) — a figure is captured when a verified claim anchored in the same
   block quotes it; an argument block is anchored when a verified claim, mention or sector span
   sits in it.
2. PASS 1b (`run_completeness`) — a SEPARATE model call re-reads the full article with the pass-1
   record and the ledger's gaps beside it, and must account for each gap: add the missed claim /
   mention / hypothesis / market-regime record, attach evidence to an existing hypothesis, or mark
   the gap immaterial WITH A REASON. Its additions are merged (`merge_completeness`) and pass
   through the SAME deterministic verification as pass 1 — nothing it returns is trusted
   unverified.
3. THE REPORT (`build_report`) — every figure ends captured / added_by_completeness_pass /
   immaterial / uncaptured; every argument block anchored / covered / added / immaterial /
   unreviewed. An uncaptured figure or an unreviewed block is an OPEN issue: logged, shown in QA
   and on the dashboard, never hidden.

THE FIGURE SCAN reads numbers with their unit (%, bp, x, $/€/£/¥, million/bn…), ranges ("60–80"),
bare values ("an average of 41") and counted periods written in words ("seven straight quarters").
It skips what is not a reported figure: years, tenors ("200-day", "10-year"), numbers that are part
of a name ("S&P 500", "Mag 7"), days of a month, clock times and list numbering.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import Field, ValidationError

from vinci.graph.llm import LlmError
from vinci.theme_intelligence.config import (
    COMPLETE_PROMPT_VERSION,
    LLM_MODEL,
    PROMPT_CACHE_PARTS,
    Taxonomy,
)
from vinci.theme_intelligence.extract import (
    _X,
    Extraction,
    InvalidAnswerError,
    LostItem,
    ToolClient,
    XAffected,
    XClaim,
    XHypothesis,
    XMention,
    XRisk,
    XSector,
    _truncated,
    cache_key,
    cost_of,
    first_error,
    salvage_fields,
    system_prompt,
    tool_parts,
    validate_items,
)
from vinci.theme_intelligence.parse import GLYPH_CODE, ParsedDocument
from vinci.theme_intelligence.schemas import BlockCheck, CompletenessReport, FigureCheck
from vinci.theme_intelligence.verify import (
    VerifiedExtraction,
    content_words,
    in_hyphenated_name,
    norm_text,
)

#: Block kinds whose text is scanned for figures, and those that carry ARGUMENT text.
FIGURE_KINDS = frozenset({"paragraph", "list_item", "heading", "chart_title", "chart_description",
                          "other", "table"})  # a manual document's tables: every value counted
ARGUMENT_KINDS = frozenset({"paragraph", "list_item"})
#: An argument block has at least this many words (shorter paragraphs are labels / captions).
ARGUMENT_MIN_WORDS = 12

_MONTHS = ("january|february|march|april|may|june|july|august|september|october|november|"
           "december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec")
#: Units a figure carries, spaced or glued. Physical / compute units and the percentile ordinal
#: were added 2026-10-10: the ledger had missed "75GW", "930MW", "1.5GW" (42 figures of one
#: SemiAnalysis power post) and J.P. Morgan's "99th percentile" — a number glued to letters is
#: otherwise refused, which is what keeps "5G", "3D" and "B200" out.
_UNIT = (r"%|percent(?:age points?)?|per cent|basis points?|bps|bp|pp|x(?![a-z])|"
         r"(?:thousand|million|billion|trillion|mn|bn|tn)\b|"
         r"(?:[kmgt]wh?|[gtp]b|nm|[mg]hz|[gt]bps)\b|"
         r"(?:st|nd|rd|th)\s+percentile\b")
#: A scale letter GLUED to its number ("744B" parameters, "77K" tokens) — never spaced.
_GLUED_SCALE = r"[bkmt](?![a-z0-9])"
_NUMBER = re.compile(
    rf"(?P<cur>[$€£¥])?(?P<neg>(?<=[\s(~])-)?(?P<num>(?<![\w.,])\d+(?:[.,]\d+)*)"
    rf"(?:\s?(?:-|to)\s?(?P<num2>\d+(?:[.,]\d+)*))?"
    rf"(?P<unit>\s?(?:{_UNIT})|{_GLUED_SCALE})?(?![A-Za-z0-9])", re.I)
#: A number word, compound first ("twenty-four" is one number) — and a word figure may be a
#: range ("three-four months", "two to three years"), read whole like "60-80 basis points".
_NUM_WORD = (r"(?:(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)[-\s])?"
             r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
             r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|"
             r"dozen)")
_WORD_FIG = re.compile(
    rf"(?<![\w-])({_NUM_WORD}(?:\s?(?:-|–|to)\s?{_NUM_WORD})?)\s+"
    r"(?:(?:more|straight|consecutive|successive|additional|further)\s+)?"
    r"(quarters|years|months|weeks|days|hikes|cuts|times|points)\b", re.I)
_TENOR = re.compile(r"^-(?:day|week|month|year|quarter|yr|mo)s?\b", re.I)
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9“\"(])")


@dataclass(frozen=True)
class Figure:
    figure_id: str
    block_id: str
    text: str  # as written, e.g. "~43%", "60-80 basis points", "seven straight quarters"
    core: str  # what a covering quote must contain, normalised (e.g. "43%", "11.2")
    sentence: str


@dataclass
class Ledger:
    figures: list[Figure]
    argument_blocks: list[str]


def _sentence_at(text: str, pos: int) -> str:
    start = 0
    for m in _SENT.finditer(text):
        if m.start() >= pos:
            return text[start:m.start()].strip()
        start = m.end()
    return text[start:].strip()


def _skip_number(text: str, m: re.Match[str]) -> bool:
    num, unit, cur = m.group("num"), m.group("unit"), m.group("cur")
    if text[max(0, m.start("num") - 5):m.start("num")].lower() == "(cid:":
        return True  # a glyph code's number — undecodable font output, never a figure
    if in_hyphenated_name(text, m.start("num")):
        return True  # part of a name: "GLM-5.3", "COVID-19", "S-1"
    after = text[m.end():]
    before = text[:m.start()].rstrip()
    if unit or cur:
        return False
    if re.fullmatch(r"(19|20)\d{2}", num) and (
            not m.group("num2") or re.fullmatch(r"(19|20)?\d{2}", m.group("num2"))):
        return True  # a year, or a range of years ("2023-2024")
    if re.fullmatch(r"\d{2}", num) and re.search(r"['’]$", text[:m.start()]):
        return True  # an abbreviated year ("Dec '23")
    if _TENOR.match(after) or re.match(r"^:\d", after):
        return True  # "200-day", "10-year", a clock time
    if re.search(rf"\b(?:{_MONTHS})\.?$", before, re.I) or \
            re.match(rf"^\s*(?:{_MONTHS})\b", after, re.I):
        return True  # a day of a month
    prev = re.search(r"([A-Za-z&][\w&.'-]*)[\s-]?$", before)
    if prev and (prev.group(1)[0].isupper() or "&" in prev.group(1)) and "." not in num:
        return True  # part of a name: "S&P 500", "Mag 7", "Russell 2000", "GPT-5"
    if before.endswith("(") and after.startswith(")") and len(num) <= 2:
        return True  # an inline enumeration marker: "demand (1) registration …, (2) …"
    return bool(not before and re.match(r"^[.)]", after))  # list numbering "1." / "2)"


def _core(m: re.Match[str]) -> str:
    num = ("-" if m.group("neg") else "") + m.group("num")
    if m.group("num2"):
        num = f"{num}-{m.group('num2')}"
    unit = (m.group("unit") or "").strip().lower()
    if unit in ("%", "percent", "per cent"):
        return f"{num}%"
    return num


def scan_article(doc: ParsedDocument) -> Ledger:
    """Every figure and argument block of the BODY, read from the text alone."""
    figures: list[Figure] = []
    args: list[str] = []
    for b in doc.blocks:
        text = norm_text(b.text)
        if b.kind in ARGUMENT_KINDS and len(GLYPH_CODE.sub(" ", text).split()) \
                >= ARGUMENT_MIN_WORDS:  # glyph codes are no argument's words
            args.append(b.block_id)
        if b.kind not in FIGURE_KINDS:
            continue
        seen: set[str] = set()
        for m in _NUMBER.finditer(text):
            if _skip_number(text, m):
                continue
            core = _core(m)
            if core in seen:
                continue
            seen.add(core)
            lo = m.start() - (1 if m.start() > 0 and text[m.start() - 1] in "~≈" else 0)
            figures.append(Figure(f"{b.block_id}#{core}", b.block_id,
                                  text[lo:m.end()].strip(), core,
                                  _sentence_at(text, m.start())))
        for m in _WORD_FIG.finditer(text):
            core = m.group(0).lower()
            if core in seen:
                continue
            seen.add(core)
            figures.append(Figure(f"{b.block_id}#{core}", b.block_id, m.group(0), core,
                                  _sentence_at(text, m.start())))
    return Ledger(figures=figures, argument_blocks=args)


def _figure_re(core: str) -> re.Pattern[str]:
    sign = core.startswith("-")
    body = core[1:] if sign else core
    pat = re.escape(body).replace(r"\-", r"\s?(?:-|to)\s?")
    if body.endswith("%"):
        pat = pat[:-1] + r"\s?(?:%|percent|per cent)"
    # a signed figure needs its minus; an unsigned one must not be the tail of " -10%"
    lead = r"(?<![\d.,])-\s?" if sign else r"(?<![\d.,])(?<!\s-)"
    return re.compile(lead + pat + r"(?![\d])")


def quote_covers(quote: str, core: str) -> bool:
    q = norm_text(quote).lower()
    if not re.search(r"\d", core):  # a counted period in words: every word must be there
        return all(w in q for w in core.split() if w not in ("more", "straight", "consecutive"))
    return _figure_re(core).search(q) is not None


#: how many words either side of a figure say what it measures ("supply deficit of 30%"). Three,
#: not five: at five the SUBJECT both facts share ("power transformers") vouches for a different
#: MEASURE ("prices … 80% higher" / "imports … 80% of supply").
_CONTEXT_WORDS = 3


def _beside(text: str, core: str) -> set[str]:
    """The content words within `_CONTEXT_WORDS` words of every occurrence of the figure — a unit
    glued to it ("50-GW+", "2,358.5GVA", "~$400") is part of the figure, not a word beside it."""
    t = norm_text(text).lower()
    near: list[str] = []
    for m in _figure_re(core).finditer(t):
        before, after = re.sub(r"\S+$", "", t[:m.start()]), re.sub(r"^\S+", "", t[m.end():])
        near += before.split()[-_CONTEXT_WORDS:] + after.split()[:_CONTEXT_WORDS]
    return {w for w in content_words(" ".join(near)) if w.isalpha()}


def _precise(text: str, core: str) -> str | None:
    """The figure written in full with what it counts — "2,358.5gva", "2,358 days" — when it has
    four or more digits (too precise to recur by coincidence); else None."""
    body = core.lstrip("-").rstrip("%")
    m = re.search(r"(?<![\d.,])(" + re.escape(body) + r"(?:[.,]\d+)*)(\S*)(?:\s+(\w+))?",
                  norm_text(text).lower())
    if m is None or sum(ch.isdigit() for ch in m.group(1)) < 4:
        return None
    return m.group(1) + (m.group(2) or " " + (m.group(3) or ""))


def states_figure(quote: str, f: Figure) -> bool:
    """A claim quoted from ANOTHER block states this figure: its quote covers the figure, and the
    words BESIDE the figure share a content word in both ("deficit" — "a supply deficit of 30%" /
    "an assumed 30% deficit"), or both write the same precise number in full with the same unit
    ("2,358.5GVA"). A shared number is not identity, nor is a word shared somewhere in a long
    sentence: the Citi Gridlock infographic reads "Power Transformers … Prices are about 80%
    higher", and "80% of U.S. power transformer supply" (imports) shares "power" with it — a
    different fact (observed 2026-10-11)."""
    if not quote_covers(quote, f.core):
        return False
    if _beside(f.sentence, f.core) & _beside(quote, f.core):
        return True
    full = _precise(f.sentence, f.core)
    return full is not None and full == _precise(quote, f.core)


# --- pass 1b: the independent re-read ----------------------------------------------------------

class XFigureReview(_X):
    figure_id: str
    verdict: str  # captured_by_added_claim | immaterial
    claim_ids: list[str] = Field(default_factory=list)
    reason: str = ""


class XBlockReview(_X):
    block_id: str
    verdict: str  # covered | added | immaterial
    hypothesis_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    reason: str = ""


class XHypothesisAddition(_X):
    hypothesis_id: str
    supporting_claim_ids: list[str] = Field(default_factory=list)
    dislocation_claim_ids: list[str] = Field(default_factory=list)
    counter_claim_ids: list[str] = Field(default_factory=list)
    catalyst_claim_ids: list[str] = Field(default_factory=list)
    affected_mentions: list[XAffected] = Field(default_factory=list)
    sector_exposures: list[XSector] = Field(default_factory=list)


class CompletenessOutput(_X):
    figure_reviews: list[XFigureReview] = Field(default_factory=list)
    block_reviews: list[XBlockReview] = Field(default_factory=list)
    added_claims: list[XClaim] = Field(default_factory=list)
    added_mentions: list[XMention] = Field(default_factory=list)
    hypothesis_additions: list[XHypothesisAddition] = Field(default_factory=list)
    added_hypotheses: list[XHypothesis] = Field(default_factory=list)
    added_risks: list[XRisk] = Field(default_factory=list)


def completeness_tool(taxonomy: Taxonomy) -> dict[str, Any]:
    parts = tool_parts(taxonomy)
    ids = {"type": "array", "items": {"type": "string"}}
    addition = {
        "type": "object",
        "properties": {
            "hypothesis_id": {"type": "string", "description": "a first-pass hypothesis id (h…)"},
            "supporting_claim_ids": ids, "dislocation_claim_ids": ids, "counter_claim_ids": ids,
            "catalyst_claim_ids": ids,
            "affected_mentions": parts["hypothesis"]["properties"]["affected_mentions"],
            "sector_exposures": {"type": "array", "items": parts["sector"]},
        },
        "required": ["hypothesis_id", "supporting_claim_ids", "dislocation_claim_ids",
                     "counter_claim_ids", "catalyst_claim_ids", "affected_mentions",
                     "sector_exposures"],
    }
    return {
        "name": "record_completeness",
        "description": "Account for every gap in the first pass: add what it missed, or mark a "
                       "gap immaterial with a reason.",
        "input_schema": {
            "type": "object",
            "properties": {
                "figure_reviews": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "figure_id": {"type": "string"},
                        "verdict": {"type": "string",
                                    "enum": ["captured_by_added_claim", "immaterial"]},
                        "claim_ids": ids, "reason": {"type": "string"}},
                    "required": ["figure_id", "verdict", "claim_ids", "reason"]}},
                "block_reviews": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "block_id": {"type": "string"},
                        "verdict": {"type": "string", "enum": ["covered", "added", "immaterial"]},
                        "hypothesis_ids": ids, "claim_ids": ids, "reason": {"type": "string"}},
                    "required": ["block_id", "verdict", "hypothesis_ids", "claim_ids",
                                 "reason"]}},
                "added_claims": {"type": "array", "items": parts["claim"]},
                "added_mentions": {"type": "array", "items": parts["mention"]},
                "hypothesis_additions": {"type": "array", "items": addition},
                "added_hypotheses": {"type": "array", "items": parts["hypothesis"]},
                "added_risks": {"type": "array", "items": parts["risk"]},
            },
            "required": ["figure_reviews", "block_reviews", "added_claims", "added_mentions",
                         "hypothesis_additions", "added_hypotheses", "added_risks"],
        },
    }


def completeness_system(taxonomy: Taxonomy) -> str:
    return """You are the SECOND, independent reader of ONE article for an equity-research triage \
registry. A first pass already recorded claims, named entities, hypotheses (investment theses and \
market-regime records) and market risks. You get its record and a DETERMINISTIC LEDGER built from \
the article text: every figure the article states and every argument paragraph, with what the \
first pass did NOT capture marked. Your job is COMPLETENESS, not repetition. Answer only by \
calling record_completeness.

1. FIGURES — for EVERY figure marked NOT CAPTURED: add a claim that captures it (one figure per \
claim, exact quote) and give verdict captured_by_added_claim with its claim id(s), or verdict \
immaterial with a SPECIFIC reason (e.g. "historical chart range shown only as context"). A figure \
the article uses to make its argument is material.
2. ARGUMENT BLOCKS — for EVERY block marked UNANCHORED: verdict covered (name the hypothesis ids \
whose argument it states), added (you added the claims / hypothesis it needs — name them), or \
immaterial with a reason.
3. ARGUMENTS — re-read the whole article. If it makes a material argument no first-pass \
hypothesis or market risk carries, add it: an investable mechanism as an investment_thesis; a \
market-structure condition from which the article draws a research OPPORTUNITY (e.g. dispersion \
making sector or thematic selection matter) as a market_regime record, even when it names no \
company; a market-structure condition presented as a RISK (concentration, a correlation that \
could cause a simultaneous drawdown) as an added_risk — a risk is never a record. Never duplicate \
a first-pass hypothesis or risk: attach new evidence to a hypothesis with hypothesis_additions \
instead.
4. ENTITIES — add every organization the article names that the first pass missed; never one it \
does not name.
5. New claim local ids start with k (k1, k2 …), new hypothesis ids with hx (hx1 …). You may cite \
first-pass claim ids (c…) in your additions. Leave a list empty when there is nothing to add.

Claims, mentions, hypotheses and risks follow EXACTLY the first pass's rules, repeated here:

""" + system_prompt(taxonomy)


#: One pass-1b call accounts for at most this many gaps (uncaptured figures + unanchored
#: paragraphs). A longer list is split into consecutive PARTS in article order, one call each, so a
#: long article is reviewed IN FULL instead of overrunning the output cap (observed 2026-10-10:
#: 124 figures + 91 paragraphs of a SemiAnalysis post truncated a single call at 21,333 tokens).
GAPS_PER_CALL = 50


@dataclass(frozen=True)
class Batch:
    """One part of a split completeness review: its gaps, in article order."""
    label: str  # "1", "2" …; a part that overran the cap is split ONCE into "2a" / "2b"
    gaps: tuple[tuple[str, str], ...]  # ("f", figure_id) | ("b", block_id)

    @property
    def figures(self) -> frozenset[str]:
        return frozenset(i for k, i in self.gaps if k == "f")

    @property
    def blocks(self) -> frozenset[str]:
        return frozenset(i for k, i in self.gaps if k == "b")

    def halves(self) -> list[Batch]:
        n = len(self.gaps) // 2
        return [Batch(self.label + "a", self.gaps[:n]), Batch(self.label + "b", self.gaps[n:])]


def completeness_message(doc: ParsedDocument, x: Extraction, ledger: Ledger,
                         captured: dict[str, list[str]], anchored: dict[str, list[str]], *,
                         publisher: str, as_of: str, batch: Batch | None = None) -> str:
    lines = [f"Publisher: {publisher}", f"Title: {doc.title or 'UNKNOWN'}",
             f"Published: {doc.published_raw or 'UNKNOWN'}",
             f"Analysis as-of date: {as_of} (do not use any knowledge of events after it)",
             "<untrusted_article>"]
    lines += [f"[{b.block_id}|{b.kind}] {b.text}" for b in doc.blocks]
    lines += ["</untrusted_article>", "<first_pass_record>", "Claims:"]
    for c in x.claims:
        val = f" (value {c.value_text} {c.unit or ''})" if c.value_text else ""
        lines.append(f"- {c.local_id} [{c.block_id}] {c.quote!r}{val}")
    lines.append("Named entities: " + ("; ".join(f"{m.name_as_written} ({m.role.value})"
                                                 for m in x.mentions) or "none"))
    lines.append("Hypotheses:")
    for h in x.hypotheses:
        lines.append(f"- {h.local_id} [{h.kind.value}] {h.title} — {h.value_chain_node}|"
                     f"{h.mechanism}|{h.direction.value} — supporting "
                     f"{', '.join(h.supporting_claim_ids) or 'none'}")
    lines.append("Market risks: " + ("; ".join(r.statement for r in x.market_risks) or "none"))
    lines.append("</first_pass_record>")
    if batch is not None:
        nf = sum(1 for f in batch.figures if not captured.get(f))
        nb = sum(1 for k in batch.blocks if not anchored.get(k))
        lines.append(
            f"<batch>This article's open gaps do not fit one answer, so the review is split into "
            f"parts. This is part {batch.label}: account for EVERY one of the {nf} uncaptured "
            f"figure(s) and {nb} unanchored paragraph(s) listed below; the article's other gaps "
            f"belong to other parts and are not listed. The record above already includes what "
            f"earlier parts added (ids beginning b): never duplicate it — attach new evidence to "
            f"it with hypothesis_additions. Number new claims k{batch.label}_1, "
            f"k{batch.label}_2 … and new hypotheses hx{batch.label}_1 ….</batch>")
    lines.append("<figure_ledger>")
    for f in ledger.figures:
        got = captured.get(f.figure_id)
        if batch is not None and (got or f.figure_id not in batch.figures):
            continue
        lines.append(f"- {f.figure_id} [{f.block_id}] {f.text!r} — "
                     + (f"captured by {', '.join(got)}" if got else "NOT CAPTURED")
                     + f" — sentence: {f.sentence[:220]!r}")
    lines += ["</figure_ledger>", "<argument_blocks>"]
    for bid in ledger.argument_blocks:
        got = anchored.get(bid)
        if batch is not None and (got or bid not in batch.blocks):
            continue
        lines.append(f"- {bid}: " + (f"anchored by {', '.join(got)}" if got else "UNANCHORED"))
    lines.append("</argument_blocks>")
    return "\n".join(lines)


def open_gaps(doc: ParsedDocument, ledger: Ledger, captured: dict[str, list[str]],
              anchored: dict[str, list[str]]) -> tuple[tuple[str, str], ...]:
    """Every uncaptured figure and unanchored argument paragraph, in article order."""
    order = {b.block_id: i for i, b in enumerate(doc.blocks)}
    gaps = [(order.get(f.block_id, 0), 0, "f", f.figure_id) for f in ledger.figures
            if not captured.get(f.figure_id)]
    gaps += [(order.get(b, 0), 1, "b", b) for b in ledger.argument_blocks if not anchored.get(b)]
    return tuple((g[2], g[3]) for g in sorted(gaps))


def batches(gaps: tuple[tuple[str, str], ...]) -> list[Batch | None]:
    """[None] (one call over the full ledger) when the gaps fit one call; else consecutive parts
    of GAPS_PER_CALL gaps each."""
    if len(gaps) <= GAPS_PER_CALL:
        return [None]
    return [Batch(str(i // GAPS_PER_CALL + 1), gaps[i:i + GAPS_PER_CALL])
            for i in range(0, len(gaps), GAPS_PER_CALL)]


def _own_reviews(out: CompletenessOutput, b: Batch) -> tuple[CompletenessOutput, list[str]]:
    """A part reviews ITS gaps only; a verdict on a gap it was not shown is ignored, and said so
    (the claims it cites are kept — coverage is re-derived from verified claims anyway)."""
    off = [f"figure_reviews: {r.figure_id} is not a gap of this part — verdict ignored"
           for r in out.figure_reviews if r.figure_id not in b.figures]
    off += [f"block_reviews: {r.block_id} is not a gap of this part — verdict ignored"
            for r in out.block_reviews if r.block_id not in b.blocks]
    return out.model_copy(update={
        "figure_reviews": [r for r in out.figure_reviews if r.figure_id in b.figures],
        "block_reviews": [r for r in out.block_reviews if r.block_id in b.blocks]}), off


def _concat(outs: list[CompletenessOutput]) -> CompletenessOutput:
    if len(outs) == 1:
        return outs[0]
    return CompletenessOutput(**{name: [item for o in outs for item in getattr(o, name)]
                                 for name in CompletenessOutput.model_fields})


def _prefixed(out: CompletenessOutput, p: str) -> CompletenessOutput:
    """One batch's local ids made unique across batches (and every reference remapped), whether or
    not the model followed the prefix instruction."""
    cm = {c.local_id: p + c.local_id for c in out.added_claims}
    hm = {h.local_id: p + h.local_id for h in out.added_hypotheses}

    def ren(ids: list[str]) -> list[str]:
        return [cm.get(i, i) for i in ids]

    def hren(ids: list[str]) -> list[str]:
        return [hm.get(i, i) for i in ids]

    return out.model_copy(update={
        "figure_reviews": [r.model_copy(update={"claim_ids": ren(r.claim_ids)})
                           for r in out.figure_reviews],
        "block_reviews": [r.model_copy(update={"claim_ids": ren(r.claim_ids),
                                               "hypothesis_ids": hren(r.hypothesis_ids)})
                          for r in out.block_reviews],
        "added_claims": [c.model_copy(update={"local_id": cm[c.local_id]})
                         for c in out.added_claims],
        "added_mentions": [m.model_copy(update={"claim_ids": ren(m.claim_ids)})
                           for m in out.added_mentions],
        "hypothesis_additions": [a.model_copy(update={
            "hypothesis_id": hm.get(a.hypothesis_id, a.hypothesis_id),
            "supporting_claim_ids": ren(a.supporting_claim_ids),
            "dislocation_claim_ids": ren(a.dislocation_claim_ids),
            "counter_claim_ids": ren(a.counter_claim_ids),
            "catalyst_claim_ids": ren(a.catalyst_claim_ids),
            "sector_exposures": [s.model_copy(update={"claim_ids": ren(s.claim_ids)})
                                 for s in a.sector_exposures]})
            for a in out.hypothesis_additions],
        "added_hypotheses": [_remap_hyp(h.model_copy(update={"local_id": hm[h.local_id]}), cm)
                             for h in out.added_hypotheses],
        "added_risks": [r.model_copy(update={"claim_ids": ren(r.claim_ids),
                                             "related_hypothesis_ids":
                                                 hren(r.related_hypothesis_ids)})
                        for r in out.added_risks]})


def first_pass_coverage(doc: ParsedDocument, x: Extraction,
                        ledger: Ledger) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """What the first pass's QUOTES cover, before verification (for the pass-1b message only —
    the report re-derives coverage from VERIFIED claims)."""
    texts = {b.block_id: b.text for b in doc.blocks}
    captured: dict[str, list[str]] = {}
    for f in ledger.figures:
        captured[f.figure_id] = [c.local_id for c in x.claims if c.block_id == f.block_id
                                 and c.quote in texts.get(c.block_id, "")
                                 and quote_covers(c.quote, f.core)]
    anchored: dict[str, list[str]] = {}
    for bid in ledger.argument_blocks:
        anchored[bid] = [c.local_id for c in x.claims if c.block_id == bid]
        anchored[bid] += [m.name_as_written for m in x.mentions if m.block_id == bid]
    return captured, anchored


@dataclass
class CompletenessCall:
    label: str  # "" for a single call; the part label otherwise
    usage: dict[str, int] | None
    cost_usd: float | None
    seconds: float
    cached: bool
    truncated: bool = False  # billed and discarded: the part was split and re-asked
    kept_as: str = ""  # a re-asked answer: the file it was kept in, beside the paid original


@dataclass
class CompletenessResult:
    output: CompletenessOutput
    raw: dict[str, Any]
    cached: bool
    usage: dict[str, int] | None
    cost_usd: float | None
    seconds: float
    model: str
    prompt_version: str = COMPLETE_PROMPT_VERSION
    calls: list[CompletenessCall] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)  # how the review was split, if it was
    #: (part label, item) a malformed field NAMED and lost — for the coverage report
    lost: list[tuple[str, LostItem]] = field(default_factory=list)


def run_completeness(doc: ParsedDocument, x: Extraction, ledger: Ledger, *, publisher: str,
                     as_of: str, taxonomy: Taxonomy, client: ToolClient | None,
                     cache_dir: Path, reask: str | None = None,
                     reask_client: ToolClient | None = None) -> CompletenessResult:
    """Pass 1b — one call, or, when the open gaps exceed GAPS_PER_CALL, consecutive PARTS. Each
    later part is shown what the earlier parts added (so it extends rather than duplicates them)
    and skipped if they already covered its gaps. A part that overruns the output cap is split
    ONCE into halves (the discarded call is recorded with its cost); a half that overruns again
    fails loud. Every call is cached by content; the paid answer is written before it is
    validated, item by item.

    An answer whose TOP level fails is recovered FIELD BY FIELD (`salvage_fields`): only the
    malformed field is lost, with its exact error. Such a part is NOT shown to later parts: what
    a later part sees is then fixed by answers already paid for, so a replay — or a re-ask of
    only that part (`reask-part`) — sends every other request byte-identical and pays for none
    of them again. Its content still joins the result and is verified like any other.

    `reask` (with `reask_client`; the `reask-part` command): send the IDENTICAL request of that
    one part again — only when its cached answer fails as a whole — and keep the new answer
    beside the original (`<key>.reask-N.json`). Every other part must come from the cache (no
    `client`), which is also the proof the requests were reproduced exactly."""
    if reask is not None:  # the whole chain must reproduce from the cache BEFORE anything is sent
        run_completeness(doc, x, ledger, publisher=publisher, as_of=as_of, taxonomy=taxonomy,
                         client=None, cache_dir=cache_dir)
    captured, anchored = first_pass_coverage(doc, x, ledger)
    tool = completeness_tool(taxonomy)
    system = completeness_system(taxonomy)
    model = client.model if client is not None else LLM_MODEL
    gaps = open_gaps(doc, ledger, captured, anchored)
    queue = batches(gaps)
    notes = ([] if queue == [None] else
             [f"{len(gaps)} open gaps after pass 1 (figures not captured + argument paragraphs "
              f"not anchored) exceed one call's {GAPS_PER_CALL} — reviewed in {len(queue)} parts"])
    outputs: list[CompletenessOutput] = []  # the parts LATER parts are shown (see below)
    final: list[CompletenessOutput] = []  # every part's usable content, in article order
    raws: list[dict[str, Any]] = []
    calls: list[CompletenessCall] = []
    dropped: list[str] = []
    lost: list[tuple[str, LostItem]] = []
    reask_done = False
    while queue:
        b = queue.pop(0)
        xk, cap, anc = x, captured, anchored
        if b is not None and outputs:  # a later part sees what the earlier parts added
            xk = merge_completeness(x, _concat(outputs)).extraction
            cap, anc = first_pass_coverage(doc, xk, ledger)
            if all(cap.get(i) for i in b.figures) and all(anc.get(i) for i in b.blocks):
                notes.append(f"part {b.label}: every gap was covered by an earlier part's "
                             f"additions — not asked")
                continue
        label = "" if b is None else b.label
        user = completeness_message(doc, xk, ledger, cap, anc, publisher=publisher,
                                    as_of=as_of, batch=b)
        key = cache_key(model, COMPLETE_PROMPT_VERSION, tool, system, user)
        path = cache_dir / "complete" / f"{key}.json"
        marker = cache_dir / "complete" / f"{key}.truncated.json"
        splittable = b is None or b.label.isdigit()  # a half ("2a") is never split again
        whole = b if b is not None else Batch("1", gaps)
        if path.exists():
            rec = json.loads(path.read_text())
            out = rec["output"]
            calls.append(CompletenessCall(label, rec.get("usage"), 0.0, 0.0, True))
            if reask is not None and label == reask:
                calls.append(_reask(path, out, label, reask_client, model=model, system=system,
                                    user=user, tool=tool))
                reask_done = True
        elif marker.exists() and splittable:  # known to overrun: split without paying again
            notes.append(_split_note(label, json.loads(marker.read_text()).get("usage")))
            queue[:0] = whole.halves()
            continue
        else:
            if client is None:
                raise RuntimeError("no cached completeness pass for this article version and no "
                                   "LLM client")
            t0 = time.monotonic()
            try:
                # a part of a split review resends the article: cache it (llm.py)
                out = client.extract(system=system, user=user, tool=tool,
                                     cache=PROMPT_CACHE_PARTS and b is not None)
            except LlmError as exc:
                if not (_truncated(exc) and splittable):
                    raise
                usage = getattr(client, "last_usage", None)
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.write_text(json.dumps({"model": model, "usage": usage, "error": str(exc),
                                              "prompt_version": COMPLETE_PROMPT_VERSION},
                                             sort_keys=True, indent=1))
                calls.append(CompletenessCall(label, usage, cost_of(model, usage),
                                              time.monotonic() - t0, False, truncated=True))
                notes.append(_split_note(label, usage))
                queue[:0] = whole.halves()
                continue
            seconds = time.monotonic() - t0
            usage = getattr(client, "last_usage", None)
            path.parent.mkdir(parents=True, exist_ok=True)  # the paid answer is kept FIRST
            path.write_text(json.dumps({"model": model, "prompt_version": COMPLETE_PROMPT_VERSION,
                                        "usage": usage, "seconds": seconds, "output": out},
                                       sort_keys=True, indent=1))
            calls.append(CompletenessCall(label, usage, cost_of(model, usage), seconds, False))
        what = f"part {b.label}" if b is not None else "the completeness answer"
        whole_ok = True
        try:
            parsed, bad = validate_items(CompletenessOutput, out)
        except ValidationError as exc:
            # FIELD BY FIELD: a malformed field costs that field, never the whole paid answer.
            # The answer stays in the cache as paid (audit); a re-asked answer, when the operator
            # paid for one (`reask-part`), sits beside it and is used instead.
            whole_ok = False
            asked = latest_reask(path)
            src = out if asked is None else json.loads(asked.read_text())["output"]
            try:
                parsed, bad, gone = salvage_fields(CompletenessOutput, src)
            except ValidationError as exc2:
                last = calls[-1]
                if b is None:  # the single call: the pass did not run; its cost is recorded
                    raise InvalidAnswerError("completeness pass", exc2,
                                             usages=[] if last.cached else [last.usage],
                                             model=model,
                                             prompt_version=COMPLETE_PROMPT_VERSION) from exc2
                dropped.append(f"part {b.label}: the whole answer dropped — "
                               f"{first_error(exc2)}; its {len(b.gaps)} gaps stay open")
                continue
            bad = [f"the answer failed as a whole ({first_error(exc)}) — "
                   + (f"the re-asked answer {asked.name} is used; the paid original is kept"
                      if asked is not None else "recovered field by field") + ":"] + bad
            notes.append(
                f"{what}: recovered {_tally(parsed)}"
                + (f" from the re-asked answer {asked.name}" if asked is not None
                   else " field by field from its malformed answer")
                + " — not shown to later parts, so their requests stay exactly as paid; "
                  "re-ask only this part with `reask-part`")
            if asked is not None:  # what the PAID original named and the re-ask did not again
                try:
                    _p, _b, gone0 = salvage_fields(CompletenessOutput, out)
                except ValidationError:
                    gone0 = []
                again = {h.local_id for h in parsed.added_hypotheses}
                gone += [LostItem(g.field, g.local_id, g.title,
                                  note=f"named by the paid answer (malformed); its re-ask "
                                       f"({asked.stem.rsplit('.', 1)[-1]}) did not propose it "
                                       f"again")
                         for g in gone0 if g.local_id not in again]
            lost += [(label, g) for g in gone]
        if b is not None:
            parsed, off = _own_reviews(parsed, b)
            parsed = _prefixed(parsed, f"b{b.label}.")
            bad += off
        dropped += [f"part {b.label}: {d}" if b else d for d in bad]
        if whole_ok:
            outputs.append(parsed)
        final.append(parsed)
        raws.append(out)
    if reask is not None and not reask_done:
        raise RuntimeError(f"no completeness part {reask!r} with a cached answer — parts: "
                           f"{', '.join(c.label or '(single)' for c in calls) or 'none'}")
    if not final:
        raise RuntimeError("the completeness pass produced no answer")
    usage_sum: dict[str, int] = {}
    for c in calls:
        for k, v in (c.usage or {}).items():
            if k != "max_tokens":
                usage_sum[k] = usage_sum.get(k, 0) + int(v)
    costs = [c.cost_usd for c in calls]
    return CompletenessResult(
        _concat(final), raws[0] if len(raws) == 1 and len(calls) == 1 else {"parts": raws},
        all(c.cached for c in calls), usage_sum or None,
        None if any(c is None for c in costs) else sum(c or 0.0 for c in costs),
        sum(c.seconds for c in calls), model, calls=calls, dropped=dropped, notes=notes,
        lost=lost)


def _reask(path: Path, out: Any, label: str, client: ToolClient | None, *, model: str,
           system: str, user: str, tool: dict[str, Any]) -> CompletenessCall:
    """Send one part's identical request again; keep the answer beside the paid original."""
    try:
        validate_items(CompletenessOutput, out)
    except ValidationError:
        pass
    else:
        raise RuntimeError(f"part {label}: its answer is valid as a whole — nothing to re-ask")
    if client is None:
        raise RuntimeError("re-asking a part needs an LLM client")
    t0 = time.monotonic()
    new = client.extract(system=system, user=user, tool=tool)
    seconds = time.monotonic() - t0
    usage = getattr(client, "last_usage", None)
    n = 1
    while (dest := path.with_name(f"{path.stem}.reask-{n}.json")).exists():
        n += 1
    dest.write_text(json.dumps({"model": model, "prompt_version": COMPLETE_PROMPT_VERSION,
                                "usage": usage, "seconds": seconds, "output": new,
                                "reask_of": path.name}, sort_keys=True, indent=1))
    return CompletenessCall(label, usage, cost_of(model, usage), seconds, False,
                            kept_as=str(dest))


def latest_reask(path: Path) -> Path | None:
    """The newest re-asked answer kept beside a cached part answer (`<key>.reask-N.json`, written
    by `reask-part`), or None. The original paid answer is never overwritten."""
    found = sorted(path.parent.glob(f"{path.stem}.reask-*.json"),
                   key=lambda p: int(p.stem.rsplit("-", 1)[1]))
    return found[-1] if found else None


def _tally(out: CompletenessOutput) -> str:
    return (f"{len(out.added_claims)} claim(s), {len(out.added_mentions)} mention(s), "
            f"{len(out.added_risks)} risk(s), {len(out.added_hypotheses)} hypothesis(-es), "
            f"{len(out.hypothesis_additions)} addition(s) to hypotheses, "
            f"{len(out.figure_reviews)} figure and {len(out.block_reviews)} paragraph review(s)")


def _split_note(label: str, usage: dict[str, int] | None) -> str:
    what = f"part {label}" if label else "the single completeness call"
    return (f"{what} overran the output cap ({(usage or {}).get('output_tokens')} output tokens, "
            f"billed and discarded) — split once into halves, each asked separately")


# --- merge and report --------------------------------------------------------------------------

@dataclass
class Merged:
    extraction: Extraction
    pass1_claims: set[str]  # local claim ids from pass 1
    pass1b_claims: set[str]  # local claim ids added by pass 1b (after any renaming)
    pass1b_mentions: set[str]  # lower-cased names added by pass 1b
    pass1b_hypotheses: set[str]
    renamed: dict[str, str] = field(default_factory=dict)
    #: pass-1b items that could not be applied (an addition naming no hypothesis) — reported
    dropped: list[str] = field(default_factory=list)


def _ren(ids: list[str], m: dict[str, str]) -> list[str]:
    return [m.get(i, i) for i in ids]


def merge_completeness(x: Extraction, c: CompletenessOutput | None) -> Merged:
    """Pass-1b additions folded into the pass-1 extraction. A colliding local id is renamed (never
    silently overwritten) and every reference to it is remapped."""
    p1 = {cl.local_id for cl in x.claims}
    if c is None:
        return Merged(x, p1, set(), set(), set())
    taken = set(p1)
    m: dict[str, str] = {}
    for cl in c.added_claims:
        if cl.local_id in taken:
            n = 1
            while f"k{n}_{cl.local_id}" in taken:
                n += 1
            m[cl.local_id] = f"k{n}_{cl.local_id}"
        taken.add(m.get(cl.local_id, cl.local_id))
    claims = list(x.claims) + [cl.model_copy(update={"local_id": m.get(cl.local_id,
                                                                         cl.local_id)})
                               for cl in c.added_claims]
    hyps = {h.local_id: h for h in x.hypotheses}
    hm: dict[str, str] = {}
    for h in c.added_hypotheses:
        if h.local_id in hyps or h.local_id in hm.values():
            hm[h.local_id] = f"{h.local_id}_b"
    added_h = [_remap_hyp(h.model_copy(update={"local_id": hm.get(h.local_id, h.local_id)}), m)
               for h in c.added_hypotheses]
    hyps.update({h.local_id: h for h in added_h})  # an addition may extend a pass-1b record too
    dropped: list[str] = []
    for a in c.hypothesis_additions:
        h0 = hyps.get(a.hypothesis_id)
        if h0 is None:
            dropped.append(f"hypothesis_additions: {a.hypothesis_id!r} names no hypothesis of "
                           f"this article — not attached (its claims stay recorded as claims)")
            continue
        hyps[a.hypothesis_id] = h0.model_copy(update={
            "supporting_claim_ids": _uniq(h0.supporting_claim_ids
                                          + _ren(a.supporting_claim_ids, m)),
            "dislocation_claim_ids": _uniq(h0.dislocation_claim_ids
                                           + _ren(a.dislocation_claim_ids, m)),
            "counter_claim_ids": _uniq(h0.counter_claim_ids + _ren(a.counter_claim_ids, m)),
            "catalyst": h0.catalyst.model_copy(update={"claim_ids": _uniq(
                h0.catalyst.claim_ids + _ren(a.catalyst_claim_ids, m))}),
            "affected_mentions": h0.affected_mentions + [
                am for am in a.affected_mentions if am not in h0.affected_mentions],
            "sector_exposures": h0.sector_exposures + [
                s.model_copy(update={"claim_ids": _ren(s.claim_ids, m)})
                for s in a.sector_exposures]})
    added_ids = {h.local_id for h in added_h}
    mentions = list(x.mentions)
    have = {(mm.name_as_written.lower(), mm.role) for mm in mentions}
    new_names: set[str] = set()
    for mm in c.added_mentions:
        if (mm.name_as_written.lower(), mm.role) not in have:
            mentions.append(mm.model_copy(update={"claim_ids": _ren(mm.claim_ids, m)}))
            have.add((mm.name_as_written.lower(), mm.role))
            new_names.add(mm.name_as_written.lower())
    risks = list(x.market_risks) + [
        r.model_copy(update={"claim_ids": _ren(r.claim_ids, m),
                             "related_hypothesis_ids": [hm.get(i, i)
                                                        for i in r.related_hypothesis_ids]})
        for r in c.added_risks]
    merged = x.model_copy(update={"claims": claims, "mentions": mentions,
                                  "hypotheses": list(hyps.values()), "market_risks": risks})
    return Merged(merged, p1, {m.get(cl.local_id, cl.local_id) for cl in c.added_claims},
                  new_names, added_ids, renamed=m, dropped=dropped)


def _uniq(ids: list[str]) -> list[str]:
    return list(dict.fromkeys(ids))


def _remap_hyp(h: XHypothesis, m: dict[str, str]) -> XHypothesis:
    if not m:
        return h

    def t(x: Any) -> Any:
        return x.model_copy(update={"claim_ids": _ren(x.claim_ids, m)}) if x is not None else x

    return h.model_copy(update={
        "supporting_claim_ids": _ren(h.supporting_claim_ids, m),
        "strongest_evidence_claim_ids": _ren(h.strongest_evidence_claim_ids, m),
        "dislocation_claim_ids": _ren(h.dislocation_claim_ids, m),
        "counter_claim_ids": _ren(h.counter_claim_ids, m),
        "catalyst": t(h.catalyst), "bottom_line_fact": t(h.bottom_line_fact),
        "bottom_line_inference": t(h.bottom_line_inference),
        "source_implication": t(h.source_implication), "near_term_view": t(h.near_term_view),
        "structural_view": t(h.structural_view),
        "opposing_explanations": [t(o) for o in h.opposing_explanations],
        "transmission_chain": [t(s) for s in h.transmission_chain],
        "sector_exposures": [t(s) for s in h.sector_exposures],
        "cited_baskets": [t(b) for b in h.cited_baskets]})


def build_report(*, ledger: Ledger, ve: VerifiedExtraction, merged: Merged,
                 output: CompletenessOutput | None, article_version_id: str, run_id: str,
                 pass_ran: bool, note: str = "") -> CompletenessReport:
    """Coverage re-derived from VERIFIED records, then the pass-1b verdicts for what is left.
    Every gap left OPEN states its cause (`open_cause`), so an open gap is never mistaken for an
    unexamined one — and never for a verified one."""
    local_of: dict[str, list[str]] = {}
    for lid, gid in ve.claim_map.items():
        local_of.setdefault(gid, []).append(lid)
    verified = ve.verified_claims

    def linked(local_ids: list[str]) -> list[str]:
        """The VERIFIED global claims a pass-1b account names (its local ids, renumbered by the
        merge) — a claim that failed verification is never linked, so it cannot vouch."""
        return _uniq([g for i in local_ids
                      if (g := ve.claim_map.get(merged.renamed.get(i, i))) is not None])

    fig_reviews = {r.figure_id: r for r in (output.figure_reviews if output else [])}
    by_id = {c.claim_id: c for c in verified}
    figures: list[FigureCheck] = []
    for f in ledger.figures:
        cov = [c for c in verified if c.block_id == f.block_id and quote_covers(c.quote, f.core)]
        p1 = [c.claim_id for c in cov if set(local_of.get(c.claim_id, [])) & merged.pass1_claims]
        p1b = [c.claim_id for c in cov
               if set(local_of.get(c.claim_id, [])) & merged.pass1b_claims]
        rv = fig_reviews.get(f.figure_id)
        # a figure RESTATED (a chart caption, a table, a summary) is captured where the article
        # states it — when pass 1b names that claim AND the claim verifiably states this figure
        named = ([g for g in linked(rv.claim_ids)
                  if g in by_id and states_figure(by_id[g].quote, f)]
                 if rv is not None and rv.verdict == "captured_by_added_claim" else [])
        cause = ""
        if p1:
            status, ids, reason = "captured", p1, ""
        elif p1b:
            status, ids, reason = "added_by_completeness_pass", p1b, ""
        elif rv is not None and rv.verdict == "immaterial" and rv.reason.strip():
            status, ids, reason = "immaterial", [], rv.reason.strip()
        elif named:
            first = any(set(local_of.get(g, [])) & merged.pass1_claims for g in named)
            homes = ", ".join(_uniq([by_id[g].block_id for g in named]))
            status, ids = ("captured" if first else "added_by_completeness_pass"), named
            reason = (f"restated here; captured where the article states it ({homes}: "
                      f"{', '.join(named)})")
        else:
            status, ids = "uncaptured", []
            # a claim quoting the figure exists but failed verification (its number or span):
            # it stays out of every thesis, so the figure stays open
            failed = [c.claim_id for c in ve.claims if c.block_id == f.block_id
                      and c.claim_id not in local_of and quote_covers(c.quote, f.core)]
            if not pass_ran:
                cause, reason = "pass_not_run", "the completeness pass did not run"
            elif failed:
                cause = "verification_failed"
                reason = (f"a claim quotes it ({', '.join(failed)}) but failed verification, so "
                          f"it is never used as evidence")
            elif rv is not None and rv.verdict == "captured_by_added_claim":
                cause, reason = ("capture_not_verified",
                                 "pass 1b claimed a capturing claim, but none verified")
            else:
                cause, reason = ("no_account", "no verified claim quotes it and no immaterial "
                                               "verdict was given")
        figures.append(FigureCheck(block_id=f.block_id, figure=f.text, sentence=f.sentence[:240],
                                   status=status, claim_ids=tuple(ids), reason=reason,
                                   open_cause=cause))
    anchored_blocks = {c.block_id for c in verified} | {m.block_id for m in ve.mentions}
    for h in ve.hypotheses:
        anchored_blocks |= {s.block_id for s in h.sectors}
    blk_reviews = {r.block_id: r for r in (output.block_reviews if output else [])}
    hyp_ids = {h.raw.local_id for h in ve.hypotheses}
    blocks: list[BlockCheck] = []
    for bid in ledger.argument_blocks:
        rv2 = blk_reviews.get(bid)
        hids = [i for i in rv2.hypothesis_ids if i in hyp_ids] if rv2 is not None else []
        cids = linked(rv2.claim_ids) if rv2 is not None else []
        if bid in anchored_blocks:
            blocks.append(BlockCheck(block_id=bid, status="anchored"))
        elif rv2 is not None and rv2.verdict == "immaterial" and rv2.reason.strip():
            blocks.append(BlockCheck(block_id=bid, status="immaterial", reason=rv2.reason.strip()))
        elif rv2 is not None and (hids or cids):
            # an account is CHECKABLE when it names a verified hypothesis or verified claim
            blocks.append(BlockCheck(block_id=bid, status="covered" if rv2.verdict == "covered"
                                     else "added",
                                     hypothesis_ids=tuple(hids), claim_ids=tuple(cids),
                                     reason=rv2.reason.strip()))
        elif not pass_ran:
            blocks.append(BlockCheck(block_id=bid, status="unreviewed",
                                     reason="the completeness pass did not run",
                                     open_cause="pass_not_run"))
        elif rv2 is not None:
            blocks.append(BlockCheck(
                block_id=bid, status="unreviewed", open_cause="account_names_no_record",
                reason=(f"pass 1b called it {rv2.verdict} — "
                        f"{rv2.reason.strip() or 'no reason given'!r} — but named no verified "
                        f"claim or hypothesis, so the account cannot be checked")))
        else:
            blocks.append(BlockCheck(
                block_id=bid, status="unreviewed", open_cause="no_account",
                reason="no verified claim sits in it and pass 1b gave no account of it"))
    without = tuple(b for b in ledger.argument_blocks if b not in anchored_blocks)
    added_mentions = sum(1 for mm in ve.mentions
                         if mm.name_as_written.lower() in merged.pass1b_mentions)
    added_hyps = sum(1 for h in ve.hypotheses if h.raw.local_id in merged.pass1b_hypotheses)
    added_claims = sum(1 for c in verified
                       if set(local_of.get(c.claim_id, [])) & merged.pass1b_claims)
    return CompletenessReport(
        article_version_id=article_version_id, run_id=run_id, figures=tuple(figures),
        argument_blocks=tuple(ledger.argument_blocks), blocks_without_claims=without,
        added_claims=added_claims, added_mentions=added_mentions, added_hypotheses=added_hyps,
        added_risks=len(output.added_risks) if output else 0,
        prompt_version=COMPLETE_PROMPT_VERSION if pass_ran else "not-run",
        created_at=datetime.now(tz=UTC), blocks=tuple(blocks), pass_ran=pass_ran, note=note)
