"""Prose units — what a fidelity metric scores, for a draw and for a gold claim alike.

A DRAW's units are #920 §4's: each bull/bear claim, each key unknown, the decisive question and each
piece of its evidence, each twin's ``distinguishing_fact``, and ``evidence_balance``. A
``source_ref`` or ``figures`` entry is never a unit — a source_ref quotes row labels ("…Charges")
and cell coordinates, which are the facts, not a reading of them.

A GOLD claim is one unit, as coded. The decisive-question claim was coded as the whole question
object (stored as a JSON object); its prose is the question and each evidence claim, with the
source_refs dropped for the same reason.
"""
from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from typing import Any

from vinci.dossier.synthesis import _decode_escapes


@dataclass(frozen=True)
class Unit:
    id: str        # "bull_points:0", "decisive_question:evidence_for:1", "evidence_balance", …
    section: str   # bull_points | bear_points | key_unknowns | decisive_question | twin |
    #                evidence_balance
    text: str


def _claim(p: Any) -> str:
    return str(p.get("claim", "")) if isinstance(p, dict) else str(p)


def draw_units(raw: dict[str, Any]) -> list[Unit]:
    """The prose units of one draw's raw tool output, decoded as `synthesize` decodes it."""
    r = _decode_escapes(raw)
    out: list[Unit] = []
    for side in ("bull_points", "bear_points"):
        for i, p in enumerate(r.get(side) or []):
            out.append(Unit(f"{side}:{i}", side, _claim(p)))
    for i, k in enumerate(r.get("key_unknowns") or []):
        out.append(Unit(f"key_unknowns:{i}", "key_unknowns",
                        k if isinstance(k, str) else json.dumps(k)))
    dq = r.get("decisive_question") or {}
    if isinstance(dq, dict):
        out.append(Unit("decisive_question:question", "decisive_question",
                        str(dq.get("question", ""))))
        for side in ("evidence_for", "evidence_against"):
            ev = dq.get(side) or []
            for i, e in enumerate(ev if isinstance(ev, list) else [ev]):
                out.append(Unit(f"decisive_question:{side}:{i}", "decisive_question", _claim(e)))
    for i, t in enumerate(r.get("twin_reference_cases") or []):
        if isinstance(t, dict):
            out.append(Unit(f"twin:{i}", "twin", str(t.get("distinguishing_fact", ""))))
    out.append(Unit("evidence_balance", "evidence_balance", str(r.get("evidence_balance", ""))))
    return [u for u in out if u.text.strip()]


def gold_prose(text: Any) -> str:
    """A gold claim's prose: its text, or — for the decisive question, stored as an object — the
    question and each evidence claim, never their source_refs."""
    obj = text
    if isinstance(text, str):
        if not text.lstrip().startswith("{"):
            return text
        try:
            obj = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return text
    if not isinstance(obj, dict):
        return str(text)
    parts = [str(obj.get("question", ""))]
    for side in ("evidence_for", "evidence_against"):
        for e in obj.get(side) or []:
            parts.append(_claim(e))
    return " ".join(p for p in parts if p)
