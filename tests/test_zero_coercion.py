"""A CIQ MARKER OR AN ABSENT ROW IS NO VALUE, NEVER 0 (audit RC1: A-D1, A-D2; 2026-10-30).

THE DEFECT. `x or 0` / `x or 0.0` turned a None — a CIQ marker ('-', 'NA', 'NM', a blank …) or a row
the sheet does not carry — into a stated zero at eight sites:
* A-D1: the revision counts (`_revision_breadth`, `_forward_revisions`, `_horizon_value`) printed a
  marker as "0↑", which reads as "no analyst moved";
* A-D2: `ev_bridge` printed a 0.0 preferred / minority line with nothing behind it on all 13
  pursued pages (18 absent rows; UBER's '-', LLY's and CNXC's 'NA'), and `propose.r4_bridge_fact`
  wrote "preferred 0.0" into the R4 record's basis from it;
* `ciq_balance.extract` added two lease rows as `or 0.0` — rows no export on file carries;
* `ev_gap._margin_figures` added an absent D&A ratio as 0, so an EBIT margin stood under the EBITDA
  label.
`ciq.read_cell` reads a cell as (value, marker), so a caller says WHY there is no value; 'No Data
Available' joins the markers. `tests/test_zero_coercion_lint.py` holds the rule for every new site.

The synthetic exports are FROZEN, so value pins are allowed on them (CLAUDE.md TEST-LAYER RULE);
each test edits a fresh bundle's cells in memory, the marker taken as the BIFF probe row decodes it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.dossier import ciq_balance, ev_gap
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, read_cell, read_sheets
from vinci.dossier.propose import r4_bridge_fact
from vinci.dossier.schemas import SourceStatus

FIX = gen.HERE
ANNUAL, QUARTERLY = FIX / gen.ANNUAL_XLS, FIX / gen.QUARTERLY_XLS
XLSX, ESTIMATES = FIX / gen.QUARTERLY_XLSX, FIX / gen.ESTIMATES_XLS
LATEST_Q = f"FQ1/CQ3 {gen._mdy(gen.Q_DATES[-1])}"


def _bundle(*paths: Path) -> CiqBundle:
    return CiqBundle.from_files(gen.TICKER, sorted(paths))


@pytest.fixture
def bundle() -> CiqBundle:
    return _bundle(ANNUAL, QUARTERLY)


@pytest.fixture
def estimates() -> CiqBundle:
    return _bundle(ESTIMATES)


def _probe(marker: str, path: Path = QUARTERLY) -> Any:
    """The marker AS DECODED from the committed probe row of `path` (BIFF or OOXML)."""
    inc = read_sheets(path)["Income Statement"]
    ri = cs._find_row(inc, gen.MARKER_ROW)
    assert ri is not None
    return inc[ri][gen.MARKERS.index(marker) + 1]


def _row(rows: list[list[Any]], label: str) -> list[Any]:
    ri = cs._find_row(rows, label)
    assert ri is not None, label
    return rows[ri]


# --- the reader ----------------------------------------------------------------------------------


@pytest.mark.parametrize("marker", gen.MARKERS, ids=lambda m: repr(m))
def test_read_cell_names_each_marker_never_a_value(marker: str) -> None:
    for path in (QUARTERLY, XLSX):
        got = read_cell(_probe(marker, path))
        assert got == (None, marker), (path.suffix, got)


def test_read_cell_tells_a_number_a_zero_and_unparseable_text_apart() -> None:
    assert read_cell("1,234.5") == (1234.5, None)
    assert read_cell(0.0) == (0.0, None) and read_cell("0.0") == (0.0, None)   # CIQ writes zeros
    assert read_cell("see note 4") == (None, None)               # neither a marker nor a value
    assert read_cell(None) == (None, "")


# --- A-D1: the revision counts -------------------------------------------------------------------


def _rev(b: CiqBundle) -> list[list[Any]]:
    return b.sheet("estimates", "Revisions")


def _window_row(rows: list[list[Any]], metric: str, window: str, label: str) -> list[Any]:
    bi = cs._find_row(rows, metric)
    assert bi is not None
    w = next(i for i in range(bi, len(rows)) if str(rows[i][0]).strip() == window)
    return rows[next(i for i in range(w, len(rows)) if str(rows[i][0]).strip() == label)]


def test_the_revisions_read_as_written(estimates: CiqBundle) -> None:
    """(+) The synthetic Revisions sheet, read: every window's counts, an explicit 0 a zero."""
    h = cs.horizon_read(estimates).value or ""
    assert "EPS (GAAP) FQ1 2027: 1m 2↑/1↓, 2m 3↑/1↓, 3m 4↑/2↓" in h
    assert "EPS (GAAP) FQ2 2027: 1m 1↑/0↓" in h
    assert cs.eps_revisions(estimates).value == "EPS (GAAP) FY 2027: 3↑/1↓ last mo"


@pytest.mark.parametrize("marker", gen.MARKERS, ids=lambda m: repr(m))
def test_a_marker_count_is_na_never_zero(estimates: CiqBundle, marker: str) -> None:
    rows = _rev(estimates)
    up = _window_row(rows, "EPS (GAAP)", "Last Month", "Upward")
    up[1] = up[3] = _probe(marker)              # FQ1 2027 and FY 2027
    assert "EPS (GAAP) FQ1 2027: 1m n/a↑/1↓" in (cs.horizon_read(estimates).value or "")
    assert cs.eps_revisions(estimates).value == "EPS (GAAP) FY 2027: n/a↑/1↓ last mo"
    counts = cs._forward_revisions(rows, "EPS (GAAP)", cs._block_starts(rows))
    one = next(r for r in counts if r.period == "FY 2027" and r.window == "1m")
    assert (one.up, one.down) == (None, 1)


def test_a_marker_count_is_shown_never_folded_into_no_revisions_md() -> None:
    """The brief classifies a horizon line by its rendered counts: an 'n/a' is a window CIQ does
    not state, never "no revisions in any window"."""
    from vinci.dossier import render
    from vinci.dossier.schemas import Sourced

    lines = render._horizon_lines(Sourced.present(
        "EPS (GAAP) FQ1 2027: 1m n/a↑/0↓, 2m 0↑/0↓", source_ref="CIQ Estimates→Revisions"))
    assert "  - EPS (GAAP) FQ1 2027: 1m n/a↑/0↓, 2m 0↑/0↓" in lines
    assert not any("no revisions in any window" in ln for ln in lines)


def test_a_marker_count_is_shown_never_folded_into_no_revisions_web(tmp_path: Path) -> None:
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node not available")
    page = json.loads(Path("data/dossiers/TJX/dossier.json").read_text())
    page["mechanical"]["catalyst_path"]["horizon_read"] = {
        "status": "present", "value": "EPS (GAAP) FQ1 2027: 1m n/a↑/0↓, 2m 0↑/0↓",
        "source_ref": "CIQ Estimates→Revisions"}
    (tmp_path / "page.json").write_text(json.dumps(page))
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = tmp_path / "driver.mjs"
    driver.write_text(f"""
import {{ readFileSync }} from "node:fs";
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
const {{ renderDossier }} = await import("{dj}");
const page = JSON.parse(readFileSync({json.dumps(str(tmp_path / "page.json"))}, "utf8"));
const html = renderDossier(page, null);
console.log(JSON.stringify({{shown: html.includes("1m n/a↑/0↓"),
  folded: /no revisions in any window: [^<]*EPS \\(GAAP\\)/.test(html)}}));
""")
    out = subprocess.run(["node", str(driver)], capture_output=True, text=True,
                         check=True).stdout.strip().splitlines()[-1]
    assert json.loads(out) == {"shown": True, "folded": False}


# --- A-D2: the EV bridge and the R4 prefill ------------------------------------------------------


def _line(bridge: Any, label: str) -> Any:
    return next(ln for ln in bridge.lines if ln.label == label)


def test_a_marker_claim_is_unread_and_says_so(bundle: CiqBundle) -> None:
    """The synthetic quarterly balance sheet writes '-' for preferred, as UBER's does."""
    b = cs.ev_bridge(bundle, fy_periods=["FY27"])
    assert b is not None
    pref = _line(b, "Total Pref. Equity")
    assert pref.value is None and pref.unread == f"'Total Pref. Equity' reads '-' at [{LATEST_Q}]"
    assert _line(b, "Total Minority Interest").value == gen.Q_MINORITY[-1]
    assert b.claims == round(gen.Q_DEBT[-1] - gen.Q_CASH[-1] + gen.Q_MINORITY[-1], 3)
    assert "unread" not in json.loads(_line(b, "Total Minority Interest").model_dump_json())


def test_an_absent_claim_row_is_named(bundle: CiqBundle) -> None:
    bs = bundle.sheet("financials", "Balance Sheet", freq="quarterly")
    bs.remove(_row(bs, "Total Minority Interest"))
    b = cs.ev_bridge(bundle, fy_periods=["FY27"])
    assert b is not None
    m = _line(b, "Total Minority Interest")
    assert m.value is None
    assert m.unread == "the balance sheet carries no 'Total Minority Interest' row"


def test_the_r4_prefill_states_an_unread_claim_never_zero() -> None:
    """DECISION PATH (R4 prefill): UBER's committed page, its preferred line as the rebuilt bridge
    writes it — the record's basis says it is not stated; the claims value does not move."""
    doc = json.loads(Path("data/dossiers/UBER/dossier.json").read_text())
    before = r4_bridge_fact(doc)
    pref = next(ln for ln in doc["ev_bridge"]["lines"] if ln["label"] == "Total Pref. Equity")
    pref.update(value=None, unread="'Total Pref. Equity' reads '-' at [Q2 Jun-30-2026]")
    got = r4_bridge_fact(doc)
    assert got["value"] == before["value"]
    assert ("preferred not stated ('Total Pref. Equity' reads '-' at [Q2 Jun-30-2026])"
            in got["basis"])
    assert "preferred 0.0" not in got["basis"]


# --- the anchor bridge's lease rows, and the EV gap's margin --------------------------------------


def test_absent_lease_rows_are_named_never_added_as_zero(bundle: CiqBundle) -> None:
    ciq = ciq_balance.extract(bundle, gen.TICKER)
    nd = ciq.facts["net_debt"]
    assert nd.value == round(gen.Q_DEBT[-1] - gen.Q_CASH[-1], 4)
    assert "carries no 'Capital Leases' or 'Operating Lease Liabilities' row" in nd.basis


@pytest.mark.parametrize("marker", gen.MARKERS, ids=lambda m: repr(m))
def test_a_marker_on_a_lease_row_refuses_the_net_debt_fact(bundle: CiqBundle, marker: str) -> None:
    bs = bundle.sheet("financials", "Balance Sheet", freq="quarterly")
    bs.append(["Capital Leases", *([4.0] * (len(gen.Q_DATES) - 1)), _probe(marker)])
    ciq = ciq_balance.extract(bundle, gen.TICKER)
    assert "net_debt" not in ciq.facts
    assert f"[{LATEST_Q}]" in ciq.unavailable["net_debt"]
    from vinci.dossier.anchor import _bridge_inputs
    nd = _bridge_inputs({}, {}, ciq)["net_debt"]
    assert nd.value is None and "CIQ's net debt: " in (nd.source or "")


def test_no_d_and_a_ratio_gives_no_ebitda_margin_beside_the_street() -> None:
    levels: dict[str, list[dict[str, object]]] = {
        "Revenue": [{"fy": "FY2027", "median": 100.0}],
        "EBITDA": [{"fy": "FY2027", "median": 20.0}]}
    got = ev_gap._margin_figures(levels, {"margin": 0.12, "d_and_a_ratio": 0.03}, "FY2027")
    assert got is not None and got["ours"] == pytest.approx(0.15)       # (+) EBIT + D&A ratio
    assert got["consensus"] == pytest.approx(0.2)
    assert ev_gap._margin_figures(levels, {"margin": 0.12}, "FY2027") is None


def test_a_valued_claim_still_reads(bundle: CiqBundle) -> None:
    """(+) a preferred CIQ states is a claim."""
    bs = bundle.sheet("financials", "Balance Sheet", freq="quarterly")
    _row(bs, "Total Pref. Equity")[-1] = 7.5
    b = cs.ev_bridge(bundle, fy_periods=["FY27"])
    assert b is not None and _line(b, "Total Pref. Equity").value == 7.5
    assert cs.net_debt(bundle).status is SourceStatus.PRESENT
