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
_MAX_ROWS = 12  # depth-stage cost/space bound; the excess is flagged, never silently dropped

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
        if len(rows) >= _MAX_ROWS:
            flags.append(f"operating-drivers: Tier-B rows capped at {_MAX_ROWS} — {metric} dropped")
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
            verbatim=quote, source_ref=src, tier="llm-fenced",
        ))
    return rows, flags, str(raw)
