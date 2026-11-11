"""A CIQ MARKER IS A STATED GAP, NEVER AN OLDER VALUE OR A DROPPED ROW — fix request 2, order 3,
the residuals of document 12's marker fixes (audits RA-D3, RA-D8, RA-D13; 2026-11-10).

Document 12's fixes made every latest-cell reader refuse a marker rather than step back to an
older column. Three readers walk a sheet their own way and kept the step-back:

* RA-D3 — Guidance. A dated column whose Guidance cell is a marker was skipped, so the next older
  dated guide was served as the "latest" and handed to the guide check.
* RA-D8 — Segments. A segment whose latest cell is a marker left the mix, and the segment count
  the gap test reads fell with it.
* RA-D13 — Consensus. One marker in the cell that identifies the consensus block left
  `consensus_levels` empty with no reason.

The real-export pins mutate the export on disk IN MEMORY, cell by cell, with each of document 7's
eight CIQ markers (the auditor's list, never the code's own, so the guard is tested and not its
list), and assert invariants that hold on whichever export the folder holds. They skip where the
licensed folder is absent, as on CI; the constructed twins below each run everywhere.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, clean_num, excel_date
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.schemas import ConsensusContext, Sourced, SourceStatus

#: Document 7's eight CIQ markers: what an export prints where it holds no value.
MARKERS = ("", "-", "—", "NM", "NA", "N/A", "Entitlement Needed", "No Data Available")


def _real(ticker: str) -> CiqBundle:
    files = LocalFolderStore.from_config(get_config()).files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


# --- RA-D3: the newest guide is the latest, whatever its cell holds ------------------------------


def _revenue_block(rows: list[list[Any]]) -> tuple[int, list[Any], int]:
    """(the Revenue block's Guidance row, its period header, its Guidance Date row)."""
    starts = cs._guidance_starts(rows)
    for idx, bi in enumerate(starts):
        if str(rows[bi][0]).strip() != "Revenue":
            continue
        end = starts[idx + 1] if idx + 1 < len(starts) else len(rows)
        gdate, guide, _actual = cs._guidance_rows(rows, bi, end)
        header = cs._nearest_period_header(rows, bi)
        assert gdate is not None and guide is not None and header is not None
        return guide, header, gdate
    pytest.skip("the export guides no revenue")


@pytest.mark.parametrize("marker", MARKERS)
def test_ra_d3_a_marker_in_smpls_newest_revenue_guide_never_serves_an_older_one(
        marker: str) -> None:
    """THE AUDIT'S CASE, on SMPL's export as it stands: every Revenue Guidance cell at the newest
    date CIQ gives a guide is set to the marker. The read must name that date and that cell, and
    the guide check must receive no guide, never the one before it (on the 2026-11-10 export:
    FQ4 2026's 322.00–332.00 of 2026-07-09, served beside guides dated 2026-10-27)."""
    b = _real("SMPL")
    rows = b.sheet("estimates", "Guidance")
    guide, header, gdate = _revenue_block(rows)
    dated = [(d, j) for j in range(1, len(header))
             if (d := excel_date(rows[gdate][j])) is not None and cs._parse_range(rows[guide][j])]
    newest = max(d for d, _j in dated)
    older = [d for d, _j in dated if d < newest]
    assert older, "the export holds no older guide, so a step-back could not be seen"
    first = min(j for d, j in dated if d == newest)
    for d, j in dated:
        if d == newest:
            rows[guide][j] = marker
    assert cs.revenue_guide_lohi(b) == (None, None, None, None), (
        "an older revenue guide was handed to the guide check in place of the newest one")
    line = cs.guidance_bridge(b).value or ""
    assert (f"Revenue: latest guide {cs.GUIDE_UNREAD} for {str(header[first]).strip()} (dated "
            f"{newest.isoformat()}) — its Guidance cell reads ") in line, line
    assert "an older guide is never read in its place" in line
    row = next(r for r in cs.guidance_bridge_rows(b).value or [] if r.metric == "Revenue")
    assert row.dated == newest.isoformat() and row.latest_guide.startswith(cs.GUIDE_UNREAD)
    assert cs.revenue_guide_from_rows([row]) == (None, None, None, None)


def _block(periods: list[str], guides: list[object], dates: list[str],
           actuals: list[object]) -> list[list[object]]:
    """One Revenue block in the real sheet shape (`tests/test_guidance_point_refusal.py`)."""
    return [["", *periods], ["Revenue"], ["Guidance Date", *dates], ["Guidance", *guides],
            ["Actual/Latest"], ["Actual", *actuals]]


def _reads(rows: list[list[object]], *, cut: date | None = None) -> Any:
    return cs._reads_at_cut(rows, cs._metric_starts(rows, ("Revenue",)), date(2026, 8, 12), 45,
                            cut)


@pytest.mark.parametrize("marker", MARKERS)
def test_ra_d3_twin_a_dated_marker_is_the_latest_guide_unread(marker: str) -> None:
    """(+) The newest dated cell reads a marker: the read is that period, that date, unread, with
    the cell named; the delivery record of the older period stands."""
    reads, after = _reads(_block(["FY 2025", "FY 2026"], ["100.00 - 110.00", marker],
                                 ["2025-02-01", "2026-02-01"], [112.0, ""]))
    assert after == [] and reads is not None
    (r,) = reads
    assert (r.guide, r.guide_num, r.guide_range, r.period, r.dated) == (
        cs.GUIDE_UNREAD, None, None, "FY 2026", date(2026, 2, 1))
    assert r.unread is not None and "row 4, column 3" in r.unread
    assert (r.resolved, r.met_n, r.recent_period) == (1, 1, "FY 2025")


def test_ra_d3_twin_a_readable_newest_guide_and_an_undated_marker_read_as_before() -> None:
    """(−) The guard fires on a DATED unread cell only. A readable newest guide is read; a marker
    with no date beside it is no guide CIQ gave, and leaves the older guide the latest."""
    (ok,), _ = _reads(_block(["FY 2025", "FY 2026"], ["100.00 - 110.00", "120.00 - 130.00"],
                             ["2025-02-01", "2026-02-01"], [112.0, ""]))
    assert (ok.guide_range, ok.period, ok.unread) == ((120.0, 130.0), "FY 2026", None)
    (old,), _ = _reads(_block(["FY 2025", "FY 2026"], ["100.00 - 110.00", "NA"],
                              ["2025-02-01", ""], [112.0, ""]))
    assert (old.guide_range, old.period, old.unread) == ((100.0, 110.0), "FY 2025", None)


def test_ra_d3_twin_a_marker_dated_after_the_cut_withholds_the_read() -> None:
    """A dated marker after the price date is a guide CIQ gave after it, like any other: CIQ's one
    guide per period has overwritten the one that stood, so the sheet is not read (STATE row 57)."""
    reads, after = _reads(_block(["FY 2025", "FY 2026"], ["100.00 - 110.00", "NA"],
                                 ["2025-02-01", "2026-09-01"], [112.0, ""]), cut=date(2026, 8, 1))
    assert reads is None
    assert [(a.period, a.read, a.value, a.dated) for a in after] == [
        ("FY 2026", "guide", "NA", "2026-09-01")]


# --- RA-D8: a segment a marker hides is named, never dropped -------------------------------------


def _segments_block(rows: list[list[Any]]) -> tuple[int, int, int]:
    hdr = cs._period_header(rows)
    start = next(i for i, r in enumerate(rows) if r and str(r[0]).strip() == "Revenues")
    total = next(i for i, r in enumerate(rows) if r and str(r[0]).strip().startswith("Total Rev"))
    col = cs.latest_cell(rows, total, hdr).col
    assert col is not None
    return start, total, col


@pytest.mark.parametrize("marker", MARKERS)
def test_ra_d8_a_marker_in_ubers_delivery_segment_is_named_and_the_count_is_unknown(
        marker: str) -> None:
    """THE AUDIT'S SHAPE, on UBER's export as it stands: the first named segment with a number at
    the latest column is set to the marker. The mix must not be printed without it, and the count
    the gap test reads must not fall (on 2026-11-10: "Mobility 57%; Freight 10%", count 2)."""
    b = _real("UBER")
    rows = b.sheet("financials", "Segments", freq="annual")
    start, total, col = _segments_block(rows)
    victim = next(i for i in range(start + 1, total)
                  if clean_num(rows[i][col]) is not None and cs.is_segment_line(str(rows[i][0])))
    name = str(rows[victim][0]).strip()
    rows[victim][col] = marker
    got = cs.segments(b)
    assert got.status is SourceStatus.UNKNOWN and got.value is None, got.value
    assert f"'{name}' reads" in (got.note or ""), got.note
    assert cs.segment_count(b) is None


def test_ra_d8_a_period_ciq_marks_in_every_real_segments_block_still_reads() -> None:
    """(−) CORPUS BEFORE SYNTHETIC: CIQ marks a segment the period does not report ('-' at the
    latest column; 28 such rows across the 69 blocks on disk 2026-11-10), and the rest then sums
    to the total. On every page's export the guard must stay silent: the mix reads as before."""
    store = LocalFolderStore.from_config(get_config())
    tickers = [t for t in ("EPAM", "GOOGL", "MCK", "UBER", "VRRM", "WERN", "WLK")
               if store.files(t)]
    if not tickers:
        pytest.skip("no licensed CIQ bundle on this machine (never committed)")
    for t in tickers:
        b = CiqBundle.from_files(t, store.files(t))
        for field in (cs.segments(b), cs.geographic(b), cs.segment_ebitda(b)):
            assert "the mix is not stated" not in (field.note or ""), (t, field.note)


def _zzfx_with_segments(rows: list[list[Any]]) -> CiqBundle:
    b = CiqBundle.from_files(gen.TICKER, sorted((gen.HERE / gen.TICKER).iterdir()))
    b.sheet("financials", "Income Statement", freq="annual")
    wb = b.workbook("financials", freq="annual")
    assert wb is not None
    b._cache[wb.path]["Segments"] = rows
    return b


def _seg_rows(alpha: object, beta: object, gamma: object, total: float) -> list[list[Any]]:
    head = ["For the Fiscal Period Ending", f"12 months\n{gen._mdy(gen.A_DATES[-2])}",
            f"12 months\n{gen._mdy(gen.A_DATES[-1])}"]
    return [head, ["Revenues"], ["Alpha", 50.0, alpha], ["Beta", 30.0, beta],
            ["Gamma", 20.0, gamma], ["Total Revenues", 100.0, total]]


def test_ra_d8_twin_a_hidden_segment_is_named_and_a_discontinued_one_is_not() -> None:
    """(+) Beta reads 'NA' and the rest is 70% of the total: UNKNOWN, Beta named, no count. (−)
    Gamma reads '-' and the rest IS the total: a segment the period does not report, dropped as
    before, the count 2."""
    hidden = _zzfx_with_segments(_seg_rows(60.0, "NA", 10.0, 100.0))
    got = cs.segments(hidden)
    assert got.status is SourceStatus.UNKNOWN and "'Beta' reads 'NA'" in (got.note or "")
    assert "70.0% of the total" in (got.note or "") and cs.segment_count(hidden) is None
    gone = _zzfx_with_segments(_seg_rows(60.0, 40.0, "-", 100.0))
    ok = cs.segments(gone)
    assert ok.status is SourceStatus.PRESENT and ok.value == "Alpha 60%; Beta 40%", ok.note
    assert cs.segment_count(gone) == 2


# --- RA-D13: an empty consensus says why ---------------------------------------------------------


def test_ra_d13_a_marker_in_smpls_probe_cells_empties_the_levels_with_a_reason() -> None:
    """THE AUDIT'S CASE, both probe cells, on SMPL's export as it stands. (+) The identified
    block's current-year Revenue cell reads 'NA', then the Market Summary's Current Year does:
    the levels are empty and the reason names the cell. (−) Unmutated, the levels read and there
    is no reason."""
    b = _real("SMPL")
    levels, why = cs.consensus_levels_read(b)
    assert levels and why is None, why
    blk = cs.consensus_block(b)
    assert blk is not None
    rows = b.sheet("estimates", "Consensus")
    col = next(k for k, c in enumerate(blk.header_cells)
               if str(c).strip().replace(".0", "") == str(blk.current_fy))
    rows[blk.start][col] = "NA"
    levels, why = cs.consensus_levels_read(b)
    assert levels == {} and why is not None
    assert f"row {blk.start + 1} reads 'NA' at FY{blk.current_fy}" in why, why

    b2 = _real("SMPL")
    rows2 = b2.sheet("estimates", "Consensus")
    ms = next(i for i, r in enumerate(rows2) if r and str(r[0]).strip() == "Market Summary")
    at = next(i for i in range(ms, ms + 60) if "Revenue" in [str(c).strip() for c in rows2[i]])
    k = [str(c).strip() for c in rows2[at]].index("Revenue")
    rows2[at][k + 2] = "NA"
    levels, why = cs.consensus_levels_read(b2)
    assert levels == {} and why is not None
    assert "Market Summary's 'Revenue' Current Year reads 'NA'" in why, why


def _consensus_rows(probe: object) -> list[list[Any]]:
    """The smallest Consensus sheet the reader identifies: the banner, the Market Summary, and
    one unindented Revenue block with its stats."""
    return [[f"Current Fiscal Year End: {gen._mdy(date(2027, 5, 31))}"], ["Market Summary"],
            ["Revenue", 115.0, 460.0, 470.0], ["Fiscal Years"],
            ["Company Level (USD)", "2026", "2027", "2028"],
            ["Revenue", 440.0, probe, 480.0],
            ["  Median", 440.0, 459.0, 479.0], ["  High", 445.0, 470.0, 490.0],
            ["  Low", 435.0, 450.0, 470.0], ["Done"]]


def _zzfx_with_consensus(rows: list[list[Any]]) -> CiqBundle:
    b = CiqBundle.from_files(gen.TICKER, [gen.HERE / gen.ESTIMATES_XLS])
    b.sheet("estimates", "Guidance")
    wb = b.workbook("estimates")
    assert wb is not None
    b._cache[wb.path]["Consensus"] = rows
    return b


@pytest.mark.parametrize("marker", MARKERS)
def test_ra_d13_twin_the_probe_cell_names_itself(marker: str) -> None:
    levels, why = cs.consensus_levels_read(_zzfx_with_consensus(_consensus_rows(marker)))
    assert levels == {} and why is not None and "row 6 reads" in why, why
    ok, none = cs.consensus_levels_read(_zzfx_with_consensus(_consensus_rows(460.0)))
    assert [(c.fy, c.median) for c in ok["Revenue"]] == [("2027", 459.0), ("2028", 479.0)]
    assert none is None


def test_ra_d13_twin_a_zero_probe_is_named_as_the_zero_it_is() -> None:
    """ORKA's and TECX's shape (pre-revenue: a Current Year of 0 over a block reading 0.0). A
    numeric zero is no figure to `_stat_num` (reported, not fixed here), and the reason says that
    rather than quoting '0.0' as if it were a marker."""
    rows = _consensus_rows(0.0)
    rows[2] = ["Revenue", 0.0, "0.0", 0.0]
    _levels, why = cs.consensus_levels_read(_zzfx_with_consensus(rows))
    assert why is not None and "Current Year (0)" in why, why
    assert "row 6 reads 0.0 at FY2027, which this reader does not count as a figure" in why
    assert "'0.0'" not in why


def test_ra_d13_the_reason_is_kept_off_the_synthesis_request_and_off_a_page_without_one() -> None:
    """The note is the page's, not the model's: `NOT_SENT` keeps every request byte-identical, and
    a None note is dropped from the JSON (`DROP_WHEN_NONE`), so no committed page moves."""
    from vinci.dossier.schemas import DROP_WHEN_NONE
    from vinci.dossier.synthesis import NOT_SENT

    blank: Sourced[str] = Sourced.unknown(note="x")
    cc = ConsensusContext(consensus_levels_note="why", eps_trend=blank, revenue_trend=blank,
                          revision_history=blank, surprise_history=blank)
    assert "consensus_levels_note" not in cc.model_dump(
        exclude=NOT_SENT["consensus_context"])
    assert ("consensus_context", "consensus_levels_note") in DROP_WHEN_NONE


def test_ra_d13_a_refresh_that_reads_levels_drops_the_note_saying_they_are_absent(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """REVIEW FINDING (order 3, round 0). Assembly writes `consensus_levels_note` only when the
    levels are absent; the refresh transform writes levels from a fresher export and left the note
    standing, so a page would carry levels beside a note saying why there are none. (+) A refresh
    that reads levels removes the note. (−) One that reads none leaves the page as it was."""
    import vinci.dossier.ciq as ciq_mod
    from vinci.dossier import refresh

    cell = cs.ConsensusCell(fy="2027", median=459.0, high=470.0, low=450.0, std_dev=None,
                            estimates=None, is_forward=True)
    monkeypatch.setattr(ciq_mod.CiqBundle, "from_files",
                        staticmethod(lambda *_a, **_k: object()))
    mech = {"consensus_context": {"consensus_levels": None, "consensus_levels_note": "why"}}

    monkeypatch.setattr(cs, "consensus_levels", lambda _b: {"Revenue": [cell]})
    out = refresh.consensus_transform("ZZFX")(mech)
    assert out["consensus_context"]["consensus_levels"]["Revenue"][0]["median"] == 459.0
    assert "consensus_levels_note" not in out["consensus_context"], out["consensus_context"]

    monkeypatch.setattr(cs, "consensus_levels", lambda _b: {})
    assert refresh.consensus_transform("ZZFX")(mech) == mech
