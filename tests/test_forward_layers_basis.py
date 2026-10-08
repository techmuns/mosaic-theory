"""The forward layers state their own basis (2026-10-08 analyst review of AMZN).

THE SHAPES THIS GUARDS, each observed on the committed exports:
- today's EV/NTM EBIT (AMZN 23.34x, Estimates export ≥10-06) sat only inside the ladder's display
  string, while the multiple HISTORY's `current` was the Financials export's 2026-09-16 close
  (22.59x) — two dates, one word;
- the history's last column is an export-day close on 23 names and a settled quarter-end on three
  (ORKA, TECX 06-30; VRRM 03-31), so "the last point is partial" is not a rule;
- CIQ's FCF and EBITDA consensus do not equal CFO − CapEx and EBIT + D&A (AMZN FY27: −$8.2bn
  against −$30.7bn; $273.6bn against $252.3bn) — each line is its own brokers' mean.

The CIQ-backed tests read the licensed workbooks on disk and SKIP without them (never committed).
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.schemas import (
    CurrentMultiple,
    Dossier,
    ForwardConsensus,
    dossier_json,
)

ROOT = Path(__file__).resolve().parents[1]
COMMITTED = sorted(p.parent.name for p in (ROOT / "data" / "dossiers").glob("*/dossier.json"))


def _bundle(ticker: str) -> CiqBundle:
    """The name's bundle, or SKIP — the licensed workbooks are never committed."""
    from vinci.config import get_config
    from vinci.dossier.manual_store import LocalFolderStore

    files = LocalFolderStore(get_config().data_dir / "manual" / "ciq").files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


def _render(cells: list[CurrentMultiple]) -> str:
    """The ladder string as `cross_name_anchor` writes it, rebuilt from the structured cells."""
    periods: list[str] = []
    for c in cells:
        if c.period not in periods:
            periods.append(c.period)
    lines = []
    for period in periods:
        row = [c for c in cells if c.period == period]
        if any(c.value is not None for c in row):
            lines.append(f"{period}: " + " · ".join(
                f"{c.metric} {c.value:.2f}" if c.value is not None else f"{c.metric} –"
                for c in row))
    return " | ".join(lines)


# --- today's multiples: the same cells as the string -------------------------------------------


@pytest.mark.parametrize("ticker", COMMITTED)
def test_the_ladder_string_is_the_structured_cells_rendered(ticker: str) -> None:
    """ACROSS THE CORPUS: the synthesis-input string and the structured values come from ONE read,
    so the string is exactly the cells rendered — no second parser, no drift."""
    b = _bundle(ticker)
    cells = cs.current_multiples(b)
    ladder = cs.cross_name_anchor(b)
    fc = cs.forward_consensus(b)
    assert fc is not None and fc.current_multiples == cells, "the layer carries other cells"
    if cells is None:
        assert ladder.value is None
        return
    assert ladder.value == _render(cells)


@pytest.mark.parametrize("ticker", COMMITTED)
def test_the_ntm_cells_are_the_sheets_own(ticker: str) -> None:
    """ACROSS THE CORPUS, read WITHOUT `_ladder_cells`: the row whose first cell is 'NTM', under the
    columns the TEV/REV header names — so a reader that shifted a column fails on every name."""
    from vinci.dossier.ciq import clean_num

    b = _bundle(ticker)
    rows = b.sheet("estimates", "Multiples")
    hdr = next(r for r in rows if any(isinstance(c, str) and "TEV/REV" in c for c in r))
    ntm = next((r for r in rows if r and str(r[0]).strip() == "NTM"), None)
    cells = {c.metric: c.value for c in cs.current_multiples(b) or [] if c.period == "NTM"}
    if ntm is None:
        assert not cells
        return
    want = {str(h).strip(): clean_num(ntm[j]) if j < len(ntm) else None
            for j, h in enumerate(hdr) if j > 0 and str(h).strip()}
    assert cells == want


def test_amzn_s_current_ev_ntm_ebit_is_the_estimates_figure_not_the_history_s_last_close() -> None:
    """THE PREVIOUSLY CONFLATED CASE, on the export the 2026-10-08 page was built from: today's
    EV/NTM EBIT is 23.34x (Estimates); the history's latest close is 22.59x on 2026-09-16
    (Financials), an export-day close after the 2026-06-30 quarter-end."""
    b = _bundle("AMZN")
    fc = cs.forward_consensus(b)
    assert fc is not None
    if fc.source_sha256 != "e10ed62223":
        pytest.skip("AMZN's Estimates export re-pulled after 2026-10-08; figure was that file's")
    ntm = {c.metric: c.value for c in fc.current_multiples or [] if c.period == "NTM"}
    assert ntm["TEV/EBIT"] == pytest.approx(23.3377, abs=1e-4)
    fm = cs.forward_multiple_history(b)
    assert fm is not None
    assert (fm.as_of, fm.latest_close_quarter_end, fm.history_through) == (
        "2026-09-16", False, "2026-06-30")


# --- the history's latest close: quarter-end or not, by its date --------------------------------


@pytest.mark.parametrize(("d", "settled"), [
    (date(2026, 9, 16), False), (date(2026, 9, 25), False), (date(2026, 8, 7), False),
    (date(2026, 6, 30), True), (date(2024, 3, 28), True), (date(2022, 12, 30), True)])
def test_a_close_is_a_quarter_end_by_its_date(d: date, settled: bool) -> None:
    """Both sides, from real columns: export-day closes (AMZN 09-16, BURL 09-25, V 08-07) are not
    quarter-ends; 2024-03-28 is (Good Friday took the 29th) and so is 2022-12-30."""
    assert cs._is_quarter_end_close(d) is settled


@pytest.mark.parametrize("ticker", COMMITTED)
def test_every_settled_column_is_a_quarter_end_and_the_latest_is_judged_by_its_date(
        ticker: str) -> None:
    """ACROSS THE CORPUS: every column before the latest passes the rule (the rule fits the sheet),
    and the latest is marked by its own date — never assumed partial (ORKA, TECX, VRRM end on a
    quarter-end)."""
    fm = cs.forward_multiple_history(_bundle(ticker))
    assert fm is not None
    dates = sorted({date.fromisoformat(p.date) for s in fm.series for p in s.points})
    assert all(cs._is_quarter_end_close(d) for d in dates[:-1])
    assert fm.latest_close_quarter_end is cs._is_quarter_end_close(dates[-1])
    assert fm.history_through == max(d for d in dates if cs._is_quarter_end_close(d)).isoformat()


# --- the reconciliations: arithmetic of the layer's own means -----------------------------------


@pytest.mark.parametrize("ticker", COMMITTED)
def test_every_reconciliation_is_the_layers_own_means_and_present_when_it_can_be(
        ticker: str) -> None:
    """ACROSS THE CORPUS: each record is the identity applied to the SAME layer's consensus means
    (capex and D&A by magnitude), and a record exists exactly where every line has a mean."""
    fc = cs.forward_consensus(_bundle(ticker))
    assert fc is not None
    means = {(s.metric, s.period): s.mean for s in fc.spreads if s.mean is not None}
    recs = {(r.period, r.identity): r for r in fc.reconciliations or []}
    # the identities stated HERE, not read from the module's table, so a sign flipped there fails
    identities = (("CFO − CapEx vs FCF", "Free Cash Flow",
                   (("Cash From Operations", 1), ("Capital Expenditure", -1))),
                  ("EBIT + D&A vs EBITDA", "EBITDA",
                   (("EBIT", 1), ("Depreciation & Amortization", 1))))
    for period in fc.periods:
        for name, reported, parts in identities:
            lines = [reported, *(line for line, _ in parts)]
            if any((line, period) not in means for line in lines):
                assert (period, name) not in recs
                continue
            r = recs[(period, name)]
            implied = sum(sign * abs(means[(line, period)] or 0.0) for line, sign in parts)
            assert r.implied == pytest.approx(implied)
            assert r.reported == means[(reported, period)]
            assert r.gap == pytest.approx(r.reported - r.implied)


def test_amzn_s_fy27_lines_do_not_add_up_and_the_record_says_by_how_much() -> None:
    """THE OBSERVED CASE: FY27 CFO 247.1bn − CapEx 277.8bn = −30.7bn, against CIQ's FCF −8.2bn,
    from 25, 33 and 14 contributors; EBIT + D&A 252.3bn against EBITDA 273.6bn."""
    fc = cs.forward_consensus(_bundle("AMZN"))
    assert fc is not None
    if fc.source_sha256 != "e10ed62223":
        pytest.skip("AMZN's Estimates export re-pulled after 2026-10-08; figures were that file's")
    recs = {r.identity: r for r in fc.reconciliations or [] if r.period == "FY 2027"}
    fcf = recs["CFO − CapEx vs FCF"]
    assert (round(fcf.implied), round(fcf.reported)) == (-30671, -8248)
    assert fcf.estimates == {"Free Cash Flow": "14/27", "Cash From Operations": "25/27",
                             "Capital Expenditure": "33/42"}
    ebitda = recs["EBIT + D&A vs EBITDA"]
    assert (round(ebitda.implied), round(ebitda.reported)) == (252321, 273634)


# --- the record: absent until built --------------------------------------------------------------


def test_a_page_built_before_the_new_keys_round_trips_byte_identically() -> None:
    """The committed pages predate these keys; written through the one serializer they must come
    back unchanged — ABSENT, never null, until a refresh fills them."""
    path = ROOT / "data" / "dossiers" / "AMZN" / "dossier.json"
    if not path.exists():
        pytest.skip("no committed AMZN dossier")
    text = path.read_text()
    doc = Dossier.model_validate_json(text)
    if doc.forward_consensus is None or doc.forward_consensus.current_multiples is not None:
        pytest.skip("AMZN's page already carries the new keys")
    assert dossier_json(doc) == text
    filled = doc.forward_consensus.model_copy(update={"current_multiples": [
        CurrentMultiple(period="NTM", metric="TEV/EBIT", value=23.34)]})
    written = json.loads(dossier_json(doc.model_copy(update={"forward_consensus": filled})))
    assert written["forward_consensus"]["current_multiples"][0]["value"] == 23.34
    assert "reconciliations" not in written["forward_consensus"]
    assert isinstance(ForwardConsensus.model_validate(written["forward_consensus"]),
                      ForwardConsensus)
