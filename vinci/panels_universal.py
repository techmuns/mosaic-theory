"""(phase 3) THE UNIVERSAL SEVEN — the panels every followed name runs, config only.

From the approved design (`docs/records/2026-08-27-between-print-monitor-panels.md`): *the call ·
kills · multiple & price · filing watch · dilution · attribution · sources*. Universal means the
CODE is shared and only configuration varies per name — a different sector still gets all seven.

WHAT THESE PANELS DO NOT DO. They measure an indicator; they never adjudicate a trigger. The
design is explicit that this distinction is the line: *"measuring an indicator is not adjudicating
a trigger, and this plan asks only for the first"*, and `vinci/monitor.py` refuses adjudication at
its own source. What the panels add is the NUMBER BESIDE THE CRITERION, so the human reads an
indicator instead of going to find it. Declaring a kill fired stays the human's call.

EVERY PANEL STATES WHAT WOULD CHANGE THE CALL, and `PanelSpec` now requires it as a non-blank
field. That is the design's own face-validity guard against its own accepted risk — *"fifteen
panels that each look important make none of them important"* — moved out of review and into the
type, because a guard enforced by reviewer attention passes on a tired day.
"""
from __future__ import annotations

from vinci.panels import PanelRegistry, PanelSpec, RenderOption, Requirement

THE_CALL = PanelSpec(
    key="the_call",
    tier="universal",
    title="The call",
    requires=(
        Requirement(
            kind="ledger_row",
            detail="verdict",
            why="the panel shows the verdict OF RECORD — the human's confirm/override, beside the "
            "machine's proposal; without the row there is no call to show",
        ),
    ),
    cadence="event",
    changes_the_call="Nothing — this IS the call. Every other tile is read against it.",
)

KILLS = PanelSpec(
    key="kills",
    tier="universal",
    title="Kill criteria",
    requires=(
        Requirement(
            kind="criterion",
            detail="measured_triggers",
            why="a criterion with no resolvable metric can only be re-printed, which is the gap "
            "this phase exists to close — the panel needs the measured form, not the prose",
        ),
    ),
    cadence="event",
    changes_the_call="A criterion crossing its threshold. The machine shows the reading; you "
    "declare the kill.",
)

MULTIPLE_AND_PRICE = PanelSpec(
    key="multiple_and_price",
    tier="universal",
    title="Multiple vs its own history",
    requires=(
        Requirement(
            kind="metric_path",
            detail="valuation.ev_ebitda",
            why="the current multiple is the left-hand side of the distance; without it there is "
            "no distance to draw",
        ),
        Requirement(
            kind="metric_path",
            detail="valuation.range_position",
            why="a multiple alone is not a position — 25.8x means nothing until it is placed in "
            "the name's own range, which is what makes compression visible",
        ),
    ),
    cadence="daily",
    # ARCHETYPE-NEUTRAL (row 26). The previous text read "for a quality megacap the multiple IS the
    # trade … the call breaking on THE ONLY AXIS THAT CAN BREAK IT" — GOOGL's condition verbatim,
    # generalised to every name and FALSE for a name whose call breaks on earnings arrival, where
    # the multiple has been paid nothing for. It said the distance MEANS something it only means for
    # one archetype. This states the distance and lets the name say which axis binds.
    changes_the_call="Where the case rests on the multiple, movement here IS the call moving. "
    "Where it rests on earnings, this line can travel a long way without the thesis changing.",
    render_config={
        "valuation_metric": RenderOption(
            means="which multiple THIS NAME'S case is underwritten on, named exactly as the "
            "dossier's own history labels it — 'P/LTM EPS' for a P/E-basis underwrite, "
            "'EV/EBITDA (TEV/LTM)' for an enterprise-basis one. Undeclared, the panel shows the "
            "repo default and SAYS so: 'the multiple the case rests on' and 'a multiple' are "
            "different claims.",
            allowed=("EV/EBITDA (TEV/LTM)", "P/LTM EPS")),
        "load_bearing_axis": RenderOption(
            means="which axis this name's underwrite actually rests on, read off its own record "
            "— 'multiple' when the case turns on the multiple re-rating or de-rating (GOOGL: bear "
            "EPS already exceeds today's NTM, so the entire downside is compression), 'earnings' "
            "when "
            "price has tracked earnings and the multiple contributes nothing",
            allowed=("multiple", "earnings")),
    },
    caveat="Trailing (LTM), not forward. No underwritten multiple is on file for this name, so "
    "the comparison shown is against its OWN history, not against a target.",
)

FILING_WATCH = PanelSpec(
    key="filing_watch",
    tier="universal",
    title="Printed since the underwrite",
    requires=(
        Requirement(
            kind="snapshot_field",
            detail="next_expected_print",
            why="the panel's job is the gap between what was read and what has since been filed; "
            "the expected date is what makes an absence meaningful rather than merely quiet",
        ),
    ),
    cadence="daily",
    changes_the_call="An unread print means the call is standing on older evidence than exists.",
    caveat="The next date is estimated from this filer's own cadence, not scheduled — late is not "
    "yet missed.",
)

DILUTION = PanelSpec(
    key="dilution",
    tier="universal",
    title="New securities registered for sale",
    requires=(
        Requirement(
            kind="metric_path",
            detail="dilution_pipeline.line",
            why="shelf and prospectus-supplement activity is the forward-looking half; a share "
            "count alone reports dilution that has already happened",
        ),
    ),
    cadence="weekly",
    changes_the_call="New SHARES sold shrink every per-share figure the case rests on, with no "
    "operating news at all. Bonds sold do not — and the count above includes both.",
    caveat="These filings MIX DEBT AND EQUITY and this panel does not separate them — a sample of "
    "eight of Alphabet's showed three bond offerings and four share registrations. It counts "
    "filings, not amounts: it cannot tell you whether your slice of the company got smaller.",
)

ATTRIBUTION = PanelSpec(
    key="attribution",
    tier="universal",
    title="Position vs its benchmark",
    requires=(
        Requirement(
            kind="snapshot_field",
            detail="excess",
            why="the decomposition is the point: a position up 30% in a market up 28% is not the "
            "same call as one up 30% in a flat market, and only the excess distinguishes them",
        ),
    ),
    cadence="daily",
    changes_the_call="Nothing — it says whether the call is being PAID. A position whose whole "
    "return is its benchmark's is a call that has not yet been right about anything.",
    caveat="Price returns both sides; dividends excluded. Do not read beside a total-return "
    "series.",
)

SOURCES = PanelSpec(
    key="sources",
    tier="universal",
    title="Sources",
    requires=(
        Requirement(
            kind="metric_path",
            detail="primary_source.filing",
            why="every other panel's figure is only as good as the filing behind it; this panel is "
            "where a reader checks rather than trusts",
        ),
    ),
    cadence="event",
    changes_the_call="Nothing — it makes the other tiles checkable rather than merely legible.",
)

#: Declaration order is RENDER order, and it is an argument rather than a list: the call first
#: because every other number is read against it; kills second because that is the panel a reader
#: opens the page for; then the two that move daily (multiple, filings); then the slower structural
#: ones; sources last because it is where a reader goes to check, not to look.
UNIVERSAL_SEVEN: tuple[PanelSpec, ...] = (
    THE_CALL, KILLS, MULTIPLE_AND_PRICE, FILING_WATCH, DILUTION, ATTRIBUTION, SOURCES,
)


def universal_registry() -> PanelRegistry:
    """The seven, in render order."""
    return PanelRegistry(UNIVERSAL_SEVEN)
