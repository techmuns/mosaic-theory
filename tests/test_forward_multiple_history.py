"""Forward-multiple history: EV/NTM Revenue, EV/NTM EBITDA, EV/NTM EBIT and P/NTM EPS (context
only), quarterly, from the Financials→Multiples export the page's trailing bands were read from.

THE SHAPES THIS GUARDS, each observed on the committed names' exports (2026-10-07):
- a prefix match on 'TEV/NTM EBIT' lands on 'TEV/NTM EBITDA', which the sheet prints first;
- `_multiples_close` folds 'NM' and '-' into one None, and the four forward rows carry 218 and 62;
- V's EV/NTM EBIT reads '-' at its latest close while its quarter-ends are numbers, so an older
  close is right there to stand in for current — and must not.

The CIQ-backed tests read the licensed workbooks on disk and SKIP without them — they are never
committed. The rest run anywhere.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, clean_num, excel_date
from vinci.dossier.schemas import (
    Dossier,
    ForwardHistoryBand,
    ForwardMultipleHistory,
    MechanicalLayer,
    MultipleClose,
    MultipleHistorySeries,
    dossier_json,
)

ROOT = Path(__file__).resolve().parents[1]
COMMITTED = sorted(p.parent.name for p in (ROOT / "data" / "dossiers").glob("*/dossier.json"))
LABELS = [label for _, label, _ in cs._FORWARD_MULTIPLES]


def _bundle(ticker: str) -> CiqBundle:
    """The name's bundle, or SKIP — the licensed workbooks are never committed."""
    from vinci.config import get_config
    from vinci.dossier.manual_store import LocalFolderStore

    files = LocalFolderStore(get_config().data_dir / "manual" / "ciq").files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


def _multiples(b: CiqBundle) -> list[list[Any]]:
    return b.sheet("financials", "Multiples", freq="quarterly")


def _own_close_cells(rows: list[list[Any]], label: str) -> list[tuple[str, Any]]:
    """The row's dated Close cells, read WITHOUT `_multiples_close_cells`: the row whose first cell
    IS the label, its 'Close' sub-row, the sheet's date header — in time order."""
    hdr = next(i for i, r in enumerate(rows) if r and str(r[0]).strip().startswith(cs._MULT_HEADER))
    li = next(i for i, r in enumerate(rows) if r and str(r[0]).strip() == label)
    ci = next(i for i in range(li, li + 6) if str(rows[i][1]).strip() == "Close")
    dated = [(excel_date(rows[hdr][j]), rows[ci][j]) for j in range(2, len(rows[hdr]))]
    return [(d.isoformat(), c) for d, c in sorted(((d, c) for d, c in dated if d is not None),
                                                  key=lambda p: p[0])]


# --- the reads, on the real workbooks -----------------------------------------------------------


@pytest.mark.parametrize("ticker", COMMITTED)
def test_every_point_is_its_own_rows_close_cell(ticker: str) -> None:
    """ACROSS THE CORPUS: each series is its EXACT row's Close, every column in time order, and a
    cell that is not a number keeps what it said."""
    b = _bundle(ticker)
    rows = _multiples(b)
    fm = cs.forward_multiple_history(b)
    assert fm is not None
    assert [s.row_label for s in fm.series] == LABELS
    for s in fm.series:
        want = [(d, clean_num(c), None if clean_num(c) is not None else cs._cell_text(c))
                for d, c in _own_close_cells(rows, s.row_label)]
        assert [(p.date, p.close, p.cell) for p in s.points] == want, s.metric


@pytest.mark.parametrize("ticker", COMMITTED)
def test_every_band_is_the_trailing_bands_own_stat_or_is_named_withheld(ticker: str) -> None:
    """One definition of current/percentile/history for trailing and forward alike. A missing band
    is named in `withheld`, with the latest cell's own text when that cell is not a number."""
    b = _bundle(ticker)
    rows = _multiples(b)
    fm = cs.forward_multiple_history(b)
    assert fm is not None
    wb = b.workbook("financials", freq="quarterly")
    assert wb is not None
    sha, mtime = cs.file_provenance(wb.path)
    assert (fm.source_file, fm.source_sha256) == (wb.path.name, sha)
    for s in fm.series:
        shared = cs._own_history_band(s.metric, cs._multiples_close(rows, s.row_label),
                                      source_file=wb.path.name, source_sha256=sha,
                                      source_mtime=mtime)
        if shared is None:
            assert s.band is None
            named = [w for w in fm.withheld if w.startswith(f"{s.metric}: no own-history band")]
            assert len(named) == 1, f"{ticker} {s.metric}: band missing and not named"
            last = s.points[-1]
            if last.close is None:
                assert f"reads '{last.cell}'" in named[0]
        else:
            # the shared helper's band, under the forward history's names (2026-10-09): its
            # `current` is the LATEST OBSERVED CLOSE, never today's multiple
            assert s.band == ForwardHistoryBand.from_own_history(
                shared.model_copy(update={"series": []})), s.metric


def test_ev_ntm_ebit_is_never_read_off_the_ebitda_row() -> None:
    """THE LABEL CLASH, on the real sheet: a prefix match on 'TEV/NTM EBIT' returns the EBITDA row,
    which comes first. The layer's EBIT series is the EBIT row's, and differs from EBITDA's."""
    b = _bundle("AMZN")
    rows = _multiples(b)
    ebitda = cs._find_row(rows, "TEV/NTM EBITDA")
    assert cs._find_row_prefix(rows, "TEV/NTM EBIT") == ebitda, "the clash shape is gone — re-check"
    fm = cs.forward_multiple_history(b)
    assert fm is not None
    by = {s.metric: [p.close for p in s.points] for s in fm.series}
    assert by["EV/NTM EBIT"] != by["EV/NTM EBITDA"]
    assert by["EV/NTM EBIT"] == [clean_num(c) for _, c in _own_close_cells(rows, "TEV/NTM EBIT")]


def test_a_missing_latest_close_leaves_no_band_and_no_older_close_stands_in() -> None:
    """THE PREVIOUSLY UNSEEN CASE, from V's export as observed 2026-10-07: EV/NTM EBIT reads '-' on
    its latest column (2026-08-07) and a number on the quarter-end before it. The point keeps '-',
    the band is withheld saying '-', and the quarter-end is not promoted to current."""
    b = _bundle("V")
    fm = cs.forward_multiple_history(b)
    assert fm is not None
    if fm.source_sha256 != "d679b77771":
        pytest.skip("V's Financials export re-pulled after 2026-10-07; the shape was that file's")
    ebit = next(s for s in fm.series if s.metric == "EV/NTM EBIT")
    assert (ebit.points[-1].date, ebit.points[-1].close, ebit.points[-1].cell) == (
        "2026-08-07", None, "-")
    assert ebit.points[-2].close is not None
    assert ebit.band is None
    assert any(w.startswith("EV/NTM EBIT: no own-history band") and "reads '-'" in w
               for w in fm.withheld)
    assert next(s for s in fm.series if s.metric == "EV/NTM EBITDA").band is not None


def test_nm_and_no_data_stay_different_states() -> None:
    """NEGATIVE PIN for the fold: a pre-revenue name's forward rows read 'NM' (a negative
    denominator), which is not '-' (no figure) — both survive as written."""
    cells = {p.cell for s in cs.forward_multiple_history(_bundle("ORKA")).series  # type: ignore[union-attr]
             for p in s.points if p.close is None}
    assert "NM" in cells
    v = cs.forward_multiple_history(_bundle("V"))
    assert v is not None
    assert "-" in {p.cell for s in v.series for p in s.points if p.close is None}


def test_points_come_in_time_order_whatever_the_column_order(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Every committed export runs oldest → newest, so a dropped sort would pass the corpus pin.
    The same real AMZN sheet with its date columns REVERSED must yield the same layer —
    `_multiples_close`'s own note: column order is the sheet's, not a time order."""
    b = _bundle("AMZN")
    want = cs.forward_multiple_history(b)
    flipped = [r[:2] + r[2:][::-1] for r in _multiples(b)]
    monkeypatch.setattr(b, "sheet", lambda *a, **k: flipped)
    got = cs.forward_multiple_history(b)
    assert got is not None and want is not None
    assert got.series == want.series and got.as_of == want.as_of


def test_only_the_pe_row_is_context_only_and_it_says_why() -> None:
    flags = {metric: ctx for metric, _, ctx in cs._FORWARD_MULTIPLES}
    assert flags == {"EV/NTM Revenue": False, "EV/NTM EBITDA": False, "EV/NTM EBIT": False,
                     "P/NTM EPS": True}
    fm = cs.forward_multiple_history(_bundle("AMZN"))
    assert fm is not None
    for s in fm.series:
        assert s.context_only is (s.metric == "P/NTM EPS")
        assert (s.note is not None) is s.context_only
    pe = next(s for s in fm.series if s.context_only)
    assert pe.note is not None and "2026-09-03-percentiles-demoted-ev-ebit-replaces" in pe.note


def test_the_anchor_still_reads_the_trailing_band() -> None:
    """The forward rows sit BESIDE the trailing bands, never in their place: `own_history_bands`
    — what the page's valuation and the anchor read — still carries exactly the two trailing
    multiples."""
    b = _bundle("AMZN")
    trailing = cs.own_history_bands(b).value
    assert trailing is not None
    assert [band.metric for band in trailing] == ["EV/EBITDA (TEV/LTM)", "P/LTM EPS"]


# --- the record: outside the synthesis, absent until built, before the anchor -------------------


def _minimal() -> ForwardMultipleHistory:
    return ForwardMultipleHistory(
        as_of="2026-09-16", source_ref="test", series=[MultipleHistorySeries(
            metric="EV/NTM EBIT", row_label="TEV/NTM EBIT", context_only=False,
            points=[MultipleClose(date="2026-06-30", close=24.3),
                    MultipleClose(date="2026-09-16", close=None, cell="-")])])


def test_the_layer_is_never_synthesis_input() -> None:
    assert "forward_multiple_history" in Dossier.model_fields
    assert "forward_multiple_history" not in MechanicalLayer.model_fields


def test_absent_until_built_and_it_sits_before_the_anchor() -> None:
    path = ROOT / "data" / "dossiers" / "AMZN" / "dossier.json"
    if not path.exists():
        pytest.skip("no committed AMZN dossier")
    doc = Dossier.model_validate_json(path.read_text())
    if doc.forward_multiple_history is None:
        assert '"forward_multiple_history"' not in dossier_json(doc), "absent was written as a key"
    built = dossier_json(doc.model_copy(update={"forward_multiple_history": _minimal()}))
    assert built.index('\n  "forward_multiple_history": {') < built.index('\n  "anchor": {')


# --- the refresh step: only from the export the page was built from ------------------------------


def _copy_page(tmp_path: Path, ticker: str) -> Path:
    src = ROOT / "data" / "dossiers" / ticker
    if not (src / "dossier.json").exists():
        pytest.skip(f"no committed {ticker} dossier")
    folder = tmp_path / ticker
    folder.mkdir()
    for name in ("dossier.json", "dossier.md"):
        (folder / name).write_text((src / name).read_text())
    return folder / "dossier.json"


def test_the_refresh_lands_the_layer_and_moves_nothing_else(tmp_path: Path) -> None:
    """END TO END on AMZN: the page's trailing bands name the export on disk, so the layer is
    written — equal to the builder's — and the synthesis, the anchor, the mechanical layer and the
    rendered page are untouched."""
    from vinci.dossier.refresh import forward_multiple_history_transform, refresh_dossier

    b = _bundle("AMZN")
    path = _copy_page(tmp_path, "AMZN")
    before = json.loads(path.read_text())
    md_before = path.with_name("dossier.md").read_text()
    refresh_dossier(path, top_level=forward_multiple_history_transform("AMZN"))
    after = json.loads(path.read_text())
    built = cs.forward_multiple_history(b)
    assert built is not None
    assert after["forward_multiple_history"] == json.loads(built.model_dump_json())
    for key in ("mechanical", "synthesis", "anchor"):
        assert after[key] == before[key], f"{key} moved"
    assert path.with_name("dossier.md").read_text() == md_before
    assert list(after)[-1] == "anchor"


def test_a_page_that_cannot_name_this_export_is_left_alone() -> None:
    """NEGATIVE: a page whose bands name another export, or no export at all, gets nothing — the
    layer would put a second vintage on it. It waits for a re-assembly."""
    from vinci.dossier.refresh import forward_multiple_history_transform

    _bundle("AMZN")
    doc: dict[str, Any] = json.loads(
        (ROOT / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())
    step = forward_multiple_history_transform("AMZN")
    assert "forward_multiple_history" in step(doc)
    bands = doc["mechanical"]["valuation"]["own_history"]["value"]
    assert len(bands) == 2, "AMZN carries both trailing bands"
    bands[1]["source_sha256"] = "0000000000"   # two bands, two exports: neither is THE page's
    assert step(doc) == {}
    for band in bands:
        band["source_sha256"] = "0000000000"
    assert step(doc) == {}
    doc["mechanical"]["valuation"]["own_history"]["value"] = None
    assert step(doc) == {}


def test_assembly_builds_the_layer_through_the_one_builder() -> None:
    """A SOURCE PIN, AND ITS LIMIT STATED: it asserts the call is written, not that it runs —
    assembly needs the network and an LLM. The artifact pass catches the consequence."""
    from vinci.dossier import assemble as asm

    assert ("forward_multiple_history=ciq_sheets.forward_multiple_history(bundle)"
            in inspect.getsource(asm.assemble_one))
