"""The SYNTHESIS layer — the project's configured LLM, **fenced**.

The model is given ONLY the mechanical layer's source-bound facts (not the web, not its own memory),
and forced through a tool whose schema is the verdict-free :class:`Synthesis` shape — there is no
field for a conclusion, so it cannot render one. Its output is then validated, not trusted:

- every bull/bear point must cite a ``source_ref`` that exists in the input (uncited → flagged);
- every number must trace to a number present in the mechanical layer (untraceable → flagged);
- twin analogues must be source-bound or tagged ``[LLM-suggested, unverified]``, and never numeric;
- the whole output is linted for directional/recommendation language and flagged for human review.

The model + the full raw output are logged. The LLM never produces a number that feeds the spread —
the dossier writes nothing to the ledger.
"""

from __future__ import annotations

import json
import re
from typing import Any

from mosaic.dossier.schemas import (
    DecisiveQuestion,
    MechanicalLayer,
    SourcedPoint,
    Synthesis,
    TwinCase,
)
from mosaic.graph.llm import LlmClient, LlmError

_UNVERIFIED = "[LLM-suggested, unverified]"
# unit renderings an LLM uses for the same stored number (fraction↔%, raw↔K/M/B) — for number-trace
_TRACE_SCALES = (1.0, 1e2, 1e-2, 1e3, 1e-3, 1e6, 1e-6, 1e9, 1e-9)
_NUM = re.compile(r"-?\d[\d,]*\.?\d+|-?\d+")
# recommendation / verdict language — flagged for human review (the dossier frames, never concludes)
_DIRECTIONAL = re.compile(
    r"\b(buy|sell|overweight|underweight|recommend\w*|conviction|undervalued|overvalued|"
    r"price target|fair value|outperform|underperform|attractive entry|should (rise|recover|"
    r"rebound|outperform)|we (expect|believe|are confident))\b",
    re.IGNORECASE,
)
# a claim ABOUT data being absent — it must bind to that field's MISSING marker, not a present field
_MISSING_CLAIM = re.compile(
    r"\b(missing|unavailable|not (disclosed|available|provided|reported)|no .{0,15}data|"
    r"absent|undisclosed|MISSING|UNKNOWN)\b",
    re.IGNORECASE,
)

_POINT = {
    "type": "object",
    "properties": {
        "claim": {"type": "string", "description": "One sentence; must rest on a cited fact."},
        "source_ref": {
            "type": "string",
            "description": "Copy a source_ref VERBATIM from the supplied facts. No uncited claims.",
        },
    },
    "required": ["claim", "source_ref"],
}

SYNTHESIS_TOOL: dict[str, Any] = {
    "name": "assemble_dossier_framing",
    "description": (
        "Assemble the two readings of a sharply de-rated name FOR A HUMAN to adjudicate — "
        "you are NOT deciding, rating, scoring, or predicting. There is no field for a verdict "
        "because the conclusion is the human's. Use ONLY the supplied source-bound facts; cite a "
        "source_ref on every point; never invent a number or a fact not in the input."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "bull_points": {
                "type": "array",
                "items": _POINT,
                "description": "The exaggerated/TEMPORARY overshoot case (mean-revert).",
            },
            "bear_points": {
                "type": "array",
                "items": _POINT,
                "description": "The secular-and-TERMINAL decline case (value-trap reading).",
            },
            "twin_reference_cases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "A SPECIFIC named company."},
                        "outcome": {"type": "string", "description": "recovered / went terminal."},
                        "distinguishing_fact": {"type": "string"},
                        "source": {
                            "type": "string",
                            "description": f"A source_ref from input, or exactly '{_UNVERIFIED}'. "
                            "Never a recovery rate, base rate, or probability.",
                        },
                    },
                    "required": ["name", "outcome", "distinguishing_fact", "source"],
                },
                "description": "3-6 named analogues for reasoning. Never numeric/aggregate.",
            },
            "decisive_question": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The decisive variable."},
                    "evidence_for": {"type": "array", "items": _POINT},
                    "evidence_against": {"type": "array", "items": _POINT},
                },
                "required": ["question", "evidence_for", "evidence_against"],
                "description": "Surface the crux with evidence on each side. Do NOT answer it.",
            },
            "key_unknowns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "What the human must still resolve — esp. MISSING/UNKNOWN facts.",
            },
        },
        "required": [
            "bull_points", "bear_points", "twin_reference_cases", "decisive_question",
            "key_unknowns",
        ],
    },
}

_SYSTEM = (
    "You assemble a research dossier's framing for a human discriminator on a sharply de-rated US "
    "equity. You ASSEMBLE AND CITE; you NEVER CONCLUDE. Hard rules: (1) Use ONLY the source-bound "
    "facts in the user message — never your own memory, never the web; if a fact is MISSING "
    "or UNKNOWN, say so in key_unknowns, don't fill it. (2) Every bull/bear point and every "
    "piece of decisive-question evidence MUST copy a source_ref verbatim from the supplied facts. "
    "(3) Give both cases honestly: the overshoot/mean-revert reading AND the terminal/value-trap "
    "reading. (4) Twin reference cases must be SPECIFIC NAMED companies; tag each source as a real "
    "source_ref or exactly '[LLM-suggested, unverified]'; never a recovery rate, base rate, or "
    "probability — analogues are for reasoning, not stats. (5) Surface the decisive question; do "
    "NOT answer it. (6) Never recommend, rate, score, or predict a direction — there is nowhere to "
    "put a verdict and it is not your job."
)


def _refs_in(mech: MechanicalLayer) -> set[str]:
    """Every source_ref / accession / url present in the mechanical layer (the citable universe)."""
    refs: set[str] = set()

    def rec(o: Any) -> None:
        if isinstance(o, dict):
            if o.get("source_ref"):
                refs.add(str(o["source_ref"]))
            if o.get("accession"):
                refs.add(str(o["accession"]))
            if o.get("url"):
                refs.add(str(o["url"]))
            for v in o.values():
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)

    rec(mech.model_dump())
    return refs


def _present_refs(mech: MechanicalLayer) -> set[str]:
    """source_refs of PRESENT facts only (MISSING/UNKNOWN carry none) + filing accessions/urls."""
    refs: set[str] = set()

    def rec(o: Any) -> None:
        if isinstance(o, dict):
            if o.get("status") == "present" and o.get("source_ref"):
                refs.add(str(o["source_ref"]))
            if o.get("accession"):
                refs.add(str(o["accession"]))
            if o.get("url"):
                refs.add(str(o["url"]))
            for v in o.values():
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)

    rec(mech.model_dump())
    return refs


def _digit_strings(text: str) -> set[str]:
    return {m.group().replace(",", "").lstrip("-") for m in _NUM.finditer(text)}


def _floats(text: str) -> list[float]:
    out: list[float] = []
    for m in _NUM.finditer(text):
        try:
            out.append(float(m.group().replace(",", "")))
        except ValueError:
            continue
    return out


def _traces(ref: str, universe: set[str]) -> bool:
    return any(ref == u or ref in u or u in ref for u in universe)


def _validate(synth: Synthesis, mech: MechanicalLayer) -> tuple[Synthesis, list[str]]:
    """Apply the guardrails: cite-check, number-trace, twin checks, directional lint → flags."""
    flags: list[str] = []
    refs = _refs_in(mech)
    present_refs = _present_refs(mech)
    mech_nums = _floats(json.dumps(mech.model_dump(), default=str))

    def _num_traces(n: float) -> bool:
        # Trace by MAGNITUDE at any standard financial unit rendering (%, thousands, millions,
        # billions): the LLM writes the stored −0.726 as "−72.6%", 29,643,500 shares as "29.6
        # million", and a stored −0.027 as "shrunk by 2.7%" (sign carried in words, not the digit).
        # Direction is the directional-lint's job; this only asks whether the figure exists.
        a = abs(n)
        for mf in mech_nums:
            for s in _TRACE_SCALES:
                target = abs(mf) * s
                if abs(a - target) <= max(0.05, target * 0.02):
                    return True
        return False

    def check_point(p: SourcedPoint, where: str) -> SourcedPoint:
        cited = _traces(p.source_ref, refs)
        if not cited:
            flags.append(f"UNCITED {where}: '{p.claim[:70]}' (ref not in mechanical facts)")
        elif _MISSING_CLAIM.search(p.claim) and _traces(p.source_ref, present_refs):
            # a "field X is missing" claim must bind to X's MISSING marker (no source_ref), not to
            # an unrelated PRESENT field — such a claim belongs in key_unknowns, not here.
            cited = False
            flags.append(
                f"MISMATCH {where}: '{p.claim[:55]}' asserts missing/UNKNOWN data yet cites a "
                "PRESENT field — move to key_unknowns, don't source-bind it"
            )
        for n in _floats(p.claim):
            if not _num_traces(n):
                flags.append(f"UNTRACEABLE figure '{n:g}' in {where}: '{p.claim[:70]}'")
        return p.model_copy(update={"cited": cited})

    bull = [check_point(p, "bull_point") for p in synth.bull_points]
    bear = [check_point(p, "bear_point") for p in synth.bear_points]
    dq = synth.decisive_question
    dq = dq.model_copy(
        update={
            "evidence_for": [check_point(p, "decisive.for") for p in dq.evidence_for],
            "evidence_against": [check_point(p, "decisive.against") for p in dq.evidence_against],
        }
    )
    for tw in synth.twin_reference_cases:
        if tw.source != _UNVERIFIED and not _traces(tw.source, refs):
            flags.append(f"TWIN '{tw.name}' source doesn't trace — should be tagged unverified")
        numeric = _digit_strings(f"{tw.outcome} {tw.distinguishing_fact}")
        if numeric:
            flags.append(f"TWIN '{tw.name}' has numbers {sorted(numeric)} — must be non-numeric")
    blob = " ".join(
        [p.claim for p in [*bull, *bear, *dq.evidence_for, *dq.evidence_against]]
        + [dq.question, *synth.key_unknowns]
        + [f"{t.outcome} {t.distinguishing_fact}" for t in synth.twin_reference_cases]
    )
    for hit in {m.group(0).lower() for m in _DIRECTIONAL.finditer(blob)}:
        flags.append(f"DIRECTIONAL language '{hit}' — human review (dossier frames, not concludes)")

    validated = synth.model_copy(
        update={"bull_points": bull, "bear_points": bear, "decisive_question": dq}
    )
    return validated, flags


def _parse(raw: dict[str, Any]) -> Synthesis:
    def pts(items: Any) -> list[SourcedPoint]:
        return [
            SourcedPoint(claim=str(i.get("claim", "")), source_ref=str(i.get("source_ref", "")))
            for i in (items or [])
            if isinstance(i, dict)
        ]

    dq = raw.get("decisive_question") or {}
    twins = [
        TwinCase(
            name=str(t.get("name", "")), outcome=str(t.get("outcome", "")),
            distinguishing_fact=str(t.get("distinguishing_fact", "")),
            source=str(t.get("source", _UNVERIFIED)),
        )
        for t in (raw.get("twin_reference_cases") or [])
        if isinstance(t, dict)
    ]
    return Synthesis(
        bull_points=pts(raw.get("bull_points")),
        bear_points=pts(raw.get("bear_points")),
        twin_reference_cases=twins,
        decisive_question=DecisiveQuestion(
            question=str(dq.get("question", "")),
            evidence_for=pts(dq.get("evidence_for")),
            evidence_against=pts(dq.get("evidence_against")),
        ),
        key_unknowns=[str(u) for u in (raw.get("key_unknowns") or [])],
    )


def synthesize(
    mech: MechanicalLayer, *, llm: LlmClient, ticker: str, name: str, transcript: str | None = None
) -> tuple[Synthesis | None, list[str], str]:
    """Run the fenced synthesis → (synthesis|None, flags, log). Fail-loud, never fabricates. The
    ``transcript`` (a mechanically-bounded slice — NOT embedded in the dossier) is QUALITATIVE
    context only; no numbers are derived from it and points still bind to the mechanical facts."""
    facts = json.dumps(mech.model_dump(), indent=2, default=str)
    user = (
        f"Name: {name} ({ticker}). The ONLY facts you may use — each carries a source_ref to copy "
        f"verbatim when you cite it:\n\n{facts}"
    )
    if transcript:
        user += (
            "\n\n=== Earnings-call transcript (prepared remarks + Q&A, mechanically bounded) — "
            "QUALITATIVE context for management posture/tone ONLY. Derive NO numbers from it; any "
            "a point resting on it cites the 'CIQ transcript …' source_ref from the facts. ===\n"
            + transcript
        )
    log_parts = [f"model: {llm.model}", "", "=== SYSTEM ===", _SYSTEM, "", "=== USER ===", user]
    try:
        raw = llm.extract(system=_SYSTEM, user=user, tool=SYNTHESIS_TOOL)
    except LlmError as exc:
        log_parts += ["", "=== ERROR ===", str(exc)]
        return None, [f"LLM synthesis failed (no usable output): {exc}"], "\n".join(log_parts)
    log_parts += ["", "=== RAW OUTPUT ===", json.dumps(raw, indent=2, default=str)]
    # the tool marks all five fields required; a missing one means a truncated response — mark the
    # synthesis UNAVAILABLE rather than silently defaulting to a blank (indistinguishable from a
    # genuinely empty field). Defence-in-depth alongside the extract-level max_tokens guard.
    missing = [k for k in SYNTHESIS_TOOL["input_schema"]["required"] if k not in raw]
    if missing:
        note = f"synthesis tool returned incomplete output — missing required field(s) {missing}"
        log_parts += ["", "=== INCOMPLETE ===", note]
        flag = f"LLM synthesis UNAVAILABLE — {note} (likely truncated)"
        return None, [flag], "\n".join(log_parts)
    synth, flags = _validate(_parse(raw), mech)
    return synth, flags, "\n".join(log_parts)
