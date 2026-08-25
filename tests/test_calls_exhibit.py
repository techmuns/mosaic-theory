"""The candle primitives in lib/exhibit.js — the file's own rules, held against the new additions.

exhibit.js states three things this test enforces on the candle code: a null datum is a GAP and is
never bridged; nothing fabricates a value the data did not carry; and every primitive is a pure
function so `node` can exercise it exactly as the browser does.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXHIBIT = ROOT / "frontend" / "lib" / "exhibit.js"
TAPE = ROOT / "frontend" / "views" / "calls" / "tape.js"


def _run(js: str) -> object:
    src = EXHIBIT.read_text().replace("\nexport ", "\n").lstrip()
    if src.startswith("export "):
        src = src[len("export "):]
    out = subprocess.run(["node", "--input-type=module", "-e", f"{src}\n{js}"],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_the_candle_primitives_are_exported_at_all() -> None:
    src = EXHIBIT.read_text()
    for name in ("candleDomain", "candles", "candleWidth"):
        assert f"export function {name}" in src or f"export const {name}" in src, (
            f"{name} is not exported from exhibit.js")


def test_the_primitive_ships_with_a_consumer_not_speculatively() -> None:
    """exhibit.js's standing rule, in its own words: extension points are built "when a real
    consumer lands — not before"; the file also says "Not shipped unused." A candle primitive with
    nothing drawing candles is exactly the shape that rule forbids."""
    assert TAPE.is_file(), "candles were added to exhibit.js with no view drawing them"
    assert "candles" in TAPE.read_text(), "the tape view does not use the candle primitive"


@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_an_incomplete_bar_is_a_gap_and_is_never_bridged() -> None:
    """THE FABRICATION PIN. A missing OHLC leg must yield nothing at that index — not a body
    carried over from the previous bar, and not an interpolated one."""
    got = _run("""
      const sx = i => i * 10, sy = v => 100 - v;
      console.log(JSON.stringify(
        candles([1, null, 3], [2, 5, 4], [0, 1, 2], [1.5, 4, 3.5], {sx, sy, width: 4})
          .map(c => c === null ? null : c.bodyH)));""")
    assert isinstance(got, list) and got[1] is None, f"the incomplete bar was bridged: {got}"
    assert got[0] is not None and got[2] is not None, "complete bars were dropped"


@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_a_price_domain_does_not_floor_at_zero_and_keeps_a_target_in_view() -> None:
    """lineDomain floors at zero because zero means something for a margin. For a PRICE it does
    not: flooring a $290-$430 range at 0 spends most of the panel below anything that ever traded.
    And a stated target above the range must stay visible, or the chart implies it was never
    approached."""
    dom = _run("console.log(JSON.stringify(candleDomain([430, 400], [290, 300])))")
    assert isinstance(dom, dict) and dom["lo"] > 200, f"price domain floored toward zero: {dom}"
    pinned = _run("console.log(JSON.stringify(candleDomain([300], [290], {include: [400]})))")
    assert isinstance(pinned, dict) and pinned["hi"] >= 400, (
        f"an out-of-range target was left off the axis: {pinned}")
    assert _run("console.log(JSON.stringify(candleDomain([null], [null])))") is None, (
        "an all-null series produced a domain instead of failing loud")


@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_a_doji_still_renders_and_direction_follows_open_versus_close() -> None:
    """open === close has zero body height; drawn literally it is a hole in the series, which reads
    as a missing day rather than an unchanged one."""
    got = _run("""
      const sx = i => i * 10, sy = v => 100 - v;
      const d = candles([5], [6], [4], [5], {sx, sy, width: 4})[0];
      const dir = candles([1, 5], [6, 6], [0, 0], [5, 1], {sx, sy}).map(c => c.up);
      console.log(JSON.stringify({bodyH: d.bodyH, wick: d.wickY0 !== d.wickY1, dir}));""")
    assert isinstance(got, dict)
    assert got["bodyH"] > 0, "a doji rendered with zero height"
    assert got["wick"] is True, "a doji lost its high-low wick"
    assert got["dir"] == [True, False], "direction does not follow open vs close"


@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_candle_width_never_falls_below_a_visible_hairline() -> None:
    """A sub-pixel body is invisible, and an invisible datum reads as an absent one."""
    got = _run("console.log(JSON.stringify(["
               "candleWidth(1240, 315), candleWidth(1240, 20), candleWidth(10, 315)]))")
    assert isinstance(got, list)
    wide, few, cramped = got
    assert few > wide > 1.0, f"width does not scale with the bar count: {got}"
    assert cramped >= 1.2, f"a cramped panel produced an invisible candle: {cramped}"
