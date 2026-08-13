"""The capital-structure panel is the LATER-FILED of the two workbooks, not the annual one.

WHAT WAS WRONG. `capital_structure_ciq` and `_capital_summary` both opened their sheet with
`freq="annual"` as a hardcoded literal. Nobody chose it, and the quarterly workbook sat unread in
the same bundle. Measured over the 19 committed bundles, 16 names carry a NEWER quarterly panel —
median ~150 days, up to 265 (V), 263 (CPB), 259 (BRBR/PENG), 254 (SMPL), 175 (NFLX). Same
instruments, staler filing: the debt table described a company as it stood six months ago while a
July panel sat in the folder.

THE RULE IS "NEWER", NOT "QUARTERLY", AND THE CORPUS IS WHY. **NIKE's annual panel (Jul-15-2026)
is newer than its quarterly one (Apr-01-2026), and ONON's (Mar-03-2026) beats a quarterly export
from Aug-12-2025 — a year stale.** A blanket switch to quarterly improves sixteen names and makes
two WORSE, which is the shape of a change that reads as a win in aggregate and is a regression on
the names it touches. The negative pins below are those two, and they are real observed shapes
rather than invented ones.

THE SECOND FINDING, which arrived with the first. The term-loan movement steps the last two period
columns of whatever sheet it opens, and in the ANNUAL workbook those two need not share a window:
**16 of 19 names had a 12-month column sitting next to a 3-month one.** SMPL printed

    term loans 397.0 (12 months Aug-30-2025 249.1 → 3 months May-30-2026 397.0)

stepping a TWELVE-month endpoint to a THREE-month one. The labels were honest — they name the
columns, per the R3 fix — so the mismatch was visible rather than hidden, but the comparison was
still between two different windows. At quarterly it reads `(3 months … 396.9 → 3 months … 397.0)`.
After the change 18 of 19 names are like-for-like.
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


# ─── the rule itself, asserted RELATIONALLY so a re-pull cannot rot it ───────────────────────────
def test_the_picked_panel_is_always_the_later_filed_one() -> None:
    """THE WHOLE RULE, over every committed bundle. Stated as a relation between the two panels'
    filed dates rather than as a table of expected answers, so re-pulling the workbooks changes the
    data without changing this test's truth — and any name that acquires a newer annual export is
    covered the day it lands, not the day someone remembers to add it."""
    checked = 0
    for tk, b in _bundles():
        a, q = _filed(b, "annual"), _filed(b, "quarterly")
        picked = cs._capital_panel_freq(b)
        if a is None and q is None:
            assert picked == "annual", f"{tk}: no readable panel, must fall back to the status quo"
            continue
        checked += 1
        if q is not None and (a is None or q > a):
            assert picked == "quarterly", f"{tk}: quarterly is later-filed ({q} > {a}) yet {picked}"
        else:
            assert picked == "annual", (
                f"{tk}: annual is later-or-equal ({a} vs {q}) yet the picker took {picked} — this "
                f"is the 'always prefer quarterly' regression, which makes this name STALER")
    assert checked, "no bundle exercised the rule — the corpus read yielded nothing"


def test_a_newer_annual_panel_is_kept_because_the_rule_is_not_prefer_quarterly() -> None:
    """THE NEGATIVE PIN, and the rejected design it rules out. Blanket-preferring quarterly was the
    obvious implementation and it is WRONG on the live corpus: at least one committed name files its
    annual panel LATER than its quarterly one. Observed instances when this shipped — NIKE
    (annual Jul-15-2026 vs quarterly Apr-01-2026) and ONON (Mar-03-2026 vs a quarterly export from
    Aug-12-2025, a year stale).

    Asserted as "at least one such name exists and every one of them keeps annual", so the pin
    survives a re-pull that reshuffles which names are in that state — but fails loudly if the
    population empties, because a rule with nothing left to test has stopped testing anything."""
    keepers = []
    for tk, b in _bundles():
        a, q = _filed(b, "annual"), _filed(b, "quarterly")
        if a is not None and q is not None and a > q:
            keepers.append((tk, a, q))
            assert cs._capital_panel_freq(b) == "annual", (
                f"{tk}: annual panel filed {a} is NEWER than quarterly {q}, so preferring "
                f"quarterly would move this name BACKWARDS in time")
    assert keepers, (
        "no committed name has a newer ANNUAL panel any more, so the negative case is untested — "
        "re-measure the corpus and pin a name that still exercises it, or this rule is only "
        "asserted by its positive half")


def test_a_tie_keeps_the_annual_panel() -> None:
    """EQUAL FILING DATES CHANGE NOTHING. FUBO is the live instance — both its workbooks carry the
    same `Q3 2026 filed Aug-05-2026` panel, because CIQ put a quarterly panel in the annual export.
    Nothing is gained by moving, so the status quo holds and the diff stays smaller."""
    ties = []
    for tk, b in _bundles():
        a, q = _filed(b, "annual"), _filed(b, "quarterly")
        if a is not None and a == q:
            ties.append(tk)
            assert cs._capital_panel_freq(b) == "annual", f"{tk}: a tie moved off the status quo"
    if not ties:
        pytest.skip("no tied pair in the corpus right now (FUBO was the instance at build time)")


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
    answers "quarterly"; WITHOUT it the fallback panel is admitted as an annual reading, takes the
    first slot, and the strict `>` then leaves the answer at "annual" — a name labelled from a
    workbook it does not have. Built from the REAL type by handing `from_files` only the quarterly
    path."""
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

    # …and the PRODUCTION picker is not fooled by it. This is the assertion the guard owns.
    assert cs._capital_panel_freq(quarterly_only) == "quarterly", (
        "the fallback workbook was admitted as an ANNUAL panel, so the picker named a frequency "
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
    re-points the picker at the column parser, the divergent case below reddens."""
    from vinci.dossier.mechanical import _cs_panel_filed as via_mechanical

    assert cs._cs_panel_filed is via_mechanical, (
        "the panel stamp has two parsers again — mechanical must re-export the one in ciq_sheets, "
        "not define its own")

    divergent = "A 2025 (Dec-31-2025) filed Jan-23-2026"
    assert cs._cs_panel_filed(divergent) == date(2026, 1, 23), "the FILING date is the ranking key"
    assert cs._cs_col_date(divergent) == (2025, 12, 31), (
        "the column parser stopped reading the bare date — if that is deliberate, this test's "
        "premise needs re-reading, because the two helpers no longer differ")

    # the ordinary shapes, where the two happen to agree — which is exactly why the trap is easy
    # to walk into and worth a pin
    for stamp, want in (("A 2025 filed Jan-23-2026", date(2026, 1, 23)),
                        ("Q2 2026 filed Jul-17-2026", date(2026, 7, 17))):
        assert cs._cs_panel_filed(stamp) == want
    assert cs._cs_panel_filed("") is None and cs._cs_panel_filed("A 2025") is None


# ─── the coupling, which is what keeps the block on ONE basis ───────────────────────────────────
def test_the_instruments_and_the_aggregates_are_read_at_one_frequency() -> None:
    """THE BASIS-MISMATCH GUARD, and the reason the summary took a `freq` parameter at all.

    Reading the Details panel at quarterly while the Summary stayed annual would put itemized
    instruments on one filing and the aggregates that reconcile against them on another — inside a
    single capital-structure block. That is worse than either panel being stale on its own, because
    the two are meant to tie out.

    Pinned by RECORDING what the production call site asks for, so deleting the `freq=` argument
    reddens this. A test that only read the outputs would stay green through exactly that edit."""
    tk, b = next(((t, x) for t, x in _bundles()
                  if cs._capital_panel_freq(x) == "quarterly"), (None, None))
    if b is None:
        pytest.skip("no bundle currently picks quarterly, so the coupling cannot be observed")

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

    freqs = {name: freq for name, freq in asked if name.startswith("Capital Structure")}
    assert freqs.get("Capital Structure Details") == "quarterly", freqs
    assert freqs.get("Capital Structure Summary") == "quarterly", (
        f"{tk}: the aggregates were read at {freqs.get('Capital Structure Summary')!r} while the "
        f"instruments came from quarterly — the two halves of one block on two filings")


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
        freq = cs._capital_panel_freq(b)
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
