"""Audience-split for the dossier's human-review flags.

Flags are emitted as plain strings by two layers — the mechanical assembler (valuation-basis
caveats) and the synthesis validator (the anti-fluent-noise guardrails). They serve TWO audiences
that were previously mixed in one block: an equity analyst (who acts on decision CAVEATS) and the
AI dev (who reads the machine's own QA self-checks). This module classifies each emitted flag at
the SCHEMA boundary — the emission logic (the guardrail moat in ``synthesis._validate``) is never
touched, so no guardrail and none of its tests can regress.

QA is the explicit HIDE-list (machine-integrity self-checks: citation traceability, twin contract,
LLM-overstep, LLM failure). Everything else defaults to a human CAVEAT — fail toward transparency,
so a newly-added flag is shown to the human, never silently hidden. The five validator-speak
caveats are re-voiced out of ALL-CAPS-token jargon; the already-plain caveats (and the ``pull CIQ``
incomplete-input notes) pass through unchanged.
"""

from __future__ import annotations

# Leading tokens that mark a flag as machine-QA — dev/JSON only, hidden from the human PDF/web view.
# DIRECTIONAL + VERIFICATION-CLAIM are QA (machine-overstep self-checks, operator-decided 2026-07):
# the offending point is already in the doc; the flag is about the machine's discipline, not the
# analyst's read. ``str.startswith`` takes this tuple directly.
_QA_MARKERS: tuple[str, ...] = (
    "UNCITED",
    "MISMATCH",
    "TRANSCRIPT-FIGURE",
    "UNTRACEABLE",
    "TWIN ",
    "DIRECTIONAL",
    "VERIFICATION-CLAIM",
    "evidence_balance MISSING",
    "LLM synthesis",
)

# The validator-speak caveats carry a `{where}:` field name (which synthesis point tripped it).
_WHERE_HUMAN: dict[str, str] = {
    "bull_point": "a bull point",
    "bear_point": "a bear point",
    "decisive.for": "a decisive-for point",
    "decisive.against": "a decisive-against point",
}
# token → plain lead, for the caveats emitted as `TOKEN {where}: '<claim>' — <explanation>`. The
# post-`—` explanation is already human-readable, so re-voicing only swaps the ALL-CAPS token +
# humanises the field name; the useful explanation is kept.
_REVOICE_WHERE: dict[str, str] = {
    "ANCHORS-ON-DISTORTED-P/E": "Distorted-P/E anchor",
    "UNRECONCILED": "Unreconciled margin-compression",
    "PEER-COMP-BARE": "Bare peer-comparison",
    "HETEROGENEOUS-BENCHMARK": "Heterogeneous-peer benchmark",
}
# token → replacement lead, for caveats without a `{where}:` field (the two FALSE-BALANCE variants).
_REVOICE_PLAIN: dict[str, str] = {
    "FALSE-BALANCE?": "Possible false balance —",
}


def is_qa(flag: str) -> bool:
    """True iff ``flag`` is a machine-QA self-check (dev/JSON only). QA is the explicit hide-list;
    anything else defaults to a human caveat (fail toward transparency)."""
    return flag.startswith(_QA_MARKERS)


def revoice(flag: str) -> str:
    """Re-voice a decision caveat out of validator-speak: replace the ALL-CAPS token (and humanise
    the `{where}:` field name) with a plain lead, keeping the explanation. Already-plain caveats and
    the `pull CIQ …` incomplete-input notes match no token and pass through unchanged."""
    for token, label in _REVOICE_WHERE.items():
        if flag.startswith(token):
            rest = flag[len(token):].lstrip()
            for where, human in _WHERE_HUMAN.items():
                if rest.startswith(f"{where}:"):
                    return f"{label} ({human}): {rest[len(where) + 1:].lstrip()}"
            return f"{label}: {rest}"
    for token, lead in _REVOICE_PLAIN.items():
        if flag.startswith(token):
            return lead + flag[len(token):]
    return flag


def partition(flags: list[str]) -> tuple[list[str], list[str]]:
    """Split emitted flags into (caveats, qa_flags): caveats are the human-facing decision flags
    (re-voiced), qa_flags are the machine self-checks (raw, dev/JSON only)."""
    caveats: list[str] = []
    qa_flags: list[str] = []
    for flag in flags:
        if is_qa(flag):
            qa_flags.append(flag)
        else:
            caveats.append(revoice(flag))
    return caveats, qa_flags
