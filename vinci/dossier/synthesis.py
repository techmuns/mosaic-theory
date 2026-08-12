"""The SYNTHESIS layer — the project's configured LLM, **fenced**.

The model is given ONLY the mechanical layer's source-bound facts (not the web, not its own memory),
and forced through a tool whose schema is the verdict-free :class:`Synthesis` shape — there is no
field for a conclusion, so it cannot render one. Its output is then validated, not trusted:

- every bull/bear point must cite a ``source_ref`` that exists in the input (uncited → flagged);
- every number must trace to the mechanical layer (untraceable → flagged), unless cited to the
  earnings-call transcript, where a prose figure earns a soft 'verify against the call' note;
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
    OperatingDriversExtract,
    PrimarySource,
    SourcedPoint,
    SourceStatus,
    Synthesis,
    TwinCase,
)
from vinci.dossier.verdict import split_lean
from vinci.graph.llm import LlmClient, LlmError
from vinci.sleeves import BY_KEY, DEFAULT_SLEEVE, Sleeve, require_sleeve

_UNVERIFIED = "[LLM-suggested, unverified]"
# unit renderings an LLM uses for the same stored number (fraction↔%, raw↔K/M/B) — for number-trace
_TRACE_SCALES = (1.0, 1e2, 1e-2, 1e3, 1e-3, 1e6, 1e-6, 1e9, 1e-9)
_NUM = re.compile(r"-?\d[\d,]*\.?\d+|-?\d+")
# Calendar/period LABELS that _NUM would wrongly extract as figures and the trace then flags as
# untraceable: 'FY21'/'FY25' (→21/25), 'Q1', 'fiscal 2025', '90 days ago' (→90), '8 quarters'. These
# are not CLAIMED values — skip a number whose immediate context is a fiscal/quarter prefix or a
# time-unit suffix. (Bare 4-digit years are NOT skipped — they collide with real $ figures.)
_CAL_BEFORE = re.compile(r"(?:\bFY|\bfiscal\s*|\bQ)\s*$", re.IGNORECASE)
_CAL_AFTER = re.compile(r"^\s*(?:days?|weeks?|months?|quarters?|qtrs?|years?)\b", re.IGNORECASE)
# A point's source_ref pointing at the earnings-call TRANSCRIPT (verbatim prose) rather than a
# structured CIQ cell. A figure cited to the transcript is NOT in the mechanical layer's number
# universe, so it earns a soft 'verify-against-the-call' note — NOT a hard UNTRACEABLE, which
# means a number cited to STRUCTURED data that lacks it (a real misbinding/fabrication).
# The canonical ref is `CIQ transcript(s): <names>` (ciq_sheets.management_commentary).
_TRANSCRIPT_REF = re.compile(r"transcript", re.IGNORECASE)
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
# analyst-RATING / external-posture context: a directional-looking token here REPORTS the consensus
# or names a domain metric — it is NOT the dossier concluding. Redact these spans before the
# directional lint. Covers buy/sell-side; a parenthetical rating ("Outperform (2.00)"); an
# N=buy…sell scale; buy/sell before "scale"/"rating"; the CPG **buy-rate** velocity metric; a
# {rating-word} + rating/recommendation ("Outperform rating", "Buy recommendation"); consensus/
# analyst + recommendation; "recommendation (source)"; and conviction DESCRIBING an external/analyst
# target — NOT a 'high/low-conviction <verdict>', which still flags. (Validated adversarially.)
_RATING_CTX = re.compile(
    r"\b(?:buy|sell)-side\b"                                # sell-side / buy-side
    # {rating} [(score)] rating/recommendation — BEFORE the bare-parenthetical arm so the longer
    # "Buy (1.00) recommendation" wins over "Buy (1.00)" (else "recommendation" is orphaned).
    r"|\b(?:buy|sell|hold|outperform|underperform|overweight|underweight)\b\s*"
    r"(?:\([^)]*\)\s*)?(?:rating|recommendation)\b"
    r"|\b(?:buy|sell|hold|outperform|underperform|overweight|underweight)\b\s*\([^)]*\)"
    r"|\b\d+\s*=\s*(?:buy|sell)\b"                          # 1=buy / 5=sell
    r"|\b(?:buy|sell|hold|outperform|underperform)\s+\d{1,2}\b"  # rating-count "Buy 2"/"Sell 0"
    r"|\b(?:buy|sell)\b(?=\s*(?:…|\.\.\.|scale|rating))"    # buy… / sell scale
    r"|\b(?:buy|sell)[\s-]?rate\b"                          # CPG buy-rate metric (not a verdict)
    r"|\b(?:buy|sell)-(?:off|in)\b"                         # sell-off/in, buy-in — market term
    r"|\b(?:consensus|analysts?|sell-side|street)\s+(?:\w+\s+){0,2}recommendation\b"
    r"|\brecommendation\b[^.]{0,30}\b(?:outperform|underperform|overweight|underweight)\b\s*\(\d"
    r"|\brecommendation\b(?=\s*\()"                         # "recommendation (CIQ …)" — reported
    r"|\b(?:external|analysts?|consensus|target|street|sell-side)\b[^.]{0,25}\bconviction\b"
    r"|\bconviction\b[^.]{0,25}\b(?:external|analysts?|consensus|target|street|sell-side)\b",
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
# ("unverified", "cannot be verified", "not demonstrably") and benign terms ("proven track record",
# "confirmed orders") are redacted FIRST, so the tripwire fires only on real over-assertion.
_VERIFIED_BENIGN = re.compile(
    r"\bun(?:verified|confirmed|proven|substantiated)\b"
    r"|\b(?:cannot|can(?:no|')t|could ?n[o']?t|not)(?:\s+(?:yet|be|been))*\s+"
    r"(?:verified|confirmed|proven|established|substantiated)\b"
    r"|\bcan(?: be)?\s+(?:verified|confirmed)\b"
    r"|\bno\s+\w{0,12}\s+(?:verification|confirmation)\b"
    r"|\bproven\s+(?:track record|model|playbook|formula|reserves?)\b"
    r"|\bestablished\s+(?:brand|player|leader|franchise|compan\w*|business|name|presence|\d{4})"
    r"|\bconfirmed\s+(?:orders?|bookings?|backlog|cases?|reservations?)\b"
    r"|\bverified\s+(?:users?|accounts?|buyers?|customers?)\b"
    # a NEGATED over-assertion adverb ('not demonstrably', 'never conclusively', "isn't/doesn't …")
    # is a HEDGE, not an over-claim — redact so the tripwire fires only on a POSITIVE claim. The
    # contraction arm uses \B (non-boundary) + a MANDATORY apostrophe so "isn't" matches but a stray
    # "nt" ("point demonstrably") does NOT — that would wrongly redact a positive claim.
    r"|(?:\b(?:not|never|no)|\Bn['’]t)\s+(?:yet\s+)?(?:demonstrabl[ey]|definitively|conclusively|"
    r"incontrovertibl[ey]|irrefutabl[ey]|certified)\b",
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
# the claim DID reconcile vs absolute EBITDA — RISING (the optical-misread defence) OR in DOLLARS in
# EITHER direction: a bear point that CHECKED absolute EBITDA and found it fell ($103M→$79M) has
# reconciled too. A bare 'absolute'/'EBITDA <year>' with no movement or $ is still not enough.
_ABS_RECON = re.compile(
    r"\bEBITDA (?:rose|grew|grow\w*|up\b|higher|increas\w*|expand\w*|climb\w*|rising)"
    r"|\bEBITDA[^.]{0,25}→"
    r"|\babsolute (?:ebitda|dollar)\w*[^.]{0,35}(?:ros\w*|grew|up\b|higher|increas\w*|rising|→)"
    r"|\babsolute\b[^.]{0,15}\bebitda\b[^.]{0,70}"
    r"(?:\$\s?\d|\bfell\b|\bfallen\b|\bdrop\w*|\bdeclin\w*|\blower\b|\bslip\w*|\bslid\b|"
    r"\beas(?:e|es|ed|ing)\b|→)"
    r"|EBITDA (?:in )?dollars|dollar EBITDA|\bscal(?:e|es|ed|ing)\b|operating leverage|reconcil\w*",
    re.IGNORECASE,
)
# a bear point that DISCLAIMS the margin-only read ("not just a falling margin %", "not optical") is
# ASSERTING real deterioration, not citing bare margin compression — so don't G.1-flag it.
_NOT_JUST_MARGIN = re.compile(
    r"\bnot (?:just|merely|only|simply)\b[^.]{0,30}\bmargin\b|\bnot an? optical\b", re.IGNORECASE
)

# Peer-comp contract (the CIQ Company Comparable Analysis read the edge must RESIST, not echo). A
# relative-valuation verdict ('cheap/rich vs peers') is a CONSENSUS framing, not a signal, until it
# is decomposed (earned vs residual, via the fundamental deltas) AND set against the peer-set
# composition. These cues let the guardrail flag a BARE peer gap and a heterogeneous set read as a
# clean benchmark — the machine POSES the question; it never computes a residual or implied upside.
_PEER_REF = re.compile(  # the claim positions the name against its comp set
    r"\bpeers?\b|\bpeer[\s-]?(?:set|group|median|multiple|average)\b|\bcomparabl\w*\b|\bcomps?\b"
    r"|\b(?:versus|vs\.?|relative to|discount to|premium to|below|above)\s+(?:the\s+)?"
    r"(?:median|group)\b",
    re.IGNORECASE,
)
_REL_VAL_CUE = re.compile(  # a relative-VALUATION verdict — NARROWED to exclude brand/quality uses
    # of premium/rich/discount (a premium BRAND, a rich ROADMAP, a discount RETAILER are NOT
    # valuation verdicts): premium/discount count only in a valuation construction ("… to/vs the
    # median", "at a premium"); "rich" only as "rich multiple/valuation".
    r"\b(cheap|inexpensive|under-?valued|over-?valued|bargain|expensive)\b"
    r"|\brich(?:ly)?\s+(?:multiple|valuation|valued|priced)\b"
    r"|\b(?:trades?|screens?|valued|priced)\s+(?:below|under|above|over)\b"
    r"|\b(?:discount|premium)\s+(?:to|versus|vs\.?|relative\s+to)\b"
    r"|\bat\s+a\s+(?:discount|premium)\b",
    re.IGNORECASE,
)
_DECOMP_REF = re.compile(  # the EARNED-vs-RESIDUAL decomposition (the fundamental deltas) — count
    # nouns PLURALISED so a decomposed claim reconciling via "margins"/"fundamentals" isn't missed.
    r"\b(earned|residuals?|justif\w*|unexplained|value.?trap|overshoot|deserv\w*|warrant\w*|"
    r"growth|margins?|leverage|betas?|fundamentals?|deltas?)\b",
    re.IGNORECASE,
)
_COMPARABILITY_ACK = re.compile(  # the peer-set COMPOSITION / comparability caveat
    r"\b(heterogen\w*|comparab\w*|composition|dispersion|roster|scale|business model|"
    r"different (?:scale|model|business)|not (?:a )?clean|confidence|caveat|scrutin\w*)\b",
    re.IGNORECASE,
)
# A MINORITY-side point that is sized against the committed lean (rule 7) — framed as a genuine
# counter-point OUTWEIGHED by the majority, not padding faking symmetry. Its presence on the
# minority side suppresses the false-balance flag (the point is honestly qualified, not laundered).
_OUTWEIGHED = re.compile(
    r"\boutweigh\w*\b|what would have to be true|counter-?point|sized against|against the lean|"
    r"\b(?:does not|doesn't|cannot|can't|insufficient to|not enough to)\s+"
    r"(?:outweigh|offset|overturn|overcome|change|reverse)\b|secondary to|subordinate to",
    re.IGNORECASE,
)
# the claim ITSELF names the multiple as distorted and pivots off it (e.g. "the GAAP basis that
# distorts the headline P/E ... forward adj basis far cheaper") — it WARNS about the distortion, the
# opposite of anchoring on it as cheap. Suppress ANCHORS-ON-DISTORTED-P/E there (keeps the genuine
# trough-anchor catch where the claim reads the distorted multiple AS cheap).
_DISTORTION_ACK = re.compile(r"\bdistort\w*|\bnon-recurring\b|\bone-time\b|\bone-off\b|\banomal\w*",
                             re.IGNORECASE)
# …but NOT when negated ("the charge is NOT one-time", "not a one-off") — a claim asserting the hit
# is PERMANENT while anchoring on the cheap multiple is the trap, so it must still flag.
_DISTORTION_DENIED = re.compile(
    r"\b(?:not|n['’]t|no)\b[^.]{0,14}?(?:distort\w*|non-recurring|one-time|one-off|anomal\w*)",
    re.IGNORECASE,
)
# a peer-comp claim that RESOLVES the gap to the EARNED / value-trap side ("the discount is earned …
# a value trap") cannot misread a heterogeneous median as a clean CHEAP signal — confidence-gating
# the median only reinforces its bearish read. Suppress HETEROGENEOUS-BENCHMARK there — but NOT when
# the claim DENIES it ("the discount is NOT earned … cheap vs peers"), which IS the clean-benchmark
# misread the gate must catch.
_EARNED_RESOLVED = re.compile(r"\b(earned|deserv\w*|value.?trap)\b", re.IGNORECASE)
_EARNED_DENIED = re.compile(
    r"\b(?:not|n['’]t|no)\b[^.]{0,14}?(?:earned|deserv\w*|value.?trap)", re.IGNORECASE
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

_TOOL_TEMPLATE: dict[str, Any] = {
    "name": "assemble_dossier_framing",
    "description": (
        "Assemble {tool_subject} FOR A HUMAN to adjudicate — "
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
                "description": "{bull_case} A 'cheap "
                "vs peers' claim is a CONSENSUS framing, not a signal: present a peer gap only "
                "WITH the peer-set composition AND the earned-vs-residual decomposition "
                "(fundamental_deltas) — POSE whether the discount is EARNED (value trap) or "
                "RESIDUAL (overshoot); never compute a residual or an implied upside, and never "
                "read a HETEROGENEOUS peer set as a clean benchmark. Every bull point must "
                "SURVIVE SCRUTINY — genuine, load-bearing, never a neutral-as-bullish padding "
                "of the count; when bull is the MINORITY under evidence_balance, frame each as a "
                "counter-point OUTWEIGHED by the bear majority, never suppressing a genuine one "
                "(rule 7).",
            },
            "bear_points": {
                "type": "array",
                "items": _POINT,
                "description": "{bear_case} For EACH bear point on an "
                "OPTICAL/timing/trailing metric (a margin %, a trailing multiple, leverage), state "
                "in the claim whether it is the REAL signal or the consensus MISREAD, using the "
                "paired reconciler in the SAME fact (margin % carries absolute EBITDA beside it; a "
                "trailing multiple carries its forward or a 'trailing-only' blind-flag). The edge "
                "diverges from the biased consensus read — do not reproduce it. Every bear point "
                "must SURVIVE SCRUTINY — genuine, load-bearing, never padding to inflate the "
                "majority; when bear is the MINORITY under evidence_balance, frame each as a "
                "counter-point OUTWEIGHED by the bull majority, never suppressing a genuine one "
                "(rule 7).",
            },
            "twin_reference_cases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "A SPECIFIC named company."},
                        "outcome": {"type": "string", "description": "{twin_outcome}"},
                        "distinguishing_fact": {
                            "type": "string",
                            "description": "QUALITATIVE: the analogue pattern only; NO figures "
                            "(caps/multiples/ratios live in peer_set / fundamental_deltas).",
                        },
                        "source": {
                            "type": "string",
                            "description": f"A source_ref from input, or exactly '{_UNVERIFIED}'. "
                            "Never a recovery rate, base rate, or probability.",
                        },
                    },
                    "required": ["name", "outcome", "distinguishing_fact", "source"],
                },
                "description": "3-6 named QUALITATIVE analogues for reasoning. No figures — "
                "caps/multiples/ratios live in peer_set / fundamental_deltas, not here.",
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

_SYSTEM_TEMPLATE = (
    "You assemble a research dossier's framing for a human discriminator on {subject}"
    ". You ASSEMBLE AND CITE; you NEVER CONCLUDE. Hard rules: (1) Use ONLY the source-bound "
    "facts in the user message — never your own memory, never the web; if a fact is MISSING "
    "or UNKNOWN, say so in key_unknowns, don't fill it. (2) Every bull/bear point and every "
    "piece of decisive-question evidence MUST copy a source_ref verbatim from the supplied facts. "
    "(3) Give both cases honestly: {both_cases}"
    ". (4) Twin reference cases must be SPECIFIC NAMED companies; tag each source as a real "
    "source_ref or exactly '[LLM-suggested, unverified]'. Keep distinguishing_fact QUALITATIVE: "
    "the analogue PATTERN only, with NO figures — caps / multiples / ratios live source-bound in "
    "peer_set / fundamental_deltas, never restated in twin prose; never a recovery rate, base "
    "rate, or probability — analogues are for reasoning, not stats. Each twin is ONE company, "
    "never a '/'-joined pair or a cohort. (4b) GROUNDING PREFERENCE (a preference, NOT a mandate): "
    "where the peer roster or the name's OWN resolved past arc already offers a valid analogue, "
    "PREFER a source-bound twin over an '[LLM-suggested, unverified]' one — but never invent or "
    "force one, and never let this steer the OUTCOME direction; an unsourced twin is fine when it "
    "is the best genuine analogue. (5) Surface the decisive "
    "question; do "
    "NOT answer it. (6) Never recommend, rate, score, or predict a direction — there is nowhere to "
    "put a verdict and it is not your job. "
    "(7) ANTI-BALANCE — SYMMETRIC, identical whether the name leans bullish or bearish: the "
    "BODY's weight must MATCH evidence_balance, never a balanced count. When the lean is "
    "committed (strongly-bearish OR strongly-bullish), the MAJORITY side (the one the lean "
    "names) is complete and rigorous; the MINORITY side carries ONLY genuine, load-bearing "
    "counter-points, EACH framed as 'a genuine counter-point, OUTWEIGHED by <the dominant "
    "majority fact>' or 'what would have to be true for the <minority> case' — sized "
    "against the lean, NEVER padded with neutral filler to fake symmetry, and NEVER "
    "suppressed when genuine (a real disconfirming fact SURVIVES, qualified). Both sides "
    "must survive scrutiny: no redundant or padding claims, and do not inflate the majority "
    "either. A one-sided reality shows a one-sided COUNT, not a laundered balanced list. "
    "evidence_balance itself is ONE concise line (≤25 words: label + the single dominant "
    "reason; not a paragraph; do not restate the points). "
    "(7b) NO NEUTRAL-AS-DIRECTIONAL (both directions): a fact the dossier flags as "
    "unresolved/neutral (e.g. a multiple at its own-history floor tagged 'trailing-only, "
    "overshoot-vs-terminal unresolved') is counted as NEITHER a bull NOR a bear point — it "
    "belongs in key_unknowns. Distinguish genuine directional evidence from neutral facts "
    "on BOTH sides. "
    "(8) OPACITY-AS-SIGNAL: a MISSING expected disclosure (no segment breakout, no cash-runway "
    "visibility, an opaque structure, no forward guide, a survival_capacity leg UNKNOWN) is NOT "
    "neutral — surface it in key_unknowns as a BEARISH risk, not a neutral gap. "
    "(9) CONTRARIAN-RECONCILIATION: for each major bear point citing an optical/timing/trailing "
    "metric, state explicitly whether it is the REAL signal or the optical/consensus MISREAD, "
    "using the paired reconciler in the same fact (a falling margin % carries the absolute EBITDA "
    "beside it — a % can fall while EBITDA RISES). The edge diverges from the biased consensus "
    "read; do not reproduce it. "
    "(10) PEER-COMP CONTRACT: the peer-comps facts (peer_set / comparability / trading_multiples / "
    "fundamental_deltas) ARE the consensus comp read — the thing the edge must RESIST, not echo. "
    "NEVER present 'cheap vs the peer median' as a conclusion: a peer multiple is meaningful only "
    "WITH the peer-set COMPOSITION beside it, and a discount to peers is a signal only once "
    "decomposed into EARNED (worse growth/margin/leverage/beta — a value trap) vs RESIDUAL "
    "(unexplained by the fundamental_deltas — a possible overshoot). POSE that "
    "justified-vs-residual question for the human; do NOT compute a residual, run a regression, "
    "or assert an implied "
    "upside / 'X% mispriced' — there is no field for it. When comparability flags a HETEROGENEOUS "
    "peer set, treat every peer stat as a CONFIDENCE-GATED input, not a clean benchmark; and read "
    "the trailing-vs-forward (LTM vs NTM) peer spread before leaning on any single multiple. "
    "(11) NEVER reference an internal rule, instruction, or their numbers ('rule 8', 'per rule 3') "
    "in any output field — the reader sees only source-bound analysis, never the machinery. "
    "(12) MECHANISM: the OPERATING-DRIVERS facts (a labelled digest below — validated volumes, "
    "pricing actions, capacity, mix, dated events) are the causal WHY behind the numbers. When a "
    "bull or bear point rests on an operating trend (volume, price, mix, capacity, a client win, a "
    "guidance move), GROUND it in the specific driver and copy THAT driver's source_ref — a "
    "mechanism-bearing point beats a bare multiple/margin observation. The decisive question's "
    "evidence_for / evidence_against should name the load-bearing driver each side turns on. Never "
    "invent a driver not in the digest, nor restate a driver's number as your own derivation."
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


def _claim_figures(text: str) -> list[float]:
    """Numbers a claim CLAIMS as figures, excluding calendar/period LABELS (FY21, Q1, "90 days")
    that _NUM extracts but the trace would wrongly flag. The number-trace runs over these, not
    raw _floats."""
    out: list[float] = []
    for m in _NUM.finditer(text):
        if _CAL_BEFORE.search(text[max(0, m.start() - 9):m.start()]):
            continue  # FY21 / Q1 / fiscal 2025
        if _CAL_AFTER.match(text[m.end():m.end() + 10]):
            continue  # 90 days ago / 8 quarters
        try:
            out.append(float(m.group().replace(",", "")))
        except ValueError:
            continue
    return out


def _twin_numbers(text: str) -> set[str]:
    """Digits a twin's prose CLAIMS as figures — excluding only an identifier fragment where a digit
    is fused to a PRECEDING letter (Q4, B2B) or sits after a letter-hyphen (GLP-1, COVID-19). A
    free-standing figure with a UNIT SUFFIX (1.5x, 200M, 50bps) or a bare decimal (a stray '3.2'
    colliding with a real multiple) is STILL caught — only `before.isalpha()` is excluded, not
    `after`, which would wrongly drop unit-suffixed figures."""
    out: set[str] = set()
    for m in _NUM.finditer(text):
        before = text[m.start() - 1] if m.start() else " "
        if before.isalpha():
            continue  # Q4 / B2B — digit fused to a preceding letter is an identifier fragment
        if before == "-" and m.start() >= 2 and text[m.start() - 2].isalpha():
            continue  # GLP-1 / COVID-19
        out.add(m.group().replace(",", "").lstrip("-"))
    return out


def _traces(ref: str, universe: set[str]) -> bool:
    return any(ref == u or ref in u or u in ref for u in universe)


# Corporate scaffolding + industry nouns SHARED across peers — never a unique identifier for the
# subject, so they must not drive the self-referential match (else 'General'/'First' or an industry
# word like 'Solar'/'Networks'/'Electric' would drop a legitimate peer twin). The guard errs toward
# KEEPING: a leaked self-ref renders as a visible, rejectable analogue; a wrongly-dropped peer is a
# silent loss the analyst never sees.
_GENERIC_CO_WORDS: frozenset[str] = frozenset({
    "THE", "INC", "CORP", "CORPORATION", "COMPANY", "GROUP", "HOLDINGS", "HOLDING", "LTD",
    "LIMITED", "PLC", "CLASS", "COMMON", "GENERAL", "FIRST", "UNITED", "AMERICAN", "NATIONAL",
    "GLOBAL",
    "INTERNATIONAL", "BANK", "BANCORP", "FINANCIAL", "FINANCE", "CAPITAL", "TRUST", "INSURANCE",
    "ENERGY", "SOLAR", "POWER", "MOTORS", "MOTOR", "AUTO", "AIRLINES", "AIRWAYS", "PHARMACEUTICALS",
    "PHARMA", "THERAPEUTICS", "BIOSCIENCES", "TECHNOLOGIES", "TECHNOLOGY", "TECH", "SYSTEMS",
    "SYSTEM", "NETWORKS", "NETWORK", "SOFTWARE", "SEMICONDUCTOR", "INDUSTRIES", "INDUSTRIAL",
    "ENTERPRISES", "PARTNERS", "PROPERTIES", "REALTY", "RESOURCES", "MATERIALS", "MINING", "FOODS",
    "BRANDS", "STORES", "RETAIL", "HEALTH", "HEALTHCARE", "MEDICAL", "COMMUNICATIONS", "MEDIA",
    "ENTERTAINMENT", "GAMING", "SOLUTIONS", "SERVICES", "PRODUCTS", "MANUFACTURING", "ELECTRIC",
    "ELECTRONICS", "ELECTRONIC", "DIGITAL", "DATA",
})


def _self_referential_twin(tw: TwinCase, ticker: str, name: str) -> bool:
    """R2: True iff a twin names the SUBJECT itself WITHOUT an explicit resolved past period. A
    valid twin is ANOTHER company, or the subject with a dated arc ('2022-2024'). The subject is
    matched by WHOLE-TOKEN equality on its ticker or a DISTINCTIVE name word (generic/industry
    words and short tokens excluded) — NEVER a substring, so a short ticker inside another company
    ('BA' in 'Alibaba', 'KO' in 'Kohl's') or a shared generic lead ('General', 'First') cannot
    false-drop a legitimate peer twin. Errs toward keeping (a leaked self-ref stays visible)."""
    tw_tokens = set(re.findall(r"[A-Z0-9]+", tw.name.upper()))
    subj = {
        w for w in re.findall(r"[A-Z0-9]+", name.upper())
        if len(w) >= 4 and w not in _GENERIC_CO_WORDS
    }
    tkr = ticker.strip().upper()
    if len(tkr) >= 3:  # a whole-token ticker match; short tickers (≤2) collide with common words
        subj.add(tkr)
    if not (subj & tw_tokens):
        return False
    # (R2) the resolved period must appear in the twin NAME itself ('Microvast (2021–2025 arc)') —
    # a bare self-name ('Microvast Holdings') is suppressed even if a year hides in outcome/fact.
    return not re.search(r"\b(?:19|20)\d\d\b|\bFY\s?\d\d\b", tw.name, re.IGNORECASE)  # (K6) FY\d\d


def _validate(
    synth: Synthesis, mech: MechanicalLayer, ticker: str = "", name: str = ""
) -> tuple[Synthesis, list[str]]:
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

    flagged_figs: set[tuple[float, bool]] = set()  # (signed value, type) for decisive-mirror dedup

    def check_point(p: SourcedPoint, where: str, *, dedup: bool = False) -> SourcedPoint:
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
        ref_is_transcript = bool(_TRANSCRIPT_REF.search(p.source_ref))
        for n in _claim_figures(p.claim):
            if _num_traces(n):
                continue
            # key on SIGNED value + flag-type: don't let abs() collapse +N/-N (distinct facts) and
            # don't let a soft TRANSCRIPT-FIGURE on one point suppress a hard UNTRACEABLE elsewhere.
            key = (round(n, 2), ref_is_transcript)
            if dedup and key in flagged_figs:
                continue  # decisive mirror of an already-flagged bull/bear figure
            flagged_figs.add(key)
            if ref_is_transcript:
                # the figure lives in the cited call's prose, not the structured layer — route it to
                # human verification; don't brand a sourced number untraceable (that would gut a
                # high-value transcript-only point, e.g. 'the GAAP profit is a non-cash artifact').
                flags.append(
                    f"TRANSCRIPT-FIGURE '{n:g}' in {where}: '{_snip(p.claim)}' — from the cited "
                    "earnings call, not the structured facts; verify against the call"
                )
            else:
                flags.append(f"UNTRACEABLE figure '{n:g}' in {where}: '{p.claim}'")  # D4 full
        return p.model_copy(update={"cited": cited})

    bull = [check_point(p, "bull_point") for p in synth.bull_points]
    bear = [check_point(p, "bear_point") for p in synth.bear_points]
    dq = synth.decisive_question
    dq = dq.model_copy(
        update={
            "evidence_for": [check_point(p, "decisive.for", dedup=True) for p in dq.evidence_for],
            "evidence_against": [
                check_point(p, "decisive.against", dedup=True) for p in dq.evidence_against
            ],
        }
    )
    for tw in synth.twin_reference_cases:
        if tw.source != _UNVERIFIED and not _traces(tw.source, refs):
            flags.append(f"TWIN '{tw.name}' source doesn't trace — should be tagged unverified")
        numeric = _twin_numbers(f"{tw.outcome} {tw.distinguishing_fact}")
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
            if _DISTORTION_ACK.search(p.claim) and not _DISTORTION_DENIED.search(p.claim):
                continue  # the claim itself warns of the distortion + pivots off it — not anchoring
            if _PE_TERM.search(p.claim) and _CHEAP_CUE.search(p.claim):
                flags.append(
                    f"ANCHORS-ON-DISTORTED-P/E {where}: '{p.claim}' — the P/E is distorted "
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
        if (
            _MARGIN_DROP.search(p.claim)
            and not _ABS_RECON.search(p.claim)
            and not _NOT_JUST_MARGIN.search(p.claim)
        ):
            flags.append(
                f"UNRECONCILED {where}: '{p.claim}' — cites margin compression without the "
                "absolute-EBITDA reconciliation (margin % can fall while EBITDA rises)"
            )
    # G.2 false-balance (DIRECTION-AGNOSTIC): evidence_balance must be present + committed. Two
    # laundering signatures, flagged the same whether the name leans bull or bear: (a) 'mixed' over
    # a lopsided split; (b) a committed STRONG lean over a near-symmetric body whose MINORITY
    # side isn't sized-as-outweighed (the MVST defect — a 'strongly-bearish' label with a 5-bull /
    # 6-bear body). The flag sizes the minority; it never asks to delete a genuine counter-point.
    eb = (synth.evidence_balance or "").strip().lower()
    # the label, before the dash-reason (so a reason can't flip the read) — via THE shared parser
    # (verdict.split_lean, also the proposal's input); an unsplit read falls back to the whole
    # string, matching the pre-pivot behavior of ``eb.split("—")[0]`` on a dash-less read.
    _parts = split_lean(eb)
    lean = _parts[0] if _parts is not None else eb
    nb, nr = len(bull), len(bear)
    if not eb:
        flags.append(
            "evidence_balance MISSING — the synthesis must commit a balance read, never default it"
        )
    # 'mixed' must be read from the LABEL (lean), never the whole string — else a reason clause like
    # '… eroding, mixed cash generation' (a bearish read) trips the flag on a mid-sentence word.
    elif "mixed" in lean and (nb + nr) >= 3 and (min(nb, nr) == 0 or max(nb, nr) > 2 * min(nb, nr)):
        flags.append(
            f"FALSE-BALANCE? the written assessment reads 'mixed' but the bull/bear split is "
            f"lopsided ({nb} bull vs {nr} bear) — confirm genuinely mixed, not one-sided dressed "
            f"as balanced"
        )
    elif "strong" in lean and ("bear" in lean or "bull" in lean) and (nb + nr) >= 3:
        lean_bear = "bear" in lean
        maj_n, minority = (nr, bull) if lean_bear else (nb, bear)
        near_symmetric = len(minority) > 0 and maj_n < 2 * len(minority)
        if near_symmetric and not any(_OUTWEIGHED.search(p.claim) for p in minority):
            side = "bull" if lean_bear else "bear"
            flags.append(
                f"FALSE-BALANCE? the written assessment commits a strong lean but the body is "
                f"near-symmetric ({nb} bull vs {nr} bear) and the minority {side}_points aren't "
                "qualified-as-outweighed — size the minority against the lean (rule 7), or it "
                "launders a one-sided case"
            )

    # G.3 peer-comp contract: the comps facts are the CONSENSUS read the edge must RESIST. A
    # relative-valuation verdict ('cheap/rich vs peers') is only a signal WITH (a) the earned-vs-
    # residual decomposition (fundamental_deltas) OR (b) the peer-set composition — a BARE gap is
    # the consensus misread. And when comparability flags the set HETEROGENEOUS, a peer stat read
    # as a clean benchmark ignores the confidence gate. Human-review flags only: the machine POSES
    # the justified-vs-residual question; it never computes a residual or an implied upside here.
    comp = mech.peer_comps.comparability
    hetero = bool(
        comp.status is SourceStatus.PRESENT
        and comp.value
        and re.search(r"heterogen|low comparability", comp.value, re.IGNORECASE)
    )
    peer_pts = ([(p, "bull_point") for p in bull] + [(p, "bear_point") for p in bear]
                + [(p, "decisive.for") for p in dq.evidence_for]
                + [(p, "decisive.against") for p in dq.evidence_against])
    for p, where in peer_pts:
        if not (_PEER_REF.search(p.claim) and _REL_VAL_CUE.search(p.claim)):
            continue
        if not _DECOMP_REF.search(p.claim) and not _COMPARABILITY_ACK.search(p.claim):
            flags.append(
                f"PEER-COMP-BARE {where}: '{p.claim}' — presents cheap/rich vs peers as a "
                "verdict without the earned-vs-residual decomposition or the peer-set composition; "
                "POSE justified-vs-residual, never the bare gap"
            )
        # HETERO doesn't fire when the claim RESOLVES the gap to EARNED/value-trap — gating a
        # heterogeneous median only reinforces a 'discount is earned' read, never misreads it as a
        # clean CHEAP signal. Keeps the directional 'NOT cheap / premium vs peers' fires; drops the
        # CNXC-style 'discount is earned, a value trap' false fire.
        if (
            hetero
            and not _COMPARABILITY_ACK.search(p.claim)
            and not (_EARNED_RESOLVED.search(p.claim) and not _EARNED_DENIED.search(p.claim))
        ):
            flags.append(
                f"HETEROGENEOUS-BENCHMARK {where}: '{p.claim}' — leans on the peer set as a "
                "clean benchmark, but comparability flags it HETEROGENEOUS; confidence-gate every "
                "peer stat"
            )

    # R2 twin-integrity guard: a twin naming the SUBJECT is invalid unless it cites an explicit
    # resolved PAST period (a '2022-2024 arc'); drop the self-referential hallucinations (QA-only).
    # D6a single-entity guard: a twin must be ONE company — a '/'-joined pair or a 'cohort' is not a
    # single analogue → dropped; an '&' name (AT&T, S&P, Procter & Gamble) is a legitimate single
    # entity → FLAGGED for QA but RENDERED (never false-positived into a drop).
    kept_twins = []
    dropped = 0
    for tw in synth.twin_reference_cases:
        nm = tw.name
        if _self_referential_twin(tw, ticker, name):
            dropped += 1
            flags.append(
                f"TWIN self-referential '{nm}' suppressed — a twin must be ANOTHER "
                "company, or the subject with an explicit resolved past period ('2022-2024 arc')"
            )
        elif "/" in nm or "cohort" in nm.lower():
            dropped += 1
            flags.append(
                f"TWIN compound '{nm}' suppressed — a twin must be ONE company, not a "
                "'/'-joined pair or a cohort"
            )
        else:
            if "&" in nm:
                flags.append(f"TWIN ampersand-name '{nm}' — verify it is a single entity (kept)")
            kept_twins.append(tw)
    if dropped:
        flags.append(f"TWIN {dropped} invalid twin(s) suppressed")
    # R3 internal-rule leak: any 'rule N' reference in the output is a leaked internal rule → QA.
    for hit in sorted({m.group(0) for m in re.finditer(r"rule\s+\d+", blob, re.IGNORECASE)}):
        flags.append(f"RULE-LEAK '{hit}' — internal rule reference leaked into synthesis output")
    validated = synth.model_copy(
        update={
            "bull_points": bull, "bear_points": bear, "decisive_question": dq,
            "twin_reference_cases": kept_twins,
        }
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


_LITERAL_UNICODE = re.compile(r"\\u([0-9a-fA-F]{4})")


def _decode_one(m: re.Match[str]) -> str:
    """Decode one literal ``\\uXXXX`` — but ONLY to a PRINTABLE BMP char. A lone surrogate
    (0xD800–0xDFFF) crashes ``model_dump_json`` ('surrogates not allowed'); a C0/C1 control (NUL,
    newline, bell) corrupts the committed dossier.json/.md. Those are left as the literal escape."""
    cp = int(m.group(1), 16)
    if 0xD800 <= cp <= 0xDFFF:
        return m.group(0)
    ch = chr(cp)
    return ch if ch.isprintable() else m.group(0)


def _decode_escapes(obj: Any) -> Any:
    r"""Decode a literal ``\uXXXX`` the LLM sometimes emits as TEXT (opus did, in evidence_balance:
    'mixed — a' showed the raw escape, not an em-dash). Recurses dicts/lists; a real char has no
    backslash so it stays. Only ``\u`` + four hex digits decoding to a PRINTABLE non-surrogate char
    is decoded (see :func:`_decode_one`); a stray ``\underway`` (non-hex) is left alone."""
    if isinstance(obj, str):
        return _LITERAL_UNICODE.sub(_decode_one, obj)
    if isinstance(obj, dict):
        return {k: _decode_escapes(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decode_escapes(v) for v in obj]
    return obj


def _operating_drivers_digest(od: OperatingDriversExtract) -> str:
    """(PR-B §5) A salient term → value → source_ref digest of the operating-driver facts for the
    synthesis phase — the causal MECHANISM the atomized bull/bear otherwise misses. Already inside
    the facts JSON, but surfaced here so the LLM leans on it and copies the exact source_ref. One
    literal example:
      [leading_indicator] sales volume: approximately 274 megawatt hours → CIQ transcript: …Q1 2026…
    """
    out = ["=== OPERATING DRIVERS — validated, cited facts. GROUND any operating bull/bear point "
           "(volume · price · mix · capacity · client · guidance) in the relevant driver and copy "
           "its source_ref. Anchored = filings; llm-fenced = the call (already validated). "
           "A '…continues:' line is THE REST OF THAT SPEAKER'S PARAGRAPH, verbatim — read it "
           "before characterising the fact above it, because it frequently qualifies, reverses or "
           "seasonally normalises the number, and a point that contradicts it is unsupported. ==="]
    for r in od.rows:
        val = r.value if len(r.value) <= 130 else r.value[:127].rstrip() + "…"
        out.append(f"[{r.kind.value}] {r.metric}: {val} → {r.source_ref}")
        # SURFACED HERE, not left to the facts dump. BRBR's quote — "70% of RTD shake category
        # volumes were sold on price promotion" — is exact and correctly cited, and the sentence
        # after it says the figure is "in line with historical norms … DOWN sequentially from the
        # heavier promoted second quarter". The synthesis had the WHOLE transcript in its prompt
        # and still built an escalating sequence out of the quote alone, because THIS digest is
        # what it is told to ground in and copy refs from. Putting the qualifier beside the fact
        # is the intervention; leaving it in the JSON would only serve the audit.
        if r.following_context:
            ctx = (r.following_context if len(r.following_context) <= 400
                   else r.following_context[:397].rstrip() + "…")
            out.append(f"    …continues: {ctx}")
    return "\n".join(out)


def newest_guidance_date(ps: PrimarySource) -> Any:
    """The latest ``filed`` among GUIDANCE-BEARING releases, or ``None`` when none is dated.

    Computed over ALL releases, never a display window: the digest shows only the four most recent,
    and keying supersession off that window would mark a stale guide CURRENT the moment a fifth
    release carried the newest one. Nothing asserts that ``releases`` arrives newest-first.
    """
    dated = [r.filed for r in ps.releases if r.guidance and r.filed]
    return max(dated) if dated else None


def guidance_vintage_mark(filed: Any, newest: Any) -> str:
    """The vintage suffix for ONE guidance line — the single derivation both consumers share.

    TWO CONSUMERS, ONE DERIVATION, DELIBERATELY. The LLM brief got this marking on 2026-08-04 and
    the analyst's `scenario-propose` template did not — it read `drawdown_cause.revised_guidance`
    instead and printed APRIL's superseded numbers under the label "current guidance", which is the
    same defect (P2) wearing the decision aid's clothes. Two places deriving "which guide is
    current" from two different fields is how that happened; one helper is how it stops.

    Marks the LINE, never a block: a section header scopes over the reported actuals beneath it.
    """
    if filed is None:
        return " [VINTAGE UNDATED — no filing date; do not read as current]"
    if newest is None or filed == newest:
        return f" [CURRENT GUIDE, filed {filed}]"
    return (f" [SUPERSEDED — filed {filed}, replaced by the guide filed {newest}; "
            "this guide is history, not the current outlook]")


_ACCESSION = re.compile(r"(\d{10}-\d{2}-\d{6})")


def _mark_drawdown_guidance(dumped: dict[str, Any], ps: PrimarySource | None) -> None:
    """(O1) Mark `drawdown_cause.revised_guidance` with its vintage, in place.

    THE SECOND PATH. #342 marked the `primary_source` digest and the 2026-08-04 SMPL roll then
    argued the FY26 guide from APRIL anyway — because the model was reading a DIFFERENT field.
    `synthesize` excludes `primary_source` from the facts dump and swaps in the marked digest, but
    `drawdown_cause` goes into that dump RAW, carrying the drawdown-moment guide's verbatim text
    with no indication that a newer guide exists. On SMPL that text is April's, and it is the
    source of the false bear point: `bear[1]`'s `-22% to -19%` appears ONLY here, never in the
    structured guidance.

    The field is CORRECTLY historical — `mechanical._revised_guidance` walks the DRAWDOWN 8-Ks and
    answers "what did management say at the gap". It was simply unlabelled as history. So this
    marks rather than drops: the cut sequence is itself evidence, and the same
    `guidance_vintage_mark` both other consumers use states which guide is current.

    The filing DATE is not on the field — only its accession is — so it is matched back to the
    release that carries one. No date ⇒ the UNDATED mark, never a guess.
    """
    dc = dumped.get("drawdown_cause")
    rg = (dc or {}).get("revised_guidance")
    if not isinstance(rg, dict) or not rg.get("value"):
        return
    filed = None
    acc = _ACCESSION.search(str(rg.get("source_ref") or ""))
    if acc is not None and ps is not None:
        for r in ps.releases:
            if acc.group(1) in str(r.source_ref or ""):
                filed = r.filed
                break
    mark = guidance_vintage_mark(filed, newest_guidance_date(ps) if ps is not None else None)
    # THE MARK LEADS, it does not trail. This field is a multi-line verbatim outlook block, so a
    # mark appended at the end is read AFTER the numbers it qualifies — and being read after the
    # numbers is exactly how April's guide became a bear point. The digest can mark inline because
    # each guidance line IS one line; a paragraph has only one position that warns before the
    # numbers are consumed, and it is the front.
    rg["value"] = f"{mark.strip()}\n{rg['value']}"


def _fragments(sl: Sleeve) -> dict[str, str]:
    """The six strings the synthesis prompt varies by BOOK. Everything else in the template —
    cite-or-drop, anti-balance, the no-conclusion contract, the peer-comp discipline — is INVARIANT,
    and that asymmetry is the whole argument for a registry over a second prompt: only the two CASE
    DEFINITIONS and the subject they concern were ever sleeve-specific."""
    return {
        "subject": sl.subject, "tool_subject": sl.tool_subject,
        "bull_case": sl.bull_case, "bear_case": sl.bear_case,
        "both_cases": sl.both_cases, "twin_outcome": sl.twin_outcome,
    }


def _fill(node: Any, frag: dict[str, str]) -> Any:
    """Substitute the fragments through the tool schema, structure untouched.

    WALKS THE TREE rather than formatting a rendered blob: the schema is a nested dict the LLM
    client consumes as JSON, so the substitution has to happen in the string LEAVES and leave every
    key, list and nesting level exactly as it was. `str.format` is deliberate — a stray brace in
    prompt prose would raise here rather than silently producing a malformed schema."""
    if isinstance(node, str):
        return node.format(**frag)
    if isinstance(node, dict):
        return {k: _fill(v, frag) for k, v in node.items()}
    if isinstance(node, list):
        return [_fill(v, frag) for v in node]
    return node


def tool_for(sleeve: str) -> dict[str, Any]:
    """The synthesis tool schema for ``sleeve``.

    REFUSES an unlisted sleeve rather than falling back to overshoot: a silent fallback is exactly
    the defect this registry exists to remove — it is how a megacap came to be asked what broke."""
    sl = BY_KEY[require_sleeve(sleeve, where="synthesis.tool_for")]
    out: dict[str, Any] = _fill(_TOOL_TEMPLATE, _fragments(sl))
    return out


def system_for(sleeve: str) -> str:
    """The system prompt for ``sleeve``. Same refusal as :func:`tool_for`."""
    sl = BY_KEY[require_sleeve(sleeve, where="synthesis.system_for")]
    return _SYSTEM_TEMPLATE.format(**_fragments(sl))


#: The OVERSHOOT prompt, kept under the historical names because it is the LIVE book's text and
#: every existing reader (the QA layer, the digests, the tests) already names them. Byte-identity
#: with the pre-registry strings is TEST-PINNED — the live fleet's prompt cannot drift as a side
#: effect of making the other books possible.
SYNTHESIS_TOOL: dict[str, Any] = tool_for(DEFAULT_SLEEVE)
_SYSTEM: str = system_for(DEFAULT_SLEEVE)


def _primary_source_digest(ps: PrimarySource) -> str:
    """(RC-1 C) A term → value → source_ref digest of the primary-source cross-checks for the LLM
    synthesis phase — VERBATIMS EXCLUDED (provenance is on-demand, never LLM input). Both
    going-concern states are facts (SUBSTANTIAL DOUBT stated vs none-stated-checked); a filing that
    STATES no near-term wall is NOT_STATED-as-KNOWN (not UNKNOWN); a QUALITATIVE guide is marked.
    One literal example:
      event impact: reduce revenue 135.0–145.0 (2026 annualized) → 8-K 0001193125-26-239351 EX-99.1
    """
    out = ["=== PRIMARY-SOURCE CROSS-CHECKS (8-K EX-99.1 + latest 10-Q) — "
           "term → value → source_ref; verbatims EXCLUDED ==="]

    def emit(term: str, s: Any) -> None:
        if s.status is SourceStatus.PRESENT and s.value:
            out.append(f"{term}: {str(s.value).replace(chr(10), ' · ')} → {s.source_ref}")

    emit("self-funding (two-input read)", ps.self_funding)
    emit("wall coherence (filing ≤12m vs CIQ panel)", ps.wall_coherence)
    emit("EBITDA-basis triangulation", ps.basis_triangulation)
    emit("guide verification", ps.guide_verification)
    fil = ps.filing
    if fil is not None:
        gc = fil.going_concern
        if gc is not None:
            state = ("SUBSTANTIAL DOUBT stated" if gc.substantial_doubt
                     else "none stated (checked, absent)")
            out.append(f"going-concern: {state}{'; plans present' if gc.plans else ''} "
                       f"→ {gc.source_ref}")
        mw = fil.maturity_wall
        if mw is not None:
            val = (f"${mw.within_12m_total}M due ≤12m" if mw.within_12m_total is not None
                   else "NOT_STATED — filing states no near-term maturity (KNOWN, not UNKNOWN)")
            out.append(f"maturity wall (filing basis): {val} → {fil.source_ref}")
        cc = fil.concentration
        for c in (cc.customers if cc is not None else []):
            kind = " (disclosed FLOOR)" if c.value_kind == "floor" else ""
            prior = f" (prior {c.prior_pct}%)" if c.prior_pct is not None else ""
            out.append(f"customer concentration: {c.name} {c.pct}%{kind}{prior} "
                       f"→ {cc.source_ref if cc is not None else ''}")
    recent = ps.releases[:4]  # the trailing ~year of releases — the LTM window + recent trend
    # THE GUIDE HISTORY GETS ITS OWN WINDOW, because one cap on the raw release list was spending
    # slots on releases that carry no guidance and dropping ones that do (2026-08-12). Measured on
    # the committed fleet: AORT and CNXC each lost a guidance-bearing release and **NCNO lost two**,
    # while guidance-LESS releases sat inside the window. That defeats the mark's own purpose — the
    # comment below says the guidance history IS a bear point and superseded releases must stay —
    # so the digest was dropping the evidence it exists to preserve, silently enough that the note
    # counted "older release(s)" without saying any of them carried a guide.
    #
    # TWO WINDOWS, NOT A BIGGER ONE: the content window stays at 4 (reconciliation, one-offs and
    # event impacts are LTM-shaped and a wider window would just add tokens), and guidance selects
    # the 4 most recent releases that actually carry some. They usually coincide; where they do
    # not, this is the difference between showing a cut sequence and implying there wasn't one.
    guided = [r for r in ps.releases if r.guidance][:4]
    omitted_guided = sum(1 for r in ps.releases if r.guidance) - len(guided)
    if len(ps.releases) > len(recent):
        tail = (f"; {omitted_guided} of them carried guidance" if omitted_guided else "")
        out.append(f"(note: {len(ps.releases) - len(recent)} older release(s) omitted from the "
                   f"digest — the four most recent are shown{tail}; full set in the JSON)")
    # WHICH GUIDE IS CURRENT — derived from the filing dates, which are already known.
    #
    # WHY: the digest emitted every release's guidance as `guidance (metric period): low–high →
    # source_ref`, with NO DATE AND NO ORDER. On SMPL that put July's `net sales 2026: 1,345–1,355`
    # and April's `1,310–1,350` side by side as equals, and the synthesis argued the FY26 guide from
    # the APRIL filing — audit defect P2, returning through the brief after the extractor was
    # fixed. The mechanical layer was right the whole time; `current_guide` even names the July 8-K.
    # Nothing carried that into the digest. 9 of 11 names carry more than one guidance-bearing
    # release (NCNO five, AORT/CNXC/VRRM four), so SMPL was among the LEAST exposed.
    #
    # MARK, NEVER DROP: the guidance history IS a bear point — SMPL's three-step cut sequence is
    # evidence — so superseded releases stay in the digest and merely stop looking current.
    #
    # DATES ONLY, no heuristic and no ranking. A release whose `filed` is absent cannot be ordered,
    # so it is labelled UNDATED rather than assumed current or stale — MVST and FUBO are that case.
    _newest = newest_guidance_date(ps)
    # The union, in the record's own order (most-recent first). A release earns its place by being
    # in the content window OR by carrying guidance the guide window keeps; each block below then
    # asks which window it is in, so neither leaks into the other.
    for r in [x for x in ps.releases if x in recent or x in guided]:
        # THE MARK GOES ON THE GUIDANCE LINE, NOT ON A BLOCK HEADER — and the first cut of this
        # change got that wrong in a way that would have done real harm. A section header reading
        # "SUPERSEDED … history, NOT the company's current outlook" visually scoped over
        # EVERYTHING that followed it: on SMPL that was April's guidance (correct) AND the Q2/Q1/
        # FY2025 REPORTED ACTUALS and the $60.9M Atkins impairment (all facts, none superseded) —
        # including the very figure 19c forces the synthesis to cite. It also bled across the
        # next guidance-less release, which emits no header of its own. A per-line mark has no
        # scope to creep and nothing to bleed into.
        _v = guidance_vintage_mark(r.filed, _newest)
        for g in (r.guidance if r in guided else []):
            # A CHANGE IS LABELLED AS ONE. "-350–-300 bps" printed like a level reads as a gross
            # margin of -350%, which is the 100x error this basis field exists to prevent.
            if g.qualitative:
                v = "QUALITATIVE (no number stated)"
            elif getattr(g, "basis", "level") == "change":
                v = f"CHANGE of {g.low}–{g.high} {g.unit} vs the prior period"
            else:
                v = f"{g.low}–{g.high}"
            out.append(f"guidance ({g.metric} {g.period}): {v}{_v} → {g.source_ref}")
        # THE CONTENT WINDOW, unchanged at 4. A release pulled in only for its guide history does
        # not also widen the LTM-shaped blocks — that would be a bigger digest by accident rather
        # than the targeted one this fix intends.
        for rv in (r.reconciliation if r in recent else []):
            out.append(f"reconciliation ({rv.metric} {rv.period}): {rv.value} → {rv.source_ref}")
        for oo in (r.one_offs if r in recent else []):
            out.append(f"one-off charge: ${oo.amount}M {oo.description[:44]} → {oo.source_ref}")
        for ei in (r.event_impacts if r in recent else []):
            rng = f"{ei.low}–{ei.high}" if ei.low is not None else "unquantified"
            out.append(f"event impact: {ei.effect} {ei.metric} {rng} ({ei.period}) "
                       f"→ {ei.source_ref}")
    return "\n".join(out)


def synthesize(
    mech: MechanicalLayer, *, llm: LlmClient, ticker: str, name: str,
    transcript: str | None = None, sleeve: str = DEFAULT_SLEEVE,
) -> tuple[Synthesis | None, list[str], str]:
    """Run the fenced synthesis → (synthesis|None, flags, log). Fail-loud, never fabricates. The
    ``transcript`` (a mechanically-bounded slice — NOT embedded in the dossier) is QUALITATIVE
    context only; no numbers are derived from it and points still bind to the mechanical facts."""
    # (RC-1 C) the raw primary_source (releases/filing) carries VERBATIMS — provenance, not input.
    # Exclude it from the dump and feed the curated term→value→source_ref digest instead. Its
    # source_refs still live in `mech`, so a cited primary-source ref traces through validation.
    _dumped = mech.model_dump(exclude={"primary_source"})
    _mark_drawdown_guidance(_dumped, mech.primary_source)
    facts = json.dumps(_dumped, indent=2, default=str)
    user = (
        f"Name: {name} ({ticker}). The ONLY facts you may use — each carries a source_ref to copy "
        f"verbatim when you cite it:\n\n{facts}"
    )
    if mech.primary_source is not None:
        user += "\n\n" + _primary_source_digest(mech.primary_source)
    if mech.operating_drivers is not None and mech.operating_drivers.rows:
        user += "\n\n" + _operating_drivers_digest(mech.operating_drivers)
    if transcript:
        user += (
            "\n\n=== Earnings-call transcripts, each fenced by a '--- <call> ---' label. With the "
            "latest and prior quarter both on file, COMPARE posture quarter-over-quarter where it "
            "shifts. Prepared remarks + Q&A, mechanically bounded. QUALITATIVE management-posture "
            "context ONLY. Derive NO numbers FROM THIS TEXT — any transcript figure you need has "
            "already been extracted, validated, and cited as an `operating_drivers` fact above; "
            "cite THAT source_ref, never a number you read here. A point resting on posture cites "
            "the 'CIQ transcript' source_ref from the facts. ===\n"
            + transcript
        )
    # PER-BOOK FRAMING, one prompt. `sleeve` defaults to overshoot so every existing caller keeps
    # the byte-identical live prompt; the followed route passes the name's own book.
    #
    # BUILT ONCE AND USED FOR BOTH THE LOG AND THE CALL. The first cut logged the module-level
    # `_SYSTEM` — the OVERSHOOT constant — while sending `system_for(sleeve)`, so every quality
    # assembly persisted an `llm_call.log` claiming it had been framed as a sharply de-rated
    # overshoot name. That is a FALSE PROVENANCE RECORD in a committed audit artifact: the one
    # document whose entire purpose is to answer "what was this model actually asked", answering
    # it wrongly, in exactly the case the sleeve work exists to serve. Two names, one binding —
    # the log cannot describe a prompt the call did not receive.
    system, tool = system_for(sleeve), tool_for(sleeve)
    log_parts = [f"model: {llm.model}", "", f"=== SLEEVE === {sleeve}",
                 "", "=== SYSTEM ===", system, "", "=== USER ===", user]
    try:
        raw = llm.extract(system=system, user=user, tool=tool)
    except LlmError as exc:
        log_parts += ["", "=== ERROR ===", str(exc)]
        return None, [f"LLM synthesis failed (no usable output): {exc}"], "\n".join(log_parts)
    # USAGE IN THE LOG, so "(likely truncated)" below can be CHECKED instead of believed. On
    # SMPL 2026-08-04 that message was emitted about a response using a fifth of its budget.
    _u = getattr(llm, "last_usage", None)
    if _u:
        log_parts += ["", "=== USAGE ===", json.dumps(_u)]
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
    synth, flags = _validate(_parse(_decode_escapes(raw)), mech, ticker=ticker, name=name)
    return synth, flags, "\n".join(log_parts)


# (P2) pending-claim patterns — a synthesis line asserting a fact is not-yet-available.
_PENDING_RE = re.compile(
    r"not extracted|extract(?:ion)? pending|pending (?:from|extraction)|not (?:yet )?parsed|"
    r"must be read|to be (?:read|extracted)|awaiting extraction|not captured|not in this data|"
    r"not in the supplied facts|not restated|"  # (K6) additions; subject-matching unchanged
    r"read the .{0,30}(?:8-K|filing|exhibit|agreement)",
    re.IGNORECASE,
)
# (P2) SUBJECT patterns — SPECIFIC to a mechanical block so a genuine opacity gap is NOT flagged
# (e.g. "no 99.1 revised-guidance exhibit parsed" — revised_guidance really IS UNKNOWN; never bare
# "8-K", which appears in many honest claims).
_COVENANT_SUBJ = re.compile(
    r"covenant term|covenant detail|conversion (?:price|rate|mechanic|term)", re.IGNORECASE)
_MATURITY_SUBJ = re.compile(
    r"notice of conversion|maturity (?:resolution|event)|term loan.{0,40}(?:convert|resol|repaid)|"
    r"(?:convert|resol|repaid).{0,40}term loan|resolution of the .{0,30}loan",
    re.IGNORECASE,
)
# (RC-1 C) primary-source contradiction subjects — a synthesis claim that conflicts with a PRESENT
# primary-source fact. Direct factual conflicts (not pending-shaped), each subject-specific.
_UNQUANTIFIED_RE = re.compile(  # 'the revenue impact is not quantified in the facts' — but it IS
    r"not (?:been )?quantif|un-?quantif|(?:magnitude|impact|size|amount|scale)\s"
    r"(?:is |remains |are )?(?:unclear|unknown|not (?:clear|known|disclosed|quantif))|"
    r"no (?:disclosed |stated |specific )?(?:figure|number|range|dollar|magnitude)",
    re.IGNORECASE,
)
_SURVIVAL_SAFE_RE = re.compile(  # survival framed safe while the 10-Q states SUBSTANTIAL DOUBT.
    # A genuine denial NAMES the thing denied: 'no/not-a going-concern', 'no substantial doubt', or
    # a going-concern PREDICATE (doubt/risk/…) negated by a DENIAL word (apply/present/material/…).
    # That denial-word whitelist is the GATE keeping benign gap-acks quiet ('going-concern plans are
    # NOT synthesized/extracted/read' — those verbs aren't denials). REPLACES the old bare
    # 'going-concern … {0,15} not' proximity arm that over-matched them (the incident) while
    # RECOVERING the genuine 'going-concern <predicate> is/does not <denial>' class it also carried.
    r"no going[- ]concern|not a going[- ]concern|no substantial doubt|"
    r"going[- ]concern\b[^.]{0,25}?\bnot\b[^.]{0,15}?\b"
    r"(?:appl(?:y|ies|icable)|warranted|present|material|issue|concern|risk|problem|threat)\b|"
    r"survival (?:is )?(?:not (?:at|a)\b|assured|secure)|no solvency (?:risk|concern)|"
    r"comfortably (?:solvent|funded|capitalized)",
    re.IGNORECASE,
)
_WALL_DIVERGE_RE = re.compile(  # claims the filing wall / CIQ panel diverge while they AGREE
    r"(?:wall|panel|maturit\w+|filing)\b.{0,45}(?:understate|overstate|diverge|conflict|mismatch|"
    r"discrepan|disagree|contradict|inconsist)|(?:understate|overstate|diverge|conflict|mismatch|"
    r"discrepan|disagree|contradict|inconsist)\w*\b.{0,45}(?:wall|panel|maturit\w+)",
    re.IGNORECASE,
)



#: A material figure below this is not worth guarding and cannot be matched reliably — a bare "3"
#: collides with any prose ("3.6%", "3 quarters"), and a $3M writedown is not the class of error
#: this exists to catch. Measured while building it: an unanchored matcher scored 14 spurious hits
#: on 3.0 and matched 391.9 against "$1,392M" REVENUE.
MATERIAL_FIGURE_FLOOR_MUSD = 10.0


def _figure_cited(prose: str, value: float) -> bool:
    """Is ``value`` cited in ``prose`` AS A DOLLAR FIGURE?

    STRICT BY NECESSITY. The figure must carry a currency or scale marker, because a bare number
    matches everything: while measuring the base rate, an unanchored form reported 391.9 as cited
    when the only match was ``$1,392M`` of REVENUE, and reported 3.0 as cited off ``3.6%``. A guard
    that reads a false citation is worse than no guard — it certifies the page.

    SCALE-AWARE (2026-07-30). Rows are stored in $M and the first cut only matched millions forms,
    so ``$1.5bn`` against a row holding −1,523.3 read as UNCITED and the guard would have REFUSED a
    correct page. Not hypothetical: −1,523.3 is CNXC's goodwill impairment and one of only two
    guarded figures on the corpus, so the blind spot sat exactly where the guard applies — and it
    blocked re-assembling the name. Past $1bn a figure is normally written in billions; the same
    quantity at the scale a human would use is the same citation.

    THE TOLERANCE IS NOT WIDENED, ONLY THE SCALE. ``$391M`` (truncation) and ``$390M`` (two
    significant figures) against 391.9 stay uncited, and ``$0.4bn`` stays uncited for the same
    reason: accepting a 2-s.f. restatement would let a nearby-but-different figure satisfy the
    check, which is the false certification this guard exists to prevent."""
    a = abs(value)
    forms = {f"{a:.1f}", f"{a:.0f}", f"{a:,.1f}", f"{a:,.0f}"}
    # ``392.0`` — the rounded value written to one decimal. The set above cannot produce it: .1f of
    # 391.9 is "391.9" and .0f is "392", never "392.0".
    forms |= {f"{round(a):.1f}", f"{round(a):,.1f}"}
    for form in forms:
        e = re.escape(form)
        if re.search(rf"\$\s?{e}\s?(?:M\b|mm\b|million)", prose, re.I):
            return True
        if re.search(rf"(?<![\d.,]){e}\s?(?:M\b|million)", prose, re.I):
            return True
    if a < 1000.0:
        return False   # under $1bn nobody writes it in billions; offering the form only adds risk
    b = a / 1000.0
    # 1, 2 and 3 dp. THE 1-DP FORM LOSES PRECISION THE MILLIONS PATH KEPT, and that is a real cost
    # accepted deliberately: "$1.5bn" spans a ±50M bucket, so if TWO material rows ever landed in
    # one bucket, citing either would satisfy the other. Today's corpus has three distinct guarded
    # figures and no collision, and detecting one needs cross-figure context this function does not
    # have (``uncited_material_figures`` holds it) — so the limitation is PINNED rather than fixed,
    # and the fix belongs in the caller if a collision ever appears. 3 dp is here because "$1.523bn"
    # is an EXACT citation of −1,523.3 and was being refused — the same false refusal, one scale up.
    bn = {f"{b:.1f}", f"{b:.2f}", f"{b:.3f}"}
    # The bare integer ONLY when the value really is that round. "$2bn" is a fair citation of
    # 2,000.4 and a LOSSY one of 1,523.3, and the second is the case this must not accept.
    # THRESHOLD IS RELATIVE-ERROR MATCHED, and the first cut was not. At 0.05 this accepted "$2bn"
    # for 1,951.0 — 2.5% off — while the millions path REFUSES "$391M" for 391.9 at 0.23%. An order
    # of magnitude looser on the one branch whose whole claim was "scale, not tolerance", and it is
    # the widening this guard exists to prevent: a nearby-but-different figure satisfying the check.
    # 0.005 (±$5M of a round billion) puts the worst accepted error at ~0.25%, in line with the
    # millions path. It is NOT the ±50M bucket of the 1-dp form above — that bucket is the price of
    # a form humans actually write, whereas the bare integer is a convenience with an exact
    # alternative ("$2.0bn") already accepted.
    if abs(b - round(b)) < 0.005:
        bn.add(f"{round(b):d}")
    for form in bn:
        e = re.escape(form)
        if re.search(rf"\$\s?{e}\s?(?:bn\b|b\b|billion)", prose, re.I):
            return True
        # no bare-``b`` here: without the ``$`` a lone "b" is far too common to key on
        if re.search(rf"(?<![\d.,]){e}\s?(?:bn\b|billion)", prose, re.I):
            return True
    return False


#: THE FIELDS THAT CARRY CLAIMS — the single list, because more than one reader needs it. The
#: mechanical-only refresh (`vinci.dossier.refresh`) asks the same question of a STORED dict rather
#: than a model, so it cannot call `_synthesis_prose`; retyping the list there missed
#: `decisive_question` and `evidence_balance`, which would have let a figure cited ONLY in those
#: read as uncited and slip the refusal. Adding a claim block means adding it here, once.
SYNTHESIS_CLAIM_LISTS: tuple[str, ...] = ("bull_points", "bear_points", "key_unknowns")
SYNTHESIS_CLAIM_SCALARS: tuple[str, ...] = ("decisive_question", "evidence_balance")


def _synthesis_prose(synth: Synthesis) -> str:
    """Every free-text claim the synthesis makes. The guard reads the PROSE, because that is where
    the reader meets a number — a figure present in a structured field but absent from the argument
    is exactly the gap (item 19c)."""
    out: list[str] = []
    for name in SYNTHESIS_CLAIM_LISTS:
        for p in (getattr(synth, name, None) or []):
            out.append(p if isinstance(p, str) else str(getattr(p, "claim", "") or ""))
    for attr in SYNTHESIS_CLAIM_SCALARS:
        v = getattr(synth, attr, None)
        if isinstance(v, str):
            out.append(v)
    return " ".join(out)


def uncited_material_figures(synth: Synthesis, mech: MechanicalLayer) -> list[str]:
    """(item 19c) A MATERIAL financial-summary figure that the synthesis prose never states.

    THE INCIDENT, and it is why this is presence-based rather than plausibility-based. SMPL's bear
    case was CORRECT on 2026-07-29 — "$60.9M Atkins impairment (FY25) plus $391.9M LTM asset
    writedown" — and WRONG on 2026-07-30 from identical inputs: "$60.9M ... plus a $249M
    OWYN/Atkins brand-asset impairment". The table said -60.9 and -391.9; the prose said 60.9 and
    249. **Synthesis correctness is stochastic**, so every figure in every run is a fresh roll and
    no amount of prompt care removes the need for a check.

    THE BAD RUN WAS NOT FABRICATING: $249M is a real Q2 charge, cited as though it were the total.
    So the check cannot ask "is this figure plausible" — every number in it was. It asks the one
    question that separates the two runs: **does the material row's own figure appear at all?**
    """
    fs = getattr(mech, "financial_summary", None)
    ann = getattr(getattr(fs, "annual", None), "value", None) if fs is not None else None
    rows = list(getattr(ann, "rows", []) or []) if ann is not None else []
    cols = list(getattr(ann, "columns", []) or []) if ann is not None else []
    # ESTIMATE COLUMNS ARE OUT OF SCOPE. The summary carries FY26E/FY27E and a per-column
    # `is_estimate` mask; demanding the prose state a FORECAST would require the argument to cite a
    # projection as though it were a fact. No material value lands in an estimate column today, so
    # this is a latent false positive rather than a live one — closed now because the flag exists
    # and ignoring it would be an unasserted assumption about which columns are actuals.
    est = list(getattr(ann, "is_estimate", []) or []) if ann is not None else []

    def is_forecast(i: int) -> bool:
        if i < len(est):
            return bool(est[i])
        return bool(i < len(cols) and str(cols[i]).rstrip(")").endswith("E"))

    prose = _synthesis_prose(synth)
    out: list[str] = []
    for r in rows:
        if not getattr(r, "material", False):
            continue
        # ONE FIGURE, REPORTED ONCE. A charge commonly repeats across columns — CNXC's -1,523.3
        # appears in both FY25 and LTM — and citing it once satisfies the reader for both. Keyed by
        # value so the refusal names a number rather than a grid position, and so the count is a
        # count of FIGURES rather than of cells.
        seen: dict[float, list[str]] = {}
        # THE LATEST ACTUAL MATERIAL VALUE. Columns run OLDEST -> NEWEST with every estimate column
        # last — verified across all eleven committed summaries, not assumed, and pinned
        # structurally by `test_actual_columns_precede_estimate_columns`. So the last write here
        # is the most recent ACTUAL: forecast columns `continue` above it and never overwrite it.
        latest: float | None = None
        for i, v in enumerate(getattr(r, "values", []) or []):
            if not isinstance(v, (int, float)) or abs(v) < MATERIAL_FIGURE_FLOOR_MUSD:
                continue
            if is_forecast(i):
                continue
            seen.setdefault(float(v), []).append(cols[i] if i < len(cols) else str(i))
            latest = float(v)
        if not seen or latest is None:
            continue
        # THE LARGEST MATERIAL VALUE **AND** THE LATEST ACTUAL ONE.
        # (Operator ruling 2026-08-03; AMENDED ON REVIEW the same day — see the last paragraph.)
        #
        # PER-VALUE WAS UNSATISFIABLE, demonstrated: five independent rolls on SMPL each cited ONE
        # of `Asset Writedown` FY25 −60.9 and LTM −391.9, never both — because they are ONE EVENT at
        # two horizons (LTM 391.9 = YTD FY26 331.0 + FY25 Q4 60.9) and an analyst narrates one. The
        # old keying turned that into two independent demands and blocked the name entirely.
        #
        # PER-ROW WOULD PASS THE ORIGINAL DEFECT: citing $60.9M beside a row showing −392 is exactly
        # the audit's P1, and a rule satisfied by ANY figure on the row accepts it.
        #
        # LARGEST-ONLY WAS ALSO WRONG, AND THIS IS THE AMENDMENT. The argument for it was that
        # citing 391.9 without 60.9 misleads nobody "because 60.9 is a COMPONENT of it" — but that
        # containment is a fact about SMPL, NOT a fact the row carries, while `max()` applies to
        # every row. Where the two figures are UNRELATED events in different periods (an old $500M
        # impairment, an unrelated current $25M one), largest-only lets the CURRENT period go
        # unmentioned — a silent omission in a MATERIALITY guard, which is the one place a known
        # hole must not ship. Demanding the latest actual as well closes it WITHOUT inventing a
        # roll-up relationship the data does not represent.
        #
        # SATISFIABILITY IS PRESERVED because the demand is keyed by VALUE, not by cell: when the
        # largest figure IS the latest one the two demands collapse into a single citation. That is
        # the live corpus — SMPL's −391.9 and CNXC's −1,523.3 are each both largest and latest — so
        # this costs nothing today and refuses exactly the case that motivated the amendment.
        biggest = max(seen, key=abs)
        for v in [biggest] if biggest == latest else [biggest, latest]:
            if not _figure_cited(prose, v):
                out.append(f"{r.label} {'/'.join(seen[v])} = {v:,.1f}")
    return out


def contradiction_flags(synth: Synthesis, mech: MechanicalLayer) -> list[str]:
    """(P2) The durable guard this incident earns: flag a synthesis pending-claim ('not extracted',
    'must be read', …) whose SUBJECT is a mechanical block that IS present — the failure where a
    pointer-shaped input made the LLM report as pending a fact the mechanical layer actually holds.
    QA-channel; names the field. A pending-claim about a genuinely-UNKNOWN block (a real
    opacity gap) is left alone — the subject match is specific, never a bare '8-K'."""
    cs = mech.capital_structure
    # (CC-3) require an actually-PRESENT term VALUE, not merely the row CONTAINER being PRESENT: an
    # all-UNKNOWN covenant_term_rows block is a genuine opacity gap, so an honest "must be read from
    # the 8-K" about it is NOT a contradiction — keying on the container alone false-positives.
    covenant_present = (cs is not None and cs.covenant_term_rows is not None
                        and cs.covenant_term_rows.status is SourceStatus.PRESENT
                        and any(r.value.status is SourceStatus.PRESENT
                                for r in (cs.covenant_term_rows.value or [])))
    maturity_present = (cs is not None and cs.maturity_event is not None
                        and cs.maturity_event.status is SourceStatus.PRESENT)
    # (RC-1 C) primary-source signals — a synthesis claim conflicting with these PRESENT facts is a
    # contradiction. quantified: an event impact the 8-K states a $ range for (Avis); gc_doubt: the
    # 10-Q states substantial doubt; wall_agrees: the filing wall cross-validates the CIQ panel.
    ps = mech.primary_source
    quantified = {ei.metric.lower() for r in (ps.releases if ps is not None else [])
                  for ei in r.event_impacts if ei.low is not None}
    gc = ps.filing.going_concern if ps is not None and ps.filing is not None else None
    gc_doubt = gc is not None and gc.substantial_doubt
    wall_agrees = (ps is not None and ps.wall_coherence.status is SourceStatus.PRESENT
                   and "AGREES" in (ps.wall_coherence.value or ""))
    if not (covenant_present or maturity_present or quantified or gc_doubt or wall_agrees):
        return []
    texts: list[tuple[str, str]] = []
    if synth.evidence_balance:
        texts.append(("evidence_balance", synth.evidence_balance))
    texts += [("bull_point", p.claim) for p in synth.bull_points]
    texts += [("bear_point", p.claim) for p in synth.bear_points]
    texts += [("key_unknown", u) for u in synth.key_unknowns]
    texts.append(("decisive_question", synth.decisive_question.question))
    texts += [("decisive.for", p.claim) for p in synth.decisive_question.evidence_for]
    texts += [("decisive.against", p.claim) for p in synth.decisive_question.evidence_against]
    flags: list[str] = []
    for where, txt in texts:
        low = txt.lower()
        if _PENDING_RE.search(txt):  # (P2) pending-claim about a PRESENT block
            if covenant_present and _COVENANT_SUBJ.search(txt):
                flags.append(f"CONTRADICTION ({where}): synthesis calls covenant terms pending — "
                             f"but covenant_term_rows IS present. Claim: “{_snip(txt)}”")
            elif maturity_present and _MATURITY_SUBJ.search(txt):
                flags.append(f"CONTRADICTION ({where}): calls the maturity resolution pending — "
                             f"but maturity_event IS present. Claim: “{_snip(txt)}”")
        # (RC-1 C) primary-source contradictions — a claim that conflicts with a PRESENT filing fact
        if quantified and _UNQUANTIFIED_RE.search(txt) and any(mt in low for mt in quantified):
            flags.append(f"CONTRADICTION ({where}): calls the event impact unquantified — but the "
                         f"8-K EX-99.1 states its $ range. Claim: “{_snip(txt)}”")
        if gc_doubt and _SURVIVAL_SAFE_RE.search(txt):
            flags.append(f"CONTRADICTION ({where}): frames survival safe — but the latest 10-Q "
                         f"states SUBSTANTIAL DOUBT (going concern). Claim: “{_snip(txt)}”")
        if wall_agrees and _WALL_DIVERGE_RE.search(txt):
            flags.append(f"CONTRADICTION ({where}): claims the wall/panel diverge — but the filing "
                         f"AGREES with the CIQ panel (same window). Claim: “{_snip(txt)}”")
    return flags
