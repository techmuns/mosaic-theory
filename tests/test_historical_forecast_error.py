"""Historical forecast error: how far the FINAL consensus missed each completed fiscal year.

THE SHAPES THIS GUARDS, each observed on the committed exports (2026-10-08):
- six exports (BRBR, IT, NKE, PARR, SMPL, V) carry a second annual company-level block under
  'Calendar Years' with different figures, so the block is found by its 'Fiscal Years' banner;
- a percentage of the estimate is meaningless where the base is small or changes sign — AMZN's
  2014 EBIT estimate was −$216M against an actual +$178M (literal −182.5%), while the same miss is
  +0.44 margin points;
- the margin error alone, multiplied by revenue, drops the revenue miss's EBIT effect: AMZN 2025
  EBIT BEAT by $78M while its margin error is −0.02 points.

The CIQ-backed tests read the licensed workbooks on disk and SKIP without them (never committed).
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, clean_num
from vinci.dossier.schemas import Dossier, HistoricalForecastError, MechanicalLayer, dossier_json

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


def _fiscal_block(rows: list[list[Any]]) -> tuple[int, int]:
    """[header, end) of the company-level block under 'Fiscal Years', found WITHOUT the module's
    helpers: the banner in column 1, the next banner, the 'Company Level' row between them."""
    banner = next(i for i, r in enumerate(rows)
                  if len(r) > 1 and str(r[1]).strip() == "Fiscal Years")
    end = next((i for i in range(banner + 1, len(rows)) if len(rows[i]) > 1
                and str(rows[i][1]).strip() in ("Calendar Years", "Fiscal Quarters",
                                                "Calendar Quarters")), len(rows))
    hdr = next(i for i in range(banner + 1, end)
               if str(rows[i][0]).strip().startswith("Company Level"))
    return hdr, end


# --- the reads, on the real workbooks ------------------------------------------------------------


@pytest.mark.parametrize("ticker", COMMITTED)
def test_every_observation_is_its_fiscal_year_cells_and_agrees_with_ciqs_difference(
        ticker: str) -> None:
    """ACROSS THE CORPUS: each observation is the Actual and Estimate cells of its year in the
    FISCAL-years block, and CIQ's own 'Difference' row equals actual − estimate — the reading and
    the sheet agree."""
    b = _bundle(ticker)
    h = cs.historical_forecast_error(b)
    if h is None:
        return
    rows = b.sheet("estimates", "Surprise")
    hdr, end = _fiscal_block(rows)
    years = {int(float(c)): j for j, c in enumerate(rows[hdr])
             if j and (n := clean_num(c)) is not None and n.is_integer() and 1990 <= n <= 2100}
    for s in h.series:
        title = next(i for i in range(hdr + 1, end) if str(rows[i][0]).strip() == s.metric)
        sub: dict[str, list[Any]] = {}
        for k in range(title + 1, end):
            label = str(rows[k][0]).strip()
            if label and label not in cs._SURPRISE_SUB_ROWS:
                break
            sub.setdefault(label, rows[k])
        for o in s.observations:
            col = years[o.fiscal_year]
            assert (o.actual, o.final_estimate) == (clean_num(sub["Actual"][col]),
                                                    clean_num(sub["Estimate"][col])), s.metric
            diff = clean_num(sub["Difference"][col])
            assert diff is not None
            assert diff == pytest.approx(o.actual - o.final_estimate, abs=0.01, rel=1e-6)


@pytest.mark.parametrize("ticker", COMMITTED)
def test_each_line_carries_only_its_meaningful_measures_and_the_identity_holds(
        ticker: str) -> None:
    """ACROSS THE CORPUS: Revenue carries a percentage and nothing revenue-normalised; profit lines
    and capex carry no percentage of their estimate. Wherever the revenue-normalised pair exists,
    error ÷ forecast revenue = ratio error + actual ratio × revenue miss, exactly."""
    h = cs.historical_forecast_error(_bundle(ticker))
    if h is None:
        return
    revenue = {o.fiscal_year: o for s in h.series if s.metric == "Revenue" for o in s.observations}
    for s in h.series:
        for o in s.observations:
            if s.metric == "Revenue":
                if o.final_estimate == 0:   # pre-revenue (TECX): no percentage, never a division
                    assert o.pct_error is None
                else:
                    assert o.pct_error == pytest.approx(o.actual / o.final_estimate - 1)
                assert o.error_per_forecast_revenue is None and o.ratio_error is None
                continue
            assert o.pct_error is None, f"{s.metric} {o.fiscal_year} carries a % of its estimate"
            magnitude = s.metric == "Capital Expenditure"
            a, e = (abs(o.actual), abs(o.final_estimate)) if magnitude else (o.actual,
                                                                             o.final_estimate)
            assert o.dollar_error == pytest.approx(a - e)
            r = revenue.get(o.fiscal_year)
            if r is None or not r.actual or not r.final_estimate:
                assert o.ratio_error is None and o.error_per_forecast_revenue is None
                continue
            assert o.error_per_forecast_revenue is not None and o.ratio_error is not None
            identity = o.ratio_error + (a / r.actual) * (r.actual / r.final_estimate - 1)
            assert o.error_per_forecast_revenue == pytest.approx(identity, abs=1e-12)


def test_a_block_missing_a_row_never_borrows_the_next_metrics(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Every committed block carries all its rows, so the corpus cannot show this. The same real
    AMZN sheet with EBIT's 'Announced Date' row removed must leave EBIT undated — not take the
    dates of the block below it, which a scan running on past the next title would."""
    b = _bundle("AMZN")
    rows = b.sheet("estimates", "Surprise")
    hdr, end = _fiscal_block(rows)
    title = next(i for i in range(hdr + 1, end) if str(rows[i][0]).strip() == "EBIT")
    gone = next(k for k in range(title + 1, end) if str(rows[k][0]).strip() == "Announced Date")
    cut = rows[:gone] + rows[gone + 1:]
    monkeypatch.setattr(b, "sheet", lambda *a, **k: cut)
    h = cs.historical_forecast_error(b)
    assert h is not None
    ebit = next(s for s in h.series if s.metric == "EBIT")
    assert all(o.announced is None for o in ebit.observations)
    ebitda = next(s for s in h.series if s.metric == "EBITDA")
    assert any(o.announced is not None for o in ebitda.observations)


def test_the_fiscal_block_is_read_never_the_calendarised_one() -> None:
    """THE OBSERVED TRAP: SMPL's export carries FY2017 revenue 396.171 under 'Fiscal Years' and a
    calendarised 404.9855 under 'Calendar Years'. The layer reads the fiscal one."""
    h = cs.historical_forecast_error(_bundle("SMPL"))
    assert h is not None
    rev = {o.fiscal_year: o.actual for s in h.series if s.metric == "Revenue"
           for o in s.observations}
    if h.source_sha256 is None or 2017 not in rev:
        pytest.skip("SMPL's export no longer carries FY2017")
    assert rev[2017] == pytest.approx(396.171)


def test_amzn_s_small_and_sign_crossing_years_read_as_margin_points() -> None:
    """THE PREVIOUSLY MISREAD YEARS, on the export the 2026-10-08 page was built from: 2014's EBIT
    estimate was negative, so no percentage is carried; its miss is +0.44 points of forecast
    revenue, the size of 2024's +0.35 — not the +182.5% a percentage would print."""
    h = cs.historical_forecast_error(_bundle("AMZN"))
    assert h is not None
    if h.source_sha256 != "e10ed62223":
        pytest.skip("AMZN's Estimates export re-pulled after 2026-10-08; figures were that file's")
    ebit = {o.fiscal_year: o for s in h.series if s.metric == "EBIT" for o in s.observations}
    assert len(ebit) == 22
    o14 = ebit[2014]
    assert o14.final_estimate == pytest.approx(-215.8, abs=0.1)
    assert o14.pct_error is None
    assert o14.error_per_forecast_revenue == pytest.approx(0.0044, abs=5e-5)
    assert ebit[2024].error_per_forecast_revenue == pytest.approx(0.0035, abs=5e-5)


def test_the_margin_error_alone_would_flip_amzn_s_2025_beat() -> None:
    """WHY BOTH MEASURES ARE KEPT: 2025 EBIT beat consensus by $78M; per forecast revenue the miss
    is positive, while the margin error is negative — it leaves out the revenue beat's EBIT."""
    h = cs.historical_forecast_error(_bundle("AMZN"))
    assert h is not None
    if h.source_sha256 != "e10ed62223":
        pytest.skip("AMZN's Estimates export re-pulled after 2026-10-08; figures were that file's")
    o = next(o for s in h.series if s.metric == "EBIT" for o in s.observations
             if o.fiscal_year == 2025)
    assert o.dollar_error > 0
    assert o.error_per_forecast_revenue is not None and o.error_per_forecast_revenue > 0
    assert o.ratio_error is not None and o.ratio_error < 0


def test_a_name_without_company_level_history_gets_no_layer() -> None:
    """NEGATIVE: FUBO's export carries no 'Fiscal Years' company-level block — no layer, never an
    empty one."""
    assert cs.historical_forecast_error(_bundle("FUBO")) is None


# --- the record: eligible as a cross-check only, outside the synthesis, absent until built -------


def test_the_layer_says_by_type_that_it_is_not_a_revision_distribution() -> None:
    fields = HistoricalForecastError.model_fields
    assert fields["usable_as_revision_distribution"].default is False
    with pytest.raises(ValueError):
        HistoricalForecastError(estimate_type="x", eligibility_note="x", usage_note="x", series=[],
                                source_ref="x", usable_as_revision_distribution=True)


def test_the_layer_is_never_synthesis_input_and_sits_before_the_anchor() -> None:
    assert "historical_forecast_error" in Dossier.model_fields
    assert "historical_forecast_error" not in MechanicalLayer.model_fields
    path = ROOT / "data" / "dossiers" / "AMZN" / "dossier.json"
    if not path.exists():
        pytest.skip("no committed AMZN dossier")
    doc = Dossier.model_validate_json(path.read_text())
    if doc.historical_forecast_error is None:
        assert '"historical_forecast_error"' not in dossier_json(doc)
    layer = HistoricalForecastError(estimate_type="x", eligibility_note="x", usage_note="x",
                                    series=[], source_ref="x")
    built = dossier_json(doc.model_copy(update={"historical_forecast_error": layer}))
    assert built.index('\n  "historical_forecast_error": {') < built.index('\n  "anchor": {')


# --- the refresh step: only from the export the page was built from ------------------------------


def test_the_refresh_lands_the_layer_only_from_the_pages_own_export(tmp_path: Path) -> None:
    """END TO END on AMZN: the page's forward consensus names this export, so the layer lands —
    equal to the builder's — and nothing else moves. NEGATIVE: a page naming another export, or
    none, is left alone."""
    from vinci.dossier.refresh import historical_forecast_error_transform, refresh_dossier

    b = _bundle("AMZN")
    src = ROOT / "data" / "dossiers" / "AMZN"
    if not (src / "dossier.json").exists():
        pytest.skip("no committed AMZN dossier")
    folder = tmp_path / "AMZN"
    folder.mkdir()
    for name in ("dossier.json", "dossier.md"):
        (folder / name).write_text((src / name).read_text())
    path = folder / "dossier.json"
    before = json.loads(path.read_text())
    step = historical_forecast_error_transform("AMZN")
    other = json.loads(json.dumps(before))
    other["forward_consensus"]["as_of"] = "≥1999-01-01"
    other["forward_consensus"].pop("source_sha256", None)
    assert step(other) == {}
    none = json.loads(json.dumps(before))
    none.pop("forward_consensus")
    assert step(none) == {}
    refresh_dossier(path, top_level=step)
    after = json.loads(path.read_text())
    built = cs.historical_forecast_error(b)
    assert built is not None
    assert after["historical_forecast_error"] == json.loads(dossier_json(
        Dossier.model_validate(after)))["historical_forecast_error"]
    assert HistoricalForecastError.model_validate(after["historical_forecast_error"]) == built
    for key in ("mechanical", "synthesis", "anchor", "forward_consensus"):
        assert after[key] == before[key], f"{key} moved"
    assert list(after)[-1] == "anchor"


def test_assembly_builds_the_layer_through_the_one_builder() -> None:
    """A SOURCE PIN, AND ITS LIMIT STATED: assembly needs the network and an LLM."""
    from vinci.dossier import assemble as asm

    assert ("historical_forecast_error=ciq_sheets.historical_forecast_error(bundle)"
            in inspect.getsource(asm.assemble_one))
