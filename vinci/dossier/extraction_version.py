"""EXTRACTION VERSION — the declared identity of the extractor that produced a dossier.

THE DEFECT IT ANSWERS (queue item 26a, from the #238 blast-radius diagnosis). After #238 the fleet
held two vintages with nothing distinguishing them: pre-guard financial summaries lack the
unusual-items rows, post-guard summaries carry them. Cross-name comparison in the verdict-pending
cohort silently assumed a common table. **THE INVARIANT: a reader can tell whether two dossiers are
comparable.** Until that holds, no dossier can be re-assembled and no new name can be underwritten
— a new name needs a dossier built on the current extraction, and an unstamped one re-opens the
same ambiguity. This module is what lifts that freeze.

DECLARED, NOT DERIVED — and this was measured, not assumed. Two derived forms were specified and
both failed on real committed bundles:

  * A content hash of the EMITTED ROW-LABEL SET. **False negative:** FUBO hashes ``6d170d2fe3`` both
    pre-#238 and post, because it carries no unusual items and its output is byte-identical across
    the change — the reader concludes "same vintage" and is wrong, which is the exact divergence the
    stamp exists to prevent. **False positive:** post-#238, SMPL/AORT/FUBO hash differently FROM
    EACH OTHER despite being one vintage. It identifies SHAPE, not VINTAGE.
  * A hash of the extractor's CODE-SIDE SCHEMA (emitted field names + the hand-named row list). It
    behaves — ``57066b8cea`` → ``42c81f752d`` across #238, name-independent — but it still only
    catches SHAPE change. Item 20 is the counter-example: ``range_position`` and ``pe_ltm_current``
    now return ``NM`` where a stale figure stood, same labels and same fields. ``16.0x`` vs ``NM``
    matters to a reader more than an added row does, and no schema hash sees it.

Not a git SHA either: a SHA moves on unrelated commits and would mark the fleet perpetually
diverged.

WHY A CHANGELOG AND NOT A BARE CONSTANT (operator 2026-07-28): *"the initial constant should declare
WHICH STATE IT NAMES, not just be a number — a version string that doesn't say what it's anchored to
is the same class as every other identifier we've corrected this week."* So the version is not a
free-standing string: it is the last row of an append-only table whose other column says what
changed. Bumping the version without saying what it names is not expressible.

WHAT THIS DOES NOT DO. Nothing here notices that extraction behaviour changed — a version is
declared by hand, so an extractor change with no bump leaves the stamp lying. That is queue item
26b (the drift test: hash the declared extraction module set, fail when it moves while the version
does not). **26b's absence is not a regression** — an unbumped stamp is exactly today's state,
minus the ambiguity 26a removes.
"""

from __future__ import annotations

# APPEND-ONLY — with ONE recorded exception, 2026-08-17. The `2026-08-16.1` row was AMENDED, not
# appended to: its second clause claimed "the multiples stamps name their close (`Close [ISO]`)",
# and #460 REVERTED that (those source_refs are join keys quoted verbatim by sealed synthesis
# citations, so dating them broke 8 of them across 7 names). Amending is legitimate here and only
# here: append-only exists so a row an ARTIFACT REFERENCES is never rewritten under it, and NO
# artifact carries `2026-08-16.1` — verified 0 of 14 committed dossiers, all still `2026-07-28.1`.
# Appending a correction row instead would have declared a vintage that never produced anything and
# left the false clause standing in the table a reader greps. The first clause is untouched because
# it is TRUE: #459's selection-by-date and the NM refusals survived the revert.
# APPEND-ONLY. One row per extraction vintage: (version, what this version NAMES). The LAST row is
# current. A new row is written when extraction OUTPUT changes — not when the code is merely
# refactored — and writing one forces you to say what changed, which is the point of the pairing.
EXTRACTION_VERSIONS: tuple[tuple[str, str], ...] = (
    (
        "2026-07-28.1",
        "unusual-items surfacing in the financial summary (#238) · multiples read from the "
        "latest close, NM rather than a stale figure (#241)",
    ),
    (
        "2026-08-16.1",
        "every Multiples reader selects the latest close BY DATE, never by column position, and "
        "refuses on an NM or undated one rather than reaching back a quarter (#459)",
    ),
    # TWO ROWS AT ONCE, AND WHY (2026-10-08, the operator's analyst review). #673, #674, #676 and
    # #678 all changed extraction OUTPUT and none appended a row, so AMZN's 2026-10-08 page — built
    # on that code — carries `2026-08-16.1`, a stamp naming code that did not build it. The first
    # row names the vintage that DID build it, so the page's stamp can be corrected to a real row;
    # the second names this change. Refresh passes land layers on older pages without re-stamping
    # them: the stamp names the extractor that ASSEMBLED a page.
    (
        "2026-10-07.1",
        "forward consensus (FY+0..FY+2 paths, spreads, revision counts) and the forward-multiple "
        "history sit beside the page, outside the synthesis (#673, #676) · horizon_read takes "
        "each metric's revision counts from its OWN block — values change on every page (#674) · "
        "a claim citing a GAAP-EPS move normalized EPS did not make is caveated (#678)",
    ),
    (
        "2026-10-08.1",
        "the forward layers state their own basis: today's forward multiples beside their "
        "history (`current_multiples`), the history's latest close marked quarter-end or not, "
        "CIQ's FCF and EBITDA consensus set against CFO − CapEx and EBIT + D&A, and the Estimates "
        "export's file and hash",
    ),
    (
        "2026-10-08.2",
        "the final consensus's miss per completed fiscal year beside the page "
        "(`historical_forecast_error`): revenue as a percentage, profit lines and capex as "
        "dollars, per forecast revenue and as a margin or intensity error — a cross-check, never "
        "a revision distribution",
    ),
)

#: The version stamped on every dossier assembled by this code.
EXTRACTION_VERSION: str = EXTRACTION_VERSIONS[-1][0]

#: What that version names — the reader-facing description of this extraction vintage.
EXTRACTION_VERSION_NAMES: str = EXTRACTION_VERSIONS[-1][1]

#: Rendered where a stamped dossier would show its version, for dossiers assembled BEFORE 26a. An
#: absent stamp must be VISIBLE, never silent: "unstamped" and "I did not look" are different
#: states, and only one of them is honest about the vintage being unknown.
UNSTAMPED = "unstamped"


def _declared(version: str | None) -> str | None:
    """Normalise to ONE unstamped state. ``None``, ``""`` and whitespace-only all mean "no version
    was recorded" and must render identically — records are hand-edited, so a blank string is
    reachable, and treating it as a *version* produced two live defects in review: the two helpers
    below disagreed with EACH OTHER on ``""`` (header "unstamped", audit tier "built by a different
    extractor" — on one document), and the python and JS twins disagreed on it too. Normalising in
    one place is what keeps all four call sites saying the same thing."""
    return (version or "").strip() or None


def stamp_label(version: str | None) -> str:
    """The short stamp shown beside the assembly date. Legacy records (assembled before 26a) carry
    no version and say so, rather than rendering nothing and reading as "no divergence here"."""
    return _declared(version) or UNSTAMPED


def stamp_detail(version: str | None) -> str:
    """The long form for the audit tier: the version plus what it names. A version we do not
    recognise is reported as such — never silently described with the CURRENT version's changes,
    which would attribute this code's behaviour to an artifact built by other code."""
    v = _declared(version)
    if v is None:
        return f"{UNSTAMPED} — assembled before extraction versions were declared; vintage unknown"
    for ver, names in EXTRACTION_VERSIONS:
        if ver == v:
            return f"{v} — {names}"
    return f"{v} — not a version this code declares; built by a different extractor"
