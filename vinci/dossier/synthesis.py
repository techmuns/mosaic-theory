"""The SYNTHESIS layer — the project's configured LLM, **fenced**.

The model is given ONLY the mechanical layer's source-bound facts (not the web, not its own memory),
and forced through a tool whose schema is the verdict-free :class:`Synthesis` shape — there is no
field for a conclusion, so it cannot render one. Its output is then validated, not trusted:

- every bull/bear point must cite a ``source_ref`` that IS one in the input — the same text, never a
  fragment of one, never empty (uncited → flagged);
- every number must trace to the FACT ITS POINT CITES (untraceable → flagged), unless cited to the
  earnings-call transcript, where a prose figure earns a soft 'verify against the call' note;
- twin analogues must be source-bound or tagged ``[LLM-suggested, unverified]``, and never numeric;
- the whole output is linted for directional/recommendation language and flagged for human review.

The model + the full raw output are logged. The LLM never produces a number that feeds the spread —
the dossier writes nothing to the ledger.
"""

from __future__ import annotations

import functools
import json
import re
import time
import warnings
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_FLOOR, Decimal
from typing import Any, cast

from vinci.dossier.materiality import UNUSUAL_ITEM_LABELS
from vinci.dossier.schemas import (
    FIGURE_OPERATIONS,
    DecisiveQuestion,
    DrawAgreement,
    FigureCite,
    ForwardConsensus,
    MechanicalLayer,
    OperatingDriver,
    OperatingDriversExtract,
    PrimarySource,
    SourcedPoint,
    SourceStatus,
    Synthesis,
    TwinCase,
)
from vinci.dossier.verdict import COMMITTED_LEANS, GATE_RULE, draw_gate, lean_key, split_lean
from vinci.graph.llm import LlmClient, LlmError
from vinci.sleeves import BY_KEY, DEFAULT_SLEEVE, Sleeve, require_sleeve
from vinci.verbatim import comparison_key

_UNVERIFIED = "[LLM-suggested, unverified]"
# unit renderings an LLM uses for the same stored number (fraction↔%, raw↔K/M/B) — for number-trace
_TRACE_SCALES = (1.0, 1e2, 1e-2, 1e3, 1e-3, 1e6, 1e-6, 1e9, 1e-9)
_NUM = re.compile(r"-?\d[\d,]*\.?\d+|-?\d+")
# Calendar/period LABELS that _NUM would wrongly extract as figures and the trace then flags as
# untraceable: 'FY21'/'FY25' (→21/25), 'Q1', 'fiscal 2025', '90 days ago' (→90), '8 quarters'. These
# are not CLAIMED values — skip a number whose immediate context is a fiscal/quarter prefix or a
# time-unit suffix. (Bare 4-digit years are NOT skipped — they collide with real $ figures.)
_CAL_BEFORE = re.compile(r"(?:\bFY|\bfiscal\s*|\bQ)\s*$", re.IGNORECASE)
_TIME_UNIT = r"(?:days?|weeks?|months?|quarters?|qtrs?|years?)"
_CAL_AFTER = re.compile(rf"^\s*{_TIME_UNIT}\b", re.IGNORECASE)
# In a synthesis CLAIM a WHOLE-NUMBER duration is the same label hyphenated, or abbreviated to "y" —
# "a 5-year window", "the 52-week low", "over ~9y". Time units only: "$5-billion" or "5-10%" still
# states a figure, and "8q", "180d" and "12m" (a month or a million) are left as they were.
# A DECIMAL ONE IS A FIGURE (cross-review of #890): "2.3y" is NCNO's band span, a fact the point
# must cite — #890 skipped it, so "7.3y" traced as readily as the true span, and so did a
# "7.4-year payback". The claim trace only — `driver_extract` keeps its `_CAL_AFTER` check, so a
# transcript row's value still needs its quote to state a hyphenated duration.
_DURATION_AFTER = re.compile(rf"^-{_TIME_UNIT}\b|^y\b", re.IGNORECASE)
# A figure written as a percentile RANK — a number, ordinal or not ("3rd", "3"), before
# "percentile" / "pctile" / "%ile". Only such a figure may trace as the rank of a percentile its
# fact states (cross-review of #890: the rank traced in ANY context, so "2.0x", "2 turns" and "fell
# 2%" cited to SMPL's 0.0183 P/E percentile all passed). An ordinal alone is no rank ("the 2nd
# straight quarter", "its 2nd-largest customer"), nor is a percentile-POINT move ("rose 2
# percentile points") — a change, which the fact's level does not state.
_RANK_AFTER = re.compile(
    r"^(?:st|nd|rd|th)?[\s-]*(?:percentile|pctile|%ile)\b(?![\s-]*(?:pts?|points?)\b)",
    re.IGNORECASE)
# Digits that state no figure: an EDGAR accession, a date (ISO; CIQ's "Aug-31-2026"; "May 07,
# 2026"; "June 1 2026"; "Aug-6"; "Nov-2025") and a period label ("Q1-26", "FY2024-25"). A claim
# that writes one is citing or dating, not claiming a number; a fact that carries one carries its
# YEAR as a label (traced as that year only), never as a value to rescale (round 1 of #859's
# review: 2026-08-14 put 2026, 8 and 14 in the fact's numbers, and 2026 x 1e-2 traced a made-up
# "20.3%").
_MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?"
_DATE_OR_ID = re.compile(
    r"\b\d{10}-\d{2}-\d{6}\b"
    r"|\b(?P<iso>(?:19|20)\d\d)-\d\d-\d\d\b"
    rf"|\b{_MONTH}[- ]\d{{1,2}}(?:(?:,\s*|[- ])(?P<md>(?:19|20)\d\d))?(?![\d.,%])"
    rf"|\b{_MONTH}[- ](?P<my>(?:19|20)\d\d)(?!\d)"
    r"|\bF?Q[1-4][- ]?'?(?P<qy>(?:19|20)?\d\d)(?![\d.,%])"
    r"|\bFY ?'?(?P<fy>(?:19|20)?\d\d)(?:[-–/]'?\d{2,4})?(?![\d.,%])")


def _label_year(m: re.Match[str]) -> float | None:
    """The year a `_DATE_OR_ID` match names, or None (an accession, or a date with no year)."""
    y = next((m.group(g) for g in ("iso", "md", "my", "qy", "fy") if m.group(g)), None)
    return None if y is None else float(y if len(y) == 4 else f"20{y}")


# A bare year inside a fact's text ("FY2026", "2026 guidance"): a label, kept as a year only. Not
# "2,026" or "$2026" — those are amounts.
_BARE_YEAR = re.compile(r"(?<![\d$.,])(?:19|20)\d\d(?!\d|[.,]\d)")
# Keys whose values identify a fact rather than state one of its numbers.
# ``locator`` (RG-D19) is a transcript row's address — a file name, two sha256 hex digests and a
# paragraph index — never a figure the row states: walked as one, its hex digit runs ("96750",
# "35", "54612808977") entered the cited call's number universe and traced any claim that wrote one.
# ``unknown_reason`` (RG-D8) says which check refused a row's value, and may print a count that is
# no figure of the row ("its quote states 23 2 times"); an unknown row's figures are none.
_ID_KEYS = frozenset({"accession", "url", "cik", "id", "locator", "unknown_reason"})
# The mechanical layer's fields that state a PERCENTILE as a 0..1 fraction (`Valuation.
# pe_percentile_5y` / `ev_ebitda_percentile_5y`, `OwnHistoryBand.percentile`). A
# percentile is written as its whole-number rank — 0.026 is "the 3rd percentile" — and the trace's
# 2% tolerance cannot reach a rank from a fraction that small (2.6 vs 3). A closed set of field
# NAMES, so a new name is a deliberate addition (`tests/test_untraceable_rank_and_duration.py`
# checks the schema) — but a new layer model that reuses the name `percentile` is in without one.
# (`ForwardHistoryBand.percentile` sits on the Dossier, outside the layer this trace reads.)
_PERCENTILE_FIELDS = frozenset({"percentile", "pe_percentile_5y", "ev_ebitda_percentile_5y"})
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
#
# NEGATED MENTIONS DO NOT COUNT, and FUBO is why. `NM` ("not meaningful") is a REAL STATE this repo
# preserves deliberately — never collapsed into "missing" — so a careful synthesis point explains
# the difference, and the only way to explain it is to use the word:
#
#     "…trailing EBITDA is negative (a real NM state, NOT MISSING); the forward view is …"
#
# The bare pattern matched the `missing` inside `not missing` and flagged the point for asserting
# absent data — penalising the model for being PRECISE about the distinction the codebase itself
# draws. FUBO carried that flag in every historical artifact commit, and re-rolling only produced a
# fresh instance of the same class, because the cause is the check rather than the prose.
#
# The lookbehinds are fixed-width (4 chars each) so Python accepts them, and IGNORECASE covers
# "NOT MISSING". They guard ONLY the bare tokens: `not disclosed` / `not available` / `not
# provided` / `not reported` still MEAN missing and must keep matching, which is why those stay
# spelled out as their own alternative rather than inheriting the guard.
_MISSING_CLAIM = re.compile(
    r"\b((?<!not )(?<!n't )(?:missing|unavailable|absent|undisclosed|MISSING|UNKNOWN)|"
    r"not (disclosed|available|provided|reported)|no .{0,15}data)\b",
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

# (item 29, operator ruling 2026-11-04 "1 + 4") one footnote per figure of the claim
_FIGURE = {
    "type": "object",
    "properties": {
        "figure": {"type": "string",
                   "description": "The figure exactly as the claim writes it, e.g. '15.1x'."},
        "source_ref": {
            "type": "string",
            "description": "The ONE fact that states this figure — its source_ref copied VERBATIM. "
                           "Omit for a computed figure.",
        },
        "derived": {
            "type": "string", "enum": list(FIGURE_OPERATIONS),
            "description": "A computed figure's operation. Omit for a cited figure.",
        },
        "inputs": {
            "type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 2,
            "description": "A computed figure's two inputs, each a figure this claim writes, "
                           "exactly as written, with its own entry.",
        },
    },
    "required": ["figure"],
}

_POINT = {
    "type": "object",
    "properties": {
        "claim": {"type": "string", "description": "One sentence; must rest on a cited fact."},
        "source_ref": {
            "type": "string",
            "description": "Copy a source_ref VERBATIM from the supplied facts. No uncited claims.",
        },
        "figures": {
            "type": "array", "items": _FIGURE,
            "description": "One entry per figure the claim writes: the fact that states it, or "
                           "the operation and inputs that compute it. Empty when the claim "
                           "writes no figure.",
        },
    },
    "required": ["claim", "source_ref", "figures"],
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
                "trailing multiple is read beside the forward (NTM) multiple wherever the page "
                "carries one). The edge "
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
    "unresolved/neutral (e.g. a multiple at its own-history floor, overshoot-vs-terminal "
    "unresolved) is counted as NEITHER a bull NOR a bear point — it "
    "belongs in key_unknowns. Distinguish genuine directional evidence from neutral facts "
    "on BOTH sides. "
    "(8) THE GAP TEST: disclosure_gaps types each missing item: 'our gap' (our pipeline did not "
    "read it), 'does not apply', 'company's normal practice', 'change or deviation', or 'type "
    "not determined'. ONLY a change or deviation may be raised as a risk, with its entry's "
    "evidence (what was disclosed, where, when it stopped); it lowers confidence, never a bear "
    "point by itself. Every other gap, listed or not, is an unknown for key_unknowns with what "
    "would resolve it and when — never bearish. Likewise a disclosure added is a dated fact, "
    "never a bull point by itself. "
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
    "invent a driver not in the digest, nor restate a driver's number as your own derivation. "
    "(13) FOOTNOTE EVERY FIGURE. Each bull/bear point and each piece of decisive evidence carries "
    "`figures`: one entry per figure its claim writes, `figure` copied exactly as the claim writes "
    "it. A figure a fact states takes THAT fact's source_ref, copied verbatim — the ONE fact that "
    "states it, even when the point's own source_ref is another fact. A figure the claim presents "
    "as a computation (a gap, a premium, a ratio, a change, '= …') may instead be `derived`: name "
    "the operation (difference, sum, ratio, premium or growth) and its two `inputs`, each a figure "
    "the same claim writes, exactly as written, with its own entry. Never cite a figure to a fact "
    "that does not state it, and never write a figure you can neither cite nor compute from cited "
    "figures. Dates, fiscal periods and durations ('FY25', '5-year', '52-week') are labels, not "
    "figures. The shape, one entry per figure in claim order (figure → source_ref, or figure → "
    "derived + inputs); one literal example: "
    '{{"claim": "Reported FCF conversion is weak relative to earnings: LTM Levered FCF was '
    "$9,343.7M against $46,489M EBITDA (CFO $30,645M less capex $10,984M = $19,661M), reflecting "
    "heavy capex/IPR&D draw — genuine, but outweighed by 121.4x coverage and 0.9x net leverage "
    'leaving reinvestment capacity intact.", "figures": ['
    '{{"figure": "$9,343.7M", "source_ref": "CIQ Financials→Cash Flow \'Levered Free Cash Flow\' '
    '[LTM 12 months Sep-30-2026]"}}, '
    '{{"figure": "$46,489M", "source_ref": "CIQ Financials→Income Statement (margin % + absolute '
    'EBITDA reconciler)"}}, '
    '{{"figure": "$30,645M", "source_ref": "CIQ Financials→Cash Flow \'Levered Free Cash Flow\' '
    '[LTM 12 months Sep-30-2026]"}}, '
    '{{"figure": "$10,984M", "source_ref": "CIQ Financials→Cash Flow \'Levered Free Cash Flow\' '
    '[LTM 12 months Sep-30-2026]"}}, '
    '{{"figure": "$19,661M", "derived": "difference", "inputs": ["$30,645M", "$10,984M"]}}, '
    '{{"figure": "121.4x", "source_ref": "CIQ Financials→Income Statement EBITDA ÷ Interest '
    'Expense [LTM 12 months Sep-30-2026]"}}, '
    '{{"figure": "0.9x", "source_ref": "CIQ Net Debt $43,858M [Q3 Sep-30-2026] ÷ CIQ EBITDA '
    '$46,489M [LTM 12 months Sep-30-2026]"}}]}}'
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
    return [v for v, _ in _claim_figure_ends(text)]


def _claim_figure_ends(text: str) -> list[tuple[float, int]]:
    """`_claim_figures`, each with where its digits end — so the trace can read what is written
    after a figure (a rank's "rd" / "percentile", `_RANK_AFTER`), and a footnote is matched to the
    place the claim writes its figure (item 29), never to another figure of the same magnitude."""
    out: list[tuple[float, int]] = []
    labels = [(d.start(), d.end()) for d in _DATE_OR_ID.finditer(text)]
    for m in _NUM.finditer(text):
        if any(lo <= m.start() < hi for lo, hi in labels):
            continue  # 2026-11-04 / Aug-6 / Nov-2025 / Q1-26 / an accession
        before = text[m.start() - 1] if m.start() else " "
        if before.isalpha() or (before == "-" and m.start() >= 2 and text[m.start() - 2].isalpha()):
            continue  # GLP-1 / B2B / low-20s — a digit fused to a word is part of a name
        if _CAL_BEFORE.search(text[max(0, m.start() - 9):m.start()]):
            continue  # FY21 / Q1 / fiscal 2025
        if _CAL_AFTER.match(text[m.end():m.end() + 10]):
            continue  # 90 days ago / 8 quarters
        if "." not in m.group() and _DURATION_AFTER.match(text[m.end():m.end() + 10]):
            continue  # a 5-year window / the 52-week low / over ~9y — never "2.3y"
        try:
            out.append((float(m.group().replace(",", "")), m.end()))
        except ValueError:
            continue
    return out


# --- item 29: every figure footnoted (operator ruling 2026-11-04, "1 + 4") ---------------------
# A point carries `figures`: one entry per figure of its claim, citing the ONE fact that states it,
# or naming an operation in `FIGURE_OPERATIONS` and two inputs (figures of the same claim, each with
# its own entry) that compute it. Each cited figure is traced to its own fact by the per-fact rule
# above (`_num_traces`, audit G-D6) — the universe a made-up figure meets is the one fact it names,
# as before. A computed figure is RECOMPUTED from its inputs as written: each input stands for the
# interval half a unit of its last written digit either side, and the figure's own interval must
# meet the result's. No tolerance is chosen — the width is what the writing states. A figure with
# no entry is traced to the point's own `source_ref`, exactly as before, so every point drawn
# before 2026-11-04 is checked as it was.

_WRITTEN = re.compile(
    r"(?P<sign>[-−+])?\s*(?P<cur>\$)?\s*(?P<num>\d[\d,]*(?:\.(?P<dec>\d+))?)\s*"
    r"(?P<scale>thousand|million|billion|trillion|mn|bn|tn|[kmbt](?![a-z]))?\s*"
    r"(?P<unit>%|pts?\b|pp\b|bps?\b|basis\s+points?\b|x\b|st\b|nd\b|rd\b|th\b)?", re.IGNORECASE)
_SCALE = {"k": 1e3, "thousand": 1e3, "m": 1e6, "mn": 1e6, "million": 1e6, "b": 1e9, "bn": 1e9,
          "billion": 1e9, "t": 1e12, "tn": 1e12, "trillion": 1e12}


@dataclass(frozen=True)
class _Written:
    """A figure as WRITTEN: its value and half a unit of its last digit (both in base units, the
    scale word applied) and its unit — pct (incl. points, and basis points at a scale of 0.01), x,
    money ($), rank (an ordinal) or plain."""

    value: float
    half: float
    unit: str
    scale: float = 1.0
    signed: bool = False   # written with a sign (+, -, −): its direction is part of the figure


def _written(lit: str) -> _Written | None:
    m = _WRITTEN.search(lit)
    if m is None:
        return None
    scale = _SCALE.get((m.group("scale") or "").lower(), 1.0)
    u = " ".join((m.group("unit") or "").lower().split())
    bps = u in ("bp", "bps", "basis point", "basis points")
    if bps:   # a basis point is a hundredth of a percentage point (Codex, round 2)
        scale *= 0.01
    value = float(m.group("num").replace(",", "")) * scale
    if m.group("sign") in ("-", "−"):
        value = -value
    half = 0.5 * 10.0 ** -len(m.group("dec") or "") * scale
    unit = ("pct" if bps or u in ("%", "pt", "pts", "pp") else "x" if u == "x"
            else "rank" if u in ("st", "nd", "rd", "th") else "money" if m.group("cur")
            else "plain")
    return _Written(value, half, unit, scale, m.group("sign") is not None)


def _abs_interval(lo: float, hi: float) -> tuple[float, float]:
    if lo <= 0 <= hi:
        return 0.0, max(-lo, hi)
    return min(abs(lo), abs(hi)), max(abs(lo), abs(hi))


def _recompute(op: str, a: _Written, b: _Written, fig: _Written) -> str | None:
    """None when ``op(a, b)`` as written can be the figure as written; else why not. A figure
    written with a sign is compared signed, so "+45pt" is not -29% − +16% (Codex, round 1); an
    unsigned one is compared on magnitudes, as the trace compares them (a fall written "fell 24%"
    carries its sign in words)."""
    if "rank" in (a.unit, b.unit):
        return "a percentile rank is not an operand"
    if a.unit != b.unit:
        return f"the {op} of a {a.unit} figure and a {b.unit} figure"
    want = {"ratio": ("x", "plain"), "premium": ("pct",), "growth": ("pct",)}.get(op, (a.unit,))
    if fig.unit not in want:
        return f"a {op} of {a.unit} figures is not written as {fig.unit}"
    a0, a1, b0, b1 = a.value - a.half, a.value + a.half, b.value - b.half, b.value + b.half
    if op == "difference":
        lo, hi = a0 - b1, a1 - b0
    elif op == "sum":
        lo, hi = a0 + b0, a1 + b1
    else:
        if b0 <= 0 <= b1:
            return "its divisor, as written, could be zero"
        qs = [x / y for x in (a0, a1) for y in (b0, b1)]
        lo, hi = min(qs), max(qs)
        if op in ("premium", "growth"):
            lo, hi = (lo - 1) * 100, (hi - 1) * 100
    r0, r1, f0, f1 = lo, hi, fig.value - fig.half, fig.value + fig.half
    if not fig.signed:
        (r0, r1), (f0, f1) = _abs_interval(lo, hi), _abs_interval(f0, f1)
    if r0 <= f1 and r1 >= f0:
        return None

    def shown(x: float) -> str:   # in the figure's own scale, as a reader writes it
        v = x / fig.scale
        return f"{v:,.0f}" if abs(v) >= 1000 else f"{v:,.2f}".rstrip("0").rstrip(".")
    return f"{op} gives {shown(r0)} to {shown(r1)} as written"


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
    """True iff ``ref`` IS one of the layer's refs (audit G-D5). Compared on the verbatim check's
    key — case, typography and whitespace folded (a gap between two digits kept as one space, audit
    G-D7), nothing else — so the model's re-typed dash still matches. NOT a substring either way:
    that counted ``''`` as cited (it is in every string) and a bare ``'EOD'`` as citing every EOD
    fact at once. An empty ref cites nothing, as an empty quote proves nothing
    (``verbatim.SourceText.match``)."""
    key = comparison_key(ref)
    return bool(key) and key in {comparison_key(u) for u in universe}


@dataclass
class _FactNumbers:
    """The numbers one citable fact STATES: its values, traced at any unit rendering; the years of
    its dates and labels, traced only as those years; and the whole-number rank of each percentile
    it states (`_PERCENTILE_FIELDS`), traced only as that rank."""

    values: list[float] = field(default_factory=list)
    years: set[float] = field(default_factory=set)
    ranks: set[float] = field(default_factory=set)


def _percentile_ranks(p: float) -> set[float]:
    """The whole-number rank(s) a 0..1 percentile is written as: the nearest whole number to it
    x100, read on its decimal as stored (0.026 -> 3) — and BOTH neighbours at an exact half. The
    page itself has no one convention there: `render._pctile` rounds 0.025 to the 2nd (Python's
    half-even), the web's `Math.round` to the 3rd, and in binary floats 0.145 x 100 is 14.4999…, so
    a writer reading "0.145" says the 15th while the page shows the 14th."""
    x = Decimal(repr(p)).scaleb(2)
    lo = x.to_integral_value(rounding=ROUND_FLOOR)
    frac = x - lo
    if frac == Decimal("0.5"):
        return {float(lo), float(lo + 1)}
    return {float(lo + 1) if frac > Decimal("0.5") else float(lo)}


def _stated_numbers(o: Any, into: _FactNumbers, name: str = "") -> None:
    """Every number ``o`` states, read from the values themselves — never from a JSON dump, whose
    dates and ids are digit runs like any other (`_DATE_OR_ID`, `_ID_KEYS`). ``name`` is the field
    ``o`` sits in (a `Sourced` wrapper's ``value`` keeps its own field's name), read only to know
    a percentile."""
    if o is None or isinstance(o, bool):
        return
    if isinstance(o, (int, float)):
        into.values.append(float(o))
        if name in _PERCENTILE_FIELDS and 0 <= o <= 1:
            into.ranks |= _percentile_ranks(float(o))
    elif isinstance(o, date):
        into.years.add(float(o.year))
    elif isinstance(o, str):
        def label(m: re.Match[str]) -> str:
            if (year := _label_year(m)) is not None:
                into.years.add(year)
            return " "
        rest = _DATE_OR_ID.sub(label, o)
        into.years.update(float(y) for y in _BARE_YEAR.findall(rest))
        into.values.extend(_floats(_BARE_YEAR.sub(" ", rest)))
    elif isinstance(o, dict):
        for k, v in o.items():
            if k not in _ID_KEYS and not str(k).endswith("_id"):
                _stated_numbers(v, into, name if k == "value" else str(k))
    elif isinstance(o, (list, tuple, set, frozenset)):
        for v in o:
            _stated_numbers(v, into, name)


def _values_by_ref(mech: MechanicalLayer) -> dict[str, _FactNumbers]:
    """The numbers each citable fact states, keyed by its ref (the ``source_ref`` / accession / url
    `_refs_in` collects, on the comparison key). A fact's numbers are its whole subtree, so a
    filing cited by accession carries its guidance and reconciliation rows."""
    out: dict[str, _FactNumbers] = {}

    def rec(o: Any, name: str) -> None:
        if isinstance(o, dict):
            keys = {comparison_key(str(o[k])) for k in ("source_ref", "accession", "url")
                    if o.get(k)}
            if keys:
                nums = _FactNumbers()
                _stated_numbers(o, nums, name)
                for k in keys:
                    acc = out.setdefault(k, _FactNumbers())
                    acc.values.extend(nums.values)
                    acc.years |= nums.years
                    acc.ranks |= nums.ranks
            for k, v in o.items():
                rec(v, str(k))
        elif isinstance(o, (list, tuple)):
            for v in o:
                rec(v, name)

    rec(mech.model_dump(), "")
    return out


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
    # THE CITED FACT'S OWN NUMBERS, not the layer's (audit G-D6). The trace ran against every number
    # in the layer — 5,615 to 11,808 of them a page — and passed 1,176 of 1,176 made-up figures on
    # the frozen SMPL page: a universe that large contains every figure at some scale. A point
    # cites ONE fact; its figures are checked against that fact.
    values_by_ref = _values_by_ref(mech)

    def _num_traces(n: float, cited: _FactNumbers, *, as_rank: bool = False) -> bool:
        # Trace by MAGNITUDE at any standard financial unit rendering (%, thousands, millions,
        # billions): the LLM writes the stored −0.726 as "−72.6%", 29,643,500 shares as "29.6
        # million", and a stored −0.027 as "shrunk by 2.7%" (sign carried in words, not the digit).
        # Direction is the directional-lint's job; this only asks whether the figure exists.
        a = abs(n)
        if a in cited.years:
            return True  # the year of a date the fact carries — as that year, never rescaled
        if as_rank and a in cited.ranks:
            return True  # a figure WRITTEN as a rank, as the rank of a percentile the fact states
        for mf in cited.values:
            for s in _TRACE_SCALES:
                target = abs(mf) * s
                if abs(a - target) <= max(0.05, target * 0.02):
                    return True
        return False

    # (signed value, type, cited ref) for decisive-mirror dedup — the ref since a figure traces or
    # not by the fact it cites, so the same figure cited to another fact is another finding
    flagged_figs: set[tuple[float, bool, str]] = set()
    # the citable universe's comparison keys, built ONCE — `_traces` rebuilds them per call, and a
    # footnoted point traces each figure and each input on its own
    ref_keys = {comparison_key(u) for u in refs}

    def _figure_entries(p: SourcedPoint, where: str) -> dict[int, FigureCite]:
        """The point's footnotes by WHERE the claim writes each one's figure (the end of its
        digits), at every place its literal is written — so a footnote checks its own figure, never
        another of the same magnitude ("-16%" before a footnoted "$16M" is traced to the point's
        own ref; Codex, round 1). The first entry for a place wins. An entry that names no figure
        the claim writes (a label, a figure not written there, two figures) is a MISMATCH — an
        extra the checker reads nothing from, never a figure left unchecked."""
        ends = _claim_figure_ends(p.claim)
        out: dict[int, FigureCite] = {}
        for e in p.figures:
            vals = _claim_figures(e.figure)
            at = [end for m in re.finditer(
                      rf"(?<![\d.,]){re.escape(e.figure)}(?![\d]|[.,]\d)", p.claim)
                  for v, end in ends
                  if m.start() < end <= m.end() and len(vals) == 1
                  and round(abs(v), 6) == round(abs(vals[0]), 6)] if e.figure else []
            if not at:
                flags.append(f"MISMATCH {where}: figure entry {e.figure!r} names no single figure "
                             f"the claim writes: '{_snip(p.claim, 55)}'")
                continue
            for end in at:
                out.setdefault(end, e)
        return out

    def check_figure(n: float, e: FigureCite, p: SourcedPoint, where: str, *,
                     dedup: bool, as_rank: bool = False) -> None:
        """One footnoted figure: a cited one traces to the fact it names (as that fact's
        percentile rank only when the claim writes it as one, ``as_rank``, #899); a computed one
        has inputs that each trace to theirs, and recomputes to the figure as written."""
        def direct(x: FigureCite, rank: bool = False) -> tuple[bool, bool]:
            """(traces, cited to a transcript OF THE PAGE) for a cited entry's own figure. A ref
            that only LOOKS like a transcript — 'transcript' in a ref the layer does not carry — is
            no softer than any other unknown ref: the soft route is for a real call's prose."""
            ref = x.source_ref or ""
            key = comparison_key(ref)
            nums = values_by_ref.get(key, _FactNumbers())
            v = _claim_figures(x.figure)
            known = bool(key) and key in ref_keys
            ok = bool(v) and known and _num_traces(v[0], nums, as_rank=rank)
            return ok, known and bool(_TRANSCRIPT_REF.search(ref))

        if e.derived is None:
            ok, tx = direct(e, as_rank)
            fkey = comparison_key(e.source_ref or "")
            if ok:
                return
            key = (round(n, 2), tx, fkey)
            if dedup and key in flagged_figs:
                return
            flagged_figs.add(key)
            if tx:
                flags.append(
                    f"TRANSCRIPT-FIGURE '{n:g}' in {where}: '{_snip(p.claim)}' — from the cited "
                    "earnings call, not its validated facts; verify against the call")
            else:
                flags.append(f"UNTRACEABLE figure '{n:g}' in {where} [cited to {e.source_ref}]: "
                             f"'{p.claim}'")
            return
        why: str | None = None
        soft = False
        operands: list[_Written] = []
        for lit in e.inputs:
            src = next((x for x in p.figures if x.derived is None and x.figure == lit), None)
            if src is None or lit not in p.claim:
                why = f"its input {lit!r} is not a cited figure of the claim"
                break
            ok, tx = direct(src)
            if not ok and tx:
                soft = True
            elif not ok:
                why = f"its input {lit!r} does not trace to the fact it cites ({src.source_ref})"
                break
            w = _written(lit)
            if w is None:
                why = f"its input {lit!r} is not a figure"
                break
            operands.append(w)
        fig = _written(e.figure)
        if why is None and fig is None:
            why = f"{e.figure!r} is not a figure"
        if why is None and fig is not None and len(operands) == 2:
            why = _recompute(e.derived, operands[0], operands[1], fig)
        key = (round(n, 2), soft and why is None, f"derived:{e.derived}:{'|'.join(e.inputs)}")
        if why is None and not soft:
            return
        if dedup and key in flagged_figs:
            return
        flagged_figs.add(key)
        if why is None:
            flags.append(
                f"TRANSCRIPT-FIGURE '{n:g}' in {where}: '{_snip(p.claim)}' — computed from a "
                "figure of the cited earnings call, not its validated facts; verify against the "
                "call")
        else:
            flags.append(f"UNDERIVED figure '{n:g}' in {where}: '{p.claim}' — {e.derived}("
                         f"{', '.join(e.inputs)}): {why}, but the claim writes {e.figure}")

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
        ref_key = comparison_key(p.source_ref)
        cited_nums = values_by_ref.get(ref_key, _FactNumbers()) if ref_key else _FactNumbers()
        entries = _figure_entries(p, where)
        for n, end in _claim_figure_ends(p.claim):
            as_rank = bool(_RANK_AFTER.match(p.claim[end:end + 32]))
            e = entries.get(end)
            if e is not None:   # (item 29) this figure carries its own footnote
                check_figure(n, e, p, where, dedup=dedup, as_rank=as_rank)
                continue
            if _num_traces(n, cited_nums, as_rank=as_rank):
                continue
            # key on SIGNED value + flag-type: don't let abs() collapse +N/-N (distinct facts) and
            # don't let a soft TRANSCRIPT-FIGURE on one point suppress a hard UNTRACEABLE elsewhere.
            key = (round(n, 2), ref_is_transcript, ref_key)
            if dedup and key in flagged_figs:
                continue  # decisive mirror of an already-flagged bull/bear figure
            flagged_figs.add(key)
            if ref_is_transcript:
                # the figure lives in the cited call's prose, not the structured layer — route it to
                # human verification; don't brand a sourced number untraceable (that would gut a
                # high-value transcript-only point, e.g. 'the GAAP profit is a non-cash artifact').
                flags.append(
                    f"TRANSCRIPT-FIGURE '{n:g}' in {where}: '{_snip(p.claim)}' — from the cited "
                    "earnings call, not its validated facts; verify against the call"
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
    # THE FLAG SAID "should be tagged unverified" AND NOTHING TAGGED IT (review finding, #455).
    # This loop only APPENDED a flag; `tw` kept whatever source the model wrote. When that source is
    # plausible-looking but untraceable — FUBO drew `CIQ peer_capital_intensity impairment
    # (per-peer grid)` for a Starz twin — the renderer's unverified path never fires, because it
    # keys on the source STRING (`_UNVERIFIED`) rather than on whether the source TRACED. The page
    # then printed "Starz Entertainment Corp. — went terminal" in the same shape as the properly
    # sourced Paramount twin directly above it, and a reader had no way to tell an evidence-bound
    # twin from an invented one. Detected-but-invisible is the two-states-must-not-render-alike
    # defect, sitting in the layer that decides what a human actually sees.
    #
    # TAGGING IS NOT REWRITING THE MODEL'S CLAIM. The twin, its outcome and its reasoning are kept
    # verbatim; only the SOURCE is replaced, with the marker stating exactly what the validator has
    # just established — this did not trace. `qa_flags` still records the original string, and
    # `check_point` above already sets `cited = False` on the same principle.
    twins = []
    for tw in synth.twin_reference_cases:
        if tw.source != _UNVERIFIED and not _traces(tw.source, refs):
            flags.append(
                f"TWIN '{tw.name}' source {tw.source!r} doesn't trace — tagged unverified")
            tw = tw.model_copy(update={"source": _UNVERIFIED})
        numeric = _twin_numbers(f"{tw.outcome} {tw.distinguishing_fact}")
        if numeric:
            flags.append(f"TWIN '{tw.name}' has numbers {sorted(numeric)} — must be non-numeric")
        twins.append(tw)
    synth = synth.model_copy(update={"twin_reference_cases": twins})
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


def _figure_cites(items: Any, notes: list[str] | None) -> list[FigureCite]:
    """(item 29) The model's footnotes for one point. An entry that is not a well-formed footnote
    (no figure, both or neither of a ref and an operation, an unknown operation, other than two
    inputs) is DROPPED and named in ``notes`` — its figure is then checked against the point's own
    ref, exactly as before footnotes existed, so a malformed entry can never loosen the check."""
    out: list[FigureCite] = []
    for i in items if isinstance(items, list) else []:
        if not isinstance(i, dict):
            continue
        raw_inputs = i.get("inputs") or []
        try:
            if not isinstance(raw_inputs, list):   # a bare string/number would iterate or raise
                raise ValueError(f"inputs is a {type(raw_inputs).__name__}, not a list")
            out.append(FigureCite(
                figure=str(i.get("figure", "")),
                source_ref=str(i["source_ref"]) if i.get("source_ref") else None,
                derived=i.get("derived") or None,
                inputs=[str(x) for x in raw_inputs]))
        except ValueError as exc:
            if notes is not None:
                notes.append(f"MISMATCH figures: entry {i!r} dropped — {exc}")
    return out


def _parse(raw: dict[str, Any], notes: list[str] | None = None) -> Synthesis:
    def pts(items: Any) -> list[SourcedPoint]:
        return [
            SourcedPoint(claim=str(i.get("claim", "")), source_ref=str(i.get("source_ref", "")),
                         figures=_figure_cites(i.get("figures"), notes))
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
        v = prompt_driver_value(r)
        val = v if len(v) <= 130 else v[:127].rstrip() + "…"
        out.append(f"[{r.kind.value}] {r.metric}: {val} → {r.source_ref}")
        # SURFACED HERE, not left to the facts dump. BRBR's quote — "70% of RTD shake category
        # volumes were sold on price promotion" — is exact and correctly cited, and the sentence
        # after it says the figure is "in line with historical norms … DOWN sequentially from the
        # heavier promoted second quarter". The synthesis had that call in its prompt (then its
        # first 12,000 characters; whole since audit G-D3) and still built an escalating sequence
        # out of the quote alone, because THIS digest is what it is told to ground in and copy
        # refs from. Putting the qualifier beside the fact is the intervention; leaving it in the
        # JSON would only serve the audit.
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
    _mark_guidance_field((dc or {}).get("revised_guidance"), ps)
    # THE DATED PARTS CARRY THE SAME KIND OF FIELD, and the at-the-anchor one is by construction
    # the OLDEST guide on the page — SMPL's is the April guide this mark exists for. Unmarked, it
    # would reopen the incident one key deeper (`DrawdownAnchor`, 2026-11-04).
    anchor = (dc or {}).get("anchor")
    if isinstance(anchor, dict):
        for part in ("at_anchor", "since"):
            window = anchor.get(part)
            if isinstance(window, dict):
                _mark_guidance_field(window.get("revised_guidance"), ps)


def _mark_guidance_field(rg: Any, ps: PrimarySource | None) -> None:
    """One dumped revised-guidance field, marked with its vintage in place
    (`_mark_drawdown_guidance`)."""
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
    # COUNTED AFTER THE UNION, AND NAMED AS THE CONTENT WINDOW (review finding, #439). The count was
    # `len(releases) - len(recent)` — the CONTENT window's leftovers — but the loop below emits
    # `recent ∪ guided`, so a release outside the content window that CARRIES guidance is in the
    # digest with its guide printed. Calling it "omitted" told the LLM the older outlook had been
    # dropped while handing it that very outlook: contradictory evidence, with no way to tell which
    # half to believe. What is genuinely absent is a release in NEITHER window.
    shown = [r for r in ps.releases if r in recent or r in guided]
    omitted = len(ps.releases) - len(shown)
    if omitted or omitted_guided:
        parts = []
        if omitted:
            parts.append(f"{omitted} older release(s) contribute nothing here")
        # DISCLOSED SEPARATELY, because it is a different loss: a guide that EXISTS and is not
        # shown, versus a release whose non-guidance content falls outside the window.
        if omitted_guided:
            parts.append(f"{omitted_guided} further release(s) state guidance that is NOT shown")
        out.append(f"(note: {'; '.join(parts)} — the content window is the 4 most recent releases, "
                   f"and guidance is carried for the 4 most recent that state any; "
                   f"full set in the JSON)")
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


#: How many independent synthesis draws an assembly takes. FIVE, chosen on the error rates of the
#: unanimity gate below and NOT on cost (operator ruling 2026-09-26).
#:
#: The gate is a test with two failure directions. Writing p for a name's chance of returning its
#: modal label on one draw, a strict unanimity gate publishes with probability p^N + (1-p)^N:
#:
#:      p      N=3     N=5      what that name looks like
#:      0.95   85.8%   77.4%    solid — the 23% at N=5 is a FALSE withhold, the price paid
#:      0.80   52.0%   32.8%    AMZN, measured 4/5 — N=3 misses it half the time
#:      0.60   28.0%    8.8%    GOOGL and NFLX, measured 3/5 — N=3 publishes 1 in 4
#:
#: N=3 barely gates: it lets an AMZN-like name through on a coin-flip, which is the exact case the
#: gate exists for. N=5 takes that to 33% and a GOOGL-like name to 9%. The asymmetry justifying the
#: strict side: withholding is already a NORMAL state (`mixed` withholds by design, and the human
#: decides either way), so a withheld proposal costs a hint — while a published noisy one feeds the
#: anchoring risk STATE.md already records.
#:
#: THE CEILING, stated so nobody raises N expecting it to help: unanimity is a weak detector of
#: mildly-wobbly names at ANY practical N (even N=7 passes a p=0.8 name 21% of the time), because
#: such a name usually IS unanimous by luck. Catching those needs a different RULE, not a bigger N.
#:
#: N IS FIXED FOR EVERY NAME, DECIDED IN ADVANCE. Drawing again because the first answer is
#: unwelcome is outcome-dependent sampling — the line this fund does not cross, and the same one
#: `docs/RUNBOOKS.md` draws at re-rolling a synthesis for cleaner flags.
SYNTHESIS_DRAWS = 5

#: A re-send started further apart than this has outlived its 5-minute cache entry, so its miss is
#: EXPIRY rather than a prompt that failed to cache. Measured start-to-start, as the TTL is.
_CACHE_TTL_S = 300.0


class PromptCacheMissWarning(UserWarning):
    """A repeated draw re-billed its whole prompt. A COST signal, never a data one — printed for the
    operator and written to the call log, and kept off the dossier, whose facts it cannot touch."""


def _cache_misses(sends: list[tuple[int, dict[str, Any], float]]) -> list[str]:
    """Draws after the first that read NOTHING from the prompt cache, each with its likely cause.

    ``sends`` is ``(draw, usage, started_s)`` for EVERY draw, in order. A draw that raised
    ``LlmError`` carries an EMPTY usage: it is never judged itself, but it stays in the list because
    the API answered it (every ``LlmError`` the client raises follows a response), so it touched the
    cache and its start is the one the next draw's gap is measured from. Dropping it measured the
    gap from the draw BEFORE it and could call a non-reuse miss "expiry". Only a usage record
    carrying ``cache_read_input_tokens`` can be judged: a client that reports no cache fields is not
    evidence of a miss, so it is skipped rather than flagged.

    WHY THIS EXISTS: a broken cache does not fail, it bills. Anything that makes the draws' prompts
    differ — a timestamp in the facts, a dict serialised in another order, the draws moved onto a
    thread pool — silently re-bills ~two thirds of synthesis input on every name, and nothing else
    in the pipeline would notice."""
    out: list[str] = []
    for (prev_n, _, prev_t), (n, usage, t) in zip(sends, sends[1:], strict=False):
        if "cache_read_input_tokens" not in usage or usage["cache_read_input_tokens"] > 0:
            continue
        prompt = sum(int(usage.get(k, 0) or 0) for k in
                     ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
        gap = t - prev_t
        cause = (f"past the {_CACHE_TTL_S:.0f}s cache lifetime" if gap > _CACHE_TTL_S
                 else "inside the cache lifetime, so the prompt was not cached or not reused")
        out.append(f"draw {n} read 0 of its {prompt:,}-token prompt from cache; it started "
                   f"{gap:.0f}s after draw {prev_n}, {cause}")
    return out


#: What the facts dump never carries. ``primary_source`` goes as its curated digest instead
#: (verbatims are provenance, not input), and ``catalyst_path.guidance_after_price_date`` holds the
#: guides CIQ dated AFTER the page's price date (STATE row 57): the cut's audit tier, which the
#: model must not read — sending it would hand the synthesis exactly what the cut withholds. The
#: releases' twin (`primary_source.releases_after_price_date`) is inside the excluded block, and
#: the digest never reads it. ``concentration.customers_listed`` (audit RBC-D1) is the display
#: twin of the roster the model already reads: the renderers print it, and sending it — a count,
#: or a null on a page without one — would change every synthesis request, which row 53 says is
#: measured on the panel before it ships. This build changes what the PAGE prints, not what the
#: model reads. ``capital_allocation.impairment_headroom`` (audit RD-D1) is the same kind: the two
#: balances the model reads, at one date, for the page to print.
#: ``operating_drivers.rows[*]``'s structured fact and locator (RG-D8/RG-D19) are for the PAGE:
#: the prompt keeps the row shape it always had, and what the check concluded reaches it through
#: ONE field — an ``unknown`` row's value reads UNKNOWN with its reason (`prompt_driver_value`),
#: in the facts and in the digest alike. So a verified row is sent byte for byte as before.
NOT_SENT: dict[str, Any] = {"primary_source": True,
                            "catalyst_path": {"guidance_after_price_date": True},
                            "concentration": {"customers_listed": True},
                            "capital_allocation": {"impairment_headroom": True},
                            "consensus_context": {"consensus_levels_note": True},
                            "operating_drivers": {"rows": {"__all__": {
                                "figures": True, "value_status": True, "unknown_reason": True,
                                "locator": True}}}}


def driver_value_as_read(value: str, status: str | None, reason: str | None) -> str:
    """A driver row's value as every READER is handed it — the synthesis and the scenario
    template alike. A transcript row whose value code could not verify against its quote
    (`driver_extract.check_fact`) is not handed over as a value — "up 7%" read off "down 7%" was,
    under the header "validated, cited facts" (RG-D8). Every other row's value is unchanged."""
    if status == "unknown":
        return f"UNKNOWN — not verified against its quote: {reason}"
    return value


def prompt_driver_value(r: OperatingDriver) -> str:
    """`driver_value_as_read` for a row of the layer."""
    return driver_value_as_read(r.value, r.value_status, r.unknown_reason)


def _mark_unverified_drivers(dumped: dict[str, Any], od: OperatingDriversExtract | None) -> None:
    """Write `prompt_driver_value` into the facts dump's driver rows, which `model_dump` emits in
    ``od.rows`` order."""
    rows = (dumped.get("operating_drivers") or {}).get("rows")
    if od is None or not rows:
        return
    for r, d in zip(od.rows, rows, strict=True):
        d["value"] = prompt_driver_value(r)


def synthesize(
    mech: MechanicalLayer, *, llm: LlmClient, ticker: str, name: str,
    transcript: str | None = None, sleeve: str = DEFAULT_SLEEVE, draws: int = 1,
) -> tuple[Synthesis | None, list[str], str]:
    """Run the fenced synthesis → (synthesis|None, flags, log). Fail-loud, never fabricates. The
    ``transcript`` (every call on file, whole — NOT embedded in the dossier) is QUALITATIVE
    context only; no numbers are derived from it and points still bind to the mechanical facts.

    ``draws`` (default ONE, so every existing caller and artifact is unmoved) asks the model that
    many times on the IDENTICAL prompt and keeps the FIRST draw carrying the modal lean label —
    first, never best-sounding, because choosing a draw on its content is selecting on outcome. The
    tally rides on the returned synthesis as :class:`DrawAgreement`, and a build whose draws
    disagree is what withholds the machine proposal downstream (`verdict.derive_proposal`)."""
    # (RC-1 C) the raw primary_source (releases/filing) carries VERBATIMS — provenance, not input.
    # Exclude it from the dump and feed the curated term→value→source_ref digest instead. Its
    # source_refs still live in `mech`, so a cited primary-source ref traces through validation.
    _dumped = mech.model_dump(exclude=NOT_SENT)
    _mark_drawdown_guidance(_dumped, mech.primary_source)
    _mark_unverified_drivers(_dumped, mech.operating_drivers)
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
            "shifts. Each call is WHOLE — prepared remarks and the full Q&A — after the "
            "boilerplate is stripped; a call past the length ceiling ends in a marker saying "
            "where it was cut. QUALITATIVE management-posture "
            "context ONLY. Derive NO numbers FROM THIS TEXT — any transcript figure you need has "
            "already been extracted, validated, and cited as an `operating_drivers` fact above; "
            "cite THAT source_ref, never a number you read here. A point resting on posture cites "
            "the 'CIQ transcript' source_ref from the facts. ===\n"
            + transcript
        )
    # (19c) THE FIGURES A DRAW IS REFUSED FOR OMITTING, named to the model from the guard's own
    # selection — so it is asked for exactly what `uncited_material_figures` demands. LAST, after
    # the transcripts, and from the facts, never from a call. No material row, no section: the
    # prompt is then the one every earlier build sent.
    if (material := demanded_material_figures(mech)):
        user += "\n\n" + _material_figures_digest(material)
    # (2026-11-04) THE DRAWDOWN AT THE ANCHOR, LAST — after the material figures, so a name with no
    # anchor sends the prompt every earlier build sent
    if (anchored := _drawdown_anchor_digest(_dumped)) is not None:
        user += "\n\n" + anchored
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
    # a missing STRUCTURAL field means a truncated response — mark the synthesis UNAVAILABLE rather
    # than silently defaulting to a blank. evidence_balance is excluded: its absence is a contract
    # REGRESSION the guardrail FLAGS (G.2), not a truncation that blocks — flag, don't drop.
    structural = [k for k in SYNTHESIS_TOOL["input_schema"]["required"] if k != "evidence_balance"]
    attempted = max(1, draws)
    usable: list[tuple[str, dict[str, Any]]] = []  # (lean label, raw) per COMPLETED draw, in order
    last_fail: str | None = None
    sends: list[tuple[int, dict[str, Any], float]] = []  # (draw, usage, started_s), EVERY draw
    t0 = time.monotonic()
    for n in range(1, attempted + 1):
        head = f"=== DRAW {n}/{attempted} ===" if attempted > 1 else "==="
        started_s = round(time.monotonic() - t0, 1)
        try:
            # A MULTI-DRAW BUILD RE-SENDS ONE PROMPT, so it asks for it to be cached; a single draw
            # passes NOTHING, and its request stays byte-identical to every build before caching.
            raw = (llm.extract(system=system, user=user, tool=tool, cache=True) if attempted > 1
                   else llm.extract(system=system, user=user, tool=tool))
        except LlmError as exc:
            # ONE BAD DRAW IS NOT A FAILED SYNTHESIS when others remain. The 2026-09-01 Opus 5
            # regression is exactly this shape — a tool call that comes back unusable perhaps half
            # the time — so a draw that raises is counted and the loop continues; only an EMPTY
            # tally fails the synthesis, which keeps the single-draw behaviour identical.
            last_fail = str(exc)
            log_parts += ["", f"{head} ERROR", str(exc)]
            sends.append((n, {}, started_s))  # timing only — see `_cache_misses`
            continue
        # USAGE IN THE LOG, so "(likely truncated)" below can be CHECKED instead of believed. On
        # SMPL 2026-08-04 that message was emitted about a response using a fifth of its budget.
        _u = getattr(llm, "last_usage", None)
        if _u:
            sends.append((n, _u, started_s))
            log_parts += ["", f"{head} USAGE", json.dumps({**_u, "started_s": started_s})]
        log_parts += ["", f"{head} RAW OUTPUT", json.dumps(raw, indent=2, default=str)]
        missing = [k for k in structural if k not in raw]
        if missing:
            note = ("synthesis tool returned incomplete output — missing required "
                    f"field(s) {missing}")
            log_parts += ["", f"{head} INCOMPLETE", note]
            last_fail = note
            continue
        decoded = cast(dict[str, Any], _decode_escapes(raw))
        parts = split_lean(str(decoded.get("evidence_balance") or ""))
        # ONE KEY with the mapping (`verdict.lean_key`): two spellings of one lean are one lean
        usable.append(((lean_key(parts[0]) if parts else ""), decoded))
    misses = _cache_misses(sends) if attempted > 1 else []
    if misses:
        log_parts += ["", "=== PROMPT CACHE MISSED ===", *misses]
        for miss in misses:
            warnings.warn(f"{ticker}: {miss}", PromptCacheMissWarning, stacklevel=2)
    if not usable:
        # THE WORDING IS LOAD-BEARING, per failure kind. A RAISED call has always flagged "synthesis
        # failed (no usable output)" and `test_synthesis_fails_loud_when_llm_errors` reads that
        # phrase; an INCOMPLETE tool call has always flagged "UNAVAILABLE … (likely truncated)".
        # Collapsing the two into one message silently retired a pin, so each keeps its own.
        note = last_fail or "no draw returned usable output"
        flag = (f"LLM synthesis UNAVAILABLE — {note} (likely truncated)"
                if "missing required field" in note
                else f"LLM synthesis failed (no usable output): {note}")
        return None, [flag], "\n".join(log_parts)
    # THE FIRST DRAW CARRYING THE MODAL LABEL — first, never best-sounding. Ties break on the
    # earliest draw for the same reason: any rule that inspects the PROSE to choose is selecting on
    # outcome. An unparseable label ("" here) is its own bucket, so a draw whose lean did not parse
    # cannot silently join the majority.
    tally = Counter(label for label, _ in usable)
    modal = max(tally.items(), key=lambda kv: (kv[1], -[lab for lab, _ in usable].index(kv[0])))[0]
    chosen = next(raw for label, raw in usable if label == modal)
    # ONE DRAW IS NOT AGREEMENT — it agrees with itself. Attaching `unanimous=True` to a
    # single-draw build would hand the gate a measured-looking pass that was never measured, which
    # is the exact false reassurance this whole mechanism exists to remove. Below two draws the
    # field stays None and the page prints nothing.
    # THE VOTE RULE (R1, R3, C(iii); `verdict.draw_gate`) over the draws ATTEMPTED: a failed draw
    # is dissent, so 1 of 5 completed is 1 of 5 — `unanimous` still records that the completed
    # draws agreed, and is what a page written before the rule decides by.
    gate = draw_gate([label for label, _ in usable], attempted)
    agreement = (DrawAgreement(attempted=attempted, completed=len(usable), labels=dict(tally),
                               unanimous=len(tally) == 1, modal_count=gate.count,
                               required=gate.required, passes=gate.passes, rule=GATE_RULE)
                 if attempted > 1 else None)
    if agreement is not None:
        log_parts += ["", "=== DRAW AGREEMENT ===",
                      json.dumps(agreement.model_dump(), indent=2, sort_keys=True)]
    parse_notes: list[str] = []
    synth, flags = _validate(_parse(chosen, parse_notes), mech, ticker=ticker, name=name)
    flags += parse_notes
    if synth is not None and agreement is not None:
        synth = synth.model_copy(update={"draw_agreement": agreement})
        if not agreement.unanimous and not gate.passes:
            # SAID OUT LOUD ON THE PAGE, not only in the log: the reader is entitled to know the
            # read was not reproduced, because the proposal it would have carried is withheld.
            flags.append(
                f"synthesis draws DISAGREED — {agreement.completed} draw(s) of {attempted} gave "
                f"{dict(tally)}; the machine proposal is withheld and the kept read is the first "
                f"draw carrying the modal label (a tally of this build, never a rate)")
        elif (not gate.passes and gate.lean in COMMITTED_LEANS
              and agreement.completed < attempted):
            # the completed draws agreed, but R1 reads the draws ATTEMPTED (R3): a failed draw is
            # dissent, never a vote the build did not take
            flags.append(
                f"synthesis draws: only {gate.count} of {attempted} draws carry {gate.lean!r} "
                f"({attempted - agreement.completed} failed, counted as dissent) — under the "
                f"{gate.required}-of-{attempted} rule the machine proposal is withheld (a tally "
                f"of this build, never a rate)")
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


#: The statement a material figure's effect is stated on (`MaterialFigure.statement`).
INCOME_STATEMENT = "Income Statement"

#: (2026-11-05) THE DIRECTION WORDS `material_direction_flags` reads: the coordinator's two
#: lists with their inflections, plus the common words outside them (review round 2). A COST word
#: frames a figure as taking from earnings, a GAIN word as adding to them. Whole words only:
#: "costly", "surcharge" and "regained" are not read.
#:
#: INCOME AND EARNINGS ARE THE MEASURE, NEVER A DIRECTION (review round 2). "reduces reported
#: income" frames a cost and "lifts reported income" a gain, so only what is DONE to the measure
#: is read (`_EFFECT_COST`, `_EFFECT_GAIN`). The item's own name for a gain, "non-operating
#: income" or "other income", is read as a gain.
_EARNINGS = r"(?:income|earnings|profits?|EPS)"
#: up to 40 characters between the verb and its object, a period only inside a number
#: ("ADDS $2,800.0M to pre-tax income", #920's echo)
_GAP = r"(?:[^.;]|\.(?=\d)){0,40}?"
_EFFECT_COST = (rf"\b(?:subtract|reduc|depress|cut|lower|dent)\w*\b{_GAP}\b{_EARNINGS}\b")
_EFFECT_GAIN = (rf"\b(?:add(?:s|ed|ing)?|lift(?:s|ed|ing)?|rais(?:e|es|ed|ing)|increas\w*)\b"
                rf"{_GAP}\b{_EARNINGS}\b")
_COST_WORD = re.compile(
    r"\b(?:charg(?:e|es|ed)|costs?|drags?|expens(?:e|es|ed)|loss(?:es)?|write-?\s?downs?|"
    r"write-?\s?offs?|impairments?|impaired|burdens?|dilut(?:ive|ion|es|ed|ing)|headwinds?|"
    r"penalt(?:y|ies)|penali[sz]\w*|weigh(?:s|ed|ing)?\s+on|hit(?=\s*(?:[.;,)]|$|to\b|on\b)))\b"
    rf"|{_EFFECT_COST}", re.IGNORECASE)
_GAIN_WORD = re.compile(
    r"\b(?:gains?|benefit(?:s|ed|ted)?|inflat(?:e|es|ed|ing)|boost(?:s|ed|ing)?|"
    r"flatter(?:s|ed|ing)?|tailwinds?|non-?operating\s+income|other\s+income)\b"
    rf"|{_EFFECT_GAIN}", re.IGNORECASE)
#: Phrases that carry a direction word and frame NO figure, removed before the words are read:
#: - BOTH DIRECTIONS AT ONCE, the accounting labels' own form: "Gain (Loss)", "(Gain) Loss",
#:   "gains and losses", "Income (Expense)";
#: - A LOSS MEASURE NAMED, not a figure framed: "net loss", "operating loss", "pre-tax loss";
#: - a cost LINE named: "cost of revenue", "cost of sales", "cost of goods".
_NEUTRAL_DIRECTION = re.compile(
    r"\bgains?\s*\(\s*loss(?:es)?\s*\)|\(\s*gains?\s*\)\s*loss(?:es)?"
    r"|\bgains?\s*(?:/|&|\band\b|\bor\b)\s*loss(?:es)?\b"
    r"|\bincome\s*\(\s*expense\s*\)|\(\s*income\s*\)\s*expense\b"
    r"|\b(?:net|operating|pre-?tax|gross|comprehensive)\s+loss(?:es)?\b"
    r"|\bcost\s+of\s+(?:revenue|sales|goods)\b",
    re.IGNORECASE)


def _neutral(text: str, *, label: str | None = None) -> str:
    """``text`` with every phrase that frames no figure blanked: the both-ways and measure
    phrases (`_NEUTRAL_DIRECTION`) and, given one, the row's own LABEL. A label's words do not
    count — "Gain (Loss) On Sale Of Invest." is the row's name, not a framing — so the label is
    matched as a phrase, loosely, the way prose writes it: case-free, "R&D" for "R & D", "and"
    for "&", a word lengthened ("Restructuring" for "Restruct.") or made singular ("Charge" for
    "Charges"). The caller passes no label when the label's own word contradicts the sign
    (`_framing`): then calling the figure by its label IS a framing."""
    if label and (phrase := _label_phrase(label)) is not None:
        text = phrase.sub(" ", text)
    return _NEUTRAL_DIRECTION.sub(" ", text)


@functools.lru_cache(maxsize=64)
def _label_phrase(label: str) -> re.Pattern[str] | None:
    """The row label as a loose phrase (`_neutral`), built once per label."""
    words = re.findall(r"[A-Za-z]+", label.removesuffix(" ($M)"))
    stems = [w[:-1] if len(w) > 3 and w.lower().endswith("s") else w for w in words]
    if not stems:
        return None
    phrase = r"(?:[\s&().,/-]|\band\b)*".join(rf"{re.escape(s)}\w*" for s in stems)
    return re.compile(rf"\b{phrase}", re.IGNORECASE)


def _direction_words(text: str) -> tuple[list[str], list[str]]:
    """(cost words, gain words) in ``text``, each once (case-free), as first written."""
    def found(rx: re.Pattern[str]) -> list[str]:
        out: dict[str, str] = {}
        for m in rx.finditer(text):
            out.setdefault(m.group().lower(), m.group())
        return list(out.values())
    return found(_COST_WORD), found(_GAIN_WORD)


def _framing(text: str, fig: MaterialFigure) -> tuple[list[str], list[str]]:
    """(cost, gain) direction words in a claim stating ``fig``, once `_neutral` has blanked what
    frames no figure. The row's label is blanked only when it does not contradict the sign: NFLX's
    "A $2,800.0M Merger & Related Restruct. Charge …" calls a gain by a cost word (review round 2,
    the incident's own shape)."""
    blank = fig.label if fig.label_against_sign is None else None
    return _direction_words(_neutral(text, label=blank))


@dataclass(frozen=True)
class MaterialFigure:
    """One figure item 19c demands the synthesis prose state: a material row's value, the actual
    columns carrying it, and the annual table's source_ref (rows carry none of their own)."""

    label: str
    periods: tuple[str, ...]
    value: float
    source_ref: str | None

    @property
    def stated(self) -> str:
        """How the prompt asks for it: millions to one decimal, the EXACT form. Never the 1-dp
        billions form the guard also accepts — a ±$50M bucket in which one citation could
        satisfy two demands (`_figure_cited`); the prompt must not invite it.

        UNSIGNED, AND IT STAYS UNSIGNED (2026-11-05). A reader writes "a $2,800.0M gain", never
        "+$2,800.0M", and the guard matches the absolute value. The direction is stated BESIDE
        this form (`effect`) and read back by a flag (`material_direction_flags`); putting it in
        the form the guard demands would make the framing a refusal, which needs a ruling."""
        return f"${abs(self.value):,.1f}M"

    @property
    def statement(self) -> str | None:
        """The statement the row is read from, or None when that cannot be told. Only CIQ's
        Income Statement unusual-items rows are named (`materiality.UNUSUAL_ITEM_LABELS`): every
        material row on the 28 committed pages is one, and no other row's sign convention has been
        measured. A Cash Flow row is never material today (`_CORE_BRIEF_LABELS`)."""
        base = self.label.removesuffix(" ($M)")
        return INCOME_STATEMENT if base in UNUSUAL_ITEM_LABELS else None

    @property
    def effect(self) -> str | None:
        """Which way the figure moves pre-tax income, read off the SIGN alone — accounting fact,
        not a view. On CIQ's Income Statement an unusual item adds to pre-tax income when positive
        and subtracts when negative (measured, `UNUSUAL_ITEM_LABELS`). None for a row from no
        identified statement: a direction stated without the convention would be a guess."""
        if self.statement != INCOME_STATEMENT:
            return None
        if self.value > 0:
            return f"it ADDS {self.stated} to pre-tax income (a gain)"
        return f"it SUBTRACTS {self.stated} from pre-tax income (a charge)"

    @property
    def label_against_sign(self) -> str | None:
        """The label's own direction word, when it points against the sign — NFLX's +2,800.0 on
        'Merger & Related Restruct. Charges'. None for a label with no direction word of its own
        ('Gain (Loss) …' names both, 'Legal Settlements' neither) or one that agrees."""
        if self.effect is None:
            return None
        cost, gain = _direction_words(_neutral(self.label.removesuffix(" ($M)")))
        if self.value > 0 and cost and not gain:
            return cost[0]
        if self.value < 0 and gain and not cost:
            return gain[0]
        return None

    def cited_in(self, prose: str) -> bool:
        return _figure_cited(prose, self.value)

    def __str__(self) -> str:
        return f"{self.label} {'/'.join(self.periods)} = {self.value:,.1f}"


def demanded_material_figures(mech: MechanicalLayer) -> list[MaterialFigure]:
    """THE ONE SELECTION of the figures item 19c demands — read by the guard
    (`uncited_material_figures`) and by the prompt (`synthesize`), so the model is asked for
    exactly what a draw is refused for omitting (audit D-D5 follow-up: two 2026-10-29 rebuild
    pages paid five draws each and were refused for a figure no line of the prompt named).

    It reads the rows ALREADY marked material (`assemble._mark_material`); an unmarked table
    demands nothing."""
    fs = getattr(mech, "financial_summary", None)
    ann_src = getattr(fs, "annual", None) if fs is not None else None
    ref = getattr(ann_src, "source_ref", None)
    ann = getattr(ann_src, "value", None)
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

    out: list[MaterialFigure] = []
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
            out.append(MaterialFigure(label=r.label, periods=tuple(seen[v]), value=v,
                                      source_ref=str(ref) if ref else None))
    return out


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
    prose = _synthesis_prose(synth)
    return [str(f) for f in demanded_material_figures(mech) if not f.cited_in(prose)]


def material_direction_flags(synth: Synthesis, mech: MechanicalLayer) -> list[str]:
    """A claim that states a MATERIAL figure and frames it only AGAINST its sign — a QA FLAG.

    THE INCIDENT (NFLX, PR #918, 2026-11-05). The table held +2,800.0 on 'Merger & Related
    Restruct. Charges' — the WBD termination fee, which ADDS to pre-tax income — and the synthesis
    called it "a one-time rather than recurring drag" and "restructuring/aborted-deal costs". The
    presence guard passed: the figure was stated, at the wrong sign. The prompt now states each
    figure's effect (`MaterialFigure.effect`); this reads the draw back, because synthesis
    correctness is stochastic and a told model can still misread.

    WHAT FIRES IT, all deterministic. For each demanded figure from an identified statement, each
    claim stating it (`_located_claims`, `cited_in`) is read for direction words (`_COST_WORD`,
    `_GAIN_WORD`) once the phrases that frame no figure are blanked (`_neutral`). It fires when the
    claim's words point ONLY against the sign: a cost word and no gain word for a figure that adds
    to pre-tax income, or the reverse. The row's label is blanked as its name, UNLESS the label's
    own word contradicts the sign: then calling the figure by it ("a $2,800.0M Merger & Related
    Restruct. Charge") is the framing (review round 2). Income and earnings are the measure, not
    a direction: "reduces reported income" frames a cost and "lifts" it a gain. A figure from no
    identified statement is reported as not checked — never read as a pass.

    THE CLAIM, NOT A SENTENCE: CIQ's labels and company names carry periods ("Restruct.",
    "Invest.", "Bros."), and a sentence split on them cut NFLX's own bear point away from its
    "drag". LIMITS, stated: a claim carrying words of both directions is read as two-sided and not
    flagged — the check cannot tell which word frames the figure; a framing outside the word lists
    is not read — "a negative for", "a positive for", "paid … outflow", "hit" as a verb ("hit a
    record") — and nor is an effect verb more than 40 characters from its "income"/"earnings";
    and it is a FLAG, not a refusal — the operator rules on HARD. The sign is accounting fact;
    whether the figure bears for or against the case is not read."""
    flags: list[str] = []
    claims = _located_claims(synth)
    for f in demanded_material_figures(mech):
        if f.effect is None:
            flags.append(f"MATERIAL-DIRECTION: {f} not checked — the row's statement is not "
                         "identified, so its sign gives no direction here")
            continue
        for where, text in claims:
            if not f.cited_in(text):
                continue
            cost, gain = _framing(text, f)
            if f.value > 0 and cost and not gain:
                frame, words = "a cost", cost
            elif f.value < 0 and gain and not cost:
                frame, words = "a gain", gain
            else:
                continue
            quoted = ", ".join(f"'{w.lower()}'" for w in words)
            flags.append(
                f"MATERIAL-DIRECTION ({where}): frames {f} as {frame} ({quoted}, nothing the other "
                f"way) — but on the {f.statement} {f.effect}, whatever its label says. Read the "
                f"sign, not the label. Claim: “{_snip(text, 120)}”")
    return flags


#: Opens the prompt section that names the figures 19c demands — present only when one is.
MATERIAL_FIGURES_HEADER = "=== MATERIAL FIGURES — STATE EACH ONE ==="

DRAWDOWN_ANCHOR_HEADER = ("=== THE DRAWDOWN WHEN THE THESIS WAS WRITTEN, AND SINCE — the event "
                          "kept dated ===")

#: ONE literal example of the digest's shape: SMPL at its 2026-08-05 underwrite, as its at-anchor
#: part reads on the 2026-11-03 store (the 8-K and exhibit are 0001702744-26-000010's).
_DRAWDOWN_ANCHOR_EXAMPLE = (
    "  at the underwrite (2026-02-06 to 2026-08-05): 2026-04-09 -18.1% earnings (2.02); "
    "2026-04-10 -11.5% earnings (2.02) → source_ref: EOD closes on or before 2026-08-05 (each "
    "move, close to close) and EDGAR 8-K item codes at the gap-down dates, filed by 2026-08-05 "
    "(not blanket-labelled earnings)\n"
    "    outlook then: [SUPERSEDED — filed 2026-04-09, replaced by the guide filed 2026-10-27; "
    "this guide is history, not the current outlook] Updating Fiscal Year 2026 (4) Outlook: • Net "
    "sales expected to range between $1.31 and $1.35 billion… → source_ref: EDGAR 8-K "
    "0001702744-26-000010 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1702744/"
    "000170274426000010/a991_pressreleasexq2x2026.htm\n"
    "  since the underwrite (2026-08-06 to 2026-11-03): no discrete gap-down — no single day of "
    "-10% or worse from 2026-08-06 to 2026-11-03 → source_ref: EOD gap-down detector, 2026-08-06 "
    "to 2026-11-03: none")


def _drawdown_anchor_digest(dumped: dict[str, Any]) -> str | None:
    """The prompt section for a name with a drawdown anchor (`DrawdownAnchor`): both dated parts,
    one line each (window → per-gap date, move and cause → source_ref, then the outlook it
    furnished → source_ref), and the question the anchor exists to ask — has the original cause
    played out. Read from ``dumped``, the facts as the prompt carries them, so the outlook here
    wears the same vintage mark as there. None for a name with no anchor: its prompt is unchanged.

    One literal example (`_DRAWDOWN_ANCHOR_EXAMPLE`, SMPL's), shape only:
      at the underwrite (2026-02-06 to 2026-08-05): 2026-04-09 -18.1% earnings (2.02); … →
      source_ref: EOD closes on or before 2026-08-05 (…) and EDGAR 8-K item codes … (…)
    No direction is given: where the evidence bears is the model's to frame, and no verdict."""
    from datetime import date as _date

    from vinci.dossier.schemas import DRAWDOWN_ANCHOR_WORDS

    anchor = (dumped.get("drawdown_cause") or {}).get("anchor")
    if not isinstance(anchor, dict):
        return None
    kind, on = str(anchor.get("kind")), str(anchor.get("on"))
    word = DRAWDOWN_ANCHOR_WORDS.get(kind, ("", "", kind))[2]
    at = anchor.get("at_anchor") or {}
    # the window's length from the part's own dates, never a restated constant
    days = (_date.fromisoformat(str(at.get("end")))
            - _date.fromisoformat(str(at.get("start")))).days

    def part(label: str, w: Any) -> list[str]:
        if not isinstance(w, dict):
            return [f"  {label}: no session after the {word} yet"]
        shape = w.get("shape") or {}
        head = f"  {label} ({w.get('start')} to {w.get('end')}): "
        lines = [head + (f"{shape.get('value')} → source_ref: {shape.get('source_ref')}"
                         if shape.get("status") == "present"
                         else f"UNKNOWN — {shape.get('note')}")]
        rg = w.get("revised_guidance") or {}
        if rg.get("status") == "present":
            text = " ".join(str(rg.get("value")).split())
            text = text if len(text) <= 360 else text[:357].rstrip() + "…"
            lines.append(f"    outlook then: {text} → source_ref: {rg.get('source_ref')}")
        return lines

    lines = [
        DRAWDOWN_ANCHOR_HEADER,
        f"This name is anchored at its {word} ({on}; {anchor.get('source_ref')}). The current "
        "window in the facts (`drawdown_cause.shape` and its siblings) ROLLS with the page's "
        "date, so the event the thesis was written on can have left it. `drawdown_cause.anchor` "
        f"keeps it, in two dated parts: `at_anchor`, the {days} days ending on the anchor date, "
        "read only from what was knowable then (closes on or before it, 8-Ks filed by it); and "
        "`since`, the day after the anchor to the page's price date.",
        "SHAPE — one line per part: part (start to end): date move cause; … → source_ref, then "
        "the outlook that part's 8-K furnished → source_ref. EXAMPLE (SMPL at its 2026-08-05 "
        "underwrite) — the SHAPE only; cite only this name's lines:",
        _DRAWDOWN_ANCHOR_EXAMPLE,
        "THIS NAME:",
        *part(f"at the {word}", anchor.get("at_anchor")),
        *part(f"since the {word}", anchor.get("since")),
        f"ASK: has the cause named at the {word} played out? Set the since part and the current "
        "facts against it — did the outlook that came with the drop hold, get cut again, or "
        "recover; did a later drop repeat the cause or name a new one. Answer inside your points "
        "(a bull or bear point, or the decisive question's evidence), citing these source_refs "
        "verbatim; where the facts cannot tell, say so in key_unknowns. An outlook marked "
        "SUPERSEDED is history, never the current guide.",
    ]
    return "\n".join(lines)


def _material_figures_digest(figs: list[MaterialFigure]) -> str:
    """The prompt section: each figure the guard will demand, in a form it accepts, with the ref a
    point stating it cites — and its SIGNED value with which way it moves pre-tax income.

    THE SIGN IS ACCOUNTING FACT, NOT A VIEW (2026-11-05). Each line states the signed value and,
    for an Income Statement unusual item, its effect on pre-tax income, derived from the sign
    alone (`MaterialFigure.effect`); where the label's own direction word points the other way,
    the line says so. The first cut printed NFLX's +2,800.0 'Merger & Related Restruct. Charges'
    as `2,800.0 in the table; write "$2,800.0M"` and called itself directionless — so the label's
    "Charges" was the only direction the line gave, and the synthesis called a gain a charge. A
    row from no identified statement gets its signed value and no effect: a direction stated
    without its convention would be a guess. Whether a figure bears FOR or AGAINST the case stays
    the model's to frame; nothing here names a lean or a verdict."""
    lines = [
        MATERIAL_FIGURES_HEADER,
        "Each row below is marked material in the annual financial summary of the facts above. "
        "State EVERY figure listed, written as shown, in at least one entry of "
        f"{', '.join(SYNTHESIS_CLAIM_LISTS)}: wherever it bears on the argument, or in "
        "key_unknowns where it bears on neither case. A point that states one cites the listed "
        "source_ref. A synthesis that does not state each listed figure is REFUSED. Each line "
        "gives the figure's SIGNED value in the table and, for an Income Statement unusual item, "
        "which way it moves pre-tax income: accounting fact, read off the sign, never off the "
        "row's label (on CIQ's Income Statement an unusual item printed positive adds to pre-tax "
        "income and one printed negative subtracts). Describe each figure the way it moves; "
        "whether that bears for or against the case is yours to frame.",
    ]
    for f in figs:
        # A form the guard would not accept would ask for a refusal; never offer one.
        if not f.cited_in(f.stated):
            raise ValueError(f"{f}: the stated form {f.stated!r} fails `_figure_cited`")
        ref = f"; source_ref: {f.source_ref}" if f.source_ref else ""
        if f.effect is None:
            how = ("from a statement this line cannot identify, so no effect on pre-tax income "
                   "is stated")
        else:
            how = f"an {f.statement} unusual item: {f.effect}, whatever the row's label says"
            if (word := f.label_against_sign) is not None:
                how += (f'; the label\'s own word "{word}" points the other way, and the sign '
                        "decides")
        lines.append(f"- {f.label}, {'/'.join(f.periods)}: {f.value:+,.1f} in the table, {how}; "
                     f'write "{f.stated}"{ref}')
    return "\n".join(lines)


def _located_claims(synth: Synthesis) -> list[tuple[str, str]]:
    """Every free-text claim the synthesis makes, with WHERE it sits — the field name a flag
    reports. One enumeration for the claim-level lints, so two of them cannot cover different
    fields."""
    texts: list[tuple[str, str]] = []
    if synth.evidence_balance:
        texts.append(("evidence_balance", synth.evidence_balance))
    texts += [("bull_point", p.claim) for p in synth.bull_points]
    texts += [("bear_point", p.claim) for p in synth.bear_points]
    texts += [("key_unknown", u) for u in synth.key_unknowns]
    texts.append(("decisive_question", synth.decisive_question.question))
    texts += [("decisive.for", p.claim) for p in synth.decisive_question.evidence_for]
    texts += [("decisive.against", p.claim) for p in synth.decisive_question.evidence_against]
    return texts


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
    flags: list[str] = []
    for where, txt in _located_claims(synth):
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


# --- GAAP-EPS momentum: a GAAP consensus move that operating EPS did not make ---------------------

#: A claim that names GAAP EPS — 'GAAP EPS', 'GAAP-EPS', 'GAAP diluted EPS', 'EPS (GAAP)'. A bare
#: 'EPS' is not enough: on CIQ's sheets the unqualified figure is the normalized one (NCNO's
#: "FY27 EPS revised net +34%" is the normalized move, 0.93 → 1.25).
_GAAP_EPS = re.compile(r"\bGAAP[\s-]+(?:diluted\s+)?EPS\b|\bEPS\s*\(GAAP\)", re.IGNORECASE)
#: A percentage the claim states, with its sign when it carries one: '+71%', '-43%', '−29%', '26%'.
_CLAIM_PCT = re.compile(r"([+\-−]?)\s*(\d+(?:\.\d+)?)\s*%")
#: How far apart, in percentage points over ONE window, the GAAP and normalized EPS consensus moves
#: may sit before the GAAP move stops describing operating momentum. FACE VALIDITY — a ten-point
#: disagreement over one window is not a rounding difference — stated with its sensitivity rather
#: than tuned: on the 26 committed pages (2026-10-07) the claims citing the current-FY GAAP move sit
#: at 60 (AMZN), 33 (AORT, CNXC) and 21 (WERN) points, and the nearest one below sits at 4 (V), so
#: any threshold from 5 to 20 gives the same answer today. Nothing here reads a forward return.
EPS_MOMENTUM_GAP = 0.10
#: A stated percentage matches a move when it is within this many points of it — the prose rounds.
_PCT_MATCH_PTS = 1.5


_EpsMove = tuple[str, int, float, float, float, float, float, float]
#: The longest lookback the synthesis is shown: `acceleration_read` prints the current-FY consensus
#: path back to 12 months, and a claim's percentage is that path's net change.
_ACCEL_MAX_MONTHS = 12


def _eps_move(fc: ForwardConsensus) -> _EpsMove | None:
    """(period, months, gaap move, normalized move, gaap then, gaap now, norm then, norm now) — the
    ONE move a claim can be citing: the current fiscal year, over the longest lookback up to 12
    months, which is what `acceleration_read` puts in front of the synthesis. The normalized move
    is taken over that SAME window or not at all — two halves of a comparison share a window
    (RUNBOOKS §m). None when either base is not positive: a sign-crossing or loss-making base
    has no percentage move.

    ONE MOVE, NOT EVERY WINDOW, AND THE CORPUS IS WHY. Matching a claim's percentage against every
    period and window found coincidences on the first real run: SMPL's GAAP-EPS SURPRISE of -9%
    matched a FY2028 six-month consensus move, AORT's 'EBT (GAAP) -79%' matched a three-month EPS
    move, and CNXC's '-43% (12m→latest)' was reported against its nine-month window."""
    if not fc.periods:
        return None
    period = fc.periods[0]
    paths = {(p.metric, p.period): {pt.months_ago: pt.value for pt in p.points} for p in fc.paths}
    gaap, norm = paths.get(("EPS (GAAP)", period)), paths.get(("EPS Normalized", period))
    if not gaap or not norm or 0 not in gaap or 0 not in norm:
        return None
    months = max((m for m in gaap if 0 < m <= _ACCEL_MAX_MONTHS), default=None)
    if months is None or months not in norm:
        return None
    g0, n0 = gaap[months], norm[months]
    if g0 <= 0 or n0 <= 0:
        return None
    return (period, months, (gaap[0] - g0) / g0, (norm[0] - n0) / n0, g0, gaap[0], n0, norm[0])


def gaap_eps_momentum_flags(synth: Synthesis, fc: ForwardConsensus | None) -> list[str]:
    """Flag a claim that cites a GAAP-EPS consensus MOVE which normalized EPS did not make over the
    same window — a human CAVEAT, because it changes how the claim should be read; never a block.

    THE INCIDENT. AMZN's committed synthesis argues the bull case from "FY26E GAAP EPS +71%". Over
    the same 12 months normalized FY26 EPS moved +10% (7.54 → 8.31): the GAAP move came in one step
    at the Q2 report, from below-the-line gains the page itself records (+$53.4bn that quarter). A
    re-assembly can repeat the claim and nothing flagged it.

    WHAT FIRES IT, all deterministic: the claim names GAAP EPS; it states a percentage within
    `_PCT_MATCH_PTS` of the current-FY GAAP consensus move the synthesis was shown (`_eps_move`;
    sign-checked when the claim gives one); and over that window the normalized move differs by
    `EPS_MOMENTUM_GAP` or more. The
    direction does not matter — a GAAP cut that is mostly charges (CNXC: −43% against −10%)
    overstates deterioration exactly as AMZN's gain overstates momentum.

    DOES IT SELECT ON FORM? No: it reads the size of two consensus moves and the figure the claim
    cites, not how either is disclosed. LIMITS, stated: a claim citing GAAP EPS LEVELS without a
    percentage, or GAAP net income, is not read here; and another figure in the same claim that
    equals the GAAP move within the tolerance is read as citing it."""
    move = _eps_move(fc) if fc is not None else None
    if move is None or abs(move[2] - move[3]) < EPS_MOMENTUM_GAP:
        return []
    period, months, g, n, g0, g1, n0, n1 = move
    flags: list[str] = []
    for where, text in _located_claims(synth):
        if not _GAAP_EPS.search(text):
            continue
        if not any(abs(abs(g) * 100 - float(num)) <= _PCT_MATCH_PTS
                   and (not sign or (sign == "+") == (g > 0))
                   for sign, num in _CLAIM_PCT.findall(text)):
            continue
        flags.append(
            f"GAAP-EPS-MOMENTUM {where}: '{_snip(text, 120)}' — over the {months} months to the "
            f"latest, {period} GAAP EPS consensus moved {g:+.0%} ({g0:,.2f} → {g1:,.2f}) while "
            f"normalized EPS moved {n:+.0%} ({n0:,.2f} → {n1:,.2f}). The gap is items CIQ's "
            "normalized figure excludes — one-offs and non-operating gains or charges — so it is "
            "not operating momentum; read the normalized move")
    return flags
