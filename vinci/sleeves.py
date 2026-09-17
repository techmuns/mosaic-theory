"""THE SLEEVE REGISTRY — which STRATEGY a name is being judged under.

A **sleeve** is a tagged strategy book with its own playbook, verdict labels and attribution curve
(STATE.md §4 SLEEVE ARCHITECTURE; glossary in docs/engineering.md). Plain words: *what are we
claiming about this name, and what is the trap on the other side of that claim.*

WHY A REGISTRY AND NOT A FORK. The dossier pipeline was hard-bound to ONE strategy — overshoot — at
seven surfaces. That was correct while one edge existed; it stopped being correct the day a
followed megacap was committed (UBER), because the machine then asks a de-rating question about a
name that never de-rated. The fix is NOT a second assembler. Every edge this fund has recorded is
already defined WITH its evil twin, and the synthesis schema (bull points / bear points / evidence
balance, and NO verdict field) is ALREADY the universal shape of "case vs twin" — only the two case
DEFINITIONS were hardcoded. So a sleeve is a ROW, and sleeve N+1 touches no assembler, no schema,
no ledger mechanics.

A FROZENSET OF PLAIN STRINGS, NOT AN ENUM — the ``BEAR_BASES`` precedent (``vinci/scenarios.py``).
The value is persisted in committed artifacts (``dossier.json``, and from PR-1b the ledger row), so
it must round-trip as data without importing this module to be read; an unlisted value is refused
with the admissible set NAMED, because an unlisted provenance is not reviewable.

WHAT THIS MODULE DOES NOT DO. It holds no prompt text, no proposal mapping and no page copy yet —
those land in Phase 2 (queue item 34, SERIES A), where each row grows the fields that make the
FRAMING per-sleeve. v0 exists so the tag can be carried and validated end to end first: a tag with
nowhere to ride is untestable, and a framing swap with nothing carrying the tag has no input.
**It concludes nothing and reads no returns** — it is a vocabulary, not a decision.
"""

from __future__ import annotations

from dataclasses import dataclass

#: The two verdict labels the overshoot book has always used. Named here so a reader of the
#: registry sees which sleeve owns which vocabulary; the enum itself stays in `schemas.ledger`
#: (this module imports nothing from it — the registry must stay importable from anywhere).
_OVERSHOOT_VERDICTS = ("BUY", "AVOID_TERMINAL")

#: `PASS` and not a second AVOID: the underwrite record ALREADY carries this concept
#: (`VerdictStatus` literal "passed", and `Verdict.avoid_priced`), so the ledger label names what
#: the record could already say. Recording "terminal" on a fully-priced compounder would be a FALSE
#: RECORD in an append-only ledger. The enum member itself lands in Phase 2 (PR-2b).
_QUALITY_VERDICTS = ("BUY", "PASS")

#: The trade book's legs are quality's labels for the same reason quality's are not overshoot's: a
#: trade not taken says the catalyst is priced or too uncertain, never that the business is going
#: away, so recording AVOID_TERMINAL on it would be a false record. Named separately so a change to
#: one book's vocabulary cannot move the other's.
_TRADE_VERDICTS = ("BUY", "PASS")


@dataclass(frozen=True)
class Sleeve:
    """One strategy book. ``bet`` and ``twin`` are the pair the discriminator must tell apart."""

    key: str
    label: str
    #: What we claim the market has wrong. One line, in plain words.
    bet: str
    #: The look-alike that LOSES money — the thing the analysis must rule out. Every edge in this
    #: fund is defined with its twin; a sleeve without one is a mood, not a strategy.
    twin: str
    #: The question the dossier exists to answer for this sleeve. Phase 2 renders it as the page's
    #: lead section; here it is the human-readable statement of what the framing WILL become.
    question: str
    #: The verdict vocabulary this sleeve records. The FIRST is always the long leg; the SECOND is
    #: the leg it is measured against (the sleeve's spread is first − second).
    verdicts: tuple[str, str]
    #: How a name ENTERS this sleeve — recorded because the entry route is what makes the tag
    #: auditable rather than declarative.
    entry: str
    #: What would prove this sleeve carries no edge. Recorded per sleeve because a kill criterion
    #: that lives only in prose is not a falsifier (STATE.md §4).
    kill: str
    #: The FRAGMENTS the synthesis prompt varies by book. Everything else in that prompt — the
    #: cite-or-drop rule, the anti-balance rule, the no-conclusion contract, the peer-comp
    #: discipline — is INVARIANT and stays in one place: only the two CASE DEFINITIONS and the
    #: subject they are about were ever sleeve-specific, which is the whole reason a registry beats
    #: a second prompt. Overshoot's fragments are the LIVE TEXT verbatim, so `system_for` and
    #: `tool_for` reproduce today's prompt byte-for-byte (test-pinned) — the live book cannot drift
    #: as a side effect of making the others possible.
    #: What the name IS, as the prompt's opening subject ("a sharply de-rated US equity").
    subject: str
    #: The tool description's subject phrase ("the two readings of a sharply de-rated name").
    tool_subject: str
    #: The opening sentence of `bull_points.description` — the LONG case, defined.
    bull_case: str
    #: The opening sentence of `bear_points.description` — the TWIN, defined.
    bear_case: str
    #: How rule 3 names the pair the model must give honestly.
    both_cases: str
    #: The twin-reference-case outcome vocabulary ("recovered / went terminal.").
    twin_outcome: str
    #: THE PAGE COPY the reader actually meets. Separate from `question` (the human-readable
    #: statement of what the book asks, used in records and this registry's own documentation)
    #: because the rendered HEADING has to be the exact live string for overshoot — the committed
    #: fleet re-renders byte-identical only if these reproduce today's text character for character.
    #: The drawdown section's heading. It asks what MOVED the price and whether the name moved
    #: alone; the overshoot book words that as "what broke", which is wrong on a name that never
    #: broke — the whole defect this build exists to remove.
    drawdown_heading: str
    #: The two case headings, as rendered on the Analysis tier and in the Brief.
    bull_label: str
    bear_label: str
    #: The Brief's "what happened" section heading. Overshoot asks whether the name can SURVIVE —
    #: the right question after a break, and a strange one to ask of a compounder.
    survive_heading: str
    #: The label on the drawdown READ row, and the subtitle under the section heading. Both said
    #: "what broke" / "the event(s) that broke the name" beneath a heading that had already been
    #: made per-book — the heading moved and its own contents did not.
    read_label: str
    drawdown_subtitle: str
    #: The `log-verdict` help text the page offers for copy-paste. It named the overshoot twin and
    #: the overshoot thesis on every page, including books that record neither.
    twin_help: str
    thesis_help: str
    #: False until the sleeve may appear on a DECISION-LEDGER row. `theme` validates in its own
    #: append-only ratification ledger; `neglect` is defined but dormant. A defined-but-inactive
    #: sleeve is deliberately NOT the same thing as an unknown one.
    ledger_active: bool


#: THE FIVE. Ordered live-first; the ORDER carries no preference.
SLEEVE_ROWS: tuple[Sleeve, ...] = (
    Sleeve(
        key="overshoot",
        survive_heading="What happened — and can it survive?",
        read_label="Read — what broke",
        drawdown_subtitle="The event(s) that broke the name, then whether it fell alone "
                          "(idiosyncratic) "
                          "or with its graph cohort.",
        twin_help="how the terminal-decline twin is ruled out",
        thesis_help="the overshoot thesis (or AVOID rationale)",
        drawdown_heading="What broke — and did it fall alone?",
        bull_label="Bull case — the decline is overdone",
        bear_label="Bear case — the decline is real",
        label="Overshot de-rating",
        bet="an exaggerated, TEMPORARY de-rating — price broke further than the business did, "
            "and a reversal is nameable",
        twin="terminal decline — the sellers are right and the business really is going away",
        question="What broke — and did it fall alone? Temporary or terminal?",
        verdicts=_OVERSHOOT_VERDICTS,
        subject="a sharply de-rated US equity",
        tool_subject="the two readings of a sharply de-rated name",
        bull_case="The exaggerated/TEMPORARY overshoot case (mean-revert).",
        bear_case="The secular-and-TERMINAL decline case.",
        both_cases="the overshoot/mean-revert reading AND the terminal/value-trap reading",
        twin_outcome="recovered / went terminal.",
        entry="the screen ($300M–$10B) → rank → dossier",
        kill="the BUY−AVOID spread stays at or below zero — the discriminator carries no "
             "information (the standing fund-wide falsifier)",
        ledger_active=True,
    ),
    Sleeve(
        key="quality",
        survive_heading="What happened — and does it change the runway?",
        read_label="Read — what moved",
        drawdown_subtitle="The event(s) that moved the price, then whether it moved alone "
                          "(idiosyncratic) or with its graph cohort.",
        twin_help="how the fully-priced twin is ruled out",
        thesis_help="the runway thesis (or PASS rationale)",
        drawdown_heading="What moved the price — and did it move alone?",
        bull_label="Bull case — the runway outlasts the price",
        bear_label="Bear case — the price already pays for it",
        label="Durable compounder",
        bet="an expectations gap on DURATION — the reinvestment runway is longer or stronger "
            "than today's price assumes",
        twin="fully priced — the market already pays for the quality; a great company bought badly",
        question="What does today's price already assume — and is the runway longer than that?",
        verdicts=_QUALITY_VERDICTS,
        subject="a durable, high-return US business trading on long-duration expectations",
        tool_subject="the two readings of a durable compounder",
        bull_case="The RUNWAY case: the reinvestment opportunity is longer, larger or "
                  "higher-returning than the price assumes.",
        bear_case="The FULLY-PRICED case: the quality is real and already paid for — the "
                  "expectations embedded in the price are the thing that must be beaten.",
        both_cases="the longer-runway reading AND the already-priced reading",
        twin_outcome="kept compounding / re-rated to fair value.",
        entry="the follow list (operator judgement; reason AND sleeve both required)",
        kill="the sleeve's BUY−PASS curve fails to beat simply INDEXING the same followed names — "
             "the judgement adds nothing over passive exposure to a list we chose anyway",
        ledger_active=True,
    ),
    Sleeve(
        key="ultra_short_term",
        survive_heading="What happened — and is the catalyst still ahead?",
        read_label="Read — what moved",
        drawdown_subtitle="The event(s) that moved the price, then whether it moved alone "
                          "(idiosyncratic) or with its graph cohort.",
        twin_help="how the priced-or-spent twin is ruled out",
        thesis_help="the dated catalyst and the exit (or PASS rationale)",
        drawdown_heading="What moved the price — and did it move alone?",
        bull_label="Bull case — the catalyst is not yet in the price",
        bear_label="Bear case — already priced, or spent before the exit",
        label="Ultra-short-term trade",
        bet="a dated, nameable catalyst moves the price within weeks, and the market has its size "
            "or its timing wrong",
        twin="priced or spent — the catalyst is already in the price, or its move comes and goes "
             "before the exit",
        question="What is the dated catalyst — and is it already in the price?",
        verdicts=_TRADE_VERDICTS,
        subject="a US equity with a dated, near-term catalyst",
        tool_subject="the two readings of a near-term catalyst trade",
        bull_case="The CATALYST case: a dated, nameable event within weeks whose size or timing "
                  "the price does not yet reflect.",
        bear_case="The PRICED-OR-SPENT case: the event is already in the price, or its move fades "
                  "before the exit.",
        both_cases="the unpriced-catalyst reading AND the priced-or-spent reading",
        twin_outcome="moved on the catalyst / was already priced or faded before the exit.",
        entry="the follow list (operator judgement; reason AND sleeve both required)",
        # THE SAME COMPARATOR QUALITY USES (`vinci/scoring/baseline.py`), scored per verdict over
        # that verdict's OWN window — so a short `--horizon-days` is what makes this book short.
        # Nothing enforces the horizon yet; it is stated at log time, verdict by verdict.
        kill="the sleeve's BUY−PASS curve, each verdict scored at its own short horizon, fails to "
             "beat simply HOLDING the same followed names over the same windows — the catalyst "
             "call adds nothing over owning the list",
        ledger_active=True,
    ),
    Sleeve(
        key="theme",
        survive_heading="What happened — and does the driver still hold?",
        read_label="Read — what moved",
        drawdown_subtitle="The event(s) that moved the basket, then whether the members moved "
                          "together "
                          "or apart.",
        twin_help="how the momentum-bucket twin is ruled out",
        thesis_help="the driver thesis (or not-ratified rationale)",
        drawdown_heading="What moved the basket — and did the members move together?",
        bull_label="Bull case — the driver is real and unpriced",
        bear_label="Bear case — momentum wearing a story",
        label="Thematic driver",
        bet="a real, nameable shared driver the market prices late or partially across a basket, "
            "and selection within that basket beats holding all of it",
        twin="a momentum bucket in a costume — driver-less co-movement, or a narrative already "
             "fully priced",
        question="Is there a nameable driver — and does picking within the basket beat the basket?",
        verdicts=("RATIFIED", "NOT-RATIFIED"),
        subject="a basket of names exposed to one nameable driver",
        tool_subject="the two readings of a thematic basket",
        bull_case="The REAL-DRIVER case: a nameable shared driver the market prices late.",
        bear_case="The MOMENTUM-BUCKET case: co-movement with no driver, or one already priced.",
        both_cases="the real-driver reading AND the momentum-bucket reading",
        twin_outcome="the driver persisted / the theme was already priced.",
        entry="the theme lane (detection → gates → analyst driver-naming)",
        kill="the RATIFIED-vs-naive-momentum spread fails to beat the baseline — the assembly is "
             "re-describing momentum, which is replicable and is not this fund's edge",
        # Validates in its OWN append-only ratification ledger (`vinci/themes/forward.py`). A theme
        # name underwritten as a SINGLE NAME enters under `overshoot`/`quality` with the
        # `variant-vs-cross-section` edge basis — the sleeve says which book, the edge basis says
        # which claim.
        ledger_active=False,
    ),
    Sleeve(
        key="neglect",
        survive_heading="What happened — and is anyone looking yet?",
        read_label="Read — what moved",
        drawdown_subtitle="The event(s) that moved the price, then whether it moved alone "
                          "(idiosyncratic) or with its graph cohort.",
        twin_help="how the value-trap twin is ruled out",
        thesis_help="the neglect thesis (or AVOID rationale)",
        drawdown_heading="What moved the price — and did it move alone?",
        bull_label="Bull case — the neglect is mechanical",
        bear_label="Bear case — cheap for a reason",
        label="Orphaned quality",
        bet="a sound business starved of flow and attention, with a mechanism for the neglect "
            "to end",
        twin="the value trap / cigar butt — cheap forever, because nothing ever makes it stop "
             "being cheap",
        question="Is the neglect informed or mechanical — and what ends it?",
        verdicts=("BUY", "AVOID_TERMINAL"),
        subject="a sound but under-covered US business",
        tool_subject="the two readings of a neglected name",
        bull_case="The NEGLECT case: nobody is looking, and something will make them look.",
        bear_case="The VALUE-TRAP case: cheap forever, with no mechanism to end the neglect.",
        both_cases="the mechanical-neglect reading AND the value-trap reading",
        twin_outcome="was re-discovered / stayed a cigar butt.",
        entry="not yet built — Edge 1, gated by the §4 GOVERNOR",
        kill="not yet testable; activating this sleeve means filling this row and stating the "
             "falsifier before the first verdict, never after",
        ledger_active=False,
    ),
)

#: The admissible keys. Plain strings, validated against this set — never an Enum (see module doc).
SLEEVES: frozenset[str] = frozenset(s.key for s in SLEEVE_ROWS)

BY_KEY: dict[str, Sleeve] = {s.key: s for s in SLEEVE_ROWS}

#: What a name assembled through the SCREEN is judged under. The screen finds overshoot setups by
#: construction (`screens/screen2.py` — "the screen finds the SETUP, never the edge"), so this is a
#: statement about the existing route, not a fallback for an unstated choice: every OTHER route must
#: name its sleeve out loud.
DEFAULT_SLEEVE = "overshoot"


class UnknownSleeveError(ValueError):
    """The stated sleeve is not one this fund has defined."""


def require_sleeve(value: object, *, where: str) -> str:
    """Validate a stated sleeve, or REFUSE naming the admissible set.

    REFUSES SILENCE THE SAME WAY IT REFUSES A TYPO. ``None``/blank is not defaulted here — a
    caller that has a legitimate default (the screen route) applies :data:`DEFAULT_SLEEVE`
    explicitly, so the default is a decision at the call site rather than something this function
    hands out to anyone who forgot to ask. Everywhere else, an unstated sleeve means the operator
    has not said which book the name belongs to, and guessing is how a megacap silently inherits a
    de-rating question.

    ``where`` names the FILE OR FIELD at fault, because the fix is elsewhere: a refusal that says
    only "unknown sleeve" leaves the reader hunting for which entry to edit.
    """
    if not isinstance(value, str) or not value.strip():
        raise UnknownSleeveError(
            f"{where}: no sleeve stated ({value!r}) — say which strategy book this name is judged "
            f"under, one of {sorted(SLEEVES)}. An unstated sleeve is how a name silently inherits "
            f"the wrong question.")
    key = value.strip()
    if key not in SLEEVES:
        raise UnknownSleeveError(
            f"{where}: sleeve {key!r} is not one of {sorted(SLEEVES)} — an unlisted strategy is "
            f"not reviewable; add the member deliberately (vinci/sleeves.py) with its bet, its "
            f"twin and its kill criterion.")
    return key
