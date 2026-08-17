""""The last pair is the latest close" was a claim about the export. Now nobody makes it.

PR-2 OF THE PRE-ASSEMBLY SET, and the last of the `…(latest)` family #453 opened.

ONE SELECTOR, NOT A SORT. `_multiples_close` returns pairs in COLUMN order — the sheet's order,
which is not a time order and never was asserted to be one. SIX reads used to take a positional
`[-1]` off it: `ev_ebitda_current`, `pe_ltm_current`, `ev_ebitda_asof`, `_own_history_band`'s
current/history split, `range_position`'s P/E tail, and the NM-at-latest guard in
`ev_ebitda_percentile`. Each silently meant "rightmost COLUMN". They now all ask `_latest_close`,
which maxes over the DATED columns and is order-immune by construction.

WHY NOT THE SORT THIS PR FIRST SHIPPED (#459 review): it could only fire when EVERY column carried
a date, and `read_sheets` pads every row to the sheet's uniform width — so ONE blank pad column
disabled it and left all six readers believing positional-last meant latest. Measured on a
descending export with a single blank pad column: `ev_ebitda_current` returned the OLDEST close,
stamped `Close [2025-09-30] — current multiple`. A confident ISO date on the wrong cell is HARDER
to catch than the `(latest)` it replaced, not easier. An all-or-nothing gate is not "degrade,
don't guess" — it is "stop looking".

AND THE LATEST CELL IS THE LATEST CELL. NM at the latest close is a REAL state (the FUBO rule),
so every reader refuses on it rather than reaching back for an older quarter. The non-Optional
value slot on `_own_history_band` was the defect GENERATOR — it forced each caller to pre-filter,
which IS the backward-fill — so the rule moved INSIDE the helper and both callers stopped filtering.

AND THE STAMPS NAME THEIR CLOSE. `Close (latest)` was an undated recency claim a reader cannot
check and that cannot go visibly stale. An undated close now REFUSES rather than degrading.

NOT IN THIS PR: the item-34 export-configuration sidecar. Its remedy is an OPERATOR action (record
the config at the next pull) and **no sidecar exists on disk** — building a reader for a file that
does not exist is the speculative build the house rules forbid.
"""

from __future__ import annotations

import pathlib
from datetime import date
from typing import Any

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.manual_store import LocalFolderStore

#: A Multiples sheet in the REAL shape `_multiples_close` parses: a header row whose first cell
#: starts with one of `_MULT_HEADER`, then each metric label followed by its `Close` row. Columns
#: start at index 2 (0 = label, 1 = the Close/Average/High/Low sub-label).
_HDR = cs._MULT_HEADER[0]


def _serial(iso: str) -> int:
    return (date.fromisoformat(iso) - date(1899, 12, 30)).days


def _bundle(headers: list[object], ev: list[object], pe: list[object]) -> Any:
    """A stub carrying ONE Multiples sheet in the real shape. `headers` takes serials for dated
    columns and a raw string ("" for a blank pad column, "LTM" for an undated one) otherwise."""
    rows: list[list[object]] = [
        [f"{_HDR} (test)", "", *headers],
        ["TEV/LTM EBITDA", "", *[""] * len(headers)],
        ["", "Close", *ev],
        ["P/LTM EPS", "", *[""] * len(headers)],
        ["", "Close", *pe],
    ]

    class _B:
        ticker = "TEST"

        def sheet(self, _kind: str, _name: str, *, freq: str | None = None) -> list[list[object]]:
            return rows

        def workbook(self, _kind: str, *, freq: str | None = None) -> None:
            return None

    return _B()


def test_a_descending_export_resolves_the_latest_close_at_every_reader() -> None:
    """THE FIX. A right-to-left export makes the rightmost column the OLDEST, and six positional
    reads would each take it as current. Asserted through the PUBLIC readers, not the parser: the
    first cut of this PR pinned `_multiples_close` alone and shipped two unguarded refusals."""
    b = _bundle([_serial("2026-06-30"), _serial("2026-03-31"), _serial("2025-12-31"),
                 _serial("2025-09-30")],
                [9.0, 8.0, 7.0, 6.0], [19.0, 18.0, 17.0, 16.0])
    ev = cs.ev_ebitda_current(b)
    assert ev.value == 9.0, f"the OLDEST close was published as current — {ev.value}"
    # the DATE is asserted structurally, not out of the stamp: the stamp reverted to the undated
    # `Close (latest)` in #460 because it is a join key, and `ev_ebitda_asof` is the honest carrier.
    assert cs.ev_ebitda_asof(b) == date(2026, 6, 30)
    assert cs.pe_ltm_current(b).value == 19.0
    assert "as-of 2026-06-30" in (cs.range_position(b).value or "")


def test_one_blank_pad_column_cannot_disable_the_selection() -> None:
    """THE #459 REVIEW DEFECT, pinned. `read_sheets` pads every row to the sheet's uniform width,
    so a single blank column is the ORDINARY case — and the sort this PR first shipped was gated
    on `all(d is not None)`, which that one blank cell defeated. It then published the oldest
    close under `Close [2025-09-30] — current multiple`: a confident date on the wrong cell."""
    b = _bundle([_serial("2026-06-30"), _serial("2026-03-31"), _serial("2025-12-31"),
                 _serial("2025-09-30"), ""],
                [9.0, 8.0, 7.0, 6.0, ""], [19.0, 18.0, 17.0, 16.0, ""])
    ev = cs.ev_ebitda_current(b)
    assert (ev.value, cs.ev_ebitda_asof(b)) == (9.0, date(2026, 6, 30)), (
        f"one blank pad column re-armed the positional read — got {ev.value} "
        f"stamped {ev.source_ref!r}")


def test_an_undated_trailing_column_does_not_erase_a_dated_close() -> None:
    """DEGRADE, DON'T GUESS — but degrading is not ERASING. The first cut refused whenever the
    last SURVIVING pair was undated, so a trailing `LTM` column blanked the whole ev_ebitda field
    on a name whose dated latest close was sitting right there. That is a regression against the
    behaviour before this PR, which returned a value. The undated column is excluded; the latest
    DATED close is still reported."""
    b = _bundle([_serial("2025-09-30"), _serial("2025-12-31"), _serial("2026-03-31"),
                 _serial("2026-06-30"), "LTM"],
                [8.0, 10.0, 15.0, 14.0, 13.0], [16.0, 18.0, 22.0, 25.0, 24.0])
    ev = cs.ev_ebitda_current(b)
    assert (ev.value, cs.ev_ebitda_asof(b)) == (14.0, date(2026, 6, 30)), (
        f"an undated trailing column erased a dated close — {ev.value} / {ev.note!r}")
    assert cs.pe_ltm_current(b).value == 25.0
    bands = {x.metric: x for x in (cs.own_history_bands(b).value or [])}
    assert bands["EV/EBITDA (TEV/LTM)"].current == 14.0
    assert bands["EV/EBITDA (TEV/LTM)"].as_of == "2026-06-30"


def test_nm_at_the_latest_close_refuses_at_every_reader() -> None:
    """NM IS A REAL STATE (the FUBO rule), NOT A GAP — and item 20 is "no backward-fill on ANY
    time series". Every reader must refuse together, or the page contradicts itself: CNXC shipped
    a P/LTM EPS band `current 8.766527, as_of 2025-12-31` beside a `range_position` reading
    "P/LTM EPS NM (no meaningful trailing P/E at this close)". THE NEGATIVE PIN for the guards."""
    b = _bundle([_serial("2025-09-30"), _serial("2025-12-31"), _serial("2026-03-31"),
                 _serial("2026-06-30"), _serial("2026-08-11")],
                [8.0, 10.0, 15.0, 14.0, "NM"], [16.0, 18.0, 22.0, 25.0, "NM"])
    ev = cs.ev_ebitda_current(b)
    assert ev.value is None and "NM at the latest Close [2026-08-11]" in (ev.note or ""), (
        f"an NM latest close backward-filled to an older quarter — {ev.value} / {ev.source_ref!r}")
    assert cs.ev_ebitda_asof(b) is None, (
        "the as-of outlived the value it dates — `_ev_ebitda_integrity_flag` reads BOTH and would "
        "compose a dated staleness caveat about a multiple the page refused to print")
    assert cs.pe_ltm_current(b).value is None
    assert cs.ev_ebitda_percentile(b).value is None
    assert not (cs.own_history_bands(b).value or []), (
        "a band was published on an NM latest close — the chart would show a current the text "
        "beside it calls NM")


def test_an_all_undated_series_refuses_rather_than_fabricating_nm() -> None:
    """AN UNDATED COLUMN AND A STATED NM ARE DIFFERENT FACTS. The first cut collapsed them: a
    blank/undated series came back as "P/LTM EPS is NM at the latest Close", which `range_position`
    printed to the human as a data state the sheet never carried. Fabricating a STATE is
    fabrication, exactly as fabricating a number is."""
    b = _bundle(["LTM", "Current"], [13.0, 12.0], [24.0, 23.0])
    ev, pe = cs.ev_ebitda_current(b), cs.pe_ltm_current(b)
    assert ev.value is None and "carries a date" in (ev.note or ""), ev.note
    assert pe.value is None and "NM" not in (pe.note or ""), (
        f"an undated series was reported as NM — a data state the sheet never stated: {pe.note!r}")


# ─── the stamps, on the live corpus ─────────────────────────────────────────────────────────────
def _bundles() -> list[tuple[str, CiqBundle]]:
    # `__file__`-relative, NOT cwd-relative. `get_config().data_dir` is the RELATIVE `Path("data")`,
    # so running pytest from anywhere but the repo root made both corpus pins SKIP — reporting
    # "licensed CIQ bundles unavailable" while the corpus sat on disk, and skipping past the
    # `assert seen` counters that exist to catch exactly that kind of silent no-op.
    root = pathlib.Path(__file__).resolve().parents[1] / "data" / "manual" / "ciq"
    if not root.is_dir() or not any(root.iterdir()):
        pytest.skip("licensed CIQ bundles unavailable (never committed)")
    ms = LocalFolderStore(root)
    return [(tk, CiqBundle.from_files(tk, ms.files(tk)))
            for tk in sorted(p.name for p in root.iterdir() if p.is_dir()) if ms.files(tk)]


def test_the_multiples_stamps_are_frozen_because_they_are_join_keys() -> None:
    """THE REVERT, PINNED (#460). `Close [ISO]` was strictly better provenance and had to go back.

    These `source_ref` strings are JOIN KEYS, not display text: an LLM synthesis point cites its
    evidence by copying the string verbatim into `SourcedPoint.source_ref`, `synthesis._traces`
    matches exact/substring, and both renderers dedup endnotes by exact string. So dating the stamp
    broke 8 sealed citations across 7 names (each keeping `cited: true` while resolving to nothing)
    and forked EPAM/IT/UBER's CIQ endnote into two contradictory entries.

    THIS PIN IS THE INVARIANT, NOT THE WORDING: whatever the stamp says, every committed dossier's
    synthesis citations must TRACE into that dossier's own mechanical layer. That is the property
    the reword actually violated, and it holds for any wording — so it cannot rot on a re-pull, and
    it fires on the next author who edits these strings without re-rolling synthesis.

    ITEM 20's `(latest)` FAMILY IS THEREFORE REOPENED. It cannot be closed by rewording; it needs
    provenance keyed by a stable id with the display string derived from it. Recorded in STATE."""
    import json

    root = pathlib.Path(__file__).resolve().parents[1]
    from vinci.dossier.schemas import Dossier
    from vinci.dossier.synthesis import _refs_in, _traces

    broken, scanned = [], 0
    for path in sorted((root / "data" / "dossiers").glob("*/dossier.json")):
        doc = json.loads(path.read_text())
        refs = _refs_in(Dossier.model_validate(doc).mechanical)
        syn = doc.get("synthesis") or {}
        for key in ("bull_points", "bear_points"):
            for i, pt in enumerate(syn.get(key) or []):
                ref = pt.get("source_ref")
                if not ref:
                    continue
                scanned += 1
                if not _traces(ref, refs):
                    broken.append(f"{path.parent.name} {key}[{i}] (cited={pt.get('cited')})")
        # DECISIVE-QUESTION EVIDENCE COUNTS TOO. The first cut walked only bull/bear points, so a
        # reworded stamp quoted ONLY here passed — measured 77 such citations on the corpus, every
        # one of them traceable today, so this is free coverage rather than a new obligation.
        dq = syn.get("decisive_question") or {}
        for side in ("evidence_for", "evidence_against"):
            for i, pt in enumerate(dq.get(side) or []):
                ref = pt.get("source_ref") if isinstance(pt, dict) else None
                if not ref:
                    continue
                scanned += 1
                if not _traces(ref, refs):
                    broken.append(f"{path.parent.name} decisive_question.{side}[{i}]")
        for i, tw in enumerate(syn.get("twin_reference_cases") or []):
            src = tw.get("source")
            if not src or "unverified" in src.lower():
                continue
            scanned += 1
            if not _traces(src, refs):
                broken.append(f"{path.parent.name} twin[{i}]")
    assert scanned, "no committed synthesis citation was scanned — the pin ran vacuously"
    assert not broken, (
        f"{len(broken)} committed synthesis citation(s) no longer trace to their own mechanical "
        f"layer: {broken}. A mechanical `source_ref` was reworded while the sealed synthesis kept "
        f"the old string, so the point still reads as source-verified while resolving to nothing. "
        f"`moved_cited_claims` cannot catch this — its grain is moved FIGURES, not moved strings.")


def test_the_value_and_its_as_of_resolve_the_same_close() -> None:
    """THE INVARIANT THAT BROKE, pinned on the live corpus. `ev_ebitda_current` and
    `ev_ebitda_asof` are read TOGETHER by `_ev_ebitda_integrity_flag`, which composes a staleness
    caveat from the pair. The first cut of this PR gave one a refusal and not the other, so they
    could resolve DIFFERENT cells — and the caveat then rendered a literal `?` where the multiple
    belongs, dating a value the page had refused to print. They share `_latest_close` now.

    PHRASING-INDEPENDENT, so a re-pull moves the data without rotting this: it asserts the two
    agree, never that either equals a particular number. (The prior form pinned committed VALUES
    against a fresh recompute — both sides living — so an ordinary CIQ re-pull failed it while
    naming the sort as the culprit.)"""
    seen = 0
    for tk, b in _bundles():
        s, asof = cs.ev_ebitda_current(b), cs.ev_ebitda_asof(b)
        assert (s.value is None) == (asof is None), (
            f"{tk}: value and as-of disagree about whether a current multiple exists — "
            f"value={s.value!r} as_of={asof!r}. A dated staleness caveat about a refused multiple "
            f"is exactly what this pair being out of step produces.")
        if s.value is None:
            continue
        seen += 1
        assert asof is not None, f"{tk}: a present multiple with no as-of to date it"
    assert seen, "no name yielded a multiple — the assertion never ran"


def test_no_band_outlives_the_close_it_reports() -> None:
    """THE BACKWARD-FILL, pinned on the live corpus. A band's `current` must BE the latest close,
    never the last one that happened to report. Live in the committed artifacts before this fix:
    CNXC shipped a P/LTM EPS band `current 8.766527, as_of 2025-12-31` on the same page whose
    `range_position` read "P/LTM EPS NM (no meaningful trailing P/E at this close)"; SMPL shipped
    `15.958736 @ 2026-03-31` with the identical contradiction.

    Asserted as AGREEMENT BETWEEN THE TWO SURFACES rather than a table of values, so it survives a
    re-pull: whatever the band calls current, the reader beside it must call current too."""
    seen = 0
    for tk, b in _bundles():
        bands = {x.metric: x for x in (cs.own_history_bands(b).value or [])}
        pe_band, pe = bands.get("P/LTM EPS"), cs.pe_ltm_current(b)
        if pe_band is None:
            continue
        seen += 1
        assert pe.value is not None, (
            f"{tk}: a P/LTM EPS band reports current={pe_band.current} @ {pe_band.as_of} while "
            f"`pe_ltm_current` refuses ({pe.note!r}) — the chart shows a multiple the text beside "
            f"it calls NM. This is the backward-fill.")
        assert round(pe_band.current, 1) == round(pe.value, 1), (
            f"{tk}: the band's current ({pe_band.current}) is not the reported latest close "
            f"({pe.value}) — the band reached back for an older quarter")
        assert pe_band.as_of is not None, f"{tk}: a band with no as-of — an undated recency claim"
    assert seen, "no name yielded a P/LTM EPS band — the assertion never ran"
