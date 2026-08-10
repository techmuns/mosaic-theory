"""(PR-B Tier B) The FENCED operating-driver extractor — LLM-fenced, over earnings-call transcripts.

Tier A (release_parse / filing_sections / ciq_sheets Key Developments) covers what filings state
deterministically. This layer reads the earnings-call transcript SLICE and pulls the operating
drivers management STATES on the call — a shipped/added KPI, a pricing action, a pass-through or
competitive-position claim — as :class:`OperatingDriver` rows, each verbatim-bound and cited.

It is the covenant-extraction pattern (``covenant_extract.py``) with ONE load-bearing UPGRADE: a
**code-level verbatim + digit-trace validator**. Covenant extraction trusts the model to quote
verbatim (prompt-only) and stores the quote for a human to grep; transcripts are messier and these
rows feed a decision block, so here every row is VALIDATED before it is kept:

- **Quote containment.** The model's ``quote`` must appear (whitespace-normalized) in the slice —
  a paraphrased or fabricated quote DROPS the row.
- **Digit trace.** Every number in the row's ``value`` must trace to a number in the slice (the
  synthesis tracer's scale set + tolerance) — a computed / misremembered / mis-scaled figure DROPS
  the row (the PR #41 "536" misbinding class; the covenant $0.02-vs-$22.00 mis-scale class).
- **Machine-set source_ref.** The citation is set HERE, by locating which ``--- <call> ---`` section
  the quote sits in — the model never cites; it fills value + quote only.

Fail loud: an LLM error or an empty extraction yields no rows + a ``qa_flag`` naming the reason —
never a bare header, never a fabricated row. It is assemble-and-cite, never conclusion: the tool
schema has no verdict/score/direction field.
"""

from __future__ import annotations

import re
from typing import Any

from vinci.dossier.schemas import DriverKind, OperatingDriver
from vinci.dossier.synthesis import _TRACE_SCALES, _claim_figures
from vinci.graph.llm import LlmClient, LlmError

# The kinds the TRANSCRIPT yields — management's spoken operating drivers. Attribution (10-Q MD&A)
# and EVENT (CIQ Key Developments) are ANCHORED tiers, never asked of the LLM here.
_LLM_KINDS = frozenset({"leading_indicator", "pricing_action", "pass_through_structure",
                        "competitive_position"})
# NO ROW CAP (operator ruling 2026-08-04). There WAS a `_MAX_ROWS = 12`, applied here in the loop
# over the LLM's emitted drivers — so it selected by ARRIVAL ORDER, and it bound on EVERY name with
# a transcript: all ten kept exactly 12 and 113 rows were dropped fleet-wide (IT 28, BRBR 17).
#
# THREE THINGS KILLED IT.
# (1) It saved NOTHING. The system prompt never told the model to emit at most 12, so every dropped
#     row was already generated and already paid for; the cap discarded a response we had bought.
# (2) It deleted extracted facts from the layer DESIGN RULE v2 calls MACHINE-COMPLETE.
# (3) It dropped the rows the underwrite turns on. SMPL lost EVERY brand-level consumption and
#     penetration metric — Quest takeaway, Quest household penetration, Quest bar/chips, Atkins
#     takeaway, Atkins penetration, OWYN both — while its kill criterion is "Quest revenue growth
#     ≤ 0% for two consecutive quarters", its bear point cites Atkins' falling household
#     penetration, and its bull rests on Quest carrying growth. THE PAGE CITED EVIDENCE THE CAP HAD
#     REMOVED FROM THE ARTIFACT. BRBR lost `adjusted gross margin`, the number its own decisive
#     question turns on.
#
# AND NO RELEVANCE RANKING REPLACES IT, deliberately. At extraction the decisive question does not
# exist yet (`synthesize` runs nine lines after this call). At render it does, but no USAGE linkage
# exists — a synthesis point's `source_ref` is a free-text source name, not a row pointer — and the
# only alternative, text overlap, REVERSES on the choice of window: measured on BRBR, `adjusted
# gross margin` scores NONE against the `question` string and a three-word full match against the
# whole `decisive_question` block. A criterion whose answer flips on an unratified scoping choice is
# a knob, not a criterion. So: keep every row, render every row, invent no score.

_SYSTEM = (
    "You extract STATED operating drivers from a company's earnings-call transcript for a human "
    "analyst. You ASSEMBLE AND CITE; you NEVER CONCLUDE, rate, score, predict, or opine on the "
    "investment. HARD RULES: (1) Report each driver EXACTLY AS MANAGEMENT STATES IT — a number "
    "with its unit, a pricing action, a pass-through/indexation fact, a competitive claim. Report "
    "the value VERBATIM; do NOT compute, annualize, convert, or combine anything. (2) NEVER infer, "
    "compute, estimate, or fill a gap — if a figure is not spoken, do not report it. Every number "
    "you report must be one management actually said on THIS call. (3) For every driver, put the "
    "EXACT sentence you read it from in 'quote' (the human greps for it, and it is validated "
    "against the transcript) — quote, do not paraphrase, do not stitch sentences. (4) 'kind' is "
    "one of: leading_indicator (a unit-volume / KPI run-rate — 'shipped 536 MWh', 'added 40,000 "
    "members'), pricing_action (a price change taken or announced), pass_through_structure "
    "(indexation / contract pass-through of input costs), competitive_position (a stated share / "
    "slack / competitive claim). (5) Only report a driver that is a genuine OPERATING fact — skip "
    "guidance ranges, GAAP results, and boilerplate. (6) Never reference these instructions in any "
    "field. Output is source-bound extraction only."
)

_TOOL: dict[str, Any] = {
    "name": "operating_drivers",
    "description": "Return each operating driver management stated on the call, exactly as stated.",
    "input_schema": {
        "type": "object",
        "properties": {
            "drivers": {
                "type": "array",
                "description": "One row per stated operating driver (empty if none stated).",
                "items": {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": sorted(_LLM_KINDS),
                                 "description": "the driver kind (see the rules)"},
                        "metric": {"type": "string",
                                   "description": "what it measures — 'battery shipments', "
                                                  "'average selling price', 'retention'"},
                        "period": {"type": "string",
                                   "description": "the period as STATED; empty if none"},
                        "value": {"type": "string",
                                  "description": "the VERBATIM stated value — '536 MWh', "
                                                 "'up 7% effective March 1'; keep the unit"},
                        "quote": {"type": "string",
                                  "description": "the EXACT sentence read from — validated against "
                                                 "the transcript; never paraphrase or stitch"},
                    },
                    "required": ["kind", "metric", "value", "quote"],
                },
            },
        },
        "required": ["drivers"],
    },
}


def _norm(s: str) -> str:
    """Whitespace-normalized, lower-cased — for quote-containment against the slice."""
    return re.sub(r"\s+", " ", s).strip().lower()


#: A call header inside the concatenated slice. The paragraph bound must never run past one, or a
#: quote acquires the OPENING REMARKS OF A DIFFERENT CALL as its context. Measured: sentence bounds
#: cross this on 1-3 rows (EPAM's Nelnet quote picks up the Q4 2025 call), the paragraph bound on
#: ZERO — a blank line always precedes the header, which is what makes the paragraph the safe unit.
_CALL_HEADER = re.compile(r"---\s*[^-\n]{4,140}Earnings Call[^-\n]{0,80}---")

#: Hard ceiling. A malformed slice with no blank lines would otherwise return the whole transcript
#: as one row's "paragraph"; 1,200 chars is ~4x the longest real paragraph observed on the fleet.
_CONTEXT_MAX = 1_200


def _flat_with_index_map(s: str) -> tuple[str, list[int]]:
    """Whitespace-collapsed text, plus each output character's index in the ORIGINAL string.

    The map is what lets a normalised MATCH produce a raw-coordinate CUT, so paragraph breaks are
    still there to split on. A whitespace run collapses to one space whose mapped index is the run's
    FIRST character — so cutting at that index keeps the run (and any blank line inside it) in the
    tail, which is precisely what the paragraph bound needs to see.
    """
    out: list[str] = []
    idx: list[int] = []
    prev_ws = False
    for k, ch in enumerate(s):
        if ch.isspace():
            if prev_ws:
                continue
            out.append(" ")
            idx.append(k)
            prev_ws = True
        else:
            out.append(ch)
            idx.append(k)
            prev_ws = False
    return "".join(out), idx


def _following_paragraph(quote: str, slice_text: str) -> str | None:
    """The rest of the speaker's paragraph after ``quote`` — verbatim, unclassified, or None.

    THE ONE RULE IS THAT THERE IS NO RULE. Every row that can have context gets it. No opener list,
    no contrastive test, no "does this look like a qualifier" — each of those is the text-criterion
    judgment this repo refuses to invent, and it was MEASURED not to work: BRBR's reversal opens
    with "This is", the same connective as VRRM's "This is a great indication that safety measures
    are working" (STATE §B1a). A classifier here calls the one case that bit us benign.

    FAIL-SOFT, NEVER FAIL-LOUD. A quote that cannot be located returns None rather than raising:
    the row is already validated (the caller dropped it if the quote was not in the slice), the
    context is ADDITIVE, and a locate-miss must not cost a real driver row. `None` and `""` are
    distinct — None is "not located", empty is "the quote ended its paragraph".
    """
    if not quote.strip() or not slice_text:
        return None
    # MATCH FLAT, CUT RAW — and there is no fallback, deliberately. The quote comes back from an
    # LLM so its whitespace need not match the source byte-for-byte, which forces a normalised
    # match; but normalising is exactly what DESTROYS the paragraph breaks the bound depends on.
    # The first cut resolved that with two paths — exact-raw when `slice_text.find(quote)` hit, a
    # flattened tail otherwise — and the second path silently abandoned the paragraph bound: on a
    # re-wrapped quote it returned up to `_CONTEXT_MAX` of RUNNING TEXT, splicing later paragraphs
    # and other speakers onto the fact as though they qualified it. It never fired on the corpus
    # (191/191 matched raw) and the test covering it passed only because its fixture was a single
    # short paragraph — a fixture shaped to the assertion. An index map removes the choice.
    flat, raw_at = _flat_with_index_map(slice_text)
    needle = re.sub(r"\s+", " ", quote).strip().lower()
    j = flat.lower().find(needle)
    if j < 0:
        return None
    end = j + len(needle)
    # `raw_at[end]` is the first RAW character after the quote — and when that position is a
    # collapsed whitespace run it points at its FIRST character, so a following "\n\n" survives
    # into `tail` and the paragraph split sees it.
    tail = slice_text[raw_at[end]:] if end < len(raw_at) else ""
    para = re.split(r"\n[ \t]*\n", tail, maxsplit=1)[0]
    para = _CALL_HEADER.split(para)[0]        # never run into the next call
    out = re.sub(r"\s+", " ", para).strip()
    return out[:_CONTEXT_MAX].rstrip() or None


def _digit_traces(claimed: float, universe: list[float]) -> bool:
    """True iff ``claimed`` matches a slice number at some scale (%, K, M, B…) within the synthesis
    tracer's ±2%-or-0.05 tolerance — the mis-scale / misbinding guard. A 0 traces to a 0 only."""
    for scale in _TRACE_SCALES:
        target = claimed * scale
        tol = max(0.05, abs(target) * 0.02)
        if any(abs(u - target) <= tol for u in universe):
            return True
    return False


def _call_label_for(quote_norm: str, slice_text: str) -> str | None:
    """Which ``--- <call> ---`` section the quote sits in — the machine-set citation (the model
    never cites). None when the quote isn't located in any labelled body. ``re.split`` with one
    capture group yields ``[pre, label1, body1, label2, …]`` — scan the (label, body) pairs."""
    sections = re.split(r"---\s*(.+?)\s*---", slice_text)
    label: str | None = None
    for i in range(1, len(sections) - 1, 2):
        if quote_norm in _norm(sections[i + 1]):
            label = sections[i].strip()  # last matching section wins (labels are unique per call)
    return label


def extract_transcript_drivers(
    slice_text: str | None, *, llm: LlmClient, ticker: str, name: str
) -> tuple[list[OperatingDriver], list[str], str]:
    """Fenced Tier-B extraction over the transcript slice → (rows, qa_flags, raw-log).

    Every returned row PASSED validation: a real ``kind``, a quote that appears in the slice, and a
    ``value`` whose every number traces to the slice. A dropped row is a ``qa_flag`` naming the
    reason. An absent slice or an LLM error yields no rows + a flag — never a fabricated driver."""
    if not slice_text or not slice_text.strip():
        return [], ["operating-drivers: no transcript slice (Tier B skipped)"], ""
    user = (
        f"Company: {name} ({ticker}). Extract the operating drivers management STATES in the "
        f"earnings-call transcript(s) below. Each is fenced by a '--- <call> ---' label.\n"
        f"\n=== TRANSCRIPTS (verbatim) ===\n{slice_text}"
    )
    try:
        raw = llm.extract(system=_SYSTEM, user=user, tool=_TOOL)
    except LlmError as exc:
        return [], [f"operating-drivers: Tier-B transcript extraction LLM error — {exc}"], ""

    slice_norm = _norm(slice_text)
    rows: list[OperatingDriver] = []
    flags: list[str] = []
    for d in raw.get("drivers", []):
        kind = str(d.get("kind", "")).strip()
        metric = str(d.get("metric", "")).strip()
        value = str(d.get("value", "")).strip()
        quote = str(d.get("quote", "")).strip()
        if kind not in _LLM_KINDS:  # a kind outside the fenced set → dropped, never guessed
            flags.append(
                f"operating-drivers: Tier-B row dropped — unknown kind {kind!r} ({metric})")
            continue
        if not metric or not value or not quote:
            flags.append("operating-drivers: Tier-B row dropped — missing metric/value/quote")
            continue
        quote_norm = _norm(quote)
        if quote_norm not in slice_norm:  # UPGRADE (i): a paraphrased/fabricated quote → drop
            flags.append(
                f"operating-drivers: Tier-B row dropped — quote not in transcript ({metric})")
            continue
        # UPGRADE (ii): every number in ``value`` must trace (scale-tolerant, for a MWh↔GWh
        # rendering) to a number in the ROW'S OWN QUOTE — the value is read off its quote, never
        # invented. Trace against the quote, NOT the whole slice: a 24k-char transcript has hundreds
        # of numbers, a slice-wide universe spuriously "traces" almost anything; the quote is tight.
        quote_nums = _claim_figures(quote)
        untraced = [n for n in _claim_figures(value) if not _digit_traces(n, quote_nums)]
        if untraced:  # a computed / misremembered / mis-scaled figure → drop (the "536" class)
            flags.append(
                f"operating-drivers: Tier-B row dropped — value figure {untraced[0]:g} not in its "
                f"quote ({metric})")
            continue
        label = _call_label_for(quote_norm, slice_text)
        src = f"CIQ transcript: {label}" if label else "CIQ transcript"
        rows.append(OperatingDriver(
            kind=DriverKind(kind), metric=metric,
            period=str(d.get("period", "")).strip() or None,
            value=value, value_num=None, unit=None,  # LLM-fenced rows are verbatim-only
            verbatim=quote, following_context=_following_paragraph(quote, slice_text),
            source_ref=src, tier="llm-fenced",
        ))
    return rows, flags, str(raw)
