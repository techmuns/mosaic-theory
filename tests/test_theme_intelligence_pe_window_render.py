"""THE DESK'S P/E COLUMN IS FIVE YEARS OR NOTHING — end to end on a real stored context.

Operator, 2026-11-11, on TH-BAA07551ED's "Companies the thesis implies": "why do we have some
names with 2y PE percentile vs some at 5y … it should be same (5y) for all names". The fixture is
that thesis's context as the registry stored it (run R-20261110T153023Z-market, registry
4527c2b1): MSFT, META and ORCL on five years; AMZN and GOOGL on two (a 2022 split inside five
years), EQIX and DLR on two (the run's Tiingo budget), VRT on two (a restated EPS). A context
stored before the standard keeps its two-year figures in the registry (append-only), so the
renderer refuses to show one in the five-year column — it is not held there, with why.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from vinci.theme_intelligence.cards import MARKET_COLUMNS, market_html, market_text
from vinci.theme_intelligence.schemas import MarketContext

FIXTURE = Path(__file__).parent / "fixtures" / "ti_market_context_TH-BAA07551ED.json"


def _context() -> MarketContext:
    return MarketContext.model_validate(json.loads(FIXTURE.read_text()))


def _pe_pct_cells(html: str) -> dict[str, str]:
    """ticker → the rendered P/E-percentile cell of its row in the implied-companies table."""
    col = [f for _c, f, _k in MARKET_COLUMNS].index("pe_percentile")
    out = {}
    for row in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        tk = re.search(r'<span class="tk">([A-Z.]+)</span>', row)
        cells = re.findall(r'<td class="n">(.*?)</td>', row, re.S)
        if tk and len(cells) == len(MARKET_COLUMNS) + 1:  # the close, then one per column
            out[tk.group(1)] = cells[col + 1]
    return out


def test_the_premise_the_stored_context_mixes_two_windows() -> None:
    c = _context()
    windows = {r.ticker: r.pe_percentile.detail for r in c.hypotheses}
    assert windows == {"MSFT": "5y", "AMZN": "2y", "GOOGL": "2y", "META": "5y", "ORCL": "5y",
                       "EQIX": "2y", "DLR": "2y", "VRT": "2y"}


def test_no_two_year_percentile_reaches_the_five_year_column() -> None:
    html = market_html(_context(), missing="")
    cells = _pe_pct_cells(html)
    assert set(cells) == {"MSFT", "AMZN", "GOOGL", "META", "ORCL", "EQIX", "DLR", "VRT"}
    assert not [t for t, c in cells.items() if "2y" in c], cells
    for t in ("AMZN", "GOOGL", "EQIX", "DLR", "VRT"):
        assert "not held" in cells[t] and "five-year standard" in cells[t], (t, cells[t])
    for t in ("MSFT", "META", "ORCL"):  # the five-year figures are shown as they were
        assert re.search(r"\d+(st|nd|rd|th) pctile · 5y", cells[t]), (t, cells[t])
    assert "P/E vs own 5y history" in html


def test_the_markdown_record_says_the_same() -> None:
    by = {r.ticker: r for r in _context().hypotheses}
    assert market_text(by["AMZN"].pe_percentile, "rank").startswith("not held")
    assert market_text(by["MSFT"].pe_percentile, "rank").endswith("pctile · 5y")


def test_the_measured_list_under_the_table_says_a_short_window_is_not_held_there() -> None:
    """The on-demand "How each figure is measured" list sits under the "5y" column header: a
    stored two-year basis there says it is not held in that column, before how it was measured."""
    html = market_html(_context(), missing="")
    how = html.split("How each figure is measured", 1)[1]
    items = re.findall(r"<li>P/E vs own 5y history: (.*?)</li>", how, re.S)
    assert len(items) == 8, len(items)
    short = [i for i in items if i.startswith("not held — a two-year figure")]
    assert len(short) == 5 and all("measured as share of its daily P/Es" in i for i in short)
