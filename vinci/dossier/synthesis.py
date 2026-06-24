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

from vinci.dossier.schemas import (
    DecisiveQuestion,
    MechanicalLayer,
    SourcedPoint,
    Synthesis,
    TwinCase,
)
from vinci.graph.llm import LlmClient, LlmError

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
# analyst-RATING context: "buy"/"sell" here describe the CONSENSUS (a fact surfaced as context),
# not the dossier concluding. Redact these spans before the directional lint so it stops flagging
# both 'buy' and 'sell' on a single sentence that merely reports the sell-side rating.
_RATING_CTX = re.compile(
    r"\b(?:buy|sell)-side\b"                                # sell-side / buy-side
    r"|\b(?:buy|sell|hold|outperform|underperform|overweight|underweight)\b\s*\([^)]*\)"
    r"|\b\d+\s*=\s*(?:buy|sell)\b"                          # 1=buy / 5=sell
    r"|\b(?:buy|sell)\b(?=\s*(?:…|\.\.\.|scale|rating))",   # buy… / sell scale
    re.IGNORECASE,
)


def _snip(s: str, n: int = 70) -> str:
    """A claim prefix that ends on a WORD boundary + '…' — so a flag never cuts mid-word (e.g.
    '…Phase 3.2 capac' → '…Phase 3.2 capacity…'). Returns the whole string when short."""
    if len(s) <= n:
        return s
    return (s[:n].rsplit(" ", 1)[0] or s[:n]) + "…"


# Anchors-on-distorted-P/E: a valuation mention (the P/E or its percentile) + a cheapness/mean-
# reversion cue. Flagged ONLY when the mechanical P/E is marked distorted (the FUBO trap — a bull
# case leaning on a multiple built on a non-current EPS). Human review, never auto-removed.
_PE_TERM = re.compile(r"\bP/E\b|\bP/?E ratio\b|percentile", re.IGNORECASE)
_CHEAP_CUE = re.compile(
    r"\b(cheap|depressed|undervalued|inexpensive|trough|floor|mean.?reversion|revert|reversion|"
    r"attractive|discount(ed)?|bargain)\b|not\b.{0,20}priced",
    re.IGNORECASE,
)

# Verification-assertion tripwire: the dossier CITES, it never VERIFIES — flag prose asserting the
# machine has verified/proven something (only the human can make that call). Honest negations
# ("unverified", "cannot be verified") and benign domain terms ("proven track record", "confirmed
# orders") are redacted FIRST, so the tripwire fires only on real over-assertion.
_VERIFIED_BENIGN = re.compile(
    r"\bun(?:verified|confirmed|proven|substantiated)\b"
    r"|\b(?:cannot|can(?:no|')t|could ?n[o']?t|not)(?:\s+(?:yet|be|been))*\s+"
    r"(?:verified|confirmed|proven|established|substantiated)\b"
    r"|\bcan(?: be)?\s+(?:verified|confirmed)\b"
    r"|\bno\s+\w{0,12}\s+(?:verification|confirmation)\b"
    r"|\bproven\s+(?:track record|model|playbook|formula|reserves?)\b"
    r"|\bestablished\s+(?:brand|player|leader|franchise|compan\w*|business|name|presence|\d{4})"
    r"|\bconfirmed\s+(?:orders?|bookings?|backlog|cases?|reservations?)\b"
    r"|\bverified\s+(?:users?|accounts?|buyers?|customers?)\b",
    re.IGNORECASE,
)
_VERIFIED_ASSERTION = re.compile(
    r"\bverified\b"
    r"|\b(?:confirm(?:s|ed|ing)?|prov(?:es|en)|demonstrat(?:es|ed)|establish(?:es|ed))\s+"
    r"(?:that|this|the (?:fact|case|thesis|bull|bear|claim))\b"
    r"|\b(?:definitively|conclusively|incontrovertibl[ey]|irrefutabl[ey]|certified|demonstrably)\b"
    r"|\bbeyond (?:any |reasonable )?doubt\b|\bestablished fact\b",
    re.IGNORECASE,
)

# Margin compression cited as a bear point WITHOUT its absolute-EBITDA reconciler (Mechanism A.1
# now pairs them) — the consensus misread. _ABS_RECON = the claim reconciled vs the absolute.
_MARGIN_DROP = re.compile(
    r"\bmargin\b[^.]{0,40}\b(compress|contract|erod|declin|fell|fall|lower|down|deteriorat|shrink|"
    r"weaken|weak\b)\w*"
    r"|\b(compress|contract|erod|declin|fell|fall|shrink)\w*[^.]{0,25}\bmargin\b",
    re.IGNORECASE,
)
# the claim DID reconcile vs the RISING absolute EBITDA (a bare 'absolute'/'EBITDA <year>' is not)
_ABS_RECON = re.compile(
    r"\bEBITDA (?:rose|grew|grow\w*|up\b|higher|increas\w*|expand\w*|climb\w*|rising)"
    r"|\bEBITDA[^.]{0,25}→"
    r"|\babsolute (?:ebitda|dollar)\w*[^.]{0,35}(?:ros\w*|grew|up\b|higher|increas\w*|rising|→)"
    r"|EBITDA (?:in )?dollars|dollar EBITDA|\bscal(?:e|es|ed|ing)\b|operating leverage|reconcil\w*",
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
                "description": "The secular-and-TERMINAL decline case. For EACH bear point on an "
                "OPTICAL/timing/trailing metric (a margin %, a trailing multiple, leverage), state "
                "in the claim whether it is the REAL signal or the consensus MISREAD, using the "
                "paired reconciler in the SAME fact (margin % carries absolute EBITDA beside it; a "
                "trailing multiple carries its forward or a 'trailing-only' blind-flag). The edge "
                "diverges from the biased consensus read — do not reproduce it.",
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
            "evidence_balance": {  # LAST on purpose: if the response truncates, this (not a
                "type": "string",  # structural field) is the casualty, and it's flag-not-block.
                "description": "ONE concise line, ≤25 words: <strongly-bearish|mixed|strongly-"
                "bullish> — <the single dominant reason>. NOT a paragraph; do not restate the "
                "bull/bear points. A lopsided reality must produce a lopsided read.",
            },
        },
        "required": [
            "bull_points", "bear_points", "twin_reference_cases", "decisive_question",
            "key_unknowns", "evidence_balance",
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
    "put a verdict and it is not your job. "
    "(7) ANTI-BALANCE: do NOT default to symmetric bull/bear lists. evidence_balance is the LAST "
    "field — ONE concise line (≤25 words: label + the single dominant reason, NOT a paragraph, do "
    "not restate the points); a one-sided reality must produce a one-sided dossier, not laundered "
    "into a balanced-looking list. "
    "(8) OPACITY-AS-SIGNAL: a MISSING expected disclosure (no segment breakout, no cash-runway "
    "visibility, an opaque structure, no forward guide, a survival_capacity leg UNKNOWN) is NOT "
    "neutral — surface it in key_unknowns as a BEARISH risk, not a neutral gap. "
    "(9) CONTRARIAN-RECONCILIATION: for each major bear point citing an optical/timing/trailing "
    "metric, state explicitly whether it is the REAL signal or the optical/consensus MISREAD, "
    "using the paired reconciler in the same fact (a falling margin % carries the absolute EBITDA "
    "beside it — a % can fall while EBITDA RISES). The edge diverges from the biased consensus "
    "read; do not reproduce it."
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
            flags.append(f"UNCITED {where}: '{_snip(p.claim)}' (ref not in mechanical facts)")
        elif _MISSING_CLAIM.search(p.claim) and _traces(p.source_ref, present_refs):
            # a "field X is missing" claim must bind to X's MISSING marker (no source_ref), not to
            # an unrelated PRESENT field — such a claim belongs in key_unknowns, not here.
            cited = False
            flags.append(
                f"MISMATCH {where}: '{_snip(p.claim, 55)}' asserts missing/UNKNOWN data yet cites "
                "a PRESENT field — move to key_unknowns, don't source-bind it"
            )
        for n in _floats(p.claim):
            if not _num_traces(n):
                flags.append(f"UNTRACEABLE figure '{n:g}' in {where}: '{_snip(p.claim)}'")
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
    lint_blob = _RATING_CTX.sub(" ", blob)  # don't flag buy/sell reporting the analyst rating
    for hit in {m.group(0).lower() for m in _DIRECTIONAL.finditer(lint_blob)}:
        flags.append(f"DIRECTIONAL language '{hit}' — human review (dossier frames, not concludes)")

    # when the mechanical P/E is marked distorted, flag a BULLISH claim leaning on the multiple as
    # cheap / mean-reverting — the bull case must not anchor on a P/E built on a non-current EPS.
    pe = mech.valuation.pe
    if pe.note and "distort" in pe.note.lower():
        bullish = [(p, "bull_point") for p in bull] + [(p, "decisive.for") for p in dq.evidence_for]
        for p, where in bullish:
            if _PE_TERM.search(p.claim) and _CHEAP_CUE.search(p.claim):
                flags.append(
                    f"ANCHORS-ON-DISTORTED-P/E {where}: '{_snip(p.claim)}' — the P/E is distorted "
                    "(rests on a non-current/non-recurring EPS); don't read it as cheap"
                )

    # Verification-assertion tripwire: the dossier cites, it never verifies. After redacting honest
    # negations + benign domain terms, any remaining claim asserting the machine VERIFIED/PROVED
    # something crosses the line the dossier can't — flag it for the human to confirm.
    pts = ([(p, "bull_point") for p in bull] + [(p, "bear_point") for p in bear]
           + [(p, "decisive.for") for p in dq.evidence_for]
           + [(p, "decisive.against") for p in dq.evidence_against])
    for p, where in pts:
        if _VERIFIED_ASSERTION.search(_VERIFIED_BENIGN.sub(" ", p.claim)):
            flags.append(
                f"VERIFICATION-CLAIM {where}: '{_snip(p.claim)}' — the dossier cites, it does not "
                "verify; confirm against the source (cited ≠ verified)"
            )

    # G.1 unreconciled margin claim: a bear/decisive-against point citing margin COMPRESSION without
    # the absolute-EBITDA reconciliation the layer now pairs it with (A.1) — the exact consensus
    # misread the fix targets (a margin % can fall while absolute EBITDA rises).
    g1 = [(x, "bear_point") for x in bear] + [(x, "decisive.against") for x in dq.evidence_against]
    for p, where in g1:
        if _MARGIN_DROP.search(p.claim) and not _ABS_RECON.search(p.claim):
            flags.append(
                f"UNRECONCILED {where}: '{_snip(p.claim)}' — cites margin compression without the "
                "absolute-EBITDA reconciliation (margin % can fall while EBITDA rises)"
            )
    # G.2 false-balance: evidence_balance must be present + committed; a 'mixed' read over a
    # lopsided bull/bear split is a one-sided case laundered to look balanced.
    eb = (synth.evidence_balance or "").strip().lower()
    nb, nr = len(bull), len(bear)
    if not eb:
        flags.append(
            "evidence_balance MISSING — the synthesis must commit a balance read, never default it"
        )
    elif "mixed" in eb and (nb + nr) >= 3 and (min(nb, nr) == 0 or max(nb, nr) > 2 * min(nb, nr)):
        flags.append(
            f"FALSE-BALANCE? evidence_balance reads 'mixed' but the bull/bear split is lopsided "
            f"({nb} bull vs {nr} bear) — confirm genuinely mixed, not one-sided dressed as balanced"
        )

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
        evidence_balance=str(raw.get("evidence_balance", "")),
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
    # a missing STRUCTURAL field means a truncated response — mark the synthesis UNAVAILABLE rather
    # than silently defaulting to a blank. evidence_balance is excluded: its absence is a contract
    # REGRESSION the guardrail FLAGS (G.2), not a truncation that blocks — flag, don't drop.
    structural = [k for k in SYNTHESIS_TOOL["input_schema"]["required"] if k != "evidence_balance"]
    missing = [k for k in structural if k not in raw]
    if missing:
        note = f"synthesis tool returned incomplete output — missing required field(s) {missing}"
        log_parts += ["", "=== INCOMPLETE ===", note]
        flag = f"LLM synthesis UNAVAILABLE — {note} (likely truncated)"
        return None, [flag], "\n".join(log_parts)
    synth, flags = _validate(_parse(raw), mech)
    return synth, flags, "\n".join(log_parts)
