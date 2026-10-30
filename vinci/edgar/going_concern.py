"""Does a filing STATE that this issuer has going-concern doubt? — one detector, two consumers.

WHY THIS EXISTS. Two places asked that question and both answered it by matching the PHRASE rather
than the CLAIM:

- the dossier's filing reader (:mod:`vinci.edgar.filing_sections`) matched
  ``raise substantial doubt about … going concern`` anywhere in a 10-Q;
- the ranker's structural demote (:mod:`vinci.rank.structural`) matched a bare
  ``going concern|substantial doubt`` anywhere in an 8-K body, and SANK the name for it.

Measured on the live corpus, that cost both surfaces. On the dossier: TECX's page asserted
``substantial_doubt: true`` for a company holding $227.1M and guiding runway into Q1 2029, and the
synthesis then wrote a **strongly-bearish** verdict citing "a stated going-concern doubt". On the
ranker: 10 of 268 queue names were sunk and **4 of them wrongly** (measured 2026-09-01).

THE TWO FAILURE FAMILIES, both from real filings, both fixed here.

**(1) The EVALUATION frame is not a conclusion.** Every filer subject to ASU 2014-15 writes a
sentence saying it PERFORMED the assessment, and that sentence necessarily contains the trigger
phrase. The conclusion is a SEPARATE sentence. The two live cases sit either side of it:

  TECX  "…the Company has EVALUATED WHETHER there are conditions … that raise substantial doubt…"
        followed by "The Company believes that its existing cash … will be sufficient …" → NO doubt
  MVST  "Management EVALUATED WHETHER conditions … raise substantial doubt…"
        followed by "THESE CONDITIONS AND EVENTS RAISE SUBSTANTIAL DOUBT…"                → DOUBT

So an evaluation sentence is SKIPPED and the scan continues; a name that really has doubt states it
in a sentence of its own, which is what fires. Matching the first sentence found is what made TECX
and MVST indistinguishable.

**(2) "Going concern" has three meanings, and two are not distress.** From the sunk queue names:

  EOSE  "…other GOING CONCERN VALUE with respect to the frontier power platform…"
                                            → a VALUATION term, not distress.
  TLRY  "…with the intent for Tilray UK to carry on the acquired business AS A GOING CONCERN."
                                            → M&A/insolvency sense: *as an operating business*.
                                              Tilray was the BUYER — the opposite of distress.
  BKKT  "…business plans or strategies; the Company's ability to continue as a going concern;
         the Company's ability to grow…"     → one item in a semicolon SAFE-HARBOR RISK LIST,
                                              which nearly every earnings release contains.
  PPTA  "…that we will be able to discharge our liabilities … and continue as a going concern.
         Forward-Looking Information are based on certain material assumptions…"
                                            → a forward-looking ASSUMPTION that they WILL continue.

None of those carries a doubt marker, which is what separates them from the real ones:

  SOC   "…such reports contained an EXPLANATORY PARAGRAPH regarding the Company's ability to
         continue as a going concern."                                                → DOUBT
  HYMC  "…contained an explanatory paragraph regarding a GOING CONCERN UNCERTAINTY."   → DOUBT
  KDK / ONDS / USAR  "…SUBSTANTIAL DOUBT about the Company's ability to continue…"     → DOUBT

DEMOTE-ONLY → BIAS TO PRECISION. This is the rule the sibling auditor-exit signal already states in
``vinci/rank/structural.py`` ("an ambiguous dismissal stays unflagged — safe under-demote; the name
still reaches the dossier"). The going-concern leg did not follow it; now it does. An ambiguous
mention is NOT doubt. Under-flagging leaves a distressed name in the queue for a human to judge;
over-flagging removes a solvent one silently, and — as TECX proved — feeds a false premise into a
synthesis that then reads as a confident verdict.

**(3) Negation, modality and the frame, read as stated (audit E2-D17, 2026-10-30).** Grown from
the 583 cached SEC filings that mention a going concern, each rule against a sentence it misread:

  EOSE  "…management has concluded that there is NO LONGER substantial doubt…"
                                                      → DENIED, was read as DOUBT
  ACRS  "…the Company DOES NOT BELIEVE that substantial doubt exists…"
                                                      → DENIED, was read as DOUBT
  RLMD  "…management's plans ALLEVIATED substantial doubt…"
                                                      → DENIED, was read as DOUBT
  ZURA  "…financial condition COULD RAISE substantial doubt…"
                                                      → a HYPOTHETICAL risk factor, read as DOUBT
  WOLF  "…management CONSIDERS WHETHER there are conditions…"
                                                      → the FRAME, read as DOUBT
  WOLF  "…management has concluded that there is substantial doubt…, IN ACCORDANCE WITH the
        requirements of ASC 205-40…"                  → DOUBT, read as None: citing the standard
                                                        is not the frame
  XIAO  "The management plan CANNOT ALLEVIATE the substantial doubt…"
                                                      → DOUBT, read as None

The frame is now the QUESTION ("evaluates/considers/concludes WHETHER …") or the disclosure POLICY,
never a citation of the standard, and a frame sentence that states its own conclusion is a
conclusion. A denial must name the doubt it denies; "alleviate" denies it only where nothing
negates it ("cannot alleviate" is doubt). A hypothetical needs its modal ON the doubt ("could raise
substantial doubt"): "could raise additional capital" beside a real conclusion is not one.

EVERY marker below was demanded by a REAL filing quoted above. The lists stay CLOSED: grow them
from an observed miss, never speculatively.
"""

from __future__ import annotations

import re
from typing import NamedTuple

#: The trigger — a mention of the concept at all. Cheap; everything else narrows it.
_MENTION = re.compile(r"going\s+concern", re.I)

#: An AFFIRMATIVE doubt marker. Without one of these in the same sentence, a "going concern"
#: mention is not a claim that this issuer is in doubt. "explanatory paragraph" is the auditor's
#: term of art and carries the claim on its own (SOC, HYMC) — it is why an auditor's report is
#: qualified, and no filer writes it about a healthy balance sheet.
_DOUBT = re.compile(
    r"substantial\s+doubt|going\s+concern\s+(?:uncertaint|qualification|matter|issue)|"
    r"explanatory\s+paragraph|material\s+uncertaint",
    re.I,
)

#: The ASU 2014-15 EVALUATION frame — a sentence saying the assessment is PERFORMED, the QUESTION
#: it asks ("evaluated whether", WOLF's "considers whether", the auditor's "Conclude whether") or
#: the disclosure POLICY (WVE). It always contains the trigger phrase, so it is skipped rather than
#: matched, and the scan CONTINUES past it: the conclusion is a later sentence (MVST). A citation
#: of the standard is NOT the frame (E2-D17): WOLF concludes doubt "in accordance with … ASC
#: 205-40" in the sentence that states it.
_EVALUATION_FRAME = re.compile(
    r"(?:evaluat|assess|consider|conclud|determin)\w*\s+whether|"
    r"required\s+to\s+make\s+certain\s+additional\s+disclosures",
    re.I,
)

#: A conclusion OF DOUBT stated in the frame's own sentence ("evaluated whether … and concluded
#: that these conditions raise substantial doubt"): then the sentence is a result. A conclusion of
#: sufficiency is not one — CRVS "evaluated whether … and concluded that our existing cash … are
#: sufficient" stays a frame.
_CONCLUSION = re.compile(
    r"\b(?:concluded|determined)\s+that\b[^.;]{0,200}?"
    r"\b(?:raised?|raises|is|exists?|was)\s+(?:a\s+)?substantial\s+doubt",
    re.I,
)

#: "Going concern VALUE" is a valuation concept (EOSE), never a distress statement.
_VALUATION_SENSE = re.compile(r"going\s+concern\s+value", re.I)

#: An explicit denial. A filer that concluded there is NO doubt says so, and the sentence still
#: contains both the phrase and a doubt marker. Each form names the doubt it denies (E2-D17):
#: "do not raise substantial doubt", EOSE's "no longer substantial doubt", MAR's "no material
#: uncertainty exists", ACRS's "does not believe that substantial doubt exists", and a doubt "has
#: been alleviated" (an issuer whose 2025 offering closed). "Alleviate" as a verb is `_ALLEVIATES`.
_NEGATED = re.compile(
    r"\b(?:no|not|does\s+not|do\s+not|did\s+not|never)\s+(?:\w+\s+){0,4}"  # "casino" is no "no"
    r"(?:raise|indicate|create)\s+substantial\s+doubt|"
    r"\bno\s+(?:longer\s+)?(?:substantial\s+doubt|material\s+uncertaint)|"
    r"\bnot\s+believe\s+(?:that\s+)?(?:there\s+(?:is|exists)\s+)?substantial\s+doubt|"
    r"substantial\s+doubt\b[^.;]{0,160}?\b(?:has|have|had|was|were)\s+(?:been\s+)?alleviated",
    re.I,
)

#: "…plans alleviated substantial doubt" (RLMD) denies the doubt — unless a negator governs the
#: verb: XIAO's "cannot alleviate the substantial doubt" says the doubt REMAINS.
_ALLEVIATES = re.compile(r"\balleviat\w*\s+(?:the\s+)?substantial\s+doubt", re.I)
_NEGATOR_BEFORE = re.compile(r"\b(?:not|cannot|can't|unable|insufficient|no)\b[^.;]{0,40}$",
                             re.I)

#: A HYPOTHETICAL: a modal ON the doubt itself — a risk factor saying what COULD happen (ZURA's
#: "could raise substantial doubt", MNLK's "may conclude that there is substantial doubt",
#: "substantial doubt could exist"). The modal must govern the doubt: "could raise additional
#: capital" in a real conclusion is not one, and SANA's "may not be sufficient …, and there is
#: substantial doubt" still states it.
_HYPOTHETICAL = re.compile(
    r"\b(?:may|might|could|would)\s+(?:also\s+)?(?:raise|create|cast)\s+(?:a\s+)?"
    r"(?:substantial|significant)\s+doubt|"
    r"\b(?:may|might|could|would)\s+(?:also\s+)?conclude\s+that\s+(?:there\s+is\s+)?(?:a\s+)?"
    r"substantial\s+doubt|"
    r"substantial\s+doubt\s+(?:may|might|could|would)\s+(?:exist|arise)|"
    # a future auditor's report that "may also contain statements expressing substantial doubt"
    r"\b(?:may|might|could|would)\s+(?:also\s+)?contain\s+(?:\w+\s+){0,2}"
    r"(?:expressing|regarding|about)\s+substantial\s+doubt|"
    # MNLK "If we seek additional financing … and there remains substantial doubt …": the doubt is
    # the condition. A comma ends the clause, so SOCC's "…, if at all, substantial doubt exists"
    # still states it.
    # (a concessive "even if" states the doubt whatever the condition)
    r"(?<!even\s)\bif\b[^,.;]{0,120}?\bthere\s+(?:is|remains|exists)\s+(?:a\s+)?"
    r"substantial\s+doubt",
    re.I,
)

#: FORWARD-LOOKING framing. A filer that HAS doubt also lists it among the topics its
#: forward-looking statements cover, so these sentences are real but are BOILERPLATE ABOUT the
#: disclosure rather than the disclosure. They are DE-PREFERRED, never excluded: excluding them
#: would lose USAR, whose only mention is a numbered risk-factor item that nonetheless ASSERTS the
#: doubt ("(24) substantial doubt regarding the Company\'s ability to continue…"). MVST is why the
#: preference exists — it carries 12 qualifying sentences and the first is FLS boilerplate, so the
#: page would have cited that instead of "These conditions and events raise substantial doubt…".
#: The VERDICT is unchanged either way; this decides which sentence gets quoted as provenance.
_FORWARD_LOOKING = re.compile(
    r"forward[- ]looking|could\s+cause\s+actual\s+results|"
    r"differ\s+materially\s+from\s+the\s+anticipated",
    re.I,
)

#: How far either side of a mention to take as its sentence. Bounded so a safe-harbor paragraph
#: (BKKT's runs to thousands of characters) cannot drag in a doubt marker from far away.
_SENTENCE_CAP = 600


class GoingConcernStatement(NamedTuple):
    """A filing sentence that STATES this issuer has going-concern doubt."""

    sentence: str
    start: int


def _sentence_around(text: str, pos: int) -> tuple[str, int]:
    """The sentence containing ``pos``, bounded by :data:`_SENTENCE_CAP` either side."""
    lo = text.rfind(". ", max(0, pos - _SENTENCE_CAP), pos)
    lo = (lo + 2) if lo != -1 else max(0, pos - _SENTENCE_CAP)
    hi = text.find(". ", pos, pos + _SENTENCE_CAP)
    hi = (hi + 1) if hi != -1 else min(len(text), pos + _SENTENCE_CAP)
    return " ".join(text[lo:hi].split()), lo


def _alleviated(sentence: str) -> bool:
    """The sentence says the doubt was alleviated: an "alleviate" no negator governs."""
    return any(not _NEGATOR_BEFORE.search(sentence[:m.start()])
               for m in _ALLEVIATES.finditer(sentence))


def find_going_concern_statement(text: str) -> GoingConcernStatement | None:
    """The first sentence that STATES going-concern doubt about this issuer, or ``None``.

    Scans EVERY mention rather than stopping at the first: the ASU evaluation frame legitimately
    precedes a real conclusion in the same note (MVST), so stopping early conflates a filer that
    assessed and cleared itself (TECX) with one that assessed and did not.
    """
    fallback: GoingConcernStatement | None = None
    for m in _MENTION.finditer(text):
        sentence, _ = _sentence_around(text, m.start())
        if _VALUATION_SENSE.search(sentence):
            continue                      # "going concern value" — a valuation term
        if _EVALUATION_FRAME.search(sentence) and not _CONCLUSION.search(sentence):
            continue                      # "has evaluated whether …" — an assessment, not a result
        if _NEGATED.search(sentence) or _alleviated(sentence):
            continue                      # the filer says the doubt does NOT exist / was alleviated
        if _HYPOTHETICAL.search(sentence):
            continue                      # "could raise substantial doubt" — what may happen
        if not _DOUBT.search(sentence):
            continue                      # a bare mention: M&A sense, risk list, forward-looking
        hit = GoingConcernStatement(sentence=sentence[:_SENTENCE_CAP], start=m.start())
        if _FORWARD_LOOKING.search(sentence):
            # real, but boilerplate ABOUT the disclosure rather than the disclosure
            fallback = fallback or hit
            continue
        return hit
    return fallback


def states_going_concern_doubt(text: str) -> bool:
    """Boolean form, for callers that only need the verdict."""
    return find_going_concern_statement(text) is not None
