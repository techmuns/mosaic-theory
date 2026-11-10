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

EVERY marker below was demanded by a REAL filing quoted above — with ONE recorded exception, the
markers TeamNostra fix request 2 asked for (RE2-D9, RE2-D10, 2026-11-10): "does not exist", the
present-tense "alleviate", "there will be substantial doubt", the conclusion with its verb after the
doubt or the company "having" it, and the "no" that stops at a conjunction were asked for on
TeamNostra's CONSTRUCTED sentences (document 14, E2-D9/D10). Two of them are live: Solo Brands' 10-Q
0001870600-26-000044 ("These plans alleviate the substantial doubt …") and Aeluma's 10-K
0001213900-25-086227, both read as doubt before; the rest have no corpus case. A filing's own
ALLEVIATION settles the doubt its conditions raised before it — never one stated after it. The lists
stay CLOSED otherwise: grow them from an observed miss, never speculatively.
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

#: The ASU 2014-15 EVALUATION frame — a sentence that asks the QUESTION, cites the STANDARD, or
#: states the disclosure POLICY. It always contains the trigger phrase, so it is skipped rather
#: than matched, and the scan CONTINUES past it: the conclusion is a later sentence (MVST).
#: - THE QUESTION is a "whether" whose object IS the going-concern evaluation: "whether there are
#:   conditions or events" (TECX, MVST, AIRS's "evaluates at each … period whether"), "whether a
#:   material uncertainty exists" (the ISA auditor), "whether the going concern basis …". A
#:   whether-clause about anything else ("assessing whether to file for protection under Chapter
#:   11, and these conditions raise substantial doubt") is no frame (review round 2).
#: - THE STANDARD cited, as main read it ("in accordance with", ASU 2014-15, ASC / Subtopic 205-40,
#:   MNPR's spaced "205 - 40"): policy boilerplate, unless the sentence states its own result.
#: - THE POLICY's own words: WVE's "required to make certain additional disclosures", CSTL's "the
#:   mitigating effect of management's plans … is only considered if".
_EVALUATION_FRAME = re.compile(
    r"\bwhether\b(?:\s*,[^,.;]{0,60},)?\s+(?:there\s+(?:are|is|were|was|exists?)\s+|(?:a|any)\s+)?"
    r"(?:(?:any|such|certain|other)\s+){0,2}"  # LRMR "whether there are certain conditions"
    r"(?:conditions|events|material\s+uncertaint|substantial\s+doubt|(?:the\s+)?going\s+concern)|"
    r"in\s+accordance\s+with|asu\s*2014-15|(?:sub)?topic\s*205\s*-\s*40|asc\s*205\s*-\s*40|"
    r"accounting\s+standards\s+(?:update|codification)|"
    r"required\s+to\s+make\s+certain\s+additional\s+disclosures|"
    r"mitigating\s+effect\s+of\s+(?:management|its\s+plans)",  # CSTL's policy, twice
    re.I,
)

#: A RESULT stated in a frame's own sentence, which makes the sentence a conclusion: "concluded /
#: determined that … raise(d) substantial doubt" or "… that a material uncertainty exists" (WOLF
#: "concluded that there is substantial doubt …, in accordance with … ASC 205-40", the Directors'
#: IFRS form), "these conditions raise substantial doubt" (VSTM, after "in accordance with the
#: applicable accounting standards"), or a plain "there is substantial doubt" no "whether" or
#: "if" asks. A conclusion of sufficiency is not one: CRVS "evaluated whether … and concluded that
#: our existing cash … are sufficient" stays a frame.
_CONCLUSION = re.compile(
    # TeamNostra fix request 2, RE2-D10: a frame's own sentence may state its result with the verb
    # AFTER the doubt ("determined that substantial doubt about the Company's ability to continue
    # as a going concern exists") or as the company HAVING it ("determined that the Company has
    # substantial doubt"); both were skipped as frames, with no flag. A negated verb is no result:
    # "determined that the Company does not have / no longer has substantial doubt" and "…
    # substantial doubt … no longer exists" stay frames (review: they read as DOUBT once widened)
    r"\b(?:concluded|determined)\s+that\b[^.;]{0,200}?(?<!\bnot\s)(?<!\blonger\s)"
    r"\b(?:(?:raised?|raises|is|exists?|was|remains|has|have|had)\s+(?:a\s+)?substantial\s+doubt|"
    r"substantial\s+doubt\b[^.;]{0,160}?(?<!\bnot\s)(?<!\blonger\s)\b(?:exists?|remains)\b|"
    r"(?:a\s+)?material\s+uncertaint\w*\s+(?:exists?|remains))|"
    r"\b(?:these|such)\s+(?:conditions|factors|events|circumstances|matters)\b[^.;]{0,80}?"
    r"\b(?:raise|raises|raised)\s+substantial\s+doubt|"
    r"(?<!whether\s)(?<!if\s)\bthere\s+is\s+(?:a\s+)?substantial\s+doubt",
    re.I,
)

#: A NEGATION OR A MODAL in the words just before a conclusion's doubt (Codex P1, round 1): "does
#: not currently have", "does not appear to have" and "may have substantial doubt" sat beyond the
#: one word the lookbehinds above read, and a framed denial or hypothetical read as DOUBT.
_QUALIFIED = re.compile(r"\b(?:not|never|no\s+longer|may|might|could|would|should|if|whether|"
                        r"unless|appears?|seems?)\b|n['’]t\b", re.I)


def _concludes(sentence: str) -> bool:
    """A frame's sentence states its own result: a `_CONCLUSION` with no negation or modal in the
    sixty characters that lead to its doubt."""
    return any(not _QUALIFIED.search(sentence, max(m.start(), m.end() - 60), m.end())
               for m in _CONCLUSION.finditer(sentence))


#: "Going concern VALUE" is a valuation concept (EOSE), never a distress statement.
_VALUATION_SENSE = re.compile(r"going\s+concern\s+value", re.I)

#: An explicit denial. A filer that concluded there is NO doubt says so, and the sentence still
#: contains both the phrase and a doubt marker. Each form names the doubt it denies (E2-D17):
#: "do not raise substantial doubt", EOSE's "no longer substantial doubt", MAR's "no material
#: uncertainty exists", ACRS's "does not believe that substantial doubt exists"; from review round
#: 2, SHBI's and ADC's "no conditions or events, considered in the aggregate, that raise(d)
#: substantial doubt", DBVT's and PCT's doubt that "is / are no longer present", PSIX's "removal
#: of substantial doubt". A doubt ALLEVIATED is `_ALLEVIATED`.
_NEGATED = re.compile(
    # the words between may not join another clause (RE2-D10): "The Company has no revenue and
    # recurring losses raise substantial doubt" denies nothing — "no" governs "revenue". "or" is no
    # clause break: "do not individually or collectively raise substantial doubt" still denies it
    r"\b(?:no|not|does\s+not|do\s+not|did\s+not|never)\s+(?:(?!(?:and|but)\b)\w+\s+){0,4}"
    r"(?:raise|indicate|create)\s+substantial\s+doubt|"  # "casino" is no "no"
    r"\bno\s+(?:longer\s+)?(?:substantial\s+doubt|material\s+uncertaint)|"
    r"\bnot\s+believe\s+(?:that\s+)?(?:there\s+(?:is|exists)\s+)?substantial\s+doubt|"
    r"\bno\s+(?:such\s+)?conditions\s+(?:or|and)\s+events\b[^.;]{0,80}?\braised?\s+substantial\s+doubt|"
    r"substantial\s+doubt\b[^.;]{0,200}?\b(?:is|are)\s+no\s+longer\s+present|"
    # RE2-D9: "concluded that substantial doubt about … does not exist" denies it
    r"substantial\s+doubt\b[^.;]{0,200}?\b(?:does|do|did)\s+not\s+exist|"
    r"\bremoval\s+of\s+(?:the\s+)?substantial\s+doubt",
    re.I,
)

#: A doubt that HAS BEEN alleviated (RLMD's "plans alleviated substantial doubt", "substantial
#: doubt … has been alleviated") denies it — but only where nothing in the sentence unsettles it.
#: A purpose ("plans to alleviate"), a future ("will alleviate"), "until …", "no assurance …" and
#: XIAO's "cannot alleviate" all leave the doubt standing (review round 2).
_ALLEVIATED = re.compile(
    r"\balleviated\s+(?:the\s+)?substantial\s+doubt|"
    # RE2-D9: "Management's plans alleviate the substantial doubt" states it alleviated too; a
    # purpose ("to") or "can" is no statement (a modal or "not" is `_UNSETTLED`)
    r"(?<!\bto\s)(?<!\bcan\s)\balleviates?\s+(?:the\s+)?substantial\s+doubt|"
    r"substantial\s+doubt\b[^.;]{0,160}?\b(?:is|are|has|have|had|was|were)\s+(?:been\s+)?"
    r"alleviated",
    re.I,
)
#: Unsettles an alleviation before it or inside its own clause. A modal anywhere there is what may
#: be, not what is: "would have alleviated", "will help alleviate", "won't alleviate" (review).
_UNSETTLED = re.compile(
    r"\b(?:not|no|cannot|can['’]t|won['’]t|unable|until|unless|whether|if|assurance|"
    r"will|would|may|might|could|should|shall)\b", re.I)
#: Unsettles an alleviation from a LATER clause too: a condition or a disclaimer attached to it
#: ("…have alleviated the substantial doubt, although there is no assurance …", "…, unless …").
_UNSETTLED_LATER = re.compile(r"\b(?:until|unless|assurance)\b", re.I)

#: A HYPOTHETICAL: a modal ON the doubt — a risk factor saying what COULD happen: ZURA's "could
#: raise substantial doubt", LODE's "could have an immediate material adverse effect on liquidity
#: and raise substantial doubt", AGL's "could in the future, result in substantial doubt", OGN's
#: "could result in a going concern qualification", EBS's "may give rise to substantial doubt",
#: DNTH's "may include an explanatory paragraph", MNLK's "may conclude that there is substantial
#: doubt", "substantial doubt could exist". The modal must reach the doubt within a few words:
#: SANA's "may not be sufficient …, and there is substantial doubt" still states it. "Cast …
#: doubt" is NOT here: in "a material uncertainty exists that may cast significant doubt" the
#: modal belongs to the IFRS / ISA 570 term of art, and the sentence is a conclusion (KYIV, LAR;
#: review round 2).
_HYPOTHETICAL = re.compile(
    r"\b(?:may|might|could|would)\b(?:[\s,]+[\w'’-]+){0,10}?[\s,]+"
    r"(?:rais(?:e|ing)|result(?:ing)?\s+in|give\s+rise\s+to|includ(?:e|ing)|caus(?:e|ing)|create|"
    r"lead\s+to)\s+(?:(?:a|an|the)\s+)?(?:substantial\s+doubt|going\s+concern\s+(?:qualification|"
    r"issue)|explanatory\s+paragraph)|"
    r"\b(?:may|might|could|would)\s+(?:also\s+)?conclude\s+that\s+(?:there\s+is\s+)?(?:a\s+)?"
    r"substantial\s+doubt|"
    r"substantial\s+doubt\s+(?:may|might|could|would)\s+(?:exist|arise)|"
    # RE2-D9: "If …, there will be substantial doubt" is what would follow, not what is
    r"\bthere\s+(?:will|would|may|might|could)\s+be\s+(?:a\s+)?substantial\s+doubt|"
    # a future auditor's report that "may also contain statements expressing substantial doubt"
    r"\b(?:may|might|could|would)\s+(?:also\s+)?contain\s+(?:\w+\s+){0,2}"
    r"(?:expressing|regarding|about)\s+substantial\s+doubt|"
    # MNLK "If we seek additional financing … and there remains substantial doubt …": the doubt is
    # the condition. A comma ends the clause, so SOCC's "…, if at all, substantial doubt exists"
    # still states it (a concessive "even if" states the doubt whatever the condition).
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
    """The sentence says the doubt HAS BEEN alleviated, and nothing unsettles that — before it, or
    inside its own clause. A later clause is another statement (RE2-D9): "…have alleviated the
    substantial doubt …, and the Company does not expect to need additional financing" was read
    as doubt because of that "not". A condition or a disclaimer in a later clause still unsettles it
    (`_UNSETTLED_LATER`)."""
    m = _ALLEVIATED.search(sentence)
    if m is None:
        return False
    end = min((j for j in (sentence.find(c, m.end()) for c in ",;") if j != -1),
              default=len(sentence))
    return not (_UNSETTLED.search(sentence, 0, end) or _UNSETTLED_LATER.search(sentence, end))


def find_going_concern_statement(text: str) -> GoingConcernStatement | None:
    """The first sentence that STATES going-concern doubt about this issuer, or ``None``.

    Scans EVERY mention rather than stopping at the first: the ASU evaluation frame legitimately
    precedes a real conclusion in the same note (MVST), so stopping early conflates a filer that
    assessed and cleared itself (TECX) with one that assessed and did not. An alleviation settles
    the doubt stated BEFORE it (ASC 205-40's alleviated outcome, RE2-D9); a doubt stated after the
    last alleviation still stands.
    """
    fallback: GoingConcernStatement | None = None
    first: GoingConcernStatement | None = None
    for m in _MENTION.finditer(text):
        sentence, _ = _sentence_around(text, m.start())
        if _VALUATION_SENSE.search(sentence):
            continue                      # "going concern value" — a valuation term
        if _EVALUATION_FRAME.search(sentence) and not _concludes(sentence):
            continue                      # "has evaluated whether …" — an assessment, not a result
        if _alleviated(sentence):
            first = fallback = None       # the filer's own plans alleviate the doubt (below)
            continue
        if _NEGATED.search(sentence):
            continue                      # the filer says the doubt does NOT exist
        if _HYPOTHETICAL.search(sentence):
            continue                      # "could raise substantial doubt" — what may happen
        if not _DOUBT.search(sentence):
            continue                      # a bare mention: M&A sense, risk list, forward-looking
        hit = GoingConcernStatement(sentence=sentence[:_SENTENCE_CAP], start=m.start())
        if _FORWARD_LOOKING.search(sentence):
            # real, but boilerplate ABOUT the disclosure rather than the disclosure
            fallback = fallback or hit
            continue
        first = first or hit
    # ALLEVIATED IS ASC 205-40'S OTHER OUTCOME, and it settles the doubt stated before it (RE2-D9).
    # Solo Brands' 10-Q (0001870600-26-000044) says its conditions "raise substantial doubt" and
    # then "These plans alleviate the substantial doubt …": the doubt the conditions raised is the
    # one the plans alleviated, so the filing states no doubt — main quoted the alleviation AS the
    # doubt. A doubt stated AFTER the last alleviation ("In fiscal 2024 … plans alleviated …. As of
    # December 31, 2025 … these conditions raise substantial doubt") is a later doubt, and stands.
    return first or fallback


def states_going_concern_doubt(text: str) -> bool:
    """Boolean form, for callers that only need the verdict."""
    return find_going_concern_statement(text) is not None
