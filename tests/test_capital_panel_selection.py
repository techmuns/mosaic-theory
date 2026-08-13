"""The DETAILS panel is the one whose stamp describes it; the SUMMARY is chosen separately.

WHAT #450 GOT WRONG, AND WHY IT MATTERED. That change read the Capital-Structure Details panel from
whichever workbook carried the later-filed `Source` note, and reported 16 names getting ~150 days
fresher. **They did not get fresher. CIQ exports no quarterly capital-structure detail.** Both
workbooks carry the identical per-fiscal-year sections — verified field-by-field across all 19
bundles: same instruments, same principals, same maturities, same coupons — and only the
workbook-level note differs. The "fresher panel" was the same data wearing a newer date.

Measured, note-period vs section-period: **annual 19/19 consistent, quarterly 18/19 MISMATCHED**
(FUBO the lone agreement, its annual export already holding an `FQ3 2026` section because the
post-combination entity has no FY yet). V is the clearest shape — a `Q3 2026 filed Jul-29-2026`
note sitting over an `FY 2025 (Sep-30-2025)` section, ten months of false freshness.

THE HARM WAS NOT COSMETIC, which is the part a "same numbers, newer date" change hides.
`_capital_structure_vintage` derives the schedule's AGE from this stamp and bounds its Item-1.02
termination search by it (`panel_filed < event <= reference_date`). Under the quarterly stamp:

    NFLX age 201d -> 26d, and the 2026-02-27 Item 1.02 fell OUT of the window,
    silently dropping the warning that the listed WBD bridge facility was terminated

— the exact disclosure STATE item 7 designates as the remedy for that finding. A newer date on
older data does not merely overstate freshness: it retires the checks that depend on knowing how
old the data is. That is why the regression pin here is the TERMINATION WINDOW, not the stamp.

THE RULE IS PROVENANCE, NOT RECENCY, and it is not a hardcoded `freq="annual"` in disguise: if CIQ
ever ships a true quarterly panel its note and section will agree and it is selected automatically.
Annual winning today is the consequence of the rule, not the rule.

WHAT SURVIVES FROM #450: the Summary half. Its aggregates come from dated period COLUMNS, not from
the panel note, and its latest column is the same date in both workbooks on all 19 names — so
preferring quarterly there cannot stale any figure (verified: no headline aggregate moves). What it
fixes is the term-loan STEP, whose two endpoints in the annual sheet are a 12-month column beside a
3-month one on 16 of 19 names — SMPL printed
`term loans 397.0 (12 months Aug-30-2025 249.1 → 3 months May-30-2026 397.0)`, stepping a
TWELVE-month endpoint to a THREE-month one. Details and Summary are therefore chosen by SEPARATE
rules, which is what this module's own contract said all along: *the itemized detail is
panel-dated, the aggregates are stamped with the period column they were actually read from.*
"""
from __future__ import annotations

import re
from datetime import date

import pytest

from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
from vinci.dossier.manual_store import LocalFolderStore

_WINDOW = re.compile(r"(\d+)\s+months", re.I)


def _root():
    r = get_config().data_dir / "manual" / "ciq"
    if not r.is_dir() or not any(r.iterdir()):
        pytest.skip("licensed CIQ bundles unavailable (never committed)")
    return r


def _bundles() -> list[tuple[str, CiqBundle]]:
    root = _root()
    ms = LocalFolderStore(root)
    out = []
    for tk in sorted(p.name for p in root.iterdir() if p.is_dir()):
        files = ms.files(tk)
        if files:
            out.append((tk, CiqBundle.from_files(tk, files)))
    return out


def _filed(bundle: CiqBundle, freq: str) -> date | None:
    """The panel's own filed date at `freq`, or None when that workbook is genuinely absent.

    Mirrors the production guard: `workbook(freq=…)` answers an unsatisfiable request with
    `cands[0]`, so the resolved workbook's OWN `.freq` decides whether it counts.
    """
    wb = bundle.workbook("financials", freq=freq)
    if wb is None or wb.freq != freq:
        return None
    try:
        rows = bundle.sheet("financials", "Capital Structure Details", freq=freq)
    except CiqUnavailableError:
        return None
    return cs._cs_panel_filed(cs._cs_detail_asof(rows))


# ─── the rule ───────────────────────────────────────────────────────────────────────────────────
def test_the_selected_details_panel_is_stamped_with_its_own_provenance() -> None:
    """THE WHOLE RULE, on every committed bundle: the panel actually read must carry a `Source`
    note naming the same period as the instrument section beneath it.

    Stated as a property of the SELECTION rather than a table of expected frequencies, so it stays
    true through a re-pull — and so it keeps meaning the right thing if CIQ ever does ship a
    genuine quarterly panel."""
    for tk, b in _bundles():
        chosen = cs._cs_details_freq(b)
        rows = cs._cs_details_rows(b, chosen)
        assert rows is not None, f"{tk}: selected {chosen!r} but that panel does not read"
        assert cs._cs_note_describes_section(rows), (
            f"{tk}: the selected {chosen} panel's note {cs._cs_detail_asof(rows)!r} does not "
            f"describe the section it stamps — this is the #450 mis-stamp, and every age and "
            f"termination window derived from it would be wrong")


def test_a_later_filed_quarterly_note_does_not_win_because_recency_is_not_provenance() -> None:
    """THE NEGATIVE PIN — the rejected design, which is what #450 actually shipped.

    On most names the quarterly workbook's note is MONTHS newer than the annual one, so a
    recency rule picks it. It must lose anyway: its note describes a quarterly FILING while the
    section beneath it is still the fiscal-year panel. Asserted as "such names exist, and every one
    of them keeps annual", so a re-pull that reshuffles the population cannot quietly empty the
    case — an assertion with nothing left to test has stopped testing."""
    tempting = []
    for tk, b in _bundles():
        a, q = _filed(b, "annual"), _filed(b, "quarterly")
        if a is None or q is None or q <= a:
            continue
        if cs._cs_note_describes_section(cs._cs_details_rows(b, "quarterly")):
            continue  # a genuine quarterly panel would be a legitimate win, not this shape
        tempting.append((tk, a, q))
        assert cs._cs_details_freq(b) == "annual", (
            f"{tk}: took the quarterly panel because its note is newer ({q} > {a}), but that note "
            f"stamps a filing the section below it does not come from")
    assert tempting, (
        "no committed name still has a later-filed-but-mis-stamped quarterly note, so the rejected "
        "design is untested here — re-measure the corpus before trusting this rule's negative half")


def test_the_selected_stamp_keeps_a_real_termination_inside_its_window() -> None:
    """THE HARM, pinned END TO END rather than at the stamp — because #450 changed only a date and
    a stamp-level test would have called that harmless.

    `_capital_structure_vintage` searches for an Item 1.02 in `panel_filed < event <= as-of`. The
    committed NFLX record carries the real instance: the WBD bridge facility is still listed in the
    panel and its termination was filed **2026-02-27**. Under the quarterly stamp the window opened
    at Jul-17-2026 and the event fell outside it — the warning vanished while the dead facility
    stayed on the page.

    Pinned on the ARITHMETIC of the window against the selected stamp, so it needs no network and
    no committed artifact, and reddens for the right reason: a stamp that post-dates a known
    termination cannot report it."""
    b = dict(_bundles()).get("NFLX")
    if b is None:
        pytest.skip("NFLX bundle unavailable (licensed workbooks are never committed)")
    _, _, as_of = cs.capital_structure_ciq(b)
    filed = cs._cs_panel_filed(as_of)
    assert filed is not None, f"the selected panel states no filing date ({as_of!r})"

    wbd_termination, reference = date(2026, 2, 27), date(2026, 8, 12)
    assert filed < wbd_termination <= reference, (
        f"the selected panel is stamped {filed} — at or after the 2026-02-27 Item 1.02 — so "
        f"_capital_structure_vintage cannot report it, and the page lists a terminated facility "
        f"with nothing saying so. Stamp was {as_of!r}")


# ─── the trap this had to be written around ─────────────────────────────────────────────────────
def test_a_missing_quarterly_workbook_cannot_pose_as_a_fresh_one() -> None:
    """THE SILENT FALLBACK, pinned as a REAL bundle rather than a mock of one.

    `CiqBundle.workbook` answers a `freq=` it cannot satisfy with `cands[0]` instead of None, so
    asking a one-workbook bundle for "quarterly" hands back the ANNUAL file. A picker that trusted
    the request would compare that panel against itself, find the dates equal, and be deciding on a
    comparison it never actually made.

    THE ONE-SIDED CASE HAS TO BE THE **QUARTERLY**-ONLY ONE, which is the whole reason this test
    reads the way it does. An ANNUAL-only bundle cannot detect the bug: the fallback hands back the
    annual panel under both requests, the two dates tie, and a guarded and an unguarded picker
    agree on "annual" by coincidence. The first cut of this test was written that way and stayed
    GREEN when the guard was deleted — it asserted through a local re-implementation of the guard
    rather than through the production one, so it was testing itself.

    Quarterly-only separates them: WITH the guard the annual request is rejected and the picker
    answers "quarterly"; WITHOUT it the annual request returns the quarterly panel, that panel is
    self-consistent (it is the only one there), and the selector answers "annual" — naming a
    frequency this bundle has no workbook for. Built from the REAL type by handing `from_files`
    only the quarterly path."""
    root = _root()
    ms = LocalFolderStore(root)
    quarterly_only = None
    for tk in sorted(p.name for p in root.iterdir() if p.is_dir()):
        paths = [p for p in ms.files(tk) if "_quarterly" in p.name.lower()]
        if paths:
            quarterly_only = CiqBundle.from_files(tk, paths)
            break
    if quarterly_only is None:
        pytest.skip("no quarterly financials workbook on disk to build the one-sided bundle from")

    # THE TRAP IS REAL — pinned so it cannot change underneath the picker unnoticed.
    wb = quarterly_only.workbook("financials", freq="annual")
    assert wb is not None and wb.freq == "quarterly", (
        "workbook() stopped falling back — if it now returns None the guard can be simplified, "
        "but the picker must be re-read before that is assumed")

    # …and the PRODUCTION selector is not fooled by it. This is the assertion the guard owns.
    assert cs._cs_details_freq(quarterly_only) == "quarterly", (
        "the fallback workbook was admitted as an ANNUAL panel, so the selector named a frequency "
        "this bundle has no workbook for")


def test_the_panel_stamp_has_exactly_one_parser_and_it_anchors_on_filed() -> None:
    """ONE STRING, ONE PARSER — the rule that decided where this code lives.

    The picker needed the panel stamp's date, and `ciq_sheets` already had `_cs_col_date` sitting
    right there. Using it would have been wrong: it searches for a BARE `Mon-DD-YYYY`, so a note
    carrying its period alongside its filing —

        A 2025 (Dec-31-2025) filed Jan-23-2026

    — reads as **Dec-31-2025**, the period end, while `_cs_panel_filed` anchors on "filed" and
    reads **Jan-23-2026**. The picker would then have ranked panels by period end while the
    staleness banner reported filing date: two answers for one string, on the same page.

    So the stamp parser moved down into `ciq_sheets` (the layer that produces the stamp) and
    `mechanical` re-exports it. This pins the distinction rather than the file layout — if someone
    re-points the selector at the column parser, the divergent case below reddens."""
    from vinci.dossier.mechanical import _cs_panel_filed as via_mechanical

    assert cs._cs_panel_filed is via_mechanical, (
        "the panel stamp has two parsers again — mechanical must re-export the one in ciq_sheets, "
        "not define its own")

    divergent = "A 2025 (Dec-31-2025) filed Jan-23-2026"
    assert cs._cs_panel_filed(divergent) == date(2026, 1, 23), "the FILING date is the age key"
    assert cs._cs_col_date(divergent) == (2025, 12, 31), (
        "the column parser stopped reading the bare date — if that is deliberate, this test's "
        "premise needs re-reading, because the two helpers no longer differ")

    # the ordinary shapes, where the two happen to agree — which is exactly why the trap is easy
    # to walk into and worth a pin
    for stamp, want in (("A 2025 filed Jan-23-2026", date(2026, 1, 23)),
                        ("Q2 2026 filed Jul-17-2026", date(2026, 7, 17))):
        assert cs._cs_panel_filed(stamp) == want
    assert cs._cs_panel_filed("") is None and cs._cs_panel_filed("A 2025") is None


# ─── the SPLIT, which is what #450 got backwards ────────────────────────────────────────────────
def test_the_two_sheets_are_read_at_their_own_correct_frequencies() -> None:
    """THE INVERSION OF #450's COUPLING, which was the wrong idea rather than an incomplete one.

    #450 argued the Details and Summary "must sit on one filing" and forced both onto the picker.
    They must not. The two are different objects with different provenance, and this module's own
    contract already said so: the itemized DETAIL is panel-dated, while the AGGREGATES are stamped
    with the period column they were read from. Fusing them dragged the Details panel onto a
    quarterly stamp that did not describe it, in service of a consistency the data never required.

    So the pin is the SPLIT: Details from the self-consistent panel (annual today), Summary from
    the sheet whose columns give a like-for-like step (quarterly). Recorded at the CALL SITE rather
    than read off the outputs, because the failure mode is an argument being dropped — a test on
    outputs alone stays green through exactly that edit."""
    tk, b = next(((t, x) for t, x in _bundles()
                  if cs._cs_details_freq(x) == "annual"
                  and cs._cs_summary_freq(x) == "quarterly"), (None, None))
    if b is None:
        pytest.skip("no committed bundle currently splits the two frequencies")

    asked: list[tuple[str, str | None]] = []

    class _Recorder:
        """Forwards to the real bundle, recording the (sheet, freq) each read requests."""

        def __init__(self, inner: CiqBundle) -> None:
            self._inner = inner

        def sheet(self, kind: str, name: str, *, freq: str | None = None):
            asked.append((name, freq))
            return self._inner.sheet(kind, name, freq=freq)

        def workbook(self, kind: str, *, freq: str | None = None):
            return self._inner.workbook(kind, freq=freq)

        def __getattr__(self, k: str):
            return getattr(self._inner, k)

    cs.capital_structure_ciq(_Recorder(b))  # type: ignore[arg-type]

    # The LAST read of each sheet is the one whose rows were used (selection reads both Details
    # candidates first, which is why this takes the last rather than the first).
    used = {name: freq for name, freq in asked if name.startswith("Capital Structure")}
    assert used.get("Capital Structure Details") == "annual", (
        f"{tk}: the instruments came from {used.get('Capital Structure Details')!r} — the "
        f"quarterly workbook repeats the annual section under a note that does not describe it")
    assert used.get("Capital Structure Summary") == "quarterly", (
        f"{tk}: the aggregates came from {used.get('Capital Structure Summary')!r}, so the "
        f"term-loan step is back to comparing a 12-month column with a 3-month one")


def test_every_details_panel_consumer_reads_the_same_frequency() -> None:
    """REVIEW FINDING (#450, P2) — the coupling has to cover ALL consumers, not the two I coupled.

    `liquidity_covenant_flags` is the THIRD reader of the Details panel and was left on
    `freq="annual"` while `capital_structure_ciq` and `_capital_summary` moved to the picker. Both
    reach `mechanical` (as `capital_structure` and as `quality.liquidity_covenant_flags`) and
    `synthesize` dumps the whole mechanical layer, so on the 16 names that pick quarterly the model
    got a FRESH structured schedule beside a STALE annual debt list, under the same source label.
    Coupling two of three readers moved the basis mismatch rather than removing it.

    THIS ASSERTS OVER THE CALL SITES, not over one function's output, because the bug was an
    UNENUMERATED consumer: a test that checked the two known readers would have passed while the
    third was wrong. It walks the module's AST for every `Capital Structure Details` read and
    requires each to sit behind the picker — so a FOURTH consumer added on a bare `freq="annual"`
    fails here rather than in a synthesis six months later."""
    import ast
    import pathlib

    src = pathlib.Path(cs.__file__).read_text()
    tree = ast.parse(src)
    offenders = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        reads = [
            n for n in ast.walk(fn)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "sheet" and len(n.args) >= 2
            and isinstance(n.args[1], ast.Constant)
            and n.args[1].value == "Capital Structure Details"
        ]
        if not reads:
            continue
        # A reader is coupled if it consults the picker, or IS one of the picker's own helpers.
        calls_picker = any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "_cs_details_freq" for n in ast.walk(fn))
        if fn.name not in ("_cs_details_rows", "_cs_details_freq") and not calls_picker:
            offenders.append(fn.name)
    assert not offenders, (
        f"these read the Capital Structure Details panel without consulting _cs_details_freq: "
        f"{offenders}. Every consumer must read the SELECTED panel — a second reader on a "
        f"hardcoded freq is how a stale debt list came to sit beside a fresh schedule")


def test_the_legacy_debt_line_is_dated_and_tracks_the_picked_panel() -> None:
    """THE OTHER HALF OF #450's P2: an UNDATED source_ref cannot distinguish two vintages of one
    sheet, which is exactly why a stale line sat beside a fresh one unnoticed. The legacy string
    now carries the panel's own as-of, and it must be the SAME panel the structured extractor read.

    Asserted on the live corpus so it is the real stamps being compared, not a fixture's."""
    checked = 0
    for tk, b in _bundles():
        liq = cs.liquidity_covenant_flags(b)
        _, _, structured_as_of = cs.capital_structure_ciq(b)
        if not liq.value or not structured_as_of:
            continue
        checked += 1
        assert structured_as_of in (liq.source_ref or ""), (
            f"{tk}: the legacy debt line cites {liq.source_ref!r} while the structured schedule "
            f"was read from {structured_as_of!r} — two vintages of one panel on one record")
    assert checked, "no name exercised both readers — the coupling was not actually observed"


def test_a_printed_term_loan_step_compares_two_like_windows() -> None:
    """THE MIXED-BASIS FIX, asserted where it matters: a printed STEP.

    16 of 19 names had a 12-month column adjacent to a 3-month one in the annual Summary, so the
    term-loan movement stepped between two different windows (SMPL's
    `12 months Aug-30-2025 249.1 → 3 months May-30-2026 397.0`). The columns are read from the
    SHEET rather than parsed back out of the rendered summary string — display formatting is never
    load-bearing, and re-parsing the line this module just wrote would be a second parser of the
    same value.

    Names whose last two columns still differ but that print NO step are not failures: with no
    movement rendered there is no comparison to mislead anyone. FUBO is that case at build time —
    a tie keeps it on annual, its columns read 12/3, and it carries no term loans. Latent, not
    live, and recorded here so it is not rediscovered as a surprise."""
    mixed_with_step, checked = [], 0
    for tk, b in _bundles():
        freq = cs._cs_summary_freq(b)
        try:
            s = b.sheet("financials", "Capital Structure Summary", freq=freq)
        except CiqUnavailableError:
            continue
        hdrs = [r for r in s if r and "Fiscal Peri" in str(r[0])]
        if not hdrs:
            continue
        vcols = [j for j in range(1, len(hdrs[-1])) if "months" in str(hdrs[-1][j]).lower()]
        if len(vcols) < 2:
            continue
        _, summary, _ = cs.capital_structure_ciq(b)
        if "→" not in (summary.value or ""):      # no movement rendered → nothing to mislead
            continue
        checked += 1
        wins = [_WINDOW.search(cs._cs_col_label(hdrs[-1][j])) for j in vcols[-2:]]
        lens = {m.group(1) for m in wins if m}
        if len(lens) > 1:
            mixed_with_step.append((tk, sorted(lens)))
    assert checked, "no name printed a term-loan step — the invariant tested nothing"
    assert not mixed_with_step, (
        f"a term-loan movement steps between two different windows: {mixed_with_step}. The step "
        f"is only a comparison if both endpoints cover the same span")
