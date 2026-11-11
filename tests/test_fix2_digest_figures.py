"""The prompt-fix program's FIX 2 (handed to fix request 2's streams on #1004): every figure the
synthesis is handed carries its sign, unit and period from the structured value.

Four places dropped one, each found on the panel's frozen requests or the CIQ rows behind them:

1. A signed change printed `{:+.0f}%`, so anything under half a percent read "+0%" or "-0%" — a
   change shown as no change (the annual and quarterly growth rows, the consensus path's net move;
   `ciq_sheets.signed_pct` now prints them all).
2. CIQ's Surprise sheet holds 0.0 where its own Actual and Estimate rows differ (NFLX's GAAP EPS
   FY2004–FY2013, PARR's FY2014–FY2016), and the page printed each "+0%" — a met estimate the rows
   contradict. It now prints "n/a", explained once in the line's note.
3. The primary-source digest printed a level guide with no unit ("10.97–11.09" for EPS in $/share,
   "1206.0–1216.0" in $M) and a reconciliation without the change its release states.
4. The operating-drivers digest printed an anchored row's VERBATIM value and never its structured
   one: SMPL's "general and administrative expenses: $0.8 million, or 1.9%" is a FALL
   (`value_num` -1.9), and no row said its period.

Value pins run on frozen inputs only: the CIQ Surprise rows cut through the real decode path
(`tests/fixtures/ciq_surprise_listings.json`, `scripts/build_surprise_listings_fixture.py`) and the
panel's frozen SMPL page (`vinci/evals/synthesis_panel.json`'s freeze, a git blob).
"""
from __future__ import annotations

import copy
import json
import pathlib
import re
import subprocess
from typing import Any

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier import synthesis as syn
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.evals import replay as rp
from vinci.evals.capture_child import pre_synthesis_mech

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX: dict[str, Any] = json.loads(
    (ROOT / "tests" / "fixtures" / "ciq_surprise_listings.json").read_text())
PANEL = rp.load_panel_file()


# --- 1. a signed change is never printed as no change ------------------------------------------

@pytest.mark.parametrize(("pct", "text"), [
    (0.3, "+0.3%"), (-0.3, "-0.3%"), (-0.5, "-0.5%"), (0.5, "+0.5%"), (0.04, "+0.04%"),
    (0.0098, "+0.01%"), (4.6, "+5%"), (-12.0, "-12%"), (0.0, "0%"),
])
def test_a_signed_change_prints_a_digit_it_has(pct: float, text: str) -> None:
    """FAILED as `{:+.0f}%` for every case under half a percent ("+0%", "-0%")."""
    assert cs.signed_pct(pct) == text


def test_no_nonzero_change_is_printed_as_zero() -> None:
    """The negative half, swept: no change other than an exact zero prints a zero."""
    for k in range(1, 2000):
        for x in (k / 1000, -k / 1000, k * 7.3, -k * 7.3):
            assert cs.signed_pct(x) not in ("+0%", "-0%", "0%"), x


def test_no_signed_whole_percent_format_is_left_in_the_ciq_reader() -> None:
    """The five `{:+.0f}%` formats TeamNostra's driver-facts stream found all go through
    `signed_pct`; the format survives only inside it."""
    src = (ROOT / "vinci/dossier/ciq_sheets.py").read_text()
    body = src.split("def signed_pct", 1)[1].split("\ndef ", 1)[0]
    assert src.count(":+.0f}%") == body.count(":+.0f}%") == 1


def test_the_consensus_paths_net_move_keeps_its_digit() -> None:
    assert cs._net_change(100.0, 100.3) == "net +0.3%"
    assert cs._net_change(100.0, 99.6) == "net -0.4%"
    assert cs._net_change(100.0, 124.0) == "net +24%"


# --- 2. CIQ's 0.0 beside an actual and an estimate that differ ---------------------------------

def _bundle(name: str, rows: list[list[Any]] | None = None) -> CiqBundle:
    path = pathlib.Path("/frozen") / FIX["_about"]["exports"][name]["file"]
    wb = CiqWorkbook(kind="estimates", path=path, fmt=CiqFormat.BIFF_XLS, freq=None)
    return CiqBundle(ticker=name, workbooks=(wb,), _cache={path: {
        "Surprise": rows if rows is not None else copy.deepcopy(FIX["names"][name]["rows"])}})


def _eps(name: str, rows: list[list[Any]] | None = None) -> dict[str, str]:
    got = cs.surprise_history(_bundle(name, rows)).value
    assert got is not None
    eps = got.split("; Revenue surprise:")[0].removeprefix("GAAP-EPS surprise: ")
    return dict(p.split(" ", 1) for p in eps.split(", "))


def test_parrs_zero_cells_beside_differing_rows_print_na() -> None:
    """FAILED at main: FY2014, FY2015, FY2016, FY2020, FY2021 and FY2024 each printed "+0%". The
    NYSE:PARR block's own rows, in the frozen export, state FY2014 actual -1.44 against estimate
    -1.87 and FY2015 -1.06 against 0.65."""
    eps = _eps("PARR")
    assert [y for y, v in eps.items() if v == "n/a"] == [
        "FY2014", "FY2015", "FY2016", "FY2020", "FY2021", "FY2024"]
    assert eps["FY2023"] == "+52%" and eps["FY2018"] == "-15%"


def test_nflxs_pre_split_years_print_na_and_its_real_surprises_stay() -> None:
    """NFLX's sub-cent split-adjusted EPS: CIQ's 0.0 for FY2004–FY2013 sits beside actuals and
    estimates that differ (FY2004: 0.00457 against 0.00423); its "Difference" row reads 0.0 too."""
    eps = _eps("NFLX")
    assert all(eps[f"FY{y}"] == "n/a" for y in range(2004, 2014))
    assert eps["FY2014"] == "+20%" and eps["FY2015"] == "+50%"


def test_googls_half_percent_surprise_is_not_printed_as_zero() -> None:
    """FAILED at main: GOOGL's FY2024 surprise, 0.005, printed "+0%" (Python rounds .5 to even)."""
    assert _eps("GOOGL")["FY2024"] == "+0.5%"


def test_a_true_zero_stays_a_zero_and_needs_no_note() -> None:
    """The negative half: a 0.0 whose actual equals its estimate is a met estimate, "0%"."""
    rows = copy.deepcopy(FIX["names"]["PARR"]["rows"])
    hdr = next(i for i, r in enumerate(rows) if r and str(r[0]).strip() == "NYSE:PARR (USD)")
    ri = next(i for i in range(hdr, len(rows)) if rows[i]
              and str(rows[i][0]).strip().startswith("EPS (GAAP)"))
    act, est = (next(i for i in range(ri, ri + 5) if rows[i]
                     and str(rows[i][0]).strip() == lab) for lab in ("Actual", "Estimate"))
    col = next(j for j in range(1, len(rows[hdr])) if cs.clean_num(rows[hdr][j]) == 2014)
    rows[est][col] = rows[act][col]
    assert _eps("PARR", rows)["FY2014"] == "0%"


def test_the_na_is_explained_once_inside_the_lines_trailing_note() -> None:
    """The web reads the line's LAST parenthetical as its note and each point's last token as its
    value (`frontend/views/shared/dossier.js` `parseSeries`): the explanation sits in that note, so
    every point still ends in a value."""
    for name in ("PARR", "NFLX", "GOOGL"):
        text = cs.surprise_history(_bundle(name)).value or ""
        note = re.search(r"\s*\(([^()]*)\)\s*$", text)
        assert note is not None
        body = text[:note.start()]
        has_na = " n/a," in body + "," or body.endswith(" n/a")
        assert (cs.NO_SURPRISE_NOTE in note.group(1)) is has_na, name
        assert text.count(cs.NO_SURPRISE_NOTE) == (1 if has_na else 0)
        for seg in body.split("; "):
            for point in seg.split(": ", 1)[1].split(", "):
                value = point.split()[-1]
                assert value == "n/a" or value.endswith("%"), (name, point)


# --- 3 and 4. the digests, on the panel's frozen SMPL page ----------------------------------------

def _smpl() -> Any:
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e",
                       f"{PANEL['freeze_ref']}^{{commit}}"], capture_output=True).returncode != 0:
        pytest.skip("the panel's freeze commit is not in this history")
    return pre_synthesis_mech(rp.page_at("SMPL", PANEL["freeze_ref"],
                                         expect_blob=PANEL["pages"]["SMPL"]["dossier_blob"]))


def test_a_level_guide_carries_its_unit_and_a_reconciliation_its_stated_change() -> None:
    """FAILED at main: "guidance (net sales 2026): 1345.0–1355.0 [SUPERSEDED …" and
    "reconciliation (adjusted ebitda Q4 2026): 57.5 → …"."""
    lines = syn._primary_source_digest(_smpl().primary_source).splitlines()
    assert any(x.startswith("guidance (net sales 2026): 1345.0–1355.0 $M [SUPERSEDED")
               for x in lines)
    assert "reconciliation (adjusted ebitda Q4 2026): 57.5 (-13.2%) → 8-K 0001702744-26-000028 " \
           "EX-99.1" in lines
    # a CHANGE guide already printed its unit, and is unmoved
    assert any(x.startswith("guidance (net sales 2026): CHANGE of -2.0–2.0 % vs the prior period")
               for x in lines)


def test_an_anchored_driver_carries_its_signed_structured_value_and_every_row_its_period() -> None:
    """FAILED at main: the row printed "$0.8 million, or 1.9%" — no sign — and no period."""
    mech = _smpl()
    lines = syn._operating_drivers_digest(mech.operating_drivers).splitlines()[1:]
    rows = [x for x in lines if x.startswith("[")]
    assert ("[attribution] general and administrative expenses (period not stated): $0.8 million, "
            "or 1.9% [structured: -1.9%] → 10-Q 0001702744-26-000023") in rows
    assert all(re.match(r"^\[\w+\] .+ \([^()]+\): ", x) for x in rows)
    # the negative half: a row with no structured value prints none
    no_num = [r for r in mech.operating_drivers.rows if r.value_num is None]
    assert no_num and not any("[structured:" in x for x, r in zip(rows, mech.operating_drivers.rows,
                                                                  strict=True)
                              if r.value_num is None)

