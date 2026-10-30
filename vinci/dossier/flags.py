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

import re

# Leading tokens that mark a flag as machine-QA — dev/JSON only, hidden from the human PDF/web view.
# DIRECTIONAL + VERIFICATION-CLAIM are QA (machine-overstep self-checks, operator-decided 2026-07):
# the offending point is already in the doc; the flag is about the machine's discipline, not the
# analyst's read. ``str.startswith`` takes this tuple directly.
#
# NOT hidden — UNTRACEABLE is a human CAVEAT (data-integrity): a figure cited to STRUCTURED data
# that doesn't contain it (a source-misbinding/fabrication). Its source_ref LOOKS legitimate, so a
# human can't catch it from the rendered citation — it must show. (Contrast TRANSCRIPT-FIGURE, whose
# source_ref honestly reads "CIQ transcript(s): …" — the reader can verify via the visible citation,
# so its soft "verify against the call" note stays QA to avoid noise.)
_QA_MARKERS: tuple[str, ...] = (
    "UNCITED",
    "MISMATCH",
    "TRANSCRIPT-FIGURE",
    "TWIN ",
    "DIRECTIONAL",
    "VERIFICATION-CLAIM",
    "evidence_balance MISSING",
    "LLM synthesis",
    "RULE-LEAK",  # R3 — an internal 'rule N' reference leaked into the output (dev QA lint)
    "CONTRADICTION",  # P2 — synthesis calls a PRESENT mechanical block pending/unread (dev QA lint)
    "(E5)",  # FIX-2 — Tier-2 covenant-extraction machine notes (cost bound / fetch fail) → dev, not
    "(P3)",  # a decision caveat; the human-facing summary is one line INSIDE the covenant block.
    "transcripts on file but unparseable",  # PR-B §3-now — an OPS action (install LibreOffice),
    "transcript cut at the ceiling",  # G-D3 — a call past the 100,000-character safety ceiling
    "operating-drivers:",  # PR-B — mechanism-tier per-source honest-miss notes → dev/JSON QA, not
    # an analyst caveat; a no-driver name renders the honest empty Mechanism line, not a caveat.
    #
    # OPERATOR RULING 2026-09-02 — an EDGAR outage that blanks the drawdown cause is dev/JSON QA.
    # This one is an EXCEPTION to the module's default above, taken deliberately, so it is argued
    # here rather than assumed: the default routes a new flag to the human, and by that default this
    # would have been a caveat (data completeness, not machine discipline — the `UNTRACEABLE` line).
    # It is hidden anyway because the READER IS ALREADY TOLD at the point of use: `_drawdown_cause`
    # degrades `shape` to UNKNOWN and `_fact` renders "_UNKNOWN_ — EDGAR filing index unavailable…"
    # in the drawdown block itself (#570). So the human surface is NOT silent — this flag is the
    # machine's twin of a message the analyst already sees, and promoting it would put the same
    # sentence in two places on every affected name of a degraded run. The visible-absence rule is
    # satisfied by the rendered UNKNOWN, not by this flag.
    # FALSIFIER: if that UNKNOWN note ever stops rendering, this entry must be removed — the flag is
    # then the only signal, and hiding it would make the outage silent. Pinned by
    # `test_the_outage_flag_is_hidden_because_the_block_itself_already_says_so`, which asserts BOTH
    # halves together (hidden AND the note present), so the two cannot drift apart.
    "drawdown-cause:",
    # (2026-10-30) an annual-summary LTM against its four quarters (`ltm_quarters`): a machine
    # check of CIQ's arithmetic. A MATERIAL row that fails it refuses the build, so what reaches a
    # page here is a non-material disagreement or a quarter reading '-' — dev/JSON QA
    "ciq-ltm-quarters:",
    # (2026-10-30, audit X1(a), operator ruling "Yes, cross-check") a share count tagged after its
    # own filing, re-dated from its cover sentence or its filing day: each correction is QA. Its
    # REFUSAL is not — "share count UNKNOWN:" explains an UNKNOWN the reader sees, so it stays a
    # caveat (`vinci.edgar.cover_count`)
    "share count:",
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
    "GAAP-EPS-MOMENTUM": "GAAP-EPS move that normalized EPS did not make",
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
    # UNTRACEABLE has an infix ("figure 'N' in {where}: …") so it needs its own re-voice, not the
    # simple TOKEN-{where} form below.
    m = re.match(r"UNTRACEABLE figure '([^']*)' in (\S+?): (.*)", flag)
    if m:
        n, where, rest = m.groups()
        human = _WHERE_HUMAN.get(where, where)
        return (f"Untraceable figure {n} ({human}) — cited to structured data that does not "
                f"contain it; verify the source before relying on it: {rest}")
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
