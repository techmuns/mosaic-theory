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
declared by hand. Queue item 26b does the noticing, as a TEST (2026-10-29, audit A-D14):
`tests/test_extraction_version_drift.py` hashes each declared extraction module and reds when one
moved while its pin did not — the PR that moves it says, in that file, whether output changed
(append a row here) or not. Without it the stamp stood still across 45 commits.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

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
    # #684 changed the anchor's net debt and appended no row — the omission the 2026-10-08.1 note
    # names — so this row names it beside its own change rather than leaving the stamp lying.
    (
        "2026-10-08.3",
        "the forward P/E states which consensus EPS line it is struck on "
        "(`forward_consensus.pe_eps_basis`): the FY rows and the NTM row each measured, never "
        "assumed · the anchor's net debt nets the short-term securities a CIQ TEV nets (#684)",
    ),
    (
        "2026-10-08.4",
        "CIQ's current TEV claims beside the page (`ev_bridge`): Net Debt + preferred + minority "
        "interest at the latest balance-sheet column, checked against CIQ's own TEV less market "
        "cap, the consensus net-debt line tested for basis over three years, and the exit "
        "default per the operator's rule",
    ),
    (
        "2026-10-09.1",
        "a page records each change made to it after assembly (`layer_refreshes`): the layers that "
        "moved, the extraction version that ran the writer, the date and the writer — printed "
        "beside the stamp, which still names the assembly",
    ),
    (
        "2026-10-09.2",
        "the non-operating read carries its count (`quality.nonoperating_quarters`: material "
        "quarters of the trailing four), and the build proposes R4 when the operator's three "
        "ratified conditions hold — shown beside a committed recipe, never written over one",
    ),
    (
        "2026-10-09.3",
        "the active recipe's basis beside the page (`valuation_basis`: bases, today's multiple "
        "and the snapshot it is struck at, bridge, exit claims, the basic share count, "
        "non-operating policy, conflicts — the template's share guard among them) and its dates "
        "named (`date_semantics`); the anchor's R1 fields carry their scenario eligibility; the "
        "forward history's latest close is `latest_observed_close`, never `current`; every writer "
        "saves through one write",
    ),
    (
        "2026-10-29.D-D1",
        "an unchecked quarter of the ex-lease history whose lease cell CIQ states as UNAVAILABLE "
        "is left unpriced (`lease_basis.observations`), never priced on the cells it does state "
        "with the missing one read as zero; the quarter names the cell (`unpriced_reason`) and "
        "the block its date (`unpriced_dates`) (audit D-D1)",
    ),
    (
        "2026-10-29.D-D5",
        "the materiality guard runs on both thresholds: a summary row and an unusual line at 5% "
        "of the revenue in the column each reads are material (`revenue` was never passed), and "
        "a missing annual Income Statement, revenue row or unusual-items block refuses the build "
        "instead of passing it (audit D-D5)",
    ),
    (
        "2026-10-29.G-V1",
        "a transcript row's call, following paragraph and period come from ONE located quote; "
        "its period stands only where the quote states it, else none; each value figure equals "
        "a figure of its quote in the quote's unit (audit G-V1, G-D1, G-D2) · a synthesis "
        "citation is a ref of the layer, never a fragment, and each figure traces to the numbers "
        "the fact it cites states, never its dates or ids; an exposure fact cites one filing and "
        "is always grounded (audit G-D5, G-D6)"
,
    ),
    (
        "2026-10-29.E2",
        "release and 10-Q figures read from what their own text states (audit E2): a footnote "
        "digit after a measure's name and a trailing-twelve-month lead-in (D5), a loss stated in "
        "words (D10), 'Revenues of' with the closing company profile refused (D11), a one-off "
        "whose amount the charge noun names (D12), the ≤12m wall's stated zero and its "
        "principal-and-interest basis (D15, `maturity_wall.basis`), a concentration column's "
        "role from its header, a refused row named (D16); a non-positive LTM EBITDA has no "
        "leverage multiple (E1-D13)"
    ),
    # THE STAMP STOOD STILL FOR 45 COMMITS (audit A-D14). Every commit to vinci/dossier, vinci/edgar
    # and vinci/ciq merged after 2026-10-09.3 (#706 … #855, 2026-10-11 → 10-29) appended no row,
    # and at least six changed output (#819, #826, #827, #831, #834, #836), so the 155 layer
    # refreshes dated 10-27 or later stamped 2026-10-09.3. The first row below names them, the
    # 2026-10-08.3 precedent; the rest are the CIQ reader's fixes (B4), one row per output change,
    # ids `<date>.<audit id>` (the Phase 1 convention, 2026-10-29). MERGING: each row is its own
    # `(` … `),` block — a line-wise union of two branches' table ends fuses two rows into one
    # element; keep every block whole, in merge order.
    (
        "2026-10-29.A-D14",
        "the dossier-output changes merged after 2026-10-09.3 that appended no row: 45 "
        "commits to vinci/dossier, vinci/edgar and vinci/ciq (#706 … #855, 2026-10-11 → "
        "10-29), among them #819, #826, #827, #831, #834 and #836 — from here a watched "
        "extraction module that moves with no row appended reds "
        "tests/test_extraction_version_drift.py",
    ),
    (
        "2026-10-29.A-D3",
        "one parser reads every Financials period header: an 'FQ4/CQ2' quarter is a quarter, "
        "with its year-on-year growth, and a quarter carries its fiscal year (A-X2); a "
        "same-quarter YoY reads only the prior fiscal year's quarter, never one two to four "
        "years back",
    ),
    (
        "2026-10-29.A-D6",
        "a bridged anchor input names the CIQ export it was read from — D&A, OCF and capex "
        "the annual workbook, the balance sheet the quarterly one — never the quarterly file "
        "for all",
    ),
    (
        "2026-10-29.A-D8",
        "every guided metric the Guidance sheet lays out is read, found by the structure of "
        "the sheet rather than a fixed list; a metric with no decided delivery direction "
        "shows its guide with no MET/MISSED record",
    ),
    (
        "2026-10-29.A-D10",
        "the recommendation and the rating counts come from the block of the listing itself "
        "in Trends, never from the industry or another listing",
    ),
    (
        "2026-10-29.A-X1",
        "a Financials export whose filename and statements state different period types is "
        "refused, and a lone export never answers for the other period type (A-D11), so an "
        "annual balance-sheet date prints as a date, never a raw serial",
    ),
    (
        "2026-10-29.BC-D10",
        "the anchor's CIQ bridge reads each statement's own unit line and refuses a sheet stated "
        "in another unit, or two exports in different units — the magnitude screen against revenue "
        "could not see either (audit BC-D10); every export on file states Millions, so no value "
        "moves",
    ),
    (
        "2026-10-29.G-D3",
        "each earnings call reaches the driver extraction and the synthesis WHOLE — prepared "
        "remarks and the full Q&A — where it was cut at 12,000 characters unmarked; a call past "
        "the 100,000-character ceiling ends in a marker and a QA flag, and a call on file that "
        "does not read is named in a QA flag (audit G-D3, G-D4)"
    ),
    (
        "2026-10-29.D-D5-prompt",
        "the synthesis is asked for every material figure the citation guard demands: the rows "
        "are marked material before the model is asked, and a section lists each figure, its "
        "period and the table's source_ref from the guard's own selection; a page with no "
        "material row is sent the prompt it was sent before (audit D-D5 follow-up)",
    ),
    (
        "2026-10-30.press-release-ltm",
        "a CIQ Income Statement whose latest LTM, fiscal-year or quarter column is a 'Press "
        "Release' column is refused at assembly and by the anchor's CIQ bridge, the header's "
        "status (filed, reclassified, "
        "restated, press release) being a parsed field; each additive annual-summary row's LTM is "
        "checked against the four quarters ending on its date, a disagreement or a '-' quarter "
        "is a QA flag, and a material row its quarters contradict refuses the build",
    ),
    (
        "2026-10-30.E2-guidance",
        "a guidance range is read as its sentence states it (audit E2-D1, D2, D7, D8, D13): a "
        "dollar range stated in thousands or with no scale is refused aloud, never stored as $M; "
        "a revenue guide qualified by a sub-line word (subscription, a region) is refused by the "
        "actuals' allowlist; a range stated as the prior outlook beside a new one never takes "
        "the metric's slot; a gross margin stated in dollars is refused; a second range joined by "
        "'and' is read when it states its own period and refused aloud when it does not",
    ),
    (
        "2026-10-30.G-D7",
        "an LLM's quote is a span of its document only with every gap between two digits kept: "
        "a quote reading 'Level 11.25%' is refused where the exhibit prints 'Level 1 1.25%', "
        "where whitespace removal had joined the two figures into one (audit G-D7); every "
        "committed quote reads as before",
    ),
    (
        "2026-10-30.cover-dated-shares",
        "a share count tagged after its own filing is dated from its cover sentence (an anchored "
        "parse; unread, at its filing day, printed 'filed <date>'), its value cross-checked "
        "against another count in the same filing and UNKNOWN past that comparison's tolerance "
        "(5% to a balance-sheet count, 10% to a diluted average or a previous count), each "
        "correction a QA flag "
        "(audit X1(a)); the covenant-pointer table names the aggregate lines and agreement "
        "families its caps leave out, and a full-text search reads every page or says it did not "
        "(audit E1-D11)",
    ),
    (
        "2026-10-30.edgar-provenance",
        "every EDGAR fallback figure says where it was filed — its tag, period, form, "
        "accession and day — and one a later filing restated names the figure it restates; a "
        "capex or D&A leg filed negative, or a D&A under the accretion-net tag, is refused, "
        "naming it, never sign-flipped (audit E1-D5, E1-D12); the screen's share change, the "
        "rank's dilution demote and the theme desk's basis check read a share count tagged "
        "after its own filing at its filing day, cross-checked (audit X1(a))",
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


def _field(entry: Any, key: str) -> Any:
    """A layer-refresh entry's field, from the model (render) or a dict (the JSON twin's shape)."""
    return entry.get(key) if isinstance(entry, dict) else getattr(entry, key, None)


def refreshed_to(entries: Sequence[Any] | None) -> str | None:
    """The extraction version of the LAST change recorded on a page after its assembly, or None.

    Printed BESIDE the stamp, never in place of it: the stamp names what assembled the page, this
    names the newest code that changed part of it. Neither alone says what the page is."""
    return stamp_label(_field(entries[-1], "extraction_version")) if entries else None


def refresh_line(entry: Any) -> str:
    """One recorded change, for the audit tier: when, what moved, which writer, at which version."""
    layers = ", ".join(_field(entry, "layers") or [])
    return (f"{_field(entry, 'date')} · {layers} — {_field(entry, 'writer')} at "
            f"{stamp_label(_field(entry, 'extraction_version'))}")


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
