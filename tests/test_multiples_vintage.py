""""The last pair is the latest close" was a claim about the export; now it is true by construction.

PR-2 OF THE PRE-ASSEMBLY SET, and the last of the `…(latest)` family #453 opened.

TWO HALVES, ONE SOURCE. `_multiples_close` returns `(date, close)` pairs in COLUMN order, and FIVE
downstream reads take a positional `[-1]`: `ev_ebitda_current`, `pe_ltm_current`, `ev_ebitda_asof`,
`_own_history_band`'s current/history split, and the NM-at-latest guard in `ev_ebitda_percentile`.
Every one of them silently means "rightmost COLUMN" unless the export happens to run
chronologically — the same unasserted convention `_latest_col` now refuses on, and the one item 20
records arriving THROUGH THE DATA PROVIDER (`source_ref="Close (latest)"` on a months-old value).

FIXED AT THE SOURCE rather than at five call sites: the pairs are sorted by date, so positional-last
IS latest-by-date. **A no-op on today's corpus — 76 metric-series across 19 bundles, 0 out of order,
0 undated** — which makes it a recurrence guard, exactly as `_latest_col`'s was when it shipped.

A PARTIALLY-DATED SERIES IS LEFT ALONE (the `_cs_col_date` contract): an undated column cannot be
PLACED in time, so reordering around it would be a guess rather than a fix.

AND THE STAMPS NAME THEIR CLOSE. `Close (latest)` was an undated recency claim a reader cannot check
and that cannot go visibly stale. Live on all 19 names; now `Close [2026-08-07]`.

NOT IN THIS PR: the item-34 export-configuration sidecar. Its remedy is an OPERATOR action (record
the config at the next pull) and **no sidecar exists on disk** — building a reader for a file that
does not exist is the speculative build the house rules forbid.
"""
from __future__ import annotations

from datetime import date

import pytest

from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.manual_store import LocalFolderStore

#: A Multiples sheet in the REAL shape `_multiples_close` parses: a header row whose first cell
#: starts with one of `_MULT_HEADER`, then the metric label, then its `Close` row. Columns start at
#: index 2 (0 = label, 1 = the Close/Average/High/Low sub-label).
_HDR = next(iter(cs._MULT_HEADER))


def _sheet(dates: list[str], closes: list[float | str]) -> list[list[object]]:
    serial = [(date.fromisoformat(d) - date(1899, 12, 30)).days for d in dates]
    return [
        [f"{_HDR} (test)", "", *serial],
        ["TEV/LTM EBITDA", "", *[""] * len(serial)],
        ["", "Close", *closes],
    ]


def test_a_descending_export_is_reordered_so_the_last_pair_is_the_latest() -> None:
    """THE FIX. A right-to-left export makes the rightmost column the OLDEST, and five positional
    reads would each take it as current. Sorting at the source makes all five right at once."""
    rows = _sheet(["2026-06-30", "2026-03-31", "2025-12-31"], [9.0, 8.0, 7.0])
    pairs = cs._multiples_close(rows, "TEV/LTM EBITDA")
    assert [d.isoformat() for d, _ in pairs] == ["2025-12-31", "2026-03-31", "2026-06-30"]
    assert pairs[-1] == (date(2026, 6, 30), 9.0), (
        "the last pair is not the latest close — every positional `[-1]` downstream is reading a "
        "stale figure as current")


def test_an_ascending_export_is_untouched() -> None:
    """THE NO-OP CASE, which is every committed bundle today: already ascending, so the sort must
    not disturb the series a band and its percentile are computed over."""
    rows = _sheet(["2025-12-31", "2026-03-31", "2026-06-30"], [7.0, 8.0, 9.0])
    pairs = cs._multiples_close(rows, "TEV/LTM EBITDA")
    assert [v for _, v in pairs] == [7.0, 8.0, 9.0]


def test_a_partially_dated_series_is_left_in_column_order() -> None:
    """DEGRADE, DON'T GUESS — the `_cs_col_date` contract. An undated column cannot be placed in
    time, so a series carrying one keeps its column order rather than being reordered AROUND the
    hole, which would assert a position the sheet never stated."""
    rows = _sheet(["2026-06-30", "2026-03-31"], [9.0, 8.0])
    rows[0].append("LTM")            # an undated column
    rows[2].append(10.0)
    pairs = cs._multiples_close(rows, "TEV/LTM EBITDA")
    assert [v for _, v in pairs] == [9.0, 8.0, 10.0], (
        "a series with an undated column was reordered — the sort guessed where the undated "
        "column belongs in time")


def test_nm_maps_to_none_and_still_holds_its_place_after_sorting() -> None:
    """NM IS A REAL STATE, not a gap (the FUBO rule), and the NM-at-latest guard in
    `ev_ebitda_percentile` reads `pairs[-1][1] is None` POSITIONALLY. Sorting must carry the None
    with its date, or that guard starts inspecting the wrong quarter."""
    rows = _sheet(["2026-06-30", "2026-03-31"], ["NM", 8.0])
    pairs = cs._multiples_close(rows, "TEV/LTM EBITDA")
    assert pairs[-1][0] == date(2026, 6, 30) and pairs[-1][1] is None, (
        "the NM latest close lost its position after sorting — the percentile guard would now "
        "refuse (or accept) on the wrong quarter")


# ─── the stamps, on the live corpus ─────────────────────────────────────────────────────────────
def _bundles() -> list[tuple[str, CiqBundle]]:
    root = get_config().data_dir / "manual" / "ciq"
    if not root.is_dir() or not any(root.iterdir()):
        pytest.skip("licensed CIQ bundles unavailable (never committed)")
    ms = LocalFolderStore(root)
    return [(tk, CiqBundle.from_files(tk, ms.files(tk)))
            for tk in sorted(p.name for p in root.iterdir() if p.is_dir()) if ms.files(tk)]


def test_the_multiples_stamps_name_their_close_and_never_say_latest() -> None:
    """THE LAST `…(latest)` PAIR, closed. Asserted as a PROPERTY of every stamp over the live
    corpus rather than a table of dates, so a re-pull changes the data without rotting this."""
    seen = 0
    for tk, b in _bundles():
        for fn, label in ((cs.ev_ebitda_current, "EV/EBITDA"), (cs.pe_ltm_current, "P/LTM EPS")):
            s = fn(b)
            if s.value is None:
                continue
            seen += 1
            ref = s.source_ref or ""
            assert "(latest)" not in ref, (
                f"{tk} {label}: the stamp still claims recency without naming a close — {ref!r}")
            assert "Close [" in ref, f"{tk} {label}: the stamp names no date — {ref!r}"
            inside = ref.split("Close [", 1)[1].split("]")[0]
            date.fromisoformat(inside)  # raises if it is not a real ISO date
    assert seen, "no name yielded a multiple — the assertion never ran"


def test_the_sort_moves_no_committed_value() -> None:
    """THE BLAST-RADIUS PIN. The sort is a recurrence guard, not a re-valuation: on a corpus that
    is already ascending it must change NOTHING. Compares the freshly-computed multiple against
    the committed artifact, so a sort that silently re-picked a quarter would redden here."""
    import json
    import pathlib

    moved = []
    for tk, b in _bundles():
        path = pathlib.Path("data/dossiers") / tk / "dossier.json"
        if not path.is_file():
            continue
        committed = (json.loads(path.read_text())["mechanical"]["valuation"].get("ev_ebitda")
                     or {}).get("value")
        fresh = cs.ev_ebitda_current(b).value
        if committed is not None and fresh is not None and abs(committed - fresh) > 0.05:
            moved.append(f"{tk}: {committed} → {fresh}")
    assert not moved, (
        f"the date sort changed a committed multiple: {moved}. On an already-ascending corpus it "
        f"must be a no-op — a move means it is re-picking the current quarter, not guarding order")
