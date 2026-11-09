"""(PR-B Tier B) The FENCED operating-driver extractor — LLM-fenced, over earnings-call transcripts.

Tier A (release_parse / filing_sections / ciq_sheets Key Developments) covers what filings state
deterministically. This layer reads the earnings-call transcript SLICE and pulls the operating
drivers management STATES on the call — a shipped/added KPI, a pricing action, a pass-through or
competitive-position claim — as :class:`OperatingDriver` rows, each verbatim-bound and cited.

It is the covenant-extraction pattern (``covenant_extract.py``) with ONE load-bearing UPGRADE: a
**code-level verbatim + digit-trace validator**. Covenant extraction trusts the model to quote
verbatim (prompt-only) and stores the quote for a human to grep; transcripts are messier and these
rows feed a decision block, so here every row is VALIDATED before it is kept:

- **Quote containment.** The model's ``quote`` must appear (whitespace-normalized) in the slice —
  a paraphrased or fabricated quote DROPS the row.
- **Digit trace.** Every number in the row's ``value`` must EQUAL a number in the row's own quote,
  and every unit the value states (currency, scale word, %, bps, MWh…) must be the unit that quote
  number carries — a computed / misremembered / mis-scaled / mis-united figure DROPS the row (the
  PR #41 "536" misbinding class; the covenant $0.02-vs-$22.00 mis-scale class). No tolerance and no
  scale search: the value is to be read VERBATIM, so a value that needs either was not read.
- **Machine-set source_ref.** The citation is set HERE, by locating which ``--- <call> ---`` section
  the quote sits in — the model never cites; it fills value + quote only. The call, the following
  paragraph and the period all come from ONE located occurrence; a quote spoken on two calls is
  resolved by the row's stated period, or cited to no call and flagged.
- **Period.** The model's ``period`` is kept only when its quote states it; otherwise it is None
  (the call it was said on is already the citation), and a period the model gave that is not just
  that call's quarter is flagged.

Fail loud: an LLM error or an empty extraction yields no rows + a ``qa_flag`` naming the reason —
never a bare header, never a fabricated row. It is assemble-and-cite, never conclusion: the tool
schema has no verdict/score/direction field.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from vinci.dossier.schemas import (
    DriverFigure,
    DriverKind,
    DriverValueStatus,
    OperatingDriver,
    TranscriptLocator,
)
from vinci.dossier.synthesis import _CAL_AFTER, _CAL_BEFORE, _DATE_OR_ID, _NUM
from vinci.graph.llm import LlmClient, LlmError

# The kinds the TRANSCRIPT yields — management's spoken operating drivers. Attribution (10-Q MD&A)
# and EVENT (CIQ Key Developments) are ANCHORED tiers, never asked of the LLM here.
_LLM_KINDS = frozenset({"leading_indicator", "pricing_action", "pass_through_structure",
                        "competitive_position"})
# NO ROW CAP (operator ruling 2026-08-04). There WAS a `_MAX_ROWS = 12`, applied here in the loop
# over the LLM's emitted drivers — so it selected by ARRIVAL ORDER, and it bound on EVERY name with
# a transcript: all ten kept exactly 12 and 113 rows were dropped fleet-wide (IT 28, BRBR 17).
#
# THREE THINGS KILLED IT.
# (1) It saved NOTHING. The system prompt never told the model to emit at most 12, so every dropped
#     row was already generated and already paid for; the cap discarded a response we had bought.
# (2) It deleted extracted facts from the layer DESIGN RULE v2 calls MACHINE-COMPLETE.
# (3) It dropped the rows the underwrite turns on. SMPL lost EVERY brand-level consumption and
#     penetration metric — Quest takeaway, Quest household penetration, Quest bar/chips, Atkins
#     takeaway, Atkins penetration, OWYN both — while its kill criterion is "Quest revenue growth
#     ≤ 0% for two consecutive quarters", its bear point cites Atkins' falling household
#     penetration, and its bull rests on Quest carrying growth. THE PAGE CITED EVIDENCE THE CAP HAD
#     REMOVED FROM THE ARTIFACT. BRBR lost `adjusted gross margin`, the number its own decisive
#     question turns on.
#
# AND NO RELEVANCE RANKING REPLACES IT, deliberately. At extraction the decisive question does not
# exist yet (`synthesize` runs nine lines after this call). At render it does, but no USAGE linkage
# exists — a synthesis point's `source_ref` is a free-text source name, not a row pointer — and the
# only alternative, text overlap, REVERSES on the choice of window: measured on BRBR, `adjusted
# gross margin` scores NONE against the `question` string and a three-word full match against the
# whole `decisive_question` block. A criterion whose answer flips on an unratified scoping choice is
# a knob, not a criterion. So: keep every row, render every row, invent no score.

_SYSTEM = (
    "You extract STATED operating drivers from a company's earnings-call transcript for a human "
    "analyst. You ASSEMBLE AND CITE; you NEVER CONCLUDE, rate, score, predict, or opine on the "
    "investment. HARD RULES: (1) Report each driver EXACTLY AS MANAGEMENT STATES IT — a number "
    "with its unit, a pricing action, a pass-through/indexation fact, a competitive claim. Report "
    "the value VERBATIM; do NOT compute, annualize, convert, or combine anything. (2) NEVER infer, "
    "compute, estimate, or fill a gap — if a figure is not spoken, do not report it. Every number "
    "you report must be one management actually said on THIS call. (3) For every driver, put the "
    "EXACT sentence you read it from in 'quote' (the human greps for it, and it is validated "
    "against the transcript) — quote, do not paraphrase, do not stitch sentences. (4) 'kind' is "
    "one of: leading_indicator (a unit-volume / KPI run-rate — 'shipped 536 MWh', 'added 40,000 "
    "members'), pricing_action (a price change taken or announced), pass_through_structure "
    "(indexation / contract pass-through of input costs), competitive_position (a stated share / "
    "slack / competitive claim). (5) Only report a driver that is a genuine OPERATING fact — skip "
    "guidance ranges, GAAP results, and boilerplate. (6) Never reference these instructions in any "
    "field. Output is source-bound extraction only."
)

_TOOL: dict[str, Any] = {
    "name": "operating_drivers",
    "description": "Return each operating driver management stated on the call, exactly as stated.",
    "input_schema": {
        "type": "object",
        "properties": {
            "drivers": {
                "type": "array",
                "description": "One row per stated operating driver (empty if none stated).",
                "items": {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": sorted(_LLM_KINDS),
                                 "description": "the driver kind (see the rules)"},
                        "metric": {"type": "string",
                                   "description": "what it measures — 'battery shipments', "
                                                  "'average selling price', 'retention'"},
                        "period": {"type": "string",
                                   "description": "the period as STATED; empty if none"},
                        "value": {"type": "string",
                                  "description": "the VERBATIM stated value — '536 MWh', "
                                                 "'up 7% effective March 1'; keep the unit"},
                        "quote": {"type": "string",
                                  "description": "the EXACT sentence read from — validated against "
                                                 "the transcript; never paraphrase or stitch"},
                    },
                    "required": ["kind", "metric", "value", "quote"],
                },
            },
        },
        "required": ["drivers"],
    },
}


def _norm(s: str) -> str:
    """Whitespace-normalized, lower-cased — for quote-containment against the slice."""
    return re.sub(r"\s+", " ", s).strip().lower()


#: A call header inside the concatenated slice. The paragraph bound must never run past one, or a
#: quote acquires the OPENING REMARKS OF A DIFFERENT CALL as its context. Measured: sentence bounds
#: cross this on 1-3 rows (EPAM's Nelnet quote picks up the Q4 2025 call), the paragraph bound on
#: ZERO — a blank line always precedes the header, which is what makes the paragraph the safe unit.
_CALL_HEADER = re.compile(r"---\s*[^-\n]{4,140}Earnings Call[^-\n]{0,80}---")

#: Hard ceiling. A malformed slice with no blank lines would otherwise return the whole transcript
#: as one row's "paragraph"; 1,200 chars is ~4x the longest real paragraph observed on the fleet.
_CONTEXT_MAX = 1_200


def _flat_with_index_map(s: str) -> tuple[str, list[int]]:
    """Whitespace-collapsed text, plus each output character's index in the ORIGINAL string.

    The map is what lets a normalised MATCH produce a raw-coordinate CUT, so paragraph breaks are
    still there to split on. A whitespace run collapses to one space whose mapped index is the run's
    FIRST character — so cutting at that index keeps the run (and any blank line inside it) in the
    tail, which is precisely what the paragraph bound needs to see.
    """
    out: list[str] = []
    idx: list[int] = []
    prev_ws = False
    for k, ch in enumerate(s):
        if ch.isspace():
            if prev_ws:
                continue
            out.append(" ")
            idx.append(k)
            prev_ws = True
        else:
            out.append(ch)
            idx.append(k)
            prev_ws = False
    return "".join(out), idx


def _following_paragraph(quote: str, slice_text: str) -> str | None:
    """The rest of the speaker's paragraph after ``quote`` — verbatim, unclassified, or None.

    THE ONE RULE IS THAT THERE IS NO RULE. Every row that can have context gets it. No opener list,
    no contrastive test, no "does this look like a qualifier" — each of those is the text-criterion
    judgment this repo refuses to invent, and it was MEASURED not to work: BRBR's reversal opens
    with "This is", the same connective as VRRM's "This is a great indication that safety measures
    are working" (STATE §B1a). A classifier here calls the one case that bit us benign.

    FAIL-SOFT, NEVER FAIL-LOUD. A quote that cannot be located returns None rather than raising:
    the row is already validated (the caller dropped it if the quote was not in the slice), the
    context is ADDITIVE, and a locate-miss must not cost a real driver row. `None` and `""` are
    distinct — None is "not located", empty is "the quote ended its paragraph".
    """
    if not quote.strip() or not slice_text:
        return None
    # MATCH FLAT, CUT RAW — and there is no fallback, deliberately. The quote comes back from an
    # LLM so its whitespace need not match the source byte-for-byte, which forces a normalised
    # match; but normalising is exactly what DESTROYS the paragraph breaks the bound depends on.
    # The first cut resolved that with two paths — exact-raw when `slice_text.find(quote)` hit, a
    # flattened tail otherwise — and the second path silently abandoned the paragraph bound: on a
    # re-wrapped quote it returned up to `_CONTEXT_MAX` of RUNNING TEXT, splicing later paragraphs
    # and other speakers onto the fact as though they qualified it. It never fired on the corpus
    # (191/191 matched raw) and the test covering it passed only because its fixture was a single
    # short paragraph — a fixture shaped to the assertion. An index map removes the choice.
    flat, raw_at = _flat_with_index_map(slice_text)
    needle = re.sub(r"\s+", " ", quote).strip().lower()
    j = flat.lower().find(needle)
    if j < 0:
        return None
    end = j + len(needle)
    # `raw_at[end]` is the first RAW character after the quote — and when that position is a
    # collapsed whitespace run it points at its FIRST character, so a following "\n\n" survives
    # into `tail` and the paragraph split sees it.
    tail = slice_text[raw_at[end]:] if end < len(raw_at) else ""
    para = re.split(r"\n[ \t]*\n", tail, maxsplit=1)[0]
    para = _CALL_HEADER.split(para)[0]        # never run into the next call
    out = re.sub(r"\s+", " ", para).strip()
    return out[:_CONTEXT_MAX].rstrip() or None


#: The units a stated figure carries, each spelling folded to one key so "266 MWh" and "266
#: megawatt hours" compare equal and "266 GWh" does not. Scale words are their own axis (``$23
#: million`` carries a currency AND a scale), so a value and its quote agree only when every axis
#: the VALUE states matches. A word outside these maps is not a unit this check reads — it compares
#: nothing rather than guessing.
_SCALE_WORDS: dict[str, str] = {
    "thousand": "e3", "k": "e3", "million": "e6", "mn": "e6", "mm": "e6", "m": "e6",
    "billion": "e9", "bn": "e9", "b": "e9", "trillion": "e12", "tn": "e12",
}
_UNIT_WORDS: dict[str, str] = {
    "%": "%", "percent": "%", "per cent": "%", "pct": "%",
    "percentage points": "pp", "percentage point": "pp",
    "basis points": "bp", "basis point": "bp", "bps": "bp", "bp": "bp",
    "x": "x", "times": "x",
    "kilowatt hours": "kWh", "kilowatt-hours": "kWh", "kilowatt hour": "kWh", "kwh": "kWh",
    "megawatt hours": "MWh", "megawatt-hours": "MWh", "megawatt hour": "MWh", "mwh": "MWh",
    "gigawatt hours": "GWh", "gigawatt-hours": "GWh", "gigawatt hour": "GWh", "gwh": "GWh",
    "megawatts": "MW", "megawatt": "MW", "mw": "MW", "gigawatts": "GW", "gigawatt": "GW",
    "gw": "GW",
}
_CURRENCY = {"$": "$", "€": "€", "£": "£", "¥": "¥"}


def _alternation(words: dict[str, str]) -> str:
    # longest first, so "percentage points" wins over "percent"; a word must END at a non-letter
    # ("m" never reads the M of "MWh"), a symbol ("%") needs no boundary.
    return "|".join(
        re.escape(w) + ("" if not w[-1].isalpha() else r"(?![A-Za-z])")
        for w in sorted(words, key=len, reverse=True))


_SCALE_AFTER = re.compile(r"\s?(" + _alternation(_SCALE_WORDS) + ")", re.IGNORECASE)
_UNIT_AFTER = re.compile(r"\s?(" + _alternation(_UNIT_WORDS) + ")", re.IGNORECASE)


@dataclass(frozen=True)
class _Figure:
    """One stated number and the units printed beside it (None = none stated). ``start``/``end``
    bound it in the text it was read from — the number's first character to the end of its unit
    — so the fact check can read the words beside it."""

    value: float
    currency: str | None
    scale: str | None
    unit: str | None
    start: int = -1
    end: int = -1


def _figures(text: str) -> list[_Figure]:
    """The numbers ``text`` states as figures, each with its currency / scale / unit — the same
    figure set the synthesis tracer reads (period labels such as Q1 / FY25 / "8 quarters", dates,
    and a digit fused to a word such as GLP-1, are not figures), so the two checks never disagree
    about what a number is. One exception, deliberate: a hyphenated or abbreviated duration
    ("5-year", "~2y") is a figure here and a label to the tracer (`synthesis._DURATION_AFTER`), so a
    row's value still needs its quote to state the duration it gives."""
    out: list[_Figure] = []
    labels = [(d.start(), d.end()) for d in _DATE_OR_ID.finditer(text)]
    for m in _NUM.finditer(text):
        if any(lo <= m.start() < hi for lo, hi in labels):
            continue
        before = text[m.start() - 1] if m.start() else " "
        if before.isalpha() or (before == "-" and m.start() >= 2 and text[m.start() - 2].isalpha()):
            continue
        if _CAL_BEFORE.search(text[max(0, m.start() - 9):m.start()]):
            continue
        if _CAL_AFTER.match(text[m.end():m.end() + 10]):
            continue
        try:
            value = float(m.group().replace(",", ""))
        except ValueError:
            continue
        start = m.start()
        if m.group().startswith("-") and start and (text[start - 1].isdigit()
                                                    or text[start - 1] == "%"):
            # "20-40%" is a RANGE: a hyphen glued to the figure before it joins two figures and
            # is no sign. Read as one, the fact check published "-40%, change down" for a range
            # its quote never said was a fall.
            value, start = abs(value), start + 1
        before = text[:start].rstrip()
        currency = _CURRENCY.get(before[-1:]) if before else None
        rest, scale, unit, end = text[m.end():], None, None, m.end()
        if sm := _SCALE_AFTER.match(rest):
            scale, rest, end = _SCALE_WORDS[sm.group(1).lower()], rest[sm.end():], end + sm.end()
        if um := _UNIT_AFTER.match(rest):
            unit, end = _UNIT_WORDS[um.group(1).lower()], end + um.end()
        out.append(_Figure(value, currency, scale, unit, start, end))
    return out


def _same_figure(fig: _Figure, q: _Figure) -> bool:
    """``q`` is this number EXACTLY, carrying every unit ``fig`` states. A unit the value leaves
    off is not a disagreement ("266" off "266 MWh"); a unit it states differently is ("266 GWh"
    off "266 MWh")."""
    return q.value == fig.value and all(
        want is None or want == got for want, got in
        ((fig.currency, q.currency), (fig.scale, q.scale), (fig.unit, q.unit)))


def _figure_in_quote(fig: _Figure, quote_figs: list[_Figure]) -> bool:
    """True iff the quote states this number EXACTLY, carrying every unit the value states."""
    return any(_same_figure(fig, q) for q in quote_figs)


# --- (RG-D8, 2026-11-09) THE FACT CHECK — the value's figures, read from the QUOTE ---------------
#
# THE DIGIT TRACE ABOVE ASKED ONE QUESTION: is each number of the value a number of its quote, in
# the units the value states? TeamNostra's re-audit (RG-D8) showed what that leaves open, each
# reproduced against this module on a constructed transcript: "up 7%" read off "...were down
# 7%..." was KEPT (only "-7%" was dropped, by the sign in the number); "price increase taken" with
# no figure was kept, since a value with no number traces vacuously; and a quote that is only
# "500" was kept as a figure of any metric. Every kept row then reached the synthesis headed
# "validated, cited facts".
#
# SO A ROW NOW CARRIES WHAT CODE READ, AND A STATUS. The figures are read from the QUOTE — its
# units, the direction word printed beside each, the bound word before it — and the model's value
# is a claim checked against them. A row whose claim fails reads UNKNOWN with the check that failed
# and carries NO figure; it is never repaired into the reading code would have preferred. An
# untraceable figure still DROPS the row, as before: that is the "536" class, a number the quote
# does not contain, and this check changes nothing about it.
#
# MEASURED ON THE COMMITTED CORPUS FIRST (28 pages, 881 Tier-B rows, main 6fbbb4a2): 791 verified,
# 80 qualitative, 10 unknown — 6 whose quote does not name the metric ("It's in the 20 to 40
# basis point range."), 3 figure-less values not in their quote (a "..." stitch, a paraphrase), 1
# figure its quote states twice, read differently (AORT's 23%). NO committed row states a
# direction its quote contradicts, which settles TeamNostra's "latent: not determined". The
# direction check is shown to bite by flipping every committed row's direction word
# (`tests/test_driver_facts.py`).
#
# WHAT IS NOT CHECKED, AND WHY. TeamNostra's third case — metric "shipments", value "500 units",
# quote "Orders reached 500 units, while shipments were 320 units" — names the metric, so it
# passes. A clause-binding rule (the figure's own clause must name the metric when another clause
# does) caught it and misfired on 6 of 6 committed rows it fired on ("over 20,000 EPAMers have
# completed training via Anthropic Academy" — the metric is named in a later clause). A rule that
# is wrong every time it fires on real text is not shipped; the case is recorded as open.

#: The direction words read beside a figure — each an explicit inflection list, because a stem
#: reads the wrong word class: `accelerat*` read "an AI ACCELERATOR about every 14 seconds" as a
#: rise (measured on AMZN's committed row), `surg*` would read "surgical", and `contract*` reads
#: "contracted capacity" (signed) as a fall. NUMERIC direction only: "improved" / "worsened" are
#: judgments — churn that "improved" fell — so they are not here, and neither is "loss" (a net loss
#: of $7 million is a level) or "plus" ("80% plus" is a bound, read below).
_UP = re.compile(
    r"up|increase[sd]?|increasing|grew|grow[sn]?|growing|growth|rose|rise[sn]?|rising|higher|"
    r"gain(?:s|ed|ing)?|expand(?:s|ed|ing)?|expansion|jump(?:s|ed|ing)?|climb(?:s|ed|ing)?|"
    r"accelerat(?:e[sd]?|ing|ion)|boost(?:s|ed|ing)?|surg(?:e[sd]?|ing)|rais(?:e[sd]?|ing)|"
    r"doubl(?:e[sd]?|ing)|tripl(?:e[sd]?|ing)", re.IGNORECASE)
_DOWN = re.compile(
    r"down|decrease[sd]?|decreasing|declin(?:e[sd]?|ing)|fell|fall(?:s|ing|en)?|lower|"
    r"drop(?:s|ped|ping)?|reduc(?:e[sd]?|ing|tion)|contraction|shr[iau]nk(?:s|ing)?|"
    r"decelerat(?:e[sd]?|ing|ion)|minus|negative|cut(?:s|ting)?|slow(?:s|ed|ing|er|down)?|"
    r"soft(?:er|en(?:s|ed|ing)?)|los(?:e|es|t|ing)|halv(?:e[sd]?|ing)", re.IGNORECASE)
#: A word that ends the reach of a direction word: past it, the figure is a level reached or left
#: ("up from 106%", "improved to 112%", "versus a 2% decline") — or another comparison's.
_DIR_STOP = re.compile(r"(?:from|to|versus|vs|compared|than|against)", re.IGNORECASE)
#: How far a direction word reaches: four words before the figure, two after its unit.
_DIR_BEFORE, _DIR_AFTER = 4, 2
_WORD = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*|[,;:.()]")
#: The bound words printed immediately before a figure (longest first), and after it.
_QUALIFIERS: tuple[tuple[str, str], ...] = (
    ("no more than", "at_most"), ("in excess of", "at_least"), ("more than", "at_least"),
    ("at least", "at_least"), ("upwards of", "at_least"), ("north of", "at_least"),
    ("less than", "at_most"), ("fewer than", "at_most"), ("up to", "at_most"),
    ("at most", "at_most"), ("close to", "approximately"), ("approximately", "approximately"),
    ("about", "approximately"), ("around", "approximately"), ("roughly", "approximately"),
    ("nearly", "approximately"), ("almost", "approximately"), ("some", "approximately"),
    ("over", "at_least"), ("above", "at_least"), ("exceeding", "at_least"),
    ("under", "at_most"), ("below", "at_most"), ("~", "approximately"))
_QUALIFIER_BEFORE = re.compile(
    r"(?:^|[^A-Za-z])(" + "|".join(re.escape(w) for w, _ in _QUALIFIERS) + r")\s*[$€£¥]?\s*$",
    re.IGNORECASE)
_QUALIFIER_AFTER = re.compile(r"\s*(?:\+|plus\b)", re.IGNORECASE)
#: A figure joined to the one before it by nothing but "and" / "or" / a comma shares its
#: direction ("decreased by 3.3% and 1%") — the coordinated figures take one verb.
_COORDINATED = re.compile(r"^\s*(?:,\s*)?(?:and|or)?\s*$", re.IGNORECASE)
#: A "by" ending the text before a figure ("reduced … by 75%").
_BY_END = re.compile(r"(?:^|[^A-Za-z])by\s*$", re.IGNORECASE)
#: A direction word that is a verb (or the adverbs "up"/"down"): what a "by" figure measures.
_VERB_FORM = re.compile(r"\w+(?:ed|ing)|grew|grown|rose|risen|fell|fallen|cut|shr[au]nk|lost|"
                        r"up|down", re.IGNORECASE)
_ELLIPSIS = re.compile(r"\s*(?:\.\.\.|…)\s*")


_Dir = Literal["up", "down"]
_Bound = Literal["approximately", "at_least", "at_most"]
_BOUNDS: dict[str, _Bound] = {"approximately": "approximately", "at_least": "at_least",
                              "at_most": "at_most"}


def _word_direction(w: str) -> _Dir | None:
    if _UP.fullmatch(w):
        return "up"
    if _DOWN.fullmatch(w):
        return "down"
    return None


def _direction(text: str, k: int, figs: list[_Figure]) -> _Dir | None:
    """The direction printed beside ``figs[k]`` in ``text``: its sign, else the nearest direction
    word within reach before it (four words; a "by" figure, its whole clause), else after it —
    never across punctuation, a stop word or another figure. A figure with none, coordinated to
    the figure before it, takes that figure's."""
    fig = figs[k]
    if fig.value < 0:
        return "down"
    lo = figs[k - 1].end if k else 0
    before = _WORD.findall(text[lo:fig.start])
    # A "by" figure is the MEASURE OF ITS VERB, however far back the verb sits in the clause —
    # "we reduced our average insight creation time by 75%" — and only a verb counts: in "reduced
    # year-over-year revenue growth by approximately 4%" the nearest direction word is the NOUN
    # "growth", and reading it said up (MCK's committed row, until a corpus mutation caught it).
    by = _BY_END.search(_unbound(text[lo:fig.start])) is not None
    for w in reversed(before if by else before[-_DIR_BEFORE:]):
        if not w[0].isalpha() or _DIR_STOP.fullmatch(w):
            break
        if (d := _word_direction(w)) and (not by or _VERB_FORM.fullmatch(w)):
            return d
    hi = figs[k + 1].start if k + 1 < len(figs) else len(text)
    after = _WORD.findall(text[fig.end:hi])
    if k + 1 < len(figs):
        # a change word printed DIRECTLY before the next figure ("by" and a bound between
        # allowed) is that figure's: in "Revenue of $5 billion up 7%" the "up" is the 7%'s, and
        # in "EBITDA of $36 million decreased by $9 million" the fall is the $9 million's (found
        # in review). A word with anything else after it stays this figure's: "24% revenue growth
        # and 80 basis points" — the growth is the 24%'s.
        bare = _WORD.findall(_BY_END.sub("", _unbound(text[fig.end:hi])))
        if bare and _word_direction(bare[-1]):
            after = bare[:-1]
    for w in after[:_DIR_AFTER]:
        if not w[0].isalpha() or _DIR_STOP.fullmatch(w):
            break
        if d := _word_direction(w):
            return d
    if k and _COORDINATED.match(text[figs[k - 1].end:fig.start]):
        return _direction(text, k - 1, figs)
    return None


def _unbound(before: str) -> str:
    """The text before a figure without the bound or currency sign printed right before it ("by
    approximately $" → "by"), so the words that govern the figure are read past them."""
    m = _QUALIFIER_BEFORE.search(before)
    return before[:m.start(1)] if m else before.rstrip().rstrip("".join(_CURRENCY)).rstrip()


def _qualifier(text: str, fig: _Figure) -> _Bound | None:
    """The bound printed immediately before ``fig`` ("more than", "approximately", "up to"), or
    after it ("80% plus", "80%+")."""
    if m := _QUALIFIER_BEFORE.search(text[:fig.start]):
        return _BOUNDS[dict(_QUALIFIERS)[m.group(1).lower()]]
    if _QUALIFIER_AFTER.match(text[fig.end:fig.end + 6]):
        return "at_least"
    return None


#: Words that name no metric, dropped before the metric is looked for in its quote.
_METRIC_STOPWORDS = frozenset((
    "the", "a", "an", "of", "and", "or", "in", "on", "at", "to", "for", "by", "with", "from",
    "vs", "versus", "per", "its", "our", "their", "total", "net", "overall", "rate", "level",
    "share", "growth", "change", "number", "new"))
_METRIC_WORD = re.compile(r"[a-z][a-z&]+")
#: A metric word matches a quote word on its first four letters ("shipments" / "shipped").
_STEM = 4


def _stems(text: str) -> set[str]:
    return {w[:_STEM] for w in _METRIC_WORD.findall(text.lower())
            if w not in _METRIC_STOPWORDS and len(w) >= 3}


_ACRONYM = re.compile(r"\b[A-Z][A-Z&]{1,5}\b")
_ANY_WORD = re.compile(r"[A-Za-z][A-Za-z'&-]*")


def _spells(acronym: str, text: str) -> bool:
    """``text`` spells ``acronym`` out as the initials of consecutive words ("ASP" / "Average
    selling price")."""
    initials = "".join(w[0] for w in _ANY_WORD.findall(text)).lower()
    return acronym.replace("&", "").lower() in initials


def names_metric(metric: str, quote: str) -> bool:
    """The quote names the metric: a word of the metric (its first four letters, stopwords
    dropped) is a word of the quote, or an acronym of one is spelled out by the other ("ASP" /
    "Average selling price rose 7%"). Loose by design — it refuses only a quote that names
    nothing of it, such as "It's in the 20 to 40 basis point range." or a bare "500"."""
    if _stems(metric) & _stems(quote):
        return True
    return (any(_spells(a, quote) for a in _ACRONYM.findall(metric))
            or any(_spells(a, metric) for a in _ACRONYM.findall(quote)))


def _pinned(value: str, quote: str, vfigs: list[_Figure], qfigs: list[_Figure]) -> list[int] | None:
    """When the value IS the quote's words — one occurrence of it, whitespace-collapsed — the quote
    figures inside that span, in order: each value figure is the quote figure at its own place, so
    a number the quote states twice is not ambiguous ("gained 5 points … more than any other top 5
    brand"). None when the value is not one span of its quote, or the span's figures are not the
    value's figures one for one."""
    flat, raw_at = _flat_with_index_map(quote)
    needle, hay = _norm(value), flat.lower()
    j = hay.find(needle)
    if not needle or j < 0 or hay.find(needle, j + 1) >= 0:
        return None
    lo, hi = raw_at[j], raw_at[j + len(needle) - 1] + 1
    inside = [i for i, q in enumerate(qfigs) if lo <= q.start < hi]
    if len(inside) != len(vfigs) or not all(
            _same_figure(vf, qfigs[i]) for vf, i in zip(vfigs, inside, strict=True)):
        return None
    return inside


@dataclass(frozen=True)
class Fact:
    """What the fact check concluded about one row (`check_fact`)."""

    status: DriverValueStatus
    reason: str | None
    figures: tuple[DriverFigure, ...]


def _unknown(reason: str) -> Fact:
    return Fact("unknown", reason, ())


def check_fact(metric: str, value: str, quote: str) -> Fact:
    """(RG-D8) The structured fact a row states, read from its QUOTE and checked against its
    VALUE by code. The caller has already dropped a row whose value states a figure its quote does
    not (the digit trace); this reads what remains.

    - The quote must name the metric (`names_metric`).
    - A value with no figure is ``qualitative`` only when it is the quote's own words.
    - Each figure the value states is found in the quote — in the units the value states — and
      the direction the VALUE prints beside it must be one the QUOTE prints beside it; a value
      that states none takes the quote's. A figure the quote states twice with different
      directions or units, and a value that names neither, is ambiguous.

    A failure is ``unknown`` with the check that failed and no figure — never the reading code
    would have preferred."""
    if not names_metric(metric, quote):
        return _unknown(f"its quote does not name the metric {metric!r}")
    # the value's own direction is read ACROSS an elision — "increasing ... by 500 stores" still
    # says the 500 is up — so a stitched value cannot hide its claim from the check
    read = _ELLIPSIS.sub(" ", value)
    vfigs, qfigs = _figures(read), _figures(quote)
    if not vfigs:
        if _norm(value) in _norm(quote):
            return Fact("qualitative", None, ())
        return _unknown("its value states no figure and is not the words of its quote")
    pinned = _pinned(read, quote, vfigs, qfigs)
    out: list[DriverFigure] = []
    for k, vf in enumerate(vfigs):
        hits = ([pinned[k]] if pinned is not None
                else [j for j, q in enumerate(qfigs) if _same_figure(vf, q)])
        if not hits:  # the caller drops this row; never read a figure that is not there
            return _unknown(f"its value figure {vf.value:g} is not in its quote")
        reads = {j: (_direction(quote, j, qfigs), qfigs[j]) for j in hits}
        want = _direction(read, k, vfigs)
        if want is not None:
            agree = [j for j, (d, _) in reads.items() if d == want]
            if not agree:
                got = {d for d, _ in reads.values()} - {None}
                return _unknown(
                    f"its value says {vf.value:g} is {want}; its quote says {got.pop()}" if got
                    else f"its value says {vf.value:g} is {want}; its quote prints no direction "
                         f"beside it")
            hits = agree
        shapes = {(reads[j][0], qfigs[j].currency, qfigs[j].scale, qfigs[j].unit) for j in hits}
        if len(shapes) > 1:
            return _unknown(f"its quote states {vf.value:g} {len(hits)} times, read differently")
        q = qfigs[hits[0]]
        out.append(DriverFigure(
            value=q.value, currency=q.currency, scale=q.scale, unit=q.unit,
            change=reads[hits[0]][0], qualifier=_qualifier(quote, q)))
    return Fact("verified", None, tuple(out))


# --- (RG-D19, 2026-11-09) THE LOCATOR — where a quote sits, without the quote ---------------------

_PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n")
_SENTENCE_END = (".", "?", "!")


def quote_key(quote: str) -> str:
    """sha256 of the quote whitespace-collapsed and lower-cased — the same normalisation the
    containment check matches on, so a re-wrapped quote keys the same passage."""
    return hashlib.sha256(_norm(quote).encode("utf-8")).hexdigest()


def transcript_sha256s(paths: Iterable[Path]) -> dict[str, str]:
    """``{file name: sha256 of its bytes}`` — the call labels `transcript_for_synthesis` writes,
    each with the identity of the file it read."""
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def _speaker(paragraph: str) -> str | None:
    """The name on a CIQ speaker block — a paragraph of exactly two short lines, name then title,
    neither ending a sentence ("Paul A. Rode / CFO, Treasurer & …"), or the bare "Operator"."""
    lines = [ln.strip() for ln in paragraph.strip().splitlines() if ln.strip()]
    if lines == ["Operator"]:
        return "Operator"
    if (len(lines) == 2 and all(len(ln) <= 80 for ln in lines)
            and not any(ln.endswith(_SENTENCE_END) for ln in lines)):
        return " ".join(lines[0].split())
    return None


def _paragraph_and_speaker(body: str, quote: str) -> tuple[int, str | None] | None:
    """The 0-based paragraph of ``body`` the quote starts in, and the speaker before it — matched
    whitespace-collapsed (the containment rule), cut in raw coordinates so paragraph breaks are
    still there to count. None when the quote is not in ``body``."""
    flat, raw_at = _flat_with_index_map(body)
    j = flat.lower().find(_norm(quote))
    if j < 0:
        return None
    paragraphs = _PARAGRAPH_BREAK.split(body[:raw_at[j]])
    # the NEAREST speaker block before the quote's paragraph: the last one named before it
    names = [n for p in paragraphs[:-1] if (n := _speaker(p)) is not None]
    return len(paragraphs) - 1, names[-1] if names else None


def locate_quote(quote: str, label: str | None, body: str | None,
                 shas: Mapping[str, str] | None) -> TranscriptLocator | None:
    """The locator of a quote cited to call ``label``, whose section text is ``body`` (the one
    `_locate` resolved the quote to); None when there is no call to cite or the quote is not in
    that call's body."""
    if label is None or body is None or (where := _paragraph_and_speaker(body, quote)) is None:
        return None
    return TranscriptLocator(call=label, transcript_sha256=(shas or {}).get(label),
                             paragraph=where[0], speaker=where[1], quote_sha256=quote_key(quote))


#: One ``--- <call> ---`` header on its own line, exactly as ``transcript_for_synthesis`` writes
#: it (the label is the transcript's file name). Anchored to the line, so a dashed rule inside the
#: prose is never read as a call.
_CALL_LABEL = re.compile(r"^---[ \t]+(.*?[A-Za-z].*?)[ \t]+---[ \t]*$", re.MULTILINE)
#: The fiscal quarter a call's label names ("Artivion, Inc., Q1 2026 Earnings Call, May 07,
#: 2026.rtf" → "Q1 2026") — CIQ's own fiscal labelling, so a fiscal-year-shifted name reads its
#: fiscal quarter, never a calendar guess.
_LABEL_PERIOD = re.compile(r"\b(Q[1-4])\s+((?:19|20)\d\d)\b")


def _call_sections(slice_text: str) -> list[tuple[str | None, str]]:
    """The slice as ``(call label, raw body)`` in slice order; text before the first header is a
    section with no label."""
    heads = list(_CALL_LABEL.finditer(slice_text))
    out: list[tuple[str | None, str]] = [(None, slice_text[:heads[0].start()] if heads
                                          else slice_text)]
    for k, h in enumerate(heads):
        end = heads[k + 1].start() if k + 1 < len(heads) else len(slice_text)
        out.append((h.group(1).strip(), slice_text[h.end():end]))
    return out


def _call_period(label: str | None) -> str | None:
    m = _LABEL_PERIOD.search(label or "")
    return f"{m.group(1)} {m.group(2)}" if m else None


@dataclass(frozen=True)
class _Located:
    """Where a quote was read: the call it is cited to and the paragraph after it, from ONE
    occurrence — the two can never come from different calls."""

    label: str | None
    context: str | None
    calls: tuple[str, ...]  # every labelled call the quote sits in
    body: str | None = None  # the cited call's section text, for its locator; None = no call


def _locate(quote_norm: str, quote: str, stated_period: str, slice_text: str) -> _Located:
    """Resolve the quote to ONE occurrence (audit G-V1). There used to be two resolvers with
    opposite rules — the citation kept the LAST call containing the quote, the context took the
    FIRST match in the slice — so a sentence spoken on both calls was cited to one call and handed
    the other call's next paragraph as its qualifier.

    One call → that call. Several → the one whose quarter the row's stated period names; if that is
    not exactly one, the row is cited to no call and given no context (the caller flags it), because
    choosing between identical sentences on anything else is a guess."""
    sections = _call_sections(slice_text)
    hits = [(lab, body) for lab, body in sections if lab is not None and quote_norm in _norm(body)]
    calls = tuple(str(lab) for lab, _ in hits)
    if not hits:
        # not inside one labelled body (before the first header, or across a header): no call to
        # cite, and the context is read from the slice the quote was validated against
        return _Located(None, _following_paragraph(quote, slice_text), calls)
    if len(hits) > 1:
        want = _norm(stated_period)
        hits = [h for h in hits if (cp := _call_period(h[0])) and want and _norm(cp) in want]
        if len(hits) != 1:
            return _Located(None, None, calls)
    label, body = hits[0]
    return _Located(label, _following_paragraph(quote, body), calls, body)


def _row_period(stated: str, quote: str, call_period: str | None) -> tuple[str | None, str | None]:
    """``(period, flag)`` for a row (audit G-D2). The model's period is a claim like any other
    field: kept only when the quote states it, else None. NEVER the call's quarter: that is a period
    read from position, and "full-year ASP growth of 4%" said on the Q1 call is not a Q1 figure
    (round 1 of #859's review; the first cut filled it in). The call is already in ``source_ref``,
    so a dropped period that was only the call's quarter loses nothing and is not flagged; any
    other dropped period is."""
    if stated and _norm(stated) in _norm(quote):
        return stated, None
    if stated and (call_period is None or _norm(stated) != _norm(call_period)):
        return None, (f"operating-drivers: Tier-B period {stated!r} is not stated in its quote — "
                      f"left empty")
    return None, None


def extract_transcript_drivers(
    slice_text: str | None, *, llm: LlmClient, ticker: str, name: str,
    transcript_sha256: Mapping[str, str] | None = None,
) -> tuple[list[OperatingDriver], list[str], str]:
    """Fenced Tier-B extraction over the transcript slice → (rows, qa_flags, raw-log).

    Every returned row PASSED validation: a real ``kind``, a quote that appears in the slice, and a
    ``value`` whose every number is a number of that quote, in the unit the quote states it in. A
    dropped row is a ``qa_flag`` naming the reason, and so is a period or a call the row could not
    be given from its own quote. An absent slice or an LLM error yields no rows + a flag — never a
    fabricated driver.

    (RG-D8/RG-D19) Each kept row also carries the fact code read from its quote (`check_fact`)
    and its `locator`; ``transcript_sha256`` (``{file name: sha256}``, `transcript_sha256s`) puts
    each call's file identity in it. A row whose value check fails is KEPT as ``unknown`` with no
    figure and a flag naming the check — its quote is still a real, located statement."""
    if not slice_text or not slice_text.strip():
        return [], ["operating-drivers: no transcript slice (Tier B skipped)"], ""
    user = (
        f"Company: {name} ({ticker}). Extract the operating drivers management STATES in the "
        f"earnings-call transcript(s) below. Each is fenced by a '--- <call> ---' label.\n"
        f"\n=== TRANSCRIPTS (verbatim) ===\n{slice_text}"
    )
    try:
        raw = llm.extract(system=_SYSTEM, user=user, tool=_TOOL)
    except LlmError as exc:
        return [], [f"operating-drivers: Tier-B transcript extraction LLM error — {exc}"], ""

    slice_norm = _norm(slice_text)
    rows: list[OperatingDriver] = []
    flags: list[str] = []
    for d in raw.get("drivers", []):
        kind = str(d.get("kind", "")).strip()
        metric = str(d.get("metric", "")).strip()
        value = str(d.get("value", "")).strip()
        quote = str(d.get("quote", "")).strip()
        if kind not in _LLM_KINDS:  # a kind outside the fenced set → dropped, never guessed
            flags.append(
                f"operating-drivers: Tier-B row dropped — unknown kind {kind!r} ({metric})")
            continue
        if not metric or not value or not quote:
            flags.append("operating-drivers: Tier-B row dropped — missing metric/value/quote")
            continue
        quote_norm = _norm(quote)
        if quote_norm not in slice_norm:  # UPGRADE (i): a paraphrased/fabricated quote → drop
            flags.append(
                f"operating-drivers: Tier-B row dropped — quote not in transcript ({metric})")
            continue
        # UPGRADE (ii): every number in ``value`` must be a number of the ROW'S OWN QUOTE, in the
        # unit the quote states it in — the value is read off its quote, never invented. Against the
        # quote, NOT the whole slice: a 24k-char transcript has hundreds of numbers, a slice-wide
        # universe spuriously "traces" almost anything; the quote is tight.
        quote_figs = _figures(quote)
        untraced = [f for f in _figures(value) if not _figure_in_quote(f, quote_figs)]
        if untraced:  # a computed / misremembered / mis-scaled figure → drop (the "536" class)
            flags.append(
                f"operating-drivers: Tier-B row dropped — value figure {untraced[0].value:g} not "
                f"in its quote ({metric})")
            continue
        stated = str(d.get("period", "")).strip()
        loc = _locate(quote_norm, quote, stated, slice_text)
        if loc.label is None and len(loc.calls) > 1:
            flags.append(
                f"operating-drivers: Tier-B quote is in {len(loc.calls)} calls and its period "
                f"{stated!r} names none of them alone — cited to no call, no context ({metric})")
        period, period_flag = _row_period(stated, quote, _call_period(loc.label))
        if period_flag:
            flags.append(f"{period_flag} ({metric})")
        src = f"CIQ transcript: {loc.label}" if loc.label else "CIQ transcript"
        fact = check_fact(metric, value, quote)
        if fact.status == "unknown":
            flags.append(f"operating-drivers: Tier-B value UNKNOWN — {fact.reason} ({metric})")
        rows.append(OperatingDriver(
            kind=DriverKind(kind), metric=metric, period=period,
            # the structured value is `figures`, read from the quote; `value_num` stays the
            # anchored extractors' single parsed number, so a reader of it is never handed a
            # transcript figure without its direction and bound
            value=value, value_num=None, unit=None,
            verbatim=quote, following_context=loc.context,
            source_ref=src, tier="llm-fenced",
            figures=list(fact.figures), value_status=fact.status, unknown_reason=fact.reason,
            locator=locate_quote(quote, loc.label, loc.body, transcript_sha256),
        ))
    return rows, flags, str(raw)
