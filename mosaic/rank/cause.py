"""Tier-3 — the LLM cause-classification **annotation channel**.

On-thesis work the machine can do that a human can't at 307-name scale: read the *textual* cause of
each de-rating (the 8-K / news) and classify it as a mean-revert candidate (guidance miss, one-time
charge, sentiment overreaction) vs a structural break (lost largest customer, regulatory kill-shot,
fraud). But it is an **annotation only**:

- It can DEMOTE a terminal-looking name; it is **never** the primary sort key. Structural metrics
  order the queue; this flag colours it.
- It is **never fabricated**. The default for every name is ``UNCLASSIFIED`` (no demotion). An LLM
  "score the best overshoots" is confident, fluent, unfalsifiable opinion — fenced here exactly as
  the assembler is fenced from rendering verdicts.

This module is the *channel*, not a runtime dependency of the ranker: the ranker consumes a plain
``{key -> CauseClass}`` map. That map is produced out-of-band by a separate LLM pass (this module's
:func:`classify_cause`) whose output is loaded via :func:`load_cause_annotations`. The live pass
needs the de-rating text (8-K body) wired onto events and an ``ANTHROPIC_API_KEY``; until then the
ranker simply runs with an empty map and every cause reads ``LLM: —``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mosaic.graph.llm import LlmClient
from mosaic.rank.profile import CauseClass

# Tool-use schema — force a validated label, not prose (mirrors the graph track's extractor).
CAUSE_TOOL: dict[str, Any] = {
    "name": "classify_derating_cause",
    "description": (
        "Classify the CAUSE of a stock's sharp de-rating from the filing/news text, for triage "
        "ONLY. You are NOT predicting returns and NOT deciding whether to buy — you label the "
        "nature of the cause so a human prioritises which names to analyse first."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "cause_class": {
                "type": "string",
                "enum": [CauseClass.MEAN_REVERT.value, CauseClass.STRUCTURAL_BREAK.value],
                "description": (
                    "mean_revert: a guidance miss, one-time charge, or apparent sentiment "
                    "overreaction — the kind of cause an overshoot is made of. "
                    "structural_break: lost largest customer, a regulatory kill-shot, fraud, or "
                    "other evidence the business itself is permanently impaired (terminal-looking)."
                ),
            },
            "rationale": {
                "type": "string",
                "description": "One sentence grounded in the text. Cite the specific cause.",
            },
        },
        "required": ["cause_class", "rationale"],
    },
}

_CAUSE_SYSTEM = (
    "You classify the cause of a sharp equity de-rating for research TRIAGE, not for a trade "
    "decision. Read only the supplied text. If the text does not clearly evidence a structural "
    "break, prefer mean_revert — a structural_break label DEMOTES the name, so only assert it on "
    "explicit evidence (named lost customer, regulatory action, restatement/fraud). Never "
    "speculate beyond the text."
)


def parse_cause_reply(raw: dict[str, Any]) -> CauseClass:
    """Map a validated tool reply to a :class:`CauseClass`. Unknown/garbled → ``UNCLASSIFIED``.

    Pure and total: an unrecognised label never raises and never fabricates a confident class — it
    falls back to the no-demotion default, honouring "annotation only, never fabricate".
    """
    value = str(raw.get("cause_class", "")).strip().lower()
    try:
        cls = CauseClass(value)
    except ValueError:
        return CauseClass.UNCLASSIFIED
    # The model may only assert the two real classes; UNCLASSIFIED is ours, not a model output.
    return cls if cls in (CauseClass.MEAN_REVERT, CauseClass.STRUCTURAL_BREAK) else (
        CauseClass.UNCLASSIFIED
    )


def classify_cause(llm: LlmClient, *, ticker: str, derate_text: str) -> CauseClass:
    """Classify one name's de-rating cause from its text. The live Tier-3 pass (run out-of-band).

    Empty text → ``UNCLASSIFIED`` (nothing to read, so nothing is asserted — never fabricate).
    """
    if not derate_text.strip():
        return CauseClass.UNCLASSIFIED
    user = f"Ticker {ticker}. De-rating text follows.\n\n{derate_text}"
    raw = llm.extract(system=_CAUSE_SYSTEM, user=user, tool=CAUSE_TOOL)
    return parse_cause_reply(raw)


def annotations_from_raw(raw: dict[str, str]) -> dict[str, CauseClass]:
    """Coerce a ``{key -> label-string}`` map (e.g. parsed JSON) to ``{key -> CauseClass}``.

    Unrecognised labels are dropped (not coerced to a real class) — a malformed annotation must not
    silently demote or boost a name.
    """
    out: dict[str, CauseClass] = {}
    for key, label in raw.items():
        try:
            cls = CauseClass(str(label).strip().lower())
        except ValueError:
            continue
        if cls in (CauseClass.MEAN_REVERT, CauseClass.STRUCTURAL_BREAK):
            out[key] = cls
    return out


def load_cause_annotations(path: Path) -> dict[str, CauseClass]:
    """Load a ``{ticker_or_internal_id -> "mean_revert"|"structural_break"}`` JSON annotation file.

    Absent file → empty map (the ranker then runs with no Tier-3 colour, the honest default). This
    is the seam a future LLM pass writes to; the ranker never calls the model itself.
    """
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        return {}
    return annotations_from_raw(raw)
